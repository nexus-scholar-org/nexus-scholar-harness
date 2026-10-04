---
name: scholar-pdf-kit
description: Instructions for using the scholar-pdf-kit Python API and CLI to discover, download, validate, and extract Open Access PDFs with YAML frontmatter.
---

# `scholar-pdf-kit` Skill Instructions

You are an expert academic research agent equipped with `scholar-pdf-kit`. This toolkit automatically resolves DOIs to legal Open Access PDFs via a multi-source cascade (OpenAlex, Unpaywall, arXiv, bioRxiv), validates binary `%PDF-` magic-byte integrity, and extracts structured section Markdown with standard YAML frontmatter.

## Core Capabilities
1. **Multi-Endpoint Open Access Cascade**: Resolves legal OA full-text across OpenAlex, Unpaywall, bioRxiv/medRxiv, and arXiv direct links.
2. **Concurrent & Resilient Downloading**: Asynchronous retrieval with exponential backoff and paywall HTML redirect rejection.
3. **Strict Binary Signature Validation**: Requires `%PDF-<major>.<minor>` magic bytes within the first 1024 bytes, a `%%EOF` trailer within the final 8 KB, and a 10 KB size floor; removes corrupted HTML/paywall block pages. Optional `--strict-validate` runs pypdf structural parsing (encryption-tolerant) as a second gate.
4. **Smart Canonical Naming**: Formats filenames as `{year}_{author}_{title}.pdf` and exports structured metadata logs.
5. **Section-Aware Markdown Extraction**: Converts PDFs to Markdown via `PyMuPDFEngine` or `DoclingEngine` preserving headers, tables, and injecting YAML frontmatter (`workspace_id`, `doi`, `title`, `authors`, `year`, `extraction_engine`, `extracted_at`; empty keys are dropped).
6. **Acquired-Document Boundary (WP01-E1)**: parent-bound, deterministic acquisition of exact PDF bytes for an *accepted* study (discovery download or `USER_PATH` ingest), publishing a `pdf-acquisition-manifest-v1` manifest. **API/CLI only — not available on MCP.**
7. **Extracted-Text Boundary (WP01-E2)**: parent-bound, deterministic extraction of committed PDF bytes, publishing a `pdf-extraction-manifest-v1` sidecar plus a non-authoritative `document_manifest` Contract v1 candidate. **API/CLI only — not available on MCP.**

---

## Acquired-document boundary (WP01-E1)

**API:** `scholar_pdf.acquisition` (typed request/outcome models in
`scholar_pdf.acquisition_models`: `AcquisitionRequest`, `AcquiredDocumentManifest`,
`AcquisitionRunConfig`, `AcquisitionBatchOutcome`; parent-binding helpers in
`scholar_pdf.contract_parents`).

**CLI:** `uv run scholar-pdf acquire <config.json> --audit-logger <path-to-log_event.py>`
— a serializable
`AcquisitionRunConfig` in, a standard operation envelope out. JSON envelope on stdout;
`--human` adds a rendered table; exit code mapped from `OperationStatus`. API and CLI
route through the *same* public domain service and
report the same `OperationStatus`, per-item `AcquisitionStatus`, errors, warnings, and
manifest reference.

- **Deterministic output.** One immutable `pdf-acquisition-manifest-v1` document per
  run, committed atomically and addressed by an opaque `ACQ-<32 hex>` identity derived
  from canonical content (never from a title, filename, or HTTP success). The manifest
  is the **commit marker**: an interrupted or torn write publishes nothing new.
- **Parent binding.** Every request must bind two already-accepted Contract v1
  artifacts — `corpus_snapshot` and `screening_decisions` — by `artifact_id`, `sha256`,
  and workspace-relative POSIX path. A request without accepted parents fails preflight.
- **Every output resolves inside the canonical workspace root.** `..`, absolute, drive,
  separator, and symlink escapes fail with `PATH_OUTSIDE_WORKSPACE`; final content paths
  are document-identity addressed (`…/DOC-<32 hex>.pdf`).
