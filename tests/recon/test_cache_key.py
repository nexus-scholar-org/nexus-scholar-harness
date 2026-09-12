"""Tests for the hierarchical recon cache-key builder (T0.2/T0.3)."""

import hashlib

from scholar_harness.recon import cache_key as exported_cache_key
from scholar_harness.recon.cache_key import cache_key, normalize_query, parse_cache_key


def test_normalization_casefold_whitespace_punctuation():
    assert normalize_query("Drones & AI.") == "drones & ai"
    assert normalize_query("  Drones   &  AI  ") == "drones & ai"
    assert normalize_query("drones & ai!") == "drones & ai"
    assert normalize_query("drones & ai???") == "drones & ai"


def test_same_query_same_key():
    a = cache_key("Drones & AI.", ["openalex"], 2020, 2026)
    b = cache_key("  drones   & ai ", ["openalex"], 2020, 2026)
    assert a == b
    digest = hashlib.sha256(b"drones & ai").hexdigest()
    assert a.endswith(f"/q/{digest}")
    assert a.startswith("v1/openalex/")
    assert "y2020-2026" in a


def test_provider_segment_changes_key():
    a = cache_key("drones", ["openalex"], 2020, 2026)
    b = cache_key("drones", ["openalex", "crossref"], 2020, 2026)
    c = cache_key("drones", ["arxiv"], 2020, 2026)
    assert len({a, b, c}) == 3


def test_year_segment_changes_key_and_single_year():
    a = cache_key("drones", ["openalex"], 2020, 2026)
    b = cache_key("drones", ["openalex"], 2015, 2026)
    assert a != b
    single = cache_key("drones", ["openalex"], 2015, 2015)
    assert "y2015" in single
    assert "y2015-2015" not in single


def test_parse_cache_key_roundtrip():
    key = cache_key("Drones & AI.", ["openalex", "arxiv"], 2015, 2026)
    parsed = parse_cache_key(key)
    assert parsed["version"] == "v1"
    assert parsed["providers"] == ["openalex", "arxiv"]
    assert parsed["year_min"] == 2015
    assert parsed["year_max"] == 2026
    digest = hashlib.sha256(b"drones & ai").hexdigest()
    assert parsed["query_hash"] == digest


def test_year_max_default_resolves():
    parsed = parse_cache_key(cache_key("drones", ["openalex"], 2000))
    assert parsed["year_min"] == 2000
    assert parsed["year_max"] is not None


def test_re_exported_cache_key_is_same_callable():
    assert exported_cache_key is cache_key