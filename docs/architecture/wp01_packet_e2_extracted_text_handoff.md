# Packet E2 — Extracted-Text Boundary

- **Status:** `COMPLETE` — closed on canonical harness main at
  `0fb665558e0808d66348476eda2c927439a96be1`; see
  `docs/architecture/wp01_packet_e2_completion_report.md`
- **Architecture owner:** Harness Contract v1
- **Implementation owner:** canonical `nexus-scholar-org/scholar-pdf-kit`
- **Declared MCP boundary owner:** canonical `nexus-scholar-org/scholar-agent-kit` (declaration/rejection adapter only)
- **Current PDF-kit pin:** `0430ee40c491edbb055af4ab068637275aada476`
- **Current agent-kit pin:** `deebfad995ba88bbd748be9beddd1aa2b8a51264`
- **Direct scientific parent:** accepted `ScreeningDecisionsArtifact` (the only Contract v1 parent type `document_manifest` may declare)
- **Required context:** the accepted E1 `AcquiredDocumentManifest` (`pdf-acquisition-manifest-v1`, `ACQ-*`) and the corpus/screening parent lineage it embeds
- **Frozen Contract v1 change required:** **none** (see §1.1)

## 1. Overview and supersession

E2 turns *validated PDF bytes* into *truthful extracted text* without ever
letting a path, a filename, or a successful HTTP/engine exit stand in for
identity, content, or lineage. It verifies the E1 acquisition manifest and the
exact committed source bytes, runs a declared extraction engine chain, records
what was requested and what actually happened, and only then constructs a
candidate for the **existing** Contract v1 `DocumentManifestArtifact`. A
bounded harness adapter owns acceptance, registry mutation, and authoritative
publication; the standalone PDF kit never imports `scholar_harness` and never
claims that its candidate was accepted.

E1 is acquisition; E2 is extraction. E1 deliberately did not emit
`DocumentManifestArtifact` because the frozen `DocumentRecord` is an
**extracted-content** record. E2 is the packet that finally makes that artifact
truthful, and it is the packet that must not make it *newer*.

### 1.0 Supersession

This handoff supersedes and replaces the extraction portion of the **“Packet E
— Downstream adapter stubs”** section of
`docs/architecture/wp01_contract_adoption_handoff.md` (that section is at
lines 116–132 of that document). The older handoff remains locked in the
Contract v1 baseline and is intentionally **not** edited. This handoff—not the
historical adapter-stub wording, and not the E1 acquisition wording—is
authoritative for E2 extraction, its provenance, and its surface boundaries.
E1's own handoff already fixed the E2 boundary language at §4.6 of
`docs/architecture/wp01_packet_e1_acquired_document_handoff.md`; this document
allocates it, names the identifiers, and makes every row checkable.

### 1.1 Frozen-contract boundary (no schema change)

E2 requires **no** Contract v1 schema, generated-schema, golden-fixture, or
baseline change. The frozen surface it must emit already exists:

| Frozen fact | Location |
|---|---|
| `DocumentRecord` = `document_id`, `study_id`, `source_hash`, `content_status`, `extracted_path`, `extraction_method` | `src/scholar_harness/contracts/models.py:472-510` |
| `document_id` is validated as `IdentifierKind.DOCUMENT` (prefix `DOC-`, opaque suffix) | `models.py:480-483`, `identifiers.py:18,35,47-53` |
| `source_hash` must be `sha256:<64 lowercase hex>` | `models.py:490-493` |
| `extracted_path` must be a workspace-relative POSIX path when present | `models.py:495-501`, `ArtifactReference.portable_workspace_path` (`models.py:152-169`) |
| `VALID`/`PARTIAL` **require** `extracted_path`; `FAILED`/`NEEDS_OCR` do not | `models.py:503-510` |
| `content_status` ∈ `VALID, PARTIAL, FAILED, NEEDS_OCR` | `models.py:124-128` |
| `extraction_method` ∈ `HUMAN, DETERMINISTIC_RULE, HEURISTIC, LLM, EXTERNAL_PROVIDER, COMPOSED` | `models.py:81-87` |
| `DocumentManifestArtifact.artifact_type == "document_manifest"`; `data.documents` ≥ 1, unique IDs | `models.py:513-525` |
| Envelope requires `schema_version` (1.x), `artifact_id` (`ART-`), `created_at` (UTC), `producer`, `workspace_id` (`WSP-`), `run_id` (`RUN-`), `protocol_fingerprint`, `corpus_fingerprint`, `data`; `inputs` defaults to `[]` | `models.py:182-223` |
| `document_manifest`'s required parent type is `screening_decisions` | `acceptance.py:40-45` (line **43**), `chain.py:32`, applied at `chain.py:193` |
| Registry lives at `audit/artifact_registry.json`; every declared input must be registered with a matching `sha256` | `acceptance.py:47`, `325-347` |

Consequences that are **normative** for E2:

1. The kit-owned acquisition manifest is **not** added to
   `DocumentManifestArtifact.inputs`. `inputs` carries the accepted
   `ScreeningDecisionsArtifact` reference only, exactly as the frozen golden
   chain shows at
   `tests/fixtures/contracts/v1/two_study_artifact_chain.json:186-191`.
2. The acquisition lineage is carried by a **new kit-owned, explicitly
   versioned extraction manifest** — `pdf-extraction-manifest-v1`, type
   `pdf_extraction_manifest`, deterministic `EXT-` manifest IDs — which is the
   inseparable provenance sidecar for the extracted bytes (§6.4). This is the
   same pattern as E1's `ACQ-` manifest, which the frozen registries provably
   reject (`tests/conformance/test_e1_acquired_document_boundary.py:344-369`,
   E1-NEG-044). The frozen keyset of six Contract v1 types must remain exactly
   that keyset (`acceptance.py:31-38`; asserted at
   `test_e1_acquired_document_boundary.py:77-86,327-341`).
3. The frozen `DocumentRecord` is published with the six contract fields only.
   The generated schema does tolerate extra properties
   (`src/scholar_harness/contracts/schemas/v1/document-manifest.schema.json:32`,
   and `ContractModel` sets `extra="allow"` at `models.py:45-48`), so embedding
   ad-hoc lineage keys in the record would be *schema-legal* — which is exactly
   why it is forbidden here. Unversioned extras inside a frozen record are the
   "adapter convenience" the contract-change rule exists to prevent, and they
   cannot be checksum-verified or rejection-tested as a unit. All lineage lives
   in the versioned sidecar. **If a later packet needs new `document_manifest`
   or `DocumentRecord` fields, that is a separate architecture/version
   decision** with regenerated schemas, regenerated golden fixtures, a negative
   regression test, and independent review.
4. A `DocumentManifestArtifact` candidate is constructed **only after** the engine chain has run
   to a determined outcome for a document, so an acquisition-only or in-flight
   document never produces a record and `chain.py` never sees a half-populated
   one. A *determined outcome* includes failure. A document whose engine chain
   yielded no usable text, or that has no text layer, is represented with
   `content_status` `FAILED`/`NEEDS_OCR` and `extracted_path` absent — exactly
   what the frozen model permits, since `models.py:503-510` requires a path only
   for `VALID`/`PARTIAL`, and exactly what the frozen chain anticipates, since
   `chain.py:335-345` refuses to ground evidence in a failed or OCR-pending
   document. Suppressing those documents would make the manifest a quiet
   selection rather than a truthful account. E1 §4.6's "after extraction has
   produced the required extracted path" is a floor, not an exclusion: the frozen
   model requires a path only for VALID/PARTIAL
   (`src/scholar_harness/contracts/models.py:503-510`) and `chain.py:335-345`
   presupposes publishable failed documents, so E2 emits determined failures
   without a path.
5. A **pre-extraction** failure is a rejection with **no** record at all: a
   stale or unverifiable parent, broken lineage, changed source bytes, or an
   identity disagreement fails the run closed and is never downgraded to a
   `FAILED` document, because that would publish an unverified document as if it
   had been extracted and verified (`E2-NEG-007`, `E2-NEG-041`). The dividing
   line is *was the engine chain actually run against verified bytes?* — if yes,
   the outcome is a truthful record; if no, it is a rejection.

E2's `document_manifest` candidate and harness publication must be
**consistent with** the frozen golden
shape, not a new shape: `producer.package == "scholar-pdf-kit"`
(`two_study_artifact_chain.json:192-196`), `inputs == [screening_decisions]`
(`:186-191`), `content_status` and `extraction_method` as recorded, `extracted_path`
a workspace-relative POSIX path under the workspace, and
`source_hash == sha256:<the E1 source_sha256>` (`:167-184`). The fixture is frozen
and is **not** regenerated; the illustrative `extracted/STU-alpha.md` path in it
shows the *shape*, not a naming rule E2 must copy (E2 addresses outputs by
document identity, §7.1).

### 1.2 Normative PDF requirement allocation (E2 rows)

E1's allocation table (`docs/architecture/wp01_packet_e1_acquired_document_handoff.md:64-82`)
closed PDF-001..007 and PDF-013..017 and deferred PDF-008..012 to E2/E3. This
table is the **E2 half of that deferral**. E2 owns the extraction semantics of
each row; where a row's remainder is a chunking/indexing concern, the chunk
half is explicitly E3 and E2 must say so rather than absorb it.

| Requirement | Owner in E2 | Binding text, E2 obligation, and deferral remainder |
|---|---|---|
| **PDF-008** | **E2 extraction** (owner: `nexus-scholar-org/scholar-pdf-kit`) | Extraction failure structure and usefulness thresholds. E2 defines per-item extraction outcomes, the minimum-usable-text rule, and when `PARTIAL`, `FAILED`, or `NEEDS_OCR` is the truthful status (§6.1, §6.7). Evidence: `E2-004`, `E2-NEG-013`, `E2-NEG-015`, `E2-NEG-016`, `E2-NEG-041`. Chunk-level usefulness scoring is E3. |
| **PDF-009** | **E2 extraction** (owner: `nexus-scholar-org/scholar-pdf-kit`) | Requested vs effective engine, engine versions, and fallback reasons are recorded per document and per attempt (§6.3). Evidence: `E2-005`, `E2-NEG-010`, `E2-NEG-011`, `E2-NEG-012`, `E2-NEG-028`, `E2-NEG-038`. Retrieval-engine selection for RAG is E3. |
| **PDF-010** | **E2 extraction + acceptance adapter** (owners: `nexus-scholar-org/scholar-pdf-kit` for the candidate; harness for acceptance/publication) | Study, DOI, bibliographic metadata, checksum, and engine/version flow into extracted frontmatter and the Contract-shaped candidate; the harness adapter passes that candidate through `accept_artifact` before the `DocumentManifestArtifact` becomes authoritative (§6.5, §6.6). E1 supplies source fields but is not that artifact (`wp01_packet_e1_acquired_document_handoff.md:75`). Evidence: `E2-008`, `E2-009`, `E2-NEG-033`. |
| **PDF-011** | **E2 integration** (owner: `nexus-scholar-org/scholar-agent-kit` for the declaration; `scholar-pdf-kit` for engine selection) | MCP engine selection, rejection of unsupported engines, and preservation of canonical metadata through the extracted artifact or its inseparable sidecar (§9). E2 does not claim an MCP extraction result. Evidence: `E2-013`, `E2-NEG-010`, `E2-NEG-019`, `E2-NEG-020`, `E2-NEG-043`. |
| **PDF-012** | **E2 extraction** (owner: `nexus-scholar-org/scholar-pdf-kit`) | `pyyaml` declaration and extraction-side packaging ship with the E2 implementation and its clean-wheel tests. Today `PyMuPDFEngine` emits YAML frontmatter with a function-local `import yaml` (`tools/scholar-pdf-kit/src/scholar_pdf/extract.py:26`) while `pyproject.toml` declares no `pyyaml` (`tools/scholar-pdf-kit/pyproject.toml:10-20`); `docs/kits_surface_matrix.md:221` already records `pyyaml` as an undeclared transitive dependency. Evidence: `E2-014`, `E2-NEG-031`, `E2-NEG-032`. |

### 1.3 E1 boundary language E2 must honour verbatim

From `docs/architecture/wp01_packet_e1_acquired_document_handoff.md`:

