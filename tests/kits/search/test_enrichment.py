"""Tests for AbstractHydrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from scholar_search.enrichment import AbstractHydrator
from scholar_search.models import Document, ExternalIds


@pytest.fixture
def mock_http_client():
    """Create a mock AcademicHttpClient."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client


@pytest.fixture
def hydrator(mock_http_client):
    """Create AbstractHydrator with mock client."""
    return AbstractHydrator(mock_http_client)


# ---------------------------------------------------------------------------
# _reconstruct_abstract (static method)
# ---------------------------------------------------------------------------


def test_reconstruct_abstract():
    """Test OpenAlex inverted index reconstruction."""
    inverted_index = {
        "machine": [0],
        "learning": [1],
        "is": [2],
        "useful": [3],
        "for": [4],
        "healthcare": [5],
    }

    result = AbstractHydrator._reconstruct_abstract(inverted_index)

    assert result == "machine learning is useful for healthcare"


def test_reconstruct_abstract_empty():
    """Test empty inverted index."""
    result = AbstractHydrator._reconstruct_abstract({})
    assert result == ""


def test_reconstruct_abstract_none():
    """Test None inverted index."""
    result = AbstractHydrator._reconstruct_abstract(None)
    assert result == ""


def test_reconstruct_abstract_single_word():
    """Test single word inverted index."""
    result = AbstractHydrator._reconstruct_abstract({"hello": [0]})
    assert result == "hello"


def test_reconstruct_abstract_disordered_positions():
    """Test positions not given in sorted order."""
    inverted_index = {
        "world": [3],
        "hello": [0],
        "foo": [2],
        "bar": [1],
    }
    result = AbstractHydrator._reconstruct_abstract(inverted_index)
    assert result == "hello bar foo world"


# ---------------------------------------------------------------------------
# _hydrate_from_s2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hydrate_from_s2_empty_dois(hydrator):
    """Test S2 hydration with no DOIs returns empty."""
    result = await hydrator._hydrate_from_s2([])
    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_s2_success(hydrator, mock_http_client):
    """Test successful S2 hydration extracts abstract by DOI."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "paperId": "abc123",
            "abstract": "A test abstract",
            "externalIds": {"DOI": "10.1234/test"},
        }
    ]
    mock_http_client.post.return_value = mock_response

    result = await hydrator._hydrate_from_s2(["10.1234/test"])

    assert "10.1234/test" in result
    assert result["10.1234/test"] == "A test abstract"


@pytest.mark.asyncio
async def test_hydrate_from_s2_no_abstract(hydrator, mock_http_client):
    """Test S2 returns paper without abstract."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "paperId": "abc123",
            "abstract": None,
            "externalIds": {"DOI": "10.1234/test"},
        }
    ]
    mock_http_client.post.return_value = mock_response

    result = await hydrator._hydrate_from_s2(["10.1234/test"])

    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_s2_no_doi_in_response(hydrator, mock_http_client):
    """Test S2 returns paper without DOI in externalIds."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "paperId": "abc123",
            "abstract": "An abstract",
            "externalIds": {},
        }
    ]
    mock_http_client.post.return_value = mock_response

    result = await hydrator._hydrate_from_s2(["10.1234/test"])

    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_s2_http_error(hydrator, mock_http_client):
    """Test S2 hydration returns empty on HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_http_client.post.return_value = mock_response

    result = await hydrator._hydrate_from_s2(["10.1234/test"])

    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_s2_exception(hydrator, mock_http_client):
    """Test S2 hydration returns empty on exception."""
    mock_http_client.post.side_effect = Exception("network error")

    result = await hydrator._hydrate_from_s2(["10.1234/test"])

    assert result == {}


