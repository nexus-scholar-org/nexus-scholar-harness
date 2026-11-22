# Scholar PDF Kit

> Status (2026-11-22, M12a Part K): downloading (`download`, `ingest`, `AsyncPDFDownloader`) is **production** (decision 2026-11-21, M12a items 15, 21 and 27); reading PDFs (`extract`, `extract-run`) and E1 `acquire` are parked. The kit is `src/scholar_pdf/` in the one `nexus-scholar` package; install `nexus-scholar` (the old kit repository and its install steps are obsolete).

**Scholar PDF Kit** downloads the open-access PDFs of papers by DOI and records which file is which paper.

It asks [OpenAlex](https://openalex.org/) (only with `SCHOLAR_OPENALEX_KEY`) and [Unpaywall](https://unpaywall.org/) for the open locations they list and takes the best open copy with a direct PDF address: published version, then accepted manuscript, then submitted version or preprint. It never builds a publisher address, never requests a landing page, never uses an institutional proxy and never poses as a browser: every request names the app and its contact (`nexus-scholar/<version> (mailto:…)`). It does not infer legal access from an HTTP response.

## How a download works

1. **Lookup**: OpenAlex (with its key) and Unpaywall, once each per DOI; a service's closed evidence (`is_oa: false`, `oa_status: closed`) overrides its `pdf_url`.
2. **Fetch**: at most three listed addresses, best version first. A 400, 401, 403, 404, 410 or 451 is not retried; a 5xx, a timeout or a 429 with a short `Retry-After` is.
3. **Checks**: `%PDF-` header, `%%EOF` trailer, a 10 KB size floor (reported as such), optional pypdf structure (`--strict-validate`); with the `pdf` extra, the DOI and title are looked for on the first two pages ("doi found", "title found", "not found: check it"; "not checked" without it).
4. **Storage**: `DOC-<sha256[:32]>.pdf`, never overwriting; a copy where the drive has no hard links.
5. **Manifest**: one JSON line per DOI asked in `download-manifest.jsonl` (or `--manifest PATH`); no file is kept without its row.

## Setup

```bash
uv sync --extra dev --extra pdf   # the pdf extra adds PyMuPDF for the identity check
export SCHOLAR_MAILTO=you@example.org        # required
export SCHOLAR_OPENALEX_KEY=...              # optional; without it only Unpaywall is asked
```

## Command Line Interface (CLI)

### Download by DOI
```bash
uv run scholar-pdf download --doi 10.7717/peerj.4375 --output pdfs/
```

The summary names the copy taken (version, licence, source, provider), prints the PDF requests each DOI cost and what each address answered, and the path of the manifest. Exit codes: `0` every DOI has its file; `3` a lookup failed (run again later); `1` a listed address gave no PDF, or another failure; `4` open access but no direct PDF address listed; `5` no open copy listed; `2` a usage error (a missing `--input` file among them).

### Download the included records
```bash
uv run scholar-pdf download --input literature/included.json --output pdfs/ --manifest pdfs/download-manifest.jsonl
```

Each record's DOI (`doi` or `external_ids.doi`) is asked; its id (`study_id`, `record_id`, `workspace_id` or `id`) and title go into its manifest row. `--export json|bibtex` adds one entry per DOI to `download_summary.*`, written atomically.

### A PDF you already have
```bash
uv run scholar-pdf ingest my_paper.pdf --doi 10.1038/s41586-023-0001 --output pdfs/ --study-id SCI-000002
```

The file is checked, stored as `DOC-*.pdf` with the access status `USER_PROVIDED`, and given its manifest row; the command exits `1` when nothing is stored.

### Contract v1 parent-bound acquisition (WP01-E1)

The `acquire` API and command are the authoritative path for Contract v1
research workspaces. They require a canonical `AcquisitionRunConfig`, accepted
corpus/screening parents, a canonical workspace-root binding, and the
workspace-manager audit logger. The service verifies the parent lineage before
writing any artifact, streams into a same-directory staging file, validates the
bytes, atomically promotes content to `pdfs/acquired/<document_id>.pdf`, and
then publishes the deterministic acquisition manifest.

```bash
uv run scholar-pdf acquire acquisition-config.json \
  --audit-logger /path/to/workspace-manager/scripts/log_event.py
```

The command emits JSON. Exit codes are `0` for success, `2` for a partial
batch, `1` for a failed batch, and `130` for cancellation. The manifest records
`SUCCESS`, `PARTIAL`, `FAILED`, or `CANCELLED`; an unresolved provider result is
not a paywall determination, and a provider or transport failure is not an
empty successful result. Content identities are deterministic `DOC-*` identities
derived from the validated bytes and scoped by workspace and study. Manifests contain
only workspace-relative POSIX paths, parent hashes, validation results,
attempts, and redacted source evidence—never absolute paths, credentials, or
provider tokens.

The programmatic entry point is `PDFAcquisitionService.acquire(...)`; use an
injected transport and audit sink for hermetic tests. Replaying the same batch
is idempotent, while a different semantic request in the same run, stale parent
lineage, changed bound bytes, or path traversal fails closed. `USER_PATH`
sources are copied only when the researcher has explicitly authorized the
read-only input; network sources never fabricate legal-access status from a
successful HTTP response. MCP acquisition is explicitly unsupported in E1; the
E1 MCP surface must return `UNSUPPORTED_CAPABILITY` until its separately governed
implementation is available.

### Contract v1 deterministic text extraction (WP01-E2)

The `extract-run` API and command are the authoritative path for turning acquired
PDFs into text. They require the same canonical run config, accepted
corpus/screening parents, canonical workspace-root binding, and audit logger as
`acquire`, plus the E1 acquisition manifest of each source document. The service
verifies the E1 manifest (including its bytes) and the parent lineage before
running any engine, stages and validates the output, atomically promotes content
to `extracted/<document_id>.md` (or `.tei.xml`), and then publishes the
deterministic extraction sidecar.

```bash
uv run scholar-pdf extract-run extraction-config.json \
  --audit-logger /path/to/workspace-manager/scripts/log_event.py
```

The requested engine is run first and the first engine that yields usable text
wins. When the requested engine is unavailable and the request permits a
fallback, the **only** fallback target is `PYMUPDF`
(`DEFAULT_ENGINE_FALLBACK_ORDER`), so a `DOCLING` request degrades to
`PYMUPDF`; `GROBID` is never substituted automatically because it is an
external provider that must be addressed explicitly. Every attempted engine,
its version, output format, and any fallback reason is recorded in the sidecar,
so `effective != requested` is never silent. A missing optional engine is
reported as an engine failure with a reason, never as a successful empty
result. Engines are optional extras (`extract`); importing `scholar_pdf` does
not import them.

The sidecar at `literature/extraction/<extraction_run_id>/<extraction_id>.json`
records the acquisition parent, screening parent, engine provenance,
per-engine attempts, frontmatter checksum, content SHA-256, and the
`extraction_status` for each item: `EXTRACTED`, `REUSED`, `PARTIAL`,
`NO_TEXT_LAYER`, `EXTRACTION_FAILED`, or `CANCELLED`. The Contract v1
`content_status` is a fixed projection of that status (`VALID`/`PARTIAL`/
`FAILED`/`NEEDS_OCR`), never chosen independently. Only
`literature/extraction/…/EXT-*.json` manifests are authoritative; a failed or
cancelled run still publishes a sidecar (with no committed output) so the
outcome is never silently lost.

Replaying the same semantic request is idempotent and returns `REUSED` without
re-running engines. One exception is a repair: if a document that previously
committed a determined failure (`EXTRACTION_FAILED`, `NO_TEXT_LAYER`) is re-run in
a different engine environment, the document already holding bytes is carried
unchanged, the failed sibling is re-driven, and a recovered document keeps the
same idempotency key under a new `EXT-` id, with the superseded failure row
retained in the sidecar. A rerun that recovers nothing republishes nothing. A
different request in the same run, stale parent lineage, changed bound bytes, or
path traversal fails closed with a typed error. Usable text is defined by a
versioned `usability-profile` (minimum character count and legacy-stub detection)
applied to the frontmatter-separated body, so structural templates are not
counted as text.

The sidecar may also carry a **non-authoritative** Contract v1 document-manifest
candidate. It is emitted only when a usable text file was committed, and it
always carries `contract_acceptance = "not_performed_by_kit"`: the kit does not
validate or accept Contract v1 artifacts. Every candidate `DocumentRecord`
carries a non-null `extraction_method` (the frozen model requires it on all
records; only `extracted_path` is conditional), and a `FAILED`/`NEEDS_OCR`
record omits `extracted_path` rather than inventing one. A run that commits no
bytes emits a failure sidecar and no candidate.

The programmatic entry point is
`PDFExtractionService.extract(requests, ...)`. Use `EngineRegistry` with the
shipped `FakeEngine` (or your own adapters) and an injected audit sink for
hermetic, offline tests. The legacy `extract` command (raw PDF → Markdown) is
retained for convenience but is **not** a Contract v1 path and produces no
manifest; use `extract-run` for workspace artifacts.

### Section-Aware Markdown Extraction
Convert PDFs into structured Markdown with YAML frontmatter for downstream RAG indexing:
```bash
uv run scholar-pdf extract papers/pdfs/ --output papers/extracted/ --engine docling
```

This legacy command is non-authoritative (see the note above); prefer
`extract-run` for Contract v1 workspaces.

### CLI Arguments Reference
- `acquire`: Execute a parent-bound Contract v1 acquisition batch and emit a deterministic manifest.
- `extract-run`: Execute a parent-bound Contract v1 extraction batch and emit deterministic extraction sidecars (authoritative).
- `download`: Production open-access retrieval by DOI (above). Files are validated and published under content-addressed `DOC-*` names, each with its manifest row.
- `ingest`: Validate and publish a local PDF under a content-addressed name, with its manifest row.
- `extract`: Legacy Markdown conversion. Not a Contract v1 path; emits no manifest.

For downloads, `access_status` comes from the location that gave the bytes
(`VERIFIED_OPEN_ACCESS`; `INSTITUTIONAL_ACCESS` for the parked gateway a library
caller can still pass; `USER_PROVIDED` for `ingest`); `was_oa` remains only as a
deprecated compatibility field. A successful HTTP response alone does not
establish that a source is open access.

## Documentation

Comprehensive documentation is available in the `docs/` directory:
- [Tutorial](docs/tutorial.md): A step-by-step guide to executing bulk downloads.
- [API Reference](docs/api_reference.md): Technical documentation for programmatic usage.

## License
This project is licensed under the MIT License.
