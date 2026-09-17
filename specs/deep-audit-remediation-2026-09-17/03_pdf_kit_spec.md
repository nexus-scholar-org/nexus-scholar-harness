# Scholar PDF Kit Remediation Specification

## Metadata

- Status: Draft for implementation
- Date: 2026-09-17
- Scope: `tools/scholar-pdf-kit` and PDF-facing harness/MCP adapters
- Evidence convention: **Confirmed** findings cite current code; **Hypothesis** items require validation.

## Problem and safety boundary

The PDF kit converts a citation into a legal full-text artifact and then into extractable evidence. A valid container is not proof of correct article identity, and an extraction stub is not evidence. The system MUST NOT claim OA availability, successful extraction, DOI identity, or usable content without recorded checks. It MUST not bypass paywalls. Downloads and extracted files MUST be atomic; failed work MUST not replace valid artifacts. All clients/files MUST close under exceptions and cancellation.

## Architecture and data flow

`AsyncPDFDownloader` resolves DOI metadata via search-kit's HTTP client, selects OpenAlex then Unpaywall URLs, optionally tries publisher patterns/proxy rewrites, streams with aiohttp, validates, and returns `DownloadResult` (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:27-54`, `tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:163-248`). Validation checks binary/trailer/optional structure. Ingest copies a local file then validates (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:250-287`). PyMuPDF/Docling/GROBID produce Markdown or TEI (`tools/scholar-pdf-kit/src/scholar_pdf/extract.py:16-112`). CLI coordinates batch operations and summaries.

## Confirmed findings

1. Downloads stream directly to the final path (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:101-104`) and delete it on failure (`:120-123`), so an interrupted refresh can destroy or expose a partial artifact.
2. Existing files are accepted solely by filename and validation (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:190-194`); no persisted DOI/content binding is checked.
3. `download_batch` constructs `AcademicHttpClient` but never closes it (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:242-248`).
4. Structural validation is applied to ingest (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:274-282`) but the downloaded-file success path uses only `clean_invalid_pdf` (`:106-109`, `:234-237`), despite the constructor exposing `structural_validation` (`:38-54`).
5. Ingest copies directly over the final destination before validation (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:268-282`). A structural failure does not explicitly remove that copied destination.
6. PyMuPDF catches every extraction exception, writes a stub line, and returns a path (`tools/scholar-pdf-kit/src/scholar_pdf/extract.py:46-92`); callers therefore cannot distinguish usable content from failure.
7. Docling silently falls back to PyMuPDF (`tools/scholar-pdf-kit/src/scholar_pdf/extract.py:95-112`) without a structured record of the requested versus effective engine.
8. YAML is imported at runtime (`tools/scholar-pdf-kit/src/scholar_pdf/extract.py:25-43`) but absent from declared dependencies (`tools/scholar-pdf-kit/pyproject.toml:10-20`).
9. The current MCP adapter routes `pymupdf`, `docling`, and `grobid` and derives metadata (`tools/scholar-agent-kit/src/scholar_agent/server.py:580-616`), but successful Docling extraction ignores the supplied metadata and writes raw Markdown (`tools/scholar-pdf-kit/src/scholar_pdf/extract.py:95-109`); Grobid has no metadata parameter (`:115-136`). Engine parity therefore remains incomplete even though the former dead-parameter defect is fixed.
10. Institutional gateway URLs and forward proxies are conflated: requests pass `proxy_url` to aiohttp's `proxy=` transport while a later attempt also rewrites the target through that same gateway (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:78-90`, `:196-228`). Current unit mocks do not prove real gateway semantics.
11. Absence of a PDF URL from OpenAlex/Unpaywall becomes `was_oa=False` (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:177-188`) and the CLI describes it as “Paywalled / Not Open Access” (`tools/scholar-pdf-kit/src/scholar_pdf/cli.py:175-178`). This overstates an unresolved lookup as confirmed access status.
12. `DownloadResult` is too coarse to distinguish resolution failure, not-OA, network failure, validation failure, and reuse (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:27-33`); broad catches collapse failures (`:239-240`, `:286-287`).
13. README examples omit the required `download` subcommand and advertise unsupported CLI `--engine pymupdf`; the surface matrix also retains pre-fix MCP claims. Documentation is not a reliable executable contract until refreshed.

