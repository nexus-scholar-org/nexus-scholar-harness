# Raw Literature Search Staging Directory

This directory stores immutable, raw provider responses and translated query provenance before deduplication:

- `provenance_manifest.json`: Execution log mapping each provider, stream (A, B, C), query string, HTTP status, and response count.
- `openalex_raw.json`: Raw OpenAlex JSON payloads.
- `semanticscholar_raw.json`: Raw Semantic Scholar bulk search JSON payloads.
- `crossref_raw.json`: Raw Crossref REST JSON payloads.
- `arxiv_raw.json`: Raw arXiv Atom XML/JSON payloads.

All raw payloads are normalized and combined into `../raw_search.json`, then deduplicated into `../deduped.json`.
