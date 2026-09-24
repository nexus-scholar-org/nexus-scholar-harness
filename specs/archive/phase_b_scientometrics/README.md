# Phase B: Scientometrics & Methodological Validation

**Specification Version:** 1.1.0  
**Status:** READY FOR IMPLEMENTATION (Post-Review)  
**Target System:** `nexus-scholar-harness` + `scholar-graph-kit`, `scholar-search-kit`, `scholar-protocol-kit`  
**Estimated Duration:** 5 days (Days 5–9)  
**Success Gates:** HITS identifies seminal reviews as Hubs (rank-based); `screen-compare` generates transition matrix with regression/progression counters; Golden Seed recall achieves 100% on benchmark seeds; protocol schema sync tests pass

---

## 1. Executive Summary

Phase B addresses **Scientometrics & Methodological Validation** through five high-value features that transform the graph kit into a full bibliometric analysis engine and add critical screening diagnostics for PRISMA compliance.

### 1.1 Features Overview

| # | Feature | Kit | Impact | Effort |
|---|---------|-----|--------|--------|
| B1 | HITS Hubs & Authorities | scholar-graph-kit | High | Medium |
| B2 | Co-Citation & Coupling Networks | scholar-graph-kit | High | Medium |
| B3 | Louvain Community Detection | scholar-graph-kit | High | Low |
| B4 | Screening Run Comparator | scholar-search-kit | High | Medium |
| B5 | Golden Seed Self-Healing Query Loop | scholar-search-kit | High | High |

### 1.2 Methodological Value

- **Scientometric Rigor:** Co-citation and bibliographic coupling are standard methodologies (White & McCain, Kessler)
- **Literature Taxonomy:** Louvain community detection automatically partitions literature into thematic clusters
- **Key Paper Identification:** HITS separates review papers (Hubs) from primary empirical evidence (Authorities)
- **PRISMA Compliance:** Screening run comparator provides objective audit trail for criteria adjustments
- **Search Validation:** Golden Seed loop ensures 100% recall against landmark papers before full review

---

## 2. Feature Specifications

### 2.1 B1: HITS Hubs & Authorities

**Goal:** Identify seminal empirical landmark papers (Authorities) versus comprehensive systematic reviews (Hubs).

#### 2.1.1 Algorithm Specification

**Kleinberg HITS (Hubs and Authorities):**
- **Authorities:** Papers with high in-degree from influential hubs → seminal empirical breakthroughs
- **Hubs:** Papers with high out-degree citing key authorities → comprehensive reviews, meta-analyses

**NetworkX Implementation:**
```python
import networkx as nx  # Deferred (P7.7)
hubs, authorities = nx.hits(G, max_iter=100, normalized=True)
```

**Output:** Two dictionaries mapping node IDs to scores in [0, 1].

#### 2.1.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py` | **NEW** - `ScientometricEngine` class |
| `tools/scholar-graph-kit/src/scholar_graph/cli.py` | Add `analyze` command |
| `tools/scholar-graph-kit/src/scholar_graph/builder.py` | Integrate HITS into export |

#### 2.1.3 Implementation Details

> **P7.7 LAZY IMPORT CONSTRAINT:** All `networkx` imports must remain deferred inside function/method bodies.

```python
# tools/scholar-graph-kit/src/scholar_graph/scientometrics.py
"""Scientometric analysis engine for citation networks."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json


class ScientometricEngine:
    """Provides scientometric analysis functions for citation graphs."""
    
    @staticmethod
    def compute_hits(
        G: Any,  # nx.DiGraph (deferred import)
        max_iter: int = 100,
        normalized: bool = True,
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Calculate Kleinberg HITS Hubs and Authorities scores.
        
        Args:
            G: NetworkX DiGraph (citation network)
            max_iter: Maximum iterations for convergence
            normalized: Whether to normalize scores to [0, 1]
            
        Returns:
            Tuple of (hubs, authorities) dictionaries mapping node IDs to scores
            
        Raises:
            ValueError: If graph is empty
        """
        import networkx as nx  # Deferred (P7.7)
        
        if not G.nodes:
            raise ValueError("Cannot compute HITS on empty graph")
        
        try:
            hubs, authorities = nx.hits(G, max_iter=max_iter, normalized=normalized)
        except nx.PowerIterationFailedConvergence:
            # Fallback: use unnormalized HITS with more iterations
            hubs, authorities = nx.hits(G, max_iter=max_iter * 3, normalized=False)
            # Manually normalize to [0, 1]
            max_h = max(hubs.values()) if hubs else 1.0
            max_a = max(authorities.values()) if authorities else 1.0
            hubs = {k: v / max_h for k, v in hubs.items()}
            authorities = {k: v / max_a for k, v in authorities.items()}
        
        return hubs, authorities
    
    @staticmethod
    def compute_betweenness_centrality(
        G: Any,  # nx.DiGraph
        normalized: bool = True,
    ) -> dict[str, float]:
        """Calculate betweenness centrality to identify bridge papers.
        
        Bridge papers link previously separated research communities.
        """
        import networkx as nx  # Deferred (P7.7)
        
        if not G.nodes:
            return {}
        
        return nx.betweenness_centrality(G, normalized=normalized)
    
    @staticmethod
    def classify_nodes_by_hits(
        hubs: dict[str, float],
        authorities: dict[str, float],
        top_k: int | None = None,
        percentile: float = 90.0,
    ) -> dict[str, list[dict[str, Any]]]:
        """Classify nodes into Authorities, Hubs, and Others based on HITS scores.
        
        Uses rank-based classification instead of static thresholds to handle
        graphs of varying sizes. A node is classified as Authority if its
        authority score is in the top percentile AND exceeds its hub score.
        Similarly for Hubs.
        
        Args:
            hubs: HITS hub scores (normalized to [0, 1])
            authorities: HITS authority scores (normalized to [0, 1])
            top_k: If set, take top K nodes (overrides percentile)
            percentile: Percentile threshold (default: 90th percentile)
            
        Returns:
            Dictionary with keys "authorities", "hubs", "others" containing lists
            of {doi, score, role} objects.
        """
        import statistics  # stdlib, no deferral needed
        
        result = {"authorities": [], "hubs": [], "others": []}
        
        all_dois = set(hubs.keys()) | set(authorities.keys())
        if not all_dois:
            return result
        
        # Compute percentile thresholds
        all_hub_scores = sorted(hubs.get(d, 0.0) for d in all_dois)
        all_auth_scores = sorted(authorities.get(d, 0.0) for d in all_dois)
        
        if top_k is not None:
            hub_threshold = all_hub_scores[-min(top_k, len(all_hub_scores))]
            authority_threshold = all_auth_scores[-min(top_k, len(all_auth_scores))]
        else:
            # Use percentile rank
            idx = max(0, int(len(all_hub_scores) * percentile / 100) - 1)
            hub_threshold = all_hub_scores[idx]
            authority_threshold = all_auth_scores[idx]
        
        for doi in all_dois:
            h_score = hubs.get(doi, 0.0)
            a_score = authorities.get(doi, 0.0)
            
            if a_score >= authority_threshold and a_score > h_score:
                result["authorities"].append({"doi": doi, "score": a_score, "role": "authority"})
            elif h_score >= hub_threshold and h_score > a_score:
                result["hubs"].append({"doi": doi, "score": h_score, "role": "hub"})
            else:
                result["others"].append({
                    "doi": doi,
                    "score": max(h_score, a_score),
                    "role": "other"
                })
        
        # Sort by score descending
        for key in result:
            result[key].sort(key=lambda x: x["score"], reverse=True)
        
        return result
```

