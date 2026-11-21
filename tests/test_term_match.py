"""M8b-triage-highlights: the search-term matcher (decisions 2026-11-21, items 3 and 10).

Whole words and phrases, case-insensitive, English plurals as one word, space
and hyphen variants of a phrase alike, no other stemming, no partial words.
"""

from __future__ import annotations

from scholar_harness.term_match import concept_marks, find_term, same_word, utf16_offset


def spans(term: str, text: str) -> list[str]:
    return [text[s:e] for s, e in find_term(term, text)]


# --------------------------------------------------------------------------- words


def test_whole_words_only_no_partial_match():
    assert spans("weed", "Weeding robots and seaweed") == []
    assert spans("UAV", "UAVision and AUAV") == []


def test_case_insensitive():
    assert spans("uav", "A UAV and a Uav") == ["UAV", "Uav"]


def test_english_plurals_are_one_word_both_ways():
    assert spans("weed", "weeds and weed") == ["weeds", "weed"]
    assert spans("weeds", "one weed") == ["weed"]
    assert spans("UAV", "two UAVs") == ["UAVs"]
    assert spans("process", "processes") == ["processes"]
    assert spans("body", "bodies") == ["bodies"]
    assert spans("bodies", "a body") == ["body"]


def test_no_stemming_beyond_plurals():
    assert spans("leaf", "leaves") == []
    assert spans("detect", "detection detected") == []
    assert spans("crop", "cropping") == []


def test_short_words_are_not_singularised():
    # "gas" is not the plural of "ga"; "us" is not the plural of "u".
    assert not same_word("ga", "gas")
    assert not same_word("u", "us")
    assert same_word("uav", "uavs")


def test_phrase_matches_consecutive_words():
    assert spans("weed detection", "Weed detection in maize") == ["Weed detection"]
    assert spans("weed detection", "weed and detection") == []


def test_phrase_plural_on_any_word():
    assert spans("weed map", "weeds maps") == ["weeds maps"]


def test_hyphen_and_space_variants_alike():
    text = "multi-spectral, multi spectral, multi‐spectral and multispectral"
    assert spans("multi-spectral", text) == ["multi-spectral", "multi spectral", "multi‐spectral"]
    assert spans("multi spectral", text) == ["multi-spectral", "multi spectral", "multi‐spectral"]
    assert spans("multispectral", text) == ["multispectral"]


def test_punctuation_ends_a_phrase():
    assert spans("weed detection", "weed. Detection") == []
    assert spans("weed detection", "weed, detection") == []
    assert spans("weed detection", "weed/detection") == []


def test_quoted_or_empty_terms():
    assert spans('"weed detection"', "weed detection") == ["weed detection"]
    assert find_term("", "anything") == []
    assert find_term("  -- ", "anything") == []


def test_unicode_letters_are_word_characters():
    assert spans("naive", "naïve") == []
    assert spans("naïve", "a naïve bayes") == ["naïve"]


# ------------------------------------------------------------------------ concepts


CONCEPTS = [
    {"concept": "UAV", "synonyms": ["drone", "unmanned aerial vehicle"]},
    {"concept": "weed", "synonyms": ["weed detection"]},
    {"concept": "maize", "synonyms": []},
]


def test_concept_marks_counts_and_absence():
    text = "Drones for weed detection: UAVs map weeds"
    marks, mentions = concept_marks(text, CONCEPTS)
    assert [(text[s:e], c) for s, e, c in marks] == [
        ("Drones", 0),
        ("weed detection", 1),
        ("UAVs", 0),
        ("weeds", 1),
    ]
    assert mentions == [2, 2, 0]


def test_overlapping_terms_longest_wins_then_concept_order():
    concepts = [
        {"concept": "aerial vehicle", "synonyms": []},
        {"concept": "unmanned aerial vehicle", "synonyms": []},
        {"concept": "vehicle", "synonyms": []},
    ]
    text = "an unmanned aerial vehicle"
    marks, mentions = concept_marks(text, concepts)
    assert [(text[s:e], c) for s, e, c in marks] == [("unmanned aerial vehicle", 1)]
    # Shadowed concepts are still mentioned: the legend must not call them missing.
    assert mentions == [1, 1, 1]


def test_same_span_two_concepts_first_listed_wins():
    concepts = [{"concept": "crop", "synonyms": []}, {"concept": "crops", "synonyms": []}]
    marks, mentions = concept_marks("crops", concepts)
    assert marks == [(0, 5, 0)]
    assert mentions == [1, 1]


def test_marks_are_sorted_and_do_not_overlap():
    concepts = [{"concept": "weed", "synonyms": ["weed map"]}, {"concept": "map", "synonyms": []}]
    text = "weed map map weed"
    marks, _ = concept_marks(text, concepts)
    assert marks == sorted(marks)
    for (_, e1, _), (s2, _, _) in zip(marks, marks[1:]):
        assert e1 <= s2


def test_concept_without_words_and_bad_entries():
    marks, mentions = concept_marks("weed", [{"concept": "", "synonyms": []}, "junk", {"concept": "weed"}])
    assert marks == [(0, 4, 2)]
    assert mentions == [0, 0, 1]


def test_deterministic():
    text = "UAV drones weeds weed detection maize"
    assert concept_marks(text, CONCEPTS) == concept_marks(text, list(CONCEPTS))


# ---------------------------------------------------------------------------- utf16


def test_utf16_offset_counts_surrogate_pairs():
    text = "a\U0001d465b weed"
    assert utf16_offset(text, 0) == 0
    assert utf16_offset(text, 2) == 3
    assert utf16_offset(text, len(text)) == len(text) + 1
