# H-small-fixes-2-2026-11-18 Gate manifest wheel builds, Windows lock follow-ups, init wording, F8
Branch: dev/fix/small-fixes-2 · Lane: **STANDARD** · Status: IN PROGRESS · Started: 2026-11-18

Base: `origin/main` at `6e39b00a`. Second bundle after `H-small-fixes-2026-11-18.md` (PR #237). No live API calls, no AI spend. Out of scope by agreement with the concurrent sessions: Inception screens, proposal and check objects, the console inception API, the Discovery plan screen, `src/scholar_search`. None of those files was edited.

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md`: bounded behaviour changes owned by one package, no public HTTP, CLI-semantics or MCP change and no Contract v1 model, schema or fixture change. The one user-visible change is the wording of one CLI line. The lock fix touches `scholar_rag` internals (a delete that waits, a flag cleared later) and no result model, error code or file format.

## Definition of done
- [x] **1. Gate manifest.** The four manifest commands that ran a bare `uv build --wheel` work on a checkout without `apps/research-ui/.next-export`.
- [x] **2. Windows lock follow-ups.** Both open follow-ups of PR #229/#230 fixed with reproducing tests.
- [x] **3. `nexus-scholar init` wording.** "1 skill was COPIED" / "N skills were COPIED", with a test.
- [ ] **4. F8.** Re-verified at the head by `phase-auditor`; outcome below.
- [ ] **5. Gates.** `/gate pr` once on the final executable commit; `generate_contract_baseline.py --check`; both ruff commands; `milestone-reviewer`.

## Findings fixed
| Item | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| 1 manifest | none (a JSON edit); checked by running the commands | `uv build --wheel` on this checkout (no export): `hatchling.build.build_wheel` failed, exit 1 | the portable one-liner builds `nexus_scholar-1.1.0b6-py3-none-any.whl` with the opt-out warning; `select_test_gate.py --check` OK (24 tasks); `tests/unit/test_select_test_gate.py` and `tests/conformance` pass (720 passed, 3 skipped) |
| 2a commit-intent deletes | `tests/kits/rag/test_index_replacement.py::test_7_3_finalize_removes_an_intent_a_reader_briefly_has_open`, `tests/kits/rag/test_index_legacy.py::test_recovery_removes_an_intent_a_reader_briefly_has_open` (WinError 32 simulated three times on the intent file) | both raised `PermissionError` | both pass: the delete is tried again |
| 2b `release()` clears `_held` first | `tests/kits/rag/test_index_replacement.py::test_a_second_release_after_an_exhausted_wait_tries_the_delete_again` | after an exhausted wait the object reported `held == False` with the file still there, and a second `release()` did nothing | the flag is cleared only after the delete; the second `release()` deletes the file; a third is a no-op |
| 3 init wording | `tests/inception/test_support_files_quiet.py::test_the_summary_agrees_in_number_for_one_copied_skill` | "1 skills were COPIED" | "1 skill was COPIED"; "3 skills were COPIED" unchanged |

## Item 1, per command
`select_test_gate.py` only prints commands; whoever runs them may use Git Bash, PowerShell or cmd, so an `ENV=1 cmd` prefix is not usable and a script with `os.environ` would be new surface. Choices:
- **T-90 `pr` and T-110 `inner`: UI-less wheel.** Both are packaging checks (the rag kit and `pyproject.toml`/`uv.lock`); the UI export adds nothing to them and Node is not needed for an inner check. They run `uv run python -c "...subprocess.call(['uv','build','--wheel'], env=dict(os.environ, NEXUS_WHEEL_ALLOW_NO_UI='1'))"`, which is the same in every shell.
- **T-120 `closure` and `area_defaults.closure`: build the export first** (`npm --prefix apps/research-ui ci`, `... run build:export`, then `uv build --wheel`), as `ci.yml` `build-wheel` does. Closure is the release-grade check, so the wheel under test should have the UI. `npm --prefix` is the form the manifest already uses.
- **Baseline.** `generate_contract_baseline.py --check` says "Contract baseline current" before and after the edit; the manifest is not covered by it. Nothing regenerated.

## Decisions
See `docs/decisions.md`, entry "2026-11-18 — Small fixes 2" (PROPOSED).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner (item 2) | `3123ec64` | the three new tests, then `uv run --extra dev --extra pdf --extra rag pytest tests/kits/rag -n 4` | the three failed before the fix; 943 passed after | 3 min |
| inner (item 3) | `eb824cbc` | `pytest tests/inception/test_support_files_quiet.py` | 1 failed before, 5 passed after | 8 s |
| inner (item 1) | `57e0890f` | the one-liner; bare `uv build --wheel`; `select_test_gate.py --check`; `pytest tests/unit/test_select_test_gate.py tests/conformance` | UI-less build ok; bare build fails by design; manifest OK; 720 passed, 3 skipped | 1.5 min |
| contract and lint | `57e0890f` | `generate_contract_baseline.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `git diff --check origin/main..HEAD` | current; clean; clean; ok | <1 min |

## Deferred
(see F8 below)
