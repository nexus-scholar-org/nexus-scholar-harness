# R3E addendum — bounded rehydration retry (UAV-HARVEST-R3E-REHYD-20261017)

Single retry pass over every DOI-bearing abstractless record in the r3d pool,
per researcher authorization ("one last time"). All outputs `v03_r3e_*` (new
files); no new search calls; strictly keyless; kit untouched.

## 1. Retry result

| Metric | Value |
|---|---|
| Candidates (DOI-bearing abstractless) | **2,659** (+ 6 title-only with no DOI — no hydration channel, untouched) |
| Attempted | 2,659 |
| **Hydrated** | **64** (OA/open channels on previously-missed records) |
| Failed | 2,595 — **S2 unauth per-IP tier still 429 on every batch** (window did not reset since r2/r3 consumption) |
| Wall | 229 s |

## 2. Effect on the corpus

| Metric | r3d | **r3e** |
|---|---|---|
| Pool | 14,413 | 14,413 |
| Pre-dedup abstract coverage | 11,748 (81.5%) | **11,811 (81.9%)** |
| Dedup reps | 14,150 | **14,150 — unchanged** (abstract merge does not alter PID/title clustering; +63 not +64 because one hydrated doc sits in a non-representative dup slot) |
| Sentinels Tier-1 PID | 7/7 | **7/7 unchanged** |

**The representative set is identical between r3d and r3e**; r3e differs only
in coverage (+63 abstracts).

## 3. Debt status: CLOSED for this session

Hydration for the remaining 2,595 DOI-bearing title-only records is
**exhausted under the keyless constraint on 2026-10-17** — the S2 fallback
tier 429'd on every attempt and the other open channels had nothing left.
They enter screening under the Decision#4 `abstract==null` guardrail (never
auto-excluded by rule; title-matched ones routed for human/fulltext
verification). The only honest top-up paths — a fresh S2 unauth quota window
or keyed S2 by researcher decision — remain parked and disclosed.

## 4. State

Final search date unchanged: **2026-10-17 UTC**. `PROVISIONAL_NOT_FROZEN`;
no screening; no identity minting.

Researcher gates remaining:
1. Confirm the definitive corpus for Step 3 identity mint — r3d vs r3e is a
   coverage-only choice (identical 14,150 reps); recommend simply carrying
   **r3e_deduped** as the canonical artifact since it supersedes r3d.
2. Canonical unpark (fork PR → `plugins.json` full-SHA bump → vendored resync)
   — still `BLOCKED_CANONICAL_REPO` until "unpark".
3. Step 2 amendment into `RESEARCHER_DECISIONS.md`.
4. Step 3 identity mint → `COR-*`/`STU-*`.

Journal chain r3e: `ABSTRACT_HYDRATION` EVT-20261017215844-9c8758,
`DEDUP_RUN` …215852-6cbb14, `CALIBRATION_SENTINELS_VERIFIED` …215858-148c6a,
`WORKSPACE_STATS` …215908-45baa7.
