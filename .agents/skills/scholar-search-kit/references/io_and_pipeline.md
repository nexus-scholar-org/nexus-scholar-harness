# Ingestion, Export, and Pipeline Integration Reference

This guide details supported file formats, importers, exporters, and downstream pipeline handoffs (e.g. to `scholar-pdf-kit` and `scholar-rag-kit`).

---

## 1. Supported File Formats

| Format | Importer Class | Exporter Method | Notes |
| :--- | :--- | :--- | :--- |
| **JSON** | `JSONImporter` | `Exporter.json(...)` | Standard JSON array of serialized `Document` objects. Primary format for downstream handoffs. |
| **JSONL** | `JSONLImporter` | `Exporter.jsonl(...)` | Line-delimited JSON. Best for streaming and large collections. |
| **RIS** | `RISImporter` | `Exporter.ris(...)` | Standard citation export format from Zotero, Mendeley, EndNote, Google Scholar. |
| **CSV** | — | `Exporter.csv(...)` | Tabular export containing `workspace_id`, `title`, `year`, `provider`, `doi`, `arxiv_id`, `pubmed_id`, `openalex_id`, `venue`, `citations_count`. |

---

## 2. CLI Format Conversion & Import

```bash
# Convert RIS library to standardized JSON
uv run scholar-search export my_library.ris papers.json --format json

# Convert JSON to CSV for spreadsheet review
uv run scholar-search export papers.json papers.csv --format csv

# Import RIS directly with verification & enrichment
uv run scholar-search import zotero_export.ris --verify --enrich --output verified.json
```

---

## 3. Downstream Pipeline Integration with `scholar-pdf-kit`

`scholar-search-kit` and `scholar-pdf-kit` form a sequential discovery-to-download pipeline:

```bash
# Step 1: Discover & deduplicate literature with scholar-search-kit
uv run scholar-search search "retrieval augmented generation" --limit 20 --output literature.json

# Step 2: Bulk download Open Access PDFs using scholar-pdf-kit
# (hand literature/included.json to the downloader — see the scholar-pdf-kit skill for exact flags)
uv run scholar-pdf download --input literature/included.json --output downloaded_pdfs/
```

### Programmatic Python Pipeline Handoff

```python
from pathlib import Path
from scholar_search import Exporter
from scholar_search.models import Document   # Document lives in scholar_search.models, NOT the package root

def save_for_pdf_kit(documents: list[Document], destination: Path) -> Path:
    """Exports Document instances to clean JSON consumable by AsyncPDFDownloader."""
    exporter = Exporter()
    return exporter.json(documents, destination)
```
