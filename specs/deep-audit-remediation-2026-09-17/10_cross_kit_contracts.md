# Nexus Scholar Cross-Kit Contracts Specification

**Status:** Proposed / normative integration baseline  
**Date:** 2026-09-17  
**Applies to:** harness plus all eight `scholar-*-kit` packages  
**Compatibility epoch:** Contract v1

## 1. Purpose and architecture

The suite currently composes independently versioned packages through Python APIs, CLIs, MCP tools, and file artifacts. The surface matrix records schema and parity drift, including divergent claims shapes and prose/JSON MCP results (`docs/kits_surface_matrix.md:91-101,296-310`), CWD-sensitive historical defaults (`kits_surface_matrix.md:42-49`), and dependency edges including an undeclared verify-to-agent runtime edge (`kits_surface_matrix.md:348-358`). This specification makes those integration boundaries explicit.

Domain kits own algorithms. The harness owns phase orchestration and workspace state. The agent kit adapts capabilities to MCP. Files are durable contracts, not incidental serialization.

## 2. Goals and non-goals

Goals: stable identity, versioned artifacts, reproducible provenance, explicit uncertainty, transactional state, safe paths, resource cleanup, and semantic parity across API/CLI/MCP.

Non-goals: one physical package, one universal internal model, silent compatibility guessing, or claims of scientific validity based only on successful execution.

## 3. Canonical identifiers

- **XC-001 MUST** use semantically distinct, opaque stable identifier fields for protocol, run, corpus snapshot, study, source record, document, chunk, claim, evidence, screening decision, artifact, and audit event. Prefixes MUST come from a versioned registry. Existing stable `SCI-*` study identifiers remain valid during migration; new suggested prefixes include `PRT-`, `RUN-`, `COR-`, `STU-`, `REC-`, `DOC-`, `CHK-`, `CLM-`, `EV-`, `SCR-`, `ART-`, and `AUD-`. Loop identifiers proposed by `13_scientific_agent_loop_framework.md` (`LOOP-*`/`SCI-LOOP-*`) are not part of this registry until a future contract revision registers them explicitly.
- **XC-001a MUST** honor the canonical semantics: `workspace_id` identifies exactly one research workspace or corpus; `study_id` identifies exactly one paper/work; `document_id` identifies one full-text document; `chunk_id` identifies one evidence unit derived from one study. No consumer may use a workspace identifier as a study identifier. These definitions are authoritative here and are operationalized in `01_harness_spec.md` (HAR-ORC-002), `05_rag_kit_spec.md` (requirements 1–4), `06_graph_kit_spec.md` (requirements 2–4), and `07_protocol_kit_spec.md` (identity rule).
- **XC-002 MUST** store provider IDs separately under `external_ids` and MUST NOT use DOI/title/filename as the canonical ID.
- **XC-003 MUST** preserve canonical IDs through deduplication; merges SHALL emit alias and lineage maps.
- **XC-004 MUST** normalize DOI for comparison while preserving the original value. Normalized DOI is lowercase, trimmed, and stripped of `doi:` and DOI resolver prefixes.
- **XC-005 MUST** generate missing IDs deterministically from artifact type, workspace namespace, and canonical input hash; migrations MUST record the algorithm version.

## 4. Artifact envelope and schema versioning

Every JSON artifact MUST have:

```json
{
  "schema_version": "1.0.0",
  "artifact_type": "claims_ledger",
  "artifact_id": "ART-...",
  "created_at": "RFC3339 UTC",
  "producer": {"package": "scholar-rag-kit", "version": "...", "commit": "..."},
  "workspace_id": "...",
  "run_id": "RUN-...",
  "protocol_fingerprint": "sha256:...",
  "corpus_fingerprint": "sha256:...",
  "inputs": [{"artifact_id": "ART-...", "sha256": "..."}],
  "data": {}
}
```

- **XC-006 MUST** use semantic schema versions independent of package versions.
- **XC-007 MUST** reject unknown major versions; unknown minor fields MUST be ignored and preserved when round-tripping where practical.
- **XC-008 MUST** validate artifacts before use and before commit.
- **XC-009 MUST** publish JSON Schema files and golden fixtures for every cross-kit artifact.
- **XC-010 MUST** provide explicit, tested migrations. Shape guessing is forbidden after legacy v0 adapters expire.
- **XC-011 MUST** canonicalize JSON before hashing: UTF-8, sorted object keys, normalized numbers, no insignificant whitespace. Array ordering is semantic unless a schema marks an array as a set and defines its sort key.

## 5. Structured operation outcome and errors

All API adapters, `--json` CLI modes, and MCP tools MUST return:

```json
{
  "contract_version": "1.0.0",
  "operation": "screen",
  "run_id": "RUN-...",
  "status": "SUCCESS|PARTIAL|ERROR|FAILED|SKIPPED|WAITING_FOR_DECISION|CANCELLED",
  "data": {},
  "artifacts": [{"artifact_id": "ART-...", "path": "literature/...", "sha256": "..."}],
  "warnings": [],
  "errors": [{"code": "...", "message": "...", "retryable": false, "details": {}}],
  "provenance": {}
}
```

