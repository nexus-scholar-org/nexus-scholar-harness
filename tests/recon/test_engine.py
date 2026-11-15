"""Hermetic tests for ReconEngine.probe (M0.1: T1.1-T1.6)."""

import asyncio
import hashlib
import json
from pathlib import Path

import pytest
from scholar_search.models import Document, ExternalIds, Query

from scholar_harness.recon import DEFAULT_PROVIDERS, ReconEngine, cache_key
from scholar_harness.recon.engine import SATURATION_SCANT, SATURATION_SPARSE


def _repo_root() -> Path:
    current = Path(__file__).resolve().parent
    while True:
        if (current / "pyproject.toml").is_file():
            return current
        current = current.parent


def _fake_docs(n: int, provider: str = "openalex") -> list[Document]:
    return [
        Document(
            title=f"Fake Doc {i}",
            year=2020 + (i % 5),
            provider=provider,
            provider_id=f"W{i:08d}",
            external_ids=ExternalIds(doi=f"10.0000/fake-{i:04d}"),
            abstract=f"abstract number {i} about drones and agriculture",
            citations_count=i * 7,
            url=f"https://example.org/{i}",
        )
        for i in range(n)
    ]


def test_probe_caps_pool_at_25(tmp_path):
    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        assert query.text == "drones & ai"
        assert query.max_results == 40
        assert providers == DEFAULT_PROVIDERS
        return _fake_docs(40)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_file, n = asyncio.run(engine.probe("drones & ai", max_results=40))

    assert n == 25
    assert 10 <= n <= 25
    assert pool_file.exists()
    payload = json.loads(pool_file.read_text(encoding="utf-8"))
    assert len(payload["docs"]) == 25
    assert payload["docs"][0]["provider"] == "openalex"
    assert payload["docs"][0]["id"].startswith("openalex|")
    assert payload["docs"][0]["doi"] == "10.0000/fake-0000"
    assert "fulltexts" in payload


def test_probe_cache_hit_is_idempotent_no_network(tmp_path):
    calls = {"n": 0}

    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        calls["n"] += 1
        return _fake_docs(12)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    p1, n1 = asyncio.run(engine.probe("drones & ai"))
    p2, n2 = asyncio.run(engine.probe("Drones & AI."))

    assert (n1, n2) == (12, 12)
    assert p1 == p2
    assert p1.read_bytes() == p2.read_bytes()
    assert calls["n"] == 1

    key = cache_key("drones & ai", DEFAULT_PROVIDERS, 2000)
    assert json.loads(p1.read_text(encoding="utf-8"))["cache_key"] == key


def test_pool_filename_is_sha1_of_cache_key(tmp_path):
    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=lambda q, p: _fake_docs(8))
    pool_file, n = asyncio.run(engine.probe("drones", providers=["openalex"], year_min=2000))
    key = cache_key("drones", ["openalex"], 2000)
    assert pool_file.name == f"{hashlib.sha1(key.encode('utf-8')).hexdigest()}_pool.json"
    assert n == 8


def test_corrupt_cache_file_treated_as_miss(tmp_path):
    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        return _fake_docs(5)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_file, _n = asyncio.run(engine.probe("drones"))
    pool_file.write_text("{not json", encoding="utf-8")
    pool_file2, n2 = asyncio.run(engine.probe("drones"))
    assert pool_file2 == pool_file
    assert n2 == 5
    assert json.loads(pool_file.read_text(encoding="utf-8"))["cache_key"]


def test_no_workspaces_guard_raises(tmp_path):
    poisoned = tmp_path / "workspaces" / "inception_recon"
    engine = ReconEngine(cache_root=poisoned, search_fn=lambda q, p: _fake_docs(3))
    with pytest.raises(RuntimeError, match="workspaces"):
        asyncio.run(engine.probe("drones"))
    assert not poisoned.exists()


def test_no_workspaces_guard_is_case_insensitive(tmp_path):
    # win32 Path.resolve() preserves input case for non-existent dirs, so a
    # differently-cased "Workspaces" segment must trip the guard too.
    poisoned = tmp_path / "Workspaces" / "inception_recon"
    engine = ReconEngine(cache_root=poisoned, search_fn=lambda q, p: _fake_docs(3))
    with pytest.raises(RuntimeError, match="workspaces"):
        asyncio.run(engine.probe("drones"))
    assert not (tmp_path / "Workspaces").exists()
    assert list(tmp_path.iterdir()) == []


