# Nexus Scholar Harness & Kits Synthesis: Grounded Architecture, Gap Analysis & Value Justifications

> **Document Purpose:** This document synthesizes the architectural and algorithmic intelligence extracted from the Nexus Scholar ecosystem ([`NEXUS_PHP_ANALYSIS.md`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/docs/NEXUS_PHP_ANALYSIS.md) and [`NEXUS_ECOSYSTEM_ANALYSIS.md`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/docs/NEXUS_ECOSYSTEM_ANALYSIS.md)) and maps each finding directly against the active codebase of the Python monorepo (`nexus-scholar-harness` and the 8 domain toolkits under `tools/`).
>
> For every capability, this document specifies:
> 1. **Current Codebase State**: Exact file paths, current implementation, and architectural limitations in our active repo.
> 2. **Donor Pattern**: The origin repository and code implementation in the Nexus Scholar ecosystem.
> 3. **Methodological Argumentation & Value**: Why this capability matters for systematic literature reviews (SLRs), PRISMA 2020 compliance, and academic rigor.
> 4. **Concrete Technical Bridge**: Target Python architecture, class signatures, data models, and CLI/MCP exposure.

---

## 1. System Baseline: Current Architecture of Harness & Toolkits

The active Python monorepo (`nexus-scholar-harness`) is organized into an orchestration harness (`src/scholar_harness/`) and eight domain toolkits (`tools/`):

```
nexus-scholar-harness/
├── src/scholar_harness/
│   ├── orchestrator.py        # 9-stage linear master research pipeline
│   ├── agent_screen.py        # File-based PRISMA 2020 screening batch handoff
│   ├── inception.py           # Phase-0 Socratic interactive methodology wizard
│   ├── pipeline_executor.py   # Async task runner with terminal status rendering
│   └── cli.py                 # Typer CLI: status, sync, run, export, inception
│
└── tools/
    ├── scholar-search-kit/    # Discovery: OpenAlex, S2, Crossref, PubMed, arXiv, bioRxiv; 2-tier dedup
    ├── scholar-pdf-kit/       # OA Harvesting: landing URL heuristics, PyMuPDF block extraction
    ├── scholar-bib-kit/       # BibTeX curation: parsing, linting, deduplication, DOI resolution
    ├── scholar-rag-kit/       # AST markdown chunking, ChromaDB vector index, PageRank-boosted retrieval
    ├── scholar-graph-kit/     # DiGraph citation networks from OpenAlex, PageRank, PyVis HTML
    ├── scholar-protocol-kit/  # Pydantic protocol compiler, criteria renderer, SHA-256 fingerprinting
    ├── scholar-verify-kit/    # Phase-4 trust: Retraction, DAS/CAS scanning, COI audit, QUADAS-2/PROBAST
    └── scholar-agent-kit/     # FastMCP server exposing 19 tools over stdio/sse
```

While our platform leads in **Phase-0 Socratic inception, Phase-4 trust verification, and agent-native file handoffs**, critical gaps exist in bibliometric algorithms, reference interchange formats, PDF extraction robustness, and living review capabilities.

---

## 2. Granular Gap Analysis, Value Justification & Technical Bridges

### 2.1 In-Text Citation Resolution ("The Librarian")

#### A. Current Codebase State
- **Files**: [`tools/scholar-rag-kit/src/scholar_rag/chunker.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/chunker.py) and [`tools/scholar-pdf-kit/src/scholar_pdf/extract.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-pdf-kit/src/scholar_pdf/extract.py).
- **Current Behavior**: `MarkdownChunker` parses markdown along structural heading tags (`#`, `##`, `###`) and enforces size boundaries (`max_chunk_chars=1500`). When extracting text from PDFs, `PyMuPDFEngine` extracts raw text blocks without parsing the bibliography or resolving citation markers.
- **The Failure Mode**: Academic papers are dense with citations: *"Following the optimization framework in [14], we evaluated on the benchmark from [28]..."*. When `ScholarRetriever` fetches this chunk, the LLM has zero knowledge of who `[14]` or `[28]` are. The LLM either:
  1. Hallucinates a plausible author/title to fill the void.
  2. Omits the citation entirely, breaking traceability.
  3. Fails the $\ge 90\%$ verbatim grounding certification during synthesis.

