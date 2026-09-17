# Scholar PDF Kit — Comprehensive Deep-Dive Analysis

**Kit**: scholar-pdf-kit (v0.1.0)
**Location**: C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-pdf-kit
**Analysis Date**: 2026-09-14
**Analyst**: Automated Deep-Dive

---

## Executive Summary

Scholar PDF Kit is a well-structured, async-first toolkit for discovering, downloading, validating, and extracting content from Open Access academic PDFs. It resolves DOIs through a multi-source cascade (OpenAlex → Unpaywall → publisher direct patterns → institutional proxy), validates downloaded files via binary signature analysis, and converts PDFs to structured Markdown with YAML frontmatter for downstream RAG indexing.

**Overall Maturity**: Beta (v0.1.0) — functional core with several design gaps, integration rough edges, and technical debt.

**Key Strengths**:
- Robust 3-attempt download cascade with publisher-specific bypass patterns
- Strict binary validation (magic bytes + size floor + EOF trailer)
- Well-tested publisher pattern rewriting (IEEE, Elsevier, Springer, arXiv, MDPI)
- Clean async architecture with configurable concurrency

**Key Weaknesses**:
- PyMuPDF extraction silently swallows all errors (fallback to stub line)
- pyyaml is an undeclared transitive dependency
- models.py (OAResult/OALocation) is defined but never used in the actual download pipeline
- BibTeX export produces malformed entries (missing braces, no escaping)
- No retry/resilience for metadata fetching (OpenAlex/Unpaywall)
- CLI extract command does not support --engine pymupdf (API-only)

---

## 1. Functionalities

### 1.1 Core Capabilities

| Capability | Status | Implementation |
|:--|:--|:--|
| DOI ? PDF resolution (OpenAlex) | Working | downloader.py:125-133 |
| DOI ? PDF fallback (Unpaywall) | Working | downloader.py:135-143 |
| Publisher direct-PDF patterns | Working | publisher_patterns.py:62-100 |
| Institutional proxy rewriting | Working | publisher_patterns.py:199-226 |
| Async concurrent downloads | Working | downloader.py:242-248 |
| Binary PDF validation | Working | alidator.py:20-49 |
| Structural PDF validation (pypdf) | Working | alidator.py:52-79 |
| Smart filename generation | Working | downloader.py:56-70 |
| PDF ? Markdown extraction (PyMuPDF) | Partial | extract.py:16-92 (error swallowing) |
| PDF ? Markdown extraction (Docling) | Working | extract.py:95-112 |
| PDF ? TEI XML extraction (Grobid) | Working | extract.py:115-136 |
| Manual PDF ingestion | Working | downloader.py:250-287 |
| JSON/BibTeX metadata export | Partial | cli.py:33-80 (malformed BibTeX) |
| YAML frontmatter injection | Working | extract.py:30-43 |

### 1.2 CLI Commands ? Functions Mapping

| CLI Command | Function | File:Line |
|:--|:--|:--|
| scholar-pdf download | cli.download() | cli.py:82-185 |
| scholar-pdf ingest | cli.ingest() | cli.py:187-224 |
| scholar-pdf extract | cli.extract() | cli.py:226-276 |

**Download sub-flow**:
`
cli.download()
  ? AsyncPDFDownloader.process_doi()
    ? fetch_openalex_metadata()  [downloader.py:125]
    ? fetch_unpaywall_metadata() [downloader.py:135]  (fallback)
    ? download_pdf()             [downloader.py:78]
    ? resolve_doi_to_publisher_pdf()  [publisher_patterns.py:62]  (attempt 2)
    ? compute_direct_pdf_from_landing_url()  [publisher_patterns.py:103]  (attempt 2)
    ? rewrite_via_proxy()        [publisher_patterns.py:199]  (attempt 3)
    ? clean_invalid_pdf()        [validator.py:82]
`

### 1.3 Data Models and Schemas

**DownloadResult** (downloader.py:26-33):
`python
@dataclass
class DownloadResult:
    doi: str
    success: bool
    file_path: Path | None = None
    error_message: str | None = None
    was_oa: bool = False
    metadata: dict | None = None
`

**OAResult / OALocation** (models.py:4-50):
- Pydantic v2 models mirroring Unpaywall/OpenAlex schema
- **DEAD CODE**: Never imported or used by the actual download pipeline (downloader.py works with raw dicts)
- est_pdf_url property exists but is never called

