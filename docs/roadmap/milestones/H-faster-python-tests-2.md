# H-faster-python-tests-2 Two more workspace templates, six slow marks, no kept temporary folders

Branch: `dev/h/faster-python-tests-2` (from `origin/main` `6f31f92e`, which holds H-faster-python-tests, PR 303) · Lane: **STANDARD** (test code and one pytest setting; no product code, contract or public surface changes) · Status: **IN REVIEW** · Started: 2026-11-23

The researcher's go-ahead of 2026-11-23 in the review session ("Yes, build them"), after the full timing passes of that day (`docs/assessment/test-suite-review-2026-11-23.md`, "Update, evening of 2026-11-23", on the local branch `dev/docs/project-review-2026-11-23`, commit `e73795d9`; items 1, 2 and 4 of "What is left"). The per-file numbers of those passes are in the sessions' shared notes folder (`test-timing-2026-11-23-branch-e8eaf753.txt`).

## What changed

**(a) Two more workspace templates** (`tests/support/workspaces.py`, unchanged; H-faster-python-tests's `copy_of`).

| Builder | Key | Callers |
| :-- | :-- | :-- |
| `tests/console/test_criteria_pilot_api.py::_workspace` (60 records accepted, three batches prepared) | records, `prepare`, the protocol file's content, `WS_ID` | the `ws` fixture and three direct calls |
| `tests/pipeline/test_citation_chase.py::build_ws` (a published screening whose includes can be chased) | `ids`, the protocol file's content, `WS_ID`, `SCREENER` | five files: `test_citation_chase`, `test_chase_accept`, `test_chase_review_repairs`, `tests/cli/test_chase_cli`, `tests/console/test_chase_api` |

Each keeps its signature; the original is `_workspace_fresh` and `_build_ws_fresh`. `build_ws` set four module globals from the built workspace (the seed's and one excluded record's identifiers); they are the same for every copy, so the fresh builder now returns them and `build_ws` sets them after each copy. **One test keeps fresh builds on purpose:** `test_dod11_the_same_seed_on_the_same_snapshot_gives_the_same_list` compares the lists drawn in two workspaces built apart; two copies of one template would share every stamp and id, and the test would say less.

**(b) Not made templates, with the measurement.** The review named nine console files; seven of them build their workspace through the product's scaffold (`catalog.create`, the `env` fixtures of `test_discovery_api`, `test_workbench_counts_api`, `test_discovery_estimate_api`, `test_workbench_seeds_comparison_api`, and the three files that borrow the discovery one) or through a genesis over HTTP (`test_workbench_amend_api`, `tests/kits/agent/test_mcp_workspace_proposals.py`). A scaffold costs 0.18 s fresh and 0.075 s as a copy (44 files, 27 folders; five runs each), so a template would save about 0.1 s a test; and the scaffold records the folder it was built in, in `.mcp.json` (the `--workspace` argument) and in `audit/journal.jsonl` (the inputs and outputs of the GENESIS event), which `copy_of` refuses, rightly: a copy would point back to the template. Rewriting those paths after the copy would make the copy something the product never wrote. Left as they are. The review's "about 110 s in nine files" was set-up time, not what a template can remove; what was removable is the pilot file (28 s) and the chase files (23 s).

**(c) Six long tests marked slow.** They ran in the inner gates (`-m "not slow"`) and each took 7 s or more in the one-process pass: `test_approve_all.py::test_finding_38_one_action_approves_54_decided_batches` (30 s), `test_assistant_critic_set.py::test_every_document_can_be_read_through_the_tool` (18 s), `test_golden_recon_cassette.py::test_the_golden_probe_keeps_each_leg_and_feeds_directions` (12 s) and `::test_the_golden_probe_runs_from_http_and_binds` (8 s), `test_golden_search_cassettes.py::test_the_cassette_holds_no_contact_address_or_key` (8 s) and `::test_the_handoff_accept_gives_the_snapshot_the_cli_run_gives` (7 s). Checkpoint, PR and full runs keep them. No assertion changed.

**(d) `tmp_path_retention_policy = "failed"`** in `pyproject.toml`. pytest's default keeps every test's temporary folder for the last three runs and deletes the fourth-oldest run's folder when a session ends. A full run left 52,452 files; a later session, even a one-file one, then spent up to a minute deleting such a folder (33 s measured in a profile on 2026-11-23). With the setting a passing test's folder is removed when the test ends (in its worker), a failed test's folder is kept, and the run's folder is removed when every test passed.

## Definition of done

- [x] (a) The pilot and chase builders are templates; the key holds every input the build reads; the one test that needs fresh builds keeps them.
- [x] (b) The scaffold-based fixtures measured and left, with the reason.
- [x] (c) Six tests marked slow; every inner command that covers their files still selects other tests.
- [x] (d) The retention setting tried on one file and on a full run, kept because the full run was not slower and no test failed.
- [x] The full suite at four workers, before and after the setting, under the suite lock.
- [x] No test weakened.
- [ ] Independent review (`milestone-reviewer`).
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
| full, setting off | (a)+(c) | `python scripts/suite_lock.py -- pytest -q -n 4 --dist worksteal --junitxml` | **5,405 results: 5,390 passed, 15 skipped, 0 failed**; 52,452 files left in the temporary folder | 522 s |
| full, setting on (the final tree) | (a)+(c)+(d) | the same | **5,405 results: 5,390 passed, 15 skipped, 0 failed**; no folder left; no template folder left | 489 s |
| pr | final tree | `select_test_gate.py --changed origin/main --stage pr` | selects `git diff --check`, `tests/console tests/kits/agent tests/pipeline` and `tests/kits/agent` (task T-110, `pyproject.toml`): all inside the full run above | |
| pr | final tree | `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `generate_contract_baseline.py --check`; `git diff --check` | pass; baseline current, no locked file changed; clean | |

**What the numbers say.** Set-up in the six files fell by 45 s of one-process time, and the inner gates that cover the four marked files run about 80 s less. The full suite at four workers did not change measurably: 522 s and 489 s here against 437 s in H-faster-python-tests's record on an idle PC; the difference between the two runs here is inside what the same tree varies by. The gain of (d) is not in a run's own time: it is the deletion a later session no longer does, and 0.5 GB a run no longer left on disk.

## Not verified

- CI, macOS and Linux. On Linux and macOS a passing test's folder is removed the same way; not run there.
- That no workflow outside the tests reads a passed test's temporary folder after the run (a developer inspecting it by hand no longer can, unless the test failed).
- The full run on an idle PC: other sessions existed, none held the suite lock.
- The six slow marks rest on one timing pass; a test may be faster on another machine.

## Deferred

- The scaffold itself (0.18 s, 44 files) and the console's import (3.7 s per process) are product code; not touched.
- Narrowing the console areas' checkpoint, and a virus-scanner exclusion for the temporary folder: the researcher's decisions (review update, items 3 and 5).

## Review

Pending.
