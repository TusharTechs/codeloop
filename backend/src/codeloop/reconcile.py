"""Second listen: compare what CodeLoop logged live with an independent post-code transcription.

The live record comes from a real-time stream; the second listen comes from AssemblyAI's async
Universal-3.5 Pro over the whole recording, run through the same deterministic grammar. Each
clinical event is classified:

  confirmed       both heard the same thing (same kind, drug/energy and value, within a few s)
  value_mismatch  both heard the event but with different values (e.g. 150 vs 300 mg)
  live_only       only the live record has it (the live stream may have misheard, or the
                  second listen missed it)
  second_only     only the second listen has it (CodeLoop may have missed it live)

Mismatches and second-only events go to "needs review" before the record is signed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .domain.models import Event, EventKind, Utterance
from .pipeline import TranscriptPipeline

CLINICAL = {EventKind.ORDER, EventKind.ACK, EventKind.DONE, EventKind.CANCEL, EventKind.RHYTHM, EventKind.ROSC}
WINDOW_S = 4.0


@dataclass
class Item:
    status: str
    what: str
    at_s: float
    live_quote: str | None = None
    second_quote: str | None = None
    live_value: float | None = None
    second_value: float | None = None


def _what(e: Event) -> str:
    kind = {"order": "ordered", "ack": "read back", "done": "given", "cancel": "cancelled"}.get(
        e.kind.value, e.kind.value
    )
    if e.action and e.action.value == "shock":
        v = f" {e.energy_j:g} J" if e.energy_j is not None else ""
        return f"shock{v} {kind}"
    if e.drug:
        v = f" {e.dose:g} {e.unit or ''}".rstrip() if e.dose is not None else ""
        return f"{e.drug.replace('_', ' ')}{v} {kind}"
    if e.kind == EventKind.RHYTHM:
        return f"rhythm {e.rhythm.value if e.rhythm else ''}"
    return kind


def _subject(e: Event) -> tuple:
    return (e.kind, e.action, e.drug if e.action is None or e.action.value == "drug" else None, e.rhythm)


def events_from_utterances(utts: list[Utterance]) -> list[Event]:
    pipe = TranscriptPipeline()
    events: list[Event] = []
    for u in utts:
        events.extend(pipe.process(u).events)
    return events


def compare(live: list[Event], second: list[Event], window_s: float = WINDOW_S) -> dict:
    live_c = [e for e in live if e.kind in CLINICAL and e.source.value != "manual"]
    second_c = [e for e in second if e.kind in CLINICAL]
    used: set[int] = set()
    items: list[Item] = []
    for e in live_c:
        best, best_d = None, window_s + 1
        for j, s in enumerate(second_c):
            if j in used or _subject(s) != _subject(e):
                continue
            d = abs(s.at_s - e.at_s)
            if d <= window_s and d < best_d:
                best, best_d = j, d
        if best is None:
            items.append(Item("live_only", _what(e), e.at_s, live_quote=e.quote, live_value=e.value()))
            continue
        used.add(best)
        s = second_c[best]
        same = (e.value() is None or s.value() is None) or abs((e.value() or 0) - (s.value() or 0)) < 1e-6
        items.append(
            Item("confirmed" if same else "value_mismatch", _what(e), e.at_s, e.quote, s.quote, e.value(), s.value())
        )
    for j, s in enumerate(second_c):
        if j not in used:
            items.append(Item("second_only", _what(s), s.at_s, second_quote=s.quote, second_value=s.value()))
    items.sort(key=lambda i: i.at_s)
    counts = {
        k: sum(1 for i in items if i.status == k) for k in ("confirmed", "value_mismatch", "live_only", "second_only")
    }
    return {"counts": counts, "live_events": len(live_c), "items": [asdict(i) for i in items]}
