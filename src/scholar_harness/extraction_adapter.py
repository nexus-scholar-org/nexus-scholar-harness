"""Bounded WP01-E2 harness adapter for the PDF kit's extraction candidate.

Packet E2 (``docs/architecture/wp01_packet_e2_extracted_text_handoff.md`` §8.3)
allocates exactly one harness-side surface for extraction acceptance: a bounded
adapter under ``src/scholar_harness/`` that "invokes the PDF kit, parses its
candidate as the frozen ``DocumentManifestArtifact``, calls ``accept_artifact``,
and returns the accepted reference". This module is that surface, and nothing
else in the harness may take its place.

Why the boundary exists
-----------------------
The canonical ``scholar-pdf-kit`` constructs a deterministic
``document_manifest`` **candidate** (``scholar_pdf.contract_candidate``) and
stamps it ``contract_acceptance == "not_performed_by_kit"``. A candidate is a
payload, not an artifact: it is non-authoritative until a harness caller runs it
through the frozen acceptance gate, and only then does an ``artifact_id`` +
``published_path`` pair exist that a caller may cite as accepted. This module is
the *only* harness surface allowed to expose such an accepted reference, so a
caller cannot obtain an "accepted extraction artifact" by any other route.

What this module deliberately does not do
-----------------------------------------
* It performs **no Contract registry mutation of its own**. Every registry write,
  ``artifacts/<type>/<id>.json`` publication, audit append, idempotency decision,
  and rejection record is the frozen gate's job; this module routes every
  mutation through :func:`scholar_harness.contracts.acceptance.accept_artifact`
  and returns its :class:`~scholar_harness.contracts.acceptance.AcceptanceResult`
  verbatim. A new write path here would be a second, unfrozen acceptance gate.
* It imports the frozen Contract v1 model and acceptance module **read-only** and
  never edits them. ``src/scholar_harness/contracts/`` is frozen by §8.4 (no
  ``models.py``, ``acceptance.py``, ``chain.py``, identifier registry, generated
  schema, golden fixture, or baseline change), and no adapter convenience may
  weaken a frozen property check.
* It re-implements no extraction behavior. Engine selection, content-status
  truthfulness, fallback recording, sidecar commit, and the E1 re-verification of
  source bytes live in the canonical PDF kit and are proven by that kit's own
  suite (§10.1.7 / §14.1: a green harness suite is *not* evidence that extraction
  works). This module only parses and accepts.
* It performs no I/O of its own beyond forwarding the caller's workspace
  ``Path`` to the frozen gate. It does not read the candidate from a file, does
  not write an artifact, and does not append an audit event itself.

Ordering guarantee
------------------
:func:`accept_extraction_candidate` parses the payload through the frozen
``DocumentManifestArtifact`` model *before* delegating, so a payload that the
frozen model would reject raises :class:`pydantic.ValidationError` here instead
of being silently downgraded to an acceptance-level rejection code. A caller
therefore never receives an ``AcceptanceResult`` for a payload the frozen model
does not recognise as a ``document_manifest``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from scholar_harness.contracts.acceptance import (
    AcceptanceContext,
    AcceptanceResult,
    accept_artifact,
)
from scholar_harness.contracts.models import DocumentManifestArtifact

__all__ = [
    "accept_extraction_candidate",
    "parse_extraction_candidate",
]

#: Default audit actor recorded by the frozen gate when this adapter accepts or
#: rejects an extraction candidate. Distinct from the frozen gate's own default
#: so an ``audit/journal.jsonl`` line can be attributed to this adapter. Private:
#: the packet's public surface for this module is exactly the two functions in
#: ``__all__``.
_DEFAULT_ADAPTER_ACTOR = "scholar-harness-extraction-adapter"


def _as_mapping(
    payload: Mapping[str, object] | str | bytes,
) -> Mapping[str, object]:
    """Return ``payload`` as a JSON object, decoding text/bytes first.

    ``accept_artifact`` accepts a mapping, a JSON string, or JSON bytes; the
    frozen pydantic model accepts an object. This is the only decoding the
    adapter does, and it never inspects or relaxes the decoded content.
    """

    if isinstance(payload, Mapping):
        return payload
    if isinstance(payload, (str, bytes, bytearray)):
        loaded = json.loads(payload)
        if not isinstance(loaded, dict):
            raise TypeError("extraction candidate payload must be a JSON object")
        return loaded
    raise TypeError("extraction candidate payload must be a mapping, str, or bytes")


def parse_extraction_candidate(
    payload: Mapping[str, object] | str | bytes,
) -> DocumentManifestArtifact:
    """Parse a PDF-kit extraction candidate through the frozen Contract v1 model.

    This is the packet's "parses its candidate as the frozen
    ``DocumentManifestArtifact``" step (§8.3, §6.5). The frozen model is used
    unmodified, so ``artifact_type`` must be exactly ``document_manifest``,
    ``DocumentManifestData.documents`` must be non-empty with unique ids, and
    ``VALID``/``PARTIAL`` records must carry a workspace-relative
    ``extracted_path`` (``models.py:503-510``).

    Raises
    ------
    pydantic.ValidationError
        If the payload is not a JSON object or does not satisfy the frozen
        ``DocumentManifestArtifact`` shape. A rejection here is *not* softened
        into an acceptance-level issue code.
    TypeError
        If the payload is neither a mapping nor JSON text/bytes.
    """

    return DocumentManifestArtifact.model_validate(_as_mapping(payload))


def accept_extraction_candidate(
    workspace: Path,
    payload: Mapping[str, object] | str | bytes,
    *,
    expected: AcceptanceContext,
    actor: str = _DEFAULT_ADAPTER_ACTOR,
) -> AcceptanceResult:
    """Accept a PDF-kit extraction candidate and return the accepted reference.

    Calls :func:`parse_extraction_candidate` first (the explicit frozen-model
    gate), then delegates the whole acceptance decision to the frozen
    :func:`~scholar_harness.contracts.acceptance.accept_artifact` with the
    caller's trusted :class:`AcceptanceContext` -- the workspace, protocol, and
    corpus fingerprints must come from workspace state, never from the candidate
    itself.

    The returned :class:`AcceptanceResult` is the *sole* carrier of an accepted
    extraction reference: ``accepted``, ``artifact_id``, ``published_path``, and
    ``event_id`` describe a registry-backed artifact, while ``accepted=False``
    with ``issues`` and no ``published_path`` is a rejection that published
    nothing and fabricated no registry entry. ``idempotent=True`` marks an exact
    replay of an already-accepted payload.
    """

    # Frozen-model gate first: a payload the frozen model would reject must not
    # reach the gate as if it were merely an acceptance-level rejection.
    parse_extraction_candidate(payload)
    return accept_artifact(workspace, payload, expected=expected, actor=actor)
