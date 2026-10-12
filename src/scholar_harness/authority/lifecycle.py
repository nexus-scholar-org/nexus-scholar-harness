"""Production single-screener review lifecycle (AG-03B).

Bounded lifecycle on top of the AG-03A feasibility adapter
(:mod:`scholar_harness.authority.binding`, extended here, never rewritten):

* worker submission is frozen into an immutable :class:`ReviewSnapshot`;
* ONE buffer object per content is thereafter the single source for
  parse/hash/display (closing the AG-03A F-02 residual, where
  same-bytes-for-parse/hash/display was caller discipline);
* operator review binds an approval to the snapshot bytes at promotion;
* an operator override preserves the original snapshot bytes verbatim and
  creates a new revision linked by ``supersedes``;
* refusals are persisted as durable records through a caller-supplied sink;
* derived outputs are bound to the approval fingerprint they were generated
  under.

Explicit non-claims (AG-03C scope, not built here): no coherent publication
generations, no downstream currentness enforcement, no crash recovery, no
concurrency/atomicity claims. POSIX arrangement unproven (Windows MIC remains
the implemented mechanism in :mod:`scholar_harness.authority.isolation`,
reused as-is). No guarantee against administrator compromise. Authority still
comes only from a publisher-constructed :class:`OperatorIdentity`; enforcement
of *who may write* publisher state remains the deployment property supplied by
:mod:`scholar_harness.authority.isolation`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from scholar_harness.authority.binding import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_SCOPE_MISMATCH,
    ApprovalBinding,
    ApprovalRecord,
    AuthorityRefused,
    OperatorIdentity,
    canonical_json_bytes,
    content_sha256,
)

#: Sidecar identity for the immutable review snapshot.
REVIEW_SNAPSHOT_SCHEMA = "harness-review-snapshot-v1"

#: Sidecar identity for a derived output bound to one approval.
DERIVED_OUTPUT_SCHEMA = "harness-derived-output-v1"

#: Sidecar identity for a durable refusal record.
REFUSAL_RECORD_SCHEMA = "harness-refusal-record-v1"

#: Views that all resolve to the single snapshot buffer.
_SNAPSHOT_VIEWS = ("parse", "hash", "display")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- immutable review snapshot --------------------------------------------- #


@dataclass(frozen=True)
class ReviewSnapshot:
    """A frozen snapshot of one worker submission under operator review.

    Each content (recommendation bytes, final-decision bytes) is held in
    exactly ONE immutable buffer. :meth:`bytes_for` (and
    :meth:`final_bytes_for`) return that same buffer object for every view,
    so a caller cannot display bytes-A while hashing bytes-B: parse, hash
    and display all read the identical bytes.
    """

    binding: ApprovalBinding
    reviewed_bytes: bytes
    final_decision_bytes: bytes
    recommendation_sha256: str
    final_decision_sha256: str
    captured_at: str
    supersedes: str | None = None
    superseded_by: str | None = None
    schema: str = REVIEW_SNAPSHOT_SCHEMA

    def bytes_for(self, view: str) -> bytes:
        """Return the single reviewed-content buffer for any view.

        ``view`` is one of ``"parse"``, ``"hash"`` or ``"display"``; all
        three return the identical bytes object.
        """
        if view not in _SNAPSHOT_VIEWS:
            raise ValueError(
                f"unknown snapshot view {view!r}; expected one of {list(_SNAPSHOT_VIEWS)}"
            )
        return self.reviewed_bytes

    def final_bytes_for(self, view: str) -> bytes:
        """Return the single final-decision buffer for any view.

        Mirrors :meth:`bytes_for` for the proposed final-decision content:
        all three views return the identical bytes object.
        """
        if view not in _SNAPSHOT_VIEWS:
            raise ValueError(
                f"unknown snapshot view {view!r}; expected one of {list(_SNAPSHOT_VIEWS)}"
            )
        return self.final_decision_bytes

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "binding": self.binding.as_dict(),
            "recommendation_sha256": self.recommendation_sha256,
            "final_decision_sha256": self.final_decision_sha256,
            "captured_at": self.captured_at,
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
        }

    def fingerprint(self) -> str:
        return content_sha256(canonical_json_bytes(self.as_dict()))


def capture_snapshot(
    reviewed_bytes: bytes,
    final_decision_bytes: bytes,
    binding: ApprovalBinding,
    *,
    captured_at: str | None = None,
) -> ReviewSnapshot:
    """Freeze a worker submission into an immutable review snapshot.

    The snapshot copies both inputs into private immutable buffers and
    records their content hashes alongside ``binding``. Thereafter
    :meth:`ReviewSnapshot.bytes_for` is the single source for
    parse/hash/display of the reviewed content.
    """
    reviewed_copy = bytes(reviewed_bytes)
    final_copy = bytes(final_decision_bytes)
    return ReviewSnapshot(
        binding=binding,
        reviewed_bytes=reviewed_copy,
        final_decision_bytes=final_copy,
        recommendation_sha256=content_sha256(reviewed_copy),
        final_decision_sha256=content_sha256(final_copy),
        captured_at=captured_at if captured_at is not None else _utcnow_iso(),
    )


# --- revision chain with supersession -------------------------------------- #


def supersede(
    snapshot: ReviewSnapshot,
    new_final_bytes: bytes,
    operator: OperatorIdentity,
    *,
    captured_at: str | None = None,
) -> ReviewSnapshot:
    """Create a new reviewed revision preserving the original bytes verbatim.

    The original recommendation buffer is carried over byte-identical; the
    override produces a distinct revision (``recommendation_revision + 1``)
    whose ``supersedes`` field links the prior snapshot fingerprint and whose
    ``superseded_by`` records the overriding operator. An identical
    ``new_final_bytes`` is idempotent and returns ``snapshot`` unchanged
    (no revision is burned), mirroring :func:`binding.record_override`.

    ``operator`` is only accepted as a publisher-constructed
    :class:`OperatorIdentity` (its constructor already refuses any other
    source); it is recorded, never re-derived here.
    """
    new_final_copy = bytes(new_final_bytes)
    if new_final_copy == snapshot.final_decision_bytes:
        return snapshot
    prior = snapshot.binding
    new_binding = ApprovalBinding(
        workspace_id=prior.workspace_id,
        run_id=prior.run_id,
        batch_id=prior.batch_id,
        protocol_fingerprint=prior.protocol_fingerprint,
        corpus_fingerprint=prior.corpus_fingerprint,
        recommendation_revision=prior.recommendation_revision + 1,
        policy_version=prior.policy_version,
    )
    return ReviewSnapshot(
        binding=new_binding,
        reviewed_bytes=snapshot.reviewed_bytes,
        final_decision_bytes=new_final_copy,
        recommendation_sha256=snapshot.recommendation_sha256,
        final_decision_sha256=content_sha256(new_final_copy),
        captured_at=captured_at if captured_at is not None else _utcnow_iso(),
        supersedes=snapshot.fingerprint(),
        superseded_by=operator.identity,
    )


# --- durable refusal record ------------------------------------------------- #


def record_refusal(
    refusal: AuthorityRefused,
    binding: ApprovalBinding,
    sink: Callable[[dict[str, Any]], None],
    *,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Persist a refusal record through ``sink`` and return it.

    The record carries the refusal ``code``/``message``/``details`` flat
    alongside the scope ``binding`` and a timestamp, so a JSONL or
    in-memory sink needs no further shaping. A failing ``sink`` is never
    swallowed: the original exception propagates and nothing is reported
    as recorded.
    """
    record: dict[str, Any] = {
        "schema": REFUSAL_RECORD_SCHEMA,
        "code": refusal.code,
        "message": refusal.message,
        "details": dict(refusal.details),
        "binding": binding.as_dict(),
        "recorded_at": recorded_at if recorded_at is not None else _utcnow_iso(),
    }
    sink(record)
    return record


