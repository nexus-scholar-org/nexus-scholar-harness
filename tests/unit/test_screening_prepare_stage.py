"""Focused HCM-04f tests for the neutral screening preparation stage.

Stage 4 preparation (agent-in-the-loop batch preparation, batch glob count,
IN PROGRESS report) lives in ``scholar_harness.pipeline.screening_prepare``;
the orchestrator delegates and keeps the ``included.json`` collect gate plus
the ``PIPELINE_RUN_PAUSED_FOR_SCREENING`` audit. Every test is hermetic
(``tmp_path`` only, no network) and asserts zero behavior change: call-time
``cmd_prepare`` resolution, identical glob/report/mapping bytes, identical
``SystemExit`` propagation, no decisions/collect/audit of its own, and the
vestigial ``protocol_data`` read left behind.

Mapping to the HCM-04f packet:

- HCM4F-01 preparation calls ``cmd_prepare`` with exact args (binding kept)
- HCM4F-02 call-time resolution, no module-top binding (fidelity seam kept)
- HCM4F-03 glob parity (excludes ``_decisions``, sorted files, alias)
- HCM4F-04 report bytes identical to the base template (golden + orch parity)
- HCM4F-05 orchestrator mapping (PENDING_AGENT_REVIEW + counts from bindings)
- HCM4F-06 SystemExit propagation (failure 1 + existing 0, stage + orch)
- HCM4F-07 zero-record (empty glob -> 0, report written, NOT complete)
- HCM4F-08 move-not-duplicate (orch region has no batcher logic)
- HCM4F-09 no decisions/collect (stage never fabricates screening output)
- HCM4F-10 no audit of its own (PAUSE stays orchestrator-side)
- HCM4F-11 vestigial ``protocol_data`` not carried + minimal signature
- HCM4F-12 console-transport guard + no broad seam + byte-restore probe

Negatives NEG-01..NEG-04 are the mutation/failure halves:

- NEG-01 SystemExit-path parity (tampered/missing/registry + existing)
- NEG-02 decision-fabrication mutation (stage must not write decisions)
- NEG-03 binding-removal mutation (deleted ``cmd_prepare`` call detected)
- NEG-04 audit-suppression mutation (deleted PAUSE / stage audit detected)

Carry-forward debt TD-HCM-TEST-SEAMS: the ``SearchEngine`` / ``Deduplicator``
/ ``DocumentVerifier`` orchestrator-namespace shims stay (fidelity stubs
patch them). This packet adds NO fourth broad seam: call-time
``cmd_prepare`` resolution needs none (proven by HCM4F-02/C16).

Zero-record behavior: batches glob empty -> total 0, report written with
``0 batch files``, mapping truthful PENDING_AGENT_REVIEW (NOT
screening-complete), Stages 5-9 SKIPPED.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import screening_prepare as prep_mod


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_FIXTURE = (
    ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)


def _real_workspace(tmp_path: Path) -> tuple[Path, dict]:
    """Workspace shaped for the REAL batcher: protocol + registry + verified."""
    from scholar_harness.contracts import AcceptanceContext, accept_artifact
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol
    from scholar_search.identity import build_corpus_snapshot_artifact
    from scholar_search.models import Author, Document, ExternalIds

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "WSP-screening-migration", "stats": {}}),
        encoding="utf-8",
    )
    protocol = json.loads(PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    protocol_hash = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    source = Document(
        title="Contract-bound screening",
        year=2026,
        provider="crossref",
        provider_id="screening-record",
        external_ids=ExternalIds(doi="10.1000/screening"),
        authors=[Author("Reviewer")],
    )
    built = build_corpus_snapshot_artifact(
        [source],
        workspace_id="WSP-screening-migration",
        run_id="RUN-search-screening",
        protocol_fingerprint=protocol_hash,
        created_at=datetime(2026, 9, 21, tzinfo=UTC),
        commit="3" * 40,
    )
    corpus = built.artifact
    result = accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=corpus["workspace_id"],
            protocol_fingerprint=protocol_hash,
            corpus_fingerprint=corpus["corpus_fingerprint"],
        ),
    )
    assert result.accepted
    study = corpus["data"]["studies"][0]
    literature = workspace / "literature"
    literature.mkdir()
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": "10.1000/screening"},
                }
            ]
        ),
        encoding="utf-8",
    )
    return workspace, study


def _write_orchestrator_protocol(
    ws: Path, slug: str = "screening-prepare-test"
) -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "screening-prepare-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Screening Preparation Stage Parity",
        "lead_researcher": "Test Lead",
        "unit_of_analysis": "Harness Pipelines",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "What is the pipeline throughput?",
                "target_facet": "evaluation_metrics",
                "required_evidence_type": "Quantitative Benchmark",
            }
        ],
        "core_concepts": [{"concept": "Pipeline", "synonyms": ["orchestrator"]}],
        "inclusion_criteria": [
            {"criterion": "Reports benchmark pass rates", "maps_to_rqs": ["RQ1"]}
        ],
        "exclusion_criteria": [
            {
                "criterion": "Non-English",
                "reason_category": "LANGUAGE",
                "maps_to_rqs": ["RQ1"],
            }
        ],
        "matrix_dimensions": [
            {
                "id": "throughput",
                "name": "Throughput",
                "description": "Operations per second",
            }
        ],
    }
    intent = IntentPacket.model_validate(data)
    proto = json.loads(canonical_json(compile_protocol(intent)).decode("utf-8"))
    p = ws / "protocol.json"
    p.write_text(json.dumps(proto), encoding="utf-8")
    return p


def _expected_report_text(ws: Path, total: int) -> str:
    return (
        f"# PRISMA Screening \u2014 IN PROGRESS\n\n"
        f"{total} batch files prepared in `literature/screening/`.\n\n"
        f"**Next step**: Ask the agent to screen the batches, then run:\n"
        f"```\npython src/scholar_harness/agent_screen.py collect {ws}\n```\n"
    )


def _journal_rows(ws: Path) -> list[dict]:
    p = ws / "audit" / "journal.jsonl"
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _pause_rows(ws: Path) -> list[dict]:
    return [
        r
        for r in _journal_rows(ws)
        if r.get("action") == "PIPELINE_RUN_PAUSED_FOR_SCREENING"
    ]


def _install_upstream_fakes(monkeypatch, docs):
    """Hermetic upstream: empty discovery/dedup/hydration/verification."""

    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            import copy

            return copy.deepcopy(docs)

        async def close(self):
            pass

    class _PassthroughVerifier:
        async def process_batch(self, docs_in, verify=True, enrich=True):
            return list(docs_in), []

    from scholar_harness.pipeline import hydration as hyd_mod

    class _PassthroughHydrator:
        def __init__(self, client):
            pass

        async def hydrate_missing_abstracts(self, docs_in, batch_size=50):
            return list(docs_in), {"attempted": 0, "hydrated": 0, "failed": 0}

    class _DummyClient:
        def __init__(self, *a, **k):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "DocumentVerifier", _PassthroughVerifier)
    monkeypatch.setattr(hyd_mod, "AbstractHydrator", _PassthroughHydrator)
    monkeypatch.setattr(hyd_mod, "AcademicHttpClient", _DummyClient)


# ---------------------------------------------------------------------------
# HCM4F-01 preparation calls cmd_prepare with exact args
# ---------------------------------------------------------------------------


def test_stage_calls_cmd_prepare_with_exact_args(tmp_path, monkeypatch):
    """HCM4F-01: workspace_dir + batch_size + force reach the batcher verbatim."""
    seen: list[tuple] = []
    seen_kwargs: list[dict] = []

    def _spy(ws, batch_size=20, force=False):
        seen.append(ws)
        seen_kwargs.append({"batch_size": batch_size, "force": force})
        (Path(ws) / "literature" / "screening").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", _spy)
    ws = tmp_path / "ws"

    outcome = prep_mod.run_screening_preparation(
        workspace_dir=ws, batch_size=5, force=False
    )

    assert len(seen) == 1
    assert Path(seen[0]) == ws
    assert seen_kwargs[0] == {"batch_size": 5, "force": False}
    assert outcome.total_batches == 0
    assert outcome.batch_files == []
    assert outcome.report_path == ws / "literature" / "prisma_screening_report.md"


def test_stage_default_args_match_base_batch_size_20_force_true(tmp_path, monkeypatch):
    """HCM4F-01b: defaults preserve the base ``batch_size=20, force=True``."""
    seen_kwargs: list[dict] = []

    def _spy(ws, batch_size=20, force=False):
        seen_kwargs.append({"batch_size": batch_size, "force": force})
        (Path(ws) / "literature" / "screening").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", _spy)
    ws = tmp_path / "ws"

    prep_mod.run_screening_preparation(workspace_dir=ws)

    assert seen_kwargs[0] == {"batch_size": 20, "force": True}


# ---------------------------------------------------------------------------
# HCM4F-02 call-time resolution, no module-top binding (NEG-03 counterpart)
# ---------------------------------------------------------------------------


def test_stage_has_no_module_top_cmd_prepare_binding():
    """HCM4F-02: the fidelity seam is call-time resolution, not a top import."""
    text = Path(prep_mod.__file__).read_text(encoding="utf-8")
    lines = text.splitlines()
    top_imports: list[str] = []
    in_docstring = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped.startswith('"""'):
            # Skip the module docstring (it names cmd_prepare in prose).
            if stripped.count('"""') >= 2:
                continue
            in_docstring = True
            continue
        if in_docstring:
            if '"""' in line:
                in_docstring = False
            continue
        if stripped.startswith(("from ", "import ")):
            top_imports.append(line)
        # Stop at the first def (end of the import block).
        if stripped.startswith(("def ", "class ", "@dataclass")):
            break
    joined = "\n".join(top_imports)
    assert "cmd_prepare" not in joined
    assert "agent_screen" not in joined
    # The call-time import lives inside the function body.
    body = text.split("def run_screening_preparation", 1)[1]
    assert "from scholar_harness.agent_screen import cmd_prepare" in body


