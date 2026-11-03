# scholar-pdf-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-pdf-kit`). Scope: `tools/scholar-pdf-kit/src/scholar_pdf/` (13,527 lines; `acquisition.py` 3,751, `extraction.py` 3,108, `extraction_models.py` 1,449, `acquisition_models.py` 1,083, `extraction_engines.py` 549, `cli.py` 616, `downloader.py` 503, `contract_candidate.py` 512, `contract_parents.py` 417, `frontmatter.py` 378, `canonical.py` 311, `publisher_patterns.py` 226, `extract.py` 157, `validator.py` 96, `models.py` 52, `config.py` 39) and `tools/scholar-pdf-kit/tests/` (7,275 lines), plus every `scholar_pdf` / `scholar-pdf` reference in `src/scholar_harness/`. Method: read the legacy stack (downloader, validator, extract, cli, publisher patterns, config) in full; read the E1/E2 services at their decision points (preflight, lineage, transport, staging, validation, promotion, locking, engine chain, usefulness evaluation, compose/verify); read the harness consumers (`pipeline/extraction.py`, `extraction_producer.py`, `console/runtimes/actions.py`, `console/api/pipelines.py`). Ran the kit suite (`uv run pytest tools/scholar-pdf-kit/tests -q`: 203 tests, 195 pass, 8 skipped, 0 fail; 7 skips are symlink tests that need a Windows privilege, 1 needs a built wheel). Reproduced defects offline with PyMuPDF-generated PDFs and stubbed HTTP. Scripts are in the session scratchpad (`r1_legacy.py` to `r4_misc.py`). No network, no installs, no file changes other than this one.

## 1. Verdict

The kit contains two unrelated systems. The newer one, the WP01-E1 acquisition and WP01-E2 extraction services (about 9.8k of the 13.5k source lines), is careful work: content-addressed storage, parent lineage checks, commit intents, checksums, typed per-item outcomes, and recorded engine fallbacks. **None of the harness pipeline calls it.** The harness runs the legacy path (`scholar-pdf download`, `scholar-pdf extract`, and `scholar_pdf.extract.PyMuPDFEngine`). That path loses the DOI-to-file link, uses file names the harness's own PDF lookup never matches, writes a success file when parsing fails, and scrambles two-column reading order. I reproduced the end-to-end failure: a correctly ingested PDF is not found by Stage 5, the study is "extracted" from its abstract alone, and the harness producer would then publish that abstract-only file as a `VALID` document. Within E2 itself, the Docling adapter can never run, and GROBID output is saved as a `.tei.xml` file that is not XML. Neither stack checks whether the retrieved PDF is the right paper. Neither measures extraction fidelity beyond a 200-character floor.

| Lens | Rating | Reason |
|---|---|---|
| Code quality & architecture | Weak | A careful E1/E2 core sits beside an unwired legacy stack, so most of the rigour never reaches a review. E2 depends on E1's private methods, and dead options are still documented. |
| Correctness & bugs | Failing | The download-to-extraction handoff the harness uses is broken end to end (reproduced). The extractor the harness uses fails silently and corrupts reading order (reproduced). The E2 Docling engine never runs (reproduced). |
| Research-method fitness | Weak | E1 records checksums and per-item non-retrieval statuses, but the harness never uses it. Nothing checks paper identity. Version, licence and retrieval date are not first-class fields. Extraction fidelity is assumed, not measured. |

## 2. Architecture and code quality

**PDF-01 — High — Two parallel stacks; the harness is wired only to the legacy one (Static).**
- Legacy stack: `downloader.py`, `extract.py`, `validator.py`, and the `download`, `ingest` and `extract` commands (`cli.py:300-612`).
- Contract stack: `acquisition.py`, `extraction.py`, `*_models.py`, `contract_*.py`, and the `acquire` and `extract-run` commands (`cli.py:153-243`).
- Harness usage:
  - Stage 5 imports `scholar_pdf.extract.PyMuPDFEngine` (`src/scholar_harness/pipeline/extraction.py:50,144,165`).
  - The console actions run `scholar-pdf download` and `scholar-pdf extract` (`console/runtimes/actions.py:84,91`; `console/api/pipelines.py:221-222,281-282,351-352`).
  - `extraction_producer.py:90-97` imports only helpers: `deterministic_document_id`, `extraction_method_for_engine`, and the frontmatter functions.
