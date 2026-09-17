# Scholar RAG Kit Remediation Specification

**Status:** Proposed  
**Date:** 2026-09-17  
**Owner:** scholar-rag-kit maintainers  
**Priority:** P0 correctness before retrieval-quality improvements  
**Scope:** `tools/scholar-rag-kit/`, its harness/MCP adapters, and cross-kit contracts

## Scientific claim boundary

This kit retrieves, groups, and presents evidence; it does not establish scientific truth. Embedding cosine, lexical overlap, graph authority, and seed boosts are ranking signals. They MUST NOT be named or reported as logical entailment, verification, causal support, consensus, or study quality. A claim is support-verified only by an explicitly named verifier with inspectable evidence and a recorded method/version. Absence from retrieval is not evidence of absence.

Canonical identity is mandatory: `workspace_id` identifies corpus scope; `study_id` identifies exactly one paper; `chunk_id` identifies one evidence unit within a study. None may substitute for another.

## Current architecture and data flow

Markdown plus frontmatter enters `ScholarIndexer.index_directory`, is chunked, embedded, and stored with metadata (`tools/scholar-rag-kit/src/scholar_rag/indexer.py:164-248`; `tools/scholar-rag-kit/src/scholar_rag/chunker.py:149-158,243-245`). `ScholarRetriever.query` filters Chroma, converts distance into similarity, optionally blends PageRank and seed boosts, and emits citation tokens (`tools/scholar-rag-kit/src/scholar_rag/retriever.py:167-279`). `GroundedSynthesisEngine` prompts a generator, extracts claims and citations, scores claim/chunk vectors, and emits synthesis artifacts (`tools/scholar-rag-kit/src/scholar_rag/synthesis.py:62-220,271-329`). Consensus and matrix modules consume those claims downstream.

## Confirmed findings

1. Identity is conflated. Indexing may derive `workspace_id` from project title (`indexer.py:203-204`); citation tokens choose `workspace_id` before paper identifiers (`retriever.py:123-131`); synthesis assigns `study_id` from `workspace_id` before `paper_id`/filename (`synthesis.py:197-220`); methodology rows repeat the same fallback (`synthesis.py:359-363`). This can collapse every paper in one corpus into one study.
2. “Entailment” is embedding similarity. `verify_claim_entailment` computes maximum cosine and maps it to VERIFIED/AMBIGUOUS/UNSUPPORTED (`synthesis.py:112-148`); model fields expose `entailment_score/status` as if verified (`models.py:193-206`). Semantic proximity cannot detect negation, direction, qualifiers, or unsupported numerical claims.
3. Retrieval joins PageRank by DOI, paper_id, or filename fallbacks (`retriever.py:235-255`) rather than one canonical `study_id`, making boosts dependent on incidental metadata.
4. Citation tokens encode a fallback identity chain headed by workspace scope (`retriever.py:123-131`), so tokens are not reliably paper-addressable.
5. The MCP/API surface has historically diverged in graph-boost parameters and database paths; the current contract is documented in `docs/kits_surface_matrix.md:232-250`, and adapters must be kept parity-tested.
6. Indexer mutates the caller-level `workspace_id` while iterating when it is initially missing (`indexer.py:203-204`), allowing the first document manifest to influence later documents.
7. The standard methodology matrix fills absent evidence with plausible values such as `Design Science / Empirical`, `Evaluation Benchmark`, `Standard Corpus`, `Accuracy / F1`, `Proposed System`, and `Domain bounded` (`tools/scholar-rag-kit/src/scholar_rag/synthesis.py:354-376`). These defaults are presented as extracted study attributes rather than missingness markers.
8. Re-indexing only upserts the current deterministic IDs (`tools/scholar-rag-kit/src/scholar_rag/indexer.py:73`); chunks removed from a shortened/revised document are not deleted and can remain retrievable.
9. `matrix.py` imports protocol-kit at module import time (`tools/scholar-rag-kit/src/scholar_rag/matrix.py:15`), but protocol-kit is absent from runtime dependencies. `extractor.py` also uses `httpx` without a direct declaration, while other declared kit dependencies appear unused (`tools/scholar-rag-kit/pyproject.toml:13-25`).
10. Audit journal discovery differs by operation and retrieval starts from process CWD (`tools/scholar-rag-kit/src/scholar_rag/retriever.py:133-161`), allowing events to disappear or land outside the intended workspace.
11. `min_chunk_chars` is stored but unused (`tools/scholar-rag-kit/src/scholar_rag/chunker.py:19`), despite API documentation promising micro-chunk merging. Matrix fallback repeats the identical retrieval call (`tools/scholar-rag-kit/src/scholar_rag/matrix.py:129-149`), and consensus mutates caller-owned claims (`tools/scholar-rag-kit/src/scholar_rag/consensus.py:297`).

## Goals

