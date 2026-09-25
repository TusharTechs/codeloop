"""AssemblyAI Voice Agent API client: CodeLoop's voice.

Design (from the day-1 spikes, docs/spike-findings.md):
- The agent never hears the room. It receives silence, except while it is speaking one of
  our lines, when room audio is forwarded so its semantic barge-in can stop it the moment a
  clinician talks over it.
- It only ever says text we give it: reply.create("Say exactly: ..."). Replies we did not
  request (e.g. the agent answering the words that interrupted it) are muted and never
  reach the room.
- If the socket drops, the session is resumed within AssemblyAI's 30 s grace window;
  otherwise a new session is opened. Lines queued meanwhile are spoken after reconnecting.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import soxr
import websockets

from ..config import Settings

log = logging.getLogger(__name__)

AGENT_RATE = 24_000
ROOM_RATE = 16_000
FRAME_MS = 50
FRAME_BYTES = AGENT_RATE * FRAME_MS // 1000 * 2

SYSTEM_PROMPT = (
    "You are the voice of CodeLoop, the recorder at an in-hospital cardiac arrest. You only ever "
    "speak the exact sentence you are instructed to say, word for word, with nothing added. You "
    "never answer questions yourself, never add advice, and never speak unless instructed."
)

AudioHandler = Callable[[bytes, str], Awaitable[None]]  # pcm16 24 kHz, line id
EventHandler = Callable[[dict], Awaitable[None]]
Connector = Callable[..., Any]


@dataclass
class Line:
    id: str
    text: str
    queued_at: float = field(default_factory=time.monotonic)


def resample_16k_to_24k(pcm: bytes) -> bytes:
    if not pcm:
        return b""
    x = np.frombuffer(pcm, dtype=np.int16)
    y = soxr.resample(x, ROOM_RATE, AGENT_RATE)
    return np.asarray(y, dtype=np.int16).tobytes()


class VoiceAgent:
    def __init__(
        self,
        settings: Settings,
        on_audio: AudioHandler,
        on_event: EventHandler,
        connect: Connector = websockets.connect,
    ) -> None:
        self.settings = settings
        self.on_audio = on_audio
        self.on_event = on_event
        self._connect = connect
        self._ws: Any = None
        self._requested: deque[Line] = deque()  # reply.create sent, reply.started not yet seen
        self._replies: dict[str, Line | None] = {}  # reply_id → our line (None = unsolicited)
        self._speaking: Line | None = None
        self._room = bytearray()  # 24 kHz room audio to forward while speaking
        self._tasks: list[asyncio.Task] = []
        self._closing = False
        self._resume_token: str | None = None
        self.session_id: str | None = None
        self.ready = asyncio.Event()
        self.errors: list[str] = []
        self._outbox: deque[Line] = deque()  # lines waiting for a connection

    @property
    def speaking(self) -> bool:
        return self._speaking is not None

    async def start(self) -> None:
        await self._open(resume=False)

    async def say(self, line: Line) -> None:
        """Speak `line.text` verbatim. Lines are spoken one at a time, in order."""
        if not self.ready.is_set():
            self._outbox.append(line)
            return
        self._requested.append(line)
        instructions = f'Say exactly the following, word for word, and nothing else: "{line.text}"'
        await self._send({"type": "reply.create", "instructions": instructions})

    def feed_room_audio(self, pcm16k: bytes) -> None:
        """Room audio (16 kHz). Kept only while CodeLoop is speaking, for barge-in."""
        if self._speaking is not None:
            self._room += resample_16k_to_24k(pcm16k)
            if len(self._room) > AGENT_RATE * 2 * 5:
                del self._room[: len(self._room) - AGENT_RATE * 2 * 5]
        else:
            self._room.clear()

    async def close(self) -> None:
        self._closing = True
        with contextlib.suppress(Exception):
            await self._send({"type": "session.end"})
        for t in self._tasks:
            t.cancel()
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()

    # ---------------------------------------------------------------- internals

    async def _open(self, resume: bool) -> None:
        headers = {"Authorization": f"Bearer {self.settings.assemblyai_api_key.get_secret_value()}"}
        self._ws = await self._connect(
            self.settings.agent_url, additional_headers=headers, max_size=None, open_timeout=10
        )
        if resume and self.session_id:
            await self._ws.send(json.dumps({"type": "session.resume", "session_id": self.session_id}))
        else:
            await self._ws.send(
                json.dumps(
                    {
                        "type": "session.update",
                        "session": {
                            "system_prompt": SYSTEM_PROMPT,
                            "input": {
                                "format": {"encoding": "audio/pcm"},
                                "turn_detection": {"interrupt_response": True},
                            },
                            "output": {"voice": self.settings.agent_voice},
                        },
                    }
                )
            )
        self._tasks = [
            asyncio.create_task(self._receive(self._ws), name="voice-receive"),
            asyncio.create_task(self._pump(), name="voice-pump"),
        ]

    async def _send(self, msg: dict) -> None:
        if self._ws is None:
            return
        try:
            await self._ws.send(json.dumps(msg))
        except websockets.ConnectionClosed:
            self._on_disconnect()

    async def _pump(self) -> None:
        """Real-time 50 ms frames: forwarded room audio while speaking, silence otherwise."""
        await self.ready.wait()
        silence = b"\x00" * FRAME_BYTES
        start = time.perf_counter()
        n = 0
        while not self._closing:
            if self._speaking is not None and len(self._room) >= FRAME_BYTES:
                frame = bytes(self._room[:FRAME_BYTES])
                del self._room[:FRAME_BYTES]
            else:
                frame = silence
            await self._send({"type": "input.audio", "audio": base64.b64encode(frame).decode()})
            n += 1
            await asyncio.sleep(max(0.0, start + n * FRAME_MS / 1000 - time.perf_counter()))

    async def _receive(self, ws: Any) -> None:
        try:
            async for raw in ws:
                msg = json.loads(raw)
                await self._handle(msg)
        except websockets.ConnectionClosed as e:
            self.errors.append(f"voice socket closed {e.code}")
        finally:
            if not self._closing:
                self._on_disconnect()

    async def _handle(self, msg: dict) -> None:
        t = msg.get("type")
        if t == "session.ready":
            self.session_id = msg.get("session_id")
            self._resume_token = msg.get("resume_token")
            self.ready.set()
            while self._outbox:
                await self.say(self._outbox.popleft())
        elif t == "reply.started":
            rid = msg.get("reply_id", "")
            line = self._requested.popleft() if self._requested else None
            self._replies[rid] = line
            if line is not None:
                self._speaking = line
                await self.on_event({"type": "agent_speaking", "line_id": line.id, "text": line.text})
        elif t == "reply.audio":
            rid = msg.get("reply_id") or self._current_reply_id()
            line = self._replies.get(rid) if rid else self._speaking
            if line is not None:
                await self.on_audio(base64.b64decode(msg["data"]), line.id)
        elif t == "transcript.agent":
            line = self._replies.get(msg.get("reply_id", ""))
            if line is not None:
                await self.on_event(
                    {
                        "type": "agent_said",
                        "line_id": line.id,
                        "text": msg.get("text", ""),
                        "interrupted": bool(msg.get("interrupted")),
                    }
                )
        elif t == "reply.done":
            line = self._replies.get(msg.get("reply_id", ""))
            if line is not None:
                interrupted = msg.get("status") == "interrupted"
                await self.on_event({"type": "agent_interrupted" if interrupted else "agent_done", "line_id": line.id})
                if self._speaking is line:
                    self._speaking = None
                    self._room.clear()
        elif t == "session.error":
            self.errors.append(f"{msg.get('code')}: {msg.get('message')}")
            log.warning("voice agent error: %s", msg)
            await self.on_event({"type": "agent_error", "code": msg.get("code"), "message": msg.get("message")})

    def _current_reply_id(self) -> str | None:
        for rid, line in reversed(self._replies.items()):
            if line is self._speaking:
                return rid
        return None

    def _on_disconnect(self) -> None:
        if self._closing or not self.ready.is_set():
            return
        self.ready.clear()
        if self._speaking is not None:
            self._speaking = None
        asyncio.get_running_loop().create_task(self._reconnect(), name="voice-reconnect")

    async def _reconnect(self) -> None:
        for t in self._tasks:
            t.cancel()
        delay = 0.5
        deadline = time.monotonic() + 25  # inside AssemblyAI's 30 s resume window
        while not self._closing:
            resume = time.monotonic() < deadline and self.session_id is not None
            try:
                await self._open(resume=resume)
                await asyncio.wait_for(self.ready.wait(), 10)
                return
            except Exception as e:
                self.errors.append(f"voice reconnect failed: {e!r}")
                if resume and time.monotonic() >= deadline:
                    self.session_id = None
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8.0)