- No harness code builds an `AcquisitionRunConfig` or `ExtractionRunConfig`, or calls `PDFAcquisitionService` or `PDFExtractionService`. A grep of `src/scholar_harness` for these names returns nothing.
- Impact: E1/E2 guarantee checksummed sources, INCLUDE-only lineage (`acquisition.py:1049-1190`), per-item failure statuses and recorded engine fallbacks. None of these guarantees applies to a review run through the harness today.

**PDF-02 — Medium — E2 is built on E1's private methods (Static).**
- `PDFExtractionService` calls `self._acquisition._safe_workspace_path`, `_new_temporary`, `_cleanup_temporary`, `_hash_file`, `_acquire_lock_file`, `_relative_path` and `_promote` (`extraction.py:2937-3006`).
- Any refactor of E1 internals silently changes E2's file-system safety behaviour. These helpers should be a shared, public module.
- The two files are monoliths (3,751 and 3,108 lines), and each method mixes policy with I/O. Reviewing replay, orphan recovery and commit-intent paths is expensive. I only skimmed those paths (see §7).

**PDF-03 — Medium — Publication needs hard links and has no fallback (Static).**
- Every promotion uses `os.link`: `downloader.py:163`, `acquisition.py:2245,2973,3566`, `extraction.py:2796`.
- On a file system without hard links (FAT or exFAT external drives, some SMB or NAS shares), every promotion raises `OSError`. That becomes `FAILED` / `ATOMIC_COMMIT_FAILED` for every document.
- Portable workspaces are a stated Phase 7 goal. No `os.replace` or `O_EXCL` copy fallback exists, and no test covers this case.

**PDF-04 — Low — Window between creating and locking the lock file (Static, POSIX only).**
- `_acquire_lock_file` creates the lock with `O_EXCL` and only then takes the OS lock (`acquisition.py:3470-3496`).
- `_reclaim_stale_lock` (`acquisition.py:3435-3454`) treats any lockable file as abandoned and unlinks it.
- If a reclaimer runs between the creator's `os.open` and its `_lock_descriptor`, it unlinks a live lock. The creator then flocks an unlinked inode, and a third process can create and own a fresh lock at the same path.
- The comment at `acquisition.py:3491-3493` assumes the window does not exist. On Windows, the unlink of an open file usually fails, which narrows the window. Not reproduced.

**PDF-05 — Low — Dead code and no-op options (Static).**
- `AsyncPDFDownloader._safe_filename` (`downloader.py:91-109`) is never called. `--smart-names` (`cli.py:320-322,479-481`) is accepted and ignored: files are always `DOC-<sha256[:32]>.pdf` (`downloader.py:114`).
- `models.py` (`OALocation` and `OAResult`) is imported by no module.
- `download_pdf` publishes to a staging path that `process_doi` immediately re-promotes, a three-hop publish (`downloader.py:384-395`).
- `PDFExtractionService.extract` is `async` but runs engines synchronously (`extraction.py:1413`). A GROBID call (120 s timeout, `extraction_engines.py:330`) blocks the event loop. The `asyncio.CancelledError` branch in `_extract_one_document` (`extraction.py:1636-1641`) can only be reached through fault injection.

**PDF-06 — Low — The legacy downloader retries definitive 4xx responses (Static).**
- `raise_for_status()` (`downloader.py:225`) raises `aiohttp.ClientResponseError`, a `ClientError`, which the tenacity policy retries 3 times with 2–10 s backoff (`downloader.py:184-188`).
- A 404 costs about 6 s per candidate URL, and up to 4 candidates per DOI.
- E1 handles this correctly: it classifies 404 and 410 as `NOT_FOUND` without retrying (`acquisition.py:1920-1921`).

Strength worth keeping: the E1/E2 design checks parent lineage before any I/O, uses content-addressed identity, writes commit intents before promotion, and refuses unknown engine tokens instead of substituting one (`extraction_engines.py:485-503`). This is the right architecture for auditable retrieval. The problem is that it is not used.

## 3. Correctness and bugs

