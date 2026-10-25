# Calibration query log - UAV crop/weed reliability pilot

> Historical calibration record. [Senior review](SENIOR_REVIEW.md) corrects sentinel/report-type and recall interpretations; [delegated decisions](RESEARCHER_DECISIONS.md) supersede the open choice list. No formal screening or independent human labels are claimed.

> Historical calibration record. [Senior review](SENIOR_REVIEW.md) corrects sentinel/report-type and recall interpretations; [delegated decisions](RESEARCHER_DECISIONS.md) supersede the open choice list. No formal screening or independent human labels are claimed.

Date: 2026-10-12/13 (UTC). All commands run from repo root
`C:\Users\mouadh\Documents\nexus-scholar-harness` via `uv run scholar-search`.
No formal screening, no corpus creation, no `literature/` writes.
Raw calibration outputs kept as `calibration/_tmp_*.json` (scratch, not a corpus).

## 1. Scope/window/language confirmation (Item 1)

Sources read: `PROTOCOL.md` (v0.2, provisional, UNFROZEN), `intent.json`,
`protocol.json` (fingerprint `sha256:a1fd8d2a82e0a5fca77deabbad360a1d8190d2d017d3ffa38342d8ac7ff73451`).

- **Scope (confirmed):** broad descriptive mapping - primary empirical crop/weed
  mapping studies AND dataset/benchmark reports; learning and non-learning
  methods (method family is a charting variable, not eligibility); detection,
  segmentation, spatial weed mapping eligible; orchards included; multispectral
  input charted, not mandatory (RGB comparisons allowed).
- **Window (confirmed):** 2020 through the actual final search date in 2026
  (`intent.json`: `start_year: 2020`, `end_year: 2026`). No search date claimed yet.
- **Language (UNCONFIRMED assumption):** English full text is the *initial
  operational* assumption (`intent.json`: `languages: ["en"]`); PROTOCOL.md
  explicitly requires researcher confirmation before freeze.
- **Ambiguities flagged for researcher (NOT resolved):** (a) English-only scope
  and its bias impact; (b) IEEE Xplore / Scopus / Web of Science access
  unconfirmed; (c) final search cutoff date unclaimed; (d) `golden_seeds` empty
  in `protocol.json` - compiler exposes no seed passthrough, so no seed
  enforcement exists (protocol.json NOT hand-edited).

## 2. Executed queries

### Q0 - seed location (WeedMap)

Exact command:

```text
uv run scholar-search search "WeedMap UAV weed mapping dataset" --provider openalex --limit 10
```

- Provider: openalex. Filters: none. Cap: 10, one page.
- Returned: 10 records (table pasted in session; top hit WeedMap 2018,
  DOI 10.3390/rs10091423, 304 citations at display time).
- Wall time: not timed (location probe, not a calibration measurement).
- Errors: none.

### Q1 - base calibration query (OpenAlex translation of the three-cluster strategy)

SEARCH_STRATEGY.md's boolean (`UAV-cluster AND weed-cluster AND task-cluster`)
is NOT submitted literally: `scholar-search search` takes a keyword
`query_text` passed to the provider's relevance-ranked search endpoint (no
provider-side boolean AND is observable from the CLI). Translation used -
keywords covering all three clusters, smallest provider surface first:

Exact command:

```text
uv run scholar-search search "UAV weed mapping detection segmentation" --provider openalex --limit 25 --output "workspaces/uav-crop-weed-reliability/calibration/_tmp_calib_openalex.json"
```

- Provider: openalex. Filters: none (no year filter - deliberate, to observe
  out-of-window behaviour). Cap: 25, one page (full recall set NOT paginated).
- Returned: **25 records** (`COUNT: 25` from executed Python read of the output
  JSON). Years spanned 2013-“2026 (unfiltered, as expected).
- Pagination behaviour: exactly `limit` records returned; no pagination tokens
  surfaced by the CLI; stopping here per small-calibration constraint.
- Timed rerun (identical query, `--output .../_tmp_calib_timed.json`):
  **3.95 s** (`Measure-Command` TotalSeconds = 3.9474605). Reran output
  re-checked: RETURNED COUNT 25.
- Errors: none on OpenAlex.

### Q2 - one documented variant (year filter 2020-“2026)

Exact command:

