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
uv run scholar-search dedup raw_search.json --output deduped.json --format csv

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
# Multi-hop BFS chaining: traverse references FORWARD (citing) and/or BACKWARD (references) up to --depth N
uv run scholar-search chain W2741809807 W290382718 --provider openalex --depth 2 --direction backward forward --output chain.json --edges-output chain_edges.json
```

---

## Programmatic Python API

```python
import asyncio
from pathlib import Path
from scholar_search import SearchEngine, Deduplicator, DocumentVerifier, Exporter
from scholar_search.models import Query   # Query/Document are NOT re-exported at package root
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

## Verified surface, MCP mapping & knowledge

- **Provider defaults**: `SearchEngine(providers=None)` builds **all 6** providers; the
  CLI search default is **5** (no bioRxiv); `compile_protocol_search` default DBs =
  openalex, semanticscholar, crossref, arxiv. `search` CLI has no single-top-K — it
  queries all providers and dedups.
- **Dedup**: PID tier → exact-normalized-title → fuzzy title ≥ 0.97 + year ±1 +
  first-author containment; assigns `SCI-%06d` canonical ids via
  `Deduplicator.deduplicate(docs) -> list[DocumentCluster]`.
- **Rate limits / env**: OpenAlex 10/s, Crossref 5/s, Semantic Scholar 1/s, PubMed 3/s,
  arXiv/bioRxiv 1/s; Scopus/WebOfScience unsupported. Set `SCHOLAR_MAILTO` (polite pool),
  `SCHOLAR_OPENALEX_KEY`, `SCHOLAR_S2_KEY`, `SCHOLAR_CACHE_DIR`. Client = httpx + hishel,
  4 transport retries, 429 → 5 exponential retries, 30 s timeout, UA
  `scholar-search-kit/0.1.0 (mailto:…)`.
- **Per-provider exceptions are swallowed** — empty results (`{"total": 0, "documents": []}`)
  are a *valid* outcome, not an error. Check provider-level errors, never assume the empty
  list means "no network".
- **Snowball sandbox**: caps depth 5 / max 500 / 2000 docs; CLI `chain` defaults
  depth 1 / 200 / 500 backward.
- **MCP tools**: `nexus_discover` (hardcodes OpenAlex/Semantic Scholar/Crossref/arXiv —
  no PubMed/bioRxiv — `dedup=True` forced, writes `.cache/mcp/discover_<slug>_<ts>.json`
  CWD-relative → pass/expect absolute workspace paths), `nexus_dedup` (JSON only),
  `nexus_screen` (in-process heuristic screening; `conflicts.json`/`prisma_report.json`
  are computed but **never written**), `nexus_screen_reconcile` (expects
  `batch_NNN_decisions*.json` files keyed by screener id from the file stem).
- **LLM screening** (`LLMBatchScreener`) needs `GEMINI_API_KEY`.

## Agent Guidelines & Best Practices

- **Protocol Conformance**: Always use `--protocol` when working within a project workspace to ensure search keywords, date bounds, and languages match the frozen research protocol.
- **Screening Transparency**: When screening candidates, always check `literature/prisma_screening_report.md` and log `SCREENING_COMPLETED` events to `audit/journal.jsonl`.
- **Handoff to PDF & Graph Kit**: Pass `literature/included.json` directly to `scholar-pdf download` and `scholar-graph build`.
