"""Claim-existence citation contract: ``(artifact_id, path, locator, value)``.

Motivation (docs/architecture/guideline_conformance_and_review_audit_2026-10-21.md
section 8.1): AGRIEVAL's reporting gate passed a meta-analysis that was never
executed because its statistics lived in ad-hoc scripts outside the harness.
This module freezes the *machine-readable citation* that makes a quantitative
claim impossible to assert without an artifact behind it.  It is a contract
only: the resolver/gate that checks citations against artifacts on disk and
the reporting-path wiring are deliberately deferred to a later unit.

Design decisions (full rationale in docs/architecture/claim_existence_contract.md):

- ``artifact_id`` reuses the frozen Contract v1 artifact identifier registry
  (``ART-`` prefix, opaque ``[A-Za-z0-9][A-Za-z0-9._-]*`` suffix).  A citation
  whose identity could not bind to a Contract v1 ``ArtifactEnvelope`` is
  precisely the failure class this surface prevents, so the registry's strict
  form is enforced: empty, whitespace-only, and ambiguous-identity strings are
  rejected at the model, not flagged later.
- ``path`` is a workspace-relative POSIX path in *canonical spelling*.  An
  escaping citation is invalid, not merely unresolvable, so absolute paths,
  Windows drive prefixes, backslashes, ``..`` segments, ``.`` segments,
  redundant/trailing separators, surrounding whitespace, and control
  characters are all rejected by the model validator.
- ``locator`` is an RFC 6901 JSON Pointer in its plain string form (no ``#``
  URI-fragment form).  It must start with ``/`` and ``~`` may appear only as
  part of a ``~0``/``~1`` escape.  JSON Pointer was chosen over page/section
  or regex schemes because it is standard, unambiguous, and deterministic to
  evaluate against parsed JSON artifacts.
- ``value`` is restricted to canonical-JSON-representable data (``null``,
  ``bool``, ``int``, finite ``float``, ``str``, lists, and string-keyed
  objects).  Functions, objects, sets, bytes, ``NaN``/``inf``, non-string
  object keys, and other unverifiable kinds are rejected at the model.  No
  ``value_type`` discriminator is added: the JSON type of ``value`` is already
  carried by the value itself, and the canonicalization below makes the type
  comparison rule total, so a discriminator would be redundant state that can
  drift from the value.
- The comparison rule is exact structural equality after the repo's single
  canonicalization (``contracts.canonical.canonical_json_bytes``): a claimed
  value matches an artifact value iff their canonical JSON bytes are equal.
  Number hazard: integral floats unify with ints (``1.0`` and ``1`` have the
  same canonical bytes), non-integral floats compare by exact binary value
  with no tolerance, and ``bool`` never equals an ``int`` (``true`` vs ``1``).
- ``extra="forbid"``: a citation is exactly the four fields; unknown fields
  are rejected rather than silently preserved.
"""

from __future__ import annotations

import math
import re
from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from ..contracts.canonical import canonical_fingerprint, canonical_json_bytes
from ..contracts.identifiers import IdentifierKind, validate_identifier

CLAIM_SURFACE = "claims/v1"
CLAIM_CITATION_CONTRACT_VERSION = "1.0.0"

_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")


def _validate_citation_path(value: str) -> str:
    """Validate a workspace-relative POSIX path in canonical spelling."""

    if not isinstance(value, str):
        raise TypeError("citation path must be a string")
    if not value:
        raise ValueError("citation path must not be empty")
    if "\\" in value:
        raise ValueError("citation path must be a POSIX path (no backslashes)")
    if _DRIVE_PREFIX_RE.match(value) or value.startswith("/"):
        raise ValueError(
            "citation path must be workspace-relative (no absolute or drive path)"
        )
    if any(ord(char) < 0x20 for char in value):
        raise ValueError("citation path must not contain control characters")
    if value.strip() != value:
        raise ValueError("citation path must not have surrounding whitespace")
    posix = PurePosixPath(value)
    if not posix.parts or ".." in posix.parts or posix.parts[0] == ".":
        raise ValueError("citation path must remain inside the workspace root")
    if str(posix) != value:
        raise ValueError(
            "citation path must be in canonical POSIX spelling "
            "(no '.', '//' or trailing '/')"
        )
    return value


