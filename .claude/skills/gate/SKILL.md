---
name: gate
description: Run the right test gate for what changed (inner, checkpoint or pr) instead of the full suite. Use after an edit ("/gate"), at a task boundary ("/gate checkpoint"), or before a PR ("/gate pr").
---

# /gate [inner|checkpoint|pr|closure] [base]

Default stage `inner`, default base `origin/main` (run `git fetch origin` first; a
stale local `main` selects hundreds of files and the full suite). Policy:
`docs/architecture/test_gate_policy.md`; selection rules:
`docs/architecture/test_gate_manifest.json` (`areas` first, then E3 tasks, then
the conservative full-suite fallback).

1. Show the selection: `uv run python scripts/select_test_gate.py --changed <base> --stage <stage>`.
2. Delegate the run to the `test-gatekeeper` agent with the stage and base. For
   `inner` with only one or two quick commands, running them directly is fine.
3. Relay the gatekeeper's table and verdict. For `checkpoint`, `pr` and `closure`,
   append a row to the Evidence table in the active `docs/roadmap/milestones/<M>.md`.

What each stage runs (H-gate-and-ci, 2026-11-23):
- `inner`: the area's own tests without `@pytest.mark.slow`, a few files for the
  console's finer areas (charting, discovery, screening, inception); a changed
  test file runs just that file; UI edits run `tsc` plus `vitest related`.
- `checkpoint`: the area plus its direct consumers, slow tests included.
- `pr`: the checkpoint again plus lint: the tests of what the change touched,
  minutes, not half an hour. The full suites are CI's, on the pull request; the
  record cites the CI run of the final commit. After a repair or a merge of
  `main`, run `checkpoint` again here and let CI rerun the full suites.
- `closure`: the full suites, for a `RELEASE` closure or a release.

A full suite on this PC (the `closure` stage, or the fallback for a path no area
matches) always runs through the machine-wide lock, which the manifest's commands
already include: `uv run python scripts/suite_lock.py -- <command>`. A second
session waits until the first finishes; `uv run python scripts/suite_lock.py
--status` shows who holds it. Never start a full suite outside the wrapper and
never use more than four workers (`-n 4 --dist worksteal`).

Never claim a gate passed without its output. If the selector falls back to the
full suite for an unknown path, say which path caused it, so the manifest can be
extended with a new area.
