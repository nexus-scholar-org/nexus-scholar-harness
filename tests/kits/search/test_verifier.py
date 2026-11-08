from unittest.mock import AsyncMock, MagicMock
import pytest

from scholar_search.models import Document, ExternalIds
from scholar_search.verifier import DocumentVerifier


@pytest.mark.asyncio
async def test_verify_document_by_doi():
    mock_crossref = MagicMock()
    mock_crossref.base_url = "https://api.crossref.org/works"
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "title": ["Attention Is All You Need"],
            "DOI": "10.5555/3295222.3295349",
            "published-print": {"date-parts": [[2017]]},
        }
    }
    mock_crossref.client.get = AsyncMock(return_value=mock_resp)
    mock_crossref._normalize_document.return_value = Document(
        title="Attention Is All You Need",
        year=2017,
        external_ids=ExternalIds(doi="10.5555/3295222.3295349"),
    )

    verifier = DocumentVerifier(
        crossref_provider=mock_crossref, openalex_provider=MagicMock()
    )
    doc = Document(
        title="Attention Is All You Need",
        external_ids=ExternalIds(doi="10.5555/3295222.3295349"),
    )

    verified, res_doc, reason = await verifier.verify_document(doc)
    assert verified is True
    assert "DOI" in reason
    assert res_doc.year == 2017


@pytest.mark.asyncio
async def test_verify_document_hallucination_detection():
    mock_crossref = MagicMock()
    mock_crossref.base_url = "https://api.crossref.org/works"
    mock_crossref.client.get = AsyncMock(side_effect=Exception("Not found"))
    mock_crossref.validate_reference = AsyncMock(return_value=None)

    mock_openalex = MagicMock()
    mock_openalex.base_url = "https://api.openalex.org/works"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": []}
    mock_openalex.client.get = AsyncMock(return_value=mock_resp)

    verifier = DocumentVerifier(
        crossref_provider=mock_crossref, openalex_provider=mock_openalex
    )
    fake_doc = Document(
        title="A Fake Hallucinated Paper On Quantum Banana Peels",
        external_ids=ExternalIds(doi="10.1234/fake.doi"),
    )

    verified, res_doc, reason = await verifier.verify_document(fake_doc)
    assert verified is False
    assert "Unverified" in reason


@pytest.mark.asyncio
async def test_hydrate_metadata():
    mock_openalex = MagicMock()
    mock_openalex.base_url = "https://api.openalex.org/works"
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "id": "W123",
        "title": "Real Paper",
    }
    mock_openalex.client.get = AsyncMock(return_value=mock_resp)
    mock_openalex._normalize_document.return_value = Document(
        title="Real Paper",
        abstract="This is the full abstract recovered from OpenAlex.",
        venue="Nature",
        citations_count=120,
        external_ids=ExternalIds(doi="10.1038/real", openalex_id="W123"),
    )

    verifier = DocumentVerifier(openalex_provider=mock_openalex)
    incomplete_doc = Document(
        title="Real Paper", external_ids=ExternalIds(doi="10.1038/real")
    )

    hydrated = await verifier.hydrate_metadata(incomplete_doc)
    assert hydrated.abstract == "This is the full abstract recovered from OpenAlex."
    assert hydrated.venue == "Nature"
    assert hydrated.citations_count == 120


@pytest.mark.asyncio
async def test_hydrate_metadata_skips_on_title_mismatch():
    """A contaminated DOI (wrong paper title vs OpenAlex record) must NOT enrich."""
    mock_openalex = MagicMock()
    mock_openalex.base_url = "https://api.openalex.org/works"
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": "W456", "title": "Unrelated Paper on Turtles"}
    mock_openalex.client.get = AsyncMock(return_value=mock_resp)
    mock_openalex._normalize_document.return_value = Document(
        title="Unrelated Paper on Turtles",
        abstract="Wrong metadata that must not leak in.",
        venue="Wrong Venue",
        citations_count=999,
        external_ids=ExternalIds(doi="10.1000/wrong", openalex_id="W456"),
    )

    verifier = DocumentVerifier(openalex_provider=mock_openalex)
    record = Document(
        title="Attention Is All You Need",
        external_ids=ExternalIds(doi="10.1000/wrong"),  # contaminated DOI
    )

    hydrated = await verifier.hydrate_metadata(record)
    assert hydrated.abstract is None
    assert hydrated.venue is None
    assert hydrated.citations_count is None


