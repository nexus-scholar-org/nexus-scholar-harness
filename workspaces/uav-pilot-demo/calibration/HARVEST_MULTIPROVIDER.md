# Definitive multi-provider harvest — UAV crop/weed reliability pilot (demo workspace)

Date (UTC): 2026-10-16. Workspace: `workspaces/uav-pilot-demo`.
Frozen inputs: `calibration/QUERIES.md` (query §Q1/Q2), `calibration/SENTINELS.md`
(5 verified sentinels), `RESEARCHER_DECISIONS.md`, `protocol.json` rev 0.2
(`sha256:a1fd8d2a82e0a5fca77deabbad360a1d8190d2d017d3ffa38342d8ac7ff73451`,
PROVISIONAL_NOT_FROZEN), `intent.json`. This run OVERWRITES the stale 200-cap
calibration harvest of 2026-10-16 12:57 UTC (journal EVTs 20261016125714…
20261016130626), the interim 1355-record repair pass (OpenAlex 200/1000 on
401), and the 2155-record OpenAlex-repaired pass (S2S 0/500 on 429); those counts
are superseded and must not be cited.
No screening, no freeze, no protocol amendment performed.

## Executed query (verbatim)

```text
UAV weed mapping detection segmentation
```

Years 2020–2026, `dedup: false` at retrieval. This is the QUERIES.md Q1/Q2
keyword translation of the SEARCH_STRATEGY.md three-cluster boolean; the
boolean text was NOT submitted literally (provider endpoints are
relevance-ranked keyword search, no provider-side boolean AND is observable
from the kit surface).

## Per-provider results (strictly sequential, one provider at a time)

Order executed: OpenAlex → SemanticScholar → Crossref → arXiv → PubMed.
Each provider ran isolated in try/except + watchdog timeout; a provider
failure is recorded in that provider's file and the run continued.

| # | Provider | Cap (`max_results`) | Retrieved (`count`) | Wall (s) | `error_note` |
| --- | ---------- | -------------------- | -------------------- | ---------- | -------------- | 
| 1 | openalex | 1000 | 1000 | 16.72 | null (clean, cap met; keyed cursor paging with `SCHOLAR_OPENALEX_KEY`) |
| 2 | semanticscholar | 500 | 10 | 0.83 | null (clean; keyed `SCHOLAR_S2_KEY` session; provider returned fewer than cap — recorded honestly, not padded; supersedes prior 0/500 on HTTP 429) |
| 3 | crossref | 1000 | 1000 | 3.30 | null (clean, cap met) |
| 4 | arxiv | 200 | 153 | 0.36 | null (clean; provider returned fewer than cap — recorded honestly, not padded) |
| 5 | pubmed | 200 | 2 | 0.92 | null (clean; provider returned fewer than cap — recorded honestly, not padded) |

Key handling: the OpenAlex key was read from the `SCHOLAR_OPENALEX_KEY`
environment variable only and the SemanticScholar key from `SCHOLAR_S2_KEY`
only; no key value was printed or written to any file
(env-name references only). The definitive OpenAlex pass ran in a session where
its variable was SET (kit `settings.openalex_key` non-empty), hence clean
1000/1000 cursor paging. An earlier interim OpenAlex pass in a key-less session honestly
recorded 200/1000 on HTTP 401 and is superseded. The SemanticScholar pass ran
keyed (`settings.s2_key` non-empty), hence clean 10/500 without HTTP 429; the
prior 0/500 on HTTP 429 is superseded.

Raw files (each carries exactly the 10 keys `executed_query, provider,
year_min, year_max, max_results, dedup, wall_seconds, count, error_note,
documents` with `count == len(documents)`):
`calibration/raw_openalex.json`, `calibration/raw_semanticscholar.json`,
`calibration/raw_crossref.json`, `calibration/raw_arxiv.json`,
`calibration/raw_pubmed.json`.

## Union

`calibration/raw_union.json` = concatenation of the 5 per-provider document
lists. Union invariant verified by executable re-read:

- Per-provider counts: 1000 + 10 + 1000 + 153 + 2 = **2165**; union documents: **2165**. Sum equals union count.

## Hydration (kit AbstractHydrator ONLY)

