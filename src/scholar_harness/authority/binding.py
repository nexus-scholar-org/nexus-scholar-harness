"""Publisher approval binding for the AG-03A protected-publisher feasibility proof.

This is a **narrow feasibility adapter**, not a production authorization service.
It implements the minimum logic the AG-03A proof needs to show that an explicit
operator action can be bound to the exact reviewed content, and re-verified at
promotion. Enforcement of *who may write these records* is a deployment property
supplied by :mod:`scholar_harness.authority.isolation`; policy logic alone is not
an authority mechanism.

Design rules preserved from the AG architecture decision:

* Authority comes from a protected operator context, never from model output. A
  recommendation's ``actor``, ``method: HUMAN`` label, confidence, or critic
  PASS confers nothing and can never become the approver identity.
* The approval binds workspace, run, batch, exact parent hashes, recommendation
  revision + content hash, proposed final-decision content hash, policy version,
  the verified operator identity, and the actual approval time.
* Changing reviewed content invalidates the approval.
* An operator override preserves the original recommendation and creates a new
  reviewed revision; it never rewrites the original bytes.

Snapshot-discipline limitation: same-bytes-for-parse/hash/display is caller
discipline in this proof; the API hashes whatever bytes it is given. A caller
that displays bytes-A while hashing bytes-B still gets a valid record. AG-03B
must introduce a single immutable buffer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

#: Sidecar identity for the provisional, harness-owned approval record.
APPROVAL_SCHEMA = "harness-approval-record-v1"

# --- typed refusal codes --------------------------------------------------- #

APPROVAL_MISSING = "APPROVAL_MISSING"
APPROVAL_NOT_OPERATOR = "APPROVAL_NOT_OPERATOR"
APPROVAL_CONTENT_CHANGED = "APPROVAL_CONTENT_CHANGED"
APPROVAL_SCOPE_MISMATCH = "APPROVAL_SCOPE_MISMATCH"
APPROVAL_POLICY_MISMATCH = "APPROVAL_POLICY_MISMATCH"
APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
APPROVAL_REVOKED = "APPROVAL_REVOKED"
PROMOTION_AUDIT_FAILED = "PROMOTION_AUDIT_FAILED"

#: Identity strings that must never count as a verified human operator.
UNTRUSTED_OPERATOR_IDENTITIES = frozenset({"", "agent-unknown", "unknown", "epoch"})


class AuthorityRefused(RuntimeError):
    """Typed refusal to promote content without valid operator approval.

    Mirrors the ``ScreeningIntegrityRefused`` shape (stable ``code``, human
    ``message``, machine-readable ``details``) so callers can branch on it.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


def content_sha256(raw_bytes: bytes) -> str:
    """Return the ``sha256:<hex>`` fingerprint of the exact reviewed bytes.

    The same bytes are used for parsing, hashing and display; callers must pass
    the immutable snapshot, not a re-serialization.
    """
    return "sha256:" + sha256(raw_bytes).hexdigest()


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Deterministic JSON bytes for a record (sorted keys, no whitespace)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


# --- records --------------------------------------------------------------- #


@dataclass(frozen=True)
class OperatorIdentity:
    """A verified operator identity obtained from a publisher-controlled source.

    ``source`` is allowlisted at the API boundary: only
    ``"publisher-operator-context"`` is accepted and anything else refuses with
    ``APPROVAL_NOT_OPERATOR``. The deployment still decides who can write the
    context; the worker process cannot construct a trusted instance because it
    cannot write the publisher-owned context.
    """

    identity: str
    source: str

    def __post_init__(self) -> None:
        if self.source != "publisher-operator-context":
            raise AuthorityRefused(
                APPROVAL_NOT_OPERATOR,
                f"untrusted operator source {self.source!r}; "
                'only "publisher-operator-context" is accepted',
                identity=self.identity,
                source=self.source,
            )
        if self.identity.strip().lower() in UNTRUSTED_OPERATOR_IDENTITIES:
            raise AuthorityRefused(
                APPROVAL_NOT_OPERATOR,
                f"operator identity {self.identity!r} is not a verified human operator",
                identity=self.identity,
                source=self.source,
            )


