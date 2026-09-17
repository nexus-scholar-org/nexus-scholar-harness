# 04 Quality Assurance Spec
<!-- Source: 04_tests_analysis.md -->
﻿# Comprehensive Test Suite Analysis

## nexus-scholar-harness `tests/` Directory

**Generated:** 2026-09-14
**Test suite stats (AGENTS.md):** 391 passed, 5 skipped, 0 failures

---

## 1. Testing Framework and Approach

### Framework Stack

| Component | Tool | Version Constraint |
|-----------|------|--------------------|
| Test runner | `pytest` | `>=8.0.0` (pyproject.toml, line 26) |
| CLI testing | `typer.testing.CliRunner` | (via typer `>=0.9.0`) |
| HTTP API testing | `fastapi.testclient.TestClient` | (via fastapi `>=0.115.0`) |
| Async HTTP testing | `httpx.AsyncClient` + `httpx.ASGITransport` | (via httpx) |
| Linter | `ruff` | `>=0.4.0` (scoped to `scripts/` only) |

### Pytest Configuration

**File:** `C:\Users\mouadh\Documents\nexus-scholar-harness\pyproject.toml` (lines 33-45)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = [
    "src",
    "tools/scholar-protocol-kit/src",
    "tools/scholar-search-kit/src",
    "tools/scholar-pdf-kit/src",
    "tools/scholar-bib-kit/src",
    "tools/scholar-rag-kit/src",
    "tools/scholar-graph-kit/src",
    "tools/scholar-agent-kit/src",
]
addopts = "-q --basetemp=tests_temp"
```

Key points:
- **`pythonpath`** injects the harness `src/` and all 8 kit `src/` directories into `sys.path`, enabling direct imports of kit modules in tests without installing them.
- **`--basetemp=tests_temp`** isolates pytest temp directories into a single tree.
- **`-q`** (quiet) for concise output.
- No conftest.py in the tests/ root (only `tools/scholar-protocol-kit/tests/conftest.py` exists, outside this scope).

### Core Testing Philosophy

The test suite follows these principles, stated repeatedly in docstrings:

1. **Hermetic tests** -- No network, no real kit CLI invocations, no heavy model loads. Every external dependency is injected via `monkeypatch`, fake classes, or `search_fn` callables.
2. **`tmp_path` workspaces** -- Every test that touches the filesystem uses pytest's `tmp_path` fixture for complete isolation.
3. **Scripted responders** -- Wizard/CLI tests use `ScriptedResponder` classes that feed predetermined answers, enabling deterministic end-to-end runs.
4. **Contract-driven assertions** -- Tests verify data schemas, append-only journal invariants, atomic writes, and cross-module contracts rather than implementation details.

---

## 2. Complete Test File Listing

### 2.1 Root-Level Test Files (22 files)

| File | Lines | Purpose | Type |
|------|-------|---------|------|
| `test_audit_log.py` | 394 | P7.6: `nexus-scholar log` CLI -- event/batch/sync-index audit-contract tests | Unit + Integration |
| `test_cli_init.py` | 322 | P7.3: `nexus-scholar init` portable workspace bootstrap (scaffold, refusal rules, slugification, skills install, wizard handoff) | Unit + Integration |
| `test_console_m52.py` | 184 | M5.2: Read observability surface -- synthesis/phase4 indexes, file serving, harvest corpus, graph asset, change-tick SSE | Unit |
| `test_console_m53.py` | 482 | M5.3: Screening decisions POST, audit POST, pipeline CRUD/dry-run, job endpoint aliases | Integration |
| `test_console_m54.py` | 358 | M5.4: JobRunner DAG integration -- pipeline action, live execution (success/halt/cancel/single-flight), builtin archetype templates | Integration |
| `test_console_serve.py` | 347 | M5.1: Harness Console server -- read endpoints, job lifecycle, SSE broadcast/fanout | Integration |
| `test_doctor.py` | 318 | P7.5: `nexus-scholar doctor` -- kits/versions, API keys, skills, workspace layout, JSON output, secret masking | Unit + Integration |
| `test_harness_cli.py` | 200 | Unit tests for `scholar-harness` CLI (status, export, sync) and orchestrator | Unit |
| `test_inception.py` | 340 | Phase-0 Inception wizard -- paradigm detection, intent packet, protocol compilation, full scripted e2e, console responder | Unit + E2E |
| `test_inception_grounded.py` | 801 | M0.3: `--grounded` wizard flag -- recon engine injection, direction proposals, anchor verification, junk filtering, headless modes | Unit + E2E |
| `test_integrations.py` | 133 | Academic ecosystem integrations -- LaTeX, Typst, Obsidian, Zotero exporters | Unit |
| `test_mcp_recon.py` | 666 | M0.5: Recon MCP surface -- `recon_probe`/`recon_distill`/`recon_delta` tools, session persistence, semantic mode, purity gate, lexicon override, corpus saturation | Integration |
| `test_mcp_setup.py` | 421 | P7.4: `nexus-scholar setup-mcp` -- multi-harness wiring, merge/idempotency, env passthrough, secret redaction, dry-run | Unit + Integration |
| `test_mcp_tools_graph.py` | 619 | nexus_* MCP tool regressions -- graph build, PDF extract, bib clean, screen, verify claims, protocol validate, verify phase4 | Unit + Integration |
| `test_nexus_scholar_metapackage.py` | 89 | Metapackage pyproject.toml validation -- entrypoints, force-include mapping, skills bundle completeness | Unit |
| `test_orchestrator_fidelity.py` | 317 | Orchestrator Stages 5-9 fidelity -- PENDING_AGENT_REVIEW gating, metadata extraction, retriever wiring, graph client | Unit + Integration |
| `test_phase1_e2e.py` | 213 | Phase 1 full funnel e2e -- IntentPacket -> protocol -> search -> dedup -> screening -> extraction -> audit trail | E2E |
| `test_phase2_e2e.py` | 283 | Phase 2 full pipeline e2e -- chunking, ChromaDB indexing, citation graph, graph-boosted retrieval, matrix extraction, grounded synthesis | E2E |
| `test_phase3_e2e.py` | 226 | Phase 3 multi-modal e2e -- orchestrator across all stages, MCP tool invocations, academic exports | E2E |
| `test_pipeline_executor.py` | 317 | M5.4: PipelineSpec DAG executor -- topological scheduling, template resolution, on_fail modes, requires_decision, idempotency, CLI wiring | Unit + Integration |
| `test_pipeline_script.py` | 314 | M5.4: Shell-script export (`export pipeline-sh`) -- rendering, shell quoting, bash execution parity | Unit + Integration |
| `test_rigor_upgrades.py` | 96 | Verbatim claim verifier, multi-screener Fleiss' kappa, reconciliation | Unit |
| `test_scholar_agent_cli.py` | 97 | P7.1: scholar-agent CLI entrypoint -- --help, --workspace, --transport passthrough, phase4 default workspace | Unit |

### 2.2 `tests/recon/` Subpackage (7 files)

| File | Lines | Purpose | Type |
|------|-------|---------|------|
| `__init__.py` | 0 | Package marker (empty) | -- |
| `test_adaptive.py` | 565 | M0.4: Adaptive probe horizon -- thin-school detection, followup planning/execution, merge semantics (DOI-union, 25-cap), corpus saturation | Unit + Integration |
| `test_cache_key.py` | 106 | T0.2/T0.3: Hierarchical cache-key builder -- normalization, roundtrip, semantic mode segment | Unit |
| `test_distiller.py` | 512 | M0.2: Term-frequency distiller -- anchored term freq/DOIs, metrics/datasets extraction, schools heuristic, topics layer (M0.6), QEI gate (M0.7) | Unit |
| `test_engine.py` | 295 | M0.1: ReconEngine.probe -- pool cap, cache hits, corrupt cache, workspaces guard, semantic threading, corpus saturation, canonical root | Unit |
| `test_gates.py` | 219 | M0.7 T7.1: Recon evaluation gates -- APR (Anchor Provenance Rate), pool sufficiency, topic purity/coherence | Unit |
| `test_inception_skill_helper.py` | 139 | Inception-agent skill parity -- subprocess tests of `grounded_directions.py` against synthetic fixtures | Integration |
| `test_lexicon.py` | 472 | M0.4: Pluggable DomainLexicon -- default lexicon coverage, oncology overlay, merge semantics, cross-domain signal | Unit |

### 2.3 `tests/conformance/` Subpackage (4 files)

| File | Lines | Purpose | Type |
|------|-------|---------|------|
| `__init__.py` | 8 | Package docstring: enforces documented surface matches code | -- |
| `test_actions_cli_parity.py` | 127 | Actions-table <-> kit-CLI parity -- every rendered action command must parse against the referenced CLI's declared options | Conformance |
| `test_count_freshness.py` | 89 | Surface count freshness -- 8 kits, 14 actions, 19 MCP tools, 11 skills mirror, pinned commit SHAs | Conformance |
| `test_mcp_tool_parity.py` | 34 | MCP tool surface parity -- actions table references must match registered MCP tools, `--help` must list all | Conformance |
| `test_nexus_scholar_pins.py` | 198 | Metapackage pin freshness -- plugins.json <-> nexus_scholar_pins.json sync, codegen determinism, --check exit code, force-include cross-validation | Conformance |

---

## 3. Test Coverage Analysis

### 3.1 Coverage by Feature Area

| Feature Area | Files | Test Count (est.) | Coverage Quality |
|--------------|-------|-------------------|------------------|
| **Inception Wizard (Phase-0)** | `test_inception.py`, `test_inception_grounded.py`, `test_cli_init.py` | ~40+ | **Excellent** -- scripted e2e, grounded mode, headless, refusal rules, determinism |
| **Recon Engine (M0.x)** | `recon/test_*.py` (7 files) + `test_mcp_recon.py` | ~60+ | **Excellent** -- engine, distiller, adaptive, cache keys, gates, lexicon, MCP surface |
| **MCP Tools** | `test_mcp_tools_graph.py`, `test_mcp_recon.py` | ~30+ | **Excellent** -- every nexus_* tool regression-tested with fake engines |
| **Console Server (M5.x)** | `test_console_m52.py`, `test_console_m53.py`, `test_console_m54.py`, `test_console_serve.py` | ~40+ | **Excellent** -- HTTP endpoints, SSE, job lifecycle, pipeline DAG, screening |
| **Pipeline Executor** | `test_pipeline_executor.py`, `test_pipeline_script.py` | ~20+ | **Excellent** -- DAG scheduling, template resolution, on_fail modes, bash parity |
| **Distribution (P7.x)** | `test_cli_init.py`, `test_doctor.py`, `test_mcp_setup.py`, `test_audit_log.py`, `test_scholar_agent_cli.py`, `test_nexus_scholar_metapackage.py` | ~50+ | **Excellent** -- init, doctor, setup-mcp, log, metapackage validation |
| **Conformance Guards** | `conformance/test_*.py` (4 files) | ~15+ | **Excellent** -- kit count, action count, MCP tool count, skills mirror, pin freshness |
| **Phase 1-3 E2E** | `test_phase1_e2e.py`, `test_phase2_e2e.py`, `test_phase3_e2e.py` | 3 large tests | **Good** -- full pipeline chains, but limited edge cases |
| **Orchestrator** | `test_orchestrator_fidelity.py`, `test_harness_cli.py` | ~15 | **Good** -- fidelity gating, retriever wiring, provider resolution |
| **Integrations** | `test_integrations.py` | 4 | **Good** -- LaTeX, Typst, Obsidian, Zotero (basic coverage) |
| **Rigor** | `test_rigor_upgrades.py` | 5 | **Good** -- verbatim verifier, Fleiss' kappa, reconciliation |

### 3.2 Coverage by Test Type

| Test Type | Count (est.) | Description |
|-----------|-------------|-------------|
| **Unit tests** | ~180+ | Pure function/class tests with no I/O beyond tmp_path |
| **Integration tests** | ~120+ | Cross-module tests using TestClient, monkeypatched kits, async runners |
| **End-to-end tests** | ~8 | Full pipeline chains (Phase 1, 2, 3, inception e2e) |
| **Conformance tests** | ~15 | Documented surface count/parity drift guards |
| **Regression tests** | ~60+ | Individual bug fixes with dedicated test cases (e.g., vision-report findings) |

### 3.3 Estimated Line Counts

| Directory | Files | Total Lines |
|-----------|-------|-------------|
| `tests/` (root) | 22 | ~6,135 |
| `tests/recon/` | 8 (incl. `__init__`) | ~2,308 |
| `tests/conformance/` | 5 (incl. `__init__`) | ~456 |
| **Total** | **35** | **~8,899** |

---

## 4. Test Patterns and Conventions

### 4.1 Naming Conventions

- **`test_<feature>_<aspect>`** -- e.g., `test_log_event_canonical_schema`, `test_probe_caps_pool_at_25`
- **Feature area prefixes** for milestone-driven tests: `test_console_m52_*`, `test_console_m53_*`, `test_console_m54_*`
- **Protocol prefixes** for phase-0 tests: `test_inception_*`, `test_inception_grounded_*`
- **Parametrized tests** used for cross-cutting checks: `@pytest.mark.parametrize("marker", [...])` in `test_cli_init.py` (line 120), `@pytest.mark.parametrize("action", ACTIONS, ...)` in `test_actions_cli_parity.py` (line 82)

### 4.2 Bootstrap Helpers

Every test file with workspace setup defines a local `_bootstrap(tmp)` or `_scaffold(tmp_path)` helper that creates the minimum canonical workspace tree:

```python
def _bootstrap(tmp):
    ws = tmp / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "synthesis").mkdir(parents=True)
    (ws / "phase4").mkdir(parents=True)
    (ws / "audit").mkdir(parents=True)
    # ... seed minimal JSON files
    return ws
