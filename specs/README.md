# Nexus Scholar Harness: Phase Specifications Summary

**Created:** 2026-09-15  
**Last Updated:** 2026-09-15  
**Author:** opencode (mimo-v2.5-free)  
**Status:** All Phase Specs Complete (A-E), Post-Review v1.1.0

---

## Overview

This document provides an overview of all phase specifications for the Nexus Scholar Harness ecosystem. Each phase builds upon the existing codebase, wrapping and enhancing existing kit APIs rather than reimplementing.

---

## Phase Summary

| Phase | Name | Duration | Features | Total Hours | Version |
|-------|------|----------|----------|-------------|---------|
| A | Interoperability | 3 days | 5 | 45.5 | 1.0.0 |
| B | Scientometrics | 5 days | 5 | 37.5 | 1.1.0 |
| C | RAG | 4 days | 3 | 20 | 1.1.0 |
| D | Agent | 2 days | 2 | 8.5 | 1.1.0 |
| E | Visualization | 2 days | 3 | 10 | 1.1.0 |
| **Total** | | **16 days** | **18** | **121.5** | |

---

## Phase A: Interoperability (Days 1–3)

**Spec Location:** `specs/phase_a_interoperability/README.md`

### Features
1. **RIS Exporter** - Export `Document` objects to RIS format for Rayyan/Covidence
2. **CSL-JSON Exporter** - Export BibTeX `Entry` objects to CSL-JSON for Zotero/Pandoc
3. **0-11 Completeness Score** - Quantitative assessment of document metadata quality
4. **Abstract Backfilling** - Enrich documents with abstracts from Crossref/Semantic Scholar
5. **GEXF/GraphML Exporters** - Export citation graphs to Gephi/yEd

### Key Learnings Applied
- DocumentCluster `.duplicates` → `.members` (actual field name)
- AcademicHttpClient has no `post()` method
- P7.7 lazy imports for networkx
- `doc.sources[0]` is a dict, not a string (access `.get("provider")`)

### Total: 45.5 hours

---

## Phase B: Scientometrics (Days 5–9)

**Spec Location:** `specs/phase_b_scientometrics/README.md`

### Features
1. **HITS Hubs & Authorities** - Identify seminal reviews (Hubs) vs. empirical trials (Authorities)
2. **Co-Citation & Coupling Networks** - Construct intellectual paradigm clusters
3. **Louvain Community Detection** - Automatic thematic partitioning (sets `community` attribute)
4. **Screening Run Comparator** - Compare screening runs with 2-state transition matrices
5. **Golden Seed Self-Healing Query** - Validate queries against landmark papers

### Key Learnings Applied
- All networkx imports deferred inside function bodies
- `ScreeningDecision` has exactly 2 states: `INCLUDE`, `EXCLUDE` (no `UNCERTAIN`)
- `golden_seeds` added to `SearchStrategy` (NOT `ResearchProtocol` directly)
- Monorepo sync with push_tools.py

### Total: 37.5 hours

---

## Phase C: RAG (Days 10–13)

**Spec Location:** `specs/phase_c_rag/README.md`

### Features
1. **ChromaDB Vector Backend** - Enhanced `ScholarIndexer` with production-grade vector storage
2. **Structured Extraction with LLM** - Schema-validated extraction aligned with `MethodologyMetadata`
3. **Gemini Embedding Integration** - Added to existing `embedder.py` with `get_embedder()` factory

### Key Learnings Applied
- Reuse existing `MarkdownChunker` (NOT `chunk_document`)
- `MethodologyMetadata` from `models.py` for extraction schemas
- PII patterns: email, ORCID, phone, grant numbers
- `_call_llm()` uses Gemini REST API with `responseMimeType:"application/json"`
- Heuristic fallback on LLM failure

### Total: 20 hours

---

## Phase D: Agent (Days 14–15)

**Spec Location:** `specs/phase_d_agent/README.md`

### Features
1. **LLM-Enhanced Screening MCP Tool** - `nexus_screen_llm` wrapping `LLMBatchScreener` + `calibration.py`
2. **Pipeline Automation MCP Tool** - `nexus_pipeline_run` wrapping existing `ResearchOrchestrator`

### Key Learnings Applied
- `MCPServer` already IS the tool registry (D2 MCP Tool Abstraction dropped)
- Wrap existing code, don't reimplement
- Use `calibration.py`'s structured boolean checklist (prevents LLM drift)
- Return `ScreeningDecision` dataclass objects (not raw dicts)
- MCP tools in `scholar-agent-kit` (no Typer CLI)

### Total: 8.5 hours

---

## Phase E: Visualization (Days 16–17)

**Spec Location:** `specs/phase_e_visualization/README.md`

### Features
1. **Enhanced Graph Visualization** - Add community coloring to existing `GraphVisualizer`
2. **PRISMA Flow Diagrams** - Add `to_mermaid()`/`to_plantuml()` to existing `PrismaFlowReport`
3. **PRISMA 2020 Compliance Scoring** - Add `prisma_compliance()` to existing `validate_protocol()`

### Key Learnings Applied
- `visualizer.py` already exists — enhance, don't recreate
- `PrismaFlowReport` already exists in `scholar-search-kit` — extend, don't duplicate
- RIS/CSL-JSON for protocols dropped (wrong format for research plans)
- E1 depends on B3's `community` attribute for node coloring
- E2 consumes `prisma_report.json` from D1's screening output

