from codeloop.aai.turns import TurnAssembler, split_turn


def w(text: str, start: int, speaker: str, conf: float = 0.9) -> dict:
    return {"text": text, "start": start, "end": start + 300, "confidence": conf, "speaker": speaker}


def test_turn_is_split_where_the_word_speaker_changes() -> None:
    turn = {
        "type": "Turn",
        "turn_order": 4,
        "end_of_turn": True,
        "speaker_label": "A",
        "words": [
            w("Give", 0, "A"),
            w("1", 300, "A"),
            w("milligram", 600, "A"),
            w("of", 900, "A"),
            w("epinephrine.", 1200, "A"),
            w("Is", 2000, "B"),
            w("IV", 2300, "B"),
            w("access", 2600, "B"),
            w("in", 2900, "B"),
            w("yet?", 3200, "B"),
            w("Line", 4000, "A"),
            w("is", 4300, "A"),
            w("in.", 4600, "A"),
        ],
    }
    utts = split_turn(turn)
    assert [(u.id, u.speaker, u.text) for u in utts] == [
        ("t4a", "A", "Give 1 milligram of epinephrine."),
        ("t4b", "B", "Is IV access in yet?"),
        ("t4c", "A", "Line is in."),
    ]
    assert utts[0].start_s == 0.0 and utts[0].end_s == 1.5
    assert utts[1].words[0].text == "Is"


def test_pending_words_join_the_neighbouring_speaker() -> None:
    turn = {
        "type": "Turn",
        "turn_order": 1,
        "end_of_turn": True,
        "speaker_label": "A",
        "words": [w("Amio", 0, "PENDING"), w("300", 300, "B"), w("is", 600, "PENDING"), w("in.", 900, "B")],
    }
    utts = split_turn(turn)
    assert [(u.speaker, u.text) for u in utts] == [("B", "Amio 300 is in.")]


def test_all_pending_falls_back_to_turn_label() -> None:
    turn = {
        "type": "Turn",
        "turn_order": 2,
        "end_of_turn": True,
        "speaker_label": "C",
        "words": [w("Resume", 0, "PENDING"), w("CPR.", 300, "PENDING")],
    }
    assert [u.speaker for u in split_turn(turn)] == ["C"]


def test_assembler_emits_each_final_turn_once_and_ignores_partials() -> None:
    a = TurnAssembler()
    partial = {"type": "Turn", "turn_order": 0, "end_of_turn": False, "words": [w("Give", 0, "A")]}
    final = {"type": "Turn", "turn_order": 0, "end_of_turn": True, "words": [w("Give", 0, "A")]}
    assert a.feed(partial) == []
    assert len(a.feed(final)) == 1
    assert a.feed(final) == []
    a.feed({"type": "SpeakerRevision", "revisions": [{"turn_order": 0, "speaker_label": "B"}]})
    assert a.revisions == [{"turn_order": 0, "speaker_label": "B"}]
