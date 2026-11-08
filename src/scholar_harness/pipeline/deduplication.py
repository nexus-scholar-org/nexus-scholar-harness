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

    # M7-method: the workspace protocol's dedup tiers (defaults when it sets none),
    # so a discovery corpus is deduplicated as the methods paragraph reports.
    from scholar_harness.screening.method import effective_method

    method = effective_method(lit_dir.parent)
    if method.source == "protocol":
        tiers = method.config.dedup
        deduplicator = Deduplicator(
            title_similarity=tiers.title_similarity,
            first_author=tiers.first_author,
            year_tolerance=tiers.year_tolerance,
        )
    else:
        deduplicator = Deduplicator()
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
    return DeduplicationOutcome(
        representatives=unique_docs,
        unique=len(unique_docs),
        duplicates_removed=dupes_removed,
    )
