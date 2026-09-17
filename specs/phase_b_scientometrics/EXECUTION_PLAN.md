# Phase B Execution Plan

## Overview

**Phase:** B — Scientometrics & Methodological Validation  
**Total Estimated Hours:** 38 (5 features)  
**Feature Dependency Graph:**

```
B1 (HITS) ──────────┬──→ B2 (Co-Citation/Coupling)
                     ├──→ B3 (Louvain)
B4 (Screen Compare) ── [INDEPENDENT]
B5 (Golden Seed)    ── [INDEPENDENT] (except schema sync in B5.1 → B5.1b → B5.1c)
```

**Parallelism Opportunities:** B1, B4, and B5 can begin simultaneously (no cross-feature deps). B2 and B3 depend on B1's `scientometrics.py` module existing.

---

## Task 1: Create `scientometrics.py` Module Skeleton [INDEPENDENT]
**Description:** Scaffold the new `ScientometricEngine` class in `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py` with the class definition, docstring, and empty method stubs for all B1/B2/B3 methods. This is the foundational module that all graph-kit scientometric features share.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py` (NEW)

### Execution Checklist
- [ ] Create `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py` with module docstring
- [ ] Add `from __future__ import annotations` and stdlib imports (`pathlib`, `typing`, `json`)
- [ ] Define `class ScientometricEngine:` with docstring describing its role
- [ ] Add stub methods with signatures only (no body): `compute_hits()`, `compute_betweenness_centrality()`, `classify_nodes_by_hits()`, `build_cocitation_network()`, `build_bibliographic_coupling()`, `build_hybrid_network()`, `detect_communities_louvain()`, `compute_modularity()`, `enrich_graph_with_communities()`
- [ ] Ensure all `networkx` imports are deferred inside method bodies (P7.7 constraint)

### Testing Strategy
- [ ] Verify module imports without error: `python -c "from scholar_graph.scientometrics import ScientometricEngine"`
- [ ] Confirm no top-level `networkx` import exists (grep for `^import networkx` at module level)

### Definition of Done (DoD)
- Module file exists, imports cleanly, `ScientometricEngine` class is importable, zero top-level networkx imports.

---

## Task 2: Implement `compute_hits()` and `compute_betweenness_centrality()` [DEPENDS: Task 1]
**Description:** Implement the HITS algorithm and betweenness centrality in `ScientometricEngine`. These are the core B1 metrics that identify seminal papers (Authorities) and comprehensive reviews (Hubs).

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py`

### Execution Checklist
- [ ] Implement `compute_hits(G, max_iter=100, normalized=True)` → returns `(hubs, authorities)` tuple of dicts
- [ ] Handle empty graph: raise `ValueError("Cannot compute HITS on empty graph")`
- [ ] Catch `nx.PowerIterationFailedConvergence`: fallback to unnormalized HITS with `max_iter * 3`, then manually normalize to [0, 1]
- [ ] Implement `compute_betweenness_centrality(G, normalized=True)` → returns dict
- [ ] All `networkx` imports deferred inside function bodies with `import networkx as nx` comment referencing P7.7

### Testing Strategy
- [ ] Create `tools/scholar-graph-kit/tests/test_scientometrics.py` (NEW)
- [ ] Write `test_compute_hits_basic()`: build small DiGraph (4 nodes, known topology), assert hubs/authorities dicts have correct keys, scores in [0,1], sum to 1.0 when normalized
- [ ] Write `test_compute_hits_empty_graph_raises()`: assert `ValueError` on empty graph
- [ ] Write `test_compute_hits_convergence_fallback()`: mock `nx.hits` to raise `PowerIterationFailedConvergence`, verify fallback path executes
- [ ] Write `test_compute_betweenness_centrality()`: known graph, assert bridge node has highest betweenness
- [ ] All tests use `import networkx as nx` (not deferred — OK in test code)

### Definition of Done (DoD)
- `test_compute_hits_basic`, `test_compute_hits_empty_graph_raises`, `test_compute_betweenness_centrality` all pass. HITS scores correctly rank review-like nodes as hubs and empirical-like nodes as authorities.

---

## Task 3: Implement `classify_nodes_by_hits()` [DEPENDS: Task 2]
**Description:** Implement rank-based classification of nodes into Authorities, Hubs, and Others based on HITS scores. This is the B1 classification layer that powers the "identify seminal papers" use case.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py`

### Execution Checklist
- [ ] Implement `classify_nodes_by_hits(hubs, authorities, top_k=None, percentile=90.0)` → returns `{"authorities": [...], "hubs": [...], "others": [...]}`
- [ ] Use percentile-based rank thresholds (not static thresholds) — handles graphs of varying sizes
- [ ] Classify node as Authority if `a_score >= threshold AND a_score > h_score`
- [ ] Classify node as Hub if `h_score >= threshold AND h_score > a_score`
- [ ] All other nodes classified as "other"
- [ ] Each entry: `{"doi": ..., "score": ..., "role": ...}`
- [ ] Sort each category list by score descending

### Testing Strategy
- [ ] Write `test_classify_nodes_by_hits_rank_based()`: synthetic hubs/authorities dicts, verify correct classification
- [ ] Write `test_classify_nodes_empty()`: empty dicts → all three lists empty
- [ ] Write `test_classify_nodes_top_k()`: with `top_k=2`, verify only top 2 in each category

### Definition of Done (DoD)
- All 3 classification tests pass. Seminal reviews classify as Hubs, empirical studies as Authorities, with rank-based thresholds.

---

## Task 4: Add `analyze` CLI Command [DEPENDS: Task 2]
**Description:** Add the `analyze` subcommand to the scholar-graph-kit CLI, exposing HITS and betweenness analysis on graph JSON files.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/cli.py`

### Execution Checklist
- [ ] Add `@app.command("analyze")` function to `cli.py`
- [ ] Parameters: `graph_file: Path` (arg), `--metric/-m` (default "hits", choices: hits/betweenness), `--output/-o` (optional Path)
- [ ] Load graph JSON via `json.loads()` + `nx.node_link_graph(data)` (deferred import)
- [ ] Import `ScientometricEngine` from `.scientometrics`
- [ ] For `metric="hits"`: call `compute_hits()` then `classify_nodes_by_hits()`, output full result dict
- [ ] For `metric="betweenness"`: call `compute_betweenness_centrality()`, output centrality dict
- [ ] If `--output` provided, write JSON to file; else print to stdout
- [ ] Use `typer.BadParameter` for unknown metrics