@pytest.mark.asyncio
async def test_hydrate_metadata_allows_positive_match():
    """A genuine DOI whose OpenAlex title matches must still hydrate normally."""
    mock_openalex = MagicMock()
    mock_openalex.base_url = "https://api.openalex.org/works"
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"id": "W789", "title": "Deep Residual Learning for Image Recognition"}
    mock_openalex.client.get = AsyncMock(return_value=mock_resp)
    mock_openalex._normalize_document.return_value = Document(
        title="Deep Residual Learning for Image Recognition",
        abstract="Recovered abstract.",
        venue="arXiv",
        citations_count=100000,
        external_ids=ExternalIds(doi="10.1000/resnet", openalex_id="W789"),
    )

    verifier = DocumentVerifier(openalex_provider=mock_openalex)
    record = Document(
        title="Deep Residual Learning for Image Recognition",
        external_ids=ExternalIds(doi="10.1000/resnet"),
    )

    hydrated = await verifier.hydrate_metadata(record)
    assert hydrated.abstract == "Recovered abstract."
    assert hydrated.venue == "arXiv"



# --- M3a-discovery D4 / SRCH-10: a DOI that resolves to another title -------


def _doi_verifier(resolved_title: str):
    mock_crossref = MagicMock()
    mock_crossref.base_url = "https://api.crossref.org/works"
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"message": {"title": [resolved_title], "DOI": "10.1/x"}}
    mock_crossref.client.get = AsyncMock(return_value=resp)
    mock_crossref._normalize_document.return_value = Document(
        title=resolved_title, year=1999, external_ids=ExternalIds(doi="10.1/x")
    )
    mock_crossref.validate_reference = AsyncMock(return_value=None)
    mock_openalex = MagicMock()
    mock_openalex.base_url = "https://api.openalex.org/works"
    notfound = MagicMock()
    notfound.status_code = 404
    mock_openalex.client.get = AsyncMock(return_value=notfound)
    return DocumentVerifier(crossref_provider=mock_crossref, openalex_provider=mock_openalex)


@pytest.mark.asyncio
async def test_doi_resolving_to_a_different_title_is_a_mismatch_not_verified():
    verifier = _doi_verifier("Unrelated Turtle Migration Paper")
    doc = Document(title="Deep learning for weed detection from UAV imagery",
                   external_ids=ExternalIds(doi="10.1/x"))
    ok, out, note = await verifier.verify_document(doc)
    assert ok is False
    assert note.startswith("DOI_TITLE_MISMATCH")
    assert out is doc
    assert out.title == "Deep learning for weed detection from UAV imagery"


@pytest.mark.asyncio
async def test_process_batch_never_swaps_a_mismatched_record():
    verifier = _doi_verifier("Unrelated Turtle Migration Paper")
    doc = Document(title="Deep learning for weed detection from UAV imagery",
                   year=2022, external_ids=ExternalIds(doi="10.1/x"))
    processed, audit = await verifier.process_batch([doc], verify=True, enrich=True)
    assert processed[0].title == "Deep learning for weed detection from UAV imagery"
    assert processed[0].year == 2022
    assert audit[0]["verified"] is False
    assert audit[0]["code"] == "DOI_TITLE_MISMATCH"


@pytest.mark.asyncio
async def test_doi_with_matching_title_still_verifies():
    verifier = _doi_verifier("Deep Learning for Weed Detection from UAV Imagery")
    doc = Document(title="Deep learning for weed detection from UAV imagery",
                   external_ids=ExternalIds(doi="10.1/x"))
    ok, _, note = await verifier.verify_document(doc)
    assert ok is True and "DOI" in note
