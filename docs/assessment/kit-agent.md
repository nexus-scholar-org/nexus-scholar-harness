# scholar-agent-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-agent-kit`).
Scope: `tools/scholar-agent-kit/src/scholar_agent/` (`server.py` 2,098 lines, `capabilities.py` 499, `calibration.py` 467; 3,064 total) and `tools/scholar-agent-kit/tests/` (9 files, 5,144 lines); MCP launcher `.agents/plugins/nexus-scholar/mcp_config.json`. The other seven kits were read only where a wrapper calls them.
Method: read all of `server.py` and `calibration.py`, the public surface of `capabilities.py`, and the wrapped functions in search, pdf, rag, graph, bib, verify, and the harness coordinator. Listed the registered tools in-process (`mcp.list_tools()`). Ran the kit test suite. Ran three offline reproduction scripts (no network: providers, retriever and embedder were stubbed) that call the tool functions directly against scratch workspaces outside the repo. Also tried a real stdio launch through the configured MCP command. No repo file was modified except this one.

## 1. Verdict

The MCP front door is the weakest layer in the stack, not because of its plumbing but because of what it lets an agent claim. Of the 25 registered tools, 3 are well-built refusals (E1/E2/E3). Most of the other 22 return output shaped like success when something has failed, drop parameters without saying so, or attach "verified", "LOW risk", "κ = 1.0" or "communities detected" to results that do not support them. The most serious problem is that an LLM can write the final `included.json`/`excluded.json` into any workspace through `nexus_screen` or `nexus_screen_llm`. No human decision is involved and no audit row is written. The harness pipeline then treats those files as `LEGACY_UNVERIFIED` and carries on, with only a log warning. Several outright bugs reproduce offline:
- `nexus_protocol_validate` rejects every valid protocol file.
- `nexus_graph_narrative` puts the real hub paper last.
- `nexus_bib_clean` can quietly point a citation key at a different paper.

The kit's own suite is red (1 of 155 tests fails), and the configured launcher does not start on this Windows checkout.

| Lens | Rating | One-line reason |
|---|---|---|
| Code quality & architecture | Weak | Paths are not confined, the launcher runs a different dependency set than the one tested, there are five error conventions, and the wrapper depends on private kit internals. |
| Correctness & bugs | Weak | 8 defects reproduced offline (validate, graph narrative, bib key swap, pipeline params, retraction no-op, extraction placeholders, empty-search success, empty-corpus "LOW risk"). |
| Research-method fitness | Failing | Screening can be done with no human in the loop and no audit trail; "verified" and κ labels are guaranteed by construction; nothing the wrapper does is written to the audit journal. |

Strengths worth keeping:
- The declared-unsupported boundary design (`capabilities.py`) is clean and pure. Each refusal returns the same envelope and does no I/O.
- Recon session IDs are validated by regex, and session roots under `workspaces/` are refused (`server.py:1633-1658`).
- Sync tools run in worker threads (`mcp/server/mcpserver/utilities/func_metadata.py:164`), so the `asyncio.run` calls inside sync tools are safe.

## 2. Architecture and code quality

**AGT-01 — High — Tool arguments are not confined to a workspace; defaults write to the repo root.** Reproduced.
- **Evidence.**
  - `_resolve_path` (`server.py:207-216`) passes absolute paths through and joins relative ones onto the anchor without normalising or checking containment. `..` is accepted. With `NEXUS_MCP_WORKSPACE` unset, the anchor is the repo root (`server.py:198-204`).
  - Reproduction R12 (env unset): `./literature`, `./deduped.json`, `./chroma_db`, `./graph.html` and `./extracted` all resolve to `C:\Users\mouadh\Documents\nexus-scholar-harness-demo\…`. These are the defaults of `nexus_screen`/`nexus_screen_llm` (`:399,456`), `nexus_dedup` (`:373`), `nexus_rag_query`/`nexus_rag_synthesize` (`:830,887`), `nexus_graph_build` (`:946`) and `nexus_extract_pdf` (`:641`). That contradicts the repo rule that nothing is dumped into the repo root.
  - R2: `nexus_screen(..., output_dir="../escaped_literature")` wrote the five PRISMA files into a sibling of the workspace.
  - R3: `nexus_dedup(output_path=<any absolute path>)` wrote there.
  - `nexus_bib_clean` overwrites its input in place by default (`:1000`). Pointed at a copy of `workspaces/uav-pilot-demo/protocol.json`, it rewrote the file (11186 → 11188 bytes) and replied `Cleaned BibTeX saved … (0 entries -> 0 unique, keys standardized)`.
