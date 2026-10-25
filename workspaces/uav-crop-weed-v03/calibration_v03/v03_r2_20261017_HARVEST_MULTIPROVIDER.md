# r2 verification harvest report — UAV-HARVEST-R2-20261017

Verification pass after the researcher-authorized 4-fix patch round
(`search_implementation=patched_post-L1L6+r2fixes`). The v0.3 baseline run
(`v03_20261017_*`) and the 2026-10-16 unpatched baseline remain untouched;
every r2 artifact carries the `v03_r2_` prefix.

## 1. Run identity

| Field | Value |
|---|---|
| Session | `UAV-HARVEST-R2-20261017` |
| Date | 2026-10-17 |
| search_implementation | `patched_post-L1L6+r2fixes` (uncommitted demo-local patch; canonical-repo stream parked) |
| S2 keyed | yes (presence only; the key is **rejected** by S2 — 403 — and the new auto-downgrade restores the leg unauthenticated) |
| Protocol fingerprint | `sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755` (unchanged; query identical to the v0.3 run — 27 terms, 3 clusters) |
| Patch applied this round | providers/pubmed.py `9f1440f3c81f6706` · providers/openalex.py `75ae6f04bd821179` · providers/semanticscholar.py `e11d6289bfa4c2aa` · providers/arxiv.py `011a508b1d54cea7` · enrichment.py `968930ba9826f3bd` (dedup.py untouched: `82c9ae71ceb065be`) |

## 2. Provider table (r2)

| Provider | Cap | Fetched | Status | Elapsed (s) | vs v0.3 run |
|---|---|---|---|---|---|
| openalex | **2000** | **1342** | SUCCESS — **exhausted below cap** (strict `title_and_abstract.search`; live universe 1344, 2-record meta drift noted) | 18.38 | 1000 (cap) → 1342 (uncapped) |
| crossref | 1000 | 1000 | SUCCESS (cap-bounded) | 2.65 | unchanged |
| arxiv | 200 | 39 | SUCCESS | 0.16 | unchanged count despite compaction (see §5 S5) |
| pubmed | 200 | 76 | SUCCESS | 1.60 | unchanged count (fix was ID-scoping, not search scope) |
| semanticscholar | 200 | **200** | SUCCESS via 403 auto-downgrade to unauthenticated tier | 3.29 | 0 (403, PARTIAL) → 200 |

## 3. Union / hydration / dedup (r2)

| Metric | Value |
|---|---|
| Union | **2657** (1342 + 200 + 1000 + 39 + 76) |
| DOI-bearing / DOI-less (union) | 2563 / 94 |
| Hydration attempted / hydrated / failed | **897 / 477 / 466** |
| Abstract coverage | 1754 → **2185** (net **+431**; OpenAlex-first carried it; S2 unauthenticated batches then mostly 429'd with backoff, by design) |
| Still no abstract (hydrated pool) | 472 |
| Dedup clusters / singletons / merged | **2356 / 2088 / 301** (rate 11.33%) |
| 2 reps sharing an identical DOI (not merged) | S6: `10.1186/s13007-023-01060-8` → SCI-000193 (openalex) + SCI-002331 (pubmed); root-caused: openalex provider stores `pubmed_id` as full URL vs pubmed bare PMID; `_has_identifier_conflict` annuls the DOI Tier-1 match. **Reported, not patched (outside the authorized packet).** |

## 4. Benchmark (deltas, numerically only)

| Metric | 2026-10-16 unpatched | v0.3 patched run | r2 verified run |
|---|---|---|---|
| Union | 2165 | 2115 | **2657** |
| Dedup unique | 2060 | 2060 | **2356** |
| Merged (rate) | 105 (4.8%) | 55 (2.6%) | **301 (11.3%)** |
| Abstract coverage | 1571 → 1654 (+83) | 1396 → 1741 (+345) | **1754 → 2185 (+431)** |
| Kit hydration | 89 | 360 | **477** |
| Abstract-less after (reps) | 511 | 364 | **432** (of a larger pool) |
| S2 leg | 10/500 | 0/200 (403) | **200/200 (downgraded tier)** |
| OpenAlex | 1000 (full-text `search`, noisy) | 1000 (full-text) | **1342 strict, exhaustive below cap** |
| Sentinel PID recall | 4/4 in-window (5-sentinel table) | 1/7 DOI-exact (+3 title) | **6/7 PID** |

## 5. Sentinel recall — Tier-1 PID (decision (b)2 applied)

| Seed | Tier-1 hit | SCI id(s) | Arrivals | Note |
|---|---|---|---|---|
| S1 WeedsGalore | ✅ DOI-exact | SCI-000128 | openalex + s2 | Recovered from title-only by the strict filter |
| S2 SemiWeedNet | ✅ DOI-exact | SCI-000224 | crossref + openalex + pubmed | Stable across runs |
| S3 Transformer | ✅ DOI-exact | SCI-000178 | openalex + s2 | **Recovered from MISS** (openalex dilution fix) |
| S4 BAWSeg | ✅ DOI-exact | SCI-000188 | openalex + s2 (+ arXiv twin 2603.01932) | Crosswalk OBSERVED, recorded |
| S5 AAMBERS (2609.05762) | ❌ MISS | — | none | **Record EXISTS — arXiv `id_list=2609.05762` resolves it — but the arXiv search leg does exact-token matching: `weedy` ≠ `weed`/`weeds` clauses (no stem expansion), so no provider return carries it** |
| S6 DeBlur (s13007) | ✅ DOI-exact ×2 | SCI-000193 + SCI-002331 | openalex + pubmed | PubMed now reports its TRUE DOI; duplicate-repair defect logged (§3) |
| S7 | ✅ DOI-exact | SCI-000186 | openalex | Recovered |

**Tier-1 PID recall: 6/7.** The single remaining miss is arXiv-side token
matching, verified above; proposal for a fix is listed under Decisions Requested.

## 6. Quality snapshot (2356 representations)

- With abstract: 1924 (**81.7%**) · title-only: 432 (**18.3%**)
- With DOI: 2294 (**97.4%**)
- In-window 2020–2026: 2356 (**100.0%**)

## 7. Reconcile

`_drivers/v03_r2_reconcile.py`, zero failures (label-alias normalized for
the `openalex-full`/`crossref-full`/`arxiv-full` template names):

**Reconciled: 2657 = 2657 = 2657 (union); 2356 = 2356 = 2356 (dedup, 301 merged).**

## 8. Scope statement

No screening performed; no eligibility decisions; **PROVISIONAL_NOT_FROZEN**;
v0.3-run artifacts, v0.2-era `calibration/`, and all parent workspaces
untouched; no commit/push performed.

## 5th finding (above the authorized packet — awaiting authorization)

OpenAlex provider stores `pubmed_id='https://pubmed.ncbi.nlm.nih.gov/37608384'`
while the PubMed provider stores `'37608384'`; `_has_identifier_conflict`
then treats the two representations of the SAME PMID as a conflict and blocks
DOI-tier merging (observed: S6 double-rep). One-line provider normalization
(strip `https://pubmed.ncbi.nlm.nih.gov/` prefix, keep the bare PMID) plus an
optional tolerant pubmed comparison would repair merges. NOT applied — outside
the authorized 4-fix packet.
