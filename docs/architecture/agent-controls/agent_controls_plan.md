# Agent controls: current execution plan

**Updated:** 2026-10-12. **Lane for this planning/protocol PR:** FAST.
**Decision:** [Approved architecture](agent_controls_decision.md).
**Next:** [AG-03A protected-publisher feasibility](ag-03a-protected-publisher-feasibility.md).

## Current status and provenance

AG-01 readiness and AG-02 integrity are delivered in merged [PR #106](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/106),
merge `0a701c786b9a610606722a6c44d70fcddd4c58cb`. Nine PR checks passed.
The AG-01 evidence ledger records 1175 passed, 6 skipped, zero failed at its
final candidate. These are dated release records, not a suite rerun claim.
[AG-00](archive/agent_control_enforcement_map.md) and the [post-AG-02 reassessment](archive/agent_layer_reassessment_2026-10-12.md)
remain historical evidence. This current plan supersedes their next-action text.

The researcher approved the protected local publisher/restricted scientific
worker on 2026-10-12 and authorized initializing the UAV protocol. No runtime
authority mechanism has been proven. The remaining block is
`BLOCKED_AUTHORITY_ENFORCEMENT`, not an unselected architecture direction.

## Ordered work

| Packet | Status | Exit condition |
|---|---|---|
| AG-00 | Assessment retained | Historical code-inspection map preserved. |
| AG-01 | Readiness delivered | Its unresolved host authority question now routes to AG-03A. |
| AG-02 | Merged, bounded integrity | Single-screener coverage/duplicates/unresolved/hash/freshness gates; no authority claim. |
| AG-03A | NEXT; model approved, feasibility unproven | Real deployment proves restricted worker cannot approve, impersonate operator, modify publisher, or overwrite final state. |
| AG-03B | Queued | Same-buffer parse/hash, immutable recommendations, evidence references, reviewer overrides and explicit supersession. |
| AG-03C | Queued | Shared authorization gate before final acceptance, coherent publication generations, downstream currentness and crash/audit/race/retry proofs. |
| AG-04 | Queued | One screening worker and minimal review interaction using the proven publisher. |
| AG-05 | Queued | Held-out scientific evaluation after calibration; measured error/correction/time/bias and proceed/revise/stop decision. |
| AG-06/07 | Deferred | Charting then synthesis require separate evidence-based decisions. |

HCM-05 remains a separate close-out track. Its inspected unit-1 record says the
harness adapter is complete while canonical-kit consumption is pending. Refresh
that status at handoff rather than overriding another active task. Finish or
explicitly defer the kit unit, pins/vendor sync, packaging gates, and conditional
HCM-06. AG-03A design and research preparation can proceed independently; keep
runtime diffs separate and refresh owner paths after HCM integration.

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
