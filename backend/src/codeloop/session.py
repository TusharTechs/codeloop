"""One live (or replayed) code: room audio → ears → pipeline → engine → screen, voice, audit.

Data flow
    room audio (browser mic or replayed WAV, PCM16 16 kHz)
      ├─► StreamingEars (U3.5 Pro: diarization, Medical Mode, keyterms)
      │      └─► TurnAssembler → utterances → TranscriptPipeline → CodeEngine
      │                                           │
      │               loops / flags / prompts ◄───┘ ──► screens (WebSocket) + audit log
      └─► VoiceAgent (only while CodeLoop is speaking, for barge-in)

Prompt scheduling: CodeLoop waits for a gap in the room before speaking (0.6 s of quiet),
but will not wait longer than 1.5 s for safety prompts, 1 s for answers to direct
questions, or 4 s for timer prompts. Stale timer prompts are dropped rather than spoken late.
Nothing is ever spoken while CodeLoop is already speaking, or while prompts are muted.
"""

from __future__ import annotations

import asyncio
import contextlib
import heapq
import itertools
import logging
import time
import wave
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .aai.streaming import SAMPLE_RATE, StreamingEars
from .aai.turns import TurnAssembler
from .aai.voice import Line, VoiceAgent
from .config import Settings
from .domain.models import Action, Event, EventKind, EventSource, PromptPolicy, Role, Utterance
from .engine.answers import answer
from .engine.engine import EngineOutput
from .pipeline import TranscriptPipeline
from .store import Store

log = logging.getLogger(__name__)

ROOM_AUDIO = b"\x01"  # binary frame prefixes sent to screens
AGENT_AUDIO = b"\x02"
QUIET_GAP_S = 0.6
MAX_WAIT_S = {4: 1.0, 3: 1.5, 2: 3.0, 1: 4.0}  # by priority
STALE_S = {4: 8.0, 3: 20.0, 2: 12.0, 1: 8.0}
ECHO_TAIL_S = 0.8
CLOSE_AFTER_END_S = 15.0


class Subscriber(Protocol):
    async def send_json(self, data: Any) -> None: ...
    async def send_bytes(self, data: bytes) -> None: ...


@dataclass(order=True)
class _Queued:
    sort_key: tuple
    line: Line = field(compare=False)
    priority: int = field(compare=False)
    queued_clock: float = field(compare=False)
    rule: str = field(compare=False)
    kind: str = field(compare=False, default="prompt")


@dataclass
class _EchoWindow:
    start_s: float
    end_s: float | None
    text: str


def _similar(a: str, b: str) -> float:
    ta = {w.strip(".,!?").lower() for w in a.split()}
    tb = {w.strip(".,!?").lower() for w in b.split()}
    ta.discard("")
    tb.discard("")
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


