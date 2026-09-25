# Phase A: Universal Interoperability & Ingestion Hygiene

**Specification Version:** 1.0.0  
**Status:** READY FOR IMPLEMENTATION  
**Target System:** `nexus-scholar-harness` + `scholar-search-kit`, `scholar-bib-kit`, `scholar-graph-kit`  
**Estimated Duration:** 4 days  
**Success Gates:** Exported `.ris` validates in Rayyan/Covidence; Dedup election deterministic; Blank abstract rate drops ≥75%; Graph files load in Gephi/yEd

---

## 1. Executive Summary

Phase A addresses **Universal Interoperability & Ingestion Hygiene** through five quick-win features that bridge critical gaps in the current Nexus Scholar Python monorepo. These features unlock interoperability with external systematic review platforms and eliminate metadata quality issues that compromise systematic literature review integrity.

### 1.1 Features Overview

| # | Feature | Kit | Impact | Effort |
|---|---------|-----|--------|--------|
| A1 | RIS Exporter (.ris) | scholar-search-kit | High | Medium |
| A2 | ~~CSL-JSON Exporter~~ | scholar-bib-kit | Dropped | Out of scope |
| A3 | 0–16 Completeness Scoring | scholar-search-kit | High | Low |
| A4 | Pre-Screening Abstract Backfilling | scholar-search-kit | High | Medium |
| A5 | GEXF & GraphML Exporters | scholar-graph-kit | High | Low |

### 1.2 Methodological Value

- **PRISMA 2020 Compliance:** Enables export to Rayyan/Covidence for institutional multi-screener validation
- **Data Hygiene:** 0–16 completeness scoring ensures highest-fidelity metadata survives deduplication
- **Selection Bias Prevention:** Abstract backfilling eliminates premature exclusions due to missing abstracts
- **Publication Readiness:** GEXF/GraphML exports enable Gephi, VOSviewer, and yEd integration

---

## 2. Feature Specifications

### 2.1 A1: RIS Exporter (.ris)

**Goal:** Add native Tagged RIS export to `scholar-search-kit` and expose via CLI and MCP tools.

#### 2.1.1 RIS Format Specification

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
C1  - arXiv:1512.03385
ER  - 
```

#### 2.1.2 Field Mappings

| RIS Tag | Document Field | Required | Notes |
|---------|---------------|----------|-------|
| `TY` | Computed from `doc.venue` | Yes | JOUR/CONF/GEN |
| `TI` | `doc.title` | Yes | |
| `AU` | `doc.authors[i]` | Yes* | `Family, Given` format |
| `PY` | `doc.year` | Yes | |
| `JO` | `doc.venue` | Conditional | When TY=JOUR |
| `T2` | `doc.venue` | Conditional | When TY=CONF |
| `AB` | `doc.abstract` | Yes* | |
| `DO` | `doc.external_ids.doi` | Yes* | |
| `UR` | `doc.url` | Yes* | |
| `DB` | `doc.sources[0].get("provider", "nexus-scholar")` | Yes | Fallback: "nexus-scholar" |
| `C1` | `doc.external_ids.arxiv_id` | Conditional | Prefix: "arXiv:" |
| `ER` | Literal | Yes | End of record |

#### 2.1.3 Type Mapping Logic

```python
def _determine_ris_type(doc: Document) -> str:
    if doc.venue and any(x in doc.venue.lower() for x in ["journal", "trans"]):
        return "JOUR"
    elif "conf" in (doc.venue or "").lower():
        return "CONF"
    return "GEN"
