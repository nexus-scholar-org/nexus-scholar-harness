"""PipelineSpec models (HCM-03 neutral core).

Moved verbatim from ``console.api.pipelines``: ``PipelineSpec``
(``schema_version 0.1.0``) is pure data shared by the console editor, the
CLI executor, the shell-script exporter, and the job runner. No transport
or persistence behavior lives here.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator

SCHEMA_VERSION = "0.1.0"


class PipelineNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    kit: str
    command: list[str]
    args: dict[str, Any] = {}
    inputs: list[str] = []
    outputs: list[str] = []
    on_fail: Literal["abort", "skip", "continue"] = "abort"
    requires_decision: bool = False


class PipelineSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: str = SCHEMA_VERSION
    id: str
    archetype: str = "PRISMA_SLR"
    name: str = ""
    workspace_slug: str = ""
    settings: dict[str, Any] = {}
    nodes: list[PipelineNode]
    edges: list[list[str]] = []
    dry_run: dict[str, Any] = {}
    created_by: str = "console"
    fingerprint: str = ""

    @field_validator("schema_version")
    @classmethod
    def _schema_version(cls, v: str) -> str:
        if v != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {v!r}; expected {SCHEMA_VERSION!r}")
        return v

    @field_validator("edges")
    @classmethod
    def _edge_shape(cls, v: list[list[str]]) -> list[list[str]]:
        for edge in v:
            if not isinstance(edge, list) or len(edge) != 2 or not all(isinstance(x, str) and x for x in edge):
                raise ValueError(f"edges must be [from_id, to_id] pairs, got {edge!r}")
        return v