- **XC-012 MUST** use stable error codes; baseline codes include `VALIDATION_ERROR`, `NOT_FOUND`, `PATH_OUTSIDE_WORKSPACE`, `SCHEMA_VERSION_UNSUPPORTED`, `PROTOCOL_FINGERPRINT_MISMATCH`, `CORPUS_FINGERPRINT_MISMATCH`, `DEPENDENCY_ERROR`, `NETWORK_ERROR`, `RATE_LIMITED`, `CONFLICT`, `IDEMPOTENCY_CONFLICT`, `ATOMIC_COMMIT_FAILED`, and `INTERNAL_ERROR`.
- **XC-012a** `ERROR` and `FAILED` are aliases for the same operation-level hard-failure state: harness and kit envelopes MAY emit either spelling, but consumers MUST treat them identically. `SKIPPED`, `WAITING_FOR_DECISION`, and `CANCELLED` are first-class terminal states (see `01_harness_spec.md` HAR-AUD-003 and `11_validation_and_test_plan.md` §4.8); they MUST NOT be collapsed into `PARTIAL` or `ERROR`.
- **XC-013 MUST NOT** encode failure through prose prefixes, empty successful artifacts, sentinel counts, or exit code alone.
- **XC-014 MUST** mark degraded/fallback results `PARTIAL`; warnings do not substitute for status.
- **XC-015 MUST** redact secrets and bound diagnostic payload sizes.

## 6. Provenance and audit semantics

- **XC-016 MUST** record producer version/commit, normalized parameters, input/output hashes, protocol/corpus fingerprints, method/model/provider identifiers, start/end time, fallback decisions, and migration history.
- **XC-017 MUST** append exactly one canonical audit event after a successful artifact commit. Failed attempts MAY append a failure event but MUST NOT claim artifact publication.
- **XC-018 MUST** use an idempotency key composed from operation, canonical inputs, configuration, and target schema. Exact retries SHALL not duplicate artifacts/events.
- **XC-019 MUST** preserve negative, excluded, unresolved, and failed results; omission is not an audit strategy.
- **XC-020 MUST** link every derived artifact to all direct parent artifacts.

## 7. Atomicity and lifecycle

- **XC-021 MUST** stage writes inside the target filesystem, validate all files/hashes, atomically promote, then update project/index state and audit ledger.
- **XC-022 MUST** never leave canonical aliases pointing to partial sets. Multi-file outputs require a run manifest and one commit boundary.
- **XC-023 MUST** use explicit overwrite/idempotency behavior; silent in-place mutation is forbidden for public commands.
- **XC-024 MUST** close network clients, file handles, databases, browser/process resources, and temporary directories on every path, including cancellation.
- **XC-025 SHOULD** expose async context managers for networked services and bounded concurrency controls.

## 8. Path anchoring and security

- **XC-026 MUST** resolve workspace-relative paths against an explicit canonical workspace root, never process CWD.
- **XC-027 MUST** reject traversal and symlink escapes after real-path resolution.
- **XC-028 MUST** mark external read-only inputs explicitly; outputs MUST remain within the workspace unless the caller gives an absolute permitted destination.
- **XC-029 MUST** serialize durable artifact paths as workspace-relative POSIX paths for portability.

## 9. CLI, API, and MCP parity

- **XC-030 MUST** route all surfaces through the same public domain service and schemas.
- **XC-031 MUST** maintain a capability registry with operation, parameters, defaults, side effects, schemas, and unsupported differences.
- **XC-032 MUST** prove semantic parity with shared golden fixtures; transport-only differences are allowed.
- **XC-033 MUST** expose warnings and item-level results on every surface.
- **XC-034 MUST** keep human output separate from JSON output; MCP always uses JSON envelopes.
- **XC-035 MUST** declare every direct runtime import. Editable monorepo availability does not satisfy packaging.

## 10. Screening fingerprint gate

- **XC-036 MUST** bind a prepared screening batch to `protocol_fingerprint`, `corpus_fingerprint`, criteria-renderer version, dedup configuration, and preparation run.
- **XC-037 MUST** verify those bindings before decisions, reconciliation, collection, or downstream Phase-4 work.
- **XC-038 MUST** fail closed on mismatch. Regeneration is a new run, never an in-place relabel.
- **XC-039 MUST** preserve screener identity, method (`HUMAN`, `LLM`, `HEURISTIC`), model/prompt version where applicable, timestamp, decision, reason, and conflict/adjudication lineage.
- **XC-040 MUST NOT** silently substitute one screening method for another.

## 11. Canonical claim and evidence vocabulary

