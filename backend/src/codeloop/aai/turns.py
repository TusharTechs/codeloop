"""Turn AssemblyAI streaming messages into speaker-homogeneous utterances.

Universal-3.5 Pro ends a turn on silence, so in a busy room one "turn" often spans several
people ("Give 1 milligram of epinephrine. Is IV access in yet?"). The turn-level
`speaker_label` is then a majority vote, but every word carries its own `speaker`. We split
each final turn wherever the word-level speaker changes, so an order and its read-back are
attributed to different people. Words still labelled PENDING are attached to a neighbouring
labelled run; a run that is entirely PENDING/UNKNOWN keeps speaker None.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.models import Utterance, Word

UNSURE = {None, "", "PENDING", "UNKNOWN"}


@dataclass
class _Run:
    speaker: str | None
    words: list[dict] = field(default_factory=list)


def split_turn(turn: dict, id_prefix: str = "t") -> list[Utterance]:
    words = turn.get("words") or []
    order = int(turn.get("turn_order", 0))
    lang = turn.get("language_code")
    if not words:
        text = (turn.get("transcript") or "").strip()
        if not text:
            return []
        return [
            Utterance(
                id=f"{id_prefix}{order}",
                turn_order=order,
                text=text,
                start_s=0.0,
                end_s=0.0,
                speaker=_label(turn.get("speaker_label")),
                language=lang,
            )
        ]

    runs: list[_Run] = []
    for w in words:
        spk = _label(w.get("speaker"))
        if runs and (spk is None or spk == runs[-1].speaker):
            runs[-1].words.append(w)
        elif runs and runs[-1].speaker is None:
            runs[-1].speaker = spk  # leading PENDING words join the first labelled run
            runs[-1].words.append(w)
        else:
            runs.append(_Run(spk, [w]))
    if all(r.speaker is None for r in runs):
        turn_spk = _label(turn.get("speaker_label"))
        for r in runs:
            r.speaker = turn_spk

    out = []
    for i, r in enumerate(runs):
        suffix = "" if len(runs) == 1 else chr(ord("a") + i)
        out.append(
            Utterance(
                id=f"{id_prefix}{order}{suffix}",
                turn_order=order,
                text=" ".join(w["text"] for w in r.words).strip(),
                start_s=r.words[0]["start"] / 1000,
                end_s=r.words[-1]["end"] / 1000,
                speaker=r.speaker,
                language=lang,
                words=[
                    Word(
                        text=w["text"],
                        start_ms=int(w["start"]),
                        end_ms=int(w["end"]),
                        confidence=float(w.get("confidence", 0.0)),
                    )
                    for w in r.words
                ],
            )
        )
    return out


def _label(x: object) -> str | None:
    s = str(x) if x is not None else None
    return None if s in UNSURE else s


class TurnAssembler:
    """Feed raw streaming messages; get new utterances as final turns arrive.

    Speaker revisions for turns already emitted are recorded in `revisions` so the UI can
    re-attribute lines; they do not re-run the engine.
    """

    def __init__(self, id_prefix: str = "t") -> None:
        self.id_prefix = id_prefix
        self.emitted: set[int] = set()
        self.revisions: list[dict] = []

    def feed(self, msg: dict) -> list[Utterance]:
        t = msg.get("type")
        if t == "SpeakerRevision":
            self.revisions += msg.get("revisions", [])
            return []
        if t != "Turn" or not msg.get("end_of_turn"):
            return []
        order = int(msg.get("turn_order", 0))
        if order in self.emitted:
            return []
        self.emitted.add(order)
        return split_turn(msg, self.id_prefix)
