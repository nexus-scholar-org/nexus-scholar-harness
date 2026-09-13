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

# 3. Extract Section-Aware Markdown (CLI engines: docling | grobid only)
uv run scholar-pdf extract \
  workspaces/<project-slug>/pdfs/ \
  --output workspaces/<project-slug>/extracted/ \
  --engine docling
# NOTE: positional PDF file/dir path — there is NO --input flag and NO --engine pymupdf
#       (PyMuPDF is the API/MCP default; the CLI only offers docling/grobid).

# 4. Ingest an Existing PDF Manually
uv run scholar-pdf ingest my_paper.pdf --doi 10.1038/35057062 --smart-names

# 5. Download Through an Institutional Proxy (Cloudflare/WAF bypass)
#    attempt 3 automatically re-runs OA + direct-PDF candidates through the proxy
uv run scholar-pdf download \
  --input workspaces/<project-slug>/literature/included.json \
  --output workspaces/<project-slug>/pdfs/ \
  --proxy https://www.sndl1.arn.dz \
  --proxy-style subdomain      # auto | subdomain | ezproxy | prefix
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
