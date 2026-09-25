"""End-to-end spoken debrief against a running server and the live AssemblyAI Voice Agent API.

A TTS "team leader" answers CodeLoop's debrief questions. Prints the conversation, tool calls
and saved notes; CodeLoop's voice goes to spikes/results/e2e_debrief_voice.wav.

    uv run --project backend python scripts/e2e_debrief.py <ended code id>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

import websockets

OUT = Path(__file__).resolve().parents[1] / "spikes" / "results"
ANSWERS = [
    "Honestly it felt fast. The shocks were quick but it got loud around the drugs.",
    "Everyone was talking about the IV line, so nobody repeated the epi order. The meds nurse should say every order back out loud.",
    "The amio was read back as one fifty. The read-back caught it, so we should always repeat the dose.",
    "Keep the fast shocks. Change: always read back every dose, and assign one person to the IV.",
    "No, that's everything. Thanks.",
]


def tts16(text: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "a.wav"
        subprocess.run(
            [
                "say",
                "-v",
                "Rishi",
                "-r",
                "185",
                "-o",
                str(out),
                "--file-format=WAVE",
                "--data-format=LEI16@16000",
                text,
            ],
            check=True,
        )
        with wave.open(str(out)) as w:
            return w.readframes(w.getnframes())


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("code_id")
    ap.add_argument("--server", default="ws://127.0.0.1:8000")
    args = ap.parse_args()
    answers = [tts16(a) for a in ANSWERS]
    voice = bytearray()
    t0 = time.perf_counter()
    state = {"agent_turns": 0, "answered": 0, "done": False, "last_agent": 0.0, "speaking_until": 0.0}

    async with websockets.connect(f"{args.server}/ws/debrief/{args.code_id}", max_size=None) as ws:

        async def mic() -> None:
            """Real-time 100 ms frames: silence, or the next answer after CodeLoop finishes a turn."""
            chunk = 3200
            start = time.perf_counter()
            n = 0
            queue = bytearray()
            while not state["done"]:
                now = time.perf_counter()
                idle = now - state["last_agent"] > 1.2 and now > state["speaking_until"]
                if not queue and idle and state["agent_turns"] > state["answered"] and state["answered"] < len(answers):
                    queue += answers[state["answered"]]
                    print(f"{now - t0:6.1f}  LEADER: {ANSWERS[state['answered']]}")
                    state["answered"] += 1
                frame = bytes(queue[:chunk]).ljust(chunk, b"\x00")
                del queue[:chunk]
                await ws.send(frame)
                n += 1
                await asyncio.sleep(max(0.0, start + n * 0.1 - time.perf_counter()))

        async def listen() -> None:
            while not state["done"]:
                raw = await ws.recv()
                now = time.perf_counter()
                if isinstance(raw, bytes):
                    voice.extend(raw[1:])
                    state["last_agent"] = now
                    state["speaking_until"] = max(state["speaking_until"], now) + (len(raw) - 1) / 48000
                    continue
                m = json.loads(raw)
                t = m["type"]
                if t == "debrief_agent":
                    state["agent_turns"] += 1
                    print(f"{now - t0:6.1f}  CODELOOP: {m['text']}{' (interrupted)' if m.get('interrupted') else ''}")
                elif t == "debrief_user":
                    print(f"{now - t0:6.1f}    heard: {m['text']}")
                elif t == "debrief_tool":
                    print(f"{now - t0:6.1f}  [tool] {m['name']}")
                elif t == "debrief_note":
                    print(f"{now - t0:6.1f}  [note:{m['kind']}] {m['note']}")
                elif t == "debrief_done":
                    print(f"{now - t0:6.1f}  [done] {m['summary']}")
                    await asyncio.sleep(6)
                    state["done"] = True
                elif t in ("error", "debrief_ready"):
                    print(f"{now - t0:6.1f}  {t}: {m.get('message') or m.get('facts')}")

        try:
            await asyncio.wait_for(asyncio.gather(mic(), listen()), timeout=180)
        except (TimeoutError, websockets.ConnectionClosed):
            pass
        state["done"] = True
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / "e2e_debrief_voice.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(bytes(voice))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