def test_call_time_patch_takes_effect_without_reimport(tmp_path, monkeypatch):
    """HCM4F-02b: patching agent_screen.cmd_prepare AFTER import is honored."""
    import scholar_harness.agent_screen as agent_screen_mod

    calls: list[bool] = []

    def _patched(ws, batch_size=20, force=True):
        calls.append(True)
        (Path(ws) / "literature" / "screening").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(agent_screen_mod, "cmd_prepare", _patched)
    ws = tmp_path / "ws"

    outcome = prep_mod.run_screening_preparation(workspace_dir=ws)

    assert calls == [True]
    assert outcome.total_batches == 0


# ---------------------------------------------------------------------------
# HCM4F-03 glob parity + HCM4F-04 report bytes (real batcher)
# ---------------------------------------------------------------------------


def test_real_batcher_one_batch_glob_and_report(tmp_path):
    """HCM4F-03/04: real batcher -> 1 batch, decisions excluded, golden report."""
    workspace, _study = _real_workspace(tmp_path)

    outcome = prep_mod.run_screening_preparation(
        workspace_dir=workspace, batch_size=20, force=True
    )

    assert outcome.total_batches == 1
    assert [p.name for p in outcome.batch_files] == ["batch_001.json"]
    assert outcome.batch_paths == outcome.batch_files
    assert (
        outcome.report_path == workspace / "literature" / "prisma_screening_report.md"
    )
    assert outcome.report_path.read_text(encoding="utf-8") == _expected_report_text(
        workspace, 1
    )
    # Glob excludes _decisions: add a decisions file, rerun count path via stub.
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text("[]", encoding="utf-8")
    (screening / "batch_001_decisions_screener2.json").write_text(
        "[]", encoding="utf-8"
    )
    recount = sorted(
        f for f in screening.glob("batch_*.json") if "_decisions" not in f.name
    )
    assert [p.name for p in recount] == ["batch_001.json"]


