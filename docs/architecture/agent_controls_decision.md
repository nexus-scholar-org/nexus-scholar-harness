# AG architecture decision — authorized screening after HCM

**Date:** 2026-10-10
**Status (2026-10-12):** Researcher approved the protected local publisher with restricted scientific worker. AG-02 integrity is merged. AG-03A deployment feasibility is next; enforced authorization is not yet implemented or proven.
**Owner:** Nexus Scholar Harness
**Execution plan:** [Post-HCM agent-control plan](agent_controls_plan.md)

**Current assessment:** [Post-AG-02 reassessment](agent_layer_reassessment_2026-10-12.md).
AG-01 readiness and AG-02 have advanced since this original decision. Preserve
the decisions below as target invariants; do not interpret them as all implemented.
The researcher subsequently selected this model in this chat on 2026-10-12.
[AG-03A](ag-03a-protected-publisher-feasibility.md) records that approval and
the remaining feasibility gate. Approval of the direction is not proof of isolation.

## Context and evidence

[AG-00](agent_control_enforcement_map.md) inspected commit `1c4255e` and
identified strong technical acceptance/parent controls but no separate
authorization boundary in the inspected screening collection path. It also
identified unresolved-to-excluded coercion, incomplete coverage, duplicate
overwrite, and declared-only critic controls. Those are code-inspection
findings, not executed behavioral proofs. Refresh affected paths after HCM.

The user requested that this architecture be recorded and scheduled next after
HCM. The decision preserves Contract v1 and toolkit ownership. It supersedes
AG-00 section 6 as the forward plan; AG-00 remains unchanged as historical
assessment evidence. In particular, this decision does not adopt that section's
suggestion to call existing accepted screening decisions recommendations.

## Decision

Build one human-reviewed screening workflow using the existing harness. Keep
technical validity, scientific review, authorization, and publication distinct.
Do not introduce a generic agent framework or a second generic artifact envelope.

```text
Accepted batch and exact protocol/corpus parents
    -> immutable recommendation snapshot (non-authoritative)
    -> technical checks and scientific review
    -> explicit human final decisions and authorization
    -> existing Contract v1 acceptance for final decision artifacts
    -> controlled publication generation and downstream consumption
```

1. **Preserve existing semantics.** An accepted `screening_decisions` artifact
   must not be relabeled a recommendation to avoid an architecture/version
   decision. New recommendation and authorization records are provisionally
   harness-owned, versioned sidecars linked by hashes. Their schemas, lifecycle,
   storage, and linkage remain to be ratified in AG-03B after the AG-01 readiness assessment. No contract
   change is presumed necessary or ruled out; any required change follows the
   frozen baseline evolution procedure.
2. **Authority comes from policy, not model output.** In the pilot, every final
   inclusion/exclusion requires explicit human authorization. Consensus and a
   critic PASS do not substitute for it. A candidate's self-reported role,
   reviewer string, confidence, or `requires_human_review` flag grants no rights.
3. **Bind authorization to exact reviewed content.** Preserve the original
   recommendation bytes/checklists; create a separate final decision record
   for overrides. Authorization binds workspace, batch, protocol/corpus,
   recommendation and final-decision hashes, actor, policy version, and actual
   time. Changing reviewed content invalidates authorization. Missing metadata
   stays explicitly unavailable; legacy epoch timestamps and `agent-unknown`
   must never count as authenticated human approval.
4. **State the trust boundary honestly.** The initial design targets a trusted
   local researcher and bounded agent interface, not protection against an
   administrator with arbitrary filesystem access. The approval action must
   obtain actor identity from a harness-controlled operator context. Agent
   interfaces cannot mint approvals or directly publish. AG-03A must demonstrate
   how that separation is enforced; a freely writable JSON file plus a hash
   is insufficient. If the host grants the agent unrestricted equivalent
   authority, report the isolation limit and do not claim enforced separation.
5. **Resolve deterministic integrity defects first.** Require exact assignment
   coverage, reject duplicate entries per study and assigned screener, and
   preserve valid dual-screening parent records. Preserve MAYBE/CONFLICT as
   unresolved; never coerce them to EXCLUDE. Partial review may be saved as a
   draft, but cannot finalize the batch or publish terminal partitions.
6. **Gate all authoritative consumption.** Put the check in shared harness
   services used by file, CLI, console, and orchestration paths, not just UI.
   Authorization precedes acceptance of new final decisions and publication.
   Existing partitions and reports need an explicit generation/currentness
   check at downstream consumption. Retain historical outputs, but never
   let a failed new run make old files appear authorized for the current run.
7. **Publish coherently.** Revalidate hashes at promotion; use a bounded
   single-writer/atomic-generation design to prevent approval/write races.
   Identical retries are idempotent. Changed content requires new review.
   Audit failure must not leave consumable final output without its required
   authorization/provenance. Recovery behavior is part of the tested design.
8. **Do not manufacture scientific certainty.** Source existence and quotation
   matching are deterministic checks; entailment remains scientific review.
   Uncertainty vocabulary follows the protocol. Model confidence is optional,
   uncalibrated metadata. Source text is untrusted input, never instructions.
9. **Preserve legacy evidence without blessing it.** Existing unauthorised
   generations remain legacy/unverified. Explicit review can produce a new
   authorized generation; no retroactive actor, timestamp, or approval is
   fabricated. No automatic migration is included.

## Consequences and rejected alternatives

- Reuse the contract gate, identities, audit service, and scientific role skills.
  Harness-only ownership is the initial target, not a guaranteed conclusion.
  If shared kit behavior must change, split the canonical-kit work and perform
  full-SHA pin/vendor synchronization.
- Reject a UI-only approval checkbox: file/CLI paths could bypass it.
- Reject final-output-only gating: earlier accepted decision artifacts and
  stale partition files could remain consumable as authoritative state.
- Reject an LLM critic as scientific approver and blanket claims of agent
  independence. A mandatory critic runtime gate is deferred; human review is
  mandatory for this pilot, and required dual-review independence must still
  be preserved and evaluated.
- No synthesis, extraction, scheduler, model-routing platform, broad UI work,
  new kit, or unrestricted autonomous scientific publication in this phase.

## Status boundary

The local baseline failure recorded by AG-00 is not repaired by this decision.
Implementation requires a verified clean baseline in the chosen checkout, or
an explicitly reviewed baseline evolution. Preserve the user's local edits;
do not revert them or regenerate the baseline merely to unlock this plan.
Documentation records future policy; it does not change frozen runtime semantics.
