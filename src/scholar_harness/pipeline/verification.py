"""Verification stage (HCM-04e neutral extraction).

Stage 3 of the research pipeline: verifier citation check, DOI-bridge
identity resolution (HCM-04e-1 Option B bridge-or-refuse), verified/quarantine
publication, and the ``VERIFICATION_IDENTITY_RESOLVED`` audit event.
Extracted verbatim from ``ResearchOrchestrator.run_pipeline_async`` so the
orchestrator delegates without behavior change.

Policy (approved Option B, preserved exactly): preserve a valid
verifier-returned ``workspace_id``; restore ONLY via a DOI bridge to a
recorded dedup parent; otherwise refuse with a typed reason. No ``SCI-``
mint, no inference, no downstream publication of the refused row. Positions
use ``enumerate`` (never ``.index`` equality).

Neutrality: stdlib plus ``scholar-search-kit`` only -- no console transport,
no Contract v1 acceptance beyond the recorded bridge. The stage owns the
authoritative ``verified.json`` publication, the ``verified_unresolved.json``
quarantine (written only when refusals exist; a clean run removes any stale
file), and the single ``VERIFICATION_IDENTITY_RESOLVED`` legacy audit event
with the observed outcome status (never a constant SUCCESS for a refused
run). Serialization (``asdict``/``indent=2``/``default=str``), filenames,
codes, messages, counts, and audit order/payload are unchanged.

Failure propagates with no fabricated documents, audit rows, or success
claims: a verifier raise publishes nothing; an audit raise propagates after
the files are written. Stage 3 has no client resource to close.

H-quota-hang (2026-11-20). The stage reads the researcher's stop between
records (``should_stop``, set on the verifier) and the verifier stops asking
a database whose quota is used up. Every record is still published (none is
dropped); the ones not checked are listed in
``literature/verification_checks.json`` (one row per published or refused
row: its code, ``not_done`` and ``reason``), and the outcome says how many.
``keep`` lets a later attempt check only those: the rows it names (by
workspace id, from an earlier checks file) are published as they are.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scholar_search.verifier import QUOTA_EXHAUSTED, DocumentVerifier
from scholar_search.verifier import STOPPED as STOPPED_BY_RESEARCHER

from scholar_harness.verification_identity import (
    AUDIT_ACTION as _VERIFICATION_AUDIT_ACTION,
    QUARANTINE_FILENAME as _VERIFICATION_QUARANTINE_FILENAME,
    VERIFICATION_IDENTITY_AMBIGUOUS_DOI,
    VERIFICATION_IDENTITY_BRIDGE_CONFLICT,
    VERIFICATION_IDENTITY_BRIDGE_MISS,
    VERIFICATION_IDENTITY_MISSING_DOI,
    build_doi_bridge,
)
from scholar_harness.workspace.audit import append_legacy_event

logger = logging.getLogger(__name__)


@dataclass
class VerificationOutcome:
    """Typed outcome of the verification stage.

    ``documents`` are the identified rows only (the ``verified_docs`` binding
    Stage 4 counts for ``papers_to_screen``); refused rows never enter it.
    ``quarantine`` is the ``literature/``-relative quarantine path when
    refusals exist, else ``None``.
    """

    documents: list[Any]
    status: str
    verified: int
    refused: int
    preserved: int
    bridge_restored: int
    refusal_reasons: dict[str, int]
    quarantine: str | None
    #: H-quota-hang: records published without a complete check, and why.
    unchecked: int = 0
    unchecked_reasons: dict[str, int] = field(default_factory=dict)
    #: The databases the verifier stopped asking, with their reset time.
    paused: list[dict[str, Any]] = field(default_factory=list)
    #: The researcher's stop ended the checks between two records.
    stopped: bool = False
    #: Records checked by this attempt (all of them unless ``keep`` named some).
    checked: int = 0


#: Read by the coordinator through this module, which imports no kit module itself (HCM-04).
__all__ = [
    "CHECKS_FILENAME", "QUOTA_EXHAUSTED", "STOPPED_BY_RESEARCHER", "VerificationOutcome", "read_checks",
    "run_verification",
]

#: The per-record check record beside ``verified.json`` (a run record, not a Contract v1 artifact).
CHECKS_FILENAME = "verification_checks.json"
CHECKS_SCHEMA = "nexus.verification-checks.v1"


def _check_row(position: int, doc: Any, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "position": position,
        "workspace_id": getattr(doc, "workspace_id", None),
        "code": row.get("code"),
        "verified": row.get("verified"),
        "not_done": [str(part) for part in (row.get("not_done") or [])],
        "reason": row.get("reason"),
        "status": row.get("status"),
    }


def read_checks(literature_dir: Path | str) -> dict[str, Any] | None:
    """The checks record of the last verification, or ``None`` when absent or unreadable."""
    path = Path(literature_dir) / CHECKS_FILENAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("schema") != CHECKS_SCHEMA or not isinstance(data.get("rows"), list):
        return None
    return data


async def run_verification(
    *,
    documents: list[Any],
    literature_dir: Path | str,
    workspace_dir: Path | str,
    should_stop: Callable[[], bool] | None = None,
    keep: dict[str, dict[str, Any]] | None = None,
) -> VerificationOutcome:
    """Verify documents, resolve identity via the DOI bridge, publish results.

    Verbatim move of orchestrator Stage 3: ``DocumentVerifier()`` +
    ``process_batch(documents, verify=True, enrich=True)`` over ALL input
    documents, ``build_doi_bridge`` over the same inputs, the ``enumerate``
    preserve-valid / bridge-restore-exact / typed-refuse
    (``MISSING_DOI`` | ``AMBIGUOUS_DOI`` | ``BRIDGE_MISS``) loop with no mint,
    ``verified.json`` publication of identified rows only, ``PARTIAL`` |
    ``FAILED`` | ``SUCCESS`` counts with quarantine write / stale-quarantine
    removal, and the ``VERIFICATION_IDENTITY_RESOLVED`` legacy audit event
    with counts+reasons.

    Only mechanical parameterization: ``documents`` / ``literature_dir`` /
    ``workspace_dir`` inputs. No logic edits, no renames of codes/messages/
    filenames.

    H-quota-hang: ``should_stop`` is read before each record; ``keep`` maps
    a workspace id to its row of an earlier checks file, and such a record is
    published as it is, without asking any database again.
    """
    lit_dir = Path(literature_dir)
    lit_dir.mkdir(parents=True, exist_ok=True)

    verifier = DocumentVerifier()
    # Set on the instance, so a verifier double with the historical
    # ``process_batch(docs, verify, enrich)`` signature still runs.
    verifier.should_stop = should_stop
    keep = keep or {}
    kept = [bool(keep) and getattr(doc, "workspace_id", None) in keep for doc in documents]
    to_check = [doc for doc, is_kept in zip(documents, kept, strict=True) if not is_kept]
    checked_docs, audit = await verifier.process_batch(
        to_check, verify=True, enrich=True
    )
    audit = audit if isinstance(audit, list) else []
    if any(kept):
        # Merge the kept rows back in their places; the verifier's rows follow in order.
        verified_docs, rows = [], []
        fresh = iter(zip(checked_docs, audit + [{}] * (len(checked_docs) - len(audit)), strict=False))
        for doc, is_kept in zip(documents, kept, strict=True):
            if is_kept:
                verified_docs.append(doc)
                rows.append(dict(keep[doc.workspace_id]))
            else:
                checked, row = next(fresh)
                verified_docs.append(checked)
                rows.append(row if isinstance(row, dict) else {})
    else:
        verified_docs = list(checked_docs)
        rows = [audit[i] if i < len(audit) and isinstance(audit[i], dict) else {} for i in range(len(verified_docs))]
    unchecked_reasons: dict[str, int] = {}
    for row in rows:
        if row.get("not_done"):
            key = str(row.get("reason") or "UNKNOWN")
            unchecked_reasons[key] = unchecked_reasons.get(key, 0) + 1
    unchecked_n = sum(unchecked_reasons.values())
    paused = getattr(verifier, "paused", None)
    paused = [dict(p) for p in paused if isinstance(p, dict)] if isinstance(paused, list) else []
    stopped = getattr(verifier, "stopped", False) is True

    wsid_by_doi, ambiguous_dois = build_doi_bridge(documents)
    identified_docs: list[Any] = []
    refused_entries: list[dict[str, Any]] = []
    preserved_n = 0
    bridge_restored_n = 0
    # CORE-10: ids held by rows that kept theirs; a bridge may not reuse one.
    # Collected first so the outcome does not depend on row order.
    claimed: set[str] = {
        vd.workspace_id for vd in verified_docs if getattr(vd, "workspace_id", None)
    }
    for _pos, vd in enumerate(verified_docs):
        _external_ids = getattr(vd, "external_ids", None)
        _doi = (
            getattr(_external_ids, "doi", None) if _external_ids is not None else None
        )
        if getattr(vd, "workspace_id", None):
            preserved_n += 1
            identified_docs.append(vd)
            continue
        if _doi and _doi in wsid_by_doi and _doi not in ambiguous_dois:
            _target = wsid_by_doi[_doi]
            _source = documents[_pos] if _pos < len(documents) else None
            _source_id = getattr(_source, "workspace_id", None)
            if _target in claimed or (_source_id and _source_id != _target):
                refused_entries.append(
                    {
                        "position": _pos,
                        "code": VERIFICATION_IDENTITY_BRIDGE_CONFLICT,
                        "reason": (
                            f"DOI {_doi!r} bridges to {_target}, which "
                            + (
                                "another row of this batch already holds"
                                if _target in claimed
                                else f"is not this row's input id {_source_id}"
                            )
                            + "; restoring it would merge two studies"
                        ),
                        "doc": vd,
                    }
                )
                continue
            vd.workspace_id = _target
            claimed.add(_target)
            bridge_restored_n += 1
            identified_docs.append(vd)
            continue
        if not _doi:
            _code = VERIFICATION_IDENTITY_MISSING_DOI
            _reason = "no DOI to bridge to a recorded dedup parent"
        elif _doi in ambiguous_dois:
            _code = VERIFICATION_IDENTITY_AMBIGUOUS_DOI
            _reason = (
                f"DOI {_doi!r} maps to multiple dedup parents; bridge is ambiguous"
            )
        else:
            _code = VERIFICATION_IDENTITY_BRIDGE_MISS
            _reason = f"DOI {_doi!r} has no recorded dedup parent"
        refused_entries.append(
            {
                "position": _pos,
                "code": _code,
                "reason": _reason,
                "doc": vd,
            }
        )

    # One check row per published or refused row, with the id the bridge left it (H-quota-hang).
    check_rows = [_check_row(pos, doc, row) for pos, (doc, row) in enumerate(zip(verified_docs, rows, strict=True))]
    # Refused rows never enter the authoritative verified.json.
    verified_docs = identified_docs

    (lit_dir / "verified.json").write_text(
        json.dumps(
            [
                asdict(d) if hasattr(d, "__dataclass_fields__") else d
                for d in verified_docs
            ],
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    _refusal_counts: dict[str, int] = {}
    for _entry in refused_entries:
        _refusal_counts[_entry["code"]] = _refusal_counts.get(_entry["code"], 0) + 1
    if refused_entries:
        _verification_status = "PARTIAL" if verified_docs else "FAILED"
        (lit_dir / _VERIFICATION_QUARANTINE_FILENAME).write_text(
            json.dumps(
                [
                    {
                        "position": e["position"],
                        "code": e["code"],
                        "reason": e["reason"],
                        "record": (
                            asdict(e["doc"])
                            if hasattr(e["doc"], "__dataclass_fields__")
                            else e["doc"]
                        ),
                    }
                    for e in refused_entries
                ],
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
    else:
        _verification_status = "SUCCESS"
        _stale_quarantine = lit_dir / _VERIFICATION_QUARANTINE_FILENAME
        if _stale_quarantine.exists():
            _stale_quarantine.unlink()
    if unchecked_n and _verification_status == "SUCCESS":
        # Compass §3: degraded work is PARTIAL and says why (the checks file, the metrics).
        _verification_status = "PARTIAL"
    (lit_dir / CHECKS_FILENAME).write_text(
        json.dumps(
            {
                "schema": CHECKS_SCHEMA,
                "records": len(check_rows),
                "unchecked": unchecked_n,
                "unchecked_reasons": unchecked_reasons,
                "paused": paused,
                "stopped": stopped,
                "checked_now": len(to_check),
                "rows": check_rows,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    _quarantine_rel = (
        f"literature/{_VERIFICATION_QUARANTINE_FILENAME}" if refused_entries else None
    )
    append_legacy_event(
        workspace_dir,
        _VERIFICATION_AUDIT_ACTION,
        "scholar-harness",
        (
            "Stage 3 verification identity bridge-or-refuse: "
            f"{preserved_n} preserved, {bridge_restored_n} bridge-restored, "
            f"{len(refused_entries)} refused"
            + (
                f"; {unchecked_n} not checked ("
                + ", ".join(f"{k}: {v}" for k, v in sorted(unchecked_reasons.items()))
                + ")"
                if unchecked_n
                else ""
            )
        ),
        [str(lit_dir / "deduped.json")],
        (
            [str(lit_dir / "verified.json")]
            + (
                [str(lit_dir / _VERIFICATION_QUARANTINE_FILENAME)]
                if refused_entries
                else []
            )
            + ([str(lit_dir / CHECKS_FILENAME)] if unchecked_n or keep else [])
        ),
        {
            "preserved": preserved_n,
            "bridge_restored": bridge_restored_n,
            "refused": len(refused_entries),
            "verified": len(verified_docs),
            "refusal_reasons": _refusal_counts,
            "status": _verification_status,
            **(
                {
                    "unchecked": unchecked_n,
                    "unchecked_reasons": unchecked_reasons,
                    "paused": paused,
                    "stopped": stopped,
                    "checked_now": len(to_check),
                }
                if unchecked_n or keep
                else {}
            ),
        },
        status=_verification_status,
    )
    return VerificationOutcome(
        documents=verified_docs,
        status=_verification_status,
        verified=len(verified_docs),
        refused=len(refused_entries),
        preserved=preserved_n,
        bridge_restored=bridge_restored_n,
        refusal_reasons=_refusal_counts,
        quarantine=_quarantine_rel,
        unchecked=unchecked_n,
        unchecked_reasons=unchecked_reasons,
        paused=paused,
        stopped=stopped,
        checked=len(to_check),
    )
