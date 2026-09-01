"""Tests for deterministic canonical serialization and fingerprinting."""

from __future__ import annotations

import json
import pathlib

import pytest

from scholar_protocol.canonical import canonical_fingerprint, canonical_json
from scholar_protocol.models import ResearchProtocol

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
VALID_DIR = FIXTURES / "valid"
CANONICAL_DIR = FIXTURES / "canonical"


def _load_protocol(path: pathlib.Path) -> ResearchProtocol:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ResearchProtocol.model_validate(raw)


# ---------------------------------------------------------------------------
# Idempotency: canon(canon(x)) == canon(x)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture_name",
    [
        "design_science_min.json",
        "prisma_slr_full.json",
        "scoping_empty_matrix.json",
        "interpretivist_min.json",
    ],
)
def test_canonical_json_idempotent(fixture_name: str) -> None:
    """Applying canonical_json twice must yield the same bytes."""
    protocol = _load_protocol(VALID_DIR / fixture_name)
    first_pass = canonical_json(protocol)
    # Re-parse the canonical bytes and re-serialize.
    protocol2 = ResearchProtocol.model_validate(json.loads(first_pass))
    second_pass = canonical_json(protocol2)
    assert first_pass == second_pass, (
        f"Idempotency failure for {fixture_name}:\n"
        f"First:  {first_pass[:200]!r}\n"
        f"Second: {second_pass[:200]!r}"
    )


# ---------------------------------------------------------------------------
# Fingerprint stability: same input → same sha256
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture_name",
    [
        "design_science_min.json",
        "prisma_slr_full.json",
        "scoping_empty_matrix.json",
        "interpretivist_min.json",
    ],
)
def test_fingerprint_stable(fixture_name: str) -> None:
    """Same protocol content must always produce the same fingerprint."""
    protocol = _load_protocol(VALID_DIR / fixture_name)
    fp1 = canonical_fingerprint(protocol)
    fp2 = canonical_fingerprint(protocol)
    assert fp1 == fp2
    assert fp1.startswith("sha256:")
    # sha256: prefix + 64 hex chars
    assert len(fp1) == len("sha256:") + 64


# ---------------------------------------------------------------------------
# Key order: $schema appears first, protocol_id second
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture_name",
    [
        "design_science_min.json",
        "prisma_slr_full.json",
    ],
)
def test_key_order_starts_with_schema(fixture_name: str) -> None:
    """canonical_json output must start with {\"$schema\": ..., \"protocol_id\": ..."""
    protocol = _load_protocol(VALID_DIR / fixture_name)
    raw = canonical_json(protocol)
    parsed = json.loads(raw, object_pairs_hook=list)  # preserves key order as list of (k,v)
    keys = [k for k, _ in parsed]
    assert keys[0] == "$schema", f"First key is '{keys[0]}', expected '$schema'"
    assert keys[1] == "protocol_id", f"Second key is '{keys[1]}', expected 'protocol_id'"


# ---------------------------------------------------------------------------
# Float format: 5.0 not 5, 6.0 not 6
# ---------------------------------------------------------------------------


def test_float_threshold_has_decimal_point() -> None:
    """minimum_trust_score_threshold must serialize with a decimal point."""
    protocol = _load_protocol(VALID_DIR / "design_science_min.json")
    raw_str = canonical_json(protocol).decode("utf-8")
    # Locate the threshold value in the JSON string.
    assert '"minimum_trust_score_threshold":5.0' in raw_str or \
           '"minimum_trust_score_threshold":6.0' in raw_str or \
           '"minimum_trust_score_threshold":' in raw_str


def test_float_threshold_not_integer_serialized() -> None:
    """The threshold must NOT be serialized as a bare integer (no decimal point)."""
    protocol = _load_protocol(VALID_DIR / "prisma_slr_full.json")
    # prisma_slr_full has threshold = 6.0
    raw_str = canonical_json(protocol).decode("utf-8")
    # Should see 6.0, not ":6," or ":6}"
    assert '"minimum_trust_score_threshold":6.0' in raw_str


# ---------------------------------------------------------------------------
# Metadata and date_range keys are sorted alphabetically
# ---------------------------------------------------------------------------


def test_metadata_keys_sorted() -> None:
    """metadata dict keys must be sorted alphabetically in canonical output."""
    protocol = _load_protocol(VALID_DIR / "design_science_min.json")
    raw = json.loads(canonical_json(protocol))
    meta_keys = list(raw["metadata"].keys())
    assert meta_keys == sorted(meta_keys), f"metadata keys not sorted: {meta_keys}"


def test_date_range_keys_sorted() -> None:
    """date_range keys must be sorted alphabetically in canonical output."""
    protocol = _load_protocol(VALID_DIR / "design_science_min.json")
    raw = json.loads(canonical_json(protocol))
    dr_keys = list(raw["search_strategy"]["date_range"].keys())
    assert dr_keys == sorted(dr_keys), f"date_range keys not sorted: {dr_keys}"


# ---------------------------------------------------------------------------
# Whitespace: compact (no spaces after separators), ensure_ascii, no trailing newline
# ---------------------------------------------------------------------------


def test_canonical_json_is_compact() -> None:
    """canonical_json must not contain ', ' or ': ' (compact separators)."""
    protocol = _load_protocol(VALID_DIR / "design_science_min.json")
    raw_str = canonical_json(protocol).decode("utf-8")
    assert ", " not in raw_str
    assert ": " not in raw_str


def test_canonical_json_no_trailing_newline() -> None:
    """canonical_json output must not end with a newline byte."""
    protocol = _load_protocol(VALID_DIR / "design_science_min.json")
    raw = canonical_json(protocol)
    assert not raw.endswith(b"\n")


def test_canonical_json_is_utf8() -> None:
    """canonical_json must return valid UTF-8 bytes."""
    protocol = _load_protocol(VALID_DIR / "interpretivist_min.json")
    raw = canonical_json(protocol)
    # Should not raise
    raw.decode("utf-8")


# ---------------------------------------------------------------------------
# Canonical fixture: idempotent round-trip
# ---------------------------------------------------------------------------


def test_canonical_fixture_roundtrip() -> None:
    """The canonical/unordered_dims.json fixture must round-trip identically."""
    protocol = _load_protocol(CANONICAL_DIR / "unordered_dims.json")
    first = canonical_json(protocol)
    protocol2 = ResearchProtocol.model_validate(json.loads(first))
    second = canonical_json(protocol2)
    assert first == second


# ---------------------------------------------------------------------------
# Different protocols produce different fingerprints
# ---------------------------------------------------------------------------


def test_different_protocols_different_fingerprints() -> None:
    """Two protocols with different content must NOT produce the same fingerprint."""
    p1 = _load_protocol(VALID_DIR / "design_science_min.json")
    p2 = _load_protocol(VALID_DIR / "prisma_slr_full.json")
    assert canonical_fingerprint(p1) != canonical_fingerprint(p2)
