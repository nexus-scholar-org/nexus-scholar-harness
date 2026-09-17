# Tools Directory Comprehensive Analysis

**Date**: 2026-09-14
**Scope**: `C:\Users\mouadh\Documents\nexus-scholar-harness\tools\`

---

## 1. Complete Listing of All Kits

The `tools/` directory contains **8 kits** that together form the Nexus Scholar Suite -- a modular toolkit for systematic literature reviews.

| # | Kit Name | Version | Description | CLI Entry Point | Package Name |
|---|----------|---------|-------------|-----------------|--------------|
| 1 | `scholar-search-kit` | 0.1.0 | Federated academic search, deduplication, verification, and export | `scholar-search` | `scholar_search` |
| 2 | `scholar-protocol-kit` | 1.0.0 | Phase 0 protocol.json schema, canonical serializer, and validation CLI | `scholar-protocol` | `scholar_protocol` |
| 3 | `scholar-pdf-kit` | 0.1.0 | Automated Open Access Discovery and PDF downloader using Unpaywall/OpenAlex | `scholar-pdf` | `scholar_pdf` |
| 4 | `scholar-bib-kit` | 0.1.0 | Manage, lint, and deduplicate BibTeX databases | `scholar-bib` | `scholar_bib` |
| 5 | `scholar-rag-kit` | 0.1.0 | Scientific RAG, structural chunking, and graph-boosted synthesis | `scholar-rag` | `scholar_rag` |
| 6 | `scholar-graph-kit` | 0.1.0 | Build and visualize citation graphs from scholar search results | `scholar-graph` | `scholar_graph` |
| 7 | `scholar-agent-kit` | 0.1.0 | MCP Server exposing all Nexus Scholar tools to AI Agents | `scholar-agent` | `scholar_agent` |
| 8 | `scholar-verify-kit` | 0.1.0 | Post-screening trust verification (retraction, open-science, COI, risk-of-bias) | `scholar-verify` | `scholar_verify` |

---

## 2. Kit Descriptions and Purposes

### 2.1 scholar-search-kit (Foundation Layer)

**Purpose**: The discovery, deduplication, and verification backbone of the suite. Provides unified search across multiple academic databases.

**Key Capabilities**:
- Federated search across 6 providers: OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv, bioRxiv
- Citation snowballing (forward and backward) and multi-hop BFS chaining
- Document verification and hallucination detection against Crossref/OpenAlex
- Smart deduplication by persistent identifiers (DOI, arXiv ID, PMID, OpenAlex ID, S2 ID) and fuzzy title matching (>=97% similarity)
- PRISMA 2020 title/abstract screening with protocol-driven inclusion/exclusion criteria
- Import/export in JSON, JSONL, CSV, and RIS formats

**Key Classes**:
- `SearchEngine` - Orchestrates search across multiple providers (`src/scholar_search/engine.py:21`)
- `Deduplicator` - Two-tier deterministic deduplication (`src/scholar_search/dedup.py:21`)
- `DocumentVerifier` - Citation existence verification (`src/scholar_search/verifier.py:45`)
- `AcademicHttpClient` - HTTP client with caching (hishel), rate limiting, retries (`src/scholar_search/http_client.py:47`)
- `SearchProvider` (Protocol) - Provider contract (`src/scholar_search/providers/base.py:12`)
- `BaseAPIProvider` (ABC) - Base class for live API providers (`src/scholar_search/providers/base.py:30`)

**Data Models** (`src/scholar_search/models.py`):
- `Document` (line 56) - Normalized scholarly document with rich metadata
- `ExternalIds` (line 8) - Persistent identifier container
- `Query` (line 128) - Search query specification
- `DocumentCluster` (line 138) - Deduplication cluster with representative document

**Providers** (`src/scholar_search/providers/`):
- `OpenAlexProvider` - OpenAlex REST API
- `SemanticScholarProvider` - Semantic Scholar API
- `CrossrefProvider` - Crossref REST API
- `ArxivProvider` - arXiv API
- `PubMedProvider` - PubMed/NCBI API
- `BiorxivProvider` - bioRxiv API

### 2.2 scholar-protocol-kit (Contract Spine)

**Purpose**: The contract spine of the research pipeline. Defines the `protocol.json` schema that drives all downstream kits.

**Key Capabilities**:
- Pydantic v2 models as sole runtime source of truth for protocol.json
- Canonical serializer producing deterministic JSON bytes + SHA-256 fingerprint
- Validation engine with structural (Pydantic) + cross-field rules
- Compiler resolving Socratic IntentPackets into full canonical protocols
- Renderer generating Markdown PRISMA SCREENING_CRITERIA.md
- Extraction API for dynamic Pydantic schema generation for RAG consumption

**Key Modules** (`src/scholar_protocol/`):
- `models.py` (lines 1-351) - Pydantic v2 models (ResearchProtocol, ResearchQuestion, ScreeningCriteria, etc.)
- `canonical.py` - Deterministic serializer + SHA-256 fingerprint
- `validate.py` - Structural + cross-field validation with ValidationReport
- `compiler.py` (lines 1-256) - IntentPacket to ResearchProtocol compiler
- `render.py` (lines 1-89) - Markdown SCREENING_CRITERIA.md generator
- `extraction.py` - Dynamic Pydantic schema synthesis for RAG
- `presets.py` - Playbook presets and configuration logic
- `cli.py` (lines 1-248) - Typer CLI with validate, fingerprint, canon, compile, render-criteria, extraction-schema, extraction-prompt commands

**Enumerations** (`src/scholar_protocol/models.py`):
- `PlaybookType` (line 27) - PRISMA_SLR, SCOPING_REVIEW, RAPID_EVIDENCE, DESIGN_SCIENCE, STUDENT_DISSERTATION
- `EpistemologicalParadigm` (line 46) - POSITIVIST, INTERPRETIVIST, DESIGN_SCIENCE, PRAGMATIST_MIXED
- `DimensionDataType` (line 62) - FREE_TEXT, NUMERIC, CATEGORICAL, LIST

**JSON Schema**: `schemas/v1/protocol.schema.json` (kept in sync via CI)

### 2.3 scholar-pdf-kit (PDF Acquisition)

**Purpose**: Automated Open Access Discovery and PDF downloader. Resolves DOIs to hosted PDF files across university repositories and open archives.

**Key Capabilities**:
- DOI-to-PDF resolution via OpenAlex (Unpaywall API)
- Concurrent async PDF downloads with aiohttp
- Integrity validation via magic bytes (PDF header/trailer)
- Institutional proxy support (EZproxy, subdomain, prefix styles)
- Smart naming (Author_Year_Title format)
- PDF-to-Markdown extraction with PyMuPDF, Docling, or Grobid engines
- Manual PDF ingestion with metadata tagging

**Key Classes** (`src/scholar_pdf/`):
- `AsyncPDFDownloader` (`downloader.py:35`) - Async PDF downloader with retry/backoff
- `DownloadResult` (`downloader.py:27`) - Download outcome dataclass
- `PyMuPDFEngine` (`extract.py:16`) - Fast structured Markdown extractor
- `DoclingEngine` (`extract.py`) - Docling-based extraction
- `GrobidEngine` (`extract.py`) - Grobid service extraction

**Configuration** (`src/scholar_pdf/config.py`):
- `Settings` (line 6) - Pydantic Settings with proxy, timeout, validation options

### 2.4 scholar-bib-kit (BibTeX Management)

**Purpose**: Manage, lint, and deduplicate BibTeX databases.

**Key Capabilities**:
- BibTeX file parsing and serialization (via bibtexparser)
- Linting: title wrapping, key standardization (AuthorYear format)
- Deduplication by DOI and title matches
- Merging multiple BibTeX files
- Resolution of messy entries via Crossref API

**Key Classes** (`src/scholar_bib/`):
- `BibParser` (`parser.py:5`) - Static load/save methods
- `BibLinter` (`linter.py`) - Title wrapping, key generation
- `BibDeduplicator` (`deduplicator.py:9`) - DOI/title-based dedup
- `BibResolver` (`resolver.py`) - Crossref API resolution

### 2.5 scholar-rag-kit (Retrieval-Augmented Generation)

**Purpose**: Scientific RAG engine with structural chunking, graph-boosted retrieval, and grounded synthesis.

**Key Capabilities**:
- AST heading hierarchy structural chunking with breadcrumb context
- ChromaDB vector store with deterministic upsert idempotency
- Hybrid graph-boosted retrieval (dense cosine similarity + PageRank + seed boost)
- Grounded synthesis with atomic citation tokens and automated entailment verification
- Cross-study methodology comparison matrix (7 dimensions)
- Consensus Cartographer for claim clustering

**Key Classes** (`src/scholar_rag/`):
- `MarkdownChunker` (`chunker.py:12`) - AST heading hierarchy parser
- `ScholarIndexer` (`indexer.py:17`) - ChromaDB indexing with rich metadata
- `ScholarRetriever` (`retriever.py:18`) - Hybrid vector search with PageRank boosting
- `GroundedSynthesisEngine` (`synthesis.py:62`) - Synthesis with claim entailment
- `MatrixExtractor` (`matrix.py`) - Dynamic protocol matrix extraction
- `ConsensusCartographer` (`consensus.py`) - Claim clustering and consensus analysis

### 2.6 scholar-graph-kit (Citation Networks)

**Purpose**: Bibliometric network construction and visualization engine.

**Key Capabilities**:
- Asynchronous citation graph construction from DOIs via OpenAlex
- Directed citation graph (nx.DiGraph) with citing/cited relationships
- Normalized PageRank centrality computation
- Interactive PyVis HTML visualization with force-directed layouts
- Node-link JSON export for RAG ingestion

**Key Classes** (`src/scholar_graph/`):
- `CitationGraphBuilder` (`builder.py:11`) - Async citation graph builder
- `GraphVisualizer` (`visualizer.py:9`) - PyVis HTML generator

### 2.7 scholar-agent-kit (MCP Server)

**Purpose**: FastMCP Server exposing all Nexus Scholar tools to AI Agents via Model Context Protocol.

**Key Capabilities**:
- Exposes all kit functionalities as MCP tools
- Session-based FAIR recon memory (recon_probe, recon_distill, recon_delta)
- Protocol compilation and validation
- Federated search, deduplication, screening
- PDF extraction, RAG indexing, query, synthesis
- Citation graph building
- BibTeX cleaning
- Multi-screener reconciliation
- Verbatim claim verification
- Phase-4 verification (retraction, open-science, COI, risk-of-bias, trust-context)

**Key File** (`src/scholar_agent/server.py`):
- `MCPServer` instance (line 132)
- 18+ MCP tool functions registered via `@mcp.tool()` decorator
- Harness source resolution adapter (lines 81-101) for runtime import of `scholar_harness.recon`

**MCP Tools**:
- `nexus_protocol_compile` - Compile intent.json to protocol.json
- `nexus_protocol_validate` - Validate protocol schema
- `nexus_protocol_render_criteria` - Render screening criteria markdown
- `nexus_discover` - Search academic literature
- `nexus_dedup` - Deduplicate paper collections
- `nexus_screen` - Screen against protocol criteria
- `nexus_extract_pdf` - Extract PDF to Markdown
- `nexus_rag_index` - Index documents into ChromaDB
- `nexus_rag_query` - Query with PageRank boosting
- `nexus_rag_synthesize` - Generate grounded synthesis
- `nexus_matrix_extract` - Extract protocol matrix dimensions
- `nexus_graph_build` - Build citation graph
- `nexus_bib_clean` - Clean BibTeX files
- `nexus_screen_reconcile` - Reconcile multi-screener decisions
- `nexus_verify_claims` - Verify synthesis claims
- `nexus_verify_phase4` - Run Phase-4 verification streams
- `recon_probe` - Probe literature surface
- `recon_distill` - Distill pool into micro-taxonomy
- `recon_delta` - Adaptive probe horizon for gaps

### 2.8 scholar-verify-kit (Trust Verification)

**Purpose**: Post-screening trust verification for systematic reviews. Certifies that the evidence base feeding a synthesis is safe to quote.

**Key Capabilities**:
- Retraction status check via OpenAlex + Crossref APIs
- Data/Code availability (DAS/CAS) regex baseline over extracted fulltext
- Conflict-of-interest audit aggregation with deterministic relabel
- Deterministic QUADAS-2/PROBAST risk-of-bias scoring (D1-D4)
- Trust-weighted consensus annotation (merges Phase-4 outputs with Consensus Cartographer)
- Verbatim claim attribution verification (character-window and token n-gram matching)

**Key Classes** (`src/scholar_verify/`):
- `RetractionChecker` (`retraction.py:35`) - OpenAlex + Crossref retraction check
- `VerifyHttpClient` (`http_client.py:15`) - Sync HTTP client with retry/backoff
- `VerbatimClaimVerifier` (`verbatim.py`) - Character-window and token n-gram matching

---

## 3. Internal Structure of Each Kit

### 3.1 scholar-search-kit

```
tools/scholar-search-kit/
  pyproject.toml
  README.md
  uv.lock
  src/scholar_search/
    __init__.py           # Public API re-exports (52 lines)
    cli.py                # Typer CLI (704 lines)
    config.py             # Pydantic Settings (56 lines)
    models.py             # Document, Query, ExternalIds, Author (154 lines)
    engine.py             # SearchEngine orchestrator (111 lines)
    dedup.py              # Deduplicator (223 lines)
    verifier.py           # DocumentVerifier (239 lines)
    export.py             # Exporter (76 lines)
    importers.py          # RIS/JSON/JSONL importers (183 lines)
    http_client.py        # AcademicHttpClient (122 lines)
    screening.py          # PRISMA 2020 screening (745 lines)
    snowball.py           # CitationChainer
    protocol_adapter.py   # Protocol-to-Query compiler (90 lines)
    query_translator.py   # Query translation
    exceptions.py         # Custom exception hierarchy (32 lines)
    providers/
      __init__.py         # Provider re-exports (20 lines)
      base.py             # SearchProvider protocol, BaseAPIProvider ABC (123 lines)
      openalex.py         # OpenAlex provider
      semanticscholar.py  # Semantic Scholar provider
      crossref.py         # Crossref provider
      arxiv.py            # arXiv provider
      pubmed.py           # PubMed provider
      biorxiv.py          # bioRxiv provider
  tests/                  # 12 test files + cassettes + fixtures
  examples/
    course_demo_api.py