### Testing Strategy
- [ ] Write `test_cli_analyze_hits()` in `tools/scholar-graph-kit/tests/test_cli.py` (UPDATE existing file): build graph JSON fixture, invoke `analyze` via CliRunner, assert exit_code 0, output contains "hubs" and "authorities" keys
- [ ] Write `test_cli_analyze_betweenness()`: similar, assert "centrality" key present
- [ ] Write `test_cli_analyze_unknown_metric()`: invoke with `--metric bogus`, assert exit_code != 0

### Definition of Done (DoD)
- `scholar-graph-kit analyze graph.json --metric hits` works end-to-end. CLI integration tests pass.

---

## Task 5: Unit Tests for HITS Classification [DEPENDS: Task 3]
**Description:** Comprehensive unit tests for the full HITS pipeline: computation + classification integration, edge cases, and the betweenness centrality bridge-paper identification.

**Files to Touch:**
- `tools/scholar-graph-kit/tests/test_scientometrics.py`

### Execution Checklist
- [ ] Write `test_hits_classification_integration()`: build graph, compute_hits, classify_nodes_by_hits, assert review node classified as Hub, empirical nodes as Authorities
- [ ] Write `test_hits_score_range()`: all scores in [0.0, 1.0]
- [ ] Write `test_hits_single_node()`: graph with one node → score = 1.0 for both hub and authority
- [ ] Write `test_hits_diamond_graph()`: 4-node diamond topology, verify hub/authority split
- [ ] Write `test_betweenness_bridge_paper()`: linear chain graph, center node has highest betweenness

### Testing Strategy
- [ ] All tests use `tmp_path` for any file I/O (though most are in-memory)
- [ ] Use `pytest` parametrize for edge cases (empty graph, single node, disconnected)

### Definition of Done (DoD)
- All 5 test cases pass. HITS correctly identifies seminal reviews as Hubs and empirical trials as Authorities across graph topologies.

---

## Task 6: Implement `build_cocitation_network()` [DEPENDS: Task 1]
**Description:** Implement the co-citation network builder using Jaccard similarity. Two papers A and B are co-cited if both are cited by the same paper C.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py`

### Execution Checklist
- [ ] Implement `build_cocitation_network(citation_graph, min_jaccard=0.15)` → returns undirected `nx.Graph`
- [ ] Build reverse adjacency: `cited_by[target] = {source1, source2, ...}`
- [ ] Find candidate pairs: papers co-cited by the same paper (from `citing_to_cited` mapping)
- [ ] Compute pairwise Jaccard: `|citing_a ∩ citing_b| / |citing_a ∪ citing_b|`
- [ ] Add edge if Jaccard >= `min_jaccard`, with `weight=jaccard, type="cocitation"`
- [ ] All nodes from citation graph present in result graph (even isolated)
- [ ] Deferred `networkx` import inside function body

### Testing Strategy
- [ ] Write `test_cocitation_basic()` in `test_scientometrics.py`: 3 papers, A and B both cited by C → edge exists
- [ ] Write `test_cocitation_no_edge_below_threshold()`: Jaccard < min_jaccard → no edge
- [ ] Write `test_cocitation_empty_graph()`: empty input → empty output graph with 0 nodes

### Definition of Done (DoD)
- Co-citation network correctly identifies papers cited together. Jaccard weights in [0, 1]. Tests pass.

---

## Task 7: Implement `build_bibliographic_coupling()` [DEPENDS: Task 1]
**Description:** Implement the bibliographic coupling network. Two papers A and B are coupled if they share common references. Edge weight = number of shared references.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py`

### Execution Checklist
- [ ] Implement `build_bibliographic_coupling(citation_graph, min_overlap=2)` → returns undirected `nx.Graph`
- [ ] Build forward adjacency: `references[source] = {target1, target2, ...}`
- [ ] Find candidate pairs: papers that cite a common reference (from `cited_to_citing` mapping)
- [ ] Compute pairwise overlap: `|refs_a ∩ refs_b|`
- [ ] Add edge if overlap >= `min_overlap`, with `weight=overlap, type="coupling"`
- [ ] All nodes from citation graph present in result graph
- [ ] Deferred `networkx` import inside function body

### Testing Strategy
- [ ] Write `test_coupling_basic()`: A and B both cite X and Y → edge with weight 2
- [ ] Write `test_coupling_below_threshold()`: shared refs < min_overlap → no edge
- [ ] Write `test_coupling_empty_graph()`: empty input → empty output

### Definition of Done (DoD)
- Bibliographic coupling correctly identifies papers with shared references. Tests pass.

---

## Task 8: Implement `build_hybrid_network()` [DEPENDS: Tasks 6, 7]
**Description:** Implement the hybrid network combining co-citation and bibliographic coupling with configurable weights and Overlap Coefficient normalization for coupling.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py`

### Execution Checklist
- [ ] Implement `build_hybrid_network(citation_graph, weight_cocite=0.5, weight_couple=0.5, min_weight=0.1)` → returns undirected `nx.Graph`
- [ ] Call `build_cocitation_network(min_jaccard=0.0)` and `build_bibliographic_coupling(min_overlap=1)` to get raw networks
- [ ] For each edge in combined edge set: `combined = w_cocite * S_cocite + w_couple * S_couple_norm`
- [ ] Normalize coupling using Overlap Coefficient: `raw_couple / min(|refs_u|, |refs_v|)`
- [ ] Only add edge if `combined >= min_weight`
- [ ] Deferred `networkx` import inside function body

### Testing Strategy
- [ ] Write `test_hybrid_basic()`: verify combined weights are weighted sum of co-citation and coupling
- [ ] Write `test_hybrid_min_weight_filter()`: edges below min_weight excluded
- [ ] Write `test_hybrid_zero_cocite_weight()`: pure coupling network when weight_cocite=0

### Definition of Done (DoD)
- Hybrid network correctly combines co-citation and coupling. Overlap coefficient normalization verified. Tests pass.

---

## Task 9: Add `--mode` Option to `build` CLI [DEPENDS: Tasks 6, 7, 8]
**Description:** Extend the existing `build` CLI command with a `--mode` option to apply scientometric network transformations after building the base citation graph.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/cli.py`

