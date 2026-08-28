# Append-Only Audit Journal & Project Index Specification

Every project workspace in `workspaces/<project-slug>/` maintains an immutable, append-only event ledger and a human-readable artifact index to provide 100% scientific reproducibility and provenance tracking.

---

## 1. Directory Layout

```text
workspaces/<project-slug>/
├── INDEX.md                        # Master human-readable index of all files & status
├── project.json                    # Machine-readable project state & manifest
├── audit/
│   ├── journal.jsonl               # Immutable, append-only JSONL log of every event
│   └── verification_audit.json     # Detailed provider audit logs
├── literature/                     # Search, deduplication, screening datasets
├── pdfs/                           # Downloaded Open Access PDFs
├── extracted/                      # Markdown/XML extractions
├── synthesis/                      # Literature reviews, tables, synthesis notes
└── exports/                        # Spreadsheets, BibTeX, RIS exports
```

---

## 2. Event Ledger Schema (`audit/journal.jsonl`)

Each line in `journal.jsonl` is a valid JSON object adhering to this schema:

```json
{
  "timestamp": "2026-08-28T17:58:00.815701+00:00",
  "event_id": "EVT-20260828-001",
  "action": "DISCOVERY_SEARCH",
  "agent_or_tool": "scholar-search-kit",
  "description": "Federated literature search across OpenAlex, Semantic Scholar, Crossref, and arXiv across 5 query clusters.",
  "parameters": {
    "queries_count": 5,
    "year_min": 2017,
    "providers": ["openalex", "semanticscholar", "crossref", "arxiv"]
  },
  "inputs": [
    "workspaces/avarel-fuse-multispectral/literature/criteria.md"
  ],
  "outputs": [
    "workspaces/avarel-fuse-multispectral/literature/raw_search.json",
    "workspaces/avarel-fuse-multispectral/literature/deduped.json",
    "workspaces/avarel-fuse-multispectral/exports/search_summary.csv"
  ],
  "metrics": {
    "raw_hits": 284,
    "unique_papers": 251,
    "duplicate_rate": 0.116
  },
  "status": "SUCCESS"
}
```

---

## 3. Standard Action Enums

- `PROJECT_INITIALIZED`: Project workspace created with `project.json` and `criteria.md`.
- `DISCOVERY_SEARCH`: Raw queries executed across academic providers.
- `DEDUPLICATION`: Merging title/DOI clusters into canonical representatives.
- `VERIFICATION_HYDRATION`: Crossref/OpenAlex DOI resolution and abstract hydration.
- `SCREENING_TITLE_ABSTRACT`: AI/manual screening against `criteria.md`.
- `PDF_DISCOVERY_DOWNLOAD`: Fetching Open Access PDFs with magic byte validation.
- `FULLTEXT_EXTRACTION`: Parsing PDFs into Markdown via Docling / Grobid.
- `RAG_INDEXING`: Chunking and vector indexing into ChromaDB.
- `SYNTHESIS_GENERATION`: Generating literature reviews and synthesis matrices.

---

## 4. Master Index Format (`INDEX.md`)

`INDEX.md` is automatically refreshed whenever an event is logged:

```markdown
# Project Index: [Project Title]

- **Project ID**: `[project-slug]`
- **Last Updated**: `[ISO-8601 Timestamp]`
- **Status**: `Active`

## Quick Statistics
- **Discovered Papers**: 251
- **Verified Papers**: 239
- **Downloaded PDFs**: 0
- **Extracted Markdowns**: 0

## Project File Catalog

| Path | Description | Last Modified | Status |
| :--- | :--- | :--- | :--- |
| `project.json` | Project manifest and global research questions | 2026-08-28 | Active |
| `audit/journal.jsonl` | Append-only provenance event journal | 2026-08-28 | Synced |
| `literature/criteria.md` | PRISMA Inclusion / Exclusion screening rules | 2026-08-28 | Ready |
| `literature/verified.json` | Hydrated & verified bibliographic records | 2026-08-28 | 239 verified |
| `exports/verified_summary.csv` | Clean tabular bibliography export | 2026-08-28 | Ready |
```
