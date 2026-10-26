"""``Envelope@1`` transport model (spec 02 §2).

The envelope is transport, not science: it describes what happened to a
request, never what a paper means. It wraps Contract v1 payloads opaquely and
never adds fields to, reinterprets, or downgrades them.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ENVELOPE_ID_RE = re.compile(r"^ENV-[0-9a-f]{16}$")


def check_sha256_hex(value: str) -> str:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError("sha256 must be 64 lowercase hex characters")
    return value


class EnvelopeStatus(StrEnum):
    """Closed status algebra (spec 02 §3). No free strings."""

    OK = "OK"
    PARTIAL = "PARTIAL"
    BLOCKED_INPUT = "BLOCKED_INPUT"
    BLOCKED_AMBIGUOUS_TASK = "BLOCKED_AMBIGUOUS_TASK"
    BLOCKED_CANONICAL_REPO = "BLOCKED_CANONICAL_REPO"
    BLOCKED_BASELINE_DRIFT = "BLOCKED_BASELINE_DRIFT"
    REFUSED = "REFUSED"
    PROVIDER_TRANSIENT = "PROVIDER_TRANSIENT"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    GATE_FAILED = "GATE_FAILED"


BLOCKED_STATUSES = frozenset(
    {
        EnvelopeStatus.BLOCKED_INPUT,
        EnvelopeStatus.BLOCKED_AMBIGUOUS_TASK,
        EnvelopeStatus.BLOCKED_CANONICAL_REPO,
        EnvelopeStatus.BLOCKED_BASELINE_DRIFT,
    }
)

#: Statuses whose `output` may be non-null.
PayloadStatuses = frozenset(
    {
        EnvelopeStatus.OK,
        EnvelopeStatus.PARTIAL,
        EnvelopeStatus.INVALID_OUTPUT,
    }
)

RefusalStatuses = frozenset(
    {
        EnvelopeStatus.BLOCKED_INPUT,
        EnvelopeStatus.BLOCKED_AMBIGUOUS_TASK,
        EnvelopeStatus.BLOCKED_CANONICAL_REPO,
        EnvelopeStatus.BLOCKED_BASELINE_DRIFT,
        EnvelopeStatus.REFUSED,
        EnvelopeStatus.PROVIDER_TRANSIENT,
        EnvelopeStatus.INVALID_OUTPUT,
        EnvelopeStatus.GATE_FAILED,
        # Resolved spec tension (decision record D2): the §3 table requires
        # PARTIAL to carry refusal codes naming the gap, so PARTIAL counts as
        # a refusal-bearing status; OK is the only refusal-free status.
        EnvelopeStatus.PARTIAL,
    }
)


class EnvelopeModel(BaseModel):
    """Envelope base: unknown fields are a defect, not a feature."""

    model_config = ConfigDict(extra="forbid")


class EnvelopeInputRef(EnvelopeModel):
    schema_: str = Field(min_length=1, alias="schema")
    path: str | None = None
    sha256: str
    role_version: str | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("sha256")
    @classmethod
    def content_hash(cls, value: str) -> str:
        return check_sha256_hex(value)


class EnvelopeParentRef(EnvelopeModel):
    artifact: str = Field(min_length=1)
    sha256: str

    @field_validator("sha256")
    @classmethod
    def content_hash(cls, value: str) -> str:
        return check_sha256_hex(value)


class EnvelopeCoverage(EnvelopeModel):
    expected: int = Field(ge=0)
    produced: int = Field(ge=0)
    unit: str = Field(min_length=1)


class EnvelopeRefusal(EnvelopeModel):
    code: str
    codes: list[str] = Field(default_factory=list)
    detail: str = Field(min_length=1)
    missing: list[str] | None = None
    unsupported: str | None = None
    alternatives: list[str] | None = None
    validation_findings: list[str] | None = None


class EnvelopeOutput(EnvelopeModel):
    schema_: str = Field(min_length=1, alias="schema")
    data: dict[str, Any]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EnvelopeProvenance(EnvelopeModel):
    adapter: Literal["opencode", "in-process"]
    adapter_version: str = Field(min_length=1)
    isolation: Literal["none", "directory", "redacted-input"]
    blinded_from: list[str] = Field(default_factory=list)
    duration_ms: int | None = None


class Envelope(EnvelopeModel):
    """``Envelope@1`` — the transport layer for every role boundary."""

    envelope: Literal[1]
    envelope_id: str
    role: str = Field(min_length=1)
    role_version: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    arm: Literal["A", "B"] | None = None
    created_at: datetime
    status: EnvelopeStatus
    retryable: bool
    human_action_required: bool
    refusal: EnvelopeRefusal | None = None
    coverage: EnvelopeCoverage | None = None
    inputs: list[EnvelopeInputRef] = Field(default_factory=list)
    parents: list[EnvelopeParentRef] = Field(default_factory=list)
    output: EnvelopeOutput | None = None
    output_sha256: str | None = None
    provenance: EnvelopeProvenance

    @field_validator("envelope_id")
    @classmethod
    def envelope_id_shape(cls, value: str) -> str:
        if _ENVELOPE_ID_RE.fullmatch(value) is None:
            raise ValueError(
                "envelope_id must be ENV-<16 lowercase hex> "
                "(deterministic envelope-id algorithm v1)"
            )
        return value

    @field_validator("created_at")
    @classmethod
    def utc_created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include an RFC3339 UTC offset")
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("created_at must be UTC")
        return value

    @field_validator("output_sha256")
    @classmethod
    def output_hash_shape(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return check_sha256_hex(value)

    @field_validator("role", "role_version", "task_id")
    @classmethod
    def no_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-blank string")
        return value
