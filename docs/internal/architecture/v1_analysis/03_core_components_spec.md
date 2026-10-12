# 03 Core Components Spec
<!-- Source: 02_source_code_analysis.md -->
﻿# Source Code Analysis: src/scholar_harness/

> Generated: 2026-09-14 | Scope: every .py file under src/scholar_harness/
> Version: 1.0.0 (per __init__.py)
> Total files: 31 Python files across 5 subpackages

---

## 1. Complete File Listing with Descriptions

### 1.1 Top-Level Package (src/scholar_harness/)

| File | Lines | Purpose |
|------|------:|---------|
| __init__.py | 7 | Package root. Exports ResearchOrchestrator and __version__ = "1.0.0". |
| cli.py | 494 | **Main CLI entry point.** Typer app with commands: status, init, setup-mcp, doctor, log (sub-app), inception, sync, 
un, export, serve. Registered as the scholar-harness console script. |
| orchestrator.py | 731 | **Core pipeline orchestrator.** ResearchOrchestrator class: get_status(), sync_state(), 
un_pipeline() / 
un_pipeline_async(). Wires together all eight kits in a 10-stage pipeline. |
| inception.py | 1846 | **Phase-0 Socratic inception wizard.** The largest file. Implements the 4-stage methodology interview: paradigm detection, refraction grid, Socratic boundary grill, protocol emission. Also contains init_command() for P7.3 portable workspace bootstrap. |
| gent_screen.py | 850 | **PRISMA screening agent.** File-based handoff protocol: prepare, collect, status, calibration, calibrate-eval. Dual-screening reconciliation logic. |
| pipeline_executor.py | 360 | **PipelineSpec DAG executor (M5.4).** Loads a PipelineSpec JSON, topologically sorts nodes, resolves templates, runs each node as a uv run subprocess. |
| udit_log.py | 269 | **Audit CLI surface (P7.6).** Commands: event, atch, sync-index. Delegates to workspace-manager's log_event.py. |
| doctor.py | 564 | **Health check command (P7.5).** Validates kits/versions, API keys, skills, workspace layout, CLI/bin seam. |
| mcp_setup.py | 318 | **MCP server wiring (P7.4).** Merges 
exus-scholar entry into Claude Desktop / Cursor / VS Code / .mcp.json configs. |
| 
escreen_workspace.py | 34 | **Convenience alias.** Forwards to gent_screen.main(). |

### 1.2 
econ/ Subpackage -- Exploratory Reconnaissance

| File | Lines | Purpose |
|------|------:|---------|
| 
econ/__init__.py | 25 | Re-exports all public names. |
| 
econ/engine.py | 314 | **Probe engine (M0.1).** ReconEngine: probes providers, deduplicates, persists content-addressed pools. Supports injectable search_fn for tests. |
| 
econ/distiller.py | 305 | **Term-frequency distiller (M0.2/M0.4).** Pure-Python: micro-taxonomy, metric/dataset/school counts, school groupings, topic layer, QEI. |
| 
econ/gates.py | 128 | **Evaluation gates (M0.7).** APR, pool sufficiency (threshold: 12), topic purity (threshold: 0.50). |
| 
econ/lexicon.py | 141 | **Pluggable domain lexicons (M0.4/P6).** DomainLexicon frozen dataclass. DEFAULT_LEXICON with CV/LLM + cross-domain patterns. |
| 
econ/cache_key.py | 113 | **Hierarchical cache key builder.** 1/<providers>/y<year>/q/<sha256>. |
| 
econ/adaptive.py | 338 | **Adaptive probe horizon (M0.4).** plan_followups(), execute_followups(), merge_pools(). |

### 1.3 console/ Subpackage -- Harness Console (Web UI)

| File | Lines | Purpose |
|------|------:|---------|
| console/__init__.py | 20 | Lazy factory: create_app(). |
| console/serve.py | 71 | **FastAPI application factory.** Mounts routers, static files, /healthz, SPA index. |

### 1.4 console/api/ -- REST API Routers

| File | Lines | Purpose |
|------|------:|---------|
| console/api/__init__.py | 1 | Docstring only. |
| console/api/workspace.py | 287 | **Read-only workspace endpoints.** 15+ endpoints serving canonical workspace files. |
| console/api/jobs.py | 144 | **Job control + SSE stream.** Start, list, get, cancel, stream (SSE). |
| console/api/screening.py | 155 | **Screening decision writer.** POST /batch/{n}/decisions with validation. |
| console/api/pipelines.py | 669 | **PipelineSpec CRUD + dry-run.** Models, 5 built-in templates, validation, DAG analysis. |
| console/api/streams.py | 67 | **Global change-tick SSE stream.** Heartbeat via INDEX.md mtime. |
| console/api/audit.py | 150 | **Audit journal writes.** log_event() + POST /audit/events. |

### 1.5 console/runtimes/ -- Job Execution

| File | Lines | Purpose |
|------|------:|---------|
| 
untimes/__init__.py | 1 | Docstring only. |
| 
untimes/actions.py | 192 | **Action-to-command mapping.** 14 actions with templates and MCP tool parity. |
| 
untimes/job_runner.py | 440 | **Asyncio subprocess job runner.** Job, JobRunner, JobConflict. Lifecycle tracking + audit journal. |

### 1.6 integrations/ -- Academic Ecosystem Export

| File | Lines | Purpose |
|------|------:|---------|
| integrations/__init__.py | 7 | Re-exports exporters. |
| integrations/latex_typst.py | 104 | **LaTeX and Typst exporter.** Markdown -> publication-ready LaTeX/Typst with citations. |
| integrations/obsidian.py | 102 | **Obsidian PKM vault exporter.** Per-paper notes with wikilinks and MOC. |
| integrations/zotero.py | 94 | **Zotero reference manager bridge.** Convert included papers to Zotero items. |
| integrations/pipeline_script.py | 146 | **PipelineSpec to bash script renderer.** Equivalently-executing shell export. |

---

## 2. Architecture Overview

### 2.1 Layer Diagram

`
+-----------------------------------------------------------------------+
|                         CLI LAYER (cli.py)                             |
|  scholar-harness status|init|setup-mcp|doctor|log|inception|          |
|  sync|run|export|serve                                                |
+-------+----------+-----------+----------+----------+---------+--------+
        |          |           |          |          |         |
        v          v           v          v          v         v
+-----------+ +--------+ +--------+ +--------+ +--------+ +----------+
|inception  | |doctor  | |audit   | |mcp     | |pipeline| |integrations|
|(wizard)   | |(health)| |_log    | |_setup  | |_exec   | |(export)   |
+-----------+ +--------+ +--------+ +--------+ +--------+ +----------+
        |          |           |          |          |         |
        v          v           v          v          v         v
+-----------------------------------------------------------------------+
|                    ORCHESTRATOR LAYER (orchestrator.py)                |
|           ResearchOrchestrator: 10-stage pipeline                      |
|    protocol -> search -> dedup -> verify -> screen -> extract ->      |
|    index -> matrix -> graph -> synthesis -> audit                     |
+-------+----------+-----------+----------+----------+---------+--------+
        |          |           |          |          |         |
        v          v           v          v          v         v
+-----------------------------------------------------------------------+
|                    EXTERNAL KIT LAYER (tools/*/src/)                   |
|  scholar-search-kit | scholar-protocol-kit | scholar-pdf-kit           |
|  scholar-rag-kit    | scholar-graph-kit    | scholar-verify-kit        |
|  scholar-bib-kit    | scholar-agent-kit                                |
+-----------------------------------------------------------------------+
        |
        v
+-----------------------------------------------------------------------+
|                    RECON SUBSYSTEM (recon/)                            |
|  ReconEngine -> distill_pool -> gates -> adaptive followups           |
+-----------------------------------------------------------------------+
        |
        v
+-----------------------------------------------------------------------+
|                    CONSOLE SUBSYSTEM (console/)                        |
|  FastAPI + uvicorn | REST API + SSE | JobRunner (asyncio subprocess)  |
|  SPA (static/) | PipelineSpec CRUD | Screening decisions              |
+-----------------------------------------------------------------------+
`

### 2.2 Key Design Principles