```

#### 2.1.4 Files to Modify

| File | Changes |
|------|---------|
| `tools/scholar-search-kit/src/scholar_search/export.py` | Add `ris()` method to `Exporter` class |
| `tools/scholar-search-kit/src/scholar_search/cli.py` | Update `_save_output()` to accept `ris` format |
| `tools/scholar-search-kit/src/scholar_search/__init__.py` | Export `Exporter` (already exported) |

#### 2.1.5 Implementation Details

```python
# tools/scholar-search-kit/src/scholar_search/export.py
class Exporter:
    def ris(self, documents: list[Document], output_file: str | Path) -> Path:
        """Export documents to standardized Tagged RIS (.ris) format.
        
        Compatible with: Rayyan, Covidence, EPPI-Reviewer, EndNote, Zotero, Mendeley
        """
        path = Path(output_file)
        if not path.suffix == ".ris":
            path = path.with_suffix(".ris")
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: list[str] = []
        for doc in documents:
            ty = self._determine_ris_type(doc)
            lines.append(f"TY  - {ty}")
            
            if doc.title:
                lines.append(f"TI  - {doc.title}")
            
            for author in doc.authors:
                if author.family_name and author.given_name:
                    lines.append(f"AU  - {author.family_name}, {author.given_name}")
                elif author.family_name:
                    lines.append(f"AU  - {author.family_name}")
            
            if doc.year:
                lines.append(f"PY  - {doc.year}")
            
            if doc.venue:
                if ty == "JOUR":
                    lines.append(f"JO  - {doc.venue}")
                elif ty == "CONF":
                    lines.append(f"T2  - {doc.venue}")
            
            if doc.abstract:
                lines.append(f"AB  - {doc.abstract}")
            
            if doc.external_ids.doi:
                lines.append(f"DO  - {doc.external_ids.doi}")
            if doc.url:
                lines.append(f"UR  - {doc.url}")
            if doc.external_ids.arxiv_id:
                lines.append(f"C1  - arXiv:{doc.external_ids.arxiv_id}")
            
            db_source = doc.sources[0].get("provider", "nexus-scholar") if doc.sources else "nexus-scholar"
            lines.append(f"DB  - {db_source}")
            lines.append("ER  - \n")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path
    
    @staticmethod
    def _determine_ris_type(doc: Document) -> str:
        if doc.venue and any(x in doc.venue.lower() for x in ["journal", "trans"]):
            return "JOUR"
        elif "conf" in (doc.venue or "").lower():
            return "CONF"
        return "GEN"
```

---

### 2.2 A2: CSL-JSON Exporter (Dropped)

**Status:** Dropped based on review feedback. CSL-JSON is out of scope for the current capabilities as it is not used by the protocol engine. Citations are handled by the RIS exporter (A1) and native BibTeX tools.

---

### 2.3 A3: 0–16 Completeness Scoring

**Goal:** Replace network-latency first-seen bias with deterministic election of highest-fidelity metadata record.

#### 2.3.1 Scoring Formula

From NEXUS_MASTER_SPECIFICATION.md Section 3.1.B:

```python
Score = 2(doi) + 2(abstract) + venue + authors + year + citations + orcid + not_retracted + provider_weight
```

**Provider Weights:**
- OpenAlex: +5
- Crossref: +4
- Semantic Scholar: +3
- arXiv: +2
- PubMed: +2

#### 2.3.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-search-kit/src/scholar_search/completeness.py` | **NEW** - Scoring utility |
| `tools/scholar-search-kit/src/scholar_search/dedup.py` | Integrate scoring into representative election |

#### 2.3.3 Implementation Details

```python
# tools/scholar-search-kit/src/scholar_search/completeness.py
from .models import Document

# Provider priority weights
PROVIDER_WEIGHTS = {
    "openalex": 5,
    "crossref": 4,
    "semanticscholar": 3,
    "s2": 3,
    "arxiv": 2,
    "pubmed": 2,
    "biorxiv": 1,
    "unknown": 0,
}

def compute_completeness_score(doc: Document) -> int:
    """Compute an objective completeness score (0-10) for representative election.
    
    Rules:
        - Has DOI: +2
        - Has Abstract (>20 chars): +2
        - Has Venue: +1
        - Has Authors (>0): +1
        - Has Year: +1
        - Has Citations (>0): +1
        - Has ORCID (any author): +1
        - Not Retracted: +1
    
    Returns:
        Integer score between 0 and 10
    """
    score = 0
    
    # DOI presence (weight 2)
    if doc.external_ids.doi:
        score += 2
    
    # Abstract presence (weight 2, must be substantial)
    if doc.abstract and len(doc.abstract.strip()) > 20:
        score += 2
    
    # Venue (weight 1)
    if doc.venue:
        score += 1
    
    # Authors (weight 1)
    if doc.authors:
        score += 1
    
    # Year (weight 1)
    if doc.year:
        score += 1
    
    # Citations (weight 1)
    if doc.citations_count and doc.citations_count > 0:
        score += 1
    
    # ORCID (weight 1)
    if any(getattr(a, "orcid", None) for a in doc.authors):
        score += 1
    
    # Not retracted (weight 1)
    if not getattr(doc, "is_retracted", False):
        score += 1
    
    return score


def compute_total_score(doc: Document) -> int:
    """Compute total score including provider weight (0-16).
    
    This is used for representative election where provider quality matters.
    """
    base_score = compute_completeness_score(doc)
    provider_weight = PROVIDER_WEIGHTS.get(doc.provider.lower(), 0)
    return base_score + provider_weight
```

