# HCM-04e-0 — Stage 3 verification identity fallback: characterization + decision

Status: CHARACTERIZED — AWAITING POLICY DECISION

**Lane:** FAST (characterization / documentation / test-only).
**Owner surface:** harness docs + characterization tests only.
**Base:** `origin/main` `f81a3e56410b4716e7f87e011477feb6c4ccf8cc` (PR #89 merged).
**Branch:** `cdx/hcm-04e0-verification-identity-characterization` (isolated workdir
`C:\Users\mouadh\AppData\Local\Temp\codex-hcm-04e0`; primary checkout untouched).
**Governing sources (capsule):** AGENTS.md; pull-request-gate SKILL; COMPASS
§§3/5/7-9; roadmap §§3-6; HCM-01 packet (`hcm_01_characterization_packet.md`);
`test_gate_policy.md` (FAST). Fresh reads: orchestrator Stage 3 slice
(:576-611, incl. :587-598 DOI-bridge + fallback), `workspace/identity.py` +
`errors.py`, `contracts/identifiers.py`, E3 identity-lineage tests, and the
fidelity / discovery / dedup / hydration / core / HCM-01 / HCM-02 tests.
**Env first (done before tests):** `install_plugins --local-only` 8/8;
baseline / schemas / fixture / pins `--check` all green.

No production change is implemented in this packet. No Stage 3 extraction, no
verifier refactor, no screening / extraction / indexing / matrix / graph /
synthesis / recon / methodology change, no auto-migration. This document
characterizes when the last-resort fallback fires and records Options A/B/C +
a recommendation, then STOPS for human approval.

## 1. Target code (verbatim, base)

`src/scholar_harness/orchestrator.py:582-598` (Stage 3: Verification):

```python
verifier = DocumentVerifier()
verified_docs, audit = await verifier.process_batch(
    docs_for_verify, verify=True, enrich=True
)

# Restore workspace_ids on verified docs using DOI as bridge
wsid_by_doi: dict[str, str] = {
    d.external_ids.doi: d.workspace_id
    for d in docs_for_verify
    if d.external_ids.doi and d.workspace_id
}
for vd in verified_docs:
    if not vd.workspace_id and vd.external_ids.doi:
        vd.workspace_id = wsid_by_doi.get(vd.external_ids.doi)
    if not vd.workspace_id:
        # Last resort: assign a temporary sequential ID
        vd.workspace_id = f"SCI-{verified_docs.index(vd) + 1:06d}"
```

Followed by `:600-610` `verified.json` (`asdict` / `indent=2` / `default=str`)
and `:611` `results["stages"]["verification"] = len(verified_docs)` into
Stage 4 screening. Parallel fallback under analysis:
`src/scholar_harness/screening/collector.py:122`
`wid = raw.get("workspace_id") or f"SCI-{i+1:06d}"`.

## 2. Observed (what the code does today)

1. The Deduplicator (Stage 2) assigns the corpus alias id `SCI-%06d` per
   cluster (`tools/scholar-search-kit/src/scholar_search/dedup.py:111`); the
   corpus-snapshot builder later records those values as `alias_ids` with a
   canonical `STU-` study id (`identity.py:328-350`).
2. `DocumentVerifier.verify_document` returns a *freshly normalized* Document
   from `_normalize_document` on every verified path; those constructors never
   take `workspace_id`, so the result is `None` (VEI-01). Only the unverified
   `return False, doc` path returns the input object.
3. The DOI bridge (`:588-592`) maps normalized DOI -> dedup `workspace_id`
   over `docs_for_verify`. It restores when the verifier preserves the DOI
   (VEI-02, including case/prefix-insensitive via `ExternalIds.__post_init__`
   normalization).
4. The last-resort fallback (`:596-598`) fires exactly when, after the bridge
   attempt, `vd.workspace_id` is still falsy (`None` or `""`). Observed firing
   inputs: (a) verifier strips DOI and workspace_id (title-only/unverified
   shape) — VEI-03a; (b) verifier returns a *different* DOI so
   `wsid_by_doi.get` misses — VEI-03b. It does NOT fire when the verifier
   preserves `workspace_id` (VEI-03c) or when the bridge hits (VEI-02).
5. Fallback mints are positional `SCI-000001..N` in `verified_docs` order
   (VEI-04), textually colliding with the dedup alias namespace but carrying
   no cluster/alias lineage (VEI-07/07b — core of Q9).
6. `verified_docs.index(vd)` reads *equality* (`Document.__eq__` over all
   fields incl. `workspace_id`), not identity (VEI-05 isolated). In production
   the in-place mutation currently masks this to enumerate-equivalent
   sequential IDs for equal `None` docs (VEI-05b), but correctness depends on
   that mutation order, not on an explicit position — fragile, `O(n^2)`, and
   order-dependent. An aliased (same-object-twice) list would duplicate one ID
   across two rows (VEI-05c, latent, controlled double only).
7. Fallback numbers identify the *row*, not the study: swapping verifier
   output order swaps which study gets which `SCI-` number (VEI-06). They are
   therefore unstable across runs with different provider/verifier ordering.
8. Downstream, `collector.py:122` re-mints positionally over `raw_verified`
   order for any row still lacking `workspace_id` (VEI-08a) — a second,
   independent positional mint sharing only the `SCI-%06d` shape. Screening
   *candidates* themselves come from the accepted corpus snapshot
   (`study_id`/`alias_ids`), joining `verified.json` abstracts only via
   accepted `alias_to_doc` (VEI-08c), so a fallback `SCI-` with no corpus
   alias entry contributes no candidate row through that path.
9. Stage 6 inherits document/study identity ONLY from the accepted
   `document_manifest` (`_accepted_document_records` over the artifact
   registry) plus the recorded `WSP-` workspace limb from `project.json`
   (HCM-01 HC1-2 lineage). With no accepted manifest the stage refuses
   (`RAG_INDEX_REJECTED`) before any backend and never consults
   `verified.json` workspace_ids (VEI-08b). A fallback `SCI-` can reach
   Stage 6 only if a later screening/extraction packet *accepts* it as a
   study — that path is not proven here (VEI-10).
10. `verified.json` + `results["stages"]["verification"]` / `papers_to_screen`
    carry fallback IDs as ordinary rows with no provenance marker (VEI-09);
    Stage 3 emits no audit event at all, so firing is unobservable post-hoc
    (VEI-10).

## 3. Evidence table (VEI-01..VEI-10)

| ID | Claim | Label | Test(s) |
|----|-------|-------|---------|
| VEI-01 | Kit normalizers return fresh docs with `workspace_id None`; `process_batch(verify=False,enrich=False)` preserves the input object, so loss is inside `verify_document`, not plumbing | REAL-KIT + SOURCE-TRACE | `test_vei_01_normalized_documents_carry_no_workspace_id`, `test_vei_01_verify_document_returns_fresh_doc_without_workspace_id` |
| VEI-02 | DOI bridge restores dedup SCI- IDs when verifier drops workspace_id but keeps DOI; DOI matching is case/prefix-insensitive via `ExternalIds` normalization | HARNESS-INTEGRATION (bridge) + REAL-KIT (normalization) | `test_vei_02_doi_bridge_restores_dedup_workspace_id`, `test_vei_02_doi_bridge_is_case_and_prefix_insensitive` |
| VEI-03a | Fallback fires when no DOI and no workspace_id (bridge has no key) | HARNESS-INTEGRATION | `test_vei_03a_fallback_fires_when_no_doi_no_workspace_id` |
| VEI-03b | Fallback fires when verifier changes DOI (bridge miss); minted IDs textually equal dedup IDs but are positional, DOI lineage broken | HARNESS-INTEGRATION | `test_vei_03b_fallback_fires_when_verifier_changes_doi` |
| VEI-03c | Preserved workspace_id never reaches fallback | HARNESS-INTEGRATION | `test_vei_03c_preserved_workspace_id_never_reaches_fallback` |
| VEI-04 | Fallback shape is positional `SCI-000001..N` in `verified_docs` order | HARNESS-INTEGRATION | `test_vei_04_fallback_shape_is_positional_sci` |
| VEI-05 | `.index(vd)` is equality-sensitive (`==`, not identity) — isolated replica | CONTROLLED-DOUBLE | `test_vei_05_index_expression_is_equality_sensitive_controlled_double` |
| VEI-05b | Production in-place mutation currently masks VEI-05 to sequential IDs for two equal `None` docs (depends on `__eq__` incl. `workspace_id`) | HARNESS-INTEGRATION | `test_vei_05b_equal_docs_still_mint_sequentially_in_production` |
| VEI-05c | Same-object-twice list duplicates one minted ID across two rows (verbatim loop replica; needs verifier aliasing to trigger) | CONTROLLED-DOUBLE | `test_vei_05c_aliased_object_gets_single_id_controlled_double` |
| VEI-06 | Fallback IDs follow verifier order, not study identity (same set, swapped order → same study gets different SCI- number) | HARNESS-INTEGRATION | `test_vei_06_fallback_ids_follow_verifier_order_not_study_identity` |
| VEI-07 | `SCI-` validates as STUDY legacy alias only; `STU-` is the mint prefix; `SCI-` refused as WORKSPACE (`WSP-<32hex>` is the registered form) | SOURCE-TRACE + REAL-KIT | `test_vei_07_sci_is_study_alias_not_workspace_identity` |
| VEI-07b | Real dedup SCI- IDs become corpus `alias_ids` under canonical `STU-` studies; a post-verification mint has no such alias entry (Q9 core) | REAL-KIT | `test_vei_07b_dedup_sci_ids_become_corpus_alias_ids` |
| VEI-08a | Collector `:122` re-mints missing IDs positionally over `raw_verified` order — independent of orchestrator `:598` | HARNESS-INTEGRATION | `test_vei_08_collector_parallel_fallback_remints_positionally` |
| VEI-08b | Stage 6 inherits only accepted `document_manifest` records + recorded `WSP-`; no registry → empty parents + `RAG_INDEX_REJECTED` before backend | SOURCE-TRACE + HARNESS-INTEGRATION | `test_vei_08b_fallback_sci_cannot_reach_stage6_without_acceptance` |
| VEI-08c | Screening candidates come from the accepted corpus (`study_id`), joining verified abstracts only via accepted `alias_to_doc` | SOURCE-TRACE | `test_vei_08c_screening_candidates_come_from_corpus_not_verified_json` |
| VEI-09 | `verified.json` (asdict/indent=2/default=str) + `results` mapping carry fallback IDs as ordinary rows | HARNESS-INTEGRATION | `test_vei_09_verified_json_and_results_mapping_carry_fallback_ids` |
| VEI-10 | Fallback firing is unobservable: no provenance field in `verified.json`, no Stage 3 audit event/counter — answering production frequency requires new instrumentation (STOP) | UNPROVEN + HARNESS-INTEGRATION (absence proof) | `test_vei_10_stage3_emits_no_provenance_or_audit_unproven` |

No test performs network I/O. All orchestrator runs use `tmp_path` workspaces,
fake engines/verifiers/hydrators, a stubbed `agent_screen.cmd_prepare`, and
the real protocol compiler. Doubles are labeled and never presented as
production frequency evidence.

## 4. Evidence sources (where each label comes from)

- REAL-KIT: direct calls into `scholar-search-kit` (`providers/crossref.py`,
  `providers/openalex.py`, `models.ExternalIds/Document`, `dedup.Deduplicator`,
  `identity.build_corpus_snapshot_artifact`) + `contracts/identifiers.py`.
- HARNESS-INTEGRATION: real `ResearchOrchestrator.run_pipeline_async` Stage 3
  lines through `orch.DocumentVerifier` / `orch.SearchEngine` /
  `pipeline.hydration.*` seams; real `_rebuild_doc`,
  `_accepted_document_records`, `_run_indexing_stage`.
- CONTROLLED-DOUBLE: verbatim `f"SCI-{verified_docs.index(vd) + 1:06d}"` loop
  replicas over hand-built `Document` lists (VEI-05/05c).
- SOURCE-TRACE: `inspect.getsource` on `batcher.cmd_prepare`; registry +
  identifier-table assertions; verifier `return True, verified_doc` path
  reading.
- UNPROVEN: VEI-10 absence assertions (no provenance key, no Stage 3 action).

## 5. Unproven / limits (explicit)

- Production firing frequency is UNKNOWN: no counter, event, or provenance
  bit distinguishes preserved vs bridge-restored vs fallback-minted rows.
- Whether the real verifier preserves, drops, or rewrites DOI per provider
  path (Crossref vs OpenAlex vs title-match) beyond the normalized shapes
  tested is not proven here — live provider behavior was deliberately not
  exercised (no network per packet).
- Whether a fallback `SCI-` can be *accepted* downstream as a screening
  `study_id` / extraction `study_id` / manifest `study_id` (the VEI-08b gap)
  is not proven: it needs the screening→extraction acceptance chain traced
  with a fallback-bearing `verified.json`, which is the follow-up packet's
  job, not this one.
- Concurrency, crash-durability, and cross-run determinism of the
  `O(n^2)` `.index` loop beyond VEI-06 ordering are not proven.
- No claim is made about which DOI-strip/DOI-change shapes occur in the
  wild — only that *if* they occur, the fallback is the observed outcome.

If answering any of these requires production edits, this packet STOPS and
reports missing observability instead (done: VEI-10 + follow-up below).

## 6. Implications

- **Compatibility:** fallback rows are shaped exactly like dedup alias rows
  (`SCI-%06d`), so every downstream consumer that string-matches `SCI-`
  cannot tell fabricated alias text from corpus lineage. The collector's
  second positional mint compounds this: two independent position spaces
  share one namespace.
- **Lineage:** a fallback `SCI-` has no `record_to_study`, no `alias_ids`
  entry, no `STU-` study, and no accepted parent. Under Contract v1 and
  COMPASS §3 (workspace/study/document distinct; no filename/index/DOI as
  substitute identity; deterministic generation where order irrelevant) it is
  not an identity — it is a row label. Treating it as a study alias breaks
  the evidence chain the compass requires (workspace → run → protocol →
  corpus → parents → reproducibility).
- **Downstream:** screening candidates are corpus-driven (VEI-08c), and
  Stage 6 is manifest-driven (VEI-08b), so a fallback ID is currently
  *contained* from authoritative indexing — but only because those stages
  ignore `verified.json` IDs. Any future stage that reads `verified.json`
  `workspace_id` as a study key would promote the fabrication silently.
- **Test:** the current suite cannot detect fallback firing (VEI-10) and the
  `.index` expression's correctness rests on `Document.__eq__` including
  `workspace_id` plus in-place mutation order — an implicit contract with no
  test outside this packet until now.
- **Contract version:** no frozen schema/fixture/baseline change is involved
  or proposed. `SCI-` remains a valid legacy STUDY *form* (identifiers.py);
  the issue is *minting* new SCI- text outside the corpus producer, not the
  form itself. No contract-version decision is needed for characterization;
  any policy that mints, refuses, or quarantines needs its own packet gate.

## 7. Options (A/B/C per roadmap §4 packet discipline)

### Option A — Instrument + preserve (bridge first, fallback last, observable)

- Keep the DOI bridge as the primary restore; keep a last-resort mint ONLY
  with an explicit provenance bit per row (e.g. `workspace_id_provenance:
  preserved | bridge_restored | fallback_minted`) plus a Stage 3 audit
  event/counter triple (preserved / restored / fallback counts, no PII).
- Replace `verified_docs.index(vd)` with `enumerate` position (same observed
  numbers per VEI-05b, minus the equality fragility and `O(n^2)` cost).
- Compatibility: byte-shape of `verified.json` rows changes additively
  (new optional provenance key); old readers ignoring it still parse.
  Lineage: fallback rows become *labeled* row labels, still not alias
  identities — downstream must still refuse them as studies.
  Downstream: collector `:122` must adopt the same provenance read (or be
  removed once verified.json guarantees IDs); screening/Stage 6 need no
  change while they stay corpus/manifest-driven.
  Test: per-path counters give VEI-10 the missing observable; add a
  duplicate-ID invariant test (no two verified rows share an ID) and an
  order-stability test.
  Contract version: none (additive, non-authoritative `verified.json` only).

### Option B — Fail-closed (bridge only; refuse or quarantine on miss)

- Keep the bridge; on bridge miss, do NOT mint. Either raise a structured
  refusal for the affected rows or publish them to an explicit quarantine
  (`verified_unresolved.json`) with `PARTIAL` stage status and a refusal
  code, never into authoritative `verified.json`.
- Compatibility: `verified.json` shrinks to identified rows only; any code
  assuming `len(verified) == len(deduped)` must handle `PARTIAL`.
  Lineage: strongest — no alias-namespace text is ever fabricated, so Q9 is
  closed by construction.
  Downstream: collector `:122` fallback must be removed in the same packet
  (it would otherwise re-fabricate what Stage 3 refused); screening must
  handle missing rows explicitly; Stage 6 unchanged (still manifest-driven).
  Test: negative test per COMPASS §7 (missing/changed-DOI → structured
  refusal + zero authoritative publication for those rows); idempotence test
  (rerun with same verifier order → same refusal set).
  Contract version: none for the harness-internal `verified.json` shape, but
  the pipeline outcome gains a new `PARTIAL`/refusal code — needs a reviewed
  outcome-vocabulary decision, not a silent change.

### Option C — Degraded-but-explicit publication (fallback allowed, never as study)

- Keep a positional mint for *display/ordering* continuity, but rename its
  namespace so it cannot collide with the alias space (e.g. `VER-` or
  `TMP-` row labels, never `SCI-`), mark every such row
  `identity_status: unresolved`, and exclude unresolved rows from screening
  batches until resolved via re-verification or human curation.
- Compatibility: breaks string-equality with dedup IDs by design (the point);
  all `SCI-`-prefix consumers need a migration pass.
  Lineage: honest — the label no longer claims alias membership; the
  unresolved flag carries the degradation explicitly (`PARTIAL` semantics
  per COMPASS §3 outcomes).
  Downstream: batcher/collector must filter on `identity_status`; Stage 6
  still refuses unresolved rows via missing manifest parents.
  Test: same as A plus a namespace test (`SCI-` never minted outside
  dedup/corpus) and a filter test (unresolved rows never become candidates).
  Contract version: none (internal row-label namespace), but the new status
  key + filter rule need review as a behavior decision.

## 8. Recommendation

**Recommend Option B (fail-closed) as the policy direction, with Option A's
`enumerate` + instrumentation as the mandatory first mechanical step inside
that packet.**

Rationale: the fallback's entire function is to let an *unidentified* row
pose as an *aliased* study (VEI-07/07b, Q9). COMPASS §3 forbids substituting
an index/position for the registered identity, and §9 forbids inventing
provenance to keep a pipeline green. Option A alone preserves the
fabrication (just labeled); Option C renames it but keeps an authoritative
`verified.json` containing rows with no lineage. Only B restores the
HCM-01/HC1-2 discipline (inherit or refuse; never mint) to Stage 3 and
closes the collector's parallel mint in the same move. The `enumerate`
cleanup and the provenance counters from A are still required — otherwise B
cannot prove it refuses exactly the rows A would have minted.

This packet implements nothing. The human approves a direction first.

## 9. Exact follow-up packet (for the approved policy)

Title: `HCM-04e-1 — verification identity policy (implement the approved option)`.
Scope (bounded, one PR):

1. Apply the approved option (B, or A/C if the human overrides) to
   `orchestrator.py:593-598` ONLY, plus the coupled `collector.py:122` line
   in the same PR (they share the `SCI-%06d` namespace; fixing one without
   the other re-opens the fabrication).
2. Replace `.index(vd)` with `enumerate` (behavior-preserving per VEI-05b;
   pin with the duplicate-ID invariant test).
3. Add per-path observability: `preserved / bridge_restored /
   fallback_or_refused` counts in the Stage 3 result + one audit event (or
   quarantine artifact for B) so VEI-10 becomes answerable.
4. Tests (hermetic, tmp_path, doubles): happy path (VEI-02), both miss
   shapes (VEI-03a/b), no-mint refusal/quarantine proof (no authoritative
   row published for refused inputs), stale/mismatched-parent N/A (Stage 3
   has no accepted parents — state explicitly), determinism/order test
   (VEI-06 rerun → same refusal set, not same positional IDs), and a
   collector-parity test (both mints gone or both labeled).
5. Gates: FAST lane still applies if the diff stays harness-internal with no
   contract/public-surface change; escalate to STANDARD/RELEASE per
   `test_gate_policy.md` if the outcome vocabulary or any persisted shape
   changes. Run the VEI suite + discovery/dedup/hydration/fidelity + E3
   lineage selections + 4 generators + `ruff` + `git diff --check`; full
   harness suite once only if the gate requires it.
6. Forbiddens carried forward: no verifier refactor beyond the call seam, no
   Stage 3 extraction, no screening/extraction/indexing/matrix/graph/
   synthesis/recon/methodology changes, no auto-migration, no
   schema/fixture/baseline/pin edits, no `tools/` changes.

## 10. Validation evidence (this packet)

- Env: `uv run python scripts/install_plugins.py --local-only` → 8/8.
- Generators (before tests, all green):
  `generate_contract_baseline.py --check`, `generate_contract_schemas.py
  --check`, `generate_two_study_contract_fixture.py --check`,
  `generate_nexus_scholar_pins.py --check`.
- New: `uv run pytest tests/unit/test_verification_identity_characterization.py`
  → **19 passed**.
- Neighbors: discovery + dedup + hydration + fidelity + pipeline-core →
  **66 passed** (`test_discovery_stage` + `test_deduplication_stage` +
  `test_hydration_stage` + `test_orchestrator_fidelity` +
  `test_pipeline_core`).
- HCM-01/02 + identity seam: `test_workspace_audit_characterization` +
  `test_workspace_audit_service` + `inception/test_registered_workspace_id`
  → **97 passed**.
- E3 lineage selection (`-k "neg_010 or neg_012 or neg_034 or neg_009 or
  neg_011 or pos_005 or ledger"`) → **8 passed, 30 deselected**.
- `uv run ruff check scripts/` → clean. `git diff --check` → clean.
- Full harness suite: NOT run (FAST lane; focused evidence per spec §6 —
  at most one full run only if needed, not needed: no production files
  changed).
- Base SHA: `f81a3e56410b4716e7f87e011477feb6c4ccf8cc`; branch
  `cdx/hcm-04e0-verification-identity-characterization`.

## 11. Forbidden-path proof

- `git status --short` shows ONLY the two allowed new paths:
  `tests/unit/test_verification_identity_characterization.py` and
  `docs/architecture/hcm_04e_verification_identity_decision.md`.
- No `src/**`, `tools/**`, pins/packaging/locks, schemas/fixtures/baseline,
  UI, workspace/audit, or primary-checkout changes. Verified via
  `git diff --name-only` (two files) + `git diff --check`.
- Toolkit sync: none (no `tools/` touched). Workspace audit event: none
  (workspace mutations forbidden; all fixtures under `tmp_path`).

## 12. Ownership and audit

- TOOLKIT_SYNC: none.
- WORKSPACE_AUDIT_EVENT: none.
- Self-review: two-repair-cycle budget used for test fixes only (VEI-06
  async helper, VEI-07b dedup precondition, VEI-10 action-vs-metrics
  assertion); no production lines read beyond the assigned slices; diff
  inspected for scope creep, permission mismatch, and weakened assertions
  (none — every fallback assertion pins the observed mint, every hazard
  assertion is labeled double vs integration).