def test_fake_docs_have_unique_dois():
    dois = [d.external_ids.doi for d in _fake_docs(6)]
    assert len(set(dois)) == 6


# ---------------------------------------------------------------------------
# M0.6 (T6.1/T6.2): semantic mode threading + topics into the pool
# ---------------------------------------------------------------------------


def test_probe_threads_semantic_to_query_and_cache_key(tmp_path):
    captured = {}

    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        captured["semantic"] = query.semantic
        return _fake_docs(5)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    asyncio.run(engine.probe("drones & ai", semantic=True))
    assert captured["semantic"] is True

    pool_sem, _ = asyncio.run(engine.probe("drones & ai", semantic=True))
    key_sem = json.loads(pool_sem.read_text(encoding="utf-8"))["cache_key"]
    assert "/m/semantic/" in key_sem

    # A different text is a cache miss -> search_fn runs again with default False.
    asyncio.run(engine.probe("drones", providers=["openalex"], year_min=2000))
    assert captured["semantic"] is False


def test_semantic_and_keyword_probes_use_distinct_cache_addresses(tmp_path):
    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        return _fake_docs(5)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_kw, _ = asyncio.run(engine.probe("drones & ai", semantic=False))
    pool_sem, _ = asyncio.run(engine.probe("drones & ai", semantic=True))

    kw_key = json.loads(pool_kw.read_text(encoding="utf-8"))["cache_key"]
    sem_key = json.loads(pool_sem.read_text(encoding="utf-8"))["cache_key"]
    assert kw_key != sem_key
    assert "/m/semantic/" not in kw_key
    assert pool_kw != pool_sem
    kw = cache_key("drones & ai", DEFAULT_PROVIDERS, 2000)
    assert kw_key == kw


def test_pool_entry_carries_topics_only_when_present(tmp_path):
    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        docs = _fake_docs(2)
        docs[0].topics = [
            {"source": "openalex_topics", "id": "T1", "display_name": "Computer vision", "score": 0.8}
        ]
        return docs

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_file, _n = asyncio.run(engine.probe("drones"))
    payload = json.loads(pool_file.read_text(encoding="utf-8"))
    by_doi = {d["doi"]: d for d in payload["docs"]}
    assert by_doi["10.0000/fake-0000"]["topics"] == [
        {"source": "openalex_topics", "id": "T1", "display_name": "Computer vision", "score": 0.8}
    ]
    assert "topics" not in by_doi["10.0000/fake-0001"]


# ---------------------------------------------------------------------------
# M0.7 (T7.3/T7.7): corpus saturation seam + canonical recon root
# ---------------------------------------------------------------------------


def test_saturation_label_boundaries():
    assert SATURATION_SCANT == 50
    assert SATURATION_SPARSE == 500
    assert ReconEngine.saturation_label(-1) == "unknown"
    assert ReconEngine.saturation_label(0) == "scant"
    assert ReconEngine.saturation_label(49) == "scant"
    assert ReconEngine.saturation_label(50) == "sparse"
    assert ReconEngine.saturation_label(500) == "sparse"
    assert ReconEngine.saturation_label(501) == "dense"
    assert ReconEngine.saturation_label(12345) == "dense"


def test_corpus_count_returns_minus_one_with_injected_search_fn(tmp_path):
    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=lambda q, p: [])
    assert asyncio.run(engine.corpus_count("edge inference")) == -1


def test_corpus_count_requires_openalex_in_scope(tmp_path):
    engine = ReconEngine(cache_root=tmp_path / "cache")
    assert asyncio.run(
        engine.corpus_count("edge inference", providers=["arxiv"])
    ) == -1


