"""Claim-existence citation contract (``claims/v1``).

A separate, versioned machine-readable surface that makes a quantitative
claim impossible to assert without a verifiable artifact citation of the
form ``(artifact_id, path, locator, value)``.

This surface is deliberately NOT part of the frozen Contract v1 baseline
(``src/scholar_harness/contracts/``): it imports and reuses the v1
canonicalization and identifier registry but registers no model in the
frozen ``SCHEMA_MODELS`` catalog, so ``scripts/generate_contract_baseline.py
--check`` and ``scripts/generate_contract_schemas.py --check`` remain
byte-stable.  See ``docs/architecture/claim_existence_contract.md`` for the
prose specification and the deferred resolver/gate unit.
"""

from __future__ import annotations

from .citation import (
    CLAIM_CITATION_CONTRACT_VERSION,
    CLAIM_SURFACE,
    ClaimCitation,
    citation_canonical_bytes,
    citation_fingerprint,
    json_values_equal,
)
from .schema_catalog import (
    CLAIM_SCHEMA_BASE_URI,
    load_schema,
    render_schema_files,
    schema_directory,
)

__all__ = [
    "CLAIM_CITATION_CONTRACT_VERSION",
    "CLAIM_SCHEMA_BASE_URI",
    "CLAIM_SURFACE",
    "ClaimCitation",
    "citation_canonical_bytes",
    "citation_fingerprint",
    "json_values_equal",
    "load_schema",
    "render_schema_files",
    "schema_directory",
]
