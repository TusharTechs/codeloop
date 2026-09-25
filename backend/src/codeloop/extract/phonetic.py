"""Cross-script phonetic keys so Devanagari renderings of English words match English cues.

AssemblyAI Universal-3.5 Pro writes Hindi-accented English in Devanagari ("रिदम चेक",
"कंप्रेशंस कंटिन्यू करो"). Rather than keep an endless alias list, both scripts are reduced
to a coarse consonant skeleton that ignores vowels, voicing and aspiration:

    "rhythm" → rtn     "रिदम" → rtn
    "compressions" → knprsns     "कंप्रेशंस" → knprsns
    "asystole" → Vstl   "एसिस्टली" → Vstl

The key is deliberately lossy; it is only compared against a small, closed vocabulary
(cue phrases, formulary aliases, the wake word), and only for tokens written in Devanagari,
so English matching is never loosened.
"""

from __future__ import annotations

import re
from functools import cache

_DEV = re.compile(r"[ऀ-ॿ]")

_CONS = {
    "क": "k",
    "ख": "k",
    "ग": "k",
    "घ": "k",
    "ङ": "n",
    "च": "C",
    "छ": "C",
    "ज": "k",
    "झ": "k",
    "ञ": "n",
    "ट": "t",
    "ठ": "t",
    "ड": "t",
    "ढ": "t",
    "ण": "n",
    "त": "t",
    "थ": "t",
    "द": "t",
    "ध": "t",
    "न": "n",
    "प": "p",
    "फ": "f",
    "ब": "p",
    "भ": "p",
    "म": "n",
    "य": "",
    "र": "r",
    "ल": "l",
    "ळ": "l",
    "व": "f",
    "श": "s",
    "ष": "s",
    "स": "s",
    "ह": "",
}
_NUKTA = {"ज": "s", "ड": "r", "ढ": "r", "फ": "f", "क": "k", "ख": "k", "ग": "k"}
_IND_VOWELS = set("अआइईउऊऋएऐओऔऍऑ")
_NASAL = {"ं": "n", "ँ": "n"}
_NUKTA_MARK = "़"


def has_devanagari(s: str) -> bool:
    return bool(_DEV.search(s))


def _collapse(key: str) -> str:
    out = []
    for ch in key:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


@cache
def key(word: str) -> str:
    """Phonetic key for one word in either script."""
    w = word.strip().lower()
    if not w:
        return ""
    return _collapse(_dev_key(w) if has_devanagari(w) else _latin_key(w))


def _dev_key(w: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(w):
        nxt = w[i + 1] if i + 1 < len(w) else ""
        if ch in _CONS:
            out.append(_NUKTA[ch] if nxt == _NUKTA_MARK and ch in _NUKTA else _CONS[ch])
        elif ch in _IND_VOWELS:
            if not out:
                out.append("V")
        elif ch in _NASAL:
            out.append(_NASAL[ch])
    return "".join(out)


_LATIN_RULES = [
    ("tch", "C"),
    ("ch", "C"),
    ("sh", "s"),
    ("ph", "f"),
    ("th", "t"),
    ("dh", "t"),
    ("kh", "k"),
    ("gh", "k"),
    ("bh", "p"),
    ("ck", "k"),
    ("qu", "k"),
    ("x", "ks"),
]
_LATIN_MAP = {
    "b": "p",
    "d": "t",
    "g": "k",
    "j": "k",
    "c": "k",
    "q": "k",
    "v": "f",
    "w": "f",
    "z": "s",
    "m": "n",
    "h": "",
    "y": "",
}
_VOWELS = set("aeiou")


def _latin_key(w: str) -> str:
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return ""
    start = "V" if w[0] in _VOWELS else ""
    for a, b in _LATIN_RULES:
        w = w.replace(a, b)
    out = [start]
    for ch in w:
        if ch in _VOWELS:
            continue
        out.append(_LATIN_MAP.get(ch, ch))
    return "".join(out)


def _dist_le1(a: str, b: str) -> bool:
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b, strict=True)) == 1
    if len(a) > len(b):
        a, b = b, a
    return any(a == b[:i] + b[i + 1 :] for i in range(len(b)))


def token_matches(token: str, cue_word: str, fuzzy_min_len: int = 4) -> bool:
    """Does a transcript token match one word of a cue phrase?

    Exact match always counts. A Devanagari token may also match an English cue word when
    their phonetic keys are equal, or differ by one edit for longer keys.
    """
    if token == cue_word:
        return True
    if not has_devanagari(token) or has_devanagari(cue_word):
        return False
    a, b = key(token), key(cue_word)
    if not a or not b:
        return a == b and not a and not b and len(token) <= 3
    if a == b:
        return True
    return min(len(a), len(b)) >= fuzzy_min_len and _dist_le1(a, b)
