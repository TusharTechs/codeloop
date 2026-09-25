"""HTTP + WebSocket API and static hosting for the crash-cart screen.

WebSocket /ws/codes/{id}
  client → server   binary: room audio, PCM16 mono 16 kHz (live codes only)
                    text:   JSON controls (assign_role, confirm_loop, manual_event, confirm_end,
                            reject_end, end_code, set_policy, mute, unmute, ask, stop)
  server → client   text:   JSON (hello, state, utterance, partial, event, loop, flag,
                            flag_resolved, prompt, answer, agent_*, line_dropped, error, closed)
                    binary: 0x01 + PCM16 16 kHz room audio (replays), 0x02 + PCM16 24 kHz CodeLoop voice
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..config import Settings, get_settings
from ..debrief import DebriefSession
from ..record import build_record
from ..session import CodeSession
from ..store import Store

log = logging.getLogger(__name__)


class ImmutableStaticFiles(StaticFiles):
    """Vite gives every built asset a content hash, so it can be cached forever."""

    async def get_response(self, path: str, scope):  # type: ignore[no-untyped-def]
        resp = await super().get_response(path, scope)
        if resp.status_code == 200:
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp


class CreateCode(BaseModel):
    mode: str = "live"  # live | replay
    scenario: str | None = None


class SessionManager:
    def __init__(self, settings: Settings, store: Store, factory=CodeSession) -> None:
        self.settings = settings
        self.store = store
        self.factory = factory
        self.sessions: dict[str, CodeSession] = {}
        self._lock = asyncio.Lock()

    def active(self) -> list[CodeSession]:
        return [s for s in self.sessions.values() if not s.closed]

    async def create(self, mode: str, scenario: str | None) -> CodeSession:
        async with self._lock:
            if len(self.active()) >= self.settings.max_concurrent_codes:
                raise HTTPException(429, "Too many codes running. End one first.")
            replay_path = None
            if mode == "replay":
                replay_path = scenario_path(self.settings.replay_dir, scenario or "")
                if replay_path is None:
                    raise HTTPException(404, f"Unknown scenario {scenario!r}")
            elif mode != "live":
                raise HTTPException(400, "mode must be 'live' or 'replay'")
            code_id = uuid.uuid4().hex[:12]
            session = self.factory(code_id, self.settings, self.store, mode=mode, scenario=scenario)
            self.sessions[code_id] = session
        try:
            await session.start(replay_path=replay_path)
        except Exception as e:
            self.sessions.pop(code_id, None)
            log.exception("could not start code")
            raise HTTPException(502, f"Could not reach AssemblyAI: {e}") from e
        return session

    def get(self, code_id: str) -> CodeSession | None:
        return self.sessions.get(code_id)

    async def stop_all(self) -> None:
        for s in self.active():
            await s.stop()


def purge_old_audio(settings: Settings) -> int:
    """Delete stored room audio older than the retention period."""
    import time

    if not settings.audio_dir.exists():
        return 0
    cutoff = time.time() - settings.audio_retention_days * 86400
    removed = 0
    for f in settings.audio_dir.glob("*.wav"):
        if f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)
            removed += 1
    return removed


def list_scenarios(replay_dir: Path) -> list[dict]:
    out = []
    # The quick tour is listed first: it is what a first-time visitor should watch.
    for gold in sorted(replay_dir.glob("*.gold.json"), key=lambda p: (not p.name.startswith("demo_tour"), p.name)):
        stem = gold.name.removesuffix(".gold.json")
        if not (replay_dir / f"{stem}.wav").exists():
            continue
        g = json.loads(gold.read_text())
        out.append(
            {
                "id": stem,
                "title": g.get("title", stem),
                "duration_s": g.get("duration_s"),
                "noise": g.get("noise"),
                "cast": {k: v.get("name") for k, v in g.get("cast", {}).items()},
            }
        )
    return out


def scenario_path(replay_dir: Path, scenario: str) -> Path | None:
    if not scenario or "/" in scenario or ".." in scenario:
        return None
    p = replay_dir / f"{scenario}.wav"
    return p if p.exists() else None


def create_app(settings: Settings | None = None, store: Store | None = None, factory=CodeSession) -> FastAPI:
    settings = settings or get_settings()
    store = store or Store(settings.database_path)
    manager = SessionManager(settings, store, factory)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        purge_old_audio(settings)
        yield
        await manager.stop_all()

    app = FastAPI(title="CodeLoop", version="0.1.0", lifespan=lifespan)
    app.state.manager = manager
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_methods=["*"], allow_headers=["*"])

    def check_token(token: str | None) -> None:
        expected = settings.access_token.get_secret_value() if settings.access_token else ""
        if expected and not (token and secrets.compare_digest(token, expected)):
            raise HTTPException(401, "Access code required")

    def auth(
        authorization: Annotated[str | None, Header()] = None, token: Annotated[str | None, Query()] = None
    ) -> None:
        bearer = authorization.removeprefix("Bearer ").strip() if authorization else None
        check_token(bearer or token)

    Auth = Depends(auth)

    @app.get("/api/health")
    async def health() -> dict:
        return {
            "ok": True,
            "assemblyai_key": settings.has_api_key,
            "active_codes": len(manager.active()),
            "auth_required": bool(settings.access_token and settings.access_token.get_secret_value()),
        }

    @app.get("/api/scenarios", dependencies=[Auth])
    async def scenarios() -> list[dict]:
        return list_scenarios(settings.replay_dir)

    @app.post("/api/codes", dependencies=[Auth])
    async def create_code(body: CreateCode) -> dict:
        if not settings.has_api_key:
            raise HTTPException(503, "Server has no AssemblyAI API key configured")
        s = await manager.create(body.mode, body.scenario)
        return {"id": s.id, "mode": s.mode, "scenario": s.scenario}

    @app.get("/api/codes", dependencies=[Auth])
    async def list_codes() -> list[dict]:
        return store.list_codes()

    @app.get("/api/codes/{code_id}", dependencies=[Auth])
    async def get_code(code_id: str) -> dict:
        s = manager.get(code_id)
        if s and not s.closed:
            return {"live": True, "state": s.state()}
        meta = store.get_code(code_id)
        if meta is None:
            raise HTTPException(404, "No such code")
        return {"live": False, "code": meta}

    @app.get("/api/codes/{code_id}/record", dependencies=[Auth])
    async def record(code_id: str) -> dict:
        try:
            return await asyncio.to_thread(build_record, store, code_id)
        except KeyError:
            raise HTTPException(404, "No such code") from None

    @app.get("/api/codes/{code_id}/audit", dependencies=[Auth])
    async def audit(code_id: str) -> dict:
        if store.get_code(code_id) is None:
            raise HTTPException(404, "No such code")
        ok, bad = store.verify(code_id)
        return {"chain_valid": ok, "first_bad_entry": bad, "entries": [e.__dict__ for e in store.entries(code_id)]}

    @app.post("/api/codes/{code_id}/control", dependencies=[Auth])
    async def control(code_id: str, body: dict[str, Any]) -> dict:
        s = manager.get(code_id)
        if s is None or s.closed:
            raise HTTPException(404, "Code is not running")
        await s.handle_control(body, actor="api")
        return {"ok": True}

    @app.websocket("/ws/codes/{code_id}")
    async def code_socket(ws: WebSocket, code_id: str, token: str | None = None) -> None:
        try:
            check_token(token)
        except HTTPException:
            await ws.close(code=4401, reason="Access code required")
            return
        s = manager.get(code_id)
        if s is None or s.closed:
            await ws.close(code=4404, reason="Code is not running")
            return
        await ws.accept()
        await s.subscribe(ws)
        try:
            while True:
                msg = await ws.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if msg.get("bytes") is not None:
                    if s.mode == "live":
                        await s.feed_audio(msg["bytes"])
                elif msg.get("text"):
                    try:
                        await s.handle_control(json.loads(msg["text"]))
                    except (ValueError, KeyError) as e:
                        await ws.send_json({"type": "error", "message": f"Bad control message: {e}"})
        except WebSocketDisconnect:
            pass
        finally:
            s.unsubscribe(ws)

    @app.websocket("/ws/debrief/{code_id}")
    async def debrief_socket(ws: WebSocket, code_id: str, token: str | None = None) -> None:
        """Spoken post-code debrief: browser mic <-> AssemblyAI Voice Agent (see debrief.py)."""
        try:
            check_token(token)
        except HTTPException:
            await ws.close(code=4401, reason="Access code required")
            return
        meta = store.get_code(code_id)
        if meta is None or meta["status"] != "ended":
            await ws.close(code=4404, reason="Debrief is available once the code has ended")
            return
        await ws.accept()
        session = DebriefSession(code_id, settings, store, ws.send_json, ws.send_bytes)
        try:
            await session.start()
            while True:
                msg = await ws.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if msg.get("bytes") is not None:
                    session.feed_audio(msg["bytes"])
                elif msg.get("text") and json.loads(msg["text"]).get("type") == "end":
                    break
        except WebSocketDisconnect:
            pass
        except Exception as e:
            log.exception("debrief failed")
            with contextlib.suppress(Exception):
                await ws.send_json({"type": "error", "message": f"Debrief could not start: {e}"})
        finally:
            await session.close()
            await asyncio.to_thread(store.append, code_id, "debrief_ended", {})

    dist = settings.frontend_dist
    if dist.exists():
        app.mount("/assets", ImmutableStaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str):
            f = dist / path
            if path and f.is_file() and dist in f.resolve().parents:
                return FileResponse(f, headers={"Cache-Control": "no-cache"})
            # index.html must never be cached, or a deploy keeps serving the old bundle.
            return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})
    else:

        @app.get("/", include_in_schema=False)
        async def root() -> JSONResponse:
            return JSONResponse({"service": "codeloop", "frontend": "not built"})

    return app
