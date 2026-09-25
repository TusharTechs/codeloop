"""Capture live AssemblyAI streaming sessions for evaluation, using the PRODUCT client.

Streams each scenario WAV through `codeloop.aai.streaming.StreamingEars` (the exact
parameters CodeLoop ships with) at real-time pace and saves the raw messages with arrival
times, so `eval/run_eval.py` can replay them through the pipeline offline, as often as needed.

    uv run --project backend python eval/capture.py eval/audio/heldout_pea.ward.wav [...]
    uv run --project backend python eval/capture.py eval/audio/*.ward.wav --parallel 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import wave
from pathlib import Path

from codeloop.aai.streaming import SAMPLE_RATE, StreamingEars, build_params
from codeloop.config import get_settings
from codeloop.domain.formulary import default_formulary

OUT = Path(__file__).resolve().parents[1] / "spikes" / "results"


async def capture(wav: Path, tag: str) -> Path:
    settings = get_settings()
    f = default_formulary()
    with wave.open(str(wav)) as w:
        pcm = w.readframes(w.getnframes())
    messages: list[dict] = []
    t0 = time.perf_counter()
    done = asyncio.Event()

    async def on_message(msg: dict) -> None:
        msg["_recv_s"] = time.perf_counter() - t0
        messages.append(msg)
        if msg.get("type") == "Termination":
            done.set()

    ears = StreamingEars(settings, f, on_message)
    await ears.start()
    chunk = SAMPLE_RATE // 10 * 2
    for i, off in enumerate(range(0, len(pcm), chunk)):
        await ears.send_audio(pcm[off : off + chunk])
        await asyncio.sleep(max(0.0, t0 + (i + 1) * 0.1 - time.perf_counter()))
    await ears.close()
    try:
        await asyncio.wait_for(done.wait(), 10)
    except TimeoutError:
        pass
    params = {k: v for k, v in build_params(settings, f).items() if k != "prompt"}
    stem = wav.name.removesuffix(".wav")
    out = OUT / f"streaming.{stem}.{tag}.raw.json"
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"params": params, "messages": messages, "speed": 1.0, "client": "product"}))
    print(f"captured {out.name}: {sum(1 for m in messages if m.get('type') == 'Turn' and m.get('end_of_turn'))} turns")
    return out


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wavs", nargs="+", type=Path)
    ap.add_argument("--tag", default="product")
    ap.add_argument("--parallel", type=int, default=3)
    args = ap.parse_args()
    sem = asyncio.Semaphore(args.parallel)

    async def one(w: Path) -> None:
        async with sem:
            await capture(w, args.tag)
            await asyncio.sleep(1)

    await asyncio.gather(*(one(w) for w in args.wavs))


if __name__ == "__main__":
    asyncio.run(main())
