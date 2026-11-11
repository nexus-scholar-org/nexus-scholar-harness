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

# --- the protocol's method block (M7-method, decision 2026-11-08) ------------
#: The protocol's ``method`` block is outside the checked limits.
PROTOCOL_METHOD_INVALID = "PROTOCOL_METHOD_INVALID"
#: Blinding is set by the protocol; the settings cannot change it.
BLINDING_SET_BY_PROTOCOL = "BLINDING_SET_BY_PROTOCOL"

# --- the inception routes (M4a, `docs/architecture/inception-api.md`) ---------
#: Raised as ``DraftRefused`` (``inception/drafts.py``), ``StepRefused``
#: (``inception/steps.py``) and ``GenesisRefused`` (``inception/emit.py``).
DRAFT_ID_INVALID = "DRAFT_ID_INVALID"
DRAFT_NOT_FOUND = "DRAFT_NOT_FOUND"
DRAFT_UNREADABLE = "DRAFT_UNREADABLE"
DRAFT_EXISTS = "DRAFT_EXISTS"
DRAFT_CONFLICT = "DRAFT_CONFLICT"
DRAFT_EMITTED = "DRAFT_EMITTED"
DRAFT_INVALID = "DRAFT_INVALID"
DRAFT_INCOMPLETE = "DRAFT_INCOMPLETE"
STEP_UNKNOWN = "STEP_UNKNOWN"
CRITERIA_UNDECIDED = "CRITERIA_UNDECIDED"
CRITERIA_MISSING = "CRITERIA_MISSING"
INTENT_INVALID = "INTENT_INVALID"
SCREENING_BOUND = "SCREENING_BOUND"
CONFIRMATION_MISMATCH = "CONFIRMATION_MISMATCH"

# --- recon over HTTP (M4c, `console/api/recon.py`) ----------------------------
#: Raised as ``ReconRefused`` (``recon/session.py``, ``inception/grounding.py``).
#: ``STALE_BINDING`` (above) also answers preview and genesis of a draft whose
#: bound pool no longer matches its recon session.
MAILTO_NOT_SET = "MAILTO_NOT_SET"
RECON_SESSION_INVALID = "RECON_SESSION_INVALID"
RECON_SESSION_NOT_FOUND = "RECON_SESSION_NOT_FOUND"
RECON_NO_POOL = "RECON_NO_POOL"
POOL_EMPTY = "POOL_EMPTY"
PROVIDERS_FAILED = "PROVIDERS_FAILED"
POOL_TOO_SMALL = "POOL_TOO_SMALL"
NARROW_BUDGET_SPENT = "NARROW_BUDGET_SPENT"
DIRECTION_UNKNOWN = "DIRECTION_UNKNOWN"
NO_DIRECTION = "NO_DIRECTION"
RECON_JOB_ACTIVE = "RECON_JOB_ACTIVE"
RECON_JOB_NOT_FOUND = "RECON_JOB_NOT_FOUND"
RECON_FAILED = "RECON_FAILED"
#: M4d: the read-only phrase check was sent no phrase.
TERM_EMPTY = "TERM_EMPTY"

