"""End-to-end smoke test against a running server and live AssemblyAI.

Starts a replay code, listens like a crash-cart screen, and reports what CodeLoop logged,
flagged and said. CodeLoop's voice is saved to spikes/results/e2e_codeloop_voice.wav.

    uv run --project backend python -m codeloop &            # the server
    uv run --project backend python scripts/e2e_replay.py vf_arrest_demo.ward
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import wave
from pathlib import Path

import httpx
import websockets

OUT = Path(__file__).resolve().parents[1] / "spikes" / "results"


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--server", default="http://127.0.0.1:8000")
    ap.add_argument("--token", default=None)
    ap.add_argument("--extra-s", type=float, default=12.0, help="keep listening after the replay ends")
    args = ap.parse_args()
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    async with httpx.AsyncClient(base_url=args.server, headers=headers, timeout=30) as http:
        r = await http.post("/api/codes", json={"mode": "replay", "scenario": args.scenario})
        if r.status_code != 200:
            print("could not start:", r.status_code, r.text)
            return 1
        code_id = r.json()["id"]
        print("code", code_id)
        ws_url = (
            args.server.replace("http", "ws") + f"/ws/codes/{code_id}" + (f"?token={args.token}" if args.token else "")
        )
        voice = bytearray()
        room_bytes = 0
        log: list[dict] = []
        t0 = time.perf_counter()
        finished_at = None
        async with websockets.connect(ws_url, max_size=None) as ws:
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), 1.0)
                except TimeoutError:
                    raw = None
                if isinstance(raw, bytes):
                    if raw[:1] == b"\x02":
                        voice += raw[1:]
                    else:
                        room_bytes += len(raw) - 1
                elif raw is not None:
                    msg = json.loads(raw)
                    msg["_t"] = round(time.perf_counter() - t0, 2)
                    log.append(msg)
                    t = msg["type"]
                    if t == "utterance":
                        print(
                            f"{msg['_t']:6.1f}  [{msg['speaker']}] {msg['text']}" + ("  (echo)" if msg["echo"] else "")
                        )
                    elif t == "event":
                        e = msg["event"]
                        print(
                            f"{msg['_t']:6.1f}      → {e['kind']} {e.get('drug') or ''} {e.get('dose') or e.get('energy_j') or ''}"
                            f"{' ' + e['rhythm'] if e.get('rhythm') else ''}{' UNCONFIRMED' if e.get('unconfirmed') else ''}"
                        )
                    elif t == "flag":
                        print(f"{msg['_t']:6.1f}  ⚑ {msg['flag']['severity'].upper()} {msg['flag']['message']}")
                    elif t in ("agent_speaking",):
                        print(f"{msg['_t']:6.1f}  🔊 {msg['text']}")
                    elif t == "agent_interrupted":
                        print(f"{msg['_t']:6.1f}  🔇 interrupted")
                    elif t == "answer":
                        print(f"{msg['_t']:6.1f}  ? {msg['question']!r} → {msg['text']!r}")
                    elif t == "error":
                        print("ERROR", msg)
                    elif t == "replay_finished":
                        finished_at = time.perf_counter()
                if finished_at and time.perf_counter() - finished_at > args.extra_s:
                    await ws.send(json.dumps({"type": "confirm_end"}))
                    await asyncio.sleep(0.5)
                    await ws.send(json.dumps({"type": "stop"}))
                    await asyncio.sleep(1.0)
                    break
        for _ in range(20):  # the server finishes closing (ears flush, audit) asynchronously
            record = (await http.get(f"/api/codes/{code_id}/record")).json()
            if record.get("summary"):
                break
            await asyncio.sleep(0.5)
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / "e2e_codeloop_voice.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24_000)
        w.writeframes(bytes(voice))
    (OUT / "e2e_log.json").write_text(json.dumps(log, indent=2, ensure_ascii=False))
    (OUT / "e2e_record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    last_state = next((m["state"] for m in reversed(log) if m["type"] == "state"), {})
    print(
        "\nroom audio relayed:", round(room_bytes / 32000, 1), "s; CodeLoop spoke:", round(len(voice) / 48000, 1), "s"
    )
    print("latency:", last_state.get("latency_ms"), " voice:", last_state.get("voice"))
    print("record integrity:", record["integrity"])
    print("needs review:", record["needs_review"])
    print("summary:", json.dumps(record["summary"], indent=None))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
