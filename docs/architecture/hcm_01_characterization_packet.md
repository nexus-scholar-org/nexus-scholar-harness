# HCM-01 — workspace and audit characterization

**State:** PREPARED; characterization implementation not yet completed.
**Lane:** FAST, test/documentation-only. No behavior-moving refactor.
**Owner:** nexus-scholar-org/nexus-scholar-harness.
**Execution base:** PR #79 merged as `83c54814efdf0956fb0a9dc8dcfb051f0d1a65fd`.
Its tree matches reviewed head `d1ddffd1b38db38e6fc6332a2d72d7b94c6cd5ac`.
WP-01/E4's qualified closure remains qualified; this packet does not waive
the remaining research-validation limits.

## Goal and stop rule

Describe and pin the current workspace/identity/audit behavior before HCM-02
moves those responsibilities into a neutral internal service. Stop after one
characterization PR. Do not implement HCM-02, move modules, flatten kits,
reorganize recon, or change interfaces in this packet.

## Compact context capsule

```yaml
task: HCM-01
delivery_lane: FAST
owner_repo: nexus-scholar-org/nexus-scholar-harness
base_sha: 83c54814efdf0956fb0a9dc8dcfb051f0d1a65fd
head_sha: preparation-only
allowed_paths:
  - tests/unit/test_workspace_audit_characterization.py
  - docs/architecture/hcm_01_characterization_packet.md
immutable_boundaries:
  - all production source and workspace-manager scripts
  - Contract v1, generated schemas/fixtures/baseline
  - toolkit source, vendor snapshots, pins and dependencies
  - UI and operator-owned working-tree edits
acceptance_ids: [HC1-1, HC1-2, HC1-3, HC1-4, HC1-5, HC1-6, HC1-7]
open_findings: []
known_baseline_failures: []
evidence:
  - PR79 head full suite 795 passed / 6 platform skips; CI 9/9 SUCCESS
next_gate: inner
stable_sources:
  - docs/architecture/harness_core_modularity_roadmap.md sections 3-6
  - docs/architecture/DEVELOPER_COMPASS.md sections 3, 5, 7-9
  - docs/architecture/test_gate_policy.md delivery lanes and evidence reuse
  - .agents/skills/workspace-manager/SKILL.md event and workspace conventions
```

PR #79 is merged; verify its recorded merge SHA and ancestry. Verify a clean
isolated checkout, four generator checks, and import resolution before tests.
Do not run against the user's dirty working tree. Use the capsule and assigned
source functions in later rounds, not the full E3/E4 transcript.

## Verified routing inventory

| Boundary | Current source | Existing test entrypoint |
|---|---|---|
| Identity mint/read policy | `src/scholar_harness/inception/genesis.py`: mint_registered_workspace_id, validate_registered_workspace_id, recorded_or_minted_workspace_id | `tests/inception/test_registered_workspace_id.py` |
| Consumer identity refusal | `src/scholar_harness/orchestrator.py`: recorded_workspace_id | same identity test file |
| Manifest merge and dry run | `src/scholar_harness/orchestrator.py`: sync_state | inspect existing sync coverage before adding duplicates |
| Console journal and projections | `src/scholar_harness/console/api/audit.py`: log_event, refresh_index_md | `tests/console/test_console_screening.py`, audit-event tests |
| Portable audit adapter | `src/scholar_harness/audit_log.py` | `tests/unit/test_audit_log.py` |
| Script-backed journal/index | `.agents/skills/workspace-manager/scripts/log_event.py` | portable audit tests and console tests |
| Acceptance audit coupling | contracts/acceptance.py and index_acceptance.py import console.api.audit | existing conformance and extraction-runtime acceptance tests |

Resolve these symbols in the actual base; do not invent a missing workspace.py
service. HCM-02 introduces that neutral boundary later.

## Migration/refusal decision

No automatic identity migration is authorized during consumption, sync, module
movement, or rerun. Consumers inherit the recorded identity or refuse; they
never derive one from the human slug.

Record the current initialization exception honestly: existing initialization
code mints when the manifest is absent or lacks the identity, preserves a valid
recorded identity, and refuses malformed/corrupt recorded state. This observed
behavior is not permission to extend migration to consumers. HCM-02 must not
silently tighten or broaden initialization semantics. Any stricter legacy-init
policy requires its own explicit behavior decision and regression packet.

## Acceptance and negative cases

1. **HC1-1 — identity:** reuse existing parity tests for both initialization
   paths; cover valid identity preservation, invalid identity, corrupt JSON,
   non-object manifest, absent field, and repeated explicit initialization.
2. **HC1-2 — consumption:** missing/invalid recorded identity refuses before
   backend creation; project/journal bytes remain unchanged; slug is never an ID.
3. **HC1-3 — manifest:** characterize sync's preservation of recorded identity,
   unrelated manifest fields, and existing stats. Dry-run must not write files
   or events. Record malformed-manifest behavior as observed, not as a newly
   approved repair policy.
4. **HC1-4 — serial journal:** append two real events; the first line remains
   byte-identical, both parse as whole records, provenance is generated by the
   writer, and canonical status/action values are retained. Do not claim
   cross-process locking, fsync durability, or whole-bundle atomicity from this.
5. **HC1-5 — projections:** characterize updated_at, existing-stat updates,
   unknown-stat handling, identity preservation, and INDEX refresh behavior.
   Distinguish authoritative journal writes from best-effort projection refresh.
6. **HC1-6 — publication failure:** reuse or add a focused accepted-parent
   case with journal append failure; prove no new accepted record/registry
   entry or success event survives. Assert the actual structured refusal,
   rather than merely catching Exception. Keep fault injection at the writer
   seam; do not patch acceptance to return success.
7. **HC1-7 — portability:** retain path/slug and wheel-bundled skill-loader
   coverage, and document every caller that HCM-02 must move. Mark untested
   concurrency and crash behavior explicitly; source inspection is not proof.

Prefer existing load-bearing tests. Add only uncovered cases in the one
allowed test file; each new case names its HC1 ID. Real fixtures live under
tmp_path, not workspaces/. Freeze volatile clock/ID seams only where needed;
do not assert a hand-invented production identity.

## Gates and review cadence

Inner: the new file, then only the directly affected existing test functions.
Checkpoint: registered-workspace, portable-audit, console-audit, and the existing
acceptance journal-failure selections. Record exact commands/counts at the base.
Run scripts lint, diff check, and all four generator --check commands.

Use the selector to determine any additional required fallback for new paths.
If it selects a full suite, run it once on the final candidate, not each edit.
Fork publication still requires the contribution gate's full-suite pass.
One scoped review; repair-delta verification only. Independent agents are not
required unless explicitly dispatched. New unrelated nits become follow-ups.

## Deliverable and HCM-02 gate

Publish the tests and a compact result table in this packet: requirement,
existing/new test, observation, unproven limit, and proposed HCM-02 caller seam.
No “characterized” claim without executed evidence. Unexpected defects are
recorded and routed separately, not fixed through test-only scope.

HCM-02 begins only after this characterization PR merges and its observations
are reconciled. Its first bounded extraction is the neutral audit service;
pipeline stages and MCP recon remain subsequent independent units.
