from codeloop.debrief import debrief_facts


def test_facts_are_spoken_sentences_built_from_the_record() -> None:
    record = {
        "code": {"outcome": "rosc"},
        "duration_s": 168.0,
        "summary": {"prompts_spoken": 3},
        "quality": [
            {"key": "time_to_first_shock", "value": 16.0, "status": "met", "display": "0:16"},
            {"key": "closed_loop_rate", "value": 1.0, "status": "met", "display": "3 of 3"},
            {"key": "cpr_fraction", "value": 0.852, "status": "met", "display": "85%"},
        ],
        "loops": [
            {
                "action": "drug",
                "drug": "epinephrine",
                "ordered_value": 1,
                "unit": "mg",
                "history": [{"state": "ORDERED", "note": ""}, {"state": "UNACKNOWLEDGED", "note": ""}],
            },
            {
                "action": "drug",
                "drug": "amiodarone",
                "ordered_value": 300,
                "unit": "mg",
                "history": [
                    {"state": "ORDERED", "note": ""},
                    {"state": "CONFLICT", "note": "read back 150 ≠ ordered 300"},
                ],
            },
        ],
        "second_listen": {"status": "done", "counts": {"confirmed": 13}, "live_events": 13},
    }
    say = debrief_facts(record)["say"]
    assert say[0] == "The code lasted two minutes forty eight seconds with return of circulation."
    assert "The first shock came sixteen seconds after the start, within the two-minute target." in say
    assert "Three of three orders were read back." in say
    assert "The order for epinephrine one milligram went unacknowledged for more than ten seconds." in say
    assert (
        "A read-back conflict was caught on amiodarone three hundred milligrams: ordered three hundred, "
        "read back one hundred fifty." in say
    )
    assert "The second listen confirmed thirteen of thirteen events in the record." in say
    assert not any(ch.isdigit() or ch == "≠" for s in say for ch in s), say  # everything spoken as words