- **Impact.** An LLM chooses these arguments. One mistaken or prompt-injected path can overwrite `included.json` in another review, or rewrite any file the user can write.

**AGT-02 — High — The configured MCP launcher runs a different environment than the one the repo tests, and here it does not start.** Reproduced (launch); Static (the divergence).
- **How it is launched.** `mcp_config.json` runs `uv run --directory tools/scholar-agent-kit scholar-agent`. That makes `uv` resolve the kit's own project (`tools/scholar-agent-kit/pyproject.toml` + `uv.lock`), not the shared `.venv`.
- **Observed on this checkout.** The stdio probe died during `initialize` with `MCPError: Connection closed`. uv's stderr showed it trying to rebuild the nested venv: `error: failed to remove file …\tools\scholar-agent-kit\.venv\lib64: Access is denied`. The nested `.venv` is a Linux venv (`pyvenv.cfg`: `home = /home/mouadh/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu/bin`). So this launch path does an implicit `uv sync` of a kit, which AGENTS.md says never works outside the monorepo. (uv aborted before changing anything; the nested venv timestamps did not change.)
- **What it would run if it did start.** Sibling kits come from git pins in `pyproject.toml:36-42`. Two of them disagree with `plugins.json`, which is the declared source of truth for kit versions:

  | Kit | `pyproject.toml` / `uv.lock` | `plugins.json` `default_rev` |
  |---|---|---|
  | scholar-search-kit | `911d864…` (`pyproject.toml:37`, `uv.lock:4303`) | `d20292a…` |
  | scholar-rag-kit | `033191e…` (`pyproject.toml:40`, `uv.lock:4302`) | `15a7a5a…` |

  The vendored, edited `tools/<kit>/src` is never used.
- **Harness-dependent tools.** `nexus-scholar-harness` is deliberately absent from the kit's dependencies (`pyproject.toml:43-54`). In that environment the three `recon_*` tools fall back to the `harness recon adapter unavailable` envelope (`server.py:1739-1747`) and `nexus_pipeline_run` raises ImportError. The tests pass only because they run in the shared `.venv` with the harness on `pythonpath`.

**AGT-03 — Medium — Five incompatible result conventions, and no use of MCP `isError`.** Static, plus a count.
1. Free-text strings, with `"Error: …"`-prefixed text on failure: 10 tools (`render_criteria`, `discover`, `dedup`, `screen`, `extract_pdf`, `rag_query`, `rag_synthesize`, `matrix_extract`, `graph_build`, `bib_clean`).
2. `{"status":"SUCCESS"|"ERROR"}`: 8 tools.
3. `{"status":"error","message"}`, lower case: the 3 recon tools.
4. `{"status":"VALID"|"INVALID","error"}`: validate, where an exception is reported as `INVALID` (`server.py:312-313`).
5. The capability envelope with `"FAILED"`: the 3 refusals.

Every tool except `nexus_discover` catches all exceptions and returns them as normal content. An agent therefore has to parse prose to tell success from failure, and the client never sees a protocol-level error. `nexus_protocol_render_criteria` returns `"Error rendering criteria: …"` in the same slot as the Markdown it would otherwise render (`:323-331`).

