"""Graph stage (HCM-04j neutral extraction).

Stage 8 of the research pipeline: citation knowledge graph and PageRank
over included studies. Extracted verbatim from
``ResearchOrchestrator.run_pipeline_async`` (:704-727) so the orchestrator
delegates without behavior change.

Preservation notes:

- Client construction is verbatim: ``AcademicHttpClient`` with the exact
  ``name="openalex-graph"`` / ``rate_limit=10`` arguments, passed
  positionally to ``CitationGraphBuilder(client)`` exactly as the base
  Stage 8 did. The client is deliberately NOT closed here: the base never
  closed the graph client (no ``close`` in :704-727), so adding one would
  be a lifecycle change. Lifecycle is identical (client per call, no
  close).
- DOI collection is verbatim: ``[d for d in (_study_doi(doc) for doc in
  included_documents) if d]`` over ALL included documents, with
  ``_study_doi`` imported from its canonical HCM-04g home
  (``pipeline.extraction``) -- never duplicated here.
- Empty-DOI seeding is verbatim: no DOIs resolve to a seeded empty
  ``nx.DiGraph()`` so downstream reads stay valid, with truthful 0
  node/edge counts (never a fabricated success claim).
- ``build_graph`` is awaited with the DOI list; ``compute_pagerank`` is
  called at class level on the resolved builder class (the base called it
  on ``CitationGraphBuilder``; the static shape is identical); ``export_json``
  publishes ``literature/knowledge_graph.json`` and ``GraphVisualizer``
  (constructed with ``str(html_path)``) publishes
  ``literature/knowledge_graph.html``. Filenames, locations,
  serialization, ordering, and shapes are byte-compatible via the
  identical kit calls.
- The stage emits NO audit event and writes NO registry/acceptance state;
  the orchestrator maps the outcome to the identical
  ``results["stages"]["graph_nodes"]`` payload (``status DONE``,
  ``nodes`` / ``edges`` counts). Stage 10 still logs the html path later,
  unchanged.
- Downstream binding: nothing consumes ``G`` in-pipeline (Stage 9 reuses
  the Stage-7 ``retriever``, not the graph), so the outcome carries only
  counts plus the json/html paths.
- Error propagation unchanged: a provider/builder/visualizer raise
  propagates with no fabricated graph, no ``DONE`` mapping, and no
  success claim.

Neutrality: stdlib plus ``scholar-graph-kit`` (builder/visualizer),
``scholar-search-kit`` (client), and ``networkx`` only -- no console
transport, no Contract v1 acceptance, no workspace audit.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from scholar_graph.builder import CitationGraphBuilder
from scholar_graph.visualizer import GraphVisualizer
from scholar_search.http_client import AcademicHttpClient

from .extraction import _study_doi

logger = logging.getLogger(__name__)


# Kit classes captured at import time so the legacy orchestrator-namespace
# seams below can tell a monkeypatched fake apart from the real kit class.
_REAL_BUILDER = CitationGraphBuilder
_REAL_VISUALIZER = GraphVisualizer


@dataclass
class GraphOutcome:
    """Typed outcome of the graph stage.

    ``nodes`` / ``edges`` are ``G.number_of_nodes()`` /
    ``G.number_of_edges()`` (the counts the orchestrator maps to
    ``stages["graph_nodes"]``); ``json_path`` / ``html_path`` are the
    ``literature/knowledge_graph.{json,html}`` paths published by
    ``export_json`` / ``generate_html``.
    """

    nodes: int
    edges: int
    json_path: Path
    html_path: Path


def _builder_class() -> type[CitationGraphBuilder]:
    """Return the ``CitationGraphBuilder`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.CitationGraphBuilder`` with a fake builder
    (fidelity ``:196``, extraction-stage ``:764``, matrix-stage ``:549``).
    The orchestrator no longer constructs the builder itself, so the stage
    honors an orchestrator-namespace override when it differs from the kit
    class and otherwise uses this module's own global (which tests may also
    patch directly). Transitional HCM-04j seam: a later stub-migration packet
    should migrate the fidelity stubs to patch
    ``scholar_harness.pipeline.graph.CitationGraphBuilder`` directly and drop
    the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("CitationGraphBuilder")
        if candidate is not None and candidate is not _REAL_BUILDER:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return CitationGraphBuilder


def _visualizer_class() -> type[GraphVisualizer]:
    """Return the ``GraphVisualizer`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.GraphVisualizer`` with a fake visualizer
    (fidelity ``:197``, extraction-stage ``:765``, matrix-stage ``:550``).
    The orchestrator no longer constructs the visualizer itself, so the
    stage honors an orchestrator-namespace override when it differs from
    the kit class and otherwise uses this module's own global (which tests
    may also patch directly). Transitional HCM-04j seam: a later
    stub-migration packet should migrate the fidelity stubs to patch
    ``scholar_harness.pipeline.graph.GraphVisualizer`` directly and drop
    the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("GraphVisualizer")
        if candidate is not None and candidate is not _REAL_VISUALIZER:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return GraphVisualizer


async def run_graph(
    *,
    included_documents: list[dict[str, Any]],
    literature_dir: Path | str,
) -> GraphOutcome:
    """Build the citation graph, compute PageRank, publish json + html.

    Verbatim move of orchestrator Stage 8 (:704-727):
    ``AcademicHttpClient(name="openalex-graph", rate_limit=10)`` via the
    resolved ``_builder_class()``, DOI collection via the canonical
    ``_study_doi`` with falsy filtering, ``await build_graph(dois)`` or a
    seeded empty ``nx.DiGraph()`` when no DOIs exist, class-level
    ``compute_pagerank(G)``, ``export_json`` to
    ``literature/knowledge_graph.json``, then the resolved
    ``_visualizer_class()(str(html_path))`` with ``generate_html(G)``.

    Only mechanical parameterization: ``included_documents`` /
    ``literature_dir`` inputs. No logic edits, no renames of
    filenames/client args/call shapes, no client close (the base never
    closed the graph client), no audit event, no registry writes. Kit
    failure propagates with no fabricated graph and no success mapping.
    """
    lit_dir = Path(literature_dir)
    builder_cls = _builder_class()
    graph_builder = builder_cls(
        AcademicHttpClient(name="openalex-graph", rate_limit=10)
    )
    dois = [d for d in (_study_doi(doc_item) for doc_item in included_documents) if d]
    if dois:
        G = await graph_builder.build_graph(dois)
    else:
        # No DOIs to resolve: seed an empty graph so downstream reads stay valid.
        G = nx.DiGraph()
    builder_cls.compute_pagerank(G)
    json_path = lit_dir / "knowledge_graph.json"
    graph_builder.export_json(G, json_path)

    html_path = lit_dir / "knowledge_graph.html"
    vis = _visualizer_class()(str(html_path))
    vis.generate_html(G)
    return GraphOutcome(
        nodes=G.number_of_nodes(),
        edges=G.number_of_edges(),
        json_path=json_path,
        html_path=html_path,
    )
