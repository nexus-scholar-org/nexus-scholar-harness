# Charting Codebook — UAV Crop-Weed Mapping Reliability & Generalization

**Protocol ID**: `proto-20261012-uav-crop-weed-reliability`
**Schema**: `schemas/v1/charting.schema.json`
**Status**: Pilot-Then-Freeze (Decision #6)

> **FROZEN v0.3.1 — 2026-10-31.** This codebook governs charting in
> `workspaces/uav-crop-weed-v03/` and supersedes the pilot `charting sidecar v0.2`
> for this workspace. It repairs limitation F1: `evidence_state` now governs the
> dimension's values and provenance (§2.1). SHA-256 of the instrument:
> `91dbe0c8f81034ccb5f7eea903a11d3d96e9a50bc42914eea6ec7d0fe7596b42`.
> The superseded v0.3.0 bytes are kept as
> `audit/charting_schema_v030_superseded.json`, and the freeze record is
> `validation_v031.json`. Reference-anchor metric values below are
> UNVERIFIED-DRAFT transcriptions from the definitive harvest abstracts and must
> be re-verified against retrieved full texts before dual-coding.

---

## 1. Fundamental Charting Rules & Unit of Analysis

1. **Full-Text Mandate**: Formal charting (`full_text_verified: true`) is strictly prohibited on title/abstract metadata alone. If a paper's full text has not yet been retrieved, its record remains in `pending_retrieval` and is never charted as `not_reported`.
2. **Study Families (`study_id`) vs. Evaluation-Setting Rows (`setting_id`)**:
   - All reports of the same underlying study (e.g., an arXiv/bioRxiv/SSRN preprint, a conference paper, a journal extension, and a Zenodo dataset deposit) share a single `study_id` (`STU-*` or primary `SCI-*`), documented in `study_reports.linked_reports`.
   - Create a **separate charting row (`SET-01`, `SET-02`, ...)** whenever any of the following changes within a study:
     1. **Dataset / Crop** (e.g., evaluating on *WeedMap RedEdge* vs. *WeedMap Sequoia*, or *Barley* vs. *Rapeseed*).
     2. **Split Independence Protocol** (e.g., `AAMBERS-UAV` comparing *target-held-out* `SET-01` vs. *target-exposed* `SET-02`, or `BAWSeg` comparing *in-year block split* `SET-01` vs. *cross-plot* `SET-02` vs. *cross-year* `SET-03`).
     3. **Physical Stress / Degradation Condition** (e.g., `DeBlurWeedSeg` evaluated on *sharp test images* `SET-01` vs. *naturally motion-blurred test images* `SET-02`).
     4. **Target-Domain Adaptation Regime** (e.g., *zero-shot direct transfer* `SET-01` vs. *15% few-shot fine-tuning* `SET-02`).
   - **Do NOT create separate rows** for repeated random seeds, $k$-fold cross-validation folds of the same split design, or standard backbone comparisons (e.g., ResNet-50 vs. EfficientNet-B0 on the exact same split). Group repeated seeds within the setting and record the best/primary proposed model alongside comparator notes in `metrics_comparators`.

---

## 2. Epistemic Evidence States (`evidence_state`)

Never collapse missingness into a single null value. Every dimension must be tagged with one of five mutually exclusive states:
- **`reported`**: Explicitly stated in the verified full text or official repository, backed by a verbatim quote and section/page/table locator.
- **`not_reported`**: Full text is in hand and inspected, but the authors omitted this methodological detail (e.g., stating an "80:10:10 split" without specifying whether tiles were drawn randomly from the same orthomosaic or separated by field/block).
- **`unavailable`**: Full text, supplementary table, or external dataset documentation required to verify this field could not be accessed.
- **`conflicting`**: The paper contains internal contradictions (e.g., text in Section 2 claims "independent field testing," but Figure 3 shows train and test tiles checker-boarded inside the same orthomosaic). Record both quotes in `provenance_limits.internal_contradictions_noted`.
- **`not_applicable`**: The dimension structurally does not apply to the setting (e.g., `fusion_mechanism.integration_topology` for a single-stream RGB-only model, or `transfer_outcomes.delta_transfer_drop` for an `in_distribution_only` experiment).

### 2.1 State governs content and provenance (v0.3.1)

`evidence_state` is the **claim**; the dimension's values and provenance are its
**evidence**. The schema enforces this per dimension, so a state word can no
longer coexist with contradicting content:

| `evidence_state` | Value fields | Provenance |
| :--- | :--- | :--- |
| `reported` | primary values present (enums non-null, required arrays non-empty) | ≥1 anchor with `absence_check: false` quoting the reported content |
| `not_reported` | all null / `[]` | one anchor with `absence_check: true` recording the explicit absence check |
| `unavailable` | all null / `[]` | one anchor with `absence_check: true` naming the access failure, not a content quote |
| `not_applicable` | all null / `[]` | one anchor with `absence_check: true` quoting why the dimension does not apply |
| `conflicting` | all null / `[]` — no single value may be asserted | `provenance` + ≥1 `additional_provenance`, every `absence_check: false`, with mutually inconsistent quotes; `narrative_summary` describes the conflict |

Three consequences coders must internalise:

1. **`false` is not "unknown".** The six boolean fields
   (`matched_modality_ablation_present`, `abstention_or_validity_rejection`,
   `weed_class_specific_metrics_reported`, `variance_or_ci_reported`,
   `failed_transfer_documented`, `funding_and_coi_disclosed`) are tri-state:
   `false` means *reported as no*, `null` means *we cannot tell*. In a
   non-`reported` state every boolean must be `null`.
2. **Absence lives in the state, not in an enum value.** `not_reported` was
   removed from the value enums (including `agricultural_setting`,
   `weed_granularity`, `independent_unit_level`, `radiometric_calibration`,
   `temporal_regime`, `partition_unit`, `integration_topology`, `stress_origin`,
   `data_availability` and `code_availability`). `spatial_leakage_risk:
   "unclear_not_reported"` remains: it is an assessed *reported* value about the
   paper's own ambiguity, not the absence of a statement. `not_applicable` stays
   a value only where it is the reported content (e.g.
   `radiometric_calibration`, `claimed_vs_demonstrated_gap`).
3. **`primary_publication_type` is the one exception.** It stays required and
   non-null in `study_reports` under every state, because it is bibliographic
   metadata about the record rather than a finding about the study.

`narrative_summary` is required (non-empty) in every state and must explain the
absence or the conflict — "not reported" alone is not a narrative.

---

## 3. Operational Coding Rules for High-Risk Dimensions

### A. `temporal_design` (Resolution of Decision #6: `heldout_date` vs. `multiple_dates_no_heldout`)
Studies frequently collect UAV flights across multiple dates or growth stages (`BBCH` stages) and claim "multi-temporal robustness." Coders must apply this strict decision tree:
1. **`single_date_snapshot`**: Imagery acquired during a single flight campaign/date (or single growth stage per field with no temporal axis).
2. **`multiple_dates_pooled_no_heldout`**: Imagery acquired across $\ge 2$ dates or growth stages, but images/tiles from **all dates are pooled together** before performing a random or spatial train/val/test split. *(Training set contains samples from every test date).*
3. **`multi_stage_stratified_no_heldout`**: Metrics are reported separately per growth stage (e.g., BBCH 15 vs. BBCH 17 vs. BBCH 19), either by training separate stage-specific models or evaluating on stage-stratified test subsets where the model was trained on all stages.
4. **`heldout_date_or_growth_stage_same_season`**: Model is trained **exclusively** on earlier/subset acquisition dates ($t_1, \dots, t_k$) and evaluated on a **completely unseen acquisition date or growth stage ($t_{k+1}$)** within the same growing season (zero frames from $t_{k+1}$ in training or validation).
5. **`heldout_cross_season_or_cross_year`**: Model is trained on data from Year/Season $Y_1$ (e.g., 2022–2024) and evaluated on an unseen growing season/year $Y_2$ (e.g., 2025), as in `BAWSeg`.
6. **`explicit_time_series_sequence_model`**: Model architecture explicitly ingests sequential multi-date registered tensors $(X_{t_1}, X_{t_2}, \dots, X_{t_k})$ of the same spatial plot over time.

### B. `split_protocol` & Spatial Autocorrelation Leakage
1. **`random_tile_or_pixel_same_orthomosaic`** (`spatial_leakage_risk: high_overlapping_or_random_tiles_from_same_flight`): A single orthomosaic or flight campaign is cropped into tiles/patches (e.g., $256\times 256$ or $512\times 512$) and randomly partitioned into train/val/test sets. Adjacent or overlapping tiles share identical soil moisture, illumination, row angle, and weed patch boundaries.
2. **`spatial_block_or_strip_same_field`**: The field/orthomosaic is geographically partitioned into non-overlapping contiguous sub-blocks or strips (e.g., East half train, West half test, or leakage-free block splits with buffer zones).
   - Tag `low_buffered_blocks_or_independent_fields_flights` if a spatial buffer/gap separates train and test blocks; tag `moderate_unbuffered_adjacent_blocks_or_frames` if blocks touch along a shared pixel boundary.
3. **`heldout_flight_or_acquisition_same_field`**: Train and test sets come from physically separate UAV flights/acquisitions (`AAMBERS-UAV` target-held-out protocol).
4. **`heldout_field_same_farm_or_region`** vs. **`heldout_geographic_location_or_farm`**: Distinguish holding out an adjacent paddock on the same experimental station (e.g., `WeedMap` Eschikon vs. Rheinbach or `Cox et al.` 12 eastern England cereal fields) from holding out a geographically distant farm/region.

### C. `uncertainty_calibration` (Disambiguating "Calibration" Traps)
Three completely different concepts are called "calibration" in UAV agricultural papers:
1. **Radiometric Sensor Calibration** (Downwelling Light Sensor / CRS reflectance panel) $\rightarrow$ Code under **`sensor_inputs.radiometric_calibration`**, and set `uncertainty_calibration.false_calibration_terminology_trap = "radiometric_sensor_panel_called_calibration"` if the text conflates them.
2. **Hardware Quantization Calibration** (e.g., TensorRT FP32-to-FP16 or INT8 post-training quantization "precision calibration" in `Deng et al. 2020`) $\rightarrow$ Set `uncertainty_calibration.uncertainty_method = "none"` and `false_calibration_terminology_trap = "hardware_quantization_fp16_int8_called_calibration"`.
3. **Statistical Predictive Uncertainty & Probability Calibration** (e.g., MC Dropout, Deep Ensembles, Dirichlet/evidential heads, temperature scaling, Expected Calibration Error `ECE`, Brier score, reliability diagrams in `WeedsGalore`, or validity rejection gates like `IRCR` in `Moldvai et al. 2025`) $\rightarrow$ Code under **`uncertainty_calibration`**.

### D. `metrics_comparators` (Weed-Class Isolation Rule)
In agricultural UAV imagery, soil/background and crop canopy often account for **85%–98% of pixels**. Consequently, a model that predicts **0% of weeds** can still achieve $>90\%$ Overall Accuracy (`OA`) and $>60\%$ 3-class `mIoU`.
- Always check whether the paper reports **weed-class-specific `weed_iou`, `weed_f1_or_dice`, or `map_50`**.
- If only `overall_accuracy` or background-inclusive `mean_iou` is reported without class-wise breakdown, set `weed_class_specific_metrics_reported = false` and flag it in `provenance_limits`.

---

## 4. Pilot Dual-Coding Reference Anchor (3 Contrasting Studies from Harvest)

> UNVERIFIED-DRAFT: every number below must be confirmed against the retrieved
> full text and the verbatim quote recorded in the row before any freeze. Strike
> anything not found verbatim in the paper.

| Study / Setting | `temporal_design` | `split_protocol` | `availability_alignment` | `uncertainty_calibration` | `transfer_outcomes` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. `BAWSeg` (`SCI-000011`, 2026)**<br>`SET-01` (In-domain)<br>`SET-02` (Cross-plot)<br>`SET-03` (Cross-year) | `heldout_cross_season_or_cross_year` (4-year dataset; cross-year protocol in `SET-03`) | `spatial_block_or_strip_same_field` (leakage-free block splits in `SET-01`/`02`; `heldout_year_or_season` in `SET-03`) | `radiometric_or_illumination_drift` + `canopy_occlusion_or_high_weed_density` (calibrated 5-band reflectance panel) | `none` | `SET-01`: mIoU 75.6% (weed IoU 63.5%)<br>`SET-02`: mIoU 71.2% ($\Delta = -4.4$)<br>`SET-03`: mIoU 69.2% ($\Delta = -6.4$) |
| **2. `WeedsGalore` (`SCI-000023`, 2025)**<br>`SET-01` (RGB vs. MSI)<br>`SET-02` (OOD evaluation) | `multiple_dates_pooled_no_heldout` / multitemporal maize flights (check full text for date-holdout split) | Check full-text split unit (`spatial_block` vs. `frame`) | `none_assumed_ideal` (evaluates RGB vs. RGB+RE+NIR band availability) | `probabilistic_output_head` / `post_hoc_calibration_ECE_Brier` (explicitly quantifies prediction uncertainty & calibration) | Evaluates OOD applicability (`zero_shot_direct_transfer`) |
| **3. `Ludeña et al.` (`SCI-000030`, 2026)**<br>`SET-01` (Barley in-field)<br>`SET-02` (Barley cross-field)<br>`SET-03` (Rapeseed 0-shot)<br>`SET-04` (Rapeseed few-shot) | `single_date_snapshot` per field | `SET-02`: `heldout_field_same_farm_or_region`<br>`SET-03`: `zero_target_exposure_strict_holdout`<br>`SET-04`: `labeled_target_few_shot_or_fine_tuning` | `none_assumed_ideal` (tests 4 spectral band configurations) | `none` (outputs weed probability map without calibration metrics) | `SET-01`: Weed F1 = 0.5833<br>`SET-02`: Weed F1 = 0.6455<br>`SET-03`: **Failed transfer** to rapeseed (F1 = 0.0534, $\Delta = -0.5299$, `failed_transfer_documented = true`)<br>`SET-04`: Few-shot (63 patches / 15%) recovers F1 = 0.6274 |