**AGT-04 — Medium — Coupling to private kit internals, and a re-implemented CLI.** Static.
- `nexus_verify_phase4` calls `scholar_verify.cli` private helpers (`_merged_records`, `_load`, `_write`, `_manifest`, `_slug`) and `trust_context._rows` (`server.py:1220-1279`). `nexus_protocol_validate` imports `scholar_protocol.validate._check_cross_field` (`:63,273`).
- The trust-context branch (`:1255-1288`) is a copy of `trust_context_cmd` (`scholar_verify/cli.py:147-193`) without its `--consensus`/`--claims-dir` overrides or its `_resolve_workspace` check (`cli.py:27-31`).
- The wrapper skips the CLI's overwrite confirmation (`cli.py:63-66`), so every call silently overwrites `phase4/*.json`.
- Any rename inside verify-kit breaks MCP with no contract test failing. AGENTS.md's "call the kit CLIs / import their APIs" does not cover underscore-private helpers.

**AGT-05 — Medium — The test suite is skewed, encodes several defects, and is currently red.** Reproduced.
- **Run result.** `uv run pytest tools/scholar-agent-kit/tests`: 155 tests, 1 failure (`test_server.py::test_nexus_protocol_compile_and_validate`, see AGT-07), 1 skipped.
- **Where the tests point.** By count of direct calls, the three refusal stubs get 46 call sites. Nine working tools get none: `nexus_discover`, `nexus_extract_pdf`, `nexus_graph_build`, `nexus_bib_clean`, `nexus_screen_reconcile`, `nexus_verify_claims`, `nexus_verify_phase4`, `nexus_critique_methodology` and `nexus_graph_narrative`. Some of these are covered from the harness side in `tests/mcp/test_mcp_tools_graph.py`.
- **Tests that lock in the defects:**
  - `test_screen_llm_fallback_on_llm_failure` and `…_on_constructor_error` assert `status == "SUCCESS"` after the LLM failed (`tests/test_screening.py:159-200`).
  - `test_screen_llm_checklist_schema_used` asserts that the schema builder is *called*, not that its output reaches the LLM (`:212-241`).
  - `test_pipeline_skip_stages` mocks the orchestrator with a `"dedup"` key. The real coordinator emits `"deduplication"` (`coordinator.py:376`), and nothing is actually skipped (AGT-11).
- **Not gated here.** The harness `testpaths = ["tests"]` (`pyproject.toml:51`) excludes `tools/*/tests`, so this repo's pytest gate does not see the red kit test.

**AGT-06 — Low — Dead code and schema imprecision.** Static.
- Dead or redundant code:
  - Unused import `search_discover` (`server.py:70`).
  - `checklist_schema` is computed and then discarded (`:499`).
  - `recon_delta` builds an engine and throws it away (`:1958-1960`).
  - PageRank is computed twice (`:979-980`).
  - `import re` sits inside a loop (`:1142`).
- Parameters declared `str = None` (for example `api_key`, `query`, `skip_stages`, `bib_file`, `section`) are published in the tool schema as plain `"string"`, not nullable. That is visible in the `list_tools()` dump.
- `calibration.py` is unreachable from MCP except for `build_checklist_schema`. Its `CalibrationReport.per_criterion` is declared, rendered (`calibration.py:303,326-338`) and never populated by `evaluate_calibration` (`:457-467`).

## 3. Correctness and bugs

**AGT-07 — High — `nexus_protocol_validate` returns `INVALID` for every valid protocol passed as a file.** Reproduced.
- **Bug.** On the success path, `_response` re-parses the protocol with `ResearchProtocol.model_validate(... p.read_text(...))` (`server.py:277-282`). `read_text` returns a `str`, not a `dict`, so Pydantic raises `model_type`. The outer `except` (`:312-313`) turns that into `{"status":"INVALID"}`.
- **Command.** Ran `nexus_protocol_validate(<ws>/protocol.json)` on all three workspaces.
- **Observed.** All three returned `{"status": "INVALID", "error": "1 validation error for ResearchProtocol\n  Input should be a valid dictionary or instance of ResearchProtocol [type=model_type, …input_type=str]"}`.
- **Comparison.** `uv run scholar-protocol validate workspaces/uav-pilot-demo/protocol.json` reports `VALID — 0 error(s)`.
- **Tests.** The kit's own test fails on exactly this. The harness parity test only covers an *invalid* file (`tests/mcp/test_mcp_tools_graph.py:524-536`), so it passes.
- **Impact.** An agent told that a valid, frozen protocol is invalid may "repair" it, which mutates the protocol of record.

