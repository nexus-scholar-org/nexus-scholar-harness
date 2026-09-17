# Comprehensive Deep Dive Analysis: scholar-verify-kit

**Kit**: scholar-verify-kit v0.1.0
**Location**: `C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-verify-kit`
**Analysis Date**: 2026-09-14
**Total Source Lines**: ~1,631 (8 modules)
**Total Test Lines**: ~961 (6 test files)

---

## Executive Summary

The scholar-verify-kit is the post-screening trust verification engine of the Nexus Scholar Suite. It implements four deterministic verification streams (retraction status, open-science DAS/CAS, conflict-of-interest audit, risk-of-bias scoring) plus two aggregation commands (trust-context annotation, verbatim claim verification). The kit is well-structured as a collection of pure functions with CLI and library interfaces, outputs machine-readable JSON and human-readable Markdown, and integrates cleanly with the harness via `uv run scholar-verify`.

**Strengths**:
- Clean separation of concerns (8 focused modules, each self-contained)
- Deterministic by construction for 5 of 6 streams (only retraction touches live APIs)
- Thorough trust-level hierarchy (BLOCKED/UNVERIFIED/WEAK/ADEQUATE/STRONG) documented at the code level
- Good test coverage across all modules including CLI smoke tests
- Properly documented data contracts in SKILL.md

**Critical Issues Found**:
- **BUG (P0)**: `cli.py:verbatim_claims_cmd` uses `re.search()` at lines 247/251 but `import re` is missing from cli.py -- the `verbatim-claims` CLI command will crash with `NameError` at runtime
- **BUG (P1)**: `retraction.py:56` has `import time` inside a hot loop -- works but is an anti-pattern
- **Dead code**: All four `save_results()` functions (retraction.py:282, open_science.py:272, coi.py:300, risk_of_bias.py:262) are defined but never called
- **Domain coupling**: `risk_of_bias.py` hardcodes UAV agriculture benchmark names and metrics
- **Inconsistent error handling**: `coi.py:128,148` and `risk_of_bias.py:149` raise `SystemExit` instead of proper exceptions
- **`all` command omission**: `cli.py:all_cmd` does not run `trust-context` or `verbatim-claims`

---

## 1. Functionalities

### 1.1 CLI Commands

| Command | CLI Entry Point | Function | Module | Network |
|---|---|---|---|---|
| `retraction` | `cli.py:76` | `retraction_cmd()` | `retraction.py` | Yes (OpenAlex + Crossref) |
| `open-science` | `cli.py:100` | `open_science_cmd()` | `open_science.py` | No |
| `coi` | `cli.py:115` | `coi_cmd()` | `coi.py` | No |
| `risk-of-bias` | `cli.py:132` | `risk_of_bias_cmd()` | `risk_of_bias.py` | No |
| `trust-context` | `cli.py:147` | `trust_context_cmd()` | `trust_context.py` | No |
| `all` | `cli.py:196` | `all_cmd()` | Multiple | Optional |
| `verbatim-claims` | `cli.py:225` | `verbatim_claims_cmd()` | `verbatim.py` | No |

### 1.2 Stream Details

#### Stream 1: Retraction Check (`retraction.py`)
- **Class**: `RetractionChecker` (line 35)
- **Lookup chain**: DOI -> OpenAlex by DOI; if no DOI, arXiv ID -> OpenAlex by arXiv abs URL -> filter API -> title/year fuzzy match; fallback to OpenAlex ID
- **Crossref checks**: `update-to` events for retraction, expression-of-concern, correction, addendum
- **DataCite awareness**: Short-circuits `10.48550/` DOIs (arXiv DataCite-managed)
- **Output fields per study**: `workspace_id`, `title`, `year`, `provider`, `doi`, `arxiv_id`, `openalex{}`, `crossref{}`, `flagged`, `flag_reasons[]`
- **Summary**: `studies_checked`, `flagged_any`, `retracted_openalex`, `crossref_update_events`, `openalex_provenance_status`, `api_errors`, `unresolved_lookups[]`
- **CLI options**: `--workspace`, `--records`, `--included`, `--sleep` (rate limit), `--dry-run`, `--yes`

