# Harness Remediation Specification

**Component:** `src/scholar_harness`  
**Version:** 1.0.0-draft  
**Status:** Ready for design review  
**Priority:** P0/P1  
**Primary owners:** Harness, console, screening, workspace-state maintainers

## 1. Problem statement

The harness exposes two pipeline models:

1. `ResearchOrchestrator.run_pipeline_async`, a fixed research workflow; and
2. `PipelineExecutor`, a user-configurable subprocess DAG used by the console.

Both models have valid use cases, but their contracts diverge. The configurable
DAG accepts templates that cannot execute against current kit CLIs, while the
fixed workflow can reuse a stale screening result after preparing new batches.
State and audit events are also derived by multiple implementations with
different semantics.

The harness must become the authoritative coordinator of state transitions,
without reimplementing toolkit domain logic.

## 2. Current architecture and evidence

### 2.1 Fixed workflow

`ResearchOrchestrator` compiles protocol search, discovers, deduplicates,
hydrates, verifies, prepares screening batches, pauses for human decisions, then
extracts, indexes, builds a matrix and graph, and synthesizes. The core flow is in
`src/scholar_harness/orchestrator.py:484-843`.

Confirmed boundary defects:

- search resources close only after successful `search_all` at
  `orchestrator.py:518-520`;
- new screening batches are forced at `orchestrator.py:646-650`, but downstream
  gating checks only existence of `literature/included.json` at `:672-675`;
- indexing passes the corpus slug as every document's `workspace_id` at
  `:754-759`, triggering RAG's study-identity collapse;
- graph client lifecycle is not closed at `:779-794`;
- audit IDs use process-randomized `hash()` and status is hardcoded `SUCCESS` at
  `:857-884`.

### 2.2 Configurable DAG

`PipelineSpec` and built-ins live in
`src/scholar_harness/console/api/pipelines.py:35-388`. The executor resolves
templates and renders every argument as a GNU-style flag at
`src/scholar_harness/pipeline_executor.py:142-199`.

Confirmed defects:

- all five built-in discovery nodes use nonexistent `scholar-search run`, first
  visible at `pipelines.py:100-105`;
- dedup's positional input is modeled as an `input` flag at `:110-115`;
- boolean options are serialized to string values by
  `pipeline_executor.py:167-175`;
- output existence is treated as idempotency without binding output to a command
  or input fingerprint at `:247-254`;
- an unknown edge source is recorded as an error but `_toposort` still indexes
  `adj[src]`, producing `KeyError` at `pipelines.py:416-423`;
- a dry run validates schema/templates but never checks the installed CLI surface
  at `pipelines.py:620-658`.

### 2.3 Screening

`screening/batcher.py:143-249` creates review batches.
`screening/collector.py:67-323` assembles decisions into canonical included and
excluded artifacts. Existing batch and decision files are not bound to the
current protocol and verified-corpus content.

### 2.4 Console and jobs

The console creates a local FastAPI application in `console/serve.py:30-71`.
The action registry is a curated command surface in
`console/runtimes/actions.py:37-152`, while saved PipelineSpecs can contain
arbitrary argv. Job state is in memory and subprocess results are written under
`.harness-console/jobs` by `console/runtimes/job_runner.py`.

## 3. Goals

1. Make every shipped pipeline template executable against pinned kit CLIs.
2. Make dry-run validity mean schema-valid, contract-valid, and resolvable.
3. Bind screening decisions and downstream gates to exact current inputs.
4. Make reruns idempotent by fingerprints, not file existence.
5. Consolidate audit events and workspace state transitions.
6. Preserve toolkit ownership of scientific/domain behavior.
7. Make cancellation, partial failure, and pending-human states explicit.
8. Support safe migration of existing workspaces and saved PipelineSpecs.

## 4. Non-goals

- Replacing toolkit algorithms with harness implementations.
- Removing the human screening handoff.
- Guaranteeing reproducibility of live provider results.
- Making the console safe for untrusted public internet exposure.
- Running independent DAG nodes concurrently in this remediation phase.
- Replacing the entire PipelineSpec format when a versioned migration suffices.

## 5. Normative requirements

### 5.1 Pipeline command model

**HAR-CMD-001 (MUST):** Every built-in PipelineSpec command must parse and execute
against the kit versions pinned in `plugins.json`.

