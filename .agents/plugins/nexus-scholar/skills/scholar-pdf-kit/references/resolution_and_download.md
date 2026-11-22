# Open Access Resolution & Download Mechanics

This reference details how `scholar-pdf-kit` resolves DOIs to legal Open Access PDFs, manages concurrent downloading, validates file integrity, and avoids publisher paywalls.

---

## 1. Multi-Stage OA Resolution

The toolkit asks both services for every DOI and takes the best open copy
either lists (`process_doi` in `src/scholar_pdf/downloader.py`, ranking in
`src/scholar_pdf/open_copies.py`):

```mermaid
flowchart TD
    DOI["Input DOI"] --> OA["1. OpenAlex Works API\n(best_oa_location / primary_location / locations,\nopen and with a pdf_url)"]
    DOI --> UP["2. Unpaywall v2 API\n(best_oa_location / oa_locations\nwith a url_for_pdf)"]
    OA --> RANK["Rank across both lists:\npublished, accepted, submitted, unlabelled"]
    UP --> RANK
    RANK -- "An address is listed" --> DL["Download Pipeline\n(at most three addresses, in order)"]
    RANK -- "No direct PDF address" --> FAIL["UNRESOLVED: lookup failed,\nopen but no direct PDF,\nor no open copy listed"]
```

1. **OpenAlex**: Asked only with `SCHOLAR_OPENALEX_KEY` (Part K item 4), sent as its `api_key` parameter and never printed or written to the manifest; without the key OpenAlex is not asked (lookup state `NOT_ASKED`, stated by the result and the command) and only Unpaywall is. A 409 reads "the daily budget is spent". Queries `https://api.openalex.org/works/https://doi.org/{doi}` via the search-kit's httpx client, once. Every listed location is read (`best_oa_location`, `primary_location`, `locations`); one counts only if OpenAlex marks it open (`is_oa: true`) and it carries a direct `pdf_url`.
2. **Unpaywall**: Queries `https://api.unpaywall.org/v2/{doi}`, once, for every DOI (decision 2026-11-21, H-pdf-resolver-locations item 4, "Always ask both services"; OpenAlex only with its key), and reads `best_oa_location` and `oa_locations` for a `url_for_pdf`.
   - **Ranking** (`scholar_pdf.open_copies.open_copies`; M12a answer F3): across both lists, published version, then accepted manuscript, then submitted version or preprint, then a copy with no version label; within a version OpenAlex's locations before Unpaywall's, each in its provider's own order; an address listed by both is kept once. At most three addresses are tried, each a provider's own; a landing page is never requested and no address is built. The copy taken is on the result (`open_copy`: version, licence, host, source, provider).
   - **Why a DOI has no file** (`DownloadResult.outcome`, with its own message and `download` exit code): `LOOKUP_FAILED` (a service failed and the other listed no address, with the HTTP status or error kind; exit 3; a 404 is an answer, not a failure), `PDF_NOT_FETCHED` (a listed address gave no PDF; exit 1), `OPEN_NO_DIRECT_PDF` (open access, landing pages only; exit 4), `NO_OPEN_COPY_LISTED` (exit 5). A service that fails while the other lists a copy does not stop the download; the failure stays on the result (`lookups`).
   - **Closed evidence first** (Part K item 7, PDF-12): a service that says the work is closed (`is_oa: false`, or `oa_status: "closed"`) has none of its addresses listed, whatever `pdf_url` it gives.
3. **No guessed publisher URL** (decision 2026-11-21, M12a items 24 and 27, K0; removed in Part K, G3): the publisher direct-PDF patterns are deleted; a stale `ENABLE_PUBLISHER_DIRECT_PATTERNS=true` is refused by `download` and `ingest` (`PUBLISHER_PATTERNS_REFUSED`).
4. **No institutional proxy** (item 25): `--proxy` or `PROXY_URL` is refused by `download` and `ingest` (`PROXY_REFUSED`). The library's gateway rewrite is parked code, used only when a caller passes a gateway explicitly; it no longer reads `PROXY_URL`.
5. **Access Status**: a stored file takes the status of the location that gave its bytes (`source_url`, `route` on the result): `VERIFIED_OPEN_ACCESS` for a provider's open location, `INSTITUTIONAL_ACCESS` for the parked gateway (never open access), `USER_PROVIDED` for `ingest`. With no file, only explicit provider OA evidence yields `VERIFIED_OPEN_ACCESS`; anything else is `UNRESOLVED` — never a paywall determination, and HTTP success alone never counts as acquisition.

> Authoritative note: raw `download` is the discovery convenience. The **authoritative**
> acquisition path is the parent-bound WP01-E1 `acquire` CLI/API (see SKILL.md) —
> never cite a discovery download as a committed acquisition.

