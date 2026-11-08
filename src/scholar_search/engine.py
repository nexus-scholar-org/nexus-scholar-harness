"""Search Engine Orchestrator for scholar-search-kit."""

import asyncio
import logging
from dataclasses import replace
from datetime import UTC, datetime

from .config import settings
from .dedup import Deduplicator, stable_order
from .exceptions import ScholarSearchError
from .models import Document, Query, SearchLeg, SearchRun
from .providers import (
    ArxivProvider,
    CrossrefProvider,
    OpenAlexProvider,
    PubMedProvider,
    SearchProvider,
    SemanticScholarProvider,
)
from .providers.base import BaseAPIProvider

logger = logging.getLogger(__name__)

# The most records one leg may fetch when the protocol sets no cap. It is a
# safety stop, not a method value: a leg that reaches it says so (cap_hit with
# cap_source "engine_ceiling"). Decision 2026-11-08, "The retrieval cap is a
# protocol method key".
ENGINE_CEILING = 10_000

# bioRxiv is not a default (SRCH-13): its API has no boolean search, so the
# provider drops AND/OR/NOT. It stays available when a protocol names it.
DEFAULT_PROVIDER_NAMES = ("openalex", "semanticscholar", "crossref", "arxiv", "pubmed")


class MailtoNotSet(ScholarSearchError):
    """A live search was started without a contact address (``MAILTO_NOT_SET``)."""

    code = "MAILTO_NOT_SET"

    def __init__(self) -> None:
        super().__init__(
            "MAILTO_NOT_SET: a live search needs a contact email for the providers' "
            "polite pools. Set SCHOLAR_MAILTO in the environment or in .env."
        )


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SearchEngine:
    """Orchestrates search across multiple academic providers."""

    def __init__(self, providers: list[SearchProvider] = None):
        """
        Initialize the search engine.
        If no providers are passed, loads a default production suite.
        """
        if providers is None:
            self.providers = [
                OpenAlexProvider(),
                SemanticScholarProvider(),
                CrossrefProvider(),
                ArxivProvider(),
                PubMedProvider(),
            ]
        else:
            self.providers = providers

        self.deduplicator = Deduplicator()
        self.last_legs: list[SearchLeg] = []

    def _check_mailto(self) -> None:
        live = any(isinstance(p, BaseAPIProvider) for p in self.providers)
        if live and not settings.mailto:
            raise MailtoNotSet()

    async def run(self, query: Query, dedup: bool = True, progress_callback=None) -> SearchRun:
        """Run the query on every provider and return the documents with one leg each.

        Each provider is paged to its reported total, to the query's cap
        (``max_results``) or to ``ENGINE_CEILING``, whichever comes first. A leg
        that stopped at a cap while the database reported more says
        ``cap_hit``. A failing provider gives a ``failed`` leg; it never
        silently disappears.
        """
        self._check_mailto()
        if query.max_results:
            cap = min(int(query.max_results), ENGINE_CEILING)
            cap_source = query.cap_source if cap == query.max_results else "engine_ceiling"
        else:
            cap, cap_source = ENGINE_CEILING, "engine_ceiling"
        leg_query = replace(query, max_results=cap)

        legs: list[SearchLeg] = []
        per_provider: list[list[Document]] = []

        async def fetch_provider(provider: SearchProvider, leg: SearchLeg, sink: list[Document]):
            logger.info(f"Querying {provider.name}...")
            try:
                provider.current_leg = leg
            except AttributeError:  # pragma: no cover - exotic providers
                pass
            leg.started_at = _now()
            leg.status = "running"
            stream = provider.search(leg_query)
            try:
                async for doc in stream:
                    sink.append(doc)
                    leg.fetched += 1
                    if progress_callback:
                        progress_callback(provider.name, leg.fetched)
                    if leg.fetched >= cap:
                        break
                leg.status = "ok"
                logger.info(f"  -> Found {leg.fetched} documents from {provider.name}.")
            except Exception as e:
                leg.status = "failed"
                leg.error = f"{type(e).__name__}: {e}"
                logger.error(f"Error querying {provider.name}: {e}")
            finally:
                aclose = getattr(stream, "aclose", None)
                if aclose is not None:
                    try:
                        await aclose()
                    except Exception:  # pragma: no cover - defensive
                        pass
                leg.finished_at = _now()
                if leg.fetched >= cap and (leg.reported_total is None or leg.reported_total > leg.fetched):
                    leg.cap_hit = True
                try:
                    provider.current_leg = None
                except AttributeError:  # pragma: no cover
                    pass

        tasks = []
        for provider in self.providers:
            leg = SearchLeg(
                provider=str(provider.name),
                query_id=query.id,
                cap=cap,
                cap_source=cap_source,
                mailto_set=bool(settings.mailto),
            )
            sink: list[Document] = []
            legs.append(leg)
            per_provider.append(sink)
            tasks.append(fetch_provider(provider, leg, sink))
        await asyncio.gather(*tasks)

        # Provider order, not arrival order, so the raw list is reproducible.
        all_results = [doc for sink in per_provider for doc in sink]
        self.last_legs = legs

        if not dedup or not all_results:
            return SearchRun(documents=all_results, legs=legs)

        logger.info(f"Deduplicating {len(all_results)} raw results...")
        clusters = self.deduplicator.deduplicate(stable_order(all_results))
        unique_results = [cluster.representative for cluster in clusters]
        logger.info(f"  -> Reduced to {len(unique_results)} unique documents.")
        return SearchRun(documents=unique_results, legs=legs)

    async def search_all(self, query: Query, dedup: bool = True, progress_callback=None) -> list[Document]:
        """Run the query and return only the documents; the legs are in ``last_legs``."""
        run = await self.run(query, dedup=dedup, progress_callback=progress_callback)
        return run.documents

    async def snowball_forward(self, document_id: str, provider_name: str, progress_callback=None) -> list[Document]:
        """Finds papers that cite the given document ID."""
        for provider in self.providers:
            if provider.name.lower() == provider_name.lower():
                logger.info(f"Forward snowballing on {provider.name} for {document_id}")
                results = []
                count = 0
                async for doc in provider.get_citations(document_id):
                    results.append(doc)
                    count += 1
                    if progress_callback:
                        progress_callback(provider.name, count)
                return results
        raise ValueError(f"Provider {provider_name} not found or not registered.")

    async def snowball_backward(self, document_id: str, provider_name: str, progress_callback=None) -> list[Document]:
        """Finds papers that the given document cites."""
        for provider in self.providers:
            if provider.name.lower() == provider_name.lower():
                logger.info(
                    f"Backward snowballing on {provider.name} for {document_id}"
                )
                results = []
                count = 0
                async for doc in provider.get_references(document_id):
                    results.append(doc)
                    count += 1
                    if progress_callback:
                        progress_callback(provider.name, count)
                return results
        raise ValueError(f"Provider {provider_name} not found or not registered.")

    async def close(self):
        """Close HTTP clients for all providers."""
        for provider in self.providers:
            if hasattr(provider, "client") and hasattr(provider.client, "close"):
                await getattr(provider.client, "close")()