### Execution Checklist
- [ ] Add `--mode` option to existing `build` command: `typer.Option("citation", "--mode", help="Graph mode: citation, cocitation, coupling, hybrid")`
- [ ] After building base citation graph `G`, apply mode-specific transformation:
  - `"citation"`: no transformation (existing behavior)
  - `"cocitation"`: `ScientometricEngine.build_cocitation_network(G)`
  - `"coupling"`: `ScientometricEngine.build_bibliographic_coupling(G)`
  - `"hybrid"`: `ScientometricEngine.build_hybrid_network(G)`
- [ ] Print node/edge counts after transformation
- [ ] Export and visualize the transformed graph

### Testing Strategy
- [ ] Write `test_cli_build_cocitation_mode()` in `test_cli.py`: build graph with `--mode cocitation`, verify output HTML/JSON exist
- [ ] Write `test_cli_build_default_citation_mode()`: existing behavior preserved (backward compatible)
- [ ] Write `test_cli_build_invalid_mode()`: `--mode bogus` → error

### Definition of Done (DoD)
- `scholar-graph-kit build --doi X --mode cocitation` works. Existing `build` command unchanged (backward compatible). Tests pass.

---

## Task 10: Implement `detect_communities_louvain()` [DEPENDS: Task 1]
**Description:** Implement Louvain community detection to automatically partition the citation network into thematic clusters.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py`

### Execution Checklist
- [ ] Implement `detect_communities_louvain(G, seed=42, resolution=1.0)` → returns `list[set[str]]`
- [ ] Convert directed graph to undirected for Louvain: `G.to_undirected() if G.is_directed() else G`
- [ ] Call `nx.community.louvain_communities(G_undirected, seed=seed, resolution=resolution)`
- [ ] Return list of sets, each set containing node IDs
- [ ] Handle empty graph: return `[]`
- [ ] Deferred `networkx` import inside function body

### Testing Strategy
- [ ] Write `test_louvain_basic()`: graph with 2 clear clusters → 2 communities detected
- [ ] Write `test_louvain_empty_graph()`: empty input → empty list
- [ ] Write `test_louvain_single_community()`: fully connected graph → 1 community
- [ ] Write `test_louvain_deterministic()`: same seed → same communities (reproducibility)

### Definition of Done (DoD)
- Louvain detects non-overlapping communities. Deterministic with same seed. Tests pass.

---

## Task 11: Implement `compute_modularity()` and `enrich_graph_with_communities()` [DEPENDS: Task 10]
**Description:** Implement modularity scoring and graph enrichment with community attributes.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/scientometrics.py`

### Execution Checklist
- [ ] Implement `compute_modularity(G, communities)` → returns `float` in [-1, 1]
- [ ] Guard: if no communities or 0 edges → return `0.0` (prevents ZeroDivisionError)
- [ ] Convert to undirected for modularity calculation
- [ ] Call `nx.community.modularity(G_undirected, communities)`
- [ ] Implement `enrich_graph_with_communities(G, communities)` → modifies G in-place
- [ ] Add `community` attribute (0-based index) and `group` attribute (1-based, for PyVis color coding) to each node

### Testing Strategy
- [ ] Write `test_modularity_good_partition()`: 2-cluster graph → modularity > 0.3
- [ ] Write `test_modularity_empty_communities()`: empty list → 0.0
- [ ] Write `test_modularity_no_edges()`: graph with nodes but no edges → 0.0
- [ ] Write `test_enrich_graph_with_communities()`: verify `community` and `group` attributes set correctly
- [ ] Write `test_enrich_graph_group_is_1_based()`: first community has group=1, second has group=2

### Definition of Done (DoD)
- Modularity score > 0.3 for well-partitioned graphs. Community/group attributes correctly assigned. ZeroDivisionError guarded. Tests pass.

---

## Task 12: Add `cluster` CLI Command [DEPENDS: Tasks 10, 11]
**Description:** Add the `cluster` subcommand to the scholar-graph-kit CLI for community detection on graph JSON files.

**Files to Touch:**
- `tools/scholar-graph-kit/src/scholar_graph/cli.py`

### Execution Checklist
- [ ] Add `@app.command("cluster")` function to `cli.py`
- [ ] Parameters: `graph_file: Path` (arg), `--resolution/-r` (float, default 1.0), `--seed/-s` (int, default 42), `--output/-o` (optional Path)
- [ ] Load graph JSON via `json.loads()` + `nx.node_link_graph(data)` (deferred import)
- [ ] Call `detect_communities_louvain()`, `compute_modularity()`, `enrich_graph_with_communities()`
- [ ] Output: `num_communities`, `modularity`, `community_sizes`, `node_community_map`
- [ ] Print community count and modularity to console

### Testing Strategy
- [ ] Write `test_cli_cluster_basic()` in `test_cli.py`: build graph JSON, invoke `cluster`, assert exit_code 0, output contains "num_communities" and "modularity"
- [ ] Write `test_cli_cluster_custom_resolution()`: `--resolution 2.0` produces more communities

### Definition of Done (DoD)
- `scholar-graph-kit cluster graph.json` works end-to-end. CLI integration tests pass.

---

## Task 13: Unit Tests for Co-Citation & Coupling [DEPENDS: Tasks 6, 7, 8]
**Description:** Comprehensive unit tests for co-citation, bibliographic coupling, and hybrid networks.

**Files to Touch:**
- `tools/scholar-graph-kit/tests/test_scientometrics.py`

### Execution Checklist
- [ ] Write `test_cocitation_jaccard_calculation()`: verify exact Jaccard values for known graphs
- [ ] Write `test_cocitation_preserves_node_attributes()`: node attrs from citation graph carried to co-citation graph
- [ ] Write `test_coupling_overlap_calculation()`: verify exact overlap counts
- [ ] Write `test_coupling_weight_is_raw_overlap()`: edge weight equals shared reference count
- [ ] Write `test_hybrid_weighted_sum()`: verify combined = w_cocite * S_cocite + w_couple * S_couple_norm
- [ ] Write `test_hybrid_overlap_coefficient()`: verify coupling normalization by min(|refs_u|, |refs_v|)
- [ ] Write `test_hybrid_directed_graph_input()`: works with DiGraph input

