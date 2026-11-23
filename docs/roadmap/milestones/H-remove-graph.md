# H-remove-graph Remove the citation graph

Branch: `dev/h/remove-graph` (from `origin/main` `9af17212`) · Lane: **RELEASE** (packaging, the base dependencies, the MCP surface and the public commands change) · Status: **BUILT, review pending** (not pushed)

The researcher's decision of 2026-11-23, in the coordinator session ("Yes, remove graph"), after the project review of that day (item 10: three base dependencies, `networkx`, `pyvis` and `scipy`, served only the parked graph code; cited in `docs/roadmap/milestones/M13-installers.md` §2.4). Delete `scholar_graph`, its tests and everything that only exists to call it. PDF extraction, the capability adapter and `claims` stay.

## Restore

Everything removed here is in `origin/main` at **`9af17212`** (2026-11-23):

```powershell
git checkout 9af17212 -- src/scholar_graph tests/kits/graph src/scholar_harness/pipeline/graph.py tests/unit/test_graph_stage.py tests/test_mcp_narrative.py .agents/skills/scholar-graph-kit docs/kits/graph
```

Then re-add `networkx`, `pyvis` and `scipy` to the base dependencies, the `scholar-graph` console script, the package entry and the skill's force-include in `pyproject.toml`; the two MCP tools in `scholar_agent/server.py`; Stage 8 in `pipeline/coordinator.py`; the `graph` and `graph_narrative` console actions; the `/api/v1/assets/graph` route; and run `uv lock` and `scripts/sync_skills_bundle.py`.

## What was deleted

`git diff --shortstat 9af17212` on the final head: see "Evidence". By part:

