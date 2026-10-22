"""Generated JSON Schema catalog for the claim-existence citation contract.

This is the ``claims/v1`` surface, deliberately separate from the frozen
Contract v1 catalog (``scholar_harness.contracts.schema_catalog``).  Adding
``ClaimCitation`` to the v1 ``SCHEMA_MODELS`` would move the frozen baseline
``docs/architecture/contract_v1_baseline.json`` and fail
``scripts/generate_contract_baseline.py --check``; the citation contract is
additive, versioned, and pinned under its own base URI instead.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from .citation import CLAIM_CITATION_CONTRACT_VERSION, ClaimCitation

CLAIM_SCHEMA_BASE_URI = "https://nexus-scholar.org/schemas/claims/v1"
CLAIM_SCHEMA_MODELS = {
    "claim-citation.schema.json": ClaimCitation,
}


def _schema_document(filename: str, model: type[Any]) -> dict[str, Any]:
    schema = model.model_json_schema(mode="validation")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{CLAIM_SCHEMA_BASE_URI}/{filename}",
        "contract_version": CLAIM_CITATION_CONTRACT_VERSION,
        **schema,
    }


def render_schema_files() -> dict[str, str]:
    """Render every generated claims/v1 schema file deterministically."""

    return {
        filename: json.dumps(
            _schema_document(filename, model),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
        for filename, model in CLAIM_SCHEMA_MODELS.items()
    }


def schema_directory():
    """Return the importlib resource traversable containing claims/v1 schemas."""

    return files("scholar_harness.claims").joinpath("schemas")


def load_schema(filename: str) -> dict[str, Any]:
    """Load a bundled claims/v1 JSON Schema by filename."""

    if filename not in render_schema_files():
        raise KeyError(f"unknown claim citation schema: {filename}")
    return json.loads(schema_directory().joinpath(filename).read_text(encoding="utf-8"))
