"""Screening decision contract reader, tier classifier, and debt ledger.

Reads *agent screening-lane* decision files -- the JSON documents a screening
agent writes for one batch -- and reports exactly what they contain.  It
answers three questions and nothing else:

1. which canonical fields does each row carry (verbatim, or ``None``);
2. is the file ``VALID``, ``DEBT``, or ``BAD``;
3. which debt, advisory, and structural findings were recorded.

The reader is **read-only**.  It never rewrites, repairs, renames, or deletes
a producer file, and the only writer in this module is :func:`cmd_validate`,
which creates exactly one new report sidecar.

**This module is NOT a Contract v1 publication surface.**  It never accepts or
publishes a Contract v1 artifact, never writes ``included.json`` /
``excluded.json`` / ``prisma_screening_report.md``, never touches the artifact
registry, and it does **not** replace the Contract v1 collector's provenance
gates.  The agent-lane schema read here (``screening_id`` / ``decision`` /
``reason_code`` / ``confidence`` / ``one_line_support``) is a *different*
schema from the one the collector consumes (``decision_id`` / ``screener_id`` /
``method`` / ``decided_at`` / ``reason`` / ``parent_decision_ids``); the two
must never be conflated, and nothing here is wired into the collector.

**Name disambiguation.**  The ``DecisionContract`` **type** exported here is a
harness screening-lane configuration object.  It is not the Contract v1
``scholar_harness.contracts`` package, not a Contract v1 artifact, and not a
Contract v1 model.  The two namespaces never mix: this module imports nothing
from ``scholar_harness.contracts``.

Public names
------------

``DecisionContract``
    Frozen, typed contract configuration: canonical fields, allowed extras,
    alias map, decision vocabulary, expected instrument SHA prefixes, embedded
    reason-code pattern, and file-name patterns.  Defaults are domain-free.
    (Type only -- see the disambiguation note above.)
``DecisionContractRefused``
    Typed refusal with a stable ``code``, a human ``message``, and
    machine-readable ``details``.
``FileClassification``
    The result of classifying one decision file: ``tier``, ``structural``,
    ``debt``, ``advisory``, ``header``, ``rows``.
``default_contract`` / ``load_contract`` / ``DecisionContract.from_dict``
    Build the domain-free default, or read a contract configuration from JSON.
``normalize_row``
    Return ``(canonical_row, tags)`` for one row.
``classify_decision_file``
    Classify one decision file against its parent batch manifest and parent
    view.  The parent artifacts are the count and id-order authority.
``discover_decision_files``
    Broad inventory of the decision-file candidates in one directory.
``resolve_parent_artifacts``
    Locate and read the parent batch manifest and the parent view.
``build_debt_ledger``
    Per-file, per-tag debt ledger over a set of classifications.
``build_report`` / ``cmd_validate``
    The report payload and the ``agent_screen.py validate`` command.
``tag_prefix``
    Return the code part of a finding tag (``CODE`` of ``CODE:detail``).
``TIERS``
    The three reader-local tier names, in reporting order.
``DEBT_PREFIXES`` / ``ADVISORY_PREFIXES`` / ``STRUCTURAL_CODES``
    The tag vocabulary: the debt tag prefixes, the advisory tag prefixes, and
    the structural codes, declared once in the vocabulary block below.
``is_debt_tag`` / ``is_advisory_tag``
    Classify a tag by its prefix.

Vocabulary
----------

Every finding code is declared once, in the "tag vocabulary" block below.
Debt tags are ``PREFIX`` or ``PREFIX:detail``; advisory tags likewise;
structural codes likewise.  ``is_debt_tag`` / ``is_advisory_tag`` classify a
tag by its prefix.

Tiers
-----

The rollup rule (:data:`TIER_RULE`, also emitted in the report):

* ``BAD`` -- the file carries at least one **structural** finding.
* ``DEBT`` -- the file carries at least one **debt or advisory** finding.
* ``VALID`` -- the file carries no finding at all.

An advisory-only file (for example unknown keys, or an over-length
``one_line_support``) is therefore ``DEBT``, not ``VALID``: both are deviations
from the frozen instrument's field list and deserve triage rather than a clean
bill.  Only structural findings make a file ``BAD``.

``BAD``
    Structurally unusable: unparseable, BOM, unattested header, missing
    parent, wrong row count, id/order mismatch against the parent view,
    missing id, decision outside the configured vocabulary, non-canonical file
    name, unsupported contract schema major version.
``DEBT``
    Usable, but a canonical field is absent, alias-named, non-numeric, out of
    range, the rationale sits only under the fallback rationale key, or the
    file carries an advisory finding (unknown key, over-length support).
``VALID``
    Every canonical field present and well-formed, with no debt and no
    advisory findings.

Never fabricate
---------------

An absent canonical field becomes ``None`` plus an explicit debt tag; no
default, guess, or synthesized value is ever substituted.  A non-numeric
confidence yields ``None`` and ``CONFIDENCE_NON_NUMERIC`` -- no numeric value
is invented.  An alias key is honored only when it appears in the configured
alias map, and its use is always tagged.  Unknown keys are surfaced as an
advisory and are never dropped from the producer file.

The parent artifacts are the authority
--------------------------------------

The parent batch manifest is the record-count authority; the **ordered id
list** comes from the view when one is configured *and* resolved, and
otherwise from the parent batch's own ordered record list (``records[]`` /
``papers[]``).  The view is an optional redaction overlay, not the primary
parent, so a lane without a view still has an id-order authority.

The two sides carry their ids under **different keys** -- a harness batch
lists its papers under ``workspace_id``, a pilot batch and a decision row use
``screening_id`` -- so each side is resolved explicitly: the decision row
under the contract's ``canonical_id_field`` (default ``screening_id``), the
parent record under the first key present among ``screening_id`` /
``workspace_id`` / ``study_id``.  If an id cannot be extracted on either
side, the order is reported as ``ID_ORDER_NOT_VERIFIABLE`` -- never as
"checked and in order".  A mismatch against the view carries
``ID_ORDER_MISMATCH_VS_VIEW``; a mismatch against the batch carries the
distinct ``ID_ORDER_MISMATCH_VS_BATCH``.

A dispatch prompt and a producer self-report are never authorities: a
decision file that copies its own record count into a ``n_records`` header is
compared against the manifest, and a disagreement is reported as
``SELF_REPORT_COUNT_MISMATCH`` (the manifest still wins).

Scan status
-----------

A scan that verified nothing is a **failure**, not an empty success:

* ``NO_DECISION_FILES`` -- the scanned directory holds no decision file; an
  empty directory cannot be told apart from a mis-pointed ``--decisions-dir``.
* ``NO_PARENTS_RESOLVED`` -- files were found but not one parent artifact
  resolved for any of them.

Either finding makes the command exit non-zero and record the journal event
with status ``FAILED`` and the reason code in its metrics and description.
A normal scan -- including one that finds ``DEBT`` or ``BAD`` files -- exits
zero with status ``SUCCESS``.
"""

from __future__ import annotations

import codecs
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any

from scholar_harness.workspace.audit import log_event

# ---------------------------------------------------------------------------
# Tag vocabulary -- the single source of truth for every finding code.
# ---------------------------------------------------------------------------

#: Debt: the file is usable, but a canonical field is absent, alias-named,
#: non-numeric, out of range, or the rationale lives under the fallback key.
DEBT_CONFIDENCE_ABSENT = "CONFIDENCE_ABSENT"
DEBT_CONFIDENCE_NON_NUMERIC = "CONFIDENCE_NON_NUMERIC"
DEBT_CONFIDENCE_OUT_OF_RANGE = "CONFIDENCE_OUT_OF_RANGE"
DEBT_RATIONALE_ABSENT = "RATIONALE_ABSENT"
DEBT_RATIONALE_IN_REASON_ONLY = "RATIONALE_IN_REASON_ONLY"
DEBT_REASON_CODE_ABSENT = "REASON_CODE_ABSENT"
DEBT_REASON_CODE_EMBEDDED_IN_TEXT = "REASON_CODE_EMBEDDED_IN_TEXT"
DEBT_ALIAS_REASON_CODE = "ALIAS_REASON_CODE"

