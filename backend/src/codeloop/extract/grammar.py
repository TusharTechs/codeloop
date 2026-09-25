"""Deterministic fast-path extraction of resuscitation events from one transcript turn.

The grammar recognises the constrained phrasing ACLS teams are trained to use, in English,
romanized Hindi and Devanagari. It needs no network, runs in microseconds, and gives the
LLM extractor an independent second opinion. Every event carries:
  - `quote`: the verbatim clause it came from (a substring of the utterance text)
  - `value_confidence`: the lowest ASR confidence among the words carrying drug/dose/energy

Statements without a clear verb ("Amiodarone three hundred.") come out as MENTION, and a
bare number ("Three hundred.") as VALUE; the stateful resolver decides whether those are
orders, read-backs or restatements, because that depends on who is speaking and what is open.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from functools import partial

from ..domain.formulary import Formulary
from ..domain.models import Action, EventKind, Rhythm, Role, Utterance
from .numbers import NumberSpan, parse_numbers


class Cue(StrEnum):
    """Grammar-level kinds; MENTION and VALUE are resolved against engine state later."""

    ORDER = "order"
    ACK = "ack"
    DONE = "done"
    CANCEL = "cancel"
    MENTION = "mention"
    VALUE = "value"


@dataclass
class Candidate:
    kind: EventKind | Cue
    quote: str
    at_s: float
    action: Action | None = None
    drug: str | None = None
    dose: float | None = None
    unit: str | None = None
    energy_j: float | None = None
    rhythm: Rhythm | None = None
    role: Role | None = None
    name: str | None = None
    value_confidence: float | None = None
    char_span: tuple[int, int] = (0, 0)
    extras: dict = field(default_factory=dict)


@dataclass
class Tok:
    text: str
    norm: str
    start: int
    end: int


_TOKEN_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?|[A-Za-zऀ-ॿ]+(?:'[A-Za-z]+)?")
_CLAUSE_SPLIT = re.compile(r"[.?!;।]+")

# Cue phrases, matched on whole tokens. Order within each list does not matter.
DONE_CUES = [
    "is in",
    "are in",
    "in ho gaya",
    "ho gaya",
    "is given",
    "given",
    "pushed",
    "delivered",
    "de diya",
    "diya gaya",
    "chala gaya",
    "done",
    "हो गया",
    "दे दिया",
    "गया",
    "in",
]
ACK_CUES = [
    "drawing up",
    "pushing",
    "going in",
    "charging",
    "de rahi",
    "de raha",
    "got it",
    "copy",
    "giving",
    "roger",
    "दे रही",
    "दे रहा",
    "on it",
    "coming up",
]
ORDER_CUES = [
    "give",
    "push",
    "charge to",
    "charge at",
    "charge",
    "shock at",
    "let's give",
    "lets give",
    "de do",
    "dijiye",
    "do",
    "दे दो",
    "दीजिए",
    "administer",
    "draw up",
    "i want",
    "can i get",
    "can we get",
    "we need",
    "hang",
    "defibrillate",
]
CANCEL_CUES = [
    "cancel",
    "hold the",
    "hold off",
    "don't give",
    "do not give",
    "dump the charge",
    "dump",
    "dumped",
    "disarm",
    "mat dena",
    "mat do",
    "मत",
    "nahi dena",
    "scratch that",
    "belay",
]
CPR_START_CUES = [
    "starting cpr",
    "start cpr",
    "cpr start",
    "begin compressions",
    "start compressions",
    "starting compressions",
    "compressions start",
    "cpr shuru",
    "सीपीआर शुरू",
]
CPR_RESUME_CUES = [
    "resume compressions",
    "resume cpr",
    "back on the chest",
    "continue compressions",
    "compressions continue",
    "continue cpr",
    "back on compressions",
    "resume",
    "continue karo",
]
CPR_PAUSE_CUES = [
    "pause compressions",
    "hold compressions",
    "stop compressions",
    "pause cpr",
    "hold cpr",
    "off the chest",
    "pause",
    "hands off",
]
RHYTHM_CHECK_CUES = ["rhythm check", "pulse check", "check rhythm", "check for a pulse", "check pulse", "rhythm dekho"]
ROSC_CUES = [
    "rosc",
    "we have a pulse",
    "got a pulse",
    "i've got a pulse",
    "pulse is back",
    "have a pulse",
    "return of spontaneous circulation",
    "pulse aa gayi",
    "pulse aa gaya",
]
TERMINATE_CUES = ["call it", "calling it", "time of death", "stop the code", "terminate resuscitation"]
SHOCK_WORDS = {
    "charge",
    "charging",
    "charged",
    "shock",
    "shocking",
    "shocked",
    "defib",
    "defibrillate",
    "joules",
    "joule",
    "dump",
    "dumped",
}
UNIT_WORDS = {
    "mg": "mg",
    "milligram": "mg",
    "milligrams": "mg",
    "मिलीग्राम": "mg",
    "migs": "mg",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "mcg": "mcg",
    "micrograms": "mcg",
    "meq": "mEq",
    "joules": "J",
    "joule": "J",
    "j": "J",
}
ROLE_WORDS = {
    "meds": Role.MEDS,
    "medications": Role.MEDS,
    "drugs": Role.MEDS,
    "medication": Role.MEDS,
    "compressions": Role.COMPRESSOR,
    "compressor": Role.COMPRESSOR,
    "airway": Role.AIRWAY,
    "bagging": Role.AIRWAY,
    "recorder": Role.RECORDER,
    "recording": Role.RECORDER,
    "scribe": Role.RECORDER,
}
ROLE_LINK_WORDS = {
    "on",
    "you're",
    "youre",
    "you",
    "are",
    "is",
    "i'm",
    "im",
    "i",
    "am",
    "take",
    "taking",
    "i'll",
    "aap",
    "tum",
    "your",
    "will",
    "do",
}
ROLE_TAIL_WORDS = {"aap", "dekho", "please", "now", "karo", "sambhalo", "handle", "lo"}
SELF_LEAD_CUES = [
    "i'm leading",
    "i am leading",
    "i'll lead",
    "i will lead",
    "i'm running",
    "i'm team lead",
    "main lead",
    "lead kar raha",
    "lead kar rahi",
    "मैं लीड",
]
NOT_NAMES = {
    "code",
    "no",
    "yes",
    "okay",
    "ok",
    "sorry",
    "wait",
    "still",
    "that's",
    "give",
    "charge",
    "pause",
    "resume",
    "epi",
    "amio",
    "starting",
    "start",
    "continue",
    "back",
    "hold",
    "line",
    "need",
    "is",
    "and",
    "so",
    "right",
    "codeloop",
}
WAKE_WORDS = [
    "codeloop",
    "code loop",
    "kodloop",
    "code lope",
    "codelope",
    "cardioloop",
    "kodlu",
    "कोडलूप",
    "कोड लूप",
    "कादलू",
    "कोडलू",
    "कोडलुप",
]
QUESTION_WORDS = {
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "can",
    "could",
    "should",
    "will",
    "would",
    "what",
    "when",
    "where",
    "who",
    "why",
    "how",
    "which",
    "have",
    "has",
    "any",
    "anyone",
    "kya",
    "kab",
    "kaun",
    "kahan",
    "kitna",
    "kyun",
    "क्या",
    "कब",
    "कौन",
    "कहाँ",
    "कितना",
}
GENERIC_ACK_CUES = [
    "got it",
    "copy",
    "roger",
    "on it",
    "pushing",
    "pushing now",
    "drawing up",
    "drawing it up",
    "charging",
    "going in",
    "giving now",
    "doing it",
    "de rahi hoon",
    "de raha hoon",
]


def tokenize(text: str) -> list[Tok]:
    return [Tok(m.group(0), m.group(0).lower().replace("’", "'"), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def _find(norms: list[str], phrase: str) -> list[tuple[int, int]]:
    p = phrase.lower().split()
    n = len(p)
    return [(i, i + n) for i in range(len(norms) - n + 1) if norms[i : i + n] == p]


def _has(norms: list[str], phrases: list[str]) -> tuple[int, int] | None:
    best = None
    for ph in phrases:
        for span in _find(norms, ph):
            if best is None or (span[1] - span[0]) > (best[1] - best[0]):
                best = span
    return best


class Grammar:
    def __init__(self, formulary: Formulary) -> None:
        self.f = formulary
        aliases: list[tuple[list[str], str]] = []
        for key, drug in formulary.drugs.items():
            for a in {key.replace("_", " "), *drug.aliases}:
                aliases.append((a.lower().replace("-", " ").split(), key))
        self._drug_aliases = sorted(aliases, key=lambda x: -len(x[0]))
        self._rhythm_aliases = sorted(
            ((a.split(), r) for a, r in formulary.rhythm_aliases.items()), key=lambda x: -len(x[0])
        )

    # -------------------------------------------------------------- public

    def extract(self, utt: Utterance) -> list[Candidate]:
        text = utt.text
        tokens = tokenize(text)
        conf = self._token_confidences(utt, tokens)
        times = self._token_times(utt, tokens)
        out: list[Candidate] = []
        whole = [t.norm for t in tokens]
        is_question_to_agent = _has(whole, WAKE_WORDS) is not None
        if is_question_to_agent:
            return [Candidate(kind=EventKind.QUESTION, quote=text.strip(), at_s=utt.end_s, char_span=(0, len(text)))]

        for c_start, c_end in self._clauses(text):
            ctoks = [t for t in tokens if t.start >= c_start and t.end <= c_end]
            if not ctoks:
                continue
            idx0 = tokens.index(ctoks[0])
            clause_text = text[ctoks[0].start : ctoks[-1].end]
            end_char = ctoks[-1].end
            norms = [t.norm for t in ctoks]
            if text[end_char : c_end + 1].strip().startswith("?") and norms[0] in QUESTION_WORDS:
                # "Is IV access in yet?" is a question; "Amio 150, pushing?" is a read-back
                # with rising intonation and must still be scored.
                continue
            at_s = times[idx0 + len(ctoks) - 1] if times else utt.end_s
            cand = partial(Candidate, quote=clause_text, at_s=at_s, char_span=(ctoks[0].start, ctoks[-1].end))
            out += self._structural(norms, ctoks, cand)
            out += self._clinical(norms, ctoks, idx0, conf, cand)
        return self._dedupe(out)

    # -------------------------------------------------------------- pieces

    @staticmethod
    def _clauses(text: str) -> list[tuple[int, int]]:
        spans = []
        start = 0
        for m in _CLAUSE_SPLIT.finditer(text):
            spans.append((start, m.start()))
            start = m.end()
        spans.append((start, len(text)))
        return [(s, e) for s, e in spans if text[s:e].strip()]

    def _structural(self, norms: list[str], ctoks: list[Tok], cand) -> list[Candidate]:
        out: list[Candidate] = []
        if _has(norms, ROSC_CUES):
            out.append(cand(EventKind.ROSC))
        if _has(norms, TERMINATE_CUES):
            out.append(cand(EventKind.TERMINATE))
        if _has(norms, CPR_START_CUES):
            out.append(cand(EventKind.CPR_START))
        elif _has(norms, CPR_RESUME_CUES):
            out.append(cand(EventKind.CPR_RESUME))
        elif _has(norms, CPR_PAUSE_CUES) and not _has(norms, ["don't pause", "no pause"]):
            out.append(cand(EventKind.CPR_PAUSE))
        if _has(norms, RHYTHM_CHECK_CUES):
            out.append(cand(EventKind.RHYTHM_CHECK))
        rhythm = self._rhythm(norms)
        if rhythm is not None:
            out.append(cand(EventKind.RHYTHM, rhythm=rhythm))
        out += self._roles(norms, ctoks, cand)
        return out

    def _rhythm(self, norms: list[str]) -> Rhythm | None:
        for alias, rhythm in self._rhythm_aliases:
            for _i, j in _find(norms, " ".join(alias)):
                # "rhythm check", "is it VF" etc. are not statements of rhythm
                if j < len(norms) and norms[j] in ("check", "checks"):
                    continue
                if rhythm == Rhythm.SINUS and "pulse" not in norms and "rosc" not in norms:
                    continue
                return rhythm
        return None

    def _roles(self, norms: list[str], ctoks: list[Tok], cand) -> list[Candidate]:
        out: list[Candidate] = []
        if _has(norms, SELF_LEAD_CUES):
            out.append(cand(EventKind.ROLE, role=Role.LEADER))
            return out
        # "On compressions." (self) / "Priya on meds." / "Priya, you're on meds." / "Karan, compressions."
        role_idx = next((i for i, n in enumerate(norms) if n in ROLE_WORDS), None)
        if role_idx is None or len(norms) > 7:
            return out
        role = ROLE_WORDS[norms[role_idx]]
        between = set(norms[1:role_idx])
        tail_ok = set(norms[role_idx + 1 :]) <= ROLE_TAIL_WORDS
        first = ctoks[0]
        has_name = (
            role_idx > 0
            and first.text[:1].isupper()
            and first.norm not in NOT_NAMES
            and first.norm not in ROLE_WORDS
            and first.norm not in ROLE_LINK_WORDS
        )
        if has_name and between <= ROLE_LINK_WORDS and tail_ok:
            out.append(cand(EventKind.ROLE, role=role, name=first.text))
        elif set(norms[:role_idx]) <= ROLE_LINK_WORDS and role_idx > 0 and tail_ok:
            out.append(cand(EventKind.ROLE, role=role))
        return out

    def _clinical(
        self, norms: list[str], ctoks: list[Tok], idx0: int, conf: list[float | None], cand
    ) -> list[Candidate]:
        numbers = parse_numbers(norms)
        drug_hits = self._drugs(norms)
        is_shock = any(n in SHOCK_WORDS for n in norms) or any(
            norms[i] in ("joules", "joule", "j") for i in range(len(norms))
        )
        cue = self._cue(norms)
        out: list[Candidate] = []

        def min_conf(spans: list[tuple[int, int]]) -> float | None:
            vals = [conf[idx0 + k] for s, e in spans for k in range(s, e) if conf and conf[idx0 + k] is not None]
            return min(vals) if vals else None

        if drug_hits:
            for (ds, de), drug_key in drug_hits:
                num = self._nearest_number(numbers, ds, de, exclude_units_of=("J",), norms=norms)
                unit = self._unit_after(norms, num) or self.f.drugs[drug_key].unit
                spans = [(ds, de)] + ([(num.start, num.end)] if num else [])
                kind = cue or Cue.MENTION
                out.append(
                    cand(
                        kind,
                        action=Action.DRUG,
                        drug=drug_key,
                        dose=num.value if num else None,
                        unit=unit,
                        value_confidence=min_conf(spans),
                    )
                )
            return out
        if is_shock:
            anchor = next((i for i, n in enumerate(norms) if n in SHOCK_WORDS), 0)
            num = self._nearest_number(numbers, anchor, anchor + 1, norms=norms, either_side=True)
            spans = [(num.start, num.end)] if num else []
            kind = cue or Cue.MENTION
            if kind == Cue.MENTION and num is None:
                return out
            out.append(
                cand(kind, action=Action.SHOCK, energy_j=num.value if num else None, value_confidence=min_conf(spans))
            )
            return out
        if cue == Cue.CANCEL:
            out.append(cand(Cue.CANCEL))
            return out
        # A clause that is only a number ("Three hundred." / "Three zero zero.") is a value
        # restatement; the resolver attaches it to the loop being discussed.
        if numbers and all(
            n in {"no", "yes", "haan", "nahi", "make", "it", "that's", "thats"}
            or any(num.start <= i < num.end for num in numbers)
            or n in UNIT_WORDS
            for i, n in enumerate(norms)
        ):
            num = numbers[-1]
            out.append(
                cand(
                    Cue.VALUE,
                    dose=num.value,
                    unit=self._unit_after(norms, num),
                    value_confidence=min_conf([(num.start, num.end)]),
                )
            )
        elif cue == Cue.ACK and _has(norms, GENERIC_ACK_CUES) and len(norms) <= 5:
            out.append(cand(Cue.ACK))  # "Pushing now." acknowledges the latest open order
        return out

    def _cue(self, norms: list[str]) -> Cue | None:
        for cue, phrases in (
            (Cue.CANCEL, CANCEL_CUES),
            (Cue.DONE, DONE_CUES),
            (Cue.ACK, ACK_CUES),
            (Cue.ORDER, ORDER_CUES),
        ):
            span = _has(norms, phrases)
            if not span:
                continue
            if cue == Cue.DONE and norms[span[0] : span[1]] == ["in"]:
                # a bare "in" only means "administered" at the end of a clause ("... amio in")
                if span[1] != len(norms):
                    continue
            if cue == Cue.ORDER and norms[span[0] : span[1]] == ["do"]:
                if span[0] == 0 or norms[span[0] - 1] != "de":
                    continue
            return cue
        return None

    def _drugs(self, norms: list[str]) -> list[tuple[tuple[int, int], str]]:
        hits: list[tuple[tuple[int, int], str]] = []
        taken: set[int] = set()
        for alias, key in self._drug_aliases:
            for s, e in _find(norms, " ".join(alias)):
                if taken.intersection(range(s, e)):
                    continue
                if key == "calcium_chloride" and alias == ["calcium"] and "gluconate" in norms:
                    continue
                hits.append(((s, e), key))
                taken.update(range(s, e))
        hits.sort()
        # the same drug named twice in one clause is one event
        seen: set[str] = set()
        uniq = []
        for span, key in hits:
            if key not in seen:
                seen.add(key)
                uniq.append((span, key))
        return uniq

    @staticmethod
    def _unit_after(norms: list[str], num: NumberSpan | None) -> str | None:
        if num is None:
            return None
        for k in (num.end, num.end + 1):
            if k < len(norms) and norms[k] in UNIT_WORDS:
                return UNIT_WORDS[norms[k]]
        return None

    def _nearest_number(
        self,
        numbers: list[NumberSpan],
        ds: int,
        de: int,
        norms: list[str],
        exclude_units_of: tuple[str, ...] = (),
        either_side: bool = False,
    ) -> NumberSpan | None:
        best, best_d = None, 99
        for num in numbers:
            unit = self._unit_after(norms, num)
            if unit in exclude_units_of:
                continue
            if num.value in (20, 18, 16) and num.end < len(norms) and norms[num.end] == "gauge":
                continue  # IV catheter size, not a dose
            # prefer numbers after the anchor ("amio three hundred"), then before ("one milligram of epi")
            d = num.start - de if num.start >= de else ds - num.end + (0 if either_side else 0.5)
            if 0 <= d < best_d:
                best, best_d = num, d
        return best if best_d <= 5 else None

    @staticmethod
    def _dedupe(cands: list[Candidate]) -> list[Candidate]:
        out: list[Candidate] = []
        seen: set[tuple] = set()
        for c in cands:
            key = (c.kind, c.action, c.drug, c.dose, c.energy_j, c.rhythm, c.role, c.name)
            if c.kind in (EventKind.ROSC, EventKind.CPR_PAUSE, EventKind.RHYTHM_CHECK, Cue.CANCEL):
                key = (c.kind, c.action, c.drug)
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        return out

    # -------------------------------------------------------------- word alignment

    @staticmethod
    def _align(utt: Utterance, tokens: list[Tok]) -> list[int | None]:
        """Map each token to the index of the ASR word that contains it."""
        if not utt.words:
            return [None] * len(tokens)
        mapping: list[int | None] = []
        wi = 0
        wnorm = [re.sub(r"[^\wऀ-ॿ']", "", w.text.lower()) for w in utt.words]
        for t in tokens:
            found = None
            for k in range(wi, min(wi + 4, len(wnorm))):
                if t.norm and (t.norm in wnorm[k] or wnorm[k] in t.norm) and wnorm[k]:
                    found = k
                    break
            mapping.append(found)
            if found is not None:
                wi = (
                    found
                    if (
                        found + 1 < len(wnorm)
                        and t.norm != wnorm[found]
                        and t.norm in wnorm[found]
                        and not wnorm[found].endswith(t.norm)
                    )
                    else found + 1
                )
        return mapping

    def _token_confidences(self, utt: Utterance, tokens: list[Tok]) -> list[float | None]:
        m = self._align(utt, tokens)
        return [utt.words[k].confidence if k is not None else None for k in m]

    def _token_times(self, utt: Utterance, tokens: list[Tok]) -> list[float]:
        if not utt.words:
            return []
        m = self._align(utt, tokens)
        out = []
        last = utt.start_s
        for k in m:
            if k is not None:
                last = utt.words[k].end_ms / 1000
            out.append(last)
        return out
