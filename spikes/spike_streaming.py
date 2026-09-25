"""Spike 1: can Universal-3.5 Pro streaming hear a resuscitation room well enough?

Streams a synthesized mock code (eval/audio/*.wav) at real-time pace and measures, against
the scenario's gold file:
  - diarization purity: do speaker labels line up with the real speakers?
  - entity accuracy: are drug names, doses, energies and rhythms transcribed correctly?
  - word confidence on the safety-critical words
  - per-line WER
  - latency: wall-clock time from the end of a spoken turn to its final transcript

Run the A/B by repeating with --variant bare (no Medical Mode, keyterms, prompt or Voice Focus).

    uv run --project backend python spikes/spike_streaming.py eval/audio/vf_arrest_demo.ward.wav
    uv run --project backend python spikes/spike_streaming.py eval/audio/vf_arrest_demo.ward.wav --variant bare
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode

import websockets
from _common import api_key, edit_distance, norm_words, pct, read_pcm16, save_json
from acls_vocab import DRUG_ALIASES, KEYTERMS, NUMBER_FORMS, PROMPT, RHYTHM_ALIASES

URL = "wss://streaming.assemblyai.com/v3/ws"
CHUNK_MS = 100


def build_params(variant: str, sample_rate: int, max_speakers: int, langs: list[str],
                 min_silence: int | None = None, max_silence: int | None = None, prompt_extra: str = "") -> dict:
    p: dict[str, object] = {
        "speech_model": "universal-3-5-pro",
        "sample_rate": sample_rate,
        "encoding": "pcm_s16le",
        "speaker_labels": "true",
        "max_speakers": max_speakers,
        "language_detection": "true",
    }
    if langs:
        p["language_codes"] = json.dumps(langs)
    if min_silence:
        p["min_turn_silence"] = min_silence
    if max_silence:
        p["max_turn_silence"] = max_silence
    if variant == "full":
        p.update(
            {
                "domain": "medical-v1",
                "keyterms_prompt": json.dumps(KEYTERMS),
                "prompt": (PROMPT + " " + prompt_extra).strip(),
                "voice_focus": "far-field",
            }
        )
    return p


async def run(wav: Path, variant: str, max_speakers: int, langs: list[str], speed: float,
              min_silence: int | None = None, max_silence: int | None = None, prompt_extra: str = "") -> dict:
    pcm, sr = read_pcm16(wav)
    params = build_params(variant, sr, max_speakers, langs, min_silence, max_silence, prompt_extra)
    url = f"{URL}?{urlencode(params)}"
    chunk = int(sr * CHUNK_MS / 1000) * 2
    messages: list[dict] = []
    t0: float | None = None

    async with websockets.connect(url, additional_headers={"Authorization": api_key()}, max_size=None) as ws:

        async def sender() -> None:
            nonlocal t0
            t0 = time.perf_counter()
            for i, off in enumerate(range(0, len(pcm), chunk)):
                await ws.send(pcm[off : off + chunk])
                target = t0 + (i + 1) * CHUNK_MS / 1000 / speed
                await asyncio.sleep(max(0.0, target - time.perf_counter()))
            await ws.send(json.dumps({"type": "Terminate"}))

        async def receiver() -> None:
            async for raw in ws:
                msg = json.loads(raw)
                msg["_recv_s"] = (time.perf_counter() - t0) if t0 else 0.0
                messages.append(msg)
                if msg.get("type") == "Termination":
                    return

        async def progress() -> None:
            while True:
                await asyncio.sleep(15)
                finals = sum(1 for m in messages if m.get("type") == "Turn" and m.get("end_of_turn"))
                print(f"  … {time.perf_counter() - (t0 or time.perf_counter()):5.0f}s sent, "
                      f"{len(messages)} msgs, {finals} final turns", file=sys.stderr, flush=True)

        audio_s = len(pcm) / 2 / sr
        prog = asyncio.create_task(progress())
        try:
            await asyncio.wait_for(asyncio.gather(sender(), receiver()), timeout=audio_s / speed + 45)
        except TimeoutError:
            print("  ! timed out waiting for Termination; scoring what arrived", file=sys.stderr)
        except websockets.ConnectionClosed as e:
            print(f"  ! connection closed: code={e.code} reason={e.reason!r}", file=sys.stderr)
        finally:
            prog.cancel()
    return {"params": {k: v for k, v in params.items() if k != "prompt"}, "messages": messages, "speed": speed}


def final_turns(messages: list[dict]) -> list[dict]:
    finals: dict[int, dict] = {}
    for m in messages:
        if m.get("type") == "Turn" and m.get("end_of_turn"):
            finals[m["turn_order"]] = m
    for m in messages:
        if m.get("type") == "SpeakerRevision":
            for rev in m.get("revisions", []):
                if rev["turn_order"] in finals:
                    finals[rev["turn_order"]]["speaker_label"] = rev["speaker_label"]
                    finals[rev["turn_order"]]["_revised"] = True
    return [finals[k] for k in sorted(finals)]


def contains_any(words: list[str], forms: set[str]) -> bool:
    joined = " " + " ".join(words) + " "
    return any(f" {f} " in joined for f in forms)


def analyse(result: dict, gold: dict, speed: float) -> dict:
    turns = final_turns(result["messages"])
    lines = gold["lines"]
    # Assign each gold line the final turns whose words overlap it in time.
    by_line: dict[int, list[dict]] = defaultdict(list)
    turn_line: dict[int, int] = {}
    for t in turns:
        ws = t.get("words") or []
        if not ws:
            continue
        ts, te = ws[0]["start"] / 1000, ws[-1]["end"] / 1000
        best, best_ov = None, 0.0
        for i, ln in enumerate(lines):
            ov = min(te, ln["end"]) - max(ts, ln["start"])
            if ov > best_ov:
                best, best_ov = i, ov
        if best is not None:
            by_line[best].append(t)
            turn_line[t["turn_order"]] = best

    # Diarization purity: majority real speaker per label.
    label_to_who: dict[str, Counter] = defaultdict(Counter)
    for t in turns:
        if t["turn_order"] in turn_line:
            label_to_who[str(t.get("speaker_label"))][lines[turn_line[t["turn_order"]]]["who"]] += 1
    mapped = sum(c.most_common(1)[0][1] for c in label_to_who.values())
    total_mapped = sum(sum(c.values()) for c in label_to_who.values())
    who_to_labels: dict[str, set] = defaultdict(set)
    for label, c in label_to_who.items():
        for who in c:
            who_to_labels[who].add(label)

    # Per-line WER, entity checks and critical-word confidence.
    per_line = []
    entity_hits = entity_total = 0
    word_errs = word_total = 0
    critical_conf: list[float] = []
    for i, ln in enumerate(lines):
        hyp_turns = by_line.get(i, [])
        hyp_text = " ".join(t.get("transcript", "") for t in hyp_turns)
        hyp = norm_words(hyp_text)
        ref = norm_words(ln["say"])
        err = edit_distance(ref, hyp)
        word_errs += err
        word_total += len(ref)
        checks = []
        for ev in ln.get("gold", []):
            if ev.get("drug"):
                checks.append(("drug", ev["drug"], DRUG_ALIASES.get(ev["drug"], {ev["drug"]})))
            for key in ("dose", "energy_j"):
                if ev.get(key) in NUMBER_FORMS:
                    checks.append((key, ev[key], NUMBER_FORMS[ev[key]]))
            if ev.get("rhythm"):
                checks.append(("rhythm", ev["rhythm"], RHYTHM_ALIASES[ev["rhythm"]]))
        seen = set()
        results = []
        for kind, val, forms in checks:
            if (kind, val) in seen:
                continue
            seen.add((kind, val))
            ok = contains_any(hyp, {f.lower() for f in forms})
            entity_hits += ok
            entity_total += 1
            results.append({"kind": kind, "value": val, "ok": ok})
        for t in hyp_turns:
            for w in t.get("words", []):
                wn = norm_words(w["text"])
                if any(
                    x.isdigit() or x in {"epi", "epinephrine", "amio", "amiodarone", "hundred", "fifty", "joules"}
                    for x in wn
                ):
                    critical_conf.append(w.get("confidence", 0.0))
        labels = [str(t.get("speaker_label")) for t in hyp_turns]
        per_line.append(
            {
                "who": ln["who"],
                "ref": ln["say"],
                "hyp": hyp_text,
                "wer_errs": err,
                "labels": labels,
                "entities": results,
                "langs": [t.get("language_code") for t in hyp_turns],
            }
        )

    # Latency: when did the final arrive vs. when the speech ended (audio time / speed)?
    lat = []
    for t in turns:
        ws = t.get("words") or []
        if ws:
            lat.append((t["_recv_s"] - ws[-1]["end"] / 1000 / speed) * 1000)
    label_counts = Counter(str(t.get("speaker_label")) for t in turns)
    return {
        "turns": len(turns),
        "gold_lines": len(lines),
        "lines_with_no_turn": sum(1 for i in range(len(lines)) if i not in by_line),
        "wer": round(word_errs / max(1, word_total), 4),
        "entity_accuracy": round(entity_hits / max(1, entity_total), 4),
        "entity_hits": entity_hits,
        "entity_total": entity_total,
        "diarization_purity": round(mapped / max(1, total_mapped), 4),
        "speaker_labels_seen": dict(label_counts),
        "labels_per_real_speaker": {k: sorted(v) for k, v in who_to_labels.items()},
        "revised_turns": sum(1 for t in turns if t.get("_revised")),
        "critical_word_conf": {
            "n": len(critical_conf),
            "min": min(critical_conf, default=None),
            "p10": pct(critical_conf, 0.1),
            "p50": pct(critical_conf, 0.5),
            "below_0_6": sum(1 for c in critical_conf if c < 0.6),
        },
        "final_latency_ms": {"p50": pct(lat, 0.5), "p90": pct(lat, 0.9), "max": max(lat, default=None)},
        "per_line": per_line,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", type=Path)
    ap.add_argument("--variant", choices=["full", "bare"], default="full")
    ap.add_argument("--max-speakers", type=int, default=5)
    ap.add_argument("--langs", default="en,hi", help="comma list; empty for auto")
    ap.add_argument("--speed", type=float, default=1.0, help=">1 streams faster than real time")
    ap.add_argument("--min-silence", type=int, help="min_turn_silence ms")
    ap.add_argument("--max-silence", type=int, help="max_turn_silence ms")
    ap.add_argument("--tag", default="", help="suffix for result files")
    ap.add_argument("--prompt-extra", default="", help="appended to the context prompt")
    args = ap.parse_args()
    gold_path = args.wav.parent / args.wav.name.replace(".wav", ".gold.json")
    gold = json.loads(gold_path.read_text())
    langs = [x for x in args.langs.split(",") if x]
    result = asyncio.run(run(args.wav, args.variant, args.max_speakers, langs, args.speed,
                             args.min_silence, args.max_silence, args.prompt_extra))
    errors = [
        m
        for m in result["messages"]
        if m.get("type") not in ("Begin", "Turn", "SpeakerRevision", "Termination", "SpeechStarted", "Heartbeat")
    ]
    report = analyse(result, gold, args.speed)
    report["unexpected_messages"] = errors[:5]
    stem = f"streaming.{args.wav.stem}.{args.variant}{'.' + args.tag if args.tag else ''}"
    save_json(stem + ".raw.json", result)
    save_json(stem + ".report.json", report)
    summary = {k: v for k, v in report.items() if k != "per_line"}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nPer line (ref → hyp [labels] entity misses):")
    for ln in report["per_line"]:
        miss = [f"{e['kind']}={e['value']}" for e in ln["entities"] if not e["ok"]]
        print(
            f"  {ln['who']:<10} {ln['ref'][:48]:<48} → {ln['hyp'][:60]:<60} {ln['labels']} "
            f"{'MISS ' + ','.join(miss) if miss else ''}"
        )


if __name__ == "__main__":
    main()
