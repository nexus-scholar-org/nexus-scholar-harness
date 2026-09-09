# Risk-of-Bias Assessment

**Corpus**: 47 studies (post-audit); **run**: 2026-09-08T10:07:37.546494+01:00
**Method**: deterministic, metadata-driven adaptation of the QUADAS-2 / PROBAST risk-of-bias domains over the canonical extraction records (`records.json`). Ratings: **L** low, **?** unclear, **H** high, **n/a** not applicable.

## Domain definitions

| Domain | Adapted from | Signal |
|---|---|---|
| D1 Dataset selection & representativeness | QUADAS-2 patient selection | UAV-collected; named dataset; sample size; explicit train/test or cross-validation split |
| D2 Metric measurement & reporting integrity | QUADAS-2 index test / PROBAST outcome | Primary accuracy metric present; extraction confidence; independent-route agreement; ambiguity flagged |
| D3 Ground-truth labeling quality | QUADAS-2 reference standard | Documented labels; public benchmark / known dataset vs unverifiable self-collected |
| D4 Runtime/efficiency claim completeness | QUADAS-2 flow & timing | Device named; runtime + efficiency measured; fps/latency/power reported |

Scoping note: this captures **reporting and verifiability** risk of the numbers entering the synthesis (can the claim be checked from the record alone?). It does not substitute for a human full-text appraisal.

## Summary

| Overall risk | Count |
|---|---|
| L | 0 |
| ? | 0 |
| H | 47 |
| n/a | 0 |

Per-domain counts:

| Domain | L | ? | H | n/a |
|---|---|---|---|---|
| d1 | 0 | 0 | 47 | 0 |
| d2 | 0 | 0 | 47 | 0 |
| d3 | 0 | 0 | 47 | 0 |
| d4 | 0 | 0 | 0 | 47 |

## Studies rated high risk (overall)

SCI-000001, SCI-000002, SCI-000003, SCI-000156, SCI-000005, SCI-000154, SCI-000104, SCI-000105, SCI-000009, SCI-000120, SCI-000158, SCI-000108, SCI-000013, SCI-000014, SCI-000101, SCI-000184, SCI-000017, SCI-000161, SCI-000181, SCI-000020, SCI-000145, SCI-000106, SCI-000125, SCI-000099, SCI-000025, SCI-000027, SCI-000171, SCI-000140, SCI-000167, SCI-000083, SCI-000032, SCI-000033, SCI-000034, SCI-000172, SCI-000019, SCI-000138, SCI-000038, SCI-000134, SCI-000115, SCI-000041, SCI-000042, SCI-000043, SCI-000044, SCI-000045, SCI-000046, SCI-000136, SCI-000144

## Studies with an edge/runtime component (D4 applicable): **0**

## Per-study ratings

| ID | Year | Overall | D1 | D2 | D3 | D4 | D4 detail (device/runtime/fps/latency) |
|---|---|---|---|---|---|---|---|
| SCI-000001 | 2026 | H | H | H | H | n/a |  |
| SCI-000002 | 2026 | H | H | H | H | n/a |  |
| SCI-000003 | 2024 | H | H | H | H | n/a |  |
| SCI-000156 | 2024 | H | H | H | H | n/a |  |
| SCI-000005 | 2024 | H | H | H | H | n/a |  |
| SCI-000154 | 2026 | H | H | H | H | n/a |  |
| SCI-000104 | 2024 | H | H | H | H | n/a |  |
| SCI-000105 | 2024 | H | H | H | H | n/a |  |
| SCI-000009 | 2024 | H | H | H | H | n/a |  |
| SCI-000120 | 2024 | H | H | H | H | n/a |  |
| SCI-000158 | 2024 | H | H | H | H | n/a |  |
| SCI-000108 | 2024 | H | H | H | H | n/a |  |
| SCI-000013 | 2024 | H | H | H | H | n/a |  |
| SCI-000014 | 2024 | H | H | H | H | n/a |  |
| SCI-000101 | 2025 | H | H | H | H | n/a |  |
| SCI-000184 | 2025 | H | H | H | H | n/a |  |
| SCI-000017 | 2024 | H | H | H | H | n/a |  |
| SCI-000161 | 2025 | H | H | H | H | n/a |  |
| SCI-000181 | 2025 | H | H | H | H | n/a |  |
| SCI-000020 | 2024 | H | H | H | H | n/a |  |
| SCI-000145 | 2025 | H | H | H | H | n/a |  |
| SCI-000106 | 2025 | H | H | H | H | n/a |  |
| SCI-000125 | 2025 | H | H | H | H | n/a |  |
| SCI-000099 | 2025 | H | H | H | H | n/a |  |
| SCI-000025 | 2024 | H | H | H | H | n/a |  |
| SCI-000027 | 2024 | H | H | H | H | n/a |  |
| SCI-000171 | 2026 | H | H | H | H | n/a |  |
| SCI-000140 | 2026 | H | H | H | H | n/a |  |
| SCI-000167 | 2026 | H | H | H | H | n/a |  |
| SCI-000083 | 2026 | H | H | H | H | n/a |  |
| SCI-000032 | 2024 | H | H | H | H | n/a |  |
| SCI-000033 | 2024 | H | H | H | H | n/a |  |
| SCI-000034 | 2024 | H | H | H | H | n/a |  |
| SCI-000172 | 2026 | H | H | H | H | n/a |  |
| SCI-000019 | 2026 | H | H | H | H | n/a |  |
| SCI-000138 | 2026 | H | H | H | H | n/a |  |
| SCI-000038 | 2024 | H | H | H | H | n/a |  |
| SCI-000134 | 2026 | H | H | H | H | n/a |  |
| SCI-000115 | 2026 | H | H | H | H | n/a |  |
| SCI-000041 | 2024 | H | H | H | H | n/a |  |
| SCI-000042 | 2024 | H | H | H | H | n/a |  |
| SCI-000043 | 2026 | H | H | H | H | n/a |  |
| SCI-000044 | 2024 | H | H | H | H | n/a |  |
| SCI-000045 | 2026 | H | H | H | H | n/a |  |
| SCI-000046 | 2024 | H | H | H | H | n/a |  |
| SCI-000136 | 2026 | H | H | H | H | n/a |  |
| SCI-000144 | 2026 | H | H | H | H | n/a |  |

## Methodological note

- A study is rated **H** on D2 when no primary accuracy metric is reported (extraction found none); it may still contribute RQ2-only data.
- D3 is conservative: self-collected datasets without annotation/benchmark documentation are automatically `?` — presence of a sentence is not proof of quality.
- D4 rates reporting completeness of runtime/efficiency numbers, which matters directly for the RQ2 (embedded edge inference) synthesis.
- Per-domain reasons and verbatim flags are stored in the JSON output for manual override of any rating.
- Regenerate with `scholar-verify risk-of-bias --workspace <dir>`.
