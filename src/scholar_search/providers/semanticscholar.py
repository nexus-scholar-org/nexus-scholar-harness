"""Semantic Scholar provider implementation."""

import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from ..config import settings
from ..exceptions import ProviderError
from ..models import Author, Document, ExternalIds, Query
from ..query_translator import BooleanQueryTranslator, QueryField
from .base import BaseAPIProvider

logger = logging.getLogger(__name__)


class SemanticScholarProvider(BaseAPIProvider):
    """Searches Semantic Scholar API."""

    def __init__(self) -> None:
        super().__init__(name="semanticscholar", rate_limit=settings.rate_limit_s2)
        # Switch to the highly efficient bulk endpoint
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

        # S2 bulk uses + for AND, | for OR, - for NOT
        self.translator = BooleanQueryTranslator(
            field_map={QueryField.ANY: ""},
            operator_map={"AND": "+", "OR": "|", "NOT": "-"},
        )
        self.fields = "paperId,externalIds,title,abstract,year,authors,venue,url,referenceCount,citationCount"

    def _get_headers(self) -> dict[str, str]:
        headers = {}
        if settings.s2_key:
            headers["x-api-key"] = settings.s2_key
        return headers

    def _normalize_document(
        self,
        raw: dict[str, Any],
        query_id: str | None = None,
        citation_intent: list[str] | None = None,
    ) -> Document:
        """Converts S2 JSON into a Document model."""

        # Parse authors
        authors = []
        for author_data in raw.get("authors", []):
            name_parts = author_data.get("name", "").split(" ")
            if len(name_parts) > 1:
                authors.append(
                    Author(
                        given_name=" ".join(name_parts[:-1]), family_name=name_parts[-1]
                    )
                )
            elif name_parts and name_parts[0]:
                authors.append(Author(family_name=name_parts[0]))

        # Parse External IDs
        ext_ids_raw = raw.get("externalIds", {})
        external_ids = ExternalIds(
            doi=ext_ids_raw.get("DOI"),
            pubmed_id=ext_ids_raw.get("PubMed"),
            s2_id=raw.get("paperId"),
        )

        doc = Document(
            title=raw.get("title") or "Untitled",
            year=raw.get("year"),
            provider=self.name,
            provider_id=raw.get("paperId", ""),
            external_ids=external_ids,
            abstract=raw.get("abstract"),
            authors=authors,
            venue=raw.get("venue"),
            url=raw.get("url"),
            citations_count=raw.get("citationCount"),
            references_count=raw.get("referenceCount"),
            tldr=raw.get("tldr", {}).get("text") if raw.get("tldr") else None,
            citation_intents=citation_intent or [],
            query_id=query_id,
        )
        doc.mark_retrieved()
        return doc

    async def search(self, query: Query) -> AsyncIterator[Document]:
        """Search Semantic Scholar using the bulk endpoint."""
        # Translate query to bulk syntax (e.g. "term1 + term2 | term3")
        translated_query = self.translator.translate(query)
        # S2 bulk search supports +, |, -, "phrase", and ( ) grouping! Only strip &
        translated_query = translated_query.replace("&", " ")
        translated_query = re.sub(r"\s+", " ", translated_query).strip()

        params = {
            "query": translated_query,
            "fields": "paperId,title,abstract,year,authors,venue,externalIds,url,citationCount,referenceCount",
        }

        if query.year_min and query.year_max:
            params["year"] = f"{query.year_min}-{query.year_max}"
        elif query.year_min:
            params["year"] = f"{query.year_min}-"
        elif query.year_max:
            params["year"] = f"-{query.year_max}"

        token = None
        count = 0
        # 403 auto-downgrade: AWS API Gateway answers 403 Forbidden when a
        # bad/expired/placeholder key reaches the S2 endpoint. A rejected key
        # must never zero out the provider leg (observed live 2026-10-17) —
        # strip the header once and continue on the unauthenticated tier.
        use_key = True

        while True:
            if token:
                params["token"] = token

            try:
                resp = await self.client.get(
                    self.base_url,
                    params=params,
                    headers=self._get_headers() if use_key else {},
                )
            except ProviderError as exc:
                if exc.status_code == 403 and use_key and settings.s2_key:
                    logger.warning(
                        "S2 rejected the x-api-key (403 Forbidden); "
                        "downgrading to the unauthenticated public tier"
                    )
                    use_key = False
                    resp = await self.client.get(self.base_url, params=params)
                else:
                    raise
            response_data = resp.json()
            data = response_data.get("data", [])
            token = response_data.get("token")

            if not data:
                break

            for item in data:
                yield self._normalize_document(item, query.id)
                count += 1
                if query.max_results and count >= query.max_results:
                    return

            if not token:
                break

    async def get_citations(self, document_id: str) -> AsyncIterator[Document]:
        """Forward Snowballing: Get papers that cite this specific S2 ID."""
        # Using the /citations endpoint
        params = {"fields": self.fields + ",contexts,intents", "limit": 1000}
        resp = await self.client.get(
            f"{self.base_url.replace('/search/bulk', '')}/{document_id}/citations",
            params=params,
            headers=self._get_headers(),
        )
        response = resp.json()

        for item in response.get("data", []):
            citing_paper = item.get("citingPaper")
            intents = item.get("intents") or []
            if citing_paper:
                yield self._normalize_document(citing_paper, citation_intent=intents)

    async def get_references(self, document_id: str) -> AsyncIterator[Document]:
        """Backward Snowballing: Get papers that this specific S2 ID cites."""
        params = {"fields": self.fields + ",contexts,intents", "limit": 1000}
        resp = await self.client.get(
            f"{self.base_url.replace('/search/bulk', '')}/{document_id}/references",
            params=params,
            headers=self._get_headers(),
        )
        response = resp.json()

        for item in response.get("data", []):
            cited_paper = item.get("citedPaper")
            intents = item.get("intents") or []
            if cited_paper:
                yield self._normalize_document(cited_paper, citation_intent=intents)