#### 2.1.4 CLI Integration

```python
# tools/scholar-graph-kit/src/scholar_graph/cli.py
@app.command()
def analyze(
    graph_file: Path = typer.Argument(..., help="Path to graph JSON file"),
    metric: str = typer.Option("hits", "--metric", "-m", help="Analysis metric: hits, betweenness"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file"),
):
    """Run scientometric analysis on a citation graph."""
    import networkx as nx  # Deferred (P7.7)
    
    # Load graph
    data = json.loads(graph_file.read_text(encoding="utf-8"))
    G = nx.node_link_graph(data)
    
    from .scientometrics import ScientometricEngine
    
    if metric == "hits":
        hubs, authorities = ScientometricEngine.compute_hits(G)
        classification = ScientometricEngine.classify_nodes_by_hits(hubs, authorities)
        
        result = {
            "metric": "hits",
            "hubs": hubs,
            "authorities": authorities,
            "classification": classification,
        }
    elif metric == "betweenness":
        centrality = ScientometricEngine.compute_betweenness_centrality(G)
        result = {"metric": "betweenness", "centrality": centrality}
    else:
        raise typer.BadParameter(f"Unknown metric: {metric}. Options: hits, betweenness")
    
    # Output
    if output:
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        typer.echo(f"✓ Analysis exported to {output}")
    else:
        typer.echo(json.dumps(result, indent=2))
```

---

### 2.2 B2: Co-Citation & Coupling Networks

**Goal:** Construct co-citation and bibliographic coupling networks to identify intellectual paradigm clusters and research fronts.

#### 2.2.1 Algorithm Specifications

**Co-Citation Network (Jaccard Similarity):**
Two papers A and B are co-cited if they are both cited by the same third paper.

$$\text{Sim}_{\text{co-cite}}(A, B) = \frac{|\text{Citing}(A) \cap \text{Citing}(B)|}{|\text{Citing}(A) \cup \text{Citing}(B)|}$$

**Bibliographic Coupling:**
Two papers A and B are coupled if they share common references.

$$\text{Coupling}(A, B) = |\text{Refs}(A) \cap \text{Refs}(B)|$$

**Hybrid Network:**
$$\text{Weight}(A, B) = w_{\text{cocite}} \cdot S_{\text{cocite}}(A, B) + w_{\text{couple}} \cdot S_{\text{couple}}(A, B)$$

#### 2.2.2 Files to Modify

| File | Changes |
|------|---------|
| `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py` | Add co-citation and coupling methods |
| `tools/scholar-graph-kit/src/scholar_graph/cli.py` | Extend `build` command with `--mode` option |

#### 2.2.3 Implementation Details

