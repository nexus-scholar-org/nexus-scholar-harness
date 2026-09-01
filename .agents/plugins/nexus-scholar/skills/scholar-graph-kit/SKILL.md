---
name: scholar-graph-kit
description: Instructions for using the scholar-graph-kit Python API and CLI to construct citation and co-citation knowledge networks, compute normalized PageRank scores, and render interactive PyVis HTML graphs.
---

# `scholar-graph-kit` Skill Instructions

You are the citation network analysis and bibliometric graph specialist of the Nexus Scholar Suite. Your role is to construct directed citation and co-citation networks from Open Access DOIs using OpenAlex, compute normalized **PageRank** importance metrics to boost downstream semantic RAG retrieval, and generate interactive force-directed HTML network maps.

## Core Capabilities

1. **OpenAlex Citation Graph Builder**: Asynchronously resolves citation references across study pools (`included.json` or explicit `--doi` lists).
2. **PageRank Score Computation**: Computes normalized PageRank vectors across the literature subgraph:
   $$\text{PageRank}(u) = \frac{1 - d}{N} + d \sum_{v \in B_u} \frac{\text{PageRank}(v)}{L(v)}$$
3. **Graph Topology & Node-Link JSON Export**: Exports standard network structures (`graph.json`) for downstream RAG weighting in `scholar-rag-kit`.
4. **Interactive PyVis HTML Visualization**: Generates standalone HTML network maps (`graph.html`) with customizable physics and node metadata tooltips.

---

## CLI Usage

### 1. Build Citation Graph from Screening Results
```bash
# Build network and export both interactive HTML visualization and PageRank JSON
uv run scholar-graph build \
  --input workspaces/<project-slug>/literature/included.json \
  --output workspaces/<project-slug>/literature/knowledge_graph.html \
  --json-output workspaces/<project-slug>/literature/knowledge_graph.json
```

### 2. Build Graph from Specific DOIs
```bash
uv run scholar-graph build \
  --doi 10.1038/s41586-024-0001 \
  --doi 10.1038/s41586-024-0002 \
  --output graph.html
```

### 3. Inspect PageRank Rankings
```bash
uv run scholar-graph pagerank workspaces/<project-slug>/literature/knowledge_graph.json
```

---

## Python API

```python
import asyncio
from scholar_graph.builder import CitationGraphBuilder
from scholar_graph.visualizer import GraphVisualizer
from scholar_search.http_client import AcademicHttpClient

async def main():
    http_client = AcademicHttpClient(name="openalex-graph")
    builder = CitationGraphBuilder(http_client)
    
    # 1. Build directed citation graph
    G = await builder.build_graph(["10.1038/s41586-024-0001", "10.1038/s41586-024-0002"])
    
    # 2. Compute PageRank
    pr = CitationGraphBuilder.compute_pagerank(G)
    
    # 3. Export Node-Link JSON & PyVis HTML
    builder.export_json(G, "knowledge_graph.json")
    vis = GraphVisualizer("knowledge_graph.html")
    vis.generate_html(G)

asyncio.run(main())
```