**AGT-08 — High — `nexus_graph_narrative` inverts hub rankings and invents community structure.** Reproduced.
- **Setup (R13).** A 3-node graph with the attributes `CitationGraphBuilder.build_graph` sets, exported with the kit's `export_json`, then passed to `nexus_graph_narrative`.
- **Cause 1, ranking.** `compute_pagerank` lower-cases the keys (`scholar_graph/builder.py:120`). `_identify_hubs` looks up the raw node id (`server.py:1332`). The node `10.1109/TGRS.2021.1`, which has the highest PageRank (1.0), therefore gets 0.0 and is ranked last: `| 3 | Paper Upper | — | 0.0000 |`, below the two papers that cite it (0.3704).
- **Cause 2, DOI column.** It is empty, because the builder stores the DOI as the node id, not as a `doi` attribute.
- **Cause 3, communities.** The builder hard-codes `group=1` on every node (`builder.py:71,101`). Louvain runs only in `scholar_graph.scientometrics` (`scientometrics.py:391`), which this path never calls. So the report states `Communities detected: 1` and lists "Key themes" made from the top three titles.
- **Fallback nodes.** DOIs OpenAlex could not resolve are added as `Study <doi>` nodes (`builder.py:96-105`) and can appear as hubs.
- **Impact.** The output is presented as a "Visual Synthesis" in `synthesis/visual_synthesis.md` and is wrong in the direction that matters.

**AGT-09 — High — `nexus_bib_clean` can silently re-point a citation key to another paper and under-reports its input.** Reproduced.
- **Input (R10).** A `.bib` with `myKey1` (Smith 2020, Paper A), `otherKey` (Smith 2020, Paper B) and a second `myKey1` (Doe 2019, Paper C).
- **Steps.**
  1. bibtexparser v2 turns the duplicate `myKey1` into a parse-failed block.
  2. `BibLinter.lint(generate_keys=True)` renames the first two entries to `Smith2020` and `Smith2020a`.
  3. `BibDeduplicator.dedup` re-emits the failed block verbatim (`scholar_bib/deduplicator.py:55-57`).
- **Observed file.** It now starts with `% WARNING Parsing failed for the following 5 lines.` followed by `@article{myKey1, author = {Doe, A}, title = {Paper C} …`. The tool replied `(2 entries -> 2 unique, keys standardized)`, but the input had 3.
- **Impact.** Under BibTeX's first-definition rule, `\cite{myKey1}` used to resolve to Paper A. It now resolves to Paper C. The file is overwritten in place by default (`server.py:1000`), with no backup and no old→new key map.
- **Scope.** Only lint and dedup are exposed. The Crossref `resolve` step of the bib CLI (`scholar_bib/cli.py:98-124`) is not, so the tool is narrower than "clean" suggests.

**AGT-10 — Medium — Tools write to stdout, which is the stdio JSON-RPC channel.** Reproduced in-process; not reproduced over a live stdio session, because of AGT-02.
- **Cause.** `verify_cli._write` calls `typer.echo("wrote … + .md")` (`scholar_verify/cli.py:48`). `nexus_verify_phase4` calls it for every stream (`server.py:1223-1252`).
- **R7.** With stdout captured, `nexus_verify_phase4(ws, stream="risk-of-bias")` emitted `'wrote …\\phase4\\risk_of_bias.json + .md\n'` to stdout.
- **Impact.** Under the stdio transport that line lands in the protocol stream as a non-JSON frame. Depending on the client it is dropped, logged as a parse error, or kills the session.

**AGT-11 — Medium — `nexus_pipeline_run` drops `query` and does not honour `skip_stages`.** Reproduced (signature), Static (flow).
- `query` is never used. `run_pipeline_async` accepts only `protocol_path`, `max_search_results` and `mock_mode` (R11; `orchestrator.py:564-583`).
- `skip_stages` is applied *after* the full run, by deleting keys from the result dict (`server.py:606-609`).
- So `skip_stages="discovery"` still performs network discovery and Stage-4 batch preparation with `force=True` (`coordinator.py:444-446`), and then hides those stages' results from the agent.

