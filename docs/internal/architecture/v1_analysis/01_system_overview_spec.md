# 01 System Overview Spec
<!-- Source: 00_SYNTHESIS.md -->
# Nexus Scholar Harness - Deep Analysis Synthesis

**Date:** 2026-09-14  
**Analyst:** opencode (mimo-v2.5-free)  
**Scope:** Complete project analysis across 6 dimensions

---

## Executive Summary

The **Nexus Scholar Harness** is a well-architected, agent-native orchestration system for systematic literature reviews. It demonstrates strong design principles with a thin orchestrator pattern driving 8 specialized research kits. The project is in **Phase 7 (Distribution/Portability)** and has achieved significant maturity with 391 passing tests and comprehensive documentation.

### Key Strengths
1. **Excellent architecture** - Thin orchestrator pattern with clean separation of concerns
2. **Strong testing** - 391 tests with hermetic, contract-driven approach
3. **Comprehensive documentation** - 50+ docs with honest self-assessment
4. **Robust automation** - 9 scripts covering deployment, code generation, and validation
5. **Agent-agnostic design** - Works with opencode, Claude, Copilot, and other AI agents

### Critical Issues
1. **Duplicated code** - Windows UTF-8 handling duplicated across 7+ files
2. **Fragile path assumptions** - Hardcoded `parents[4]` in audit.py
3. **Missing shared fixtures** - No conftest.py at tests root
4. **Documentation gaps** - No CONTRIBUTING.md, CHANGELOG.md, or testing guide
5. **Script testing** - No unit tests for automation scripts

---

## 1. Architecture Analysis

### 1.1 System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    CLI LAYER (cli.py)                        │
│  scholar-harness status|init|setup-mcp|doctor|log|inception │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 ORCHESTRATION LAYER                          │
│  orchestrator.py (731 lines) - 10-stage pipeline            │
│  inception.py (1846 lines) - Socratic wizard                │
│  agent_screen.py (850 lines) - PRISMA screening             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    KIT LAYER (tools/)                        │
│  scholar-protocol-kit (contract spine)                      │
│  scholar-search-kit (federated discovery)                   │
│  scholar-pdf-kit (PDF acquisition)                          │
│  scholar-bib-kit (BibTeX management)                        │
│  scholar-rag-kit (RAG synthesis)                            │
│  scholar-graph-kit (citation networks)                      │
│  scholar-agent-kit (MCP server)                             │
│  scholar-verify-kit (trust verification)                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow
1. **Protocol Phase**: IntentPacket → ResearchProtocol (protocol.json)
2. **Discovery Phase**: Federated search → Deduplication → Verification
3. **Screening Phase**: PRISMA 2020 title/abstract screening (agent-in-the-loop)
4. **Extraction Phase**: PDF download → Markdown extraction
5. **Synthesis Phase**: RAG indexing → Graph construction → Grounded synthesis
6. **Verification Phase**: Retraction check, COI audit, risk-of-bias scoring

### 1.3 Design Patterns
- **Workspace-as-file-contract**: Canonical layout with audit/journal.jsonl
- **Atomic file writes**: temp-file + os.replace dance
- **Agent-in-the-loop**: File-based handoff for screening decisions
- **Fork + PR workflow**: Enforced by pre-push hook

---

## 2. Code Quality Assessment

### 2.1 Strengths
- **Consistent error handling**: Graceful degradation throughout
- **Platform-specific handling**: Windows UTF-8 reconfiguration
- **Deferred imports**: Heavy dependencies loaded lazily
- **Contract-driven validation**: Pydantic v2 models as source of truth

### 2.2 Issues Identified

#### High Priority
1. **Duplicated Windows UTF-8 code** (7+ files)
   - Files: All kit CLI files + install_plugins.py
   - Impact: Maintenance burden, inconsistency risk
   - Solution: Extract to shared utility module

2. **Fragile path assumption** (audit.py:33)
   - Code: `Path(__file__).parents[4]`
   - Impact: Breaks if directory structure changes
   - Solution: Use environment variable or config

