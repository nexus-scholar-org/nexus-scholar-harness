# Agent controls (AG) track

Entrypoint for the AG track: authorization boundaries for agent-assisted
screening/publication. AG-03A proved protected-publisher feasibility for the
Windows MIC disposable flow; AG-03B's review lifecycle merged in PR #121 at
`fea8f40`; AG-03C delivered shared-gate enforcement with coherent publication
generations (merged in PR #125 at `2846066`). Next is AG-04. POSIX remains
unproven.

## Current

| Document | Role |
|---|---|
| [`agent_controls_plan.md`](./agent_controls_plan.md) | **Current execution plan** (status, ordered work, completion criteria). Supersedes the next-action text of AG-00 and the reassessment. |
| [`agent_controls_decision.md`](./agent_controls_decision.md) | Approved architecture decision (target invariants). |
| [`ag-03a-protected-publisher-feasibility.md`](./ag-03a-protected-publisher-feasibility.md) | Completed Windows MIC feasibility packet and its measured limits; POSIX unproven. |

## Completion record (AG-00 – AG-03C)

Dated packet documents were removed in the 2026-10-12 consolidation; the
must-survive facts are here and the originals remain in git history.

| Packet | Outcome | Evidence |
|---|---|---|
| **AG-00** — enforcement map (assessment) | Code-inspection map of every refusal/blocked path, cited by `file:line` at inspected commit `1c4255e`. Retained as evidence, not behaviour tests. | `1c4255e` |
| **AG-01** — authorization readiness | Delivered. Verdict for AG-03: **`BLOCKED_AUTHORITY_MODEL`** — no authority model was selected or enforced. Evidence ledger recorded (test/doc citations, integrity-only claims). | PR #105 base |
| **AG-02** — screening decision integrity | **Merged** — single-path, fail-closed integrity gates: exact per-screener coverage, duplicate rejection, unresolved preservation (`MAYBE`/`CONFLICT` are **not** coerced), parent/hash/freshness binding on the decisions collector. | PR #106, merge `0a701c7`; suite 1175 passed / 6 skipped |
| **AG-03A** — protected-publisher feasibility | **FEASIBILITY_PROVEN** — Windows MIC (Low-IL worker vs Medium publisher store, no admin, no container); POSIX unproven. | AG-03A packet result |
| **AG-03B** — review lifecycle | **Merged** — immutable snapshot buffer, preserved overrides with supersession, publisher-constructed identity, durable refusals, derived-output binding. | PR #121, merge `fea8f40` |
| **AG-03C** — shared gate + coherent generations | **Merged** (PR #125, `2846066`) — collect requires staged approval; generation.json commit point; downstream currentness enforced; crash/race/retry/audit-failure proven on Windows MIC. | PR #125; packet `ag-03c-publication-generations.md` |

**Integrity guarantees introduced by AG-02** (all typed, fail-closed, tested):

- `COVERAGE_INCOMPLETE` — a decision file missing an assigned study is refused, not accepted.
- `DUPLICATE_ENTRY` — duplicate study decisions are refused.
- `UNRESOLVED_FINALIZE_REFUSED` — finalising with unresolved `MAYBE`/`CONFLICT` is refused.
- Parent binding: `prepare` binds the protocol/corpus fingerprint; `collect` re-binds to
  registry-resolved parents (never the handoff text) and raises before writing on mismatch.

**Unresolved limitations (do not overclaim):**

1. **Production publication adoption delivered on the tested path.** AG-03C
   connects the shared authorization gate, coherent generations, downstream
   currentness and crash/race/retry handling on Windows MIC. Residual: POSIX
   unproven, single-host lock, no filesystem-durability claim beyond tmp+rename,
   dated LEGACY migration exception pending fixture migration.
2. **Tamper-evidence ≠ authorization.** A hash says *which* bytes, never *who* approved;
   a filesystem-privileged actor can still rewrite the registry and defeat replay detection.
3. Residual notes carried from AG-01/AG-02: alias canonicalisation and `accepted_at`
   string ordering; the handoff's embedded protocol summary is unaudited display text.

Do not cite the removed packet files as current status; use this record and
[`agent_controls_plan.md`](./agent_controls_plan.md).

