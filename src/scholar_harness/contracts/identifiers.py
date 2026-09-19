"""Canonical identifier registry for Nexus Scholar contract v1."""

from __future__ import annotations

import re
from enum import StrEnum


class IdentifierKind(StrEnum):
    """Semantically distinct identities that may cross package boundaries."""

    WORKSPACE = "workspace"
    PROTOCOL = "protocol"
    RUN = "run"
    CORPUS = "corpus"
    STUDY = "study"
    SOURCE_RECORD = "source_record"
    DOCUMENT = "document"
    CHUNK = "chunk"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    SCREENING_DECISION = "screening_decision"
    ARTIFACT = "artifact"
    AUDIT_EVENT = "audit_event"


ID_PREFIXES: dict[IdentifierKind, tuple[str, ...]] = {
    IdentifierKind.WORKSPACE: ("WSP-",),
    IdentifierKind.PROTOCOL: ("PRT-",),
    IdentifierKind.RUN: ("RUN-",),
    IdentifierKind.CORPUS: ("COR-",),
    # SCI-* is the registered legacy study-ID form and remains valid in v1.
    IdentifierKind.STUDY: ("STU-", "SCI-"),
    IdentifierKind.SOURCE_RECORD: ("REC-",),
    IdentifierKind.DOCUMENT: ("DOC-",),
    IdentifierKind.CHUNK: ("CHK-",),
    IdentifierKind.CLAIM: ("CLM-",),
    IdentifierKind.EVIDENCE: ("EV-",),
    IdentifierKind.SCREENING_DECISION: ("SCR-",),
    IdentifierKind.ARTIFACT: ("ART-",),
    IdentifierKind.AUDIT_EVENT: ("AUD-", "EVT-"),
}

_OPAQUE_SUFFIX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def primary_prefix(kind: IdentifierKind) -> str:
    """Return the prefix used when minting new identifiers of *kind*."""

    return ID_PREFIXES[kind][0]


def validate_identifier(kind: IdentifierKind, value: str) -> str:
    """Validate the semantic prefix and opaque suffix of a contract identifier."""

    if not isinstance(value, str):
        raise TypeError(f"{kind.value}_id must be a string")
    matching_prefix = next(
        (prefix for prefix in ID_PREFIXES[kind] if value.startswith(prefix)), None
    )
    if matching_prefix is None:
        expected = ", ".join(ID_PREFIXES[kind])
        raise ValueError(f"{kind.value}_id must start with one of: {expected}")
    suffix = value[len(matching_prefix) :]
    if not suffix or not _OPAQUE_SUFFIX.fullmatch(suffix):
        raise ValueError(f"{kind.value}_id has an invalid opaque suffix")
    return value


def identifier_registry() -> dict[str, dict[str, object]]:
    """Return a JSON-serializable registry used by schema/docs generation."""

    return {
        kind.value: {
            "prefixes": list(prefixes),
            "mint_prefix": prefixes[0],
            "legacy_prefixes": list(prefixes[1:]),
        }
        for kind, prefixes in ID_PREFIXES.items()
    }
