import pytest

from codeloop.extract.numbers import parse_numbers


def vals(text: str) -> list[float]:
    return [s.value for s in parse_numbers(text.lower().split())]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("give one milligram", [1]),
        ("amiodarone three hundred milligrams", [300]),
        ("three zero zero", [300]),
        ("3 0 0", [300]),
        ("amio one fifty pushing", [150]),
        ("one hundred and fifty", [150]),
        ("charge to two hundred", [200]),
        ("200 joules", [200]),
        ("point five", [0.5]),
        ("0.5 mg", [0.5]),
        ("epi ek milligram de do", [1]),
        ("teen sau", [300]),
        ("dedh sau", [150]),
        ("तीन सौ", [300]),
        ("डेढ़ सौ", [150]),
        ("एपि एक मिलीग्राम", [1]),
        ("twenty gauge", [20]),
        ("one twenty", [120]),
        ("de do", []),
        ("oh no", []),
    ],
)
def test_parse_numbers(text: str, expected: list[float]) -> None:
    assert vals(text) == expected