3. **Missing shared test fixtures**
   - Issue: No conftest.py at tests root
   - Impact: Fixture duplication across 10+ files
   - Solution: Create tests/conftest.py with shared fixtures

#### Medium Priority
4. **Large file sizes**
   - inception.py: 1,846 lines (wizard + recon + scaffolding)
   - orchestrator.py: 731 lines (pipeline orchestration)
   - agent_screen.py: 850 lines (screening logic)
   - Solution: Consider splitting into smaller modules

5. **Duplicated utility functions**
   - `_read_env_file()` exists in both doctor.py and mcp_setup.py
   - Solution: Extract to shared utility module

6. **Inconsistent versioning**
   - protocol-kit: 1.0.0, others: 0.1.0
   - Solution: Align versioning strategy

#### Low Priority
7. **Missing README for scholar-agent-kit**
8. **Sparse models in scholar-graph-kit** (14 lines)
9. **Minimal documentation for scholar-bib-kit** (3-line README)

---

## 3. Testing Analysis

### 3.1 Test Suite Overview
- **Framework**: pytest >=8.0.0
- **Scale**: 35 test files, ~8,900 lines, 391 tests passing
- **Approach**: Hermetic, contract-driven, no network dependencies

### 3.2 Test Coverage Matrix
| Category | Coverage | Quality | Notes |
|----------|----------|---------|-------|
| Recon subsystem | Excellent | High | 7 test files + 2 integration |
| Console M5.x | Excellent | High | 4 test files, full lifecycle |
| Distribution P7.x | Excellent | High | 5 test files, CLI surface |
| Conformance guards | Excellent | High | 4 test files, drift detection |
| Pipeline executor | Good | High | 2 test files, DAG scheduling |
| Integration tests | Good | Medium | ~120+ tests with monkeypatch |
| E2E tests | Limited | Medium | ~8 tests, single-path only |
| Performance tests | None | N/A | No load/stress tests |
| Error recovery | None | N/A | No failure scenario tests |

### 3.3 Test Quality Indicators
- ✅ **Hermetic**: No network, no real kit CLI invocations
- ✅ **Isolated**: tmp_path workspaces for filesystem tests
- ✅ **Deterministic**: ScriptedResponder classes for wizard tests
- ✅ **Contract-driven**: Schema and invariant assertions

### 3.4 Recommendations
1. **Add shared conftest.py** - Extract common fixtures (highest impact)
2. **Adopt pytest-asyncio** - Cleaner async test code
3. **Add performance baselines** - Critical path benchmarks
4. **Expand E2E edge cases** - Empty inputs, concurrent access, large datasets
5. **Add error recovery tests** - Kit crashes, disk full, corrupt inputs

---

## 4. Documentation Assessment

### 4.1 Documentation Inventory
- **Total files**: 50+ Markdown files
- **Total lines**: 6,300+ lines
- **Coverage**: User guides, architecture, API references, internal docs

### 4.2 Documentation Quality
| Category | Quality | Notes |
|----------|---------|-------|
| Technical depth | Excellent | kits_surface_matrix.md (387 lines) |
| Self-assessment | Excellent | Honest internal audits |
| Design sets | Complete | Phase 5 & 7 thorough |
| Spec-first | Good | Protocol schema implementation-ready |
| User guides | Good | Comprehensive installation/usage |
| API documentation | Good | CLI/MCP references |

### 4.3 Documentation Gaps
1. **Missing standard open-source docs**
   - No CONTRIBUTING.md
   - No CHANGELOG.md
   - No glossary
   - No testing guide

2. **Docs lag implementation**
   - Phase 5 docs say "Planning" but code exists
   - Need to update status indicators

3. **Missing cross-references**
   - No linking between specs/ and docs/architecture/
   - Kit READMEs not indexed

4. **No API reference generation**
   - No automated doc generation from code
   - Consider mkdocs or sphinx

---

## 5. Automation & Scripts