`calibration/raw_union_hydrated.json` via `scholar_search.enrichment.AbstractHydrator`
(SemanticScholar batch → OpenAlex fallback), applied to rebuilt `Document`
objects; no text invented. Records without a DOI stay abstract-less by
construction (hydrator only attempts DOI-bearing records).

- Abstract coverage before: 1571 with / 594 without (of 2165).
- Kit hydrator stats dict (verbatim): `{'attempted': 593, 'hydrated': 89, 'failed': 510}`
  (S2 batch leg repeatedly hit HTTP 429; OpenAlex fallback recovered a subset).
- Abstract coverage after (file recount): 1654 with / **511 without** — net gain **+83**.
  The 6-record difference between kit-reported `hydrated: 89` and net `+83`
  is per-DOI map application: 6 records already carrying an abstract share a
  DOI with a hydrated record (code path `enrichment.py`: map applied to every
  document whose DOI is in the hydrated map). No abstract text was invented;
  hydrated abstracts trace to the S2/OpenAlex source for that DOI (spot-check:
  3 hydrated abstracts are genuine source texts, e.g. DOIs 10.1016/j.compag.2020.105446,
  10.1016/j.compag.2021.106067, 10.1016/j.robot.2021.103861).
- Abstract-less after: **511** records (148 records in the union carry no DOI
  at all and were never hydration candidates; the remainder are DOI-bearing
  records whose source returned no abstract, mostly under the S2 429 window).

## Dedup (kit Deduplicator ONLY)

`calibration/deduped.json` via `scholar_search.dedup.Deduplicator` (PID tier →
exact-normalized-title → fuzzy ≥ 0.97 + year/author guards). Nothing deleted:
representatives plus full member clusters are retained.

- Input 2165 → **2060 unique** representatives, **105** duplicates merged
  (duplicate rate 0.0485 ≈ 4.8%), 2060 clusters of which 1964 singletons.
  Canonical `SCI-%06d` workspace ids assigned by the kit (dedup-run-local,
  not stable cross-run study identities).

## Sentinel recall (exact lower-cased DOI match; title probe kept separate)

Recall base: `raw_union_hydrated.json` (2165 records). DOI match is exact
equality on the normalized DOI; title match is NOT identity and semantic
similarity is NOT entailment.

| Sentinel | DOI | Title (short) | DOI-exact | Title-probe | Verdict |
|----------|-----|---------------|-----------|-------------|---------|
| S1 | 10.1109/wacv61041.2025.00467 | WeedsGalore (2025, in-window) | 2 (openalex + crossref copies) | 3 | HIT |
| S2 | 10.3390/rs10091423 | WeedMap (2018, OUT-of-window) | 0 | 45 (title mentions only, not the paper) | MISS — expected, excluded by year-min 2020; background-only |
| S3 | 10.3389/fpls.2022.927368 | SemiWeedNet (2022) | 2 | 2 | HIT |
| S4 | 10.3390/rs15215165 | Transformer in UAV weed mapping (2023) | 2 | 2 | HIT |
| S5 | 10.1016/j.atech.2025.101656 | Precision weed detection review (2025 per OpenAlex display / 2026 per Crossref — provider year discrepancy noted) | 1 | 1 | HIT |

In-window sentinel recall: **4/4** (S1, S3, S4, S5). S2 is out-of-window by
design and never counts toward in-window recall.

## Completeness statement

Retrieval used relevance-ranked keyword search endpoints with per-provider
caps, two providers returning fewer than cap (SemanticScholar 10/500 and
arXiv 153/200 and PubMed 2/200 as honest provider returns);
**relevance-ranked retrieval supports no PRISMA completeness claim** — this harvest is a bounded calibration-style retrieval
probe, not an exhaustive systematic search, and must not be cited as a
complete corpus.

## Limitations / residual risks

- SemanticScholar keyed but returned 10/500 (honest provider return under keyed quota); coverage leans on OpenAlex/Crossref/arXiv/PubMed.
- arXiv (153) and PubMed (2) returned fewer than cap; honest provider behaviour.
- Crossref returned 2 records dated 2027 despite year-max 2026 (e-pub-ahead-of-print provider semantics); retain in harvest, disposition at screening per EXC-04/date.
- S5 year differs by provider (2025 vs 2026); eligibility turns on the future
  recorded final search date per RESEARCHER_DECISIONS.md.
- `deduped.json` representatives carry dedup-run-local `SCI-` ids only.
