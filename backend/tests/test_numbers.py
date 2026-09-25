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


def test_one_hundred_and_fifty_joules_is_one_shock_not_two() -> None:
    # Regression (held-out v2): the "several actions" split once turned this into 100 J and 50 J.
    from codeloop.domain.formulary import default_formulary
    from codeloop.domain.models import Utterance
    from codeloop.extract.grammar import Grammar

    g = Grammar(default_formulary())
    for text in ("Shock at one hundred and fifty joules.", "Charge to two hundred and give amio three hundred."):
        cands = g.extract(Utterance(id="u", turn_order=0, text=text, start_s=0, end_s=2))
        shocks = [c.energy_j for c in cands if c.action == "shock"]
        assert shocks in ([150.0], [200.0]), (text, shocks)
