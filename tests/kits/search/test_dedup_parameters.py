"""M7-method M4: the dedup tiers are parameters, today's values the defaults.

Decision 2026-11-08: a protocol may set ``title_similarity`` (0.90-1.00),
``first_author`` and ``year_tolerance`` (0-2). With no arguments the
deduplicator behaves exactly as before (the existing dedup suites pin that).
"""

from __future__ import annotations

from difflib import SequenceMatcher

import pytest

from scholar_search.dedup import Deduplicator, _title_key
from scholar_search.models import Author, Document


def _doc(title: str, year: int, surname: str, pid: str) -> Document:
    return Document(title=title, year=year, provider="local_ris", provider_id=pid, authors=[Author(family_name=surname)])


NEAR_A = "Weed mapping in maize with unmanned aerial vehicles and deep learning"
NEAR_B = "Weed mapping in maize using unmanned aerial vehicle and deep learning"


def test_the_near_titles_sit_between_the_two_thresholds() -> None:
    ratio = SequenceMatcher(None, _title_key(NEAR_A), _title_key(NEAR_B)).ratio()
    assert 0.93 <= ratio < 0.97, ratio  # the pair the next test relies on


def _clusters(dedup: Deduplicator, docs: list[Document]) -> int:
    return len(dedup.deduplicate(docs))


def test_a_looser_title_threshold_merges_a_pair_097_keeps_apart() -> None:
    def pair():
        return [_doc(NEAR_A, 2021, "Huang", "a"), _doc(NEAR_B, 2021, "Huang", "b")]

    assert _clusters(Deduplicator(), pair()) == 2
    assert _clusters(Deduplicator(title_similarity=0.93), pair()) == 1


def test_year_tolerance_zero_separates_a_pair_one_year_apart() -> None:
    def pair():
        return [_doc(NEAR_A, 2020, "Huang", "a"), _doc(NEAR_A + " ", 2021, "Huang", "b")]

    assert _clusters(Deduplicator(), pair()) == 1
    assert _clusters(Deduplicator(year_tolerance=0), pair()) == 2


def test_year_tolerance_two_merges_a_pair_two_years_apart() -> None:
    def pair():
        return [_doc(NEAR_A, 2019, "Huang", "a"), _doc(NEAR_A, 2021, "Huang", "b")]

    assert _clusters(Deduplicator(), pair()) == 2
    assert _clusters(Deduplicator(year_tolerance=2), pair()) == 1


def test_first_author_off_merges_a_pair_with_different_first_authors() -> None:
    def pair():
        return [_doc(NEAR_A, 2021, "Huang", "a"), _doc(NEAR_A, 2021, "Deng", "b")]

    assert _clusters(Deduplicator(), pair()) == 2
    assert _clusters(Deduplicator(first_author=False), pair()) == 1


@pytest.mark.parametrize(
    "kwargs",
    [{"title_similarity": 0.89}, {"title_similarity": 1.2}, {"year_tolerance": 3}, {"year_tolerance": -1}, {"year_tolerance": True}],
)
def test_the_deduplicator_refuses_values_outside_the_limits(kwargs) -> None:
    with pytest.raises(ValueError):
        Deduplicator(**kwargs)