def test_glob_excludes_decisions_with_stubbed_prepare(tmp_path, monkeypatch):
    """HCM4F-03b: pre-existing decisions files never inflate the count."""
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )
    ws = tmp_path / "ws"
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True)
    (screening / "batch_001.json").write_text("{}", encoding="utf-8")
    (screening / "batch_002.json").write_text("{}", encoding="utf-8")
    (screening / "batch_001_decisions.json").write_text("[]", encoding="utf-8")
    (screening / "batch_002_decisions_screener2.json").write_text(
        "[]", encoding="utf-8"
    )
    (screening / "MANIFEST.json").write_text("{}", encoding="utf-8")

    outcome = prep_mod.run_screening_preparation(workspace_dir=ws)

    assert outcome.total_batches == 2
    assert sorted(p.name for p in outcome.batch_files) == [
        "batch_001.json",
        "batch_002.json",
    ]
    assert outcome.report_path.read_text(encoding="utf-8") == _expected_report_text(
        ws, 2
    )


# ---------------------------------------------------------------------------
# HCM4F-05 orchestrator mapping (PENDING + counts from own bindings)
# ---------------------------------------------------------------------------


def test_orchestrator_mapping_truthful_pending_with_stubbed_batches(
    tmp_path, monkeypatch
):
    """HCM4F-05: mapping is PENDING_AGENT_REVIEW; papers_to_screen from Stage 3."""
    from scholar_search.models import Document, ExternalIds

    docs = [
        Document(
            title="First Study",
            year=2024,
            provider="openalex",
            provider_id="W1",
            external_ids=ExternalIds(doi="10.1000/aaa"),
            abstract="First abstract.",
        ),
        Document(
            title="Second Study",
            year=2023,
            provider="crossref",
            provider_id="C2",
            external_ids=ExternalIds(doi="10.1000/bbb"),
            abstract="Second abstract.",
        ),
    ]
    _install_upstream_fakes(monkeypatch, docs)

    def _two_batches(ws, batch_size=20, force=True):
        screening = Path(ws) / "literature" / "screening"
        screening.mkdir(parents=True, exist_ok=True)
        (screening / "batch_001.json").write_text("{}", encoding="utf-8")
        (screening / "batch_002.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", _two_batches)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_orchestrator_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["status"] == "PENDING_AGENT_REVIEW"
    assert results["stages"]["screening"] == {
        "status": "PENDING_AGENT_REVIEW",
        "batch_files_prepared": 2,
        "papers_to_screen": 2,
    }
    assert (ws / "literature" / "prisma_screening_report.md").read_text(
        encoding="utf-8"
    ) == _expected_report_text(ws.resolve(), 2)
    for stage in ("extraction", "indexing", "matrix", "graph", "synthesis"):
        assert results["stages"][stage]["status"] == "SKIPPED"
    assert len(_pause_rows(ws)) == 1