#### 2.3.4 Integration with Deduplicator

> **CRITICAL:** `DocumentCluster` uses `members: list[Document]`, NOT `duplicates`. The elected representative must inherit the cluster's `workspace_id` and `cluster_id`.

```python
# tools/scholar-search-kit/src/scholar_search/dedup.py
# Add import at top:
from .completeness import compute_total_score

# Modify deduplicate() method:
def deduplicate(self, documents: list[Document]) -> list[DocumentCluster]:
    # ... existing logic ...
    
    # When a duplicate is found, compare scores:
    if match:
        candidate_score = compute_total_score(document)
        current_score = compute_total_score(match.representative)
        
        if candidate_score > current_score:
            # Swap: new document becomes representative
            old_rep = match.representative
            # Preserve cluster identity
            document.workspace_id = old_rep.workspace_id
            document.cluster_id = old_rep.cluster_id
            # Merge metadata from old representative into new
            self._merge_metadata(document, old_rep)
            match.representative = document
            # Add old representative to members list
            match.members.append(old_rep)
        else:
            # Current representative stays; add candidate to members
            document.workspace_id = match.representative.workspace_id
            document.cluster_id = match.representative.cluster_id
            self._merge_metadata(match.representative, document)
            match.members.append(document)
    # ...
```

---

### 2.4 A4: Pre-Screening Abstract Backfilling

**Goal:** Eliminate selection bias from missing abstracts by batch-hydrating from Semantic Scholar and OpenAlex.

#### 2.4.1 API Endpoints

**Semantic Scholar:**
```
POST https://api.semanticscholar.org/graph/v1/paper/batch
Body: {"ids": ["DOI:10.1109/CVPR.2016.90", "DOI:10.xxx"]}
Query params: fields=paperId,abstract
```

**OpenAlex:**
```
GET https://api.openalex.org/works?filter=doi:10.1109/CVPR.2016.90
```

#### 2.4.2 Required Addition: `AcademicHttpClient.post()`

> **CRITICAL:** The current `AcademicHttpClient` only implements `get()` and `close()`. The `post()` method must be added for Semantic Scholar batch API.

```python
# tools/scholar-search-kit/src/scholar_search/http_client.py
# Add to AcademicHttpClient class:

async def post(
    self, 
    url: str, 
    json: dict | list | None = None,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: float = 30.0,
) -> httpx.Response:
    """Send POST request with rate limiting, caching, and retries.
    
    Args:
        url: Target URL
        json: JSON body payload
        params: Query parameters
        headers: Additional headers
        timeout: Request timeout in seconds
        
    Returns:
        httpx.Response object
        
    Raises:
        httpx.HTTPStatusError: On 4xx/5xx responses after retries
    """
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    
    for attempt in range(self.max_retries):
        await self._rate_limit.wait()
        try:
            response = await self.client.post(
                url,
                json=json,
                params=params,
                headers=request_headers,
                timeout=timeout,
            )
            
            # Handle rate limit headers directly if present
            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", 5))
                await asyncio.sleep(retry_after)
                continue
                
            response.raise_for_status()
            return response
            
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            if attempt == self.max_retries - 1:
                raise
            
            # Exponential backoff
            await asyncio.sleep(self.base_delay * (2 ** attempt))
```

#### 2.4.3 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-search-kit/src/scholar_search/http_client.py` | Add `post()` method with rate limiting and error handling |
| `tools/scholar-search-kit/src/scholar_search/enrichment.py` | **NEW** - AbstractHydrator class |
| `src/scholar_harness/orchestrator.py` | Insert hydration step between dedup and screening |

#### 2.4.3 Implementation Details

