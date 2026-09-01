---
name: scholar-bib-kit
description: Instructions for using the scholar-bib-kit Python API and CLI to parse, lint, merge, deduplicate, and resolve BibTeX bibliography databases.
---

# `scholar-bib-kit` Skill Instructions

You are the bibliographic management and BibTeX curation specialist of the Nexus Scholar Suite. Your role is to parse raw BibTeX databases, lint formatting and protect title capitalization with double braces, merge disparate `.bib` files, deduplicate citation keys and title clusters, and enrich incomplete entries against the Crossref API.

## Core Capabilities

1. **BibTeX Parsing & Serialization (`BibParser`)**:
   - High-performance, robust parsing of BibTeX databases using `bibtexparser`.
2. **Title Protection & Key Standardization (`BibLinter`)**:
   - Wraps titles in double braces (`{{...}}`) to prevent LaTeX casing degradation.
   - Standardizes citation keys into canonical `AuthorYear` or sequential alphanumeric formats.
3. **Multi-Source Bibliography Merging (`BibDeduplicator`)**:
   - Merges multiple bibliography databases while pruning duplicate DOI and title records.
4. **Crossref Metadata Resolution (`BibResolver`)**:
   - Queries Crossref to resolve missing DOIs, publication years, journals, and page numbers for messy citation entries.

---

## CLI Usage

All commands are executed via `uv run`:

### 1. Lint and Protect BibTeX Database
```bash
# Lint database and wrap titles in double braces
uv run scholar-bib lint references.bib --output clean_references.bib

# Standardize citation keys to AuthorYear format
uv run scholar-bib lint references.bib --generate-keys --output standardized.bib
```

### 2. Merge Multiple BibTeX Files
```bash
# Merge multiple libraries and deduplicate automatically
uv run scholar-bib merge library1.bib library2.bib library3.bib --output merged.bib
```

### 3. Deduplicate a Single BibTeX File
```bash
# Deduplicate records by DOI and title similarity
uv run scholar-bib dedup references.bib --output deduped.bib
```

### 4. Resolve Incomplete Entries via Crossref API
```bash
# Resolve missing metadata and DOIs against Crossref
uv run scholar-bib resolve raw_entries.bib --output resolved.bib
```

---

## Python API

```python
import asyncio
from pathlib import Path
from scholar_bib.parser import BibParser
from scholar_bib.linter import BibLinter
from scholar_bib.deduplicator import BibDeduplicator
from scholar_bib.resolver import BibResolver

async def main():
    # 1. Load BibTeX Library
    library = BibParser.load(Path("workspaces/my-project/synthesis/references.bib"))

    # 2. Lint and format titles
    linted = BibLinter.lint(library, generate_keys=True)

    # 3. Deduplicate entries
    deduped = BibDeduplicator.dedup(linted)

    # 4. Resolve missing DOIs via Crossref (Async)
    resolver = BibResolver()
    await resolver.resolve_library(deduped)

    # 5. Save curated database
    BibParser.save(deduped, Path("workspaces/my-project/synthesis/references.bib"))

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Agent Guidelines & Best Practices

- **Companion References in RAG**: When indexing extracted literature with `scholar-rag-kit`, ensure the companion `references.bib` has been linted and deduplicated with `scholar-bib-kit` for clean metadata enrichment.
- **Handoff to Workspace Exports**: Save curated project bibliographies to `workspaces/<project-slug>/synthesis/references.bib` or `workspaces/<project-slug>/exports/references.bib`.
