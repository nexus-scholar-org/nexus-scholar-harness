# Phase D Execution Plan

**Phase:** D — LLM-Enhanced Screening & Pipeline MCP Tools  
**Total Effort:** 8.5 hours  
**Target System:** `scholar-agent-kit` MCP server  
**Spec:** `specs/phase_d_agent/README.md`

---

## Task 1: Add `nexus_screen_llm` MCP Tool Skeleton [INDEPENDENT]
**Description:** Register a new `nexus_screen_llm` MCP tool function in `server.py` with the correct signature, docstring, and path resolution. No business logic yet — just the scaffolding that passes path validation and returns a placeholder.

**Files to Touch:**
- `tools/scholar-agent-kit/src/scholar_agent/server.py`

### Execution Checklist
- [ ] Add `@mcp.tool()` decorated function `nexus_screen_llm` after the existing `nexus_screen` tool (around line 356)
- [ ] Parameters: `input_path: str`, `protocol_path: str`, `output_dir: str = "./literature"`, `api_key: str = None`, `model: str = "gemini-2.0-flash"`, `batch_size: int = 20`, `temperature: float = 0.1`
- [ ] Add docstring describing LLM-enhanced screening with checklist-based prompts and heuristic fallback
- [ ] Add path resolution calls: `_resolve_path(input_path)`, `_resolve_path(protocol_path)`, `_resolve_path(output_dir)`
- [ ] Add early-exit error for missing input/protocol files
- [ ] Return placeholder JSON: `{"status": "NOT_IMPLEMENTED"}`

### Testing Strategy
- Run `uv run pytest tests/conformance/test_mcp_tool_parity.py -v` — verify `nexus_screen_llm` appears in `REGISTERED_TOOLS` and `--help` output
- Unit test: call `nexus_screen_llm` with non-existent paths, assert error message returned
- Mock: none required for skeleton

### Definition of Done (DoD)
- `nexus_screen_llm` appears in `mcp._tool_manager.list_tools()` set
- `uv run pytest tests/conformance/test_mcp_tool_parity.py` passes
- Calling with missing files returns a JSON error, not an unhandled exception

---

## Task 2: Wire `LLMBatchScreener` + `calibration.py` Integration [INDEPENDENT]
**Description:** Implement the happy-path LLM screening logic inside `nexus_screen_llm`: load inputs, build checklist schema via `calibration.py`, invoke `LLMBatchScreener`, convert results to `ScreeningDecision` objects, partition, and write output artifacts.

**Files to Touch:**
- `tools/scholar-agent-kit/src/scholar_agent/server.py`

### Execution Checklist
- [ ] Add deferred imports inside the function body (P7.7 lazy-import rule):
  ```python
  from scholar_search.screening import LLMBatchScreener, partition_screening_results
  from scholar_search.importers import JSONImporter
  from scholar_agent.calibration import build_checklist_schema, checklist_to_decision
  ```
- [ ] Load raw docs via `JSONImporter().parse(inp)` and protocol data via `json.loads()`
- [ ] Build checklist schema: `checklist_schema = build_checklist_schema(protocol_data)`
- [ ] Instantiate `LLMBatchScreener(api_key=api_key, model=model, batch_size=batch_size, temperature=temperature)`
- [ ] Call `await screener.screen_batch(raw_docs, protocol_data)` inside `asyncio.run()`
- [ ] Partition results: `partition_screening_results(raw_docs, decisions)`
- [ ] Write 5 output files: `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json`, `prisma_screening_report.md` to `output_dir`
- [ ] Return success message with counts

### Testing Strategy
- Unit test in `tools/scholar-agent-kit/tests/test_screening.py`: mock `LLMBatchScreener.screen_batch` to return pre-canned `ScreeningDecision` objects; verify all 5 output files are written
- Mock `JSONImporter.parse` to return sample documents
- Use `sample_papers_json` and `sample_protocol_json` fixtures from spec §3.3

### Definition of Done (DoD)
- Happy-path call with mock LLM produces `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json`, `prisma_screening_report.md`
- No real LLM API calls made (mocked)
- `uv run pytest tools/scholar-agent-kit/tests/test_screening.py -v` passes

---

## Task 3: Add Heuristic Fallback on LLM Failure
**Description:** Wrap the LLM call in a try/except so that if `LLMBatchScreener` fails (network error, rate limit, auth), the tool falls back to `evaluate_heuristic_screening()` — the same logic used by the existing `nexus_screen` tool.