```python
# tools/scholar-search-kit/src/scholar_search/enrichment.py
import asyncio
from .models import Document
from .http_client import AcademicHttpClient

class AbstractHydrator:
    """Asynchronously hydrates missing abstracts across Semantic Scholar and OpenAlex."""
    
    def __init__(self, http_client: AcademicHttpClient):
        self.http_client = http_client
        self.s2_base = "https://api.semanticscholar.org/graph/v1"
        self.oa_base = "https://api.openalex.org/works"
    
    async def hydrate_missing_abstracts(
        self, documents: list[Document], batch_size: int = 50
    ) -> tuple[list[Document], dict[str, int]]:
        """Identifies papers with missing abstracts and queries batch APIs.
        
        Args:
            documents: List of documents to hydrate
            batch_size: Number of DOIs per batch request
            
        Returns:
            Tuple of (hydrated documents, stats dict)
        """
        stats = {"attempted": 0, "hydrated": 0, "failed": 0}
        
        # Filter to documents needing abstracts
        candidates = [
            doc for doc in documents 
            if not doc.abstract and doc.external_ids.doi
        ]
        
        stats["attempted"] = len(candidates)
        
        if not candidates:
            return documents, stats
        
        # Process in batches
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            batch_dois = [doc.external_ids.doi for doc in batch]
            
            # Try Semantic Scholar first
            hydrated = await self._hydrate_from_s2(batch_dois)
            
            # Fall back to OpenAlex for remaining
            remaining = [doi for doi in batch_dois if doi not in hydrated]
            if remaining:
                hydrated.update(await self._hydrate_from_openalex(remaining))
            
            # Update documents
            for doc in batch:
                if doc.external_ids.doi in hydrated:
                    doc.abstract = hydrated[doc.external_ids.doi]
                    stats["hydrated"] += 1
                else:
                    stats["failed"] += 1
        
        return documents, stats
    
    async def _hydrate_from_s2(self, dois: list[str]) -> dict[str, str]:
        """Batch query Semantic Scholar for abstracts."""
        result = {}
        try:
            response = await self.http_client.post(
                f"{self.s2_base}/paper/batch",
                json={"ids": [f"DOI:{doi}" for doi in dois]},
                params={"fields": "paperId,externalIds,abstract"}
            )
            if response.status_code == 200:
                papers = response.json()
                for paper in papers:
                    if paper and paper.get("abstract"):
                        doi = paper.get("externalIds", {}).get("DOI")
                        if doi:
                            result[doi] = paper["abstract"]
        except Exception:
            pass  # Graceful degradation
        return result
    
    async def _hydrate_from_openalex(self, dois: list[str]) -> dict[str, str]:
        """Query OpenAlex for abstracts (one at a time, rate-limited)."""
        result = {}
        for doi in dois:
            try:
                response = await self.http_client.get(
                    self.oa_base,
                    params={"filter": f"doi:{doi}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        abstract = data["results"][0].get("abstract_inverted_index")
                        if abstract:
                            result[doi] = self._reconstruct_abstract(abstract)
            except Exception:
                pass
        return result
    
    @staticmethod
    def _reconstruct_abstract(inverted_index: dict) -> str:
        """Reconstruct abstract from OpenAlex inverted index format."""
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        return " ".join(word for _, word in word_positions)
```

---

### 2.5 A5: GEXF & GraphML Exporters

**Goal:** Enable publication-ready graph exports for Gephi, VOSviewer, yEd, and Cytoscape.

> **P7.7 LAZY IMPORT CONSTRAINT:** Per AGENTS.md, all `networkx` imports must remain deferred inside function/method bodies. Top-level imports will violate the minimal-dependency import time gate and break `uv run pytest tests/test_scholar_agent_cli.py`.

#### 2.5.1 NetworkX Export Functions

```python
# GEXF (Gephi native format)
nx.write_gexf(G, "graph.gexf")

# GraphML (yEd, Cytoscape, NetworkX native)
nx.write_graphml(G, "graph.graphml")

# Cytoscape.js JSON
cytoscape_data = nx.cytoscape_data(G)
```

#### 2.5.2 Files to Modify

| File | Changes |
|------|---------|
| `tools/scholar-graph-kit/src/scholar_graph/builder.py` | Add `export_gexf()` and `export_graphml()` static methods |
| `tools/scholar-graph-kit/src/scholar_graph/cli.py` | Extend `--format` option to include `gexf`, `graphml` |

#### 2.5.3 Implementation Details

