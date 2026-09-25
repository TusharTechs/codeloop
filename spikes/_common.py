"""Shared helpers for the day-1 spikes."""

from __future__ import annotations

import json
import os
import re
import sys
import wave
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "spikes" / "results"
load_dotenv(REPO / ".env")


def api_key() -> str:
    key = os.environ.get("ASSEMBLYAI_API_KEY", "").strip()
    if not key:
        sys.exit("ASSEMBLYAI_API_KEY is not set. Put it in codeloop/.env (see .env.example).")
    return key


def read_pcm16(path: Path) -> tuple[bytes, int]:
    with wave.open(str(path)) as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            sys.exit(f"{path} must be mono PCM16")
        return w.readframes(w.getnframes()), w.getframerate()


def write_pcm16(path: Path, pcm: bytes, rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)


def save_json(name: str, data: object) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / name
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return p


_NUM_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "fifteen": 15,
    "twenty": 20,
    "fifty": 50,
    "hundred": 100,
    "ek": 1,
    "do": 2,
    "teen": 3,
}


def norm_words(text: str) -> list[str]:
    text = text.lower().replace("-", " ")
    return re.findall(r"[a-z0-9ऀ-ॿ]+", text)


def edit_distance(a: list[str], b: list[str]) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, round(q * (len(s) - 1)))]
