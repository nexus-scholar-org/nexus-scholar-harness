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
7. **Append-Only Audit Journal**: Logs `RAG_INDEX_BUILT`, `RAG_QUERY_RETRIEVED`, and `SYNTHESIS_GENERATED` events to `audit/journal.jsonl`.

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

---

## Python API

```python
from scholar_rag import MarkdownChunker, ScholarIndexer, ScholarRetriever, GroundedSynthesisEngine

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
