"""AG-03A authority feasibility adapter (protected publisher / restricted worker).

This package exists only to prove, or disprove, the AG-03A deployment boundary.
It is not a production authorization service; AG-03B owns the production
recommendation/review lifecycle and AG-03C owns complete publication.

* :mod:`scholar_harness.authority.binding` - approval binding + verification logic.
* :mod:`scholar_harness.authority.isolation` - the OS deployment boundary that
  decides *who may write* publisher state, and whether a worker can be contained.
"""

from __future__ import annotations

from scholar_harness.authority.binding import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_EXPIRED,
    APPROVAL_MISSING,
    APPROVAL_NOT_OPERATOR,
    APPROVAL_POLICY_MISMATCH,
    APPROVAL_REVOKED,
    APPROVAL_SCHEMA,
    APPROVAL_SCOPE_MISMATCH,
    PROMOTION_AUDIT_FAILED,
    ApprovalBinding,
    ApprovalRecord,
    AuthorityRefused,
    OperatorIdentity,
    PromotionResult,
    canonical_json_bytes,
    content_sha256,
    mint_approval,
    promote,
    record_override,
    verify_approval,
)

__all__ = [
    "APPROVAL_CONTENT_CHANGED",
    "APPROVAL_EXPIRED",
    "APPROVAL_MISSING",
    "APPROVAL_NOT_OPERATOR",
    "APPROVAL_POLICY_MISMATCH",
    "APPROVAL_REVOKED",
    "APPROVAL_SCHEMA",
    "APPROVAL_SCOPE_MISMATCH",
    "PROMOTION_AUDIT_FAILED",
    "ApprovalBinding",
    "ApprovalRecord",
    "AuthorityRefused",
    "OperatorIdentity",
    "PromotionResult",
    "canonical_json_bytes",
    "content_sha256",
    "mint_approval",
    "promote",
    "record_override",
    "verify_approval",
]
