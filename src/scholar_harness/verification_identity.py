"""HCM-04e-1 bridge-or-refuse vocabulary (harness-owned, toolkit-free).

Option B policy: preserve a valid verifier-returned ``workspace_id``; restore
ONLY via a DOI bridge to a recorded dedup parent; otherwise refuse with a
typed, auditable reason. No ``SCI-`` mint, no inference, no downstream
publication of the refused row.

Why a new module instead of existing vocabulary:

* ``OperationStatus`` carries ``PARTIAL`` but no refusal code; a status alone
  cannot name the exact miss/changed/ambiguous reason honestly.
* ``PublicationRefused`` is extraction-producer scope and would force a
  circular import (``extraction_producer`` imports orchestrator helpers).
* ``RegisteredWorkspaceIdentityMissingError`` is ``WSP-`` workspace scope;
  reusing it for study/alias rows would conflate workspace and study identity,
  which the packet explicitly forbids.

So the smallest honest location is this tiny harness-owned module: stable
string codes, one typed exception mirroring the ``PublicationRefused`` shape,
and the deterministic DOI-bridge builder shared by both mint points
(``orchestrator`` Stage 3 and ``screening/collector``). It imports only the
standard library, so both sites can share it without cycles.
"""

from __future__ import annotations

from typing import Any

#: Verified row has no DOI, so there is no bridge key to a dedup parent.
VERIFICATION_IDENTITY_MISSING_DOI = "VERIFICATION_IDENTITY_MISSING_DOI"
#: Verified row carries a DOI, but no recorded dedup parent has that DOI
#: (changed/unmatched DOI; bridge miss).
VERIFICATION_IDENTITY_BRIDGE_MISS = "VERIFICATION_IDENTITY_BRIDGE_MISS"
#: Verified row carries a DOI that maps to more than one recorded dedup
#: parent; picking one would be inference, so the bridge is refused.
VERIFICATION_IDENTITY_AMBIGUOUS_DOI = "VERIFICATION_IDENTITY_AMBIGUOUS_DOI"

#: Quarantine filename for refused Stage-3 rows. Named in the HCM-04e
#: decision record (Option B): refused rows are never published to the
#: authoritative ``verified.json``; they are preserved here with their exact
#: refusal reason so the refusal is auditable post-hoc (closes VEI-10).
QUARANTINE_FILENAME = "verified_unresolved.json"

#: Stage-3 audit action for the bridge-or-refuse outcome. Emitted through the
#: established orchestrator legacy adapter so prior journal bytes are
#: preserved; the event status carries the observed outcome (never a
#: constant SUCCESS for a refused run).
AUDIT_ACTION = "VERIFICATION_IDENTITY_RESOLVED"


class VerificationIdentityRefused(RuntimeError):
    """Typed refusal to mint or publish an unidentified verification row.

    Mirrors the ``PublicationRefused`` shape (stable ``code``, human
    ``message``, machine-readable ``details``) so callers can branch on the
    failure. A subclass of ``RuntimeError`` so existing
    ``pytest.raises(RuntimeError)`` collector guards still catch it.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


def build_doi_bridge(docs_for_verify: Any) -> tuple[dict[str, str], set[str]]:
    """Build the DOI bridge from recorded dedup parents.

    Maps each normalized DOI to its single recorded ``workspace_id``. A DOI
    claimed by more than one dedup parent is ambiguous and is returned in the
    second element instead of a mapping, so the caller refuses rather than
    picking one (inference). Deterministic and order-independent: the singleton
    map and the ambiguous set do not depend on input order.

    Skips rows with a falsy DOI or a falsy ``workspace_id`` (they cannot serve
    as a bridge parent). DOI values are used as the kit normalized them
    (``ExternalIds.__post_init__`` lowercases/strips DOI and removes
    ``https://doi.org/``-style prefixes, which is what makes the bridge
    case/prefix-insensitive); this builder performs no re-normalization.
    """

    claimants: dict[str, set[str]] = {}
    for doc in docs_for_verify or []:
        external_ids = getattr(doc, "external_ids", None)
        doi = getattr(external_ids, "doi", None) if external_ids is not None else None
        wid = getattr(doc, "workspace_id", None)
        if not doi or not wid:
            continue
        claimants.setdefault(doi, set()).add(wid)

    singletons: dict[str, str] = {}
    ambiguous: set[str] = set()
    for doi, wsids in claimants.items():
        if len(wsids) == 1:
            singletons[doi] = next(iter(wsids))
        else:
            ambiguous.add(doi)
    return singletons, ambiguous
