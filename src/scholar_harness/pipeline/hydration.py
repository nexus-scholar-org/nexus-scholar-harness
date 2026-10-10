"""Hydration stage (HCM-04d neutral extraction).

Stage 2.5 of the research pipeline: abstract backfill for documents with
missing abstracts, the ``ABSTRACT_HYDRATION`` audit event, and HTTP client
lifecycle. Extracted verbatim from
``ResearchOrchestrator.run_pipeline_async`` so the orchestrator delegates
without behavior change.

Unlike the discovery/deduplication stages, this stage emits the pipeline's
first audit event (``ABSTRACT_HYDRATION``). It calls
``workspace.audit.append_legacy_event`` directly with the same arguments the
orchestrator's thin ``_log_audit_event`` adapter passed through -- same
action, agent, description (pre-hydration document count), inputs, outputs,
metrics (verbatim stats mapping), and default ``SUCCESS`` status -- so the
journal bytes are unchanged. It writes no registry/acceptance state.

Order is hard: hydrate, then audit, then client close (``finally``), so a
close failure can never suppress a recorded success. Failure propagates
with no fabricated documents, audit rows, or success claims, and the close
is still attempted on every path.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scholar_harness.workspace.audit import append_legacy_event
from scholar_search.enrichment import AbstractHydrator
from scholar_search.http_client import AcademicHttpClient

logger = logging.getLogger(__name__)


@dataclass
class HydrationOutcome:
    """Typed outcome of the hydration stage: hydrated docs plus kit stats."""

    documents: list[Any]
    stats: dict[str, int]


async def run_hydration(
    *,
    documents: list[Any],
    workspace_dir: Path | str,
) -> HydrationOutcome:
    """Backfill missing abstracts over ALL input documents and audit the run.

    Verbatim move of orchestrator Stage 2.5: ``AcademicHttpClient`` built with
    the exact ``name="hydration"`` / ``rate_limit=10`` arguments,
    ``AbstractHydrator(client).hydrate_missing_abstracts`` over ALL
    ``documents`` (never a subset), the ``Hydration complete`` log line at
    the same position, the ``ABSTRACT_HYDRATION`` legacy audit event with the
    pre-hydration document count in its description, and ``await
    client.close()`` in a ``finally`` so the close runs on success and on
    failure alike.

    Kit, audit, or close failure propagates unchanged: no fabricated
    documents, no success audit row, no outcome is returned.
    """
    client = AcademicHttpClient(name="hydration", rate_limit=10)
    try:
        hydrator = AbstractHydrator(client)
        hydrated_docs, hydration_stats = await hydrator.hydrate_missing_abstracts(
            documents
        )
        logger.info(f"Hydration complete: {hydration_stats}")

        append_legacy_event(
            workspace_dir,
            "ABSTRACT_HYDRATION",
            "scholar-harness",
            f"Hydrated missing abstracts for {len(documents)} documents",
            [],
            [],
            hydration_stats,
        )
        return HydrationOutcome(documents=hydrated_docs, stats=hydration_stats)
    finally:
        await client.close()