```

**Files with bootstrap helpers:** `test_console_m52.py` (line 19), `test_console_m53.py` (line 36), `test_console_m54.py` (line 77), `test_console_serve.py` (line 22), `test_pipeline_executor.py` (line 95), `test_pipeline_script.py` (line 115), `test_audit_log.py` (line 44), `test_doctor.py` (line 174)

### 4.3 Fake/Stub Patterns

The codebase uses several injection strategies:

1. **Callable injection (`search_fn`)** -- The `ReconEngine` accepts a `search_fn(query, providers) -> list[Document]` callable, enabling fully hermetic recon tests without touching any academic API. Used in `test_mcp_recon.py`, `test_inception_grounded.py`, `recon/test_engine.py`, `recon/test_adaptive.py`.

2. **Class monkeypatching** -- Kit classes are replaced with fakes: `_FakeEngine`, `_FakeDedup`, `_FakeVerifier`, `_FakeIndexer`, `_RecorderRetriever`, `_FakeMatrix`, `_FakeSynth`, `_FakeGraph`, `_FakeVis` in `test_orchestrator_fidelity.py` (lines 66-163).

3. **Stub runners** -- `_StubRunner`/`_FakeJob` classes for the console server job lifecycle tests in `test_console_serve.py` (lines 146-207) and `test_console_m53.py` (lines 397-437).

4. **Scripted responders** -- `ScriptedResponder` (in `test_inception.py`, line 186) and `GroundedScriptedResponder` (in `test_inception_grounded.py`, line 128) feed predetermined answers to the wizard prompts.

### 4.4 Key Invariants Tested

- **Append-only journal** -- Tests verify old events are untouched after appending (`test_audit_log.py`, line 114)
- **Atomic writes** -- No temp file residue after writes (`test_harness_cli.py`, line 155; `test_console_m53.py`, line 110)
- **Deterministic fingerprints** -- Protocol fingerprints are SHA-256 of canonical bytes (`test_inception.py`, lines 157-172; `test_cli_init.py`, lines 100-112)
- **Idempotency** -- Repeated runs skip existing outputs (`test_pipeline_executor.py`, line 226; `test_pipeline_script.py`, line 259)
- **Security** -- Path traversal rejection (`test_console_m52.py`, line 82), secret masking (`test_doctor.py`, line 224; `test_mcp_setup.py`, line 229), workspaces root refusal (`test_mcp_recon.py`, line 347; `recon/test_engine.py`, line 101)
- **Cross-kit contracts** -- Actions table references valid CLIs (`test_actions_cli_parity.py`), MCP tools are registered (`test_mcp_tool_parity.py`), pin freshness (`test_nexus_scholar_pins.py`)

### 4.5 Async Test Patterns

Async tests use `asyncio.run()` rather than `pytest-asyncio`:

```python
def test_something(tmp_path):
    async def scenario():
        ...
    assert asyncio.run(scenario())