---

## 2. Download Pipeline & Resiliency

Downloads are executed asynchronously using `aiohttp` and `tenacity` (`AsyncPDFDownloader.download_pdf`):
- **Concurrency Limiting**: Managed via `asyncio.Semaphore(max_concurrent)` (default: 5) to prevent socket starvation and CDN IP blocking.
- **Staged, Validated Promotion**: Bytes stream to a per-candidate temp file; only candidates passing binary validation are atomically promoted to their content-addressed final path (`DOC-<32 hex>.pdf`). Staging files are always unlinked. There is no `Content-Type` header gate — paywall/error HTML is rejected by the signature check below.
- **Retries only for what can pass** (Part K item 6, PDF-06): a connection error, a timeout or a 5xx is retried (2 to 10 s backoff, 3 attempts); a 429 is retried after its own `Retry-After` when that is at most 60 s, otherwise it ends at once with "the host asks to try later"; 400, 401, 403, 404, 410 and 451 are asked once.
- **Every PDF request is kept** (`DownloadResult.attempts`, `request_count`, `request_hosts()`): the address, host, HTTP status or error, retry flag, final address, redirects, content type and checks. `download` prints per DOI how many PDF requests went to which host and what each answered, so a higher-ranked address that gave no PDF (PubMed Central's, in the live check after PR 278) is named with its answer when a lower-ranked copy is stored. Nothing poses as a browser to get past such an answer.
- **Portable writes** (PDF-03): where hard links fail (FAT or exFAT drives, some shares), the file is published by an exclusive-create copy with fsync; nothing is ever overwritten.
- **Transport Identity**: every request (the PDF over `aiohttp`, the OpenAlex and Unpaywall lookups over the search-kit's httpx client) names the app, `nexus-scholar/<version> (mailto:<address>)`; the address is `SCHOLAR_MAILTO` or the kit's `MAILTO`, required (K0).

---

## 3. Magic Byte Integrity Validation

Publisher CDNs occasionally return `200 OK` responses containing error HTML instead of binary PDFs. `scholar-pdf-kit` protects against corrupt files using binary signature inspection (`is_valid_pdf` in `src/scholar_pdf/validator.py`):

```python
MIN_PDF_SIZE_BYTES = 10 * 1024  # 10 KB floor: block-pages are typically smaller
_HEADER_SCAN = 1024             # versioned header may sit behind leading garbage
_TRAILER_SCAN = 8 * 1024        # %%EOF must appear in the final 8 KB

def is_valid_pdf(file_path: Path) -> bool:
    ...
    if file_path.stat().st_size < MIN_PDF_SIZE_BYTES:
        return False
    head = f.read(_HEADER_SCAN)
    if _HEADER_RE.search(head) is None:   # regex: rb"%PDF-\d+\.\d+"
        return False
    f.seek(max(0, size - _TRAILER_SCAN))
    return b"%%EOF" in f.read(_TRAILER_SCAN)
```

Each check is also named (`validator.pdf_checks`: `pdf_header`, `pdf_trailer`, `size_floor`, and `structure` with `--strict-validate`) and the failed one is said in words; a genuine PDF under 10 KB reads "below the 10 KB size floor", not invalid (PDF-17).

A real PDF must be at least 10 KB, carry a versioned `%PDF-<major>.<minor>` header within the first 1024 bytes, and end with a `%%EOF` trailer within the last 8 KB — deliberately stricter than a 5-byte prefix check, so `%PDF-`-prefixed HTML abuse fails the trailer test. Candidates failing validation are never promoted (staging unlinked). Optional `--strict-validate` adds a pypdf structural parse as a second, encryption-tolerant gate.

---

## 4. Identity and the manifest

- **Identity** (Part K item 9, PDF-22; `scholar_pdf.identity.check_identity`): with PyMuPDF (the `pdf` extra) the DOI and the title's words are looked for on the first two pages: "doi found", "title found", or "not found: check it"; without PyMuPDF, "not checked". It never blocks a file; check a "not found" file by hand.
- **Manifest** (Part K item 8, PDF-07; `scholar_pdf.manifest`): one JSON line per DOI asked, at `AsyncPDFDownloader(manifest_path=...)`, `download --manifest PATH`, or `download-manifest.jsonl` in `--output`. It holds the DOI, the study id (from the input record), the outcome, the file, its size and SHA-256, the address asked, the final address and redirects, the HTTP status, content type, version, licence, host type, provider, route, access status, each check by name, the lookups in short, every PDF request, the time and the app version. No file is kept without its row (`MANIFEST_NOT_WRITTEN`). The legacy `literature/pdf_manifest.json` is not written.
