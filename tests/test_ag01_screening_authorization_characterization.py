"""AG-01 characterization: what the screening handoff enforces today.

Read-only behavioral evidence for
``docs/architecture/ag-01-authorization-readiness.md``. Every test below
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

from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.console.api.screening import DecisionsBody
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
    """AG-01 integrity gap (AG-02 target): 1 of 2 candidates still publishes.

    Membership is checked one direction only (entries ⊆ candidates), so a
    decision file that silently drops a candidate is accepted and the missing
    study appears in neither partition output.
    """
    workspace, studies = _workspace(tmp_path, n_docs=2)
    assert len(studies) == 2
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": studies[0]["study_id"],
                    "decision": "INCLUDE",
                    "method": "LLM",
                    "screening_reasoning": "Only the first candidate was screened.",
                }
            ]
        ),
        encoding="utf-8",
    )

    cmd_collect(workspace)

    included = json.loads(
        (workspace / "literature" / "included.json").read_text(encoding="utf-8")
    )
    excluded = json.loads(
        (workspace / "literature" / "excluded.json").read_text(encoding="utf-8")
    )
    seen = {d.get("workspace_id") for d in included + excluded}
    assert studies[0]["study_id"] in seen
    assert studies[1]["study_id"] not in seen


def test_duplicate_study_entries_are_accepted_today(tmp_path: Path) -> None:
    """AG-01 integrity gap (AG-02 target): duplicate rows are not rejected.

    Two entries for the same study mint two accepted ``ContractDecision``
    records instead of failing closed.
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
                    "screening_reasoning": "First row for the study.",
                },
                {
                    "workspace_id": studies[0]["study_id"],
                    "decision": "INCLUDE",
                    "method": "LLM",
                    "screening_reasoning": "Second row for the same study.",
                },
            ]
        ),
        encoding="utf-8",
    )

    cmd_collect(workspace)

    payloads = _accepted_screening_decisions(workspace)
    assert len(payloads) == 1
    decisions = payloads[0]["data"]["decisions"]
    assert len(decisions) == 2
    assert {d["study_id"] for d in decisions} == {studies[0]["study_id"]}


def test_maybe_decision_is_silently_coerced_to_exclude_today(
    tmp_path: Path,
) -> None:
    """AG-01 fidelity gap (AG-02 target): unresolved MAYBE becomes EXCLUDE.

    The contract model carries MAYBE, but the single-screener collect path
    coerces any non-INCLUDE legacy decision to EXCLUDE, so an explicitly
    unresolved judgment publishes as a terminal exclusion.
    """
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": studies[0]["study_id"],
                    "decision": "MAYBE",
                    "method": "LLM",
                    "screening_reasoning": "Cannot tell from the abstract alone.",
                }
            ]
        ),
        encoding="utf-8",
    )

    cmd_collect(workspace)

    excluded = json.loads(
        (workspace / "literature" / "excluded.json").read_text(encoding="utf-8")
    )
    assert [d.get("workspace_id") for d in excluded] == [studies[0]["study_id"]]
    payloads = _accepted_screening_decisions(workspace)
    assert payloads[0]["data"]["decisions"][0]["decision"] == "EXCLUDE"


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
