# Fulltext Extraction Reference (Legacy Raw-Path CLI)

> **Scope: non-authoritative convenience only.** `scholar-pdf extract` writes to an
> arbitrary output directory with no acquisition/extraction lineage, no bound
> frontmatter, and no sidecar manifest. It can never write the authoritative
> `extracted/<document_id>.md` contract path. The **authoritative** path is the
> parent-bound WP01-E2 `extract-run` CLI / `PDFExtractionService` API (see SKILL.md),
> whose engines (`PYMUPDF | DOCLING | GROBID`) run through a declared registry with
> recorded fallback chains — an unknown engine token is rejected, never silently
> substituted.

`scholar-pdf-kit` includes built-in fulltext extraction to convert raw PDFs into structured Markdown or TEI XML for downstream RAG and LLM consumption.

---

## 1. Extraction Engines

| Engine | CLI Flag (`extract`) | E2 Registry Token | Output Format | Best Used For |
| :--- | :--- | :--- | :--- | :--- |
| **PyMuPDF** | API/MCP only (no CLI flag) | `PYMUPDF` (deterministic rule-based) | Structured Markdown (`.md`) + YAML frontmatter | Fast local extraction with `metadata=` frontmatter injection. |
| **Docling** | `--engine docling` (CLI default) | `DOCLING` (model-backed) | Structured Markdown (`.md`) | Reading text, tables, headers directly into LLM prompts and vector chunkers. |
| **Grobid** | `--engine grobid` | `GROBID` (external provider, TEI output) | TEI XML (`.tei.xml`) | Deep bibliographic parsing, section labeling, and citation extraction. |

CLI `extract` accepts only `docling | grobid` (anything else exits `Unknown engine`);
PyMuPDF is reachable via the Python API (`scholar_pdf.extract.PyMuPDFEngine`) and the
MCP `nexus_extract_pdf` default. Docling falls back to PyMuPDF when conversion fails.

---

## 2. CLI Usage (positional path — there is NO `--input` flag)

```bash
# Extract Markdown from a single PDF using Docling
uv run scholar-pdf extract downloads/my_paper.pdf --output markdown/

# Extract all PDFs in a folder to Markdown
uv run scholar-pdf extract downloads/ --output markdown/ --engine docling

# Extract TEI XML using a local Grobid container
uv run scholar-pdf extract downloads/ --output tei/ --engine grobid --grobid-url http://localhost:8070
```

On parse failure the legacy emitter appends an `Extracted content from <name>` stub
marker line — a failure marker, never content. Always spot-check output for real body
text; the authoritative E2 path refuses such stubs explicitly.

---

## 3. Running Grobid via Docker

If using the Grobid engine, run the official container using the provided compose file:
```bash
docker compose -f docker-compose.grobid.yml up -d
```
Service runs on port `8070`.

---

## 4. Programmatic Usage in Python

```python
from pathlib import Path
from scholar_pdf.extract import DoclingEngine, GrobidEngine, PyMuPDFEngine

pdf_file = Path("downloads/sample.pdf")
output_dir = Path("markdown_output")

# 1. Extract Markdown with frontmatter metadata (preferred local path)
md_path = PyMuPDFEngine.extract_markdown(
    pdf_file, output_dir, metadata={"doi": "10.1371/journal.pbio.3000246"}
)

# 2. Extract Markdown with Docling (falls back to PyMuPDF on failure)
md_path = DoclingEngine.extract_markdown(pdf_file, output_dir, metadata={...})

# 3. Extract TEI XML with Grobid (no frontmatter metadata — TEI output)
tei_path = GrobidEngine.extract_markdown(pdf_file, output_dir, grobid_url="http://localhost:8070")
print(f"Generated TEI XML at: {tei_path}")
```