- Make every stored and emitted evidence item traceable corpus -> paper -> chunk.
- Rename similarity-derived outputs truthfully and reserve entailment language for a real verifier.
- Make API, CLI, MCP, persisted metadata, and exported artifacts behaviorally equivalent.
- Reject ambiguous inputs instead of inventing identity, RQ, model, database, or provenance defaults.
- Preserve reproducibility through explicit algorithms, model versions, thresholds, and audit events.

## Non-goals

- Proving claims true, grading study quality, or inferring causality.
- Choosing a universal embedding model or threshold.
- Treating PageRank as evidential strength.
- Reconstructing missing paper identity from workspace names.

## Normative requirements

Requirement IDs: the numbered requirements below carry stable IDs `RAG-001`…`RAG-021`
(requirement *n* = `RAG-0nn`). Regression tests and the traceability ledger required
by `11_validation_and_test_plan.md` (VAL-001, §11–§12) MUST reference these IDs.

1. Every indexed chunk MUST carry non-empty `workspace_id`, `study_id`, and `chunk_id`; `chunk_id` MUST be unique within a study and the composite `(workspace_id, study_id, chunk_id)` MUST be globally unique in a collection.
2. DOI, OpenAlex ID, filename, and legacy `paper_id` MAY be aliases for resolving `study_id`; they MUST NOT replace it in persisted primary identity.
3. Indexing MUST fail with a structured per-document error when `workspace_id` or `study_id` cannot be resolved. It MUST NOT use title, filename, DOI, or `UNKNOWN` as an unlabeled semantic substitute.
4. Citation tokens MUST encode the canonical triple and a version, for example `[rag:v2:<workspace_id>:<study_id>:<chunk_id>]`. Parsers MUST validate all components. This token grammar SHALL be registered as the canonical evidence locator format in `10_cross_kit_contracts.md` §11 before consumers outside this kit (verify, agent, harness) rely on it.
5. Vector cosine MUST be named `semantic_similarity_score`; thresholds MUST produce labels such as `HIGH_SIMILARITY`, never `VERIFIED` or `ENTAILED`. The similarity-label vocabulary SHALL be added to the shared vocabulary in `10_cross_kit_contracts.md` §11 so that kit and contract documents never disagree on these labels.
6. An `entailment_status` MAY be emitted only when an explicit entailment/verbatim verifier ran; output MUST include verifier type, version, threshold, evidence offsets or quote, and failure reason.
7. Synthesis MUST preserve all supporting study IDs for a claim. It MUST NOT select the first study and discard the remainder.
8. Consensus counts MUST deduplicate by canonical `study_id`; multiple chunks/claims from one paper MUST NOT count as independent studies.
9. Hybrid scoring MUST expose raw distance, normalized similarity, PageRank, seed indicator, alpha, beta, and final score. PageRank MUST join exclusively through canonical `study_id` after alias resolution.
10. `workspace_id`, `rq_id`, collection/database path, embedding provider/model, graph source, alpha, and beta MUST be explicit at execution boundaries or inherited from a recorded workspace manifest. No invented `RQ1`, CWD database, model, or corpus identity is allowed.
11. Missing optional boosts MUST mean “disabled,” not silently defaulted to an undocumented value. Any retained compatibility default MUST be surfaced in output provenance and deprecation warnings.
12. Indexing and synthesis MUST write atomic artifacts and machine-readable failure manifests; partial success MUST not be reported as complete success.
13. Audit events MUST record input fingerprints, corpus/study/chunk counts, rejected documents, embedding identity, scoring configuration, and artifact paths without storing secrets.
14. API, CLI, and MCP MUST share one typed request/result service layer and parity tests.
15. Existing collections lacking canonical identities MUST be read-only until migrated or explicitly indexed in legacy mode; legacy mode MUST never emit paper-level scientific counts.
16. Missing methodology/evidence values MUST remain null with a typed `missing_reason`; no domain-plausible default may be emitted as observed evidence.
17. Re-indexing a study MUST implement replacement semantics: stage the new chunk set, delete obsolete chunks for that `study_id`, then atomically expose the replacement. Identical re-indexing MUST be idempotent.
18. Audit/workspace path MUST be explicit in public requests or resolved from a recorded workspace manifest, never discovered from process CWD.
19. Every direct runtime import MUST be declared and verified by an isolated install/import test; unused kit dependencies SHOULD be removed.
20. Public configuration such as `min_chunk_chars` MUST either affect behavior as documented or be removed/deprecated. Fallback retrieval MUST differ intentionally or be eliminated.
21. Consensus and matrix operations MUST NOT mutate caller-owned claim/input models.

## API, data, and CLI behavior

Introduce versioned `EvidenceIdentity`, `IndexedChunkV2`, `RetrievalScoreV2`, and `ClaimSupportV2` models. `index_directory` returns counts plus per-file failures, not only a scalar count. `query` accepts one request object containing explicit corpus and scoring configuration. `synthesize` accepts canonical retrieval results and separates `semantic_alignment` from optional `verification`.