- E2 consumes these **committed** fields from the accepted E1 manifest and
  preserves the manifest reference: `document_id`, `study_id`, `source_sha256`,
  `byte_length`, `media_type`, `workspace_relative_path`,
  `validation_profile`, `validation_profile_version`, `access_status`,
  `selected_source_url`, `attempts`, `acquisition_method` (lines 421-439).
  For `USER_PATH`, E2 preserves the null/absent `selected_source_url`, the
  workspace-relative `selected_source`, and the `access_assertion`, and must not
  invent a URL (lines 441-442).
- E2 verifies the E1 manifest checksum and its parent references **before**
  extraction and fails closed if they are stale (lines 456-462).
- The required Contract v1 parent stays `screening_decisions`
  (`acceptance.py`/`chain.py`, lines 443-447).
- `extraction_failed` is reserved for E2 and is not fabricated by E1
  (line 179); E1's projected status vocabulary deliberately has no
  extraction-failure member.
- E1 makes no claim about E2 extraction on MCP; that is this packet (lines
  484-485).
- E1's own boundaries: the deferred rows are not E1 work (line 841), E1's
  completion claim covers only its allocated rows (line 840), and E1's tests may
  not claim PDF-008..012 (lines 841-847, 999-1000).

From `docs/architecture/wp01_packet_e1_completion_report.md`:

- "WP01-E2 must verify this manifest and the source bytes before it emits
  Contract v1 `DocumentManifestArtifact` records with truthful extraction
  state." (lines 16-20)
- "WP01-E2 owns extraction provenance and Contract v1
  `DocumentManifestArtifact` emission" and "E2 must revisit MCP semantic parity
  if extraction adds or changes MCP behavior; E1's unsupported acquisition
  declaration must not be silently broadened." (lines 158-170)

From `docs/architecture/DEVELOPER_COMPASS.md:227-233` (the five-line E2
definition this packet elaborates): consume the accepted E1 manifest, verify its
parent lineage, bind extracted text to the accepted document ID and source
checksum, emit the registered `DocumentManifestArtifact` only after extraction,
and record requested/effective engines, fallback chain, page/character counts,
content status, and failure reason.

### 1.4 Current extraction behavior, characterized at the pinned revisions

Every claim below was read at the pinned vendored snapshots
(`tools/scholar-pdf-kit` = `858911f6…`, `tools/scholar-agent-kit` = `6050e0c…`).
E2 replaces or wraps this behavior; it must not silently inherit it.

| # | Verified current fact | Location | E2 obligation |
|---|---|---|---|
| 1 | `PyMuPDFEngine.extract_markdown` writes frontmatter with only `workspace_id`, `doi`, `title`, `authors`, `year`, `extraction_engine`, `extracted_at` (empty keys dropped). It carries **no** `document_id`, no `source_sha256`, and no acquisition lineage. | `tools/scholar-pdf-kit/src/scholar_pdf/extract.py:31-49` | Frontmatter must become **bound**: add `document_id`, `source_sha256`, `acquisition_manifest_sha256`, engine name/version, and content status (§6.6). |
| 2 | On **any** exception the PyMuPDF path appends the stub line `Extracted content from {name}` and still writes the file and returns it as success. | `extract.py:97-104` | "success" ≠ content. A stub output must never become `VALID` (§6.7, `E2-NEG-013`). |
| 3 | Output name is `{pdf_path.stem}.md` — filename-addressed, not identity-addressed. | `extract.py:102` | Authoritative extraction is addressed by document identity (§7.1). |
| 4 | `DoclingEngine` writes markdown with **no frontmatter at all**, and any failure silently falls back to `PyMuPDFEngine` with no reason recorded. | `extract.py:107-127` (fallback 123-127) | Fallback must be explicit and reason-recorded (§6.3, `E2-NEG-011`/`012`). |
| 5 | `GrobidEngine` is an **external provider** returning TEI XML, writes `{stem}.tei.xml`, and raises on non-200. | `extract.py:130-157` | `extraction_method` must reflect provider use (`EXTERNAL_PROVIDER`/`HEURISTIC`), and TEI vs markdown output must be an explicit recorded fact. |
| 6 | Engine selection is not exposed consistently: the CLI's `--engine` accepts only `docling\|grobid` (default `docling`), so the default is an engine most installs do not have. | `tools/scholar-pdf-kit/src/scholar_pdf/cli.py:426-496` (option 437; routing 478-486) | Requested-engine semantics must be explicit and an unavailable default must produce a recorded fallback, never a silent one. |
| 7 | The CLI takes a **positional raw path**, has no parent/manifest binding, no checksum verification, no identity, and counts a per-file exception as "not successful" text without a structured envelope. | `cli.py:426-496` | The authoritative path is manifest-driven; the legacy raw-path form is either re-implemented over the E2 service or explicitly marked non-authoritative (§7.2). |
| 8 | `scholar_pdf/__init__.py` imports the extract module at package import (`from .extract import DoclingEngine, GrobidEngine, PyMuPDFEngine`), while `extract.py`'s own top-level imports are stdlib-only and every heavy dependency (`yaml`, `fitz`, `docling`, `requests`) is function-local. | `tools/scholar-pdf-kit/src/scholar_pdf/__init__.py:63`; `extract.py:1-4,26,52,114,137` | Extraction must stay import-cheap: the harness wheel and both metapackage entrypoints answer `--help` on a minimal-dep environment (`E2-014`, `E2-NEG-032`). |
| 9 | `nexus_extract_pdf` takes a raw `pdf_path`, derives `title` from the filename stem, a DOI by regex over the stem, and a `workspace_id` by regex `SCI-\d+` over the path, then returns free text `f"Extracted {pdf.name} to {res_file}"` (line 639) or `f"Error: PDF {pdf_path} not found."` (line 630) / `f"Error during PDF extraction: {e}"` (line 641). It verifies nothing, identifies nothing, and emits no manifest or Contract artifact. | `tools/scholar-agent-kit/src/scholar_agent/server.py:596-615,618-641` | This is **not** an authoritative surface and must be declared as such; MCP extraction becomes a declared capability boundary (§9, `E2-NEG-019`). |
| 10 | The agent server imports the extract engines at module import time, so the wheel must bundle `scholar_pdf.extract`. | `server.py:76` | MCP semantic parity here means "extraction ships in the wheel", exactly as E1 shipped `pypdf` for import-time reachability (`packaging/nexus-scholar/pyproject.toml`, E1 R7 precedent; `docs/kits_surface_matrix.md:221`). |
| 11 | The agent kit's capability registry is an immutable `MappingProxyType` of frozen `CapabilityDeclaration`s with pure envelope builders and zero-I/O guarantees; a non-enum `code` string is an explicitly supported extension point. | `tools/scholar-agent-kit/src/scholar_agent/capabilities.py:30-52,112-250` | E2 adds a **new** declaration (`pdf_extraction`); it must not mutate or broaden `pdf_acquisition` (`E2-NEG-020`). |
| 12 | E1's `verify_manifest` already recomputes the payload fingerprint, the null-excluded `artifact_checksum`, the deterministic `ACQ-` id, the `e2_reference` path, `parent_lineage_sha256`, every record's `DOC-` id, and (with `verify_bytes=True`) each file's size and SHA-256 (and, with `verify_bytes=True`, re-runs the E1 PDF/structural validation at `acquisition.py:3105-3109`, which E2 inherits rather than repeats). | `tools/scholar-pdf-kit/src/scholar_pdf/acquisition.py:3019-3104` (checksum 3026-3037; id 3041-3052; e2 ref 3053-3063; lineage 3064-3070; `DOC-` id 3071-3081; bytes 3082-3104); structural revalidation `3105-3109` | **Normative consumption shape:** E2 consumes `PDFAcquisitionService.verify_manifest(manifest, verify_bytes=True)` and treats `AcquisitionCommitError.code` as the structured failure; if a result object is wanted for reporting, extract a public wrapper rather than re-deriving any check. The method returns `None` and raises on the first failed check (`acquisition.py:3019-3021`), so there is no partial-verdict object to read and no re-derivation to justify. |
| 13 | The E1 manifest's `e2_reference.acquisition_manifest_path` convention is `literature/acquisition/<run_id>/<ACQ-…>.json`, enforced on both write and verify. | `acquisition.py:2681-2687`, `2820-2859`, `3053-3063` | E2 loads exactly that path; any other path is a mismatch, not a convenience lookup. |
| 14 | The kit already has a reusable `ManifestReference` (manifest_id, manifest_type, workspace_relative_path, artifact_checksum) and `ArtifactReference` (artifact_id, path, sha256) model, plus `canonical_json_bytes`/`canonical_fingerprint` and `deterministic_document_id`/`deterministic_acquisition_manifest_id`. | `acquisition_models.py:933-975`, `canonical.py:81-104,168-246` | E2's sidecar reuses these primitives; it does not mint a second canonicalization or identity rule. |
| 15 | The kit's local frozen-shape gate validates only `corpus_snapshot` and `screening_decisions` parents and reports anything else rather than coercing it. | `tools/scholar-pdf-kit/src/scholar_pdf/contract_parents.py:83-100` | `document_manifest`'s required parent is `screening_decisions`, so E2 can validate its Contract parent with the existing gate and must never coerce an unknown parent type. |
| 16 | The `nexus-scholar` metapackage and the pdf kit declare **no** `pyyaml`. | `packaging/nexus-scholar/pyproject.toml` (dependency block), `tools/scholar-pdf-kit/pyproject.toml:10-20` | PDF-012 is a real, currently open defect; E2 must close it in the canonical kit **and** reflect it in the metapackage dependency list when the kit starts importing `yaml` on an authoritative path. |
| 17 | The MCP surface is 25 registered tools (22 `nexus_*` + 3 `recon_*`; WP01-E2 added the declared-unsupported `nexus_pdf_extraction`), and two harness conformance files assert tool-registration/`--help` parity. | `tools/scholar-agent-kit/.../server.py` (tool count asserted in `tests/conformance/test_e1_acquired_document_boundary.py:538-547`); `tests/conformance/test_mcp_tool_parity.py:16-31` | If E2 adds or removes an MCP tool, the count assertions are an E2 harness obligation — a test update, never a contract change. |
| 18 | The canonical workspace layout includes `pdfs/` and `extracted/`. | `AGENTS.md:33` | E2's extracted-text store is `extracted/`, alongside E1's `pdfs/acquired/` (`acquisition_models.py:201` `storage_prefix`). |

## 2. Scope

### 2.1 What E2 does

1. **Consume the accepted E1 acquisition manifest**: load it at the exact
   `e2_reference.acquisition_manifest_path`, validate it with the kit-owned
   schema, and verify its `artifact_checksum` (null-excluded canonical
   construction), its deterministic `ACQ-` id, its `parent_lineage_sha256`, and
   its embedded E2 reference. Reuse the E1 verifier; do not re-derive it. The
   consumption shape is **normative**: call
   `PDFAcquisitionService.verify_manifest(manifest, verify_bytes=True)` and treat
   `AcquisitionCommitError.code` as the structured failure
   (`acquisition.py:3019-3021`; `AcquisitionCommitError` at `:116-129` with
   `code` at `:128`); if a result object is wanted for reporting, extract a
   public wrapper rather than re-deriving any check.
2. **Verify the direct scientific parent**: the accepted
   `ScreeningDecisionsArtifact` (loaded by ID, type-checked, workspace-checked,
   canonical fingerprint recomputed) must agree with the acquisition manifest's
   `protocol_fingerprint`, `corpus_fingerprint`, and `workspace_id`, and must
   list every study E2 extracts. The kit's local frozen-shape gate validates the
   parent structurally; a stale, cross-workspace, hash-mismatched, or
   unknown-study parent fails before any engine runs.
3. **Verify the source bytes** before extraction: the file at the record's
   `workspace_relative_path` must exist, be a regular file inside the canonical
   workspace root, and hash and size exactly to the manifest's `source_sha256`
   and `byte_length`. Extraction reads exactly those bytes.
4. **Extract bound text** with a declared engine chain, writing a
   deterministic, identity-addressed output under `extracted/` with a bound
   YAML frontmatter header (§6.6).
5. **Record the extraction truth**: per document — requested and effective
   engine with versions, the ordered fallback chain with a reason for every
   step, page count, character count, content status, failure reason,
   extraction method, extracted path, and the deterministic binding of
   `document_id` + `source_sha256` → extracted bytes (`extracted_sha256`).
