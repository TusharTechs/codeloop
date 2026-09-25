"""The deterministic heart of CodeLoop.

`CodeEngine` consumes validated events (from the extractor or a human) and the passage of
code time, and produces loop changes, flags and spoken prompts. It performs no I/O, never
calls a model and never reads the wall clock, so every behaviour is unit-testable and a
recorded code replays to exactly the same result.

Two responsibilities:
  1. Closed-loop ledger: every order opens a loop that must be acknowledged and completed.
     Silence past the threshold → UNACKNOWLEDGED. A read-back with a different value →
     CONFLICT. Nothing is ever deleted; every transition is kept in the loop history.
  2. ACLS clock: 2-minute CPR cycles, the epinephrine 3–5 minute window, shock count,
     rhythm consistency, amiodarone sequence. It reminds and flags; it never recommends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

from ..domain.formulary import Formulary, default_formulary
from ..domain.models import (
    Action,
    Event,
    EventKind,
    Flag,
    FlagSeverity,
    Loop,
    LoopState,
    LoopTransition,
    Prompt,
    PromptCategory,
    PromptPolicy,
    Rhythm,
    Role,
    fmt_num,
)
from .speech import say_drug, say_duration, say_quantity

GENERIC_ACK_WINDOW_S = 20.0  # "got it" with no drug named acknowledges an order this recent
VALUE_TOLERANCE = 1e-6


@dataclass
class EngineOutput:
    loops: list[Loop] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)
    resolved_flags: list[Flag] = field(default_factory=list)
    prompts: list[Prompt] = field(default_factory=list)
    state_changed: bool = False

    def extend(self, other: EngineOutput) -> None:
        self.loops += [lp for lp in other.loops if lp not in self.loops]
        self.flags += other.flags
        self.resolved_flags += other.resolved_flags
        self.prompts += other.prompts
        self.state_changed |= other.state_changed

    @property
    def empty(self) -> bool:
        return not (self.loops or self.flags or self.resolved_flags or self.prompts or self.state_changed)


@dataclass
class Administration:
    at_s: float
    drug: str
    dose: float | None
    unit: str | None
    loop_id: str


@dataclass
class ShockRecord:
    at_s: float
    energy_j: float | None
    loop_id: str


class CodeEngine:
    def __init__(
        self, formulary: Formulary | None = None, policy: PromptPolicy = PromptPolicy.TIMERS_AND_LOOPS
    ) -> None:
        self.f = formulary or default_formulary()
        self.policy = policy
        self.now_s = 0.0
        self.started_at_s: float | None = None
        self.ended_at_s: float | None = None
        self.outcome: str | None = None
        # ROSC / termination heard but not yet confirmed by a human: one mis-heard word must
        # never end a resuscitation, so the code only ends through confirm_end()/end_code().
        self.pending_end: tuple[str, float] | None = None
        self.cpr_running = False
        self.cpr_segments: list[list[float | None]] = []
        self.cycle_started_at_s: float | None = None
        self.cycle_index = 0
        self.rhythm: Rhythm | None = None
        self.rhythm_at_s: float | None = None
        self.rhythm_history: list[tuple[float, Rhythm]] = []
        self.shocks: list[ShockRecord] = []
        self.given: list[Administration] = []
        self.loops: dict[str, Loop] = {}
        self.flags: dict[str, Flag] = {}
        self.events: list[Event] = []
        self.roles: dict[str, Role] = {}  # diarization label → role
        self.names: dict[str, Role] = {}  # spoken name → role (from the role call)
        self._fired: set[str] = set()
        self._ids = {k: count(1) for k in ("L", "F", "P")}

    # ------------------------------------------------------------------ public API

    @property
    def active(self) -> bool:
        return self.started_at_s is not None and self.ended_at_s is None

    def clock_s(self, now_s: float | None = None) -> float:
        if self.started_at_s is None:
            return 0.0
        end = self.ended_at_s if self.ended_at_s is not None else (now_s if now_s is not None else self.now_s)
        return max(0.0, end - self.started_at_s)

    def advance(self, now_s: float) -> EngineOutput:
        """Move code time forward, firing any timers that came due. Idempotent."""
        out = EngineOutput()
        if now_s < self.now_s:
            return out
        self.now_s = now_s
        if not self.active:
            return out
        out.extend(self._check_loops(now_s))
        if self.pending_end is None:
            out.extend(self._check_cycle(now_s))
            out.extend(self._check_epinephrine(now_s))
        return out

    def confirm_end(self, at_s: float | None = None) -> EngineOutput:
        """A human confirmed the ROSC / termination that was heard."""
        if self.pending_end is None:
            return EngineOutput()
        outcome, heard_at = self.pending_end
        return self.end_code(heard_at if at_s is None else at_s, outcome)

    def reject_end(self) -> EngineOutput:
        """A human rejected a heard ROSC / termination (mis-heard, or re-arrest)."""
        self.pending_end = None
        return EngineOutput(state_changed=True)

    def end_code(self, at_s: float, outcome: str) -> EngineOutput:
        if self.ended_at_s is not None:
            return EngineOutput()
        if self.cpr_running:
            self.cpr_running = False
            self.cpr_segments[-1][1] = at_s
            self.cycle_started_at_s = None
        self.pending_end = None
        self.ended_at_s = at_s
        self.outcome = outcome
        if outcome == "rosc":
            self.rhythm_history.append((at_s, Rhythm.SINUS))
        return EngineOutput(state_changed=True)

    def apply(self, ev: Event) -> EngineOutput:
        """Apply one validated event. Advances time to the event first."""
        out = self.advance(max(ev.at_s, self.now_s))
        self.events.append(ev)
        if self.started_at_s is None and ev.kind not in (EventKind.ROLE, EventKind.QUESTION):
            self.started_at_s = ev.at_s
            out.state_changed = True
        handler = {
            EventKind.CPR_START: self._on_cpr_start,
            EventKind.CPR_RESUME: self._on_cpr_start,
            EventKind.CPR_PAUSE: self._on_cpr_pause,
            EventKind.RHYTHM: self._on_rhythm,
            EventKind.ORDER: self._on_order,
            EventKind.ACK: self._on_ack,
            EventKind.DONE: self._on_done,
            EventKind.CANCEL: self._on_cancel,
            EventKind.ROSC: self._on_end,
            EventKind.TERMINATE: self._on_end,
            EventKind.ROLE: self._on_role,
        }.get(ev.kind)
        if handler:
            out.extend(handler(ev))
        return out

    def assign_role(self, speaker: str, role: Role) -> None:
        self.roles[speaker] = role

    def role_of(self, speaker: str | None) -> Role | None:
        return self.roles.get(speaker) if speaker else None

    def open_loops(self) -> list[Loop]:
        return [lp for lp in self.loops.values() if lp.state.is_open]

    def active_flags(self) -> list[Flag]:
        return [fl for fl in self.flags.values() if fl.resolved_at_s is None]

    def last_given(self, drug: str) -> Administration | None:
        for a in reversed(self.given):
            if a.drug == drug:
                return a
        return None

    def snapshot(self, now_s: float | None = None) -> dict:
        """Everything the UI and the voice agent's tools may say about the code."""
        now = self.now_s if now_s is None else now_s
        cycle = None
        if self.cpr_running and self.cycle_started_at_s is not None:
            el = now - self.cycle_started_at_s
            cycle = {"elapsed_s": round(el, 1), "remaining_s": round(max(0.0, self.f.timers.cpr_cycle_s - el), 1)}
        last_drugs = {}
        for drug in {a.drug for a in self.given}:
            a = self.last_given(drug)
            assert a is not None
            last_drugs[drug] = {
                "dose": fmt_num(a.dose),
                "unit": a.unit,
                "given_at_clock_s": round(self.clock_s(a.at_s), 1),
                "seconds_ago": round(now - a.at_s, 1),
                "total_doses": sum(1 for x in self.given if x.drug == drug),
            }
        return {
            "status": self._status(),
            "outcome": self.outcome,
            "clock_s": round(self.clock_s(now), 1),
            "cpr": {"running": self.cpr_running, "cycle": cycle, "cycles_completed": self.cycle_index},
            "rhythm": {
                "current": self.rhythm.value if self.rhythm else None,
                "recorded_seconds_ago": round(now - self.rhythm_at_s, 1) if self.rhythm_at_s else None,
                "shockable": self.rhythm in self.f.shockable if self.rhythm else None,
            },
            "shocks": {
                "count": len(self.shocks),
                "last_energy_j": fmt_num(self.shocks[-1].energy_j) if self.shocks else None,
                "last_seconds_ago": round(now - self.shocks[-1].at_s, 1) if self.shocks else None,
            },
            "last_drugs": last_drugs,
            "epinephrine_window": self._epi_window(now),
            "open_orders": [
                {
                    "id": lp.id,
                    "order": lp.label(),
                    "state": lp.state.value,
                    "seconds_open": round(now - lp.ordered_at_s, 1),
                    "heard_value": fmt_num(lp.heard_value) if lp.heard_value is not None else None,
                }
                for lp in self.open_loops()
            ],
            "active_flags": [
                {"rule": fl.rule, "severity": fl.severity.value, "message": fl.message} for fl in self.active_flags()
            ],
            "roles": {k: v.value for k, v in self.roles.items()},
        }

    def _status(self) -> str:
        if self.started_at_s is None:
            return "not_started"
        if self.ended_at_s is not None:
            return "ended"
        if self.pending_end is not None:
            return f"{self.pending_end[0]}_pending_confirmation"
        return "active"

    # ------------------------------------------------------------------ helpers

    def _id(self, prefix: str) -> str:
        return f"{prefix}{next(self._ids[prefix])}"

    def _flag(
        self,
        rule: str,
        severity: FlagSeverity,
        message: str,
        at_s: float,
        loop: Loop | None = None,
        ev: Event | None = None,
    ) -> Flag:
        fl = Flag(
            id=self._id("F"),
            rule=rule,
            severity=severity,
            message=message,
            at_s=at_s,
            loop_id=loop.id if loop else None,
            event_id=ev.id if ev else None,
        )
        self.flags[fl.id] = fl
        return fl

    def _resolve_flags(self, loop: Loop, at_s: float, rules: set[str] | None = None) -> list[Flag]:
        done = []
        for fl in self.flags.values():
            if fl.loop_id == loop.id and fl.resolved_at_s is None and (rules is None or fl.rule in rules):
                fl.resolved_at_s = at_s
                done.append(fl)
        return done

    def _prompt(
        self,
        rule: str,
        category: PromptCategory,
        text: str,
        at_s: float,
        key: str,
        priority: int = 1,
        loop: Loop | None = None,
    ) -> list[Prompt]:
        """Emit a spoken prompt once per key, if the prompt policy allows its category."""
        if key in self._fired or not self.policy.allows(category):
            return []
        self._fired.add(key)
        return [
            Prompt(
                id=self._id("P"),
                rule=rule,
                category=category,
                text=text,
                at_s=at_s,
                priority=priority,
                loop_id=loop.id if loop else None,
            )
        ]

    def _transition(self, loop: Loop, state: LoopState, at_s: float, ev: Event | None, note: str = "") -> None:
        loop.state = state
        loop.history.append(LoopTransition(at_s=at_s, state=state, event_id=ev.id if ev else None, note=note))
        if not state.is_open:
            loop.closed_at_s = at_s

    def _find_open(self, ev: Event) -> Loop | None:
        """Most recent open loop for the same action (and drug, for drugs)."""
        for lp in reversed(list(self.loops.values())):
            if not lp.state.is_open or lp.action != ev.action:
                continue
            if ev.action == Action.DRUG and ev.drug and lp.drug != ev.drug:
                continue
            return lp
        return None

    def generic_ack_target(self, ev: Event) -> Loop | None:
        for lp in reversed(list(self.loops.values())):
            if (
                lp.state in (LoopState.ORDERED, LoopState.UNACKNOWLEDGED)
                and ev.at_s - lp.ordered_at_s <= GENERIC_ACK_WINDOW_S
            ):
                return lp
        return None

    @staticmethod
    def _same(a: float | None, b: float | None) -> bool:
        return a is None or b is None or abs(a - b) <= VALUE_TOLERANCE

    def _new_loop(self, ev: Event, state: LoopState, without_order: bool = False) -> Loop:
        lp = Loop(
            id=self._id("L"),
            action=ev.action or Action.DRUG,
            drug=ev.drug,
            ordered_value=ev.value(),
            unit=ev.unit if ev.action == Action.DRUG else "J",
            state=state,
            opened_at_s=ev.at_s,
            ordered_at_s=ev.at_s,
            order_event_id=ev.id if ev.kind == EventKind.ORDER else None,
            ordered_by=ev.speaker if ev.kind == EventKind.ORDER else None,
            acknowledged_by=ev.speaker if ev.kind in (EventKind.ACK, EventKind.DONE) else None,
            without_order=without_order,
            needs_confirmation=ev.unconfirmed,
            history=[
                LoopTransition(
                    at_s=ev.at_s,
                    state=state,
                    event_id=ev.id,
                    note="given without an order heard" if without_order else "",
                )
            ],
        )
        self.loops[lp.id] = lp
        return lp

    def _qty(self, loop: Loop, value: float | None) -> str:
        if loop.action == Action.SHOCK:
            return say_quantity(value, "J")
        return say_quantity(value, loop.unit)

    def _spoken_order(self, loop: Loop) -> str:
        if loop.action == Action.SHOCK:
            return f"Shock {self._qty(loop, loop.ordered_value)}".strip()
        return f"{say_drug(loop.drug).capitalize()} {self._qty(loop, loop.ordered_value)}".strip()

    # ------------------------------------------------------------------ event handlers

    def _on_cpr_start(self, ev: Event) -> EngineOutput:
        out = EngineOutput()
        if self.cpr_running or not self.active:
            return out
        if self.pending_end is not None:
            # CPR restarted after ROSC was called: re-arrest, or the ROSC was mis-heard.
            for fl in self.flags.values():
                if fl.rule.endswith("_NEEDS_CONFIRMATION") and fl.resolved_at_s is None:
                    fl.resolved_at_s = ev.at_s
                    out.resolved_flags.append(fl)
            out.flags.append(
                self._flag(
                    "CPR_RESUMED_AFTER_ROSC", FlagSeverity.WARNING, "CPR resumed after ROSC was called", ev.at_s, ev=ev
                )
            )
            self.pending_end = None
        self.cpr_running = True
        self.cpr_segments.append([ev.at_s, None])
        self.cycle_started_at_s = ev.at_s
        out.state_changed = True
        return out

    def _on_cpr_pause(self, ev: Event) -> EngineOutput:
        out = EngineOutput()
        if not self.cpr_running:
            return out
        self.cpr_running = False
        self.cpr_segments[-1][1] = ev.at_s
        if self.cycle_started_at_s is not None and ev.at_s - self.cycle_started_at_s >= self.f.timers.cpr_cycle_warn_s:
            self.cycle_index += 1
        self.cycle_started_at_s = None
        out.state_changed = True
        return out

    def _on_rhythm(self, ev: Event) -> EngineOutput:
        if ev.rhythm is None:
            return EngineOutput()
        self.rhythm = ev.rhythm
        self.rhythm_at_s = ev.at_s
        self.rhythm_history.append((ev.at_s, ev.rhythm))
        return EngineOutput(state_changed=True)

    def _on_order(self, ev: Event) -> EngineOutput:
        out = EngineOutput(state_changed=True)
        out.extend(self._protocol_checks(ev))
        lp = self._find_open(ev)
        value = ev.value()
        if lp is None:
            lp = self._new_loop(ev, LoopState.ORDERED)
            out.loops.append(lp)
            return out
        # The order was stated again, or changed, while its loop is still open.
        if (
            lp.state == LoopState.CONFLICT
            and self._same(value, lp.heard_value)
            and value is not None
            and not self._same(value, lp.ordered_value)
        ):
            # Leader accepts the value that was read back: both sides now agree.
            lp.ordered_value = value
            self._transition(lp, LoopState.ACKNOWLEDGED, ev.at_s, ev, "order changed to the read-back value")
            out.resolved_flags += self._resolve_flags(lp, ev.at_s)
        elif self._same(value, lp.ordered_value):
            note = "order restated"
            if lp.state == LoopState.CONFLICT:
                note = "order restated to resolve read-back conflict"
                out.resolved_flags += self._resolve_flags(lp, ev.at_s, {"LOOP_CONFLICT"})
            elif lp.state == LoopState.UNACKNOWLEDGED:
                out.resolved_flags += self._resolve_flags(lp, ev.at_s, {"LOOP_UNACKNOWLEDGED"})
            if lp.ordered_value is None and value is not None:
                lp.ordered_value = value
            lp.ordered_at_s = ev.at_s
            lp.heard_value = None
            self._fired.discard(f"unack:{lp.id}")
            self._fired.discard(f"unack-nudge:{lp.id}")
            self._transition(lp, LoopState.ORDERED, ev.at_s, ev, note)
        else:
            # A different value from the orderer is a changed order.
            old = lp.ordered_value
            lp.ordered_value = value
            lp.ordered_at_s = ev.at_s
            lp.heard_value = None
            out.resolved_flags += self._resolve_flags(lp, ev.at_s)
            self._transition(
                lp, LoopState.ORDERED, ev.at_s, ev, f"order changed from {fmt_num(old)} to {fmt_num(value)}"
            )
        if ev.unconfirmed:
            lp.needs_confirmation = True
        out.loops.append(lp)
        return out

    def _on_ack(self, ev: Event) -> EngineOutput:
        out = EngineOutput(state_changed=True)
        lp = self._find_open(ev) if ev.action else self.generic_ack_target(ev)
        if lp is None:
            if ev.action is None:
                return EngineOutput()
            lp = self._new_loop(ev, LoopState.ACKNOWLEDGED, without_order=True)
            out.loops.append(lp)
            return out
        value = ev.value()
        if ev.unconfirmed:
            lp.needs_confirmation = True
        if self._same(value, lp.ordered_value):
            if lp.ordered_value is None and value is not None:
                lp.ordered_value = value
            lp.acknowledged_by = ev.speaker
            lp.heard_value = None
            if lp.state in (LoopState.ORDERED, LoopState.UNACKNOWLEDGED, LoopState.CONFLICT):
                self._transition(
                    lp,
                    LoopState.ACKNOWLEDGED,
                    ev.at_s,
                    ev,
                    "read-back matches" if value is not None else "acknowledged",
                )
                out.resolved_flags += self._resolve_flags(lp, ev.at_s, {"LOOP_UNACKNOWLEDGED", "LOOP_CONFLICT"})
        else:
            out.extend(self._conflict(lp, ev, value, "read back"))
        out.loops.append(lp)
        return out

    def _conflict(self, lp: Loop, ev: Event, heard: float | None, verb: str) -> EngineOutput:
        out = EngineOutput(state_changed=True)
        lp.heard_value = heard
        self._transition(
            lp, LoopState.CONFLICT, ev.at_s, ev, f"{verb} {fmt_num(heard)} ≠ ordered {fmt_num(lp.ordered_value)}"
        )
        out.resolved_flags += self._resolve_flags(lp, ev.at_s, {"LOOP_UNACKNOWLEDGED"})
        unit = "J" if lp.action == Action.SHOCK else (lp.unit or "")
        fl = self._flag(
            "LOOP_CONFLICT",
            FlagSeverity.CRITICAL,
            f"{lp.label()} ordered, {verb} {fmt_num(heard)} {unit}".strip(),
            ev.at_s,
            lp,
            ev,
        )
        out.flags.append(fl)
        what = "Check energy" if lp.action == Action.SHOCK else "Check dose"
        subject = "" if lp.action == Action.SHOCK else f"{say_drug(lp.drug)} "
        text = f"{what}. Ordered {subject}{self._qty(lp, lp.ordered_value)}, {verb} {self._qty(lp, heard)}."
        out.prompts += self._prompt(
            "LOOP_CONFLICT", PromptCategory.LOOP, text, ev.at_s, key=f"conflict:{lp.id}:{ev.id}", priority=3, loop=lp
        )
        return out

    def _on_done(self, ev: Event) -> EngineOutput:
        out = EngineOutput(state_changed=True)
        lp = self._find_open(ev)
        value = ev.value()
        if lp is None:
            lp = self._new_loop(ev, LoopState.DONE, without_order=True)
            lp.closed_at_s = ev.at_s
        else:
            if ev.unconfirmed:
                lp.needs_confirmation = True
            if self._same(value, lp.ordered_value):
                if lp.ordered_value is None:
                    lp.ordered_value = value
                self._transition(lp, LoopState.DONE, ev.at_s, ev, "completed")
                out.resolved_flags += self._resolve_flags(lp, ev.at_s, {"LOOP_UNACKNOWLEDGED", "LOOP_CONFLICT"})
            else:
                # Given with a different value than ordered: record what was actually given.
                ordered = lp.ordered_value
                self._transition(
                    lp, LoopState.DONE, ev.at_s, ev, f"given {fmt_num(value)} but ordered {fmt_num(ordered)}"
                )
                out.resolved_flags += self._resolve_flags(lp, ev.at_s, {"LOOP_UNACKNOWLEDGED"})
                out.flags.append(
                    self._flag(
                        "GIVEN_DIFFERS_FROM_ORDER",
                        FlagSeverity.CRITICAL,
                        f"{lp.label()} ordered, {fmt_num(value)} {lp.unit or 'J'} given",
                        ev.at_s,
                        lp,
                        ev,
                    )
                )
                lp.heard_value = value
        if not lp.acknowledged_by:
            lp.acknowledged_by = ev.speaker
        given_value = value if value is not None else lp.ordered_value
        if lp.action == Action.SHOCK:
            self.shocks.append(ShockRecord(ev.at_s, given_value, lp.id))
        else:
            self.given.append(Administration(ev.at_s, lp.drug or "unknown", given_value, lp.unit, lp.id))
            if lp.drug == "epinephrine":
                for k in ("epi-open", "epi-overdue"):
                    self._fired = {x for x in self._fired if not x.startswith(k)}
        out.loops.append(lp)
        return out

    def _on_cancel(self, ev: Event) -> EngineOutput:
        out = EngineOutput(state_changed=True)
        lp = self._find_open(ev) if ev.action else next(iter(reversed(self.open_loops())), None)
        if lp is None:
            return EngineOutput()
        self._transition(lp, LoopState.CANCELLED, ev.at_s, ev, "cancelled")
        out.resolved_flags += self._resolve_flags(lp, ev.at_s)
        out.loops.append(lp)
        return out

    def _on_end(self, ev: Event) -> EngineOutput:
        if self.ended_at_s is not None:
            return EngineOutput()
        out = EngineOutput(state_changed=True)
        if self.cpr_running:
            self._on_cpr_pause(ev)
        outcome = "rosc" if ev.kind == EventKind.ROSC else "terminated"
        self.pending_end = (outcome, ev.at_s)
        what = "ROSC" if outcome == "rosc" else "Termination"
        out.flags.append(
            self._flag(
                f"{what.upper()}_NEEDS_CONFIRMATION",
                FlagSeverity.WARNING,
                f"{what} heard: confirm to end the code",
                ev.at_s,
                ev=ev,
            )
        )
        return out

    def _on_role(self, ev: Event) -> EngineOutput:
        if ev.role is None:
            return EngineOutput()
        if ev.name:
            self.names[ev.name.lower()] = ev.role
        else:  # self-assignment: "I'm leading"
            if ev.speaker:
                self.roles[ev.speaker] = ev.role
        return EngineOutput(state_changed=True)

    # ------------------------------------------------------------------ protocol checks

    def _protocol_checks(self, ev: Event) -> EngineOutput:
        out = EngineOutput()
        if ev.action == Action.SHOCK and self.rhythm is not None and self.rhythm not in self.f.shockable:
            key = f"nonshockable:{ev.id}"
            msg = f"Shock ordered but last recorded rhythm is {self.rhythm.value}"
            out.flags.append(self._flag("RHYTHM_NONSHOCKABLE_CHARGE", FlagSeverity.CRITICAL, msg, ev.at_s, ev=ev))
            rhythm_word = {"ASYSTOLE": "asystole", "PEA": "P E A", "SINUS": "an organized rhythm"}.get(
                self.rhythm.value, self.rhythm.value
            )
            out.prompts += self._prompt(
                "RHYTHM_NONSHOCKABLE_CHARGE",
                PromptCategory.SAFETY,
                f"Check rhythm. Last recorded rhythm is {rhythm_word}.",
                ev.at_s,
                key=key,
                priority=3,
            )
        if ev.action == Action.DRUG and ev.drug:
            drug = self.f.drugs.get(ev.drug)
            prior = [a for a in self.given if a.drug == ev.drug]
            if drug and drug.sequence:
                n = len(prior)
                if n >= len(drug.sequence):
                    out.flags.append(
                        self._flag(
                            f"{ev.drug.upper()}_BEYOND_SEQUENCE",
                            FlagSeverity.WARNING,
                            f"{drug.display} dose {n + 1} ordered; protocol sequence has {len(drug.sequence)}",
                            ev.at_s,
                            ev=ev,
                        )
                    )
                elif ev.dose is not None and not self._same(ev.dose, drug.sequence[n]):
                    out.flags.append(
                        self._flag(
                            f"{ev.drug.upper()}_SEQUENCE_DOSE",
                            FlagSeverity.INFO,
                            f"{drug.display} dose {n + 1} ordered as {fmt_num(ev.dose)} {drug.unit}; "
                            f"protocol dose {n + 1} is {fmt_num(drug.sequence[n])} {drug.unit}",
                            ev.at_s,
                            ev=ev,
                        )
                    )
            if drug and drug.interval_s and prior:
                since = ev.at_s - prior[-1].at_s
                if since < drug.interval_s[0]:
                    out.flags.append(
                        self._flag(
                            f"{ev.drug.upper()}_EARLY",
                            FlagSeverity.INFO,
                            f"{drug.display} ordered {say_duration(since)} after the last dose",
                            ev.at_s,
                            ev=ev,
                        )
                    )
        return out

    # ------------------------------------------------------------------ timers

    def _check_loops(self, now: float) -> EngineOutput:
        out = EngineOutput()
        t = self.f.timers
        for lp in self.loops.values():
            if lp.state == LoopState.ORDERED and now - lp.ordered_at_s >= t.unacknowledged_s:
                at = lp.ordered_at_s + t.unacknowledged_s
                self._transition(lp, LoopState.UNACKNOWLEDGED, at, None, "no acknowledgement heard")
                out.flags.append(
                    self._flag(
                        "LOOP_UNACKNOWLEDGED", FlagSeverity.WARNING, f"{lp.label()} ordered, not acknowledged", at, lp
                    )
                )
                out.loops.append(lp)
                out.state_changed = True
            if lp.state == LoopState.UNACKNOWLEDGED and now - lp.ordered_at_s >= t.unacknowledged_nudge_s:
                at = lp.ordered_at_s + t.unacknowledged_nudge_s
                out.prompts += self._prompt(
                    "LOOP_UNACKNOWLEDGED",
                    PromptCategory.LOOP,
                    f"{self._spoken_order(lp)} ordered. Not acknowledged.",
                    at,
                    key=f"unack-nudge:{lp.id}",
                    priority=2,
                    loop=lp,
                )
        return out

    def _check_cycle(self, now: float) -> EngineOutput:
        out = EngineOutput()
        if not self.cpr_running or self.cycle_started_at_s is None:
            return out
        t = self.f.timers
        el = now - self.cycle_started_at_s
        start_key = f"{self.cycle_started_at_s:.3f}"
        if el >= t.cpr_cycle_warn_s:
            out.prompts += self._prompt(
                "CPR_CYCLE_WARN",
                PromptCategory.TIMER,
                f"{say_duration(t.cpr_cycle_s - t.cpr_cycle_warn_s).capitalize()} to rhythm check.",
                self.cycle_started_at_s + t.cpr_cycle_warn_s,
                key=f"cycle-warn:{start_key}",
                priority=1,
            )
        if el >= t.cpr_cycle_s:
            out.prompts += self._prompt(
                "CPR_CYCLE_DUE",
                PromptCategory.TIMER,
                "Two minutes. Pause compressions for rhythm and pulse check.",
                self.cycle_started_at_s + t.cpr_cycle_s,
                key=f"cycle-due:{start_key}",
                priority=2,
            )
        return out

    def _epi_window(self, now: float) -> dict:
        drug = self.f.drugs.get("epinephrine")
        last = self.last_given("epinephrine")
        if drug is None or drug.interval_s is None or last is None:
            return {"state": "none_given"}
        since = now - last.at_s
        lo, hi = drug.interval_s
        state = "waiting" if since < lo else ("open" if since < hi else "overdue")
        return {"state": state, "seconds_since_last": round(since, 1), "opens_in_s": round(max(0.0, lo - since), 1)}

    def _check_epinephrine(self, now: float) -> EngineOutput:
        out = EngineOutput()
        drug = self.f.drugs.get("epinephrine")
        last = self.last_given("epinephrine")
        if drug is None or drug.interval_s is None or last is None:
            return out
        lo, hi = drug.interval_s
        since = now - last.at_s
        if since >= lo:
            out.prompts += self._prompt(
                "EPI_WINDOW_OPEN",
                PromptCategory.TIMER,
                f"Epinephrine window open. Last dose {say_duration(lo)} ago.",
                last.at_s + lo,
                key=f"epi-open:{last.loop_id}",
                priority=1,
            )
        if since >= hi and f"epi-overdue:{last.loop_id}" not in self._fired:
            fl = self._flag(
                "EPI_OVERDUE", FlagSeverity.WARNING, f"{say_duration(hi)} since last epinephrine", last.at_s + hi
            )
            out.flags.append(fl)
            out.prompts += self._prompt(
                "EPI_OVERDUE",
                PromptCategory.TIMER,
                f"{say_duration(hi).capitalize()} since last epinephrine.",
                last.at_s + hi,
                key=f"epi-overdue:{last.loop_id}",
                priority=2,
            )
            self._fired.add(f"epi-overdue:{last.loop_id}")
        return out
