# Scholar Graph Kit — Comprehensive Deep-Dive Analysis

**Kit Path:** C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-graph-kit
**Entry Point:** scholar_graph.cli:app (console script scholar-graph)
**Version:** 0.1.0
**Dependencies:** networkx>=3.0, pyvis>=0.3.2, typer>=0.9.0, rich>=13.0.0, aiohttp>=3.9.0, pydantic>=2.0.0, scholar-search-kit

---

## Table of Contents

1. Executive Summary
2. Dimension 1: Functionalities
3. Dimension 2: Improvements
4. Dimension 3: Problems
5. Dimension 4: Optimizations
6. Dimension 5: Scientific Correction
7. Dimension 6: Agent/Skill Recommendation
8. Priority-Ranked Improvement Suggestions

---

## 1. Executive Summary

The scholar-graph-kit is a **minimal but functional** bibliometric graph construction and visualization engine. It has exactly **four source files** (excluding __init__.py):

| File | Lines | Role |
|------|-------|------|
| models.py | 14 | Dataclasses (GraphNode, GraphEdge) — **DEAD CODE** |
| config.py | 9 | Pydantic Settings — **DEAD CODE** |
| uilder.py | 130 | Core: CitationGraphBuilder (fetch, build, PageRank, export) |
| isualizer.py | 59 | GraphVisualizer (PyVis HTML generation) |
| cli.py | 125 | Typer CLI (build, pagerank commands) |

**Strengths:**
- Clean async OpenAlex integration via AcademicHttpClient
- NetworkX DiGraph backbone with standard node-link JSON export
- PyVis interactive HTML with physics-based layout
- PageRank normalization to [0, 1] at 4 decimal places
- Orchestrator integration as Stage 8 of the full pipeline

**Critical Weaknesses:**
- ~50% of the kit is dead code (models.py, config.py)
- Documentation (tutorial.md, api_reference.md) describes classes that do NOT exist (GraphBuilder, NetworkAnalyzer, GraphData, NodeMetadata)
- Only citation edges — no co-citation, bibliographic coupling, or scientometric analysis
- Only one export format (PyVis HTML) — no GEXF, GraphML, or Cytoscape JSON
- All error handling is silent (except Exception: pass)
- No CLI command for analyzing graph structure, communities, or centrality

---

## 2. Dimension 1: Functionalities

### 2.1 Complete Feature Inventory

| # | Feature | Status | Location |
|---|---------|--------|----------|
| 1 | Fetch work metadata from OpenAlex API | Implemented | builder.py:15-26 |
| 2 | Build directed citation graph from DOIs | Implemented | builder.py:28-100 |
| 3 | Parse included.json for DOIs | Implemented | cli.py:40-52 |
| 4 | Compute normalized PageRank | Implemented | builder.py:102-114 |
| 5 | Export node-link JSON + PageRank | Implemented | builder.py:116-130 |
| 6 | PyVis HTML visualization | Implemented | visualizer.py:13-59 |
| 7 | CLI build command | Implemented | cli.py:29-91 |
| 8 | CLI pagerank command | Implemented | cli.py:94-121 |
| 9 | Fallback nodes for unindexed DOIs | Implemented | builder.py:85-98 |
| 10 | Co-citation analysis | NOT IMPLEMENTED | — |
| 11 | Bibliographic coupling | NOT IMPLEMENTED | — |
| 12 | HITS (Hubs and Authorities) | NOT IMPLEMENTED | — |
| 13 | Louvain community detection | NOT IMPLEMENTED | — |
| 14 | K-core decomposition | NOT IMPLEMENTED | — |
| 15 | GEXF export | NOT IMPLEMENTED | — |
| 16 | GraphML export | NOT IMPLEMENTED | — |
| 17 | Cytoscape JSON export | NOT IMPLEMENTED | — |
| 18 | Temporal citation dynamics | NOT IMPLEMENTED | — |
| 19 | Edge weighting / TF-based scoring | NOT IMPLEMENTED | — |
| 20 | CLI export command | NOT IMPLEMENTED | — |
| 21 | CLI analyze command | NOT IMPLEMENTED | — |
| 22 | CLI cluster command | NOT IMPLEMENTED | — |