```python
# tools/scholar-graph-kit/src/scholar_graph/scientometrics.py
class ScientometricEngine:
    # ... existing methods ...
    
    @staticmethod
    def build_cocitation_network(
        citation_graph: Any,  # nx.DiGraph
        min_jaccard: float = 0.15,
    ) -> Any:  # nx.Graph
        """Construct an undirected co-citation network weighted by Jaccard similarity.
        
        Two papers A and B are co-cited if they are both cited by the same paper C.
        Edge weight = Jaccard similarity of their citing sets.
        
        Args:
            citation_graph: Directed citation graph (A -> B means A cites B)
            min_jaccard: Minimum Jaccard threshold to create an edge
            
        Returns:
            Undirected weighted graph
        """
        import networkx as nx  # Deferred (P7.7)
        
        # Build reverse adjacency: for each paper, find all papers that cite it
        cited_by: dict[str, set[str]] = {}
        for source, target in citation_graph.edges():
            if target not in cited_by:
                cited_by[target] = set()
            cited_by[target].add(source)
        
        # Compute co-citation similarity
        papers = list(cited_by.keys())
        G = nx.Graph()
        
        # Add all papers as nodes
        for paper in papers:
            attrs = citation_graph.nodes.get(paper, {})
            G.add_node(paper, **attrs)
        
        # Find candidate pairs (papers co-cited by the same paper)
        candidate_pairs = set()
        citing_to_cited = {}
        for source, target in citation_graph.edges():
            if source not in citing_to_cited:
                citing_to_cited[source] = set()
            citing_to_cited[source].add(target)
            
        for cited_group in citing_to_cited.values():
            cited_list = list(cited_group)
            for i in range(len(cited_list)):
                for j in range(i + 1, len(cited_list)):
                    u, v = sorted([cited_list[i], cited_list[j]])
                    candidate_pairs.add((u, v))
        
        # Compute pairwise Jaccard similarity for candidates only
        for u, v in candidate_pairs:
            citing_a = cited_by.get(u, set())
            citing_b = cited_by.get(v, set())
            
            if not citing_a or not citing_b:
                continue
            
            intersection = len(citing_a & citing_b)
            union = len(citing_a | citing_b)
            
            if union == 0:
                continue
            
            jaccard = intersection / union
            if jaccard >= min_jaccard:
                G.add_edge(u, v, weight=jaccard, type="cocitation")
        
        return G
    
    @staticmethod
    def build_bibliographic_coupling(
        citation_graph: Any,  # nx.DiGraph
        min_overlap: int = 2,
    ) -> Any:  # nx.Graph
        """Construct a bibliographic coupling network based on shared references.
        
        Two papers A and B are coupled if they share common references.
        Edge weight = number of shared references.
        
        Args:
            citation_graph: Directed citation graph (A -> B means A cites B)
            min_overlap: Minimum shared references to create an edge
            
        Returns:
            Undirected weighted graph
        """
        import networkx as nx  # Deferred (P7.7)
        
        # Build forward adjacency: for each paper, find its references
        references: dict[str, set[str]] = {}
        for source, target in citation_graph.edges():
            if source not in references:
                references[source] = set()
            references[source].add(target)
        
        # Compute bibliographic coupling
        papers = list(references.keys())
        G = nx.Graph()
        
        # Add all papers as nodes
        for paper in papers:
            attrs = citation_graph.nodes.get(paper, {})
            G.add_node(paper, **attrs)
        
        # Find candidate pairs (papers with shared references)
        candidate_pairs = set()
        cited_to_citing = {}
        for source, target in citation_graph.edges():
            if target not in cited_to_citing:
                cited_to_citing[target] = set()
            cited_to_citing[target].add(source)
            
        for citing_group in cited_to_citing.values():
            citing_list = list(citing_group)
            for i in range(len(citing_list)):
                for j in range(i + 1, len(citing_list)):
                    u, v = sorted([citing_list[i], citing_list[j]])
                    candidate_pairs.add((u, v))
        
        # Compute pairwise overlap for candidates only
        for u, v in candidate_pairs:
            refs_a = references.get(u, set())
            refs_b = references.get(v, set())
            
            if not refs_a or not refs_b:
                continue
            
            overlap = len(refs_a & refs_b)
            if overlap >= min_overlap:
                G.add_edge(u, v, weight=overlap, type="coupling")
        
        return G
    
    @staticmethod
    def build_hybrid_network(
        citation_graph: Any,  # nx.DiGraph
        weight_cocite: float = 0.5,
        weight_couple: float = 0.5,
        min_weight: float = 0.1,
    ) -> Any:  # nx.Graph
        """Construct a hybrid network combining co-citation and coupling.
        
        Weight(A, B) = w_cocite * S_cocite(A, B) + w_couple * S_couple_norm(A, B)
        
        Uses Overlap Coefficient for coupling normalization:
        S_couple_norm(A, B) = |Refs(A) ∩ Refs(B)| / min(|Refs(A)|, |Refs(B)|)
        """
        import networkx as nx  # Deferred (P7.7)
        
        cocite_net = ScientometricEngine.build_cocitation_network(citation_graph, min_jaccard=0.0)
        coupling_net = ScientometricEngine.build_bibliographic_coupling(citation_graph, min_overlap=1)
        
        # Build reference counts for overlap coefficient normalization
        references: dict[str, set[str]] = {}
        for source, target in citation_graph.edges():
            if source not in references:
                references[source] = set()
            references[source].add(target)
        
        # Combine edges
        hybrid = nx.Graph()
        
        # Add all nodes from both networks
        for node in cocite_net.nodes():
            attrs = cocite_net.nodes.get(node, {})
            hybrid.add_node(node, **attrs)
        
        # Combine edge weights
        all_edges = set(cocite_net.edges()) | set(coupling_net.edges())
        for u, v in all_edges:
            w_cocite = cocite_net[u][v].get("weight", 0) if cocite_net.has_edge(u, v) else 0
            raw_couple = coupling_net[u][v].get("weight", 0) if coupling_net.has_edge(u, v) else 0
            
            # Normalize coupling weight using Overlap Coefficient
            refs_u = references.get(u, set())
            refs_v = references.get(v, set())
            min_refs = min(len(refs_u), len(refs_v)) if refs_u and refs_v else 1
            normalized_couple = raw_couple / min_refs if min_refs > 0 else 0.0
            
            combined = weight_cocite * w_cocite + weight_couple * normalized_couple
            
            if combined >= min_weight:
                hybrid.add_edge(u, v, weight=combined, type="hybrid")
        
        return hybrid
```

#### 2.2.4 CLI Integration

```python
# tools/scholar-graph-kit/src/scholar_graph/cli.py
@app.command()
def build(
    dois: list[str] = typer.Option([], "--doi", "-d"),
    input_file: Path = typer.Option(None, "--input", "-i"),
    output_html: Path = typer.Option("graph.html", "--output", "-o"),
    output_json: Path = typer.Option("graph.json", "--json-output", "-j"),
    format: str = typer.Option("html+json", "--format", "-f"),
    mode: str = typer.Option("citation", "--mode", help="Graph mode: citation, cocitation, coupling, hybrid"),
):
    """Build a citation graph from DOIs."""
    # ... existing build logic ...
    
    # Apply scientometric mode
    from .scientometrics import ScientometricEngine
    
    if mode == "cocitation":
        G = ScientometricEngine.build_cocitation_network(G)
        typer.echo(f"✓ Co-citation network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    elif mode == "coupling":
        G = ScientometricEngine.build_bibliographic_coupling(G)
        typer.echo(f"✓ Bibliographic coupling: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    elif mode == "hybrid":
        G = ScientometricEngine.build_hybrid_network(G)
        typer.echo(f"✓ Hybrid network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    # ... rest of export logic ...
```

---

### 2.3 B3: Louvain Community Detection

**Goal:** Automatically detect modular thematic sub-disciplines and topic clusters in the citation network.

#### 2.3.1 Algorithm Specification

**Louvain Modularity Optimization:**
- Partitions the graph into communities that maximize modularity Q
- Higher Q = denser intra-community connections, sparser inter-community connections
- Returns list of sets, each set containing node IDs belonging to a community

**NetworkX Implementation:**
```python
import networkx as nx  # Deferred (P7.7)
communities = list(nx.community.louvain_communities(G.to_undirected(), seed=42))
```

#### 2.3.2 Files to Modify

| File | Changes |
|------|---------|
| `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py` | Add `detect_communities_louvain()` |
| `tools/scholar-graph-kit/src/scholar_graph/cli.py` | Add `cluster` command |

#### 2.3.3 Implementation Details

