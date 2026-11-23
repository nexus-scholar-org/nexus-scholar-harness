# Test Gate Selection Policy

**Status:** Active

**Applies to:** harness and canonical `scholar-*-kit` development

**Machine-readable map:** `docs/architecture/test_gate_manifest.json`

## Purpose

Fast feedback and merge confidence are different concerns. Running the full
harness suite after every edit wastes time and encourages agents to skip useful
tests entirely. This policy keeps the inner loop narrow while retaining full
coverage at the points where a revision becomes a merge or completion claim.

## Four gates

| Gate | When | Required evidence |
|---|---|---|
| `inner` | after an executable edit | tests mapped to the active task/path, touched-file lint where available, `git diff --check` |
| `checkpoint` | a task such as E3 `T-10` or `T-20` is complete | all tests for that task and its direct boundary; drift checks affected by the change |
| `pr` | the final executable candidate is ready to publish | locally: the touched areas' checkpoint, lint, type check and drift checks; the full suites, package/wheel smoke and the CI matrix in CI on the pull request (since H-gate-and-ci, 2026-11-23) |
| `closure` | packet adoption, a release, or cross-repository synchronization | full harness suite (locally under the machine-wide lock), conformance/mutation tests, pin/vendor checks, packaging smoke, CI matrix |

Documentation-only revisions run prose/link checks, drift checks required by
their governing packet, and `git diff --check`. They do not invalidate a full
suite result for the same executable tree.

## Delivery lanes and review cadence

Every task packet must declare one delivery lane before implementation starts.
The lane selects the minimum review cadence; it never waives a gate made
necessary by the actual changed surface.

Gate selection uses the task's current commit, changed paths, and evidence
record; a repair round reads its delta rather than replaying the complete task
history.

| Lane | Use for | Minimum evidence and review cadence |
|---|---|---|
| `FAST` | Documentation, isolated UI, test-only corrections, and local refactors with no public or persisted semantic change | `inner` evidence, one scoped review, and a repair-delta check. No owner-repository full suite unless the changed path or a failed gate requires it. |
| `STANDARD` | A bounded behavior, packaging, or dependency change owned by one repository | `inner` and `checkpoint` evidence while editing; the full suites once for the final PR candidate, in CI; one broad review and, if repaired, one review limited to the original findings and repair delta. The full suites for the final candidate are CI's (see "Local gate and CI gate"). |
| `RELEASE` | Contract semantics; artifact identity or persistence; public API, CLI, or MCP semantics; cross-kit compatibility; pins, vendors, or acceptance publication | The applicable `pr` and `closure` evidence (closure: the CI run of the final commit, see "Local gate and CI gate"), independent review/tester where the governing packet requires them, and cross-repository checks. |

Escalate a task to `RELEASE` immediately when its actual diff changes Contract
v1 semantics, an authoritative artifact's identity or publication behavior, a
public API/CLI/MCP contract, or a cross-kit compatibility boundary. A declared
lane may not be used to avoid that escalation.

After the first broad review, repairs must be bounded to accepted findings.
New unrelated P3 observations become follow-up tasks. A new broad review is
required only when a repair expands scope, changes a public/persisted boundary,
or invalidates recorded evidence. This preserves adversarial review while
preventing unrelated polish from repeatedly reopening an otherwise-ready PR.

## Evidence reuse

A test result may be reused by a coder, reviewer, or tester when all of these
are true:

1. the tested commit is an ancestor of the reviewed commit;
2. no executable file, dependency declaration, generated input, fixture, test,
   workflow, pin, or vendored toolkit changed after that result;
3. the command, repository, interpreter version, result, and tested commit SHA
   are recorded;
4. the reviewer independently checks the intervening path delta; and
5. no observed failure, merge-base change, or nondeterminism invalidates it.

Whitespace, spelling, or documentation-only repair commits therefore reuse the
last valid executable result. A reviewer reruns the smallest load-bearing test
needed to verify the repair, not the entire suite.

Evidence must not be reused across a rebase onto changed executable code, a pin
or lockfile change, a generated-fixture change, or a failed/flaky run.

## Selector

The selector prints the required commands; it deliberately does not execute
them:

```powershell
git fetch origin
uv run python scripts/select_test_gate.py --changed --stage inner   # usual form (base origin/main)
uv run python scripts/select_test_gate.py --path src/scholar_search/engine.py --stage checkpoint
uv run python scripts/select_test_gate.py --task T-120 --stage closure --format json
uv run python scripts/select_test_gate.py --check
```

`--changed [BASE]` adds every path changed since the merge base with `BASE`
(default `origin/main`, so fetch first: a stale local `main` once selected 696
files and the full suite), including staged, unstaged and untracked files. In Claude Code,
`/gate [stage]` runs this and the selected commands.

Selection, in order:

1. **Areas** (`areas` in the manifest, added 2026-11-03 after the one-package
   merge). Each non-Markdown path takes the first area whose globs match it:
   screening, contracts, authority, console, inception, recon, pipeline,
   workspace-audit, harness-cli, a `src/scholar_harness/**` catch-all, one area
   per package under `src/scholar_*`, the selector itself, and `research-ui`
   (typecheck, `lint:ui` and `vitest related` for the touched files at inner;
   typecheck, `lint:ui` and the full vitest under the lock at checkpoint and pr;
   the build at closure, and in CI on every pull request; never the Python suite;
   there is no browser suite since 2026-11-23). The console has finer areas before its
   catch-all: console-charting (with `src/scholar_harness/charting/`),
   console-discovery, console-screening and console-inception, so `inner` is a
   few files; packaging and ci-workflows (`scripts/check_workflows.py`) are areas
   too. Area `pr` defaults to the area's `checkpoint` plus lint (`@checkpoint`
   in the manifest); area `closure` to the full Python suite once, under the lock,
   with four workers (`-n 4 --dist worksteal`). `select_test_gate.py --check`
   fails when a Python test file is named by no area's inner or checkpoint
   commands (the catch-all `tests` does not count) or an area names a test path
   that does not exist.