**Files to Touch:**
- `tools/scholar-agent-kit/src/scholar_agent/server.py`

### Execution Checklist
- [ ] Add deferred import: `from scholar_search.screening import evaluate_heuristic_screening`
- [ ] Wrap `LLMBatchScreener.screen_batch()` call in `try/except Exception`
- [ ] On exception: log warning via `logger.warning("LLM screening failed (%s), falling back to heuristic", llm_err)`
- [ ] Fallback path: `decisions = [evaluate_heuristic_screening(d, protocol_data) for d in raw_docs]`
- [ ] Ensure fallback uses same `protocol_data` dict (extract `screening_criteria` and `research_questions` keys if needed)

### Testing Strategy
- Unit test: mock `LLMBatchScreener.screen_batch` to raise `ConnectionError`; assert fallback still produces valid `included.json`/`excluded.json`
- Unit test: mock `LLMBatchScreener` constructor to raise; assert tool returns output files and success message
- Fixture: same `sample_papers_json` + `sample_protocol_json`

### Definition of Done (DoD)
- When LLM call raises any exception, tool produces identical output structure (5 files) via heuristic path
- Warning is logged (visible in test output with `-v`)
- `uv run pytest tools/scholar-agent-kit/tests/test_screening.py -v` passes

---

## Task 4: Add `nexus_screen_llm` Conformance + Integration Tests [INDEPENDENT]
**Description:** Write comprehensive tests for the LLM screening tool: conformance (registration + schema), unit (mock LLM path, fallback path), and integration (end-to-end with mocked LLM returning realistic decisions).

**Files to Touch:**
- `tests/conformance/test_mcp_tool_parity.py` (verify it already covers new tool — no edits needed if `@mcp.tool()` registration works)
- `tools/scholar-agent-kit/tests/test_screening.py` (new file)

### Execution Checklist
- [ ] Create `tools/scholar-agent-kit/tests/test_screening.py`
- [ ] Add fixtures: `sample_papers_json(tmp_path)`, `sample_protocol_json(tmp_path)` per spec §3.3
- [ ] Test: `test_screen_llm_tool_registered` — verify `nexus_screen_llm` in `REGISTERED_TOOLS`
- [ ] Test: `test_screen_llm_missing_input` — call with nonexistent path, assert error returned
- [ ] Test: `test_screen_llm_missing_protocol` — call with valid input but missing protocol, assert error
- [ ] Test: `test_screen_llm_happy_path_mock_llm` — mock `LLMBatchScreener` to return 2 `ScreeningDecision` objects (1 INCLUDE, 1 EXCLUDE), verify 5 output files written with correct counts
- [ ] Test: `test_screen_llm_fallback_on_llm_failure` — mock LLM to raise, verify heuristic fallback produces output files
- [ ] Test: `test_screen_llm_checklist_schema_used` — mock LLM, verify `build_checklist_schema` was called with protocol data (use `unittest.mock.patch`)

### Testing Strategy
- All tests use `unittest.mock.patch` / `unittest.mock.MagicMock` for LLM and importer
- Use `tmp_path` fixture for all file I/O (hermetic)
- No real API calls
- Run: `uv run pytest tools/scholar-agent-kit/tests/test_screening.py -v`

### Definition of Done (DoD)
- All 8 tests pass
- `uv run pytest tools/scholar-agent-kit/tests/test_screening.py -v` — 0 failures
- `uv run pytest tests/conformance/test_mcp_tool_parity.py -v` — still passes

---

## Task 5: Add `nexus_pipeline_run` MCP Tool Skeleton [INDEPENDENT]
**Description:** Register a new `nexus_pipeline_run` MCP tool function in `server.py` with the correct signature, docstring, and workspace validation. No business logic — just scaffolding.

**Files to Touch:**
- `tools/scholar-agent-kit/src/scholar_agent/server.py`

### Execution Checklist
- [ ] Add `@mcp.tool()` decorated function `nexus_pipeline_run` after `nexus_screen_llm`
- [ ] Parameters: `workspace_dir: str`, `query: str = None`, `protocol_path: str = None`, `skip_stages: str = None`
- [ ] Add docstring: "Run the full 10-stage ResearchOrchestrator pipeline."
- [ ] Add path resolution: `_resolve_path(workspace_dir)`
- [ ] Add workspace existence check: `if not ws.is_dir(): return error`
- [ ] Return placeholder JSON: `{"status": "NOT_IMPLEMENTED"}`

