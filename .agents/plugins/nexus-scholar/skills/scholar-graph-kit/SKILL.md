---
name: scholar-graph-kit
description: Instructions for using the scholar-graph-kit Python API and CLI to construct citation knowledge networks, compute normalized PageRank scores, and render interactive PyVis HTML graphs.
---

# `scholar-graph-kit` Skill Instructions

You are the citation network analysis and bibliometric graph specialist of the Nexus Scholar Suite. Your role is to construct directed citation networks from Open Access DOIs using OpenAlex, compute normalized **PageRank** importance metrics to boost downstream semantic RAG retrieval, and generate interactive force-directed HTML network maps.

> Verified against pinned `scholar-graph-kit` `646b84cec215ebd9b7b449448bca879492e78492` (`plugins.json` `default_rev`) and `docs/kits_surface_matrix.md` graph rows + finding 2 (RESOLVED real client). See that matrix for the full API↔CLI↔MCP map; this file is the operational subset.

## Routing — choose the surface first

| Task | Use |
| :--- | :--- |
| Build graph + visualize from screening/DOIs, persists `graph.html` + `graph.json` | CLI `uv run scholar-graph build …` / `pagerank` |
| Hermetic join / import in Python | `scholar_graph.builder.CitationGraphBuilder` + `visualizer.GraphVisualizer` with a real `AcademicHttpClient` |
| Agent front-door (no shell) | MCP `nexus_graph_build` (real client) / `nexus_graph_narrative` (`synthesis/visual_synthesis.md`) |
| Full map, failure modes, cross-kit contracts | `docs/kits_surface_matrix.md` graph section + finding 2 |

> **Scope check (verified):** this kit builds **citation** edges only. There is **no
> co-citation logic**, no TF-based edge weighting (RAG does that), and
> `config.Settings` / `models.GraphNode` / `GraphEdge` are **dead** (present but
> never imported by the builder/CLI/visualizer). OpenAlex is the only source and
> no polite-pool mailto is sent.

## Core Capabilities

1. **OpenAlex Citation Graph Builder**: Asynchronously resolves citation references across study pools (`included.json` or explicit `--doi` lists).
2. **PageRank Score Computation**: Computes normalized PageRank vectors across the literature subgraph:
   $$\text{PageRank}(u) = \frac{1 - d}{N} + d \sum_{v \in B_u} \frac{\text{PageRank}(v)}{L(v)}$$
3. **Graph Topology & Node-Link JSON Export**: Exports standard network structures (`graph.json`) for downstream RAG weighting in `scholar-rag-kit`.
4. **Interactive PyVis HTML Visualization**: Generates interactive HTML network maps (`graph.html`) with customizable physics and node metadata tooltips (hybrid local bindings + CDN — not offline).

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

> **Sidecar:** `build` always writes JSON — `--json-output <path>` when given, else `<output-stem>.json` beside the HTML (e.g. `knowledge_graph.json`). `pagerank <graph.json>` needs that file's top-level `"pagerank"` key.

---

## Python API

```python
import asyncio
from scholar_graph.builder import CitationGraphBuilder
from scholar_graph.visualizer import GraphVisualizer
from scholar_search.http_client import AcademicHttpClient

async def main():
    http_client = AcademicHttpClient(name="openalex-graph", rate_limit=10)
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

---

## Verified surface, MCP mapping & knowledge

- **`http_client` is mandatory** in `CitationGraphBuilder(http_client)` (API-pinned,
  `builder.py:13`); there is no default client. Pass
  `scholar_search.http_client.AcademicHttpClient`. `fetch_work_data` swallows
  failures to `None` (`builder.py:16-27`); `build_graph` raises nothing.
- **MCP `nexus_graph_build` uses a real client (finding 2 RESOLVED):** it builds
  `AcademicHttpClient(name="openalex-graph", rate_limit=10)` exactly like the CLI
  (`server.py:1009-1011`), so it produces real edges — not the old 0-edge
  `http_client=None` fallback. Uniform PageRank `1.0` with `0 edges` is the
  **failure fallback** (`compute_pagerank` except-branch, `builder.py:123-124`),
  never a success signal; on `0 edges` check DOIs/client before trusting ranks.
- **DOI precedence + empty-input error:** both CLI (`cli.py:77-81`) and MCP
  (`server.py:1019`) prefer `external_ids.doi` then `doi`. MCP also accepts
  `{"results"|"items": [...]}` dict payloads and returns
  `Error: No DOIs found in <input>` on empty input (`server.py:1016-1024`); CLI
  with no DOIs prints `No DOIs provided` and exits `0` (`cli.py:89-91`).
- **MCP `nexus_graph_narrative`** (`server.py:1559`) reads a build-produced
  `graph.json` (node-link + `pagerank`/`group`), ranks hubs by PageRank and groups
  by `group`, and writes `<ws>/synthesis/visual_synthesis.md` (hub table + thematic
  communities).
- **CLI build renders HTML before exporting JSON** (`cli.py:150-164`) — the JSON
  written by the CLI (including the sidecar `<stem>.json` when `--json-output` is
  omitted) carries PyVis node attributes (`value`/`title`) mutated during rendering.
  For a minimal node-link graph, use `builder.export_json` directly.
- **`pagerank <graph.json>` reads the top-level `"pagerank"` key** (`cli.py:193`) —
  feed it a build-produced graph.json, not an arbitrary node-link JSON.
- **Intra-pool edges only** (`builder.py:83-86`): source → referenced work that is
  itself *in the pool* (wid→doi resolution); no external nodes. Fallback nodes get
  `year=None`, `title="Study <doi>"` (`builder.py:96-105`).
- **PageRank** (`compute_pagerank(alpha=0.85)`, `builder.py:110-124`) is normalized
  to max `1.0` at 4 decimals, keys lowercased. RAG's hybrid blend (α=`0.25`/β=`0.15`)
  is separate from the computation α=`0.85`.
- **HTML is hybrid (local PyVis bindings + CDN vis.js)** — not standalone-offline; the
  vendored `lib/` (pyvis `0.3.2`) materializes in the run CWD. Unbounded per-DOI
  concurrency; OpenAlex only.
