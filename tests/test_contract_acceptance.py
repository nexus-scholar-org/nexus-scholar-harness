from __future__ import annotations

import copy
import json
from pathlib import Path

from scholar_harness.contracts import AcceptanceContext, accept_artifact

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "contracts" / "v1" / "two_study_artifact_chain.json"
RUN_FIXTURE = ROOT / "tests" / "fixtures" / "contracts" / "v1" / "run_manifest.json"


def _chain() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["artifacts"]


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "WS-GOLDEN", "stats": {}}), encoding="utf-8"
    )
    return workspace


def _context(artifact: dict) -> AcceptanceContext:
    return AcceptanceContext(
        workspace_id=artifact["workspace_id"],
        protocol_fingerprint=artifact["protocol_fingerprint"],
        corpus_fingerprint=artifact["corpus_fingerprint"],
    )


def test_accepts_and_registers_valid_artifact_before_audit(tmp_path: Path) -> None:
    artifact = _chain()[0]
    workspace = _workspace(tmp_path)

    result = accept_artifact(workspace, artifact, expected=_context(artifact))

    assert result.accepted
    assert result.published_path
    assert (workspace / result.published_path).is_file()
    registry = json.loads((workspace / "audit" / "artifact_registry.json").read_text())
    assert registry["artifacts"][artifact["artifact_id"]]["sha256"] == result.payload_hash
    event = json.loads((workspace / "audit" / "journal.jsonl").read_text().splitlines()[-1])
    assert event["action"] == "ARTIFACT_ACCEPTED"
    assert event["parameters"]["payload_hash"] == result.payload_hash


