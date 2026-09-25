"""Deterministic answers to questions addressed to CodeLoop.

The live spike showed the Voice Agent's managed LLM calling the state tool and then reading
out the wrong fact, so spoken answers are composed here from engine state and the Voice
Agent only voices them verbatim. Anything we cannot classify gets "Check the screen." —
CodeLoop never guesses a time, dose or count.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..domain.models import Action, Rhythm, Utterance
from ..extract.grammar import Grammar, tokenize
from .engine import CodeEngine
from .speech import say_drug, say_duration, say_quantity


class Topic(StrEnum):
    LAST_DRUG = "last_drug"
    DUE = "due"
    SHOCKS = "shocks"
    RHYTHM = "rhythm"
    CLOCK = "clock"
    ROLES = "roles"
    OPEN_ORDERS = "open_orders"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Answer:
    topic: Topic
    text: str
    drug: str | None = None


CHECK_SCREEN = "Check the screen."

_DUE = {"due", "next", "baaki", "pending", "remaining"}
_SHOCK = {"shock", "shocks", "shocked", "defib", "joules"}
_RHYTHM = {"rhythm", "ridam"}
_CLOCK = {"time", "long", "clock", "duration", "minutes", "kitna", "kitni"}
_ROLE = {"who", "kaun", "meds", "compressions", "airway", "leading", "lead"}
_ORDERS = {"orders", "order", "open", "outstanding", "unacknowledged"}

_RHYTHM_SPOKEN = {
    Rhythm.VF: "V-fib",
    Rhythm.PVT: "pulseless V-tach",
    Rhythm.PEA: "P E A",
    Rhythm.ASYSTOLE: "asystole",
    Rhythm.SINUS: "an organized rhythm",
}


def classify(text: str, grammar: Grammar) -> tuple[Topic, str | None]:
    tokens = tokenize(text)
    norms = [grammar.canonical(t.norm) for t in tokens]
    words = set(norms)
    drugs = grammar._drugs(norms)
    drug = drugs[0][1] if drugs else None
    if words & _DUE:
        return Topic.DUE, drug
    if drug:
        return Topic.LAST_DRUG, drug
    if words & _SHOCK:
        return Topic.SHOCKS, None
    if words & _RHYTHM:
        return Topic.RHYTHM, None
    if words & _ORDERS:
        return Topic.OPEN_ORDERS, None
    if words & {"who", "kaun"} and words & _ROLE:
        return Topic.ROLES, None
    if words & _CLOCK:
        return Topic.CLOCK, None
    return Topic.UNKNOWN, None


def answer(utt: Utterance, engine: CodeEngine, grammar: Grammar, now_s: float | None = None) -> Answer:
    now = engine.now_s if now_s is None else now_s
    topic, drug = classify(utt.text, grammar)
    text = {
        Topic.LAST_DRUG: lambda: _last_drug(engine, drug, now),
        Topic.DUE: lambda: _due(engine, now, drug),
        Topic.SHOCKS: lambda: _shocks(engine, now),
        Topic.RHYTHM: lambda: _rhythm(engine, now),
        Topic.CLOCK: lambda: f"Code time {say_duration(engine.clock_s(now))}.",
        Topic.ROLES: lambda: _roles(engine),
        Topic.OPEN_ORDERS: lambda: _open_orders(engine, now),
        Topic.UNKNOWN: lambda: CHECK_SCREEN,
    }[topic]()
    return Answer(topic=topic, text=text, drug=drug)


def _last_drug(engine: CodeEngine, drug: str | None, now: float) -> str:
    if drug is None:
        return CHECK_SCREEN
    name = say_drug(drug)
    last = engine.last_given(drug)
    parts = []
    if last is None:
        parts.append(f"No {name} recorded.")
    else:
        dose = say_quantity(last.dose, last.unit)
        count = sum(1 for a in engine.given if a.drug == drug)
        parts.append(f"Last {name}, {dose}, {say_duration(now - last.at_s)} ago.".replace(", ,", ","))
        if count > 1:
            parts.append(f"{count} doses total.")
    pending = [lp for lp in engine.open_loops() if lp.action == Action.DRUG and lp.drug == drug]
    if pending:
        parts.append(f"{name.capitalize()} ordered, not yet given.")
    return " ".join(parts)


def _due(engine: CodeEngine, now: float, drug: str | None) -> str:
    parts: list[str] = []
    snap = engine.snapshot(now)
    for lp in engine.open_loops():
        if drug and lp.drug != drug:
            continue
        what = "Shock" if lp.action == Action.SHOCK else say_drug(lp.drug).capitalize()
        qty = say_quantity(lp.ordered_value, "J" if lp.action == Action.SHOCK else lp.unit)
        state = {
            "UNACKNOWLEDGED": "not acknowledged",
            "CONFLICT": "dose not agreed",
            "ORDERED": "ordered",
            "ACKNOWLEDGED": "acknowledged, not given",
        }[lp.state.value]
        parts.append(f"{what} {qty} {state}.".replace("  ", " "))
    if drug in (None, "epinephrine"):
        w = snap["epinephrine_window"]
        if w["state"] == "open":
            parts.append("Epinephrine window open.")
        elif w["state"] == "overdue":
            parts.append(f"Epinephrine overdue, {say_duration(w['seconds_since_last'])} since last dose.")
        elif w["state"] == "waiting":
            parts.append(f"Next epinephrine in {say_duration(w['opens_in_s'])}.")
    if drug is None and snap["cpr"]["cycle"]:
        parts.append(f"Rhythm check in {say_duration(snap['cpr']['cycle']['remaining_s'])}.")
    return " ".join(parts) if parts else "Nothing due."


def _shocks(engine: CodeEngine, now: float) -> str:
    if not engine.shocks:
        return "No shocks recorded."
    last = engine.shocks[-1]
    n = len(engine.shocks)
    head = "One shock." if n == 1 else f"{n} shocks."
    return f"{head} Last {say_quantity(last.energy_j, 'J')}, {say_duration(now - last.at_s)} ago."


def _rhythm(engine: CodeEngine, now: float) -> str:
    if engine.rhythm is None or engine.rhythm_at_s is None:
        return "No rhythm recorded."
    return f"Last recorded rhythm {_RHYTHM_SPOKEN[engine.rhythm]}, {say_duration(now - engine.rhythm_at_s)} ago."


def _roles(engine: CodeEngine) -> str:
    if not engine.names:
        return CHECK_SCREEN
    return " ".join(f"{name.capitalize()} on {role.value}." for name, role in engine.names.items())


def _open_orders(engine: CodeEngine, now: float) -> str:
    if not engine.open_loops():
        return "No open orders."
    return _due(engine, now, None)
