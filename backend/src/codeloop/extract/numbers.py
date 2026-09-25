"""Parse spoken numbers inside a token stream, in English, romanized Hindi and Devanagari.

Handles the forms clinicians actually use for doses and energies:
  "three hundred", "three zero zero", "one fifty", "one hundred and fifty", "300",
  "one", "0.5", "point five", "ek", "teen sau", "तीन सौ", "डेढ़ सौ", "एक".
"""

from __future__ import annotations

from dataclasses import dataclass

_UNITS = {
    "zero": 0,
    "oh": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    # romanized Hindi
    "ek": 1,
    "teen": 3,
    "chaar": 4,
    "char": 4,
    "paanch": 5,
    "panch": 5,
    "chhe": 6,
    "saat": 7,
    "aath": 8,
    "nau": 9,
    "das": 10,
    # Devanagari
    "शून्य": 0,
    "एक": 1,
    "दो": 2,
    "तीन": 3,
    "चार": 4,
    "पांच": 5,
    "पाँच": 5,
    "छह": 6,
    "सात": 7,
    "आठ": 8,
    "नौ": 9,
    "दस": 10,
}
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "bees": 20,
    "pachaas": 50,
    "pachas": 50,
    "बीस": 20,
    "पचास": 50,
}
_HUNDRED = {"hundred", "sau", "सौ"}
_THOUSAND = {"thousand", "hazaar", "hazar", "हज़ार", "हजार"}
_HALF_MORE = {"dedh": 1.5, "डेढ़": 1.5, "dhai": 2.5, "ढाई": 2.5}  # dedh sau = 150
_AMBIGUOUS_SINGLE = {"do", "oh"}  # "do" is also English; "oh" is an interjection


@dataclass(frozen=True)
class NumberSpan:
    value: float
    start: int  # token index, inclusive
    end: int  # token index, exclusive


def _digit(tok: str) -> float | None:
    try:
        return float(tok.replace(",", ""))
    except ValueError:
        return None


def parse_numbers(tokens: list[str]) -> list[NumberSpan]:
    """Find numbers in lower-cased tokens. Returns non-overlapping spans, left to right."""
    out: list[NumberSpan] = []
    i = 0
    n = len(tokens)
    while i < n:
        span = _parse_at(tokens, i)
        if span is None:
            i += 1
            continue
        out.append(span)
        i = span.end
    return out


def _small(tokens: list[str], i: int) -> tuple[int, int] | None:
    """Parse 0-99 starting at i. Returns (value, next_index)."""
    t = tokens[i]
    if t in _TENS:
        v = _TENS[t]
        if i + 1 < len(tokens) and tokens[i + 1] in _UNITS and 0 < _UNITS[tokens[i + 1]] < 10:
            return v + _UNITS[tokens[i + 1]], i + 2
        return v, i + 1
    if t in _UNITS:
        return _UNITS[t], i + 1
    return None


def _parse_at(tokens: list[str], i: int) -> NumberSpan | None:
    t = tokens[i]
    n = len(tokens)

    # "point five"
    if t == "point" and i + 1 < n and tokens[i + 1] in _UNITS and _UNITS[tokens[i + 1]] < 10:
        return NumberSpan(float(f"0.{_UNITS[tokens[i + 1]]}"), i, i + 2)

    d = _digit(t)
    if d is not None:
        # "3 0 0" spoken digit by digit and transcribed as separate digits
        j = i + 1
        digits = t if t.isdigit() and len(t) == 1 else None
        while digits is not None and j < n and tokens[j].isdigit() and len(tokens[j]) == 1:
            digits += tokens[j]
            j += 1
        if digits is not None and len(digits) > 1:
            return NumberSpan(float(digits), i, j)
        return NumberSpan(d, i, i + 1)

    # "dedh sau" = 150
    if t in _HALF_MORE and i + 1 < n and tokens[i + 1] in _HUNDRED:
        return NumberSpan(_HALF_MORE[t] * 100, i, i + 2)

    if t not in _UNITS and t not in _TENS:
        return None
    if t in _AMBIGUOUS_SINGLE and not (i + 1 < n and (tokens[i + 1] in _HUNDRED or tokens[i + 1] in _UNITS)):
        return None

    # Digit-by-digit: "three zero zero", "one five zero"
    if t in _UNITS and _UNITS[t] < 10:
        j = i
        digits = ""
        while j < n and tokens[j] in _UNITS and _UNITS[tokens[j]] < 10:
            digits += str(_UNITS[tokens[j]])
            j += 1
        if len(digits) >= 3 and ("0" in digits[1:]):
            return NumberSpan(float(digits), i, j)

    small = _small(tokens, i)
    if small is None:
        return None
    value, j = small
    total = 0
    if j < n and tokens[j] in _HUNDRED:
        value *= 100
        j += 1
        if j < n and tokens[j] == "and":
            j += 1
        rest = _small(tokens, j) if j < n else None
        if rest:
            value += rest[0]
            j = rest[1]
    elif j < n and tokens[j] in _THOUSAND:
        total = value * 1000
        return NumberSpan(float(total), i, j + 1)
    elif value < 10 and j < n and tokens[j] in _TENS:
        # "one fifty" = 150, "two twenty" = 220 (energy / dose shorthand)
        tail = _small(tokens, j)
        assert tail is not None
        return NumberSpan(float(value * 100 + tail[0]), i, tail[1])
    return NumberSpan(float(value), i, j)
