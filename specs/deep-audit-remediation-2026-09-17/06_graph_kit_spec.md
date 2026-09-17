# Scholar Graph Kit Remediation Specification

**Status:** Draft for implementation  
**Date:** 2026-09-17  
**Owner:** `scholar-graph-kit` maintainers  
**Priority:** P0 broken modes; P1 provenance and failure semantics  
**Scope:** graph API/CLI, scientometrics, visualization, RAG and MCP adapters

## Scientific claim boundary

A citation edge is a provider-observed bibliographic relation. Co-citation and
bibliographic coupling are derived structural relations. PageRank, HITS,
betweenness, and community membership describe the observed graph; none is a
direct measure of study quality, evidence strength, agreement, or causal impact.
Missing nodes/edges may reflect provider and identifier coverage.

`workspace_id` scopes a corpus. `study_id` identifies one paper and is the primary
graph-node identity. DOI/OpenAlex identifiers are aliases. Graph metrics consumed
by RAG must resolve to the same canonical `study_id`.

## Current architecture and data flow

`CitationGraphBuilder` fetches OpenAlex works, adds seed nodes and intra-pool
citation edges, computes PageRank, and exports node-link/XML formats
(`tools/scholar-graph-kit/src/scholar_graph/builder.py:12-191`).
`ScientometricEngine` computes HITS, betweenness, classification, co-citation,
bibliographic coupling, hybrid transforms, and communities
(`tools/scholar-graph-kit/src/scholar_graph/scientometrics.py:9-391`).
`GraphVisualizer` copies graph data into PyVis and renders HTML
(`tools/scholar-graph-kit/src/scholar_graph/visualizer.py:58-242`). The CLI exposes
`build`, `pagerank`, `cluster`, `analyze`, and `visualize`
(`tools/scholar-graph-kit/src/scholar_graph/cli.py:29-350`). The harness Stage 8
uses a real search-kit HTTP client and emits JSON/HTML
(`src/scholar_harness/orchestrator.py:777-799`).

## Confirmed findings

1. `build --mode coupling` passes nonexistent `min_jaccard` at
   `tools/scholar-graph-kit/src/scholar_graph/cli.py:127-132`; the API expects
   `min_overlap` at `scientometrics.py:189-200`. The mode raises `TypeError`.
2. `build --mode hybrid` passes nonexistent `alpha` at `cli.py:135-140`; the API
   expects `weight_cocite`, `weight_couple`, and `min_weight` at
   `scientometrics.py:245-256`. The mode raises `TypeError`.
3. Co-citation creates bare nodes (`scientometrics.py:163-169`); coupling includes
   only nodes participating in candidate pairs and drops metadata/isolates
   (`:223-243`); hybrid likewise recreates bare nodes (`:270-300`). Titles, years,
   citations, and complete corpus membership are lost.
4. The operation documented as Louvain calls
   `greedy_modularity_communities`; the supplied seed is unused
   (`scientometrics.py:304-340`). CLI help therefore promises a different
   algorithm and reproducibility control.
5. Fetch exceptions are swallowed (`builder.py:18-27`), producing fallback
   isolated nodes that can look like a valid graph. PageRank exceptions become
   uniform `1.0` scores (`builder.py:109-124`), conflating a computational failure
   with a legitimate edgeless/uniform result.
6. `Settings.max_concurrent_requests` and email are not applied; all DOI fetches
   are scheduled together (`builder.py:29-47`). Large pools have no toolkit-level
   concurrency bound.
7. `config.py` imports `pydantic_settings`, and scientometric classification uses
   NumPy, but neither is declared in runtime dependencies
   (`tools/scholar-graph-kit/pyproject.toml:14-22`). The shared environment masks
   clean-install failure.
8. CLI `--format` is misleading: HTML and JSON are always written, while the
   option only gates additional XML formats (`cli.py:150-176`).
9. A nonexistent `--input` path falls through to “No DOIs” and exits successfully
   (`cli.py:71-91`), hiding pipeline/input mistakes.
10. DOI normalization occurs after response, not at request ingress
    (`builder.py:18`, `:56-59`, `:92-94`). URL-form DOI input can produce an invalid
    doubled request path; node case and lowercased PageRank keys can diverge.
11. Visualizer forces directed rendering even for transformed undirected graphs
    (`visualizer.py:186-192`). GEXF/GraphML completeness checks accept partially
    populated PageRank attributes (`builder.py:164-190`).