1. **Thin orchestrator**: The harness imports kit APIs directly (not re-implements them). All domain logic lives in 	ools/*/src/ packages.
2. **File-based state**: Every workspace artifact is a canonical file (protocol.json, included.json, udit/journal.jsonl, etc.). No database.
3. **Agent-in-the-loop**: The PRISMA screening step is a file handoff -- the harness prepares batches, an agent (LLM) reads them and writes decisions, then collect assembles results.
4. **Append-only audit**: Every significant action appends to udit/journal.jsonl. INDEX.md is regenerated from the journal.
5. **Atomic writes**: JSON files are written via temp-file + os.replace() to prevent corruption on crash.
6. **Wheel-portable**: Skills are resolved via NEXUS_SKILLS_SRC env -> wheel bundle -> repo .agents/skills.

---

## 3. Main Entry Points and CLI Structure

### 3.1 Primary CLI: scholar-harness (cli.py, line 29-494)

`
scholar-harness
  status          Display workspace status and pipeline metrics
  init            Bootstrap a portable workspace (P7.3)
  setup-mcp       Wire MCP server into harness config files (P7.4)
  doctor          Validate kits, keys, skills, layout (P7.5)
  inception       Run the Phase-0 Socratic methodology interview
  sync            Rebuild project.json + INDEX.md from filesystem
  run             Execute a research pipeline (--protocol or --pipeline)
  export          Export to LaTeX/Typst/Obsidian/Zotero/bash
  serve           Run the Harness Console server (FastAPI)
  log             Sub-app:
    event           Append one audit event
    batch           Append JSONL batch of events
    sync-index      Regenerate INDEX.md
`

### 3.2 Secondary CLI: gent_screen.py (line 795-850)

`
python agent_screen.py
  prepare         Chunk verified.json into batch files
  status          Show screening progress
  collect         Assemble decisions into final outputs
  calibration     Generate pre-flight calibration batch
  calibrate-eval  Evaluate calibration against gold standard
`

---

## 4. Core Modules and Their Responsibilities

### 4.1 orchestrator.py -- The Central Orchestrator

**Class: ResearchOrchestrator** (line 108)

| Method | Lines | Purpose |
|--------|------:|---------|
| __init__ | 111-112 | Sets workspace_dir |
| get_status() | 114-247 | Inspects workspace state across all directories |
| sync_state() | 249-392 | Atomically rebuilds project.json + INDEX.md |
| 
un_pipeline_async() | 430-698 | **The 10-stage pipeline** |
| 
un_pipeline() | 700-702 | Synchronous wrapper |
| _log_audit_event() | 704-731 | Appends to udit/journal.jsonl |
| _refresh_index_md_atomic() | 394-428 | Regenerates INDEX.md via workspace-manager |

**Provider resolution** (line 39-67): Maps provider name strings to SearchProvider instances via _PROVIDER_MAP.

### 4.2 inception.py -- The Socratic Wizard (1846 lines)

**Key dataclasses:**
- ConceptDraft (line 474): Search concept with synonyms.
- RQDraft (line 480): Research question with facet, evidence type, synthesis method.
- Survey (line 488): Complete interview result.

**Key functions:**
- detect_leanings() (line 305): Keyword-scores across 4 paradigms.
- make_intent() (line 522): Assembles IntentPacket for deterministic compilation.
- compile_protocol_files() (line 599): intent.json -> protocol.json + SCREENING_CRITERIA.md.
- scaffold_project() (line 625): Delegates to workspace-manager.
- scaffold_raw_project() (line 649): Direct layout for P7.3 portable init.
- 
un_wizard() (line 1280): Full 4-stage interview flow.
- init_command() (line 1771): P7.3 portable workspace bootstrap.

**Responder protocol** (line 373): Abstraction over interactive prompts for testability.

**Grounded recon loop** (lines 1034-1273): Probes, distills, presents directions, enforces anchor provenance.

### 4.3 
econ/ -- Exploratory Reconnaissance

**ReconEngine** (engine.py, line 123): Manages probe lifecycle with CWD-independent cache.

**distill_pool()** (distiller.py, line 249): Pure-Python term extraction, no ML dependencies.

**Gates** (gates.py): APR, pool sufficiency (12 docs), topic purity (0.50 top-3 share).

**Adaptive probing** (adaptive.py): Detects thin sub-schools (n <= 2), bounded follow-up probes.

### 4.4 console/ -- Harness Console

**Job lifecycle** (job_runner.py):
`
queued -> running -> success | failed | cancelled
`

**Single-flight per action** (job_runner.py, line 110-112): Prevents concurrent runs of the same action.

**Pipeline jobs** run in a worker thread (line 233-340), streaming output to SSE via a thread-safe queue.

---

## 5. Data Flow and Architecture

### 5.1 End-to-End Research Pipeline

`
[Phase 0: Inception]
  topic -> detect_leanings() -> paradigm/playbook selection
  -> Socratic boundary grill -> RQ drafting -> concept clustering
  -> make_intent() -> compile_protocol_files() -> protocol.json
  -> scaffold -> GENESIS audit event

[Phase 1: Discovery + Screening]
  protocol.json -> compile_protocol_search() -> Query
  -> SearchEngine.search_all() -> raw_search.json
  -> Deduplicator.deduplicate() -> deduped.json
  -> DocumentVerifier.process_batch() -> verified.json
  -> agent_screen prepare -> screening/batch_NNN.json
  -> [AGENT SCREENS] -> batch_NNN_decisions.json
  -> agent_screen collect -> included.json + excluded.json

[Phase 2: Harvest + Extract]
  included.json -> scholar-pdf download -> pdfs/
  -> PyMuPDFEngine.extract_markdown() -> extracted/*.md

[Phase 3: Index + Matrix + Graph + Synthesis]
  extracted/*.md -> ScholarIndexer -> chroma_db/
  -> MatrixExtractor -> synthesis_matrix.csv/json
  -> CitationGraphBuilder -> knowledge_graph.json/html
  -> GroundedSynthesisEngine -> literature_review.md

[Phase 4: Verification]
  -> trust_consensus, retraction_check, coi_audit, risk_of_bias

[Phase 5: Export + Console]
  -> LaTeX/Typst/Obsidian/Zotero export
  -> Harness Console for observability
`

### 5.2 Screening Sub-Flow

`
verified.json + protocol.json
    -> prepare -> batch_001.json ... batch_NNN.json
    -> [AGENT SCREENS EACH BATCH]
    -> batch_001_decisions.json ... batch_NNN_decisions.json
    -> collect -> included.json + excluded.json + prisma_report.json
`

### 5.3 Recon Sub-Flow

`
topic -> ReconEngine.probe() -> pool JSON (cached)
  -> distill_pool() -> terms JSON
  -> _grounded_directions_for_terms() -> 3 DOI-anchored directions
  -> _enforce_grounded_anchors() -> verify anchor provenance
  -> recon_context -> audit/recon_context.json
`

---

## 6. External Integrations

### 6.1 Kit Dependencies

| Kit | Import Path | Used In |
|-----|-------------|---------|
| scholar-search-kit | scholar_search.* | orchestrator, recon/engine, agent_screen |
| scholar-protocol-kit | scholar_protocol.* | inception (compile_protocol_files) |
| scholar-pdf-kit | scholar_pdf.extract.PyMuPDFEngine | orchestrator (Stage 6) |
| scholar-rag-kit | scholar_rag.* | orchestrator (Stages 7-8-9) |
| scholar-graph-kit | scholar_graph.* | orchestrator (Stage 9) |
| scholar-agent-kit | scholar_agent.calibration | agent_screen (optional) |

### 6.2 Search Providers (via scholar-search-kit)

| Provider | Class |
|----------|-------|
| OpenAlex | OpenAlexProvider |
| Semantic Scholar | SemanticScholarProvider |
| Crossref | CrossrefProvider |
| ArXiv | ArxivProvider |
| PubMed | PubMedProvider |
| bioRxiv | BiorxivProvider |

### 6.3 Tool Integrations

| Tool | Module | Type |
|------|--------|------|
| Zotero | integrations/zotero.py | REST API or offline export |
| Obsidian | integrations/obsidian.py | File export (markdown + wikilinks) |
| LaTeX | integrations/latex_typst.py | File export |
| Typst | integrations/latex_typst.py | File export |
| ChromaDB | orchestrator.py (inline import) | Vector store |
| NetworkX | orchestrator.py (import) | Citation graph + PageRank |

---

## 7. Error Handling Patterns

### 7.1 Graceful Degradation

- **Audit logging never crashes**: _log_project_event() (inception.py:152) catches exceptions and prints a warning.
- **INDEX.md refresh is best-effort**: _refresh_index_md_atomic() (orchestrator.py:394) restores backup on failure.
- **Journal writing failure swallowed**: _journal_event() (job_runner.py:408) catches all exceptions.
- **Provider errors degrade to -1**: corpus_count() (engine.py:193) returns -1 on failure.
- **Missing optional modules**: gent_screen.py (line 106) sets _HAS_CALIBRATION = False on ImportError.

### 7.2 Atomic Writes

All critical JSON writes use temp-file + os.replace():
`python
# Pattern used throughout (e.g., orchestrator.py:101-105)
tmp = path.with_suffix(path.suffix + ".tmp")
tmp.write_text(json.dumps(payload, ...))
os.replace(tmp, path)
`

### 7.3 Input Validation

- **PipelineSpec** (pipelines.py:441): Structural checks before execution.
- **Screening decisions** (screening.py:98): Validates workspace_ids, decision codes, confidence range.
- **Batch records** (audit_log.py:170): Lenient-skip policy for malformed input.

### 7.4 Platform Handling

- **Windows UTF-8** (cli.py:22-27): Reconfigures stdout/stderr on Windows.
- **BOM handling** (doctor.py:172): Uses utf-8-sig for Windows-created .env files.
- **Symlink fallback** (inception.py:1636-1639): Falls back to shutil.copytree() on Windows without admin.

### 7.5 Timeout and Cancellation

- **Job timeouts** (job_runner.py:30-32): 30 min default, 12 hours for download/extract.
- **Pipeline cancellation** (pipeline_executor.py:320): Cooperative via should_cancel callback.

---

## 8. Code Patterns and Conventions

### 8.1 Style

- **Type hints**: Pervasive rom __future__ import annotations and modern union syntax.
- **Dataclasses**: Immutable data (DomainLexicon, ConceptDraft, RQDraft, Survey).
- **Pydantic models**: API request/response bodies and PipelineSpec validation.
- **Rich console**: All CLI output uses 
ich.console.Console.
- **Typer**: CLI framework with sub-apps.

### 8.2 File Organization

`
src/scholar_harness/
  __init__.py              # Package root (7 lines)
  cli.py                   # Main CLI entry point (494 lines)
  orchestrator.py          # Core pipeline orchestrator (731 lines)
  inception.py             # Phase-0 wizard (1846 lines -- largest)
  agent_screen.py          # PRISMA screening (850 lines)
  pipeline_executor.py     # DAG executor (360 lines)
  audit_log.py             # Audit CLI (269 lines)
  doctor.py                # Health checks (564 lines)
  mcp_setup.py             # MCP wiring (318 lines)
  rescreen_workspace.py    # Alias (34 lines)
  recon/                   # Exploratory reconnaissance (6 modules, ~1339 lines)
  console/                 # Web console (FastAPI)
    api/                   # REST routers (6 modules, ~1472 lines)
    runtimes/              # Job execution (2 modules, ~632 lines)
    static/                # SPA assets (vendored JS)
  integrations/            # Academic ecosystem (4 modules, ~446 lines)
`

### 8.3 Naming Conventions

- **Modules**: snake_case.py
- **Classes**: PascalCase (ResearchOrchestrator, ReconEngine, PipelineSpec)
- **Functions**: snake_case (detect_leanings, distill_pool, compute_apr)
- **Constants**: UPPER_SNAKE_CASE (POOL_MAX, SATURATION_SCANT, DEFAULT_LEXICON)
- **Private functions**: _leading_underscore (_resolve_providers, _study_doi, _atomic_write_json)

### 8.4 Documentation

- Module-level docstrings on every file.
- Function/method docstrings on significant functions.
- Extensive inline comments explaining design decisions.
- Cross-references to spec documents (e.g., "M0.1", "P7.3", "SPECS section 3").

---

## 9. Issues and Areas for Improvement

### 9.1 Potential Issues

1. **inception.py is 1846 lines** -- the largest file by far. It mixes the wizard logic, grounded recon, workspace scaffolding, skill vendoring, and .env/.mcp.json generation. Consider splitting into inception_wizard.py, inception_scaffold.py, and inception_recon.py.

2. **Inline import of chromadb** in orchestrator.py (lines 219, 326) -- this is a heavy dependency imported at runtime only when needed. The pattern is acceptable but should be documented as a soft dependency.

3. **gent_screen.py line 95**: sys.path.insert(0, ...) is used to allow running from repo root without install. This is fragile and only works when the file is run directly.

4. **console/api/audit.py line 33**: REPO_ROOT = Path(__file__).resolve().parents[4] is a hardcoded path traversal that assumes a specific directory depth. If the package structure changes, this breaks silently.

5. **
escreen_workspace.py** (34 lines) is a thin alias that imports rom agent_screen import main -- this works but the sys.path.insert on line 29 is fragile.

6. **No type stubs or py.typed marker** -- the package doesn't declare itself as typed, which could affect downstream consumers.

7. **orchestrator.py _log_audit_event()** (line 704) uses hash(action + description) for event IDs, which is not cryptographically secure and could theoretically collide. The console's _journal_event() uses uuid.uuid4().hex[:6] which is better.

8. **doctor.py _read_env_file()** is duplicated in mcp_setup.py (lines 166-185 vs 133-154). These should be extracted into a shared utility.

### 9.2 Architectural Observations

1. **No dependency injection** in orchestrator.py -- the kit classes are instantiated directly. Testability relies on the kits themselves being testable.

2. **The 10-stage pipeline is monolithic** -- stages 5-9 are tightly coupled to the screening output. Consider making each stage independently testable with fixture data.

3. **The console subsystem is self-contained** -- good separation of concerns. The REST API serves canonical workspace files without owning state.

4. **The recon subsystem is well-isolated** -- injectable search_fn, CWD-independent cache, and hermetic test seams.

5. **The grounded recon loop** (inception.py lines 1034-1273) is complex but well-documented with spec cross-references.

---

## 10. Summary Statistics

| Metric | Value |
|--------|-------|
| Total Python files | 31 |
| Total lines of code | ~7,800 |
| Largest file | inception.py (1,846 lines) |
| Smallest file | console/api/__init__.py (1 line) |
| Subpackages | 4 (
econ/, console/, console/api/, console/runtimes/, integrations/) |
| External kit imports | 6 kits |
| Search providers | 6 |
| CLI commands | 10 + 3 (log sub-app) |
| Console API endpoints | ~20 |
| Pipeline stages | 10 |
| Built-in pipeline templates | 5 |
| Actions (job runner) | 14 |


---

<!-- Source: 03_tools_analysis.md -->
﻿# Tools Directory Comprehensive Analysis

**Date**: 2026-09-14
**Scope**: `C:\Users\mouadh\Documents\nexus-scholar-harness\tools\`

---

## 1. Complete Listing of All Kits

The `tools/` directory contains **8 kits** that together form the Nexus Scholar Suite -- a modular toolkit for systematic literature reviews.

| # | Kit Name | Version | Description | CLI Entry Point | Package Name |
|---|----------|---------|-------------|-----------------|--------------|
| 1 | `scholar-search-kit` | 0.1.0 | Federated academic search, deduplication, verification, and export | `scholar-search` | `scholar_search` |
| 2 | `scholar-protocol-kit` | 1.0.0 | Phase 0 protocol.json schema, canonical serializer, and validation CLI | `scholar-protocol` | `scholar_protocol` |
| 3 | `scholar-pdf-kit` | 0.1.0 | Automated Open Access Discovery and PDF downloader using Unpaywall/OpenAlex | `scholar-pdf` | `scholar_pdf` |
| 4 | `scholar-bib-kit` | 0.1.0 | Manage, lint, and deduplicate BibTeX databases | `scholar-bib` | `scholar_bib` |
| 5 | `scholar-rag-kit` | 0.1.0 | Scientific RAG, structural chunking, and graph-boosted synthesis | `scholar-rag` | `scholar_rag` |
| 6 | `scholar-graph-kit` | 0.1.0 | Build and visualize citation graphs from scholar search results | `scholar-graph` | `scholar_graph` |
| 7 | `scholar-agent-kit` | 0.1.0 | MCP Server exposing all Nexus Scholar tools to AI Agents | `scholar-agent` | `scholar_agent` |
| 8 | `scholar-verify-kit` | 0.1.0 | Post-screening trust verification (retraction, open-science, COI, risk-of-bias) | `scholar-verify` | `scholar_verify` |

---

## 2. Kit Descriptions and Purposes

### 2.1 scholar-search-kit (Foundation Layer)

**Purpose**: The discovery, deduplication, and verification backbone of the suite. Provides unified search across multiple academic databases.

**Key Capabilities**:
- Federated search across 6 providers: OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv, bioRxiv
- Citation snowballing (forward and backward) and multi-hop BFS chaining
- Document verification and hallucination detection against Crossref/OpenAlex
- Smart deduplication by persistent identifiers (DOI, arXiv ID, PMID, OpenAlex ID, S2 ID) and fuzzy title matching (>=97% similarity)
- PRISMA 2020 title/abstract screening with protocol-driven inclusion/exclusion criteria
- Import/export in JSON, JSONL, CSV, and RIS formats

**Key Classes**:
- `SearchEngine` - Orchestrates search across multiple providers (`src/scholar_search/engine.py:21`)
- `Deduplicator` - Two-tier deterministic deduplication (`src/scholar_search/dedup.py:21`)
- `DocumentVerifier` - Citation existence verification (`src/scholar_search/verifier.py:45`)
- `AcademicHttpClient` - HTTP client with caching (hishel), rate limiting, retries (`src/scholar_search/http_client.py:47`)
- `SearchProvider` (Protocol) - Provider contract (`src/scholar_search/providers/base.py:12`)
- `BaseAPIProvider` (ABC) - Base class for live API providers (`src/scholar_search/providers/base.py:30`)

**Data Models** (`src/scholar_search/models.py`):
- `Document` (line 56) - Normalized scholarly document with rich metadata
- `ExternalIds` (line 8) - Persistent identifier container
- `Query` (line 128) - Search query specification
- `DocumentCluster` (line 138) - Deduplication cluster with representative document

**Providers** (`src/scholar_search/providers/`):
- `OpenAlexProvider` - OpenAlex REST API
- `SemanticScholarProvider` - Semantic Scholar API
- `CrossrefProvider` - Crossref REST API
- `ArxivProvider` - arXiv API
- `PubMedProvider` - PubMed/NCBI API
- `BiorxivProvider` - bioRxiv API

### 2.2 scholar-protocol-kit (Contract Spine)

**Purpose**: The contract spine of the research pipeline. Defines the `protocol.json` schema that drives all downstream kits.

**Key Capabilities**:
- Pydantic v2 models as sole runtime source of truth for protocol.json
- Canonical serializer producing deterministic JSON bytes + SHA-256 fingerprint
- Validation engine with structural (Pydantic) + cross-field rules
- Compiler resolving Socratic IntentPackets into full canonical protocols
- Renderer generating Markdown PRISMA SCREENING_CRITERIA.md
- Extraction API for dynamic Pydantic schema generation for RAG consumption

**Key Modules** (`src/scholar_protocol/`):
- `models.py` (lines 1-351) - Pydantic v2 models (ResearchProtocol, ResearchQuestion, ScreeningCriteria, etc.)
- `canonical.py` - Deterministic serializer + SHA-256 fingerprint
- `validate.py` - Structural + cross-field validation with ValidationReport
- `compiler.py` (lines 1-256) - IntentPacket to ResearchProtocol compiler
- `render.py` (lines 1-89) - Markdown SCREENING_CRITERIA.md generator
- `extraction.py` - Dynamic Pydantic schema synthesis for RAG
- `presets.py` - Playbook presets and configuration logic
- `cli.py` (lines 1-248) - Typer CLI with validate, fingerprint, canon, compile, render-criteria, extraction-schema, extraction-prompt commands

**Enumerations** (`src/scholar_protocol/models.py`):
- `PlaybookType` (line 27) - PRISMA_SLR, SCOPING_REVIEW, RAPID_EVIDENCE, DESIGN_SCIENCE, STUDENT_DISSERTATION
- `EpistemologicalParadigm` (line 46) - POSITIVIST, INTERPRETIVIST, DESIGN_SCIENCE, PRAGMATIST_MIXED
- `DimensionDataType` (line 62) - FREE_TEXT, NUMERIC, CATEGORICAL, LIST

**JSON Schema**: `schemas/v1/protocol.schema.json` (kept in sync via CI)

### 2.3 scholar-pdf-kit (PDF Acquisition)

**Purpose**: Automated Open Access Discovery and PDF downloader. Resolves DOIs to hosted PDF files across university repositories and open archives.

**Key Capabilities**:
- DOI-to-PDF resolution via OpenAlex (Unpaywall API)
- Concurrent async PDF downloads with aiohttp
- Integrity validation via magic bytes (PDF header/trailer)
- Institutional proxy support (EZproxy, subdomain, prefix styles)
- Smart naming (Author_Year_Title format)
- PDF-to-Markdown extraction with PyMuPDF, Docling, or Grobid engines
- Manual PDF ingestion with metadata tagging

**Key Classes** (`src/scholar_pdf/`):
- `AsyncPDFDownloader` (`downloader.py:35`) - Async PDF downloader with retry/backoff
- `DownloadResult` (`downloader.py:27`) - Download outcome dataclass
- `PyMuPDFEngine` (`extract.py:16`) - Fast structured Markdown extractor
- `DoclingEngine` (`extract.py`) - Docling-based extraction
- `GrobidEngine` (`extract.py`) - Grobid service extraction

**Configuration** (`src/scholar_pdf/config.py`):
- `Settings` (line 6) - Pydantic Settings with proxy, timeout, validation options

### 2.4 scholar-bib-kit (BibTeX Management)

**Purpose**: Manage, lint, and deduplicate BibTeX databases.

**Key Capabilities**:
- BibTeX file parsing and serialization (via bibtexparser)
- Linting: title wrapping, key standardization (AuthorYear format)
- Deduplication by DOI and title matches
- Merging multiple BibTeX files
- Resolution of messy entries via Crossref API

**Key Classes** (`src/scholar_bib/`):
- `BibParser` (`parser.py:5`) - Static load/save methods
- `BibLinter` (`linter.py`) - Title wrapping, key generation
- `BibDeduplicator` (`deduplicator.py:9`) - DOI/title-based dedup
- `BibResolver` (`resolver.py`) - Crossref API resolution

### 2.5 scholar-rag-kit (Retrieval-Augmented Generation)

**Purpose**: Scientific RAG engine with structural chunking, graph-boosted retrieval, and grounded synthesis.

**Key Capabilities**:
- AST heading hierarchy structural chunking with breadcrumb context
- ChromaDB vector store with deterministic upsert idempotency
- Hybrid graph-boosted retrieval (dense cosine similarity + PageRank + seed boost)
- Grounded synthesis with atomic citation tokens and automated entailment verification
- Cross-study methodology comparison matrix (7 dimensions)
- Consensus Cartographer for claim clustering

**Key Classes** (`src/scholar_rag/`):
- `MarkdownChunker` (`chunker.py:12`) - AST heading hierarchy parser
- `ScholarIndexer` (`indexer.py:17`) - ChromaDB indexing with rich metadata
- `ScholarRetriever` (`retriever.py:18`) - Hybrid vector search with PageRank boosting
- `GroundedSynthesisEngine` (`synthesis.py:62`) - Synthesis with claim entailment
- `MatrixExtractor` (`matrix.py`) - Dynamic protocol matrix extraction
- `ConsensusCartographer` (`consensus.py`) - Claim clustering and consensus analysis

### 2.6 scholar-graph-kit (Citation Networks)

**Purpose**: Bibliometric network construction and visualization engine.

**Key Capabilities**:
- Asynchronous citation graph construction from DOIs via OpenAlex
- Directed citation graph (nx.DiGraph) with citing/cited relationships
- Normalized PageRank centrality computation
- Interactive PyVis HTML visualization with force-directed layouts
- Node-link JSON export for RAG ingestion

**Key Classes** (`src/scholar_graph/`):
- `CitationGraphBuilder` (`builder.py:11`) - Async citation graph builder
- `GraphVisualizer` (`visualizer.py:9`) - PyVis HTML generator

### 2.7 scholar-agent-kit (MCP Server)

**Purpose**: FastMCP Server exposing all Nexus Scholar tools to AI Agents via Model Context Protocol.

**Key Capabilities**:
- Exposes all kit functionalities as MCP tools
- Session-based FAIR recon memory (recon_probe, recon_distill, recon_delta)
- Protocol compilation and validation
- Federated search, deduplication, screening
- PDF extraction, RAG indexing, query, synthesis
- Citation graph building
- BibTeX cleaning
- Multi-screener reconciliation
- Verbatim claim verification
- Phase-4 verification (retraction, open-science, COI, risk-of-bias, trust-context)

**Key File** (`src/scholar_agent/server.py`):
- `MCPServer` instance (line 132)
- 18+ MCP tool functions registered via `@mcp.tool()` decorator
- Harness source resolution adapter (lines 81-101) for runtime import of `scholar_harness.recon`

**MCP Tools**:
- `nexus_protocol_compile` - Compile intent.json to protocol.json
- `nexus_protocol_validate` - Validate protocol schema
- `nexus_protocol_render_criteria` - Render screening criteria markdown
- `nexus_discover` - Search academic literature
- `nexus_dedup` - Deduplicate paper collections
- `nexus_screen` - Screen against protocol criteria
- `nexus_extract_pdf` - Extract PDF to Markdown
- `nexus_rag_index` - Index documents into ChromaDB
- `nexus_rag_query` - Query with PageRank boosting
- `nexus_rag_synthesize` - Generate grounded synthesis
- `nexus_matrix_extract` - Extract protocol matrix dimensions
- `nexus_graph_build` - Build citation graph
- `nexus_bib_clean` - Clean BibTeX files
- `nexus_screen_reconcile` - Reconcile multi-screener decisions
- `nexus_verify_claims` - Verify synthesis claims
- `nexus_verify_phase4` - Run Phase-4 verification streams
- `recon_probe` - Probe literature surface
- `recon_distill` - Distill pool into micro-taxonomy
- `recon_delta` - Adaptive probe horizon for gaps

### 2.8 scholar-verify-kit (Trust Verification)

**Purpose**: Post-screening trust verification for systematic reviews. Certifies that the evidence base feeding a synthesis is safe to quote.

**Key Capabilities**:
- Retraction status check via OpenAlex + Crossref APIs
- Data/Code availability (DAS/CAS) regex baseline over extracted fulltext
- Conflict-of-interest audit aggregation with deterministic relabel
- Deterministic QUADAS-2/PROBAST risk-of-bias scoring (D1-D4)
- Trust-weighted consensus annotation (merges Phase-4 outputs with Consensus Cartographer)
- Verbatim claim attribution verification (character-window and token n-gram matching)

**Key Classes** (`src/scholar_verify/`):
- `RetractionChecker` (`retraction.py:35`) - OpenAlex + Crossref retraction check
- `VerifyHttpClient` (`http_client.py:15`) - Sync HTTP client with retry/backoff
- `VerbatimClaimVerifier` (`verbatim.py`) - Character-window and token n-gram matching

---

## 3. Internal Structure of Each Kit

### 3.1 scholar-search-kit

```
tools/scholar-search-kit/
  pyproject.toml
  README.md
  uv.lock
  src/scholar_search/
    __init__.py           # Public API re-exports (52 lines)
    cli.py                # Typer CLI (704 lines)
    config.py             # Pydantic Settings (56 lines)
    models.py             # Document, Query, ExternalIds, Author (154 lines)
    engine.py             # SearchEngine orchestrator (111 lines)
    dedup.py              # Deduplicator (223 lines)
    verifier.py           # DocumentVerifier (239 lines)
    export.py             # Exporter (76 lines)
    importers.py          # RIS/JSON/JSONL importers (183 lines)
    http_client.py        # AcademicHttpClient (122 lines)
    screening.py          # PRISMA 2020 screening (745 lines)
    snowball.py           # CitationChainer
    protocol_adapter.py   # Protocol-to-Query compiler (90 lines)
    query_translator.py   # Query translation
    exceptions.py         # Custom exception hierarchy (32 lines)
    providers/
      __init__.py         # Provider re-exports (20 lines)
      base.py             # SearchProvider protocol, BaseAPIProvider ABC (123 lines)
      openalex.py         # OpenAlex provider
      semanticscholar.py  # Semantic Scholar provider
      crossref.py         # Crossref provider
      arxiv.py            # arXiv provider
      pubmed.py           # PubMed provider
      biorxiv.py          # bioRxiv provider
  tests/                  # 12 test files + cassettes + fixtures
  examples/
    course_demo_api.py
```

### 3.2 scholar-protocol-kit

```
tools/scholar-protocol-kit/
  pyproject.toml
  README.md                               # Comprehensive (169 lines)
  uv.lock
  src/scholar_protocol/
    __init__.py         # Public API (75 lines, comprehensive)
    cli.py              # Typer CLI (248 lines)
    models.py           # Pydantic v2 models (351 lines)
    canonical.py        # Deterministic serializer
    validate.py         # Validation engine
    compiler.py         # IntentPacket compiler (256 lines)
    intent.py           # IntentPacket model
    render.py           # Markdown renderer (89 lines)
    extraction.py       # Dynamic schema synthesis
    presets.py          # Playbook presets
  schemas/v1/
    protocol.schema.json  # JSON Schema (CI-synced)
  tests/                # 6 test files + fixtures (valid/invalid/canonical)
```

### 3.3 scholar-pdf-kit

```
tools/scholar-pdf-kit/
  pyproject.toml                          # Includes [extract] optional deps
  README.md                               # Comprehensive (106 lines)
  uv.lock
  docker-compose.grobid.yml
  src/scholar_pdf/
    __init__.py           # Comprehensive re-exports (39 lines)
    cli.py                # Typer CLI (279 lines)
    config.py             # Pydantic Settings (39 lines)
    models.py             # Data models
    downloader.py         # AsyncPDFDownloader (287 lines)
    extract.py            # PyMuPDF/Docling/Grobid engines (136 lines)
    validator.py          # PDF validation (magic bytes)
    publisher_patterns.py # Direct-PDF URL patterns
  tests/
  docs/
    tutorial.md
    api_reference.md
```

### 3.4 scholar-bib-kit

```
tools/scholar-bib-kit/
  pyproject.toml
  README.md                               # Minimal (3 lines)
  uv.lock
  src/scholar_bib/
    __init__.py           # Minimal (1 line)
    cli.py                # Typer CLI (127 lines)
    parser.py             # BibParser (14 lines)
    linter.py             # BibLinter
    deduplicator.py       # BibDeduplicator (60 lines)
    resolver.py           # BibResolver (Crossref API)
  tests/
  clean.bib, messy.bib, messy_no_doi.bib, resolved.bib  # Example files
  docs/
```

### 3.5 scholar-rag-kit

```
tools/scholar-rag-kit/
  pyproject.toml
  README.md                               # Comprehensive (134 lines)
  uv.lock
  LICENSE                                 # MIT
  src/scholar_rag/
    __init__.py           # Comprehensive re-exports (53 lines)
    cli.py                # Typer CLI (443 lines)
    models.py             # Pydantic models (269 lines)
    chunker.py            # MarkdownChunker (265 lines)
    indexer.py            # ScholarIndexer (267 lines)
    retriever.py          # ScholarRetriever (281 lines)
    synthesis.py          # GroundedSynthesisEngine (415 lines)
    matrix.py             # MatrixExtractor
    embedder.py           # Embedding provider abstraction
    consensus.py          # ConsensusCartographer
  tests/                  # 8 test files
  docs/
```

### 3.6 scholar-graph-kit

```
tools/scholar-graph-kit/
  pyproject.toml
  README.md                               # Comprehensive (100 lines)
  uv.lock
  src/scholar_graph/
    __init__.py           # Minimal (1 line)
    cli.py                # Typer CLI (125 lines)
    models.py             # GraphNode, GraphEdge (14 lines)
    builder.py            # CitationGraphBuilder (130 lines)
    visualizer.py         # GraphVisualizer (59 lines)
    config.py             # Configuration
  tests/
    test_builder.py
  docs/
  map.html, test_graph.html               # Example visualizations
```

### 3.7 scholar-agent-kit

```
tools/scholar-agent-kit/
  pyproject.toml                          # Depends on all other kits
  .gitignore
  uv.lock
  src/scholar_agent/
    server.py             # FastMCP server (1200+ lines)
    calibration.py        # Pre-flight screener calibration (467 lines)
  tests/
    test_calibration.py
    test_server.py
  .cache/               # Recon session cache
```

### 3.8 scholar-verify-kit

```
tools/scholar-verify-kit/
  pyproject.toml
  README.md                               # Detailed (51 lines)
  src/scholar_verify/
    __init__.py           # Module re-exports (5 lines)
    cli.py                # Typer CLI (272 lines)
    http_client.py        # VerifyHttpClient (47 lines)
    retraction.py         # RetractionChecker (287 lines)
    open_science.py       # DAS/CAS regex baseline (276 lines)
    coi.py                # COI audit aggregator (304 lines)
    risk_of_bias.py       # QUADAS-2/PROBAST scoring (266 lines)
    trust_context.py      # Trust-weighted consensus (380 lines)
    verbatim.py           # Verbatim claim verifier (179 lines)
  tests/                  # 6 test files
  docs/
```

---

## 4. Dependencies and Integration Points

### 4.1 Dependency Graph

```
scholar-protocol-kit  (zero kit dependencies - foundation)
    |
scholar-search-kit    (zero kit dependencies - foundation)
    |
    +-- scholar-bib-kit          (depends on: search-kit)
    +-- scholar-pdf-kit          (depends on: search-kit)
    +-- scholar-graph-kit        (depends on: search-kit)
    |
    +-- scholar-rag-kit          (depends on: search-kit, bib-kit, graph-kit)
            |
            +-- scholar-agent-kit  (depends on: ALL kits + harness recon)
                    |
                    +-- scholar-verify-kit  (depends on: requests only)
```

### 4.2 Detailed Dependency Matrix

| Kit | Kit Dependencies | External Dependencies |
|-----|-----------------|----------------------|
| scholar-protocol-kit | None | pydantic>=2.0, typer>=0.9, rich>=13.0 |
| scholar-search-kit | None | pydantic>=2.0, pydantic-settings>=2.0, httpx>=0.28, hishel==0.0.32, rich>=13.9, typer>=0.9 |
| scholar-bib-kit | scholar-search-kit | typer>=0.9, rich>=13.0, bibtexparser>=2.0b7, pydantic>=2.0 |
| scholar-pdf-kit | scholar-search-kit | pydantic>=2.0, pydantic-settings>=2.0, aiohttp>=3.9, typer>=0.9, requests>=2.31, rich>=13.0, tenacity>=8.0, pypdf>=4.0, pymupdf>=1.24; optional: docling>=2.5 |
| scholar-graph-kit | scholar-search-kit | typer>=0.9, rich>=13.0, networkx>=3.0, pyvis>=0.3.2, aiohttp>=3.9, pydantic>=2.0 |
| scholar-rag-kit | scholar-search-kit, scholar-bib-kit, scholar-graph-kit | typer>=0.9, rich>=13.0, chromadb>=0.4.22, sentence-transformers>=2.3.1, openai>=1.12.0, networkx>=3.0, pydantic>=2.0, bibtexparser>=2.0b7 |
| scholar-agent-kit | ALL kits (protocol, search, bib, pdf, rag, graph) | mcp |
| scholar-verify-kit | None (standalone) | typer>=0.9, rich>=13.0, requests>=2.31 |

### 4.3 Integration with Main Harness

The harness orchestrator (`src/scholar_harness/orchestrator.py`, lines 16-37) directly imports from kits:

```python
from scholar_graph.builder import CitationGraphBuilder
from scholar_graph.visualizer import GraphVisualizer
from scholar_pdf.extract import PyMuPDFEngine
from scholar_protocol.models import ResearchProtocol
from scholar_rag.indexer import ScholarIndexer
from scholar_rag.matrix import MatrixExtractor
from scholar_rag.retriever import ScholarRetriever
from scholar_rag.synthesis import GroundedSynthesisEngine
from scholar_search.dedup import Deduplicator
from scholar_search.engine import SearchEngine
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.providers import (OpenAlexProvider, SemanticScholarProvider, ...)
from scholar_search.verifier import DocumentVerifier
```

### 4.4 [tool.uv.sources] Cross-References

All kits use relative path references for editable installs:

```toml
[tool.uv.sources]
scholar-search-kit = { path = "../scholar-search-kit", editable = true }
```

This enables `uv pip install -e .` to resolve inter-kit dependencies correctly within the monorepo.

---

## 5. CLI Interfaces and Usage Patterns

### 5.1 Common CLI Patterns

All kits follow consistent patterns:

1. **Framework**: Typer CLI with Rich console output
2. **Entry Point**: Defined in `[project.scripts]` of pyproject.toml
3. **Invocation**: `uv run <cli-name> <command> [options]`
4. **Windows UTF-8**: All CLIs include `sys.stdout.reconfigure(encoding="utf-8")` for Windows compatibility

### 5.2 CLI Command Summary

| Kit | CLI | Commands |
|-----|-----|----------|
| scholar-search-kit | `scholar-search` | `search`, `snowball`, `chain`, `import`, `dedup`, `verify`, `export`, `screen` |
| scholar-protocol-kit | `scholar-protocol` | `validate`, `fingerprint`, `canon`, `compile`, `render-criteria`, `extraction-schema`, `extraction-prompt` |
| scholar-pdf-kit | `scholar-pdf` | `download`, `ingest`, `extract` |
| scholar-bib-kit | `scholar-bib` | `lint`, `merge`, `dedup`, `resolve` |
| scholar-rag-kit | `scholar-rag` | `index`, `query`, `synthesize`, `consensus`, `matrix`, `stats` |
| scholar-graph-kit | `scholar-graph` | `build`, `pagerank` |
| scholar-agent-kit | `scholar-agent` | Starts FastMCP server (no subcommands) |
| scholar-verify-kit | `scholar-verify` | `retraction`, `open-science`, `coi`, `risk-of-bias`, `trust-context`, `all`, `verbatim-claims` |

### 5.3 Typical Pipeline Usage

```bash
# Phase 0: Protocol creation
scholar-protocol compile intent.json > protocol.json
scholar-protocol validate protocol.json
scholar-protocol render-criteria protocol.json > SCREENING_CRITERIA.md

# Phase 1: Discovery
scholar-search search --protocol protocol.json --output results.json
scholar-search dedup results.json --output deduped.json
scholar-search screen --input deduped.json --protocol protocol.json --output-dir literature/

# Phase 2: PDF acquisition
scholar-pdf download --input literature/included.json --output pdfs/ --smart-names
scholar-pdf extract pdfs/ --output extracted/ --engine pymupdf

# Phase 2.5: BibTeX management
scholar-bib lint references.bib --output clean.bib
scholar-bib dedup references.bib

# Phase 2: RAG indexing
scholar-rag index extracted/ --bib references.bib --workspace-id SCI-000412
scholar-rag query "research question" --section-category methodology --limit 5

# Phase 2: Citation graph
scholar-graph build --input literature/included.json --output graph.html

# Phase 2: Synthesis
scholar-rag synthesize "research question" --rq-id RQ1 --output synthesis.md

# Phase 4: Verification
scholar-verify all --workspace workspaces/my-project/ --skip-retraction
scholar-verify verbatim-claims --claims synthesis/claims.json --extracted extracted/
```

---

## 6. Shared Utilities and Patterns

### 6.1 Windows UTF-8 Reconfiguration

All 7 CLI modules include the same pattern (`src/scholar_*/cli.py`):

```python
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
```

This is a duplicated utility that could be extracted into a shared module.

### 6.2 HTTP Client Abstraction

Two HTTP client implementations exist:

1. **Async**: `scholar_search.http_client.AcademicHttpClient` (hishel caching, rate limiting, retries)
   - Used by: scholar-search-kit, scholar-pdf-kit, scholar-graph-kit, scholar-agent-kit
   - Import: `from scholar_search.http_client import AcademicHttpClient`

2. **Sync**: `scholar_verify.http_client.VerifyHttpClient` (requests-based, retry/backoff)
   - Used by: scholar-verify-kit only
   - Standalone implementation, does not depend on search-kit

### 6.3 Configuration Pattern

Three kits use Pydantic Settings:
- `scholar_search.config.Settings` (env prefix: `SCHOLAR_`) - `src/scholar_search/config.py:9`
- `scholar_pdf.config.Settings` (no prefix) - `src/scholar_pdf/config.py:6`
- `scholar_protocol` (no config module - uses model defaults)

### 6.4 Data Model Patterns

- **Pydantic v2**: Used by protocol-kit, rag-kit, verify-kit for structured validation
- **Dataclasses**: Used by search-kit (Document, Query, ExternalIds), graph-kit (GraphNode, GraphEdge)
- **bibtexparser models**: Used by bib-kit for BibTeX-specific structures

### 6.5 CLI Pattern (Typer + Rich)

All CLIs follow the same structure:

```python
import typer
from rich.console import Console

