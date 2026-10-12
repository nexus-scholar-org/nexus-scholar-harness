"""AG-03A end-to-end disposable-flow proof (cross-platform, hermetic).

Demonstrates the complete protected-publisher proof path on disposable
``tmp_path`` state with synthetic bytes only, using the already-present
adapter (:mod:`scholar_harness.authority.binding`) plus the AG-02 workflow
gates (:mod:`scholar_harness.screening.integrity`).

Proof-item map (feasibility spec sections 19-37, bounded items 1-6):

* :func:`test_full_disposable_path` -- proof item: accepted batch through
  AG-02 gates, snapshot, operator review of the exact bytes, bound approval,
  fail-closed promotion with attributed audit.
* :func:`test_worker_submission_cannot_self_approve` -- proof item: forged
  worker fields confer no authority (APPROVAL_MISSING without an approval).
* :func:`test_content_swap_after_review_invalidates` -- proof item:
  revalidation at promotion (APPROVAL_CONTENT_CHANGED).
* :func:`test_replay_across_batch_refuses` -- proof item: scope binding
  (APPROVAL_SCOPE_MISMATCH on cross-batch replay).
* :func:`test_override_creates_new_revision_preserving_original` -- proof
  item: operator override preserves the original and burns a new revision;
  the old approval does not cover the new revision.
* :func:`test_audit_failure_is_not_success` -- proof item: fail-closed
  promotion (PROMOTION_AUDIT_FAILED leaves no consumable output).
* :func:`test_expired_approval_refuses` / :func:`test_revoked_approval_refuses`
  -- proof item: stale and revoked approvals refuse.

Explicit non-claims (every test below): no production atomicity, no
concurrency safety, no downstream enforcement, no scientific-truth judgment.
The OS deployment boundary (who may write publisher state) is proven in
``tests/authority/test_isolation_windows.py`` and is NOT exercised here; this
file intentionally calls no OS functions so it passes on Windows and POSIX.
AG-02 gates are workflow-integrity checks only, not authorization.

Snapshot-discipline limitation: same-bytes-for-parse/hash/display is caller
discipline in this proof; the API hashes whatever bytes it is given. A caller
that displays bytes-A while hashing bytes-B still gets a valid record. AG-03B
must introduce a single immutable buffer.

Refusals are preserved as in-memory AuthorityRefused.as_dict() records in this
proof; durable refusal audit is AG-03B scope.

There is no guarantee against administrator compromise.
POSIX arrangement unproven (Windows MIC is the implemented mechanism).
There are no concurrency/atomicity claims.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scholar_harness.authority.binding import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_EXPIRED,
    APPROVAL_MISSING,
    APPROVAL_REVOKED,
    APPROVAL_SCOPE_MISMATCH,
    PROMOTION_AUDIT_FAILED,
    ApprovalBinding,
    ApprovalRecord,
    AuthorityRefused,
    OperatorIdentity,
    canonical_json_bytes,
    content_sha256,
    mint_approval,
    promote,
    record_override,
    verify_approval,
)
from scholar_harness.authority import isolation
from scholar_harness.screening.integrity import (
    check_exact_coverage,
    check_no_unresolved_for_finalize,
)

POLICY = "ag03a-approval-policy-v1"
NOW = "2026-10-12T12:00:00+00:00"
LATER_THAN_WINDOW = "2026-10-12T12:11:00+00:00"  # 660 s after NOW

WORKSPACE_ID = "WSP-" + "a" * 32
RUN_ID = "RUN-DISPOSABLE-1"
BATCH_ID = "BATCH-001"
OTHER_BATCH_ID = "BATCH-002"
PROTOCOL_FP = "sha256:" + "b" * 64  # immutable parent hash (synthetic)
CORPUS_FP = "sha256:" + "c" * 64  # immutable parent hash (synthetic)

# Forged, worker-authored provenance. Must never become authority.
FORGED_ACTOR = "Dr. Forged Human Reviewer"


def _entries() -> list[dict[str, object]]:
    return [
        {"study_id": "STU-001", "decision": "INCLUDE"},
        {"study_id": "STU-002", "decision": "INCLUDE"},
    ]


def _binding(
    batch_id: str = BATCH_ID, recommendation_revision: int = 1
) -> ApprovalBinding:
    return ApprovalBinding(
        workspace_id=WORKSPACE_ID,
        run_id=RUN_ID,
        batch_id=batch_id,
        protocol_fingerprint=PROTOCOL_FP,
        corpus_fingerprint=CORPUS_FP,
        recommendation_revision=recommendation_revision,
        policy_version=POLICY,
    )


def _recommendation_bytes(
    batch_id: str = BATCH_ID, recommendation_revision: int = 1
) -> bytes:
    return canonical_json_bytes(
        {
            "batch_id": batch_id,
            "recommendation_revision": recommendation_revision,
            "entries": _entries(),
            # Untrusted self-reported provenance: confers nothing.
            "actor": FORGED_ACTOR,
            "method": "HUMAN",
            "confidence": 0.99,
            "critic": "PASS",
        }
    )


def _final_decision_bytes(batch_id: str = BATCH_ID, revision: int = 1) -> bytes:
    return canonical_json_bytes(
        {"batch_id": batch_id, "revision": revision, "entries": _entries()}
    )


def _operator() -> OperatorIdentity:
    return OperatorIdentity(
        identity="disposable-operator@example", source="publisher-operator-context"
    )


def _mint(
    binding: ApprovalBinding, reviewed: bytes, final_decision: bytes
) -> ApprovalRecord:
    return mint_approval(
        operator=_operator(),
        binding=binding,
        reviewed_bytes=reviewed,
        final_decision_bytes=final_decision,
        approved_at=NOW,
    )


def test_full_disposable_path(tmp_path: Path) -> None:
    """AG-03A proof item: full disposable path from accepted batch to audited output.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    # Accepted synthetic batch (2 studies) + immutable parent hashes feed the
    # AG-02 workflow gates (integrity only, not authorization).
    candidate_ids = {"STU-001", "STU-002"}
    entries = [
        {"study_id": "STU-001", "decision": "INCLUDE"},
        {"study_id": "STU-002", "decision": "INCLUDE"},
    ]
    check_exact_coverage(candidate_ids, entries)
    check_no_unresolved_for_finalize(entries)

    # Worker-authored recommendation carrying forged authority-looking fields.
    recommendation = _recommendation_bytes()
    payload = json.loads(recommendation)
    assert payload["actor"] == FORGED_ACTOR
    assert payload["method"] == "HUMAN"
    assert payload["confidence"] == 0.99
    assert payload["critic"] == "PASS"

    # Snapshot the exact bytes (sha recorded); the operator reviews the snapshot.
    snapshot_path = tmp_path / "inbox" / "recommendation.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(recommendation)
    snapshot_sha = content_sha256(recommendation)
    assert content_sha256(snapshot_path.read_bytes()) == snapshot_sha

    reviewed = snapshot_path.read_bytes()
    assert reviewed == recommendation
    assert reviewed == snapshot_path.read_bytes()

    binding = _binding()
    final_decision = _final_decision_bytes()
    record = _mint(binding, reviewed, final_decision)

    events: list[dict[str, object]] = []
    out = tmp_path / "publisher" / "final_decisions.json"
    result = promote(
        record=record,
        expected_binding=binding,
        reviewed_bytes=reviewed,
        final_decision_bytes=final_decision,
        policy_version=POLICY,
        now=NOW,
        output_path=out,
        output_bytes=final_decision,
        audit_append=events.append,
    )

    assert out.read_bytes() == final_decision
    assert result.output_sha256 == content_sha256(final_decision)
    assert len(events) == 1
    assert events[0]["operator_identity"] == "disposable-operator@example"
    assert events[0]["approval_fingerprint"] == record.fingerprint()

    # Forged worker fields confer nothing and leak nowhere into authority.
    assert record.operator_identity == "disposable-operator@example"
    assert record.operator_identity != FORGED_ACTOR
    record_json = json.dumps(record.as_dict(), sort_keys=True)
    event_json = json.dumps(events[0], sort_keys=True)
    assert FORGED_ACTOR not in record_json
    assert FORGED_ACTOR not in event_json


