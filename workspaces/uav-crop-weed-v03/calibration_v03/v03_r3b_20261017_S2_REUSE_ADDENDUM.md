# R3B addendum — S2-leg completion by cached reuse (UAV-HARVEST-R3B-20261017)

Supplements `v03_r3_20261017_HARVEST_MULTIPROVIDER.md`. Authorized as decision (i)
Option A (`EVT-20261017191328`); supersedes the "S2 top-up next window" scheduling.
All outputs `v03_r3b_*` (new files); no r3/r2/v0.2 artifact touched.

## 1. What was reused and why it is legitimate

| Item | Value |
|---|---|
| Source | `v03_r2_20261017_raw_semanticscholar.json` (cached, verified; 200 records) |
| Original retrieval | 2026-10-17 ~16:10, code state `patched_post-L1L6+r2fixes`, unauthenticated endpoint after keyed-403 downgrade |
| New API calls in r3b | **none** (per-IP unauth pool untouched; top-up driver parked for later windows) |
| Protocol fingerprint | `sha256:f81e6c58…f755` (unchanged; same 27-term boolean) |
| Kit state at r3b | 8 dirty files (models.py PMID normalization added, `0c1ca071855acbd0`), probes 8/8 PASS pre-run |

## 2. Overlap verification (measured, not assumed)

| Metric | Value |
|---|---|
| S2 records retrieved | 200 |
| Already represented in the r3 pool (PID via DOI/arxiv_id OR title+year signature) | **187** |
| Genuinely new at retrieval | **13** |
| Net new unique representatives after clustering | **10** (3 of the 13 merge intra-batch/base at title level) |

The researcher's indirect duplicate math (301−175=126 dups → ~74 unique) is
**empirically superseded**: the r2→r3 merge-delta over-estimated S2's discovery
value because the r3 pool's provider mix and compaction changes independently
altered merge counts. True S2 incremental value: **10 corpus records** — most of
S2's yield was already covered by OpenAlex/Crossref/PubMed/arXiv.

## 3. Pool and dedup (r3b, corrected pass)

| Metric | pass-1 (defective snapshot) | **r3b final** |
|---|---|---|
| Pool (union) | 2469 | **2469** (2456 + 13) |
| Pre-dedup abstract coverage | 2015 (artefact) | **2008** = 2000 + 8 (81.4%); +1 vs r3 live count = deterministic serialization round-trip of one abstract string, documented |
| Hydration | — | attempted **0** (verified correct: the 5 abstractless new S2 docs are DOI-less) |
| Dedup | 2291 / 178 | **2291 reps, 178 merged (7.21%), 2130 singletons, zero errors** |
| Sentinel Tier-1 PID | — | **7/7 unchanged** (expected memo: no change) |

Defect correction on the record (`EVT-20261017192044`): pass-1 wrote the pool
snapshot *after* dedup; `Deduplicator._merge_metadata` mutates representatives
in place during clustering (longer-abstract-wins, PID/source/OA merge — kit
design, dedup.py lines 244–283). 17 records carried representative-enriched
abstracts under a pre-dedup name. Drivers now snapshot before dedup; dedup
statistics were and remain computed from genuine clustering (identical to
pass-1 → deterministic). No r3 number is affected: the r3 main union wrote its
pool before dedup from the start.

## 4. PRISMA-ScR per-database identification lines (final)

| Database | Retrieved (2026-10-17) | Duplicates removed | Unique at identification | Note |
|---|---|---|---|---|
| OpenAlex (`title_and_abstract.search`) | 1343 | in dedup | in dedup | exhaustive below cap; universe 1344 probed (±1 meta drift) |
| Crossref | 1000 | in dedup | in dedup | cap-bounded |
| arXiv | 37 | in dedup | in dedup | real compaction + stem family |
| PubMed | 76 | in dedup | in dedup | — |
| Semantic Scholar | **200 (cached verified retrieval, reused per authorization)** | **187 (pre-dedup overlap test)** | **13** (10 net after clustering) | retrieval leg state `patched_post-L1L6+r2fixes`; labelled in `v03_r3b_20261017_s2_reuse.json` |

## 5. State

`PROVISIONAL_NOT_FROZEN` until formally frozen; no screening; no identity
minting yet. Freeze sequencing pending researcher confirmation of the
corrected Step 1 (canonical unpark before any `resolve_producer_commit()` pin).

Scope: writes confined to `calibration_v03/v03_r3b_*` + `_drivers` + journal.
Kit source remains demo-local (8 files; `BLOCKED_CANONICAL_REPO` for the PR
stream with the updated 8-file inclusion list).