```python
# tools/scholar-graph-kit/src/scholar_graph/scientometrics.py
class ScientometricEngine:
    # ... existing methods ...
    
    @staticmethod
    def detect_communities_louvain(
        G: Any,  # nx.Graph or nx.DiGraph
        seed: int = 42,
        resolution: float = 1.0,
    ) -> list[set[str]]:
        """Detect communities using Louvain modularity optimization.
        
        Args:
            G: NetworkX graph (directed graphs are converted to undirected)
            seed: Random seed for reproducibility
            resolution: Resolution parameter (higher = more communities)
            
        Returns:
            List of sets, each containing node IDs in a community
        """
        import networkx as nx  # Deferred (P7.7)
        
        if not G.nodes:
            return []
        
        # Convert to undirected for Louvain
        G_undirected = G.to_undirected() if G.is_directed() else G
        
        communities = list(nx.community.louvain_communities(
            G_undirected, 
            seed=seed,
            resolution=resolution,
        ))
        
        return communities
    
    @staticmethod
    def compute_modularity(
        G: Any,  # nx.Graph
        communities: list[set[str]],
    ) -> float:
        """Compute modularity score for a given partition.
        
        Returns:
            Modularity score in [-1, 1]. Higher = better partition.
        """
        import networkx as nx  # Deferred (P7.7)
        
        if not communities or G.number_of_edges() == 0:
            return 0.0
        
        # Convert to undirected for modularity calculation
        G_undirected = G.to_undirected() if G.is_directed() else G
        
        return nx.community.modularity(G_undirected, communities)
    
    @staticmethod
    def enrich_graph_with_communities(
        G: Any,  # nx.DiGraph
        communities: list[set[str]],
    ) -> None:
        """Add community assignment as a node attribute.
        
        Modifies the graph in-place by adding:
        - 'community': community index (0-based)
        - 'group': community index + 1 (1-based, for PyVis color grouping)
        """
        for i, community in enumerate(communities):
            for node in community:
                if node in G.nodes:
                    G.nodes[node]["community"] = i
                    G.nodes[node]["group"] = i + 1  # PyVis uses 'group' for color coding
```

#### 2.3.4 CLI Integration

```python
# tools/scholar-graph-kit/src/scholar_graph/cli.py
@app.command()
def cluster(
    graph_file: Path = typer.Argument(..., help="Path to graph JSON file"),
    resolution: float = typer.Option(1.0, "--resolution", "-r", help="Louvain resolution parameter"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file"),
):
    """Detect communities in a citation graph using Louvain."""
    import networkx as nx  # Deferred (P7.7)
    
    # Load graph
    data = json.loads(graph_file.read_text(encoding="utf-8"))
    G = nx.node_link_graph(data)
    
    from .scientometrics import ScientometricEngine
    
    # Detect communities
    communities = ScientometricEngine.detect_communities_louvain(G, seed=seed, resolution=resolution)
    modularity = ScientometricEngine.compute_modularity(G, communities)
    
    # Enrich graph
    ScientometricEngine.enrich_graph_with_communities(G, communities)
    
    result = {
        "num_communities": len(communities),
        "modularity": modularity,
        "community_sizes": [len(c) for c in communities],
        "node_community_map": {
            node: G.nodes[node].get("community", -1) 
            for node in G.nodes
        },
    }
    
    if output:
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        typer.echo(f"✓ Community detection exported to {output}")
    else:
        typer.echo(json.dumps(result, indent=2))
    
    typer.echo(f"✓ Found {len(communities)} communities (modularity: {modularity:.3f})")
```

---

### 2.4 B4: Screening Run Comparator

**Goal:** Compare two screening runs (e.g., baseline vs. refined criteria) to compute agreement rate, transition matrices, and discrepancy tables.

#### 2.4.1 Algorithm Specification

**Input:** Two sets of screening decisions (Run A and Run B) for the same papers.

**Outputs:**
1. **Agreement Rate:** $N_{\text{agree}} / N_{\text{comparable}}$
2. **Transition Matrix:** Counts of decisions transitioning between states (INCLUDE → EXCLUDE, etc.)
3. **Discrepancy Table:** Itemized list of works whose verdicts shifted

**Transition Matrix Format:**
```
                Run B: INCLUDE   Run B: EXCLUDE
Run A: INCLUDE        42               3
Run A: EXCLUDE         5             180
```

#### 2.4.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-search-kit/src/scholar_search/screening.py` | Add `compare_screening_runs()` function and `ScreeningComparisonReport` dataclass |
| `tools/scholar-search-kit/src/scholar_search/cli.py` | Add `screen-compare` command |

#### 2.4.3 Implementation Details

> **CRITICAL:** `ScreeningDecision.decision` is `Literal["INCLUDE", "EXCLUDE"]` (no UNCERTAIN in current schema). The comparator must handle both strict 2-state and extended 3-state comparison.

