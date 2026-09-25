"""Closed-loop ledger behaviour."""

from __future__ import annotations

from conftest import ack_drug, done_drug, ev, order_drug, shock

from codeloop.domain.models import EventKind, LoopState, PromptPolicy
from codeloop.engine.engine import CodeEngine


def only_loop(engine: CodeEngine):
    assert len(engine.loops) == 1
    return next(iter(engine.loops.values()))


def test_order_ack_done_closes_the_loop(engine: CodeEngine) -> None:
    engine.apply(order_drug(30, "epinephrine", 1, speaker="A"))
    engine.apply(ack_drug(32, "epinephrine", 1, speaker="B"))
    out = engine.apply(done_drug(40, "epinephrine", 1, speaker="B"))
    lp = only_loop(engine)
    assert lp.state == LoopState.DONE
    assert [t.state for t in lp.history] == [LoopState.ORDERED, LoopState.ACKNOWLEDGED, LoopState.DONE]
    assert lp.ordered_by == "A" and lp.acknowledged_by == "B"
    assert engine.last_given("epinephrine").at_s == 40
    assert not engine.active_flags()
    assert not out.prompts


def test_silence_marks_unacknowledged_then_nudges_once(engine: CodeEngine) -> None:
    engine.apply(order_drug(30, "epinephrine", 1))
    assert engine.advance(39.9).empty
    out = engine.advance(40.0)
    lp = only_loop(engine)
    assert lp.state == LoopState.UNACKNOWLEDGED
    assert [f.rule for f in out.flags] == ["LOOP_UNACKNOWLEDGED"]
    assert not out.prompts  # screen first
    out = engine.advance(45.0)
    assert [p.text for p in out.prompts] == ["Epinephrine one milligram ordered. Not acknowledged."]
    assert out.prompts[0].at_s == 45.0
    assert not engine.advance(80.0).prompts  # never repeats


def test_late_acknowledgement_resolves_the_flag(engine: CodeEngine) -> None:
    engine.apply(order_drug(30, "epinephrine", 1))
    engine.advance(46)
    out = engine.apply(ack_drug(48, "epinephrine", 1))
    lp = only_loop(engine)
    assert lp.state == LoopState.ACKNOWLEDGED
    assert [f.rule for f in out.resolved_flags] == ["LOOP_UNACKNOWLEDGED"]
    assert not engine.active_flags()


def test_readback_conflict_then_restatement_then_correct_readback(engine: CodeEngine) -> None:
    engine.apply(order_drug(58, "amiodarone", 300, speaker="A"))
    out = engine.apply(ack_drug(61, "amiodarone", 150, speaker="B"))
    lp = only_loop(engine)
    assert lp.state == LoopState.CONFLICT
    assert lp.heard_value == 150
    assert [f.rule for f in out.flags] == ["LOOP_CONFLICT"]
    assert (
        out.prompts[0].text
        == "Check dose. Ordered amiodarone three hundred milligrams, read back one hundred fifty milligrams."
    )
    assert out.prompts[0].priority == 3

    out = engine.apply(order_drug(64, "amiodarone", 300, speaker="A"))  # "No. Three hundred."
    assert lp.state == LoopState.ORDERED
    assert [f.rule for f in out.resolved_flags] == ["LOOP_CONFLICT"]
    engine.apply(ack_drug(67, "amiodarone", 300, speaker="B"))
    engine.apply(done_drug(71, "amiodarone", 300, speaker="B"))
    assert lp.state == LoopState.DONE
    assert len(engine.loops) == 1
    assert [t.state for t in lp.history] == [
        LoopState.ORDERED,
        LoopState.CONFLICT,
        LoopState.ORDERED,
        LoopState.ACKNOWLEDGED,
        LoopState.DONE,
    ]
    assert engine.last_given("amiodarone").dose == 300


def test_restated_order_restarts_the_acknowledgement_clock(engine: CodeEngine) -> None:
    engine.apply(order_drug(30, "epinephrine", 1))
    engine.advance(41)
    engine.apply(order_drug(42, "epinephrine", 1))
    lp = only_loop(engine)
    assert lp.state == LoopState.ORDERED
    assert engine.advance(51).empty
    engine.advance(52)
    assert lp.state == LoopState.UNACKNOWLEDGED