#: Advisory: reported, never a structural defect; advisory findings mark the file
#: ``DEBT``, never ``BAD``.
ADVISORY_SUPPORT_OVER_MAX_WORDS = "SUPPORT_OVER_25_WORDS"
ADVISORY_UNKNOWN_KEYS = "UNKNOWN_KEYS"

#: Debt tag prefixes.
DEBT_PREFIXES: tuple[str, ...] = (
    DEBT_CONFIDENCE_ABSENT,
    DEBT_CONFIDENCE_NON_NUMERIC,
    DEBT_CONFIDENCE_OUT_OF_RANGE,
    DEBT_RATIONALE_ABSENT,
    DEBT_RATIONALE_IN_REASON_ONLY,
    DEBT_REASON_CODE_ABSENT,
    DEBT_REASON_CODE_EMBEDDED_IN_TEXT,
    DEBT_ALIAS_REASON_CODE,
)

#: Advisory tag prefixes.
ADVISORY_PREFIXES: tuple[str, ...] = (
    ADVISORY_SUPPORT_OVER_MAX_WORDS,
    ADVISORY_UNKNOWN_KEYS,
)

#: Structural codes: the file is unusable as evidence.
STRUCT_FILE_MISSING = "FILE_MISSING"
STRUCT_FILE_UNREADABLE = "FILE_UNREADABLE"
STRUCT_BOM_DETECTED = "BOM_DETECTED"
STRUCT_UTF8_DECODE_ERROR = "UTF8_DECODE_ERROR"
STRUCT_JSON_PARSE = "JSON_PARSE"
STRUCT_NOT_A_JSON_OBJECT = "NOT_A_JSON_OBJECT"
STRUCT_NO_ROWS_KEY = "NO_ROWS_KEY"
STRUCT_FILENAME_NOT_CANONICAL = "FILENAME_NOT_CANONICAL"
STRUCT_SCHEMA_VERSION_UNSUPPORTED = "SCHEMA_VERSION_UNSUPPORTED"
STRUCT_PARENT_MISSING = "PARENT_MISSING"
STRUCT_PARENT_BATCH_MISSING = "PARENT_BATCH_MISSING"
STRUCT_PARENT_VIEW_MISSING = "PARENT_VIEW_MISSING"
STRUCT_PARENT_BATCH_UNREADABLE = "PARENT_BATCH_UNREADABLE"
STRUCT_PARENT_VIEW_UNREADABLE = "PARENT_VIEW_UNREADABLE"
STRUCT_PARENT_ROW_COUNT_UNAVAILABLE = "PARENT_ROW_COUNT_UNAVAILABLE"
STRUCT_SELF_REPORT_COUNT_MISMATCH = "SELF_REPORT_COUNT_MISMATCH"
STRUCT_ID_ORDER_NOT_VERIFIABLE = "ID_ORDER_NOT_VERIFIABLE"
STRUCT_ID_ORDER_MISMATCH_VS_VIEW = "ID_ORDER_MISMATCH_VS_VIEW"
STRUCT_ID_ORDER_MISMATCH_VS_BATCH = "ID_ORDER_MISMATCH_VS_BATCH"
STRUCT_HEADER_UNATTESTED = "HEADER_UNATTESTED"
STRUCT_CRITERIA_SHA_MISSING = "CRITERIA_SHA_MISSING"
STRUCT_CRITERIA_SHA_MISMATCH = "CRITERIA_SHA_MISMATCH"
STRUCT_PROMPT_SHA_MISSING = "PROMPT_SHA_MISSING"
STRUCT_PROMPT_SHA_MISMATCH = "PROMPT_SHA_MISMATCH"
STRUCT_ROW_COUNT = "ROW_COUNT"

#: Scan-level finding: not one parent artifact resolved for any scanned
#: file.  It makes "the parents are not where the contract says" loud, so it
#: can never be mistaken for a corpus in which every file is genuinely bad.
SCAN_NO_PARENTS_RESOLVED = "NO_PARENTS_RESOLVED"

#: Scan-level finding: the scanned directory holds no decision file at all.
#: An empty directory cannot be told apart from a mis-pointed decisions
#: directory, so the scan is a failure, not an empty success.
SCAN_NO_DECISION_FILES = "NO_DECISION_FILES"

#: Structural codes.
STRUCTURAL_CODES: tuple[str, ...] = (
    STRUCT_FILE_MISSING,
    STRUCT_FILE_UNREADABLE,
    STRUCT_BOM_DETECTED,
    STRUCT_UTF8_DECODE_ERROR,
    STRUCT_JSON_PARSE,
    STRUCT_NOT_A_JSON_OBJECT,
    STRUCT_NO_ROWS_KEY,
    STRUCT_FILENAME_NOT_CANONICAL,
    STRUCT_SCHEMA_VERSION_UNSUPPORTED,
    STRUCT_PARENT_MISSING,
    STRUCT_PARENT_BATCH_MISSING,
    STRUCT_PARENT_VIEW_MISSING,
    STRUCT_PARENT_BATCH_UNREADABLE,
    STRUCT_PARENT_VIEW_UNREADABLE,
    STRUCT_PARENT_ROW_COUNT_UNAVAILABLE,
    STRUCT_SELF_REPORT_COUNT_MISMATCH,
    STRUCT_ID_ORDER_NOT_VERIFIABLE,
    STRUCT_ID_ORDER_MISMATCH_VS_VIEW,
    STRUCT_ID_ORDER_MISMATCH_VS_BATCH,
    STRUCT_HEADER_UNATTESTED,
    STRUCT_CRITERIA_SHA_MISSING,
    STRUCT_CRITERIA_SHA_MISMATCH,
    STRUCT_PROMPT_SHA_MISSING,
    STRUCT_PROMPT_SHA_MISMATCH,
    STRUCT_ROW_COUNT,
)

# ---------------------------------------------------------------------------
# Tiers, field names, and contract defaults
# ---------------------------------------------------------------------------

TIER_VALID = "VALID"
TIER_DEBT = "DEBT"
TIER_BAD = "BAD"

#: The three reader-local tiers, in reporting order.
TIERS: tuple[str, ...] = (TIER_VALID, TIER_DEBT, TIER_BAD)

#: The tier rollup rule, stated once and emitted in every report.
TIER_RULE = (
    "A file is BAD when it carries any structural finding; DEBT when it "
    "carries any debt or advisory finding; VALID when it carries no finding."
)

#: Canonical field the alias map and the embedded-code extraction target.
REASON_CODE_FIELD = "reason_code"
#: Canonical field carrying the numeric confidence.
CONFIDENCE_FIELD = "confidence"
#: Canonical field carrying the one-line rationale.
SUPPORT_FIELD = "one_line_support"
#: Canonical field carrying the record id a decision row is keyed by.  The
#: parent artifacts may use a different spelling; see
#: :data:`PARENT_ID_KEYS`.
DEFAULT_CANONICAL_ID_FIELD = "screening_id"
#: Allowed-extra key that may carry the rationale when the canonical one is
#: absent.  Its presence is reported, never silently copied.
RATIONALE_FALLBACK_FIELD = "reason"
#: Maximum word count of the one-line rationale before an advisory is raised.
SUPPORT_MAX_WORDS = 25

#: Contract schema major version this reader understands.
SUPPORTED_SCHEMA_MAJOR = 1