**PDF-07 — Critical — Reproduced — PDFs the kit downloads are never found by the harness extraction stage, so included studies are "extracted" from their abstract.**
- Code paths:
  - The kit publishes every acquired file as `DOC-<sha256[:32]>.pdf` (`downloader.py:111-114,395`).
  - Harness `_study_pdf` looks only for `<workspace_id|study_id>.pdf`, `<doi_slug>.pdf`, or a file whose stem starts with the DOI slug (`pipeline/extraction.py:79-95`).
  - With no match, Stage 5 writes a metadata-only file containing `## Abstract` and `extraction_engine: "metadata"` (`pipeline/extraction.py:171-189`), and the stage still reports `DONE`.
- `scholar-pdf download` persists no DOI-to-file mapping. The table is printed to the console (`cli.py:428-458`), and the only record is the optional `--export json` (`cli.py:463-465`), which the harness never passes (`actions.py:84`; `pipelines.py:223`).
- Evidence (`r3_integration.py`, stub HTTP):
  ```
  ingest: True ACQUIRED -> DOC-f3a76d1ac0c225e9617a4286f6e1111f.pdf
  metadata_frontmatter_only: ['SCI-000001.md']
  extraction_engine: "metadata"   ## Abstract  Abstract only.
  ```
- Compounding effect (harness side, kit API): `extraction_producer.py:966-1029` marks a file `VALID` when `measure_extracted_body` counts at least 200 characters and the file is not the legacy stub. A typical abstract passes. A 343-character abstract measured 343, not a stub. `extraction_method_for_engine("metadata")` returns `HEURISTIC`.
- Impact: the accepted `document_manifest` can declare abstract-only "full text" as `VALID`. Data extraction and risk-of-bias work downstream would then run on abstracts while the record claims full text.

**PDF-08 — High — Reproduced — The legacy extractor writes a success file when parsing fails.**
- `PyMuPDFEngine.extract_markdown` catches every exception, appends `Extracted content from <name>`, writes the `.md` file and returns its path normally (`extract.py:238-291`).
- Stage 5 counts that path as an extracted document (`pipeline/extraction.py:163-167`). It does not go into `metadata_frontmatter_only`.
- The kit's own test feeds a 25-byte fake PDF and asserts success (`tests/test_extract.py:7-27`), which locks the defect in.
- Evidence: `[a] returned: corrupt.md | body tail: 'Extracted content from corrupt.pdf'`.
- The harness producer later refuses the stub (`extraction_producer.py:967`). But Stage 5 already reported the document as extracted, and any reader of `extracted/` that bypasses the producer sees a stub.

**PDF-09 — High — Reproduced — The legacy extractor (the one the harness uses) scrambles two-column papers and invents headings.**
- `sorted(blocks, key=lambda b: (b[1], b[0]))` (`extract.py:246`) orders blocks by vertical position across the whole page. In a two-column layout this interleaves the columns paragraph by paragraph, even when the PDF's content stream is already in correct column order.
- Evidence (`r2_columns.py`, a PDF whose content stream is column-major):
  ```
  legacy (harness Stage 5): ['LEFT1','RIGHT1','LEFT2','RIGHT2','LEFT3','RIGHT3']
  E2 PyMuPDFTextEngine     : ['LEFT1','LEFT2','LEFT3','RIGHT1','RIGHT2','RIGHT3']
  ```
- The heading regex (`extract.py:256-275`) promotes any block under 80 characters that starts with a digit and a space, or with a section word, to a `##` heading.
- Evidence: `'## 2 participants withdrew before follow-up.'` and `'## Results were not reported for the control arm.'`.
- Most journal articles in a review are two-column. Sentences stitched across columns and spurious headings feed straight into LLM data extraction and RAG chunking.

**PDF-10 — High — Reproduced — The E2 Docling engine can never succeed.**
- `DoclingTextEngine.extract` passes raw `bytes` to `DocumentConverter.convert` (`extraction_engines.py:303-304`).
- Docling 2.141 declares `convert(source: Path | str | DocumentStream | HttpSource)` under `validate_call(strict=True)`, so every call fails validation before conversion starts.
- Evidence: `ENGINE_ERROR DOCLING_CONVERSION_FAILED | ... 4 validation errors for DocumentConverter.convert`.
- Every `docling` request therefore falls back to PyMuPDF and is committed as `PARTIAL` (`ENGINE_SUBSTITUTED`, `extraction.py:2019-2020`). With `allow_fallback=false` it fails outright.
- No test exercises the real Docling or GROBID adapters. Engine tests use `FakeEngine`; the one real-engine test is PyMuPDF on a 1-page fixture (`tests/test_extraction_contract.py:650-681`).
- Separately, `page_range` is recorded in Docling's `request_shape` but never applied (`extraction_engines.py:314-320`).