@dataclass(frozen=True)
class ApprovalBinding:
    """The exact scope an approval is good for (no content hashes)."""

    workspace_id: str
    run_id: str
    batch_id: str
    protocol_fingerprint: str
    corpus_fingerprint: str
    recommendation_revision: int
    policy_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "protocol_fingerprint": self.protocol_fingerprint,
            "corpus_fingerprint": self.corpus_fingerprint,
            "recommendation_revision": self.recommendation_revision,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True)
class ApprovalRecord:
    """The immutable, harness-owned approval sidecar."""

    binding: ApprovalBinding
    recommendation_sha256: str
    final_decision_sha256: str
    operator_identity: str
    approved_at: str
    schema: str = APPROVAL_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "binding": self.binding.as_dict(),
            "recommendation_sha256": self.recommendation_sha256,
            "final_decision_sha256": self.final_decision_sha256,
            "operator_identity": self.operator_identity,
            "approved_at": self.approved_at,
        }

    def fingerprint(self) -> str:
        return content_sha256(canonical_json_bytes(self.as_dict()))


# --- operator approval (publisher side) ------------------------------------ #


def mint_approval(
    *,
    operator: OperatorIdentity,
    binding: ApprovalBinding,
    reviewed_bytes: bytes,
    final_decision_bytes: bytes,
    approved_at: str,
) -> ApprovalRecord:
    """Create an approval bound to the exact reviewed content.

    ``operator`` MUST come from the publisher's protected operator context. Any
    ``actor``/``reviewer``/``method``/``confidence``/``critic`` fields embedded in
    ``reviewed_bytes`` are irrelevant here and never influence the record.
    """
    return ApprovalRecord(
        binding=binding,
        recommendation_sha256=content_sha256(reviewed_bytes),
        final_decision_sha256=content_sha256(final_decision_bytes),
        operator_identity=operator.identity,
        approved_at=approved_at,
    )


def record_override(
    *, original_bytes: bytes, new_final_decision_bytes: bytes, current_revision: int
) -> tuple[int, bytes]:
    """Return ``(new_revision, preserved_original_bytes)`` for an operator override.

    The original recommendation bytes are returned unchanged; the override
    produces a distinct reviewed revision rather than rewriting the original.
    """
    if new_final_decision_bytes == original_bytes:
        return current_revision, original_bytes
    return current_revision + 1, original_bytes


# --- verification (publisher side, re-run at promotion) -------------------- #


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def verify_approval(
    *,
    record: ApprovalRecord | None,
    expected_binding: ApprovalBinding,
    reviewed_bytes: bytes,
    final_decision_bytes: bytes,
    policy_version: str,
    now: str,
    revoked_fingerprints: frozenset[str] = frozenset(),
    max_age_seconds: int | None = None,
) -> ApprovalRecord:
    """Re-verify an approval against the *current* content and scope.

    Raises :class:`AuthorityRefused` on any mismatch. Called again at promotion,
    so a content change after review cannot retain approval.
    """
    if record is None:
        raise AuthorityRefused(APPROVAL_MISSING, "no approval record for this batch")
    if record.schema != APPROVAL_SCHEMA:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH, f"unexpected approval schema {record.schema!r}"
        )
    if record.operator_identity.strip().lower() in UNTRUSTED_OPERATOR_IDENTITIES:
        raise AuthorityRefused(
            APPROVAL_NOT_OPERATOR,
            f"approval carries untrusted operator {record.operator_identity!r}",
        )
    if record.binding.as_dict() != expected_binding.as_dict():
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            "approval scope does not match the requested workspace/run/batch/parents/revision",
            approved=record.binding.as_dict(),
            expected=expected_binding.as_dict(),
        )
    if record.binding.policy_version != policy_version:
        raise AuthorityRefused(
            APPROVAL_POLICY_MISMATCH,
            "approval was granted under a different policy version",
            approved_policy=record.binding.policy_version,
            current_policy=policy_version,
        )
    if content_sha256(reviewed_bytes) != record.recommendation_sha256:
        raise AuthorityRefused(
            APPROVAL_CONTENT_CHANGED,
            "reviewed recommendation content changed after approval",
        )
    if content_sha256(final_decision_bytes) != record.final_decision_sha256:
        raise AuthorityRefused(
            APPROVAL_CONTENT_CHANGED,
            "proposed final-decision content changed after approval",
        )
    if record.fingerprint() in revoked_fingerprints:
        raise AuthorityRefused(APPROVAL_REVOKED, "approval has been revoked")
    if max_age_seconds is not None:
        age = _parse_time(now) - _parse_time(record.approved_at)
        if age > timedelta(seconds=max_age_seconds):
            raise AuthorityRefused(
                APPROVAL_EXPIRED,
                "approval is older than the policy maximum age",
                age_seconds=age.total_seconds(),
                max_age_seconds=max_age_seconds,
            )
    return record


