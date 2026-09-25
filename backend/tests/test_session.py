"""CodeSession orchestration with fake ears and voice (no network)."""

from __future__ import annotations

import asyncio

import pytest

from codeloop.aai.voice import Line
from codeloop.config import Settings
from codeloop.domain.models import LoopState
from codeloop.session import CodeSession
from codeloop.store import Store


class FakeEars:
    def __init__(self, settings, formulary, on_message) -> None:
        self.on_message = on_message
        self.clock = 0.0
        self.connected = asyncio.Event()
        self.connected.set()
        self.sent = 0

    @property
    def audio_clock_s(self) -> float:
        return self.clock

    async def start(self) -> None: ...
    async def close(self) -> None: ...
    async def force_endpoint(self) -> None: ...

    async def send_audio(self, pcm: bytes) -> None:
        self.sent += len(pcm)


class FakeVoice:
    def __init__(self, settings, on_audio, on_event) -> None:
        self.on_event = on_event
        self.said: list[Line] = []
        self.ready = asyncio.Event()
        self.ready.set()
        self.speaking = False

    async def start(self) -> None: ...
    async def close(self) -> None: ...

    def feed_room_audio(self, pcm: bytes) -> None: ...

    async def say(self, line: Line) -> None:
        self.said.append(line)


class Screen:
    def __init__(self) -> None:
        self.json: list[dict] = []
        self.bytes: list[bytes] = []

    async def send_json(self, data) -> None:
        self.json.append(data)

    async def send_bytes(self, data: bytes) -> None:
        self.bytes.append(data)

    def of(self, t: str) -> list[dict]:
        return [m for m in self.json if m.get("type") == t]


def turn(order: int, speaker: str, words: list[tuple[str, float]], conf: float = 0.95) -> dict:
    return {
        "type": "Turn",
        "turn_order": order,
        "end_of_turn": True,
        "speaker_label": speaker,
        "transcript": " ".join(w for w, _ in words),
        "words": [
            {"text": w, "start": int(t * 1000), "end": int(t * 1000) + 250, "confidence": conf, "speaker": speaker}
            for w, t in words
        ],
    }


def said(text: str, speaker: str, start: float, order: int) -> dict:
    return turn(order, speaker, [(w, start + i * 0.3) for i, w in enumerate(text.split())])


@pytest.fixture
async def session():
    s = CodeSession(
        "c1", Settings(assemblyai_api_key="x"), Store(":memory:"), ears_factory=FakeEars, voice_factory=FakeVoice
    )
    await s.start()
    for t in s._tasks:  # drive time manually in tests
        t.cancel()
    s._tasks.clear()
    yield s
    s.closed = True


async def step(s: CodeSession, until: float, dt: float = 0.25) -> None:
    while s.ears.clock < until:
        s.ears.clock = round(s.ears.clock + dt, 3)
        out = s.pipeline.advance(s.clock)
        if not out.empty:
            await s._handle_output(out)
        await s._speak_next()


async def test_unacknowledged_order_is_spoken_when_the_room_is_quiet(session: CodeSession) -> None:
    screen = Screen()
    await session.subscribe(screen)
    session.ears.clock = 1.0
    await session._on_ears(said("Starting CPR now.", "A", 0.2, 0))
    session.ears.clock = 31.5
    await session._on_ears(said("Give one milligram of epinephrine.", "A", 30.0, 1))
    await step(session, 44.0)
    assert not session.voice.said  # still within 15 s
    # The room keeps talking at 45-46 s; CodeLoop waits for a gap but at most 4 s.
    session._room_speech_clock = 45.9
    await step(session, 46.0)
    assert not session.voice.said
    await step(session, 47.0)
    assert [x.text for x in session.voice.said] == ["Epinephrine one milligram ordered. Not acknowledged."]
    assert screen.of("flag")[0]["flag"]["rule"] == "LOOP_UNACKNOWLEDGED"
    ok, bad = session.store.verify("c1")
    assert ok, bad


async def test_question_to_codeloop_gets_a_deterministic_answer(session: CodeSession) -> None:
    session.ears.clock = 1.0
    await session._on_ears(said("Starting CPR now.", "A", 0.2, 0))
    session.ears.clock = 55.0
    await session._on_ears(said("Epi one milligram is in.", "B", 52.0, 1))
    session.ears.clock = 243.0
    await session._on_ears(said("CodeLoop, last epi kab diya tha?", "C", 241.0, 2))
    await step(session, 245.0)
    texts = [x.text for x in session.voice.said]
    assert any(t.startswith("Last epinephrine, one milligram, three minutes") for t in texts), texts


async def test_codeloops_own_voice_is_not_logged_as_the_team(session: CodeSession) -> None:
    session.ears.clock = 1.0
    await session._on_ears(said("Starting CPR now.", "A", 0.2, 0))
    session._enqueue(
        Line(id="P9", text="Two minutes. Pause compressions for rhythm and pulse check."), 2, "CPR_CYCLE_DUE", "prompt"
    )
    session._room_speech_clock = -10
    await step(session, 10.0)
    assert session.voice.said
    await session._on_agent_event({"type": "agent_done", "line_id": "P9"})
    session.ears.clock = 14.0
    await session._on_ears(said("Two minutes. Pause compressions for rhythm and pulse check.", "D", 9.5, 1))
    assert session._utterances[-1]["echo"] is True
    assert session.engine.cpr_running  # the echoed "pause compressions" did not pause CPR


async def test_screen_confirmation_resolves_a_conflict(session: CodeSession) -> None:
    session.ears.clock = 1.0
    await session._on_ears(said("Starting CPR now.", "A", 0.2, 0))
    session.ears.clock = 62.0
    await session._on_ears(said("Amiodarone three hundred milligrams.", "A", 58.0, 1))
    await session._on_ears(said("Amio one fifty, pushing.", "B", 60.5, 2))
    lp = next(iter(session.engine.loops.values()))
    assert lp.state == LoopState.CONFLICT
    await session.handle_control({"type": "confirm_loop", "loop_id": lp.id, "value": 300})
    assert lp.state == LoopState.ACKNOWLEDGED and lp.ordered_value == 300
    kinds = [e.kind for e in session.store.entries("c1")]
    assert "control" in kinds and "loop" in kinds


async def test_mute_clears_and_blocks_speech(session: CodeSession) -> None:
    session._enqueue(Line(id="P1", text="Fifteen seconds to rhythm check."), 1, "CPR_CYCLE_WARN", "prompt")
    await session.handle_control({"type": "mute", "seconds": 30})
    await step(session, 5.0)
    assert not session.voice.said
    assert session.state()["muted"] is True


async def test_stale_timer_prompts_are_dropped_not_spoken_late(session: CodeSession) -> None:
    session.voice.speaking = True  # CodeLoop is busy for a long time
    session._enqueue(Line(id="P1", text="Fifteen seconds to rhythm check."), 1, "CPR_CYCLE_WARN", "prompt")
    await step(session, 9.0)
    session.voice.speaking = False
    await step(session, 10.0)
    assert not session.voice.said
    assert any(e.kind == "line_dropped" for e in session.store.entries("c1"))