#### B. Donor Pattern
- **Source**: [`nexus-scholar/pdf-struct-rag`](https://github.com/nexus-scholar/pdf-struct-rag) (`src/pdf_chat/librarian.py`).
- **Mechanism**:
  - `parse_references_markdown()` parses the bibliography into a structured `ReferenceLibrary` containing `{number, authors, title, year, venue, doi}`.
  - `extract_citation_numbers()` identifies numeric references (`[14]`, `[1-4]`, `[12, 15]`) and `extract_author_date_citations()` identifies textual references (`(Vaswani et al., 2017)`).
  - Injects resolved bibliographic data directly into the chunk footer:
    ```markdown
    Cited References in this Passage:
    - [14] He, K. et al. (2016) "Deep Residual Learning for Image Recognition" (doi:10.1109/CVPR.2016.90)
    ```

#### C. Methodological Argumentation & Value
- **PRISMA 2020 Item 13 (Synthesis Methods)**: Requires transparent attribution of evidence to original studies.
- **RAG Grounding**: By binding cited works into the retrieved chunk, the LLM synthesis engine (`scholar_rag.synthesis.GroundedSynthesisEngine`) can accurately attribute comparative claims without secondary retrieval passes.
- **Scientific Veracity**: Eliminates the single largest source of hallucination in scientific literature RAG.

#### D. Concrete Technical Bridge
1. Add `CitationResolver` to `scholar-rag-kit/src/scholar_rag/citations.py`.
2. Update `MarkdownChunker.chunk()` to accept an optional `references: dict[str, Reference]` map.
3. If references exist in frontmatter or document footer, resolve citations and append a structured `metadata.cited_works` field to `ChunkMetadata`.

---

### 2.2 Pre-Screening Batch Abstract Hydration

#### A. Current Codebase State
- **Files**: [`src/scholar_harness/orchestrator.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py) (Stages 1–4) and [`tools/scholar-search-kit/src/scholar_search/engine.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/engine.py).
- **Current Behavior**: Stage 1 queries search APIs. Crossref, bioRxiv, and certain PubMed records routinely return with `abstract: None` or empty strings. Stage 2 deduplicates. Stage 3 runs `DocumentVerifier`, which verifies DOIs and computes hashes but does not systematically backfill missing abstracts in batch. Stage 4 splits papers into 20-paper batches (`literature/screening/batch_NNN.json`).
- **The Failure Mode**: An agent or human screener reviewing `batch_NNN.json` encounters 15–30% of records with only a title and venue.
  - If the screener excludes them due to lack of information, **high-impact eligible studies are erroneously eliminated (fatal PRISMA selection bias)**.
  - If the screener marks them `NEEDS_REVIEW`, the screening queue clogs with manual retrieval tasks.

#### B. Donor Pattern
- **Source**: [`nexus-scholar/lit-screen-first`](https://github.com/nexus-scholar/lit-screen-first) (`src/lit_screener/screening.py: enrich_missing_abstracts`).
- **Mechanism**:
  - Filters deduplicated papers where `abstract is None and doi is not None`.
  - Executes asynchronous batch queries against the Semantic Scholar Graph API (`POST /graph/v1/paper/batch` with fields `paperId,abstract`) and OpenAlex Works API (`GET /works?filter=doi:...`).
  - Successfully hydrates abstracts for $\sim 80\%$ of previously blank records before screening begins.

#### C. Methodological Argumentation & Value
- **Cochrane Handbook §4.4 & PRISMA 2020 Item 6**: Title-only screening has an unacceptably high error rate ($>20\%$ accidental exclusion of eligible trials). Screening Title *and* Abstract is the gold standard.
- **Screening Throughput**: Screeners can make confident, definitive decisions (`INCLUDE` / `EXCLUDE`) on the first pass rather than deferring to full-text retrieval.

#### D. Concrete Technical Bridge
1. Add `AbstractHydrator` to `scholar-search-kit/src/scholar_search/enrichment.py`.
2. Insert a dedicated batch hydration step between Stage 2 (Deduplication) and Stage 4 (PRISMA Screening) in `orchestrator.py`:
   ```python
   # Stage 2.5: Batch Abstract Hydration
   hydrator = AbstractHydrator(http_client=engine.http_client)
   hydrated_docs, stats = await hydrator.hydrate_missing_abstracts(unique_docs)
   ```

---

### 2.3 0–11 Completeness Scoring for Deduplication Cluster Election

#### A. Current Codebase State
- **Files**: [`tools/scholar-search-kit/src/scholar_search/dedup.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/dedup.py) (`Deduplicator.deduplicate`).
- **Current Behavior**: In lines 60–90:
  ```python
  if match:
      match.duplicates.append(document)
      self._merge_metadata(match.representative, document)
  ```
  The document that was *encountered first* in the search array is permanently designated `match.representative`.
- **The Failure Mode**: Search results are fetched concurrently via `asyncio.gather()` across 6 providers. Network latency dictates which provider returns first. If Crossref (which lacks abstracts and citation counts) finishes 20ms faster than OpenAlex (which contains full abstracts, citation counts, open-access URLs, and ORCIDs), the Crossref record becomes the primary representative document throughout the entire project! Even though `_merge_metadata` patches empty fields, primary attributes (e.g. title casing, author formatting, primary venue) remain anchored to the inferior record.

#### B. Donor Pattern
- **Source**: [`nexus-scholar/core`](https://github.com/nexus-scholar/core) (`src/Deduplication/Infrastructure/CompletenessElectionPolicy.php`).
- **Mechanism**:
  Every candidate document in a duplicate cluster is evaluated using an objective, deterministic completeness score (0–11):
  $$\text{Score} = 2(\text{DOI}) + 2(\text{Abstract}) + \text{Venue} + \text{Authors} + \text{Year} + \text{Citations} + \text{ORCID} + \text{Active} + \text{ProviderWeight}$$
  Where provider priority breaks ties: `openalex (+5) > crossref (+4) > semanticscholar (+3) > arxiv (+2) > pubmed (+2)`.
  The document with the highest score is elected the cluster representative.

#### C. Methodological Argumentation & Value
- **Determinism & Reproducibility**: Deduplication representative election becomes 100% independent of network race conditions.
- **Metadata Quality**: Guarantees that the highest-fidelity metadata surviving into `literature/deduped.json`, `INDEX.md`, and synthesis tables is the most complete record available.

#### D. Concrete Technical Bridge
1. Add `def compute_completeness_score(doc: Document) -> int` to `scholar-search-kit/src/scholar_search/dedup.py`.
2. When a duplicate is matched:
   ```python
   candidate_score = compute_completeness_score(document)
   current_score = compute_completeness_score(match.representative)
   if candidate_score > current_score:
       # Swap: new document becomes representative, old representative moves to duplicates
       old_rep = match.representative
       match.representative = document
       match.duplicates.append(old_rep)
   else:
       match.duplicates.append(document)
   self._merge_metadata(match.representative, document)
   ```

---

### 2.4 Tagged RIS (`.ris`), CSL-JSON & EndNote XML Exporters

#### A. Current Codebase State
- **Files**: [`tools/scholar-search-kit/src/scholar_search/export.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/export.py) and [`tools/scholar-bib-kit/src/scholar_bib/`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-bib-kit/src/scholar_bib/).
- **Current Behavior**: `scholar_search.export.Exporter` only supports `.json`, `.jsonl`, and `.csv`. `scholar-bib-kit` only supports BibTeX (`.bib`).
- **The Failure Mode**: Real-world systematic literature reviews are collaborative endeavors. Healthcare and social science review teams use **Rayyan, Covidence, EPPI-Reviewer, EndNote, and Zotero**. None of these systematic review platforms accept custom JSON or JSONL. They mandate **Tagged RIS (`.ris`)** or **CSL-JSON (`.json`)**.
  Without RIS export, researchers cannot export their discovered or screened corpus into Rayyan or Covidence for institutional multi-screener validation, trapping Nexus Scholar in an isolated silo.

#### B. Donor Pattern
- **Sources**: [`nexus-scholar/refmanager`](https://github.com/nexus-scholar/refmanager) (`src/Formats/RisFormat.php`, `CslJsonFormat.php`, `EndNoteXmlFormat.php`) and [`nexus-scholar/nexus-research`](https://github.com/nexus-scholar/nexus-research) (`src/nexus/export/ris_exporter.py`).
- **Mechanism**:
  - Implements standard RIS specification:
    `TY - JOUR`, `TI - Title`, `AU - Author`, `PY - Year`, `JO - Journal`, `AB - Abstract`, `DO - DOI`, `UR - URL`, `DB - Provider`, `ER -`.
  - CSL-JSON specification (`application/vnd.citationstyles.csl+json`) for Pandoc and Zotero.

#### C. Methodological Argumentation & Value
- **Universal Ecosystem Interoperability**: Instantly unlocks two-way workflow bridges with Rayyan, Covidence, EndNote, Zotero, Mendeley, and Overleaf.
- **PRISMA Protocol Export**: Enables exporting the exact included/excluded sets directly into reference managers for publication bibliography formatting.

#### D. Concrete Technical Bridge
1. Port `RISExporter` to `scholar-search-kit/src/scholar_search/export.py`:
   ```python
   def ris(self, documents: list[Document], output_file: str | Path) -> Path: ...
   ```
2. Add `--format ris` and `--format csl-json` to `scholar-search export` CLI and FastMCP `export_literature` tool.
3. Update `src/scholar_harness/cli.py export` to support RIS.

---

### 2.5 Advanced Scientometrics: Co-Citation, Coupling, HITS & Louvain

#### A. Current Codebase State
- **Files**: [`tools/scholar-graph-kit/src/scholar_graph/builder.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-graph-kit/src/scholar_graph/builder.py) and [`visualizer.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-graph-kit/src/scholar_graph/visualizer.py).
- **Current Behavior**: Builds a simple directed graph ($A \rightarrow B$ if $A$ cites $B$). Calculates standard PageRank via `nx.pagerank(G)`. Renders an interactive PyVis HTML file with nodes colored by year.
- **The Failure Mode**:
  1. Direct citation networks are sparse and sensitive to citation lag (newer seminal papers have fewer direct citations).
  2. PageRank favors older, heavily cited foundational works, failing to identify **thematic sub-disciplines, emerging research fronts, or review surveys**.
  3. Researchers cannot identify which papers are **Authorities** (landmark empirical breakthroughs) versus **Hubs** (comprehensive systematic reviews and surveys).

#### B. Donor Pattern
- **Sources**: [`nexus-scholar/graph-algorithms`](https://github.com/nexus-scholar/graph-algorithms) (`Hits.php`, `Louvain.php`, `KCore.php`, `CitationNetwork/`) and [`nexus-scholar/scholar-graph`](https://github.com/nexus-scholar/scholar-graph) (`TemporalGraph.php`).
- **Mechanism**:
  - **HITS (Kleinberg Hubs & Authorities)**:
    ```python
    hubs, authorities = nx.hits(G, max_iter=100)
    ```
  - **Co-Citation Network**:
    Edge weight between $A$ and $B$ is the Jaccard similarity of their common citing papers:
    $$\text{Sim}_{\text{co-cite}}(A, B) = \frac{|\text{Citing}(A) \cap \text{Citing}(B)|}{|\text{Citing}(A) \cup \text{Citing}(B)|}$$
  - **Bibliographic Coupling**:
    Edge weight is the overlap in their bibliographies:
    $$\text{Coupling}(A, B) = |\text{Refs}(A) \cap \text{Refs}(B)|$$
  - **Louvain Community Detection**:
    ```python
    communities = nx.community.louvain_communities(G.to_undirected(), seed=42)
    ```
  - **Temporal Citation Dynamics**:
    Tracks citation cluster volume and trajectory across publication years.

#### C. Methodological Argumentation & Value
- **Scientometric Rigor**: Co-citation and bibliographic coupling are standard bibliometric methodologies (White & McCain, Kessler). They map intellectual structures independent of citation counts.
- **Literature Taxonomy Inception**: Louvain community detection automatically partitions the literature into thematic clusters, providing objective domain groupings for Phase-0 taxonomy synthesis.
- **Finding Key Surveys vs. Empirical Trials**: HITS separates review papers (high Hub score) from primary empirical evidence (high Authority score), which is essential during screening.

#### D. Concrete Technical Bridge
1. Add `ScientometricGraphBuilder` to `scholar-graph-kit/src/scholar_graph/scientometrics.py`.
2. Expose CLI commands:
   - `scholar-graph analyze --metric hits` (emits `literature/hits_analysis.json`).
   - `scholar-graph cluster --method louvain` (emits clustered communities with node assignments).
   - `scholar-graph build --mode co-citation` / `--mode coupling`.

---

### 2.6 Graph Interchange Exporters (GEXF, GraphML, Cytoscape.js)

#### A. Current Codebase State
- **Files**: [`tools/scholar-graph-kit/src/scholar_graph/visualizer.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-graph-kit/src/scholar_graph/visualizer.py).
- **Current Behavior**: Renders an standalone PyVis HTML document.
- **The Failure Mode**: PyVis HTML is convenient for quick visual checks, but unusable for academic publications. Researchers generating publication figures for journals or conferences require **Gephi, VOSviewer, Cytoscape, or yEd**. Without standard graph interchange files (`.gexf`, `.graphml`, Cytoscape JSON), researchers cannot perform advanced visual styling or run specialized community layout algorithms.

#### B. Donor Pattern
- **Sources**: [`nexus-scholar/graph-core`](https://github.com/nexus-scholar/graph-core) (`GexfExporter.php`, `GraphMLExporter.php`, `CytoscapeJsonExporter.php`).
- **Mechanism**:
  - GEXF (Graph Exchange XML Format) with typed node/edge attributes (year, citation count, PageRank, community).
  - GraphML for yEd and NetworkX.
  - Cytoscape.js JSON for headless web graph embedding.

#### C. Methodological Argumentation & Value
- **Publication Readiness**: Directly enables exporting citation networks into Gephi for high-resolution vector rendering in journal manuscripts.
- **Tool Interoperability**: Seamless integration with the broader network science toolchain.

#### D. Concrete Technical Bridge
NetworkX includes built-in support for these formats:
```python
# scholar-graph-kit/src/scholar_graph/exporters.py
def export_gexf(G: nx.Graph, path: Path) -> Path:
    nx.write_gexf(G, str(path))
    return path

def export_graphml(G: nx.Graph, path: Path) -> Path:
    nx.write_graphml(G, str(path))
    return path

def export_cytoscape(G: nx.Graph, path: Path) -> Path:
    data = nx.cytoscape_data(G)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path
```
Expose via `scholar-graph export <graph.json> --format gexf|graphml|cytoscape`.

---

### 2.7 Screening Run Comparator & Transition Matrices (`screen-compare`)

#### A. Current Codebase State
- **Files**: [`tools/scholar-search-kit/src/scholar_search/screening.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/screening.py) and [`src/scholar_harness/agent_screen.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/agent_screen.py).
- **Current Behavior**: Supports single-pass multi-screener adjudication with Fleiss' $\kappa$ inter-rater agreement (`adjudicate_batch()`).
- **The Failure Mode**: During a systematic review, criteria are frequently calibrated or prompt instructions refined between pilot passes. Currently, there is NO mechanism to compare **Run A (pilot / prompt v1)** against **Run B (calibrated / prompt v2)**. Researchers cannot answer:
  - *"How did our criteria refinement change inclusion decisions?"*
  - *"Which papers flipped from EXCLUDE to INCLUDE?"*
  - *"What is our sensitivity drift across model versions?"*

#### B. Donor Pattern
- **Source**: [`nexus-scholar/core`](https://github.com/nexus-scholar/core) (`src/Screening/Application/CompareScreeningRunsHandler.php`).
- **Mechanism**:
  - Ingests two screening decision sets (`runA.json` and `runB.json`).
  - Computes:
    1. **Overall Agreement Rate**: $N_{\text{agree}} / N_{\text{comparable}}$.
    2. **State Transition Matrix**:
       ```
                       Run B: INCLUDE   Run B: EXCLUDE   Run B: UNCERTAIN
       Run A: INCLUDE        42               3                 2
       Run A: EXCLUDE         5             180                 1
       Run A: UNCERTAIN       4               2                 6
       ```
    3. **Itemized Discrepancy Table**: Identifies every work that shifted verdict, showing previous vs. current exclusion reasons.

#### C. Methodological Argumentation & Value
- **PRISMA 2020 & MECIR (Cochrane) Compliance**: Methodological guidelines mandate reporting pilot screening results and criteria adjustments.
- **Sensitivity Calibration**: Provides an objective mathematical basis for validating automated agent screening prompts before launching full-scale review runs.

#### D. Concrete Technical Bridge
1. Add `compare_screening_runs(run_a: list[Decision], run_b: list[Decision]) -> ScreeningComparisonReport` to `scholar-search-kit/src/scholar_search/screening.py`.
2. Add CLI command: `scholar-search screen-compare <run_a.json> <run_b.json> --output comparison_report.md`.

---

### 2.8 Golden Seed Self-Healing Query Diagnostic Loop

#### A. Current Codebase State
- **Files**: [`tools/scholar-search-kit/src/scholar_search/protocol_adapter.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/protocol_adapter.py) and [`src/scholar_harness/inception.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/inception.py).
- **Current Behavior**: Inception compiles research questions and boundary criteria into search query strings. Queries are executed blindly in Stage 1.
- **The Failure Mode**: Researchers usually know 3–5 benchmark landmark studies in their topic ("Golden Seeds"). If the compiled search query misses even one of these landmark papers (due to overly restrictive boolean operators or terminology mismatch), the entire systematic review is compromised before it starts. The researcher only discovers this weeks later during manuscript preparation.

#### B. Donor Pattern
- **Source**: [`nexus-scholar/nexus-scout`](https://github.com/nexus-scholar/nexus-scout) (`scout/resources/views/prompts/diagnostic_critique_system.blade.php`).
- **Mechanism**:
  - The protocol specifies a `golden_seeds: list[str]` (DOIs of landmark papers).
  - An automated Diagnostic Critique loop:
    1. Executes candidate queries on academic APIs.
    2. Checks whether all `golden_seeds` are present in the retrieved set.
    3. If any seed is missing ($Recall < 100\%$), passes the missing seeds' titles, abstracts, and keywords to an LLM diagnostic critique.
    4. The critique identifies the syntax failure (e.g. *"Query required 'pruning' AND 'edge AI', but landmark paper DOI 10.1145/... uses 'model compression' and 'embedded systems'"*).
    5. The engine automatically heals the query syntax and re-runs until recall reaches $100\%$.

#### C. Methodological Argumentation & Value
- **Search Strategy Validation (Cochrane Handbook §4.4.4)**: Validating electronic search strategies against a pre-identified set of relevant studies is a mandatory methodological check in Cochrane systematic reviews.
- **Guaranteed Coverage**: Ensures the review starts on a validated, high-recall search foundation.

#### D. Concrete Technical Bridge
1. Add `golden_seeds: list[str] = Field(default_factory=list)` to `scholar_protocol.models.ResearchProtocol`.
2. In `src/scholar_harness/inception.py`, add a Step to solicit 2–5 Golden Seed DOIs.
3. Add `validate_and_heal_queries(query, golden_seeds, engine)` in `scholar-search-kit/src/scholar_search/query_validator.py`.

---

### 2.9 Living Systematic Reviews (LSR) & Delta Tracking

#### A. Current Codebase State
- **Files**: [`src/scholar_harness/orchestrator.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py) and [`src/scholar_harness/cli.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/cli.py).
- **Current Behavior**: The harness runs as a single-shot execution pipeline (`scholar-harness run`). If the user wants to update their review 6 months later, they must re-run the entire pipeline from scratch, blowing away existing screening decisions or forcing manual dedup.
- **The Failure Mode**: Literature reviews rapidly decay into obsolescence. In fields like artificial intelligence, biomedicine, and renewable energy, dozens of relevant papers are published monthly. Without incremental delta tracking, systematic reviews are outdated the day they are published.

#### B. Donor Pattern
- **Source**: [`nexus-scholar-org/scholar-monitor-kit`](https://github.com/nexus-scholar-org/scholar-monitor-kit) (`LiteratureMonitor`, `MonitorState`, `ReportGenerator`).
- **Mechanism**:
  - Maintains a workspace state tracking file (`.scholar_monitor.json`) with query aliases and last execution timestamps (`last_run: "2026-06-01T00:00:00Z"`).
  - Uses provider publication date filters (`from_date`) to fetch *only newly published studies*.
  - Compares against existing `literature/deduped.json` and queues delta studies into a new screening batch (`literature/screening/batch_delta_NNN.json`).
  - Generates incremental delta reports (`synthesis/delta_report_YYYY-MM.md`).

#### C. Methodological Argumentation & Value
- **Living Systematic Reviews (LSR, Elliott et al., BMJ 2017)**: The recognized gold standard for maintaining current evidence in dynamic fields.
- **Efficiency**: Eliminates re-screening hundreds of previously assessed papers; researchers only review the incremental delta.

#### D. Concrete Technical Bridge
1. Add `scholar-harness monitor <workspace> [--cron]` command to the harness CLI.
2. Store `.scholar_monitor.json` inside `<workspace>/audit/`.
3. Generate incremental PRISMA flowcharts showing:
   $$\text{Total Corpus} = \text{Baseline Corpus} + \Delta\text{ New Studies}$$

---

### 2.10 Living Research Wiki Scaffolding (`scholar-harness wiki init`)

#### A. Current Codebase State
- **Files**: [`src/scholar_harness/orchestrator.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py) and [`src/scholar_harness/cli.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/cli.py).
- **Current Behavior**: Pipeline artifacts are emitted as isolated JSON and Markdown files: `literature/included.json`, `extracted/*.md`, `synthesis/synthesis_matrix.json`, `synthesis/report.md`.
- **The Failure Mode**: These artifacts sit in terminal folders. Outside of the orchestrator CLI, researchers cannot easily browse, navigate, or build upon the knowledge graph. The synthesis report is read once, and the rich semantic connections between extracted papers are lost.

#### B. Donor Pattern
- **Source**: [`nexus-scholar/nexus-cli`](https://github.com/nexus-scholar/nexus-cli) (`NexusWikiInit.php`).
- **Mechanism**:
  - Automatically initializes and seeds a living, interconnected Markdown research wiki:
    ```
    <workspace>/docs/wiki/
    ├── papers/        # Interconnected Markdown notes per included study
    ├── concepts/      # Thematic concept pages linking studies by topic
    ├── synthesis/     # PRISMA reports and interactive evidence matrices
    ├── SCHEMA.md      # Wiki taxonomy guidelines
    ├── index.md       # Digital garden home
    └── log.md         # Chronological knowledge base changelog
    ```
  - Fully compatible with **Obsidian, Foam, Dendron, Quartz, and GitHub Pages**.

#### C. Methodological Argumentation & Value
- **Knowledge Permanence**: Converts a transient systematic literature review into an evergreen institutional research repository.
- **Collaborative Synthesis**: Team members can open the workspace directly in Obsidian, navigate bidirectional links between papers and concepts, and annotate findings.

#### D. Concrete Technical Bridge
1. Add `scholar-harness wiki init <workspace>` command.
2. In `orchestrator.py` Stage 9 (Synthesis), auto-generate linked Markdown notes in `docs/wiki/papers/<study_slug>.md` with bidirectional `[[wikilinks]]` to related concepts and cited studies.

---

### 2.11 Clean Zotero API Bridge

#### A. Current Codebase State
- **Files**: [`src/scholar_harness/cli.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/cli.py) and [`tools/scholar-search-kit/src/scholar_search/export.py`](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/export.py).
- **Current Behavior**: Outputs files to local disk.
- **The Failure Mode**: Researchers must manually drag and drop files into Zotero. Standard Zotero browser import often scrapes messy metadata (mangled author names, missing DOIs, incorrect publication years).

#### B. Donor Pattern
- **Source**: [`nexus-scholar/scholar-search-engine`](https://github.com/nexus-scholar/scholar-search-engine) (`ZOTERO_INTEGRATION.md`).
- **Mechanism**:
  - Uses `pyzotero` to connect directly to the user's Zotero Web API.
  - Automatically creates a dedicated collection named after the research workspace (e.g. `SLR: Edge AI in Agriculture`).
  - Pre-flight DOI duplicate prevention.
  - Pushes clean, structured author objects (`firstName`/`lastName`), clean DOIs, and venues.
  - Tags every entry with `#NexusScholar_Import` and `Source:<provider>`.

#### C. Methodological Argumentation & Value
- **Data Hygiene**: Bypasses messy HTML scraping and gives researchers an immaculate, verified Zotero collection ready for manuscript drafting.

#### D. Concrete Technical Bridge
1. Add `scholar_search.integrations.zotero.ZoteroBridge`.
2. Expose CLI command: `scholar-search zotero-sync <included.json> --collection "My Project" --api-key <key> --user-id <id>`.

---

## 3. Comprehensive Value & Effort Matrix

| Finding # | Capability | Target Toolkit / Location | Donor Origin | PRISMA / Methodological Value | Implementation Effort | ROI Priority |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | **In-Text Citation Resolution** | `scholar-rag-kit` / `chunker.py` | `pdf-struct-rag` | Eliminates RAG citation hallucination; ensures verifiable synthesis attribution. | Medium | **P1 (Critical)** |
| **2** | **Pre-Screening Abstract Backfilling** | `scholar-search-kit` / `engine.py` | `lit-screen-first` | Eliminates selection bias from missing abstracts (PRISMA Item 6). | Low | **P1 (Critical)** |
| **3** | **0–11 Completeness Scoring** | `scholar-search-kit` / `dedup.py` | `core` | Deterministic election of best metadata record; network race immunity. | Low | **P1 (Quick Win)** |
| **4** | **Universal RIS & CSL-JSON Exporter** | `scholar-search-kit` / `export.py` | `refmanager` | Interoperability with Rayyan, Covidence, EndNote, Zotero, Pandoc. | Low | **P1 (Quick Win)** |
| **5** | **Advanced Scientometrics (HITS/Co-Cite)** | `scholar-graph-kit` / `builder.py` | `graph-algorithms` | Identifies landmark Authorities vs review Hubs; uncovers thematic clusters. | Medium | **P2 (High Value)** |
| **6** | **Graph Interchange (GEXF/GraphML)** | `scholar-graph-kit` / `visualizer.py`| `graph-core` | Publication-ready network exports for Gephi, VOSviewer, and Cytoscape. | Low | **P2 (Quick Win)** |
| **7** | **Screening Run Comparator** | `scholar-search-kit` / `screening.py`| `core` | Verifies screener sensitivity drift & transition matrices across prompt revisions. | Medium | **P2 (High Value)** |
| **8** | **Golden Seed Self-Healing Queries** | `scholar-harness` / `inception.py` | `nexus-scout` | Validates search strategy recall against seminal benchmarks before full run. | Medium | **P2 (High Value)** |
| **9** | **Living Systematic Reviews (LSR)** | `scholar-harness` / `orchestrator.py`| `scholar-monitor-kit` | Prevents review obsolescence via automated recurring query delta tracking. | High | **P3 (Differentiator)** |
| **10** | **Living Research Wiki Scaffolding** | `scholar-harness` / `cli.py` | `nexus-cli` | Converts transient review outputs into linked Obsidian-compatible knowledge bases. | Low | **P3 (High Value)** |
| **11** | **Clean Zotero API Bridge** | `scholar-search-kit` / `integrations`| `scholar-search-engine`| Clean metadata push directly into researchers' reference libraries. | Low | **P3 (High Value)** |

---

## 4. Prioritized Engineering Execution Roadmap

```
PHASE A: IMMEDIATE WINS & INTEROPERABILITY (Days 1–3)
├── 1. Add RIS (.ris) and CSL-JSON exporter to scholar-search-kit/export.py
├── 2. Implement 0–11 Completeness Scoring election in scholar-search-kit/dedup.py
├── 3. Add GEXF (.gexf) and GraphML (.graphml) exports to scholar-graph-kit
└── 4. Add batch abstract backfilling (enrich_missing_abstracts) to scholar-search-kit

PHASE B: SCIENTOMETRICS & METHODOLOGICAL VALIDATION (Days 4–7)
├── 1. Add HITS (Hubs & Authorities) and Louvain community detection to scholar-graph-kit
├── 2. Add Co-Citation and Bibliographic Coupling network modes to scholar-graph-kit
├── 3. Implement screen-compare CLI command and transition matrix diagnostics in scholar-search-kit
└── 4. Implement Golden Seed validation loop in Phase-0 inception.py

PHASE C: DEEP PDF INTELLIGENCE & GROUNDED RAG (Days 8–11)
├── 1. Implement In-Text Citation Resolution ("The Librarian") in scholar-rag-kit
├── 2. Add sticky figure/table caption binding to scholar-pdf-kit extraction
└── 3. Add 2-stage retrieval with cross-encoder reranking to scholar-rag-kit

PHASE D: LIVING PLATFORM CAPABILITIES (Days 12–15)
├── 1. Integrate Living Systematic Review (LSR) delta tracking (scholar-harness monitor)
├── 2. Add scholar-harness wiki init research digital garden scaffolding
└── 3. Implement clean Zotero API sync bridge
```

---

## 5. Architectural Conclusion

By grounding the discoveries from the 17 donor repositories directly into the active Python codebase, this blueprint bridges the remaining gaps between the historical implementations and our active monorepo.

The result is a unified platform that combines:
- **Unrivaled Socratic Inception & Verification**: Phase-0 intent refinement and Phase-4 trust scoring (Retraction/DAS/CAS/COI/RoB).
- **Universal Bibliographic Interoperability**: Full compatibility with Rayyan, Covidence, EndNote, Zotero, Gephi, and Obsidian.
- **Deep Evidence Grounding**: Structural PDF chunking with in-text citation resolution and cross-encoder reranking.
- **Living, Self-Healing Automation**: Golden Seed diagnostic loops and continuous Living Systematic Review monitoring.
