# Research Project Schema & State Management

Each research project inside `workspaces/<project-slug>/` contains a canonical `project.json` manifest that documents metadata, research objectives, search configurations, and execution milestones.

---

## 1. `project.json` Specification

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "project_id": "transformer-attention-survey",
  "registered_workspace_id": "WSP-9f2c1d0a7b3e4f5a8c6d2e1b0a9f8e7d",
  "title": "Comprehensive Survey on Transformer Attention Mechanisms",
  "description": "Systematic literature review investigating sparse and linear attention scaling properties.",
  "created_at": "2026-08-28T18:00:00Z",
  "updated_at": "2026-08-28T18:00:00Z",
  "status": "active",
  "authors": [
    {
      "name": "Lead Researcher",
      "email": "researcher@university.edu"
    }
  ],
  "research_questions": [
    "RQ1: What are the primary mathematical formulations for linear attention complexity?",
    "RQ2: How do sparse attention mechanisms compare in hardware memory efficiency?"
  ],
  "keywords": [
    "transformers",
    "attention mechanism",
    "sparse attention",
    "linear complexity"
  ],
  "search_criteria": {
    "year_min": 2017,
    "year_max": 2026,
    "languages": ["en"],
    "primary_providers": ["openalex", "arxiv", "semanticscholar"]
  },
  "stats": {
    "discovered_papers": 0,
    "verified_papers": 0,
    "downloaded_pdfs": 0,
    "extracted_markdowns": 0
  }
}
```

### 1.1 Required identity fields

| Field | Required | Form | Meaning |
|---|---|---|---|
| `project_id` | yes | human slug, e.g. `transformer-attention-survey` | Human-readable label. The directory name, the label in `INDEX.md`, and the `project_slug` in `intent.json`. **Not an identity.** |
| `registered_workspace_id` | yes | `WSP-` + 32 lowercase hex | The registered Contract v1 workspace identity. Minted once at initialization from the OS CSPRNG and recorded here; never regenerated. |

`registered_workspace_id` is the value every Contract v1 artifact under this
workspace states as its `workspace_id`. The frozen identifier registry admits
exactly one registered form for a workspace (`WSP-<opaque>`), so a slug is
refused by the typed surfaces: `project_id` is a label, `registered_workspace_id`
is the identity, and the two must never be used interchangeably.

Rules:

- **Mint once, at initialization.** `init_project.py` and the inception wizard
  mint it when `project.json` is first written. Re-initializing an existing
  workspace reuses the recorded value rather than minting a new one — otherwise
  artifacts already accepted under the old id would stop sharing a workspace.
- **Record, never mint, at use time.** Consumers read the recorded value. A
  workspace with no `registered_workspace_id` is a pre-registration workspace:
  indexing fails closed naming the missing field. Do not mint one, do not
  substitute `project_id`, and do not derive an id from the title or slug.
- **Survives `sync`.** `scholar-harness sync` merges statistics into the existing
  manifest instead of rebuilding it, so the recorded id is preserved.

---

## 2. Directory Layout Semantics

```text
workspaces/<project-slug>/
├── project.json            # Central project manifest (above)
├── literature/             # Raw queries, deduplicated corpora, and verification audits
│   ├── raw_search.json     # Initial multi-provider search dump
│   ├── deduped.json        # Deduplicated cluster representations
│   └── verified.json       # Crossref/OpenAlex verified records with hydrated abstracts
├── pdfs/                   # Binary Open Access PDFs
│   ├── download_summary.json # Resolution statuses and local file mappings
│   └── *.pdf               # Formatted as {year}_{author}_{title}.pdf
├── extracted/              # Full-text extracts
│   ├── *.md                # Clean Markdown produced via Docling
│   └── *.tei.xml           # Structured TEI XML produced via Grobid
├── synthesis/              # Synthesized literature review artifacts
│   ├── literature_review.md # Structured review narrative
│   ├── comparative_table.md # Cross-paper comparison matrices
│   └── evidence_matrix.csv  # Extracted findings mapped to Research Questions
└── exports/                # Exported citation bundles
    ├── references.bib      # Compiled BibTeX bibliography
    ├── library.ris         # RIS export for Zotero/Mendeley
    └── summary.csv         # Spreadsheet review export
```