A claim ledger item MUST contain `claim_id`, `claim_text`, `claim_kind`, `study_ids`, `evidence_ids`, `citation_tokens`, `generation_method`, and optional `rq_ids`. Evidence MUST contain `evidence_id`, `study_id`, `document_id`, `locator`, `quote`, `extraction_method`, and source hash.

- **XC-041 MUST** distinguish these orthogonal axes:
  - retrieval: `SOURCE_AVAILABLE|SOURCE_UNAVAILABLE`;
  - lexical support: `SUPPORTED_VERBATIM|PARTIAL_MATCH|NOT_FOUND|NOT_CHECKED`;
  - entailment: `ENTAILED|CONTRADICTED|UNCERTAIN|NOT_ASSESSED`;
  - trust checks: `CLEAR|FLAGGED|UNRESOLVED|NOT_APPLICABLE|NOT_CHECKED`.
- **XC-042 MUST NOT** use `VERIFIED` without an axis qualifier.
- **XC-043 MUST NOT** infer entailment from lexical overlap or trustworthiness from absence of a flag.
- **XC-044 MUST** attach thresholds, algorithm versions, and evidence locators to automated judgments.
- **XC-045 MUST** retain per-claim results when producing aggregates.
- **XC-045a** The canonical evidence knowledge graph.
  - **Citation token grammar:** `[rag:v2:<workspace_id>:<study_id>:<chunk_id>]` (registered per `05_rag_kit_spec.md` requirement 4). Parsers MUST validate every component; tokens with a different version tag MUST NOT be accepted by v1 parsers without a registered migration.
  - **Semantic-similarity axis:** vector cosine results are named `semantic_similarity_score` and labeled, e.g. `HIGH_SIMILARITY`; they MUST NOT be emitted as `VERIFIED` or `ENTAILED` (registered per `05_rag_kit_spec.md` requirement 5).

## 12. Dependency and compatibility governance

- **XC-046 MUST** keep the canonical kit repository, vendored `tools/<kit>` snapshot, plugin manifest full-SHA pin, and generated distribution pins synchronized for every kit change.
- **XC-047 MUST** run a clean-wheel dependency audit and entrypoint smoke test for each kit.
- **XC-048 MUST** document deprecations for at least one minor release and provide fixtures for every supported migration.
- **XC-049 SHOULD** enforce schema and dependency graphs in CI rather than prose alone.

## 13. Prioritized implementation

### P0

1. Publish shared envelope, error, ID, claim/evidence, screening, and run-manifest schemas.
2. Enforce declared dependencies and clean-install smoke tests.
3. Add protocol/corpus fingerprint gates.
4. Replace prose errors and silent fallbacks in MCP.
5. Introduce transactional artifact commits and canonical audit ordering.

### P1

1. Add capability registry and cross-surface golden parity suite.
2. Add ID/lineage migration for legacy workspaces.
3. Normalize uncertainty/claim vocabulary and Phase-4 outputs.
4. Add resource lifecycle and cancellation conformance tests.

### P2

1. Generate reference docs from schemas/registry.
2. Add compatibility test corpus across supported schema minors.
3. Add resumable/idempotent execution for expensive operations.

## 14. Failure-focused conformance matrix

| Scenario | Required behavior |
|---|---|
| Unknown artifact major version | reject with `SCHEMA_VERSION_UNSUPPORTED` |
| Reordered set-like field | same fingerprint after canonical sort |
| Reordered semantic list | different fingerprint |
| Stale protocol/corpus | fail closed before writes |
| Undeclared dependency in clean wheel | CI failure |
| MCP/API/CLI same fixture | equivalent canonical result |
| Output path symlink escape | `PATH_OUTSIDE_WORKSPACE` |
| Crash between staged files | previous canonical set intact |
| Crash after promotion before audit | recovery detects and appends/reconciles exactly once |
| Provider timeout | `PARTIAL`/`ERROR`, never reassuring scientific state |
| Cancellation | resources closed, staging recoverable/cleaned |
| Legacy ID-less input | deterministic migrated IDs plus provenance |
| Lexical match without entailment | lexical axis set; entailment remains `NOT_ASSESSED` |
| Silent method fallback attempted | rejected unless explicitly authorized |

## 15. Definition of done and documentation

- JSON Schemas, typed reference models, golden fixtures, and migration fixtures exist for every cross-kit artifact.
- Every kit passes schema, fingerprint, path, atomicity, lifecycle, dependency, and parity conformance tests.
- The full suite passes on Windows, Linux, macOS, and supported Python versions.
- No canonical artifact lacks producer, run, fingerprints, hashes, lineage, or schema version.
- No tool silently degrades method or converts infrastructure failure into a scientific conclusion.
- Kit repositories, vendored snapshots, and pins are synchronized.

Update `docs/kits_surface_matrix.md`, architecture diagrams, workspace layout, audit-event reference, CLI/API/MCP references, schema catalog, migration guide, contribution checklist, and release notes. CI MUST verify generated documentation and examples against executable schemas.