### Testing Strategy
- Run `uv run pytest tests/conformance/test_mcp_tool_parity.py -v` — verify `nexus_pipeline_run` in `REGISTERED_TOOLS`
- Unit test: call with nonexistent workspace dir, assert error message
- Mock: none required for skeleton

### Definition of Done (DoD)
- `nexus_pipeline_run` appears in `mcp._tool_manager.list_tools()` set
- `uv run pytest tests/conformance/test_mcp_tool_parity.py` passes
- Calling with missing workspace returns a JSON error

---

## Task 6: Wire `ResearchOrchestrator` Import and `run_pipeline_async`
**Description:** Implement the pipeline execution logic inside `nexus_pipeline_run`: import `ResearchOrchestrator`, parse `skip_stages`, instantiate the orchestrator, and call `run_pipeline_async`.

**Files to Touch:**
- `tools/scholar-agent-kit/src/scholar_agent/server.py`

### Execution Checklist
- [ ] Add deferred import inside function body (P7.7 lazy-import):
  ```python
  from scholar_harness.orchestrator import ResearchOrchestrator
  ```
- [ ] Parse `skip_stages`: `skip = {s.strip() for s in skip_stages.split(",")}` if provided, else empty set
- [ ] Instantiate orchestrator: `orchestrator = ResearchOrchestrator(workspace_dir=ws)`
- [ ] Call result: `result = asyncio.run(orchestrator.run_pipeline_async(protocol_path=protocol_path_resolved))`
- [ ] Return JSON with `status`, `workspace`, `stages_completed`, `final_status`
- [ ] Wrap in try/except returning `{"status": "ERROR", "error": str(e)}`

### Testing Strategy
- Unit test in `tools/scholar-agent-kit/tests/test_pipeline.py`: mock `ResearchOrchestrator` constructor and `run_pipeline_async` to return canned result; verify JSON response
- Unit test: mock `ResearchOrchestrator` to raise `FileNotFoundError`; verify error response
- Mock `asyncio.run` if needed to avoid event loop issues in tests

### Definition of Done (DoD)
- Happy-path call with mock orchestrator returns `{"status": "SUCCESS", "stages_completed": {...}}`
- Missing workspace returns error JSON
- `uv run pytest tools/scholar-agent-kit/tests/test_pipeline.py -v` passes

---

## Task 7: Add `nexus_pipeline_run` Conformance + Integration Tests [INDEPENDENT]
**Description:** Write comprehensive tests for the pipeline tool: conformance, unit, and integration tests with mocked orchestrator.

**Files to Touch:**
- `tools/scholar-agent-kit/tests/test_pipeline.py` (new file)

### Execution Checklist
- [ ] Create `tools/scholar-agent-kit/tests/test_pipeline.py`
- [ ] Test: `test_pipeline_tool_registered` — verify `nexus_pipeline_run` in `REGISTERED_TOOLS`
- [ ] Test: `test_pipeline_missing_workspace` — call with nonexistent dir, assert error
- [ ] Test: `test_pipeline_happy_path_mock` — mock `ResearchOrchestrator` to return `{"status": "SUCCESS", "stages": {"discovery": 10}}`, verify JSON response
- [ ] Test: `test_pipeline_skip_stages` — pass `skip_stages="discovery,dedup"`, verify orchestrator called correctly
- [ ] Test: `test_pipeline_orchestrator_error` — mock orchestrator to raise, verify error JSON returned
- [ ] Test: `test_pipeline_with_query` — pass `query` parameter, verify it's passed to orchestrator context

### Testing Strategy
- All tests use `unittest.mock.patch` for `ResearchOrchestrator`
- Use `tmp_path` fixture to create a temp workspace directory
- No real pipeline execution
- Run: `uv run pytest tools/scholar-agent-kit/tests/test_pipeline.py -v`

### Definition of Done (DoD)
- All 6 tests pass
- `uv run pytest tools/scholar-agent-kit/tests/test_pipeline.py -v` — 0 failures
- `uv run pytest tests/conformance/test_mcp_tool_parity.py -v` — still passes

---

## Task 8: Update SKILL.md Documentation [INDEPENDENT]
**Description:** Update the `scholar-agent-kit` SKILL.md to document the two new MCP tools (`nexus_screen_llm`, `nexus_pipeline_run`) with their parameters, usage examples, and behavioral notes.

**Files to Touch:**
- `.agents/skills/scholar-agent-kit/SKILL.md`