```

### 3.2 scholar-protocol-kit

```
tools/scholar-protocol-kit/
  pyproject.toml
  README.md                               # Comprehensive (169 lines)
  uv.lock
  src/scholar_protocol/
    __init__.py         # Public API (75 lines, comprehensive)
    cli.py              # Typer CLI (248 lines)
    models.py           # Pydantic v2 models (351 lines)
    canonical.py        # Deterministic serializer
    validate.py         # Validation engine
    compiler.py         # IntentPacket compiler (256 lines)
    intent.py           # IntentPacket model
    render.py           # Markdown renderer (89 lines)
    extraction.py       # Dynamic schema synthesis
    presets.py          # Playbook presets
  schemas/v1/
    protocol.schema.json  # JSON Schema (CI-synced)
  tests/                # 6 test files + fixtures (valid/invalid/canonical)
```

### 3.3 scholar-pdf-kit

```
tools/scholar-pdf-kit/
  pyproject.toml                          # Includes [extract] optional deps
  README.md                               # Comprehensive (106 lines)
  uv.lock
  docker-compose.grobid.yml
  src/scholar_pdf/
    __init__.py           # Comprehensive re-exports (39 lines)
    cli.py                # Typer CLI (279 lines)
    config.py             # Pydantic Settings (39 lines)
    models.py             # Data models
    downloader.py         # AsyncPDFDownloader (287 lines)
    extract.py            # PyMuPDF/Docling/Grobid engines (136 lines)
    validator.py          # PDF validation (magic bytes)
    publisher_patterns.py # Direct-PDF URL patterns
  tests/
  docs/
    tutorial.md
    api_reference.md