#### Stream 2: Open-Science DAS/CAS (`open_science.py`)
- **Pure regex baseline** scanning extracted fulltext markdown
- **Data patterns** (line 19): 12 patterns including `data_avail_kw`, `avail_on_request`, `repository_kw`, etc.
- **Code patterns** (line 44): 8 patterns including `code_avail_kw`, `github_kw`, `implementation_available`, etc.
- **Negation patterns**: `DATA_NEGATE` (line 33, 8 patterns), `CODE_NEGATE` (line 54, 4 patterns)
- **Classification hierarchy** (line 104): `public+link` > `request-only` > `statement-only` > `explicitly-unavailable` > `not-stated`
- **Repo host detection** (line 62): github.com, gitlab.com, zenodo, figshare, osf.io, kaggle.com, huggingface.co, paperswithcode.com
- **Context windows**: +/-140 chars around each match (line 74)

#### Stream 3: COI Audit (`coi.py`)
- **Input**: Per-chunk analyst COI classifications (`coi_chunk_*.json`)
- **Label taxonomy** (line 17): `no-statement`, `academic-or-public`, `industry-money`, `industry-affiliation-or-equipment`, `declared-no-conflict`
- **Entity kinds** (line 24): `funding`, `affiliation`, `donated-equipment`, `tooling`, `unspecified`
- **Deterministic relabel** (line 94-108): `no-statement` -> `declared-no-conflict` (if COI statement present), `academic-or-public` (if only funding), `industry-money` (if funding entity), `industry-affiliation-or-equipment` (if non-tooling entity)
- **Schema normalization**: Accepts both flat schema and v2 schema
- **Validation**: Rejects duplicates, missing, and extra IDs against manifest

#### Stream 4: Risk-of-Bias (`risk_of_bias.py`)
- **Framework**: QUADAS-2/PROBAST adaptation with 4 domains
- **D1** (Dataset Selection): UAV-collected check, named dataset, image count, train/test split
- **D2** (Metric Reporting): Primary metric presence, confidence, agreement, ambiguity
- **D3** (Ground Truth): Benchmark detection, annotation documentation, known datasets
- **D4** (Runtime/Efficiency): Device, runtime, efficiency, fps, latency, power
- **Ratings**: L (low), ? (unclear), H (high), n/a
- **Overall**: Worst applicable domain
- **Domain-specific benchmarks** (line 23): Hardcoded list of agriculture/weed detection benchmarks

#### Stream 5: Trust-Context (`trust_context.py`)
- **Pure join**: Merges Consensus Cartographer output with all four Phase-4 streams
- **Trust levels** (line 39): `BLOCKED` > `UNVERIFIED` > `WEAK` > `ADEQUATE` > `STRONG`
- **RQ-scoping**: Can filter by research question ID via `--rq-id`
- **Claims attribution**: Loads per-RQ claim pools (`claims_rq*.json`) and attributes clusters to RQs

#### Stream 6: Verbatim Claims (`verbatim.py`)
- **Algorithms**: Character-window coverage (window=8, step=4) + token n-gram coverage (n=6, step=3)
- **Text normalization**: NFKC, zero-width space removal, dash/quote unification, hyphenated linebreak joining
- **Output**: `VerbatimResult` dataclass per claim with `char_coverage`, `token_coverage`, `max_coverage`, `is_verified`, `failure_reason`
- **Threshold**: Default 0.90 (configurable via `--threshold`)

### 1.3 Data Models / Schemas

**Standard envelope**: All streams produce `{run_metadata, summary, results}`:
- `run_metadata`: `tool`, `run_date_utc`, `data_sources`/`scan`/`method`, `corpus_size`
- `summary`: Stream-specific aggregated counts
- `results`: Per-study row arrays

**Input schemas**:
- `records.json`: Canonical merged extraction records with `workspace_id`, `study{title,year,extracted_md}`, `segmentation{dataset,metrics}`, `edge{}`
- `included.json`: Screened documents with `workspace_id`, `external_ids{doi,arxiv_id,openalex_id}`
- `_manifest.json`: `[{workspace_id, title, year}]`
- `coi_chunk_*.json`: Analyst COI entries
- `consensus.json`: Consensus Cartographer output with `high_consensus`, `active_debates`, `unresolved`, `provisional`