- **Fail-closed.** Unresolved legal OA is `UNRESOLVED`, never `RESTRICTED_CONFIRMED` and
  never an empty success. All-failure batches still publish a manifest with `records=[]`
  and `OperationStatus=FAILED`, which is distinguishable from a missing manifest.
- **Not a Contract v1 registry type.** `pdf_acquisition_manifest` is kit-owned. Passing
  it to the frozen harness acceptance/chain registries is rejected as
  `UNSUPPORTED_ARTIFACT_TYPE` and **no registry entry is fabricated**.

> **MCP: `UNSUPPORTED_CAPABILITY`.** PDF acquisition is **not** served on the MCP
> surface. The agent kit declares capability `pdf_acquisition` with
> `mcp_supported=false` and answers with `operation="acquire_pdf"`, `status="FAILED"`,
> `artifacts=[]`, and one non-retryable `UNSUPPORTED_CAPABILITY` error — before any
> provider transport, file, manifest, or audit I/O. This is a declared unsupported
> difference, **not** a parity claim. Use the CLI/API above.

Conformance: `tests/conformance/test_e1_acquired_document_boundary.py`.

---

## Extracted-text boundary (WP01-E2)

Parent-bound, deterministic extraction of **committed PDF bytes** for an *accepted*
study, producing a `pdf-extraction-manifest-v1` sidecar and a `document_manifest`
Contract v1 **candidate**. **API/CLI only — not available on MCP.**

**API:** `scholar_pdf.extraction.PDFExtractionService` (typed models in
`scholar_pdf.extraction_models`: `ExtractedDocumentRecord`, `ExtractionRequest`,
`ArtifactRecordProjection`; the Contract v1 candidate builder in
`scholar_pdf.contract_candidate.build_document_manifest_candidate`).

**CLI:** `uv run scholar-pdf extract-run <config.json> --audit-logger <path-to-log_event.py>`
— a serializable run config in, a standard operation envelope out. The legacy
`uv run scholar-pdf extract` (positional raw path, CLI engines `docling|grobid` only)
remains as a non-authoritative convenience; **the parent-bound path is `extract-run`**.

- **The candidate is non-authoritative.** The kit stamps
  `contract_acceptance="not_performed_by_kit"`; only the harness adapter
  (`scholar_harness.extraction_adapter.accept_extraction_candidate`) can accept it, and
  it binds the accepted `screening_decisions` parent. Until then there is no accepted
  `artifact_id`/`published_path` to cite.
- **Parent binding.** Every request must bind **exactly one** already-accepted
  Contract v1 artifact — `screening_decisions` — by `artifact_id`, `sha256`, and
  workspace-relative POSIX path, with the corpus bound by `corpus_fingerprint` as a
  transitive ancestor through the screening chain. (E1's `acquire` request is the one
  that really does bind both `corpus_snapshot` and `screening_decisions`; the E2 request
  model forbids extra fields, so a config still carrying a `corpus_snapshot` key is
  rejected explicitly instead of ignored.) A request without the accepted parent fails
  preflight, and a parent bound to another workspace is rejected.
- **Deterministic identity.** A record is addressed by an opaque `DOC-<32 hex>`
  identity derived from study + source hash + workspace; never from a title or filename.
  The sidecar is the commit marker: an interrupted or torn write publishes nothing.
- **Fail-closed and truthful.** No usable text is `FAILED` or `NEEDS_OCR`, never an
  empty success; a `VALID`/`PARTIAL` record always carries a workspace-relative
  `extracted_path`. Every output resolves inside the canonical workspace root — `..`,
  absolute, drive, separator, and symlink escapes fail with `PATH_OUTSIDE_WORKSPACE`.
