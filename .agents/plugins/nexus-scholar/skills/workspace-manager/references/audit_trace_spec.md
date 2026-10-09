# Append-Only Audit Journal & Project Index Specification

Every project workspace in `workspaces/<project-slug>/` maintains an immutable, append-only event ledger and a human-readable artifact index to provide 100% scientific reproducibility and provenance tracking.

---

## 1. Directory Layout

Canonical lifecycle layout (`init_project.py` scaffolds `audit/`, `literature/`,
`pdfs/`, `extracted/`, `synthesis/`, `exports/` plus `project.json`,
`synthesis/literature_review.md`, `audit/journal.jsonl`, and `INDEX.md`; the
rest appears via later pipeline stages):

```text
workspaces/<project-slug>/
├── INDEX.md                        # Master human-readable index of all files & status
├── intent.json                     # Socratic LLM intent packet (methodology-copilot)
├── protocol.json                   # Canonical deterministic research protocol contract
├── SCREENING_CRITERIA.md           # Rendered inclusion/exclusion criteria document
├── project.json                    # Machine-readable project state & manifest
├── audit/
│   ├── journal.jsonl               # Immutable, append-only JSONL log of every event
│   └── recon_context.json          # GENESIS provenance sidecar (grounded inception only)
├── literature/                     # Search, deduplication, screening datasets
├── pdfs/                           # Downloaded Open Access PDFs
├── extracted/                      # Markdown with YAML frontmatter
├── synthesis/                      # Literature reviews, tables, synthesis notes
├── exports/                        # Spreadsheets, BibTeX, RIS exports
└── phase4/                         # Verify-kit outputs (trust consensus, RoB/COI, retraction)
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
    "workspaces/avarel-fuse-multispectral/protocol.json"
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

## 3. Standard Action Names

`log_event.py` uppercases any `--action` string (log_event.py:188) and enforces
no closed enum: the names below are the committed convention, not a validator.
`PROJECT_INITIALIZED` is written by `init_project.py`; `GENESIS` follows once
`intent.json` + `protocol.json` exist (`specs/inception-ecosystem/02_handoffs.md`
§§2.1-2.2). Stage names for search/screening/extraction/RAG/synthesis/verify
follow `02_handoffs.md` §2.4; the `INDEX.md` catalog scan registers the
screening/prisma/extraction/synthesis filenames it knows (log_event.py:30-62).

- `PROJECT_INITIALIZED`: workspace created with `project.json` (+ `INDEX.md`).
- `GENESIS`: protocol provenance (+ `audit/recon_context.json` sidecar when grounded).
- `DISCOVERY_SEARCH`: raw queries executed across academic providers.
- `DEDUPLICATION`: merging title/DOI clusters into canonical representatives.
- `VERIFICATION_HYDRATION`: Crossref/OpenAlex DOI resolution and abstract hydration.
- `SCREENING_TITLE_ABSTRACT`: AI/manual screening against `SCREENING_CRITERIA.md`.
- `PDF_DISCOVERY_DOWNLOAD`: fetching Open Access PDFs with magic byte validation.
- `FULLTEXT_EXTRACTION`: parsing PDFs into Markdown with YAML frontmatter.
- `RAG_INDEXING`: chunking and vector indexing.
- `SYNTHESIS_GENERATION`: generating literature reviews and synthesis matrices.

---

## 4. Master Index Format (`INDEX.md`)

`INDEX.md` is automatically refreshed whenever an event is logged
(`refresh_index_md`: log_event.py:11-156). Committed headings and labels:

```markdown
# Project Index: [Project Title]

- **Project Slug**: `[project-slug]`
- **Last Updated**: `[YYYY-MM-DD HH:MM:SS UTC]`
- **Project Status**: `ACTIVE`

## 📊 Summary Metrics
- **Discovered Papers**: 251
- **Verified Papers**: 239
- **Downloaded PDFs**: 0
- **Extracted Markdowns**: 0

## 🎯 Research Questions
1. **RQ1**: ...
2. **RQ2**: ...

## 📂 Project File Catalog

| File / Directory | Description | Last Modified | Status |
| :--- | :--- | :--- | :--- |
| `project.json` | Project manifest, metadata, and research questions | 2026-08-28 | Active |
| `INDEX.md` | Master project directory and status catalog | 2026-08-28 | Synced |
| `audit/journal.jsonl` | Append-only provenance event journal | 2026-08-28 | Active |
| `SCREENING_CRITERIA.md` | PRISMA inclusion / exclusion screening rules | 2026-08-28 | Ready |
| `literature/verified.json` | Hydrated bibliographic records with DOIs & abstracts | 2026-08-28 | Verified |
| `exports/verified_summary.csv` | Clean verified bibliography spreadsheet | 2026-08-28 | Exported |
```

Conditional metric rows appear only when the key exists in `project.json`
`stats`: `Screened Papers`, `Full-Text Eligible Candidates` (with confirmed +
provisional-caveat split), `Confirmed Excluded Studies`, `Post-Audit Clean
Corpus`, `Merged Canonical Records` (log_event.py:87-115). The catalog lists
only files that exist on disk, from the committed `key_files` table plus a
`reports/*.md` scan and `pdfs/` / `extracted/` counts (log_event.py:30-85).
