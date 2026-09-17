# Source Code Analysis: src/scholar_harness/

> Generated: 2026-09-14 | Scope: every .py file under src/scholar_harness/
> Version: 1.0.0 (per __init__.py)
> Total files: 31 Python files across 5 subpackages

---

## 1. Complete File Listing with Descriptions

### 1.1 Top-Level Package (src/scholar_harness/)

| File | Lines | Purpose |
|------|------:|---------|
| __init__.py | 7 | Package root. Exports ResearchOrchestrator and __version__ = "1.0.0". |
| cli.py | 494 | **Main CLI entry point.** Typer app with commands: status, init, setup-mcp, doctor, log (sub-app), inception, sync, un, export, serve. Registered as the scholar-harness console script. |
| orchestrator.py | 731 | **Core pipeline orchestrator.** ResearchOrchestrator class: get_status(), sync_state(), un_pipeline() / un_pipeline_async(). Wires together all eight kits in a 10-stage pipeline. |
| inception.py | 1846 | **Phase-0 Socratic inception wizard.** The largest file. Implements the 4-stage methodology interview: paradigm detection, refraction grid, Socratic boundary grill, protocol emission. Also contains init_command() for P7.3 portable workspace bootstrap. |
| gent_screen.py | 850 | **PRISMA screening agent.** File-based handoff protocol: prepare, collect, status, calibration, calibrate-eval. Dual-screening reconciliation logic. |
| pipeline_executor.py | 360 | **PipelineSpec DAG executor (M5.4).** Loads a PipelineSpec JSON, topologically sorts nodes, resolves templates, runs each node as a uv run subprocess. |
| udit_log.py | 269 | **Audit CLI surface (P7.6).** Commands: event, atch, sync-index. Delegates to workspace-manager's log_event.py. |
| doctor.py | 564 | **Health check command (P7.5).** Validates kits/versions, API keys, skills, workspace layout, CLI/bin seam. |
| mcp_setup.py | 318 | **MCP server wiring (P7.4).** Merges 
exus-scholar entry into Claude Desktop / Cursor / VS Code / .mcp.json configs. |
| escreen_workspace.py | 34 | **Convenience alias.** Forwards to gent_screen.main(). |

### 1.2 econ/ Subpackage -- Exploratory Reconnaissance

| File | Lines | Purpose |
|------|------:|---------|
| econ/__init__.py | 25 | Re-exports all public names. |
| econ/engine.py | 314 | **Probe engine (M0.1).** ReconEngine: probes providers, deduplicates, persists content-addressed pools. Supports injectable search_fn for tests. |
| econ/distiller.py | 305 | **Term-frequency distiller (M0.2/M0.4).** Pure-Python: micro-taxonomy, metric/dataset/school counts, school groupings, topic layer, QEI. |
| econ/gates.py | 128 | **Evaluation gates (M0.7).** APR, pool sufficiency (threshold: 12), topic purity (threshold: 0.50). |
| econ/lexicon.py | 141 | **Pluggable domain lexicons (M0.4/P6).** DomainLexicon frozen dataclass. DEFAULT_LEXICON with CV/LLM + cross-domain patterns. |
| econ/cache_key.py | 113 | **Hierarchical cache key builder.** 1/<providers>/y<year>/q/<sha256>. |
| econ/adaptive.py | 338 | **Adaptive probe horizon (M0.4).** plan_followups(), execute_followups(), merge_pools(). |

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
| untimes/__init__.py | 1 | Docstring only. |
| untimes/actions.py | 192 | **Action-to-command mapping.** 14 actions with templates and MCP tool parity. |
| untimes/job_runner.py | 440 | **Asyncio subprocess job runner.** Job, JobRunner, JobConflict. Lifecycle tracking + audit journal. |

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
| un_pipeline_async() | 430-698 | **The 10-stage pipeline** |
| un_pipeline() | 700-702 | Synchronous wrapper |
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
- un_wizard() (line 1280): Full 4-stage interview flow.
- init_command() (line 1771): P7.3 portable workspace bootstrap.

**Responder protocol** (line 373): Abstraction over interactive prompts for testability.

**Grounded recon loop** (lines 1034-1273): Probes, distills, presents directions, enforces anchor provenance.

### 4.3 econ/ -- Exploratory Reconnaissance

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
- **Rich console**: All CLI output uses ich.console.Console.
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

5. **escreen_workspace.py** (34 lines) is a thin alias that imports rom agent_screen import main -- this works but the sys.path.insert on line 29 is fragile.

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
| Subpackages | 4 (econ/, console/, console/api/, console/runtimes/, integrations/) |
| External kit imports | 6 kits |
| Search providers | 6 |
| CLI commands | 10 + 3 (log sub-app) |
| Console API endpoints | ~20 |
| Pipeline stages | 10 |
| Built-in pipeline templates | 5 |
| Actions (job runner) | 14 |