# --- promotion (fail-closed) ----------------------------------------------- #


@dataclass(frozen=True)
class PromotionResult:
    output_path: str
    output_sha256: str
    idempotent: bool
    audit_event: dict[str, Any] = field(default_factory=dict)


def promote(
    *,
    record: ApprovalRecord | None,
    expected_binding: ApprovalBinding,
    reviewed_bytes: bytes,
    final_decision_bytes: bytes,
    policy_version: str,
    now: str,
    output_path: Path,
    output_bytes: bytes,
    audit_append: Callable[[dict[str, Any]], None],
    revoked_fingerprints: frozenset[str] = frozenset(),
    max_age_seconds: int | None = None,
) -> PromotionResult:
    """Verify, then publish a disposable final output with attributed audit.

    Fail-closed: if the audit append fails, the output is removed so a required
    authorization/provenance cannot be missing from consumable output. Identical
    retries are idempotent (byte-identical output is not rewritten).
    """
    verified = verify_approval(
        record=record,
        expected_binding=expected_binding,
        reviewed_bytes=reviewed_bytes,
        final_decision_bytes=final_decision_bytes,
        policy_version=policy_version,
        now=now,
        revoked_fingerprints=revoked_fingerprints,
        max_age_seconds=max_age_seconds,
    )

    digest = content_sha256(output_bytes)
    idempotent = output_path.exists() and output_path.read_bytes() == output_bytes
    tmp = output_path.with_name(output_path.name + ".tmp")
    if not idempotent:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            tmp.write_bytes(output_bytes)
            tmp.replace(output_path)
        except Exception:
            # Fail closed on write failure: remove both the sidecar and any
            # stale pre-existing output (no longer verified-current), then
            # re-raise the ORIGINAL exception unwrapped.
            for stale in (tmp, output_path):
                try:
                    stale.unlink(missing_ok=True)
                except Exception:
                    pass
            raise

    event = {
        "action": "SCREENING_FINAL_DECISIONS_PUBLISHED",
        "status": "SUCCESS",
        "operator_identity": verified.operator_identity,
        "approval_fingerprint": verified.fingerprint(),
        "batch_id": expected_binding.batch_id,
        "output_sha256": digest,
        "declared_at": now,
    }
    try:
        audit_append(event)
    except Exception as exc:  # noqa: BLE001 - any audit failure must fail closed
        output_path.unlink(missing_ok=True)
        raise AuthorityRefused(
            PROMOTION_AUDIT_FAILED,
            "audit append failed; refusing to leave consumable output without provenance",
            output_path=str(output_path),
            cause=type(exc).__name__,
        ) from exc

    return PromotionResult(
        output_path=str(output_path),
        output_sha256=digest,
        idempotent=idempotent,
        audit_event=event,
    )
