from scholar_search.dedup import Deduplicator
from scholar_search.models import Document, ExternalIds


def test_dedup_metadata_merging():
    doc_openalex = Document(
        title="Attention Is All You Need",
        year=2017,
        provider="openalex",
        external_ids=ExternalIds(
            doi="10.5555/3295222.3295349", openalex_id="W2741809807"
        ),
        url="https://openaccess.thecvf.com/paper.pdf",
        citations_count=60000,
    )
    doc_pubmed = Document(
        title="Attention is all you need.",  # slight title casing/punctuation variation
        year=2017,
        provider="pubmed",
        external_ids=ExternalIds(doi="10.5555/3295222.3295349", pubmed_id="12345678"),
        abstract="We propose a new simple network architecture, the Transformer...",
        mesh_terms=["Neural Networks, Computer", "Artificial Intelligence"],
    )
    doc_s2 = Document(
        title="Attention Is All You Need",
        year=2017,
        provider="semanticscholar",
        external_ids=ExternalIds(
            doi="10.5555/3295222.3295349",
            s2_id="204e3073870fae3d05bcbc2f6a8e263d9b72e776",
        ),
        tldr="The Transformer, a model architecture eschewing recurrence...",
    )

    deduplicator = Deduplicator()
    clusters = deduplicator.deduplicate([doc_openalex, doc_pubmed, doc_s2])

    assert len(clusters) == 1
    rep = clusters[0].representative

    # Verify that representative inherited metadata from all 3 providers
    assert rep.external_ids.doi == "10.5555/3295222.3295349"
    assert rep.external_ids.openalex_id == "W2741809807"
    assert rep.external_ids.pubmed_id == "12345678"
    assert rep.external_ids.s2_id == "204e3073870fae3d05bcbc2f6a8e263d9b72e776"
    assert (
        rep.abstract
        == "We propose a new simple network architecture, the Transformer..."
    )
    assert rep.tldr == "The Transformer, a model architecture eschewing recurrence..."
    assert rep.url == "https://openaccess.thecvf.com/paper.pdf"
    assert rep.citations_count == 60000
    assert "Neural Networks, Computer" in rep.mesh_terms
    assert rep.workspace_id == "SCI-000001"
    assert len(rep.sources) == 3


def test_dedup_fuzzy_matching_with_author_and_year():
    from scholar_search.models import Author

    doc_preprint = Document(
        title="Grounded Language Models for Scientific Discovery",
        year=2023,
        provider="arxiv",
        authors=[Author(family_name="Chen", given_name="Alex")],
        abstract="<jats:p>We introduce a novel grounded RAG architecture.</jats:p>",
    )
    doc_journal = Document(
        title="Grounded Language Models for Scientific Discovery.",
        year=2024,  # +1 year publication delay
        provider="crossref",
        authors=[Author(family_name="Chen", given_name="A.")],
        external_ids=ExternalIds(doi="10.1038/s41586-024-0001"),
    )

    deduplicator = Deduplicator()
    clusters = deduplicator.deduplicate([doc_preprint, doc_journal])

    assert len(clusters) == 1
    rep = clusters[0].representative
    assert rep.workspace_id == "SCI-000001"
    assert rep.external_ids.doi == "10.1038/s41586-024-0001"
    # Abstract should have JATS tags stripped
    assert rep.abstract == "We introduce a novel grounded RAG architecture."
    assert len(rep.sources) == 2


def test_dedup_distinct_papers_not_merged():
    from scholar_search.models import Author

    doc1 = Document(
        title="Deep Learning for Code Generation",
        year=2022,
        provider="arxiv",
        authors=[Author(family_name="Smith")],
    )
    doc2 = Document(
        title="Reinforcement Learning for Code Generation",
        year=2022,
        provider="arxiv",
        authors=[Author(family_name="Smith")],
    )

    deduplicator = Deduplicator()
    clusters = deduplicator.deduplicate([doc1, doc2])

    assert len(clusters) == 2
    assert clusters[0].representative.workspace_id == "SCI-000001"
    assert clusters[1].representative.workspace_id == "SCI-000002"


# ---------------------------------------------------------------------------
# K0 identity-conflict conformance (AC-3 / AC-4, NEGATIVE CASES 1-3)
#
# Narrowness condition of the reviewed relaxation: the ONLY tolerated
# identifier disagreement is the preprint <-> publisher pair (both DOIs
# present, different after normalization, and EXACTLY ONE of them a
# preprint/repository DOI). Every other conflicting non-empty identifier
# blocks the merge.
# ---------------------------------------------------------------------------


def _doc(
    *,
    title="A Stable Title For Identity Checks",
    doi=None,
    arxiv_id=None,
    pubmed_id=None,
    openalex_id=None,
    s2_id=None,
    year=2024,
):
    """Builds a document with a controlled identifier set."""
    from scholar_search.models import Author

    return Document(
        title=title,
        year=year,
        provider="openalex",
        authors=[Author(family_name="Nakamura")],
        external_ids=ExternalIds(
            doi=doi,
            arxiv_id=arxiv_id,
            pubmed_id=pubmed_id,
            openalex_id=openalex_id,
            s2_id=s2_id,
        ),
    )


