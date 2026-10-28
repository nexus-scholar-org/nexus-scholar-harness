"""Conformance tests for agent-layer Phase C (``HumanConfirmation@1``).

Spec: ``specs/agent-layer-portability/06_human_confirmation.md`` — every §6
negative case must surface through a *named* refusal, plus the §3 binding
rules (streamed hashes, coverage, mutation fail-closed) and the §4 export gate.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from scholar_harness.contracts.confirmation.api import (
    CONFIRMATION_RELPATH,
    ConfirmationRefusalError,
    discover_decision_artifacts,
    enforce_coverage,
    export_gate,
    validate,
    verify_artifacts,
)
from scholar_harness.contracts.envelope.registry import RefusalCode

ROOT = Path(__file__).resolve().parent.parent.parent

BATCH_DECISIONS = {
    "decisions": [
        {"study_id": "STU-1", "decision": "INCLUDE"},
        {"study_id": "STU-2", "decision": "EXCLUDE"},
    ]
}

PROVENANCE = {
    "tool": "test-producer",
    "created_at": "2026-10-27T00:00:00Z",
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _ws(tmp_path: Path) -> Path:
    """Scratch workspace with one batch, one screener2 file, one adjudication file."""
    ws = tmp_path / "ws"
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True)
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(BATCH_DECISIONS), encoding="utf-8"
    )
    return ws


def _add_screener2(ws: Path) -> None:
    (ws / "literature" / "screening" / "batch_001_decisions_screener2.json").write_text(
        json.dumps(BATCH_DECISIONS), encoding="utf-8"
    )


def _record(ws: Path, **over: Any) -> dict[str, Any]:
    paths = discover_decision_artifacts(ws)
    return {
        "schema": "HumanConfirmation@1",
        "retrospective": False,
        "reviewer": {
            "name": "A. Reviewer",
            "affiliation": "Customer Org",
            "signing_capacity": "lead_reviewer",
        },
        "artifacts": [
            {"path": p, "sha256": _sha(ws / p), "label": "batch decisions"}
            for p in paths
        ],
        "decisions": [
            {"study_id": "STU-1", "verdict": "confirmed"},
            {"study_id": "STU-2", "verdict": "confirmed"},
        ],
        "summary": {"considered": 2, "confirmed": 2, "changed": 0, "deferred": 0},
        "provenance": dict(PROVENANCE),
        **over,
    }


def _producer():
    path = ROOT / "scripts" / "confirm_screening.py"
    spec = importlib.util.spec_from_file_location("confirm_screening", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    sys.modules["confirm_screening"] = module
    return module


# ---------------------------------------------------------------------------
# Spec 06 §2/§5 — schema and invariant refusals
# ---------------------------------------------------------------------------


def test_valid_record_accepts(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    model = validate(_record(ws))
    assert model.reviewer.name == "A. Reviewer"


def test_changed_row_without_rationale_is_named(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws)
    record["decisions"][0] = {
        "study_id": "STU-1",
        "verdict": "changed",
        "amended": "INCLUDE",
        "rationale": "   ",
    }
    record["decisions"][1] = {
        "study_id": "STU-2",
        "verdict": "deferred",
        "defer_reason": "needs a second look",
    }
    record["summary"] = {"considered": 2, "confirmed": 0, "changed": 1, "deferred": 1}
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        validate(record)
    assert excinfo.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert "rationale" in excinfo.value.detail


def test_summary_disagreement_is_named(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(
        ws, summary={"considered": 2, "confirmed": 1, "changed": 0, "deferred": 0}
    )
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        validate(record)
    assert excinfo.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert "confirmed" in excinfo.value.detail


def test_duplicate_study_id_is_named(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws)
    record["decisions"] = [{"study_id": "STU-1", "verdict": "confirmed"}] * 2
    record["summary"] = {"considered": 2, "confirmed": 2, "changed": 0, "deferred": 0}
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        validate(record)
    assert excinfo.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert "duplicate" in excinfo.value.detail


def test_schema_near_miss_is_named(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws, schema="HumanConfirmation@2")
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        validate(record)
    assert excinfo.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert "near-miss" in excinfo.value.detail


def test_retrospective_is_schema_valid_but_gate_refused(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws, retrospective=True)
    # Schema-level: retrospective records validate (labelled, not forbidden).
    assert validate(record).retrospective is True
    # Export gate: a retrospective signature may never satisfy it.
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        export_gate(ws)
    assert excinfo.value.refusal_code is RefusalCode.REFUSED_UNSUPPORTED


# ---------------------------------------------------------------------------
# Spec 06 §3 — binding: coverage, streamed hashes, mutation fail-closed
# ---------------------------------------------------------------------------


def test_missing_coverage_names_the_file(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws)  # bound while only the batch file exists...
    _add_screener2(ws)  # ...then signed artifacts under-cover the directory
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        validate(record, verify_artifacts=True, root=ws)
    assert excinfo.value.refusal_code is RefusalCode.BLOCKED_INPUT
    assert "batch_001_decisions_screener2.json" in excinfo.value.detail


def test_enforce_coverage_accepts_explicit_list(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    covered = discover_decision_artifacts(ws)
    assert covered == ["literature/screening/batch_001_decisions.json"]
    assert enforce_coverage(covered, ws) == covered


def test_discovery_includes_arm_tagged_decisions(tmp_path: Path) -> None:
    """Arm-tagged dual-screen artifacts are covered; informal side files are not."""
    ws = _ws(tmp_path)
    screening = ws / "literature" / "screening"
    for name in (
        "batch_001_decisions_A.json",
        "batch_001_decisions_B.json",
        "batch_001_decisions_notes.json",
    ):
        (screening / name).write_text(json.dumps(BATCH_DECISIONS), encoding="utf-8")
    discovered = discover_decision_artifacts(ws)
    assert "literature/screening/batch_001_decisions_A.json" in discovered
    assert "literature/screening/batch_001_decisions_B.json" in discovered
    assert "literature/screening/batch_001_decisions_notes.json" not in discovered
    assert discovered == [
        "literature/screening/batch_001_decisions.json",
        "literature/screening/batch_001_decisions_A.json",
        "literature/screening/batch_001_decisions_B.json",
    ]
    assert enforce_coverage(discovered, ws) == discovered


def test_enforce_coverage_refuses_partial_and_unknown(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    _add_screener2(ws)
    with pytest.raises(ConfirmationRefusalError) as partial:
        enforce_coverage(["literature/screening/batch_001_decisions.json"], ws)
    assert partial.value.refusal_code is RefusalCode.BLOCKED_INPUT
    assert "screener2" in partial.value.detail
    with pytest.raises(ConfirmationRefusalError) as extra:
        enforce_coverage(["literature/screening/batch_009_decisions.json"], ws)
    assert extra.value.refusal_code is RefusalCode.BLOCKED_INPUT


def test_mutated_bytes_after_signing_refuse(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws)
    assert verify_artifacts(record, ws) == discover_decision_artifacts(ws)
    # The reviewer's bytes are mutated after the signature: never a re-hash.
    screening = ws / "literature" / "screening"
    path = screening / "batch_001_decisions.json"
    path.write_text(
        json.dumps({"decisions": [{"study_id": "STU-TAMPER"}]}), encoding="utf-8"
    )
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        verify_artifacts(record, ws)
    assert excinfo.value.refusal_code is RefusalCode.PARENT_HASH_MISMATCH


def test_absent_artifact_is_block_input(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws)
    (ws / "literature" / "screening" / "batch_001_decisions.json").unlink()
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        verify_artifacts(record, ws)
    assert excinfo.value.refusal_code is RefusalCode.BLOCKED_INPUT


def test_scope_violation_refused_out_of_root(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    record = _record(ws)
    record["artifacts"][0]["path"] = "../../../etc/passwd"
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        verify_artifacts(record, ws)
    assert excinfo.value.refusal_code is RefusalCode.SCOPE_VIOLATION


def test_fingerprint_excludes_created_at_only(tmp_path: Path) -> None:
    from scholar_harness.contracts.confirmation.api import confirmation_fingerprint

    ws = _ws(tmp_path)
    first = _record(ws)
    retimed = json.loads(json.dumps(first))
    retimed["provenance"]["created_at"] = "2027-01-01T00:00:00Z"
    # Timing metadata moves identity nowhere (Phase B convention).
    assert confirmation_fingerprint(first) == confirmation_fingerprint(retimed)
    retooled = json.loads(json.dumps(first))
    retooled["provenance"]["created_at"] = "2027-01-01T00:00:00Z"
    retooled["provenance"]["tool"] = "changed-tool"
    # Everything else (including the tool label) moves identity.
    assert confirmation_fingerprint(first) != confirmation_fingerprint(retooled)


# ---------------------------------------------------------------------------
# Spec 06 §4 — export gate
# ---------------------------------------------------------------------------


def test_export_gate_refuses_without_artifact(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        export_gate(ws)
    assert excinfo.value.refusal_code is RefusalCode.REFUSED_UNSUPPORTED
    assert "no human confirmation artifact" in excinfo.value.detail


def test_export_gate_accepts_and_reads_valid(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws / "literature" / "screening" / "HUMAN_CONFIRMATION.json").write_text(
        json.dumps(_record(ws)), encoding="utf-8"
    )
    model = export_gate(ws)
    assert model.reviewer.signing_capacity == "lead_reviewer"


def test_export_gate_refuses_after_mutation(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws / "literature" / "screening" / "HUMAN_CONFIRMATION.json").write_text(
        json.dumps(_record(ws)), encoding="utf-8"
    )
    (ws / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps({"decisions": [{"study_id": "STU-9"}]}), encoding="utf-8"
    )
    with pytest.raises(ConfirmationRefusalError) as excinfo:
        export_gate(ws)
    assert excinfo.value.refusal_code is RefusalCode.PARENT_HASH_MISMATCH


# ---------------------------------------------------------------------------
# Producer end-to-end through scripts/confirm_screening.py
# ---------------------------------------------------------------------------


def _producer_run(
    ws: Path, argv: list[str] | None = None, probe=None
) -> tuple[int, Path]:
    """Run the producer with a default one-reviewer queue, written here."""
    module = _producer()
    queue = ws.parent / "queue.json"
    queue.write_text(
        json.dumps(
            {"reviewer": {"name": "A. Reviewer", "affiliation": "Customer Org"}}
        ),
        encoding="utf-8",
    )
    if probe is not None:
        module._MUTATION_PROBE = probe
    code = module.main(["--from-queue", str(queue), str(ws), *(argv or [])])
    if probe is not None:
        module._MUTATION_PROBE = None
    return code, ws / Path(*CONFIRMATION_RELPATH.split("/"))


def test_producer_signs_and_binds_all_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = _ws(tmp_path)
    _add_screener2(ws)
    monkeypatch.chdir(tmp_path)
    code, out_path = _producer_run(ws)
    assert code == 0
    record = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(record["artifacts"]) == 2
    assert record["summary"] == {
        "considered": 2,
        "confirmed": 2,
        "changed": 0,
        "deferred": 0,
    }
    assert record["reviewer"]["name"] == "A. Reviewer"
    assert record["retrospective"] is False
    # The audit journal names the real actor and reviewer.
    journal = (
        (ws / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    event = json.loads(journal[-1])
    assert event["action"] == "HUMAN_CONFIRMATION"
    assert event["parameters"]["reviewer"] == "A. Reviewer"
    # The signed record validates with byte verification against the workspace.
    assert (
        validate(out_path, verify_artifacts=True, root=ws).schema_
        == "HumanConfirmation@1"
    )


def test_producer_refuses_uncovered_artifact_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = _ws(tmp_path)
    _add_screener2(ws)
    (ws / "literature" / "explicit-artifacts.json").write_text(
        json.dumps(["literature/screening/batch_001_decisions.json"]), encoding="utf-8"
    )
    queue = tmp_path / "queue_partial.json"
    queue.write_text(
        json.dumps(
            {
                "reviewer": {"name": "A. Reviewer", "affiliation": "Customer Org"},
                "artifacts": ["literature/screening/batch_001_decisions.json"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    module = _producer()
    code = module.main(["--from-queue", str(queue), str(ws)])
    assert code == 1
    assert not (ws / "literature" / "screening" / "HUMAN_CONFIRMATION.json").exists()


def test_producer_refuses_mutation_between_saw_and_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = _ws(tmp_path)
    monkeypatch.chdir(tmp_path)

    def mutate(workspace: Path) -> None:
        artifact = workspace / "literature" / "screening" / "batch_001_decisions.json"
        artifact.write_text(
            json.dumps({"decisions": [{"study_id": "STU-LATER"}]}), encoding="utf-8"
        )

    code, out_path = _producer_run(ws, probe=mutate)
    assert code == 1
    assert not out_path.exists()


def test_producer_refuses_unknown_override_study(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§5: a queue override for a study absent from the artifacts refuses."""
    ws = _ws(tmp_path)
    queue = tmp_path / "queue_unknown.json"
    queue.write_text(
        json.dumps(
            {
                "reviewer": {"name": "A. Reviewer", "affiliation": "Customer Org"},
                "overrides": {
                    "STU-GHOST": {
                        "verdict": "changed",
                        "amended": "EXCLUDE",
                        "rationale": "epistemic worry",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    module = _producer()
    code = module.main(["--from-queue", str(queue), str(ws)])
    assert code == 1
    assert not (ws / "literature" / "screening" / "HUMAN_CONFIRMATION.json").exists()


def test_producer_honours_queue_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = _ws(tmp_path)
    queue = tmp_path / "queue_overrides.json"
    queue.write_text(
        json.dumps(
            {
                "reviewer": {"name": "A. Reviewer", "affiliation": "Customer Org"},
                "overrides": {
                    "STU-1": {
                        "verdict": "deferred",
                        "defer_reason": "wait for protocol fix",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    module = _producer()
    code = module.main(["--from-queue", str(queue), str(ws)])
    out_path = ws / Path(*CONFIRMATION_RELPATH.split("/"))
    assert code == 0
    record = json.loads(out_path.read_text(encoding="utf-8"))
    assert record["summary"] == {
        "considered": 2,
        "confirmed": 1,
        "changed": 0,
        "deferred": 1,
    }
    rows = {row["study_id"]: row for row in record["decisions"]}
    assert rows["STU-1"]["defer_reason"] == "wait for protocol fix"


def test_producer_decline_never_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Interactive decline refuses INVALID_OUTPUT and writes nothing."""
    ws = _ws(tmp_path)
    monkeypatch.chdir(tmp_path)
    module = _producer()
    answers = iter(["A. Reviewer", "Customer Org", "", "", "no"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    code = module.main(["--interactive", str(ws)])
    assert code == 1
    assert not (ws / "literature" / "screening" / "HUMAN_CONFIRMATION.json").exists()


def test_cli_module_renders_schema() -> None:
    from scholar_harness.contracts.confirmation.schema import (
        render_confirmation_schema,
    )

    rendered = render_confirmation_schema()
    assert "HumanConfirmation@1" in rendered
