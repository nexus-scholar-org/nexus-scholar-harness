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
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scholar_search.verifier import DocumentVerifier

from scholar_harness.verification_identity import (
    AUDIT_ACTION as _VERIFICATION_AUDIT_ACTION,
    QUARANTINE_FILENAME as _VERIFICATION_QUARANTINE_FILENAME,
    VERIFICATION_IDENTITY_AMBIGUOUS_DOI,
    VERIFICATION_IDENTITY_BRIDGE_MISS,
    VERIFICATION_IDENTITY_MISSING_DOI,
    build_doi_bridge,
)
from scholar_harness.workspace.audit import append_legacy_event

logger = logging.getLogger(__name__)


# Kit class captured at import time so the legacy orchestrator-namespace seam
# below can tell a monkeypatched fake apart from the real verifier.
_REAL_VERIFIER = DocumentVerifier


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


def _verifier_class() -> type[DocumentVerifier]:
    """Return the ``DocumentVerifier`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.DocumentVerifier`` with a fake verifier. The
    orchestrator no longer constructs the verifier itself, so the stage honors
    an orchestrator-namespace override when it differs from the kit class and
    otherwise uses this module's own global (which tests may also patch
    directly). Transitional HCM-04e seam: a later coordinator packet should
    migrate the fidelity stubs to patch
    ``scholar_harness.pipeline.verification.DocumentVerifier`` directly and
    drop the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("DocumentVerifier")
        if candidate is not None and candidate is not _REAL_VERIFIER:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return DocumentVerifier


async def run_verification(
    *,
    documents: list[Any],
    literature_dir: Path | str,
    workspace_dir: Path | str,
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
    """
    lit_dir = Path(literature_dir)
    lit_dir.mkdir(parents=True, exist_ok=True)

    verifier = _verifier_class()()
    verified_docs, audit = await verifier.process_batch(
        documents, verify=True, enrich=True
    )

    wsid_by_doi, ambiguous_dois = build_doi_bridge(documents)
    identified_docs: list[Any] = []
    refused_entries: list[dict[str, Any]] = []
    preserved_n = 0
    bridge_restored_n = 0
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
            vd.workspace_id = wsid_by_doi[_doi]
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
        ),
        [str(lit_dir / "deduped.json")],
        (
            [str(lit_dir / "verified.json")]
            + (
                [str(lit_dir / _VERIFICATION_QUARANTINE_FILENAME)]
                if refused_entries
                else []
            )
        ),
        {
            "preserved": preserved_n,
            "bridge_restored": bridge_restored_n,
            "refused": len(refused_entries),
            "verified": len(verified_docs),
            "refusal_reasons": _refusal_counts,
            "status": _verification_status,
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
    )
