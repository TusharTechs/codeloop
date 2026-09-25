from codeloop.engine.speech import say_clock, say_duration, say_number, say_quantity


def test_numbers() -> None:
    assert say_number(1) == "one"
    assert say_number(150) == "one hundred fifty"
    assert say_number(300) == "three hundred"
    assert say_number(0.5) == "zero point five"
    assert say_number(1000) == "one thousand"


def test_quantities_use_full_unit_words() -> None:
    assert say_quantity(1, "mg") == "one milligram"
    assert say_quantity(300, "mg") == "three hundred milligrams"
    assert say_quantity(200, "J") == "two hundred joules"
    assert say_quantity(50, "mEq") == "fifty milliequivalents"


def test_durations_and_clock() -> None:
    assert say_duration(180) == "three minutes"
    assert say_duration(190) == "three minutes ten seconds"
    assert say_duration(15) == "fifteen seconds"
    assert say_clock(52) == "zero fifty-two"
    assert say_clock(125) == "two oh five"