#: Domain-free defaults: the screening-lane field vocabulary only.
DEFAULT_CANONICAL_FIELDS: tuple[str, ...] = (
    "screening_id",
    "decision",
    "reason_code",
    "confidence",
    "one_line_support",
)
DEFAULT_ALLOWED_EXTRAS: tuple[str, ...] = (
    "reason",
    "criterion_refs",
    "moderation_status",
    "moderation_redacted",
)
DEFAULT_DECISION_VOCABULARY: tuple[str, ...] = ("INCLUDE", "EXCLUDE", "PENDING")
#: The default file-name patterns follow the lane the harness itself produces
#: (``batcher.py``): ``batch_001.json`` / ``batch_001_decisions.json``.  Any
#: other layout is expressed by a contract config, never by changing these.
DEFAULT_DECISION_FILE_PATTERN = "batch_{n:03d}_decisions.json"
DEFAULT_BATCH_FILE_PATTERN = "batch_{n:03d}.json"
#: The harness lane publishes no view artifact, so no view authority is
#: configured by default; the id-order check is then recorded as not
#: applicable rather than failed.
DEFAULT_VIEW_FILE_PATTERN = ""

#: The reader's own artifact file names.  They are excluded from every scan
#: **by name**, so the reader can never re-ingest its own output.
CONTRACT_CONFIG_FILE_NAME = "decision_contract.json"
REPORT_FILE_NAME = "decision_contract_report.json"
#: Artifact names that are never treated as decision files.
READER_ARTIFACT_FILE_NAMES: tuple[str, ...] = (
    CONTRACT_CONFIG_FILE_NAME,
    REPORT_FILE_NAME,
)

#: Workspace-relative locations used by the command surface.
CONTRACT_RELATIVE_PATH = Path("literature") / "screening" / CONTRACT_CONFIG_FILE_NAME
REPORT_RELATIVE_PATH = Path("literature") / "screening_reports" / REPORT_FILE_NAME
#: Default workspace-relative directory the reader scans.
DEFAULT_DECISIONS_DIR = Path("literature") / "screening"

#: Audit vocabulary for the command surface.
AUDIT_ACTION = "SCREENING_VALIDATION"
AUDIT_AGENT = "agent_screen.validate"

#: Refusal codes raised by the command surface.
REFUSAL_REPORT_EXISTS = "REPORT_EXISTS"
REFUSAL_CONTRACT_CONFIG_MISSING = "CONTRACT_CONFIG_MISSING"
REFUSAL_CONTRACT_CONFIG_UNUSABLE = "CONTRACT_CONFIG_UNUSABLE"
REFUSAL_DECISIONS_DIR_MISSING = "DECISIONS_DIR_MISSING"
REFUSAL_SCHEMA_VERSION_UNSUPPORTED = "SCHEMA_VERSION_UNSUPPORTED"
REFUSAL_WORKSPACE_MISSING = "WORKSPACE_MISSING"