**Settings** (config.py:6-36):
- Pydantic-settings based configuration
- Environment variables: MAILTO, DOWNLOAD_DIR, MAX_CONCURRENT_DOWNLOADS, DOWNLOAD_TIMEOUT, PROXY_URL, PROXY_STYLE, PDF_STRUCTURAL_VALIDATION, ENABLE_PUBLISHER_DIRECT_PATTERNS

### 1.4 Integration Points with Other Kits

| Integration | Direction | Mechanism | Status |
|:--|:--|:--|:--|
| scholar-search-kit | PDF ? Search | AcademicHttpClient for metadata fetching | Working (hard dep) |
| scholar-search-kit | Search ? PDF | included.json / 
esults.json input parsing | Working |
| scholar-rag-kit | PDF ? RAG | Markdown extraction ? vector indexing | Working (via frontmatter) |
| scholar-agent-kit (MCP) | Agent ? PDF | 
exus_extract_pdf tool | Working (metadata dropping fixed) |
| scholar-harness | Orchestrator ? PDF | PyMuPDFEngine import in orchestrator | Working |
| scholar-bib-kit | PDF ? Bib | BibTeX export | Broken (malformed output) |

### 1.5 Extraction Engines

| Engine | File | Output | Dependencies | Error Handling |
|:--|:--|:--|:--|:--|
| **PyMuPDFEngine** | extract.py:16-92 | .md with YAML frontmatter | itz (PyMuPDF) | **Swallows all exceptions** ? stub line |
| **DoclingEngine** | extract.py:95-112 | .md (structured) | docling (optional) | Falls back to PyMuPDF on failure |
| **GrobidEngine** | extract.py:115-136 | .tei.xml (TEI XML) | 
equests (sync) | Raises RuntimeError on HTTP failure |

**Publisher Direct-PDF Patterns** (publisher_patterns.py:28-59):
| Publisher | DOI Prefix | Direct PDF URL Template |
|:--|:--|:--|
| IEEE | 10.1109/ | ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={suffix} |
| Elsevier | 10.1016/ | sciencedirect.com/science/article/pii/{pii}/pdfft?... |
| MDPI | 10.3390/ | mdpi.com/{path}/pdf |
| Springer | 10.1007/ or 10.1140/ | link.springer.com/content/pdf/{doi}.pdf |
| arXiv | 10.48550/ | rxiv.org/pdf/{arxiv_id}.pdf |

---

## 2. Improvements

### 2.1 Code Quality Issues

#### Critical: PyMuPDF Error Swallowing
**File**: extract.py:85-87
`python
except Exception:
    # Fallback simple text reader
    md_lines.append(f"Extracted content from {pdf_path.name}")
`
This catches **all** exceptions (including KeyboardInterrupt via bare Exception) and produces a stub line instead of the actual content. The output file will contain valid YAML frontmatter but no content, making it appear successful. Downstream RAG indexing will silently index empty documents.

**Recommendation**: Log the exception, propagate a warning, and consider raising or returning a structured error.

