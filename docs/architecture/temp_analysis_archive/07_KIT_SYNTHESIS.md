# Nexus Scholar Kits - Deep Analysis Synthesis

**Date:** 2026-09-14  
**Analyst:** opencode (mimo-v2.5-free)  
**Scope:** Comprehensive analysis of all 8 kits with agent/skill recommendations

---

## Executive Summary

I've completed deep dive analysis of all 8 kits in the Nexus Scholar Harness. Here are the key findings and recommendations for creating specialized agents with narrow scope, evaluation metrics, and critic capabilities.

### Overall Kit Assessment

| Kit | Maturity | Quality | Critical Issues | Agent Recommended |
|-----|----------|---------|-----------------|-------------------|
| scholar-protocol-kit | Production | A | 4 | **YES** - protocol-qa-agent |
| scholar-search-kit | Beta | B+ | 3 | **YES** - search-optimizer-agent |
| scholar-pdf-kit | Beta | B | 5 | **YES** - pdf-quality-agent |
| scholar-bib-kit | Alpha | C+ | 4 | NO (fix docs first) |
| scholar-rag-kit | Beta | B | 4 | **YES** - rag-quality-agent |
| scholar-graph-kit | Alpha | C+ | 5 | NO (expand SKILL.md) |
| scholar-agent-kit | Beta | B+ | 3 | **YES** - calibration-agent |
| scholar-verify-kit | Beta | B | 2 | NO (deterministic) |

---

## 1. Kit-by-Kit Analysis Summary

### 1.1 scholar-protocol-kit (Contract Spine)
**Status:** Production-ready, exemplary determinism guarantees

**Key Strengths:**
- Mathematical determinism: same IntentPacket → byte-identical protocol.json
- Two-tier validation: structural (Pydantic) + cross-field semantic rules
- Comprehensive golden fixture conformance testing with pinned SHA-256 fingerprints
- Clean CLI with proper exit code semantics

**Critical Issues:**
1. Missing `date_range` key existence validation (`validate.py:178-198`)
2. Missing `target_candidate_pool_size` key existence validation (`validate.py:200-215`)
3. Missing `created_at` ISO-8601 format validation (`models.py:316-319`)
4. Untyped `metadata` field with no validation

**Scientific Accuracy:**
- ✅ Protocol schema aligns with research methodology standards
- ✅ Epistemological paradigm handling is correct
- ⚠️ No protocol versioning/migration strategy beyond v1.0.0
- ⚠️ Limited extraction model capabilities for categorical dimensions

**Agent Recommendation:** **YES** - Create `protocol-qa-agent`
- **Evaluation Metrics:** Validation coverage %, cross-field rule completeness, extraction model accuracy
- **Critic Capabilities:** Schema validator, methodology checker, integration tester
- **Agent-in-the-loop:** Protocol review, quality assurance, downstream compatibility check

---

### 1.2 scholar-search-kit (Discovery Engine)
**Status:** Beta, mature architecture with integration gaps

**Key Strengths:**
- Clean separation of concerns across 22 source files
- Non-destructive metadata fusion during dedup
- Robust HTTP resilience layer with caching
- LLM-powered screening capability
- PRISMA 2020 compliance

**Critical Issues:**
1. **CRITICAL:** OpenAlex Boolean query approximation (`openalex.py:28`) - AND/OR both map to space, scientifically incorrect for SLR
2. **CRITICAL:** `get_references` URL normalization missing (`openalex.py:281`) - backward snowballing returns empty results
3. **CRITICAL:** Hardcoded screening signals (`screening.py:155-205`) - UAV/spectral domain locked, causes false exclusions

**Scientific Accuracy:**
- ⚠️ OpenAlex query translation is lossy (AND/OR → space)
- ⚠️ Dedup threshold (0.97) may be too aggressive for some domains
- ✅ PRISMA screening alignment is sound
- ⚠️ Missing Semantic Scholar in verification pipeline

