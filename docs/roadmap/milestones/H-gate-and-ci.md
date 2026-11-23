# H-gate-and-ci

Status: **BUILT 2026-11-23 — see "Review" for the verdict** (branch `dev/h/gate-and-ci`, cut from `origin/main` `8dd7904a`; not pushed). Lane: **RELEASE** (it changes the gate every later milestone runs and the CI workflow).

Source: `docs/assessment/test-suite-review-2026-11-23.md` (local branch `dev/docs/project-review-2026-11-23`), steps 1 and 2, chosen by the researcher on 2026-11-23 in the coordinator session ("Gate settings and CI"). That choice named a standing permission for sessions to push work branches to the fork; the permission is **not given**, so this build keeps every push the coordinator's, on the researcher's approval, and names the permission as an open item. Companion part: `H-test-diet` (`dev/h/test-diet`), built the same day.

## Definition of done

- [x] **Workers and base.** `-n 4 --dist worksteal` wherever a local full run was `-n auto` (manifest, policy, `/gate`, `/ship`, `AGENTS.md`); the console's inner gate too. `select_test_gate.py --changed` defaults to `origin/main`; `/gate`, `test-gatekeeper` and `milestone-reviewer` say so.
- [x] **One machine-wide lock** around any full suite: `scripts/suite_lock.py`, the operating system's lock on one file, freed when its holder process ends (the stale-lock rule), a second session waits; every full-suite command in the manifest runs through it. Tested (11 tests, three of them with real processes).
- [x] **Local gate = touched areas; CI = full gate.** Area `pr` is the area's `checkpoint` plus lint (`@checkpoint` in the manifest); a changed test file outside every area runs its folder at `pr`; no E3 task runs the full suite at `pr` either; the full suites run locally only for a release, as the unknown-path fallback, or when the researcher asks (the selector's `closure` stage prints them). The policy's repair rule is replaced: after a repair or a merge of `main`, the affected tests locally and the full suites in CI.
- [x] **Finer console areas:** console-charting (with `src/scholar_harness/charting/`), console-discovery, console-screening, console-inception, before the console catch-all; their `inner` is 4 to 23 named files. **The selector's check fails** when a Python test file is named by no area's inner or checkpoint commands (the catch-all `tests --ignore=…` does not count), and when an area or an E3 task names a test path that does not exist.
- [x] **CI:** Python with `-n auto --dist worksteal` on the runner; `uv` cache (setup-uv `enable-cache`) in every job that installs uv; npm cache in both Node jobs (already there); the UI built once (build-wheel's `build:export`), the `research-ui` job no longer builds or sets up Python; a `concurrency` group that cancels a superseded pull-request run.
- [x] `tests/unit/test_select_test_gate.py` and the selector's own checks match; new tests for the lock and the workflow check.
- [x] An entry in `docs/decisions.md` with the two lists kept apart.
- [ ] **Closure evidence (RELEASE):** the CI run of the final commit with every required check green. Not yet run: nothing is pushed.
- [ ] Independent review: see "Review".

## What changed

| Where | Change |
| :-- | :-- |
| `scripts/suite_lock.py` (new) | Runs a command under the operating system's lock on one file for the machine (`NEXUS_SUITE_LOCK`, else `<temp>/nexus-scholar-suite.lock`, outside every checkout): `msvcrt.locking` on Windows, `fcntl.flock` elsewhere. `<lock>.json` names the holder (pid, host, start time, folder, command). A second caller waits and prints, every minute, who holds it; `--timeout N` gives up with exit 75; `--status` prints the holder. **Stale rule:** the system frees the lock when its holder process ends, however it ends, so a lock cannot outlive its holder and nothing is ever deleted or taken over by another caller; a holder file left behind is replaced, and that is printed. A holder alive for over 3 h (`--max-age`) is reported, not broken. The command's exit code is returned and the lock released however it ends. |
| `scripts/check_workflows.py` (new) | A local check of `.github/workflows/*.yml`: parses, triggers, `runs-on`, steps with `uses` or `run`, versioned actions, `needs` naming real jobs with no cycle, each downloaded artifact uploaded by a job it needs. It is the gate of a new `ci-workflows` area, so a workflow edit no longer falls back to the full suite locally. |
| `scripts/select_test_gate.py` | `@checkpoint` token (allowed at pr and closure only); test files outside areas run their folder at `pr`; the full-suite dedup knows the locked spelling; `--changed` defaults to `origin/main`; `--check` adds the unowned-test-file and missing-path rules. |
| `docs/architecture/test_gate_manifest.json` | Every full Python suite is `uv run python scripts/suite_lock.py -- uv run pytest -q -n 4 --dist worksteal` (areas' and E3 tasks' closure, and the fallback; no task runs it at `pr`); `area_defaults.pr` is `@checkpoint` plus ruff; the UI area runs the full vitest under the lock at checkpoint and pr, and adds the build and the browser suite (under the lock) at closure only; six new areas (four console, `packaging`, `ci-workflows`); 22 test files that no area named are now named (screening, console, agent-mcp, pipeline, harness-other, packaging). |
| `docs/architecture/test_gate_policy.md` | The four-gates and lanes tables; the selector section; a new "Local gate and CI gate" section (who pushes: open) and "One full suite at a time on the PC"; the repair rule replaced. |
| `.claude/skills/gate`, `.claude/skills/ship`, `.claude/agents/test-gatekeeper.md`, `.claude/agents/milestone-reviewer.md`, `AGENTS.md` | The same rules in the words each reader uses: base `origin/main`; `pr` is the touched areas; the full suites are CI's and the record cites the CI run; after a repair `/gate checkpoint`; the lock; the reviewer no longer asks for a local full run. |
| `.github/workflows/ci.yml` | `concurrency`: a pull request's runs share a group and a newer push cancels the older run; a push to `main` or `develop` is grouped by its own run id, so it is never queued, replaced or cancelled; `astral-sh/setup-uv@v2` → `@v5` with `enable-cache: true` and `cache-dependency-glob: uv.lock` (4 jobs); `pytest -n auto --dist worksteal`; the `research-ui` job is pure Node (no uv, no Python) and keeps its standalone build. |

## Required CI checks

Part 2 adds and removes no job: **12** required checks (`build-wheel`; `lint-and-smoke` × 6; `python-test`; `wheel-e2e` × 2; `research-ui`; `research-ui-browser`). With H-test-diet merged, **11** (`research-ui-browser` is gone). The coordinator merges on "all green"; a branch protection rule that lists `research-ui-browser` must drop it when H-test-diet merges.

## Choices made in the build (for the reviewer)

1. **The lock is the operating system's file lock** (first build: a lock file created with `O_EXCL` and stale rules; review round 1 reproduced a race where a waiter judged a just-created, not yet written file stale and deleted it, and two waiters could both take over a dead holder's lock). With the system lock there is no takeover and nothing to delete. **It lives in the user's temp folder,** one per Windows user. All sessions on this PC run as the same user, so it is machine-wide in practice; a session under another account would not see it. `NEXUS_SUITE_LOCK` overrides it.
2. **A holder alive for over 3 hours is reported, not broken,** well above the longest full run recorded (about 17 min for the Python suite, 20 min for the browser suite): it may be stuck, and stopping a session is the researcher's call. On Windows, Ctrl+C ends `uv` but pytest-xdist workers may outlive the wrapper; the lock is then free while they finish (not handled).
3. **The lock wraps the command, not pytest itself:** any full suite (Python, vitest, the browser suite) uses the same wrapper; nested `uv run` costs about a second.
4. **Exit 75 (EX_TEMPFAIL)** when `--timeout` runs out, so a caller can tell "busy" from "failed". No timeout by default: a second session waits.
5. **`@checkpoint`** rather than copying each area's checkpoint into a `pr` list: one source of truth; the selector refuses it at inner and checkpoint.
6. **The UI area's full vitest is locked at checkpoint and pr**, and the browser suite and the build moved to closure: CI runs them on every pull request.
7. **No E3 task runs the full suite at `pr`** (review round 1): T-120, T-130, T-140 and T-160 to T-230 run their checkpoint plus ruff at `pr`, the full suite at `closure`; a test says so. **What counts as owning a test file:** a path under `tests/` in an area's inner or checkpoint command; `--ignore=` paths and the bare `tests` do not count. The 22 files that failed the new rule went to the area whose source they import (listed in the manifest diff); `tests/e2e` is now in the pipeline area's checkpoint whole.
8. **`pyproject.toml` and `uv.lock` keep their E3 task T-110** (the RAG and agent kits' suites at `pr`, as on `main`); the full suites for a dependency change are CI's. `hatch_build.py` and `scripts/build_mcpb.py` form a small `packaging` area.
9. **Finer console areas run their inner with `-n 4 --dist worksteal`,** as the console catch-all did: the four charting files took 112 s on one worker and 81 s on four.
10. **The checkpoint of every console area is all of `tests/console` plus `tests/authority`** (as the catch-all's), plus the users outside that folder (review round 1): discovery adds `tests/unit/test_discovery_stage.py`, `tests/kits/agent/test_mcp_assistant.py`, `tests/kits/agent/test_mcp_workspace_proposals.py`, `tests/kits/search/test_provider_resilience.py`; inception adds `tests/inception`, `tests/recon`, `tests/kits/agent/test_mcp_assistant.py`, `tests/pipeline/test_golden_recon_cassette.py`; screening adds `tests/test_read_store.py`. Only `inner` is narrow.
11. **`setup-uv` v2 → v5** for `enable-cache`; `version: "0.12.5"` is kept. This is a major-version change of an action that could not be run here.
12. **The UI is built once per kind in CI:** the export in `build-wheel` (shared with every wheel job through the artifact) and the standalone app in `research-ui`. The first build of this part dropped the standalone build; review round 1 showed it is the only build that compiles the console proxy route (`app/api/console/[...path]/route.ts`) and the redirects (the export compiles `.tsx` pages only), so it stays. The third build, inside the browser job's Playwright `webServer`, goes when H-test-diet removes that job; this part does not share one build between those two jobs.
13. **The `research-ui` job drops Python:** its comment said vitest starts `uv run scholar-harness serve`; no test does (searched `apps/research-ui/tests` on `origin/main`: the only child process is `build-tokens.mjs --check` under Node).
14. **`concurrency`** groups a pull request's runs by its number and cancels the superseded one; other runs are grouped by their own run id (review round 1: grouping pushes to `main` by ref would queue them and replace a pending one).

## Evidence

On the researcher's PC, branch `dev/h/gate-and-ci`, venv synced offline with `--extra dev --extra pdf --extra rag`. No network; CI not run.

| What | Command | Result |
| :-- | :-- | :-- |
| lock and workflow tests (first build) | same files | 18 passed (12 lock, 6 workflow check), on the first lock |
| lock tests after round 1 | `uv run pytest tests/unit/test_suite_lock.py -q --durations=4` | 11 passed: a lock held in this process makes a second caller wait and give up; a real holder process killed outright has its lock freed by the system; an empty holder file (the round-1 race) never frees the lock; a 4-hour holder is reported, not broken; a real second process starts its command after the first's end (3.3 s, marked slow) |
| selector, lock and workflow tests after round 1 | `uv run pytest tests/unit/test_select_test_gate.py tests/unit/test_suite_lock.py tests/unit/test_check_workflows.py -q` | 72 passed (55 selector, 11 lock, 6 workflow) |
| selector tests | `uv run pytest tests/unit/test_select_test_gate.py -q` | 53 passed (45 updated or kept, 8 new) |
| selector check | `uv run python scripts/select_test_gate.py --check` | `OK: 24 tasks, 25 areas, 4 stages` |
| the check can fail | a temporary `tests/test_zz_probe.py`, then `--check` | `ERROR: tests/test_zz_probe.py belongs to no area`, exit 2; file removed |
| workflows | `uv run python scripts/check_workflows.py` | `OK: 3 workflows` |
| this change's own `pr` gate (the new rules), first build `c9d549cc` | `select_test_gate.py --changed origin/main --stage pr`: `git diff --check`; `check_workflows.py`; `pytest tests/unit/test_select_test_gate.py tests/unit/test_suite_lock.py tests/unit/test_check_workflows.py tests/conformance -q`; `--check`; `ruff check scripts/`; `pytest tests/unit -q` | all passed: 754 results (3 skipped) in 52 s; 732 in 62 s; ruff clean. About two minutes, against 917 s for the full Python suite on the same PC (H-test-diet's run) |
| the same gate after round 1 | `9c016482`, same six commands | all passed: 755 results (3 skipped) in 131 s; 733 in 120 s; `--check` OK; ruff clean (slower than the first run; the PC was not idle) |
| a finer console area | `pytest` on the four charting files `-m "not slow"` | 121 tests: 112 s on one worker, 81 s with `-n 4 --dist worksteal` |
| lock status | `uv run python scripts/suite_lock.py --status` | `suite-lock: free (…\Temp\nexus-scholar-suite.lock)` |
| ruff (CI rules) | `uv run ruff check scripts/` | clean (one unused import fixed) |

The full Python suite was not run for this part: the diff changes no `src/` file; the selector picked the gate above, which is the point of the change.

## Not verified

- **Closure (RELEASE).** The CI run of the final commit is this part's closure evidence; it does not exist until the coordinator pushes and opens the pull request.
- **CI.** Nothing was pushed. Only a real run shows: that `astral-sh/setup-uv@v5` accepts these inputs and caches, the `concurrency` expression, `-n auto` on the runner (cores, time), the `research-ui` job without Python, and how long CI now takes.
- **The lock under real contention between sessions.** Tested with real processes in tests; not yet seen with two Claude sessions starting suites together. `fcntl.flock` (Linux, macOS) is written but ran nowhere here.
- **Branch protection** may list job names; none was renamed.
- **The cleanup session's deletions.** `dev/h/remove-rag-verify` removes `tests/kits/rag`, `tests/kits/verify` and their users and edits the manifest lines naming them. The missing-path check (areas and, since round 1, E3 tasks) fails if a deleted test path stays named, which is the intent; whichever branch merges second must pass `--check`.
- **Conflicts with H-test-diet** in `ci.yml`, the manifest's `research-ui` area, the policy's area paragraph, `/gate` and `tests/unit/test_select_test_gate.py`: whichever merges second merges `main`.

## Review

**Round 1** (`milestone-reviewer`, on `c9d549cc`): **CHANGES**, 5 P2 and 5 P3. Fixed in the next commit:

1. (P2) Lock race at creation and takeover (reproduced on this PC): replaced by the system file lock (choice 1); tests for the race.
2. (P2) The new console areas' checkpoints missed users of their code: all three now run `tests/console tests/authority` plus the outside users found (choice 10).
3. (P2) E3 tasks still ran the full suite at `pr`: eleven tasks set to checkpoint plus ruff; a test.
4. (P2) `concurrency` grouped pushes to `main` by ref: grouped by run id now (choice 14).
5. (P2) RELEASE closure evidence contradicted itself: the policy says the CI run of the final commit is that evidence; the DoD box stays open until it exists.
6. (P3) `pyproject.toml`/`uv.lock` wording: corrected (choice 8, decision 10).
7. (P3) Dropping the standalone build lost the proxy route's compilation: the build is kept (choice 12).
8. (P3) The missing-path check skipped E3 tasks: it covers them; a test.
9. (P3) The two-process lock test exceeded the slow threshold: marked slow.
10. (P3) "CI runs on a pushed branch": the policy and decision 1 say a pull request (a draft is enough) must be open.

Reviewer follow-ups also done: `.agents/skills/pull-request-gate/SKILL.md` no longer says "full suite for executable"; `ci-workflows` has a `closure`. Not done: `-n 4` for a changed test file's folder run at `pr`; checking argparse's `const` rather than the constant; the parked imports of `tests/integrations/test_rigor_upgrades.py` and `tests/test_parked_labels.py` (owned by harness-other only).