app = typer.Typer(help="...", no_args_is_help=True)
console = Console()

@app.command("command-name")
def command(...):
    """Docstring for help."""
    ...
```

### 6.6 Deferred Imports Pattern

Several kits use deferred imports for heavy dependencies:

```python
# scholar-graph-kit builder.py (line 30)
import networkx as nx  # Deferred (P7.7): module load stays stdlib-only

# scholar-rag-kit indexer.py (line 39)
import chromadb  # deferred: keeps import chromadb-free

# scholar-rag-kit retriever.py (line 56)
import networkx as nx  # deferred: keeps import networkx-free
```

### 6.7 Deterministic/Idempotent Patterns

- **scholar-protocol-kit**: Canonical serialization produces byte-identical JSON
- **scholar-rag-kit**: Chunk IDs are deterministic (`chk-<doc_id>-<sec_slug>-<index:02d>`); ChromaDB upserts are idempotent
- **scholar-search-kit**: Deduplication is deterministic (same inputs -> same clusters)
- **scholar-verify-kit**: All streams except retraction are deterministic

### 6.8 Audit Logging

The RAG indexer automatically logs `RAG_INDEX_BUILT` events to `audit/journal.jsonl`.

---

## 7. Test Coverage and Quality

### 7.1 Test Directory Summary

| Kit | Test Files | Key Test Areas |
|-----|-----------|----------------|
| scholar-search-kit | 12 test files | CLI, dedup, engine, importers/exporters, models, providers, protocol adapter, query translator, screening, snowball, verifier |
| scholar-protocol-kit | 6 test files | canonical, CLI, compiler, models, schema sync, validate |
| scholar-pdf-kit | Tests exist | Downloader, extraction |
| scholar-bib-kit | Tests exist | Parser, deduplicator, linter |
| scholar-rag-kit | 8 test files | chunker, CLI, consensus, embedder, indexer, matrix, retriever, synthesis |
| scholar-graph-kit | 1 test file | builder |
| scholar-agent-kit | 2 test files | calibration, server |
| scholar-verify-kit | 6 test files | CLI, COI, open_science, retraction, risk_of_bias, trust_context |

### 7.2 Test Infrastructure

- **VCR.py cassettes**: scholar-search-kit uses HTTP recording for deterministic tests
- **Golden fixtures**: scholar-protocol-kit uses golden files for canonical serialization verification
- **Mock providers**: scholar-search-kit includes InMemoryProvider for offline testing

---

## 8. Issues and Areas for Improvement

### 8.1 Duplicated Windows UTF-8 Code

**Files**: All `cli.py` files (7 occurrences)
**Issue**: The Windows UTF-8 reconfiguration pattern is copy-pasted across all CLI modules.
**Recommendation**: Extract into a shared utility module (e.g., `scholar_common.cli_compat`).

### 8.2 Missing README for scholar-agent-kit

**File**: `tools/scholar-agent-kit/README.md`
**Issue**: The agent-kit has no README.md file (file not found).
**Recommendation**: Add documentation for the MCP server, tool list, and usage instructions.

### 8.3 Inconsistent __init__.py Exports

**Issue**: Some kits have comprehensive exports (protocol-kit: 75 lines, rag-kit: 53 lines, pdf-kit: 39 lines) while others have minimal exports (bib-kit: 1 line, graph-kit: 1 line, verify-kit: 5 lines).
**Recommendation**: Standardize public API surface across all kits.

### 8.4 scholar-verify-kit is Isolated

**Issue**: verify-kit has zero kit dependencies (only requests). It uses its own HTTP client rather than the shared `AcademicHttpClient`.
**Recommendation**: Consider whether verify-kit should use the shared HTTP client for consistency, or document the intentional isolation.

### 8.5 scholar-bib-kit Minimal Documentation

**File**: `tools/scholar-bib-kit/README.md` (3 lines)
**Issue**: The README is essentially empty.
**Recommendation**: Add usage documentation, API reference, and examples matching other kits.

### 8.6 scholar-graph-kit Sparse Models

**File**: `tools/scholar-graph-kit/src/scholar_graph/models.py` (14 lines)
**Issue**: The models module is very thin with simple dataclasses.
**Recommendation**: Consider Pydantic models for consistency with other kits, or document the design choice.

### 8.7 Dual HTTP Client Implementations

**Issue**: Two separate HTTP client implementations exist:
- `scholar_search.http_client.AcademicHttpClient` (async, hishel caching)
- `scholar_verify.http_client.VerifyHttpClient` (sync, requests-based)

**Recommendation**: Document the rationale for separation, or consider a shared base with sync/async variants.

### 8.8 scholar-agent-kit Harness Import Hack

**File**: `tools/scholar-agent-kit/src/scholar_agent/server.py` (lines 81-106)
**Issue**: The agent-kit uses a `sys.path` manipulation to import `scholar_harness.recon` at runtime.
**Recommendation**: This is a known design trade-off documented in the code. The adapter seam is well-documented but should be monitored.

### 8.9 Version Inconsistency

**Issue**: Most kits are at version 0.1.0, but scholar-protocol-kit is at 1.0.0.
**Recommendation**: This appears intentional (protocol-kit is the "contract spine" with frozen serialization rules). Document the versioning strategy.

### 8.10 scholar-rag-kit Heavy Dependencies

**Issue**: scholar-rag-kit pulls in chromadb, sentence-transformers, openai, and networkx -- some of the heaviest dependencies in the suite.
**Recommendation**: The deferred import pattern (chromadb, networkx) helps with import time. Consider whether some dependencies could be optional extras.

---

## 9. Architecture Summary

The tools directory implements a **layered, composable architecture** for systematic literature reviews:

```
Layer 4 (Agent):     scholar-agent-kit (MCP server, all tools exposed)
                      scholar-verify-kit (trust verification)