### 1.4 Integration Points

| Integration | Target | Mechanism |
|---|---|---|
| `scholar-agent-kit` MCP server | `nexus_verify_claims` (server.py:656) | Imports `VerbatimClaimVerifier` directly |
| `scholar-agent-kit` MCP server | `nexus_verify_phase4` (server.py:740) | Calls `verify_cli._write()`, individual stream `.run()` functions |
| Harness console actions | `trust_context` action (actions.py:91) | `uv run scholar-verify trust-context --workspace {ws}` |
| Harness API | `/phase4` endpoint (workspace.py:198) | Reads `phase4/` directory files |
| Harness inception wizard | Protocol config (inception.py:592) | Sets `retraction_check_required`, `coi_and_funding_audit_required` |
| `plugins.json` | Kit registration (plugins.json:63) | Source of truth for kit version pin |

---

## 2. Improvements

### 2.1 Code Quality Issues

| Priority | File:Line | Issue | Recommendation |
|---|---|---|---|
| **P0** | `cli.py:247,251` | **BUG**: `re.search()` used but `import re` is missing from the module-level imports. The `verbatim-claims` CLI command will crash with `NameError: name 're' is not defined` at runtime. | Add `import re` to the top of `cli.py` |
| **P1** | `retraction.py:56` | `import time` is inside the hot loop `for rec in records:` -- import executed on every iteration | Move `import time` to module-level imports |
| **P2** | `retraction.py:56` | The `import time` inside the loop is also redundant -- `http_client.py:46` already handles sleep via `self.sleep_s * (attempt + 1)` in the HTTP client | Remove the loop-level sleep entirely or use the http_client's built-in rate limiting |
| **P2** | `coi.py:128,148` | `raise SystemExit(...)` for validation errors kills the process ungracefully | Use `typer.BadParameter` or a custom exception; `SystemExit` prevents programmatic API usage |
| **P2** | `risk_of_bias.py:149` | Same `SystemExit` issue for missing records | Same fix as above |
| **P3** | `retraction.py:282`, `open_science.py:272`, `coi.py:300`, `risk_of_bias.py:262` | `save_results()` functions defined in all four modules but never called anywhere -- dead code | Remove or consolidate into `cli._write()` (which already handles this) |

### 2.2 Missing Features / Capabilities

1. **No `--json` output flag**: Individual stream commands print summary to stdout but have no flag to output the full JSON result. Users must know to look at `phase4/*.json`. (The `verbatim-claims` command has `--output` but other streams do not.)

2. **No incremental/cached retraction checks**: Running `retraction` on a 200-paper corpus hits OpenAlex + Crossref for every study, even if a previous run already checked some. No caching of API responses.

3. **No `--workers` / parallel API calls**: Retraction checks are sequential with `time.sleep()` between each. For large corpora, this is slow (94 studies ~ 19s at 0.2s sleep).

4. **No streaming/progress indication**: Long-running commands (especially `retraction`) give no progress feedback during execution. No `rich.progress` bars despite `rich` being a dependency.

5. **No JSON schema validation**: Outputs are not validated against any declared schema. Adding pydantic models or JSON Schema files would enable downstream type checking.

6. **No `--format` option**: Commands always produce both JSON and Markdown. There is no way to produce only JSON (for automation) or only Markdown (for human review).

7. **COI chunk count is hardcoded**: `coi.load_chunks()` (line 122) defaults to `n_chunks=8` with no auto-detection of how many chunks exist. Adding more chunks requires passing `--chunks` and counting manually.

8. **No confidence intervals or effect sizes**: The risk-of-bias scorer produces categorical ratings (L/?/H) but no quantitative confidence or calibrated scores that would enable meta-analytic weighting.

### 2.3 API Design Improvements

1. **Inconsistent function signatures**:
   - `retraction.py`: Class-based (`RetractionChecker.check(records, included)`)
   - `open_science.py`, `risk_of_bias.py`: Module-level `run(records, manifest)`
   - `trust_context.py`: Both `annotate()` and `run()` (with different signatures)
   - `verbatim.py`: Class-based (`VerbatimClaimVerifier.verify_claims_ledger()`)
   
   Recommendation: Unify to either all class-based or all function-based.

