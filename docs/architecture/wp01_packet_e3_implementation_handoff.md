# Packet E3 — Stable Chunks and Index Lineage Boundary

- **Status:** `SPECIFICATION` — this document authorizes **no** runtime change.
  Runtime coding waits until this handoff is independently reviewed and merged
  (readiness baseline §11, `docs/architecture/wp01_packet_e3_readiness_baseline.md:241-244`).
- **Architecture owner:** Harness Contract v1
- **Implementation owner:** canonical `nexus-scholar-org/scholar-rag-kit`
- **Declared MCP boundary owner:** canonical `nexus-scholar-org/scholar-agent-kit`
  (declaration/rejection adapter only)
- **Current RAG-kit pin:** `f108fa897147f4c837760c81b558d1b82a044fdf` (merge of canonical PR #12, `fix/e3-identity-limbs-through-chroma-store`; superseded pin `033191eff967abf19023b258539c9a1422c8747f` is pre-fix and is retained here only as that PR's base)
- **Current agent-kit pin:** `79ffe421dfea2a2b6e4c02fdff651e6d23ce9b92`
- **Governing readiness baseline:** `docs/architecture/wp01_packet_e3_readiness_baseline.md`
- **Normative requirement source:** `specs/deep-audit-remediation-2026-09-17/05_rag_kit_spec.md:54-74`
  (`RAG-001`…`RAG-021`), `specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md:134`
- **Citation convention:** every `path/to/file.py:NN` reference in this
  document is repo-relative and machine-resolvable. A bare `:NN` in the same
  table cell continues the file named earlier in that cell; it never names a
  different file. No citation relies on a bare basename.
- **Direct Contract v1 input:** the accepted E2 `DocumentManifestArtifact`
  (read-only; E3 never mutates, re-emits, or re-parents it)
- **Authored at:** harness `0a15bbb` (merge of PR #52, the readiness baseline)
- **Frozen Contract v1 change required:** **none** (§1.1)

## 1. Decision and scope

E3 turns *accepted E2 extraction lineage* into **stable chunk identities and a
reproducible evidence index**. It does so without letting a filename, a section
number, an array position, a project title, or a successful Chroma `upsert` stand
in for content identity, completeness, or currentness. The RAG kit produces a
typed, deterministic, **kit-owned Index Manifest v1 sidecar**; a bounded harness
adapter re-verifies the immutable Contract v1 parent, re-computes every
fingerprint, proves the live backend holds exactly the declared visible chunk
set, and only then records the accepted E3 record and the canonical audit event.

E2 is extraction; E3 is chunking and indexing. E2 deliberately stopped at
`DocumentManifestArtifact` because the frozen `DocumentRecord` is an
**extracted-content** record, not an evidence-unit record. E3 is the packet that
makes evidence-unit identity provable — and the packet that must not make it
*newer*, because Contract v1 has no index artifact to accept.

### 1.0 Status of this document and what it supersedes

1. This handoff **encodes** the readiness baseline; it does not re-open it. Where
   the baseline is explicit (`§4` seven-step acceptance, `§5` required manifest
   content, `§6` identity rules, `§7` replacement semantics, `§8` failure
   classes, `§9` repository order, `§10` non-scope), this document is the
   checkable form of that decision, never a softer restatement of it.
2. This handoff supersedes the **"Packet E — Downstream adapter stubs"** section
   of `docs/architecture/wp01_contract_adoption_handoff.md` (that section is at
   lines 116–132 of that document) **for chunking and indexing only**. That file
   is locked in the Contract v1 baseline and is intentionally **not** edited.
3. This handoff also supersedes, for the indexing boundary, the aspirational
   "Proposition 2.1/2.2/2.7" claims embedded in RAG-kit docstrings and module
   prose (`tools/scholar-rag-kit/src/scholar_rag/chunker.py:66-68`,
   `tools/scholar-rag-kit/src/scholar_rag/retriever.py:124-127`, `tools/scholar-rag-kit/src/scholar_rag/indexer.py:143`). Those claims are the baseline
   evidence in §1.4, not a specification.
4. `specs/deep-audit-remediation-2026-09-17/05_rag_kit_spec.md` remains the
   normative requirement source; §1.2 allocates rows to E3 and names the rows
   that stay with later packets. §1.2 never *weakens* a requirement — a
   deferred row is deferred, not deleted.
5. E1 (`docs/architecture/wp01_packet_e1_acquired_document_handoff.md`) and E2
   (`docs/architecture/wp01_packet_e2_extracted_text_handoff.md`) are unchanged
   and remain authoritative for acquisition and extraction.

### 1.1 Frozen-contract boundary (no schema change)

E3 requires **no** Contract v1 model, schema, generated-schema, golden-fixture,
baseline, identifier-registry, or parent-map change. Every fact E3 depends on
already exists and is quoted from the frozen baseline:

| Frozen fact | Location |
|---|---|
| The registered artifact types are exactly `claims_ledger`, `corpus_snapshot`, `document_manifest`, `run_manifest`, `screening_batch`, `screening_decisions` | `src/scholar_harness/contracts/acceptance.py:31-38` |
| The frozen parent map binds `claims_ledger` **directly** to `document_manifest`; there is no index parent and no index child | `src/scholar_harness/contracts/acceptance.py:40-45` (`:44`) |
| An unknown `artifact_type` is rejected with `UNSUPPORTED_ARTIFACT_TYPE` | `src/scholar_harness/contracts/acceptance.py:256-264` (code at `:263`) |
| A missing/registered-parent disagreement is rejected with `MISSING_PARENT_ARTIFACT` / `PARENT_HASH_MISMATCH`; a wrong required parent type with `REQUIRED_PARENT_TYPE_MISSING` | `src/scholar_harness/contracts/acceptance.py:325-345` (`:331`, `:341`), `:390-401` (`:399-401`) |
| `IdentifierKind.CHUNK` exists and its only registered prefix is `CHK-` | `src/scholar_harness/contracts/identifiers.py:19`, `:36` |
| Identifier validation is case-sensitive and requires a non-empty `[A-Za-z0-9][A-Za-z0-9._-]*` suffix | `src/scholar_harness/contracts/identifiers.py:44`, `:58-67` |
| The registered citation grammar is `^\[rag:v2:(ws):(study):(chunk)\]$` and all three components are validated | `src/scholar_harness/contracts/models.py:19-21`; registered at `specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md:134` |
| `OperationStatus` ∈ `SUCCESS, PARTIAL, ERROR, FAILED, SKIPPED, WAITING_FOR_DECISION, CANCELLED` | `src/scholar_harness/contracts/models.py:51-58` |
| `ErrorCode` ∈ `VALIDATION_ERROR, NOT_FOUND, PATH_OUTSIDE_WORKSPACE, SCHEMA_VERSION_UNSUPPORTED, PROTOCOL_FINGERPRINT_MISMATCH, CORPUS_FINGERPRINT_MISMATCH, DEPENDENCY_ERROR, NETWORK_ERROR, RATE_LIMITED, CONFLICT, IDEMPOTENCY_CONFLICT, ATOMIC_COMMIT_FAILED, INTERNAL_ERROR` | `src/scholar_harness/contracts/models.py:65-78` |
| `MethodProvenance` ∈ `HUMAN, DETERMINISTIC_RULE, HEURISTIC, LLM, EXTERNAL_PROVIDER, COMPOSED` | `src/scholar_harness/contracts/models.py:81-87` |
| `DocumentContentStatus` ∈ `VALID, PARTIAL, FAILED, NEEDS_OCR` | `src/scholar_harness/contracts/models.py:124-128` |
| `DocumentRecord` = `document_id`, `study_id`, `source_hash`, `content_status`, `extracted_path`, `extraction_method` — and nothing else | `src/scholar_harness/contracts/models.py:472-478` |
| `source_hash` must be `sha256:<64 lowercase hex>`; `extracted_path` must be a workspace-relative POSIX path | `src/scholar_harness/contracts/models.py:490-501`, `ArtifactReference.portable_workspace_path` (`src/scholar_harness/contracts/models.py:152-169`) |
| `VALID`/`PARTIAL` **require** `extracted_path`; `FAILED`/`NEEDS_OCR` do not | `src/scholar_harness/contracts/models.py:503-510` |
| `DocumentManifestData.documents` has `min_length=1` and unique `document_id` | `src/scholar_harness/contracts/models.py:513-521` |
| The envelope requires `schema_version` (1.x), `artifact_id` (`ART-`), `created_at` (UTC), `producer`, `workspace_id` (`WSP-`), `run_id` (`RUN-`), `protocol_fingerprint`, `corpus_fingerprint`, `data`; `inputs` defaults to `[]` | `src/scholar_harness/contracts/models.py:182-223` |
| Evidence may be grounded only in a `VALID`/`PARTIAL` document | `src/scholar_harness/contracts/chain.py:335-345` (`UNUSABLE_EVIDENCE_DOCUMENT`) |
| Canonical JSON, canonical fingerprint, and the deterministic-ID minting primitive already exist and are the ones E3 reuses | `src/scholar_harness/contracts/canonical.py:93-114` (`canonical_json_bytes`), `:117-125` (`canonical_fingerprint`), `:167-183` (`deterministic_id`) |

Consequences that follow and are **not** negotiable in this packet:

1. **`index_manifest` is not an `artifact_type`.** It is a kit sidecar type
   alongside E1's `pdf_acquisition_manifest` and E2's `pdf_extraction_manifest`.
   The frozen registries must keep rejecting it (`E3-NEG-038`).
2. **No chunk manifest is published into `artifacts/`.** The accepted E3 record
   is an adapter-owned registry/sidecar record, not a Contract v1 artifact
   (readiness baseline §4). A future cross-kit Contract v2 may add an index
   artifact; E3 must not pre-empt that decision
   (readiness baseline `:93-95`).
3. **`claims_ledger` keeps `document_manifest` as its only parent.** E3 does not
   insert an index artifact between them, and the chain gate must stay clean
   for `DocumentManifestArtifact` (`E3-NEG-038`, `E3-NEG-039`).
4. **`CHK-` is the only chunk-ID form.** A lower-case `chk-*` ID, a bare
   `chk-<n>` ordinal, or a DOI/section composite is a contract violation, not a
   stylistic variant (`E3-NEG-033`, §1.4 limb 7).
5. **`canonical_json_bytes`/`canonical_fingerprint`/`deterministic_id` are
   reused, not re-derived.** The RAG kit ships its own byte-equivalent
   primitive — exactly as the PDF kit does
   (`tools/scholar-pdf-kit/src/scholar_pdf/canonical.py:31-105`) — and a harness
   conformance test proves the two agree (`E3-NEG-047`).

### 1.2 Normative requirement allocation (RAG rows)

`specs/deep-audit-remediation-2026-09-17/05_rag_kit_spec.md:54-74` is normative. This table allocates rows; it does not
modify them. "E3" means E3 must ship the behavior **and** its tests in the
canonical RAG-kit PR (§12 step 2).

| Requirement | Owner | E3 scope and required evidence |
|---|---|---|
| **RAG-001** chunk identity triple and global uniqueness | **E3** | Every visible chunk carries non-empty `workspace_id`, `study_id`, `CHK-*`; uniqueness is enforced per study and per collection. Evidence: `E3-001`, `E3-NEG-030`, `E3-NEG-031`. |
| **RAG-002** aliases may resolve `study_id` but never replace it | **E3** | DOI/OpenAlex/filename/legacy `paper_id` may appear only in a declared alias map; persisted primary identity is the parent's `study_id`. Evidence: `E3-002`, `E3-NEG-029`. |
| **RAG-003** structured per-document error when identity is unresolvable | **E3** | Per-document rejection with a code, never a title/filename/DOI/`UNKNOWN` substitute. Evidence: `E3-002`, `E3-NEG-010`, `E3-NEG-011`. |
| **RAG-004** citation tokens encode the canonical triple and a version | **E3** (emission) | E3 emits `CHK-*` identities the registered grammar already requires and proves the emittable form matches `src/scholar_harness/contracts/models.py:19-21`. Token *emission* at query time belongs to the retrieval packet. Evidence: `E3-003`, `E3-NEG-034`. |
| **RAG-010** explicit `workspace_id`/embedding identity at the execution boundary | **E3** | No CWD-derived, project-title-derived, or invented identity; every execution-boundary identity is explicit or inherited from the recorded workspace manifest. Evidence: `E3-004`, `E3-NEG-012`, `E3-NEG-026`. |
| **RAG-012** atomic artifacts, machine-readable failure manifests, partial ≠ complete | **E3** | The Index Manifest v1 sidecar *is* the machine-readable failure record; a mixed batch is `PARTIAL`, never `SUCCESS`. Evidence: `E3-005`, `E3-006`, `E3-NEG-013`, `E3-NEG-042`. |
| **RAG-013** audit events record fingerprints, counts, rejected documents, embedding identity, configuration, artifact paths, no secrets | **E3** | `§4.1` and `§6.6` define the field set; the event is the harness's, not the kit's, and carries no secret, no absolute path, no timestamp-derived identity. Evidence: `E3-007`, `E3-NEG-037`. |
| **RAG-014** API, CLI, and MCP share one typed service layer and parity tests | **E3** | One request/result model behind all three surfaces, with an explicit declared-unsupported MCP limb (§9). Evidence: `E3-008`, `E3-NEG-040`. |
| **RAG-015** legacy collections are read-only until migrated | **E3** | `§7.6`: detection, read-only, dry-run migrator, manifest-before-commit. Evidence: `E3-009`, `E3-NEG-045`, `E3-NEG-046`. |
| **RAG-017** replacement semantics; identical re-index is idempotent | **E3** | `§7`: stage, commit-intent, visibility switch, obsolete removal, publish-after-match. Evidence: `E3-010`, `E3-NEG-032`, `E3-NEG-043`, `E3-NEG-044`. |
| **RAG-018** explicit audit/workspace path, never CWD discovery | **E3** | The journal is an explicit request field or the recorded workspace path; the current parent-walking discovery is removed from the authoritative path. Evidence: `E3-011`, `E3-NEG-025`. |
| **RAG-019** declared runtime imports, isolated install/import test | **E3** | Any dependency E3 puts on an authoritative path is declared in the kit and the metapackage, proven by a clean-wheel smoke. Evidence: `E3-012`, `E3-NEG-048`. |
| **RAG-020** `min_chunk_chars` must work as documented or be deprecated | **E3** | The dead option is either implemented and tested or removed with a deprecation warning; a stored-but-inert option fails the manifest validation. Evidence: `E3-013`, `E3-NEG-027`. |
| RAG-005, RAG-006 (similarity naming, `entailment_status` provenance) | **E3 (negative only)** | E3 removes any indexing surface that would emit a false contract and adds the mandatory refusal (`E3-NEG-036`). The similarity/label vocabulary redesign and any real verifier are **not** E3. |
| RAG-007, RAG-008, RAG-009, RAG-016, RAG-021 | **not E3** | Claim-level study retention, consensus de-duplication, hybrid score decomposition, `missing_reason`, and caller-model immutability are retrieval/synthesis/consensus/matrix concerns (readiness baseline `§10`). E3 must not silently change them, and its tests must not claim them. |

### 1.3 E2 boundary language E3 must honour verbatim

E2 allocated its own boundary and E3 inherits it unchanged:

1. **"No chunking, embedding, indexing, retrieval, or chunk IDs — that is E3"**
   (`docs/architecture/wp01_packet_e2_extracted_text_handoff.md:269`). E2
   therefore owns no chunk, embedder, collection, or `CHK-` behavior, and E3
   claims none of E2's engine/provenance behavior.
2. **"Chunk-level usefulness scoring is E3"** (E2 `:137`, allocating PDF-008) and
   **"Retrieval-engine selection for RAG is E3"** (E2 `:138`, allocating
   PDF-009). E3 owns the chunk-level threshold that decides whether an extracted
   document is indexable; E3 does not redesign extraction engines.
3. **E2's authoritative inputs are bound and closed**: the accepted
   `DocumentRecord` set, each `extracted_path` a workspace-relative POSIX path
   under the canonical root (`src/scholar_harness/contracts/models.py:152-169`, `:495-501`), and the
   `VALID`/`PARTIAL` requirement for a path (`:503-510`). E3 consumes exactly
   those fields and re-verifies them; it does not re-derive `document_id`,
   `study_id`, or `extraction_method`.
   `source_hash` is consumed **transitively**, not directly: it is a field of the
   parent's `DocumentRecord` and therefore reaches E3 only inside the parent's
   registered `artifact_checksum`, which E3 verifies as `parent_artifact_sha256`
   (`§5.1`). `source_hash` appears in no E3 sidecar field (`§4.2`) and in no
   chunk-identity canonical input (`§5.1`), and must not be added to either: E3
   binds lineage, not source content, and re-deriving `source_hash` would be
   re-deriving E2's identity.
4. **The E2 sidecar path is `literature/extraction/<run_id>/<EXT-…>.json`**
   (E2 `:740`) and the E1 sidecar path is
   `literature/acquisition/<run_id>/<ACQ-…>.json` (E2 `:741`). E3's own sidecar
   path is fixed in `§4.4` and must not collide with either.
5. **E2's E2-`APPROVE` precondition** (E2 `:1381-1386`): the extracted-text
   boundary is safe for E3 to consume only when identity is reused, lineage is
   verifiable, and status is truthful. E3 verifies those preconditions at
   runtime (`§6.1`) rather than assuming them, and an E3 run against a workspace
   that lacks an accepted E2 `document_manifest` is a refusal, not a default.
6. **E2's non-scope is inherited**: E3 does not re-litigate extraction
   usefulness thresholds, engine chains, frontmatter binding, or PDF provenance
   (`docs/architecture/wp01_packet_e2_extracted_text_handoff.md:267-289`).

### 1.4 Indexing behavior at the pinned revisions (pre-fix characterization)

Every row below was read at RAG-kit pin
`c89b68f0d35173082a03b8c6b228e84381271185` — the **superseded pre-fix** revision —
and, where marked *executed*, was run offline against that vendored tree. These are
observations, not permission to preserve the behavior (readiness baseline `:74`).

The shipped pin on this branch is `f108fa897147f4c837760c81b558d1b82a044fdf`
(`.agents/plugins/nexus-scholar/plugins.json`), so rows 1–3 describe code that is
**no longer at those line numbers**: at the shipped pin `chunker.py` mints `CHK-`
ids from the frozen canonical rule (`chunker.py:136`, `:616`). The lower-case
`chk-` spelling those rows describe survives only as classified legacy/degraded
state — `recovery.py:160-161` (`^chk-[0-9a-z]+$`, `^chk-\d+$`), the `chk-*`
legacy-identity detail at `recovery.py:946`, and the Chroma return-value
placeholder at `retriever.py:222`. The `CHK-` registry form is defined at
`canonical.py:65` and validated at `index_manifest.py:282`. Re-read a row's
location at the shipped pin before citing it as current behaviour.

| # | Observed fact | Location (at the superseded pin) | E3 consequence |
|---|---|---|---|
| 1 | Chunk IDs are `chk-<doc-slug>-<section-slug>-<NN>` — lower-case, and the trailing component is a **global running position** | `tools/scholar-rag-kit/src/scholar_rag/chunker.py:78`, called at `:216-218` (superseded; at the shipped pin the mint is `CHK-` at `chunker.py:136`/`:616`) | Not content identity: §5.1 mints `CHK-*` from a canonical payload. `E3-NEG-033`. |
| 2 | *executed:* `generate_deterministic_chunk_id("10.1016/j.jclinepi.2024.1","data",1)` returns `chk-1010-a11ef5-data-01`, and returns the **same string** after any change to the text | `tools/scholar-rag-kit/src/scholar_rag/chunker.py:64-78` (superseded); the caller passed the DOI or the filename stem (`tools/scholar-rag-kit/src/scholar_rag/indexer.py:248`) | This is the positional-reuse defect: identical identity, different content. `E3-NEG-028`, and it is the limb the `§5.1` rule fixes. |
| 3 | *executed:* the frozen registry rejects that id: `validate_identifier(IdentifierKind.CHUNK, "chk-1010-a11ef5-data-01")` → `ValueError: chunk_id must start with one of: CHK-` | `src/scholar_harness/contracts/identifiers.py:58-66` | The current surface cannot emit a contract-valid chunk identity. `E3-NEG-033`. |
| 4 | The only backend mutation in the whole kit is `collection.upsert(...)`; there is no delete/replace call anywhere | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:78` (sole mutation), `tools/scholar-rag-kit/src/scholar_rag/indexer.py:265-267` (only `count()`) | A shortened or revised document leaves obsolete chunks retrievable. `E3-NEG-032`. |
| 5 | `min_chunk_chars` is accepted and stored, and read nowhere else in the kit | `tools/scholar-rag-kit/src/scholar_rag/chunker.py:23`, `:27` (assignment only) | Stored-but-inert behaviour-affecting option. `E3-013`/`E3-NEG-027`. |
| 6 | Document identity resolves through `doc_id → workspace_id → paper_id → doi → filename → md5(markdown)[:8]`, i.e. a fallback chain ending in a *text hash prefix* | `tools/scholar-rag-kit/src/scholar_rag/chunker.py:153-161` | A document's own YAML frontmatter can override the identity used for its chunks. `E3-002`/`E3-NEG-010`. |
| 7 | Directory indexing passes `doc_id = base_meta.get("doi") or md_file.stem` | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:248` | A DOI or a filename is what currently binds a chunk to a document. `E3-NEG-029`. |
| 8 | `workspace_id` is inferred from `project.json`'s `project_id` **or** `title` when the caller omits it | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:199-204` | A workspace is not a study identity, and a title is not an identity. `E3-004`/`E3-NEG-012`. |
| 9 | The same `workspace_id` variable is reused as the per-document base metadata, so a document's own `workspace_id` frontmatter can diverge from the index-level value for its own chunks | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:217-220` with `tools/scholar-rag-kit/src/scholar_rag/chunker.py:156` | Cross-workspace chunk identity is currently expressible. `E3-NEG-024`. |
| 10 | Markdown files are discovered with an unsorted `glob("*.md")` and processed in that order | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:208`, `:213` | Backend/filesystem iteration order is observable; determinism must be established by sorting. `E3-NEG-028`. |
| 11 | Provider/model configuration lives only in process configuration; **no durable manifest** binds provider, model, chunking configuration, input hashes, or the visible chunk set | absence across `tools/scholar-rag-kit/src/scholar_rag/indexer.py:23-50`, `tools/scholar-rag-kit/src/scholar_rag/chunker.py:19-28`; readiness baseline `:65-67` | §4 introduces the sidecar that makes the index reproducible. `E3-005`/`E3-NEG-024`. |
| 12 | The only backend identity recorded anywhere is `{"hnsw:space": "cosine"}` written at collection creation | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:43-45` | Storage schema version and collection identity must be recorded. `E3-NEG-024`. |
| 13 | Journal discovery walks up to five parent directories from the data directory and **silently suppresses** write errors | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:129-140`, `:158-162`; the retriever repeats the walk (`tools/scholar-rag-kit/src/scholar_rag/retriever.py:133-143`) | Not an atomic publication boundary, and CWD-derived. `E3-011`/`E3-NEG-025`. |
| 14 | The audit event is `RAG_INDEX_BUILT` with counts and a `db_path`, and no fingerprints, no rejected documents, no embedding identity, no configuration | `tools/scholar-rag-kit/src/scholar_rag/indexer.py:142-157`; `docs/kits_surface_matrix.md:379` | Fails RAG-013. `§6.6` replaces the field set. `E3-007`. |
| 15 | *executed:* citation tokens are emitted as `[<ws>#<sec-slug>#<chunk>]`; the frozen grammar rejects that form and accepts `[rag:v2:<ws>:<study>:<chunk>]` | `tools/scholar-rag-kit/src/scholar_rag/retriever.py:122-131`; grammar at `src/scholar_harness/contracts/models.py:19-21` | The retrieval surface cannot emit a v1 citation token. `E3-003`/`E3-NEG-034`. |
| 16 | When the backend returns no ids, the retriever **fabricates** `chk-<index>` ordinals for returned results | `tools/scholar-rag-kit/src/scholar_rag/retriever.py:222` | Fabricated identity is a hard failure, not a fallback. `E3-NEG-033`. |
| 17 | Vector cosine is reported as `entailment_score` with a `VERIFIED` label at `>= 0.85` | `tools/scholar-rag-kit/src/scholar_rag/synthesis.py:112-148`; module docstring `:1` | Similarity is not entailment. `E3-NEG-036`; the vocabulary redesign is not E3 (§1.2). |
| 18 | API, CLI, and MCP expose materially different defaults: MCP hard-codes `db_path="./chroma_db"`, takes a directory only, and returns free-text success/failure strings | `tools/scholar-agent-kit/src/scholar_agent/server.py:774-799`; `docs/kits_surface_matrix.md:368-371` | No typed parity, and a divergence a client can silently act on. `E3-008`/`E3-NEG-040`. |
| 19 | The surface matrix already warns that `upsert` is idempotent while re-index is **not** rebuild/replacement | `docs/kits_surface_matrix.md:355-359` | The documentation is honest today; the behavior must change to match. `E3-010`. |

## 2. Scope and governing invariants

### 2.1 What E3 does

1. Defines the **Index Manifest v1** kit-owned sidecar: a closed, typed,
   deterministic, self-describing record of *which* chunks are visible, *from
   which* accepted parent, under *which* chunker and embedder configuration, in
   *which* backend collection (readiness baseline `§5`; model in `§4`).
2. Defines **chunk identity** as a deterministic function of the accepted parent,
   the study/document identities, the extracted-text content hash, the effective
   chunker configuration, the normalized structural locator, and the normalized
   chunk-text hash — minted with the registered `CHK-` form and the frozen
   `deterministic_id` primitive (`§5.1`).
3. Defines **index identity** as a self-reference-safe, order-independent
   fingerprint over exactly that content, plus the three baseline fingerprints
   (`chunk_set_fingerprint`, `configuration_fingerprint`, `index_fingerprint`)
   with a stage order that cannot cycle (`§5.2`).
4. Defines the **E3 acceptance chain**: seven ordered checks owned by a bounded
   harness adapter, ending in an all-or-nothing publication of the accepted E3
   record and the canonical audit event (readiness baseline `§4`; `§6`).
5. Defines **replacement semantics**: a re-index stages a complete candidate set,
   writes a recoverable commit intent, switches visibility atomically, removes
   the superseded chunks of the same canonical document, and publishes only
   after the live set matches the manifest (readiness baseline `§7`; `§7.3`).
6. Defines **legacy store handling**: detection, read-only default, and an
   explicit dry-run/commit migrator that writes its own manifest before
   committing (readiness baseline `§10`; `§7.6`).
7. Allocates the RAG rows in `§1.2` to a named owner with named tests, and
   records what E3 explicitly does **not** answer.
8. Specifies the typed API/CLI/MCP surface, the declared MCP boundary, the
   negative ledger, the acceptance map, the repository sequence, and the
   executable gates.

### 2.2 What E3 does **not** do

1. **No Contract v1 change.** No new `artifact_type`, no `chunk_manifest`, no new
   `DocumentRecord`/`EvidenceItem` field, no identifier-registry change, no
   parent-map change, no regenerated schema, fixture, or baseline
   (readiness baseline §2 items 2 and 5, and §11; §1.1).
2. **No retrieval, scoring, synthesis, consensus, or methodology-matrix
   redesign** (`readiness baseline §10`). E3 fixes the *emission* of chunk
   identity and the *currentness* of the index; it does not re-rank, re-verify,
   or re-synthesize. E3 removes false contract language where the new indexing
   boundary would otherwise emit it, and nothing more.
3. **No in-place migration of arbitrary historical stores.** Legacy stores are
   detected and made read-only or migrated through an explicit workflow
   (`readiness baseline §10`; `§7.6`).
4. **No authoring of scientific meaning.** E3 does not decide which chunks are
   relevant, which claims are supported, or which studies agree.
5. **No runtime change in this document.** §12 step 1 is a specification PR.
6. **No widening of the packet to absorb another packet's row.** A convenience
   never authorizes deferring a `RAG-0nn` row that E3 claims (§1.2), and E3
   never claims a row it did not close.

### 2.3 Governing invariants

These are stated once here and are referenced by the criteria in §3.

- **G-1 Parent-first.** Nothing is written to a backend before the accepted E2
  `document_manifest` is loaded through the frozen registry, its declared
  `artifact_id`/hash are verified, and its workspace/protocol/corpus bindings
  agree. Failure ⇒ zero authoritative publication.
- **G-2 Identity is content, not position.** No chunk identity may be derived
  from a filename, title, DOI, section slug, or ordinal alone. Two different
  contents never share a `CHK-`; the same content under the same parent and
  configuration always does.
- **G-3 Namespace honesty.** A workspace, a study, a document, and a chunk are
  four different things. None may stand in for another, and none may be derived
  from a project title, a directory name, or a `project.json` field.
- **G-4 Replacement, not accumulation.** A re-index publishes exactly the new
  complete set. Obsolete chunks of the same canonical document are removed, not
  left retrievable. An identical re-index is a no-op/reuse with byte-identical
  deterministic manifest content.
- **G-5 All-or-nothing publication.** The accepted E3 record and the canonical
  audit event are published together or not at all. Any failure before that
  point leaves the last known complete index visible and current.
- **G-6 Determinism is a property of the projection, not of the run.** File
  enumeration order, backend iteration order, timestamps, run IDs, temporary
  names, process IDs, absolute paths, and secrets do not influence any
  deterministic fingerprint (`readiness baseline §5` final paragraph; `§5.4`).
- **G-7 Truthful status.** A partial success is `PARTIAL`, an empty successful
  result is not a success, and a rejected document is visible with a code rather
  than dropped (`RAG-012`).
- **G-8 No fabricated contract.** The sidecar is not a Contract v1 artifact; a
  lower-case chunk ID, an off-grammar citation token, or a similarity labelled
  `VERIFIED`/`ENTAILED` is a refusal, not a value.
- **G-9 Kit/harness separation.** The canonical RAG kit never imports
  `scholar_harness`, never writes the Contract registry, and never claims its
  candidate was accepted. The harness adapter never re-implements kit internals;
  it calls the kit's typed service and verifies its declared candidate.
- **G-10 Honest evidence.** A green harness suite is not evidence that indexing
  works; the canonical kit suites are. E3 claims only what it can observe.

## 3. Acceptance criteria

Each criterion is checkable and maps to at least one `E3-POS-###`/`E3-NEG-###`
ID in `§10`. This document is a **specification**: it does not claim these tests
exist or pass.

- **E3-001 Chunk identity is canonical, `CHK-`-prefixed, and content-bound:**
  `chunk_id` equals the frozen `deterministic_id(IdentifierKind.CHUNK, …)`
  result over the `§5.1` canonical input; it validates against
  `src/scholar_harness/contracts/identifiers.py:36`; it is not derivable from filename, title, DOI, section
  slug, or ordinal; and two studies with identical text produce distinct chunk
  identities. Any change to the parent, the study/document identity, the
  extracted text, the locator, the chunk text, or the effective chunker
  configuration changes the affected identity or makes the old manifest stale.
  Every canonical input component is covered by a named limb in `§5.1`, including
  the normalized locator (`E3-NEG-007`, `E3-NEG-055`), the chunker algorithm version
  (`E3-NEG-056`), and the workspace namespace (`E3-NEG-053`).
  Evidence: `E3-NEG-001`…`E3-NEG-008`, `E3-NEG-028`, `E3-NEG-030`, `E3-NEG-031`,
  `E3-NEG-051`, `E3-NEG-053`, `E3-NEG-055`, `E3-NEG-056`.
- **E3-002 Study/document identity is reused, never re-derived:** every indexed
  document's `document_id`/`study_id` are byte-for-byte the accepted parent's
  `DocumentRecord` values; a document absent from the parent, or a `study_id`
  absent from the accepted corpus/screening lineage, is refused; a DOI,
  OpenAlex ID, filename, or legacy `paper_id` may resolve an alias but never
  replaces the persisted primary identity; a document's own frontmatter can
  never re-bind its own chunk identity. Evidence: `E3-NEG-009`, `E3-NEG-010`,
  `E3-NEG-011`, `E3-NEG-029`.
- **E3-003 Emittable identity matches the registered grammar:** the identity E3
  commits is sufficient to emit `[rag:v2:<workspace_id>:<study_id>:<chunk_id>]`
  as registered at `specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md:134` and enforced by
  `src/scholar_harness/contracts/models.py:19-21`; a token in any other form is refused, and no ordinal or
  fabricated `chk-<n>` identifier is ever emitted. Evidence: `E3-NEG-033`,
  `E3-NEG-034`.
- **E3-004 Execution-boundary identity is explicit:** `workspace_id`, run, parent
  artifact, backend, collection, and embedding identity are explicit request
  fields or inherited from the recorded workspace manifest; none is inferred
  from a process CWD, a project title, a `project.json` field, or a default
  model. Evidence: `E3-NEG-012`, `E3-NEG-026`, `E3-NEG-024`.
- **E3-005 The Index Manifest v1 sidecar is closed, typed, and complete:** it
  carries exactly the fields in `§4.1`, validates them by `§4.3`, contains no
  undeclared field, and is not a Contract v1 artifact. Evidence: `E3-NEG-037`,
  `E3-NEG-038`, `E3-NEG-024`, `E3-NEG-050`.
- **E3-006 Deterministic identity and status are truthful:** identical inputs
  and configuration produce byte-identical deterministic manifest content
  (`index_fingerprint`, `chunk_set_fingerprint`, `configuration_fingerprint`
  unchanged); a mixed batch is `PARTIAL` with the rejected documents and their
  codes recorded; a run that accepts nothing publishes no accepted record and no
  success audit event; no fingerprint is influenced by timestamps, run IDs,
  temporary names, process IDs, absolute paths, secrets, or iteration order.
  Evidence: `E3-NEG-013`, `E3-NEG-014`, `E3-NEG-028`, `E3-NEG-042`.
- **E3-007 The acceptance chain is the only publication path:** the accepted E3
  record and its canonical audit event exist if and only if all seven checks in
  `§6` passed, and they are published together; a rejection yields no accepted
  record, no registry mutation, no success audit event, and a preserved last
  known complete index. Evidence: `E3-NEG-016`, `E3-NEG-017`, `E3-NEG-020`,
  `E3-NEG-049`.
- **E3-008 Typed surface parity with a declared MCP boundary:** the Python API,
  the CLI, and the MCP surface share one typed request/result model; MCP either
  calls the same service with semantic parity or is declared unsupported with the
  deterministic `UNSUPPORTED_CAPABILITY` boundary of `§9`; no surface returns a
  different status, count, or error envelope for the same request.
  Evidence: `E3-NEG-040`, `E3-NEG-041`.
- **E3-009 Legacy stores are detected, read-only, and migrated explicitly:** a
  store lacking canonical identities or an E3 sidecar is never read as
  authoritative, never contributes a paper-level scientific count, and is
  migrated only through the dry-run/commit workflow of `§7.6`. Evidence:
  `E3-NEG-045`, `E3-NEG-046`.
- **E3-010 Replacement semantics and idempotency:** a re-index stages the
  complete candidate set, writes a recoverable commit intent, switches
  visibility atomically, removes the superseded chunks of the same canonical
  document, and publishes only after the live set matches; a shortened document
  leaves no old chunk retrievable; identical re-indexing is a no-op/reuse;
  readers see the old complete set or the new complete set, never a mixture.
  Evidence: `E3-NEG-001`, `E3-NEG-032`, `E3-NEG-043`, `E3-NEG-044`,
  `E3-NEG-052`, `E3-NEG-054`.
- **E3-011 Containment and explicit journal path:** every read and write is
  workspace-anchored; traversal, absolute, drive-letter, and symlink escapes are
  refused before I/O; the journal path is an explicit request field or the
  recorded workspace path, never discovered by walking parent directories.
  Evidence: `E3-NEG-025`, `E3-NEG-022`, `E3-NEG-021`.
- **E3-012 Backend verification and packaging:** the live backend is verified to
  hold exactly the declared visible chunk set (no missing chunk, no obsolete
  extra, no count mismatch, no metadata corruption, no embedding-identity
  mismatch); and every dependency E3 puts on an authoritative path is declared in
  the canonical kit and the metapackage, proven by a clean-wheel import and
  `--help` smoke. Evidence: `E3-NEG-023`, `E3-NEG-024`, `E3-NEG-048`.
- **E3-013 No undeclared or inert configuration:** every behavior-affecting
  option is present in the recorded chunker configuration and changes the result
  when changed; `min_chunk_chars` is implemented and tested or removed with a
  deprecation warning; an option that is stored but has no effect fails manifest
  validation rather than passing silently. Evidence: `E3-NEG-027`, `E3-NEG-024`.
- **E3-014 Synchronization, traceability, and claim honesty:** the canonical kit
  commits, the vendored `tools/<kit>/` snapshot, the full-SHA `plugins.json`
  pins, and the generated metapackage pins agree; every `RAG-0nn` row E3 claims
  maps to a named test ID; E3 claims no retrieval, scoring, synthesis, consensus,
  or matrix behavior and no Contract v1 change; and §14.1's residual risks are
  restated in the completion report. Evidence: `E3-NEG-047`, the `§10.3`
  requirement matrix, and `§14.1`.

## 4. Index Manifest v1 (kit-owned sidecar)

### 4.1 Closed field set

The sidecar is a self-describing object with `schema_version =
"index-manifest-v1"` and `manifest_type = "index_manifest"`. That type is **not**
a Contract v1 `artifact_type`; the frozen registries must keep rejecting it
(`§1.1` consequence 1, `E3-NEG-038`). The field set is closed: an undeclared
field is a validation failure, never a silently tolerated extension.

| Field | Type | Required | Meaning and rule |
|---|---|---|---|
| `schema_version` | `str` | yes | Exactly `index-manifest-v1`. |
| `manifest_type` | `str` | yes | Exactly `index_manifest`; a sidecar type, never an `artifact_type`. |
| `chunk_identity_algorithm_version` | `str` | yes | The identity algorithm that produced every `chunk_id` (currently `rag-chunk-identity-v1`). It is recorded so the manifest can re-derive its own chunk identities (§4.3 rule 4). |
| `manifest_id` | `str` | yes | `^IDX-[0-9a-f]{32}$`, deterministic (§5.3). Mirrors E1's `^ACQ-[0-9a-f]{32}$` and E2's `^EXT-[0-9a-f]{32}$` construction. |
| `manifest_identity_algorithm_version` | `str` | yes | The identity algorithm that produced `manifest_id` (currently `rag-index-identity-v1`). |
| `artifact_checksum` | `str` | yes | `sha256:<64 lowercase hex>` over the canonical manifest with this field set to `null` — the E1 construction (`tools/scholar-pdf-kit/src/scholar_pdf/acquisition.py:2694-2698`) and its verification (`:3025-3033`). |
| `workspace_id` | `str` | yes | `WSP-` identifier; must equal the accepted parent's. |
| `run_id` | `str` | yes | `RUN-` identifier of the indexing run. **Provenance only** — excluded from `index_fingerprint` (§5.2). |
| `protocol_fingerprint` | `str` | yes | Must equal the accepted parent's. |
| `corpus_fingerprint` | `str` | yes | Must equal the accepted parent's. |
| `parent_artifact_ref` | object | yes | Exactly `{artifact_id, artifact_type, sha256}` for the accepted `DocumentManifestArtifact`; `artifact_type` must be `document_manifest`. |
| `parent_lineage_sha256` | `str` | yes | `canonical_fingerprint` over the canonical parent reference, the same construction E1/E2 use (`tools/scholar-pdf-kit/src/scholar_pdf/acquisition.py:2668-2670`; E2 `:703-705`). |
| `chunker` | object | yes | `{algorithm_version, configuration, configuration_fingerprint}` (§4.2). |
| `embedder` | object | yes | `{provider, model, model_revision, dimension, normalize_embeddings, distance_metric, configuration_fingerprint}` (§4.2). `model_revision` is `null` when the backend cannot report it — and then the field is explicitly null, never inferred. |
| `backend` | object | yes | `{type, collection_name, storage_schema_version, hnsw_space, configuration_fingerprint}` (§4.2). **No absolute path, no CWD, no temporary name** (`readiness baseline §5`). |
| `documents` | array | yes | One `IndexedDocument` per accepted document, sorted by `document_id` (§4.2). May be empty only when `status` is `FAILED`. |
| `rejected_documents` | array | yes | One `RejectedDocument` per eligible document that was refused, sorted by `document_id` (§4.2). May be empty. |
| `visible_chunks` | array | yes | The exact live chunk inventory, sorted by `chunk_id` (§4.2). |
| `counts` | object | yes | `{accepted_documents, rejected_documents, visible_chunks}`, each `≥ 0`, each equal to the length of the corresponding array. |
| `chunk_set_fingerprint` | `str` | yes | `sha256:…` over the normalized visible inventory (§5.2). |
| `configuration_fingerprint` | `str` | yes | `sha256:…` over the effective chunker + embedder + backend configuration (§5.2). |
| `index_fingerprint` | `str` | yes | `sha256:…` over the self-reference-safe manifest payload (§5.2). |
| `status` | enum | yes | The frozen `OperationStatus` vocabulary (`src/scholar_harness/contracts/models.py:51-58`). E3 permits the subset `SUCCESS`, `PARTIAL`, `FAILED`, `ERROR`, `CANCELLED`; the remaining frozen members `SKIPPED` and `WAITING_FOR_DECISION` are valid `OperationStatus` values but are not producible by an indexing run, and their presence in a manifest is a validation failure. **No new status vocabulary is introduced** (§4.5). |
| `failures` | array | yes | Structured run-level failures; empty on `SUCCESS`. Each entry is `{code, detail, document_id?}` (§4.5). |
| `producer` | object | yes | `{package, version, commit}`; `package` must be `scholar-rag-kit` (readiness baseline §5). |
| `created_at` | `str` | yes | RFC3339 UTC. **Provenance only** — excluded from `index_fingerprint` (§5.2). |
| `production_fingerprint` | `str` | yes | Run-scoped reproducibility token: `fp({producer: {package, version, commit}, index_fingerprint})` (`§5.2` stage H). It commits to the implementation that produced the run while staying out of the deterministic identity, so G-4's "byte-identical" claim is checkable. It is excluded from stage F because stage H derives it **from** F, so it cannot cycle. |

No other top-level key is permitted. In particular the sidecar carries **no**
absolute path, no secret or credential, no process ID, no temporary file name, no
wall-clock-derived identity, and no free-text success claim.

### 4.2 Kit models

Names may follow repository convention; the fields, types, and validators may
not drift.

```text
IndexedDocument {
  document_id                  DOC- identifier, byte-for-byte from the parent
  study_id                     STU-/SCI- identifier, byte-for-byte from the parent
  extracted_path               workspace-relative POSIX path from the parent
  extracted_content_sha256     sha256:… over the exact bytes read at extracted_path
  extraction_method            MethodProvenance, byte-for-byte from the parent
  status                       IndexDocumentStatus
  detail                       str | null — required non-empty exactly when status == PARTIAL
  chunk_ids                    sorted list of CHK- identifiers
}

RejectedDocument {
  document_id                  DOC- identifier as requested
  study_id                     STU-/SCI- identifier as requested
  extracted_path               workspace-relative POSIX path, or null when absent
  code                         one closed E3 code (§4.5)
  detail                       bounded, non-empty, no path or secret leakage
}

VisibleChunk {
  chunk_id                     CHK- identifier (frozen registry form)
  document_id                  DOC- identifier
  study_id                     STU-/SCI- identifier
  locator                      {heading_path[], ordinal_in_section, section_category}
  chunk_text_sha256            sha256:… over the normalized chunk text
  character_count              int ≥ 1 over the same normalized text
}
```

`IndexDocumentStatus` is a **kit-sidecar per-document** status following the
E1/E2 per-item convention (`docs/architecture/wp01_packet_e2_extracted_text_handoff.md:557-576`):
`INDEXED` (staged, embedded, visible), `REUSED` (an exact, parent-bound,
configuration-bound re-index returned the committed set unchanged), `PARTIAL`
(indexed, degraded, and therefore carrying a non-empty `detail` that names the
degradation — an optional-overlap chunk, a truncated tail chunk, a downgraded
locator precision), `CANCELLED` (caller cancelled before commit), `FAILED`
(internal, filesystem, or commit failure prevented commit). A document with any
of these statuses is **not** in `rejected_documents`, and a document in
`rejected_documents` has no `chunk_ids` and is not visible. `detail` is
`null` for every status except `PARTIAL`: a degradation reason that is optional
is a `PARTIAL` claim a reviewer cannot check (`E3-013`, `G-7`).

### 4.3 Validation and truthfulness rules

The sidecar is valid only if all of the following hold. These are the rules the
harness adapter re-checks in `§6`; they are not re-implementations of them.

1. `manifest_id`, `artifact_checksum`, `chunk_set_fingerprint`,
   `configuration_fingerprint`, and `index_fingerprint` all recompute exactly
   from the manifest's own content by the `§5.2` stage order.
2. `counts.*` equals the corresponding array lengths, and
   `counts.accepted_documents == len(documents)`,
   `counts.visible_chunks == len(visible_chunks)`.
3. Every `documents[].chunk_ids` entry appears in `visible_chunks`, and every
   `visible_chunks[].chunk_id` appears in exactly one `documents[].chunk_ids`
   entry. No orphan, no unlisted chunk, no duplicate.
4. Every `chunk_id` validates against `src/scholar_harness/contracts/identifiers.py:36` and is a fixed point of
   the `§5.1` rule: recomputing the identity from the manifest's own
   `parent_artifact_ref`, `chunker`, `locator`, and `chunk_text_sha256` returns
   the same id. A manifest that merely *lists* an id it cannot re-derive is
   invalid (`E3-NEG-018`).
5. `documents` is sorted by `document_id`; `rejected_documents` is sorted by
   `document_id`; `visible_chunks` is sorted by `chunk_id`; every `chunk_ids`
   list is sorted. Sorting is part of validity, not a formatting preference.
6. Every `documents[]`/`visible_chunks[]` identifier is present in the accepted
   parent with the same values, and every `rejected_documents[]` identifier is
   present in the parent and is either unusable (no path) or refused with a
   reason.
7. `workspace_id`, `protocol_fingerprint`, and `corpus_fingerprint` equal the
   parent's; `parent_artifact_ref` matches the accepted artifact's id and
   registered hash.
8. `status == SUCCESS` requires `rejected_documents` empty, `failures` empty, and
   `counts.accepted_documents ≥ 1`. `status == PARTIAL` requires at least one
   entry in `rejected_documents` or `failures` **and** at least one accepted
   document. `status == FAILED` requires `documents` empty and no success claim.
   A `PARTIAL` manifest is never reported as a complete index (`E3-NEG-042`).
9. `documents[].detail` is non-null **iff** `documents[].status == PARTIAL`; it
   is non-empty, bounded, and leaks no path or secret. A `PARTIAL` document with
   a `null` detail and a non-`PARTIAL` document with a detail both fail
   validation (`E3-013`).
10. `chunker.configuration` contains **every** behavior-affecting option
    (§4.6) and no option that the implementation ignores (`E3-NEG-024`).
11. `backend` contains no absolute path, no CWD-derived value, and a
    `storage_schema_version` the implementation can actually enforce.
12. No field contains a secret, an API key, a bearer token, or an environment
    value. `embedder` records provider/model identity, never credentials.
13. Exactly the `§4.1` field set is present. An undeclared top-level key, an
    undeclared `IndexedDocument`/`RejectedDocument`/`VisibleChunk` key, or a
    missing required key is a validation failure, never a tolerated extension
    (`E3-NEG-024`).

### 4.4 Placement and lifecycle

The sidecar lives at `rag/index/<run_id>/<IDX-…>.json`, mirroring E1's
`literature/acquisition/<run_id>/<ACQ-…>.json` and E2's
`literature/extraction/<run_id>/<EXT-…>.json` while keeping the RAG kit's own
`rag/` subtree (the Chroma store already lives at `rag/chroma_db/`; the surface
matrix records the current CWD-relative default at
`docs/kits_surface_matrix.md:371`). Its destination is derived from its own
embedded identity; a relocated, symlinked, or escaping sidecar is a placement
failure (`E3-NEG-022`). The commit intent of `§7.3` is written first, at
`rag/index/<run_id>/commit-intent.json`, and is removed only after the accepted
record and audit event are durable.

### 4.5 Status and code vocabulary

E3 introduces **no new status vocabulary**: the manifest `status` uses the frozen
`OperationStatus` (`src/scholar_harness/contracts/models.py:51-58`) and per-document status follows the E1/E2
kit-sidecar convention (§4.2). Every mandatory failure class in `§10.2` maps to
a code, and every code is either an existing frozen `ErrorCode`
(`src/scholar_harness/contracts/models.py:65-78`) or one of the ten E3 sidecar constants below. The E3
constants are **sidecar codes, not Contract v1 `ErrorCode` members**, and no
harness, verify, or agent surface may present them as Contract codes.

| Failure class (`§10.2`) | Code | Kind |
|---|---|---|
| Missing / unreadable parent | `NOT_FOUND` | frozen `ErrorCode` |
| Malformed parent payload or failed frozen-model validation | `VALIDATION_ERROR` | frozen `ErrorCode` |
| Parent `artifact_type` not a Contract v1 type (or an attempt to publish `index_manifest` as one) | `UNSUPPORTED_ARTIFACT_TYPE` | harness acceptance-gate code (`src/scholar_harness/contracts/acceptance.py:263`) |
| Unaccepted parent (absent from the registry) | `MISSING_PARENT_ARTIFACT` | acceptance-gate code (`src/scholar_harness/contracts/acceptance.py:331`) |
| Hash-stale parent | `PARENT_HASH_MISMATCH` | acceptance-gate code (`src/scholar_harness/contracts/acceptance.py:341`) |
| Parent whose `workspace_id` is not the accepted workspace's namespace | `WORKSPACE_NAMESPACE_MISMATCH` | **E3 sidecar constant** |
| Wrong required parent type | `REQUIRED_PARENT_TYPE_MISSING` | acceptance-gate code (`src/scholar_harness/contracts/acceptance.py:399-401`) |
| Protocol / corpus fingerprint mismatch | `PROTOCOL_FINGERPRINT_MISMATCH` / `CORPUS_FINGERPRINT_MISMATCH` | frozen `ErrorCode` |
| Path escape, symlink escape, wrong file type, unreadable extraction | `PATH_OUTSIDE_WORKSPACE` | frozen `ErrorCode` |
| Chunk identity collision / cross-document reuse / non-derivable id | `CHUNK_IDENTITY_COLLISION` | **E3 sidecar constant** |
| Locator not unique inside one document | `LOCATOR_NOT_UNIQUE` | **E3 sidecar constant** |
| Extracted text empty/unusable after normalization | `EXTRACTED_TEXT_UNUSABLE` | **E3 sidecar constant** |
| Bytes at the committed path changed without a re-index request | `EXTRACTED_CONTENT_CHANGED` | **E3 sidecar constant** |
| Stored-but-inert behavior-affecting option | `CONFIGURATION_INEFFECTIVE` | **E3 sidecar constant** |
| Embedding provider/model/dimension changed while reusing a collection | `EMBEDDING_IDENTITY_CHANGED` | **E3 sidecar constant** |
| Live backend disagrees with the declared visible set | `BACKEND_STATE_INCONSISTENT` | **E3 sidecar constant** |
| Legacy store without canonical identities | `LEGACY_STORE_READ_ONLY` | **E3 sidecar constant** |
| Journal path discovered by a parent-directory walk, or an undeclared dependency on an authoritative path | `DEPENDENCY_ERROR` | frozen `ErrorCode` |
| MCP indexing surface offered before the `§9` boundary lifts | `UNSUPPORTED_CAPABILITY` | **E3 sidecar constant** |
| Kit canonical primitive, commit, vendored tree, or full-SHA pin drift | `BLOCKED_KIT_DRIFT` | harness gate code |
| Concurrent same-document and different-document indexing | `CONFLICT` | frozen `ErrorCode` |
| Interrupted staging / visibility switch / manifest-or-audit publication | `ATOMIC_COMMIT_FAILED` | frozen `ErrorCode` |
| Replay with a changed non-volatile payload under an existing identity | `IDEMPOTENCY_CONFLICT` | frozen `ErrorCode` |
| Internal defect | `INTERNAL_ERROR` | frozen `ErrorCode` |

Similarity must never be reported as verification or entailment
(`RAG-005`, `RAG-006`): there is **no** code for "verified by similarity", and
an indexing surface that emits `VERIFIED`/`ENTAILED` from a cosine score is
refused with `VALIDATION_ERROR` (`E3-NEG-036`).

### 4.6 The effective chunker configuration is closed

`chunker.configuration` records exactly the options that change chunk output for
a given extracted text. For the `structural-ast-markdown-v2` chunker the set is
`{max_chunk_chars, min_chunk_chars, overlap_chars, heading_levels,
strip_frontmatter, normalize_whitespace, sentence_split_pattern}`. An option
outside the set is a validation failure (`E3-NEG-024`); an option inside the set
that the implementation does not actually honor is
`CONFIGURATION_INEFFECTIVE` (`E3-NEG-027`). `min_chunk_chars` is therefore
either implemented and tested or removed with a deprecation warning
(`RAG-020`; today it is stored and never read, `tools/scholar-rag-kit/src/scholar_rag/chunker.py:23,27`).

## 5. Chunk and index identity, canonicalization, and golden examples

Every rule in this section is **executable**: each example below was produced with
the frozen helpers in `src/scholar_harness/contracts/canonical.py` at harness
`0a15bbb`, and `§5.5` gives the exact reproduction. A reviewer can re-derive every
digest in this document from the printed inputs.

### 5.1 Chunk identity

`chunk_id` is minted with the **frozen** helper, not a new rule:

```text
chunk_id = deterministic_id(
    IdentifierKind.CHUNK,
    workspace_namespace = <accepted workspace_id>,
    canonical_input = {
        "parent_artifact_id":            <accepted ART- id of the document_manifest>,
        "parent_artifact_sha256":        <its registered canonical sha256:…>,
        "study_id":                      <parent DocumentRecord.study_id>,
        "document_id":                   <parent DocumentRecord.document_id>,
        "extracted_content_sha256":      <sha256:… over the bytes read at extracted_path>,
        "chunker_algorithm_version":     "structural-ast-markdown-v2",
        "chunker_configuration_fingerprint": <§5.2 stage A>,
        "locator": {"heading_path": [...], "ordinal_in_section": N,
                    "section_category": "..."},
        "chunk_text_sha256":             <sha256:… over the normalized chunk text>
    },
    algorithm_version = "rag-chunk-identity-v1",
)
```

`deterministic_id` (`src/scholar_harness/contracts/canonical.py:167-183`) hashes
`{algorithm_version, kind, workspace_namespace, input}` with
`canonical_json_bytes` and prefixes `primary_prefix(IdentifierKind.CHUNK)`,
i.e. `CHK-` (`src/scholar_harness/contracts/identifiers.py:36,47-50`). Consequences that are binding:

- The result is `CHK-` plus 32 lowercase hex characters, which satisfies
  `src/scholar_harness/contracts/identifiers.py:44,58-67` exactly. Nothing else is a valid `chunk_id`.
- The **normalized** structural locator is a *component of the identity*, not a
  display label. Renaming a heading changes the chunk identity, because the
  content a reader would cite has changed; a pure position shift that leaves the
  same locator and the same text does not.
- Filename, title, DOI, section slug alone, and ordinal alone are all excluded as
  identity sources (§3 `E3-001`).
- The `extracted_content_sha256` and `chunk_text_sha256` are computed over the
  **normalized** text (the same normalization the chunker applies), so a
  whitespace-only edit is not a content change and a word change is.

**Golden limbs.** With `chunker_configuration_fingerprint =
sha256:df987253699f5dd93e8821d81eaf48f873323a1f7efee4baf6f37cb3ddc40846` and
`workspace_id = WSP-0123456789abcdef0123456789abcdef`, the canonical input
serializes to exactly:

```json
{"chunk_text_sha256":"sha256:9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d","chunker_algorithm_version":"structural-ast-markdown-v2","chunker_configuration_fingerprint":"sha256:df987253699f5dd93e8821d81eaf48f873323a1f7efee4baf6f37cb3ddc40846","document_id":"DOC-33333333333333333333333333333333","extracted_content_sha256":"sha256:5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b","locator":{"heading_path":["Methods","Data"],"ordinal_in_section":1,"section_category":"methods"},"parent_artifact_id":"ART-11111111111111111111111111111111","parent_artifact_sha256":"sha256:1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a","study_id":"STU-44444444444444444444444444444444"}
```

| Limb | Change to the canonical input | Resulting `chunk_id` | Ledger | Claim proved |
|---|---|---|---|---|
| baseline | none - the printed canonical input verbatim | `CHK-ab10cb5729e20ff5dc8d26a93455010c` | `E3-POS-001` | the frozen reference form |
| replay | none at all (identical input and configuration) | `CHK-ab10cb5729e20ff5dc8d26a93455010c` | `E3-NEG-001` | identical input + configuration is byte-stable (G-2) |
| new parent id | `parent_artifact_id` → `ART-22222222222222222222222222222222` | `CHK-51e673b76218cb974e7f73bf874afd8e` | `E3-NEG-002` | a new accepted parent re-derives identity, so stale chunks cannot be reused silently |
| new parent hash | `parent_artifact_sha256` → `sha256:2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c` | `CHK-64217494f04a174971e3c562f0a9fb17` | `E3-NEG-003` | re-registered parent content is a new identity, not a silent continuation |
| study change | `study_id` → `STU-55555555555555555555555555555555` | `CHK-fbd05b14b42e0660bd52fff2db68ca74` | `E3-NEG-004` | two studies with byte-identical text get distinct chunk identities (`RAG-001`, G-3) |
| document change | `document_id` → `DOC-77777777777777777777777777777777` | `CHK-5f643b091718d7953bec5dfd5c02f6fe` | `E3-NEG-005` | a chunk belongs to its document, not to a path or a filename |
| locator ordinal | `locator.ordinal_in_section` 1 → 2 | `CHK-fa4b72e1836c63eba7322668b902ac34` | `E3-NEG-007` | the cited position is part of the identity, so a position shift is not cosmetic |
| heading rename | `locator.heading_path` `["Methods","Data"]` → `["Methods","Data Sources"]` | `CHK-979d043153dfeaaccd66b1cc2c975381` | `E3-NEG-055` | renaming a heading changes the normalized locator and therefore the identity, because the content a reader would cite has changed (`§5.1` binding consequence 2) |
| extracted text | `extracted_content_sha256` → `sha256:aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae` | `CHK-a3e0f12ee1e8d0f6dc0fdb790a991397` | `E3-NEG-006` | changed text at an unchanged locator changes identity - the limb the current positional scheme fails (`§1.4` #2) |
| chunk text | `chunk_text_sha256` → `sha256:bfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbf` | `CHK-34f8ebac998f08f337dc27f1132f3d50` | `E3-NEG-008` | a chunk-level change is identity-changing, not cosmetic |
| config change | `chunker_configuration_fingerprint` → `sha256:582e7dbf9c7dad8e561a1dfb422974edb49752fae85b210456b8b0337d9711e8` | `CHK-12ad8c52142b31dfab7c50dea3fe0dc3` | `E3-NEG-051` | a behavior-affecting configuration change changes identity (`RAG-020`) |
| chunker algorithm version | `chunker_algorithm_version` `structural-ast-markdown-v2` → `structural-ast-markdown-v3` | `CHK-c2fc5e3c33946d65cac5c6d8c0eea9c7` | `E3-NEG-056` | the version string is inside the canonical payload, so a chunker algorithm change changes every identity it produced |
| cross-workspace | `workspace_namespace` → `WSP-99999999999999999999999999999999` | `CHK-90dc5333896c124d343ed44d03debc1e` | `E3-NEG-053` | a workspace is a namespace, not a cosmetic label (G-3) |

Every perturbation above is printed in full, so each `CHK-` id is re-derivable
offline by substituting exactly one printed value into the canonical input block
and calling the frozen `deterministic_id` - no truncated hash, no unstated
intermediate. The `13` rows yield `12` distinct ids.

Each limb is a **distinct** id. There is no limb in which a change produces the
baseline id, and no two change-limbs produce the same id as each other - with one
deliberate exception: the **replay** limb, whose whole claim is that *no* change
produces a different id. That is why 13 rows yield 12 distinct ids.

### 5.2 Fingerprint stages (self-reference-safe, order-independent)

The three deterministic fingerprints are computed in a fixed stage order, so no
stage can depend on a value that does not exist yet. Each stage uses
`canonical_fingerprint` (`src/scholar_harness/contracts/canonical.py:117-125`).

```text
Stage A  chunker_configuration_fingerprint =
             fp(chunker.configuration)                       # contains no fingerprint key
Stage B  embedder.configuration_fingerprint =
             fp(embedder minus configuration_fingerprint)
Stage C  backend.configuration_fingerprint =
             fp(backend minus configuration_fingerprint)
Stage D  configuration_fingerprint =
             fp({chunker: {..., "configuration_fingerprint": <A>},
                 embedder: {..., "configuration_fingerprint": <B>},
                 backend: {..., "configuration_fingerprint": <C>}})
Stage E  chunk_set_fingerprint =
             fp({"visible_chunks": <normalized sorted inventory>},
                set_like_arrays={"/visible_chunks"})
Stage F  index_fingerprint =
             fp(manifest minus {run_id, created_at,          # volatile (readiness §5)
                                production_fingerprint}     # derived from F itself
                    with {manifest_id: null,
                          artifact_checksum: null,
                          index_fingerprint: null})         # self-reference-safe
Stage G  manifest_id =
             "IDX-" + sha256(canonical_json_bytes(
                 <Stage F payload> with index_fingerprint = <F>))[:32]
Stage H  production_fingerprint =
             fp({producer: {package, version, commit}, index_fingerprint: <F>})
Stage I  artifact_checksum =
             fp(<full manifest> with artifact_checksum = null)   # the E1 construction
```

The stages are a **total order over a DAG**: `A,B,C → D`; `E → F`;
`F → G`; `F → H`; `{G, H} → I`. No stage reads a value that does not exist yet
and no stage transitively reads itself. `production_fingerprint` is excluded from
stage F because stage H derives it **from** F; it is included in stage I because
the outer seal covers the whole manifest, including the run-scoped token.

One named projection makes the determinism claim precise:

```text
deterministic_projection = manifest minus {run_id, created_at, artifact_checksum}
```

`deterministic_projection` is what "the index" means for comparison purposes: it
is the whole manifest except the two provenance fields and the seal over the
whole file. `artifact_checksum` is deliberately *not* run-invariant — it seals the
bytes as written, run identity included, exactly as E1's does — so a no-op
re-index is compared through the projection, never through the seal.

Four rules make this safe and are individually testable:

1. **Self-reference safety.** `index_fingerprint` is computed with its own field
   set to `null`, and `manifest_id`/`artifact_checksum` are nulled in the same
   payload. A fingerprint therefore never has to hash its own value. This is the
   E1/E2 construction, not a new one (`tools/scholar-pdf-kit/src/scholar_pdf/acquisition.py:2694-2698,3025-3033`).
2. **Volatile-field exclusion.** `run_id` and `created_at` are removed from the
   stage F payload, so a replay under a new run at a new wall-clock time has the
   same `index_fingerprint` and the same `manifest_id`, and its
   `deterministic_projection` is byte-identical. They remain in the manifest as
   provenance and in the audit event as run identity. `artifact_checksum` is
   *not* in that claim: it seals the file as written, so it changes with the run
   and is re-derived, not compared.
3. **Order independence.** Arrays whose order carries no meaning are registered
   as set-like at their JSON pointer (`src/scholar_harness/contracts/canonical.py:79-89,93-114`), so
   filesystem enumeration order and backend iteration order cannot reach a
   fingerprint. **The sidecar's arrays are additionally sorted on the way in
   (§4.3 rule 5)**, so the manifest is readable and stable, not merely
   order-insensitive.
4. **Byte-identity of a no-op re-index.** Rules 1–3 plus stage H make
   `deterministic_projection` identical for two runs over the same accepted
   parent, configuration, and chunk inventory at the same `producer.commit`:
   `production_fingerprint` is a function of `producer.commit` and
   `index_fingerprint`, so it is invariant too. Two such manifests therefore
   differ in **exactly** `{run_id, created_at, artifact_checksum}` and in nothing
   else. That is the checkable form of G-4 and of readiness §7's "byte-identical
   deterministic manifest content" (`E3-NEG-001`, the `§5.1` replay limb): the test
   asserts
   `canonical_json_bytes(deterministic_projection(a)) ==
   canonical_json_bytes(deterministic_projection(b))`, asserts the differing-key
   set is exactly those three, and separately asserts that each re-derives.

A `producer.commit` change **does** change `index_fingerprint`, deliberately: a
different implementation commit is a different reproducibility claim, and §14.1
records that consequence. Content-identical re-indexing at the same commit does
not change it.

### 5.3 Golden manifest

A worked `Index Manifest v1` sidecar for a `PARTIAL` run: three documents
eligible, two accepted (three visible chunks), one refused as unusable. It is
reproduced verbatim from the frozen helpers and is the fixture the canonical
tests and the harness conformance test must share.

```json
{
  "artifact_checksum": "sha256:93a5464304f2fb8b6bdc7fe12b0fe571be3050ab5cb17031102e9d2dbc5c8273",
  "backend": {
    "collection_name": "nexus-evidence-v1",
    "configuration_fingerprint": "sha256:3eeab05fb65e7134aae01eb437f7a69cc74b995a60b1056420ea2115101e7c82",
    "hnsw_space": "cosine",
    "storage_schema_version": "chroma-2",
    "type": "chroma"
  },
  "chunk_identity_algorithm_version": "rag-chunk-identity-v1",
  "chunk_set_fingerprint": "sha256:1b7ae1a9ea99dd1173f51b87e1c57f8e700b5ca7722ff34052b2027c4ba052c5",
  "chunker": {
    "algorithm_version": "structural-ast-markdown-v2",
    "configuration": {
      "heading_levels": [
        1,
        2,
        3
      ],
      "max_chunk_chars": 1200,
      "min_chunk_chars": 200,
      "normalize_whitespace": true,
      "overlap_chars": 120,
      "sentence_split_pattern": "(?<=[.!?])\\s+",
      "strip_frontmatter": true
    },
    "configuration_fingerprint": "sha256:df987253699f5dd93e8821d81eaf48f873323a1f7efee4baf6f37cb3ddc40846"
  },
  "configuration_fingerprint": "sha256:a5a536f0263ac1ff84aafc2f5201d2da8bdffabce855fc668120c29f7a0201c6",
  "corpus_fingerprint": "sha256:3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d3d",
  "counts": {
    "accepted_documents": 2,
    "rejected_documents": 1,
    "visible_chunks": 3
  },
  "created_at": "2026-09-27T00:00:00Z",
  "documents": [
    {
      "chunk_ids": [
        "CHK-ab10cb5729e20ff5dc8d26a93455010c",
        "CHK-c7c2ec27c99f59ad643a0979f2341523"
      ],
      "detail": null,
      "document_id": "DOC-33333333333333333333333333333333",
      "extracted_content_sha256": "sha256:5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b",
      "extracted_path": "extracted/DOC-33333333333333333333333333333333.md",
      "extraction_method": "DETERMINISTIC_RULE",
      "status": "INDEXED",
      "study_id": "STU-44444444444444444444444444444444"
    },
    {
      "chunk_ids": [
        "CHK-4d2120ace9cbf53314aa2878a2ddc3a2"
      ],
      "detail": null,
      "document_id": "DOC-66666666666666666666666666666666",
      "extracted_content_sha256": "sha256:6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e6e",
      "extracted_path": "extracted/DOC-66666666666666666666666666666666.md",
      "extraction_method": "HUMAN",
      "status": "INDEXED",
      "study_id": "STU-77777777777777777777777777777777"
    }
  ],
  "embedder": {
    "configuration_fingerprint": "sha256:04efcfeecbc7e30057c0a8e2101d4140d0bc153f7b136faee510be98fa703783",
    "dimension": 384,
    "distance_metric": "cosine",
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "model_revision": null,
    "normalize_embeddings": true,
    "provider": "sentence-transformers"
  },
  "failures": [],
  "index_fingerprint": "sha256:c1f6a2d084e09691985d82715612103e0bf90a008bf26d310cbf6e45bbb7ba37",
  "manifest_id": "IDX-748c4d3dd6cfc8133835092b36b7b4bc",
  "manifest_identity_algorithm_version": "rag-index-identity-v1",
  "manifest_type": "index_manifest",
  "parent_artifact_ref": {
    "artifact_id": "ART-11111111111111111111111111111111",
    "artifact_type": "document_manifest",
    "sha256": "sha256:1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"
  },
  "parent_lineage_sha256": "sha256:79734e6cbbdf269b8b76a2de677bd189d7d87e9b9a81271866be285b4449406b",
  "producer": {
    "commit": "c89b68f0d35173082a03b8c6b228e84381271185",
    "package": "scholar-rag-kit",
    "version": "0.2.0"
  },
  "production_fingerprint": "sha256:948aac5f8a68da8a1b7dadc01d393d2b28d597b58a3ae1843381a08188e025d3",
  "protocol_fingerprint": "sha256:2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c2c",
  "rejected_documents": [
    {
      "code": "EXTRACTED_TEXT_UNUSABLE",
      "detail": "extracted text is 0 usable characters after normalization",
      "document_id": "DOC-99999999999999999999999999999999",
      "extracted_path": "extracted/DOC-99999999999999999999999999999999.md",
      "study_id": "STU-88888888888888888888888888888888"
    }
  ],
  "run_id": "RUN-0f3a9c2b1d4e5f60718293a4b5c6d7e8",
  "schema_version": "index-manifest-v1",
  "status": "PARTIAL",
  "visible_chunks": [
    {
      "character_count": 1103,
      "chunk_id": "CHK-4d2120ace9cbf53314aa2878a2ddc3a2",
      "chunk_text_sha256": "sha256:bfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbfbf",
      "document_id": "DOC-66666666666666666666666666666666",
      "locator": {
        "heading_path": ["Results"],
        "ordinal_in_section": 1,
        "section_category": "results"
      },
      "study_id": "STU-77777777777777777777777777777777"
    },
    {
      "character_count": 1184,
      "chunk_id": "CHK-ab10cb5729e20ff5dc8d26a93455010c",
      "chunk_text_sha256": "sha256:9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d9d",
      "document_id": "DOC-33333333333333333333333333333333",
      "locator": {
        "heading_path": [
          "Methods",
          "Data"
        ],
        "ordinal_in_section": 1,
        "section_category": "methods"
      },
      "study_id": "STU-44444444444444444444444444444444"
    },
    {
      "character_count": 962,
      "chunk_id": "CHK-c7c2ec27c99f59ad643a0979f2341523",
      "chunk_text_sha256": "sha256:aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae",
      "document_id": "DOC-33333333333333333333333333333333",
      "locator": {
        "heading_path": [
          "Methods",
          "Data"
        ],
        "ordinal_in_section": 2,
        "section_category": "methods"
      },
      "study_id": "STU-44444444444444444444444444444444"
    }
  ],
  "workspace_id": "WSP-0123456789abcdef0123456789abcdef"
}
```

Golden values, all recomputed by `§5.5`:

| Quantity | Value |
|---|---|
| `parent_lineage_sha256` | `sha256:79734e6cbbdf269b8b76a2de677bd189d7d87e9b9a81271866be285b4449406b` |
| `chunker.configuration_fingerprint` | `sha256:df987253699f5dd93e8821d81eaf48f873323a1f7efee4baf6f37cb3ddc40846` |
| `embedder.configuration_fingerprint` | `sha256:04efcfeecbc7e30057c0a8e2101d4140d0bc153f7b136faee510be98fa703783` |
| `backend.configuration_fingerprint` | `sha256:3eeab05fb65e7134aae01eb437f7a69cc74b995a60b1056420ea2115101e7c82` |
| `configuration_fingerprint` | `sha256:a5a536f0263ac1ff84aafc2f5201d2da8bdffabce855fc668120c29f7a0201c6` |
| `chunk_set_fingerprint` | `sha256:1b7ae1a9ea99dd1173f51b87e1c57f8e700b5ca7722ff34052b2027c4ba052c5` |
| `index_fingerprint` | `sha256:c1f6a2d084e09691985d82715612103e0bf90a008bf26d310cbf6e45bbb7ba37` |
| `manifest_id` | `IDX-748c4d3dd6cfc8133835092b36b7b4bc` |
| `artifact_checksum` | `sha256:93a5464304f2fb8b6bdc7fe12b0fe571be3050ab5cb17031102e9d2dbc5c8273` |
| `production_fingerprint` | `sha256:948aac5f8a68da8a1b7dadc01d393d2b28d597b58a3ae1843381a08188e025d3` |

The example is deliberately **not** a clean success. It is `PARTIAL` with one
rejected document and a recorded code, which is the shape `RAG-012` demands and
the shape a naive implementation hides (`G-7`).

### 5.4 What must never influence a deterministic fingerprint

Excluded by construction from the Stage F payload: `run_id`, `created_at`,
secrets and credentials, absolute and machine-specific paths, temporary file
names, process IDs, backend iteration order, filesystem enumeration order, and
the order of any set-like array. Prohibited outright by §4.1/§4.3: any
wall-clock-derived identity, any invented workspace/study identity, and any
undeclared configuration key.

### 5.5 Reproduction

Every digest above is reproducible offline from **this document**, with the frozen
helpers, no network, no backend, no workspace, and no fixture file. The script
reads the `§5.3` block out of this file, so it cannot drift from what is printed:

```powershell
$env:PYTHONPATH = "$PWD/src"
@'
import hashlib, json, pathlib, re
from scholar_harness.contracts.canonical import (
    canonical_fingerprint as fp, canonical_json_bytes, deterministic_id)
from scholar_harness.contracts.identifiers import IdentifierKind

doc = pathlib.Path("docs/architecture/wp01_packet_e3_implementation_handoff.md")
blocks = re.findall(r"```json\n(.*?)\n```", doc.read_text(encoding="utf-8"), re.S)
m = json.loads(next(b for b in blocks if '"manifest_id"' in b))
raw_input = next(b for b in blocks if '"parent_artifact_id"' in b)
assert canonical_json_bytes(json.loads(raw_input)).decode() == raw_input, \
    "the printed canonical input is not canonical bytes"

def stage_f(src):
    out = {k: v for k, v in src.items()
           if k not in {"run_id", "created_at", "production_fingerprint"}}
    for k in ("manifest_id", "artifact_checksum", "index_fingerprint"):
        out[k] = None
    return out

def projection(src):
    return {k: v for k, v in src.items()
            if k not in {"run_id", "created_at", "artifact_checksum"}}

assert fp(stage_f(m)) == m["index_fingerprint"], "stage F"
assert "IDX-" + hashlib.sha256(
    canonical_json_bytes({**stage_f(m), "index_fingerprint": m["index_fingerprint"]})
).hexdigest()[:32] == m["manifest_id"], "stage G"
assert fp({"producer": {k: m["producer"][k]
                        for k in ("package", "version", "commit")},
           "index_fingerprint": m["index_fingerprint"]}) == m["production_fingerprint"], "stage H"
assert fp({**m, "artifact_checksum": None}) == m["artifact_checksum"], "stage I"
assert fp({"visible_chunks": m["visible_chunks"]},
          set_like_arrays={"/visible_chunks"}) == m["chunk_set_fingerprint"], "stage E"
assert fp(m["parent_artifact_ref"]) == m["parent_lineage_sha256"]
assert fp(m["chunker"]["configuration"]) == m["chunker"]["configuration_fingerprint"]
assert fp({k: v for k, v in m["embedder"].items()
           if k != "configuration_fingerprint"}) == m["embedder"]["configuration_fingerprint"], "stage B"
assert fp({k: v for k, v in m["backend"].items()
           if k != "configuration_fingerprint"}) == m["backend"]["configuration_fingerprint"], "stage C"
assert fp({"chunker": m["chunker"], "embedder": m["embedder"],
           "backend": m["backend"]}) == m["configuration_fingerprint"]

listed = [c for d in m["documents"] for c in d["chunk_ids"]]
assert sorted(listed) == sorted(c["chunk_id"] for c in m["visible_chunks"])
for d in m["documents"]:
    for cid in d["chunk_ids"]:
        c = next(x for x in m["visible_chunks"] if x["chunk_id"] == cid)
        assert deterministic_id(IdentifierKind.CHUNK, m["workspace_id"], {
            "parent_artifact_id": m["parent_artifact_ref"]["artifact_id"],
            "parent_artifact_sha256": m["parent_artifact_ref"]["sha256"],
            "study_id": d["study_id"], "document_id": d["document_id"],
            "extracted_content_sha256": d["extracted_content_sha256"],
            "chunker_algorithm_version": m["chunker"]["algorithm_version"],
            "chunker_configuration_fingerprint": m["chunker"]["configuration_fingerprint"],
            "locator": c["locator"], "chunk_text_sha256": c["chunk_text_sha256"],
        }, algorithm_version=m["chunk_identity_algorithm_version"]) == cid, cid

# rule 4: a no-op re-index changes run_id, created_at and the whole-file seal only
replay = {**m, "run_id": "RUN-" + "f" * 32, "created_at": "2027-01-01T00:00:00Z",
          "artifact_checksum": None}
replay["artifact_checksum"] = fp(replay)
assert canonical_json_bytes(projection(m)) == canonical_json_bytes(projection(replay))
diff = sorted(k for k in set(m) | set(replay)
              if canonical_json_bytes(m.get(k, "<absent>"))
              != canonical_json_bytes(replay.get(k, "<absent>")))
assert diff == ["artifact_checksum", "created_at", "run_id"], diff
assert fp(stage_f(replay)) == m["index_fingerprint"]

print("E3 golden manifest: stages A-I, every chunk identity, and the "
      "no-op-reindex projection rule all re-derive")
'@ | uv run --no-sync python -
```

The required tests ship the same assertions in the canonical kit
(`tests/test_index_identity.py`) and the harness conformance test
(`tests/conformance/test_e3_index_lineage_boundary.py`) as executable code
(`E3-POS-003`), so a fingerprint change is a deliberate, reviewable edit rather
than a regenerated blob.

## 6. The E3 acceptance chain

### 6.1 Who owns what

The RAG kit produces a **candidate**. The harness E3 acceptance adapter decides
whether that candidate becomes the accepted E3 record. Neither may do the other's
job (G-9).

| Actor | May | May not |
|---|---|---|
| `scholar-rag-kit` | read the accepted parent through the harness-supplied reference; chunk, embed, stage, replace in the backend; write the sidecar, the commit intent, and its own run report | import `scholar_harness`; write `audit/journal.jsonl`; write any Contract v1 registry; claim its candidate was accepted; mint a non-`CHK-` identity |
| harness E3 acceptance adapter | load the parent through the frozen registry, re-verify identity/lineage/config, recompute every fingerprint, interrogate the backend, write the accepted record and the canonical audit event | re-implement chunking, embedding, retrieval, or scoring; repair the candidate instead of rejecting it; publish a `PARTIAL` candidate as complete |

The adapter calls the kit's typed service and the kit's own verification query. It
does not open a Chroma file to count rows and call that verification.

### 6.2 The seven ordered checks

These are the readiness baseline's `§4` steps 1–7 in order. Each has one owner,
one code on failure, and one test. The chain is **ordered and fail-fast**: a
failure at step *k* means steps *k+1…7* never run, which is what makes "zero
authoritative publication" checkable rather than aspirational.

| # | Check | Owner | Failure code | Ledger |
|---|---|---|---|---|
| 1 | Load the parent through the frozen Contract v1 registry; confirm it is registered as `document_manifest` and re-validate it against the frozen models | adapter | `NOT_FOUND` / `UNSUPPORTED_ARTIFACT_TYPE` / `VALIDATION_ERROR` | `E3-NEG-016`, `E3-NEG-015`, `E3-NEG-038` |
| 2 | Verify the declared parent `artifact_id` **and** canonical payload hash against the registry entry | adapter | `PARENT_HASH_MISMATCH` | `E3-NEG-017` |
| 3 | Verify `workspace_id`, `protocol_fingerprint`, and `corpus_fingerprint` agree with the parent, and that the parent is the required type for the accepted chain position. A workspace-namespace disagreement (`WORKSPACE_NAMESPACE_MISMATCH`, `C-05`) is a distinct condition from a wrong required parent type (`REQUIRED_PARENT_TYPE_MISSING`, `C-07`); neither implies the other | adapter | `REQUIRED_PARENT_TYPE_MISSING` / `PROTOCOL_FINGERPRINT_MISMATCH` / `CORPUS_FINGERPRINT_MISMATCH` / `WORKSPACE_NAMESPACE_MISMATCH` | `E3-NEG-039`, `E3-NEG-049`, `E3-NEG-012` |
| 4 | Verify every indexed and every rejected `document_id`/`study_id` is eligible in the parent, with byte-identical values, and that no document's own metadata re-bound its identity | adapter + kit | `VALIDATION_ERROR` | `E3-NEG-009`, `E3-NEG-010`, `E3-NEG-011`, `E3-NEG-029` |
| 5 | Recompute `manifest_id`, `artifact_checksum`, `chunk_set_fingerprint`, `configuration_fingerprint`, `production_fingerprint`, and `index_fingerprint` by the `§5.2` stage order, and re-derive every `chunk_id` by the `§5.1` rule | adapter | `VALIDATION_ERROR` / `CHUNK_IDENTITY_COLLISION` | `E3-NEG-018`, `E3-NEG-019`, `E3-NEG-001`…`008`, `E3-NEG-051` |
| 6 | Prove the live backend holds **exactly** the declared visible chunk set — no missing chunk, no obsolete extra, no count mismatch, no metadata corruption, no embedding-identity mismatch — through the kit's typed verification query | kit, invoked by the adapter | `BACKEND_STATE_INCONSISTENT` / `EMBEDDING_IDENTITY_CHANGED` | `E3-NEG-023`, `E3-NEG-024`, `E3-NEG-043` |
| 7 | Publish the accepted E3 record **and** the canonical audit event together, then remove the commit intent | adapter | `ATOMIC_COMMIT_FAILED` | `E3-NEG-020`, `E3-NEG-044` |

Checks 1–3 and 5 are pure verification over immutable inputs and a file. Check 4
adds the eligibility join. Check 6 is the only one that touches the backend, and
it is a **read**. Check 7 is the only writer. Nothing before check 7 mutates
authoritative state (G-5).

### 6.3 The accepted E3 record

The accepted E3 record is **adapter-owned and non-Contract**. It is deliberately
not a `run_manifest` and not a `document_manifest`: those types are frozen and
mean something else (`§1.1`).

| Property | Value | Why |
|---|---|---|
| Location | `rag/index/accepted.json` | One file per workspace, outside `artifacts/`, so it can never be mistaken for a published Contract artifact; sibling to the per-run sidecars of `§4.4`. |
| Contents | `{schema_version: "index-acceptance-v1", workspace_id, parent_artifact_ref, parent_lineage_sha256, manifest_id, manifest_path, artifact_checksum, index_fingerprint, chunk_set_fingerprint, configuration_fingerprint, production_fingerprint, status, counts, accepted_at, accepted_by}` | Enough to re-verify the accepted index later without re-running the chain; no secret, no absolute path, no free text. |
| Identity of acceptance | the accepted record's own content is sealed by `artifact_checksum`; a replay of the same `index_fingerprint` is a no-op, a replay of a **different** payload under the same `manifest_id` is `IDEMPOTENCY_CONFLICT` | G-4 without a second identity namespace. |
| Contract v1 status | never registered, never a parent, never a `data` payload of a registered artifact | `E3-NEG-038`, `E3-NEG-039`. |
| Removal | only by an explicit supersession (a later successful acceptance) or by workspace teardown | No implicit deletion. |

A `PARTIAL` candidate may be accepted and recorded with `status: PARTIAL`. It is
recorded; it is never reported as a complete index, and `counts` lets a consumer
see the rejected documents without opening the sidecar (G-7, `E3-NEG-042`).

### 6.4 Publication is all-or-nothing

Steps 1–6 leave the previous accepted state untouched. Step 7 is a single
transaction over exactly two durable writes plus one delete:

1. the accepted E3 record (`rag/index/accepted.json`), and
2. one appended line in `audit/journal.jsonl`.

Both are prepared, then committed; if the audit append fails, the accepted record
is rolled back and the run reports `ATOMIC_COMMIT_FAILED` with the last known
complete index still visible (`E3-NEG-044`, `E3-NEG-020`). The commit intent of
`§7.3` is removed only after both writes are durable. A partially written
`accepted.json` is detected on the next run by its own `artifact_checksum` and is
treated as absent, never as a truncated truth.

### 6.5 Rejection is total and quiet

A rejection at any step:

- writes **no** accepted record and **no** success audit event;
- performs **no** Contract v1 registry mutation;
- leaves the previously accepted index exactly as it was;
- records the refusal in the kit's own run report (not the journal), with the code
  from `§4.5` and the failing step;
- returns a typed refusal through the same result model as a success, so a client
  cannot mistake an exception for a refusal or a refusal for a partial success.

A failed *re-index* additionally leaves the staging area and the commit intent in
place for `§7.5` recovery. A failed *first* index leaves the backend empty, which
is a correct state: an absent index and a stale index are different claims and the
harness must be able to tell them apart.

### 6.6 The canonical audit event

One event, appended by the adapter, using the canonical vocabulary from
`.agents/skills/workspace-manager/SKILL.md` and the existing uppercase action
convention (`RAG_INDEX_BUILT` is already in use at `tools/scholar-rag-kit/src/scholar_rag/indexer.py:142-157` and
`docs/kits_surface_matrix.md:379`).

| Field | Value |
|---|---|
| `action` | `RAG_INDEX_BUILT` on success; `RAG_INDEX_REJECTED` on a refusal. Both are new *actions* in the same uppercase convention, never a new `status` vocabulary. |
| `workspace_id` | the accepted parent's |
| `run_id` | the indexing run |
| `parent_artifact_id`, `parent_artifact_sha256` | the accepted `document_manifest` |
| `manifest_id`, `manifest_path`, `artifact_checksum` | workspace-relative sidecar reference |
| `index_fingerprint`, `chunk_set_fingerprint`, `configuration_fingerprint`, `production_fingerprint` | the four deterministic tokens |
| `protocol_fingerprint`, `corpus_fingerprint` | the parent's |
| `counts` | accepted documents, rejected documents, visible chunks |
| `rejected_documents` | `{document_id, code}[]` — never free text |
| `embedding_identity` | `{provider, model, dimension, distance_metric}` |
| `configuration` | the chunker configuration object |
| `failing_step`, `code` | present only on `RAG_INDEX_REJECTED` |
| **never** | an absolute path, a `db_path`, a secret, a bearer token, an environment value, a timestamp-derived identity, or a free-text success claim |

This is the field set `RAG-013` demands and the current event lacks (`§1.4` #14,
`E3-NEG-037`). A journal write error is never suppressed
(`E3-NEG-025`); the run fails and the index stays unpublished.

## 7. Replacement, atomicity, recovery, and legacy stores

### 7.1 The seven replacement steps

Readiness baseline `§7`, mapped to concrete ownership. The public semantics and the
fixtures are **backend-neutral**: a non-Chroma backend must be able to satisfy the
same assertions with different mechanics, and the tests are written against the
semantics, not against Chroma.

| # | Step | Owner | Postcondition |
|---|---|---|---|
| R1 | Validate parent lineage and **all** configuration before any backend mutation | adapter | Nothing written; a mismatch is `E3-NEG-017`/`E3-NEG-043`/`E3-NEG-049` |
| R2 | Build the complete candidate chunk set in staging | kit | Staging holds the whole new set; partial staging is `E3-NEG-044` |
| R3 | Embed and verify the candidate set | kit | Every candidate chunk has an embedding of the declared dimension and a stored `chunk_id` |
| R4 | Write a recoverable commit intent | kit | `rag/index/<run_id>/commit-intent.json` names parent, old manifest, new manifest, and the intended visible set |
| R5 | Atomically switch visibility to the new complete set | kit | Readers see the old complete set or the new complete set, never a mixture (`E3-NEG-044`) |
| R6 | Remove obsolete chunks belonging to the same canonical document | kit | A shortened document leaves no old chunk retrievable (`E3-NEG-032`) |
| R7 | Publish the manifest and the audit event only after the visible set matches | adapter | Check 6 then check 7 of `§6.2`; a mismatch is `BACKEND_STATE_INCONSISTENT` |

**The visibility switch is the only non-reversible moment**, so it is designed to
be non-destructive on the way in: R5 is a pointer move (or a set-level marker
change), never an in-place edit of the visible set. R6 then removes what the
pointer no longer covers, and R6 is idempotent — running it twice removes nothing
the second time. A crash between R5 and R6 leaves a *superset*, and `§7.5` knows
that a superset with a committed pointer is recoverable garbage, not corruption.

### 7.2 Idempotency is a fingerprint claim, not a boolean

A no-op re-index is detected **before** any backend mutation, by comparing
`index_fingerprint` against the accepted record. Equality means: report `REUSED`,
write the sidecar with new `run_id`/`created_at`/seal only, and mutate nothing
else. `E3-NEG-001` (the `§5.1` replay limb) asserts the deterministic projections are
byte-identical, so "identical" means identical at the byte level, not "no exception
raised".

A *replay* — the same `manifest_id` with a different non-volatile payload — is
`IDEMPOTENCY_CONFLICT` (`E3-NEG-054` class `C-22`), never an overwrite. This is
the same frozen code the rest of Contract v1 uses, so a caller does not have to
learn a second conflict vocabulary.

### 7.3 The commit intent

`rag/index/<run_id>/commit-intent.json` is written before R5 and removed after
check 7. Its own content is sealed the same way a sidecar is, and it records
enough to finish or abandon the run: parent reference and hash, the previously
accepted `manifest_id`, the candidate `manifest_id`, the complete intended visible
chunk set, the configuration fingerprints, the intended visibility-switch mode, and
`created_at`. It carries no absolute path. An abandoned intent is never silently
deleted: it is removed by an explicit recovery run that also records why.

### 7.4 Concurrency

Two runs must not interleave their visibility switches. The kit takes a
workspace-scoped lock at R1 and holds it through check 7, and a
**same-document** second run is refused with `CONFLICT` (frozen `ErrorCode`) rather
than queued, so a caller is told the truth instead of waiting on a stale snapshot.
A **different-document** run is refused as well — a workspace has one evidence
index, and two concurrent complete sets are not a thing that can be published.
Both are `E3-NEG-052`. The lock file is workspace-relative and contains no secret;
it is not a publication boundary and its absence is not treated as authority.

### 7.5 Recovery is deterministic and ownership-safe

On start, a run inspects `rag/index/<run_id>/` before touching the backend:

| Observed | Meaning | Action |
|---|---|---|
| no commit intent | nothing was in flight | proceed from R1 |
| intent present, no accepted record for the candidate, backend still on the old pointer | crash before R5 | roll back: delete staging, remove the intent, record `RAG_INDEX_REJECTED` with `ATOMIC_COMMIT_FAILED` |
| intent present, accepted record present for the candidate | crash between the two writes of check 7 | roll **forward**: re-append the audit event, then remove the intent |
| intent present, backend on the new pointer, accepted record absent | crash between R5 and check 7 | roll **forward** if the live set matches the candidate, else roll back by restoring the old pointer and re-removing; never leave a mixture |
| intent present, backend is a superset of the candidate with the new pointer | crash between R5 and R6 | re-run R6 (idempotent), then roll forward |

Recovery never guesses. Every branch is decided by facts the run reads, and every
branch ends in either a complete old index or a complete new index. Ownership-safe
means a run may only recover an intent whose `parent_artifact_ref` matches the
currently accepted parent; an intent from a superseded parent is abandoned, not
replayed. `E3-NEG-044` covers each row.

### 7.6 Legacy stores

A store is **legacy** when it holds chunks that cannot be re-derived under `§5.1`:
lower-case `chk-*` ids, `chk-<n>` ordinals, no `document_manifest` parent, no
embedder identity, or a schema version the E3 code cannot enforce.

1. **Detection** is automatic and read-only. Any read of a legacy store marks it
   legacy in the run report; there is no configuration that turns detection off
   (`E3-NEG-045`).
2. **Default read-only.** A legacy store is never used as an authoritative index,
   never counted as evidence, and never contributes a paper-level scientific
   count. A request to index into it is refused with `LEGACY_STORE_READ_ONLY`.
3. **Dry run first.** The migrator has a mandatory dry-run mode that reports the
   proposed chunk set, the proposed `index_fingerprint`, and every document it
   would refuse, and **writes nothing** to the backend.
4. **Manifest before commit.** The commit mode writes the new sidecar and its
   commit intent and only then switches visibility. There is no in-place
   migration path at all: a legacy store is migrated by re-indexing from the
   accepted parent, never by mutating historical rows (`E3-NEG-046`,
   readiness baseline `§10`).
5. **Refused documents are visible.** Anything the dry run would refuse appears in
   `rejected_documents` with a code; nothing is dropped silently.

Because migration re-derives identity from the accepted parent rather than
reusing legacy ids, a migrated index contains **no** legacy identity. That is the
observable difference between a migration and a copy, and it is what `E3-NEG-046`
asserts.

## 8. Implementation task packet

Tasks are ordered by dependency, and each names its owner repository, its
acceptance criteria, and its gates. A task may not start before the tasks it
depends on are merged. `T-00` is this document.

| ID | Task | Repo | Depends on | Criteria | Gate |
|---|---|---|---|---|---|
| `T-00` | This handoff: sidecar schema, identity rules, chain, ledgers, gates | harness | — | all | `§11.4` spec gate; independent review |
| `T-10` | Frozen primitive parity: ship a byte-equivalent canonical module in the kit and prove parity with the harness helper | `scholar-rag-kit` | `T-00` | `E3-001` | `E3-NEG-047` |
| `T-20` | Chunk identity: replace `generate_deterministic_chunk_id` with the `§5.1` rule; delete the fallback chain and the positional ids | `scholar-rag-kit` | `T-10` | `E3-001`, `E3-002` | `E3-NEG-001`…`008`, `E3-NEG-033`, `E3-NEG-051` |
| `T-30` | Identity is explicit: require `workspace_id`, `document_id`, `study_id`, parent, backend, and collection as request fields or inherited from the recorded workspace manifest; remove title / `project.json` / CWD inference and frontmatter re-binding | `scholar-rag-kit` | `T-20` | `E3-002`, `E3-004` | `E3-NEG-010`, `E3-NEG-011`, `E3-NEG-012`, `E3-NEG-026`, `E3-NEG-029` |
| `T-40` | Closed chunker configuration: implement or deprecate `min_chunk_chars`; record the full effective set; reject an unrecognized or inert key | `scholar-rag-kit` | `T-20` | `E3-013` | `E3-NEG-027`, `E3-NEG-024` |
| `T-50` | Index Manifest v1 sidecar: typed closed model, `§5.2` stage order, `§4.3` validation, sorted arrays, `deterministic_projection` | `scholar-rag-kit` | `T-30`, `T-40` | `E3-005`, `E3-006` | `E3-POS-001`…`004`, `E3-NEG-018`, `E3-NEG-019`, `E3-NEG-042` |
| `T-60` | Replacement protocol: R1–R7, commit intent, atomic visibility switch, obsolete removal, idempotency, concurrency lock | `scholar-rag-kit` | `T-50` | `E3-010` | `E3-NEG-001`, `E3-NEG-032`, `E3-NEG-043`, `E3-NEG-044`, `E3-NEG-052`, `E3-NEG-054` |
| `T-70` | Recovery state machine and the legacy read-only + dry-run/commit migrator | `scholar-rag-kit` | `T-60` | `E3-009`, `E3-010` | `E3-NEG-044`, `E3-NEG-045`, `E3-NEG-046` |
| `T-80` | Backend verification query: exact visible-set proof, count, metadata, embedding identity | `scholar-rag-kit` | `T-50` | `E3-012` | `E3-NEG-023`, `E3-NEG-024`, `E3-NEG-043` |
| `T-90` | Typed service parity: one request/result model behind the Python API and the CLI; replace free-text success/failure with typed results; explicit journal path; no suppressed write errors | `scholar-rag-kit` | `T-50`, `T-80` | `E3-008`, `E3-011` | `E3-NEG-025`, `E3-NEG-040`, `E3-NEG-041` |
| `T-95` | Remove false contract language from the indexing surface: no `VERIFIED`/`ENTAILED` from a cosine score, no fabricated `chk-<n>`, no off-grammar token, no claim that a stored option is effective | `scholar-rag-kit` | `T-50` | `E3-003`, `E3-006` | `E3-NEG-033`, `E3-NEG-034`, `E3-NEG-036` |
| `T-100` | MCP boundary: declared-unsupported adapter, or full parity if the boundary is later lifted | `scholar-agent-kit` | `T-90` | `E3-008` | `E3-NEG-040`, `E3-NEG-041` |
| `T-110` | Declared dependencies: every package on an authoritative path is declared in the kit and reachable from the metapackage | `scholar-rag-kit`, `scholar-agent-kit` | `T-90`, `T-100` | `E3-012` | `E3-NEG-048` |
| `T-120` | Harness synchronization: vendor the exact merged commits, bump the full-SHA `plugins.json` pins, regenerate the metapackage pins, update the surface matrix and the skill mirrors | harness | `T-100`, `T-110` | `E3-014` | `E3-NEG-047`, `§11.2` pin checks |
| `T-130` | E3 acceptance adapter: the seven checks of `§6.2`, the accepted record, the atomic publication, the canonical audit event | harness | `T-120` | `E3-007`, `E3-012` | `E3-NEG-016`, `E3-NEG-017`, `E3-NEG-020`, `E3-NEG-049` |
| `T-140` | Harness conformance: the golden manifest shared byte-for-byte with the kit, the negative ledger, the mutation tests, the packing/isolation tests | harness | `T-130` | all | `§11.4`; `E3-POS-005` |
| `T-150` | Surface-matrix and documentation correction, including the `upsert`-idempotent / re-index-not-replacement warning | harness | `T-120` | `E3-014` | review |

`T-150` is not cosmetic: `docs/kits_surface_matrix.md:355-359` is currently
accurate and must stop being accurate in the same PR that makes replacement real,
or the documentation becomes wrong in the dangerous direction.

## 9. The MCP boundary

### 9.1 Decision: declared unsupported, with a typed refusal

E3 declares the **indexing surface unsupported over MCP** for this packet,
following the E1 and E2 precedent in the agent kit. This is a deliberate boundary,
not an omission:

- the current MCP indexing tool does **not** omit workspace identity, and the
  distinction matters for the fix. `nexus_rag_index` declares an optional
  `workspace_id: str = None` (`tools/scholar-agent-kit/src/scholar_agent/server.py:779`) and forwards it to
  `index_directory` (`tools/scholar-agent-kit/src/scholar_agent/server.py:794-796`), so the parameter exists. What it cannot
  do is make that identity **authoritative**: the kit silently replaces an absent
  value with `project.json`'s `project_id` or `title` (`tools/scholar-rag-kit/src/scholar_rag/indexer.py:203-204`), so
  the caller cannot state a verified workspace, cannot pass the accepted parent,
  cannot pass the embedder identity, and cannot express a `PARTIAL` result. It also
  hard-codes `db_path="./chroma_db"` and returns free-text success/failure strings
  (`§1.4` #18, `tools/scholar-agent-kit/src/scholar_agent/server.py:774-799`). The boundary is therefore a *silent*
  substitution, which is exactly the failure mode a declared refusal prevents;
- adding parity requires the shared service of `T-90` to land first, and `T-100`
  follows it by design;
- an *undeclared* surface that silently diverges is worse than a declared refusal
  (`RAG-014`, `E3-NEG-040`).

### 9.2 The required shape

1. The capability is **declared** in the agent kit's capability list with
   `mcp_supported: false` for indexing, plus a one-line reason.
2. Any attempt returns the deterministic `UNSUPPORTED_CAPABILITY` envelope — the
   same error family the agent kit already uses for out-of-scope tools — not a
   free-text string, a partial result, or a silent success.
3. The refusal names the supported alternative: the Python API and the CLI, both
   behind the shared service from `T-90`.
4. The refusal is **identical** on every surface for the same request, so an agent
   cannot discover a different answer by switching transport (`E3-NEG-041`).
5. A retrieval MCP tool that would emit a citation token may only be wired up in
   the retrieval packet, against the grammar at `src/scholar_harness/contracts/models.py:19-21`; E3 does not add
   it and E3's tests must not claim it (`E3-003`).

### 9.3 What lifting the boundary requires

A follow-up PR in `scholar-agent-kit` that (a) depends on the merged `T-90`
service, (b) passes the same parity suite as the API and CLI with the *same*
fixtures, and (c) updates this section. Lifting the boundary is a change to this
handoff and needs review like any other.

## 10. Traceability: tests, ledger, and requirement matrix

This document is a **specification**. It does not claim that any test below exists
or passes. `§11` gives the commands that will prove it once the tasks land.

### 10.1 Positive tests

| ID | Assertion | Criteria | Where it lives |
|---|---|---|---|
| `E3-POS-001` | Every `chunk_id` in the golden manifest re-derives from the manifest's own fields via `§5.1` and validates against `src/scholar_harness/contracts/identifiers.py:36` | `E3-001` | `scholar-rag-kit` `tests/test_index_identity.py` **and** harness `tests/conformance/test_e3_index_lineage_boundary.py` — the same assertion over the same bytes |
| `E3-POS-002` | Stages A–I re-derive from the golden manifest, and the printed canonical input is byte-identical to `canonical_json_bytes` of its own parse | `E3-006` | the same two files |
| `E3-POS-003` | A no-op re-index produces a byte-identical `deterministic_projection` and a differing-key set of exactly `{run_id, created_at, artifact_checksum}` | `E3-010` | the same two files |
| `E3-POS-004` | A `PARTIAL` golden manifest validates: the three arrays are sorted, `counts` equal the array lengths, the chunk inventory and the per-document lists agree exactly, every id re-derives, and `status`/`detail` are consistent | `E3-005`, `E3-006` | the same two files |
| `E3-POS-005` | The kit and the harness agree, byte for byte, on the golden manifest fixture; the parity test fails if either drifts | `E3-014` | harness conformance + `E3-NEG-047` |
| `E3-POS-006` | Replacement: after a shortened-document re-index the live set equals the new manifest and no old chunk is retrievable; during the switch a concurrent reader sees one complete set or the other, never a mixture | `E3-010` | kit tests with a backend-neutral fake plus a Chroma-backed test |
| `E3-POS-007` | The acceptance chain refuses before step 7 at each of the seven failure points and proves zero publication: no accepted record, no registry mutation, no success audit event, last known complete index intact | `E3-007` | harness adapter tests over a temp workspace with a real journal |
| `E3-POS-008` | The audit event carries the full `§6.6` field set and contains no absolute path, secret, or free-text success claim | `E3-005`, `E3-007` | harness adapter tests |
| `E3-POS-009` | API, CLI, and MCP return the same typed result and the same error envelope for the same request; MCP returns `UNSUPPORTED_CAPABILITY` | `E3-008` | kit + agent-kit parity tests |
| `E3-POS-010` | Recovery: each row of the `§7.5` table, driven from a real interrupted run, ends in a complete old or a complete new index | `E3-010` | kit tests with fault injection |
| `E3-POS-011` | A legacy dry run writes nothing and reports its refusals; a legacy commit re-derives all identity and leaves no legacy id in the result | `E3-009` | kit tests over a seeded legacy store |
| `E3-POS-012` | The metapackage wheel answers `--help` on a minimal-dependency environment with every E3 import declared | `E3-012` | harness `tests/conformance/` plus the CI smoke |

### 10.2 Negative ledger - 35 failure classes covering `E3-NEG-001`...`E3-NEG-056`

The readiness baseline `§8` names **18** mandatory failure bullets. Normalizing
them into classes:

| baseline bullet | becomes |
|---|---|
| 1 - missing, malformed, unsupported, unaccepted, cross-workspace, or hash-stale parent | six classes, `C-01`...`C-06`, one per enumerated failure |
| 2 - protocol/corpus fingerprint mismatch | `C-08` |
| 3 - document or study absent from the accepted parent | two classes, `C-09`/`C-10` (**+1**) |
| 4 - changed extracted bytes at an unchanged path | `C-11` |
| 5 - path escape, symlink escape, wrong file type, unreadable or empty extraction | two classes, `C-12`/`C-13` (**+1**) |
| 6 - duplicate/colliding chunk id and cross-document collision | `C-14` |
| 7 - positional-id reuse after changed text | `C-15` |
| 8 - changed chunker configuration with reuse of an old manifest | `C-16` |
| 9 - changed embedding provider/model/dimension with reuse of an old collection | `C-17` |
| 10 - backend metadata corruption, missing chunk, extra obsolete chunk, or count mismatch | `C-18` |
| 11 - shortened re-index leaving an old chunk retrievable | `C-19` |
| 12 - partial embedding failure; interrupted staging, visibility switch, manifest/audit publication | two classes, `C-20`/`C-21` (**+1**) |
| 13 - concurrent same-document and different-document indexing | `C-22` |
| 14 - undeclared or ineffective configuration | `C-23` |
| 15 - nondeterministic file/backend iteration order | merged into `C-15`; it fails the same way - order reaching a fingerprint (**-1**) |
| 16 - API/CLI/MCP semantic or error-envelope divergence | `C-24` |
| 17 - similarity labelled verification or entailment | `C-25` |
| 18 - attempt to publish the sidecar as a Contract v1 artifact | merged into `C-03`; the same `UNSUPPORTED_ARTIFACT_TYPE` gate (**-1**) |

The arithmetic closes as `18 + 5 + 1 + 1 + 1 - 1 - 1 = 24` split-derived classes
(`C-01`...`C-06`, `C-08`...`C-25`). One further mandatory class is **added**, not
split: `C-07`, a wrong required parent type, which is a real acceptance-gate code
(`src/scholar_harness/contracts/acceptance.py:399-401`) that the baseline enumerates inside bullet 1's *category*
but does not name as one of its six failures. `24 + 1 = 25` mandatory classes
(`C-01`...`C-25`). `C-22` additionally carries the replay limb as a second assertion
inside one class, not as a twenty-sixth class.

Ten further classes (`C-26`...`C-35`) are required by the `RAG-0nn` rows this handoff
owns, by the `§5.1` limb battery, and by G-9, giving **35 classes** over **56**
negative IDs. No baseline bullet is dropped: every one of the 18 maps to at least
one class above.

Every one of the 56 IDs has at least one class below. An ID may appear under more
than one class only when the same assertion is checked at two different chain
steps; each such ID is still a single named test. Every class must prove **zero
authoritative publication** and a preserved last known complete index.

| # | Failure class | Code | Ledger IDs | Defends |
|---|---|---|---|---|
| C-01 | Parent missing or unreadable | `NOT_FOUND` | `E3-NEG-016` | G-1 |
| C-02 | Parent present but failing frozen-model validation (malformed) | `VALIDATION_ERROR` | `E3-NEG-015` | G-1 |
| C-03 | Parent `artifact_type` is not a Contract v1 type, or the sidecar is offered as one | `UNSUPPORTED_ARTIFACT_TYPE` | `E3-NEG-038` | G-8, §1.1 |
| C-04 | Parent absent from the registry (never accepted) | `MISSING_PARENT_ARTIFACT` | `E3-NEG-020` | G-1 |
| C-05 | Cross-workspace parent | `WORKSPACE_NAMESPACE_MISMATCH` | `E3-NEG-012` | G-1, G-3 |
| C-06 | Hash-stale parent (content changed after registration) | `PARENT_HASH_MISMATCH` | `E3-NEG-017` | G-1 |
| C-07 | Wrong required parent type | `REQUIRED_PARENT_TYPE_MISSING` | `E3-NEG-039` | G-1 |
| C-08 | Protocol or corpus fingerprint mismatch | `PROTOCOL_FINGERPRINT_MISMATCH` / `CORPUS_FINGERPRINT_MISMATCH` | `E3-NEG-049` | G-1 |
| C-09 | Document absent from the accepted parent | `VALIDATION_ERROR` | `E3-NEG-009` | G-1, G-2 |
| C-10 | Study absent from the accepted corpus/screening lineage | `VALIDATION_ERROR` | `E3-NEG-011` | G-1, G-2 |
| C-11 | Changed extracted bytes at an unchanged committed path with no re-index request | `EXTRACTED_CONTENT_CHANGED` | `E3-NEG-050` | G-2, G-7 |
| C-12 | Path escape, drive-letter or symlink escape, wrong file type, or unreadable extraction | `PATH_OUTSIDE_WORKSPACE` | `E3-NEG-021`, `E3-NEG-022` | G-3 |
| C-13 | Extraction empty or unusable after normalization | `EXTRACTED_TEXT_UNUSABLE` | `E3-NEG-035` | G-2 |
| C-14 | Duplicate/colliding chunk id, cross-document identity reuse, or a listed id that cannot be re-derived | `CHUNK_IDENTITY_COLLISION` | `E3-NEG-019`, `E3-NEG-018` | G-2 |
| C-15 | Positional-id reuse after changed text, nondeterministic file/backend iteration order reaching a fingerprint, or a locator that is not unique inside one document | `CHUNK_IDENTITY_COLLISION` / `VALIDATION_ERROR` / `LOCATOR_NOT_UNIQUE` | `E3-NEG-028` | G-2, G-6 |
| C-16 | Changed chunker configuration with reuse of an old manifest | `CONFIGURATION_INEFFECTIVE` | `E3-NEG-051` | G-4, G-6 |
| C-17 | Changed embedding provider/model/dimension with reuse of an old collection, or a durable embedding identity never recorded | `EMBEDDING_IDENTITY_CHANGED` | `E3-NEG-043`, `E3-NEG-026` | G-3, G-4 |
| C-18 | Live backend disagrees with the declared visible set: metadata corruption, missing chunk, extra obsolete chunk, or count mismatch | `BACKEND_STATE_INCONSISTENT` | `E3-NEG-023` | G-5 |
| C-19 | Shortened-document re-index leaving an old chunk retrievable | `BACKEND_STATE_INCONSISTENT` | `E3-NEG-032` | G-5, G-7 |
| C-20 | Partial embedding failure (some documents embedded, others not) | `BACKEND_STATE_INCONSISTENT` | `E3-NEG-044` | G-5, G-7 |
| C-21 | Interrupted staging, visibility switch, or manifest/audit publication, or an accepted record / success audit published without all seven checks | `ATOMIC_COMMIT_FAILED` | `E3-NEG-044`, `E3-NEG-020` | G-5 |
| C-22 | Concurrent same-document and different-document indexing, or a replay whose non-volatile payload changed under an existing `manifest_id` | `CONFLICT` / `IDEMPOTENCY_CONFLICT` | `E3-NEG-052`, `E3-NEG-054` | G-4, G-5 |
| C-23 | Undeclared or ineffective configuration: an inert stored option (`min_chunk_chars`), an undeclared sidecar field, or a durable identity/configuration value never recorded | `CONFIGURATION_INEFFECTIVE` | `E3-NEG-027`, `E3-NEG-024` | G-4, G-6 |
| C-24 | API, CLI, and MCP semantic or error-envelope divergence for the same request | `UNSUPPORTED_CAPABILITY` / `VALIDATION_ERROR` | `E3-NEG-040`, `E3-NEG-041` | G-8 |
| C-25 | Similarity labelled verification or entailment | `VALIDATION_ERROR` | `E3-NEG-036` | G-8 |
| C-26 | Chunk identity not stable or not sensitive: the `§5.1` limb battery - identical input not byte-stable, or a changed parent, study, document, extracted text, locator, heading, chunk text, chunker configuration, chunker algorithm version, or workspace namespace that fails to re-derive | `CHUNK_IDENTITY_COLLISION` | `E3-NEG-001`, `E3-NEG-002`, `E3-NEG-003`, `E3-NEG-004`, `E3-NEG-005`, `E3-NEG-006`, `E3-NEG-007`, `E3-NEG-008`, `E3-NEG-053`, `E3-NEG-055`, `E3-NEG-056` | G-2, G-3 |
| C-27 | Chunk identity out of scope: not unique within a study, or not globally unique in the collection | `CHUNK_IDENTITY_COLLISION` | `E3-NEG-030`, `E3-NEG-031` | G-2, G-3 |
| C-28 | Document/study identity re-derived instead of inherited: frontmatter re-binding its own chunk identity, or a DOI, OpenAlex id, filename, or legacy `paper_id` used as the primary identity | `VALIDATION_ERROR` | `E3-NEG-010`, `E3-NEG-029` | G-2 |
| C-29 | Status dishonesty: partial reported as complete, a mixed batch reported as `SUCCESS`, or a zero-accepted run reported as a success | `VALIDATION_ERROR` | `E3-NEG-042`, `E3-NEG-013`, `E3-NEG-014` | G-7 |
| C-30 | Emittable identity off-grammar: a fabricated or ordinal `chk-<n>` id, or a citation token in any form other than the registered `[rag:v2:<workspace_id>:<study_id>:<chunk_id>]` | `VALIDATION_ERROR` | `E3-NEG-033`, `E3-NEG-034` | G-8, G-9 |
| C-31 | Legacy store read as authoritative or migrated in place | `LEGACY_STORE_READ_ONLY` | `E3-NEG-045`, `E3-NEG-046` | G-8, G-9 |
| C-32 | Audit event field set incomplete, or carrying an absolute path, a secret, or a free-text success claim | `VALIDATION_ERROR` | `E3-NEG-037` | G-7 |
| C-33 | Journal path discovered by walking parent directories, or a suppressed journal write error | `DEPENDENCY_ERROR` | `E3-NEG-025` | G-3 |
| C-34 | An undeclared dependency on an authoritative path, or a clean-wheel import / `--help` smoke failure | `DEPENDENCY_ERROR` | `E3-NEG-048` | G-9 |
| C-35 | Kit canonical primitive, commit, vendored `tools/<kit>/` tree, or full-SHA pin drift | `BLOCKED_KIT_DRIFT` | `E3-NEG-047` | G-9 |

`C-26` and `C-27` are the two halves of G-2: `C-26` is stability and sensitivity
(determinism), `C-27` is scope (uniqueness). They fail differently - a collision
is a different defect from a non-deterministic re-derivation - so they are not
merged. `C-30` and `C-31` share G-8/G-9 but stay apart because the first is a
grammar failure and the second a store-migration failure; merging them, as an
earlier draft of this table did, would hide a migration defect behind a
token-format defect. `C-33` and `C-34` are separated for the same reason: a
journal discovered by directory walk and a missing declared package dependency
have different owners and different fixes.

### 10.3 Requirement matrix

Every `RAG-0nn` row is either owned by E3 with evidence, or explicitly not, with a
reason. No row is silently dropped.

| Row | E3? | Acceptance criteria | Positive | Negative |
|---|---|---|---|---|
| RAG-001 | yes | `E3-001` | `E3-POS-001` | `E3-NEG-001`…`008`, `E3-NEG-030`, `E3-NEG-031`, `E3-NEG-051`, `E3-NEG-053`, `E3-NEG-055`, `E3-NEG-056` |
| RAG-002 | yes | `E3-002` | `E3-POS-001` | `E3-NEG-029` |
| RAG-003 | yes | `E3-002` | `E3-POS-004` | `E3-NEG-009`, `E3-NEG-010`, `E3-NEG-011` |
| RAG-004 | emission only | `E3-003` | — | `E3-NEG-033`, `E3-NEG-034` |
| RAG-005 | negative only | — | — | `E3-NEG-036` |
| RAG-006 | negative only | — | — | `E3-NEG-036` |
| RAG-007 | no | — | — | retrieval / consensus packet |
| RAG-008 | no | — | — | retrieval / consensus packet |
| RAG-009 | no | — | — | retrieval / synthesis packet |
| RAG-010 | yes | `E3-004` | `E3-POS-004` | `E3-NEG-012`, `E3-NEG-026`, `E3-NEG-024` |
| RAG-011 | no | — | — | not allocated in the normative range |
| RAG-012 | yes | `E3-005`, `E3-006` | `E3-POS-002`, `E3-POS-004` | `E3-NEG-013`, `E3-NEG-014`, `E3-NEG-028`, `E3-NEG-042` |
| RAG-013 | yes | `E3-007` | `E3-POS-008` | `E3-NEG-037` |
| RAG-014 | yes | `E3-008` | `E3-POS-009` | `E3-NEG-040`, `E3-NEG-041` |
| RAG-015 | yes | `E3-009` | `E3-POS-011` | `E3-NEG-045`, `E3-NEG-046` |
| RAG-016 | no | — | — | matrix packet |
| RAG-017 | yes | `E3-010` | `E3-POS-003`, `E3-POS-006`, `E3-POS-010` | `E3-NEG-001`, `E3-NEG-032`, `E3-NEG-043`, `E3-NEG-044`, `E3-NEG-052`, `E3-NEG-054` |
| RAG-018 | yes | `E3-011` | `E3-POS-008` | `E3-NEG-025` |
| RAG-019 | yes | `E3-012` | `E3-POS-012` | `E3-NEG-048` |
| RAG-020 | yes | `E3-013` | `E3-POS-002` | `E3-NEG-027`, `E3-NEG-024`, `E3-NEG-051`, `E3-NEG-056` |
| RAG-021 | no | — | — | later packets |

`RAG-011` and `RAG-021` are listed as "no" for honesty rather than omitted: the
normative range is stated to contain `RAG-001`…`RAG-021`, and the handoff must
show that the gaps were looked at. A row E3 declines is a decision, not an
oversight.

## 11. Executable gates and validation

### 11.1 Environment

All commands run from the harness repository root through the project venv.
Never a system Python.

```powershell
uv sync
uv run python scripts/install_plugins.py   # editable kit installs into .venv
```

`uv sync` alone does **not** install the kits; a bare sync leaves
`scholar-rag`/`scholar-pdf`/… missing and every kit test uncollectable. The kit
suites are only meaningful after `install_plugins.py` has run.

### 11.2 Baseline-drift and pin gates (run before and after every PR)

These are the hard Contract v1 gates from `AGENTS.md`. A failure is
`BLOCKED_BASELINE_DRIFT`, and regenerating to make them pass is not a fix.

```powershell
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
uv run pytest tests/conformance -q
uv run ruff check scripts/
```

`generate_nexus_scholar_pins.py --check` is the metapackage freshness gate; it
reads `plugins.json` and must never be satisfied by hand-editing
`nexus_scholar_pins.json`. `test_count_freshness.py` enforces that every
`default_rev` is a full commit SHA and is merged — no floating branch, no unmerged
toolkit revision.

### 11.3 E3-specific gates

```powershell
# the sidecar schema and identity rules
uv run pytest tests/conformance/test_e3_index_lineage_boundary.py -q
uv run --directory tools/scholar-rag-kit run pytest tests/test_index_identity.py -q
uv run --directory tools/scholar-rag-kit run pytest tests/test_index_replacement.py -q
uv run --directory tools/scholar-rag-kit run pytest tests/test_index_legacy.py -q
uv run --directory tools/scholar-agent-kit run pytest tests/test_mcp_indexing_boundary.py -q
# the full harness suite at phase completion, not during development
uv run pytest -q
```

A network-free, backend-free reproduction of the golden values lives in `§5.5` and
is runnable straight from this document; it is the cheapest possible check that the
document and the frozen helpers still agree.

### 11.4 Definition of done for the E3 packet

E3 is done only when **all** of these hold. They are conjunctive.

| # | Gate |
|---|---|
| 1 | This handoff is independently reviewed and merged through the fork + PR gate (`.agents/skills/pull-request-gate/SKILL.md`). No direct push to `origin`. |
| 2 | The canonical `scholar-rag-kit` PR is **merged**, and its tests pass in that repository — not only in the vendored tree. |
| 3 | The canonical `scholar-agent-kit` PR (or the declared-unsupported boundary of `§9`) is **merged**. |
| 4 | `tools/scholar-rag-kit/` and `tools/scholar-agent-kit/` in this repo hold the **exact merged commits**, not a dirty approximation. |
| 5 | `.agents/plugins/nexus-scholar/plugins.json` `default_rev` for both kits is the resulting **full commit SHA**. |
| 6 | The metapackage pins are regenerated from `plugins.json`, never hand-edited, and `--check` passes. |
| 7 | All four generator `--check` commands in `§11.2` pass with no regeneration. |
| 8 | Every `E3-POS-*` and `E3-NEG-*` ID referenced in `§10` exists as a real test and passes. |
| 9 | Every row in `§10.3` marked "yes" has at least one passing test, and every row marked "no" is untouched by the E3 diff. |
| 10 | The `§5.5` reproduction passes against the merged kit commit's checked-in fixture. |
| 11 | `docs/kits_surface_matrix.md` and `.agents/skills/scholar-rag-kit/SKILL.md` describe the merged behavior, including the declared MCP boundary. |
| 12 | The E3 completion report of `§14` is merged with the merge SHAs and the command output. |

A vendored-only change is **not** done. A kit source change that exists only under
`tools/<kit>/` and not in the canonical repository is **not** done, no matter how
green the harness suite is (G-10).

## 12. Repository and stage ownership

The order is the readiness baseline `§9` order. Each step has its own PR; the
sequence is a dependency chain, not a preference.

| Step | Repository | PR contents | Must not contain |
|---|---|---|---|
| 1 | harness | this handoff only | any runtime change, any schema change |
| 2 | `scholar-rag-kit` (canonical) | `T-10`…`T-95`: candidate service, typed sidecar, replacement protocol, CLI/API behavior, legacy handling, focused tests | `scholar_harness` imports, journal writes, Contract v1 registry writes |
| 3 | `scholar-agent-kit` (canonical) | `T-100`, `T-110`: the declared MCP boundary and declared dependencies | a second, divergent implementation of indexing |
| 4 | harness | `T-120`…`T-150`: vendor the exact merged commits, bump full-SHA pins, regenerate metapackage pins, add the acceptance adapter, the conformance/golden/mutation tests, update the surface matrix and skill mirrors | a hand-edited pin file, a floating branch, a kit source edit that is not in the canonical repo |
| 5 | harness | the E3 completion report (`§14`) | new behavior |
| 6 | harness (E4) | adversarial mutation proof: PDF bytes, extracted bytes, chunking config, embedding identity, manifest lineage, live index contents | E3 scope creep |

Two rules bind this sequence:

- **No pin may target an unmerged toolkit revision.** Steps 4 and 5 are blocked
  until steps 2 and 3 are merged and their SHAs are known.
- **Kit source, canonical repo, vendored tree, and pin move together.** A change to
  `tools/<kit>/` that has no canonical-repo counterpart is drift, and drift fails
  gate 4.

Contributions follow the fork + PR gate: no feature branch is pushed to `origin`.
The pre-push hook (`scripts/hooks/pre-push`, enabled via
`git config core.hooksPath scripts/hooks`) enforces it.

## 13. Stop conditions and blocked labels

The following are **not** obstacles to be worked around. Each is a labelled stop,
and each label is part of the return contract.

| Condition | Label |
|---|---|
| A proposal to add `chunk_manifest` or `index_manifest` to Contract v1, or any other frozen-contract change, to make E3 convenient | `BLOCKED_CONTRACT_VERSION_DECISION` |
| A `generate_contract_*.py --check` failure that would need regeneration to pass | `BLOCKED_BASELINE_DRIFT` |
| An adapter inconvenience used as a reason to weaken a schema, a fingerprint rule, a sorted-array rule, or a status rule | `BLOCKED_CONTRACT_WEAKENING` |
| The canonical kit repository cannot be updated, or the merge SHA cannot be verified, so the vendored tree cannot be pinned | `BLOCKED_CANONICAL_REPO` |
| A required input is missing: no accepted E2 `document_manifest`, no workspace, no recorded workspace manifest, no parent hash | `BLOCKED_INPUT` |
| The task packet is under-specified for a safe bounded change | `BLOCKED_AMBIGUOUS_TASK` |
| A kit surface is changed but the vendored snapshot, the canonical repo, and `plugins.json` cannot all be updated in the same change | `BLOCKED_KIT_DRIFT` |
| A claimed test cannot be run hermetically (requires a network provider, a live model download, or a non-reproducible backend) | `BLOCKED_NON_HERMETIC_TEST` |

Three prohibitions that are stops rather than findings:

1. A green harness suite is **not** evidence that indexing works; the canonical kit
   suites are (G-10).
2. A successful `upsert` is **not** evidence that the visible set is correct, current,
   or complete. That is what `§6.2` step 6 exists to prove.
3. Silent journal-write suppression is **not** an acceptable degradation mode. It is
   `E3-NEG-025`, and the run fails.

## 14. E3 completion report

### 14.1 Residual risks this packet accepts

These are real, accepted consequences of the design above, not defects. They must be
restated verbatim in the completion report.

| # | Residual risk | Why it is accepted | Mitigation |
|---|---|---|---|
| R-1 | `producer.commit` participates in `index_fingerprint`, so upgrading the kit invalidates every accepted index even when the chunk set is identical | A different implementation commit is a different reproducibility claim; pretending otherwise would make the fingerprint lie about who produced the bytes | A `REUSED`-equivalent fast path compares `chunk_set_fingerprint` and `configuration_fingerprint` first and reports an explicit `reindex_required_for_producer_change` instead of silently re-deriving |
| R-2 | `artifact_checksum` is not run-invariant, because it seals the file as written | It is the E1 construction; a whole-file seal that ignored run identity would not be a seal of the file | Comparability is defined on `deterministic_projection` (§5.2) and asserted there |
| R-3 | `production_fingerprint` is an E3 field with no Contract v1 counterpart | Contract v1 has no index artifact to carry it; adding one is a v2 decision | It is a sidecar field only, and it feeds no stage that can cycle |
| R-4 | The atomic visibility switch is backend-dependent, so "atomic" is a property of the backend's own set-level operation | Readiness `§7` allows backend-specific mechanics with backend-neutral semantics | R5 is required to be a pointer/marker move, never an in-place edit; a backend that cannot do this is refused rather than approximated |
| R-5 | A legacy store cannot be migrated in place, so migration costs a full re-index from the accepted parent | Readiness `§10` forbids in-place migration; a cheaper path would reuse un-derivable identity | The mandatory dry run reports the cost and every refusal before anything is written |
| R-6 | The accepted E3 record is adapter-owned and non-Contract, so a consumer that only reads Contract v1 artifacts cannot see that an index exists | Contract v1 has no index artifact type; the baseline ratifies this boundary explicitly | The accepted record is workspace-local, content-sealed, and always paired with the audit event that names the same `manifest_id` |
| R-7 | `min_chunk_chars` must be implemented or removed, and either choice changes existing chunk boundaries for some workspaces | The option is currently inert, so "no change" is already false in spirit: the configuration claims an effect it does not have | The choice is a reviewed decision in the canonical PR; a deprecation warning is emitted and the option is absent from the recorded configuration afterwards |
| R-8 | The golden manifest is a fixture in two repositories, which is a drift surface | The parity test (`E3-POS-005`) fails on drift, and a single canonical source is generated into both | The §5.5 reproduction re-derives the digests from the document itself, so a hand-edited digest cannot pass review |
| R-9 | Rejecting indexing over MCP is a capability regression for any agent that used the current tool | The current tool cannot express the required identity or a `PARTIAL` result, so parity is not available to preserve | `§9` declares the boundary with a typed `UNSUPPORTED_CAPABILITY` refusal and names the supported alternatives |

### 14.2 What the completion report must contain

1. The canonical merge SHA of `scholar-rag-kit` and of `scholar-agent-kit`.
2. The `plugins.json` `default_rev` values after the bump, and the regenerated
   metapackage pin file — with the `--check` output proving freshness.
3. The output of every command in `§11.2` and `§11.3`, unedited.
4. The `§5.5` reproduction output against the **merged** kit fixture.
5. A coverage table: every `E3-001`…`E3-014` criterion against the test that proves
   it, and every `§10.2` class against its test.
6. The `§10.3` matrix with any change, and the reason for the change.
7. `§14.1`'s nine residual risks restated, plus any **new** risk discovered during
   implementation — a completion report that adds no new risk after a packet this
   size has not been read carefully enough.
8. An explicit statement of what E3 did **not** do: no retrieval, scoring, synthesis,
   consensus, claim verification, risk-of-bias, methodology-matrix, or agent-loop
   change, and no Contract v1 change.
9. The exact diff of `docs/kits_surface_matrix.md`, so a reviewer can confirm the
   `upsert`-idempotent / re-index-not-replacement warning was corrected rather than
   deleted.

### 14.3 The handoff to E4

E3's output is E4's input. When this packet is done, E4 must be able to mutate, from
the outside: the PDF bytes, the extracted bytes, the chunking configuration, the
embedding identity, the manifest lineage, and the live index contents — and observe
that each mutation is **detected** rather than absorbed. E4 does not need E3's
cooperation to do that; if it does, E3 has claimed an enforcement it does not have.