6. **Publish the extraction manifest** (`pdf-extraction-manifest-v1`,
   `EXT-*`) atomically as the commit marker, then append exactly one canonical
   workspace-manager audit event (§7.3).
7. **Construct a frozen Contract v1 `DocumentManifestArtifact` candidate**
   **only after** extraction, with truthful content status (including
   `FAILED`/`NEEDS_OCR` records with no `extracted_path`),
   `inputs == [screening_decisions]`, producer `scholar-pdf-kit`, and
   `source_hash` equal to the E1 `source_sha256`. The PDF kit returns that
   deterministic candidate without importing the harness or mutating its
   registry; the bounded harness adapter alone passes it through
   `accept_artifact` and may describe it as published. A run with no
   byte-bearing record constructs no candidate and publishes no Contract
   artifact (§1.1 consequence 4, §6.5).
8. **Declare the MCP boundary** for extraction in the agent kit: a new
   `pdf_extraction` capability declaration, the pre-I/O rejection envelope, and a
   truthful statement that the existing raw-path `nexus_extract_pdf` is
   non-authoritative (§9).
9. **Declare dependencies and packaging truthfully**: `pyyaml` and any engine
   dependency E2 puts on an authoritative path, with clean-wheel import and
   entrypoint smokes, and lazily imported heavy engines.

### 2.2 What E2 does **not** do

- **No chunking, embedding, indexing, retrieval, or chunk IDs** — that is E3
  (`DEVELOPER_COMPASS.md:235-239`). E2 must not mint `CHK-` identities.
- **No claims, evidence, citations, verification axes, or synthesis** — later
  packets. E2 must not emit `ClaimEvidenceLedger`; the fact that
  `chain.py:335-345` refuses to ground evidence in a `FAILED`/`NEEDS_OCR`
  document is a *reason* for truthful status, not an E2 deliverable.
- **No verify/analyze/synthesize/critic loops**, no dual-coding, no adjudication.
- **No acquisition behavior changes**: E2 re-verifies E1's committed facts and
  never re-downloads, re-derives `DOC-` differently, relabels access status, or
  rewrites an E1 record.
- **No Contract v1 change**: no new `artifact_type`, no schema, no generated
  schema, no golden fixture, no baseline, no identifier-registry change, and no
  edit to `acceptance.py`/`chain.py` registries.
- **No workspace scientific content**: E2 does not create, curate, or annotate
  a `workspaces/<slug>/` project as part of this packet; harness-side artifacts
  stay under `tests/`, `docs/`, `tools/`, `packaging/`, and `.agents/`.
- **No unrelated kit cleanup**, including the pre-existing agent-kit
  protocol-validation and non-hermetic RAG test behavior that E1 already
  recorded as separate maintenance items
  (`wp01_packet_e1_completion_report.md:167-170`).

### 2.3 Governing invariants

1. `document_id` is **reused from the E1 manifest**; the recomputed value must
   equal it or extraction fails. E2 never mints a second identity rule.
2. A path is a location, not document identity; a filename, DOI, title, or URL
   is not identity either.
3. `source_hash` in the candidate or accepted Contract artifact is the E1 `source_sha256` of
   the exact validated bytes, re-verified before extraction.
4. Acquisition lineage is an **embedded, checksummed reference**, never a
   Contract v1 parent edge.
5. `VALID` means usable extracted text exists; `PARTIAL` means it exists and the
   degradation is explained; `FAILED`/`NEEDS_OCR` never carry a fabricated
   `extracted_path`.
6. A successful engine exit is not extracted text. A stub, empty, or
   placeholder body is a failure, not a partial success.
7. Every fallback is recorded with a reason; an unrecorded substitution is a
   failure of the record, not a silent convenience.
8. Publication is fail-closed: the PDF kit constructs no
   `DocumentManifestArtifact` candidate without a committed extraction
   manifest, and the harness publishes no candidate that fails
   `accept_artifact`; no extraction manifest exists without verified source
   bytes.
9. Every committed path is relative to one caller-supplied canonical workspace
   root and is a portable POSIX path.
10. A failed batch is still a real machine-readable outcome. Zero extracted
    records is `FAILED`, never an empty `SUCCESS`.
11. Extraction determinism: the same accepted manifest, bytes, and requested
    engine produce the same `EXT-` id and the same candidate payload, independent
    of input order, attempt order, and wall-clock time.
12. Required tests are hermetic, scriptable, and offline: local PDF fixtures, no
    network, no provider daemon, no sleep-dependent assertions.

## 3. Acceptance criteria

- **E2-001 Acquisition-manifest verification and fail-closed preflight:** a
  missing, unreadable, stale, cross-workspace, checksum-mutated,
  lineage-mutated, or id-inconsistent acquisition manifest is rejected before
  any engine runs, any output file is written, or any audit event is appended.
  Evidence: `E2-NEG-001..004`, `E2-NEG-009`, `E2-NEG-025`.
- **E2-002 Deterministic document identity reuse:** each candidate or published
  `DocumentRecord.document_id` is byte-for-byte the E1 `document_id`, and equals
  the helper's result for
  `deterministic_document_id(study_id=..., source_hash=<E1 source_sha256>,
  workspace_id=..., algorithm_version="v1")` — a keyword-only helper whose
  payload also pins `media_type="application/pdf"`
  (`tools/scholar-pdf-kit/src/scholar_pdf/canonical.py:168-211`). A study, byte,
  or workspace change yields a different identity; two studies with identical
  text remain two documents. Evidence: `E2-NEG-005`, `E2-NEG-006`,
  `E2-NEG-026`, `E2-NEG-027`.
- **E2-003 Source-byte binding:** the bytes opened for extraction are the
  committed bytes — same SHA-256, same length, same regular file, inside the
  canonical root. A changed, truncated, replaced, missing, or symlink-escaping
  source fails closed rather than extracting a substitute. Evidence:
  `E2-NEG-007`, `E2-NEG-008`, `E2-NEG-024`.
- **E2-004 Truthful content status:** `VALID` requires usable extracted text
  under a recorded threshold; `PARTIAL` requires an explicit reason; `FAILED`
  and `NEEDS_OCR` never fabricate `extracted_path`; the current stub-on-parse-
  failure "success" is not accepted as content. Evidence: `E2-NEG-013`,
  `E2-NEG-014`, `E2-NEG-015`, `E2-NEG-016`, `E2-NEG-039`, `E2-NEG-041`.
- **E2-005 Engine chain provenance:** requested engine, effective engine,
  engine versions, and an ordered fallback chain with one reason per step are
  recorded; an unsupported or unavailable requested engine produces a recorded
  fallback or a structured failure, never a silent substitution. Evidence:
  `E2-NEG-010`, `E2-NEG-011`, `E2-NEG-012`, `E2-NEG-028`, `E2-NEG-038`.
- **E2-006 Deterministic extraction-manifest identity:** the `EXT-` id is
  deterministic over the extraction schema version, workspace, run, the E1
  manifest reference and checksum, and the normalized per-document extraction
  records; timestamps, retry counters, and attempt ordinals are excluded.
  Evidence: `E2-NEG-009`, `E2-NEG-042`.
- **E2-007 Fail-closed publication and recovery:** the PDF kit constructs the
  `DocumentManifestArtifact` candidate only after the extraction manifest is
  committed, and the harness publishes it only after acceptance; faults
  injected at output write, manifest replace, adapter acceptance, and
  post-commit audit append leave either the prior valid state or an explicitly
  recoverable committed state, with an idempotent rerun. Evidence:
  `E2-NEG-023`, `E2-NEG-029`, `E2-NEG-034`.
- **E2-008 Bound extracted frontmatter (PDF-010):** every authoritative
  extracted file carries `document_id`, `source_sha256`,
  `acquisition_manifest_sha256`, acquisition manifest ID, engine name/version,
  and content status in its frontmatter, matching the sidecar record. A file
  missing those bindings is not authoritative. Evidence: `E2-NEG-033`,
  `E2-NEG-040`.
- **E2-009 Registered Contract v1 publication (PDF-010):** the PDF kit's
  deterministic candidate validates against the frozen
  `DocumentManifestArtifact` shape with
  `inputs == [screening_decisions]`, `producer.package == "scholar-pdf-kit"`,
  matching `protocol_fingerprint`/`corpus_fingerprint`/`workspace_id`, and
  truthful per-document state. The harness adapter parses the candidate through
  the frozen model, calls `accept_artifact`, and only then exposes the accepted
  artifact reference; the PDF kit never imports `scholar_harness`, writes the
  Contract registry, or claims acceptance. The frozen chain map is unchanged.
  Evidence: `E2-NEG-021`, `E2-NEG-022`, `E2-NEG-023`,
  `E2-NEG-035`, `E2-NEG-045`.
- **E2-010 Idempotency, replay, and determinism:** an exact replay reuses the
  committed extraction without duplicating a file, manifest, candidate,
  accepted artifact, or audit
  event; a changed non-volatile input under an existing key is an
  `IDEMPOTENCY_CONFLICT` and never overwrites; candidate payload hashes are
  stable across runs and input order. Evidence: `E2-NEG-017`, `E2-NEG-018`,
  `E2-NEG-034`, `E2-NEG-042`.
- **E2-011 Workspace containment and portability:** extracted outputs and
  sidecars are workspace-relative POSIX paths inside the canonical root;
  traversal, absolute, drive-letter, and symlink escapes are rejected before
  read/write; the sidecar and candidate/published artifact round-trip on Windows and POSIX
  with no absolute path. Evidence: `E2-NEG-024`, `E2-NEG-046`, `E2-NEG-025`.
- **E2-012 Structured outcomes and surface parity:** success, partial, failed,
  `NEEDS_OCR`, all-failure, cancellation, and internal-failure outcomes stay
  distinguishable and use the canonical `OperationStatus` vocabulary, with the
  same statuses and references exposed by the Python API and the CLI. Evidence:
  `E2-NEG-030`, `E2-NEG-041`, `E2-NEG-010`.
- **E2-013 Declared MCP boundary (PDF-011):** the agent kit declares
  `pdf_extraction` with `mcp_supported=false` and returns the standard envelope
  with zero I/O; the raw-path `nexus_extract_pdf` is documented as
  non-authoritative and cannot emit a Contract artifact; `pdf_acquisition`
  remains declared unsupported and is not broadened; no metadata, identity, or
  status is fabricated from a filename, URL, or regex over a path. Evidence:
  `E2-NEG-019`, `E2-NEG-020`, `E2-NEG-043`, `E2-NEG-044`.
- **E2-014 Packaging and dependency declaration (PDF-012):** `pyyaml` — currently
  undeclared in both `tools/scholar-pdf-kit/pyproject.toml:10-20` and the
  metapackage dependency list (`packaging/nexus-scholar/pyproject.toml:48-71`) —
  plus any other dependency E2 puts on an authoritative path, is declared in the
  canonical kit and reflected in the metapackage list. Today `pymupdf` is a
  declared *hard* kit dependency (`pyproject.toml:19`); `docling` and `lxml` are in
  the `[extract]` extra only (`pyproject.toml:29,31`), while `requests` is in
  **both** the hard dependency list and the `[extract]` extra
  (`tools/scholar-pdf-kit/pyproject.toml:15` and `:30`). All of them, and `yaml`,
  are imported function-locally (`extract.py:26,52,114,137`) and E2 must
  keep them that way, so both wheel entrypoints still answer `--help` on a
  minimal-dep environment — the property the metapackage comment at
  `packaging/nexus-scholar/pyproject.toml:58-64` relies on for `pypdf`. A clean
  wheel can import the public extraction models and run the extraction command's
  `--help` without the repository checkout. Evidence: `E2-POS-004`,
  `E2-NEG-031`, `E2-NEG-032`.
- **E2-015 Synchronization and lineage:** every changed canonical kit commit,
  the vendored `tools/<kit>/` snapshot, the full-SHA `plugins.json` pin, and the
  generated metapackage pin agree; the E1 `artifact_checksum`, the embedded
  acquisition reference, the `EXT-` id, and the candidate/accepted artifact payload hash
  agree exactly; the frozen Contract v1 registries, schemas, fixture, and
  baseline are unchanged. Evidence: `E2-NEG-037`, `E2-NEG-009`, `E2-NEG-035`.
