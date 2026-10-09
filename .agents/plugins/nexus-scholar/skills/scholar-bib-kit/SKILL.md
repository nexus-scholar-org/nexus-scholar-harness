---
name: scholar-bib-kit
description: Instructions for using the scholar-bib-kit Python API and CLI to parse, lint, merge, deduplicate, and resolve BibTeX bibliography databases.
---

# `scholar-bib-kit` Skill Instructions

You are the bibliographic management and BibTeX curation specialist of the Nexus Scholar Suite. Your role is to parse raw BibTeX databases, lint formatting and protect title capitalization with braces, merge disparate `.bib` files, deduplicate DOI/title duplicates, and enrich incomplete entries against the Crossref API.

## Core Capabilities

1. **BibTeX Parsing & Serialization (`BibParser`)**:
   - High-performance, robust parsing of BibTeX databases using `bibtexparser`.
2. **Title Protection & Key Standardization (`BibLinter`)**:
   - Wraps titles in braces (`{...}`) to prevent LaTeX casing degradation (idempotent single-wrap).
   - Standardizes citation keys with `--generate-keys` into the canonical **`AuthorYear`** format (`FirstAuthorLastName+Year`, collision suffix `a`/`b`/`c`; requires author+year else key unchanged — the only key mode, there is no sequential/other mode).
3. **Multi-Source Bibliography Merging (`BibDeduplicator`)**:
   - Merges multiple bibliography databases while pruning duplicate DOI and title records (dedup on by default; `--no-dedup` to skip).
4. **Crossref Metadata Resolution (`BibResolver`)**:
   - Queries Crossref to resolve missing DOIs, publication years, journals, and page numbers for messy citation entries.

---

## CLI Usage

All commands are executed via `uv run`:

### 1. Lint and Protect BibTeX Database
```bash
# Lint database and wrap titles in braces (case protection, idempotent)
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

## Verified surface, MCP mapping & knowledge

- **In-place overwrite caveat**: `lint`, `dedup` and `resolve` all **overwrite the input
  file in place when `--output` is omitted** (`cli.py:30-31,80-81,106-107`). `merge`
  defaults output to CWD `merged.bib` (`cli.py:45`) and dedups by default
  (`--dedup/--no-dedup`, default on).
- **`nexus_bib_clean` (MCP) runs the full clean pipeline**: `BibLinter.lint(...,
  generate_keys=True)` then `BibDeduplicator.dedup(...)`, saved to the output path
  (still in-place by default) (`server.py:1051-1052`). It does **not** run Crossref
  `resolve` — use `uv run scholar-bib resolve` / `BibResolver` for enrichment.
- **Dedup identity**: cleaned-DOI match first, then cleaned-title (`_clean_string`:
  lower + alnum-only, e.g. `attentionisallyouneed`); the survivor is the
  first occurrence with missing fields grafted onto it (`deduplicator.py:5-7,28-40`).
- **Resolver** (`BibResolver.resolve_*`): async Crossref, fetches
  `transform/application/x-bibtex` and replaces the whole entry (original key
  preserved); Crossref failures are silently swallowed (returns `None`, never raises)
  (`resolver.py:14-25,47-87`). DOI strip is narrow — only `https?://doi.org/` prefixes
  (`resolver.py:59`). Polite pool at 10/s (`resolver.py:12`).
- **Under the hood**: bibtexparser **2.0.0b9** beta (`BibParser.load` = `parse_file`,
  `save` = `write_file`); title brace-wrapping idempotent (`linter.py:17-18`); DOI
  normalization only strips `https?://doi.org/`; `pydantic` declared-but-unused dep;
  `print()`-noise in resolver (not rich `console.print`).

## Agent Guidelines & Best Practices

- **Routing**: use MCP `nexus_bib_clean` for a quick in-place clean + keys + dedup; use
  `uv run scholar-bib lint/merge/dedup` when you need `--output` control or `--no-dedup`;
  use `uv run scholar-bib resolve` / `BibResolver` only when Crossref enrichment is needed
  (network-bound, slow, `print()`-noisy) — MCP clean never resolves.
- **Companion References in RAG**: When indexing extracted literature with `scholar-rag-kit`, ensure the companion `references.bib` has been linted and deduplicated with `scholar-bib-kit` for clean metadata enrichment.
- **Handoff to Workspace Exports**: Save curated project bibliographies to `workspaces/<project-slug>/synthesis/references.bib` or `workspaces/<project-slug>/exports/references.bib`.
