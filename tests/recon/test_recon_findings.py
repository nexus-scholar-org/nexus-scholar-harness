"""INC-09 and INC-21 (docs/assessment/harness-inception-recon-console.md), M4c.

INC-09: a failed or partial probe was cached for ever. A probe now keeps one
leg per provider, never caches a pool that is empty or has a failed leg,
``refresh=True`` probes again, and the grounded context carries each pool's
``created_at``.

INC-21: "anchored" meant only that a provider returned something. A term is now
anchored only on records whose title or abstract contains it; the number of
records the provider returned is kept apart, and APR counts occurrence.

Hermetic: every search goes through an injected ``search_fn``.
"""

from __future__ import annotations

import asyncio
import json

import pytest
import typer
from scholar_search.models import Document, ExternalIds, Query, SearchLeg, SearchRun

from scholar_harness.inception.grounded import _enforce_grounded_anchors, _run_grounded_recon
from scholar_harness.inception.intent import ConceptDraft
from scholar_harness.recon import ReconEngine


def _doc(doi: str, title: str, abstract: str = "") -> Document:
    return Document(
        title=title, year=2023, provider="openalex", provider_id="W" + doi[-6:].replace("/", ""),
        external_ids=ExternalIds(doi=doi), abstract=abstract, url=f"https://example.org/{doi}",
    )


def _docs(n: int) -> list[Document]:
    return [_doc(f"10.1/d{i:03d}", f"Edge inference for weed detection {i}", "embedded vision") for i in range(n)]


def _run(docs: list[Document], legs: list[SearchLeg]) -> SearchRun:
    return SearchRun(documents=docs, legs=legs)


def _leg(provider: str, status: str = "ok", fetched: int = 0, error: str | None = None) -> SearchLeg:
    return SearchLeg(provider=provider, query_id="q", status=status, fetched=fetched, error=error)


# --------------------------------------------------------------------------- INC-09


def test_inc09_an_empty_probe_is_not_cached(tmp_path):
    calls = []

    def search_fn(query: Query, providers: list[str]):
        calls.append(query.text)
        return [] if len(calls) == 1 else _docs(15)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    _path, first = asyncio.run(engine.probe("weed detection"))
    _path, second = asyncio.run(engine.probe("weed detection"))
    assert (first, second) == (0, 15)
    assert len(calls) == 2


def test_inc09_a_failed_leg_is_recorded_and_the_pool_is_not_cached(tmp_path):
    calls = []

    def search_fn(query: Query, providers: list[str]):
        calls.append(query.text)
        legs = [_leg("openalex", "failed", error="HTTPStatusError: 429"), _leg("arxiv", fetched=15)]
        return _run(_docs(15), legs)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    path, n = asyncio.run(engine.probe("weed detection", providers=["openalex", "arxiv"]))
    pool = json.loads(path.read_text(encoding="utf-8"))
    assert n == 15
    assert pool["status"] == "partial"
    assert {leg["provider"]: leg["status"] for leg in pool["legs"]} == {"openalex": "failed", "arxiv": "ok"}
    assert pool["legs"][0]["error"].startswith("HTTPStatusError")
    asyncio.run(engine.probe("weed detection", providers=["openalex", "arxiv"]))
    assert len(calls) == 2, "a partial pool must not be served from the cache"


def test_inc09_refresh_probes_again(tmp_path):
    calls = []

    def search_fn(query: Query, providers: list[str]):
        calls.append(query.text)
        return _docs(15)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    asyncio.run(engine.probe("weed detection"))
    asyncio.run(engine.probe("weed detection"))
    assert len(calls) == 1
    asyncio.run(engine.probe("weed detection", refresh=True))
    assert len(calls) == 2


def test_inc09_grounded_context_carries_each_pool_created_at(tmp_path):
    def search_fn(query: Query, providers: list[str]):
        return [
            _doc(f"10.1/g{i}", f"Grape disease detection study {i}", "grape disease detection in vineyards")
            for i in range(14)
        ]

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    ctx = _run_grounded_recon(None, "grape disease detection", engine, auto_select=True)
    assert len(ctx["pool_created_at"]) == len(ctx["cache_keys"]) == 1
    assert ctx["pool_created_at"][0].startswith("20")


# --------------------------------------------------------------------------- INC-21


def _birds_engine(tmp_path) -> ReconEngine:
    def search_fn(query: Query, providers: list[str]):
        return [_doc("10.9/birds", "Bird migration over the Sahara", "Seasonal routes of passerines.")]

    return ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)


def test_inc21_a_concept_is_not_anchored_on_a_record_that_does_not_contain_it(tmp_path):
    ctx = {"anchored_terms": {}, "cache_keys": [], "pool_sizes": []}
    concepts = [ConceptDraft(concept="quantum error correction", synonyms=[])]
    with pytest.raises(typer.Exit):
        _enforce_grounded_anchors(concepts, ctx, _birds_engine(tmp_path))


def test_inc21_a_synonym_with_hits_but_no_occurrence_is_dropped_and_hits_are_kept_apart(tmp_path):
    ctx = {"anchored_terms": {"quantum error correction": ["10.1/q"]}, "cache_keys": [], "pool_sizes": []}
    draft = ConceptDraft(concept="quantum error correction", synonyms=["surface codes"])
    out = _enforce_grounded_anchors([draft], ctx, _birds_engine(tmp_path))
    assert draft.synonyms == []
    assert "surface codes" not in out["anchored_terms"]
    assert out["term_evidence"]["surface codes"] == {"hits": 1, "observed_in": 0, "anchor_dois": []}


def test_inc21_the_topic_is_anchored_only_where_it_occurs(tmp_path):
    def search_fn(query: Query, providers: list[str]):
        docs = [
            _doc(f"10.1/g{i}", f"Grape disease detection with drones {i}", "grape disease detection")
            for i in range(13)
        ]
        docs.append(_doc("10.9/other", "Vineyard irrigation scheduling", "water balance"))
        return docs

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    ctx = _run_grounded_recon(None, "grape disease detection", engine, auto_select=True)
    assert "10.9/other" not in ctx["anchored_terms"]["grape disease detection"]
    assert ctx["term_evidence"]["grape disease detection"]["hits"] == 14
    assert ctx["term_evidence"]["grape disease detection"]["observed_in"] == 13


def test_inc21_apr_measures_occurrence_not_hits():
    from scholar_harness.recon.gates import compute_apr_observed

    evidence = {
        "weed detection": {"hits": 25, "observed_in": 9, "anchor_dois": ["10.1/a"]},
        "surface codes": {"hits": 1, "observed_in": 0, "anchor_dois": []},
    }
    assert compute_apr_observed(evidence) == 0.5
