"""Regression tests for the claims/v1 claim-existence citation contract.

Positive path: golden fixtures pin the canonical bytes of one valid citation
and of two citations that differ only in ways that MUST change the bytes.
Negative path: every one of the four fields has model-level rejection tests
(an invalid citation never becomes a valid object that is flagged later).
Determinism: the canonical-serialization path is executed repeatedly in-test
and must yield byte-identical output for equal content.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from scholar_harness.claims import (
    CLAIM_SCHEMA_BASE_URI,
    ClaimCitation,
    citation_canonical_bytes,
    citation_fingerprint,
    json_values_equal,
    load_schema,
    render_schema_files,
)
from scholar_harness.contracts.schema_catalog import (
    SCHEMA_BASE_URI as V1_SCHEMA_BASE_URI,
)
from scholar_harness.contracts.schema_catalog import (
    SCHEMA_MODELS as V1_SCHEMA_MODELS,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "claim_citation"

VALID_SOURCE = {
    "artifact_id": "ART-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",
    "path": "synthesis/meta_analysis.json",
    "locator": "/results/pooled_effect/risk_ratio",
    "value": 1.42,
}


def _citation(**overrides) -> ClaimCitation:
    payload = {**VALID_SOURCE, **overrides}
    return ClaimCitation.model_validate(payload)


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURE_DIR / name).read_bytes()


# ---------------------------------------------------------------------------
# Positive path and golden fixtures
# ---------------------------------------------------------------------------


def test_valid_citation_fields_are_preserved():
    citation = _citation()
    assert citation.artifact_id == VALID_SOURCE["artifact_id"]
    assert citation.path == VALID_SOURCE["path"]
    assert citation.locator == VALID_SOURCE["locator"]
    assert citation.value == VALID_SOURCE["value"]


def test_canonical_bytes_match_golden_fixture():
    assert citation_canonical_bytes(_citation()) == _fixture_bytes(
        "valid_citation.canonical.json"
    )


def test_source_fixture_parses_to_the_golden_citation():
    source = json.loads(_fixture_bytes("valid_citation.json"))
    assert citation_canonical_bytes(ClaimCitation.model_validate(source)) == (
        _fixture_bytes("valid_citation.canonical.json")
    )


def test_value_shift_must_change_canonical_bytes():
    shifted = citation_canonical_bytes(_citation(value=1.43))
    golden = _fixture_bytes("valid_citation.canonical.json")
    assert shifted == _fixture_bytes("value_shifted_citation.canonical.json")
    assert shifted != golden


def test_locator_shift_must_change_canonical_bytes():
    shifted = citation_canonical_bytes(
        _citation(locator="/results/pooled_effect/odds_ratio")
    )
    golden = _fixture_bytes("valid_citation.canonical.json")
    assert shifted == _fixture_bytes("locator_shifted_citation.canonical.json")
    assert shifted != golden


# ---------------------------------------------------------------------------
# Determinism and canonicalization identity
# ---------------------------------------------------------------------------


def test_canonicalization_is_deterministic_across_calls_and_instances():
    first = citation_canonical_bytes(_citation())
    for _ in range(3):
        assert citation_canonical_bytes(_citation()) == first


def test_canonicalization_is_content_based_not_identity_based():
    golden = _fixture_bytes("valid_citation.canonical.json")
    rekeyed = ClaimCitation.model_validate(
        {
            "value": 1.42,
            "locator": "/results/pooled_effect/risk_ratio",
            "path": "synthesis/meta_analysis.json",
            "artifact_id": "ART-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",
        }
    )
    via_kwargs = ClaimCitation(
        artifact_id="ART-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",
        value=1.42,
        path="synthesis/meta_analysis.json",
        locator="/results/pooled_effect/risk_ratio",
    )
    assert citation_canonical_bytes(rekeyed) == golden
    assert citation_canonical_bytes(via_kwargs) == golden
    assert citation_canonical_bytes(_citation()) == golden


def test_fingerprint_tracks_canonical_bytes():
    citation = _citation()
    fingerprint = citation_fingerprint(citation)
    assert fingerprint.startswith("sha256:")
    assert len(fingerprint) == len("sha256:") + 64
    assert citation_fingerprint(_citation()) == fingerprint


def test_serialization_rejects_non_citation_input():
    with pytest.raises(TypeError):
        citation_canonical_bytes({"artifact_id": "ART-x"})  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        citation_fingerprint("not-a-citation")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Value-comparison rule (including the number hazard)
# ---------------------------------------------------------------------------


def test_integral_float_unifies_with_int():
    # Documented number rule: 1.0 and 1 have identical canonical bytes.
    assert json_values_equal(1.0, 1) is True
    assert citation_canonical_bytes(_citation(value=1.0)) == (
        citation_canonical_bytes(_citation(value=1))
    )


def test_boolean_never_equals_int():
    # true and 1 are distinct JSON values; canonical bytes differ.
    assert json_values_equal(True, 1) is False
    assert json_values_equal(False, 0) is False


def test_numbers_do_not_coerce_to_strings():
    assert json_values_equal("1.42", 1.42) is False
    assert json_values_equal(1.42, "1.42") is False


def test_non_integral_floats_compare_exactly_without_tolerance():
    assert json_values_equal(1.42, 1.42) is True
    assert json_values_equal(1.42, 1.4200000000000002) is False


def test_structural_equality_over_nested_values():
    assert json_values_equal({"a": [1, {"b": None}]}, {"a": [1, {"b": None}]})
    assert not json_values_equal({"a": [1, {"b": None}]}, {"a": [1, {"c": None}]})
    assert json_values_equal(None, None)
    assert not json_values_equal(None, "null")


def test_json_values_equal_rejects_unverifiable_kinds():
    with pytest.raises(ValueError):
        json_values_equal(lambda: None, 1)


def test_tuple_and_list_values_serialize_identically():
    assert citation_canonical_bytes(_citation(value=(1, 2))) == (
        citation_canonical_bytes(_citation(value=[1, 2]))
    )


# ---------------------------------------------------------------------------
# Field 1: artifact_id — rejected at the model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_id",
    [
        "",  # empty
        "   ",  # whitespace-only
        "ART-",  # empty suffix
        "ART-abc def",  # whitespace makes identity ambiguous
        "ART-abc/def",  # path separator makes identity ambiguous
        "ART-abc:def",  # colon makes identity ambiguous
        "ART-.",  # suffix must start alphanumeric
        "art-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",  # wrong case prefix
        "7c1e9b3a52d84f6e8a0c2d4f1b9e3a57",  # missing ART- prefix
        "ART-abc~def",  # tilde makes identity ambiguous
        "ART-é1",  # non-ASCII suffix
    ],
)
def test_artifact_id_is_rejected_at_the_model(bad_id):
    with pytest.raises(ValidationError):
        _citation(artifact_id=bad_id)


def test_artifact_id_accepts_the_registry_form():
    assert _citation().artifact_id == "ART-7c1e9b3a52d84f6e8a0c2d4f1b9e3a57"


# ---------------------------------------------------------------------------
# Field 2: path — escaping the workspace is invalid, not merely unresolvable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_path",
    [
        "",  # empty
        "..",  # escapes the root
        "../secrets.json",  # escapes the root
        "synthesis/../../secrets.json",  # escapes mid-path
        "/etc/passwd",  # absolute
        "/",  # absolute root
        "C:/Windows/system32.json",  # Windows drive prefix
        "c:payload.json",  # drive-relative prefix
        "a\\b.json",  # backslash separator
        ".",  # current directory only
        "synthesis/./meta.json",  # '.' segment (non-canonical spelling)
        "synthesis//meta.json",  # redundant separator
        "synthesis/meta.json/",  # trailing separator
        " leading.json",  # leading whitespace
        "trailing.json ",  # trailing whitespace
        "synth\nesis/meta.json",  # control character
    ],
)
def test_path_is_rejected_at_the_model(bad_path):
    with pytest.raises(ValidationError):
        _citation(path=bad_path)


@pytest.mark.parametrize(
    "good_path",
    [
        "meta.json",
        "synthesis/meta_analysis.json",
        "a/b/c/d/e.json",
        "phase4/risk_of_bias/sci-1.json",
        "результаты/анализ.json",
    ],
)
def test_path_accepts_workspace_relative_posix_forms(good_path):
    assert _citation(path=good_path).path == good_path


# ---------------------------------------------------------------------------
# Field 3: locator — RFC 6901 JSON Pointer, deterministic pointer only
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_locator",
    [
        "",  # empty: no pointer into the artifact
        "results/pooled",  # missing leading '/'
        "#/results/pooled",  # URI-fragment form is not accepted
        "/a/~2b",  # invalid escape '~2'
        "/a/~",  # dangling escape
        "/a/~b",  # unescaped '~'
        "/a/b~",  # trailing unescaped '~'
        "~~0/a",  # missing leading '/' plus bad escape
    ],
)
def test_locator_is_rejected_at_the_model(bad_locator):
    with pytest.raises(ValidationError):
        _citation(locator=bad_locator)


@pytest.mark.parametrize(
    "good_locator",
    [
        "/",
        "/risk_ratio",
        "/results/0/pooled/estimate",
        "/results//doubled",
        "/a~1b",
        "/m~0n",
        "/a/~01b",
    ],
)
def test_locator_accepts_rfc6901_pointers(good_locator):
    assert _citation(locator=good_locator).locator == good_locator


# ---------------------------------------------------------------------------
# Field 4: value — only verifiable (canonical-JSON) kinds are accepted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        {1, 2},  # set: unverifiable kind
        b"bytes",  # bytes: unverifiable kind
        complex(1, 2),  # complex: unverifiable kind
        datetime(2026, 1, 1, tzinfo=UTC),  # datetime: unverifiable kind
        object(),  # bare object: unverifiable kind
        (lambda: None),  # bare function: unverifiable kind
        {1: "int-keyed object"},
        {"nested": (lambda: None)},  # unverifiable kind nested deep
        {"nested": [float("nan")]},  # non-finite nested deep
        [{"ok": 1}, {2: "int key nested"}],
    ],
)
def test_value_is_rejected_at_the_model(bad_value):
    with pytest.raises(ValidationError):
        _citation(value=bad_value)


def test_accepted_value_kinds():
    for value in [None, True, 0, -3, 1.5, "1.42", [1, "two"], {"a": [None]}]:
        assert _citation(value=value).value == value


# ---------------------------------------------------------------------------
# The citation is exactly four fields
# ---------------------------------------------------------------------------


def test_extra_field_is_rejected_at_the_model():
    with pytest.raises(ValidationError):
        ClaimCitation.model_validate({**VALID_SOURCE, "confidence": 0.9})


@pytest.mark.parametrize("missing", ["artifact_id", "path", "locator", "value"])
def test_missing_field_is_rejected_at_the_model(missing):
    payload = {key: value for key, value in VALID_SOURCE.items() if key != missing}
    with pytest.raises(ValidationError):
        ClaimCitation.model_validate(payload)


@pytest.mark.parametrize(
    "field",
    ["artifact_id", "path", "locator", "value"],
)
def test_non_string_field_types_are_rejected(field):
    # strict=True rejects a non-string for the three string fields; for
    # ``value`` an int would be a legitimate JSON number, so an
    # unverifiable object stands in as the non-JSON type.
    bad_type: object = object() if field == "value" else 7
    payload = {**VALID_SOURCE, field: bad_type}
    with pytest.raises(ValidationError):
        ClaimCitation.model_validate(payload)


# ---------------------------------------------------------------------------
# Versioned-surface separation and schema drift
# ---------------------------------------------------------------------------


def test_claims_surface_is_registered_under_its_own_base_uri():
    schema = load_schema("claim-citation.schema.json")
    assert schema["$id"] == (f"{CLAIM_SCHEMA_BASE_URI}/claim-citation.schema.json")
    assert schema["$id"].startswith("https://nexus-scholar.org/schemas/claims/v1/")
    assert not schema["$id"].startswith(V1_SCHEMA_BASE_URI)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert sorted(schema["required"]) == ["artifact_id", "locator", "path", "value"]


def test_frozen_v1_catalog_is_untouched_by_the_claims_surface():
    assert "claim-citation.schema.json" not in V1_SCHEMA_MODELS
    assert V1_SCHEMA_BASE_URI == "https://nexus-scholar.org/schemas/contracts/v1"
    # No v1 catalog entry may be the claim-existence citation model; the
    # v1 "claim-evidence-ledger" model is a different, frozen artifact.
    assert all(model is not ClaimCitation for model in V1_SCHEMA_MODELS.values())


def test_bundled_schema_file_matches_the_renderer():
    expected = render_schema_files()["claim-citation.schema.json"].encode("utf-8")
    bundled = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "scholar_harness"
        / "claims"
        / "schemas"
        / "claim-citation.schema.json"
    ).read_bytes()
    assert bundled == expected


def test_unknown_schema_filename_is_rejected():
    with pytest.raises(KeyError):
        load_schema("not-a-schema.json")
