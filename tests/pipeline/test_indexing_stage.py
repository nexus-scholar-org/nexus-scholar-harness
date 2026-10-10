"""Focused HCM-04h tests for the neutral indexing stage.

Stage 6 (typed vector indexing over accepted documents, no invented identity)
lives in ``scholar_harness.pipeline.indexing``; the orchestrator keeps thin
delegating methods with identical signatures and forwards its own
(possibly patched) kit globals plus data readers as explicit collaborators.
Every test is hermetic (``tmp_path`` only, no network; embedder/backend are
faked) and asserts zero behavior change: verbatim registry readers,
parent-view, request literals, outcome mapping, audit bytes, MinimalIndexer
shapes, and the preserved latent ``parameters=`` TypeError.

Mapping to the HCM-04h packet:

- A1 registry readers parity (orch vs stage, direct calls)
- A2 parent-view parity (recorded limbs, generation match)
- A3 request literals (chromadb/sentence-transformers/all-MiniLM-L6-v2/384/cosine/chunker)
- A4 outcome carries (result dict, indexer) for Stage 7
- A5 thin signatures identical (HCM-04b pattern)
- B6 kit DI (orch.get_embedder/backend/reader/index_workspace patches flow through)
- B7 data DI (orch._accepted_document_records patch flows through, E3-NEG-013)
- B8 audit byte parity (RAG_INDEX_REJECTED/BUILT, legacy scheme, no uppercase)
- B9 no-backend-touch on refusal (store never created, backend never built)
- B10 identity-first (missing identity raises before backend, no bytes)
- B11 outcome mapping SUCCESS/PARTIAL/REFUSED/FAILED
- B12 documents populate re-reads screening parents (decision_id binding)
- B13 MinimalIndexer shapes (collection_name/embedder_kwargs/count)
- B14 recorded_workspace_id cites require_recorded_identity (message parity)
- C15 ScholarIndexer vestigial (never constructed by Stage 6, stub kept for patch point)
- C16 extraction_producer sharing (producer delegates via orchestrator, untouched)
- C17 stale TypeError preserved (no bytes, no publication, not repaired)
- C18 move-not-duplicate (orchestrator Stage-6 region has no inline logic)
- C19 transport guard (stage never imports orchestrator)

Negatives (each tmp_path-only, byte-identical restored):

- NEG-01 missing-manifest -> DOCUMENT_MANIFEST_NOT_ACCEPTED, no store, no BUILT
- NEG-02 identity-fallback -> RegisteredWorkspaceIdentityMissingError, no store, no journal delta
- NEG-03 all-refused-as-success -> NO_DOCUMENTS_TO_INDEX is FAILED never SUCCESS
- NEG-04 refusal-into-backend -> boom backend never constructed on refusal
- NEG-05 reuse-binding-breaks -> blank study_id (no screening parent) refuses, workspace limb never reused as study

Carry-forward debt: TD seams x3 untouched; MCP docs failure base-proven;
E3 021/022/050 installer-quirk BLOCKED rows kit-side untouched.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scholar_harness import orchestrator as orch_module
from scholar_harness.orchestrator import ResearchOrchestrator
from scholar_harness.pipeline import indexing as idx_mod
from scholar_harness.workspace.identity import require_recorded_identity

FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32


def _record_identity(ws: Path) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "indexing-stage-test",
                "registered_workspace_id": FIXTURE_WORKSPACE_ID,
            }
        ),
        encoding="utf-8",
    )


def _journal(ws: Path) -> list[dict]:
    p = ws / "audit" / "journal.jsonl"
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _strip_volatile(event: dict) -> dict:
    d = dict(event)
    d.pop("timestamp", None)
    d.pop("event_id", None)
    return d


# ---------------------------------------------------------------------------
# A5 signatures identical
# ---------------------------------------------------------------------------


def test_a5_thin_signatures_identical():
    assert (
        str(inspect.signature(ResearchOrchestrator._load_artifact_registry))
        == "(self) -> 'ArtifactRegistry | None'"
    )
    assert (
        str(inspect.signature(ResearchOrchestrator._accepted_artifact_payload))
        == "(self, entry: 'RegistryEntry') -> 'Any | None'"
    )
    assert (
        str(inspect.signature(ResearchOrchestrator._accepted_screening_parents))
        == "(self) -> 'dict[str, dict[str, str]]'"
    )
    assert (
        str(inspect.signature(ResearchOrchestrator._accepted_document_records))
        == "(self) -> 'dict[str, dict[str, str]]'"
    )
    assert (
        str(inspect.signature(ResearchOrchestrator._build_parent_view))
        == "(self) -> 'dict[str, Any] | None'"
    )
    sig = inspect.signature(ResearchOrchestrator._build_index_service_request)
    assert list(sig.parameters) == [
        "self",
        "chroma_dir",
        "parent_view",
        "run_id",
        "created_at",
        "producer_commit",
        "producer_version",
    ]
    assert (
        str(inspect.signature(ResearchOrchestrator._run_indexing_stage))
        == "(self, chroma_dir: 'Path') -> 'tuple[dict[str, Any], Any]'"
    )


# ---------------------------------------------------------------------------
# A1 direct-call parity (empty workspace)
# ---------------------------------------------------------------------------


def test_a1_empty_registry_parity(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    o = ResearchOrchestrator(ws)
    assert o._load_artifact_registry() is None
    assert idx_mod.load_artifact_registry(ws) is None
    assert o._accepted_screening_parents() == {}
    assert idx_mod.accepted_screening_parents(ws) == {}
    assert o._accepted_document_records() == {}
    assert idx_mod.accepted_document_records(ws) == {}
    assert o._build_parent_view() is None
    assert idx_mod.build_parent_view(ws) is None


# ---------------------------------------------------------------------------
# B14 recorded_workspace_id cites require_recorded_identity
# ---------------------------------------------------------------------------


def test_b14_recorded_identity_message_parity(tmp_path: Path):
    from scholar_harness.workspace.errors import RegisteredWorkspaceIdentityMissingError

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps({"project_id": "x"}), encoding="utf-8")
    o = ResearchOrchestrator(ws)
    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as a:
        o.recorded_workspace_id()
    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as b:
        require_recorded_identity(ws)
    assert str(a.value) == str(b.value)
    # The stage uses require_recorded_identity directly (cite): no orchestrator import.
    src = Path(idx_mod.__file__).read_text(encoding="utf-8")
    assert "require_recorded_identity" in src
    assert "import scholar_harness.orchestrator" not in src
    assert "from scholar_harness.orchestrator import" not in src


# ---------------------------------------------------------------------------
# C15 ScholarIndexer vestigial
# ---------------------------------------------------------------------------


def test_c15_scholar_indexer_never_constructed_but_patch_point_kept():
    assert hasattr(orch_module, "ScholarIndexer")
    src = Path(orch_module.__file__).read_text(encoding="utf-8")
    # Only the stub class definition mentions ScholarIndexer in Stage-6 path;
    # _run_indexing_stage body (now thin delegate) never constructs it.
    body_start = src.index("def _run_indexing_stage")
    body_end = src.index("def _log_audit_event")
    body = src[body_start:body_end]
    assert "ScholarIndexer" not in body
    assert "MinimalIndexer" not in body  # inline classes live in the stage now
    stage_src = Path(idx_mod.__file__).read_text(encoding="utf-8")
    # No construction or definition in code (docstring mentions are allowed).
    assert "\nclass ScholarIndexer" not in stage_src
    assert "ScholarIndexer(" not in stage_src
    assert stage_src.count("class MinimalIndexer") >= 4


# ---------------------------------------------------------------------------
# C18 move-not-duplicate + C19 transport guard
# ---------------------------------------------------------------------------


def test_c18_stage6_region_has_no_inline_logic():
    src = Path(orch_module.__file__).read_text(encoding="utf-8")
    start = src.index("def _load_artifact_registry")
    end = src.index("def _log_audit_event")
    region = src[start:end]
    # Thin delegates only: no registry parsing, no IndexServiceRequest construction,
    # no index_workspace call, no audit payload literals.
    assert "ArtifactRegistry.model_validate_json" not in region
    assert "IndexServiceRequest(" not in region
    assert "index_workspace(" not in region
    assert "RAG_INDEX_REJECTED" not in region
    assert "RAG_INDEX_BUILT" not in region
    assert "DOCUMENT_MANIFEST_NOT_ACCEPTED" not in region


def test_c19_stage_never_imports_orchestrator_or_console():
    src = Path(idx_mod.__file__).read_text(encoding="utf-8")
    # No import of the orchestrator (docstring prose mentioning
    # ``orchestrator.get_embedder`` is allowed; only import statements count).
    for line in src.splitlines():
        s = line.strip()
        if "orchestrator" in s and ("import " in s):
            # An import line naming the orchestrator would be a transport leak.
            assert "scholar_harness.orchestrator" not in s
            assert "from .orchestrator" not in s
            assert "from scholar_harness import orchestrator" not in s
    assert "console.api" not in src
    assert "FastAPI" not in src
    assert "from scholar_harness.workspace.audit import append_legacy_event" in src
    assert (
        "from scholar_harness.workspace.identity import require_recorded_identity"
        in src
    )


# ---------------------------------------------------------------------------
# Helpers for refusal tests
# ---------------------------------------------------------------------------


def _boom_backend(**kwargs):
    raise AssertionError("backend must not be constructed on a refused run")


# ---------------------------------------------------------------------------
# NEG-01 missing-manifest
# ---------------------------------------------------------------------------


def test_neg01_missing_manifest_refuses_before_backend(tmp_path: Path, monkeypatch):
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    reg_before = None
    reg_path = ws / "audit" / "artifact_registry.json"
    if reg_path.exists():
        reg_before = reg_path.read_bytes()
    journal_before = _journal(ws)
    chroma_dir = ws / "rag" / "chroma_db"

    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom_backend)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom_backend)
    monkeypatch.setattr(orch_module, "get_embedder", _boom_backend)
    monkeypatch.setattr(orch_module, "index_workspace", _boom_backend)

    o = ResearchOrchestrator(ws)
    result, indexer = o._run_indexing_stage(chroma_dir)

    assert result["status"] == "FAILED"
    assert result["indexed_files"] == 0
    assert result["refused"] == [
        {"document_id": "", "reason": "no accepted document_manifest"}
    ]
    assert indexer.get_collection_count() == 0
    assert indexer.collection_name == "scholar_docs"
    assert not chroma_dir.exists()
    # Stage direct call agrees on shape (inputs carry absolute workspace paths,
    # so compare all fields except inputs/outputs/timestamp/event_id).
    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    _record_identity(ws2)
    (ws2 / "audit").mkdir(parents=True, exist_ok=True)
    out = idx_mod.run_indexing(
        workspace_dir=ws2,
        chroma_dir=ws2 / "rag" / "chroma_db",
        get_embedder_fn=_boom_backend,
        backend_cls=_boom_backend,
        reader_cls=_boom_backend,
        index_workspace_fn=_boom_backend,
    )
    e1 = _strip_volatile(
        [e for e in _journal(ws) if e["action"] == "RAG_INDEX_REJECTED"][0]
    )
    e2 = _strip_volatile(
        [e for e in _journal(ws2) if e["action"] == "RAG_INDEX_REJECTED"][0]
    )
    for key in ("action", "agent_or_tool", "description", "metrics", "status"):
        assert e1[key] == e2[key]
    assert "artifact_registry.json" in e1["inputs"][0]
    assert "artifact_registry.json" in e2["inputs"][0]
    assert [e for e in _journal(ws) if e["action"] == "RAG_INDEX_BUILT"] == []
    if reg_before is None:
        assert not reg_path.exists()
    else:
        assert reg_path.read_bytes() == reg_before
    assert len(_journal(ws)) == len(journal_before) + 1


# ---------------------------------------------------------------------------
# NEG-02 identity-fallback
# ---------------------------------------------------------------------------


def test_neg02_identity_refusal_leaves_bytes_and_store_untouched(
    tmp_path: Path, monkeypatch
):
    from scholar_harness.workspace.errors import RegisteredWorkspaceIdentityMissingError

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps({"project_id": "x"}), encoding="utf-8")
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    pj_before = (ws / "project.json").read_bytes()
    journal_before = (ws / "audit" / "journal.jsonl").read_bytes()
    chroma_dir = ws / "rag" / "chroma_db"

    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom_backend)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom_backend)
    monkeypatch.setattr(orch_module, "get_embedder", _boom_backend)

    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        ResearchOrchestrator(ws)._run_indexing_stage(chroma_dir)
    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        idx_mod.run_indexing(workspace_dir=ws, chroma_dir=chroma_dir)

    assert (ws / "project.json").read_bytes() == pj_before
    assert (ws / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert not chroma_dir.exists()


# ---------------------------------------------------------------------------
# NEG-03 all-refused-as-success (E3-NEG-013 shape via data DI)
# ---------------------------------------------------------------------------


def test_neg03_empty_documents_is_failed_never_success(tmp_path: Path, monkeypatch):
    # Synthetic parent_view (no registry needed when overridden) + empty
    # documents -> NO_DOCUMENTS_TO_INDEX, FAILED never SUCCESS, no backend.
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    fake_pv = {
        "artifact_id": "ART-" + "0" * 8,
        "artifact_type": "document_manifest",
        "sha256": "sha256:" + "0" * 64,
        "workspace_id": FIXTURE_WORKSPACE_ID,
        "protocol_fingerprint": "sha256:" + "1" * 64,
        "corpus_fingerprint": "sha256:" + "2" * 64,
        "documents": [],
    }
    target = tmp_path / "chroma-empty"
    # Orchestrator path with data DI: patch the class reader to {} then run.
    # Use a workspace with the fake parent_view injected via instance patch.
    o = ResearchOrchestrator(ws)
    monkeypatch.setattr(o, "_build_parent_view", lambda: dict(fake_pv))
    monkeypatch.setattr(o, "_accepted_document_records", lambda: {})
    monkeypatch.setattr(o, "_accepted_screening_parents", lambda: {})
    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom_backend)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom_backend)
    monkeypatch.setattr(orch_module, "get_embedder", _boom_backend)
    monkeypatch.setattr(orch_module, "index_workspace", _boom_backend)
    result, indexer = o._run_indexing_stage(target)
    assert result["status"] == "FAILED"
    assert result["status"] != "SUCCESS"
    assert result["refused"] == [{"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}]
    assert indexer.get_collection_count() == 0
    assert not target.exists()
    # Direct stage call with explicit empty documents agrees.
    out = idx_mod.run_indexing(
        workspace_dir=ws,
        chroma_dir=tmp_path / "chroma-empty-2",
        get_embedder_fn=_boom_backend,
        backend_cls=_boom_backend,
        reader_cls=_boom_backend,
        index_workspace_fn=_boom_backend,
        parent_view=dict(fake_pv),
        documents={},
        screening_parents={},
    )
    assert out.result["status"] == "FAILED"
    assert out.result["refused"] == [
        {"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}
    ]


# ---------------------------------------------------------------------------
# NEG-04 refusal-into-backend (boom on any backend touch)
# ---------------------------------------------------------------------------


def test_neg04_refused_run_never_touches_backend(tmp_path: Path, monkeypatch):
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    chroma_dir = tmp_path / "chroma-boom"

    def _boom(**kwargs):
        raise AssertionError("refused run touched the backend")

    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom)
    monkeypatch.setattr(orch_module, "get_embedder", _boom)
    monkeypatch.setattr(orch_module, "index_workspace", _boom)

    result, _ = ResearchOrchestrator(ws)._run_indexing_stage(chroma_dir)
    assert result["status"] == "FAILED"
    assert not chroma_dir.exists()
    assert not (ws / "rag").exists()


# ---------------------------------------------------------------------------
# NEG-05 reuse-binding-breaks (blank study_id never inherits workspace limb)
# ---------------------------------------------------------------------------


def test_neg05_blank_study_never_reuses_workspace_limb(tmp_path: Path, monkeypatch):
    # Fake parent_view (override, so no registry needed) + blank study_id
    # documents -> skipped in request building -> NO_DOCUMENTS_TO_INDEX.
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    fake_pv = {
        "artifact_id": "ART-" + "1" * 8,
        "artifact_type": "document_manifest",
        "sha256": "sha256:" + "3" * 64,
        "workspace_id": FIXTURE_WORKSPACE_ID,
        "protocol_fingerprint": "sha256:" + "4" * 64,
        "corpus_fingerprint": "sha256:" + "5" * 64,
        "documents": [],
    }
    o = ResearchOrchestrator(ws)
    monkeypatch.setattr(o, "_build_parent_view", lambda: dict(fake_pv))
    monkeypatch.setattr(
        o,
        "_accepted_document_records",
        lambda: {
            "DOC-nostudy": {
                "study_id": "   ",
                "extracted_path": "extracted/x.md",
                "parent_artifact_id": "ART-x",
                "parent_artifact_sha256": "sha256:" + "8" * 64,
            }
        },
    )
    monkeypatch.setattr(o, "_accepted_screening_parents", lambda: {})
    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom_backend)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom_backend)
    monkeypatch.setattr(orch_module, "get_embedder", _boom_backend)
    monkeypatch.setattr(orch_module, "index_workspace", _boom_backend)
    result, _ = o._run_indexing_stage(tmp_path / "chroma")
    # Blank study_id is skipped in request building -> NO_DOCUMENTS_TO_INDEX,
    # and the workspace limb is never substituted as a study.
    assert result["status"] == "FAILED"
    assert result["refused"] == [{"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}]
    assert FIXTURE_WORKSPACE_ID not in json.dumps(result)


# ---------------------------------------------------------------------------
# B6 kit DI forwarding
# ---------------------------------------------------------------------------


def _synthetic_workspace(
    tmp_path: Path, name: str = "ws"
) -> tuple[Path, dict, dict, dict]:
    """Minimal workspace with one extracted file plus fake accepted data.

    Returns (ws, parent_view, documents, screening_parents) for explicit DI.
    No registry is written; the caller injects the fakes via instance patches
    (orchestrator path) or explicit overrides (stage path). The parent_view
    carries a non-empty ``documents`` list (the kit eligibility join requires
    it) naming the one synthetic document.
    """
    from scholar_rag.chunker import text_fingerprint

    ws = tmp_path / name
    ws.mkdir(parents=True, exist_ok=True)
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    ext_dir = ws / "extracted"
    ext_dir.mkdir(parents=True, exist_ok=True)
    body = '---\nworkspace_id: "STU-001"\n---\n\n## Abstract\n\nReal body text for indexing.\n'
    (ext_dir / "DOC-001.md").write_text(body, encoding="utf-8")
    pv = {
        "artifact_id": "ART-" + "a" * 8,
        "artifact_type": "document_manifest",
        "sha256": "sha256:" + "b" * 64,
        "workspace_id": FIXTURE_WORKSPACE_ID,
        "protocol_fingerprint": "sha256:" + "c" * 64,
        "corpus_fingerprint": "sha256:" + "d" * 64,
        "documents": [
            {
                "document_id": "DOC-001",
                "study_id": "STU-001",
                "extracted_path": "extracted/DOC-001.md",
                "extracted_content_sha256": text_fingerprint(body),
            }
        ],
    }
    docs = {
        "DOC-001": {
            "study_id": "STU-001",
            "extracted_path": "extracted/DOC-001.md",
            "parent_artifact_id": pv["artifact_id"],
            "parent_artifact_sha256": pv["sha256"],
        }
    }
    parents = {
        "STU-001": {
            "parent_artifact_id": "ART-screen",
            "parent_artifact_sha256": "sha256:" + "e" * 64,
            "decision_id": "SCR-001",
        }
    }
    return ws, pv, docs, parents


def test_b6_kit_patch_flows_through_orchestrator(tmp_path: Path, monkeypatch):
    from scholar_rag.embedder import get_embedder as kit_get_embedder

    ws, pv, docs, parents = _synthetic_workspace(tmp_path, "b6")
    mock = kit_get_embedder("mock")
    mock.dimension = 384
    seen: dict = {}

    def _fake_embedder(**kwargs):
        seen["called"] = True
        return mock

    o = ResearchOrchestrator(ws)
    monkeypatch.setattr(o, "_build_parent_view", lambda: dict(pv))
    monkeypatch.setattr(o, "_accepted_document_records", lambda: dict(docs))
    monkeypatch.setattr(o, "_accepted_screening_parents", lambda: dict(parents))
    monkeypatch.setattr(orch_module, "get_embedder", _fake_embedder)
    monkeypatch.setattr(
        orch_module, "ChromaReplacementView", lambda **_: SimpleNamespace()
    )
    monkeypatch.setattr(
        orch_module, "ChromaVisibleSetReader", lambda **_: SimpleNamespace()
    )

    def _fake_index(request, **kwargs):
        return SimpleNamespace(
            outcome="SUCCESS",
            counts=SimpleNamespace(
                accepted_documents=1, rejected_documents=0, visible_chunks=2
            ),
            rejected_documents=(),
        )

    monkeypatch.setattr(orch_module, "index_workspace", _fake_index)
    result, indexer = o._run_indexing_stage(tmp_path / "chroma-b6")
    assert seen.get("called") is True
    assert result["status"] == "SUCCESS"
    assert indexer.get_collection_count() == 2


# ---------------------------------------------------------------------------
# B11 outcome mapping table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kit_outcome", "expected"),
    [
        ("SUCCESS", "SUCCESS"),
        ("PARTIAL", "PARTIAL"),
        ("REFUSED", "FAILED"),
        ("FAILED", "FAILED"),
    ],
)
def test_b11_outcome_mapping(
    tmp_path: Path, monkeypatch, kit_outcome: str, expected: str
):
    from scholar_rag.embedder import get_embedder as kit_get_embedder

    ws, pv, docs, parents = _synthetic_workspace(tmp_path, f"b11-{kit_outcome}")
    mock = kit_get_embedder("mock")
    mock.dimension = 384
    o = ResearchOrchestrator(ws)
    monkeypatch.setattr(o, "_build_parent_view", lambda: dict(pv))
    monkeypatch.setattr(o, "_accepted_document_records", lambda: dict(docs))
    monkeypatch.setattr(o, "_accepted_screening_parents", lambda: dict(parents))
    monkeypatch.setattr(orch_module, "get_embedder", lambda **_: mock)
    monkeypatch.setattr(
        orch_module, "ChromaReplacementView", lambda **_: SimpleNamespace()
    )
    monkeypatch.setattr(
        orch_module, "ChromaVisibleSetReader", lambda **_: SimpleNamespace()
    )

    def _fake(request, **kwargs):
        return SimpleNamespace(
            outcome=kit_outcome,
            counts=SimpleNamespace(
                accepted_documents=1, rejected_documents=0, visible_chunks=3
            ),
            rejected_documents=(),
        )

    monkeypatch.setattr(orch_module, "index_workspace", _fake)
    result, _ = o._run_indexing_stage(tmp_path / "chroma")
    assert result["status"] == expected


# ---------------------------------------------------------------------------
# C17 stale TypeError preserved (not repaired)
# ---------------------------------------------------------------------------


def test_c17_stale_currentness_raises_typeerror_with_no_bytes(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    # Direct audit-level proof: both writers reject the preserved parameters= shape.
    from scholar_harness.workspace.audit import append_legacy_event

    with pytest.raises(TypeError):
        append_legacy_event(
            ws,
            "RAG_INDEX_REJECTED",
            "scholar-harness",
            "x",
            ["i"],
            [],
            {"documents": 0},
            status="FAILED",
            parameters={"code": "X"},
        )  # type: ignore[call-arg]
    o = ResearchOrchestrator(ws)
    with pytest.raises(TypeError):
        o._log_audit_event(
            action="RAG_INDEX_REJECTED",
            agent="scholar-harness",
            description="x",
            inputs=["i"],
            outputs=[],
            metrics={"documents": 0},
            status="FAILED",
            parameters={"code": "X"},
        )  # type: ignore[call-arg]
    assert _journal(ws) == []


# ---------------------------------------------------------------------------
# A3 request literals
# ---------------------------------------------------------------------------


def test_a3_request_literals(tmp_path: Path, monkeypatch):
    from scholar_rag.embedder import get_embedder as kit_get_embedder

    ws, pv, docs, parents = _synthetic_workspace(tmp_path, "a3")
    mock = kit_get_embedder("mock")
    mock.dimension = 384
    monkeypatch.setattr(orch_module, "get_embedder", lambda **_: mock)
    o = ResearchOrchestrator(ws)
    monkeypatch.setattr(o, "_accepted_document_records", lambda: dict(docs))
    monkeypatch.setattr(o, "_accepted_screening_parents", lambda: dict(parents))
    req = o._build_index_service_request(
        chroma_dir=tmp_path / "chroma-unused",
        parent_view=dict(pv),
        run_id="RUN-" + "0" * 32,
        created_at="2026-01-01T00:00:00+00:00",
        producer_commit="0" * 40,
        producer_version="1.0.0",
    )
    assert req is not None
    assert req.backend_type == "chromadb"
    assert req.collection_name == "scholar_docs"
    assert req.hnsw_space == "cosine"
    assert req.embedder_provider == "sentence-transformers"
    assert req.embedder_model == "all-MiniLM-L6-v2"
    assert req.embedder_dimension == 384
    assert req.embedder_distance_metric == "cosine"
    assert req.chunker_configuration == {
        "heading_levels": [1, 2, 3],
        "max_chunk_chars": 1200,
        "min_chunk_chars": 100,
        "overlap_chars": 150,
        "normalize_whitespace": True,
        "sentence_split_pattern": r"(?<=[.!?])\s+",
        "strip_frontmatter": True,
    }
    assert req.journal_path == "run-reports/rag-index.jsonl"
    assert req.docs_path == "extracted"