**Agent Recommendation:** **YES** - Create `search-optimizer-agent`
- **Evaluation Metrics:** Query precision/recall, dedup accuracy, verification coverage, screening F1
- **Critic Capabilities:** Query validator, provider health checker, dedup tuner, result quality assessor
- **Agent-in-the-loop:** Query refinement, provider recommendation, screening calibration

---

### 1.3 scholar-pdf-kit (PDF Acquisition)
**Status:** Beta, robust download cascade with extraction gaps

**Key Strengths:**
- Robust 3-attempt download cascade (OpenAlex → Unpaywall → publisher patterns → proxy)
- Strict binary validation (magic bytes + 10KB size floor + EOF trailer)
- Well-tested publisher pattern rewriting for 5 major publishers
- Clean async architecture with configurable concurrency

**Critical Issues:**
1. **CRITICAL:** PyMuPDF error swallowing (`extract.py:85-87`) - silently produces stub lines, causing downstream RAG to index empty documents
2. **CRITICAL:** Undeclared `pyyaml` dependency - breaks on clean install
3. **CRITICAL:** Malformed BibTeX export (`cli.py:63-77`) - missing braces, no escaping
4. User-Agent mismatch - docs claim polite UA but code uses Chrome browser UA
5. Dead code - `OAResult`/`OALocation` models defined but never used

**Scientific Accuracy:**
- ⚠️ No OCR fallback for scanned PDFs
- ⚠️ Section detection limited to common headers
- ⚠️ Single-author metadata extraction only
- ⚠️ No license tracking despite model support

**Agent Recommendation:** **YES** - Create `pdf-quality-agent`
- **Evaluation Metrics:** Download success rate, extraction completeness, metadata accuracy, validation pass rate
- **Critic Capabilities:** PDF validator, extraction quality assessor, metadata consistency checker
- **Agent-in-the-loop:** Download review, extraction validation, metadata hydration

---

### 1.4 scholar-bib-kit (BibTeX Management)
**Status:** Alpha, minimal with critical documentation gaps

**Key Strengths:**
- Simple, focused API for BibTeX operations
- Clean CLI with 4 commands (lint, merge, dedup, resolve)
- Deterministic deduplication

**Critical Issues:**
1. **CRITICAL:** Documentation entirely stale - `docs/api_reference.md` and `docs/tutorial.md` describe classes that don't exist
2. **CRITICAL:** Entry corruption risk - `resolver.py:80` calls `entry.fields_dict.clear()` before verifying new entry parsed successfully
3. **CRITICAL:** Incorrect resolution output - resolved.bib shows wrong paper matches (no relevance score check)
4. Resource leak - `BibResolver` creates `AcademicHttpClient` but never closes it

**Scientific Accuracy:**
- ⚠️ No relevance scoring for resolution matches
- ⚠️ No confidence thresholds for automated resolution
- ⚠️ Missing integration with scholar-search-kit's CrossrefProvider

**Agent Recommendation:** **NO** (fix docs first)
- The existing SKILL.md is well-structured
- Create a dedicated agent only if resolve pipeline needs intelligent orchestration
- **First priority:** Rewrite documentation to match actual API

---

### 1.5 scholar-rag-kit (RAG Synthesis)
**Status:** Beta, sophisticated with scientific accuracy gaps

**Key Strengths:**
- 8 source modules with 1,827 lines of core logic
- 12 Pydantic data models covering full RAG pipeline
- 6 RAG components: AST chunker, idempotent indexer, hybrid retriever, synthesis engine, matrix extractor, consensus cartographer
- Comprehensive integration with other kits

**Critical Issues:**
1. **CRITICAL:** Undeclared dependency (`matrix.py:15-16`) - `scholar-protocol-kit` imported but not in pyproject.toml
2. **CRITICAL:** Dead parameter (`chunker.py:23`) - `min_chunk_chars` accepted but never used
3. **CRITICAL:** Schema mismatch (`models.py:193-202`) - `SynthesisClaim` lacks `evidence_quote`/`claim_id` needed by verify-kit
4. **CRITICAL:** Misleading default (`synthesis.py:318`) - `entailment_rate = 1.0` when no claims exist

