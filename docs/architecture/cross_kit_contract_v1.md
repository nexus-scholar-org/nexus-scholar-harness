# Cross-Kit Contract v1 Architecture Decision

**Status:** Accepted for WP-00 implementation
**Decision date:** 2026-09-18
**Normative source:** `specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md`
**Implementation:** `src/scholar_harness/contracts/`

## Context

The harness composes eight independently versioned kits across Python, CLI, MCP,
and file boundaries. Existing artifacts do not share one enforceable definition
of identity, versioning, partial failure, provenance, or screening generation.
Downstream remediation cannot safely proceed while those meanings remain
implicit.

This decision freezes the WP-00 integration baseline. It does not migrate kit
producers or legacy workspaces; those remain separate work packages.

## Decisions

### Identity

- `workspace_id` identifies one research workspace/corpus namespace.
- `study_id` identifies one scholarly work.
- `document_id` identifies one acquired full-text representation of a study.
- `chunk_id` identifies one evidence unit derived from one document/study.
- Provider identifiers are aliases in `external_ids`, never canonical IDs.
- New IDs use the registry bundled as
  `contracts/schemas/v1/identifier-registry.json`; existing `SCI-*` study IDs
  and `EVT-*` audit IDs remain registered legacy forms.
- Missing IDs are deterministically minted from semantic kind, workspace
  namespace, algorithm version, and canonical input.

### Artifact and operation contracts

- JSON artifacts use `ArtifactEnvelope` v1 and carry producer, run,
  protocol/corpus fingerprints, direct inputs, and typed data.
- API adapters, JSON CLI modes, and MCP adapters converge on
  `OperationOutcome` v1.
- `ERROR` and `FAILED` are equivalent hard-failure states. `PARTIAL`, `SKIPPED`,
  `WAITING_FOR_DECISION`, and `CANCELLED` remain distinct.
- Unknown v1 minor fields are preserved by reference models. Unknown major
  versions are rejected.
- Durable artifact paths are workspace-relative POSIX paths.

### Fingerprints and normalization

- General contract fingerprints use UTF-8 canonical JSON with sorted object
  keys, normalized integral numbers, and semantic array order.
- Set-like arrays are sorted only when the caller explicitly registers their
  JSON pointer.
- Protocol-kit's existing protocol serializer remains authoritative for
  protocol fingerprints; it is not silently replaced by the general serializer.
- DOI comparison removes `doi:`/resolver prefixes, trims, and lowercases while
  preserving the source value separately.

### Claims and trust

- Retrieval availability, lexical support, entailment, and trust are orthogonal
  axes. Semantic similarity is a score, never an entailment verdict.
- Retractions and expressions of concern block default trust. Corrections and
  addenda are visible flags but do not block by event type alone; an explicit
  policy/rule may escalate them when they invalidate relevant evidence.

### Screening

- A screening generation binds protocol fingerprint, corpus fingerprint,
  criteria-renderer version, dedup-configuration hash, and preparation run.
- Batches and decisions repeat the same binding. Mismatch is a closed gate, not
  a warning or implicit regeneration.
- Method provenance and screener identity are required. Silent LLM-to-heuristic
  substitution is not permitted.

### Discovery mode

- Best-effort is the compatibility default: successful providers are preserved,
  but any provider failure yields `PARTIAL` plus item/provider diagnostics.
- Strict mode is opt-in and converts any required-provider failure into a hard
  failure after resources are closed. Neither mode may represent provider
  failure as an unqualified empty success.

### PipelineSpec v1 policy

- Built-in nodes use typed argument kinds and a capability registry.
- Arbitrary shell command text is disabled by default. A custom command requires
  explicit workspace policy, an executable allowlist, and structured arguments;
  shell interpolation is never the implicit execution model.
- This decision freezes policy only; WP-04 owns its implementation/migration.

### Legacy compatibility

- Unversioned artifacts are legacy v0 and may be diagnosed/read through explicit
  adapters during the compatibility window.
- Writers emit only current schemas. Legacy inputs are never rewritten in place.
- Artifacts whose lineage cannot be reconstructed remain
  `LEGACY_UNVERIFIED`.
- Screening artifacts without matching protocol/corpus generations require
  re-screening before downstream execution.
- The compatibility adapter remains supported for one minor release after the
  corresponding v1 writer ships, followed by a documented deprecation cycle.

## Published contract assets

The generated catalog in `src/scholar_harness/contracts/schemas/v1/` contains:

- artifact envelope;
- operation outcome and structured error;
- corpus snapshot and normalized identity graph;
- claim/evidence ledger;
- document manifest and extraction usability state;
- screening batch and decision artifacts;
- run manifest;
- identifier registry.

`scripts/generate_contract_schemas.py --check` is the drift gate. Golden payloads
live under `tests/fixtures/contracts/v1/` and are parsed by the same typed models
used to generate the schemas.

The two-study closed-chain fixture is additionally generated by
`scripts/generate_two_study_contract_fixture.py`. Its parent hashes and corpus
fingerprint are derived, not illustrative placeholders. The
`validate_artifact_chain` reference validator checks graph closure, parent
hashes, shared execution fingerprints, screening bindings, and study/document/
claim identity continuity.

## Consequences

- Toolkit adapters have one stable contract target, but no kit is considered
  migrated merely because the reference package exists.
- The harness now directly declares Pydantic because it imports Pydantic models.
- The repository-wide fixed pytest base directory is removed. Pytest-managed
  per-process temporary roots are required for parallel-safe contract tests.
- Contract changes require a schema-version decision, regenerated catalog,
  updated golden fixtures, and conformance tests.

## Deferred implementation

WP-01 and later work packages own producer/consumer adoption, migrations,
transactional commits, capability parity, and kit-repository synchronization.
No vendored toolkit source is changed by this decision.
