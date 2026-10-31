#!/usr/bin/env python3
"""Pilot charting driver for schema v0.3.1 (single-pass, explicitly labelled).

Builds one row per materially distinct evaluation setting from the nine
EXTRACTED_VALID pilot full texts. Every ``reported`` provenance quote is
verified as a whitespace-normalised substring of the corresponding extracted
Markdown. This is a single-coder agent pass; it makes no dual-coding claim.

Run:
    uv run python workspaces/uav-crop-weed-v03/_drivers/v031_charting_pilot.py
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import jsonschema

WS = Path(__file__).resolve().parents[1]
SCHEMA_PATH = WS / "charting.schema.json"
EXTRACTED = WS / "extracted"
OUT_DIR = WS / "charting"
OUT_ROWS = OUT_DIR / "pilot_rows_v031.json"
OUT_SUMMARY = OUT_DIR / "pilot_rows_v031_summary.json"

CODER_ID = "agent-opencode-single-pass"
SCHEMA_SHA256 = "91dbe0c8f81034ccb5f7eea903a11d3d96e9a50bc42914eea6ec7d0fe7596b42"

EXTRACTS = {
    "SCI-000006": "DOC-cc20c0a5fb951209987865322cf9b698.md",
    "SCI-000291": "DOC-5f69b252014ad57855691ce5a35e05e7.md",
    "SCI-000372": "DOC-5267a62b6f0196f79611f8dda2a25b73.md",
    "SCI-000607": "DOC-a7e8aa9adc0a1d4c443f9c995ba74310.md",
    "SCI-000041": "DOC-152b6eefd597d80302307a991d13b313.md",
    "SCI-000044": "DOC-bc7e2858087c8617d4984c278e8a070e.md",
    "SCI-000151": "DOC-a84e328fcfb7acc794728a9e0a918ee5.md",
    "SCI-000644": "DOC-73bc0aef90667fe533ecc0b1b3bcb608.md",
    "SCI-000736": "DOC-5797121f2521f5eff944bc444858a932.md",
}

_NULLS = {
    "study_reports": {
        "primary_report_doi": None,
        "primary_publication_type": "journal_article",
        "primary_publication_year": None,
        "linked_reports": [],
    },
    "task_context": {
        "agricultural_setting": None,
        "crop_species": [],
        "weed_granularity": None,
        "vision_task": None,
        "uav_separability": None,
    },
    "dataset_units": {
        "dataset_origin": None,
        "dataset_names": [],
        "unique_fields_count": None,
        "unique_orthomosaics_or_flights_count": None,
        "unique_acquisition_dates_count": None,
        "unique_seasons_or_years_count": None,
        "total_tiles_or_patches_count": None,
        "independent_unit_level": None,
    },
    "sensor_inputs": {
        "modalities_used": [],
        "spectral_bands": [],
        "derived_indices_used": [],
        "gsd_mm_per_pixel": None,
        "flight_altitude_m": None,
        "radiometric_calibration": None,
    },
    "availability_alignment": {
        "stress_categories_evaluated": [],
        "stress_origin": None,
        "alignment_or_restoration_method": None,
    },
    "temporal_design": {
        "temporal_regime": None,
        "crop_growth_stages_bbch": None,
    },
    "split_protocol": {
        "partition_unit": None,
        "spatial_leakage_risk": None,
        "target_domain_data_use": None,
    },
    "fusion_mechanism": {
        "architecture_family": None,
        "integration_topology": None,
        "matched_modality_ablation_present": None,
    },
    "uncertainty_calibration": {
        "uncertainty_method": None,
        "calibration_metrics_reported": [],
        "abstention_or_validity_rejection": None,
        "false_calibration_terminology_trap": None,
    },
    "metrics_comparators": {
        "weed_class_specific_metrics_reported": None,
        "primary_metrics": {
            "weed_iou": None,
            "weed_f1_or_dice": None,
            "mean_iou": None,
            "macro_f1": None,
            "map_50": None,
            "map_50_95": None,
            "overall_accuracy": None,
            "weed_cover_r2": None,
        },
        "repeated_seeds_or_folds_count": None,
        "variance_or_ci_reported": None,
    },
    "transfer_outcomes": {
        "shift_axes_tested": [],
        "adaptation_regime": None,
        "source_weed_metric_value": None,
        "target_weed_metric_value": None,
        "delta_transfer_drop": None,
        "failed_transfer_documented": None,
    },
    "provenance_limits": {
        "missing_or_ambiguous_dimensions": [],
        "internal_contradictions_noted": None,
        "claimed_vs_demonstrated_gap": None,
    },
    "open_science": {
        "data_availability": None,
        "code_availability": None,
        "license": None,
        "retraction_or_correction_status": None,
        "funding_and_coi_disclosed": None,
    },
}


def anchor(quote: str, locator: str, absence: bool = False) -> dict:
    return {"verbatim_quote": quote, "locator": locator, "absence_check": absence}


def nr(dim: str, narrative: str, quote: str, locator: str) -> dict:
    body = {k: ([] if isinstance(v, list) else v) for k, v in _NULLS[dim].items()}
    # deep-copy nested primary_metrics dict
    if dim == "metrics_comparators":
        body["primary_metrics"] = dict(_NULLS[dim]["primary_metrics"])
    out = {"evidence_state": "not_reported"}
    out.update(body)
    out["narrative_summary"] = narrative
    out["provenance"] = anchor(quote, locator, True)
    return out


def na(dim: str, narrative: str, quote: str, locator: str) -> dict:
    out = nr(dim, narrative, quote, locator)
    out["evidence_state"] = "not_applicable"
    return out


def rep(dim: str, values: dict, narrative: str, quote: str, locator: str,
        additional: list[dict] | None = None) -> dict:
    out = {"evidence_state": "reported"}
    body = dict(_NULLS[dim])
    if dim == "metrics_comparators":
        body["primary_metrics"] = dict(_NULLS[dim]["primary_metrics"])
    body.update(values)
    out.update(body)
    out["narrative_summary"] = narrative
    out["provenance"] = anchor(quote, locator, False)
    if additional:
        out["additional_provenance"] = additional
    return out


def study_reports(doi: str, ptype: str, year: int, narrative: str,
                  quote: str, locator: str) -> dict:
    return rep("study_reports", {
        "primary_report_doi": doi,
        "primary_publication_type": ptype,
        "primary_publication_year": year,
        "linked_reports": [],
    }, narrative, quote, locator)


# --------------------------------------------------------------------------
# study-level shared fragments
# --------------------------------------------------------------------------

def sci006(crop: str, setting: str) -> dict:
    return {
        "study_id": "SCI-000006",
        "setting_id": setting,
        "study_reports": study_reports(
            "10.1371/journal.pone.0251008", "journal_article", 2021,
            "PLOS ONE 2021 research article; the two croplands are reported inside one publication, charted as separate crop settings.",
            "A novel semi-supervised framework for UAV based crop/weed classification",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "vegetable_horticulture",
            "crop_species": [crop],
            "weed_granularity": "binary_crop_vs_weed",
            "vision_task": "patch_or_tile_classification",
            "uav_separability": "uav_only",
        }, f"Binary crop-versus-weed patch classification on {crop}; UAV RGB frames only.",
            "Two different croplands, pea, and strawberry were selected" if crop == "pea"
            else "Two different croplands, pea, and strawberry were selected",
            "Materials and methods, field description"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "primary_newly_collected",
            "dataset_names": ["Peshawar pea/strawberry UAV video dataset"],
            "unique_fields_count": 1,
            "unique_orthomosaics_or_flights_count": 1,
            "unique_acquisition_dates_count": 7,
            "unique_seasons_or_years_count": 1,
            "total_tiles_or_patches_count": None,
            "independent_unit_level": "single_raw_uav_frame",
        }, f"Frames were extracted from a one-week video campaign on the {crop} field. The extract reports 2,600 crop and 2,800 weed images without unambiguously assigning them to the two croplands, so the per-crop total is left null.",
            "The data set comprised 2600 images and 2800 images of crops and weeds",
            "Materials and methods, dataset paragraph"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB"],
            "spectral_bands": ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": 3.0,
            "flight_altitude_m": 2.0,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "DJI Spark RGB video at 2 m and 0.3 cm spatial resolution; no radiometric calibration or reflectance panel is described, so the imagery is coded as uncalibrated 8-bit DN.",
            "The altitude for the flight was kept 2m above the ground, and spatial resolution was 0.3cm.",
            "Materials and methods, flight campaign"),
        "availability_alignment": nr(
            "availability_alignment",
            "No degradation/stress condition (blur, misregistration, illumination drift, band dropout, occlusion) was manipulated or evaluated.",
            "[Checked Methods and Results: no stress/degradation condition evaluated]",
            "Methods and Results, absence check"),
        "temporal_design": rep("temporal_design", {
            "temporal_regime": "multiple_dates_pooled_no_heldout",
            "crop_growth_stages_bbch": "early growth stage; exact BBCH not stated",
        }, "Seven daily acquisitions (23 Feb-1 Mar 2020) were pooled; the first/second half of the video is a frame split, not a date holdout, so dates are pooled.",
            "Flights were conducted for one week from February 23 to March 1 2020",
            "Materials and methods, flight campaign"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "random_raw_frame_same_flight",
            "spatial_leakage_risk": "high_overlapping_or_random_tiles_from_same_flight",
            "target_domain_data_use": "in_domain_split_only",
        }, "Frames from the same video/field were split 70/15/15, with the first half of the video used for training and the latter half for testing; adjacent video frames share scene context, so leakage risk is high.",
            "The data set was split into 70% for training, 15% each for validation and testing.",
            "Materials and methods, dataset split"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "cnn_segmentation_encoder_decoder",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "Best-fit mapping: the method is a semi-supervised GAN classifier (discriminator CNN), not a segmentation encoder-decoder; it is RGB-only and reports no modality ablation.",
            "semi-supervised generative adversarial network for crops and weeds classification",
            "Abstract; Section 2"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "Softmax outputs are used for classification but no predictive-uncertainty method, calibration metric, abstention rule, or calibration terminology is reported.",
            "[Checked Results and Discussion: no uncertainty/calibration metric reported]",
            "Results and Discussion, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": False,
            "primary_metrics": {
                "overall_accuracy": 0.9375 if crop == "pea" else 0.946,
            },
            "repeated_seeds_or_folds_count": None,
            "variance_or_ci_reported": False,
        }, "Binary crop/weed accuracy is reported at the 80% labeled rate: pea 93.75% and strawberry 94.6% in Table 3. No weed-class IoU/F1 is given.",
            ("Crops and Weed 89.15% 90.08% 91.36% 93.75%" if crop == "pea"
             else "Crops and Weed 90.06% 90.66% 91.98% 94.6%"),
            "Results, Table 3"),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["none_in_distribution_only"],
            "adaptation_regime": "not_applicable_in_distribution",
            "source_weed_metric_value": None,
            "target_weed_metric_value": None,
            "delta_transfer_drop": None,
            "failed_transfer_documented": False,
        }, "Both croplands use the study's own model and in-domain splits; no external field, season, sensor or crop transfer is tested.",
            "on the Red Green Blue (RGB) images obtained by a quadcopter",
            "Abstract"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "radiometric calibration not stated",
                "per-crop image counts ambiguous",
                "no BBCH stage recorded",
                "no external validation",
            ],
            "internal_contradictions_noted": "The methods state that the first half of each video was used for training and the latter half for testing, but also state a 70/15/15 train/validation/test split of the dataset; the two descriptions do not reconcile into one partition protocol.",
            "claimed_vs_demonstrated_gap": "overclaimed_generalization_from_random_tile_split",
        }, "The paper motivates transfer to other horticultural crops, but evidence is limited to two in-field video datasets and a frame-level split at fixed 2 m altitude.",
            "evaluated on images collected at a fixed 2m altitude",
            "Discussion, limitations"),
        "open_science": rep("open_science", {
            "data_availability": "not_available_or_proprietary",
            "code_availability": "not_available",
            "license": "CC BY 4.0",
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": True,
        }, "PLOS data statement says all relevant data are within the paper; no code repository is given. Funding (HEC grant) and a no-competing-interests statement are present. Crossref check on 2026-10-31 found no retraction/correction relation.",
            "Data Availability Statement: All relevant data are within the paper.",
            "Data Availability Statement"),
    }


def sci044() -> dict:
    return {
        "study_id": "SCI-000044",
        "setting_id": "SET-01",
        "study_reports": study_reports(
            "10.48550/arxiv.2106.10581", "preprint_only", 2021,
            "arXiv preprint (v1, 19 Jun 2021); no journal/conference version or code repository linked in the extract.",
            "Supervised learning for crop/weed classification based on color and texture features",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "arable_row_crop",
            "crop_species": ["soybean"],
            "weed_granularity": "coarse_group_broadleaf_narrowleaf",
            "vision_task": "patch_or_tile_classification",
            "uav_separability": "uav_only",
        }, "Four-class segment classification (soil, soybean, grass, broadleaf weeds) on a public UAV soybean dataset.",
            "discrimination of Soybean crops and weeds",
            "Abstract"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "reused_pre_2020_uav_benchmark",
            "dataset_names": ["Weed detection in soybean crops (Kaggle, Dos Santos Ferreira et al.)"],
            "unique_fields_count": 1,
            "unique_orthomosaics_or_flights_count": None,
            "unique_acquisition_dates_count": None,
            "unique_seasons_or_years_count": None,
            "total_tiles_or_patches_count": 15336,
            "independent_unit_level": "sub_image_tile_or_patch",
        }, "Public soybean UAV dataset split by SLIC into 15,336 annotated segments across four classes.",
            "The image dataset contained 15,336 segments",
            "Dataset description"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB"],
            "spectral_bands": ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": None,
            "flight_altitude_m": None,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "RGB UAV imagery from a reused public dataset; neither GSD nor altitude is stated in the extract, and no radiometric calibration is described, so imagery is coded as uncalibrated.",
            "obtained from an unmanned aerial vehicle (UAV), which is publicly available",
            "Dataset description"),
        "availability_alignment": nr(
            "availability_alignment",
            "No degradation/stress condition is manipulated or evaluated; only colour/texture feature combinations are compared.",
            "[Checked Methods and Results: no stress/degradation condition evaluated]",
            "Methods and Results, absence check"),
        "temporal_design": nr(
            "temporal_design",
            "The reused benchmark description in this extract gives no acquisition date, season or growth stage, so no temporal regime can be charted.",
            "[Checked Dataset description: no acquisition date or season stated]",
            "Dataset description, absence check"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "random_tile_or_pixel_same_orthomosaic",
            "spatial_leakage_risk": "high_overlapping_or_random_tiles_from_same_flight",
            "target_domain_data_use": "in_domain_split_only",
        }, "Segments are randomly divided into training and testing sets; no spatial block, flight or field holdout is used.",
            "The obtained feature matrices and label values were divided randomly into two sets",
            "Methods, SVM training"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "classical_ml_rf_svm_obia",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "SVM on handcrafted RGB/HSV colour plus GLCM/LBP texture features; no learned multimodal fusion or modality ablation.",
            "Support Vector Machine (SVM)",
            "Abstract"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "SVM decision outputs are used directly; no predictive-uncertainty method or calibration metric is reported.",
            "[Checked Methods and Results: no uncertainty/calibration metric reported]",
            "Methods and Results, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": True,
            "primary_metrics": {"overall_accuracy": 0.9617},
            "repeated_seeds_or_folds_count": 10,
            "variance_or_ci_reported": False,
        }, "Best overall accuracy 96.17% for SVM one-vs-one with colour+LBP, averaged over 10 random iterations; per-class confusion matrices are given but no variance/CI is reported.",
            "reaches 96.17%",
            "Results, Table II"),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["none_in_distribution_only"],
            "adaptation_regime": "not_applicable_in_distribution",
            "source_weed_metric_value": None,
            "target_weed_metric_value": None,
            "delta_transfer_drop": None,
            "failed_transfer_documented": False,
        }, "Only an in-domain random segment split is evaluated; no cross-field, cross-date, cross-sensor or cross-crop transfer.",
            "discriminate crops, weeds and soil",
            "Conclusion"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "GSD and flight altitude not stated",
                "acquisition date and growth stage not stated",
                "no radiometric calibration",
                "random segment split only",
            ],
            "internal_contradictions_noted": None,
            "claimed_vs_demonstrated_gap": "overclaimed_generalization_from_random_tile_split",
        }, "The accuracy claim rests on randomly split segments from one public UAV dataset without spatial or temporal holdout, and the imaging geometry is unreported.",
            "Because the trained data are generated randomly",
            "Results, evaluation protocol"),
        "open_science": rep("open_science", {
            "data_availability": "reused_public_benchmark_only",
            "code_availability": "not_available",
            "license": None,
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": False,
        }, "The Kaggle soybean dataset is publicly linked; no code repository, funding statement, or conflict-of-interest statement appears in the extract. DataCite check on 2026-10-31 found no retraction/correction relation.",
            "The database used in this study is available online and can be downloaded from",
            "Dataset description"),
    }


def sci041() -> dict:
    return {
        "study_id": "SCI-000041",
        "setting_id": "SET-01",
        "study_reports": study_reports(
            "10.48550/arxiv.2505.07444", "preprint_only", 2025,
            "arXiv preprint (v1, 12 May 2025). The extract shows no journal/conference venue or linked code repository.",
            "Lightweight Multispectral Crop-Weed Segmentation for Precision Agriculture",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "arable_row_crop",
            "crop_species": ["maize"],
            "weed_granularity": "multi_species_fine_grained",
            "vision_task": "semantic_segmentation",
            "uav_separability": "uav_only",
        }, "Five-class WeedsGalore labels (maize, amaranth, barnyard grass, quickweed, other weeds) are remapped to background/crop/weed for three-class semantic segmentation.",
            "segmentation in maize fields",
            "Section III, dataset"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "reused_in_window_uav_benchmark",
            "dataset_names": ["WeedsGalore"],
            "unique_fields_count": 1,
            "unique_orthomosaics_or_flights_count": 4,
            "unique_acquisition_dates_count": 4,
            "unique_seasons_or_years_count": 1,
            "total_tiles_or_patches_count": 156,
            "independent_unit_level": "sub_image_tile_or_patch",
        }, "WeedsGalore: one 1,840 m2 maize plot, four flights May-June 2023, 156 annotated 600x600 tiles.",
            "156 image tiles of 600×600 pixels",
            "Section III, dataset"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB", "MS_narrowband"],
            "spectral_bands": ["red", "green", "blue", "red-edge 730 nm", "NIR 840 nm"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": 2.5,
            "flight_altitude_m": 5.0,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "DJI Phantom P4 Multispectral at 5 m with 2.5 mm GSD; RGB, red-edge and NIR are used. The extract reports no reflectance panel or irradiance-sensor calibration, so acquisition is coded uncalibrated.",
            "achieving a ground sampling distance (GSD) of 2.5 mm",
            "Section III, dataset"),
        "availability_alignment": nr(
            "availability_alignment",
            "The study compares modality sets but does not evaluate blur, misregistration, illumination drift, band dropout, resolution degradation or occlusion as stress conditions.",
            "[Checked Results: no degradation/stress condition evaluated]",
            "Results, absence check"),
        "temporal_design": rep("temporal_design", {
            "temporal_regime": "multiple_dates_pooled_no_heldout",
            "crop_growth_stages_bbch": "four growth stages sampled; exact BBCH not stated",
        }, "Four flights across May-June 2023 are pooled and then split spatially; no date is held out.",
            "Four flights, conducted between May and June 2023",
            "Section III, dataset"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "spatial_block_or_strip_same_field",
            "spatial_leakage_risk": "moderate_unbuffered_adjacent_blocks_or_frames",
            "target_domain_data_use": "in_domain_split_only",
        }, "109/23/24 tiles are spatially separated with no overlap between splits, but no buffer width is reported, so leakage risk is coded moderate.",
            "109 training (70%), 23 validation (15%), and 24 test (15%) tiles, ensuring no spatial overlap",
            "Section III, dataset"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "vision_transformer_or_hybrid_segmentation",
            "integration_topology": "dual_stream_cross_modal_attention_or_gating",
            "matched_modality_ablation_present": True,
        }, "Transformer-CNN hybrid with dynamic gated multispectral fusion; an RGB-only variant is trained and compared (mIoU 63.08), so the modality ablation is matched.",
            "adaptive gated fusion mechanism",
            "Conclusion"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "No predictive-uncertainty method, calibration metric, abstention rule, or 'calibration' terminology is reported.",
            "[Checked Results and Conclusion: no uncertainty/calibration metric reported]",
            "Results and Conclusion, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": False,
            "primary_metrics": {"mean_iou": 0.7888},
            "repeated_seeds_or_folds_count": None,
            "variance_or_ci_reported": False,
        }, "Multispectral model mIoU 78.88% versus RGB-only 63.08%; per-class IoU is mentioned but no weed-specific value or run variance is stated.",
            "achieved an mIoU of 78.88%",
            "Section IV, results"),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["none_in_distribution_only"],
            "adaptation_regime": "not_applicable_in_distribution",
            "source_weed_metric_value": None,
            "target_weed_metric_value": None,
            "delta_transfer_drop": None,
            "failed_transfer_documented": False,
        }, "Evaluation is on a held-out in-domain test split of the same benchmark; no cross-field or cross-season transfer is tested.",
            "held-out test set of 24 images",
            "Section IV, evaluation"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "single field and single season",
                "no radiometric calibration statement",
                "no run-to-run variance",
                "spatial buffer width not stated",
            ],
            "internal_contradictions_noted": None,
            "claimed_vs_demonstrated_gap": "aligned_claims_match_split_independence",
        }, "The paper claims efficiency and multispectral gain on one field; the matched RGB-only ablation supports the gain, and the authors do not claim cross-field generalization.",
            "with only 8.7M parameters",
            "Conclusion"),
        "open_science": rep("open_science", {
            "data_availability": "reused_public_benchmark_only",
            "code_availability": "not_available",
            "license": None,
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": False,
        }, "WeedsGalore is a public benchmark; the extract contains no code repository, funding statement, or conflict-of-interest statement. DataCite check on 2026-10-31 found no retraction/correction relation.",
            "is a publicly available",
            "Section III, dataset"),
    }


def sci151(crop: str, setting: str, dataset_bits: dict) -> dict:
    cwfid = crop == "carrot"
    return {
        "study_id": "SCI-000151",
        "setting_id": setting,
        "study_reports": study_reports(
            "10.3389/frsen.2022.755939", "journal_article", 2022,
            "Frontiers in Remote Sensing 2022 article comparing four segmentation architectures on two public benchmark datasets.",
            "Deep Convolutional Neural Networks for Weeds and Crops Discrimination From UAS Imagery",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "vegetable_horticulture" if cwfid else "arable_row_crop",
            "crop_species": ["carrot"] if cwfid else ["sugarcane"],
            "weed_granularity": "binary_crop_vs_weed",
            "vision_task": "semantic_segmentation",
            "uav_separability": "mixed_platform_uav_separable" if cwfid else "uav_only",
        }, ("CWFID was captured by a ground field robot, so the platform is mixed and must be separated from UAV evidence." if cwfid
            else "Sugarcane orthomosaic was captured by a fixed-wing UAV."),
            "organic carrot farm in Northern Germany" if cwfid
            else "a sugarcane plantation in Northern Brazil",
            "Section 3, dataset description"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "reused_pre_2020_uav_benchmark",
            "dataset_names": ["CWFID" if cwfid else "Sugar Cane Orthomosaic"],
            "unique_fields_count": 1,
            "unique_orthomosaics_or_flights_count": 1,
            "unique_acquisition_dates_count": 1,
            "unique_seasons_or_years_count": 1,
            "total_tiles_or_patches_count": dataset_bits["tiles"],
            "independent_unit_level": "single_raw_uav_frame" if cwfid else "sub_image_tile_or_patch",
        }, dataset_bits["dataset_narrative"], dataset_bits["dataset_quote"], dataset_bits["dataset_locator"]),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB", "MS_narrowband"] if cwfid else ["RGB"],
            "spectral_bands": ["red", "green", "blue", "multispectral band set not enumerated"] if cwfid else ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": None if cwfid else 50.0,
            "flight_altitude_m": None,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, dataset_bits["sensor_narrative"], dataset_bits["sensor_quote"], dataset_bits["sensor_locator"]),
        "availability_alignment": nr(
            "availability_alignment",
            "No degradation/stress condition is manipulated or evaluated; the paper notes resolution differences post hoc but does not run a stress experiment.",
            "[Checked Methods and Discussion: no stress/degradation condition evaluated]",
            "Methods and Discussion, absence check"),
        "temporal_design": rep("temporal_design", {
            "temporal_regime": "single_date_snapshot",
            "crop_growth_stages_bbch": None,
        }, dataset_bits["temporal_narrative"], dataset_bits["temporal_quote"], dataset_bits["temporal_locator"])
        if cwfid else nr(
            "temporal_design",
            "The sugarcane benchmark description gives no acquisition date or growth stage, so no temporal regime can be charted.",
            "[Checked Section 3: no acquisition date or growth stage stated]",
            "Section 3, absence check"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "random_tile_or_pixel_same_orthomosaic",
            "spatial_leakage_risk": "high_overlapping_or_random_tiles_from_same_flight",
            "target_domain_data_use": "in_domain_split_only",
        }, "Ten-fold cross-validation over randomly partitioned images/patches from the same dataset; no spatial or temporal holdout.",
            "A 10-fold cross-validation procedure was used",
            "Section 4, training"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "cnn_segmentation_encoder_decoder",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "DeepLabV3+ encoder-decoder segmentation compared against SegNet/FCN/U-Net; no modality-fusion ablation.",
            "DeepLabV3+",
            "Section 2, DeepLabV3+"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "No predictive-uncertainty method, calibration metric, abstention rule, or 'calibration' terminology is reported.",
            "[Checked Results and Conclusion: no uncertainty/calibration metric reported]",
            "Results and Conclusion, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": True if cwfid else False,
            "primary_metrics": {"overall_accuracy": 0.843 if cwfid else 0.7099},
            "repeated_seeds_or_folds_count": 10,
            "variance_or_ci_reported": False,
        }, dataset_bits["metrics_narrative"], dataset_bits["metrics_quote"], dataset_bits["metrics_locator"]),
        "transfer_outcomes": nr(
            "transfer_outcomes",
            "No model is transferred between the datasets: each architecture is fine-tuned separately on CWFID and on sugarcane and the scores are compared. The CWFID-versus-sugarcane gap is a cross-dataset comparison, not a demonstrated transfer outcome, so it is not charted as transfer.",
            "[Checked Training and Results: models fine-tuned separately on each dataset, no cross-dataset transfer]",
            "Training and Results, absence check"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "random 10-fold split only",
                "no radiometric calibration",
                "no run-to-run variance",
                "sugarcane date/season not stated",
            ],
            "internal_contradictions_noted": None,
            "claimed_vs_demonstrated_gap": "overclaimed_generalization_from_random_tile_split",
        }, "The comparison across platforms is informative but both evaluations use random cross-validation within a single dataset, not spatial or temporal holdout.",
            "Although the overall average performance improvement for all models using CWFID was about 6%",
            "Discussion"),
        "open_science": rep("open_science", {
            "data_availability": "reused_public_benchmark_only",
            "code_availability": "not_available",
            "license": None,
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": False,
        }, "Both datasets are public benchmarks; no code repository is given, funding is disclosed (NSF grants), but no conflict-of-interest statement appears in the extract. Crossref check on 2026-10-31 found no retraction/correction relation.",
            "The original contributions presented in the study are included in the article/supplementary material",
            "Data Availability Statement"),
    }


def sci291() -> dict:
    return {
        "study_id": "SCI-000291",
        "setting_id": "SET-01",
        "study_reports": study_reports(
            "10.1038/s41598-025-15380-3", "journal_article", 2025,
            "Scientific Reports 2025 article on teff weed detection with UAV imagery.",
            "Detection of weeds in teff crops using deep learning and UAV imagery for precision",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "broadacre_cereal",
            "crop_species": ["teff"],
            "weed_granularity": "binary_crop_vs_weed",
            "vision_task": "bounding_box_object_detection",
            "uav_separability": "uav_only",
        }, "Binary teff-versus-weed detection with bounding boxes and class labels on drone RGB imagery.",
            "Teff is a vital staple crop",
            "Abstract"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "primary_newly_collected",
            "dataset_names": ["University of Gondar teff UAV dataset"],
            "unique_fields_count": 3,
            "unique_orthomosaics_or_flights_count": 4,
            "unique_acquisition_dates_count": 4,
            "unique_seasons_or_years_count": 1,
            "total_tiles_or_patches_count": 1308,
            "independent_unit_level": "single_raw_uav_frame",
        }, "1,308 raw drone images from four flight sessions over three teff fields, plus augmented copies; the raw count is charted as the dataset size.",
            "A dataset of 1308 high-resolution drone-captured images",
            "Abstract"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB"],
            "spectral_bands": ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": None,
            "flight_altitude_m": None,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "DJI Air 2S RGB at 1-2 m above ground, 3056x3056 px; altitude is a range and GSD is not stated. No calibration is described, so imagery is coded uncalibrated.",
            "altitudes of 1–2 m above the ground",
            "Image acquisition"),
        "availability_alignment": nr(
            "availability_alignment",
            "No degradation/stress condition is manipulated or evaluated; augmentation and optimiser choices are compared, not sensor or environment stress.",
            "[Checked Methods and Results: no stress/degradation condition evaluated]",
            "Methods and Results, absence check"),
        "temporal_design": rep("temporal_design", {
            "temporal_regime": "multiple_dates_pooled_no_heldout",
            "crop_growth_stages_bbch": "multiple growth stages; exact BBCH not stated",
        }, "Four flight sessions across growth stages and weather are pooled before a random train/test split; no date is held out.",
            "four drone flight sessions conducted over three Teff fields",
            "Image acquisition"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "random_raw_frame_same_flight",
            "spatial_leakage_risk": "high_overlapping_or_random_tiles_from_same_flight",
            "target_domain_data_use": "in_domain_split_only",
        }, "Images are randomly split 80/20 across pooled dates and fields; adjacent frames from the same flight can land on both sides, so leakage risk is high.",
            "with 80% of the data allocated for training and 20% for testing",
            "Data splitting"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "one_stage_yolo_detector_or_segmenter",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "Best-fit mapping: the schema has no CNN-classifier member, so the evaluated YOLOv8 detector family is charted; the best-performing model is the fine-tuned MobileNetV2 classifier. RGB-only, no modality fusion.",
            "MobileNetV2",
            "Results"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "No predictive-uncertainty method, calibration metric, abstention rule, or 'calibration' terminology is reported.",
            "[Checked Results and Conclusion: no uncertainty/calibration metric reported]",
            "Results and Conclusion, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": False,
            "primary_metrics": {"overall_accuracy": 0.964, "map_50": 0.958},
            "repeated_seeds_or_folds_count": None,
            "variance_or_ci_reported": False,
        }, "Fine-tuned MobileNetV2 reports 96.40% accuracy and 95.80% fixed-threshold mAP (Table 9); the paper's COCO mAP at IoU 0.5:0.95 is 61.50%. No run-to-run variance is given.",
            "achieved the highest accuracy (96.40%)",
            "Abstract"),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["none_in_distribution_only"],
            "adaptation_regime": "not_applicable_in_distribution",
            "source_weed_metric_value": None,
            "target_weed_metric_value": None,
            "delta_transfer_drop": None,
            "failed_transfer_documented": False,
        }, "All reported scores come from the in-domain random train/test partition; no external field or season is held out.",
            "The dataset was partitioned into training and testing sets",
            "Convolution and pooling"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "GSD not stated",
                "altitude reported only as a range",
                "split fraction internally inconsistent",
                "no run-to-run variance",
            ],
            "internal_contradictions_noted": "Text states an 80/20 train/test split, while Table 2 reports 1,831 training images as 70% and 523 test images as 20% of the total; the fractions do not reconcile with the 2,616 augmented images.",
            "claimed_vs_demonstrated_gap": "overclaimed_generalization_from_random_tile_split",
        }, "The headline 96.4% rests on a random split of pooled dates and fields; the paper's wording about varied conditions is broader than the demonstrated holdout.",
            "Train 1831 70% of the total dataset",
            "Table 2"),
        "open_science": rep("open_science", {
            "data_availability": "available_upon_reasonable_request",
            "code_availability": "not_available",
            "license": "CC BY-NC-ND 4.0",
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": True,
        }, "Data are available from the corresponding author on request; no code repository is given. Funding (none) and competing interests (none) are both disclosed. Crossref check on 2026-10-31 found no retraction/correction relation.",
            "available from the corresponding author upon reasonable request",
            "Data availability"),
    }


def sci372(blurred: bool) -> dict:
    setting = "SET-02" if blurred else "SET-01"
    return {
        "study_id": "SCI-000372",
        "setting_id": setting,
        "study_reports": study_reports(
            "10.1038/s41598-026-58738-x", "journal_article", 2026,
            "Scientific Reports 2026 article in press (accepted 16 June 2026).",
            "Deblurring-aware semantic segmentation of crops and weeds in UAV sorghum imagery",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "arable_row_crop",
            "crop_species": ["sorghum"],
            "weed_granularity": "binary_crop_vs_weed",
            "vision_task": "semantic_segmentation",
            "uav_separability": "uav_only",
        }, "Three-class semantic segmentation (background, sorghum, weed) on the public DeBlurWeedSeg benchmark.",
            "three semantic categories, namely background, crop (sorghum), and weed",
            "Section 3.1"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "reused_in_window_uav_benchmark",
            "dataset_names": ["DeBlurWeedSeg"],
            "unique_fields_count": 1,
            "unique_orthomosaics_or_flights_count": 1,
            "unique_acquisition_dates_count": 1,
            "unique_seasons_or_years_count": 1,
            "total_tiles_or_patches_count": 1300,
            "independent_unit_level": "sub_image_tile_or_patch",
        }, "Public DeBlurWeedSeg: one sorghum field in Southern Germany, 1,300 paired 128x128 sharp/blurred patches.",
            "1,300 pairs of 128×128 pixel image patches",
            "Section 4.1"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB"],
            "spectral_bands": ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": None,
            "flight_altitude_m": None,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "DJI Mavic 2 Pro RGB patches; the extract gives no GSD, altitude or radiometric calibration statement, so acquisition is coded uncalibrated.",
            "using a DJI Mavic 2 Pro consumer-grade drone",
            "Section 4.1"),
        "availability_alignment": rep("availability_alignment", {
            "stress_categories_evaluated": ["motion_or_defocus_blur"],
            "stress_origin": "naturally_observed_in_field",
            "alignment_or_restoration_method": "NAFNet deblurring front-end with restoration-aware fine-tuning",
        }, "Motion blur is naturally present in the paired blurred patches; NAFNet is used as a deblurring front-end and jointly fine-tuned with the segmentation network.",
            "an explicit deblurring module based on NAFNet",
            "Abstract") if blurred else rep("availability_alignment", {
            "stress_categories_evaluated": ["none_assumed_ideal"],
            "stress_origin": "not_applicable",
            "alignment_or_restoration_method": None,
        }, "The sharp test subset is the ideal-condition reference; the degraded condition is charted separately as SET-02.",
            "corresponding sharp counterpart",
            "Section 4.1"),
        "temporal_design": rep("temporal_design", {
            "temporal_regime": "single_date_snapshot",
            "crop_growth_stages_bbch": "BBCH 13",
        }, "The benchmark was acquired at a single growth stage (BBCH 13); no temporal holdout is described.",
            "At the time of image acquisition, sorghum was at the BBCH 13 growth stage",
            "Section 4.1"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "random_tile_or_pixel_same_orthomosaic",
            "spatial_leakage_risk": "high_overlapping_or_random_tiles_from_same_flight",
            "target_domain_data_use": "in_domain_split_only",
        }, "Stratified 70/15/15 patch-level split with a fixed seed; patches from the same field are randomly assigned, so spatial leakage risk is high.",
            "stratified 70%/15%/15% ratio at the patch level",
            "Section 4.2"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "cnn_segmentation_encoder_decoder",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "UNet decoder with a ResNet encoder; RGB-only, no multimodal fusion or modality ablation.",
            "UNet with a ResNet encoder backbone",
            "Abstract"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "No predictive-uncertainty method, calibration metric, abstention rule, or 'calibration' terminology is reported.",
            "[Checked Results and Discussion: no uncertainty/calibration metric reported]",
            "Results and Discussion, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": False,
            "primary_metrics": {"macro_f1": 0.7614 if blurred else 0.9198},
            "repeated_seeds_or_folds_count": 1,
            "variance_or_ci_reported": False,
        }, ("On the motion-blurred test subset the proposed NAFNet+UNet-ResNet34 pipeline reaches mDS 0.7614 (sharp 0.8924, combined 0.8223); only one fixed seed (seed 0) is used."
            if blurred else
            "ResNet-34 reaches mean Dice Score 0.9198 on the sharp hold-out test set; only one fixed seed (seed 0) is used, so variance is not reported."),
            "Proposed + DeBlur3 0.8924 0.7614 0.8223" if blurred else "highest mean Dice Score of 0.9198",
            "Results, Table 4" if blurred else "Abstract"),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["none_in_distribution_only"],
            "adaptation_regime": "not_applicable_in_distribution",
            "source_weed_metric_value": None,
            "target_weed_metric_value": None,
            "delta_transfer_drop": None,
            "failed_transfer_documented": False,
        }, "The sharp subset is evaluated in-domain; the blur comparison is a physical-stress condition charted in availability_alignment, not a domain-transfer axis.",
            "corresponding sharp counterpart",
            "Section 4.1") if not blurred else nr(
            "transfer_outcomes",
            "The motion-blur subset is a degradation condition already charted under availability_alignment; the schema's transfer axes do not include blur, so no transfer outcome is charted for this setting.",
            "[Checked transfer axes: blur degradation is not a schema transfer axis]",
            "Methods, absence check"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "single field and single growth stage",
                "no GSD or altitude",
                "single seed only",
                "random patch split",
            ],
            "internal_contradictions_noted": None,
            "claimed_vs_demonstrated_gap": "aligned_claims_match_split_independence",
        }, "The authors explicitly caveat single-seed inference and leave multi-seed variance to future work; the modest in-domain claims match the patch-level split.",
            "a full multi-seed variance analysis is left for future work",
            "Section 4.2"),
        "open_science": rep("open_science", {
            "data_availability": "reused_public_benchmark_only",
            "code_availability": "public_repository_verified_link",
            "license": "MIT (code)",
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": True,
        }, "DeBlurWeedSeg is public via Mendeley/GitHub; training/evaluation code is archived on Zenodo and GitHub under MIT. Funding (none) and conflict of interest (none) are disclosed. Crossref check on 2026-10-31 found no retraction/correction relation.",
            "is released under the MIT License",
            "Code Availability"),
    }


def sci607(synthetic: bool) -> dict:
    setting = "SET-02" if synthetic else "SET-01"
    return {
        "study_id": "SCI-000607",
        "setting_id": setting,
        "study_reports": study_reports(
            "10.1038/s41598-022-23399-z", "journal_article", 2022,
            "Scientific Reports 2022 article on synthetic-image training for cotton weed detection and biomass estimation.",
            "Use of synthetic images for training a deep learning model for weed detection",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "arable_row_crop",
            "crop_species": ["cotton"],
            "weed_granularity": "multi_species_fine_grained",
            "vision_task": "instance_segmentation",
            "uav_separability": "uav_only",
        }, "Three-class instance segmentation (cotton, morningglory, grass weeds) plus biomass regression from mask area.",
            "weed detection and biomass estimation in cotton",
            "title"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "primary_newly_collected",
            "dataset_names": ["Cotton1 (2020)", "Cotton2 (2021)", "real-plant-instance synthetic images"],
            "unique_fields_count": 1,
            "unique_orthomosaics_or_flights_count": 2,
            "unique_acquisition_dates_count": 2,
            "unique_seasons_or_years_count": 2,
            "total_tiles_or_patches_count": 560,
            "independent_unit_level": "single_raw_uav_frame",
        }, "Two primary cotton acquisitions (2020 and 2021) plus a synthetic-image pipeline; 560 real images in Cotton1 and 100 in Cotton2.",
            "Cotton 1 was the main dataset and comprised 560 images",
            "Data collection"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB"],
            "spectral_bands": ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": 0.0274,
            "flight_altitude_m": 4.9,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "Fujifilm GFX100 RGB on a Hylio AG-110 at 4.9 m, 0.0274 mm/px, 16-bit PNG; no reflectance panel or irradiance calibration is described, so imagery is coded uncalibrated.",
            "operating at 4.9 m above ground level",
            "Data collection"),
        "availability_alignment": nr(
            "availability_alignment",
            "Synthetic training images are a data-source manipulation, not a degradation/stress condition; no blur, misregistration, illumination, band-dropout or occlusion stress is evaluated.",
            "[Checked Methods and Results: no degradation/stress condition evaluated]",
            "Methods and Results, absence check"),
        "temporal_design": rep("temporal_design", {
            "temporal_regime": "heldout_cross_season_or_cross_year" if synthetic else "single_date_snapshot",
            "crop_growth_stages_bbch": "4-5 leaves (Cotton1); 2-4 leaves (Cotton2)",
        }, ("Training uses 2020 imagery/synthetic derivatives and evaluation includes the unseen 2021 Cotton2 dataset, so the regime is cross-year."
            if synthetic else
            "Cotton1 was acquired on a single date in May 2020; no temporal holdout within Cotton1."),
            "Cotton2 June 13, 2021" if synthetic else "Cotton1 May 06, 2020",
            "Table 1"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "heldout_year_or_season" if synthetic else "random_raw_frame_same_flight",
            "spatial_leakage_risk": "low_buffered_blocks_or_independent_fields_flights" if synthetic else "high_overlapping_or_random_tiles_from_same_flight",
            "target_domain_data_use": "zero_target_exposure_strict_holdout" if synthetic else "in_domain_split_only",
        }, ("Synthetic images are generated from 2020 plant instances and evaluated on real Cotton1/Cotton2; the 2021 Cotton2 test is an unseen season with no target labels in training."
            if synthetic else
            "Cotton1 is split into 460 training/validation and 100 hold-out test images at the frame level within the same acquisition."),
            "Cotton 2 had 100 images for test purposes" if synthetic
            else "460 were reserved for the training and validation dataset, and the remaining 100 as hold-out test dataset",
            "Data collection"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "two_stage_rcnn_detector_or_segmenter",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "Mask R-CNN instance segmentation with a ResNet101 backbone; RGB-only, no multimodal fusion.",
            "Mask R-CNN, an instance segmentation",
            "Model training"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "No predictive-uncertainty method, calibration metric, abstention rule, or 'calibration' terminology is reported.",
            "[Checked Results and Discussion: no uncertainty/calibration metric reported]",
            "Results and Discussion, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": False,
            "primary_metrics": {"map_50": 0.60 if synthetic else 0.80},
            "repeated_seeds_or_folds_count": None,
            "variance_or_ci_reported": False,
        }, ("Synthetic-image training reaches mAPm 0.60 versus 0.80 for real images; single training runs, no variance."
            if synthetic else
            "Real-image training reaches mAPm 0.80 and mAPb 0.81 on the Cotton1 test set; single training runs, no variance."),
            "mean average precision for mask-mAPm: 0.60" if synthetic
            else "mAPm: 0.80",
            "Abstract"),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["cross_year_or_season"] if synthetic else ["none_in_distribution_only"],
            "adaptation_regime": "zero_shot_direct_transfer" if synthetic else "not_applicable_in_distribution",
            "source_weed_metric_value": 0.80 if synthetic else None,
            "target_weed_metric_value": None,
            "delta_transfer_drop": None,
            "failed_transfer_documented": False,
        }, ("Synthetic 2020 training transfers to the unseen 2021 Cotton2 test set; the paper reports performance without target fine-tuning, so this is zero-shot cross-year transfer."
            if synthetic else
            "The real-image model is evaluated on the in-domain Cotton1 hold-out and on Cotton2; only the in-domain setting is charted here, while the cross-year comparison is SET-02."),
            "Cotton1 and Cotton2 test datasets were used to assess all the models",
            "Results and discussion"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "single field/region",
                "no radiometric calibration",
                "no run-to-run variance",
                "biomass regression R2 inconsistent (0.66 vs 0.48/0.66 in text)",
            ],
            "internal_contradictions_noted": "Abstract reports Grass biomass R2 = 0.46 while the Results text reports R2 = 0.48 for Grass canopy-mask area.",
            "claimed_vs_demonstrated_gap": ("aligned_claims_match_split_independence" if synthetic
                                            else "overclaimed_generalization_from_random_tile_split"),
        }, "The cross-year test is a genuine temporal holdout, but training/evaluation remain within one region and one crop, and the biomass R2 values are internally inconsistent.",
            "the annotation proportion of the real image training dataset was imbalanced between the species",
            "Model training"),
        "open_science": rep("open_science", {
            "data_availability": "available_upon_reasonable_request",
            "code_availability": "not_available",
            "license": "CC BY 4.0",
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": True,
        }, "Data are available on reasonable request; no code repository is given. USDA funding and a no-competing-interests statement are present. Crossref check on 2026-10-31 found no retraction/correction relation.",
            "This study was funded by the USDA-Natural Resources Conservation Service-Conservation Innovation Grant",
            "Funding"),
    }


def sci644() -> dict:
    return {
        "study_id": "SCI-000644",
        "setting_id": "SET-01",
        "study_reports": study_reports(
            "10.3389/fpls.2021.702626", "journal_article", 2021,
            "Frontiers in Plant Science 2021 article on UAS weed mapping in sod production.",
            "Unmanned Aerial System-Based Weed Mapping in Sod Production Using a Convolutional",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "managed_pasture_forage",
            "crop_species": ["turfgrass (sod)"],
            "weed_granularity": "multi_species_fine_grained",
            "vision_task": "patch_or_tile_classification",
            "uav_separability": "uav_only",
        }, "Multi-label 1.5 m cell classification into broadleaf, grass weeds, spotted spurge, sedge and no-weeds classes.",
            "Weeds are a persistent problem on sod farms",
            "Abstract"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "primary_newly_collected",
            "dataset_names": ["Georgia sod farm surveys 2019-2020"],
            "unique_fields_count": None,
            "unique_orthomosaics_or_flights_count": 6,
            "unique_acquisition_dates_count": 6,
            "unique_seasons_or_years_count": 2,
            "total_tiles_or_patches_count": 10000,
            "independent_unit_level": "spatial_plot_or_block",
        }, "Six surveys on Georgia sod farms during 2019-2020, more than 10,000 1.5 m grid-cell images; the number of distinct fields and the exact image total are not stated, so the field count is null and 10,000 is a floor.",
            "More than 10,000 images from 6 surveys",
            "CNN training"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB"],
            "spectral_bands": ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": None,
            "flight_altitude_m": None,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "DJI Phantom 4 Pro V2 RGB at 20-40 m with 0.57-1.28 cm/px; GSD and altitude are ranges and no radiometric calibration is described, so imagery is coded uncalibrated.",
            "DJI Phantom 4 Pro V2",
            "Unmanned Aerial Systems Survey"),
        "availability_alignment": nr(
            "availability_alignment",
            "No degradation/stress condition is manipulated; resolution is discussed as a limitation post hoc, not as an evaluated stress axis.",
            "[Checked Methods and Discussion: no stress/degradation condition evaluated]",
            "Methods and Discussion, absence check"),
        "temporal_design": rep("temporal_design", {
            "temporal_regime": "multiple_dates_pooled_no_heldout",
            "crop_growth_stages_bbch": "establishing, mature and post-harvest turf; exact BBCH not stated",
        }, "Six surveys across 2019-2020 are pooled before an 80/20 random split; no survey/date is held out.",
            "during the growing season in 2019 and 2020",
            "Ground Survey"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "random_tile_or_pixel_same_orthomosaic",
            "spatial_leakage_risk": "high_overlapping_or_random_tiles_from_same_flight",
            "target_domain_data_use": "in_domain_split_only",
        }, "Random 80/20 training/validation split of grid cells from all six surveys; no test set and no spatial or temporal holdout.",
            "The images were divided into training (80%) and validation (20%) datasets",
            "CNN training"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "cnn_segmentation_encoder_decoder",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "Best-fit mapping: the study uses a Fastai multi-label ResNet-34 image classifier, which the schema has no exact member for; it is charted under the CNN encoder-decoder family and is not a segmentation model. RGB-only, no modality ablation.",
            "The architecture used was ResNet 34.",
            "CNN training"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "No predictive-uncertainty method, calibration metric, abstention rule, or 'calibration' terminology is reported.",
            "[Checked Results and Discussion: no uncertainty/calibration metric reported]",
            "Results and Discussion, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": True,
            "primary_metrics": {"weed_f1_or_dice": 0.80},
            "repeated_seeds_or_folds_count": None,
            "variance_or_ci_reported": False,
        }, "The schema has no F-beta field: 0.80 is the reported overall F2 score (beta=2), not F1/Dice, and is mapped to weed_f1_or_dice with this caveat. Class-wise precision/recall ranges and F2 scores are given; no variance.",
            "F2 score 0.80",
            "Table 2"),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["none_in_distribution_only"],
            "adaptation_regime": "not_applicable_in_distribution",
            "source_weed_metric_value": None,
            "target_weed_metric_value": None,
            "delta_transfer_drop": None,
            "failed_transfer_documented": False,
        }, "All metrics are computed on a random validation subset of the pooled surveys; no external field or season is held out.",
            "The model output of the validation dataset",
            "Metrics, Thresholds, and Performance Comparison"),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "no test set",
                "random cell split across pooled surveys",
                "GSD and altitude reported only as ranges",
                "no radiometric calibration",
            ],
            "internal_contradictions_noted": None,
            "claimed_vs_demonstrated_gap": "overclaimed_generalization_from_random_tile_split",
        }, "The paper reports performance across six surveys, but because all surveys are pooled and randomly split, the validation score does not demonstrate transfer to an unseen date or field.",
            "Image resolution is currently the major limiting factor",
            "Discussion"),
        "open_science": rep("open_science", {
            "data_availability": "available_upon_reasonable_request",
            "code_availability": "not_available",
            "license": "CC BY 4.0",
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": True,
        }, "Data are stated to be in the article/supplementary material with inquiries to the corresponding author; no code repository. Funding and conflict-of-interest statements are present. Crossref check on 2026-10-31 found no retraction/correction relation.",
            "This project was funded by the Georgia Department of Agriculture Specialty Crop Block Grant Program",
            "Funding"),
    }


def sci736(regime: str, setting: str) -> dict:
    zero = regime == "zero_shot"
    few = regime == "few_shot"
    daod = regime == "daod"
    regime_label = "zero-shot direct transfer" if zero else ("few-shot supervised fine-tuning" if few else "unsupervised domain adaptation")
    metrics_value = 0.578 if zero else (0.800 if few else 0.503)
    adapt = "zero_shot_direct_transfer" if zero else ("few_shot_supervised_fine_tuning" if few else "unsupervised_domain_adaptation")
    target_use = "zero_target_exposure_strict_holdout" if zero else ("labeled_target_few_shot_or_fine_tuning" if few else "unlabeled_target_images_for_uda_or_tta")
    failed = False if few else True
    return {
        "study_id": "SCI-000736",
        "setting_id": setting,
        "study_reports": study_reports(
            "10.48550/arxiv.2608.21254", "preprint_only", 2026,
            "arXiv preprint (v1, 21 Aug 2026); no journal/conference version is linked in the extract.",
            "On the Transferability of Agricultural Weed Detection Under Cross-Field Distribution",
            "title page"),
        "task_context": rep("task_context", {
            "agricultural_setting": "arable_row_crop",
            "crop_species": ["cotton", "soybean"],
            "weed_granularity": "binary_crop_vs_weed",
            "vision_task": "bounding_box_object_detection",
            "uav_separability": "uav_only",
        }, "Cross-crop weed-localization transfer between cotton and soybean UAV datasets, plus two public auxiliary datasets.",
            "agricultural weed detection in cotton fields",
            "Abstract"),
        "dataset_units": rep("dataset_units", {
            "dataset_origin": "hybrid_primary_and_benchmark",
            "dataset_names": ["new cotton UAV dataset", "soybean dataset (Stoneville, MS)", "CoFly-WeedDB", "CottonWeedDet12"],
            "unique_fields_count": None,
            "unique_orthomosaics_or_flights_count": None,
            "unique_acquisition_dates_count": None,
            "unique_seasons_or_years_count": None,
            "total_tiles_or_patches_count": 13189,
            "independent_unit_level": "sub_image_tile_or_patch",
        }, "Four datasets: 1,628 soybean tiles + 5,706 new cotton tiles + 207 CoFly + 5,648 CWDet12 = 13,189 tiles. The number of distinct physical fields, dates and seasons is not enumerated, so those counts are null.",
            "Our evaluation uses four datasets of aerial and ground weed imagery",
            "Section 3, Datasets"),
        "sensor_inputs": rep("sensor_inputs", {
            "modalities_used": ["RGB"],
            "spectral_bands": ["red", "green", "blue"],
            "derived_indices_used": [],
            "gsd_mm_per_pixel": 21.3,
            "flight_altitude_m": 7.62,
            "radiometric_calibration": "uncalibrated_raw_or_8bit_dn",
        }, "The primary cotton/soybean surveys use RGB UAV imagery at 25 ft with approximately 2.13 cm/px; no radiometric calibration is described, so acquisition is coded uncalibrated. CoFly and CWDet12 acquisition geometry is not stated in the extract.",
            "25 ft (ground resolution ≈2.13 cm/pixel)",
            "Section 3, Datasets"),
        "availability_alignment": nr(
            "availability_alignment",
            "The study manipulates domain shift (field/crop/dataset) rather than sensor degradation; no blur, misregistration, illumination, band-dropout or occlusion stress is evaluated.",
            "[Checked Datasets and Results: no degradation/stress condition evaluated]",
            "Datasets and Results, absence check"),
        "temporal_design": nr(
            "temporal_design",
            "Acquisition dates, seasons and growth stages are not stated for the four datasets in the extract, so no temporal regime can be charted.",
            "[Checked Section 3: no acquisition date, season or growth stage stated]",
            "Section 3, absence check"),
        "split_protocol": rep("split_protocol", {
            "partition_unit": "heldout_field_same_farm_or_region",
            "spatial_leakage_risk": "low_buffered_blocks_or_independent_fields_flights",
            "target_domain_data_use": target_use,
        }, f"Each source/target pair uses distinct datasets/fields, and the train/val/test partition is held fixed across runs. Adaptation regime: {regime_label}.",
            "The train/val/test partition is held fixed across all runs",
            "Section 4, Training"),
        "fusion_mechanism": rep("fusion_mechanism", {
            "architecture_family": "two_stage_rcnn_detector_or_segmenter",
            "integration_topology": "single_modality_rgb_only",
            "matched_modality_ablation_present": False,
        }, "Faster R-CNN with a ResNet-50-FPN backbone inside the ALDI framework; RGB-only, no multimodal fusion.",
            "Faster R-CNN with a ResNet-50-FPN backbone",
            "Section 4, Training"),
        "uncertainty_calibration": nr(
            "uncertainty_calibration",
            "Seed variance is reported for repeatability, but no predictive-uncertainty method, calibration metric, abstention rule, or 'calibration' terminology is reported.",
            "[Checked Results: no predictive uncertainty or calibration metric reported]",
            "Results, absence check"),
        "metrics_comparators": rep("metrics_comparators", {
            "weed_class_specific_metrics_reported": False,
            "primary_metrics": {"map_50": metrics_value},
            "repeated_seeds_or_folds_count": 5 if (few or daod) else None,
            "variance_or_ci_reported": (few or daod),
        }, (("Few-shot k=25 reaches mAP@50 80.0 +/- 3.2 over M=5 label draws." if few
             else ("Zero-shot cotton->soybean transfer reaches mAP@50 57.8 against 76.8 in-domain." if zero
                   else "Unsupervised DAOD on cotton->soybean falls to 50.3 (Distill) or 42.8 (Align) from a source-only 57.8."))),
            "k=25 reaches 80.0±3.2" if few else ("Cotton →Soybean (57.8)" if zero else "Distill and Align fall to 50.3 and 42.8 from a source-only baseline of 57.8"),
            "Results, Q3" if few else ("Results, Q1" if zero else "Results, Q2")),
        "transfer_outcomes": rep("transfer_outcomes", {
            "shift_axes_tested": ["cross_field_same_crop", "cross_crop_species"],
            "adaptation_regime": adapt,
            "source_weed_metric_value": 0.768 if zero else 0.578,
            "target_weed_metric_value": metrics_value,
            "delta_transfer_drop": round(metrics_value - (0.768 if zero else 0.578), 4),
            "failed_transfer_documented": failed,
        }, (("Zero-shot cross-crop transfer collapses from 76.8 in-domain soybean mAP@50 to 57.8, a documented failure for most other pairs." if zero
             else ("Few-shot fine-tuning with k=25 labeled target examples reaches 80.0 mAP@50, above the 57.8 source-only baseline, recovering in-domain performance." if few
                   else "Out-of-the-box DAOD is inconsistent and degrades the cotton->soybean pair from 57.8 to 50.3/42.8, documenting failed unsupervised adaptation."))),
            "Most zero-shot transfer collapses to single-digits" if zero
            else ("few-shot fine-tuning with as few as 25 labeled target examples outperforms unsupervised DAOD" if few
                  else "applying a modern DAOD framework out of the box does not yield consistent improvements"),
            "Results, Q1" if zero else ("Results, Q3" if few else "Results, Q2")),
        "provenance_limits": rep("provenance_limits", {
            "missing_or_ambiguous_dimensions": [
                "acquisition dates/seasons not stated",
                "no radiometric calibration",
                "supplementary split table (A2) not in extract",
                "single region for primary data",
            ],
            "internal_contradictions_noted": None,
            "claimed_vs_demonstrated_gap": "aligned_claims_match_split_independence",
        }, (("The paper explicitly documents zero-shot failure and does not overclaim transfer; the limitation is that most analysis is one cotton->soybean pair." if zero
             else ("Few-shot gains are demonstrated on one learnable target (soybean); the authors note harder targets such as cotton do not recover." if few
                   else "DAOD failure is reported honestly; the authors note ALDI used default configuration, so the negative result is bounded."))),
            "its in-domain accuracy is not an indication of how far it will fall" if zero
            else ("source domain selection combined with modest target supervision is more productive" if few
                  else "results are highly variable"),
            "Results and Conclusion"),
        "open_science": rep("open_science", {
            "data_availability": "not_available_or_proprietary",
            "code_availability": "not_available",
            "license": None,
            "retraction_or_correction_status": "none_detected",
            "funding_and_coi_disclosed": False,
        }, "The paper introduces a new cotton dataset but gives no repository/access statement; no code repository is linked. AFOSR funding is disclosed, but no conflict-of-interest statement appears, so the combined disclosure field is false. DataCite check on 2026-10-31 found no retraction/correction relation.",
            "The authors gratefully acknowledge the generous support from AFOSR award",
            "Acknowledgements"),
    }


def build_rows() -> list[dict]:
    rows = [
        sci006("pea", "SET-01"),
        sci006("strawberry", "SET-02"),
        sci044(),
        sci041(),
        sci151("carrot", "SET-01", {
            "tiles": 60,
            "dataset_narrative": "CWFID: 60 top-down ground-robot images of an organic carrot field, annotated into soil/crop/weed.",
            "dataset_quote": "60 top-down looking images of 1,296 × 966 pixel size",
            "dataset_locator": "Section 3, CWFID",
            "sensor_narrative": "Ground robot with a multispectral camera; band set not enumerated and no GSD or flight altitude (not a UAV).",
            "sensor_quote": "mounted with multi-spectral camera",
            "sensor_locator": "Section 3, CWFID",
            "temporal_narrative": "Single 2013 acquisition before manual weed control.",
            "temporal_quote": "before applying manual weed control in 2013",
            "temporal_locator": "Section 3, CWFID",
            "metrics_narrative": "DeepLabV3+ overall accuracy 84.3% (kappa 0.82) on CWFID; weed-class accuracy 90.55% is also reported, but no run variance.",
            "metrics_quote": "DeepLab v3+ 84.3 0.82",
            "metrics_locator": "Results, Table 3",
        }),
        sci151("sugarcane", "SET-02", {
            "tiles": 60,
            "dataset_narrative": "Sugarcane orthomosaic from Northern Brazil split into 50-60 540x540 patches.",
            "dataset_quote": "We split this single orthomosic into 60 images",
            "dataset_locator": "Section 3, sugarcane",
            "sensor_narrative": "Fixed-wing UAV with a Canon G9X RGB camera at 125-200 m; 5 cm/px. Altitude is a range, so it is not charted as a single value.",
            "sensor_quote": "spatial resolution of 5 cm/",
            "sensor_locator": "Section 3, sugarcane",
            "temporal_narrative": "No date",
            "temporal_quote": "",
            "temporal_locator": "",
            "metrics_narrative": "DeepLabV3+ overall accuracy 70.99% (kappa 0.74) on sugarcane; no weed-specific value or run variance.",
            "metrics_quote": "DeepLab v3+ 70.99 0.74",
            "metrics_locator": "Results, Table 4",
        }),
        sci291(),
        sci372(blurred=False),
        sci372(blurred=True),
        sci607(synthetic=False),
        sci607(synthetic=True),
        sci644(),
        sci736("zero_shot", "SET-01"),
        sci736("few_shot", "SET-02"),
        sci736("daod", "SET-03"),
    ]
    for row in rows:
        row["coder_id"] = CODER_ID
        row["full_text_verified"] = True
    return rows


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_quotes(rows: list[dict]) -> list[str]:
    texts = {}
    for sid, fname in EXTRACTS.items():
        raw = (EXTRACTED / fname).read_text(encoding="utf-8", errors="replace")
        texts[sid] = _norm(raw.replace("\x00", " "))
    problems = []
    for row in rows:
        sid = row["study_id"]
        text = texts[sid]
        for dim, value in row.items():
            if not isinstance(value, dict) or "provenance" not in value:
                continue
            anchors = [value["provenance"]]
            anchors += value.get("additional_provenance", [])
            for a in anchors:
                if a["absence_check"]:
                    if len(a["verbatim_quote"].strip()) < 5:
                        problems.append(f"{sid} {row['setting_id']} {dim}: absence anchor too short")
                    continue
                q = _norm(a["verbatim_quote"])
                if q not in text:
                    problems.append(f"{sid} {row['setting_id']} {dim}: QUOTE NOT FOUND -> {a['verbatim_quote']!r}")
    return problems


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    sha = hashlib.sha256(canonical).hexdigest()
    # Hash of file bytes is the frozen instrument hash; verify it matches.
    file_sha = hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()
    if file_sha != SCHEMA_SHA256:
        raise SystemExit(f"BLOCKED_BASELINE_DRIFT: schema bytes sha {file_sha} != frozen {SCHEMA_SHA256}")

    rows = build_rows()
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for row in rows:
        for err in validator.iter_errors(row):
            errors.append(f"{row['study_id']} {row['setting_id']} {list(err.path)}: {err.message}")
    if errors:
        print("\n".join(errors))
        raise SystemExit(f"SCHEMA VALIDATION FAILED ({len(errors)} errors)")

    problems = verify_quotes(rows)
    if problems:
        print("\n".join(problems))
        raise SystemExit(f"QUOTE VERIFICATION FAILED ({len(problems)} problems)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "instrument": {
            "schema_path": "charting.schema.json",
            "schema_version": "v0.3.1",
            "schema_sha256": SCHEMA_SHA256,
            "codebook": "CHARTING_CODEBOOK.md",
        },
        "coder_id": CODER_ID,
        "coding_mode": "single_pass_agent",
        "dual_coding_status": "OUTSTANDING",
        "dual_coding_claim": False,
        "human_review_of_charting": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": rows,
    }
    OUT_ROWS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    summary = {
        "instrument_sha256": SCHEMA_SHA256,
        "coder_id": CODER_ID,
        "coding_mode": "single_pass_agent",
        "dual_coding_status": "OUTSTANDING",
        "rows_count": len(rows),
        "studies_count": len({r["study_id"] for r in rows}),
        "rows_by_study": {},
        "reported_dimensions": 0,
        "not_reported_dimensions": 0,
        "quotes_verified": 0,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    dims = [
        "study_reports", "task_context", "dataset_units", "sensor_inputs",
        "availability_alignment", "temporal_design", "split_protocol",
        "fusion_mechanism", "uncertainty_calibration", "metrics_comparators",
        "transfer_outcomes", "provenance_limits", "open_science",
    ]
    for row in rows:
        summary["rows_by_study"].setdefault(row["study_id"], []).append(row["setting_id"])
        for dim in dims:
            state = row[dim]["evidence_state"]
            if state == "reported":
                summary["reported_dimensions"] += 1
                summary["quotes_verified"] += 1
            else:
                summary["not_reported_dimensions"] += 1
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {OUT_ROWS}")
    print(f"Wrote {OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