```

### 3.4 scholar-bib-kit

```
tools/scholar-bib-kit/
  pyproject.toml
  README.md                               # Minimal (3 lines)
  uv.lock
  src/scholar_bib/
    __init__.py           # Minimal (1 line)
    cli.py                # Typer CLI (127 lines)
    parser.py             # BibParser (14 lines)
    linter.py             # BibLinter
    deduplicator.py       # BibDeduplicator (60 lines)
    resolver.py           # BibResolver (Crossref API)
  tests/
  clean.bib, messy.bib, messy_no_doi.bib, resolved.bib  # Example files
  docs/
```

### 3.5 scholar-rag-kit

```
tools/scholar-rag-kit/
  pyproject.toml
  README.md                               # Comprehensive (134 lines)
  uv.lock
  LICENSE                                 # MIT
  src/scholar_rag/
    __init__.py           # Comprehensive re-exports (53 lines)
    cli.py                # Typer CLI (443 lines)
    models.py             # Pydantic models (269 lines)
    chunker.py            # MarkdownChunker (265 lines)
    indexer.py            # ScholarIndexer (267 lines)
    retriever.py          # ScholarRetriever (281 lines)
    synthesis.py          # GroundedSynthesisEngine (415 lines)
    matrix.py             # MatrixExtractor
    embedder.py           # Embedding provider abstraction
    consensus.py          # ConsensusCartographer
  tests/                  # 8 test files
  docs/