### Total: 10 hours

---

## Cross-Phase Dependencies

```
Phase A (Interoperability) ← independent
Phase B (Scientometrics) ← independent
Phase C (RAG) ← independent
Phase D (Agent) ← independent (wraps existing code)
Phase E (Visualization) ← depends on B3 (community coloring for E1)
```

**Key Data Flow Chains:**
- B3 → E1: Community detection sets `community` attribute → E1 colors nodes by community
- D1 → E2: Screening produces `prisma_report.json` → E2 generates Mermaid/PlantUML diagrams
- A3 → A4: Completeness scoring identifies missing abstracts → backfilling enriches them

---

## Implementation Order

### Recommended Sequence

1. **Phase A** (Days 1-3) - Foundation for interoperability
2. **Phase B** (Days 5-9) - Scientometric analysis
3. **Phase C** (Days 10-13) - RAG capabilities
4. **Phase D** (Days 14-15) - Agent integration
5. **Phase E** (Days 16-17) - Visualization

All phases are substantially independent except E1→B3.

---

## Specification Quality Checklist

Each specification includes:

- [x] **Executive Summary** - High-level overview
- [x] **Algorithm Specifications** - Detailed algorithms with pseudocode
- [x] **File Modifications** - Exact files to create/modify
- [x] **Implementation Details** - Complete code examples
- [x] **CLI Integration** - Command-line interface design
- [x] **Testing Strategy** - Unit and integration tests
- [x] **Task List** - Breakdown with dependencies and estimates
- [x] **Monorepo Governance** - Sync requirements
- [x] **Definition of Done** - Feature and phase-level criteria
- [x] **Acceptance Criteria** - Measurable targets
- [x] **Dependencies & Constraints** - External and internal
- [x] **Risk Mitigation** - Identified risks and mitigations

---

## Lessons Learned (Applied Across All Phases)

### From Phase A
1. **Attribute Verification:** Always verify field names against actual code
2. **Method Existence:** Check that methods exist before referencing them
3. **P7.7 Lazy Imports:** All heavy dependencies must remain deferred
4. **Monorepo Governance:** Kit changes require `push_tools.py` → `plugins.json` → `generate_nexus_scholar_pins.py`

### From Phase B
1. **ScreeningDecision Schema:** Exactly 2 states: `INCLUDE`, `EXCLUDE` (no `UNCERTAIN`)
2. **Co-Citation Complexity:** O(n²) for large graphs, use sparse matrices
3. **Louvain Determinism:** Use `seed=42` for reproducibility

### From Phase C
1. **ChromaDB Batch Size:** Default 100 documents per batch
2. **PII Patterns:** Email, ORCID, phone, grant number regex patterns
3. **Pydantic Validation:** Use `model_json_schema()` for LLM prompts

### From Phase D
1. **Kit Non-Reinvention:** Wrap existing code, don't reimplement
2. **MCP Server:** `MCPServer` already handles tool registration and validation
3. **Calibration:** Use structured boolean checklist to prevent LLM drift

### From Phase E
1. **Enhance, Don't Recreate:** Existing classes should be extended, not replaced
2. **Correct Kit Placement:** Features must live where their data models live
3. **Format Appropriateness:** RIS/CSL-JSON are for citations, not research plans

---

## Testing Strategy Across Phases

### Common Principles
1. **Hermetic Tests:** No network calls, no real API invocations
2. **Isolated Workspaces:** Use `tmp_path` fixture for all file I/O
3. **Contract-Driven:** Verify data schemas, not implementation details
4. **Deterministic:** Same inputs always produce same outputs

### Test Execution
```bash
# Run all tests
uv run pytest -v

# Run specific phase tests
uv run pytest tests/ -k "phase_a" -v
uv run pytest tests/ -k "phase_b" -v
uv run pytest tests/ -k "phase_c" -v
uv run pytest tests/ -k "phase_d" -v
uv run pytest tests/ -k "phase_e" -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

---

## Monorepo Governance (All Phases)

### Post-Implementation Steps

For each phase completion:

```bash
# 1. Sync kit changes to external repos
python scripts/push_tools.py

# 2. Update plugins.json (manual step after push)
# Edit .agents/plugins/nexus-scholar/plugins.json

# 3. Regenerate metapackage pins
python scripts/generate_nexus_scholar_pins.py --check  # Verify freshness
python scripts/generate_nexus_scholar_pins.py          # Regenerate

# 4. Run conformance tests
uv run pytest tests/conformance/ -v

# 5. Run full test suite
uv run pytest -v
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | ≥90% | `pytest --cov` |
| Lint Clean | 0 errors | `ruff check scripts/` |
| Type Clean | 0 errors | `mypy src/` |
| Conformance | 100% | `pytest tests/conformance/` |
| No Regressions | 0 failures | `pytest` |

---

## Next Steps

1. **Review Phase A spec** - Start with `specs/phase_a_interoperability/README.md`
2. **Approve or request changes** - Before implementation begins
3. **Begin implementation** - After approval
4. **Continue with Phase B** - After Phase A completion

---

*Summary created by opencode (mimo-v2.5-free) on 2026-09-15*
*Last updated: 2026-09-15 (post-sweep fixes applied)*
*Source: Phase specifications A through E (all v1.1.0 or v1.0.0)*
