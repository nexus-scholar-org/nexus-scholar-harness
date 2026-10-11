# AG-02 Packet — Screening Decision Integrity (bounded, no authorization claims)

```yaml
task: AG-02-screening-decision-integrity
delivery_lane: RELEASE
owner_repo: nexus-scholar-org/nexus-scholar-harness
base_sha: d07100f39a94a750bbc858da4cb8638543486762
head_sha: <recorded-at-AG-02-implementation>
branch: cdx/ag-02-screening-decision-integrity
allowed_paths:
  - src/scholar_harness/screening/collector.py (single-path gates only; dual path untouched)
  - src/scholar_harness/screening/integrity.py (new; pure gate functions + typed refusal codes)
  - src/scholar_harness/console/api/screening.py (only if draft/finalize labeling needs it; no new auth)
  - tests/test_screening_decision_integrity.py (new)
  - docs/architecture/ag-01-authorization-readiness.md (capsule evidence update only)
immutable_boundaries:
  - docs/architecture/contract_v1_baseline.json (never regenerate to bless drift)
  - src/scholar_harness/contracts/** (frozen ContractDecision/ScreeningDecisionsData unchanged)
  - tools/** (no kit change; no pin change)
  - Dual-path unanimity-or-adjudication semantics (collector.py:360-426, byte-for-behavior)
  - workspaces/** real workspaces (tmp_path fixtures only)
  - .opencode/agent/** (no permission changes)
acceptance_ids: [AG-C01, AG-C02, AG-C04hash, AG-C05, AG-C06, AG-C07retry,
  AG-C08dual, AG-C03guard, AG-C10guard]
open_findings: [AG-03-authorization-identity-source-unresolved (carried, not solved here)]
known_baseline_failures: []
evidence: []
next_gate: inner
stable_sources:
  - docs/architecture/ag-01-authorization-readiness.md@d07100f+ (§§2-5, row-level evidence)
  - src/scholar_harness/screening/collector.py@d07100f (single path :540-796)
  - src/scholar_harness/screening/batcher.py@d07100f (:165-183 provenance fallbacks)
  - src/scholar_harness/console/api/screening.py@d07100f (:88-141 writer)
  - docs/architecture/agent_context_protocol.md@d07100f
```

**Status:** implementation packet. Parent: AG-01 readiness
(`ag-01-authorization-readiness.md`, verdict `BLOCKED_AUTHORITY_MODEL` for
authorization). This packet implements **workflow-integrity only**.

## 1. Objective (one paragraph)

Make `cmd_collect` refuse loudly — with typed codes, journal rows, and no
partition outputs — when a single-screener decision file is incomplete
(missing candidates), duplicated (same study twice per screener),
unresolved (MAYBE/CONFLICT presented for finalization), content-changed
since its last acceptance, or bound to a superseded batch; and record the
exact decision-file sha256 in the accepted artifact lineage so substitution
is detectable. Nothing in this packet identifies, authenticates, or
authorizes any human or agent.

## 2. Non-claims (normative; a reviewer must fail the PR if any is violated)

1. No new concept of approver, approval, authority, or operator identity is
   introduced. No field is named `approved*`, `authorized*`, or
   `approved_by`.
2. `method: HUMAN`, human-like `reviewed_by` strings, confidence scores,
   and critic verdicts confer nothing. A dedicated guard test
   (`test_human_labeled_but_unapproved_file_is_not_privileged`, AG-C03guard)
   asserts a `method: HUMAN` file is treated byte-identically to a
   `method: LLM` file.
3. The PR body and docs state "workflow-integrity (tamper-evidence +
   fail-closed), not authorization" verbatim. Any sentence claiming the
   gate distinguishes agent bytes from human bytes is a defect.
4. Publication semantics are unchanged in the authorized dimension:
   integrity-valid recommendations still publish exactly as today; AG-03
   alone may gate publication on approval.

## 3. Mechanism (exact)

### 3.1 New pure module `src/scholar_harness/screening/integrity.py`

Pure functions of `(accepted parent batch candidates, submitted decision
file bytes + parsed entries, registry head)` — no filesystem writes, no
clock reads, no network:

- `decision_file_sha256(raw_bytes: bytes) -> str` (sha256 hex; canonical
  `hashlib`, no new dependency).
- `check_exact_coverage(candidate_ids: set[str], entries: list[dict]) ->
  None` — raises on missing ids, extra ids (extra stays fail-closed as
  today), and duplicate study ids **per screener** (two distinct assigned
  screeners are not duplicates; single path has one screener by
  construction).
- `check_no_unresolved_for_finalize(entries) -> None` — raises if any entry
  carries MAYBE/CONFLICT (legacy string or checklist-derived), because
  finalization with unresolved rows is what today silently coerces.
- `bind_batch(batch_index, registry_head_batch_artifact)
  -> (artifact_id, sha256)` — the freshness anchor: run id + parent batch
  artifact id + sha the decision file is collected against.
- Typed refusal `ScreeningIntegrityRefused(code, detail, ...)` mirroring
  the `VerificationIdentityRefused` shape, with codes:
  `COVERAGE_INCOMPLETE`, `DUPLICATE_ENTRY`, `UNRESOLVED_FINALIZE_REFUSED`,
  `CONTENT_CHANGED`, `STALE_BINDING`.

### 3.2 Collector wiring (single path only, `collector.py:540-796`)

1. After `_load_decision_payload` and parent-batch resolution, run
   `check_exact_coverage` + `check_no_unresolved_for_finalize` **before**
   any `ContractDecision` is minted or state is touched (same position as
   the existing Packet-D membership gate `:580-611`). On failure: rename
   file to `.rejected`, mark batch `MISSING`, raise `RuntimeError` via the
   existing fail-closed tail (`:787-796`) — no new publication paths.
2. Compute `decision_file_sha256` of the raw file bytes. Look up any
   existing accepted `screening_decisions` artifact for this batch in the
   registry: identical recorded hash ⇒ idempotent accept (no duplicate
   artifact, AG-C07retry); different bytes ⇒ raise
   `ScreeningIntegrityRefused(CONTENT_CHANGED, old_hash, new_hash)` —
   changed content never silently re-publishes as the same acceptance.
3. Record the decision-file hash in lineage: add to the accepted envelope's
   `inputs` list (verifying `accept_artifact`'s inputs-entry schema first —
   if the schema admits only artifact references, record instead in the
   batch `MANIFEST.json` row **and** the acceptance journal parameters;
   the packet requires hash-in-lineage + hash-in-journal, field choice
   follows the schema, never a schema weakening to fit).
4. `STALE_BINDING`: the batch artifact id+sha resolved at collect time is
   the binding; a decision file collected after its batch was superseded
   (registry head for that index differs) refuses instead of attaching to
   the old acceptance. Deterministic-ids make identical-input re-prepare
   idempotent (existing behavior, regression-tested).
5. Remove the silent coercion (`collector.py:639`): non-INCLUDE legacy
   values no longer become EXCLUDE — they are either MAYBE/CONFLICT
   (refused by `check_no_unresolved_for_finalize`) or invalid (rejected as
   today). Partition's non-INCLUDE→excluded branch then only ever sees
   explicit EXCLUDE.
6. Dual path (`:199-538`): **untouched** except reusing the
   `decision_file_sha256` recording if it fits without semantic change;
   any dual behavior delta is out of scope (AG-C08dual is regression-only).

### 3.3 Console writer (`console/api/screening.py`)

Default: **no change**. The console remains draft-capable: partial,
duplicate-containing, or unresolved drafts may be *saved* (they are
working state, visibly incomplete), but `collect` — the finalize gate —
refuses them. If draft/finalize labeling needs a flag, it is display-only
metadata, never an authority claim. Membership checks stay exactly as they
are (`:105-130`).

### 3.4 Draft vs finalize (decision-doc item 5, made mechanical)

- Draft: any saved `batch_NNN_decisions.json` (partial coverage allowed,
  unresolved allowed). Never published from.
- Finalize: `cmd_collect` succeeds only on exact coverage, zero
  duplicates, zero unresolved rows, fresh binding, and hash-consistent
  bytes. Anything else ⇒ typed refusal + no `included.json`/`excluded.json`
  writes + prior outputs untouched.