def test_orchestrator_report_matches_direct_stage_bytes_on_same_workspace(
    tmp_path, monkeypatch
):
    """HCM4F-04b/C15: same-workspace orch report == direct-stage report bytes."""
    _install_upstream_fakes(monkeypatch, [])

    def _one_batch(ws, batch_size=20, force=True):
        screening = Path(ws) / "literature" / "screening"
        screening.mkdir(parents=True, exist_ok=True)
        (screening / "batch_001.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", _one_batch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_orchestrator_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert results["stages"]["screening"]["batch_files_prepared"] == 1
    orch_bytes = (ws / "literature" / "prisma_screening_report.md").read_bytes()

    # Direct stage over the SAME workspace (batches preserved) is byte-identical.
    direct_outcome = prep_mod.run_screening_preparation(
        workspace_dir=ws, batch_size=20, force=True
    )
    # NOTE: the stub above overwrote batch_001.json with identical "{}" bytes,
    # so the glob count is unchanged; the report must be byte-identical.
    assert direct_outcome.total_batches == 1
    assert (ws / "literature" / "prisma_screening_report.md").read_bytes() == orch_bytes


# ---------------------------------------------------------------------------
# HCM4F-07 zero-record (empty glob -> 0, truthful, NOT complete)
# ---------------------------------------------------------------------------


def test_zero_record_stage_total_zero_report_written(tmp_path, monkeypatch):
    """HCM4F-07a: empty glob -> total 0, report written with 0, no decisions."""
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )
    ws = tmp_path / "ws"

    outcome = prep_mod.run_screening_preparation(workspace_dir=ws)

    assert outcome.total_batches == 0
    assert outcome.batch_files == []
    assert outcome.report_path.read_text(encoding="utf-8") == _expected_report_text(
        ws, 0
    )
    assert "0 batch files" in outcome.report_path.read_text(encoding="utf-8")
    assert not (ws / "literature" / "included.json").exists()
    assert (
        list((ws / "literature" / "screening").glob("batch_*.json")) == []
        if (ws / "literature" / "screening").exists()
        else True
    )


