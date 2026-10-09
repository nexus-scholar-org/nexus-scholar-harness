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
5. **Systematic Screening Engine**: Evaluates candidate title/abstract relevance against `protocol.json.screening_criteria`, generating `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json`, and markdown PRISMA 2020 flow diagrams.
6. **Standardized Export**: Exports normalized collections to JSON, JSONL, or CSV for direct handoff to `scholar-pdf-kit`, `scholar-graph-kit`, and `scholar-rag-kit`.

---

## Quick CLI Cheat-Sheet

All commands should be run within the project context via `uv run`:

```bash
# 1. Search Literature (Protocol-Driven or Query String)
uv run scholar-search search --protocol workspaces/<project-slug>/protocol.json --output raw_search.json
uv run scholar-search search "transformer attention mechanism" --limit 30 --output results.json

# 2. 2-Tier Deduplication & Canonical Workspace ID Assignment
# (dedup takes a positional input file and only --output/--format — no --export/--csv-output)
uv run scholar-search dedup raw_search.json --output deduped.json

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
uv run scholar-search chain W2741809807 W290382718 --provider openalex --depth 2 --direction backward --direction forward --output chain.json --edges-output chain_edges.json

# 6. Export for Reference Managers (export takes INPUT + OUTPUT positionals — no --output flag)
uv run scholar-search export results.json results.ris --format ris

# 7. Export to CSV / JSONL
uv run scholar-search export results.json results.csv --format csv
uv run scholar-search export results.json results.jsonl --format jsonl

# 8. Compare Screening Runs
uv run scholar-search screen-compare run_a.json run_b.json
uv run scholar-search screen-compare run_a.json run_b.json -o report.md

# 9. Validate Search Query Recall
uv run scholar-search validate-query "machine learning" --seed 10.1000/test1 --seed 10.1000/test2
uv run scholar-search validate-query "NLP" --seed 10.1000/a --seed 10.1000/b -o results.json
```

### RIS Export

Export documents to RIS (Tagged) format for Rayyan/Covidence/EndNote/Zotero:

```bash
scholar-search export results.json results.ris --format ris
```

`export` takes `<input_file> <output_file>` positionals plus `--format` — it has
no `--output` flag. Do not invent one.

**Field Mappings:**
- TY: JOUR (journal), CONF (conference), GEN (generic)
- TI: Title
- AU: Family, Given format
- PY: Publication year
- JO/T2: Journal/Conference name
- AB: Abstract
- DO: DOI
- UR: URL
- C1: arXiv ID (prefixed with "arXiv:")
- DB: Source provider
- ER: Record terminator

### Screen-Compare Command

Compare two screening runs for inter-rater reliability.

```bash
uv run scholar-search screen-compare run_a.json run_b.json
uv run scholar-search screen-compare run_a.json run_b.json -o report.md
```

**Output:** Markdown report with agreement rate, transition matrix, and discrepancies.

### Validate-Query Command

Validate search query recall against golden seed DOIs.

```bash
uv run scholar-search validate-query "machine learning" --seed 10.1000/test1 --seed 10.1000/test2
uv run scholar-search validate-query "NLP" --seed 10.1000/a --seed 10.1000/b -o results.json
```

**Options:**
- `--seed/-s`: Golden seed DOI (repeatable, required)
- `--output/-o`: Output JSON file path

### Completeness Scoring

Documents are scored 0-10 for representative election during deduplication:

| Criterion | Points |
|-----------|--------|
| Has DOI | +2 |
| Has Abstract (>20 chars) | +2 |
| Has Venue | +1 |
| Has Authors | +1 |
| Has Year | +1 |
| Has Citations | +1 |
| Has ORCID | +1 |
| Not Retracted | +1 |

