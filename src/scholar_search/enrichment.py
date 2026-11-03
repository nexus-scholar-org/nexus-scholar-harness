"""Abstract backfilling for documents with missing abstracts."""

from __future__ import annotations

import logging
from typing import Any

from .exceptions import ProviderError
from .http_client import AcademicHttpClient
from .models import Document

logger = logging.getLogger(__name__)


class AbstractHydrator:
    """Batch-queries Semantic Scholar and OpenAlex for missing abstracts."""

    S2_BASE = "https://api.semanticscholar.org/graph/v1"
    OA_BASE = "https://api.openalex.org"

    def __init__(self, http_client: AcademicHttpClient):
        self.http_client = http_client

    async def hydrate_missing_abstracts(
        self, documents: list[Document], batch_size: int = 50
    ) -> tuple[list[Document], dict[str, int]]:
        """Hydrate documents with missing abstracts from S2 and OpenAlex.

        Args:
            documents: List of documents to hydrate.
            batch_size: Number of DOIs to query per batch.

        Returns:
            Tuple of (hydrated documents, stats dict).
        """
        stats = {"attempted": 0, "hydrated": 0, "failed": 0}

        # Filter docs needing abstracts
        needs_abstract = [
            doc for doc in documents if not doc.abstract and doc.external_ids.doi
        ]

        stats["attempted"] = len(needs_abstract)

        if not needs_abstract:
            return documents, stats

        # Process in batches
        hydrated_map: dict[str, str] = {}

        for i in range(0, len(needs_abstract), batch_size):
            batch = needs_abstract[i : i + batch_size]
            dois = [doc.external_ids.doi for doc in batch if doc.external_ids.doi]

            # OpenAlex pipe-batch FIRST: fast, key-authenticated, and the only
            # leg that hydrated reliably when the S2 key was rejected with 403
            # (observed live 2026-10-17: OA-first carried +345 abstracts while
            # every S2 batch 403'd). S2 batch now runs SECOND, only on DOIs
            # OpenAlex could not recover.
            oa_results = await self._hydrate_from_openalex(dois)
            hydrated_map.update(oa_results)
            missing_dois = [d for d in dois if d not in hydrated_map]
            if missing_dois:
                s2_results = await self._hydrate_from_s2(missing_dois)
                hydrated_map.update(s2_results)

        # Apply hydrated abstracts
        for doc in documents:
            if doc.external_ids.doi and doc.external_ids.doi in hydrated_map:
                doc.abstract = hydrated_map[doc.external_ids.doi]
                stats["hydrated"] += 1
            elif doc.external_ids.doi and not doc.abstract:
                stats["failed"] += 1

        return documents, stats

    async def _hydrate_from_s2(self, dois: list[str]) -> dict[str, str]:
        """Batch-query Semantic Scholar for abstracts."""
        if not dois:
            return {}

        try:
            from .config import settings

            url = f"{self.S2_BASE}/paper/batch"
            payload = {"ids": [f"DOI:{doi}" for doi in dois]}
            params = {"fields": "paperId,externalIds,abstract"}
            headers = {"x-api-key": settings.s2_key} if settings.s2_key else {}

            try:
                response = await self.http_client.post(
                    url, json=payload, params=params, headers=headers
                )
            except ProviderError as exc:
                if exc.status_code == 403 and headers:
                    # Key rejected at the API Gateway (bad/expired/placeholder
                    # token observed live 2026-10-17): one retry on the
                    # unauthenticated tier. If that also 403s (batch endpoint
                    # may require a valid key), return {} — OpenAlex-first
                    # ordering already did the heavy lifting.
                    logger.warning(
                        "S2 batch rejected the x-api-key (403 Forbidden); "
                        "retrying unauthenticated"
                    )
                    try:
                        response = await self.http_client.post(
                            url, json=payload, params=params
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"S2 batch request failed: {e}")
                        return {}
                else:
                    logger.warning(f"S2 batch request failed: {exc}")
                    return {}

            if response.status_code != 200:
                logger.warning(f"S2 batch request failed: {response.status_code}")
                return {}

            results = response.json()
            abstract_map = {}

            for item in results:
                if item and item.get("abstract"):
                    ext_ids = item.get("externalIds", {})
                    doi = ext_ids.get("DOI")
                    if doi:
                        abstract_map[doi.strip().lower()] = item["abstract"]

            return abstract_map
        except Exception as e:
            logger.warning(f"S2 hydration failed: {e}")
            return {}

    async def _hydrate_from_openalex(self, dois: list[str]) -> dict[str, str]:
        """Query OpenAlex for abstracts using inverted index."""
        if not dois:
            return {}

        from .config import settings

        abstract_map = {}
        # Pipe-batch up to 50 DOIs per single OpenAlex request
        for i in range(0, len(dois), 50):
            chunk = [d.strip().lower() for d in dois[i : i + 50]]
            doi_filter = "|".join(f"https://doi.org/{d}" for d in chunk)
            params: dict[str, Any] = {"filter": f"doi:{doi_filter}", "per-page": 200}
            if settings.openalex_key:
                params["api_key"] = settings.openalex_key
            try:
                resp = await self.http_client.get(
                    f"{self.OA_BASE}/works", params=params
                )
                if resp.status_code != 200:
                    continue
                for work in resp.json().get("results", []):
                    work_doi = (work.get("ids") or {}).get("doi", "")
                    work_doi = work_doi.lower().removeprefix("https://doi.org/").strip()
                    inv = work.get("abstract_inverted_index")
                    if work_doi and inv:
                        abstract = self._reconstruct_abstract(inv)
                        if abstract:
                            abstract_map[work_doi] = abstract
            except Exception as e:
                logger.debug(f"OpenAlex batch lookup failed: {e}")
        return abstract_map

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict[str, list[int]]) -> str:
        """Reconstruct abstract from OpenAlex inverted index."""
        if not inverted_index:
            return ""

        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))

        word_positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in word_positions)
