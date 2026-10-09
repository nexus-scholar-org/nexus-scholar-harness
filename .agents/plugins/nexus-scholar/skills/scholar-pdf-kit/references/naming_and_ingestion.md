# Naming, Ingestion, and Export Reference

This guide covers output naming, manual ingestion of local PDF files, and bibliographic metadata export.

---

## 1. File Naming

### Content-addressed output (pinned behavior)

Discovery `download` and manual `ingest` promote validated bytes to
identity-addressed paths of the form `DOC-<32 hex>.pdf` (content hash via
`_content_path`/`_promote_candidate` in
`tools/scholar-pdf-kit/src/scholar_pdf/downloader.py`) — never from a title,
filename, or HTTP success. A concurrent writer publishing different bytes to the
same identity path fails rather than overwrites.

### `--smart-names` (retained flag, no renaming effect)

The CLI still accepts `--smart-names`, and the downloader keeps the
`_safe_filename` helper (`{year}_{author}_{title}.pdf`, title truncated to 50
alphanumeric characters) — but the helper is never called on the pinned path, so
the flag does not change the final filename. Treat smart-naming as a deferred
toolkit defect (D1), not as behavior to rely on.

### Legacy DOI naming

Pre-content-addressing, files were named by replacing invalid filesystem
characters in the DOI with underscores:
- DOI: `10.1038/s41586-020-2649-2` $\rightarrow$ `10.1038_s41586-020-2649-2.pdf`

Do not assume this layout for current outputs — resolve `file_path` from the
result record or `--export json` instead.

---

## 2. Manual Ingestion (`scholar-pdf ingest`)

When a PDF has been acquired manually (e.g. author copy or institutional archive), it can be ingested into the managed library:
```bash
uv run scholar-pdf ingest path/to/manual_paper.pdf --doi 10.1038/35057062 --export json
```
### Ingestion Workflow
1. Queries OpenAlex/Unpaywall to hydrate metadata for the provided DOI.
2. Validates PDF magic bytes plus trailer/size floor in staging (optional pypdf gate via `--strict-validate`).
3. Atomically promotes validated bytes to the content-addressed `DOC-<32 hex>.pdf` path without overwriting existing bytes.
4. Appends record to `download_summary.json` or `download_summary.bibtex`.

---

## 3. Metadata Export Formats

Using `--export <format>` outputs an aggregated summary of all successfully retrieved documents:

- **JSON (`--export json`)**:
  Appends to `downloads/download_summary.json`, skipping DOIs already recorded:
  ```json
  [
    {
      "doi": "10.1371/journal.pbio.3000246",
      "file_path": "downloads/DOC-9f2c4a1b3d5e6f708192a3b4c5d6e7f8.pdf",
      "metadata": {
        "title": "Point of View: How open science helps researchers succeed",
        "author": "McKiernan",
        "year": "2019"
      }
    }
  ]
  ```
- **BibTeX (`--export bibtex`)**:
  Appends formatted BibTeX entries to `downloads/download_summary.bibtex`.
