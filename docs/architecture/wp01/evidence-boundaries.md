# WP-01 evidence boundaries — implemented rules

> **What this is.** The implemented acquisition / extraction / indexing /
> currentness boundaries of the Contract v1 adoption (WP-01), consolidated from
> the former E1–E4 handoff packets (removed in the 2026-10-12 cleanup; the full
> packets remain in git history).
>
> **Where authority lives.** The frozen contract set
> (`docs/architecture/wp01_contract_adoption_handoff.md`,
> `docs/architecture/wp01_packet_c_reference.md`,
> `docs/architecture/cross_kit_contract_v1.md`,
> `docs/architecture/contract_v1_baseline.md`), the normative per-kit
> requirements (`specs/deep-audit-remediation-2026-09-17/`), and the
> conformance tests are the normative sources. This document records **what the
> implementation does**; if it disagrees with those sources, they win.

## Ownership model (all three boundaries)

| Owner | Responsibility |
|---|---|
| **Canonical kit** | Owns the domain implementation and its kit-local sidecar; never imports `scholar_harness`, never writes the Contract registry, never claims its candidate was accepted. |
| **Harness** | Sole owner of Contract acceptance and publication: loads the accepted parent through the frozen registry, re-verifies identity/fingerprints, publishes the accepted record and the canonical audit event. Never re-implements kit internals. |
| **Agent kit (MCP)** | Declares the authoritative operation **unsupported** on MCP (capability `pdf_extraction`, rejection code `UNSUPPORTED_CAPABILITY`) and rejects it **without I/O**, naming a truthful authoritative alternative. |

---

## E1 — acquired-document boundary

**Governing invariants** (normative; preserved from the packet):

1. `study_id` comes from the accepted screening/corpus lineage; the PDF kit never mints or infers it from DOI, title, filename, URL, or array position.
2. A path is a location, not document identity.
3. `source_sha256` is computed from the bytes that were actually validated.
4. A reusable document binds to the complete reuse tuple — not to a filename or a path that happens to exist.
5. Failure to resolve a legal OA copy is `UNRESOLVED`, never proof of a paywall.
6. No invalid, partial, HTML, identity-mismatched, or uncommitted file becomes authoritative output.
7. Publication is fail-closed and preserves every previously committed valid artifact and manifest.
8. A failed batch is a real machine-readable outcome: zero committed records means `FAILED`, never an empty `SUCCESS`.
9. Every committed path is relative to one caller-supplied canonical workspace root, serialized as a workspace-relative POSIX path.
10. Required tests use local fixtures and fake transports — no network.

**Input binding.** Each request is rejected *before* transport or filesystem I/O
when its parent or path binding is invalid: `workspace_id` must equal the
accepted parent and use the registered form; `workspace_root` is required,
absolute, caller-supplied, resolved and bound to the accepted `workspace_id`
(never inferred from CWD, title, DOI, or a relative path); `study_id` must be
included by the accepted screening decisions and exist in the accepted corpus
snapshot; `protocol_fingerprint`/`corpus_fingerprint` must equal both accepted
parents; `inputs` carries the exact artifact ID and SHA-256 of the direct
screening parent (recomputed with the harness canonical fingerprint function).
`doi` is an optional normalized lookup hint, never identity. `source_mode`
(`DISCOVERY` | `USER_PATH`) decides whether `source_path` is a permitted
read-only input; `USER_PATH` requires an `access_assertion` recording
`supplied_by` and `permission_basis` (no independent legal verification is
claimed).

**Manifest.** The kit-owned `pdf_acquisition_manifest` is published at the E1
convention `literature/acquisition/<run_id>/<ACQ-…>.json`; it is **not** a frozen
Contract v1 registry type. `AcquiredDocumentRecord` identity is the deterministic
`DOC-` id derived from validated bytes; the manifest embeds the `e2_reference`
path consumed by E2.

**Commit and recovery.** Publication follows the packet's commit state machine
with exact reuse binding (a reusable document binds to the full tuple), idempotent
replays, and recovery that never leaves a half-written authoritative state;
collisions are named rather than overwritten.

---

## E2 — extracted-text boundary

**Governing invariants** (normative; preserved from the packet):

1. `document_id` is **reused from the E1 manifest**; the recomputed value must equal it or extraction fails. E2 never mints a second identity rule.
2. A path is a location, not identity; a filename, DOI, title, or URL is not identity either.
3. `source_hash` is the E1 `source_sha256` of the exact validated bytes, re-verified before extraction.
4. Acquisition lineage is an **embedded, checksummed reference**, never a Contract v1 parent edge.
5. `VALID` means usable extracted text exists; `PARTIAL` means it exists and the degradation is explained; `FAILED`/`NEEDS_OCR` never carry a fabricated `extracted_path`.
6. A successful engine exit is not extracted text: a stub, empty, or placeholder body is a **failure**, not a partial success.
7. Every fallback is recorded with a reason; an unrecorded substitution is a failure of the record.
8. Publication is fail-closed: no `DocumentManifestArtifact` candidate without a committed extraction manifest; the harness publishes no candidate that fails `accept_artifact`; no extraction manifest exists without verified source bytes.
9. Committed paths are workspace-relative POSIX paths under the caller-supplied canonical root.
10. A failed batch is a real outcome: zero extracted records is `FAILED`, never an empty `SUCCESS`.
11. **Determinism:** the same accepted manifest, bytes, and requested engine produce the same `EXT-` id and the same candidate payload, independent of input order, attempt order, and wall-clock time.
12. Required tests are hermetic, scriptable, offline (local PDF fixtures; no network, no daemon, no sleep-dependent assertions).