def test_zero_record_orchestrator_truthful_pending_not_complete(tmp_path, monkeypatch):
    """HCM4F-07b: orchestrator with 0 batches is PENDING, never SUCCESS."""
    _install_upstream_fakes(monkeypatch, [])
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_orchestrator_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["stages"]["screening"] == {
        "status": "PENDING_AGENT_REVIEW",
        "batch_files_prepared": 0,
        "papers_to_screen": 0,
    }
    assert results["status"] == "PENDING_AGENT_REVIEW"
    assert results["status"] != "SUCCESS"
    for stage in ("extraction", "indexing", "matrix", "graph", "synthesis"):
        assert results["stages"][stage]["status"] == "SKIPPED"
    assert "0 batch files" in (
        ws / "literature" / "prisma_screening_report.md"
    ).read_text(encoding="utf-8")
    assert not (ws / "literature" / "included.json").exists()
    assert not (ws / "extracted").exists() or not list((ws / "extracted").glob("*.md"))
    assert len(_pause_rows(ws)) == 1


# ---------------------------------------------------------------------------
# HCM4F-06 / NEG-01 SystemExit propagation (stage + orchestrator)
# ---------------------------------------------------------------------------


def test_stage_systemexit_1_on_protocol_mismatch_no_report(tmp_path):
    """NEG-01a: tampered protocol -> SystemExit(1), no report, no batches."""
    workspace, _study = _real_workspace(tmp_path)
    protocol_path = workspace / "protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol["screening_criteria"]["inclusion"][0]["criterion"] = (
        "Tampered criterion text with a different canonical fingerprint."
    )
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        prep_mod.run_screening_preparation(
            workspace_dir=workspace, batch_size=20, force=True
        )

    assert exc_info.value.code == 1
    assert not (workspace / "literature" / "prisma_screening_report.md").exists()
    screening = workspace / "literature" / "screening"
    assert not list(screening.glob("batch_*.json"))


def test_stage_systemexit_0_on_existing_without_force_preserves_report(tmp_path):
    """NEG-01b: existing batches + force=False -> SystemExit(0), report kept."""
    workspace, _study = _real_workspace(tmp_path)

    first = prep_mod.run_screening_preparation(
        workspace_dir=workspace, batch_size=20, force=True
    )
    assert first.total_batches == 1
    report_before = (
        workspace / "literature" / "prisma_screening_report.md"
    ).read_bytes()

    with pytest.raises(SystemExit) as exc_info:
        prep_mod.run_screening_preparation(
            workspace_dir=workspace, batch_size=20, force=False
        )

    assert exc_info.value.code == 0
    # The SystemExit escaped before any rewrite: the prior report is intact.
    assert (workspace / "literature" / "prisma_screening_report.md").read_bytes() == (
        report_before
    )


