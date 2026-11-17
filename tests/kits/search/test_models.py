from datetime import UTC

from scholar_search.models import Author, Document, DocumentCluster, ExternalIds, Query


def test_external_ids_normalization():
    cases = [
        ("https://doi.org/10.1000/182", "10.1000/182"),
        ("http://doi.org/10.1000/182", "10.1000/182"),
        ("DOI:10.1000/182", "10.1000/182"),
        ("doi: 10.1000/182", "10.1000/182"),
        ("10.1000/182", "10.1000/182"),
        ("HTTPS://DOI.ORG/10.1000/ABC", "10.1000/abc"),
    ]
    for raw, expected in cases:
        ids = ExternalIds(doi=raw)
        assert ids.doi == expected


def test_author_properties():
    a1 = Author(family_name="Turing", given_name="Alan")
    assert a1.full_name == "Alan Turing"

    a2 = Author(family_name="Euclid")
    assert a2.full_name == "Euclid"


def test_document_defaults_and_retrieval():
    doc = Document(title="Computing Machinery and Intelligence", year=1950)
    assert doc.external_ids is not None
    assert doc.authors == []
    assert doc.retrieved_at is None

    doc.mark_retrieved()
    assert doc.retrieved_at is not None
    assert doc.retrieved_at.tzinfo == UTC


def test_query_model():
    q = Query(
        id="Q01",
        text='"deep learning" AND robotics',
        year_min=2020,
        year_max=2024,
        max_results=100,
    )
    assert q.id == "Q01"
    assert q.year_min == 2020
    assert q.year_max == 2024
    assert q.max_results == 100


def test_document_cluster():
    d1 = Document(
        "Paper A", external_ids=ExternalIds(doi="10.1/abc"), provider="openalex"
    )
    d2 = Document(
        "Paper A", external_ids=ExternalIds(doi="10.1/abc"), provider="crossref"
    )

    cluster = DocumentCluster(cluster_id=1, representative=d1, members=[d1, d2])

    assert cluster.size == 2
    assert cluster.confidence == 1.0
    assert d1 in cluster.members
    assert d2 in cluster.members


def _saved(doc):
    """A record as the search stages save it (``asdict`` through JSON, ``default=str``)."""
    import json
    from dataclasses import asdict

    return json.dumps(asdict(doc), indent=2, default=str)


def test_document_from_record_gives_the_same_saved_record():
    """M3i: a saved record read back and saved again is the same text, field for field."""
    import json
    from datetime import datetime

    from scholar_search.models import document_from_record

    doc = Document(
        title="Scaling &amp;amp; limits of <i>remote</i> sensing",
        year=2023,
        provider="openalex",
        provider_id="W1",
        external_ids=ExternalIds(doi="10.1000/ABC", arxiv_id="2301.00001", pubmed_id="123", openalex_id="W1"),
        abstract="An abstract with &amp;lt;markup&amp;gt; left in.",
        authors=[Author(family_name="Turing", given_name="Alan", orcid="0000-0001")],
        venue="A venue",
        workspace_id="SCI-000001",
        oa_locations=[{"url": "https://example.invalid/a.pdf"}],
        topics=[{"source": "openalex", "id": "T1", "display_name": "Topic", "score": 0.9}],
        cluster_id=7,
        raw_data={"nested": {"n": 1}},
    )
    doc.sources.append({"provider": "crossref", "id": "c-1"})
    doc.mark_retrieved()
    saved = _saved(doc)

    back = document_from_record(json.loads(saved))

    assert _saved(back) == saved
    assert isinstance(back.retrieved_at, datetime) and back.retrieved_at == doc.retrieved_at
    assert back.external_ids.doi == "10.1000/abc" and back.authors[0].full_name == "Alan Turing"
    # The constructor's clean-up is not applied a second time: the saved title is kept as saved.
    assert back.title == doc.title


def test_document_from_record_ignores_unknown_keys_and_keeps_defaults():
    from scholar_search.models import document_from_record

    back = document_from_record({"title": "Only a title", "not_a_field": 1, "external_ids": {"doi": "10.1/x", "other": "y"}})
    assert back.title == "Only a title" and back.external_ids.doi == "10.1/x"
    assert back.sources == [] and back.authors == [] and back.retrieved_at is None
    assert not hasattr(back, "not_a_field")