**PDF-11 — High — URL construction reproduced; wrong-paper outcome not reproduced (needs live access) — The IEEE direct-PDF pattern builds an arnumber from the DOI suffix.**
- `resolve_doi_to_publisher_pdf` takes the last dot-separated token of an IEEE DOI as the `arnumber` (`publisher_patterns.py:73-83`).
- Evidence:
  ```
  10.1109/CVPR.2016.90       -> ...getPDF.jsp?tp=&arnumber=90
  10.1109/TPAMI.2016.2577031 -> ...arnumber=2577031
  ```
- For modern IEEE DOIs the suffix is not the Xplore arnumber; for example, CVPR 2016 paper 90 has arnumber 7780459. The URL therefore addresses a different, arbitrary document.
- `process_doi` adds this candidate after the OA URL and through the institutional gateway (`downloader.py:363-380`). Whatever validates as a PDF is saved under the requested DOI, keeps `access_status=VERIFIED_OPEN_ACCESS`, and gets no identity check (see PDF-22).
- Old IEEE DOIs such as `10.1109/5.771073` happen to match, which is probably why the heuristic looked correct.

**PDF-12 — Medium — Reproduced — Open-access classification ignores explicit closed evidence and does not record the URL that succeeded.**
- `_provider_access_status` returns `VERIFIED_OPEN_ACCESS` as soon as `primary_location` has a `pdf_url`. It checks this before the `is_oa` field (`downloader.py:296-301`).
  - Evidence: `{"open_access": {"is_oa": False, "oa_status": "closed"}, "primary_location": {"pdf_url": ...}}` gives `VERIFIED_OPEN_ACCESS`.
- The E1 request validator uses the same disjunction (`acquisition_models.py:290-312`). Any truthy location `pdf_url` counts as OA evidence even next to `is_oa: false`.
- `process_doi` tries the OA URL, then a publisher-pattern URL, then proxied variants (`downloader.py:361-380`). It returns success without recording which candidate produced the bytes (`downloader.py:396-404`). A paper obtained through the institutional gateway is therefore reported as verified OA.

**PDF-13 — Medium — Reproduced — E2 GROBID output is saved as a `.tei.xml` file that is not XML, and an empty TEI counts as usable.**
- `_commit_bytes` always calls `compose_extracted_file` (`extraction.py:2079`). That function prepends a YAML block and a `# title` heading (`frontmatter.py:277-281`), while the file is named `<DOC>.tei.xml` (`extraction.py:167-170,2252-2254`).
  - Evidence: `committed .tei.xml is not XML: syntax error: line 1, column 0 | first line: ---`.
- The 200-character usability rule runs on raw TEI markup (`extraction.py:1842`; `extraction_engines.py:397-403`). A header-only TEI with an empty `<body/>` measured 376 characters and would be committed as `EXTRACTED`/`VALID`.
- `page_count=text.count("<page ")` (`extraction_engines.py:401`) counts an element GROBID TEI does not emit, so page counts are 0 (Static).
- The two stacks expect different `grobid_url` values:
  - Legacy appends `/api/processFulltextDocument` (`extract.py:331`).
  - E2 posts to the URL exactly as given (`extraction_engines.py:372`).
  - The README's base URL (`http://localhost:8070`) therefore fails under E2.

**PDF-14 — Medium — Static — The E2 engine chain stops at any non-empty output, even below the usefulness threshold.**
- `_run_chain` returns as soon as `character_count > 0` (`extraction.py:1843-1858`). `_evaluate` then rejects anything under 200 characters as `EXTRACTION_FAILED` (`extraction.py:2012-2017`) without trying the next engine.
- The README states the opposite (§5). A requested engine that yields a 50-character fragment blocks a fallback that would have produced full text.