```

### 3.6 scholar-graph-kit

```
tools/scholar-graph-kit/
  pyproject.toml
  README.md                               # Comprehensive (100 lines)
  uv.lock
  src/scholar_graph/
    __init__.py           # Minimal (1 line)
    cli.py                # Typer CLI (125 lines)
    models.py             # GraphNode, GraphEdge (14 lines)
    builder.py            # CitationGraphBuilder (130 lines)
    visualizer.py         # GraphVisualizer (59 lines)
    config.py             # Configuration
  tests/
    test_builder.py
  docs/
  map.html, test_graph.html               # Example visualizations
```

### 3.7 scholar-agent-kit

```
tools/scholar-agent-kit/
  pyproject.toml                          # Depends on all other kits
  .gitignore
  uv.lock
  src/scholar_agent/
    server.py             # FastMCP server (1200+ lines)
    calibration.py        # Pre-flight screener calibration (467 lines)
  tests/
    test_calibration.py
    test_server.py
  .cache/               # Recon session cache
```

### 3.8 scholar-verify-kit

```
tools/scholar-verify-kit/
  pyproject.toml
  README.md                               # Detailed (51 lines)
  src/scholar_verify/
    __init__.py           # Module re-exports (5 lines)
    cli.py                # Typer CLI (272 lines)
    http_client.py        # VerifyHttpClient (47 lines)
    retraction.py         # RetractionChecker (287 lines)
    open_science.py       # DAS/CAS regex baseline (276 lines)
    coi.py                # COI audit aggregator (304 lines)
    risk_of_bias.py       # QUADAS-2/PROBAST scoring (266 lines)
    trust_context.py      # Trust-weighted consensus (380 lines)
    verbatim.py           # Verbatim claim verifier (179 lines)
  tests/                  # 6 test files
  docs/
