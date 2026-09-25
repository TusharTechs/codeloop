"""End-to-end on clean transcripts: every scripted line → grammar → resolver → engine.

This is the upper bound of the pipeline (perfect ASR and diarization). The live evaluation
harness runs the same scoring on real AssemblyAI output.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codeloop.domain.models import Utterance
from codeloop.evaluation import check_outcomes, load_scenario, score_line
from codeloop.pipeline import TranscriptPipeline

SCENARIOS = sorted((Path(__file__).resolve().parents[2] / "eval" / "scenarios").glob("*.yaml"))


def run(path: Path):
    spec = load_scenario(path)
    pipe = TranscriptPipeline()
    scores = []
    for i, line in enumerate(spec["lines"]):
        utt = Utterance(
            id=f"u{i}", turn_order=i, text=line["say"], start_s=line["start"], end_s=line["end"], speaker=line["who"]
        )
        res = pipe.process(utt)
        scores.append(score_line(line["say"], line.get("gold", []), res.events))
    pipe.advance(spec["lines"][-1]["end"] + 1)
    return pipe, scores, check_outcomes(pipe.engine, spec.get("expected_outcomes", []))


@pytest.mark.parametrize("path", SCENARIOS, ids=[p.stem for p in SCENARIOS])
def test_scenario_events_match_gold(path: Path) -> None:
    _, scores, _ = run(path)
    problems = [f"{s.say!r}: missed {s.missed} extra {s.extra}" for s in scores if s.missed or s.extra]
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("path", SCENARIOS, ids=[p.stem for p in SCENARIOS])
def test_scenario_outcomes(path: Path) -> None:
    _, _, outcomes = run(path)
    failed = [f"{exp}: {detail}" for exp, ok, detail in outcomes if not ok]
    assert not failed, "\n".join(failed)


def test_demo_scenario_speaks_the_expected_prompts() -> None:
    pipe = TranscriptPipeline()
    spec = load_scenario(SCENARIOS[[p.stem for p in SCENARIOS].index("vf_arrest_demo")])
    spoken = []
    t = 0.0
    lines = iter(enumerate(spec["lines"]))
    nxt = next(lines, None)
    while t < 150:
        while nxt and nxt[1]["end"] <= t:
            i, line = nxt
            utt = Utterance(
                id=f"u{i}",
                turn_order=i,
                text=line["say"],
                start_s=line["start"],
                end_s=line["end"],
                speaker=line["who"],
            )
            spoken += [p.text for p in pipe.process(utt).output.prompts]
            nxt = next(lines, None)
        spoken += [p.text for p in pipe.advance(t).prompts]
        t += 0.25
    assert "Epinephrine one milligram ordered. Not acknowledged." in spoken
    assert "Check dose. Ordered amiodarone three hundred milligrams, read back one hundred fifty milligrams." in spoken
    assert "Two minutes. Pause compressions for rhythm and pulse check." in spoken
