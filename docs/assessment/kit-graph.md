# scholar-graph-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-graph-kit`). Scope: `tools/scholar-graph-kit/src/scholar_graph/` (~1.2k lines: `scientometrics.py` 391, `cli.py` 383, `visualizer.py` 242, `builder.py` 192, `config.py` 9, `models.py` 14) and `tests/` (6 files, ~1.3k lines); harness consumers `src/scholar_harness/pipeline/graph.py` and `src/scholar_harness/console/runtimes/actions.py:139-165`. Method: read all source in full; ran `uv run --no-sync pytest tools/scholar-graph-kit/tests -q` (79 passed, **3 failed**, 1 skipped); offline reproductions with a stubbed async HTTP client and `typer.testing.CliRunner`; README, `docs/`, SKILL.md and `docs/kits_surface_matrix.md` treated as claims only.

## 1. Verdict

The kit builds a directed citation graph of *within-corpus* citations from OpenAlex, normalises PageRank and renders it with PyVis; for that narrow job the core path works. Around it, the defects are of the "looks fine, is wrong" kind: a network outage produces a graph of isolated nodes with uniform PageRank that the CLI reports as "Citation graph built!" (GRAPH-01), two of the four advertised `--mode`s crash on argument names (GRAPH-02), DOI casing creates phantom duplicate nodes (GRAPH-03), and the PageRank the harness "computes" is thrown away and never reaches the HTML (GRAPH-04). Methodologically, co-citation and bibliographic coupling are computed only over citations between included studies, which makes coupling structurally empty for most reviews (GRAPH-05); "Louvain" is a different algorithm with an ignored seed (GRAPH-06). PageRank is presented as an "importance" signal that boosts RAG retrieval, which a small intra-corpus graph cannot support (§4). The test suite is red at HEAD.

| Lens | Rating | Reason |
|---|---|---|
| Code quality & architecture | Weak | Small and readable, but CLI calls its own engine with wrong kwargs, dead `config`/`models`, broad `except Exception: pass`, failing tests left in tree |
| Correctness & bugs | Weak | Silent provider-failure masking, DOI-case duplicate nodes, discarded PageRank, two crashing modes — all reproduced |
| Research-method fitness | Weak | Intra-corpus-only edges make coupling/co-citation near-meaningless; "Louvain" mislabelled; PageRank framed as importance |

## 2. Architecture and code quality

- **Structure.** `CitationGraphBuilder` (fetch + build + export) → `ScientometricEngine` (co-citation, coupling, hybrid, HITS, betweenness, communities) → `GraphVisualizer` (PyVis). Reasonable split; heavy imports deferred (P7.7). `ScientometricEngine` is only reachable from the CLI, never from the harness pipeline.
- **CLI/engine contract drift.** `cli.py:131` calls `build_bibliographic_coupling(min_jaccard=0.15)` but the signature is `min_overlap: int` (`scientometrics.py:189`); `cli.py:139` calls `build_hybrid_network(alpha=0.5)` but the signature is `weight_cocite/weight_couple/min_weight` (`:245-250`). No test invokes `--mode` (grep of `tests/` for `mode` finds none), so both paths have never run.
- **Error handling.** `fetch_work_data` swallows every exception (`builder.py:25-26`); `compute_pagerank` returns uniform 1.0 on any exception (`:123-124`); `compute_modularity` returns 0.0 on any exception (`scientometrics.py:370-371`). Failures become plausible-looking numbers.
- **Dead code.** `config.py` (`Settings`, incl. unused `max_concurrent_requests` and `openalex_email`) and `models.py` (`GraphNode`, `GraphEdge`) are imported nowhere in `src/`.
- **Concurrency.** `build_graph` schedules every DOI at once via `asyncio.as_completed` (`builder.py:37-46`) with no semaphore; throttling depends entirely on the injected `AcademicHttpClient`.
- **Inconsistent PageRank representations.** JSON: max-normalised, 4 dp, **lowercased keys** (`builder.py:119-122`); GEXF/GraphML: raw PageRank written onto nodes (`:165-168`, `:185-188`); HTML: none (GRAPH-04).
- **Visualizer.** Always `directed=True` (`visualizer.py:191`) even for the undirected co-citation/coupling graphs; node label is the DOI, not the computed `label`/title attribute (`:198`); `_sanitize_node_attrs` mutates the caller's graph (`builder.py:143-152`).
- **Tests are red at HEAD.** `test_cli.py:42` asserts the string "Graph built successfully", which the CLI no longer prints (it prints "Citation graph built!", `cli.py:114-116`); `test_scientometrics.py::test_compute_hits_single_node` and `::test_hits_single_node` expect `ValueError` but networkx 3.x raises `PowerIterationFailedConvergence` from the retry branch (`scientometrics.py:29-32`). Also `tests/test_cli.py` collides by basename with `scholar-verify-kit/tests/test_cli.py` (combined collection fails with "import file mismatch").
- **Harness coupling.** `pipeline/graph.py` imports `CitationGraphBuilder`/`GraphVisualizer` directly (`graph.py:57-58`); console actions shell out to `scholar-graph build` and `scholar-graph pagerank` (`actions.py:141-143,163`). Neither uses `ScientometricEngine`.