Provider weight (0-5) is added for total score (0-15).

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
    # NOTE: compile_protocol_search returns provider NAME strings, but
    # SearchEngine needs provider INSTANCES — resolve names to instances
    # (see references/providers.md) or omit providers for the default suite.
    from scholar_search.providers import (
        ArxivProvider, BiorxivProvider, CrossrefProvider,
        OpenAlexProvider, PubMedProvider, SemanticScholarProvider,
    )
    _PROVIDER_CTORS = {
        "openalex": OpenAlexProvider, "semanticscholar": SemanticScholarProvider,
        "crossref": CrossrefProvider, "arxiv": ArxivProvider,
        "pubmed": PubMedProvider, "biorxiv": BiorxivProvider,
    }
    engine = SearchEngine(
        providers=[_PROVIDER_CTORS[n]() for n in providers if n in _PROVIDER_CTORS]
        or None
    )
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
- **Dedup**: PID tier (doi/arxiv/pubmed/openalex/s2) → exact-normalized-title →
  fuzzy title ≥ 0.97 + year ±1 + first-author containment; a conflicting
  persistent ID in the same namespace vetoes any title match; assigns `SCI-%06d`
  canonical ids via `Deduplicator.deduplicate(docs) -> list[DocumentCluster]`
  (representative elected by completeness score + provider weight).
- **Verifier thresholds**: match = SequenceMatcher ratio ≥ 0.90 over normalized
  title keys, or bidirectional title containment with the contained title ≥ 12
  chars (`bidirectional_title_similarity`); Crossref `validate_reference` further
  requires relevance `score > 40`.
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
- **MCP tools** (subset of the full CLI/API surface — no full provider parity):
  `nexus_discover(query, limit=10, start_year=2020)` hardcodes 4 providers only
  (OpenAlex/Semantic Scholar/Crossref/arXiv — no PubMed/bioRxiv), forces
  `dedup=True`, and writes `.cache/mcp/discover_<slug>_<ts>.json` resolved via
  `_resolve_path` (`NEXUS_MCP_WORKSPACE` else repo root) → pass absolute
  workspace paths; `nexus_dedup` reads JSON only (`JSONImporter`) and writes
  JSON; `nexus_screen` runs in-process **heuristic** screening and persists all
  five artifacts (`included.json`, `excluded.json`, `conflicts.json`,
  `prisma_report.json`, `prisma_screening_report.md`); `nexus_screen_llm` is the
  LLM variant (checklist prompt per protocol criteria, heuristic fallback per
  batch on API failure); `nexus_screen_reconcile` accepts either a
  screener-id → `{workspace_id: INCLUDE|EXCLUDE}` JSON map or a directory of
  `batch_*_decisions*.json` files (screener key derived from the file stem),
  plus an optional adjudication map — strict-majority voting with Fleiss' Kappa.
- **LLM screening** (`LLMBatchScreener`) needs `GEMINI_API_KEY` (default model
  `gemini-2.0-flash`, batch size 20).
- **Screening is two tracks — do not conflate them.** The harness's authoritative
  PRISMA track is the **agent-in-the-loop** file handoff (`agent_screen.py
  prepare` chunks candidates into `literature/screening/batch_NNN.json`; an
  agent writes `batch_NNN_decisions.json`; `collect` assembles the final
  `included/excluded` + PRISMA report). The CLI `screen` / MCP `nexus_screen`
  heuristic (and `nexus_screen_llm`) is a fast deterministic pre-filter, not a
  substitute for agent review.
- **Identity**: `workspace_id` (`SCI-%06d`) is a dedup-run-local canonical id,
  not a stable cross-run study identity. Corpus-level lineage lives in
  `scholar_search.identity` (`CorpusSnapshotIdentity`, `build_corpus_snapshot_artifact`).

## Task routing → references/

| Task | Read first |
| :--- | :--- |
| Provider choice, keys, polite-pool, rate limits | `references/providers.md` |
| Query syntax, protocol search, snowball/chain | `references/search_and_snowballing.md` |
| Verify/hydrate, dedup tiers, representative election | `references/verification_and_dedup.md` |
| Import/export formats, PDF-handoff shape | `references/io_and_pipeline.md` |

## Agent Guidelines & Best Practices

- **Protocol Conformance**: Always use `--protocol` when working within a project workspace to ensure search keywords, date bounds, and languages match the frozen research protocol.
- **Screening Transparency**: Heuristic `screen` output is candidate triage only. Authoritative inclusion requires the agent `prepare`/`collect` handoff; always check `literature/prisma_screening_report.md` and log `SCREENING_COMPLETED` events to `audit/journal.jsonl`.
- **Handoff to PDF & Graph Kit**: Pass `literature/included.json` directly to the `scholar-pdf-kit` downloader and `scholar-graph` builder (see those skills for exact commands).
