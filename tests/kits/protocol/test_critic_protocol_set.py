"""The M10c critic test set is honest today, without any model.

``tests/fixtures/critic_protocols/`` holds two sound protocols (a scoping review
and a systematic review) and deliberately broken variants of them. These tests
prove only what can be proved with the existing compiler and validator:

* every fixture loads and the manifest and the folder agree;
* the two bases compile and validate without an error or a warning;
* each variant differs from its base exactly in the fields the manifest names;
* the manifest says truthfully which variants existing validation rejects.

They do not test the fixed checks of M10b (that code is written elsewhere) and
they do not score a critic (M10c does that; see the folder's ``README.md``).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scholar_protocol.canonical import canonical_fingerprint, canonical_json
from scholar_protocol.compiler import compile_protocol
from scholar_protocol.intent import IntentPacket
from scholar_protocol.validate import validate_protocol

ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "critic_protocols"
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
VARIANTS: list[dict[str, Any]] = MANIFEST["variants"]
NONE = "none: critic only"
SEVERITIES = {"critical", "major", "minor"}
REJECTED_BY = {None, "intent_model", "compile", "validate_protocol"}
# What the set must cover (the defect classes the M10c brief names).
# Which fixed check should catch which defect ("<variant>#<defect index>"); pinned here so
# a change of the manifest's assignments is a visible change of this file too.
FIXED_CHECK_ASSIGNMENTS = {
    "scoping-search-omits-weed-concept#0": ["CONCEPT_TERM_MISSING", "PLAN_QUERY_TERM_MISSING"],
    "scoping-one-merged-concept#0": ["CONCEPTS_ONE_ONLY"],
    "scoping-single-seed#0": ["DIRECTION_SEEDS_FEW"],
    "scoping-planned-corpus-too-small#0": ["PLAN_ESTIMATE_ABOVE_TARGET", "HARVEST_ABOVE_TARGET"],
    "scoping-unit-of-analysis-empty#0": ["SHAPE_REQUIRED_MISSING"],
    "scoping-no-exclusion-criterion#0": ["CRITERIA_SIDE_MISSING", "REVIEW_COMPILER_REFUSED"],
    "scoping-exclusion-reasons-uniform#0": ["CRITERIA_REASONS_UNIFORM"],
    "sr-search-omits-uav-concept#0": ["CONCEPT_TERM_MISSING", "PLAN_QUERY_TERM_MISSING"],
    "sr-start-year-missing#0": ["SCOPE_START_YEAR_DEFAULTED"],
    "sr-planned-size-left-to-preset#0": ["SHAPE_PLANNED_SIZE_EMPTY"],
    "sr-planned-size-small-and-query-flooding#0": ["CONCEPTS_ONE_ONLY"],
    "sr-planned-size-small-and-query-flooding#1": ["PLAN_ESTIMATE_ABOVE_TARGET", "HARVEST_ABOVE_TARGET"],
}
REQUIRED_CATEGORIES = {
    "question-criteria-alignment",
    "criteria-consistency",
    "criteria-operationality",
    "search-concepts",
    "search-limits",
    "review-type",
    "seeds",
    "size",
    "completeness",
    "identity",
}


def _load(rel: str) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _resolves(doc: Any, pointer: str) -> bool:
    """True when the JSON pointer names something in ``doc`` (list indexes are integers)."""
    node = doc
    for part in pointer.strip("/").split("/"):
        if isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        elif isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return False
    return True


def _diff(a: Any, b: Any, path: str = "") -> list[str]:
    """Paths (JSON pointer) where ``b`` differs from ``a``.

    Dicts recurse by key; lists of equal length recurse by index; a list whose
    length changed is reported as the list path itself; scalars are reported
    where they differ.
    """
    if type(a) is not type(b):
        return [path or "/"]
    if isinstance(a, dict):
        out: list[str] = []
        for key in sorted(set(a) | set(b)):
            sub = f"{path}/{key}"
            if key not in a or key not in b:
                out.append(sub)
            else:
                out += _diff(a[key], b[key], sub)
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [path]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += _diff(x, y, f"{path}/{i}")
        return out
    return [] if a == b else [path]


def _validate_doc(doc: dict[str, Any]) -> tuple[list[str], list[str]]:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "protocol.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        report = validate_protocol(path)
    return sorted({f.code for f in report.errors}), sorted({f.code for f in report.warnings})


def _existing_validation(variant: dict[str, Any]) -> tuple[str | None, list[str], list[str]]:
    """Run the real compiler and validator on a variant: (rejected_by, errors, warnings)."""
    doc = _load(variant["file"])
    if variant["format"] == "protocol":
        errors, warnings = _validate_doc(doc)
        return ("validate_protocol" if errors else None), errors, warnings
    try:
        intent = IntentPacket.model_validate(doc)
    except ValidationError:
        return "intent_model", [], []
    try:
        protocol = compile_protocol(intent)
    except ValidationError:
        return "compile", [], []
    errors, warnings = _validate_doc(json.loads(canonical_json(protocol)))
    return ("validate_protocol" if errors else None), errors, warnings


# --------------------------------------------------------------------------- manifest and folder


def test_manifest_and_folder_agree() -> None:
    assert MANIFEST["shape"] == "critic-protocols-v1"
    ids = [v["id"] for v in VARIANTS]
    assert len(ids) == len(set(ids)), "duplicate variant id"
    assert 30 <= len(ids) <= 40, f"the brief asks for 30 to 40 variants, got {len(ids)}"

    listed = {v["file"] for v in VARIANTS}
    for base in MANIFEST["bases"].values():
        listed |= {base["intent"], base["protocol"]}
    on_disk = {
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*.json")
        if p.name != "manifest.json"
    }
    assert listed == on_disk, f"missing: {sorted(listed - on_disk)}; orphans: {sorted(on_disk - listed)}"

    for rel in sorted(listed):
        _load(rel)  # every fixture is valid JSON


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v["id"])
def test_manifest_entry_is_complete(variant: dict[str, Any]) -> None:
    assert variant["base"] in MANIFEST["bases"]
    assert variant["format"] in MANIFEST["formats"]
    assert variant["kind"] in {"single", "interacting"}
    assert variant["existing_validation"]["rejected_by"] in REJECTED_BY
    assert variant["rejected_by_existing_validation"] == (
        variant["existing_validation"]["rejected_by"] is not None
    )
    defects = variant["defects"]
    assert len(defects) == (2 if variant["kind"] == "interacting" else 1)
    catalogue = set(MANIFEST["fixed_check_catalogue"]["ids"])
    union: set[str] = set()
    for defect in defects:
        assert defect["severity"] in SEVERITIES
        assert defect["category"] in MANIFEST["categories"]
        assert defect["defect"].strip().endswith(".") and defect["finding"].strip()
        assert defect["fields"], "a defect names the field or fields at fault"
        assert defect["catching_check"] == NONE or defect["catching_check"] in catalogue
        for other in defect.get("also_caught_by", []):
            assert other in catalogue
        union |= set(defect["fields"])
        for locator in defect.get("accepted_locators", []):
            assert locator not in defect["fields"]
    assert sorted(union) == variant["fields"]


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v["id"])
def test_accepted_locators_exist(variant: dict[str, Any]) -> None:
    """A locator that is not an edited field (the other half of a pair) must still exist."""
    base_key = "intent" if variant["format"] == "intent" else "protocol"
    base = _load(MANIFEST["bases"][variant["base"]][base_key])
    doc = _load(variant["file"])
    for defect in variant["defects"]:
        for locator in defect.get("accepted_locators", []):
            assert _resolves(doc, locator) or _resolves(base, locator), locator


def test_fixed_check_assignments_are_pinned() -> None:
    actual = {
        f"{v['id']}#{i}": [d["catching_check"], *d.get("also_caught_by", [])]
        for v in VARIANTS
        for i, d in enumerate(v["defects"])
        if d["catching_check"] != NONE
    }
    assert actual == FIXED_CHECK_ASSIGNMENTS


def test_the_catalogue_is_the_51_fixed_checks() -> None:
    ids = MANIFEST["fixed_check_catalogue"]["ids"]
    assert len(ids) == len(set(ids)) == 51


def test_the_set_shows_what_the_fixed_checks_cannot_see() -> None:
    defects = [d for v in VARIANTS for d in v["defects"]]
    critic_only = [d for d in defects if d["catching_check"] == NONE]
    assert len(critic_only) * 2 >= len(defects), "the critic-only group is the point of the set"
    assert any(d["catching_check"] != NONE for d in defects), "keep some a fixed check should catch"
    assert any(v["rejected_by_existing_validation"] for v in VARIANTS)
    assert any(not v["rejected_by_existing_validation"] for v in VARIANTS)
    assert {d["category"] for d in defects} >= REQUIRED_CATEGORIES
    assert any(v["kind"] == "interacting" for v in VARIANTS)


# --------------------------------------------------------------------------- the bases are sound


@pytest.mark.parametrize("key", sorted(MANIFEST["bases"]))
def test_base_compiles_cleanly(key: str) -> None:
    base = MANIFEST["bases"][key]
    intent = IntentPacket.model_validate(_load(base["intent"]))
    protocol = compile_protocol(intent)
    assert canonical_fingerprint(protocol) == base["protocol_fingerprint"]
    compiled = json.loads(canonical_json(protocol))
    assert compiled == _load(base["protocol"]), "the checked-in protocol is the compiled intent"
    assert compiled["playbook_type"] == base["playbook_type"]
    errors, warnings = _validate_doc(compiled)
    assert errors == [] and warnings == [], "a sound base has no error and no warning"


@pytest.mark.parametrize("key", sorted(MANIFEST["bases"]))
def test_base_seeds_are_real_records_the_criteria_keep(key: str) -> None:
    base = _load(MANIFEST["bases"][key]["intent"])
    catalogue = {s["doi"]: s for s in MANIFEST["seed_catalog"]}
    for doi in base.get("golden_seeds", []):
        seed = catalogue[doi]
        assert "review" not in seed["kind"]
        assert base["start_year"] <= seed["year"] <= base["end_year"]


# --------------------------------------------------------------------------- the variants are honest


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v["id"])
def test_variant_differs_from_its_base_only_in_the_named_fields(variant: dict[str, Any]) -> None:
    base_key = "intent" if variant["format"] == "intent" else "protocol"
    base = _load(MANIFEST["bases"][variant["base"]][base_key])
    changed = _diff(base, _load(variant["file"]))
    assert changed == variant["fields"]


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda v: v["id"])
def test_existing_validation_says_what_the_manifest_says(variant: dict[str, Any]) -> None:
    rejected_by, errors, warnings = _existing_validation(variant)
    expected = variant["existing_validation"]
    assert rejected_by == expected["rejected_by"]
    assert errors == expected["errors"]
    assert warnings == expected["warnings"]
    if variant["rejected_by_existing_validation"]:
        assert rejected_by is not None
    else:
        # Not rejected: it compiles, and protocol validation finds no error.
        assert rejected_by is None and errors == []


def test_the_compiler_refuses_almost_nothing() -> None:
    """The compiler (intent model and compile step) refuses at most a few variants: the rest are for the critic."""
    refused = [
        v["id"] for v in VARIANTS if v["existing_validation"]["rejected_by"] in ("intent_model", "compile")
    ]
    assert len(refused) <= 3, refused
