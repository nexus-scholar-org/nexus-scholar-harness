# H-screening-read-performance

Status: **BUILT 2026-11-23; items 6 to 23 accepted by the researcher the same day; push, PR and merge at 12 of 12 approved** (branch `dev/h/screening-read-performance`; see "Build 2026-11-23" below). Specification: questions 1 to 5 answered by the researcher on 2026-11-22, each as recommended; amended 2026-11-23. Lane: **RELEASE** (question 2: results are kept between requests, a store in front of the checks that guard publication).

Findings it answers: 47 (`docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md`), and the researcher's own reading that the engine, not the page, is slow.

## What was measured

Workspace: the sensor-stress review (2,176 records harvested, 1,062 screened in 54 batches, about 1,100 decision events, published). App built from `main` `76c445ef`; profile run on a copy of the workspace with the source at `main` `21a4e6a3`, on the researcher's PC. Nothing was written to the workspace.

**In the running app, Screening home:** the document loads in 0.1 s; the last of its eight API answers arrives at 9.8 s. The routes are ordinary (non-async) functions doing Python work, so under the interpreter lock they finish one after another although the page sends them together.

| Route | Alone, in the app | In the profile run | Files opened per call |
| :-- | --: | --: | --: |
| `GET /review/next-step` | 3.9 s | 4.9 s | 3,466 |
| `GET /workspaces` | 2.7 s | not profiled | not counted |
| `GET /screening/prisma/preview` | 2.5 s | 2.7 s | 3,302 |
| `GET /ui/publication-status` | 2.4 s | 3.3 s | 3,320 |
| `GET /screening/corpus` | 1.0 s | 1.0 s | 12 |
| `GET /screening/summary` | 0.5 s | 0.4 s | 116 |
| `GET /screening/agreement` | 0.3 s | 0.3 s | 61 |
| `GET /screening/ui/batches` | 0.2 s | 0.2 s | 325 |

A second call takes as long as the first: nothing is kept between requests.

## Where the time goes

1. **The decision log is reloaded once per batch.** `screening/events.py::stale_projections` calls `projection_is_current` for each of the 54 decision files; each call reads `project.json`, then `project_batch`, which calls `load_context` and `read_events` afresh. One call of `/ui/publication-status` therefore reads `protocol.json` and `project.json` 56 times each, the artifact registry and each artifact file 54 times, and parses about 60,600 JSON lines for a log of about 1,100 events. `screening_currentness` → `export.load_published` → `_check_decisions_unchanged` → `stale_projections` is the whole 3.2 s of that route.
2. **The latest decision of a record is found by scanning every event.** `events.heads` filters the full event list for one study; it ran 4,248 times in one `/review/next-step` call (about 6 million dictionary reads, 1.8 s).
3. **A frozen corpus is rebuilt on every call.** `corpus_accept.corpus_status` → `preview_staged` re-parses the five staged exports (2,181 records) and re-runs `scholar_search.dedup.Deduplicator` (22,183 pair checks), about 1 s, for a corpus accepted days earlier.
4. **The same work is repeated within one page.** `console/next_step.py::build_workspace` computes the currentness (3.2 s) and the corpus view (3.1 s under the profiler) that the page also requests separately; Screening home requests `/screening/corpus` twice.

**How much is disk.** In the 3.2 s currentness check: opening and reading files about 0.85 s (3,320 opens), JSON decoding about 1.0 s, the rest Python logic. Disk is about a quarter here; with antivirus scanning each open, or a slower disk, it would be more. One read per file removes it either way.

## Proposal

No route changes its answer. No Contract v1 file changes. The checks that guard publication keep comparing the same bytes.