class DecisionContractRefused(RuntimeError):
    """Typed refusal to run the decision contract reader.

    Mirrors the ``ScreeningIntegrityRefused`` shape (stable ``code``, human
    ``message``, machine-readable ``details``) so callers can branch on the
    failure instead of parsing text.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details)

    def as_dict(self) -> dict[str, Any]:
        """Return the refusal as a JSON-serializable mapping."""
        return {"code": self.code, "message": self.message, "details": self.details}


def is_debt_tag(tag: str) -> bool:
    """Return whether ``tag`` is a debt tag (prefix before the first colon)."""
    return tag.split(":", 1)[0] in DEBT_PREFIXES


def is_advisory_tag(tag: str) -> bool:
    """Return whether ``tag`` is an advisory tag (prefix before the colon)."""
    return tag.split(":", 1)[0] in ADVISORY_PREFIXES


def tag_prefix(tag: str) -> str:
    """Return the code part of a finding tag (``CODE`` of ``CODE:detail``)."""
    return tag.split(":", 1)[0]


@dataclass(frozen=True)
class DecisionContract:
    """Domain-parameterized screening decision contract.

    Every field is domain-free by default: no expected instrument SHA
    prefixes, no embedded reason-code pattern, and no aliases.  A workspace
    supplies its own values through ``decision_contract.json``.
    """

    schema_version: str = "1"
    canonical_fields: tuple[str, ...] = DEFAULT_CANONICAL_FIELDS
    allowed_extras: tuple[str, ...] = DEFAULT_ALLOWED_EXTRAS
    reason_code_aliases: Mapping[str, str] = field(default_factory=dict)
    decision_vocabulary: tuple[str, ...] = DEFAULT_DECISION_VOCABULARY
    canonical_id_field: str = DEFAULT_CANONICAL_ID_FIELD
    expected_criteria_sha256_prefix: str = ""
    expected_prompt_sha256_prefix: str = ""
    embedded_reason_code_pattern: str = ""
    decision_file_pattern: str = DEFAULT_DECISION_FILE_PATTERN
    batch_file_pattern: str = DEFAULT_BATCH_FILE_PATTERN
    view_file_pattern: str = DEFAULT_VIEW_FILE_PATTERN

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code_aliases",
            MappingProxyType(dict(self.reason_code_aliases)),
        )

    @property
    def schema_major(self) -> int:
        """Return the major component of the contract schema version."""
        head = self.schema_version.split(".", 1)[0].strip()
        try:
            return int(head)
        except ValueError:
            return -1

    @property
    def schema_version_supported(self) -> bool:
        """Return whether this reader understands the contract schema major."""
        return self.schema_major == SUPPORTED_SCHEMA_MAJOR

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DecisionContract:
        """Build a contract from a configuration mapping.

        Unknown keys are ignored; every documented key is optional and a
        missing key falls back to the domain-free default.  A malformed value
        raises :class:`DecisionContractRefused` rather than being coerced.
        """
        if not isinstance(data, Mapping):
            raise DecisionContractRefused(
                REFUSAL_CONTRACT_CONFIG_UNUSABLE,
                "decision contract configuration must be a JSON object",
            )

        def _string_tuple(key: str, default: tuple[str, ...]) -> tuple[str, ...]:
            value = data.get(key)
            if value is None:
                return tuple(default)
            if isinstance(value, str):
                return (value,)
            if isinstance(value, (list, tuple)):
                return tuple(str(item) for item in value)
            raise DecisionContractRefused(
                REFUSAL_CONTRACT_CONFIG_UNUSABLE,
                f"decision contract key {key!r} must be a list of strings",
            )

        aliases = data.get("reason_code_aliases")
        if aliases is None:
            alias_map: dict[str, str] = {}
        elif isinstance(aliases, Mapping):
            alias_map = {str(key): str(value) for key, value in aliases.items()}
        else:
            raise DecisionContractRefused(
                REFUSAL_CONTRACT_CONFIG_UNUSABLE,
                "decision contract key 'reason_code_aliases' must be an object",
            )

        embedded = data.get("embedded_reason_code_pattern") or ""
        if not isinstance(embedded, str):
            raise DecisionContractRefused(
                REFUSAL_CONTRACT_CONFIG_UNUSABLE,
                "decision contract key 'embedded_reason_code_pattern' must be a string",
            )
        if embedded:
            try:
                re.compile(embedded)
            except re.error as exc:
                raise DecisionContractRefused(
                    REFUSAL_CONTRACT_CONFIG_UNUSABLE,
                    f"embedded reason-code pattern is not a valid regex: {exc}",
                ) from exc

        contract = cls(
            schema_version=str(data.get("schema_version") or "1"),
            canonical_fields=_string_tuple(
                "canonical_fields", DEFAULT_CANONICAL_FIELDS
            ),
            allowed_extras=_string_tuple("allowed_extras", DEFAULT_ALLOWED_EXTRAS),
            reason_code_aliases=alias_map,
            decision_vocabulary=_string_tuple(
                "decision_vocabulary", DEFAULT_DECISION_VOCABULARY
            ),
            canonical_id_field=str(
                data.get("canonical_id_field") or DEFAULT_CANONICAL_ID_FIELD
            ),
            expected_criteria_sha256_prefix=str(
                data.get("expected_criteria_sha256_prefix") or ""
            ),
            expected_prompt_sha256_prefix=str(
                data.get("expected_prompt_sha256_prefix") or ""
            ),
            embedded_reason_code_pattern=embedded,
            decision_file_pattern=str(
                data.get("decision_file_pattern") or DEFAULT_DECISION_FILE_PATTERN
            ),
            batch_file_pattern=str(
                data.get("batch_file_pattern") or DEFAULT_BATCH_FILE_PATTERN
            ),
            view_file_pattern=str(
                data.get("view_file_pattern") or DEFAULT_VIEW_FILE_PATTERN
            ),
        )
        return contract

    def as_dict(self) -> dict[str, Any]:
        """Return the contract as a JSON-serializable mapping."""
        return {
            "schema_version": self.schema_version,
            "canonical_fields": list(self.canonical_fields),
            "allowed_extras": list(self.allowed_extras),
            "reason_code_aliases": dict(sorted(self.reason_code_aliases.items())),
            "decision_vocabulary": list(self.decision_vocabulary),
            "canonical_id_field": self.canonical_id_field,
            "expected_criteria_sha256_prefix": self.expected_criteria_sha256_prefix,
            "expected_prompt_sha256_prefix": self.expected_prompt_sha256_prefix,
            "embedded_reason_code_pattern": self.embedded_reason_code_pattern,
            "decision_file_pattern": self.decision_file_pattern,
            "batch_file_pattern": self.batch_file_pattern,
            "view_file_pattern": self.view_file_pattern,
        }


def default_contract() -> DecisionContract:
    """Return the domain-free default contract."""
    return DecisionContract()


def load_contract(path: Path | str | None) -> DecisionContract:
    """Load a contract configuration from JSON.

    A missing file yields the domain-free default; an unreadable or malformed
    file raises :class:`DecisionContractRefused`.
    """
    if path is None:
        return default_contract()
    config_path = Path(path)
    if not config_path.is_file():
        return default_contract()
    try:
        raw = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DecisionContractRefused(
            REFUSAL_CONTRACT_CONFIG_UNUSABLE,
            f"decision contract configuration is unreadable: {exc}",
        ) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DecisionContractRefused(
            REFUSAL_CONTRACT_CONFIG_UNUSABLE,
            f"decision contract configuration is not valid JSON: {exc.msg}",
        ) from exc
    return DecisionContract.from_dict(data)


# ---------------------------------------------------------------------------
# Row normalization
# ---------------------------------------------------------------------------


@lru_cache(maxsize=32)
def _compiled_embedded(pattern: str) -> re.Pattern[str] | None:
    """Return the compiled embedded reason-code pattern (or ``None``)."""
    if not pattern:
        return None
    try:
        return re.compile(pattern)
    except re.error:  # pragma: no cover - validated at contract build time
        return None


def _extract_embedded_code(text: str, contract: DecisionContract) -> str | None:
    """Extract a reason code embedded in rationale text, or ``None``."""
    pattern = _compiled_embedded(contract.embedded_reason_code_pattern)
    if pattern is None or not text:
        return None
    match = pattern.search(text)
    if match is None:
        return None
    groups = pattern.groupindex or {}
    if "code" in groups:
        return match.group("code")
    if pattern.groups:
        return match.group(1)
    return match.group(0)


def _word_count(text: Any) -> int:
    """Return the number of whitespace-separated words in ``text``."""
    if not isinstance(text, str):
        return 0
    return len(re.findall(r"\S+", text))


def normalize_row(
    row: Mapping[str, Any], contract: DecisionContract
) -> tuple[dict[str, Any], list[str]]:
    """Return ``(canonical_row, tags)`` for one decision row.

    Canonical values are copied verbatim from the row, or ``None`` when the
    canonical key is absent.  An alias key is honored only when it appears in
    the configured alias map, and its use is always tagged.  Nothing is
    fabricated: an absent or unusable value stays ``None`` and is reported
    through a debt tag.

    ``tags`` carries debt and advisory findings only.  Structural findings
    (a missing id, a decision outside the vocabulary) are raised by
    :func:`classify_decision_file`, which owns the file tier.
    """
    if not isinstance(row, Mapping):
        return {}, [DEBT_RATIONALE_ABSENT]

    tags: list[str] = []
    canonical: dict[str, Any] = {
        field_name: row.get(field_name) for field_name in contract.canonical_fields
    }

    if REASON_CODE_FIELD in contract.canonical_fields:
        if canonical.get(REASON_CODE_FIELD) is None:
            for alias_key, canonical_field in contract.reason_code_aliases.items():
                if alias_key in row and row[alias_key] is not None:
                    canonical[canonical_field] = row[alias_key]
                    tags.append(f"{DEBT_ALIAS_REASON_CODE}:{alias_key}")
                    break
        if canonical.get(REASON_CODE_FIELD) is None:
            extracted = None
            for source in (RATIONALE_FALLBACK_FIELD, SUPPORT_FIELD):
                text = row.get(source)
                if not isinstance(text, str) or not text.strip():
                    continue
                extracted = _extract_embedded_code(text, contract)
                if extracted:
                    break
            if extracted:
                canonical[REASON_CODE_FIELD] = extracted
                tags.append(DEBT_REASON_CODE_EMBEDDED_IN_TEXT)
            else:
                tags.append(DEBT_REASON_CODE_ABSENT)

    if SUPPORT_FIELD in contract.canonical_fields:
        if canonical.get(SUPPORT_FIELD) is None:
            fallback = row.get(RATIONALE_FALLBACK_FIELD)
            if isinstance(fallback, str) and fallback.strip():
                tags.append(DEBT_RATIONALE_IN_REASON_ONLY)
            else:
                tags.append(DEBT_RATIONALE_ABSENT)
        else:
            words = _word_count(canonical.get(SUPPORT_FIELD))
            if words > SUPPORT_MAX_WORDS:
                tags.append(f"{ADVISORY_SUPPORT_OVER_MAX_WORDS}:{words}")

    if CONFIDENCE_FIELD in contract.canonical_fields:
        confidence = canonical.get(CONFIDENCE_FIELD)
        if confidence is None:
            tags.append(DEBT_CONFIDENCE_ABSENT)
        elif isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            tags.append(DEBT_CONFIDENCE_NON_NUMERIC)
            canonical[CONFIDENCE_FIELD] = None
        elif not 0.0 <= float(confidence) <= 1.0:
            tags.append(DEBT_CONFIDENCE_OUT_OF_RANGE)
            canonical[CONFIDENCE_FIELD] = None

    known = (
        set(contract.canonical_fields)
        | set(contract.allowed_extras)
        | set(contract.reason_code_aliases)
    )
    unknown = sorted(str(key) for key in row if key not in known)
    if unknown:
        tags.append(f"{ADVISORY_UNKNOWN_KEYS}:{','.join(unknown)}")

    return canonical, tags


# ---------------------------------------------------------------------------
# File-name patterns
# ---------------------------------------------------------------------------

_PATTERN_FIELD = re.compile(r"\{(n|family)(?::0(\d+)d)?\}")


@lru_cache(maxsize=64)
def _compile_file_pattern(pattern: str, strict: bool) -> re.Pattern[str] | None:
    """Compile a ``{n:04d}`` / ``{family}`` file pattern into a regex.

    ``strict`` pins the numeric width exactly as configured.  The relaxed form
    accepts any numeric width; it is used only to *diagnose* a near-canonical
    name and to locate a parent artifact, never to accept a name.
    """
    if not pattern:
        return None
    parts: list[str] = []
    position = 0
    for match in _PATTERN_FIELD.finditer(pattern):
        parts.append(re.escape(pattern[position : match.start()]))
        if match.group(1) == "n":
            width = match.group(2)
            if strict and width:
                parts.append(f"(?P<n>\\d{{{width}}})")
            else:
                parts.append("(?P<n>\\d+)")
        else:
            parts.append("(?P<family>.+?)")
        position = match.end()
    parts.append(re.escape(pattern[position:]))
    try:
        return re.compile("".join(parts))
    except re.error:  # pragma: no cover - pattern comes from configuration
        return None


def _render_file_pattern(pattern: str, index: int, family: str) -> str | None:
    """Render a file pattern with a batch index and family."""
    try:
        return pattern.format(n=index, family=family)
    except (KeyError, IndexError, ValueError):  # pragma: no cover
        return None


@dataclass(frozen=True)
class _NameMatch:
    """Outcome of matching one decision file name against the pattern."""

    canonical: bool
    index: int | None
    family: str | None
    expected_name: str | None


def _match_decision_name(name: str, contract: DecisionContract) -> _NameMatch:
    """Match a decision file name against the configured pattern.

    A pattern without a ``{family}`` placeholder (the harness lane's own
    layout) yields no family; the screener-id attestation is then recorded as
    not applicable instead of failed.
    """
    strict = _compile_file_pattern(contract.decision_file_pattern, strict=True)
    if strict is not None:
        match = strict.fullmatch(name)
        if match is not None:
            return _NameMatch(
                canonical=True,
                index=int(match.group("n")),
                family=match.groupdict().get("family"),
                expected_name=name,
            )
    relaxed = _compile_file_pattern(contract.decision_file_pattern, strict=False)
    if relaxed is not None:
        match = relaxed.fullmatch(name)
        if match is not None:
            index = int(match.group("n"))
            family = match.groupdict().get("family")
            return _NameMatch(
                canonical=False,
                index=index,
                family=family,
                expected_name=_render_file_pattern(
                    contract.decision_file_pattern, index, family or ""
                ),
            )
    return _NameMatch(canonical=False, index=None, family=None, expected_name=None)


# ---------------------------------------------------------------------------
# Parent artifacts (the count and id-order authority)
# ---------------------------------------------------------------------------


def _candidate_parent_dirs(directory: Path) -> list[Path]:
    """Return the directories searched for parent artifacts.

    The decisions directory itself, its parent, and any sibling directory
    whose name contains ``view`` (a view directory).
    """
    candidates = [directory]
    parent = directory.parent
    if parent != directory:
        candidates.append(parent)
        try:
            children = sorted(child for child in parent.iterdir() if child.is_dir())
        except OSError:  # pragma: no cover - unreadable parent
            children = []
        candidates.extend(child for child in children if "view" in child.name.lower())
    return candidates


def _read_parent_document(
    directory: Path, pattern: str, index: int
) -> tuple[dict[str, Any] | None, str | None]:
    """Read one parent artifact; return ``(document, problem_code)``."""
    if not pattern:
        return None, None
    for candidate_dir in _candidate_parent_dirs(directory):
        candidate = candidate_dir / _render_file_pattern(pattern, index, "")
        if not candidate.is_file():
            continue
        try:
            document = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None, "UNREADABLE"
        if isinstance(document, dict):
            return document, None
        return None, "UNREADABLE"
    return None, "MISSING"


def resolve_parent_artifacts(
    path: Path | str, contract: DecisionContract
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    """Resolve the parent batch manifest and parent view for a decision file.

    Returns ``(parent_batch, parent_view, notes)``.  A parent that cannot be
    located resolves to ``None``; the caller decides what that means.  The
    parent batch manifest carries the authoritative record count, and the
    parent view carries the authoritative id order.
    """
    file_path = Path(path)
    name_match = _match_decision_name(file_path.name, contract)
    notes: list[str] = []
    if name_match.index is None:
        return None, None, notes
    batch_document, batch_problem = _read_parent_document(
        file_path.parent, contract.batch_file_pattern, name_match.index
    )
    view_document, view_problem = _read_parent_document(
        file_path.parent, contract.view_file_pattern, name_match.index
    )
    if batch_problem == "UNREADABLE":
        notes.append(STRUCT_PARENT_BATCH_UNREADABLE)
    if view_problem == "UNREADABLE":
        notes.append(STRUCT_PARENT_VIEW_UNREADABLE)
    return batch_document, view_document, notes


def _attested_sha(
    document: Mapping[str, Any],
    parent_batch: Mapping[str, Any] | None,
    parent_view: Mapping[str, Any] | None,
    key: str,
) -> tuple[str | None, str | None]:
    """Return the attested value of ``key`` and the artifact it came from."""
    for source, candidate in (
        ("decision_file", document),
        ("parent_batch", parent_batch),
        ("parent_view", parent_view),
    ):
        if not candidate:
            continue
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            return value, source
    return None, None


def _as_int(value: Any) -> int | None:
    """Return ``value`` as an int, or ``None`` when it is not numeric."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