```python
# tools/scholar-graph-kit/src/scholar_graph/builder.py
class CitationGraphBuilder:
    # ... existing methods ...
    
    @staticmethod
    def _sanitize_node_attrs(G: "nx.DiGraph") -> None:
        """Sanitize node attributes for XML export (GEXF/GraphML).
        
        XML validators fail on None values. This converts None to appropriate defaults.
        Must be called before nx.write_gexf() or nx.write_graphml().
        """
        for node, data in G.nodes(data=True):
            for key, value in data.items():
                if value is None:
                    if isinstance(key, str) and key in ("year", "citations", "pagerank"):
                        data[key] = 0
                    else:
                        data[key] = ""
    
    @staticmethod
    def export_gexf(G: "nx.DiGraph", output_path: str | Path) -> Path:
        """Export graph to GEXF format (Gephi-compatible).
        
        Includes all node attributes: title, year, citations, pagerank, label.
        P7.7: networkx import deferred to method body.
        """
        import networkx as nx  # Deferred (P7.7)
        
        path = Path(output_path)
        if not path.suffix == ".gexf":
            path = path.with_suffix(".gexf")
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure pagerank is computed
        if G.nodes and "pagerank" not in list(G.nodes(data=True))[0][1]:
            pagerank = nx.pagerank(G, alpha=0.85)
            nx.set_node_attributes(G, pagerank, "pagerank")
        
        # Sanitize for XML compliance
        CitationGraphBuilder._sanitize_node_attrs(G)
        
        nx.write_gexf(G, str(path))
        return path
    
    @staticmethod
    def export_graphml(G: "nx.DiGraph", output_path: str | Path) -> Path:
        """Export graph to GraphML format (yEd, Cytoscape compatible).
        
        P7.7: networkx import deferred to method body.
        """
        import networkx as nx  # Deferred (P7.7)
        
        path = Path(output_path)
        if not path.suffix == ".graphml":
            path = path.with_suffix(".graphml")
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure pagerank is computed
        if G.nodes and "pagerank" not in list(G.nodes(data=True))[0][1]:
            pagerank = nx.pagerank(G, alpha=0.85)
            nx.set_node_attributes(G, pagerank, "pagerank")
        
        # Sanitize for XML compliance
        CitationGraphBuilder._sanitize_node_attrs(G)
        
        nx.write_graphml(G, str(path))
        return path
```

#### 2.5.4 CLI Integration

```python
# tools/scholar-graph-kit/src/scholar_graph/cli.py
@app.command()
def build(
    dois: list[str] = typer.Option([], "--doi", "-d"),
    input_file: Path = typer.Option(None, "--input", "-i"),
    output_html: Path = typer.Option("graph.html", "--output", "-o"),
    output_json: Path = typer.Option("graph.json", "--json-output", "-j"),
    format: str = typer.Option("html+json", "--format", "-f", help="Export formats: html, json, gexf, graphml, all"),
):
    # ... existing build logic ...
    
    # Export based on format
    formats = [f.strip() for f in format.split("+")]
    
    if "gexf" in formats or "all" in formats:
        gexf_path = output_json.with_suffix(".gexf")
        builder.export_gexf(G, gexf_path)
        typer.echo(f"✓ GEXF exported to {gexf_path}")
    
    if "graphml" in formats or "all" in formats:
        graphml_path = output_json.with_suffix(".graphml")
        builder.export_graphml(G, graphml_path)
        typer.echo(f"✓ GraphML exported to {graphml_path}")
    
    # Existing exports
    if "html" in formats or "all" in formats:
        viz = GraphVisualizer(output_html)
        viz.generate_html(G)
    
    if "json" in formats or "all" in formats:
        builder.export_json(G, output_json)
```

---

## 3. Testing Strategy

### 3.1 Testing Principles

1. **Hermetic Tests:** No network calls, no real API invocations
2. **Isolated Workspaces:** Use `tmp_path` fixture for all file I/O
3. **Contract-Driven:** Verify data schemas, not implementation details
4. **Deterministic:** Same inputs always produce same outputs

### 3.2 Test Categories

#### 3.2.1 Unit Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| RIS Exporter | `test_export_ris.py` | RIS format compliance, field mapping, type detection |
| CSL-JSON | `test_csl_json.py` | CSL-JSON schema, type mapping, author parsing |
| Completeness Scoring | `test_completeness.py` | Score calculation, provider weights, edge cases |
| Abstract Hydration | `test_enrichment.py` | Batch processing, API mocking, graceful degradation |
| GEXF/GraphML | `test_graph_export.py` | Format compliance, attribute preservation |

#### 3.2.2 Integration Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| CLI RIS Export | `test_cli_search.py` | End-to-end CLI command, format selection |
| CLI CSL-JSON | `test_cli_bib.py` | Export command, import roundtrip |
| Dedup + Scoring | `test_dedup_scoring.py` | Representative election with scoring |
| Orchestrator + Hydration | `test_orchestrator.py` | Pipeline integration |

#### 3.2.3 Conformance Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| RIS Roundtrip | `test_ris_roundtrip.py` | Export → Import → Compare |
| CSL-JSON Roundtrip | `test_csl_roundtrip.py` | Export → Import → Compare |
| GEXF/Gephi Validation | `test_gephi_compat.py` | GEXF loads in Gephi validator |