- **E2-016 Evidence and test-claim honesty:** PDF-008..012 each map to named
  test IDs; the harness claims no kit-internal behavior it cannot observe; no
  E2 test or document claims E3 chunking, later evidence work, or Contract v1
  change. Evidence: the traceability matrix in §5 plus the residual-risk
  statement in §14.

## 4. Positive fixtures and mandatory negative tests (VAL-001)

### 4.1 Positive fixture IDs

These IDs are deliberately small; every required negative and fault case has an
explicit `E2-NEG-###` identifier.

- `E2-POS-001`: an accepted E1 manifest plus committed bytes extracts through
  the deterministic engine, publishes a fail-closed extraction manifest, the
  PDF kit returns a deterministic `DocumentManifestArtifact` candidate, and the
  harness adapter passes it through the frozen acceptance gate.
- `E2-POS-002`: an exact second run detects the committed extraction manifest
  and returns a reused result with identical `EXT-` id, artifact payload hash,
  and audit event identity — no duplicate file, manifest, artifact, or event.
- `E2-POS-003`: a requested engine that is unavailable produces a **recorded**
  fallback to the deterministic engine with a reason, and the emitted status and
  frontmatter state the effective engine.
- `E2-POS-004`: a clean isolated wheel imports the public extraction models and
  answers `scholar-pdf extract-run --help` without the repository checkout and
  without heavy engines. The legacy `extract --help` smoke does not substitute
  for the authoritative E2 entrypoint.

### 4.2 Stable negative-test ledger

Each ID is a required test name (or stable parametrized case ID). Each asserts
the stated status, the no-publication condition, cleanup, and the lineage
outcome.

| Test ID | Required case and assertion |
|---|---|
| `E2-NEG-001` | Missing or unreadable acquisition manifest: reject before any engine call, output file, manifest, or audit event; no `DocumentManifestArtifact`. |
| `E2-NEG-002` | Stale acquisition manifest: a changed parent payload, registry entry, or parent fingerprint since the E1 commit is detected and rejected before extraction. |
| `E2-NEG-003` | Manifest checksum mutation: changing any field other than `artifact_checksum` changes the null-excluded canonical digest; changing only the stored digest also fails; neither is trusted. |
| `E2-NEG-004` | Cross-workspace or out-of-root acquisition manifest: a manifest whose `workspace_id`, `run_id`, or location does not match the accepted binding is rejected; no identity is minted in the wrong namespace. |
| `E2-NEG-005` | Unbound document: a requested `document_id` absent from the manifest `records` is rejected before extraction; E2 never invents a document for a study E1 did not commit. |
| `E2-NEG-006` | Identity disagreement: a manifest whose `document_id` differs from `deterministic_document_id(study_id=..., source_hash=record.source_sha256, workspace_id=manifest.workspace_id, algorithm_version=record.document_identity_algorithm_version)` is rejected; the recomputed value is never substituted silently. |
| `E2-NEG-007` | Changed source bytes: a one-byte mutation, truncation, or replaced file at the committed path is rejected before extraction; E2 does not re-hash-and-continue and does not downgrade the item to `FAILED` as a substitute for the lineage failure. |
| `E2-NEG-008` | Missing/irregular source: a missing path, a directory, a symlink escaping the canonical root, or a length mismatch is rejected with no output. |
| `E2-NEG-009` | Extraction-manifest integrity: mutation of any sidecar field, of `parent_lineage_sha256`, or of the null-excluded `artifact_checksum` fails verification and blocks candidate construction and Contract publication. |
| `E2-NEG-010` | Unsupported/unavailable requested engine: an engine that is not installed or not reachable produces a recorded fallback with a reason (or a structured failure), never a silent substitution. |
| `E2-NEG-011` | Unrecorded fallback: the current silent `DoclingEngine → PyMuPDFEngine` behavior (and its CLI equivalent) is rejected as an authoritative outcome; a fallback without a reason entry fails the record. |
| `E2-NEG-012` | Fallback-chain completeness: `effective != requested` with an empty reason, or a chain whose order contradicts the recorded attempts, is rejected. |
| `E2-NEG-013` | Stub output is not content: a fixture whose parse path fails (producing the `Extracted content from {name}` stub) can never be published as `VALID`; the item becomes `FAILED` or `NEEDS_OCR` with a reason. |
| `E2-NEG-014` | Truthful failure and no fabricated path: in a **mixed** batch, a sibling that produced no usable text is emitted with `content_status` `FAILED`/`NEEDS_OCR` and `extracted_path` **absent** (accepted by `models.py:503-510`), while a `FAILED`/`NEEDS_OCR` record carrying a non-null `extracted_path` is rejected. Both limbs are required: suppressing the failed sibling and inventing a path for it are the same fabrication. |
| `E2-NEG-015` | `VALID` requires usable text: a body below the recorded usefulness threshold (empty, whitespace-only, frontmatter-only) cannot be `VALID`. |
| `E2-NEG-016` | `PARTIAL` requires an explanation: `PARTIAL` without a fallback reason or degradation diagnostic is rejected. |
| `E2-NEG-017` | Replay binding: an exact replay recomputes and matches the same `EXT-` id and `extracted_sha256`; a changed extracted body under a committed path is detected and is not silently re-published. |
| `E2-NEG-018` | Idempotency conflict: the same key with a changed non-volatile extraction payload (different requested engine, different document set) fails as `IDEMPOTENCY_CONFLICT` and never overwrites the earlier manifest. |
| `E2-NEG-019` | Unbound raw-path extraction: an MCP/CLI extraction invoked with a bare path, no acquisition manifest, no checksum verification, and no parent is declared **non-authoritative** and cannot produce a Contract artifact or a sidecar claim of one. |
| `E2-NEG-020` | No silent broaden: E2 does not flip `pdf_acquisition` to supported, does not emit an authoritative artifact from MCP, and E1's `acquire_pdf` rejection envelope tests still pass unchanged. |
| `E2-NEG-021` | Non-registry sidecar (E1-NEG-044 analog): `pdf_extraction_manifest` handed to the frozen acceptance/chain registries is rejected as `UNSUPPORTED_ARTIFACT_TYPE`; no registry entry is fabricated; the frozen keyset remains exactly the six Contract v1 types. |
| `E2-NEG-022` | Parent discipline: the PDF-kit candidate may be constructed for validation, but the harness adapter rejects a `DocumentManifestArtifact` whose `inputs` contain the acquisition manifest, a corpus snapshot, or anything but the accepted `screening_decisions` reference (`REQUIRED_PARENT_TYPE_MISSING` / `MISSING_PARENT_ARTIFACT` / `PARENT_HASH_MISMATCH`); an empty `inputs` list is also rejected and no registry entry is written. |
| `E2-NEG-023` | No premature publication: injecting a failure between extraction success and candidate construction leaves no candidate; injecting one between candidate construction and harness acceptance leaves no published artifact and no registry entry. |
| `E2-NEG-024` | Output containment: `..`, absolute, drive-letter, separator tricks, and symlinked parents in the extracted destination fail before read/write. |
| `E2-NEG-025` | Cross-workspace extraction: an acquisition manifest or screening parent bound to another workspace is rejected; the candidate/published artifact and sidecar stay in the accepted workspace only. |
| `E2-NEG-026` | Two studies, one text: identical extracted text for two studies produces two distinct document identities and two records; text is not identity. |
| `E2-NEG-027` | Unknown study: a document whose `study_id` is not in the accepted corpus/screening lineage is rejected before emission (`UNKNOWN_DOCUMENT_STUDY` semantics, `chain.py:280-293`). |
| `E2-NEG-028` | Engine-version provenance: an attempt without an engine version, or `requested == effective` while a fallback entry claims a step, is rejected. |
| `E2-NEG-029` | Atomic-commit faults: faults injected at extracted-file promotion, sidecar replace, and post-commit audit append leave no partial authoritative state and preserve prior valid outputs. |
| `E2-NEG-030` | PDF-kit API/CLI parity: the standalone Python API and CLI report the same `OperationStatus`, per-item extraction status, errors, warnings, sidecar reference, and non-authoritative candidate reference/checksum; neither exposes an accepted-artifact reference. Harness-adapter tests separately require the accepted reference only after `accept_artifact`. |
| `E2-NEG-031` | Clean-wheel packaging: the built wheel declares and can import its YAML dependency and public extraction models, and the extraction entrypoint's `--help` works with no repository checkout and no heavy engines. |
| `E2-NEG-032` | Lazy heavy engines: importing the kit package, the agent server, and the metapackage entrypoints does not import `fitz`, `docling`, `requests`, or any other heavy engine at import time. |
| `E2-NEG-033` | Frontmatter binding: an extracted file whose frontmatter lacks `document_id`/`source_sha256`/`acquisition_manifest_sha256`, or whose values disagree with the sidecar, is not authoritative and is rejected on verification. |
| `E2-NEG-034` | Post-commit/pre-audit recovery: sidecar replace succeeds, audit append fails, rerun completes exactly the one missing event or returns an idempotent reused result with no duplication. |
| `E2-NEG-035` | Parent registration at publication: an unregistered screening parent, or one whose registered `sha256` differs from the declared input hash, is rejected by the harness adapter's acceptance gate; the parent is never silently replaced. |
| `E2-NEG-036` | Fingerprint agreement: a protocol/corpus fingerprint or workspace disagreement between the acquisition manifest, the screening parent, the E2 request, and the candidate/published artifact fails closed. |
| `E2-NEG-037` | Cross-repository drift (E1-NEG-030 analog): canonical kit commits, the vendored `tools/<kit>/` snapshot (staged index and worktree content), the `plugins.json` full-SHA pin, and the generated metapackage pin must agree; any mismatch fails. |
| `E2-NEG-038` | Unknown engine name: an unrecognized engine request (including a typo) is a structured error, never a silent fallback to the default engine. |
| `E2-NEG-039` | `NEEDS_OCR` justification: `NEEDS_OCR` requires a recorded detection reason (for example, no extractable text layer) and never carries an authoritative `extracted_path` or grounds downstream evidence. |
| `E2-NEG-040` | Extracted-content mutation: editing or truncating a committed extracted file (or its frontmatter) is detected on replay through the recorded `extracted_sha256` and is not re-published as current. |
| `E2-NEG-041` | All-failure batch: a run where every document fails publishes a fail-closed extraction manifest with zero extracted records, explicit per-item outcomes and errors, and `OperationStatus=FAILED`; it is distinguishable from a missing manifest and never an empty success. Because `DocumentManifestData.documents` has `min_length=1`, **no** `DocumentManifestArtifact` and no registry entry is published for such a run (§6.5). |
| `E2-NEG-042` | Determinism: the same manifest, bytes, and requested engine yield the same `EXT-` id and the same candidate payload hash regardless of document input order, attempt order, or wall-clock time. |
| `E2-NEG-043` | No fabricated metadata: filename-, URL-, or regex-derived title/DOI/workspace values (the current `_pdf_metadata` behavior) never enter an authoritative frontmatter, sidecar, candidate, or published artifact. |
| `E2-NEG-044` | Doc-surface parity (E1-NEG-047 analog): the capability registry, both PDF/agent kit skills (canonical and mirrored), and `docs/kits_surface_matrix.md` state the same E2 extraction surfaces, the declared MCP boundary, and the non-authoritative raw-path tool. |
| `E2-NEG-045` | Artifact idempotency: when the harness adapter re-presents a different payload under an already registered `ART-` id, `accept_artifact` returns `IDEMPOTENCY_CONFLICT`, not an overwrite; standalone PDF-kit replay does not write the registry. |
| `E2-NEG-046` | Sidecar placement and containment: the sidecar must live at the deterministic in-root path for its `EXT-` id and run; a relocated, symlinked, or escaping sidecar is rejected. |

## 5. Traceability

### 5.1 Acceptance-criterion to test-ID matrix

