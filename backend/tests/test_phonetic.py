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


def test_hinglish_resuscitation_line_in_devanagari() -> None:
    from codeloop.domain.formulary import default_formulary
    from codeloop.domain.models import Utterance
    from codeloop.extract.grammar import Grammar

    g = Grammar(default_formulary())
    u = Utterance(id="u", turn_order=0, text="पॉज कंप्रेशंस रिदम चेक दैट्स वीफिब चार्ज टू 200 जूल्स", start_s=0, end_s=3)
    kinds = [(str(c.kind), c.rhythm, c.energy_j) for c in g.extract(u)]
    assert ("cpr_pause", None, None) in kinds
    assert ("rhythm_check", None, None) in kinds
    assert any(k[0] == "order" and k[2] == 200 for k in kinds)