**Scientific Accuracy:**
- ⚠️ Entailment score scaling inflates cosine similarity by +1.0 shift
- ⚠️ Deterministic synthesis produces shallow bullet lists, not genuine synthesis
- ⚠️ Section slug truncation to 10 chars may cause collisions
- ⚠️ BibTeX filename matching uses greedy substring search (false positive risk)
- ⚠️ Consensus verdicts ignore study quality/statistical significance

**Agent Recommendation:** **YES** - Create `rag-quality-agent`
- **Evaluation Metrics:** Indexing quality, retrieval MRR/NDCG, synthesis entailment rate, consensus coherence, matrix completeness
- **Critic Capabilities:** Chunking validator, retrieval quality assessor, synthesis evaluator, citation checker
- **Agent-in-the-loop:** Query expansion, claim verification, threshold tuning, quality gate

---

### 1.6 scholar-graph-kit (Citation Networks)
**Status:** Alpha, minimal but functional

**Key Strengths:**
- Clean, focused API for citation graph construction
- Correct PageRank implementation (alpha=0.85, normalized)
- Interactive PyVis HTML visualization
- Simple CLI with 2 commands (build, info)

**Critical Issues:**
1. **CRITICAL:** Unbounded concurrency (`builder.py:36-40`) - all DOIs fetched simultaneously with no semaphore, WILL trigger OpenAlex 429s
2. **CRITICAL:** Silent error swallowing (`builder.py:24-25`) - all fetch failures produce `pass`
3. **CRITICAL:** PageRank fallback (`builder.py:113-114`) - errors silently return uniform 1.0
4. Dead code - `models.py` and `config.py` account for ~50% of source
5. Documentation references nonexistent classes

**Scientific Accuracy:**
- ✅ PageRank implementation is correct
- ✅ Edge direction is correct (source cites target; target receives PageRank)
- ⚠️ Missing: HITS, betweenness centrality, citation velocity, co-citation clustering
- ⚠️ Visualization uses citation count for sizing but ignores PageRank

**Agent Recommendation:** **NO** (expand SKILL.md)
- Narrow scope, low frequency, fully automated
- Add graph quality validation metrics to existing SKILL.md
- Agent-in-the-loop opportunities: graph interpretation, community analysis, anomaly detection

---

### 1.7 scholar-agent-kit (MCP Server)
**Status:** Beta, well-designed orchestration layer

**Key Strengths:**
- 19 MCP tools exposing all kits to AI agents
- Clean separation of concerns
- Comprehensive calibration module (467 lines, 11 tests)
- Well-documented tool schemas

**Critical Issues:**
1. **CRITICAL:** Undeclared `scholar-verify-kit` dependency - works only via shared venv
2. Duplicate `import re` inside function body (`server.py:703`)
3. `nexus_extract_pdf` silent fallback for unrecognized engine names
4. `recon_distill` dual-type parameter violates MCP type system

**Scientific Accuracy:**
- ✅ MCP protocol compliance is good
- ⚠️ Tool design could be more granular
- ⚠️ Missing batch operations for common workflows

**Agent Recommendation:** **YES** - Create `calibration-agent`
- **Evaluation Metrics:** Tool call success rate ≥95%, sensitivity ≥80%, specificity ≥70%, inclusion-rate drift <0.15
- **Critic Capabilities:** Calibration validator, sensitivity analyzer, specificity assessor
- **Agent-in-the-loop:** Calibration build, calibration evaluate, threshold tuning

---

### 1.8 scholar-verify-kit (Trust Verification)
**Status:** Beta, deterministic with domain coupling

