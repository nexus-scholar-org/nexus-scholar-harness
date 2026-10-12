# 02 Kits Architecture Spec
<!-- Source: 07_KIT_SYNTHESIS.md -->
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

---

<!-- Source: kit_01_protocol.md -->
﻿# scholar-protocol-kit: Comprehensive Deep Dive Analysis

> **Kit Location:** tools/scholar-protocol-kit
> **Version:** 1.0.0
> **Analysis Date:** 2026-09-14

---

## Executive Summary

The scholar-protocol-kit is the **contract spine** of the Nexus Scholar research pipeline. It provides a deterministic, zero-LLM, zero-network protocol compilation and validation system for Phase 0 of systematic literature reviews. The kit is well-designed with strong determinism guarantees, comprehensive test coverage (83 test functions across 6 test files), and a clean separation of concerns across 9 source modules.

**Key Strengths:**
- Mathematical determinism: same IntentPacket always produces byte-identical protocol.json
- Two-tier validation: structural (Pydantic) + cross-field semantic rules
- Comprehensive golden fixture conformance testing with pinned SHA-256 fingerprints
- Clean CLI with proper exit code semantics (0=valid, 1=invalid, 2=usage error)
- Schema sync CI guard preventing model/schema drift

**Key Weaknesses:**
- Several edge cases in validation not covered (e.g., date_range missing keys, target_databases empty list)
- metadata field is untyped Dict[str, Any] with no validation
- No protocol versioning/migration strategy beyond v1.0.0
- Limited extraction model capabilities (no enum constraint propagation for categorical dimensions)
- Missing integration tests with downstream kits (scholar-rag-kit, scholar-agent-kit)

**Overall Assessment:** Production-ready for its core use case. The determinism guarantees and test suite are exemplary. Main areas for improvement are edge case handling, extraction model sophistication, and cross-kit integration robustness.

---

## 1. Functionalities

### 1.1 Complete Capability Inventory

| # | Capability | Module | CLI Command | Python API |
|---|-----------|--------|-------------|------------|
| 1 | Protocol validation (structural + cross-field) | validate.py | scholar-protocol validate [path] [--strict] | validate_protocol(path) -> ValidationReport |
| 2 | Deterministic protocol compilation | compiler.py | scholar-protocol compile [intent_path] | compile_protocol(intent) -> ResearchProtocol |
| 3 | Canonical JSON serialization | canonical.py | scholar-protocol canon [path] | canonical_json(protocol) -> bytes |
| 4 | SHA-256 fingerprinting | canonical.py | scholar-protocol fingerprint [path] | canonical_fingerprint(protocol) -> str |
| 5 | Screening criteria rendering | render.py | scholar-protocol render-criteria [path] | render_screening_criteria(protocol) -> str |
| 6 | Dynamic extraction model generation | extraction.py | scholar-protocol extraction-schema [path] | build_extraction_model(protocol) -> Type[BaseModel] |
| 7 | Extraction prompt generation | extraction.py | scholar-protocol extraction-prompt [path] | generate_extraction_prompt(protocol) -> str |
| 8 | Playbook presets | presets.py | (used internally by compiler) | PRESETS dict |
| 9 | Intent packet definition | intent.py | (input to compile) | IntentPacket model |
| 10 | JSON Schema generation | scripts/generate_schema.py | python scripts/generate_schema.py | generate_schema() -> dict |

### 1.2 CLI Command-to-Function Mapping

scholar-protocol validate [path] [--strict]
  -> validate_protocol(path)          [validate.py:284]
  -> report.is_valid / report.is_valid_strict()
  -> Exit 0 (valid), 1 (invalid), 2 (usage error)

scholar-protocol fingerprint [path]
  -> _load_protocol(path)             [cli.py:79]
  -> canonical_fingerprint(protocol)  [canonical.py:132]
  -> print(fp) to stdout

scholar-protocol canon [path]
  -> _load_protocol(path)             [cli.py:79]
  -> canonical_json(protocol)         [canonical.py:96]
  -> sys.stdout.buffer.write(bytes)

scholar-protocol compile [intent_path]
  -> compile_from_file(path)          [compiler.py:243]
  -> canonical_json(protocol)         [canonical.py:96]
  -> sys.stdout.buffer.write(bytes)

scholar-protocol render-criteria [path]
  -> _load_protocol(path)             [cli.py:79]
  -> render_screening_criteria(protocol) [render.py:14]
  -> print(md) to stdout

scholar-protocol extraction-schema [path]
  -> _load_protocol(path)             [cli.py:79]
  -> build_extraction_model(protocol) [extraction.py:17]
  -> model.model_json_schema()
  -> print(json.dumps(schema, indent=2))

scholar-protocol extraction-prompt [path]
  -> _load_protocol(path)             [cli.py:79]
  -> generate_extraction_prompt(protocol) [extraction.py:69]
  -> print(prompt) to stdout

### 1.3 Data Models and Schemas

#### Root Model: ResearchProtocol (models.py:292-351)

ResearchProtocol
  |--  (alias: schema_version) = schemas/v1/protocol.schema.json
  |-- protocol_id: str (required)
  |-- created_at: str (ISO-8601, auto-generated)
  |-- project_slug: str (required)
  |-- playbook_type: PlaybookType (required, enum)
  |-- metadata: Dict[str, Any] (freeform, open)
  |-- epistemology: EpistemologyConfig (required)
  |-- research_questions: List[ResearchQuestion] (min_length=1)
  |-- search_strategy: SearchStrategy (required)
  |-- screening_criteria: ScreeningCriteria (required)
  |-- matrix_dimensions: List[MatrixDimension] (default=[])
  +-- verification: VerificationConfig (default factory)

#### Sub-models:

PlaybookType (models.py:27-44) - 5 archetypes:
- PRISMA_SLR - Exhaustive systematic review
- SCOPING_REVIEW - Broad landscape mapping
- RAPID_EVIDENCE - Time-bounded review (24-72h)
- DESIGN_SCIENCE - Artifact engineering
- STUDENT_DISSERTATION - Pedagogical starter

EpistemologicalParadigm (models.py:46-59) - 4 stances:
- POSITIVIST - Quantitative, generalizable
- INTERPRETIVIST - Qualitative, lived experience
- DESIGN_SCIENCE - Computational artifacts
- PRAGMATIST_MIXED - Mixed methods

DimensionDataType (models.py:62-76) - 4 types:
- FREE_TEXT - Descriptive summary
- NUMERIC - Numbers with units
- CATEGORICAL - Bounded enum
- LIST - Array of items

ResearchQuestion (models.py:83-100):
- id, text, target_facet, synthesis_type (default=Comparative Matrix), required_evidence_type

ConceptCluster (models.py:103-116):
- concept, synonyms (list), boolean_operator (default=OR)

SearchStrategy (models.py:118-147):
- core_concepts (min_length=1), target_databases (4 defaults), date_range, languages, open_access_preferred, target_candidate_pool_size

ScreeningCriterion (models.py:150-164):
- id, criterion, maps_to_rqs (list of RQ refs), reason_category (optional)

ScreeningCriteria (models.py:167-185):
- inclusion (min_length=1), exclusion (min_length=1), two_tier_screening (default=True)

MatrixDimension (models.py:188-228):
- id, name, description, target_section_category (optional), data_type, required, fallback_value

EpistemologyConfig (models.py:231-259):
- primary_paradigm, secondary_paradigm (optional), unit_of_analysis, trustworthiness_framework, epistemological_rationale, incompatible_concepts

VerificationConfig (models.py:262-284):
- retraction_check_required, coi_and_funding_audit_required, reproducibility_das_cas_check, minimum_trust_score_threshold (0.0-10.0)

IntentPacket (intent.py:126-246):
A flattened, minimal representation that the compiler resolves against presets. Key design: IDs for RQs and criteria are auto-generated from declaration order.

### 1.4 Integration Points with Other Kits

| Downstream Kit | Integration | Direction | Data Flow |
|---------------|-------------|-----------|-----------|
| scholar-rag-kit | build_extraction_model() | protocol-kit -> rag-kit | Dynamic Pydantic model for matrix extraction |
| scholar-agent-kit | compile_protocol(), validate_protocol(), render_screening_criteria() | agent-kit -> protocol-kit | MCP tools nexus_protocol_compile/validate/render_criteria |
| scholar-search-kit | Protocol validation | search-kit -> protocol-kit | Validates protocol before search execution |
| scholar-verify-kit | Protocol metadata | verify-kit -> protocol-kit | Reads verification config flags |
| workspace-manager | Protocol file management | workspace-manager -> protocol-kit | Writes protocol.json to workspace |

**Known Issue:** scholar-rag-kit imports scholar_protocol.compiler.build_extraction_model but does NOT declare scholar-protocol-kit as a dependency in its pyproject.toml (documented in docs/kits_surface_matrix.md:354).

---

## 2. Improvements

### 2.1 Code Quality Issues

**[MEDIUM] Untyped metadata field** (models.py:328-336)

metadata: Dict[str, Any] = Field(
    default_factory=lambda: {
        "title": "",
        "lead_researcher": "",
        "target_venue_type": "",
        "timeline_weeks": 4,
    },
    description="Freeform project metadata (title, researcher, venue, timeline)",
)

- Problem: Dict[str, Any] allows any keys/values with no validation
- Impact: Typos in metadata keys silently pass validation; downstream consumers may miss data
- Fix: Create a typed MetadataConfig model with optional fields, or add a validator that checks for expected keys

**[LOW] Unused import in validate.py** (validate.py:179)

import datetime as dt  # imported inside function body

- Problem: datetime is imported at module level (line 15) AND inside _check_cross_field (line 179)
- Impact: Minor code smell; the module-level import is unused
- Fix: Remove the module-level import datetime or consolidate imports

**[MEDIUM] No protocol versioning strategy** (models.py:307-311)

schema_version: str = Field(
    "schemas/v1/protocol.schema.json",
    alias="",
    description="URI of the JSON Schema (relative kit path, resolved locally by the validator)",
)

- Problem: Schema is frozen at v1.0.0 with no migration path for future versions
- Impact: Any schema change requires manual migration; no backward compatibility
- Fix: Add a schema_version field that can be parsed and validated; add migration functions

**[LOW] Extract model naming** (extraction.py:59)

clean_id = protocol.protocol_id.replace("-", "_").title().replace("_", "")
model_name = f"{clean_id}ExtractionRow"

- Problem: The .title().replace("_", "") produces PascalCase but may produce unexpected results for certain protocol IDs
- Impact: Minor; model names appear in JSON Schema output
- Fix: Document the naming convention or use a more predictable transformation

### 2.2 Missing Features or Capabilities

**[HIGH] No --output flag on CLI commands**
- Current: All commands print to stdout; user must redirect
- Impact: Inconvenient for interactive use; no -i/-o flags
- Recommendation: Add optional --output flag to compile, render-criteria, extraction-schema, extraction-prompt commands while keeping stdout as default

**[HIGH] No protocol diff/comparison tool**
- Current: No way to compare two protocol.json files semantically
- Impact: Difficult to track protocol changes across iterations
- Recommendation: Add scholar-protocol diff [path1] [path2] command that shows semantic differences

**[MEDIUM] No protocol summary/statistics command**
- Current: No quick overview of protocol contents
- Impact: Researchers must manually inspect protocol files
- Recommendation: Add scholar-protocol summary [path] that shows RQ count, criterion count, matrix dimensions, etc.

**[MEDIUM] No extraction model validation**
- Current: build_extraction_model() generates models but does not validate they can be used
- Impact: Runtime errors when extraction model is incompatible with RAG system
- Recommendation: Add validate_extraction_model(protocol) that checks field names are valid Python identifiers, no collisions, etc.

**[LOW] No JSON Schema validation of protocol.json against the checked-in schema**
- Current: Validation uses Pydantic models, not the JSON Schema file
- Impact: The JSON Schema file (schemas/v1/protocol.schema.json) is generated but never used for validation
- Recommendation: Optionally validate against the JSON Schema for external tool compatibility

### 2.3 API Design Improvements

**[MEDIUM] validate_protocol() requires file path, not dict** (validate.py:284)

def validate_protocol(path: str | pathlib.Path) -> ValidationReport:

- Problem: Cannot validate an in-memory protocol dict without writing to disk first
- Impact: Test code must use tempfile.NamedTemporaryFile (see test_validate.py:19-26)
- Recommendation: Add overload: validate_protocol(path: str | Path) and validate_protocol(data: dict)

**[MEDIUM] No protocol serialization to YAML/TOML** (canonical.py)
- Current: Only JSON serialization
- Impact: Some users prefer YAML for readability
- Recommendation: Add canonical_yaml(protocol) and canonical_toml(protocol) functions

**[LOW] No protocol deserialization from canonical bytes** (canonical.py)
- Current: canonical_json(protocol) -> bytes exists but no reverse
- Impact: Cannot round-trip from canonical bytes back to protocol object
- Recommendation: Add protocol_from_canonical(bytes) -> ResearchProtocol

### 2.4 Error Handling Gaps

**[HIGH] No validation of target_databases values** (validate.py)
- Current: target_databases accepts any string values
- Impact: Typos like openalexx pass validation silently
- Recommendation: Add a validator that checks against known database names (openalex, semanticscholar, crossref, arxiv, etc.)

**[MEDIUM] No validation of languages format** (validate.py:217-223)

if not protocol.search_strategy.languages:
    report.add_error(...)

- Problem: Only checks non-empty; does not validate ISO 639-1 format
- Impact: Invalid language codes like english or eng pass validation
- Recommendation: Add regex or enum validation for ISO 639-1 codes

**[MEDIUM] No validation of created_at format** (models.py:316-319)

created_at: str = Field(
    default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
    description="ISO-8601 timestamp of protocol creation (UTC)",
)

- Problem: created_at is typed as str with no ISO-8601 validation
- Impact: Invalid timestamps like not-a-date pass validation
- Recommendation: Add a Pydantic validator or use datetime type with JSON serialization

**[MEDIUM] No validation of protocol_id format** (models.py:312-315)
- Problem: protocol_id accepts any string
- Impact: Spaces, special characters, or extremely long IDs pass validation
- Recommendation: Add regex pattern validation (e.g., ^[a-z0-9][a-z0-9-]*$)

**[LOW] No validation of concept length** (models.py:108)
- Problem: concept accepts empty strings
- Impact: Empty concept clusters may cause downstream search failures
- Recommendation: Add min_length=1 to concept field

### 2.5 Documentation Needs

**[HIGH] Missing CHANGELOG**
- Problem: No CHANGELOG.md to track version changes
- Impact: Users cannot easily understand what changed between versions
- Recommendation: Create CHANGELOG.md following Keep a Changelog format

**[MEDIUM] Missing API reference documentation**
- Problem: README.md shows examples but no complete API reference
- Impact: Developers must read source code to understand all parameters
- Recommendation: Generate API docs with Sphinx or mkdocstrings

**[MEDIUM] No architecture decision records (ADRs)**
- Problem: Design decisions (e.g., why canonical serialization works this way) are not documented
- Impact: New contributors cannot understand the rationale
- Recommendation: Create ADRs for key design decisions

---

## 3. Problems

### 3.1 Known Bugs or Issues

**[HIGH] date_range missing key validation** (validate.py:178-198)

dr = protocol.search_strategy.date_range
start = dr.get("start_year")
end = dr.get("end_year")
if start is not None and end is not None:
    if start > end:
        ...

- Problem: If date_range is missing start_year or end_year, validation passes silently
- Impact: Incomplete date ranges may cause search failures
- Fix: Add validation that both keys exist when date_range is provided

**[MEDIUM] target_candidate_pool_size missing key validation** (validate.py:200-215)

pool = protocol.search_strategy.target_candidate_pool_size
p_min = pool.get("min", 0)
p_max = pool.get("max", 0)

- Problem: Uses .get("min", 0) which silently defaults to 0 if key is missing
- Impact: Missing keys are treated as 0, which may not be intended
- Fix: Add validation that both min and max keys exist

**[MEDIUM] _check_cross_field imports inside function body** (validate.py:179, 239)

import datetime as dt  # line 179
from scholar_protocol.models import EpistemologicalParadigm, PlaybookType  # line 239

- Problem: These imports are inside the function body, executed on every call
- Impact: Minor performance overhead; code smell
- Fix: Move imports to module level

**[LOW] Temp file cleanup in tests** (test_validate.py:19-26)

def _write_tmp(data: dict) -> pathlib.Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, f, ensure_ascii=True)
    f.close()
    return pathlib.Path(f.name)

- Problem: Temp files are created with delete=False but never cleaned up
- Impact: Temp file accumulation on repeated test runs
- Fix: Add cleanup in test fixtures or use tmp_path pytest fixture

### 3.2 Edge Cases Not Handled

**[HIGH] Empty core_concepts.synonyms list** (models.py:109)

synonyms: List[str] = Field(
    default_factory=list,
    description="Alternative keyword synonyms (author order preserved)",
)

- Problem: Empty synonyms list is valid; may cause search query generation failures
- Impact: Downstream search kits may not handle empty synonym lists
- Fix: Add warning when synonyms list is empty

**[MEDIUM] target_section_category values not validated** (models.py:210-216)

target_section_category: Optional[str] = Field(
    None,
    description=(
        "Preferred source section: 'methodology', 'results_empirical', "
        "'discussion_limitations', or 'abstract_intro'.  Null = search all sections."
    ),
)

- Problem: Description lists valid values but no enum validation
- Impact: Invalid section categories pass validation
- Fix: Create TargetSectionCategory enum or add validator

**[MEDIUM] reason_category not validated** (models.py:163)

reason_category: Optional[str] = Field(
    None,
    description="Optional rejection category e.g. 'WRONG_POPULATION', 'WRONG_OUTCOME'",
)

- Problem: No validation of reason category format
- Impact: Inconsistent reason categories across protocols
- Fix: Add enum or pattern validation for common categories

**[LOW] boolean_operator not validated to OR/AND** (models.py:113-115)

boolean_operator: str = Field(
    "OR", description="Operator joining synonyms: 'OR' or 'AND'"
)

- Problem: Description says OR or AND but no enum validation
- Impact: Invalid operators like XOR pass validation
- Fix: Change to Literal[OR, AND] or add enum

**[LOW] minimum_trust_score_threshold precision** (models.py:279-284)
- Problem: Threshold accepts any float (e.g., 5.123456789)
- Impact: Canonical serialization may produce unexpected precision
- Fix: Round to 1 decimal place in validator

### 3.3 Limitations in Current Implementation

**[HIGH] No support for protocol inheritance or templating**
- Current: Each protocol is standalone; no way to base one protocol on another
- Impact: Common sections must be duplicated across protocols
- Recommendation: Add protocol templates or inheritance mechanism

**[MEDIUM] No support for multi-language protocols**
- Current: languages field is just a list of codes; no language-specific content
- Impact: Cannot create protocols with content in multiple languages
- Recommendation: Add language-tagged content fields

**[MEDIUM] No support for protocol revisions**
- Current: Protocol is immutable after compilation
- Impact: Cannot track protocol changes over time
- Recommendation: Add revision history or version tracking

**[LOW] No support for protocol comparison/merging**
- Current: No way to compare or merge two protocols
- Impact: Cannot combine protocols from different researchers
- Recommendation: Add protocol diff and merge operations

### 3.4 Technical Debt

**[MEDIUM] Hardcoded preset values** (presets.py:69-144)
- Problem: All preset values are hardcoded in Python; not configurable
- Impact: Adding new presets requires code changes
- Recommendation: Load presets from JSON/YAML files

**[MEDIUM] No plugin architecture for custom validators** (validate.py)
- Problem: Cross-field rules are hardcoded in _check_cross_field()
- Impact: Cannot add custom validation rules without modifying source
- Recommendation: Add validator plugin system

**[LOW] Test fixtures not parameterized for all edge cases** (tests/test_validate.py)
- Problem: Some edge cases are tested inline rather than as parameterized fixtures
- Impact: Inconsistent test coverage
- Recommendation: Convert all edge cases to parameterized fixtures

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

**[LOW] Repeated imports in _check_cross_field** (validate.py:179, 239)

import datetime as dt  # line 179
from scholar_protocol.models import EpistemologicalParadigm, PlaybookType  # line 239

- Problem: Imports executed on every validation call
- Impact: ~0.1ms overhead per validation
- Fix: Move to module level

**[LOW] Redundant model_dump() calls in compiler** (compiler.py:233-238)

"epistemology": epistemology.model_dump(mode="json"),
"research_questions": [rq.model_dump(mode="json") for rq in _build_rqs(intent)],
"search_strategy": search_strategy.model_dump(mode="json"),
"screening_criteria": screening_criteria.model_dump(mode="json"),
"matrix_dimensions": [d.model_dump(mode="json") for d in _build_dimensions(intent)],
"verification": verification.model_dump(mode="json"),

- Problem: Each sub-model is dumped separately, then the whole dict is validated again
- Impact: Minor performance overhead for large protocols
- Optimization: Pass model objects directly to ResearchProtocol constructor

### 4.2 Memory Usage Issues

**[LOW] Large protocol fixtures in tests** (tests/fixtures/valid/prisma_slr_full.json)
- Problem: Full protocol fixtures are loaded into memory during tests
- Impact: ~10KB per fixture; 4 fixtures = ~40KB total
- Acceptable: This is well within normal test memory usage

### 4.3 Algorithm Efficiency

**[MEDIUM] Canonical serialization key sorting** (canonical.py:62-78)

if "metadata" in raw and isinstance(raw["metadata"], dict):
    raw["metadata"] = dict(sorted(raw["metadata"].items()))

- Problem: Sorting is O(n log n) for each nested dict
- Impact: Negligible for small dicts; could matter for very large metadata
- Optimization: Cache sorted results or use ordered dict from start

### 4.4 Caching Opportunities

**[MEDIUM] Schema generation caching** (scripts/generate_schema.py:92-118)
- Problem: generate_schema() regenerates schema on every call
- Impact: ~5ms per call; repeated in tests
- Recommendation: Cache generated schema in module-level variable

**[LOW] Fingerprint caching** (canonical.py:132-146)
- Problem: canonical_fingerprint() recomputes canonical JSON on every call
- Impact: ~1ms per call
- Recommendation: Cache fingerprint on ResearchProtocol instance (use functools.lru_cache or __hash__)

### 4.5 Parallelization Potential

**[LOW] Test execution** (tests/)
- Problem: Tests are run sequentially
- Impact: ~2s total test time
- Recommendation: Use pytest-xdist for parallel test execution (already available in dev dependencies)

---

## 5. Scientific Correction

### 5.1 Accuracy of Protocol Schema

**[HIGH] Missing PRISMA 2020 flow diagram support**
- Current: Protocol captures screening criteria but not the PRISMA flow diagram structure
- Impact: Researchers must manually create PRISMA flow diagrams
- Recommendation: Add optional prisma_flow field with diagram metadata

**[MEDIUM] No support for PICO/PICOS framework** (models.py:83-100)
- Current: Research questions are freeform text
- Impact: Cannot enforce structured PICO (Population, Intervention, Comparison, Outcome, Study design) format
- Recommendation: Add optional pico field to ResearchQuestion model

