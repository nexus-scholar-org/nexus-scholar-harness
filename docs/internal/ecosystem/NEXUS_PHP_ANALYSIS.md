# Nexus Scholar PHP Ecosystem Analysis & Porting Blueprint

> **Scope:** Deep-dive architectural evaluation of the complete Nexus Scholar PHP repository ecosystem:
> 1. [`nexus-scholar/nexus-php`](https://github.com/nexus-scholar/nexus-php) (Legacy unified SLR library, 349 tests)
> 2. [`nexus-scholar/core`](https://github.com/nexus-scholar/core) (Modern Hexagonal/DDD scholarly review engine)
> 3. [`nexus-scholar/graph-algorithms`](https://github.com/nexus-scholar/graph-algorithms) (Standalone graph theory & scientometrics algorithm package)
>
> *For the complete 17-repository analysis across Python, PHP, .NET, and TypeScript, see [NEXUS_ECOSYSTEM_ANALYSIS.md](file:///c:/Users/mouadh/Documents/nexus-scholar-harness/docs/NEXUS_ECOSYSTEM_ANALYSIS.md).*
>
> Evaluated against the active Nexus Scholar Python monorepo (`nexus-scholar-harness` + the 8 domain toolkits).

---

## 1. Executive Summary

The Nexus Scholar PHP ecosystem represents a mature, well-engineered body of scholarly informatics software. While `nexus-php` was the original monolithic package, the project evolved into a clean Hexagonal / Domain-Driven Architecture in `core`, supported by an independent algorithmic layer in `graph-algorithms`.

Our Python monorepo (`nexus-scholar-harness`) remains vastly superior in **methodological inception (Phase-0 Socratic wizard), scientific trust verification (Phase-4 retraction/DAS/CAS/COI/RoB), structural AST vector retrieval (`scholar-rag-kit`), inter-screener Fleiss' $\kappa$, and bench-portable CLI distribution (`nexus-scholar init`)**.

However, across `core` and `graph-algorithms`, the PHP ecosystem developed several **production-grade bibliometric algorithms, full-text harvesting channels, screening comparison diagnostics, and serialization formats** that are missing in our Python kits. Adopting these features will significantly elevate our platform's capabilities.

---

## 2. Complete Ecosystem Comparison Matrix

| Capability Domain | PHP Ecosystem (`core` + `graph-algorithms`) | Python Monorepo (`scholar-*-kit`) | Verdict & Action |
| :--- | :--- | :--- | :--- |
| **Search Providers** | OpenAlex, Crossref, arXiv, S2, PubMed, **DOAJ**, **IEEE Xplore** | OpenAlex, Crossref, arXiv, S2, PubMed, bioRxiv | **Adopt:** Add DOAJ (free OA) & IEEE Xplore |
| **Query Normalization** | Typographic smart-quote & non-breaking hyphen sanitizer | Pydantic model + API parameter builders | **Adopt:** Add query text sanitization |
| **Deduplication Strategy** | Exact PID + Title Blocking + Fuzzy Levenshtein + **Completeness Scoring (0–11)** | Exact PID + Title Blocking + Fuzzy Levenshtein + `_merge_metadata` | **Adopt:** Formalize `completeness_score()` for representative election |
| **Corpus Governance** | **Corpus Locking (`LockCorpus` / `UnlockCorpus`)** | Ad-hoc file writes in `literature/` | **Adopt:** Formalize corpus lock milestone & audit event |
| **Full-Text OA Harvesting** | Direct URLs, Unpaywall, arXiv, S2, OpenAlex, **Europe PMC**, **PubMed Central OAI-PMH** | OpenAlex, Unpaywall, direct publisher heuristics, proxy cascade | **Adopt:** Add Europe PMC & PMC OAI-PMH to `scholar-pdf-kit` |
| **Citation Graph** | Directed citation graph (`DiGraph`, $A \rightarrow B$) | Directed citation graph (`DiGraph`, `builder.py`) | Parity |
| **Centrality Metrics** | PageRank, Degree (In/Out/Total), **Betweenness**, **HITS (Hubs & Authorities)**, **Personalized PageRank** | PageRank (`nx.pagerank`) | **Adopt:** Add HITS, Betweenness, and Degree Centrality via NetworkX |
| **Scientometric Modes** | **Co-Citation (Jaccard), Bibliographic Coupling, Hybrid Similarity** | Direct citations only | **High-Value Gap:** Add to `scholar-graph-kit` |
| **Community Detection** | **Louvain Modularity**, Strongly/Weakly Connected Components | Strongly connected components | **Adopt:** Add `nx.community.louvain_communities` |
| **Decomposition & Traversal** | **K-Core Decomposition**, **Shortest Citation Path (Dijkstra/BFS)** | Simple citation tree | **Adopt:** Add `nx.k_core` & `nx.shortest_path` |
| **Link Prediction** | **Adamic-Adar, Common Neighbors, Resource Allocation** | *None* | **Adopt:** Add citation link predictors via NetworkX |
| **Graph Interchange** | **PyVis HTML, GEXF (Gephi), GraphML (yEd), Cytoscape.js** | PyVis HTML only | **High-Value Gap:** Add GEXF, GraphML, Cytoscape.js |
| **SLR Export Formats** | BibTeX, **RIS**, CSV, JSON, JSONL | BibTeX, CSV, JSON, JSONL | **High-Value Gap:** Add RIS exporter (`.ris`) |
| **Screening Diagnostics** | **Run Comparison (`CompareScreeningRuns`), Transition Matrix** | Single-run Fleiss' $\kappa$ & adjudication | **High-Value Gap:** Add cross-run comparator |
| **Multi-Agent Voting** | **Council Aggregator with Conflict & Split Detection** | Majority voting + deadlock isolation | Parity |
| **Methodology / Inception** | Basic query plans (`queries.yml`) | Socratic 4-stage wizard, intent compiler, SHA-256 fingerprinting | **Python Monorepo Authoritative** |
| **Phase-4 Trust Layer** | *None* | Retraction audit, Open Science DAS/CAS, COI audit, QUADAS-2/PROBAST | **Python Monorepo Authoritative** |
| **RAG & Synthesis** | Plain text extraction dumps | AST chunking, ChromaDB sectional retrieval, verbatim certification ($\ge 90\%$) | **Python Monorepo Authoritative** |
| **Agent / Distribution** | Laravel AI SDK bindings | FastMCP server (19 tools), Harness Console UI, `nexus-scholar init` wheel | **Python Monorepo Authoritative** |

---

## 3. High-Value Discoveries & Porting Candidates

### 3.1 Advanced Scientometrics & Graph Theory (`scholar-graph-kit`)

`nexus-scholar/graph-algorithms` is a complete library of network algorithms. Because `scholar-graph-kit` already uses `networkx`, implementing these capabilities in Python is straightforward and requires zero heavy external dependencies.

#### A. HITS: Hubs & Authorities (`Centrality/Hits.php`)
- **Bibliometric Role**:
  - **Authorities** (high in-degree from influential hubs) = Seminal empirical breakthroughs / landmark papers.
  - **Hubs** (high out-degree citing key authorities) = Comprehensive systematic reviews, meta-analyses, and taxonomy surveys.
- **Python Implementation**:
  ```python
  import networkx as nx
  hubs, authorities = nx.hits(G, max_iter=100)
  ```

#### B. Co-Citation & Bibliographic Coupling (`CitationNetwork/`)
- **Co-Citation Analysis**: Quantifies intellectual paradigm clusters based on third-party co-occurrence:
  $$\text{Sim}_{\text{co-cite}}(A, B) = \frac{|\text{Citing}(A) \cap \text{Citing}(B)|}{|\text{Citing}(A) \cup \text{Citing}(B)|}$$
- **Bibliographic Coupling**: Quantifies current research fronts based on shared reference lists:
  $$\text{Coupling}(A, B) = |\text{Refs}(A) \cap \text{Refs}(B)|$$
- **Hybrid Similarity Network**:
  $$\text{Weight}(A, B) = w_{\text{cocite}} \cdot S_{\text{cocite}}(A, B) + w_{\text{couple}} \cdot S_{\text{couple}}(A, B) \quad (\ge \tau)$$

#### C. Louvain Community Detection (`Decomposition/Louvain.php`)
- Automatically detects modular sub-disciplines and thematic clusters in the literature network without requiring manual topic labels:
  ```python
  import networkx.algorithms.community as nx_comm
  communities = nx_comm.louvain_communities(G.to_undirected(), seed=42)
  ```

#### D. K-Core Decomposition (`Decomposition/KCore.php`)
- Iteratively prunes peripheral papers (degree $< k$) to extract the cohesive, high-density core of the field:
  ```python
  core_graph = nx.k_core(G, k=k)
  ```

#### E. Shortest Citation Path & Betweenness Centrality
- **Shortest Path (`Pathfinding/Dijkstra.php`)**: Trace the chain of scientific influence connecting a historical discovery to a contemporary paper (`nx.shortest_path(G, source, target)`).
- **Betweenness Centrality (`Centrality/Betweenness.php`)**: Identifies "bridge" papers linking previously separated research communities (`nx.betweenness_centrality(G)`).

---

### 3.2 Graph Interchange Formats (`scholar-graph-kit`)

Currently, `scholar-graph-kit` only exports interactive HTML via PyVis. `nexus-php` and `core` implement industry-standard serialization formats:

1. **GEXF Exporter (`GexfSerializer.php`)**: Native format for **Gephi** (node/edge attributes, weights, visual styling). Python: `nx.write_gexf(G, path)`.
2. **GraphML Exporter (`GraphMlSerializer.php`)**: Supported by **yEd**, Cytoscape, and NetworkX. Python: `nx.write_graphml(G, path)`.
3. **Cytoscape.js Exporter (`CytoscapeSerializer.php`)**: Emits JSON elements with `{data: {id, label, year, citations}, color}` formatted with year-based color gradients for immediate web rendering. Python: `nx.cytoscape_data(G)`.

---

### 3.3 Systematic Review Universal Export: RIS Format (`scholar-search-kit`)

In medical, health, and social science systematic literature reviews, external screening and reference management tools are standard:
- **Rayyan**
- **Covidence**
- **EPPI-Reviewer**
- **EndNote / Zotero / Mendeley**

All these tools expect **Tagged RIS (`.ris`)** files.
`core/src/Dissemination/Infrastructure/Serializer/RisSerializer.php` produces standard RIS records:
```text
TY  - JOUR
TI  - Deep Residual Learning for Image Recognition
AU  - He, Kaiming
AU  - Zhang, Xiangyu
PY  - 2016
JO  - IEEE Conference on Computer Vision and Pattern Recognition
AB  - Deeper neural networks are more difficult to train...
DO  - 10.1109/CVPR.2016.90
UR  - https://doi.org/10.1109/CVPR.2016.90
DB  - crossref
C1  - arXiv: 1512.03385
ER  - 
```

**Recommendation:** Add an `export.ris()` method to `scholar_search.export.Exporter` and expose `--format ris` across CLI and MCP.

---

### 3.4 Open Access Full-Text Expansion: Europe PMC & PMC OAI-PMH (`scholar-pdf-kit`)

In `nexus-scholar/core`, `Dissemination/Infrastructure/PdfSource/` incorporates two high-yield medical/biological OA full-text resolvers:
1. **Europe PMC Full-Text API (`EuropePmcFullTextSource.php`)**:
   - Directly retrieves open-access XML and PDF links from the Europe PMC REST API (`https://www.ebi.ac.uk/europepmc/webservices/rest/`).
2. **PubMed Central OAI-PMH (`PmcOaiFullTextSource.php`)**:
   - Queries the official NCBI PMC OAI-PMH service (`https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord`) using PMCIDs to retrieve authoritative full-text download links.

**Recommendation:** Incorporate Europe PMC and PMC OAI-PMH resolvers into `scholar-pdf-kit`'s candidate discovery cascade.

---

### 3.5 Screening Sensitivity & Run Comparison (`scholar-search-kit` / `scholar-verify-kit`)

In `core`, `CompareScreeningRunsHandler.php` implements a crucial SLR workflow: **comparing two screening passes**:
- Compares a **Baseline Run** (e.g. initial criteria / Model A) against a **Candidate Run** (e.g. refined criteria / Model B).
- Calculates:
  - **Agreement Rate**: $agreement / comparable$.
  - **Transition Matrix**: Count of decisions transitioning between states (`INCLUDE -> EXCLUDE`, `EXCLUDE -> INCLUDE`, `INCLUDE -> NEEDS_REVIEW`).
  - **Discrepancy Table**: Itemized list of works whose verdicts shifted, with before/after rationales.
- **Why it matters**: Systematic review guidelines (PRISMA, Cochrane) require researchers to justify criteria adjustments and calibrate screener sensitivity. Adding `scholar-search screen-compare runA.json runB.json` provides an objective audit trail.

---

### 3.6 Representative Election via Completeness Scoring (`scholar-search-kit`)

In `core/src/Deduplication/Infrastructure/CompletenessElectionPolicy.php`:
Rather than arbitrarily picking the first document in a duplicate cluster, each candidate work is evaluated by an objective **Completeness Score (0–11)**:
- Presence of DOI: `+2`
- Presence of Abstract: `+2`
- Presence of Publication Venue: `+1`
- Presence of Authors: `+1`
- Presence of Publication Year: `+1`
- Presence of Citation Count: `+1`
- Presence of ORCID: `+1`
- Not Retracted: `+1`
- Provider Priority: `openalex (+5) > crossref (+4) > semantic_scholar (+3) > arxiv (+2) > pubmed (+2)`

The candidate with the highest combined score is elected the cluster representative, guaranteeing the highest-quality metadata survives deduplication.

---

### 3.7 Corpus Governance: Locking & Snapshotting (`scholar-harness`)

In `core/src/Deduplication/Application/LockCorpusHandler.php`:
- Once deduplication is verified, the corpus is formally **locked**.
- Locking generates a cryptographic SHA-256 manifest of the unique documents and prevents accidental mutation or re-ingestion from perturbing subsequent PRISMA screening, extraction, and synthesis.
- If new search queries are executed, the corpus must be explicitly unlocked, triggering an audit record.

---

## 4. Where Nexus Scholar Python Is Authoritative

The following core pillars in our Python monorepo are far superior to the PHP implementations and must remain intact:

1. **Protocol Rigor & Inception (`scholar-protocol-kit`):**
   - 4-stage Socratic methodology protocol (latent intent mining, refraction grid, boundary grill, criteria formulation).
   - Deterministic Pydantic contract compilation and SHA-256 fingerprint verification.
2. **Phase-4 Trust Layer (`scholar-verify-kit`):**
   - Retraction tracking across OpenAlex and Crossref.
   - Open-science DAS/CAS artifact scanning.
   - Conflict-of-interest audit trail.
   - Deterministic QUADAS-2 and PROBAST risk of bias scoring.
3. **AST RAG & Grounded Synthesis (`scholar-rag-kit`):**
   - Structural AST chunking preserving markdown headers and section hierarchy.
   - Hybrid dense retrieval boosted by Graph PageRank.
   - Consensus Cartographer (lexical and embedding stance clustering).
   - Verbatim claim verification ($\ge 90\%$ verbatim certification via dual-pass $n$-grams and character sliding windows).
4. **Platform & Portability (`nexus-scholar init`):**
   - FastMCP server exposing 19 tools over `stdio`, `sse`, and `streamable-http`.
   - Local-first Harness Console with real-time DAG execution.
   - Zero-friction portable distribution via `uvx nexus-scholar init`.

---

## 5. Prioritized Adoption Roadmap for the Python Kits

| Milestone | Toolkit Target | Feature to Port | Impact |
| :---: | :--- | :--- | :--- |
| **P1** | `scholar-search-kit` | **RIS Exporter (`.ris`)** | Immediate compatibility with Rayyan, Covidence, EndNote, Zotero |
| **P1** | `scholar-graph-kit` | **Scientometric Modes** (Co-Citation, Bibliographic Coupling, Hybrid) | Evolves graph kit into a full bibliometric analysis engine |
| **P1** | `scholar-graph-kit` | **Graph Exporters** (GEXF, GraphML, Cytoscape.js) | Native Gephi, VOSviewer, and web visualization interchange |
| **P2** | `scholar-graph-kit` | **Network Algorithms** (HITS Hubs/Authorities, Louvain, K-Core, Shortest Path) | Advanced network analysis via native NetworkX methods |
| **P2** | `scholar-pdf-kit` | **Europe PMC & PMC OAI-PMH Resolvers** | Unlocks direct biomedical OA full texts bypassing paywalls |
| **P2** | `scholar-search-kit` | **Screening Run Comparator** (`screen-compare`) | Objective criteria sensitivity & transition matrix analysis |
| **P3** | `scholar-search-kit` | **Completeness Scoring** (0–11) in Deduplication | Mathematically optimal cluster representative election |
| **P3** | `scholar-search-kit` | **DOAJ & IEEE Xplore Providers** | Expanded open-access and engineering corpus coverage |
| **P3** | `scholar-harness` | **Corpus Locking Contract** (`corpus.lock`) | Immutable dataset snapshots before screening & synthesis |
