"""``scholar_harness.contracts.confirmation`` — the ``HumanConfirmation@1`` payload."""

from __future__ import annotations

from .api import (
    ConfirmationRefusalError,
    discover_decision_artifacts,
    enforce_coverage,
    validate,
    verify_artifacts,
)
from .model import (
    SCHEMA_NAME,
    ArtifactRef,
    ConfirmationModel,
    ConfirmationProvenance,
    ConfirmationSummary,
    DecisionRow,
    HumanConfirmation,
    Reviewer,
)
from .schema import (
    SCHEMA_BASE_URI,
    SCHEMA_FILENAME,
    render_confirmation_schema,
)

__all__ = [
    "ArtifactRef",
    "ConfirmationModel",
    "ConfirmationProvenance",
    "ConfirmationRefusalError",
    "ConfirmationSummary",
    "DecisionRow",
    "HumanConfirmation",
    "Reviewer",
    "SCHEMA_BASE_URI",
    "SCHEMA_FILENAME",
    "SCHEMA_NAME",
    "discover_decision_artifacts",
    "enforce_coverage",
    "render_confirmation_schema",
    "validate",
    "verify_artifacts",
]