**[MEDIUM] No support for GRADE evidence certainty** (models.py:262-284)
- Current: VerificationConfig has trust score but no GRADE framework
- Impact: Cannot assess evidence certainty using GRADE methodology
- Recommendation: Add optional grade_assessment field

### 5.2 Alignment with Research Methodology Standards

**[HIGH] PRISMA 2020 compliance gaps**
- Current: ScreeningCriteria has two_tier_screening flag but no PRISMA-specific fields
- Missing:
  - prisma_flow_eligibility_criteria (PRISMA-S specific)
  - prisma_flow_information_sources
  - prisma_flow_selection_process
  - prisma_flow_data_extraction
- Impact: Researchers must supplement protocol with PRISMA-specific documentation
- Recommendation: Add optional prisma_config field

**[MEDIUM] No support for ROBIS (Risk of Bias in Systematic Reviews)**
- Current: VerificationConfig has basic flags but no structured ROBIS assessment
- Impact: Cannot systematically assess risk of bias using ROBIS tool
- Recommendation: Add optional robis_domains field

**[MEDIUM] No support for CASP (Critical Appraisal Skills Programme) checklists**
- Current: No study design-specific appraisal checklists
- Impact: Cannot enforce study design-specific quality assessment
- Recommendation: Add optional casp_checklist_type field

### 5.3 Correctness of Validation Rules

**[HIGH] date_range validation is incomplete** (validate.py:178-198)
- Current: Validates start_year <= end_year and year bounds
- Missing:
  - Validation that both keys exist when date_range is provided
  - Validation that years are integers (not floats or strings)
- Impact: Invalid date ranges may pass validation
- Fix: Add explicit key existence check

**[MEDIUM] target_candidate_pool_size validation is incomplete** (validate.py:200-215)
- Current: Validates min <= max and non-negative
- Missing:
  - Validation that both keys exist
  - Validation that values are integers (not floats)
- Impact: Invalid pool sizes may pass validation
- Fix: Add explicit key existence check

**[MEDIUM] No validation of synthesis_type values** (models.py:93-96)
- Current: synthesis_type accepts any string
- Impact: Inconsistent synthesis types across protocols
- Recommendation: Add enum validation (e.g., Comparative Matrix, Taxonomy, Narrative, Meta-Analysis)

**[LOW] No validation of required_evidence_type values** (models.py:97-100)
- Current: required_evidence_type accepts any string
- Impact: Inconsistent evidence types across protocols
- Recommendation: Add enum validation for common evidence types

### 5.4 Epistemological Paradigm Handling

**[HIGH] Limited paradigm options** (models.py:46-59)
- Current: 4 paradigms (Positivist, Interpretivist, Design Science, Pragmatist/Mixed)
- Missing:
  - Critical Theory
  - Constructivist
  - Post-positivist
  - Participatory/Action Research
- Impact: Researchers with other epistemological stances cannot accurately represent their work
- Recommendation: Add more paradigm options or allow custom paradigms

**[MEDIUM] No paradigm validation against methodology** (validate.py:236-251)
- Current: Only warns on questionable paradigm-playbook combinations
- Missing:
  - Validation that paradigm matches methodology (e.g., Positivist should use quantitative methods)
  - Validation that unit_of_analysis is appropriate for paradigm
- Impact: Epistemologically inconsistent protocols may pass validation
- Recommendation: Add paradigm-methodology coherence checks

**[MEDIUM] incompatible_concepts is freeform** (models.py:256-259)
- Current: No validation of what constitutes an incompatible concept
- Impact: Researchers may list concepts that are not actually incompatible
- Recommendation: Add guidance or validation for incompatible concept lists
## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent or Skill Be Created?

**Recommendation: YES -- Create a specialized protocol-qa-agent skill**

The scholar-protocol-kit already has a SKILL.md (.agents/skills/scholar-protocol-kit/SKILL.md), but it is a passive instruction document. A specialized agent (not just a skill) would add significant value because:

1. **Protocol quality is a critical gate** -- A bad protocol cascades errors through the entire research pipeline (search, screening, extraction, synthesis).
2. **Subjective assessment needed** -- Many protocol quality issues (e.g., Is this research question answerable? Are these criteria comprehensive?) require judgment, not just rule-based validation.
3. **Agent-in-the-loop opportunity** -- The inception wizard already uses LLM interaction; a QA agent could validate the wizard's output before compilation.

### 6.2 Narrow Scope of Tasks

| Task | Description | Frequency |
|------|-------------|-----------|
| Protocol Completeness Check | Verify all required fields are meaningful (not just present) | Every protocol |
| Research Question Quality | Assess RQs for clarity, answerability, scope | Every protocol |
| Criterion Coverage Analysis | Check that criteria comprehensively cover all RQs | Every protocol |
| Search Strategy Adequacy | Evaluate concept clusters for completeness | Every protocol |
| Paradigm-Methodology Coherence | Verify epistemological consistency | Every protocol |
| Extraction Dimension Validity | Check matrix dimensions are extractable and meaningful | When dimensions defined |
| Cross-Protocol Comparison | Compare two protocol versions for meaningful changes | On revision |

### 6.3 Evaluation Metrics for Agent Performance

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| Completeness Score | % of protocol fields that pass quality checks | > 90% | Automated + LLM assessment |
| RQ Quality Score | Average RQ clarity rating (1-5) from LLM judge | > 4.0 | LLM-based rubric scoring |
| Criterion Coverage Ratio | % of RQs covered by at least one criterion | 100% | Automated |
| Search Recall Estimate | Estimated % of relevant papers captured | > 80% | LLM-based estimation |
| Paradigm Coherence Score | Binary: paradigm-methodology-consistent | 100% | Rule-based + LLM |
| False Positive Rate | % of QA warnings that are incorrect | < 5% | Human evaluation |
| False Negative Rate | % of real issues missed by QA | < 10% | Human evaluation |
| Response Time | Time to complete QA assessment | < 30s | Automated |

### 6.4 Critic Capabilities Needed

The agent should be able to:

1. **Detect common protocol anti-patterns:** Overly broad RQs, vague criteria, missing exclusion criteria, inconsistent terminology
2. **Suggest improvements:** Recommend additional criteria, refine vague criteria, propose search concepts, identify biases
3. **Validate against methodology standards:** PRISMA compliance, PICO structure, DSR methodology alignment
4. **Cross-reference with domain knowledge:** Concept appropriateness, standard exclusion criteria, missing verification steps

### 6.5 Agent-in-the-Loop Opportunities

| Loop Point | Agent Role | Trigger | Output |
|-----------|-----------|---------|--------|
| Post-Inception | Validate wizard output before compilation | After Socratic interview | QA report with pass/fail + suggestions |
| Pre-Search | Validate protocol before search execution | Before scholar-search runs | Search readiness assessment |
| Post-Screening | Validate screening decisions against protocol | After batch screening | Protocol adherence report |
| Pre-Extraction | Validate extraction dimensions for completeness | Before RAG extraction | Extraction readiness assessment |
| Post-Synthesis | Validate synthesis against original RQs | After synthesis completes | RQ coverage report |

### 6.6 Automation Potential

| Task | Current State | Automation Potential |
|------|--------------|---------------------|
| Schema validation | Fully automated | Already done |
| Cross-field validation | Fully automated | Already done |
| RQ quality assessment | Manual | HIGH -- LLM-based rubric scoring |
| Criterion coverage analysis | Manual | HIGH -- Automated graph analysis |
| Search adequacy assessment | Manual | MEDIUM -- LLM + heuristics |
| Paradigm coherence check | Semi-automated (warning only) | HIGH -- Rule-based + LLM |
| Protocol comparison | Manual | HIGH -- Diff + semantic analysis |


---

## 7. Priority-Ranked Improvement Suggestions

### Priority 1 (Critical -- Fix Immediately)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 1 | Add date_range key existence validation | validate.py:178-198 | High | Low |
| 2 | Add target_candidate_pool_size key existence validation | validate.py:200-215 | High | Low |
| 3 | Add created_at ISO-8601 format validation | models.py:316-319 | High | Low |
| 4 | Add protocol_id format validation | models.py:312-315 | Medium | Low |

### Priority 2 (High -- Fix Soon)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 5 | Add target_databases value validation | validate.py | High | Medium |
| 6 | Add languages ISO 639-1 validation | validate.py:217-223 | Medium | Medium |
| 7 | Add target_section_category enum validation | models.py:210-216 | Medium | Low |
| 8 | Add boolean_operator Literal validation | models.py:113-115 | Low | Low |
| 9 | Add validate_protocol(dict) overload | validate.py:284 | Medium | Medium |
| 10 | Add --output flag to CLI commands | cli.py | Medium | Medium |

### Priority 3 (Medium -- Plan for Next Release)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 11 | Add protocol versioning/migration strategy | models.py:307-311 | High | High |
| 12 | Add CHANGELOG.md | root | Medium | Low |
| 13 | Add protocol diff command | cli.py | Medium | Medium |
| 14 | Add protocol summary command | cli.py | Low | Low |
| 15 | Add PRISMA 2020 flow diagram support | models.py | Medium | High |
| 16 | Add PICO framework support | models.py:83-100 | Medium | High |
| 17 | Create protocol-qa-agent skill | .agents/skills/ | High | High |

### Priority 4 (Low -- Backlog)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 18 | Add YAML/TOML serialization | canonical.py | Low | Medium |
| 19 | Add extraction model validation | extraction.py | Low | Medium |
| 20 | Add protocol inheritance/templating | models.py | Low | High |
| 21 | Add ROBIS/CASP support | models.py | Low | High |
| 22 | Add more epistemological paradigms | models.py:46-59 | Low | Low |
| 23 | Add synthesis_type enum validation | models.py:93-96 | Low | Low |
| 24 | Move presets to JSON/YAML config | presets.py | Low | Medium |
| 25 | Add validator plugin system | validate.py | Low | High |

---

## Appendix A: File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| src/scholar_protocol/__init__.py | 75 | Public API re-exports |
| src/scholar_protocol/models.py | 351 | Pydantic v2 models (sole source of truth) |
| src/scholar_protocol/canonical.py | 146 | Deterministic serializer + sha256 fingerprint |
| src/scholar_protocol/validate.py | 324 | Structural + cross-field validation |
| src/scholar_protocol/compiler.py | 256 | IntentPacket to ResearchProtocol compiler |
| src/scholar_protocol/render.py | 89 | Markdown criteria renderer |
| src/scholar_protocol/extraction.py | 98 | Dynamic Pydantic schema synthesis |
| src/scholar_protocol/presets.py | 145 | Playbook presets |
| src/scholar_protocol/intent.py | 246 | IntentPacket model |
| src/scholar_protocol/cli.py | 248 | Typer + Rich CLI |
| scripts/generate_schema.py | 176 | JSON Schema generator |
| schemas/v1/protocol.schema.json | 483 | Checked-in JSON Schema |
| tests/test_validate.py | 267 | Validation tests |
| tests/test_models.py | 211 | Model parsing tests |
| tests/test_canonical.py | 306 | Canonical serialization tests |
| tests/test_compiler.py | 240 | Compiler conformance tests |
| tests/test_cli.py | 261 | CLI exit code tests |
| tests/test_schema_sync.py | 179 | Schema sync CI guard |

**Total source lines:** ~1,788 (src/) + ~1,244 (tests/) + ~176 (scripts/) = ~3,208 lines

## Appendix B: Test Coverage Summary

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| test_validate.py | 18 | Validation rules, error codes, warnings |
| test_models.py | 16 | Model parsing, enums, bounds, defaults |
| test_canonical.py | 14 | Serialization determinism, fingerprinting |
| test_compiler.py | 12 | Compiler conformance, preset application |
| test_cli.py | 16 | CLI exit codes, output format |
| test_schema_sync.py | 7 | Schema-model synchronization |

**Total tests:** 83 test functions across 6 test files

---

*Analysis complete. Generated: 2026-09-14*


---

<!-- Source: kit_02_search.md -->
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

---

<!-- Source: kit_03_pdf.md -->
# Scholar PDF Kit — Comprehensive Deep-Dive Analysis

**Kit**: scholar-pdf-kit (v0.1.0)
**Location**: C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-pdf-kit
**Analysis Date**: 2026-09-14
**Analyst**: Automated Deep-Dive

---

## Executive Summary

Scholar PDF Kit is a well-structured, async-first toolkit for discovering, downloading, validating, and extracting content from Open Access academic PDFs. It resolves DOIs through a multi-source cascade (OpenAlex → Unpaywall → publisher direct patterns → institutional proxy), validates downloaded files via binary signature analysis, and converts PDFs to structured Markdown with YAML frontmatter for downstream RAG indexing.

**Overall Maturity**: Beta (v0.1.0) — functional core with several design gaps, integration rough edges, and technical debt.

**Key Strengths**:
- Robust 3-attempt download cascade with publisher-specific bypass patterns
- Strict binary validation (magic bytes + size floor + EOF trailer)
- Well-tested publisher pattern rewriting (IEEE, Elsevier, Springer, arXiv, MDPI)
- Clean async architecture with configurable concurrency

**Key Weaknesses**:
- PyMuPDF extraction silently swallows all errors (fallback to stub line)
- pyyaml is an undeclared transitive dependency
- models.py (OAResult/OALocation) is defined but never used in the actual download pipeline
- BibTeX export produces malformed entries (missing braces, no escaping)
- No retry/resilience for metadata fetching (OpenAlex/Unpaywall)
- CLI extract command does not support --engine pymupdf (API-only)

---

## 1. Functionalities

### 1.1 Core Capabilities

| Capability | Status | Implementation |
|:--|:--|:--|
| DOI ? PDF resolution (OpenAlex) | Working | downloader.py:125-133 |
| DOI ? PDF fallback (Unpaywall) | Working | downloader.py:135-143 |
| Publisher direct-PDF patterns | Working | publisher_patterns.py:62-100 |
| Institutional proxy rewriting | Working | publisher_patterns.py:199-226 |
| Async concurrent downloads | Working | downloader.py:242-248 |
| Binary PDF validation | Working | alidator.py:20-49 |
| Structural PDF validation (pypdf) | Working | alidator.py:52-79 |
| Smart filename generation | Working | downloader.py:56-70 |
| PDF ? Markdown extraction (PyMuPDF) | Partial | extract.py:16-92 (error swallowing) |
| PDF ? Markdown extraction (Docling) | Working | extract.py:95-112 |
| PDF ? TEI XML extraction (Grobid) | Working | extract.py:115-136 |
| Manual PDF ingestion | Working | downloader.py:250-287 |
| JSON/BibTeX metadata export | Partial | cli.py:33-80 (malformed BibTeX) |
| YAML frontmatter injection | Working | extract.py:30-43 |

### 1.2 CLI Commands ? Functions Mapping

| CLI Command | Function | File:Line |
|:--|:--|:--|
| scholar-pdf download | cli.download() | cli.py:82-185 |
| scholar-pdf ingest | cli.ingest() | cli.py:187-224 |
| scholar-pdf extract | cli.extract() | cli.py:226-276 |

**Download sub-flow**:
`
cli.download()
  ? AsyncPDFDownloader.process_doi()
    ? fetch_openalex_metadata()  [downloader.py:125]
    ? fetch_unpaywall_metadata() [downloader.py:135]  (fallback)
    ? download_pdf()             [downloader.py:78]
    ? resolve_doi_to_publisher_pdf()  [publisher_patterns.py:62]  (attempt 2)
    ? compute_direct_pdf_from_landing_url()  [publisher_patterns.py:103]  (attempt 2)
    ? rewrite_via_proxy()        [publisher_patterns.py:199]  (attempt 3)
    ? clean_invalid_pdf()        [validator.py:82]
`

### 1.3 Data Models and Schemas

**DownloadResult** (downloader.py:26-33):
`python
@dataclass
class DownloadResult:
    doi: str
    success: bool
    file_path: Path | None = None
    error_message: str | None = None
    was_oa: bool = False
    metadata: dict | None = None
`

**OAResult / OALocation** (models.py:4-50):
- Pydantic v2 models mirroring Unpaywall/OpenAlex schema
- **DEAD CODE**: Never imported or used by the actual download pipeline (downloader.py works with raw dicts)
- est_pdf_url property exists but is never called

**Settings** (config.py:6-36):
- Pydantic-settings based configuration
- Environment variables: MAILTO, DOWNLOAD_DIR, MAX_CONCURRENT_DOWNLOADS, DOWNLOAD_TIMEOUT, PROXY_URL, PROXY_STYLE, PDF_STRUCTURAL_VALIDATION, ENABLE_PUBLISHER_DIRECT_PATTERNS

### 1.4 Integration Points with Other Kits

| Integration | Direction | Mechanism | Status |
|:--|:--|:--|:--|
| scholar-search-kit | PDF ? Search | AcademicHttpClient for metadata fetching | Working (hard dep) |
| scholar-search-kit | Search ? PDF | included.json / 
esults.json input parsing | Working |
| scholar-rag-kit | PDF ? RAG | Markdown extraction ? vector indexing | Working (via frontmatter) |
| scholar-agent-kit (MCP) | Agent ? PDF | 
exus_extract_pdf tool | Working (metadata dropping fixed) |
| scholar-harness | Orchestrator ? PDF | PyMuPDFEngine import in orchestrator | Working |
| scholar-bib-kit | PDF ? Bib | BibTeX export | Broken (malformed output) |

### 1.5 Extraction Engines

| Engine | File | Output | Dependencies | Error Handling |
|:--|:--|:--|:--|:--|
| **PyMuPDFEngine** | extract.py:16-92 | .md with YAML frontmatter | itz (PyMuPDF) | **Swallows all exceptions** ? stub line |
| **DoclingEngine** | extract.py:95-112 | .md (structured) | docling (optional) | Falls back to PyMuPDF on failure |
| **GrobidEngine** | extract.py:115-136 | .tei.xml (TEI XML) | 
equests (sync) | Raises RuntimeError on HTTP failure |

**Publisher Direct-PDF Patterns** (publisher_patterns.py:28-59):
| Publisher | DOI Prefix | Direct PDF URL Template |
|:--|:--|:--|
| IEEE | 10.1109/ | ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={suffix} |
| Elsevier | 10.1016/ | sciencedirect.com/science/article/pii/{pii}/pdfft?... |
| MDPI | 10.3390/ | mdpi.com/{path}/pdf |
| Springer | 10.1007/ or 10.1140/ | link.springer.com/content/pdf/{doi}.pdf |
| arXiv | 10.48550/ | rxiv.org/pdf/{arxiv_id}.pdf |

---

## 2. Improvements

### 2.1 Code Quality Issues

#### Critical: PyMuPDF Error Swallowing
**File**: extract.py:85-87
`python
except Exception:
    # Fallback simple text reader
    md_lines.append(f"Extracted content from {pdf_path.name}")
`
This catches **all** exceptions (including KeyboardInterrupt via bare Exception) and produces a stub line instead of the actual content. The output file will contain valid YAML frontmatter but no content, making it appear successful. Downstream RAG indexing will silently index empty documents.

**Recommendation**: Log the exception, propagate a warning, and consider raising or returning a structured error.