**PDF-15 — Medium — Reproduced — Legacy commands exit 0 on failure.**
- `ingest` prints the failure and returns normally (`cli.py:528-529`). Evidence: `exit_code= 0 / Failed to ingest PDF: Provided PDF path does not exist.`
- `download --input <missing file>` skips parsing because of `input_file.exists()` (`cli.py:354`) and exits 0 with "No DOIs provided" (`cli.py:378-380`). Evidence: `download missing --input exit_code= 0`.
- The console pipeline uses `on_fail: abort` (`pipelines.py:226`). A wrong `included.json` path is therefore recorded as success.

**PDF-16 — Low — Reproduced — The body digest round-trip is asymmetric, and the first H1 of engine output is dropped.**
- `measure_extracted_body` always strips one leading `# ` heading (`frontmatter.py:152-155`). `compose_extracted_file` writes that heading only when a title exists (`frontmatter.py:278-279`).
- A file with no title whose body starts with an H1 fails `verify_bound_frontmatter` right after it is composed. Evidence: `freshly composed, unmodified file fails verification: EXTRACTED_BODY_MUTATED`.
- `_run_chain` keeps `measured.body` (`extraction.py:1842,1849`), so an engine's own leading H1 is silently removed from the committed text.

**PDF-17 — Low — Reproduced — The 10 KB floor rejects genuine PDFs with a misleading message.**
- `MIN_PDF_SIZE_BYTES = 10 * 1024` (`validator.py:8,34`). A 6-page text-only PDF of 4,498 bytes was rejected: `ingest: False FAILED The provided file is not a valid PDF.`
- Short reports and posters with non-embedded fonts are real cases. The message should say the file is "below the size floor", not "invalid".

**PDF-18 — Low — Reproduced (year) / Static (exports) — Legacy metadata and export defects.**
- `str(oa_data.get("publication_year", ""))` produces `'None'` for a null year (`downloader.py:267,275`). Evidence: `{'title': 'T', 'author': '', 'year': 'None'}`. That value reaches `--export bibtex` as `year={None}` (`cli.py:285-288`).
- BibTeX export appends without de-duplication (`cli.py:291`).
- JSON export rewrites `download_summary.json` non-atomically (`cli.py:274-275`).
- The same `None` leak exists in the harness template: `year: {metadata['year']}` (`pipeline/extraction.py:181`) parses back as the string `'None'`.

**PDF-19 — Low — Static — Resource and contract gaps in the legacy extractor.**
- `fitz.open` is never closed (`extract.py:241`). On Windows this holds a file handle until garbage collection.
- `DoclingEngine` writes Markdown with no frontmatter at all (`extract.py:303-309`). It is the CLI default (`cli.py:543`), and the console "Extract fulltext" action uses that default (`actions.py:91`). The result is `extracted/DOC-<hash>.md` with nothing tying it to a study.
- `DoclingEngine` falls back to PyMuPDF without saying so (`extract.py:310-314`).

## 4. Research-method fitness

**Auditable retrieval (source, version, licence, checksum, date).**
- Legacy path (the one in use): nothing is persisted per study. The content hash survives only as the file name. The source URL, the candidate that succeeded, OA version and licence are all lost (`downloader.py:396-404`).
- E1 records `source_sha256`, `byte_length`, every attempt's HTTP status and media type, and a redacted `selected_source_url` (`acquisition.py:2276-2357`). Three gaps remain:
  - **PDF-20 — Medium — Reproduced.** `_redact_source` drops the whole query string (`acquisition.py:2397-2423`). `https://europepmc.org/articles/PMC1234567?pdf=render` becomes `.../PMC1234567`, and a DSpace `...paper.pdf?sequence=1&isAllowed=y` loses its selector. The recorded URL cannot reproduce the fetch, and URLs that differ only by query collapse into the same idempotency input (`acquisition.py:1263-1271`).
  - OA `version` (submitted, accepted or published) and `license` survive only if the caller copies them into the untyped `provider_evidence` (`_SAFE_PROVIDER_KEYS`, `acquisition.py:72-87`). The record has no typed preprint-versus-VoR field. The legacy downloader prefers `best_oa_location` (`downloader.py:320`), which is often a repository preprint, and records nothing about it.
  - `AcquisitionAttempt.attempted_at` exists (`acquisition_models.py:458`) but is never set anywhere in `acquisition.py`, so the date of retrieval is not recorded. E2 sets `attempted_at` (`extraction.py:1799`), so the gap is specific to E1.