def test_worker_submission_cannot_self_approve(tmp_path: Path) -> None:
    """AG-03A proof item: forged worker fields alone cannot authorize promotion.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=None,
            expected_binding=_binding(),
            reviewed_bytes=recommendation,
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
        )
    assert excinfo.value.code == APPROVAL_MISSING
    assert not out.exists()


def test_content_swap_after_review_invalidates(tmp_path: Path) -> None:
    """AG-03A proof item: revalidation at promotion (D7); swapped bytes refuse.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    record = _mint(_binding(), recommendation, final_decision)

    swapped = bytearray(recommendation)
    swapped[10] ^= 0x01
    assert bytes(swapped) != recommendation

    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=_binding(),
            reviewed_bytes=bytes(swapped),
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
        )
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED
    assert not out.exists()


def test_replay_across_batch_refuses(tmp_path: Path) -> None:
    """AG-03A proof item: scope binding; BATCH-001 approval is useless for BATCH-002.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    record = _mint(_binding(batch_id=BATCH_ID), recommendation, final_decision)

    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=_binding(batch_id=OTHER_BATCH_ID),
            reviewed_bytes=recommendation,
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
        )
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH
    assert not out.exists()


def test_override_creates_new_revision_preserving_original(tmp_path: Path) -> None:
    """AG-03A proof item: override burns a new revision, preserves the original.

    The old (revision-1) approval no longer verifies the new (revision-2)
    binding. Uses disposable ``tmp_path`` only to read back the preserved bytes.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    original = _recommendation_bytes(recommendation_revision=1)
    changed_final = canonical_json_bytes(
        {
            "batch_id": BATCH_ID,
            "revision": 2,
            "entries": [
                {"study_id": "STU-001", "decision": "INCLUDE"},
                {"study_id": "STU-002", "decision": "EXCLUDE"},
            ],
        }
    )
    assert changed_final != original

    new_revision, preserved = record_override(
        original_bytes=original,
        new_final_decision_bytes=changed_final,
        current_revision=1,
    )
    assert new_revision == 2
    assert preserved == original
    assert content_sha256(preserved) == content_sha256(original)

    # Byte-identical preservation check through disposable state.
    preserved_path = tmp_path / "publisher" / "recommendation_rev1.json"
    preserved_path.parent.mkdir(parents=True, exist_ok=True)
    preserved_path.write_bytes(preserved)
    assert preserved_path.read_bytes() == original

    old_record = _mint(
        _binding(recommendation_revision=1), original, _final_decision_bytes()
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        verify_approval(
            record=old_record,
            expected_binding=_binding(recommendation_revision=new_revision),
            reviewed_bytes=original,
            final_decision_bytes=_final_decision_bytes(),
            policy_version=POLICY,
            now=NOW,
        )
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH


def test_audit_failure_is_not_success(tmp_path: Path) -> None:
    """AG-03A proof item (D7): audit failure leaves no consumable output.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    record = _mint(_binding(), recommendation, final_decision)
    out = tmp_path / "publisher" / "final_decisions.json"

    def failing_audit(_event: dict[str, object]) -> None:
        raise OSError("disposable journal unavailable")

    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=_binding(),
            reviewed_bytes=recommendation,
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=failing_audit,
        )
    assert excinfo.value.code == PROMOTION_AUDIT_FAILED
    assert not out.exists()
    assert not out.with_name(out.name + ".tmp").exists()


def test_expired_approval_refuses(tmp_path: Path) -> None:
    """AG-03A proof item: a stale approval outside the max-age window refuses.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    record = _mint(_binding(), recommendation, final_decision)
    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=_binding(),
            reviewed_bytes=recommendation,
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=LATER_THAN_WINDOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
            max_age_seconds=600,
        )
    assert excinfo.value.code == APPROVAL_EXPIRED
    assert not out.exists()