def test_stage_systemexit_1_on_missing_registry(tmp_path):
    """NEG-01c: no artifact registry -> SystemExit(1), no report fabricated."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "protocol.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        prep_mod.run_screening_preparation(workspace_dir=ws)

    assert exc_info.value.code == 1
    assert not (ws / "literature" / "prisma_screening_report.md").exists()


def test_orchestrator_systemexit_propagates_without_mapping_or_pause(
    tmp_path, monkeypatch
):
    """NEG-01d: orchestrator delegates SystemExit identically (no swallow)."""
    _install_upstream_fakes(monkeypatch, [])
    # Real batcher with no registry in this workspace -> sys.exit(1).
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_orchestrator_protocol(ws)

    with pytest.raises(SystemExit) as exc_info:
        asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert exc_info.value.code == 1
    assert not (ws / "literature" / "prisma_screening_report.md").exists()
    assert _pause_rows(ws) == []


# ---------------------------------------------------------------------------
# HCM4F-09 / NEG-02 no decisions/collect fabrication
# ---------------------------------------------------------------------------


def test_stage_emits_no_decisions_collect_or_audit(tmp_path):
    """NEG-02: stage writes batches+report only; no decisions/included/pause."""
    workspace, _study = _real_workspace(tmp_path)

    outcome = prep_mod.run_screening_preparation(
        workspace_dir=workspace, batch_size=20, force=True
    )

    assert outcome.total_batches == 1
    screening = workspace / "literature" / "screening"
    assert sorted(p.name for p in screening.glob("*")) == [
        "MANIFEST.json",
        "batch_001.json",
    ]
    assert list(screening.glob("*_decisions*")) == []
    assert not (workspace / "literature" / "included.json").exists()
    assert not (workspace / "literature" / "excluded.json").exists()
    # No PAUSE/collect audit of its own: the only journal rows are the batch
    # ARTIFACT_ACCEPTED rows the batcher publishes via accept_artifact
    # (inherited preparation state, not a stage audit).
    rows = _journal_rows(workspace)
    assert all(r.get("action") != "PIPELINE_RUN_PAUSED_FOR_SCREENING" for r in rows)
    assert all("collect" not in str(r.get("action", "")).lower() for r in rows)
    # The batcher publishes screening_batch artifacts, never decisions.
    registry = json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    assert any(
        e.get("artifact_type") == "screening_batch"
        for e in registry["artifacts"].values()
    )
    assert all(
        e.get("artifact_type") != "screening_decisions"
        for e in registry["artifacts"].values()
    )


def test_stage_never_collects_even_when_decisions_exist(tmp_path, monkeypatch):
    """NEG-02b: pre-existing decisions never become included.json via the stage."""
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )
    ws = tmp_path / "ws"
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True)
    (screening / "batch_001.json").write_text("{}", encoding="utf-8")
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "human-reviewer-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "decisions": [],
            }
        ),
        encoding="utf-8",
    )

    outcome = prep_mod.run_screening_preparation(workspace_dir=ws)

    assert outcome.total_batches == 1
    assert not (ws / "literature" / "included.json").exists()
    assert not (ws / "literature" / "excluded.json").exists()


def test_stage_source_has_no_collect_or_audit_calls():
    """NEG-02c/04b: reintroducing collect/audit calls into the stage breaks this."""
    text = Path(prep_mod.__file__).read_text(encoding="utf-8")
    # Code-call guards (prose in the module docstring names the forbidden
    # concepts to document the split; only an actual call breaks parity).
    assert "cmd_collect(" not in text
    assert "cmd_status(" not in text
    assert "append_legacy_event(" not in text
    assert "_log_audit_event(" not in text
    # Import-statement guard: no collector/audit/console transport import.
    lines = text.splitlines()
    out, buf, depth = [], "", 0
    in_docstring = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('"""'):
            if line.strip().count('"""') >= 2:
                continue
            in_docstring = True
            continue
        if in_docstring:
            if '"""' in line:
                in_docstring = False
            continue
        stripped = line.strip()
        if not buf and not stripped.startswith(("from ", "import ")):
            continue
        buf += line + "\n"
        depth += line.count("(") - line.count(")")
        if line.rstrip().endswith("\\"):
            continue
        if depth <= 0:
            out.append(buf)
            buf, depth = "", 0
    if buf:
        out.append(buf)
    joined = "\n".join(out).lower()
    assert "collector" not in joined
    assert "audit" not in joined
    assert "console" not in joined
    assert "fastapi" not in joined


