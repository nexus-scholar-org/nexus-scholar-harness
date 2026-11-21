"""M11a Part A: the query workbench's pure core (`scholar_search.workbench`).

A version of the query is concepts joined by AND, terms joined by OR, years and
languages. The workbench compiles it with the genesis compiler, lists the
variants one Count asks (the full query and the query with each concept left
out), the variants "what each synonym adds" asks, and the gains. It also holds
the workbench's word match (whole words, English plurals folded). Nothing here
sends a request.
"""

from __future__ import annotations

import pytest

from scholar_search import workbench as wb
from scholar_search.protocol_adapter import compile_protocol_search


def _version(*concepts, start=2015, end=2025, languages=("en",)):
    return wb.parse_version({
        "query_key": "main",
        "concepts": [{"concept": c[0], "synonyms": list(c[1:])} for c in concepts],
        "start_year": start, "end_year": end, "languages": list(languages),
    })


FOUR = (("aerial", "unmanned aerial vehicle"), ("multispectral", "multi-spectral"), ("plant",), ("segmentation", "semantic segmentation"))


# --------------------------------------------------------------------------- the version


def test_a_version_compiles_with_the_genesis_compiler():
    version = _version(*FOUR)
    query = wb.compile_version(version)
    expected, _ = compile_protocol_search(wb.protocol_dict(version))
    assert query.text == expected.text
    assert query.text == ('(aerial OR "unmanned aerial vehicle") AND (multispectral OR multi-spectral) '
                          'AND plant AND (segmentation OR "semantic segmentation")')
    assert (query.year_min, query.year_max, query.language) == (2015, 2025, "en")


def test_a_version_with_no_concept_is_invalid():
    with pytest.raises(wb.VersionInvalid, match="at least one concept"):
        _version()
    with pytest.raises(wb.VersionInvalid, match="at least one concept"):
        wb.parse_version({"concepts": [{"concept": "  ", "synonyms": [" "]}]})


def test_a_version_refuses_years_in_the_wrong_order_and_another_query_key():
    with pytest.raises(wb.VersionInvalid, match="start year"):
        _version(("a",), start=2025, end=2015)
    with pytest.raises(wb.VersionInvalid, match="main"):
        wb.parse_version({"query_key": "second", "concepts": [{"concept": "a"}]})


def test_blank_and_repeated_terms_are_dropped_and_a_blank_name_takes_its_first_synonym():
    version = wb.parse_version({"concepts": [{"concept": " ", "synonyms": ["Plant", "plant", " ", "crop plant"]}]})
    assert version.concepts[0].terms == ("Plant", "crop plant")
    assert version.query_key == "main"


# --------------------------------------------------------------------------- variants


def test_one_count_asks_the_full_query_and_one_query_per_concept_left_out():
    version = _version(*FOUR)
    variants = wb.count_variants(version)
    assert [(v.kind, v.concept_index) for v in variants] == [("full", None), ("drop", 0), ("drop", 1), ("drop", 2), ("drop", 3)]
    dropped = wb.compile_version(variants[2].version).text
    assert "multispectral" not in dropped and "aerial" in dropped
    assert variants[2].concept == "multispectral"


def test_one_concept_has_no_drop_variant():
    assert [v.kind for v in wb.count_variants(_version(("plant", "plants")))] == ["full"]


def test_what_each_synonym_adds_removes_one_term_at_a_time():
    version = _version(*FOUR)
    variants = wb.synonym_variants(version, 1)
    assert [(v.kind, v.term) for v in variants] == [("full", None), ("synonym", "multispectral"), ("synonym", "multi-spectral")]
    assert "(multispectral OR" not in wb.compile_version(variants[1].version).text
    assert "multi-spectral" in wb.compile_version(variants[1].version).text


def test_removing_the_only_term_of_a_concept_leaves_the_concept_out():
    version = _version(*FOUR)
    only = wb.synonym_variants(version, 2)
    assert [(v.kind, v.term) for v in only] == [("full", None), ("synonym", "plant")]
    assert wb.compile_version(only[1].version).text == wb.compile_version(wb.without_concept(version, 2)).text


def test_the_only_term_of_the_only_concept_cannot_be_removed():
    assert [v.kind for v in wb.synonym_variants(_version(("plant",)), 0)] == ["full"]


def test_a_concept_index_out_of_range_is_invalid():
    with pytest.raises(wb.VersionInvalid, match="no concept 9"):
        wb.synonym_variants(_version(*FOUR), 9)


# --------------------------------------------------------------------------- gains and the note


def test_gain_and_ratio_are_the_engines():
    assert wb.gain(130, 236) == {"gain": 106, "ratio": 1.8}
    assert wb.gain(130, 512) == {"gain": 382, "ratio": 3.9}
    assert wb.gain(0, 12) == {"gain": 12, "ratio": None}
    assert wb.gain(None, 12) == {"gain": None, "ratio": None}


def test_the_note_is_raised_when_leaving_a_concept_out_at_least_doubles_a_count():
    assert wb.NOTE_RATIO == 2.0
    assert wb.doubles(166, 332) and wb.doubles(166, 781)
    assert not wb.doubles(166, 331)
    assert wb.doubles(0, 3) and not wb.doubles(0, 0)
    assert not wb.doubles(None, 300) and not wb.doubles(166, None)


def test_the_largest_effect_is_the_largest_gain():
    assert wb.largest([{"gain": 106}, {"gain": 382}, {"gain": None}]) == 1
    assert wb.largest([{"gain": 0}, {"gain": None}]) is None


# --------------------------------------------------------------------------- the word match (whole words, English plurals)


@pytest.mark.parametrize(("term", "text", "hit"), [
    ("plant", "Plants in a field", True),
    ("plants", "one plant", True),
    ("image", "multispectral images", True),
    ("species", "a species list", True),
    ("library", "two libraries", True),
    ("box", "boxes of seed", True),
    ("branch", "branches", True),
    ("glass", "glasses", True),
    ("class", "the class", True),
    ("plant", "planting", False),
    ("plant", "transplant", False),
    ("semantic segmentation", "Semantic-segmentation of images", True),
    ("semantic segmentation", "semantic instance segmentation", False),
    ("multi-spectral", "multi spectral camera", True),
    ("bus", "a bus", True),
])
def test_a_term_matches_whole_words_with_english_plurals(term, text, hit):
    assert wb.term_matches(term, text) is hit


def test_a_version_matches_a_text_concept_by_concept():
    version = _version(*FOUR)
    text = "Semantic segmentation of plants from unmanned aerial vehicle imagery"
    assert wb.concepts_found(version, text) == [True, False, True, True]
    assert wb.lacking(version, text) == ["multispectral"]
    assert not wb.matches(version, text)
    assert wb.matches(version, text + " with a multispectral camera")


def test_the_fold_is_stated_once():
    assert wb.fold_word("Libraries") == "library"
    assert wb.fold_word("boxes") == "box"
    assert wb.fold_word("glass") == "glass"
    assert wb.fold_word("bus") == "bus"
    assert wb.fold_word("cats") == "cat"