```

---

## 4. Dependencies and Integration Points

### 4.1 Dependency Graph

```
scholar-protocol-kit  (zero kit dependencies - foundation)
    |
scholar-search-kit    (zero kit dependencies - foundation)
    |
    +-- scholar-bib-kit          (depends on: search-kit)
    +-- scholar-pdf-kit          (depends on: search-kit)
    +-- scholar-graph-kit        (depends on: search-kit)
    |
    +-- scholar-rag-kit          (depends on: search-kit, bib-kit, graph-kit)
            |
            +-- scholar-agent-kit  (depends on: ALL kits + harness recon)
                    |
                    +-- scholar-verify-kit  (depends on: requests only)
```

### 4.2 Detailed Dependency Matrix

| Kit | Kit Dependencies | External Dependencies |
|-----|-----------------|----------------------|
| scholar-protocol-kit | None | pydantic>=2.0, typer>=0.9, rich>=13.0 |
| scholar-search-kit | None | pydantic>=2.0, pydantic-settings>=2.0, httpx>=0.28, hishel==0.0.32, rich>=13.9, typer>=0.9 |
| scholar-bib-kit | scholar-search-kit | typer>=0.9, rich>=13.0, bibtexparser>=2.0b7, pydantic>=2.0 |
| scholar-pdf-kit | scholar-search-kit | pydantic>=2.0, pydantic-settings>=2.0, aiohttp>=3.9, typer>=0.9, requests>=2.31, rich>=13.0, tenacity>=8.0, pypdf>=4.0, pymupdf>=1.24; optional: docling>=2.5 |
| scholar-graph-kit | scholar-search-kit | typer>=0.9, rich>=13.0, networkx>=3.0, pyvis>=0.3.2, aiohttp>=3.9, pydantic>=2.0 |
| scholar-rag-kit | scholar-search-kit, scholar-bib-kit, scholar-graph-kit | typer>=0.9, rich>=13.0, chromadb>=0.4.22, sentence-transformers>=2.3.1, openai>=1.12.0, networkx>=3.0, pydantic>=2.0, bibtexparser>=2.0b7 |
| scholar-agent-kit | ALL kits (protocol, search, bib, pdf, rag, graph) | mcp |
| scholar-verify-kit | None (standalone) | typer>=0.9, rich>=13.0, requests>=2.31 |

### 4.3 Integration with Main Harness

The harness orchestrator (`src/scholar_harness/orchestrator.py`, lines 16-37) directly imports from kits:

```python
from scholar_graph.builder import CitationGraphBuilder
from scholar_graph.visualizer import GraphVisualizer
from scholar_pdf.extract import PyMuPDFEngine
from scholar_protocol.models import ResearchProtocol
from scholar_rag.indexer import ScholarIndexer
from scholar_rag.matrix import MatrixExtractor
from scholar_rag.retriever import ScholarRetriever
from scholar_rag.synthesis import GroundedSynthesisEngine
from scholar_search.dedup import Deduplicator
from scholar_search.engine import SearchEngine
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.providers import (OpenAlexProvider, SemanticScholarProvider, ...)
from scholar_search.verifier import DocumentVerifier
```

### 4.4 [tool.uv.sources] Cross-References

All kits use relative path references for editable installs:

```toml
[tool.uv.sources]
scholar-search-kit = { path = "../scholar-search-kit", editable = true }
```

This enables `uv pip install -e .` to resolve inter-kit dependencies correctly within the monorepo.

---

## 5. CLI Interfaces and Usage Patterns

### 5.1 Common CLI Patterns

All kits follow consistent patterns:

1. **Framework**: Typer CLI with Rich console output
2. **Entry Point**: Defined in `[project.scripts]` of pyproject.toml
3. **Invocation**: `uv run <cli-name> <command> [options]`
4. **Windows UTF-8**: All CLIs include `sys.stdout.reconfigure(encoding="utf-8")` for Windows compatibility

### 5.2 CLI Command Summary

| Kit | CLI | Commands |
|-----|-----|----------|
| scholar-search-kit | `scholar-search` | `search`, `snowball`, `chain`, `import`, `dedup`, `verify`, `export`, `screen` |
| scholar-protocol-kit | `scholar-protocol` | `validate`, `fingerprint`, `canon`, `compile`, `render-criteria`, `extraction-schema`, `extraction-prompt` |
| scholar-pdf-kit | `scholar-pdf` | `download`, `ingest`, `extract` |
| scholar-bib-kit | `scholar-bib` | `lint`, `merge`, `dedup`, `resolve` |
| scholar-rag-kit | `scholar-rag` | `index`, `query`, `synthesize`, `consensus`, `matrix`, `stats` |
| scholar-graph-kit | `scholar-graph` | `build`, `pagerank` |
| scholar-agent-kit | `scholar-agent` | Starts FastMCP server (no subcommands) |
| scholar-verify-kit | `scholar-verify` | `retraction`, `open-science`, `coi`, `risk-of-bias`, `trust-context`, `all`, `verbatim-claims` |

### 5.3 Typical Pipeline Usage

```bash
# Phase 0: Protocol creation
scholar-protocol compile intent.json > protocol.json
scholar-protocol validate protocol.json
scholar-protocol render-criteria protocol.json > SCREENING_CRITERIA.md