### 2.2 CLI Commands to Functions Mapping

scholar-graph build -> cli.py:build() -> CitationGraphBuilder.build_graph() -> GraphVisualizer.generate_html() -> CitationGraphBuilder.export_json()

scholar-graph pagerank <graph_file> -> cli.py:pagerank() -> reads JSON "pagerank" key -> Rich table display

### 2.3 Data Models and Schemas

**Defined but unused** (models.py:3-14):

GraphNode dataclass with doi, title, year, citations, group fields.
GraphEdge dataclass with source, target fields.

**Actual in-use schema** (NetworkX node attributes in builder.py:63-70):

Per-node dict stored on nx.DiGraph with: doi_clean (node ID), title (work title), year (publication year), citations (cited_by_count), group (cluster coloring, always 1), label (truncated title, 30 chars for PyVis).

**Export schema** (builder.py:126-129):

JSON with nodes (node_link_data format), links (directed edges), directed (true), pagerank (normalized to max 1.0).

**Config schema** (config.py:3-8):

Settings with openalex_email (NOT USED, no polite-pool) and max_concurrent_requests (NOT USED, unbounded).

### 2.4 Integration Points with Other Kits

| Integration | Direction | Location | Status |
|-------------|-----------|----------|--------|
| scholar-search-kit (AcademicHttpClient) | inbound | builder.py:9,12, cli.py:64 | Working |
| scholar-search-kit (included.json) | inbound | cli.py:40-52 | Working |
| scholar-rag-kit (graph.json pagerank) | outbound | builder.py:127 | Working |
| scholar-agent-kit (MCP nexus_graph_build) | inbound | server.py:535-571 | Was broken, now fixed |
| scholar-harness orchestrator (Stage 8) | inbound | orchestrator.py:648-662 | Working |

---

## 3. Dimension 2: Improvements

### 3.1 Code Quality Issues

#### 3.1.1 Dead Code — models.py (14 lines entirely dead)

**File:** src/scholar_graph/models.py:1-14

The GraphNode and GraphEdge dataclasses are never imported by any module in the kit. The actual graph nodes are plain dicts on nx.DiGraph. This file exists only as historical residue.

**Impact:** Misleading; new contributors will import GraphNode thinking it is the canonical model.

**Recommendation:** Delete the file entirely, or replace with a Pydantic model that matches the actual NetworkX node dict.

#### 3.1.2 Dead Code — config.py (9 lines entirely dead)

**File:** src/scholar_graph/config.py:1-9

Settings is instantiated as module-level settings = Settings() but never referenced by builder.py, visualizer.py, or cli.py. The openalex_email setting (intended for polite-pool) is never sent in API requests. max_concurrent_requests is ignored — builder.py uses asyncio.as_completed with no semaphore.

**Impact:** Wasted dependency on pydantic-settings; unbounded concurrency may hit OpenAlex rate limits.

#### 3.1.3 Silent Exception Swallowing

**File:** src/scholar_graph/builder.py:24-25

Every OpenAlex fetch failure is silently consumed. A network error, a 429 rate-limit, or a malformed JSON response all produce the same result: the DOI vanishes from the graph with zero diagnostic output.

**File:** src/scholar_graph/cli.py:19

Windows UTF-8 reconfiguration failures are silently ignored (acceptable for Windows compat, but should log a warning).

#### 3.1.4 CLI Mutates Graph Node Attributes During Render

**File:** src/scholar_graph/cli.py:68-81

The build command calls vis.generate_html(G) which mutates G.nodes[data] by adding value (for sizing) and title (for tooltips) — see visualizer.py:19-22. Then builder.export_json(G, ...) serializes the mutated graph. This means the exported JSON contains PyVis-specific attributes (value, title) that pollute the pure node-link structure.

**Documented in SKILL.md:** "CLI build renders HTML before exporting JSON — the JSON written by the CLI carries PyVis node attributes."

