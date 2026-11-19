"""Sample curation, engine side (M10b Part C, ``02-explore`` "Sample curation (M10b)").

``effective_pool`` reads a pool without the papers a draft left out and refills
the sample from the records the probe fetched beyond the first 25 (``reserve``).
"""

from __future__ import annotations

import asyncio
import hashlib
import json

from scholar_search.models import Document, ExternalIds, Query

from scholar_harness.recon import ReconEngine, cache_key
from scholar_harness.recon.distiller import distill_pool
from scholar_harness.recon.engine import POOL_MAX, POOL_SAMPLE
from scholar_harness.recon.sample import (
    BELOW_FLOOR,
    MOSTLY_OFF_TOPIC,
    effective_pool,
    exclusions_digest,
    paper_key,
    view,
)
from scholar_harness.recon.session import directions_for


def _entry(i: int, title: str = "", abstract: str = "", doi: bool = True) -> dict:
    return {
        "id": f"openalex|W{i}", "provider": "openalex", "doi": f"10.1/w{i:03d}" if doi else None,
        "title": title or f"Paper {i}", "abstract": abstract, "year": 2023, "citations": 0, "oa_url": None,
    }


def _pool(n_docs: int = 25, n_reserve: int = 5, reserve: bool = True) -> dict:
    pool = {"docs": [_entry(i) for i in range(n_docs)], "legs": [], "query": "q"}
    if reserve:
        pool["reserve"] = [_entry(1000 + i) for i in range(n_reserve)]
    return pool


def test_the_effective_pool_drops_left_out_dois_and_pool_ids_and_refills_from_the_reserve_in_order():
    pool = _pool()
    no_doi = _entry(7, doi=False)
    pool["docs"][7] = no_doi
    left = ["10.1/w003", "openalex|W7"]
    eff = effective_pool(pool, left)
    keys = [paper_key(d) for d in eff["docs"]]
    assert len(keys) == POOL_MAX
    assert "10.1/w003" not in keys and "openalex|W7" not in keys
    assert keys[-2:] == ["10.1/w1000", "10.1/w1001"], "the reserve fills in its order"
    assert [d["added_for"] for d in eff["docs"][-2:]] == ["10.1/w003", "openalex|W7"]
    assert "reserve" not in eff, "no reader counts a reserve paper"
    assert all("added_for" not in d for d in eff["docs"][:-2]), "the sample's own papers carry no mark"


def test_the_effective_pool_never_exceeds_25_and_is_the_pool_itself_without_exclusions():
    pool = _pool(n_reserve=40)
    assert effective_pool(pool, [])["docs"] == pool["docs"]
    assert len(effective_pool(pool, [f"10.1/w{i:03d}" for i in range(10)])["docs"]) == POOL_MAX


def test_without_a_reserve_the_sample_only_gets_smaller():
    pool = _pool(reserve=False)
    eff = effective_pool(pool, ["10.1/w000", "10.1/w001"])
    assert len(eff["docs"]) == 23
    sample = view(pool, {"sample_exclusions": {"items": [{"key": "10.1/w000"}, {"key": "10.1/w001"}]}})
    assert (sample["has_reserve"], sample["reserve_n"], sample["n_docs"], sample["n_docs_raw"]) == (False, 0, 23, 25)


def test_leaving_out_the_only_second_anchor_of_a_direction_removes_it():
    """Reproducing (strict run 2026-11-13): a direction from off-topic papers stays until the researcher can leave one out."""
    docs = [_entry(i, f"Real-time weed detection on embedded hardware {i}", "an on-device inference pipeline for weed detection")
            for i in range(8)]
    docs += [_entry(100 + i, f"Note {w}", f"{w} alone") for i, w in enumerate(["apple", "river", "violin", "granite"])]
    docs += [_entry(200 + i, f"Hyperspectral canopy imaging study {i}", "hyperspectral canopy imaging of fields") for i in range(2)]
    pool = {"docs": docs, "legs": [], "query": "weed detection"}

    def labels(p: dict) -> list[str]:
        return [d["label"] for d in directions_for(distill_pool(p, query_text="weed detection"), p)]

    assert "hyperspectral canopy imaging" in labels(pool)
    assert "hyperspectral canopy imaging" not in labels(effective_pool(pool, ["10.1/w200"]))


