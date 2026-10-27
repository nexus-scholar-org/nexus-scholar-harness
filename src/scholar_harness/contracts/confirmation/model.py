"""``HumanConfirmation@1`` payload model (spec ``06_human_confirmation.md`` §2).

A confirmation binds a *named* customer reviewer to the exact bytes of every
decision artifact present under ``literature/screening/`` at sign time, plus
row-level honesty: ``changed`` rows carry reasons, ``deferred`` rows are
first-class, and ``confirmed`` rows carry no amendments.

The model enforces *shape only* (types, non-blank strings, hash format, closed
vocabularies). The §2/§5 semantic invariants (counts, rationale pricing,
disjoint amendment data, unique study ids) live in the invariant step of
``api.py`` so every defect surfaces through one named-refusal path.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_NAME = "HumanConfirmation@1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def check_sha256_hex(value: str) -> str:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError("sha256 must be 64 lowercase hex characters")
    return value


class ConfirmationModel(BaseModel):
    """Base: unknown fields are a defect, not a feature (envelope convention)."""

    model_config = ConfigDict(extra="forbid")


class Reviewer(ConfirmationModel):
    """The named person who reviewed the artifacts (spec `06` owner decision)."""

    name: str = Field(min_length=1)
    affiliation: str = Field(min_length=1)
    signing_capacity: Literal["lead_reviewer"]

    @field_validator("name", "affiliation")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-blank string")
        return value


class ArtifactRef(ConfirmationModel):
    """One decision artifact the reviewer saw, hashed over its raw bytes."""

    path: str = Field(min_length=1)
    sha256: str
    label: str = Field(min_length=1)

    @field_validator("sha256")
    @classmethod
    def content_hash(cls, value: str) -> str:
        return check_sha256_hex(value)

    @field_validator("path", "label")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-blank string")
        return value


class DecisionRow(ConfirmationModel):
    """One study-level judgement: confirmed, changed, or deferred."""

    study_id: str = Field(min_length=1)
    verdict: Literal["confirmed", "changed", "deferred"]
    amended: str | None = None
    rationale: str | None = None
    defer_reason: str | None = None

    @field_validator("study_id")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-blank string")
        return value


class ConfirmationSummary(ConfirmationModel):
    """Counts over ``decisions``; the invariant step ties them to the rows."""

    considered: int = Field(ge=0)
    confirmed: int = Field(ge=0)
    changed: int = Field(ge=0)
    deferred: int = Field(ge=0)


class ConfirmationProvenance(ConfirmationModel):
    """Tool provenance; ``created_at`` is timing metadata, never identity."""

    tool: str = Field(min_length=1)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include an RFC3339 UTC offset")
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("created_at must be UTC")
        return value


class HumanConfirmation(ConfirmationModel):
    """``HumanConfirmation@1`` — "who decided this?", answered with bytes."""

    schema_: Literal[SCHEMA_NAME] = Field(SCHEMA_NAME, alias="schema")
    retrospective: bool = False
    reviewer: Reviewer
    artifacts: list[ArtifactRef] = Field(min_length=1)
    decisions: list[DecisionRow]
    summary: ConfirmationSummary
    provenance: ConfirmationProvenance

    model_config = ConfigDict(extra="forbid", populate_by_name=True)
