"""Hermetic tests for ReconEngine.probe (M0.1: T1.1-T1.6)."""

import asyncio
import hashlib
import json

import pytest
from scholar_search.models import Document, ExternalIds, Query

from scholar_harness.recon import DEFAULT_PROVIDERS, ReconEngine, cache_key


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