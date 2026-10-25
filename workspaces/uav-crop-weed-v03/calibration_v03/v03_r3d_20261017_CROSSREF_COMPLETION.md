# R3D addendum — Crossref quarterly completion sweep (UAV-HARVEST-R3D-20261017)

Completes the Crossref leg begun in `v03_r3_20261017_HARVEST_MULTIPROVIDER.md`
and deepened by `v03_r3c_20261017_CROSSREF_YEAR_SWEEP.md`. All outputs
`v03_r3d_*` (new files); nothing overwritten.

## 1. Design

| Item | Value |
|---|---|
| Query | same 27-term boolean, fingerprint `f81e6c58…f755` (unchanged since r0) |
| Partition | 28 disjoint cells = 7 years (2020–2026) × Q1–Q4 |
| Semantics | same kit `CrossrefProvider` translated query + kit `_normalize_document`; the quarter filter is built EXPLICITLY at the driver (harness composition — the kit's `search()` only supports year granularity and would silently re-fetch whole years). No kit changes. |
| Caps | 1000 rows/cell |
| Auth | strictly keyless; zero S2 API calls |
| Search date | 2026-10-17 UTC |

## 2. Result — Crossref leg COMPLETE

| Verdict | Evidence |
|---|---|
| **28/28 cells SUCCESS** | zero failed calls |
| **Zero cap-bound** | quarter universes 104–843, all far below the 1000-row cap |
| **fetched 13,096 = universe 13,096** | 100% of the leg's universe retrieved |
| **Partition-internal consistency** | per-year quarter sums reconcile EXACTLY with the r3c full-year totals (1521 / 1685 / 1691 / 1938 / 2395 / 2319 / 1547) |

Coverage chain for the Crossref leg under its fixed semantics:
full-range top-1000 (r3) → year sweep 7,000/13,096 = **53.5%** (r3c; arithmetic
correction of the earlier "58%" misc-add, journaled at EVT-…214341) →
**100.0%** (r3d).

## 3. Pool, hydration, dedup

| Metric | Value |
|---|---|
| Sweep yield | 13,096 fetched → 7,065 pool duplicates → **6,031 genuinely new** |
| Pool (union) | **14,413** = r3c 8,382 + 6,031 |
| Pre-dedup abstract coverage | **11,748 (81.5%)** — mutation-safe snapshot ordering held |
| Hydration (new only) | attempted 3,319 → hydrated **2,077**, failed 1,243 (S2 tier still 429-dry; OA-first carried all successes) |
| Dedup | **14,150 reps / 263 merged (1.82%) / 13,906 singletons / zero errors** |
| Sentinel Tier-1 PID | **7/7 unchanged** (`v03_r3d_20261017_sentinel_memo.md`) |

## 4. Search-closure state (per-database, stratified)

| Database | Identified | Status |
|---|---|---|
| OpenAlex (strict boolean) | 1,343 | **exhaustive** (universe 1,344; below cap) — PRIMARY, unchanged |
| Crossref (translated-leg) | 13,096-fetched universe | **COMPLETE** after r3+ r3c + r3d |
| arXiv | 37 | real compaction + research-config stem family |
| PubMed | 76 | exhaustive for its leg |
| Semantic Scholar | 200 (cached verified reuse) | unauth tier = quota debt, disclosed |
| **Union → dedup** | **14,150 reps** | r3d = definitive candidate corpus |

## 5. State and next gates

`keyed=no` throughout; `PROVISIONAL_NOT_FROZEN`; no screening; no identity
minting. Scope: writes confined to `calibration_v03/v03_r3d_*`, `_drivers`,
journal. Kit untouched (7 dirty files, domain-token-free, decontamination held).

Researcher gates remaining before screening:
1. **Confirm the r3d corpus (14,150 reps) as the definitive search corpus**
   entering Step 3 — this decision point is now *this addendum's* primary ask.
2. Canonical unpark (fork PR → `plugins.json` full-SHA bump → vendored resync)
   — still `BLOCKED_CANONICAL_REPO` until "unpark".
3. Step 2 amendment into `RESEARCHER_DECISIONS.md` (roles, 2026-10-17 UTC
   cutoff, codebook freeze).
4. Step 3 identity mint on the confirmed corpus → `COR-*`/`STU-*`.

Journal chain r3d: `DISCOVERY_SEARCH` EVT-20261017214341-ab19bc,
`ABSTRACT_HYDRATION` …214455-aee9e3, `DEDUP_RUN` …214502-545ad3,
`CALIBRATION_SENTINELS_VERIFIED` …214509-9a776d, `WORKSPACE_STATS`
…214521-b5494d.