2. **`_write()` is in `cli.py` but used by MCP server**: The MCP server (`server.py:769-817`) imports `verify_cli._write()` and `verify_cli._merged_records()` -- private helpers should be promoted to public API or moved to a shared module.

3. **Return type inconsistency**: Some streams return the full output dict from `run()` and separately return Markdown from `render_report()`. The CLI calls both; library users must remember to call both. Consider returning a named tuple or dataclass with both.

### 2.4 Error Handling Gaps

1. **`coi.load_chunks()` raises `SystemExit` on missing chunk** (line 128): This prevents the MCP server or any caller from handling the error gracefully.

2. **No timeout on retraction API calls in the loop**: While `VerifyHttpClient` has a `timeout` parameter, the `RetractionChecker._check_one()` method does not distinguish between "API returned 404" and "API timed out" in a way that would allow partial retry.

3. **`trust_context.py` silently skips missing phase4 files** (line 175-176): If a phase4 file does not exist, it is silently omitted from the trust index. This could produce misleading trust scores if a user forgot to run a stream.

4. **`open_science.py` file read errors**: `errors="replace"` (line 177) silently replaces encoding errors. No logging or reporting of which files had encoding issues.

### 2.5 Documentation Needs

1. **`docs/` directory is empty**: The kit has no developer documentation, architecture diagrams, or contribution guide.

2. **No CHANGELOG**: Version is locked at `0.1.0` with no history.

3. **Risk-of-bias domain mappings lack literature references**: The QUADAS-2/PROBAST adaptation in `risk_of_bias.py` has no inline citations to the original frameworks or justification for each threshold (e.g., why `images >= 20` is the cutoff for D1).

4. **Trust level thresholds undocumented in code**: The `trust_level()` function (trust_context.py:129) has 5 levels with specific threshold rules, but the reasoning behind the thresholds (why 50% coverage, why industry-money demotes to WEAK) is only in the SKILL.md, not in code docstrings.

---

## 3. Problems

### 3.1 Known Bugs

| Severity | Location | Description |
|---|---|---|
| **Critical** | `cli.py:247,251` | `NameError: name 're' is not defined` in `verbatim-claims` CLI. The `re` module is not imported but `re.search()` is used to map source files by `SCI-xxxx` IDs. Every invocation of `scholar-verify verbatim-claims` will crash. |
| **Medium** | `retraction.py:56` | `import time` inside the `for` loop body. Python caches module imports after the first, so this is functionally harmless but wasteful and confusing. |
| **Low** | `cli.py:240` | `verbatim_claims_cmd` raises `typer.BadParameter` for non-list JSON, but other JSON loading (`_load`) uses `typer.Exit`. Inconsistent error presentation. |

### 3.2 Edge Cases Not Handled

1. **Empty corpus**: `risk_of_bias.run()` with an empty records list will return a summary with empty counters. `trust_context.trust_level([], 0.0)` correctly returns `UNVERIFIED`, but `annotate()` with empty consensus buckets will produce a valid but empty report -- no explicit warning.

2. **Duplicate workspace_ids in records**: `retraction.py:52` builds `by_id` via dict comprehension, silently deduplicating. If two included records share a workspace_id, only the last one is used. No warning.

3. **Malformed Crossref responses**: `_crossref_by_doi()` (line 100) catches the DataCite short-circuit but does not handle Crossref rate limiting (429 status), which would hit the generic `raise_for_status()` and return `_error`.

4. **Unicode in titles**: `_norm_title()` (line 31) strips non-alphanumeric characters, which could cause false matches for titles differing only in diacritics.

5. **Very long fulltext files**: `open_science.py` reads entire markdown files into memory. For extracted PDFs with very long text, this could be memory-intensive.

6. **Claims with multiple study_ids**: `verbatim.py:120` uses `claim.get("study_id")` -- if a claim cites multiple studies, only the first study_id is used for source lookup.

7. **COI chunk files with different prefixes**: `coi.load_chunks()` (line 122) hardcodes prefix `coi_chunk_`. Custom chunk naming requires both `prefix` and `n_chunks` parameters.

