"""The console API refusal set (screening API contract §7).

Typed refusal codes the console returns as ``{"detail": {"code", "message"}}``.
They are the API's vocabulary, separate from the agent-role registry
(``contracts/envelope/registry.py``, ``Envelope@1``) and outside Contract v1.

Codes that predate this module keep their home and are re-exported here, so
the UI has one list to map to copy. ``tests/console/test_console_refusals.py``
keeps this set and the contract's §7 table in step: adding a code means adding
it here and to the contract in the same change.
"""

from __future__ import annotations

from scholar_harness.authority.pairing import PAIRING_CODE_INVALID
from scholar_harness.screening.integrity import (
    COVERAGE_INCOMPLETE,
    PROVENANCE_MISSING,
    STALE_BINDING,
    UNRESOLVED_FINALIZE_REFUSED,
)

# --- added by the screening API contract (M1a) -------------------------------
#: The agent's proposal is hidden: blinding is on and the study has no decision.
PROPOSAL_HIDDEN = "PROPOSAL_HIDDEN"
#: No accepted corpus snapshot; run ``nexus-scholar accept-corpus`` first.
SNAPSHOT_NOT_ACCEPTED = "SNAPSHOT_NOT_ACCEPTED"
#: The ``study_id`` is not in the bound corpus.
UNKNOWN_STUDY = "UNKNOWN_STUDY"
#: An EXCLUDE without a valid protocol reason code.
REASON_CODE_INVALID = "REASON_CODE_INVALID"
#: A decisions file differs from the decision events; publish refuses (M1b-0).
PROJECTION_STALE = "PROJECTION_STALE"
#: A phone-scoped token on a desktop-only route, or an expired token.
TOKEN_SCOPE_REFUSED = "TOKEN_SCOPE_REFUSED"
#: No recorded consent for this provider (M1b).
CONSENT_REQUIRED = "CONSENT_REQUIRED"
#: One agent run per workspace at a time (M1b).
RUN_ALREADY_ACTIVE = "RUN_ALREADY_ACTIVE"
#: A run stopped at its per-run cost ceiling; finished proposals are kept (M1b).
COST_CEILING_REACHED = "COST_CEILING_REACHED"
#: No key for the provider in the OS keychain or the environment (M1b-2).
PROVIDER_KEY_MISSING = "PROVIDER_KEY_MISSING"
#: No agent run with that id in this workspace (M1b-2).
UNKNOWN_RUN = "UNKNOWN_RUN"

# --- console guards (INC-01, M0) ----------------------------------------------
HOST_REFUSED = "HOST_REFUSED"
TOKEN_REQUIRED = "TOKEN_REQUIRED"
ACTION_ORIGIN_REFUSED = "ACTION_ORIGIN_REFUSED"

#: Codes the contract added in §7 "Proposed here" (``ENGINE_UNREACHABLE`` is
#: client-side only and never sent by the engine, so it is not here).
CONTRACT_ADDED = frozenset(
    {
        PROPOSAL_HIDDEN,
        SNAPSHOT_NOT_ACCEPTED,
        UNKNOWN_STUDY,
        REASON_CODE_INVALID,
        TOKEN_SCOPE_REFUSED,
        CONSENT_REQUIRED,
        RUN_ALREADY_ACTIVE,
        COST_CEILING_REACHED,
        PROVIDER_KEY_MISSING,
        UNKNOWN_RUN,
        PROVENANCE_MISSING,
        PROJECTION_STALE,
    }
)

#: Every code the console API may return.
CONSOLE_REFUSALS = CONTRACT_ADDED | frozenset(
    {
        HOST_REFUSED,
        TOKEN_REQUIRED,
        ACTION_ORIGIN_REFUSED,
        PAIRING_CODE_INVALID,
        COVERAGE_INCOMPLETE,
        STALE_BINDING,
        UNRESOLVED_FINALIZE_REFUSED,
    }
)