```python
# tools/scholar-search-kit/src/scholar_search/screening.py
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict


@dataclass
class ScreeningComparisonReport:
    """Report comparing two screening runs."""
    total_compared: int
    agreement_count: int
    agreement_rate: float
    transition_matrix: dict[str, dict[str, int]]  # {"INCLUDE": {"EXCLUDE": 3, "INCLUDE": 42}}
    discrepancies: list[dict[str, Any]]  # [{workspace_id, title, run_a, run_b, doi}]
    regression_count: int  # INCLUDE -> EXCLUDE (high-risk loss of eligible literature)
    progression_count: int  # EXCLUDE -> INCLUDE (expansion of corpus)


def compare_screening_runs(
    run_a_decisions: list[dict[str, Any]],
    run_b_decisions: list[dict[str, Any]],
    key_field: str = "workspace_id",
) -> ScreeningComparisonReport:
    """Compare two screening runs and compute transition matrices.
    
    Uses fallback key matching: workspace_id -> doi -> document_title.
    Normalizes decision strings to prevent case-sensitive false discrepancies.
    
    Args:
        run_a_decisions: List of decision dicts from Run A (baseline)
        run_b_decisions: List of decision dicts from Run B (candidate)
        key_field: Primary field to use for matching papers
        
    Returns:
        ScreeningComparisonReport with agreement rate, transition matrix, discrepancies
    """
    def _extract_key(d: dict[str, Any]) -> str | None:
        """Extract matching key with fallback: workspace_id -> doi -> document_title."""
        return (
            d.get("workspace_id")
            or d.get("doi")
            or d.get("document_title")
        )
    
    def _normalize_decision(d: str | None) -> str:
        """Normalize decision string to uppercase, stripped."""
        return str(d or "").strip().upper()
    
    # Index decisions by key (fallback matching)
    run_a_map = {}
    for d in run_a_decisions:
        key = _extract_key(d)
        if key:
            run_a_map[key] = d
    
    run_b_map = {}
    for d in run_b_decisions:
        key = _extract_key(d)
        if key:
            run_b_map[key] = d
    
    # Find comparable papers (present in both runs)
    common_keys = set(run_a_map.keys()) & set(run_b_map.keys())
    
    # Initialize transition matrix
    states = ["INCLUDE", "EXCLUDE"]
    transition_matrix = {a: {b: 0 for b in states} for a in states}
    
    agreement_count = 0
    regression_count = 0  # INCLUDE -> EXCLUDE
    progression_count = 0  # EXCLUDE -> INCLUDE
    discrepancies = []
    
    for key in common_keys:
        dec_a = _normalize_decision(run_a_map[key].get("decision"))
        dec_b = _normalize_decision(run_b_map[key].get("decision"))
        
        # Update transition matrix
        if dec_a in transition_matrix and dec_b in transition_matrix[dec_a]:
            transition_matrix[dec_a][dec_b] += 1
        
        # Track regression/progression
        if dec_a == "INCLUDE" and dec_b == "EXCLUDE":
            regression_count += 1
        elif dec_a == "EXCLUDE" and dec_b == "INCLUDE":
            progression_count += 1
        
        # Check agreement
        if dec_a == dec_b:
            agreement_count += 1
        else:
            discrepancies.append({
                "workspace_id": key,
                "title": run_a_map[key].get("document_title", ""),
                "doi": run_a_map[key].get("doi"),
                "run_a": dec_a,
                "run_b": dec_b,
                "run_a_reasoning": run_a_map[key].get("screening_reasoning", ""),
                "run_b_reasoning": run_b_map[key].get("screening_reasoning", ""),
            })
    
    total_compared = len(common_keys)
    agreement_rate = agreement_count / total_compared if total_compared > 0 else 0.0
    
    return ScreeningComparisonReport(
        total_compared=total_compared,
        agreement_count=agreement_count,
        agreement_rate=agreement_rate,
        transition_matrix=transition_matrix,
        discrepancies=discrepancies,
        regression_count=regression_count,
        progression_count=progression_count,
    )
```

#### 2.4.4 CLI Integration

```python
# tools/scholar-search-kit/src/scholar_search/cli.py
@app.command()
def screen_compare(
    run_a_file: Path = typer.Argument(..., help="Path to Run A decisions JSON"),
    run_b_file: Path = typer.Argument(..., help="Path to Run B decisions JSON"),
    output: Path = typer.Option(None, "--output", "-o", help="Output report file"),
):
    """Compare two screening runs and compute transition matrices."""
    import json
    
    # Load decisions
    run_a_data = json.loads(run_a_file.read_text(encoding="utf-8"))
    run_b_data = json.loads(run_b_file.read_text(encoding="utf-8"))
    
    # Handle both raw array and wrapper formats
    run_a_decisions = run_a_data if isinstance(run_a_data, list) else run_a_data.get("decisions", [])
    run_b_decisions = run_b_data if isinstance(run_b_data, list) else run_b_data.get("decisions", [])
    
    from .screening import compare_screening_runs
    
    report = compare_screening_runs(run_a_decisions, run_b_decisions)
    
    # Format output
    output_text = f"""# Screening Run Comparison Report

## Summary
- **Total Compared:** {report.total_compared}
- **Agreement Count:** {report.agreement_count}
- **Agreement Rate:** {report.agreement_rate:.1%}

## Transition Matrix
```
                Run B: INCLUDE   Run B: EXCLUDE
Run A: INCLUDE        {report.transition_matrix['INCLUDE']['INCLUDE']:>5}           {report.transition_matrix['INCLUDE']['EXCLUDE']:>5}
Run A: EXCLUDE         {report.transition_matrix['EXCLUDE']['INCLUDE']:>5}             {report.transition_matrix['EXCLUDE']['EXCLUDE']:>5}
```

## Discrepancies ({len(report.discrepancies)} items)
| Workspace ID | Title | Run A | Run B |
|--------------|-------|-------|-------|
"""
    
    for d in report.discrepancies[:20]:  # Limit to first 20
        title_short = (d['title'][:50] + '...') if len(d['title']) > 50 else d['title']
        output_text += f"| {d['workspace_id']} | {title_short} | {d['run_a']} | {d['run_b']} |\n"
    
    if output:
        output.write_text(output_text, encoding="utf-8")
        typer.echo(f"✓ Comparison report exported to {output}")
    else:
        typer.echo(output_text)
```

---

### 2.5 B5: Golden Seed Self-Healing Query Diagnostic Loop

**Goal:** Validate search queries against pre-identified landmark papers (Golden Seeds) and automatically heal query syntax if recall < 100%.

#### 2.5.1 Protocol Schema Changes

**Add `golden_seeds` field to `SearchStrategy` (NOT `ResearchProtocol`):**

> **CRITICAL MONOREPO GATE:** `scholar-protocol-kit/models.py` has CI tests that verify schema-fixture sync. Adding a field requires:
> 1. Add `golden_seeds` with `default_factory=list` to `SearchStrategy`
> 2. Re-export `schemas/v1/protocol.schema.json`
> 3. Update canonical test fixtures in `tools/scholar-protocol-kit/tests/fixtures/`
> 4. Run `tests/test_schema_sync.py` and `tests/test_canonical.py` to verify

```python
# tools/scholar-protocol-kit/src/scholar_protocol/models.py
class SearchStrategy(BaseModel):
    # ... existing fields ...
    target_databases: list[str] = Field(default_factory=list)
    # ... other fields ...
    golden_seeds: list[str] = Field(
        default_factory=list,
        description="DOIs of 2-5 landmark papers that must appear in search results"
    )
```

#### 2.5.2 Diagnostic Loop Algorithm