### Execution Checklist
- [ ] Add `nexus_screen_llm` to "Discovery / screening" section (bump count from 4 to 5)
- [ ] Document parameters: `input_path`, `protocol_path`, `output_dir`, `api_key`, `model`, `batch_size`, `temperature`
- [ ] Note: falls back to heuristic screening on LLM failure
- [ ] Add `nexus_pipeline_run` as new "Pipeline (1)" section
- [ ] Document parameters: `workspace_dir`, `query`, `protocol_path`, `skip_stages`
- [ ] Note: wraps existing `ResearchOrchestrator` — 10-stage async pipeline
- [ ] Update tool count in header from "19 total" to "21 total"

### Testing Strategy
- Manual review: ensure SKILL.md renders correctly (Markdown lint)
- Grep for `nexus_screen_llm` and `nexus_pipeline_run` in SKILL.md — both present

### Definition of Done (DoD)
- `grep -c "nexus_screen_llm" .agents/skills/scholar-agent-kit/SKILL.md` returns 1+
- `grep -c "nexus_pipeline_run" .agents/skills/scholar-agent-kit/SKILL.md` returns 1+
- Tool count updated to 21

---

## Task 9: Full Test Suite Regression Check
**Description:** Run the entire test suite to confirm zero regressions and that all new tests pass alongside existing tests.

**Files to Touch:**
- None (read-only verification)

### Execution Checklist
- [ ] Run `uv run pytest tests/conformance/test_mcp_tool_parity.py -v` — conformance passes
- [ ] Run `uv run pytest tools/scholar-agent-kit/tests/ -v` — all agent-kit tests pass
- [ ] Run `uv run ruff check scripts/` — lint clean (CI scope)
- [ ] Run `uv run pytest -v` — full suite, 0 failures

### Testing Strategy
- Full suite execution — no mocking, no new tests, just verification
- Expected: all existing 391+ tests still pass; new tests (4–6 per feature) also pass

### Definition of Done (DoD)
- `uv run pytest -v` — 0 failures, all tests green
- `uv run ruff check scripts/` — 0 errors

---

## Task 10: Monorepo Sync (Post-Implementation) [INDEPENDENT]
**Description:** Sync kit changes to external repos, update `plugins.json` commit SHA, and regenerate metapackage pins per AGENTS.md monorepo governance rules.

**Files to Touch:**
- `plugins.json` (commit SHA update)
- `packaging/nexus-scholar/nexus_scholar_pins.json` (regenerated)

### Execution Checklist
- [ ] Run `python scripts/push_tools.py` — sync `tools/scholar-agent-kit/` to its external repo
- [ ] Update `plugins.json` `scholar-agent-kit` `default_rev` to the new full commit SHA
- [ ] Run `python scripts/generate_nexus_scholar_pins.py --check` — verify freshness
- [ ] Run `python scripts/generate_nexus_scholar_pins.py` — regenerate pins if needed
- [ ] Run `uv run pytest tests/conformance/ -v` — conformance still passes after pin update

### Testing Strategy
- Verify `plugins.json` SHA matches latest commit in kit repo
- Verify `nexus_scholar_pins.json` is deterministic (re-run `--check` passes)
- Full conformance suite after sync

### Definition of Done (DoD)
- `python scripts/generate_nexus_scholar_pins.py --check` exits 0
- `uv run pytest tests/conformance/ -v` — all pass
- Kit external repo contains the new `nexus_screen_llm` and `nexus_pipeline_run` functions

---

## Execution Order Summary

```
Task 1 (D1 skeleton)  ──┐
Task 5 (D2 skeleton)  ──┼── [INDEPENDENT, can run in parallel]
Task 8 (SKILL.md)     ──┘
                         │
Task 2 (D1 LLM wiring) ── depends on Task 1
Task 3 (D1 fallback)   ── depends on Task 2
Task 4 (D1 tests)      ── depends on Tasks 1–3
                         │
Task 6 (D2 wiring)     ── depends on Task 5
Task 7 (D2 tests)      ── depends on Tasks 5–6
                         │
Task 9 (full regression) ── depends on Tasks 4, 7
Task 10 (monorepo sync)  ── depends on Task 9
```

**Parallelizable group:** Tasks 1, 5, 8 (no dependencies on each other)  
**Critical path:** 1 → 2 → 3 → 4 → 9 → 10 (D1: 4.5h)  
**D2 path:** 5 → 6 → 7 → 9 → 10 (D2: 2.5h, runs alongside D1)
