"""AG-03B production review-lifecycle tests (cross-platform, hermetic).

Covers the bounded single-screener lifecycle on synthetic ``tmp_path`` state
only: immutable snapshot with a single parse/hash/display buffer, revision
chain with supersession, durable refusal records, derived-output binding,
and the changed-content / cross-revision / revoked refusal paths (no output
file in any refusal case).

Explicit non-claims: no coherent publication generations, no downstream
currentness, no crash recovery, no concurrency/atomicity, no POSIX proof.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from scholar_harness.authority import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_NOT_OPERATOR,
    APPROVAL_REVOKED,
    APPROVAL_SCOPE_MISMATCH,
    ApprovalBinding,
    ApprovalRecord,
    AuthorityRefused,
    OperatorIdentity,
    canonical_json_bytes,
    content_sha256,
    mint_approval,
    promote,
    verify_approval,
)
from scholar_harness.authority.lifecycle import (
    DerivedOutputRecord,
    ReviewSnapshot,
    bind_derived_output,
    capture_snapshot,
    record_refusal,
    supersede,
    verify_derived,
)

POLICY = "ag03a-approval-policy-v1"
NOW = "2026-10-12T12:00:00+00:00"
LATER = "2026-10-12T12:01:00+00:00"


def _binding(revision: int = 1) -> ApprovalBinding:
    return ApprovalBinding(
        workspace_id="WSP-" + "a" * 32,
        run_id="RUN-LIFECYCLE-1",
        batch_id="BATCH-001",
        protocol_fingerprint="sha256:" + "b" * 64,
        corpus_fingerprint="sha256:" + "c" * 64,
        recommendation_revision=revision,
        policy_version=POLICY,
    )


def _recommendation() -> bytes:
    return canonical_json_bytes(
        {
            "batch_id": "BATCH-001",
            "recommendation_revision": 1,
            "entries": [{"study_id": "STU-1", "decision": "INCLUDE"}],
            "actor": "Dr. Forged Reviewer",
            "method": "HUMAN",
            "confidence": 0.99,
            "critic": "PASS",
        }
    )


def _final(revision: int = 1) -> bytes:
    return canonical_json_bytes(
        {
            "batch_id": "BATCH-001",
            "revision": revision,
            "entries": [{"study_id": "STU-1", "decision": "INCLUDE"}],
        }
    )


def _operator() -> OperatorIdentity:
    return OperatorIdentity(
        identity="lifecycle-operator@example", source="publisher-operator-context"
    )


def _snapshot() -> ReviewSnapshot:
    return capture_snapshot(_recommendation(), _final(), _binding(), captured_at=NOW)


def _mint_for(snapshot: ReviewSnapshot) -> ApprovalRecord:
    return mint_approval(
        operator=_operator(),
        binding=snapshot.binding,
        reviewed_bytes=snapshot.bytes_for("hash"),
        final_decision_bytes=snapshot.final_bytes_for("hash"),
        approved_at=NOW,
    )


# --- 1. immutable review snapshot: one buffer for parse/hash/display ------- #


def test_snapshot_views_return_identical_bytes() -> None:
    snapshot = _snapshot()
    parsed = snapshot.bytes_for("parse")
    hashed = snapshot.bytes_for("hash")
    displayed = snapshot.bytes_for("display")
    assert parsed == hashed == displayed
    assert parsed is hashed is displayed
    assert hashed == _recommendation()


def test_snapshot_final_views_return_identical_bytes() -> None:
    snapshot = _snapshot()
    assert snapshot.final_bytes_for("parse") == snapshot.final_bytes_for("hash")
    assert snapshot.final_bytes_for("hash") is snapshot.final_bytes_for("display")
    assert snapshot.final_bytes_for("display") == _final()


def test_snapshot_hashes_match_the_single_buffer() -> None:
    snapshot = _snapshot()
    assert snapshot.recommendation_sha256 == content_sha256(snapshot.bytes_for("hash"))
    assert snapshot.final_decision_sha256 == content_sha256(
        snapshot.final_bytes_for("hash")
    )
    assert snapshot.recommendation_sha256 == content_sha256(_recommendation())
    assert snapshot.final_decision_sha256 == content_sha256(_final())


def test_snapshot_is_frozen() -> None:
    snapshot = _snapshot()
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshot.captured_at = LATER  # type: ignore[misc]


def test_unknown_snapshot_view_refuses() -> None:
    snapshot = _snapshot()
    with pytest.raises(ValueError):
        snapshot.bytes_for("render")
    with pytest.raises(ValueError):
        snapshot.final_bytes_for("render")


# --- 2. revision chain with supersession ------------------------------------ #


def test_supersede_preserves_original_verbatim_and_links_prior() -> None:
    snapshot = _snapshot()
    changed_final = canonical_json_bytes(
        {
            "batch_id": "BATCH-001",
            "revision": 2,
            "entries": [{"study_id": "STU-1", "decision": "EXCLUDE"}],
        }
    )
    assert changed_final != snapshot.final_bytes_for("display")

    new = supersede(snapshot, changed_final, _operator(), captured_at=LATER)

    assert new.reviewed_bytes == snapshot.reviewed_bytes
    assert new.recommendation_sha256 == snapshot.recommendation_sha256
    assert content_sha256(new.reviewed_bytes) == content_sha256(_recommendation())
    assert new.final_bytes_for("display") == changed_final
    assert new.supersedes == snapshot.fingerprint()
    assert new.superseded_by == "lifecycle-operator@example"
    assert new.binding.recommendation_revision == 2
    assert new.captured_at == LATER
    # The prior snapshot is untouched: still revision 1, no link.
    assert snapshot.binding.recommendation_revision == 1
    assert snapshot.supersedes is None
    assert snapshot.final_bytes_for("display") == _final()


def test_supersede_identical_final_is_idempotent() -> None:
    snapshot = _snapshot()
    assert supersede(snapshot, _final(), _operator()) is snapshot


def test_old_approval_verifies_only_old_revision() -> None:
    snapshot = _snapshot()
    old_record = _mint_for(snapshot)
    # Old approval still verifies the old revision through the snapshot buffers.
    verify_approval(
        record=old_record,
        expected_binding=snapshot.binding,
        reviewed_bytes=snapshot.bytes_for("hash"),
        final_decision_bytes=snapshot.final_bytes_for("hash"),
        policy_version=POLICY,
        now=NOW,
    )
    # The same record presented for the superseding revision refuses.
    new = supersede(
        snapshot,
        canonical_json_bytes({"batch_id": "BATCH-001", "revision": 2}),
        _operator(),
        captured_at=LATER,
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        verify_approval(
            record=old_record,
            expected_binding=new.binding,
            reviewed_bytes=new.bytes_for("hash"),
            final_decision_bytes=new.final_bytes_for("hash"),
            policy_version=POLICY,
            now=NOW,
        )
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH


# --- 3. durable refusal record ---------------------------------------------- #


def test_record_refusal_in_memory_sink() -> None:
    snapshot = _snapshot()
    record = _mint_for(snapshot)
    changed = bytearray(snapshot.bytes_for("hash"))
    changed[10] ^= 0x01
    with pytest.raises(AuthorityRefused) as excinfo:
        verify_approval(
            record=record,
            expected_binding=snapshot.binding,
            reviewed_bytes=bytes(changed),
            final_decision_bytes=snapshot.final_bytes_for("hash"),
            policy_version=POLICY,
            now=NOW,
        )
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED

    sunk: list[dict[str, object]] = []
    stored = record_refusal(
        excinfo.value, snapshot.binding, sunk.append, recorded_at=NOW
    )
    assert len(sunk) == 1
    assert sunk[0] is stored
    assert stored["code"] == APPROVAL_CONTENT_CHANGED
    assert stored["message"]
    assert isinstance(stored["details"], dict)
    assert stored["binding"] == snapshot.binding.as_dict()
    assert stored["recorded_at"] == NOW


def test_record_refusal_jsonl_sink_round_trip(tmp_path: Path) -> None:
    snapshot = _snapshot()
    refusal = AuthorityRefused(
        APPROVAL_SCOPE_MISMATCH, "approval scope does not match", batch_id="BATCH-002"
    )
    journal = tmp_path / "refusals.jsonl"

    def jsonl_sink(entry: dict[str, object]) -> None:
        with journal.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    stored = record_refusal(refusal, snapshot.binding, jsonl_sink, recorded_at=NOW)
    lines = journal.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    reloaded = json.loads(lines[0])
    assert reloaded == json.loads(json.dumps(stored, sort_keys=True))
    assert reloaded["code"] == APPROVAL_SCOPE_MISMATCH
    assert reloaded["message"] == "approval scope does not match"
    assert reloaded["details"] == {"batch_id": "BATCH-002"}
    assert reloaded["binding"] == snapshot.binding.as_dict()
    assert reloaded["recorded_at"] == NOW


def test_refusal_sink_failure_surfaces_and_records_nothing() -> None:
    snapshot = _snapshot()
    refusal = AuthorityRefused(APPROVAL_REVOKED, "approval has been revoked")
    sunk: list[dict[str, object]] = []

    def failing_sink(_entry: dict[str, object]) -> None:
        raise OSError("refusal journal unavailable")

    with pytest.raises(OSError, match="refusal journal unavailable"):
        record_refusal(refusal, snapshot.binding, failing_sink, recorded_at=NOW)
    assert sunk == []


# --- 4. derived-output binding ---------------------------------------------- #


def test_bind_and_verify_derived_output() -> None:
    snapshot = _snapshot()
    approval = _mint_for(snapshot)
    derived = canonical_json_bytes({"batch_id": "BATCH-001", "report": "summary"})
    bound = bind_derived_output(approval, derived)
    assert isinstance(bound, DerivedOutputRecord)
    assert bound.approval_fingerprint == approval.fingerprint()
    assert bound.output_sha256 == content_sha256(derived)
    verified = verify_derived(bound, approval.fingerprint(), derived)
    assert verified == bound


def test_verify_derived_refuses_on_byte_mismatch() -> None:
    snapshot = _snapshot()
    approval = _mint_for(snapshot)
    derived = canonical_json_bytes({"batch_id": "BATCH-001", "report": "summary"})
    bound = bind_derived_output(approval, derived)
    tampered = canonical_json_bytes({"batch_id": "BATCH-001", "report": "altered"})
    assert tampered != derived
    with pytest.raises(AuthorityRefused) as excinfo:
        verify_derived(bound, approval.fingerprint(), tampered)
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED


def test_verify_derived_refuses_on_approval_mismatch() -> None:
    snapshot = _snapshot()
    approval = _mint_for(snapshot)
    derived = canonical_json_bytes({"batch_id": "BATCH-001", "report": "summary"})
    bound = bind_derived_output(approval, derived)
    other = mint_approval(
        operator=_operator(),
        binding=_binding(),
        reviewed_bytes=b'{"other": true}',
        final_decision_bytes=_final(),
        approved_at=NOW,
    )
    assert other.fingerprint() != approval.fingerprint()
    with pytest.raises(AuthorityRefused) as excinfo:
        verify_derived(bound, other.fingerprint(), derived)
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED


# --- 5. changed-content / cross-revision / revoked refuse, no output -------- #


def test_changed_snapshot_bytes_refuse_with_no_output(tmp_path: Path) -> None:
    snapshot = _snapshot()
    record = _mint_for(snapshot)
    changed = bytearray(snapshot.bytes_for("hash"))
    changed[10] ^= 0x01
    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=snapshot.binding,
            reviewed_bytes=bytes(changed),
            final_decision_bytes=snapshot.final_bytes_for("hash"),
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=snapshot.final_bytes_for("display"),
            audit_append=lambda _e: None,
        )
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED
    assert not out.exists()


def test_cross_revision_reuse_refuses_with_no_output(tmp_path: Path) -> None:
    snapshot = _snapshot()
    record = _mint_for(snapshot)
    new = supersede(
        snapshot,
        canonical_json_bytes({"batch_id": "BATCH-001", "revision": 2}),
        _operator(),
        captured_at=LATER,
    )
    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=new.binding,
            reviewed_bytes=new.bytes_for("hash"),
            final_decision_bytes=new.final_bytes_for("hash"),
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=new.final_bytes_for("display"),
            audit_append=lambda _e: None,
        )
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH
    assert not out.exists()


def test_revoked_approval_refuses_with_no_output(tmp_path: Path) -> None:
    snapshot = _snapshot()
    record = _mint_for(snapshot)
    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=snapshot.binding,
            reviewed_bytes=snapshot.bytes_for("hash"),
            final_decision_bytes=snapshot.final_bytes_for("hash"),
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=snapshot.final_bytes_for("display"),
            audit_append=lambda _e: None,
            revoked_fingerprints=frozenset({record.fingerprint()}),
        )
    assert excinfo.value.code == APPROVAL_REVOKED
    assert not out.exists()


# --- 6. operator identity stays publisher-constructed ------------------------ #


@pytest.mark.parametrize("source", ["model", "worker", "worker-forged"])
def test_forged_operator_source_refuses(source: str) -> None:
    with pytest.raises(AuthorityRefused) as excinfo:
        OperatorIdentity(identity="lifecycle-operator@example", source=source)
    assert excinfo.value.code == APPROVAL_NOT_OPERATOR


def test_only_publisher_context_identity_mints_and_verifies() -> None:
    snapshot = _snapshot()
    operator = OperatorIdentity(
        identity="lifecycle-operator@example", source="publisher-operator-context"
    )
    record = mint_approval(
        operator=operator,
        binding=snapshot.binding,
        reviewed_bytes=snapshot.bytes_for("hash"),
        final_decision_bytes=snapshot.final_bytes_for("hash"),
        approved_at=NOW,
    )
    assert record.operator_identity == "lifecycle-operator@example"
    verified = verify_approval(
        record=record,
        expected_binding=snapshot.binding,
        reviewed_bytes=snapshot.bytes_for("hash"),
        final_decision_bytes=snapshot.final_bytes_for("hash"),
        policy_version=POLICY,
        now=NOW,
    )
    assert verified.operator_identity == operator.identity
