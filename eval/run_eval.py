"""Score CodeLoop end to end on captured AssemblyAI streaming sessions.

Replays each capture (raw streaming messages with arrival times) through the real product
pipeline — turn splitting, grammar, resolver, ACLS engine — at its original timing, and
scores it against the scenario's gold file:

  events      precision / recall of clinical events per scripted line
  outcomes    did each expected loop end in the right state, was each expected flag raised
  prompts     what CodeLoop would have said, and when
  speakers    word-level diarization purity
  latency     speech end → event available

    uv run --project backend python eval/run_eval.py spikes/results/streaming.vf_arrest_demo.ward.full.raw.json
    uv run --project backend python eval/run_eval.py spikes/results/streaming.*.raw.json --json eval/results.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from codeloop.evaluation import (
    assign_to_lines,
    check_outcomes,
    diarization_purity,
    replay_capture,
    score_line,
)
from codeloop.pipeline import TranscriptPipeline

ROOT = Path(__file__).resolve().parent


def gold_for(raw_path: Path) -> Path:
    m = re.match(r"streaming\.(.+?\.(?:none|ward|loud))\.", raw_path.name)
    if not m:
        sys.exit(f"cannot infer scenario from {raw_path.name}")
    return ROOT / "audio" / f"{m.group(1)}.gold.json"


def pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    return round(s[min(len(s) - 1, round(q * (len(s) - 1)))])


def evaluate(raw_path: Path) -> dict:
    raw = json.loads(raw_path.read_text())
    gold = json.loads(gold_for(raw_path).read_text())
    lines = gold["lines"]
    pipe = TranscriptPipeline()
    rep = replay_capture(raw["messages"], pipe)
    by_line = assign_to_lines(rep.events, lines)
    scores = [score_line(ln["say"], ln.get("gold", []), by_line[i]) for i, ln in enumerate(lines)]
    tp = sum(len(s.gold) - len(s.missed) for s in scores)
    fn = sum(len(s.missed) for s in scores)
    fp = sum(len(s.extra) for s in scores)
    unassigned = len(rep.events) - sum(len(v) for v in by_line.values())
    outcomes = check_outcomes(pipe.engine, gold.get("expected_outcomes", []))
    purity, table = diarization_purity(rep.utterances, lines)
    return {
        "capture": raw_path.name,
        "params": raw.get("params", {}),
        "events": {
            "tp": tp,
            "fp": fp + unassigned,
            "fn": fn,
            "precision": round(tp / max(1, tp + fp + unassigned), 3),
            "recall": round(tp / max(1, tp + fn), 3),
        },
        "outcomes": [{"expected": e, "ok": ok, "detail": d} for e, ok, d in outcomes],
        "outcomes_met": f"{sum(ok for _, ok, _ in outcomes)}/{len(outcomes)}",
        "prompts": rep.prompts,
        "diarization_word_purity": round(purity, 3),
        "speaker_table": table,
        "event_latency_ms": {"p50": pct(rep.latencies_ms, 0.5), "p90": pct(rep.latencies_ms, 0.9)},
        "lines": [{"say": s.say, "missed": s.missed, "extra": s.extra} for s in scores if s.missed or s.extra],
        "utterances": [{k: v for k, v in u.items() if k != "words"} for u in rep.utterances],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("captures", nargs="+", type=Path)
    ap.add_argument("--json", type=Path, help="write the full report here")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()
    reports = [evaluate(p) for p in args.captures]
    for r in reports:
        e = r["events"]
        print(f"\n{r['capture']}")
        print(
            f"  events     precision {e['precision']:.2f}  recall {e['recall']:.2f}  "
            f"(tp {e['tp']}, fp {e['fp']}, fn {e['fn']})"
        )
        print(f"  outcomes   {r['outcomes_met']}")
        for o in r["outcomes"]:
            print(f"    {'✓' if o['ok'] else '✗'} {o['expected']}  — {o['detail']}")
        print(f"  speakers   word purity {r['diarization_word_purity']:.2f}")
        print(f"  latency    p50 {r['event_latency_ms']['p50']} ms, p90 {r['event_latency_ms']['p90']} ms")
        print("  prompts    " + "\n             ".join(f"{p['at_s']:6.1f}s  {p['text']}" for p in r["prompts"]))
        if args.verbose:
            for ln in r["lines"]:
                print(f"    line {ln['say']!r}: missed {ln['missed']} extra {ln['extra']}")
            for u in r["utterances"]:
                print(f"    [{u['speaker']}] {u['start_s']:6.1f}-{u['end_s']:6.1f} (+{u['emitted_s']:.1f}) {u['text']}")
    if args.json:
        args.json.write_text(json.dumps(reports, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
