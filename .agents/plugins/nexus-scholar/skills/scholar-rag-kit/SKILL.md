---
name: scholar-rag-kit
description: Instructions for using scholar-rag-kit Python API and CLI for structural AST chunking, methodology tagging, hybrid graph-boosted retrieval, and grounded synthesis over scientific literature.
---

# `scholar-rag-kit` Skill Instructions

You are the retrieval-augmented generation and synthesis specialist of the Nexus Scholar Suite: you index extracted literature through the **typed E3 service**, run **hybrid graph-boosted retrieval**, and generate **grounded synthesis** with atomic citation tokens. Similarity scores are never verification.

## Pinned surface

- Kit `scholar-rag-kit` **0.1.0** (`tools/scholar-rag-kit/pyproject.toml:7`), canonical rev `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad` (vendored `tools/scholar-rag-kit/`, sync commit `45304e1`).
- Entrypoints: CLI `scholar-rag` (`index|query|synthesize|consensus|matrix|stats|extract`, `cli.py`); Python API `scholar_rag.index_service.index_workspace` (`index_service.py:752`) over `IndexServiceRequest` (`index_service.py:400`); MCP `nexus_rag_query` / `nexus_rag_synthesize` / `nexus_matrix_extract` only — **indexing has no MCP parity** (see Boundaries).
- `scholar-protocol-kit` is a declared dependency (`pyproject.toml:33`), resolved from its pinned commit for `matrix.py`.

## Task map — which ref for which task

- `references/typed_index.md` — indexing: full required/optional flags, request assembly, exits, journal rule, manifest + R1–R7 + live-set proof, authoritative-vs-candidate.
- `references/retrieval_synthesis.md` — `query` / `synthesize` / `consensus` / `matrix` / `stats` flags, hybrid formula, citation tokens, entailment-similarity vocabulary, claims/verify mismatch.
- `references/mcp_and_boundaries.md` — MCP availability table, the declared-unsupported refusal envelope, audit events, legacy-vs-current, identity rules.

Read the ref for the task at hand; do not load all three by default.

## Prerequisites