def test_revoked_approval_refuses(tmp_path: Path) -> None:
    """AG-03A proof item: a revoked approval (fingerprint set) refuses.

    Non-claims: no production atomicity, no concurrency safety, no downstream
    enforcement, no scientific-truth judgment.
    """
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    record = _mint(_binding(), recommendation, final_decision)
    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=_binding(),
            reviewed_bytes=recommendation,
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
            revoked_fingerprints=frozenset({record.fingerprint()}),
        )
    assert excinfo.value.code == APPROVAL_REVOKED
    assert not out.exists()


def test_snapshot_discipline_limitation_displayed_bytes_are_not_bound() -> None:
    """F-02 limitation: the record binds the hashed bytes only, not displayed bytes.

    Same-bytes-for-parse/hash/display is caller discipline in this proof; the
    API hashes whatever bytes it is given. A caller that displays bytes-A while
    hashing bytes-B still gets a valid record, so the divergence below is
    detectable: ``recommendation_sha256`` does NOT equal the displayed
    content's hash. AG-03B must introduce a single immutable buffer.
    """
    displayed = _recommendation_bytes()
    hashed = canonical_json_bytes(
        {
            "batch_id": BATCH_ID,
            "recommendation_revision": 1,
            "entries": [{"study_id": "STU-001", "decision": "EXCLUDE"}],
            "actor": FORGED_ACTOR,
            "method": "HUMAN",
            "confidence": 0.99,
            "critic": "PASS",
        }
    )
    assert hashed != displayed
    record = _mint(_binding(), hashed, _final_decision_bytes())
    assert record.recommendation_sha256 == content_sha256(hashed)
    assert record.recommendation_sha256 != content_sha256(displayed)


