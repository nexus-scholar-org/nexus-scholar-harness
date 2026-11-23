# H-close-side-doors Close the side doors around the decision ledger

Branch: `dev/h/close-side-doors` (from `origin/main` `8dd7904a`) · Lane: **RELEASE** (a public API route, an MCP tool and the screening API contract change) · Status: **READY FOR PR** (review round 2 APPROVE; build accepted by the researcher 2026-11-23; items 1, 2, 4 accepted as proposed; item 3 decided as "a number is required", a follow-up not built here; `origin/main` `81f821f5` merged in, with H-remove-rag-verify)

The researcher's decision of 2026-11-23, in the coordinator session, after the project review of that day (`docs/assessment/project-review-2026-11-23.md`, section 3 points 2 and 4, evidence E4 to E7). Four doors let a decision, a setting or a spend happen around the guarded paths. Each is closed with a test that fails on `origin/main`'s code.

This branch was cut from `origin/main` `8dd7904a`; `origin/main` `81f821f5` (with H-remove-rag-verify, PR 300) was merged in on 2026-11-23: the MCP surface is now 24 tools, and the agent skill's table was renumbered on top of Part 1's.

## The four doors

### 1. The old batch decisions route

`POST /api/v1/screening/batch/{n}/decisions` (`console/api/screening.py:111`) wrote `batch_NNN_decisions.json` directly, with a caller-set `method` and a free `reviewed_by`, around the ledger. The web app no longer called it (searched `apps/research-ui/{app,components,lib}`: only the proxy's allowlist names it).

- **Removed** from the engine with its request models (`Decision`, `DecisionsBody`) and helpers. The route answers 404 and writes nothing. Decisions are recorded only through `POST /screening/decisions/events`, which accepts only a human decision.
- **Allowlist:** the entry is removed from both lists, which `tests/console/test_browser_access.py::test_the_allowlist_equals_the_development_proxys` keeps equal: `console/browser.py` (the packaged app) and the development proxy `apps/research-ui/app/api/console/[...path]/route.ts`. A browser POST to the old path is refused before the engine: 405 `CONSOLE_METHOD_REFUSED` (`test_writes_follow_the_allowlist_and_need_this_origin`) and 405 in the proxy. The proxy's unit test `apps/research-ui/tests/console-proxy.test.ts` used this path as its sample forwarded POST; with the coordinator's leave (option A, 2026-11-23), that one case now forwards `decisions/events` and asserts the old path is refused and not forwarded. That file is in the cleanup-tests session's area: the branch `dev/h/test-diet` may touch it too, and whichever merges second resolves.
- Tests: `tests/console/test_console_screening.py::test_old_batch_decisions_route_is_gone_and_writes_nothing`, `tests/console/test_screening_actions.py::test_old_drafts_route_is_gone`. Four tests of the route's own behaviour (atomic write, merge, unreadable draft, validation) and the AG-01 characterization of its request body are deleted with it. Two tests that used it only to set up a draft file now write the file directly in the same shape (`test_screening_parity_console_wrapper`; `test_screening_read_api.py::_write_draft_decisions`), so the collector's reading of that shape stays covered.

### 2. Pre-ledger MCP screening tools

Every MCP tool that screens or reconciles, at `origin/main`:

| Tool | What it does | Can it produce a decision outside the ledger? | Done |
| :-- | :-- | :-- | :-- |
| `nexus_screen_llm` | sends records to a Gemini model (default `gemini-2.0-flash`) with no consent, estimate or ceiling; on any failure falls back to the keyword heuristic and still labels the output with the model | writes proposals only (`screening_proposals.json`), but spends without consent and mislabels a fallback | **removed** (31 tools) |
| `nexus_screen` | keyword heuristic over a candidates file | no: proposals only (`screening_proposals.json`, status `PROPOSALS_ONLY`, AGT-16), never a decision file; no network | kept (decision item 1) |
| `nexus_screen_reconcile` | majority vote and Fleiss' kappa over legacy `batch_*_decisions*.json` files or a JSON map | no: returns JSON, writes nothing | kept (decision item 1) |
| `nexus_submit_proposal`, `nexus_screening_queue`, `nexus_screening_record` | the ledger-era proposal tools | no: the proposal store, never a decision | kept |

Test: `tests/conformance/test_count_freshness.py::test_mcp_tool_count_matches_documentation` pins the exact 31-name set (fails on `origin/main`, where it is 32). `tests/kits/agent/test_screening.py` (the removed tool's own tests) is deleted. `scholar_search.screening.LLMBatchScreener` now has no caller outside its module; left for a later pass.

### 3. `ai_agreed_exclusion`

Validated, journaled, shown on three screens and stated in every methods paragraph ("The AI-agreed-exclusion setting was off."); nothing acted on it.

**Refused and no longer reported, not removed.** Why not removed: the web app's Prepare, Home and Agreement screens read `settings.mode`, and their unit tests (in `apps/research-ui/tests`, owned by the cleanup-tests session) click the option and render it; workspaces may hold `mode: "ai_agreed_exclusion"` in `literature/screening/settings.json` and in `SCREENING_SETTINGS_CHANGED` journal rows. So:

- `PUT /screening/settings` with `mode: "ai_agreed_exclusion"` is refused `INVALID_OUTPUT` ("not available"), with or without the confirmation, and nothing is journaled.
- `GET /screening/settings` always answers `mode: "human_sees_every_record"`, also for a workspace that stored the old value (which is what happened: every record was seen by the reviewer). The stored file and the journal are left as they are.
- The methods paragraph no longer states the setting, and `figures` no longer carries `mode`. A re-export of a screening published before this change loses that one sentence.
- Tests: `test_screening_api_v1.py::test_settings_change_is_journaled_and_ai_exclusion_is_refused`; `test_methods_api.py::test_a_stored_ai_agreed_exclusion_setting_is_not_stated` (a workspace that stored it before: settings read "every record", the paragraph says nothing); `test_no_op_settings_rows_are_not_repeated` and the paragraph test assert the sentence is gone.
- Documents: `docs/architecture/screening-api-contract.md` (the settings row and the note on `mode`), `docs/architecture/agent_autonomy_ladder.md` §2.
- **Still offered on the Prepare screen** (decision item 2): choosing it now shows the engine's refusal.

### 4. The agent-run request

`POST /screening/proposals/runs` and `/proposals/calibrations` defaulted to `provider: "anthropic"`, `model: "claude-opus-5-5"` (the dearest model) and no ceiling (`console/api/screening_v1.py:1275-1286`, `:1457-1460`).

- No default provider or model: a request without one is refused `INVALID_OUTPUT` ("model is required: there is no default"), estimate included (it is priced by the model).
- A run or a calibration must state `cost_ceiling_usd`: a number, or `null` for no ceiling. A request without the key is refused before anything is recorded or sent. An estimate need not state it.
- **The screen keeps working:** it always sends `provider`, `model`, `effort` and `cost_ceiling_usd` (a number, or `null` when the field is blank or the model is unpriced) (`apps/research-ui/lib/screening-v1.ts:622-631`, `components/screening-proposals.tsx:376`, `:387`, `:437`, `:493`, `components/screening-pilot.tsx:142`, `:1119`, `:1159`). No web app file changed.
- Tests: `test_agent_runs_api.py::test_a_run_without_a_provider_or_model_is_refused_and_nothing_leaves` (provider, model), `::test_a_run_must_state_its_ceiling_and_an_estimate_need_not`, `::test_a_calibration_without_a_model_or_a_ceiling_is_refused`. The run tests that relied on the defaults now send them explicitly (`RUN` in `test_screening_api_v1.py`).
- `agent_runs.py:418` is unchanged: it already refuses a ceiling on an unpriced model (`CEILING_NOT_PRICED`) and an estimate above the ceiling (`COST_CEILING_REACHED`).
- Not changed: `base_url` stays free (decision item 4); the `nexus-scholar gate` measurement commands keep their `claude-opus-5-5` default (developer tools that spend only with `--yes`; `gate measure` sets a ceiling of 1.5 x the estimate by default).

## Proof that each test fails on today's code

The four changed source files (`console/api/screening.py`, `console/api/screening_v1.py`, `screening/export.py`, `scholar_agent/server.py`) were put back to `origin/main`'s version and the new and changed tests run: **10 of 10 failed** (the two route tests, the tool-count test, the settings refusal, the two methods tests, the four run and calibration tests). The files were then restored.

The allowlist, separately: with `origin/main`'s `browser.py`, `test_writes_follow_the_allowlist_and_need_this_origin` fails (the old path reaches the engine); with `origin/main`'s `route.ts`, the changed `console-proxy.test.ts` case fails (the old path is forwarded). Both pass on the branch (vitest: that file alone, 77 passed, run through a link to the main checkout's `node_modules`, whose lock file equals `origin/main`'s).

## Open

- **The ceiling half of brief item 4 is met in form, not in substance, for the screen** (decision item 3; the researcher answered on 2026-11-23 that the ceiling must be a number: a follow-up with a screen change, not built on this branch): a run must state `cost_ceiling_usd`, but `null` means no ceiling, and the screen sends `null` when its ceiling field is blank. A run from the screen with a blank field still has no ceiling, as before. It is closed in substance only if the researcher chooses item 3's alternative (a number required for a priced model, with a screen change).
- **The Prepare screen still offers AI-agreed exclusion** (decision item 2); choosing it now shows the engine's refusal. Removing the option means changing the web app's unit tests.
- Follow-ups not done here: re-record `apps/research-ui/tests/fixtures/page-engine.json` (`tests/console/_record_page_engine.py`), which still carries `figures.mode` and the removed sentence (nothing compares it with the engine); amendment notes on the FINAL UX specs that describe the sentence and the opt-in (`docs/ux/phase2-screening/final/02-prepare.md`, `07-agreement-with-agent.md`, `09-publish.md:47`, `10-export-and-methods.md:166`, `:203`); the historical UI-07 documents that describe the old route as the draft writer; `LLMBatchScreener` with no outside caller.

## Evidence

All on this PC (Windows 11, the project venv on Python 3.14.7 synced `--extra dev --extra pdf --extra rag`, as on `main`). No network request, no AI spend, no real workspace opened.

| Check | Head | Result |
| :-- | :-- | :-- |
| Full Python suite, `uv run pytest -n 4 -p no:cacheprovider -o addopts="" -q` with a junit file | `a9d01da5` | **6,569 passed, 15 skipped, 0 failed, 0 errors** (junit 6,584); 607 s |
| The same, before review round 1 | `5ecc41e6` | 6,568 passed, 15 skipped, 0 failed (junit 6,583); 775 s |
| Fails first: the four changed source files and `browser.py` at `origin/main`, the new and changed tests run | before `5ecc41e6` | 10 of 10, then the browser test: all fail on their assertions (the reviewer repeated this independently: 12 of 12); the round-1 test fails on `5ecc41e6` by reading |
| `apps/research-ui/tests/console-proxy.test.ts` alone (vitest, through a link to the main checkout's `node_modules`, same lock file as `origin/main`) | `5ecc41e6` (`route.ts` unchanged since) | 77 passed; with `origin/main`'s `route.ts`, the changed case fails |
| PR-stage selection, `select_test_gate.py --changed origin/main --stage pr` | `a9d01da5` | areas screening, console, agent-mcp, research-ui. Run: the Python suite (with `-n 4`), `git diff --check`. **Not run**: the research-ui area's typecheck, full UI unit suite, build and browser suite (the coordinator asked for the one vitest file alone; the cleanup-tests session owns those suites) |
| `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | `a9d01da5` | pass |
| `generate_contract_baseline.py --check`, `generate_protocol_schema.py --check`, `sync_skills_bundle.py --check` | `a9d01da5` | pass; no locked path in the diff |

**Not verified.**
- The web app in a browser: the Prepare screen's handling of the new refusal, and an agent run started from the screen against the stricter request (read from the code only; no web app file but `route.ts` and the one test changed).
- The full UI unit suite, typecheck, build and browser suite.
- CI.

## Review

- **Round 1** (`milestone-reviewer`, on `5ecc41e6`): **CHANGES**, documentation-level, no P0 or P1. Findings: `docs/architecture/console/SPECS.md` still listed the route as live (P2); the search skill's preflight still named `nexus_screen_llm`; a save over a stored `ai_agreed_exclusion` journaled the forced value as `before`; `sample_audit_size` left unnamed; the ceiling "required in form only" to be said plainly. All fixed or stated in `a9d01da5`, with a test for the journal fix. The reviewer confirmed: every new test fails on `origin/main` on its own assertion; no test was weakened beyond the removed code; every screen request to `/proposals/runs` and `/proposals/calibrations` sends provider, model and the ceiling key.
- **Round 2** (on `a9d01da5`): **APPROVE**. Targeted run 169 passed; baseline current.