12. Documentation is materially stale: API/tutorial describe nonexistent classes
    and even the wrong executable; the skill/surface matrix still describes the
    former zero-edge MCP bug and denies transforms that now exist. Current MCP uses
    a real client (`tools/scholar-agent-kit/src/scholar_agent/server.py:783-811`).
13. Toolkit tests observed 77 passes and one stale CLI-message assertion failure;
    the broken coupling/hybrid modes and dependency isolation are not covered.

## Goals

- Make every advertised graph mode execute against one stable typed API.
- Preserve canonical study nodes, metadata, isolates, and provenance across
  transformations.
- Make provider and metric failure distinguishable from valid sparse graphs.
- Align algorithm names/options with implementation.
- Provide a stable graph/RAG identity contract and truthful format behavior.

## Non-goals

- Treating centrality or community membership as research quality.
- Inferring missing citation relations.
- Guaranteeing field-wide graph completeness from an included corpus.
- Keeping incorrect CLI option names indefinitely.

## Normative requirements

Requirement IDs: the numbered requirements below carry stable IDs `GR-001`…`GR-016`
(requirement *n* = `GR-0nn`). Regression tests and the traceability ledger required
by `11_validation_and_test_plan.md` (VAL-001, §11–§12) MUST reference these IDs.

1. All documented `build --mode` values MUST execute through typed request
   models whose argument names match the domain API.
2. The canonical study-node roster MUST survive citation, co-citation, coupling,
   and hybrid transforms, including isolates and uncoupled studies unless a
   separately named projection explicitly filters them.
3. Every transformed node MUST retain canonical `study_id`, title, year,
   citations, external IDs, resolution state, and source provenance where known.
4. Derived edges MUST declare `relation_type` (`cites`, `co_cited`,
   `bibliographically_coupled`, or hybrid component), weight, algorithm version,
   and derivation parameters.
5. The community operation MUST either call actual seeded Louvain or be renamed
   to greedy modularity and reject/retire `seed`. Help, API, and docs MUST match.
6. Fetch results MUST include per-study `resolved|not_found|provider_failed|
   malformed|cancelled` outcomes. A graph with failures MUST be `PARTIAL` unless
   strict mode rejects publication.
7. PageRank computation failures MUST be errors. Uniform valid scores on an
   edgeless graph MUST be labeled as structurally uninformative, not silently used
   as a failure fallback.
8. Fetch concurrency, timeouts, retries, and provider rate limits MUST be bounded,
   configurable, and recorded.
9. DOI/provider identities MUST be normalized once at ingress; requests must be
   URL-safe; graph nodes and PageRank maps MUST use canonical `study_id`.
10. `--input` supplied but missing/unreadable MUST produce nonzero structured
    failure. An intentionally empty valid input MUST be distinguishable.
11. Output format selection MUST be literal: requested formats are emitted and
    unrequested formats are not, except an explicitly documented manifest.
12. Visualization MUST preserve graph directedness and operate on a copy. It MUST
    not modify canonical graph attributes.
13. XML export MUST populate required attributes for every node or fail
    validation; an `any(node has pagerank)` check is insufficient.
14. `numpy` and `pydantic-settings` MUST be declared if retained; clean-wheel
    imports and every CLI subcommand `--help` MUST pass.
15. API, CLI, MCP, and harness adapters MUST use the same build/transform service,
    schemas, identity normalization, defaults, and error semantics.
16. Graph and metric artifacts MUST be versioned, atomically written, and include
    workspace/corpus fingerprint, requested/resolved/failure counts, algorithms,
    parameters, provider, timestamps, and input/output hashes.

## API, data, and CLI behavior

Introduce typed `GraphBuildRequest`, `GraphTransformRequest`, `GraphBuildOutcome`,
`GraphMetricOutcome`, `StudyNode`, and `DerivedEdge` models. Keep NetworkX graphs
as internal computation objects; public results include the graph plus item-level
resolution diagnostics.

CLI behavior:

- `build --mode citation|cocitation|coupling|hybrid` validates mode-specific
  options before any network call;
- `--format html|json|gexf|graphml|all` emits exactly the named formats;
- `--allow-partial` controls publication after fetch failures;
- `--concurrency`, `--timeout`, and metric parameters are recorded;
- `--json` emits the shared outcome envelope;
- missing input exits with validation error.