#### Malformed BibTeX Export
**File**: cli.py:63-77
`python
bibtex = f"@article{{{key},\n  title={{{title}}},\n  author={{{author}}},\n  year={{{year}}},\n  doi={{{res.doi}}}\n}}\n"
`
Issues:
1. BibTeX values are not brace-wrapped properly (missing outer braces for title/author)
2. No escaping of special characters (&, %, #, _) in titles/authors
3. key generation ("{author}{year}") can produce duplicate keys for multi-author papers
4. No journal field included despite metadata being available

#### Dead Code: OAResult/OALocation Models
**File**: models.py:1-50
The Pydantic models OAResult and OALocation are defined and exported in __init__.py but never used by the download pipeline. The downloader works with raw dicts from API responses. This creates confusion about the canonical data shape.

#### Inconsistent User-Agent
**File**: downloader.py:81
`python
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."
`
The docs (
esolution-and-download.md:22) claim the UA is scholar-pdf-kit/0.1.0 (mailto:{mailto}) but the code uses a Chrome browser UA. This discrepancy violates polite crawling guidelines and could trigger bot detection.

#### Missing pyyaml Dependency
**File**: extract.py:26
yaml is imported inside PyMuPDFEngine.extract_markdown() but pyyaml is not declared in pyproject.toml dependencies. It works only because pyyaml is a transitive dependency of other packages.

### 2.2 Missing Features

1. **No --engine pymupdf in CLI**: The extract CLI only accepts docling or grobid (cli.py:230). PyMuPDF extraction is API/MCP only. This is documented but unintuitive.

2. **No incremental/retry download**: If a batch download partially fails, there is no --resume or --retry-failed flag. Users must re-run the entire batch.

3. **No download manifest**: Failed downloads are reported in the terminal table but not persisted to a file for later retry.

4. **No PDF page count/quality metrics**: No validation of whether the downloaded PDF is actually readable (e.g., scanned image-only PDFs vs. text PDFs).

5. **No rate limiting for Unpaywall**: OpenAlex is rate-limited via AcademicHttpClient, but Unpaywall requests have no explicit rate limiting.

6. **No proxy authentication**: The proxy system supports URL-based proxies but not SOCKS5 or authenticated proxies.

### 2.3 API Design Improvements

1. **DownloadResult should be a Pydantic model** (currently a dataclass) for consistency with OAResult and JSON serialization.

2. **extract_markdown() should return a structured result** (not just a Path) including metadata about what was extracted, page count, word count, etc.

3. **AsyncPDFDownloader constructor** should accept an optional http_client parameter instead of always creating one internally (for testability and shared client reuse).

4. **Publisher patterns should be extensible** — currently hardcoded in _PUBLISHER_PATTERNS. A plugin system or config-based pattern registry would improve maintainability.

### 2.4 Error Handling Gaps

1. **etch_openalex_metadata** (downloader.py:125-133): Silently returns None on any exception. No logging, no differentiation between 404 (DOI not found) and 500 (server error).

2. **etch_unpaywall_metadata** (downloader.py:135-143): Same silent failure pattern. Unpaywall has rate limits (10K requests/day for free tier) that are not managed.

3. **download_pdf** (downloader.py:78-123): Cleans up the file on exception but does not log the failure reason before re-raising.

4. **process_doi** (downloader.py:163-240): The outer try/except catches all exceptions and wraps them in DownloadResult, losing the traceback.

5. **GrobidEngine.extract_markdown** (extract.py:117-136): Uses synchronous 
equests in an otherwise async toolkit. No retry logic for Grobid server timeouts.

### 2.5 Documentation Needs

1. **
esolution-and-download.md:30-36**: Shows outdated 5-byte magic check (.read(5) == b"%PDF-") — the actual validator is much more sophisticated (1024-byte header scan + 8KB trailer scan + 10KB size floor).

2. **No changelog or version history** — impossible to track what changed between releases.

3. **No architecture diagram** in the kit's own docs (only in pipeline-integration.md as a high-level flow).

4. **Missing API docs for publishers_patterns.py** — the proxy rewriting system is complex but only documented in SKILL.md.

---

## 3. Problems

### 3.1 Known Bugs

#### Bug 1: CLI Extract Does Not Support PyMuPDF
**File**: cli.py:230
`python
engine: str = typer.Option("docling", help="Extraction engine: docling or grobid"),
`
The CLI default is docling but the help says "docling or grobid". If a user passes --engine pymupdf, it falls through to the else branch and exits with error. This is inconsistent with the MCP tool which defaults to pymupdf.

#### Bug 2: BibTeX Key Collisions
**File**: cli.py:72
`python
key = f"{author}{year}".replace(" ", "")
`
Multiple papers by the same first author in the same year produce identical BibTeX keys, causing silent overwrites.

#### Bug 3: Smart Filename Truncation Lossy
**File**: downloader.py:65
`python
safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (" ", "_")).replace(" ", "_")
`
Titles with special characters (e.g., "C++", "Node.js", "C#") lose meaningful content. Two different papers with titles that truncate to the same 50 chars will collide.

#### Bug 4: GrobidEngine Returns .tei.xml Not .md
**File**: extract.py:134-135
`python
out_xml = output_dir / f"{pdf_path.stem}.tei.xml"
out_xml.write_bytes(tei_xml)
return out_xml
`
The function is named extract_markdown but returns TEI XML. The CLI prints "Extracted {name} -> {out}" which is fine, but calling code expecting Markdown will get XML.

### 3.2 Edge Cases Not Handled

1. **DOIs with URL encoding**: 10.1007%2Fs11263-023-01798-x (percent-encoded slash) is not normalized before API queries.

2. **Retracted papers**: No check for retraction status before downloading. The kit will happily download retracted PDFs.

3. **Empty/metadata-only PDFs**: Downloaded PDFs that are valid but contain only a cover page or metadata page pass validation but have no useful content.

4. **Concurrent file writes**: If two processes download the same DOI simultaneously, the dest_path.exists() check (downloader.py:193) has a TOCTOU race condition.

5. **Very large PDFs**: No size limit on downloads. A malicious or broken endpoint could serve a multi-GB file.

6. **Non-DOI inputs**: The --input JSON parser (cli.py:106-116) only handles external_ids.doi and doi fields. Other identifier types (PMID, ArXiv ID) are ignored.

### 3.3 Limitations

1. **5 publishers covered**: IEEE, Elsevier, MDPI, Springer, arXiv. Missing: ACM, Wiley, Taylor & Francis, SAGE, ACS, APS, IOP, etc.

2. **Single-author metadata**: extract_metadata() (downloader.py:145-161) only extracts the first author's last name. Multi-author papers lose author information.

3. **No full-text search within PDFs**: Cannot search inside downloaded PDFs for specific content.

4. **Synchronous Grobid**: The Grobid engine uses blocking 
equests calls, breaking the async architecture.

### 3.4 Technical Debt

1. **models.py dead code**: The OAResult/OALocation models are exported but unused. Either integrate them into the pipeline or remove them.

2. **Duplicate MIN_PDF_SIZE_BYTES**: Defined in both alidator.py:8 and publisher_patterns.py:19 with the same value (10KB). The one in publisher_patterns.py is exported but the validator uses its own copy.

3. **Global mutable settings**: config.py:39 creates a module-level settings instance that is mutated by CLI commands (cli.py:98-99). This is not thread-safe and makes testing harder.

4. **No type stubs or py.typed marker**: The package does not declare type information for downstream consumers.

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

#### Bottleneck 1: Sequential Metadata Fetching
**File**: downloader.py:166-185
`python
data = await self.fetch_openalex_metadata(http_client, doi)
# ...
if not pdf_url:
    unpaywall_data = await self.fetch_unpaywall_metadata(http_client, doi)
`
Metadata fetching is sequential: OpenAlex is tried first, then Unpaywall as fallback. For DOIs where OpenAlex returns no PDF URL, this doubles the latency. Could be parallelized with syncio.gather().

#### Bottleneck 2: Synchronous File I/O in Download
**File**: downloader.py:102-104
`python
with open(dest_path, "wb") as f:
    async for chunk in response.content.iter_chunked(8192):
        f.write(chunk)
`
The file write is synchronous (open() + write()), blocking the event loop during disk I/O. Should use iofiles or loop.run_in_executor().

#### Bottleneck 3: Synchronous Grobid Requests
**File**: extract.py:128
`python
response = requests.post(url, files=files, timeout=300)
`
Blocking HTTP call in an async toolkit. Should use iohttp or httpx async client.

#### Bottleneck 4: Sequential Extraction
**File**: cli.py:258-274
`python
for pdf in pdfs:
    progress.update(task, description=f"Extracting {pdf.name}...")
    # ... extraction ...
`
PDF extraction is sequential in the CLI. For large batches, this is a significant bottleneck.

### 4.2 Memory Usage Issues

1. **Full PDF download into memory**: The iter_chunked(8192) approach is memory-efficient for streaming, but the 
esponse.content is not bounded — a 10GB PDF would stream fine but the dest_path write has no size limit.

2. **PyMuPDF document not explicitly closed**: extract.py:48 opens itz.open(str(pdf_path)) but never calls doc.close(). For batch extraction, this leaks file handles.

### 4.3 Algorithm Efficiency

1. **Smart filename collision**: The current approach (year_author_title.pdf) should include a DOI hash suffix to prevent collisions when titles truncate.

2. **Publisher pattern matching**: _PUBLISHER_PATTERNS is a list of dicts searched sequentially. For 5 publishers this is fine, but if extended, a dict keyed by DOI prefix would be O(1).

### 4.4 Caching Opportunities

1. **Metadata caching**: OpenAlex/Unpaywall responses for the same DOI are fetched fresh every time. A simple disk cache (JSON files keyed by DOI hash) would eliminate redundant API calls.

2. **Publisher pattern results**: 
esolve_doi_to_publisher_pdf() is pure and deterministic — results could be memoized.

3. **Extraction results**: If a .md file already exists for a PDF with the same mtime, extraction could be skipped (--force to override).

### 4.5 Parallelization Potential

1. **Batch extraction**: PyMuPDFEngine.extract_markdown() is stateless per PDF — perfect for syncio.gather() or concurrent.futures.ProcessPoolExecutor.

2. **Grobid batch processing**: Grobid supports batch mode natively — sending multiple PDFs in one request reduces HTTP overhead.

3. **Parallel metadata resolution**: For large batches, OpenAlex metadata for multiple DOIs could be fetched in parallel with rate limiting.

---

## 5. Scientific Correction

### 5.1 Accuracy of PDF Extraction

**PyMuPDFEngine** (extract.py:16-92):
- **Section detection** uses regex patterns (extract.py:63-67) that match common section headers (Introduction, Methods, etc.) but miss domain-specific sections (e.g., "Background", "Materials and Methods", "Appendix").
- **Block sorting** (extract.py:53) sorts by (y, x) coordinates, which works for single-column PDFs but may misorder content in multi-column layouts.
- **Table/Figure detection** (extract.py:77-81) only checks if the first line starts with "Table " or "Figure " — misses numbered figures (e.g., "Fig. 1", "Figure 2a").
- **Fallback stub** (extract.py:87): On parse failure, writes "Extracted content from {filename}" — this is a valid Markdown file with no content, indistinguishable from an empty PDF.

**DoclingEngine** (extract.py:95-112):
- Delegates entirely to Docling's DocumentConverter — accuracy depends on Docling's model quality.
- Falls back to PyMuPDF on failure, losing Docling-specific structure.

**GrobidEngine** (extract.py:115-136):
- Produces TEI XML, not Markdown — inconsistent with the other engines.
- No post-processing to convert TEI to Markdown for downstream consumption.

### 5.2 Metadata Preservation

**Frontmatter completeness** (extract.py:31-41):
- workspace_id, doi, 	itle, uthors, year are injected from the metadata dict.
- **Missing**: journal, olume, issue, pages, publisher, license, bstract.
- **Empty keys are dropped** (extract.py:41): If metadata is None or empty, only extraction_engine and extracted_at appear — no DOI, no title.

**Smart filename metadata** (downloader.py:56-70):
- Only first author's last name is used (downloader.py:154).
- Year defaults to "0000" if missing (downloader.py:61).
- Title truncated to 50 chars without word-boundary awareness.

### 5.3 Open Access Compliance

**Strengths**:
- Respects OA licensing by using OpenAlex/Unpaywall (legal OA sources).
- Does not scrape publisher websites directly (uses API-resolved URLs).
- Publisher direct-PDF patterns use official endpoints (e.g., IEEE stamp, Springer content PDF).

**Weaknesses**:
- **No license tracking**: The OALocation.license field is in the model but never extracted or stored.
- **No embargo detection**: Some OA papers have embargo periods — the kit does not check.
- **Proxy usage** (downloader.py:196-232): Using institutional proxies to bypass paywalls is legally???? — the kit should document this clearly.

### 5.4 Citation Extraction Correctness

The kit does **not** extract citations from PDFs. Citation extraction is delegated to:
- GrobidEngine (TEI XML contains parsed references)
- scholar-rag-kit (post-extraction chunking)

**Gap**: No validation that extracted references match the PDF's actual reference list.

### 5.5 Academic Content Integrity

1. **No OCR fallback**: Scanned PDFs (image-only) will extract as empty or garbled text via PyMuPDF. No detection or warning.

2. **No page-range extraction**: Cannot extract specific sections (e.g., "only pages 5-10") — always processes the entire document.

3. **No watermark/stamp detection**: Downloaded PDFs may contain institutional watermarks or stamps that are not stripped.

4. **No version detection**: Cannot distinguish between preprint and published versions of the same paper.

---

## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent/Skill Be Created?

**Recommendation: YES — a pdf-quality-agent (or extend scholar-pdf-kit skill)**

**Rationale**: The kit has a narrow, well-defined scope (PDF lifecycle management) with clear evaluation metrics and multiple agent-in-the-loop opportunities.

### 6.2 Evaluation Metrics

| Metric | Definition | Target |
|:--|:--|:--|
| **Download Success Rate** | success_count / total_dois | = 70% for OA literature |
| **PDF Validation Pass Rate** | alid_downloads / total_downloads | = 99% |
| **Extraction Completeness** | 
on_empty_md_files / total_extractions | = 95% |
| **Frontmatter Completeness** | ields_present / expected_fields | = 80% (7 fields) |
| **Section Detection Accuracy** | correctly_identified_sections / total_sections | = 85% |
| **Smart Name Uniqueness** | unique_filenames / total_files | 100% |
| **Metadata Accuracy** | correct_metadata_fields / total_fields | = 90% |
| **Publisher Pattern Coverage** | matched_dois / total_publisher_dois | = 60% |
| **Retry Efficiency** | successful_retries / total_retries | = 30% |
| **Extraction Time per Page** | 	otal_time / total_pages | = 2 seconds |

### 6.3 Critic Capabilities Needed

1. **PDF Validator Critic**: Verifies that downloaded PDFs are actually readable (not just valid magic bytes). Checks page count, text density, image-to-text ratio.

2. **Extraction Quality Critic**: Compares extracted Markdown against the original PDF for completeness. Flags stub extrations, missing sections, garbled text.

3. **Metadata Consistency Critic**: Cross-checks extracted metadata (title, authors, year) against OpenAlex/Unpaywall records for accuracy.

4. **Frontmatter Completeness Critic**: Validates that all expected YAML fields are present and non-empty before handoff to RAG.

5. **Publisher Pattern Critic**: Monitors download success rates per publisher and flags patterns that are failing (e.g., IEEE stamp URL changed).

### 6.4 Agent-in-the-Loop Opportunities

1. **Download Review Agent**: After batch download, an agent reviews the summary table, identifies failures, and decides whether to retry with different strategies (proxy, alternative sources).

2. **Extraction Validation Agent**: After extraction, an agent spot-checks a sample of extracted Markdown files for quality (non-empty, reasonable section structure, frontmatter present).

3. **Metadata Hydration Agent**: For DOIs where OpenAlex/Unpaywall metadata is incomplete, the agent can query Crossref or Semantic Scholar to fill gaps.

4. **Proxy Configuration Agent**: Automatically detects the best proxy configuration based on download failure patterns and institutional affiliation.

5. **Content Deduplication Agent**: After extraction, identifies duplicate or near-duplicate content across extracted files (useful for preprint+published pairs).

### 6.5 Automation Potential

| Task | Current State | Automation Opportunity |
|:--|:--|:--|
| Batch download with retry | Manual re-run | Auto-retry with exponential backoff + proxy escalation |
| Extraction quality check | Manual spot-check | Automated heuristic scoring (text density, section count) |
| Metadata enrichment | Single-source (OpenAlex) | Multi-source cascade with fallback |
| Publisher pattern updates | Hardcoded | Community-maintained pattern registry |
| PDF deduplication | None | Content-hash based dedup across batches |
| Extracted content validation | None | LLM-based quality scoring |

---

## 7. Priority-Ranked Improvement Suggestions

### P0 — Critical (Fix Immediately)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 1 | PyMuPDF error swallowing produces silent stubs | extract.py:85-87 | RAG indexes empty documents |
| 2 | pyyaml undeclared dependency | pyproject.toml | Breaks on clean install |
| 3 | Malformed BibTeX export | cli.py:63-77 | Unusable bibliography output |
| 4 | User-Agent mismatch (docs vs code) | downloader.py:81 | Polite crawling violation |

### P1 — High (Next Sprint)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 5 | Synchronous file writes blocking event loop | downloader.py:102-104 | Performance degradation under load |
| 6 | No metadata caching (redundant API calls) | downloader.py:125-143 | Slow batch processing, API quota waste |
| 7 | Smart filename collisions on truncation | downloader.py:65 | File overwrites in batch downloads |
| 8 | models.py dead code (OAResult/OALocation) | models.py:1-50 | Confusion, maintenance burden |
| 9 | Sequential metadata fetching | downloader.py:166-185 | 2x latency for non-OA papers |

### P2 — Medium (Backlog)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 10 | No --engine pymupdf in CLI | cli.py:230 | Inconsistent API/CLI surface |
| 11 | PyMuPDF document handle leak | extract.py:48 | File handle exhaustion in batch |
| 12 | GrobidEngine returns XML not Markdown | extract.py:134-135 | Inconsistent output format |
| 13 | Duplicate MIN_PDF_SIZE_BYTES | alidator.py:8, publisher_patterns.py:19 | Maintenance risk |
| 14 | Single-author metadata extraction | downloader.py:154 | Incomplete metadata |
| 15 | No download size limit | downloader.py:78 | Risk of downloading huge files |
| 16 | TOCTOU race in file existence check | downloader.py:193 | Potential file corruption |

### P3 — Low (Nice-to-Have)

| # | Issue | File:Line | Impact |
|:--|:--|:--|:--|
| 17 | Publisher pattern extensibility | publisher_patterns.py:28-59 | Limited publisher coverage |
| 18 | No page-range extraction | extract.py | Cannot extract specific sections |
| 19 | No OCR fallback for scanned PDFs | extract.py | Empty extraction for image PDFs |
| 20 | No --resume / --retry-failed | cli.py | Manual re-run required |
| 21 | No type stubs / py.typed | Package root | Poor IDE support |
| 22 | Sequential extraction in CLI | cli.py:258-274 | Slow for large batches |

---

## Appendix A: File Inventory

| File | Lines | Purpose |
|:--|:--|:--|
| src/scholar_pdf/__init__.py | 39 | Package exports |
| src/scholar_pdf/cli.py | 279 | Typer CLI (download/ingest/extract) |
| src/scholar_pdf/config.py | 39 | Pydantic-settings configuration |
| src/scholar_pdf/downloader.py | 287 | Async PDF downloader with cascade |
| src/scholar_pdf/extract.py | 136 | PyMuPDF/Docling/Grobid extraction |
| src/scholar_pdf/models.py | 50 | Pydantic OA models (unused) |
| src/scholar_pdf/publisher_patterns.py | 226 | Publisher direct-PDF + proxy rewrite |
| src/scholar_pdf/validator.py | 96 | Binary + structural PDF validation |
| 	ests/test_cli.py | 95 | CLI integration tests |
| 	ests/test_downloader.py | 224 | Downloader unit tests |
| 	ests/test_extract.py | 25 | Extraction tests (minimal) |
| 	ests/test_publisher_patterns.py | 160 | Publisher pattern tests |
| 	ests/test_validator.py | 128 | Validator tests (comprehensive) |

**Total source**: ~1,153 lines (src) + ~632 lines (tests) = ~1,785 lines

## Appendix B: Dependency Map

`
scholar-pdf-kit
+-- Core deps (pyproject.toml)
¦   +-- pydantic >= 2.0.0
¦   +-- pydantic-settings >= 2.0.0
¦   +-- aiohttp >= 3.9.0
¦   +-- typer >= 0.9.0
¦   +-- requests >= 2.31.0
¦   +-- rich >= 13.0.0
¦   +-- tenacity >= 8.0.0
¦   +-- pypdf >= 4.0.0
¦   +-- pymupdf >= 1.24.0
¦   +-- scholar-search-kit (editable)
+-- Optional deps [extract]
¦   +-- docling >= 2.5.0
¦   +-- requests
¦   +-- lxml
+-- Undeclared transitive deps
¦   +-- pyyaml (via docling/pymupdf)
¦   +-- fitz (PyMuPDF import name)
+-- External services
    +-- OpenAlex API (api.openalex.org)
    +-- Unpaywall API (api.unpaywall.org)
    +-- Grobid server (localhost:8070, optional)
`

## Appendix C: Test Coverage Assessment

| Module | Test File | Test Count | Coverage Assessment |
|:--|:--|:--|:--|
| cli.py | 	est_cli.py | 5 | **Low**: No extract/ingest tests, no export tests |
| downloader.py | 	est_downloader.py | 5 | **Medium**: Core flows covered, no edge cases |
| extract.py | 	est_extract.py | 1 | **Very Low**: Only frontmatter test, no content extraction |
| publisher_patterns.py | 	est_publisher_patterns.py | 12 | **Good**: All patterns + proxy rewriting covered |
| alidator.py | 	est_validator.py | 9 | **Good**: Comprehensive edge cases |
| config.py | — | 0 | **None**: No config tests |
| models.py | — | 0 | **None**: No model tests (dead code) |

**Overall**: ~32 tests, uneven coverage. Extraction engine testing is critically underrepresented.

---

*Analysis generated by automated deep-dive. All file:line references verified against source code.*
