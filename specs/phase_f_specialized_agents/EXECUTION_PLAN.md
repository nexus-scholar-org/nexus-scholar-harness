# Phase F Execution Plan

## Task 1: Design Data Contracts for F1 and F2 [INDEPENDENT]
**Description:** Define the input/output JSON schemas and Pydantic models that both `nexus_critique_methodology` and `nexus_graph_narrative` will consume and produce. This is a pure-spec task with no code coupling.
**Files to Touch:** `specs/phase_f_specialized_agents/schemas.py` (new), `specs/phase_f_specialized_agents/README.md` (update)

### Execution Checklist
- [ ] Define `CritiqueRequest` model: `workspace_dir: str`, `protocol_path: str | None`, `rq_id: str | None`
- [ ] Define `CritiqueResult` model: `overall_risk: str`, `domain_ratings: dict`, `per_study: list`, `summary_md: str`
- [ ] Define `NarrativeRequest` model: `workspace_dir: str`, `graph_json_path: str`, `consensus_path: str | None`
- [ ] Define `NarrativeResult` model: `hub_summary: str`, `community_summaries: list[dict]`, `narrative_md: str`
- [ ] Write docstrings and field descriptions matching existing kit conventions (dataclass-style, not Pydantic BaseModel for MCP return dicts)
- [ ] Update README §2.1 and §2.2 with formal schema references

### Testing Strategy
- No runtime tests needed; schemas are validated by import and by downstream task tests.

### Definition of Done (DoD)
- Both schema definitions exist, importable without error, and are referenced in the spec README.

---

## Task 2: Implement `nexus_critique_methodology` MCP Tool [DEPENDS ON Task 1]
**Description:** Add the Methodology Critique Agent tool to `scholar-agent-kit`'s MCP server. Wraps `scholar-verify-kit` risk-of-bias and protocol-kit criteria into a single MCP call that evaluates extracted studies against the protocol.
**Files to Touch:** `tools/scholar-agent-kit/src/scholar_agent/server.py`

### Execution Checklist
- [ ] Add imports: `from scholar_verify import risk_of_bias, cli as verify_cli` (already present), `from scholar_protocol.models import ResearchProtocol` (already present)
- [ ] Add helper `_load_records(workspace_dir: Path) -> list[dict]` — loads `literature/extraction/merged/records.json` (mirrors `verify_cli._merged_records`)
- [ ] Add helper `_load_manifest(workspace_dir: Path) -> list[dict]` — loads `phase4/_manifest.json` (mirrors `verify_cli._manifest`)
- [ ] Implement `@mcp.tool() def nexus_critique_methodology(workspace_dir: str, protocol_path: str | None = None, rq_id: str | None = None) -> str`:
  - Resolve paths via `_resolve_path`
  - Load `protocol.json` if `protocol_path` provided; extract RQs
  - Load records via `_load_records`; load manifest via `_load_manifest`
  - Call `risk_of_bias.run(records, manifest)` to get per-study RoB
  - Compute aggregate stats: count H/?/L per domain, overall distribution
  - Render `methodological_critique.md` with domain-level summary and per-study table
  - Write `<workspace_dir>/phase4/methodological_critique.md`
  - Return JSON `{status, overall_risk, domain_ratings, per_study_count, output_path}`
- [ ] Update `main()` epilog to list `nexus_critique_methodology`
- [ ] Handle errors with `try/except` returning `json.dumps({"status": "ERROR", "error": str(e)})`

### Testing Strategy
- **Unit test:** `tests/test_mcp_critique.py` (new) — call `nexus_critique_methodology` with a `tmp_path` workspace containing fixture `records.json`, `_manifest.json`, and `protocol.json`. Assert JSON return has `status == "SUCCESS"`, file `methodological_critique.md` is created, and domain ratings are present.
- **Conformance:** existing `tests/conformance/test_mcp_tool_parity.py` will catch if the tool is not registered (if an action references it); add a new `Action` entry in `actions.py` (see Task 5).

### Definition of Done (DoD)
- `nexus_critique_methodology` is callable via MCP, returns valid JSON, writes `methodological_critique.md`, and passes unit test.

---

## Task 3: Implement `nexus_graph_narrative` MCP Tool [DEPENDS ON Task 1]
**Description:** Add the Visual Synthesis Agent tool to `scholar-agent-kit`'s MCP server. Reads graph stats (PageRank hubs, community structure) and generates a narrative summary.
**Files to Touch:** `tools/scholar-agent-kit/src/scholar_agent/server.py`

