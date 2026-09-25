from conftest import ack_drug, done_drug, ev, order_drug, rhythm, shock

from codeloop.domain.models import EventKind, Rhythm
from codeloop.engine.engine import CodeEngine
from codeloop.engine.metrics import quality_metrics


def by_key(e: CodeEngine, now: float) -> dict:
    return {m["key"]: m for m in quality_metrics(e, now)}


def test_vf_code_metrics() -> None:
    e = CodeEngine()
    e.apply(ev(EventKind.CPR_START, 0))
    e.apply(ev(EventKind.CPR_PAUSE, 10))
    e.apply(rhythm(12, Rhythm.VF))
    e.apply(shock(EventKind.ORDER, 14, 200))
    e.apply(shock(EventKind.ACK, 16, 200))
    e.apply(shock(EventKind.DONE, 19, 200))
    e.apply(ev(EventKind.CPR_RESUME, 20))
    e.apply(order_drug(30, "epinephrine", 1))
    e.advance(45)  # unacknowledged
    e.apply(ack_drug(46, "epinephrine", 1))
    e.apply(done_drug(53, "epinephrine", 1))
    e.apply(order_drug(58, "amiodarone", 300))
    e.apply(ack_drug(61, "amiodarone", 150))
    e.apply(order_drug(63, "amiodarone", 300))
    e.apply(ack_drug(66, "amiodarone", 300))
    e.apply(done_drug(70, "amiodarone", 300))
    m = by_key(e, 100)
    assert m["time_to_first_shock"]["display"] == "0:19" and m["time_to_first_shock"]["status"] == "met"
    assert m["time_to_first_epinephrine"]["status"] == "info"  # shockable arrest: no 5-minute target
    assert (
        m["longest_pause"]["display"] == "10.0 s"
        and m["longest_pause"]["value"] == 10.0
        and m["longest_pause"]["status"] == "missed"
    )
    assert m["cpr_fraction"]["display"] == "90%" and m["cpr_fraction"]["status"] == "met"
    assert m["closed_loop_rate"]["display"] == "3 of 3"
    assert m["orders_unacknowledged"]["value"] == 1 and m["orders_unacknowledged"]["status"] == "missed"
    assert m["dose_conflicts"]["value"] == 1


def test_non_shockable_epinephrine_target_and_intervals() -> None:
    e = CodeEngine()
    e.apply(ev(EventKind.CPR_START, 0))
    e.apply(rhythm(10, Rhythm.ASYSTOLE))
    e.apply(done_drug(400, "epinephrine", 1))
    e.apply(done_drug(520, "epinephrine", 1))  # 2:00 apart: too early
    m = by_key(e, 600)
    assert m["time_to_first_epinephrine"]["status"] == "missed"
    assert m["epinephrine_interval"]["display"] == "0 of 1 intervals"
    assert m["given_without_order"]["value"] == 2


def test_no_metrics_before_the_code_starts() -> None:
    assert quality_metrics(CodeEngine(), 10) == []