def _validate_json_pointer(value: str) -> str:
    """Validate an RFC 6901 JSON Pointer in its plain string form."""

    if not isinstance(value, str):
        raise TypeError("citation locator must be a string")
    if not value.startswith("/"):
        raise ValueError(
            "citation locator must be an RFC 6901 JSON Pointer starting with '/'"
            " (URI-fragment form is not accepted)"
        )
    index = 0
    while index < len(value):
        if value[index] == "~":
            if index + 1 >= len(value) or value[index + 1] not in "01":
                raise ValueError('JSON Pointer escapes must be "~0" or "~1"')
            index += 2
            continue
        index += 1
    return value


def _validate_json_value(value: Any, *, at: str = "$") -> Any:
    """Validate that *value* is canonical-JSON-representable, recursively.

    Returns a normalized copy (tuples become lists, mappings become plain
    dicts) so equal content is structurally identical regardless of the
    Python container types used to construct it.
    """

    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"citation value at {at} must not be NaN or infinity")
        return value
    if isinstance(value, (list, tuple)):
        return [
            _validate_json_value(item, at=f"{at}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        # ValueError (not TypeError) so pydantic converts it into a
        # ValidationError at the model boundary; pydantic 2 does not wrap
        # TypeError raised inside validators.
        non_string_keys = [key for key in value if not isinstance(key, str)]
        if non_string_keys:
            raise ValueError(
                f"citation value object keys at {at} must be strings: "
                f"{non_string_keys!r}"
            )
        return {
            key: _validate_json_value(item, at=f"{at}.{key}")
            for key, item in value.items()
        }
    raise ValueError(
        f"citation value at {at} contains non-JSON type {type(value).__name__}"
    )


class ClaimCitation(BaseModel):
    """A machine-readable citation binding a quantitative claim to an artifact."""

    model_config = ConfigDict(extra="forbid", strict=True)

    artifact_id: str
    path: str
    locator: str
    value: Any

    @field_validator("artifact_id")
    @classmethod
    def artifact_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.ARTIFACT, value)

    @field_validator("path")
    @classmethod
    def contained_workspace_path(cls, value: str) -> str:
        return _validate_citation_path(value)

    @field_validator("locator")
    @classmethod
    def deterministic_pointer(cls, value: str) -> str:
        return _validate_json_pointer(value)

    @field_validator("value", mode="before")
    @classmethod
    def verifiable_value(cls, value: Any) -> Any:
        return _validate_json_value(value)


def citation_canonical_bytes(citation: ClaimCitation) -> bytes:
    """Serialize a citation with the repo's one canonical JSON function."""

    if not isinstance(citation, ClaimCitation):
        raise TypeError("citation must be a ClaimCitation")
    return canonical_json_bytes(citation.model_dump(mode="json"))


def citation_fingerprint(citation: ClaimCitation) -> str:
    """Return the ``sha256:<hex>`` fingerprint of a citation's canonical bytes."""

    if not isinstance(citation, ClaimCitation):
        raise TypeError("citation must be a ClaimCitation")
    return canonical_fingerprint(citation.model_dump(mode="json"))


def json_values_equal(claimed: Any, artifact_value: Any) -> bool:
    """Compare two JSON values under the claims/v1 comparison rule.

    Exact structural equality after canonical JSON serialization: two values
    match iff their canonical bytes are equal.  Integral floats unify with
    ints, ``bool`` never equals an ``int``, and no numeric tolerance is
    applied.  Raises ``ValueError`` for values that are not
    canonical-JSON-representable (a programming error, never a silent
    mismatch).
    """

    left = _validate_json_value(claimed, at="claimed")
    right = _validate_json_value(artifact_value, at="artifact_value")
    return canonical_json_bytes(left) == canonical_json_bytes(right)