# Phase 1: Discovery
scholar-search search --protocol protocol.json --output results.json
scholar-search dedup results.json --output deduped.json
scholar-search screen --input deduped.json --protocol protocol.json --output-dir literature/

# Phase 2: PDF acquisition
scholar-pdf download --input literature/included.json --output pdfs/ --smart-names
scholar-pdf extract pdfs/ --output extracted/ --engine pymupdf

# Phase 2.5: BibTeX management
scholar-bib lint references.bib --output clean.bib
scholar-bib dedup references.bib

# Phase 2: RAG indexing
scholar-rag index extracted/ --bib references.bib --workspace-id SCI-000412
scholar-rag query "research question" --section-category methodology --limit 5

# Phase 2: Citation graph
scholar-graph build --input literature/included.json --output graph.html

# Phase 2: Synthesis
scholar-rag synthesize "research question" --rq-id RQ1 --output synthesis.md

# Phase 4: Verification
scholar-verify all --workspace workspaces/my-project/ --skip-retraction
scholar-verify verbatim-claims --claims synthesis/claims.json --extracted extracted/
```

---

## 6. Shared Utilities and Patterns

### 6.1 Windows UTF-8 Reconfiguration

All 7 CLI modules include the same pattern (`src/scholar_*/cli.py`):

```python
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
```

This is a duplicated utility that could be extracted into a shared module.

### 6.2 HTTP Client Abstraction

Two HTTP client implementations exist:

1. **Async**: `scholar_search.http_client.AcademicHttpClient` (hishel caching, rate limiting, retries)
   - Used by: scholar-search-kit, scholar-pdf-kit, scholar-graph-kit, scholar-agent-kit
   - Import: `from scholar_search.http_client import AcademicHttpClient`

2. **Sync**: `scholar_verify.http_client.VerifyHttpClient` (requests-based, retry/backoff)
   - Used by: scholar-verify-kit only
   - Standalone implementation, does not depend on search-kit

### 6.3 Configuration Pattern

Three kits use Pydantic Settings:
- `scholar_search.config.Settings` (env prefix: `SCHOLAR_`) - `src/scholar_search/config.py:9`
- `scholar_pdf.config.Settings` (no prefix) - `src/scholar_pdf/config.py:6`
- `scholar_protocol` (no config module - uses model defaults)

### 6.4 Data Model Patterns

- **Pydantic v2**: Used by protocol-kit, rag-kit, verify-kit for structured validation
- **Dataclasses**: Used by search-kit (Document, Query, ExternalIds), graph-kit (GraphNode, GraphEdge)
- **bibtexparser models**: Used by bib-kit for BibTeX-specific structures

### 6.5 CLI Pattern (Typer + Rich)

All CLIs follow the same structure:

```python
import typer
from rich.console import Console