- Extracted Markdown corpus (`<ws>/extracted/`), the **accepted parent view** JSON (acceptance adapter's output — never discovered here), and an explicit journal path. The typed path never infers any of these.
- A Chroma store path you state explicitly (default is CWD-relative `./chroma_db` on every command — always pass an absolute `<ws>/chroma_db` in workspaces).
- An embedder provider via `get_embedder` (`embedder.py:89`): `sentence-transformers` (default model `all-MiniLM-L6-v2`, downloads from HuggingFace on first use), `openai` (needs `OPENAI_API_KEY`), `gemini` (needs `GEMINI_API_KEY`), or hermetic `mock` for CI. The provider is locked per store — re-index into a fresh db to change it.
- Methodology enrichment (paradigm/study design) comes from the companion BibTeX only (`indexer.py:294`); without `--bib`/`bib_file` chunks lack it even if `project.json` exists.

## Common ops (minimal; full flags in refs)

```bash
# Typed index: 1 positional + 10 required options, none minted or discovered
uv run scholar-rag index <ws>/extracted/ \
  --parent-view <ws>/parent-view.json \
  --journal <ws>/run-reports/rag-index.jsonl \
  --workspace-root <ws> \
  --run-id <RUN-...> --created-at <rfc3339> \
  --producer-version <version> --producer-commit <40-hex> \
  --embedder-provider <provider> --embedder-model <model> --embedder-dimension <int>
# exits: 0 SUCCESS / 2 REFUSED / 3 PARTIAL / 4 FAILED (index_service.py:223)

# Hybrid retrieval with sectional slicing and graph boost
uv run scholar-rag query "<query>" --section-category methodology \
  --graph <ws>/literature/graph.json --alpha 0.25 --beta 0.15 --limit 5

# Grounded synthesis (+ claim ledger for consensus)
uv run scholar-rag synthesize "<research question>" --rq-id RQ1 \
  --output <ws>/synthesis/literature_review.md \
  --output-claims <ws>/synthesis/claims.json

# Protocol matrix (dynamic dims) or 7-dimension methodology matrix (no --protocol)
uv run scholar-rag matrix --protocol <ws>/protocol.json --output-dir <ws>/literature/
uv run scholar-rag consensus <ws>/synthesis/claims.json --rq-id RQ1 \
  --output-json <ws>/synthesis/consensus.json --output-md <ws>/synthesis/consensus.md
```

```python
from scholar_rag import ScholarRetriever, GroundedSynthesisEngine, get_embedder
from scholar_rag.index_service import IndexServiceRequest, index_workspace
from scholar_rag.replacement import ChromaReplacementView
from scholar_rag.index_verifier import ChromaVisibleSetReader

embed = get_embedder(provider="sentence-transformers")  # or "mock" (hermetic), "openai", "gemini"
result = index_workspace(  # same T-90 service the CLI calls; exits map to result.outcome
    request,  # IndexServiceRequest: explicit limbs + accepted parent_view + journal/docs refs
    backend=ChromaReplacementView(db_path="<explicit store>", collection_name="scholar_docs", embedder=embed),
    reader=ChromaVisibleSetReader(db_path="<explicit store>", collection_name="scholar_docs"),
    embedder=embed,
    workspace_root="<ws>",
)
retriever = ScholarRetriever(db_path="<explicit store>")
hits = retriever.query(query_text="...", section_category="methodology",
                       boost_dois=["10.1038/s41586-024"], graph_source="<graph.json>")
synthesis = GroundedSynthesisEngine(retriever=retriever).synthesize("...", rq_id="RQ1")
```

## Safety boundaries (non-negotiable)

- **Identity is recorded-artifact-only.** Chunk ids are content-derived `CHK-` identities minted by `mint_chunk_id` (`chunker.py:121`) from limbs read from `base_metadata` only — no fallback to frontmatter, filename, DOI, title, CWD, or `project.json` (`chunker.py:18-28`, identity reader `chunker.py:592`). A missing limb is a typed refusal, never a degraded id. The chunker option set is closed (`chunker.py:83`); `min_chunk_chars` is the honored micro-chunk merge threshold (`chunker.py:531`).
- **Parent lineage decides eligibility.** A document is indexed because the accepted parent named it; `docs_path` only scopes which files the run may read. The run refuses on disagreement — it never silently skips or invents Methodology/Results/Limitations.
- **Refusal, not silent defaults.** Missing `--journal`, identity limbs, or parent `documents` → `REFUSED` (exit 2) with a closed-vocabulary code. Provider failure is never an empty successful result. `--workspace-id` was removed from `index` (it survives only on `query`).
- **Authoritative vs candidate.** The typed run publishes an `IndexManifest` v1 sidecar (`index_manifest.py:130`), commits through the R1–R7 replacement protocol (`replacement.py:1385`, intent `replacement.py:638`) with live-set proof via `verify_backend` (`index_verifier.py:563`), and appends its own run report (`RAG_INDEX_RUN_BUILT` / `RAG_INDEX_RUN_REJECTED`, `index_service.py:209`) to the **explicit** journal destination — never to the canonical adapter ledger `audit/journal.jsonl` (refused, G-9). The §6.6 accepted-record event belongs to the future `index-acceptance-v1` adapter, not to this kit run.
- **Similarity is not entailment.** `entailment_score` with `VERIFIED (≥0.85)` / `AMBIGUOUS (≥0.50)` / `UNSUPPORTED` is embedding-cosine scaled to [0,1] with a lexical-overlap fallback (`synthesis.py:112`; status words `models.py:207`). No synthesis claim verifies semantic entailment, and RAG `claims.json` carries no `evidence_quote`/`claim_id` (see retrieval ref).
- **Legacy is superseded, not current.** `ScholarIndexer.index_markdown/index_directory` upsert (`indexer.py:84,280`, `collection.upsert` at `indexer.py:126`) is the path Stage 6 no longer uses (harness stub `orchestrator.py:58`; Stage 6 calls `index_workspace`, `orchestrator.py:1425`). Never present it as the typed path; `matrix` (no-`--protocol` fallback) and `stats` still drive it — that is stated in the retrieval ref, not a recommendation.
- **MCP has no indexing parity.** `nexus_rag_index` is **declared unsupported** (capability `rag_indexing`, `mcp_supported: false`, owner `nexus-scholar-org/scholar-rag-kit`, `capabilities.py:56`): every call returns `operation="rag_index"`, `status="FAILED"`, zero I/O, one non-retryable `UNSUPPORTED_CAPABILITY` error (`server.py:826`). Use the `scholar-rag index` CLI or `scholar_rag.index_service` API. This narrows nothing else: `nexus_rag_query` / `nexus_rag_synthesize` / `nexus_matrix_extract` remain available (see MCP ref).

## Versions and status

- Shipped package `0.1.0`; golden `producer.version 0.2.0` is the producing-kit version stamped inside the frozen golden manifest bytes, not the installed version.
- Status: E3 in progress. Live harness rows (incl. `E3-POS-005` golden parity) proven; 14 ledger rows stay honestly `MISSING` upstream of adapter/parity work. Do not claim acceptance semantics this kit does not publish.
- Auxiliary only (never the publication path): `NumpyBackend` (in-memory test backend), `LLMExtractor`/`PIIRedactor` and the `scholar-rag extract` command (Gemini `gemini-pro` extraction with heuristic fallback + PII redaction), and `gemini` embedding (`text-embedding-004`, 768-d). Details in refs; `index` has **no** `--api-key` flag.