### 3.3 Limitations

1. **Risk-of-bias is domain-coupled to UAV agriculture**: The `BENCH_RE` regex (line 23) hardcodes `weedsgalore|weedmap|phenobench|cofly|weeddb|agriculture-vision|cwfid|...`. The `PRIMARY_METRICS` (line 34) include `weed_F1`, `crop_F1`. The D1 rater checks `uav_collected`. This makes the scorer unusable for non-UAV/non-agriculture domains without modification.

2. **No longitudinal retraction monitoring**: Retraction checks are point-in-time. There is no mechanism to periodically re-check a corpus for new retractions.

3. **COI depends on LLM analyst chunks**: The `coi` stream aggregates pre-computed analyst classifications, not raw text. This means the COI audit quality depends entirely on the upstream LLM agent's accuracy.

4. **Open-science regex baseline has known precision limits**: The methodology note (line 263) explicitly states labels are "heuristic and intended for manual verification." False positives from patterns like `github_kw` matching non-code-related mentions are expected.

5. **Verbatim verification cannot detect paraphrasing**: The char-window and token n-gram algorithms only detect near-exact matches. Paraphrased or reworded claims will fail verification even if semantically correct.

### 3.4 Technical Debt

1. **4 dead `save_results()` functions** across retraction/open_science/coi/risk_of_bias modules (never called by CLI or MCP server).

2. **`_load()` and `_write()` are CLI-private but MCP-public**: Used by `server.py` via `verify_cli._write()`. These should be in a shared I/O module.

3. **`re` import missing from `cli.py`**: Should have been caught by tests, but `test_cli.py` tests `verbatim-claims` with `--output` flag which does not exercise the `re.search()` path that requires the `re` import.

4. **No type annotations on some return values**: `risk_of_bias.rate_d1/d2/d3/d4` return tuples but are typed as `-> Any` implicitly (no return annotation).

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

| Bottleneck | Location | Impact | Fix |
|---|---|---|---|
| Sequential API calls with `time.sleep()` | `retraction.py:54-58` | 94 studies = ~19s at 0.2s sleep; 500 studies = ~100s | Use `asyncio` + `aiohttp`, or `concurrent.futures.ThreadPoolExecutor` with rate limiting |
| `re` import in loop body | `retraction.py:56` | Negligible but wasteful | Move to module-level |
| Full file reads for DAS/CAS scan | `open_science.py:177` | Large extracted files loaded entirely into memory | Stream or chunk reads for very large files |
| Regex patterns recompiled | `open_science.py:19-61` | Pattern lists are module-level but `find_matches()` calls `re.finditer()` per pattern per record | Pre-compile patterns at module level (they already are for `URL_PATTERN` and `BENCH_RE`/`SPLIT_RE`/`ANNOT_RE` in risk_of_bias.py, but not for `DATA_PATTERNS`/`CODE_PATTERNS`) |

### 4.2 Caching Opportunities

1. **OpenAlex/Crossref response cache**: Studies with the same DOI will produce identical API responses. A simple JSON file cache keyed by DOI would eliminate redundant calls on re-runs. Location: `retraction.py:75-103`.

2. **Open-science file content cache**: If `open_science.run()` is called multiple times on the same workspace (e.g., during development), extracted file reads could be cached. Low priority since the operation is fast.

3. **Trust-context memoization**: `trust_context.build_trust_index()` (line 90) runs in O(N) and is called once per `annotate()`. No optimization needed unless called in a loop.

### 4.3 Parallelization Potential

1. **Retraction API calls**: The highest-impact optimization. OpenAlex and Crossref both support rate-limited parallel requests (OpenAlex: ~10 req/s with polite pool; Crossref: ~50 req/s with mailto). Could reduce 94-study check from ~19s to ~3-5s.

2. **COI chunk loading**: `coi.load_chunks()` reads 8 JSON files sequentially. Could use `concurrent.futures` for I/O parallelism. Low impact since files are small.

3. **Verbatim claim verification**: Claims are independent and could be verified in parallel. High impact for large claim sets.

### 4.4 Memory Usage