class CodeSession:
    def __init__(
        self,
        code_id: str,
        settings: Settings,
        store: Store,
        mode: str = "live",
        scenario: str | None = None,
        ears_factory: Callable[..., StreamingEars] = StreamingEars,
        voice_factory: Callable[..., VoiceAgent] | None = VoiceAgent,
    ) -> None:
        self.id = code_id
        self.settings = settings
        self.store = store
        self.mode = mode
        self.scenario = scenario
        self.pipeline = TranscriptPipeline(policy=settings.prompt_policy, low_confidence=settings.low_confidence)
        self.engine = self.pipeline.engine
        self.assembler = TurnAssembler()
        self.subscribers: set[Subscriber] = set()
        self._ears_factory = ears_factory
        self._voice_factory = voice_factory if settings.agent_enabled else None
        self.ears: StreamingEars | None = None
        self.voice: VoiceAgent | None = None
        self._queue: list[_Queued] = []
        self._seq = itertools.count()
        self._answers = itertools.count(1)
        self._echo: list[_EchoWindow] = []
        self._room_speech_clock = -10.0
        self._muted_until = -1.0
        self._tasks: list[asyncio.Task] = []
        self._utterances: list[dict] = []
        self._spoken: list[dict] = []
        self._latency_ms: list[float] = []
        self._started_wall = time.monotonic()
        self._last_state_push = 0.0
        self.closed = False
        self._closer: asyncio.Task | None = None
        self.voice_status = "off"
        self.ears_status = "connecting"

    # ================================================================ lifecycle

    async def start(self, replay_path: Path | None = None) -> None:
        self.store.create_code(self.id, self.mode, self.scenario)
        await self._audit(
            "code_started",
            {
                "mode": self.mode,
                "scenario": self.scenario,
                "policy": self.engine.policy.value,
                "formulary": self.engine.f.version,
            },
        )
        self.ears = self._ears_factory(self.settings, self.engine.f, self._on_ears)
        await self.ears.start()
        self.ears_status = "live"
        if self._voice_factory is not None:
            try:
                self.voice = self._voice_factory(self.settings, self._on_agent_audio, self._on_agent_event)
                await self.voice.start()
                self.voice_status = "ready"
            except Exception as e:
                log.warning("voice agent unavailable: %r", e)
                self.voice = None
                self.voice_status = "unavailable"
                await self._audit("voice_unavailable", {"error": repr(e)})
        self._tasks.append(asyncio.create_task(self._tick_loop(), name=f"tick-{self.id}"))
        if replay_path is not None:
            self._tasks.append(asyncio.create_task(self._replay(replay_path), name=f"replay-{self.id}"))
        await self.push_state(force=True)

    async def _close_after(self, seconds: float) -> None:
        await self.broadcast({"type": "closing", "in_s": seconds})
        await asyncio.sleep(seconds)
        await self.stop()

    async def stop(self) -> None:
        if self.closed:
            return
        self.closed = True
        for t in self._tasks:
            t.cancel()
        if self.ears:
            await self.ears.close()
        if self.voice:
            await self.voice.close()
        summary = self.summary()
        await self._audit("code_closed", summary)
        self.store.finish_code(self.id, "ended", self.engine.outcome, summary)
        await self.broadcast({"type": "closed", "summary": summary})

    @property
    def clock(self) -> float:
        return self.ears.audio_clock_s if self.ears else 0.0

    # ================================================================ audio in

    async def feed_audio(self, pcm: bytes) -> None:
        if self.closed or self.ears is None:
            return
        if self.clock > self.settings.max_code_minutes * 60:
            await self.broadcast({"type": "error", "message": "Maximum code length reached; capture stopped."})
            await self.stop()
            return
        await self.ears.send_audio(pcm)
        if self.voice is not None:
            self.voice.feed_room_audio(pcm)

    async def _replay(self, path: Path) -> None:
        """Stream a recorded mock code through the live pipeline at real-time pace."""
        try:
            with wave.open(str(path)) as w:
                if w.getframerate() != SAMPLE_RATE or w.getnchannels() != 1 or w.getsampwidth() != 2:
                    raise ValueError("replay audio must be 16 kHz mono PCM16")
                pcm = w.readframes(w.getnframes())
            chunk = SAMPLE_RATE // 10 * 2
            start = time.perf_counter()
            for i, off in enumerate(range(0, len(pcm), chunk)):
                if self.closed:
                    return
                piece = pcm[off : off + chunk]
                await self.feed_audio(piece)
                await self._send_all_bytes(ROOM_AUDIO + piece)
                await asyncio.sleep(max(0.0, start + (i + 1) * 0.1 - time.perf_counter()))
            await self.broadcast({"type": "replay_finished"})
            await asyncio.sleep(1.5)
            if self.ears:
                await self.ears.force_endpoint()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.exception("replay failed")
            await self.broadcast({"type": "error", "message": f"Replay failed: {e}"})

    # ================================================================ ears

    async def _on_ears(self, msg: dict) -> None:
        t = msg.get("type")
        if t == "Turn" and not msg.get("end_of_turn"):
            self._room_speech_clock = self.clock
            await self.broadcast(
                {"type": "partial", "text": msg.get("transcript", ""), "speaker": msg.get("speaker_label")}
            )
            return
        if t == "SpeechStarted":
            self._room_speech_clock = self.clock
            return
        if t == "SpeakerRevision":
            self.assembler.feed(msg)
            await self.broadcast(
                {
                    "type": "speaker_revision",
                    "revisions": [
                        {"turn_order": r.get("turn_order"), "speaker": r.get("speaker_label")}
                        for r in msg.get("revisions", [])
                    ],
                }
            )
            return
        if t == "Turn":
            self._room_speech_clock = self.clock
            for u in self.assembler.feed(msg):
                await self._process_utterance(u)

    async def _process_utterance(self, u: Utterance) -> None:
        echo = self._is_echo(u)
        latency = max(0.0, (self.clock - u.end_s) * 1000)
        self._latency_ms = [*self._latency_ms, latency][-200:]
        record = {
            "id": u.id,
            "speaker": u.speaker,
            "role": self._role(u.speaker),
            "text": u.text,
            "start_s": round(u.start_s, 2),
            "end_s": round(u.end_s, 2),
            "language": u.language,
            "min_confidence": round(min((w.confidence for w in u.words), default=1.0), 3),
            "echo": echo,
            "latency_ms": round(latency),
        }
        self._utterances.append(record)
        await self._audit("utterance", record, u.end_s)
        await self.broadcast({"type": "utterance", **record})
        if echo:
            return
        res = self.pipeline.process(u)
        for ev in res.events:
            data = ev.model_dump(mode="json")
            await self._audit("event", data, ev.at_s)
            await self.broadcast({"type": "event", "event": data})
            if ev.kind == EventKind.QUESTION:
                await self._answer(u)
        await self._handle_output(res.output)

    def _is_echo(self, u: Utterance) -> bool:
        """Did the room mic pick up CodeLoop's own voice?"""
        for w in self._echo[-6:]:
            end = (w.end_s if w.end_s is not None else self.clock) + ECHO_TAIL_S
            overlaps = u.start_s <= end and u.end_s >= w.start_s - 0.3
            if overlaps and _similar(u.text, w.text) >= 0.6:
                return True
        return False

    def _role(self, speaker: str | None) -> str | None:
        r = self.engine.role_of(speaker)
        return r.value if r else None

    # ================================================================ engine output

    async def _handle_output(self, out: EngineOutput) -> None:
        for lp in out.loops:
            data = lp.model_dump(mode="json")
            await self._audit("loop", data, lp.history[-1].at_s if lp.history else None)
            await self.broadcast({"type": "loop", "loop": data})
        for fl in out.flags:
            data = fl.model_dump(mode="json")
            await self._audit("flag", data, fl.at_s)
            await self.broadcast({"type": "flag", "flag": data})
        for fl in out.resolved_flags:
            data = fl.model_dump(mode="json")
            await self._audit("flag_resolved", data, fl.resolved_at_s)
            await self.broadcast({"type": "flag_resolved", "flag": data})
        for p in out.prompts:
            self._enqueue(Line(id=p.id, text=p.text), p.priority, p.rule, "prompt")
            await self.broadcast({"type": "prompt", "prompt": p.model_dump(mode="json")})
        if out.state_changed or out.loops or out.flags:
            await self.push_state(force=True)

    async def _answer(self, u: Utterance) -> None:
        a = answer(u, self.engine, self.pipeline.grammar, self.clock)
        line = Line(id=f"A{next(self._answers)}", text=a.text)
        data = {"id": line.id, "question": u.text, "topic": a.topic.value, "text": a.text, "drug": a.drug}
        await self._audit("answer", data, self.clock)
        await self.broadcast({"type": "answer", **data})
        self._enqueue(line, 4, f"ANSWER_{a.topic.value.upper()}", "answer")

    # ================================================================ speaking

    def _enqueue(self, line: Line, priority: int, rule: str, kind: str) -> None:
        heapq.heappush(self._queue, _Queued((-priority, next(self._seq)), line, priority, self.clock, rule, kind))

    async def _speak_next(self) -> None:
        if not self._queue:
            return
        now = self.clock
        # Drop lines that are too old to be useful.
        fresh = []
        for q in self._queue:
            if now - q.queued_clock > STALE_S.get(q.priority, 8.0):
                await self._audit(
                    "line_dropped", {"id": q.line.id, "text": q.line.text, "rule": q.rule, "reason": "stale"}, now
                )
                await self.broadcast({"type": "line_dropped", "id": q.line.id, "reason": "stale"})
            else:
                fresh.append(q)
        self._queue = fresh
        heapq.heapify(self._queue)
        if not self._queue:
            return
        if self.voice is None or not self.voice.ready.is_set() or self.voice.speaking:
            return
        if now < self._muted_until:
            return
        head = self._queue[0]
        quiet = now - self._room_speech_clock >= QUIET_GAP_S
        waited = now - head.queued_clock
        if not quiet and waited < MAX_WAIT_S.get(head.priority, 4.0):
            return
        heapq.heappop(self._queue)
        self._echo = [*self._echo, _EchoWindow(now, None, head.line.text)][-10:]
        await self.voice.say(head.line)
        entry = {
            "id": head.line.id,
            "text": head.line.text,
            "rule": head.rule,
            "kind": head.kind,
            "waited_s": round(waited, 2),
            "room_quiet": quiet,
        }
        self._spoken.append({**entry, "at_s": round(now, 2)})
        await self._audit("spoken", entry, now)

    async def _on_agent_audio(self, pcm: bytes, line_id: str) -> None:
        await self._send_all_bytes(AGENT_AUDIO + pcm)

    async def _on_agent_event(self, ev: dict) -> None:
        t = ev.get("type")
        if t in ("agent_done", "agent_interrupted"):
            for w in reversed(self._echo):
                if w.end_s is None:
                    w.end_s = self.clock
                    break
        if t in ("agent_interrupted", "agent_done", "agent_error"):
            await self._audit(t, ev, self.clock)
        if t == "agent_error":
            self.voice_status = "error"
        await self.broadcast(ev)

    # ================================================================ ticking

    async def _tick_loop(self) -> None:
        try:
            while not self.closed:
                out = self.pipeline.advance(self.clock)
                if not out.empty:
                    await self._handle_output(out)
                await self._speak_next()
                await self.push_state()
                await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("tick loop crashed")
            await self.broadcast({"type": "error", "message": "Engine loop stopped; check the server log."})

    async def push_state(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_state_push < 1.0:
            return
        self._last_state_push = now
        await self.broadcast({"type": "state", "state": self.state()})

    def state(self) -> dict:
        snap = self.engine.snapshot(self.clock)
        lat = sorted(self._latency_ms)
        return {
            **snap,
            "code_id": self.id,
            "mode": self.mode,
            "scenario": self.scenario,
            "audio_clock_s": round(self.clock, 1),
            "policy": self.engine.policy.value,
            "muted": self.clock < self._muted_until,
            "voice": self.voice_status
            if self.voice is None
            else ("speaking" if self.voice.speaking else ("ready" if self.voice.ready.is_set() else "reconnecting")),
            "ears": "live" if self.ears and self.ears.connected.is_set() else "reconnecting",
            "latency_ms": {
                "p50": lat[len(lat) // 2] if lat else None,
                "p90": lat[int(len(lat) * 0.9)] if lat else None,
            },
            "names": {k: v.value for k, v in self.engine.names.items()},
        }

    # ================================================================ controls from the screen

    async def handle_control(self, msg: dict, actor: str = "screen") -> None:
        t = msg.get("type")
        now = self.clock
        await self._audit("control", {**msg, "actor": actor}, now)
        out = EngineOutput()
        if t == "assign_role":
            self.engine.assign_role(str(msg["speaker"]), Role(msg["role"]))
            out.state_changed = True
        elif t == "confirm_loop":
            out = self.engine.confirm_loop(str(msg["loop_id"]), _num(msg.get("value")), now, by=actor)
        elif t == "manual_event":
            out = self._manual_event(msg, now)
        elif t == "confirm_end":
            out = self.engine.confirm_end()
        elif t == "reject_end":
            out = self.engine.reject_end()
        elif t == "end_code":
            out = self.engine.end_code(now, str(msg.get("outcome", "terminated")))
        elif t == "set_policy":
            self.engine.policy = PromptPolicy(msg["policy"])
            out.state_changed = True
        elif t == "mute":
            self._muted_until = now + float(msg.get("seconds", 60))
            self._queue.clear()
            out.state_changed = True
        elif t == "unmute":
            self._muted_until = -1.0
            out.state_changed = True
        elif t == "ask":
            text = str(msg.get("text", ""))[:200]
            await self._answer(
                Utterance(id=f"typed{int(now * 1000)}", turn_order=-1, text=text, start_s=now, end_s=now)
            )
        elif t == "stop":
            await self.stop()
            return
        await self._handle_output(out)
        if self.engine.ended_at_s is not None and self._closer is None:
            # Keep listening briefly so final words and the record flush, then close the code.
            self._closer = asyncio.create_task(self._close_after(CLOSE_AFTER_END_S), name=f"close-{self.id}")

    def _manual_event(self, msg: dict, now: float) -> EngineOutput:
        kind = EventKind(msg["kind"])
        action = Action(msg["action"]) if msg.get("action") else None
        ev = Event(
            id=f"m{int(now * 1000)}",
            kind=kind,
            at_s=now,
            action=action,
            drug=msg.get("drug"),
            dose=_num(msg.get("dose")),
            unit=msg.get("unit"),
            energy_j=_num(msg.get("energy_j")),
            rhythm=msg.get("rhythm"),
            quote="(entered on screen)",
            source=EventSource.MANUAL,
        )
        return self.engine.apply(ev)

    # ================================================================ subscribers

    async def subscribe(self, sub: Subscriber) -> None:
        self.subscribers.add(sub)
        await sub.send_json(
            {
                "type": "hello",
                "state": self.state(),
                "loops": [lp.model_dump(mode="json") for lp in self.engine.loops.values()],
                "flags": [f.model_dump(mode="json") for f in self.engine.flags.values()],
                "events": [e.model_dump(mode="json") for e in self.engine.events[-300:]],
                "utterances": self._utterances[-300:],
                "spoken": self._spoken[-100:],
            }
        )

    def unsubscribe(self, sub: Subscriber) -> None:
        self.subscribers.discard(sub)

    async def broadcast(self, data: dict) -> None:
        dead = []
        for s in list(self.subscribers):
            try:
                await s.send_json(data)
            except Exception:
                dead.append(s)
        for s in dead:
            self.subscribers.discard(s)

    async def _send_all_bytes(self, data: bytes) -> None:
        for s in list(self.subscribers):
            with contextlib.suppress(Exception):
                await s.send_bytes(data)

    async def _audit(self, kind: str, payload: Any, at_code_s: float | None = None) -> None:
        try:
            await self.store.append_async(self.id, kind, payload, at_code_s)
        except Exception:
            log.exception("audit append failed")

    # ================================================================ summary

    def summary(self) -> dict:
        e = self.engine
        loops = list(e.loops.values())
        return {
            "outcome": e.outcome,
            "clock_s": round(e.clock_s(self.clock), 1),
            "shocks": len(e.shocks),
            "drugs_given": len(e.given),
            "loops": len(loops),
            "loops_closed": sum(1 for lp in loops if lp.state.value in ("DONE", "CANCELLED")),
            "loops_unacknowledged_ever": sum(
                1 for lp in loops if any(h.state.value == "UNACKNOWLEDGED" for h in lp.history)
            ),
            "conflicts": sum(1 for lp in loops if any(h.state.value == "CONFLICT" for h in lp.history)),
            "prompts_spoken": len(self._spoken),
            "unresolved_flags": len(e.active_flags()),
            "audit_head": self.store.head_hash(self.id),
        }


def _num(x: Any) -> float | None:
    if x is None or x == "":
        return None
    return float(x)