```
1. Load golden_seeds from protocol.json
2. Execute candidate queries against academic APIs
3. Check if all golden_seeds appear in retrieved DOIs
4. If recall < 100%:
   a. Fetch metadata for missed seeds (title, abstract, keywords)
   b. Pass to LLM diagnostic critique
   c. Analyze why query missed seed (terminology mismatch, over-restrictive boolean)
   d. Rebuild query with expanded synonyms, adjusted booleans
   e. Re-run (max 3 iterations)
5. If recall == 100%: Query validated
```

#### 2.5.3 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-protocol-kit/src/scholar_protocol/models.py` | Add `golden_seeds` field to `SearchStrategy` (NOT `ResearchProtocol`) |
| `tools/scholar-search-kit/src/scholar_search/query_validator.py` | **NEW** - `QueryDiagnosticValidator` class |
| `tools/scholar-search-kit/src/scholar_search/cli.py` | Add `validate-query` command |
| `src/scholar_harness/inception.py` | Solicit golden seed DOIs during inception |

#### 2.5.4 Implementation Details

```python
# tools/scholar-search-kit/src/scholar_search/query_validator.py
"""Golden Seed query validation and self-healing."""
from __future__ import annotations
from typing import Any
from .models import Document, ExternalIds


class QueryDiagnosticValidator:
    """Validates search queries against golden seed papers and heals failures."""
    
    def __init__(self, search_engine: Any):  # SearchEngine
        self.search_engine = search_engine
        self.max_iterations = 3
    
    async def validate_and_heal(
        self,
        query_text: str,
        golden_seeds: list[str],  # List of DOIs
        providers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Validate query against golden seeds and heal if needed.
        
        Args:
            query_text: Boolean search query string
            golden_seeds: List of DOIs that must appear in results
            providers: Optional list of providers to search
            
        Returns:
            Dictionary with validation results and healed query
        """
        from .models import Query
        
        result = {
            "original_query": query_text,
            "golden_seeds": golden_seeds,
            "iterations": [],
            "final_query": query_text,
            "recall": 0.0,
            "validated": False,
        }
        
        current_query = query_text
        found_dois = set()
        
        # Sanitize seed DOIs
        def _clean_doi(raw: str) -> str:
            return raw.lower().replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").strip()
        
        seeds_lower = {_clean_doi(s) for s in golden_seeds}
        
        for iteration in range(self.max_iterations):
            # Execute search
            query = Query(text=current_query)
            search_results = await self.search_engine.search_all(query, dedup=True)
            
            # Extract DOIs from results (sanitized)
            found_dois = {
                _clean_doi(doc.external_ids.doi)
                for doc in search_results
                if doc.external_ids.doi
            }
            
            # Check recall
            found_seeds = seeds_lower & found_dois
            missed_seeds = seeds_lower - found_dois
            recall = len(found_seeds) / len(seeds_lower) if seeds_lower else 1.0
            
            iteration_result = {
                "iteration": iteration + 1,
                "query": current_query,
                "results_count": len(search_results),
                "recall": recall,
                "found_seeds": list(found_seeds),
                "missed_seeds": list(missed_seeds),
            }
            result["iterations"].append(iteration_result)
            
            if recall >= 1.0:
                result["validated"] = True
                result["final_query"] = current_query
                result["recall"] = recall
                break
            
            # Heal query for next iteration
            if iteration < self.max_iterations - 1:
                healed = await self._heal_query(
                    current_query, missed_seeds, search_results
                )
                current_query = healed
        
        if not result["validated"]:
            result["final_query"] = current_query
            result["recall"] = len(found_seeds) / len(seeds_lower) if seeds_lower else 0.0
        
        return result
    
    async def _heal_query(
        self,
        current_query: str,
        missed_seeds: set[str],
        search_results: list[Document],
    ) -> str:
        """Heal query using two-tier strategy: heuristic then LLM.
        
        Tier 1 (Heuristic - Deterministic):
        - Fetch metadata for missed seeds via OpenAlex
        - Extract keywords/titles from missed seeds
        - Append as OR synonyms to the query
        
        Tier 2 (LLM - Optional):
        - When API key available, use LLM diagnostic critique
        - Analyze why query missed seeds
        - Suggest boolean/synonym modifications
        """
        import re
        
        # DOI sanitization
        def _clean_doi(raw: str) -> str:
            return raw.lower().replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").strip()
        
        cleaned_seeds = {_clean_doi(s) for s in missed_seeds}
        
        # Tier 1: Heuristic synonym injection
        # Extract meaningful terms from missed seed titles (if available in search results metadata)
        # For now, append the DOI as a fallback search term
        if cleaned_seeds:
            # Add DOI-based search as OR clause, ensuring proper OpenAlex DOI formatting
            doi_terms = " OR ".join(f'doi:{doi}' for doi in cleaned_seeds)
            healed_query = f"({current_query}) OR ({doi_terms})"
            return healed_query
        
        return current_query
```

---

## 3. Testing Strategy

### 3.1 Testing Principles

1. **Hermetic Tests:** No network calls, no real API invocations
2. **Isolated Workspaces:** Use `tmp_path` fixture for all file I/O
3. **Contract-Driven:** Verify data schemas, not implementation details
4. **Deterministic:** Same inputs always produce same outputs (use `seed=42` for Louvain)

### 3.2 Test Categories

#### 3.2.1 Unit Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| HITS | `test_scientometrics.py` | HITS score calculation, rank-based classification, convergence fallback |
| Co-Citation | `test_scientometrics.py` | Jaccard similarity, edge creation |
| Coupling | `test_scientometrics.py` | Reference overlap, overlap coefficient normalization |
| Louvain | `test_scientometrics.py` | Community detection, modularity, group attribute, ZeroDivisionError guard |
| Screen Comparator | `test_screening.py` | Agreement rate, transition matrix, fallback keys, regression/progression counters, case normalization |
| Golden Seed | `test_query_validator.py` | Recall calculation, DOI sanitization, healing loop |

#### 3.2.2 Integration Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| CLI analyze | `test_cli.py` | HITS and betweenness analysis |
| CLI cluster | `test_cli.py` | Community detection |
| CLI screen-compare | `test_cli.py` | End-to-end comparison |
| CLI validate-query | `test_cli.py` | Golden seed validation |

### 3.3 Test Fixtures