**AGT-12 — Medium — `nexus_verify_phase4(stream="retraction")` does nothing and reports success.** Reproduced.
- `skip_retraction` defaults to `True` (`server.py:1184`), so the branch at `:1219` is skipped.
- R6 returned `{"status": "SUCCESS", "stream": "retraction", "written": {}}`.
- `stream="all"` likewise omits retraction silently. The workspace protocols set `"retraction_check_required": true`.

**AGT-13 — Medium — `nexus_critique_methodology` reports `overall_risk: "LOW"` for zero assessed studies.** Reproduced.
- **R8.** With empty `records.json` and `_manifest.json` it returned `{"status": "SUCCESS", "overall_risk": "LOW", "per_study_count": 0, …}` and wrote `phase4/methodological_critique.md`.
- **Cause.** The label rule (`server.py:1426-1432`: HIGH if any H; else UNCLEAR if `?` > L; else LOW) defaults to LOW.
- **Method problem.** A corpus-level "overall risk" is not a QUADAS-2 or PROBAST construct, which is applied per study.

**AGT-14 — Medium — `nexus_extract_pdf` reports success when nothing was extracted.** Reproduced.
- **R4.** For a 17-byte non-PDF named `10.1234_fake.pdf`, the tool returned `Extracted 10.1234_fake.pdf to …\10.1234_fake.md`. The file's frontmatter says `doi: 10.1234_fake` (a path heuristic, `server.py:630-632`) and the body is the placeholder `Extracted content from 10.1234_fake.pdf`. That comes from PyMuPDF's catch-all (`scholar_pdf/extract.py:97-99`).
- **Other quiet behaviours:**
  - `engine="nonsense"` silently uses PyMuPDF (`server.py:685`).
  - Docling silently falls back to PyMuPDF (`extract.py:123-127`).
  - `engine="grobid"` writes `.tei.xml`, not the Markdown the docstring promises (`extract.py:155-157`).
  - The default `output_dir="./extracted"` is the repo-root `extracted/` (AGT-01).
- **Note.** The docstring's NON-AUTHORITATIVE warning (`server.py:643-671`) is accurate, but the return string gives an agent no cue.

**AGT-15 — Medium — `nexus_discover` turns total provider failure into "Search completed".** Reproduced.
- **R9.** With all four providers raising `RuntimeError("network down")`, it returned `Search completed: 0 unique papers (deduped). Saved to …discover_uav_weed_1793664353.json.` The errors went only to the log (`scholar_search/engine.py:60-61`).
- **No provenance.** No per-provider status or counts are returned or saved.
- **Defaults and limits.**
  - `start_year=2020` is applied by default (`server.py:340,352`), whatever the protocol's `date_range` says.
  - `limit` is per provider, not total (`Query.max_results`).
  - The epilog says "Search OpenAlex" (`:2033`) although four providers are queried.

## 4. Research-method fitness

**AGT-16 — Critical — Screening can be completed with no human decision, no record of how decisions were made, and no audit row; the pipeline then consumes the result.** Reproduced.
1. **Direct writes.** `nexus_screen` and `nexus_screen_llm` write `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json` and `prisma_screening_report.md` straight into any `output_dir` (`server.py:423-441,527-542`). The harness's agent-in-the-loop contract (`agent_screen.py` batch → decisions → `collect`), its authorization generations, and its MAYBE/CONFLICT refusal (`src/scholar_harness/screening/integrity.py:32`) are all skipped.
2. **Fallback reported as success.** R1, with no `GEMINI_API_KEY`: `nexus_screen_llm` returned `{"status": "SUCCESS", "included": 1, "excluded": 1, …}`. The decisions came from the keyword heuristic (`screening_reasoning`: `Matched inclusion criteria ['INC-01'] via title+abstract: evidence=['imagery', 'weed', 'detection']`). The decision record has no field naming the method, model, prompt or fallback (keys: `confidence, decision, document_title, doi, matched_inclusion_criteria, relevant_rqs, screening_reasoning, violated_exclusion_criteria, workspace_id`). Per-batch LLM failures in the kit also fall back silently (`scholar_search/screening.py:686-692`).
3. **Wrong PRISMA counts.** The wrapper never passes `total_identified` or `duplicates_removed` to `partition_screening_results` (`server.py:419-421`). The generated report therefore states `Total Records Identified (Federated Search): 2` and `Duplicate Records Removed: 0` for whatever file was screened.
4. **Downstream consumption.** After R1, `require_current_generation(ws)` returned `GenerationStatus.LEGACY_UNVERIFIED`. The coordinator handles that state by logging a warning and continuing into extraction, indexing, matrix, graph and synthesis (`coordinator.py:495-502`). The returned result carries no marker.
5. **Audit.** No journal row is written (`audit journal exists: False`).