- **Low concern**: The kit operates on structured JSON, not large binary files. Even a 500-study corpus would have `records.json` at ~500KB and extracted markdown files at ~5-10MB total.
- **One optimization**: `open_science.py` loads all extracted text for a study into a single string. For very large extractions, this is fine since regex matching requires the full text.

---

## 5. Scientific Correction

### 5.1 Verification Accuracy

**Retraction Detection**:
- **OpenAlex `is_retracted`**: Reliable but metadata-snapshot dependent. OpenAlex updates within days of publisher action but may lag for smaller publishers. The kit correctly notes this limitation (line 275).
- **Crossref `update-to`**: Comprehensive for DOIs but does not cover all retraction channels (e.g., PubPeer annotations, Retraction Watch database). The kit only checks Crossref, not Retraction Watch.
- **Accuracy estimate**: ~95-98% for DOIs (OpenAlex + Crossref combined), ~80-85% for non-DOI records (arXiv fallback with title matching). The title-fuzzy-match path (`_openalex_by_arxiv` line 89-97) is the weakest link -- exact title normalization may fail for non-English titles or titles with special characters.

**Recommendation**: Add Retraction Watch database as an optional third source for higher recall.

### 5.2 Retraction Detection Reliability

- **Strength**: Dual-source verification (OpenAlex + Crossref) provides redundancy
- **Weakness**: Neither source covers predatory journal retractions that occur outside formal Crossref/OpenAlex channels
- **Weakness**: Preprint retractions (e.g., withdrawn from arXiv) may not propagate to OpenAlex immediately
- **Mitigation**: The `unresolved_lookups` summary field correctly surfaces studies that could not be checked

### 5.3 Open Science Compliance

- **Precision concern**: The regex pattern `github_kw` (line 50) matches any occurrence of "github" in text, including mentions like "inspired by GitHub Copilot" or "available on GitHub Enterprise" (private). These would be classified as `public+link` if a github URL is nearby.
- **Recall concern**: The patterns do not cover institutional repositories, domain-specific data portals (e.g., Dryad, Dataverse, Zenodo via non-standard URLs), or DOIs that resolve to data.
- **Classification edge case**: A study that says "Data is available from the corresponding author upon request" + has a GitHub link for code would classify DAS as `request-only` (the `avail_from_author` signal takes precedence over the link). This is technically correct but the link might be for data too.

### 5.4 COI Detection Correctness

- **Reliability depends on upstream analyst**: The COI module is an aggregator, not a detector. Its accuracy ceiling is bounded by the LLM analyst's classification accuracy.
- **Deterministic relabel logic** (coi.py:94-108): Well-documented and logically sound. The relabel chain correctly handles the common analyst error of using `no-statement` when a COI statement exists.
- **Entity classification**: The `company` -> `kind` mapping (line 63-70) uses `affiliation_role` heuristics. Edge case: a company that provides both funding AND equipment would be classified as whichever role appears first. The severity-ordered label (`industry-money` > `industry-affiliation-or-equipment`) handles this correctly at the label level, but entity-level ambiguity persists.

### 5.5 Risk-of-Bias Scoring Accuracy

- **D1 domain coupling**: The `uav_collected` check (line 62) means any non-UAV study is automatically rated H (high risk). This is by design (the RQ scope is UAV-based), but limits the scorer's applicability.
- **D2 metric detection**: The `PRIMARY_METRICS` list (line 34) is finite. Studies reporting IoU, Recall, Precision, or custom metrics will be rated H even if the metrics are well-reported. Consider expanding the list or using a fuzzy match.
- **D3 benchmark detection**: The `BENCH_RE` regex (line 23) is a hardcoded list of known benchmarks. New benchmarks would be missed, defaulting to "?" (unclear).
- **D4 completeness check**: Correctly identifies studies that claim edge deployment but do not report device, fps, or latency. The threshold logic (line 127) requiring device + runtime + efficiency + (fps or latency) for "L" is appropriately strict.

---

## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent/Skill Be Created?

**Verdict: The existing `scholar-verify-kit` SKILL.md is sufficient. No new agent is needed.**

