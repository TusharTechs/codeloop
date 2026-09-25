"""Render numbers, doses and durations as unambiguous spoken English.

Every word CodeLoop speaks is built here from engine values; the LLM never invents numbers.
Doses are spoken in full ("three hundred milligrams", never "three hundred mg") so that
TTS and listeners cannot confuse units, and decimals are read digit by digit.
"""

from __future__ import annotations

_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

_UNITS = {
    "mg": ("milligram", "milligrams"),
    "g": ("gram", "grams"),
    "mcg": ("microgram", "micrograms"),
    "mEq": ("milliequivalent", "milliequivalents"),
    "J": ("joule", "joules"),
}


def say_int(n: int) -> str:
    if n < 0:
        return "minus " + say_int(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + ("" if ones == 0 else " " + _ONES[ones])
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        return _ONES[hundreds] + " hundred" + ("" if rest == 0 else " " + say_int(rest))
    thousands, rest = divmod(n, 1000)
    return say_int(thousands) + " thousand" + ("" if rest == 0 else " " + say_int(rest))


def say_number(x: float) -> str:
    if float(x).is_integer():
        return say_int(int(x))
    whole, frac = f"{x:g}".split(".")
    return say_int(int(whole)) + " point " + " ".join(_ONES[int(d)] for d in frac)


def say_quantity(x: float | None, unit: str | None) -> str:
    if x is None:
        return ""
    singular, plural = _UNITS.get(unit or "", (unit or "", unit or ""))
    word = singular if x == 1 else plural
    return f"{say_number(x)} {word}".strip()


def say_duration(seconds: float) -> str:
    s = round(seconds)
    m, s = divmod(s, 60)
    parts = []
    if m:
        parts.append(f"{say_int(m)} minute{'s' if m != 1 else ''}")
    if s or not m:
        parts.append(f"{say_int(s)} second{'s' if s != 1 else ''}")
    return " ".join(parts)


def say_clock(seconds: float) -> str:
    """Code clock as spoken: 52 s → "zero fifty-two"; 125 s → "two oh five"."""
    m, s = divmod(round(seconds), 60)
    sec = f"oh {say_int(s)}" if s < 10 else say_int(s).replace(" ", "-")
    return f"{say_int(m)} {sec}"


def say_drug(drug: str | None) -> str:
    return (drug or "the drug").replace("_", " ")