- **Not a Contract v1 registry type.** `pdf_extraction_manifest` is kit-owned. Passing
  it to the frozen harness acceptance/chain registries is rejected as
  `UNSUPPORTED_ARTIFACT_TYPE` and **no registry entry is fabricated**; the registries
  stay frozen at the six Contract v1 types.

> **MCP: `UNSUPPORTED_CAPABILITY`.** PDF extraction is **not** served on the MCP
> surface. The agent kit declares capability `pdf_extraction` with
> `mcp_supported=false` and answers with `operation="extract_pdf"`, `status="FAILED"`,
> `artifacts=[]`, and one non-retryable `UNSUPPORTED_CAPABILITY` error — before any
> engine execution, extracted text, sidecar, Contract artifact, or audit I/O. This is a
> declared unsupported difference, **not** a parity claim. Use the CLI/API above.
> (`nexus_extract_pdf` still exists as the older, non-authoritative PyMuPDF tool; it is
> not the parent-bound E2 path.)

Conformance: `tests/conformance/test_e2_extraction_boundary.py`.

---

## Runtime acceptance of the E2 output (harness, E2-RUNTIME-ACCEPTANCE-ADOPTION)

The kit publishes a **non-authoritative candidate**; the harness producer is what turns
committed Stage 5 output into an accepted Contract v1 `document_manifest` that Stage 6
actually consumes. It adds no second gate — it hands the candidate to the frozen adapter
`scholar_harness.extraction_adapter.accept_extraction_candidate`, which owns acceptance,
the registry entry, the published path, the rejection record, and idempotency.

**CLI:** `uv run scholar-harness extract <status|publish|index> <workspace>` (also
`python src/scholar_harness/agent_extract.py ...`).

- **Trusted context, never the candidate.** The `AcceptanceContext` limbs are derived
  from *recorded state only*: `project.json` → `registered_workspace_id` (a
  `WSP-<32 hex>` minted at inception — the project slug is a label, never an identity),
  `protocol.json` → `scholar_protocol` canonical fingerprint, and the accepted
  `corpus_snapshot` → `corpus_fingerprint`. That context travels on the candidate as
  `Candidate.context` and is handed to the gate as `expected=`; it is never rebuilt from
  the candidate payload, because a payload-derived expectation always agrees with the
  payload it is checking. A candidate limb that disagrees is refused by the gate.
- **Scientific lineage.** Every included study must resolve to an accepted
  `screening_decisions` artifact carrying its `INCLUDE` decision, and the accepted
  screening run must match the corpus generation. A study admitted by an amended
  protocol, or by a screening decision that never included it, is refused.
- **Fail-closed refusals.** Legacy `Extracted content from …` stubs, bodies under the
  200-character usability threshold, unreadable frontmatter, a file whose frontmatter
  claims another study or DOI, a missing or unusable accepted generation, a registry
  path that is not workspace-relative, a study PDF whose link resolves outside the
  workspace, and provider/indexer failure are all typed refusals or `FAILED` — never an
  empty success, and never a fabricated registry entry.
- **CRLF on Windows.** The kit's frontmatter grammar is LF-only, and Stage 5 on Windows
  commits CRLF. The producer normalizes to LF before parsing and records both the
  on-disk and normalized-body hashes plus `line_endings_normalized: true`.
- **Skips are disclosed, never silent.** A *registered* artifact that cannot be used is
  not refused — passing it over is correct — but it is also never invisible. Skipped
  artifact ids and reasons (`OTHER_GENERATION`, `ACCEPTED_ARTIFACT_UNREADABLE`,
  `CORPUS_SNAPSHOT_INVALID`, …) appear in `skipped_registry_entries` on the outcome, in
  the publication record, in the `DOCUMENT_MANIFEST_PUBLISHED` event parameters, and in
  `extract status`. A corrupt entry from an older generation is then visible as an entry
  that existed, rather than looking like one that never did.
