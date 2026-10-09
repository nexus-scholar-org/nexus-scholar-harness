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

## HCM-01 characterization results (executed 2026-10-09, isolated checkout)

New file `tests/unit/test_workspace_audit_characterization.py`: 17 passed.
Directly affected: `tests/inception/test_registered_workspace_id.py` (43) +
`tests/unit/test_audit_log.py` (16) + `tests/console/test_console_screening.py` (9)
= 68 passed. Checkpoint acceptance pair
(`test_audit_failure_rolls_back_publication_and_registry` +
`test_e2_neg_023_injected_log_event_failure_in_the_acceptance_window_publishes_nothing`)
= 2 passed via `-k "audit_failure or injected_log_event_failure"`.
Generators `--check`: baseline 0, schemas 0, fixture 0, pins 0.
`git diff --check` clean; `ruff check scripts/` clean. Full suite once on final
candidate (required for fork publication).

| requirement | existing/new test | observed behavior | unproven limit | proposed HCM-02 caller seam |
|---|---|---|---|---|
| HC1-1 identity mint-once | existing `tests/inception/test_registered_workspace_id.py` (mint shape, distinct, both-creators reuse/mint/refuse table, stable reads, rescaffold, sync/audit preserve) + new `test_hc1_1_mint_then_reread_via_resolver_returns_same_value` | init mints only when no manifest or no recorded field (incl. explicit null); valid `WSP-<32 hex>` reused verbatim by both writers; invalid/corrupt/non-object refused typed; rescaffold reuses; `project_id` stays slug | mint entropy source (`secrets`) not audited; no crash-durability claim for the mint-then-write window | `genesis.recorded_or_minted_workspace_id` + `init_project.recorded_or_minted_workspace_id` -> neutral identity service; keep single typed refusal |
| HC1-2 consumption refusal | existing `test_stage6_refuses_without_a_recorded_identity`, `test_refusal_names_the_slug_it_declined_to_use`, `test_unreadable_manifest_refuses_rather_than_guessing`, `test_missing_project_json_refuses`, `test_stage6_identity_refusal_leaves_no_store_behind` + new `test_hc1_2_consumer_refuses_invalid_recorded_forms[5]`, `test_hc1_2_refusal_leaves_bytes_and_store_untouched`, `test_hc1_2_nonobject_consumer_manifest_crashes_untyped_observed` | consumer `recorded_workspace_id` refuses absent/empty/null/legacy-non-hex/short/non-string/corrupt/slug with `RegisteredWorkspaceIdentityMissingError` before any backend; `project.json`/journal bytes unchanged; no `rag/chroma_db` created; slug never returned | no concurrent-consumer or crash-mid-read claim; non-object array consumer path is untyped `AttributeError` (defect below), not typed | `orchestrator.recorded_workspace_id` + `_run_indexing_stage` identity gate -> neutral service `require_recorded_identity(ws)`; no mint/fallback in consumers |
| HC1-3 manifest merge/dry-run | existing `test_sync_state_preserves_the_recorded_identity`, `test_sync_command_rebuilds_project_state`, `test_sync_command_dry_run_writes_nothing` + new `test_hc1_3_sync_preserves_unrelated_fields_and_merges_stats`, `test_hc1_3_dry_run_writes_nothing`, `test_hc1_3_corrupt_manifest_rebuilds_fresh_observed`, `test_hc1_3_nonobject_manifest_raises_typeerror_observed` | sync keeps `registered_workspace_id`, unrelated fields (`custom_field`, title, paradigm, RQs), and pre-existing custom stats; counted stats overwrite stale values; `updated_at` bumped; `phase` recomputed; dry-run returns `dry_run True`, `index_regenerated False`, writes no files and no `STATE_SYNC` | no atomicity/crash claim for the temp+replace + INDEX + journal triple; malformed paths are OBSERVED-NOT-APPROVED (see defects) | `orchestrator.sync_state` + `_refresh_index_md_atomic` -> neutral manifest-merge + atomic-write service; malformed-manifest policy needs its own decision packet |
| HC1-4 serial journal | existing `test_audit_event_post`, `test_log_event_canonical_schema` (single-append) + new `test_hc1_4_serial_append_preserves_first_line` | two serial `console.api.audit.log_event` appends: first line byte-identical after second; both parse as whole records; `event_id`/`timestamp` minted by writer (`EVT-<14>-<hex6>`, ISO); `action`/`status` uppercased and retained | serial-only: no cross-process locking, fsync durability, or whole-bundle atomicity proven | `console.api.audit.log_event` append + `workspace-manager log_event.log_project_event` append -> neutral `append_event(ws, ...)`; writer owns provenance |
| HC1-5 projections | existing `test_log_event_canonical_schema` (`updated_at`), `test_post_screening_decisions_atomic` (`updated_at`) + new `test_hc1_5_projection_ignores_unknown_stats_and_preserves_identity`, `test_hc1_5_refresher_failure_does_not_block_journal` | journal `metrics` keeps unknown keys; `project.json stats` projection updates only pre-existing keys; `registered_workspace_id` preserved; `updated_at` bumped; raising INDEX refresher does not fail `log_event`/journal append (best-effort) | INDEX content correctness and crash ordering between journal and projection unproven | `console.api.audit.log_event` projection block + `refresh_index_md` best-effort wrapper -> neutral service with authoritative-append vs best-effort-projection split |
| HC1-6 publication failure | existing `test_audit_failure_rolls_back_publication_and_registry`, `test_staging_failure_returns_structured_issue_without_publication`, `test_e2_neg_023_injected_log_event_failure_in_the_acceptance_window_publishes_nothing` + new `test_hc1_6_accept_failure_reports_atomic_and_publishes_nothing` | journal-append failure in the commit window returns single-issue `ATOMIC_COMMIT_FAILED` (OSError text verbatim), `accepted False`, `published_path None`, `event_id None`; no `artifacts/`, no `artifact_registry.json`, no `ARTIFACT_ACCEPTED`; rejection record retained | no crash-between-`os.replace` claim; kit-side pre-candidate window covered by pdf-kit tests, not re-proven here | `contracts/acceptance.accept_artifact` (imports `console.api.audit.log_event` at `acceptance.py:16`, calls at `:196`/`:538`) -> neutral audit sink injection; keep fault at writer seam |
| HC1-7 portability | existing `test_log_event_resolves_workspace_by_slug`, `test_log_event_refuses_non_workspace_dir`, `test_log_event_uses_wheel_bundled_log_module`, `test_skills_source_resolution_env_override`, `test_log_sync_index_refreshes_without_appending` + new `test_hc1_7_portable_loader_prefers_env_override` | path-with-`project.json` resolves; `workspaces/<slug>` CWD-relative fallback; plain-dir/missing refused without creating a ledger; `NEXUS_SKILLS_SRC` override and wheel bundle both load `log_project_event`; `sync-index` refreshes INDEX without appending | untested: concurrency, crash-durability, and any non-local skill source; source inspection is not proof | every caller HCM-02 must move: `orchestrator._log_audit_event` + `_refresh_index_md_atomic` + `_run_indexing_stage` audit lines, `console.api.audit.log_event`/`refresh_index_md`/`_load_index_refresher`, `audit_log._resolve_log_module`/`_resolve_workspace`/`run_log_event`/`run_log_batch`/`run_sync_index`, `genesis._log_project_event`/`_load_log_module`/`resolve_skills_root`/`resolve_workspace_manager_scripts`, `contracts/acceptance.log_event` import |

Unexpected defects (recorded, not fixed in this test-only packet): (1) consumer
`recorded_workspace_id` on a valid-JSON non-object manifest raises untyped
`AttributeError` (`manifest.get`), not the typed refusal. (2) `sync_state` on a
valid-JSON non-object manifest raises untyped `TypeError` at
`manifest["updated_at"] = ...`. (3) `sync_state` on corrupt JSON silently
rebuilds a fresh default manifest (`project_id == ws.name`, no
`registered_workspace_id`) and logs `STATE_SYNC SUCCESS`, discarding the corrupt
recorded identity. HCM-02 must not silently adopt any of these as policy.
