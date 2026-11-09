"""The recon session store shared by the CLI wizard, the MCP tools and the console (M4c).

Hermetic: probes go through an injected ``search_fn``; the MAILTO_NOT_SET case
builds the real M3a ``SearchEngine``, which refuses before any request.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from scholar_search.config import settings
from scholar_search.models import Document, ExternalIds, Query, SearchLeg, SearchRun

from scholar_harness.recon.session import (
    MAILTO_NOT_SET,
    POOL_EMPTY_REFUSED,
    PROVIDERS_FAILED,
    ReconRefused,
    ReconSessions,
    pool_fingerprint,
    refuse_unusable_pool,
    term_evidence,
    term_occurs,
)

TOPIC = "grape disease detection"


def _doc(i: int, title: str, abstract: str = "") -> Document:
    return Document(
        title=title, year=2023, provider="openalex", provider_id=f"W{i:06d}",
        external_ids=ExternalIds(doi=f"10.1/g{i:03d}"), abstract=abstract, url=f"https://example.org/{i}",
    )


def _pool_docs() -> list[Document]:
    docs = [_doc(i, f"Grape disease detection with drone imagery {i}", "multispectral uav imagery of vineyards") for i in range(8)]
    docs += [_doc(100 + i, f"Lightweight cnn for grape disease detection {i}", "lightweight cnn on edge devices") for i in range(6)]
    return docs


def _search_fn(query: Query, providers: list[str]) -> SearchRun:
    docs = _pool_docs()
    legs = [SearchLeg(provider=p, query_id=query.id, status="ok", fetched=len(docs) if p == providers[0] else 0) for p in providers]
    return SearchRun(documents=docs, legs=legs)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    return ReconSessions(root=tmp_path / "recon", search_fn=_search_fn)


def test_a_probe_records_its_pool_with_fingerprint_created_at_and_legs(store):
    out = asyncio.run(store.probe(TOPIC, topic=TOPIC))
    pool = json.loads(Path(out["pool_path"]).read_text(encoding="utf-8"))
    assert out["fingerprint"] == pool_fingerprint(pool)
    assert out["created_at"] == pool["created_at"]
    assert out["status"] == "complete"
    assert [leg["provider"] for leg in out["legs"]] == ["openalex", "semanticscholar", "crossref", "arxiv"]
    session = store.load(out["session_id"])
    assert session["probes"][-1]["fingerprint"] == out["fingerprint"]
    assert session["pools"][-1] == out["pool_path"]


def test_a_second_probe_is_served_from_the_cache_and_says_so(store):
    first = asyncio.run(store.probe(TOPIC))
    again = asyncio.run(store.probe(TOPIC, session_id=first["session_id"]))
    assert (first["served_from_cache"], again["served_from_cache"]) == (False, True)
    assert again["fingerprint"] == first["fingerprint"]


def test_the_fingerprint_is_canonical():
    assert pool_fingerprint({"b": 1, "a": [1, 2]}) == pool_fingerprint({"a": [1, 2], "b": 1})
    assert pool_fingerprint({"a": 1}).startswith("sha256:")


def test_distill_and_directions_read_the_latest_pool(store):
    sid = asyncio.run(store.probe(TOPIC))["session_id"]
    explore = store.distill(sid)
    assert explore["gates"]["pool"]["n_docs"] == 14
    assert explore["gates"]["pool"]["sufficient"] is True
    assert explore["papers"][0]["directions_anchored"] >= 1
    found = store.directions(sid)
    assert found["directions"], "two families each in >= 2 papers"
    for d in found["directions"]:
        assert len(d["anchor_dois"]) >= 2
        assert d["observed_in"] == len(d["anchor_dois"])
        assert d["n_docs"] == 14
    assert found["narrower_left"] == 1


def test_term_occurrence_ignores_case_hyphens_and_needs_whole_words():
    assert term_occurs("weed detection", "On-device WEED-detection pipelines")
    assert not term_occurs("weed detection", "seaweed detections")
    assert not term_occurs("", "anything")
    pool = {"docs": [{"doi": "10.1/a", "title": "Weed detection"}, {"doi": "10.1/b", "title": "Birds"}, {"title": "weed detection, no DOI"}]}
    assert term_evidence(pool, "weed detection") == {"hits": 3, "observed_in": 1, "anchor_dois": ["10.1/a"]}


def test_an_unusable_pool_is_refused_with_a_reason():
    with pytest.raises(ReconRefused) as failed:
        refuse_unusable_pool({"n_docs": 0, "legs": [{"provider": "openalex", "status": "failed"}]})
    assert failed.value.code == PROVIDERS_FAILED
    with pytest.raises(ReconRefused) as empty:
        refuse_unusable_pool({"n_docs": 0, "legs": [{"provider": "openalex", "status": "ok"}]})
    assert empty.value.code == POOL_EMPTY_REFUSED
    refuse_unusable_pool({"n_docs": 3, "legs": []})


def test_mailto_not_set_refuses_before_any_request(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "mailto", None)
    store = ReconSessions(root=tmp_path / "recon")  # the real M3a SearchEngine
    with pytest.raises(ReconRefused) as refused:
        asyncio.run(store.probe(TOPIC))
    assert refused.value.code == MAILTO_NOT_SET
    assert "SCHOLAR_MAILTO" in refused.value.message
    assert not (tmp_path / "recon" / "pools").exists()


# --------------------------------------------------------------------------- front doors


def test_the_mcp_tool_uses_the_store_and_reports_legs(tmp_path, monkeypatch):
    from scholar_agent import server

    server._ensure_harness_recon_loaded()
    monkeypatch.setattr(server, "RECON_CACHE_ROOT", tmp_path / "recon")
    monkeypatch.setattr(server, "RECON_SEARCH_FN", _search_fn)
    out = json.loads(server.recon_probe(topic=TOPIC))
    assert out["status"] == "probe_ok"
    assert out["pool_status"] == "complete" and out["created_at"] and out["pool_fingerprint"].startswith("sha256:")
    assert len(out["legs"]) == 4
    store = ReconSessions(root=tmp_path / "recon", search_fn=_search_fn)
    assert store.load(out["session_id"])["probes"][-1]["fingerprint"] == out["pool_fingerprint"]


def test_the_mcp_tool_answers_mailto_not_set_in_its_envelope(tmp_path, monkeypatch):
    from scholar_agent import server

    server._ensure_harness_recon_loaded()
    monkeypatch.setattr(server, "RECON_CACHE_ROOT", tmp_path / "recon")
    monkeypatch.setattr(server, "RECON_SEARCH_FN", None)
    monkeypatch.setattr(settings, "mailto", None)
    out = json.loads(server.recon_probe(topic=TOPIC))
    assert out == {"status": "error", "code": MAILTO_NOT_SET, "message": out["message"], "cache_key": None}


def test_the_cli_wizard_records_its_probe_in_the_same_store(tmp_path, monkeypatch):
    from scholar_harness.inception.grounded import _run_grounded_recon
    from scholar_harness.recon import ReconEngine

    engine = ReconEngine(cache_root=tmp_path / "recon", search_fn=_search_fn)
    ctx = _run_grounded_recon(None, TOPIC, engine, auto_select=True)
    session = ReconSessions(engine=engine).load(ctx["session_id"])
    assert [p["fingerprint"] for p in session["probes"]] == ctx["pool_fingerprints"]
    assert ctx["pool_created_at"] == [p["created_at"] for p in session["probes"]]


def test_the_cli_wizard_exits_with_mailto_not_set(tmp_path, monkeypatch):
    import typer

    from scholar_harness.inception.grounded import _run_grounded_recon
    from scholar_harness.recon import ReconEngine

    monkeypatch.setattr(settings, "mailto", None)
    with pytest.raises(typer.Exit) as stop:
        _run_grounded_recon(None, TOPIC, ReconEngine(cache_root=tmp_path / "recon"), auto_select=True)
    assert "MAILTO_NOT_SET" in str(stop.value)
