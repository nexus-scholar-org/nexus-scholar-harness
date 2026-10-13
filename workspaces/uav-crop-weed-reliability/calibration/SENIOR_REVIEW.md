# Senior research verification — calibration corrections

## Verdict

Development calibration is useful; formal search/screening, independent human
reference labels and accepted charting remain uncompleted. Original calibration
artifacts and audit rows are retained. This review supersedes their interpretations
where explicitly corrected below; it does not rewrite historical measurements.

## Corrected sentinel roles

| Sentinel | Current role | Source-backed reason |
|---|---|---|
| S1 WeedsGalore | Positive eligibility/recall candidate | UAV maize segmentation dataset/method and uncertainty experiments; full-text preprint inspected. |
| S2 WeedMap 2018 | Date-negative/background probe | Outside selected 2020 lower bound. |
| S3 SemiWeedNet | Positive eligibility/recall candidate | Publisher original research, UAV RGB crop/weed segmentation. |
| S4 Transformer in UAV Image-Based Weed Mapping | Positive eligibility/recall candidate; prior likely-review label corrected | Publisher methods describe model design, ablations and ground-reference validation. Title alone misled the prior classification. |
| S5 Precision weed detection review | Report-type/background probe; date provenance retained | Review is outside the primary empirical corpus irrespective of the 2025/2026 indexing disagreement. Publisher issue is March 2026. |

These are preliminary calibration classifications, not collected/accepted final
screening decisions. Never use S2 or S5 as records the primary search must include.
The query log's 4/4 in-window hits mix eligible positives and a review boundary.
verification.json recomputes eligible-positive coverage using S1/S3/S4, plus all
five development-probe hits separately. Both are coverage of a 25-result page,
not search sensitivity or a held-out performance estimate.

## Query interpretation

The year filter recovered S1 within the tested OpenAlex top-25 window. Keep it
for further calibration, but do not conclude year filtering alone establishes
recall-safe retrieval. Ranking, budget, query translation and pagination all
matter. No location of S1 beyond the unfiltered top 25 was measured. Complete
retrieval and additional sources remain open. A pending validation retry is not
successful merely because a background process was started.

## Charting interpretation

All unavailable pilot cells demonstrate missing-source discipline only. They
cannot establish charting speed, accuracy, or a universal retrieval bottleneck.
Available abstracts may support some limited facts; the current codebook's
accepted-document requirement is what prevents accepted cells before lineage.
Do not fabricate DOC identities to make source notes pass the accepted-row schema.
Schema compliance and quote entailment remain distinct checks.

## Source-based codebook re-pilot (preliminary notes)

Two full texts were inspected: WeedsGalore arXiv v1 and SemiWeedNet publisher HTML.
No accepted-document artifacts or final charting rows were constructed. Source
URLs and inspection scope are in verification.json. This is a qualitative coding
walkthrough, not independently double-coded extraction.

- WeedsGalore sections 3/4 distinguish multitemporal data diversity from the
  separate Maize2024 OOD experiment. Section 4.3 mixes field, year, growth stage
  and cover shift; code combined shift with its axes, not an isolated sensor or
  date effect. Section 4.2/Table 7 evaluate calibration, rather than merely
  displaying attention or uncertainty. Separate in-domain and OOD setting rows.
- SemiWeedNet Proposed Method and Data/Dataset uses an RGB subset of WeedMap
  with random 8:2 image splitting. Code RGB actual input separately from the
  original dataset's sensor inventory. Semi-supervised unlabelled training is not
  automatically target-domain adaptation; target_data_use requires an explicitly
  distinct evaluation target and supporting assignment evidence.
- S4 publisher indexed methods establish primary-study status, but direct fetch
  returned 429. Do not count this as a retained complete full-text snapshot.

Full-text walkthrough confirms the need for evaluation-setting rows and explicit
combined-shift notes. No protocol taxonomy change is needed yet; independent
coding and accepted source lineage remain prerequisites for formal charting.