```

**Files using this pattern:** `test_console_m52.py` (line 168), `test_console_m53.py` (line 474), `test_console_m54.py` (line 248), `test_console_serve.py` (line 245), `test_mcp_recon.py` (line 125), `recon/test_engine.py` (line 68), `recon/test_adaptive.py` (line 410)

### 4.6 Skip Markers

- `BASH = pytest.mark.skipif(not _bash_available(), ...)` in `test_pipeline_script.py` (line 43) -- skips bash-execution parity tests on Windows when bash is unavailable
- `@pytest.mark.skip` is not used elsewhere; no `xfail` markers found

---

## 5. Fixtures and Utilities

### 5.1 Shared Test Utilities

**`ScriptedResponder`** (defined in `test_inception.py`, line 186, reused in `test_cli_init.py` line 12):
- A generic pre-scripted answer provider implementing `text()`, `confirm()`, `choice()`, `multi()`, `num_if_valid()` methods
- Used across inception wizard tests for deterministic prompt filling

**`E2E_ANSWERS`** (defined in `test_inception.py`, line 215):
- The canonical answer sequence for the inception wizard e2e test
- Reused in `test_cli_init.py` for wizard handoff tests

**`GENESIS_TS`** (defined in `test_inception.py`, line 28):
- Frozen genesis timestamp `"2026-09-06T12:00:00+00:00"` used across inception tests for deterministic fingerprints

### 5.2 Fixtures

The suite uses **no shared conftest.py** in the tests/ root. Fixtures are defined locally within test files:

| Fixture | File | Line | Scope | Purpose |
|---------|------|------|-------|---------|
| `mock_protocol_workspace` | `test_harness_cli.py` | 19 | function | Creates a compiled protocol workspace for CLI tests |
| `mock_workspace` | `test_integrations.py` | 12 | function | Creates a workspace with included.json, references.bib, and synthesis markdown |
| `phase3_test_workspace` | `test_phase3_e2e.py` | 34 | function | Creates a Phase 3 workspace with canonical protocol |
| `stub_app` | `test_console_serve.py` | 209 | function | App with stub JobRunner injected into app.state |
| `_isolate_recon_cache_root` | `test_mcp_recon.py` | 35 | autouse | Pins MCP server's recon cache to tmp_path |
| `clean_env` | `test_scholar_agent_cli.py` | 15 | autouse | Saves/restores NEXUS_MCP_WORKSPACE and NEXUS_RECON_ROOT env vars |

### 5.3 Common Helper Functions

**Journal reader helpers** (defined in multiple files):
- `_journal(ws)` in `test_audit_log.py` (line 34), `test_cli_init.py` (line 31), `test_console_m54.py` (line 97)
- Pattern: reads `audit/journal.jsonl`, parses JSON lines, returns list of dicts

**Document factories** (defined in multiple files):
- `_doc(doi, title, abstract)` -- creates `Document` or dict with DOI-anchored fields
- `_fake_docs(n)` -- creates N fake documents for pool/engine tests
- `_pool(docs, cache_key)` -- wraps docs into a pool payload dict

---

## 6. Areas with Good/Poor Test Coverage

### 6.1 Excellent Coverage

1. **Recon subsystem** (`tests/recon/` + `test_mcp_recon.py` + `test_inception_grounded.py`)
   - Every layer tested: engine probe, distiller, adaptive followups, cache keys, gates, lexicon, MCP surface
   - Hermetic with injected `search_fn` -- zero network calls
   - Edge cases: empty pools, corrupt caches, workspaces root refusal, semantic mode, QEI gate

2. **Console server M5.x** (`test_console_m52.py`, `test_console_m53.py`, `test_console_m54.py`, `test_console_serve.py`)
   - Full HTTP endpoint coverage via TestClient
   - SSE streaming, job lifecycle (start/get/cancel), screening decisions, audit POST
   - Pipeline DAG execution (success, halt, cancel, single-flight) with real subprocesses

3. **Distribution/P7.x** (`test_cli_init.py`, `test_doctor.py`, `test_mcp_setup.py`, `test_audit_log.py`)
   - Comprehensive CLI surface coverage with help text assertions
   - Refusal rules, idempotency, secret masking, BOM tolerance
   - Wheel bundle loader simulation

4. **Conformance guards** (`tests/conformance/`)
   - Count-based drift detection: kits, actions, MCP tools, skills
   - Pin freshness (full SHA enforcement), codegen determinism
   - Actions-table <-> kit-CLI parity (parametrized across all 14 actions)

5. **Pipeline executor** (`test_pipeline_executor.py`, `test_pipeline_script.py`)
   - DAG scheduling, template resolution, on_fail modes, requires_decision halt/resume
   - Idempotency, cycle detection, bash execution parity

### 6.2 Areas with Moderate Coverage

1. **Phase 1-3 E2E tests** -- Full pipeline chains exist but are single-path; no edge-case variations (empty inputs, partial failures, large datasets)

2. **Orchestrator fidelity** -- Good monkeypatched coverage but relies on fake kit classes; no integration test with real kit CLIs

3. **Integration exporters** (`test_integrations.py`) -- Basic happy-path tests for LaTeX, Typst, Obsidian, Zotero; no error handling or edge cases tested

### 6.3 Areas with No/Low Coverage

1. **Error recovery and resilience** -- No tests for:
   - Kit CLI crashes mid-pipeline
   - Disk full / permission denied during writes
   - Corrupt protocol.json recovery
   - Concurrent workspace access

2. **Performance/load tests** -- Zero performance or load tests exist anywhere in the suite

3. **Security edge cases** -- While path traversal and secret masking are tested, there are no tests for:
   - Malicious input injection in CLI arguments
   - Large payload handling
   - Unicode/special character edge cases in workspace titles

4. **Kit-internal behavior** -- Kit packages (under `tools/`) have their own test suites (e.g., `tools/scholar-protocol-kit/tests/`); the harness tests only verify kit contracts at the CLI/API boundary

5. **Windows-specific behavior** -- BOM tolerance is tested in `test_doctor.py` (line 207) and `test_mcp_setup.py` (line 214), but most tests do not explicitly validate Windows path handling or line endings

6. **Export functionality beyond basic** -- The `test_harness_cli.py` tests export commands (LaTeX, Typst, Obsidian, Zotero) but only verify file existence, not content correctness (content tests are in `test_integrations.py`)

---

## 7. Recommendations for Improvement

### 7.1 High Priority

1. **Add a `conftest.py` at `tests/` root** -- Extract common fixtures (`_bootstrap`, `_journal`, `_scaffold`, document factories) to reduce duplication across 10+ files. This would also be the natural place for the `ScriptedResponder` and `E2E_ANSWERS` shared by `test_inception.py` and `test_cli_init.py`.

2. **Add pytest-asyncio** -- Replace `asyncio.run(scenario())` patterns with `@pytest.mark.asyncio` for cleaner async test code and better error reporting. The current pattern loses tracebacks from async exceptions.

3. **Add performance baselines** -- Even simple assertions like "inception wizard completes in <10s" or "pool merge of 25 docs completes in <1s" would catch regressions.

4. **Expand E2E edge cases** -- Add tests for:
   - Empty protocol / no research questions
   - Pipeline with all nodes failing
   - Concurrent screening decision writes
   - Very large candidate pools (1000+ papers)

### 7.2 Medium Priority

5. **Add parametrized conftest for kit CLI smoke tests** -- Instead of testing kit imports only in `test_count_freshness.py`, add a parametrized fixture that imports each kit and runs `--help` to catch import-time failures.

6. **Add fixture for workflow state machine** -- The console server tests duplicate workspace state setup; a shared fixture factory for common states (discovery, screening, synthesis, phase4) would reduce boilerplate.

7. **Add snapshot testing for rendered outputs** -- The pipeline script rendering tests (`test_pipeline_script.py`) verify content inline; snapshot tests would make it easier to review intentional rendering changes.

8. **Cross-platform CI assertions** -- Add explicit Windows/macOS path assertions in more tests (currently only `test_doctor.py` line 207 tests BOM tolerance on Windows).

### 7.3 Low Priority

9. **Add `--strict-markers` to pytest config** -- Currently no unknown markers warning; this would catch typos in `@pytest.mark.parametrize` or custom markers.

10. **Add test coverage reporting** -- Configure `pytest-cov` to generate coverage reports; the current suite has no coverage measurement.

11. **Document test architecture** -- The test suite has grown to ~8,900 lines across 35 files. A `tests/README.md` documenting the test architecture, conventions, and how to add new tests would help contributors.

12. **Consider `pytest-xdist` for parallel test execution** -- With 391 tests, parallel execution could significantly speed up CI.

---

## Appendix: File Tree

```
tests/
  __pycache__/
  conformance/
    __init__.py                          (8 lines)
    test_actions_cli_parity.py           (127 lines)
    test_count_freshness.py              (89 lines)
    test_mcp_tool_parity.py              (34 lines)
    test_nexus_scholar_pins.py           (198 lines)
  recon/
    __init__.py                          (0 lines)
    test_adaptive.py                     (565 lines)
    test_cache_key.py                    (106 lines)
    test_distiller.py                    (512 lines)
    test_engine.py                       (295 lines)
    test_gates.py                        (219 lines)
    test_inception_skill_helper.py       (139 lines)
    test_lexicon.py                      (472 lines)
  test_audit_log.py                      (394 lines)
  test_cli_init.py                       (322 lines)
  test_console_m52.py                    (184 lines)
  test_console_m53.py                    (482 lines)
  test_console_m54.py                    (358 lines)
  test_console_serve.py                  (347 lines)
  test_doctor.py                         (318 lines)
  test_harness_cli.py                    (200 lines)
  test_inception_grounded.py             (801 lines)
  test_inception.py                      (340 lines)
  test_integrations.py                   (133 lines)
  test_mcp_recon.py                      (666 lines)
  test_mcp_setup.py                      (421 lines)
  test_mcp_tools_graph.py                (619 lines)
  test_nexus_scholar_metapackage.py      (89 lines)
  test_orchestrator_fidelity.py          (317 lines)
  test_phase1_e2e.py                     (213 lines)
  test_phase2_e2e.py                     (283 lines)
  test_phase3_e2e.py                     (226 lines)
  test_pipeline_executor.py              (317 lines)
  test_pipeline_script.py                (314 lines)
  test_rigor_upgrades.py                 (96 lines)
  test_scholar_agent_cli.py              (97 lines)