# --- discovery over HTTP (M3b-api, `console/api/discovery.py`) ----------------
#: `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.7. ``MAILTO_NOT_SET``,
#: ``PROTOCOL_INVALID``, ``CORPUS_ALREADY_ACCEPTED`` and ``PROVIDERS_FAILED``
#: (above) answer the discovery routes too.
PROTOCOL_MISSING = "PROTOCOL_MISSING"
DISCOVERY_JOB_ACTIVE = "DISCOVERY_JOB_ACTIVE"
DISCOVERY_JOB_NOT_FOUND = "DISCOVERY_JOB_NOT_FOUND"
RUN_NOT_FOUND = "RUN_NOT_FOUND"
RECALL_NOT_RUN = "RECALL_NOT_RUN"
#: M3h-providers (F12): a run that selects OpenAlex while the console has no
#: ``SCHOLAR_OPENALEX_KEY``; OpenAlex requires a key since 2026-02-13.
OPENALEX_KEY_NOT_SET = "OPENALEX_KEY_NOT_SET"
SEEDS_INVALID = "SEEDS_INVALID"
CAP_INVALID = "CAP_INVALID"
#: A database name the engine does not know, in a run's or a check's ``providers``.
PROVIDER_UNKNOWN = "PROVIDER_UNKNOWN"
#: A discovery job stopped on an unexpected error; ``message`` names it.
DISCOVERY_FAILED = "DISCOVERY_FAILED"
#: E5: typed codes on a run job's ``error`` (the coordinator's resume refusals
#: and its snapshot refusal), formerly only reason-string prefixes.
PROTOCOL_CHANGED_SINCE_SNAPSHOT = "PROTOCOL_CHANGED_SINCE_SNAPSHOT"
BATCHES_INCOMPLETE = "BATCHES_INCOMPLETE"
STAGED_IMPORT_PENDING = "STAGED_IMPORT_PENDING"
#: E5: a failed search leg's ``error_code``: a leg field, never an HTTP status
#: (a failed leg makes a PARTIAL run).
PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"
PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
PROVIDER_REFUSED = "PROVIDER_REFUSED"
LEG_ERROR_CODES = frozenset({PROVIDER_RATE_LIMITED, PROVIDER_TIMEOUT, PROVIDER_UNAVAILABLE, PROVIDER_REFUSED})
#: E3 (M3d-engine): a staged export's ``rejected[].code``: a row field, never an
#: HTTP status (the importer's own constants, ``scholar_search.importers``).
IMPORT_NO_TITLE = "IMPORT_NO_TITLE"
IMPORT_BAD_TAG = "IMPORT_BAD_TAG"
IMPORT_BAD_YEAR = "IMPORT_BAD_YEAR"
IMPORT_REJECTION_CODES = frozenset({IMPORT_NO_TITLE, IMPORT_BAD_TAG, IMPORT_BAD_YEAR})
#: E4a (M3d-engine): ``GET /discovery/dedup`` before any deduplication.
DEDUP_NOT_RUN = "DEDUP_NOT_RUN"
#: Review F3 (M3d-engine): the hand-off accept of a run whose query or years the protocol no longer has.
PROTOCOL_CHANGED_SINCE_RUN = "PROTOCOL_CHANGED_SINCE_RUN"

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
        PROTOCOL_METHOD_INVALID,
        BLINDING_SET_BY_PROTOCOL,
        DRAFT_ID_INVALID,
        DRAFT_NOT_FOUND,
        DRAFT_UNREADABLE,
        DRAFT_EXISTS,
        DRAFT_CONFLICT,
        DRAFT_EMITTED,
        DRAFT_INVALID,
        DRAFT_INCOMPLETE,
        STEP_UNKNOWN,
        CRITERIA_UNDECIDED,
        CRITERIA_MISSING,
        INTENT_INVALID,
        SCREENING_BOUND,
        CONFIRMATION_MISMATCH,
        MAILTO_NOT_SET,
        RECON_SESSION_INVALID,
        RECON_SESSION_NOT_FOUND,
        RECON_NO_POOL,
        POOL_EMPTY,
        PROVIDERS_FAILED,
        POOL_TOO_SMALL,
        NARROW_BUDGET_SPENT,
        DIRECTION_UNKNOWN,
        NO_DIRECTION,
        RECON_JOB_ACTIVE,
        RECON_JOB_NOT_FOUND,
        RECON_FAILED,
        TERM_EMPTY,
        PROTOCOL_MISSING,
        DISCOVERY_JOB_ACTIVE,
        DISCOVERY_JOB_NOT_FOUND,
        RUN_NOT_FOUND,
        RECALL_NOT_RUN,
        OPENALEX_KEY_NOT_SET,
        SEEDS_INVALID,
        CAP_INVALID,
        PROVIDER_UNKNOWN,
        DISCOVERY_FAILED,
        PROTOCOL_CHANGED_SINCE_SNAPSHOT,
        BATCHES_INCOMPLETE,
        STAGED_IMPORT_PENDING,
        DEDUP_NOT_RUN,
        PROTOCOL_CHANGED_SINCE_RUN,
    }
    | LEG_ERROR_CODES
    | IMPORT_REJECTION_CODES
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