def test_conflicting_openalex_ids_are_not_merged():
    """NEGATIVE CASE 1: conflicting OpenAlex IDs block the merge.

    Same title, same year, same author — only the OpenAlex ID disagrees.
    A provider-ID disagreement must never be silently merged.
    """
    doc_a = _doc(openalex_id="W100000001")
    doc_b = _doc(openalex_id="W200000002")

    clusters = Deduplicator().deduplicate([doc_a, doc_b])

    assert len(clusters) == 2


def test_conflicting_s2_ids_are_not_merged():
    """NEGATIVE CASE 1: conflicting Semantic Scholar IDs block the merge."""
    doc_a = _doc(s2_id="s2aaaaaaaaaa")
    doc_b = _doc(s2_id="s2bbbbbbbbbb")

    clusters = Deduplicator().deduplicate([doc_a, doc_b])

    assert len(clusters) == 2


def test_conflicting_openalex_ids_with_same_doi_are_not_merged():
    """NEGATIVE CASE 1 on the Tier-1 (DOI) path: the DOI hit is rejected too.

    The DOI tier finds a candidate cluster; the identifier-conflict check
    must veto the merge instead of trusting the shared DOI.
    """
    doc_a = _doc(doi="10.1234/same", openalex_id="W100000001")
    doc_b = _doc(doi="10.1234/same", openalex_id="W200000002")

    clusters = Deduplicator().deduplicate([doc_a, doc_b])

    assert len(clusters) == 2


def test_preprint_doi_merges_with_publisher_counterpart():
    """AC-4: a preprint DOI merges with its publisher counterpart.

    The publisher minted a NEW DOI for the version of record, and OpenAlex /
    S2 assign distinct ids to the two versions, so both the DOI disagreement
    and the provider-id disagreement are expected in exactly this case.
    """
    preprint = _doc(
        doi="10.1101/2024.01.01.123456",
        openalex_id="W111111111",
        s2_id="s2preprint01",
    )
    publisher = _doc(
        doi="10.1234/published-version",
        openalex_id="W222222222",
        s2_id="s2publisher01",
    )

    clusters = Deduplicator().deduplicate([preprint, publisher])

    assert len(clusters) == 1


def test_two_different_non_preprint_dois_still_conflict():
    """NEGATIVE CASE 2: the preprint allowance is not a general DOI bypass."""
    doc_a = _doc(doi="10.1234/publisher-a")
    doc_b = _doc(doi="10.5678/publisher-b")

    clusters = Deduplicator().deduplicate([doc_a, doc_b])

    assert len(clusters) == 2


def test_two_different_preprint_dois_still_conflict():
    """NEGATIVE CASE 2: two different preprint/repository DOIs still conflict.

    The allowance requires EXACTLY ONE preprint DOI; two preprints are two
    different works.
    """
    doc_a = _doc(doi="10.1101/2024.01.01.111111")
    doc_b = _doc(doi="10.1101/2024.01.01.222222")

    clusters = Deduplicator().deduplicate([doc_a, doc_b])

    assert len(clusters) == 2


def test_missing_identifier_stays_compatible():
    """NEGATIVE CASE 3: a missing identifier remains compatible.

    A record with a DOI and a record with only an arXiv ID stay
    merge-eligible; a missing identifier is not a conflict.
    """
    doc_doi = _doc(doi="10.1234/has-doi")
    doc_arxiv = _doc(arxiv_id="2401.00001")

    clusters = Deduplicator().deduplicate([doc_doi, doc_arxiv])

    assert len(clusters) == 1


def test_provider_id_conflict_is_tolerated_only_for_preprint_publisher_pair():
    """AC-3(b) narrowness proof: the relaxation is limited to one case.

    (a) A provider-ID conflict IS tolerated for a preprint <-> publisher pair.
    (b) The SAME conflict with equal / non-preprint DOIs still blocks the
        merge. Together these two directions prove the relaxation is narrow.
    """
    preprint = _doc(
        doi="10.1101/2024.02.02.222222",
        openalex_id="W333333333",
        s2_id="s2preprint02",
    )
    publisher = _doc(
        doi="10.1234/published-version-2",
        openalex_id="W444444444",
        s2_id="s2publisher02",
    )

    relaxed = Deduplicator().deduplicate([preprint, publisher])
    assert len(relaxed) == 1

    # Same provider-ID conflict, but the DOIs are equal and NOT preprints.
    same_doi_a = _doc(doi="10.1234/identical", openalex_id="W555555555")
    same_doi_b = _doc(doi="10.1234/identical", openalex_id="W666666666")

    blocked = Deduplicator().deduplicate([same_doi_a, same_doi_b])
    assert len(blocked) == 2


def test_doi_conflict_check_normalizes_doi_surface_forms():
    """The DOI comparison is scheme-insensitive (identity, not surface form).

    ``https://doi.org/10.1234/x`` and ``doi:10.1234/x`` are the same DOI and
    must NOT be reported as a conflict; ``10.1234/x`` vs ``10.1234/y`` must.
    """
    doc_a = _doc(doi="https://doi.org/10.1234/Same")
    doc_b = _doc(doi="doi:10.1234/same")

    assert Deduplicator._has_identifier_conflict(doc_a, doc_b) is False

    doc_c = _doc(doi="10.1234/other")
    assert Deduplicator._has_identifier_conflict(doc_a, doc_c) is True