#### 3.1.5 Tutorial and API Reference Are Stale

**File:** docs/tutorial.md:9-45

References scholar-bib build --doi (wrong CLI name), GraphBuilder, NetworkAnalyzer, export_html() — none of which exist in the current code.

**File:** docs/api_reference.md:1-44

References GraphBuilder(provider="openalex"), NetworkAnalyzer, GraphData, NodeMetadata — classes that do NOT exist. Describes calculate_centrality() which does not exist.

### 3.2 Missing Features

1. No graph export beyond HTML — no GEXF, GraphML, or Cytoscape JSON (planned in Ecosystem Analysis Phase A)
2. No scientometric modes — no co-citation, bibliographic coupling, or hybrid similarity (planned in Phase B)
3. No network analysis CLI — no analyze, cluster, or export commands
4. No progress reporting — progress_callback in build_graph is called but never actually reports (the callback in cli.py:69-70 is a no-op pass)
5. No caching — repeated builds re-fetch all DOIs from OpenAlex
6. No rate limiting — no asyncio.Semaphore despite config.max_concurrent_requests
7. No polite-pool email — OpenAlex recommends sending mailto for higher rate limits

### 3.3 API Design Improvements

1. CitationGraphBuilder requires AcademicHttpClient but has no default — the MCP tool previously passed None. A factory method or optional default would prevent this.
2. compute_pagerank is a @staticmethod that takes G as an argument but is always called as CitationGraphBuilder.compute_pagerank(G) after build_graph. It should be an instance method or called automatically.
3. export_json is a @staticmethod but is called as builder.export_json(...) — inconsistent with the static decorator.
4. No __all__ export in __init__.py — the public API is not explicitly declared.

### 3.4 Error Handling Gaps

1. No validation of DOI format — malformed DOIs silently produce no graph nodes
2. No timeout on OpenAlex requests — a hanging connection blocks the entire build
3. No retry on transient failures — 429/503 responses are silently swallowed
4. No graph size limits — a 10,000-DOI list would fire 10,000 concurrent HTTP requests
5. pagerank command silently returns empty table if file has no "pagerank" key — no error
6. build_graph does not validate that returned referenced_works are valid OpenAlex work IDs

### 3.5 Documentation Needs

| Document | Issue | Severity |
|----------|-------|----------|
| docs/tutorial.md | References nonexistent GraphBuilder, NetworkAnalyzer, scholar-bib build | Critical |
| docs/api_reference.md | References nonexistent GraphBuilder, NetworkAnalyzer, GraphData, NodeMetadata | Critical |
| README.md | Mostly accurate but says "Co-Citation" in description (not implemented) | Medium |
| SKILL.md | Accurate and well-maintained | OK |
| Inline docstrings | build_graph, compute_pagerank, export_json have minimal docstrings | Low |

---

## 4. Dimension 3: Problems

### 4.1 Known Bugs and Issues

#### Bug 1: MCP nexus_graph_build Was Broken (Now Fixed)

Historical: The MCP tool previously constructed CitationGraphBuilder(http_client=None), causing every OpenAlex fetch to fail silently, producing a graph of isolated fallback nodes with uniform PageRank 1.0.

Status: Fixed in server.py:548 — now creates AcademicHttpClient(name="openalex-graph", rate_limit=10).

#### Bug 2: Unbounded Concurrency

**File:** builder.py:36-40

All DOIs are fetched concurrently with no semaphore. For 500 DOIs, this fires 500 simultaneous HTTP requests. OpenAlex rate limits are ~10 requests/second for polite pool, ~1/second without email. This WILL trigger 429s.

#### Bug 3: PageRank Error Falls Back to Uniform 1.0

**File:** builder.py:113-114

If nx.pagerank fails (e.g., on an empty graph or a graph with only self-loops), all nodes get identical PageRank 1.0 — making the metric meaningless. The error is silently swallowed.

#### Bug 4: DOI Cleaning Does Not Handle All Cases

**File:** builder.py:55

Does not handle doi: prefix, uppercase DOI, or URLs with path fragments. Only handles the two https://doi.org/ and http://doi.org/ prefixes.

