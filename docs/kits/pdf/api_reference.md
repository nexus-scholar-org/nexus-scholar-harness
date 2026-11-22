# Scholar PDF Kit: API Reference

> Status (2026-11-22, M12a Part K): the downloader (`AsyncPDFDownloader`, and the
> `download` and `ingest` commands) is **production** (decision 2026-11-21, M12a
> items 15, 21 and 27); reading PDFs (`extract`, `extract-run`) and E1 `acquire`
> are parked. The kit is `src/scholar_pdf/` in the one `nexus-scholar` package.

## `AsyncPDFDownloader`

Takes DOIs, asks OpenAlex (only with `SCHOLAR_OPENALEX_KEY`) and Unpaywall for the
open locations they list, and downloads the best open copy with a direct PDF
address (published version, then accepted manuscript, then submitted version or
preprint; at most three addresses per DOI). It needs a contact e-mail
(`SCHOLAR_MAILTO`, or the kit's `MAILTO`); without one it raises
`MailtoNotSetError` before any request. No guessed publisher address is built and
no proxy setting is read.

```python
import asyncio
from pathlib import Path

from scholar_pdf.downloader import AsyncPDFDownloader


async def download_papers():
    downloader = AsyncPDFDownloader(
        output_dir=Path("workspace/pdfs/fetched"),
        manifest_path=Path("workspace/charting/fetch_manifest.jsonl"),  # one row per DOI asked
    )
    results = await downloader.download_batch(["10.7717/peerj.4375"])
    for res in results:
        print(res.doi, res.outcome, res.file_path, res.identity, res.request_count)


asyncio.run(download_papers())
```

`process_doi(session, http_client, doi, *, title=None, study_id=None)` handles one
DOI with the caller's own `aiohttp.ClientSession` and lookup client; `title` is
looked for on the first pages and `study_id` is written to the manifest row.
`ingest_pdf(http_client, path, doi, *, study_id=None)` stores a PDF the researcher
already has.

- **Retries:** only a connection error, a timeout, a 5xx, or a 429 whose
  `Retry-After` is at most 60 s. 400, 401, 403, 404, 410 and 451 are asked once.
- **Storage:** `DOC-<sha256[:32]>.pdf` in `output_dir`, published by hard link, or
  by an exclusive-create copy where hard links fail; an existing file is never
  overwritten.
- **Manifest** (`scholar_pdf.manifest`, schema `scholar-pdf-download-manifest-v1`):
  one JSON line per DOI asked, written before the call returns; if it cannot be
  written, a file the call created is removed and the DOI fails
  (`MANIFEST_NOT_WRITTEN`). A row holds the DOI, study id, outcome, file (relative
  to the manifest's folder), size, SHA-256, the address asked, the final address,
  the redirects, the HTTP status, the content type, the version, licence, host
  type, source and provider of the copy, the route, the access status, each check
  by name (`pdf_header`, `pdf_trailer`, `size_floor`, `structure` when asked,
  `identity`), the lookups in short, every PDF request (address, host, retry,
  status or error), the request count and hosts, the time and the app version.
  It never holds the contact e-mail or the OpenAlex key.

## `DownloadResult`

```python
@dataclass
class DownloadResult:
    doi: str
    success: bool
    file_path: Path | None
    error_message: str | None          # the reason in words
    was_oa: bool                       # deprecated; use access_status
    metadata: dict | None              # title, author, year ("" when unknown)
    access_status: str | None          # VERIFIED_OPEN_ACCESS, INSTITUTIONAL_ACCESS (parked gateway),
                                       # USER_PROVIDED (ingest), RESTRICTED_CONFIRMED, UNRESOLVED
    status: str | None                 # ACQUIRED, UNRESOLVED, FAILED
    outcome: str | None                # ACQUIRED, PDF_NOT_FETCHED, LOOKUP_FAILED, OPEN_NO_DIRECT_PDF,
                                       # NO_OPEN_COPY_LISTED, MANIFEST_NOT_WRITTEN, NOT_STORED (ingest)
    open_copy: OpenCopy | None         # version, licence, host type, source, provider
    lookups: tuple[LookupOutcome, ...] # ANSWERED, NOT_FOUND, FAILED or NOT_ASKED per service
    copies_listed: int
    copies_tried: int
    attempts: tuple[FetchAttempt, ...] # each PDF request: url, host, retry, http_status,
                                       # final_url, redirects, content_type, error, checks
    source_url: str | None             # the address that gave the bytes
    route: str | None                  # open_location, institutional_gateway, user_provided
    identity: str | None               # "doi found", "title found", "not found: check it", "not checked"
    study_id: str | None
    size: int | None
    sha256: str | None
    checks: tuple[PdfCheck, ...]       # ingest's checks (a download's are on its attempts)
    new_file: bool                     # this call created the file
```

`request_count` and `request_hosts()` count the PDF requests; `request_lines()`
gives each one in words.

## Checks and identity

- `scholar_pdf.validator.pdf_checks(path, structural=False)` returns each check by
  name with its result; `check_failure(checks)` says which failed, in words (a
  genuine PDF below 10 KB is "below the 10 KB size floor", not invalid).
- `scholar_pdf.identity.check_identity(path, doi, title)` looks for the DOI and the
  title's words on the first two pages with PyMuPDF (the `pdf` extra); without it,
  "not checked". It never blocks a file.

`OAResult` and `OALocation` (`scholar_pdf.models`) were removed in Part K: nothing
used them.
