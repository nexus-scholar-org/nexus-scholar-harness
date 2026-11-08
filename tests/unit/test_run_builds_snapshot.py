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


# ---------------------------------------------------------------------------
# M3a review findings 2, 4, 6.
# ---------------------------------------------------------------------------


def _install(monkeypatch):
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)


def _aborted(ws: Path) -> list[dict]:
    return [r for r in _journal_rows(ws) if r.get("action") == "PIPELINE_RUN_ABORTED"]


_RIS = "TY  - JOUR\nTI  - An imported study of weeds\nPY  - 2021\nDO  - 10.9/ris1\nER  - \n"


def test_staged_imports_are_never_silently_swapped_for_the_run(tmp_path, monkeypatch):
    """Finding 2: accept_corpus would materialise staged RIS over the run's records."""
    from scholar_harness.corpus_accept import stage_ris_source

    _install(monkeypatch)
    ws = _workspace(tmp_path)
    ris = tmp_path / "export.ris"
    ris.write_text(_RIS, encoding="utf-8")
    stage_ris_source(ws, "Scopus", ris.read_bytes(), file_name="export.ris", searched_on="2026-11-01")

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["status"] == "FAILED"
    snap = results["stages"]["corpus_snapshot"]
    assert snap["status"] == "REFUSED" and snap["code"] == "STAGED_IMPORT_PENDING"
    assert not (ws / "audit" / "artifact_registry.json").exists()
    assert _aborted(ws)


def test_resume_refuses_an_edited_protocol(tmp_path, monkeypatch):
    """Finding 4a: an accepted snapshot binds the protocol; resume checks it."""
    _install(monkeypatch)
    ws = _workspace(tmp_path)
    asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    proto = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    proto["research_questions"][0]["text"] += " (edited)"
    (ws / "protocol.json").write_text(json.dumps(proto), encoding="utf-8")

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["status"] == "FAILED"
    assert results["stages"]["screening"]["reason"].startswith("PROTOCOL_CHANGED_SINCE_SNAPSHOT")
    assert _aborted(ws)


def test_resume_refuses_batches_that_do_not_cover_the_snapshot(tmp_path, monkeypatch):
    """Finding 4b: a partial batch set is never reported as complete."""
    _install(monkeypatch)
    ws = _workspace(tmp_path)
    asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    batch = ws / "literature" / "screening" / "batch_001.json"
    data = json.loads(batch.read_text(encoding="utf-8"))
    data["papers"] = data["papers"][:1]
    batch.write_text(json.dumps(data), encoding="utf-8")

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["status"] == "FAILED"
    assert results["stages"]["screening"]["reason"].startswith("BATCHES_INCOMPLETE")


def test_no_project_json_reports_not_built(tmp_path, monkeypatch):
    """Finding 6: a folder that is not a workspace builds no snapshot."""
    _install(monkeypatch)
    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert results["stages"]["corpus_snapshot"]["status"] == "NOT_BUILT"
    assert "no project.json" in results["stages"]["corpus_snapshot"]["reason"]


def test_unregistered_workspace_reports_not_built(tmp_path, monkeypatch):
    _install(monkeypatch)
    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps({"project_id": "legacy", "stats": {}}), encoding="utf-8")
    _write_protocol(ws)
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert results["stages"]["corpus_snapshot"]["status"] == "NOT_BUILT"
    assert "registered_workspace_id" in results["stages"]["corpus_snapshot"]["reason"]


def test_a_prepare_exit_in_a_registered_workspace_is_journalled(tmp_path, monkeypatch):
    """Finding 6: the SystemExit path with a real snapshot."""
    import sys

    _install(monkeypatch)
    ws = _workspace(tmp_path)
    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: sys.exit(1))
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert results["status"] == "FAILED"
    assert results["stages"]["corpus_snapshot"]["status"] == "ACCEPTED"
    assert results["stages"]["screening"]["status"] == "SKIPPED"
    assert _aborted(ws)


def test_the_snapshot_outcome_is_journalled_with_provider_warnings(tmp_path, monkeypatch):
    """Finding 5: the PARTIAL outcome and its warnings are persisted, not dropped."""
    _install(monkeypatch)
    ws = _workspace(tmp_path)
    from scholar_harness.pipeline import coordinator as coord

    real = coord._accept_run_corpus
    monkeypatch.setattr(coord, "_accept_run_corpus",
                        lambda w, errors: real(w, {"crossref": "ProviderError: HTTP 500"}))
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert results["stages"]["corpus_snapshot"]["outcome_status"] == "PARTIAL"
    rows = [r for r in _journal_rows(ws) if r.get("action") == "CORPUS_SNAPSHOT_ACCEPTED"]
    assert rows and rows[-1]["status"] == "PARTIAL"
    assert rows[-1]["parameters"]["provider_warnings"] == ["crossref: ProviderError: HTTP 500"]