```


---

<!-- Source: 05_documentation_analysis.md -->
# Documentation & Specifications Analysis

## Nexus Scholar Harness � Comprehensive Documentation Review

**Date:** 2026-09-14
**Scope:** docs/ and specs/ directories
**Total Documentation Files:** 50+ Markdown files across 2 major directories

---

## 1. Documentation Structure Overview

The documentation is organized into two primary directories with clear separation of concerns:

`
docs/
+-- README.md                          # Master documentation index
+-- nexus_scholar_user_guide.md        # End-user guide (PyPI/wheel)
+-- kits_surface_matrix.md             # API/CLI/MCP reference (all 8 kits)
+-- UPCOMING_WORK.md                   # Live roadmap & backlog
+-- architecture/
�   +-- README.md                      # Lifecycle architecture map
�   +-- phase_0/                       # Socratic inception (6 docs)
�   +-- phase_5/                       # Harness Console (5 docs)
�   +-- phase_6/                       # Scientific Trust Bridge (1 doc)
�   +-- phase_7_distribution/          # Distribution (1 doc)
+-- internal/
    +-- README.md                      # Internal docs index
    +-- COMMIT_SNAPSHOTS.md            # Historical workspace restore points
    +-- audits/                        # 3 adversarial review reports
    +-- ecosystem/                     # 4 ecosystem analysis docs
    +-- review_prompts/                # 2 reviewer agent templates