**Sidecar and refusal.** The kit publishes the deterministic
`pdf-extraction-manifest-v1` (`pdf_extraction_manifest`, kit-owned, outside the
frozen registry) and constructs a **non-authoritative** frozen-Contract
`DocumentManifestArtifact` candidate. Changed extracted text under old E2
provenance is refused with **`STALE_EXTRACTED_BODY`**; replay of a changed body is
refused rather than re-published. Extraction emits `EXT-*` codes; frontmatter is
bound to the extraction (never invented).

---

## E3 — stable chunks and index-lineage boundary

**Governing invariants** (normative; preserved from the packet):

- **G-1 Parent-first.** Nothing is written to a backend before the accepted E2 `document_manifest` is loaded through the frozen registry, its declared `artifact_id`/hash verified, and its workspace/protocol/corpus bindings agreed. Failure ⇒ zero authoritative publication.
- **G-2 Identity is content, not position.** No chunk identity from filename, title, DOI, section slug, or ordinal alone. Different contents never share a `CHK-`; the same content under the same parent and configuration always does.
- **G-3 Namespace honesty.** Workspace, study, document, and chunk are four different things; none may stand in for another or be derived from a project title, directory name, or `project.json` field.
- **G-4 Replacement, not accumulation.** A re-index publishes exactly the new complete set; obsolete chunks of the same canonical document are removed, not left retrievable. An identical re-index is a no-op/reuse with byte-identical deterministic manifest content.
- **G-5 All-or-nothing publication.** The accepted E3 record and the canonical audit event are published together or not at all; any earlier failure leaves the last complete index visible and current.
- **G-6 Determinism is a property of the projection, not the run.** File enumeration order, backend iteration order, timestamps, run IDs, temporary names, process IDs, absolute paths, and secrets never influence a deterministic fingerprint.
- **G-7 Truthful status.** A partial success is `PARTIAL`; an empty successful result is not a success; a rejected document is visible with a code, never dropped.
- **G-8 No fabricated contract.** The sidecar is not a Contract v1 artifact; a lower-case chunk id, an off-grammar citation token, or a similarity labelled `VERIFIED`/`ENTAILED` is a refusal, not a value.
- **G-9 Kit/harness separation.** The canonical RAG kit never imports `scholar_harness`, never writes the registry, never claims acceptance. The harness adapter calls the kit's typed service and verifies its declared candidate.
- **G-10 Honest evidence.** A green harness suite is not evidence that indexing works; the canonical kit suites are.

**Acceptance chain.** The kit produces the typed, deterministic Index Manifest v1
sidecar with `CHK-` content identity. The bounded harness adapter
(`index-acceptance-v1`) runs **seven ordered checks** — parent load/verification,
fingerprint recomputation, and proof that the live backend holds exactly the
declared visible chunk set — and only then publishes the accepted record at
`rag/index/accepted.json` plus the canonical §6.6 audit event. With no accepted
`document_manifest`, Stage 6 refuses **before any backend** with
`DOCUMENT_MANIFEST_NOT_ACCEPTED`, leaving no `rag/chroma_db`.

**Refusal vocabulary observed in conformance:** `PATH_OUTSIDE_WORKSPACE`,
`PROTOCOL_FINGERPRINT_MISMATCH`, `BACKEND_STATE_INCONSISTENT`, `VALIDATION_ERROR`,
`RAG_INDEX_REJECTED` / `RAG_INDEX_RUN_REJECTED`, `DOCUMENT_MANIFEST_NOT_ACCEPTED`.

---

## E4 — evidence currentness (adversarial proof)

Six mutation cases plus a rebuild case were executed and merged (PR #77):

| Case | Observed |
|---|---|
| E4-NEG-001 | Changed PDF bytes ⇒ new ART lineage; Stage 6 FAILED with `RAG_INDEX_RUN_REJECTED`, no new manifest id; old E3 record stays historical. |
| E4-NEG-002 | Changed extracted text ⇒ E2 replay refused with `STALE_EXTRACTED_BODY`; Stage 6 preflight creates no backend. |
| E4-NEG-003 | Changed `max_chunk_chars` ⇒ moved fingerprints; stale declared digests refused at check 5. |
| E4-NEG-004 | Changed embedding model ⇒ moved index fingerprint; stale digests refused at check 5. |
| E4-NEG-005 | Changed protocol fingerprint ⇒ refused at check 3 with `PROTOCOL_FINGERPRINT_MISMATCH`. |
| E4-NEG-006 | Missing visible chunk ⇒ named by the typed verifier; replay refuses with `BACKEND_STATE_INCONSISTENT`. |

An unmodified replay succeeds without rewriting the accepted record or emitting a
new success event. The rebuild case constructs a **separate generation**; it does
**not** prove in-place migration of an existing review generation.

---

## Documented surface fact (cross-checked by conformance)

The MCP surface is 25 registered tools (22 `nexus_*` + 3 `recon_*`).

`tests/conformance/test_e2_extraction_boundary.py` asserts this number against the
live registry; `tests/conformance/test_mcp_tool_parity.py` and
`tests/conformance/test_count_freshness.py` assert the same surface. If a tool is
added or removed, the counts move together — a test update, never a contract
change.
