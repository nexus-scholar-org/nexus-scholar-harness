# Verified sentinels - UAV crop/weed reliability pilot

> Historical calibration record. [Senior review](SENIOR_REVIEW.md) corrects sentinel/report-type and recall interpretations; [delegated decisions](RESEARCHER_DECISIONS.md) supersede the open choice list. No formal screening or independent human labels are claimed.

> Historical calibration record. [Senior review](SENIOR_REVIEW.md) corrects sentinel/report-type and recall interpretations; [delegated decisions](RESEARCHER_DECISIONS.md) supersede the open choice list. No formal screening or independent human labels are claimed.

Date: 2026-10-12/13 (UTC). Every record below was independently verified with
`uv run scholar-search verify ... --enrich` (Crossref/OpenAlex backends) from
repo root. No metadata invented; failed verifications recorded honestly.
`protocol.json` / `golden_seeds` NOT touched (empty by compiler design).

## Verification commands (exact)

```text
uv run scholar-search verify "workspaces/uav-crop-weed-reliability/calibration/_tmp_verify_input.json" --enrich
uv run scholar-search verify "workspaces/uav-crop-weed-reliability/calibration/_tmp_verify_input.json" --enrich --output "workspaces/uav-crop-weed-reliability/calibration/_tmp_verify_output.json"
=> Loaded 1 records / Verified: 1/1 documents confirmed real.

uv run scholar-search verify "workspaces/uav-crop-weed-reliability/calibration/_tmp_verify2_input.json" --enrich --output "workspaces/uav-crop-weed-reliability/calibration/_tmp_verify2_output.json"
=> Loaded 4 records / Verified: 3/4 documents confirmed real. / Warning: 1 records could not be verified in Crossref/OpenAlex.

uv run scholar-search verify "workspaces/uav-crop-weed-reliability/calibration/_tmp_verify3_input.json" --enrich --output "workspaces/uav-crop-weed-reliability/calibration/_tmp_verify3_output.json"
=> Loaded 4 records / Verified: 4/4 documents confirmed real.
```

## Failed / rejected candidates (exact failures)

- `10.3389/fpls.2022.930819` (my constructed guess for the SemiWeedNet paper):
  **could not be verified** - returned as `Untitled`, provider `local_json`.
  The suffix was never confirmed; DISCARDED, not a sentinel. (Lesson: the true
  DOI found via OpenAlex search output was `10.3389/fpls.2022.927368`.)
- `10.1016/j.neucom.2023.126898` (my constructed guess for the lightweight
  vision-transformer weed-mapping paper): resolved to a DIFFERENT paper -
  "Advances in teaching-learning-based optimization algorithm: A comprehensive
  survey (ICIC2022)". Wrong-paper match; DISCARDED, not a sentinel.

## Selected sentinels (5)

### S1 - WeedsGalore (clear include; dataset + uncertainty + OOD)

- DOI: `10.1109/wacv61041.2025.00467` (canonical; OpenAlex ID
  `https://openalex.org/W4409263155`).
- Title: "WeedsGalore: A Multispectral and Multitemporal UAV-Based Dataset for
  Crop and Weed Segmentation in Agricultural Maize Fields".
- Venue: 2025 IEEE/CVF Winter Conference on Applications of Computer Vision
  (WACV). Year: **2025** - in window. Provider: crossref.
- Language: metadata carries no language tag; abstract is English; full-text
  language NOT yet verified (feeds the English-assumption decision).
- Citations: 28 (Crossref verify) / 26 (OpenAlex search display) - counts are
  provider snapshots, not findings.
- Boundary rationale: the STRONG positive control - in-window UAV multispectral
  multitemporal dataset report whose abstract explicitly mentions probabilistic
  uncertainty quantification, model calibration, and out-of-distribution
  applicability. Any recall failure on S1 is a retrieval defect, not a scope
  question.

### S2 - WeedMap (out-of-window foundation; background-only boundary)

- DOI: `10.3390/rs10091423`. Title: "WeedMap: A Large-Scale Semantic Weed
  Mapping Framework Using Aerial Multispectral Imaging and Deep Neural Network
  for Precision Farming".
- Venue: Remote Sensing. Year: **2018 - OUTSIDE the 2020â†’ window**.
- Boundary rationale: tests the date criterion (EXC-04 / INC-03). Expected
  verdict under current scope: EXCLUDE on date, retain as background. If the
  researcher expands the window, S2 becomes the first re-screen candidate.
  S2 must never count toward in-window recall.

### S3 - SemiWeedNet (in-window method study; target-data-use boundary)

- DOI: `10.3389/fpls.2022.927368`. Title: "Semi-supervised Learning for Weed
  and Crop Segmentation Using UAV Imagery".
- Venue: Frontiers in Plant Science. Year: **2022** - in window.
- Boundary rationale: semi-supervised use of unlabelled images directly probes
  the `target_data_use` charting axis (none vs unlabeled_adaptation vs
  target_training) - the kind of record where charting, not exclusion, carries
  the evidence. Provisional verdict: INCLUDE (full-text confirms setting).

### S4 - Transformer in UAV Image-Based Weed Mapping (report-type boundary)

- DOI: `10.3390/rs15215165`. Title: "Transformer in UAV Image-Based Weed
  Mapping". Venue: Remote Sensing. Year: **2023** - in window.
- Boundary rationale: title/abstract read as an overview-style report -
  exercises EXC-03 (confirmed review/editorial/commentary exclusion) vs
  primary-study inclusion. Provisional verdict: likely EXCLUDE as
  WRONG_REPORT_TYPE with retention as background, pending full-text
  confirmation that no separable primary experiment exists.

### S5 - Precision weed detection review (report-type + date-cutoff boundary)

- DOI: `10.1016/j.atech.2025.101656`. Title: "Precision weed detection using
  UAVs and deep learning: Models, paradigms, and challenges".
- Venue: Smart Agricultural Technology. Year: **2026 per Crossref verify vs
  2025 per OpenAlex search display** - provider year discrepancy recorded;
  abstract self-describes as "This review explores the state-of-the-art-¦".
- Boundary rationale: double boundary - (a) review report type (EXC-03
  candidate, background retention); (b) sits at the window's upper edge, where
  the *unclaimed final search cutoff date* decides eligibility. Demonstrates
  why the cutoff date must be frozen and why year filters are coarse
  (SEARCH_STRATEGY.md Â§Coverage).

## Sentinel set coverage

5 sentinels: 1 clear include (S1), 1 out-of-window foundation (S2),
1 in-window method boundary (S3), 2 report-type/date boundaries (S4, S5).
All have verified DOI + title + year; rationale per record above.