| Criterion | Required test IDs |
|---|---|
| E2-001 | `E2-NEG-001`, `E2-NEG-002`, `E2-NEG-003`, `E2-NEG-004`, `E2-NEG-009`, `E2-NEG-025` |
| E2-002 | `E2-NEG-005`, `E2-NEG-006`, `E2-NEG-026`, `E2-NEG-027` |
| E2-003 | `E2-NEG-007`, `E2-NEG-008`, `E2-NEG-024` |
| E2-004 | `E2-NEG-013`, `E2-NEG-014`, `E2-NEG-015`, `E2-NEG-016`, `E2-NEG-039`, `E2-NEG-041` |
| E2-005 | `E2-NEG-010`, `E2-NEG-011`, `E2-NEG-012`, `E2-NEG-028`, `E2-NEG-038` |
| E2-006 | `E2-NEG-009`, `E2-NEG-042` |
| E2-007 | `E2-NEG-023`, `E2-NEG-029`, `E2-NEG-034` |
| E2-008 | `E2-NEG-033`, `E2-NEG-040` |
| E2-009 | `E2-NEG-021`, `E2-NEG-022`, `E2-NEG-023`, `E2-NEG-035`, `E2-NEG-045` |
| E2-010 | `E2-NEG-017`, `E2-NEG-018`, `E2-NEG-034`, `E2-NEG-042` |
| E2-011 | `E2-NEG-024`, `E2-NEG-025`, `E2-NEG-046` |
| E2-012 | `E2-NEG-030`, `E2-NEG-041`, `E2-NEG-010` |
| E2-013 | `E2-NEG-019`, `E2-NEG-020`, `E2-NEG-043`, `E2-NEG-044` |
| E2-014 | `E2-POS-004`, `E2-NEG-031`, `E2-NEG-032` |
| E2-015 | `E2-NEG-009`, `E2-NEG-035`, `E2-NEG-037` |
| E2-016 | §5.2 mapping plus the §14 residual-risk statement |

### 5.2 Deferred-requirement coverage (the PDF-008..PDF-012 close-out)

E1 claimed no coverage of these rows
(`docs/architecture/wp01_packet_e1_acquired_document_handoff.md:841-847,999-1000`);
this table is where they become E2's to answer.

| Requirement | Owning repository | E2 acceptance row | Required test IDs |
|---|---|---|---|
| PDF-008 extraction failure structure and usefulness thresholds | `nexus-scholar-org/scholar-pdf-kit` | E2-004 | `E2-NEG-013`, `E2-NEG-015`, `E2-NEG-016`, `E2-NEG-039`, `E2-NEG-041` |
| PDF-009 requested/effective engines and fallback reasons | `nexus-scholar-org/scholar-pdf-kit` | E2-005 | `E2-NEG-010`, `E2-NEG-011`, `E2-NEG-012`, `E2-NEG-028`, `E2-NEG-038` |
| PDF-010 metadata into extracted frontmatter + registered `DocumentManifestArtifact` | `nexus-scholar-org/scholar-pdf-kit` (candidate) + harness (acceptance/publication) | E2-008, E2-009 | `E2-NEG-033`, `E2-NEG-040`, `E2-NEG-022`, `E2-NEG-035` |
| PDF-011 MCP engine selection/rejection and canonical metadata preservation | `nexus-scholar-org/scholar-agent-kit` (declaration) + `nexus-scholar-org/scholar-pdf-kit` (engine selection) | E2-013 | `E2-NEG-019`, `E2-NEG-020`, `E2-NEG-043`, `E2-NEG-044` |
| PDF-012 `pyyaml` declaration and clean-wheel tests | `nexus-scholar-org/scholar-pdf-kit` (+ harness metapackage dependency list) | E2-014 | `E2-POS-004`, `E2-NEG-031`, `E2-NEG-032` |

## 6. PDF-kit extraction model

The canonical PDF kit owns these serialized models. Names may follow repository
conventions; field semantics and conditions are fixed. The models follow the E1
shape: a self-describing, kit-owned manifest with its own schema version,
identity algorithm version, null-excluded `artifact_checksum`, parent lineage,
structured errors, and an idempotency key.

### 6.1 `ExtractionStatus`

A committed per-item domain status, distinct from the Contract v1
`OperationStatus` used for the batch envelope and distinct from the E1
`AcquisitionStatus`:

- `EXTRACTED`: text was extracted and the usefulness threshold was met.
- `REUSED`: an exact, checksum-bound committed extraction was reused, including
  an exact replay after a prior commit.
- `PARTIAL`: text was extracted but the result is degraded (for example, a
  fallback engine, missing pages, or a truncated structure); a reason is
  mandatory.
- `NO_TEXT_LAYER`: the PDF exposes no usable text layer; the truthful frozen
  `content_status` is `NEEDS_OCR` and a detection reason is mandatory.
- `EXTRACTION_FAILED`: the engine chain produced no usable text. This is the
  status E1 explicitly reserved for E2
  (`docs/architecture/wp01_packet_e1_acquired_document_handoff.md:179`); E1 never
  fabricates it.
- `CANCELLED`: the caller cancelled before commit.
- `FAILED`: an internal, filesystem, or commit failure prevented commit.

Only `EXTRACTED`, `PARTIAL`, and `REUSED` can produce a byte-bearing committed
record, because a byte-bearing record is defined by the existence of extracted
bytes. Failed, no-text-layer, and cancelled items stay visible in
`item_outcomes` with an explicit error or warning, exactly as E1 preserved
negative acquisition results — and those `item_outcomes` are the source from
which the Contract candidate's `FAILED`/`NEEDS_OCR` `DocumentRecord`s are
derived (§1.1 consequence 4, §6.5), so a failure is never invisible and never
dropped just because it owns no file.

Mapping to the frozen `DocumentContentStatus` (`models.py:124-128`) is fixed and
one-way:

| `ExtractionStatus` | `DocumentContentStatus` | `extracted_path` | `extraction_method` |
|---|---|---|---|
| `EXTRACTED` | `VALID` | required | recorded effective method |
| `PARTIAL` | `PARTIAL` | required | recorded effective method |
| `NO_TEXT_LAYER` | `NEEDS_OCR` | must be absent/null | recorded method |
| `EXTRACTION_FAILED` | `FAILED` | must be absent/null | recorded method |
| `CANCELLED` / `FAILED` (pre-commit) | no record emitted | — | — |

A projected status is never silently upgraded, and a `content_status` is never
inferred from a filename, a directory listing, or a successful engine exit.

### 6.2 `ExtractedDocumentRecord`

Required fields of a byte-bearing committed record:

```text
document_id                      # exactly the E1 record's document_id
study_id                         # exactly the E1 record's study_id
acquisition_manifest_id          # E1 ACQ-* identity
acquisition_manifest_sha256      # E1 null-excluded artifact_checksum
acquisition_manifest_path        # E1 e2_reference path, workspace-relative
source_sha256                    # E1 validated source bytes, re-verified
byte_length                      # re-verified
media_type                       # application/pdf
extraction_status                # EXTRACTED | PARTIAL | REUSED
content_status                   # VALID | PARTIAL (a byte-bearing record has text)
extraction_method                # MethodProvenance of the effective engine
requested_engine
requested_engine_version
effective_engine
effective_engine_version
fallback_chain                   # ordered [engine, version, reason] entries
page_count
character_count
extracted_sha256                 # sha256 of the committed extracted bytes
extracted_path                   # workspace-relative POSIX, identity-addressed
extraction_output_format         # MARKDOWN | TEI_XML
access_status                    # preserved from E1, never re-derived
acquisition_method               # preserved from E1
attempts                         # preserved E1 acquisition attempts
```

Preservation rules: `access_status`, `acquisition_method`, `attempts`,
`selected_source_url` (absent for `USER_PATH`), `selected_source`, and
`access_assertion` are carried from the E1 record unchanged. E2 never re-derives
access state, never invents a URL for a `USER_PATH` record, and never rewrites
E1's attempt history.

### 6.3 Engine attempts and the fallback chain

Each engine attempt records:

- ordinal and engine name (`PYMUPDF`, `DOCLING`, `GROBID`, or another
  explicitly declared engine);
- engine version as reported by the runtime, or an explicit `unknown` marker
  with a diagnostic — never omitted;
- the request/response shape that matters (`grobid_url` for an external
  provider, a document-page range when applicable);
- the attempt result, a bounded diagnostic code, and a bounded message;
- whether the attempt was the effective one.

`fallback_chain` is the ordered list of *substituted* attempts, each with a
mandatory reason from a closed vocabulary (for example
`ENGINE_NOT_INSTALLED`, `ENGINE_UNAVAILABLE`, `ENGINE_ERROR`,
`ENGINE_OUTPUT_UNUSABLE`, `ENGINE_LICENSE_MISSING`). The rules:

1. `effective_engine` is the engine whose output was committed. It is always an
   element of the attempt list.
2. If `effective_engine != requested_engine`, the fallback chain is non-empty and
   every entry has a reason.
3. If `effective_engine == requested_engine`, the fallback chain is empty —
   otherwise the record contradicts itself.
4. A failed attempt is recorded even when it produced no output, and its
   diagnostic is bounded. Secrets, tokens, cookies, and proxy credentials are
   never serialized.
5. An external provider engine (`GROBID`) yields
   `extraction_method=EXTERNAL_PROVIDER`; a rule-based local engine
   (`PYMUPDF`) yields `DETERMINISTIC_RULE`; a model-backed engine
   (`DOCLING`) yields `HEURISTIC`. The frozen enum is
   `HUMAN|DETERMINISTIC_RULE|HEURISTIC|LLM|EXTERNAL_PROVIDER|COMPOSED`
   (`models.py:81-87`); E2 uses only these values.
6. Attempt timestamps are provenance only and never participate in the `EXT-`
   identity or the idempotency key.

### 6.4 The extraction manifest (inseparable provenance sidecar)

The sidecar is a kit-owned, self-describing object with its own
`schema_version = "pdf-extraction-manifest-v1"` and
`manifest_type = "pdf_extraction_manifest"`. That type is **not** a Contract v1
`artifact_type`; the frozen registries must keep rejecting it (§1.1, `E2-NEG-021`).

The manifest contains:

- `schema_version`, `manifest_type`, deterministic `manifest_id`, and the
  manifest identity algorithm version;
- workspace, run, protocol, and corpus context;
- `acquisition_manifest_ref`: the E1 `ManifestReference` — `manifest_id`
  (`ACQ-*`), `manifest_type`, `workspace_relative_path`, `artifact_checksum` —
  reusing the existing kit model (`acquisition_models.py:954-975`); **and, in
  every per-document `ExtractedDocumentRecord` (§6.2), the same two reference
  fields are embedded per record — `acquisition_manifest_id` and
  `acquisition_manifest_sha256` — alongside the preserved exact E1
  `document_id` and `source_sha256`.** That per-record embedding in the
  inseparable, explicitly versioned sidecar is precisely how E2 satisfies E1
  handoff lines 451-455: "every E2 document record (or its inseparable, explicitly
  versioned provenance sidecar) MUST embed the reference fields
  `acquisition_manifest_id` and `acquisition_manifest_sha256`, and MUST preserve
  the exact E1 `document_id` and source hash";
- the direct Contract parent reference: the accepted
  `ScreeningDecisionsArtifact` as an `ArtifactReference` (`artifact_id`, `path`,
  `sha256`, `acquisition_models.py:933-951`), used for verification and for
  constructing the emitted `inputs`; it is **not** an `EXT-` parent edge in the
  Contract artifact;
- `parent_lineage_sha256` over the canonical parent references, computed exactly
  as E1 does (`canonical_fingerprint(parent_refs)`;
  `acquisition.py:2668-2670` and its verification at `3064-3070`);
- producer package, version, and commit;
- `usability_profile`: the required versioned usefulness rule
  (`{name, version, minimum_character_count}`) that §6.7(5) applies, so every
  `content_status` is explainable after the fact (§14.1 item 5);
- `records` and `item_outcomes` (§6.1, §6.2), sorted deterministically;
- a canonical stable payload fingerprint and a non-self-referential
  `artifact_checksum` over the canonical manifest with that field set to null —
  the same construction E1 uses (`acquisition.py:2694-2698`) and the same
  verification E1 already implements (`acquisition.py:3031-3037`);
- batch `OperationStatus`, errors, warnings, and the idempotency key.

#### Manifest identity

