"""Scoring CodeLoop against scenario gold labels (shared by tests and eval/run_eval.py)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .domain.models import Event, EventKind, LoopState
from .engine.engine import CodeEngine

WORDS_PER_S = 2.9  # approximate speaking rate when a scenario line has no measured timing


def load_scenario(path: Path) -> dict:
    """Load a scenario YAML and give every line approximate start/end times (seconds)."""
    spec = yaml.safe_load(path.read_text())
    cursor = 0.0
    for line in spec["lines"]:
        start = float(line["at"]) if "at" in line else cursor + float(line.get("gap", 0.6))
        dur = max(0.6, len(line["say"].split()) / WORDS_PER_S)
        line["start"], line["end"] = round(start, 3), round(start + dur, 3)
        cursor = line["end"]
    return spec


def event_key(e: dict | Event) -> tuple:
    d = e.model_dump(mode="json") if isinstance(e, Event) else e
    kind = d["kind"]
    if kind == EventKind.ROLE:
        return (kind, d.get("role"), (d.get("name") or "").lower() or None)
    if kind in (EventKind.ORDER, EventKind.ACK, EventKind.DONE, EventKind.CANCEL):
        value = d.get("energy_j") if d.get("action") == "shock" else d.get("dose")
        return (kind, d.get("action"), d.get("drug"), float(value) if value is not None else None)
    if kind == EventKind.RHYTHM:
        return (kind, d.get("rhythm"))
    return (kind,)


@dataclass
class LineScore:
    say: str
    gold: list[tuple]
    got: list[tuple]
    missed: list[tuple] = field(default_factory=list)
    extra: list[tuple] = field(default_factory=list)


@dataclass
class ScenarioScore:
    lines: list[LineScore]
    outcomes: list[tuple[dict, bool, str]]

    @property
    def tp(self) -> int:
        return sum(len(ln.gold) - len(ln.missed) for ln in self.lines)

    @property
    def fn(self) -> int:
        return sum(len(ln.missed) for ln in self.lines)

    @property
    def fp(self) -> int:
        return sum(len(ln.extra) for ln in self.lines)

    @property
    def precision(self) -> float:
        return self.tp / max(1, self.tp + self.fp)

    @property
    def recall(self) -> float:
        return self.tp / max(1, self.tp + self.fn)

    @property
    def outcomes_met(self) -> int:
        return sum(1 for _, ok, _ in self.outcomes if ok)


def score_line(say: str, gold: list[dict], got: list[Event]) -> LineScore:
    # Restatements are scored as orders. The resolver's speaker-mapping echo of a
    # self-introduction (id suffix "s") is bookkeeping, not a separate statement.
    g = [event_key({k: v for k, v in e.items() if k != "restatement"}) for e in gold]
    p = [event_key(e) for e in got if not (e.kind == EventKind.ROLE and e.id.endswith("s"))]
    remaining = list(p)
    missed = []
    for k in g:
        if k in remaining:
            remaining.remove(k)
        else:
            missed.append(k)
    return LineScore(say=say, gold=g, got=p, missed=missed, extra=remaining)


def check_outcomes(engine: CodeEngine, expected: list[dict]) -> list[tuple[dict, bool, str]]:
    results = []
    loops = list(engine.loops.values())
    for exp in expected:
        if "flag" in exp:
            ok = any(f.rule == exp["flag"] for f in engine.flags.values())
            results.append((exp, ok, "raised" if ok else "not raised"))
            continue
        matching = [lp for lp in loops if lp.label() == exp["loop"]]
        if "count" in exp:
            ok = len(matching) == exp["count"] and all(lp.state == LoopState(exp["final_state"]) for lp in matching)
            results.append((exp, ok, f"{len(matching)} loops, states {[lp.state.value for lp in matching]}"))
            continue
        if not matching:
            results.append((exp, False, "loop not found; have " + ", ".join(lp.label() for lp in loops)))
            continue
        lp = matching[0]
        ok = lp.state == LoopState(exp["final_state"])
        detail = " → ".join(h.state.value for h in lp.history)
        if "first_state" in exp:
            ok &= any(h.state == LoopState(exp["first_state"]) for h in lp.history)
        results.append((exp, ok, detail))
    return results
