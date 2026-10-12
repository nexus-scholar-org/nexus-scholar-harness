"""AG-02 screening decision integrity tests (workflow-integrity only).

Every test runs ``cmd_collect`` against a synthetic ``tmp_path`` workspace
(2-study corpus variant of the ``test_screening_migration`` pattern); no real
research workspace is touched. Each refusal test asserts the refusal shape
**and** the absence of publication side effects. Nothing here treats a
``method: HUMAN`` label, a human-like ``reviewed_by`` string, a confidence
score, or a critic verdict as carrying any weight: identical bytes collect
(or refuse) identically whatever those fields claim.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
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
SRC_ROOT = ROOT / "src" / "scholar_harness" / "screening"
PROTOCOL_FIXTURE = (
    ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)
STAMP = "2026-09-21T12:00:00Z"
PARTITION_FILES = (
    "included.json",
    "excluded.json",
    "conflicts.json",
    "prisma_screening_report.md",
    "prisma_report.json",
)


def _workspace(
    tmp_path: Path,
    n_docs: int = 2,
    workspace_id: str = "WSP-ag02-integrity",
    run_id: str = "RUN-ag02-integrity",
    tag: str = "workspace",
) -> tuple[Path, list[dict]]:
    workspace = tmp_path / tag
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "project.json").write_text(
        json.dumps({"project_id": workspace_id, "stats": {}}), encoding="utf-8"
    )
    protocol = json.loads(PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    protocol_hash = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    sources = [
        Document(
            title=f"AG-02 synthetic record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"ag02-record-{i}",
            external_ids=ExternalIds(doi=f"10.1000/ag02-{i}"),
            authors=[Author("Reviewer")],
        )
        for i in range(n_docs)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=workspace_id,
        run_id=run_id,
        protocol_fingerprint=protocol_hash,
        created_at=datetime(2026, 9, 21, tzinfo=UTC),
        commit="1" * 40,
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
    literature.mkdir(exist_ok=True)
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": f"10.1000/ag02-{i}"},
                }
                for i, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )
    return workspace, studies


def _entry(study_id: str, decision: str = "INCLUDE", **overrides) -> dict:
    record = {
        "workspace_id": study_id,
        "decision": decision,
        "method": "LLM",
        "screening_reasoning": f"{decision} for {study_id}: meets the frozen criteria.",
    }
    record.update(overrides)
    return record


def _write_decisions(
    workspace: Path, entries: list[dict], *, reviewed_by: str = "reviewer-1"
) -> Path:
    path = workspace / "literature" / "screening" / "batch_001_decisions.json"
    path.write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": reviewed_by,
                "timestamp": STAMP,
                "decisions": entries,
            }
        ),
        encoding="utf-8",
    )
    return path


def _registry(workspace: Path) -> dict:
    return json.loads(
        (workspace / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )


def _decision_artifacts(workspace: Path) -> list[tuple[str, dict, dict]]:
    registry = _registry(workspace)
    found = []
    for artifact_id, entry in registry["artifacts"].items():
        if entry["artifact_type"] == "screening_decisions":
            envelope = json.loads(
                (workspace / entry["path"]).read_text(encoding="utf-8")
            )
            found.append((artifact_id, entry, envelope))
    return found


def _journal_rows(workspace: Path) -> list[dict]:
    journal = workspace / "audit" / "journal.jsonl"
    if not journal.exists():
        return []
    return [
        json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()
    ]


def _refusal_rows(workspace: Path, code: str) -> list[dict]:
    return [
        row
        for row in _journal_rows(workspace)
        if row.get("action") == "SCREENING_COLLECT_REFUSED"
        and row.get("parameters", {}).get("code") == code
    ]


def _batch_row(workspace: Path, index: int = 1) -> dict:
    manifest = json.loads(
        (workspace / "literature" / "screening" / "MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )
    return next(b for b in manifest["batches"] if b["batch_index"] == index)


def _assert_fail_closed_fresh(workspace: Path, decisions_path: Path, code: str) -> None:
    """Refusal on a fresh workspace: typed code, zero partition outputs."""
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)
    assert not decisions_path.exists()
    assert decisions_path.with_name(decisions_path.name + ".rejected").is_file()
    assert _batch_row(workspace)["status"] == "MISSING"
    for name in PARTITION_FILES:
        assert not (workspace / "literature" / name).exists()
    assert _decision_artifacts(workspace) == []
    assert not list((workspace / "audit").glob("artifacts/screening_decisions/*"))
    assert _refusal_rows(workspace, code), f"no journal row with code {code}"


def test_incomplete_coverage_refuses_without_publication(tmp_path: Path) -> None:
    """AG-C01: a 1-of-2 file refuses with COVERAGE_INCOMPLETE and no outputs."""
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    decisions_path = _write_decisions(workspace, [_entry(studies[0]["study_id"])])
    _assert_fail_closed_fresh(workspace, decisions_path, "COVERAGE_INCOMPLETE")


def test_duplicate_entries_refuse_without_publication(tmp_path: Path) -> None:
    """AG-C01: the same study twice refuses with DUPLICATE_ENTRY."""
    workspace, studies = _workspace(tmp_path, n_docs=1)
    cmd_prepare(workspace, batch_size=20)
    decisions_path = _write_decisions(
        workspace,
        [
            _entry(studies[0]["study_id"], screening_reasoning="First row."),
            _entry(studies[0]["study_id"], screening_reasoning="Second row."),
        ],
    )
    _assert_fail_closed_fresh(workspace, decisions_path, "DUPLICATE_ENTRY")


def test_extra_ids_still_refuse(tmp_path: Path) -> None:
    """AG-C01: unknown study ids still refuse (now via the coverage gate)."""
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    decisions_path = _write_decisions(
        workspace,
        [
            _entry(studies[0]["study_id"]),
            _entry(studies[1]["study_id"]),
            _entry("STU-UNKNOWN-12345"),
        ],
    )
    _assert_fail_closed_fresh(workspace, decisions_path, "COVERAGE_INCOMPLETE")


def test_maybe_and_conflict_refuse_finalize(tmp_path: Path) -> None:
    """AG-C02: MAYBE/CONFLICT rows refuse finalize; nothing is coerced."""
    for value in ("MAYBE", "CONFLICT"):
        workspace, studies = _workspace(tmp_path, tag=f"ws-{value.lower()}")
        cmd_prepare(workspace, batch_size=20)
        decisions_path = _write_decisions(
            workspace,
            [
                _entry(studies[0]["study_id"], "INCLUDE"),
                _entry(
                    studies[1]["study_id"],
                    value,
                    screening_reasoning="Cannot tell from the abstract alone.",
                ),
            ],
        )
        with pytest.raises(RuntimeError, match="collection blocked"):
            cmd_collect(workspace)
        # The unresolved study appears in neither partition, and no accepted
        # decision coerces it to EXCLUDE: there are no partitions and no
        # accepted screening_decisions artifact at all.
        for name in PARTITION_FILES:
            assert not (workspace / "literature" / name).exists()
        assert _decision_artifacts(workspace) == []
        assert not decisions_path.exists()
        assert decisions_path.with_name(decisions_path.name + ".rejected").is_file()
        assert _batch_row(workspace)["status"] == "MISSING"
        assert _refusal_rows(workspace, "UNRESOLVED_FINALIZE_REFUSED")


def test_no_silent_exclusion_regression(tmp_path: Path) -> None:
    """AG-C02: explicit EXCLUDE judgments still publish with reasons."""
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    _write_decisions(
        workspace,
        [
            _entry(
                studies[0]["study_id"],
                "EXCLUDE",
                screening_reasoning="Wrong population for RQ1.",
            ),
            _entry(
                studies[1]["study_id"],
                "EXCLUDE",
                screening_reasoning="No empirical data presented.",
            ),
        ],
    )
    cmd_collect(workspace)
    excluded = json.loads(
        (workspace / "literature" / "excluded.json").read_text(encoding="utf-8")
    )
    assert {d.get("workspace_id") for d in excluded} == {s["study_id"] for s in studies}
    artifacts = _decision_artifacts(workspace)
    assert len(artifacts) == 1
    assert {d["decision"] for d in artifacts[0][2]["data"]["decisions"]} == {"EXCLUDE"}


def test_decision_hash_recorded_in_lineage_and_journal(tmp_path: Path) -> None:
    """AG-C04hash: the accepted artifact lineage and journal name the bytes."""
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    decisions_path = _write_decisions(
        workspace, [_entry(s["study_id"]) for s in studies]
    )
    cmd_collect(workspace)
    expected = "sha256:" + hashlib.sha256(decisions_path.read_bytes()).hexdigest()
    artifacts = _decision_artifacts(workspace)
    assert len(artifacts) == 1
    assert artifacts[0][2]["decision_file_sha256"] == expected
    assert _batch_row(workspace)["decision_file_sha256"] == expected
    recorded = [
        row
        for row in _journal_rows(workspace)
        if row.get("action") == "SCREENING_DECISIONS_RECORDED"
    ]
    assert recorded, "no lineage journal row for the accepted decision file"
    assert recorded[0]["parameters"]["decision_file_sha256"] == expected
    assert recorded[0]["parameters"]["batch_index"] == 1


def test_changed_bytes_after_acceptance_refuse(tmp_path: Path) -> None:
    """AG-C05: overwriting an accepted file refuses with CONTENT_CHANGED."""
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    decisions_path = _write_decisions(
        workspace, [_entry(s["study_id"]) for s in studies]
    )
    cmd_collect(workspace)
    first_hash = "sha256:" + hashlib.sha256(decisions_path.read_bytes()).hexdigest()
    artifacts = _decision_artifacts(workspace)
    assert len(artifacts) == 1
    artifact_id, _, envelope = artifacts[0]
    artifact_path = workspace / _registry(workspace)["artifacts"][artifact_id]["path"]
    artifact_bytes_before = artifact_path.read_bytes()
    included_before = (workspace / "literature" / "included.json").read_bytes()

    decisions_path.write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "reviewer-1",
                "timestamp": STAMP,
                "decisions": [
                    _entry(
                        s["study_id"],
                        screening_reasoning="Rewritten after acceptance.",
                    )
                    for s in studies
                ],
            }
        ),
        encoding="utf-8",
    )
    second_hash = "sha256:" + hashlib.sha256(decisions_path.read_bytes()).hexdigest()
    assert second_hash != first_hash

    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)
    rows = _refusal_rows(workspace, "CONTENT_CHANGED")
    assert rows, "no CONTENT_CHANGED journal row"
    params = rows[0]["parameters"]
    assert params["previous_decision_file_sha256"] == first_hash
    assert params["current_decision_file_sha256"] == second_hash
    # Old acceptance intact; no new publication.
    assert artifact_path.read_bytes() == artifact_bytes_before
    assert len(_decision_artifacts(workspace)) == 1
    assert (workspace / "literature" / "included.json").read_bytes() == included_before
    assert decisions_path.with_name(decisions_path.name + ".rejected").is_file()
    assert _batch_row(workspace)["status"] == "MISSING"


def test_identical_recollect_is_idempotent(tmp_path: Path) -> None:
    """AG-C07retry: collecting identical bytes twice mints nothing new."""
    workspace, studies = _workspace(tmp_path)
    cmd_prepare(workspace, batch_size=20)
    _write_decisions(workspace, [_entry(s["study_id"]) for s in studies])
    cmd_collect(workspace)
    before = _registry(workspace)
    cmd_collect(workspace)
    after = _registry(workspace)
    assert after["artifacts"].keys() == before["artifacts"].keys()
    assert len(_decision_artifacts(workspace)) == 1


def test_failed_promotion_leaves_no_consumable_output(tmp_path: Path) -> None:
    """AG-C06: every refusal kind leaves prior partition outputs byte-identical."""
    # Kind 1: changed bytes after acceptance.
    workspace, studies = _workspace(tmp_path, tag="ws-changed")
    cmd_prepare(workspace, batch_size=20)
    changed_path = _write_decisions(workspace, [_entry(s["study_id"]) for s in studies])
    cmd_collect(workspace)
    before_files = {
        name: (workspace / "literature" / name).read_bytes() for name in PARTITION_FILES
    }
    before_keys = set(_registry(workspace)["artifacts"])
    before_decisions = {aid for aid, _, _ in _decision_artifacts(workspace)}
    changed_path.write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "reviewer-1",
                "timestamp": STAMP,
                "decisions": [
                    _entry(s["study_id"], screening_reasoning="Rewritten bytes.")
                    for s in studies
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)
    assert _refusal_rows(workspace, "CONTENT_CHANGED")
    for name, content in before_files.items():
        assert (workspace / "literature" / name).read_bytes() == content
    assert set(_registry(workspace)["artifacts"]) == before_keys
    assert {aid for aid, _, _ in _decision_artifacts(workspace)} == before_decisions

    # Kind 2: stale binding after a re-prepare with a grown corpus.
    stale_ws, stale_studies = _workspace(
        tmp_path,
        tag="ws-stale",
        workspace_id="WSP-ag02-stale",
        run_id="RUN-ag02-stale",
    )
    cmd_prepare(stale_ws, batch_size=20)
    stale_path = _write_decisions(
        stale_ws, [_entry(s["study_id"]) for s in stale_studies]
    )
    cmd_collect(stale_ws)
    stale_before_files = {
        name: (stale_ws / "literature" / name).read_bytes() for name in PARTITION_FILES
    }
    stale_before_keys = set(_registry(stale_ws)["artifacts"])
    stale_before_decisions = {aid for aid, _, _ in _decision_artifacts(stale_ws)}
    protocol = json.loads((stale_ws / "protocol.json").read_text(encoding="utf-8"))
    protocol_hash = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    grown = build_corpus_snapshot_artifact(
        [
            Document(
                title=f"AG-02 synthetic record {i}",
                year=2026,
                provider="crossref",
                provider_id=f"ag02-record-{i}",
                external_ids=ExternalIds(doi=f"10.1000/ag02-{i}"),
                authors=[Author("Reviewer")],
            )
            for i in range(3)
        ],
        workspace_id="WSP-ag02-stale",
        run_id="RUN-ag02-stale-v2",
        protocol_fingerprint=protocol_hash,
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
        commit="1" * 40,
    )
    grown_result = accept_artifact(
        stale_ws,
        grown.artifact,
        expected=AcceptanceContext(
            workspace_id="WSP-ag02-stale",
            protocol_fingerprint=protocol_hash,
            corpus_fingerprint=grown.artifact["corpus_fingerprint"],
        ),
    )
    assert grown_result.accepted
    cmd_prepare(stale_ws, batch_size=20, force=True)
    batch = json.loads(
        (stale_ws / "literature" / "screening" / "batch_001.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(batch["papers"]) == 3
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(stale_ws)
    assert _refusal_rows(stale_ws, "STALE_BINDING")
    for name, content in stale_before_files.items():
        assert (stale_ws / "literature" / name).read_bytes() == content
    assert {aid for aid, _, _ in _decision_artifacts(stale_ws)} == (
        stale_before_decisions
    )
    assert stale_before_keys <= set(_registry(stale_ws)["artifacts"])
    assert stale_path.with_name(stale_path.name + ".rejected").is_file()
    assert _batch_row(stale_ws)["status"] == "MISSING"


def test_dual_path_semantics_unchanged(tmp_path: Path) -> None:
    """AG-C08dual: consensus still mints COMPOSED with both parents."""
    workspace, studies = _workspace(tmp_path, n_docs=1)
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    study_id = studies[0]["study_id"]
    common = {
        "workspace_id": study_id,
        "decision": "INCLUDE",
        "method": "HUMAN",
        "screening_reasoning": "Meets all frozen criteria.",
    }
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {
                    **common,
                    "decision_id": "SCR-ag02-screener-1",
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
                    "decision_id": "SCR-ag02-screener-2",
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
    artifacts = _decision_artifacts(workspace)
    assert len(artifacts) == 1
    decisions = artifacts[0][2]["data"]["decisions"]
    assert {item["decision_id"] for item in decisions[:2]} == {
        "SCR-ag02-screener-1",
        "SCR-ag02-screener-2",
    }
    final = decisions[-1]
    assert final["method"] == "COMPOSED"
    assert set(final["parent_decision_ids"]) == {
        "SCR-ag02-screener-1",
        "SCR-ag02-screener-2",
    }


def test_human_labeled_but_unapproved_file_is_not_privileged(
    tmp_path: Path,
) -> None:
    """AG-C03guard: HUMAN-labeled files behave byte-identically to LLM twins."""
    twins = {}
    for label, method, reviewed_by in (
        ("human", "HUMAN", "dr-chen"),
        ("llm", "LLM", "agent-7"),
    ):
        workspace, studies = _workspace(
            tmp_path,
            tag=f"ws-{label}",
            workspace_id=f"WSP-ag02-twin-{label}",
            run_id=f"RUN-ag02-twin-{label}",
        )
        cmd_prepare(workspace, batch_size=20)
        _write_decisions(
            workspace,
            [
                _entry(
                    studies[0]["study_id"],
                    "INCLUDE",
                    method=method,
                    screening_reasoning="Twin judgment one.",
                ),
                _entry(
                    studies[1]["study_id"],
                    "EXCLUDE",
                    method=method,
                    screening_reasoning="Twin judgment two.",
                ),
            ],
            reviewed_by=reviewed_by,
        )
        cmd_collect(workspace)
        twins[label] = workspace
    for name in ("included.json", "excluded.json"):
        assert (twins["human"] / "literature" / name).read_bytes() == (
            twins["llm"] / "literature" / name
        ).read_bytes()
    # And an integrity-invalid HUMAN-labeled file refuses exactly like its twin.
    for label, method in (("human-bad", "HUMAN"), ("llm-bad", "LLM")):
        workspace, studies = _workspace(
            tmp_path,
            tag=f"ws-{label}",
            workspace_id=f"WSP-ag02-twin-{label}",
            run_id=f"RUN-ag02-twin-{label}",
        )
        cmd_prepare(workspace, batch_size=20)
        decisions_path = _write_decisions(
            workspace,
            [_entry(studies[0]["study_id"], method=method)],
            reviewed_by="dr-chen" if method == "HUMAN" else "agent-7",
        )
        with pytest.raises(RuntimeError, match="collection blocked"):
            cmd_collect(workspace)
        assert _refusal_rows(workspace, "COVERAGE_INCOMPLETE")
        assert decisions_path.with_name(decisions_path.name + ".rejected").is_file()


def test_no_authorization_concept_in_new_code() -> None:
    """AG-C10guard: no approver/authority identifiers; stdlib-only imports."""
    integrity_src = (SRC_ROOT / "integrity.py").read_text(encoding="utf-8")
    collector_src = (SRC_ROOT / "collector.py").read_text(encoding="utf-8")
    for name, text in (
        ("integrity.py", integrity_src),
        ("collector.py", collector_src),
    ):
        for lineno, line in enumerate(text.splitlines(), start=1):
            if re.search(r"approv|authoriz", line, re.IGNORECASE):
                assert "non-claim" in line.lower(), (
                    f"{name}:{lineno} introduces an authority-shaped "
                    f"identifier outside an explicitly marked non-claim: {line!r}"
                )
    tree = ast.parse(integrity_src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= {"__future__", "hashlib", "typing"}, imported
