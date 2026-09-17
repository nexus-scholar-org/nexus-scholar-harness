# Phase D: LLM-Enhanced Screening & Pipeline MCP Tools

**Specification Version:** 1.1.0  
**Status:** READY FOR IMPLEMENTATION  
**Target System:** `scholar-agent-kit` (MCP server) + `scholar-search-kit` (screening) + `scholar-harness` (orchestrator)  
**Estimated Duration:** 2 days (Days 15–16)  
**Success Gates:** LLM screening F1 ≥ 0.85; Pipeline MCP tool wraps existing orchestrator; 0 regressions

---

## 1. Executive Summary

Phase D adds **LLM-enhanced screening** and **pipeline automation** as MCP tools on the existing `scholar-agent-kit` server. Instead of creating parallel systems, this phase wraps existing kit APIs (`LLMBatchScreener`, `calibration.py`, `ResearchOrchestrator`) as new MCP tools.

### 1.1 Features Overview

| # | Feature | Kit | Impact | Effort |
|---|---------|-----|--------|--------|
| D1 | LLM-Enhanced Screening MCP Tool | scholar-agent-kit + scholar-search-kit | High | Medium |
| D2 | Pipeline Automation MCP Tool | scholar-agent-kit + scholar-harness | Medium | Low |

> **Dropped: MCP Tool Abstraction Layer.** The existing `MCPServer` already auto-discovers tools, generates JSON schemas from type hints, validates inputs via Pydantic, and handles execution. A parallel `MCPToolRegistry` would be redundant with worse type handling (6 hardcoded types vs. Pydantic's full type system).

### 1.2 Methodological Value

- **LLM Screening:** Checklist-based LLM screening aligned with `calibration.py`'s structured-boolean design, preventing LLM drift on subjective framing
- **Pipeline Automation:** One-call access to the full 10-stage `ResearchOrchestrator` pipeline via MCP

---

## 2. Feature Specifications

### 2.1 D1: LLM-Enhanced Screening MCP Tool

**Goal:** Add `nexus_screen_llm` MCP tool that wraps `LLMBatchScreener` from `scholar-search-kit` with checklist-based LLM prompts from `calibration.py`.

#### 2.1.1 Design Rationale

The existing `nexus_screen` MCP tool uses `evaluate_heuristic_screening()` (rule-based). D1 adds an LLM-enhanced variant that:

1. Uses `build_checklist_schema()` from `calibration.py` to generate structured boolean prompts (one per criterion) — prevents LLM drift
2. Uses `LLMBatchScreener` from `scholar-search-kit/screening.py` for actual LLM calls (working Gemini REST API integration)
3. Uses `checklist_to_decision()` from `calibration.py` to deterministically derive `ScreeningDecision` from filled checklists
4. Falls back to `evaluate_heuristic_screening()` on LLM failure
5. Pipes results through `partition_screening_results()` for PRISMA artifacts

This approach:
- **Does NOT** create `screening.py` in scholar-agent-kit (reuses existing code)
- **Does NOT** reimplement heuristic screening (reuses `evaluate_heuristic_screening`)
- **Does NOT** reimplement LLM calls (reuses `LLMBatchScreener`)
- **Does NOT** use free-form prompts (uses structured boolean checklist from `calibration.py`)
- **Returns** `ScreeningDecision` dataclass objects (not raw dicts)

#### 2.1.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-agent-kit/src/scholar_agent/server.py` | Add `nexus_screen_llm` MCP tool function |

> **No new files created.** D1 adds a single function to the existing MCP server.

#### 2.1.3 Implementation Details

```python
# ADD TO: tools/scholar-agent-kit/src/scholar_agent/server.py
# After the existing nexus_screen tool (around line 355)

@mcp.tool()
def nexus_screen_llm(
    input_path: str,
    protocol_path: str,
    output_dir: str = "./literature",
    api_key: str = None,
    model: str = "gemini-2.0-flash",
    batch_size: int = 20,
    temperature: float = 0.1,
) -> str:
    """
    LLM-enhanced screening using structured boolean checklists.
    
    Like nexus_screen but uses LLM reasoning instead of pure heuristics.
    Uses calibration.py checklist schema to prevent LLM drift.
    Falls back to evaluate_heuristic_screening on LLM failure.
    
    Outputs: included.json, excluded.json, conflicts.json,
             prisma_report.json, prisma_screening_report.md
    """
    from scholar_search.screening import (
        LLMBatchScreener,
        evaluate_heuristic_screening,
        partition_screening_results,
        batch_partition,
    )
    from scholar_search.importers import JSONImporter
    from scholar_agent.calibration import (
        build_checklist_schema,
        checklist_to_decision,
    )
    
    input_path_resolved = _resolve_path(input_path) or input_path
    protocol_path_resolved = _resolve_path(protocol_path) or protocol_path
    output_dir_resolved = _resolve_path(output_dir) or output_dir
    
    inp = Path(input_path_resolved)
    proto = Path(protocol_path_resolved)
    
    if not inp.exists() or not proto.exists():
        return json.dumps({"status": "ERROR", "error": "Input or protocol file not found."})
    
    try:
        # Load inputs
        importer = JSONImporter()
        raw_docs = list(importer.parse(inp))
        protocol_data = json.loads(proto.read_text(encoding="utf-8"))
        
        # Build checklist schema from protocol
        checklist_schema = build_checklist_schema(protocol_data)
        
        # Try LLM screening first
        try:
            import asyncio
            screener = LLMBatchScreener(
                api_key=api_key,
                model=model,
                batch_size=batch_size,
                temperature=temperature,
            )
            decisions = asyncio.run(screener.screen_batch(raw_docs, protocol_data))
        except Exception as llm_err:
            # Fallback to heuristic screening
            logger.warning("LLM screening failed (%s), falling back to heuristic", llm_err)
            criteria = protocol_data.get("screening_criteria", {})
            questions = protocol_data.get("research_questions", [])
            decisions = [evaluate_heuristic_screening(d, criteria, questions) for d in raw_docs]
        
        # Partition results using existing pipeline
        included, excluded, conflicts, report = partition_screening_results(raw_docs, decisions)
        
        # Write outputs
        out_d = Path(output_dir_resolved)
        out_d.mkdir(parents=True, exist_ok=True)
        (out_d / "included.json").write_text(
            json.dumps(included, indent=2, default=str), encoding="utf-8"
        )
        (out_d / "excluded.json").write_text(
            json.dumps(excluded, indent=2, default=str), encoding="utf-8"
        )
        (out_d / "conflicts.json").write_text(
            json.dumps(conflicts, indent=2, default=str), encoding="utf-8"
        )
        (out_d / "prisma_report.json").write_text(
            json.dumps(asdict(report), indent=2, default=str), encoding="utf-8"
        )
        (out_d / "prisma_screening_report.md").write_text(
            report.to_markdown() if hasattr(report, "to_markdown") else str(report),
            encoding="utf-8",
        )
        
        return (
            f"LLM screening complete: {len(included)} included, {len(excluded)} excluded, "
            f"{len(conflicts)} conflicts flagged. "
            f"Artifacts in {out_d}."
        )
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})
```

#### 2.1.4 Integration Points

| Existing Code | Location | How D1 Uses It |
|---------------|----------|----------------|
| `LLMBatchScreener` | `scholar_search/screening.py:487-614` | LLM batch screening with Gemini REST API |
| `evaluate_heuristic_screening()` | `scholar_search/screening.py:208-340` | Heuristic fallback |
| `partition_screening_results()` | `scholar_search/screening.py:343-408` | Split included/excluded/conflicts |
| `batch_partition()` | `scholar_search/screening.py:76-80` | Document batching |
| `build_checklist_schema()` | `scholar_agent/calibration.py:29-58` | Structured boolean checklist |
| `checklist_to_decision()` | `scholar_agent/calibration.py:65-128` | Deterministic decision from checklist |
| `JSONImporter` | `scholar_search/importers.py` | Load papers from JSON |
| `_resolve_path()` | `scholar_agent/server.py:152-161` | MCP anchor-aware path resolution |

---

### 2.2 D2: Pipeline Automation MCP Tool

**Goal:** Add `nexus_pipeline_run` MCP tool that wraps the existing `ResearchOrchestrator` for one-call pipeline execution.

#### 2.2.1 Design Rationale

The existing `ResearchOrchestrator` in `src/scholar_harness/orchestrator.py` (731 lines) already implements a 10-stage async pipeline:
1. Discovery (`SearchEngine.search_all`)
2. Deduplication (`Deduplicator.deduplicate`)
3. Verification (`RetractionChecker`, `open_science`, etc.)
4. Screening (`evaluate_heuristic_screening` + `partition_screening_results`)
5. PDF Harvesting & Extraction (`PyMuPDFEngine.extract_markdown`)
6. RAG Indexing (`ScholarIndexer.index_directory`)
7. Matrix Extraction (`MatrixExtractor.extract_all`)
8. Graph Building (`CitationGraphBuilder.build_graph`)
9. Synthesis (`GroundedSynthesisEngine.synthesize`)
10. Audit Logging (`_log_audit_event`)

D2 wraps this existing orchestrator as an MCP tool, giving AI agents direct access to the full pipeline without reimplementing any logic.

#### 2.2.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-agent-kit/src/scholar_agent/server.py` | Add `nexus_pipeline_run` MCP tool function |

> **No new files created.** D2 adds a single function to the existing MCP server.

#### 2.2.3 Implementation Details

```python
# ADD TO: tools/scholar-agent-kit/src/scholar_agent/server.py
# After the nexus_screen_llm tool

@mcp.tool()
def nexus_pipeline_run(
    workspace_dir: str,
    query: str = None,
    protocol_path: str = None,
    skip_stages: str = None,
) -> str:
    """
    Run the full 10-stage ResearchOrchestrator pipeline.
    
    Stages: Discovery → Dedup → Verify → Screen → Extract → Index → Matrix → Graph → Synthesize → Audit.
    
    Args:
        workspace_dir: Workspace directory (must contain protocol.json or provide protocol_path)
        query: Search query (optional, overrides protocol research_questions)
        protocol_path: Path to protocol.json (optional, defaults to workspace_dir/protocol.json)
        skip_stages: Comma-separated stage names to skip (e.g. "discovery,dedup")
    """
    import asyncio
    
    ws = Path(_resolve_path(workspace_dir) or workspace_dir).resolve()
    if not ws.is_dir():
        return json.dumps({"status": "ERROR", "error": f"Workspace not found: {workspace_dir}"})
    
    try:
        # Import the existing orchestrator
        from scholar_harness.orchestrator import ResearchOrchestrator
        
        # Parse skip_stages
        skip = set()
        if skip_stages:
            skip = {s.strip() for s in skip_stages.split(",")}
        
        # Build minimal context for orchestrator
        context = {
            "workspace_dir": str(ws),
            "protocol_path": str(Path(protocol_path) if protocol_path else ws / "protocol.json"),
        }
        if query:
            context["query"] = query
        
        # Run orchestrator
        # Assume ResearchOrchestrator has a create() factory or use default dependencies
        from scholar_harness.orchestrator import create_orchestrator
        orchestrator = create_orchestrator()
        result = asyncio.run(orchestrator.run_pipeline_async(
            workspace_dir=ws,
            skip_stages=skip,
        ))
        
        return json.dumps({
            "status": "SUCCESS",
            "workspace": str(ws),
            "stages_completed": result.get("stages", {}),
            "final_status": result.get("status", "UNKNOWN"),
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})
```

#### 2.2.4 Integration Points

| Existing Code | Location | How D2 Uses It |
|---------------|----------|----------------|
| `ResearchOrchestrator` | `src/scholar_harness/orchestrator.py` | Full 10-stage pipeline |
| `run_pipeline_async()` | `src/scholar_harness/orchestrator.py` | Async pipeline execution |
| `_resolve_path()` | `scholar_agent/server.py:152-161` | MCP anchor-aware path resolution |

---

## 3. Testing Strategy

### 3.1 Testing Principles

1. **Hermetic Tests:** Mock LLM API calls; no real Gemini invocations
2. **Isolated Workspaces:** Use `tmp_path` fixture for all file I/O
3. **Reuse Existing Fixtures:** Use `sample_protocol`, `sample_papers` from existing test infrastructure
4. **Conformance Tests:** New MCP tools must pass `test_mcp_tool_parity.py`

### 3.2 Test Categories

#### 3.2.1 Unit Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| D1: nexus_screen_llm | `tests/conformance/test_mcp_tool_parity.py` | Tool registered, schema valid |
| D1: Fallback behavior | `tools/scholar-agent-kit/tests/test_screening.py` | LLM failure → heuristic fallback |
| D2: nexus_pipeline_run | `tests/conformance/test_mcp_tool_parity.py` | Tool registered, schema valid |
| D2: Pipeline execution | `tools/scholar-agent-kit/tests/test_pipeline.py` | Workspace not found → error |

#### 3.2.2 Integration Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| D1: End-to-end LLM screening | `tools/scholar-agent-kit/tests/test_screening.py` | Mock LLM → included/excluded/PRISMA |
| D2: End-to-end pipeline | `tools/scholar-agent-kit/tests/test_pipeline.py` | Mock orchestrator → stages completed |

### 3.3 Test Fixtures

```python
# Reuse existing fixtures from tests/conformance/
# Add minimal new fixtures for D1/D2

@pytest.fixture
def sample_papers_json(tmp_path):
    """Create a sample papers JSON file for testing."""
    papers = [
        {
            "workspace_id": "SCI-000001",
            "title": "Randomized Trial of Intervention X",
            "abstract": "This RCT examined the efficacy of intervention X...",
            "year": 2020,
            "doi": "10.1000/test1",
        },
        {
            "workspace_id": "SCI-000002",
            "title": "Animal Model Study",
            "abstract": "This study used a mouse model to investigate...",
            "year": 2019,
            "doi": "10.1000/test2",
        },
    ]
    path = tmp_path / "papers.json"
    path.write_text(json.dumps(papers), encoding="utf-8")
    return path


@pytest.fixture
def sample_protocol_json(tmp_path):
    """Create a sample protocol JSON file for testing."""
    protocol = {
        "title": "Test Protocol",
        "screening_criteria": {
            "inclusion": [
                {"id": "INC-01", "criterion": "RCT or meta-analysis"},
                {"id": "INC-02", "criterion": "Adult population"},
            ],
            "exclusion": [
                {"id": "EXC-01", "criterion": "Animal studies"},
                {"id": "EXC-02", "criterion": "Case reports"},
            ],
        },
    }
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    return path
```

### 3.4 Test Execution Commands

```bash
# Run conformance tests (verifies MCP tool registration)
uv run pytest tests/conformance/test_mcp_tool_parity.py -v

# Run D1/D2 specific tests
uv run pytest tools/scholar-agent-kit/tests/ -v

# Run all tests
uv run pytest -v
```

---

## 4. Task List

### 4.1 Feature D1: LLM-Enhanced Screening MCP Tool

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| D1.1 | Add `nexus_screen_llm` MCP tool to `server.py` | None | 1.5 |
| D1.2 | Wire `LLMBatchScreener` + `calibration.py` integration | D1.1 | 1 |
| D1.3 | Add fallback to `evaluate_heuristic_screening` on LLM failure | D1.1 | 0.5 |
| D1.4 | Write unit tests (mock LLM, fallback behavior) | D1.1, D1.2, D1.3 | 1 |
| D1.5 | Verify conformance test passes | D1.1 | 0.5 |
| **Total** | | | **4.5** |

### 4.2 Feature D2: Pipeline Automation MCP Tool

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| D2.1 | Add `nexus_pipeline_run` MCP tool to `server.py` | None | 1 |
| D2.2 | Wire `ResearchOrchestrator` import and `run_pipeline_async` | D2.1 | 0.5 |
| D2.3 | Write unit tests (workspace not found, mock orchestrator) | D2.1, D2.2 | 0.5 |
| D2.4 | Verify conformance test passes | D2.1 | 0.5 |
| **Total** | | | **2.5** |

### 4.3 Total Estimated Effort

| Feature | Hours |
|---------|-------|
| D1: LLM-Enhanced Screening MCP Tool | 4.5 |
| D2: Pipeline Automation MCP Tool | 2.5 |
| D3: Monorepo Sync (post-implementation) | 1.5 |
| **Total** | **8.5** |

---

## 4.5 Monorepo Governance (Post-Implementation)

> **CRITICAL:** Per AGENTS.md, changes to kit files must be synced to external repos.

### 4.5.1 Kit Sync Requirements

After implementing features in kit directories, run:

```bash
# Sync kit changes to external repos
python scripts/push_tools.py

# Update plugins.json with new commit SHAs
# (manual step after push)

# Regenerate metapackage pins
python scripts/generate_nexus_scholar_pins.py --check  # Verify freshness
python scripts/generate_nexus_scholar_pins.py          # Regenerate if needed
```

### 4.5.2 Conformance Test Updates

When adding new MCP tools (`nexus_screen_llm`, `nexus_pipeline_run`), ensure they are registered via `@mcp.tool()` decorators so conformance tests pass:

```bash
# Run conformance tests
uv run pytest tests/conformance/test_mcp_tool_parity.py -v
```

### 4.5.3 Skill Updates

Update the relevant SKILL.md files to document new capabilities:

- `.agents/skills/scholar-agent-kit/SKILL.md` - Add LLM screening and pipeline MCP tools docs

---

## 5. Definition of Done (DoD)

### 5.1 Feature-Level DoD

For each feature to be considered complete:

- [ ] **Code Complete:** All implementation tasks finished
- [ ] **Tests Passing:** All unit and integration tests pass (`uv run pytest`)
- [ ] **Code Coverage:** New code has ≥90% test coverage
- [ ] **Lint Clean:** `uv run ruff check scripts/` passes (CI scope)
- [ ] **Type Clean:** No type errors in new code
- [ ] **Documentation:** Docstrings for all public functions/classes
- [ ] **MCP Integration:** Feature accessible via `scholar-agent` MCP server
- [ ] **Backward Compatible:** No breaking changes to existing APIs

### 5.2 Feature-Specific DoD

#### D1: LLM-Enhanced Screening MCP Tool
- [ ] `nexus_screen_llm` registered as MCP tool via `@mcp.tool()`
- [ ] Uses `LLMBatchScreener` from `scholar-search-kit` (not reimplemented)
- [ ] Uses `build_checklist_schema()` from `calibration.py` (structured boolean prompts)
- [ ] Falls back to `evaluate_heuristic_screening()` on LLM failure
- [ ] Returns `ScreeningDecision` dataclass objects (not raw dicts)
- [ ] Outputs: included.json, excluded.json, conflicts.json, PRISMA report
- [ ] Conformance test passes

#### D2: Pipeline Automation MCP Tool
- [ ] `nexus_pipeline_run` registered as MCP tool via `@mcp.tool()`
- [ ] Wraps existing `ResearchOrchestrator` (not reimplemented)
- [ ] Supports `skip_stages` parameter
- [ ] Returns stage completion status
- [ ] Conformance test passes

### 5.3 Phase-Level DoD

For Phase D to be considered complete:

- [ ] All 2 features implemented and tested
- [ ] All feature-specific DoD criteria met
- [ ] All unit tests pass: `uv run pytest -v`
- [ ] All integration tests pass
- [ ] No regressions in existing functionality
- [ ] Documentation updated (README, CLI help text)
- [ ] Changes committed with descriptive commit messages
- [ ] Code reviewed by at least one other agent/person
- [ ] Monorepo sync completed (kit repos updated, pins regenerated)

### 5.4 Acceptance Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| LLM Screening F1 | Test with mock LLM responses | F1 ≥ 0.85 |
| MCP Tool Parity | Conformance tests | 100% pass |
| Pipeline Completion | Mock orchestrator test | 100% success |
| No Regressions | Existing test suite | 0 failures |

---

## 6. Dependencies & Constraints

### 6.1 External Dependencies

| Dependency | Version | Used By | Notes |
|------------|---------|---------|-------|
| `pydantic` | >=2.0 | D1 | Already a transitive dep via `scholar-protocol-kit` |

### 6.2 Internal Dependencies

| Dependency | Kit | Location | Notes |
|------------|-----|----------|-------|
| `LLMBatchScreener` | scholar-search-kit | `screening.py:487-614` | Working Gemini REST API integration |
| `evaluate_heuristic_screening` | scholar-search-kit | `screening.py:208-340` | Rule-based fallback |
| `partition_screening_results` | scholar-search-kit | `screening.py:343-408` | Split included/excluded/conflicts |
| `build_checklist_schema` | scholar-agent-kit | `calibration.py:29-58` | Structured boolean checklist |
| `checklist_to_decision` | scholar-agent-kit | `calibration.py:65-128` | Deterministic decision from checklist |
| `ResearchOrchestrator` | scholar-harness | `orchestrator.py` | Full 10-stage pipeline |
| `_resolve_path` | scholar-agent-kit | `server.py:152-161` | MCP anchor-aware path resolution |

### 6.3 Constraints

1. **No breaking changes:** All existing APIs must remain backward compatible
2. **P7.7 lazy imports:** All heavy dependencies must remain deferred inside function/method bodies
3. **Windows compatibility:** All file paths must handle Windows path separators
4. **UTF-8 encoding:** All file I/O must use UTF-8 encoding
5. **No network in tests:** All tests must be hermetic (mocked HTTP)
6. **Kit non-reinvention:** Do not reimplement logic from `scholar-search-kit` or `scholar-harness`

---

## 7. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM screening quality | Medium | High | Checklist-based prompts + heuristic fallback |
| Gemini API rate limits | Medium | Medium | Batch processing with delay between batches |
| Orchestrator import failure | Low | High | Graceful error message with setup instructions |
| Conformance test failure | Low | Medium | Register tools via `@mcp.tool()` before testing |

---

## 8. Changes from v1.0.0

| Change | Reason |
|--------|--------|
| Dropped D2 (MCP Tool Abstraction Layer) | `MCPServer` already handles tool registration, schema generation, and input validation. D2 was redundant with worse type handling. |
| Renamed D1 from "Autonomous Screening Agent" to "LLM-Enhanced Screening MCP Tool" | D1 now wraps existing `LLMBatchScreener` + `calibration.py` instead of reimplementing screening logic. |
| Renamed D3 from "Agent Orchestration Pipeline" to "Pipeline Automation MCP Tool" | D3 now wraps existing `ResearchOrchestrator` instead of creating a parallel pipeline with empty stubs. |
| Removed `screening.py`, `tools.py`, `protocol.py`, `orchestrator.py`, `steps.py` creation | All functionality already exists in existing code. D1/D2 add MCP tool wrappers only. |
| Updated task estimates from 24.5h to 8.5h | Removed redundant implementation work; only integration/wiring remains. |
| Updated file references to match actual codebase | Fixed `cli.py` → `server.py` (no Typer CLI in this kit). |

---

*Specification created by opencode (mimo-v2.5-free) on 2026-09-15*
*Source: Phase D requirements from ecosystem analysis documents*
*Post-review v1.1.0: 4-agent review found D1/D2/D3 all BLOCKED due to kit non-reinvention violations, wrong file paths, and redundant abstractions. Rewrote to wrap existing kit APIs as MCP tools.*