app = typer.Typer(help="...", no_args_is_help=True)
console = Console()

@app.command("command-name")
def command(...):
    """Docstring for help."""
    ...
```

### 6.6 Deferred Imports Pattern

Several kits use deferred imports for heavy dependencies:

```python
# scholar-graph-kit builder.py (line 30)
import networkx as nx  # Deferred (P7.7): module load stays stdlib-only

# scholar-rag-kit indexer.py (line 39)
import chromadb  # deferred: keeps import chromadb-free

# scholar-rag-kit retriever.py (line 56)
import networkx as nx  # deferred: keeps import networkx-free
```

### 6.7 Deterministic/Idempotent Patterns

- **scholar-protocol-kit**: Canonical serialization produces byte-identical JSON
- **scholar-rag-kit**: Chunk IDs are deterministic (`chk-<doc_id>-<sec_slug>-<index:02d>`); ChromaDB upserts are idempotent
- **scholar-search-kit**: Deduplication is deterministic (same inputs -> same clusters)
- **scholar-verify-kit**: All streams except retraction are deterministic

### 6.8 Audit Logging

The RAG indexer automatically logs `RAG_INDEX_BUILT` events to `audit/journal.jsonl`.

---

## 7. Test Coverage and Quality

### 7.1 Test Directory Summary

| Kit | Test Files | Key Test Areas |
|-----|-----------|----------------|
| scholar-search-kit | 12 test files | CLI, dedup, engine, importers/exporters, models, providers, protocol adapter, query translator, screening, snowball, verifier |
| scholar-protocol-kit | 6 test files | canonical, CLI, compiler, models, schema sync, validate |
| scholar-pdf-kit | Tests exist | Downloader, extraction |
| scholar-bib-kit | Tests exist | Parser, deduplicator, linter |
| scholar-rag-kit | 8 test files | chunker, CLI, consensus, embedder, indexer, matrix, retriever, synthesis |
| scholar-graph-kit | 1 test file | builder |
| scholar-agent-kit | 2 test files | calibration, server |
| scholar-verify-kit | 6 test files | CLI, COI, open_science, retraction, risk_of_bias, trust_context |

### 7.2 Test Infrastructure

- **VCR.py cassettes**: scholar-search-kit uses HTTP recording for deterministic tests
- **Golden fixtures**: scholar-protocol-kit uses golden files for canonical serialization verification
- **Mock providers**: scholar-search-kit includes InMemoryProvider for offline testing

---

## 8. Issues and Areas for Improvement

### 8.1 Duplicated Windows UTF-8 Code

**Files**: All `cli.py` files (7 occurrences)
**Issue**: The Windows UTF-8 reconfiguration pattern is copy-pasted across all CLI modules.
**Recommendation**: Extract into a shared utility module (e.g., `scholar_common.cli_compat`).

### 8.2 Missing README for scholar-agent-kit

**File**: `tools/scholar-agent-kit/README.md`
**Issue**: The agent-kit has no README.md file (file not found).
**Recommendation**: Add documentation for the MCP server, tool list, and usage instructions.

### 8.3 Inconsistent __init__.py Exports

**Issue**: Some kits have comprehensive exports (protocol-kit: 75 lines, rag-kit: 53 lines, pdf-kit: 39 lines) while others have minimal exports (bib-kit: 1 line, graph-kit: 1 line, verify-kit: 5 lines).
**Recommendation**: Standardize public API surface across all kits.

### 8.4 scholar-verify-kit is Isolated

**Issue**: verify-kit has zero kit dependencies (only requests). It uses its own HTTP client rather than the shared `AcademicHttpClient`.
**Recommendation**: Consider whether verify-kit should use the shared HTTP client for consistency, or document the intentional isolation.

### 8.5 scholar-bib-kit Minimal Documentation

**File**: `tools/scholar-bib-kit/README.md` (3 lines)
**Issue**: The README is essentially empty.
**Recommendation**: Add usage documentation, API reference, and examples matching other kits.

### 8.6 scholar-graph-kit Sparse Models

**File**: `tools/scholar-graph-kit/src/scholar_graph/models.py` (14 lines)
**Issue**: The models module is very thin with simple dataclasses.
**Recommendation**: Consider Pydantic models for consistency with other kits, or document the design choice.

### 8.7 Dual HTTP Client Implementations

**Issue**: Two separate HTTP client implementations exist:
- `scholar_search.http_client.AcademicHttpClient` (async, hishel caching)
- `scholar_verify.http_client.VerifyHttpClient` (sync, requests-based)

**Recommendation**: Document the rationale for separation, or consider a shared base with sync/async variants.

### 8.8 scholar-agent-kit Harness Import Hack

**File**: `tools/scholar-agent-kit/src/scholar_agent/server.py` (lines 81-106)
**Issue**: The agent-kit uses a `sys.path` manipulation to import `scholar_harness.recon` at runtime.
**Recommendation**: This is a known design trade-off documented in the code. The adapter seam is well-documented but should be monitored.

### 8.9 Version Inconsistency

**Issue**: Most kits are at version 0.1.0, but scholar-protocol-kit is at 1.0.0.
**Recommendation**: This appears intentional (protocol-kit is the "contract spine" with frozen serialization rules). Document the versioning strategy.

### 8.10 scholar-rag-kit Heavy Dependencies

**Issue**: scholar-rag-kit pulls in chromadb, sentence-transformers, openai, and networkx -- some of the heaviest dependencies in the suite.
**Recommendation**: The deferred import pattern (chromadb, networkx) helps with import time. Consider whether some dependencies could be optional extras.

---

## 9. Architecture Summary

The tools directory implements a **layered, composable architecture** for systematic literature reviews:

```
Layer 4 (Agent):     scholar-agent-kit (MCP server, all tools exposed)
                      scholar-verify-kit (trust verification)

Layer 3 (RAG):       scholar-rag-kit (chunking, indexing, retrieval, synthesis)
                      scholar-graph-kit (citation networks, PageRank)

Layer 2 (Acquisition): scholar-pdf-kit (PDF download, extraction)
                        scholar-bib-kit (BibTeX management)

Layer 1 (Discovery):  scholar-search-kit (federated search, dedup, screening)

Layer 0 (Contract):   scholar-protocol-kit (protocol.json schema, validation)
```

**Key Design Principles**:
1. **Protocol-driven**: All downstream kits read `protocol.json` validated by protocol-kit
2. **Modular**: Each kit is independently installable and testable
3. **Composable**: Kits can be used via CLI or Python API
4. **Deterministic**: Core operations produce byte-identical outputs
5. **Auditable**: Every significant step logs to `audit/journal.jsonl`
6. **MCP-exposed**: All tools accessible to AI agents via scholar-agent-kit

---

*Analysis completed on 2026-09-14. Total kits analyzed: 8. Total source files reviewed: 80+.*