```text
uv run scholar-search search "UAV weed mapping detection segmentation" --provider openalex --limit 25 --year-min 2020 --year-max 2026 --output "workspaces/uav-crop-weed-reliability/calibration/_tmp_calib_yearfilt.json"
```

- Returned: **25 records**, all dated 2020-“2026. Wall time: **3.41 s**
  (TotalSeconds = 3.4101391).
- No other rewriting attempted (per one-variant limit).

### Q3 - `validate-query` CLI attempt

Exact command:

```text
uv run scholar-search validate-query "UAV weed mapping detection segmentation" --seed 10.1109/wacv61041.2025.00467 --seed 10.3390/rs10091423 --seed 10.3389/fpls.2022.927368 --seed 10.3390/rs15215165 --seed 10.1016/j.atech.2025.101656
```

- Attempt 1 (foreground, default 120 s timeout): **TIMED OUT before completion.**
  Partial stderr captured an upstream error:
  `ERROR:scholar_search.engine:Error querying semanticscholar: [semanticscholar] Rate limit exceeded on academic API (HTTP 429)`.
  `validate-query` fans out to all providers (including SemanticScholar), so one
  provider's 429 + full-provider latency exceeded the timeout. No recall verdict
  was produced by the tool.
- Attempt 2 (background, no timeout, `--output .../_tmp_validate_query.json`,
  4 in-window seeds only): status PENDING at time of writing - see note at end
  of this file.
- Because the tool produced no verdict, recall below is measured **manually and
  deterministically**: exact lower-cased DOI match of the 5 verified sentinels
  against the executed Q1/Q2 output JSON files (script output pasted in session).

## 3. Recall tables (manual DOI match - see SENTINELS.md for sentinel verification)

Sentinels: S1 WeedsGalore (2025, in-window), S2 WeedMap (2018, OUT-of-window),
S3 SemiWeedNet (2022), S4 Transformer-in-UAV-mapping (2023),
S5 Precision-weed-detection review (2025/2026, see year discrepancy note).

| Sentinel | Q1 base page (25, unfiltered) | Q2 year-filtered page (25, 2020-“2026) |
|---|---|---|
| S1 10.1109/wacv61041.2025.00467 | MISS | HIT |
| S2 10.3390/rs10091423 (2018) | MISS | MISS (expected - excluded by year-min 2020) |
| S3 10.3389/fpls.2022.927368 | HIT | HIT |
| S4 10.3390/rs15215165 | HIT | HIT |
| S5 10.1016/j.atech.2025.101656 | HIT | HIT |
| **Recall on page** | **3/5** | **4/5 (4/4 of in-window sentinels)** |

Hypotheses (no further rewriting per constraint):

- S1 miss in Q1: relevance ranking without year filter buries the 2025 IEEE
  record below older highly-cited records; adding the window filter (Q2)
  recovers it. Implication: unfiltered keyword ranking is NOT a recall-safe
  retrieval mode for this review - year-bounded (and eventually paginated)
  retrieval is required.
- S2 miss in Q1: same ranking effect (2018 record did not rank in top 25 for
  Q1's keyword mix, though Q0's title-weighted query found it at rank 1).
  S2 miss in Q2 is by design (out-of-window). S2 remains a background-only
  foundation, never an in-window recall requirement - researcher to confirm.
- Page-level recall â‰  search recall: both Q1/Q2 stopped at 25 of an unknown
  total; full recall requires complete paginated retrieval, which was
  explicitly out of scope for this pilot.

## 4. Provider/error log

- openalex: OK on all runs (Q0, Q1 Ã—2, Q2). No key required. 3-“4 s per
  25-record page.
- crossref: OK (verify backend; 1/1 then 3/4 then 4/4 verifications confirmed).
- semanticscholar: **HTTP 429 rate limit** observed during `validate-query`
  fan-out (exact message above). No key configured. Continue-with-what-works
  applied: OpenAlex + Crossref paths unaffected.
- arxiv: not exercised in this pilot (draft provider list only).
- IEEE/Scopus/WoS: access unconfirmed - no attempt made; recorded as open
  researcher decision (see REVIEW_DESIGN.md).

## 5. Background `validate-query` retry - outcome

Attempt 2 was still running at log finalisation (no output file produced yet).
The manual recall tables above stand as the calibration verdict; the tool retry
is non-blocking. If the retry later completes, append its verdict here with the
exact pasted output - do not replace the manual tables.
