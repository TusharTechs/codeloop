from __future__ import annotations

import pytest
from conftest import done_drug, ev, order_drug, rhythm, shock

from codeloop.domain.formulary import default_formulary
from codeloop.domain.models import EventKind, Rhythm, Role, Utterance
from codeloop.engine.answers import CHECK_SCREEN, Topic, answer, classify
from codeloop.engine.engine import CodeEngine
from codeloop.extract.grammar import Grammar

G = Grammar(default_formulary())


def q(text: str) -> Utterance:
    return Utterance(id="q", turn_order=0, text=text, start_s=0, end_s=1)


@pytest.mark.parametrize(
    ("text", "topic", "drug"),
    [
        ("CodeLoop, when was the last epinephrine given?", Topic.LAST_DRUG, "epinephrine"),
        ("CodeLoop, last epi kab diya tha?", Topic.LAST_DRUG, "epinephrine"),
        ("कादलू, लास्ट ईपी क्या दिया था?", Topic.LAST_DRUG, "epinephrine"),
        ("CodeLoop, how much amio have we given?", Topic.LAST_DRUG, "amiodarone"),
        ("CodeLoop, what's due?", Topic.DUE, None),
        ("CodeLoop, next epi kab due hai?", Topic.DUE, "epinephrine"),
        ("CodeLoop, how many shocks?", Topic.SHOCKS, None),
        ("CodeLoop, what was the last rhythm?", Topic.RHYTHM, None),
        ("CodeLoop, how long have we been going?", Topic.CLOCK, None),
        ("CodeLoop, who is on meds?", Topic.ROLES, None),
        ("CodeLoop, any open orders?", Topic.OPEN_ORDERS, None),
        ("CodeLoop, what's the weather?", Topic.UNKNOWN, None),
    ],
)
def test_classify(text: str, topic: Topic, drug: str | None) -> None:
    assert classify(text, G) == (topic, drug)


@pytest.fixture
def code() -> CodeEngine:
    e = CodeEngine()
    e.apply(ev(EventKind.CPR_START, 0))
    e.apply(rhythm(12, Rhythm.VF))
    e.apply(shock(EventKind.DONE, 20, 200))
    e.apply(done_drug(52, "epinephrine", 1))
    e.apply(ev(EventKind.ROLE, 1, role=Role.MEDS, name="Priya"))
    e.advance(242)
    return e


def test_last_drug_answer_is_spoken_in_words(code: CodeEngine) -> None:
    a = answer(q("CodeLoop, last epi kab diya tha?"), code, G)
    assert a.text == "Last epinephrine, one milligram, three minutes ten seconds ago."


def test_drug_never_given(code: CodeEngine) -> None:
    assert answer(q("CodeLoop, last amio?"), code, G).text == "No amiodarone recorded."


def test_pending_order_is_mentioned(code: CodeEngine) -> None:
    code.apply(order_drug(243, "amiodarone", 300))
    a = answer(q("CodeLoop, amiodarone?"), code, G, now_s=244)
    assert a.text == "No amiodarone recorded. Amiodarone ordered, not yet given."


def test_whats_due_lists_open_orders_epi_window_and_rhythm_check(code: CodeEngine) -> None:
    code.apply(order_drug(243, "amiodarone", 300))
    code.advance(254)
    text = answer(q("CodeLoop, what's due?"), code, G, now_s=254).text
    assert text.startswith("Amiodarone three hundred milligrams not acknowledged.")
    assert "Epinephrine window open." in text
    assert "Rhythm check in" in text


def test_shocks_rhythm_clock_roles(code: CodeEngine) -> None:
    assert (
        answer(q("CodeLoop, shocks?"), code, G).text
        == "One shock. Last two hundred joules, three minutes forty two seconds ago."
    )
    assert (
        answer(q("CodeLoop, rhythm?"), code, G).text == "Last recorded rhythm V-fib, three minutes fifty seconds ago."
    )
    assert answer(q("CodeLoop, code time kitna hua?"), code, G).text == "Code time four minutes two seconds."
    assert answer(q("CodeLoop, who is on meds?"), code, G).text == "Priya on meds."


def test_unknown_question_never_guesses(code: CodeEngine) -> None:
    assert answer(q("CodeLoop, should we give bicarb?"), code, G).text == "No sodium bicarbonate recorded."
    assert answer(q("CodeLoop, what do you think?"), code, G).text == CHECK_SCREEN