#### Bug 5: Edge Direction May Be Counterintuitive

**File:** builder.py:79-83

Edge is source -> target where source is the citing paper and target is the cited paper. This means edges point FROM the newer paper TO the older paper it cites. While technically correct for a citation graph, this is counterintuitive for PageRank (the cited paper receives the rank, but edges point away from it). NetworkX pagerank on a DiGraph treats incoming edges as "votes for" — so the cited paper gets rank from being pointed AT. This is correct.

#### Bug 6: group Field Always 1

**File:** builder.py:68 and builder.py:96

The group attribute is always hardcoded to 1. No clustering or community detection is performed. The PyVis visualization uses this for coloring, so all nodes have the same color.

### 4.2 Edge Cases Not Handled

1. Empty input list — build_graph([]) returns an empty graph (correct but no warning)
2. All DOIs fail to resolve — returns graph with only fallback nodes, no edges
3. Self-citing papers — filtered by source_doi != target_doi check (correct)
4. Duplicate DOIs in input — deduplicated by list if doi not in doi_list in CLI, but build_graph does not deduplicate
5. DOIs with trailing slashes or fragments — not cleaned
6. Very large graphs — PyVis HTML can become very large (500+ nodes); no pagination or filtering
7. Graph with zero edges — PageRank returns all 1.0; the pagerank CLI shows this without warning

### 4.3 Limitations in Current Implementation

1. Intra-pool edges only — only edges between papers that are BOTH in the input DOI list. No expansion to referenced works outside the pool. This means the graph is sparse for small input sets.
2. No edge weighting — all citation edges are binary (present/absent). No weighting by co-citation strength, bibliographic coupling overlap, or recency.
3. Single data source — OpenAlex only. No Semantic Scholar, Crossref, or PubMed citation data.
4. No incremental builds — cannot add new DOIs to an existing graph; must rebuild from scratch.
5. No graph persistence — the graph exists only in memory; must export to JSON for reuse.

### 4.4 Technical Debt

1. Dead files (models.py, config.py) should be removed
2. Stale documentation (tutorial.md, api_reference.md) should be rewritten
3. pydantic-settings dependency is unnecessary if config.py is removed
4. No type hints on export_json return — returns Path but signature says str | Path
5. compute_pagerank normalization divides by max(pr.values()) — this means the most central node always gets 1.0, which is fine for relative ranking but loses absolute scale information

---

## 5. Dimension 4: Optimizations

### 5.1 Performance Bottlenecks

#### Bottleneck 1: Unbounded HTTP Concurrency

**File:** builder.py:36-40

Impact: For N DOIs, fires N concurrent requests. OpenAlex will 429 after ~10 requests without polite pool.

Fix: Add asyncio.Semaphore(settings.max_concurrent_requests):

    sem = asyncio.Semaphore(settings.max_concurrent_requests)
    async def limited_fetch(doi):
        async with sem:
            return await self.fetch_work_data(doi)
    tasks = [limited_fetch(doi) for doi in dois]

#### Bottleneck 2: Sequential Edge Resolution

**File:** builder.py:72-83

Edges are added in a Python for loop over works_data. For large graphs (1000+ nodes), this is O(N*R) where R is average references per work. NetworkX add_edge is O(1) amortized, so this is fine for typical systematic review sizes (<500 papers).

#### Bottleneck 3: PyVis HTML Rendering for Large Graphs

**File:** visualizer.py:13-59

PyVis generates a self-contained HTML file with inline JavaScript. For 1000+ nodes, the HTML file can exceed 10MB. No options for: Node filtering, Lazy loading, Subgraph extraction, Static image export.

### 5.2 Memory Usage Issues

**File:** builder.py:28-100

build_graph keeps ALL works_data (raw OpenAlex JSON) in memory alongside the NetworkX graph. For 500 papers, each with full OpenAlex metadata, this could be 50-100MB of raw JSON plus the graph structure.

**Recommendation:** Process and discard raw data incrementally.

