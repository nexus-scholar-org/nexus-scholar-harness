# Risk-of-Bias Assessment

**Corpus**: 94 studies (post-audit); **run**: 2026-09-05T20:02:26.935735+01:00
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
| L | 2 |
| ? | 77 |
| H | 15 |
| n/a | 0 |

Per-domain counts:

| Domain | L | ? | H | n/a |
|---|---|---|---|---|
| d1 | 71 | 20 | 3 | 0 |
| d2 | 10 | 72 | 12 | 0 |
| d3 | 37 | 56 | 1 | 0 |
| d4 | 18 | 32 | 0 | 44 |

## Studies rated high risk (overall)

SCI-000016, SCI-000040, SCI-000092, SCI-000149, SCI-000482, SCI-000570, SCI-000618, SCI-000890, SCI-000903, SCI-000980, SCI-001023, SCI-001029, SCI-001046, SCI-001085, SCI-001376

## Studies rated unclear (overall)

SCI-000001, SCI-000003, SCI-000005, SCI-000007, SCI-000010, SCI-000012, SCI-000013, SCI-000017, SCI-000067, SCI-000074, SCI-000075, SCI-000083, SCI-000084, SCI-000089, SCI-000091, SCI-000129, SCI-000136, SCI-000138, SCI-000145, SCI-000160, SCI-000180, SCI-000203, SCI-000225, SCI-000271, SCI-000286, SCI-000346, SCI-000371, SCI-000440, SCI-000483, SCI-000488, SCI-000489, SCI-000492, SCI-000501, SCI-000505, SCI-000514, SCI-000547, SCI-000548, SCI-000555, SCI-000565, SCI-000637, SCI-000650, SCI-000669, SCI-000683, SCI-000708, SCI-000754, SCI-000810, SCI-000816, SCI-000852, SCI-000878, SCI-000881, SCI-000898, SCI-000962, SCI-000968, SCI-000981, SCI-001005, SCI-001017, SCI-001053, SCI-001081, SCI-001084, SCI-001090, SCI-001096, SCI-001153, SCI-001173, SCI-001203, SCI-001210, SCI-001292, SCI-001305, SCI-001333, SCI-001334, SCI-001335, SCI-001368, SCI-001371, SCI-001379, SCI-001382, SCI-001406, SCI-001411, SCI-001413

## Studies with an edge/runtime component (D4 applicable): **50**

## Per-study ratings

