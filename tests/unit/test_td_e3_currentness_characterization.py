"""TD-E3-CURRENTNESS-01, the part that outlived Stage 6 indexing.

The Stage-6 stale-currentness matrices (B, C, D and the negatives) left with
``scholar_rag`` and the indexing stage in H-remove-rag-verify (2026-11-23).
What stays guards code that is still here: the legacy audit writer and the
orchestrator adapter reject an unsupported ``parameters=`` keyword (A1, A2),
and the extraction producer raises the typed ``STALE_EXTRACTED_BODY``
refusal for a changed body (A4).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scholar_harness.orchestrator import ResearchOrchestrator

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
