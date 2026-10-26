"""T-ALP-B conformance gate for ``Envelope@1`` and the refusal registry.

Every invariant of ``specs/agent-layer-portability/02_envelope_and_refusals.md``
§3 is a named test, the §8 negative matrix is parametrised, and the generated
artifacts (docs table, JSON schema) are pinned to the code that renders them.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from scholar_harness.contracts.envelope import (
    EnvelopeStatus,
    RefusalCode,
    diff,
    envelope_id,
    output_sha256,
    validate,
    verify_parents,
)
from scholar_harness.contracts.envelope.api import EnvelopeRefusalError
from scholar_harness.contracts.envelope.registry import render_refusals_doc
from scholar_harness.contracts.envelope.schema import render_envelope_schema

ROOT = Path(__file__).resolve().parents[2]
ROLES = ROOT / "roles"
FIXTURES = ROOT / "tests" / "conformance" / "fixtures" / "envelope"
REFUSALS_DOC = ROOT / "docs" / "architecture" / "refusals.md"
SCHEMA_FILE = (
    ROOT
    / "src"
    / "scholar_harness"
    / "contracts"
    / "schemas"
    / "envelope"
    / "envelope.schema.json"
)

BLOCKED_STATUS_VALUES = [
    "BLOCKED_INPUT",
    "BLOCKED_AMBIGUOUS_TASK",
    "BLOCKED_CANONICAL_REPO",
    "BLOCKED_BASELINE_DRIFT",
]


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def mutate(base: dict[str, Any], **changes: Any) -> dict[str, Any]:
    """Return a raw envelope dict with ``changes`` applied and hashes recomputed."""

    raw = json.loads(json.dumps(base))
    raw.update(changes)
    raw["envelope_id"] = envelope_id(raw)
    return raw


def all_base_statuses() -> list[dict[str, Any]]:
    return [load_fixture(name) for name in FIXTURE_LIST]


FIXTURE_LIST = [
    "ok",
    "partial",
    "blocked_input",
    "refused",
    "provider_transient",
    "invalid_output",
    "parent_hash_mismatch",
]


def _as_coder(base: dict[str, Any], *, status: str) -> dict[str, Any]:
    """Rebind ``base`` to a role whose records allow all four BLOCKED codes."""

    return mutate(
        base,
        status=status,
        role="coder",
        role_version="2.0.0",
        arm=None,
        refusal=dict(load_fixture("blocked_input")["refusal"], code=status),
        provenance=dict(
            base["provenance"], adapter="in-process", isolation="none", blinded_from=[]
        ),
    )


# ---------------------------------------------------------------------------
# Golden fixtures validate (each fixture is asserted, not just present)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", FIXTURE_LIST)
def test_fixture_validates(name: str) -> None:
    envelope = validate(load_fixture(name), roles_dir=ROLES)
    assert envelope.envelope == 1
    assert envelope.envelope_id == load_fixture(name)["envelope_id"]


def test_fixture_output_hash_matches_payload() -> None:
    for name in FIXTURE_LIST:
        raw = load_fixture(name)
        assert raw["output_sha256"] == output_sha256(raw)


# ---------------------------------------------------------------------------
# Spec 02 §3 invariants — each named here
# ---------------------------------------------------------------------------


def test_invariant_ok_complete_and_valid() -> None:
    envelope = validate(load_fixture("ok"), roles_dir=ROLES)
    assert envelope.status is EnvelopeStatus.OK
    assert envelope.output is not None
    assert envelope.coverage.produced == envelope.coverage.expected


def test_invariant_ok_rejects_output_null() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(load_fixture("ok"), output=None, output_sha256=None), roles_dir=ROLES
        )
    assert "OK requires output" in info.value.detail


def test_invariant_ok_rejects_without_coverage() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(load_fixture("ok"), coverage=None), roles_dir=ROLES)
    assert "OK requires coverage" in info.value.detail


def test_invariant_ok_rejects_inner_coverage_gap() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(
                load_fixture("ok"),
                coverage={"expected": 50, "produced": 49, "unit": "records"},
            ),
            roles_dir=ROLES,
        )
    assert "PARTIAL" in info.value.detail  # the finding names the downgrade


def test_invariant_ok_rejects_schema_invalid_payload() -> None:
    raw = load_fixture("ok")
    raw["output"]["data"]["decisions"][0]["decision"] = "PERMANENT"
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(raw), roles_dir=ROLES)
    assert info.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert "Contract v1 schema" in info.value.detail


def test_invariant_partial_incomplete_with_refusal() -> None:
    envelope = validate(load_fixture("partial"), roles_dir=ROLES)
    assert envelope.status is EnvelopeStatus.PARTIAL
    assert envelope.coverage.produced < envelope.coverage.expected
    assert envelope.refusal.codes == ["BATCH_INCOMPLETE"]


def test_invariant_partial_rejects_full_coverage() -> None:
    raw = load_fixture("partial")
    raw["coverage"]["produced"] = raw["coverage"]["expected"]
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(raw), roles_dir=ROLES)
    assert "PARTIAL requires coverage.produced < expected" in info.value.detail


def test_invariant_partial_rejects_without_refusal() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(load_fixture("partial"), refusal=None), roles_dir=ROLES)
    assert "PARTIAL requires refusal" in info.value.detail


@pytest.mark.parametrize("status", BLOCKED_STATUS_VALUES)
def test_invariant_blocked_shape(status: str) -> None:
    raw = _as_coder(load_fixture("blocked_input"), status=status)
    envelope = validate(raw, roles_dir=ROLES)
    assert envelope.status is EnvelopeStatus(status)
    assert envelope.output is None
    assert envelope.human_action_required is True


@pytest.mark.parametrize("status", BLOCKED_STATUS_VALUES)
def test_invariant_blocked_rejects_payload(status: str) -> None:
    raw = _as_coder(load_fixture("ok"), status=status)
    raw["refusal"] = dict(load_fixture("blocked_input")["refusal"], code=status)
    raw["envelope_id"] = envelope_id(raw)
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert f"{status} must ship no payload" in info.value.detail


@pytest.mark.parametrize("status", BLOCKED_STATUS_VALUES)
def test_invariant_blocked_requires_human_action(status: str) -> None:
    raw = _as_coder(load_fixture("blocked_input"), status=status)
    raw["human_action_required"] = False
    raw["envelope_id"] = envelope_id(raw)
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert "human_action_required" in info.value.detail


def test_invariant_refused_registry_code_only() -> None:
    envelope = validate(load_fixture("refused"), roles_dir=ROLES)
    assert envelope.refusal.code == RefusalCode.REFUSED_UNSUPPORTED


def test_invariant_refused_rejects_payload() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(load_fixture("refused"), output=load_fixture("ok")["output"]),
            roles_dir=ROLES,
        )
    assert "REFUSED must ship no payload" in info.value.detail


def test_invariant_transient_shape() -> None:
    envelope = validate(load_fixture("provider_transient"), roles_dir=ROLES)
    assert envelope.output is None
    assert envelope.refusal.code == RefusalCode.PROVIDER_TRANSIENT
    assert envelope.retryable is True
    assert envelope.human_action_required is False


def test_invariant_transient_rejects_payload() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(
                load_fixture("provider_transient"), output=load_fixture("ok")["output"]
            ),
            roles_dir=ROLES,
        )
    assert "must ship no payload" in info.value.detail


def test_invariant_transient_rejects_unretryable() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(load_fixture("provider_transient"), retryable=False), roles_dir=ROLES
        )
    assert "retryable" in info.value.detail


def test_invariant_transient_rejects_human_action() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(load_fixture("provider_transient"), human_action_required=True),
            roles_dir=ROLES,
        )
    assert "no human action" in info.value.detail


def test_invariant_invalid_output_retains_forensics() -> None:
    envelope = validate(load_fixture("invalid_output"), roles_dir=ROLES)
    assert envelope.output is not None
    assert envelope.refusal.validation_findings


def test_invariant_invalid_output_rejects_empty_findings() -> None:
    raw = load_fixture("invalid_output")
    raw["refusal"]["validation_findings"] = []
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(raw), roles_dir=ROLES)
    assert "non-empty validation findings" in info.value.detail


def test_invariant_gate_failed_carry_details() -> None:
    base = load_fixture("parent_hash_mismatch")
    provenance = dict(base["provenance"], isolation="directory")
    provenance["blinded_from"] = ["coder"]
    raw = mutate(
        base,
        status="GATE_FAILED",
        role="tester",
        role_version="2.0.0",
        arm="A",
        provenance=provenance,
        refusal={"code": "TEST_GATE_FAILED", "detail": "declared gate command failed"},
    )
    envelope = validate(raw, roles_dir=ROLES)
    assert envelope.refusal.code == RefusalCode.TEST_GATE_FAILED
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(raw, refusal=None), roles_dir=ROLES)
    assert "GATE_FAILED requires a refusal" in info.value.detail


# ---------------------------------------------------------------------------
# Packet §4 negative matrix
# ---------------------------------------------------------------------------


def test_refusal_present_with_non_refusal_status_rejected() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(load_fixture("ok"), refusal=load_fixture("refused")["refusal"]),
            roles_dir=ROLES,
        )
    # OK is refusal-free; the finding names the conflict with the status.
    assert "refusal must be null for OK" in info.value.detail


def test_unknown_refusal_code_named() -> None:
    raw = load_fixture("provider_transient")
    raw["refusal"]["code"] = "REFUSED_ADMIRABLY"
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(raw), roles_dir=ROLES)
    assert "unknown refusal code 'REFUSED_ADMIRABLY'" in info.value.detail


def test_envelope_id_tamper_rejected() -> None:
    raw = load_fixture("ok")
    raw["envelope_id"] = "ENV-" + "f" * 16
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert "envelope_id tampered" in info.value.detail


def test_unknown_status_named() -> None:
    raw = load_fixture("ok")
    raw["status"] = "failed"
    raw["envelope_id"] = envelope_id(raw)
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert "unknown status 'failed'" in info.value.detail


def test_contraband_payload_field_not_rescued() -> None:
    raw = load_fixture("ok")
    raw["output"]["data"]["contraband_extra_evidence"] = {"lie": True}
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(raw), roles_dir=ROLES)
    assert "fields the schema does not define" in info.value.detail
    assert info.value.refusal_code is RefusalCode.INVALID_OUTPUT


# ---------------------------------------------------------------------------
# Hashing and identity (spec 02 §4)
# ---------------------------------------------------------------------------


def test_envelope_id_stable_across_runs() -> None:
    first = validate(load_fixture("ok"), roles_dir=ROLES).envelope_id
    second = validate(load_fixture("ok"), roles_dir=ROLES).envelope_id
    assert first == second == load_fixture("ok")["envelope_id"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("role", "reviewer"),
        ("role_version", "3.0.0"),
        ("task_id", "T-SC-999"),
        ("arm", "A"),
        ("status", "PARTIAL"),
    ],
)
def test_envelope_id_changes_with_immutable_fields(field: str, value: Any) -> None:
    base = load_fixture("ok")
    raw = mutate(base, **{field: value})
    assert raw["envelope_id"] != base["envelope_id"]


def test_envelope_id_changes_with_input_parent_and_payload_hashes() -> None:
    base = load_fixture("ok")
    assert (
        mutate(base, inputs=[dict(base["inputs"][0], sha256="d" * 64)])["envelope_id"]
        != base["envelope_id"]
    )
    assert (
        mutate(base, parents=[{"artifact": "protocol.json", "sha256": "e" * 64}])[
            "envelope_id"
        ]
        != base["envelope_id"]
    )
    payload_variant = json.loads(json.dumps(base))
    payload_variant["output"]["data"]["decisions"][0]["decision"] = "MAYBE"
    payload_variant["output_sha256"] = output_sha256(payload_variant)
    payload_variant["envelope_id"] = envelope_id(payload_variant)
    assert payload_variant["envelope_id"] != base["envelope_id"]


@pytest.mark.parametrize(
    "changes",
    [
        {"created_at": "2030-01-01T00:00:00Z"},
        {
            "provenance": {
                "adapter": "in-process",
                "adapter_version": "2.0.0",
                "isolation": "redacted-input",
                "blinded_from": ["screener@A"],
                "duration_ms": 9999,
            }
        },
    ],
)
def test_timing_fields_do_not_affect_hashes(changes: dict[str, Any]) -> None:
    base = load_fixture("ok")
    raw = json.loads(json.dumps(base))
    raw.update(changes)
    raw["envelope_id"] = envelope_id(raw)
    # envelope_id ignores timing by construction (recompute leaves it equal).
    assert raw["envelope_id"] == base["envelope_id"]
    assert raw["output_sha256"] == base["output_sha256"]


def test_duration_ms_and_adapter_excluded_independently() -> None:
    base = load_fixture("ok")
    variants = [
        {"provenance": dict(base["provenance"], duration_ms=1)},
        {"provenance": dict(base["provenance"], adapter="in-process")},
        {"provenance": dict(base["provenance"], adapter_version="9.9.9")},
        {"created_at": "2000-01-01T00:00:00Z"},
    ]
    for variant in variants:
        raw = json.loads(json.dumps(base))
        raw.update(variant)
        raw["envelope_id"] = envelope_id(raw)
        assert raw["envelope_id"] == base["envelope_id"]
        assert raw["output_sha256"] == base["output_sha256"]


def test_transient_retry_preserves_identity() -> None:
    base = load_fixture("provider_transient")
    attempt_two = json.loads(json.dumps(base))
    attempt_two["created_at"] = "2026-10-23T10:31:22Z"
    attempt_two["provenance"] = dict(base["provenance"], duration_ms=9310)
    attempt_two["envelope_id"] = envelope_id(attempt_two)
    assert attempt_two["envelope_id"] == base["envelope_id"]
    assert attempt_two["output_sha256"] == base["output_sha256"]


# ---------------------------------------------------------------------------
# Parent binding (spec 02 §5)
# ---------------------------------------------------------------------------


@pytest.fixture()
def binding_root(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """A tmp tree holding the two parents the ok fixture declares."""

    root = tmp_path / "ws"
    (root / "literature" / "screening").mkdir(parents=True)
    (root / "protocol.json").write_bytes(
        b'{"title": "protocol"}\n'
    )  # write_bytes: text-mode on win32 would translate the newline
    (root / "SCREENING_CRITERIA.md").write_bytes(b"# criteria\n")
    (root / "literature" / "screening" / "batch_0001.json").write_bytes(
        json.dumps({"batch_id": "batch_0001"}).encode("utf-8")
    )
    raw = json.loads(json.dumps(load_fixture("ok")))
    raw["parents"] = [
        {
            "artifact": "protocol.json",
            "sha256": hashlib.sha256(b'{"title": "protocol"}\n').hexdigest(),
        },
        {
            "artifact": "SCREENING_CRITERIA.md",
            "sha256": hashlib.sha256(b"# criteria\n").hexdigest(),
        },
    ]
    raw["inputs"] = [
        {
            "schema": "ScreeningBatch@1",
            "path": "literature/screening/batch_0001.json",
            "sha256": hashlib.sha256(
                json.dumps({"batch_id": "batch_0001"}).encode("utf-8")
            ).hexdigest(),
            "role_version": None,
        }
    ]
    raw["envelope_id"] = envelope_id(raw)
    return root, raw


def test_verify_parents_ok(binding_root: tuple[Path, dict[str, Any]]) -> None:
    root, raw = binding_root
    envelope = validate(raw, verify_parents=True, root=root, roles_dir=ROLES)
    assert envelope.parents[0].artifact == "protocol.json"


def test_verify_parents_mutated_hash_is_mismatch(
    binding_root: tuple[Path, dict[str, Any]],
) -> None:
    root, raw = binding_root
    envelope = validate(raw, roles_dir=ROLES)
    (root / "SCREENING_CRITERIA.md").write_bytes(b"# criteria mutated\n")
    with pytest.raises(EnvelopeRefusalError) as info:
        verify_parents(envelope, root)
    assert info.value.refusal_code is RefusalCode.PARENT_HASH_MISMATCH
    assert "SCREENING_CRITERIA.md" in info.value.detail


def test_verify_parents_missing_file_is_blocked_input(
    binding_root: tuple[Path, dict[str, Any]],
) -> None:
    root, raw = binding_root
    envelope = validate(raw, roles_dir=ROLES)
    (root / "SCREENING_CRITERIA.md").unlink()
    with pytest.raises(EnvelopeRefusalError) as info:
        verify_parents(envelope, root)
    assert info.value.refusal_code is RefusalCode.BLOCKED_INPUT


def test_verify_parents_silent_rebind_not_allowed(
    binding_root: tuple[Path, dict[str, Any]],
) -> None:
    """A mismatch is never downgraded to a re-bind of the envelope."""

    root, raw = binding_root
    envelope = validate(raw, roles_dir=ROLES)
    (root / "SCREENING_CRITERIA.md").write_bytes(b"# criteria mutated\n")
    with pytest.raises(EnvelopeRefusalError) as info:
        verify_parents(envelope, root)
    assert info.value.refusal_code is RefusalCode.PARENT_HASH_MISMATCH


# ---------------------------------------------------------------------------
# Role records (Phase A artifacts, read-only)
# ---------------------------------------------------------------------------


def test_unknown_role_named() -> None:
    raw = mutate(load_fixture("ok"), role="synthetic-critic")
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert "unknown role 'synthetic-critic'" in info.value.detail


def test_role_version_major_mismatch_named() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(load_fixture("ok"), role_version="3.0.0"), roles_dir=ROLES)
    assert "incompatible with screener@2.0.0" in info.value.detail


def test_blinded_from_beyond_the_declaration_rejected() -> None:
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(
            mutate(
                load_fixture("ok"),
                provenance=dict(
                    load_fixture("ok")["provenance"], blinded_from=["reviewer@2.0.0"]
                ),
            ),
            roles_dir=ROLES,
        )
    assert "declaration does not grant" in info.value.detail


def test_peer_arm_blinding_is_consistent() -> None:
    envelope = validate(load_fixture("ok"), roles_dir=ROLES)
    assert envelope.provenance.blinded_from == ["screener@A"]


def test_role_emitter_codes_and_registry_agree() -> None:
    """Every record-declared code is a registry code (payload verdict excepted)."""

    for record_path in sorted(ROLES.glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        declared = set(record.get("refusal_codes") or [])
        rogue = (
            declared
            - {member.value for member in RefusalCode}
            - {"VERDICT_CHANGES_REQUESTED"}
        )
        assert not rogue, f"{record_path.name} declares unregistered codes: {rogue}"


def test_runtime_refusal_within_role_declaration() -> None:
    """A screening code claimed by an extraction-only role is rejected."""

    raw = _as_coder(load_fixture("blocked_input"), status="BLOCKED_INPUT")
    raw = mutate(
        raw,
        role="extractor-a",
        role_version="2.0.0",
        refusal={
            "code": "CRITERIA_HASH_MISMATCH",
            "detail": "criteria_sha256 does not match the protocol fingerprint",
        },
    )
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert "may not emit" in info.value.detail


# ---------------------------------------------------------------------------
# Schema-name compatibility (repair T-ALP-B: near-miss names must fail loud)
# ---------------------------------------------------------------------------


def _with_output_schema(base: dict[str, Any], name: str) -> dict[str, Any]:
    raw = json.loads(json.dumps(base))
    raw["output"]["schema"] = name
    # output_sha256 covers output.data only: the data is unchanged, so the
    # declared hash need not move — exactly why a silent typo would slip past.
    raw["envelope_id"] = envelope_id(raw)
    return raw


@pytest.mark.parametrize(
    "name",
    [
        "ScreeningDecisions@2",  # version drift
        "ScreeningDecisions",  # versionless
        "ScreeningDecisions2@1",  # glued version
        "screeningdecisions@1",  # case drift
    ],
)
def test_near_miss_output_schema_named_refusal(name: str) -> None:
    raw = _with_output_schema(load_fixture("ok"), name)
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert info.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert f"output.schema {name!r}" in info.value.detail  # the claimed name
    assert "declared: ['ScreeningDecisions@1']" in info.value.detail  # and theirs


def test_input_schema_not_declared_by_role_named_refusal() -> None:
    raw = load_fixture("ok")
    raw["inputs"] = [dict(raw["inputs"][0], schema="CorpusSnapshot@1")]
    raw["envelope_id"] = envelope_id(raw)
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=ROLES)
    assert info.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert "inputs[0].schema 'CorpusSnapshot@1'" in info.value.detail
    assert "declared: ['Protocol@1'" in info.value.detail
    assert "'ScreeningBatch@1'" in info.value.detail


def test_declared_but_unregistered_output_schema_named_refusal(
    tmp_path: Path,
) -> None:
    """A synthetic role record declaring a schema the harness cannot validate.

    Not a shipped record: written to ``tmp_path`` so ``roles/`` stays untouched.
    """

    record = {
        "id": "synthetic-validator",
        "version": "1.0.0",
        "inputs": [{"schema": "ScreeningBatch@1"}],
        "outputs": [{"schema": "SyntheticArtifact@1"}],
        "refusal_codes": ["INVALID_OUTPUT"],
        "independence": {"blinded_from": [], "isolation": "redacted-input"},
    }
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "synthetic-validator.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    raw = _with_output_schema(load_fixture("ok"), "SyntheticArtifact@1")
    raw = mutate(
        raw,
        role="synthetic-validator",
        role_version="1.0.0",
        provenance=dict(raw["provenance"], isolation="redacted-input", blinded_from=[]),
    )
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(raw, roles_dir=roles_dir)
    assert info.value.refusal_code is RefusalCode.INVALID_OUTPUT
    assert "SyntheticArtifact@1" in info.value.detail
    assert "not registered with the harness" in info.value.detail


# ---------------------------------------------------------------------------
# Refusal registry closure (packet criterion 7) and generated artifacts
# ---------------------------------------------------------------------------


def test_docs_table_covers_every_enum_code() -> None:
    doc = render_refusals_doc()
    for code in RefusalCode:
        assert f"`{code.value}`" in doc, f"{code.value} absent from generated docs"


def test_docs_table_has_no_code_absent_from_enum() -> None:
    doc = render_refusals_doc()
    rendered = set(re.findall(r"`([A-Z][A-Z_]{3,})`", doc))
    known = {member.value for member in RefusalCode} | {
        "VERDICT_CHANGES_REQUESTED",  # payload row, deliberately annotated
        "PENDING",  # quoted in the transient policy prose as a payload state
        "EXCLUDED",
        "PARTIAL",  # quoted as an envelope status in the policy prose
        "REFUSED",  # quoted as an envelope status in the policy prose
    }
    unknown = rendered - known
    assert not unknown, f"docs name refusal-ish codes outside the registry: {unknown}"


def test_committed_refusals_doc_matches_renderer() -> None:
    assert REFUSALS_DOC.read_text(encoding="utf-8") == render_refusals_doc()


def test_verdict_changes_requested_is_payload_not_refusal() -> None:
    assert "VERDICT_CHANGES_REQUESTED" not in {m.value for m in RefusalCode}
    raw = load_fixture("refused")
    raw["refusal"] = {
        "code": "VERDICT_CHANGES_REQUESTED",
        "detail": "repairs requested",
    }
    with pytest.raises(EnvelopeRefusalError) as info:
        validate(mutate(raw), roles_dir=ROLES)
    assert "unknown refusal code" in info.value.detail


def test_committed_envelope_schema_matches_renderer() -> None:
    assert SCHEMA_FILE.read_text(encoding="utf-8") == render_envelope_schema()


# ---------------------------------------------------------------------------
# diff (spec 02 §4)
# ---------------------------------------------------------------------------


def test_diff_identical_envelopes_is_empty() -> None:
    raw = load_fixture("ok")
    report = diff(raw, json.loads(json.dumps(raw)))
    assert report.differing_fields == []
    assert report.hash_changes == {}
    assert report.same_output_different_identifiers is None


def test_diff_flags_differing_fields_and_hashes() -> None:
    report = diff(load_fixture("ok"), load_fixture("partial"))
    assert "status" in report.differing_fields
    assert "envelope_id" in report.differing_fields
    assert (
        report.hash_changes["envelope_id"]["a"]
        != report.hash_changes["envelope_id"]["b"]
    )


def test_diff_same_output_different_identifiers_names_cause() -> None:
    """Same payload, different inputs: the report names the differing input."""

    base_a = load_fixture("ok")
    base_b = mutate(
        load_fixture("ok"),
        inputs=[dict(load_fixture("ok")["inputs"][0], sha256="d" * 64)],
    )
    report = diff(base_a, base_b)
    assert report.hash_changes.get("output_sha256") is None
    assert (
        report.hash_changes["envelope_id"]["a"]
        != report.hash_changes["envelope_id"]["b"]
    )
    assert report.same_output_different_identifiers is not None
    assert "inputs[0].sha256" in report.same_output_different_identifiers
    assert "d" * 64 in report.same_output_different_identifiers


def test_diff_exposes_timing_only_differences() -> None:
    base = load_fixture("ok")
    altered = mutate(base, created_at="2030-01-01T00:00:00Z")
    report = diff(base, altered)
    assert report.timing_only == ["created_at"]
    assert report.differing_fields == []
