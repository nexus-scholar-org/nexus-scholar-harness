"""Neutral pipeline core (HCM-03).

Owns the reusable pipeline specification: models, validation, topological
scheduling, and fingerprinting. Dependency direction::

    pipeline_executor / integrations / console / CLI  ->  pipeline.*

``pipeline`` imports only stdlib and pydantic -- never console transport
(FastAPI), never kits. The console editor (``console.api.pipelines``) stays
the operator surface: it re-exports these names for backward-compatible
seams and retains only transport-owned concerns (HTTP endpoints, the
``.harness-console`` spec store, and the built-in gallery templates).
"""

from __future__ import annotations

from .fingerprint import _fingerprint
from .models import SCHEMA_VERSION, PipelineNode, PipelineSpec
from .validation import (
    _TEMPLATE_RE,
    _extract_template_keys,
    _lookup,
    _output_collisions,
    _toposort,
    validate_spec,
)

__all__ = [
    "SCHEMA_VERSION",
    "PipelineNode",
    "PipelineSpec",
    "_TEMPLATE_RE",
    "_extract_template_keys",
    "_fingerprint",
    "_lookup",
    "_output_collisions",
    "_toposort",
    "validate_spec",
]
