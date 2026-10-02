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

## Delivery lanes and review cadence

Every task packet must declare one delivery lane before implementation starts.
The lane selects the minimum review cadence; it never waives a gate made
necessary by the actual changed surface.

| Lane | Use for | Minimum evidence and review cadence |
|---|---|---|
| `FAST` | Documentation, isolated UI, test-only corrections, and local refactors with no public or persisted semantic change | `inner` evidence, one scoped review, and a repair-delta check. No owner-repository full suite unless the changed path or a failed gate requires it. |
| `STANDARD` | A bounded behavior, packaging, or dependency change owned by one repository | `inner` and `checkpoint` evidence while editing; the owning repository's full suite once for the final PR candidate; one broad review and, if repaired, one review limited to the original findings and repair delta. |
| `RELEASE` | Contract semantics; artifact identity or persistence; public API, CLI, or MCP semantics; cross-kit compatibility; pins, vendors, or acceptance publication | The applicable `pr` and `closure` evidence, independent review/tester where the governing packet requires them, and cross-repository checks. |

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

For the current sequence, `T-110` is `STANDARD`; `T-120` and `T-130` are
`RELEASE`. Documentation, test-only, and isolated UI work that does not change
the above semantic boundaries normally uses `FAST`.

The full suite must still be rerun after any executable repair made following a
failed PR gate. Cross-platform repetition belongs to CI unless the failure is
platform-specific.