CLI commands MUST support `--workspace-id`, a study-ID manifest/mapping, explicit `--db-path`, `--embedding-provider`, `--embedding-model`, and `--json`. Missing required identity exits non-zero. `--legacy-identities` is opt-in and emits a warning. MCP accepts the same fields and returns the same schema.

## Migration and backward compatibility

- Add schema version 2 collections; do not rewrite v1 in place.
- Provide a dry-run migrator that maps DOI/OpenAlex/legacy paper_id to `study_id`, reports collisions/unresolved rows, and writes a manifest before committing.
- Read v1 results through an adapter that marks `identity_quality=legacy_ambiguous`; prohibit consensus study counts until migrated.
- Retain old field names for one release as deprecated aliases. `entailment_score/status` derived from cosine become `semantic_similarity_score/label`; never silently reinterpret historical values as verified entailment.
- Regenerate citation tokens during migration and preserve old-to-new token mapping.

## Work plan

### P0

1. Implement canonical identity models, validation, composite IDs, and v2 storage.
2. Remove workspace-as-study fallbacks from indexer, retriever, synthesis, matrix, and consensus.
3. Rename cosine “entailment” fields and statuses; gate genuine verification behind an explicit verifier result.
4. Version citation tokens and emit complete multi-study support.
5. Remove invented methodology defaults and add typed missingness with evidence provenance.
6. Implement study-scoped replacement indexing so obsolete chunks cannot survive.

### P1

1. Build safe v1 -> v2 dry-run/commit migration with collision reports.
2. Unify API/CLI/MCP request/result paths and graph-boost/database-path parity.
3. Add atomic writes, partial-failure manifests, and richer audit records.
4. Join graph authority by canonical study identity and expose score decomposition.
5. Make audit/workspace location explicit and correct runtime dependency metadata.

### P2

1. Calibrate retrieval/verification separately on labeled corpora.
2. Add collection/model compatibility checks and reproducibility manifests.
3. Improve observability, performance bounds, and deterministic batch behavior.
4. Implement or retire dead chunking configuration, remove duplicate matrix queries, and avoid input mutation.

## Failure-focused test matrix

| Area | Cases | Required assertion |
|---|---|---|
| Identity | missing workspace; missing study; same DOI aliases; duplicate chunk; two papers in one workspace | reject ambiguity; no cross-paper collapse |
| Migration | clean v1; collisions; unresolved filename; interrupted commit | dry-run exact; atomic rollback; mapping retained |
| Citation | malformed token; delimiter characters; stale v1 token; cross-workspace lookup | strict parse; correct triple; no leakage |
| Similarity | paraphrase; negation; reversed comparison; unsupported number; unrelated high-overlap text | similarity never labeled verified/entailed |
| Verification | verifier absent/error/timeout; quote mismatch; multiple evidence units | explicit unavailable/error; provenance retained |
| Retrieval | no graph; missing graph node; alias mismatch; alpha/beta boundaries; NaN distance | deterministic decomposition; validation failure where invalid |
| Consensus | many chunks from one paper; duplicate claim; unknown study | one vote per study; unknown rejected/quarantined |
| Storage | corrupt Chroma metadata; embedding dimension mismatch; partial batch; concurrent index | no silent overwrite; recoverable manifest |
| Replacement | document loses sections/chunks; identical re-index; interrupted replacement | obsolete chunks removed; idempotent exact set; old complete set survives interruption |
| Missing evidence | no paradigm/dataset/metric/baseline/limitation in source | null + typed missing reason; no plausible fabricated value |
| Surface parity | Python/CLI/MCP equivalent request | equivalent schema, defaults, paths, exit/error semantics |
| Audit | success, partial, failure, secret-like API key | complete event; secrets redacted |
| Input immutability | consensus/matrix invoked twice on same objects | caller objects unchanged; deterministic output |

## Definition of done

- All P0 requirements and failure tests pass on Python 3.11/3.12 and supported OSes.
- No production path derives `study_id` from `workspace_id` or labels cosine as entailment.
- No matrix or synthesis path replaces absent evidence with invented methodology values.
- Re-indexing a shortened study leaves no stale chunks.
- A two-paper/one-workspace fixture retains two study identities through index, retrieval, synthesis, consensus, and matrix export.
- Migration is dry-run-first, collision-safe, atomic, and documented.
- API/CLI/MCP parity and schema-version tests pass; full harness suite passes.
- Scientific docs explicitly state that similarity and PageRank are retrieval signals, not proof.

## Dependencies and risks

Depends on graph-kit emitting canonical `study_id` nodes and protocol-kit supplying explicit extraction/RQ contracts. Verify-kit integration is required for genuine support verification. Risks include breaking persisted Chroma collections, citation-token consumers, and historical reports; versioning and read-only adapters mitigate these risks.

## Documentation updates

Update `tools/scholar-rag-kit/README.md`, `docs/api_reference.md`, `docs/tutorial.md`, the harness surface matrix, MCP tool docs, artifact schemas, and migration guide. Include identity examples, score decomposition, explicit non-entailment language, failure semantics, and one end-to-end corpus/study/chunk example.
