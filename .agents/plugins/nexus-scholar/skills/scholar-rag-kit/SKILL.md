---
name: scholar-rag-kit
description: Instructions for using scholar-rag-kit Python API and CLI for structural AST chunking, methodology tagging, hybrid graph-boosted retrieval, and grounded synthesis over scientific literature.
---

# `scholar-rag-kit` Skill Instructions

You are the scientific retrieval-augmented generation and synthesis specialist of the Nexus Scholar Suite. Your role is to index extracted literature corpora using **structural AST sectional chunking**, execute **hybrid graph-boosted semantic retrieval** (combining dense vector search with citation network PageRank), and generate **grounded research synthesis** with atomic claim-level attribution tokens.

## Core Capabilities

1. **Structural AST Chunking**: Splits papers along header hierarchies (`#`, `##`, `###`) to preserve section context (`Abstract`, `Methodology`, `Results`, `Limitations`), maintains hierarchy breadcrumbs, and enforces size guards. Chunk ids are content-derived `CHK-` identities minted by `mint_chunk_id` (`tools/scholar-rag-kit/src/scholar_rag/chunker.py:121`) from the ten §5.1 limbs read from `base_metadata` only — no fallback to frontmatter, filename, DOI, title, CWD, or `project.json` (`chunker.py:18-28,593`); `min_chunk_chars` is the honored micro-chunk merge threshold (`chunker.py:530`).
2. **Methodology Metadata Tagging**: Enriches chunks with paradigm, study design, sample size, evaluation metrics, dataset, and DOI from the companion `references.bib` as non-identity enrichment only. Identity is recorded-artifact-only: nothing is inferred from `project.json`, a title, the CWD, a DOI, a filename, or a document's own frontmatter (`tools/scholar-rag-kit/src/scholar_rag/indexer.py:294`, `chunker.py:18`).
3. **Typed Index Path**: Indexes through `scholar_rag.index_service.index_workspace` (`index_service.py:722`) over an explicit `IndexServiceRequest` — request limbs, the accepted `parent_view`, the embedder identity, and the journal/docs destinations are all stated, none inferred — publishing an `IndexManifest` v1 sidecar (`index_manifest.py:130`), committing through the R1–R7 replacement protocol (`replacement.py:1385`) with live-set proof via `verify_backend` (`index_verifier.py:563`). Legacy `ScholarIndexer.index_markdown/index_directory` upsert is the superseded path Stage 6 no longer uses (`src/scholar_harness/orchestrator.py:58,1402).
4. **Hybrid Graph-Boosted Retrieval**:
   $$\text{Score}(d) = \text{CosineSim}(q, d) + \alpha \cdot \text{PageRank}(d) + \beta \cdot \mathbb{I}_{\text{seed}}(d)$$
5. **Grounded Attributed Synthesis**: Generates research reviews with atomic citation tokens `[WORKSPACE_ID#SECTION#CHUNK_ID]` as shipped (`tools/scholar-rag-kit/src/scholar_rag/retriever.py:123`). Claim scores are kit-observed similarity vocabulary — `entailment_score` with `VERIFIED (≥0.85)` / `AMBIGUOUS (≥0.50)` / `UNSUPPORTED` is an embedding-cosine score scaled to [0,1] with a lexical-overlap fallback (`synthesis.py:112`; status words in `models.py:207`): similarity is not entailment, and synthesis does not verify semantic entailment.
6. **Cross-Study Methodology Matrix**: Extracts 7-dimension comparative matrices (`matrix.json` and `matrix.md`).
7. **Consensus Cartographer**: Clusters attributed synthesis claims into high-consensus findings vs. active debates with deterministic stance attribution and verdicts (`consensus.json`/`consensus.md`).
8. **Explicit-Journal, No-Discovery Indexing**: `index` writes its audit events to the journal you pass via `--journal` (`<ws>/audit/journal.jsonl`). It never discovers, infers, or creates a journal path. The typed service refuses any run whose identity limbs it was not told — `--run-id`, `--created-at`, `--producer-version`, `--producer-commit`, `--embedder-provider`, `--embedder-model`, `--embedder-dimension`, `--parent-view`, `--workspace-root` are all required, and none is ever minted or read for you. A missing journal flag is a failure, not a silent default.

---

## CLI Usage

### 1. Index Extracted Literature
```bash
uv run scholar-rag index <ws>/extracted/ \
  --parent-view <ws>/parent-view.json \
  --journal <ws>/audit/journal.jsonl \
  --workspace-root <ws> \
  --run-id <RUN-...> \
  --created-at <rfc3339> \
  --producer-version <version> \
  --producer-commit <40-hex> \
  --embedder-provider <provider> \
  --embedder-model <model> \
  --embedder-dimension <int>
```
All ten flags are **required** — the typed indexing service will not invent any identity limb you omit. `--workspace-id` was removed from `index` (it survives only on `query`) and is not a valid substitute for `--workspace-root`. Supply your own `db_path` explicitly if you need a persistent store: the default is CWD-relative `./chroma_db`.

### 2. Query with Graph Boost & Slicing
```bash
# Query methodology sections with PageRank boosting
uv run scholar-rag query "<search query>" \
  --section-category methodology \
  --paradigm "Design Science" \
  --graph workspaces/<project-slug>/literature/graph.json \
  --boost-doi <DOI> \
  --alpha 0.25 --beta 0.15 \
  --limit 5
```

### 3. Generate Grounded Synthesis
```bash
uv run scholar-rag synthesize "<research question>" \
  --rq-id RQ1 \
  --output workspaces/<project-slug>/synthesis/literature_review.md
```

### 4. Generate Dynamic Protocol Extraction Matrix
```bash
# Extract dynamic dimensions from protocol.json
uv run scholar-rag matrix \
  --protocol workspaces/<project-slug>/protocol.json \
  --output-dir workspaces/<project-slug>/literature/

# Or generate standard 7-dimension methodology matrix
uv run scholar-rag matrix \
  --output-md workspaces/<project-slug>/literature/matrix.md \
  --output-json workspaces/<project-slug>/literature/matrix.json
```

### 5. Consensus Cartographer (High-Consensus vs. Active Debates)
```bash
# Emit claims from synthesis for downstream cartography
uv run scholar-rag synthesize "<research question>" --rq-id RQ1 \
  --output workspaces/<project-slug>/synthesis/literature_review.md \
  --output-claims workspaces/<project-slug>/synthesis/claims.json

# Bucket claims into high-consensus findings / active debates
uv run scholar-rag consensus workspaces/<project-slug>/synthesis/claims.json \
  --rq-id RQ1 \
  --output-json workspaces/<project-slug>/synthesis/consensus.json \
  --output-md workspaces/<project-slug>/synthesis/consensus.md
```
Behavior: Jaccard greedy clustering (default threshold `0.30`, override `--threshold`), deterministic polarity-lexicon stance (`POSITIVE`/`NEGATIVE`/`NEUTRAL`) auto-derived from claim text unless a `stance` is pre-set in the claim input, per-study majority-stance dedup, then verdicts: `HIGH_CONSENSUS` (agreed ≥ contested threshold), `ACTIVE_DEBATE` (opposing*3 ≥ contested), `UNRESOLVED` (neutral majority), `PROVISIONAL` (<2 studies).

For real literature, paraphrased claims rarely share enough content words for lexical Jaccard to merge (e.g. max pairwise Jaccard ~0.17 on UAV-CV corpus → every-claim-is-its-own-cluster). Use semantic clustering, which replaces the scorer with embedding cosine (`embedder_claim_scorer`, falls back to lexical on embedder errors):

```bash
uv run scholar-rag consensus workspaces/<project-slug>/synthesis/claims.json \
  --rq-id RQ1 \
  --similarity sentence-transformers \
  --threshold 0.40 \
  --output-json workspaces/<project-slug>/synthesis/consensus.json \
  --output-md workspaces/<project-slug>/synthesis/consensus.md
```

A threshold of ~`0.40` (vs `0.30` lexical-default) gives topically coherent clusters on paraphrase-heavy corpora; sweep thresholds when in doubt. Filter obvious non-claim fragments (section headers like `5.1. Results…`, PDF watermarks/footers, figure captions, in-text reference lines) out of the claim pool first — they pollute clustering.

---

## In-Memory Vector Backend (NumpyBackend)

Lightweight vector storage without ChromaDB dependency.

```python
from scholar_rag.backends import NumpyBackend

backend = NumpyBackend()
backend.set_embedder(my_embedder)
backend.add_documents(ids=["1"], documents=["text"])
results = backend.query(query_embeddings=[[0.1, 0.2, ...]], n_results=5)
```

## Structured Extraction with LLM

Extract metadata from academic papers using Gemini or heuristic fallback.

```bash
uv run scholar-rag extract paper.md --output extraction.json
uv run scholar-rag extract paper.md --schema paper --api-key YOUR_KEY
```

**Features:**
- LLM-based extraction via Gemini REST API
- Heuristic fallback when LLM unavailable
- Automatic PII redaction (emails, ORCIDs, phones, grants)
- Confidence scoring

## Gemini Embedding Integration

Use Google's text-embedding-004 model for vector storage.

```bash
uv run scholar-rag index docs/ --embedder gemini
```

Requires `GEMINI_API_KEY` environment variable or `--api-key` flag.

---

## Python API

```python
from scholar_rag import (
    ScholarRetriever, GroundedSynthesisEngine,
    ConsensusCartographer, embedder_claim_scorer, get_embedder,
    NumpyBackend, LLMExtractor, PIIRedactor,
)
from scholar_rag.index_service import IndexServiceRequest, index_workspace
from scholar_rag.replacement import ChromaReplacementView
from scholar_rag.index_verifier import ChromaVisibleSetReader

# Index through the typed E3 service (primary path): the request carries the
# identity limbs per document, the accepted parent_view, the embedder identity,
# and explicit journal/docs destinations — stated, never inferred
# (tools/scholar-rag-kit/src/scholar_rag/index_service.py:370,722).
# The `scholar-rag index` CLI builds this same request (cli.py:224).
embed = get_embedder(provider="sentence-transformers")
result = index_workspace(
    request,  # IndexServiceRequest with explicit limbs + parent_view
    backend=ChromaReplacementView(db_path="<explicit store path>", collection_name="scholar_docs", embedder=embed),
    reader=ChromaVisibleSetReader(db_path="<explicit store path>", collection_name="scholar_docs"),
    embedder=embed,
    workspace_root="<ws>",
)
# Legacy ScholarIndexer.index_markdown/index_directory upsert is superseded:
# Stage 6 no longer uses it (src/scholar_harness/orchestrator.py:58,1402).

# Retrieve with Hybrid Graph Boost
retriever = ScholarRetriever(db_path="<explicit store path>")
results = retriever.query(
    query_text="adversarial robustness benchmark",
    section_category="methodology",
    boost_dois=["10.1038/s41586-024"],
    alpha=0.25,
    beta=0.15
)

# Grounded Synthesis
engine = GroundedSynthesisEngine(retriever=retriever)
synthesis = engine.synthesize("What are the empirical findings?", rq_id="RQ1")
```

---

## Verified surface, MCP mapping & knowledge

- **`nexus_rag_index` is declared unsupported** (capability `rag_indexing`, `mcp_supported: false`, owner `nexus-scholar-org/scholar-rag-kit`). The MCP server refuses it with a non-retryable `UNSUPPORTED_CAPABILITY` envelope before any file, manifest, or audit I/O; it is not a soft "not found" and not a parity claim. Use the `scholar-rag index` CLI or the `scholar_rag.index_service` Python API instead. That declaration does not narrow the query tools: `nexus_rag_query(query, db_path="./chroma_db", …, graph_source=None, alpha=0.25, beta=0.15)` (`server.py:876`) still defaults its store CWD-relative — always pass absolute workspace paths (e.g. `<ws>/chroma_db`). `nexus_matrix_extract` pins its db to `<workspace_dir>/chroma_db`, so align by indexing with an explicit `db_path=<ws>/chroma_db`.
- **MCP `nexus_rag_query` supports graph boosting**: the tool exposes `graph_source` plus `alpha` (default 0.25) and `beta` (default 0.15) alongside the single-`boost_doi` seed boost (`tools/scholar-agent-kit/src/scholar_agent/server.py:876`), matching the CLI (`--graph <graph.json> --alpha 0.25 --beta 0.15`) and `ScholarRetriever.query(…, graph_source=…)` (`Score = cos + α·PR + β·seed`).
- **`nexus_rag_synthesize`**: `rq_id` defaults to `"RQ1"` (pass explicitly); no seed-boost
  or LLM override. Deterministic bullet synthesis when no `llm_callable`.
- **`nexus_verify_claims` does not pair with `claims.json`**: RAG claims
  (`SynthesisClaim.__dict__`) carry `claim_text`/`citation_tokens`/`entailment_status`
  but **no `evidence_quote`/`claim_id`** — the verify tool expects those fields, so every
  claim returns `MISSING_QUOTE` and only aggregate metrics are returned. The two
  notions are unrelated (embedding similarity vs verbatim quote match).
- **Chunk ids are content-derived `CHK-` identities**: minted by `mint_chunk_id` (`tools/scholar-rag-kit/src/scholar_rag/chunker.py:121`) from content plus locator limbs — identity is content, not position; sections are `#`/`##`/`###` AST-split and `min_chunk_chars` folds micro-chunks (`chunker.py:530`).
  Citation tokens in synthesis render as `[<workspace_id|paper_id|doi|filename>#<sec10>#<chunk_id>]` (`retriever.py:123`). `entailment_score` / `VERIFIED` / `AMBIGUOUS` / `UNSUPPORTED` are kit-observed similarity vocabulary (embedding cosine, lexical fallback — `synthesis.py:112`): similarity is not entailment, and no synthesis claim verifies semantic entailment.
- **Embeddings**: default `all-MiniLM-L6-v2` (first use downloads from HuggingFace);
  hermetic `mock` provider for CI; OpenAI provider requires `OPENAI_API_KEY`. Provider is
  locked per store — re-index with a different provider into a fresh db.
- **Metadata tagging (paradigm/study_design) comes from the companion BibTeX only** —
  without `--bib`/`bib_file`, chunks lack it even if `project.json` exists.
- **Consensus verdicts are study-count based** (`ConsensusCartographer(threshold=0.30)`);
  for paraphrase-heavy corpora prefer `--similarity sentence-transformers --threshold 0.40`.
- **Audit events**: the kit's own run report appends `RAG_INDEX_RUN_BUILT` / `RAG_INDEX_RUN_REJECTED` to the explicit journal destination (`index_service.py:195`) — distinct from the harness continuity event, and never the §6.6 accepted-record event, which belongs to the future `index-acceptance-v1` adapter (MISSING `E3-NEG-037`/`E3-POS-008`). Legacy query/synthesis paths log `RAG_QUERY_RETRIEVED` / `SYNTHESIS_GENERATED`; `MATRIX_EXTRACTED` on matrix runs.
- **`scholar-protocol-kit` is a declared dependency** of the rag kit (`tools/scholar-rag-kit/pyproject.toml:33`, pinned git ref used by `matrix.py`) — it resolves from its pinned canonical commit, not from a bare PyPI name.
- **Status (E3 in progress, `docs/architecture/wp01_e3_adoption_status.md:30`)**: T-140 (`9931dce`) proves the harness-live rows including `E3-POS-005` golden parity plus a real-Chroma diagnostic whose healthy-path `SUCCESS` leaves the historical `ATOMIC_COMMIT_FAILED` concern UNSUBSTANTIATED on that path/env; 14 ledger rows stay honestly `MISSING` upstream of adapter/parity work — kit-owned `E3-NEG-009/011`, `017`, `021/022`, `030/031`, `035`, `050`, plus publish-time `039`, adapter-future `037`/`POS-008` (§6.6/`index-acceptance-v1`), MCP-parity `POS-009`, and CI-wheel `POS-012`.
- **Versions**: the shipped kit package is `0.1.0` (`tools/scholar-rag-kit/pyproject.toml:7`); golden `producer.version 0.2.0` is the producing-kit version stamped inside the frozen golden manifest bytes (`tests/conformance/fixtures/e3_golden_manifest.json`), not the installed package version.