```text
normalized_extraction_records = sorted committed per-document records by
    study_id, then document_id
extraction_identity_payload = {
  "schema_version": "pdf-extraction-manifest-v1",
  "workspace_id": <accepted workspace_id>,
  "run_id": <run_id>,
  "acquisition_manifest_ref": <canonical E1 manifest reference above>,
  "extraction_records": <normalized_extraction_records>
}
manifest_id = "EXT-" + sha256(canonical_json_bytes(extraction_identity_payload)).hexdigest()[:32]
```

`EXT-` is validated against `^EXT-[0-9a-f]{32}$`, mirroring E1's
`^ACQ-[0-9a-f]{32}$` (`acquisition_models.py:35`, validated at `:835-840`).
Timestamps, retry counters, attempt ordinals, and response headers are excluded
from the identity payload while remaining in the manifest provenance. Document
input order and attempt order are normalized and do not change the identity.

#### Placement

The sidecar lives at `literature/extraction/<run_id>/<EXT-…>.json`, mirroring
E1's `literature/acquisition/<run_id>/<ACQ-…>.json`
(`acquisition.py:584-588,2681-2687,2820-2859,3053-3063`). Its destination is
derived from its own embedded identity, and any mismatch is
`PATH_OUTSIDE_WORKSPACE`/placement failure rather than a convenience write
(`E2-NEG-046`).

### 6.5 Constructing and accepting the frozen `DocumentManifestArtifact`

Only after the extraction manifest is committed does the PDF-kit E2 service
construct the deterministic Contract v1 candidate:

```text
schema_version            1.x (frozen envelope validator, models.py:195-198)
artifact_type             "document_manifest"
artifact_id               ART-…  (deterministic per the acceptance gate's
                           idempotency rule; the harness re-presenting a
                           different payload under the same id is
                           IDEMPOTENCY_CONFLICT)
created_at                RFC3339 UTC
producer                  {package: "scholar-pdf-kit", version, commit}
workspace_id              accepted parent workspace
run_id                    the extraction run id
protocol_fingerprint      equal to both accepted parents
corpus_fingerprint        equal to both accepted parents
inputs                    exactly the accepted ScreeningDecisionsArtifact
                          reference (artifact_id + sha256)
data.documents            one DocumentRecord per document with a determined
                          engine outcome: VALID/PARTIAL carrying its
                          workspace-relative extracted_path, and
                          FAILED/NEEDS_OCR with extracted_path absent (§1.1
                          consequence 4)
```

The candidate set is the set of documents whose engine chain actually ran against
verified bytes, so the manifest is a complete account of the batch rather than a
quiet selection of the successes. Two boundaries follow from the frozen model
and are not negotiable here:

- `DocumentManifestData.documents` has `min_length=1` (`models.py:513-514`).
  A run in which **no** document produced a byte-bearing record therefore
  constructs **no** Contract candidate and publishes no Contract artifact; the fail-closed sidecar with
  `OperationStatus=FAILED` is the authoritative outcome (`E2-NEG-041`). A
  `DocumentManifestArtifact` with an empty `documents` list is a frozen-model
  violation, not a lenient encoding of "nothing worked".
- A batch that has at least one byte-bearing record includes all of its determined
  records, including the failed ones, because `chain.py:335-345` is written to
  catch evidence grounded in a failed or OCR-pending document and therefore
  presupposes that such documents can be published.

This boundary must not reverse the repository dependency. The canonical PDF kit
has no `scholar_harness` dependency, imports no harness module, writes no
Contract registry, and never labels its returned candidate as accepted. Its
standalone API/CLI outcome may expose the candidate and checksum, but an
accepted-artifact reference is absent until a harness caller performs
acceptance.

The bounded harness adapter parses the candidate through the frozen
`DocumentManifestArtifact` model and calls `accept_artifact`, so the frozen
property checks run: workspace/protocol/corpus agreement, parent registration
and parent-hash agreement, the required `screening_decisions` parent
(`acceptance.py:40-45,325-403`), and artifact-id idempotency
(`acceptance.py:311-323`). Only successful acceptance makes the artifact
authoritative and yields an accepted-artifact reference. A rejection is
reported as a rejection: the artifact is not published, no registry entry is
fabricated, and the harness outcome is `PARTIAL` or `FAILED` with the acceptance
issues attached. The chain gate must remain clean for
`DocumentManifestArtifact` (`chain.py:280-293`).

### 6.6 Bound extracted frontmatter

Every authoritative extracted file begins with a YAML header that is **bound** to
the sidecar record. The existing keys are preserved and the lineage keys are
added:

```text
document_id                # the E1 DOC-* identity
study_id
source_sha256              # E1 validated bytes
acquisition_manifest_id    # E1 ACQ-* identity
acquisition_manifest_sha256 # E1 null-excluded artifact_checksum
extraction_engine          # effective engine name
extraction_engine_version  # effective engine version
extraction_requested_engine
extraction_status          # EXTRACTED | PARTIAL | REUSED
content_status             # VALID | PARTIAL | NEEDS_OCR
extracted_sha256           # sha256 of the extracted body bytes
workspace_id
doi                        # normalized DOI when the E1 record has one
title / authors / year     # when supplied by the caller or the extraction
                           # runtime; never inferred from a filename or URL
extracted_at               # provenance only; never in the identity payload
```

Rules: the current key set is
`workspace_id|doi|title|authors|year|extraction_engine|extracted_at` with empty
keys dropped (`extract.py:31-41`; documented at
`docs/kits_surface_matrix.md:217-219` and
`.agents/skills/scholar-pdf-kit/SKILL.md:15`). E2 keeps those keys and adds the
binding keys, and the identity keys (`document_id`, `source_sha256`,
`acquisition_manifest_sha256`, `extracted_sha256`) are **never** dropped. A file
whose frontmatter disagrees with the sidecar is not authoritative
(`E2-NEG-033`). The YAML dependency must be declared (PDF-012, §1.2).

### 6.7 Validation and truthfulness rules for an extraction candidate

A candidate is eligible for commit as a `VALID`/`PARTIAL` record only when all
enabled checks pass:

1. the accepted acquisition manifest and its parent lineage verify (§2.1.1-2);
2. the committed source bytes verify against the E1 `source_sha256` and
   `byte_length` (§2.1.3);
3. the extraction target is inside the canonical workspace root, under the
   identity-addressed extracted path, and no prior valid output is overwritten by
   a different identity;
4. the engine chain completes with at least one recorded attempt and a
   deterministic effective engine (§6.3);
5. the extracted body passes the recorded usefulness rule, evaluated in this
   exact order and on this count basis:
   a. strip the YAML frontmatter block, then the `# {title}` heading the current
      emitter writes unconditionally (`extract.py:43-49`) — that heading is not
      extracted content, and leaving it in is exactly how a stub body would
      clear a naive length check;
   b. the remaining body must be non-empty after `str.strip()`; this rule is
      **subsumed** by (c) and exists only for readability — the count in (c)
      governs, so a record whose count satisfies `minimum_character_count` is not
      failed by (b), and a whitespace-only body fails (c) regardless;
   c. `character_count`, defined as the length of that stripped body in Unicode
      characters after whitespace collapsing, must be `>=
      usability_profile.minimum_character_count`;
   d. `usability_profile` (`{name, version, minimum_character_count}`) is a
      **required, versioned** sidecar field, so a later run can tell why a
      document was `PARTIAL` and a threshold change can never silently
      reclassify an already-committed document (§14.1 item 5). The packet fixes
      the rule and the recording obligation; the numeric default is a declared
      kit configuration, and a sidecar that omits `usability_profile` is
      non-conformant. `E2-NEG-015` compares against the **recorded** value
      rather than a hard-coded constant;
6. `content_status` is derived only from (4) and (5) and the recorded
   degradation reasons;
7. the recorded `extracted_sha256` is computed from the committed body bytes;
8. the `DocumentRecord` fields are derived from the E1 record and the extraction
   result, with no value invented;
9. **single-document successor:** if a document that previously committed as
   `EXTRACTION_FAILED` or `NO_TEXT_LAYER` later extracts successfully, the new run
   commits exactly **one** successor record for the same `document_id` — never a
   second record for the same document, and never a relabelling of the old
   outcome in place. The superseded outcome stays visible in the new sidecar's
   `item_outcomes` alongside the new byte-bearing record, referenced by the prior
   `EXT-` id, and the new `EXT-` id is recomputed over the new normalized records
   (§6.4), so the recovery is auditable rather than a silent overwrite.

Failures are not all the same, and the distinction from §1.1 consequence 5 is
what keeps the batch honest:

- A failure at steps **1-3** (parent, lineage, or source bytes) or at the commit
  itself is a **rejection**: it leaves the prior valid output and the prior valid
  manifest untouched, constructs **no** candidate record, and publishes **no** Contract artifact for that document. It
  is not downgraded to a `FAILED` document, because no engine ever ran against
  verified bytes.
- A failure at steps **4-5** (the engine chain or the usefulness rule) is a
  **determined outcome**: no byte-bearing record is created for that document,
  but the batch still accounts for it truthfully — `EXTRACTION_FAILED` or
  `NO_TEXT_LAYER` in `item_outcomes`, and a `FAILED`/`NEEDS_OCR`
  `DocumentRecord` with `extracted_path` absent in the candidate manifest
  alongside its successful siblings (§6.5). If it is the *only* document, no
  candidate manifest is constructed at all (`models.py:513-514`, `E2-NEG-041`).

## 7. Identity, containment, atomicity, and recovery

### 7.1 Identity reuse and output addressing

E2 reuses the E1 identity; it never re-derives a competing one. For every
committed E1 record, E2 recomputes
`deterministic_document_id(study_id=..., source_hash=..., workspace_id=...,
algorithm_version=record.document_identity_algorithm_version)` — the exact helper
E1 uses at commit and verification time (`canonical.py:193-211`;
`acquisition.py:3071-3081`) — and requires equality with the manifest value. A
mismatch is an identity failure, not an opportunity to re-mint.

The extracted output is **identity-addressed**, for example
`extracted/<document_id>.md`, and never `{stem}.md`. This directly replaces the
current filename-derived naming (`extract.py:102`), which collides across studies
that share a title and cannot be traced back to an identity. TEI output, when a
`GROBID` attempt is effective, is written beside it as
`extracted/<document_id>.tei.xml` and recorded in
`extraction_output_format`.

### 7.2 Legacy raw-path extraction

The existing `scholar-pdf extract <path>` positional form and
`nexus_extract_pdf(pdf_path, …)` remain useful for exploration, but E2 must make
their status unambiguous:

- The CLI keeps working as a **non-authoritative** convenience, and its help
  text says so; it does not claim a Contract artifact, a sidecar, or an
  identity. If E2 routes it through the new service, it must do so through a
  manifest-bound path; if it does not, it must not emit authoritative state.
- The MCP tool is documented as non-authoritative in the registry, the skills,
  and `docs/kits_surface_matrix.md` (`E2-NEG-019`, `E2-NEG-044`).
- Neither surface may write into the authoritative `extracted/` identity paths
  or the sidecar directory.

### 7.3 Commit state machine

Per extracted document, publication is the following state machine. Temporary
files live in the **same directory as their final destination**.

1. **Preflight:** verify the E1 manifest (id, checksum, parent lineage, embedded
   reference), the direct screening parent, workspace-root binding, path
   containment, requested-engine validity, configuration, and the idempotency
   key. No extraction and no output are produced before this succeeds.
2. **Stage:** read the verified bytes and run the engine chain into a uniquely
   named same-directory temporary; never expose the temporary as authoritative.
3. **Validate:** apply §6.7; on failure remove this attempt's temporary and
   preserve prior valid output.
4. **Promote content:** atomically rename the validated body into its
   identity-addressed final path. If that path already holds the same
   `extracted_sha256` for the same identity, coalesce deterministically; never
   overwrite a different identity.
5. **Publish sidecar:** build and validate the extraction manifest, stage it in
   its destination directory, and atomically replace it. **The successfully
   replaced sidecar is the commit marker for extraction state.**
6. **Return the Contract candidate:** the PDF kit returns the frozen
   `DocumentManifestArtifact` candidate and writes no Contract registry. The
   bounded harness adapter parses the candidate and calls `accept_artifact`.
   A rejection is a structured harness failure, never a silent success and
   never a fabricated registry entry; standalone kit outcomes never claim
   acceptance.