**Rationale**:
- The kit's tasks are well-defined deterministic operations, not exploratory or creative tasks that benefit from LLM reasoning
- The verification streams are orchestrated by CLI commands, not agent-in-the-loop workflows
- The only agent-facing integration is `nexus_verify_claims` and `nexus_verify_phase4` in the MCP server, which are already implemented
- The COI stream requires an LLM analyst, but that analyst is part of the broader `scholar-agent-kit`, not a new agent

### 6.2 Evaluation Metrics That Could Be Defined

If a verification quality gate were added to the pipeline, these metrics would be useful:

| Metric | Definition | Source | Threshold |
|---|---|---|---|
| `retraction_coverage` | % of studies successfully looked up (not unresolved) | `retraction.py` summary | >= 0.95 |
| `retraction_flag_rate` | % of studies flagged for retraction/correction | `retraction.py` summary | Report only (no threshold) |
| `open_science_public_rate` | % of studies with DAS=`public+link` | `open_science.py` summary | Context-dependent |
| `coi_industry_rate` | % of studies with any industry tie | `coi.py` summary | Report only |
| `coi_no_statement_rate` | % of studies with no COI statement | `coi.py` summary | <= 0.10 |
| `rob_high_risk_rate` | % of studies with overall_risk=H | `risk_of_bias.py` summary | <= 0.30 |
| `rob_d4_applicable_rate` | % of studies with D4 (edge) applicable | `risk_of_bias.py` summary | Context-dependent |
| `trust_strong_rate` | % of clusters rated STRONG | `trust_context.py` output | >= 0.50 |
| `trust_blocked_rate` | % of clusters rated BLOCKED | `trust_context.py` output | == 0.00 |
| `verbatim_verification_rate` | % of claims verified at threshold | `verbatim.py` metrics | >= 0.85 |
| `verbatim_missing_quote_rate` | % of claims missing evidence_quote | `verbatim.py` failure_reasons | <= 0.05 |

### 6.3 Critic Capabilities Needed

If an agent-in-the-loop verification critic were to be created:

1. **Retraction re-review agent**: When a study is flagged by retraction check, an agent should re-read the extraction and determine if the study's contribution to the synthesis is still valid. This requires understanding the study's claims and their dependency on the retracted/corrected content.

2. **COI interpretation agent**: The deterministic relabel handles common analyst errors, but a critic agent could review `declared-no-conflict` studies with non-tooling entities (flagged in `coi.py:271-285`) and determine if the conflict is material to the synthesis.

3. **Trust-level override agent**: The trust-context module assigns worst-case levels. A critic agent could review `WEAK` or `ADEQUATE` clusters and determine if the trust level should be upgraded based on qualitative evidence (e.g., a study rated H on D2 still contributes valid D4 edge data).

### 6.4 Automation Potential

| Automation | Current State | Recommendation |
|---|---|---|
| **Full Phase-4 run** | `all` command runs 4 streams sequentially | Already automated; add `trust-context` to `all` |
| **Incremental retraction re-check** | Not available | Add `--since YYYY-MM-DD` flag to re-check only studies added since last run |
| **COI chunk generation** | Manual (agent writes chunks) | Could be automated by having the agent kit generate chunks as part of extraction |
| **Trust-quality gate** | Manual review of trust_consensus.json | Add `--fail-if-blocked` flag to `trust-context` for CI/CD integration |
| **Verbatim re-verification** | One-shot | Add `--watch` mode to re-verify claims when extracted files change |
| **Schema validation** | None | Add `validate` command that checks all phase4 outputs against JSON schemas |

---

## 7. Priority-Ranked Improvement Suggestions

### Priority 0 (Critical -- Fix Immediately)

| # | Fix | Files | Effort |
|---|---|---|---|
| 1 | Add `import re` to `cli.py` to fix `verbatim-claims` crash | `cli.py:13-18` | 1 line |
| 2 | Move `import time` out of the for-loop in `retraction.py` | `retraction.py:56` | 1 line |

### Priority 1 (High -- Fix Soon)