### 5.1 Script Inventory
| Script | Purpose | Quality |
|--------|---------|---------|
| install_plugins.py | Plugin installation | Good, 357 lines |
| generate_nexus_scholar_pins.py | Code generation | Good, 116 lines |
| validate_manifest.py | Validation | Basic, 35 lines |
| pre_commit_check.py | Pre-commit checks | Good, 112 lines |
| push_tools.py | Toolkit sync | Good, 82 lines |
| generate_latex.py | LaTeX generation | Good, 137 lines |
| sync_skills_bundle.py | Skills sync | Good, 84 lines |
| reconcile_dual_screening.py | Data processing | Good, 416 lines |
| hooks/pre-push | Git hook | Good, 38 lines |

### 5.2 Script Quality Issues
1. **No unit tests** - All scripts lack test coverage
2. **Hardcoded paths** - Reduced flexibility
3. **Missing error handling** - Some gaps in propagation
4. **No docstrings** - Missing usage examples

### 5.3 Recommendations
1. **Add script tests** - Unit tests for critical scripts
2. **Parameterize paths** - Use config or environment variables
3. **Improve error handling** - Consistent error propagation
4. **Add docstrings** - Usage examples and documentation

---

## 6. Strategic Recommendations

### 6.1 Immediate Actions (1-2 weeks)
1. **Extract shared utilities**
   - Create `src/scholar_harness/utils/` module
   - Move Windows UTF-8 handling, _read_env_file(), etc.
   - Update all imports

2. **Create shared test fixtures**
   - Add `tests/conftest.py`
   - Extract common fixtures from 10+ test files
   - Reduce duplication

3. **Fix fragile path assumption**
   - Replace `parents[4]` with config-based approach
   - Add tests for path resolution

### 6.2 Short-term Improvements (1 month)
1. **Split large files**
   - Break inception.py into wizard, recon, scaffolding modules
   - Consider orchestrator.py decomposition

2. **Add missing documentation**
   - CONTRIBUTING.md
   - CHANGELOG.md
   - Testing guide

3. **Improve script quality**
   - Add unit tests for scripts
   - Add docstrings and usage examples
   - Parameterize hardcoded paths

### 6.3 Long-term Enhancements (3 months)
1. **Performance testing**
   - Add load tests for critical paths
   - Benchmark pipeline execution
   - Monitor memory usage

2. **Error recovery testing**
   - Kit crash scenarios
   - Disk full conditions
   - Corrupt input handling

3. **Documentation automation**
   - Set up mkdocs or sphinx
   - Auto-generate API docs from code
   - Implement docs-as-code workflow

---

## 7. Conclusion

The Nexus Scholar Harness is a **well-engineered project** with strong fundamentals. The thin orchestrator pattern, comprehensive testing, and honest self-assessment demonstrate mature software engineering practices. The main areas for improvement are code deduplication, shared utilities, and documentation gaps.

### Overall Assessment
- **Architecture**: ★★★★★ (Excellent)
- **Code Quality**: ★★★★☆ (Good, some duplication)
- **Testing**: ★★★★★ (Excellent, comprehensive)
- **Documentation**: ★★★★☆ (Good, some gaps)
- **Automation**: ★★★★☆ (Good, needs tests)
- **Maintainability**: ★★★★☆ (Good, with suggested improvements)

### Priority Matrix
| Impact | Effort | Action |
|--------|--------|--------|
| High | Low | Extract shared utilities |
| High | Low | Create shared test fixtures |
| High | Medium | Fix fragile path assumptions |
| Medium | Medium | Split large files |
| Medium | Low | Add missing documentation |
| Low | Low | Add script tests |

---

*Analysis generated by opencode (mimo-v2.5-free) on 2026-09-14*
*Detailed findings in: 01_project_overview.md through 06_scripts_analysis.md*

---

<!-- Source: 01_project_overview.md -->
# Nexus Scholar Harness - Project Overview

> **Analysis Date:** 2026-09-14
> **Repository:** C:\Users\mouadh\Documents\nexus-scholar-harness
> **Version:** 1.0.0 (nexus-scholar-harness) / 1.0.0 (nexus-scholar metapackage)

---

## 1. Project Purpose and Description

**Nexus Scholar Harness** is an **agent-native, audited orchestration system for systematic literature reviews**. It is a thin orchestrator that drives eight external research kits through a unified CLI, workspace-as-file-contract state management, and an append-only audit ledger.

