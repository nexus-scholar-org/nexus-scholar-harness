"""T-D0D2 screening decision contract reader tests.

Every test runs against a synthetic workspace materialized from the static
fixtures under ``tests/fixtures/screening_decision_contract/``.  No real
research workspace, no network, and no producer file is ever touched: the
reader is read-only and the only writer under test is the report sidecar.

The forbidden-token guard below needs the demo's domain tokens as *search
strings*; they appear in this test module only, never in the module under
test.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scholar_harness.screening import decision_contract as dc
from scholar_harness.screening.decision_contract import (
    DecisionContract,
    build_debt_ledger,
    classify_decision_file,
    cmd_validate,
    default_contract,
    discover_decision_files,
    load_contract,
    normalize_row,
)

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "scholar_harness" / "screening"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "screening_decision_contract"
CONTRACTS = FIXTURES / "contracts"
PARENTS = FIXTURES / "parents"
SCENARIOS = FIXTURES / "scenarios"
CLI = ROOT / "src" / "scholar_harness" / "agent_screen.py"

#: Domain tokens that must never appear in the module under test.
FORBIDDEN_TOKENS = ("uav", "weed", "crossref", "openalex", "9ae1f97d", "0c7f129d")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _screening_dir(workspace: Path) -> Path:
    return workspace / "literature" / "screening"


def _materialize(
    tmp_path: Path,
    scenario: str,
    *,
    contract: str | None = "agent_lane",
    parents: bool = True,
) -> Path:
    """Build a synthetic workspace from one scenario fixture.

    ``contract=None`` copies no contract configuration, so the reader falls
    back to its domain-free defaults.
    """
    workspace = tmp_path / "ws"
    screening = _screening_dir(workspace)
    screening.mkdir(parents=True, exist_ok=True)
    (workspace / "project.json").write_text(
        json.dumps({"project_slug": "fixture-workspace", "stats": {}}, indent=2),
        encoding="utf-8",
    )
    if contract is not None:
        shutil.copyfile(
            CONTRACTS / f"{contract}.json", screening / "decision_contract.json"
        )
    if parents:
        for name in ("batch_0001.json", "batch_0001.view.json"):
            shutil.copyfile(PARENTS / name, screening / name)
    for source in sorted((SCENARIOS / scenario).iterdir()):
        shutil.copyfile(source, screening / source.name)
    return workspace


def _materialize_batches(
    tmp_path: Path, scenarios: list[str], *, contract: str = "agent_lane"
) -> Path:
    """Build one workspace holding several decision batches."""
    workspace = tmp_path / "ws"
    screening = _screening_dir(workspace)
    screening.mkdir(parents=True, exist_ok=True)
    (workspace / "project.json").write_text(
        json.dumps({"project_slug": "fixture-workspace", "stats": {}}, indent=2),
        encoding="utf-8",
    )
    shutil.copyfile(
        CONTRACTS / f"{contract}.json", screening / "decision_contract.json"
    )
    for index, scenario in enumerate(scenarios, start=1):
        stem = f"batch_{index:04d}"
        shutil.copyfile(PARENTS / "batch_0001.json", screening / f"{stem}.json")
        shutil.copyfile(
            PARENTS / "batch_0001.view.json", screening / f"{stem}.view.json"
        )
        shutil.copyfile(
            SCENARIOS / scenario / "batch_0001_decisions_A1.json",
            screening / f"{stem}_decisions_A1.json",
        )
    return workspace


def _contract_for(workspace: Path) -> DecisionContract:
    return load_contract(_screening_dir(workspace) / "decision_contract.json")


def _agent_lane_contract(**overrides) -> DecisionContract:
    """Return the agent-lane contract, optionally with keys overridden."""
    data = json.loads((CONTRACTS / "agent_lane.json").read_text(encoding="utf-8"))
    data.update(overrides)
    return DecisionContract.from_dict(data)


def _classifications(
    workspace: Path, contract: DecisionContract | None = None
) -> tuple[DecisionContract, list[dc.FileClassification]]:
    loaded = contract or _contract_for(workspace)
    files = discover_decision_files(
        _screening_dir(workspace),
        loaded,
        exclude=[_screening_dir(workspace) / "decision_contract.json"],
    )
    return loaded, [classify_decision_file(item, loaded) for item in files]


def _only(
    workspace: Path, contract: DecisionContract | None = None
) -> tuple[DecisionContract, dc.FileClassification]:
    _, classifications = _classifications(workspace, contract)
    assert len(classifications) == 1, [item.file for item in classifications]
    return _, classifications[0]


def _codes(classification: dc.FileClassification) -> list[str]:
    return [dc.tag_prefix(code) for code in classification.structural]


def _debt_tags(classification: dc.FileClassification) -> list[str]:
    tags: list[str] = []
    for entry in classification.debt:
        tags.extend(entry["debt"])
    return tags


def _advisory_tags(classification: dc.FileClassification) -> list[str]:
    return classification.advisory_tags()


def _snapshot(directory: Path) -> dict[str, tuple[bytes, int]]:
    """Snapshot paths, bytes, and mtimes of every file under ``directory``."""
    return {
        str(path.relative_to(directory)).replace("\\", "/"): (
            path.read_bytes(),
            path.stat().st_mtime_ns,
        )
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _journal_rows(workspace: Path) -> list[dict]:
    journal = workspace / "audit" / "journal.jsonl"
    if not journal.exists():
        return []
    return [
        json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()
    ]


# ---------------------------------------------------------------------------
# AC-1 / AC-35 -- module surface and domain freedom
# ---------------------------------------------------------------------------


def test_module_has_no_domain_token() -> None:
    """AC-1: the module carries no domain token from the reference workspace."""
    source = (SRC_ROOT / "decision_contract.py").read_text(encoding="utf-8")
    lowered = source.lower()
    for token in FORBIDDEN_TOKENS:
        assert token not in lowered, f"domain token {token!r} leaked into the module"
    assert re.search(r"INC-\d{2}", source) is None
    assert re.search(r"EXC-\d{2}", source) is None


def test_module_imports_cleanly_and_exposes_its_public_names() -> None:
    """AC-1/AC-35: the public surface is importable and documented."""
    for name in (
        "DecisionContract",
        "DecisionContractRefused",
        "FileClassification",
        "normalize_row",
        "classify_decision_file",
        "build_debt_ledger",
        "discover_decision_files",
        "resolve_parent_artifacts",
        "load_contract",
        "default_contract",
        "cmd_validate",
    ):
        assert hasattr(dc, name), f"missing public name {name}"
    docstring = dc.__doc__ or ""
    flat = " ".join(docstring.split())
    for name in (
        "DecisionContract",
        "DecisionContractRefused",
        "FileClassification",
        "normalize_row",
        "classify_decision_file",
        "discover_decision_files",
        "resolve_parent_artifacts",
        "build_debt_ledger",
        "cmd_validate",
    ):
        assert name in flat, f"{name} is not documented in the module docstring"
    assert "NOT a Contract v1 publication surface" in flat
    assert "does **not** replace the Contract v1 collector's provenance gates" in flat


def test_module_does_not_wire_into_the_contract_v1_collector() -> None:
    """G-10: the reader is not wired into the Contract v1 publication path."""
    collector = (SRC_ROOT / "collector.py").read_text(encoding="utf-8")
    assert "decision_contract" not in collector
    assert "cmd_validate" not in collector
    tree = ast.parse((SRC_ROOT / "decision_contract.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module or ''}.{alias.name}" for alias in node.names)
    assert not any("collector" in name for name in imported), imported
    assert not any("batcher" in name for name in imported), imported


# ---------------------------------------------------------------------------
# AC-2 -- domain-free defaults
# ---------------------------------------------------------------------------


def test_default_contract_is_domain_free() -> None:
    """AC-2/A3: no expected prefixes, no embedded pattern, no aliases by default."""
    contract = default_contract()
    assert contract.expected_criteria_sha256_prefix == ""
    assert contract.expected_prompt_sha256_prefix == ""
    assert contract.embedded_reason_code_pattern == ""
    assert dict(contract.reason_code_aliases) == {}
    assert contract.schema_version_supported
    # A3: the default file-name patterns follow the lane the harness itself
    # produces (``batcher.py``), not the pilot's 4-digit/family layout.
    assert contract.decision_file_pattern == "batch_{n:03d}_decisions.json"
    assert contract.batch_file_pattern == "batch_{n:03d}.json"
    assert contract.view_file_pattern == ""


def test_default_contract_does_not_turn_every_file_bad(tmp_path: Path) -> None:
    """AC-2/A3/D4: with no configured prefixes a canonical file is not BAD."""
    workspace = _materialize(tmp_path, "harness_lane", contract=None, parents=False)
    contract = default_contract()
    _, classification = _only(workspace, contract)
    assert classification.tier == dc.TIER_VALID
    assert classification.structural == ()
    assert classification.file == "batch_001_decisions.json"
    # The skipped instrument checks are recorded as unattested, not failed.
    assert classification.header["criteria_sha256_attested"] is False
    assert (
        classification.header["checks"]["criteria_sha256"]
        == "SKIPPED_NO_EXPECTED_PREFIX"
    )
    assert (
        classification.header["checks"]["prompt_template_sha256"]
        == "SKIPPED_NO_EXPECTED_PREFIX"
    )


def test_missing_contract_file_falls_back_to_the_domain_free_default(
    tmp_path: Path,
) -> None:
    """AC-2: an absent configuration yields the domain-free default."""
    contract = load_contract(tmp_path / "does-not-exist.json")
    assert contract.expected_criteria_sha256_prefix == ""
    assert dict(contract.reason_code_aliases) == {}


# ---------------------------------------------------------------------------
# AC-3 -- canonical rows
# ---------------------------------------------------------------------------


def test_canonical_rows_are_valid_without_debt_or_advisory(tmp_path: Path) -> None:
    """AC-3: a canonical file is VALID with zero debt and zero advisory."""
    workspace = _materialize(tmp_path, "canonical")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_VALID
    assert classification.structural == ()
    assert _debt_tags(classification) == []
    assert _advisory_tags(classification) == []
    assert classification.rows == 2
    assert classification.canonical_rows[0]["reason_code"] == "CODE_ONE"


# ---------------------------------------------------------------------------
# AC-4 -- alias classes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "alias_key",
    ["exclusion_reason_code", "pending_reason_code", "inclusion_hint", "reason_CODE"],
)
def test_alias_classes_are_debt_tagged_and_verbatim(
    tmp_path: Path, alias_key: str
) -> None:
    """AC-4: an alias is honored only when configured, and always tagged."""
    workspace = _materialize(tmp_path, f"alias_{alias_key}")
    _contract, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert f"ALIAS_REASON_CODE:{alias_key}" in _debt_tags(classification)
    source_rows = json.loads(
        (_screening_dir(workspace) / "batch_0001_decisions_A1.json").read_text(
            encoding="utf-8"
        )
    )["decisions"]
    for index, row in enumerate(source_rows):
        assert classification.canonical_rows[index]["reason_code"] == row[alias_key]
    # The alias key is a known key, so it is never reported as unknown.
    assert not [
        tag for tag in _advisory_tags(classification) if tag.startswith("UNKNOWN_KEYS")
    ]


def test_unconfigured_alias_is_not_honored(tmp_path: Path) -> None:
    """AC-4/G3: an alias outside the configured map is never silently coerced."""
    workspace = _materialize(tmp_path, "alias_exclusion_reason_code")
    contract = _agent_lane_contract(reason_code_aliases={})
    _, classification = _only(workspace, contract)
    assert classification.tier == dc.TIER_DEBT
    assert "ALIAS_REASON_CODE:exclusion_reason_code" not in _debt_tags(classification)
    assert "REASON_CODE_ABSENT" in _debt_tags(classification)
    assert classification.canonical_rows[0]["reason_code"] is None


# ---------------------------------------------------------------------------
# AC-5 / AC-6 / AC-7 -- confidence
# ---------------------------------------------------------------------------


def test_missing_confidence_is_debt_with_a_none_value(tmp_path: Path) -> None:
    """AC-5: an absent confidence is DEBT and the value is None."""
    workspace = _materialize(tmp_path, "missing_confidence")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert "CONFIDENCE_ABSENT" in _debt_tags(classification)
    assert classification.canonical_rows[0]["confidence"] is None


def test_non_numeric_confidence_is_debt_and_invents_no_number(
    tmp_path: Path,
) -> None:
    """AC-6: a non-numeric confidence yields None and no numeric value."""
    workspace = _materialize(tmp_path, "non_numeric_confidence")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert "CONFIDENCE_NON_NUMERIC" in _debt_tags(classification)
    for row in classification.canonical_rows:
        assert row["confidence"] is None
    out = tmp_path / "report.json"
    cmd_validate(workspace, out=out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ledger"]["debt_tag_counts"] == {"CONFIDENCE_NON_NUMERIC": 2}
    serialized = out.read_text(encoding="utf-8")
    assert '"confidence": null' in serialized
    for numeric in ("0.0", "1.0", "0.5", "0.9", "0.8"):
        assert numeric not in serialized, f"numeric default {numeric} leaked"


def test_out_of_range_confidence_is_debt_with_a_none_value(tmp_path: Path) -> None:
    """AC-7: an out-of-range confidence is DEBT and the value is None."""
    workspace = _materialize(tmp_path, "out_of_range_confidence")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert "CONFIDENCE_OUT_OF_RANGE" in _debt_tags(classification)
    for row in classification.canonical_rows:
        assert row["confidence"] is None


# ---------------------------------------------------------------------------
# AC-8 / AC-9 / AC-10 -- rationale and reason code
# ---------------------------------------------------------------------------


def test_rationale_only_under_the_fallback_key_is_debt(tmp_path: Path) -> None:
    """AC-8: a rationale that only sits under the fallback key is DEBT."""
    workspace = _materialize(tmp_path, "rationale_in_reason_only")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert "RATIONALE_IN_REASON_ONLY" in _debt_tags(classification)
    for row in classification.canonical_rows:
        assert row["one_line_support"] is None


def test_absent_reason_code_is_debt(tmp_path: Path) -> None:
    """AC-9: an absent reason code is DEBT, never fabricated."""
    workspace = _materialize(tmp_path, "absent_reason_code")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert "REASON_CODE_ABSENT" in _debt_tags(classification)
    for row in classification.canonical_rows:
        assert row["reason_code"] is None


def test_reason_code_embedded_in_text_is_extracted_and_tagged(tmp_path: Path) -> None:
    """AC-10: a code recoverable only from the text is extracted and tagged."""
    workspace = _materialize(tmp_path, "embedded_reason_code")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert "REASON_CODE_EMBEDDED_IN_TEXT" in _debt_tags(classification)
    assert classification.canonical_rows[0]["reason_code"] == "OUT_OF_SCOPE_CODE"


# ---------------------------------------------------------------------------
# AC-11 -- unknown keys
# ---------------------------------------------------------------------------


def test_unknown_keys_are_advisory_and_never_bad(tmp_path: Path) -> None:
    """AC-11/D2: unknown keys are surfaced as an advisory, never as a defect.

    A2: an advisory finding marks the file ``DEBT`` (it is a deviation from
    the frozen instrument's allowed field list), but it is never ``BAD``.
    """
    workspace = _materialize(tmp_path, "unknown_keys")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_DEBT
    assert classification.structural == ()
    assert "UNKNOWN_KEYS:operator_note" in _advisory_tags(classification)
    assert _debt_tags(classification) == []


# ---------------------------------------------------------------------------
# AC-12 .. AC-23 -- structural findings
# ---------------------------------------------------------------------------


def test_row_without_canonical_or_alias_field_is_bad(tmp_path: Path) -> None:
    """AC-12: a foreign-schema row carries no decodable canonical field."""
    workspace = _materialize(tmp_path, "no_canonical_field")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "ROW_0_NO_CANONICAL_FIELDS" in classification.structural
    assert "ROW_0_MISSING_SCREENING_ID" in classification.structural
    assert any(
        code.startswith("ROW_0_DECISION_OUT_OF_VOCAB")
        for code in classification.structural
    )


def test_unattested_header_is_bad(tmp_path: Path) -> None:
    """AC-13: a screener id that does not match the file family is BAD."""
    workspace = _materialize(tmp_path, "header_unattested")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "HEADER_UNATTESTED" in _codes(classification)


def test_absent_screener_id_is_bad(tmp_path: Path) -> None:
    """AC-13: a header without a screener id is unattested and BAD."""
    workspace = _materialize(tmp_path, "missing_screener_id")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "HEADER_UNATTESTED" in _codes(classification)
    assert classification.header["screener_id"] is None


def test_absent_instrument_sha_is_bad_when_a_prefix_is_configured(
    tmp_path: Path,
) -> None:
    """AC-13: an instrument that is not attested at all is BAD."""
    workspace = _materialize(
        tmp_path, "missing_instrument", contract="agent_lane_with_sha"
    )
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "CRITERIA_SHA_MISSING" in _codes(classification)
    assert "PROMPT_SHA_MISSING" in _codes(classification)


def test_row_count_mismatch_against_the_parent_manifest_is_bad(tmp_path: Path) -> None:
    """AC-14: the parent manifest is the row-count authority."""
    workspace = _materialize(tmp_path, "row_count_mismatch")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "ROW_COUNT:2!=3" in classification.structural


def test_id_order_mismatch_against_the_parent_view_is_bad(tmp_path: Path) -> None:
    """AC-15: the parent view is the id-order authority."""
    workspace = _materialize(tmp_path, "id_order_mismatch")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "ID_ORDER_MISMATCH_VS_VIEW" in _codes(classification)


def test_wrong_workspace_ids_are_bad(tmp_path: Path) -> None:
    """Negative case 2: ids from another corpus fail the parent-view check."""
    workspace = _materialize(tmp_path, "wrong_workspace_ids")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "ID_ORDER_MISMATCH_VS_VIEW" in _codes(classification)


def test_missing_screening_id_is_bad(tmp_path: Path) -> None:
    """AC-16: a row without an identifier is BAD."""
    workspace = _materialize(tmp_path, "missing_screening_id")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "ROW_1_MISSING_SCREENING_ID" in classification.structural


def test_empty_screening_id_is_bad(tmp_path: Path) -> None:
    """AC-16 / negative case 5: an empty identifier is BAD."""
    workspace = _materialize(tmp_path, "empty_screening_id")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "ROW_1_MISSING_SCREENING_ID" in classification.structural


def test_decision_outside_the_vocabulary_is_bad(tmp_path: Path) -> None:
    """AC-17: a decision outside the configured vocabulary is BAD."""
    workspace = _materialize(tmp_path, "decision_out_of_vocab")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert any(
        code.startswith("ROW_1_DECISION_OUT_OF_VOCAB")
        for code in classification.structural
    )


def test_non_canonical_filename_is_surfaced(tmp_path: Path) -> None:
    """AC-18 / negative case 9: a padded file name is surfaced, not invisible."""
    workspace = _materialize(tmp_path, "non_canonical_filename")
    _contract, classifications = _classifications(workspace)
    assert len(classifications) == 1
    classification = classifications[0]
    assert classification.file == "batch_000001_decisions_A1.json"
    assert classification.tier == dc.TIER_BAD
    assert "FILENAME_NOT_CANONICAL" in _codes(classification)
    assert (
        classification.header["canonical_file_name"] == "batch_0001_decisions_A1.json"
    )
    assert classification.header["file_name_canonical"] is False


def test_bom_prefixed_file_is_bad_with_the_explicit_code(tmp_path: Path) -> None:
    """AC-19: a BOM produces the explicit BOM_DETECTED finding."""
    workspace = _materialize(tmp_path, "bom_prefixed")
    path = _screening_dir(workspace) / "batch_0001_decisions_A1.json"
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "BOM_DETECTED" in _codes(classification)
    assert not [
        code for code in classification.structural if code.startswith("JSON_PARSE")
    ]


def test_malformed_json_is_bad_with_a_json_parse_code(tmp_path: Path) -> None:
    """AC-20: an unparseable file is BAD with JSON_PARSE."""
    workspace = _materialize(tmp_path, "malformed_json")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert any(code.startswith("JSON_PARSE:") for code in classification.structural)


def test_missing_parent_is_bad_not_a_silent_pass(tmp_path: Path) -> None:
    """AC-21 / negative case 1: absent parents fail closed."""
    workspace = _materialize(tmp_path, "missing_parent", parents=False)
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "PARENT_MISSING" in _codes(classification)


def test_stale_instrument_fingerprint_is_bad(tmp_path: Path) -> None:
    """AC-22 / negative case 3: an attested SHA that does not match is BAD."""
    workspace = _materialize(
        tmp_path, "stale_instrument", contract="agent_lane_with_sha"
    )
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "CRITERIA_SHA_MISMATCH" in _codes(classification)
    assert classification.header["criteria_sha256_attested"] is False


def test_matching_instrument_fingerprint_is_attested(tmp_path: Path) -> None:
    """AC-22: a matching configured prefix attests the instrument."""
    workspace = _materialize(tmp_path, "canonical", contract="agent_lane_with_sha")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_VALID
    assert classification.header["criteria_sha256_attested"] is True
    assert classification.header["prompt_template_sha256_attested"] is True


def test_unsupported_schema_major_is_bad(tmp_path: Path) -> None:
    """AC-23 / negative case 4: an unknown major version is BAD."""
    workspace = _materialize(tmp_path, "canonical", contract="unsupported_major")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "SCHEMA_VERSION_UNSUPPORTED" in _codes(classification)


def test_unsupported_schema_major_refuses_the_command(tmp_path: Path) -> None:
    """AC-23: the command publishes nothing on an unusable contract."""
    workspace = _materialize(tmp_path, "canonical", contract="unsupported_major")
    out = tmp_path / "report.json"
    with pytest.raises(SystemExit) as excinfo:
        cmd_validate(workspace, out=out)
    assert excinfo.value.code == 1
    assert not out.exists()


# ---------------------------------------------------------------------------
# AC-24 / AC-25 / negative case 11 -- no producer mutation, no publication
# ---------------------------------------------------------------------------


def test_reader_never_writes_into_the_decisions_directory(tmp_path: Path) -> None:
    """AC-24 / negative case 11: the decisions tree is byte-identical.

    A1/D3: the default report path lives outside the scanned directory, so
    the literal AC-24 wording holds -- the decisions tree is unchanged
    (paths, bytes, and mtimes) after a default run.
    """
    workspace = _materialize(tmp_path, "canonical")
    screening = _screening_dir(workspace)
    before = _snapshot(screening)
    cmd_validate(workspace)
    after = _snapshot(screening)
    assert before == after
    report = (
        workspace / "literature" / "screening_reports" / "decision_contract_report.json"
    )
    assert report.is_file()
    assert not (screening / "decision_contract_report.json").exists()


def test_reader_never_modifies_a_producer_file_even_when_the_report_is_inside(
    tmp_path: Path,
) -> None:
    """AC-24/G8: writing the report inside the tree changes no producer file."""
    workspace = _materialize(tmp_path, "canonical")
    screening = _screening_dir(workspace)
    before = _snapshot(screening)
    cmd_validate(workspace, out=screening / "decision_contract_report.json")
    after = _snapshot(screening)
    added = set(after) - set(before)
    assert added == {"decision_contract_report.json"}
    for name, (payload, mtime) in before.items():
        assert after[name] == (payload, mtime), f"{name} was modified"


def test_reader_does_not_reingest_its_own_report(tmp_path: Path) -> None:
    """D1: a second run with a different --out sees exactly the same corpus."""
    workspace = _materialize(tmp_path, "canonical")
    first = tmp_path / "first" / "decision_contract_report.json"
    cmd_validate(workspace, out=first)
    first_report = json.loads(first.read_text(encoding="utf-8"))
    second = tmp_path / "second" / "decision_contract_report.json"
    cmd_validate(workspace, out=second)
    second_report = json.loads(second.read_text(encoding="utf-8"))
    assert (
        second_report["ledger"]["files_scanned"]
        == (first_report["ledger"]["files_scanned"])
    )
    assert (
        second_report["ledger"]["files_by_tier"]
        == (first_report["ledger"]["files_by_tier"])
    )


def test_reader_does_not_reingest_a_report_written_into_the_decisions_directory(
    tmp_path: Path,
) -> None:
    """D1: the report sidecar is excluded by name, not only by output path."""
    workspace = _materialize(tmp_path, "canonical")
    screening = _screening_dir(workspace)
    first = screening / "decision_contract_report.json"
    cmd_validate(workspace, out=first)
    first_report = json.loads(first.read_text(encoding="utf-8"))
    second = tmp_path / "second" / "decision_contract_report.json"
    cmd_validate(workspace, out=second)
    second_report = json.loads(second.read_text(encoding="utf-8"))
    assert first_report["ledger"]["files_scanned"] == 1
    assert (
        second_report["ledger"]["files_scanned"]
        == (first_report["ledger"]["files_scanned"])
    )
    assert (
        second_report["ledger"]["files_by_tier"]
        == (first_report["ledger"]["files_by_tier"])
    )
    assert [entry["file"] for entry in second_report["files"]] == [
        "batch_0001_decisions_A1.json"
    ]


def test_reader_does_not_reingest_the_contract_configuration(
    tmp_path: Path,
) -> None:
    """D1: the contract configuration is excluded by name as well."""
    workspace = _materialize(tmp_path, "canonical")
    screening = _screening_dir(workspace)
    assert (screening / "decision_contract.json").is_file()
    out = tmp_path / "report.json"
    cmd_validate(workspace, out=out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ledger"]["files_scanned"] == 1
    assert [entry["file"] for entry in report["files"]] == [
        "batch_0001_decisions_A1.json"
    ]


def test_reader_never_publishes_contract_v1_artifacts(tmp_path: Path) -> None:
    """AC-25: no Contract v1 artifact and no partition output is written."""
    workspace = _materialize(tmp_path, "canonical")
    cmd_validate(workspace, out=tmp_path / "report.json")
    literature = workspace / "literature"
    for name in (
        "included.json",
        "excluded.json",
        "prisma_screening_report.md",
        "prisma_report.json",
        "conflicts.json",
    ):
        assert not (literature / name).exists(), f"{name} must not be published"
    assert not (workspace / "audit" / "artifact_registry.json").exists()
    assert not list((workspace / "audit").glob("artifacts/**/*"))


# ---------------------------------------------------------------------------
# AC-26 / AC-27 -- determinism and idempotency
# ---------------------------------------------------------------------------


def test_two_runs_produce_byte_identical_reports(tmp_path: Path) -> None:
    """AC-26: the same inputs produce byte-identical report content."""
    workspace = _materialize(tmp_path, "canonical")
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    cmd_validate(workspace, out=first)
    cmd_validate(workspace, out=second)
    assert first.read_bytes() == second.read_bytes()


def test_second_run_refuses_with_report_exists(tmp_path: Path) -> None:
    """AC-27 / negative case 6: a second run refuses and mutates nothing."""
    workspace = _materialize(tmp_path, "canonical")
    out = tmp_path / "report.json"
    cmd_validate(workspace, out=out)
    original = out.read_bytes()
    with pytest.raises(SystemExit) as excinfo:
        cmd_validate(workspace, out=out)
    assert excinfo.value.code == 1
    assert out.read_bytes() == original


# ---------------------------------------------------------------------------
# AC-28 -- ledger reconciliation
# ---------------------------------------------------------------------------


def test_debt_ledger_reconciles(tmp_path: Path) -> None:
    """AC-28: per-file and per-tag counts reconcile with the classifications."""
    workspace = _materialize_batches(
        tmp_path,
        ["canonical", "alias_exclusion_reason_code", "missing_confidence"],
    )
    _contract, classifications = _classifications(workspace)
    ledger = build_debt_ledger(classifications)
    assert sum(ledger["files_by_tier"].values()) == ledger["files_scanned"]
    assert ledger["files_scanned"] == len(classifications)
    per_file = {entry["file"]: entry["tier"] for entry in ledger["files"]}
    for classification in classifications:
        assert per_file[classification.file] == classification.tier
    assert ledger["files_by_tier"]["VALID"] == 1
    assert ledger["files_by_tier"]["DEBT"] == 2
    assert ledger["files_by_tier"]["BAD"] == 0
    assert ledger["debt_tag_counts"]["CONFIDENCE_ABSENT"] == 2
    assert ledger["debt_tag_counts"]["ALIAS_REASON_CODE:exclusion_reason_code"] == 2
    assert ledger["rows_scanned"] == 6


# ---------------------------------------------------------------------------
# AC-29 -- command surface and audit event
# ---------------------------------------------------------------------------


def test_validate_command_writes_a_report_and_logs_one_audit_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-29: one report, one per-tier summary, exactly one audit event."""
    workspace = _materialize(tmp_path, "canonical")
    calls: list[tuple[tuple, dict]] = []

    def _record(*args, **kwargs):
        calls.append((args, kwargs))
        return {"event_id": "EVT-TEST"}

    monkeypatch.setattr(dc, "log_event", _record)
    cmd_validate(workspace)

    out = (
        workspace / "literature" / "screening_reports" / "decision_contract_report.json"
    )
    assert out.is_file()
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ledger"]["files_by_tier"]["VALID"] == 1
    assert report["ledger"]["files_by_tier"]["DEBT"] == 0
    assert report["ledger"]["files_by_tier"]["BAD"] == 0
    assert report["tier_rule"] == dc.TIER_RULE

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[1] == dc.AUDIT_ACTION
    assert kwargs["agent"] == dc.AUDIT_AGENT
    assert kwargs["status"] == "SUCCESS"
    assert kwargs["outputs"] == [
        "literature/screening_reports/decision_contract_report.json"
    ]
    assert kwargs["metrics"] == {
        "files_scanned": 1,
        "valid": 1,
        "debt": 0,
        "bad": 0,
        "debt_tag_count": 0,
        "scan_finding_count": 0,
        "scan_findings": [],
    }
    assert "1 VALID / 0 DEBT / 0 BAD" in args[2]
    assert "literature/screening/decision_contract.json" in kwargs["inputs"]


def test_validate_command_prints_a_per_tier_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """AC-29: the command prints one summary line with the tier counts."""
    workspace = _materialize(tmp_path, "canonical")
    cmd_validate(workspace, out=tmp_path / "report.json")
    captured = capsys.readouterr()
    assert "VALID 1 / DEBT 0 / BAD 0" in captured.out


def test_validate_command_appends_exactly_one_journal_event(tmp_path: Path) -> None:
    """AC-29/G12: the real audit writer records the run in the journal."""
    workspace = _materialize(tmp_path, "canonical")
    cmd_validate(workspace)
    rows = [
        row for row in _journal_rows(workspace) if row.get("action") == dc.AUDIT_ACTION
    ]
    assert len(rows) == 1
    assert rows[0]["agent_or_tool"] == dc.AUDIT_AGENT
    assert rows[0]["status"] == "SUCCESS"
    assert rows[0]["metrics"]["files_scanned"] == 1
    assert rows[0]["outputs"] == [
        "literature/screening_reports/decision_contract_report.json"
    ]


def test_refused_run_logs_a_failed_audit_event(tmp_path: Path) -> None:
    """G12: a refusal is recorded with a truthful FAILED status."""
    workspace = _materialize(tmp_path, "canonical")
    out = tmp_path / "report.json"
    cmd_validate(workspace, out=out)
    with pytest.raises(SystemExit):
        cmd_validate(workspace, out=out)
    rows = [
        row for row in _journal_rows(workspace) if row.get("action") == dc.AUDIT_ACTION
    ]
    assert len(rows) == 2
    assert rows[-1]["status"] == "FAILED"
    assert "REPORT_EXISTS" in rows[-1]["description"]


# ---------------------------------------------------------------------------
# AC-30 -- existing command surface is unchanged
# ---------------------------------------------------------------------------


EXISTING_HELP_FRAGMENTS = {
    "calibration": (
        "usage: agent_screen.py calibration",
        "--sample-size",
        "--gold-file",
    ),
    "calibrate-eval": ("usage: agent_screen.py calibrate-eval",),
    "prepare": (
        "usage: agent_screen.py prepare",
        "--batch-size",
        "--force",
        "Overwrite existing batch files",
    ),
    "status": ("usage: agent_screen.py status",),
    "collect": ("usage: agent_screen.py collect",),
    "recommend": ("usage: agent_screen.py recommend", "--batch"),
    "review": ("usage: agent_screen.py review", "--batch"),
    "approve": (
        "usage: agent_screen.py approve",
        "--decisions-file",
        "--message",
        "--begin",
    ),
    "defer": ("usage: agent_screen.py defer", "--reason"),
}


@pytest.mark.parametrize("command", sorted(EXISTING_HELP_FRAGMENTS))
def test_existing_subcommand_help_text_is_unchanged(command: str) -> None:
    """AC-30: the pre-existing subcommands keep their help text."""
    environment = dict(os.environ, COLUMNS="80")
    result = subprocess.run(
        [sys.executable, str(CLI), command, "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    for fragment in EXISTING_HELP_FRAGMENTS[command]:
        assert fragment in result.stdout
    assert "validate" not in result.stdout


def test_validate_subcommand_is_exposed() -> None:
    """AC-29: the new subcommand is a first-class, re-runnable command."""
    environment = dict(os.environ, COLUMNS="80")
    result = subprocess.run(
        [sys.executable, str(CLI), "validate", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert "usage: agent_screen.py validate" in result.stdout
    assert "--out" in result.stdout
    assert "--contract" in result.stdout


# ---------------------------------------------------------------------------
# Negative case 10 -- prompt-authority inversion
# ---------------------------------------------------------------------------


def test_producer_self_report_never_overrides_the_parent_manifest(
    tmp_path: Path,
) -> None:
    """Negative case 10 / D5: a producer self-report never wins.

    The decision file copies its own record count into an ``n_records``
    header; the parent batch manifest remains the authority and the
    disagreement is reported as ``SELF_REPORT_COUNT_MISMATCH``.
    """
    workspace = _materialize(tmp_path, "self_report_count_mismatch")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "SELF_REPORT_COUNT_MISMATCH:5!=2" in classification.structural
    # The manifest count (2) agrees with the row count, so no row-count
    # mismatch is invented: only the self-report disagreement is reported.
    assert not [
        code for code in classification.structural if code.startswith("ROW_COUNT")
    ]


def test_no_invented_prompt_count_key_is_read() -> None:
    """D5: the invented ``prompt_n_records`` key is gone from the module."""
    source = (SRC_ROOT / "decision_contract.py").read_text(encoding="utf-8")
    assert "prompt_n_records" not in source
    assert "PROMPT_COUNT_MISMATCH" not in source
    assert "SELF_REPORT_COUNT_MISMATCH" in source


# ---------------------------------------------------------------------------
# Repair round 1 -- D2 / D4 / D6 / D7 / D8
# ---------------------------------------------------------------------------


def test_harness_lane_names_classify_with_the_default_contract(
    tmp_path: Path,
) -> None:
    """D4/A3: the harness lane's own file names classify with the defaults.

    ``batch_001.json`` states its record count as ``batch_size`` and
    ``batch_001_decisions.json`` carries the agent-lane rows; the default
    contract must accept that layout without a config file.
    """
    workspace = _materialize(tmp_path, "harness_lane", contract=None, parents=False)
    contract = default_contract()
    _, classification = _only(workspace, contract)
    assert classification.file == "batch_001_decisions.json"
    assert classification.header["file_name_canonical"] is True
    assert classification.header["batch_index"] == 1
    assert classification.header["parent_batch_resolved"] is True
    assert classification.rows == 2
    assert classification.tier == dc.TIER_VALID
    assert classification.structural == ()


def test_scan_without_any_resolved_parent_is_loud(tmp_path: Path) -> None:
    """D4/A3/R2: a scan in which no parent resolves is not silently all-bad."""
    workspace = _materialize(tmp_path, "canonical", parents=False)
    out = tmp_path / "report.json"
    with pytest.raises(SystemExit):
        cmd_validate(workspace, out=out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ledger"]["files_by_tier"]["BAD"] == 1
    assert report["parent_resolution"] == {
        "files_scanned": 1,
        "files_with_parents": 0,
        "files_without_parents": 1,
    }
    assert report["scan_findings"] == ["NO_PARENTS_RESOLVED"]
    rows = [
        row for row in _journal_rows(workspace) if row.get("action") == dc.AUDIT_ACTION
    ]
    assert rows[-1]["metrics"]["scan_finding_count"] == 1
    assert "NO_PARENTS_RESOLVED" in rows[-1]["description"]


def test_decisions_dir_flag_reaches_a_nested_lane(tmp_path: Path) -> None:
    """D6/A4: a workspace-relative decisions directory reaches another lane."""
    workspace = tmp_path / "ws"
    nested = workspace / "calibration_v03" / "screening_scr1" / "decisions"
    nested.mkdir(parents=True)
    (workspace / "project.json").write_text(
        json.dumps({"project_slug": "fixture-workspace", "stats": {}}), encoding="utf-8"
    )
    shutil.copyfile(
        SCENARIOS / "canonical" / "batch_0001_decisions_A1.json",
        nested / "batch_0001_decisions_A1.json",
    )
    for name in ("batch_0001.json", "batch_0001.view.json"):
        shutil.copyfile(PARENTS / name, nested / name)
    contract_path = workspace / "literature" / "screening" / "decision_contract.json"
    contract_path.parent.mkdir(parents=True)
    shutil.copyfile(CONTRACTS / "agent_lane.json", contract_path)

    out = tmp_path / "report.json"
    cmd_validate(
        workspace,
        out=out,
        decisions_dir="calibration_v03/screening_scr1/decisions",
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ledger"]["files_scanned"] == 1
    assert report["ledger"]["files_by_tier"]["VALID"] == 1
    assert report["scan_findings"] == []


def test_missing_workspace_root_refuses_without_logging(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """D7: a mistyped workspace path never materialises a ledger."""
    missing = tmp_path / "does-not-exist"
    with pytest.raises(SystemExit) as excinfo:
        cmd_validate(missing)
    assert excinfo.value.code == 1
    assert "WORKSPACE_MISSING" in capsys.readouterr().err
    assert not missing.exists()
    assert not (tmp_path / "audit").exists()


def test_docstring_names_the_public_vocabulary() -> None:
    """D8: the docstring names every public name it omits before."""
    flat = " ".join((dc.__doc__ or "").split())
    for name in (
        "tag_prefix",
        "TIERS",
        "DEBT_PREFIXES",
        "ADVISORY_PREFIXES",
        "STRUCTURAL_CODES",
    ):
        assert name in flat, f"{name} is not documented in the module docstring"
    # The reviewer's disambiguation line.
    assert "``DecisionContract`` **type**" in flat
    assert "not the Contract v1" in flat
    assert "scholar_harness.contracts" in flat


def test_report_states_the_tier_rule(tmp_path: Path) -> None:
    """D2/A2: the report states the tier rollup it applied."""
    workspace = _materialize(tmp_path, "canonical")
    out = tmp_path / "report.json"
    cmd_validate(workspace, out=out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["tier_rule"] == dc.TIER_RULE
    assert "advisory" in report["tier_rule"]
    assert report["tier_vocabulary"] == ["VALID", "DEBT", "BAD"]


def test_advisory_findings_mark_the_file_debt(tmp_path: Path) -> None:
    """D2/A2: an advisory-only file is DEBT, never VALID."""
    workspace = _materialize(tmp_path, "unknown_keys")
    _, classification = _only(workspace)
    assert set(_advisory_tags(classification)) == {"UNKNOWN_KEYS:operator_note"}
    assert len(_advisory_tags(classification)) == 2
    assert _debt_tags(classification) == []
    assert classification.tier == dc.TIER_DEBT


def test_validate_subcommand_exposes_the_decisions_dir_flag() -> None:
    """D6/A4: the CLI exposes the workspace-relative decisions directory."""
    environment = dict(os.environ, COLUMNS="80")
    result = subprocess.run(
        [sys.executable, str(CLI), "validate", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert "--decisions-dir" in result.stdout
    assert "literature/screening" in result.stdout


# ---------------------------------------------------------------------------
# Repair round 2 -- R1 / R2 / N1 / N2
# ---------------------------------------------------------------------------


def test_reordered_harness_lane_file_is_not_valid(tmp_path: Path) -> None:
    """R1/B1.5: a reordered harness-lane file must not come out VALID.

    Under the default contract there is no view, so the parent batch's
    ordered ``papers[]`` list is the id-order authority -- and the two sides
    carry their ids under different keys (``workspace_id`` in the batch,
    ``screening_id`` in the row).
    """
    workspace = _materialize(
        tmp_path, "harness_lane_reordered", contract=None, parents=False
    )
    contract = default_contract()
    _, classification = _only(workspace, contract)
    assert classification.tier == dc.TIER_BAD
    assert "ID_ORDER_MISMATCH_VS_BATCH" in _codes(classification)
    assert classification.header["id_order_authority"] == "batch"


def test_id_order_not_verifiable_when_the_parent_yields_no_ids(
    tmp_path: Path,
) -> None:
    """R1/B1.3: an unresolvable parent id list is reported, never passed."""
    workspace = _materialize(
        tmp_path, "id_order_not_verifiable", contract=None, parents=False
    )
    contract = default_contract()
    _, classification = _only(workspace, contract)
    assert classification.tier == dc.TIER_BAD
    assert "ID_ORDER_NOT_VERIFIABLE" in _codes(classification)


def test_id_order_not_verifiable_when_a_row_yields_no_id(tmp_path: Path) -> None:
    """R1/B1.3: a row without the canonical id makes the order unverifiable."""
    workspace = _materialize(tmp_path, "missing_screening_id")
    _, classification = _only(workspace)
    assert classification.tier == dc.TIER_BAD
    assert "ID_ORDER_NOT_VERIFIABLE" in _codes(classification)
    assert "ROW_1_MISSING_SCREENING_ID" in classification.structural


def test_id_order_check_cannot_pass_vacuously(tmp_path: Path) -> None:
    """R1: the id comparison is incapable of a None-versus-None pass.

    The parent list carries ids under ``workspace_id`` and the rows under
    ``screening_id``; the implementation resolves each side explicitly and
    refuses to compare when either side yields no id.
    """
    source = (SRC_ROOT / "decision_contract.py").read_text(encoding="utf-8")
    assert "PARENT_ID_KEYS" in source
    assert "canonical_id_field" in source
    assert "ID_ORDER_NOT_VERIFIABLE" in source
    assert "ID_ORDER_MISMATCH_VS_BATCH" in source
    # A row id is read under exactly one field, never a chain that could
    # resolve to None on both sides.
    row_ids = dc._row_ids([{"screening_id": "A"}], "screening_id")
    assert row_ids == ["A"]
    assert dc._row_ids([{"workspace_id": "A"}], "screening_id") == [None]
    assert dc._row_ids([{"screening_id": ""}], "screening_id") == [None]
    # The parent side resolves under the first key present.
    assert dc._extract_ordered_ids({"papers": [{"workspace_id": "A"}]}) == ["A"]
    assert dc._extract_ordered_ids({"papers": [{"title": "x"}]}) == [None]
    assert dc._extract_ordered_ids({"records": [{"screening_id": "B"}]}) == ["B"]


def test_scan_with_no_resolved_parent_is_failed(tmp_path: Path) -> None:
    """R2/B2 (i): files found but no parent resolved -> FAILED, non-zero."""
    workspace = _materialize(tmp_path, "canonical", parents=False)
    out = tmp_path / "report.json"
    with pytest.raises(SystemExit) as excinfo:
        cmd_validate(workspace, out=out)
    assert excinfo.value.code == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["scan_findings"] == ["NO_PARENTS_RESOLVED"]
    rows = [
        row for row in _journal_rows(workspace) if row.get("action") == dc.AUDIT_ACTION
    ]
    assert rows[-1]["status"] == "FAILED"
    assert rows[-1]["metrics"]["scan_findings"] == ["NO_PARENTS_RESOLVED"]
    assert "NO_PARENTS_RESOLVED" in rows[-1]["description"]


def test_scan_with_no_decision_files_is_failed(tmp_path: Path) -> None:
    """R2/B2 (ii): an empty scan is a distinct failure, not an empty success."""
    workspace = tmp_path / "ws"
    screening = _screening_dir(workspace)
    screening.mkdir(parents=True)
    (workspace / "project.json").write_text(
        json.dumps({"project_slug": "fixture-workspace", "stats": {}}), encoding="utf-8"
    )
    shutil.copyfile(CONTRACTS / "agent_lane.json", screening / "decision_contract.json")
    out = tmp_path / "report.json"
    with pytest.raises(SystemExit) as excinfo:
        cmd_validate(workspace, out=out)
    assert excinfo.value.code == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["scan_findings"] == ["NO_DECISION_FILES"]
    assert report["ledger"]["files_scanned"] == 0
    rows = [
        row for row in _journal_rows(workspace) if row.get("action") == dc.AUDIT_ACTION
    ]
    assert rows[-1]["status"] == "FAILED"
    assert rows[-1]["metrics"]["scan_findings"] == ["NO_DECISION_FILES"]
    assert "NO_DECISION_FILES" in rows[-1]["description"]
    # The reason text must make the cause legible, not mysterious.
    assert (
        "--decisions-dir" in rows[-1]["description"]
        or "mis-pointed" in (rows[-1]["description"])
    )


def test_normal_scan_with_debt_is_success(tmp_path: Path) -> None:
    """R2/B2 (iii): a normal scan, DEBT and/or BAD present, is SUCCESS."""
    workspace = _materialize(tmp_path, "alias_exclusion_reason_code")
    out = tmp_path / "report.json"
    assert cmd_validate(workspace, out=out) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["scan_findings"] == []
    rows = [
        row for row in _journal_rows(workspace) if row.get("action") == dc.AUDIT_ACTION
    ]
    assert rows[-1]["status"] == "SUCCESS"
    assert rows[-1]["metrics"]["scan_findings"] == []


def test_validate_help_pins_the_current_default_report_path() -> None:
    """N1/B3: the --out help names the real default, in full.

    argparse hard-wraps a long token at the terminal width, so the rendered
    help is compared with all whitespace removed -- that rejoins the broken
    path and keeps the assertion independent of the column width.
    """
    environment = dict(os.environ, COLUMNS="80")
    result = subprocess.run(
        [sys.executable, str(CLI), "validate", "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    compact = "".join(result.stdout.split())
    assert "literature/screening_reports/decision_contract_report.json" in compact
    assert "literature/screening/decision_contract_report.json" not in compact
    source = (ROOT / "src" / "scholar_harness" / "agent_screen.py").read_text(
        encoding="utf-8"
    )
    assert "literature/screening_reports/" in source
    assert "literature/screening/decision_contract_report.json" not in source


def test_advisory_vocabulary_comment_matches_the_rollup() -> None:
    """N2/B4: the advisory comment no longer denies a tier change."""
    source = (SRC_ROOT / "decision_contract.py").read_text(encoding="utf-8")
    assert "never a tier change" not in source
    assert "advisory findings mark the file" in source


# ---------------------------------------------------------------------------
# Negative case 12 -- vacuous-green guard
# ---------------------------------------------------------------------------


def test_validator_can_fail_on_a_deliberately_malformed_fixture(
    tmp_path: Path,
) -> None:
    """Negative case 12: a validator that cannot fail proves nothing."""
    workspace = _materialize(tmp_path, "malformed_json")
    _, classification = _only(workspace)
    assert classification.structural, "a malformed fixture must produce findings"
    assert classification.tier == dc.TIER_BAD


def test_all_three_tiers_are_reachable(tmp_path: Path) -> None:
    """Negative case 12: the scenario corpus exercises VALID, DEBT, and BAD."""
    tiers = set()
    for index, scenario in enumerate(
        ("canonical", "missing_confidence", "malformed_json")
    ):
        workspace = _materialize(tmp_path / f"case{index}", scenario)
        _, classification = _only(workspace)
        tiers.add(classification.tier)
    assert tiers == {dc.TIER_VALID, dc.TIER_DEBT, dc.TIER_BAD}


# ---------------------------------------------------------------------------
# Row-level unit surface
# ---------------------------------------------------------------------------


def test_normalize_row_returns_verbatim_values_or_none() -> None:
    """G3: normalize_row copies verbatim or returns None -- never a default."""
    contract = DecisionContract.from_dict(
        {
            "reason_code_aliases": {"alt_reason_code": "reason_code"},
            "embedded_reason_code_pattern": r"\b([A-Z][A-Z0-9_]{2,})\b",
        }
    )
    canonical, tags = normalize_row(
        {
            "screening_id": "REC-1",
            "decision": "INCLUDE",
            "alt_reason_code": "CODE_X",
            "confidence": 0.5,
            "one_line_support": "decisive signal",
            "extra_key": "kept by the producer",
        },
        contract,
    )
    assert canonical["reason_code"] == "CODE_X"
    assert canonical["confidence"] == 0.5
    assert tags == ["ALIAS_REASON_CODE:alt_reason_code", "UNKNOWN_KEYS:extra_key"]


def test_ledger_is_deterministically_ordered(tmp_path: Path) -> None:
    """AC-28: the ledger order does not depend on the input order."""
    workspace = _materialize_batches(tmp_path, ["canonical", "missing_confidence"])
    _contract, classifications = _classifications(workspace)
    forward = build_debt_ledger(classifications)
    backward = build_debt_ledger(list(reversed(classifications)))
    assert forward == backward
    assert [entry["file"] for entry in forward["files"]] == sorted(
        entry["file"] for entry in forward["files"]
    )
