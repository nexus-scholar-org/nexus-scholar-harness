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


# --- H-provenance-s2 (2026-11-20): a verifying lookup keeps the record's own databases --


def _crossref_resolving_every_doi():
    """A Crossref that answers every DOI lookup, normalized by the real provider.

    The live harvest of 2026-11-19 showed 61 of 64 works as ``crossref`` in
    ``verified.json``: the DOI lookup's record replaced the harvested one.
    """
    from scholar_search.providers.crossref import CrossrefProvider

    crossref = CrossrefProvider()

    async def get(url, **_kwargs):
        doi = url.rsplit("/works/", 1)[-1]
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"message": {
            "title": ["Weed detection in cereal crops from UAV imagery"],
            "DOI": doi,
            "published-print": {"date-parts": [[2021]]},
            "container-title": ["Remote Sensing"],
            "author": [{"family": "Smith", "given": "Ann"}],
        }}
        return resp

    crossref.client = MagicMock()
    crossref.client.get = get
    openalex = MagicMock()
    openalex.base_url = "https://api.openalex.org/works"
    notfound = MagicMock()
    notfound.status_code = 404
    openalex.client.get = AsyncMock(return_value=notfound)
    return DocumentVerifier(crossref_provider=crossref, openalex_provider=openalex)


def _harvested(provider: str, provider_id: str, **ids) -> Document:
    return Document(
        title="Weed detection in cereal crops from UAV imagery",
        year=2021,
        provider=provider,
        provider_id=provider_id,
        workspace_id="SCI-000007",
        external_ids=ExternalIds(doi="10.3390/rs13010001", **ids),
    )


@pytest.mark.asyncio
async def test_a_doi_lookup_does_not_replace_the_databases_that_found_the_work():
    verifier = _crossref_resolving_every_doi()
    doc = _harvested("openalex", "W42", openalex_id="W42")
    # Deduplication merged a Semantic Scholar copy of the same work.
    doc.sources.append({"provider": "semanticscholar", "id": "abc123"})
    doc.external_ids.s2_id = "abc123"

    ok, out, note = await verifier.verify_document(doc)

    assert ok is True and "Crossref" in note
    assert out.provider == "openalex"
    assert out.provider_id == "W42"
    assert [s["provider"] for s in out.sources] == ["openalex", "semanticscholar"]
    assert out.workspace_id == "SCI-000007"
    assert out.external_ids.openalex_id == "W42" and out.external_ids.s2_id == "abc123"
    # The lookup still fills what the record lacked.
    assert out.venue == "Remote Sensing"
    assert [a.family_name for a in out.authors] == ["Smith"]


@pytest.mark.asyncio
async def test_process_batch_keeps_each_records_provider_and_leaves_the_input_untouched():
    verifier = _crossref_resolving_every_doi()
    docs = [
        _harvested("openalex", "W1", openalex_id="W1"),
        _harvested("semanticscholar", "s2-1", s2_id="s2-1"),
        _harvested("arxiv", "2101.00001", arxiv_id="2101.00001"),
        _harvested("crossref", "10.3390/rs13010001"),
    ]
    processed, audit = await verifier.process_batch(docs, verify=True, enrich=False)

    assert [d.provider for d in processed] == ["openalex", "semanticscholar", "arxiv", "crossref"]
    assert [[s["provider"] for s in d.sources] for d in processed] == [
        ["openalex"], ["semanticscholar"], ["arxiv"], ["crossref"],
    ]
    assert all(d.workspace_id == "SCI-000007" for d in processed)
    assert all(a["code"] == "VERIFIED" for a in audit)
    # The input records are not changed by the verification.
    assert docs[0].venue is None and docs[0].authors == []


@pytest.mark.asyncio
async def test_a_title_match_fills_a_missing_doi_but_never_overwrites_a_different_one():
    from scholar_search.providers.crossref import CrossrefProvider

    resolved = CrossrefProvider()._normalize_document({
        "title": ["Weed detection in cereal crops from UAV imagery"],
        "DOI": "10.9999/resolved",
        "published-print": {"date-parts": [[2021]]},
    })
    crossref = MagicMock()
    crossref.base_url = "https://api.crossref.org/works"
    crossref.validate_reference = AsyncMock(return_value=resolved)
    openalex = MagicMock()
    verifier = DocumentVerifier(crossref_provider=crossref, openalex_provider=openalex)

    no_doi = Document(title="Weed detection in cereal crops from UAV imagery",
                      provider="arxiv", provider_id="2101.00002",
                      external_ids=ExternalIds(arxiv_id="2101.00002"))
    ok, out, _ = await verifier.verify_document(no_doi)
    assert ok is True
    assert out.provider == "arxiv" and [s["provider"] for s in out.sources] == ["arxiv"]
    assert out.external_ids.doi == "10.9999/resolved"  # a canonical DOI is still resolved
    assert out.external_ids.arxiv_id == "2101.00002"
    assert no_doi.external_ids.doi is None


@pytest.mark.asyncio
async def test_an_untitled_probe_takes_the_resolved_title():
    """``recall._title_check`` sends an ``Untitled`` probe and reads the title back."""
    verifier = _crossref_resolving_every_doi()
    probe = Document(title="Untitled", external_ids=ExternalIds(doi="10.3390/rs13010001"))
    ok, out, _ = await verifier.verify_document(probe)
    assert ok is True
    assert out.title == "Weed detection in cereal crops from UAV imagery"


@pytest.mark.asyncio
async def test_a_title_match_with_another_doi_names_it_in_the_note():
    """Review finding 2: the record keeps its DOI, and the conflict stays visible."""
    from scholar_search.providers.crossref import CrossrefProvider

    resolved = CrossrefProvider()._normalize_document({
        "title": ["Weed detection in cereal crops from UAV imagery"], "DOI": "10.9999/other",
    })
    crossref = MagicMock()
    crossref.base_url = "https://api.crossref.org/works"
    unresolved = MagicMock()
    unresolved.status_code = 404
    crossref.client.get = AsyncMock(return_value=unresolved)
    crossref.validate_reference = AsyncMock(return_value=resolved)
    openalex = MagicMock()
    openalex.base_url = "https://api.openalex.org/works"
    openalex.client.get = AsyncMock(return_value=unresolved)
    verifier = DocumentVerifier(crossref_provider=crossref, openalex_provider=openalex)

    doc = _harvested("openalex", "W9", openalex_id="W9")
    doc.external_ids.doi = "10.3390/typo"
    ok, out, note = await verifier.verify_document(doc)
    assert ok is True and out.external_ids.doi == "10.3390/typo"
    assert "10.9999/other differs, the record keeps 10.3390/typo" in note
