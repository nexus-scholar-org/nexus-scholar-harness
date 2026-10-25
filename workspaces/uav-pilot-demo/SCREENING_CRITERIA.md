# Screening Criteria: Reliability and Generalization in UAV Crop-Weed Mapping: A Scoping Review

**Protocol ID**: `proto-20261012-uav-crop-weed-reliability`
**Lead Researcher**: Mouadh
**Playbook**: SCOPING_REVIEW
**Paradigm**: Pragmatist / Mixed Methods

## Context & Rationale
**Unit of Analysis**: Linked study/report families, with separate evaluation-setting rows for each materially distinct dataset/split/shift/target-data-use condition; repeated seeds are grouped within a setting.

Descriptive evidence mapping combines structured counts with qualitative comparison of evaluation designs; it does not estimate pooled causal effects or assume generalization from reported accuracy.

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
**Criterion**: Uses UAV-acquired imagery for crop/weed detection, segmentation, or spatial weed mapping in an agricultural field context; UAV results must be separable in mixed-platform studies.
**Serves**: RQ1, RQ2, RQ3, RQ4

### INC-02
**Criterion**: Primary empirical method study or dataset/benchmark report describing a UAV crop/weed mapping method, experiment, or annotated dataset. Journal, conference, and substantive preprint reports are eligible. Missing evaluation details are charted as not reported; inaccessible full text remains pending retrieval rather than excluded.
**Serves**: RQ1, RQ2, RQ3, RQ4

### INC-03
**Criterion**: Published from 2020 through the recorded final search cutoff, inclusive; English full text in the provisional scope. Older foundational sources remain background unless a logged amendment expands eligibility.
**Serves**: RQ1, RQ2, RQ3, RQ4

## Exclusion Criteria

### EXC-01
**Criterion**: Satellite-only, ground-robot-only, handheld, or laboratory imaging with no separable eligible UAV mapping evidence.
**Rejection Reason Code**: `WRONG_PLATFORM`
**Serves**: RQ1, RQ2, RQ3, RQ4

### EXC-02
**Criterion**: UAV navigation/SLAM, yield, disease, phenotyping, or non-agricultural mapping without a separable crop/weed localization or mapping task.
**Rejection Reason Code**: `WRONG_TASK`
**Serves**: RQ1, RQ2, RQ3, RQ4

### EXC-03
**Criterion**: Confirmed review, editorial, commentary, protocol-only report, or abstract-only publication with no associated substantive primary report. An incomplete search-provider abstract or failure to retrieve full text is not this exclusion; retain useful reviews as background.
**Rejection Reason Code**: `WRONG_REPORT_TYPE`
**Serves**: RQ1, RQ2, RQ3, RQ4

### EXC-04
**Criterion**: Outside the frozen publication date or language scope after bibliographic/full-text verification.
**Rejection Reason Code**: `OUTSIDE_DATE_LANGUAGE`
**Serves**: RQ1, RQ2, RQ3, RQ4

## Verification Constraints

- [x] Retraction check required
- [x] Conflict of Interest & Funding audit required
- [x] Reproducibility (Data/Code Availability) check required
- Minimum Trust Score: 0.0