7. **Post-commit audit:** append exactly one canonical workspace-manager audit
   event for the successful extraction commit, using the real kit identity, the
   `EXT-` id/checksum, the acquisition manifest ID/checksum, the document ID and
   source hash, the candidate Contract artifact ID, the operation status, and
   the idempotency key. If the harness adapter runs, canonical Contract
   acceptance evidence comes from `accept_artifact`; the extraction event must
   not claim acceptance when step 6 was standalone or acceptance failed.

For an all-failure run, steps 2-4 are skipped, the fail-closed sidecar is still
staged, atomically published, and followed by the appropriate canonical
failure/outcome event: zero extracted records, explicit `item_outcomes`, and
`OperationStatus=FAILED` (`E2-NEG-041`).

All file handles and owned clients close on success, retry, exception, and
cancellation. Cleanup removes only this operation's temporary/orphan output.

### 7.4 Idempotency and recovery

```text
source_payload = {
  "schema_version": "pdf-extraction-manifest-v1",
  "workspace_id": <accepted workspace_id>,
  "run_id": <run_id>,
  "acquisition_manifest_ref": <canonical E1 manifest reference>,
  "documents": sorted [{"document_id", "source_sha256",
                        "requested_engine"} ...]
}
idempotency_key = canonical_fingerprint(source_payload)
```

The payload deliberately excludes timestamps, retry counts, attempt ordinals, and
transient diagnostics. A changed non-volatile payload under an existing key is
`IDEMPOTENCY_CONFLICT`; it cannot overwrite or relabel the earlier sidecar.

An exact replay computes the same key and `EXT-` id, detects the published
sidecar, re-verifies its checksum, its bound source bytes, and the committed
extracted `extracted_sha256`, and reports `REUSED` without re-running the engine
or duplicating the sidecar, candidate, accepted artifact, or audit event. If the
sidecar exists but its extracted body is missing, altered, or its source bytes no
longer verify, recovery fails closed (`E2-NEG-017`, `E2-NEG-040`).

The replay lookup is keyed by the recomputed `EXT-` id, not by the idempotency
key alone; a run whose key matches but whose `EXT-` id differs is a new commit
under §6.7(9) — neither a replay nor a conflict. The two identities are not
redundant: `idempotency_key` covers the request-side payload (workspace, run,
acquisition reference, document set, requested engine), while the `EXT-` id
covers the normalized extraction records and therefore their outcomes. A retry
that succeeds where a previous attempt committed `EXTRACTION_FAILED` keeps the
key but mints a new `EXT-` id, which is precisely the §6.7(9) successor and
must not be reported as `REUSED` or as `IDEMPOTENCY_CONFLICT`.

If the sidecar replace succeeds but the audit append fails, the sidecar remains
the authoritative commit marker; the operation reports a structured
recovery/partial outcome and a rerun with the same key completes the one missing
event exactly once, or returns an already-idempotent `REUSED` result
(`E2-NEG-034`). If the process dies after content promotion but before the
sidecar replace, the content is an orphan until the deterministic key/`EXT-` check
either recovers it under the same identity or removes it; it is never treated as
committed. If it dies after the sidecar replace but before harness Contract
acceptance, the adapter rerun re-presents the same candidate: the acceptance gate answers idempotently
for an identical payload and raises `IDEMPOTENCY_CONFLICT` for a different one
(`E2-NEG-045`).

### 7.5 Collision, naming, and lifecycle requirements

Authoritative extraction storage is addressed by document identity, not by a
smart filename. Two studies whose PDFs share a title, and two documents whose
extracted text is identical, receive distinct documents and distinct outputs.
Concurrent duplicate logical inputs (same workspace, run, accepted study,
acquisition manifest, and bytes) deterministically coalesce to exactly one
committed extraction carrying the one deterministic `EXT-` id; concurrent
distinct identities receive separate paths or a conflict-safe explicit result.
Owned HTTP/session clients for provider engines close on success, retry,
exception, and cancellation; externally supplied clients are not closed by E2.
A valid existing output is never removed by a failed refresh.

## 8. Implementation task packet

```text
TASK_ID: WP01-E2
OBJECTIVE: Implement the deterministic extracted-text boundary in the
  canonical scholar-pdf-kit, add the declared thin MCP boundary for extraction
  in the canonical scholar-agent-kit, and synchronize both into the harness.
OWNER_SURFACE: nexus-scholar-org/scholar-pdf-kit
MCP_ADAPTER_OWNER_SURFACE: nexus-scholar-org/scholar-agent-kit
  (declaration/rejection only)
CONTRACT_ACCEPTANCE_OWNER_SURFACE: nexus-scholar-harness
  (bounded adapter and registry publication only)
DEPENDENCIES_AND_EVIDENCE:
  - the accepted E1 AcquiredDocumentManifest (pdf-acquisition-manifest-v1,
    ACQ-*) at pin 858911f6b7dd5738de94fa749ffc4c65b6d0b70e
  - the accepted ScreeningDecisionsArtifact and its corpus parent
  - the frozen Contract v1 DocumentManifestArtifact / DocumentRecord shape
  - current extraction behavior characterized at §1.4
GOVERNING_REQUIREMENTS:
  - the E2 allocation table in §1.2: PDF-008..PDF-012 are E2 scope
  - this document sections 2-7 and 9
  - the toolkit synchronization rule in DEVELOPER_COMPASS.md
OUTPUTS:
  - typed extraction request/outcome/attempt/record/manifest models
  - kit-owned extraction manifest (pdf-extraction-manifest-v1, EXT-*) that is
    the inseparable provenance sidecar for extracted bytes
  - reuse of the E1 identity, checksum, and canonicalization helpers
  - engine chain with requested/effective engines, versions, and reasons
  - identity-addressed, bound-frontmatter extracted output
  - a deterministic frozen Contract v1 DocumentManifestArtifact candidate
    builder with inputs == [screening_decisions] and truthful content status
  - a bounded harness adapter that parses the candidate through the frozen
    model, calls accept_artifact, and alone exposes an accepted reference
  - a pdf_extraction capability declaration and thin MCP rejection, without
    implementing PDF domain logic in the adapter
  - declared dependencies (pyyaml and any authoritative-path engine dependency)
  - local-fixture tests and public documentation
```

### 8.1 Allowed canonical PDF-kit paths

- `src/scholar_pdf/` extraction service, models, engines, CLI, and public
  exports;
- `tests/` focused extraction/identity/atomicity/engine-chain/path/recovery
  tests and local PDF fixtures;
- `README.md` and package-owned documentation;
- `pyproject.toml` only for demonstrated runtime/test dependencies
  (`pyyaml` and any other dependency an authoritative extraction path needs).

### 8.2 Allowed canonical agent-kit paths

- `src/scholar_agent/capabilities.py` — a **new** `pdf_extraction`
  `CapabilityDeclaration` plus its pure rejection envelope; the existing
  `pdf_acquisition` declaration must not be mutated or broadened;
- `src/scholar_agent/server.py` — the thin declared-unsupported extraction tool
  and truthful documentation of the existing raw-path `nexus_extract_pdf` as
  non-authoritative;
- focused canonical agent-kit tests for the capability registry, the exact
  rejection envelope, zero I/O, and the unchanged E1 boundary;
- canonical agent-kit documentation needed to keep its public surface truthful.

### 8.3 Allowed harness paths after the canonical kit changes land

- `src/scholar_harness/` for the bounded E2 orchestration adapter that invokes
  the PDF kit, parses its candidate as the frozen `DocumentManifestArtifact`,
  calls `accept_artifact`, and returns the accepted reference; this allowance
  does not permit edits under `src/scholar_harness/contracts/`;
- `tools/scholar-pdf-kit/` synchronized snapshot;
- `tools/scholar-agent-kit/` synchronized snapshot when the E2 MCP boundary
  changes the adapter;
- `.agents/plugins/nexus-scholar/plugins.json` full-SHA pins for every changed
  canonical kit;
- generated `packaging/nexus-scholar/nexus_scholar_pins.json`;
- `packaging/nexus-scholar/pyproject.toml` dependency entries that E2's declared
  kit dependencies make necessary;
- focused cross-kit/conformance tests and E2 fixtures
  (`tests/conformance/`), including any E1 fixture/tool-count assertion that E2's
  MCP change makes stale;
- `.agents/skills/scholar-pdf-kit/SKILL.md`, its plugin mirror, the agent-kit
  skill, and its mirror, plus the generated skills bundle;
- `docs/kits_surface_matrix.md`, limited to the E2-relevant PDF
  extraction/API/CLI/MCP capability, status, and manifest rows. **In particular,
  finding 3's `RESOLVED` status changes to "present, non-authoritative" under E2**
  (`docs/kits_surface_matrix.md:63-72`): the "resolution" recorded there is that
  the raw-path `nexus_extract_pdf` now *derives* `title`/`doi`/`workspace_id`
  from the PDF path, and E2 does not remove that behavior — it keeps the
  path-heuristic metadata, but `E2-NEG-043` bars filename-, URL-, and
  regex-derived values from any authoritative frontmatter, sidecar, candidate, or published
  artifact, and `§7.2`/`§9.4` mark the tool non-authoritative. A matrix that
  still advertises finding 3 as simply `RESOLVED` would imply the heuristic is
  safe to rely on, which is exactly the claim E2 forbids;
- this handoff and the compass only when status evidence changes.

### 8.4 Forbidden paths and scope

- `src/scholar_harness/contracts/` models, registries, `acceptance.py`,
  `chain.py`, identifier registry, generated schemas under
  `src/scholar_harness/contracts/schemas/`, the golden fixture
  `tests/fixtures/contracts/v1/two_study_artifact_chain.json`, and
  `docs/architecture/contract_v1_baseline.json` — all frozen and unchanged;
- `docs/architecture/wp01_contract_adoption_handoff.md` (locked; superseded for
  extraction by this document, not edited);
- chunking, embedding, indexing, retrieval, and claim/evidence implementation;
- any other kit's source or vendored tree;
- `workspaces/` scientific content or any real research project;
- vendored-only PDF-kit or agent-kit changes;
- network- or daemon-dependent required tests.

## 9. MCP surface boundary

E1 declared `pdf_acquisition` unsupported on MCP and made that boundary
observable through a registered rejection tool
(`tools/scholar-agent-kit/src/scholar_agent/server.py:644-679`;
`capabilities.py:168-250`). E2 keeps that boundary exactly as it is and adds a
**separate** declaration for extraction:

1. The agent kit's capability registry declares `pdf_extraction` with
   `mcp_supported=false`, owning surfaces `("API", "CLI")`, owner
   `nexus-scholar-org/scholar-pdf-kit`, and the stable non-retryable code
   `UNSUPPORTED_CAPABILITY` (a plain string code is an explicitly supported
   extension point — `capabilities.py:30-34`).
2. Capability discovery and any extraction-shaped MCP request return the
   standard operation envelope: `operation="extract_pdf"`, `status="FAILED"`,
   `artifacts=[]`, `warnings=[]`, and exactly one non-retryable error naming the
   API/CLI alternatives. The envelope is built by pure functions over the
   immutable declaration, so zero I/O is structural, not asserted.
3. The rejection happens **before** any engine import, provider transport,
   temporary or final file creation, sidecar construction, or audit append.
4. The existing `nexus_extract_pdf` remains available as a clearly
   **non-authoritative** convenience: it verifies nothing, identifies nothing,
   derives metadata heuristically from the path
   (`server.py:596-615`), and therefore MUST NOT write into the authoritative
   `extracted/` identity paths, the sidecar directory, or claim a Contract
   artifact. Its docstring, the skills, and the surface matrix must say so.
5. This is a declared unsupported difference, **not** a semantic-parity claim,
   and it does not broaden or re-interpret `pdf_acquisition`. E1's
   `E1-NEG-047` harness assertions must keep passing unchanged.
