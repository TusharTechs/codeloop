"""Resuscitation quality metrics, computed deterministically from the code's record.

These are the measures resuscitation committees and simulation debriefs review. Targets follow
AHA adult ACLS guidance and Get With The Guidelines-Resuscitation quality measures:
  - time to first shock for VF / pulseless VT ≤ 2 minutes
  - time to first epinephrine (non-shockable arrest) ≤ 5 minutes
  - chest-compression fraction ≥ 80%, pauses under 10 seconds
  - epinephrine every 3–5 minutes
CPR timing is estimated from spoken calls ("pause compressions", "resume"), so the CPR metrics
are labelled as estimates; a defibrillator's accelerometer data would replace them in production.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import pairwise
from statistics import median

from ..domain.models import Action, LoopState
from .engine import CodeEngine


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    value: float | None
    display: str
    target: str
    status: str  # "met" | "missed" | "info" | "n/a"
    note: str = ""


def _mmss(s: float | None) -> str:
    if s is None:
        return "—"
    s = max(0, round(s))
    return f"{s // 60}:{s % 60:02d}"


def quality_metrics(engine: CodeEngine, now_s: float | None = None) -> list[dict]:
    e = engine
    if e.started_at_s is None:
        return []
    start = e.started_at_s
    end = (
        e.ended_at_s
        if e.ended_at_s is not None
        else (e.pending_end[1] if e.pending_end is not None else (now_s if now_s is not None else e.now_s))
    )
    out: list[Metric] = []

    # Time to first shock, for shockable arrests.
    shockable_seen = next((t for t, r in e.rhythm_history if r in e.f.shockable), None)
    if shockable_seen is not None or e.shocks:
        t = e.shocks[0].at_s - start if e.shocks else None
        if t is None:
            out.append(
                Metric(
                    "time_to_first_shock",
                    "Time to first shock",
                    None,
                    "no shock yet",
                    "≤ 2:00 for VF/pVT",
                    "missed" if end - start > 120 else "n/a",
                )
            )
        else:
            out.append(
                Metric(
                    "time_to_first_shock",
                    "Time to first shock",
                    round(t, 1),
                    _mmss(t),
                    "≤ 2:00 for VF/pVT",
                    "met" if t <= 120 else "missed",
                )
            )

    # Time to first epinephrine.
    epi = [a for a in e.given if a.drug == "epinephrine"]
    nonshockable = any(r not in e.f.shockable for _, r in e.rhythm_history if r.value != "SINUS")
    if epi:
        t = epi[0].at_s - start
        out.append(
            Metric(
                "time_to_first_epinephrine",
                "Time to first epinephrine",
                round(t, 1),
                _mmss(t),
                "≤ 5:00 (non-shockable)",
                ("met" if t <= 300 else "missed") if nonshockable else "info",
            )
        )
    elif end - start > 300 and nonshockable:
        out.append(
            Metric(
                "time_to_first_epinephrine",
                "Time to first epinephrine",
                None,
                "not given",
                "≤ 5:00 (non-shockable)",
                "missed",
            )
        )

    # Epinephrine spacing.
    if len(epi) >= 2:
        gaps = [b.at_s - a.at_s for a, b in pairwise(epi)]
        ok = sum(1 for g in gaps if 180 <= g <= 300)
        out.append(
            Metric(
                "epinephrine_interval",
                "Epinephrine every 3–5 min",
                ok / len(gaps),
                f"{ok} of {len(gaps)} intervals",
                "every interval 3–5 min",
                "met" if ok == len(gaps) else "missed",
                "intervals " + ", ".join(_mmss(g) for g in gaps),
            )
        )

    # CPR fraction and pauses (estimated from spoken CPR calls).
    if e.cpr_segments:
        first = e.cpr_segments[0][0]
        assert first is not None
        span = end - first
        on = sum(((seg[1] if seg[1] is not None else end) - seg[0]) for seg in e.cpr_segments if seg[0] is not None)
        if span > 0:
            frac = on / span
            out.append(
                Metric(
                    "cpr_fraction",
                    "Compression fraction (est.)",
                    round(frac, 3),
                    f"{frac * 100:.0f}%",
                    "≥ 80%",
                    "met" if frac >= 0.8 else "missed",
                    "from spoken pause/resume calls",
                )
            )
        pauses = [
            nxt[0] - seg[1]
            for seg, nxt in zip(e.cpr_segments, e.cpr_segments[1:], strict=False)
            if seg[1] is not None and nxt[0] is not None
        ]
        if pauses:
            longest = max(pauses)
            out.append(
                Metric(
                    "longest_pause",
                    "Longest pause in compressions (est.)",
                    round(longest, 1),
                    f"{longest:.1f} s",
                    "< 10 s",
                    "met" if longest < 10 else "missed",
                    f"{len(pauses)} pause{'s' if len(pauses) != 1 else ''}",
                )
            )

    # Closed-loop communication.
    ordered = [lp for lp in e.loops.values() if not lp.without_order]
    if ordered:
        read_back = [lp for lp in ordered if any(h.state == LoopState.ACKNOWLEDGED for h in lp.history)]
        rate = len(read_back) / len(ordered)
        out.append(
            Metric(
                "closed_loop_rate",
                "Orders read back (closed loop)",
                round(rate, 3),
                f"{len(read_back)} of {len(ordered)}",
                "every order",
                "met" if rate == 1 else "missed",
            )
        )
        waits = []
        for lp in read_back:
            first_ack = next(h.at_s for h in lp.history if h.state == LoopState.ACKNOWLEDGED)
            waits.append(first_ack - lp.opened_at_s)
        if waits:
            m = median(waits)
            out.append(Metric("time_to_read_back", "Median time to read-back", round(m, 1), f"{m:.0f} s", "—", "info"))
        unack = sum(1 for lp in ordered if any(h.state == LoopState.UNACKNOWLEDGED for h in lp.history))
        conflicts = sum(1 for lp in ordered if any(h.state == LoopState.CONFLICT for h in lp.history))
        out.append(
            Metric(
                "orders_unacknowledged",
                "Orders left unacknowledged ≥ 10 s",
                unack,
                str(unack),
                "0",
                "met" if unack == 0 else "missed",
            )
        )
        out.append(
            Metric(
                "dose_conflicts",
                "Read-back conflicts caught",
                conflicts,
                str(conflicts),
                "—",
                "info",
                "each one a potential dosing error caught before it was given",
            )
        )
    given_without_order = sum(
        1 for lp in e.loops.values() if lp.without_order and lp.state == LoopState.DONE and lp.action == Action.DRUG
    )
    if given_without_order:
        out.append(
            Metric(
                "given_without_order",
                "Drugs given with no order heard",
                given_without_order,
                str(given_without_order),
                "0",
                "missed",
            )
        )
    return [asdict(m) for m in out]
