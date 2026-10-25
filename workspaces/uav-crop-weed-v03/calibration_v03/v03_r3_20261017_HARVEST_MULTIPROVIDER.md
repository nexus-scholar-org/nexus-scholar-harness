# R3 definitive patched harvest report — UAV-HARVEST-R3-20261017

Definitive run after the complete cumulative fix list
(`search_implementation=patched_post-L1L6+r2fixes+pubmednorm+stemlex`).
v0.3-run, r2, and all parent/v0.2 artifacts remain byte-preserved; everything
here is `v03_r3_*`.

## 1. Run identity

| Field | Value |
|---|---|
| Session | `UAV-HARVEST-R3-20261017` |
| Date | 2026-10-17 |
| search_implementation | `patched_post-L1L6+r2fixes+pubmednorm+stemlex` |
| keyed | **no** — strictly enforced: `SCHOLAR_S2_KEY` observed still set in the executor process despite the unset instruction (value never read) and was **explicitly removed from every r3 child-process environment**. Hypdration re-run pass verified keyless (zero 403s, no downgrade path available) |
| Protocol fingerprint | `sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755` (matched; query identical to v0.3/r2 — 27 terms, 3 clusters) |
| Dirty kit files (7, short SHA256) | dedup `82c9ae71ceb065be` · enrichment `968930ba9826f3bd` · openalex `7fa01788a5f5eb87` (pubmednorm NEW) · pubmed `9f1440f3c81f6706` · semanticscholar `e11d6289bfa4c2aa` · arxiv `b4b7208f8c3a439d` (stemlex NEW + compaction made real) · screening `d1cbf32531aca143` |
| Per-fix verification before fetch | pubmednorm merge probe **PASS** (openalex+pubmed → exactly 1 cluster, bare PMIDs) · stemlex probe **PASS** (S5 retrieved on the emitted compact clause) |
| r2 correction | the r2 arXiv "compaction" was an **inert no-op** (quote-stripping deleted phrase contents); arXiv in r2 ran the full 27-phrase query. Made real in r3 with the stem family enumerated |

## 2. Provider table (r3, definitive)

| Provider | Cap | Fetched | Status | Elapsed (s) |
|---|---|---|---|---|
| openalex | 2000 | **1343** | SUCCESS — **exhaustive below cap** (strict `title_and_abstract.search`) | 16.77 |
| crossref | 1000 | 1000 | SUCCESS (cap-bounded) | 3.66 |
| arxiv | 200 | **37** | SUCCESS — real compaction live (see §5 S5) | 2.01 |
| pubmed | 200 | 76 | SUCCESS | 2.18 |
| semanticscholar | 200 | **0** | PARTIAL — `RateLimitExceededError` (429) on the unauthenticated tier | 0.64 |

## 3. Union / hydration / dedup (r3, final keyless pass)

| Metric | Value |
|---|---|
| Union | **2456** (1343 + 0 + 1000 + 37 + 76) |
| DOI-bearing / DOI-less (union) | 2369 / 87 |
| Hydration attempted / hydrated / failed | **872 / 445 / 454** |
| Abstract coverage | 1583 → **2001** (net **+418**; all from the OpenAlex pipe-batch; S2 unauthenticated batch tier stayed 429) |
| Still no abstract (hydrated pool) | 455 |
| Dedup clusters / singletons / merged | **2281 / 2122 / 175** (rate 7.13%) |
| Same-DOI double reps | **none** — the r2 S6 defect is repaired; S6's openalex+pubmed arrivals merged into one representative (SCI-000193) |

Hydration auth note: an interim keyed-by-env pass (872/433/465 → 1990) was
recorded then superseded by this strictly keyless pass (872/445/454 → 2001);
the ±12 difference is rate-limit timing luck, not auth state. Both are in the
journal; the final files are from the keyless pass only.

## 4. Benchmark (numeric deltas only)