### 5.3 Caching Opportunities

1. DOI metadata caching — OpenAlex work metadata changes rarely. Cache by OpenAlex work ID with TTL.
2. Graph JSON caching — if input DOIs have not changed, skip rebuild entirely.
3. PageRank caching — recompute only if graph structure changed.

### 5.4 Parallelization Potential

1. Edge resolution — the current asyncio.as_completed is good for I/O-bound fetching but edge construction is CPU-bound for large graphs. Could use concurrent.futures.ProcessPoolExecutor for graph construction.
2. PageRank — NetworkX pagerank is single-threaded. For very large graphs, use scipy.sparse implementation.

---

## 6. Dimension 5: Scientific Correction

### 6.1 PageRank Implementation Accuracy

**File:** builder.py:103-114

**Assessment:**

- The alpha=0.85 damping factor is the standard PageRank default (Brin and Page, 1998). **Correct.**
- Normalization by max(pr.values()) scales to [0, 1]. This is a valid normalization but loses absolute scale. For academic use, relative ranking is typically sufficient. **Acceptable.**
- Keys are lowercased (k.lower()). DOIs are case-insensitive, so this is correct for DOI-keyed graphs. **Correct.**
- Rounding to 4 decimal places provides sufficient precision for ranking. **Correct.**

**Potential Issue:** If the graph is disconnected (multiple weakly connected components), PageRank distributes rank proportional to component size. Small components get less total rank. This is standard behavior but may surprise users.

### 6.2 Citation Network Analysis

**Edge Direction:** source -> target where source cites target. In a citation graph, this means:

- pagerank assigns higher rank to papers that are cited by many high-rank papers
- This correctly identifies influential papers in the citation network
- This is standard academic practice.

**Limitation:** Only direct citation edges are captured. No:

- Co-citation similarity (papers cited together)
- Bibliographic coupling (papers sharing references)
- Bibliometric coupling strength

### 6.3 Academic Impact Metrics

The kit currently provides:

1. PageRank — measures structural importance in the citation network
2. Citation count (cited_by_count from OpenAlex) — raw impact measure

**Missing metrics that would be valuable:**

1. HITS Hubs/Authorities — distinguishes review papers (hubs) from empirical breakthroughs (authorities)
2. Betweenness centrality — identifies papers bridging sub-disciplines
3. In-degree / Out-degree — basic citation metrics
4. h-index of cited papers — aggregate impact of references
5. Citation velocity — citations per year (emerging vs. declining)
6. Co-citation clustering — thematic groupings

### 6.4 Visualization Accuracy

**File:** visualizer.py:19-22

**Assessment:**

- Node size is proportional to citation count + 5 (base). This means a paper with 0 citations still has visible size. **Reasonable.**
- No PageRank-based sizing — the most structurally important paper may not be the most visually prominent. **Missed opportunity.**
- Tooltip shows DOI, title, year, and citations. **Good.**
- No color coding by year, community, or any metric. **Missing.**

**Physics layout** (visualizer.py:29-55):

- Uses forceAtlas2Based solver with reasonable parameters
- gravitationalConstant: -50 (moderate repulsion)
- springLength: 100, springConstant: 0.08 (moderate attraction)
- Assessment: Reasonable defaults for academic citation networks. No major issues.

---

## 7. Dimension 6: Agent/Skill Recommendation

### 7.1 Should a Specialized Agent or Skill Be Created?

**Current SKILL.md exists** at .agents/skills/scholar-graph-kit/SKILL.md (100 lines). It is well-maintained and accurate.

**Recommendation: YES, a dedicated skill should be expanded, but a full agent is NOT warranted.**

**Rationale:**

| Factor | Assessment |
|--------|------------|
| Task scope | Narrow (graph build + visualize + PageRank) |
| Task frequency | Low (typically once per systematic review) |
| Agent-in-the-loop potential | LOW — the graph build is fully automated |
| Evaluation metrics needed | YES — graph quality metrics would be valuable |
| Critic capabilities | MODERATE — could validate graph structure |
| Automation potential | HIGH — currently automated in orchestrator Stage 8 |