def test_the_sample_recommends_another_search_below_the_floor_and_a_new_question_when_mostly_left_out():
    small = _pool(n_docs=14, reserve=False)
    items = [{"key": f"10.1/w{i:03d}"} for i in range(3)]
    below = view(small, {"sample_exclusions": {"items": items}})
    assert below["n_docs"] == 11 and below["recommend"]["reasons"] == [BELOW_FLOOR]
    assert below["recommend"]["reason"] == BELOW_FLOOR and below["recommend"]["search"] is True

    full = _pool(n_reserve=75)
    half = view(full, {"sample_exclusions": {"items": [{"key": f"10.1/w{i:03d}"} for i in range(25)]}})
    # 25 left out, 25 refilled: 25 of the 50 papers that were in the sample.
    assert (half["n_docs"], half["excluded_in_pool"], half["recommend"]["marked_share"]) == (25, 25, 0.5)
    assert half["recommend"]["reasons"] == [MOSTLY_OFF_TOPIC]
    fewer = view(full, {"sample_exclusions": {"items": [{"key": f"10.1/w{i:03d}"} for i in range(24)]}})
    assert fewer["recommend"]["reasons"] == [] and fewer["recommend"]["search"] is False


def test_a_left_out_paper_the_pool_no_longer_holds_is_listed_but_not_counted():
    pool = _pool()
    sample = view(pool, {"sample_exclusions": {"items": [{"key": "10.1/w003"}, {"key": "10.1/old"}]}})
    assert [(e["key"], e["in_pool"]) for e in sample["excluded"]] == [("10.1/w003", True), ("10.1/old", False)]
    assert sample["excluded_in_pool"] == 1


def test_the_exclusions_digest_is_of_the_sorted_keys():
    assert exclusions_digest(["b", "a"]) == exclusions_digest(["a", "b", "a"]) != exclusions_digest([])


def _docs(n: int) -> list[Document]:
    return [
        Document(title=f"Paper {i}", year=2023, provider="openalex", provider_id=f"W{i:04d}",
                 external_ids=ExternalIds(doi=f"10.2/p{i:03d}"), abstract="a", url=f"https://example.org/{i}")
        for i in range(n)
    ]


def test_a_probe_keeps_the_records_beyond_the_sample_as_its_reserve(tmp_path):
    calls = {"n": 0}

    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        calls["n"] += 1
        return _docs(32)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool, _path, cached = asyncio.run(engine.probe_pool("weed mapping", providers=["openalex"]))
    assert (cached, calls["n"]) == (False, 1)
    assert [d["doi"] for d in pool["docs"]] == [f"10.2/p{i:03d}" for i in range(25)]
    assert [d["doi"] for d in pool["reserve"]] == [f"10.2/p{i:03d}" for i in range(25, 32)]
    assert pool["sample"] == POOL_SAMPLE == "relevance-2"


def test_a_pool_cached_before_the_reserve_is_fetched_again_and_gains_one(tmp_path):
    calls = {"n": 0}

    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        calls["n"] += 1
        return _docs(30)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    key = cache_key("weed mapping", ["openalex"], 2000)
    path = engine.pools_dir / f"{hashlib.sha1(key.encode('utf-8')).hexdigest()}_pool.json"
    path.parent.mkdir(parents=True)
    old = {"cache_key": key, "status": "complete", "sample": "relevance-1", "query": "weed mapping",
           "providers": ["openalex"], "legs": [], "docs": [_entry(1)], "fulltexts": {}}
    path.write_text(json.dumps(old), encoding="utf-8")
    pool, _path, cached = asyncio.run(engine.probe_pool("weed mapping", providers=["openalex"]))
    assert (cached, calls["n"], len(pool["reserve"])) == (False, 1, 5)


def test_two_papers_without_a_doi_or_an_id_keep_their_place_when_nothing_is_left_out():
    """Review of Part C, finding 4: such papers share a key; with nothing left out the sample is the pool's own."""
    pool = _pool()
    for i in (3, 4):
        pool["docs"][i] = {**_entry(i, doi=False), "id": "arxiv", "provider": "arxiv"}
    assert effective_pool(pool, [])["docs"] == pool["docs"]
    assert effective_pool(pool, ["10.1/w999"])["docs"] == pool["docs"], "a key the pool does not hold changes nothing"
