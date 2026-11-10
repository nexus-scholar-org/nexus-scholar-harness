"""Crossref provider implementation."""

from collections.abc import AsyncIterator
from typing import Any

from ..config import settings
from ..models import Author, Document, ExternalIds, Query
from ..query_translator import BooleanQueryTranslator, QueryField
from .base import BaseAPIProvider


class CrossrefProvider(BaseAPIProvider):
    """Searches Crossref REST API (https://api.crossref.org/works)."""

    PAGE_SIZE = 1000  # Crossref's maximum rows per request

    def __init__(self) -> None:
        super().__init__(name="crossref", rate_limit=settings.rate_limit_crossref)
        self.base_url = "https://api.crossref.org/works"

        # Crossref query syntax supports + for AND, - for NOT
        self.translator = BooleanQueryTranslator(
            field_map={QueryField.ANY: ""},
            operator_map={"AND": "+", "OR": "", "NOT": "-"},
        )

    def _normalize_document(
        self, raw: dict[str, Any], query_id: str | None = None
    ) -> Document:
        """Converts Crossref JSON into a Document model."""

        # Parse authors
        authors = []
        for author_data in raw.get("author", []):
            authors.append(
                Author(
                    given_name=author_data.get("given"),
                    family_name=author_data.get("family", "Unknown"),
                    orcid=author_data.get("ORCID"),
                )
            )

        # Parse year (Crossref returns a complex date-parts array)
        year = None
        published = (
            raw.get("published-print")
            or raw.get("published-online")
            or raw.get("issued")
        )
        if published and "date-parts" in published and published["date-parts"]:
            try:
                year = int(published["date-parts"][0][0])
            except (ValueError, IndexError, TypeError):
                pass

        # Parse External IDs
        external_ids = ExternalIds(doi=raw.get("DOI"))

        title = "Untitled"
        if raw.get("title") and len(raw["title"]) > 0:
            title = raw["title"][0]

        venue = None
        if raw.get("container-title") and len(raw["container-title"]) > 0:
            venue = raw["container-title"][0]

        doc = Document(
            title=title,
            year=year,
            provider=self.name,
            provider_id=raw.get("DOI", ""),
            external_ids=external_ids,
            abstract=raw.get("abstract"),  # Crossref rarely provides full abstracts
            authors=authors,
            venue=venue,
            url=raw.get("URL"),
            citations_count=raw.get("is-referenced-by-count", 0),
            references_count=raw.get("reference-count", 0),
            query_id=query_id,
        )
        doc.mark_retrieved()
        return doc

    def translate(self, query: Query) -> tuple[str, dict, list[str]]:
        translated_query = self.translator.translate(query)

        limit = query.max_results
        params = {
            "query": translated_query,
            "rows": min(limit or self.PAGE_SIZE, self.PAGE_SIZE),
            # Deep paging (SRCH-11): Crossref's cursor walks the full result set.
            "cursor": "*",
        }

        # Crossref uses filter syntax for years
        filters = []
        if query.year_min:
            filters.append(f"from-pub-date:{query.year_min}-01-01")
        if query.year_max:
            filters.append(f"until-pub-date:{query.year_max}-12-31")

        # We only want journal articles, proceedings, preprints usually (to avoid filtering out too much)
        # But we'll leave it open for now unless specified

        if filters:
            params["filter"] = ",".join(filters)
        return translated_query, params, []

    async def search(self, query: Query) -> AsyncIterator[Document]:
        """Search Crossref works."""
        _, params, _ = self._record_translation(query)
        limit = query.max_results

        count = 0
        while True:
            resp = await self.client.get(self.base_url, params=params)
            self._record_page()
            message = resp.json().get("message", {}) or {}
            self._record_total(message.get("total-results"))
            items = message.get("items", []) or []
            for item in items:
                yield self._normalize_document(item, query.id)
                count += 1
                if limit and count >= limit:
                    return
            total = message.get("total-results")
            next_cursor = message.get("next-cursor")
            if not items or not next_cursor:
                return
            if total is not None and count >= int(total):
                return
            params["cursor"] = next_cursor
            if limit:
                params["rows"] = min(limit - count, self.PAGE_SIZE)

    # --- Snowballing features are not supported well by Crossref (use OpenAlex or S2) ---

    # --- Reference validation ---

    async def validate_reference(self, messy_citation: str) -> Document | None:
        """
        Validates a messy citation string (e.g. from a PDF or a dirty .bib file)
        and returns the canonical Crossref Document with a verified DOI.

        No caller in the harness uses it yet (scholar-bib-kit was removed in M5-slim).
        """
        # Crossref has a specific query.bibliographic field for this
        params = {
            "query.bibliographic": messy_citation,
            "rows": 1,  # We just want the single best match
        }
        try:
            resp = await self.client.get(self.base_url, params=params)
            response = resp.json()
            items = response.get("message", {}).get("items", [])

            if items:
                # We could check the crossref relevance score here to ensure it's a good match
                match = items[0]
                if match.get("score", 0) > 40:  # Arbitrary confidence threshold
                    return self._normalize_document(match)
        except Exception:
            pass
        return None