| ID | Year | Overall | D1 | D2 | D3 | D4 | D4 detail (device/runtime/fps/latency) |
|---|---|---|---|---|---|---|---|
| SCI-000001 | 2025 | ? | L | ? | L | ? | device=n, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-000003 | 2025 | ? | L | ? | ? | n/a |  |
| SCI-000005 | 2026 | ? | ? | ? | L | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000007 | 2026 | ? | L | ? | L | n/a |  |
| SCI-000010 | 2019 | ? | ? | ? | L | n/a |  |
| SCI-000012 | 2022 | ? | ? | ? | ? | ? | device=y, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-000013 | 2026 | ? | L | ? | L | n/a |  |
| SCI-000016 | 2018 | H | ? | H | ? | n/a |  |
| SCI-000017 | 2025 | ? | L | ? | L | n/a |  |
| SCI-000040 | 2026 | H | H | ? | L | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000067 | 2024 | ? | L | ? | L | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000074 | 2026 | ? | L | ? | L | n/a |  |
| SCI-000075 | 2024 | ? | L | ? | L | n/a |  |
| SCI-000083 | 2026 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000084 | 2020 | ? | L | ? | L | ? | device=y, runtime=y, eff=n, fps=False, lat=True, pwr=False |
| SCI-000089 | 2022 | ? | L | ? | L | n/a |  |
| SCI-000091 | 2023 | ? | L | ? | ? | n/a |  |
| SCI-000092 | 2020 | H | H | ? | H | n/a |  |
| SCI-000129 | 2026 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000136 | 2020 | ? | L | ? | ? | n/a |  |
| SCI-000138 | 2024 | ? | ? | ? | ? | n/a |  |
| SCI-000145 | 2023 | ? | ? | ? | ? | ? | device=n, runtime=y, eff=y, fps=False, lat=True, pwr=False |
| SCI-000149 | 2024 | H | L | H | ? | ? | device=y, runtime=y, eff=n, fps=False, lat=True, pwr=False |
| SCI-000160 | 2026 | ? | L | ? | L | n/a |  |
| SCI-000180 | 2025 | ? | L | ? | ? | ? | device=n, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-000203 | 2023 | ? | L | ? | ? | n/a |  |
| SCI-000225 | 2025 | ? | L | ? | ? | n/a |  |
| SCI-000271 | 2024 | ? | L | ? | ? | n/a |  |
| SCI-000286 | 2024 | ? | ? | ? | ? | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=False |
| SCI-000346 | 2026 | ? | ? | ? | L | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000371 | 2024 | ? | L | ? | ? | ? | device=n, runtime=y, eff=y, fps=True, lat=False, pwr=False |
| SCI-000440 | 2024 | ? | L | ? | L | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=True |
| SCI-000482 | 2018 | H | ? | H | ? | n/a |  |
| SCI-000483 | 2021 | ? | L | ? | L | n/a |  |
| SCI-000488 | 2023 | ? | L | ? | L | n/a |  |
| SCI-000489 | 2023 | ? | ? | L | ? | ? | device=n, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-000492 | 2020 | ? | L | ? | ? | n/a |  |
| SCI-000501 | 2022 | ? | L | ? | ? | n/a |  |
| SCI-000505 | 2025 | ? | L | ? | L | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=False |
| SCI-000514 | 2018 | ? | L | L | ? | n/a |  |
| SCI-000547 | 2018 | ? | L | L | ? | n/a |  |
| SCI-000548 | 2021 | ? | L | ? | ? | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=False |
| SCI-000555 | 2020 | ? | L | ? | ? | n/a |  |
| SCI-000565 | 2020 | ? | L | ? | ? | ? | device=y, runtime=y, eff=n, fps=True, lat=False, pwr=False |
| SCI-000570 | 2022 | H | L | H | ? | n/a |  |
| SCI-000582 | 2018 | L | L | L | L | n/a |  |
| SCI-000618 | 2022 | H | L | H | ? | ? | device=y, runtime=y, eff=n, fps=False, lat=True, pwr=False |
| SCI-000624 | 2022 | L | L | L | L | n/a |  |
| SCI-000637 | 2025 | ? | L | ? | ? | ? | device=n, runtime=y, eff=n, fps=False, lat=True, pwr=False |
| SCI-000650 | 2024 | ? | L | ? | ? | ? | device=y, runtime=y, eff=n, fps=False, lat=True, pwr=False |
| SCI-000669 | 2025 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=False |
| SCI-000683 | 2025 | ? | L | ? | L | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000708 | 2022 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=False |
| SCI-000754 | 2025 | ? | L | ? | L | L | device=y, runtime=y, fps=False, lat=True |
| SCI-000810 | 2026 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000816 | 2026 | ? | L | ? | L | ? | device=y, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-000852 | 2025 | ? | L | ? | L | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000878 | 2026 | ? | L | ? | ? | ? | device=y, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-000881 | 2026 | ? | L | ? | ? | n/a |  |
| SCI-000890 | 2025 | H | L | H | L | n/a |  |
| SCI-000898 | 2025 | ? | L | ? | L | ? | device=n, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-000903 | 2024 | H | L | H | ? | ? | device=n, runtime=y, eff=y, fps=False, lat=True, pwr=False |
| SCI-000962 | 2023 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=False |
| SCI-000968 | 2021 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=True |
| SCI-000980 | 2024 | H | L | H | L | n/a |  |
| SCI-000981 | 2025 | ? | ? | ? | ? | L | device=y, runtime=y, fps=True, lat=True |
| SCI-001005 | 2023 | ? | ? | ? | L | ? | device=n, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-001017 | 2026 | ? | L | ? | ? | L | device=y, runtime=y, fps=True, lat=True |
| SCI-001023 | 2025 | H | H | L | L | n/a |  |
| SCI-001029 | 2024 | H | L | H | L | ? | device=n, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-001046 | 2024 | H | L | H | ? | n/a |  |
| SCI-001053 | 2024 | ? | L | ? | ? | n/a |  |
| SCI-001081 | 2022 | ? | ? | ? | ? | n/a |  |
| SCI-001084 | 2025 | ? | ? | ? | L | ? | device=y, runtime=n, eff=y, fps=False, lat=False, pwr=False |
| SCI-001085 | 2026 | H | ? | H | ? | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=False |
| SCI-001090 | 2026 | ? | ? | ? | L | n/a |  |
| SCI-001096 | 2026 | ? | L | ? | ? | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=False |
| SCI-001153 | 2021 | ? | L | ? | ? | n/a |  |
| SCI-001173 | 2020 | ? | ? | ? | ? | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=False |
| SCI-001203 | 2024 | ? | L | L | ? | n/a |  |
| SCI-001210 | 2021 | ? | L | ? | ? | n/a |  |
| SCI-001292 | 2026 | ? | L | ? | L | L | device=y, runtime=y, fps=True, lat=True |
| SCI-001305 | 2023 | ? | L | ? | L | n/a |  |
| SCI-001333 | 2021 | ? | L | L | ? | L | device=y, runtime=y, fps=True, lat=False |
| SCI-001334 | 2025 | ? | L | ? | L | ? | device=n, runtime=y, eff=y, fps=False, lat=True, pwr=False |
| SCI-001335 | 2025 | ? | ? | ? | ? | ? | device=n, runtime=y, eff=y, fps=False, lat=True, pwr=False |
| SCI-001368 | 2023 | ? | L | ? | ? | n/a |  |
| SCI-001371 | 2024 | ? | L | L | ? | ? | device=n, runtime=y, eff=y, fps=True, lat=False, pwr=False |
| SCI-001376 | 2025 | H | ? | H | ? | ? | device=n, runtime=y, eff=n, fps=False, lat=True, pwr=False |
| SCI-001379 | 2023 | ? | L | ? | L | ? | device=y, runtime=y, eff=n, fps=True, lat=True, pwr=False |
| SCI-001382 | 2025 | ? | L | ? | L | n/a |  |
| SCI-001406 | 2021 | ? | ? | ? | ? | n/a |  |
| SCI-001411 | 2026 | ? | L | ? | ? | n/a |  |
| SCI-001413 | 2025 | ? | L | L | ? | ? | device=n, runtime=y, eff=y, fps=True, lat=False, pwr=False |

## Methodological note

- A study is rated **H** on D2 when no primary accuracy metric is reported (extraction found none); it may still contribute RQ2-only data.
- D3 is conservative: self-collected datasets without annotation/benchmark documentation are automatically `?` — presence of a sentence is not proof of quality.
- D4 rates reporting completeness of runtime/efficiency numbers, which matters directly for the RQ2 (embedded edge inference) synthesis.
- Per-domain reasons and verbatim flags are stored in `risk_of_bias.json` for manual override of any rating.
- Regenerate with `uv run python phase4/risk_of_bias_check.py`.
