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