## 4. Test map (new file `tests/test_screening_decision_integrity.py`)

All fixtures reuse the `test_screening_migration.py::_workspace` pattern on
`tmp_path` with a 2-study corpus variant. Each test asserts refusal shape
**and** absence of publication side effects.

| Test | AG-ID | Asserts |
|---|---|---|
| `test_incomplete_coverage_refuses_without_publication` | AG-C01 | 1-of-2 file ⇒ `RuntimeError`/`ScreeningIntegrityRefused(COVERAGE_INCOMPLETE)`; no `included/excluded/conflicts/prisma*`; no `screening_decisions` artifact; `.rejected` rename; MANIFEST `MISSING` |
| `test_duplicate_entries_refuse_without_publication` | AG-C01 | same study twice ⇒ `DUPLICATE_ENTRY`; same no-output guarantees |
| `test_extra_ids_still_refuse` (regression of existing) | AG-C01 | keeps `test_collect_rejects_decisions_outside_parent_batch` green; asserts the new code path, not a parallel one |
| `test_maybe_and_conflict_refuse_finalize` | AG-C02 | MAYBE row ⇒ `UNRESOLVED_FINALIZE_REFUSED`; study appears in **neither** partition; accepted decision is **not** EXCLUDE (anti-coercion assertion) |
| `test_no_silent_exclusion_regression` | AG-C02 | full-EXCLUDE valid file still publishes exclusions with reasons (proves the gate blocks *unresolved*, not *negative* judgments) |
| `test_decision_hash_recorded_in_lineage_and_journal` | AG-C04hash | accepted artifact lineage + journal row name the exact decision-file sha256 (recomputed independently in-test from file bytes) |
| `test_changed_bytes_after_acceptance_refuse` | AG-C05 | collect → overwrite file (same study, different reason) → re-collect ⇒ `CONTENT_CHANGED` naming both hashes; old artifact intact; no new publication |
| `test_identical_recollect_is_idempotent` | AG-C07retry | collect ×2 identical bytes ⇒ same registry keys (extends existing idempotency test to hash-aware acceptance) |
| `test_failed_promotion_leaves_no_consumable_output` | AG-C06 | each refusal above ⇒ prior `included.json` (from an earlier good collect) byte-identical; no partial new files |
| `test_dual_path_semantics_unchanged` | AG-C08dual | existing dual/adjudication tests green unmodified; consensus still mints `COMPOSED` with both parents |
| `test_human_labeled_but_unapproved_file_is_not_privileged` | AG-C03guard | `method: HUMAN` + human-like `reviewed_by`, integrity-valid ⇒ publishes exactly like the LLM twin (same outputs); integrity-invalid ⇒ refuses exactly like the LLM twin. Documents that AG-02 grants zero authority. |
| `test_no_authorization_concept_in_new_code` | AG-C10guard | static: `integrity.py` + collector diff contain no `approv*`/`authoriz*` identifiers except in comments explicitly marked non-claims; no new identity/key/session imports |

Explicitly **out of scope** (with owner): concurrency leases (future work;
AG-00 row 16 carried), AG-C03/C10 identity enforcement (AG-03, BLOCKED),
AG-C09 source-anchor rules (extraction-layer concern), checklist-sidecar
linkage format (needs the AG-01 architecture decision on record shape —
propose, don't presume), any contract model change, any kit change.

## 5. Acceptance + gates (RELEASE lane)

- All 12 new tests pass; `tests/test_screening_migration.py`,
  `tests/console/test_console_screening.py`,
  `tests/test_contract_acceptance.py`,
  `tests/test_contract_artifact_chain.py` green unmodified (dual + acceptance
  regressions prove no silent behavior drift).
- Baseline/schema/fixture/pin `--check`s green; `ruff check scripts/`;
  `git diff --check`.
- Full owning-repo suite once for the PR candidate (`pr` gate) + closure
  gates per `test_gate_policy.md`; independent reviewer + tester (AG-01
  ADR §6: review of the *mechanism*).
- PR body carries the §2 non-claims verbatim + "No canonical kit repo
  affected; harness-only integrity track." Fork→origin, never merge from
  the coder.
