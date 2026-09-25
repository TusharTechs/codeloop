"""AssemblyAI Universal-3.5 Pro streaming client: CodeLoop's ears on the room.

- Audio is PCM16 mono 16 kHz, sent in 100 ms chunks (AssemblyAI accepts 50-1000 ms).
- If the socket drops, audio keeps buffering (up to `max_buffer_s`), the client reconnects
  with backoff, and word timestamps / turn numbers from the new session are shifted so the
  code clock and the transcript stay continuous.
- `update_keyterms` swaps the vocabulary mid-code (e.g. after a patient's allergies load).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlencode

import websockets

from ..config import Settings
from ..domain.formulary import Formulary

log = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
CHUNK_BYTES = SAMPLE_RATE // 10 * 2  # 100 ms of PCM16

CONTEXT_PROMPT = (
    "Audio from an in-hospital cardiac arrest (code blue), captured by a tablet on the crash cart. "
    "Several clinicians talk over monitor alarms and chest compressions: a team leader giving "
    "orders, a medication nurse reading doses back, a compressor, and an airway clinician. Speech "
    "contains ACLS drug names and doses such as epinephrine 1 milligram and amiodarone 300 or 150 "
    "milligrams, defibrillation energies in joules, rhythms such as VF, pulseless VT, PEA and "
    "asystole, and Hindi-English code-switching. Doses and numbers are safety-critical and are "
    "spoken exactly."
)

MessageHandler = Callable[[dict], Awaitable[None]]
Connector = Callable[..., Any]


def build_params(settings: Settings, formulary: Formulary) -> dict[str, Any]:
    p: dict[str, Any] = {
        "speech_model": settings.speech_model,
        "sample_rate": SAMPLE_RATE,
        "encoding": "pcm_s16le",
        "speaker_labels": "true",
        "max_speakers": settings.max_speakers,
        "language_detection": "true",
        "min_turn_silence": settings.min_turn_silence_ms,
        "max_turn_silence": settings.max_turn_silence_ms,
        "keyterms_prompt": json.dumps(formulary.keyterms()),
        "prompt": CONTEXT_PROMPT,
    }
    if settings.language_codes:
        p["language_codes"] = json.dumps(settings.language_codes)
    if settings.medical_mode:
        p["domain"] = "medical-v1"
    if settings.voice_focus:
        p["voice_focus"] = settings.voice_focus
    return p


class StreamingEars:
    def __init__(
        self,
        settings: Settings,
        formulary: Formulary,
        on_message: MessageHandler,
        connect: Connector = websockets.connect,
        max_buffer_s: float = 30.0,
    ) -> None:
        self.settings = settings
        self.formulary = formulary
        self.on_message = on_message
        self._connect = connect
        self._max_buffer = int(max_buffer_s * SAMPLE_RATE * 2)
        self._ws: Any = None
        self._pending = bytearray()  # audio not yet sent (partial chunk or while disconnected)
        self._sent_bytes = 0  # audio delivered to the current session
        self._offset_ms = 0  # audio clock at the start of the current session
        self._turn_base = 0
        self._session_index = 0
        self._recv_task: asyncio.Task | None = None
        self._closing = False
        self._reconnecting = False
        self.connected = asyncio.Event()
        self.session_id: str | None = None
        self.errors: list[str] = []

    @property
    def audio_clock_s(self) -> float:
        """Seconds of room audio received so far (the code clock's time base)."""
        return (self._offset_ms / 1000) + (self._sent_bytes + len(self._pending)) / 2 / SAMPLE_RATE

    async def start(self) -> None:
        await self._open()

    async def _open(self) -> None:
        url = f"{self.settings.streaming_url}?{urlencode(build_params(self.settings, self.formulary))}"
        headers = {"Authorization": self.settings.assemblyai_api_key.get_secret_value()}
        self._ws = await self._connect(url, additional_headers=headers, max_size=None, open_timeout=10)
        self.connected.set()
        self._recv_task = asyncio.create_task(self._receive(self._ws), name="ears-receive")

    async def send_audio(self, pcm: bytes) -> None:
        self._pending += pcm
        if len(self._pending) > self._max_buffer:
            dropped = len(self._pending) - self._max_buffer
            del self._pending[:dropped]
            self._offset_ms += dropped * 1000 // (2 * SAMPLE_RATE)
            self.errors.append(f"dropped {dropped / 2 / SAMPLE_RATE:.1f}s of audio while disconnected")
        if not self.connected.is_set():
            return
        while len(self._pending) >= CHUNK_BYTES:
            chunk = bytes(self._pending[:CHUNK_BYTES])
            try:
                await self._ws.send(chunk)
            except websockets.ConnectionClosed:
                self._on_disconnect()
                return
            del self._pending[:CHUNK_BYTES]
            self._sent_bytes += CHUNK_BYTES

    async def update_keyterms(self, terms: list[str]) -> None:
        if self._ws is not None and self.connected.is_set():
            await self._ws.send(json.dumps({"type": "UpdateConfiguration", "keyterms_prompt": terms[:100]}))

    async def force_endpoint(self) -> None:
        if self._ws is not None and self.connected.is_set():
            await self._ws.send(json.dumps({"type": "ForceEndpoint"}))

    async def close(self) -> None:
        self._closing = True
        if self._ws is not None and self.connected.is_set():
            with contextlib.suppress(Exception):
                if self._pending:
                    await self._ws.send(bytes(self._pending))
                    self._pending.clear()
                await self._ws.send(json.dumps({"type": "Terminate"}))
            if self._recv_task:
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(self._recv_task, 5)
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()

    # ---------------------------------------------------------------- internals

    async def _receive(self, ws: Any) -> None:
        try:
            async for raw in ws:
                if isinstance(raw, bytes):
                    continue
                msg = json.loads(raw)
                if msg.get("type") == "Begin":
                    self.session_id = msg.get("id")
                self._shift(msg)
                await self.on_message(msg)
                if msg.get("type") == "Termination":
                    return
        except websockets.ConnectionClosed as e:
            log.warning("streaming socket closed: code=%s reason=%s", e.code, e.reason)
            self.errors.append(f"socket closed {e.code}")
        finally:
            if not self._closing:
                self._on_disconnect()

    def _shift(self, msg: dict) -> None:
        """Rebase timestamps and turn numbers from a reconnected session onto the code clock."""
        if self._offset_ms == 0 and self._turn_base == 0:
            return
        if msg.get("type") in ("Turn",):
            msg["turn_order"] = int(msg.get("turn_order", 0)) + self._turn_base
            for w in msg.get("words") or []:
                w["start"] = int(w["start"]) + self._offset_ms
                w["end"] = int(w["end"]) + self._offset_ms
        elif msg.get("type") == "SpeakerRevision":
            for rev in msg.get("revisions", []):
                rev["turn_order"] = int(rev.get("turn_order", 0)) + self._turn_base

    def _on_disconnect(self) -> None:
        if self._closing or self._reconnecting:
            return
        self.connected.clear()
        self._reconnecting = True
        asyncio.get_running_loop().create_task(self._reconnect(), name="ears-reconnect")

    async def _reconnect(self) -> None:
        # The new session's clock starts at the first byte it receives.
        self._offset_ms += self._sent_bytes * 1000 // (2 * SAMPLE_RATE)
        self._sent_bytes = 0
        self._session_index += 1
        self._turn_base = self._session_index * 100_000
        delay = 0.5
        try:
            while not self._closing:
                try:
                    await self._open()
                    log.info("streaming reconnected (session %d)", self._session_index)
                    await self.send_audio(b"")  # flush what buffered while we were away
                    return
                except Exception as e:
                    self.errors.append(f"reconnect failed: {e!r}")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 8.0)
        finally:
            self._reconnecting = False