**PRISMA "reports not retrieved".**
- **PDF-21 — Medium — Static.** E1 has the right material. Every requested study gets an `AcquisitionItemOutcome` with a status (`UNRESOLVED`, `NOT_FOUND`, `NETWORK_FAILED`, `INVALID_CONTENT`, `IDENTITY_MISMATCH`, `FAILED`) and a code, and the manifest requires at least one outcome (`acquisition_models.py:45-55,807`).
- The vocabulary is technical, not reportable:
  - A 401/403 (`SOURCE_ACCESS_RESTRICTED`) becomes generic `FAILED` (`acquisition.py:1915-1919,2502-2507`), indistinguishable at status level from an internal error.
  - Nothing aggregates "sought for retrieval / not retrieved, by reason" for the PRISMA 2020 flow diagram.
- On the legacy path, non-retrieval exists only as console output (`cli.py:439-456`). A run leaves no persistent record of which included studies lack full text, or why.

**Wrong-paper detection.**
- **PDF-22 — High — Static.** Neither stack inspects the retrieved bytes for identity.
  - E1 compares two caller-supplied DOI fields (`acquisition.py:1740-1750`) and checks that they appear in the corpus (`acquisition.py:1183-1190`).
  - `title_similarity` is supplied by the caller, never computed, and advisory only. A similarity of 0.0 still commits `ACQUIRED` with a `TITLE_SIMILARITY_REVIEW` warning (`acquisition.py:2425-2432`; it is attached in `_acquire_one`).
  - The legacy path has no check at all.
- Combined with PDF-11 (guessed IEEE URLs) and institutional-proxy candidates, a landing page, supplementary file or neighbouring article can be stored as the study's full text. A cheap first-page DOI or title match against the corpus record, with the result stored, would catch most of these.

**Extraction fidelity.**
- **PDF-23 — High — Static.** "Usable" means at least 200 whitespace-collapsed characters (`extraction_models.py:103`; `extraction.py:2012`). Nothing measures or flags tables, column order, references, equations or truncation:
  - E2 PyMuPDF emits plain `get_text("text")` per page, labelled `MARKDOWN` (`extraction_engines.py:207,226`), so tables come out as flattened text.
  - The legacy engine actively damages order (PDF-09).
  - The only real-PDF test asserts a marker string on a 1-page fixture (`tests/test_extraction_contract.py:659-679`).
- For a review that extracts numeric outcomes from tables, fidelity is assumed, not measured. A small labelled fixture set (two-column, table-heavy, scanned, with references) with per-engine checks is missing.

## 5. Doc drift

- `--smart-names` is documented as renaming to `Author_Year_Title` (`README.md:87,93`; `docs/naming-and-ingestion.md:13`). It is a no-op (PDF-05).
- `README.md:16` says validation rejects "encrypted" responses. The legacy validator treats encrypted PDFs as valid (`validator.py:73-77`), and structural validation is off by default (`config.py:23`). Only E1 rejects encryption (`acquisition.py:1988-1989`).
- `README.md:146-150` says "the first engine that yields usable text wins" and that DOCLING degrades to PYMUPDF "when the requested engine is unavailable". In fact the first engine with any text wins (PDF-14), and Docling always degrades because of PDF-10, even when it is installed.
- `README.md:84-88` presents `download --input literature/included.json` as SLR pipeline integration. The output cannot be consumed by the harness extraction stage (PDF-07).

## 6. Prioritized recommendations

Kit-source fixes belong in `nexus-scholar-org/scholar-pdf-kit` first, followed by a `plugins.json` `default_rev` bump and a re-vendor (repo rule). Harness-side items (marked H) belong in this repo.

