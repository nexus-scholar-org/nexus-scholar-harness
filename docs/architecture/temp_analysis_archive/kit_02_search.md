# Scholar Search Kit -- Deep Dive Analysis
## Kit 02: tools/scholar-search-kit

**Date**: 2026-09-14
**Analyst**: Automated deep-dive (full source, tests, docs reviewed)
**Version**: 0.1.0 (hatchling wheel, pyproject.toml line 6)
**Files reviewed**: 22 source files, 11 test files, 13 doc files, 1 skill file

---

# Executive Summary

The scholar-search-kit is a mature, well-structured async Python toolkit for federated scholarly literature search, deduplication, verification, and export. It covers 6 live academic APIs (OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed, bioRxiv), 2 offline providers (InMemory, LocalFile), and provides both a CLI (scholar-search) and a programmatic Python API. The codebase is approximately 3,400 lines of production code across 22 files, with 11 test files and 19 test classes/functions.

**Strengths**: Clean separation of concerns, well-defined data models, non-destructive metadata fusion during dedup, robust HTTP resilience layer, LLM-powered screening capability, PRISMA 2020 compliance, and comprehensive documentation with 19 lesson files.

**Key Gaps**: No get_references for arXiv/bioRxiv providers; domain-specific screening heuristic (hardcoded UAV/spectral imaging); QueryParser unused as standalone; Exporter.csv silently drops fields; LLMBatchScreener not wired into CLI.

**Overall Quality**: B+ (good architecture, some gaps in integration, minor dead code, needs broader testing).

---

# 1. Functionalities

## 1.1 Complete Capability Map

