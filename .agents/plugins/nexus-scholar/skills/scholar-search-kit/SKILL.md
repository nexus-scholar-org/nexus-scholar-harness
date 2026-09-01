---
name: scholar-search-kit
description: Instructions for using the scholar-search-kit Python API and CLI to search, snowball, verify, deduplicate, screen, and export academic literature across OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv, and bioRxiv.
---

# `scholar-search-kit` Skill Instructions

You are an expert academic research agent equipped with `scholar-search-kit`. This toolkit is the discovery, deduplication, verification, and screening backbone of the Nexus Scholar Suite.

## Core Capabilities
1. **Protocol-Driven Federated Academic Search**: Compiles `protocol.json.search_strategy` into targeted queries across `OpenAlex`, `Semantic Scholar`, `Crossref`, `PubMed`, `arXiv`, and `bioRxiv`.
2. **Citation Snowballing**: Traces forward citing papers and backward reference graphs.
3. **Verification & Abstract Hydration**: Verifies citation authenticity against Crossref/OpenAlex to detect hallucinations, strips JATS XML markup (`<jats:p>`), and hydrates rich abstracts.
4. **Smart 2-Tier Deduplication**: Merges duplicate records by persistent IDs (DOI, arXiv, PMID, OpenAlex) and fuzzy title similarity ($\ge 97\%$) with author/year validation, assigning canonical `workspace_id: SCI-XXXXXX` identifiers.
5. **Systematic Screening Engine**: Evaluates candidate title/abstract relevance against `protocol.json.screening_criteria`, generating `included.json`, `excluded.json`, `conflicts.json`, and markdown PRISMA 2020 flow diagrams.
6. **Standardized Export**: Exports normalized collections to JSON, JSONL, or CSV for direct handoff to `scholar-pdf-kit`, `scholar-graph-kit`, and `scholar-rag-kit`.

---

## Quick CLI Cheat-Sheet

All commands should be run within the project context via `uv run`:

```bash
# 1. Search Literature (Protocol-Driven or Query String)
uv run scholar-search search --protocol workspaces/<project-slug>/protocol.json --output raw_search.json
uv run scholar-search search "transformer attention mechanism" --limit 30 --output results.json

# 2. 2-Tier Deduplication & Canonical Workspace ID Assignment
uv run scholar-search dedup raw_search.json --output deduped.json --export csv --csv-output dedup_summary.csv

# 3. Verify Authenticity & Hydrate Rich Abstracts
uv run scholar-search verify deduped.json --output verified.json --enrich

# 4. PRISMA 2020 Systematic Screening
uv run scholar-search screen \
  --input verified.json \
  --protocol workspaces/<project-slug>/protocol.json \
  --output-dir workspaces/<project-slug>/literature/

# 5. Citation Snowballing (Forward = Citing Papers, Backward = References)
uv run scholar-search snowball W2741809807 --provider openalex --direction forward --output citing.json
uv run scholar-search snowball W2741809807 --provider openalex --direction backward --output references.json
```

---

## Programmatic Python API

```python
import asyncio
from pathlib import Path
from scholar_search import SearchEngine, Query, Deduplicator, DocumentVerifier, Exporter
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.screening import evaluate_heuristic_screening, partition_screening_results

async def main():
    # 1. Compile Query from Protocol
    query, providers = compile_protocol_search(Path("workspaces/my-project/protocol.json"))

    # 2. Federated Search Across Academic Providers (Async)
    engine = SearchEngine(providers=providers)
    documents = await engine.search_all(query, dedup=False)
    await engine.close()

    # 3. 2-Tier Deduplication & Canonical Workspace ID Fusion
    deduplicator = Deduplicator()
    clusters = deduplicator.deduplicate(documents)
    unique_docs = [c.representative for c in clusters]

    # 4. Verify & Hydrate Abstracts (Async)
    verifier = DocumentVerifier()
    processed_docs, audit = await verifier.process_batch(unique_docs, verify=True, enrich=True)

    # 5. Export for downstream PDF harvesting and graph building
    exporter = Exporter()
    exporter.json(processed_docs, "workspaces/my-project/literature/verified.json")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Agent Guidelines & Best Practices

- **Protocol Conformance**: Always use `--protocol` when working within a project workspace to ensure search keywords, date bounds, and languages match the frozen research protocol.
- **Screening Transparency**: When screening candidates, always check `literature/prisma_screening_report.md` and log `SCREENING_COMPLETED` events to `audit/journal.jsonl`.
- **Handoff to PDF & Graph Kit**: Pass `literature/included.json` directly to `scholar-pdf download` and `scholar-graph build`.