| ID | Severity | Effort | Action |
|---|---|---|---|
| PDF-07 | Critical | M | Have `download` and `ingest` write a persistent per-run manifest (DOI and study to `DOC-*` path, sha256, source URL, status). (H) Have Stage 5 resolve PDFs through that manifest instead of guessing names. (H) Refuse `VALID` for `extraction_engine: metadata` files in `extraction_producer.py`. |
| PDF-01 | High | L | Decide on one stack. Either wire the harness to `acquire` / `extract-run` (build the run configs from accepted artifacts), or formally deprecate E1/E2. Do not keep both. |
| PDF-08 | High | S | Make `PyMuPDFEngine` raise on parse failure. Delete the stub path and fix `tests/test_extract.py` to expect failure. |
| PDF-09 | High | S | Stop the global `(y, x)` block sort; use PyMuPDF's native order or `sort=True` per column. Drop the digit and keyword heading heuristic, or require font-size evidence. Add a two-column regression test. |
| PDF-22 | High | M | Add a first-pages identity check (DOI string or normalized title match against the corpus record). Record the result in the attempt, and route mismatches to `IDENTITY_MISMATCH` or manual review. |
| PDF-11 | High | S | Remove the DOI-suffix-to-arnumber IEEE rule, or only use an arnumber taken from a resolved landing URL. |
| PDF-10 | High | S | Pass `DocumentStream(name=..., stream=BytesIO(data))` to Docling. Add one real-Docling test, marked optional. |
| PDF-23 | High | M | Create a small fidelity fixture set (two-column, tables, references, scanned) with per-engine assertions. Report table and column degradation as `PARTIAL` reasons. |
| PDF-13 | Medium | S | Store TEI as pure XML with the binding in the sidecar, or name it `.md`. Measure usability on TEI `<body>` text. Unify the `grobid_url` semantics. |
| PDF-12 | Medium | S | Treat explicit `is_oa: false` or `oa_status: closed` as overriding a `pdf_url`. Record which candidate (OA, publisher pattern, gateway) produced the bytes, and set the access status from that candidate. |
| PDF-20 | Medium | S | Keep non-secret query parameters, and redact only by key. Add typed `oa_version`, `license` and `retrieved_at` fields to `AcquiredDocumentRecord`. |
| PDF-21 | Medium | M | Map item statuses to PRISMA "not retrieved" reasons. Give 401/403 its own status (for example `ACCESS_RESTRICTED`). Emit sought and not-retrieved counts per run. |
| PDF-14 | Medium | S | Continue the engine chain when output is below the profile threshold, and record the reason `ENGINE_OUTPUT_UNUSABLE`. |
| PDF-15 | Medium | S | Make `ingest` exit non-zero on failure, and make `download --input` fail when the file is missing. |
| PDF-03 | Medium | M | Fall back to an `O_EXCL` copy plus fsync when `os.link` fails with `EPERM`/`ENOTSUP`. Test it on a non-hard-link file system. |
| PDF-02 | Medium | M | Extract the shared file-system safety primitives into a public module used by both services. |
| PDF-16 | Low | S | Strip the heading only when the frontmatter has a title. Do not strip from engine output in `_run_chain`. |
| PDF-04 | Low | S | Take the OS lock before publishing the lock path (lock a temp file, then link or rename it), or reclaim only files older than a grace period. |
| PDF-17/18/19/05/06 | Low | S | Lower the size floor or report it separately; fix the `'None'` year and the export bugs; close `fitz` documents; delete `_safe_filename`, `models.py` and `--smart-names`; stop retrying 4xx responses. |

## 7. Limits of this assessment

- No network calls were made. Unpaywall, OpenAlex, publisher and GROBID behaviour is inferred from code and stubs.
  - The wrong-article outcome of PDF-11 is not reproduced against IEEE. The arnumber mismatch rests on known IEEE numbering.
  - PDF-12's real-world frequency, meaning how often OpenAlex returns a `pdf_url` on a closed work, is not measured.
- Docling was exercised only up to its input validation (PDF-10). No full conversion was run, to avoid model downloads.
- I read the E1/E2 replay, orphan-recovery, supersession and sidecar-publication paths (`acquisition.py:1402-1556,2102-2210,3584-3740`; `extraction.py:973-1305,2757-2840`) only partially. Crash-consistency claims in those paths are neither confirmed nor refuted here. The suite's 195 passing tests cover many of them, all with `FakeEngine` or synthetic bytes.
- The lock race (PDF-04) and the hard-link portability failure (PDF-03) are static. This Windows host could not run the 7 symlink tests, which were skipped.
- Harness-side findings (parts of PDF-07 and PDF-18) are reported because they decide whether the kit's output is used correctly. They are not a full harness review.
