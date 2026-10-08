# E3 RAG Chroma Recovery — Task Context Capsule

**Status:** ready for dispatch  
**Task:** `E3-RAG-CHROMA-REPLACEMENT-RECOVERY`  
**Delivery lane:** `RELEASE` — replacement changes persisted backend state and
the E3 currentness boundary.  
**Owner repository:** `nexus-scholar-org/scholar-rag-kit`  
**Required base:** canonical RAG-kit commit
`f108fa897147f4c837760c81b558d1b82a044fdf` (the harness-pinned revision).  
**Harness base:** `657b9d5` (PR #64), after E2 runtime acceptance and E3 T-130
Stage-6 integration.

## Goal

Reproduce and fix the reported real-Chroma `ATOMIC_COMMIT_FAILED` on the E3
replacement path. The fix must preserve the seven-step E3 boundary: a failed
replacement leaves the prior visible index intact, and a successful replacement
is verifiable by the kit's typed backend query.

This is a **canonical kit task**. Do not patch `tools/scholar-rag-kit/` in the
harness. A harness vendor/pin synchronization PR is a separate follow-up after
the canonical kit PR merges.

## Stable sources — read once

1. `docs/architecture/wp01_packet_e3_implementation_handoff.md` §6.2,
   §6.4, §8 rows T-60/T-80/T-90, and §11.4.
2. `docs/architecture/test_gate_policy.md` — `RELEASE` lane and E3 cadence.
3. `.agents/skills/scholar-rag-kit/SKILL.md` — typed index API/CLI boundary.
4. In the canonical kit at the required base: `src/scholar_rag/replacement.py`,
   `src/scholar_rag/index_service.py`, and their directly mapped tests.

The capsule and a repair delta are the working context for later rounds. Do not
reload the entire E3 handoff unless an immutable boundary, public surface, pin,
merge base, or selected gate changes.

## Established facts

- Harness PR #65 is merged. Its Stage 6 calls the typed `IndexService`; it does
  not authorize bypassing the replacement protocol or falling back to the legacy
  `ScholarIndexer` path.
- A reported integration run reaches the real backend but returns
  `ATOMIC_COMMIT_FAILED` during replacement. This capsule does **not** assert a
  root cause: first reproduce it in a minimal real-Chroma test and retain the
  original exception/cause as evidence.
- `ATOMIC_COMMIT_FAILED` is a correct fail-closed outcome for an interrupted or
  failed write, but it is not acceptable as the normal result of a healthy
  replacement run.
- Harness-side T-140 conformance and T-150 documentation remain open. Do not
  start either in this task.

## Allowed and forbidden scope

**Allowed in the canonical kit:** the smallest source and test paths required
to reproduce and repair the real-Chroma replacement failure. Begin with the
replacement/service modules and their direct test files; record any scope
extension in the capsule before editing it.

**Forbidden:** Contract v1 models or schemas; harness source/tests; vendored
tool snapshots; `plugins.json`; generated package pins; agent-kit code; MCP
policy; unrelated lint cleanup; weakened error mapping; mock-only success used
as evidence for a Chroma failure.

## Acceptance conditions

1. A regression test uses the real Chroma backend and reproduces the pre-fix
   failure at the canonical base.
2. The repaired healthy replacement succeeds, yields exactly the declared
   visible chunk set, and passes `verify_backend`.
3. A forced replacement failure still reports `ATOMIC_COMMIT_FAILED`, preserves
   the previous visible state, and publishes no false-success result.
4. The typed Python API and CLI retain the same outcome/error semantics.
5. Existing E3 identity, manifest, recovery, and replacement tests remain
   green. Run the kit's full suite once only for the final PR candidate, then
   the applicable release gates/CI.
6. The PR body records the exact real-Chroma reproducer, original failure,
   repaired behavior, base/head SHAs, and any known baseline failures.

## Dispatch sequence

1. Create a clean canonical-kit checkout from the required base; verify source
   resolution is the checkout, not `tools/` or an installed stale wheel.
2. Run the narrow replacement/service tests and construct the smallest
   real-Chroma reproducer. If it does not reproduce, stop and report the exact
   environment/version delta rather than guessing a fix.
3. Implement only the demonstrated repair and add the regression plus the
   forced-failure preservation test.
4. Run inner and checkpoint gates while editing; run the owner suite once for
   the final candidate; obtain an independent review focused on the persisted
   replacement semantics.
5. Publish only through the kit fork and canonical kit PR. After merge, record
   the full merge SHA.
6. Then create a **separate** harness synchronization PR: vendor the exact kit
   commit, update the full SHA pin, regenerate `nexus_scholar_pins.json`, and
   only then resume T-140.

## Evidence record to update after each repair

```yaml
base_sha: f108fa897147f4c837760c81b558d1b82a044fdf
head_sha: <candidate SHA>
changed_paths: []
reproducer:
  command: <exact command>
  before: <failure including cause>
  after: <result>
open_findings: []
known_baseline_failures: []
next_gate: inner|checkpoint|pr|closure
```

## Stop conditions

Stop and report rather than broadening scope when the failure depends on a
different package, a changed Chroma version, an undeclared dependency, or a
missing environment precondition. Any resulting cross-kit or packaging repair
needs its own capsule and PR sequence.