# --- derived-output binding ------------------------------------------------- #


@dataclass(frozen=True)
class DerivedOutputRecord:
    """Binds one derived output to the approval it was generated under."""

    approval_fingerprint: str
    output_sha256: str
    schema: str = DERIVED_OUTPUT_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "approval_fingerprint": self.approval_fingerprint,
            "output_sha256": self.output_sha256,
        }


def bind_derived_output(
    approval: ApprovalRecord, derived_bytes: bytes
) -> DerivedOutputRecord:
    """Link ``derived_bytes`` to ``approval`` via content fingerprints."""
    return DerivedOutputRecord(
        approval_fingerprint=approval.fingerprint(),
        output_sha256=content_sha256(bytes(derived_bytes)),
    )


def verify_derived(
    record: DerivedOutputRecord,
    approval_fingerprint: str,
    derived_bytes: bytes,
) -> DerivedOutputRecord:
    """Re-verify a derived output against its approval fingerprint and bytes.

    Any mismatch refuses with ``APPROVAL_CONTENT_CHANGED``: the output is no
    longer the bytes the approval was granted for, or it is presented under
    a different approval.
    """
    if record.schema != DERIVED_OUTPUT_SCHEMA:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            f"unexpected derived-output schema {record.schema!r}",
        )
    if record.approval_fingerprint != approval_fingerprint:
        raise AuthorityRefused(
            APPROVAL_CONTENT_CHANGED,
            "derived output is presented under a different approval",
            approved_fingerprint=record.approval_fingerprint,
            presented_fingerprint=approval_fingerprint,
        )
    if record.output_sha256 != content_sha256(bytes(derived_bytes)):
        raise AuthorityRefused(
            APPROVAL_CONTENT_CHANGED,
            "derived output bytes changed after binding",
            expected_output_sha256=record.output_sha256,
            presented_output_sha256=content_sha256(bytes(derived_bytes)),
        )
    return record