For a sole-reviewer review this is the shortest path to a PRISMA flow and an included set that look legitimate but were produced by `"weed" in abstract`.

**AGT-17 — High — `nexus_rag_synthesize` reports "verified claims" and "% entailment" that are guaranteed by construction.** Reproduced.
- **Why.** The wrapper never passes `llm_callable`. The kit's deterministic path makes each "claim" the first line of a retrieved chunk and cites that same chunk (`scholar_rag/synthesis.py:308-314`). It then scores the claim against the chunk it was cut from (`:195`).
- **R3a.** With the query "Does UAV weed detection improve crop yield?" and two stub chunks, one about bananas and one stating the opposite, the tool returned `Grounded Synthesis … (2/2 verified claims, 100.0% entailment)`. This was with a model-free embedder.
- **R3b.** With an embedder that raises, the lexical fallback gives the same 100% (`synthesis.py:149-161`).
- **No-claims case.** If no claims are parsed, `entailment_rate` is 1.0 (`:318`).
- **Impact.** SKILL.md §4 warns that this is cosine wording. The tool's own header still says "verified", which is the word an agent will repeat.

**AGT-18 — High — `nexus_screen_reconcile` reports perfect agreement for a single screener and silently resolves undecided records to EXCLUDE.** Reproduced.
- **Single screener (R5).** In directory mode, every `batch_*_decisions.json` without a suffix maps to screener `"screener1"` (`server.py:1037-1040`). A single-reviewer directory therefore gives `n_raters = 1`. `calculate_fleiss_kappa` returns 1.0 when `n <= 1` (`scholar_search/screening.py:750-751`). R5 output: `"fleiss_kappa": 1.0`.
- **Undecided values.** The same run turned a record marked `"UNCERTAIN"` into `"reconciled": {"SCI-000003": "EXCLUDE"}`. Votes that are neither INCLUDE nor EXCLUDE count as a tie, and an unadjudicated tie becomes EXCLUDE (`screening.py:836-844`).
- **Missing votes (R5b).** A record one screener never rated is counted as that screener's EXCLUDE (`screening.py:823`), which both decides the record and distorts κ (−0.333).
- **Conflict with the harness.** Harness integrity explicitly refuses MAYBE/CONFLICT at finalization (`integrity.py:32,104`). The MCP path quietly turns them into exclusions and reports a κ that an agent can cite as inter-rater reliability.

**AGT-19 — High — No wrapper action reaches the audit journal; the MCP path cannot be reproduced from the record.** Static, confirmed by grep plus R1.
- **Grep.** Searching `tools/scholar-agent-kit/src` for `journal|audit|log_event|append_legacy_event` finds only docstrings and output file names. No tool calls the workspace-manager logger.
- **Indirect logging only:**
  - `nexus_pipeline_run`, through the coordinator.
  - `nexus_rag_synthesize`, through the rag kit's journal search. That search starts from the process CWD (`synthesis.py:229-243`), which for MCP is `tools/scholar-agent-kit`, so where it writes depends on directory layout.
- **What goes unrecorded:**
  - Discovery: query string, provider list, per-provider counts, date. The output is a timestamped cache file under `.cache/mcp` (`server.py:358-364`).
  - Screening: method, model and fallback.
  - Bib key rewrites.
  - Phase-4 overwrites.
- **Rule.** AGENTS.md treats journal logging as a hard convention, and the front door ignores it.

