"""Tests for the COI audit aggregator."""

from __future__ import annotations

from scholar_verify import coi
from scholar_verify.coi import norm_entities, normalize

MANIFEST = [
    {"workspace_id": "W1", "title": "UAV weed detection", "year": 2023},
    {"workspace_id": "W2", "title": "Drone phenotyping", "year": 2022},
    {"workspace_id": "W3", "title": "Field trials", "year": 2021},
]


def test_norm_entities_kind_mapping():
    ents = norm_entities(
        [
            {"name": "BASF", "kind": "company", "affiliation_role": "field_access"},
            "some vendor",
            {"name": "Bayer", "kind": "company", "affiliation_role": "funding"},
            {"name": "X", "kind": "tooling", "quote": "we used X"},
        ]
    )
    by_name = {e["entity"]: e for e in ents}
    assert by_name["BASF"]["kind"] == "donated-equipment"
    assert by_name["Bayer"]["kind"] == "funding"
    assert by_name["some vendor"]["kind"] == "unspecified"
    assert by_name["X"]["kind"] == "tooling"


def test_norm_entities_string_and_quote():
    ents = norm_entities(["Plain string", {"name": "N", "kind": "funding", "quote": "  trimmed  "}])
    assert ents[0] == {"entity": "Plain string", "kind": "unspecified", "quote": ""}
    assert ents[1]["quote"] == "trimmed"


def test_normalize_flat_schema_relabel():
    e = {
        "workspace_id": "W1",
        "coi_label": "no-statement",
        "funding_statement": "Supported by NSF grant",
        "industry_entities": [{"name": "Vendor", "kind": "tooling"}],
    }
    n = normalize(e)
    assert n["coi_label"] == "academic-or-public"
    assert n["adjusted_from"] == "no-statement"


def test_normalize_v2_schema_company_affiliation_role():
    e = {
        "study_id": "W2",
        "coi_label": "no-statement",
        "coi_verbatim": "Authors declare no conflict.",
        "industry_entities": [{"name": "AgriTech Co", "kind": "company", "affiliation_role": "support", "quote": "donated drones"}],
    }
    n = normalize(e)
    # a non-tooling entity exists, so the 'coi -> declared-no-conflict' branch is bypassed
    assert n["coi_label"] == "industry-affiliation-or-equipment"
    assert n["industry_entities"][0]["kind"] == "donated-equipment"
    assert n["adjusted_from"] == "no-statement"


def test_normalize_industry_money_upgrade():
    e = {
        "workspace_id": "W3",
        "coi_label": "no-statement",
        "industry_entities": [{"name": "SeedCorp", "kind": "company", "affiliation_role": "funding"}],
    }
    n = normalize(e)
    assert n["coi_label"] == "industry-money"
    assert n["adjusted_from"] == "no-statement"


def test_run_validation_and_summary():
    chunks = [
        {
            "workspace_id": "W1",
            "coi_label": "no-statement",
            "funding_statement": "Agriculture Victoria funding",
            "industry_entities": [],
        },
        {
            "study_id": "W2",
            "coi_label": "no-statement",
            "acknowledgments": "Thanks to SeedCo for field access",
            "industry_entities": [{"name": "SeedCo", "kind": "company", "affiliation_role": "field_access"}],
        },
        {
            "workspace_id": "W3",
            "coi_label": "industry-money",
            "industry_entities": [{"name": "CropMotors", "kind": "company", "affiliation_role": "funding"}],
        },
    ]
    out = coi.run(MANIFEST, chunks)
    s = out["summary"]
    assert s["studies_scanned"] == 3
    assert s["labels"]["academic-or-public"] == 1       # W1: funding, no non-tooling entity
    assert s["labels"]["industry-affiliation-or-equipment"] == 1  # W2: non-tooling entity, no funding kind
    assert s["labels"]["industry-money"] == 1           # W3 as declared
    assert s["industry_money_count"] == 1
    assert s["industry_affiliation_or_equipment_count"] == 1
    assert s["adjusted_relabels"] == 2
    assert out["industry_money_studies"] == ["W3"]
    assert out["industry_affiliation_or_equipment_studies"] == ["W2"]
    # adjusted order follows manifest iteration
    assert out["adjusted_studies"] == [("W1", "academic-or-public"), ("W2", "industry-affiliation-or-equipment")]


def test_run_rejects_duplicates():
    chunks = [
        {"workspace_id": "W1", "coi_label": "no-statement"},
        {"workspace_id": "W1", "coi_label": "no-statement"},
        {"workspace_id": "W2", "coi_label": "no-statement"},
        {"workspace_id": "W3", "coi_label": "no-statement"},
    ]
    try:
        coi.run(MANIFEST, chunks)
    except SystemExit as exc:
        assert "dups=['W1']" in str(exc)


def test_render_report_markdown():
    out = coi.run(
        MANIFEST,
        [
            {"workspace_id": "W1", "coi_label": "no-statement", "funding_statement": "NSF", "industry_entities": []},
            {"workspace_id": "W2", "coi_label": "no-statement", "coi_statement": "none", "industry_entities": []},
            {"workspace_id": "W3", "coi_label": "industry-money", "industry_entities": [{"name": "X", "kind": "company", "affiliation_role": "funding"}]},
        ],
    )
    md = coi.render_report(out)
    assert "# Conflict-of-Interest Audit" in md
    assert "| industry-money | 1 |" in md
    assert "## Adjusted labels" in md
