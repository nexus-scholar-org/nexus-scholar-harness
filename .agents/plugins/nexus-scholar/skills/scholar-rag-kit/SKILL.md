---
name: scholar-rag-kit
description: Instructions for using scholar-rag-kit Python API and CLI for structural AST chunking, methodology tagging, hybrid graph-boosted retrieval, and grounded synthesis over scientific literature.
---

# `scholar-rag-kit` Skill Instructions

You are the scientific retrieval-augmented generation and synthesis specialist of the Nexus Scholar Suite. Your role is to index extracted literature corpora using **structural AST sectional chunking**, execute **hybrid graph-boosted semantic retrieval** (combining dense vector search with citation network PageRank), and generate **grounded research synthesis** with atomic claim-level attribution tokens.

## Core Capabilities

1. **Structural AST Chunking**: Splits papers along header hierarchies (`#`, `##`, `###`) to preserve section context (`Abstract`, `Methodology`, `Results`, `Limitations`), maintains hierarchy breadcrumbs, and enforces size guards.
2. **Methodology Metadata Tagging**: Enriches chunks with paradigm, study design, sample size, evaluation metrics, dataset, and DOI from companion `references.bib` and `project.json`.
3. **Idempotent Vector Store**: Assigns deterministic IDs (`chk-<doc_id>-<sec_slug>-<idx:02d>`) and uses `collection.upsert()` for idempotent re-indexing.
4. **Hybrid Graph-Boosted Retrieval**:
   $$\text{Score}(d) = \text{CosineSim}(q, d) + \alpha \cdot \text{PageRank}(d) + \beta \cdot \mathbb{I}_{\text{seed}}(d)$$
5. **Grounded Attributed Synthesis**: Generates research reviews with atomic citation tokens `[WORKSPACE_ID#SECTION#CHUNK_ID]` and verifies semantic claim entailment.
6. **Cross-Study Methodology Matrix**: Extracts 7-dimension comparative matrices (`matrix.json` and `matrix.md`).
7. **Consensus Cartographer**: Clusters attributed synthesis claims into high-consensus findings vs. active debates with deterministic stance attribution and verdicts (`consensus.json`/`consensus.md`).
8. **Append-Only Audit Journal**: Logs `RAG_INDEX_BUILT`, `RAG_QUERY_RETRIEVED`, and `SYNTHESIS_GENERATED` events to `audit/journal.jsonl`.

---

## CLI Usage

### 1. Index Extracted Literature
```bash
uv run scholar-rag index workspaces/<project-slug>/extracted/ \
  --bib workspaces/<project-slug>/literature/references.bib \
  --workspace-id <project-slug>
```

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

## Python API

```python
from scholar_rag import (
    MarkdownChunker, ScholarIndexer, ScholarRetriever, GroundedSynthesisEngine,
    ConsensusCartographer, embedder_claim_scorer, get_embedder,
)

# Initialize Indexer
indexer = ScholarIndexer(db_path="./chroma_db", embedder_kwargs={"provider": "sentence-transformers"})
indexer.index_directory("workspaces/<project-slug>/extracted/", bib_file="workspaces/<project-slug>/literature/references.bib")

# Retrieve with Hybrid Graph Boost
retriever = ScholarRetriever(db_path="./chroma_db")
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

- **MCP tool defaults are CWD-relative**: `nexus_rag_index(docs_dir, db_path="./chroma_db")`
  and `nexus_rag_query(db_path="./chroma_db")` resolve against `tools/scholar-agent-kit/`
  when launched through MCP — always pass absolute workspace paths
  (e.g. `<ws>/chroma_db`). `nexus_matrix_extract` pins its db to
  `<workspace_dir>/chroma_db`, so align by indexing with an explicit
  `db_path=<ws>/chroma_db`.
- **MCP `nexus_rag_query` cannot graph-boost**: the tool exposes only `boost_doi`
  (seed boost, β=0.15); there is no `graph_source`/`alpha`/`beta` parameter. Full hybrid
  retrieval (`Score = cos + α·PR + β·seed`) requires the CLI (`--graph <graph.json>
  --alpha 0.25 --beta 0.15`) or the Python `ScholarRetriever.query(…, graph_source=…)`.
- **`nexus_rag_synthesize`**: `rq_id` defaults to `"RQ1"` (pass explicitly); no seed-boost
  or LLM override. Deterministic bullet synthesis when no `llm_callable`.
- **`nexus_verify_claims` does not pair with `claims.json`**: RAG claims
  (`SynthesisClaim.__dict__`) carry `claim_text`/`citation_tokens`/`entailment_status`
  but **no `evidence_quote`/`claim_id`** — the verify tool expects those fields, so every
  claim returns `MISSING_QUOTE` and only aggregate metrics are returned. The two
  "verification" notions are unrelated (embedding entailment vs verbatim quote match).
- **Chunk ids**: `chk-<doc-slug>-<sec-slug>-<NN>`; sections are `#`/`##`/`###` AST-split.
  Citation tokens in synthesis render as `[<workspace_id|doi|filename>#<sec10>#<chunk_id>]`.
- **Embeddings**: default `all-MiniLM-L6-v2` (first use downloads from HuggingFace);
  hermetic `mock` provider for CI; OpenAI provider requires `OPENAI_API_KEY`. Provider is
  locked per store — re-index with a different provider into a fresh db.
- **Metadata tagging (paradigm/study_design) comes from the companion BibTeX only** —
  without `--bib`/`bib_file`, chunks lack it even if `project.json` exists.
- **Consensus verdicts are study-count based** (`ConsensusCartographer(threshold=0.30)`);
  for paraphrase-heavy corpora prefer `--similarity sentence-transformers --threshold 0.40`.
- **Audit events**: `RAG_INDEX_BUILT`, `RAG_QUERY_RETRIEVED`, `SYNTHESIS_GENERATED`,
  `MATRIX_EXTRACTED`.
- **`scholar-protocol-kit` is imported but an undeclared dependency** — it resolves only
  because the shared venv installs all kits.