**HAR-CMD-002 (MUST):** A node argument must declare its rendering kind:
`positional`, `option`, `repeatable_option`, `switch`, or `json_value`. The
executor must not infer all arguments as `--key value`.

**HAR-CMD-003 (MUST):** Built-in search nodes must use `scholar-search search`.
The query must be positional or protocol-driven according to the actual CLI.

**HAR-CMD-004 (MUST):** Built-in dedup nodes must provide the collection as a
positional input and explicitly pass the declared output path.

**HAR-CMD-005 (MUST):** `False` switches must be omitted. `True` switches must be
rendered as a bare flag unless the registered CLI contract explicitly accepts a
boolean value.

**HAR-CMD-006 (MUST):** Repeatable options must emit one flag per value when the
CLI requires repetition.

**HAR-CMD-007 (MUST):** Pipeline validation must resolve the command against a
versioned command registry or an equivalent generated CLI manifest. Unknown
commands, subcommands, options, or positional layouts are validation errors.

**HAR-CMD-008 (SHOULD):** The command registry should be generated from toolkit
Typer surfaces or maintained by the owning toolkit with conformance tests; it
should not be duplicated manually in the console.

**HAR-CMD-009 (MUST):** Arbitrary custom commands must be explicitly marked
`custom: true` and must not be presented as verified kit commands.

### 5.2 DAG validation and execution

**HAR-DAG-001 (MUST):** Graph validation must accumulate unknown-node errors and
return without calling topological sort on invalid edges.

**HAR-DAG-002 (MUST):** Topological ordering must be deterministic for a fixed
specification. The tie-break policy must be documented and tested.

**HAR-DAG-003 (MUST):** A node may run only after all declared predecessors have
reached an allowed terminal state. `on_fail=continue` must not implicitly make a
missing required input valid.

**HAR-DAG-004 (MUST):** Node success requires exit code zero and validation of
all declared outputs. Missing outputs after a zero exit are a failure.

**HAR-DAG-005 (MUST):** Idempotent skip requires a matching node-run manifest
containing the node fingerprint, resolved command, input fingerprints, output
fingerprints, kit versions, and prior successful outcome. File existence alone
must not skip execution.

**HAR-DAG-006 (MUST):** `requires_decision` must halt in a first-class
`WAITING_FOR_DECISION` state rather than raising a generic pipeline error.

**HAR-DAG-007 (MUST):** Cancellation must distinguish `CANCEL_REQUESTED`,
`CANCELLED_BEFORE_NODE`, and `CANCELLED_AFTER_ACTIVE_NODE`; it must never claim an
already completed node was cancelled.

**HAR-DAG-008 (MUST):** A pipeline result must retain every node result even when
the pipeline aborts or halts.

**HAR-DAG-009 (SHOULD):** Node subprocess output should stream to a bounded log
sink rather than accumulate unbounded bytes in memory.

### 5.3 Screening provenance gate

**HAR-SCR-001 (MUST):** Batch preparation must compute a `screening_run_id` from:

- protocol canonical fingerprint;
- verified-corpus canonical fingerprint;
- screening schema version;
- batch size and ordering policy;
- required screener count and reconciliation policy.

**HAR-SCR-002 (MUST):** Every batch and decision file must include the same
`screening_run_id`, batch number, batch content fingerprint, and schema version.

**HAR-SCR-003 (MUST):** Collection must reject missing, duplicate, extra, stale,
or fingerprint-mismatched decisions. Rejection must not overwrite a prior valid
included corpus.

**HAR-SCR-004 (MUST):** `included.json`, `excluded.json`, conflicts, and PRISMA
reports must record the `screening_run_id` and upstream fingerprints.

**HAR-SCR-005 (MUST):** The fixed orchestrator may proceed past screening only
when the included artifact's `screening_run_id` matches the newly prepared
screening run. Mere file existence must never satisfy the gate.

**HAR-SCR-006 (MUST):** `force` preparation must archive or invalidate old batch,
decision, and collected-output state in a recoverable way. It must not silently
mix generations.

**HAR-SCR-007 (SHOULD):** Existing unversioned screening artifacts should be
recognized as `LEGACY_UNVERIFIED` and require explicit migration or re-screening.

### 5.4 Fixed orchestrator fidelity

**HAR-ORC-001 (MUST):** External clients must be closed using `try/finally` or
async context managers on success, failure, cancellation, and timeout.