Hypothesis to verify: concurrent smart-name collisions can target the same final path for distinct DOIs. The filename omits DOI when metadata is sufficient (`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:56-70`), but a collision test is required.

## Goals and non-goals

Goals: atomic and identity-bound acquisition; explicit legal/OA and failure outcomes; equivalent validation across download/ingest; evidence-safe extraction; complete lineage; deterministic cleanup. Non-goals: paywall circumvention, OCR quality research, asserting semantic correctness solely from PDF syntax, or changing source licensing policy.

## Normative requirements

Requirement IDs: the numbered requirements below carry stable IDs `PDF-001`…`PDF-017`
(requirement *n* = `PDF-0nn`). Regression tests and the traceability ledger required
by `11_validation_and_test_plan.md` (VAL-001, §11–§12) MUST reference these IDs.

1. Every download/ingest MUST write to a unique same-directory temporary file and atomically replace only after all enabled validations pass.
2. An existing artifact MUST be reused only when its manifest binds normalized DOI, checksum, byte length, validation profile, and final path.
3. Every operation MUST return a versioned structured outcome with stage, status, source URL class, OA state, attempts, validation results, checksum, and sanitized error.
4. `not_open_access`, `not_found`, `network_failed`, `invalid_pdf`, `identity_mismatch`, `extraction_failed`, `reused`, and `success` MUST be distinguishable.
5. `structural_validation=True` MUST apply equally to network downloads, ingest, and reused artifacts.
6. Invalid or failed temporary files MUST be removed; a previously valid final file MUST remain untouched.
7. Owned aiohttp and AcademicHttpClient instances MUST close on success, exception, and cancellation; externally supplied clients MUST not be closed.
8. Extraction MUST fail structurally when parsing fails or content is below a documented usefulness threshold. A stub MAY be diagnostic output but MUST NOT be a success artifact.
9. Requested and effective extraction engines plus fallback reasons MUST be recorded in frontmatter/outcome.
10. `workspace_id` and `study_id` (when known), normalized DOI, title, authors, year, source PDF checksum, engine/version, and extraction timestamp MUST flow through CLI/API/MCP whenever known. Missing values MUST remain explicitly missing. `study_id` is required by the downstream RAG identity contract (`05_rag_kit_spec.md` requirements 1–3 and `10_cross_kit_contracts.md` XC-001a); the PDF kit MUST carry it through to extracted frontmatter whenever it can be resolved, and MUST NOT substitute `workspace_id` for it.
11. MCP `engine` MUST select a supported engine or reject the request; every output engine MUST preserve canonical identity/metadata through either the artifact or an inseparable sidecar manifest.
12. `pyyaml` MUST be a declared direct dependency if YAML remains required.
13. Smart filenames MUST be collision-safe and stable; distinct DOI identities MUST never overwrite one another.
14. Summary/manifest writes MUST be atomic and machine-readable. Success counts MUST include only committed, validated artifacts.
15. No OA status or article identity MAY be fabricated from a successful HTTP response or filename alone.
16. Institutional URL gateways and transport-level forward proxies MUST be separately configured, validated, and tested. The same value MUST NOT implicitly serve both roles.
17. Failure to resolve a legal OA URL MUST be reported as `unresolved_no_legal_oa_copy_found` (or equivalent), not as confirmed paywall status.

## API, data, and CLI behavior