# ---------------------------------------------------------------------------
# HCM4F-08 move-not-duplicate + HCM4F-10/11 + NEG-03/NEG-04
# ---------------------------------------------------------------------------


def test_stage_4_prepare_region_has_no_direct_batcher_use():
    """HCM4F-08: orchestrator delegates; the batcher logic lives in the stage."""
    source = Path(orch.__file__).read_text(encoding="utf-8")
    region = source.split("Stage 4: Systematic PRISMA 2020 Screening", 1)[1]
    region = region.split("Stage 5:", 1)[0]
    prepare = region.split("Stages 5-9 require", 1)[0]
    # No direct batcher code in the prepare region (prose in the HCM-04f
    # comment names the moved concepts; only code patterns break parity).
    assert "cmd_prepare(" not in prepare
    assert "_prepare_batches(" not in prepare
    assert ".glob(" not in prepare
    assert ".write_text(" not in prepare
    assert "protocol_data =" not in prepare
    assert "p_path.read_text" not in prepare
    assert "run_screening_preparation" in prepare
    assert "preparation_outcome" in prepare
    # The collect gate + PAUSE audit stay orchestrator-side (not moved).
    gate = region.split("Stages 5-9 require", 1)[1]
    assert "included.json" in gate
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" in gate
    assert "run_screening_preparation" not in gate


def test_orchestrator_source_has_no_screening_batcher_import():
    """NEG-03b: the orchestrator must not rebind cmd_prepare at module top."""
    text = Path(orch.__file__).read_text(encoding="utf-8")
    assert "from scholar_harness.agent_screen import" not in text
    assert "from .agent_screen import" not in text


def test_binding_removal_mutation_detected_by_spy(tmp_path, monkeypatch):
    """NEG-03: deleting the cmd_prepare call leaves no batches/report."""
    calls: list[bool] = []

    def _spy(ws, batch_size=20, force=True):
        calls.append(True)
        (Path(ws) / "literature" / "screening").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", _spy)
    ws = tmp_path / "ws"

    prep_mod.run_screening_preparation(workspace_dir=ws)

    assert calls == [True]
    # A binding-removal mutation (stage that never calls cmd_prepare) would
    # produce this same empty outcome WITHOUT the call -- the spy proves the
    # real path called through. If the call were deleted, `calls` stays empty
    # and this assertion (plus the real-batcher tests above) fails.


def test_audit_suppression_mutation_detected(tmp_path, monkeypatch):
    """NEG-04: stage writes no audit; orchestrator PAUSE is the only pause row."""
    # Stage alone: no journal at all.
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )
    ws_stage = tmp_path / "ws-stage"
    prep_mod.run_screening_preparation(workspace_dir=ws_stage)
    assert _journal_rows(ws_stage) == []

    # Orchestrator: exactly one PAUSE row (suppressing it breaks parity).
    _install_upstream_fakes(monkeypatch, [])
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_orchestrator_protocol(ws)
    asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    pauses = _pause_rows(ws)
    assert len(pauses) == 1
    row = pauses[0]
    assert row["agent_or_tool"] == "scholar-harness"
    assert "screen literature/screening/batch_*.json" in row["description"]
    assert row["status"] == "SUCCESS"


# ---------------------------------------------------------------------------
# HCM4F-11 vestigial + signature + HCM4F-12 guards/seam/restore
# ---------------------------------------------------------------------------


def test_vestigial_protocol_data_not_carried_and_signature_minimal():
    """HCM4F-11: vestigial read not carried as code; signature is minimal trio."""
    text = Path(prep_mod.__file__).read_text(encoding="utf-8")
    # Code guards (the docstring documents the vestigial read in prose).
    assert "protocol_data =" not in text
    assert "protocol_data[" not in text
    sig = inspect.signature(prep_mod.run_screening_preparation)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == ["workspace_dir", "batch_size", "force"]
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params)
    assert sig.parameters["batch_size"].default == 20
    assert sig.parameters["force"].default is True
    # The outcome carries no paper count (orchestrator binds papers_to_screen).
    import dataclasses

    assert "papers_to_screen" not in [
        f.name for f in dataclasses.fields(prep_mod.ScreeningPreparationOutcome)
    ]
    assert "papers_to_screen=" not in text