### Key Design Principles

1. **Deterministic and Idempotent** - Re-runs produce identical artifacts (protocol.json carries a SHA-256 fingerprint)
2. **Audited** - Every significant step appends an immutable event to udit/journal.jsonl
3. **Agent-Agnostic** - The same CLI, MCP tools, and workspace files drive opencode, Claude, Copilot, and any other coding agent
4. **Thin Orchestrator** - Does NOT re-implement research logic; instead orchestrates purpose-built kits

### Research Pipeline Flow

`
Socratic Inception --> Federated Discovery --> Dedup & Verify --> PRISMA Screening --> OA Harvest --> Extraction --> RAG Synthesis --> Trust Verification
(methodology-copilot)     (scholar-search)       (scholar-search)    (agent-in-the-loop)    (scholar-pdf)    (scholar-pdf)    (scholar-rag)      (scholar-verify)
`

### The Eight Research Kits

| Kit | Purpose | CLI |
|-----|---------|-----|
| scholar-protocol-kit | Research protocol compiler, JSON-schema contract | scholar-protocol |
| scholar-search-kit | Federated academic search, dedup, verify, export | scholar-search |
| scholar-pdf-kit | OA discovery, downloading, validation, extraction | scholar-pdf |
| scholar-bib-kit | BibTeX parse, lint, merge, dedup, resolve | scholar-bib |
| scholar-rag-kit | ChromaDB indexing, RAG synthesis | scholar-rag |
| scholar-graph-kit | Citation/co-citation networks, PageRank | scholar-graph |
| scholar-agent-kit | MCP server exposing all kits to AI agents | scholar-agent |
| scholar-verify-kit | Trust verification (retraction, COI, risk-of-bias) | scholar-verify |

---

## 2. Key Dependencies and Versions

### Harness Dependencies (pyproject.toml, line 17-22)

| Dependency | Version Constraint | Purpose |
|------------|-------------------|---------|
| 	yper | >=0.9.0 | CLI framework |
| 
ich | >=13.0.0 | Terminal formatting/output |
| astapi | >=0.115.0 | Web API framework (console) |
| uvicorn | >=0.30.0 | ASGI server (console) |

### Dev Dependencies (pyproject.toml, line 25-28)

| Dependency | Version Constraint | Purpose |
|------------|-------------------|---------|
| pytest | >=8.0.0 | Testing framework |
| 
uff | >=0.4.0 | Linter |

### Metapackage Dependencies (packaging/nexus-scholar/pyproject.toml, line 48-64)

The 
exus-scholar metapackage bundles the full stack:

| Dependency | Version | Purpose |
|------------|---------|---------|
| iohttp | >=3.9.0 | Async HTTP client |
| ibtexparser | >=2.0.0 | BibTeX parsing |
| astapi | >=0.115.0 | Web framework |
| hishel | ==0.0.32 | HTTP caching |
| httpx | >=0.28.1 | HTTP client |
| mcp | >=1.0.0 | Model Context Protocol |
| 
etworkx | >=3.0 | Graph algorithms |
| pydantic | >=2.0.0 | Data validation |
| pydantic-settings | >=2.0.0 | Settings management |
| pyvis | >=0.3.0 | Network visualization |
| 
equests | >=2.31.0 | HTTP client |
| 
ich | >=13.0.0 | Terminal output |
| 	enacity | >=8.0.0 | Retry logic |
| 	yper | >=0.9.0 | CLI framework |
| uvicorn | >=0.30.0 | ASGI server |

### Python Version

- **Required:** Python >=3.11
- **Tested against:** Python 3.11 and 3.12 (CI matrix)

### Build System

- **Build backend:** hatchling
- **Lock file:** uv.lock (413 lines, uv version 1, revision 3)

---

## 3. Project Structure Overview

### Top-Level Directory Layout