6. MCP *bundling* parity is a packaging fact, not a semantic one: the agent
   server imports `scholar_pdf.extract` at module import (`server.py:76`), so
   the wheel must carry the extraction module and its declared dependencies
   (E1's `pypdf` R7 precedent). The minimal-dep `--help` smoke must still pass.

## 10. Test conventions and traceability discipline (VAL-001)

### 10.1 Conventions

1. Every `E2-0xx` criterion maps to at least one stable `E2-POS-###` or
   `E2-NEG-###` ID; the matrix in §5.1 is the authority, and an unmapped
   criterion is a packet defect.
2. Required tests are hermetic and scriptable: local PDF fixtures committed to
   the canonical kit, temporary workspaces, fake transports, no network, no
   Grobid daemon, no clock dependence in assertions, no sleep-based races.
3. Tests assert status, no-publication, cleanup, and lineage outcome together. A
   negative case that only asserts a raised exception is incomplete.
4. IDs are required test names or stable parametrized case IDs. This document is
   a **specification**: it does not claim the tests already exist or pass.
5. Provider and daemon engines are exercised through injected fakes in required
   tests; live-provider runs are optional and never a gate.
6. Where a fault must be injected, the injection point is named in the test
   name/parametrization, not chosen implicitly by the test's control flow.
7. Behavioral proofs for the extraction domain live in the **canonical kit**
   repositories. The harness enforces cross-repository obligations (pins,
   vendored-tree drift, frozen-registry rejection, doc-surface parity), exactly
   as it did for E1.

### 10.2 Required fault-injection points and recovery assertions

| Point | Test IDs | Required state/action |
|---|---|---|
| Engine attempt | `E2-NEG-010`, `E2-NEG-038` | No authoritative output; the attempt and its reason are recorded, or the item is `EXTRACTION_FAILED`/`FAILED`. |
| Fallback substitution | `E2-NEG-011`, `E2-NEG-012` | The effective engine and the reason are recorded; an unrecorded substitution is rejected. |
| Body validation | `E2-NEG-013`, `E2-NEG-015`, `E2-NEG-016` | Remove/quarantine the temporary; never publish a stub as `VALID`; preserve prior valid output. |
| Content promotion | `E2-NEG-029` | No partial final; prior valid output and sidecar remain readable. |
| Sidecar replace | `E2-NEG-029` | No newly authoritative sidecar; staged bytes cleaned. |
| Harness-adapter Contract acceptance | `E2-NEG-023`, `E2-NEG-022`, `E2-NEG-035` | The PDF-kit candidate remains non-authoritative; no published artifact or fabricated registry entry exists, and the rejection issues are reported. |
| Post-commit append | `E2-NEG-034` | The sidecar is the extraction commit marker; the rerun appends or reconciles exactly one audit event. |

### 10.3 Mandatory negatives E2 inherits from E1's classes

E2 must cover the E1 negative *classes* that apply to extraction, with the IDs in
§4.2: stale/missing/mismatched parent (`002`, `035`, `036`), cross-workspace
rejection (`004`, `025`), containment and portability (`024`, `046`),
all-failure versus missing manifest (`041`), operation-status mapping (`041`),
cancellation (`041` covers the batch; a cancelled item is never authoritative),
idempotency conflict and exact replay (`017`, `018`, `034`), non-registry
manifest rejection (`021`), and doc-surface parity (`044`).

## 11. Validation commands

The implementation PRs must report exact commands and counts. Adapt only the
canonical-kit command prefix to the checkout environment. Note that the three
named extraction test modules (`tests/test_extraction_contract.py`,
`tests/test_extraction_atomicity.py`, `tests/test_mcp_extraction_capability.py`)
are created by §12 steps 1-2; until they exist, scope the run with
`uv run pytest -k extraction`.

```powershell
# canonical scholar-pdf-kit checkout
uv run pytest tests/test_extraction_contract.py tests/test_extraction_atomicity.py
uv run pytest
uv run ruff check src tests
uv build --wheel

# canonical scholar-agent-kit checkout (declared extraction boundary)
uv run pytest tests/test_mcp_extraction_capability.py
uv run pytest
uv run ruff check src tests
uv build --wheel

# harness after canonical merges, vendoring, and pin updates
uv run pytest tests/conformance/test_e2_extraction_boundary.py
uv run pytest tests/test_cross_kit_contracts.py tests/test_contract_artifact_chain.py tests/conformance/test_mcp_tool_parity.py tests/conformance/test_e1_acquired_document_boundary.py
uv run pytest
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check

# distribution smoke
uv build --wheel packaging/nexus-scholar
$wheel = (Resolve-Path packaging/nexus-scholar/dist/nexus_scholar-*.whl).Path
uvx --from $wheel nexus-scholar --help
uvx --from $wheel scholar-agent --help

# documentation/review gate
git diff --check
git status --short
```

Required test names may differ, but the focused suites must cover every E2
acceptance criterion and the IDs in §4. The four generator `--check` commands
are non-negotiable: E2 changes no contract artifact, so a failure in any of them
is `BLOCKED_BASELINE_DRIFT`, not a regenerated file. All required tests are
offline and deterministic.

## 12. Repository and PR sequence

Each step lists its own gates; a later step must not start before the earlier
step's gates are green at a **merged canonical** commit.

1. **PDF-kit canonical extraction boundary.**
   Branch in the canonical `scholar-pdf-kit` fork. Implement §6 and §7: models,
   sidecar, engine chain, bound frontmatter, identity reuse, atomicity,
   recovery, deterministic Contract candidate construction, CLI/API surface,
   declared dependencies. The kit must not import `scholar_harness`, mutate a
   Contract registry, or claim that a candidate is accepted.
   Gates: focused extraction tests, full kit suite, `uv run ruff check src tests`,
   `uv build --wheel` plus a clean-wheel import and `scholar-pdf extract-run --help`
   smoke, and the frozen-registry rejection check for
   `pdf_extraction_manifest`. Open a PR to
   `nexus-scholar-org/scholar-pdf-kit` and record the full merge SHA.
2. **Agent-kit MCP boundary.**
   Separate fork branch. Add the `pdf_extraction` declaration, the pure rejection
   envelope, the thin tool, and truthful non-authoritative documentation for
   `nexus_extract_pdf`; leave `pdf_acquisition` untouched. Gates: the focused
   agent-kit tests, the **unchanged** E1 boundary tests, `uv run ruff check src
   tests`, and a wheel build whose `--help` still works on a minimal-dep
   environment. Merge and record the full commit SHA.
3. **Harness synchronization.**
   Separate harness branch. Synchronize each changed kit to its exact merged
   commit, update the affected `plugins.json` full-SHA pins, regenerate the
   metapackage pins, implement the bounded E2 adapter that invokes the PDF kit,
   parses its candidate through the frozen `DocumentManifestArtifact`, and
   calls `accept_artifact`, add the E2 conformance test and fixtures (including
   cross-repository drift, frozen-registry rejection, and doc-surface parity
   limbs), update the E2 rows in `docs/kits_surface_matrix.md` and the affected
   kit skills, and add any metapackage dependency E2 made necessary. Gates: the
   full harness suite, the four generator `--check` commands, `uv run ruff check
   scripts/`, the conformance count/freshness gate, and the distribution wheel
   smokes. Open the harness PR through the personal fork; never push a feature
   branch to canonical `origin`, and never open a pin PR against an unmerged or
   floating kit revision.
4. **Closure report and compass.**
   Record the §14 completion report, update the E2 status line in
   `docs/architecture/DEVELOPER_COMPASS.md` §10 (status evidence only), and leave
   `docs/architecture/wp01_contract_adoption_handoff.md` and the frozen contract
   untouched.

## 13. Stop conditions and label semantics

The `BLOCKED_*` values below are planner/reviewer stop labels explaining why
implementation cannot safely continue. They are **not** runtime statuses, not
`ExtractionStatus`/`AcquisitionStatus` values, and not substitutes for the
stable runtime error codes in the structured envelope.

Stop and report the named blocker when:

- Contract v1 must change (a new `artifact_type`, a new `DocumentRecord` field,
  a parent-type change, a registry entry for a kit-owned manifest):
  `BLOCKED_CONTRACT_VERSION_DECISION`;
- an accepted parent or the E1 acquisition manifest cannot be verified:
  `BLOCKED_PARENT_LINEAGE`;
- source bytes cannot be bound to the E1 `source_sha256`:
  `BLOCKED_SOURCE_BINDING`;
- document identity would have to be re-derived differently from E1:
  `BLOCKED_DOCUMENT_IDENTITY`;
- access or provenance facts would have to be invented (for example an OA or
  identity claim derived from a filename, URL, or HTTP success):
  `BLOCKED_ACCESS_PROVENANCE`;
- atomic publication cannot preserve a prior valid artifact:
  `BLOCKED_ATOMICITY_DESIGN`;
- a canonical PDF-kit or agent-kit repository required by E2 cannot be updated or
  verified: `BLOCKED_CANONICAL_REPO`;
- a frozen generated-file check fails: `BLOCKED_BASELINE_DRIFT`.

A runtime engine, filesystem, provider, cancellation, or audit failure is
reported through `ExtractionStatus`, `OperationStatus`, and bounded error codes;
it is never relabelled as a planner `BLOCKED_*` status.

## 14. Completion report

```text
Packet: WP01-E2
PDF-kit canonical repository, PR, and merge SHA:
Agent-kit canonical repository, PR, and merge SHA:
Extraction schema/version:
Sidecar manifest type, id prefix, and placement:
Engine names/versions supported and their optional extras:
Public API/CLI surface and non-authoritative candidate result:
Harness acceptance adapter and accepted-reference surface:
Declared MCP capability (name, mcp_supported, rejection code/operation):
Legacy surfaces retained/deprecated and their authoritative status:
Files changed:
Acceptance criteria covered (E2-001..E2-016):
Deferred PDF rows covered (PDF-008..PDF-012) with test IDs:
Negative fixtures added (E2-NEG-###, per repository):
Targeted/full test results per repository:
Wheel/import smoke results (kit, agent kit, metapackage, entrypoints):
Harness vendored SHAs and plugins.json pins:
Generated-pin check result:
Frozen-contract check results (baseline/schemas/golden fixture):
Residual risks and any blocked decisions:
Reviewer verdict: APPROVE | CHANGES_REQUESTED | BLOCKED
```

An `APPROVE` verdict means the extracted-text boundary is safe for E3 to
consume: identity is reused, lineage is verifiable, status is truthful, and the
Contract candidate exists only after real extraction, and the authoritative
artifact exists only after harness acceptance. It does **not** claim
chunking, indexing, evidence, claims, or synthesis are complete, and it does not
claim MCP semantic parity.

### 14.1 Residual risks and honest limits (must be restated in the report)

1. **The harness does not collect kit suites.** E2's behavioral proofs
   (extraction truthfulness, engine fallback, atomicity, recovery, packaging)
   live in the canonical `scholar-pdf-kit` and `scholar-agent-kit` repositories
   and are executed there. The harness enforces only cross-repository
   obligations: vendored-tree and pin agreement, frozen-registry rejection of
   the sidecar type, and documentation parity. A green harness suite is
   therefore **not** evidence that extraction works; the kit suites are.
2. **MCP semantic parity is limited to packaging.** The agent server imports
   `scholar_pdf.extract` at import time (`server.py:76`), so "extraction ships in
   the wheel" is the parity that exists, mirroring E1's `pypdf` R7 precedent.
   MCP *behavior* is a declared unsupported difference (§9); no E2 result may be
   claimed through MCP.
3. **Import-time dependency declarations must be re-confirmed.** E1 established
   the precedent that a kit dependency needed at package import must be declared
   in the metapackage. E2 must re-run that check for the YAML dependency it puts
   on an authoritative path: if the authoritative emitter imports `yaml` during
   extraction and the kit is bundled in the wheel, the dependency must be
   declared in both `tools/scholar-pdf-kit/pyproject.toml` and
   `packaging/nexus-scholar/pyproject.toml`, and proven by a clean-wheel smoke
   (`E2-NEG-031`).
4. **Provider engines are not gated offline.** `GROBID` and `DOCLING` behavior is
   proven with injected fakes in required tests; live-provider behavior is not a
   gate and must not be claimed in the report.
5. **Useful-text thresholds are a policy, not a fact.** The minimum character
   count and page expectations are recorded with a version in the sidecar. A
   later packet that changes the threshold must version it explicitly; E2 must
   not silently reclassify previously committed documents.
6. **Pre-existing maintenance items remain open** and are not E2's to fix:
   the agent-kit protocol-validation baseline and non-hermetic RAG tests, the
   agent-kit `.gitignore`, and upstream docstring hygiene recorded in
   `docs/architecture/wp01_packet_e1_completion_report.md:167-170`.
