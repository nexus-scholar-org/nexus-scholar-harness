# Screening Criteria: Reliability and Generalization in UAV Crop-Weed Mapping: A Scoping Review

**Protocol ID**: `proto-20261012-uav-crop-weed-reliability`
**Lead Researcher**: Mouadh
**Playbook**: SCOPING_REVIEW
**Paradigm**: Pragmatist / Mixed Methods

## Context & Rationale
**Unit of Analysis**: Linked study/report families (collapsing preprints, conference proceedings, and dataset repositories into their primary journal report), with separate evaluation-setting rows for each materially distinct dataset/split/shift/target-data-use condition; repeated seeds are grouped within a setting.

Descriptive evidence mapping combines structured categorical counts with qualitative comparison of evaluation designs; it does not estimate pooled causal effects or assume generalization from reported in-distribution accuracy.

## Research Questions

### RQ1
**Question**: How do UAV crop-weed mapping studies define and evaluate reliability under spectral degradation, sensor differences, and temporal shift?
- **Required Evidence**: Primary empirical study or dataset/benchmark report with source-linked methods
- **Synthesis Type**: Descriptive evidence map and narrative comparison

### RQ2
**Question**: Which datasets, sensors, dates, fields, and split units support the reported generalization claims?
- **Required Evidence**: Primary empirical study or dataset/benchmark report with source-linked methods
- **Synthesis Type**: Descriptive evidence map and narrative comparison

### RQ3
**Question**: How are uncertainty, calibration, missing evidence, and failed transfer reported?
- **Required Evidence**: Primary empirical study or dataset/benchmark report with source-linked methods
- **Synthesis Type**: Descriptive evidence map and narrative comparison

### RQ4
**Question**: Which evidence gaps remain after separating dataset diversity, model mechanisms, and demonstrated external validation?
- **Required Evidence**: Primary empirical study or dataset/benchmark report with source-linked methods
- **Synthesis Type**: Descriptive evidence map and narrative comparison

## Inclusion Criteria

### INC-01
**Criterion**: Uses UAV-acquired imagery for crop/weed detection, segmentation, classification, or spatial weed mapping in an agricultural context (arable row crops, broadacre cereals, vegetables, or managed perennial orchards, vineyards, and pastures); UAV results must be separable in mixed-platform studies.
**Serves**: RQ1, RQ2, RQ3, RQ4

### INC-02
**Criterion**: Primary empirical method study or dataset/benchmark report describing a UAV crop/weed mapping method, experiment, or annotated dataset. Journal, conference, and substantive preprint reports are eligible (linked into study families). In-window method studies (2020-2026) evaluated on pre-2020 UAV datasets (e.g., WeedMap 2018) are eligible. Missing evaluation details are charted as not reported; records with missing abstracts matching UAV+weed title heuristics and inaccessible full texts remain pending retrieval/audit rather than auto-excluded.
**Serves**: RQ1, RQ2, RQ3, RQ4

### INC-03
**Criterion**: Published from 2020 through the recorded final search cutoff, inclusive; English full text in scope. Older foundational UAV datasets remain background/provenance sources unless a logged amendment expands eligibility. Screened under Option C (single lead reviewer Mouadh Bekhouche confirming all agent triage suggestions, with independent ~10% random sample plus boundary-exclude verification by Soumia Zertal and Fadhila Djenba).
**Serves**: RQ1, RQ2, RQ3, RQ4

## Exclusion Criteria

### EXC-01
**Criterion**: Satellite-only, ground-robot-only (including studies framed around field weed mapping that evaluate exclusively on proximal/ground datasets such as Sugar Beets 2016, CWFID, or DeepWeeds without UAV data), handheld, or laboratory/pot imaging with no separable eligible UAV mapping evidence.
**Rejection Reason Code**: `WRONG_PLATFORM`
**Serves**: RQ1, RQ2, RQ3, RQ4

### EXC-02
**Criterion**: UAV navigation/SLAM, yield estimation only, crop disease/pest damage, wildlife crop damage, crop lodging, phenotyping, or non-agricultural vegetation mapping (e.g., invasive aquatic weeds such as water hyacinth, forestry/wildfire, urban turfgrass) without a separable agricultural crop/weed localization, classification, or mapping task.
**Rejection Reason Code**: `WRONG_TASK`
**Serves**: RQ1, RQ2, RQ3, RQ4

### EXC-03
**Criterion**: Confirmed review (systematic, scoping, narrative, or bibliometric), editorial, commentary, protocol-only report, or standalone abstract with no associated substantive primary report. An incomplete search-provider abstract (abstract=null) or failure to retrieve full text is not this exclusion; retain useful reviews as background for citation chasing.
**Rejection Reason Code**: `WRONG_REPORT_TYPE`
**Serves**: RQ1, RQ2, RQ3, RQ4

### EXC-04
**Criterion**: Outside the frozen publication date (published before 2020 or after the recorded final search cutoff date) or non-English full text after bibliographic/full-text verification.
**Rejection Reason Code**: `OUTSIDE_DATE_LANGUAGE`
**Serves**: RQ1, RQ2, RQ3, RQ4

## Verification Constraints

- [x] Retraction check required
- [x] Conflict of Interest & Funding audit required
- [x] Reproducibility (Data/Code Availability) check required
- Minimum Trust Score: 0.0