# ---------------------------------------------------------------------------
# _hydrate_from_openalex
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hydrate_from_openalex_empty_dois(hydrator):
    """Test OpenAlex hydration with no DOIs returns empty."""
    result = await hydrator._hydrate_from_openalex([])
    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_openalex_success(hydrator, mock_http_client):
    """OpenAlex hydration keys the abstract map by the ECHOED, normalized DOI.

    K0 AC-2 / NEGATIVE CASE 5: the map is keyed by the DOI the OpenAlex work
    echoes (``work["ids"]["doi"]``), normalized (scheme stripped, lower-cased).
    A work is never credited to a DOI it did not echo.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "ids": {"doi": "https://doi.org/10.1234/test"},
                "abstract_inverted_index": {
                    "test": [0],
                    "abstract": [1],
                },
            }
        ]
    }
    mock_http_client.get.return_value = mock_response

    result = await hydrator._hydrate_from_openalex(["10.1234/test"])

    # The key is the ECHOED DOI, normalized to the bare lower-case form.
    assert "10.1234/test" in result
    assert result["10.1234/test"] == "test abstract"


@pytest.mark.asyncio
async def test_hydrate_from_openalex_response_without_echoed_doi_credits_nothing(
    hydrator, mock_http_client
):
    """NEGATIVE CONTROL for the echoed-DOI assertion above.

    Mutation: the mocked OpenAlex work omits ``ids``. The repaired assertion
    in ``test_hydrate_from_openalex_success`` must FAIL against this mutant:
    without an echoed DOI there is nothing to key the map on, so no abstract
    may be attributed to the requested DOI.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "abstract_inverted_index": {
                    "test": [0],
                    "abstract": [1],
                }
            }
        ]
    }
    mock_http_client.get.return_value = mock_response

    result = await hydrator._hydrate_from_openalex(["10.1234/test"])

    assert result == {}
    assert "10.1234/test" not in result


@pytest.mark.asyncio
async def test_hydrate_from_openalex_unmatched_echoed_doi_is_not_credited(
    hydrator, mock_http_client
):
    """K0 NEGATIVE CASE 5: a work that echoes a DIFFERENT DOI is not credited.

    The unmatched work is recorded under its own echoed DOI (i.e. it stays
    unmatched); it is never attributed to the requested DOI.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "ids": {"doi": "https://doi.org/10.9999/other"},
                "abstract_inverted_index": {
                    "other": [0],
                    "abstract": [1],
                },
            }
        ]
    }
    mock_http_client.get.return_value = mock_response

    result = await hydrator._hydrate_from_openalex(["10.1234/test"])

    assert "10.1234/test" not in result
    assert result == {"10.9999/other": "other abstract"}


@pytest.mark.asyncio
async def test_hydrate_from_openalex_no_results(hydrator, mock_http_client):
    """Test OpenAlex hydration with empty results list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_http_client.get.return_value = mock_response

    result = await hydrator._hydrate_from_openalex(["10.1234/test"])

    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_openalex_no_inverted_index(hydrator, mock_http_client):
    """Test OpenAlex result without abstract_inverted_index."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [{"title": "Some work"}]}
    mock_http_client.get.return_value = mock_response

    result = await hydrator._hydrate_from_openalex(["10.1234/test"])

    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_openalex_http_error(hydrator, mock_http_client):
    """Test OpenAlex hydration skips on HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_http_client.get.return_value = mock_response

    result = await hydrator._hydrate_from_openalex(["10.1234/test"])

    assert result == {}


@pytest.mark.asyncio
async def test_hydrate_from_openalex_exception(hydrator, mock_http_client):
    """Test OpenAlex hydration skips on exception."""
    mock_http_client.get.side_effect = Exception("connection error")

    result = await hydrator._hydrate_from_openalex(["10.1234/test"])

    assert result == {}