def test_rejection_retains_hash_not_raw_payload(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    payload = '{"secret_raw_payload": true'
    context = _context(_chain()[0])

    result = accept_artifact(workspace, payload, expected=context)

    assert not result.accepted
    assert result.issues[0].code == "INVALID_JSON"
    rejection = (workspace / result.rejection_path).read_text(encoding="utf-8")
    assert "secret_raw_payload" not in rejection
    assert result.payload_hash in rejection
    assert not (workspace / "artifacts").exists()


def test_context_mismatch_fails_before_publication(tmp_path: Path) -> None:
    artifact = _chain()[0]
    workspace = _workspace(tmp_path)
    context = _context(artifact).model_copy(update={"workspace_id": "WS-OTHER"})

    result = accept_artifact(workspace, artifact, expected=context)

    assert not result.accepted
    assert {issue.code for issue in result.issues} == {"WORKSPACE_ID_MISMATCH"}
    assert not (workspace / "artifacts").exists()


def test_child_requires_registered_parent_with_exact_hash(tmp_path: Path) -> None:
    corpus, batch = _chain()[:2]
    workspace = _workspace(tmp_path)
    context = _context(corpus)

    missing = accept_artifact(workspace, batch, expected=context)
    assert not missing.accepted
    assert missing.issues[0].code == "MISSING_PARENT_ARTIFACT"

    assert accept_artifact(workspace, corpus, expected=context).accepted
    bad_batch = copy.deepcopy(batch)
    bad_batch["inputs"][0]["sha256"] = "sha256:" + "0" * 64
    mismatch = accept_artifact(workspace, bad_batch, expected=context)
    assert not mismatch.accepted
    assert mismatch.issues[0].code == "PARENT_HASH_MISMATCH"


def test_same_payload_is_idempotent_but_same_id_different_payload_is_not(tmp_path: Path) -> None:
    artifact = _chain()[0]
    workspace = _workspace(tmp_path)
    context = _context(artifact)

    first = accept_artifact(workspace, artifact, expected=context)
    second = accept_artifact(workspace, artifact, expected=context)
    assert first.accepted and second.accepted and second.idempotent

    changed = copy.deepcopy(artifact)
    changed["producer"]["version"] = "different"
    conflict = accept_artifact(workspace, changed, expected=context)
    assert not conflict.accepted
    assert conflict.issues[0].code == "IDEMPOTENCY_CONFLICT"


def test_idempotent_replay_still_enforces_current_context(tmp_path: Path) -> None:
    artifact = _chain()[0]
    workspace = _workspace(tmp_path)

    assert accept_artifact(workspace, artifact, expected=_context(artifact)).accepted
    wrong_context = _context(artifact).model_copy(update={"workspace_id": "WS-OTHER"})

    replay = accept_artifact(workspace, artifact, expected=wrong_context)

    assert not replay.accepted
    assert {issue.code for issue in replay.issues} == {"WORKSPACE_ID_MISMATCH"}


def test_required_parent_type_is_enforced_from_registry(tmp_path: Path) -> None:
    chain = _chain()
    batch = copy.deepcopy(chain[1])
    run_manifest = json.loads(RUN_FIXTURE.read_text(encoding="utf-8"))
    for field in ("workspace_id", "protocol_fingerprint", "corpus_fingerprint"):
        run_manifest[field] = batch[field]
    workspace = _workspace(tmp_path)
    context = _context(batch)

    accepted_parent = accept_artifact(workspace, run_manifest, expected=context)
    assert accepted_parent.accepted
    batch["inputs"] = [
        {
            "artifact_id": run_manifest["artifact_id"],
            "sha256": accepted_parent.payload_hash,
        }
    ]

    result = accept_artifact(workspace, batch, expected=context)

    assert not result.accepted
    assert "REQUIRED_PARENT_TYPE_MISSING" in {issue.code for issue in result.issues}


def test_screening_decisions_must_match_registered_batch(tmp_path: Path) -> None:
    corpus, batch, decisions = copy.deepcopy(_chain()[:3])
    workspace = _workspace(tmp_path)
    context = _context(corpus)

    assert accept_artifact(workspace, corpus, expected=context).accepted
    assert accept_artifact(workspace, batch, expected=context).accepted
    decisions["data"]["batch_id"] = "batch-other"

    result = accept_artifact(workspace, decisions, expected=context)

    assert not result.accepted
    assert "SCREENING_BATCH_ID_MISMATCH" in {issue.code for issue in result.issues}


def test_orphan_destination_is_rejected_without_overwrite(tmp_path: Path) -> None:
    artifact = _chain()[0]
    workspace = _workspace(tmp_path)
    destination = (
        workspace
        / "artifacts"
        / artifact["artifact_type"]
        / f"{artifact['artifact_id']}.json"
    )
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"preserve me")

    result = accept_artifact(workspace, artifact, expected=_context(artifact))

    assert not result.accepted
    assert result.issues[0].code == "ORPHAN_ARTIFACT_PATH"
    assert destination.read_bytes() == b"preserve me"


def test_audit_failure_rolls_back_publication_and_registry(tmp_path: Path, monkeypatch) -> None:
    artifact = _chain()[0]
    workspace = _workspace(tmp_path)

    def fail_audit(*args, **kwargs):
        raise OSError("audit unavailable")

    monkeypatch.setattr("scholar_harness.contracts.acceptance.log_event", fail_audit)
    result = accept_artifact(workspace, artifact, expected=_context(artifact))

    assert not result.accepted
    assert result.issues[0].code == "ATOMIC_COMMIT_FAILED"
    assert not (workspace / "artifacts").exists()
    registry = workspace / "audit" / "artifact_registry.json"
    assert not registry.exists()


def test_staging_failure_returns_structured_issue_without_publication(
    tmp_path: Path, monkeypatch
) -> None:
    artifact = _chain()[0]
    workspace = _workspace(tmp_path)
    real_write_temp = __import__(
        "scholar_harness.contracts.acceptance", fromlist=["_write_temp"]
    )._write_temp
    calls = 0

    def fail_second_write(path, content):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("registry staging unavailable")
        return real_write_temp(path, content)

    monkeypatch.setattr(
        "scholar_harness.contracts.acceptance._write_temp", fail_second_write
    )
    result = accept_artifact(workspace, artifact, expected=_context(artifact))

    assert not result.accepted
    assert result.issues[0].code == "ATOMIC_COMMIT_FAILED"
    assert not (workspace / "artifacts").exists()
    assert not (workspace / "audit" / "artifact_registry.json").exists()
