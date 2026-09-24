from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_FIXTURE = (
    ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)


def _workspace(tmp_path: Path) -> tuple[Path, dict]:
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


def test_prepare_and_collect_publish_bound_idempotent_artifacts(tmp_path: Path) -> None:
    workspace, study = _workspace(tmp_path)

    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    batch = json.loads((screening / "batch_001.json").read_text(encoding="utf-8"))
    assert batch["artifact_id"].startswith("ART-")
    assert batch["binding"]["protocol_fingerprint"] == canonical_fingerprint(
        ResearchProtocol.model_validate(
            json.loads((workspace / "protocol.json").read_text(encoding="utf-8"))
        )
    )

    decisions_path = screening / "batch_001_decisions.json"
    decisions_path.write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "human-reviewer-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "decisions": [
                    {
                        "workspace_id": study["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "screening_reasoning": "Matches the frozen criteria.",
                        "parent_decision_ids": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    cmd_collect(workspace)
    first_registry = json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    decision_entries = [
        entry
        for entry in first_registry["artifacts"].values()
        if entry["artifact_type"] == "screening_decisions"
    ]
    assert len(decision_entries) == 1
    payload = json.loads(
        (workspace / decision_entries[0]["path"]).read_text(encoding="utf-8")
    )
    decision = payload["data"]["decisions"][0]
    assert decision["screener_id"] == "human-reviewer-1"
    assert decision["method"] == "HUMAN"
    assert (screening / "legacy" / decisions_path.name).is_file()

    cmd_collect(workspace)
    second_registry = json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    assert second_registry["artifacts"].keys() == first_registry["artifacts"].keys()


def test_collect_fails_closed_when_decision_file_is_missing(tmp_path: Path) -> None:
    workspace, _ = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)

    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)

    literature = workspace / "literature"
    assert not (literature / "included.json").exists()
    assert not (literature / "excluded.json").exists()
    registry = json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    assert all(
        entry["artifact_type"] != "screening_decisions"
        for entry in registry["artifacts"].values()
    )


def test_dual_screening_preserves_source_and_parent_lineage(tmp_path: Path) -> None:
    workspace, study = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    common = {
        "workspace_id": study["study_id"],
        "decision": "INCLUDE",
        "method": "HUMAN",
        "screening_reasoning": "Meets all frozen criteria.",
    }
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {
                    **common,
                    "decision_id": "SCR-screener-1",
                    "screener_id": "reviewer-1",
                    "decided_at": "2026-09-21T12:00:00Z",
                }
            ]
        ),
        encoding="utf-8",
    )
    (screening / "batch_001_decisions_screener2.json").write_text(
        json.dumps(
            [
                {
                    **common,
                    "decision_id": "SCR-screener-2",
                    "screener_id": "reviewer-2",
                    "decided_at": "2026-09-21T12:01:00Z",
                }
            ]
        ),
        encoding="utf-8",
    )
    (screening / "_adjudication_resolved_group_001.json").write_text(
        "[]", encoding="utf-8"
    )

    cmd_collect(workspace)

    registry = json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    entry = next(
        item
        for item in registry["artifacts"].values()
        if item["artifact_type"] == "screening_decisions"
    )
    artifact = json.loads((workspace / entry["path"]).read_text(encoding="utf-8"))
    decisions = artifact["data"]["decisions"]
    assert {item["decision_id"] for item in decisions[:2]} == {
        "SCR-screener-1",
        "SCR-screener-2",
    }
    final = decisions[-1]
    assert final["method"] == "COMPOSED"
    assert set(final["parent_decision_ids"]) == {
        "SCR-screener-1",
        "SCR-screener-2",
    }


def test_dual_screening_fails_closed_without_source_provenance(tmp_path: Path) -> None:
    workspace, study = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    incomplete = [{"workspace_id": study["study_id"], "decision": "INCLUDE"}]
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(incomplete), encoding="utf-8"
    )
    (screening / "batch_001_decisions_screener2.json").write_text(
        json.dumps(incomplete), encoding="utf-8"
    )
    (screening / "_adjudication_resolved_group_001.json").write_text(
        "[]", encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="missing contract provenance fields"):
        cmd_collect(workspace)

    assert not (workspace / "literature" / "included.json").exists()