- **A refusal after acceptance does not un-accept it.** The frozen `DocumentRecord` has
  no body field, so an edited body yields the *same* `artifact_id`; republishing it would
  report an idempotent replay over bytes that were never accepted and overwrite the
  record. That is refused with `STALE_EXTRACTED_BODY`, leaving the accepted manifest and
  its record byte-identical. An unchanged body still replays idempotently.
- **Provenance is harness-owned.** The publication record lives at
  `literature/extraction_publications/<ART-…>.json` with per-document source kind/hash,
  extraction method, and the registered parent. It is **not** the kit's
  `pdf-extraction-manifest-v1` sidecar and is never presented as one.
- **Indexing is an observation, not a claim.** `extract index` hands *accepted*
  documents to `ScholarIndexer` and records what actually happened; indexing zero
  documents is `FAILED`, and Stage 6 re-reads the accepted manifest rather than the
  provenance record. It also refuses with `DOCUMENT_MANIFEST_NOT_ACCEPTED` **before**
  constructing Stage 6, so a workspace that has never published gets no
  `rag/chroma_db` directory and no embedding-model download.

Acceptance evidence: `tests/e2e/test_extraction_runtime_acceptance.py`.

---

## Quick CLI Cheat-Sheet

All commands should be executed via `uv run`:

```bash
# 1. Download by Single DOI
uv run scholar-pdf download --doi 10.1371/journal.pbio.3000246 --output downloads/

# 2. Bulk Download from Screening Output with Smart Naming
uv run scholar-pdf download \
  --input workspaces/<project-slug>/literature/included.json \
  --output workspaces/<project-slug>/pdfs/ \
  --smart-names \
  --export json

# 3. Extract Section-Aware Markdown (legacy raw-path CLI; engines: docling | grobid only)
uv run scholar-pdf extract \
  workspaces/<project-slug>/pdfs/ \
  --output workspaces/<project-slug>/extracted/ \
  --engine docling
# NOTE: positional PDF file/dir path — there is NO --input flag and NO --engine pymupdf
#       (PyMuPDF is the API/MCP default; the CLI only offers docling/grobid).
#       This legacy command is NOT the parent-bound path — that is `extract-run` (#7).

# 4. Ingest an Existing PDF Manually
uv run scholar-pdf ingest my_paper.pdf --doi 10.1038/35057062 --smart-names

# 5. Download Through an Institutional Proxy (Cloudflare/WAF bypass)
#    attempt 3 automatically re-runs OA + direct-PDF candidates through the proxy
uv run scholar-pdf download \
  --input workspaces/<project-slug>/literature/included.json \
  --output workspaces/<project-slug>/pdfs/ \
  --proxy https://www.sndl1.arn.dz \
  --proxy-style subdomain      # auto | subdomain | ezproxy | prefix

# 6. WP01-E1 Acquired-Document Boundary (API/CLI only; NOT on MCP)
#    Parent-bound, fail-closed acquisition publishing a deterministic
#    pdf-acquisition-manifest-v1 (ACQ-<32hex>), bound to accepted
#    corpus_snapshot + screening_decisions parents.
uv run scholar-pdf acquire workspaces/<project-slug>/acquisition_run.json \
  --audit-logger .agents/skills/workspace-manager/scripts/log_event.py

# 7. WP01-E2 Extracted-Text Boundary (API/CLI only; NOT on MCP)
#    Parent-bound, fail-closed extraction of committed PDF bytes. Publishes a
#    pdf-extraction-manifest-v1 (EXT-<32hex>) sidecar plus a NON-AUTHORITATIVE
#    document_manifest candidate; only the harness adapter
#    (scholar_harness.extraction_adapter.accept_extraction_candidate) can accept it.
uv run scholar-pdf extract-run workspaces/<project-slug>/extraction_run.json \
  --audit-logger .agents/skills/workspace-manager/scripts/log_event.py

# 8. Harness runtime acceptance of the E2 output (E2-RUNTIME-ACCEPTANCE-ADOPTION)
#    Accepts the Stage 5 committed extraction through the FROZEN adapter and
#    publishes the Contract v1 document_manifest Stage 6 consumes. Fail-closed:
#    a stub, a short body, a mismatched frontmatter, or a missing accepted
#    screening parent refuses and publishes nothing.
uv run scholar-harness extract status  workspaces/<project-slug>
uv run scholar-harness extract publish workspaces/<project-slug> --index
uv run scholar-harness extract index  workspaces/<project-slug>
```

