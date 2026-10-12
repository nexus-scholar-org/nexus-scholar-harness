"""AG-03A approval-binding tests (cross-platform policy logic).

These tests exercise the *binding and refusal* semantics of the feasibility
adapter. They deliberately do **not** claim enforcement: who may write the
approval record is an OS property proven in
``tests/authority/test_isolation_windows.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scholar_harness.authority import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_EXPIRED,
    APPROVAL_MISSING,
    APPROVAL_NOT_OPERATOR,
    APPROVAL_POLICY_MISMATCH,
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

POLICY = "ag03a-approval-policy-v1"
NOW = "2026-10-12T12:00:00+00:00"

RECOMMENDATION = canonical_json_bytes(
    {
        "batch_id": "BATCH-001",
        "recommendation_revision": 1,
        "entries": [{"study_id": "STU-1", "decision": "INCLUDE"}],
        # Untrusted, self-reported provenance: none of this may become authority.
        "actor": "Dr. Human Reviewer",
        "method": "HUMAN",
        "confidence": 0.99,
        "critic": "PASS",
        "requires_human_review": True,
    }
)
FINAL_DECISION = canonical_json_bytes(
    {
        "batch_id": "BATCH-001",
        "revision": 1,
        "entries": [{"study_id": "STU-1", "decision": "INCLUDE"}],
    }
)


def binding(**overrides: object) -> ApprovalBinding:
    base = {
        "workspace_id": "WSP-" + "a" * 32,
        "run_id": "RUN-1",
        "batch_id": "BATCH-001",
        "protocol_fingerprint": "sha256:" + "b" * 64,
        "corpus_fingerprint": "sha256:" + "c" * 64,
        "recommendation_revision": 1,
        "policy_version": POLICY,
    }
    base.update(overrides)
    return ApprovalBinding(**base)  # type: ignore[arg-type]


OPERATOR = OperatorIdentity(
    identity="mouadh@local-operator", source="publisher-operator-context"
)


def approved_record(**overrides: object) -> ApprovalRecord:
    return mint_approval(
        operator=OPERATOR,
        binding=binding(**overrides),
        reviewed_bytes=RECOMMENDATION,
        final_decision_bytes=FINAL_DECISION,
        approved_at=NOW,
    )


def verify(record: ApprovalRecord | None, **kwargs: object) -> ApprovalRecord:
    params: dict[str, object] = {
        "record": record,
        "expected_binding": binding(),
        "reviewed_bytes": RECOMMENDATION,
        "final_decision_bytes": FINAL_DECISION,
        "policy_version": POLICY,
        "now": NOW,
    }
    params.update(kwargs)
    return verify_approval(**params)  # type: ignore[arg-type]


# --- authority comes from the operator context, not model output ----------- #


def test_recommendation_claimed_actor_never_becomes_the_approver() -> None:
    record = approved_record()
    assert record.operator_identity == OPERATOR.identity
    assert record.operator_identity != "Dr. Human Reviewer"

    # A different self-reported actor produces the same operator identity.
    other = canonical_json_bytes({"actor": "Someone Else", "entries": []})
    again = mint_approval(
        operator=OPERATOR,
        binding=binding(),
        reviewed_bytes=other,
        final_decision_bytes=FINAL_DECISION,
        approved_at=NOW,
    )
    assert again.operator_identity == OPERATOR.identity


def test_human_method_label_confidence_and_critic_pass_grant_nothing() -> None:
    payload = json.loads(RECOMMENDATION)
    assert payload["method"] == "HUMAN" and payload["critic"] == "PASS"
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(None)
    assert excinfo.value.code == APPROVAL_MISSING


def test_untrusted_operator_identity_is_refused_at_construction_and_verification() -> (
    None
):
    with pytest.raises(AuthorityRefused) as excinfo:
        OperatorIdentity(identity="agent-unknown", source="model")
    assert excinfo.value.code == APPROVAL_NOT_OPERATOR

    forged = ApprovalRecord(
        binding=binding(),
        recommendation_sha256=content_sha256(RECOMMENDATION),
        final_decision_sha256=content_sha256(FINAL_DECISION),
        operator_identity="agent-unknown",
        approved_at=NOW,
    )
    with pytest.raises(AuthorityRefused) as excinfo2:
        verify(forged)
    assert excinfo2.value.code == APPROVAL_NOT_OPERATOR


@pytest.mark.parametrize("source", ["model", "worker", "worker-forged"])
def test_untrusted_operator_source_is_refused(source: str) -> None:
    """F-01: only ``publisher-operator-context`` is an accepted identity source."""
    with pytest.raises(AuthorityRefused) as excinfo:
        OperatorIdentity(identity="mouadh@local-operator", source=source)
    assert excinfo.value.code == APPROVAL_NOT_OPERATOR


@pytest.mark.parametrize(
    "identity",
    ["", "agent-unknown", "unknown", "epoch", "AGENT-UNKNOWN", "  epoch  "],
)
def test_untrusted_operator_identity_is_refused_at_construction(
    identity: str,
) -> None:
    """F-06: the full untrusted identity set refuses at construction."""
    with pytest.raises(AuthorityRefused) as excinfo:
        OperatorIdentity(identity=identity, source="publisher-operator-context")
    assert excinfo.value.code == APPROVAL_NOT_OPERATOR


@pytest.mark.parametrize(
    "identity",
    ["", "agent-unknown", "unknown", "epoch", "AGENT-UNKNOWN", "  epoch  "],
)
def test_untrusted_operator_identity_is_refused_at_verification(
    identity: str,
) -> None:
    """F-06: the full untrusted identity set refuses at verification."""
    forged = ApprovalRecord(
        binding=binding(),
        recommendation_sha256=content_sha256(RECOMMENDATION),
        final_decision_sha256=content_sha256(FINAL_DECISION),
        operator_identity=identity,
        approved_at=NOW,
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(forged)
    assert excinfo.value.code == APPROVAL_NOT_OPERATOR


# --- scope, policy, content, revocation, expiry ---------------------------- #


def test_missing_approval_refuses() -> None:
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(None)
    assert excinfo.value.code == APPROVAL_MISSING


@pytest.mark.parametrize(
    "override",
    [
        {"workspace_id": "WSP-" + "d" * 32},
        {"run_id": "RUN-2"},
        {"batch_id": "BATCH-002"},
        {"protocol_fingerprint": "sha256:" + "e" * 64},
        {"corpus_fingerprint": "sha256:" + "f" * 64},
        {"recommendation_revision": 2},
    ],
    ids=["workspace", "run", "batch", "protocol", "corpus", "revision"],
)
def test_replay_into_a_different_scope_refuses(override: dict[str, object]) -> None:
    record = approved_record()
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(record, expected_binding=binding(**override))
    assert excinfo.value.code == APPROVAL_SCOPE_MISMATCH


def test_policy_version_mismatch_refuses() -> None:
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(approved_record(), policy_version="ag03a-approval-policy-v2")
    assert excinfo.value.code == APPROVAL_POLICY_MISMATCH


def test_changed_recommendation_content_invalidates_approval() -> None:
    record = approved_record()
    changed = canonical_json_bytes(
        {"entries": [{"study_id": "STU-1", "decision": "EXCLUDE"}]}
    )
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(record, reviewed_bytes=changed)
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED


def test_changed_final_decision_content_invalidates_approval() -> None:
    record = approved_record()
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(
            record,
            final_decision_bytes=b'{"entries":[{"study_id":"STU-1","decision":"EXCLUDE"}]}',
        )
    assert excinfo.value.code == APPROVAL_CONTENT_CHANGED


def test_revoked_approval_refuses() -> None:
    record = approved_record()
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(record, revoked_fingerprints=frozenset({record.fingerprint()}))
    assert excinfo.value.code == APPROVAL_REVOKED


def test_expired_approval_refuses_but_fresh_one_passes() -> None:
    record = approved_record()
    verify(record, now="2026-10-12T12:09:00+00:00", max_age_seconds=600)
    with pytest.raises(AuthorityRefused) as excinfo:
        verify(record, now="2026-10-12T12:11:00+00:00", max_age_seconds=600)
    assert excinfo.value.code == APPROVAL_EXPIRED


# --- override preserves the original -------------------------------------- #


def test_override_preserves_original_and_creates_a_new_revision() -> None:
    changed = canonical_json_bytes(
        {"entries": [{"study_id": "STU-1", "decision": "EXCLUDE"}]}
    )
    revision, preserved = record_override(
        original_bytes=RECOMMENDATION,
        new_final_decision_bytes=changed,
        current_revision=1,
    )
    assert revision == 2
    assert preserved == RECOMMENDATION
    assert content_sha256(preserved) == content_sha256(RECOMMENDATION)


def test_identical_override_does_not_burn_a_revision() -> None:
    revision, preserved = record_override(
        original_bytes=RECOMMENDATION,
        new_final_decision_bytes=RECOMMENDATION,
        current_revision=1,
    )
    assert revision == 1
    assert preserved == RECOMMENDATION


# --- promotion ------------------------------------------------------------- #


def test_promotion_writes_output_and_attributable_audit(tmp_path: Path) -> None:
    events: list[dict[str, object]] = []
    out = tmp_path / "publisher" / "final_decisions.json"
    result = promote(
        record=approved_record(),
        expected_binding=binding(),
        reviewed_bytes=RECOMMENDATION,
        final_decision_bytes=FINAL_DECISION,
        policy_version=POLICY,
        now=NOW,
        output_path=out,
        output_bytes=FINAL_DECISION,
        audit_append=events.append,
    )
    assert out.read_bytes() == FINAL_DECISION
    assert result.output_sha256 == content_sha256(FINAL_DECISION)
    assert events and events[0]["operator_identity"] == OPERATOR.identity
    assert events[0]["approval_fingerprint"] == approved_record().fingerprint()


def test_identical_retry_is_idempotent(tmp_path: Path) -> None:
    out = tmp_path / "final_decisions.json"
    kwargs: dict[str, object] = {
        "record": approved_record(),
        "expected_binding": binding(),
        "reviewed_bytes": RECOMMENDATION,
        "final_decision_bytes": FINAL_DECISION,
        "policy_version": POLICY,
        "now": NOW,
        "output_path": out,
        "output_bytes": FINAL_DECISION,
        "audit_append": lambda _e: None,
    }
    first = promote(**kwargs)  # type: ignore[arg-type]
    second = promote(**kwargs)  # type: ignore[arg-type]
    assert first.idempotent is False
    assert second.idempotent is True


def test_audit_failure_leaves_no_consumable_output(tmp_path: Path) -> None:
    out = tmp_path / "final_decisions.json"

    def failing_audit(_event: dict[str, object]) -> None:
        raise OSError("journal unavailable")

    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=approved_record(),
            expected_binding=binding(),
            reviewed_bytes=RECOMMENDATION,
            final_decision_bytes=FINAL_DECISION,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=FINAL_DECISION,
            audit_append=failing_audit,
        )
    assert excinfo.value.code == PROMOTION_AUDIT_FAILED
    assert not out.exists()


def test_refused_promotion_leaves_no_output(tmp_path: Path) -> None:
    out = tmp_path / "final_decisions.json"
    with pytest.raises(AuthorityRefused) as excinfo:
        promote(
            record=None,
            expected_binding=binding(),
            reviewed_bytes=RECOMMENDATION,
            final_decision_bytes=FINAL_DECISION,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=FINAL_DECISION,
            audit_append=lambda _e: None,
        )
    assert excinfo.value.code == APPROVAL_MISSING
    assert not out.exists()


def test_promotion_write_failure_removes_output_and_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-03: a write failure cleans both output and .tmp, then re-raises as-is.

    Covers the stale-pre-existing-output case: the stale file (different bytes,
    no longer verified-current) must also be removed rather than left consumable.
    """
    from pathlib import Path as _Path

    out = tmp_path / "final_decisions.json"
    # Stale pre-existing output with DIFFERENT bytes (no longer verified-current).
    out.write_bytes(b'{"stale": true}')
    assert out.exists()

    def failing_write_bytes(self: _Path, *args: object, **kwargs: object) -> int:
        raise OSError("injected write failure")

    monkeypatch.setattr(_Path, "write_bytes", failing_write_bytes)
    with pytest.raises(OSError, match="injected write failure"):
        promote(
            record=approved_record(),
            expected_binding=binding(),
            reviewed_bytes=RECOMMENDATION,
            final_decision_bytes=FINAL_DECISION,
            policy_version=POLICY,
            now=NOW,
            output_path=out,
            output_bytes=FINAL_DECISION,
            audit_append=lambda _e: None,
        )
    assert not out.exists()
    assert not out.with_name(out.name + ".tmp").exists()
