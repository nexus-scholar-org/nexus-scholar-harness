"""``scholar_harness.contracts.envelope`` — the ``Envelope@1`` transport layer."""

from __future__ import annotations

from .api import (
    PAYLOAD_MODELS,
    EnvelopeDiff,
    EnvelopeRefusalError,
    diff,
    envelope_id,
    find_roles_dir,
    output_sha256,
    validate,
    verify_parents,
)
from .model import (
    Envelope,
    EnvelopeCoverage,
    EnvelopeInputRef,
    EnvelopeOutput,
    EnvelopeParentRef,
    EnvelopeProvenance,
    EnvelopeRefusal,
    EnvelopeStatus,
)
from .registry import ANY_EMITTER_CODES, RefusalCode, allowed_emitter_roles
from .schema import render_envelope_schema

__all__ = [
    "ANY_EMITTER_CODES",
    "PAYLOAD_MODELS",
    "Envelope",
    "EnvelopeCoverage",
    "EnvelopeDiff",
    "EnvelopeInputRef",
    "EnvelopeOutput",
    "EnvelopeParentRef",
    "EnvelopeProvenance",
    "EnvelopeRefusal",
    "EnvelopeRefusalError",
    "EnvelopeStatus",
    "RefusalCode",
    "allowed_emitter_roles",
    "diff",
    "envelope_id",
    "find_roles_dir",
    "output_sha256",
    "render_envelope_schema",
    "validate",
    "verify_parents",
]