specs/
+-- exploratory-grounding-agent/       # 16 spec docs + evaluation data
�   +-- README.md                      # Spec index
�   +-- 01-16_*.md                     # Detailed specifications
�   +-- evaluation/                    # Trial evidence (JSON)
+-- inception-ecosystem/               # 4 orchestration skill specs
    +-- README.md                      # Ecosystem spec index
    +-- 01_skill_boundaries.md
    +-- 02_handoffs.md
    +-- 03_skill_tree_and_plugin_distribution.md
`

### Key Structural Decisions

1. **Phase-based architecture docs**: Phases 1-4 are NOT in docs/architecture/ because they are the 8 modular kits in 	ools/ � documented in kits_surface_matrix.md instead (line 21-23, docs/architecture/README.md).
2. **Internal vs. Public separation**: docs/internal/ holds adversarial audits, ecosystem analyses, and review prompts � not published to users.
3. **Specs as standalone**: specs/ holds detailed, interdependent specifications for complex subsystems (inception agent, ecosystem orchestration).

---

## 2. Key Documents and Their Purposes

### 2.1 Top-Level Documentation Index

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\README.md (44 lines)

The authoritative index that organizes all documentation into 5 categories:
- User & Getting Started Guides
- Technical References & Roadmap
- Architecture & Phase Design Sets
- Formal Specifications Series
- Internal Development & Archival Records

**Assessment:** Well-organized and concise. Serves as an effective entry point.

### 2.2 User Guide

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\nexus_scholar_user_guide.md (334 lines)

A comprehensive end-user guide covering:
- Installation (uvx, pip, uv tool) � lines 18-55
- Quick start (4-command workflow) � lines 57-73
- 
exus-scholar init � workspace scaffolding � lines 77-118
- 
exus-scholar setup-mcp � MCP wiring � lines 121-148
- 
exus-scholar doctor � health checks � lines 151-186
- 
exus-scholar log � audit contract � lines 189-262
- scholar-agent � MCP server � lines 264-282
- Configuration & environment variables � lines 285-297
- Troubleshooting � lines 318-328

**Assessment:** Excellent. Covers the full user journey from install to troubleshooting. This is production-quality documentation.

### 2.3 Kit Surface Matrix

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\kits_surface_matrix.md (387 lines)

The most technically dense document � a complete API/CLI/MCP reference for all 8 kits:
- Quick map table (lines 20-32)
- Critical cross-cutting findings (11 documented bugs/gaps, lines 35-157)
- Per-kit surface details (lines 160-342)
- Cross-kit dependency graph (lines 345-361)
- Environment variables and version pins (lines 363-381)

**Assessment:** Exceptional technical reference. The "critical cross-cutting findings" section (35 lines documenting 11 resolved issues) is particularly valuable � it is a living record of integration bugs found and fixed. This is the kind of document that prevents regression.

### 2.4 Roadmap (UPCOMING_WORK.md)

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\UPCOMING_WORK.md (60 lines)

Consolidated roadmap covering:
- Immediate architectural debt (P0-P1 fixes) � lines 7-13
- Phase 0-7 feature status with checkboxes � lines 17-60
- Phase 7 distribution checklist (P7.1-P7.9) � lines 50-60

**Assessment:** Concise and actionable. Supersedes earlier roadmap documents. Each item has clear status markers.

---

## 3. Architecture Documentation

### 3.1 Master Architecture Map

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\README.md (33 lines)

Defines the 8-phase lifecycle:
| Phase | Subsystem | Status |
|-------|-----------|--------|
| Phase 0 | Socratic Inception | Implemented |
| Phase 1 | Federated Discovery | Implemented |
| Phase 2 | PRISMA Screening | Implemented |
| Phase 3 | Extraction & RAG | Implemented |
| Phase 4 | Trust & Verification | Implemented |
| Phase 5 | Harness Console | Design Complete |
| Phase 6 | Scientific Trust Bridge | Active/Hardening |
| Phase 7 | Distribution | Shipped v1.0.0 |

**Assessment:** Clean and accurate. Explains why Phases 1-4 lack separate doc folders (they are the kits).

### 3.2 Phase 0: Socratic Inception (6 documents)

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_0\

| Document | Lines | Purpose |
|----------|-------|---------|
|  1_protocol_schema_specification.md | 298 | Full Pydantic v2 data models + JSON Schema for protocol.json |
|  2_playbook_templates_guide.md | 240 | 5 canonical research playbooks (PRISMA, Scoping, REA, Design Science, Novice) |
|  3_dynamic_matrix_dimensions.md | 225 | Domain-adaptive extraction dimensions (CS, Clinical, Social Science) |
|  4_socratic_inception_protocol.md | 86 | 4-stage interview protocol with Mermaid diagrams |
|  5_cycle_a_contract_first.md | 220 | Build spec for schema-freezing, canonical serialization, golden fixtures |

**Assessment:** The most thoroughly documented phase. The protocol schema specification (01) is essentially a complete API contract with Pydantic models, sample JSON, and validation rules. The cycle-A spec (05) is a build specification with precise deliverables and test matrices � unusual quality for open-source docs.

### 3.3 Phase 5: Harness Console (5 documents)

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_5\

| Document | Lines | Purpose |
|----------|-------|---------|
| README.md | 97 | Decision log (D1-D6), design rationale, Q&A |
| BLUEPRINT.md | 102 | System architecture diagram, layer responsibilities |
| PLAN.md | 75 | Milestones M5.0-M5.4, sequencing, risk register |
| SPECS.md | 223 | HTTP API, PipelineSpec schema, job runner, UI screens |
| COMPONENTS.md | 38 | Tailwind CSS component catalog mapping |

**Assessment:** Complete design set. The decision log (README lines 32-41) is particularly valuable � it documents 6 architectural decisions with rationale and source conflicts resolved. The SPECS.md is implementation-ready with endpoint definitions and acceptance tests.

### 3.4 Phase 6: Scientific Trust Bridge

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_6\README.md (134 lines)

Covers:
- Verbatim evidence verification (dual-pass character/token matching)
- Multi-screener Fleiss' kappa adjudication
- DeepSeek Harness (DSH) integration guide
- Verification metrics table

**Assessment:** Concise but complete. The DSH integration guide (lines 72-111) is actionable step-by-step documentation.

### 3.5 Phase 7: Distribution

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_7_distribution\README.md (166 lines)

Covers:
- 3-tier shipping strategy (metapackage, workspace CLI, universal MCP)
- Technical review with 11 identified gaps (lines 129-151)
- Implementation checklist P7.1-P7.9 (lines 154-165)

**Assessment:** Honest and thorough. The gap analysis (lines 131-151) identifies real obstacles before they become problems. All P7.x items are marked complete.

---

## 4. API Documentation

### 4.1 Kit Surface Matrix (Primary API Reference)

The kits_surface_matrix.md serves as the definitive API reference for all 8 kits. Key API surfaces documented:

**scholar-search-kit:**
- Public API: SearchEngine, Deduplicator, DocumentVerifier, CitationChainer, screening functions, Exporter
- CLI: 8 subcommands (search/snowball/chain/import/dedup/verify/export/screen)
- MCP: 
exus_discover, 
exus_dedup, 
exus_screen, 
exus_screen_reconcile
- Rate limits: OpenAlex 10/s, Crossref 5/s, S2 1/s, PubMed 3/s

**scholar-pdf-kit:**
- Public API: AsyncPDFDownloader, PyMuPDFEngine/DoclingEngine/GrobidEngine
- CLI: 3 subcommands (download/ingest/extract)
- MCP: 
exus_extract_pdf

**scholar-rag-kit:**
- Public API: ScholarIndexer, ScholarRetriever, GroundedSynthesisEngine, ConsensusCartographer, MatrixExtractor
- CLI: 6 subcommands (index/query/synthesize/consensus/matrix/stats)
- MCP: 
exus_rag_index, 
exus_rag_query, 
exus_rag_synthesize, 
exus_matrix_extract

**scholar-verify-kit:**
- Public API: RetractionChecker, open-science DAS/CAS, COI audit, QUADAS-2/PROBAST RoB, VerbatimClaimVerifier
- CLI: 7 subcommands (retraction/open-science/coi/risk-of-bias/trust-context/all/verbatim-claims)
- MCP: 
exus_verify_claims, 
exus_verify_phase4

### 4.2 Phase 5 HTTP API Specification

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_5\SPECS.md (lines 38-62)

Defines 20+ REST endpoints:
- GET /api/v1/workspace/meta � project.json, INDEX.md summary
- GET /api/v1/workspace/status � full status payload
- GET /api/v1/literature/candidates � deduped candidates
- POST /api/v1/screening/batch/{n}/decisions � append decisions
- POST /api/v1/jobs � create async job
- GET /api/v1/jobs/{id}/events � SSE stream
- GET /api/v1/agents/actions � CLI/MCP parity mapping

### 4.3 MCP Tool Inventory

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\kits_surface_matrix.md (lines 295-315)

19 MCP tools total (16 
exus_* + 3 
econ_*):
- Protocol: 
exus_protocol_compile, 
exus_protocol_validate, 
exus_protocol_render_criteria
- Discovery: 
exus_discover, 
exus_dedup
- Screening: 
exus_screen, 
exus_screen_reconcile
- PDF: 
exus_extract_pdf
- RAG: 
exus_rag_index, 
exus_rag_query, 
exus_rag_synthesize, 
exus_matrix_extract
- Graph: 
exus_graph_build
- Bibliography: 
exus_bib_clean
- Verification: 
exus_verify_claims, 
exus_verify_phase4
- Recon: 
econ_probe, 
econ_distill, 
econ_delta

---

## 5. Specifications and Protocols

### 5.1 Exploratory Grounding Agent (16 spec documents)

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\specs\exploratory-grounding-agent\

This is the most extensive specification in the repo � 16 interdependent documents covering the pre-protocol reconnaissance subsystem:

| Spec | Lines | Purpose |
|------|-------|---------|
|  1_problem_definition.md | 51 | Cold-inception gap, unknown-unknowns, hallucination risk |
|  2_architecture.md | 96 | Component inventory, sequence diagram, rate limits |
|  3_lifecycle.md | 59 | 5-step recon lifecycle (clarify?scan?distill?propose?refine) |
|  4_memory_and_cache.md | TBD | Two-tier storage, cache keys, session schema |
|  5_tool_contracts.md | TBD | Verified harness subsystem roles |
|  6_deployment_options.md | TBD | CLI wizard, autonomous agent/MCP, console |
|  7_walkthrough.md | TBD | End-to-end walkthrough (COBOL/Fortran LLM) |
|  8_milestones.md | TBD | M0.x implementation milestones |
|  9_mcp_integration.md | TBD | MCP surface for recon tools |
| 10_task_list.md | TBD | Implementation checklist |
| 11_honest_review.md | TBD | Post-M0.x retrospective |
| 12_semantic_grounding.md | TBD | Semantic search + topics taxonomy |
| 13_evaluation.md | 111 | 4-dimension evaluation framework (APR, QEI, downstream yield, navigation) |
| 14_agent_loops.md | TBD | 5 autonomous agent loops + 2 MCP seams |
| 15_scientific_publication_plan.md | TBD | Publication strategy & ReconBench |
| 16_inception_improvements.md | TBD | Post-evaluation improvement backlog |

**Key Invariant (from 01_problem_definition.md, line 42):** "Zero workspace pollution: all scratch state lives under .cache/inception_recon/."

**Key Invariant (from 03_lifecycle.md, line 57):** "Every term that survives into the final protocol must be traceable to a real Document."

### 5.2 Inception Ecosystem (4 spec documents)

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\specs\inception-ecosystem\

| Spec | Purpose |
|------|---------|
|  1_skill_boundaries.md | 3-layer skill stack: inception-agent ? methodology-copilot ? workspace-manager |
|  2_handoffs.md | Handoff contracts: scaffold ? intent ? compile ? audit |
|  3_skill_tree_and_plugin_distribution.md | Dual-tree topology, canonical-source rule, sync procedure |

**Key Design (from 01_skill_boundaries.md, lines 9-17):**
`	ext
inception-agent         (conversation driver)
        �
