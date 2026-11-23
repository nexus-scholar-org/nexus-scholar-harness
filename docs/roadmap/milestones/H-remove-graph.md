# H-remove-graph Remove the citation graph

Branch: `dev/h/remove-graph` (from `origin/main` `9af17212`; `origin/main` `cc0e8fa1`, the 1.1.0b7 release, merged in on 2026-11-24 as `a269cda1`) · Lane: **RELEASE** (packaging, the base dependencies, the MCP surface and the public commands change) · Status: **READY FOR PR** (review round 2 APPROVE; not pushed)

The researcher's decision of 2026-11-23, in the coordinator session ("Yes, remove graph"), after the project review of that day (item 10: three base dependencies, `networkx`, `pyvis` and `scipy`, served only the parked graph code; cited in `docs/roadmap/milestones/M13-installers.md` §2.4). The researcher confirmed finishing it on 2026-11-24 ("Yes, finish it"), after 1.1.0b7 was released, so the removal ships in the release after 1.1.0b7. Delete `scholar_graph`, its tests and everything that only exists to call it. PDF extraction, the capability adapter and `claims` stay.

## Restore

Everything removed here is in `origin/main` at **`9af17212`** (2026-11-23):

```powershell
git checkout 9af17212 -- src/scholar_graph tests/kits/graph src/scholar_harness/pipeline/graph.py tests/unit/test_graph_stage.py tests/test_mcp_narrative.py .agents/skills/scholar-graph-kit docs/kits/graph
```

Then re-add `networkx`, `pyvis` and `scipy` to the base dependencies, the `scholar-graph` console script, the package entry and the skill's force-include in `pyproject.toml`; the two MCP tools in `scholar_agent/server.py`; Stage 8 in `pipeline/coordinator.py`; the `graph` and `graph_narrative` console actions; the `/api/v1/assets/graph` route; and run `uv lock` and `scripts/sync_skills_bundle.py`.

## What was deleted

`git diff --shortstat 9af17212..ee412b58`: 74 files, +371 / −4,842 lines (the deletions, the repairs, this record and the decisions entry). By part:

