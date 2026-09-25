from __future__ import annotations

import json
import wave

import pytest
from fastapi.testclient import TestClient
from test_session import FakeEars, FakeVoice

from codeloop.api.app import create_app
from codeloop.config import Settings
from codeloop.session import CodeSession
from codeloop.store import Store


def fake_session(*args, **kwargs) -> CodeSession:
    return CodeSession(*args, ears_factory=FakeEars, voice_factory=FakeVoice, **kwargs)


@pytest.fixture
def replay_dir(tmp_path):
    with wave.open(str(tmp_path / "tiny.ward.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16_000)
        w.writeframes(b"\x00\x00" * 16_000)
    (tmp_path / "tiny.ward.gold.json").write_text(
        json.dumps({"title": "Tiny", "duration_s": 1.0, "noise": "ward", "cast": {"leader": {"name": "Dr. X"}}})
    )
    return tmp_path


def make_client(replay_dir, token: str | None = None) -> TestClient:
    settings = Settings(
        assemblyai_api_key="k", replay_dir=replay_dir, access_token=token, frontend_dist=replay_dir / "nope"
    )
    return TestClient(create_app(settings, Store(":memory:"), factory=fake_session))


def test_health_and_scenarios(replay_dir) -> None:
    with make_client(replay_dir) as c:
        assert c.get("/api/health").json()["assemblyai_key"] is True
        assert c.get("/api/scenarios").json() == [
            {"id": "tiny.ward", "title": "Tiny", "duration_s": 1.0, "noise": "ward", "cast": {"leader": "Dr. X"}}
        ]


def test_live_code_socket_controls_and_record(replay_dir) -> None:
    with make_client(replay_dir) as c:
        code = c.post("/api/codes", json={"mode": "live"}).json()
        with c.websocket_connect(f"/ws/codes/{code['id']}") as ws:
            hello = ws.receive_json()
            assert hello["type"] == "hello" and hello["state"]["mode"] == "live"
            ws.send_bytes(b"\x00\x00" * 1600)
            ws.send_text(json.dumps({"type": "manual_event", "kind": "cpr_start"}))
            ws.send_text(
                json.dumps(
                    {
                        "type": "manual_event",
                        "kind": "done",
                        "action": "drug",
                        "drug": "epinephrine",
                        "dose": 1,
                        "unit": "mg",
                    }
                )
            )
            ws.send_text(json.dumps({"type": "ask", "text": "CodeLoop, last epi?"}))
            msgs = [ws.receive_json() for _ in range(8)]
            assert any(m["type"] == "answer" and m["text"].startswith("Last epinephrine, one milligram") for m in msgs)
            ws.send_text(json.dumps({"type": "not-a-control"}))
            assert ws.receive_json()["type"] in ("error", "state")
        rec = c.get(f"/api/codes/{code['id']}/record").json()
        assert rec["integrity"]["chain_valid"] is True
        assert rec["administered"][0]["what"] == "epinephrine 1 mg"
        assert rec["administered"][0]["without_order"] is True


def test_replay_requires_known_scenario(replay_dir) -> None:
    with make_client(replay_dir) as c:
        assert c.post("/api/codes", json={"mode": "replay", "scenario": "../etc/passwd"}).status_code == 404
        assert c.post("/api/codes", json={"mode": "replay", "scenario": "tiny.ward"}).status_code == 200


def test_access_token_is_enforced(replay_dir) -> None:
    with make_client(replay_dir, token="s3cret") as c:
        assert c.get("/api/scenarios").status_code == 401
        assert c.get("/api/scenarios", headers={"Authorization": "Bearer s3cret"}).status_code == 200
        code = c.post("/api/codes", json={"mode": "live"}, params={"token": "s3cret"}).json()
        with pytest.raises(Exception):  # noqa: B017 - starlette raises on a rejected socket
            with c.websocket_connect(f"/ws/codes/{code['id']}") as ws:
                ws.receive_json()


def test_index_is_never_cached_but_hashed_assets_are(tmp_path) -> None:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>")
    (dist / "assets" / "index-abc123.js").write_text("console.log(1)")
    settings = Settings(assemblyai_api_key="k", replay_dir=tmp_path, frontend_dist=dist)
    with TestClient(create_app(settings, Store(":memory:"), factory=fake_session)) as c:
        assert c.get("/").headers["cache-control"] == "no-cache"
        assert c.get("/some/route").headers["cache-control"] == "no-cache"
        assert "immutable" in c.get("/assets/index-abc123.js").headers["cache-control"]
