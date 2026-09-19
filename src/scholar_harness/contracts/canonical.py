"""Canonical JSON, fingerprints, deterministic IDs, and DOI normalization."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping
from typing import Any

from .identifiers import IdentifierKind, primary_prefix

_DOI_PREFIX = re.compile(
    r"^(?:doi\s*:\s*|https?://(?:dx\.)?doi\.org/)", re.IGNORECASE
)


def normalize_doi(value: str) -> str:
    """Normalize a DOI for comparison without replacing the stored original."""

    if not isinstance(value, str):
        raise TypeError("DOI must be a string")
    normalized = value.strip()
    while True:
        stripped = _DOI_PREFIX.sub("", normalized, count=1).strip()
        if stripped == normalized:
            break
        normalized = stripped
    if not normalized:
        raise ValueError("DOI is empty after normalization")
    return normalized.lower()


def _pointer(path: tuple[str, ...]) -> str:
    if not path:
        return ""
    escaped = (part.replace("~", "~0").replace("/", "~1") for part in path)
    return "/" + "/".join(escaped)


def _normalize_json(
    value: Any,
    *,
    path: tuple[str, ...],
    set_like_arrays: frozenset[str],
) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON rejects NaN and infinity")
        if value == 0:
            return 0
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, Mapping):
        non_string_keys = [key for key in value if not isinstance(key, str)]
        if non_string_keys:
            raise TypeError("canonical JSON object keys must be strings")
        return {
            key: _normalize_json(
                child,
                path=(*path, key),
                set_like_arrays=set_like_arrays,
            )
            for key, child in value.items()
        }
    if isinstance(value, (list, tuple)):
        normalized = [
            _normalize_json(
                child,
                path=(*path, str(index)),
                set_like_arrays=set_like_arrays,
            )
            for index, child in enumerate(value)
        ]
        if _pointer(path) in set_like_arrays:
            normalized.sort(
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
        return normalized
    raise TypeError(f"unsupported canonical JSON type: {type(value).__name__}")


def canonical_json_bytes(
    value: Any, *, set_like_arrays: Iterable[str] = ()
) -> bytes:
    """Serialize JSON-compatible data deterministically.

    Object keys are sorted, insignificant whitespace is removed, integral
    floats are normalized to integers, and array order remains semantic unless
    the caller explicitly registers that array's JSON pointer as set-like.
    """

    normalized = _normalize_json(
        value,
        path=(),
        set_like_arrays=frozenset(set_like_arrays),
    )
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_fingerprint(
    value: Any, *, set_like_arrays: Iterable[str] = ()
) -> str:
    """Return a ``sha256:<hex>`` fingerprint of canonical JSON data."""

    digest = hashlib.sha256(
        canonical_json_bytes(value, set_like_arrays=set_like_arrays)
    ).hexdigest()
    return f"sha256:{digest}"


def corpus_snapshot_fingerprint(value: Any) -> str:
    """Fingerprint corpus identity independent of incidental collection order."""

    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if not isinstance(value, Mapping):
        raise TypeError("corpus snapshot data must be a mapping or Pydantic model")
    studies = value.get("studies")
    record_to_study = value.get("record_to_study")
    if not isinstance(studies, list) or not isinstance(record_to_study, Mapping):
        raise TypeError("corpus snapshot requires studies and record_to_study")

    normalized_studies: list[dict[str, Any]] = []
    for study in studies:
        if not isinstance(study, Mapping):
            raise TypeError("each corpus study must be a mapping")
        external_ids = study.get("external_ids", {})
        if not isinstance(external_ids, Mapping):
            raise TypeError("study external_ids must be a mapping")
        normalized_studies.append(
            {
                **study,
                "source_record_ids": sorted(study.get("source_record_ids", [])),
                "alias_ids": sorted(study.get("alias_ids", [])),
                "external_ids": {
                    provider: sorted(values)
                    for provider, values in external_ids.items()
                },
            }
        )
    normalized_studies.sort(key=lambda study: study["study_id"])
    normalized = {
        **value,
        "studies": normalized_studies,
        "record_to_study": dict(record_to_study),
    }
    return canonical_fingerprint(normalized)


def deterministic_id(
    kind: IdentifierKind,
    workspace_namespace: str,
    canonical_input: Any,
    *,
    algorithm_version: str = "v1",
) -> str:
    """Mint a stable opaque ID from semantic kind, namespace, and input."""

    payload = {
        "algorithm_version": algorithm_version,
        "kind": kind.value,
        "workspace_namespace": workspace_namespace,
        "input": canonical_input,
    }
    suffix = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()[:32]
    return f"{primary_prefix(kind)}{suffix}"
