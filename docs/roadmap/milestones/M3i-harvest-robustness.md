# M3i-harvest-robustness: a harvest says which stage it is in, and can be finished
Branch: dev/m3i/harvest-robustness · Lane: **RELEASE** · Status: IN PROGRESS · Started: 2026-11-17

Source: the strict acceptance run of 2026-11-13 (installed wheel, second PC). A browser harvest `run_001` returned 1,074 records and 1,050 works, and the Hand-off said "There is nothing to hand off yet". Accepted by the researcher on 2026-11-15 as its own fix before the M10b build (answer R5; `docs/roadmap/milestones/M10b-proposals-checks.md` on the local branch `dev/m10b/proposals-checks`, and `docs/ux/shared/final/04-next-step.md` there, "Order of work" and "What the engine cannot tell apart today").

**Lane.** RELEASE, from `docs/architecture/test_gate_policy.md` ("public API, CLI, or MCP semantics" and "acceptance publication"): the milestone adds a route (`POST /api/v1/discovery/runs/{run}/prepare`), a `preparation` object on three public answers (`GET /discovery/runs`, `/runs/{run}`, `/handoff`), two refusal codes, and a refusal on the hand-off accept while a harvest's preparation is unfinished. No Contract v1 model, schema or golden fixture changes; the baseline check runs in every commit that touches `src/`.

## What was wrong (re-verified at `97768cdc` by the `phase-auditor`, 2026-11-17)
One harvest job runs four stages: search, deduplication, abstracts, verification.
- (a) The run is archived as published (`raw_published: true` in `legs.json`) right after the search (`pipeline/discovery.py:473, 500-512`), before the three later stages.
- (b) Only verification writes `literature/verified.json` (`pipeline/verification.py:172`), which the Hand-off and the accept need. The file carries no run id: after a run 2 that died after its search, the Hand-off showed run 1's works under run 2's name and the accept froze them as run 2's.
- (c) Stop is read by the search only (`coordinator.py:584-600`); the three later stages never look at it, and the cancel route answers a job that then ends `succeeded`.
- (d) A job that dies after the search (an exception, or the console closed: jobs are in memory only) leaves no trace on disk. After a reload the Harvest screen reads "The harvest is finished" and the Hand-off "There is nothing to hand off yet".

## Definition of done
- [x] **D1 Stage marker.** `literature/search_runs/run_NNN/pipeline.json` is written when the search is published and rewritten, atomically, as each later stage ends; it names the run that produced `verified.json` (`verified_run`) and how the preparation ended. Test: `tests/pipeline/test_harvest_marker.py`, `tests/console/test_harvest_preparation_api.py::test_pipeline_marker_written_by_each_stage`.
- [x] **D2 A failure after the search is on disk and on the run.** An exception in deduplication, abstracts or verification ends the marker as `FAILED` at that stage, journals the abort, and `GET /discovery/runs`, `/runs/{run}` and `/handoff` carry `preparation` with `state: "failed"`. Test: `test_a_run_that_dies_after_search_says_so`.
- [x] **D3 Stop between stages.** A stop requested after the search ends the job `cancelled` before the next stage starts; the marker ends `STOPPED` at that stage; nothing later is written. Test: `test_a_stop_after_the_search_is_honoured_before_the_next_stage`.
- [x] **D4 Finish preparing without a new search.** `POST /discovery/runs/{run}/prepare` runs the remaining stages from the run's saved records; no database is searched; `verified.json` equals, byte for byte, the file of an uninterrupted run on the same records. A run made before this milestone (no marker) can be finished too. Refusals typed. Tests: `test_finish_preparing_resumes_from_the_marker_without_a_search`, `test_finished_preparation_equals_an_uninterrupted_run`, `test_a_run_without_a_marker_can_be_finished`, the refusal tests.
- [x] **D5 After a restart.** A new console process (no job in memory) reads the same `preparation` from the marker: `interrupted` at the first unfinished stage. Test: `test_after_a_restart_the_marker_answers`.
- [x] **D6 Hand-off and accept.** While the newest published run's preparation is unfinished, the Hand-off answer says so (also when an earlier run's `verified.json` is still on disk) and the accept is refused by the engine with a typed code. Tests: `test_the_handoff_never_offers_an_earlier_runs_works_as_a_later_runs`, `test_the_accept_refuses_an_unfinished_preparation`.
- [x] **D7 Harvest screen.** It names the real stage while a job runs, says plainly when the preparation is unfinished, failed or stopped (also after a reload), offers "Finish preparing this corpus" and keeps Stop in every stage. Copy in en, fr and ar. Tests: `apps/research-ui/tests/discovery-harvest.test.tsx`, Playwright `tests-browser/discovery.spec.ts`.
- [x] **D8 Hand-off screen.** When nothing can be handed off because the preparation is unfinished, it says that and links to the action, instead of "There is nothing to hand off yet". Tests: `apps/research-ui/tests/discovery-handoff.test.tsx`, Playwright.
- [x] **D9 Specs.** `docs/ux/phase1-discovery/final/03-harvest.md` and `08-handoff.md` amended for the above; `07-states.md` lists the two new codes.
- [x] **D10 Decisions.** Every architectural choice is in `docs/decisions.md` as proposed, for the researcher.
- [ ] **D11 Gates.** `/gate pr` once on the final executable commit, `generate_contract_baseline.py --check`, both ruff commands, `git diff --check`, and the `milestone-reviewer` verdict, recorded below.