# ---------------------------------------------------------------------------
# hydrate_missing_abstracts (integration of S2 + OpenAlex)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_empty(hydrator):
    """Test hydration with empty document list."""
    result, stats = await hydrator.hydrate_missing_abstracts([])

    assert result == []
    assert stats["hydrated"] == 0
    assert stats["attempted"] == 0


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_all_have_abstract(hydrator):
    """Test hydration when all documents already have abstracts."""
    doc = Document(
        title="Already has abstract",
        abstract="I already exist",
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    result, stats = await hydrator.hydrate_missing_abstracts([doc])

    assert stats["attempted"] == 0
    assert stats["hydrated"] == 0
    assert doc.abstract == "I already exist"


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_no_doi(hydrator):
    """Test hydration for documents without DOIs (cannot be looked up)."""
    doc = Document(title="No DOI", abstract=None)

    result, stats = await hydrator.hydrate_missing_abstracts([doc])

    assert stats["attempted"] == 0
    assert doc.abstract is None


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_s2_success(hydrator, mock_http_client):
    """Test full pipeline: S2 returns abstract, no OpenAlex fallback needed."""
    doc = Document(
        title="Needs abstract",
        abstract=None,
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "paperId": "abc",
            "abstract": "Hydrated from S2",
            "externalIds": {"DOI": "10.1234/test"},
        }
    ]
    mock_http_client.post.return_value = mock_response

    result, stats = await hydrator.hydrate_missing_abstracts([doc])

    assert stats["hydrated"] == 1
    assert stats["failed"] == 0
    assert doc.abstract == "Hydrated from S2"


@pytest.mark.asyncio
async def test_hydrate_from_openalex_sends_api_key_when_configured(
    hydrator, mock_http_client, monkeypatch
):
    """The OpenAlex leg is key-authenticated when a key is configured.

    The key is passed as the ``api_key`` request parameter (never logged, never
    asserted in the response); without a key the parameter is absent.
    """
    from scholar_search.config import settings

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_http_client.get.return_value = mock_response

    monkeypatch.setattr(settings, "openalex_key", None)
    await hydrator._hydrate_from_openalex(["10.1234/test"])
    assert "api_key" not in mock_http_client.get.await_args.kwargs["params"]

    monkeypatch.setattr(settings, "openalex_key", "configured-key")
    await hydrator._hydrate_from_openalex(["10.1234/test"])
    assert (
        mock_http_client.get.await_args.kwargs["params"]["api_key"] == "configured-key"
    )


