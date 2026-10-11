"""TD-E3-CURRENTNESS-01 characterization: stale-currentness `parameters=` TypeError.

Status: CHARACTERIZATION ONLY. No runtime change, no repair, no mitigation.

Target (base `origin/main` `dab85b4`):
  `src/scholar_harness/pipeline/indexing.py:530-539` calls
  `append_legacy_event(..., parameters={"code": exc.code})` with
  `# type: ignore[call-arg]`; neither `workspace.audit.append_legacy_event`
  nor `ResearchOrchestrator._log_audit_event` accepts `parameters`.

Packet mapping (entry paths 1-10, all classified by EXECUTION below):
  (1) direct `pipeline.indexing.run_indexing` with controlled stale parent_view
  (2) coordinator/orchestrator full-pipeline route (`_run_indexing_stage` delegate)
  (3) CLI `extract index` -> `extraction_producer.index_accepted_documents`
      (:1648; preflight `validate` :1695 BEFORE `orch._run_indexing_stage` :1697)
  (4) `agent_extract` same-producer path
  (5) `index_acceptance.py:658-666` preflight context (check 4)
  (6) valid-accepted-stale | (7) missing-manifest | (8) missing-source-parent
  (9) no-documents | (10) mixed-batch-stale / reuse-rebuild

Matrices:
  A: mechanism (bad-keyword, not missing-param/shape; harness owner, not kit)
  B: direct stale reachability + replay stability (paths 1-2, shape 6)
  C: earlier-path / unreachable classification (paths 3-5)
  D: consequence snapshots for spec shapes (6-10)
  NEG: five hermetic negatives incl. missing-manifest-takes-earlier-path,
       each with before/after snapshot; stale path asserts byte-identical
       (no publication); refusal paths assert exactly-one-line delta with
       prior bytes preserved; every negative restores no residue outside tmp.

Labels: REAL-KIT / HARNESS-INTEGRATION / CONTROLLED-DOUBLE / SOURCE-TRACE /
  UNPROVEN. Doubles are labeled and never presented as production evidence.
  No network. tmp_path only. Controlled stale is injected by monkeypatching
  `scholar_harness.extraction_producer.validate_extraction_currentness` to raise
  the kit's real typed `PublicationRefused("STALE_EXTRACTED_BODY", ...)`; the
  kit's own raise is proven real in A4 with a hand-built publication record.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from scholar_harness import orchestrator as orch_module
from scholar_harness.orchestrator import ResearchOrchestrator
from scholar_harness.pipeline import indexing as idx_mod

FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32


def _record_identity(ws: Path) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "td-currentness-test",
                "registered_workspace_id": FIXTURE_WORKSPACE_ID,
            }
        ),
        encoding="utf-8",
    )


def _journal_lines(ws: Path) -> list[dict]:
    p = ws / "audit" / "journal.jsonl"
    if not p.is_file():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _journal_bytes(ws: Path) -> bytes:
    p = ws / "audit" / "journal.jsonl"
    return p.read_bytes() if p.is_file() else b""


def _snapshot(ws: Path) -> dict[str, Any]:
    journal = ws / "audit" / "journal.jsonl"
    registry = ws / "audit" / "artifact_registry.json"
    accepted = ws / "rag" / "index" / "accepted.json"
    chroma = ws / "rag" / "chroma_db"
    rag = ws / "rag"
    return {
        "journal_bytes": journal.read_bytes() if journal.is_file() else b"",
        "journal_lines": _journal_lines(ws),
        "registry_bytes": registry.read_bytes() if registry.is_file() else None,
        "project_bytes": (ws / "project.json").read_bytes()
        if (ws / "project.json").is_file()
        else None,
        "chroma_exists": chroma.exists(),
        "rag_exists": rag.exists(),
        "accepted_exists": accepted.is_file(),
        "tmp_leftovers": sorted(str(p.relative_to(ws)) for p in ws.rglob("*.tmp-*"))
        if ws.exists()
        else [],
    }


def _fake_parent_view(documents: list[dict] | None = None) -> dict[str, Any]:
    return {
        "artifact_id": "ART-" + "a" * 8,
        "artifact_type": "document_manifest",
        "sha256": "sha256:" + "b" * 64,
        "workspace_id": FIXTURE_WORKSPACE_ID,
        "protocol_fingerprint": "sha256:" + "c" * 64,
        "corpus_fingerprint": "sha256:" + "d" * 64,
        "documents": documents if documents is not None else [],
    }


def _boom_backend(**kwargs: Any) -> Any:
    raise AssertionError("backend must not be constructed on a refused run")


def _stale_raise(workspace: Path, artifact_id: str) -> None:
    from scholar_harness.extraction_producer import PublicationRefused

    raise PublicationRefused(
        "STALE_EXTRACTED_BODY",
        "Extracted bytes differ from the accepted E2 publication (controlled double).",
        artifact_id=artifact_id,
    )


# ---------------------------------------------------------------------------
# Matrix A — mechanism: bad-keyword, harness owner, kit raises typed correctly
# ---------------------------------------------------------------------------


def test_a1_append_legacy_event_rejects_parameters_keyword(tmp_path: Path):
    """A1 (HARNESS-INTEGRATION): real writer rejects `parameters=` (bad-keyword)."""
    from scholar_harness.workspace.audit import append_legacy_event

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    before = _snapshot(ws)
    with pytest.raises(TypeError) as caught:
        append_legacy_event(
            ws,
            "RAG_INDEX_REJECTED",
            "scholar-harness",
            "x",
            ["i"],
            [],
            {"documents": 0},
            status="FAILED",
            parameters={"code": "X"},  # type: ignore[call-arg]
        )
    assert "unexpected keyword argument 'parameters'" in str(caught.value)
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"] == b""
    assert after["journal_lines"] == []
    assert after["tmp_leftovers"] == []


def test_a2_orchestrator_adapter_rejects_parameters_keyword(tmp_path: Path):
    """A2 (HARNESS-INTEGRATION): orchestrator adapter rejects the same keyword."""
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    before = _snapshot(ws)
    o = ResearchOrchestrator(ws)
    with pytest.raises(TypeError) as caught:
        o._log_audit_event(
            action="RAG_INDEX_REJECTED",
            agent="scholar-harness",
            description="x",
            inputs=["i"],
            outputs=[],
            metrics={"documents": 0},
            status="FAILED",
            parameters={"code": "X"},  # type: ignore[call-arg]
        )
    assert "unexpected keyword argument 'parameters'" in str(caught.value)
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"] == b""


def test_a3_neither_writer_signature_accepts_parameters():
    """A3 (SOURCE-TRACE): both signatures lack `parameters` (not missing-param)."""
    from scholar_harness.workspace.audit import append_legacy_event

    assert "parameters" not in inspect.signature(append_legacy_event).parameters
    assert (
        "parameters"
        not in inspect.signature(ResearchOrchestrator._log_audit_event).parameters
    )
    # The stale call site carries the explicit ignore marker (preserved defect).
    src = Path(idx_mod.__file__).read_text(encoding="utf-8")
    assert 'parameters={"code": exc.code}' in src
    assert "# type: ignore[call-arg]" in src


def test_a4_kit_validate_raises_typed_stale_for_changed_body(tmp_path: Path):
    """A4 (REAL-KIT): kit `validate_extraction_currentness` raises typed STALE.

    Hand-built publication record + real extracted file: the recorded hash is
    stale, the file changed. The kit raises `PublicationRefused` with code
    `STALE_EXTRACTED_BODY` (not TypeError, not None). Proves the harness call
    construction owns the TypeError, not the kit.
    """
    from scholar_pdf.frontmatter import sha256_bytes
    from scholar_harness.extraction_producer import (
        PublicationRefused,
        validate_extraction_currentness,
    )

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    artifact_id = "ART-" + "c" * 8
    pub_dir = ws / "literature" / "extraction_publications"
    pub_dir.mkdir(parents=True, exist_ok=True)
    ext_dir = ws / "extracted"
    ext_dir.mkdir(parents=True, exist_ok=True)
    rel = "extracted/DOC-001.md"
    (ws / rel).write_text("## Abstract\n\nOriginal body text.\n", encoding="utf-8")
    recorded_hash = sha256_bytes(b"## Abstract\n\nA different published body.\n")
    (pub_dir / f"{artifact_id}.json").write_text(
        json.dumps(
            {
                "artifact_id": artifact_id,
                "documents": [
                    {
                        "document_id": "DOC-001",
                        "extracted_path": rel,
                        "extracted_file_sha256": recorded_hash,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(PublicationRefused) as caught:
        validate_extraction_currentness(ws, artifact_id)
    assert caught.value.code == "STALE_EXTRACTED_BODY"
    assert "Extracted bytes differ" in str(caught.value)


# ---------------------------------------------------------------------------
# Matrix B — direct stale reachability (paths 1-2, shape 6) + replay
# ---------------------------------------------------------------------------


def test_b1_run_indexing_stale_raises_typeerror_with_no_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """B1 (HARNESS-INTEGRATION + CONTROLLED-DOUBLE stale): direct path REACHABLE.

    Controlled double: real `run_indexing` + monkeypatched kit stale raise.
    Asserts raw TypeError (not typed/mapped), chained from STALE, with
    before/after snapshots byte-identical and no backend/chroma/accepted.
    """
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    before = _snapshot(ws)
    chroma_dir = ws / "rag" / "chroma_db"
    with pytest.raises(TypeError) as caught:
        idx_mod.run_indexing(
            workspace_dir=ws,
            chroma_dir=chroma_dir,
            get_embedder_fn=_boom_backend,
            backend_cls=_boom_backend,
            reader_cls=_boom_backend,
            index_workspace_fn=_boom_backend,
            parent_view=_fake_parent_view(),
        )
    assert "unexpected keyword argument 'parameters'" in str(caught.value)
    # Chained cause is the kit's typed stale refusal (mechanism proof).
    assert type(caught.value.__context__).__name__ == "PublicationRefused"
    assert getattr(caught.value.__context__, "code", None) == "STALE_EXTRACTED_BODY"
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"] == b""
    assert after["journal_lines"] == []
    assert after["chroma_exists"] is False
    assert after["rag_exists"] is False
    assert after["accepted_exists"] is False
    assert after["tmp_leftovers"] == []
    assert after["registry_bytes"] == before["registry_bytes"]


def test_b2_orchestrator_stage_stale_raises_typeerror_with_no_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """B2 (HARNESS-INTEGRATION): orchestrator delegate path REACHABLE (same shape).

    Patches the orchestrator's data seam to supply the controlled stale
    parent_view plus the kit stale raise; asserts the same raw TypeError and
    the same no-publication observables. Covers entry path (2) via the thin
    delegate `orch._run_indexing_stage` (coordinator calls this same fn).
    """
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    o = ResearchOrchestrator(ws)
    monkeypatch.setattr(o, "_build_parent_view", lambda: _fake_parent_view())
    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom_backend)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom_backend)
    monkeypatch.setattr(orch_module, "get_embedder", _boom_backend)
    monkeypatch.setattr(orch_module, "index_workspace", _boom_backend)
    before = _snapshot(ws)
    with pytest.raises(TypeError) as caught:
        o._run_indexing_stage(tmp_path / "chroma-orch")
    assert "unexpected keyword argument 'parameters'" in str(caught.value)
    assert getattr(caught.value.__context__, "code", None) == "STALE_EXTRACTED_BODY"
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"] == b""
    assert not (tmp_path / "chroma-orch").exists()
    assert after["accepted_exists"] is False


def test_b3_stale_replay_still_typeerror_still_no_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """B3 (HARNESS-INTEGRATION): replay stability — two runs, same TypeError."""
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    before = _snapshot(ws)
    for _ in range(2):
        with pytest.raises(TypeError, match="unexpected keyword argument"):
            idx_mod.run_indexing(
                workspace_dir=ws,
                chroma_dir=ws / "rag" / "chroma_db",
                get_embedder_fn=_boom_backend,
                backend_cls=_boom_backend,
                reader_cls=_boom_backend,
                index_workspace_fn=_boom_backend,
                parent_view=_fake_parent_view(),
            )
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"] == b""
    assert after["chroma_exists"] is False


# ---------------------------------------------------------------------------
# Matrix C — earlier-path classification (paths 3-5): typed first, no TypeError
# ---------------------------------------------------------------------------


def test_c1_producer_preflight_raises_typed_before_orchestrator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """C1 (CONTROLLED-DOUBLE): CLI/agent producer path UNREACHABLE for stale.

    `index_accepted_documents` validates (:1695) BEFORE `orch._run_indexing_stage`
    (:1697). Controlled doubles: fake context + one manifest id + stale raise +
    boom orchestrator. Asserts typed `STALE_EXTRACTED_BODY` (not TypeError) and
    the orchestrator was never entered; no journal/chroma. Covers paths (3)+(4)
    at the shared producer (both CLI `extract index` and `agent_extract index`
    call this one function — see SOURCE-TRACE C2/C3).
    """
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    fake_context = type(
        "Ctx",
        (),
        {
            "workspace_id": FIXTURE_WORKSPACE_ID,
            "protocol_fingerprint": "p",
            "corpus_fingerprint": "c",
        },
    )()
    monkeypatch.setattr(
        prod, "build_acceptance_context", lambda workspace: fake_context
    )
    monkeypatch.setattr(prod, "_load_registry", lambda workspace: object())
    monkeypatch.setattr(
        prod, "_accepted_manifest_ids", lambda workspace, registry, context: ["ART-1"]
    )
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    called = {"orch": False}

    def _boom_stage(self: Any, target: Any) -> Any:
        called["orch"] = True
        raise AssertionError("orchestrator must not run after stale preflight")

    monkeypatch.setattr(ResearchOrchestrator, "_run_indexing_stage", _boom_stage)
    before = _snapshot(ws)
    with pytest.raises(prod.PublicationRefused) as caught:
        prod.index_accepted_documents(ws)
    assert caught.value.code == "STALE_EXTRACTED_BODY"
    assert called["orch"] is False
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"] == b""
    assert after["chroma_exists"] is False
    assert after["rag_exists"] is False


def test_c2_cli_extract_index_maps_typed_to_stage6_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """C2 (CONTROLLED-DOUBLE + SOURCE-TRACE): CLI maps typed, never TypeError."""
    import scholar_harness.extraction_producer as prod
    from scholar_harness import cli as cli_module

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)

    def _raise_stale(workspace: Path) -> Any:
        raise prod.PublicationRefused(
            "STALE_EXTRACTED_BODY", "stale preflight (controlled double)"
        )

    monkeypatch.setattr(prod, "index_accepted_documents", _raise_stale)
    result, exit_code = cli_module._extract_index(str(ws), 0)
    assert result.get("stage6_refused") is True
    assert result.get("status") == "FAILED"
    assert result.get("code") == "STALE_EXTRACTED_BODY"
    assert exit_code == 1


def test_c3_agent_extract_maps_typed_to_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """C3 (CONTROLLED-DOUBLE + SOURCE-TRACE): agent path shares producer, same map."""
    import scholar_harness.extraction_producer as prod
    from scholar_harness import agent_extract as agent_module

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)

    def _raise_stale(workspace: Path) -> Any:
        raise prod.PublicationRefused(
            "STALE_EXTRACTED_BODY", "stale preflight (controlled double)"
        )

    monkeypatch.setattr(prod, "index_accepted_documents", _raise_stale)
    monkeypatch.setattr(agent_module, "index_accepted_documents", _raise_stale)
    emitted: dict[str, Any] = {}
    monkeypatch.setattr(
        agent_module, "_emit", lambda payload, as_json: emitted.update(payload)
    )
    rc = agent_module._cmd_index(ws, True)
    assert rc == 1
    assert "indexing_refused" in emitted
    assert emitted["indexing_refused"]["code"] == "STALE_EXTRACTED_BODY"
    # Source-trace: both entry points call the one shared producer function.
    import inspect as _inspect

    assert "index_accepted_documents" in _inspect.getsource(agent_module._cmd_index)
    assert "index_accepted_documents" in _inspect.getsource(
        __import__("scholar_harness.cli", fromlist=["_extract_index"])._extract_index
    )


def test_c4_index_acceptance_maps_stale_to_step4_validation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """C4 (HARNESS-INTEGRATION + CONTROLLED-DOUBLE validate): adapter path SEPARATE.

    Minimal registry + parent payload passing checks 1-3; controlled stale
    raise at check 4 (`index_acceptance.py:663-666`). Asserts typed
    `IndexAcceptanceResult(accepted=False, failing_step=4,
    code=VALIDATION_ERROR)` — never TypeError — with zero publication
    (no accepted record, no journal line, prior bytes preserved).
    """
    from scholar_harness.contracts.canonical import canonical_fingerprint
    from scholar_harness.contracts.models import DocumentManifestArtifact
    from scholar_harness.index_acceptance import accept_index_candidate
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    ws_id = FIXTURE_WORKSPACE_ID
    proto_fp = "sha256:" + "1" * 64
    corpus_fp = "sha256:" + "2" * 64
    parent_id = "ART-" + "d" * 8
    parent_payload = {
        "schema_version": "1.0.0",
        "artifact_type": "document_manifest",
        "artifact_id": parent_id,
        "workspace_id": ws_id,
        "protocol_fingerprint": proto_fp,
        "corpus_fingerprint": corpus_fp,
        "run_id": "RUN-" + "e" * 8,
        "created_at": "2026-01-01T00:00:00+00:00",
        "producer": {"package": "p", "version": "1.0.0", "commit": "0" * 40},
        "inputs": [],
        "data": {
            "documents": [
                {
                    "document_id": "DOC-001",
                    "study_id": "STU-001",
                    "source_hash": "sha256:" + "f" * 64,
                    "content_status": "VALID",
                    "extracted_path": "extracted/DOC-001.md",
                    "extraction_method": "DETERMINISTIC_RULE",
                }
            ]
        },
    }
    DocumentManifestArtifact.model_validate(parent_payload)
    parent_hash = canonical_fingerprint(parent_payload)
    artifacts_dir = ws / "artifacts" / "document_manifest"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    rel_parent = "artifacts/document_manifest/payload.json"
    (ws / rel_parent).write_text(json.dumps(parent_payload), encoding="utf-8")
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "artifact_registry.json").write_text(
        json.dumps(
            {
                "artifacts": {
                    parent_id: {
                        "artifact_type": "document_manifest",
                        "path": rel_parent,
                        "sha256": parent_hash,
                        "accepted_at": "2026-01-01T00:00:00+00:00",
                        "run_id": "RUN-" + "e" * 8,
                        "producer": {
                            "package": "p",
                            "version": "1.0.0",
                            "commit": "0" * 40,
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    candidate = {
        "parent_artifact_ref": {
            "artifact_id": parent_id,
            "sha256": parent_hash,
            "artifact_type": "document_manifest",
        },
        "workspace_id": ws_id,
        "protocol_fingerprint": proto_fp,
        "corpus_fingerprint": corpus_fp,
        "manifest_id": "IDX-" + "0" * 8,
        "index_fingerprint": "sha256:" + "3" * 64,
        "documents": [{"document_id": "DOC-001", "study_id": "STU-001"}],
        "rejected_documents": [],
        "counts": {
            "accepted_documents": 1,
            "rejected_documents": 0,
            "visible_chunks": 1,
        },
    }
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    before = _snapshot(ws)
    result = accept_index_candidate(
        ws,
        candidate,
        run_id="RUN-" + "9" * 8,
        manifest_path="rag/index/sidecar.json",
        reader=object(),
    )
    assert result.accepted is False
    assert result.failing_step == 4
    assert result.code == "VALIDATION_ERROR"
    assert "STALE_EXTRACTED_BODY" in (result.detail or "")
    after = _snapshot(ws)
    assert after["accepted_exists"] is False
    assert after["journal_bytes"] == before["journal_bytes"] == b""


# ---------------------------------------------------------------------------
# Matrix D — consequence snapshots for spec shapes 6-10
# ---------------------------------------------------------------------------


def test_d1_stale_consequence_table_is_no_publication_no_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """D1: full consequence row for valid-accepted-stale (shape 6, path 1)."""
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    before = _snapshot(ws)
    with pytest.raises(TypeError):
        idx_mod.run_indexing(
            workspace_dir=ws,
            chroma_dir=ws / "rag" / "chroma_db",
            get_embedder_fn=_boom_backend,
            backend_cls=_boom_backend,
            reader_cls=_boom_backend,
            index_workspace_fn=_boom_backend,
            parent_view=_fake_parent_view(
                documents=[
                    {
                        "document_id": "DOC-001",
                        "study_id": "STU-001",
                        "extracted_path": "extracted/DOC-001.md",
                        "extracted_content_sha256": "sha256:" + "9" * 64,
                    }
                ]
            ),
        )
    after = _snapshot(ws)
    # backend/client constructed? No (boom would have raised AssertionError).
    # index/replacement started? No chroma/rag. manifest/accepted? No.
    # audit event? None. journal bytes? Unchanged. residue? None.
    # result? Raw TypeError (not typed PublicationRefused, not mapped dict).
    assert after == before
    assert after["journal_bytes"] == b""


def test_d2_missing_manifest_takes_earlier_path_with_one_rejection_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """D2/NEG-01 (shape 7): missing-manifest bypasses stale, writes one line."""
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom_backend)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom_backend)
    monkeypatch.setattr(orch_module, "get_embedder", _boom_backend)
    monkeypatch.setattr(orch_module, "index_workspace", _boom_backend)
    before = _snapshot(ws)
    out = idx_mod.run_indexing(
        workspace_dir=ws,
        chroma_dir=ws / "rag" / "chroma_db",
        get_embedder_fn=_boom_backend,
        backend_cls=_boom_backend,
        reader_cls=_boom_backend,
        index_workspace_fn=_boom_backend,
        parent_view=None,
    )
    assert out.result["status"] == "FAILED"
    assert out.result["refused"] == [
        {"document_id": "", "reason": "no accepted document_manifest"}
    ]
    after = _snapshot(ws)
    assert len(after["journal_lines"]) == len(before["journal_lines"]) + 1
    evt = after["journal_lines"][-1]
    assert evt["action"] == "RAG_INDEX_REJECTED"
    assert evt["status"] == "FAILED"
    assert evt["metrics"]["rejection_code"] == "DOCUMENT_MANIFEST_NOT_ACCEPTED"
    assert after["chroma_exists"] is False
    assert after["accepted_exists"] is False
    assert after["tmp_leftovers"] == []
    # Prior bytes preserved (append-only, byte-identical prefix).
    assert after["journal_bytes"].startswith(before["journal_bytes"])


def test_d3_no_documents_is_failed_never_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """D3 (shape 9): empty sources -> NO_DOCUMENTS_TO_INDEX, FAILED never SUCCESS."""
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prod, "validate_extraction_currentness", lambda w, a: None)
    before = _snapshot(ws)
    out = idx_mod.run_indexing(
        workspace_dir=ws,
        chroma_dir=tmp_path / "chroma-empty",
        get_embedder_fn=_boom_backend,
        backend_cls=_boom_backend,
        reader_cls=_boom_backend,
        index_workspace_fn=_boom_backend,
        parent_view=_fake_parent_view(),
        documents={},
        screening_parents={},
    )
    assert out.result["status"] == "FAILED"
    assert out.result["status"] != "SUCCESS"
    assert out.result["refused"] == [
        {"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}
    ]
    assert not (tmp_path / "chroma-empty").exists()
    after = _snapshot(ws)
    assert len(after["journal_lines"]) == len(before["journal_lines"]) + 1
    assert after["journal_lines"][-1]["metrics"]["rejection_code"] == (
        "NO_DOCUMENTS_TO_INDEX"
    )


def test_d4_blank_study_never_reuses_workspace_limb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """D4 (shape 8: missing-source-parent): blank study skipped, never WSP limb."""
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prod, "validate_extraction_currentness", lambda w, a: None)
    out = idx_mod.run_indexing(
        workspace_dir=ws,
        chroma_dir=tmp_path / "chroma-blank",
        get_embedder_fn=_boom_backend,
        backend_cls=_boom_backend,
        reader_cls=_boom_backend,
        index_workspace_fn=_boom_backend,
        parent_view=_fake_parent_view(),
        documents={
            "DOC-nostudy": {
                "study_id": "   ",
                "extracted_path": "extracted/x.md",
                "parent_artifact_id": "ART-x",
                "parent_artifact_sha256": "sha256:" + "8" * 64,
            }
        },
        screening_parents={},
    )
    assert out.result["status"] == "FAILED"
    assert out.result["refused"] == [
        {"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}
    ]
    assert FIXTURE_WORKSPACE_ID not in json.dumps(out.result)


# ---------------------------------------------------------------------------
# NEGATIVES: five hermetic probes with before/after snapshot discipline
# ---------------------------------------------------------------------------


def test_neg01_missing_manifest_takes_earlier_path_no_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """NEG-01: missing-manifest never reaches stale validate (earlier path)."""
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    seen = {"validate": False}

    def _tracking_validate(workspace: Path, artifact_id: str) -> None:
        seen["validate"] = True

    monkeypatch.setattr(prod, "validate_extraction_currentness", _tracking_validate)
    before = _snapshot(ws)
    out = idx_mod.run_indexing(
        workspace_dir=ws,
        chroma_dir=ws / "rag" / "chroma_db",
        parent_view=None,
    )
    assert seen["validate"] is False
    assert out.result["status"] == "FAILED"
    after = _snapshot(ws)
    assert len(after["journal_lines"]) == len(before["journal_lines"]) + 1
    assert after["journal_bytes"].startswith(before["journal_bytes"])
    assert after["tmp_leftovers"] == []


def test_neg02_identity_refusal_leaves_bytes_and_store_untouched(tmp_path: Path):
    """NEG-02: missing identity raises before backend, bytes unchanged."""
    from scholar_harness.workspace.errors import RegisteredWorkspaceIdentityMissingError

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps({"project_id": "x"}), encoding="utf-8")
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    pj_before = (ws / "project.json").read_bytes()
    journal_before = (ws / "audit" / "journal.jsonl").read_bytes()
    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        idx_mod.run_indexing(workspace_dir=ws, chroma_dir=ws / "rag" / "chroma_db")
    assert (ws / "project.json").read_bytes() == pj_before
    assert (ws / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert not (ws / "rag" / "chroma_db").exists()


def test_neg03_refused_run_never_touches_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """NEG-03: refused run never constructs backend (boom on any touch)."""
    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)

    def _boom(**kwargs: Any) -> Any:
        raise AssertionError("refused run touched the backend")

    monkeypatch.setattr(orch_module, "ChromaReplacementView", _boom)
    monkeypatch.setattr(orch_module, "ChromaVisibleSetReader", _boom)
    monkeypatch.setattr(orch_module, "get_embedder", _boom)
    monkeypatch.setattr(orch_module, "index_workspace", _boom)
    before = _snapshot(ws)
    result, _ = ResearchOrchestrator(ws)._run_indexing_stage(ws / "rag" / "chroma_db")
    assert result["status"] == "FAILED"
    after = _snapshot(ws)
    assert after["chroma_exists"] is False
    assert after["rag_exists"] is False
    assert len(after["journal_lines"]) == len(before["journal_lines"]) + 1


def test_neg04_stale_exception_path_writes_no_bytes_restores_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """NEG-04: stale exception path snapshot is byte-identical (no publication)."""
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    # Seed one unrelated journal line to prove prefix preservation (still none new).
    from scholar_harness.workspace.audit import append_legacy_event

    append_legacy_event(
        ws,
        "RAG_INDEX_REJECTED",
        "scholar-harness",
        "seed line (unrelated refusal)",
        ["i"],
        [],
        {"indexed_files": 0},
        status="FAILED",
    )
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    before = _snapshot(ws)
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        idx_mod.run_indexing(
            workspace_dir=ws,
            chroma_dir=ws / "rag" / "chroma_db",
            get_embedder_fn=_boom_backend,
            backend_cls=_boom_backend,
            reader_cls=_boom_backend,
            index_workspace_fn=_boom_backend,
            parent_view=_fake_parent_view(),
        )
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"]
    assert after["journal_lines"] == before["journal_lines"]
    assert after["tmp_leftovers"] == []


def test_neg05_mixed_batch_stale_still_typeerror_no_partial_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """NEG-05 (shape 10): multi-doc stale parent still TypeError, no PARTIAL."""
    import scholar_harness.extraction_producer as prod

    ws = tmp_path / "ws"
    ws.mkdir()
    _record_identity(ws)
    (ws / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(prod, "validate_extraction_currentness", _stale_raise)
    before = _snapshot(ws)
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        idx_mod.run_indexing(
            workspace_dir=ws,
            chroma_dir=ws / "rag" / "chroma_db",
            get_embedder_fn=_boom_backend,
            backend_cls=_boom_backend,
            reader_cls=_boom_backend,
            index_workspace_fn=_boom_backend,
            parent_view=_fake_parent_view(
                documents=[
                    {
                        "document_id": "DOC-001",
                        "study_id": "STU-001",
                        "extracted_path": "extracted/DOC-001.md",
                        "extracted_content_sha256": "sha256:" + "1" * 64,
                    },
                    {
                        "document_id": "DOC-002",
                        "study_id": "STU-002",
                        "extracted_path": "extracted/DOC-002.md",
                        "extracted_content_sha256": "sha256:" + "2" * 64,
                    },
                ]
            ),
        )
    after = _snapshot(ws)
    assert after["journal_bytes"] == before["journal_bytes"] == b""
    assert after["accepted_exists"] is False
