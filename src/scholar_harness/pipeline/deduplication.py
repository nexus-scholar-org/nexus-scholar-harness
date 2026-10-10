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

from scholar_search.dedup import Deduplicator

logger = logging.getLogger(__name__)


# Kit class captured at import time so the legacy orchestrator-namespace seam
# below can tell a monkeypatched fake apart from the real deduplicator.
_REAL_DEDUPLICATOR = Deduplicator


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


def _deduplicator_class() -> type[Deduplicator]:
    """Return the ``Deduplicator`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.Deduplicator`` with a fake deduplicator. The
    orchestrator no longer constructs the deduplicator itself, so the stage
    honors an orchestrator-namespace override when it differs from the kit
    class and otherwise uses this module's own global (which tests may also
    patch directly). Transitional HCM-04c seam: a later packet should migrate
    the fidelity stubs to patch
    ``scholar_harness.pipeline.deduplication.Deduplicator`` directly and drop
    the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("Deduplicator")
        if candidate is not None and candidate is not _REAL_DEDUPLICATOR:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return Deduplicator


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

    deduplicator = _deduplicator_class()()
    clusters = deduplicator.deduplicate(discovered_documents)
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
