# Agent layer reassessment after AG-02

> Historical assessment before the researcher's subsequent approval on the same
> date. The protected publisher/restricted worker is now selected; its enforcement
> remains unproven. Use [AG-03A](../ag-03a-protected-publisher-feasibility.md) and the
> [current plan](../agent_controls_plan.md) for status and next actions. Unselected-model
> and primary-untracked statements below describe the assessment-time state.

**Date:** 2026-10-12
**Lane:** FAST, documentation and source inspection only.
**Verdict:** AG-02 is merged workflow-integrity progress, not human authorization.
AG-03 remains `BLOCKED_AUTHORITY_MODEL`. Recommend a bounded authority feasibility
packet before authorization implementation; pilot protocol preparation can proceed.

## Context capsule and evidence

```yaml
task: AG-post-106-reassessment
delivery_lane: FAST
owner_repo: nexus-scholar-org/nexus-scholar-harness
base_sha: 0a701c786b9a610606722a6c44d70fcddd4c58cb
head_sha: 070b448 (primary checkout; not updated)
allowed_paths:
  - docs/architecture/agent-controls/archive/agent_layer_reassessment_2026-10-12.md
  - docs/architecture/agent-controls/agent_controls_plan.md
  - docs/architecture/agent-controls/agent_controls_decision.md
immutable_boundaries: [contracts, baseline, tools, primary-Git-state, other-local-edits]
acceptance_ids: [AG-STATUS-REFRESH, AG-AUTHORITY-PROPOSAL, AG-NEXT-PACKETS]
open_findings: [authority-model-unselected, plan-not-canonical, runtime-limits-below]
known_baseline_failures: [primary-local-reviewer-drift-carried-not-repaired]
evidence:
  - command: gh pr view 106 --repo nexus-scholar-org/nexus-scholar-harness --json state,mergedAt,mergeCommit,statusCheckRollup,url
    commit: 0a701c786b9a610606722a6c44d70fcddd4c58cb
    result: MERGED; nine PR checks SUCCESS; merged 2026-10-12T07:32:43Z
  - command: git show 0a701c7:<AG-01 ADR, AG-02 packet, collector, integrity, tests>
    commit: 0a701c786b9a610606722a6c44d70fcddd4c58cb
    result: source inspected; no runtime test executed this turn
  - command: git status -sb; git log -3 --oneline
    commit: 070b448
    result: main behind origin/main by eight commits; 14 pre-existing dirty/untracked paths
next_gate: docs validation; authority decision then bounded feasibility proof
stable_sources:
  - docs/architecture/agent-controls/archive/ag-01-authorization-readiness.md@0a701c7
  - docs/architecture/agent-controls/archive/ag-02-screening-decision-integrity-packet.md@0a701c7
  - docs/architecture/harness-core-modularity/hcm_05_mcp_recon_adapter_characterization.md@0a701c7
  - docs/architecture/test_gate_policy.md@070b448
```

The merged AG-01 evidence ledger records `1175 passed, 6 skipped, 0 failed`
for candidate `cf959bb2dfa2b25feb7eacfc5b0df14d7d63249c`. This is recorded
local release evidence, not a suite rerun here. The nine checks above are PR
checks, not a claim that a separate merge-commit CI run was inspected.