## 3. Correctness and bugs

**GRAPH-01 — High — Reproduced. OpenAlex failures are masked as a successful, edgeless graph with uniform PageRank.**
`fetch_work_data` catches everything and returns `None` (`builder.py:19-27`); the seed fallback then adds every requested DOI as an isolated node titled `Study <doi>` (`:89-105`).
Repro (client whose `get` raises `ConnectionError`): `nodes: ['10.1/a', '10.1/b']  edges: 0  pagerank: {'10.1/a': 1.0, '10.1/b': 1.0}`. The CLI then prints "Citation graph built! (Nodes: N, Edges: 0)" (`cli.py:114-116`) and writes HTML+JSON with exit 0.
Impact: a reviewer cannot distinguish "the included studies don't cite each other" from "OpenAlex was unreachable". The harness docstring claims the opposite ("a provider/builder/visualizer raise propagates with no fabricated graph", `pipeline/graph.py:40-42`) — the builder never raises for provider failure. 404s and non-200s are also indistinguishable from transport errors.

**GRAPH-02 — High — Reproduced. `scholar-graph build --mode coupling` and `--mode hybrid` crash.**
CliRunner: `mode=coupling exit=1 TypeError: … build_bibliographic_coupling() got an unexpected keyword argument 'min_jaccard'`; `mode=hybrid exit=1 TypeError: … build_hybrid_network() got an unexpected keyword argument 'alpha'`; `mode=cocitation exit=0`. The crash happens *after* the network fetch, so the work is lost.

**GRAPH-03 — Medium — Reproduced. DOI case creates duplicate phantom nodes; PageRank keys do not match node ids.**
Nodes are keyed by OpenAlex's (lowercase) DOI (`builder.py:56-59`), but the seed fallback compares the caller's raw string case-sensitively (`:92-95`). Repro with seeds `["10.1/A", "10.1/b"]`: `nodes: ['10.1/A', '10.1/a', '10.1/b']` — the same paper appears twice, once isolated. Separately, `compute_pagerank` lowercases keys (`:120`) while node ids keep their case: graph `10.1/ABC→10.1/X` yields keys `['10.1/abc', '10.1/x']` vs nodes `['10.1/ABC', '10.1/X']`, so any consumer joining PageRank to nodes by id misses mixed-case DOIs. Prefixes other than `https://doi.org/`/`http://doi.org/` (`doi:`, `https://dx.doi.org/`) are not stripped, and DOIs are not URL-encoded in the fetch URL (`:18`).
Impact: inflated node counts, a fake isolated "study", and a duplicate PageRank entry; DOIs in included.json are frequently mixed-case.

**GRAPH-04 — Medium — Reproduced. The PageRank the harness computes is discarded; HTML tooltips always show "PageRank: N/A".**
`compute_pagerank` returns a dict and never writes node attributes (`builder.py:110-124`). The harness calls it and ignores the return value (`pipeline/graph.py:116`) — a no-op. The visualizer reads `attrs.get("pagerank", "N/A")` (`visualizer.py:128`). Repro: generated HTML contains `PageRank:</b> N/A` for every node. (JSON is unaffected: `export_json` recomputes, `builder.py:137`.)

