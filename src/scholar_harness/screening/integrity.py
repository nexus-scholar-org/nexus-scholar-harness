"""Screening decision integrity gates (AG-02, workflow-integrity only).

Pure functions of (accepted parent batch candidates, submitted decision file
bytes + parsed entries, registry head binding). No filesystem writes, no clock
reads, no network, no identity lookup.

These gates treat every recommendation source identically: method labels,
reviewer-name strings, confidence scores, and critic verdicts confer nothing,
and no field here introduces a new person, role, or permission concept.
"""

# non-claim (AG-02 S2): workflow-integrity (tamper-evidence + fail-closed), not authorization.

from __future__ import annotations

import hashlib
from typing import Any

#: Decision file covers fewer, or more, studies than its parent batch.
COVERAGE_INCOMPLETE = "COVERAGE_INCOMPLETE"
#: The same study appears twice for the single screener.
DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
#: A MAYBE/CONFLICT row was presented for finalization.
UNRESOLVED_FINALIZE_REFUSED = "UNRESOLVED_FINALIZE_REFUSED"
#: Decision bytes differ from the previously accepted bytes for the same batch.
CONTENT_CHANGED = "CONTENT_CHANGED"
#: The parent batch was superseded after the recorded acceptance.
STALE_BINDING = "STALE_BINDING"

#: Legacy decision strings (and any checklist-derived outcome) that count as
#: unresolved. Finalization refuses them instead of coercing them.
UNRESOLVED_VALUES = frozenset({"MAYBE", "CONFLICT"})


class ScreeningIntegrityRefused(RuntimeError):
    """Typed refusal to finalize a single-screener decision file.

    Mirrors the ``VerificationIdentityRefused`` shape (stable ``code``,
    human ``message``, machine-readable ``details``) so callers can branch
    on the failure. A subclass of ``RuntimeError`` so the existing
    fail-closed ``cmd_collect`` tail (``raise RuntimeError`` on missing
    batches) still catches it without a new publication path.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


def decision_file_sha256(raw_bytes: bytes) -> str:
    """Return the ``sha256:<hex>`` fingerprint of exact decision-file bytes."""
    return "sha256:" + hashlib.sha256(raw_bytes).hexdigest()


def _entry_study_id(entry: dict[str, Any]) -> str:
    """Study key for one decision entry (same expression the collector uses)."""
    return str(entry.get("workspace_id") or entry.get("study_id") or "")


def check_exact_coverage(
    candidate_ids: set[str], entries: list[dict[str, Any]]
) -> None:
    """Require a 1:1 correspondence between parent candidates and entries.

    Raises ``ScreeningIntegrityRefused`` with ``DUPLICATE_ENTRY`` when the
    same study id appears twice for the single screener, or with
    ``COVERAGE_INCOMPLETE`` when any candidate is missing or any entry
    references a study outside the accepted parent candidate set (extra
    stays fail-closed, as before).
    """
    seen: set[str] = set()
    duplicates: set[str] = set()
    for entry in entries:
        key = _entry_study_id(entry)
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        raise ScreeningIntegrityRefused(
            DUPLICATE_ENTRY,
            "decision file repeats study id(s) for the single screener: "
            + ", ".join(sorted(duplicates)),
            duplicate_study_ids=sorted(duplicates),
        )
    keys = {_entry_study_id(entry) for entry in entries}
    missing = sorted(set(candidate_ids) - keys)
    extra = sorted(keys - set(candidate_ids))
    if missing or extra:
        raise ScreeningIntegrityRefused(
            COVERAGE_INCOMPLETE,
            "decision file does not exactly cover the parent batch candidate "
            f"set (missing={missing}, extra={extra})",
            missing_study_ids=missing,
            extra_study_ids=extra,
        )


def check_no_unresolved_for_finalize(entries: list[dict[str, Any]]) -> None:
    """Refuse finalization while any entry carries MAYBE/CONFLICT.

    Applies to explicit legacy decision strings and to checklist-derived
    outcomes alike: callers pass derived ``{"workspace_id", "decision"}``
    records through the same gate so unresolved rows are never silently
    coerced into terminal exclusions.
    """
    unresolved: list[dict[str, str]] = []
    for entry in entries:
        raw = entry.get("decision")
        if isinstance(raw, str) and raw.strip().upper() in UNRESOLVED_VALUES:
            unresolved.append(
                {
                    "study_id": _entry_study_id(entry),
                    "decision": raw.strip().upper(),
                }
            )
    if unresolved:
        raise ScreeningIntegrityRefused(
            UNRESOLVED_FINALIZE_REFUSED,
            "decision file carries unresolved row(s) presented for "
            "finalization; refusing instead of coercing to EXCLUDE",
            unresolved_rows=unresolved,
        )


def bind_batch(
    batch_index: int, registry_head_batch_artifact: dict[str, Any]
) -> tuple[str, str]:
    """Return the freshness anchor a decision file is collected against.

    The binding is the registry head batch artifact id + sha for
    ``batch_index`` (run id + parent batch artifact id + sha): identical
    inputs re-prepare idempotently to the same binding, while a superseded
    batch resolves to a different one.
    """
    return (
        str(registry_head_batch_artifact["artifact_id"]),
        str(registry_head_batch_artifact["sha256"]),
    )