### 7.2 Evaluation Metrics for Agent Assessment

An agent evaluating scholar-graph-kit output should check:

| Metric | Definition | Threshold | Location to Check |
|--------|-----------|-----------|-------------------|
| graph.node_count | Number of nodes in graph | > 0 | G.number_of_nodes() |
| graph.edge_count | Number of edges in graph | > 0 (if >1 DOI) | G.number_of_edges() |
| graph.density | Edges / (N*(N-1)) | Varies | nx.density(G) |
| graph.weakly_connected | Single connected component? | Preferred | nx.is_weakly_connected(G) |
| graph.pagerank_range | Min to max PageRank | [0, 1] | min/max of pr values |
| graph.pagerank_unique | All scores unique? | Yes | len(set(pr.values())) == len(pr) |
| graph.has_fallback_nodes | Nodes with title="Study <doi>" | Count | Check node titles |
| graph.doi_coverage | Input DOIs present in graph | 100% | Check all input DOIs as nodes |
| html.file_size | Size of generated HTML | < 10MB | Path(html).stat().st_size |
| html.contains_nodes | HTML has node data | True | Parse HTML content |
| json.has_pagerank | JSON export has "pagerank" key | True | Check JSON structure |

### 7.3 Critic Capabilities Needed

An agent critic for scholar-graph-kit should:

1. Validate input quality — check that DOIs are well-formed, included.json has the expected schema
2. Validate output structure — verify graph JSON has nodes, links, and pagerank keys
3. Flag sparse graphs — if edges/nodes < 0.5, warn that the graph may not be informative
4. Detect fallback nodes — count nodes with title="Study <doi>" and report what fraction of input DOIs were unresolvable
5. Check PageRank sanity — verify that the most-cited paper has high PageRank (if not, investigate graph structure)
6. Compare across runs — if the same DOIs are built twice, the graph should be deterministic

### 7.4 Agent-in-the-Loop Opportunities

The current scholar-graph-kit is fully automated — no agent-in-the-loop is needed for the core workflow. However, the following agent interactions could be valuable:

1. Graph interpretation agent — after graph build, an agent could analyze the structure and explain which papers are most central and why
2. Community detection agent — an agent could run Louvain clustering and explain the thematic groups
3. Anomaly detection agent — an agent could flag unusual citation patterns (e.g., a paper citing a much newer paper, which suggests data issues)

### 7.5 Automation Potential

| Workflow Step | Current | Automated? | Agent Needed? |
|---------------|---------|-----------|---------------|
| DOI list from included.json | CLI --input | Yes | No |
| OpenAlex metadata fetch | build_graph | Yes | No |
| Graph construction | build_graph | Yes | No |
| PageRank computation | compute_pagerank | Yes | No |
| JSON export | export_json | Yes | No |
| HTML visualization | generate_html | Yes | No |
| Graph quality validation | None | No | Yes |
| Graph interpretation | None | No | Yes |
| Community analysis | None | No | Yes |

---

## 8. Priority-Ranked Improvement Suggestions

### Priority 1 (Critical — Fix Now)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 1.1 | Delete dead code (models.py, config.py) | Reduces confusion | 5 min | models.py, config.py |
| 1.2 | Add asyncio.Semaphore to bound concurrency | Prevents 429 errors | 30 min | builder.py:36-40 |
| 1.3 | Fix stale documentation | Prevents user errors | 1 hr | docs/tutorial.md, docs/api_reference.md |
| 1.4 | Add error logging to fetch_work_data | Enables debugging | 15 min | builder.py:24-25 |
| 1.5 | Fix CLI render-before-export mutation | Clean JSON output | 30 min | cli.py:75-91 |

### Priority 2 (High — Next Sprint)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 2.1 | Add GEXF/GraphML export (export CLI command) | Enables Gephi/VOSviewer | 2 hr | New exporters.py, cli.py |
| 2.2 | Add co-citation network mode | Scientometric analysis | 4 hr | New scientometrics.py |
| 2.3 | Add bibliographic coupling mode | Scientometric analysis | 4 hr | New scientometrics.py |
| 2.4 | Add HITS (Hubs/Authorities) analysis | Hub vs authority distinction | 2 hr | builder.py or new module |
| 2.5 | Add DOI format validation | Prevents silent failures | 30 min | builder.py |

