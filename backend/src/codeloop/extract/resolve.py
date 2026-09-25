"""Turn grammar/LLM candidates into validated engine events, using live engine state.

Resolution rules (all deterministic):
  MENTION "Amiodarone three hundred."  → ORDER if the speaker is the orderer or the team
                                          leader, or nothing is open; otherwise a read-back ACK.
  VALUE   "Three hundred."              → attaches to the loop under discussion (conflict first,
                                          then the most recent open loop within 20 s).
  CPR start/resume/pause                → normalised against whether CPR is running.
  CANCEL with nothing open              → dropped.
  ROLE "Priya on meds." (not addressed) → self-introduction: also maps the speaker's label.

Validation gates applied to every event before it reaches the engine:
  - the quote must be a verbatim substring of the utterance
  - drug must be in the formulary; dose/energy must be inside formulary bounds, else the event
    is kept but marked UNCONFIRMED
  - value words below the ASR confidence threshold mark the event UNCONFIRMED
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.formulary import Formulary
from ..domain.models import Action, Event, EventKind, EventSource, Loop, LoopState, Role, Utterance
from ..engine.engine import CodeEngine
from .grammar import Candidate, Cue

VALUE_WINDOW_S = 20.0
ADDRESSED_CUES = ("you're", "you are", "youre", "aap", "tum", "you")


@dataclass
class Dropped:
    candidate: Candidate
    reason: str


class Resolver:
    def __init__(self, formulary: Formulary, low_confidence: float = 0.6) -> None:
        self.f = formulary
        self.low_confidence = low_confidence
        self.dropped: list[Dropped] = []

    def resolve(
        self, c: Candidate, utt: Utterance, engine: CodeEngine, event_id: str, source: EventSource = EventSource.GRAMMAR
    ) -> list[Event]:
        if c.quote and c.quote not in utt.text:
            self._drop(c, "quote is not verbatim in the transcript")
            return []
        speaker = utt.speaker if utt.speaker not in (None, "UNKNOWN", "PENDING") else None
        base = dict(
            at_s=c.at_s,
            utterance_id=utt.id,
            speaker=speaker,
            quote=c.quote,
            source=source,
            value_confidence=c.value_confidence,
        )
        kind = c.kind

        if kind == Cue.VALUE:
            return self._value(c, engine, speaker, base, event_id)
        if kind == Cue.MENTION:
            if c.action == Action.DRUG and c.dose is None:
                self._drop(c, "drug named with no dose and no verb")
                return []
            kind = self._mention_kind(c, engine, speaker)
        elif isinstance(kind, Cue):
            kind = EventKind(kind.value)

        if kind in (EventKind.CPR_START, EventKind.CPR_RESUME, EventKind.CPR_PAUSE):
            kind = self._cpr_kind(kind, engine)
            if kind is None:
                self._drop(c, "CPR state already matches")
                return []
        if kind == EventKind.CANCEL:
            target = self._open_loop(engine, c.action, c.drug)
            if target is None:
                self._drop(c, "nothing open to cancel")
                return []
            # "Cancel that" inherits what it cancels, so the record says what was cancelled.
            c.action, c.drug = target.action, target.drug
            if target.action == Action.SHOCK:
                c.energy_j = target.ordered_value
            else:
                c.dose, c.unit = target.ordered_value, target.unit
        if kind == EventKind.ROLE:
            return self._roles(c, engine, speaker, base, event_id)

        ev = Event(
            id=event_id,
            kind=kind,
            action=c.action,
            drug=c.drug,
            dose=c.dose,
            unit=c.unit,
            energy_j=c.energy_j,
            rhythm=c.rhythm,
            **base,
        )
        if kind == EventKind.ACK and ev.action is None:
            # "Pushing now." — record what it acknowledges.
            lp = engine.generic_ack_target(ev)
            if lp is not None:
                ev.action, ev.drug = lp.action, lp.drug
                if lp.action == Action.SHOCK:
                    ev.energy_j = lp.ordered_value
                else:
                    ev.dose, ev.unit = lp.ordered_value, lp.unit
        if kind in (EventKind.ACK, EventKind.DONE) and ev.action and ev.value() is None:
            lp = self._open_loop(engine, ev.action, ev.drug)
            if lp is not None and lp.ordered_value is not None:
                if ev.action == Action.SHOCK:
                    ev.energy_j = lp.ordered_value
                else:
                    ev.dose, ev.unit = lp.ordered_value, lp.unit
        return [self._validate(ev)]

    # ------------------------------------------------------------------ rules

    def _mention_kind(self, c: Candidate, engine: CodeEngine, speaker: str | None) -> EventKind:
        lp = self._open_loop(engine, c.action, c.drug)
        role = engine.role_of(speaker)
        if lp is None:
            # With nothing open, a stated drug + dose is an order. Diarization mistakes make
            # the speaker's role an unreliable reason to call it a read-back.
            return EventKind.ORDER
        if speaker is not None and speaker == lp.ordered_by:
            return EventKind.ORDER
        if role == Role.LEADER:
            return EventKind.ORDER
        return EventKind.ACK

    def _value(self, c: Candidate, engine: CodeEngine, speaker: str | None, base: dict, event_id: str) -> list[Event]:
        lp = self._loop_under_discussion(engine, c.at_s)
        if lp is None:
            self._drop(c, "number with no order under discussion")
            return []
        is_orderer = speaker is not None and speaker == lp.ordered_by
        kind = EventKind.ORDER if is_orderer or engine.role_of(speaker) == Role.LEADER else EventKind.ACK
        ev = Event(id=event_id, kind=kind, action=lp.action, drug=lp.drug, **base)
        if lp.action == Action.SHOCK:
            ev.energy_j = c.dose
        else:
            ev.dose, ev.unit = c.dose, c.unit or lp.unit
        return [self._validate(ev)]

    def _roles(self, c: Candidate, engine: CodeEngine, speaker: str | None, base: dict, event_id: str) -> list[Event]:
        events = [Event(id=event_id, kind=EventKind.ROLE, role=c.role, name=c.name, **base)]
        if c.name and speaker and engine.role_of(speaker) != Role.LEADER:
            words = {w.strip(",.").lower() for w in c.quote.split()}
            if not words.intersection(ADDRESSED_CUES):
                # "Priya on meds." said by Priya: she is introducing herself
                events.append(Event(id=f"{event_id}s", kind=EventKind.ROLE, role=c.role, **base))
        return events

    @staticmethod
    def _cpr_kind(kind: EventKind, engine: CodeEngine) -> EventKind | None:
        if kind in (EventKind.CPR_START, EventKind.CPR_RESUME):
            if engine.cpr_running:
                return None
            return EventKind.CPR_START if engine.started_at_s is None else EventKind.CPR_RESUME
        return EventKind.CPR_PAUSE if engine.cpr_running else None

    @staticmethod
    def _open_loop(engine: CodeEngine, action: Action | None, drug: str | None) -> Loop | None:
        for lp in reversed(list(engine.loops.values())):
            if not lp.state.is_open or (action and lp.action != action):
                continue
            if action == Action.DRUG and drug and lp.drug != drug:
                continue
            return lp
        return None

    def _has_open(self, engine: CodeEngine, action: Action | None, drug: str | None) -> bool:
        return self._open_loop(engine, action, drug) is not None

    @staticmethod
    def _loop_under_discussion(engine: CodeEngine, at_s: float) -> Loop | None:
        open_loops = [lp for lp in engine.loops.values() if lp.state.is_open]
        conflicts = [lp for lp in open_loops if lp.state == LoopState.CONFLICT]
        if conflicts:
            return conflicts[-1]
        recent = [lp for lp in open_loops if at_s - lp.history[-1].at_s <= VALUE_WINDOW_S]
        return recent[-1] if recent else None

    # ------------------------------------------------------------------ validation

    def _validate(self, ev: Event) -> Event:
        reasons = []
        if ev.action == Action.DRUG and ev.drug:
            drug = self.f.drugs.get(ev.drug) or self.f.drug_for(ev.drug)
            if drug is None:
                reasons.append("drug not in formulary")
            else:
                ev.drug = drug.key
                if ev.dose is not None and not drug.in_bounds(ev.dose):
                    reasons.append("dose outside formulary bounds")
                if ev.unit is None:
                    ev.unit = drug.unit
        if ev.action == Action.SHOCK and ev.energy_j is not None and not self.f.shock_in_bounds(ev.energy_j):
            reasons.append("energy outside bounds")
        if ev.value_confidence is not None and ev.value_confidence < self.low_confidence:
            reasons.append(f"low ASR confidence {ev.value_confidence:.2f}")
        if reasons:
            ev.unconfirmed = True
        return ev

    def _drop(self, c: Candidate, reason: str) -> None:
        self.dropped.append(Dropped(c, reason))