1. **One load per request.** `stale_projections` (and `project_batch` beneath it) take an optional loaded context and event list; the callers load them once and pass them down. The projection of each batch is computed from the one event list.
2. **An index for the latest decision.** `heads` and `winning_event` read from a per-(study, screener) index built once from the event list; the functions keep their signatures for other callers.
3. **The accepted corpus is read, not rebuilt.** Once a corpus snapshot is accepted, `corpus_status` answers from the snapshot and its acceptance record; the staged exports are re-parsed and de-duplicated only while no snapshot is accepted, or when a staged file changed since.
4. **Results kept between requests (question 2).** A small in-process store per workspace, keyed by the names, sizes and modification times of the files a result was computed from (the event logs only grow; the decision files and the protocol are rewritten atomically). A result is reused only when every key matches; otherwise it is recomputed. Never written to disk.
5. **The page.** Screening home asks for the corpus once; the next-step bar and the page share the publication status; each screen shows a loading state with its headings in place while the engine answers (finding 47's blank page).

## Definition of done (proposed)

1. A fixture of the sensor-stress size (generated: 54 batches, 1,062 decided records, about 1,100 events) on which `/ui/publication-status`, `/review/next-step` and `/screening/prisma/preview` each open at most 150 files; the test fails on today's code (about 3,300).
2. On that fixture each of those three routes answers in under 0.5 s on the researcher's PC, recorded in the build record; the test asserts the file count, not the time (a time limit would be one more test that fails under load).
3. Every existing test of currentness, projection, conflicts and publication passes unchanged; a new test changes one decision event between two calls and sees the second call report the change (question 2's store must not hide it), and another edits a decision file by hand and sees it reported stale.
4. `/screening/corpus` on an accepted corpus does not call the de-duplicator (a test double counts the calls); on a staged, unaccepted corpus it still does.
5. Screening home sends `/screening/corpus` once; a vitest test counts the requests.
6. A before-and-after table of the eight routes on a copy of the sensor-stress workspace, in the build record.

## Questions closed (2026-11-22)

Asked in the main session, one by one; each answered as recommended. Decision: `docs/decisions.md`, "2026-11-22 — H-screening-read-performance".

1. **Scope: screening's read routes and the next-step bar now.** `/workspaces`, Charting and Discovery are measured first and fixed in a second part if they show the same pattern. *Not chosen:* everything in one build.
2. **Results are kept between requests**, keyed by the names, sizes and modification times of the files they came from. Known cost: a store in front of the publication check, so the lane is RELEASE and the review looks at it specifically. *Not chosen:* per request only, then measure.
3. **Display routes trust the store; Approve and Publish always recompute from disk.** Known cost: a file rewritten by hand with the same size inside one tick of the clock is not noticed by a display route. *Not chosen:* a content-hash key.
4. **Requests keep queuing**; no combined route. *Not chosen:* one "screening home" route.
5. **The loading state is headings and empty cards**, with the sentence the page already has; no animation. *Not chosen:* an animated skeleton.

## Amendment 2026-11-23: the study's findings, and a wider scope

Accepted by the researcher on 2026-11-23 (asked in the main session; the answer was to go with its recommendation). Source: a read-only study by a second session on a copy of the same workspace, `slow-loading-study-2026-11-22.md` in the sessions' shared notes folder (not in the repository). Its times are about twice those above, because other sessions were running test suites on the PC while it measured, and it reports run-to-run noise of up to two times; the proportions are what it is used for here.

**What it adds**

- **`GET /review/next-step` is sent by every page** (the next-step bar in the app shell) and was 4.6 to 11.3 s across its runs. No page is fast on this review, whatever it shows.
- **Page totals, requests one after another (its medians):** Export 21.9 s, Publish 18.1 s, Charting one study 17.7 s, Screening home 14.8 s, Charting table 12.4 s, Workspaces 11.0 s, Triage first record 10.9 s.
- **Charting is slow too:** `GET /charting` about 5 s and 1.28 MB; `GET /charting/records/{id}` about 5 s; the one-study view requests the whole table again on each move to another study.
- **Requests a page does not need or repeats:** `/screening/corpus` is sent by every screening page's step bar and again by some pages; Publish sends one batch-review request per batch (54); the pilot page asks for the summary and the criteria twice; Export runs three slow checks in a row.
- **Time split of the currentness check:** file open and read about 24%, JSON decoding about 32%, the project's own logic about 23%, other about 20%, hashing and validation under 1%.

**Experiments** (monkeypatched in its own scripts; each route's answer checked byte-identical; medians, noisy)

| Trial | Result |
| :-- | :-- |
| Context and event log loaded once per request | publication status 7.3 s to 1.4 s (a later pass 2.5 s to 0.5 s); next step 11.3 s to 3.5 s; workspaces 4.6 s to 1.4 s. The largest effect |
| The corpus view kept (what skipping the rebuild saves) | next step 11.3 s to 4.7 s |
| An index for the latest decision | summary 0.66 s to 0.40 s; no reliable gain on the heavy routes |
| Load-once and the index together | publication status 0.74 s; next step 1.75 s on one pass |
| A C-backed JSON parser (`orjson`) | no reliable gain at route level (one pass faster, the next within noise). The standard parser already runs in C; a micro-benchmark on the event log gave 23.7 ms to 13.3 ms per pass, an estimate |
| An array library (numpy) | not applicable: the work is files, JSON, strings and dictionaries |
| The duplicate detector | compares titles with the standard library's pure-Python `difflib.SequenceMatcher`; no C string library is imported. It matters only while a corpus is not yet accepted |

**What changes in this specification**

1. **Order of work.** The next-step bar comes first: it must not recompute the publication check and the corpus view on every page. Then proposals 1 to 4 above.
2. **Scope (replaces closed question 1's "measured first" for Charting).** `GET /charting` and `GET /charting/records/{id}` are in scope, with the same load-once repair; the table's 1.28 MB answer is reduced where the page does not use what it carries (to be listed in the build's own choices). `/workspaces` and the Discovery frame's `/discovery/checks` (2.4 s on every Discovery page) are in scope for load-once. The duplicate detector is not: a C string-matching library is a later, separate decision.
3. **What pages ask for.** The step bar's corpus request is shared with the page's own, and not sent by pages that do not show it; Publish reads its batch reviews in one request (a new read route, answering what the 54 answer today); the one-study view does not request the whole table on each move; the pilot page asks for the summary and the criteria once.
4. **Definition of done, added.** (7) No page of Screening, Charting or Workspaces sends the same GET twice on load (a vitest test per page counts requests). (8) `GET /review/next-step` opens at most 150 files on the fixture of DoD 1. (9) The before-and-after table of DoD 6 covers every page listed above, measured with nothing else running on the machine, three passes each.

Closed questions 2 to 5 stand as answered.

## Not verified

- The estimate "under a second" comes from the profile, not from a changed engine.
- ~~`/workspaces`, Charting, Discovery and Inception were not profiled. Triage's per-record routes were not timed.~~ Measured by the study of 2026-11-22 (amendment above), on one workspace, under load from other sessions; a cold file cache was not measured.
- The study's first probe listed the researcher's real workspaces folder through `/workspaces` and `/inception/drafts` before it was pointed at the copy; it reports that nothing there was opened or written.
- One workspace, one machine, one run of each measurement (three repeats per route in the profile run; two in the app).
- Whether the artifact registry reads can share one load was not read in the code; the count comes from the open-file tally.

## Build 2026-11-23

Branch: `dev/h/screening-read-performance` (from `origin/main` `ac6d29d8`) · Lane: **RELEASE** · Status: **READY FOR PR, not pushed** (`milestone-reviewer` APPROVE, round 3; decision items 6 to 23 PROPOSED) · Built in a session started by the main session; the researcher approved the start on 2026-11-23.

**What was built**, in the amendment's order:

1. **The next-step bar no longer recomputes on every page.** Its route, and every route that shows a state, runs inside the store (`src/scholar_harness/screening/read_store.py`, `display_route`); the publication check, the corpus view and the summary it needs are kept between requests.
2. **One load per request** (proposal 1). `events.stale_projections` reads the context, the event log and `project.json` once (at the first decisions file that claims the log) and each decisions file once; `project_batch` and `projection_is_current` take them as optional arguments. Inside a display route each file is opened once per request.
3. **An index for the latest decision** (proposal 2). `events.EventIndex`, a tuple with its (study, screener) groups and its ids built once; `heads`, `winning_event`, `conflicts` and the supersession chain read it when given one, and keep their signatures. `project_batch` and the screening routes' `_state` use it.
4. **The accepted corpus is read, not rebuilt** (proposal 3). `corpus_accept.corpus_status` answers from the snapshot and its import manifest when it is certain they are what the staged files would give (decision item 11); otherwise, and always while nothing is accepted, it parses and de-duplicates as before. The de-duplicator is not changed.
5. **Results kept between requests** (proposal 4, questions 2 and 3). Keyed by the name, size and modification time of every file under the workspace (six top-level folders aside, item 7); kept only if the key did not change while computing; never on disk. Approve, Publish (collect), export, the methods paragraph and every write read the disk.
6. **The page** (proposal 5). The request helper shares a GET between readers of the same address that start in the same synchronous run, one render's effects (Screening home's corpus is asked once); a read after a write always sends its own; Publish reads every batch review in one new request (`GET /screening/ui/batches/review`); the screening pages show their name, their sentence and empty cards while they wait, with no animation.
7. **The amendment's routes.** `/workspaces`, `/charting`, `/charting/records/{id}`, `/discovery/checks` and `/discovery/handoff` run inside the store; the charting table's rows leave out `abstract`.

**The fixture.** The researcher's review was not read. `tests/console/_sensor_stress.py` builds a stand-in through the engine's own paths: five exports staged and accepted (2,181 records, 1,062 studies), 54 batches, 1,062 decisions and 38 changed ones (1,100 events), projected, approved, published (about 45 s). On today's code its counts are the review's: 3,320 files opened by `/ui/publication-status` (review: 3,320), 3,463 by `/review/next-step` (3,466), 3,301 by `/screening/prisma/preview` (3,302).

### Definition of done

| # | Item | State | Evidence |
| :-- | :-- | :-- | :-- |
| 1 | ≤ 150 files for `/ui/publication-status`, `/review/next-step`, `/screening/prisma/preview` on the fixture; fails on today's code | **Met** | `tests/console/test_read_performance.py::test_a_read_route_opens_at_most_150_files_on_the_sensor_stress_fixture` (store empty, first call): 127, 138 and 115 files. On `ac6d29d8` the test failed with 3,320, 3,463 and 3,301 (commit `71430303`, run before the change) |
| 2 | Under 0.5 s each on the researcher's PC, recorded | **Met on the fixture, first call with the store empty**: 430 ms, 403 ms and 220 ms (25, 61 and 76 ms when called again); on `ac6d29d8` 2,138, 3,340 and 2,515 ms. Measured on this PC (the researcher's), not on the real review | table below |
| 3 | Existing currentness, projection, conflict and publication tests pass unchanged; a changed decision event between two calls is reported; a decision file edited by hand is reported stale | **Met** | no existing Python test changed in these areas (the Publish vitest and Playwright fake engines gained a `/ui/batches/review` answer, no assertion changed); `test_a_decision_changed_between_two_calls_is_reported_by_the_second` (projected and not projected), `test_a_decision_file_edited_by_hand_is_reported_stale`, `test_a_same_size_hand_edit_with_a_new_modification_time_is_reported_stale`, `test_approve_and_publish_recompute_from_disk_even_where_the_store_cannot_see_the_edit`, `tests/test_read_store.py` (15) |
| 4 | `/screening/corpus` on an accepted corpus does not call the de-duplicator; a staged one does | **Met** | `test_the_corpus_of_an_accepted_snapshot_is_not_deduplicated_again` (0 calls, same counts as a full re-parse), `test_a_staged_corpus_not_yet_accepted_is_still_deduplicated`, `test_a_staged_export_changed_on_disk_after_acceptance_is_parsed_again`; failed on today's code (1 call) |
| 5 | Screening home sends `/screening/corpus` once (vitest) | **Met** | `apps/research-ui/tests/page-requests.test.tsx` "DoD 5"; failed with the old request helper (corpus ×2) |
| 6 | Before-and-after table of the eight routes on a copy of the sensor-stress review | **Met on the generated fixture; on a copy of the review: deferred** (decision item 23, PROPOSED: this session may not read the review) | table below |
| 7 | No Screening, Charting or Workspaces page sends the same GET twice on load (vitest per page) | **Met** | `page-requests.test.tsx`: 12 pages (Home, Import, Prepare, Agent proposals, Triage, Agreement, Publish, Export, pilot, Charting table, Charting one study, Workspaces), each against a real engine's recorded answers |
| 8 | `/review/next-step` ≤ 150 files on the fixture | **Met** | the DoD 1 test's next-step case |
| 9 | Table of every page, nothing else running, three passes each | **Met on the generated fixture; on the review: deferred** (item 23). "Nothing else running" means no other job of this session; other sessions on the PC were not checked | table below |

### Routes on the fixture

Measured 2026-11-23 on this PC with no other job of this session running; `ac6d29d8` (before) and this branch (after) on the same fixture copy. Files opened: the first call with the store empty. Every answer was compared with `ac6d29d8`'s, route by route: byte for byte the same apart from `computed_at`, the charting form's own creation times, and the table's removed abstracts.

| Route | Files opened, before | after (first call) | Time before (median of 3) | after, first call (store empty) | after, again (median of 3) | Answer bytes before → after |
| :-- | --: | --: | --: | --: | --: | :-- |
| `GET /review/next-step` | 3,463 | 138 | 3,340 ms | 403 ms | 61 ms | 431 → 431 |
| `GET /workspaces` | 3,324 | 131 | 2,437 ms | 311 ms | 49 ms | 564 → 564 |
| `GET /screening/prisma/preview` | 3,301 | 115 | 2,515 ms | 220 ms | 76 ms | 654 → 654 |
| `GET /ui/publication-status` | 3,320 | 127 | 2,138 ms | 430 ms | 25 ms | 752 → 752 |
| `GET /screening/corpus` | 11 | 10 | 957 ms | 83 ms | 25 ms | 2,133 → 2,133 |
| `GET /screening/summary` | 114 | 57 | 401 ms | 119 ms | 27 ms | 260 → 260 |
| `GET /screening/agreement` | 58 | 58 | 151 ms | 65 ms | 65 ms | 320 → 320 |
| `GET /screening/ui/batches` | 325 | 325 | 225 ms | 318 ms | 297 ms | 10,100 → 10,100 |
| `GET /screening/methods` | 3,372 | 244 | 2,223 ms | 383 ms | 380 ms | 13,000 → 13,000 |
| `GET /charting` | 3,328 | 134 | 3,289 ms | 422 ms | 56 ms | 635,844 → 237,985 |
| `GET /charting/records/{id}` | 3,328 | 134 | 2,345 ms | 364 ms | 44 ms | 3,808 → 3,808 |
| `GET /discovery/checks` | 33 | 23 | 818 ms | 188 ms | 159 ms | 4,020 → 4,020 |
| `GET /discovery/handoff` | 19 | 14 | 1,278 ms | 138 ms | 88 ms | 2,940 → 2,940 |
| `GET /screening/decisions/conflicts` | 57 | 57 | 225 ms | 61 ms | 54 ms | 12 → 12 |
| `GET /screening/criteria` | 111 | 111 | 85 ms | 83 ms | 78 ms | 441 → 441 |
| `GET /screening/queue?view=needs_you&limit=50` | 112 | 112 | 353 ms | 126 ms | 123 ms | 56 → 56 |
| `GET /screening/records/{id}` | 113 | 113 | 455 ms | 192 ms | 134 ms | 4,845 → 4,845 |
| `GET /screening/proposals/setup` | 57 | 57 | 42 ms | 39 ms | 39 ms | 589 → 589 |

### Pages on the fixture

Each page's requests in the order it sends them, one after another (the engine answers its read routes one at a time), summed; three passes. Pass 1 starts with an empty store, as the first page after a change; passes 2 and 3 keep it. Before, Publish sent one review request per batch (54 here).

| Page | Requests before → after | Total before (median of 3) | After, first page after a change (pass 1) | After, again (median of passes 2 and 3) |
| :-- | :-- | --: | --: | --: |
| Screening home | 8 → 7 | 8,847 ms | 704 ms | 346 ms |
| Publish | 61 → 8 | 10,155 ms | 1,341 ms | 971 ms |
| Export | 5 → 5 | 10,735 ms | 1,559 ms | 573 ms |
| Triage, first record | 7 → 7 | 2,435 ms | 557 ms | 409 ms |
| Charting table | 2 → 2 | 2,391 ms | 421 ms | 56 ms |
| Charting one study | 3 → 3 | 4,481 ms | 431 ms | 114 ms |
| Workspaces | 1 → 1 | 2,830 ms | 416 ms | 63 ms |

### Gates

| Check | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| New tests fail on today's code | `71430303` (tests only, on `ac6d29d8`) | `uv run pytest tests/console/test_read_performance.py` | DoD 1/8: 3,320, 3,463 and 3,301 files; DoD 4: 1 de-duplication; the store guards (DoD 3) pass, as they must |
| Affected Python suites | `76006eed` | `uv run pytest tests/console tests/authority tests/pipeline tests/test_screening_events.py tests/test_handoff.py tests/test_read_store.py tests/cli -n 4` | 1,681 passed, 4 skipped |
| Full Python suite | `1fbf5088` | `uv run pytest -q -n 4 -p no:cacheprovider` | **6,573 passed, 15 skipped, 0 failed** (counted from the progress lines; `addopts` hides the summary line) |
| Full vitest, first run | `1fbf5088` tree before the pilot-test helper fix | `npx vitest run` | 1,437 passed, 2 failed (the pilot tests took the loading frame's heading as the page's; their helper now waits for the frame to go) |
| Full vitest after review round 1 | `a4119db2` | `npx tsc --noEmit`; `npx vitest run` | tsc clean; **119 files, 1,441 of 1,441 passed** |
| Browser specs of the touched screens | `1fbf5088` | `npx playwright test` screening-states, -pilot, -export, -import, -proposals, next-step, charting, charting-study, workspaces (both projects) | 115 passed, 11 skipped |
| Full browser suite (PR gate) | `ede125c2` | `npx playwright test` (build included) | **732 passed, 16 skipped, 0 failed** (17.4 min, Chromium light and dark) |
| After review round 1 (Python) | `a4119db2` | `pytest tests/console/test_read_performance.py tests/console/test_corpus_api.py tests/console/test_corpus_import_api.py tests/console/test_combined_corpus_api.py -n 4` | 50 passed |
| Lint as CI | `a4119db2` | `uv run ruff check scripts/`; `uv run ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | clean |
| Contract baseline | `a4119db2` | `uv run python scripts/generate_contract_baseline.py --check` | current |
| Other checkpoint checks | `a4119db2` | `git diff --check`; `select_test_gate.py --check`; `sync_skills_bundle.py --check` | pass |

The PR gate's `pytest -n auto` was run as `-n 4` (the PC went down once under parallel suites); the full Python suite was not run again after review round 1, whose Python change is one `try` in `corpus_accept._accepted_counts` and two tests (run above).

### Not verified

- **The researcher's review was not measured.** Every number above is the generated fixture's, on this PC, warm OS file cache. The real review has more files outside the screening folders (harvest, discovery runs), which the key reads each lookup (one `os.stat` per file; about 28 ms for 295 files here).
- Run-to-run noise was not studied beyond three passes; other sessions' load on the PC was not checked.
- A cold OS file cache, antivirus scanning per open and a slower disk were not measured.
- The corpus fast path's counts equal a full re-parse on the fixture (2,181, 1,119, 1,062); that the snapshot's de-duplication of `verified.json` rows always equals the old preview's de-duplication of the parsed exports was not proven (item 11).
- The fast path's other branches (a combined corpus, a chase round, a protocol changed after acceptance) were checked by reading and by the existing combined-corpus and chase tests, not by a test of their counts with the fast path in place.
- Not tried in a real browser: the loading frame and the shared requests were checked in jsdom only; the Playwright spec whose fake engine was updated (`tests-browser/screening-states.spec.ts`) and the other specs of the touched screens passed in Chromium (light and dark); nobody looked at the screens by hand.
- The dev server's React Strict Mode runs each effect twice; a dev-browser network panel may still show pairs. Not checked.
- The key's coverage test runs the kept results on the fixture's state only; a branch of them that reads another folder in another state (a harvest, a chase round) is covered by reading, not by that test.

- The key's walk does not follow a folder linked into the workspace (`os.walk` without `followlinks`): a workspace whose `literature/` is a link would not see changes there (found by the reviewer; not tried).
- A test that edits a file with the same size within one tick of the Windows clock (about 15 ms) after a display call would see the accepted cost of question 3; the full suite passed once, so no such test was seen, but none was looked for.

### Follow-up (not in this change)

- A structural test that no write route is wrapped by `display_route` and that Approve and Publish never run inside `display_reads` (the reviewer checked it by reading).
- Linked folders in the key's walk (above); the kept workspaces' order moves on a store, not on a read (a workspace read often can be dropped first among 32).
- The three audit hooks the tests install stay for the whole test process (review finding 6, P3, not changed): cheap, but one shared hook in a conftest would be tidier.
- The real review's own before-and-after table (DoD 6 and 9 on a copy of the sensor-stress review), for a session allowed to copy it.

### Review

`milestone-reviewer`, round 1 on `ac6d29d8..1fbf5088`: **CHANGES**. It found the engine store sound by reading (no stale display answer beyond question 3's cost; Approve, Publish, export and methods read the disk; the event functions' failure paths unchanged). Findings: (1) P2, reproduced: a read made after a write could join a request started before it, so a reload after a second quick change could show the first change's answer; (2) P2, reproduced: the corpus fast path answered 409 where the old code answered 200 when `protocol.json` was missing or not JSON; (3) the build record was missing; (4) P3: the batch-reviews refusal message fell back to "" instead of the status text; (5) P3: a loose test assertion; (6) P3: the tests' audit hooks stay for the whole test process.

Repaired in `a4119db2`: (1) a request is shared only between readers that start in the same synchronous run, with two regression tests; (2) the fast path falls back to the full preview when the protocol cannot be read, with a test (invalid and missing); (4) a status-text fallback (Publish's uses of the reviews were already guarded); (5) the assertion needs `PROJECTION_STALE` and `007`; (6) not changed (follow-up). `ede125c2` restores a committed screenshot the browser run had rewritten.

Round 2 on `1fbf5088..ede125c2`: **CHANGES, documentation only**: findings 1, 2, 4 and 5 resolved (1 and 2 re-reproduced against the repairs: two requests and the later answer; ACCEPTED 2/0/2 as the old path), 6 a follow-up; finding 3 open until this section existed and DoD 6 and 9's fixture-only measurement was an explicit deferral (now decision item 23, PROPOSED).

Round 3 on `ede125c2..99c5a685` (documentation only): **APPROVE**. Two wording follow-ups ("What was built" item 6 and DoD 3) were applied after it. Before merge the researcher answers decision items 6 to 23, including item 11's known limit and item 23's deferral.

## Measured on a copy of the review, 2026-11-23

By the main session, at the researcher's word, on the copy of the sensor-stress review made for the profile of 2026-11-22 (589 files; the copy was unchanged after each run). One process per commit, an in-process test client, each route called three times in the order listed, so a later route may find results an earlier one left in the store. Times in ms, on the researcher's PC, one run.

| Route | `main` `ac6d29d8` | Build `154da1a2` | Answer |
| :-- | :-- | :-- | :-- |
| `GET /review/next-step` | 6370, 4177, 4333 | 911, 140, 139 | equal apart from `computed_at` |
| `GET /ui/publication-status` | 2523, 2593, 2539 | 32, 29, 29 | byte-identical |
| `GET /screening/prisma/preview` | 2711, 2723, 3326 | 313, 88, 94 | byte-identical |
| `GET /screening/corpus` | 2081, 1635, 1483 | 31, 32, 31 | byte-identical |
| `GET /screening/summary` | 532, 617, 542 | 32, 30, 32 | byte-identical |
| `GET /screening/agreement` | 374, 358, 357 | 223, 202, 202 | byte-identical |
| `GET /screening/ui/batches` | 1233, 277, 265 | 225, 220, 226 | byte-identical |
| `GET /screening/settings` | 5, 4, 4 | 5, 3, 3 | byte-identical |
| `GET /screening/decisions/conflicts` | 164, 167, 161 | 49, 44, 46 | byte-identical |
| `GET /charting` | 3165, 2796, 2763 | 82, 78, 147 | 1,281,396 to 723,525 bytes; the only difference is `abstract` absent from the 443 rows |
| `GET /discovery/checks` | 1691, 1273, 1373 | 226, 188, 190 | equal apart from `computed_at` |

Not measured there: files opened per call, `/workspaces`, `/charting/records/{id}`, the pages in a browser, a first call of the publication status with an empty store. DoD 6 and 9's page tables remain the generated fixture's.