#: Keys a parent artifact may use to state its own record count, in order of
#: preference.  The harness lane states it as ``batch_size``; the pilot lane
#: states it as ``n_records``.
PARENT_RECORD_COUNT_KEYS: tuple[str, ...] = (
    "n_records",
    "batch_size",
    "record_count",
)
#: Keys a parent artifact may use to carry its records as a list.
PARENT_RECORD_LIST_KEYS: tuple[str, ...] = ("records", "papers")

#: Keys a parent *record* may use to state its own id, in order of
#: preference.  The decision rows carry their id under the contract's
#: canonical id field, which may be a different spelling -- so the two sides
#: are resolved explicitly and never assumed to share a key.
PARENT_ID_KEYS: tuple[str, ...] = ("screening_id", "workspace_id", "study_id")


def _parent_record_count(document: Mapping[str, Any] | None) -> int | None:
    """Return the record count a parent artifact states for itself.

    The parent artifact is the count authority; the key it uses to state the
    count depends on the lane, so several documented spellings are accepted.
    """
    if not document:
        return None
    for key in PARENT_RECORD_COUNT_KEYS:
        count = _as_int(document.get(key))
        if count is not None:
            return count
    for key in PARENT_RECORD_LIST_KEYS:
        records = document.get(key)
        if isinstance(records, list):
            return len(records)
    return None


def _extract_ordered_ids(
    document: Mapping[str, Any] | None,
) -> list[str | None] | None:
    """Return the ordered id list a parent artifact carries, or ``None``.

    ``None`` means the artifact carries no ordered record list at all.  A
    list entry is ``None`` when that record states no id under any of
    :data:`PARENT_ID_KEYS` -- the caller must then treat the order as *not
    verifiable* rather than as matching.
    """
    if not document:
        return None
    for list_key in PARENT_RECORD_LIST_KEYS:
        records = document.get(list_key)
        if not isinstance(records, list):
            continue
        ids: list[str | None] = []
        for record in records:
            value: str | None = None
            if isinstance(record, dict):
                for id_key in PARENT_ID_KEYS:
                    candidate = record.get(id_key)
                    if candidate is not None and str(candidate).strip():
                        value = str(candidate)
                        break
            ids.append(value)
        return ids
    return None


def _row_ids(rows: list[Any], id_field: str) -> list[str | None]:
    """Return the ordered id list of the decision rows.

    The id is read under one explicit field only -- the contract's
    ``canonical_id_field``.  A row that states no id under that field yields
    ``None``, so the comparison can never pass vacuously.
    """
    ids: list[str | None] = []
    for row in rows:
        value: str | None = None
        if isinstance(row, dict):
            candidate = row.get(id_field)
            if candidate is not None and str(candidate).strip():
                value = str(candidate)
        ids.append(value)
    return ids


