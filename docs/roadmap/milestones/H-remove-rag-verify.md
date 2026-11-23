# H-remove-rag-verify Remove the retrieval and verification kits

Branch: `dev/h/remove-rag-verify` (from `origin/main` `8dd7904a`) · Lane: **RELEASE** (packaging, the MCP surface and the public commands change) · Status: **READY FOR PR** (not pushed; see "Review" for the verdict)

The researcher's decision of 2026-11-23, in the coordinator session, after the project review and the test-suite review of that day (`docs/assessment/project-review-2026-11-23.md`, section 3, "Complexity that is not earning its keep"): delete `scholar_rag` and `scholar_verify`, their tests, and every stage, MCP tool, command, skill and extra that only exists to call them. Their words: "I want to delete the rag and verify module and their test entirely. They are saved in the commit history." `scholar_graph`, PDF extraction, the capability adapter and `claims` stay for a later pass.

## Restore

Everything removed here is in `origin/main` at **`8dd7904a`** (2026-11-23). To bring a package back:

```powershell
git checkout 8dd7904a -- src/scholar_rag tests/kits/rag
```

The same for `src/scholar_verify`, `tests/kits/verify`, the four harness modules, the skills and the test files listed below; then re-add the `rag` extra, the two console scripts and the two package entries in `pyproject.toml`, and the stages in `pipeline/coordinator.py`.

## What was deleted

`git diff --shortstat origin/main..HEAD` at the final head: 208 files, +636 / −52,370 lines (113 deleted, 94 changed, 1 added: this record). `src/`: +87 / −19,972. `tests/`: +262 / −29,451. `uv.lock`: +2 / −1,122.

| What | Files | Lines |
| :-- | --: | --: |
| `src/scholar_rag` | 21 | 14,486 |
| `src/scholar_verify` | 9 | 2,017 |
| `tests/kits/rag` | 19 | 14,884 |
| `tests/kits/verify` | 7 | 959 |
| Harness modules that only called rag: `index_acceptance.py` (976), `pipeline/indexing.py` (895), `pipeline/matrix.py` (110), `pipeline/synthesis.py` (124) | 4 | 2,105 |
| Test files of removed code: `conformance/test_e3_index_lineage_boundary.py` (2,409) and its fixture `e3_golden_manifest.json` (150), `kits/agent/test_mcp_indexing_boundary.py` (1,421), `pipeline/test_indexing_stage.py` (707), `unit/test_matrix_stage.py` (778), `unit/test_synthesis_stage.py` (884), `e2e/test_e2e_extract_index.py` (356), `e2e/test_e2e_synthesis.py` (391), `test_mcp_critique.py` (93), `e2e/test_e4_negative_proof.py` (961), `e2e/e4_sealed_fixture.py` (777) | 11 | 8,927 |
| `tests/e2e/fixtures/e4_golden/` (the sealed E1-to-E3 fixture) | 29 | 604 |
| Skills `scholar-rag-kit`, `scholar-verify-kit` and their bundled copies | 10 | 1,066 |
| `docs/kits/rag/`, `docs/kits/verify/` | 3 | 291 |

Changed, not deleted: the MCP server (−582 lines: seven tools and the rag/verify imports), the capability registry (the E3 `rag_indexing` declaration), the orchestrator (the rag imports, the `ScholarIndexer` stub, seven indexing delegates, the Chroma reads), the pipeline coordinator (Stages 6, 7, 9 and the `indexing_fn` parameter), the extraction producer and its two command lines (`index_accepted_documents`, `extract index`, `--index`), the console's actions table and default pipeline, the pipeline allowlist, `doctor`, the skill vocabulary, `pyproject.toml`, the plugin manifest, CI, the gate manifest and selector, and 36 test files repaired (one of them `tests/conftest.py`, a comment).

