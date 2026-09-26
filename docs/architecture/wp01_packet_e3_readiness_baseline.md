# WP01-E3 Readiness Baseline: Stable Chunks and Index Lineage

**Status:** READY FOR HANDOFF AUTHORING; implementation is not authorized by this document

**Date:** 2026-09-26

**Owner:** Nexus Scholar Harness maintainers

**Canonical starting point:** harness `f9aa0b64165983b00d502f988e9af0a303eb33e0`

**Pinned RAG kit:** `c89b68f0d35173082a03b8c6b228e84381271185`

## 1. Purpose

This document freezes the observed starting state and the decisions that the
WP01-E3 implementation handoff must encode. It exists so a smaller coding agent
does not invent a chunk contract, weaken Contract v1, or mistake a successful
Chroma upsert for a current, lineage-bound evidence index.

E3 begins only after E2. E2 accepts extracted text into a
`document_manifest`; E3 must derive stable chunks and a reproducible index from
that accepted extraction lineage. E4 will then attack the completed E1-E3 chain
with stale-input mutations.

This is a preparation artifact, not the E3 implementation specification. The
implementation packet must still provide numbered acceptance criteria, a
complete negative-test ledger, exact repository sequencing, and executable
gates.

## 2. Normative facts that E3 must not reinterpret

1. Contract v1 is frozen. Its registered artifact models are
   `corpus_snapshot`, `screening_batch`, `screening_decisions`,
   `document_manifest`, `claims_ledger`, and `run_manifest`.
2. Contract v1 does **not** define or accept a `chunk_manifest` or
   `index_manifest` artifact type. The frozen parent map binds
   `claims_ledger` directly to `document_manifest`.
3. `CHK-*` is nevertheless a registered, semantically distinct identifier.
   A chunk identifies one evidence unit derived from one study; it is not a
   workspace, study, document, filename, section number, or array position.
4. The registered citation grammar is
   `[rag:v2:<workspace_id>:<study_id>:<chunk_id>]` and validates all three
   identifiers.
5. E3 may not edit Contract v1 models, schemas, identifier registry, golden
   fixtures, baseline fingerprints, or the Contract v1 parent map. Such a
   change requires a separate architecture/version decision.
6. The authoritative E3 input is the accepted E2 `document_manifest`, including
   exact artifact ID, canonical payload hash, workspace/protocol/corpus
   bindings, document ID, study ID, source hash, extraction path, and extraction
   method.

## 3. Observed RAG-kit baseline

At the pinned RAG-kit revision:

- `MarkdownChunker` resolves document identity through a fallback chain and
  generates `chk-<doc-slug>-<section-slug>-<position>`. Positional IDs can be
  reused for changed text and therefore do not prove content identity.
- `ScholarIndexer.index_markdown` performs only `collection.upsert(...)`.
  Re-indexing a shortened document does not delete obsolete chunks.
- `min_chunk_chars` is stored but does not affect chunking.
- directory indexing may infer `workspace_id` from a project title, but a
  document's own YAML frontmatter may override that inferred identity for that
  document's chunks.
- embedding provider configuration is held in process configuration, but no
  durable manifest binds provider/model, chunking configuration, input hashes,
  and the exact visible chunk set.
- journal discovery walks parent directories from a supplied path and silently
  suppresses write errors. It is not an explicit atomic publication boundary.
- API, CLI, and MCP expose materially different defaults and capabilities.
- the current surface matrix accurately calls `upsert` idempotent while warning
  that re-index is not rebuild/replacement.

These are baseline observations, not permission to preserve the behavior.

## 4. Ratified E3 architecture boundary

E3 will use a **kit-owned Index Manifest v1 sidecar**, not a new Contract v1
artifact type. This follows the E2 pattern: the kit produces a typed candidate
and the harness verifies its immutable Contract-v1 parent before treating the
index as current.

The sidecar is non-authoritative until the harness E3 acceptance adapter has:

1. loaded the parent through the existing Contract v1 registry;
2. verified the declared parent artifact ID and canonical hash;
3. verified workspace, protocol, and corpus bindings;
4. verified every indexed study/document is eligible in the parent;
5. recomputed the manifest and index fingerprints;
6. proved the live backend contains exactly the declared visible chunk set; and
7. atomically published the accepted E3 record and audit event.

The accepted E3 record is an adapter-owned registry/sidecar record. It must not
be presented as a Contract v1 artifact. A future cross-kit Contract v2 may add
an index artifact explicitly; E3 must not pre-empt that version decision.

## 5. Required Index Manifest v1 content

The handoff must define a closed typed schema containing at least:

- schema and algorithm versions;
- workspace ID, protocol fingerprint, and corpus fingerprint;
- exact accepted `document_manifest` artifact ID and canonical SHA-256;
- one entry per source document: study ID, document ID, extracted-text content
  hash, extraction method, and sorted chunk IDs;
- canonical chunking configuration, including every behavior-affecting option;
- embedding provider, model, model revision/dimension when knowable, and
  normalization/distance configuration;
- backend type, collection identity, and storage schema version without
  machine-specific absolute paths;
- sorted visible chunk inventory with each chunk's canonical content hash and
  locator metadata;
- counts for accepted documents, rejected documents, and visible chunks;
- deterministic `chunk_set_fingerprint`, `configuration_fingerprint`, and
  `index_fingerprint`;