Replace the boolean-centered result with a backward-compatible `PDFOperationOutcome` projection. Include `operation_id`, normalized DOI, `status`, `was_oa: true|false|null`, selected source, attempted sources, temporary/final paths, checksum, validation report, metadata provenance, and error category. Add `ExtractionOutcome` with requested/effective engine, fallback chain, page/character counts, frontmatter, source checksum, and committed output.

CLI MUST emit a JSON summary option and deterministic exit statuses: zero only when every requested operation reaches an allowed terminal state; `not_open_access` is a truthful non-success, not a network failure. Preserve current human tables. Extraction should accept explicit metadata/manifest association rather than reconstructing identity from stems.

## Migration and backward compatibility

- Keep `DownloadResult.success`, `file_path`, and `was_oa` as deprecated projections for one release.
- Existing PDFs without manifests may be validated and adopted only via an explicit migration command that computes checksums and records unresolved identity.
- Continue reading existing extracted Markdown; require stronger frontmatter only for new committed outputs.
- Coordinate MCP and harness changes before making outcome-only APIs mandatory.

## Delivery plan

### P0

1. Atomic download/ingest, preservation of existing valid files, and cleanup tests.
2. Close the search HTTP client and all sessions reliably.
3. Enforce structural validation consistently.
4. Replace extraction stubs-as-success with `ExtractionOutcome` failures.
5. Normalize metadata across PyMuPDF, Docling, Grobid/TEI sidecars, and declare PyYAML.

### P1

1. Add checksum manifests and identity-bound reuse.
2. Introduce complete status taxonomy and JSON CLI summaries.
3. Make smart naming collision-safe.
4. Record fallback engine/source provenance and separate gateway from forward-proxy configuration.

### P2

1. Add legacy adoption tooling, extraction usefulness profiles, and bounded observability metrics.
2. Consider content-identity checks (title/DOI text) only as explicitly probabilistic signals.

## Failure-focused test matrix

| Area | Cases | Required assertion |
|---|---|---|
| Download | timeout mid-stream, cancellation, 404, 429, HTML, truncated PDF | no partial final; classified outcome; bounded retry |
| Replacement | valid existing file plus failed refresh | original bytes/checksum preserved |
| Validation | magic failure, absent EOF, malformed structure, encrypted PDF | profile-specific result; consistent paths |
| Ingest | source equals destination, copy failure, structural failure | safe temporary path; no source damage |
| Reuse | matching manifest, wrong DOI, changed bytes, stale profile | only exact binding reused |
| Collision | same smart metadata/different DOI, concurrent duplicate DOI | separate identity-safe paths or deterministic coalescing |
| Cleanup | success, exception, cancellation | all owned clients/files closed; temps removed |
| Extraction | fitz error, zero text, encrypted, Docling fallback, GROBID error | failure/fallback explicit; no false success |
| Metadata | API/CLI/MCP with complete/partial metadata | known lineage preserved; no invented values |
| Persistence | disk full/rename failure/summary failure | artifact/manifest transaction remains consistent |

## Definition of done

All P0 tests pass across supported platforms; no injected failure leaves a partial final file or leaked client; every successful extraction contains usable content and source lineage; MCP/API/CLI agree on status and engine; legal OA boundaries remain intact; canonical kit repo, vendored tree, and pin are synchronized.

## Dependencies and risks

The kit depends directly on search-kit's HTTP client (`tools/scholar-pdf-kit/pyproject.toml:18-20`), so search outcome/retry changes require coordination. Atomic replace semantics differ on Windows when targets are open. Checksums add I/O cost. Strict extraction thresholds can reject image-only PDFs; classify them as `ocr_required`, not invalid evidence.

## Documentation updates

Update README, API, resolution/download, extraction, naming/ingestion and pipeline docs, `.agents/skills/scholar-pdf-kit/SKILL.md`, and `docs/kits_surface_matrix.md` with status schemas, legal boundary, atomic behavior, validation profiles, manifest format, fallback semantics, metadata requirements, and executable CLI/MCP examples.
