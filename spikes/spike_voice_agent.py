"""Spike 2: can the Voice Agent API be CodeLoop's voice?

Opens one Voice Agent session with a CodeLoop system prompt and a `get_code_state` tool,
keeps a real-time audio stream running (silence between tests, like an open mic), and checks:

  T1 prompt      engine-triggered speech via reply.create: latency and exact wording
  T2 question    spoken English question → tool call → grounded answer
  T3 hinglish    spoken Hinglish question → tool call → grounded answer
  T4 barge-in    human speaks over the agent: time until the reply is interrupted
  T5 chatter     room talk not addressed to CodeLoop: does the agent stay quiet?

Agent audio for each test is written to spikes/results/agent_<test>.wav.

    uv run --project backend python spikes/spike_voice_agent.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import tempfile
import time
from pathlib import Path

import websockets
from _common import RESULTS, api_key, read_pcm16, save_json, write_pcm16
from acls_vocab import KEYTERMS

URL = "wss://agents.assemblyai.com/v1/ws"
SR = 24_000
FRAME_MS = 50
FRAME_BYTES = SR * FRAME_MS // 1000 * 2

SYSTEM_PROMPT = """You are CodeLoop, the voice of a recorder at an in-hospital cardiac arrest.
The room is loud and busy. Rules:
- Only respond when someone addresses you as "CodeLoop" or asks you directly about the code
  (times, doses, last drug, what is due). For any other speech, respond with an empty reply.
- Never state a time, dose, rhythm or count unless it came from a get_code_state tool result in
  this conversation. If the tool fails, say "Check the screen."
