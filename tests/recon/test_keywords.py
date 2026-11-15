"""The keyword query a topic sentence is probed with (M10a OBS-1; decisions 2026-11-14 item 4)."""

from __future__ import annotations

import os
import subprocess
import sys
import unicodedata

import pytest

from scholar_harness.recon.keywords import MAX_TERMS, keyword_query

SENTENCE = (
    "How does on-device inference of lightweight CNN models affect real-time "
    "weed detection accuracy in crop rows under field conditions?"
)


def test_a_sentence_becomes_its_first_six_topic_words():
    assert keyword_query(SENTENCE) == "on-device inference lightweight CNN models real-time"
    assert len(keyword_query(SENTENCE).split()) == MAX_TERMS == 6


def test_the_golden_topic_is_sent_byte_identical():
    # tests/fixtures/cassettes/golden_recon_probe.yaml replays this exact request.
    assert keyword_query("UAV crop weed mapping") == "UAV crop weed mapping"


@pytest.mark.parametrize(
    "query",
    [
        '"weed detection" AND UAV',
        "(weed OR crop) mapping",
        "weed mapping NOT satellite",
        "  UAV AND weed  ",
    ],
)
def test_a_query_that_is_already_boolean_is_sent_as_written(query):
    assert keyword_query(query) == query.strip()


def test_a_plain_and_or_not_word_never_becomes_an_operator():
    out = keyword_query("Weed detection and crop mapping or yield, not soil")
    assert out == "Weed detection crop mapping yield soil"
    assert not {w.upper() for w in out.split()} & {"AND", "OR", "NOT"}


def test_duplicates_are_dropped_keeping_the_first_spelling_and_case():
    assert keyword_query("UAV weed maps: uav Weed maps from a UAV") == "UAV weed maps"


def test_trailing_punctuation_and_one_letter_words_are_removed():
    assert keyword_query("weed, crop; (x)") == "weed crop"
    assert keyword_query("weed, crop; x rows.") == "weed crop rows"


# --------------------------------------------------------------------------- review fixes (round 1)


def _whole_words(out: str, topic: str) -> bool:
    """Every output token is a whole word of the NFC topic, punctuation aside."""
    nfc = unicodedata.normalize("NFC", topic)
    words = {w.strip("?.,;:!()") for w in nfc.split()}
    return bool(out) and all(token in words for token in out.split())


def test_nfd_french_is_not_split_at_its_accents():
    topic = "détection des mauvaises herbes par télédétection"
    out = keyword_query(topic)
    assert out == "détection des mauvaises herbes par télédétection"
    assert _whole_words(out, topic)


@pytest.mark.parametrize(
    "topic",
    [
        # Arabic with harakat: weed detection by drones.
        "كَشْفُ الأَعْشَابِ "
        "الضَّارَّةِ "
        "بِالطَّائِرَاتِ",
        # Devanagari: weed detection for drones.
        "खरपतवार पहचान ड्रोन",
        # Tamil: weed detection drone.
        "களை கண்டறிதல் ட்ரோன்",
    ],
    ids=["arabic-harakat", "devanagari", "tamil"],
)
def test_combining_marks_stay_inside_their_word(topic):
    out = keyword_query(topic)
    assert _whole_words(out, topic)
    assert out.split() == unicodedata.normalize("NFC", topic).split()


def test_a_one_letter_word_is_measured_on_its_base_letters():
    # Arabic "wa" (and) with its vowel mark is one letter; a two-letter word with marks is kept.
    assert keyword_query("وَ زَرْع") == "زَرْع"


@pytest.mark.parametrize(
    ("topic", "query"),
    [
        ("Is NO a signal molecule in plants", "NO signal molecule plants"),
        ("AI in IT security", "AI IT security"),
        ("What DO teams do with UAV data", "DO teams UAV data"),
    ],
)
def test_an_acronym_is_never_dropped_as_a_stopword(topic, query):
    assert keyword_query(topic) == query


def test_an_all_caps_topic_drops_its_stopwords():
    assert keyword_query("HOW IS IT USED IN WEED MAPPING") == "WEED MAPPING"


def test_parentheses_alone_are_punctuation_not_a_query():
    topic = "How do unmanned aerial vehicles (UAVs) improve weed mapping?"
    assert keyword_query(topic) == "unmanned aerial vehicles UAVs improve weed"


