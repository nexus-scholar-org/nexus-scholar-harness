# v0.3 harvest report — UAV-HARVEST-V03-PATCHED-20261017

Multi-provider calibration harvest under v0.3 + patched kit code. Nothing
screened, nothing frozen. All artifacts under `calibration_v03/` (drivers in
`_drivers/`); v0.2-era calibration untouched.

## 1. Run identity

| Field | Value |
|---|---|
| Session | `UAV-HARVEST-V03-PATCHED-20261017` |
| Date | 2026-10-17 |
| search_implementation | `patched_post-L1L6` (5-file demo-local patch, uncommitted; canonical-repo stream parked) |
| S2 keyed | yes (env presence only; value never read — S2 still returned HTTP 403, see incidents) |
| Protocol fingerprint | `sha256:f81e6c58aefb3159cb679ca87c4a83382dca199e0b02bb12ac409c15f8a4f755` (matched exactly in preflight) |
| Parent v0.2 fingerprint | `sha256:a1fd8d2a82e0a5fca77deabbad360a1d8190d2d017d3ffa38342d8ac7ff73451` |
| Patched file short SHA256s | dedup.py `82c9ae71ceb065be` · enrichment.py `9d5f24d7f474b366` · providers/openalex.py `7a48439da48a60c5` · providers/semanticscholar.py `10f9378502a858f2` · screening.py `d1cbf32531aca143` |

Query: deterministic build from `protocol.json search_strategy.core_concepts`
— 27 quoted terms in 3 OR-clusters joined by AND (cluster 1 = concept label +
10 synonyms; cluster 2 = 8; cluster 3 = 8), uppercase operators, year filter
2020–2026, language en. Full query recorded verbatim in the manifest.

## 2. Provider table

| Provider | Cap | Fetched | Status | Elapsed (s) |
|---|---|---|---|---|
| openalex | 1000 | 1000 | SUCCESS | 12.17 |
| crossref | 1000 | 1000 | SUCCESS | 2.62 |
| arxiv | 200 | 39 | SUCCESS (provider exhausted below cap) | 4.35 |
| pubmed | 200 | 76 | SUCCESS (provider exhausted below cap) | 1.97 |
| semanticscholar | 200 | 0 | PARTIAL — HTTP 403 Forbidden despite keyed=yes | 0.37 |

Executed in plan order openalex → crossref → arxiv → pubmed → semanticscholar
(key last). Per-provider try/except isolation + watchdogs verified: a
provider failure stopped only that leg and kept its file (empty S2 file kept
with a PARTIAL manifest record).

## 3. Union / hydration / dedup counts

| Metric | Value |
|---|---|
| Per-provider docs | openalex 1000, semanticscholar 0, crossref 1000, arxiv 39, pubmed 76 |
| Union total | **2115** (== sum of per-provider counts == manifest counts == live records) |
| Records rebuilt | 2115 (0 skipped) |
| Hydration attempted / hydrated / failed | **718 / 360 / 373** (kit stats verbatim; DOI-bearing records only) |
| Abstract coverage | 1396 → **1741** (net **+345**; 360 map applications minus 15 already-abstracted DOI overlaps) |
| Still no abstract (post-hydration, hydrated pool) | 2115 − 1741 = **374** |
| DOI-less (union, corrected recount) | **72 of 2115** (2043 DOI-bearing) — driver's initial `doi-less=2115` was a has_doi() defect on string-typed external_ids and is superseded by this regex recount |
| DOI-less (deduped representatives) | 66 of 2060 |
| Dedup clusters / singletons / merged | **2060 / 2006 / 55** (rate 2.60%) |

Hydration mechanics: patched pipe-batch path (OpenAlex fallback batches of 50
DOIs; S2 batch first with `x-api-key` when keyed) — S2 leg 403'd on every
batch (consistent with the provider 403); OpenAlex fallback carried all 360
hydrations. No text invented.

## 4. Benchmark vs the unpatched 2026-10-16 definitive run

Deltas, numerically only (baseline → v0.3-patched):

| Metric | 2026-10-16 (unpatched) | v0.3 patched | Δ |
|---|---|---|---|
| Union | 2165 | 2115 | **−50** |
| Dedup unique | 2060 | 2060 | **0** |
| Merged duplicates | 105 (4.8%) | 55 (2.6%) | **−50** |
| Abstract coverage | 1571 → 1654 | 1396 → 1741 | net **+83 → +345** |
| Kit hydration poured | 593 attempted / 89 hydrated / 510 failed | 718 attempted / 360 hydrated / 373 failed | hydrated **+271** |
| Abstract-less after | 511 | 364 (deduped reps) | **−147** |
| S2 provider | 10/500 | 0/200 | **−10**, new 403 |
| arXiv | 153/200 | 39/200 | −114 |
| PubMed | 2/200 | 76/200 | +74 |
| OpenAlex / Crossref | 1000 / 1000 | 1000 / 1000 | 0 |

