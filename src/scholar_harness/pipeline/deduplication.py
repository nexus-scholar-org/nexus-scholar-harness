"""Deduplication stage (HCM-04c neutral extraction).

Stage 2 of the research pipeline: 2-tier deduplication, PID cluster
assignment, and deduped-result publication. Extracted verbatim from
``ResearchOrchestrator.run_pipeline_async`` so the orchestrator delegates
without behavior change.

Neutrality: stdlib plus ``scholar-search-kit`` only -- no console transport,
no Contract v1 acceptance, no workspace audit. The stage emits **no** audit
event and writes **no** registry/acceptance state; the first pipeline audit
event remains ``ABSTRACT_HYDRATION`` downstream of this stage.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scholar_search.dedup import Deduplicator, stable_order

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationOutcome:
    """Typed outcome of the deduplication stage.

    ``representatives`` are the per-cluster representatives (the ``unique_docs``
    binding Stage 2.5 hydrates); ``unique`` is their count and
    ``duplicates_removed`` is ``len(input) - len(unique)``.
    """

    representatives: list[Any]
    unique: int
    duplicates_removed: int

    @property
    def documents(self) -> list[Any]:
        """Alias for ``representatives`` (DiscoveryOutcome parity)."""
        return self.representatives

    @property
    def unique_docs(self) -> list[Any]:
        """Alias for ``representatives`` (orchestrator Stage 2.5 binding)."""
        return self.representatives


#: E4a (M3d-engine): the per-cluster record of the deduplication, beside deduped.json.
CLUSTERS_FILE = Path("dedup") / "clusters.json"


def _newest_run(lit_dir: Path) -> str | None:
    """The search run this deduplication follows.

    The newest run published as the corpus: deduplication only ever runs on
    that run's records, right after its search or when its preparation is
    finished later (M3i). A newer folder can be a search that was stopped,
    which is not deduplicated. Without a published run (a bare folder), the
    newest run folder, as before.
    """
    from .harvest_marker import corpus_run_dir

    corpus_run = corpus_run_dir(lit_dir)
    if corpus_run is not None:
        return corpus_run.name
    runs_dir = lit_dir / "search_runs"
    if not runs_dir.is_dir():
        return None
    numbers = [int(d.name[4:]) for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_") and d.name[4:].isdigit()]
    return f"run_{max(numbers):03d}" if numbers else None


def _record(doc: Any) -> dict[str, Any]:
    ext = getattr(doc, "external_ids", None)
    return {
        "workspace_id": getattr(doc, "workspace_id", None),
        "provider": getattr(doc, "provider", None),
        "provider_id": getattr(doc, "provider_id", None),
        "doi": getattr(ext, "doi", None),
        "title": getattr(doc, "title", None),
        "year": getattr(doc, "year", None),
    }


def _merged_by(cluster: Any, index: int) -> str | None:
    merges = list(getattr(cluster, "merges", None) or [])
    return merges[index - 1] if 0 < index <= len(merges) else None


def _deduplicator(lit_dir: Path) -> tuple[Deduplicator, str]:
    """The deduplicator the workspace's protocol asks for, and where its tiers come from.

    M7-method: the protocol's dedup tiers (defaults when it sets none), so a
    discovery corpus is deduplicated as the methods paragraph reports.
    """
    from scholar_harness.screening.method import effective_method

    method = effective_method(lit_dir.parent)
    if method.source == "protocol":
        tiers = method.config.dedup
        return Deduplicator(
            title_similarity=tiers.title_similarity,
            first_author=tiers.first_author,
            year_tolerance=tiers.year_tolerance,
        ), "protocol"
    return Deduplicator(), "default"


def _method_record(deduplicator: Deduplicator, source: str) -> dict[str, Any]:
    return {
        "title_similarity": getattr(deduplicator, "title_similarity", None),
        "year_tolerance": getattr(deduplicator, "year_tolerance", None),
        "first_author": getattr(deduplicator, "first_author", None),
        "source": source,
    }


def current_method(literature_dir: Path | str) -> dict[str, Any]:
    """The method a deduplication run now would record (``clusters.json`` ``method``).

    M3i-harvest-robustness: a harvest is finished from ``deduped.json`` only
    when that file was made with the tiers the protocol asks for today.
    """
    return _method_record(*_deduplicator(Path(literature_dir)))


def _write_clusters(lit_dir: Path, clusters: list[Any], deduplicator: Deduplicator, source: str) -> None:
    """``literature/dedup/clusters.json``: which tier merged each cluster (E4a, packet §4.5).

    ``tier`` is the tier of the cluster's first merge (``None`` for a
    singleton); each member after the first says which tier merged it
    (``merged_by``), so the counts per tier add up to the records removed.
    Writes nothing the snapshot or the ids depend on.
    """
    data = {
        "schema": "nexus.dedup-clusters.v1",
        "run": _newest_run(lit_dir),
        "method": _method_record(deduplicator, source),
        "clusters": [
            {
                "cluster_id": cluster.cluster_id,
                "tier": getattr(cluster, "tier", None),
                "representative": _record(cluster.representative),
                "members": [
                    {**_record(member), "merged_by": _merged_by(cluster, i)}
                    for i, member in enumerate(cluster.members)
                ],
            }
            for cluster in clusters
        ],
    }
    path = lit_dir / CLUSTERS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def run_deduplication(
    *,
    discovered_documents: list[Any],
    literature_dir: Path | str,
) -> DeduplicationOutcome:
    """Deduplicate all discovered documents and publish the deduped corpus.

    Verbatim move of orchestrator Stage 2: ``Deduplicator().deduplicate`` over
    ALL ``discovered_documents`` (never a subset), representative election,
    ``duplicates_removed = len(input) - len(unique)``, then identical
    ``asdict``/``json`` serialization into ``deduped.json``.

    The deduplicator assigns ``workspace_id`` (``SCI-XXXXXX``) here. No audit
    event is emitted and no registry/acceptance state is touched.
    """
    lit_dir = Path(literature_dir)
    lit_dir.mkdir(parents=True, exist_ok=True)

    deduplicator, source = _deduplicator(lit_dir)
    # CORE-06: content order, not arrival order, so a re-run gives the same ids.
    clusters = deduplicator.deduplicate(stable_order(discovered_documents))
    unique_docs = [c.representative for c in clusters]
    dupes_removed = len(discovered_documents) - len(unique_docs)

    # Byte-equivalent serialization of the orchestrator slice (asdict/indent=2/default=str).
    payload = json.dumps(
        [asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in unique_docs],
        indent=2,
        default=str,
    )
    (lit_dir / "deduped.json").write_text(payload, encoding="utf-8")
    _write_clusters(lit_dir, clusters, deduplicator, source)
    return DeduplicationOutcome(
        representatives=unique_docs,
        unique=len(unique_docs),
        duplicates_removed=dupes_removed,
    )