**AGT-20 — Medium — `nexus_screen_llm` describes a method it does not run, and asks for the API key as an argument.** Static.
- **Docstring vs code.** The docstring promises a "structured boolean checklist" and verdicts "backed by per-criterion booleans" (`server.py:462-466`). The checklist is built (`:499`) and never passed on. The kit prompt contains no checklist; `screening.py` has no `checklist`/`boolean` token.
- **Kit-level, for the search-kit owner.** An LLM entry missing `decision` defaults to INCLUDE (`scholar_search/screening.py:550`).
- **API key.** `api_key` is a tool argument, so the key enters the agent transcript and MCP logs. The kit sends it as a URL query parameter (`screening.py:648`).

**Human-in-the-loop summary.**
- Protocol approval: no MCP tool persists `protocol.json` (`nexus_protocol_compile` only returns it), so that gate is intact. AGT-07, however, invites hand-editing.
- Screening: the gate is bypassable (AGT-16, AGT-18).
- Phase-4 and synthesis outputs: overwritten without confirmation (AGT-04).

## 5. Doc drift

Only claims shown false above are listed. The "25 tools" claim (SKILL.md:13, `kits_surface_matrix.md:29,405`) is **true**: 25 tools are registered.

| Claim | Where | Reality |
|---|---|---|
| Validate: "**both** modes run structural + cross-field rules", file mode returns VALID | `.agents/skills/scholar-agent-kit/SKILL.md:60`; `docs/kits_surface_matrix.md:87-90,394` ("RESOLVED") | File mode returns INVALID for every valid protocol (AGT-07). |
| `nexus_pipeline_run` "comma-separated skips" | SKILL.md:80; `server.py:580-581` | Skips happen only in the output (AGT-11). |
| "#6/#7 are heuristic/LLM-checklist screening"; "INCLUDE/EXCLUDE verdict backed by per-criterion booleans" | SKILL.md:161; `server.py:462-466` | No checklist reaches the LLM (AGT-20). |
| "`scholar-verify-kit` is an undeclared MCP-side dep" | SKILL.md:177-178 | Stale: declared at `pyproject.toml:42`. |
| "Validate protocol schema and checksum"; "Search OpenAlex" | `server.py:2031,2033` (`--help` epilog) | No checksum is validated; four providers are queried. |
| The MCP server "launched `--directory tools/scholar-agent-kit`" shares the recon cache with the CLI | AGENTS.md (grounded-recon bullet) | That launch uses the kit-local environment, which has no harness, so recon is unavailable there (AGT-02). |
| Coordinator "REPORTS the typed LEGACY_UNVERIFIED code explicitly" | `src/scholar_harness/pipeline/coordinator.py:488-489` | Only `logger.warning` (`:496-502`); the result carries no code. This is in the harness, not this kit, but it makes AGT-16 worse. |

## 6. Prioritized recommendations

All fixes to `tools/scholar-agent-kit/src` belong in **nexus-scholar-org/scholar-agent-kit**. Each fix must then be synced back to `tools/` and the `plugins.json` `default_rev` bumped, per the repo's three-invariant rule. Items that touch other kits are marked with the owning repo.

