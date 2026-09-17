# Comprehensive Test Suite Analysis

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