### Execution Checklist
- [ ] Add import: `from scholar_graph.builder import CitationGraphBuilder` (already present)
- [ ] Add helper `_load_graph_json(graph_path: Path) -> dict` — reads and returns parsed graph JSON
- [ ] Add helper `_identify_hubs(graph_data: dict, top_n: int = 10) -> list[dict]` — sorts nodes by `pagerank` score, returns top-N with title, doi, score
- [ ] Add helper `_summarize_communities(graph_data: dict) -> list[dict]` — groups nodes by `group` field (Louvain community ID), returns per-community node count, top-3 nodes by PageRank, and a descriptive label
- [ ] Implement `@mcp.tool() def nexus_graph_narrative(workspace_dir: str, graph_json_path: str, top_hubs: int = 10) -> str`:
  - Resolve paths
  - Load graph JSON via `_load_graph_json`
  - Extract hubs via `_identify_hubs`
  - Extract communities via `_summarize_communities`
  - Compose `visual_synthesis.md` narrative with sections: "Hub Papers", "Thematic Communities", "Network Overview"
  - Write `<workspace_dir>/synthesis/visual_synthesis.md`
  - Return JSON `{status, n_hubs, n_communities, output_path}`
- [ ] Update `main()` epilog to list `nexus_graph_narrative`
- [ ] Handle errors with `try/except` returning JSON error

### Testing Strategy
- **Unit test:** `tests/test_mcp_narrative.py` (new) — create a fixture `graph.json` with 5 nodes, 4 edges, `pagerank` dict, and `group` fields. Call `nexus_graph_narrative` with `tmp_path`. Assert JSON has `status == "SUCCESS"`, `visual_synthesis.md` is created, hub count and community count are correct.
- **Conformance:** same as Task 2.

### Definition of Done (DoD)
- `nexus_graph_narrative` is callable via MCP, produces `visual_synthesis.md`, and passes unit test.

---

## Task 4: Register New MCP Tools in Conformance & Actions [DEPENDS ON Tasks 2, 3]
**Description:** Update the actions table and conformance tests so the two new MCP tools are recognized as part of the official surface. This prevents silent drift.
**Files to Touch:** `src/scholar_harness/console/runtimes/actions.py`, `tests/conformance/test_mcp_tool_parity.py`

### Execution Checklist
- [ ] In `actions.py`, add two new `Action` entries:
  - `Action("critique_methodology", "Methodology critique", "uv run scholar-verify risk-of-bias -w {ws}", "nexus_critique_methodology", True)`
  - `Action("graph_narrative", "Graph narrative synthesis", "uv run scholar-graph pagerank {ws}/literature/knowledge_graph.json", "nexus_graph_narrative", False)`
- [ ] Verify `test_action_mcp_tools_are_registered` passes (the new `mcp_tool` names must be in `REGISTERED_TOOLS`)
- [ ] Verify `test_help_lists_all_registered_tools` passes (new tools must appear in `--help` epilog)

### Testing Strategy
- Run existing conformance tests: `uv run pytest tests/conformance/test_mcp_tool_parity.py -v`
- No new test files; the existing suite covers registration drift.

### Definition of Done (DoD)
- Both conformance tests pass with zero failures.

---

## Task 5: Design Handoff Protocol State Machine [DEPENDS ON Task 1]
**Description:** Define the agent phase sequence, state-file contracts, and transition logic for F3's supervisor. This is a design-only task.
**Files to Touch:** `specs/phase_f_specialized_agents/handoff_spec.md` (new)

### Execution Checklist
- [ ] Define phase sequence: `inception` → `screening` → `extraction` → `graph` → `synthesis` → `critique` → `complete`
- [ ] Define state-file trigger conventions:
  - `intent.json` → inception complete
  - `protocol.json` → protocol finalized
  - `literature/included.json` → screening complete
  - `literature/extraction/merged/records.json` → extraction complete
  - `literature/knowledge_graph.json` → graph complete
  - `synthesis/consensus.json` → synthesis complete
  - `phase4/methodological_critique.md` → critique complete
- [ ] Define the `handoff_state.json` schema: `{current_phase, completed_phases: list, workspace_dir, timestamp}`
- [ ] Define supervisor loop behavior: poll for trigger files, advance phase, emit audit event

### Testing Strategy
- No runtime tests; pure specification.

### Definition of Done (DoD)
- `handoff_spec.md` exists with complete state machine, file contracts, and transition table.

---

## Task 6: Implement Handoff State File Schema [DEPENDS ON Task 5]
**Description:** Create the dataclass and serialization logic for `handoff_state.json`, the persistent state file that the supervisor reads and writes.
**Files to Touch:** `src/scholar_harness/handoff.py` (new)