**Key Strengths:**
- Clean separation of concerns across 8 modules
- Deterministic trust-level hierarchy (BLOCKED > UNVERVERIFIED > WEAK > ADEQUATE > STRONG)
- Standard `{run_metadata, summary, results}` envelope
- Well-defined integration points

**Critical Issues:**
1. **CRITICAL:** Missing `import re` in `cli.py:247,251` - `verbatim-claims` CLI command will crash with NameError
2. **CRITICAL:** `import time` inside hot loop (`retraction.py:56`) - anti-pattern
3. Domain coupling - `risk_of_bias.py` hardcodes UAV agriculture benchmarks
4. Inconsistent error handling - `SystemExit` instead of proper exceptions

**Scientific Accuracy:**
- ⚠️ Risk-of-bias scoring is domain-locked (UAV agriculture)
- ⚠️ No adaptive thresholds for different research domains
- ✅ Trust-level hierarchy is well-documented and deterministic
- ✅ Integration with OpenAlex/Crossref for retraction checks

**Agent Recommendation:** **NO** (deterministic operations)
- Tasks are deterministic, best driven by CLI commands
- MCP server integration already provides agent-facing surface
- LLM-dependent components properly delegated to scholar-agent-kit

---

## 2. Agent/Skill Creation Recommendations

### 2.1 Recommended Agents (5 new)

#### 1. protocol-qa-agent
**Purpose:** Quality assurance for research protocols
**Scope:** Narrow - protocol validation, methodology checking, integration testing
**Evaluation Metrics:**
- Validation coverage: % of edge cases caught
- Cross-field rule completeness: % of semantic rules implemented
- Extraction model accuracy: % of dimensions correctly typed
- Integration compatibility: % of downstream kits that consume protocol.json without errors

**Critic Capabilities:**
- Schema validator: Check protocol.json against JSON Schema
- Methodology checker: Verify alignment with PRISMA/PRISMA-S
- Integration tester: Validate protocol consumes correctly by downstream kits
- Version compatibility: Check protocol version compatibility

**Agent-in-the-loop Opportunities:**
- Protocol review before finalization
- Quality assurance checkpoint
- Downstream compatibility verification

#### 2. search-optimizer-agent
**Purpose:** Optimize literature search queries and provider selection
**Scope:** Narrow - query refinement, provider recommendation, dedup tuning
**Evaluation Metrics:**
- Query precision: % of returned documents relevant
- Query recall: % of relevant documents returned
- Dedup accuracy: % of true duplicates correctly identified
- Verification coverage: % of documents successfully verified
- Screening F1: Harmonic mean of precision and recall

**Critic Capabilities:**
- Query validator: Check query syntax and Boolean logic
- Provider health checker: Monitor API availability and rate limits
- Dedup tuner: Adjust thresholds based on domain characteristics
- Result quality assessor: Score document relevance and completeness

**Agent-in-the-loop Opportunities:**
- Query refinement based on initial results
- Provider recommendation for specific domains
- Screening calibration for different research types

#### 3. pdf-quality-agent
**Purpose:** Ensure PDF download and extraction quality
**Scope:** Narrow - download validation, extraction quality, metadata accuracy
**Evaluation Metrics:**
- Download success rate: % of PDFs successfully downloaded
- Extraction completeness: % of content extracted without errors
- Metadata accuracy: % of fields correctly extracted
- Validation pass rate: % of PDFs passing validation checks

**Critic Capabilities:**
- PDF validator: Check binary integrity and structure
- Extraction quality assessor: Score extraction completeness and accuracy
- Metadata consistency checker: Verify metadata against external sources
- Format compliance checker: Ensure output meets downstream requirements

**Agent-in-the-loop Opportunities:**
- Download review for failed or questionable downloads
- Extraction validation for critical documents
- Metadata hydration for incomplete records

