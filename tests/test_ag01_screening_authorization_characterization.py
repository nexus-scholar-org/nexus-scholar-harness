"""AG-01 characterization: what the screening handoff enforces today.

Read-only behavioral evidence for
``docs/architecture/agent-controls/archive/ag-01-authorization-readiness.md``. Every test below
demonstrates CURRENT harness behavior on synthetic ``tmp_path`` workspaces —
no real research workspace is touched, no production behavior is changed, and
no test asserts an authorization property the harness does not have.

Conventions used here are defined by the inspected code at the AG-01 base:

* ``reviewed_by`` / ``screener_id`` are free strings with honest fallbacks
  (``batcher.py`` ``_load_decision_payload``; ``collector.py`` single path).
* Single-screener ``collect`` is a 1:1 technical transform of the submitted
  recommendation file into an accepted ``screening_decisions`` artifact plus
  legacy partition outputs. No authorization record exists anywhere in the
  path (``collector.py`` ``cmd_collect`` takes only ``workspace_dir``).
* Membership is validated one direction only (entries ⊆ accepted parent
  batch candidates). There is no exact-coverage check and no duplicate
  rejection in the single path.
* Non-INCLUDE legacy decisions coerce to EXCLUDE (``collector.py``).
"""

from __future__ import annotations

import inspect
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.console.api.screening import DecisionsBody
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect
from scholar_harness.screening.integrity import (
    COVERAGE_INCOMPLETE,
    DUPLICATE_ENTRY,
    UNRESOLVED_FINALIZE_REFUSED,
    ScreeningIntegrityRefused,
    check_exact_coverage,
    check_no_unresolved_for_finalize,
)
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


