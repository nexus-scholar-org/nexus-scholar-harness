# Charting codebook v0.2 — provisional

This research-local profile is separate from the compiler's 13 optional narrative
dimensions. Those dimensions produce preliminary notes, not accepted charting.
[charting.schema.json](charting.schema.json) validates structure, vocabulary,
evidence-state requirements and the exact current protocol fingerprint. It is
not a new Contract registry type, acceptance gate, or automatic evidence verifier.

## Units and denominators

One study row represents one linked report family. Preserve publication and
preprint versions and use the most complete current report while retaining
contradictions. A distinct primary experiment remains a distinct study even
when it reuses another study's dataset. Do not merge studies merely by title or DOI.

An evaluation row refers to its study and represents one materially distinct
dataset/split/shift/target-data-use condition. Separate clean versus stressed
settings and direct transfer versus adaptation. Group repeated seeds under a
setting; report counts and variation there. evaluation_key is a local row label,
not a newly minted Contract identity. Add explicit setting definitions when
categories combine multiple axes. Count studies, reports, settings and datasets
separately; shared datasets do not establish independent replication.

## Controlled fields

| Field | Reported value vocabulary |
|---|---|
| task | detection, semantic_segmentation, instance_segmentation, spatial_mapping, multiple |
| method_family | deep_learning, other_machine_learning, object_based, rule_based, mixed |
| report_type | journal, conference, preprint, dataset_report, mixed |
| split_unit | pixel, patch_or_tile, image, orthomosaic, plot, field, flight, date, season, site, sensor, multiple |
| shift_axes | none, spectral_degradation, sensor, field, site, date, season, growth_stage, class_prior, combined |
| temporal_design | single_date, multiple_dates_no_heldout, sequence_modeling_no_heldout, heldout_date, heldout_season, sequence_modeling_with_heldout, multiple |
| target_data_use | none, unlabeled_adaptation, labeled_finetuning, target_training, target_validation_selection, multiple |
| uncertainty_evaluation | none, estimated_only, calibration_evaluated, selective_prediction_evaluated, calibration_and_selective_prediction |
| stress_origin | none, synthetic, observed, both |
| sensor_awareness | none, band_availability, sensor_or_band_metadata, learned_band_fusion, multiple |

Use multiple/combined only with an explanation in the setting definition. Split
independence is determined by actual assignments, not the authors' terminology.
Sequence modeling and held-out-time evaluation are separate properties.
Target validation used to select a model is target-data use. Learned fusion is
not calibrated uncertainty or proof of sensor transfer.

Narrative study cells: report_family, dataset_provenance, crop_context, open_science.
Narrative setting cells: setting_definition, sensor_bands, group_counts,
metrics_and_controls, transfer_result, seeds_and_intervals, limitations.
Record units, class-specific metrics, comparator conditions, original numbers,
and direction of negative results; no cross-dataset leaderboard is implied.

## Evidence states and provenance

Every cell has state, value, evidence and note. Required cells can honestly be
unknown; required never means invent a measured value.

- reported: a source supports the value; at least one quotation/locator is required.
- not_reported: the available relevant sections were checked; value is null and
  the note records the inspected scope. Silence is not an explicit negative.
- unavailable: the necessary source/section cannot be inspected; value is null.
- conflicting: at least two supported incompatible statements are retained;
  value is null pending recorded resolution, with both source references.
- not_applicable: a justified inapplicability, not missing information; value is null.

Explicitly reported none is a reported value with evidence. Measured zero is a
reported metric, never missing data. Each evidence entry contains accepted
document_id, exact source checksum, locator and verbatim quotation. Derived
interpretations need supporting inputs and a derivation note. Schema validation
does not verify document acceptance, checksum resolution, quotation occurrence,
or entailment; reviewer/source checks remain mandatory.

Relational checks before acceptance: unique study_id, unique (study_id,
evaluation_key), every evaluation links an existing study, and no evidence links
an unassigned source. Those checks are not supplied by basic JSON Schema.
Do not create real rows or fabricate IDs during protocol revision.

## Coding examples (illustrative, not literature findings)

- Images collected on three dates, randomly split across tiles: temporal_design
  is multiple_dates_no_heldout; split_unit is patch_or_tile. Do not code heldout_date.
- Source sensor trained and target labels used for fine-tuning: target_data_use
  is labeled_finetuning. This is not direct transfer without adaptation.
- Attention weights described but no calibration experiment: record the fusion
  mechanism; uncertainty_evaluation is not_reported unless explicit evidence
  supports estimated_only or none.

Pilot this codebook on a few full texts before freeze and revise with logged
reasons. No completed charting corpus is created here.