### 3.3 Test Fixtures

```python
# tests/fixtures.py
import pytest
from scholar_search.models import Document, ExternalIds, Author

@pytest.fixture
def sample_documents():
    """Sample documents for export testing."""
    return [
        Document(
            title="Deep Residual Learning for Image Recognition",
            year=2016,
            provider="openalex",
            external_ids=ExternalIds(doi="10.1109/CVPR.2016.90"),
            authors=[
                Author(family_name="He", given_name="Kaiming"),
                Author(family_name="Zhang", given_name="Xiangyu"),
            ],
            venue="IEEE Conference on Computer Vision and Pattern Recognition",
            abstract="Deeper neural networks are more difficult to train...",
            url="https://doi.org/10.1109/CVPR.2016.90",
            sources=[{"provider": "openalex", "id": "W2965490812"}],
            citations_count=100000,
        ),
        Document(
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            year=2019,
            provider="crossref",
            external_ids=ExternalIds(doi="10.18653/v1/N19-1423"),
            authors=[
                Author(family_name="Devlin", given_name="Jacob"),
                Author(family_name="Chang", given_name="Ming-Wei"),
            ],
            venue="Conference of the North American Chapter of the Association for Computational Linguistics",
            abstract="We introduce BERT...",
            sources=[{"provider": "crossref", "id": "N19-1423"}],
            citations_count=50000,
        ),
    ]

@pytest.fixture
def sample_graph():
    """Sample NetworkX graph for export testing."""
    import networkx as nx
    G = nx.DiGraph()
    G.add_node("10.1109/CVPR.2016.90", title="ResNet", year=2016, citations=100000, pagerank=0.8)
    G.add_node("10.18653/v1/N19-1423", title="BERT", year=2019, citations=50000, pagerank=0.6)
    G.add_edge("10.18653/v1/N19-1423", "10.1109/CVPR.2016.90")
    return G
```

### 3.4 Test Execution Commands

```bash
# Run all Phase A tests
uv run pytest tests/ -k "phase_a or ris or csl or completeness or enrichment or gexf or graphml" -v

# Run specific feature tests
uv run pytest tests/test_export_ris.py -v
uv run pytest tests/test_csl_json.py -v
uv run pytest tests/test_completeness.py -v
uv run pytest tests/test_enrichment.py -v
uv run pytest tests/test_graph_export.py -v

# Run with coverage
uv run pytest tests/ --cov=scholar_search --cov=scholar_bib --cov=scholar_graph --cov-report=html
```

---

## 4. Task List

### 4.1 Feature A1: RIS Exporter

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| A1.1 | Create `ris()` method in `Exporter` class | None | 2 |
| A1.2 | Add `_determine_ris_type()` helper | None | 0.5 |
| A1.3 | Update `_save_output()` in CLI | A1.1 | 0.5 |
| A1.4 | Update CLI help text for `--format` option | A1.3 | 0.25 |
| A1.5 | Write unit tests for RIS export | A1.1 | 1.5 |
| A1.6 | Write integration test for CLI | A1.3 | 1 |
| A1.7 | Test with Rayyan/Covidence import | A1.6 | 1 |
| **Total** | | | **6.75** |

### 4.2 Feature A2: CSL-JSON Exporter

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| A2.1 | Create `csl_json.py` module in `scholar-bib-kit` | None | 1 |
| A2.2 | Implement `CslJsonExporter.export()` for BibTeX Entry | A2.1 | 2 |
| A2.3 | Implement `_convert_entry()` | A2.2 | 1.5 |
| A2.4 | Implement `_parse_authors()` with institutional author handling | A2.2 | 1 |
| A2.5 | Implement `CslJsonImporter` | A2.1 | 2 |
| A2.6 | Add `export` command to `scholar-bib` CLI | A2.2 | 0.5 |
| A2.7 | Add `csl_json()` method to `scholar-search-kit` `Exporter` class | A2.2 | 1.5 |
| A2.8 | Update `scholar-search export --format csl-json` | A2.7 | 0.5 |
| A2.9 | Write unit tests | A2.2, A2.5, A2.7 | 2 |
| A2.10 | Write roundtrip tests (BibTeX ↔ CSL-JSON, Document → CSL-JSON) | A2.9 | 1 |
| **Total** | | | **13** |