def _workspace(tmp_path: Path, n_docs: int = 1) -> tuple[Path, list[dict]]:
    """Scaffold a synthetic workspace with ``n_docs`` corpus studies."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "WSP-ag01-characterization", "stats": {}}),
        encoding="utf-8",
    )
    protocol = json.loads(PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    protocol_hash = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    sources = [
        Document(
            title=f"AG-01 synthetic record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"ag01-record-{i}",
            external_ids=ExternalIds(doi=f"10.1000/ag01-{i}"),
            authors=[Author("Reviewer")],
        )
        for i in range(n_docs)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id="WSP-ag01-characterization",
        run_id="RUN-ag01-characterization",
        protocol_fingerprint=protocol_hash,
        created_at=datetime(2026, 10, 11, tzinfo=UTC),
        commit="0" * 40,
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
    studies = list(corpus["data"]["studies"])
    literature = workspace / "literature"
    literature.mkdir()
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {
                        "doi": f"10.1000/ag01-{i}",
                    },
                }
                for i, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )
    return workspace, studies


def _accepted_screening_decisions(workspace: Path) -> list[dict]:
    registry = json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    payloads = []
    for entry in registry["artifacts"].values():
        if entry["artifact_type"] == "screening_decisions":
            payloads.append(
                json.loads((workspace / entry["path"]).read_text(encoding="utf-8"))
            )
    return payloads


def test_forged_reviewed_by_string_is_accepted_as_screener_identity(
    tmp_path: Path,
) -> None:
    """AG-01 negative case: ``reviewed_by`` is a free string, not authority.

    A decision file claiming ``reviewed_by: "professor-x"`` — an actor that
    was never authenticated anywhere — collects successfully and the forged
    string is minted verbatim into the accepted ``ContractDecision``.
    """
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "professor-x",
                "timestamp": "2026-10-11T12:00:00Z",
                "decisions": [
                    {
                        "workspace_id": studies[0]["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "screening_reasoning": "Forged attribution.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    cmd_collect(workspace)

    payloads = _accepted_screening_decisions(workspace)
    assert len(payloads) == 1
    assert payloads[0]["data"]["decisions"][0]["screener_id"] == "professor-x"


def test_publication_happens_with_no_authorization_record_anywhere(
    tmp_path: Path,
) -> None:
    """AG-01 central gap: ``included.json`` publishes with no approval artifact.

    After a successful single-screener collect, the legacy partition outputs
    exist while the registry holds no authorization-typed artifact and no
    authorization file exists anywhere under the workspace.
    """
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": studies[0]["study_id"],
                    "decision": "INCLUDE",
                    "method": "LLM",
                    "screening_reasoning": "Agent recommendation.",
                }
            ]
        ),
        encoding="utf-8",
    )

    cmd_collect(workspace)

    assert (workspace / "literature" / "included.json").is_file()
    registry = json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    assert all(
        "authoriz" not in entry["artifact_type"]
        for entry in registry["artifacts"].values()
    )
    assert not list(workspace.rglob("*authoriz*"))


def test_collect_takes_no_critique_input_and_needs_none(tmp_path: Path) -> None:
    """AG-01 declared-only gate: the critic review is not a collect input.

    ``cmd_collect`` accepts only ``workspace_dir`` — there is no parameter
    through which a critique could even be supplied — and collection succeeds
    while no critique/critic file exists anywhere under the workspace.
    """
    assert list(inspect.signature(cmd_collect).parameters) == ["workspace_dir"]

    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": studies[0]["study_id"],
                    "decision": "EXCLUDE",
                    "method": "LLM",
                    "screening_reasoning": "No critique was ever written.",
                }
            ]
        ),
        encoding="utf-8",
    )

    cmd_collect(workspace)

    assert (workspace / "literature" / "excluded.json").is_file()
    assert not list(workspace.rglob("*critic*"))
    assert not list(workspace.rglob("*critique*"))


def test_coverage_incomplete_file_is_accepted_today(tmp_path: Path) -> None:
    """AG-01 integrity gap, now fail-closed (AG-02 target met).

    Pre-AG-02 characterization (base 86a9478): this input was accepted —
    a 1-of-2 decision file published with the missing study in neither
    partition. Post-AG-02: typed fail-closed refusal COVERAGE_INCOMPLETE.
    Historical evidence retained; assertion updated to prevent regression
    to the defect.
    """
    workspace, studies = _workspace(tmp_path, n_docs=2)
    assert len(studies) == 2
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    decisions_path = screening / "batch_001_decisions.json"
    entry = {
        "workspace_id": studies[0]["study_id"],
        "decision": "INCLUDE",
        "method": "LLM",
        "screening_reasoning": "Only the first candidate was screened.",
    }
    decisions_path.write_text(json.dumps([entry]), encoding="utf-8")

    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)

    journal_path = workspace / "audit" / "journal.jsonl"
    rows = [
        json.loads(line)
        for line in journal_path.read_text(encoding="utf-8").splitlines()
    ]
    refused = [
        row
        for row in rows
        if row.get("action") == "SCREENING_COLLECT_REFUSED"
        and row.get("parameters", {}).get("code") == COVERAGE_INCOMPLETE
    ]
    assert refused, "no SCREENING_COLLECT_REFUSED row with code COVERAGE_INCOMPLETE"
    assert refused[0]["parameters"]["code"] == "COVERAGE_INCOMPLETE"
    assert not decisions_path.exists()
    assert decisions_path.with_name(decisions_path.name + ".rejected").is_file()
    manifest = json.loads((screening / "MANIFEST.json").read_text(encoding="utf-8"))
    assert (
        next(b for b in manifest["batches"] if b["batch_index"] == 1)["status"]
        == "MISSING"
    )
    for name in (
        "included.json",
        "excluded.json",
        "conflicts.json",
        "prisma_screening_report.md",
        "prisma_report.json",
    ):
        assert not (workspace / "literature" / name).exists()
    assert _accepted_screening_decisions(workspace) == []
    with pytest.raises(ScreeningIntegrityRefused) as excinfo:
        check_exact_coverage({s["study_id"] for s in studies}, [entry])
    assert excinfo.value.code == COVERAGE_INCOMPLETE
    assert excinfo.value.code == "COVERAGE_INCOMPLETE"


def test_duplicate_study_entries_are_accepted_today(tmp_path: Path) -> None:
    """AG-01 integrity gap, now fail-closed (AG-02 target met).

    Pre-AG-02 characterization (base 86a9478): this input was accepted —
    two entries for the same study minted two accepted ContractDecision
    records instead of failing closed. Post-AG-02: typed fail-closed
    refusal DUPLICATE_ENTRY. Historical evidence retained; assertion
    updated to prevent regression to the defect.
    """
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    decisions_path = screening / "batch_001_decisions.json"
    entries = [
        {
            "workspace_id": studies[0]["study_id"],
            "decision": "INCLUDE",
            "method": "LLM",
            "screening_reasoning": "First row for the study.",
        },
        {
            "workspace_id": studies[0]["study_id"],
            "decision": "INCLUDE",
            "method": "LLM",
            "screening_reasoning": "Second row for the same study.",
        },
    ]
    decisions_path.write_text(json.dumps(entries), encoding="utf-8")

    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)

    journal_path = workspace / "audit" / "journal.jsonl"
    rows = [
        json.loads(line)
        for line in journal_path.read_text(encoding="utf-8").splitlines()
    ]
    refused = [
        row
        for row in rows
        if row.get("action") == "SCREENING_COLLECT_REFUSED"
        and row.get("parameters", {}).get("code") == DUPLICATE_ENTRY
    ]
    assert refused, "no SCREENING_COLLECT_REFUSED row with code DUPLICATE_ENTRY"
    assert refused[0]["parameters"]["code"] == "DUPLICATE_ENTRY"
    assert not decisions_path.exists()
    assert decisions_path.with_name(decisions_path.name + ".rejected").is_file()
    manifest = json.loads((screening / "MANIFEST.json").read_text(encoding="utf-8"))
    assert (
        next(b for b in manifest["batches"] if b["batch_index"] == 1)["status"]
        == "MISSING"
    )
    for name in (
        "included.json",
        "excluded.json",
        "conflicts.json",
        "prisma_screening_report.md",
        "prisma_report.json",
    ):
        assert not (workspace / "literature" / name).exists()
    assert _accepted_screening_decisions(workspace) == []
    with pytest.raises(ScreeningIntegrityRefused) as excinfo:
        check_exact_coverage({s["study_id"] for s in studies}, entries)
    assert excinfo.value.code == DUPLICATE_ENTRY
    assert excinfo.value.code == "DUPLICATE_ENTRY"


def test_maybe_decision_is_silently_coerced_to_exclude_today(
    tmp_path: Path,
) -> None:
    """AG-01 fidelity gap, now fail-closed (AG-02 target met).

    Pre-AG-02 characterization (base 86a9478): this input was accepted —
    an explicitly unresolved MAYBE judgment was silently coerced to EXCLUDE
    and published as a terminal exclusion. Post-AG-02: typed fail-closed
    refusal UNRESOLVED_FINALIZE_REFUSED. Historical evidence retained;
    assertion updated to prevent regression to the defect.
    """
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    decisions_path = screening / "batch_001_decisions.json"
    entry = {
        "workspace_id": studies[0]["study_id"],
        "decision": "MAYBE",
        "method": "LLM",
        "screening_reasoning": "Cannot tell from the abstract alone.",
    }
    decisions_path.write_text(json.dumps([entry]), encoding="utf-8")

    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)

    journal_path = workspace / "audit" / "journal.jsonl"
    rows = [
        json.loads(line)
        for line in journal_path.read_text(encoding="utf-8").splitlines()
    ]
    refused = [
        row
        for row in rows
        if row.get("action") == "SCREENING_COLLECT_REFUSED"
        and row.get("parameters", {}).get("code") == UNRESOLVED_FINALIZE_REFUSED
    ]
    assert refused, (
        "no SCREENING_COLLECT_REFUSED row with code UNRESOLVED_FINALIZE_REFUSED"
    )
    assert refused[0]["parameters"]["code"] == "UNRESOLVED_FINALIZE_REFUSED"
    assert not decisions_path.exists()
    assert decisions_path.with_name(decisions_path.name + ".rejected").is_file()
    manifest = json.loads((screening / "MANIFEST.json").read_text(encoding="utf-8"))
    assert (
        next(b for b in manifest["batches"] if b["batch_index"] == 1)["status"]
        == "MISSING"
    )
    # The unresolved study appears in neither partition, and no accepted
    # decision coerces it to EXCLUDE: there are no partitions and no
    # accepted screening_decisions artifact at all.
    for name in (
        "included.json",
        "excluded.json",
        "conflicts.json",
        "prisma_screening_report.md",
        "prisma_report.json",
    ):
        assert not (workspace / "literature" / name).exists()
    assert _accepted_screening_decisions(workspace) == []
    with pytest.raises(ScreeningIntegrityRefused) as excinfo:
        check_no_unresolved_for_finalize([entry])
    assert excinfo.value.code == UNRESOLVED_FINALIZE_REFUSED
    assert excinfo.value.code == "UNRESOLVED_FINALIZE_REFUSED"


def test_console_decisions_body_accepts_any_reviewed_by_string() -> None:
    """AG-01 console boundary: ``reviewed_by`` is unauthenticated metadata.

    The console writer validates batch membership, but the ``reviewed_by``
    attribution on the validated body is an arbitrary free string — the same
    forgery available to any file writer.
    """
    body = DecisionsBody.model_validate(
        {
            "batch": 1,
            "reviewed_by": "professor-x",
            "decisions": [
                {
                    "workspace_id": "STU-synthetic-001",
                    "decision": "INCLUDE",
                    "confidence": 0.9,
                    "screening_reasoning": "Console-shaped forgery.",
                }
            ],
        }
    )
    assert body.reviewed_by == "professor-x"
    assert body.decisions[0].resolved_id == "STU-synthetic-001"