### Priority 3 (Medium — Backlog)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 3.1 | Add Louvain community detection | Thematic clustering | 2 hr | New module |
| 3.2 | Add analyze CLI command | Graph structure insights | 2 hr | cli.py |
| 3.3 | Add node coloring by PageRank/community | Better visualization | 1 hr | visualizer.py |
| 3.4 | Add DOI metadata caching | Faster rebuilds | 3 hr | builder.py |
| 3.5 | Add progress reporting (tqdm/rich) | Better UX | 1 hr | cli.py, builder.py |

### Priority 4 (Low — Nice to Have)

| # | Improvement | Impact | Effort | Files |
|---|-------------|--------|--------|-------|
| 4.1 | Add polite-pool email support | Higher OpenAlex rate limits | 15 min | config.py, builder.py |
| 4.2 | Add incremental graph builds | Efficiency for large reviews | 4 hr | builder.py |
| 4.3 | Add static image export (PNG/SVG) | Publication-ready figures | 3 hr | New module |
| 4.4 | Add graph diff/comparison | Track changes across runs | 4 hr | New module |
| 4.5 | Replace models.py with Pydantic models | Type safety | 2 hr | models.py |

---

## Appendix A: File Inventory

| File | Lines | Status |
|------|-------|--------|
| src/scholar_graph/__init__.py | 1 | Empty module docstring only |
| src/scholar_graph/models.py | 14 | DEAD — never imported |
| src/scholar_graph/config.py | 9 | DEAD — never used |
| src/scholar_graph/builder.py | 130 | Core logic — needs semaphore + logging |
| src/scholar_graph/visualizer.py | 59 | Working — needs coloring + exports |
| src/scholar_graph/cli.py | 125 | Working — needs export/analyze commands |
| tests/test_builder.py | 55 | Minimal — needs edge cases |
| tests/test_cli.py | 42 | Minimal — needs error path tests |
| tests/test_visualizer.py | 20 | Minimal — needs content checks |
| docs/tutorial.md | 45 | STALE — references nonexistent classes |
| docs/api_reference.md | 44 | STALE — references nonexistent classes |
| README.md | 100 | Mostly accurate |
| pyproject.toml | 35 | Clean |
| map.html | 222 | Generated artifact (PyVis template) |

**Total source code:** 319 lines (including dead code)
**Total test code:** 117 lines
**Test coverage:** Minimal — 3 test files, no edge-case or error-path coverage

---

## Appendix B: Integration Dependency Graph

    scholar-search-kit (AcademicHttpClient)
            |
            v
    scholar-graph-kit
      builder.py -----> nx.DiGraph (networkx)
      visualizer.py --> PyVis (pyvis)
      cli.py ---------> Typer + Rich
            |
            v
    scholar-rag-kit (reads graph.json pagerank key)
    scholar-agent-kit (MCP nexus_graph_build tool)
    scholar-harness (orchestrator Stage 8)

---

## Appendix C: Cross-References to Ecosystem Analysis

| Ecosystem Feature | Kit Module | Status | Priority |
|-------------------|-----------|--------|----------|
| GEXF/GraphML Exporters | visualizer.py / new exporters.py | Phase A | P1 |
| Co-Citation and Coupling | new scientometrics.py | Phase B | P1 |
| HITS Hubs/Authorities | builder.py | Phase B | P2 |
| Louvain Community Detection | new module | Phase B | P2 |
| K-Core Decomposition | new module | Phase B | P2 |
| Temporal Citation Dynamics | new module | Phase C | P3 |
| Cytoscape.js JSON | visualizer.py | Phase A | P2 |

---

Analysis generated on 2026-09-14 by deep-dive review of tools/scholar-graph-kit/ source, tests, docs, and ecosystem cross-references.