**HAR-ORC-002 (MUST):** The orchestrator must pass corpus identity and per-study
identity separately when indexing. It must never assign one workspace identifier
as every paper's study identity.

**HAR-ORC-003 (MUST):** Abstract-only fallback artifacts must retain an explicit
`content_status: abstract_only` and must not be counted as successfully extracted
full text.

**HAR-ORC-004 (MUST):** Extraction, index, graph, matrix, and synthesis stage
results must preserve structured success, partial, failed, skipped, and pending
states plus reason codes.

**HAR-ORC-005 (MUST):** The orchestrator must not catch a toolkit programming
fault and present it as a domain-negative result.

**HAR-ORC-006 (SHOULD):** Once DAG parity is proven, the fixed workflow should be
expressed through the same typed execution primitives rather than a second state
machine. Migration may be incremental.

### 5.5 Audit and workspace state

**HAR-AUD-001 (MUST):** All harness surfaces must call one canonical audit API.
Direct ad hoc journal appends must be removed or delegated to that API.

**HAR-AUD-002 (MUST):** Event IDs must use collision-resistant stable generation
such as UUIDv7/ULID or the repository's canonical event generator; Python
`hash()` must not participate.

**HAR-AUD-003 (MUST):** Event status must reflect actual outcome:
`SUCCESS`, `PARTIAL`, `FAILED`, `SKIPPED`, `WAITING_FOR_DECISION`, or `CANCELLED`.

**HAR-AUD-004 (MUST):** Audit append must be concurrency-safe within supported
local execution modes. A failed append must be reported and must not return a
fabricated event ID.

**HAR-AUD-005 (MUST):** Each event must contain schema version, run ID, action,
tool/kit version, resolved parameters with secrets removed, input and output
artifact references/fingerprints, metrics, timestamps, and reason codes.

**HAR-AUD-006 (MUST):** A successful significant mutation must refresh
`project.json` and `INDEX.md` through the canonical workspace manager.

**HAR-AUD-007 (MUST):** State derivation must distinguish file counts from
validated stage completion. A nonempty synthesis file or PDF count alone is not
proof a phase completed.

### 5.6 Console security and persistence

**HAR-CON-001 (MUST):** Default binding remains loopback-only. Non-loopback
binding must display a warning and require an explicit opt-in flag.

**HAR-CON-002 (MUST):** Request-provided workspace overrides must resolve within
the configured workspace or an explicitly allowed workspace root.

**HAR-CON-003 (MUST):** Saved pipeline IDs must be validated as safe identifiers;
path traversal or separator characters must be rejected.

**HAR-CON-004 (MUST):** Job metadata required for recovery must persist to disk.
After restart, incomplete jobs must appear as `INTERRUPTED`, not disappear.

**HAR-CON-005 (MUST):** SSE subscriber queues must be bounded and slow consumers
must not cause unbounded memory growth.

**HAR-CON-006 (SHOULD):** Arbitrary custom pipeline execution should be disabled
when bound outside loopback unless an authentication/authorization layer exists.

## 6. Data contracts

### 6.1 Node run manifest

Each completed node writes a manifest under
`.harness-console/runs/<pipeline-run-id>/<node-id>.json`:

```json
{
  "schema_version": "1.0.0",
  "pipeline_run_id": "run-...",
  "node_id": "n1_discovery",
  "node_fingerprint": "sha256:...",
  "resolved_argv": ["uv", "run", "scholar-search", "search", "..."],
  "tool_versions": {"scholar-search-kit": "commit-or-version"},
  "inputs": [{"path": "protocol.json", "sha256": "..."}],
  "outputs": [{"path": "literature/candidates.json", "sha256": "..."}],
  "state": "SUCCESS",
  "started_at": "...",
  "finished_at": "...",
  "reason_code": null
}
```

### 6.2 Screening manifest

`literature/screening/manifest.json` must include the run identity, upstream
fingerprints, ordered batch roster, and decision coverage. Collection output must
copy its immutable provenance fields.

## 7. Migration and compatibility

1. Introduce `PipelineSpec.schema_version = "1.0.0"`; continue reading `0.1.0`
   through a pure migration function.
2. Migrate known built-ins automatically to typed arguments.
3. Mark saved legacy specs containing generic `args` as unverified until migrated.
4. Do not silently reinterpret ambiguous boolean or positional arguments.
5. Preserve legacy screening outputs, but move them under a timestamped legacy
   archive when a new screening generation starts.
