# H-faster-python-tests-2 Two more workspace templates and six slow marks

Branch: `dev/h/faster-python-tests-2` (from `origin/main` `6f31f92e`, which holds H-faster-python-tests, PR 303) · Lane: **STANDARD** (test code only; no product code, contract or public surface changes) · Status: **READY FOR PR** (review round 2 APPROVE on `b9ee992a`; not pushed; decision items 1 to 3 PROPOSED) · Started: 2026-11-23

`origin/main` `460f23f3` (PR 304, the M13-installers specification, documentation only) was merged in at `b9ee992a`; one conflict, `docs/decisions.md`, both entries kept.

The researcher's go-ahead of 2026-11-23 in the review session ("Yes, build them"), after the full timing passes of that day (`docs/assessment/test-suite-review-2026-11-23.md`, "Update, evening of 2026-11-23", on the local branch `dev/docs/project-review-2026-11-23`, commit `e73795d9`; items 1, 2 and 4 of "What is left"). The per-file numbers of those passes are in the sessions' shared notes folder (`test-timing-2026-11-23-branch-e8eaf753.txt`).

Of the three items, two are built and one is refused: the temporary-folder setting (d) was tried, measured and taken out after review.

## What changed

**(a) Two more workspace templates** (`tests/support/workspaces.py`, unchanged; H-faster-python-tests's `copy_of`).

| Builder | Key | Callers |
| :-- | :-- | :-- |
| `tests/console/test_criteria_pilot_api.py::_workspace` (60 records accepted, three batches prepared) | records, `prepare`, the protocol file's content, `WS_ID` | the `ws` fixture and three direct calls |
| `tests/pipeline/test_citation_chase.py::build_ws` (a published screening whose includes can be chased) | `ids`, the protocol file's content, `WS_ID`, `SCREENER` | five files: `test_citation_chase`, `test_chase_accept`, `test_chase_review_repairs`, `tests/cli/test_chase_cli`, `tests/console/test_chase_api` |

Each keeps its signature; the original is `_workspace_fresh` and `_build_ws_fresh`. `build_ws` set four module globals from the built workspace (the seed's and one excluded record's identifiers); they are the same for every copy, so the fresh builder now returns them and `build_ws` sets them after each copy. **One test keeps fresh builds on purpose:** `test_dod11_the_same_seed_on_the_same_snapshot_gives_the_same_list` compares the lists drawn in two workspaces built apart; two copies of one template would share every stamp and id, and the test would say less.

**(b) Not made templates, with the measurement.** The review named nine console files; seven of them build their workspace through the product's scaffold (`catalog.create`, the `env` fixtures of `test_discovery_api`, `test_workbench_counts_api`, `test_discovery_estimate_api`, `test_workbench_seeds_comparison_api`, and the three files that borrow the discovery one) or through a genesis over HTTP (`test_workbench_amend_api`, `tests/kits/agent/test_mcp_workspace_proposals.py`). A scaffold costs 0.18 s fresh and 0.075 s as a copy (44 files, 27 folders; five runs each), so a template would save about 0.1 s a test; and the scaffold records the folder it was built in, in `.mcp.json` (the `--workspace` argument) and in `audit/journal.jsonl` (the inputs and outputs of the GENESIS event), which `copy_of` refuses, rightly: a copy would point back to the template. Rewriting those paths after the copy would make the copy something the product never wrote. Left as they are. The review's "about 110 s in nine files" was set-up time, not what a template can remove; what was removable is the pilot file (28 s) and the chase files (23 s).

**(c) Six long tests marked slow.** They ran in the inner gates (`-m "not slow"`) and each took 7 s or more in the one-process pass: `test_approve_all.py::test_finding_38_one_action_approves_54_decided_batches` (30 s), `test_assistant_critic_set.py::test_every_document_can_be_read_through_the_tool` (18 s), `test_golden_recon_cassette.py::test_the_golden_probe_keeps_each_leg_and_feeds_directions` (12 s) and `::test_the_golden_probe_runs_from_http_and_binds` (8 s), `test_golden_search_cassettes.py::test_the_cassette_holds_no_contact_address_or_key` (8 s) and `::test_the_handoff_accept_gives_the_snapshot_the_cli_run_gives` (7 s). Checkpoint, PR and full runs keep them. No assertion changed.

What the inner gates lose with them, and what was done about it (review round 1, findings 2 and 3):

- **The 54-batch approve-all test was the only test of four properties:** a publication approval fingerprint after a full bulk approval, each approval binding its own batch's decision bytes, `bulk: true` on every journal row, and a second paste approving nothing. Its body is now a helper run twice: with 54 batches (slow, the reproduction of finding 38) and with **three batches (not slow, a new test,** `test_one_action_approves_three_decided_batches_each_bound_to_its_own_bytes`), so every assertion stays in the inner gates. The new test fails when an expected value is flipped (checked with `bulk`).
- **`test_the_handoff_accept_gives_the_snapshot_the_cli_run_gives` is the only assertion that the browser hand-off accept and the command-line accept give the same artifact id.** It leaves the `pipeline` area's inner command; the checkpoint, the PR stage and CI keep it. Named in the decisions entry, item 2.
- The other four (the reviewer's reading): the two golden recon replays reached an inner command only through the `pipeline` area, which does not own recon code; the assistant's workspace read has other tests in `tests/kits/agent`; and `test_the_cassette_holds_no_contact_address_or_key` has no neighbour in an inner gate: its guard is that a change to a cassette selects the full suite.

**(d) `tmp_path_retention_policy = "failed"`: tried, then refused.** pytest's default keeps every test's temporary folder for the last three runs and deletes the fourth-oldest run's folder when a session ends: a full run left 52,452 files, and a later session, even a one-file one, spent up to a minute deleting such a folder (33 s in a profile on 2026-11-23). The setting removes a passing test's folder when the test ends. It cost nothing measurable in run time (table below), and both full runs passed. **But it makes temporary paths repeat inside one process:** pytest names a folder from the first 30 characters of the test's name plus the lowest free number, so once a folder is removed the next test with the same start of name gets the same absolute path. The read store keeps results by absolute workspace path and a name, size and modification-time signature (`src/scholar_harness/screening/read_store.py:109-147`), which a copy of the same template reproduces. The reviewer showed the consequence in `tests/console/test_read_performance.py`: the three cases of the 150-file test shared one path, and the `next-step` case opened 69 files instead of 139, because it was served results kept by the case before it. The test passed, measuring a warm store. The templates of H-faster-python-tests rest on the same assumption (a test's path is its own). The setting is not in this branch. The path repetition was reproduced separately with a three-case throwaway test (`all`: three paths; `failed`: one).

## Definition of done

- [x] (a) The pilot and chase builders are templates; the key holds every input the build reads; the one test that needs fresh builds keeps them.
- [x] (b) The scaffold-based fixtures measured and left, with the reason.
- [x] (c) Six tests marked slow. What each was the only inner-gate guard of is named above; the approve-all properties keep an unmarked test, the hand-off accept identity does not.
- [x] (d) The retention setting tried on one file and on a full run; refused, because it weakens a test.
- [x] The full suite at four workers under the suite lock (twice: without the setting, which is this branch's tree before the approve-all repair, and with it).
- [x] No test weakened on the final tree.
- [x] Independent review (`milestone-reviewer`): round 1 CHANGES, repaired; round 2 APPROVE.
- [ ] Closure: the CI run of the pull request (CI is the full gate; nothing is pushed).

## Decisions

`docs/decisions.md`, "2026-11-23 — H-faster-python-tests-2".

## Evidence

On the researcher's PC (Windows, 4 cores, 8 threads), this worktree, venv synced offline with `--extra dev --extra pdf`, Python 3.14.7. No network. Other sessions were idle or light; the PC was not otherwise checked.

| Stage | Tree | Command | Result | Duration |
| :-- | :-- | :-- | :-- | --: |
| before | `dev/h/faster-python-tests` `e8eaf753`, one process (the review's pass) | `pytest -q --durations=0` | set-up of the six template files: pilot 28.0 s, chase accept 6.7, chase repairs 6.5, chase CLI 3.2, chase API 3.1, citation chase 3.2 (50.7 s) | 1,448 s the whole suite |
| inner | (a) | `pytest tests/console/test_criteria_pilot_api.py -q` | 51 passed | |
| checkpoint | (a) | `pytest` on the six files, `--durations=0`, one process | 102 passed, 0 failed; set-up 1.8, 0.5, 0.9, 0.1, 1.1, 0.8 s (**5.2 s**, from 50.7 s) | 43 s |
| checkpoint | (a)+(c) | `pytest` on the four marked files, `-m "not slow"` | 39 passed (of 45), 0 failed; the longest left is 4.3 s, so the time did not move to a neighbour | 26 s (107 s for the 45 in the pass) |
| (c) | manifest | the inner commands that cover the four files (`tests/pipeline`, `tests/console` and its finer areas, `tests/kits/agent`) | each selects a folder or a list of files with many other tests; `select_test_gate.py --check`: `OK: 11 tasks, 24 areas, 4 stages` | |
| (d) one file | (a)+(c) | `pytest tests/console/test_next_step_api.py -q -o tmp_path_retention_policy=all` and `=failed`, twice each, alternating | 46 passed each time; suite time 34.0 and 28.5 s kept, 32.8 and 32.9 s removed; with `failed` the run left no folder | |
| full, setting off | (a)+(c), before the approve-all repair | `python scripts/suite_lock.py -- pytest -q -n 4 --dist worksteal --junitxml` | **5,405 results: 5,390 passed, 15 skipped, 0 failed**; 52,452 files left in the temporary folder | 522 s |
| full, setting on (refused later) | (a)+(c)+(d) | the same | 5,405 results: 5,390 passed, 15 skipped, 0 failed; no folder left. **This run passed with the weakened read-performance case in it**, which is why a green run was not enough to keep the setting | 489 s |
| (d) path repetition | a throwaway three-case test outside the repository | `-o tmp_path_retention_policy=all`, then `=failed` | `all`: three paths (`…mos0`, `…mos1`, `…mos2`); `failed`: one path three times | |
| after review | final tree (the setting out, the approve-all helper) | `pytest tests/console/test_approve_all.py -q` | 26 passed (25 and the new one); with `-m "not slow"` 25 passed; the new test with `bulk` expected `False`: failed, then restored | 54-batch test 44 s; the others under 4 s each |
| pr | final tree | `select_test_gate.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `generate_contract_baseline.py --check`; `git diff --check` | pass; baseline current, no locked file changed; clean | |
| checkpoint | final tree `b9ee992a` | the selector's checkpoint for `--changed origin/main`: `python scripts/suite_lock.py -- pytest tests/console tests/kits/agent tests/pipeline -q -n 4 --dist worksteal --junitxml` | **1,621 results: 1,617 passed, 4 skipped, 0 failed** | 419 s |

The full suite was not run a third time for the final tree: it differs from the "setting off" run by one test file (`tests/console/test_approve_all.py`) and a documentation merge, and the selector's checkpoint above ran on it. CI is the full gate.

**What the numbers say.** Set-up in the six files fell by 45 s of one-process time, and the inner gates that cover the four marked files run about 80 s less (a few seconds are given back by the new three-batch test). The full suite at four workers did not change measurably: 522 s here against 437 s in H-faster-python-tests's record on an idle PC. The deletion of old temporary folders at the end of a session stays as it was.

## Not verified

- CI, macOS and Linux.
- The full run on an idle PC: other sessions existed, none held the suite lock.
- The six slow marks rest on one timing pass; a test may be faster on another machine.
- Whether another path-keyed store exists beside the read store; the reviewer probed 13 files.

## Deferred

- **The temporary-folder cost** (item 4 of the review's update). Open ways, none built: clearing the read store before every test and then using the setting (it would need a search for every other store keyed by path); a retention count of one (less disk, the same deletion); writing fewer files per test. Each is a design choice for a later part.
- The scaffold itself (0.18 s, 44 files) and the console's import (3.7 s per process) are product code; not touched.
- Narrowing the console areas' checkpoint, and a virus-scanner exclusion for the temporary folder: the researcher's decisions (review update, items 3 and 5).
- Reviewer follow-ups that predate this branch: the `screening` area's checkpoint does not list `tests/console/test_approve_all.py`; `AGENTS.md` still names `scholar_rag`, `scholar_verify` and `--extra rag`.

## Review

**Round 2** (on `b9ee992a`): **APPROVE**. The four findings are closed: with the setting out the three route cases get three paths again and `next-step` opens 139 files on its first call; the three-batch test fails when the product drops `bulk` from the journal row (the reviewer's probe: 1 failed, 24 passed in the not-slow selection). Three P3 points on this record's wording, fixed in the next commit: the checkpoint selection run on the final tree (evidence table), the cassette check's guard named in (c), the merge of `460f23f3` named at the top.

**Round 1** (`milestone-reviewer`, on `c95c6fbf`): **CHANGES**. The two templates were found sound (no other test compares two workspaces built from one key; the keys are complete; the four globals are right for every caller, `ids="doi"` and `ids="none"` included; 102 passed).

1. (P1) The retention setting made temporary paths repeat, and the read store then served an earlier test's results to the `next-step` case of the 150-file test (69 files opened instead of 139). **Repaired by taking the setting out;** the reason is recorded in (d).
2. (P2) The 54-batch approve-all test was the only test of four approval properties. **Repaired:** a three-batch test with the same assertions, not slow.
3. (P3) The hand-off accept identity leaves the `pipeline` inner command. **Named** in (c) and in the decisions entry, item 2.
4. (P3) DoD (c) was weaker than "nothing is guarded only by one of the six". **Reworded.**