---

## Programmatic Python API

```python
import asyncio
from pathlib import Path
from scholar_pdf.downloader import AsyncPDFDownloader
from scholar_pdf.extract import PyMuPDFEngine

async def main():
    dois = ["10.1371/journal.pbio.3000246", "10.7717/peerj.4375"]

    # 1. Initialize Downloader (add proxy_url/proxy_style to re-run
    #    failures through an institutional proxy; optional pypdf gate)
    downloader = AsyncPDFDownloader(
        output_dir=Path("workspaces/my-project/pdfs"),
        use_smart_names=True,
        proxy_url="https://www.sndl1.arn.dz",
        proxy_style="subdomain",      # auto | subdomain | ezproxy | prefix
        structural_validation=True,
    )

    # 2. Batch Download (Async)
    results = await downloader.download_batch(dois)
    for res in results:
        if res.success:
            print(f"Downloaded OA PDF: {res.doi} -> {res.file_path}")

            # 3. Extract Markdown with YAML Frontmatter
            md_path = PyMuPDFEngine.extract_markdown(
                res.file_path,
                output_dir=Path("workspaces/my-project/extracted"),
                metadata={"doi": res.doi, "workspace_id": "SCI-000001"}
            )
            print(f"Extracted Markdown: {md_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Verified surface, MCP mapping & knowledge

- **Cascade**: OpenAlex `best_oa_location` → Unpaywall → publisher direct-PDF
  (IEEE/Springer/arXiv patterns) → optional institutional proxy rewrite.
- **Validation**: ≥ 10 KB size floor + `%PDF-` within first 1024 bytes + `%%EOF`
  within final 8 KB; optional pypdf structural gate (`--strict-validate`,
  encryption-tolerant). Invalid files are auto-deleted.
- **Frontmatter is only complete via the Python API.** `PyMuPDFEngine.extract_markdown(
  pdf, output_dir, metadata=…)` injects `workspace_id`/`doi`/`year`/`authors` from the
  `metadata` dict. The **MCP `nexus_extract_pdf` drop filter never passes metadata** —
  extracted files contain only stem-derived `title` + `extraction_engine` +
  `extracted_at`; their `doi` is silently lost, degrading downstream RAG DOI/enrichment.
  Re-annotate frontmatter after any MCP extraction.
- **Env**: `MAILTO`, `DOWNLOAD_DIR`, `MAX_CONCURRENT_DOWNLOADS`, `DOWNLOAD_TIMEOUT`,
  `PROXY_URL`/`PROXY_STYLE`, `PDF_STRUCTURAL_VALIDATION`,
  `ENABLE_PUBLISHER_DIRECT_PATTERNS`.
- **PyMuPDF is imported as `fitz`**; `pyyaml` is an undeclared transitive dep.
- **"Success" ≠ content**: extraction writes a stub marker line on parse failure; always
  spot-check extracted markdown non-empty.

## Agent Guidelines & Best Practices

- **Paywall Recognition**: Not all academic literature is Open Access. If resolution reports `was_oa=False`, clearly inform the user that no legal Open Access copy is available. Do not attempt to bypass commercial paywalls with web scrapers.
- **Frontmatter Preservation**: Always ensure extracted markdown contains YAML frontmatter (`workspace_id`, `doi`, `title`, `year`) before handing off to `scholar-rag-kit` for chunking and vector indexing.