### Execution Checklist
- [ ] Define `HandoffPhase` enum: `INCEPTION`, `SCREENING`, `EXTRACTION`, `GRAPH`, `SYNTHESIS`, `CRITIQUE`, `COMPLETE`
- [ ] Define `HandoffState` dataclass: `current_phase: HandoffPhase`, `completed_phases: list[HandoffPhase]`, `workspace_dir: str`, `updated_at: str`
- [ ] Implement `load_handoff_state(workspace_dir: Path) -> HandoffState` — reads `handoff_state.json` or returns default initial state
- [ ] Implement `save_handoff_state(state: HandoffState, workspace_dir: Path) -> Path` — atomic write to `handoff_state.json`
- [ ] Implement `advance_phase(state: HandoffState, next_phase: HandoffPhase) -> HandoffState` — moves current to completed, sets new current
- [ ] Ensure all methods are hermetic (no network, no LLM calls)

### Testing Strategy
- **Unit test:** `tests/test_handoff.py` (new) — test `load_handoff_state` returns default when no file exists, `save_handoff_state` creates file, `advance_phase` transitions correctly, round-trip persistence works.
- Use `tmp_path` fixture; no mocks needed.

### Definition of Done (DoD)
- `handoff.py` exists, all unit tests pass, state file round-trips correctly.

---

## Task 7: Implement Supervisor Phase Detection [DEPENDS ON Task 6]
**Description:** Implement the core detection logic that inspects the workspace filesystem to determine which phase has completed, so the supervisor can advance the state machine.
**Files to Touch:** `src/scholar_harness/handoff.py` (extend)

### Execution Checklist
- [ ] Define `PHASE_TRIGGERS: dict[HandoffPhase, list[Path]]` — maps each phase to the files whose existence signals completion
- [ ] Implement `detect_completed_phases(workspace_dir: Path) -> set[HandoffPhase]` — iterates `PHASE_TRIGGERS`, returns phases whose trigger files all exist
- [ ] Implement `next_actionable_phase(state: HandoffState, completed: set[HandoffPhase]) -> HandoffPhase | None` — returns the first phase in the sequence whose prerequisites are met but which is not yet in `completed_phases`
- [ ] Handle edge cases: missing workspace dir returns empty set, malformed JSON returns current state unchanged

### Testing Strategy
- **Unit test:** extend `tests/test_handoff.py` — create fixture directories with trigger files, verify `detect_completed_phases` returns correct set, verify `next_actionable_phase` returns correct next phase.
- Test edge cases: empty workspace, partial triggers, all-complete state.

### Definition of Done (DoD)
- Detection logic is hermetic, handles all phase transitions, and passes all unit tests.

---

## Task 8: Implement Supervisor Loop CLI [DEPENDS ON Task 7]
**Description:** Create the supervisor entry point as a CLI subcommand (`scholar-harness supervise`) that runs the detection-advance loop once or in watch mode.
**Files to Touch:** `src/scholar_harness/cli.py`, `src/scholar_harness/handoff.py` (extend)

### Execution Checklist
- [ ] Add `supervise` subcommand to `cli.py` via `@app.command("supervise")`:
  - Arguments: `--workspace` (Path), `--once` (bool, default True), `--interval` (int seconds, default 60)
  - If `--once`: run one detection pass, print result, exit
  - If not `--once`: loop with `time.sleep(interval)`, printing each advance
- [ ] Implement `run_supervisor_once(workspace_dir: Path) -> dict` in `handoff.py`:
  - Load state → detect completed → compute next actionable → advance if possible → save state → log audit event → return summary dict
- [ ] Log each phase advance to `audit/journal.jsonl` via existing `_log_audit_event` pattern
- [ ] Print human-readable status via `rich` console (matching existing CLI style)

### Testing Strategy
- **Unit test:** `tests/test_supervisor.py` (new) — test `run_supervisor_once` with fixture workspace at various stages; mock file existence; assert correct phase transitions and audit events written.
- **Integration test:** `tests/test_supervisor_cli.py` (new) — invoke `scholar-harness supervise --workspace <tmp> --once` via `typer.testing.CliRunner`, assert exit code 0 and output contains phase name.

### Definition of Done (DoD)
- `uv run scholar-harness supervise -w <ws> --once` runs without error, advances phase if triggers are present, and exits cleanly.

---

## Task 9: Wire Supervisor into Existing Pipeline [DEPENDS ON Task 8]
**Description:** Integrate the supervisor so that `ResearchOrchestrator.run_pipeline` calls the supervisor after each stage, ensuring phase transitions are recorded automatically.
**Files to Touch:** `src/scholar_harness/orchestrator.py`