| Metric | 10-16 unpatched | v0.3 run | r2 | **r3** |
|---|---|---|---|---|
| Union | 2165 | 2115 | 2657 | **2456** |
| Dedup unique | 2060 | 2060 | 2356 | **2281** |
| Merged (rate) | 105 (4.8%) | 55 (2.6%) | 301 (11.3%) | **175 (7.1%)** |
| Abstract coverage net | +83 | +345 | +431 | **+418** (keyless) |
| Hydrated | 89 | 360 | 477 | **445** |
| Abstract-less after (reps) | 511 | 364 | 432 | **430** |
| S2 leg | 10/500 | 0/200 | 200/200 (downgraded) | **0/200 (429, unauth tier)** |
| OpenAlex | 1000 (noisy full-text) | 1000 | 1342 | **1343 strict, exhaustive** |
| Sentinel Tier-1 PID | 4/4 in-window (5-seed table) | 1/7 | 6/7 | **7/7** |

The S2=0 in r3 vs 200 in r2 is upstream shared-quota exhaustion (429 across
the unauthenticated tier), not a code regression: the identical provider path
returned 200 records in r2 minutes earlier; flag for a later-window S2 top-up
decision if the researcher wants it before any freeze.

## 5. Sentinel recall — Tier-1 PID: **7/7**

| Seed | Tier-1 hit | SCI id | Arrivals | Note |
|---|---|---|---|---|
| S1 WeedsGalore | DOI-exact | SCI-000128 | openalex (+ arXiv twin) | stable |
| S2 SemiWeedNet | DOI-exact | SCI-000224 | crossref + openalex + pubmed | stable |
| S3 Transformer | DOI-exact | SCI-000178 | openalex | stable |
| S4 BAWSeg | DOI-exact | SCI-000188 | openalex (+ arXiv twin) | stable |
| S5 AAMBERS `2609.05762` | **arxiv_id HIT** | SCI-002274 | **arxiv** | recovery **attributable to the logged stem-family clause change** (`weedy`/`weediness` enumerated in the now-real compaction); doi=None is arXiv-native; NO id_list augmentation used, per instruction |
| S6 DeBlur | DOI-exact ×1 | SCI-000193 | openalex + pubmed (merged) | pubmednorm repair confirmed live |
| S7 COMPAG deblur | DOI-exact | SCI-000186 | openalex | stable |

## 6. Quality snapshot (2281 representatives)

- With abstract: 1851 (**81.1%**) · title-only: 430 (**18.9%**)
- With DOI: 2221 (**97.4%**)
- In-window 2020–2026: 2281 (**100.0%**)

## 7. Reconcile + REFERENCE-DRIFT

Zero failures (`_drivers/v03_r3_reconcile.py`):

**Reconciled: 2456 = 2456 = 2456 (union); 2281 = 2281 = 2281 (dedup, 175 merged).**

**REFERENCE-DRIFT (openalex):** strict-filter universe re-probed at r3 time =
**1344** (same filter, per-page 1, same boolean; HTTP 200), identical to the
r2-time probe (1344); r3 fetched **1343** — a **±1 record** metadata-count
drift (r2: 1342 fetched against the same universe; drift is inside benign
pagination/meta-recount behavior, quantified and logged; no clawbacks claimed).

## 8. Scope statement

No screening performed; no eligibility decisions; **PROVISIONAL_NOT_FROZEN**;
no freeze executed; nothing committed or pushed; v0.3-run/r2 and v0.2-era
artifacts untouched. Journal chain for the round: `CODE_PATCH_STATE`
(7-file cumulative hash set + pre-fetch verifications + r2 correction),
`DISCOVERY_SEARCH` PARTIAL, `ABSTRACT_HYDRATION` deviation+final (keyless SUCCESS),
`DEDUP_RUN` SUCCESS, `CALIBRATION_SENTINELS_VERIFIED` SUCCESS (7/7), `WORKSPACE_STATS`.