methodology-copilot     (classic interview)
        �
workspace-manager       (state layer)
`

### 5.3 Protocol Schema Specification

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_0\01_protocol_schema_specification.md (298 lines)

The machine-readable contract for protocol.json:
- 12 Pydantic v2 model classes
- 5 enum types (PlaybookType, EpistemologicalParadigm, DimensionDataType, etc.)
- Complete sample JSON (167-297)
- Validation rules and cross-field constraints

### 5.4 PipelineSpec Schema

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_5\SPECS.md (lines 66-128)

JSON DAG schema for no-code pipeline execution:
- Nodes reference kit CLIs with args
- Edges define execution order
- 
equires_decision: true for agent-in-the-loop steps
- Fingerprint-based idempotency
- Template variables: {{settings_key}} / {{input_key}}

---

## 6. User Guides and Tutorials

### 6.1 Primary User Guide

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\nexus_scholar_user_guide.md (334 lines)

Covers the complete user journey:
1. Install (uvx/pip/uv) � 3 options
2. Quick start � 4-command workflow
3. Workspace scaffolding (init)
4. MCP wiring (setup-mcp)
5. Health checks (doctor)
6. Audit logging (log)
7. MCP server (scholar-agent)
8. Configuration
9. Full CLI reference
10. Troubleshooting
11. Versioning

### 6.2 Project Landing Page

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\README.md

Referenced in docs/README.md but not read in this analysis. Contains ecosystem overview, quickstart, architecture flow, and package links.

### 6.3 Walkthrough (Spec)

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\specs\exploratory-grounding-agent\07_walkthrough.md

A concrete end-to-end walkthrough for LLM unit-test generation for legacy COBOL/Fortran code.

### 6.4 DSH Integration Guide

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\architecture\phase_6\README.md (lines 72-111)

Step-by-step DeepSeek Harness integration:
1. Register MCP server
2. Configure Creator Mode agent preset
3. File-contract routing

---

## 7. Internal Development Documents

### 7.1 Adversarial Audit Reports

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\internal\audits\

| Report | Purpose |
|--------|---------|
| harness_vision_report.md | Full-picture rating (5.2/10 overall), vision, 10 prioritized directions |
| harness_vision_report-11.md | Earlier version of the vision report |
| unified_harness_vision_report.md | Unified/consolidated vision report |

**Key Finding (from harness_vision_report.md, line 21):**
> "The Nexus Scholar Harness is a rigorously-specified, exhaustively-documented research suite whose governance discipline materially outstrips the reliability of its own primary runtime path."

This honest self-assessment identifies specific code-level bugs with line references.

### 7.2 Ecosystem Analyses

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\internal\ecosystem\

| Document | Purpose |
|----------|---------|
| NEXUS_ECOSYSTEM_ANALYSIS.md | Analysis of 17 related repositories across the ecosystem |
| NEXUS_HARNESS_SYNTHESIS.md | Synthesis of harness capabilities |
| NEXUS_MASTER_SPECIFICATION.md | Master specification across the ecosystem |
| NEXUS_PHP_ANALYSIS.md | Analysis of legacy PHP predecessor |

### 7.3 Review Prompts

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\internal\review_prompts\

| Prompt | Purpose |
|--------|---------|
| 
eview_prompt_harness_vision.md | Strategic review prompt (rate, vision, agent blueprint) |
| 
eview_prompt_inception_sweep.md | Inception subsystem sweep review prompt |

### 7.4 Commit Snapshots

**File:** C:\Users\mouadh\Documents\nexus-scholar-harness\docs\internal\COMMIT_SNAPSHOTS.md (49 lines)

Documents the pre-cleanup baseline snapshot (72090e5) for restoring historical workspace content.

---

## 8. Evaluation Data

### 8.1 Multi-Domain Trial Evidence

**Directory:** C:\Users\mouadh\Documents\nexus-scholar-harness\specs\exploratory-grounding-agent\evaluation\

| File | Purpose |
|------|---------|
| multi_domain_trial_2026-09-13.json | First trial run data |
| multi_domain_trial2_2026-09-13.json | Second trial run data |

Used to calibrate evaluation gates (QEI thresholds, pool sufficiency, topical coherence).

---

## 9. Areas Needing More Documentation

### 9.1 Documentation Gaps Identified

1. **Phase 5 Console Implementation Status:**
   - docs/architecture/phase_5/README.md (line 3) says "Planning" but the audit report (harness_vision_report.md, line 27) notes that serve.py, job_runner.py, ctions.py, and API routers are already implemented. The docs lag the code.

2. **Kit-Level Documentation:**
   - Phases 1-4 are documented only in kits_surface_matrix.md. Individual kit READMEs exist in 	ools/*/ but are not indexed in the main docs.

3. **Agent Skill Documentation:**
   - .agents/skills/*/SKILL.md files are referenced but not part of docs/. A mapping from skills to kit capabilities would help.

4. **Testing Documentation:**
   - No dedicated testing guide. The audit report notes that the "CI drift test" promised in ctions.py does not exist yet.

5. **Contributing Guide:**
   - CONTRIBUTING.md is not present. The contribution gate is documented in .agents/skills/pull-request-gate/SKILL.md but not in standard docs.

6. **API Versioning Policy:**
   - Protocol schema is v1.0.0, PipelineSpec is v0.1.0, but there is no document describing the versioning policy or backward compatibility guarantees.

7. **Deployment/Operations Guide:**
   - No guide for self-hosting, production deployment, or scaling considerations.

8. **Changelog/Release Notes:**
   - No CHANGELOG.md or structured release notes beyond git tags.

9. **Glossary:**
   - Technical terms (APR, QEI, PRISMA, DAS/CAS, QUADAS-2, PROBAST) are used throughout but not collected in a glossary.

10. **ReconBench Benchmark:**
    - 13_evaluation.md (line 80+) describes the ReconBench benchmark but it is marked as "proposed" � no implementation documentation exists yet.

### 9.2 Documentation Quality Observations

**Strengths:**
- Exceptional technical depth in kits_surface_matrix.md � the 11 documented and resolved cross-cutting findings are a model for integration documentation
- Honest self-assessment in audit reports with specific code-line references
- Complete design sets for Phase 5 and Phase 7 with decision logs
- Protocol schema specification is implementation-ready with Pydantic models
- Evaluation framework is mathematically grounded (APR, QEI formulas)

**Weaknesses:**
- Some docs lag implementation status (Phase 5 described as "Planning" when code exists)
- No cross-referencing between specs/ and docs/architecture/ documents
- Internal documents could be better indexed
- No API changelog or version migration guides

---

## 10. Documentation Statistics

| Category | Files | Total Lines (approx) |
|----------|-------|---------------------|
| Top-level docs | 4 | 825 |
| Architecture phase docs | 13 | 2,100+ |
| Internal docs | 10 | 1,500+ |
| Specs (exploratory agent) | 16 | 1,500+ |
| Specs (inception ecosystem) | 4 | 400+ |
| **Total** | **47+** | **6,300+** |

---

## 11. Key Findings Summary

1. **Documentation is exceptionally thorough** for an open-source project � the kit surface matrix alone (387 lines) is more detailed than most projects' entire API docs.

2. **Honest self-assessment** is a recurring theme � the audit reports document real bugs with line numbers, and the roadmap honestly marks items as incomplete.

3. **The documentation-to-code ratio is high** � this is a "spec-first" project where architecture decisions are documented before implementation.

4. **Phase-based organization is clean** � the decision to document kits in kits_surface_matrix.md rather than creating empty phase folders is pragmatic.

5. **The main gap is between docs and implementation status** � Phase 5 docs say "Planning" but code exists; this should be reconciled.

6. **Missing standard open-source docs**: CONTRIBUTING.md, CHANGELOG.md, glossary, and testing guide would improve onboarding.

---

*Analysis completed 2026-09-14 by documentation analysis agent.*


---