@pytest.mark.asyncio
async def test_hydrate_from_openalex_batches_at_most_fifty_dois(
    hydrator, mock_http_client
):
    """The OpenAlex leg pipe-batches at most 50 DOIs per request."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_http_client.get.return_value = mock_response

    dois = [f"10.1234/work{index}" for index in range(120)]
    await hydrator._hydrate_from_openalex(dois)

    assert mock_http_client.get.await_count == 3  # 50 + 50 + 20
    first_filter = mock_http_client.get.await_args_list[0].kwargs["params"]["filter"]
    assert first_filter.count("|") == 49  # 50 DOIs joined by "|"
    assert first_filter.startswith("doi:https://doi.org/10.1234/work0")


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_openalex_first_then_s2_for_remainder(
    hydrator, mock_http_client
):
    """K0 AC-2 (reframed): OpenAlex FIRST, Semantic Scholar SECOND.

    Former intent of ``test_hydrate_missing_abstracts_fallback_to_openalex``
    ("S2 misses, OpenAlex fills in") is retained in the second half of this
    test, but the ORDER is now OpenAlex-first: the OpenAlex pipe-batch leg
    runs first and the S2 batch runs second, on the DOIs OpenAlex could not
    recover only.
    """
    doc_oa = Document(
        title="Recovered by OpenAlex",
        abstract=None,
        external_ids=ExternalIds(doi="10.1234/alpha"),
    )
    doc_s2 = Document(
        title="Recovered by Semantic Scholar",
        abstract=None,
        external_ids=ExternalIds(doi="10.1234/beta"),
    )

    # OpenAlex echoes only the first DOI.
    oa_response = MagicMock()
    oa_response.status_code = 200
    oa_response.json.return_value = {
        "results": [
            {
                "ids": {"doi": "https://doi.org/10.1234/alpha"},
                "abstract_inverted_index": {
                    "openalex": [0],
                    "abstract": [1],
                },
            }
        ]
    }

    # S2 answers only the remainder.
    s2_response = MagicMock()
    s2_response.status_code = 200
    s2_response.json.return_value = [
        {
            "paperId": "p2",
            "abstract": "s2 abstract",
            "externalIds": {"DOI": "10.1234/beta"},
        }
    ]

    mock_http_client.get.return_value = oa_response
    mock_http_client.post.return_value = s2_response

    _, stats = await hydrator.hydrate_missing_abstracts([doc_oa, doc_s2])

    assert stats["attempted"] == 2
    assert stats["hydrated"] == 2
    assert stats["failed"] == 0
    assert doc_oa.abstract == "openalex abstract"
    # Former fallback intent: a DOI OpenAlex could not recover is filled in
    # by the second (S2) leg.
    assert doc_s2.abstract == "s2 abstract"

    # The second leg is consulted for the REMAINDER only.
    s2_ids = mock_http_client.post.await_args.kwargs["json"]["ids"]
    assert s2_ids == ["DOI:10.1234/beta"]


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_openalex_first_precedes_s2(
    hydrator, mock_http_client
):
    """NEGATIVE CONTROL for the OpenAlex-first ordering assertion.

    Both legs can answer for the same DOI. The OpenAlex-first order means the
    OpenAlex abstract is the one applied; with the previous S2-first order the
    S2 abstract would have won, so this assertion fails against that mutant.
    """
    doc = Document(
        title="Both legs can answer",
        abstract=None,
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    oa_response = MagicMock()
    oa_response.status_code = 200
    oa_response.json.return_value = {
        "results": [
            {
                "ids": {"doi": "https://doi.org/10.1234/test"},
                "abstract_inverted_index": {
                    "openalex": [0],
                    "abstract": [1],
                },
            }
        ]
    }
    s2_response = MagicMock()
    s2_response.status_code = 200
    s2_response.json.return_value = [
        {
            "paperId": "p1",
            "abstract": "s2 abstract",
            "externalIds": {"DOI": "10.1234/test"},
        }
    ]

    mock_http_client.get.return_value = oa_response
    mock_http_client.post.return_value = s2_response

    _, stats = await hydrator.hydrate_missing_abstracts([doc])

    assert stats["hydrated"] == 1
    assert doc.abstract == "openalex abstract"
    # OpenAlex answered for every requested DOI -> the S2 leg is not needed.
    mock_http_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_unmatched_openalex_work_not_credited(
    hydrator, mock_http_client
):
    """K0 NEGATIVE CASE 5 at pipeline level: an unmatched work is not credited.

    The OpenAlex work echoes a DOI that was never requested, so the document
    stays un-hydrated and is honestly counted as failed.
    """
    doc = Document(
        title="Needs abstract",
        abstract=None,
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    oa_response = MagicMock()
    oa_response.status_code = 200
    oa_response.json.return_value = {
        "results": [
            {
                "ids": {"doi": "https://doi.org/10.9999/other"},
                "abstract_inverted_index": {
                    "other": [0],
                    "abstract": [1],
                },
            }
        ]
    }
    s2_response = MagicMock()
    s2_response.status_code = 200
    s2_response.json.return_value = []

    mock_http_client.get.return_value = oa_response
    mock_http_client.post.return_value = s2_response

    _, stats = await hydrator.hydrate_missing_abstracts([doc])

    assert stats["hydrated"] == 0
    assert stats["failed"] == 1
    assert doc.abstract is None


@pytest.mark.asyncio
async def test_hydrate_from_s2_rejected_key_retries_unauthenticated_then_degrades(
    hydrator, mock_http_client, monkeypatch
):
    """K0 NEGATIVE CASE 4: a rejected S2 key must not be reported as success.

    Path exercised: the keyed request is rejected with HTTP 403 -> exactly one
    unauthenticated retry -> that retry also fails -> the leg degrades
    honestly to an empty result (no hydration is claimed).
    """
    from scholar_search.config import settings
    from scholar_search.exceptions import ProviderError

    monkeypatch.setattr(settings, "s2_key", "rejected-key")

    mock_http_client.post.side_effect = [
        ProviderError("semanticscholar", "forbidden", status_code=403),
        ProviderError("semanticscholar", "forbidden", status_code=403),
    ]

    result = await hydrator._hydrate_from_s2(["10.1234/test"])

    assert result == {}
    assert mock_http_client.post.await_count == 2

    first_call = mock_http_client.post.await_args_list[0]
    second_call = mock_http_client.post.await_args_list[1]
    # The keyed attempt carried the key ...
    assert first_call.kwargs["headers"] == {"x-api-key": "rejected-key"}
    # ... the single retry did not.
    assert "headers" not in second_call.kwargs


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_s2_rejected_key_is_not_a_success(
    hydrator, mock_http_client, monkeypatch
):
    """K0 NEGATIVE CASE 4 at pipeline level: a rejected key is not a success.

    A failed hydration is not an empty successful result: the document stays
    without an abstract and is counted as failed, never as hydrated.
    """
    from scholar_search.config import settings
    from scholar_search.exceptions import ProviderError

    monkeypatch.setattr(settings, "s2_key", "rejected-key")

    doc = Document(
        title="Needs abstract",
        abstract=None,
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    oa_response = MagicMock()
    oa_response.status_code = 200
    oa_response.json.return_value = {"results": []}

    mock_http_client.get.return_value = oa_response
    mock_http_client.post.side_effect = [
        ProviderError("semanticscholar", "forbidden", status_code=403),
        ProviderError("semanticscholar", "forbidden", status_code=403),
    ]

    _, stats = await hydrator.hydrate_missing_abstracts([doc])

    assert stats["hydrated"] == 0
    assert stats["failed"] == 1
    assert doc.abstract is None


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_both_fail(hydrator, mock_http_client):
    """Test both S2 and OpenAlex fail -> document stays without abstract."""
    doc = Document(
        title="Unhydratable",
        abstract=None,
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    # S2 returns empty
    s2_response = MagicMock()
    s2_response.status_code = 200
    s2_response.json.return_value = []

    # OpenAlex returns no results
    oa_response = MagicMock()
    oa_response.status_code = 200
    oa_response.json.return_value = {"results": []}

    mock_http_client.post.return_value = s2_response
    mock_http_client.get.return_value = oa_response

    result, stats = await hydrator.hydrate_missing_abstracts([doc])

    assert stats["hydrated"] == 0
    assert stats["failed"] == 1
    assert doc.abstract is None


@pytest.mark.asyncio
async def test_hydrate_missing_abstracts_mixed_documents(hydrator, mock_http_client):
    """Test hydration with mix of: already has abstract, no DOI, needs hydration."""
    doc_with_abstract = Document(
        title="Has abstract",
        abstract="Already there",
        external_ids=ExternalIds(doi="10.1111/aaa"),
    )
    doc_no_doi = Document(title="No DOI", abstract=None)
    doc_needs = Document(
        title="Needs it",
        abstract=None,
        external_ids=ExternalIds(doi="10.2222/bbb"),
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "paperId": "p1",
            "abstract": "Looked up abstract",
            "externalIds": {"DOI": "10.2222/bbb"},
        }
    ]
    mock_http_client.post.return_value = mock_response

    result, stats = await hydrator.hydrate_missing_abstracts(
        [doc_with_abstract, doc_no_doi, doc_needs]
    )

    assert stats["attempted"] == 1  # only doc_needs needs hydration
    assert stats["hydrated"] == 1
    assert doc_with_abstract.abstract == "Already there"
    assert doc_no_doi.abstract is None
    assert doc_needs.abstract == "Looked up abstract"