| What | Files | Lines |
| :-- | --: | --: |
| `src/scholar_graph` (builder, CLI, scientometrics, visualizer, config, models) | 7 | 1,241 |
| `tests/kits/graph` | 6 | 1,130 |
| `src/scholar_harness/pipeline/graph.py` (the pipeline's Stage 8) | 1 | 128 |
| `tests/unit/test_graph_stage.py` (754), `tests/test_mcp_narrative.py` (131) | 2 | 885 |
| Skill `scholar-graph-kit` and its bundled copy | 2 | 296 |
| `docs/kits/graph/` | 2 | 148 |

Changed, not deleted: the MCP server (−245 lines: the two tools, their imports and the parked list), the pipeline coordinator (Stage 8, its skip and abort shapes), the console (two actions, one route), the command-line app (the "Citation Graph Nodes" status row and the "Graph Nodes" run-summary line), `doctor`'s kit list, the pipeline allowlist, the skill vocabulary and its transform script, the orchestrator's graph re-export, `pyproject.toml`, `uv.lock` (−218 lines), the plugin manifest, the gate manifest (the `graph` area), the MCP bundle description (`scripts/build_mcpb.py`, which still called rag, verify and graph "parked"), three skills (agent, search, workspace-manager) and 24 test files repaired.

**Tests.** Collected before (`9af17212`): **5,405**. The deleted files held 101 tests; the repaired files lost 3 more whose whole subject was the graph tool (`tests/mcp/test_mcp_tools_graph.py`: real HTTP client, results dict, no DOIs) and the two `/assets/graph` route tests, and one parked-label test (`scholar_graph.cli`). Added: the `/assets/graph` route answers 404; a pipeline node naming `scholar-graph` is refused. Mixed files kept every assertion over kept code; the removed stage, keys, actions and tools gained negative checks (Definition of done, item 3).

## What a user loses

- **Command:** `scholar-graph` (`build`, `pagerank`).
- **MCP tools (24 to 22):** `nexus_graph_build` and `nexus_graph_narrative`. An MCP client that calls either now gets an unknown-tool error.
- **The pipeline after a collected screening** (`nexus-scholar run`, `nexus_pipeline_run`): extraction only. Its result no longer carries the `graph_nodes` stage, no `literature/knowledge_graph.json` or `.html` is written, and its summary no longer prints "Graph Nodes". `nexus-scholar status` no longer prints the "Citation Graph Nodes" row (the status JSON keeps its `graph_nodes` key, read from an existing `knowledge_graph.json`, as `vector_chunks` stayed after H-remove-rag-verify).
- **Console:** the `graph` and `graph_narrative` actions (12 to 10) and the `/api/v1/assets/graph` route (now 404). A stored pipeline spec with a `scholar-graph` node is refused at validation (`COMMAND_NOT_ALLOWED`). The web app used none of them.
- **Install:** `networkx`, `pyvis` and `scipy` leave the base dependencies; with `pyvis` go the 15 packages only it brought (`ipython`, `jedi`, `parso`, `traitlets`, `prompt-toolkit`, `jsonpickle` and their dependencies). `numpy` was only there through `scipy` and goes too. They still arrive with an extra: `networkx` and `numpy` with `pdf` (PyMuPDF 2.1 requires `networkx`; `numpy` through PyMuPDF's layout packages), `scipy` and `numpy` with `extract` (Docling).
- **Skill:** `scholar-graph-kit` (10 mirrored skills to 9; 11 shipped to 10).

## Measured effect on a fresh install

The wheel built without the UI export (`NEXUS_WHEEL_ALLOW_NO_UI=1`), installed offline from the uv cache into a fresh Python 3.12 venv with no extra (the base install), on this PC. Timings are three runs each, warm disk cache.

| | Before (`9af17212`) | After (this branch) |
| :-- | --: | --: |
| Wheel | 1,456 KB, 313 files | see "Evidence" |
| Environment on disk | 267 MB, 12,884 files | see "Evidence" |
| Packages installed | 82 | see "Evidence" |
| `networkx` / `pyvis` / `scipy` / `numpy` / `jedi` / `IPython` importable | all yes | see "Evidence" |
| MCP tools (`scholar-agent --help`) | 24 | 22 |
| `import scholar_harness.cli` | 2.77, 2.38, 2.14 s | see "Evidence" |
| `nexus-scholar --help` | 2.51, 3.58, 3.20 s | see "Evidence" |

`uv.lock`: 16 packages removed (asttokens, executing, ipython, ipython-pygments-lexers, jedi, jsonpickle, matplotlib-inline, parso, pexpect, prompt-toolkit, ptyprocess, pure-eval, pyvis, stack-data, traitlets, wcwidth). `networkx`, `scipy` and `numpy` stay in the lock, reached only through the `pdf` and `extract` extras (`uv tree --invert`).

**For the M13 bundle** (base + `ai` + `pdf`, `docs/roadmap/milestones/M13-installers.md` §8): `scipy`, `pyvis` and the `jedi`/`IPython` family leave it (`jedi` alone was 5,536 of its 7,594 files); `networkx` and `numpy` stay, because PyMuPDF 2.1 brings them. The bundle was not rebuilt here.

## What must stay true, and how it was checked

| Must stay true | Evidence |
| :-- | :-- |
| No product path needs the graph or `networkx` | searched `src/` and `apps/research-ui/{app,components,lib}` before deleting: only `scholar_agent/server.py` and `pipeline/graph.py` imported `scholar_graph`; nothing in `src/` imports `networkx`, `pyvis`, `scipy` or `numpy`. Citation chasing, deduplication, the discovery report and charting import none of them (their tests are in the full run) |
| The wheel builds and both entry points answer `--help` on the base install | fresh-environment install ("Evidence") |
| The MCP server keeps the other 22 tools | `tests/conformance/test_count_freshness.py` pins the exact 22-name set; `test_mcp_tool_parity.py`; the E1/E2 count tests, which also read the documented counts |
| Old workspaces still read | `get_status`, `sync_state`, the handoff phases and the corpus counts still read or exclude an existing `knowledge_graph.json`; nothing writes one |
| Contract v1 | `generate_contract_baseline.py --check`: current, no drift; no locked file changed |

## Definition of done

- [x] 1. `src/scholar_graph` and `tests/kits/graph` deleted, and every stage, MCP tool, command, action, route, skill and dependency that existed only for them (tables above).
- [x] 2. No reference remains in `src/`, `tests/`, `scripts/`, `pyproject.toml`, `.agents/`, CI or the gate manifest, except a line that records the removal, the read-only handling of old workspaces' `knowledge_graph.json`, or a test file name (below).
- [x] 3. Removed behaviour is absent or refused, with tests: no `graph_nodes` stage and no graph files after a collected screening (`test_after_collect_runs_extraction_only`, the coordinator tests); the coordinator no longer imports `run_graph` (`test_coordinator`); `/api/v1/assets/graph` answers 404 (`test_assets_graph_route_is_gone`); the `graph` and `graph_narrative` actions are absent (`test_agent_actions_table`); a `scholar-graph` pipeline node is refused (`test_pipeline_commands_outside_the_allowlist_are_invalid`); the two tools are absent from the exact set (`test_count_freshness`); the summaries print no "Graph Nodes" (`test_cli_pipeline_summary`).
- [x] 4. Packaging: `pyproject.toml`, `uv.lock` (`uv lock --check`), the plugin manifest, the skills bundle, skill portability.
- [x] 5. Gate manifest: the `graph` area removed, `tests/test_mcp_narrative.py` out of the agent-mcp checkpoint; `select_test_gate.py --check` passes.
- [x] 6. Documents corrected where they would now be false: `AGENTS.md`, `README.md`, `docs/kits_surface_matrix.md`, `docs/nexus_scholar_user_guide.md`, `docs/data-flow.md`, `docs/architecture/wp01/evidence-boundaries.md` (its count is test-read), the agent, search and workspace-manager skills.
- [ ] 7. Gate on the final head ("Evidence").
- [ ] 8. Independent review.

## Left as it is, on purpose

- **`tests/mcp/test_mcp_tools_graph.py` keeps its name**: its remaining tests cover `nexus_extract_pdf`, `nexus_screen`, path resolution and protocol validation, and the surface matrix and assessments cite the file by name.
- **Old workspaces' graph files are still read, never written:** `get_status` and `sync_state` count nodes from an existing `knowledge_graph.json`; `handoff.py` keeps its `GRAPH` phase (as it kept `SYNTHESIS` and `CRITIQUE`); `workspace/counts.py` still excludes `graph.json` and `knowledge_graph.json` from corpus counts.
- **`lib/`** (vis.js and tom-select that pyvis wrote into the working directory) is gitignored and untracked; nothing serves it. It was not deleted from this PC.
- **`docs/architecture/console/SPECS.md`** still lists the `graph` action and the `/assets/graph` route, as it still lists the rag and verify actions: a design record of 2026-09, not a description of today.
- **History documents** (`docs/roadmap/`, `docs/assessment/`, `docs/decisions.md`, `docs/ux/`, `specs/`) and the numbered findings in the surface matrix that name the graph tool still describe it as it was.

## Evidence

All on this PC (Windows 11, the project venv on Python 3.14.7, synced `--extra dev --extra pdf`). No network request, no AI spend.

| Check | Head | Result |
| :-- | :-- | :-- |
| Full Python suite | | |
| Targeted run of the affected areas (authority, conformance, console, agent kit, MCP, pipeline, unit, CLI, handoff, parked labels, packaging tests), `-n 4` | working tree before the docs | 3,130 passed, 7 skipped, 1 failed: the documented tool count (24) in the surface matrix, fixed with the docs; the E2 and count tests then 47 passed |
| `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | | pass |
| `generate_contract_baseline.py --check` | | "Contract baseline current" |
| `generate_contract_schemas.py`, `generate_two_study_contract_fixture.py`, `generate_protocol_schema.py` (`--check`) | | pass |
| `sync_skills_bundle.py --check`, `validate_manifest.py`, `select_test_gate.py --check` (11 tasks, 23 areas), `check_workflows.py`, `uv lock --check` | | pass |
| `uv build --wheel` and the fresh-environment install | | |
| `git diff --check` | | |

**Not verified.**
- CI (Ubuntu, Python 3.12, cross-OS): not run, nothing pushed.
- The wheel with the UI export inside it.
- The MCP server driven by a real MCP client; the 22-tool surface is checked through the tool manager and `--help`.
- Any real workspace: none was opened.