| ID | Severity | Effort | Action |
|---|---|---|---|
| AGT-16 | Critical | M | Remove or gate `nexus_screen`/`nexus_screen_llm`. Either write only proposals, for example `literature/screening/mcp_proposals_*.json` that feed the `agent_screen` handoff, or refuse unless the target workspace has an authorized generation. Record `screening_method`, `model` and `fallback_used` on every decision. Return `status:"DEGRADED"` when any fallback happened. Pass the real identification and duplicate counts. Separately (harness repo), report `LEGACY_UNVERIFIED` in the pipeline result. |
| AGT-07 | High | S | In `_response`, use `json.loads(p.read_text())` (or reuse the parsed object). Add a test for a valid *file* in the kit and in the harness parity test. |
| AGT-01 | High | M | Confine every path argument: resolve, require the result to be inside an explicit workspace root (env var or `-w`), reject `..` escapes and absolute paths outside it, and require an explicit output path for anything that overwrites (no in-place default for `nexus_bib_clean`). |
| AGT-18 | High | S | Refuse κ when fewer than 2 raters. Report unknown, MAYBE or missing votes as `UNRESOLVED` instead of imputing EXCLUDE. Return ties without a default decision. The defaults at `screening.py:823,844` are owned by scholar-search-kit. |
| AGT-17 | High | S | Rename the header to "chunk-similarity (not entailment)" and drop "verified". Or refuse the deterministic path and require an LLM callable. The scoring itself is owned by scholar-rag-kit. |
| AGT-08 | High | S | Normalise PageRank keys consistently (scholar-graph-kit), or look them up case-insensitively in the wrapper. Run Louvain, or omit communities when every `group` is identical. Emit the DOI from the node id. |
| AGT-09 | High | S | Refuse inputs with parse-failed blocks, return an old→new key map, write to a new file by default, and count failed blocks in the message. |
| AGT-19 | High | M | Have every state-changing tool append a journal event (tool, arguments, inputs/outputs, counts, fallbacks) through the workspace-manager logger. Persist a search log for `nexus_discover`. |
| AGT-02 | High | M | Point `mcp_config.json` at the shared environment, for example `uv run --no-sync scholar-agent -w <ws>` from the repo root, or the `nexus-scholar` wheel entrypoint. Align `pyproject.toml`/`uv.lock` pins with `plugins.json`. |
| AGT-10 | Medium | S | Stop calling `verify_cli._write`. Use the verify-kit public API, or redirect stdout to stderr around kit calls. |
| AGT-11 | Medium | S | Forward or remove `query`. Implement real stage skipping in the harness, or remove the parameter. |
| AGT-12 / AGT-13 | Medium | S | Return an error, or `status:"SKIPPED"` with a reason, when a requested stream does not run. Return `INSUFFICIENT_DATA` for zero studies. Drop the corpus-level "overall risk". |
| AGT-14 / AGT-15 | Medium | S | Fail on extraction placeholders and on unknown engines. Report the engine actually used. Return per-provider status, and an error when every provider failed. Take `start_year` from the protocol. |
| AGT-03 / AGT-04 | Medium | M | Adopt one envelope (`status`, `errors`, `warnings`, `artifacts`) for all 25 tools, and set MCP `isError` on failure. Replace private-helper calls with public verify and protocol APIs. |
| AGT-05 | Medium | S | Add behavioural tests for the 9 untested tools, rewrite the tests that assert SUCCESS on fallback, and fix the red test. Consider adding `tools/scholar-agent-kit/tests` to a gated job. |
| AGT-20 | Medium | S | Either send the checklist and parse booleans through `checklist_to_decision`, or correct the docstring. Read the key from the environment only. |
| AGT-06 | Low | S | Remove dead code and make optional parameters `str | None`. |

## 7. Limits of this assessment

- **Stdio not exercised live.** I never got a working stdio session: the configured launcher failed (AGT-02), and I did not repair the environment. AGT-10's damage to the transport is inferred from the stdout capture, not observed at a client.
- **No network or models.** Provider, retriever and embedder behaviour was stubbed. Retrieval quality, matrix extraction (`nexus_matrix_extract`) and graph construction from live OpenAlex were not exercised. AGT-17 was shown with stub embedders. A real sentence-transformer would also score a chunk's own first line highly, but I did not measure it.
- **Pipeline not run end to end.** `nexus_pipeline_run` needs network discovery. AGT-16's downstream consumption rests on the reproduced `LEGACY_UNVERIFIED` status plus a static read of `coordinator.py:495-502`.
- **Recon not reviewed in depth.** The recon tools (`recon_*`) were reviewed for path and session safety only. Their distillation semantics belong to the harness recon assessment.
- **Wrapped kits only as needed.** Their internals were read only as far as each wrapper's behaviour required. Defects attributed to them here (bib dedup, search fallback defaults, rag scoring, graph key case) should be confirmed by the per-kit assessments.
- **Reproduction scripts.** They live outside the repo, in the session scratchpad (`repro.py`, `repro2.py`, `repro3.py`, `stdio_probe.py`), and are not committed.