### Testing Strategy
- [ ] Use `pytest.approx` for floating-point Jaccard comparisons
- [ ] All tests construct small, deterministic graphs (4-6 nodes)

### Definition of Done (DoD)
- All 7 test cases pass. Jaccard similarity and overlap coefficient calculations verified. Node attributes preserved. Tests pass.

---

## Task 14: Unit Tests for Community Detection [DEPENDS: Tasks 10, 11]
**Description:** Comprehensive unit tests for Louvain community detection, modularity, and graph enrichment.

**Files to Touch:**
- `tools/scholar-graph-kit/tests/test_scientometrics.py`

### Execution Checklist
- [ ] Write `test_louvain_two_clusters()`: 2 clear clusters → exactly 2 communities, each containing correct nodes
- [ ] Write `test_louvain_modularity_above_threshold()`: well-partitioned graph → modularity > 0.3
- [ ] Write `test_louvain_single_community_fully_connected()`: complete graph → 1 community
- [ ] Write `test_louvain_deterministic_with_seed()`: same seed → same result, different seed → possibly different
- [ ] Write `test_enrich_graph_community_and_group_attrs()`: verify both attributes set
- [ ] Write `test_zero_edge_graph_modularity()`: graph with nodes but no edges → modularity 0.0

### Testing Strategy
- [ ] Use `pytest.approx` for modularity comparisons
- [ ] Use `pytest.mark.parametrize` for seed-based determinism tests

### Definition of Done (DoD)
- Communities are non-overlapping. Modularity > 0.3 for meaningful partitions. Results reproducible with same seed. Tests pass.

---

## Task 15: Add `ScreeningComparisonReport` Dataclass [INDEPENDENT]
**Description:** Define the `ScreeningComparisonReport` dataclass in the screening module as the return type for the screening run comparator.

**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/screening.py`

### Execution Checklist
- [ ] Add `@dataclass` class `ScreeningComparisonReport` to `screening.py`
- [ ] Fields: `total_compared: int`, `agreement_count: int`, `agreement_rate: float`, `transition_matrix: dict[str, dict[str, int]]`, `discrepancies: list[dict[str, Any]]`, `regression_count: int`, `progression_count: int`
- [ ] Add docstring explaining each field
- [ ] Ensure `Any` is imported from `typing` (already imported in file)

### Testing Strategy
- [ ] Verify dataclass instantiation with sample values in a unit test
- [ ] Verify all fields accessible

### Definition of Done (DoD)
- `ScreeningComparisonReport` is importable from `scholar_search.screening` and can be instantiated with all fields.

---

## Task 16: Implement `compare_screening_runs()` [DEPENDS: Task 15]
**Description:** Implement the core screening run comparator that computes agreement rate, transition matrices, and discrepancy tables between two screening runs.

**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/screening.py`

### Execution Checklist
- [ ] Add `compare_screening_runs(run_a_decisions, run_b_decisions, key_field="workspace_id")` function
- [ ] Implement fallback key matching: `workspace_id → doi → document_title`
- [ ] Normalize decision strings to uppercase, stripped (prevents case-sensitive false discrepancies)
- [ ] Initialize 2x2 transition matrix: `{INCLUDE: {INCLUDE: 0, EXCLUDE: 0}, EXCLUDE: {INCLUDE: 0, EXCLUDE: 0}}`
- [ ] For each common key: update transition matrix, track regression (INCLUDE→EXCLUDE) and progression (EXCLUDE→INCLUDE)
- [ ] Compute agreement rate: `agreement_count / total_compared`
- [ ] Build discrepancy list with `workspace_id`, `title`, `doi`, `run_a`, `run_b`, reasoning fields
- [ ] Return `ScreeningComparisonReport`

### Testing Strategy
- [ ] Create `tools/scholar-search-kit/tests/test_screen_comparator.py` (NEW file, or add to existing `test_screening.py`)
- [ ] Write `test_compare_screening_runs_identical()`: same decisions → 100% agreement, 0 discrepancies
- [ ] Write `test_compare_screening_runs_with_discrepancies()`: known transitions → correct matrix and counts
- [ ] Write `test_compare_screening_runs_regression_count()`: INCLUDE→EXCLUDE tracked correctly
- [ ] Write `test_compare_screening_runs_progression_count()`: EXCLUDE→INCLUDE tracked correctly
- [ ] Write `test_compare_screening_runs_fallback_key_doi()`: match by DOI when workspace_id absent
- [ ] Write `test_compare_screening_runs_case_normalization()`: "include" == "INCLUDE" (no false discrepancy)
- [ ] Write `test_compare_screening_runs_empty_intersection()`: no common keys → 0 compared, 0% agreement

### Definition of Done (DoD)
- Agreement rate, transition matrix, regression/progression counters, and discrepancies all correct. Fallback key matching and case normalization work. Tests pass.

---

## Task 17: Add `screen-compare` CLI Command [DEPENDS: Task 16]
**Description:** Add the `screen-compare` subcommand to the scholar-search-kit CLI for comparing two screening runs.