def test_stage_has_no_console_transport_import():
    """HCM4F-12a: neutral stage imports no console/FastAPI transport."""
    text = Path(prep_mod.__file__).read_text(encoding="utf-8")
    lines = text.splitlines()
    out, buf, depth = [], "", 0
    in_docstring = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('"""'):
            if line.strip().count('"""') >= 2:
                continue
            in_docstring = True
            continue
        if in_docstring:
            if '"""' in line:
                in_docstring = False
            continue
        stripped = line.strip()
        if not buf and not stripped.startswith(("from ", "import ")):
            continue
        buf += line + "\n"
        depth += line.count("(") - line.count(")")
        if line.rstrip().endswith("\\"):
            continue
        if depth <= 0:
            out.append(buf)
            buf, depth = "", 0
    if buf:
        out.append(buf)
    for stmt in out:
        low = stmt.lower()
        assert "console" not in low
        assert "fastapi" not in low
        assert "uvicorn" not in low


def test_no_broad_compat_seam_added():
    """HCM4F-12b/C16: call-time resolution needs NO orchestrator fallback seam."""
    text = Path(prep_mod.__file__).read_text(encoding="utf-8")
    # Code-pattern guards (the docstring documents the absent seam in prose).
    assert "_REAL_" not in text
    assert "__dict__.get(" not in text
    assert "import scholar_harness.orchestrator" not in text
    assert "from scholar_harness.orchestrator import" not in text
    assert "_prepare_class" not in text
    assert "_prepare_batches_class" not in text
    # The stage resolves only the batcher entry point, never kit engines.
    lines = text.splitlines()
    out, buf, depth = [], "", 0
    in_docstring = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('"""'):
            if line.strip().count('"""') >= 2:
                continue
            in_docstring = True
            continue
        if in_docstring:
            if '"""' in line:
                in_docstring = False
            continue
        stripped = line.strip()
        if not buf and not stripped.startswith(("from ", "import ")):
            continue
        buf += line + "\n"
        depth += line.count("(") - line.count(")")
        if line.rstrip().endswith("\\"):
            continue
        if depth <= 0:
            out.append(buf)
            buf, depth = "", 0
    if buf:
        out.append(buf)
    joined = "\n".join(out)
    assert "SearchEngine" not in joined
    assert "Deduplicator" not in joined
    assert "DocumentVerifier" not in joined
    # No re-export shim required in the orchestrator either.
    assert not hasattr(orch, "run_screening_preparation")
    assert not hasattr(orch, "ScreeningPreparationOutcome")


def test_byte_identical_probe_restore(tmp_path):
    """HCM4F-12c: delete the report, rerun with force, bytes restored exactly."""
    workspace, _study = _real_workspace(tmp_path)

    first = prep_mod.run_screening_preparation(
        workspace_dir=workspace, batch_size=20, force=True
    )
    batch_before = (
        workspace / "literature" / "screening" / "batch_001.json"
    ).read_bytes()
    report_before = (
        workspace / "literature" / "prisma_screening_report.md"
    ).read_bytes()
    assert first.total_batches == 1

    (workspace / "literature" / "prisma_screening_report.md").unlink()

    second = prep_mod.run_screening_preparation(
        workspace_dir=workspace, batch_size=20, force=True
    )

    assert second.total_batches == 1
    assert second.batch_files == first.batch_files
    assert second.report_path == first.report_path
    assert (workspace / "literature" / "screening" / "batch_001.json").read_bytes() == (
        batch_before
    )
    assert (workspace / "literature" / "prisma_screening_report.md").read_bytes() == (
        report_before
    )