Immutable source links: [PR #106](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/106),
[AG-01 ADR](https://github.com/nexus-scholar-org/nexus-scholar-harness/blob/0a701c786b9a610606722a6c44d70fcddd4c58cb/docs/architecture/agent-controls/archive/ag-01-authorization-readiness.md),
[AG-02 packet](https://github.com/nexus-scholar-org/nexus-scholar-harness/blob/0a701c786b9a610606722a6c44d70fcddd4c58cb/docs/architecture/agent-controls/archive/ag-02-screening-decision-integrity-packet.md).
Use these until the primary checkout is deliberately integrated; the new
upstream files do not yet exist in this checkout.

## What changed in the assessment

| Layer | Current conclusion | Remaining boundary |
|---|---|---|
| HCM coordination | HCM-05 harness adapter merged in #105 | Inspected HCM-05 record says adapter available but unwired; canonical agent-kit adoption and sync are unit 2. Do not infer later work absent or complete from this record. |
| Scientific artifacts | Existing identity/parent/acceptance mechanisms reused | Technical acceptance is not scientific approval. |
| AG-01 | Readiness design and executable characterizations delivered | Authority selection was deliberately left blocked; do not repeat AG-01 wholesale. |
| AG-02 | Single-screener exact coverage, duplicates, unresolved refusal, parent freshness and decision-file hash checks merged | Dual path unchanged; no blanket per-screener parity claim. |
| Role skills and critics | Operating procedures and lineage expectations exist | Critic PASS, prompt role, and reviewer strings do not grant authority or prove independence. |
| Scientific review | Can be conducted by researchers now | Source anchoring, criterion interpretation, and decision quality require separate evidence. |
| Execution/authorization | No trusted approver boundary established | AG-03 remains blocked; current unrestricted same-user agents cannot be distinguished by writable metadata. |
| Pilot | UAV crop/weed reliability review remains a candidate from this conversation | Protocol and independent human reference decisions can be prepared without claiming an authorized AG workflow. |

AG-02 does not need to be reopened just because its declared scope excluded
authorization. Preserve the merged gate and historical characterization results.

## Remaining engineering limits to carry explicitly

These are scoped source observations and future test requirements, not reproduced
exploits or newly failing tests:

1. **Single/dual distinction.** New gates sit in the single-screener branch.
   Decide whether the first pilot supports only that path. If dual collection
   is offered, prove coverage/duplicate/unresolved/content parity in a separate
   bounded packet while preserving unanimity/adjudication lineage.
2. **Same-byte snapshot.** At the inspected commit, `collector.py:694` parses
   through `_load_decision_payload`, while `:729` separately calls `read_bytes`
   for the hash. A writer between those reads could separate parsed content
   from recorded hash. Before approval binding, parse and hash one immutable
   buffer and test mutation between validation and promotion. Concurrent-write
   safety was excluded from AG-02; serial exact-byte tests do not establish it.
3. **Prior output is not current output.** AG-02 preserves old partitions on
   refusal. Downstream generation/currentness enforcement must prevent those
   historical files from being mistaken for output of the failed current run.
4. **Multi-file publication.** Partition/report writes remain sequential at
   `collector.py:1123` onward. Atomic accepted artifacts do not prove an atomic
   report generation. AG-03 needs an explicit promotion/recovery boundary.
5. **Revision after review.** `CONTENT_CHANGED` correctly blocks substitution
   under the same acceptance. Add a deliberate new review revision/supersession
   flow; never teach operators to delete registry entries to make an override pass.
6. **Draft UI capability.** The inspected console API still accepts only
   INCLUDE/EXCLUDE. File-based unresolved support is not evidence that the UI
   can save an uncertain review state. Add that only in the relevant interface packet.

Source: [collector at reviewed commit](https://github.com/nexus-scholar-org/nexus-scholar-harness/blob/0a701c786b9a610606722a6c44d70fcddd4c58cb/src/scholar_harness/screening/collector.py).

## Authority recommendation — proposed, not selected

**Recommend a protected local publisher with a restricted agent worker** for
the first enforceable pilot. Prove feasibility before building a review UI.

- Worker receives read-only assigned evidence and an output inbox. It cannot
  write accepted artifacts, registry, policy/trust configuration, audit state,
  publisher code, or final partitions, and cannot invoke approval credentials.
- Publisher owns authoritative state under a separate protected execution
  identity/boundary. Researcher reviews exact immutable content and approves
  through its operator interface. Actor comes from verified operator context,
  never candidate metadata. UI automation and session/token access are included
  in the worker threat model, not assumed impossible because a page is local.
- Publication binds workspace, run, batch and exact parent hashes, recommendation
  revision, final decision content, review policy version, and actual approver.
  All supported consumers require its current publication generation.
- A bounded local deployment may use OS-account isolation; an isolated worker
  service/container is another implementation option only if its mounts,
  credentials, host interfaces, and permissions actually enforce the same rule.
  Choice is a feasibility outcome, not an unsupported guarantee about this host.

This changes the execution model: it is not achievable by adding a JSON file or
checkbox while leaving the scientific worker unrestricted under the publisher's
OS identity. Do not conflate a trusted development agent editing application
code with the restricted scientific worker operating the released workflow.

Alternative if a worker boundary is impractical: external approval service or
externally held signing key with protected verification trust configuration and
downstream enforcement. A signature alone does not prevent a privileged worker
from bypassing the verifier or altering its trust root. No bespoke PKI is needed
for the first decision. Hardware/session credentials also require a demonstrated
operator interaction and agent-access limits; their presence is not proof that
a human read the evidence.

An attended manual run remains usable for formative research meanwhile. Label
it **operator-attended, procedurally reviewed**, not enforced authorization.
Scientific quality and actual human attention are never guaranteed by authentication.

## Revised next sequence

| Packet / track | Outcome before advancing |
|---|---|
| Documentation reconciliation | Integrate the primary Compass hunk with upstream deliberately; publish the local AG roadmap/decision through the fork/PR route. Preserve AG-00 history. Do not stash/reset blindly or call untracked files canonical. |
| HCM-05 close-out (separate track) | Finish or explicitly defer canonical-kit unit 2, dependency/wheel boundary, full-SHA pin/vendor/metapackage sync and applicable gates; record HCM closure/conditional HCM-06 disposition. |
| AG-03A: authority ADR + feasibility | Researcher selects authority model; one synthetic batch demonstrates worker cannot approve or overwrite final state, real operator can approve exact content, and bypass attempts refuse. Record supported host and unsupported assumptions. RELEASE for executable permissions/publication changes. |
| AG-03B: snapshot and review lifecycle | Same-buffer parse/hash, immutable recommendations, preserved overrides, explicit supersession, review policy and source references. Single-screener scope first unless dual parity is separately proven. |
| AG-03C: publication and consumption | Shared approval gate before final acceptance; coherent output generation; stale/replayed/changed-content refusal; crash/audit/retry/race tests; all consumers reject unauthorized or obsolete generations. |
| AG-04: one bounded worker and review interaction | One screening skill/adapter with model/skill provenance and draft uncertainty; optional critic advisory output; every final decision approved through the proven boundary. No generic scheduler or model-routing platform. |
| AG-05: scientific and workflow evaluation | Independent reference review, held-out sample after calibration, missed eligible studies and evidence errors, correction time and bias; separate deterministic tests from scientific evaluation. |

AG-03A design and pilot protocol preparation need not wait idly for unrelated
HCM work. Keep implementation packets separate and rebase/refresh their exact
owner paths after HCM changes. Do not make HCM-06 UI completion a hidden
requirement for a CLI/service authority feasibility proof.

For the UAV pilot, prepare eligibility rules and a deliberately varied 30–50
record development set, then an untouched evaluation set. Screening quality
remains measured independently of software integrity. Do not require literature
collection or model experiments merely to test an approval boundary: synthetic
fixtures suffice for AG-03A. No workspace or literature run is created here.

## Documentation issues to reconcile before AG-03

- Local plan says no runtime work started and AG-01 is next; both are now stale.
- Canonical AG-01 contains historical observations and packet-era status text;
  retain dated evidence but add current summaries in a scoped docs PR.
- Canonical AG-02 packet still has a placeholder head SHA/status. Link the merge
  and evidence ledger rather than manufacturing new validation results.
- Some AG-01 prose calls technically accepted decisions recommendations. State
  that **human authorization is not attested** without silently redefining the
  frozen `screening_decisions` type. Adopt any schema/semantic change explicitly.
- The earlier generic AG-C01/C02/C06/C07 goals are not all closed by AG-02:
  single-path integrity and serial retry evidence do not close dual parity,
  stale-consumer safety, or concurrent/atomic publication obligations.

## Verification scope

No code, permissions, contracts, pins, real workspace data, branch state, or
existing Compass hunk changed. No pull, reset, stash, commit, push, merge, full
suite, or baseline regeneration was performed. Baseline-green evidence is the
recorded clean AG-02 candidate evidence, not a certification of this dirty primary
checkout. Document links/whitespace and scoped self-review are the delivery gate.
