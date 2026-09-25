"""Core domain types. All times are code-time seconds (audio clock) unless named otherwise."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    LEADER = "leader"
    MEDS = "meds"
    COMPRESSOR = "compressor"
    AIRWAY = "airway"
    RECORDER = "recorder"
    OTHER = "other"


class EventKind(StrEnum):
    ORDER = "order"
    ACK = "ack"
    DONE = "done"
    CANCEL = "cancel"
    RHYTHM = "rhythm"
    RHYTHM_CHECK = "rhythm_check"
    CPR_START = "cpr_start"
    CPR_PAUSE = "cpr_pause"
    CPR_RESUME = "cpr_resume"
    ROSC = "rosc"
    TERMINATE = "terminate"
    ROLE = "role"
    QUESTION = "question"


class Action(StrEnum):
    DRUG = "drug"
    SHOCK = "shock"


class Rhythm(StrEnum):
    VF = "VF"
    PVT = "PVT"
    PEA = "PEA"
    ASYSTOLE = "ASYSTOLE"
    SINUS = "SINUS"


class EventSource(StrEnum):
    GRAMMAR = "grammar"
    LLM = "llm"
    BOTH = "both"
    MANUAL = "manual"


class LoopState(StrEnum):
    ORDERED = "ORDERED"
    UNACKNOWLEDGED = "UNACKNOWLEDGED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CONFLICT = "CONFLICT"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

    @property
    def is_open(self) -> bool:
        return self not in (LoopState.DONE, LoopState.CANCELLED)


class Word(BaseModel):
    text: str
    start_ms: int
    end_ms: int
    confidence: float


class Utterance(BaseModel):
    """One final transcript turn from the room."""

    id: str
    turn_order: int
    text: str
    start_s: float
    end_s: float
    speaker: str | None = None  # diarization label (A, B, ...), None/UNKNOWN when unsure
    language: str | None = None
    words: list[Word] = Field(default_factory=list)


class Event(BaseModel):
    """A clinically meaningful statement extracted from one utterance.

    `quote` must be a verbatim substring of the utterance text; the validator enforces this.
    `value_confidence` is the lowest ASR confidence among the words carrying the drug, dose or
    energy, and drives UNCONFIRMED marking.
    """

    id: str
    kind: EventKind
    at_s: float
    utterance_id: str | None = None
    speaker: str | None = None
    action: Action | None = None
    drug: str | None = None
    dose: float | None = None
    unit: str | None = None
    energy_j: float | None = None
    rhythm: Rhythm | None = None
    role: Role | None = None
    name: str | None = None
    quote: str = ""
    source: EventSource = EventSource.GRAMMAR
    value_confidence: float | None = None
    unconfirmed: bool = False

    def value(self) -> float | None:
        return self.energy_j if self.action == Action.SHOCK else self.dose

    def describe(self) -> str:
        if self.action == Action.SHOCK:
            return f"shock {fmt_num(self.energy_j)} J" if self.energy_j else "shock"
        if self.action == Action.DRUG:
            parts = [self.drug or "drug"]
            if self.dose is not None:
                parts.append(f"{fmt_num(self.dose)} {self.unit or ''}".strip())
            return " ".join(parts)
        return self.kind.value


class LoopTransition(BaseModel):
    at_s: float
    state: LoopState
    event_id: str | None = None
    note: str = ""


class Loop(BaseModel):
    """Closed-loop tracking for one order: ordered → acknowledged → done."""

    id: str
    action: Action
    drug: str | None = None
    ordered_value: float | None = None
    heard_value: float | None = None  # value in the conflicting read-back
    unit: str | None = None
    state: LoopState
    opened_at_s: float
    ordered_at_s: float  # last time the order was (re)stated; drives the unacknowledged timer
    closed_at_s: float | None = None
    order_event_id: str | None = None
    ordered_by: str | None = None
    acknowledged_by: str | None = None
    without_order: bool = False  # acknowledged/given with no order heard
    needs_confirmation: bool = False  # built on low-confidence ASR
    history: list[LoopTransition] = Field(default_factory=list)

    def label(self) -> str:
        if self.action == Action.SHOCK:
            return f"shock {fmt_num(self.ordered_value)} J" if self.ordered_value else "shock"
        v = f" {fmt_num(self.ordered_value)} {self.unit or ''}".rstrip() if self.ordered_value is not None else ""
        return f"{self.drug}{v}"


class FlagSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Flag(BaseModel):
    id: str
    rule: str
    severity: FlagSeverity
    message: str
    at_s: float
    loop_id: str | None = None
    event_id: str | None = None
    resolved_at_s: float | None = None


class PromptCategory(StrEnum):
    TIMER = "timer"  # protocol clock: CPR cycle, epinephrine window
    LOOP = "loop"  # closed-loop communication: unacknowledged order, read-back conflict
    SAFETY = "safety"  # consistency checks such as a shock ordered on a non-shockable rhythm


class PromptPolicy(StrEnum):
    SILENT = "silent"  # screen only
    TIMERS = "timers"  # speak protocol timers only
    TIMERS_AND_LOOPS = "timers_and_loops"  # default: timers, loop nudges and safety checks

    def allows(self, category: PromptCategory) -> bool:
        if self == PromptPolicy.SILENT:
            return False
        if self == PromptPolicy.TIMERS:
            return category == PromptCategory.TIMER
        return True


class Prompt(BaseModel):
    """Something CodeLoop wants to say out loud. Text comes only from fixed templates."""

    id: str
    rule: str
    category: PromptCategory
    text: str
    at_s: float
    priority: int = 1  # higher speaks first; stale low-priority prompts may be dropped
    loop_id: str | None = None


def fmt_num(x: float | None) -> str:
    if x is None:
        return ""
    return str(int(x)) if float(x).is_integer() else f"{x:g}"
