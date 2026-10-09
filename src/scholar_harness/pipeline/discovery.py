"""Discovery stage (HCM-04b neutral extraction).

Stage 1 of the research pipeline: protocol-query compilation, federated
search, and raw-result publication. Extracted verbatim from
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

from scholar_search.engine import SearchEngine
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.providers import (
    ArxivProvider,
    BaseAPIProvider,
    BiorxivProvider,
    CrossrefProvider,
    OpenAlexProvider,
    PubMedProvider,
    SearchProvider,
    SemanticScholarProvider,
)

logger = logging.getLogger(__name__)


# Kit class captured at import time so the legacy orchestrator-namespace seam
# below can tell a monkeypatched fake apart from the real engine.
_REAL_SEARCH_ENGINE = SearchEngine


_PROVIDER_MAP: dict[str, type[SearchProvider]] = {
    "openalex": OpenAlexProvider,
    "semanticscholar": SemanticScholarProvider,
    "semantic_scholar": SemanticScholarProvider,
    "crossref": CrossrefProvider,
    "arxiv": ArxivProvider,
    "pubmed": PubMedProvider,
    "biorxiv": BiorxivProvider,
}


def _resolve_providers(providers: list[Any] | None) -> list[SearchProvider] | None:
    """Resolve provider instances from names (strings) or existing instances."""
    if not providers:
        return None
    instances: list[SearchProvider] = []
    for p in providers:
        if isinstance(p, str):
            key = p.lower().strip().replace("-", "_").replace(" ", "_")
            cls = _PROVIDER_MAP.get(key)
            if cls:
                instances.append(cls())
            else:
                logger.warning("Unknown search provider: %s", p)
        elif isinstance(p, BaseAPIProvider) or hasattr(p, "search"):
            instances.append(p)
        else:
            logger.warning("Unexpected provider item: %r", p)
    return instances if instances else None


@dataclass
class DiscoveryOutcome:
    """Typed outcome of the discovery stage: raw documents plus their count."""

    documents: list[Any]
    count: int


def _search_engine_class() -> type[SearchEngine]:
    """Return the ``SearchEngine`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.SearchEngine`` with a fake engine. The
    orchestrator no longer constructs the engine itself, so the stage honors
    an orchestrator-namespace override when it differs from the kit class and
    otherwise uses this module's own global (which tests may also patch
    directly). Transitional HCM-04b seam: HCM-04c should migrate the fidelity
    stubs to patch ``scholar_harness.pipeline.discovery.SearchEngine``
    directly and drop the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("SearchEngine")
        if candidate is not None and candidate is not _REAL_SEARCH_ENGINE:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return SearchEngine


async def run_discovery(
    *,
    protocol_path: Path | str,
    literature_dir: Path | str,
    max_search_results: int | None = None,
) -> DiscoveryOutcome:
    """Compile the protocol query, run federated search, publish raw results.

    Verbatim move of orchestrator Stage 1: ``compile_protocol_search``,
    ``max_search_results`` override, ``SearchEngine`` construction via
    ``_resolve_providers``, ``search_all(query, dedup=False)``, ``close()``,
    then identical ``asdict``/``json`` serialization into
    ``all_raw_search.json`` and ``raw_search.json``.

    Provider failure propagates (never an empty success); no audit event is
    emitted and no registry/acceptance state is touched.
    """
    p_path = Path(protocol_path).resolve()
    if not p_path.exists():
        raise FileNotFoundError(f"Protocol file not found at {p_path}")

    lit_dir = Path(literature_dir)
    lit_dir.mkdir(parents=True, exist_ok=True)

    query, providers = compile_protocol_search(p_path)
    if max_search_results:
        query.max_results = max_search_results

    engine = _search_engine_class()(providers=_resolve_providers(providers))
    discovered_docs = await engine.search_all(query, dedup=False)
    await engine.close()

    # Save both combined raw and first-provider raw for reference
    payload = json.dumps(
        [
            asdict(d) if hasattr(d, "__dataclass_fields__") else d
            for d in discovered_docs
        ],
        indent=2,
        default=str,
    )
    (lit_dir / "all_raw_search.json").write_text(payload, encoding="utf-8")
    (lit_dir / "raw_search.json").write_text(payload, encoding="utf-8")
    return DiscoveryOutcome(documents=discovered_docs, count=len(discovered_docs))
