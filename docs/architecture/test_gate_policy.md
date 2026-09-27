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
| `pr` | the final executable candidate is ready to publish | the owning repository's full suite once, package/wheel smoke where applicable, lint and drift checks |
| `closure` | packet adoption or cross-repository synchronization | full harness suite, conformance/mutation tests, pin/vendor checks, packaging smoke, CI matrix |

Documentation-only revisions run prose/link checks, drift checks required by
their governing packet, and `git diff --check`. They do not invalidate a full
suite result for the same executable tree.

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
uv run python scripts/select_test_gate.py --task T-10 --stage inner
uv run python scripts/select_test_gate.py --task T-20 --stage checkpoint
uv run python scripts/select_test_gate.py --path tools/scholar-rag-kit/src/scholar_rag/chunker.py --stage inner
uv run python scripts/select_test_gate.py --task T-120 --stage closure --format json
uv run python scripts/select_test_gate.py --check
```

Multiple tasks and paths are unioned in deterministic order. Path inference is
conservative: if a changed executable path matches no rule, the selector emits
the full-suite fallback for the requested repository/stage. An empty selection
is an error, not permission to skip testing.

## E3 cadence

- `T-10` through `T-95`: targeted RAG-kit tests in the inner loop; the full
  RAG-kit suite once for the final canonical kit PR candidate.
- `T-100`: targeted Agent-kit capability/parity tests; its full suite once for
  the Agent-kit PR candidate.
- `T-110`: isolated install/import and wheel checks in both affected kits.
- `T-120` through `T-150`: focused harness conformance during development;
  full harness, pins, vendoring, wheel, and CI matrix at closure.

The full suite must still be rerun after any executable repair made following a
failed PR gate. Cross-platform repetition belongs to CI unless the failure is
platform-specific.
