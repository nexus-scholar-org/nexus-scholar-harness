# H-small-fixes-2-2026-11-18 Gate manifest wheel builds, Windows lock follow-ups, init wording, F8
Branch: dev/fix/small-fixes-2 · Lane: **STANDARD** · Status: MERGED (PR #243, merge commit `1d478f4f`, 2026-11-18) · Started: 2026-11-18

Base: `origin/main` at `6e39b00a`. Second bundle after `H-small-fixes-2026-11-18.md` (PR #237). No live API calls, no AI spend. Out of scope by agreement with the concurrent sessions: Inception screens, proposal and check objects, the console inception API, the Discovery plan screen, `src/scholar_search`. None of those files was edited.

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md`: bounded behaviour changes owned by one package, no public HTTP, CLI-semantics or MCP change and no Contract v1 model, schema or fixture change. The one user-visible change is the wording of one CLI line. The lock fix touches `scholar_rag` internals (a delete that waits, a flag cleared later) and no result model, error code or file format.

## Definition of done
- [x] **1. Gate manifest.** The four manifest commands that ran a bare `uv build --wheel` work on a checkout without `apps/research-ui/.next-export`.
- [x] **2. Windows lock follow-ups.** Both open follow-ups of PR #229/#230 fixed with reproducing tests.
- [x] **3. `nexus-scholar init` wording.** "1 skill was COPIED" / "N skills were COPIED", with a test.
- [x] **4. F8.** Re-verified at the head by `phase-auditor`: all three claims still real. F8-1 and F8-3 fixed with reproducing tests; F8-2 deliberately not changed (below).
- [x] **5. Gates.** `/gate pr` once on the final executable commit (`c454625d`); `generate_contract_baseline.py --check`; both ruff commands; `milestone-reviewer` (verdict at the end).

## Findings fixed
| Item | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| 1 manifest | none (a JSON edit); checked by running the commands | `uv build --wheel` on this checkout (no export): `hatchling.build.build_wheel` failed, exit 1 | the portable one-liner builds `nexus_scholar-1.1.0b6-py3-none-any.whl` with the opt-out warning; `select_test_gate.py --check` OK (24 tasks); `tests/unit/test_select_test_gate.py` and `tests/conformance` pass (720 passed, 3 skipped) |
| 2a commit-intent deletes | `tests/kits/rag/test_index_replacement.py::test_7_3_finalize_removes_an_intent_a_reader_briefly_has_open`, `tests/kits/rag/test_index_legacy.py::test_recovery_removes_an_intent_a_reader_briefly_has_open` (WinError 32 simulated three times on the intent file) | both raised `PermissionError` | both pass: the delete is tried again |
| 2b `release()` clears `_held` first | `tests/kits/rag/test_index_replacement.py::test_a_second_release_after_an_exhausted_wait_tries_the_delete_again` | after an exhausted wait the object reported `held == False` with the file still there, and a second `release()` did nothing | the flag is cleared only after the delete; the second `release()` deletes the file; a third is a no-op |
| 4 F8-1 publish retry | `tests/console/test_screening_actions.py::test_publish_idempotent_retry_logs_one_row` | two identical publishes wrote two `SCREENING_PUBLISH_COMPLETED` rows (same `generation_id`) | one row; the retry's `journal_event_id` is the first row's. A first publish whose row could not be written still gets it on retry (`test_publish_retry_with_broken_audit_still_joins_current` passes) |
| 4 F8-3 legacy event id | `tests/unit/test_workspace_audit_characterization.py::test_legacy_events_with_the_same_action_and_text_get_distinct_ids` | two `append_legacy_event` calls with the same action and text gave identical ids (`EVT-20261118192519-08e3b7` twice) | distinct ids, shape `EVT-<14 digits>-<6 hex>` unchanged |
| 3 init wording | `tests/inception/test_support_files_quiet.py::test_the_summary_agrees_in_number_for_one_copied_skill` | "1 skills were COPIED" | "1 skill was COPIED"; "3 skills were COPIED" unchanged |

## Item 4, F8 per claim
`phase-auditor` re-verified at `6e39b00a`; nothing dedupes, indexes or verifies on the journal's `event_id`, and no Contract v1 artifact, golden fixture or the baseline holds one (only the `AUD-`/`EVT-` prefix pattern of `RunManifestData.audit_event_id`, which a uuid limb satisfies). The edits are in `console/api/screening.py` (the screening action API, not the inception API) and `workspace/audit.py`.
- **F8-1, fixed.** `console/api/screening.py`: before journaling, the publish handler looks for a row with the same `generation_id` **and** `generation_fingerprint` and reuses it (the reviewer's P2: `generation_id` names only the scope, so a re-publish under another approval is a new record with the same id and needs its own row). It does not key on "the generation was already CURRENT", because the handler relies on a retry writing the row that an earlier `OSError` lost.
- **F8-3, fixed.** `workspace/audit.py::append_legacy_event`: `uuid4` limb and one clock reading. The finding was slightly off: `hash()` is randomised per process, so the old id was not deterministic across runs, only stable within one process (which is why same-process repeats collided). The comment said the scheme was "preserved per HCM-02"; a random-per-process limb could never match a fixture, so no parity is lost. The existing id-shape tests (`^EVT-\d{14}-[0-9a-f]{6}$`) pass unchanged.
- **F8-2, not changed.** One `ARTIFACT_ACCEPTED` row per batch is the acceptance gate's per-artifact provenance (`screening/batcher.py` calls `accept_artifact` per chunk, `contracts/acceptance.py` writes the row, and the gate's journal-before-publish rollback depends on it). `scripts/check_golden_workspace.py` requires one row with `artifact_type == screening_batch`. Collapsing rows is a contract decision; the only cheap option is grouping them when shown (UI or INDEX), which touches Inception/Screening UI files other sessions own. Kept as a deliberate behaviour.

## Item 1, per command
`select_test_gate.py` only prints commands; whoever runs them may use Git Bash, PowerShell or cmd, so an `ENV=1 cmd` prefix is not usable and a script with `os.environ` would be new surface. Choices:
- **T-90 `pr` and T-110 `inner`: UI-less wheel.** Both are packaging checks (the rag kit and `pyproject.toml`/`uv.lock`); the UI export adds nothing to them and Node is not needed for an inner check. They run `uv run python -c "...subprocess.call(['uv','build','--wheel'], env=dict(os.environ, NEXUS_WHEEL_ALLOW_NO_UI='1'))"`, which is the same in every shell.
- **T-120 `closure` and `area_defaults.closure`: build the export first** (`npm --prefix apps/research-ui ci`, `... run build:export`, then `uv build --wheel`), as `ci.yml` `build-wheel` does. Closure is the release-grade check, so the wheel under test should have the UI. `npm --prefix` is the form the manifest already uses.
- **Baseline.** `generate_contract_baseline.py --check` says "Contract baseline current" before and after the edit; the manifest is not covered by it. Nothing regenerated.

## Decisions
See `docs/decisions.md`, entry "2026-11-18 — Small fixes 2": item 4 (F8-1, F8-3) accepted 2026-11-18; items 1 to 3 and 5 PROPOSED.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner (item 2) | `3123ec64` | the three new tests, then `uv run --extra dev --extra pdf --extra rag pytest tests/kits/rag -n 4` | the three failed before the fix; 943 passed after | 3 min |
| inner (item 3) | `eb824cbc` | `pytest tests/inception/test_support_files_quiet.py` | 1 failed before, 5 passed after | 8 s |
| inner (item 1) | `57e0890f` | the one-liner; bare `uv build --wheel`; `select_test_gate.py --check`; `pytest tests/unit/test_select_test_gate.py tests/conformance` | UI-less build ok; bare build fails by design; manifest OK; 720 passed, 3 skipped | 1.5 min |
| inner (item 4) | `c454625d` | the two new tests (failed before), then `pytest tests/console/test_screening_actions.py tests/unit/test_workspace_audit*.py tests/unit/test_audit_log.py tests/unit/test_coordinator.py tests/unit/test_hydration_stage.py tests/pipeline/test_indexing_stage.py tests/conformance -n 4` | 844 passed, 3 skipped | 2 min |
| pr | `c454625d` | `git diff --check origin/main...HEAD`; `uv run --extra dev --extra pdf --extra rag pytest -n auto -o addopts="" -q` (the repo's own `-q` addopts would hide the summary); `ruff check scripts/`; `select_test_gate.py --check` | ok; **5 367 passed, 15 skipped, 0 failed, exit 0**; clean; OK (24 tasks) | 18 min |
| contract and lint | `c454625d` | `generate_contract_baseline.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `git diff --check origin/main..HEAD` | current; clean; clean; ok | <1 min |

## Deferred
- **F8-2** (`ARTIFACT_ACCEPTED` per batch): by design, see above; a grouped display needs the Screening/Inception UI owners.
- **Not fixed, still open from PR #230:** nothing. Both follow-ups are done. An exhausted wait on the lock or on the intent still raises the OS error unchanged (the 2026-11-12 decision).
- The `git diff` warnings "LF will be replaced by CRLF" for new files are the checkout's autocrlf, not a content change.

## Not verified
- The Windows lock and intent races were exercised by simulated `WinError 32` (the same technique as the existing tests), not by a real open handle on the intent file; the real-handle test of PR #230 covers only the lock file.
- The new manifest closure commands (`npm ci`, `build:export`, then the wheel) were not run end to end here (no Node install was done); the UI-less one-liner was run. CI's own `build-wheel` job uses the same two npm commands.
- The pr gate's UI half (typecheck, vitest, Playwright) was not run: `select_test_gate.py` selected `inception,rag,test-gate-selector` areas and no UI file changed.

## Review
`milestone-reviewer` on `76166c11`: **CHANGES**, no P1, two P2, three P3 (it ran no tests). Repairs in the commit after `76166c11`, bounded to the findings:
1. P2, `_published_event` matched `generation_id` alone: now also `generation_fingerprint`; non-dict `parameters` are skipped (P3 4). Regression test `test_published_event_matches_the_exact_publication_only`. Not reproduced through HTTP (a re-publish with another approval); covered at the function level.
2. P2, the `audit.py` module docstring still said the hash scheme must not be normalised without a behaviour-decision packet: rewritten to point at decision item 4 (item 4 accepted by the researcher on 2026-11-18).
3. P3, stale `_delete_lock_file` in the `release()` docstring: renamed.
5. P3 (closure does not set `NEXUS_WHEEL_REQUIRE_UI=1`, so a stale export could be bundled): left as is; `build:export` rebuilds the export in the same command list.
Also raised by the reviewer: `inception/wizard.py` (the init wording, one line) sits in the Inception package; it is not a screen, the console API or a proposal object, but the researcher may want the M10b session told.

Evidence for the repair: `pytest tests/console/test_screening_actions.py tests/unit/test_workspace_audit_characterization.py tests/kits/rag/test_index_replacement.py -n 4` (the new test and the 39 + rag + audit tests pass); ruff F-class clean; `git diff --check` ok. The full 5 367-passed run is on `c454625d`; the repair changes `screening.py` (one helper), two docstrings and one test, so it was not re-run in full (a repair delta, per the policy's evidence reuse; the screening action file's own tests were).

Re-review (repair delta `76166c11..bb159b45`, limited to the findings above): **APPROVE**. All four findings resolved; the new test would fail on the old matching; the reviewer re-ran 57 tests and the F-class ruff check (clean). Evidence for the final head: the full pytest run on `c454625d` (5 367 passed) plus the targeted runs above; the commits after it change one helper, docstrings, one test and docs.
