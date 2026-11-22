# Naming, Ingestion, and Export Reference

This guide covers output naming, manual ingestion of local PDF files, and bibliographic metadata export.

---

## 1. File Naming

### Content-addressed output (pinned behavior)

Discovery `download` and manual `ingest` promote validated bytes to
identity-addressed paths of the form `DOC-<32 hex>.pdf` (content hash via
`_content_path`/`_promote_candidate` in
`src/scholar_pdf/downloader.py`) — never from a title,
filename, or HTTP success. A concurrent writer publishing different bytes to the
same identity path fails rather than overwrites.

### Which file is which paper: the manifest

`--smart-names` and `_safe_filename` were removed in Part K (PDF-05): they never
renamed anything. The mapping from a DOI (and the study id of its record) to its
`DOC-<32 hex>.pdf` file is the manifest row (`download-manifest.jsonl` in
`--output`, or `--manifest PATH`; see `resolution_and_download.md` §4).

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
uv run scholar-pdf ingest path/to/manual_paper.pdf --doi 10.1038/35057062 --study-id SCI-000002 --export json
```
`ingest` exits 1 when it stores nothing (a missing file, not a PDF, below the size floor, or a manifest row that cannot be written).
### Ingestion Workflow
1. Queries OpenAlex/Unpaywall to hydrate metadata for the provided DOI.
2. Validates PDF magic bytes plus trailer/size floor in staging (optional pypdf gate via `--strict-validate`).
3. Atomically promotes validated bytes to the content-addressed `DOC-<32 hex>.pdf` path without overwriting existing bytes (a copy where hard links fail).
4. Records the identity check and writes the manifest row (route `user_provided`, access status `USER_PROVIDED`).
5. With `--export`, adds the record to `download_summary.json` or `download_summary.bibtex`.

---

## 3. Metadata Export Formats

Using `--export <format>` outputs an aggregated summary of all successfully retrieved documents:

- **JSON (`--export json`)**:
  Adds to `downloads/download_summary.json`, skipping DOIs already recorded; the file is replaced atomically:
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
  Adds one entry per DOI to `downloads/download_summary.bibtex` (DOIs already in the file are skipped; a year the services do not give is left out, never `None`), replaced atomically.