MCP and harness must accept the same data request, except transport-only fields.
RAG receives a `study_id -> pagerank` map plus graph fingerprint; alias guessing is
not part of RAG retrieval.

## Migration and backward compatibility

1. Version graph schema v2; continue reading v1 through an explicit adapter.
2. Convert legacy DOI/case node IDs to canonical study IDs using a dry-run mapping;
   block commit on collisions.
3. Preserve old max-normalized values as `pagerank_max_normalized`; expose raw
   probability PageRank separately.
4. Keep old CLI flags as aliases for one release where unambiguous. Invalid
   coupling/hybrid names may map to corrected names with deprecation warnings.
5. Strip presentation-only attributes during v1 conversion and retain the source
   file hash/migration record.

## Work plan

### P0

1. Fix coupling/hybrid signature mismatches and add end-to-end tests for every
   mode.
2. Preserve node roster/metadata/isolates in every transform.
3. Decide and implement actual Louvain or truthful greedy-modularity naming.
4. Stop converting fetch/PageRank exceptions into successful-looking outputs.

### P1

1. Implement canonical study IDs, DOI ingress normalization, and RAG mapping.
2. Add bounded concurrency and structured per-item outcomes.
3. Make format selection truthful; validate XML completeness and directedness.
4. Correct dependency metadata and isolated-package tests.
5. Version and atomically publish graph/provenance artifacts.

### P2

1. Add transform complexity benchmarks and declared safe pool sizes.
2. Add optional external-reference nodes under a distinct scope mode.
3. Rewrite README, tutorial, API reference, skill, and surface matrix.

## Failure-focused test matrix

| Area | Cases | Required assertion |
|---|---|---|
| Modes | citation, co-citation, coupling, hybrid with common fixture | all parse and execute; correct typed parameters |
| Metadata | isolates, uncoupled nodes, failed seed, transform chain | complete roster and attributes preserved |
| Community | seeded Louvain or greedy mode; repeated runs | documented algorithm and deterministic semantics |
| Fetch | 404, 429, timeout, malformed JSON, cancellation | bounded attempts; item failures; honest overall status |
| PageRank | empty, edgeless, disconnected, nonconvergence | valid warnings versus computation failure separated |
| DOI | resolver URL, `doi:` prefix, case, punctuation, duplicate aliases | one URL-safe canonical study node |
| Input | missing path, malformed list/dict, empty valid corpus | nonzero errors versus explicit empty outcome |
| Format | each format and `all` | only requested artifacts; schemas load successfully |
| Transform | title/year/citation/isolate preservation | no bare recreated nodes; deterministic edges/weights |
| Visualization | directed and undirected inputs | direction preserved; source graph unchanged |
| Packaging | clean wheel import and scientometric call | all direct dependencies present |
| Surface parity | API/CLI/MCP same fixture | identical nodes, edges, metrics, warnings, failures |
| RAG join | canonical ID, alias collision, absent graph node | boost only on unambiguous canonical study ID |

## Definition of done

- Coupling and hybrid modes no longer raise signature errors.
- Every transform preserves the complete study roster and metadata.
- Community help/API names match the implemented algorithm and seed behavior.
- No provider or PageRank failure appears as valid isolated/uniform success.
- Format behavior, identity, graph direction, and XML completeness are tested.
- Clean wheel and entrypoints pass with declared dependencies only.
- API/CLI/MCP/harness parity tests and full repository tests pass.
- Canonical kit repository, vendored snapshot, plugin pin, skills, and matrix agree.

## Dependencies and risks

The kit relies on search-kit's HTTP client and provides PageRank to RAG. Identity
changes therefore require search/RAG contract coordination. Preserving isolates
may change transformed graph counts; correcting algorithms can change published
metrics. Migration must retain old artifacts and label recomputed values rather
than silently replacing them. Pairwise transforms may be expensive on dense
graphs and need bounded benchmarks.

## Documentation updates

Rewrite the README, tutorial, and API reference from live symbols. Update CLI/MCP
help, `scholar-graph-kit` skill, surface matrix, JSON schemas, and RAG integration
guide. Explicitly document graph scope, each relation type, edge direction,
algorithm parameters, failure/partial semantics, centrality limitations, and
supported package dependencies.

