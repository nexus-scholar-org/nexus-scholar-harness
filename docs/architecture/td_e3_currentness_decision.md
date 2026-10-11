# TD-E3-CURRENTNESS-01 — stale-currentness `parameters=` TypeError: characterization + decision

Status: CHARACTERIZED — AWAITING POLICY DECISION

**Lane:** FAST (characterization; full suite at most once and only if needed — prefer focused evidence).
**Owner surface:** characterization tests + decision doc only.
**Base:** `origin/main` `dab85b4b10806b4f9332e43a310479e5715daef1` (PR #101 merged; HEAD==origin/main, clean, hooks set).
**Branch:** `cdx/td-e3-currentness-characterization` (isolated workdir `C:\Users\mouadh\AppData\Local\Temp\codex-td-currentness`; primary checkout untouched).
**Governing sources (capsule):** AGENTS.md; COMPASS §§3/5/7-9; `contract_v1_baseline.md` (frozen boundary); WP01-E3 readiness (`wp01_packet_e3_readiness_baseline.md`), implementation handoff (`wp01_packet_e3_implementation_handoff.md` §6), completion (`wp01_packet_e3_completion_report.md`); `test_gate_policy.md` (FAST); `agent_context_protocol.md`. Fresh reads: `pipeline/indexing.py` stale block (:515-544), `index_acceptance.py` (:658-666 preflight + adapter), `extraction_producer.validate_extraction_currentness` (:1392) + `index_accepted_documents` (:1648-1700), `contracts` identifiers/acceptance/canonical, E3 conformance + Stage-6 + e2e tests, entry points (CLI `extract index` :415-418, `agent_extract`, coordinator `indexing_fn`), `kits_surface_matrix.md`, rag-kit SKILL.
**Env first (done before tests):** `install_plugins --local-only` 8/8 (pre-existing `.venv`; verified imports); 4 generators green BEFORE tests (baseline / schemas / fixture / pins `--check`).

No runtime change is implemented in this packet. No indexing/coordinator/orchestrator/adapter/toolkit/pin/packaging/generated/contract-schema/fixture/UI/governance change, no weakening/deselection/xfail/baseline-regen, no mitigation. This document characterizes when the preserved stale-currentness `TypeError` fires and records Options A/B/C + a recommendation, then STOPS for human approval.

## 1. Scope and non-goals

**In scope (evidence-only):**

- Prove the mechanism by execution: bad-keyword `parameters=` (not missing-param/shape); owner is harness argument construction, not kit.
- Classify every entry path (1)-(5) plus spec shapes (6)-(10) by EXECUTION, not assumption, with before/after snapshots for every reachable shape.
- Map contract (Observed vs Requirement vs Inference vs Recommended-policy) without calling anything a violation until a mapped requirement proves it.
- Record Options A/B/C + recommendation (only if evidence supports) + bounded follow-up per option.

**Non-goals (explicit STOP):**

- No fix to `pipeline/indexing.py:530-539`, no coordinator/orchestrator/adapter change, no new vocabulary, no audit-event repair, no result-shape repair.
- No `tools/` change (if reproducer showed kit-side origin instead, this packet would STOP as `BLOCKED_CANONICAL_REPO` — not observed; see §3).
- No workspace mutation (all fixtures under `tmp_path`); no `workspaces/` audit event.
- No full-suite run (FAST lane; focused + required selections only — full once only if needed, not needed: no production files changed; see §11).
- Missing observability is reported, never repaired by editing production (see §8 UNPROVEN).

## 2. Target code (verbatim, base)

`src/scholar_harness/pipeline/indexing.py:515-544` (stale-currentness branch):

```python
if parent_view is not None:
    from scholar_harness.extraction_producer import (
        PublicationRefused,
        validate_extraction_currentness,
    )

    try:
        validate_extraction_currentness(ws, parent_view["artifact_id"])
    except PublicationRefused as exc:
        # PRESERVED LATENT DEFECT (parity-only, not repaired): the base
        # passes ``parameters={"code": ...}`` to an audit writer that
        # accepts no such keyword, so both the base
        # (``_log_audit_event``) and this stage (``append_legacy_event``)
        # raise ``TypeError`` before any byte is written, with no
        # publication. The call shape is kept verbatim.
        append_legacy_event(
            ws,
            action="RAG_INDEX_REJECTED",
            agent="scholar-harness",
            description="Stage 6 refused stale extraction provenance",
            inputs=[str(parent_view["artifact_id"])],
            outputs=[],
            metrics={"documents": 0},
            status="FAILED",
            parameters={"code": exc.code},  # type: ignore[call-arg]
        )
        return IndexingOutcome(
            result={"status": "FAILED", "code": exc.code, "documents": 0},
            indexer=None,
        )
```

Writer signatures (base, SOURCE-TRACE):

```python
# workspace/audit.py:229
def append_legacy_event(workspace, action, agent, description, inputs, outputs, metrics, status="SUCCESS") -> None
# orchestrator.py:655
def _log_audit_event(self, action, agent, description, inputs, outputs, metrics, status="SUCCESS") -> None
```

Neither accepts `parameters`. The canonical writer that *does* accept `parameters` is `workspace.audit.append_event` / `console.api.audit.log_event` (different function, different byte discipline) — not called here.

Producer preflight (CLI/agent path, SOURCE-TRACE):

```python
# extraction_producer.py:1694-1697
for artifact_id in manifest_ids:
    validate_extraction_currentness(workspace, artifact_id)
try:
    result, _indexer = ResearchOrchestrator(workspace)._run_indexing_stage(target)
```

Adapter preflight (index-acceptance check 4, SOURCE-TRACE):

```python
# index_acceptance.py:658-666
from scholar_harness.extraction_producer import PublicationRefused, validate_extraction_currentness
try:
    validate_extraction_currentness(workspace, parent.artifact_id)
except PublicationRefused as exc:
    raise _Refusal(4, "VALIDATION_ERROR", str(exc)) from exc
```

## 3. Mechanism (bad-keyword, harness owner — proved by execution)

| ID | Claim | Label | Test(s) |
|----|-------|-------|---------|
| TD-01 | Real `append_legacy_event(..., parameters={"code":...})` raises `TypeError: got an unexpected keyword argument 'parameters'` with zero journal bytes (bad-keyword, not missing-param/shape) | HARNESS-INTEGRATION | `test_a1_append_legacy_event_rejects_parameters_keyword` |
| TD-02 | Real `ResearchOrchestrator._log_audit_event(..., parameters=...)` raises the identical `TypeError` with zero bytes (same shape existed at base via `_log_audit_event`) | HARNESS-INTEGRATION | `test_a2_orchestrator_adapter_rejects_parameters_keyword` |
| TD-03 | Neither signature contains `parameters`; the stale site carries `# type: ignore[call-arg]` verbatim (preserved defect, not repaired) | SOURCE-TRACE | `test_a3_neither_writer_signature_accepts_parameters` |
| TD-04 | Kit `validate_extraction_currentness` raises typed `PublicationRefused(STALE_EXTRACTED_BODY)` for a real changed body (hand-built record + real file) — never `TypeError` | REAL-KIT | `test_a4_kit_validate_raises_typed_stale_for_changed_body` |

Owner: harness argument construction (`workspace.audit.append_legacy_event` + `_log_audit_event` signatures + stale call site). NOT kit: the kit raises typed correctly (TD-04). No `BLOCKED_CANONICAL_REPO` trigger observed. Every observation above is measured; no inference is presented as mechanism.

Chained proof (HARNESS-INTEGRATION + CONTROLLED-DOUBLE): `test_b1`/`test_b2` assert `TypeError.__context__` is `PublicationRefused` with `code == STALE_EXTRACTED_BODY` — the kit refusal is the cause, the harness keyword is the failure.

## 4. Reachability (entry paths 1-10, classified by EXECUTION)

| # | Entry path | Verdict (measured) | Evidence |
|---|---|---|---|
| (1) | Direct `pipeline.indexing.run_indexing` with controlled stale `parent_view` | REACHABLE — raw `TypeError`, no bytes | HARNESS-INTEGRATION `test_b1_run_indexing_stale_raises_typeerror_with_no_bytes` (controlled stale double + real stage; boom backends prove no construction) |
| (2) | Coordinator/orchestrator full-pipeline route | REACHABLE-VIA-DELEGATE — same `TypeError` through `orch._run_indexing_stage`; coordinator wiring is verbatim delegate call | HARNESS-INTEGRATION `test_b2_orchestrator_stage_stale_raises_typeerror_with_no_bytes` + SOURCE-TRACE `coordinator.py:107,317` (`indexing_fn(chroma_dir)` with `indexing_fn=self._run_indexing_stage`; no mapping, propagate). Full end-to-end with real discovery→extraction→registry UNPROVEN (would need a real accepted workspace through all 9 stages; not run per FAST lane) |
| (3) | CLI `extract index` → `index_accepted_documents` (:1695 BEFORE :1697) | UNREACHABLE for stale via this path — preflight raises typed `STALE_EXTRACTED_BODY` FIRST; orchestrator never entered; no `TypeError` | CONTROLLED-DOUBLE `test_c1_producer_preflight_raises_typed_before_orchestrator` (boom orchestrator proves non-entry) + CONTROLLED-DOUBLE `test_c2_cli_extract_index_maps_typed_to_stage6_refused` (CLI maps to `stage6_refused`, exit 1) |
| (4) | `agent_extract` same-producer path | UNREACHABLE — shares the one producer function; same typed refusal, exit 1, never `TypeError` | CONTROLLED-DOUBLE `test_c3_agent_extract_maps_typed_to_refusal` + SOURCE-TRACE (both call `index_accepted_documents`; `agent_extract._cmd_index` + `cli._extract_index` source assertions) |
| (5) | `index_acceptance.py:660-666` preflight context | SEPARATE — stale maps to typed `IndexAcceptanceResult(accepted=False, failing_step=4, code=VALIDATION_ERROR)` with `STALE_EXTRACTED_BODY` in detail; never `TypeError`; zero publication | HARNESS-INTEGRATION + CONTROLLED-DOUBLE `test_c4_index_acceptance_maps_stale_to_step4_validation_error` (minimal registry/parent passing checks 1-3 + controlled stale raise) |
| (6) | Valid-accepted-stale | REACHABLE via (1)/(2) only; UNREACHABLE via (3)/(4)/(5) (each has earlier typed handling) | `test_b1`/`test_d1`/`test_neg05` (multi-doc still `TypeError`, no PARTIAL) |
| (7) | Missing-manifest | Takes EARLIER path — `parent_view is None` skips stale check; `DOCUMENT_MANIFEST_NOT_ACCEPTED` with one `RAG_INDEX_REJECTED` line; stale validate never called | HARNESS-INTEGRATION `test_d2_missing_manifest_takes_earlier_path_with_one_rejection_line` + `test_neg01_missing_manifest_takes_earlier_path_no_stale` (tracking-validate proves non-entry) |
| (8) | Missing-source-parent (blank study, no screening parent) | Takes LATER path — skipped in request building → `NO_DOCUMENTS_TO_INDEX`, `FAILED` never `SUCCESS`; workspace limb never reused as study | HARNESS-INTEGRATION `test_d4_blank_study_never_reuses_workspace_limb` |
| (9) | No-documents | Takes LATER path — `request is None` → `NO_DOCUMENTS_TO_INDEX`, `FAILED` never `SUCCESS`, no backend | HARNESS-INTEGRATION `test_d3_no_documents_is_failed_never_success` |
| (10) | Mixed-batch-stale / reuse-rebuild | Mixed (2-doc) stale still raw `TypeError`, no PARTIAL publication; replay (rebuild) still `TypeError`, still no bytes (no idempotent reuse reached — exception precedes any reuse check) | HARNESS-INTEGRATION `test_neg05_mixed_batch_stale_still_typeerror_no_partial_publication` + `test_b3_stale_replay_still_typeerror_still_no_bytes` |

No path is called fixed/safe/compliant/unreachable without the measured proof named above. Path (2) full-pipeline end-to-end remains UNPROVEN beyond the delegate (explicit limit, §8).

## 5. Consequences (measured bytes/files/backend/journal before+after)

Snapshot discipline: every test records `_snapshot(ws)` before/after (journal bytes/lines, registry bytes, project bytes, chroma/rag/accepted existence, `*.tmp-*` leftovers). Exception path requires byte-identical snapshots.

| Shape | Backend/client built? | Index/replacement started? | Manifest/accepted written? | Audit event? | Journal bytes? | Temp/quarantine/residue? | Result form? | Replay? |
|---|---|---|---|---|---|---|---|---|
| Stale via (1)/(2) (TD-05) | No — boom embedder/backend/reader/index would raise `AssertionError`; observed `TypeError` instead (HARNESS-INTEGRATION `test_b1`/`test_b2`/`test_d1`) | No — `rag/` absent, `chroma_db` absent (same tests) | No — `rag/index/accepted.json` absent (same) | None — zero lines (same) | Unchanged — `after == before`, `b""` when seeded empty; seeded line preserved verbatim with no addition (`test_neg04`) | None — `tmp_leftovers == []`, no quarantine (Stage 6 owns none) | Raw `TypeError` (not typed `PublicationRefused`, not mapped dict); `__context__.code == STALE_EXTRACTED_BODY` | Stable — 2nd run same `TypeError`, still no bytes (`test_b3`) |
| Stale via (3)/(4) preflight | No — boom orchestrator never entered (`test_c1`) | No — `rag/` absent | No | None | Unchanged (`b""`) | None | Typed `PublicationRefused(code=STALE_EXTRACTED_BODY)`; CLI maps to `{"stage6_refused":True,"status":"FAILED",code}` exit 1; agent maps to `{"indexing_refused":...}` exit 1 (`test_c2`/`test_c3`) | N/A (deterministic typed refusal; replay would re-raise same code — UNPROVEN for real registry replay beyond doubles) |
| Stale via (5) adapter | No backend touch (check 6 never runs — fail-fast at step 4) | No | No — `accepted.json` absent | None — steps 1-6 write no journal line (spec §6.5) | Unchanged (`b""`) | None | Typed `IndexAcceptanceResult(accepted=False, failing_step=4, code=VALIDATION_ERROR, detail contains STALE)` (`test_c4`) | N/A |
| Missing-manifest (7) | No (boom proves) | No | No | One `RAG_INDEX_REJECTED` `FAILED` with `metrics.rejection_code == DOCUMENT_MANIFEST_NOT_ACCEPTED` | +1 line; prior bytes preserved as prefix (`test_d2`/`test_neg01`) | None | Mapped dict `{"status":"FAILED","indexed_files":0,...,"refused":[{"document_id":"","reason":"no accepted document_manifest"}]}` + `MinimalIndexer(count 0)` | N/A |
| No-documents (9) / blank-study (8) | No | No | No | One `RAG_INDEX_REJECTED` `FAILED` with `NO_DOCUMENTS_TO_INDEX` | +1 line; prefix preserved | None | Mapped dict `{"status":"FAILED",...,"refused":[{"document_id":"","code":"NO_DOCUMENTS_TO_INDEX"}]}`; `FAILED` never `SUCCESS`; WSP limb absent from payload (`test_d3`/`test_d4`) | N/A |

No no-publication claim is made without the observables above. The stale exception path snapshots are byte-identical (`test_d1` asserts `after == before`; `test_neg04` asserts seeded-line preservation).

## 6. Contract map (Observed vs Requirement vs Inference vs Recommended-policy)

Do NOT call anything a violation until a mapped requirement proves it. Each row: Observed (measured) → Requirement (frozen source) → Inference (allowed) → Recommended-policy (needs approval).

| Topic | Observed (label) | Requirement (source) | Inference (not a violation finding) | Recommended-policy (needs packet) |
|---|---|---|---|---|
| Currentness / fingerprint | Stale body is detected by kit `validate` as typed `STALE_EXTRACTED_BODY` (REAL-KIT TD-04); direct Stage-6 stale branch crashes before audit with no event (HARNESS-INTEGRATION TD-05) | COMPASS §3: reject stale/mismatched parents; E3 readiness §8 + handoff §10.2: changed extracted bytes at unchanged path must refuse; E4-NEG-002 proves producer `STALE_EXTRACTED_BODY` refusal with record preserved (e2e `test_republication...`, 1 passed §11) | The detection exists and is typed at the producer/kit seam; the direct Stage-6 branch fails to *report* it (no event, wrong exception) but does not publish. Whether unobservability alone is a contract violation is UNPROVEN here — no mapped clause requires a Stage-6 stale audit shape; audit-truthfulness (below) is the nearest requirement | Policy must choose a typed stale report + audit shape (Options A/B/C §10); do not invent provenance to keep the pipeline green (COMPASS §9) |
| Accepted-parent fail-closed | Direct stale: no backend, no accepted record, no journal, raw raise (HARNESS-INTEGRATION §5); preflight/adapter: typed refusal, no store, previous index intact (CONTROLLED-DOUBLE/HARNESS-INTEGRATION §4) | COMPASS §3 fail-closed: validation/acceptance failure must stop authoritative publication; E3 handoff §6.4-6.5: steps 1-6 leave previous state untouched; step 7 is the only writer | Fail-closed *publication* holds on every stale shape measured (no authoritative bytes). This is an observation, not a compliance verdict — failure to *report* is separate from failure to *stop* | Keep fail-closed publication in every option; add a reportable refusal (B) or minimal audit repair (A) — never publish on stale |
| E3 vocabulary: is there an existing STALE code? | Producer owns `STALE_EXTRACTED_BODY` (E2 replay + Stage-6 preflight; e2e Major 5 + `test_c1`); Stage-6 direct branch has no STALE code (returns `code` only in its dead `{"status":"FAILED","code":...}` dict, never reached); adapter maps stale to `VALIDATION_ERROR` step 4 (HARNESS-INTEGRATION `test_c4`); frozen `ErrorCode` owns `INTERNAL_ERROR` (`contracts/models.py:78`) | Handoff §4.5 + E3-NEG-050 note: index-time staleness has no Stage-6 check by design (`EXTRACTED_CONTENT_CHANGED` is kit T-50); publish-time staleness is producer `STALE_EXTRACTED_BODY` (conformance `:80-82`); handoff §6.2 step 4 failure code is `VALIDATION_ERROR` | An existing stale-specific code exists at the producer, not at Stage-6. Reusing it at Stage-6 would be a harness vocabulary choice, not a kit change. `DOCUMENT_MANIFEST_NOT_ACCEPTED` would misdescribe (manifest IS accepted); `INTERNAL_ERROR` would hide cause (see §10 fit analysis) | Option B names `STALE_EXTRACTED_BODY` as the leading existing-vocabulary candidate (fit analysis §10); Option C costs a new code/version if B is rejected |
| Stage-6 status mapping | Direct stale (if it returned) would be `{"status":"FAILED","code":exc.code,"documents":0}` — `FAILED` is canonical (`OperationStatus.FAILED`) but shape lacks `indexed_files/total_chunks/collection_count/refused` that every other Stage-6 refusal carries; other refusals are `FAILED` never `SUCCESS` with `DOCUMENT_MANIFEST_NOT_ACCEPTED`/`NO_DOCUMENTS_TO_INDEX` (HARNESS-INTEGRATION §5) | COMPASS §3 outcomes: empty is not success; degraded is `PARTIAL` with explanation; hard failure carries structured error; `OperationStatus` is the canonical vocabulary (producer `publication_status`, CLI `INDEXING_STATUS_NOT_CANONICAL` check) | Shape inconsistency is observed; whether it violates a frozen status requirement is UNPROVEN — no frozen Stage-6 result schema was cited as normative for this packet. Do not call it a violation here | Any policy must return the established Stage-6 refusal shape (`indexed_files/total_chunks/refused[].code`) with a canonical `FAILED` (B), not the dead 3-key dict |
| CLI/API expectations | CLI `extract index` renders typed refusal as `{"stage6_refused":True,"status":"FAILED",code}` exit 1 (CONTROLLED-DOUBLE `test_c2`); agent `index` emits `{"indexing_refused":...}` exit 1 (same `test_c3`); zero-indexed success exits 1 via `indexed_files==0` rule (`cli.py:426`) | CLI contract: refusal is data, not a traceback; exit non-zero on refusal/zero-indexed (agent `EXIT_REFUSED=1`, CLI `exit_code or 1`) | Typed preflight preserves the CLI/API contract on stale; the direct-path `TypeError` would break it (uncaught traceback, no `stage6_refused` shape) — but that path is unreachable via CLI/agent (measured §4), so no CLI violation is observed | Keep typed preflight first (all options); direct-path repair must also satisfy the CLI shape if that path ever becomes CLI-reachable |
| No-fabrication + audit-truthfulness | Stale direct path writes no success, no `PARTIAL`, no invented `workspace_id` — but also writes no refusal/rejection/failure event, so firing is unobservable post-hoc (HARNESS-INTEGRATION absence proof: `after == before`) | COMPASS §3: record the actual method; a fallback must be explicit; do not invent provenance; §9: never invent provenance to keep a pipeline green; HCM-04e VEI-10 precedent: unobservable firing is a gap, not a pass | No fabrication is observed (nothing invented). Audit-truthfulness gap is observed (no event for a real refusal). The gap is reported as debt, not as a proven violation — no clause cited here mandates a specific stale audit payload | Every option must make stale observable (A: minimal audit line; B: typed code + event; C: versioned event). Missing provenance is legacy debt, not retroactively fabricated |

## 7. Evidence table (matrix A/B/C/D + negatives)

| ID | Claim | Label | Test(s) |
|----|-------|-------|---------|
| TD-A1 | Bad-keyword `TypeError` on real `append_legacy_event`, zero bytes | HARNESS-INTEGRATION | `test_a1_append_legacy_event_rejects_parameters_keyword` |
| TD-A2 | Same `TypeError` on real `_log_audit_event`, zero bytes | HARNESS-INTEGRATION | `test_a2_orchestrator_adapter_rejects_parameters_keyword` |
| TD-A3 | Signatures lack `parameters`; stale site has `ignore[call-arg]` | SOURCE-TRACE | `test_a3_neither_writer_signature_accepts_parameters` |
| TD-A4 | Kit raises typed `STALE_EXTRACTED_BODY` for real changed body | REAL-KIT | `test_a4_kit_validate_raises_typed_stale_for_changed_body` |
| TD-B1 | Direct `run_indexing` stale → raw `TypeError` chained from STALE, no bytes/backend/chroma/accepted | HARNESS-INTEGRATION + CONTROLLED-DOUBLE | `test_b1_run_indexing_stale_raises_typeerror_with_no_bytes` |
| TD-B2 | Orchestrator delegate stale → same `TypeError`, same observables | HARNESS-INTEGRATION | `test_b2_orchestrator_stage_stale_raises_typeerror_with_no_bytes` |
| TD-B3 | Replay still `TypeError`, still no bytes | HARNESS-INTEGRATION | `test_b3_stale_replay_still_typeerror_still_no_bytes` |
| TD-C1 | Producer preflight typed `STALE_EXTRACTED_BODY` before orchestrator; orchestrator never entered | CONTROLLED-DOUBLE | `test_c1_producer_preflight_raises_typed_before_orchestrator` |
| TD-C2 | CLI maps typed to `stage6_refused` exit 1, never `TypeError` | CONTROLLED-DOUBLE + SOURCE-TRACE | `test_c2_cli_extract_index_maps_typed_to_stage6_refused` |
| TD-C3 | Agent maps typed to `indexing_refused` exit 1; shares producer | CONTROLLED-DOUBLE + SOURCE-TRACE | `test_c3_agent_extract_maps_typed_to_refusal` |
| TD-C4 | Adapter maps stale to `(4, VALIDATION_ERROR)` with STALE in detail, zero publication | HARNESS-INTEGRATION + CONTROLLED-DOUBLE | `test_c4_index_acceptance_maps_stale_to_step4_validation_error` |
| TD-D1 | Stale consequence row: `after == before`, no backend/chroma/accepted/event; raw `TypeError` | HARNESS-INTEGRATION | `test_d1_stale_consequence_table_is_no_publication_no_audit` |
| TD-D2 | Missing-manifest earlier path: one `RAG_INDEX_REJECTED` (`DOCUMENT_MANIFEST_NOT_ACCEPTED`), prefix preserved | HARNESS-INTEGRATION | `test_d2_missing_manifest_takes_earlier_path_with_one_rejection_line` |
| TD-D3 | No-documents: `NO_DOCUMENTS_TO_INDEX`, `FAILED` never `SUCCESS` | HARNESS-INTEGRATION | `test_d3_no_documents_is_failed_never_success` |
| TD-D4 | Blank study never reuses WSP limb; same `NO_DOCUMENTS_TO_INDEX` | HARNESS-INTEGRATION | `test_d4_blank_study_never_reuses_workspace_limb` |
| TD-NEG-01 | Missing-manifest never calls stale validate (tracking double) | HARNESS-INTEGRATION + CONTROLLED-DOUBLE | `test_neg01_missing_manifest_takes_earlier_path_no_stale` |
| TD-NEG-02 | Identity refusal before backend, bytes/store untouched | HARNESS-INTEGRATION | `test_neg02_identity_refusal_leaves_bytes_and_store_untouched` |
| TD-NEG-03 | Refused run never touches backend (boom on any touch) | HARNESS-INTEGRATION | `test_neg03_refused_run_never_touches_backend` |
| TD-NEG-04 | Stale exception path with seeded line: byte-identical, no addition | HARNESS-INTEGRATION | `test_neg04_stale_exception_path_writes_no_bytes_restores_identical` |
| TD-NEG-05 | Mixed 2-doc stale still `TypeError`, no `PARTIAL`, no accepted | HARNESS-INTEGRATION | `test_neg05_mixed_batch_stale_still_typeerror_no_partial_publication` |

No test performs network I/O. All workspaces live under `tmp_path`; embedder/backend are faked or boom-guarded; stale is a labeled controlled double except TD-A4 (real kit) and the real-stage paths that consume it. Doubles are never presented as production frequency evidence.

## 8. Evidence sources, labels, and unproven limits

- REAL-KIT: direct `scholar_pdf.frontmatter.sha256_bytes` + `extraction_producer.validate_extraction_currentness` over hand-built record/file (TD-A4).
- HARNESS-INTEGRATION: real `pipeline.indexing.run_indexing` / `orch._run_indexing_stage` / `index_acceptance.accept_index_candidate` / `cli._extract_index` / `agent_extract._cmd_index` with `tmp_path` workspaces, fake/boom kit seams, real registry/parent shapes where stated.
- CONTROLLED-DOUBLE: monkeypatched `validate_extraction_currentness` raising the kit's real `PublicationRefused(STALE_EXTRACTED_BODY)`; boom backends/readers/embedders; fake `parent_view`/context/manifest-ids. Each such test names the double in its docstring.
- SOURCE-TRACE: `inspect.signature` on both writers; `read_text` on the stale site (`parameters=` + `ignore`); `getsource` on CLI/agent producer calls; `coordinator.py:107,317` delegate wiring; `extraction_producer.py:1695-before-1697` ordering; `index_acceptance.py:663-666` mapping.
- UNPROVEN (explicit):
  - Full end-to-end pipeline (discovery→synthesis) reaching stale indexing with a real accepted registry + real publication record: not run (FAST lane; delegate + preflight proofs suffice for classification).
  - Production firing frequency of the direct stale path: UNKNOWN (no counter/event/provenance bit; direct path writes nothing, so frequency is unobservable without new instrumentation — STOP, do not instrument here).
  - Live provider/real-Chroma stale shapes beyond the mock/boom seams: not exercised (no network, no model download, `HF_HUB_OFFLINE` pattern not needed here since backend never constructed).
  - Whether any caller beyond the five classified paths invokes `run_indexing` with a stale-capable `parent_view`: not exhaustively grepped as proof (source search is not execution).
  - Reuse/rebuild semantics beyond replay-still-`TypeError`: no idempotent-reuse path is reached on stale (exception precedes it); supersession by a different `manifest_id` is adapter-owned and out of scope.

If answering any of these requires production edits, this packet STOPS and reports missing observability instead (done: this section + §9).

## 9. Implications

- **Compatibility:** the dead stale `return {"status":"FAILED","code":...,"documents":0}` is unreachable (raise precedes it). Any repair that merely fixes the keyword but keeps that 3-key shape would introduce a *new* reachable result shape inconsistent with every other Stage-6 refusal (`indexed_files/total_chunks/refused[].code`). Callers reading `indexed_files` (CLI `:426`) would see `0` via `.get` default — same exit, different introspection.
- **Lineage:** stale means the accepted manifest's identity limbs are unchanged while the bytes behind `extracted_path` changed (E2 `STALE_EXTRACTED_BODY` semantics). The frozen `DocumentRecord` carries no body field, so the artifact id cannot express the change — republishing would lie as idempotent replay. Fail-closed publication holds today (no bytes), but the report is a raw `TypeError`, not a lineage-bound refusal.
- **Downstream:** CLI/agent are *contained* (typed preflight first); the adapter is *separate* (step-4 `VALIDATION_ERROR`). Only direct `run_indexing`/`_run_indexing_stage` callers (orchestrator delegate, coordinator `indexing_fn`, tests, future stages) observe the `TypeError`. Any future stage that calls the direct path with a stale-capable `parent_view` inherits the crash silently.
- **Test:** the existing `test_c17_stale_currentness_raises_typeerror_with_no_bytes` pins the audit-level `TypeError` but does not exercise the real `run_indexing` stale branch, the preflight-first ordering, the adapter mapping, or the consequence snapshots — this packet's 20 tests fill that gap without touching production.
- **Contract version:** no frozen schema/fixture/baseline change is involved or proposed. `STALE_EXTRACTED_BODY` is producer-owned (not frozen `ErrorCode`); `INTERNAL_ERROR` is frozen; `VALIDATION_ERROR` is the adapter's step-4 code. Any policy that mints, renames, or versions vocabulary needs its own packet gate (§10C).

## 10. Options A/B/C + recommendation + bounded follow-up per option

### Option A — Minimal keyword repair (keep branch, fix audit call only)

- Change ONLY the stale `append_legacy_event` call to a keyword the writer accepts (e.g. drop `parameters=` and carry `exc.code` in `metrics`/`description`, or call the canonical `append_event` with `parameters=` and the §6.6 field discipline — exact choice is the follow-up packet's, not this doc's). Keep the branch position, the `RAG_INDEX_REJECTED` action, `FAILED` status, and fail-closed (no backend/accepted on stale).
- Compatibility: smallest diff; journal gains one stale line where today there are zero. Lineage: still reports the kit's `STALE_EXTRACTED_BODY` cause (as text/metrics), but result shape stays the dead 3-key dict unless the packet also normalizes it (recommended: normalize to the established refusal shape in the same one-line packet, else the new shape becomes a second inconsistency).
- Downstream: CLI/agent unchanged (still preflight-first); direct callers stop crashing and start receiving the branch return. Test: stale now returns (not raises) with one audit line; replay returns identically; negatives unchanged.
- Contract version: none (harness-internal audit + result dict). Cost: one-line diff + this packet's 20 tests updated (raise→return) + one new audit-shape assertion.

### Option B — Typed refusal on existing vocabulary (bridge-or-refuse for currentness)

- Keep preflight-first; on stale (both direct branch and preflight), refuse with the EXISTING producer code as the machine-readable cause. Leading candidate: **`STALE_EXTRACTED_BODY`**.
  - Fit: exact cause (bytes differ from accepted E2 publication; E2 Major 5 + E4-NEG-002 precedent; `test_c1`/`test_a4` prove the code already means this). Stage-6 would carry it as `refused[].code` (or top-level `code` alongside the normalized shape) with `status FAILED`, plus a `RAG_INDEX_REJECTED` event naming the code — no new vocabulary, no version bump.
  - Rejected alternatives: `DOCUMENT_MANIFEST_NOT_ACCEPTED` — WRONG fit (manifest IS accepted; reusing it would conflate absence with staleness and break the missing-manifest invariant `test_d2`/`test_neg01`). `INTERNAL_ERROR` — POOR fit (frozen `ErrorCode` for internal defects; the stale cause is caller-visible data drift with an actionable fix — re-run extraction or new generation — not a defect; using it would hide the repair and force operators to treat data staleness as a bug; reserved for genuine adapter faults per `indexing.py:814` + e2e `test_orchestrator_adapter_fault...`).
- Compatibility: result shape normalized to the established Stage-6 refusal (`indexed_files:0/total_chunks:0/collection_count:None/documents:[]/refused:[{document_id:"",code:STALE...}]`); audit line uses only accepted keywords. Lineage: strongest honest report without new namespace. Downstream: CLI `stage6_refused`/`indexing_refused` shapes can carry the code verbatim; adapter step-4 `VALIDATION_ERROR` detail already names it (no change needed there).
- Test: happy (valid-accepted-current still indexes — proven by existing A1/e2e selections §11), both miss shapes (stale → typed `STALE_EXTRACTED_BODY` + zero publication + one audit line), no-mint proof (no `SCI-`-style fabrication — N/A here; no-publication proof per §5 snapshots), determinism (rerun → same refusal set), collector-parity N/A (no collector mint in Stage 6).
- Contract version: none (reuses producer-owned code + established refusal shape). Cost: small branch edit + audit-line addition + ~5 focused tests (stale-typed, audit-shape, replay, CLI/agent parity, adapter no-change).

### Option C — Explicit stale-currentness boundary (new code/version/schema)

- Introduce a NEW stale-currentness vocabulary or versioned event (e.g. `RAG_INDEX_STALE` action, or `STALE_INDEX_PARENT` code, or `index-acceptance-v2` stale field, or a frozen-contract stale artifact — exact namespace is an architecture/version decision, not this packet's).
- Compatibility: breaks string-equality with `STALE_EXTRACTED_BODY` consumers by design; every `STALE_*`/`VALIDATION_ERROR`/CLI-shape consumer needs a migration pass. Lineage: explicit, but pays for distinction the existing code already carries.
- Downstream: batcher/collector/adapter/CLI/MCP docs must adopt the new token; screening/Stage 6 result readers must handle the new shape. Test: same as B plus namespace test (old code never emitted on the new path) + migration test (old workspaces still refuse, never misread).
- Contract version: LIKELY (new persisted code/action/schema or frozen-contract addition) — requires architecture/version decision, regenerated schemas and golden fixtures, a negative regression test, and independent review per COMPASS §5/§9. Cost: version decision + schema/fixture regen + full E3/e2e gates + docs/migration. Only justified if B's reuse is ruled ambiguous by the human.

### Recommendation

**Recommend Option B (typed refusal on existing `STALE_EXTRACTED_BODY`) as the policy direction, with Option A's audit-keyword fix as the mandatory first mechanical step inside that packet.**

Rationale (evidence-bound): the kit already names this exact cause with a typed, actionable refusal (TD-A4 REAL-KIT + E2 Major 5 + E4-NEG-002); the harness already propagates that exact code typed-first on the CLI/agent paths (`test_c1` CONTROLLED-DOUBLE) and names it in the adapter's step-4 detail (`test_c4`); only the direct branch loses it to a bad keyword (TD-01..TD-03 + `test_b1`/`test_b2` chained-cause proof). Reusing the code closes the report gap with zero new vocabulary, preserves fail-closed publication (§5), and keeps the CLI/adapter contracts unchanged. Option A alone would stop the crash but keep the dead 3-key shape and leave the cause taxonomy split (`STALE_*` at producer vs anonymous at Stage-6). Option C pays version/schema costs for distinction the evidence does not require.

This packet implements nothing. The human approves a direction first.

### Bounded follow-up outline per option (one PR each, FAST→STANDARD escalation per gate)

- **If A approved (`TD-E3-CURRENTNESS-02-A`):** edit `pipeline/indexing.py:530-539` audit call ONLY (+ normalize result dict to the established refusal shape in the same hunk); update `test_c17` + this packet's B/D/NEG stale expectations (raise→return + one audit line); run new file + Stage-6 + E3 selections + e2e stale trio + 4 generators + ruff + diff-check. Forbiddens: no vocabulary change, no adapter/producer/coordinator change, no schema/fixture/pin change, no `tools/` change.
- **If B approved (`TD-E3-CURRENTNESS-02-B`):** A-step plus carry `STALE_EXTRACTED_BODY` as `refused[].code` (and top-level `code` if the established shape requires it) with `RAG_INDEX_REJECTED` event metrics naming the code; add stale-typed + audit-shape + replay + CLI/agent parity tests; prove zero publication per §5 snapshots; document `DOCUMENT_MANIFEST_NOT_ACCEPTED`/`INTERNAL_ERROR` non-fit in the PR description. Same gates as A plus the e2e `STALE` + `DOCUMENT_MANIFEST` + adapter-fault trio (§11). No new code/version.
- **If C approved (`TD-E3-CURRENTNESS-02-C`):** architecture/version decision first; then new token/schema/event + migration + regen (schemas/fixtures/baseline/pins via generators, never hand-edits) + namespace + migration tests + full harness suite once (STANDARD/RELEASE per `test_gate_policy.md`) + cross-kit checks if the token crosses the kit boundary. Do not weaken schemas or fixtures to make tests pass.

## 11. Validation evidence + forbidden-path proof + ownership/audit

- Env: `.venv` pre-existing (thin + 8 kits; `import scholar_rag, scholar_harness` ok). Generators BEFORE tests, all green: `generate_contract_baseline.py --check` (current), `generate_contract_schemas.py --check` (exit True), `generate_two_study_contract_fixture.py --check` (exit True), `generate_nexus_scholar_pins.py --check` (OK, in sync).
- New: `uv run pytest tests/unit/test_td_e3_currentness_characterization.py` → **20 passed** (A4+B3+C4+D4+NEG5).
- Neighbors: `tests/pipeline/test_indexing_stage.py` → **18 passed** (Stage-6 parity + preserved `test_c17` audit-level `TypeError` still green — this packet does not alter it).
- E3 lineage selection (`-k "neg_010 or neg_012 or neg_034 or neg_009 or neg_011 or pos_005 or ledger or neg_016 or neg_013"`) → **10 passed, 28 deselected**.
- E2E extraction-runtime trio (`-k "republication_after_the_body_changes_is_refused or index_without_an_accepted_manifest or orchestrator_adapter_fault"`) → **3 passed, 79 deselected** (producer `STALE_EXTRACTED_BODY` + `DOCUMENT_MANIFEST_NOT_ACCEPTED` + adapter-fault `INTERNAL_ERROR` shapes — the vocabulary fit witnesses for §10B).
- Selectors: `select_test_gate.py --task TD-E3-CURRENTNESS-01 --stage inner` → `ERROR: unknown tasks: TD-E3-CURRENTNESS-01` (no TD mapping expected — documented); `--path tests/unit/test_td_e3_currentness_characterization.py --stage inner` → full-suite fallback (no path rule; documented). Used nearest Stage-6/E3 groups above instead of full suite per FAST lane. `--check` → `OK: 16 tasks, 4 stages`.
- `uv run ruff check scripts/` → clean (`All checks passed!`). `git diff --check` → clean.
- Full harness suite: NOT run (FAST lane; focused evidence per spec §6 — at most one full run only if needed, not needed: no production files changed; base-compare N/A with no failures to compare).
- Base SHA: `dab85b4b10806b4f9332e43a310479e5715daef1`; branch `cdx/td-e3-currentness-characterization`.

**Forbidden-path proof:**

- `git status --short` shows ONLY the two allowed new paths: `tests/unit/test_td_e3_currentness_characterization.py` and `docs/architecture/td_e3_currentness_decision.md` (this file).
- No `src/**`, `tools/**`, pins/packaging/locks, schemas/fixtures/baseline, UI, workspace/audit, or primary-checkout changes. Verified via `git diff --name-only` (two files) + `git diff --check` (clean).
- Toolkit sync: none (no `tools/` touched). Workspace audit event: none (workspace mutations forbidden; all fixtures under `tmp_path`).

**Ownership and audit:**

- TOOLKIT_SYNC: none.
- WORKSPACE_AUDIT_EVENT: none.
- Self-review: one-repair-cycle budget used for test fix only (C3 agent-module binding: `prod` vs `agent_module` import seam; no production lines read beyond assigned slices §§2/6; diff inspected for scope creep, permission mismatch, weakened assertions — none; every stale assertion pins the observed `TypeError`, every typed assertion pins the observed code/step).

## 12. No-behavior-change statement

This packet changes no behavior. No runtime file was edited; no toolkit, pin, packaging, generated, contract-schema, fixture, UI, or governance file was edited; no test was weakened, deselected, `xfail`ed, or baseline-regenerated; no unrelated docs were touched; no origin push was made. The two new files are characterization evidence (20 tests) and this decision record. The preserved stale-currentness `TypeError` still fires exactly as at the base; the CLI/agent preflight still refuses typed first; the adapter still maps to step-4 `VALIDATION_ERROR`. Any repair, mitigation, vocabulary choice, or observability addition requires the human-approved follow-up packet in §10. Missing observability is reported, never edited into production by this packet.
