"""Score the pipeline on the scripted (perfect-ASR) transcripts of every scenario.

This isolates CodeLoop's own understanding from speech recognition: each scenario line is
fed as a final utterance with the right speaker. Held-out scenarios are reported separately.

    uv run --project backend python eval/run_text_eval.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from codeloop.domain.models import Utterance
from codeloop.evaluation import check_outcomes, load_scenario, score_line
from codeloop.pipeline import TranscriptPipeline

SCENARIOS = Path(__file__).resolve().parent / "scenarios"


def run(path: Path) -> tuple[int, int, int, list, list]:
    spec = load_scenario(path)
    pipe = TranscriptPipeline()
    tp = fp = fn = 0
    misses = []
    for i, line in enumerate(spec["lines"]):
        utt = Utterance(id=f"u{i}", turn_order=i, text=line["say"], start_s=line["start"], end_s=line["end"],
                        speaker=line["who"])
        s = score_line(line["say"], line.get("gold", []), pipe.process(utt).events)
        tp += len(s.gold) - len(s.missed)
        fn += len(s.missed)
        fp += len(s.extra)
        if s.missed or s.extra:
            misses.append((line["say"], s.missed, s.extra))
    pipe.advance(spec["lines"][-1]["end"] + 20)
    return tp, fp, fn, check_outcomes(pipe.engine, spec.get("expected_outcomes", [])), misses


def main() -> int:
    groups = {"tuning": [], "held-out": []}
    for p in sorted(SCENARIOS.glob("*.yaml")):
        groups["held-out" if p.stem.startswith("heldout_") else "tuning"].append(p)
    for name, paths in groups.items():
        TP = FP = FN = OK = N = 0
        print(f"\n== {name} scenarios")
        for p in paths:
            tp, fp, fn, outcomes, misses = run(p)
            ok = sum(1 for _, good, _ in outcomes if good)
            TP, FP, FN, OK, N = TP + tp, FP + fp, FN + fn, OK + ok, N + len(outcomes)
            print(f"  {p.stem:28s} P {tp / max(1, tp + fp):.2f}  R {tp / max(1, tp + fn):.2f}  outcomes {ok}/{len(outcomes)}")
            for say, missed, extra in misses:
                print(f"      {say!r}: missed {missed} extra {extra}")
            for exp, good, detail in outcomes:
                if not good:
                    print(f"      ✗ {exp}: {detail}")
        print(f"  TOTAL                        P {TP / max(1, TP + FP):.2f}  R {TP / max(1, TP + FN):.2f}  outcomes {OK}/{N}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