**GRAPH-05 — Medium — Reproduced. Bibliographic coupling is structurally empty; co-citation is restricted to the corpus.**
The builder keeps a reference edge only when the cited work is itself in the seed set (`builder.py:82-86`); all external `referenced_works` are discarded and not stored. `build_bibliographic_coupling` therefore only sees intra-corpus references (`scientometrics.py:207-211`). Repro: two included papers sharing three external references → `coupling edges: 0, nodes: 0`. Coupling also drops isolated nodes entirely (`:234-238`) whereas co-citation keeps them (`:167-168`) — the two networks are not comparable node sets.

**GRAPH-06 — Medium — Reproduced (source inspection). "Louvain" is CNM greedy modularity and the `--seed` is ignored.**
`detect_communities_louvain` calls `greedy_modularity_communities` (`scientometrics.py:328-332`); `seed` is accepted (`:305`) but never referenced in the body (checked programmatically: `seed referenced in body: False`). The code comment "networkx doesn't have exact Louvain" (`:326-327`) is false — `networkx.community.louvain_communities(seed=…)` exists since 2.8 and the installed version is 3.x. Output reports "Louvain" and a seed that implies reproducibility controls that do not exist (greedy modularity is deterministic, so the outcome is reproducible — but not for the stated reason, and not Louvain).

**GRAPH-07 — Low — Static. HITS fallback can still raise; role classification compares incomparable scales.**
The retry with `normalized=False` (`scientometrics.py:30-32`) raises the same `PowerIterationFailedConvergence` on degenerate graphs (the two failing tests). `classify_nodes_by_hits` requires `a_score > h_score` (`:97,101`), comparing hub and authority vectors normalised independently.

**GRAPH-08 — Low — Static.** `analyze --output` writes without `encoding` (`cli.py:313`) — cp1252 on Windows; undirected networks rendered with arrows (`visualizer.py:191`); PageRank on co-citation mode is computed on an undirected similarity graph and still labelled "PageRank" in JSON.

## 4. Research-method fitness

- **What the graph is.** Nodes = included studies resolvable in OpenAlex; edges = "included study A cites included study B". For a typical SLR corpus (tens of studies, often contemporaneous), this graph is sparse and frequently near-empty. That is a legitimate *descriptive* artifact (who in the corpus builds on whom), and the edge direction (citing → cited, `builder.py:86`) is correct for PageRank flowing to cited work.
- **PageRank as "importance".** README (`README.md:6`) and SKILL.md (`:12`) frame normalised PageRank as an "importance" metric used "to boost downstream semantic RAG retrieval". Within-corpus PageRank is dominated by (a) publication date — older studies can be cited by newer ones, never the reverse — and (b) the teleport baseline: in a disconnected graph every source and isolated node gets the same score (repro: `{'a': 0.37, 'c': 0.37, 'e': 0.37, 'z': 0.37, 'b': 0.69, 'd': 1.0}`, where `z` is isolated). An isolated node because OpenAlex failed (GRAPH-01) is scored identically to a genuinely uncited study. Max-normalisation (`builder.py:118-121`) discards absolute scale, so "1.0" in a 2-edge graph looks as authoritative as in a 2,000-edge one. None of this measures study quality or evidential weight; using it to re-rank retrieved evidence for synthesis biases the synthesis toward older, more-cited corpus members — a known citation bias, not a correction for one. If kept, it should be an exploratory view, never a retrieval weight, and the report should state graph density and the share of isolated nodes.
- **Co-citation / coupling.** These are standard science-mapping methods, but they are meaningful over the *full* reference lists (coupling) or the citing universe beyond the corpus (co-citation). Restricting both to intra-corpus links (GRAPH-05) makes them unrepresentative; a coupling network of a review corpus should, at minimum, use each study's complete `referenced_works`.
- **Communities.** Modularity communities on a sparse intra-corpus graph will mostly be singletons or date-driven chains; labelling them "Louvain" (GRAPH-06) in a methods section would be inaccurate.
- **Fitness for a PRISMA-style SLR.** The graph is not a PRISMA component and nothing in the harness depends on it for inclusion or synthesis decisions in-pipeline (`pipeline/graph.py:37-39`). The risk is downstream: PageRank re-ranking in RAG and narrative "hub/authority" claims built on GRAPH-01-masked or GRAPH-03-duplicated graphs.

