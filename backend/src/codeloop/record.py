"""The Code Record, rebuilt from the hash-chained audit log alone.

Because the record is derived from the audit log (never from mutable in-memory state), a
live code and a closed code produce the same record, and the record carries its own
integrity check: the chain is verified and its head hash is printed on the record.
"""

from __future__ import annotations

from typing import Any

from .store import Store

EVENT_LABELS = {
    "order": "ordered",
    "ack": "read back",
    "done": "given",
    "cancel": "cancelled",
    "rhythm": "rhythm",
    "rhythm_check": "rhythm check",
    "cpr_start": "CPR started",
    "cpr_pause": "CPR paused",
    "cpr_resume": "CPR resumed",
    "rosc": "ROSC called",
    "terminate": "termination called",
    "role": "role",
    "question": "asked CodeLoop",
}


def clock(seconds: float | None, start: float | None) -> str:
    if seconds is None:
        return "--:--"
    s = max(0, round(seconds - (start or 0.0)))
    return f"{s // 60:02d}:{s % 60:02d}"


def build_record(store: Store, code_id: str) -> dict[str, Any]:
    meta = store.get_code(code_id)
    if meta is None:
        raise KeyError(code_id)
    entries = store.entries(code_id)
    ok, bad_seq = store.verify(code_id)
    utterances = {e.payload["id"]: e.payload for e in entries if e.kind == "utterance"}
    events = [e.payload for e in entries if e.kind == "event"]
    start = next((ev["at_s"] for ev in events if ev["kind"] not in ("role", "question")), None)

    loops: dict[str, dict] = {}
    for e in entries:
        if e.kind == "loop":
            loops[e.payload["id"]] = e.payload
    flags: dict[str, dict] = {}
    for e in entries:
        if e.kind in ("flag", "flag_resolved"):
            flags[e.payload["id"]] = e.payload

    timeline = []
    for ev in events:
        if ev["kind"] == "role":
            continue
        u = utterances.get(ev.get("utterance_id") or "", {})
        timeline.append(
            {
                "clock": clock(ev["at_s"], start),
                "at_s": ev["at_s"],
                "what": describe(ev),
                "kind": ev["kind"],
                "quote": ev.get("quote", ""),
                "speaker": u.get("speaker") or ev.get("speaker"),
                "role": u.get("role"),
                "source": ev.get("source"),
                "confidence": ev.get("value_confidence"),
                "unconfirmed": ev.get("unconfirmed", False),
            }
        )

    spoken = [e.payload | {"at_s": e.at_code_s} for e in entries if e.kind == "spoken"]
    controls = [e.payload | {"at_s": e.at_code_s} for e in entries if e.kind == "control"]
    answers = [e.payload for e in entries if e.kind == "answer"]
    needs_review = [
        {
            "loop": lp["id"],
            "what": loop_label(lp),
            "state": lp["state"],
            "reason": "value not agreed"
            if lp["state"] == "CONFLICT"
            else ("low ASR confidence" if lp.get("needs_confirmation") else "never completed"),
        }
        for lp in loops.values()
        if lp["state"] in ("CONFLICT", "ORDERED", "UNACKNOWLEDGED", "ACKNOWLEDGED") or lp.get("needs_confirmation")
    ]
    closed = [e.payload for e in entries if e.kind == "code_closed"]
    if closed and closed[-1].get("clock_s") is not None:
        duration_s: float | None = float(closed[-1]["clock_s"])
    elif events and start is not None:
        duration_s = max(ev["at_s"] for ev in events) - start
    else:
        duration_s = None
    administered = [
        {
            "clock": clock(lp.get("closed_at_s"), start),
            "what": loop_label(lp),
            "without_order": lp.get("without_order", False),
            "closed_loop": any(h["state"] == "ACKNOWLEDGED" for h in lp.get("history", [])),
        }
        for lp in loops.values()
        if lp["state"] == "DONE"
    ]
    return {
        "code": meta,
        "integrity": {
            "chain_valid": ok,
            "first_bad_entry": bad_seq,
            "entries": len(entries),
            "head_hash": store.head_hash(code_id),
        },
        "summary": closed[-1] if closed else None,
        "duration": clock(duration_s, 0) if duration_s is not None else None,
        "duration_s": duration_s,
        "administered": sorted(administered, key=lambda x: x["clock"]),
        "quality": (closed[-1].get("quality") if closed else None) or [],
        "timeline": timeline,
        "loops": list(loops.values()),
        "flags": list(flags.values()),
        "spoken": spoken,
        "answers": answers,
        "controls": controls,
        "needs_review": needs_review,
    }


def loop_label(lp: dict) -> str:
    v = lp.get("ordered_value")
    num = "" if v is None else (str(int(v)) if float(v).is_integer() else str(v))
    if lp["action"] == "shock":
        return f"shock {num} J".replace("  ", " ").strip()
    return f"{(lp.get('drug') or 'drug').replace('_', ' ')} {num} {lp.get('unit') or ''}".strip()


def describe(ev: dict) -> str:
    kind = ev["kind"]
    label = EVENT_LABELS.get(kind, kind)
    if ev.get("action") == "shock":
        j = ev.get("energy_j")
        return f"Shock {int(j) if j else ''} J {label}".replace("  ", " ")
    if ev.get("action") == "drug":
        dose = ev.get("dose")
        num = "" if dose is None else (str(int(dose)) if float(dose).is_integer() else str(dose))
        return f"{(ev.get('drug') or '').replace('_', ' ').capitalize()} {num} {ev.get('unit') or ''} {label}".replace(
            "  ", " "
        ).strip()
    if kind == "rhythm":
        return f"Rhythm: {ev.get('rhythm')}"
    return label[0].upper() + label[1:]
