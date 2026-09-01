---
name: scholar-pdf-kit
description: Instructions for using the scholar-pdf-kit Python API and CLI to discover, download, validate, and extract Open Access PDFs with YAML frontmatter.
---

# `scholar-pdf-kit` Skill Instructions

You are an expert academic research agent equipped with `scholar-pdf-kit`. This toolkit automatically resolves DOIs to legal Open Access PDFs via a multi-source cascade (OpenAlex, Unpaywall, arXiv, bioRxiv), validates binary `%PDF-` magic-byte integrity, and extracts structured section Markdown with standard YAML frontmatter.

## Core Capabilities
1. **Multi-Endpoint Open Access Cascade**: Resolves legal OA full-text across OpenAlex, Unpaywall, bioRxiv/medRxiv, and arXiv direct links.
2. **Concurrent & Resilient Downloading**: Asynchronous retrieval with exponential backoff and paywall HTML redirect rejection.
3. **Strict Magic Byte Validation**: Verifies binary `%PDF-` signature and removes corrupted or redirected HTML paywall files.
4. **Smart Canonical Naming**: Formats filenames as `{year}_{author}_{title}.pdf` and exports structured metadata logs.
5. **Section-Aware Markdown Extraction**: Converts PDFs to Markdown via `PyMuPDFEngine` or `DoclingEngine` preserving headers, tables, and injecting YAML frontmatter (`workspace_id`, `doi`, `title`, `year`, `extraction_engine`).

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

# 3. Extract Section-Aware Markdown with YAML Frontmatter (PyMuPDF)
uv run scholar-pdf extract \
  --input workspaces/<project-slug>/pdfs/ \
  --output workspaces/<project-slug>/extracted/ \
  --engine pymupdf

# 4. Ingest an Existing PDF Manually
uv run scholar-pdf ingest my_paper.pdf --doi 10.1038/35057062 --smart-names
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

    # 1. Initialize Downloader
    downloader = AsyncPDFDownloader(
        output_dir=Path("workspaces/my-project/pdfs"),
        use_smart_names=True
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

## Agent Guidelines & Best Practices

- **Paywall Recognition**: Not all academic literature is Open Access. If resolution reports `was_oa=False`, clearly inform the user that no legal Open Access copy is available. Do not attempt to bypass commercial paywalls with web scrapers.
- **Frontmatter Preservation**: Always ensure extracted markdown contains YAML frontmatter (`workspace_id`, `doi`, `title`, `year`) before handing off to `scholar-rag-kit` for chunking and vector indexing.