**Tests.** Collected before (`origin/main` `8dd7904a`, with the `rag` extra): **6,590**, of which 1,006 in `tests/kits/rag` and `tests/kits/verify`. After (final head, without the `rag` extra): **5,351** (5,336 passed, 15 skipped). 1,245 were removed (the 1,006 kit tests and 239 in the deleted or split harness, conformance, e2e and MCP files) and 6 added (the four refusal tests of the indexing commands, two allowlist negatives). No test of code that stays was dropped to make the suite pass: a test was deleted only when everything it exercised was deleted; where a test mixed both (the extraction acceptance file, the canonical-profile parity, the registered-identity tests, the coordinator tests, the console tests), the part over kept code stayed and was repaired, and removed behaviour gained negative checks (below).

## What a user loses

- **Commands:** `scholar-rag` (index, query, synthesize, consensus, matrix and the rest) and `scholar-verify` (retraction, open-science, coi, risk-of-bias, trust-context, verbatim-claims); `nexus-scholar extract index` and `extract publish --index`; `agent_extract.py index` and `publish --index`. `extract status` and `extract publish` stay.
- **MCP tools (32 to 25):** `nexus_rag_index` (the E3 refusal), `nexus_rag_query`, `nexus_rag_synthesize`, `nexus_matrix_extract`, `nexus_verify_claims`, `nexus_verify_phase4`, `nexus_critique_methodology`. Kept: inception (`nexus_protocol_*`), recon (`recon_*`), the assistant and critic (`nexus_assistant_*`), the screening task (`nexus_screening_queue`, `nexus_screening_record`, `nexus_submit_proposal`), discovery, dedup, screening, the graph tools, the PDF refusals, `nexus_extract_pdf` and `nexus_pipeline_run`.
- **The pipeline after a collected screening** (`nexus-scholar run`, `nexus_pipeline_run`): extraction and the citation graph only; no index, matrix or synthesis. Its result no longer carries the `indexing`, `matrix_rows` and `synthesis` stages, and its summary no longer prints "Matrix Rows" or "Grounded Claims". `nexus-scholar status` no longer prints the vector-chunk, matrix and synthesis rows (the console's status JSON keeps its keys; `vector_chunks` is always 0).
- **Console actions** (the agents actions table): `rag_index`, `trust_context`, `synthesize`, `critique_methodology` (16 to 12). The default design-science pipeline loses its `n5_ds_matrix` node. A stored pipeline spec with a `scholar-rag` or `scholar-verify` node is now refused at validation (`COMMAND_NOT_ALLOWED`), as any command outside the allowlist is.
- **Install:** the `rag` extra (chromadb, sentence-transformers, openai) is gone; `all` is `pdf` + `extract`. The OpenAI-compatible screening driver does not use the `openai` package and is unaffected.
- **Skills:** `scholar-rag-kit` and `scholar-verify-kit` (12 mirrored skills to 10).

## What must stay true, and how it was checked

| Must stay true | Evidence |
| :-- | :-- |
| The wheel builds | `uv build --wheel` (with `NEXUS_WHEEL_ALLOW_NO_UI=1`: this worktree has no UI export); 312 files, no `scholar_rag`/`scholar_verify` path, seven console scripts, extras `ai, all, dev, extract, pdf` |
| `nexus-scholar --help`, `scholar-agent --help` on the base install | the wheel installed offline from the uv cache into a fresh Python 3.12 venv: both answer; `--help` lists 25 tools; `scholar_rag`, `scholar_verify`, `chromadb` and `torch` are not importable |
| The MCP server keeps its inception, recon, assistant, protocol and screening-task tools | `tests/conformance/test_count_freshness.py` pins the exact 25-name set; `test_mcp_tool_parity.py`; the E1/E2 count tests |
| Charting's PDF download keeps working | `scholar_pdf` untouched; `tests/kits/pdf` and the charting tests are in the full run |
| The console and the web app unchanged in behaviour | no file under `apps/` or `console/api` changed beyond the discovery route's dropped `indexing_fn=_no_indexing` (a placeholder that raised if called); the web app reads none of the removed stage keys or actions (searched `apps/research-ui/{app,components,lib}`) |
| Contract v1 | `generate_contract_baseline.py --check`: current, no drift. No locked file changed; `contracts/` untouched. Schemas, two-study fixture and protocol schema checks pass |

## Definition of done

- [x] 1. `src/scholar_rag`, `src/scholar_verify`, `tests/kits/rag`, `tests/kits/verify` deleted, and every module, stage, MCP tool, command, action, skill, extra and test that existed only to call them (tables above).
- [x] 2. No reference to the two packages remains in `src/`, `tests/` (outside the baseline-locked contract fixtures), `scripts/`, `pyproject.toml`, `.agents/`, CI or the gate manifest, except where a line records the removal, or in a baseline-locked file (below).
- [x] 3. Removed behaviour is refused, not silently ignored, with tests: `extract index`, `extract publish --index` and `agent_extract.py index` / `publish --index` are usage errors (exit 2) that create nothing (`test_cli_indexing_entry_points_are_refused`, `test_script_indexing_entry_points_are_refused`); `indexing_fn` passed to the coordinator is a `TypeError` and no stage runs (`test_indexing_fn_is_refused_now_that_indexing_is_gone`); pipeline specs naming `scholar-rag` or `scholar-verify` are refused (`test_pipeline_commands_outside_the_allowlist_are_invalid`); the removed actions, tools and stage keys are absent (`test_agent_actions_table`, `test_count_freshness`, `test_scholar_agent_cli_help_subprocess`, the coordinator and orchestrator-fidelity tests); the wheel carries neither package (CI smoke).
- [x] 4. Packaging: `pyproject.toml`, `uv.lock` (`uv lock --check`), the plugin manifest (`validate_manifest.py`), the skills bundle (`sync_skills_bundle.py --check`), skill portability (`skill_portability_transform.py --check`).
- [x] 5. CI: the wheel smoke no longer imports the removed modules and asserts they are absent; the Python job syncs `--extra dev --extra pdf` and no longer fetches the embedding model. Only those lines changed.
- [x] 6. Gate manifest: the tasks that existed only for E3 indexing (T-10 to T-100, T-130, T-140), the `rag` and `verify` areas and the `scholar-rag-kit` fallback are removed; `select_test_gate.py --check` passes; its tests repaired to remaining tasks.
- [x] 7. Documents corrected where they would now be false: `AGENTS.md`, `README.md`, `docs/kits_surface_matrix.md`, `docs/nexus_scholar_user_guide.md`, the agent skill and five other skills, and `docs/architecture/wp01/evidence-boundaries.md` (its tool count is test-read).
- [x] 8. Gate: the two ruff commands, the contract, schema, fixture, protocol-schema, skills and manifest checks, the wheel, and one full Python suite with `-n 4` on the final head ("Evidence").

## Left as it is, on purpose

- **Baseline-locked files that name the rag kit:** `docs/architecture/cross_kit_contract_v1.md`, `wp01_contract_adoption_handoff.md`, `wp01_packet_c_reference.md`, the E3 packet documents, `scripts/generate_contract_baseline.py` (its `E_downstream_adapter_stubs` packet names `scholar-rag-kit`) and the frozen fixtures under `tests/fixtures/contracts/v1/` (a producer string `scholar-rag-kit`). Changing any of them is a contract decision (decision item 1).
- **`contracts/` keeps its index and chunk types** (`IndexManifest` artifacts, `CHK-` identities, the `rag-chunk-identity-v1` golden): they are Contract v1, not rag code.
- **History documents** (`docs/roadmap/`, `docs/assessment/`, `docs/decisions.md`, `docs/architecture/*` reports, `docs/ux/` archives, `latex/`, `specs/`) still describe the kits as they were.
- **`scholar_protocol.extraction.build_extraction_model`** has no consumer now (the matrix was its only one); left for the later pass with `scholar_graph` and PDF extraction.
- **`HF_HUB_OFFLINE` / `TRANSFORMERS_OFFLINE`** stay set in `tests/conftest.py`: Docling (the `extract` extra) loads Hugging Face models too.

## Evidence

All on this PC (Windows 11, the project venv on Python 3.14.7, synced `--extra dev --extra pdf`, so without chromadb, sentence-transformers, torch or openai). No network request, no AI spend.

| Check | Head | Result |
| :-- | :-- | :-- |
| Full Python suite, `uv run pytest -n 4 -p no:cacheprovider -o addopts="" -q` (the gate's `-q`, with the summary line kept) with a junit file | `e16464f7` | **5,336 passed, 15 skipped, 0 failed, 0 errors** (junit: 5,351 tests); 872 s (14 min 32 s) |
| First full run (before review round 1) | `6f8ab643` plus two uncommitted test edits | 3 failed: stale expectations in `tests/mcp/test_mcp_recon.py` (32 tools) and `tests/unit/test_screening_prepare_stage.py` (two `indexing` keys); fixed in `8f4daea3`; 671 s |
| PR-stage selection, `select_test_gate.py --changed origin/main --stage pr` | `e16464f7` | the full suite (run with `-n 4`, not the manifest's `-n auto`), `ruff check scripts/`, `sync_skills_bundle.py --check`, `select_test_gate.py --check`, `git diff --check`: all pass |
| `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | `e16464f7` | pass |
| `generate_contract_baseline.py --check` | `e16464f7` | "Contract baseline current"; no locked path in the diff |
| `generate_contract_schemas.py`, `generate_two_study_contract_fixture.py`, `generate_protocol_schema.py`, `generate_canonical_profile_goldens.py` (`--check`) | `e16464f7` | pass |
| `sync_skills_bundle.py --check`, `skill_portability_transform.py --check`, `validate_manifest.py`, `select_test_gate.py --check` (11 tasks, 17 areas), `uv lock --check` | `e16464f7` | pass |
| `uv build --wheel` (`NEXUS_WHEEL_ALLOW_NO_UI=1`) | `6f8ab643` (later commits change tests and texts, plus `cli.py` help text and `identity.py` and comment wording) | built; 312 files; base-install smoke as in the table above |
| `git diff --check origin/main` | final head | pass (two trailing blank lines in test files removed after the full run; whitespace only) |

**Not verified.**
- CI (Ubuntu, Python 3.12, cross-OS): not run, nothing pushed.
- The wheel with the UI export inside it, and the wheel rebuilt on the final head (the commits after `6f8ab643` touch no packaging file).
- The MCP server driven by a real MCP client; the 25-tool surface is checked through the tool manager and `--help`.
- Any real workspace: none was opened. An old workspace that has `rag/chroma_db` or `phase4/` keeps those folders; nothing reads them now, and `sync_state` no longer refreshes a stale `stats.vector_chunks` in its `project.json`.

## Review

- **Round 1** (`milestone-reviewer`, on `6f8ab643`): **CHANGES**, no P0 or P1. Ten findings: stale texts that still sent agents to `extract index` and `--index` (the pdf skill, shipped in the wheel), `extract --help`, README, the identity refusal, AGENTS, the surface matrix, `data-flow.md` and the plan; an empty evidence section; a dead tail in the extraction acceptance tests; no negative test for the removed indexing commands; decision item 1 not naming the MCP behaviour change. All ten fixed in `e16464f7`, with four of the reviewer's follow-ups (the workspace-manager skill's `phase4/` line, three comments naming Stages 6 and 9, the matrix's "8 kit APIs", the user guide's skill count). Reviewer's own checks: 878 tests of the changed files passed; every deleted test covered only removed code; the kept-code assertions in mixed files survive; the coordinator's maps agree on every path; no product path lost anything it needs.
- **Round 2:** see below.