2. **Changed test files** outside every area run themselves at inner, their
   directory at checkpoint and pr, and the full suite (under the lock) at closure.
3. **E3 tasks** (`T-10`…`T-230`) apply to remaining paths and to explicit
   `--task`; they are kept as history.
4. **Docs:** prose takes the light gate; consumed and baseline-locked docs keep
   their boundary and drift checks.
5. **Fallback:** an executable path that nothing above matches takes the full
   suite, under the lock. Add an area rather than living with the fallback. An empty selection is
   an error, not permission to skip testing.

**Slow tests.** Tests that take about 2.5 s or more (real subprocesses, real
servers, real indexes) carry `@pytest.mark.slow`. Inner area gates run
`-m "not slow"`; checkpoint, pr and closure run them. Measured on 2026-11-03
(Windows, 8 logical cores): the full suite took 10 m 25 s serially and about
5 m 47 s with `-n auto` (on 2026-11-23, 6,590 tests took 917 s with `-n 4 --dist worksteal`); inner area gates for the screening, search, inception,
protocol and agent areas took 6–29 s. Mark a new test slow when it exceeds the
threshold; a test that starts a server must stop the whole process tree (on
Windows, `taskkill /T /F`), or the orphan locks the venv's console scripts.

## E3 cadence

- `T-10` through `T-95`: targeted RAG-kit tests in the inner loop; the full
  RAG-kit suite once for the final canonical kit PR candidate.
- `T-100`: targeted Agent-kit capability/parity tests; its full suite once for
  the Agent-kit PR candidate.
- `T-110`: isolated install/import and wheel checks in both affected kits.
- `T-120` through `T-150`: focused harness conformance during development;
  full harness, pins, vendoring, wheel, and CI matrix at closure.

For the current sequence, `T-110` is `STANDARD`; `T-120` and `T-130` are
`RELEASE`. Documentation, test-only, and isolated UI work that does not change
the above semantic boundaries normally uses `FAST`.

After an executable repair (a review finding, a failed gate) or a merge of `main`
into the branch, run the affected areas' tests locally (the selector at
`checkpoint` against `origin/main`); CI runs the full suites again on the new
commit. A local full-suite rerun is not required (this replaces, on 2026-11-23,
the rule that asked for the whole suite again locally after a repair).
Cross-platform repetition belongs to CI unless the failure is platform-specific.

## Local gate and CI gate (H-gate-and-ci, 2026-11-23)

One PC (8 cores) is shared by two to four sessions. The local gate therefore runs
what a change touched; CI, which runs off the PC, is the full gate.

- **Local:** the tests of the areas the change touched (the selector's
  `checkpoint`, which `pr` reuses), plus lint and the type check. Minutes, not
  half an hour. Compare with `origin/main` (`--changed` defaults to it; fetch
  first), never a stale local `main`.
- **CI:** the full Python suite (`-n auto` on the runner), the UI jobs
  (type check, unit tests, build), the wheel smoke and the cross-OS jobs, on the
  pull request. A part's record cites the CI run of its final commit (every
  required check green) instead of a local full-suite table. Nothing merges on a
  red or unfinished CI.
- **After a repair or a merge of `main`:** the affected tests locally (the
  selector at `checkpoint` against `origin/main`), and the full suites again in CI
  on the new commit. A local full-suite rerun is not required.
- **`RELEASE` closure evidence** is the CI run of the part's final commit with
  every required check green. Until it exists the record says "closure: CI run
  of <sha>, not yet run" and the part is not ready to merge.
- **Full suites on the PC** run only for a release, when a path matches no area
  (the fallback), or when the researcher asks, and always through the lock
  below. The selector's `closure` stage prints them for those cases.

**Who pushes (open).** CI runs on a pull request (a draft is enough) or a push to
`main` or `develop`, so a work branch must be pushed and have a pull request open. Every push is approved by
the researcher today, and the coordinator session pushes on that approval; a build
session never pushes. A standing permission for sessions to push their work
branch to the fork and open a draft pull request, so CI can run while they work,
has been proposed and is **not given**. Until it is, a build session records "full suites: CI, not yet run" and
names the commit; the coordinator pushes on the researcher's word, waits for CI,
and merges only on all green.

## One full suite at a time on the PC

`scripts/suite_lock.py` holds one lock for the whole machine
(`NEXUS_SUITE_LOCK`, else `<temp>/nexus-scholar-suite.lock`, outside every
checkout and worktree). Every full-suite command in the manifest runs through it:

```powershell
uv run python scripts/suite_lock.py -- uv run pytest -q -n 4 --dist worksteal
uv run python scripts/suite_lock.py --status
```

A second session waits, printing every minute who holds the lock (process id,
start time, folder, command), and starts when it is released. `--timeout N`
gives up after `N` seconds with exit code 75. The lock is released however the
command ends, and the command's exit code is returned. **Stale-lock rule:** the
lock is taken over when its holder process is no longer running on this machine,
when it is older than three hours (`--max-age`), or when its file cannot be read;
the takeover is printed. Never start a full suite outside the wrapper, and never
use more than four workers locally (`-n 4 --dist worksteal`): the PC stopped once
with three suites running.
