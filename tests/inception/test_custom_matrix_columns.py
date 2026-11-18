"""The researcher's own matrix columns (M10b, ``05-criteria``).

Strict run 2026-11-13, finding 6: only the playbook's suggested columns could
be chosen, and ``build_intent`` dropped any other name silently. Own columns
are now a draft field holding the whole dimension, and they compile.
"""

from __future__ import annotations

import json

import pytest
from test_steps_proof_optional import TS, ready_draft

from scholar_harness.inception import steps
from scholar_harness.inception.genesis import _default_matrix_dimensions
from scholar_protocol.validate import validate_protocol

OWN = [
    {"name": "Sensor", "description": "Camera or sensor on the UAV", "data_type": "categorical", "required": True},
    {"name": "Flight altitude (m)", "description": "Altitude of the flights", "data_type": "numeric"},
]


def _dims(draft: dict) -> list[dict]:
    return steps.preview(draft, genesis_timestamp=TS)["intent"]["matrix_dimensions"]


def test_own_columns_follow_the_ticked_suggestions_and_reach_the_protocol():
    suggested = _default_matrix_dimensions("PRISMA_SLR", "field trials")[0]["name"]
    draft = {**ready_draft(), "matrix_columns": [suggested], "custom_matrix_columns": OWN}
    dims = _dims(draft)
    assert [d["name"] for d in dims] == [suggested, "Sensor", "Flight altitude (m)"]
    sensor = dims[1]
    assert sensor["id"] == "sensor" and sensor["data_type"] == "categorical" and sensor["required"] is True
    assert sensor["target_section_category"] is None and sensor["fallback_value"] == "Not Reported"
    assert dims[2]["id"] == "flight_altitude_m"
    protocol = steps.preview(draft, genesis_timestamp=TS)["protocol"]
    assert [d["name"] for d in protocol["matrix_dimensions"]] == [suggested, "Sensor", "Flight altitude (m)"]


def test_an_own_column_alone_still_reaches_the_protocol():
    """Before M10b ``if draft.matrix_columns:`` skipped the matrix when nothing was ticked."""
    assert [d["name"] for d in _dims({**ready_draft(), "custom_matrix_columns": OWN[:1]})] == ["Sensor"]


def test_the_matrix_step_answers_the_derived_ids():
    out = steps.run_step("matrix", {**ready_draft(), "custom_matrix_columns": OWN})
    assert [(c["id"], c["name"]) for c in out["custom_columns"]] == [("sensor", "Sensor"), ("flight_altitude_m", "Flight altitude (m)")]
    assert out["selected"][-2:] == ["Sensor", "Flight altitude (m)"]


def test_an_imported_id_is_kept_when_unique_and_replaced_on_a_clash():
    own = [
        {"id": "platform", "name": "Platform", "description": "d"},
        {"id": "sample_size", "name": "N", "description": "d"},  # clashes with a suggested id
    ]
    ids = [c["id"] for c in steps.run_step("matrix", {**ready_draft(), "custom_matrix_columns": own})["custom_columns"]]
    assert ids == ["platform", "n"]


def test_two_columns_with_one_slug_get_distinct_ids_and_the_protocol_validates(tmp_path):
    own = [{"name": "Crop type", "description": "d"}, {"name": "Crop-type!", "description": "d"}]
    draft = {**ready_draft(), "custom_matrix_columns": own}
    assert [d["id"] for d in _dims(draft)] == ["crop_type", "crop_type_2"]
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(steps.preview(draft, genesis_timestamp=TS)["protocol"]), encoding="utf-8")
    report = validate_protocol(path)
    assert not [f for f in report.findings if f.code == "DUPLICATE_DIMENSION_ID"]
    assert not [f for f in report.findings if f.severity == "error"]


def test_a_name_clash_is_draft_invalid_naming_the_field():
    suggested = _default_matrix_dimensions("PRISMA_SLR", "field trials")[0]["name"]
    with pytest.raises(steps.StepRefused) as exc:
        steps.run_step("matrix", {**ready_draft(), "custom_matrix_columns": [{"name": suggested.upper(), "description": "d"}]})
    assert exc.value.code == "DRAFT_INVALID"
    assert exc.value.details["errors"][0]["loc"] == ["custom_matrix_columns", 0, "name"]
    with pytest.raises(steps.StepRefused) as exc:
        steps.parse_draft({**ready_draft(), "custom_matrix_columns": [{"name": "A", "description": "d"}, {"name": "a", "description": "d"}]})
    assert exc.value.code == "DRAFT_INVALID"


def test_the_51st_column_is_too_large_and_a_bad_type_is_invalid():
    many = [{"name": f"C{i}", "description": "d"} for i in range(51)]
    with pytest.raises(steps.StepRefused) as exc:
        steps.parse_draft({**ready_draft(), "custom_matrix_columns": many})
    assert exc.value.code == "DRAFT_TOO_LARGE"
    with pytest.raises(steps.StepRefused) as exc:
        steps.parse_draft({**ready_draft(), "custom_matrix_columns": [{"name": "X", "data_type": "date"}]})
    assert exc.value.code == "DRAFT_INVALID"


def test_a_playbook_change_keeps_own_columns():
    draft = {**ready_draft(), "playbook": "SCOPING_REVIEW", "custom_matrix_columns": OWN}
    assert [d["name"] for d in _dims(draft)] == ["Sensor", "Flight altitude (m)"]