`
nexus-scholar-harness/
+-- .agents/                    # Agent configuration and skills
�   +-- plugins/                # Plugin registry (kit versions)
�   �   +-- nexus-scholar/      # Plugin manifest + MCP config
�   +-- skills/                 # 12 agent skills (per-kit)
+-- .cache/                     # Runtime cache (gitignored)
+-- .github/                    # CI/CD workflows
�   +-- workflows/              # 3 workflow files
+-- .opencode/                  # OpenCode configuration
+-- docs/                       # Documentation
+-- latex/                      # LaTeX templates
+-- lib/                        # Vendored JS (gitignored, vis/tom-select)
+-- packaging/                  # Distribution metapackage
�   +-- nexus-scholar/          # Source-bundling wheel
+-- scripts/                    # Build/install/lint scripts
+-- specs/                      # Living specifications
+-- src/                        # Harness source code
�   +-- scholar_harness/        # Core orchestrator package
+-- tests/                      # Test suite (26 test files)
+-- tools/                      # 8 tracked kit packages
+-- workspaces/                 # Research workspaces (empty, tracked)
+-- pyproject.toml              # Project configuration
+-- uv.lock                     # Dependency lock file
+-- opencode.json               # OpenCode MCP configuration
+-- AGENTS.md                   # Agent operational guidance
`

### Source Code (src/scholar_harness/)

**File: __init__.py** (line 1-7)
- Package version: 1.0.0
- Exports: ResearchOrchestrator

**File: cli.py** (494 lines)
- Main CLI entry point: scholar-harness
- Subcommands: status, init, setup-mcp, doctor, log, inception, sync, 
un, export, serve
- Uses Typer + Rich for CLI framework
- Platform-aware encoding handling (Windows UTF-8 support)

**File: orchestrator.py** (731 lines)
- Core ResearchOrchestrator class
- 10-stage research pipeline implementation
- Importable kit modules: scholar_search, scholar_pdf, scholar_rag, scholar_graph, scholar_protocol
- Atomic file writes, audit journal logging, state synchronization
- ChromaDB integration for vector indexing

**Other Source Files:**
- gent_screen.py - PRISMA screening agent-in-the-loop
- udit_log.py - Audit event management
- doctor.py - Health checks
- inception.py - Socratic methodology wizard
- mcp_setup.py - MCP server configuration
- pipeline_executor.py - DAG pipeline execution
- console/ - FastAPI web console (API, runtimes, static)
- integrations/ - LaTeX/Typst, Obsidian, Zotero exporters

### Kits (	ools/)

All 8 kits are tracked in git and installed editable:

`
tools/
+-- scholar-agent-kit/          # MCP server
+-- scholar-bib-kit/            # BibTeX management
+-- scholar-graph-kit/          # Citation graphs
+-- scholar-pdf-kit/            # PDF harvesting/extraction
+-- scholar-protocol-kit/       # Protocol compiler
+-- scholar-rag-kit/            # RAG synthesis
+-- scholar-search-kit/         # Federated search
+-- scholar-verify-kit/         # Trust verification
`

### Tests (	ests/)

26 test files covering:
- CLI commands (	est_harness_cli.py, 	est_cli_init.py)
- Console endpoints (	est_console_m52.py, 	est_console_m53.py, 	est_console_m54.py, 	est_console_serve.py)
- Core functionality (	est_orchestrator_fidelity.py, 	est_pipeline_executor.py)
- E2E flows (	est_phase1_e2e.py, 	est_phase2_e2e.py, 	est_phase3_e2e.py)
- Integrations (	est_integrations.py, 	est_mcp_setup.py, 	est_mcp_tools_graph.py)
- Conformance (	ests/conformance/)

---

## 4. CI/CD Setup

### Workflow Files

**Location:** .github/workflows/ (3 files)

#### 1. ci.yml (192 lines) - Main CI Pipeline

**Triggers:**
- Push to main or develop branches
- Pull requests to main or develop

**Jobs:**

