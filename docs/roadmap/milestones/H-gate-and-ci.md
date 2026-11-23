# H-gate-and-ci

Status: **BUILT 2026-11-23 — see "Review" for the verdict** (branch `dev/h/gate-and-ci`, cut from `origin/main` `8dd7904a`; not pushed). Lane: **RELEASE** (it changes the gate every later milestone runs and the CI workflow).

Source: `docs/assessment/test-suite-review-2026-11-23.md` (local branch `dev/docs/project-review-2026-11-23`), steps 1 and 2, chosen by the researcher on 2026-11-23 in the coordinator session ("Gate settings and CI"). That choice named a standing permission for sessions to push work branches to the fork; the permission is **not given**, so this build keeps every push the coordinator's, on the researcher's approval, and names the permission as an open item. Companion part: `H-test-diet` (`dev/h/test-diet`), built the same day.

## Definition of done

- [x] **Workers and base.** `-n 4 --dist worksteal` wherever a local full run was `-n auto` (manifest, policy, `/gate`, `/ship`, `AGENTS.md`); the console's inner gate too. `select_test_gate.py --changed` defaults to `origin/main`; `/gate`, `test-gatekeeper` and `milestone-reviewer` say so.
- [x] **One machine-wide lock** around any full suite: `scripts/suite_lock.py`, a stale-lock rule, a second session waits; every full-suite command in the manifest runs through it. Tested (12 tests, two of them with real processes).
- [x] **Local gate = touched areas; CI = full gate.** Area `pr` is the area's `checkpoint` plus lint (`@checkpoint` in the manifest); a changed test file outside every area runs its folder at `pr`; the full suites run locally only at `closure` or as the unknown-path fallback. The policy's repair rule is replaced: after a repair or a merge of `main`, the affected tests locally and the full suites in CI.
- [x] **Finer console areas:** console-charting (with `src/scholar_harness/charting/`), console-discovery, console-screening, console-inception, before the console catch-all; their `inner` is 4 to 23 named files. **The selector's check fails** when a Python test file is named by no area's inner or checkpoint commands (the catch-all `tests --ignore=…` does not count), and when an area names a test path that does not exist.
- [x] **CI:** Python with `-n auto --dist worksteal` on the runner; `uv` cache (setup-uv `enable-cache`) in every job that installs uv; npm cache in both Node jobs (already there); the UI built once (build-wheel's `build:export`), the `research-ui` job no longer builds or sets up Python; a `concurrency` group that cancels a superseded pull-request run.
- [x] `tests/unit/test_select_test_gate.py` and the selector's own checks match; new tests for the lock and the workflow check.
- [x] An entry in `docs/decisions.md` with the two lists kept apart.
- [ ] Independent review: see "Review".

## What changed

| Where | Change |
| :-- | :-- |
| `scripts/suite_lock.py` (new) | Runs a command under one lock file for the machine (`NEXUS_SUITE_LOCK`, else `<temp>/nexus-scholar-suite.lock`, outside every checkout). A second caller waits and prints, every minute, the holder's pid, start time, folder and command; `--timeout N` gives up with exit 75; `--status` prints the holder. **Stale rule:** taken over when the holder process is no longer running on this host, when the lock is older than 3 h (`--max-age`), or when its file cannot be read; the takeover is printed. The command's exit code is returned and the lock released however it ends; a lock that is no longer ours is never removed. |
| `scripts/check_workflows.py` (new) | A local check of `.github/workflows/*.yml`: parses, triggers, `runs-on`, steps with `uses` or `run`, versioned actions, `needs` naming real jobs with no cycle, each downloaded artifact uploaded by a job it needs. It is the gate of a new `ci-workflows` area, so a workflow edit no longer falls back to the full suite locally. |
| `scripts/select_test_gate.py` | `@checkpoint` token (allowed at pr and closure only); test files outside areas run their folder at `pr`; the full-suite dedup knows the locked spelling; `--changed` defaults to `origin/main`; `--check` adds the unowned-test-file and missing-path rules. |
| `docs/architecture/test_gate_manifest.json` | Every full Python suite is `uv run python scripts/suite_lock.py -- uv run pytest -q -n 4 --dist worksteal` (areas' closure, the E3 tasks, the fallback); `area_defaults.pr` is `@checkpoint` plus ruff; the UI area runs the full vitest under the lock at checkpoint and pr, and adds the build and the browser suite (under the lock) at closure only; six new areas (four console, `packaging`, `ci-workflows`); 22 test files that no area named are now named (screening, console, agent-mcp, pipeline, harness-other, packaging). |
| `docs/architecture/test_gate_policy.md` | The four-gates and lanes tables; the selector section; a new "Local gate and CI gate" section (who pushes: open) and "One full suite at a time on the PC"; the repair rule replaced. |
| `.claude/skills/gate`, `.claude/skills/ship`, `.claude/agents/test-gatekeeper.md`, `.claude/agents/milestone-reviewer.md`, `AGENTS.md` | The same rules in the words each reader uses: base `origin/main`; `pr` is the touched areas; the full suites are CI's and the record cites the CI run; after a repair `/gate checkpoint`; the lock; the reviewer no longer asks for a local full run. |
| `.github/workflows/ci.yml` | `concurrency` (cancels only pull-request runs, never `main`); `astral-sh/setup-uv@v2` → `@v5` with `enable-cache: true` and `cache-dependency-glob: uv.lock` (4 jobs); `pytest -n auto --dist worksteal`; the `research-ui` job is pure Node: no uv, no Python, no `npm run build` (the app is built once, in `build-wheel`), plus `npm run tokens:check`, which the build's `prebuild` step used to run. |

## Required CI checks

Part 2 adds and removes no job: **12** required checks (`build-wheel`; `lint-and-smoke` × 6; `python-test`; `wheel-e2e` × 2; `research-ui`; `research-ui-browser`). With H-test-diet merged, **11** (`research-ui-browser` is gone). The coordinator merges on "all green"; a branch protection rule that lists `research-ui-browser` must drop it when H-test-diet merges.

## Choices made in the build (for the reviewer)

1. **The lock file lives in the user's temp folder,** one per Windows user. All sessions on this PC run as the same user, so it is machine-wide in practice; a session under another account would not see it. `NEXUS_SUITE_LOCK` overrides it.
2. **Stale after 3 hours,** well above the longest full run recorded (about 17 min for the Python suite, 20 min for the browser suite); it also covers a reused process id. A holder on another host is judged by age only.
3. **The lock wraps the command, not pytest itself:** any full suite (Python, vitest, the browser suite) uses the same wrapper; nested `uv run` costs about a second.
4. **Exit 75 (EX_TEMPFAIL)** when `--timeout` runs out, so a caller can tell "busy" from "failed". No timeout by default: a second session waits.
5. **`@checkpoint`** rather than copying each area's checkpoint into a `pr` list: one source of truth; the selector refuses it at inner and checkpoint.
6. **The UI area's full vitest is locked at checkpoint and pr**, and the browser suite and the build moved to closure: CI runs them on every pull request.
7. **What counts as owning a test file:** a path under `tests/` in an area's inner or checkpoint command; `--ignore=` paths and the bare `tests` do not count. The 22 files that failed the new rule went to the area whose source they import (listed in the manifest diff); `tests/e2e` is now in the pipeline area's checkpoint whole.
8. **`pyproject.toml` and `uv.lock` keep the full-suite fallback** (under the lock): a dependency change can touch every area. `hatch_build.py` and `scripts/build_mcpb.py` form a small `packaging` area.
9. **Finer console areas run their inner with `-n 4 --dist worksteal`,** as the console catch-all did: the four charting files took 112 s on one worker and 81 s on four.
10. **The checkpoint of console-screening stays all of `tests/console` plus `tests/authority`** (as the catch-all's): screening routes are read by most console tests. Charting, discovery and inception name their files.
11. **`setup-uv` v2 → v5** for `enable-cache`; `version: "0.12.5"` is kept. This is a major-version change of an action that could not be run here.
12. **The UI is built once in CI** by `build-wheel` (`build:export`, the build that ships). On `main` today the browser job still builds the app inside its Playwright `webServer`; H-test-diet removes that job. Until both merge, CI builds the UI twice instead of three times.
13. **The `research-ui` job drops Python:** its comment said vitest starts `uv run scholar-harness serve`; no test does (searched `apps/research-ui/tests` on `origin/main`: the only child process is `build-tokens.mjs --check` under Node).
14. **`concurrency`** groups by pull request number (else ref) and cancels only pull-request runs, so a push to `main` is never cancelled.

## Evidence

On the researcher's PC, branch `dev/h/gate-and-ci`, venv synced offline with `--extra dev --extra pdf --extra rag`. No network; CI not run.

| What | Command | Result |
| :-- | :-- | :-- |
| lock and workflow tests | `uv run pytest tests/unit/test_suite_lock.py tests/unit/test_check_workflows.py -q` | 18 passed (12 lock, including a real second process that waits for the first and starts after its end, and a lock from a finished process taken over; 6 workflow check) |
| selector tests | `uv run pytest tests/unit/test_select_test_gate.py -q` | 53 passed (45 updated or kept, 8 new) |
| selector check | `uv run python scripts/select_test_gate.py --check` | `OK: 24 tasks, 25 areas, 4 stages` |
| the check can fail | a temporary `tests/test_zz_probe.py`, then `--check` | `ERROR: tests/test_zz_probe.py belongs to no area`, exit 2; file removed |
| workflows | `uv run python scripts/check_workflows.py` | `OK: 3 workflows` |
| this change's own `pr` gate (the new rules) | `select_test_gate.py --changed origin/main --stage pr`: `git diff --check`; `check_workflows.py`; `pytest tests/unit/test_select_test_gate.py tests/unit/test_suite_lock.py tests/unit/test_check_workflows.py tests/conformance -q`; `--check`; `ruff check scripts/`; `pytest tests/unit -q` | all passed: 754 results (3 skipped) in 52 s; 732 in 62 s; ruff clean. About two minutes, against 917 s for the full Python suite on the same PC (H-test-diet's run) |
| a finer console area | `pytest` on the four charting files `-m "not slow"` | 121 tests: 112 s on one worker, 81 s with `-n 4 --dist worksteal` |
| lock status | `uv run python scripts/suite_lock.py --status` | `suite-lock: free (…\Temp\nexus-scholar-suite.lock)` |
| ruff (CI rules) | `uv run ruff check scripts/` | clean (one unused import fixed) |

The full Python suite was not run for this part: the diff changes no `src/` file; the selector picked the gate above, which is the point of the change.

## Not verified

- **CI.** Nothing was pushed. Only a real run shows: that `astral-sh/setup-uv@v5` accepts these inputs and caches, the `concurrency` expression, `-n auto` on the runner (cores, time), the `research-ui` job without Python, and how long CI now takes.
- **The lock under real contention between sessions.** Tested with two processes in one test; not yet seen with two Claude sessions starting suites together.
- **Branch protection** may list job names; none was renamed.
- **The cleanup session's deletions.** `dev/h/remove-rag-verify` removes `tests/kits/rag`, `tests/kits/verify` and their users and edits the manifest lines naming them. The new missing-path check fails if a deleted test path stays named, which is the intent; whichever branch merges second must pass `--check`.
- **Conflicts with H-test-diet** in `ci.yml`, the manifest's `research-ui` area, the policy's area paragraph, `/gate` and `tests/unit/test_select_test_gate.py`: whichever merges second merges `main`.

## Review

(filled after the `milestone-reviewer` run)
