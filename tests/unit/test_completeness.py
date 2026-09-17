"""Tests for completeness scoring functions."""

from __future__ import annotations

import pytest

from scholar_search.completeness import (
    PROVIDER_WEIGHTS,
    compute_completeness_score,
    compute_total_score,
)
from scholar_search.models import Author, Document, ExternalIds


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def empty_doc():
    """Document with no metadata — base score should be 1 (not retracted)."""
    return Document(title="Empty")


@pytest.fixture
def full_doc():
    """Document with all metadata fields populated — base score should be 10."""
    return Document(
        title="Full Paper",
        year=2023,
        provider="openalex",
        provider_id="W123",
        external_ids=ExternalIds(doi="10.1234/example"),
        abstract="A" * 50,  # >20 chars
        authors=[
            Author(family_name="Smith", given_name="John", orcid="0000-0001-2345-6789")
        ],
        venue="Journal of Testing",
        url="https://example.com",
        citations_count=42,
    )


@pytest.fixture
def retracted_doc():
    """Document that would be retracted (model doesn't have retracted flag yet)."""
    return Document(
        title="Retracted Paper",
        year=2020,
        external_ids=ExternalIds(doi="10.1234/retracted"),
        abstract="This paper has been retracted for misconduct.",
        authors=[Author(family_name="Fraud", given_name="Bob")],
        venue="Sketchy Journal",
        citations_count=0,
    )


@pytest.fixture
def doc_short_abstract():
    """Document with abstract <= 20 chars — should not score for abstract bit."""
    return Document(
        title="Short Abstract",
        abstract="Short.",
        authors=[Author(family_name="A", given_name="B")],
        year=2021,
        external_ids=ExternalIds(doi="10.1234/short"),
    )


@pytest.fixture
def doc_no_doi():
    """Document without DOI — should not score for DOI bit."""
    return Document(
        title="No DOI Paper",
        year=2022,
        authors=[Author(family_name="X", given_name="Y")],
        venue="Conference Proceedings",
    )


@pytest.fixture
def doc_no_authors():
    """Document without authors — should not score for authors bit."""
    return Document(
        title="Anonymous Paper",
        year=2020,
        external_ids=ExternalIds(doi="10.1234/anon"),
    )


@pytest.fixture
def doc_with_orcid():
    """Document where at least one author has an ORCID."""
    return Document(
        title="ORCID Paper",
        authors=[Author(family_name="A", given_name="B", orcid="0000-0002-0000-0000")],
        year=2021,
    )


@pytest.fixture
def doc_with_citations():
    """Document with citations_count > 0."""
    return Document(
        title="Cited Paper",
        citations_count=10,
        year=2020,
    )


# ---------------------------------------------------------------------------
# Tests: compute_completeness_score
# ---------------------------------------------------------------------------


def test_empty_doc_score(empty_doc):
    """Empty doc should score 1 (only 'not retracted')."""
    assert compute_completeness_score(empty_doc) == 1


def test_full_doc_score(full_doc):
    """Full doc should score 10 (all bits set)."""
    score = compute_completeness_score(full_doc)
    assert score == 10


def test_retracted_doc_score(retracted_doc):
    """Retracted doc should score the same as non-retracted (model has no flag yet)."""
    score = compute_completeness_score(retracted_doc)
    # Has: doi(+2), abstract>20(+2), venue(+1), authors(+1), year(+1), not retracted(+1) = 8
    assert score == 8


def test_short_abstract_no_score(doc_short_abstract):
    """Abstract <= 20 chars should not contribute."""
    score = compute_completeness_score(doc_short_abstract)
    # Has: doi(+2), authors(+1), year(+1), not retracted(+1) = 5
    assert score == 5


def test_no_doi_no_score(doc_no_doi):
    """Missing DOI should not contribute."""
    score = compute_completeness_score(doc_no_doi)
    # Has: venue(+1), authors(+1), year(+1), not retracted(+1) = 4
    assert score == 4


def test_no_authors_no_score(doc_no_authors):
    """Missing authors should not contribute."""
    score = compute_completeness_score(doc_no_authors)
    # Has: doi(+2), year(+1), not retracted(+1) = 4
    assert score == 4


def test_orcid_contributes(doc_with_orcid):
    """Author ORCID should contribute +1."""
    score = compute_completeness_score(doc_with_orcid)
    # Has: authors(+1), year(+1), orcid(+1), not retracted(+1) = 4
    assert score == 4


def test_citations_contribute(doc_with_citations):
    """Citations > 0 should contribute +1."""
    score = compute_completeness_score(doc_with_citations)
    # Has: year(+1), citations(+1), not retracted(+1) = 3
    assert score == 3


def test_zero_citations_no_score():
    """Citations == 0 should not contribute."""
    doc = Document(title="Zero Cites", citations_count=0, year=2020)
    score = compute_completeness_score(doc)
    # Has: year(+1), not retracted(+1) = 2
    assert score == 2


# ---------------------------------------------------------------------------
# Tests: compute_total_score
# ---------------------------------------------------------------------------


def test_total_score_adds_provider_weight(full_doc):
    """Total score = completeness + provider weight."""
    total = compute_total_score(full_doc)
    completeness = compute_completeness_score(full_doc)
    assert total == completeness + PROVIDER_WEIGHTS["openalex"]


def test_total_score_case_insensitive_provider():
    """Provider weight lookup should be case-insensitive."""
    doc = Document(title="Test", provider="OpenAlex", year=2020)
    total = compute_total_score(doc)
    assert total == compute_completeness_score(doc) + 5


def test_total_score_unknown_provider():
    """Unknown provider should return 0 weight."""
    doc = Document(title="Test", provider="unknown", year=2020)
    total = compute_total_score(doc)
    assert total == compute_completeness_score(doc) + 0


def test_total_score_arxiv_weight():
    """arxiv provider should add weight 2."""
    doc = Document(title="Test", provider="arxiv", year=2020)
    total = compute_total_score(doc)
    assert total == compute_completeness_score(doc) + 2


def test_total_score_crossref_weight():
    """crossref provider should add weight 4."""
    doc = Document(title="Test", provider="crossref", year=2020)
    total = compute_total_score(doc)
    assert total == compute_completeness_score(doc) + 4


def test_total_score_semanticscholar_weight():
    """semanticscholar provider should add weight 3."""
    doc = Document(title="Test", provider="semanticscholar", year=2020)
    total = compute_total_score(doc)
    assert total == compute_completeness_score(doc) + 3


def test_total_score_empty_doc():
    """Empty doc total = 1 (base) + 0 (unknown provider)."""
    doc = Document(title="Empty")
    assert compute_total_score(doc) == 1