**Job 1: lint-and-test** (lines 10-85)
- **Matrix:** ubuntu-latest, windows-latest, macos-latest x Python 3.11, 3.12
- **Steps:**
  1. Checkout code
  2. Install uv (v0.12.5)
  3. Set up Python
  4. uv sync --extra dev
  5. Lint with ruff: uv run ruff check scripts/
  6. Test plugin installer syntax: uv run python scripts/install_plugins.py --help
  7. Verify plugin manifest: uv run python scripts/validate_manifest.py
  8. Enforce nexus-scholar pins freshness: uv run python scripts/generate_nexus_scholar_pins.py --check
  9. Build metapackage wheel: uv build --wheel packaging/nexus-scholar
  10. Smoke test metapackage (P7.7 lazy-imports gate)
  11. Install plugins (git-only, best-effort)
  12. Workspace-manager smoke test

**Job 2: schema-validation** (lines 87-110)
- Validates plugin manifest JSON schema
- Checks required fields: 
ame, 
epo, default_rev, console_script

**Job 3: wheel-e2e** (lines 112-192)
- **Matrix:** ubuntu-latest, windows-latest
- End-to-end test of the metapackage wheel in a fresh temp folder
- Tests: init, setup-mcp, doctor, log event, sync-index
- Verifies portability (workspace outside git checkout)

#### 2. publish.yml (41 lines) - PyPI Publishing

**Triggers:**
- Push of * tags
- Manual workflow_dispatch

**Permissions:** id-token: write, contents: write

**Steps:**
1. Checkout code
2. Install uv
3. Build metapackage wheel
4. Publish to PyPI via Trusted Publishing (OIDC)

**Environment:** pypi deployment environment required

#### 3. 
elease.yml (82 lines) - GitHub Release

**Triggers:**
- Push of * tags
- Manual workflow_dispatch

**Steps:**
1. Checkout code
2. Install uv
3. Build metapackage wheel
4. Create GitHub Release with wheel attachment
5. Idempotent guard (skip if release already exists)

### CI Quality Gates

1. **Lint:** 
uff check scripts/ (CI scope)
2. **Manifest validation:** Plugin JSON schema compliance
3. **Pin freshness:** plugins.json SHA pins must be current
4. **Wheel smoke:** Both entrypoints answer --help (P7.7 lazy-imports gate)
5. **E2E uvx flow:** Full init/setup-mcp/doctor/log/sync-index from wheel (P7.8 gate)

---

## 5. Configuration Files

### opencode.json (10 lines)

`json
{
  "": "https://opencode.ai/config.json",
  "mcp": {
    "nexus-scholar": {
      "type": "local",
      "command": ["uv", "run", "--directory", "tools/scholar-agent-kit", "scholar-agent"],
      "enabled": true
    }
  }
}
`

**Purpose:** Configures OpenCode to use the scholar-agent-kit MCP server.

### AGENTS.md (extensive)

**Key instructions for agents:**
- Run everything through project venv with uv run ...
- Never rely on system Python
- All tests: uv run pytest (391 passed, 5 skipped)
- Lint: uv run ruff check scripts/
- Never push feature branches to origin (fork + PR workflow)
- Workspaces are file contracts with canonical layout
- Audit ledger is mandatory for every significant step

### .agents/plugins/nexus-scholar/plugins.json (71 lines)

**Plugin registry** defining all 8 kits with:
- 
ame - Kit identifier
- description - Kit purpose
- 
epo - Git repository URL
- default_rev - Pinned commit SHA (not floating branch)
- console_script - CLI entry point
- extras - Optional dependency groups

**Kit versions (commit SHAs):**
- scholar-protocol-kit: 46874778cd0dde6d89414532b52d258843789132
- scholar-search-kit:  0010694b9f957a84047da340dff40c51e583ea1
- scholar-pdf-kit: 9fa9e00361cd6d3bd7aec3c5a079db80f0287f58
- scholar-bib-kit:  bf3cdd2d0ace6dc626f033871747a78681c6ddf
- scholar-graph-kit:  be6299bb28a11c745e9e6291c32ef1cec30918e
- scholar-rag-kit: c89b68f0d35173082a03b8c6b228e84381271185
- scholar-agent-kit:  c78a83ce548a0c3c71121f5751e32c0788309df
- scholar-verify-kit: 44a8d63cc0a11694bbcb7a355a53f73c3f93145c

### .agents/plugins/nexus-scholar/mcp_config.json (13 lines)

