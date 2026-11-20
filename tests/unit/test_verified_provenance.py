"""H-provenance-s2 (2026-11-20): ``verified.json`` keeps the databases that found each work.

Observed in a live harvest on 2026-11-19 (OpenAlex, Semantic Scholar,
Crossref and arXiv, 20 records each): after deduplication, abstracts and
verification the Hand-off "Provider mix" read Crossref 61 of 64, arXiv 2,
OpenAlex 1 and no Semantic Scholar, and every ``verified.json`` row had one
source. The verifier's Crossref DOI lookup replaced each harvested record.

Every other pipeline test passes verification through a fake verifier; this
one runs the real ``DocumentVerifier`` (with its HTTP answers faked, no
network) between the real deduplicator and ``verified.json``.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from scholar_harness.pipeline import verification as ver_mod
from scholar_harness.pipeline.deduplication import run_deduplication
from scholar_search.models import Document, ExternalIds
from scholar_search.providers.crossref import CrossrefProvider
from scholar_search.verifier import DocumentVerifier

TITLES = {
    "10.1/a": "Weed detection in wheat from UAV imagery",
    "10.1/b": "Drone mapping of grass weeds in barley",
    "10.1/c": "Deep learning for herbicide spot spraying with UAVs",
}


def _verifier() -> DocumentVerifier:
    """Crossref answers every DOI (normalized by the real provider); OpenAlex has nothing."""
    crossref = CrossrefProvider()

    async def get(url, **_kwargs):
        doi = url.rsplit("/works/", 1)[-1]
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"message": {
            "title": [TITLES[doi]], "DOI": doi, "published-print": {"date-parts": [[2022]]},
            "container-title": ["Precision Agriculture"],
        }}
        return resp

    crossref.client = MagicMock()
    crossref.client.get = get
    openalex = MagicMock()
    openalex.base_url = "https://api.openalex.org/works"
    empty = MagicMock()
    empty.status_code = 404
    empty.json.return_value = {}
    openalex.client.get = AsyncMock(return_value=empty)
    return DocumentVerifier(crossref_provider=crossref, openalex_provider=openalex)


def _leg_records() -> list[Document]:
    """Four legs: ``10.1/a`` found by three databases, ``10.1/b`` by two, ``10.1/c`` by one."""
    def doc(provider: str, pid: str, doi: str, **ids) -> Document:
        return Document(title=TITLES[doi], year=2022, provider=provider, provider_id=pid,
                        external_ids=ExternalIds(doi=doi, **ids))

    return [
        doc("openalex", "W1", "10.1/a", openalex_id="W1"),
        doc("openalex", "W2", "10.1/b", openalex_id="W2"),
        doc("semanticscholar", "S1", "10.1/a", s2_id="S1"),
        doc("semanticscholar", "S3", "10.1/c", s2_id="S3"),
        doc("crossref", "10.1/a", "10.1/a"),
        doc("arxiv", "2201.00002", "10.1/b", arxiv_id="2201.00002"),
    ]


def _mix(rows: list[dict]) -> dict[str, int]:
    """Counted as the Hand-off counts it (``console/api/discovery.py::handoff``)."""
    mix: dict[str, int] = {}
    for row in rows:
        for name in {s["provider"] for s in row["sources"]}:
            mix[name] = mix.get(name, 0) + 1
    return mix


def test_verified_json_keeps_every_database_that_found_each_work(tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    legs = _leg_records()
    deduped = run_deduplication(discovered_documents=legs, literature_dir=lit).representatives
    assert len(deduped) == 3

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _verifier)
    outcome = asyncio.run(ver_mod.run_verification(documents=deduped, literature_dir=lit, workspace_dir=ws))

    assert outcome.status == "SUCCESS" and outcome.verified == 3
    # The ids come from deduplication, not from a DOI bridge after a replacement.
    assert outcome.preserved == 3 and outcome.bridge_restored == 0
    rows = json.loads((lit / "verified.json").read_text(encoding="utf-8"))
    by_doi = {row["external_ids"]["doi"]: row for row in rows}
    assert sorted(s["provider"] for s in by_doi["10.1/a"]["sources"]) == ["crossref", "openalex", "semanticscholar"]
    assert sorted(s["provider"] for s in by_doi["10.1/b"]["sources"]) == ["arxiv", "openalex"]
    assert [s["provider"] for s in by_doi["10.1/c"]["sources"]] == ["semanticscholar"]
    assert by_doi["10.1/c"]["provider"] == "semanticscholar"
    assert all(row["venue"] == "Precision Agriculture" for row in rows)  # the lookup still fills

    # Each database's count is what its leg fetched, after duplicates.
    fetched = {}
    for d in legs:
        fetched.setdefault(d.provider, set()).add(d.external_ids.doi)
    assert _mix(rows) == {name: len(dois) for name, dois in fetched.items()}
