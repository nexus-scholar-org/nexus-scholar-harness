# Charting pilot — eligibility dry run + abstract-only charting limits

> Historical calibration record. [Senior review](SENIOR_REVIEW.md) corrects sentinel/report-type and recall interpretations; [delegated decisions](RESEARCHER_DECISIONS.md) supersede the open choice list. No formal screening or independent human labels are claimed.

Date: 2026-10-12/13 (UTC). 4 deliberately varied records from the executed Q2
calibration page (year-filtered OpenAlex, 25 records, 23/25 with abstracts).
Judgments apply SCREENING_CRITERIA.md (INC-01..03 / EXC-01..04) at
title/abstract level with criterion-specific reasons. No formal screening; no
corpus; no `literature/` writes.

## Dry-run records and screening judgments

### D1 — CLEAR INCLUDE: WeedsGalore (S1)

- DOI `10.1109/wacv61041.2025.00467`, WACV 2025, in-window.
- Evidence: verified Crossref record + abstract (see SENTINELS.md). Abstract
  describes a multispectral multitemporal UAV dataset for crop/weed
  segmentation in maize with baseline experiments, probabilistic uncertainty
  quantification, calibration, and out-of-distribution testing.
- Judgment: **INCLUDE (provisional, advances to full-text charting).**
  INC-01 met (UAV crop/weed segmentation, field setting); INC-02 met
  (dataset/benchmark report with experiments); INC-03 met provisionally (2025;
  full-text language still to verify). No exclusion triggered.

### D2 — CLEAR EXCLUDE: vine disease detection (title-only, no abstract)

- DOI `10.1016/j.compag.2020.105446`, Computers and Electronics in Agriculture,
  2020. Title: "Vine disease detection in UAV multispectral images using
  optimized image registration and deep learning segmentation approach".
- Evidence: title + venue + year from provider metadata; **abstract NONE**
  (one of 2/25 Q2 records without abstracts).
- Judgment: **EXCLUDE per EXC-02 (WRONG_TASK)** — disease detection /
  phenotyping-type task with no crop/weed localization in the title evidence.
  Caveat recorded: exclusion rests on title only; per PROTOCOL.md, genuinely
  ambiguous records advance to full text, but a disease-detection title with no
  weed signal is a reasonable title-level WRONG_TASK exclusion. Also
  demonstrates missing-abstract handling: provider metadata gaps are retrieval
  states, not evidence.

### D3 — BOUNDARY (provisional include): UAV + PlanetScope maize weed mapping

- DOI `10.3390/su151813416`, Sustainability, 2023. Title: "Weed Detection in
  Rainfed Maize Crops Using UAV and PlanetScope Imagery".
- Evidence: provider abstract states the objectives as assessing mapping
  precision with "multi-temporal, unmanned aerial vehicle (UAV), and
  PlanetScope data", using RF and SVM on spectral bands/indices/PCA inputs,
  with "eight experiments … conducted, four experiments each for UAV and
  PlanetScope datasets spanning four months" (provider abstract snippet,
  truncated in session output).
- Judgment: **PROVISIONAL INCLUDE, full text required.** INC-01's
  mixed-platform clause is the deciding test: the abstract suggests separable
  per-platform experiments (four UAV + four satellite), which would satisfy
  "UAV results must be separable" — but separability of reported metrics must
  be confirmed at full text, not assumed from the abstract. INC-02 met
  (primary empirical study); INC-03 met provisionally (2023).
- Why boundary: exercises the exact clause most likely to generate
  reviewer disagreement (platform separability) and the temporal axis
  (four-month multi-temporal acquisition vs held-out-date testing — abstract
  does not establish a held-out design).

### D4 — BOUNDARY (provisional exclude): UAV + deep learning weed-management overview

- DOI `10.3390/agronomy14030494`, Agronomy, 2024. Title: "Advancements of UAV
  and Deep Learning Technologies for Weed Management in Farmland".
- Evidence: provider abstract "provides an overview of the development of UAV
  platforms, … types and characteristics of data …, and discusses the
  application of deep learning technology in weed detection" and "presents
  current advancements" (provider abstract snippet, truncated in session output).
- Judgment: **PROVISIONAL EXCLUDE per EXC-03 (WRONG_REPORT_TYPE)** — reads as
  a review/overview with no separable primary experiment; **retain as
  background** per protocol (useful reviews are background, and overlap with
  existing reviews must be checked before gap claims). Full-text check required
  before the exclusion is final: if a separable primary experiment exists
  inside, the verdict flips to include.

## Charting rows (one per included record: D1, D3)

Two pilot study rows (`STU-PILOT-01` ← D1, `STU-PILOT-02` ← D3) plus one
evaluation row each were drafted from abstracts only and structurally
validated (see below). **Every cell is `state: unavailable`, `value: null`** —
deliberately. Rationale, per CHARTING_CODEBOOK.md §Evidence states:

- `reported` requires an accepted `DOC-*` source with exact checksum, locator,
  and verbatim quotation. No document registry exists at calibration stage;
  fabricating `DOC-*` IDs or `sha256:…` checksums to force `reported` states
  would be invented provenance, so no controlled-vocabulary value (task,
  method_family, split_unit, temporal_design, …) was coded from abstracts —
  even where the abstract hints at it (e.g. S1's "multitemporal" ≠
  `heldout_date`; D3's "four months" ≠ held-out design; S1's "probabilistic
  methods" ≠ `calibration_evaluated`).
- `not_reported` requires the relevant full-text sections to have been checked
  — they were not. `unavailable` is therefore the only honest state, with notes
  recording what the abstract suggests but does not establish.

Rows file: `calibration/_tmp_charting_pilot_rows.json` (2 studies, 2 evaluations).

Structural validation (executed):

```text
uv run python -c "import json, jsonschema; ..."  # Draft202012Validator against charting.schema.json
=> ERRORS: 0 / studies: 2 evaluations: 2
```

Validator: `jsonschema` 4.26.0 (Draft 2020-12). Structural conformance holds;
relational checks (unique study_id, evaluation linkage) hold by construction
and were confirmed in the same read (2/2). Schema validation does NOT verify
source acceptance, quotation, or entailment — there is nothing to entail yet.

## Finding: abstract-only charting limits

1. Title/abstract screening CAN render criterion-specific verdicts (D1–D4 above),
   including provisional boundaries with explicit full-text tests.
2. Title/abstract evidence CANNOT populate a single charting evidence cell
   under this codebook: 100% of pilot cells are `unavailable`, because every
   substantive value needs an accepted, checksummed, quoted source.
3. Consequence for planning: charting throughput is gated entirely on full-text
   retrieval + document acceptance, not on screening speed. The review's
   timeline estimate should budget retrieval/acceptance as the bottleneck, and
   the pilot-before-freeze requirement in the codebook should be re-run on 2–3
   full texts (not abstracts) before freeze.
4. Incidental retrieval finding: 2/25 Q2 records lacked abstracts entirely
   (`10.1016/j.eja.2024.127289`, `10.1016/j.compag.2020.105446`) — abstract
   availability is itself a retrieval state to track at screening.