- structured per-document failures and overall status;
- producer package/version/commit and run ID.

Secrets, timestamps, absolute paths, temporary names, process IDs, and backend
iteration order must not influence deterministic fingerprints.

## 6. Identity and fingerprint decisions

The implementation handoff must use these rules:

### 6.1 Chunk identity

`chunk_id` is derived from a canonical payload containing:

- workspace namespace;
- accepted parent artifact ID and hash;
- study ID and document ID;
- extracted-text content hash;
- chunker algorithm version and effective configuration fingerprint;
- normalized structural locator; and
- normalized chunk-text hash.

The ID must use the registered `CHK-` form. Filename, title, DOI, section slug,
or ordinal alone is forbidden. Identical input and effective configuration must
produce the same IDs. Any change to extracted text, locator, or behavior-
affecting chunk configuration must change the affected identity or make the old
manifest stale.

### 6.2 Index identity

The index fingerprint is computed over canonical manifest content excluding the
fingerprint field itself. It commits to the exact parent, effective chunker and
embedder configuration, backend schema, and sorted visible chunk inventory.
The implementation packet must provide golden canonical-JSON examples and
self-reference-safe checksum rules.

## 7. Replacement and atomicity semantics

Upsert-only behavior is insufficient. A document re-index is a replacement:

1. validate parent lineage and all configuration before backend mutation;
2. build the complete candidate chunk set in staging;
3. embed and verify the candidate set;
4. write a recoverable commit intent;
5. atomically switch visibility to the new complete set;
6. remove obsolete chunks belonging to the same canonical document; and
7. publish the manifest and audit event only after the visible set matches it.

On interruption, readers see either the old complete set or the new complete
set, never a mixture. Recovery must be deterministic and ownership-safe.
Failure must not publish an accepted record or success audit event. Identical
re-indexing must be a no-op/reuse result with byte-identical deterministic
manifest content.

Backend-specific mechanics may differ, but the public semantics and test
fixtures must be backend-neutral.

## 8. Mandatory failure classes for the E3 handoff

The numbered negative ledger must cover at least:

- missing, malformed, unsupported, unaccepted, cross-workspace, or hash-stale
  document-manifest parent;
- protocol/corpus fingerprint mismatch;
- document or study absent from the accepted parent;
- changed extracted bytes at an unchanged path;
- path escape, symlink escape, wrong file type, unreadable or empty extraction;
- duplicate/colliding chunk ID and cross-document identity collision;
- positional-ID reuse after changed text;
- changed chunker configuration with reuse of an old manifest;
- changed embedding provider/model/dimension with reuse of an old collection;
- backend metadata corruption, missing chunk, extra obsolete chunk, or count
  mismatch;
- shortened-document re-index leaving any old chunk retrievable;
- partial embedding failure, interrupted staging, interrupted visibility switch,
  and interrupted manifest/audit publication;
- concurrent same-document and different-document indexing;
- undeclared or ineffective configuration (`min_chunk_chars` must work and be
  tested, or be removed/deprecated);
- nondeterministic file/backend iteration order;
- API/CLI/MCP semantic or error-envelope divergence;
- attempt to label similarity as verification or entailment; and
- attempt to publish the kit sidecar as a Contract v1 artifact.

Every refusal must prove zero authoritative publication and preserve the last
known complete index.

## 9. Repository and stage ownership

The required sequence is:

1. **E3 handoff PR in the harness.** Specify models, canonicalization, complete
   acceptance/negative ledgers, fixtures, surfaces, and exact gates. No runtime
   implementation.
2. **Canonical `scholar-rag-kit` PR.** Implement the candidate service, typed
   sidecar, replacement protocol, CLI/API behavior, migrations/read-only legacy
   handling, and focused tests.
3. **Canonical `scholar-agent-kit` PR if MCP is supported.** It must call the
   shared service with semantic parity. If MCP is deliberately unsupported,
   declare and test a deterministic `UNSUPPORTED_CAPABILITY` boundary.
4. **Harness synchronization PR.** Vendor exact merged kit commits, bump full
   SHA pins, regenerate metapackage pins, add the acceptance adapter,
   conformance/golden/mutation tests, and update the surface matrix and skill
   mirrors.
5. **E3 completion report.** Record canonical merge SHAs and executable proof.
6. **E4 adversarial proof.** Mutate PDF bytes, extracted bytes, chunking config,
   embedding identity, manifest lineage, and live index contents end-to-end.

No pin may target an unmerged toolkit revision. Kit source, canonical repo,
vendored tree, and pin move together.

## 10. Explicit non-scope

E3 does not redesign retrieval scoring, synthesis, consensus, methodology
matrices, claim verification, risk of bias, or scientific agent loops. It may
remove misleading terminology only where the new indexing boundary would
otherwise emit a false contract. Those downstream scientific semantics remain
separate packets after E4.

E3 also does not migrate arbitrary historical Chroma stores in place. Legacy
stores must be detected and made read-only or migrated through an explicit
dry-run/commit workflow specified by the handoff.

## 11. Exit gate for preparation

The next agent may author the full E3 handoff only if it preserves every rule
above. Runtime coding must wait for that handoff to be independently reviewed
and merged. Any proposal to add `chunk_manifest` to Contract v1 is
`BLOCKED_CONTRACT_VERSION_DECISION`, not an implementation shortcut.
