# WP01-E3 Completion Report

> Historical close-out snapshot. The installer and three blocked execution
> rows were subsequently repaired; see [E3 residual repair](e3_residual_repair.md).
> The original evidence and verdict below are preserved, not retroactively rewritten.

- **Packet:** WP01-E3 — stable chunks and index lineage boundary
- **Final verdict:** `APPROVE` (blocked-with-cause close-out: 26/29 ledger IDs live, 3 blocked with recorded cause and owner; see ledger table)
- **Base:** `38c89bc4a54014bdea004831a243a81ab39f0200` (merge of harness PR #74, vendor/pin sync to canonical rag-kit PR #13)
- **Ledger close-out:** harness PR #75 (`dev/phase-e3/task-136-ledger-closure-pos012`, head `e09e9093cd8e570f964a00cc2c88f1b83d236f51`) — `OPEN`, CI 9/9 green including the wheel E3 import probe
- **Next packet:** WP01-E4 — adversarial evidence-currentness proof (unblocked upon this report's merge; its six external mutation cases need a separate packet)

## Closure statement

WP01-E3 is complete as a **blocked-with-cause** boundary. The stable-chunks/index-lineage boundary is adopted: the canonical `scholar-rag-kit` produces a typed, deterministic, kit-owned Index Manifest v1 sidecar with `CHK-` content identity; the bounded harness adapter (`index-acceptance-v1`) re-verifies the immutable Contract v1 parent, re-computes every fingerprint, proves the live backend holds exactly the declared visible chunk set, and only then records the accepted E3 record (`rag/index/accepted.json`) and the canonical `§6.6` audit event; the agent kit declares RAG indexing unsupported on MCP and rejects it without I/O. The harness vendors both canonical implementations at immutable full-SHA pins and is the sole owner of Contract acceptance and publication.

Of the 29 required ledger IDs, **26 are live** (18 harness-executed at the base plus 8 proof-bound in PR #75 against kit ledger tests at the pinned kit commit) and **3 are blocked with cause** (`E3-NEG-021`/`E3-NEG-022`/`E3-NEG-050`: green at the pinned kit `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad` including canonical CI; harness-side execution in this worktree is blocked on the installer quirk where agent-kit's git dependency overwrites the rag-kit editable, resolving `scholar_rag` to stale `033191e` while the pin is `15a7a5a` — a separate packet owns that fix; the harness never synthesizes a path and claims no coverage for the three rows until the blocked behavior is proven).

This closure does not claim retrieval, scoring, synthesis, consensus, claim verification, risk-of-bias, methodology-matrix, or agent-loop behavior. Those remain later packets after E4. The kit-owned `index_manifest` remains outside the frozen Contract v1 registry.

## Canonical publication ledger

### Packet chain (merge SHAs verified in this worktree)

| Stage | Canonical repository / PR | Merge commit | Harness evidence |
|---|---|---|---|
| Packets A–D producers | `nexus-scholar-org/nexus-scholar-harness` PR #42 | `ca6a77bb99615efea1e04e165a0042482297e92f` | Protocol/corpus/acceptance/screening producers adopted; compass records A/B/C/D adopted (`docs/architecture/DEVELOPER_COMPASS.md:1-28`). |
| E1 acquired-document boundary | `nexus-scholar-org/nexus-scholar-harness` PR #47 | `baaeeb43977897924bd6ba9fda252e1bc9d464b8` | E1 completion report closed at that SHA (`docs/architecture/wp01_packet_e1_completion_report.md:5`). |
| E2 extracted-text boundary | `nexus-scholar-org/nexus-scholar-harness` PR #50 | `0fb665558e0808d66348476eda2c927439a96be1` | E2 completion report closed at that SHA (`docs/architecture/wp01_packet_e2_completion_report.md:5`). |
| E2 runtime acceptance | `nexus-scholar-org/nexus-scholar-harness` PR #63 | `193209dd57446fd726b9a845befa6d9e4fbd1578` | Stage 5 extraction published through the frozen acceptance gate (commits `f443b83`, `c5b68cb`). |
| E3 identity limbs | `nexus-scholar-org/nexus-scholar-harness` PR #60 | `fcc2467335a5f72f6b0dcfdca11579bd49f64478` | Bib/graph/rag/agent kits adopted with workspace identity; recorded as E3 base in `docs/architecture/wp01_e3_adoption_status.md:3`. |
| T-130 Stage 6 → IndexService | `nexus-scholar-org/nexus-scholar-harness` PR #65 | `3255333af69692321d092725ac7075298269fc77` | Stage 6 wired to the typed IndexService (commit `0fcde84be16586ca08bcfb91131b7812907dfe67`). |
| E3 adoption status | `nexus-scholar-org/nexus-scholar-harness` PR #64 | `657b9d574b966ea88e3129841507005952656edc` | Status record that identity limbs are merged and full E3 remains open (commit `023d258d874f34c129f780e607648a41a47f9655`; `docs/architecture/wp01_e3_adoption_status.md:1-36`). |
| E3 acceptance adapter | `nexus-scholar-org/nexus-scholar-harness` PR #69 | `bb40f9d6bf593175ffa897740d43a8503adda0e4` | `index-acceptance-v1` adapter, seven-step acceptance, `§6.6` event (commits `9527983`, `fb22077`, `ecd0bc6`, `a16e3cd`). |
| 039 parent-type re-check | `nexus-scholar-org/nexus-scholar-harness` PR #70 | `fb3629d81547a38a4e3380bff86b0f923947d670` | Adapter re-checks the required parent type at publication time (commit `b312cc67db17c70b378b59ef8c89f33168fcf21d`). |
| Rag-kit canonical domain | `nexus-scholar-org/scholar-rag-kit` PR #12 | `f108fa897147f4c837760c81b558d1b82a044fdf` | Identity-limbs fix recorded as the shipped pin in `docs/architecture/wp01_packet_e3_implementation_handoff.md:10`; superseded pre-fix pin `033191eff967abf19023b258539c9a1422c8747f` retained there only as history (`docs/architecture/wp01_packet_e3_implementation_handoff.md:10`). |
| Rag-kit canonical domain | `nexus-scholar-org/scholar-rag-kit` PR #13 | `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad` | Current canonical pin in `.agents/plugins/nexus-scholar/plugins.json:56` and `docs/architecture/wp01_e3_adoption_status.md:6`; vendored at `tools/scholar-rag-kit/` (commit `45304e1002761078585fabceaae1557cd7db814c`). |
| Vendor/pin sync | `nexus-scholar-org/nexus-scholar-harness` PR #74 | `38c89bc4a54014bdea004831a243a81ab39f0200` | Rag-kit vendor-sync to canonical `15a7a5a` (commit `45304e1002761078585fabceaae1557cd7db814c`); this report's base. |
| Ledger / POS-012 close-out | `nexus-scholar-org/nexus-scholar-harness` PR #75 | head `e09e9093cd8e570f964a00cc2c88f1b83d236f51` (`OPEN`) | Three ledger commits `655f9681d52f42ec58f57e0e7bfda319b68173fa`, `70404b0ce7e974a0ebda40ade0318770986e6f14`, `e09e9093cd8e570f964a00cc2c88f1b83d236f51`; CI 9/9 green (6 lint-and-test + schema-validation + 2 wheel-e2e) including the wheel E3 import probe (`.github/workflows/ci.yml:73-77` on that branch; `gh pr checks 75`). |

The frozen Contract v1 models, registries, generated schemas, golden fixtures, baseline, and locked WP01 adoption handoff remained unchanged.

### Kit pins and vendoring

| Kit | `plugins.json` and generated metapackage pin |
|---|---|
| `scholar-rag-kit` | `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad` (`.agents/plugins/nexus-scholar/plugins.json:56`; mirrored in `packaging/nexus-scholar/nexus_scholar_pins.json`) |
| `scholar-agent-kit` | `79ffe421dfea2a2b6e4c02fdff651e6d23ce9b92` (`.agents/plugins/nexus-scholar/plugins.json:64`; mirrored in `packaging/nexus-scholar/nexus_scholar_pins.json`) |

- Pin/import agreement is proven harness-side by `test_e3_neg_048_rag_kit_pin_is_a_full_merged_sha_and_resolves_vendored` (`tests/conformance/test_e3_index_lineage_boundary.py:997`): the pin is a 40-hex full SHA, `scholar_rag` resolves under `tools/scholar-rag-kit`, and the metapackage pin follows `plugins.json` (`tests/conformance/test_nexus_scholar_pins.py:1-70` enforces the mirror with `--check`).
- Agent-kit surface agreement is pinned by the POS-009 tripwire in PR #75 (branch file `tests/conformance/test_e3_index_lineage_boundary.py:1871-1908` at `e09e909`), which asserts the vendored `tools/scholar-agent-kit/src/scholar_agent/server.py:830` shape (`workspace_id: str = None,`), the `mcp_supported=False` declaration (`tools/scholar-agent-kit/src/scholar_agent/capabilities.py:56`), and the 45/45 canonical boundary tests at pinned `79ffe42` (`tools/scholar-agent-kit/tests/test_mcp_indexing_boundary.py`).
- `scripts/generate_nexus_scholar_pins.py --check` passes at the base (enforced by `tests/conformance/test_nexus_scholar_pins.py:67-80`).

### Golden manifest, adapter, and ATOMIC disposition

- Golden manifest `IDX-748c4d3dd6cfc8133835092b36b7b4bc` is unchanged: the harness fixture carries it at `tests/conformance/fixtures/e3_golden_manifest.json:75`, byte-identical to the kit-pinned `GOLDEN_MANIFEST` (`tools/scholar-rag-kit/tests/test_index_manifest.py:66`) via `test_e3_pos_005_harness_fixture_matches_kit_golden_bytes` (`tests/conformance/test_e3_index_lineage_boundary.py:490`), and the baseline `CHK-ab10cb5729e20ff5dc8d26a93455010c` re-derives from the fixture's own limbs (`tests/conformance/test_e3_index_lineage_boundary.py:205`, `:520`).
- The `index-acceptance-v1` adapter owns the accepted E3 record plus the canonical `§6.6` event: schema `index-acceptance-v1` (`src/scholar_harness/index_acceptance.py:122`), record path `rag/index/accepted.json` (`src/scholar_harness/index_acceptance.py:129`), seven-step verdict with `failing_step` 1–7 (`src/scholar_harness/index_acceptance.py:177-203`, `:478`), audit actions `RAG_INDEX_BUILT` / `RAG_INDEX_REJECTED` (`src/scholar_harness/index_acceptance.py:134-140`). Live rows `E3-NEG-037` / `E3-POS-008` prove the exact `§6.6` field set with no forbidden member (`tests/conformance/test_e3_index_lineage_boundary.py:1163`, `:1204`).
- `ATOMIC` concern is `UNSUBSTANTIATED` on the shipped path: the real-Chroma diagnostic (`test_e3_diagnostic_real_chroma_index_workspace_reproducer`, `tests/conformance/test_e3_index_lineage_boundary.py:1670`) records the conditional close-out in the module docstring (`tests/conformance/test_e3_index_lineage_boundary.py:95-103`) — healthy indexing asserts `live_set_matches`, `CHK-` visible ids, and no `ATOMIC_COMMIT_FAILED` in the result/envelope/journal blob; a reproduction would carry the exact typed-request limbs plus backend state before/after plus the full `__cause__` chain as a `REOPEN-KIT` failure. The exact environment (chromadb/python/OS versions, printed by the test) is the scope of that claim.

## §14 completion record

### Handoff references

- Governing handoff: `docs/architecture/wp01_packet_e3_implementation_handoff.md` (Status `SPECIFICATION`, pins at `:10-11`, acceptance criteria `§3` at `:309-406`, manifest `§4` at `:408-590`, identity `§5` at `:616-975` with reproduction `§5.5` at `:975`, acceptance chain `§6` at `:1063`, replacement `§7`, MCP boundary `§9` at `:1315`, ledger `§10` at `:1361-1508`, gates `§11` at `:1509-1574`, completion requirements `§14.2` at `:1655-1673`, handoff to E4 `§14.3` at `:1675-1681`, residual risks `§14.1` at `:1636-1653`).
- Readiness baseline: `docs/architecture/wp01_packet_e3_readiness_baseline.md` (`§4` seven-step acceptance at `:76-95`, `§9` repository order at `:203-225`).
- E4 definition: `docs/architecture/wp01_packet_e4_negative_proof_handoff.md` (status `BLOCKED_E3_COMPLETION` at `:3`, preconditions at `:23-37`, mutation matrix `§5` at `:70-88`).

### Index Manifest v1, identity, and placement (E3-001–E3-006)

- Manifest schema/type: `index-manifest-v1` / `index_manifest` (kit-owned sidecar; the frozen registries reject it with `UNSUPPORTED_ARTIFACT_TYPE` per `E3-NEG-038` at `tests/conformance/test_e3_index_lineage_boundary.py:962` mirroring E2-NEG-021).
- Manifest identity: deterministic `IDX-` (`tests/conformance/fixtures/e3_golden_manifest.json:75`); chunk identity `CHK-` minted from the `§5.1` canonical input and re-derived in `E3-POS-005` (`tests/conformance/test_e3_index_lineage_boundary.py:520`).
- Placement: kit sidecar under the RAG `rag/` subtree per handoff `§4.4`; the accepted adapter record at `rag/index/accepted.json` (`src/scholar_harness/index_acceptance.py:129`); a relocated/symlinked/escaping sidecar is a placement failure (`E3-NEG-022`, blocked — see ledger).
- Study/document identity is inherited byte-for-byte from the accepted parent (`E3-NEG-010` at `tests/conformance/test_e3_index_lineage_boundary.py:560`); cross-workspace manifests are refused before any store (`E3-NEG-012` at `:620`); embedder/backend identity is explicit (`E3-NEG-026` at `:842`); sources are deterministically ordered (`E3-NEG-028` at `:878`).
- Status truthfulness: zero-accepted is `FAILED` with `NO_DOCUMENTS_TO_INDEX` (`E3-NEG-013` at `:661`); mixed batches are `PARTIAL` (`E3-NEG-014` at `:752`); malformed/unaccepted parents refuse before any store (`E3-NEG-015` at `:780`, `E3-NEG-016` at `:807`); generation agreement breaks on protocol mutation (`E3-NEG-049` at `:1024`); publication-time parent-type divergence refuses `(7, REQUIRED_PARENT_TYPE_MISSING)` with zero publication (`E3-NEG-039` at `:1272`, PR #70 `fb3629d` / `b312cc6`).

### Public surfaces and ownership (E3-008)

- Authoritative kit path: `scholar_rag.index_service.IndexServiceRequest` / `index_workspace` plus `index_manifest`, `replacement`, `index_verifier`, `chunker`, `embedder` (POS-012 static half enumerates the authoritative set in PR #75 at `tests/conformance/test_e3_index_lineage_boundary.py:1911-1964`).
- Harness acceptance: `scholar_harness.index_acceptance.accept_index_candidate` (`src/scholar_harness/index_acceptance.py:478`) and the Stage 6 entry `scholar_harness.extraction_producer.index_accepted_documents` (`src/scholar_harness/extraction_producer.py:1620`), wired through the orchestrator in PR #65 (`3255333` / `0fcde84`).
- MCP capability `rag_indexing` is declared with `mcp_supported=False` (`tools/scholar-agent-kit/src/scholar_agent/capabilities.py:56`); `nexus_rag_index` returns the deterministic `UNSUPPORTED_CAPABILITY` envelope (`tools/scholar-agent-kit/src/scholar_agent/server.py:826-836`); the vendored surface shape `workspace_id: str = None,` is pinned at `tools/scholar-agent-kit/src/scholar_agent/server.py:830` and tripwired by `E3-POS-009` (PR #75 at `tests/conformance/test_e3_index_lineage_boundary.py:1871`).

### Per-ID ledger table (29 rows)

Live = harness-executed at the base OR proof-bound in PR #75 (open, CI green) against the named kit ledger test at pinned `15a7a5a` (rag) / `79ffe42` (agent). Blocked = honest `MISSING` marker; the harness claims no coverage until the blocked behavior is proven.

| ID | State | Proof location (live) or blocked cause + owner + next packet |
|---|---|---|
| E3-NEG-009 | LIVE (proof-bound, PR #75) | Harness `test_e3_neg_009_kit_document_eligibility_join_is_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1592`) + kit `test_t90_neg_009_a_document_absent_from_the_accepted_parent_is_refused` (`tools/scholar-rag-kit/tests/test_index_service.py:2140` @`15a7a5a`). |
| E3-NEG-010 | LIVE | `test_e3_neg_010_request_limbs_inherit_recorded_identity` (`tests/conformance/test_e3_index_lineage_boundary.py:560`). |
| E3-NEG-011 | LIVE (proof-bound, PR #75) | Harness `test_e3_neg_011_kit_study_lineage_join_is_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1651`) + kit `test_t90_neg_011_a_study_absent_from_the_accepted_lineage_is_refused` (`tools/scholar-rag-kit/tests/test_index_service.py:2176` @`15a7a5a`). |
| E3-NEG-012 | LIVE | `test_e3_neg_012_cross_workspace_manifest_is_not_inherited` (`tests/conformance/test_e3_index_lineage_boundary.py:620`). |
| E3-NEG-013 | LIVE | `test_e3_neg_013_zero_accepted_run_is_failed_never_success` (`tests/conformance/test_e3_index_lineage_boundary.py:661`). |
| E3-NEG-014 | LIVE | `test_e3_neg_014_mixed_batch_is_partial_never_success` (`tests/conformance/test_e3_index_lineage_boundary.py:752`). |
| E3-NEG-015 | LIVE | `test_e3_neg_015_malformed_parent_refuses_before_any_store` (`tests/conformance/test_e3_index_lineage_boundary.py:780`). |
| E3-NEG-016 | LIVE | `test_e3_neg_016_no_manifest_refuses_before_touching_a_store` (`tests/conformance/test_e3_index_lineage_boundary.py:807`). |
| E3-NEG-017 | LIVE (proof-bound, PR #75) | Harness `test_e3_neg_017_kit_parent_hash_mismatch_is_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1694`) + kit `test_neg_017_a_hash_stale_parent_is_refused_with_parent_hash_mismatch` (`tools/scholar-rag-kit/tests/test_index_manifest.py:1951` @`15a7a5a`). |
| E3-NEG-021 | BLOCKED | Cause: harness-side execution blocked on the installer quirk — kit T-90 021 expects `PATH_OUTSIDE_WORKSPACE` at pinned `15a7a5a` (clean green) but resolves `VALIDATION_ERROR` under stale `033191e` in this worktree; the harness never synthesizes a path (recorded in PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:2047`). Owner: installer-quirk packet (agent-kit's git dep overwrites the rag-kit editable; see `scripts/install_plugins.py:178-200`; superseded pin `033191e` per `docs/architecture/wp01_packet_e3_implementation_handoff.md:10`). Next: separate packet owns the fix; do not re-close with a loosened assertion. |
| E3-NEG-022 | BLOCKED | Cause: same installer-quirk block as 021 — kit T-90 022 expects `PATH_OUTSIDE_WORKSPACE` at pinned `15a7a5a` (clean green) but resolves `VALIDATION_ERROR` under stale `033191e` (recorded in PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:2055`). Owner: installer-quirk packet. Next: separate packet owns the fix. |
| E3-NEG-026 | LIVE | `test_e3_neg_026_embedder_identity_is_explicit_in_the_request` (`tests/conformance/test_e3_index_lineage_boundary.py:842`). |
| E3-NEG-028 | LIVE | `test_e3_neg_028_sources_are_deterministically_ordered` (`tests/conformance/test_e3_index_lineage_boundary.py:878`). |
| E3-NEG-030 | LIVE (proof-bound, PR #75) | Harness `test_e3_neg_030_kit_per_study_uniqueness_is_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1745`) + kit `test_neg_030_a_chunk_id_reused_within_one_study_is_refused` (`tools/scholar-rag-kit/tests/test_index_manifest.py:722` @`15a7a5a`). |
| E3-NEG-031 | LIVE (proof-bound, PR #75) | Harness `test_e3_neg_031_kit_collection_uniqueness_is_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1792`) + kit `test_neg_031_a_chunk_id_reused_across_studies_is_refused` (`tools/scholar-rag-kit/tests/test_index_manifest.py:756` @`15a7a5a`). |
| E3-NEG-034 | LIVE | `test_e3_neg_034_no_emittable_identity_leaves_stage6` (`tests/conformance/test_e3_index_lineage_boundary.py:907`). |
| E3-NEG-035 | LIVE (proof-bound, PR #75) | Harness `test_e3_neg_035_kit_usability_refusal_is_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1836`) + kit `test_t90_neg_035_an_unusable_extraction_is_rejected_with_its_code` (`tools/scholar-rag-kit/tests/test_index_service.py:1014` @`15a7a5a`). |
| E3-NEG-036 | LIVE | `test_e3_neg_036_no_similarity_as_entailment_language` (`tests/conformance/test_e3_index_lineage_boundary.py:936`). |
| E3-NEG-037 | LIVE | `test_e3_neg_037_acceptance_event_has_no_incomplete_or_leaking_field` (`tests/conformance/test_e3_index_lineage_boundary.py:1163`). |
| E3-NEG-038 | LIVE | `test_e3_neg_038_frozen_registries_reject_the_index_manifest_sidecar` (`tests/conformance/test_e3_index_lineage_boundary.py:962`). |
| E3-NEG-039 | LIVE | `test_e3_neg_039_publication_time_parent_type_is_rechecked` (`tests/conformance/test_e3_index_lineage_boundary.py:1272`; PR #70 `fb3629d`). |
| E3-NEG-048 | LIVE | `test_e3_neg_048_rag_kit_pin_is_a_full_merged_sha_and_resolves_vendored` (`tests/conformance/test_e3_index_lineage_boundary.py:997`). |
| E3-NEG-049 | LIVE | `test_e3_neg_049_protocol_mutation_breaks_generation_agreement` (`tests/conformance/test_e3_index_lineage_boundary.py:1024`). |
| E3-NEG-050 | BLOCKED | Cause: same installer-quirk block — kit T-90 050 expects `PARTIAL`/exit 3 at pinned `15a7a5a` (clean green) but resolves `SUCCESS`/exit 0 under stale `033191e`; index-time staleness has no Stage 6 check by design (recorded in PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:2063`). Owner: installer-quirk packet. Next: separate packet owns the fix. |
| E3-POS-005 | LIVE | `test_e3_pos_005_harness_fixture_matches_kit_golden_bytes` + `test_e3_pos_005_baseline_chunk_id_rederives_from_the_fixture_limbs` (`tests/conformance/test_e3_index_lineage_boundary.py:490`, `:520`; kit source `tools/scholar-rag-kit/tests/test_index_manifest.py:66` @`15a7a5a`). |
| E3-POS-007 | LIVE | `test_e3_pos_007_refusal_proves_zero_publication` (`tests/conformance/test_e3_index_lineage_boundary.py:1050`). |
| E3-POS-008 | LIVE | `test_e3_pos_008_acceptance_event_carries_the_full_section_66_field_set` (`tests/conformance/test_e3_index_lineage_boundary.py:1204`). |
| E3-POS-009 | LIVE (proof-bound, PR #75) | Harness `test_e3_pos_009_mcp_boundary_tripwire_is_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1871`) + agent-kit `tools/scholar-agent-kit/tests/test_mcp_indexing_boundary.py` (45/45 at pinned `79ffe42`) + vendored shape `tools/scholar-agent-kit/src/scholar_agent/server.py:830`. |
| E3-POS-012 | LIVE (PR #75) | Harness `test_e3_pos_012_declared_imports_are_proof_bound` (PR #75 `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:1911`) + CI Smoke-step E3 import probe (`.github/workflows/ci.yml:73-77` on PR #75; green in run `37896825642` / `37899537605`, 9/9 jobs). |

Ledger index completeness is enforced by `test_e3_ledger_index_covers_every_required_id` (`tests/conformance/test_e3_index_lineage_boundary.py:1848` at the base; `26 live / 3 MISSING` form in PR #75 at `e09e909`, `tests/conformance/test_e3_index_lineage_boundary.py:2330-2410`). The three blocked rows are never counted as live above.

### §14.2 mapping (where each required item lives)

1. Canonical merge SHAs: rag-kit PR #12 `f108fa897147f4c837760c81b558d1b82a044fdf` and PR #13 `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad` (`docs/architecture/wp01_packet_e3_implementation_handoff.md:10`); agent-kit `79ffe421dfea2a2b6e4c02fdff651e6d23ce9b92` (`.agents/plugins/nexus-scholar/plugins.json:64`).
2. `plugins.json` pins plus regenerated metapackage pins: tables above; `--check` enforced by `tests/conformance/test_nexus_scholar_pins.py:67-80`.
3. `§11.2`/`§11.3` gate outputs: CI 9/9 green on PR #75 (`gh pr checks 75`; runs `37896825642`, `37899537605`); the four generator `--check` commands are CI-enforced (handoff `§11.2` at `docs/architecture/wp01_packet_e3_implementation_handoff.md:1525`).
4. `§5.5` reproduction against the merged kit fixture: `E3-POS-005` (`tests/conformance/test_e3_index_lineage_boundary.py:490`, `:520`; handoff `§5.5` at `docs/architecture/wp01_packet_e3_implementation_handoff.md:975`).
5. Coverage table: the 29-row ledger above (criteria `E3-001`–`E3-014` at `docs/architecture/wp01_packet_e3_implementation_handoff.md:309-406`; classes `§10.2` at `:1383`).
6. `§10.3` matrix: unchanged from the handoff (`docs/architecture/wp01_packet_e3_implementation_handoff.md:1475`); no requirement row was moved by E3.
7. Residual risks: `§14.1` R-1–R-9 restated verbatim below, plus the new installer-quirk risk discovered during implementation.
8. Explicit non-scope: no retrieval, scoring, synthesis, consensus, claim verification, risk-of-bias, methodology-matrix, agent-loop, or Contract v1 change (handoff `§2.2` / readiness `§10` at `docs/architecture/wp01_packet_e3_readiness_baseline.md:227-237`).
9. Surface-matrix diff: the `upsert`-idempotent / re-index-not-replacement warning correction is owned by the E3 adoption PRs (#60 `fcc2467`, #65 `3255333`, #69 `bb40f9d`); no Contract v1 file was edited for it.

### Residual risks (§14.1 restated verbatim) plus new risk

| # | Residual risk | Why it is accepted | Mitigation |
|---|---|---|---|
| R-1 | `producer.commit` participates in `index_fingerprint`, so upgrading the kit invalidates every accepted index even when the chunk set is identical | A different implementation commit is a different reproducibility claim; pretending otherwise would make the fingerprint lie about who produced the bytes | A `REUSED`-equivalent fast path compares `chunk_set_fingerprint` and `configuration_fingerprint` first and reports an explicit `reindex_required_for_producer_change` instead of silently re-deriving |
| R-2 | `artifact_checksum` is not run-invariant, because it seals the file as written | It is the E1 construction; a whole-file seal that ignored run identity would not be a seal of the file | Comparability is defined on `deterministic_projection` (§5.2) and asserted there |
| R-3 | `production_fingerprint` is an E3 field with no Contract v1 counterpart | Contract v1 has no index artifact to carry it; adding one is a v2 decision | It is a sidecar field only, and it feeds no stage that can cycle |
| R-4 | The atomic visibility switch is backend-dependent, so "atomic" is a property of the backend's own set-level operation | Readiness §7 allows backend-specific mechanics with backend-neutral semantics | R5 is required to be a pointer/marker move, never an in-place edit; a backend that cannot do this is refused rather than approximated |
| R-5 | A legacy store cannot be migrated in place, so migration costs a full re-index from the accepted parent | Readiness §10 forbids in-place migration; a cheaper path would reuse un-derivable identity | The mandatory dry run reports the cost and every refusal before anything is written |
| R-6 | The accepted E3 record is adapter-owned and non-Contract, so a consumer that only reads Contract v1 artifacts cannot see that an index exists | Contract v1 has no index artifact type; the baseline ratifies this boundary explicitly | The accepted record is workspace-local, content-sealed, and always paired with the audit event that names the same `manifest_id` |
| R-7 | `min_chunk_chars` must be implemented or removed, and either choice changes existing chunk boundaries for some workspaces | The option is currently inert, so "no change" is already false in spirit: the configuration claims an effect it does not have | The choice is a reviewed decision in the canonical PR; a deprecation warning is emitted and the option is absent from the recorded configuration afterwards |
| R-8 | The golden manifest is a fixture in two repositories, which is a drift surface | The parity test (`E3-POS-005`) fails on drift, and a single canonical source is generated into both | The §5.5 reproduction re-derives the digests from the document itself, so a hand-edited digest cannot pass review |
| R-9 | Rejecting indexing over MCP is a capability regression for any agent that used the current tool | The current tool cannot express the required identity or a `PARTIAL` result, so parity is not available to preserve | `§9` declares the boundary with a typed `UNSUPPORTED_CAPABILITY` refusal and names the supported alternatives |
| R-10 (new) | The plugin installer can let a kit's git dependency overwrite another kit's editable install, so the executing `scholar_rag` resolves stale while the pin and vendored tree are current | Editable-vs-git precedence is installer behavior, not index semantics; papering it over inside E3 tests would hide a real environment defect | PR #75 keeps 021/022/050 honestly `MISSING` with the stale-vs-clean record (`033191e` vs `15a7a5a`); a separate installer packet owns the fix and must re-prove the three rows without loosening their assertions |

### Deferred maintenance (non-blocking, separately owned)

- Installer quirk: `scripts/install_plugins.py:178-200` (editable vs `git+...@rev` precedence). Owner: installer packet. Next: fix precedence/isolation, then re-execute 021/022/050 harness-side with no assertion change.
- E2E/inception hermetic-mock watch: `tests/e2e/test_e2e_extract_index.py:164` and `tests/inception/test_registered_workspace_id.py:407` use the deterministic mock embedder; the anti-drift assertion pattern is documented at `tests/inception/test_registered_workspace_id.py:1016-1019`. Owner: e2e/inception maintenance. Next: separate follow-up if mock shapes drift from the kit; not an E3 blocker.
- Agent-prompt hygiene: `.opencode/agent/reviewer.md:4-11` declares the reviewer read-only; any user edit to that contract is outside E3. Owner: dev-loop maintenance. Next: separate follow-up; not an E3 blocker.

### E4 statement

E4 is unblocked upon this report's merge. Its six external mutation cases need a separate packet: flip one acquired PDF byte (`E4-NEG-001`), change one accepted extracted byte (`E4-NEG-002`), change one chunking-configuration value (`E4-NEG-003`), change embedding identity (`E4-NEG-004`), alter parent lineage (`E4-NEG-005`), and remove/add/corrupt backend chunks or metadata (`E4-NEG-006`) — each per `docs/architecture/wp01_packet_e4_negative_proof_handoff.md:77-84`, under the `BLOCKED_E3_COMPLETION` gate at `:3` and preconditions at `:23-37`. E4 mutates copies of a sealed fixture only and must observe refusal, stale/currentness failure, or a new lineage-bound rebuild for each case. This report starts none of that work.

## Reviewer verdict

`APPROVE` — WP01-E3 is safe for WP01-E4 to consume under the blocked-with-cause terms above. Exact pins agree across the canonical kit commits, the vendored trees, `plugins.json`, and the generated metapackage pins; the golden `IDX-748c4d3dd6cfc8133835092b36b7b4bc` manifest is unchanged and its baseline `CHK-` re-derives; the `index-acceptance-v1` adapter plus `rag/index/accepted.json` plus the `§6.6` event is the only publication path; 26/29 ledger IDs are live with executable proof and the remaining 3 are honestly blocked (not claimed as live) with a recorded clean-green kit state and a separately owned installer fix; PR #75 CI is 9/9 green including the wheel E3 import probe; no Contract v1 schema was weakened, no unmerged toolkit revision is pinned, no vendored-only toolkit implementation was introduced, and no scientific workspace was modified.

## Audit disposition

No `workspaces/<slug>/` research project was modified, so no scientific workspace journal event applies. The durable audit trail is the canonical PR/merge ledger above, the immutable toolkit pins, the golden fixture plus `E3-POS-005` parity gate, the `index-acceptance-v1` accepted records and `RAG_INDEX_BUILT` / `RAG_INDEX_REJECTED` events asserted by the conformance suite, the PR #75 CI runs (`37896825642`, `37899537605`), and this completion report. Tester gate: `GATE_PASS` on the ledger/CI evidence cited above (PR #75 9/9 green; base conformance file owns the 18 executed rows and the ledger-index completeness check).
