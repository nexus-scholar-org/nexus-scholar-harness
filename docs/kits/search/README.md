# Scholar Search Kit

[![CI Status](https://github.com/nexus-scholar-org/scholar-search-kit/actions/workflows/scholar-search-kit-ci.yml/badge.svg)](https://github.com/nexus-scholar-org/scholar-search-kit/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Scholar Search Kit** is the discovery, deduplication, and verification backbone of the Nexus Scholar Suite.

It provides a unified Python API and Command Line Interface (CLI) to query, normalize, verify, and export academic literature across major scholarly databases: **OpenAlex**, **Semantic Scholar**, **Crossref**, **PubMed**, **arXiv**, and **bioRxiv**.

---

## Key Features

- **Federated Academic Search**: Search across multiple scholarly repositories simultaneously with automatic rate limiting and polite crawler headers.
- **Citation Snowballing**: Perform forward snowballing (finding citing papers) and backward snowballing (traversing references) to map research fields.
- **Document Verification & Hydration**: Detect LLM hallucinations and verify citation existence against Crossref/OpenAlex, hydrating missing abstracts, venues, and metrics.
- **Smart Deduplication**: Merges duplicate records by persistent identifiers (DOI, arXiv ID, PMID, OpenAlex ID) and title similarity ($\ge 97\%$), combining metadata into a comprehensive representative record.
- **Interoperable Export**: Directly export normalized results to JSON, JSONL, or CSV for seamless downstream processing with `scholar-pdf-kit` and `scholar-rag-kit`.

---

## Installation

The kit is no longer a separate repository. Since 2026-11-03 it is the `scholar_search` package inside the one `nexus-scholar` package (`src/scholar_search/`). The old `scholar-search-kit` repository and its CI badge above are archived history.

```bash
# As a user: the released beta
uv tool install "nexus-scholar>=1.1.0b6"

# As a developer, from a clone of this repository
uv sync --extra dev
```

---

## Provider facts (2026-11)

The full reference is [`PROVIDERS_2026-11.md`](PROVIDERS_2026-11.md): what each provider offers today, what our code sends, and the ranked hardening candidates. The points that change how you run a search:

- **Contact email.** `SCHOLAR_MAILTO` has no default. A live search refuses with `MAILTO_NOT_SET` until it is set (`src/scholar_search/config.py:12-17`, `src/scholar_search/engine.py:35-44`).
- **OpenAlex needs a key.** OpenAlex made API keys mandatory on 2026-02-13. Without `SCHOLAR_OPENALEX_KEY` a request shares a small daily budget with every caller on your IP, and OpenAlex documents that cursor paging past the first page answers 401. The code still calls the key "Premium ... (Optional)" (`config.py:20-22`) and still sends `mailto`, which OpenAlex no longer uses. Set the key.
- **OpenAlex page size.** OpenAlex supports `per_page` up to 100; 200 is deprecated. Keyword mode asks for up to 200 (`src/scholar_search/providers/openalex.py:160`) and snowballing asks for 200 (`openalex.py:266, 297`). Known issue, not fixed.
- **Crossref rate.** Crossref allows list requests at 3 per second in the polite pool (1 per second without a contact address) since 2026-07-21. Our default is 5 per second (`config.py:46-48`), so long legs draw 429 retries. Known issue, not fixed.
- **PubMed `[ab]` is not a field tag (known bug).** `src/scholar_search/providers/pubmed.py:33` maps the abstract field to `[ab]`. PubMed does not know that tag and silently widens the term to all fields, while the leg's executed query still shows `[ab]`. The fix (`[tiab]`) is planned, not done.
- **Default databases disagree (known inconsistency).** Five providers (OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed) are the default in `src/scholar_search/engine.py:32`, `src/scholar_search/plan.py:26`, the browser plan (`src/scholar_harness/console/api/discovery.py:53`) and `scholar-search search` without a protocol (`src/scholar_search/cli.py:195-201`). Four (no PubMed) are the default when a protocol has no `target_databases` (`src/scholar_search/protocol_adapter.py:81-84`, `src/scholar_protocol/models.py:126-129`), in recon (`src/scholar_harness/recon/engine.py:32`) and in the MCP tool `nexus_discover` (`src/scholar_agent/server.py:510-515`). bioRxiv is never a default.
- **User-Agent.** Requests carry `scholar-search-kit/0.1.0`, plus ` (mailto:<address>)` when a contact email is set (`src/scholar_search/http_client.py:74-76`). The version string is stale: the package is `nexus-scholar` 1.1.0b5.

---

## Command Line Interface (CLI)

### 1. Multi-Provider Literature Search
```bash
# Direct keyword search
uv run scholar-search search "transformer attention mechanism" --limit 20 --output results.json

# Protocol-driven federated search (Phase 0 -> Phase 1 integration)
uv run scholar-search search --protocol protocol.json --output results.json
```

**Example Output:**
```text
Search Results for: 'transformer attention mechanism'
┌────────┬────────────────────────────────┬──────────────┬──────────────────────┬────────────┐
│ Year   │ Title                          │ Provider     │ DOI / ID             │  Citations │
├────────┼────────────────────────────────┼──────────────┼──────────────────────┼────────────┤
│ 2017   │ Attention Is All You Need      │ openalex     │ 10.5555/3295222.329… │     145000 │
│ 2018   │ BERT: Pre-training of Deep     │ arxiv        │ 1810.04805           │      92000 │
│        │ Bidirectional Transformers     │              │                      │            │
└────────┴────────────────────────────────┴──────────────┴──────────────────────┴────────────┘
Saved 20 documents to results.json (JSON)
```

### 2. Citation Snowballing
```bash
# Forward snowballing (papers citing Attention Is All You Need)
uv run scholar-search snowball W2741809807 --provider openalex --direction forward --limit 25 --output citing.json

# Backward snowballing (papers cited by Attention Is All You Need)
uv run scholar-search snowball W2741809807 --provider openalex --direction backward --limit 25 --output refs.json
```

### 3. Ingestion, Verification, & Hydration
```bash
# Import an RIS or JSON library, verify existence, and hydrate missing abstracts
uv run scholar-search import my_collection.ris --verify --enrich --output verified.json
```

### 4. Deduplication & Entity Resolution
```bash
uv run scholar-search dedup raw_papers.json --output deduped.json
```

### 5. PRISMA 2020 Title/Abstract Screening
```bash
# Evaluates candidate papers against protocol.json inclusion/exclusion rules
uv run scholar-search screen --input deduped.json --protocol protocol.json --output-dir literature/
```
Generates:
- `literature/included.json`: Included papers advancing to full-text retrieval
- `literature/excluded.json`: Excluded papers with reason codes (`EXC-01`, `EXC-02`)
- `literature/conflicts.json`: Borderline confidence cases flagged for human review
- `literature/prisma_screening_report.md`: Formatted PRISMA 2020 flow report table

---

## Programmatic Python API

```python
import asyncio

from scholar_search import SearchEngine, Query, DocumentVerifier, Exporter
from scholar_search.providers import OpenAlexProvider, ArxivProvider

async def main():
    # 1. Initialize Engine
    engine = SearchEngine(providers=[OpenAlexProvider(), ArxivProvider()])
    try:
        # 2. Execute Query (search_all is async: engine.py:222)
        query = Query(text='title:"deep learning"', year_min=2022, max_results=25)
        documents = await engine.search_all(query, dedup=True)
    finally:
        await engine.close()

    # 3. Export to JSON for scholar-pdf-kit
    Exporter().json(documents, "literature_review.json")

asyncio.run(main())
```

---

## Documentation

- [API Reference](api_reference.md): Technical interface documentation.
- [Provider reference, 2026-11](PROVIDERS_2026-11.md): provider limits, what the code sends, known gaps.
- [`docs/kits_surface_matrix.md`](../../kits_surface_matrix.md): the verified API, CLI and MCP map.

The tutorial this section used to link (`docs/tutorial.md`) does not exist in this repository.

---

## License

This project is licensed under the MIT License.