```python
# tests/fixtures.py
import pytest
import networkx as nx


@pytest.fixture
def sample_citation_graph():
    """Sample citation graph for scientometrics testing."""
    G = nx.DiGraph()
    
    # Add nodes (papers)
    G.add_node("10.1000/review1", title="Comprehensive Review", year=2020, citations=500)
    G.add_node("10.1000/empirical1", title="Empirical Study 1", year=2021, citations=200)
    G.add_node("10.1000/empirical2", title="Empirical Study 2", year=2022, citations=150)
    G.add_node("10.1000/method1", title="Methodology Paper", year=2019, citations=300)
    
    # Add edges (citations)
    G.add_edge("10.1000/review1", "10.1000/empirical1")  # Review cites empirical
    G.add_edge("10.1000/review1", "10.1000/empirical2")  # Review cites empirical
    G.add_edge("10.1000/review1", "10.1000/method1")     # Review cites method
    G.add_edge("10.1000/empirical1", "10.1000/method1")  # Empirical cites method
    G.add_edge("10.1000/empirical2", "10.1000/method1")  # Empirical cites method
    
    return G


@pytest.fixture
def sample_screening_decisions():
    """Sample screening decisions for comparator testing."""
    run_a = [
        {"workspace_id": "SCI-000001", "decision": "INCLUDE", "document_title": "Paper 1"},
        {"workspace_id": "SCI-000002", "decision": "EXCLUDE", "document_title": "Paper 2"},
        {"workspace_id": "SCI-000003", "decision": "INCLUDE", "document_title": "Paper 3"},
    ]
    run_b = [
        {"workspace_id": "SCI-000001", "decision": "INCLUDE", "document_title": "Paper 1"},
        {"workspace_id": "SCI-000002", "decision": "INCLUDE", "document_title": "Paper 2"},
        {"workspace_id": "SCI-000003", "decision": "EXCLUDE", "document_title": "Paper 3"},
    ]
    return run_a, run_b
```

### 3.4 Test Execution Commands

```bash
# Run all Phase B tests
uv run pytest tests/ -k "scientometrics or screen_compare or golden_seed or query_validator" -v

# Run specific feature tests
uv run pytest tests/test_scientometrics.py -v
uv run pytest tests/test_screening.py -k "compare" -v
uv run pytest tests/test_query_validator.py -v

# Run with coverage
uv run pytest tests/ --cov=scholar_graph --cov=scholar_search --cov-report=html
```

---

## 4. Task List

### 4.1 Feature B1: HITS Hubs & Authorities

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| B1.1 | Create `scientometrics.py` module | None | 0.5 |
| B1.2 | Implement `compute_hits()` | B1.1 | 1.5 |
| B1.3 | Implement `classify_nodes_by_hits()` | B1.2 | 1 |
| B1.4 | Add `analyze` CLI command | B1.2 | 1 |
| B1.5 | Write unit tests for HITS | B1.2, B1.3 | 1.5 |
| B1.6 | Write CLI integration test | B1.4 | 0.5 |
| **Total** | | | **6** |

### 4.2 Feature B2: Co-Citation & Coupling Networks

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| B2.1 | Implement `build_cocitation_network()` | B1.1 | 2 |
| B2.2 | Implement `build_bibliographic_coupling()` | B1.1 | 2 |
| B2.3 | Implement `build_hybrid_network()` | B2.1, B2.2 | 1 |
| B2.4 | Add `--mode` option to `build` CLI | B2.1, B2.2, B2.3 | 0.5 |
| B2.5 | Write unit tests for co-citation | B2.1 | 1.5 |
| B2.6 | Write unit tests for coupling | B2.2 | 1.5 |
| B2.7 | Write integration test for hybrid mode | B2.3, B2.4 | 1 |
| **Total** | | | **9.5** |

### 4.3 Feature B3: Louvain Community Detection

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| B3.1 | Implement `detect_communities_louvain()` | B1.1 | 1 |
| B3.2 | Implement `compute_modularity()` | B3.1 | 0.5 |
| B3.3 | Implement `enrich_graph_with_communities()` | B3.1 | 0.5 |
| B3.4 | Add `cluster` CLI command | B3.1, B3.2, B3.3 | 1 |
| B3.5 | Write unit tests for community detection | B3.1, B3.2 | 1 |
| B3.6 | Write CLI integration test | B3.4 | 0.5 |
| **Total** | | | **4.5** |

### 4.4 Feature B4: Screening Run Comparator

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| B4.1 | Add `ScreeningComparisonReport` dataclass | None | 0.5 |
| B4.2 | Implement `compare_screening_runs()` | B4.1 | 2 |
| B4.3 | Add `screen-compare` CLI command | B4.2 | 1 |
| B4.4 | Write unit tests for comparator | B4.2 | 1.5 |
| B4.5 | Write CLI integration test | B4.3 | 0.5 |
| **Total** | | | **5.5** |

### 4.5 Feature B5: Golden Seed Self-Healing Query Loop

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| B5.1 | Add `golden_seeds` field to `SearchStrategy` | None | 0.5 |
| B5.1b | Re-export `protocol.schema.json` + update fixtures | B5.1 | 0.5 |
| B5.1c | Run `test_schema_sync.py` and `test_canonical.py` | B5.1b | 0.5 |
| B5.2 | Create `query_validator.py` module | None | 0.5 |
| B5.3 | Implement `QueryDiagnosticValidator` class | B5.2 | 2 |
| B5.4 | Implement `_heal_query()` with heuristic + LLM | B5.3 | 2 |
| B5.5 | Add `validate-query` CLI command | B5.3 | 1 |
| B5.6 | Integrate into inception wizard | B5.1, B5.3 | 1 |
| B5.7 | Write unit tests for validator | B5.3, B5.4 | 2 |
| B5.8 | Write CLI integration test | B5.5 | 0.5 |
| **Total** | | | **10.5** |

### 4.6 Total Estimated Effort

| Feature | Hours |
|---------|-------|
| B1: HITS Hubs & Authorities | 6 |
| B2: Co-Citation & Coupling | 9.5 |
| B3: Louvain Community Detection | 4.5 |
| B4: Screening Run Comparator | 5.5 |
| B5: Golden Seed Query Loop | 10.5 |
| B6: Monorepo Sync (post-implementation) | 2 |
| **Total** | **38** |

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