## Findings fixed
The four points were re-verified by the `phase-auditor` at `97768cdc` (all CONFIRMED; (d) confirmed for a closed console and for a reload, and partly masked while the Harvest page stays open on a live console, where the job's `DISCOVERY_FAILED` card showed until the next reload). It added one finding, here (b2). Each engine test was run against the unchanged engine first (16 of 16 in `tests/console/test_harvest_preparation_api.py` failed), each screen test against the unchanged screens (15 of 19 in `apps/research-ui/tests/discovery-preparation.test.tsx` failed; the other four test the new state cards and an unchanged case).

| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| (a) the run is published right after the search, with no record of the later stages | `test_harvest_preparation_api.py::test_pipeline_marker_written_by_each_stage`, `::test_a_run_that_dies_after_search_says_so` | `FileNotFoundError: ...run_001\pipeline.json`; `KeyError: 'preparation'` | yes |
| (b) only verification writes `verified.json`; nothing says it is missing | `::test_a_run_that_dies_after_search_says_so`, `::test_the_accept_refuses_an_unfinished_preparation` | no marker, no `preparation`; the accept answered `NOTHING_STAGED` | yes |
| (b2) an earlier run's `verified.json` is shown and accepted as a later run's (auditor) | `::test_the_handoff_never_offers_an_earlier_runs_works_as_a_later_runs`, `::test_the_engine_accept_refuses_while_the_marker_has_no_end` | `KeyError: 'preparation'`; the hand-off reported `run_002` with run 1's works and `corpus.state` `STAGED` | yes |
| (c) Stop is ignored after the search | `::test_a_stop_after_the_search_is_honoured_before_the_next_stage`; `tests/pipeline/test_harvest_marker.py::test_the_stop_is_read_before_each_stage` | the cancel answered a job that ended `succeeded` with `PENDING_CORPUS_ACCEPT` | yes |
| (d) a job that dies after the search leaves Harvest "finished" and the Hand-off "nothing to hand off" | engine: `::test_after_a_restart_the_marker_answers`, `::test_a_preparation_that_never_ended_reads_as_interrupted`; screens: `discovery-preparation.test.tsx` "says a harvest whose checks failed is not prepared…", "after a restart (no job in memory)…", "says the corpus is not prepared and links to the action…"; Playwright "M3i: the hand-off of an unfinished harvest…" | engine: `KeyError: 'preparation'`; screens: the old headings "The harvest is finished…" and "There is nothing to hand off yet." | yes |
| no way forward except a new search | `::test_finish_preparing_resumes_from_the_marker_without_a_search`, `::test_finished_preparation_equals_an_uninterrupted_run`, `::test_a_failed_deduplication_is_finished_from_the_saved_records` | `404` on `POST /discovery/runs/run_001/prepare` | yes |

## Decisions
All in `docs/decisions.md`, 2026-11-17 "M3i: the harvest stage marker, finishing a preparation, and stop between stages". Every item is **proposed**, built as its recommended option, and the researcher's to confirm or overrule:
1. what the marker holds (fields added to the accepted text; the engine's own stage names);
2. `raw_published` keeps its meaning; "ready" is a new fact (`preparation.state`);
3. where finishing starts (the marker, then `deduped.json` or the run's `raw.json`; abstracts are run again; only the newest published run);
4. a kit function to read saved records back, field for field;
5. runs made before the marker are not guessed at;
6. Stop is read between stages only; verification is never interrupted;
7. an unfinished preparation is never accepted (`corpus_status`, the hand-off, the accept); the CLI `accept-corpus` is not guarded;
8. two refusal codes;
9. journal rows for a failure, a stop and each finish attempt;
10. where the action lives on the screens.
The lane (RELEASE) is stated at the top with its reason.

## Evidence
Base for every selection: `origin/main` (`97768cdc`). The local `main` branch of the main checkout is 14 commits behind and was not touched (another session may be using that folder), so the selector was run with `--changed origin/main`.

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| fail-before (engine) | `97768cdc` + tests only | `uv run pytest tests/console/test_harvest_preparation_api.py` | 16 failed (`KeyError: 'preparation'`, no `pipeline.json`, a cancelled job that ended `succeeded`, 404 on the finish route) | 35 s |
| fail-before (screens) | `274c58c0` screens + new tests | `npx vitest run tests/discovery-preparation.test.tsx` | 15 failed, 4 passed (the 4 test the new state cards and an unchanged case) | 20 s |
| inner | working tree before `274c58c0` | `uv run pytest tests/console tests/pipeline tests/unit tests/test_handoff.py tests/kits/search -m "not slow" -n auto` | 1667 passed, 4 skipped | 2 m 48 s |
| checkpoint (D1 to D8, one run; `test-gatekeeper`) | `d6156704` | `select_test_gate.py --changed origin/main --stage checkpoint`, every command: `tests/console tests/authority`; `tests/pipeline tests/unit` and the e2e search-screen test; `tests --ignore=tests/kits`; the search kit set; `npm run typecheck`; `npm test`; `tests/console tests/kits/search tests/pipeline` | 697 passed, 1 skipped; 823 passed, 3 skipped; 3051 passed, 8 skipped; 408 passed; tsc clean; vitest 44 files, 631 passed; 963 passed, 4 skipped. `generate_contract_baseline.py --check` current; both ruff commands clean; `git diff --check origin/main...HEAD` clean | 15 min |
| contract generators | `d6156704` | `generate_contract_baseline.py`, `generate_contract_schemas.py`, `generate_two_study_contract_fixture.py`, `generate_protocol_schema.py`, each `--check` | all exit 0 | 1 min |
| browser, new tests only | working tree before `d6156704` | `npx playwright test tests-browser/discovery.spec.ts -g "M3i"` | 30 of 32 passed; the 2 failures were one test's own assertions (a trailing slash in an address pattern, then a list the screen clears when a job ends), both corrected; the whole browser suite runs in the PR gate | 1 m 36 s |
| live look, real engine and real screens, no network | `d6156704` | a console on a scratch workspace outside the repository, with in-memory doubles for the databases, the abstract client and the verifier (`scratchpad/serve_doubles.py`), and `next dev` | a harvest whose verification raised read "The search finished, but preparing the corpus failed." with the step and the engine's message; after the console process was killed and started again the Harvest and the Hand-off read the same from `pipeline.json`; a second harvest stopped during abstracts ended "stopped before Checks" and the accept answered `PREPARATION_UNFINISHED` while run 1's `verified.json` was still on disk; Finish ran abstracts and checks and the Hand-off opened; en, fr and ar rendered; no console error | by hand |

## Deferred
None of these is needed for the definition of done; each is a follow-up for the researcher to order.
- **Deduplication off the event loop.** It is one synchronous call; for a large corpus the console may not answer while it runs. Not measured (decision item 6).
- **Stopping inside a stage.** Stop is read between stages; abstracts and verification each run to their end. A stop during the last stage has no effect, and the screen says so.
- **The console's shutdown wait.** Closing the console asks every job to stop and waits 30 s; a stage that takes longer is cut off and the run reads `interrupted` (it can be finished).
- **A checkpoint for abstracts.** Abstracts are fetched again when a harvest is finished after a failed verification (decision item 3).
- **The CLI.** `nexus-scholar accept-corpus` is not guarded against an unfinished preparation (decision item 7), and there is no CLI command to finish a harvest; both are browser-only today.
- **Runs made before the marker.** For those, an earlier run's `verified.json` cannot be told from the run's own (decision item 5).
- **The Hand-off does not poll** while a preparation runs; "Check again" re-reads it. The M10b bar is the planned place for a live line.
- **The finished Harvest view does not keep the list of steps** once a job ends (as before this milestone); the `preparation.stages` the engine now sends could feed it.
- **The Import step and screening Home** show an unfinished harvest as an empty corpus, as before; the Import accept shows the typed refusal. M10b replaces that accept with a link to the Hand-off and adds the bar.
- **Status lines.** The plan's M10a row still reads "in progress" (merged 2026-11-17, PR #233); the strict-run runbook does not yet say how to recover the stopped run. Not changed here.

## Release note (for the next version's notes; no release file exists for it yet)
Discovery: a harvest now says which step it is in. If the steps after the search (duplicates, abstracts, checks) fail, are stopped, or the console is closed while they run, the Harvest and Hand-off screens say so instead of "nothing to hand off", and **Finish preparing this corpus** completes them from the saved records without a new search. Stop works in every step. The accept refuses a corpus whose preparation is unfinished.

## Not verified
- **No human run and no live database.** Every test and the live look used recorded or in-memory doubles. The real abstract client and the real verifier have not run on records read back from `raw.json` or `deduped.json`; the byte-for-byte equality is proven on the doubles' records and, for each field of the record, in the kit's unit test.
- **The strict run's workspace** (second PC, `run_001`, 1,074 records, no marker) was not touched. By the tests it should read "The search finished, but the corpus was not prepared" and finish from `raw.json`; that folder itself was not tried.
- **Size.** Nothing was run at 1,000 records or more; how long the console stays silent during deduplication is unknown.
- **The installed wheel.** No wheel was built or installed; the screens were exercised in `next dev` and in the production build Playwright starts, not through `nexus-scholar ui`.
- **Other platforms.** Windows only, Python 3.12; the CI matrix runs on the PR.