**MCP server configuration** for Claude Desktop, Cursor, VS Code:
`json
{
  "mcpServers": {
    "nexus-scholar": {
      "command": "uv",
      "args": ["run", "--directory", "tools/scholar-agent-kit", "scholar-agent"]
    }
  }
}
`

### packaging/nexus-scholar/nexus_scholar_pins.json (52 lines)

**Deterministic kit pins** derived from plugins.json via scripts/generate_nexus_scholar_pins.py. Used by the metapackage wheel build. CI enforces freshness with --check.

### pyproject.toml (48 lines)

**Build system:** hatchling
**Package name:** 
exus-scholar-harness
**Entry point:** scholar-harness = "scholar_harness.cli:app"
**Test configuration:**
- 	estpaths = ["tests"]
- pythonpath includes src/ and all 8 kit src/ directories
- ddopts = "-q --basetemp=tests_temp"

### .gitignore (72 lines)

**Key exclusions:**
- workspaces/**/pdfs/ (heavy binary PDFs)
- workspaces/**/rag/chroma_db/ (vector stores)
- .cache/, __pycache__/, .venv/
- scratch/ (development scratch)
- IDE files, OS files, LaTeX build artifacts

---

## 6. Notable Patterns and Conventions

### Architecture Patterns

1. **Thin Orchestrator Pattern**
   - Harness does NOT re-implement research logic
   - Delegates to 8 specialized kits via CLI/API calls
   - Maintains workspace state and audit trail

2. **Workspace-as-File-Contract**
   - Canonical layout: protocol.json, intent.json, SCREENING_CRITERIA.md, INDEX.md, project.json, udit/journal.jsonl
   - Heavy artifacts (PDFs, chroma_db) are gitignored
   - Text/metadata files are tracked

3. **Agent-in-the-Loop Screening**
   - PRISMA screening is not an opaque API
   - Pipeline writes atch_NNN.json, agent reads and writes atch_NNN_decisions.json
   - collect assembles final included.json/excluded.json

4. **Append-Only Audit Ledger**
   - Every significant step logs to udit/journal.jsonl
   - Immutable events with timestamps, action, agent/tool, description, inputs, outputs, metrics

5. **Atomic File Writes**
   - Uses temp-file + os.replace dance for crash safety
   - Prevents truncated manifests or orphaned files

### Development Conventions

1. **Never Push to Origin**
   - Fork + PR workflow enforced by pre-push hook
   - Hook location: scripts/hooks/pre-push
   - Enable: git config core.hooksPath scripts/hooks

2. **Kit Repo Sync (Hard Rule)**
   - Changes to 	ools/<kit>/ must also land in kit's own repo
   - plugins.json default_rev must be bumped to resulting commit SHA
   - 	ools/<kit>/ tree must not drift from that commit