### 4.3 Feature A3: 0–11 Completeness Scoring

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| A3.1 | Create `completeness.py` module | None | 0.5 |
| A3.2 | Implement `compute_completeness_score()` | A3.1 | 1 |
| A3.3 | Implement `compute_total_score()` | A3.2 | 0.5 |
| A3.4 | Add `PROVIDER_WEIGHTS` constant | A3.1 | 0.25 |
| A3.5 | Integrate into `Deduplicator.deduplicate()` | A3.3 | 1.5 |
| A3.6 | Write unit tests for scoring | A3.2, A3.3 | 1.5 |
| A3.7 | Write integration tests for dedup | A3.5 | 1.5 |
| A3.8 | Verify determinism across runs | A3.7 | 0.5 |
| **Total** | | | **7.25** |

### 4.4 Feature A4: Pre-Screening Abstract Backfilling

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| A4.0 | Add `post()` method to `AcademicHttpClient` | None | 1.5 |
| A4.1 | Create `enrichment.py` module | None | 0.5 |
| A4.2 | Implement `AbstractHydrator` class | A4.0, A4.1 | 2 |
| A4.3 | Implement `_hydrate_from_s2()` | A4.2 | 1.5 |
| A4.4 | Implement `_hydrate_from_openalex()` | A4.2 | 1.5 |
| A4.5 | Implement `_reconstruct_abstract()` | A4.4 | 0.5 |
| A4.6 | Integrate into orchestrator pipeline | A4.2 | 1 |
| A4.7 | Write unit tests with mocked APIs | A4.2 | 2 |
| A4.8 | Write integration test for orchestrator | A4.6 | 1.5 |
| A4.9 | Test graceful degradation (API failures) | A4.7 | 0.5 |
| **Total** | | | **12.5** |

### 4.5 Feature A5: GEXF & GraphML Exporters

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| A5.1 | Add `export_gexf()` to `CitationGraphBuilder` | None | 0.5 |
| A5.2 | Add `export_graphml()` to `CitationGraphBuilder` | None | 0.5 |
| A5.3 | Ensure PageRank is computed before export | A5.1, A5.2 | 0.5 |
| A5.4 | Extend CLI `--format` option | A5.1, A5.2 | 0.5 |
| A5.5 | Write unit tests for exports | A5.1, A5.2 | 1 |
| A5.6 | Test with Gephi/yEd import | A5.5 | 1 |
| **Total** | | | **4** |

### 4.6 Total Estimated Effort

| Feature | Hours |
|---------|-------|
| A1: RIS Exporter | 6.75 |
| A2: CSL-JSON Exporter | 13 |
| A3: Completeness Scoring | 7.25 |
| A4: Abstract Backfilling | 12.5 |
| A5: GEXF/GraphML Exporters | 4 |
| A6: Monorepo Sync (post-implementation) | 2 |
| **Total** | **45.5** |

---

## 4.7 Monorepo Governance (Post-Implementation)

> **CRITICAL:** Per AGENTS.md, changes to kit files must be synced to external repos.

### 4.7.1 Kit Sync Requirements

After implementing features in kit directories, run:

```bash
# Sync kit changes to external repos
python scripts/push_tools.py

# Update plugins.json with new commit SHAs
# (manual step after push)

# Regenerate metapackage pins
python scripts/generate_nexus_scholar_pins.py --check  # Verify freshness
python scripts/generate_nexus_scholar_pins.py          # Regenerate if needed
```

### 4.7.2 Conformance Test Updates

When adding new CLI options (`--format ris`, `--format gexf`, etc.), ensure they are registered in the Typer app so conformance tests pass:

```bash
# Run conformance tests
uv run pytest tests/conformance/test_actions_cli_parity.py -v
uv run pytest tests/conformance/test_mcp_tool_parity.py -v
```

### 4.7.3 Skill Updates

Update the relevant SKILL.md files to document new capabilities:

- `.agents/skills/scholar-search-kit/SKILL.md` - Add RIS/CSL-JSON export docs
- `.agents/skills/scholar-bib-kit/SKILL.md` - Add CSL-JSON export/import docs
- `.agents/skills/scholar-graph-kit/SKILL.md` - Add GEXF/GraphML export docs

---

## 5. Definition of Done (DoD)

### 5.1 Feature-Level DoD

For each feature to be considered complete:

- [ ] **Code Complete:** All implementation tasks finished
- [ ] **Tests Passing:** All unit and integration tests pass (`uv run pytest`)
- [ ] **Code Coverage:** New code has ≥90% test coverage
- [ ] **Lint Clean:** `uv run ruff check scripts/` passes (CI scope)
- [ ] **Type Clean:** No type errors in new code
- [ ] **Documentation:** Docstrings for all public functions/classes
- [ ] **CLI Integration:** Feature accessible via `scholar-search`, `scholar-bib`, or `scholar-graph` CLI
- [ ] **Backward Compatible:** No breaking changes to existing APIs

