import pytest

from codeloop.extract.phonetic import key, token_matches


@pytest.mark.parametrize(
    ("dev", "eng"),
    [
        ("रिदम", "rhythm"),
        ("चेक", "check"),
        ("कंप्रेशंस", "compressions"),
        ("कंटिन्यू", "continue"),
        ("एसिस्टली", "asystole"),
        ("एसिस्टोल", "asystole"),
        ("मिलीग्राम", "milligram"),
        ("एमियोडरोन", "amiodarone"),
        ("एपी", "epi"),
        ("ईपी", "epi"),
        ("चार्ज", "charge"),
        ("स्टार्ट", "start"),
        ("करो", "karo"),
        ("लेड", "lead"),
        ("कैंसल", "cancel"),
        ("पॉज़", "pause"),
        ("कोडलूप", "codeloop"),
    ],
)
def test_devanagari_rendering_matches_english(dev: str, eng: str) -> None:
    assert token_matches(dev, eng), (dev, key(dev), eng, key(eng))


@pytest.mark.parametrize(
    ("dev", "eng"),
    [
        ("सुनीता", "asystole"),
        ("मत", "amio"),
        ("नॉट", "no"),
        ("हियर", "hold"),
        ("एपी", "atropine"),
    ],
)
def test_unrelated_words_do_not_match(dev: str, eng: str) -> None:
    assert not token_matches(dev, eng)


def test_english_tokens_are_never_fuzzy_matched() -> None:
    assert not token_matches("rythm", "rhythm")  # English stays exact; ASR handles spelling
    assert token_matches("rhythm", "rhythm")