# ---------------------------------------------------------------------------
# File classification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FileClassification:
    """The classification of one decision file.

    ``tier`` is one of :data:`TIERS`; ``structural`` holds the blocking
    findings, ``debt`` holds one entry per row that carries a debt finding,
    ``advisory`` holds one entry per row that carries an advisory finding,
    ``header`` holds the attested header information, ``rows`` is the row
    count, and ``canonical_rows`` is the canonical projection of every row
    (verbatim values, or ``None`` where a canonical field was absent).
    """

    file: str
    tier: str
    structural: tuple[str, ...] = ()
    debt: tuple[dict[str, Any], ...] = ()
    advisory: tuple[str, ...] = ()
    header: Mapping[str, Any] = field(default_factory=dict)
    rows: int = 0
    canonical_rows: tuple[dict[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return the classification as a JSON-serializable mapping."""
        return {
            "file": self.file,
            "tier": self.tier,
            "rows": self.rows,
            "header": dict(self.header),
            "structural": list(self.structural),
            "debt": [dict(entry) for entry in self.debt],
            "advisory": list(self.advisory),
            "canonical_rows": [dict(row) for row in self.canonical_rows],
        }

    def debt_tags(self) -> list[str]:
        """Return every debt tag recorded for this file, in row order."""
        tags: list[str] = []
        for entry in self.debt:
            tags.extend(str(tag) for tag in entry.get("debt", []))
        return tags

    def advisory_tags(self) -> list[str]:
        """Return every advisory tag recorded for this file, in row order."""
        tags: list[str] = []
        for entry in self.advisory:
            tags.extend(str(tag) for tag in entry.get("advisory", []))
        return tags


def _finish(
    name: str,
    structural: list[str],
    debt_rows: list[dict[str, Any]],
    advisory_rows: list[dict[str, Any]],
    header: dict[str, Any],
    rows: int,
    canonical_rows: list[dict[str, Any]] | None = None,
) -> FileClassification:
    """Assemble a classification and derive its tier.

    The rollup is :data:`TIER_RULE`: a structural finding makes the file
    ``BAD``; any debt **or advisory** finding makes it ``DEBT``; otherwise it
    is ``VALID``.
    """
    if structural:
        tier = TIER_BAD
    elif debt_rows or advisory_rows:
        tier = TIER_DEBT
    else:
        tier = TIER_VALID
    return FileClassification(
        file=name,
        tier=tier,
        structural=tuple(structural),
        debt=tuple(debt_rows),
        advisory=tuple(advisory_rows),
        header=header,
        rows=rows,
        canonical_rows=tuple(canonical_rows or ()),
    )


def classify_decision_file(
    path: Path | str,
    contract: DecisionContract,
    *,
    parent_batch: Mapping[str, Any] | None = None,
    parent_view: Mapping[str, Any] | None = None,
) -> FileClassification:
    """Classify one decision file against its parent artifacts.

    The parent batch manifest is the record-count authority and the parent
    view is the id-order authority.  A dispatch prompt or a producer
    self-report is never an authority; a disagreement is reported as
    ``SELF_REPORT_COUNT_MISMATCH``.

    ``parent_batch`` / ``parent_view`` override the on-disk resolution when a
    mapping is supplied.  The on-disk resolution is deterministic, so an
    absent parent always resolves to ``None``.
    """
    file_path = Path(path)
    name = file_path.name
    structural: list[str] = []
    advisory_rows: list[dict[str, Any]] = []
    debt_rows: list[dict[str, Any]] = []
    header: dict[str, Any] = {"checks": {}}
    checks: dict[str, str] = header["checks"]

    if not contract.schema_version_supported:
        header["schema_version"] = contract.schema_version
        structural.append(STRUCT_SCHEMA_VERSION_UNSUPPORTED)
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)

    name_match = _match_decision_name(name, contract)
    header["file_name_canonical"] = name_match.canonical
    header["canonical_file_name"] = name_match.expected_name
    header["batch_index"] = name_match.index
    header["family"] = name_match.family
    if not name_match.canonical:
        structural.append(STRUCT_FILENAME_NOT_CANONICAL)

    if not file_path.is_file():
        structural.append(STRUCT_FILE_MISSING)
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        structural.append(f"{STRUCT_FILE_UNREADABLE}:{exc.strerror or 'read failed'}")
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)

    if raw.startswith(codecs.BOM_UTF8):
        structural.append(STRUCT_BOM_DETECTED)
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        structural.append(f"{STRUCT_UTF8_DECODE_ERROR}:{exc.reason}")
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        structural.append(f"{STRUCT_JSON_PARSE}:{exc.msg}")
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)
    if not isinstance(document, dict):
        structural.append(STRUCT_NOT_A_JSON_OBJECT)
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)

    # -- parents: the count and id-order authority -------------------------
    resolved_batch, resolved_view, parent_notes = resolve_parent_artifacts(
        file_path, contract
    )
    structural.extend(parent_notes)
    batch_document = parent_batch if parent_batch is not None else resolved_batch
    view_document = parent_view if parent_view is not None else resolved_view

    batch_expected = bool(contract.batch_file_pattern)
    view_expected = bool(contract.view_file_pattern)
    batch_missing = batch_expected and batch_document is None
    view_missing = view_expected and view_document is None
    header["parent_batch_resolved"] = batch_document is not None
    header["parent_view_resolved"] = view_document is not None
    header["parent_resolved"] = batch_document is not None or view_document is not None
    if batch_missing and view_missing:
        structural.append(STRUCT_PARENT_MISSING)
    else:
        if batch_missing:
            structural.append(STRUCT_PARENT_BATCH_MISSING)
        if view_missing:
            structural.append(STRUCT_PARENT_VIEW_MISSING)

    # -- header attestation -------------------------------------------------
    screener_id = document.get("screener_id")
    header["screener_id"] = str(screener_id) if screener_id is not None else None
    if name_match.family is None:
        checks["screener_id"] = "SKIPPED_FAMILY_UNRESOLVED"
    elif str(screener_id) != name_match.family:
        structural.append(f"{STRUCT_HEADER_UNATTESTED}:screener_id={screener_id!r}")
        checks["screener_id"] = "FAILED"
    else:
        checks["screener_id"] = "PASSED"

    for key, prefix, missing_code, mismatch_code in (
        (
            "criteria_sha256",
            contract.expected_criteria_sha256_prefix,
            STRUCT_CRITERIA_SHA_MISSING,
            STRUCT_CRITERIA_SHA_MISMATCH,
        ),
        (
            "prompt_template_sha256",
            contract.expected_prompt_sha256_prefix,
            STRUCT_PROMPT_SHA_MISSING,
            STRUCT_PROMPT_SHA_MISMATCH,
        ),
    ):
        value, source = _attested_sha(document, batch_document, view_document, key)
        header[key] = value
        header[f"{key}_source"] = source
        if not prefix:
            checks[key] = "SKIPPED_NO_EXPECTED_PREFIX"
            header[f"{key}_attested"] = False
        elif value is None:
            structural.append(missing_code)
            checks[key] = "FAILED"
            header[f"{key}_attested"] = False
        elif not value.startswith(prefix):
            structural.append(mismatch_code)
            checks[key] = "FAILED"
            header[f"{key}_attested"] = False
        else:
            checks[key] = "PASSED"
            header[f"{key}_attested"] = True

    # -- rows ---------------------------------------------------------------
    rows = document.get("decisions")
    if rows is None:
        rows = document.get("rows")
    if not isinstance(rows, list):
        structural.append(STRUCT_NO_ROWS_KEY)
        return _finish(name, structural, debt_rows, advisory_rows, header, 0)
    row_count = len(rows)

    expected_count = _parent_record_count(batch_document)
    if expected_count is None:
        expected_count = _parent_record_count(view_document)
    if expected_count is None:
        if batch_document is not None or view_document is not None:
            structural.append(STRUCT_PARENT_ROW_COUNT_UNAVAILABLE)
    else:
        if row_count != expected_count:
            structural.append(f"{STRUCT_ROW_COUNT}:{row_count}!={expected_count}")
        # A producer self-report is never the authority: the parent batch
        # manifest wins and the disagreement is surfaced.  The self-report is
        # the record count a producer copies into its own decision-file header
        # under ``n_records``; nothing else writes that key.
        claimed = _as_int(document.get("n_records"))
        if claimed is not None and claimed != expected_count:
            structural.append(
                f"{STRUCT_SELF_REPORT_COUNT_MISMATCH}:{claimed}!={expected_count}"
            )

    # -- id order: the authoritative ordered id list ------------------------
    #
    # The view is the authority when one is configured *and* resolved; it is
    # an optional redaction overlay.  Otherwise the parent batch's ordered
    # record list is the authority.  The two sides carry their ids under
    # different keys (harness batch: ``workspace_id``; decision row:
    # ``screening_id``), so each side is resolved explicitly and a missing
    # id on either side makes the order *not verifiable* -- it can never be
    # reported as "checked and in order".
    authority: str | None = None
    authority_ids: list[str | None] | None = None
    if view_document is not None:
        authority = "view"
        authority_ids = _extract_ordered_ids(view_document)
    elif batch_document is not None:
        authority = "batch"
        authority_ids = _extract_ordered_ids(batch_document)
    header["id_order_authority"] = authority
    if authority is not None:
        row_ids = _row_ids(rows, contract.canonical_id_field)
        if (
            not authority_ids
            or not row_ids
            or any(identifier is None for identifier in authority_ids)
            or any(identifier is None for identifier in row_ids)
        ):
            structural.append(STRUCT_ID_ORDER_NOT_VERIFIABLE)
        elif row_ids != authority_ids:
            structural.append(
                STRUCT_ID_ORDER_MISMATCH_VS_VIEW
                if authority == "view"
                else STRUCT_ID_ORDER_MISMATCH_VS_BATCH
            )

    # -- per row ------------------------------------------------------------
    vocabulary = contract.decision_vocabulary
    canonical_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            structural.append(f"ROW_{row_index}_NOT_AN_OBJECT")
            canonical_rows.append({})
            continue
        canonical, tags = normalize_row(row, contract)
        canonical_rows.append(dict(canonical))
        present = [
            name_ for name_ in contract.canonical_fields if row.get(name_) is not None
        ]
        alias_hit = any(
            alias_key in row and row[alias_key] is not None
            for alias_key in contract.reason_code_aliases
        )
        if not present and not alias_hit:
            structural.append(f"ROW_{row_index}_NO_CANONICAL_FIELDS")
        screening_id = row.get("screening_id")
        if "screening_id" in contract.canonical_fields and not screening_id:
            structural.append(f"ROW_{row_index}_MISSING_SCREENING_ID")
        decision = canonical.get("decision")
        if vocabulary and decision not in vocabulary:
            structural.append(f"ROW_{row_index}_DECISION_OUT_OF_VOCAB:{decision!r}")
        debt_tags = [tag for tag in tags if is_debt_tag(tag)]
        advisory_tags = [tag for tag in tags if is_advisory_tag(tag)]
        row_identity = {
            "row": row_index,
            "screening_id": screening_id if isinstance(screening_id, str) else None,
        }
        if debt_tags:
            debt_rows.append({**row_identity, "debt": debt_tags})
        if advisory_tags:
            advisory_rows.append({**row_identity, "advisory": advisory_tags})

    return _finish(
        name, structural, debt_rows, advisory_rows, header, row_count, canonical_rows
    )


# ---------------------------------------------------------------------------
# Inventory and ledger
# ---------------------------------------------------------------------------


def discover_decision_files(
    directory: Path | str,
    contract: DecisionContract,
    *,
    exclude: Iterable[Path | str] = (),
) -> list[Path]:
    """Return the decision-file candidates in ``directory``.

    The inventory is deliberately coarse: every ``*.json`` file is a candidate
    except the parent batch manifests, the parent views, the batch manifest
    index, and the explicitly excluded paths.  A decision file whose name is
    not canonical is therefore *surfaced* rather than silently dropped.

    The reader's own artifacts are excluded **by name**
    (:data:`READER_ARTIFACT_FILE_NAMES`) as well as by path, so the reader
    can never re-ingest its report sidecar or its contract configuration.
    """
    base = Path(directory)
    if not base.is_dir():
        raise DecisionContractRefused(
            REFUSAL_DECISIONS_DIR_MISSING,
            f"screening decisions directory not found: {base}",
        )
    excluded = {Path(item).resolve() for item in exclude}
    batch_pattern = _compile_file_pattern(contract.batch_file_pattern, strict=False)
    view_pattern = _compile_file_pattern(contract.view_file_pattern, strict=False)
    found: list[Path] = []
    for candidate in sorted(base.glob("*.json")):
        if not candidate.is_file():
            continue
        if candidate.resolve() in excluded:
            continue
        if candidate.name in READER_ARTIFACT_FILE_NAMES:
            continue
        if candidate.name == "MANIFEST.json":
            continue
        if batch_pattern is not None and batch_pattern.fullmatch(candidate.name):
            continue
        if view_pattern is not None and view_pattern.fullmatch(candidate.name):
            continue
        found.append(candidate)
    return found


def build_debt_ledger(
    classifications: Iterable[FileClassification],
) -> dict[str, Any]:
    """Return the per-file, per-tag debt ledger for a set of classifications.

    The ledger is deterministically ordered (files by name, tags by code) and
    reconciles: the per-tier file counts sum to ``files_scanned`` and every
    per-file tier matches its classification.

    ``debt_tag_counts`` / ``advisory_tag_counts`` count the full tag (for
    example ``ALIAS_REASON_CODE:exclusion_reason_code``); the matching
    ``*_prefix_counts`` histograms aggregate by code, so the ledger can be
    compared with a prefix-keyed histogram directly.
    """
    files = sorted(classifications, key=lambda item: item.file)
    ledger: dict[str, Any] = {
        "files_scanned": len(files),
        "files_by_tier": {tier: 0 for tier in TIERS},
        "rows_scanned": 0,
        "debt_tag_counts": {},
        "debt_prefix_counts": {},
        "advisory_tag_counts": {},
        "advisory_prefix_counts": {},
        "structural_code_counts": {},
        "files": [],
    }
    debt_counts: dict[str, int] = {}
    debt_prefix_counts: dict[str, int] = {}
    advisory_counts: dict[str, int] = {}
    advisory_prefix_counts: dict[str, int] = {}
    structural_counts: dict[str, int] = {}
    for classification in files:
        tier = classification.tier
        ledger["files_by_tier"][tier] = ledger["files_by_tier"].get(tier, 0) + 1
        ledger["rows_scanned"] += classification.rows
        file_debt: dict[str, int] = {}
        file_advisory: dict[str, int] = {}
        for tag in classification.debt_tags():
            file_debt[tag] = file_debt.get(tag, 0) + 1
            debt_counts[tag] = debt_counts.get(tag, 0) + 1
            prefix = tag_prefix(tag)
            debt_prefix_counts[prefix] = debt_prefix_counts.get(prefix, 0) + 1
        for tag in classification.advisory_tags():
            file_advisory[tag] = file_advisory.get(tag, 0) + 1
            advisory_counts[tag] = advisory_counts.get(tag, 0) + 1
            prefix = tag_prefix(tag)
            advisory_prefix_counts[prefix] = advisory_prefix_counts.get(prefix, 0) + 1
        for code in classification.structural:
            prefix = tag_prefix(code)
            structural_counts[prefix] = structural_counts.get(prefix, 0) + 1
        ledger["files"].append(
            {
                "file": classification.file,
                "tier": tier,
                "rows": classification.rows,
                "structural": list(classification.structural),
                "debt_tags": dict(sorted(file_debt.items())),
                "advisory_tags": dict(sorted(file_advisory.items())),
            }
        )
    ledger["debt_tag_counts"] = dict(sorted(debt_counts.items()))
    ledger["debt_prefix_counts"] = dict(sorted(debt_prefix_counts.items()))
    ledger["advisory_tag_counts"] = dict(sorted(advisory_counts.items()))
    ledger["advisory_prefix_counts"] = dict(sorted(advisory_prefix_counts.items()))
    ledger["structural_code_counts"] = dict(sorted(structural_counts.items()))
    return ledger


def build_report(
    contract: DecisionContract, classifications: Iterable[FileClassification]
) -> dict[str, Any]:
    """Return the deterministic report payload for a set of classifications.

    The payload carries no timestamp and no absolute path, so two runs over
    identical inputs produce byte-identical report content.  It states the
    tier rollup rule (:data:`TIER_RULE`), reports how many parents resolved,
    and raises a scan-level finding when the scan verified nothing:
    ``NO_DECISION_FILES`` for an empty scan, ``NO_PARENTS_RESOLVED`` when not
    one parent artifact resolved for any scanned file.
    """
    ordered = sorted(classifications, key=lambda item: item.file)
    with_parents = sum(1 for item in ordered if item.header.get("parent_resolved"))
    scan_findings: list[str] = []
    if not ordered:
        scan_findings.append(SCAN_NO_DECISION_FILES)
    elif not with_parents:
        scan_findings.append(SCAN_NO_PARENTS_RESOLVED)
    return {
        "report_version": "1",
        "tier_vocabulary": list(TIERS),
        "tier_rule": TIER_RULE,
        "scan_findings": scan_findings,
        "parent_resolution": {
            "files_scanned": len(ordered),
            "files_with_parents": with_parents,
            "files_without_parents": len(ordered) - with_parents,
        },
        "contract": contract.as_dict(),
        "ledger": build_debt_ledger(ordered),
        "files": [item.as_dict() for item in ordered],
    }


# ---------------------------------------------------------------------------
# Command surface
# ---------------------------------------------------------------------------


def _relative_to_workspace(workspace: Path, path: Path) -> str:
    """Return ``path`` relative to ``workspace`` when possible."""
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_output_path(
    workspace: Path, value: Path | str | None, default: Path
) -> Path:
    """Resolve an output path argument relative to the workspace."""
    if value is None:
        return default
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return workspace / candidate


def _scan_finding_reason(finding: str, decisions_path: Path) -> str:
    """Return the legible reason text for a scan-level finding."""
    if finding == SCAN_NO_DECISION_FILES:
        return (
            f"no screening decision file was found in {decisions_path}; the "
            "decisions directory is empty or mis-pointed -- some lanes keep "
            "the decision files one level down (for example "
            "<lane>/decisions/), so check --decisions-dir"
        )
    if finding == SCAN_NO_PARENTS_RESOLVED:
        return (
            f"not one parent artifact resolved for any scanned file under "
            f"{decisions_path}; the parent locations do not match the "
            "contract -- this is not the same as a corpus in which every "
            "file is genuinely bad"
        )
    return "the scan verified nothing; see the report scan findings"


def cmd_validate(
    workspace_dir: Path | str,
    *,
    out: Path | str | None = None,
    contract: Path | str | None = None,
    decisions_dir: Path | str | None = None,
) -> int:
    """Validate the screening decision files of one workspace.

    Scans the workspace decisions directory, writes exactly one new JSON
    report sidecar, prints a per-tier summary, and logs exactly one audit
    event through ``scholar_harness.workspace.audit.log_event``.

    ``decisions_dir`` is a workspace-relative path (default
    ``literature/screening``); it makes a differently laid-out lane readable
    without moving a single file.  ``out`` and ``contract`` accept a
    workspace-relative path or an absolute one.

    The command refuses to overwrite an existing report (``REPORT_EXISTS``)
    and never writes into the producer decision files.  A missing workspace
    root is refused *before* anything is logged, so a mistyped path never
    materialises ``audit/journal.jsonl`` or ``INDEX.md``.
    """
    workspace = Path(workspace_dir).resolve()
    if not workspace.is_dir():
        # Refused before logging: there is no workspace to hold a ledger, and
        # a typo must not create one.
        print(
            f"{REFUSAL_WORKSPACE_MISSING}: workspace root does not exist: {workspace}",
            file=sys.stderr,
        )
        sys.exit(1)

    decisions_relative = Path(decisions_dir) if decisions_dir else DEFAULT_DECISIONS_DIR
    decisions_path = _resolve_output_path(
        workspace, decisions_relative, workspace / DEFAULT_DECISIONS_DIR
    )
    contract_path = _resolve_output_path(
        workspace, contract, workspace / CONTRACT_RELATIVE_PATH
    )
    report_path = _resolve_output_path(workspace, out, workspace / REPORT_RELATIVE_PATH)
    contract_relative = _relative_to_workspace(workspace, contract_path)

    try:
        if contract is not None and not contract_path.is_file():
            raise DecisionContractRefused(
                REFUSAL_CONTRACT_CONFIG_MISSING,
                f"decision contract configuration not found: {contract_path}",
            )
        if report_path.exists():
            raise DecisionContractRefused(
                REFUSAL_REPORT_EXISTS,
                f"refusing to overwrite the existing decision contract report: {report_path}",
            )
        if not decisions_path.is_dir():
            raise DecisionContractRefused(
                REFUSAL_DECISIONS_DIR_MISSING,
                f"screening decisions directory not found: {decisions_path}",
            )
        loaded = load_contract(contract_path)
        if not loaded.schema_version_supported:
            raise DecisionContractRefused(
                REFUSAL_SCHEMA_VERSION_UNSUPPORTED,
                "unsupported decision contract schema major version: "
                f"{loaded.schema_version}",
            )
        candidates = discover_decision_files(
            decisions_path, loaded, exclude=[contract_path, report_path]
        )
        classifications = [classify_decision_file(item, loaded) for item in candidates]
    except DecisionContractRefused as refusal:
        log_event(
            workspace,
            AUDIT_ACTION,
            f"Decision contract validation refused: {refusal.code}: {refusal.message}",
            agent=AUDIT_AGENT,
            inputs=[contract_relative],
            outputs=[],
            parameters={
                "contract_path": contract_relative,
                "decisions_dir": _relative_to_workspace(workspace, decisions_path),
                "tier_vocabulary": list(TIERS),
            },
            metrics={
                "files_scanned": 0,
                "valid": 0,
                "debt": 0,
                "bad": 0,
                "debt_tag_count": 0,
            },
            status="FAILED",
        )
        print(f"{refusal.code}: {refusal.message}", file=sys.stderr)
        sys.exit(1)

    report = build_report(loaded, classifications)
    ledger = report["ledger"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    files_scanned = ledger["files_scanned"]
    valid = ledger["files_by_tier"].get(TIER_VALID, 0)
    debt = ledger["files_by_tier"].get(TIER_DEBT, 0)
    bad = ledger["files_by_tier"].get(TIER_BAD, 0)
    debt_tag_count = sum(ledger["debt_tag_counts"].values())
    scan_findings = list(report["scan_findings"])
    findings_note = ""
    if scan_findings:
        findings_note = "; scan findings: " + " | ".join(
            f"{finding} -- {_scan_finding_reason(finding, decisions_path)}"
            for finding in scan_findings
        )
    description = (
        f"Validated {files_scanned} screening decision file(s) against the "
        f"workspace decision contract: {valid} VALID / {debt} DEBT / {bad} BAD; "
        f"{debt_tag_count} debt tag(s) recorded; no producer file modified"
        f"{findings_note}"
    )
    # A scan that verified nothing must not report SUCCESS: an empty or
    # parent-less scan is a failure of the scan, not a clean result.
    status = "FAILED" if scan_findings else "SUCCESS"
    log_event(
        workspace,
        AUDIT_ACTION,
        description,
        agent=AUDIT_AGENT,
        inputs=[
            *[
                _relative_to_workspace(workspace, item)
                for item in sorted(candidates, key=lambda path: path.name)
            ],
            contract_relative,
        ],
        outputs=[_relative_to_workspace(workspace, report_path)],
        parameters={
            "contract_path": contract_relative,
            "decisions_dir": _relative_to_workspace(workspace, decisions_path),
            "tier_vocabulary": list(TIERS),
            "tier_rule": TIER_RULE,
        },
        metrics={
            "files_scanned": files_scanned,
            "valid": valid,
            "debt": debt,
            "bad": bad,
            "debt_tag_count": debt_tag_count,
            "scan_finding_count": len(scan_findings),
            "scan_findings": list(scan_findings),
        },
        status=status,
    )
    print(
        f"Screening decision contract validation: {files_scanned} file(s) scanned - "
        f"VALID {valid} / DEBT {debt} / BAD {bad}; "
        f"{debt_tag_count} debt tag(s) recorded"
    )
    for finding in scan_findings:
        print(
            f"SCAN FINDING {finding}: {_scan_finding_reason(finding, decisions_path)}",
            file=sys.stderr,
        )
    if scan_findings:
        sys.exit(1)
    return 0
