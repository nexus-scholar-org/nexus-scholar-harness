"""Generated JSON Schema catalog for cross-kit contract v1."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from .identifiers import identifier_registry
from .models import (
    ArtifactEnvelope,
    ClaimEvidenceLedger,
    ContractError,
    CorpusSnapshotArtifact,
    DocumentManifestArtifact,
    OperationOutcome,
    RunManifest,
    ScreeningBatchArtifact,
    ScreeningDecisionsArtifact,
)

SCHEMA_BASE_URI = "https://nexus-scholar.org/schemas/contracts/v1"
SCHEMA_MODELS = {
    "artifact-envelope.schema.json": ArtifactEnvelope[dict[str, Any]],
    "claim-evidence-ledger.schema.json": ClaimEvidenceLedger,
    "contract-error.schema.json": ContractError,
    "corpus-snapshot.schema.json": CorpusSnapshotArtifact,
    "document-manifest.schema.json": DocumentManifestArtifact,
    "operation-outcome.schema.json": OperationOutcome[dict[str, Any]],
    "run-manifest.schema.json": RunManifest,
    "screening-batch.schema.json": ScreeningBatchArtifact,
    "screening-decisions.schema.json": ScreeningDecisionsArtifact,
}


def _schema_document(filename: str, model: type[Any]) -> dict[str, Any]:
    schema = model.model_json_schema(mode="validation")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE_URI}/{filename}",
        **schema,
    }


def render_schema_files() -> dict[str, str]:
    """Render every generated catalog file with deterministic formatting."""

    rendered = {
        filename: json.dumps(
            _schema_document(filename, model),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
        for filename, model in SCHEMA_MODELS.items()
    }
    rendered["identifier-registry.json"] = (
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": f"{SCHEMA_BASE_URI}/identifier-registry.json",
                "contract_version": "1.0.0",
                "identifiers": identifier_registry(),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    )
    return rendered


def schema_directory():
    """Return the importlib resource traversable containing v1 schemas."""

    return files("scholar_harness.contracts").joinpath("schemas", "v1")


def load_schema(filename: str) -> dict[str, Any]:
    """Load a bundled v1 JSON Schema or registry document by filename."""

    if filename not in render_schema_files():
        raise KeyError(f"unknown contract schema: {filename}")
    return json.loads(schema_directory().joinpath(filename).read_text(encoding="utf-8"))