def test_corpus_count_openalex_meta_count(tmp_path, monkeypatch):
    import scholar_harness.recon.engine as eng

    captured = {}

    class FakeOpenAlex:
        base_url = "https://api.openalex.org/works"

        def __init__(self):
            self.client = self

        async def get(self, url, params=None):
            captured["url"] = url
            captured["params"] = params

            class _Resp:
                def json(self):
                    return {"meta": {"count": 1200}}

            return _Resp()

        async def close(self):
            captured["closed"] = True

    monkeypatch.setattr(eng, "OpenAlexProvider", FakeOpenAlex)
    monkeypatch.setattr(eng.settings, "mailto", "researcher@example.invalid")
    engine = eng.ReconEngine(cache_root=tmp_path / "cache")
    assert asyncio.run(
        engine.corpus_count("grape disease detection", year_min=2019, year_max=2021)
    ) == 1200
    assert captured["url"] == FakeOpenAlex.base_url
    params = captured["params"]
    assert params["search"] == "grape disease detection"
    assert params["per-page"] == 1
    assert "from_publication_date:2019-01-01" in params["filter"]
    assert "to_publication_date:2021-12-31" in params["filter"]
    # The per-call provider async client is always released (no leak in the
    # long-lived MCP server even on the happy path).
    assert captured["closed"] is True


def test_corpus_count_without_a_contact_address_sends_nothing(tmp_path, monkeypatch):
    """M3a: no live request without SCHOLAR_MAILTO; the count is unknown (-1)."""
    import scholar_harness.recon.engine as eng

    class NoCall:
        def __init__(self):
            raise AssertionError("no provider may be built without a contact address")

    monkeypatch.setattr(eng, "OpenAlexProvider", NoCall)
    monkeypatch.setattr(eng.settings, "mailto", None)
    engine = eng.ReconEngine(cache_root=tmp_path / "cache")
    assert asyncio.run(engine.corpus_count("grape disease detection")) == -1


def test_corpus_count_failure_returns_minus_one(tmp_path, monkeypatch):
    import scholar_harness.recon.engine as eng

    class BrokenOpenAlex:
        base_url = "https://api.openalex.org/works"

        def __init__(self):
            self.client = self

        async def get(self, url, params=None):
            raise RuntimeError("boom")

        async def close(self):
            pass

    monkeypatch.setattr(eng, "OpenAlexProvider", BrokenOpenAlex)
    monkeypatch.setattr(eng.settings, "mailto", "researcher@example.invalid")
    engine = eng.ReconEngine(cache_root=tmp_path / "cache")
    assert asyncio.run(engine.corpus_count("edge inference")) == -1


def test_nexus_recon_root_env_overrides_cache_root(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(tmp_path / "canonical"))
    engine = ReconEngine(cache_root=tmp_path / "ignored" / "cache")
    assert engine.cache_root == (tmp_path / "canonical").resolve()
    assert engine.pools_dir == (tmp_path / "canonical" / "pools").resolve()