### Execution Checklist
- [ ] Add import: `from scholar_harness.handoff import run_supervisor_once`
- [ ] At the end of `run_pipeline_async` (after Stage 10 audit logging), call `run_supervisor_once(self.workspace_dir)` and merge the result into `results["stages"]["handoff"]`
- [ ] Ensure the supervisor call is best-effort: wrap in `try/except` so pipeline failure does not cascade
- [ ] Do NOT block pipeline on supervisor failure; log warning and continue

### Testing Strategy
- **Unit test:** extend `tests/test_pipeline_executor.py` or `tests/test_orchestrator_fidelity.py` — mock `run_supervisor_once`, assert it is called after pipeline completes.
- Verify that supervisor failure does not raise in the orchestrator.

### Definition of Done (DoD)
- Pipeline runs end-to-end with supervisor invoked; supervisor errors are caught and logged; existing pipeline tests still pass.

---

## Task 10: End-to-End Smoke Tests for F1 and F2 [DEPENDS ON Tasks 2, 3]
**Description:** Create integration-level smoke tests that exercise the full MCP tool path from Python (not stdio) with realistic fixture data, validating that F1 and F2 produce correct output files.
**Files to Touch:** `tests/test_phase_f_e2e.py` (new)

### Execution Checklist
- [ ] Create fixture workspace under `tests/fixtures/phase_f/` with:
  - `protocol.json` (minimal valid protocol)
  - `literature/extraction/merged/records.json` (2-3 mock records with `segmentation` fields)
  - `phase4/_manifest.json` (matching workspace_ids)
  - `literature/knowledge_graph.json` (5 nodes, edges, pagerank, groups)
- [ ] Test F1: call `nexus_critique_methodology(workspace_dir=fixture_ws)` → assert `phase4/methodological_critique.md` exists, content contains "Risk of Bias" heading, JSON status is SUCCESS
- [ ] Test F2: call `nexus_graph_narrative(workspace_dir=fixture_ws, graph_json_path=fixture_ws / "literature/knowledge_graph.json")` → assert `synthesis/visual_synthesis.md` exists, content contains "Hub Papers" and "Thematic Communities"
- [ ] Test F3: create workspace at each phase trigger stage, call `run_supervisor_once`, assert phase advances correctly through full sequence

### Testing Strategy
- All tests use `tmp_path` with copied fixtures; no network, no LLM mocks needed (all operations are deterministic/file-based).
- Mark tests with `@pytest.mark.slow` if fixture setup is heavy.

### Definition of Done (DoD)
- All three E2E smoke tests pass; output files are validated for structure and content.

---

## Task 11: Update Skill Documentation [DEPENDS ON Tasks 2, 3, 8]
**Description:** Update the `scholar-agent-kit` SKILL.md and AGENTS.md to document the two new MCP tools and the supervisor CLI.
**Files to Touch:** `.agents/skills/scholar-agent-kit/SKILL.md`, `AGENTS.md`

### Execution Checklist
- [ ] In `SKILL.md`, add entries for `nexus_critique_methodology` and `nexus_graph_narrative` to the "Exposed MCP Tools" table with descriptions and usage examples
- [ ] In `SKILL.md`, update tool count from 19 to 21
- [ ] In `AGENTS.md`, add a note under "Multi-step research" about `scholar-harness supervise` for automated phase transitions
- [ ] Verify `test_help_lists_all_registered_tools` still passes (epilog already updated in Tasks 2/3)

### Testing Strategy
- Documentation-only; verified by conformance tests.

### Definition of Done (DoD)
- SKILL.md lists all 21 tools; AGENTS.md references the supervisor; conformance tests pass.

---

## Execution Order Summary

```
Task 1 (schemas) ─────────┬──> Task 2 (F1 tool) ──┬──> Task 4 (conformance) ──> Task 11 (docs)
                          │                        │
                          └──> Task 3 (F2 tool) ───┘
                          │
                          └──> Task 5 (handoff spec) ──> Task 6 (state schema) ──> Task 7 (detection) ──> Task 8 (supervisor CLI) ──> Task 9 (wire into orchestrator)

Tasks 2, 3, 5 can run in parallel after Task 1.
Tasks 2+3 → Task 4 (serial dependency on both tools existing).
Tasks 5→6→7→8→9 form a strict chain.
Task 10 runs after Tasks 2, 3, 8 are complete.
Task 11 runs last (documentation).
```

**Parallelizable groups:**
- **Group A (after Task 1):** Tasks 2, 3, 5 — entirely independent
- **Group B (after Group A):** Task 4 (needs both 2+3), Task 6 (needs 5)
- **Group C:** Task 7 (needs 6), and Task 10 can start as soon as its dependencies (2, 3, 8) are done
- **Final:** Task 11 (all code complete)