| What | Files | Lines |
| :-- | --: | --: |
| `src/scholar_graph` (builder, CLI, scientometrics, visualizer, config, models) | 7 | 1,241 |
| `tests/kits/graph` | 6 | 1,130 |
| `src/scholar_harness/pipeline/graph.py` (the pipeline's Stage 8) | 1 | 128 |
| `tests/unit/test_graph_stage.py` (754), `tests/test_mcp_narrative.py` (131) | 2 | 885 |
| Skill `scholar-graph-kit` and its bundled copy | 2 | 296 |
| `docs/kits/graph/` | 2 | 148 |

Changed, not deleted: the MCP server (−245 lines: the two tools, their imports and the parked list), the pipeline coordinator (Stage 8, its skip and abort shapes, the stage-number comments, and two journal texts: the `PIPELINE_RUN_COMPLETED` row's `outputs` now names the `extracted/` folder instead of `literature/knowledge_graph.html`, and the stale-generation pause says "before the extraction stage" instead of "before stages 5-9"), the console (two actions, one route), the command-line app (the "Citation Graph Nodes" status row and the "Graph Nodes" run-summary line), `doctor`'s kit list, the pipeline allowlist, the skill vocabulary and its transform script, the orchestrator's graph re-export, `pyproject.toml`, `uv.lock` (−218 lines), the plugin manifest, the gate manifest (the `graph` area), the MCP bundle description (`scripts/build_mcpb.py`, which still called rag, verify and graph "parked"), three skills (agent, search, workspace-manager; the workspace layout no longer shows `graph.html`/`graph.json`), and 22 test files changed beside the 8 deleted.

**Tests.** Collected before (`9af17212`): **5,405**. The deleted files held 101 tests; the repaired files lost 3 more whose whole subject was the graph tool (`tests/mcp/test_mcp_tools_graph.py`: real HTTP client, results dict, no DOIs) and the two `/assets/graph` route tests, and one parked-label test (`scholar_graph.cli`); and the parametrized cases whose parameter left: the `graph` and `graph_narrative` cases of `test_actions_cli_parity.py`, `graph_build` × 5 path escapes in `test_mcp_path_containment.py`, and the `scholar-graph-kit` cases of the skill-portability tests. Added: the `/assets/graph` route answers 404; a pipeline node naming `scholar-graph` is refused; `networkx`, `pyvis` and `scipy` stay out of the base dependencies (`tests/test_dependency_bounds.py`). Mixed files kept every assertion over kept code; the removed stage, keys, actions and tools gained negative checks (Definition of done, item 3).

## What a user loses

- **Command:** `scholar-graph` (`build`, `pagerank`).
- **MCP tools (24 to 22):** `nexus_graph_build` and `nexus_graph_narrative`. An MCP client that calls either now gets an unknown-tool error.
- **The pipeline after a collected screening** (`nexus-scholar run`, `nexus_pipeline_run`): extraction only. Its result no longer carries the `graph_nodes` stage, no `literature/knowledge_graph.json` or `.html` is written, and its summary no longer prints "Graph Nodes". `nexus-scholar status` no longer prints the "Citation Graph Nodes" row (the status JSON keeps its `graph_nodes` key, read from an existing `knowledge_graph.json`, as `vector_chunks` stayed after H-remove-rag-verify).
- **Console:** the `graph` and `graph_narrative` actions (12 to 10) and the `/api/v1/assets/graph` route (now 404). A stored pipeline spec with a `scholar-graph` node is refused at validation (`COMMAND_NOT_ALLOWED`). The web app used none of them.
- **Install:** `networkx`, `pyvis` and `scipy` leave the base dependencies; with `pyvis` go the packages only it brought (`ipython`, `jedi`, `parso`, `traitlets`, `prompt-toolkit`, `jsonpickle`, `jinja2`, `markupsafe`, `psutil` and their dependencies). `numpy` was only there through `scipy` and goes too. A base install loses 20 packages in all on Windows (measured below); 22 on Linux and macOS, where `pexpect` and `ptyprocess` also go. They still arrive with an extra: `networkx` and `numpy` with `pdf` (PyMuPDF 2.1 requires `networkx`; `numpy` through PyMuPDF's layout packages), and `networkx`, `scipy` and `numpy` with `extract` (Docling, `networkx` through torch).
- **Skill:** `scholar-graph-kit` (10 mirrored skills to 9; 11 shipped to 10).

## Release: unreleased, after 1.1.0b7

1.1.0b7 was tagged (`v1.1.0b7` on `cc0e8fa1`) before this branch was finished, so 1.1.0b7 still ships the graph and its release note (`docs/releases/1.1.0b7.md`) is not edited. The repository keeps one note per release and no running "unreleased" file; the lines for the next release's note are decision item 3 in `docs/decisions.md`. For a 1.1.0b7 user who upgrades:

- `scholar-graph` is gone ("command not found").
- The MCP server registers **22** tools, not 24: `nexus_graph_build` and `nexus_graph_narrative` answer "unknown tool".
- `networkx`, `pyvis` and `scipy` are no longer installed with the base package (with them go `numpy`, `ipython`, `jedi` and 14 more; 20 packages in all on Windows, 22 on Linux and macOS). `networkx` and `numpy` still come with `[pdf]`; `networkx`, `scipy` and `numpy` with `[extract]`.
- The pipeline after a collected screening runs extraction only; the console's `graph`/`graph_narrative` actions and `/api/v1/assets/graph` are gone; the `scholar-graph-kit` skill is no longer bundled.

## Measured effect on a fresh install

The wheel built without the UI export (`NEXUS_WHEEL_ALLOW_NO_UI=1`), installed offline from the uv cache into a fresh Python 3.12 venv with no extra (the base install), on this PC. Timings are three runs each, warm disk cache. "After" is `ee412b58` (1.1.0b6 number); the merged head `a269cda1` (1.1.0b7 number) measured the same wheel size and file count, environment, package list (identical), import checks and 22 tools; its timings (import 2.94, 2.81, 2.77 s; `--help` 4.01, 4.82, 4.76 s) were taken while a review's test run shared the machine. "Before" is `9af17212`, whose dependencies are 1.1.0b7's (the release changed no dependency).

| | Before (`9af17212`) | After (this branch) |
| :-- | --: | --: |
| Wheel | 1,456 KB, 313 files | 1,432 KB, 304 files |
| Environment on disk | 267 MB, 12,884 files | **69 MB, 3,470 files** |
| Packages installed | 82 | 62 |
| `networkx` / `pyvis` / `scipy` / `numpy` / `jedi` / `IPython` importable | all yes | all no |
| MCP tools (`scholar-agent --help`) | 24 | 22 |
| `import scholar_harness.cli` | 2.77, 2.38, 2.14 s | 2.63, 2.70, 2.58 s |
| `nexus-scholar --help` | 2.51, 3.58, 3.20 s | 3.17, 2.77, 2.63 s |

The 20 packages a base install no longer gets: asttokens, executing, ipython, ipython-pygments-lexers, jedi, jinja2, jsonpickle, markupsafe, matplotlib-inline, networkx, numpy, parso, prompt-toolkit, psutil, pure-eval, pyvis, scipy, stack-data, traitlets, wcwidth. Start-up time does not change: the graph code was never imported at start-up, so the times above differ only by noise. The console scripts are now `nexus-scholar`, `scholar-agent`, `scholar-harness`, `scholar-pdf`, `scholar-protocol`, `scholar-search` (`scholar-graph` gone).

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
- [x] 7. Gate ("Evidence").
- [x] 8. Independent review ("Review").

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
| Full Python suite, `suite_lock.py -- uv run pytest -q -n 4 --dist worksteal -p no:cacheprovider` | working tree of `645aedf7` before its last two edits (`build_mcpb.py` text, one allowlist case, both run separately: 29 passed) | **exit 0: 5,268 passed, 15 skipped** (counted from the progress lines; the doubled `-q` hides the summary). Collected now: 5,284 (5,405 before: 101 in deleted files, 6 removed and 1 added in mixed files, about 15 parametrized cases that left with their parameter, e.g. the `graph`/`graph_narrative` action-parity cases) |
| Targeted run of the affected areas (authority, conformance, console, agent kit, MCP, pipeline, unit, CLI, handoff, parked labels, packaging tests), `-n 4` | working tree before the docs | 3,130 passed, 7 skipped, 1 failed: the documented tool count (24) in the surface matrix, fixed with the docs; the E2 and count tests then 47 passed |
| `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | | pass |
| `generate_contract_baseline.py --check` | | "Contract baseline current" |
| `generate_contract_schemas.py`, `generate_two_study_contract_fixture.py`, `generate_protocol_schema.py` (`--check`) | | pass |
| `sync_skills_bundle.py --check`, `validate_manifest.py`, `select_test_gate.py --check` (11 tasks, 23 areas), `check_workflows.py`, `uv lock --check` | | pass |
| `uv build --wheel` (`NEXUS_WHEEL_ALLOW_NO_UI=1`) and the install into a fresh Python 3.12 venv, offline from the uv cache, base only | `ee412b58` | built, 304 files; both `nexus-scholar --help` and `scholar-agent --help` answer; 22 tools; `networkx`, `pyvis`, `scipy`, `numpy`, `jedi`, `IPython` not importable; numbers in "Measured effect" |
| Review round 1 repairs (wording, the journal text, one new test): `tests/test_dependency_bounds.py`, coordinator, publication generations, orchestrator fidelity | `ee412b58` | 77 passed; ruff `src/` pass; skills bundle and gate manifest checks pass |
| `git diff --check 9af17212` | `ee412b58` | pass |
| Merge of `origin/main` `cc0e8fa1` (1.1.0b7): conflicts in AGENTS.md, README, the user guide, `pyproject.toml` (version) and the decisions log, all text; `uv lock` re-run | `a269cda1` | lock at version 1.1.0b7, 185 packages, no `pyvis`/`jedi`/`ipython`; `uv lock --check` pass; no Python file of this branch touched by the merge |
| Environment refreshed to 1.1.0b7 (`uv sync --extra dev --extra pdf`), then `generate_screening_api_fixtures.py --check` and `tests/console/test_screening_api_contract.py` | `a269cda1` | "fixtures are current (19 files)", no diff against `origin/main` under `tests/fixtures/screening_api`; 6 passed |
| Static checks after the merge: both ruff commands, contract baseline, schemas, two-study fixture, protocol schema, skills bundle, skill portability, manifest, `select_test_gate.py --check`, `git diff --check origin/main` | `a269cda1` | pass; baseline current |
| PR-stage selection after the merge (`select_test_gate.py --changed --stage pr`, base `origin/main` `cc0e8fa1`): its pytest commands together are `tests` without `tests/kits` plus `tests/kits/agent`, run once through the lock with `-n 4` and a junit file. The selector also listed the two deleted paths `tests/kits/graph` and `tests/test_mcp_narrative.py`: it does not drop deleted files from "changed" (a selector follow-up); they were left out | `a269cda1` | junit: 4,086 tests, **4,077 passed, 8 skipped, 1 failed**: `test_stage_4_prepare_region_has_no_direct_batcher_use` slices the coordinator source on the comment "Stages 5-9 require", which round 1's repair reworded. Fixed (the test splits on the new text), with the leftover "stages 5-9" docstrings; then `tests/unit tests/pipeline tests/authority tests/e2e` with `-n 4`: **1,034 passed, 4 skipped, 0 failed** |
| Wheel and fresh install after the merge | `a269cda1` | `nexus_scholar-1.1.0b7-py3-none-any.whl`, 1,432 KB, 304 files; as above |

**Not verified.**
- CI (Ubuntu, Python 3.12, cross-OS): not run, nothing pushed.
- The wheel with the UI export inside it.
- The MCP server driven by a real MCP client; the 22-tool surface is checked through the tool manager and `--help`.
- Any real workspace: none was opened.

## Review

- **Round 1** (`milestone-reviewer`, on `645aedf7`): **CHANGES**, no P0 to P2. Six P3 findings: AGENTS.md's "six packages"; the plan's §8 parked list; the workspace-manager layout (`graph.html`, `graph.json`, "Graph" among the steps to log) and the search skill's "graph building"; the coordinator's "Stages 5-9" texts, one of them a journal description; this record's test-file count, two unlisted parametrized losses and `networkx`'s route through `extract`; the `PIPELINE_RUN_COMPLETED` outputs change not named. All six fixed in `ee412b58`, with two of the reviewer's follow-ups: a test that keeps the three dependencies out of the base install, and the coordinator test's docstring naming `stages.graph` again. Reviewer's own checks: 818 targeted tests passed (2 skipped); every deleted test covered only removed code; the negative tests fail on the old code; runtime counts 22 tools, 10 actions, 4 kits, 9 mirrored skills; no product path imports `networkx`, `pyvis`, `scipy` or `numpy`.
- **Round 2** (on `cf92912a`): **APPROVE**. All six round-1 findings fixed; both follow-ups correct; the record's shortstat, the 20-package list and 82 → 62 (checked against `uv export` of the base dependencies at both heads, for Windows on Python 3.12), the console scripts and the collected count (5,285 with the new test) confirmed. Its P3 notes, applied after: three docstrings still said "stages 5-9" (`screening_prepare.py`, `test_publication_generations.py`, `test_extraction_runtime_acceptance.py`), and the package count is Windows's (22 on Linux and macOS). Not reviewed by it: the merge `a269cda1` beyond a spot check (the merge changed docs, `pyproject.toml`'s version, `uv.lock` and main's own screening API fixtures, no Python file of this branch), and the fresh-install figures, which it could not rebuild.
