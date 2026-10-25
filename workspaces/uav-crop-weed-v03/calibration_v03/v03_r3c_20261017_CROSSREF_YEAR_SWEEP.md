# R3C addendum — Crossref year-partitioned sweep (UAV-HARVEST-R3C-20261017)

Supplements `v03_r3_20261017_HARVEST_MULTIPROVIDER.md` and
`v03_r3b_20261017_S2_REUSE_ADDENDUM.md`. Researcher-authorized completion probe
of the Crossref leg. All outputs `v03_r3c_*` (new files); nothing overwritten.

## 1. The design that ran

| Item | Value |
|---|---|
| Query | same 27-term protocol boolean, fingerprint `f81e6c58…f755` (unchanged) |
| Partition | disjoint publication-year sub-queries 2020–2026 (7 legs) |
| Semantics | identical kit CrossrefProvider behavior as the full-range leg (relevance-ranked, OR-collapsed tokens, identical `from/until-pub-date` filters) |
| Caps | 1000 rows/partition |
| Search date | 2026-10-17 UTC |
| Auth | strictly keyless, no S2 API calls |

## 2. Findings — the partition probe revised what the full-range leg reported

| Year | Universe (`total-results`) | Fetched | Cap-bound |
|---|---|---|---|
| 2020 | 1,521 | 1,000 | YES |
| 2021 | 1,685 | 1,000 | YES |
| 2022 | 1,691 | 1,000 | YES |
| 2023 | 1,938 | 1,000 | YES |
| 2024 | 2,395 | 1,000 | YES |
| 2025 | 2,319 | 1,000 | YES |
| 2026 | 1,547 | 1,000 | YES |
| **Σ** | **≈12,096** | **7,000** | all years |

- The r3 leg's "1000 cap-bound" hid that the whole-range universe under this
  leg semantics is ~12k. The year sweep lifts Crossref coverage from ~8% to
  **~58%**, but the partition is **still partially complete** — quarterly
  (28 partitions, every quarter far below the per-call cap) remains feasible
  and would complete the leg.
- Sweep records: 7,000 fetched → 1,087 duplicates against the r3b pool →
  **5,913 genuinely new** at identification.

## 3. Pool / hydration / dedup (r3c, corrected pass discipline)

| Metric | Value |
|---|---|
| Pool (union) | **8,382** = r3b 2,469 + 5,913 new |
| Pre-dedup abstract coverage | **6,963 (83.0%)** — mutation-safe snapshot ordering (r3b lesson applied) |
| Hydration (new only) | attempted 3,428 → hydrated **2,471**, failed 958 (S2 429 tier still dry; OA-first carried all successes) |
| Dedup | **8,180 reps / 202 merged (2.41%) / zero errors** (vs r3b: 2,291 / 178) |
| Sentinel Tier-1 PID | **7/7 unchanged** (`v03_r3c_20261017_sentinel_memo.md`) |

## 4. The open researcher decision this creates

The definitive corpus artifact for identity minting (Step 3) must now be chosen:

- **Option r3b** — 2,291 reps: high-precision relevance-top crossref slice;
  OpenAlex primary exhaustive; crossref disclosed cap-bound (1000/~12,096).
  Smaller screening workload; prioritized recall on the strong engine only.
- **Option r3c (current standing)** — 8,180 reps: deep crossref year-sweep
  supplement; crossref coverage ~58%, disclosed per-year cap-bound; OpenAlex
  unchanged (still the exhaustive primary). ~3.6× screening workload; the
  sweep tail is lower-precision by rank and will be handled in screening.
- **Option r3d** — complete the crossref leg fully with quarterly partitions
  (~28 calls; adds the remaining ~2.5–4k tail records; crossref leg then
  honestly "complete"; pool grows to roughly 10–11k reps).

OpenAlex remains the exhaustive primary database under all three options —
that claim does not move. The choice is about the crossref supplement's depth
and the screening budget it implies.

## 5. State

`keyed=no` throughout; `PROVISIONAL_NOT_FROZEN`; no screening; no identity
minting. Scope: writes confined to `calibration_v03/v03_r3c_*`, `_drivers`,
journal. Kit source untouched this round (decontamination held: 7 dirty files,
all domain-token-free).