#### 4. rag-quality-agent
**Purpose:** Ensure RAG indexing and synthesis quality
**Scope:** Narrow - chunking quality, retrieval relevance, synthesis accuracy
**Evaluation Metrics:**
- Indexing quality: % of documents correctly chunked and indexed
- Retrieval MRR: Mean Reciprocal Rank of relevant chunks
- Retrieval NDCG: Normalized Discounted Cumulative Gain
- Synthesis entailment rate: % of claims supported by evidence
- Consensus coherence: Inter-annotator agreement on consensus verdicts

**Critic Capabilities:**
- Chunking validator: Check chunk boundaries and overlap
- Retrieval quality assessor: Score retrieval relevance and diversity
- Synthesis evaluator: Verify claims against source material
- Citation checker: Ensure all claims have proper citations

**Agent-in-the-loop Opportunities:**
- Query expansion for better retrieval
- Claim verification for critical synthesis outputs
- Threshold tuning for similarity and entailment scores
- Quality gate before final synthesis delivery

#### 5. calibration-agent
**Purpose:** Build and evaluate screener calibration for PRISMA screening
**Scope:** Narrow - calibration building, sensitivity/specificity analysis
**Evaluation Metrics:**
- Tool call success rate: ≥95%
- Sensitivity: ≥80% (true positive rate)
- Specificity: ≥70% (true negative rate)
- Inclusion-rate drift: <0.15 (difference between calibration and full screening)

**Critic Capabilities:**
- Calibration validator: Check calibration dataset quality
- Sensitivity analyzer: Evaluate true positive detection
- Specificity assessor: Evaluate true negative detection
- Drift detector: Monitor inclusion-rate changes

**Agent-in-the-loop Opportunities:**
- Calibration build from sample screening decisions
- Calibration evaluate against gold standard
- Threshold tuning for different research domains

### 2.2 NOT Recommended (3 kits)

#### scholar-bib-kit
**Reason:** Fix documentation first
- Existing SKILL.md is well-structured
- Create agent only if resolve pipeline needs intelligent orchestration
- **First priority:** Rewrite `docs/api_reference.md` and `docs/tutorial.md` to match actual API

#### scholar-graph-kit
**Reason:** Narrow scope, fully automated
- Expand existing SKILL.md with quality validation metrics
- Add graph quality metrics (node count, density, fallback ratio, PageRank sanity)
- Agent-in-the-loop opportunities exist but don't warrant full agent

#### scholar-verify-kit
**Reason:** Deterministic operations
- Tasks are deterministic, best driven by CLI commands
- MCP server integration already provides agent-facing surface
- LLM-dependent components properly delegated to scholar-agent-kit

---

## 3. Cross-Kit Integration Issues

### 3.1 Undeclared Dependencies
1. scholar-rag-kit → scholar-protocol-kit (matrix.py:15-16)
2. scholar-agent-kit → scholar-verify-kit (pyproject.toml)
3. scholar-bib-kit → scholar-search-kit (resolver.py builds its own Crossref client)

### 3.2 Schema Mismatches
1. scholar-rag-kit `SynthesisClaim` lacks `evidence_quote`/`claim_id` needed by scholar-verify-kit
2. scholar-protocol-kit extraction models don't propagate enum constraints for categorical dimensions

### 3.3 API Inconsistencies
1. scholar-bib-kit resolver builds its own Crossref client instead of using scholar-search-kit's `CrossrefProvider.validate_reference()`
2. scholar-verify-kit uses private APIs (`_merged_records`, `_load`, `_write`) from other kits

---

## 4. Priority-Ranked Improvements

### 4.1 Critical (P0) - Fix Immediately
1. **Fix OpenAlex Boolean query translation** (`search-kit/openalex.py:28`)
2. **Fix PyMuPDF error swallowing** (`pdf-kit/extract.py:85-87`)
3. **Fix missing `import re` in verify-kit CLI** (`verify-kit/cli.py:247`)
4. **Fix entry corruption risk in bib-kit** (`bib-kit/resolver.py:80`)
5. **Add asyncio.Semaphore to graph-kit** (`graph-kit/builder.py:36-40`)