## 5. Doc drift

- `docs/tutorial.md:22` documents a `--direction forward|backward|both` option; no such option exists (`cli.py:29-67`). `docs/api_reference.md:14` shows `build_graph(seed_dois=…, direction="both")`; the signature is `build_graph(dois, progress_callback=None)` (`builder.py:29`).
- `README.md:6,12` — "fetches … citation and co-citation structures"; "Citation & Co-Citation Graph Builder (`CitationGraphBuilder`)": the builder has no co-citation logic; it exists only in `ScientometricEngine` via `--mode cocitation`.
- `docs/kits_surface_matrix.md` (graph section) — "**no co-citation logic exists**" and CLI listed as `build/pagerank` only: co-citation exists (`scientometrics.py:123-187`), and `cluster`, `analyze`, `visualize` commands exist (`cli.py:212,268,319`).
- `SKILL.md:144` — "a provider-unreachable run may never be reported as an empty successful result": refuted by GRAPH-01.
- `src/scholar_harness/pipeline/graph.py:40-42` — "a provider/builder/visualizer raise propagates": the builder never raises on provider failure (GRAPH-01).

## 6. Prioritized recommendations

Source fixes belong in `nexus-scholar-org/scholar-graph-kit` (then bump `plugins.json` `default_rev` and re-vendor); the harness discard (GRAPH-04) is a harness fix in this repo.

| ID | Severity | Effort | Action |
|---|---|---|---|
| GRAPH-01 | High | S | Count fetch outcomes (ok / 404 / error); include them in JSON metadata; exit non-zero (or mark `status: DEGRADED`) when errors > 0; stop catching bare `Exception` |
| GRAPH-02 | High | S | Fix kwargs (`min_overlap`, `weight_*`), add a CLI test per `--mode` |
| GRAPH-03 | Medium | S | Normalise DOIs once (strip any doi.org/`doi:` prefix, lowercase, trim) at the CLI/builder boundary; URL-encode in the fetch; keep PageRank keys identical to node ids |
| GRAPH-04 | Medium | S | Have `compute_pagerank` (or the harness) write `pagerank` onto node attrs before `generate_html`; drop the no-op call in `pipeline/graph.py:116` |
| GRAPH-05 | Medium | M | Store full `referenced_works` per node; compute coupling over full reference lists; document co-citation scope |
| GRAPH-06 | Medium | S | Use `nx.community.louvain_communities(seed=…)` or rename to "greedy modularity (CNM)" and drop `--seed` |
| §4 PageRank | Medium | S | Report density, isolated-node share and fetch failures alongside PageRank; document it as exploratory, not as an evidence weight; reconsider using it for RAG re-ranking |
| Tests | Medium | S | Fix `test_cli.py:42` string and the two HITS single-node tests; rename `tests/test_cli.py` to a unique basename |
| GRAPH-07/08 | Low | S | Guard HITS on degenerate graphs; `encoding="utf-8"` on writes; `directed=G.is_directed()` in the visualizer; delete `config.py`/`models.py` or wire them in |

## 7. Limits of this assessment

- No live OpenAlex calls; all graph builds used a stub client. OpenAlex-side issues (merged work ids in `referenced_works`, DOI casing in responses) were not measured.
- The RAG consumer of `knowledge_graph.json` (`scholar-rag-kit` retriever) was not read; whether it lowercases node ids before joining PageRank (GRAPH-03) is unverified.
- Rendered HTML was inspected as text, not in a browser; vis-network's treatment of HTML in tooltips was not checked.
- No real workspace existed to measure typical graph density; §4's sparsity claim is a methodological expectation, not a measurement.