Interpretation is deferred to the human; headline drivers visible in the
numbers: (a) the query expanded from 10 to 27 terms, shifting every ranked
leg; (b) S2 contributed 0 records this run (403) vs 10 before; (c) the
OpenAlex boolean truncation patch is live (full boolean string executed,
1000/1000) so openalex-side coverage changed distribution; (d) dedup unique
stable at 2060 is coincidental — input and merge behavior both changed.

## 5. Sentinel recall (full table in `v03_20261017_sentinel_recall.md`)

| Seed | DOI | DOI-exact | Title-fallback | Arrivals | Note |
|---|---|---|---|---|---|
| S1 | 10.1109/wacv61041.2025.00467 | 0 | 1 | title-axis: arxiv | DOI-less arXiv twin (2502.13103); identical title |
| S2 | 10.3389/fpls.2022.927368 | 1 | n/a | crossref | DOI-exact via crossref (SCI-001516) — historically an expected miss; appears under patched code, verified, not assumed |
| S3 | 10.3390/rs15215165 | 0 | 0 | none | MISS — no raw record with DOI or exact title (relevance shift + cap truncation) |
| S4 | 10.3390/rs18060915 | 0 | 1 | title-axis: arxiv | DOI-less arXiv twin (2603.01932) |
| S5 | 10.48550/arxiv.2609.05762 | 0 | 0 | none | MISS — not in the 39-record arXiv return |
| S6 | 10.1186/s13007-023-01060-8 | 0 | 1 | title-axis: pubmed | Same title, recorded DOI 10.7717/peerj.453 ≠ seed — possible PubMed ArticleId mis-parse or true title collision; NOT a DOI hit |
| S7 | 10.1016/j.compag.2022.107388 | 0 | 0 | none | MISS |

Recall: **4/7 total** (1 DOI-exact + 3 title-fallback; 3 MISS). vs the
2026-10-16 baseline (4/4 in-window on its 5-seed table): S3 dropped from
DOI-exact 2 to MISS, S1/S4 resolve only via the title axis through DOI-less
arXiv twins, and S6's only same-title record carries a mismatched DOI.
Seed titles for the fallback axis were taken from verified baseline
artifacts, never invented.

## 6. Quality snapshot (2060 deduped representatives)

- With abstract: 1696 (**82.3%**) · title-only (no abstract): 364 (**17.7%**)
- With DOI: 1994 (**96.8%**) · DOI-less: 66
- In-window 2020–2026: 2060 (**100.0%**) — providers applied the year filter server-side

## 7. Reconcile

Verified programmatically (`_drivers/v03_reconcile.py`, zero failures):
per-provider manifest counts == raw-file count-fields == live docs (5/5);
union_count == sum(manifest) == live union docs (2115 = 2115 = 2115); dedup
cluster_count == representatives == unique_documents (2060 = 2060 = 2060,
55 merged recounted from cluster sizes).

**Reconciled: 2115 = 2115 = 2115 (union); 2060 = 2060 = 2060 (dedup).**

## 8. Scope statement

No screening performed; no eligibility decisions; **PROVISIONAL_NOT_FROZEN**;
nothing from the v0.2-era `calibration/` touched.

## Incidents (honest log)

1. Attempt-1 harvest driver carried a paren-join defect producing an
   unbalanced boolean string; OpenAlex answered HTTP 500. Driver script
   corrected in place (kit code untouched); defective attempt-1 manifest
   preserved as `_drivers/v03_run_manifest_ATTEMPT1_parenbug.json`;
   attempt-2 executed the full boolean query successfully (1000/1000). The
   OPENALEX CHECKPOINT was NOT triggered on attempt-2 — no keyword fallback
   ever occurred.
2. Semantic Scholar returned HTTP 403 Forbidden on both the provider leg and
   every hydration batch, despite `SCHOLAR_S2_KEY` present in the process
   environment (env var name verified: `SCHOLAR_S2_KEY` → `settings.s2_key`
   via `SCHOLAR_` prefix). Key value never read, printed, or persisted.
   S2 coverage is 0 this run; spec did not authorize touching kit code to
   diagnose further — flagged for the human (key validity/endpoint scope?).
3. Hybrid orientation of arXiv records: WACV/MDPI seed papers surface as
   DOI-less arXiv twins (S1, S4) — title axis only in this run's sentinel
   table; DOI crosswalk left to the human decision on whether to seed arXiv
   IDs as alternate identifiers.
4. PubMed record matching the s13007 seed carries DOI 10.7717/peerj.453
   (likely ArticleIdList mis-parse by the provider or true title collision).
   Flagged; treated as title-fallback only.
