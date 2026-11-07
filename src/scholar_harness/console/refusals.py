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
from scholar_harness.screening.export import (
    EXPORT_FORMAT_INVALID,
    EXPORT_NOT_PUBLISHED,
    EXPORT_SOURCE_MISMATCH,
    METHODS_SOURCE_MISSING,
)
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
#: An EXCLUDE whose reason contradicts the same event's answer (M6-beta).
REASON_CODE_INCONSISTENT = "REASON_CODE_INCONSISTENT"
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
#: The provider's driver cannot be built: its SDK is not installed, or a base URL is missing (M1b-2).
DRIVER_UNAVAILABLE = "DRIVER_UNAVAILABLE"
#: A cost ceiling on a provider/model the price table does not price, so its cost cannot be measured (M1b-2).
CEILING_NOT_PRICED = "CEILING_NOT_PRICED"
#: The workspaces routes (M5-slim, `docs/architecture/workspaces-api.md` §5).
WORKSPACE_TITLE_INVALID = "WORKSPACE_TITLE_INVALID"
WORKSPACE_EXISTS = "WORKSPACE_EXISTS"
WORKSPACE_PATH_REFUSED = "WORKSPACE_PATH_REFUSED"
WORKSPACE_ROOT_UNAVAILABLE = "WORKSPACE_ROOT_UNAVAILABLE"
WORKSPACE_NOT_VALID = "WORKSPACE_NOT_VALID"
WORKSPACE_BUSY = "WORKSPACE_BUSY"
RESTART_UNSUPPORTED = "RESTART_UNSUPPORTED"
#: The export and methods routes (M5-slim, spec 10) are re-exported from
#: ``screening/export.py`` above.

# --- the corpus import (M5b, spec 11) and Prepare (M6-beta) --------------------
#: Raised as ``AcceptCorpusRefused.code`` in ``corpus_accept.py``.
SOURCE_LABEL_INVALID = "SOURCE_LABEL_INVALID"
SOURCE_DATE_INVALID = "SOURCE_DATE_INVALID"
SOURCE_NOT_RIS = "SOURCE_NOT_RIS"
SOURCE_TOO_LARGE = "SOURCE_TOO_LARGE"
SOURCE_DUPLICATE_FILE = "SOURCE_DUPLICATE_FILE"
SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
VERIFIED_EXISTS = "VERIFIED_EXISTS"
CORPUS_ALREADY_ACCEPTED = "CORPUS_ALREADY_ACCEPTED"
NOTHING_STAGED = "NOTHING_STAGED"
PROTOCOL_INVALID = "PROTOCOL_INVALID"
ACCEPT_CORPUS_REFUSED = "ACCEPT_CORPUS_REFUSED"
#: Prepare's batch size outside the bounds the screen offers.
BATCH_SIZE_INVALID = "BATCH_SIZE_INVALID"

# --- console guards (INC-01, M0) ----------------------------------------------
HOST_REFUSED = "HOST_REFUSED"
TOKEN_REQUIRED = "TOKEN_REQUIRED"
ACTION_ORIGIN_REFUSED = "ACTION_ORIGIN_REFUSED"
#: The packaged UI's browser surface (M5-slim, `console/browser.py`): the same
#: codes the development proxy returns, plus a used or expired launch link.
CONSOLE_PATH_REFUSED = "CONSOLE_PATH_REFUSED"
CONSOLE_ORIGIN_REFUSED = "CONSOLE_ORIGIN_REFUSED"
CONSOLE_METHOD_REFUSED = "CONSOLE_METHOD_REFUSED"
LAUNCH_CODE_INVALID = "LAUNCH_CODE_INVALID"

#: Codes the contract added in §7 "Proposed here" (``ENGINE_UNREACHABLE`` is
#: client-side only and never sent by the engine, so it is not here).
CONTRACT_ADDED = frozenset(
    {
        PROPOSAL_HIDDEN,
        SNAPSHOT_NOT_ACCEPTED,
        UNKNOWN_STUDY,
        REASON_CODE_INVALID,
        REASON_CODE_INCONSISTENT,
        TOKEN_SCOPE_REFUSED,
        CONSENT_REQUIRED,
        RUN_ALREADY_ACTIVE,
        COST_CEILING_REACHED,
        PROVIDER_KEY_MISSING,
        UNKNOWN_RUN,
        DRIVER_UNAVAILABLE,
        CEILING_NOT_PRICED,
        WORKSPACE_TITLE_INVALID,
        WORKSPACE_EXISTS,
        WORKSPACE_PATH_REFUSED,
        WORKSPACE_ROOT_UNAVAILABLE,
        WORKSPACE_NOT_VALID,
        WORKSPACE_BUSY,
        RESTART_UNSUPPORTED,
        PROVENANCE_MISSING,
        PROJECTION_STALE,
        EXPORT_NOT_PUBLISHED,
        EXPORT_FORMAT_INVALID,
        EXPORT_SOURCE_MISMATCH,
        METHODS_SOURCE_MISSING,
        SOURCE_LABEL_INVALID,
        SOURCE_DATE_INVALID,
        SOURCE_NOT_RIS,
        SOURCE_TOO_LARGE,
        SOURCE_DUPLICATE_FILE,
        SOURCE_NOT_FOUND,
        VERIFIED_EXISTS,
        CORPUS_ALREADY_ACCEPTED,
        NOTHING_STAGED,
        PROTOCOL_INVALID,
        ACCEPT_CORPUS_REFUSED,
        BATCH_SIZE_INVALID,
    }
)

#: Every code the console API may return.
CONSOLE_REFUSALS = CONTRACT_ADDED | frozenset(
    {
        HOST_REFUSED,
        TOKEN_REQUIRED,
        ACTION_ORIGIN_REFUSED,
        CONSOLE_PATH_REFUSED,
        CONSOLE_ORIGIN_REFUSED,
        CONSOLE_METHOD_REFUSED,
        LAUNCH_CODE_INVALID,
        PAIRING_CODE_INVALID,
        COVERAGE_INCOMPLETE,
        STALE_BINDING,
        UNRESOLVED_FINALIZE_REFUSED,
    }
)