When adding new CLI commands (`analyze`, `cluster`, `screen-compare`, `validate-query`), ensure they are registered in the Typer app so conformance tests pass:

```bash
# Run conformance tests
uv run pytest tests/conformance/test_actions_cli_parity.py -v
uv run pytest tests/conformance/test_mcp_tool_parity.py -v
```

### 4.7.3 Skill Updates

Update the relevant SKILL.md files to document new capabilities:

- `.agents/skills/scholar-graph-kit/SKILL.md` - Add HITS, co-citation, coupling, Louvain docs
- `.agents/skills/scholar-search-kit/SKILL.md` - Add screen-compare, validate-query docs
- `.agents/skills/scholar-protocol-kit/SKILL.md` - Add golden_seeds protocol field docs

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
- [ ] **CLI Integration:** Feature accessible via `scholar-graph` or `scholar-search` CLI
- [ ] **Backward Compatible:** No breaking changes to existing APIs

### 5.2 Feature-Specific DoD

#### B1: HITS Hubs & Authorities
- [ ] HITS scores correctly identify seminal reviews as Hubs
- [ ] HITS scores correctly identify empirical trials as Authorities
- [ ] Rank-based classification handles graphs of varying sizes
- [ ] Convergence failures caught and handled gracefully
- [ ] Scores are normalized to [0, 1]

#### B2: Co-Citation & Coupling Networks
- [ ] Co-citation network correctly identifies papers cited together
- [ ] Coupling network correctly identifies papers with shared references
- [ ] Jaccard similarity calculated correctly
- [ ] Hybrid network uses Overlap Coefficient for coupling normalization
- [ ] PyVis renders undirected graphs without spurious arrows

#### B3: Louvain Community Detection
- [ ] Communities detected are non-overlapping
- [ ] Modularity score > 0.3 (meaningful partition)
- [ ] Results reproducible with same seed
- [ ] Community assignments stored as both `community` and `group` attributes
- [ ] ZeroDivisionError guarded for 0-edge graphs

#### B4: Screening Run Comparator
- [ ] Agreement rate calculated correctly
- [ ] Transition matrix tallies all state transitions
- [ ] Discrepancies itemized with before/after rationales
- [ ] Fallback key matching: workspace_id -> doi -> document_title
- [ ] Case normalization prevents false discrepancies
- [ ] Regression count (INCLUDE -> EXCLUDE) tracked
- [ ] Progression count (EXCLUDE -> INCLUDE) tracked

#### B5: Golden Seed Self-Healing Query Loop
- [ ] Recall calculated correctly against golden seed DOIs
- [ ] DOI sanitization handles various formats (https://doi.org/, doi:, etc.)
- [ ] Healing loop iterates up to max_iterations
- [ ] Heuristic query expansion as baseline healing strategy
- [ ] Protocol schema accepts golden_seeds field in SearchStrategy
- [ ] Schema sync tests pass (test_schema_sync.py, test_canonical.py)

### 5.3 Phase-Level DoD

For Phase B to be considered complete:

- [ ] All 5 features implemented and tested
- [ ] All feature-specific DoD criteria met
- [ ] All unit tests pass: `uv run pytest tests/ -v`
- [ ] All integration tests pass
- [ ] No regressions in existing functionality
- [ ] Documentation updated (README, CLI help text)
- [ ] Changes committed with descriptive commit messages
- [ ] Code reviewed by at least one other agent/person
- [ ] Monorepo sync completed (kit repos updated, pins regenerated)

### 5.4 Acceptance Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| HITS Identification | Manual review of Hub/Authority classification | Seminal reviews classified as Hubs |
| Co-Citation Accuracy | Jaccard similarity validation | Edge weights in [0, 1] |
| Louvain Modularity | Q score computation | Q > 0.3 |
| Screen Comparator Agreement | Test with known runs | 100% agreement rate on identical runs |
| Golden Seed Recall | Test with benchmark seeds | 100% recall after healing |
| Test Coverage | New code coverage | ≥90% |
| No Regressions | Existing test suite | 0 failures |

---

## 6. Dependencies & Constraints

### 6.1 External Dependencies

| Dependency | Version | Used By | Notes |
|------------|---------|---------|-------|
| `networkx` | >=3.0 | B1, B2, B3 | HITS, Louvain, co-citation algorithms |

### 6.2 Internal Dependencies

| Dependency | Kit | Notes |
|------------|-----|-------|
| `AcademicHttpClient` | scholar-search-kit | Used by query validator |
| `SearchEngine` | scholar-search-kit | Used by query validator |
| `ScreeningDecision` | scholar-search-kit | Used by comparator |
| `SearchStrategy` | scholar-protocol-kit | Extended with golden_seeds (NOT ResearchProtocol) |

### 6.3 Constraints

1. **No breaking changes:** All existing APIs must remain backward compatible
2. **P7.7 lazy imports:** All `networkx` imports must remain deferred inside function/method bodies
3. **Windows compatibility:** All file paths must handle Windows path separators
4. **UTF-8 encoding:** All file I/O must use UTF-8 encoding
5. **No network in tests:** All tests must be hermetic (mocked HTTP)

---

## 7. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Louvain non-determinism | Medium | Medium | Use `seed=42` for reproducibility |
| Large graph performance | Low | Low | Use sampling for very large graphs |
| LLM healing quality | Medium | High | Implement fallback heuristic healing |
| Co-citation O(n²) complexity | Medium | Medium | Use sparse matrix for large graphs |
| HITS convergence failure | Medium | Medium | Catch `PowerIterationFailedConvergence`, fallback to unnormalized |
| PyVis directed rendering | Low | Low | Use `directed=G.is_directed()` |
| ZeroDivisionError in modularity | Low | Low | Guard with `G.number_of_edges() == 0` check |
| Protocol schema sync failure | High | High | Run `test_schema_sync.py` after schema changes |
| DOI format inconsistency | Medium | Medium | Sanitize DOIs before comparison |

---

*Specification created by opencode (mimo-v2.5-free) on 2026-09-15*
*Source: Phase B requirements from ecosystem analysis documents*
*Lessons learned: Phase A specification review (attribute verification, P7.7 constraints, monorepo governance)*
*Post-review fixes (v1.1.0): Rank-based HITS thresholds, overlap coefficient normalization, PyVis directed flag, screening fallback keys, regression/progression counters, SearchStrategy schema location, concrete query healing*