6. `status` and `doctor` must surface legacy/unverified state and the action needed.

## 8. Implementation plan

### P0

1. Define typed command/argument schema and migrate all five built-ins.
2. Add executable CLI-contract validation and built-in end-to-end dry executions.
3. Implement screening run fingerprints and reject stale `included.json`.
4. Fix unknown-node validation crash.
5. Coordinate RAG canonical study identity at the orchestrator boundary.

### P1

6. Replace file-existence idempotency with node-run manifests.
7. Consolidate audit logging and state synchronization.
8. Add resource lifecycle protection for search, verification, graph, and RAG.
9. Persist recoverable job state and structured halt/cancel outcomes.
10. Harden workspace/spec path validation and bounded event streams.

### P2

11. Unify fixed and configurable pipeline state primitives.
12. Add migration tooling for legacy specs and screening artifacts.
13. Refresh architecture, console, CLI, and operational documentation.

## 9. Test matrix

| Test ID | Scenario | Expected result |
|---|---|---|
| HAR-T001 | Validate every built-in against installed CLI registry | Zero unknown commands/options/argument-shape errors |
| HAR-T002 | Execute built-ins with hermetic fake providers | Commands parse; declared outputs validated |
| HAR-T003 | Edge references unknown source | Structured validation error; no exception |
| HAR-T004 | Two independent zero-indegree nodes | Stable deterministic order across runs/platforms |
| HAR-T005 | Existing output with changed input fingerprint | Node reruns |
| HAR-T006 | Existing output with matching successful manifest | Node skips with provenance |
| HAR-T007 | Zero exit but missing output | Node fails with `OUTPUT_MISSING` |
| HAR-T008 | Fresh batches plus stale included artifact | Pipeline returns `WAITING_FOR_DECISION` |
| HAR-T009 | Decision file has wrong batch fingerprint | Collection rejects without overwriting prior corpus |
| HAR-T010 | Force prepare over old decisions | Old generation archived; no mixed state |
| HAR-T011 | Search raises before close | Client close asserted |
| HAR-T012 | Graph build raises | Graph client close asserted |
| HAR-T013 | Audit append fails | Mutation reports audit failure; no fake event ID |
| HAR-T014 | Two simultaneous audit writers | Valid JSONL with no lost/interleaved records |
| HAR-T015 | Console workspace override escapes root | HTTP 400/403; no command started |
| HAR-T016 | Restart with active job record | Job restored as `INTERRUPTED` |
| HAR-T017 | Multiple papers indexed | Distinct `study_id` values preserved |
| HAR-T018 | Abstract-only fallback | Not counted as full-text extraction |
| HAR-T019 | Parallel pytest workers | Unique base-temp roots; no cleanup collision |

## 10. Definition of done

- All `HAR-*` MUST requirements have implementation and regression-test links.
- Every built-in PipelineSpec passes schema, semantic, CLI-contract, and hermetic
  execution tests.
- A stale screening generation cannot unlock downstream stages.
- Two papers in one workspace remain two studies through synthesis and Phase 4.
- No pipeline stage skips solely because a declared output file exists.
- All external clients close under injected failures.
- Audit/state behavior is identical across CLI, console, fixed orchestrator, and
  PipelineExecutor.
- Legacy specs/workspaces receive an explicit migration or refusal message.
- Harness suite passes serially and under supported parallel test execution.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Typed command schema makes custom pipelines harder | Retain explicit unverified custom-command mode |
| Fingerprinting large artifacts is costly | Stream SHA-256; cache by size/mtime only as an optimization, never identity |
| Existing workspaces lack manifests | Provide read-only diagnosis and explicit migration/re-screen workflow |
| Audit consolidation causes broad changes | Introduce adapter first, then migrate callers incrementally |
| Cross-repo CLI changes invalidate registry | Generate parity fixtures and gate `plugins.json` pin bumps |

## 12. Documentation updates

- Update `docs/architecture/phase_5` to describe typed commands and runtime states.
- Update console help to distinguish schema dry-run from executable validation;
  after remediation only the latter may be called “valid.”
- Document screening generation fingerprints and legacy migration.
- Document audit outcome states and node-run manifests.
- Update `docs/kits_surface_matrix.md` only after live behavior and tests land.

