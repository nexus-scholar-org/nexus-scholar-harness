"""M3a-discovery D6 / CORE-07: a search run builds the corpus snapshot (Packet B).

Before M3a no runtime path from ``run`` called ``build_corpus_snapshot_artifact``,
so ``cmd_prepare`` exited with "No artifact registry found" on every fresh run
and screening was unreachable without a manual ``accept-corpus``. The run now
accepts the snapshot after verification, so screening batches are prepared in
the same run. A re-run on an accepted corpus does not search again.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import discovery as disc
from scholar_harness.pipeline import verification as ver_mod

from test_verification_identity_policy import (
    _install_fake_engine,
    _install_passthrough_hydration,
    _journal_rows,
    _make_two_distinct_docs,
    _write_protocol,
)


class _PassthroughVerifier:
    async def process_batch(self, docs, verify=True, enrich=True):
        return list(docs), []


def _workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws-core07", "title": "T", "stats": {},
                    "registered_workspace_id": "WSP-0123456789abcdef0123456789abcdef"}),
        encoding="utf-8",
    )
    _write_protocol(ws)
    return ws


def _registry(ws: Path) -> dict:
    return json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))


def test_a_fresh_run_builds_the_snapshot_and_prepares_screening(tmp_path, monkeypatch):
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)
    ws = _workspace(tmp_path)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    corpora = [e for e in _registry(ws)["artifacts"].values() if e["artifact_type"] == "corpus_snapshot"]
    assert len(corpora) == 1
    assert results["stages"]["corpus_snapshot"]["status"] == "ACCEPTED"
    assert results["stages"]["corpus_snapshot"]["study_count"] == 2
    assert results["status"] == "PENDING_AGENT_REVIEW"
    assert results["stages"]["screening"]["batch_files_prepared"] == 1
    assert list((ws / "literature" / "screening").glob("batch_001.json"))


def test_a_rerun_on_an_accepted_corpus_does_not_search_again(tmp_path, monkeypatch):
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)
    ws = _workspace(tmp_path)
    asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    batch = (ws / "literature" / "screening" / "batch_001.json").read_bytes()

    class _MustNotSearch:
        def __init__(self, providers=None):
            raise AssertionError("discovery re-ran on an accepted corpus")

    monkeypatch.setattr(disc, "SearchEngine", _MustNotSearch)
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["discovery"]["status"] == "SKIPPED"
    assert "CORPUS_ALREADY_ACCEPTED" in results["discovery"]["reason"]
    # Screening batches are kept, not reshuffled.
    assert (ws / "literature" / "screening" / "batch_001.json").read_bytes() == batch
    assert len([e for e in _registry(ws)["artifacts"].values() if e["artifact_type"] == "corpus_snapshot"]) == 1


def test_a_refused_snapshot_aborts_the_run_with_a_journal_row(tmp_path, monkeypatch):
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)
    ws = _workspace(tmp_path)
    (ws / "project.json").write_text("{not json", encoding="utf-8")

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["status"] == "FAILED"
    assert results["stages"]["corpus_snapshot"]["status"] == "REFUSED"
    aborted = [r for r in _journal_rows(ws) if r.get("action") == "PIPELINE_RUN_ABORTED"]
    assert aborted and "corpus snapshot" in aborted[-1]["description"].lower()