def test_an_operator_inside_a_hyphenated_word_is_not_a_query():
    assert keyword_query("NOT-gate circuits for the logic?") == "NOT-gate circuits logic"
    assert keyword_query("ANDROID apps OR-mapping for the farm") == "ANDROID apps OR-mapping farm"


def test_the_french_sentence_is_pinned():
    """A known limit: the stopwords are English, so French function words are kept.

    The six-word cap then spends most of the query on them; the researcher sees
    the query and may edit it (decision 2026-11-14, 1a).
    """
    topic = (
        "Quelle est l'influence de la télédétection par drone sur "
        "la détection des mauvaises herbes ?"
    )
    assert keyword_query(topic) == "Quelle est de la télédétection par"


@pytest.mark.slow
def test_the_query_does_not_depend_on_the_hash_seed():
    code = (
        "import sys; from scholar_harness.recon.keywords import keyword_query; "
        "sys.stdout.buffer.write(keyword_query(sys.argv[1]).encode('utf-8'))"
    )
    outs = set()
    for seed in ("0", "1", "12345"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        proc = subprocess.run(
            [sys.executable, "-c", code, SENTENCE], capture_output=True, env=env, timeout=120, check=True
        )
        outs.add(proc.stdout.decode("utf-8"))
    assert outs == {"on-device inference lightweight CNN models real-time"}


def test_the_same_topic_always_gives_the_same_query():
    assert len({keyword_query(SENTENCE) for _ in range(5)}) == 1


def test_a_topic_with_nothing_left_is_sent_stripped():
    assert keyword_query("  How does it affect what?  ") == "How does it affect what?"
    assert keyword_query("") == ""


def test_a_french_sentence_keeps_its_words():
    out = keyword_query("Détection des mauvaises herbes par drone en agriculture de précision")
    assert out and out.split()[0] == "Détection"
    assert len(out.split()) <= MAX_TERMS


# --------------------------------------------------------------------------- review fixes (round 2)


@pytest.mark.parametrize(
    "topic",
    ["weed (OR crop)", "weed AND, crop yield", "Effects of NOT. weed", "  weed mapping (NOT satellite)  "],
)
def test_a_capital_operator_glued_to_punctuation_makes_the_topic_a_query(topic):
    """Review item 3: never keyworded, so a capital operator is never sent bare as an 'acronym'."""
    assert keyword_query(topic) == topic.strip()


def test_a_hyphenated_operator_word_is_still_keyworded():
    assert keyword_query("NOT-gate circuits for the logic?") == "NOT-gate circuits logic"


def test_a_keyworded_output_never_holds_an_operator_word_in_any_case():
    import random

    vocab = ["weed", "crop", "UAV", "and", "AND", "And", "or", "OR", "oR", "not", "NOT", "Not",
             "NOT-gate", "OR-mapping", "ANDROID", "the", "of", "mapping", "x"]
    glue = ["", "", "(", ")", ",", ".", ";", ":", "?"]
    rng = random.Random(20261114)
    checked = 0
    for _ in range(2000):
        words = []
        for _w in range(rng.randint(1, 8)):
            word = rng.choice(vocab)
            if rng.random() < 0.3:
                word = rng.choice(glue) + word + rng.choice(glue)
            words.append(word)
        topic = " ".join(words)
        out = keyword_query(topic)
        if out == topic.strip():
            continue  # sent as written: a query, or nothing left
        checked += 1
        assert not {t.casefold() for t in out.split()} & {"and", "or", "not"}, (topic, out)
    assert checked > 500


def test_a_persian_zwnj_word_stays_one_word():
    """Review item 4: U+200C between two letters is inside the word, like the hyphen."""
    topic = "تشخیص علف‌های هرز با پهپاد"  # weed detection with drones
    out = keyword_query(topic)
    nfc = unicodedata.normalize("NFC", topic)
    assert "علف‌های" in out.split()
    assert out.split() == nfc.split()
    assert all(token in nfc for token in out.split())


def test_a_zwj_between_letters_stays_and_a_trailing_one_is_a_separator():
    assert keyword_query("क्‍ष weed‍ mapping") == "क्‍ष weed mapping"


def test_each_leg_summary_names_the_query_its_database_received():
    from scholar_harness.recon.session import _legs_summary

    legs = _legs_summary([
        {"provider": "openalex", "status": "ok", "executed_query": "UAV crop weed mapping"},
        {"provider": "crossref", "status": "ok"},
    ])
    assert [leg["executed_query"] for leg in legs] == ["UAV crop weed mapping", None]