- Answer in one short sentence in English, even when the question mixes Hindi and English.
- Never recommend treatment. You are a recorder and timekeeper."""

TOOLS = [
    {
        "type": "function",
        "name": "get_code_state",
        "description": "Current state of the code: clock, rhythm, shocks, last drug doses with "
        "time since given, open orders, and which timers are due. Call this before "
        "answering any question about times, doses, drugs, shocks or what is due.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }
]

CODE_STATE = {
    "clock": "04:02",
    "rhythm": "VF",
    "shocks": 1,
    "last_epinephrine": {"dose": "1 mg", "given_at_clock": "00:52", "seconds_ago": 190},
    "last_amiodarone": {"dose": "300 mg", "given_at_clock": "01:10", "seconds_ago": 172},
    "due": ["epinephrine window open (3 to 5 minutes)"],
    "open_orders": [],
}


def tts24(text: str, voice: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "u.wav"
        subprocess.run(
            ["say", "-v", voice, "-r", "180", "-o", str(out), "--file-format=WAVE", "--data-format=LEI16@24000", text],
            check=True,
        )
        pcm, _ = read_pcm16(out)
    return pcm


class Session:
    def __init__(self, ws: websockets.ClientConnection) -> None:
        self.ws = ws
        self.t0 = time.perf_counter()
        self.speech: asyncio.Queue[bytes] = asyncio.Queue()
        self.events: list[dict] = []
        self.audio: bytearray = bytearray()
        self.pending_results: dict[str, str] = {}
        self.audio_replies: set[str | None] = set()
        self.sending_speech = False
        self.ready = asyncio.Event()

    def now(self) -> float:
        return time.perf_counter() - self.t0

    async def pump_audio(self) -> None:
        """Continuous real-time mic: queued speech frames, otherwise low-level room noise."""
        await self.ready.wait()
        start = time.perf_counter()
        n = 0
        buf = b""
        while True:
            if len(buf) < FRAME_BYTES and not self.speech.empty():
                buf += self.speech.get_nowait()
            self.sending_speech = bool(buf) or not self.speech.empty()
            if buf:
                frame, buf = buf[:FRAME_BYTES], buf[FRAME_BYTES:]
                frame = frame.ljust(FRAME_BYTES, b"\x00")
            else:
                frame = b"\x00" * FRAME_BYTES
            await self.ws.send(json.dumps({"type": "input.audio", "audio": base64.b64encode(frame).decode()}))
            n += 1
            await asyncio.sleep(max(0.0, start + n * FRAME_MS / 1000 - time.perf_counter()))

    async def receive(self) -> None:
        async for raw in self.ws:
            msg = json.loads(raw)
            t = msg.get("type")
            if t == "reply.audio":
                self.audio += base64.b64decode(msg["data"])
                rid = msg.get("reply_id") or self.current_reply()
                if rid not in self.audio_replies:  # log only the first chunk of each reply
                    self.audio_replies.add(rid)
                    self.events.append({"type": "reply.audio", "_t": self.now(), "reply_id": rid})
                continue
            msg["_t"] = self.now()
            self.events.append(msg)
            if t == "session.ready":
                self.ready.set()
            elif t == "tool.call":
                args = msg.get("arguments") or {}
                self.pending_results[msg["call_id"]] = json.dumps(
                    CODE_STATE if msg["name"] == "get_code_state" else {"error": "unknown tool"}
                )
                msg["_args"] = args
            elif t == "reply.done":
                if msg.get("status") == "interrupted":
                    self.pending_results.clear()
                for call_id, result in list(self.pending_results.items()):
                    await self.ws.send(json.dumps({"type": "tool.result", "call_id": call_id, "result": result}))
                    del self.pending_results[call_id]
            elif t in ("session.error", "session.ended"):
                if t == "session.ended":
                    return

    def current_reply(self) -> str | None:
        for e in reversed(self.events):
            if e.get("type") == "reply.started":
                return e.get("reply_id")
        return None

    def since(self, t: float) -> list[dict]:
        return [e for e in self.events if e.get("_t", 0) >= t]

    async def wait_for(self, pred, limit_s: float, since: float) -> dict | None:
        end = time.perf_counter() + limit_s
        while time.perf_counter() < end:
            for e in self.since(since):
                if pred(e):
                    return e
            await asyncio.sleep(0.02)
        return None

    async def settle(self, quiet_s: float = 2.0, limit_s: float = 25.0) -> None:
        """Wait until queued speech has streamed, no reply is in progress, and nothing has
        arrived for quiet_s."""
        await asyncio.sleep(0.2)
        end = time.perf_counter() + limit_s
        while time.perf_counter() < end:
            if self.sending_speech or not self.speech.empty():
                await asyncio.sleep(0.1)
                continue
            last = self.events[-1]["_t"] if self.events else 0
            open_replies = {e.get("reply_id") for e in self.events if e.get("type") == "reply.started"}
            done = {e.get("reply_id") for e in self.events if e.get("type") == "reply.done"}
            if self.now() - last > quiet_s and not (open_replies - done):
                return
            await asyncio.sleep(0.1)


def summarize(ev: list[dict], t_start: float) -> dict:
    def first(pred):
        for e in ev:
            if pred(e):
                return round((e["_t"] - t_start) * 1000)
        return None

    return {
        "user_transcripts": [e.get("text") for e in ev if e.get("type") == "transcript.user"],
        "tool_calls": [{"name": e.get("name"), "args": e.get("_args")} for e in ev if e.get("type") == "tool.call"],
        "agent_said": [e.get("text") for e in ev if e.get("type") == "transcript.agent"],
        "interrupted": any(e.get("type") == "reply.done" and e.get("status") == "interrupted" for e in ev),
        "ms_to_first_audio": first(lambda e: e.get("type") == "reply.audio"),
        "ms_to_speech_started": first(lambda e: e.get("type") == "input.speech.started"),
        "ms_to_interrupted": first(lambda e: e.get("type") == "reply.done" and e.get("status") == "interrupted"),
        "errors": [e for e in ev if e.get("type") == "session.error"],
    }


async def main() -> None:
    results: dict[str, dict] = {}
    q_en = tts24("CodeLoop, when was the last epinephrine given?", "Rishi")
    q_hi = tts24("CodeLoop, last epi kab diya tha?", "Lekha")
    stop = tts24("Got it, pausing now.", "Rishi")
    chatter = tts24("Resume compressions. Good depth, keep going.", "Daniel")

    async with websockets.connect(
        URL, additional_headers={"Authorization": f"Bearer {api_key()}"}, max_size=None
    ) as ws:
        s = Session(ws)
        await ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {
                        "system_prompt": SYSTEM_PROMPT,
                        "tools": TOOLS,
                        "input": {
                            "format": {"encoding": "audio/pcm"},
                            "keyterms": KEYTERMS[:100],
                            "turn_detection": {"interrupt_response": True},
                        },
                        "output": {"voice": "michael"},
                    },
                }
            )
        )
        recv = asyncio.create_task(s.receive())
        pump = asyncio.create_task(s.pump_audio())
        await asyncio.wait_for(s.ready.wait(), 15)
        results["session_ready_ms"] = round(s.now() * 1000)
        await s.settle(quiet_s=1.5)

        async def test(name: str, action) -> None:
            before_audio = len(s.audio)
            t = s.now()
            await action()
            await s.settle(quiet_s=3.0)
            results[name] = summarize(s.since(t), t)
            write_pcm16(RESULTS / f"agent_{name}.wav", bytes(s.audio[before_audio:]), SR)
            print(name, json.dumps(results[name], ensure_ascii=False))

        prompt_text = "Two minutes. Pause compressions for rhythm and pulse check."

        async def t1():
            await ws.send(json.dumps({"type": "reply.create", "instructions": f'Say exactly: "{prompt_text}"'}))

        await test("T1_prompt", t1)
        results["T1_prompt"]["expected"] = prompt_text

        async def t2():
            await s.speech.put(q_en)

        await test("T2_question_en", t2)

        async def t3():
            await s.speech.put(q_hi)

        await test("T3_question_hinglish", t3)

        async def t4():
            long = (
                "Epinephrine one milligram was ordered at zero thirty and has not been "
                "acknowledged. Please confirm who is drawing it up and read back the dose."
            )
            t = s.now()
            await ws.send(json.dumps({"type": "reply.create", "instructions": f'Say exactly: "{long}"'}))
            first_audio = await s.wait_for(lambda e: e.get("type") == "reply.audio", 10, t)
            if first_audio:
                await asyncio.sleep(1.2)  # let it talk, then a human cuts in
                results.setdefault("T4_meta", {})["human_speech_sent_at_ms"] = round((s.now() - t) * 1000)
                await s.speech.put(stop)

        await test("T4_barge_in", t4)

        async def t5():
            await s.speech.put(chatter)

        await test("T5_chatter", t5)

        await ws.send(json.dumps({"type": "session.end"}))
        pump.cancel()
        try:
            await asyncio.wait_for(recv, 10)
        except (TimeoutError, websockets.ConnectionClosed):
            pass
    save_json("voice_agent.report.json", results)
    save_json("voice_agent.events.json", s.events)
    print("\nSaved spikes/results/voice_agent.report.json")


if __name__ == "__main__":
    asyncio.run(main())
