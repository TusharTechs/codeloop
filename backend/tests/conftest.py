from __future__ import annotations

from itertools import count

import pytest

from codeloop.domain.models import Action, Event, EventKind, Rhythm
from codeloop.engine.engine import CodeEngine

_ids = count(1)


def ev(kind: EventKind | str, at: float, **kw) -> Event:
    kind = EventKind(kind)
    return Event(id=f"e{next(_ids)}", kind=kind, at_s=at, **kw)


def order_drug(at: float, drug: str, dose: float | None, unit: str = "mg", **kw) -> Event:
    return ev(EventKind.ORDER, at, action=Action.DRUG, drug=drug, dose=dose, unit=unit, **kw)


def ack_drug(at: float, drug: str | None, dose: float | None, unit: str = "mg", **kw) -> Event:
    return ev(EventKind.ACK, at, action=Action.DRUG if drug else None, drug=drug, dose=dose, unit=unit, **kw)


def done_drug(at: float, drug: str, dose: float | None, unit: str = "mg", **kw) -> Event:
    return ev(EventKind.DONE, at, action=Action.DRUG, drug=drug, dose=dose, unit=unit, **kw)


def shock(kind: EventKind | str, at: float, joules: float | None, **kw) -> Event:
    return ev(kind, at, action=Action.SHOCK, energy_j=joules, **kw)


def rhythm(at: float, r: Rhythm) -> Event:
    return ev(EventKind.RHYTHM, at, rhythm=r)


@pytest.fixture
def engine() -> CodeEngine:
    e = CodeEngine()
    e.apply(ev(EventKind.CPR_START, 0.0))
    return e