| # | Fix | Files | Effort |
|---|---|---|---|
| 3 | Replace `SystemExit` with proper exceptions in `coi.py` and `risk_of_bias.py` | `coi.py:128,148`, `risk_of_bias.py:149` | Small |
| 4 | Remove or deprecate dead `save_results()` functions | 4 files | Small |
| 5 | Add `--output` flag to all stream CLI commands (not just `verbatim-claims`) | `cli.py` | Medium |
| 6 | Add `trust-context` to the `all` command | `cli.py:196-222` | Small |

### Priority 2 (Medium -- Plan for Next Sprint)

| # | Fix | Files | Effort |
|---|---|---|---|
| 7 | Add retraction response caching (JSON file keyed by DOI) | `retraction.py`, `http_client.py` | Medium |
| 8 | Add `rich.progress` bars for long-running operations | `retraction.py`, `cli.py` | Medium |
| 9 | Make `risk_of_bias.py` configurable (externalize benchmark list, metrics, UAV check) | `risk_of_bias.py` | Medium-Large |
| 10 | Promote `cli._write()` / `_merged_records()` / `_manifest()` to public API | `cli.py` | Small |
| 11 | Add JSON Schema files for all outputs | New `schemas/` directory | Medium |
| 12 | Auto-detect COI chunk count instead of hardcoding `n_chunks=8` | `coi.py:122` | Small |

### Priority 3 (Low -- Backlog)

| # | Fix | Files | Effort |
|---|---|---|---|
| 13 | Add async HTTP client for parallel retraction checks | `http_client.py`, `retraction.py` | Large |
| 14 | Add Retraction Watch as optional third source | `retraction.py` | Large |
| 15 | Expand `PRIMARY_METRICS` and `BENCH_RE` for broader domain support | `risk_of_bias.py` | Medium |
| 16 | Add pre-compiled regex for `DATA_PATTERNS`/`CODE_PATTERNS` | `open_science.py` | Small |
| 17 | Write developer documentation in `docs/` | `docs/` | Medium |
| 18 | Add confidence intervals to risk-of-bias ratings | `risk_of_bias.py` | Large |
| 19 | Add `--fail-if` flags for CI/CD integration | `cli.py` | Medium |
| 20 | Unify API style (class vs. function) across all streams | All modules | Large |

---

## Appendix A: File Inventory

| File | Lines | Role |
|---|---|---|
| `src/scholar_verify/__init__.py` | 5 | Package init, version |
| `src/scholar_verify/cli.py` | 272 | Typer CLI, workspace I/O |
| `src/scholar_verify/http_client.py` | 47 | HTTP fetch with retry/backoff |
| `src/scholar_verify/retraction.py` | 287 | OpenAlex + Crossref retraction check |
| `src/scholar_verify/open_science.py` | 276 | DAS/CAS regex baseline |
| `src/scholar_verify/coi.py` | 304 | COI audit aggregator |
| `src/scholar_verify/risk_of_bias.py` | 266 | QUADAS-2/PROBAST scoring |
| `src/scholar_verify/trust_context.py` | 380 | Trust-weighted consensus annotation |
| `src/scholar_verify/verbatim.py` | 179 | Verbatim claim verification |
| `tests/test_cli.py` | 149 | CLI smoke tests |
| `tests/test_retraction.py` | 132 | Retraction checker tests |
| `tests/test_open_science.py` | 102 | Open-science scanner tests |
| `tests/test_coi.py` | 134 | COI aggregator tests |
| `tests/test_risk_of_bias.py` | 110 | Risk-of-bias scorer tests |
| `tests/test_trust_context.py` | 332 | Trust context tests (largest test file) |
| `pyproject.toml` | 43 | Build config, dependencies |
| `README.md` | 51 | Usage documentation |

## Appendix B: Dependency Graph

```
cli.py
  -> retraction.py -> http_client.py (requests)
  -> open_science.py (re, json)
  -> coi.py (json)
  -> risk_of_bias.py (re, json)
  -> trust_context.py (json)
  -> verbatim.py (re, unicodedata, dataclasses)

MCP Server (scholar-agent-kit/server.py)
  -> imports: retraction, open_science, coi, risk_of_bias, trust_context, verbatim
  -> imports: cli._write, cli._merged_records, cli._manifest, cli._load, cli._slug
```

---

*Analysis generated 2026-09-14 by deep-dive code review of scholar-verify-kit v0.1.0.*