#### Malformed BibTeX Export
**File**: cli.py:63-77
`python
bibtex = f"@article{{{key},\n  title={{{title}}},\n  author={{{author}}},\n  year={{{year}}},\n  doi={{{res.doi}}}\n}}\n"
`
Issues:
1. BibTeX values are not brace-wrapped properly (missing outer braces for title/author)
2. No escaping of special characters (&, %, #, _) in titles/authors
3. key generation ("{author}{year}") can produce duplicate keys for multi-author papers
4. No journal field included despite metadata being available

#### Dead Code: OAResult/OALocation Models
**File**: models.py:1-50
The Pydantic models OAResult and OALocation are defined and exported in __init__.py but never used by the download pipeline. The downloader works with raw dicts from API responses. This creates confusion about the canonical data shape.

#### Inconsistent User-Agent
**File**: downloader.py:81
`python
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."
`
The docs (
esolution-and-download.md:22) claim the UA is scholar-pdf-kit/0.1.0 (mailto:{mailto}) but the code uses a Chrome browser UA. This discrepancy violates polite crawling guidelines and could trigger bot detection.

#### Missing pyyaml Dependency
**File**: extract.py:26
yaml is imported inside PyMuPDFEngine.extract_markdown() but pyyaml is not declared in pyproject.toml dependencies. It works only because pyyaml is a transitive dependency of other packages.

### 2.2 Missing Features

1. **No --engine pymupdf in CLI**: The extract CLI only accepts docling or grobid (cli.py:230). PyMuPDF extraction is API/MCP only. This is documented but unintuitive.

2. **No incremental/retry download**: If a batch download partially fails, there is no --resume or --retry-failed flag. Users must re-run the entire batch.

3. **No download manifest**: Failed downloads are reported in the terminal table but not persisted to a file for later retry.

4. **No PDF page count/quality metrics**: No validation of whether the downloaded PDF is actually readable (e.g., scanned image-only PDFs vs. text PDFs).

5. **No rate limiting for Unpaywall**: OpenAlex is rate-limited via AcademicHttpClient, but Unpaywall requests have no explicit rate limiting.

6. **No proxy authentication**: The proxy system supports URL-based proxies but not SOCKS5 or authenticated proxies.

### 2.3 API Design Improvements

1. **DownloadResult should be a Pydantic model** (currently a dataclass) for consistency with OAResult and JSON serialization.

2. **extract_markdown() should return a structured result** (not just a Path) including metadata about what was extracted, page count, word count, etc.

3. **AsyncPDFDownloader constructor** should accept an optional http_client parameter instead of always creating one internally (for testability and shared client reuse).

4. **Publisher patterns should be extensible** — currently hardcoded in _PUBLISHER_PATTERNS. A plugin system or config-based pattern registry would improve maintainability.

### 2.4 Error Handling Gaps

1. **etch_openalex_metadata** (downloader.py:125-133): Silently returns None on any exception. No logging, no differentiation between 404 (DOI not found) and 500 (server error).

2. **etch_unpaywall_metadata** (downloader.py:135-143): Same silent failure pattern. Unpaywall has rate limits (10K requests/day for free tier) that are not managed.

3. **download_pdf** (downloader.py:78-123): Cleans up the file on exception but does not log the failure reason before re-raising.

4. **process_doi** (downloader.py:163-240): The outer try/except catches all exceptions and wraps them in DownloadResult, losing the traceback.

5. **GrobidEngine.extract_markdown** (extract.py:117-136): Uses synchronous 
equests in an otherwise async toolkit. No retry logic for Grobid server timeouts.

### 2.5 Documentation Needs

1. **
esolution-and-download.md:30-36**: Shows outdated 5-byte magic check (.read(5) == b"%PDF-") — the actual validator is much more sophisticated (1024-byte header scan + 8KB trailer scan + 10KB size floor).

2. **No changelog or version history** — impossible to track what changed between releases.

3. **No architecture diagram** in the kit's own docs (only in pipeline-integration.md as a high-level flow).

4. **Missing API docs for publishers_patterns.py** — the proxy rewriting system is complex but only documented in SKILL.md.

---

## 3. Problems

### 3.1 Known Bugs

#### Bug 1: CLI Extract Does Not Support PyMuPDF
**File**: cli.py:230
`python
engine: str = typer.Option("docling", help="Extraction engine: docling or grobid"),
`
The CLI default is docling but the help says "docling or grobid". If a user passes --engine pymupdf, it falls through to the else branch and exits with error. This is inconsistent with the MCP tool which defaults to pymupdf.

#### Bug 2: BibTeX Key Collisions
**File**: cli.py:72
`python
key = f"{author}{year}".replace(" ", "")
`
Multiple papers by the same first author in the same year produce identical BibTeX keys, causing silent overwrites.

#### Bug 3: Smart Filename Truncation Lossy
**File**: downloader.py:65
`python
safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (" ", "_")).replace(" ", "_")
`
Titles with special characters (e.g., "C++", "Node.js", "C#") lose meaningful content. Two different papers with titles that truncate to the same 50 chars will collide.

#### Bug 4: GrobidEngine Returns .tei.xml Not .md
**File**: extract.py:134-135
`python
out_xml = output_dir / f"{pdf_path.stem}.tei.xml"
out_xml.write_bytes(tei_xml)
return out_xml
`
The function is named extract_markdown but returns TEI XML. The CLI prints "Extracted {name} -> {out}" which is fine, but calling code expecting Markdown will get XML.

### 3.2 Edge Cases Not Handled

1. **DOIs with URL encoding**: 10.1007%2Fs11263-023-01798-x (percent-encoded slash) is not normalized before API queries.

2. **Retracted papers**: No check for retraction status before downloading. The kit will happily download retracted PDFs.

3. **Empty/metadata-only PDFs**: Downloaded PDFs that are valid but contain only a cover page or metadata page pass validation but have no useful content.

4. **Concurrent file writes**: If two processes download the same DOI simultaneously, the dest_path.exists() check (downloader.py:193) has a TOCTOU race condition.

5. **Very large PDFs**: No size limit on downloads. A malicious or broken endpoint could serve a multi-GB file.

6. **Non-DOI inputs**: The --input JSON parser (cli.py:106-116) only handles external_ids.doi and doi fields. Other identifier types (PMID, ArXiv ID) are ignored.

### 3.3 Limitations

1. **5 publishers covered**: IEEE, Elsevier, MDPI, Springer, arXiv. Missing: ACM, Wiley, Taylor & Francis, SAGE, ACS, APS, IOP, etc.

2. **Single-author metadata**: extract_metadata() (downloader.py:145-161) only extracts the first author's last name. Multi-author papers lose author information.

3. **No full-text search within PDFs**: Cannot search inside downloaded PDFs for specific content.

4. **Synchronous Grobid**: The Grobid engine uses blocking 
equests calls, breaking the async architecture.

### 3.4 Technical Debt

1. **models.py dead code**: The OAResult/OALocation models are exported but unused. Either integrate them into the pipeline or remove them.

2. **Duplicate MIN_PDF_SIZE_BYTES**: Defined in both alidator.py:8 and publisher_patterns.py:19 with the same value (10KB). The one in publisher_patterns.py is exported but the validator uses its own copy.

3. **Global mutable settings**: config.py:39 creates a module-level settings instance that is mutated by CLI commands (cli.py:98-99). This is not thread-safe and makes testing harder.

4. **No type stubs or py.typed marker**: The package does not declare type information for downstream consumers.

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

#### Bottleneck 1: Sequential Metadata Fetching
**File**: downloader.py:166-185
`python
data = await self.fetch_openalex_metadata(http_client, doi)
# ...
if not pdf_url:
    unpaywall_data = await self.fetch_unpaywall_metadata(http_client, doi)
`
Metadata fetching is sequential: OpenAlex is tried first, then Unpaywall as fallback. For DOIs where OpenAlex returns no PDF URL, this doubles the latency. Could be parallelized with syncio.gather().

#### Bottleneck 2: Synchronous File I/O in Download
**File**: downloader.py:102-104
`python
with open(dest_path, "wb") as f:
    async for chunk in response.content.iter_chunked(8192):
        f.write(chunk)
`
The file write is synchronous (open() + write()), blocking the event loop during disk I/O. Should use iofiles or loop.run_in_executor().

#### Bottleneck 3: Synchronous Grobid Requests
**File**: extract.py:128
`python
response = requests.post(url, files=files, timeout=300)
`
Blocking HTTP call in an async toolkit. Should use iohttp or httpx async client.

#### Bottleneck 4: Sequential Extraction
**File**: cli.py:258-274
`python
for pdf in pdfs:
    progress.update(task, description=f"Extracting {pdf.name}...")
    # ... extraction ...
`
PDF extraction is sequential in the CLI. For large batches, this is a significant bottleneck.

### 4.2 Memory Usage Issues

1. **Full PDF download into memory**: The iter_chunked(8192) approach is memory-efficient for streaming, but the 
esponse.content is not bounded — a 10GB PDF would stream fine but the dest_path write has no size limit.

2. **PyMuPDF document not explicitly closed**: extract.py:48 opens itz.open(str(pdf_path)) but never calls doc.close(). For batch extraction, this leaks file handles.

### 4.3 Algorithm Efficiency

1. **Smart filename collision**: The current approach (year_author_title.pdf) should include a DOI hash suffix to prevent collisions when titles truncate.

2. **Publisher pattern matching**: _PUBLISHER_PATTERNS is a list of dicts searched sequentially. For 5 publishers this is fine, but if extended, a dict keyed by DOI prefix would be O(1).

### 4.4 Caching Opportunities

1. **Metadata caching**: OpenAlex/Unpaywall responses for the same DOI are fetched fresh every time. A simple disk cache (JSON files keyed by DOI hash) would eliminate redundant API calls.

2. **Publisher pattern results**: 
esolve_doi_to_publisher_pdf() is pure and deterministic — results could be memoized.

3. **Extraction results**: If a .md file already exists for a PDF with the same mtime, extraction could be skipped (--force to override).

### 4.5 Parallelization Potential

1. **Batch extraction**: PyMuPDFEngine.extract_markdown() is stateless per PDF — perfect for syncio.gather() or concurrent.futures.ProcessPoolExecutor.

2. **Grobid batch processing**: Grobid supports batch mode natively — sending multiple PDFs in one request reduces HTTP overhead.

3. **Parallel metadata resolution**: For large batches, OpenAlex metadata for multiple DOIs could be fetched in parallel with rate limiting.

---

## 5. Scientific Correction

### 5.1 Accuracy of PDF Extraction

**PyMuPDFEngine** (extract.py:16-92):
- **Section detection** uses regex patterns (extract.py:63-67) that match common section headers (Introduction, Methods, etc.) but miss domain-specific sections (e.g., "Background", "Materials and Methods", "Appendix").
- **Block sorting** (extract.py:53) sorts by (y, x) coordinates, which works for single-column PDFs but may misorder content in multi-column layouts.
- **Table/Figure detection** (extract.py:77-81) only checks if the first line starts with "Table " or "Figure " — misses numbered figures (e.g., "Fig. 1", "Figure 2a").
- **Fallback stub** (extract.py:87): On parse failure, writes "Extracted content from {filename}" — this is a valid Markdown file with no content, indistinguishable from an empty PDF.

**DoclingEngine** (extract.py:95-112):
- Delegates entirely to Docling's DocumentConverter — accuracy depends on Docling's model quality.
- Falls back to PyMuPDF on failure, losing Docling-specific structure.

**GrobidEngine** (extract.py:115-136):
- Produces TEI XML, not Markdown — inconsistent with the other engines.
- No post-processing to convert TEI to Markdown for downstream consumption.

### 5.2 Metadata Preservation

**Frontmatter completeness** (extract.py:31-41):
- workspace_id, doi, 	itle, uthors, year are injected from the metadata dict.
- **Missing**: journal, olume, issue, pages, publisher, license, bstract.
- **Empty keys are dropped** (extract.py:41): If metadata is None or empty, only extraction_engine and extracted_at appear — no DOI, no title.

**Smart filename metadata** (downloader.py:56-70):
- Only first author's last name is used (downloader.py:154).
- Year defaults to "0000" if missing (downloader.py:61).
- Title truncated to 50 chars without word-boundary awareness.

### 5.3 Open Access Compliance

**Strengths**:
- Respects OA licensing by using OpenAlex/Unpaywall (legal OA sources).
- Does not scrape publisher websites directly (uses API-resolved URLs).
- Publisher direct-PDF patterns use official endpoints (e.g., IEEE stamp, Springer content PDF).

**Weaknesses**:
- **No license tracking**: The OALocation.license field is in the model but never extracted or stored.
- **No embargo detection**: Some OA papers have embargo periods — the kit does not check.
- **Proxy usage** (downloader.py:196-232): Using institutional proxies to bypass paywalls is legally???? — the kit should document this clearly.

### 5.4 Citation Extraction Correctness

The kit does **not** extract citations from PDFs. Citation extraction is delegated to:
- GrobidEngine (TEI XML contains parsed references)
- scholar-rag-kit (post-extraction chunking)

**Gap**: No validation that extracted references match the PDF's actual reference list.

### 5.5 Academic Content Integrity

1. **No OCR fallback**: Scanned PDFs (image-only) will extract as empty or garbled text via PyMuPDF. No detection or warning.

2. **No page-range extraction**: Cannot extract specific sections (e.g., "only pages 5-10") — always processes the entire document.

3. **No watermark/stamp detection**: Downloaded PDFs may contain institutional watermarks or stamps that are not stripped.

4. **No version detection**: Cannot distinguish between preprint and published versions of the same paper.

---

## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent/Skill Be Created?

**Recommendation: YES — a pdf-quality-agent (or extend scholar-pdf-kit skill)**

**Rationale**: The kit has a narrow, well-defined scope (PDF lifecycle management) with clear evaluation metrics and multiple agent-in-the-loop opportunities.

### 6.2 Evaluation Metrics

| Metric | Definition | Target |
|:--|:--|:--|
| **Download Success Rate** | success_count / total_dois | = 70% for OA literature |
| **PDF Validation Pass Rate** | alid_downloads / total_downloads | = 99% |
| **Extraction Completeness** | 
on_empty_md_files / total_extractions | = 95% |
| **Frontmatter Completeness** | ields_present / expected_fields | = 80% (7 fields) |
| **Section Detection Accuracy** | correctly_identified_sections / total_sections | = 85% |
| **Smart Name Uniqueness** | unique_filenames / total_files | 100% |
| **Metadata Accuracy** | correct_metadata_fields / total_fields | = 90% |
| **Publisher Pattern Coverage** | matched_dois / total_publisher_dois | = 60% |
| **Retry Efficiency** | successful_retries / total_retries | = 30% |
| **Extraction Time per Page** | 	otal_time / total_pages | = 2 seconds |

### 6.3 Critic Capabilities Needed

1. **PDF Validator Critic**: Verifies that downloaded PDFs are actually readable (not just valid magic bytes). Checks page count, text density, image-to-text ratio.

2. **Extraction Quality Critic**: Compares extracted Markdown against the original PDF for completeness. Flags stub extrations, missing sections, garbled text.

3. **Metadata Consistency Critic**: Cross-checks extracted metadata (title, authors, year) against OpenAlex/Unpaywall records for accuracy.

4. **Frontmatter Completeness Critic**: Validates that all expected YAML fields are present and non-empty before handoff to RAG.

5. **Publisher Pattern Critic**: Monitors download success rates per publisher and flags patterns that are failing (e.g., IEEE stamp URL changed).

### 6.4 Agent-in-the-Loop Opportunities

1. **Download Review Agent**: After batch download, an agent reviews the summary table, identifies failures, and decides whether to retry with different strategies (proxy, alternative sources).

2. **Extraction Validation Agent**: After extraction, an agent spot-checks a sample of extracted Markdown files for quality (non-empty, reasonable section structure, frontmatter present).

3. **Metadata Hydration Agent**: For DOIs where OpenAlex/Unpaywall metadata is incomplete, the agent can query Crossref or Semantic Scholar to fill gaps.

4. **Proxy Configuration Agent**: Automatically detects the best proxy configuration based on download failure patterns and institutional affiliation.

5. **Content Deduplication Agent**: After extraction, identifies duplicate or near-duplicate content across extracted files (useful for preprint+published pairs).

### 6.5 Automation Potential

| Task | Current State | Automation Opportunity |
|:--|:--|:--|
| Batch download with retry | Manual re-run | Auto-retry with exponential backoff + proxy escalation |
| Extraction quality check | Manual spot-check | Automated heuristic scoring (text density, section count) |
| Metadata enrichment | Single-source (OpenAlex) | Multi-source cascade with fallback |
| Publisher pattern updates | Hardcoded | Community-maintained pattern registry |
| PDF deduplication | None | Content-hash based dedup across batches |
| Extracted content validation | None | LLM-based quality scoring |

---

## 7. Priority-Ranked Improvement Suggestions

### P0 — Critical (Fix Immediately)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 1 | PyMuPDF error swallowing produces silent stubs | extract.py:85-87 | RAG indexes empty documents |
| 2 | pyyaml undeclared dependency | pyproject.toml | Breaks on clean install |
| 3 | Malformed BibTeX export | cli.py:63-77 | Unusable bibliography output |
| 4 | User-Agent mismatch (docs vs code) | downloader.py:81 | Polite crawling violation |

### P1 — High (Next Sprint)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 5 | Synchronous file writes blocking event loop | downloader.py:102-104 | Performance degradation under load |
| 6 | No metadata caching (redundant API calls) | downloader.py:125-143 | Slow batch processing, API quota waste |
| 7 | Smart filename collisions on truncation | downloader.py:65 | File overwrites in batch downloads |
| 8 | models.py dead code (OAResult/OALocation) | models.py:1-50 | Confusion, maintenance burden |
| 9 | Sequential metadata fetching | downloader.py:166-185 | 2x latency for non-OA papers |

### P2 — Medium (Backlog)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 10 | No --engine pymupdf in CLI | cli.py:230 | Inconsistent API/CLI surface |
| 11 | PyMuPDF document handle leak | extract.py:48 | File handle exhaustion in batch |
| 12 | GrobidEngine returns XML not Markdown | extract.py:134-135 | Inconsistent output format |
| 13 | Duplicate MIN_PDF_SIZE_BYTES | alidator.py:8, publisher_patterns.py:19 | Maintenance risk |
| 14 | Single-author metadata extraction | downloader.py:154 | Incomplete metadata |
| 15 | No download size limit | downloader.py:78 | Risk of downloading huge files |
| 16 | TOCTOU race in file existence check | downloader.py:193 | Potential file corruption |

### P3 — Low (Nice-to-Have)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 17 | Publisher pattern extensibility | publisher_patterns.py:28-59 | Limited publisher coverage |
| 18 | No page-range extraction | extract.py | Cannot extract specific sections |
| 19 | No OCR fallback for scanned PDFs | extract.py | Empty extraction for image PDFs |
| 20 | No --resume / --retry-failed | cli.py | Manual re-run required |
| 21 | No type stubs / py.typed | Package root | Poor IDE support |
| 22 | Sequential extraction in CLI | cli.py:258-274 | Slow for large batches |

---

## Appendix A: File Inventory

| File | Lines | Purpose |
|:--|:--|:--|
| src/scholar_pdf/__init__.py | 39 | Package exports |
| src/scholar_pdf/cli.py | 279 | Typer CLI (download/ingest/extract) |
| src/scholar_pdf/config.py | 39 | Pydantic-settings configuration |
| src/scholar_pdf/downloader.py | 287 | Async PDF downloader with cascade |
| src/scholar_pdf/extract.py | 136 | PyMuPDF/Docling/Grobid extraction |
| src/scholar_pdf/models.py | 50 | Pydantic OA models (unused) |
| src/scholar_pdf/publisher_patterns.py | 226 | Publisher direct-PDF + proxy rewrite |
| src/scholar_pdf/validator.py | 96 | Binary + structural PDF validation |
| 	ests/test_cli.py | 95 | CLI integration tests |
| 	ests/test_downloader.py | 224 | Downloader unit tests |
| 	ests/test_extract.py | 25 | Extraction tests (minimal) |
| 	ests/test_publisher_patterns.py | 160 | Publisher pattern tests |
| 	ests/test_validator.py | 128 | Validator tests (comprehensive) |

**Total source**: ~1,153 lines (src) + ~632 lines (tests) = ~1,785 lines

## Appendix B: Dependency Map

`
scholar-pdf-kit
+-- Core deps (pyproject.toml)
¦   +-- pydantic >= 2.0.0
¦   +-- pydantic-settings >= 2.0.0
¦   +-- aiohttp >= 3.9.0
¦   +-- typer >= 0.9.0
¦   +-- requests >= 2.31.0
¦   +-- rich >= 13.0.0
¦   +-- tenacity >= 8.0.0
¦   +-- pypdf >= 4.0.0
¦   +-- pymupdf >= 1.24.0
¦   +-- scholar-search-kit (editable)
+-- Optional deps [extract]
¦   +-- docling >= 2.5.0
¦   +-- requests
¦   +-- lxml
+-- Undeclared transitive deps
¦   +-- pyyaml (via docling/pymupdf)
¦   +-- fitz (PyMuPDF import name)
+-- External services
    +-- OpenAlex API (api.openalex.org)
    +-- Unpaywall API (api.unpaywall.org)
    +-- Grobid server (localhost:8070, optional)
`

## Appendix C: Test Coverage Assessment

| Module | Test File | Test Count | Coverage Assessment |
|:--|:--|:--|:--|
| cli.py | 	est_cli.py | 5 | **Low**: No extract/ingest tests, no export tests |
| downloader.py | 	est_downloader.py | 5 | **Medium**: Core flows covered, no edge cases |
| extract.py | 	est_extract.py | 1 | **Very Low**: Only frontmatter test, no content extraction |
| publisher_patterns.py | 	est_publisher_patterns.py | 12 | **Good**: All patterns + proxy rewriting covered |
| alidator.py | 	est_validator.py | 9 | **Good**: Comprehensive edge cases |
| config.py | — | 0 | **None**: No config tests |
| models.py | — | 0 | **None**: No model tests (dead code) |

**Overall**: ~32 tests, uneven coverage. Extraction engine testing is critically underrepresented.

---

*Analysis generated by automated deep-dive. All file:line references verified against source code.*


---

<!-- Source: kit_04_bib.md -->
﻿# Scholar Bib Kit -- Comprehensive Deep Dive Analysis

> **Kit path:** `C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-bib-kit`
> **Analysis date:** 2026-09-14
> **Version:** 0.1.0 (hatchling build)
> **Total source files:** 5 Python modules + 1 test file
> **Total source LOC:** ~351 lines (src + tests)

---

## 1. Executive Summary

`scholar-bib-kit` is the bibliography management component of the Nexus Scholar Suite. It provides four core capabilities -- parsing, linting, deduplication, and Crossref resolution -- for BibTeX databases. Despite its small codebase (~290 LOC of application code), it plays a critical role in the literature review pipeline: every project's `references.bib` should pass through this kit for hygiene before being consumed by RAG indexing, graph construction, or export.

**Current maturity: Early alpha.** The kit has a working CLI with four commands, a thin Python API, and basic tests. However, it exhibits significant gaps in documentation accuracy, error handling, API surface consistency with its own docs, and integration alignment with the rest of the Nexus Suite. The documentation (`docs/tutorial.md`, `docs/api_reference.md`) describes classes and methods (`RepairEngine`, `CrossrefValidator`, `BibEntry` model) that do not exist in the codebase -- a strong signal of stale/aspirational docs that will confuse agents and developers.

**Key finding:** The kit's documentation describes a `fix` command, `RepairEngine`, `CrossrefValidator`, and `BibEntry`/`RepairStats` Pydantic models that are **entirely absent** from the implementation. The actual implementation provides `lint`, `merge`, `dedup`, `resolve` commands and `BibParser`, `BibLinter`, `BibDeduplicator`, `BibResolver` classes. This is a major coherence failure.

---

## 2. Detailed Analysis by Dimension

### 2.1 Functionalities

#### 2.1.1 Complete Capability Inventory

| Capability | Module | Status | Notes |
|:--|:--|:--|:--|
| BibTeX file loading | `parser.py` | Working | Thin wrapper around `bibtexparser.parse_file` |
| BibTeX file saving | `parser.py` | Working | Thin wrapper around `bibtexparser.write_file` |
| Title case protection (double braces) | `linter.py:12-18` | Working | Idempotent, handles single-brace and no-brace |
| Citation key standardization (AuthorYear) | `linter.py:21-48` | Working | Single mode only; suffix starts at 'a' (chr(97)) |
| Multi-file merge | `cli.py:42-72` | Working | Sequential load + block-level add |
| DOI-based deduplication | `deduplicator.py:22-30` | Working | Exact match on cleaned DOI |
| Title-based deduplication | `deduplicator.py:31-33` | Working | Exact match on cleaned title |
| Field grafting on dedup | `deduplicator.py:36-40` | Working | Merges missing fields from duplicate into survivor |
| Crossref DOI resolution | `resolver.py:14-25` | Working | Fetches `application/x-bibtex` from Crossref |
| Crossref title/author search | `resolver.py:27-45` | Working | Fallback when DOI is missing |
| Entry-level resolution | `resolver.py:47-87` | Working | Replaces entire entry fields in-place |
| Library-level resolution | `resolver.py:89-100` | Working | Parallel async tasks via `as_completed` |
| CLI: `lint` | `cli.py:23-40` | Working | With `--generate-keys` option |
| CLI: `merge` | `cli.py:42-72` | Working | With `--dedup/--no-dedup` |
| CLI: `dedup` | `cli.py:74-96` | Working | Standalone dedup command |
| CLI: `resolve` | `cli.py:98-124` | Working | Async Crossref resolution |

#### 2.1.2 CLI Commands to Functions Mapping

| CLI Command | Entry Function | Core API Calls |
|:--|:--|:--|
| `scholar-bib lint <file>` | `cli.lint()` | `BibParser.load()` -> `BibLinter.lint()` -> `BibParser.save()` |
| `scholar-bib merge <files>` | `cli.merge()` | `BibParser.load()` x N -> `Library.add()` loop -> `BibDeduplicator.dedup()` -> `BibParser.save()` |
| `scholar-bib dedup <file>` | `cli.dedup()` | `BibParser.load()` -> `BibDeduplicator.dedup()` -> `BibParser.save()` |
| `scholar-bib resolve <file>` | `cli.resolve()` | `BibParser.load()` -> `BibResolver.resolve_library()` -> `BibParser.save()` |

#### 2.1.3 Data Models and Schemas

The kit uses `bibtexparser` v2 data models directly -- there are **no custom Pydantic models** despite `pydantic` being a declared dependency and the docs claiming `BibEntry`/`RepairStats` models exist.

**Actual data flow:**
```
File (.bib) -> bibtexparser.parse_file() -> Library (blocks: list[Block])
  -> Library.entries: list[Entry]
    -> Entry.key: str
    -> Entry.entry_type: str
    -> Entry.fields_dict: dict[str, Field]
      -> Field.key: str
      -> Field.value: str
  -> Library.blocks: list[Block] (includes Entry, Preamble, Comment)
```

#### 2.1.4 Integration Points with Other Kits

| Consumer Kit | Integration Point | Usage |
|:--|:--|:--|
| `scholar-agent-kit` | `server.py:66-68,586-591` | MCP tool `nexus_bib_clean` imports `BibParser`, `BibLinter`, `BibDeduplicator` |
| `scholar-search-kit` | `providers/crossref.py:116-142` | Crossref provider exposes `validate_reference()` hook intended for bib-kit (but bib-kit does NOT use it -- it has its own Crossref client) |
| `scholar-search-kit` | `http_client.py:47-122` | `BibResolver` uses `AcademicHttpClient` for HTTP requests |
| `scholar-harness` | `tests/test_mcp_tools_graph.py:191-208` | Integration tests exercise `BibParser` round-trips |
| `nexus-scholar` metapackage | `pyproject.toml` | Kit is included in distribution wheel via hatchling `force-include` |

**Critical integration gap:** `BibResolver` builds its own Crossref query (lines 29-31 of `resolver.py`) rather than using the `CrossrefProvider.validate_reference()` hook from `scholar-search-kit`. This duplicates rate limiting, user-agent handling, and error recovery logic. The `scholar-search-kit` Crossref provider at `providers/crossref.py:118-141` already has a `validate_reference()` method with a relevance score threshold (>40) that `BibResolver` lacks.

---

### 2.2 Improvements

#### 2.2.1 Code Quality Issues

**[IMP-1] Debug print statements in production code**
- `resolver.py:19`: `print(f"DOI {doi} status: {response.status_code}, content: {response.text[:100]}")`
- `resolver.py:23`: `print(f"Error fetching DOI {doi}: {e}")`
- `resolver.py:33`: `print(f"Search status: {response.status_code}")`
- `resolver.py:39`: `print(f"Found DOI from search: {doi}")`
- `resolver.py:49`: `print(f"Resolving entry: {entry.key}")`
- `resolver.py:54`: `print(f"DOI field: {doi_field}")`
- `resolver.py:60`: `print(f"Using DOI: {doi}")`
- `resolver.py:75`: `print(f"Resolved new entry for {entry.key} with {len(new_entry.fields_dict)} fields")`
- `resolver.py:85`: `print(f"No entries parsed from crossref string for {entry.key}: {bibtex_str}")`
- `resolver.py:87`: `print(f"Exception parsing bibtex string: {e}")`

These are debug prints that should use `logging` or be removed. They leak potentially sensitive data (full DOI strings, API responses) to stdout.

**[IMP-2] Stale documentation describes non-existent API**
- `docs/api_reference.md:18-31` describes `CrossrefValidator` class with `get_by_doi()` and `fuzzy_match()` methods -- does not exist.
- `docs/api_reference.md:33-51` describes `RepairEngine` class with `repair_entry()` method -- does not exist.
- `docs/api_reference.md:53-57` describes `BibEntry` and `RepairStats` Pydantic models -- do not exist.
- `docs/tutorial.md:10` describes `scholar-bib fix` command -- does not exist (actual commands: `lint`, `merge`, `dedup`, `resolve`).
- `docs/tutorial.md:16-21` describes `--no-fuzzy` and `--overwrite` options -- do not exist.
- `docs/api_reference.md:12-16` describes `BibParser` as instantiated with `BibParser(Path("file.bib"))` followed by `.read()` / `.write()` -- the actual API is `BibParser.load(filepath)` / `BibParser.save(library, filepath)` (static methods).

**[IMP-3] Unused `pydantic` dependency**
- `pyproject.toml:18` declares `pydantic>=2.0.0` but no module in the kit imports or uses Pydantic.

**[IMP-4] Inconsistent `__init__.py` exports**
- `__init__.py:1` contains only `"""Scholar Bib Kit"""` -- no public API re-exports.
- Consumers must import from submodules (`from scholar_bib.parser import BibParser`).

**[IMP-5] No type hints on CLI functions**
- `cli.py` functions lack return type annotations and parameter type hints beyond what Typer infers.

#### 2.2.2 Missing Features or Capabilities

**[FEAT-1] No `fix`/`repair` command** -- The docs promise a `fix` command that repairs entries using Crossref. The actual `resolve` command does something similar but is not the documented interface.

**[FEAT-2] No confidence scoring on resolution** -- `BibResolver.resolve_search()` takes the first Crossref result without any relevance score check. The `scholar-search-kit` Crossref provider (`crossref.py:138`) checks `score > 40` but `BibResolver` does not.

**[FEAT-3] No `--format` export option** -- Cannot export to RIS, EndNote, or other formats. BibTeX is the only supported format.

**[FEAT-4] No `validate`/`check` command** -- No way to validate a BibTeX file for structural issues without linting it.

**[FEAT-5] No batch/file-list input for resolve** -- Can only resolve one `.bib` file at a time.

**[FEAT-6] No `--verbose`/`--quiet` flags** -- All commands have fixed output verbosity.

**[FEAT-7] No progress reporting for resolve** -- The `progress_callback` in `resolve_library()` is a no-op (`pass` at `cli.py:118`). No progress bar or percentage is shown.

**[FEAT-8] No structured output (JSON)** -- All output is human-readable console text. No `--json` flag for machine consumption.

#### 2.2.3 API Design Improvements

**[API-1] `BibParser` should support string parsing**
- `BibParser` only has `load(filepath)` and `save(library, filepath)`. There is no `parse_string(text)` static method, even though `bibtexparser.parse_string()` is used directly in `resolver.py:72`.

**[API-2] `BibResolver` should return results, not mutate in-place**
- `resolve_entry()` mutates the entry in-place and returns `None`. This is error-prone and makes it impossible to compare before/after. A better design returns a new `Entry` or a result object.

**[API-3] `BibDeduplicator.dedup()` should accept configuration**
- No way to configure dedup strategy (DOI-only, title-only, fuzzy threshold, case sensitivity).

**[API-4] `BibLinter.lint()` should accept a configuration object**
- Only `generate_keys` is configurable. No control over title wrapping style, key format, field normalization, etc.

**[API-5] Inconsistent error handling patterns**
- `BibParser.load()` has no error handling (raw exception propagation).
- `BibResolver.resolve_doi()` catches all exceptions and returns `None`.
- `BibResolver.resolve_search()` catches all exceptions and returns `None`.
- `BibDeduplicator.dedup()` has no error handling.
- `BibLinter.lint()` has no error handling.

#### 2.2.4 Error Handling Gaps

**[ERR-1] No file-existence check in `BibParser.load()`**
- Passing a non-existent path will raise an opaque `FileNotFoundError` from bibtexparser.

**[ERR-2] Silent failure on empty library**
- `cli.py:49-51` checks `if not input_files` but `cli.py:64` accesses `merged_library.entries` without checking if `merged_library is None` (the `for` loop body might never execute if `input_files` is empty after the guard).

**[ERR-3] Resolver swallows all errors silently**
- `resolver.py:22-24`, `resolver.py:43-44`, `resolver.py:86-87` catch `Exception` and either `pass` or `print` -- no way for callers to know resolution failed.

**[ERR-4] No validation of input file format**
- If the input is not a valid `.bib` file, `bibtexparser` may raise cryptic errors.

**[ERR-5] `resolve` CLI overwrites input on error**
- `cli.py:107` sets `output_file = input_file` by default. If `resolve_library()` fails partway through, the original file may be corrupted since `BibParser.save()` writes back to the same path.

**[ERR-6] `BibResolver` creates `AcademicHttpClient` but never closes it**
- `resolver.py:12` creates `self.http_client = AcademicHttpClient(...)` but there is no `__aenter__`/`__aexit__` or `close()` method. The HTTP session leaks.

#### 2.2.5 Documentation Needs

**[DOC-1] README.md is a stub** -- Only 3 lines: "# scholar-bib-kit" and "Part of the Nexus Scholar Suite."

**[DOC-2] API reference is entirely wrong** -- Describes non-existent classes and methods (see IMP-2).

**[DOC-3] Tutorial describes non-existent command** -- `scholar-bib fix` does not exist.

**[DOC-4] No CHANGELOG or version history**

**[DOC-5] No contribution guidelines**

---

### 2.3 Problems

#### 2.3.1 Known Bugs

**[BUG-1] Documentation/code mismatch is a blocking issue for agents**
- An agent reading `docs/api_reference.md` will attempt `from scholar_bib.validator import CrossrefValidator` and fail. This is the single most impactful problem because agents rely on docs.

**[BUG-2] `nexus_bib_clean` MCP tool was historically lint-only**
- Per `kits_surface_matrix.md:73-81`, this was documented as a known issue. It has been resolved in the MCP server, but the kit itself has no corresponding `clean()` convenience function that bundles lint + dedup.

**[BUG-3] `resolved.bib` contains incorrect search result**
- `resolved.bib:18-25` shows the "Attention Is All You Need" resolution matched to `DOI: 10.65215/r5bs2d54` (Shenzhen Medical Academy, 2025) instead of the actual Vaswani et al. 2017 paper. The resolver picks the first Crossref result without relevance validation.

**[BUG-4] `BibResolver.resolve_entry()` can corrupt entry on partial failure**
- `resolver.py:80`: `entry.fields_dict.clear()` is called before the new entry is fully verified. If the BibTeX string parsing at line 72-83 fails after the clear, the entry is left with zero fields.

#### 2.3.2 Edge Cases Not Handled

**[EDGE-1] Entries with no DOI and no title**
- `BibResolver.resolve_entry()` requires either a DOI or a title to attempt resolution. Entries with neither (e.g., only author + year) are silently skipped.

**[EDGE-2] Very long author lists**
- `linter.py:27` splits on ` and ` to get the first author. Author lists with ` and ` in affiliations or names (e.g., "Institute of Science and Technology") will be incorrectly split.

**[EDGE-3] Unicode in author names**
- `linter.py:34` strips all non-ASCII from author names with `re.sub(r'[^a-zA-Z]', '', first_author)`. Names with diacritics (e.g., "Muller" -> "Muller", "Garcia" -> "Garcia") are fine, but non-Latin scripts (CJK, Cyrillic, Arabic) produce empty keys.

**[EDGE-4] Entries with non-ASCII DOI characters**
- `deduplicator.py:7` cleans DOIs with `re.sub(r'[^a-z0-9]', '', str(s).lower())`. This is correct for standard DOIs but would strip URL-encoded characters.

**[EDGE-5] Concurrent modification during dedup**
- `deduplicator.py:38-40` modifies `target_entry` while iterating over the duplicate's fields. This is safe with bibtexparser v2's dict-like `fields_dict`, but would be problematic if the library is shared.

**[EDGE-6] Merge with duplicate keys across files**
- `cli.py:61-62` adds blocks by reference. If two files have entries with the same key but different content, both are added (no key collision check). `BibDeduplicator` only deduplicates by DOI/title, not by key.

**[EDGE-7] `asyncio.run()` in `resolve` CLI**
- `cli.py:121` calls `asyncio.run(run_resolve())`. This is correct for a fresh event loop, but if the kit is ever called from an already-running async context (e.g., from an MCP server), this will fail with "RuntimeError: This event loop is already running."

#### 2.3.3 Limitations

**[LIM-1] No fuzzy dedup** -- Title dedup is exact (after cleaning). Typos, abbreviation differences, or subtitle variations produce false negatives.

**[LIM-2] No author-based dedup** -- Two entries for the same paper with different DOIs (e.g., preprint vs. published) are not caught.

**[LIM-3] No field normalization** -- Author names, journal abbreviations, and date formats are not standardized.

**[LIM-4] BibTeX-only** -- No RIS, EndNote, CSV, or JSON import/export.

**[LIM-5] Single-threaded HTTP** -- Despite using `asyncio`, the resolver does not use connection pooling or concurrent connection limits beyond the rate limiter.

---

### 2.4 Optimizations

#### 2.4.1 Performance Bottlenecks

**[OPT-1] Sequential file loading in merge**
- `cli.py:55-62` loads files one at a time in a `for` loop. For large bibliographies (10k+ entries), this could be parallelized with `asyncio.gather()` or `concurrent.futures`.

**[OPT-2] O(n^2) potential in dedup**
- `deduplicator.py:28-33` does O(1) dict lookups per entry, which is good. However, the `unique_entries` list is scanned linearly for field grafting (`unique_entries[target_idx]`), and the list is rebuilt at the end. For very large libraries (100k+ entries), the list operations could be optimized.

**[OPT-3] Unbounded concurrency in resolver**
- `resolver.py:91-93` creates all resolve tasks upfront and runs them with `as_completed()`. With a library of 10,000 entries, this creates 10,000 concurrent HTTP requests. The rate limiter (10/s) throttles but the task objects themselves consume memory.

**[OPT-4] No connection pooling**
- Each `BibResolver` instance creates a new `AcademicHttpClient`. If multiple resolvers are instantiated (e.g., in a pipeline), each has its own connection pool.

#### 2.4.2 Caching Opportunities

**[CACHE-1] Crossref DOI resolution**
- `resolve_doi()` fetches the same DOI multiple times if it appears in different entries. The `AcademicHttpClient` uses `hishel` caching, but the cache key includes the full URL. Identical DOIs would hit the cache, but the overhead of URL construction and cache lookup per request is unnecessary.

**[CACHE-2] Title search results**
- `resolve_search()` queries Crossref for each title. If the same title appears in multiple entries (e.g., duplicates before dedup), the same search is performed repeatedly.

#### 2.4.3 Parallelization Potential

**[PAR-1] Library-level dedup**
- The dedup algorithm is inherently sequential (order-dependent for field grafting). However, the initial DOI/title map building could be parallelized, followed by a sequential merge pass.

**[PAR-2] Lint operations**
- Each entry's linting is independent. The `lint()` method could process entries in parallel with `concurrent.futures.ThreadPoolExecutor`.

---

### 2.5 Scientific Correction

#### 2.5.1 BibTeX Parsing Accuracy

**[SCHOL-1] bibtexparser v2 beta**
- The kit pins `bibtexparser>=2.0.0b7` (actual installed: `2.0.0b9`). This is a beta version of a major rewrite. Known issues include:
  - Stripping of outer braces from titles (partially addressed by the linter).
  - Inconsistent handling of `@string` and `@preamble` directives.
  - Potential data loss on round-trip for entries with unusual formatting.

**[SCHOL-2] Title brace wrapping is incomplete**
- `linter.py:17` checks `if not (title.startswith('{') and title.endswith('}'))` -- this catches single-brace wrapping (`{Title}`) but not nested braces (`{{Title}}`). The bibtexparser v2 beta may strip outer braces, leaving `{{Title}}` as `{Title}`, which the linter would then re-wrap to `{{{Title}}}`.

**[SCHOL-3] Crossref BibTeX is not standardized**
- Crossref's `application/x-bibtex` format uses its own field naming (e.g., `ISSN` instead of `issn`, mixed-case field names). The kit does not normalize these after resolution.

#### 2.5.2 Reference Format Compliance

**[SCHOL-4] DOI normalization is minimal**
- `resolver.py:59` only strips `https://doi.org/` and `http://doi.org/` prefixes. It does not handle:
  - `doi:` prefix (common in some tools)
  - URL-encoded DOIs
  - DOIs with trailing slashes or query parameters
  - `10.` prefix validation

**[SCHOL-5] Key generation does not handle edge cases**
- `linter.py:34` strips non-alpha from author names, producing empty strings for numeric-only names. `linter.py:35` strips non-digits from year, but does not validate the year is a reasonable academic year (e.g., 1900-2099).

#### 2.5.3 Citation Style Correctness

**[SCHOL-6] No citation style enforcement**
- The kit does not enforce any citation style (APA, Chicago, IEEE, etc.). It focuses on BibTeX structural hygiene, not bibliography formatting.

**[SCHOL-7] Journal name normalization is absent**
- Abbreviated vs. full journal names are not standardized. "J. Mach. Learn. Res." and "Journal of Machine Learning Research" are treated as different values.

#### 2.5.4 Academic Standards Adherence

**[SCHOL-8] No retraction/correction awareness**
- The kit does not check whether resolved DOIs correspond to retracted papers. This is handled by `scholar-verify-kit` but is not integrated into the resolution pipeline.

**[SCHOL-9] No open-access metadata enrichment**
- Resolved entries from Crossref do not include open-access status, license, or version information.

---

### 2.6 Agent/Skill Recommendation

#### 2.6.1 Should a specialized agent or skill be created?

**Current state:** A `scholar-bib-kit` skill already exists at `.agents/skills/scholar-bib-kit/SKILL.md` (110 lines). It is well-structured and covers CLI usage, Python API, and agent guidelines.

**Recommendation: No new skill is needed. The existing skill is sufficient but needs updates to match the actual API.**

However, the kit's scope is narrow enough that a **dedicated agent** could add value if the following conditions are met:

1. **The documentation is fixed** -- An agent reading stale docs will fail.
2. **The resolve pipeline needs orchestration** -- Currently, the `resolve` command is a black box. An agent could provide intelligent resolution strategies (e.g., "resolve only entries missing DOIs", "resolve but preserve existing fields", "resolve with confidence threshold").

#### 2.6.2 Evaluation Metrics for Agent

If a bib-kit agent were created, these metrics would be relevant:

| Metric | Definition | Target |
|:--|:--|:--|
| `bib_parse_success_rate` | % of `.bib` files parsed without errors | >99% |
| `bib_dedup_precision` | % of detected duplicates that are true duplicates | >95% |
| `bib_dedup_recall` | % of true duplicates that are detected | >90% |
| `bib_resolve_accuracy` | % of resolved entries matching the correct paper | >85% |
| `bib_resolve_coverage` | % of entries successfully resolved | >70% (for messy inputs) |
| `bib_lint_idempotency` | Running lint twice produces identical output | 100% |
| `bib_roundtrip_fidelity` | load -> save -> load produces identical Library | 100% |
| `bib_key_uniqueness` | Generated keys are unique within the library | 100% |

#### 2.6.3 Critic Capabilities Needed

A bib-kit critic should check:
1. **Stale documentation** -- Verify that all documented classes/methods/commands exist in the code.
2. **Resolution quality** -- Verify that Crossref-resolved entries match the original intent (title similarity, year consistency, author overlap).
3. **Dedup correctness** -- Verify that removed entries were true duplicates and no entries were incorrectly merged.
4. **Key uniqueness** -- Verify that generated citation keys are unique and meaningful.
5. **Roundtrip safety** -- Verify that `load -> process -> save -> load` produces equivalent results.

#### 2.6.4 Agent-in-the-Loop Opportunities

| Opportunity | Description | Priority |
|:--|:--|:--|
| Resolution review | Agent reviews Crossref matches before accepting | High |
| Dedup conflict resolution | Agent decides when two entries are "similar enough" | Medium |
| Field merging strategy | Agent decides which fields to keep when duplicates have conflicting values | Medium |
| Key generation review | Agent reviews generated keys for meaningfulness | Low |

#### 2.6.5 Automation Potential

| Automation | Description | Complexity |
|:--|:--|:--|
| Pre-commit bib lint | Auto-lint `.bib` files on commit | Low |
| CI bib validation | Validate `.bib` files in CI pipeline | Low |
| Batch resolve with progress | Resolve large libraries with progress reporting | Medium |
| Smart dedup with fuzzy matching | Use embeddings or string similarity for dedup | High |

---

## 3. Priority-Ranked Improvement Suggestions

### Priority 1 (Critical -- Blocking)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| IMP-2 | **Fix documentation to match actual API** -- Rewrite `docs/api_reference.md` and `docs/tutorial.md` to describe `BibParser`, `BibLinter`, `BibDeduplicator`, `BibResolver` and the `lint`/`merge`/`dedup`/`resolve` commands. | 2h | Critical -- agents and developers rely on docs |
| BUG-1 | **Remove stale Crossref/Repair class references** -- Delete references to `CrossrefValidator`, `RepairEngine`, `BibEntry`, `RepairStats` from docs. | 1h | Critical -- prevents import errors |
| ERR-5 | **Add output-before-overwrite safety** -- Write to a temp file first, then rename on success. Prevents data loss on partial failure. | 4h | Critical -- data loss prevention |

### Priority 2 (High -- Important)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| IMP-1 | **Replace print() with logging** -- Use `logging` module throughout `resolver.py`. Remove all debug prints. | 2h | High -- production readiness |
| ERR-3 | **Add structured error reporting** -- Return success/failure per entry from resolver. Log failures. | 4h | High -- observability |
| BUG-3 | **Add relevance score check to resolver** -- Use Crossref's `score` field to filter low-confidence matches. Add configurable threshold. | 4h | High -- scientific accuracy |
| BUG-4 | **Fix entry corruption on partial failure** -- Do not clear entry fields until new entry is fully parsed. | 2h | High -- data integrity |
| ERR-6 | **Add context manager to BibResolver** -- Implement `__aenter__`/`__aexit__` to properly close HTTP client. | 2h | High -- resource leak |

### Priority 3 (Medium -- Nice to Have)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| FEAT-7 | **Add progress reporting for resolve** -- Show progress bar using `rich.progress`. | 4h | Medium -- user experience |
| FEAT-6 | **Add --verbose/--quiet flags** -- Control output verbosity. | 2h | Medium -- usability |
| IMP-3 | **Remove unused pydantic dependency** -- Or implement validation models. | 1h | Medium -- dependency hygiene |
| IMP-4 | **Add public API re-exports to __init__.py** -- `from scholar_bib import BibParser, BibLinter, ...` | 1h | Medium -- API ergonomics |
| EDGE-3 | **Handle non-Latin author names in key generation** -- Fall back to entry key or generate hash. | 2h | Medium -- internationalization |
| LIM-1 | **Add fuzzy title dedup** -- Use string similarity (Levenshtein, Jaccard) for title comparison. | 8h | Medium -- dedup quality |
| SCHOL-4 | **Expand DOI normalization** -- Handle `doi:` prefix, URL-encoded DOIs, trailing slashes. | 2h | Medium -- robustness |

### Priority 4 (Low -- Future Work)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| FEAT-3 | **Add RIS/EndNote/JSON export** -- Multi-format output support. | 16h | Low -- niche use case |
| FEAT-4 | **Add validate/check command** -- Structural validation without modification. | 4h | Low -- nice to have |
| OPT-1 | **Parallelize merge file loading** -- Use async or threading for large file sets. | 4h | Low -- perf at scale |
| OPT-3 | **Add concurrency limits to resolver** -- Use `asyncio.Semaphore` to cap parallel requests. | 2h | Low -- memory at scale |
| LIM-6 | **Add field normalization** -- Standardize author names, journal abbreviations, date formats. | 16h | Low -- quality of life |

---

## 4. File Inventory with Line References

| File | LOC | Purpose | Key Issues |
|:--|:--|:--|:--|
| `src/scholar_bib/__init__.py` | 1 | Package marker | Empty -- no public API exports |
| `src/scholar_bib/cli.py` | 127 | Typer CLI with 4 commands | No type hints; progress callback is no-op; overwrite safety missing |
| `src/scholar_bib/parser.py` | 14 | BibTeX load/save wrapper | No string parsing; no error handling |
| `src/scholar_bib/linter.py` | 50 | Title wrapping + key generation | Unicode edge cases; single key mode |
| `src/scholar_bib/deduplicator.py` | 60 | DOI + title dedup | No fuzzy matching; no config |
| `src/scholar_bib/resolver.py` | 100 | Crossref resolution | Debug prints; no confidence check; resource leak; entry corruption risk |
| `tests/test_bib.py` | 61 | Basic unit tests | Only 2 test functions; no resolver tests; no edge case coverage |
| `docs/api_reference.md` | 57 | API documentation | **Entirely wrong** -- describes non-existent classes |
| `docs/tutorial.md` | 40 | Tutorial | **Entirely wrong** -- describes non-existent command |
| `README.md` | 3 | Package README | Stub -- no useful content |

---

## 5. Cross-Reference: Kit vs. Surface Matrix

The `kits_surface_matrix.md` (lines 212-225) documents these known facts about `scholar-bib-kit`:

| Surface Matrix Claim | Verified? | Notes |
|:--|:--|:--|
| `BibParser.load/save` (bibtexparser v2) | Yes | `parser.py:7-14` |
| `BibLinter.lint(lib, generate_keys=False)` -- only AuthorYear key mode | Yes | `linter.py:6-50` |
| `BibDeduplicator.dedup` -- cleaned-DOI first, then cleaned-title; survivor = first occurrence | Yes | `deduplicator.py:11-60` |
| `BibResolver.resolve_doi/search/entry/library` -- async, Crossref x-bibtex, replaces whole entry | Yes | `resolver.py:14-100` |
| CLI: lint/merge/dedup/resolve | Yes | `cli.py:23-124` |
| lint/dedup/resolve overwrite input in place when --output omitted | Yes | `cli.py:30-31,80-81,106-107` |
| merge default output = CWD merged.bib | Yes | `cli.py:45` |
| MCP: `nexus_bib_clean` = in-place lint only | Was true, now resolved | See matrix finding 4 |
| bibtexparser 2.0.0b9 (beta) | Yes | `pyproject.toml:17` |
| title brace-wrapping idempotent | Partially -- see SCHOL-2 | |
| DOI normalization only strips `https?://doi.org/` | Yes | `resolver.py:59` |
| pydantic declared-but-unused | Yes | `pyproject.toml:18` |
| print()-based output in resolve | Yes | 10 print statements in resolver.py |

---

*Analysis generated 2026-09-14 by deep-dive file sweep of `tools/scholar-bib-kit/`.*


---

<!-- Source: kit_05_rag.md -->
﻿# Scholar RAG Kit — Comprehensive Deep Dive Analysis

**Kit**: `scholar-rag-kit` (v0.1.0)
**Location**: `C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-rag-kit`
**Analysis Date**: 2026-09-14
**Analyst**: File Search Specialist

---

## Executive Summary

`scholar-rag-kit` is the scientific retrieval-augmented generation engine in the Nexus Scholar Suite. It provides structural AST chunking, methodology metadata tagging, hybrid graph-boosted semantic retrieval, grounded synthesis with atomic claim-level attribution, cross-study methodology matrix extraction, and consensus cartography. The kit comprises **8 source modules** (463 lines CLI + 1,827 lines core logic), **8 test files** (957 lines), and **2 documentation files** (190 lines).

**Overall Assessment**: The kit is architecturally sound with clean separation of concerns, strong idempotency guarantees, and a well-defined hybrid scoring formula. However, it suffers from **3 critical issues** (undeclared dependency, dead parameter, schema mismatch with verify-kit), **5 moderate code quality issues**, **4 performance bottlenecks**, and **2 significant scientific correction needs**. The kit is a strong candidate for a specialized agent/skill given its narrow scope and well-defined evaluation metrics.

---

## 1. Functionalities — Complete Capability Map

### 1.1 Module Inventory

| Module | File | Lines | Responsibility |
|--------|------|-------|----------------|
| `chunker.py` | `src/scholar_rag/chunker.py` | 265 | Structural AST markdown chunking with hierarchy breadcrumbs |
| `indexer.py` | `src/scholar_rag/indexer.py` | 267 | ChromaDB vector store indexing with idempotent upserts |
| `retriever.py` | `src/scholar_rag/retriever.py` | 281 | Hybrid graph-boosted semantic retrieval |
| `embedder.py` | `src/scholar_rag/embedder.py` | 115 | Embedding function factory (SentenceTransformers/OpenAI/Mock) |
| `synthesis.py` | `src/scholar_rag/synthesis.py` | 415 | Grounded synthesis engine + methodology matrix generator |
| `matrix.py` | `src/scholar_rag/matrix.py` | 272 | Dynamic protocol extraction matrix extractor |
| `consensus.py` | `src/scholar_rag/consensus.py` | 400 | Consensus Cartographer (claim clustering + verdicts) |
| `models.py` | `src/scholar_rag/models.py` | 269 | Pydantic data models and schemas |
| `cli.py` | `src/scholar_rag/cli.py` | 443 | Typer CLI (6 commands) |
| `__init__.py` | `src/scholar_rag/__init__.py` | 53 | Public API surface (22 exports) |

### 1.2 CLI Commands → Function Mapping

| CLI Command | Entry Point | Core Function | Key Parameters |
|-------------|-------------|---------------|----------------|
| `scholar-rag index` | `cli.py:33-74` | `ScholarIndexer.index_directory()` | `docs_path`, `--bib`, `--workspace-id`, `--embedder` |
| `scholar-rag query` | `cli.py:77-187` | `ScholarRetriever.query()` | `query_text`, `--section-category`, `--paradigm`, `--graph`, `--alpha`, `--beta` |
| `scholar-rag synthesize` | `cli.py:189-266` | `GroundedSynthesisEngine.synthesize()` | `query_text`, `--rq-id`, `--output`, `--output-claims` |
| `scholar-rag consensus` | `cli.py:269-370` | `ConsensusCartographer.analyze()` | `claims_file`, `--threshold`, `--similarity`, `--output-json/md` |
| `scholar-rag matrix` | `cli.py:373-423` | `MatrixExtractor.extract_all()` or `generate_methodology_matrix()` | `--protocol`, `--output-dir` |
| `scholar-rag stats` | `cli.py:426-439` | `ScholarIndexer.get_collection_count()` | `--db-path`, `--collection` |

### 1.3 Data Models and Schemas

**Core Models** (`models.py`):

| Model | Lines | Purpose | Key Fields |
|-------|-------|---------|------------|
| `SectionCategory` | 12-19 | Enum for 5 section categories | `ABSTRACT_INTRO`, `METHODOLOGY`, `RESULTS_EMPIRICAL`, `DISCUSSION_LIMITATIONS`, `OTHER` |
| `MethodologyMetadata` | 91-119 | Paper methodology extraction | `paradigm`, `study_design`, `sample_size`, `evaluation_metrics`, `dataset` |
| `ChunkMetadata` | 122-168 | Rich chunk metadata for ChromaDB | `chunk_id`, `workspace_id`, `doi`, `section_hierarchy`, `methodology` |
| `Chunk` | 171-176 | Structural document chunk | `chunk_id`, `text`, `metadata` |
| `RetrievalResult` | 179-190 | Hybrid query result | `cosine_sim`, `pagerank_score`, `seed_boost`, `hybrid_score`, `citation_token` |
| `SynthesisClaim` | 193-202 | Attributed factual claim | `claim_text`, `citation_tokens`, `entailment_score/status`, `study_id`, `stance` |
| `SynthesisResult` | 205-214 | Synthesis output | `synthesis_markdown`, `claims`, `entailment_rate` |
| `MethodologyMatrixRow` | 217-226 | 7-dimension matrix row | `study_id`, `epistemological_design`, `primary_metrics_results` |
| `ClaimStance` | 229-234 | Stance polarity enum | `POSITIVE`, `NEGATIVE`, `NEUTRAL` |
| `ConsensusVerdict` | 237-243 | Verdict bucket enum | `HIGH_CONSENSUS`, `ACTIVE_DEBATE`, `UNRESOLVED`, `PROVISIONAL` |
| `ClaimGroup` | 246-255 | Evidence cluster | `cluster_id`, `theme`, `consensus_score`, `verdict` |
| `ConsensusReport` | 258-269 | Full consensus analysis | `high_consensus`, `active_debates`, `unresolved`, `provisional` |

### 1.4 Integration Points with Other Kits

| Upstream Kit | Integration Point | Mechanism |
|-------------|-------------------|-----------|
| `scholar-protocol-kit` | `matrix.py:15-16` | `build_extraction_model()` for dynamic Pydantic schemas; `ResearchProtocol` model |
| `scholar-graph-kit` | `retriever.py:54-86` | `_load_pagerank_from_graph()` consumes `graph.json` (node-link format) |
| `scholar-bib-kit` | `indexer.py:82-127` | `_load_bib_metadata()` parses BibTeX for DOI/paradigm enrichment |
| `scholar-search-kit` | `pyproject.toml:24` | Declared dependency (unused in code — possible dead dependency) |
| `scholar-pdf-kit` | Indirect via workspace | Reads extracted markdown files from `workspaces/<slug>/extracted/` |
| `scholar-verify-kit` | Schema mismatch | `SynthesisClaim` lacks `evidence_quote`/`claim_id` fields needed by `VerbatimClaimVerifier` |
| `scholar-agent-kit` | MCP tools | `nexus_rag_index/query/synthesize`, `nexus_matrix_extract` |
| `scholar-harness` | `orchestrator.py:20-23` | `ScholarIndexer`, `ScholarRetriever`, `GroundedSynthesisEngine`, `MatrixExtractor` |

### 1.5 RAG Components and Capabilities

**1. Structural AST Chunker** (`chunker.py`):
- Parses markdown heading hierarchy (`#`, `##`, `###`) with stack-based tracking
- Maintains breadcrumb context (e.g., `Introduction > Background > Transformer Models`)
- Classifies sections into 5 canonical categories via keyword matching (`models.py:22-88`)
- Enforces size guards (default 1500 chars) with sentence-boundary splitting and overlap
- Generates deterministic chunk IDs: `chk-<doc_slug>-<sec_slug>-<idx:02d>`
- Parses YAML frontmatter for metadata enrichment

**2. Idempotent Vector Indexer** (`indexer.py`):
- ChromaDB PersistentClient with HNSW cosine space
- `collection.upsert()` for guaranteed idempotent re-indexing
- BibTeX metadata enrichment via `bibtexparser` v2
- Auto-discovery of `references.bib` in adjacent directories
- Audit journal event logging (`RAG_INDEX_BUILT`)

**3. Hybrid Graph-Boosted Retriever** (`retriever.py`):
- Formula: `Score(d) = CosineSim(q, d) + alpha * PageRank(d) + beta * I_seed(d)`
- ChromaDB cosine distance `[0, 2]` converted to similarity `[0, 1]`
- Over-fetch `x4` when graph boost is active for re-ranking
- Multi-field ChromaDB where-filter construction (section, paradigm, study_design, workspace_id, DOI)
- Citation token formatting: `[workspace_id#section_slug#chunk_id]`

**4. Grounded Synthesis Engine** (`synthesis.py`):
- Deterministic bullet synthesis (no LLM required) or LLM-callable override
- Claim extraction via regex citation token pattern matching
- Automated entailment verification: cosine similarity between claim and supporting chunks
- Thresholds: VERIFIED >= 0.85, AMBIGUOUS 0.50-0.84, UNSUPPORTED < 0.50
- Lexical fallback when embedding fails (token overlap with 0.6/0.3 thresholds)

**5. Matrix Extractor** (`matrix.py`):
- Dynamic protocol dimensions from `protocol.json.matrix_dimensions`
- Per-dimension targeted retrieval scoped to study workspace_id/DOI
- Dynamic Pydantic model validation via `build_extraction_model()`
- Multi-format export: JSON, CSV, Markdown table

**6. Consensus Cartographer** (`consensus.py`):
- Greedy agglomerative clustering with configurable similarity (Jaccard or embedding cosine)
- Polarity lexicon stance classification (68 positive words, 48 negative words)
- Per-study majority-stance dedup (one vote per study)
- Verdict rules: HIGH_CONSENSUS, ACTIVE_DEBATE, UNRESOLVED, PROVISIONAL
- Deterministic and hermetic (no network required)

---

## 2. Improvements

### 2.1 Code Quality Issues

**CRITICAL — Undeclared Dependency** (`matrix.py:15-16`):
```python
from scholar_protocol.extraction import build_extraction_model
from scholar_protocol.models import ResearchProtocol
```
`scholar-protocol-kit` is imported but NOT declared in `pyproject.toml` dependencies (line 13-25). This only works because the shared `.venv` installs all kits. A standalone `pip install scholar-rag-kit` would fail on `MatrixExtractor` instantiation.

**MODERATE — Dead Parameter** (`chunker.py:23,27`):
`min_chunk_chars` is accepted in the constructor and stored as `self.min_chunk_chars` but **never referenced** in any method. The `_split_into_guarded_chunks()` method only checks `self.max_chunk_chars` and `self.overlap_chars`. The API reference (`docs/api_reference.md:13`) documents it as "Threshold for merging micro-chunks" but no merging logic exists.

**MODERATE — Bare Exception Swallowing**:
- `indexer.py:124`: `except Exception: pass` in BibTeX parsing silently discards malformed entries
- `indexer.py:161`: `except Exception: pass` in audit journal logging
- `retriever.py:74-75`: `except Exception: pass` in PageRank graph loading
- `synthesis.py:174-175`: `except Exception: pass` in LLM extraction
- `matrix.py:174-175`: `except Exception: pass` in LLM extraction

These should at minimum log warnings.

**MODERATE — Duplicate Journal Discovery Logic**:
`_find_workspace_audit_journal()` is implemented independently in 3 classes:
- `indexer.py:129-140`
- `retriever.py:133-143`
- `synthesis.py:227-243`
- `matrix.py:58-74`

Each has slightly different search root logic. Should be extracted to a shared utility.

**MODERATE — Inconsistent Error Handling in CLI**:
`cli.py:50-51` raises `typer.Exit(1)` on invalid path but other commands (query, synthesize, stats) do not validate inputs similarly.

### 2.2 Missing Features

1. **No `delete` or `rebuild` command**: No way to remove specific documents from the vector store or rebuild from scratch without deleting the entire ChromaDB directory.

2. **No batch query support**: `query()` only handles a single query text; no multi-query or batch retrieval.

3. **No query history or caching**: Repeated identical queries re-embed and re-search every time.

4. **No incremental metadata update**: Re-indexing a document with updated BibTeX metadata requires full re-processing; no partial update path.

5. **No `--verbose`/`--debug` flag**: No way to inspect intermediate chunking/retrieval decisions from CLI.

6. **No concurrent indexing**: `index_directory()` processes files sequentially; no parallel embedding.

7. **No cross-encoder reranking**: Single-stage retrieval only; the ecosystem analysis documents a planned "2-stage RAG with cross-encoder reranking" (`NEXUS_ECOSYSTEM_ANALYSIS.md:388`).

8. **No in-text citation resolution**: The chunker does not resolve `[12]`-style inline citations to BibTeX metadata. This is documented as a high-value gap (`NEXUS_ECOSYSTEM_ANALYSIS.md:284,340`).

### 2.3 API Design Improvements

1. **`ScholarRetriever.query()` parameter explosion**: 12 parameters on the query method. Consider a `QueryRequest` Pydantic model.

2. **`GroundedSynthesisEngine` coupling**: Creates its own `ScholarRetriever` if not provided, but the retriever's embedder is then used for entailment — tight coupling between retrieval and verification.

3. **`ConsensusCartographer` mutates input claims**: `analyze()` modifies `c.stance` and `c.study_id` in-place on the input list (`consensus.py:300-303`). This is a side effect that callers may not expect.

4. **`MarkdownChunker.chunk_markdown = chunk`** (`chunker.py:265`): Dead alias — never used anywhere.

### 2.4 Documentation Needs

1. **`docs/api_reference.md`** is incomplete — missing `ConsensusCartographer`, `MatrixExtractor`, `ConsensusClaim`, `ConsensusReport` models.

2. **No architecture decision records (ADRs)** explaining why Jaccard clustering was chosen over DBSCAN/HDBSCAN for consensus.

3. **No benchmarking results** documenting retrieval quality (MRR, NDCG) on sample corpora.

4. **`README.md` installation section** references `uv pip install -e .` but the canonical path is via the harness's `scripts/install_plugins.py`.

---

## 3. Problems

### 3.1 Known Bugs and Issues

**BUG 1 — Schema Impedance Mismatch with verify-kit** (`models.py:193-202`):
`SynthesisClaim` emits `claim_text`/`citation_tokens`/`entailment_status` but `scholar-verify-kit`'s `VerbatimClaimVerifier` requires `evidence_quote`/`claim_id`. Every claim returns `MISSING_QUOTE`. The kits_surface_matrix documents this as finding #6. While the MCP `nexus_verify_claims` was patched to bridge this, the Python API gap remains.

**BUG 2 — Dead `min_chunk_chars` parameter** (`chunker.py:23`):
As documented in kits_surface_matrix line 229: "`min_chunk_chars` dead". The parameter is accepted but never used in any splitting/merging logic.

**BUG 3 — `entailment_rate` default of 1.0 when no claims** (`synthesis.py:318`):
```python
entailment_rate = (verified_count / len(claims)) if claims else 1.0
```
When there are no claims, the entailment rate is reported as 100%, which is misleading. Should be 0.0 or NaN.

**BUG 4 — `_split_into_guarded_chunks` overlap inconsistency** (`chunker.py:110-111`):
The overlap logic only keeps the last sentence if `len(s_parts[-1]) <= self.overlap_chars`, but this is a character count comparison against a sentence, which may not represent semantic overlap. Additionally, paragraph-level splitting (`chunker.py:86`) does not implement any overlap at all.

### 3.2 Edge Cases Not Handled

1. **Empty documents**: `chunker.py:181-183` skips empty sections but does not handle documents with zero headings (entire text goes to "Abstract/Intro").

2. **Unicode-heavy content**: `_slugify()` (`chunker.py:31-36`) strips all non-ASCII characters, potentially losing meaningful section identifiers in non-English papers.

3. **Very large documents**: No streaming or chunked reading — `md_file.read_text(encoding="utf-8")` (`indexer.py:214`) loads entire file into memory.

4. **Concurrent ChromaDB access**: No locking mechanism — concurrent `index` and `query` from different processes could corrupt the HNSW index.

5. **BibTeX with duplicate keys**: `_load_bib_metadata()` (`indexer.py:116-122`) overwrites entries with the same key/DOI/title slug, silently losing metadata.

6. **Graph with self-loops**: `_load_pagerank_from_graph()` (`retriever.py:79`) passes the graph directly to `nx.pagerank()` without checking for self-loops.

### 3.3 Limitations

1. **Single-collection architecture**: All documents share one ChromaDB collection. No way to isolate corpora per project without separate `db_path` values.

2. **No multi-modal support**: Only markdown text is indexed; no image embedding, table structure, or code block handling.

3. **No query expansion**: Raw query text is used directly without synonym expansion, query rewriting, or HyDE.

4. **Fixed embedding dimension**: MockEmbeddingFunction hardcodes 384 dimensions; no validation that the actual embedder matches.

5. **ChromaDB dependency**: Heavy dependency (chromadb + sentence-transformers/torch); first use downloads ~90MB model. Phase 7 documentation notes this as a distribution concern.

### 3.4 Technical Debt

1. **`scholar-search-kit` declared but unused** (`pyproject.toml:24`): The dependency is listed but never imported in any source file. Dead dependency.

2. **`scholar-graph-kit` and `scholar-bib-kit` declared but only used indirectly** (`pyproject.toml:23,24`): These are only consumed through the shared venv; the RAG kit itself never imports them.

3. **Version pinned at 0.1.0**: No version bump mechanism; plugins.json pins to commit SHA but the package version is static.

4. **No type stubs for ChromaDB**: The `chromadb` import is deferred but used without type annotations.

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

**BOTTLENECK 1 — Sequential Directory Indexing** (`indexer.py:213-252`):
Files are processed one-by-one with synchronous BibTeX parsing, chunking, embedding, and upserting. For large corpora (100+ papers), this is I/O and CPU bound.

**Estimated impact**: 100 papers x ~5 chunks/paper = 500 upserts. With SentenceTransformers on CPU, embedding 500 chunks takes ~5-10 seconds. Parallelization could reduce this to ~2-3 seconds.

**BOTTLENECK 2 — Full Collection Fetch for Matrix** (`synthesis.py:351`):
```python
records = collection.get(include=["metadatas", "documents"])
```
Fetches ALL documents and metadata from ChromaDB. For large collections, this loads everything into memory. The `MatrixExtractor` does the same (`matrix.py:200`).

**BOTTLENECK 3 — O(n^2) Clustering** (`consensus.py:210-226`):
Greedy agglomerative clustering compares each new claim against all existing cluster representatives. With n claims and k clusters, this is O(n*k). For large claim sets (100+), this could be slow with embedding-based similarity.

**BOTTLENECK 4 — Repeated Embedder Initialization**:
Every CLI command creates a new `ScholarIndexer`/`ScholarRetriever`/`GroundedSynthesisEngine`, each of which initializes a new embedder and ChromaDB client. The `stats` command (`cli.py:435`) creates a full `ScholarIndexer` just to call `get_collection_count()`.

### 4.2 Memory Usage Issues

1. **`collection.get(include=["metadatas", "documents"])`** (`synthesis.py:351`, `matrix.py:200`): Loads entire corpus into memory. Should use pagination or streaming.

2. **Embedding computation**: `self.embedder(supporting_chunks_text)` (`synthesis.py:126`) computes embeddings for all supporting chunks at once. For large chunk sets, this could exhaust memory.

### 4.3 Algorithm Efficiency

1. **Clustering**: Replace greedy agglomerative with union-find or HDBSCAN for better scalability.

2. **Entailment verification**: Currently computes cosine similarity against each supporting chunk individually. Could batch-embed and compute matrix similarity.

3. **PageRank computation**: Recomputed on every query call (`retriever.py:200`). Could be cached after first computation per graph file.

### 4.4 Caching Opportunities

1. **PageRank scores**: `_load_pagerank_from_graph()` should cache computed PageRank per graph file hash.

2. **Embeddings**: Repeated queries for the same text could cache embeddings.

3. **BibTeX parsing**: `_load_bib_metadata()` parses the same file on every `index_directory()` call if invoked multiple times.

4. **ChromaDB client**: Multiple classes create separate `PersistentClient` instances for the same `db_path`. Should be shared.

### 4.5 Parallelization Potential

1. **Directory indexing**: Use `concurrent.futures.ThreadPoolExecutor` for parallel file processing (embedding is GIL-releasing in sentence-transformers).

2. **Multi-study matrix extraction**: `MatrixExtractor.extract_all()` processes studies sequentially; each study's dimension extraction is independent.

3. **Batch claim entailment**: `verify_claim_entailment()` processes claims one-by-one; batch embedding would be more efficient.

---

## 5. Scientific Correction

### 5.1 RAG Accuracy and Grounding

**Issue 1 — Entailment Score Scaling** (`synthesis.py:139`):
```python
entailment_score = max(0.0, min(1.0, (best_sim + 1.0) / 2.0))
```
This linearly maps cosine similarity `[-1, 1]` to `[0, 1]`. However, for normalized embeddings (which all providers produce), cosine similarity is already in `[0, 1]`. The `+1.0` shift means a cosine of 0.5 maps to 0.75, inflating scores. The threshold of 0.85 for "VERIFIED" is effectively a cosine threshold of ~0.70, which is quite low for semantic entailment.

**Recommendation**: Either use raw cosine similarity `[0, 1]` with adjusted thresholds, or document the mapping clearly.

**Issue 2 — Deterministic Synthesis is Shallow** (`synthesis.py:308-314`):
The non-LLM synthesis path simply concatenates cleaned snippets with citation tokens. This produces "bullet lists" rather than genuine synthesis. The `SynthesisClaim` extraction from these bullets is trivial — each bullet becomes a claim. This does not test the synthesis engine's ability to handle conflicting evidence, methodological differences, or nuanced findings.

### 5.2 Citation Correctness

**Issue 3 — Citation Token Format** (`retriever.py:123-131`):
```python
def format_citation_token(meta, chunk_id):
    ws_id = meta.get("workspace_id") or meta.get("paper_id") or meta.get("doi") or meta.get("filename", "DOC")
    sec_name = meta.get("section", "sec")
    sec_slug = re.sub(r"[^a-zA-Z0-9]", "", sec_name.lower())[:10] or "sec"
    return f"[{ws_id}#{sec_slug}#{chunk_id}]"
```
The section slug is truncated to 10 characters, which could make different sections indistinguishable (e.g., "methodology" and "methodolog" both become "methodolog"). The `chunk_id` provides uniqueness but the section component loses information.

**Issue 4 — BibTeX Matching Heuristic** (`indexer.py:222-229`):
The filename-to-BibTeX matching uses a greedy substring search (`if k in stem`), which can match false positives. A file named `paper_chen_results.md` might match a BibTeX entry with key `chen` if the stem contains the key.

### 5.3 Synthesis Quality

**Issue 5 — Claim Extraction Depends on Citation Token Presence** (`synthesis.py:175-176`):
```python
found_tokens = token_pattern.findall(unit)
if not found_tokens:
    continue
```
Claims without citation tokens are silently dropped. If the deterministic synthesis generator produces a bullet without a citation token (e.g., due to an empty snippet), the claim is lost entirely.

**Issue 6 — Study ID Attribution** (`synthesis.py:197-206`):
The first matching study ID is used as the canonical `study_id`, but a claim may cite multiple studies. This loses multi-study attribution.

### 5.4 Chunking Strategy Effectiveness

**Issue 7 — Heading-Level Splitting May Break Arguments**:
The AST chunker splits on heading boundaries, but scientific arguments often span multiple subsections. A methodology description under `## 3.1 Data Collection` may reference results from `## 4.2 Quantitative Findings`, but these will be in separate chunks with no cross-reference.

**Issue 8 — No Overlap at Paragraph Boundaries**:
The overlap mechanism (`chunker.py:110-111`) only operates within sentence-level splitting of oversized paragraphs. When a section is split across multiple chunks at paragraph boundaries (`chunker.py:123-129`), there is NO overlap between chunks. This can lose context at chunk boundaries.

### 5.5 Academic Rigor

**Issue 9 — Consensus Verdicts are Study-Count Based** (`consensus.py:252-281`):
Verdicts are derived from the number of studies holding each stance, not from the statistical significance or methodological quality of those studies. A single well-powered RCT should carry more weight than ten underpowered observational studies, but the current system treats them equally.

**Issue 10 — No Confidence Intervals or Effect Sizes**:
The methodology matrix extracts point values but no uncertainty estimates. A proper academic synthesis should report confidence intervals, effect sizes, or at minimum flag when quantitative data is missing.

---

## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent Be Created?

**YES** — A specialized `scholar-rag-agent` (or enhanced skill) is strongly recommended. The rationale:

**Narrow Scope**: The kit performs 6 distinct operations (index, query, synthesize, consensus, matrix, stats) with well-defined inputs/outputs. This is an ideal candidate for an agent that can chain these operations.

**Evaluation Metrics Available**:
1. **Indexing quality**: Chunk count, average chunk size, section coverage distribution
2. **Retrieval quality**: MRR@k, NDCG@k, Precision@k (against ground truth queries)
3. **Synthesis quality**: Entailment rate, claim count, citation token coverage
4. **Consensus quality**: Cluster coherence (intra-cluster similarity), verdict stability across thresholds
5. **Matrix completeness**: Fill rate per dimension, fallback value usage

### 6.2 Critic Capabilities Needed

1. **Retrieval Critic**: Evaluate whether retrieved chunks actually answer the query (relevance judgment).
2. **Synthesis Critic**: Check that synthesis claims are genuinely derived from evidence, not paraphrased noise.
3. **Consensus Critic**: Validate that stance classification is accurate (false positive/negative detection).
4. **Matrix Critic**: Verify extracted dimensions against source text (hallucination detection).

### 6.3 Agent-in-the-Loop Opportunities

1. **Query Expansion Agent**: Before retrieval, an LLM rewrites the query with synonyms and related concepts.
2. **Claim Verification Agent**: After synthesis, an LLM reviews each claim against its cited chunks for accuracy.
3. **Threshold Tuning Agent**: Sweeps clustering thresholds and reports optimal values for the specific corpus.
4. **Quality Gate Agent**: After indexing, checks chunk quality (size distribution, section coverage, metadata completeness).

### 6.4 Automation Potential

1. **Auto-indexing trigger**: Watch for new files in `extracted/` and auto-index.
2. **Incremental synthesis**: After new papers are indexed, auto-generate updated synthesis for each RQ.
3. **Consensus drift detection**: Monitor how consensus shifts as new evidence is added.
4. **Matrix gap filling**: Identify missing dimensions and trigger targeted retrieval.

### 6.5 Proposed Skill Design

```
Skill: scholar-rag-agent
Scope: End-to-end RAG pipeline management
Trigger: "Index and synthesize [topic]" or "Update RAG for [workspace]"
Steps:
  1. Validate workspace state (extracted files exist, bib file present)
  2. Index with optimal chunker settings
  3. Run quality checks (chunk distribution, metadata completeness)
  4. For each RQ in protocol.json:
     a. Execute hybrid retrieval with graph boost
     b. Generate grounded synthesis
     c. Verify claim entailment
     d. Run consensus cartography (if multiple RQs)
  5. Generate methodology matrix
  6. Log all events to audit journal
  7. Return quality metrics summary
Evaluation:
  - Entailment rate >= 80%
  - All RQs have synthesis output
  - Matrix has no more than 20% fallback values
  - Audit journal has all expected events
```

---

## 7. Priority-Ranked Improvement Suggestions

### Priority 1 (Critical — Fix Immediately)

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 1 | Undeclared `scholar-protocol-kit` dependency | `pyproject.toml:13-25` | Add `scholar-protocol-kit` to dependencies |
| 2 | Dead `min_chunk_chars` parameter | `chunker.py:23` | Remove parameter or implement micro-chunk merging |
| 3 | `entailment_rate = 1.0` when no claims | `synthesis.py:318` | Change to `0.0` |
| 4 | Schema mismatch with verify-kit | `models.py:193-202` | Add `evidence_quote`/`claim_id` fields to `SynthesisClaim` |

### Priority 2 (High — Fix Before Next Release)

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 5 | Extract `_find_workspace_audit_journal()` to shared utility | `indexer.py`, `retriever.py`, `synthesis.py`, `matrix.py` | Create `utils.py` with shared journal discovery |
| 6 | Replace bare `except Exception: pass` with logging | Multiple files | Use `logging.warning()` with context |
| 7 | Document entailment score scaling formula | `synthesis.py:139` | Add docstring explaining `[-1,1] -> [0,1]` mapping |
| 8 | Remove dead `scholar-search-kit` dependency | `pyproject.toml:24` | Remove unused dependency |
| 9 | Fix `ConsensusCartographer` input mutation | `consensus.py:300-303` | Deep-copy claims before modifying |

### Priority 3 (Medium — Planned Improvements)

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 10 | Add overlap at paragraph chunk boundaries | `chunker.py:123-129` | Implement configurable paragraph overlap |
| 11 | Cache PageRank computation per graph | `retriever.py:54-86` | Add lru_cache keyed on graph file hash |
| 12 | Batch embedding for entailment verification | `synthesis.py:123-148` | Batch-embed claim + chunks in single call |
| 13 | Add `delete`/`rebuild` CLI commands | `cli.py` | Implement collection management |
| 14 | Complete `api_reference.md` | `docs/api_reference.md` | Add ConsensusCartographer, MatrixExtractor docs |

### Priority 4 (Low — Future Enhancements)

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| 15 | Implement in-text citation resolution | `chunker.py` | Add `CitationsResolver` module |
| 16 | Add cross-encoder reranking | `retriever.py` | 2-stage retrieval with cross-encoder |
| 17 | Parallel directory indexing | `indexer.py:213-252` | Use ThreadPoolExecutor |
| 18 | Add query expansion | `retriever.py` | LLM-based query rewriting |
| 19 | Multi-modal chunk support | `chunker.py` | Handle tables, code, images |

---

## Appendix A: Test Coverage Analysis

| Test File | Tests | Lines | Coverage Area |
|-----------|-------|-------|---------------|
| `test_chunker.py` | 5 | 108 | Section classification, hierarchy, deterministic IDs, size guards, frontmatter |
| `test_indexer.py` | 2 | 76 | Idempotent upsert, directory indexing with BibTeX |
| `test_retriever.py` | 3 | 95 | Section filter, paradigm filter, hybrid graph boost |
| `test_embedder.py` | 2 | 26 | Mock embedder determinism, factory validation |
| `test_synthesis.py` | 2 | 76 | Synthesis generation, methodology matrix |
| `test_consensus.py` | 12 | 288 | Tokenization, similarity, stance, clustering, verdicts, rendering, CLI |
| `test_cli.py` | 1 | 71 | End-to-end CLI flow |
| `test_matrix.py` | 2 | 113 | Dynamic matrix extraction, CLI matrix command |
| **Total** | **29** | **953** | |

**Missing Test Coverage**:
- No test for empty documents or zero-heading documents
- No test for concurrent access
- No test for large document sets (performance regression)
- No test for Unicode-heavy content
- No test for BibTeX parsing edge cases (malformed entries, duplicate keys)
- No test for `ScholarRetriever.query()` with `log_journal=True` (audit path)
- No test for `GroundedSynthesisEngine` with LLM callable
- No test for `MatrixExtractor` with LLM callable
- No test for `ConsensusCartographer` with semantic similarity scorer on real embeddings

---

## Appendix B: File Size and Complexity Metrics

| Module | Lines | Functions/Classes | Max Complexity |
|--------|-------|-------------------|----------------|
| `cli.py` | 443 | 6 commands | Medium (Typer routing) |
| `synthesis.py` | 415 | 4 functions + 1 class | High (entailment verification) |
| `consensus.py` | 400 | 7 functions + 1 class | High (clustering + verdicts) |
| `retriever.py` | 281 | 5 methods + 1 class | High (hybrid scoring) |
| `matrix.py` | 272 | 4 methods + 1 class | Medium (dimension extraction) |
| `chunker.py` | 265 | 6 methods + 1 class | Medium (AST parsing) |
| `indexer.py` | 267 | 6 methods + 1 class | Medium (BibTeX + indexing) |
| `models.py` | 269 | 12 models + 1 function | Low (data definitions) |
| `embedder.py` | 115 | 3 functions + 1 class | Low (factory pattern) |

---

## Appendix C: Cross-Kit Dependency Issues

```
scholar-rag-kit
  ├── DECLARES: typer, rich, chromadb, sentence-transformers, openai, networkx, pydantic, bibtexparser
  ├── DECLARES: scholar-graph-kit, scholar-bib-kit, scholar-search-kit (unused in code)
  ├── IMPORTS BUT DOES NOT DECLARE: scholar-protocol-kit (matrix.py:15-16)
  └── SCHEMA MISMATCH: scholar-verify-kit (SynthesisClaim vs VerbatimClaimVerifier)
```

The undeclared `scholar-protocol-kit` dependency is the most critical packaging issue. The `scholar-search-kit` declaration is dead weight that should be removed. The `scholar-graph-kit` and `scholar-bib-kit` declarations are technically correct (used indirectly through shared venv) but not imported directly in RAG kit code.


---

<!-- Source: kit_06_graph.md -->
﻿# Scholar Graph Kit — Comprehensive Deep-Dive Analysis

**Kit Path:** C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-graph-kit
**Entry Point:** scholar_graph.cli:app (console script scholar-graph)
**Version:** 0.1.0
**Dependencies:** networkx>=3.0, pyvis>=0.3.2, typer>=0.9.0, rich>=13.0.0, aiohttp>=3.9.0, pydantic>=2.0.0, scholar-search-kit

---

## Table of Contents

1. Executive Summary
2. Dimension 1: Functionalities
3. Dimension 2: Improvements
4. Dimension 3: Problems
5. Dimension 4: Optimizations
6. Dimension 5: Scientific Correction
7. Dimension 6: Agent/Skill Recommendation
8. Priority-Ranked Improvement Suggestions

---

## 1. Executive Summary

The scholar-graph-kit is a **minimal but functional** bibliometric graph construction and visualization engine. It has exactly **four source files** (excluding __init__.py):

| File | Lines | Role |
|------|-------|------|
| models.py | 14 | Dataclasses (GraphNode, GraphEdge) — **DEAD CODE** |
| config.py | 9 | Pydantic Settings — **DEAD CODE** |
| uilder.py | 130 | Core: CitationGraphBuilder (fetch, build, PageRank, export) |
| isualizer.py | 59 | GraphVisualizer (PyVis HTML generation) |
| cli.py | 125 | Typer CLI (build, pagerank commands) |

**Strengths:**
- Clean async OpenAlex integration via AcademicHttpClient
- NetworkX DiGraph backbone with standard node-link JSON export
- PyVis interactive HTML with physics-based layout
- PageRank normalization to [0, 1] at 4 decimal places
- Orchestrator integration as Stage 8 of the full pipeline

**Critical Weaknesses:**
- ~50% of the kit is dead code (models.py, config.py)
- Documentation (tutorial.md, api_reference.md) describes classes that do NOT exist (GraphBuilder, NetworkAnalyzer, GraphData, NodeMetadata)
- Only citation edges — no co-citation, bibliographic coupling, or scientometric analysis
- Only one export format (PyVis HTML) — no GEXF, GraphML, or Cytoscape JSON
- All error handling is silent (except Exception: pass)
- No CLI command for analyzing graph structure, communities, or centrality

---

## 2. Dimension 1: Functionalities

### 2.1 Complete Feature Inventory

| # | Feature | Status | Location |
|---|---------|--------|----------|
| 1 | Fetch work metadata from OpenAlex API | Implemented | builder.py:15-26 |
| 2 | Build directed citation graph from DOIs | Implemented | builder.py:28-100 |
| 3 | Parse included.json for DOIs | Implemented | cli.py:40-52 |
| 4 | Compute normalized PageRank | Implemented | builder.py:102-114 |
| 5 | Export node-link JSON + PageRank | Implemented | builder.py:116-130 |
| 6 | PyVis HTML visualization | Implemented | visualizer.py:13-59 |
| 7 | CLI build command | Implemented | cli.py:29-91 |
| 8 | CLI pagerank command | Implemented | cli.py:94-121 |
| 9 | Fallback nodes for unindexed DOIs | Implemented | builder.py:85-98 |
| 10 | Co-citation analysis | NOT IMPLEMENTED | — |
| 11 | Bibliographic coupling | NOT IMPLEMENTED | — |
| 12 | HITS (Hubs and Authorities) | NOT IMPLEMENTED | — |
| 13 | Louvain community detection | NOT IMPLEMENTED | — |
| 14 | K-core decomposition | NOT IMPLEMENTED | — |
| 15 | GEXF export | NOT IMPLEMENTED | — |
| 16 | GraphML export | NOT IMPLEMENTED | — |
| 17 | Cytoscape JSON export | NOT IMPLEMENTED | — |
| 18 | Temporal citation dynamics | NOT IMPLEMENTED | — |
| 19 | Edge weighting / TF-based scoring | NOT IMPLEMENTED | — |
| 20 | CLI export command | NOT IMPLEMENTED | — |
| 21 | CLI analyze command | NOT IMPLEMENTED | — |
| 22 | CLI cluster command | NOT IMPLEMENTED | — |

### 2.2 CLI Commands to Functions Mapping

scholar-graph build -> cli.py:build() -> CitationGraphBuilder.build_graph() -> GraphVisualizer.generate_html() -> CitationGraphBuilder.export_json()

scholar-graph pagerank <graph_file> -> cli.py:pagerank() -> reads JSON "pagerank" key -> Rich table display

### 2.3 Data Models and Schemas

**Defined but unused** (models.py:3-14):

GraphNode dataclass with doi, title, year, citations, group fields.
GraphEdge dataclass with source, target fields.

**Actual in-use schema** (NetworkX node attributes in builder.py:63-70):

Per-node dict stored on nx.DiGraph with: doi_clean (node ID), title (work title), year (publication year), citations (cited_by_count), group (cluster coloring, always 1), label (truncated title, 30 chars for PyVis).

**Export schema** (builder.py:126-129):

JSON with nodes (node_link_data format), links (directed edges), directed (true), pagerank (normalized to max 1.0).

**Config schema** (config.py:3-8):

Settings with openalex_email (NOT USED, no polite-pool) and max_concurrent_requests (NOT USED, unbounded).

### 2.4 Integration Points with Other Kits

| Integration | Direction | Location | Status |
|-------------|-----------|----------|--------|
| scholar-search-kit (AcademicHttpClient) | inbound | builder.py:9,12, cli.py:64 | Working |
| scholar-search-kit (included.json) | inbound | cli.py:40-52 | Working |
| scholar-rag-kit (graph.json pagerank) | outbound | builder.py:127 | Working |
| scholar-agent-kit (MCP nexus_graph_build) | inbound | server.py:535-571 | Was broken, now fixed |
| scholar-harness orchestrator (Stage 8) | inbound | orchestrator.py:648-662 | Working |

---

## 3. Dimension 2: Improvements

### 3.1 Code Quality Issues

#### 3.1.1 Dead Code — models.py (14 lines entirely dead)

**File:** src/scholar_graph/models.py:1-14

The GraphNode and GraphEdge dataclasses are never imported by any module in the kit. The actual graph nodes are plain dicts on nx.DiGraph. This file exists only as historical residue.

**Impact:** Misleading; new contributors will import GraphNode thinking it is the canonical model.

**Recommendation:** Delete the file entirely, or replace with a Pydantic model that matches the actual NetworkX node dict.

#### 3.1.2 Dead Code — config.py (9 lines entirely dead)

**File:** src/scholar_graph/config.py:1-9

Settings is instantiated as module-level settings = Settings() but never referenced by builder.py, visualizer.py, or cli.py. The openalex_email setting (intended for polite-pool) is never sent in API requests. max_concurrent_requests is ignored — builder.py uses asyncio.as_completed with no semaphore.

**Impact:** Wasted dependency on pydantic-settings; unbounded concurrency may hit OpenAlex rate limits.

#### 3.1.3 Silent Exception Swallowing

**File:** src/scholar_graph/builder.py:24-25

Every OpenAlex fetch failure is silently consumed. A network error, a 429 rate-limit, or a malformed JSON response all produce the same result: the DOI vanishes from the graph with zero diagnostic output.

**File:** src/scholar_graph/cli.py:19

Windows UTF-8 reconfiguration failures are silently ignored (acceptable for Windows compat, but should log a warning).

#### 3.1.4 CLI Mutates Graph Node Attributes During Render

**File:** src/scholar_graph/cli.py:68-81

The build command calls vis.generate_html(G) which mutates G.nodes[data] by adding value (for sizing) and title (for tooltips) — see visualizer.py:19-22. Then builder.export_json(G, ...) serializes the mutated graph. This means the exported JSON contains PyVis-specific attributes (value, title) that pollute the pure node-link structure.

**Documented in SKILL.md:** "CLI build renders HTML before exporting JSON — the JSON written by the CLI carries PyVis node attributes."

#### 3.1.5 Tutorial and API Reference Are Stale

**File:** docs/tutorial.md:9-45

References scholar-bib build --doi (wrong CLI name), GraphBuilder, NetworkAnalyzer, export_html() — none of which exist in the current code.

**File:** docs/api_reference.md:1-44

References GraphBuilder(provider="openalex"), NetworkAnalyzer, GraphData, NodeMetadata — classes that do NOT exist. Describes calculate_centrality() which does not exist.

### 3.2 Missing Features

1. No graph export beyond HTML — no GEXF, GraphML, or Cytoscape JSON (planned in Ecosystem Analysis Phase A)
2. No scientometric modes — no co-citation, bibliographic coupling, or hybrid similarity (planned in Phase B)
3. No network analysis CLI — no analyze, cluster, or export commands
4. No progress reporting — progress_callback in build_graph is called but never actually reports (the callback in cli.py:69-70 is a no-op pass)
5. No caching — repeated builds re-fetch all DOIs from OpenAlex
6. No rate limiting — no asyncio.Semaphore despite config.max_concurrent_requests
7. No polite-pool email — OpenAlex recommends sending mailto for higher rate limits

### 3.3 API Design Improvements

1. CitationGraphBuilder requires AcademicHttpClient but has no default — the MCP tool previously passed None. A factory method or optional default would prevent this.
2. compute_pagerank is a @staticmethod that takes G as an argument but is always called as CitationGraphBuilder.compute_pagerank(G) after build_graph. It should be an instance method or called automatically.
3. export_json is a @staticmethod but is called as builder.export_json(...) — inconsistent with the static decorator.
4. No __all__ export in __init__.py — the public API is not explicitly declared.

### 3.4 Error Handling Gaps

1. No validation of DOI format — malformed DOIs silently produce no graph nodes
2. No timeout on OpenAlex requests — a hanging connection blocks the entire build
3. No retry on transient failures — 429/503 responses are silently swallowed
4. No graph size limits — a 10,000-DOI list would fire 10,000 concurrent HTTP requests
5. pagerank command silently returns empty table if file has no "pagerank" key — no error
6. build_graph does not validate that returned referenced_works are valid OpenAlex work IDs

### 3.5 Documentation Needs

| Document | Issue | Severity |
|----------|-------|----------|
| docs/tutorial.md | References nonexistent GraphBuilder, NetworkAnalyzer, scholar-bib build | Critical |
| docs/api_reference.md | References nonexistent GraphBuilder, NetworkAnalyzer, GraphData, NodeMetadata | Critical |
| README.md | Mostly accurate but says "Co-Citation" in description (not implemented) | Medium |
| SKILL.md | Accurate and well-maintained | OK |
| Inline docstrings | build_graph, compute_pagerank, export_json have minimal docstrings | Low |

---

## 4. Dimension 3: Problems

### 4.1 Known Bugs and Issues

#### Bug 1: MCP nexus_graph_build Was Broken (Now Fixed)

Historical: The MCP tool previously constructed CitationGraphBuilder(http_client=None), causing every OpenAlex fetch to fail silently, producing a graph of isolated fallback nodes with uniform PageRank 1.0.

Status: Fixed in server.py:548 — now creates AcademicHttpClient(name="openalex-graph", rate_limit=10).

#### Bug 2: Unbounded Concurrency

**File:** builder.py:36-40

All DOIs are fetched concurrently with no semaphore. For 500 DOIs, this fires 500 simultaneous HTTP requests. OpenAlex rate limits are ~10 requests/second for polite pool, ~1/second without email. This WILL trigger 429s.

#### Bug 3: PageRank Error Falls Back to Uniform 1.0

**File:** builder.py:113-114

If nx.pagerank fails (e.g., on an empty graph or a graph with only self-loops), all nodes get identical PageRank 1.0 — making the metric meaningless. The error is silently swallowed.

#### Bug 4: DOI Cleaning Does Not Handle All Cases

**File:** builder.py:55

Does not handle doi: prefix, uppercase DOI, or URLs with path fragments. Only handles the two https://doi.org/ and http://doi.org/ prefixes.

#### Bug 5: Edge Direction May Be Counterintuitive

**File:** builder.py:79-83

Edge is source -> target where source is the citing paper and target is the cited paper. This means edges point FROM the newer paper TO the older paper it cites. While technically correct for a citation graph, this is counterintuitive for PageRank (the cited paper receives the rank, but edges point away from it). NetworkX pagerank on a DiGraph treats incoming edges as "votes for" — so the cited paper gets rank from being pointed AT. This is correct.

#### Bug 6: group Field Always 1

**File:** builder.py:68 and builder.py:96

The group attribute is always hardcoded to 1. No clustering or community detection is performed. The PyVis visualization uses this for coloring, so all nodes have the same color.

### 4.2 Edge Cases Not Handled

1. Empty input list — build_graph([]) returns an empty graph (correct but no warning)
2. All DOIs fail to resolve — returns graph with only fallback nodes, no edges
3. Self-citing papers — filtered by source_doi != target_doi check (correct)
4. Duplicate DOIs in input — deduplicated by list if doi not in doi_list in CLI, but build_graph does not deduplicate
5. DOIs with trailing slashes or fragments — not cleaned
6. Very large graphs — PyVis HTML can become very large (500+ nodes); no pagination or filtering
7. Graph with zero edges — PageRank returns all 1.0; the pagerank CLI shows this without warning

### 4.3 Limitations in Current Implementation

1. Intra-pool edges only — only edges between papers that are BOTH in the input DOI list. No expansion to referenced works outside the pool. This means the graph is sparse for small input sets.
2. No edge weighting — all citation edges are binary (present/absent). No weighting by co-citation strength, bibliographic coupling overlap, or recency.
3. Single data source — OpenAlex only. No Semantic Scholar, Crossref, or PubMed citation data.
4. No incremental builds — cannot add new DOIs to an existing graph; must rebuild from scratch.
5. No graph persistence — the graph exists only in memory; must export to JSON for reuse.

### 4.4 Technical Debt

1. Dead files (models.py, config.py) should be removed
2. Stale documentation (tutorial.md, api_reference.md) should be rewritten
3. pydantic-settings dependency is unnecessary if config.py is removed
4. No type hints on export_json return — returns Path but signature says str | Path
5. compute_pagerank normalization divides by max(pr.values()) — this means the most central node always gets 1.0, which is fine for relative ranking but loses absolute scale information

---

## 5. Dimension 4: Optimizations

### 5.1 Performance Bottlenecks

#### Bottleneck 1: Unbounded HTTP Concurrency

**File:** builder.py:36-40

Impact: For N DOIs, fires N concurrent requests. OpenAlex will 429 after ~10 requests without polite pool.

Fix: Add asyncio.Semaphore(settings.max_concurrent_requests):

    sem = asyncio.Semaphore(settings.max_concurrent_requests)
    async def limited_fetch(doi):
        async with sem:
            return await self.fetch_work_data(doi)
    tasks = [limited_fetch(doi) for doi in dois]

#### Bottleneck 2: Sequential Edge Resolution

**File:** builder.py:72-83

Edges are added in a Python for loop over works_data. For large graphs (1000+ nodes), this is O(N*R) where R is average references per work. NetworkX add_edge is O(1) amortized, so this is fine for typical systematic review sizes (<500 papers).

#### Bottleneck 3: PyVis HTML Rendering for Large Graphs

**File:** visualizer.py:13-59

PyVis generates a self-contained HTML file with inline JavaScript. For 1000+ nodes, the HTML file can exceed 10MB. No options for: Node filtering, Lazy loading, Subgraph extraction, Static image export.

### 5.2 Memory Usage Issues

**File:** builder.py:28-100

build_graph keeps ALL works_data (raw OpenAlex JSON) in memory alongside the NetworkX graph. For 500 papers, each with full OpenAlex metadata, this could be 50-100MB of raw JSON plus the graph structure.

**Recommendation:** Process and discard raw data incrementally.

### 5.3 Caching Opportunities

1. DOI metadata caching — OpenAlex work metadata changes rarely. Cache by OpenAlex work ID with TTL.
2. Graph JSON caching — if input DOIs have not changed, skip rebuild entirely.
3. PageRank caching — recompute only if graph structure changed.

### 5.4 Parallelization Potential

1. Edge resolution — the current asyncio.as_completed is good for I/O-bound fetching but edge construction is CPU-bound for large graphs. Could use concurrent.futures.ProcessPoolExecutor for graph construction.
2. PageRank — NetworkX pagerank is single-threaded. For very large graphs, use scipy.sparse implementation.

---

## 6. Dimension 5: Scientific Correction

### 6.1 PageRank Implementation Accuracy

**File:** builder.py:103-114

**Assessment:**

- The alpha=0.85 damping factor is the standard PageRank default (Brin and Page, 1998). **Correct.**
- Normalization by max(pr.values()) scales to [0, 1]. This is a valid normalization but loses absolute scale. For academic use, relative ranking is typically sufficient. **Acceptable.**
- Keys are lowercased (k.lower()). DOIs are case-insensitive, so this is correct for DOI-keyed graphs. **Correct.**
- Rounding to 4 decimal places provides sufficient precision for ranking. **Correct.**

**Potential Issue:** If the graph is disconnected (multiple weakly connected components), PageRank distributes rank proportional to component size. Small components get less total rank. This is standard behavior but may surprise users.

### 6.2 Citation Network Analysis

**Edge Direction:** source -> target where source cites target. In a citation graph, this means:

- pagerank assigns higher rank to papers that are cited by many high-rank papers
- This correctly identifies influential papers in the citation network
- This is standard academic practice.

**Limitation:** Only direct citation edges are captured. No:

- Co-citation similarity (papers cited together)
- Bibliographic coupling (papers sharing references)
- Bibliometric coupling strength

### 6.3 Academic Impact Metrics

The kit currently provides:

1. PageRank — measures structural importance in the citation network
2. Citation count (cited_by_count from OpenAlex) — raw impact measure

**Missing metrics that would be valuable:**

1. HITS Hubs/Authorities — distinguishes review papers (hubs) from empirical breakthroughs (authorities)
2. Betweenness centrality — identifies papers bridging sub-disciplines
3. In-degree / Out-degree — basic citation metrics
4. h-index of cited papers — aggregate impact of references
5. Citation velocity — citations per year (emerging vs. declining)
6. Co-citation clustering — thematic groupings

### 6.4 Visualization Accuracy

**File:** visualizer.py:19-22

**Assessment:**

- Node size is proportional to citation count + 5 (base). This means a paper with 0 citations still has visible size. **Reasonable.**
- No PageRank-based sizing — the most structurally important paper may not be the most visually prominent. **Missed opportunity.**
- Tooltip shows DOI, title, year, and citations. **Good.**
- No color coding by year, community, or any metric. **Missing.**

**Physics layout** (visualizer.py:29-55):

- Uses forceAtlas2Based solver with reasonable parameters
- gravitationalConstant: -50 (moderate repulsion)
- springLength: 100, springConstant: 0.08 (moderate attraction)
- Assessment: Reasonable defaults for academic citation networks. No major issues.

---

## 7. Dimension 6: Agent/Skill Recommendation

### 7.1 Should a Specialized Agent or Skill Be Created?

**Current SKILL.md exists** at .agents/skills/scholar-graph-kit/SKILL.md (100 lines). It is well-maintained and accurate.

**Recommendation: YES, a dedicated skill should be expanded, but a full agent is NOT warranted.**

**Rationale:**

| Factor | Assessment |
|--------|------------|
| Task scope | Narrow (graph build + visualize + PageRank) |
| Task frequency | Low (typically once per systematic review) |
| Agent-in-the-loop potential | LOW — the graph build is fully automated |
| Evaluation metrics needed | YES — graph quality metrics would be valuable |
| Critic capabilities | MODERATE — could validate graph structure |
| Automation potential | HIGH — currently automated in orchestrator Stage 8 |

### 7.2 Evaluation Metrics for Agent Assessment

An agent evaluating scholar-graph-kit output should check:

| Metric | Definition | Threshold | Location to Check |
|--------|-----------|-----------|-------------------|
| graph.node_count | Number of nodes in graph | > 0 | G.number_of_nodes() |
| graph.edge_count | Number of edges in graph | > 0 (if >1 DOI) | G.number_of_edges() |
| graph.density | Edges / (N*(N-1)) | Varies | nx.density(G) |
| graph.weakly_connected | Single connected component? | Preferred | nx.is_weakly_connected(G) |
| graph.pagerank_range | Min to max PageRank | [0, 1] | min/max of pr values |
| graph.pagerank_unique | All scores unique? | Yes | len(set(pr.values())) == len(pr) |
| graph.has_fallback_nodes | Nodes with title="Study <doi>" | Count | Check node titles |
| graph.doi_coverage | Input DOIs present in graph | 100% | Check all input DOIs as nodes |
| html.file_size | Size of generated HTML | < 10MB | Path(html).stat().st_size |
| html.contains_nodes | HTML has node data | True | Parse HTML content |
| json.has_pagerank | JSON export has "pagerank" key | True | Check JSON structure |

### 7.3 Critic Capabilities Needed

An agent critic for scholar-graph-kit should:

1. Validate input quality — check that DOIs are well-formed, included.json has the expected schema
2. Validate output structure — verify graph JSON has nodes, links, and pagerank keys
3. Flag sparse graphs — if edges/nodes < 0.5, warn that the graph may not be informative
4. Detect fallback nodes — count nodes with title="Study <doi>" and report what fraction of input DOIs were unresolvable
5. Check PageRank sanity — verify that the most-cited paper has high PageRank (if not, investigate graph structure)
6. Compare across runs — if the same DOIs are built twice, the graph should be deterministic

### 7.4 Agent-in-the-Loop Opportunities

The current scholar-graph-kit is fully automated — no agent-in-the-loop is needed for the core workflow. However, the following agent interactions could be valuable:

1. Graph interpretation agent — after graph build, an agent could analyze the structure and explain which papers are most central and why
2. Community detection agent — an agent could run Louvain clustering and explain the thematic groups
3. Anomaly detection agent — an agent could flag unusual citation patterns (e.g., a paper citing a much newer paper, which suggests data issues)

### 7.5 Automation Potential

| Workflow Step | Current | Automated? | Agent Needed? |
|---------------|---------|-----------|---------------|
| DOI list from included.json | CLI --input | Yes | No |
| OpenAlex metadata fetch | build_graph | Yes | No |
| Graph construction | build_graph | Yes | No |
| PageRank computation | compute_pagerank | Yes | No |
| JSON export | export_json | Yes | No |
| HTML visualization | generate_html | Yes | No |
| Graph quality validation | None | No | Yes |
| Graph interpretation | None | No | Yes |
| Community analysis | None | No | Yes |

---

## 8. Priority-Ranked Improvement Suggestions

### Priority 1 (Critical — Fix Now)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 1.1 | Delete dead code (models.py, config.py) | Reduces confusion | 5 min | models.py, config.py |
| 1.2 | Add asyncio.Semaphore to bound concurrency | Prevents 429 errors | 30 min | builder.py:36-40 |
| 1.3 | Fix stale documentation | Prevents user errors | 1 hr | docs/tutorial.md, docs/api_reference.md |
| 1.4 | Add error logging to fetch_work_data | Enables debugging | 15 min | builder.py:24-25 |
| 1.5 | Fix CLI render-before-export mutation | Clean JSON output | 30 min | cli.py:75-91 |

### Priority 2 (High — Next Sprint)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 2.1 | Add GEXF/GraphML export (export CLI command) | Enables Gephi/VOSviewer | 2 hr | New exporters.py, cli.py |
| 2.2 | Add co-citation network mode | Scientometric analysis | 4 hr | New scientometrics.py |
| 2.3 | Add bibliographic coupling mode | Scientometric analysis | 4 hr | New scientometrics.py |
| 2.4 | Add HITS (Hubs/Authorities) analysis | Hub vs authority distinction | 2 hr | builder.py or new module |
| 2.5 | Add DOI format validation | Prevents silent failures | 30 min | builder.py |

### Priority 3 (Medium — Backlog)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 3.1 | Add Louvain community detection | Thematic clustering | 2 hr | New module |
| 3.2 | Add analyze CLI command | Graph structure insights | 2 hr | cli.py |
| 3.3 | Add node coloring by PageRank/community | Better visualization | 1 hr | visualizer.py |
| 3.4 | Add DOI metadata caching | Faster rebuilds | 3 hr | builder.py |
| 3.5 | Add progress reporting (tqdm/rich) | Better UX | 1 hr | cli.py, builder.py |

### Priority 4 (Low — Nice to Have)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 4.1 | Add polite-pool email support | Higher OpenAlex rate limits | 15 min | config.py, builder.py |
| 4.2 | Add incremental graph builds | Efficiency for large reviews | 4 hr | builder.py |
| 4.3 | Add static image export (PNG/SVG) | Publication-ready figures | 3 hr | New module |
| 4.4 | Add graph diff/comparison | Track changes across runs | 4 hr | New module |
| 4.5 | Replace models.py with Pydantic models | Type safety | 2 hr | models.py |

---

## Appendix A: File Inventory

| File | Lines | Status |
|------|-------|--------|
| src/scholar_graph/__init__.py | 1 | Empty module docstring only |
| src/scholar_graph/models.py | 14 | DEAD — never imported |
| src/scholar_graph/config.py | 9 | DEAD — never used |
| src/scholar_graph/builder.py | 130 | Core logic — needs semaphore + logging |
| src/scholar_graph/visualizer.py | 59 | Working — needs coloring + exports |
| src/scholar_graph/cli.py | 125 | Working — needs export/analyze commands |
| tests/test_builder.py | 55 | Minimal — needs edge cases |
| tests/test_cli.py | 42 | Minimal — needs error path tests |
| tests/test_visualizer.py | 20 | Minimal — needs content checks |
| docs/tutorial.md | 45 | STALE — references nonexistent classes |
| docs/api_reference.md | 44 | STALE — references nonexistent classes |
| README.md | 100 | Mostly accurate |
| pyproject.toml | 35 | Clean |
| map.html | 222 | Generated artifact (PyVis template) |

**Total source code:** 319 lines (including dead code)
**Total test code:** 117 lines
**Test coverage:** Minimal — 3 test files, no edge-case or error-path coverage

---

## Appendix B: Integration Dependency Graph

    scholar-search-kit (AcademicHttpClient)
            |
            v
    scholar-graph-kit
      builder.py -----> nx.DiGraph (networkx)
      visualizer.py --> PyVis (pyvis)
      cli.py ---------> Typer + Rich
            |
            v
    scholar-rag-kit (reads graph.json pagerank key)
    scholar-agent-kit (MCP nexus_graph_build tool)
    scholar-harness (orchestrator Stage 8)

---

## Appendix C: Cross-References to Ecosystem Analysis

| Ecosystem Feature | Kit Module | Status | Priority |
|-------------------|-----------|--------|----------|
| GEXF/GraphML Exporters | visualizer.py / new exporters.py | Phase A | P1 |
| Co-Citation and Coupling | new scientometrics.py | Phase B | P1 |
| HITS Hubs/Authorities | builder.py | Phase B | P2 |
| Louvain Community Detection | new module | Phase B | P2 |
| K-Core Decomposition | new module | Phase B | P2 |
| Temporal Citation Dynamics | new module | Phase C | P3 |
| Cytoscape.js JSON | visualizer.py | Phase A | P2 |

---

Analysis generated on 2026-09-14 by deep-dive review of tools/scholar-graph-kit/ source, tests, docs, and ecosystem cross-references.

---

<!-- Source: kit_07_agent.md -->
﻿# scholar-agent-kit — Comprehensive Deep Dive Analysis

**Kit:** `scholar-agent-kit` (`tools/scholar-agent-kit/`)
**Version:** 0.1.0
**Source files:** 2 modules (`server.py` = 1257 lines, `calibration.py` = 467 lines)
**Test files:** 2 test modules (`test_server.py` = 151 lines, `test_calibration.py` = 218 lines) + 3 harness-level test modules (`test_mcp_recon.py` = 666 lines, `test_mcp_tools_graph.py` = 619 lines, `conformance/test_mcp_tool_parity.py` = 34 lines)
**Total LOC (kit source):** ~1724 lines
**Date of analysis:** 2026-09-14

---

## Executive Summary

`scholar-agent-kit` is the **MCP front-door** for the entire Nexus Scholar Suite. It wraps 7 other kits behind 19 Model Context Protocol tools, enabling AI agents (Claude Code, Antigravity, etc.) to drive the full systematic literature review pipeline through a single MCP server.

**Key characteristics:**
- **Thin orchestration layer**: zero domain logic; delegates entirely to kit APIs
- **Phase-0.5 recon bridge**: uniquely bridges the harness `scholar_harness.recon` module via a `sys.path` adapter seam, adding 3 recon tools to the 16 `nexus_*` tools
- **Calibration module**: a standalone pre-flight screener calibration system for PRISMA screening bias mitigation
- **Heavily tested**: ~1300 lines of hermetic tests at the harness level + 369 lines in-kit tests

**Strengths:**
- Clean separation of concerns (server is pure delegation)
- Robust path resolution (`_resolve_path` anchors to `NEXUS_MCP_WORKSPACE` / repo root)
- Session persistence with content-addressed artifacts (FAIR memory)
- Comprehensive error handling (every tool wraps in try/except, returns structured JSON)

**Weaknesses:**
- `scholar-verify-kit` imported but not declared as a dependency (shared-venv hidden dep)
- No `__init__.py` in the `scholar_agent` package (relies on `pyproject.toml` entrypoint)
- Inconsistent return types (some JSON strings, some prose strings)
- `calibration.py` not exposed as an MCP tool
- CLI `--help` string is a static copy of the tool registry (drift risk)

---

## 1. Functionalities

### 1.1 Complete Tool Inventory (19 MCP Tools)

| # | Tool | Source Line | Kit Delegation | Return Type |
|---|------|-------------|----------------|-------------|
| 1 | `nexus_protocol_compile` | server.py:168 | scholar-protocol-kit | JSON (`{status, protocol_id, fingerprint, protocol}`) |
| 2 | `nexus_protocol_validate` | server.py:195 | scholar-protocol-kit | JSON (`{status: VALID/INVALID, ...}`) |
| 3 | `nexus_protocol_render_criteria` | server.py:242 | scholar-protocol-kit | Markdown string |
| 4 | `nexus_discover` | server.py:262 | scholar-search-kit | Prose string (success + file path) |
| 5 | `nexus_dedup` | server.py:293 | scholar-search-kit | Prose string |
| 6 | `nexus_screen` | server.py:318 | scholar-search-kit | Prose string |
| 7 | `nexus_extract_pdf` | server.py:375 | scholar-pdf-kit | Prose string |
| 8 | `nexus_rag_index` | server.py:403 | scholar-rag-kit | Prose string |
| 9 | `nexus_rag_query` | server.py:424 | scholar-rag-kit | Prose string |
| 10 | `nexus_rag_synthesize` | server.py:480 | scholar-rag-kit | Prose string |
| 11 | `nexus_matrix_extract` | server.py:511 | scholar-rag-kit + scholar-protocol-kit | Prose string |
| 12 | `nexus_graph_build` | server.py:534 | scholar-graph-kit | Prose string |
| 13 | `nexus_bib_clean` | server.py:574 | scholar-bib-kit | Prose string |
| 14 | `nexus_screen_reconcile` | server.py:604 | scholar-search-kit | JSON (reconciliation result) |
| 15 | `nexus_verify_claims` | server.py:655 | scholar-verify-kit | JSON (`{status, metrics, claims}`) |
| 16 | `nexus_verify_phase4` | server.py:739 | scholar-verify-kit | JSON (`{status, stream, written}`) |
| 17 | `recon_probe` | server.py:934 | scholar-harness.recon | JSON (session + pool + lineage) |
| 18 | `recon_distill` | server.py:1024 | scholar-harness.recon | JSON (terms + purity + pool gate) |
| 19 | `recon_delta` | server.py:1111 | scholar-harness.recon | JSON (merged pool + followups + lineage) |

### 1.2 Kit-to-Tool Delegation Map

```
scholar-protocol-kit  -->  nexus_protocol_compile, nexus_protocol_validate, nexus_protocol_render_criteria
scholar-search-kit    -->  nexus_discover, nexus_dedup, nexus_screen, nexus_screen_reconcile
scholar-pdf-kit       -->  nexus_extract_pdf
scholar-rag-kit       -->  nexus_rag_index, nexus_rag_query, nexus_rag_synthesize, nexus_matrix_extract
scholar-graph-kit     -->  nexus_graph_build
scholar-bib-kit       -->  nexus_bib_clean
scholar-verify-kit    -->  nexus_verify_claims, nexus_verify_phase4
scholar-harness.recon -->  recon_probe, recon_distill, recon_delta
```

### 1.3 Calibration Module (Not MCP-exposed)

The `calibration.py` module (467 lines) provides a standalone pre-flight screener calibration system:

| Component | Function | Purpose |
|-----------|----------|---------|
| Checklist schema builder | `build_checklist_schema()` | Converts protocol criteria into structured boolean checklist |
| Decision derivator | `checklist_to_decision()` | Deterministic INCLUDE/EXCLUDE from filled checklist |
| Calibration batch builder | `build_preflight_calibration()` | Samples 20 gold-labeled papers for pre-flight calibration |
| Calibration evaluator | `evaluate_calibration()` | Computes sensitivity, specificity, accuracy, inclusion-rate drift |

### 1.4 Data Models and Schemas

**Session state** (`session.json`):
```json
{
  "session_id": "rec_<hex>",
  "topic": "<string>",
  "cache_keys": ["v1/..."],
  "pools": ["<absolute_path>/pool_<sha>.json"],
  "created_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>"
}
```

**Pool artifact** (`pool_<sha>.json`):
```json
{
  "cache_key": "v1/...",
  "docs": [<Document objects>],
  "merged_from_cache_keys": ["..."]
}
```

**Distilled artifact** (`distilled_<sha>.json` or `distilled_lx<sha>_<...>.json`):
```json
{
  "cache_key": "...",
  "qei": <float>,
  "metrics": {"<label>": <count>},
  "datasets": {"<label>": <count>},
  "schools": [{"label": "...", "n": <int>, "anchor_dois": [...]}],
  "micro_taxonomy": [...],
  "topics": [{"label": "...", "n": <int>, "anchor_dois": [...], "score": <float>}]
}
```

**Calibration report** (`CalibrationReport` dataclass):
```python
@dataclass
class CalibrationReport:
    total: int
    inclusion_rate: float
    gold_inclusion_rate: float
    inclusion_rate_delta: float
    sensitivity: float | None
    specificity: float | None
    accuracy: float
    verdict: Literal["PASS", "FLAG"]
    reasons: list[str]
    per_criterion: dict[str, dict[str, float]]
```

### 1.5 Integration Points

1. **Harness recon adapter** (`_harness_src()`, server.py:81-101): Walks up directory tree to find `scholar_harness.recon` and injects it onto `sys.path`. Uses `NEXUS_HARNESS_SRC` env override.
2. **MCP anchor resolution** (`_mcp_anchor()`, server.py:135-149): Resolves relative paths against `NEXUS_MCP_WORKSPACE` or nearest `.git` ancestor.
3. **RECON_SEARCH_FN seam** (server.py:114): Global `None`-able callable injected by tests to replace real search in `ReconEngine`.
4. **RECON_CACHE_ROOT** (server.py:126): CWD-independent cache root from `canonical_recon_root()`.
5. **Content-addressed artifact persistence** (`_persist_artifact()`, server.py:924-931): SHA-1 based dedup of pool/distilled artifacts.

---

## 2. Improvements

### 2.1 Code Quality Issues

**2.1.1 Missing `__init__.py`**
The `src/scholar_agent/` directory has no `__init__.py`. While the package builds via `pyproject.toml` and setuptools, this can cause issues with some tooling (mypy, IDEs, certain import patterns).

**2.1.2 Static CLI help string (server.py:1201-1221)**
The `main()` function hardcodes the tool list in `epilog`. This is a drift risk -- the `conformance/test_mcp_tool_parity.py` test catches it, but the string should ideally be generated from the registered tools.

**2.1.3 Inconsistent return types**
- Protocol tools return JSON strings: `json.dumps({"status": "SUCCESS", ...})`
- Discovery/screening tools return prose strings: `"Search completed: N papers..."`
- This forces consumers to parse differently per tool. A uniform envelope would improve agent integration.

**2.1.4 Unused import: `Time` (server.py:21)**
`time` is imported and used only for timestamping cache filenames. Minor but present.

**2.1.5 Dead code path in `nexus_verify_phase4` (server.py:769-773)**
The `retraction` stream's `recs = verify_cli._merged_records(ws)` call before `inc = verify_cli._load(...)` suggests `recs` should be used, but `retraction.RetractionChecker.check(recs, inc)` takes both. This is correct but the variable naming is unclear.

### 2.2 Missing Features / Capabilities

**2.2.1 `calibration.py` not exposed via MCP**
The pre-flight calibration system is a sophisticated, well-tested module that should be accessible to agents. Adding `nexus_calibration_build` and `nexus_calibration_evaluate` MCP tools would enable agents to self-calibrate before screening.

**2.2.2 No `nexus_protocol_extraction_schema` or `nexus_protocol_extraction_prompt` tools**
The protocol kit's `build_extraction_model` and extraction prompt generation have no MCP surface (noted in kits_surface_matrix.md). Agents cannot dynamically generate extraction schemas from protocols.

**2.2.3 No batch discover/search tool**
`nexus_discover` does single-query search. A batch search tool (multiple queries, multi-provider matrix) would improve research efficiency.

**2.2.4 No PDF download tool**
The PDF kit's `AsyncPDFDownloader` has no MCP surface. Agents must use CLI for downloading.

**2.2.5 No consensus/consensus-matrix tool**
`scholar-rag-kit`'s `ConsensusCartographer` has no MCP surface.

### 2.3 API Design Improvements

**2.3.1 Unified return envelope**
All tools should return:
```json
{
  "status": "SUCCESS|ERROR",
  "tool": "<tool_name>",
  "data": { ... },
  "error": null | "<message>"
}
```
Currently, some return `{"status": "SUCCESS", "protocol": ...}` while others return prose strings.

**2.3.2 Type-safe `lexicon_json` parameter**
`recon_distill` accepts `str | dict | None` for `lexicon_json` (server.py:1026). While this handles agent framework quirks, it violates MCP's type system. A cleaner approach: always accept string, document that agents should `json.dumps()` dicts.

**2.3.3 `nexus_screen_reconcile` file-name parsing (server.py:619-623)**
Screener key derivation from `batch_*_decisions*.json` file stems is fragile:
```python
parts = f.stem.split("_decisions")
screener_key = parts[1].strip("_") if len(parts) > 1 and parts[1] else "screener1"
```
This breaks for filenames like `batch_001_decisions_screener_a.json` where the key becomes `screener_a` but the split is on `_decisions`.

### 2.4 Error Handling Gaps

**2.4.1 `nexus_discover` does not handle provider failures gracefully**
If all providers fail (network error), the exception propagates as a generic string. Per-provider error swallowing in the search kit means the agent sees an empty result set with no indication of failure.

**2.4.2 `nexus_graph_build` silent DOI failure**
If `asyncio.run(builder.build_graph(dois))` fails, the outer try/except catches it, but intermediate errors during DOI resolution are silently consumed by the graph kit.

**2.4.3 No timeout on `nexus_rag_index`**
Large document directories could hang indefinitely. No timeout parameter exists.

**2.4.4 `recon_delta` hard cap 3 followups (server.py:1139)**
The budget is `max(0, min(int(followups), 3))`. This is documented but could silently confuse agents that pass `followups=10`.

### 2.5 Documentation Needs

**2.5.1 No module docstring for `calibration.py` purpose in MCP context**
The module documents itself well, but there's no guidance on how it connects to the MCP server (it doesn't -- it's standalone).

**2.5.2 SKILL.md mentions 16 tools in CLI help but 19 are registered**
The SKILL.md (line 60) says "lists 16 tools" but the conformance test enforces 19. The help text string is accurate (lists all 19), but the SKILL.md comment is stale.

**2.5.3 No API reference for `CalibrationBatch.write()`**
The batch writer is tested but not documented for external consumers.

---

## 3. Problems

### 3.1 Known Bugs / Issues

**3.1.1 Undeclared `scholar-verify-kit` dependency**
`server.py` imports `from scholar_verify.verbatim import VerbatimClaimVerifier` (line 53) and `from scholar_verify import cli as verify_cli` (line 54), but `pyproject.toml` does not list `scholar-verify-kit` as a dependency. This works only because the shared venv install (`scripts/install_plugins.py`) makes it available. A standalone `uv sync` would fail.

**3.1.2 `import re` inside function body (server.py:703-708)**
In `nexus_verify_claims`, `re` is imported at module level (line 18) but re-imported at line 703 inside a `for` loop body. This is harmless but indicates code that was likely copy-pasted.

**3.1.3 `_validate_session_id` does not enforce max hex length (server.py:844)**
The regex `^rec_[0-9a-f]{6,64}$` accepts 6-64 hex chars. UUID4 generates 32 hex chars. The upper bound of 64 is arbitrary and not documented.

### 3.2 Edge Cases Not Handled

**3.2.1 `nexus_extract_pdf` with non-existent engine**
If `engine` is neither "grobid" nor "docling" (case-insensitive), it falls back to PyMuPDF (server.py:392-393). The fallback is silent and undocumented. An unrecognized engine name should error.

**3.2.2 `recon_probe` with `session_id=None` and no session dir**
When `session_id` is None, a new ID is generated (server.py:955). But if the generated ID collides with an existing session (astronomically unlikely with UUID4), the session would be silently overwritten because `load_session` is only called if `session.json` exists.

**3.2.3 `nexus_bib_clean` in-place overwrite**
When `output_bib_path` is None, the tool writes back to `input_bib_path` (server.py:585). This silently destroys the original file. No confirmation or backup.

**3.2.4 `nexus_screen` empty input**
If the input JSON file contains an empty list, the tool reports "Screening complete: 0 included, 0 excluded, 0 conflicts" as success. This is correct but could be confusing.

### 3.3 Limitations in Current Implementation

**3.3.1 No multi-turn state for `nexus_*` tools**
Unlike `recon_*` tools which maintain session state across calls, the `nexus_*` tools are stateless. Each call is independent. There's no way to build on previous search results incrementally.

**3.3.2 No streaming or progress callbacks**
All tools are synchronous (except `nexus_discover` which is async internally but the tool itself is not truly streaming). Long operations (RAG indexing, graph building, PDF extraction) block with no progress indication.

**3.3.3 `nexus_rag_query` limited to single `boost_doi`**
Despite accepting a list parameter `boost_dois` in `ScholarRetriever.query`, the MCP tool wraps only a single `boost_doi` string (server.py:447-448).

### 3.4 Technical Debt

**3.4.1 `_harness_src()` adapter seam (server.py:81-101)**
This function walks up the directory tree to find `scholar_harness.recon`. It's documented as a temporary adapter but has persisted since M0.5. The proper fix is to declare `scholar-harness` as a dependency.

**3.4.2 `RECON_SEARCH_FN` global mutable state (server.py:114)**
Test seam is a module-level global. This makes the server non-reentrant and could cause issues in concurrent test execution.

**3.4.3 Static tool list in `main()` epilog (server.py:1201-1221)**
Must be manually updated whenever tools are added/removed. The conformance test catches drift, but auto-generation would be better.

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

**4.1.1 `nexus_discover` sequential provider queries**
The `SearchEngine.search_all()` method (delegated to scholar-search-kit) runs providers sequentially. Parallel provider queries would reduce wall-clock time from `sum(provider_times)` to `max(provider_times)`.

**4.1.2 `nexus_graph_build` blocking `asyncio.run()` (server.py:563)**
The tool is synchronous but calls `asyncio.run(builder.build_graph(dois))`. If the MCP server is already running an event loop, this would fail. The `asyncio.run()` call creates a new loop each time.

**4.1.3 `nexus_rag_index` no incremental indexing**
The `ScholarIndexer.index_directory()` re-indexes all files. For large directories, differential indexing (skip unchanged files) would save time.

### 4.2 Memory Usage Issues

**4.2.1 Full document loading in `nexus_verify_claims` (server.py:698-709)**
All `*.md` files in the extracted directory are loaded into memory as `source_texts` dict. For large corpora (hundreds of fulltext papers), this could consume significant RAM.

**4.2.2 `nexus_rag_query` over-fetching (4x n_results)**
When graph boosting is active, the retriever fetches `4 * n_results` chunks (per scholar-rag-kit documentation). For `n_results=5`, this fetches 20 chunks from ChromaDB.

### 4.3 Caching Opportunities

**4.3.1 Protocol validation cache**
`nexus_protocol_validate` re-parses the protocol JSON on every call. For agents that repeatedly validate the same protocol, a memoization cache keyed on content hash would help.

**4.3.2 `nexus_bib_clean` caching**
If the input file hasn't changed, the lint+dedup pipeline could be skipped. Content hash comparison would enable this.

### 4.4 Parallelization Potential

**4.4.1 `nexus_verify_phase4` stream parallelization**
The Phase-4 streams (retraction, open-science, coi, risk-of-bias, trust-context) are independent. Running them in parallel (using `asyncio.gather` or `concurrent.futures`) would reduce total time, especially for the network-bound retraction check.

**4.4.2 `nexus_extract_pdf` batch mode**
Currently processes one PDF at a time. A batch mode with concurrent extraction engines would improve throughput.

---

## 5. Scientific Correction

### 5.1 MCP Protocol Compliance

**5.1.1 Tool naming convention**
All tools use `snake_case` which is MCP-compliant. The `recon_*` prefix correctly separates the harness-bridged tools from the kit tools.

**5.1.2 Return type inconsistency (protocol violation)**
MCP tools should return structured content. Currently:
- Protocol tools return JSON objects (compliant)
- Recon tools return JSON objects (compliant)
- Discovery/screening tools return unstructured prose (partially non-compliant)

**5.1.3 `recon_distill` dual-type parameter (server.py:1026)**
```python
def recon_distill(session_id: str, lexicon_json: str | dict | None = None) -> str:
```
MCP tool parameters should be JSON-serializable types only. `dict` in the type annotation is a Python convenience, not an MCP schema type. The MCP schema generator may produce incorrect JSON Schema for this parameter.

### 5.2 Tool Design Correctness

**5.2.1 `nexus_screen` bypasses agent-in-the-loop pattern**
The tool runs heuristic screening in-process. The real PRISMA contract is the batch handoff via `agent_screen.py`. The MCP tool is a shortcut that may produce lower-quality decisions.

**5.2.2 `nexus_verify_phase4` reuses CLI internal helpers**
The tool calls `verify_cli._merged_records()`, `verify_cli._load()`, `verify_cli._write()` (server.py:769-818). These are private API (`_`-prefixed) of the verify kit. Breaking changes in the verify kit would silently break this tool.

**5.2.3 `recon_delta` budget hard cap**
The 3-followup cap (server.py:1139) is documented but the parameter still accepts any integer. A cleaner API would reject values > 3 with an error.

### 5.3 Agent Interaction Patterns

**5.3.1 No tool chaining guidance**
The SKILL.md lists tools but doesn't provide recommended tool chains (e.g., "protocol compile -> discover -> screen -> extract -> index -> query"). Agent frameworks would benefit from workflow templates.

**5.3.2 No conversation state management**
The `recon_*` tools maintain state via `session_id`, but the `nexus_*` tools are stateless. Agents must manually thread file paths between calls. A session abstraction for the full pipeline would improve UX.

### 5.4 Academic Workflow Alignment

**5.4.1 PRISMA compliance**
The `nexus_screen` tool outputs `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json`, and `prisma_screening_report.md`. This aligns with PRISMA 2020 flow diagram requirements.

**5.4.2 Calibration for bias mitigation**
The `calibration.py` module addresses a real academic problem (screener bias, Kappa ~0.115). Its 20-paper pre-flight calibration is a sound methodological approach.

**5.4.3 Verbatim claim verification**
The `nexus_verify_claims` tool correctly bridges RAG synthesis claims to verbatim quote matching, addressing the reproducibility crisis in systematic reviews.

---

## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent or Skill Be Created?

**Recommendation: YES — a `calibration-agent` skill should be created, and the existing `scholar-agent-kit` skill should be split.**

### 6.2 Rationale

The `scholar-agent-kit` currently serves two distinct roles:
1. **MCP tool registry** (how to call tools)
2. **Calibration system** (how to ensure screening quality)

These should be separated:

**Skill A: `scholar-agent-kit` (existing, refined)**
- Focus: MCP tool documentation, usage patterns, tool chains
- Narrow scope: 19 MCP tools, their parameters, return types, and integration patterns
- Evaluation metrics: tool call success rate, parameter validation, error handling

**Skill B: `calibration-agent` (new)**
- Focus: Pre-flight screener calibration, checklist management, bias detection
- Narrow scope: 4 calibration functions + MCP tool wrappers
- Evaluation metrics: Kappa improvement, sensitivity/specificity thresholds, inclusion-rate drift detection

### 6.3 Evaluation Metrics for Agent Evaluation

| Metric | Definition | Target | Source |
|--------|------------|--------|--------|
| **Tool call success rate** | % of MCP tool calls returning `status: SUCCESS` | >= 95% | All tools |
| **Parameter validation rate** | % of calls where all params are valid types | 100% | All tools |
| **Inclusion-rate drift** | |agent_inclusion_rate - gold_inclusion_rate| | < 0.15 | calibration.py:438 |
| **Sensitivity** | TP / (TP + FN) for gold-INCLUDE papers | >= 0.80 | calibration.py:444 |
| **Specificity** | TN / (TN + FP) for gold-EXCLUDE papers | >= 0.70 | calibration.py:450 |
| **Calibration verdict** | PASS or FLAG | PASS | calibration.py:436 |
| **Session persistence** | session.json survives across calls | 100% | recon tools |
| **Content-addressed dedup** | Same payload -> same artifact filename | 100% | `_persist_artifact()` |
| **CWD independence** | Relative paths anchor to workspace, not kit dir | 100% | `_resolve_path()` |

### 6.4 Critic Capabilities Needed

1. **Schema validator critic**: Validates MCP tool parameters against JSON Schema before execution
2. **Calibration critic**: Compares agent screening decisions against gold standard, flags drift
3. **Workflow critic**: Validates tool chain ordering (e.g., protocol before screening, index before query)
4. **Path safety critic**: Validates all file paths are within workspace boundaries

### 6.5 Agent-in-the-Loop Opportunities

1. **Calibration loop**: Agent fills checklist -> evaluator compares to gold -> agent re-screens flagged papers -> re-evaluate -> iterate until PASS
2. **Screening reconciliation loop**: Multiple agents screen independently -> reconcile -> adjudicate conflicts -> re-screen borderline cases
3. **Grounded recon loop**: probe -> distill -> delta (gap follow-ups) -> re-distill until purity is "coherent"

### 6.6 Automation Potential

| Workflow | Current State | Automation Potential |
|----------|---------------|---------------------|
| Protocol compile + validate | Manual two-step | HIGH: auto-validate after compile |
| Discover + dedup + screen | Three separate calls | HIGH: chain into single workflow |
| Extract + index + query | Three separate calls | HIGH: pipeline automation |
| Calibration + screening | Not connected | HIGH: auto-calibrate before screening |
| Graph build + RAG query with boosting | Manual parameter threading | MEDIUM: auto-construct graph_source path |

---

## 7. Priority-Ranked Improvement Suggestions

### Priority 1: Critical (Blocks correctness)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P1.1 | Declare `scholar-verify-kit` as dependency | pyproject.toml:6-14 | Add `"scholar-verify-kit"` to `dependencies` |
| P1.2 | Remove duplicate `import re` inside loop | server.py:703 | Remove `import re` (already at line 18) |
| P1.3 | `_resolve_path` should not treat all non-JSON strings as paths | server.py:156 | Add file existence check before path resolution |

### Priority 2: High (Improves reliability)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P2.1 | `nexus_extract_pdf` silent fallback for unknown engine | server.py:392 | Error on unrecognized engine names |
| P2.2 | `nexus_bib_clean` in-place overwrite without backup | server.py:585 | Add `.bak` backup or document behavior |
| P2.3 | Static CLI help string drift risk | server.py:1201-1221 | Generate from registered tools |
| P2.4 | Expose calibration module via MCP tools | calibration.py | Add `nexus_calibration_build`, `nexus_calibration_evaluate` |

### Priority 3: Medium (Improves UX)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P3.1 | Inconsistent return types (JSON vs prose) | server.py:all | Standardize all tools to JSON envelope |
| P3.2 | `nexus_rag_query` single boost_doi limit | server.py:447 | Accept list of DOIs |
| P3.3 | No batch discover tool | N/A | Add `nexus_discover_batch` |
| P3.4 | No PDF download tool via MCP | N/A | Add `nexus_pdf_download` |

### Priority 4: Low (Cleanup / tech debt)

| # | Issue | File:Line | Fix |
|---|-------|-----------|-----|
| P4.1 | Missing `__init__.py` | src/scholar_agent/ | Add empty `__init__.py` |
| P4.2 | `_harness_src()` adapter is long-lived tech debt | server.py:81-101 | Properly declare harness dependency |
| P4.3 | `RECON_SEARCH_FN` global mutable state | server.py:114 | Consider contextvar or fixture pattern |
| P4.4 | `recon_distill` dual-type parameter | server.py:1026 | Document MCP limitation, keep for compat |
| P4.5 | SKILL.md stale tool count comment | SKILL.md:60 | Update to "19 tools" |

---

## Appendix A: File Structure

```
tools/scholar-agent-kit/
  pyproject.toml              # Package definition, deps (MISSING: scholar-verify-kit)
  .gitignore                  # Standard ignores
  uv.lock                     # Lockfile
  src/
    scholar_agent/
      server.py               # MCP server, 19 tools, 1257 lines
      calibration.py           # Pre-flight calibration, 467 lines
      __pycache__/
  tests/
    test_server.py            # 151 lines, 3 test functions
    test_calibration.py       # 218 lines, 11 test functions
  .cache/
    mcp/                      # Cached discover results
    inception_recon/          # FAIR recon session cache
      sessions/               # Session state (session.json + pool/distilled artifacts)
      pools/                  # Content-addressed pool artifacts
    hishel/                   # HTTP cache
  .venv/                      # Kit-local venv (not shared)
```

## Appendix B: Key Code References

| Concept | File | Lines |
|---------|------|-------|
| MCP server instance | server.py | 132 |
| Harness adapter seam | server.py | 81-106 |
| MCP path anchor | server.py | 135-161 |
| Content-addressed persistence | server.py | 910-931 |
| Session state management | server.py | 836-908 |
| Session ID validation | server.py | 844-851 |
| Workspaces root safety guard | server.py | 854-862 |
| Checklist schema builder | calibration.py | 29-58 |
| Checklist-to-decision logic | calibration.py | 65-128 |
| Calibration batch builder | calibration.py | 154-283 |
| Calibration evaluator | calibration.py | 342-467 |
| CLI entrypoint | server.py | 1194-1257 |
| MCP config (launch) | .agents/plugins/nexus-scholar/mcp_config.json | 1-13 |
| SKILL.md | .agents/skills/scholar-agent-kit/SKILL.md | 1-128 |
| Kit surface matrix entry | docs/kits_surface_matrix.md | 295-314 |

## Appendix C: Test Coverage Summary

| Test Module | Lines | Test Count | Focus |
|-------------|-------|------------|-------|
| `tests/test_server.py` | 151 | 3 | Protocol compile/validate/render, dedup+screen, RAG+matrix |
| `tests/test_calibration.py` | 218 | 11 | Checklist schema, decision derivation, calibration build/evaluate |
| `tests/test_mcp_recon.py` | 666 | 18 | recon_probe/distill/delta, session persistence, lexicon merge, purity gates, workspaces safety |
| `tests/test_mcp_tools_graph.py` | 619 | ~20 | Graph HTTP client, PDF metadata, bib clean, screen artifacts, verify claims normalization, protocol validation parity, RAG graph boosting |
| `tests/conformance/test_mcp_tool_parity.py` | 34 | 2 | Action table MCP references, --help registry drift |

**Total test coverage:** ~1688 lines, ~54 test functions across 5 modules.


---

<!-- Source: kit_08_verify.md -->
﻿# Comprehensive Deep Dive Analysis: scholar-verify-kit

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


---