def test_nexus_recon_root_unset_keeps_explicit_root(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    engine = ReconEngine(cache_root=tmp_path / "cache")
    assert engine.cache_root == (tmp_path / "cache").resolve()


def test_default_recon_root_is_repo_anchored_not_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    # Launch from an unrelated directory: the default must NOT scatter there.
    monkeypatch.chdir(tmp_path)
    engine = ReconEngine()
    expected = (_repo_root() / ".cache" / "inception_recon").resolve()
    assert engine.cache_root == expected
    assert engine.cache_root.is_absolute()
    assert not str(engine.cache_root).startswith(str(tmp_path.resolve()))


# ---------------------------------------------------------------------------
# M10a OBS-2: the 25 are chosen by each database's own order, in the
# researcher's database order; duplicate representatives are unchanged.
# ---------------------------------------------------------------------------

ORDER = ["openalex", "semanticscholar", "crossref", "arxiv"]
SHARED_DOI = "10.5555/shared-record"


def _ranked_docs(
    name: str, n: int = 25, shared: dict[str, int | tuple[int, ...]] | None = None
) -> list[Document]:
    """``n`` records of one database in its relevance order.

    ``provider_id`` runs against the rank, so an order by id is not the
    database's order. ``shared`` maps a database to the rank (or ranks) that
    carry ``SHARED_DOI``.
    """
    ranks = (shared or {}).get(name, ())
    ranks = ranks if isinstance(ranks, tuple) else (ranks,)
    docs = []
    for i in range(n):
        doi = f"10.5555/{name}-{i:03d}"
        if i in ranks:
            doi = SHARED_DOI
        docs.append(
            Document(
                title=f"{name} paper ranked {i}",
                year=2022,
                provider=name,
                provider_id=f"{24 - i:03d}",
                external_ids=ExternalIds(doi=doi),
                abstract=f"{name} abstract {i}" + (" with more detail" if name == "crossref" else ""),
            )
        )
    return docs


def _fake_provider_classes(shared: dict[str, int | tuple[int, ...]] | None = None) -> dict[str, type]:
    classes = {}
    for name in ORDER:

        class _Fake:
            _name = name

            def __init__(self):
                self.name = self._name
                self.current_leg = None

            async def search(self, query):
                for doc in _ranked_docs(self.name, shared=shared):
                    yield doc

        classes[name] = _Fake
    return classes


def _probe_ids(tmp_path, monkeypatch, providers, shared=None, refresh=False) -> tuple[list[str], dict]:
    import scholar_harness.recon.engine as eng

    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    monkeypatch.setattr(eng, "_PROVIDER_CLASSES", _fake_provider_classes(shared))
    engine = ReconEngine(cache_root=tmp_path / "cache")
    pool, _path, _cached = asyncio.run(engine.probe_pool("weed mapping", providers=providers, refresh=refresh))
    return [d["id"] for d in pool["docs"]], pool


def test_sample_is_filled_by_rank_in_the_chosen_database_order(tmp_path, monkeypatch):
    ids, pool = _probe_ids(tmp_path, monkeypatch, ORDER)
    assert len(ids) == 25
    assert {d["provider"] for d in pool["docs"]} == set(ORDER)
    assert ids[:4] == [f"{name}|024" for name in ORDER]
    assert ids[4:8] == [f"{name}|023" for name in ORDER]
    again, _pool = _probe_ids(tmp_path, monkeypatch, ORDER, refresh=True)
    assert again == ids


def test_reversed_database_order_reverses_the_rank_zero_records(tmp_path, monkeypatch):
    order = list(reversed(ORDER))
    ids, _pool = _probe_ids(tmp_path, monkeypatch, order)
    assert ids[:4] == [f"{name}|024" for name in order]


def test_a_duplicate_appears_once_with_the_usual_representative(tmp_path, monkeypatch):
    from scholar_search.dedup import Deduplicator, stable_order

    shared = {"openalex": 0, "crossref": 3}
    ids, pool = _probe_ids(tmp_path, monkeypatch, ORDER, shared=shared)
    raw = [doc for name in ORDER for doc in _ranked_docs(name, shared=shared)]
    clusters = Deduplicator().deduplicate(stable_order(raw))
    (cluster,) = [c for c in clusters if c.representative.external_ids.doi == SHARED_DOI]
    assert cluster.size == 2
    expected = f"{cluster.representative.provider}|{cluster.representative.provider_id}"
    assert [d["doi"] for d in pool["docs"]].count(SHARED_DOI) == 1
    assert ids[0] == expected


def test_one_database_keeps_its_own_order(tmp_path, monkeypatch):
    ids, _pool = _probe_ids(tmp_path, monkeypatch, ["crossref"])
    assert ids == [f"crossref|{24 - i:03d}" for i in range(25)]


def test_a_duplicate_within_one_database_takes_the_stable_order_representative(tmp_path, monkeypatch):
    """The same DOI at ranks 0 and 5 of one database, with equal scores.

    Arrival order would keep rank 0 (``openalex|024``); ``stable_order`` puts
    ``openalex|019`` first, so that record is the representative. The group
    still sits at rank 0.
    """
    from scholar_search.dedup import Deduplicator, stable_order

    shared = {"openalex": (0, 5)}
    ids, pool = _probe_ids(tmp_path, monkeypatch, ORDER, shared=shared)
    raw = [doc for name in ORDER for doc in _ranked_docs(name, shared=shared)]
    clusters = Deduplicator().deduplicate(stable_order(raw))
    (cluster,) = [c for c in clusters if c.representative.external_ids.doi == SHARED_DOI]
    assert cluster.size == 2
    expected = f"{cluster.representative.provider}|{cluster.representative.provider_id}"
    assert expected == "openalex|019", "the fixture must make arrival order and stable order disagree"
    assert [d["doi"] for d in pool["docs"]].count(SHARED_DOI) == 1
    assert ids[0] == expected


def _old_pool(key: str, providers: list[str]) -> dict:
    """A complete pool as written before M10a: no ``sample`` marker."""
    return {
        "cache_key": key,
        "created_at": "2026-11-01T00:00:00+00:00",
        "status": "complete",
        "query": "weed mapping",
        "providers": providers,
        "year_min": 2000,
        "year_max": None,
        "languages": None,
        "max_results": 25,
        "semantic": False,
        "legs": [],
        "docs": [{"id": "arxiv|old", "provider": "arxiv", "doi": None, "title": "old", "abstract": None,
                  "year": 2020, "citations": 0, "oa_url": None}],
        "fulltexts": {},
    }


@pytest.mark.parametrize("marker", [None, "relevance"], ids=["no-marker", "previous-marker"])
def test_a_pool_cached_before_the_relevance_sample_is_fetched_again(tmp_path, marker):
    """A pool without the current ``sample`` marker, or with an earlier one, is fetched again."""
    from scholar_harness.recon.engine import POOL_SAMPLE

    calls = {"n": 0}

    def search_fn(query: Query, providers: list[str]) -> list[Document]:
        calls["n"] += 1
        return _ranked_docs("crossref", 3) + _ranked_docs("openalex", 3)

    providers = ["openalex", "crossref"]
    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    key = cache_key("weed mapping", providers, 2000)
    pool_path = engine.pools_dir / f"{hashlib.sha1(key.encode('utf-8')).hexdigest()}_pool.json"
    pool_path.parent.mkdir(parents=True)
    old = _old_pool(key, providers)
    if marker is not None:
        old["sample"] = marker
    pool_path.write_text(json.dumps(old), encoding="utf-8")

    pool, path, cached = asyncio.run(engine.probe_pool("weed mapping", providers=providers))
    assert (cached, calls["n"], path) == (False, 1, pool_path)
    assert pool["sample"] == POOL_SAMPLE != marker
    assert [d["id"] for d in pool["docs"]] == [
        "openalex|024", "crossref|024", "openalex|023", "crossref|023", "openalex|022", "crossref|022"
    ]
    assert json.loads(pool_path.read_text(encoding="utf-8")) == pool, "the old pool is overwritten"

    again, _path, cached = asyncio.run(engine.probe_pool("weed mapping", providers=providers))
    assert (cached, calls["n"]) == (True, 1), "a pool with the marker is reused"
    assert again == pool


def _blocks() -> list[Document]:
    """Three listed databases and one unlisted (``core``), in blocks, not in the requested order.

    ``SHARED_DOI`` is crossref rank 0 and openalex rank 1.
    """
    shared = {"crossref": 0, "openalex": 1}
    return (
        _ranked_docs("crossref", 3, shared=shared)
        + _ranked_docs("core", 2)
        + _ranked_docs("openalex", 3, shared=shared)
        + _ranked_docs("semanticscholar", 1)
    )


@pytest.mark.parametrize("as_run", [True, False], ids=["search-run", "bare-list"])
def test_an_injected_search_is_put_in_rank_order_without_merging(tmp_path, as_run):
    from scholar_search.models import SearchRun

    def search_fn(query: Query, providers: list[str]):
        return SearchRun(documents=_blocks(), legs=[]) if as_run else _blocks()

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool, _path, _cached = asyncio.run(
        engine.probe_pool("weed mapping", providers=["openalex", "semanticscholar", "crossref"])
    )
    assert [d["id"] for d in pool["docs"]] == [
        "openalex|024", "semanticscholar|024", "crossref|024", "core|024",
        "openalex|023", "crossref|023", "core|023",
        "openalex|022", "crossref|022",
    ]
    assert [d["doi"] for d in pool["docs"]].count(SHARED_DOI) == 2, "this path does not merge duplicates"