Layer 3 (RAG):       scholar-rag-kit (chunking, indexing, retrieval, synthesis)
                      scholar-graph-kit (citation networks, PageRank)

Layer 2 (Acquisition): scholar-pdf-kit (PDF download, extraction)
                        scholar-bib-kit (BibTeX management)

Layer 1 (Discovery):  scholar-search-kit (federated search, dedup, screening)

Layer 0 (Contract):   scholar-protocol-kit (protocol.json schema, validation)
```

**Key Design Principles**:
1. **Protocol-driven**: All downstream kits read `protocol.json` validated by protocol-kit
2. **Modular**: Each kit is independently installable and testable
3. **Composable**: Kits can be used via CLI or Python API
4. **Deterministic**: Core operations produce byte-identical outputs
5. **Auditable**: Every significant step logs to `audit/journal.jsonl`
6. **MCP-exposed**: All tools accessible to AI agents via scholar-agent-kit

---

*Analysis completed on 2026-09-14. Total kits analyzed: 8. Total source files reviewed: 80+.*


---

<!-- Source: 06_scripts_analysis.md -->
﻿# Scripts Directory Comprehensive Analysis

**Date:** 2026-09-14
**Directory:** `C:\Users\mouadh\Documents\nexus-scholar-harness\scripts\`

---

## 1. Complete Script Listing

| Script | Lines | Purpose | Category |
|--------|-------|---------|----------|
| `install_plugins.py` | 357 | Unified plugin installer for all 8 scholarly toolkits | Deployment |
| `generate_nexus_scholar_pins.py` | 116 | Code generation for metapackage pins | Code Generation |
| `validate_manifest.py` | 35 | Validates plugin manifest structure | Validation |
| `pre_commit_check.py` | 112 | Pre-commit checklist for plugin harness refactor | Validation |
| `push_tools.py` | 82 | Push toolkit changes to remote repositories | Deployment |
| `generate_latex.py` | 137 | Generate XeLaTeX manuscripts from markdown sources | Code Generation |
| `sync_skills_bundle.py` | 84 | Sync canonical skills to plugin bundle | Synchronization |
| `reconcile_dual_screening.py` | 416 | Reconcile dual-screening decisions for literature review | Data Processing |
| `hooks/pre-push` | 38 | Git pre-push hook enforcing contribution workflow | CI/CD |

---

## 2. Automation Workflows

### 2.1 Plugin Installation Pipeline (`install_plugins.py`)
**Location:** `scripts/install_plugins.py` (lines 1-357)

**Key Features:**
- **Dependency-ordered installation** (line 77-85): Kits installed in order: protocol -> search -> pdf -> bib -> graph -> rag -> agent
- **Dual installation modes**: Local editable (`-e`) vs. Git remote installation
- **Environment detection**: Checks `NEXUS_PLUGIN_PATH` env var and `tools/` directory
- **Legacy cleanup**: Removes per-tool `.venv` directories (line 140-157)
- **Post-install verification**: Runs `--help` on each console_script (line 215-246)

**CLI Options:**
- `--manifest`: Path to plugins.json (default: `.agents/plugins/nexus-scholar/plugins.json`)
- `--plugin/-p`: Install specific plugin only
- `--dev-path/-d`: Custom dev path for kit sources
- `--git-only`: Force remote Git installation
- `--local-only`: Only install from local checkouts
- `--upgrade/-U`: Upgrade installed packages
- `--clean`: Remove legacy per-tool .venv directories
- `--verify/--no-verify`: Post-install verification

**Windows Compatibility:** Lines 27-71 handle UTF-8 encoding for emojis on Windows console.

### 2.2 Toolkit Synchronization (`push_tools.py`)
**Location:** `scripts/push_tools.py` (lines 1-82)

**Workflow:**
1. Reads plugin manifest from `.agents/plugins/nexus-scholar/plugins.json`
2. For each toolkit in `tools/`:
   - Clones remote repository (shallow clone, `--depth 1`)
   - Copies local changes to cloned repo (excluding `.git`, `.venv`, `.pytest_cache`, etc.)
   - Commits with message: `feat(<name>): synchronize toolkit with nexus-scholar monorepo`
   - Pushes to `main` branch

**Error Handling:** Graceful fallback if clone fails (initializes fresh repo).

### 2.3 Skills Bundle Synchronization (`sync_skills_bundle.py`)
**Location:** `scripts/sync_skills_bundle.py` (lines 1-84)

**Purpose:** Mirror canonical `.agents/skills/<name>` trees into the plugin bundle.

**Key Logic:**
- Canonical source: `.agents/skills/` (always edited first)
- Target: `.agents/plugins/nexus-scholar/skills/`
- **Intentional exclusions** (line 27): `pull-request-gate` is excluded from mirroring
- **Drift detection**: `--check` mode reports differences without copying
- **File comparison**: Uses `filecmp.cmp` for byte-identical verification

---

## 3. Build and Deployment Processes

### 3.1 Metapackage Pins Generation (`generate_nexus_scholar_pins.py`)
**Location:** `scripts/generate_nexus_scholar_pins.py` (lines 1-116)

**Purpose:** Generate deterministic pins snapshot for `packaging/nexus-scholar/` metapackage.

**Data Flow:**
- **Input**: `.agents/plugins/nexus-scholar/plugins.json` (source of truth for kit versions)
- **Output**: `packaging/nexus-scholar/nexus_scholar_pins.json`

**Key Features:**
- **Deterministic output**: Kits sorted by name, fixed field order (line 34-39)
- **CI freshness check**: `--check` flag fails CI when pins drift (line 62-65)
- **Cross-platform support**: Normalizes CRLF to LF for Windows compatibility (line 52-59)
- **Diff output**: Shows exact changes needed when drift detected (line 68-75)

**Fields Captured per Kit:**
- `name`, `repo`, `default_rev` (commit SHA), `console_script`

### 3.2 LaTeX Manuscript Generation (`generate_latex.py`)
**Location:** `scripts/generate_latex.py` (lines 1-137)

**Purpose:** Generate XeLaTeX manuscripts from committed markdown sources.

**Deliverables Configured (lines 66-100):**
1. **d1**: UAV-CV precision agriculture manuscript
2. **d2**: AI research harnesses trust manuscript (d2)
3. **d3**: AI research harnesses trust main manuscript
4. **d4**: Software paper scope document
5. **thesis**: Thesis assembly document

**Build Process:**
- Uses `pandoc` for Markdown -> LaTeX conversion
- Applies custom XeLaTeX preamble with:
  - Times New Roman font
  - Math symbols (->)
  - Table formatting (booktabs, longtable)
  - Figure scaling (pandocbounded)
  - Hyperlinks and fancy headers

**Build Command:** `cd latex/<name> && xelatex -output-directory=build main.tex (x2)`

---

## 4. Code Generation Patterns

### 4.1 Deterministic Pin Generation Pattern
**File:** `generate_nexus_scholar_pins.py`

**Pattern:**
```python
# Input: plugins.json with full metadata
# Transform: Extract specific fields, sort alphabetically
# Output: Deterministic JSON with fixed key order
kits = [
    {field: plugin[field] for field in FIELDS}
    for plugin in manifest["plugins"]
]
kits.sort(key=lambda kit: kit["name"])
```

**Why Deterministic?**
- CI enforces freshness with `--check`
- Prevents accidental drift between source of truth and metapackage
- Byte-identical output enables strict equality checks

### 4.2 Skills Mirroring Pattern
**File:** `sync_skills_bundle.py`

**Pattern:**
```python
# Canonical source -> Bundle target
# Exclusion list for repo-policy skills
# File-level comparison for drift detection
src = CANONICAL / name
dst = BUNDLE / name
drifted = not (dst.is_dir() and _same_tree(src, dst))
```

---

## 5. Utility Functions

### 5.1 Plugin Registry Loader (`install_plugins.py`, lines 88-100)
```python
def load_registry(manifest_path: Path) -> list[dict[str, Any]]:
    """Loads plugin list from JSON registry."""