| Capability | Source File | CLI Command | API Entry Point |
|:---|:---|:---|:---|
| Federated multi-provider search | engine.py:43-73 | scholar-search search | SearchEngine.search_all() |
| Single-provider search | providers/*.py | --provider <name> | Provider.search(query) |
| Protocol-driven search | protocol_adapter.py:10-90 | --protocol protocol.json | compile_protocol_search() |
| Forward snowballing | engine.py:75-88 | scholar-search snowball -d forward | SearchEngine.snowball_forward() |
| Backward snowballing | engine.py:90-105 | scholar-search snowball -d backward | SearchEngine.snowball_backward() |
| Multi-hop BFS chaining | snowball.py:105-242 | scholar-search chain | CitationChainer.chain() |
| Document verification | verifier.py:59-146 | scholar-search verify | DocumentVerifier.verify_document() |
| Metadata hydration | verifier.py:148-205 | --enrich flag | DocumentVerifier.hydrate_metadata() |
| Batch verify+hydrate | verifier.py:207-239 | scholar-search import --verify --enrich | DocumentVerifier.process_batch() |
| Deterministic dedup | dedup.py:28-104 | scholar-search dedup | Deduplicator.deduplicate() |
| Metadata merging | dedup.py:159-223 | (automatic) | Deduplicator._merge_metadata() |
| Heuristic screening | screening.py:208-340 | scholar-search screen | evaluate_heuristic_screening() |
| LLM batch screening | screening.py:487-614 | (programmatic only) | LLMBatchScreener.screen() |
| PRISMA flow report | screening.py:31-73 | (auto-generated) | PrismaFlowReport.to_markdown() |
| Multi-rater reconciliation | screening.py:672-744 | (programmatic only) | reconcile_multi_screener_decisions() |
| Fleiss kappa | screening.py:617-669 | (programmatic only) | calculate_fleiss_kappa() |
| JSON export | export.py:14-23 | --format json | Exporter.json() |
| JSONL export | export.py:25-32 | --format jsonl | Exporter.jsonl() |
| CSV export | export.py:34-76 | --format csv | Exporter.csv() |
| RIS import | importers.py:11-81 | (auto-detected) | RISImporter.parse() |
| JSON import | importers.py:84-146 | (auto-detected) | JSONImporter.parse() |
| JSONL import | importers.py:149-183 | (auto-detected) | JSONLImporter.parse() |
| Query translation | query_translator.py | (internal) | BooleanQueryTranslator.translate() |
| HTTP caching | http_client.py:47-121 | (automatic) | AcademicHttpClient |
| Rate limiting | http_client.py:18-44 | (automatic) | RateLimiter |
## 1.2 CLI Command-to-Function Mapping

| CLI Command | Function (cli.py) | Core API Call |
|:---|:---|:---|
| search (line 120) | search() | SearchEngine.search_all() |
| snowball (line 230) | snowball() | SearchEngine.snowball_forward/backward() |
| chain (line 312) | chain() | CitationChainer.chain() |
| import (line 431) | import_citations() | DocumentVerifier.process_batch() |
| dedup (line 507) | dedup() | Deduplicator.deduplicate() |
| verify (line 544) | verify() | DocumentVerifier.process_batch() |
| export (line 610) | export() | Exporter.json/jsonl/csv() |
| screen (line 632) | screen() | evaluate_heuristic_screening() |

## 1.3 Data Models and Schemas

### ExternalIds (models.py:8-38)
- Fields: doi, arxiv_id, pubmed_id, openalex_id, s2_id (all str | None)
- Auto-normalization: strips URL prefixes (https://doi.org/, doi:, etc.), lowercases DOIs

### Author (models.py:40-52)
- Fields: family_name: str, given_name: str | None, orcid: str | None
- Property: full_name returns "Given Family" or just "Family"

### Document (models.py:55-125)
- Core: title, year, provider, provider_id, external_ids, abstract, authors, venue, url
- Workspace: workspace_id, sources, oa_locations
- Enhanced: citations_count, references_count, citation_intents, mesh_terms, tldr, topics
- Auto-cleaning: HTML unescape, XML/JATS tag stripping, whitespace normalization

### Query (models.py:127-135)
- Fields: text, id="Q001", year_min, year_max, language="en", max_results, semantic=False

### DocumentCluster (models.py:138-154)
- Fields: cluster_id: int, representative: Document, members: list[Document]
- Properties: size, confidence (1.0 if persistent ID exists, else 0.95)

### ScreeningDecision (screening.py:17-27)
- Fields: workspace_id, decision (INCLUDE/EXCLUDE), confidence, screening_reasoning, matched_inclusion_criteria, violated_exclusion_criteria, relevant_rqs

### PrismaFlowReport (screening.py:30-73)
- Fields: total_identified, duplicates_removed, records_screened, records_excluded, records_included, conflicts_flagged, exclusion_reasons_breakdown
- Method: to_markdown() renders PRISMA 2020 flow table

### CitationEdge (snowball.py:60-68)
- Fields: source_id, target_id, direction, hop, provider

### Settings (config.py:9-52)
- Pydantic Settings: mailto, openalex_key, s2_key, cache_dir, cache_expire_days, rate limits
- Env prefix: SCHOLAR_

## 1.4 Integration Points with Other Kits

| Integration | Kit | Direction | Mechanism |
|:---|:---|:---|:---|
| Protocol consumption | scholar-protocol-kit | Inbound | protocol_adapter.py reads protocol.json |
| PDF harvesting | scholar-pdf-kit | Outbound | JSON export handoff (export.py) |
| RAG indexing | scholar-rag-kit | Outbound | JSON/JSONL export handoff |
| Bibliography validation | scholar-bib-kit | Outbound | CrossrefProvider.validate_reference() |
| Citation graph | scholar-graph-kit | Outbound | CitationEdge manifest (JSON) |
| Verification | scholar-verify-kit | Outbound | DocumentVerifier.process_batch() audit log |

## 1.5 Search Providers and Capabilities

| Provider | Search | Fwd Snowball | Bwd Snowball | Special Features |
|:---|:---:|:---:|:---:|:---|
| OpenAlex | Yes | Yes (cursor) | Yes (chunked) | Inverted-index abstract, topics, OA URLs, semantic search |
| Semantic Scholar | Yes (bulk) | Yes (intents) | Yes (intents) | TLDR, citation intents, bulk endpoint |
| Crossref | Yes | No | No | DOI validation, bibliographic matching |
| arXiv | Yes | No | No | Atom XML, arXiv ID extraction |
| PubMed | Yes | Yes (elink) | No | MeSH terms, esearch+efetch, XML parsing |
| bioRxiv | Yes | No | No | Chronological, local keyword filtering |
| InMemory | Yes | No | No | Offline testing |
| LocalFile | Yes | No | No | Offline .ris/.jsonl |
---

# 2. Improvements

## 2.1 Code Quality Issues

### 2.1.1 Dead Code: QueryParser unused as standalone utility
- Location: query_translator.py:63-153
- Issue: QueryParser is instantiated in BaseQueryTranslator but no provider calls parser.parse() standalone. Works within translator but not independently testable.
- Impact: Low.

### 2.1.2 Duplicate client close pattern
- Location: cli.py:486-487, cli.py:589-590
- Issue: Both import_citations() and verify() manually close verifier.crossref.client and verifier.openalex.client. HTTP clients leak on exceptions.
- Fix: Add __aenter__/__aexit__ to DocumentVerifier or wrap in try/finally.

### 2.1.3 Inconsistent exception swallowing in engine.py
- Location: engine.py:53-61
- Issue: fetch_provider() catches all exceptions and only logs them. Complete provider failure silently swallowed.
- Fix: Collect errors and return them alongside results.

### 2.1.4 RISImporter duplicate ER check
- Location: importers.py:25
- Issue: line.startswith("ER  -") or line.startswith("ER  -") -- identical condition (dead branch).

### 2.1.5 Type annotations inconsistency
- Location: engine.py:24
- Issue: providers: list[SearchProvider] = None should be list[SearchProvider] | None = None.

### 2.1.6 Missing __all__ entries in providers __init__.py
- Location: providers/__init__.py
- Issue: __all__ does not include InMemoryProvider or LocalFileProvider.

## 2.2 Missing Features

### 2.2.1 No get_references for arXiv and bioRxiv
- Location: arxiv.py:153, biorxiv.py:128
- Issue: Only comment stubs. CrossRef-based fallback possible using DOI.

### 2.2.2 LLMBatchScreener not wired into CLI screen command
- Location: screening.py:487-614 vs cli.py:632-695
- Issue: screen CLI only uses heuristic screener. LLMBatchScreener exists but has no CLI path.

### 2.2.3 No BibTeX export
- Location: export.py
- Issue: No .bib format. docs/lessons/17-export-bibtex.md suggests it was planned.

### 2.2.4 No CSV import
- Location: importers.py
- Issue: CSV is export-only. Common in manual screening workflows.

### 2.2.5 No incremental/streaming dedup
- Location: dedup.py:28-104
- Issue: Requires all documents in memory. Problematic for >100K documents.

### 2.2.6 No provider health check
- Issue: No CLI command to verify provider connectivity before full search.

## 2.3 API Design Improvements

### 2.3.1 SearchEngine.close() should be async context manager
- Location: engine.py:107-111
- Issue: Manual await engine.close() is error-prone. Should support async with.

### 2.3.2 DocumentVerifier lacks close()
- Issue: CLI manually closes internal clients. Verifier should own its lifecycle.

### 2.3.3 Query model should validate inputs
- Location: models.py:127-135
- Issue: No validation that max_results is positive or year_min <= year_max.

## 2.4 Error Handling Gaps

### 2.4.1 SearchEngine.snowball raises ValueError for missing provider
- Location: engine.py:88, 105
- Issue: Should raise custom ProviderNotFoundError.

### 2.4.2 DocumentVerifier.verify_document silently returns unverified on errors
- Location: verifier.py:68-90
- Issue: Non-200 responses and exceptions silently swallowed at debug level.

### 2.4.3 biorxiv.py has no pagination upper bound
- Location: biorxiv.py:95-127
- Issue: No timeout or max iteration guard on while True loop.

### 2.4.4 PubMedProvider XML parse error unhandled
- Location: pubmed.py:40
- Issue: ET.fromstring() raises ParseError on malformed XML.

### 2.4.5 crossref.py:validate_reference catches bare Exception
- Location: crossref.py:140-141
- Issue: except Exception: pass swallows all errors.
---

# 3. Problems

## 3.1 Known Bugs

### 3.1.1 RISImporter duplicate ER check
- Location: importers.py:25
- Code: line.startswith("ER  -") or line.startswith("ER  -") -- identical condition.

### 3.1.2 ScreeningDecision confidence threshold for conflicts
- Location: screening.py:388
- Code: if 0.40 <= dec.confidence <= 0.70: conflict_items.append(doc_dict)
- Issue: Low-confidence excludes (0.45) land in excluded without conflict flagging.

### 3.1.3 partition_screening_results double-counts conflicts
- Location: screening.py:388-394
- Issue: A document with confidence 0.55 added to BOTH conflict_items AND excluded_items.

### 3.1.4 OpenAlex get_references missing ID normalization
- Location: openalex.py:281
- Code: params = {"filter": f"openalex:{id_filter}"}
- Issue: referenced_works contains full URLs but filter expects short IDs. Backward snowballing returns empty results.

## 3.2 Edge Cases Not Handled

### 3.2.1 Empty title documents merge falsely
- Location: models.py:99-100, dedup.py:11
- Issue: Two documents with title "Untitled" would be falsely merged.

### 3.2.2 Year-only dedup pruning with None years
- Location: dedup.py:80
- Issue: If both documents have year=None, year gate skipped. False fuzzy matches possible.

### 3.2.3 Concurrent modification of all_results
- Location: engine.py:48-63
- Issue: Plain list mutated by concurrent coroutines via asyncio.gather().

### 3.2.4 CitationChainer visited set inconsistent
- Location: snowball.py:158-161
- Issue: Seeds added as raw AND normalized, but discovered docs only get normalized IDs.

### 3.2.5 bioRxiv pagination assumes sequential cursor
- Location: biorxiv.py:126
- Issue: cursor += len(collection) may not match API cursor semantics.

## 3.3 Limitations

### 3.3.1 Heuristic screening is domain-locked
- Location: screening.py:155-205
- Issue: _EXC_PHRASE_SIGNALS hardcoded for UAV/spectral imaging. Irrelevant for other domains.

### 3.3.2 Single-threaded verification
- Location: verifier.py:217-239
- Issue: Sequential processing. 1000 docs takes ~200s minimum.

### 3.3.3 arXiv year filtering is client-side
- Location: arxiv.py:128-151
- Issue: Fetches max_results entries then filters locally. Effective count much less than requested.
---

# 4. Optimizations

## 4.1 Performance Bottlenecks

### 4.1.1 Sequential verification in process_batch
- Location: verifier.py:217
- Impact: O(N) sequential API calls. 1000 docs = ~200s minimum.
- Fix: asyncio.gather() with semaphore for bounded parallelism.

### 4.1.2 Fuzzy dedup is O(N*M)
- Location: dedup.py:74-89
- Issue: Linear scan over all previous documents. 10K docs = ~50M comparisons.
- Fix: Sorted title key blocks or LSH for large collections.

### 4.1.3 OpenAlex inverted index reconstruction
- Location: openalex.py:125-138
- Issue: Sort-based reconstruction. Could pre-allocate array.

## 4.2 Memory Usage

### 4.2.1 All results loaded into memory
- Location: engine.py:48
- Issue: all_results accumulates all documents. Significant memory for 10K+ docs.
- Fix: Stream through deduplicator using iterator pattern.

### 4.2.2 Deduplicator fuzzy_pool grows unboundedly
- Location: dedup.py:32
- Issue: Memory proportional to total documents.

## 4.3 Caching Opportunities

### 4.3.1 Cross-provider dedup cache
- Issue: Same document from different providers not recognized across sessions.
- Fix: Persistent DOI-to-cluster mapping.

### 4.3.2 Snowballing reference cache
- Issue: get_references() and get_citations() not cached beyond HTTP cache.
- Fix: Cache citation lists keyed by document_id at provider level.

## 4.4 Parallelization Potential

### 4.4.1 Multi-provider search (already parallelized)
- Location: engine.py:63
- Status: asyncio.gather() runs concurrently. Well-implemented.

### 4.4.2 Batch verification parallelization
- Potential: 5-10x speedup for large batches with bounded concurrency.

### 4.4.3 Snowballing BFS parallelization
- Potential: Significant speedup for depth>2 by parallelizing within hop levels.
---

# 5. Scientific Correction

## 5.1 Accuracy of Search Algorithms

### 5.1.1 OpenAlex Boolean query approximation
- Location: openalex.py:28
- Issue: operator_map={"AND": " ", "OR": " ", "NOT": "-"} -- both AND and OR map to space.
- Impact: HIGH. "deep learning" AND "crop disease" treated as OR by OpenAlex.
- Mitigation: _build_params (line 140) handles AND/OR by extracting key terms, but translator is lossy.

### 5.1.2 Crossref relevance score threshold
- Location: crossref.py:138
- Issue: score > 40 described as "arbitrary." Higher threshold (60-70) would reduce false positives.

### 5.1.3 Title similarity threshold in dedup
- Location: dedup.py:87
- Threshold: >= 0.97
- Assessment: Conservative and appropriate. May miss near-duplicates with title variations.

### 5.1.4 Verification title match threshold
- Location: verifier.py:114, 137
- Threshold: >= 0.90
- Assessment: Reasonable. Bidirectional containment adds robustness for subtitle variations.

## 5.2 Deduplication Correctness

### 5.2.1 Two-tier strategy is sound
- Tier 1 (canonical IDs) O(1). Tier 2 (fuzzy title) pruned linear scan.
- Author surname and year tolerance (+/-1) are appropriate guards.

### 5.2.2 Metadata merge is non-destructive
- Only fills missing fields, takes maximums for numerical, prefers richer author lists. Correct for SLR.

### 5.2.3 Weakness: No cross-reference validation during merge
- Conflicting metadata for same DOI silently picks first title. No conflict detection.

## 5.3 Verification Reliability

### 5.3.1 Multi-fallback strategy is robust
- DOI (Crossref) -> DOI (OpenAlex) -> arXiv ID (OpenAlex) -> Title (Crossref) -> Title (OpenAlex).

### 5.3.2 Title mismatch guard prevents contamination
- Location: verifier.py:161-180
- bidirectional_title_similarity check prevents contaminated DOIs from overwriting metadata.

### 5.3.3 Weakness: No Semantic Scholar verification
- Only Crossref and OpenAlex used. S2 could provide additional verification.

## 5.4 PRISMA Screening Alignment

### 5.4.1 Heuristic screener is a pre-filter
- Documented as "deterministic rule-based baseline screener." LLMBatchScreener is the capable alternative.

### 5.4.2 PRISMA flow report is accurate
- PrismaFlowReport.to_markdown() correctly implements PRISMA 2020 flow diagram.

### 5.4.3 Weakness: Hardcoded exclusion signals
- Location: screening.py:155-205
- Domain-specific (UAV/spectral). Should be configurable per protocol.

## 5.5 Academic Database Coverage

### 5.5.1 Good coverage of major databases
- OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv, bioRxiv. Covers vast majority.

### 5.5.2 Missing proprietary databases
- Scopus, Web of Science, IEEE Xplore, ACM DL not accessible via free APIs.
---

# 6. Agent/Skill Recommendation

## 6.1 Should a specialized agent or skill be created?

YES -- a specialized search-optimizer skill/agent is recommended.

### 6.1.1 Rationale

1. Query optimization is iterative: users refine queries based on result quality.
2. Provider selection is context-dependent: different domains benefit from different mixes.
3. Dedup tuning requires judgment: 0.97 threshold may need domain adjustment.
4. Screening calibration needs feedback loops: heuristic accuracy varies by domain.

### 6.1.2 Narrow Scope of Tasks

| Task | Description | Frequency |
|:---|:---|:---|
| Query refinement | Suggest query modifications based on result quality | Per search session |
| Provider recommendation | Recommend optimal provider mix by research domain | Per project |
| Dedup threshold tuning | Adjust fuzzy match threshold by domain | Per project |
| Result quality assessment | Evaluate search completeness and precision | Per search session |
| Screening calibration | Tune heuristic signals based on human feedback | Per protocol |

### 6.1.3 Evaluation Metrics

| Metric | Definition | Target |
|:---|:---|:---|
| Search Recall | (Relevant found) / (Relevant total) | >= 0.85 |
| Search Precision | (Relevant found) / (Total retrieved) | >= 0.30 |
| Dedup Accuracy | (Correctly merged) / (Total merged) | >= 0.99 |
| Dedup Recall | (Correctly merged) / (Total duplicates) | >= 0.90 |
| Verification Precision | (True verified) / (Total verified) | >= 0.95 |
| Verification Recall | (True verified) / (Total real docs) | >= 0.80 |
| Screening Kappa | Agreement between heuristic and LLM | >= 0.70 |
| Query Iterations | Number of refinements needed | <= 3 |
| Provider Coverage | Fraction of relevant literature covered | >= 0.90 |

### 6.1.4 Critic Capabilities Needed

1. Query Quality Critic: evaluates precision/recall balance
2. Result Diversity Critic: checks venue/year/author spread
3. Dedup Quality Critic: samples merged clusters for correctness
4. Provider Coverage Critic: identifies provider gaps
5. Screening Calibration Critic: compares heuristic vs LLM/human decisions

### 6.1.5 Agent-in-the-Loop Opportunities

1. Search iteration loop: search -> evaluate -> refine -> re-search
2. Dedup review loop: present borderline clusters for human confirmation
3. Screening calibration loop: screen sample -> human review -> adjust -> re-screen
4. Snowballing expansion decisions: decide which cited papers to follow
5. Provider health monitoring: detect degraded providers and adjust mix

### 6.1.6 Automation Potential

| Process | Current State | Automation Potential |
|:---|:---|:---|
| Query formulation | Manual | HIGH |
| Provider selection | Manual (default set) | MEDIUM |
| Dedup threshold | Fixed (0.97) | MEDIUM |
| Screening | Heuristic or LLM (separate) | HIGH |
| Snowballing depth | Manual | MEDIUM |
| Verification | Sequential, manual trigger | HIGH |
---

# 7. Priority-Ranked Improvement Suggestions

## Priority 1: Critical (affects correctness)

| # | Issue | Location | Fix |
|:---|:---|:---|:---|
| P1-1 | OpenAlex AND/OR both map to space | openalex.py:28 | Use OpenAlex filter for AND queries |
| P1-2 | get_references URL normalization missing | openalex.py:281 | Apply _normalize_doc_id() before joining |
| P1-3 | Conflicts overlap with included/excluded | screening.py:388-394 | Document explicitly or separate conflict set |
| P1-4 | Hardcoded screening signals domain-locked | screening.py:155-205 | Make signals configurable via protocol JSON |

## Priority 2: High (affects reliability)

| # | Issue | Location | Fix |
|:---|:---|:---|:---|
| P2-1 | No async context manager for SearchEngine | engine.py:107-111 | Add __aenter__/__aexit__ |
| P2-2 | DocumentVerifier lacks close() | verifier.py | Add async with support |
| P2-3 | Silent provider failure | engine.py:53-61 | Collect and report errors |
| P2-4 | Sequential verification bottleneck | verifier.py:217-239 | Parallelize with semaphore |
| P2-5 | PubMed XML parse error unhandled | pubmed.py:40 | Wrap in try/except |

## Priority 3: Medium (affects usability)

| # | Issue | Location | Fix |
|:---|:---|:---|:---|
| P3-1 | No BibTeX export | export.py | Add Exporter.bibtex() |
| P3-2 | LLMBatchScreener not in CLI | screening.py/cli.py | Wire into screen with --llm flag |
| P3-3 | RISImporter duplicate ER check | importers.py:25 | Remove redundant condition |
| P3-4 | Exporter.csv drops fields silently | export.py:44-56 | Document or add optional fields |
| P3-5 | No provider health check | cli.py | Add scholar-search status |

## Priority 4: Low (affects polish)

| # | Issue | Location | Fix |
|:---|:---|:---|:---|
| P4-1 | Type annotation list[X] = None | engine.py:24 | Use list[X] | None = None |
| P4-2 | __all__ missing InMemoryProvider | providers/__init__.py | Add to __all__ |
| P4-3 | QueryParser.validate() never standalone | query_translator.py:137 | Expose as CLI or documented API |
| P4-4 | No streaming dedup | dedup.py | Implement block-based dedup |
| P4-5 | bioRxiv cursor may be incorrect | biorxiv.py:126 | Verify against API docs |

---

# Appendix A: File Inventory

## Source Files (22)

| File | Lines | Purpose |
|:---|---:|:---|
| __init__.py | 52 | Public API exports |
| models.py | 154 | Core data models |
| cli.py | 704 | Typer CLI application |
| engine.py | 111 | Search orchestration |
| dedup.py | 223 | Deduplication engine |
| verifier.py | 239 | Verification and hydration |
| snowball.py | 242 | Multi-hop citation snowballing |
| query_translator.py | 219 | Boolean query parsing/translation |
| screening.py | 745 | PRISMA screening engine |
| export.py | 76 | Document exporters |
| importers.py | 183 | Document importers |
| config.py | 56 | Pydantic settings |
| exceptions.py | 32 | Exception hierarchy |
| http_client.py | 122 | HTTP client with caching/rate limiting |
| protocol_adapter.py | 90 | Protocol JSON compiler |
| providers/__init__.py | 20 | Provider package exports |
| providers/base.py | 123 | Provider protocol and base classes |
| providers/openalex.py | 288 | OpenAlex implementation |
| providers/crossref.py | 142 | Crossref implementation |
| providers/semanticscholar.py | 157 | Semantic Scholar implementation |
| providers/arxiv.py | 153 | arXiv implementation |
| providers/pubmed.py | 184 | PubMed implementation |
| providers/biorxiv.py | 128 | bioRxiv implementation |

**Total production code**: ~3,437 lines

## Test Files (11)

| File | Tests | Lines |
|:---|---:|---:|
| test_models.py | 5 | 66 |
| test_scholar_search.py | 1 | 15 |
| test_dedup.py | 3 | 110 |
| test_verifier.py | 5 | 152 |
| test_engine.py | 2 | 73 |
| test_providers.py | 16 | 536 |
| test_cli.py | 4 | 103 |
| test_snowball.py | 12 | 348 |
| test_screening.py | 4 | 133 |
| test_importers_exporters.py | 2 | 68 |
| test_query_translator.py | 4 | 53 |
| test_protocol_adapter.py | 3 | 93 |

**Total test code**: ~1,850 lines, ~61 test functions

---

# Appendix B: Key Code References

- **Dedup threshold**: dedup.py:87 (>= 0.97)
- **Verification threshold**: verifier.py:114,137 (>= 0.90)
- **Bidirectional containment min**: verifier.py:17 (_BIDIRECTIONAL_CONTAINMENT_MIN = 12)
- **Rate limits**: config.py:34-45 (OpenAlex 10, Crossref 5, S2 1, PubMed 3 req/s)
- **Cache TTL**: config.py:29-30 (30 days default)
- **Max results per provider**: OpenAlex 200/page, Crossref 1000, S2 paginated, arXiv 1000, PubMed 1000
- **Sandbox limits (chaining)**: snowball.py:22-26 (depth 5, per-node 500, total 2000)
- **Screening conflict zone**: screening.py:388 (confidence 0.40-0.70)
- **Hardcoded exclusion signals**: screening.py:155-205 (UAV/spectral domain)