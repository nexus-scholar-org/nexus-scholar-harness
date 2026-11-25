# H-b8-followups The contact e-mail no longer stored in a review; the engine's restart wording; the 1.1.0b8 status lines
Branch: dev/h/b8-followups · Lane: **STANDARD** · Status: READY FOR PR, not pushed (nothing committed) · Started: 2026-11-25

Base: `origin/main` at `d60f2ef3` (PR #317, H-b8-small-faults, merged 2026-11-25). Source: the researcher's answers of 2026-11-25 (in the coordinator session) to the open items of `docs/decisions.md` "2026-11-25 — H-b8-small-faults": items 1 to 7, 9 and 10 "Accept all nine"; item 8 "Keep, now disclosed"; item 11 "Correct in a follow-up"; item 12 "Stop storing it" ("the run file and the journal record only that a contact address was set, not the address. Existing reviews keep what they already hold."). No live request, no AI spend, the app was not started, the version is unchanged, `docs/releases/1.1.0b8.md` is not edited.

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md`: one bounded behaviour change in `scholar_harness.charting.fetch` (what a look-up writes into the review, and what `GET /charting/fetch` answers for an old run), five engine refusal messages, one optional field of a presentation type in the web app, a test fixture and documentation. No Contract v1 model, schema, golden fixture, CLI flag or MCP tool changes; no route is added or removed. The baseline-locked files are untouched.

## Definition of done
- [x] **1. Item 12.** A new look-up writes no contact address anywhere in the review; its run file and journal start row say `contact_email_set: true`; an older run file that holds the address still loads and the address is not answered; the plan still shows the address on the screen.
- [x] **2. Item 11.** The five engine messages name the Settings screen first, then the environment line with its restart; the fake engine and the two FINAL specs follow.
- [x] **3. Records.** Decisions entry marked; H-b8-small-faults record merged with a Follow-up section; this record; 1.1.0b8 status lines say released.

## What changed

### 1. The contact e-mail is no longer stored in a review (item 12)
- `src/scholar_harness/charting/fetch.py` `start`: the run record (`charting/fetch_runs/<run>.json`, line 805) and the `CHARTING_FETCH_STARTED` journal row's `parameters` (line 822) carry `contact_email_set: true` instead of `email: <address>`. `require_mailto()` still runs first, so a run never starts without an address, and the address is still sent to Unpaywall and in the User-Agent (item 8, kept).
- `fetch._view` (line 1113-1115): a run file written by 1.1.0b7 or 1.1.0b8 that holds `email` is answered with `contact_email_set: true` and without the address. The file is not rewritten.
- `plan()` (line 572) still returns `email`: the screen names the address before the researcher starts a look-up (the consent of spec 03); the plan is never written to disk.
- `apps/research-ui/lib/charting-api.ts` `FetchRun`: `email?: string` replaced by `contact_email_set?: boolean` (no component read `FetchRun.email`; `components/charting-fetch.tsx:573` reads `plan.email`). `tests/charting-helpers.tsx` `runView` follows.
- Tests (`tests/console/test_charting_fetch_api.py`): `test_a_run_writes_no_contact_address_into_the_review_and_the_plan_still_shows_it` (the plan shows the address; Unpaywall was still asked with it; the run file has `contact_email_set` and no `email`; `GET /fetch` does not hold it; a byte search of every file under the workspace finds the address nowhere); `test_an_older_run_file_that_holds_the_address_still_loads_and_the_address_is_not_answered` (200, the run read, `contact_email_set: true`, no address in the answer, the file unchanged); `test_the_journal_rows_carry_the_counts_and_never_the_key` now asserts `contact_email_set` and no `email`.
- `docs/data-flow.md`: reviews written from this change on do not hold the address; look-ups run by 1.1.0b7 and 1.1.0b8 did write it into both files, and a review holding one still carries it (read, not shown, not removed). The user guide, the beta page and getting started make no claim about the stored address (checked); the public site is in another repository and was not checked.

**Readers of the two fields, found at `d60f2ef3`** (searches of `src/`, `tests/`, `apps/research-ui/{lib,app,components,tests}`, `docs/`, `scripts/`, `contracts`-named paths):

| Reader | What it reads | Effect |
| :-- | :-- | :-- |
| `charting/fetch.py` `read_run`, `current`, `_view` (1098-1137) | the whole run dict | passed to `GET /charting/fetch` and the start's 202 answer; now without the address |
| `charting/fetch.py` `_finish`, `cancel`, `_execute.update` | rewrite only the live run of this console (`live.run`) | an old run file is never rewritten |
| `charting/report.py` `_services` (182-193), the export's methods text | `parameters.providers` of `CHARTING_FETCH_STARTED` only | none |
| `console/api/charting.py` 218-259 | returns `fx.plan`, `fx._view`, `fx.current` | as above |
| web app: `lib/charting-api.ts` `FetchRun.email` (optional, typed only), `components/charting-fetch.tsx:573` (`plan.email`) | the plan's address | none; the run type now names `contact_email_set` |
| tests: `tests/console/test_charting_fetch_api.py:262` (plan), `:617` (journal); `tests/console/test_charting_export_api.py:291` (journal rows with `providers` only); `apps/research-ui/tests/charting-helpers.tsx` 272, 611 | | updated where they named the run's `email` |
| Contract v1, `contract_v1_baseline.json` `locked_files`, `contracts/schemas/v1/*`, `tests/fixtures/contracts/v1/*`, screening API fixtures, the audit event schema | none names `CHARTING_FETCH_*` or `fetch_runs` | none |

**Compatibility.**
- *Contract.* Neither the run file nor the journal row is a Contract v1 artifact, a typed model or a golden fixture (the baseline's `locked_files` list names no charting file; `git grep CHARTING_FETCH\|fetch_runs` finds only `fetch.py` and two console tests). No contract decision and no baseline regeneration is needed; `generate_contract_baseline.py --check` stays current.
- *An older build reading a new review.* 1.1.0b8's `_view` returns the run dict as it is; the new `contact_email_set` is one more key and its screen never read the run's `email` (only `plan.email`). Its export reads `providers`. Nothing is refused, misread or overwritten.
- *This build reading an old review.* The old `email` key is read without error and answered as `contact_email_set: true` (test above); the file and the journal are not changed (the journal is append-only).
- *Format version.* `CURRENT_FORMAT` (`src/scholar_harness/workspace/format.py`) is not raised: the rule in `DEVELOPER_COMPASS.md` ("a change that an older build would refuse, misread or overwrite") is not met: no value an older build interprets changes, no file changes what a reader counts or reports, and no file is rewritten by another reader.

### 2. The restart wording in the engine (item 11)
Each now names the Settings screen first (the contact e-mail and the OpenAlex key are saved there and apply at once), then the environment line with its restart, as `require_mailto` in `charting/fetch.py` does since #317:
- `console/api/discovery.py` `_require_mailto`, `console/api/recon.py` `_require_mailto`, `recon/session.py` (the probe and the follow-ups): "A search needs a contact email for the literature databases. Save it on the Settings screen (it applies at once), or set SCHOLAR_MAILTO for the console (environment or .env) and start it again."
- `console/api/discovery.py` `_require_openalex_key`: "OpenAlex needs an API key. Save it on the Settings screen (it applies at once), or set SCHOLAR_OPENALEX_KEY for the console (environment or .env) and start it again, or leave OpenAlex out of this run."
- No Python test pinned them. `apps/research-ui/tests/fixtures/discovery-engine.ts` (the fake engine; four places) follows.
- FINAL specs: `docs/ux/phase1-discovery/final/07-states.md` (the `MAILTO_NOT_SET` row now quotes the screen's words of `lib/screening-states.ts`, "Add it in Settings", names the Settings link and gives the engine's new text) and `docs/ux/phase0-inception/final/02-explore.md` (the `MAILTO_NOT_SET` body no longer says there is no setting in the app). Neither is baseline-locked.

### 3. Records
- `docs/decisions.md` "2026-11-25 — H-b8-small-faults": heading and the researcher's four answers; items 13 (the field name and shape) and 14 (what the engine answers for an old run) PROPOSED.
- `docs/roadmap/milestones/H-b8-small-faults.md`: merged (PR #317, `d60f2ef3`, 12 checks passed and 1 skipped on `05ea7316`); a Follow-up section.
- 1.1.0b8 released on 2026-11-25 (`git tag -l v1.1.0b8`; `git log -1 v1.1.0b8`: `1985267b`, the merge of PR #316): `AGENTS.md` (the released beta is `1.1.0b8`), `docs/roadmap/milestones/R-1.1.0b8.md` (status RELEASED with the three workflow runs; the `attach` job ran on the tag), `docs/roadmap/production-plan.md` (progress line and §6 row 7). `README.md` and `docs/README.md` already said released and are not changed.

## Independent review

One round on the uncommitted tree: **APPROVE**, one P2 and three P3. The reviewer tried to find the address on disk under a workspace after a look-up (run file at every write, both journal events, the manifest and attempt rows, the export) and in the app's log, and found none; it confirmed from the code at the tag that 1.1.0b8 reads a new run file, that `CURRENT_FORMAT` need not change, and that no contract model, schema or locked file names the event or the field. Repaired by the coordinator on the same tree:

| # | Finding | Done |
| :-- | :-- | :-- |
| 1 | P2: the two messages in `recon/session.py` said a saved address "applies at once", which is true only inside the console; they are seen by the MCP server and the command-line wizard | Reworded: "Save it on the Settings screen, or set SCHOLAR_MAILTO (environment or .env). The console applies a saved address at once; an MCP server or a command already running reads it when it next starts." |
| 2 | P3: `docs/ux/phase0-inception/final/02-explore.md` held the engine's words in the screen's body cell | The cell holds the card's words; the engine's text is in the note |
| 3 | P3: "does not show the address" is true for the screens only; the journal route answers old rows as stored | Said so in `docs/data-flow.md` and in decision item 14 |
| 4 | P3, outside this change: the search HTTP cache keeps each request with its headers and address, so it holds the contact e-mail | One sentence added to `docs/data-flow.md`. **The behaviour is not changed**; whether the cache should keep the address is a question for the researcher |

After these: the 15 test files naming `MAILTO_NOT_SET`, the fetch tests and the count check were run again with `-n 4`: 456 tests, 0 failures, 0 skipped (junit); the gate table below is the builder's run before these wording repairs. The reviewer did not check PyPI, the GitHub release or the workflow run numbers (no network), and did not run `lint:ui` or the full suites.

## Gates
All on the uncommitted working tree of `dev/h/b8-followups` (base `d60f2ef3`), 2026-11-25, Windows 11, Python from the worktree's venv. Python counts read from `--junitxml` files.

| Stage | Command | Result |
| :-- | :-- | :-- |
| inner | `uv run pytest tests/console/test_charting_fetch_api.py -k "contact or older_run or journal_rows or plan_sends or interrupted"` | 7 passed |
| selector | `uv run python scripts/select_test_gate.py --changed --stage pr` (base `origin/main` = `d60f2ef3`) | areas `console-charting,console-discovery,console-inception,recon,research-ui`; the commands below |
| pr | `uv run python scripts/suite_lock.py -- uv run pytest tests/console tests/authority tests/inception tests/recon tests/unit/test_discovery_stage.py tests/kits/agent/test_mcp_assistant.py tests/kits/agent/test_mcp_workspace_proposals.py tests/kits/search/test_provider_resilience.py tests/pipeline/test_golden_recon_cassette.py tests/mcp/test_mcp_recon.py tests/kits/agent/test_mcp_recon_adapter.py tests/unit/test_recon_adapter_characterization.py -q -n 4 --dist worksteal --junitxml=…` (the union of the five pytest lines the selector named) | **2 143 tests, 0 failures, 0 errors, 2 skipped**, exit 0 (407 s) |
| pr | `npm --prefix apps/research-ui run typecheck` | exit 0 |
| pr | `npm --prefix apps/research-ui run lint:ui` | 1 file, 76 tests passed |
| pr | `uv run python scripts/suite_lock.py -- npm --prefix apps/research-ui test` | 120 files, 1 395 tests passed |
| docs, fixtures | `uv run pytest tests/conformance/test_count_freshness.py tests/console/test_screening_api_contract.py --junitxml=…` | 10 tests, 0 failures |
| lint | `uv run ruff check scripts/`; `uv run ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | both "All checks passed!" |
| contract | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current"; nothing regenerated |
| checks | `generate_protocol_schema.py --check`; `sync_skills_bundle.py --check`; `select_test_gate.py --check`; `check_workflows.py`; `uv lock --check`; `git diff --check` | in sync; OK (9 skills); OK (11 tasks, 24 areas, 4 stages); OK (4 workflows); exit 0; clean (only Git's LF/CRLF notices) |

## Decisions
`docs/decisions.md`, entry "2026-11-25 — H-b8-small-faults": items 1 to 10 ACCEPTED 2026-11-25 (8 as built), 11 and 12 decided and built here, 13 and 14 PROPOSED.

## Not verified
- **The screens in a running app.** The Charting run card and the Discovery and Explore refusal cards were not looked at; the app was not started.
- **A real look-up.** The run was made against the stub PDF host and fake lookup clients of the console tests; no live service.
- **1.1.0b8 itself reading a new run file.** Reasoned from its code (the same `_view` and screen as `d60f2ef3`), not run.
- **The MCP server's wording.** `recon/session.py` is also reached from the MCP server (`scholar_agent/server.py`); a Settings save applies at once to the console's process, and to a separately started MCP server only when it next reads its settings. The message names "the console", as before.
- **The public site** (`nexus-scholar-org/nexus-scholar-site`) was not checked for a sentence about the stored address.
- **The full Python suite** was not run (CI runs it); the areas the selector named were.