### 5.2 Feature-Specific DoD

#### A1: RIS Exporter
- [ ] Exported `.ris` file validates in Rayyan import
- [ ] Exported `.ris` file validates in Covidence import
- [ ] Exported `.ris` file validates in Zotero import
- [ ] All RIS tags (TY, TI, AU, PY, JO, AB, DO, UR, DB, C1, ER) correctly mapped
- [ ] Publication type (JOUR/CONF/GEN) correctly determined

#### A2: CSL-JSON Exporter
- [ ] CSL-JSON conforms to `application/vnd.citationstyles.csl+json` spec
- [ ] Roundtrip: BibTeX → CSL-JSON → BibTeX preserves all fields
- [ ] Zotero can import the exported CSL-JSON
- [ ] Pandoc can cite from the exported CSL-JSON

#### A3: 0–11 Completeness Scoring
- [ ] Deterministic: same inputs always produce same scores
- [ ] Provider weights correctly applied (OpenAlex > Crossref > S2 > arXiv > PubMed)
- [ ] Representative election independent of network race conditions
- [ ] Score calculation matches specification formula

#### A4: Pre-Screening Abstract Backfilling
- [ ] Blank abstract rate drops ≥75% on test corpus
- [ ] Semantic Scholar batch API correctly queried
- [ ] OpenAlex API correctly queried as fallback
- [ ] Graceful degradation when APIs fail
- [ ] Rate limiting respected (no 429 errors)

#### A5: GEXF & GraphML Exporters
- [ ] GEXF file loads in Gephi without error
- [ ] GraphML file loads in yEd without error
- [ ] Node attributes (title, year, citations, pagerank) preserved
- [ ] Edge direction preserved in exported files

### 5.3 Phase-Level DoD

For Phase A to be considered complete:

- [ ] All 5 features implemented and tested
- [ ] All feature-specific DoD criteria met
- [ ] All unit tests pass: `uv run pytest tests/ -v`
- [ ] All integration tests pass
- [ ] No regressions in existing functionality
- [ ] Documentation updated (README, CLI help text)
- [ ] Changes committed with descriptive commit messages
- [ ] Code reviewed by at least one other agent/person

### 5.4 Acceptance Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| RIS Export Validity | Import in Rayyan/Covidence | 100% success |
| CSL-JSON Conformance | Schema validation | 100% compliant |
| Completeness Score Determinism | Multiple runs, same inputs | 100% identical |
| Abstract Recovery Rate | Test corpus with 30% missing abstracts | ≥75% recovered |
| Graph Export Compatibility | Load in Gephi/yEd | 100% success |
| Test Coverage | New code coverage | ≥90% |
| No Regressions | Existing test suite | 0 failures |

---

## 6. Dependencies & Constraints

### 6.1 External Dependencies

| Dependency | Version | Used By | Notes |
|------------|---------|---------|-------|
| `networkx` | >=3.0 | A5 | Native GEXF/GraphML support |
| `bibtexparser` | >=2.0.0b7 | A2 | BibTeX parsing |
| `httpx` | >=0.28.1 | A4 | Async HTTP for API calls |
| `hishel` | ==0.0.32 | A4 | HTTP caching |

### 6.2 Internal Dependencies

| Dependency | Kit | Notes |
|------------|-----|-------|
| `AcademicHttpClient` | scholar-search-kit | Used by A4, A5 |
| `Document` model | scholar-search-kit | Used by A1, A3, A4 |
| `Entry` model | bibtexparser | Used by A2 |

### 6.3 Constraints

1. **No breaking changes:** All existing APIs must remain backward compatible
2. **Windows compatibility:** All file paths must handle Windows path separators
3. **UTF-8 encoding:** All file I/O must use UTF-8 encoding
4. **No network in tests:** All tests must be hermetic (mocked HTTP)

---

## 7. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RIS format variations across tools | Medium | High | Test with Rayyan, Covidence, Zotero |
| API rate limiting during hydration | Medium | Medium | Implement exponential backoff |
| Large graph export performance | Low | Low | Use streaming for very large graphs |
| bibtexparser v2 API changes | Low | Medium | Pin version in pyproject.toml |

---

*Specification created by opencode (mimo-v2.5-free) on 2026-09-15*
*Source: Phase A requirements from ecosystem analysis documents*