### 4.2 High (P1) - Fix Soon
1. **Add validation for date_range, target_candidate_pool_size** (`protocol-kit/validate.py`)
2. **Fix hardcoded screening signals** (`search-kit/screening.py:155-205`)
3. **Declare all dependencies explicitly** in pyproject.toml files
4. **Rewrite stale documentation** for bib-kit and graph-kit
5. **Fix malformed BibTeX export** (`pdf-kit/cli.py:63-77`)

### 4.3 Medium (P2) - Schedule
1. **Extract shared utilities** (Windows UTF-8, _read_env_file)
2. **Create shared test fixtures** (tests/conftest.py)
3. **Split large files** (inception.py, orchestrator.py)
4. **Add performance baselines** for critical paths
5. **Expand E2E edge cases** (empty inputs, concurrent access)

### 4.4 Low (P3) - Backlog
1. **Add script unit tests** for automation scripts
2. **Implement documentation automation** (mkdocs/sphinx)
3. **Add protocol versioning/migration strategy**
4. **Expand graph-kit with HITS, betweenness centrality**
5. **Add OCR fallback for scanned PDFs**

---

## 5. Agent Design Patterns

### 5.1 Narrow Scope Principle
Each agent should focus on ONE specific task:
- **protocol-qa-agent:** Protocol validation only
- **search-optimizer-agent:** Query optimization only
- **pdf-quality-agent:** PDF quality only
- **rag-quality-agent:** RAG quality only
- **calibration-agent:** Calibration only

### 5.2 Evaluation Metrics
Each agent needs quantifiable metrics:
- **Success rate:** % of operations completed successfully
- **Accuracy:** % of correct results (precision/recall/F1)
- **Coverage:** % of edge cases handled
- **Performance:** Execution time and resource usage

### 5.3 Critic Capabilities
Each agent needs self-evaluation:
- **Validator:** Check input/output correctness
- **Assessor:** Score quality against standards
- **Checker:** Verify compliance with requirements
- **Detector:** Identify anomalies and edge cases

### 5.4 Agent-in-the-loop Integration
Each agent should support human review:
- **Review points:** Where human input is needed
- **Confidence thresholds:** When to escalate to human
- **Audit trail:** Log all decisions for review
- **Feedback loop:** Learn from human corrections

---

## 6. Implementation Roadmap

### Phase 1: Foundation (2 weeks)
1. Fix critical bugs (P0 items)
2. Extract shared utilities
3. Create shared test fixtures
4. Rewrite stale documentation

### Phase 2: Agent Development (4 weeks)
1. Create protocol-qa-agent skill
2. Create search-optimizer-agent skill
3. Create pdf-quality-agent skill
4. Create rag-quality-agent skill
5. Create calibration-agent skill

### Phase 3: Integration (2 weeks)
1. Integrate agents with MCP server
2. Add evaluation metrics to each agent
3. Implement critic capabilities
4. Create agent-in-the-loop workflows

### Phase 4: Testing & Optimization (2 weeks)
1. Add performance baselines
2. Expand E2E test coverage
3. Optimize critical paths
4. Document agent workflows

---

## 7. Conclusion

The Nexus Scholar Harness has a solid foundation with 8 well-designed kits. The main opportunities are:

1. **Fix critical bugs** that affect scientific accuracy
2. **Create specialized agents** with narrow scope and evaluation metrics
3. **Improve cross-kit integration** by fixing schema mismatches and undeclared dependencies
4. **Enhance documentation** to match actual API capabilities
5. **Add quality gates** at each pipeline stage

The recommended agents (protocol-qa, search-optimizer, pdf-quality, rag-quality, calibration) will provide significant value by adding intelligent quality assurance to deterministic operations. Each agent should have clear evaluation metrics, critic capabilities, and agent-in-the-loop integration points.

---

*Analysis generated by opencode (mimo-v2.5-free) on 2026-09-14*
*Detailed findings in: kit_01_protocol.md through kit_08_verify.md*