def test_leader_accepting_the_readback_value_agrees_the_loop(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "amiodarone", 300))
    engine.apply(ack_drug(12, "amiodarone", 150))
    engine.apply(order_drug(14, "amiodarone", 150))  # "Yes, one fifty."
    lp = only_loop(engine)
    assert lp.state == LoopState.ACKNOWLEDGED
    assert lp.ordered_value == 150
    assert not [f for f in engine.active_flags() if f.loop_id == lp.id]


def test_orderer_changing_the_dose_reopens_the_order(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "amiodarone", 300))
    engine.apply(order_drug(12, "amiodarone", 150))  # "Actually, make it one fifty."
    lp = only_loop(engine)
    assert lp.state == LoopState.ORDERED and lp.ordered_value == 150
    assert "order changed from 300 to 150" in lp.history[-1].note


def test_given_dose_different_from_order_is_critical(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "amiodarone", 300))
    engine.apply(ack_drug(12, "amiodarone", 300))
    out = engine.apply(done_drug(20, "amiodarone", 150))
    lp = only_loop(engine)
    assert lp.state == LoopState.DONE
    assert [f.rule for f in out.flags] == ["GIVEN_DIFFERS_FROM_ORDER"]
    assert engine.last_given("amiodarone").dose == 150  # the record shows what was given


def test_generic_acknowledgement_closes_the_most_recent_order(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "epinephrine", 1))
    engine.apply(ack_drug(12, None, None))  # "Got it."
    assert only_loop(engine).state == LoopState.ACKNOWLEDGED


def test_generic_acknowledgement_ignores_stale_orders(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "epinephrine", 1))
    out = engine.apply(ack_drug(40, None, None))
    assert out.empty or only_loop(engine).state != LoopState.ACKNOWLEDGED


def test_ack_without_value_fills_missing_order_dose(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "epinephrine", None))  # "Give epi."
    engine.apply(ack_drug(12, "epinephrine", 1))
    lp = only_loop(engine)
    assert lp.state == LoopState.ACKNOWLEDGED and lp.ordered_value == 1


def test_given_without_order_is_still_recorded(engine: CodeEngine) -> None:
    engine.apply(done_drug(20, "epinephrine", 1))
    lp = only_loop(engine)
    assert lp.state == LoopState.DONE and lp.without_order
    assert engine.last_given("epinephrine") is not None


def test_cancel_closes_the_loop_and_its_flags(engine: CodeEngine) -> None:
    engine.apply(shock(EventKind.ORDER, 34, 200))
    engine.advance(45)
    out = engine.apply(shock(EventKind.CANCEL, 46, None))
    lp = only_loop(engine)
    assert lp.state == LoopState.CANCELLED
    assert out.resolved_flags
    assert not engine.shocks


def test_shock_loop_counts_shocks(engine: CodeEngine) -> None:
    engine.apply(shock(EventKind.ORDER, 15, 200))
    engine.apply(shock(EventKind.ACK, 18, 200))
    engine.apply(shock(EventKind.DONE, 21, 200))
    assert len(engine.shocks) == 1 and engine.shocks[0].energy_j == 200


def test_energy_readback_conflict_speaks_joules(engine: CodeEngine) -> None:
    engine.apply(shock(EventKind.ORDER, 15, 200))
    out = engine.apply(shock(EventKind.ACK, 17, 120))
    assert out.prompts[0].text == "Check energy. Ordered two hundred joules, read back one hundred twenty joules."


def test_two_different_drugs_keep_separate_loops(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "epinephrine", 1))
    engine.apply(order_drug(11, "amiodarone", 300))
    engine.apply(ack_drug(13, "amiodarone", 300))
    states = {lp.drug: lp.state for lp in engine.loops.values()}
    assert states == {"epinephrine": LoopState.ORDERED, "amiodarone": LoopState.ACKNOWLEDGED}


def test_low_confidence_values_mark_the_loop(engine: CodeEngine) -> None:
    engine.apply(order_drug(10, "amiodarone", 300, unconfirmed=True))
    assert only_loop(engine).needs_confirmation


def test_silent_policy_raises_flags_but_never_speaks() -> None:
    e = CodeEngine(policy=PromptPolicy.SILENT)
    e.apply(ev(EventKind.CPR_START, 0))
    e.apply(order_drug(10, "amiodarone", 300))
    out = e.apply(ack_drug(12, "amiodarone", 150))
    assert out.flags and not out.prompts