def test_capability_report_declares_absent_routes() -> None:
    """F-04: the proof exposes no HTTP service, credential file, or operator UI."""
    report = isolation.capability_report()
    assert report["http_service"] is None
    assert report["credential_file"] is None
    assert report["operator_ui"] is None


def test_refusal_record_carries_scope_and_content_details(tmp_path: Path) -> None:
    """F-05: the raised AuthorityRefused.as_dict() IS the preserved refusal record."""
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    record = _mint(_binding(batch_id=BATCH_ID), recommendation, final_decision)

    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as scope_exc:
        promote(
            record=record,
            expected_binding=_binding(batch_id=OTHER_BATCH_ID),
            reviewed_bytes=recommendation,
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
        )
    assert scope_exc.value.code == APPROVAL_SCOPE_MISMATCH
    scope_dict = scope_exc.value.as_dict()
    assert scope_dict["code"] == APPROVAL_SCOPE_MISMATCH
    assert "approved" in scope_dict["details"] and "expected" in scope_dict["details"]
    assert not out.exists()

    swapped = bytearray(recommendation)
    swapped[10] ^= 0x01
    out2 = tmp_path / "publisher" / "final_decisions_swapped.json"
    with pytest.raises(AuthorityRefused) as content_exc:
        promote(
            record=record,
            expected_binding=_binding(batch_id=BATCH_ID),
            reviewed_bytes=bytes(swapped),
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out2,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
        )
    assert content_exc.value.code == APPROVAL_CONTENT_CHANGED
    content_dict = content_exc.value.as_dict()
    assert content_dict["code"] == APPROVAL_CONTENT_CHANGED
    assert (
        "code" in content_dict
        and "message" in content_dict
        and "details" in content_dict
    )
    assert not out2.exists()


def test_cleared_approval_registry_refuses(tmp_path: Path) -> None:
    """F-08: a cleared disposable registry (record reference dropped) refuses.

    The disposable registry in this proof is the record reference itself;
    AG-03C owns durable generations.
    """
    recommendation = _recommendation_bytes()
    final_decision = _final_decision_bytes()
    record = _mint(_binding(), recommendation, final_decision)
    assert record.fingerprint()

    # Simulate a registry clear by dropping the reference.
    record = None
    out = tmp_path / "publisher" / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=record,
            expected_binding=_binding(),
            reviewed_bytes=recommendation,
            final_decision_bytes=final_decision,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=final_decision,
            audit_append=lambda _e: None,
        )
    assert excinfo.value.code == APPROVAL_MISSING
    assert not out.exists()