**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/cli.py`

### Execution Checklist
- [ ] Add `@app.command("screen-compare")` function to `cli.py`
- [ ] Parameters: `run_a_file: Path` (arg), `run_b_file: Path` (arg), `--output/-o` (optional Path)
- [ ] Load both JSON files, handle both raw array and `{"decisions": [...]}` wrapper formats
- [ ] Call `compare_screening_runs(run_a_decisions, run_b_decisions)`
- [ ] Format output as Markdown report: Summary, Transition Matrix, Discrepancies table
- [ ] If `--output` provided, write report to file; else print to stdout
- [ ] Import `compare_screening_runs` from `.screening`

### Testing Strategy
- [ ] Write `test_cli_screen_compare_basic()` in `test_cli.py` (UPDATE existing): create two decision JSON files, invoke `screen-compare`, assert exit_code 0, output contains "Agreement Rate"
- [ ] Write `test_cli_screen_compare_with_output()`: verify file written when `--output` provided
- [ ] Write `test_cli_screen_compare_wrapper_format()`: handle `{"decisions": [...]}` wrapper

### Definition of Done (DoD)
- `scholar-search screen-compare run_a.json run_b.json` works end-to-end. CLI integration tests pass.

---

## Task 18: Add `golden_seeds` Field to `SearchStrategy` [INDEPENDENT]
**Description:** Add the `golden_seeds` field to the `SearchStrategy` Pydantic model in `scholar-protocol-kit`. This is the schema change that enables the B5 Golden Seed feature.

**Files to Touch:**
- `tools/scholar-protocol-kit/src/scholar_protocol/models.py`

### Execution Checklist
- [ ] In `SearchStrategy` class, add field: `golden_seeds: list[str] = Field(default_factory=list, description="DOIs of 2-5 landmark papers that must appear in search results")`
- [ ] Place field after `target_candidate_pool_size` (preserves canonical field order)
- [ ] Verify `default_factory=list` so existing protocols without this field remain valid (backward compatible)

### Testing Strategy
- [ ] Verify existing test fixtures still parse without error (backward compatibility)
- [ ] Write test: `SearchStrategy(core_concepts=[...])` without `golden_seeds` → field defaults to `[]`
- [ ] Write test: `SearchStrategy(core_concepts=[...], golden_seeds=["10.1000/test"])` → field populated

### Definition of Done (DoD)
- `SearchStrategy` accepts `golden_seeds` field. All existing tests pass without modification (backward compatible).

---

## Task 19: Re-export Protocol Schema + Update Fixtures [DEPENDS: Task 18]
**Description:** Re-export `protocol.schema.json` from updated models and update all canonical test fixtures with the new `golden_seeds` field (empty list default means most fixtures don't need content changes, but fingerprints may shift).

**Files to Touch:**
- `tools/scholar-protocol-kit/schemas/v1/protocol.schema.json` (REGENERATE)
- `tools/scholar-protocol-kit/tests/fixtures/valid/*.json` (VERIFY — may not need changes if default is `[]`)
- `tools/scholar-protocol-kit/tests/fixtures/valid/*.json.sha256` (REGENERATE fingerprints if canonical serialization changes)

### Execution Checklist
- [ ] Run `python tools/scholar-protocol-kit/scripts/generate_schema.py` to regenerate `protocol.schema.json`
- [ ] Verify schema diff shows `golden_seeds` field in `SearchStrategy` definition
- [ ] Run `uv run pytest tools/scholar-protocol-kit/tests/test_schema_sync.py -v` — must pass
- [ ] Run `uv run pytest tools/scholar-protocol-kit/tests/test_canonical.py -v` — check if fingerprints changed
- [ ] If fingerprints changed: regenerate `.sha256` files using `scholar-protocol fingerprint <fixture>` CLI or compute sha256 manually
- [ ] Verify all valid fixtures parse with updated schema: `uv run pytest tools/scholar-protocol-kit/tests/test_validate.py -v`

### Testing Strategy
- [ ] `test_schema_in_sync_with_models` (existing CI gate) must pass
- [ ] `test_pinned_golden_fingerprint` must pass (after fingerprint update if needed)
- [ ] `test_schema_contains_all_required_fields` must pass (golden_seeds has default, so not required)

### Definition of Done (DoD)
- `test_schema_sync.py` and `test_canonical.py` both pass. Schema file reflects `golden_seeds` field. No regressions.

---

## Task 20: Run Protocol Schema Sync Tests [DEPENDS: Task 19]
**Description:** Verify the full protocol schema sync pipeline passes with the new `golden_seeds` field. This is the CI gate that prevents schema drift.

**Files to Touch:**
- (no file changes — verification only)

### Execution Checklist
- [ ] Run `uv run pytest tools/scholar-protocol-kit/tests/test_schema_sync.py -v` — all tests pass
- [ ] Run `uv run pytest tools/scholar-protocol-kit/tests/test_canonical.py -v` — all tests pass
- [ ] Run `uv run pytest tools/scholar-protocol-kit/tests/test_validate.py -v` — all tests pass
- [ ] Run `uv run pytest tools/scholar-protocol-kit/tests/test_models.py -v` — all tests pass

### Testing Strategy
- [ ] This is the validation task — no new tests, just confirm existing CI gates pass

### Definition of Done (DoD)
- All protocol-kit tests pass. Schema is in sync with models. Fingerprints are stable.

---

## Task 21: Create `query_validator.py` Module [INDEPENDENT]
**Description:** Scaffold the `QueryDiagnosticValidator` class in a new `query_validator.py` module in scholar-search-kit.

**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/query_validator.py` (NEW)

### Execution Checklist
- [ ] Create `tools/scholar-search-kit/src/scholar_search/query_validator.py` with module docstring
- [ ] Add `from __future__ import annotations` and necessary imports
- [ ] Define `class QueryDiagnosticValidator:` with `__init__(self, search_engine)` and `max_iterations = 3`
- [ ] Add method stubs: `validate_and_heal()`, `_heal_query()`
- [ ] Add `_clean_doi()` helper function for DOI sanitization

### Testing Strategy
- [ ] Verify module imports: `python -c "from scholar_search.query_validator import QueryDiagnosticValidator"`

### Definition of Done (DoD)
- Module file exists, imports cleanly, class is instantiable.

---

## Task 22: Implement `QueryDiagnosticValidator.validate_and_heal()` [DEPENDS: Task 21]
**Description:** Implement the main validation loop that checks golden seed recall and triggers healing iterations.

**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/query_validator.py`

### Execution Checklist
- [ ] Implement `async validate_and_heal(query_text, golden_seeds, providers=None)` → returns dict with results
- [ ] Sanitize seed DOIs via `_clean_doi()` (handles `https://doi.org/`, `doi:` prefixes)
- [ ] Loop up to `max_iterations`:
  - Execute search via `self.search_engine.search_all(query, dedup=True)`
  - Extract DOIs from results (sanitized)
  - Compute recall: `len(found_seeds) / len(seeds_lower)`
  - If recall >= 1.0: break with `validated=True`
  - If recall < 1.0 and iterations remain: call `_heal_query()`
- [ ] Track each iteration: query used, results count, recall, found/missed seeds
- [ ] Return result dict: `original_query`, `golden_seeds`, `iterations`, `final_query`, `recall`, `validated`

### Testing Strategy
- [ ] Create `tools/scholar-search-kit/tests/test_query_validator.py` (NEW)
- [ ] Write `test_validate_and_heal_perfect_recall()`: mock search engine returns all seeds → validated=True, 0 iterations
- [ ] Write `test_validate_and_heal_healing_needed()`: mock search engine misses seeds → healing loop runs, eventually validated or max iterations reached
- [ ] Write `test_doi_sanitization()`: verify `https://doi.org/10.1000/test` → `10.1000/test`

### Definition of Done (DoD)
- Recall calculation correct. DOI sanitization handles various formats. Healing loop iterates up to max_iterations. Tests pass.

---

## Task 23: Implement `_heal_query()` with Heuristic + LLM Strategy [DEPENDS: Task 22]
**Description:** Implement the two-tier query healing strategy: deterministic heuristic (DOI-based expansion) and optional LLM diagnostic critique.

**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/query_validator.py`

### Execution Checklist
- [ ] Implement `async _heal_query(current_query, missed_seeds, search_results)` → returns healed query string
- [ ] **Tier 1 (Heuristic):** Extract DOIs of missed seeds, build `doi:10.xxxx OR doi:10.yyyy` clause, append as `(current_query) OR (doi_terms)`
- [ ] **Tier 2 (LLM - Optional):** If API key available, use LLM to analyze why query missed seeds and suggest boolean/synonym modifications
- [ ] Return healed query string (at minimum the heuristic expansion)

### Testing Strategy
- [ ] Write `test_heal_query_heuristic_expansion()`: verify DOI terms appended as OR clause
- [ ] Write `test_heal_query_no_missed_seeds()`: no missed seeds → query unchanged
- [ ] Write `test_heal_query_preserves_original_query()`: original query preserved in parentheses

### Definition of Done (DoD)
- Heuristic healing correctly expands query with DOI-based OR clauses. Original query preserved. Tests pass.

---

## Task 24: Add `validate-query` CLI Command [DEPENDS: Task 22]
**Description:** Add the `validate-query` subcommand to the scholar-search-kit CLI for golden seed validation.

**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/cli.py`

### Execution Checklist
- [ ] Add `@app.command("validate-query")` function to `cli.py`
- [ ] Parameters: `query_text: str` (arg), `--seed/-s` (list[str], required, multiple), `--output/-o` (optional Path)
- [ ] Instantiate `QueryDiagnosticValidator` with a `SearchEngine` (default providers)
- [ ] Call `await validator.validate_and_heal(query_text, seeds)`
- [ ] Output: iteration summary table, final recall, validated status
- [ ] If `--output` provided, write JSON result to file

### Testing Strategy
- [ ] Write `test_cli_validate_query_basic()` in `test_cli.py`: invoke with query and seeds, assert exit_code 0 (mock search engine internally)
- [ ] Write `test_cli_validate_query_output_file()`: verify file written when `--output` provided

### Definition of Done (DoD)
- `scholar-search validate-query "query" --seed doi1 --seed doi2` works end-to-end. CLI integration tests pass.

---

## Task 25: Integrate Golden Seeds into Inception Wizard [DEPENDS: Tasks 18, 22]
**Description:** Extend the inception wizard to solicit golden seed DOIs from the researcher during the protocol inception flow.

**Files to Touch:**
- `src/scholar_harness/inception.py`

### Execution Checklist
- [ ] In Stage 3 (Socratic boundary grill) or Stage 4 (Protocol emission), add a prompt for golden seed DOIs
- [ ] Ask: "Do you have 2-5 landmark papers (DOIs) that MUST appear in your search results? (comma-separated, or press Enter to skip)"
- [ ] Parse input into list of DOI strings
- [ ] Include `golden_seeds` in the emitted `protocol.json` under `search_strategy`
- [ ] Log the golden seeds solicitation as an audit event

### Testing Strategy
- [ ] Verify inception wizard still completes without golden seeds (backward compatible — empty list default)
- [ ] Verify inception wizard accepts golden seeds input and includes them in protocol.json
- [ ] Write integration test with mock Responder that provides golden seeds

### Definition of Done (DoD)
- Inception wizard solicits and includes golden seeds in protocol.json. Backward compatible (empty default). Tests pass.

---

## Task 26: Unit Tests for Query Validator [DEPENDS: Tasks 22, 23]
**Description:** Comprehensive unit tests for the QueryDiagnosticValidator including healing loop behavior and edge cases.

**Files to Touch:**
- `tools/scholar-search-kit/tests/test_query_validator.py`

### Execution Checklist
- [ ] Write `test_validate_perfect_recall_no_healing()`: all seeds found → 1 iteration, validated=True
- [ ] Write `test_validate_partial_recall_heals()`: some seeds missing → healing triggered, final recall improved
- [ ] Write `test_validate_max_iterations_respected()`: mock never finds seeds → stops at max_iterations
- [ ] Write `test_validate_empty_seeds()`: empty golden_seeds → recall=1.0, validated=True
- [ ] Write `test_heal_query_appends_doi_terms()`: verify heuristic expansion format
- [ ] Write `test_doi_sanitization_various_formats()`: test `https://doi.org/`, `http://doi.org/`, `doi:`, bare DOI
- [ ] Write `test_validate_returns_iteration_history()`: each iteration logged with query, count, recall

### Testing Strategy
- [ ] Mock `search_engine.search_all()` to return controlled Document lists
- [ ] Use `AsyncMock` for async search engine methods
- [ ] Use `pytest.mark.asyncio` for async test functions

### Definition of Done (DoD)
- All 7 test cases pass. Recall calculated correctly. DOI sanitization handles all formats. Healing loop respects max iterations. Tests pass.

---

## Task 27: Write B1 (HITS) CLI Integration Tests [DEPENDS: Tasks 4, 5]
**Description:** End-to-end CLI integration tests for the HITS analysis feature, verifying the full pipeline from graph JSON file to analysis output.

**Files to Touch:**
- `tools/scholar-graph-kit/tests/test_cli.py`

### Execution Checklist
- [ ] Write `test_cli_analyze_hits_from_file()`: create graph JSON fixture file, invoke `analyze --metric hits`, verify JSON output has `hubs`, `authorities`, `classification` keys
- [ ] Write `test_cli_analyze_hits_output_file()`: invoke with `--output`, verify file written
- [ ] Write `test_cli_analyze_hits_stdout()`: invoke without `--output`, verify output to stdout
- [ ] Write `test_cli_analyze_classification_ranking()`: verify authorities are ranked above hubs by score

### Testing Strategy
- [ ] Use `typer.testing.CliRunner` for CLI invocation
- [ ] Create graph JSON fixtures using `nx.node_link_data()`
- [ ] Parse CLI output as JSON for assertions

### Definition of Done (DoD)
- All 4 CLI integration tests pass. HITS analysis works end-to-end from file to output.

---

## Task 28: Write B2 (Co-Citation/Coupling) CLI Integration Tests [DEPENDS: Task 9]
**Description:** End-to-end CLI integration tests for co-citation, coupling, and hybrid network modes.

**Files to Touch:**
- `tools/scholar-graph-kit/tests/test_cli.py`

### Execution Checklist
- [ ] Write `test_cli_build_cocitation_mode()`: build with `--mode cocitation`, verify output files exist
- [ ] Write `test_cli_build_coupling_mode()`: build with `--mode coupling`, verify output files exist
- [ ] Write `test_cli_build_hybrid_mode()`: build with `--mode hybrid`, verify output files exist
- [ ] Write `test_cli_build_default_citation_mode()`: existing behavior unchanged (backward compatibility)

### Testing Strategy
- [ ] Mock HTTP calls to OpenAlex (use existing mock patterns from `test_builder.py`)
- [ ] Use `tmp_path` for output files
- [ ] Verify node/edge counts in output JSON

### Definition of Done (DoD)
- All 4 CLI integration tests pass. Co-citation, coupling, hybrid modes work via CLI. Backward compatible.

---

## Task 29: Write B3 (Louvain) CLI Integration Tests [DEPENDS: Task 12]
**Description:** End-to-end CLI integration tests for community detection.

**Files to Touch:**
- `tools/scholar-graph-kit/tests/test_cli.py`

### Execution Checklist
- [ ] Write `test_cli_cluster_basic()`: create graph JSON, invoke `cluster`, verify output has `num_communities`, `modularity`
- [ ] Write `test_cli_cluster_output_file()`: invoke with `--output`, verify file written
- [ ] Write `test_cli_cluster_custom_resolution()`: `--resolution 2.0` → more communities than default
- [ ] Write `test_cli_cluster_modularity_positive()`: modularity > 0 for well-partitioned graph

### Testing Strategy
- [ ] Use `nx.node_link_data()` to create graph JSON fixtures
- [ ] Parse CLI output as JSON for assertions

### Definition of Done (DoD)
- All 4 CLI integration tests pass. Community detection works end-to-end via CLI.

---

## Task 30: Write B4 (Screen Comparator) CLI Integration Tests [DEPENDS: Task 17]
**Description:** End-to-end CLI integration tests for the screening run comparator.

**Files to Touch:**
- `tools/scholar-search-kit/tests/test_cli.py`

### Execution Checklist
- [ ] Write `test_cli_screen_compare_identical_runs()`: same decisions → 100% agreement in output
- [ ] Write `test_cli_screen_compare_with_discrepancies()`: different decisions → transition matrix and discrepancies in output
- [ ] Write `test_cli_screen_compare_output_file()`: invoke with `--output`, verify Markdown report written
- [ ] Write `test_cli_screen_compare_wrapper_format()`: handle `{"decisions": [...]}` wrapper

### Testing Strategy
- [ ] Create decision JSON fixtures using `tmp_path`
- [ ] Parse Markdown output for assertions

### Definition of Done (DoD)
- All 4 CLI integration tests pass. Screen comparator works end-to-end via CLI.

---

## Task 31: Write B5 (Golden Seed) CLI Integration Tests [DEPENDS: Task 24]
**Description:** End-to-end CLI integration tests for the golden seed query validator.

**Files to Touch:**
- `tools/scholar-search-kit/tests/test_cli.py`

### Execution Checklist
- [ ] Write `test_cli_validate_query_basic()`: invoke with query and seeds, assert exit_code 0
- [ ] Write `test_cli_validate_query_output_file()`: invoke with `--output`, verify JSON file written
- [ ] Write `test_cli_validate_query_multiple_seeds()`: multiple `--seed` flags work correctly

### Testing Strategy
- [ ] Mock search engine internally (the CLI instantiates its own)
- [ ] Use `tmp_path` for output files

### Definition of Done (DoD)
- All 3 CLI integration tests pass. Golden seed validation works end-to-end via CLI.

---

## Task 32: Update SKILL.md Documentation [DEPENDS: Tasks 4, 9, 12, 17, 24]
**Description:** Update the SKILL.md files for scholar-graph-kit, scholar-search-kit, and scholar-protocol-kit to document new capabilities.

**Files to Touch:**
- `.agents/skills/scholar-graph-kit/SKILL.md`
- `.agents/skills/scholar-search-kit/SKILL.md`
- `.agents/skills/scholar-protocol-kit/SKILL.md`

### Execution Checklist
- [ ] Update `scholar-graph-kit/SKILL.md`: add documentation for `analyze` (HITS, betweenness), `cluster` (Louvain), `--mode` option (cocitation, coupling, hybrid)
- [ ] Update `scholar-search-kit/SKILL.md`: add documentation for `screen-compare` and `validate-query` commands
- [ ] Update `scholar-protocol-kit/SKILL.md`: document `golden_seeds` field in `SearchStrategy`
- [ ] Include example CLI invocations for each new command
- [ ] Document output formats and data schemas

### Testing Strategy
- [ ] Documentation-only task — no code tests needed
- [ ] Verify SKILL.md files are readable and well-formatted

### Definition of Done (DoD)
- All three SKILL.md files updated with new feature documentation. Example invocations included.

---

## Task 33: Run Full Test Suite + Lint [INDEPENDENT]
**Description:** Run the complete test suite and linter to verify no regressions across all Phase B features.

**Files to Touch:**
- (no file changes — verification only)

### Execution Checklist
- [ ] Run `uv run pytest tools/scholar-graph-kit/tests/ -v` — all graph-kit tests pass
- [ ] Run `uv run pytest tools/scholar-search-kit/tests/ -v` — all search-kit tests pass
- [ ] Run `uv run pytest tools/scholar-protocol-kit/tests/ -v` — all protocol-kit tests pass
- [ ] Run `uv run ruff check scripts/` — CI-scoped lint passes
- [ ] Run `uv run pytest tests/conformance/ -v` — conformance tests pass (new CLI commands registered in Typer apps)
- [ ] Check coverage: new code has ≥90% test coverage

### Testing Strategy
- [ ] This is the final validation pass — no new tests, just comprehensive verification

### Definition of Done (DoD)
- All 391+ existing tests pass (no regressions). All new Phase B tests pass. Lint clean. Coverage ≥90% for new code.

---

## Task 34: Monorepo Sync + Conformance Verification [INDEPENDENT]
**Description:** Sync kit changes to external repos, update plugin pins, regenerate metapackage pins, and verify conformance tests pass.

**Files to Touch:**
- `plugins.json` (via `scripts/push_tools.py`)
- `packaging/nexus-scholar/nexus_scholar_pins.json` (via `scripts/generate_nexus_scholar_pins.py`)

### Execution Checklist
- [ ] Run `python scripts/push_tools.py` to sync kit changes to external repos
- [ ] Update `plugins.json` `default_rev` to new commit SHAs for modified kits
- [ ] Run `python scripts/generate_nexus_scholar_pins.py` to regenerate metapackage pins
- [ ] Run `python scripts/generate_nexus_scholar_pins.py --check` to verify freshness
- [ ] Run `uv run pytest tests/conformance/test_actions_cli_parity.py -v` — new commands registered
- [ ] Run `uv run pytest tests/conformance/test_mcp_tool_parity.py -v` — MCP tools in parity

### Testing Strategy
- [ ] This is the monorepo governance verification — confirms external repos are in sync
- [ ] Conformance tests verify CLI/MCP parity

### Definition of Done (DoD)
- Kit repos updated with new commits. Plugins.json pins current. Metapackage pins fresh. Conformance tests pass.

---

## Task 35: Run All Phase B Tests End-to-End [INDEPENDENT]
**Description:** Final comprehensive test run covering all Phase B features together.

**Files to Touch:**
- (no file changes — verification only)

### Execution Checklist
- [ ] Run `uv run pytest tests/ -k "scientometrics or screen_compare or golden_seed or query_validator or screen-compare or validate-query" -v`
- [ ] Verify zero failures across all Phase B test cases
- [ ] Run `uv run pytest tests/ -v` — full suite, no regressions
- [ ] Verify test count ≥ 391 (existing) + all new Phase B tests

### Testing Strategy
- [ ] This is the final Phase B acceptance gate — all tests must pass

### Definition of Done (DoD)
- All Phase B tests pass. No regressions. Test count increased by all new test cases. Phase B complete.

---

## Summary: Task Dependencies & Parallelism

```
Phase B Dependency Graph:

Layer 0 (start immediately, parallel):
  Task 1  [INDEPENDENT] - scientometrics.py skeleton
  Task 15 [INDEPENDENT] - ScreeningComparisonReport dataclass
  Task 18 [INDEPENDENT] - golden_seeds schema field
  Task 21 [INDEPENDENT] - query_validator.py skeleton

Layer 1 (after Layer 0):
  Task 2  [after Task 1]  - compute_hits + compute_betweenness
  Task 6  [after Task 1]  - build_cocitation_network
  Task 7  [after Task 1]  - build_bibliographic_coupling
  Task 10 [after Task 1]  - detect_communities_louvain
  Task 16 [after Task 15] - compare_screening_runs
  Task 19 [after Task 18] - schema re-export + fixtures
  Task 22 [after Task 21] - validate_and_heal

Layer 2 (after Layer 1):
  Task 3  [after Task 2]  - classify_nodes_by_hits
  Task 8  [after Task 6,7] - build_hybrid_network
  Task 11 [after Task 10] - compute_modularity + enrich
  Task 17 [after Task 16] - screen-compare CLI
  Task 20 [after Task 19] - schema sync tests
  Task 23 [after Task 22] - _heal_query
  Task 24 [after Task 22] - validate-query CLI
  Task 5  [after Task 3]  - HITS unit tests
  Task 13 [after Task 6,7,8] - Co-citation/coupling tests
  Task 14 [after Task 10,11] - Louvain tests

Layer 3 (after Layer 2):
  Task 4  [after Task 2]  - analyze CLI
  Task 9  [after Task 6,7,8] - --mode CLI option
  Task 12 [after Task 10,11] - cluster CLI
  Task 25 [after Task 18,22] - inception wizard integration
  Task 26 [after Task 22,23] - query validator tests

Layer 4 (after Layer 3):
  Task 27 [after Task 4,5]   - HITS CLI integration tests
  Task 28 [after Task 9]     - Co-citation CLI integration tests
  Task 29 [after Task 12]    - Louvain CLI integration tests
  Task 30 [after Task 17]    - Screen-compare CLI integration tests
  Task 31 [after Task 24]    - Validate-query CLI integration tests
  Task 32 [after Task 4,9,12,17,24] - SKILL.md updates

Layer 5 (final):
  Task 33 [INDEPENDENT] - Full test suite + lint
  Task 34 [INDEPENDENT] - Monorepo sync + conformance
  Task 35 [INDEPENDENT] - All Phase B tests E2E
```

**Maximum Parallelism (critical path):**

```
Task 1 ──→ Task 2 ──→ Task 3 ──→ Task 4 ──→ Task 27 ──→ Task 33/35
              ↓
Task 6 ──→ Task 8 ──→ Task 9 ──→ Task 28
Task 7 ──↗
              ↓
Task 10 ──→ Task 11 ──→ Task 12 ──→ Task 29

Task 15 ──→ Task 16 ──→ Task 17 ──→ Task 30
Task 18 ──→ Task 19 ──→ Task 20
Task 21 ──→ Task 22 ──→ Task 23 ──→ Task 26
                     └──→ Task 24 ──→ Task 31
```

---

*Execution plan generated by opencode (mimo-v2.5-free) on 2026-09-17*
*Source: Phase B specification v1.1.0 at `specs/phase_b_scientometrics/README.md`*
*Total tasks: 35 | Estimated hours: 38 | Independent tasks: 8 | Parallelizable layers: 5*
