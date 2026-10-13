# Agent controls: current execution plan

**Updated:** 2026-10-13. **Lane for this planning/protocol PR:** FAST.
**Decision:** [Approved architecture](agent_controls_decision.md).
**Next product work:** UI-07/HCM-06 prerequisite reconciliation and boundary specification, then separately reviewed actions and connected UI-04. AG-05 remains conditional on a real screening backend, independent labels and prospective design.

## Current status and provenance

AG-01 readiness and AG-02 integrity are delivered in merged [PR #106](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/106),
merge `0a701c786b9a610606722a6c44d70fcddd4c58cb`. Nine PR checks passed.
The AG-01 evidence ledger records 1175 passed, 6 skipped, zero failed at its
final candidate. These are dated release records, not a suite rerun claim.
AG-00 and the post-AG-02 reassessment (both historical; summarized in this folder's README completion record)
remain historical evidence. This current plan supersedes their next-action text.

The researcher approved the protected local publisher/restricted scientific
worker on 2026-10-12 and authorized initializing the UAV protocol. AG-03A is
FEASIBILITY_PROVEN for the Windows MIC disposable flow (see the AG-03A packet
result); POSIX remains unproven. AG-03B merged in [PR #121](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/121) at `fea8f40cd41028d1cf9cd0df20e21aee15af964f`; AG-03C delivered (shared gate, coherent generations, downstream currentness, crash/race/retry proofs on the tested Windows deployment; POSIX unproven). AG-04 merged (PR #130 at `28e5c42`): one deterministic CLI worker with researcher review/override/approve/defer on the protected publisher; AG-03C gate and currentness reused untouched.

## Ordered work

| Packet | Status | Exit condition |
|---|---|---|
| AG-00 | Assessment retained | Historical code-inspection map preserved. |
| AG-01 | Readiness delivered | Its unresolved host authority question now routes to AG-03A. |
| AG-02 | Merged, bounded integrity | Single-screener coverage/duplicates/unresolved/hash/freshness gates; no authority claim. |
| AG-03A | FEASIBILITY_PROVEN (Windows MIC disposable flow); POSIX unproven | Windows MIC proves the restricted worker cannot approve, impersonate the operator, modify publisher state, or overwrite final output; POSIX arrangement still unproven. Next: AG-03B. |
| AG-03B | Delivered (PR #121 merged at fea8f40); single-screener review lifecycle on Windows MIC | Immutable snapshot buffer, preserved overrides with supersession links, publisher-constructed operator identity, durable refusal records, derived-output binding; AG-03C (generations, currentness, crash recovery) still open. |
| AG-03C | Merged (PR #125 at `2846066`); shared gate + coherent generations on Windows MIC | Collect requires staged approval; generation.json commit point; extraction/coordinator/handoff enforce currentness; crash/race/retry/audit-failure proven; POSIX unproven; dated LEGACY migration exception recorded. |
| AG-04 | Merged (PR #130 at `28e5c42`); CLI worker + review on Windows MIC | Deterministic recommend scaffolds, single-buffer review display, publisher-owned operator identity with Low-IL refusal, preserved overrides, defer/cancel states, CURRENT downstream publication; POSIX unproven. |
| AG-05 | Conditional; not the immediate product task | Held-out scientific evaluation after calibration; measured error/correction/time/bias and proceed/revise/stop decision. |
| AG-06/07 | Deferred | Charting then synthesis require separate evidence-based decisions. |

HCM-05 is complete: the harness adapter **and** canonical agent-kit integration
are adopted (PR #107 merged; kit pins/vendored snapshot synchronized). Next is
the conditional HCM-06 gating. AG-03A design and research preparation can proceed
independently; keep runtime diffs separate.

## Non-negotiable completion criteria

- Exact assignment coverage, per-screener duplicate rejection and unresolved
  preservation. AG-02 proves its single path, not dual-path parity.
- Human identity comes from protected operator context; payload strings, model
  confidence, role prompts, and critic PASS never confer approval.
- Review binds exact immutable recommendation and final-decision content,
  workspace/run/batch parents and policy. Revision invalidates old approval.
- One immutable buffer supplies parsing and hashing; promotion detects changes.
- Final artifacts and partitions require authorization, not merely a UI button.
  Historical outputs cannot appear current after a failed run.
- Idempotent retries, controlled writers, coherent multi-file generation,
  audit-failure handling and tested crash recovery precede authorized-pilot claims.
- Preserve existing Contract v1 decision meanings. A new record or semantic
  change follows explicit version/architecture review; no generic second envelope.
- Source anchors can be checked mechanically; entailment and scientific quality
  still require review. Authentication never proves that someone read a paper.

## Research pilot

The [UAV crop/weed reliability workspace](../../../workspaces/uav-crop-weed-reliability/README.md)
is initialized with a provisional compiled protocol, not a searched or screened
corpus. Scope: UAV crop/weed mapping, charting spectral degradation, sensor
differences, temporal evaluation, uncertainty, and independent validation units.
These dimensions are not simultaneous inclusion requirements.

Prepare 30–50 deliberately varied development records and independent human
decisions, then a held-out evaluation sample. No sample has been collected yet.
Methodological weakness is charted rather than silently used as exclusion.
An attended research pilot can proceed with procedural review while AG-03 is
unproven; it must not be labeled enforced authorization. Synthetic fixtures are
sufficient for AG-03A and do not require this literature corpus.

## Delivery capsule

Base: `0a701c786b9a610606722a6c44d70fcddd4c58cb`; branch
`cdx/ag-authority-uav-protocol`. Allowed changes: AG planning documents,
Compass/HCM routing, and `workspaces/uav-crop-weed-reliability/` only.
Frozen contracts, toolkit code/pins, agent permissions and unrelated primary
checkout edits remain unchanged. No known baseline failure in this clean branch;
the primary's recorded local drift is not absorbed. Stable sources: Compass,
AG-01 readiness, AG-02 packet, and test-gate policy. Acceptance: consistent current
status, recorded selection, linked next packet, reproducible valid draft protocol,
registered identity, real audit events, and preserved unrelated local work.
Evidence and commands are recorded in the PR and workspace validation report.
Runtime AG-03 work is RELEASE, with independent review and applicable gate mapping.
This documentation/protocol change does not implement it.
