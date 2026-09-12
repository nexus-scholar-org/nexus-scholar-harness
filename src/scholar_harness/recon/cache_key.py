"""Hierarchical cache-key builder for the exploratory recon sandbox.

Key format (spec 04_memory_and_cache.md section 3)::

    v1/<providers>/y<year_min>-<year_max>/q/<sha256(normalized_text)>

* ``<providers>`` is a comma-joined, ordered provider list.
* ``y2015`` is used for a single-year window (year_min == year_max).
* The query text is normalized (case-fold, collapse whitespace, strip
  trailing punctuation) so equivalent phrasings share one cache address.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

VERSION = "v1"

_TRAILING_PUNCT = re.compile(r"[.,;:!?]+$")
_WHITESPACE = re.compile(r"\s+")


def _current_year() -> int:
    return datetime.now(UTC).year


def normalize_query(text: str) -> str:
    """Case-fold, collapse whitespace, and strip trailing punctuation."""
    if not text:
        return ""
    s = str(text).casefold()
    s = _WHITESPACE.sub(" ", s).strip()
    s = _TRAILING_PUNCT.sub("", s)
    return s.strip()


def _year_segment(year_min: int, year_max: int | None) -> str:
    if year_max is None:
        year_max = _current_year()
    if int(year_min) == int(year_max):
        return f"y{int(year_min)}"
    return f"y{int(year_min)}-{int(year_max)}"


def cache_key(
    query: str,
    providers: list[str],
    year_min: int,
    year_max: int | None = None,
    version: str = VERSION,
) -> str:
    """Build the hierarchical cache key for a probe."""
    normalized = normalize_query(query)
    provider_seg = ",".join(providers)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{version}/{provider_seg}/{_year_segment(year_min, year_max)}/q/{digest}"


def _parse_year_segment(segment: str) -> tuple[int, int]:
    if not segment.startswith("y"):
        raise ValueError(f"malformed year segment: {segment!r}")
    body = segment[1:]
    if "-" in body:
        low, high = body.split("-", 1)
        return int(low), int(high)
    year = int(body)
    return year, year


def parse_cache_key(key: str) -> dict[str, Any]:
    """Parse a cache key back into {version, providers, year_min, year_max, query_hash}."""
    parts = key.split("/")
    if len(parts) != 5 or parts[3] != "q":
        raise ValueError(f"malformed cache key: {key!r}")
    version, providers_seg, year_seg, _, query_hash = parts
    year_min, year_max = _parse_year_segment(year_seg)
    return {
        "version": version,
        "providers": providers_seg.split(","),
        "year_min": year_min,
        "year_max": year_max,
        "query_hash": query_hash,
    }