```
- Validates manifest exists
- Extracts `plugins` array
- Returns structured plugin data

### 5.2 Local Path Resolution (`install_plugins.py`, lines 103-132)
```python
def resolve_local_path(
    plugin_name: str,
    custom_dev_path: Path | None = None,
    repo_root: Path = Path("."),
) -> Path | None:
```
- Checks multiple candidate paths:
  - Custom dev path
  - `NEXUS_PLUGIN_PATH` environment variable
  - `tools/<plugin_name>` (local checkout)
  - Sibling directories (`../<plugin_name>`, `../../<plugin_name>`)

### 5.3 Legacy Venv Cleanup (`install_plugins.py`, lines 140-157)
```python
def clean_legacy_venvs(repo_root: Path) -> None:
```
- Removes `tools/*/.venv` directories
- Prevents duplicate disk usage from per-tool virtual environments

### 5.4 Installation Verification (`install_plugins.py`, lines 215-246)
```python
def verify_installation(plugins: list[dict[str, Any]]) -> dict[str, bool]:
```
- Runs `<console_script> --help` for each installed plugin
- Returns success/failure map
- Catches `FileNotFoundError` for missing commands

### 5.5 UTF-8 Encoding Handler (`install_plugins.py`, lines 27-71)
```python
def _reconfigure_encoding_for_utf8() -> None:
```
- Windows-specific: Reconfigures stdout/stderr for emoji support
- Strategy 1: `reconfigure()` method (Python 3.7+)
- Strategy 2: Wrap streams with `io.TextIOWrapper`

### 5.6 Tree Comparison (`sync_skills_bundle.py`, lines 38-42)
```python
def _same_tree(a: Path, b: Path) -> bool:
```
- Compares file lists (excluding `__pycache__`, `.pyc`)
- Byte-level file comparison with `filecmp.cmp(shallow=False)`

---

## 6. CI/CD Integration

### 6.1 Git Pre-Push Hook (`scripts/hooks/pre-push`)
**Location:** `scripts/hooks/pre-push` (lines 1-38)

**Purpose:** Enforce contribution workflow - all improvements must go through fork + PR.

**Logic:**
- Only gates pushes to `origin` (canonical repo)
- **Allowed refs:**
  - `refs/heads/main` (housekeeping baseline)
  - `refs/tags/*` (release tags)
- **Blocked refs:** All other branches with instructions to use fork + PR

**Installation:** `git config core.hooksPath scripts/hooks`

**Error Message (lines 28-32):**
```
BLOCKED: pushing '<ref>' directly to origin (canonical repo).
  Improve on the fork and submit a pull request instead:
    git push fork <ref>
    gh pr create -R nexus-scholar-org/nexus-scholar-harness --base main
  See .agents/skills/pull-request-gate/SKILL.md
```

### 6.2 Manifest Validation (`validate_manifest.py`)
**Purpose:** Validates plugin manifest structure for CI.

**Checks:**
- Manifest file exists at expected path
- `plugins` array is non-empty
- Each plugin has required fields: `name`, `repo`, `default_rev`, `console_script`

**Exit Codes:**
- 0: All validations passed
- 1: Validation failed

### 6.3 Pre-Commit Checklist (`pre_commit_check.py`)
**Purpose:** Comprehensive pre-commit validation for plugin harness refactor.

**Checks Performed (lines 19-88):**
1. Validate plugin manifest (JSON structure, non-empty)
2. Check `install_plugins.py` syntax (`py_compile`)
3. Verify `.gitignore` includes `tools/`
4. Check README describes plugin installer
5. Verify GitHub Actions CI workflow exists
6. Check `tools/` is tracked in git (expected state)

**Output:** Pass/fail summary with recommended git commands.

### 6.4 CI Integration Points
Based on AGENTS.md and script analysis:

**CI Workflow (referenced but not found in repo):**
- Lint: `uv run ruff check scripts/`
- Plugin installer help: `uv run python scripts/install_plugins.py --help`
- Manifest schema validation: `uv run python scripts/validate_manifest.py`
- Pins freshness: `uv run python scripts/generate_nexus_scholar_pins.py --check`
- Skills drift: `uv run python scripts/sync_skills_bundle.py --check`

---

## 7. Data Processing Scripts

### 7.1 Dual-Screening Reconciliation (`reconcile_dual_screening.py`)
**Location:** `scripts/reconcile_dual_screening.py` (lines 1-416)

**Purpose:** Synchronize dual-screening decisions, 3rd-party adjudication, and Option B (Provisional 150) into primary literature deliverables.

**Input Files:**
- `literature/verified.json` - 1488 verified documents
- `literature/screening/batch_*_decisions.json` - Screener 1 decisions
- `literature/screening/batch_*_decisions_screener2.json` - Screener 2 decisions
- `literature/screening/_adjudication_resolved_group_*.json` - Adjudication decisions
- `literature/screening/_final_reconciled_include.txt` - 111 confirmed include IDs

**Processing Logic (lines 26-238):**
1. Load all screening decisions
2. Identify 39 caveat papers:
   - 22 papers with missing abstracts
   - 17 contested EXC-06 papers with in-scope cues
3. Partition documents into:
   - Included (111 confirmed + 39 provisional)
   - Excluded (1338 confirmed)
   - Conflicts (690 disputed)
4. Build structured document records with screening metadata

**Output Files:**
- `literature/included.json` - 150 papers (111 + 39)
- `literature/excluded.json` - 1338 papers
- `literature/conflicts.json` - 690 disputed papers
- `literature/screening/adjudicated_caveats.json` - 39 caveat papers
- `literature/prisma_report.json` - PRISMA metrics
- `literature/prisma_screening_report.md` - Detailed markdown report
- `literature/conflict_adjudication_log.md` - Audit ledger

**Key Metrics (lines 263-274):**
- Total identified: 1837
- Duplicates removed: 349
- Records screened: 1488
- Cohen's Kappa: 0.115 (slight agreement)
- Conflicts adjudicated: 690

**Domain-Specific Logic:**
- Agricultural UAV CV terminology regex (line 72): `crop|weed|vegetation|segmentation|UAV|drone|wheat|maize|corn|rice|canola|soybean|field|row`
- EXC-06 exclusion code handling for incomplete benchmark data

---

## 8. Areas for Improvement

### 8.1 Robustness Issues

**1. Error Handling in `push_tools.py`**
- Lines 63-68: `commit_res.stdout.splitlines()[0]` may raise IndexError if stdout is empty
- Lines 71-80: Push failure is logged but not raised as error
- **Recommendation:** Add explicit error propagation for push failures

**2. Path Validation in `generate_latex.py`**
- Lines 66-100: Hardcoded workspace paths assume specific directory structure
- **Recommendation:** Add path existence checks before processing

**3. Regex Sensitivity in `reconcile_dual_screening.py`**
- Line 72: Agricultural terminology regex is project-specific
- **Recommendation:** Make regex configurable or parameterized

### 8.2 Security Concerns

**1. Shell Injection in `pre_commit_check.py`**
- Line 9: `shell=True` in `subprocess.run` with string command
- **Recommendation:** Use list form: `["uv", "run", "python", "-m", "py_compile", "scripts/install_plugins.py"]`

**2. Temporary Directory Usage in `push_tools.py`**
- Lines 29-82: Clones remote repos to temp directory
- **Recommendation:** Ensure temp directory cleanup on failure

### 8.3 Maintainability Issues

**1. Hardcoded Paths**
- `reconcile_dual_screening.py` line 22: `WORKSPACE = REPO_ROOT / "workspaces" / "uav-cv-precision-agriculture"`
- `generate_latex.py` lines 66-100: Multiple hardcoded workspace paths
- **Recommendation:** Accept workspace path as CLI argument

**2. Magic Numbers**
- `reconcile_dual_screening.py` line 85: `assert len(caveat_39_ids) == 39`
- **Recommendation:** Extract to named constants or config

**3. DRY Violations**
- `install_plugins.py` and `validate_manifest.py` both load and validate plugins.json
- **Recommendation:** Extract shared validation logic

### 8.4 Testing Gaps

**1. No Unit Tests**
- Scripts directory has no `test_*.py` files
- **Recommendation:** Add tests for:
  - Plugin registry loading
  - Path resolution logic
  - Pin generation determinism
  - Skills synchronization

**2. Integration Testing**
- CI runs `--help` checks but not full installation
- **Recommendation:** Add integration test that installs one kit in isolated env

### 8.5 Documentation

**1. Missing Docstrings**
- `push_tools.py`: No module-level docstring
- `validate_manifest.py`: Minimal function docstrings
- **Recommendation:** Add comprehensive docstrings

**2. Usage Examples**
- Scripts lack usage examples in docstrings
- **Recommendation:** Add examples in `"""..."""` blocks

### 8.6 Performance Considerations

**1. Sequential Processing in `push_tools.py`**
- Lines 18-82: Processes toolkits sequentially
- **Recommendation:** Consider parallel processing for multiple kits

**2. Full File Reads**
- `reconcile_dual_screening.py`: Reads entire JSON files into memory
- **Recommendation:** For large datasets, consider streaming parsing

### 8.7 Cross-Platform Compatibility

**1. Path Separators**
- All scripts use `pathlib.Path` (good)
- `.gitignore` check in `pre_commit_check.py` line 48: String matching may fail on different line endings
- **Recommendation:** Normalize line endings before comparison

**2. Encoding Handling**
- `install_plugins.py` handles Windows UTF-8 (good)
- Other scripts lack explicit encoding handling
- **Recommendation:** Add `encoding="utf-8"` to all `open()` calls

---

## 9. Script Dependencies

### External Tools Required
- `uv`: Package installer (used by install_plugins.py, generate_latex.py)
- `pandoc`: Document conversion (used by generate_latex.py)
- `xelatex`: LaTeX compilation (referenced in generate_latex.py docstring)
- `git`: Version control (used by push_tools.py, pre-push hook)

### Internal Dependencies
- `.agents/plugins/nexus-scholar/plugins.json`: Source of truth for kit versions
- `tools/<kit>/`: Local kit checkouts
- `workspaces/<project>/`: Research output directories

---

## 10. Summary

The `scripts/` directory contains **9 automation scripts** covering:

- **Deployment (2 scripts):** Plugin installation and toolkit synchronization
- **Code Generation (2 scripts):** Metapackage pins and LaTeX manuscripts
- **Validation (2 scripts):** Manifest validation and pre-commit checks
- **Data Processing (1 script):** Dual-screening reconciliation
- **Synchronization (1 script):** Skills bundle mirroring
- **CI/CD (1 script):** Git pre-push hook

**Strengths:**
- Well-structured plugin architecture with dependency ordering
- Deterministic code generation with CI freshness checks
- Comprehensive validation and verification
- Cross-platform compatibility (Windows UTF-8 handling)

**Weaknesses:**
- No unit tests for scripts
- Hardcoded paths reduce flexibility
- Some error handling gaps
- Documentation could be more comprehensive

**Overall Assessment:** The scripts provide a solid foundation for the Nexus Scholar Harness automation, with clear separation of concerns and good engineering practices. The main areas for improvement are testing coverage, parameterization, and error handling robustness.


---

