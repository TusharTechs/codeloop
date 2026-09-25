"""Synthesize realistic multi-speaker mock-code audio from scenario YAML files.

Each speaker is rendered with a different macOS voice, placed on a shared timeline, given
room reverb and a distance gain, then mixed with the sounds of a real resuscitation room:
compressions (only while CPR is running, derived from the gold events), a monitor beep,
a periodic alarm and room tone. The output is 16 kHz mono PCM16 WAV plus a gold JSON
with the actual start/end time of every line, which the evaluation harness scores against.

Usage:
    uv run --project backend python eval/synth.py --all
    uv run --project backend python eval/synth.py eval/scenarios/vf_arrest_demo.yaml --noise loud
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
import yaml

SR = 16_000
ROOT = Path(__file__).resolve().parent
SCENARIOS = ROOT / "scenarios"
OUT = ROOT / "audio"

NOISE_PROFILES = {
    # name: (compressions dBFS, monitor dBFS, alarm dBFS, room dBFS, reverb wet)
    "none": (None, None, None, None, 0.0),
    "ward": (-30.0, -34.0, -30.0, -48.0, 0.18),
    "loud": (-24.0, -28.0, -24.0, -42.0, 0.28),
}


def db(x: float) -> float:
    return float(10 ** (x / 20))


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2 and w.getnchannels() == 1
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def write_wav(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def tts(text: str, voice: str, rate: int, tmp: Path, idx: int) -> np.ndarray:
    out = tmp / f"line_{idx}.wav"
    subprocess.run(
        ["say", "-v", voice, "-r", str(rate), "-o", str(out), "--file-format=WAVE", "--data-format=LEI16@16000", text],
        check=True,
    )
    x = read_wav(out)
    # Trim leading/trailing digital silence so placement times are accurate.
    nz = np.flatnonzero(np.abs(x) > 1e-3)
    return x[nz[0] : nz[-1] + 1] if nz.size else x


def room_ir(rt60: float, rng: np.random.Generator) -> np.ndarray:
    n = int(SR * rt60)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-6.9 * t / rt60)
    ir[0] = 0.0
    return ir / np.sqrt(np.sum(ir**2))


def convolve(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    n = len(x) + len(h) - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size), size)[:n]
    return y[: len(x)]


def lowpass_noise(n: int, rng: np.random.Generator, alpha: float) -> np.ndarray:
    white = rng.standard_normal(n)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):  # one-pole low-pass; n is small enough for bursts
        acc = alpha * acc + (1 - alpha) * white[i]
        y[i] = acc
    return y / (np.max(np.abs(y)) + 1e-9)


def compressions(total: int, windows: list[tuple[float, float]], level: float, rng: np.random.Generator) -> np.ndarray:
    out = np.zeros(total)
    period = 60 / 110  # 110 compressions per minute
    burst_len = int(0.07 * SR)
    for start, end in windows:
        t = start
        while t < end:
            i = int(t * SR)
            if i + burst_len >= total:
                break
            burst = lowpass_noise(burst_len, rng, 0.93) * np.hanning(burst_len)
            out[i : i + burst_len] += burst
            t += period * rng.uniform(0.96, 1.04)
    return out * level


def monitor(total: int, level: float) -> np.ndarray:
    out = np.zeros(total)
    beep = np.sin(2 * np.pi * 960 * np.arange(int(0.08 * SR)) / SR) * np.hanning(int(0.08 * SR))
    step = int(0.62 * SR)
    for i in range(int(0.3 * SR), total - len(beep), step):
        out[i : i + len(beep)] += beep
    return out * level


def alarm(total: int, level: float) -> np.ndarray:
    # IEC 60601-1-8-style medium-priority 3-pulse burst every 10 s.
    out = np.zeros(total)
    pulse_n = int(0.18 * SR)
    t = np.arange(pulse_n) / SR
    pulse = (np.sin(2 * np.pi * 523 * t) + 0.5 * np.sin(2 * np.pi * 1046 * t)) * np.hanning(pulse_n)
    for start in np.arange(4.0, total / SR - 1, 10.0):
        for k in range(3):
            i = int((start + k * 0.25) * SR)
            if i + pulse_n < total:
                out[i : i + pulse_n] += pulse
    return out * level / 1.5


def cpr_windows(lines: list[dict], total_s: float) -> list[tuple[float, float]]:
    windows: list[tuple[float, float]] = []
    running_since: float | None = None
    for line in lines:
        for ev in line.get("gold", []):
            k = ev["kind"]
            if k in ("cpr_start", "cpr_resume") and running_since is None:
                running_since = line["end"]
            elif k in ("cpr_pause", "rosc") and running_since is not None:
                windows.append((running_since, line["start"]))
                running_since = None
    if running_since is not None:
        windows.append((running_since, total_s))
    return windows


def synth(path: Path, noise: str, rate: int, seed: int, out_dir: Path = OUT) -> Path:
    spec = yaml.safe_load(path.read_text())
    rng = np.random.default_rng(seed)
    comp_db, mon_db, alarm_db, room_db, wet = NOISE_PROFILES[noise]
    ir = room_ir(0.35, rng)

    placed: list[dict] = []
    clips: list[np.ndarray] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cursor = 0.0
        for idx, line in enumerate(spec["lines"]):
            who = spec["cast"][line["who"]]
            clip = tts(line["say"], who["voice"], rate, tmp, idx)
            clip = clip / (np.max(np.abs(clip)) + 1e-9) * db(-6) * who.get("distance", 1.0)
            if wet:
                clip = (1 - wet) * clip + wet * convolve(clip, ir) * 0.5
            start = float(line["at"]) if "at" in line else cursor + float(line.get("gap", 0.6))
            end = start + len(clip) / SR
            cursor = end
            placed.append(
                {
                    **line,
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "voice": who["voice"],
                    "speaker_name": who["name"],
                }
            )
            clips.append(clip)

    total_s = max(p["end"] for p in placed) + 2.0
    total = int(total_s * SR)
    mix = np.zeros(total)
    for p, clip in zip(placed, clips, strict=True):
        i = int(p["start"] * SR)
        mix[i : i + len(clip)] += clip

    if noise != "none":
        mix += compressions(total, cpr_windows(placed, total_s), db(comp_db), rng)
        mix += monitor(total, db(mon_db))
        mix += alarm(total, db(alarm_db))
        mix += rng.standard_normal(total) * db(room_db)

    peak = np.max(np.abs(mix))
    if peak > db(-1):
        mix *= db(-1) / peak

    stem = f"{spec['id']}.{noise}"
    wav_path = out_dir / f"{stem}.wav"
    write_wav(wav_path, mix)
    gold = {
        "id": spec["id"],
        "title": spec.get("title", ""),
        "noise": noise,
        "duration_s": round(total_s, 3),
        "cast": spec["cast"],
        "expected_outcomes": spec.get("expected_outcomes", []),
        "lines": [{k: v for k, v in p.items() if k not in ("at", "gap")} for p in placed],
    }
    (out_dir / f"{stem}.gold.json").write_text(json.dumps(gold, indent=2, ensure_ascii=False))
    return wav_path


def main() -> int:
    if sys.platform != "darwin" or not shutil.which("say"):
        print("synth.py needs macOS `say` for multi-voice TTS.", file=sys.stderr)
        return 1
    ap = argparse.ArgumentParser()
    ap.add_argument("scenarios", nargs="*", type=Path)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--noise", choices=list(NOISE_PROFILES), action="append")
    ap.add_argument("--rate", type=int, default=185, help="speaking rate, words per minute")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=OUT, help="output directory")
    args = ap.parse_args()
    paths = sorted(SCENARIOS.glob("*.yaml")) if args.all else args.scenarios
    if not paths:
        ap.error("give scenario paths or --all")
    for p in paths:
        for noise in args.noise or ["none", "ward"]:
            out = synth(p, noise, args.rate, args.seed, args.out)
            print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
