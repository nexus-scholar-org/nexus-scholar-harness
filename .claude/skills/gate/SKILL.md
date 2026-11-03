---
name: gate
description: Run the right test gate for what changed (inner, checkpoint or pr) instead of the full suite. Use after an edit ("/gate"), at a task boundary ("/gate checkpoint"), or before a PR ("/gate pr").
---

# /gate [inner|checkpoint|pr|closure] [base]

Default stage `inner`, default base `main`. Policy:
`docs/architecture/test_gate_policy.md`; selection rules:
`docs/architecture/test_gate_manifest.json` (`areas` first, then E3 tasks, then
the conservative full-suite fallback).

1. Show the selection: `uv run python scripts/select_test_gate.py --changed <base> --stage <stage>`.
2. Delegate the run to the `test-gatekeeper` agent with the stage and base. For
   `inner` with only one or two quick commands, running them directly is fine.
3. Relay the gatekeeper's table and verdict. For `checkpoint`, `pr` and `closure`,
   append a row to the Evidence table in the active `docs/roadmap/milestones/<M>.md`.

What each stage costs (measured 2026-11-03, Windows, 8 cores):
- `inner`: the area's own tests without `@pytest.mark.slow`, usually seconds to
  about a minute; a changed test file runs just that file; UI edits run
  `tsc` plus `vitest related` for the touched files.
- `checkpoint`: the area plus its direct consumers, slow tests included.
- `pr`: the full Python suite once, in parallel (`-n auto`), plus lint; UI changes
  add vitest, build and Playwright. Run it once per final executable commit;
  documentation-only repairs reuse it (policy §"Evidence reuse").

Never claim a gate passed without its output. If the selector falls back to
`uv run pytest -q` for an unknown path, run it — and say which path caused it, so
the manifest can be extended with a new area.
