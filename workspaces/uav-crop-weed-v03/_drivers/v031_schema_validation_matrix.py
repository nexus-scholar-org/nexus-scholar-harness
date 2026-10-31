#!/usr/bin/env python3
"""v0.3.1 charting-schema validation matrix (F1 repair).

Proves the schema now refuses the rows v0.3.0 accepted, and that the
positive shapes still validate. Writes audit/charting_validation_matrix_v031.json.

Run: uv run python workspaces/uav-crop-weed-v03/_drivers/v031_schema_validation_matrix.py
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

WS = Path(__file__).resolve().parents[1]
SCHEMA = WS / "charting.schema.json"
V030 = WS / "audit" / "charting_schema_v030_superseded.json"
OUT = WS / "audit" / "charting_validation_matrix_v031.json"

DIMS = [
    "study_reports", "task_context", "dataset_units", "sensor_inputs",
    "availability_alignment", "temporal_design", "split_protocol",
    "fusion_mechanism", "uncertainty_calibration", "metrics_comparators",
    "transfer_outcomes", "provenance_limits", "open_science",
]


EMPTY_FIELDS = {
    "study_reports": {"primary_report_doi": "null", "primary_publication_year": "null",
                      "linked_reports": "empty"},
    "task_context": {"agricultural_setting": "null", "crop_species": "empty",
                     "weed_granularity": "null", "vision_task": "null",
                     "uav_separability": "null"},
    "dataset_units": {"dataset_origin": "null", "dataset_names": "empty",
                      "unique_fields_count": "null",
                      "unique_orthomosaics_or_flights_count": "null",
                      "unique_acquisition_dates_count": "null",
                      "unique_seasons_or_years_count": "null",
                      "total_tiles_or_patches_count": "null",
                      "independent_unit_level": "null"},
    "sensor_inputs": {"modalities_used": "empty", "spectral_bands": "empty",
                      "derived_indices_used": "empty", "gsd_mm_per_pixel": "null",
                      "flight_altitude_m": "null", "radiometric_calibration": "null"},
    "availability_alignment": {"stress_categories_evaluated": "empty",
                               "stress_origin": "null",
                               "alignment_or_restoration_method": "null"},
    "temporal_design": {"temporal_regime": "null", "crop_growth_stages_bbch": "null"},
    "split_protocol": {"partition_unit": "null", "spatial_leakage_risk": "null",
                       "target_domain_data_use": "null"},
    "fusion_mechanism": {"architecture_family": "null", "integration_topology": "null",
                         "matched_modality_ablation_present": "null"},
    "uncertainty_calibration": {"uncertainty_method": "null",
                                "calibration_metrics_reported": "empty",
                                "abstention_or_validity_rejection": "null",
                                "false_calibration_terminology_trap": "null"},
    "metrics_comparators": {"weed_class_specific_metrics_reported": "null",
                            "variance_or_ci_reported": "null",
                            "repeated_seeds_or_folds_count": "null",
                            "primary_metrics.weed_iou": "null",
                            "primary_metrics.weed_f1_or_dice": "null",
                            "primary_metrics.mean_iou": "null",
                            "primary_metrics.macro_f1": "null",
                            "primary_metrics.map_50": "null",
                            "primary_metrics.map_50_95": "null",
                            "primary_metrics.overall_accuracy": "null",
                            "primary_metrics.weed_cover_r2": "null"},
    "transfer_outcomes": {"shift_axes_tested": "empty", "adaptation_regime": "null",
                          "source_weed_metric_value": "null",
                          "target_weed_metric_value": "null",
                          "delta_transfer_drop": "null",
                          "failed_transfer_documented": "null"},
    "provenance_limits": {"missing_or_ambiguous_dimensions": "empty",
                          "internal_contradictions_noted": "null",
                          "claimed_vs_demonstrated_gap": "null"},
    "open_science": {"data_availability": "null", "code_availability": "null",
                     "license": "null", "retraction_or_correction_status": "null",
                     "funding_and_coi_disclosed": "null"},
}


def anchor(quote: str, locator: str = "Section 2, p. 3", absence: bool = False) -> dict:
    return {"verbatim_quote": quote, "locator": locator, "absence_check": absence}


def base_row() -> dict:
    """A fully reported row (the positive baseline)."""
    return {
        "study_id": "SCI-000030",
        "setting_id": "SET-01",
        "coder_id": "mouadh",
        "full_text_verified": True,
        "study_reports": {
            "evidence_state": "reported",
            "primary_report_doi": "10.1016/j.compag.2024.109000",
            "primary_publication_type": "journal_article",
            "primary_publication_year": 2024,
            "linked_reports": [{
                "identifier": "arXiv:2401.00001",
                "report_role": "preprint_version",
                "year": 2023,
            }],
            "narrative_summary": "Journal article with an earlier preprint.",
            "provenance": anchor("Published in Computers and Electronics in Agriculture."),
        },
        "task_context": {
            "evidence_state": "reported",
            "agricultural_setting": "arable_row_crop",
            "crop_species": ["barley"],
            "weed_granularity": "binary_crop_vs_weed",
            "vision_task": "semantic_segmentation",
            "uav_separability": "uav_only",
            "narrative_summary": "Barley field mapped from UAV imagery.",
            "provenance": anchor("The study maps weeds in a barley field."),
        },
        "dataset_units": {
            "evidence_state": "reported",
            "dataset_origin": "primary_newly_collected",
            "dataset_names": ["Custom_Barley_UAV"],
            "unique_fields_count": 1,
            "unique_orthomosaics_or_flights_count": 3,
            "unique_acquisition_dates_count": 3,
            "unique_seasons_or_years_count": 1,
            "total_tiles_or_patches_count": 4200,
            "independent_unit_level": "spatial_plot_or_block",
            "narrative_summary": "One field, three flights, block-level units.",
            "provenance": anchor("Three flights were conducted over one barley field."),
        },
        "sensor_inputs": {
            "evidence_state": "reported",
            "modalities_used": ["RGB", "MS_narrowband"],
            "spectral_bands": ["R", "G", "B", "RE", "NIR"],
            "derived_indices_used": ["NDVI", "ExG"],
            "gsd_mm_per_pixel": 12.5,
            "flight_altitude_m": 30.0,
            "radiometric_calibration": "calibrated_reflectance_panel_and_dls",
            "narrative_summary": "Five-band MS plus RGB at 12.5 mm/px.",
            "provenance": anchor("Images were captured at 30 m with a reflectance panel."),
        },
        "availability_alignment": {
            "evidence_state": "reported",
            "stress_categories_evaluated": ["motion_or_defocus_blur"],
            "stress_origin": "naturally_observed_in_field",
            "alignment_or_restoration_method": "deblurring network",
            "narrative_summary": "Natural blur evaluated with a restoration baseline.",
            "provenance": anchor("Blurred images were collected during windy conditions."),
        },
        "temporal_design": {
            "evidence_state": "reported",
            "temporal_regime": "multiple_dates_pooled_no_heldout",
            "crop_growth_stages_bbch": "BBCH 15, 17, 19",
            "narrative_summary": "Three dates pooled without a held-out date.",
            "provenance": anchor("Data from three dates were pooled for training."),
        },
        "split_protocol": {
            "evidence_state": "reported",
            "partition_unit": "spatial_block_or_strip_same_field",
            "spatial_leakage_risk": "moderate_unbuffered_adjacent_blocks_or_frames",
            "target_domain_data_use": "in_domain_split_only",
            "narrative_summary": "Spatial blocks within one field, no target exposure.",
            "provenance": anchor("The field was divided into adjacent blocks."),
        },
        "fusion_mechanism": {
            "evidence_state": "reported",
            "architecture_family": "cnn_segmentation_encoder_decoder",
            "integration_topology": "early_channel_stacking_concatenation",
            "matched_modality_ablation_present": True,
            "narrative_summary": "Early fusion with a matched RGB-only ablation.",
            "provenance": anchor("RGB and MS bands were concatenated at the input."),
        },
        "uncertainty_calibration": {
            "evidence_state": "reported",
            "uncertainty_method": "mc_dropout_or_bayesian_approximation",
            "calibration_metrics_reported": ["ECE", "Brier_score"],
            "abstention_or_validity_rejection": False,
            "false_calibration_terminology_trap": "none",
            "narrative_summary": "MC dropout with ECE and Brier score.",
            "provenance": anchor("Monte Carlo dropout was used to estimate uncertainty."),
        },
        "metrics_comparators": {
            "evidence_state": "reported",
            "weed_class_specific_metrics_reported": True,
            "primary_metrics": {"weed_iou": 0.72, "weed_f1_or_dice": 0.81},
            "repeated_seeds_or_folds_count": 5,
            "variance_or_ci_reported": True,
            "narrative_summary": "Weed-specific IoU and F1 over five seeds.",
            "provenance": anchor("Weed IoU reached 0.72 averaged over five seeds."),
        },
        "transfer_outcomes": {
            "evidence_state": "reported",
            "shift_axes_tested": ["cross_field_same_crop"],
            "adaptation_regime": "zero_shot_direct_transfer",
            "source_weed_metric_value": 0.81,
            "target_weed_metric_value": 0.62,
            "delta_transfer_drop": -0.19,
            "failed_transfer_documented": False,
            "narrative_summary": "Zero-shot transfer to a second field.",
            "provenance": anchor("The model was evaluated zero-shot on a second field."),
        },
        "provenance_limits": {
            "evidence_state": "reported",
            "missing_or_ambiguous_dimensions": ["calibration_method"],
            "internal_contradictions_noted": None,
            "claimed_vs_demonstrated_gap": "aligned_claims_match_split_independence",
            "narrative_summary": "Claims match the block-level split; calibration under-specified.",
            "provenance": anchor("Blocks were split spatially before training."),
        },
        "open_science": {
            "evidence_state": "reported",
            "data_availability": "public_repository_verified_link",
            "code_availability": "public_repository_verified_link",
            "license": "CC-BY-4.0",
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": True,
            "narrative_summary": "Data and code linked in the paper; no retraction.",
            "provenance": anchor("The dataset and code are available at the linked repository."),
        },
    }


def set_state(row: dict, dim: str, state: str, absence: bool) -> None:
    row[dim]["evidence_state"] = state
    row[dim]["provenance"]["absence_check"] = absence


def errors(schema: dict, row: dict) -> list[str]:
    v = Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in v.iter_errors(row)]


def main() -> int:
    schema = json.loads(SCHEMA.read_text())
    v030 = json.loads(V030.read_text()) if V030.exists() else None
    Draft202012Validator.check_schema(schema)
    results = []

    def record(name: str, ok: bool, detail: str) -> None:
        results.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    record("schema_self_check", True, "draft 2020-12 metaschema ok")

    positive = base_row()
    e = errors(schema, positive)
    record("P1_full_reported_row", not e, "valid" if not e else e[0])

    # --- absence states: empty content + absence quote -----------------
    for state in ("not_reported", "unavailable", "not_applicable"):
        row = base_row()
        set_state(row, "task_context", state, True)
        row["task_context"].update({
            "agricultural_setting": None, "crop_species": [],
            "weed_granularity": None, "vision_task": None,
            "uav_separability": None,
            "narrative_summary": f"Dimension is {state}; checked the full text.",
            "provenance": anchor(f"[Checked Sections 2-3: task context {state}]", absence=True),
        })
        e = errors(schema, row)
        record(f"P2_{state}_empty_task_context", not e, "valid" if not e else e[0])

    # --- each dimension: absence state with a genuinely empty shape -----
    for dim in DIMS:
        row = base_row()
        set_state(row, dim, "not_reported", True)
        for field, kind in EMPTY_FIELDS[dim].items():
            if "." in field:
                outer, inner = field.split(".", 1)
                row[dim][outer][inner] = None
            elif kind == "empty":
                row[dim][field] = []
            else:
                row[dim][field] = None
        row[dim]["narrative_summary"] = "Authors did not report this dimension."
        row[dim]["provenance"] = anchor(
            "[Checked Sections 2-5: no statement on this dimension]", absence=True
        )
        e = errors(schema, row)
        record(f"P2_{dim}_not_reported_empty", not e, "valid" if not e else e[0])

    # --- conflicting: two anchors, no asserted value -------------------
    row = base_row()
    set_state(row, "task_context", "conflicting", False)
    row["task_context"].update({
        "agricultural_setting": None, "crop_species": [],
        "weed_granularity": None, "vision_task": None, "uav_separability": None,
        "narrative_summary": "Text says one crop; Table 1 lists another.",
        "provenance": anchor("The trial was conducted in a barley field."),
        "additional_provenance": [anchor("Table 1: experiments were performed on rapeseed.")],
    })
    e = errors(schema, row)
    record("P3_conflicting_two_anchors", not e, "valid" if not e else e[0])

    # --- 13-dimension populated-under-absence matrix -------------------
    for dim in DIMS:
        row = base_row()
        set_state(row, dim, "not_reported", True)
        row[dim]["narrative_summary"] = "Authors did not report this dimension."
        e = errors(schema, row)
        record(f"N1_{dim}_not_reported_but_populated", bool(e), e[0] if e else "ACCEPTED (integrity gap)")

    # --- targeted negative cases ---------------------------------------
    row = base_row()
    set_state(row, "task_context", "not_reported", False)  # wrong anchor flag
    row["task_context"].update({
        "agricultural_setting": None, "crop_species": [], "weed_granularity": None,
        "vision_task": None, "uav_separability": None,
        "narrative_summary": "Absent.",
    })
    e = errors(schema, row)
    record("N2_absence_quote_flagged_as_content", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["task_context"]["provenance"]["absence_check"] = True  # reported + absence quote
    e = errors(schema, row)
    record("N3_reported_with_absence_quote", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["uncertainty_calibration"].update({
        "evidence_state": "not_reported",
        "provenance": anchor("[Checked Sections 4-5: no calibration reported]", absence=True),
        "narrative_summary": "No calibration metrics reported.",
    })
    e = errors(schema, row)
    record("N4_not_reported_with_method", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["task_context"].update({
        "evidence_state": "conflicting",
        "agricultural_setting": None, "crop_species": [], "weed_granularity": None,
        "vision_task": None, "uav_separability": None,
        "provenance": anchor("The trial was conducted in a barley field."),
        "narrative_summary": "Conflicting crop statement.",
    })
    e = errors(schema, row)
    record("N5_conflicting_with_one_anchor", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["task_context"].update({
        "evidence_state": "conflicting",
        "provenance": anchor("The trial was conducted in a barley field."),
        "additional_provenance": [anchor("Table 1: experiments were performed on rapeseed.")],
        "narrative_summary": "Conflicting crop statement.",
    })
    e = errors(schema, row)
    record("N6_conflicting_with_asserted_value", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["study_reports"]["primary_publication_year"] = None  # reported + null primary field
    e = errors(schema, row)
    record("N7_reported_with_null_primary_field", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["open_science"]["data_availability"] = "not_reported"  # removed enum member
    e = errors(schema, row)
    record("N8_removed_absence_enum_member", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["fusion_mechanism"]["matched_modality_ablation_present"] = "unknown"  # tri-state, not free text
    e = errors(schema, row)
    record("N9_boolean_not_tri_state_value", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    del row["task_context"]["provenance"]["absence_check"]  # now required
    e = errors(schema, row)
    record("N10_anchor_without_absence_flag", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["uncertainty_calibration"].update({
        "evidence_state": "not_reported",
        "uncertainty_method": None, "calibration_metrics_reported": [],
        "abstention_or_validity_rejection": None,
        "false_calibration_terminology_trap": None,
        "provenance": anchor("[Checked Sections 4-5: no calibration reported]", absence=True),
        "narrative_summary": "No calibration metrics reported.",
    })
    row["uncertainty_calibration"]["provenance"]["absence_check"] = False
    e = errors(schema, row)
    record("N11_absence_quote_marked_content", bool(e), e[0] if e else "ACCEPTED")

    row = base_row()
    row["metrics_comparators"]["primary_metrics"] = {
        "weed_iou": None, "weed_f1_or_dice": None, "mean_iou": None, "macro_f1": None,
        "map_50": None, "map_50_95": None, "overall_accuracy": None, "weed_cover_r2": None,
    }
    e = errors(schema, row)
    record("N12_reported_metrics_with_no_values", bool(e), e[0] if e else "ACCEPTED")

    # --- regression against the superseded v0.3.0 ----------------------
    if v030 is not None:
        # Same claim, expressed in each schema's own anchor shape: v0.3.0 has no
        # absence_check, so the fixture strips it there and sets it here.
        row = base_row()
        row["uncertainty_calibration"].update({
            "evidence_state": "not_reported",
            "narrative_summary": "Authors omit calibration.",
        })
        v030_row = copy.deepcopy(row)
        for dim in DIMS:
            v030_row[dim]["provenance"].pop("absence_check", None)
            for extra in v030_row[dim].get("additional_provenance", []):
                extra.pop("absence_check", None)
        set_state(row, "uncertainty_calibration", "not_reported", True)
        v030_errors = errors(v030, v030_row)
        v031_errors = errors(schema, row)
        record(
            "R1_v030_fixture_now_refused",
            not v030_errors and bool(v031_errors),
            f"v0.3.0 accepted; v0.3.1 refuses ({len(v031_errors)} error(s))",
        )
    else:
        record("R1_v030_fixture_now_refused", False, "missing audit/charting_schema_v030_superseded.json")

    failed = [r for r in results if r["status"] != "PASS"]
    payload = {
        "schema": "charting.schema.json",
        "schema_version": "v0.3.1",
        "schema_sha256": hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),
        "superseded_sha256": hashlib.sha256(V030.read_bytes()).hexdigest() if V030.exists() else None,
        "checked_at": "2026-10-31",
        "results": results,
        "summary": {"total": len(results), "passed": len(results) - len(failed), "failed": len(failed)},
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    for r in results:
        print(f"{r['status']:4} {r['name']}: {r['detail']}")
    print(f"\n{payload['summary']} -> {OUT.relative_to(WS)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