3. **CI Scope**
   - Ruff lint scoped to scripts/ only
   - Tests import from src/ and 	ools/*/src via pythonpath
   - Test count baseline: 391 passed, 5 skipped

4. **Distribution Metapackage**
   - packaging/nexus-scholar/ is the 
exus-scholar metapackage
   - Source-bundling wheel: harness + 8 kits via hatchling orce-include
   - Kit pins come ONLY from plugins.json via deterministic codegen
   - Never hand-edit 
exus_scholar_pins.json

5. **Lazy Imports (P7.7)**
   - Heavy deps (chromadb, torch, sentence-transformers) deferred
   - Wheel entrypoints answer --help on minimal-dep env
   - CI smoke is a hard gate

### Platform Considerations

1. **Windows UTF-8 Support**
   - CLI reconfigures stdout/stderr for UTF-8 encoding
   - sys.stdout.reconfigure(encoding="utf-8") with fallbacks

2. **Cross-Platform CI**
   - Tests run on ubuntu, windows, macos
   - E2E wheel tests on ubuntu + windows
   - Path normalization for Windows (cygpath)

### Version Management

1. **Semver Adherence**
   - Harness version: 1.0.0
   - Metapackage version: 1.0.0
   - Git tags: * pattern

2. **Pin Enforcement**
   - plugins.json contains full commit SHAs (never floating branches)
   - 
exus_scholar_pins.json is auto-generated, never hand-edited
   - CI enforces freshness with --check flag

---

## 7. Current Development Status

### Active Milestone: Phase 7 (Distribution/Portability)

**Recent commits (last 20):**
1. d08b388 - docs: reorganize docs into public hubs, architecture blueprints, and internal archive (#33)
2. 6eb0fbe - docs: document live PyPI distribution and install forms (P7.9) (#32)
3. 5c908e - docs(README): dual-audience landing page with released-app quickstart (#31)
4. 4eb1da1 - pkg: PyPI publish groundwork for nexus-scholar metapackage (P7.9) (#30)
5. 7508e2 - docs: nexus-scholar v1.0.0 user guide (#29)
6. 6e73a0a - gate: allow release tags through the origin pre-push hook (release flow) (#28)
7.  eb3852 - ci: wheel e2e uvx-flow gate + github release workflow (P7.8) (#27)
8. 3f2c1c1 - feat(cli): nexus-scholar log - importable audit-contract CLI (P7.6) (#26)
9. 5e61393 - feat(cli): nexus-scholar doctor - distribution-health checks (P7.5) (#25)
10. 1538dd7 - chore(meta): bump test-count baselines to 355 (measured post-P7.4) (#24)

### P7.x Checklist (from docs/architecture/phase_7_distribution/README.md)

- [x] P7.1 - Rootdir resolution
- [x] P7.2 - Metapackage with plugins.json-derived pins
- [x] P7.3 - 
exus-scholar init <title> scaffold
- [x] P7.4 - 
exus-scholar setup-mcp
- [x] P7.5 - 
exus-scholar doctor
- [x] P7.6 - 
exus-scholar log
- [x] P7.7 - Lazy-import rag/graph (light wheel entrypoints)
- [x] P7.8 - Wheel e2e uvx-flow gate + GitHub release
- [x] P7.9 - PyPI publish groundwork

---

## 8. Key File References

| File | Path | Lines | Purpose |
|------|------|-------|---------|
| README.md | /README.md | 246 | Project documentation |
| pyproject.toml | /pyproject.toml | 48 | Project configuration |
| AGENTS.md | /AGENTS.md | extensive | Agent operational guidance |
| cli.py | /src/scholar_harness/cli.py | 494 | Main CLI entry point |
| orchestrator.py | /src/scholar_harness/orchestrator.py | 731 | Core pipeline orchestrator |
| plugins.json | /.agents/plugins/nexus-scholar/plugins.json | 71 | Plugin registry (kit versions) |
| ci.yml | /.github/workflows/ci.yml | 192 | Main CI pipeline |
| publish.yml | /.github/workflows/publish.yml | 41 | PyPI publishing |
| release.yml | /.github/workflows/release.yml | 82 | GitHub Release |
| opencode.json | /opencode.json | 10 | OpenCode MCP config |
| mcp_config.json | /.agents/plugins/nexus-scholar/mcp_config.json | 13 | MCP server config |
| install_plugins.py | /scripts/install_plugins.py | 357 | Plugin installer |
| packaging pyproject.toml | /packaging/nexus-scholar/pyproject.toml | 96 | Metapackage config |
| nexus_scholar_pins.json | /packaging/nexus-scholar/nexus_scholar_pins.json | 52 | Deterministic kit pins |

---

## 9. Summary

**Nexus Scholar Harness** is a well-architected, agent-native orchestration system for systematic literature reviews. Its key strengths include:

1. **Modular Design** - Thin orchestrator delegating to 8 specialized kits
2. **Auditability** - Append-only journal ledger for every significant step
3. **Portability** - Source-bundling wheel with lazy imports, works via uvx
4. **CI/CD Excellence** - Multi-platform testing, wheel E2E gates, PyPI publishing
5. **Agent Integration** - MCP server exposing all kits to AI agents
6. **Workspace Convention** - File-contract layout with deterministic state management

The project is at **v1.0.0** with Phase 7 (Distribution/Portability) complete. It demonstrates mature software engineering practices with comprehensive testing (391 tests), thorough documentation, and robust CI/CD pipelines.


---

