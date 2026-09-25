"""ACLS clock, protocol checks, snapshot and determinism."""

from __future__ import annotations

from conftest import done_drug, ev, order_drug, rhythm, shock

from codeloop.domain.models import EventKind, PromptPolicy, Rhythm
from codeloop.engine.engine import CodeEngine


def prompts_between(engine: CodeEngine, start: float, end: float, step: float = 0.25) -> list:
    out = []
    t = start
    while t <= end:
        out += engine.advance(t).prompts
        t += step
    return out


def test_cpr_cycle_warns_then_calls_rhythm_check_once(engine: CodeEngine) -> None:
    ps = prompts_between(engine, 0, 130)
    assert [(p.rule, p.at_s) for p in ps] == [("CPR_CYCLE_WARN", 105), ("CPR_CYCLE_DUE", 120)]
    assert ps[0].text == "Fifteen seconds to rhythm check."
    assert ps[1].text == "Two minutes. Pause compressions for rhythm and pulse check."


def test_pause_and_resume_start_a_new_cycle(engine: CodeEngine) -> None:
    prompts_between(engine, 0, 121)
    engine.apply(ev(EventKind.CPR_PAUSE, 122))
    assert engine.cycle_index == 1
    assert not prompts_between(engine, 122, 131)  # no cycle prompts while paused
    engine.apply(ev(EventKind.CPR_RESUME, 131))
    ps = prompts_between(engine, 131, 252)
    assert [(p.rule, p.at_s) for p in ps] == [("CPR_CYCLE_WARN", 236), ("CPR_CYCLE_DUE", 251)]


def test_short_pause_does_not_count_as_a_cycle(engine: CodeEngine) -> None:
    engine.apply(ev(EventKind.CPR_PAUSE, 30))
    assert engine.cycle_index == 0


def test_epinephrine_window_opens_at_three_and_overdue_at_five_minutes(engine: CodeEngine) -> None:
    engine.apply(order_drug(30, "epinephrine", 1))
    engine.apply(done_drug(40, "epinephrine", 1))
    ps = [p for p in prompts_between(engine, 40, 350) if p.rule.startswith("EPI")]
    assert [(p.rule, p.at_s) for p in ps] == [("EPI_WINDOW_OPEN", 220), ("EPI_OVERDUE", 340)]
    assert ps[0].text == "Epinephrine window open. Last dose three minutes ago."
    assert ps[1].text == "Five minutes since last epinephrine."
    assert any(f.rule == "EPI_OVERDUE" for f in engine.active_flags())


def test_new_epinephrine_dose_resets_the_window(engine: CodeEngine) -> None:
    engine.apply(done_drug(40, "epinephrine", 1))
    prompts_between(engine, 40, 230)
    engine.apply(done_drug(230, "epinephrine", 1))
    snap = engine.snapshot(231)
    assert snap["epinephrine_window"]["state"] == "waiting"
    ps = [p for p in prompts_between(engine, 231, 420) if p.rule == "EPI_WINDOW_OPEN"]
    assert [p.at_s for p in ps] == [410]


def test_shock_on_non_shockable_rhythm_is_flagged_and_spoken(engine: CodeEngine) -> None:
    engine.apply(rhythm(10, Rhythm.ASYSTOLE))
    out = engine.apply(shock(EventKind.ORDER, 34, 200))
    assert [f.rule for f in out.flags] == ["RHYTHM_NONSHOCKABLE_CHARGE"]
    assert out.prompts[0].text == "Check rhythm. Last recorded rhythm is asystole."


def test_shock_on_shockable_rhythm_is_quiet(engine: CodeEngine) -> None:
    engine.apply(rhythm(10, Rhythm.VF))
    out = engine.apply(shock(EventKind.ORDER, 12, 200))
    assert not out.flags and not out.prompts


def test_amiodarone_sequence_checks(engine: CodeEngine) -> None:
    out = engine.apply(order_drug(10, "amiodarone", 150))
    assert [f.rule for f in out.flags] == ["AMIODARONE_SEQUENCE_DOSE"]
    engine.apply(done_drug(12, "amiodarone", 150))
    engine.apply(done_drug(300, "amiodarone", 150))
    out = engine.apply(order_drug(600, "amiodarone", 150))
    assert "AMIODARONE_BEYOND_SEQUENCE" in [f.rule for f in out.flags]


def test_early_epinephrine_is_an_info_flag_not_a_prompt(engine: CodeEngine) -> None:
    engine.apply(done_drug(10, "epinephrine", 1))
    out = engine.apply(order_drug(70, "epinephrine", 1))
    assert [f.rule for f in out.flags] == ["EPINEPHRINE_EARLY"]
    assert not out.prompts


def test_rosc_stops_the_clock_and_all_timers(engine: CodeEngine) -> None:
    engine.apply(done_drug(10, "epinephrine", 1))
    engine.apply(ev(EventKind.ROSC, 60))
    assert engine.snapshot(500)["status"] == "ended"
    assert engine.clock_s(500) == 60
    assert not prompts_between(engine, 60, 500, step=5)


def test_timers_only_policy_speaks_timers_not_loops() -> None:
    e = CodeEngine(policy=PromptPolicy.TIMERS)
    e.apply(ev(EventKind.CPR_START, 0))
    e.apply(order_drug(10, "epinephrine", 1))
    ps = prompts_between(e, 10, 121)
    assert {p.rule for p in ps} == {"CPR_CYCLE_WARN", "CPR_CYCLE_DUE"}


def test_self_assigned_role_maps_the_speaker() -> None:
    e = CodeEngine()
    from codeloop.domain.models import Role

    e.apply(ev(EventKind.ROLE, 1, role=Role.LEADER, speaker="A"))
    e.apply(ev(EventKind.ROLE, 1, role=Role.MEDS, name="Priya", speaker="A"))
    assert e.roles == {"A": Role.LEADER}
    assert e.names == {"priya": Role.MEDS}


def test_snapshot_reports_what_the_voice_agent_may_say(engine: CodeEngine) -> None:
    engine.apply(rhythm(12, Rhythm.VF))
    engine.apply(shock(EventKind.DONE, 20, 200))
    engine.apply(done_drug(52, "epinephrine", 1))
    engine.apply(order_drug(58, "amiodarone", 300))
    snap = engine.snapshot(242)
    assert snap["clock_s"] == 242
    assert snap["rhythm"]["current"] == "VF" and snap["rhythm"]["shockable"] is True
    assert snap["shocks"] == {"count": 1, "last_energy_j": "200", "last_seconds_ago": 222}
    assert snap["last_drugs"]["epinephrine"]["seconds_ago"] == 190
    assert snap["epinephrine_window"]["state"] == "open"
    assert snap["open_orders"][0]["order"] == "amiodarone 300 mg"


def test_replay_is_deterministic() -> None:
    def run() -> dict:
        e = CodeEngine()
        e.apply(ev(EventKind.CPR_START, 0))
        e.apply(rhythm(12, Rhythm.VF))
        e.apply(order_drug(30, "epinephrine", 1))
        e.advance(45)
        e.apply(order_drug(58, "amiodarone", 300))
        e.apply(done_drug(60, "amiodarone", 150))
        e.advance(400)
        snap = e.snapshot()
        return {
            "snap": snap,
            "loops": [lp.model_dump() for lp in e.loops.values()],
            "flags": sorted(f.rule for f in e.flags.values()),
        }

    a, b = run(), run()
    for x in (a, b):  # event ids differ between runs; compare everything else
        for lp in x["loops"]:
            lp.pop("order_event_id")
            for h in lp["history"]:
                h.pop("event_id")
    assert a == b
