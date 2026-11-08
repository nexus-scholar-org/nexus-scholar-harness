"""arXiv provider implementation."""

import re
import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator

from ..models import Author, Document, ExternalIds, Query
from ..query_translator import BooleanQueryTranslator, QueryField
from .base import BaseAPIProvider


class ArxivProvider(BaseAPIProvider):
    """Searches arXiv API (http://export.arxiv.org/api/query)."""

    PAGE_SIZE = 1000  # arXiv recommends at most 2000 per call; 1000 keeps responses small

    def __init__(
        self,
        *,
        compact_stoplist: tuple[str, ...] | list[str] | None = None,
        compact_stem_families: dict[str, tuple[str, ...] | list[str]] | None = None,
    ) -> None:
        # arXiv allows 1 req/sec without API key
        super().__init__(name="arxiv", rate_limit=1.0)
        self.base_url = "https://export.arxiv.org/api/query"
        self.ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        }

        # arXiv supports AND, OR, ANDNOT. Prefixes: all, ti, au, abs
        self.translator = BooleanQueryTranslator(
            field_map={
                QueryField.ANY: "all",
                QueryField.TITLE: "ti",
                QueryField.ABSTRACT: "abs",
                QueryField.AUTHOR: "au",
            },
            operator_map={"AND": "AND", "OR": "OR", "NOT": "ANDNOT"},
        )

        # Domain-neutral compaction knobs. arXiv's Lucene layer does NO
        # stemming and cannot budget long multi-cluster booleans, so research
        # layers (protocol/query-translator code, never kit internals) may:
        #  - pass token "stoplist" entries to exclude bare single-token heads
        #    that are too generic as standalone `all:` terms for the domain;
        #  - declare "stem families" {prefix: (expansions, ...)}: whenever any
        #    kept token starts with the prefix, the un-stemmed morphology
        #    variants are enumerated into the clause so recall is not lost.
        # Defaults are EMPTY: with no research config the compact query is the
        # pure single-token translation with no domain knowledge inside the
        # kit (genericity rule enforced live 2026-10-17 at the harness layer).
        self.compact_stoplist: frozenset[str] = frozenset(
            s.lower() for s in (compact_stoplist or ())
        )
        self.compact_stem_families: tuple[tuple[str, tuple[str, ...]], ...] = tuple(
            (p.lower(), tuple(e.lower() for e in extras))
            for p, extras in (compact_stem_families or {}).items()
        )

    def _parse_xml_entry(
        self, entry: ET.Element, query_id: str | None = None
    ) -> Document:
        """Converts an arXiv Atom XML entry into a Document model."""

        # Parse Title
        title_elem = entry.find("atom:title", self.ns)
        title = (
            title_elem.text.strip().replace("\n", " ")
            if title_elem is not None
            else "Untitled"
        )

        # Parse Abstract
        summary_elem = entry.find("atom:summary", self.ns)
        abstract = (
            summary_elem.text.strip().replace("\n", " ")
            if summary_elem is not None
            else None
        )

        # Parse Year (from published date)
        year = None
        published_elem = entry.find("atom:published", self.ns)
        if published_elem is not None and published_elem.text:
            year = int(published_elem.text[:4])

        # Parse Authors
        authors = []
        for author_elem in entry.findall("atom:author", self.ns):
            name_elem = author_elem.find("atom:name", self.ns)
            if name_elem is not None and name_elem.text:
                name_parts = name_elem.text.strip().split(" ")
                if len(name_parts) > 1:
                    authors.append(
                        Author(
                            given_name=" ".join(name_parts[:-1]),
                            family_name=name_parts[-1],
                        )
                    )
                else:
                    authors.append(Author(family_name=name_parts[0]))

        # Extract Arxiv ID from the ID URL (e.g. http://arxiv.org/abs/2101.01234v1 -> 2101.01234)
        id_elem = entry.find("atom:id", self.ns)
        arxiv_id = None
        if id_elem is not None and id_elem.text:
            arxiv_id = id_elem.text.split("/")[-1].split("v")[
                0
            ]  # Remove version number

        # Extract DOI if available (often added after peer review publication)
        doi = None
        for link_elem in entry.findall("atom:link", self.ns):
            title_attr = link_elem.get("title")
            if title_attr == "doi":
                doi_url = link_elem.get("href", "")
                if "doi.org/" in doi_url:
                    doi = doi_url.split("doi.org/")[-1]

        # PDF URL
        pdf_url = None
        for link_elem in entry.findall("atom:link", self.ns):
            if link_elem.get("title") == "pdf":
                pdf_url = link_elem.get("href")

        external_ids = ExternalIds(doi=doi, arxiv_id=arxiv_id)

        doc = Document(
            title=title,
            year=year,
            provider=self.name,
            provider_id=arxiv_id or "",
            external_ids=external_ids,
            abstract=abstract,
            authors=authors,
            venue="arXiv Preprint",
            url=pdf_url or (id_elem.text if id_elem is not None else None),
            query_id=query_id,
        )
        doc.mark_retrieved()
        return doc

    async def search(self, query: Query) -> AsyncIterator[Document]:
        """Search arXiv."""
        translated_query = self.translator.translate(query)
        # arXiv's negation is the single operator ANDNOT; "a AND NOT b"
        # translates to "a AND ANDNOT b", which arXiv cannot parse. Only that
        # form is collapsed: "a OR NOT b" has no ANDNOT equivalent and is sent
        # as written rather than changed in meaning.
        translated_query = re.sub(r"\bAND\s+ANDNOT\b", "ANDNOT", translated_query)

        # If translator didn't apply any field, fallback to all:
        if ":" not in translated_query:
            translated_query = f'all:"{translated_query}"'

        # arXiv's Atom/Lucene parser degrades recall on long multi-clause
        # boolean strings, and Lucene does NO stemming — morphology variants
        # are unreachable unless enumerated. Compact long multi-cluster
        # queries to the core single-token terms per cluster: single-token
        # phrases are kept, multi-word phrases are dropped (they exceed
        # arXiv's practical clause budget). Observed live 2026-10-17: an
        # earlier compaction revision stripped quote+content together and
        # was an inert no-op (arXiv ran the full multi-phrase query). Domain
        # stoplists/stem families arrive ONLY via constructor config from the
        # research layer; the kit default carries neither.
        has_not = bool(re.search(r"\bNOT\b", query.text))
        if len(translated_query) > 300 and " AND " in query.text and has_not:
            # Compaction reads clauses as bags of tokens, so a NOT term would
            # become a required one (SRCH-12). Send the full query instead.
            self._record_note(
                "arXiv query not compacted: it contains NOT, which compaction cannot keep; "
                "the full translation was sent"
            )
        elif len(translated_query) > 300 and " AND " in query.text:
            import re as _re

            original_translation = translated_query
            dropped_phrases: list[str] = []
            compact_clauses = []
            for clause in query.text.split(" AND "):
                phrases = _re.findall(r'"([^"]*)"', clause)
                bare = _re.sub(r'"[^"]*"', " ", clause)
                tokens = []
                for p in phrases:
                    p_toks = _re.findall(r"[a-zA-Z0-9_-]{2,}", p)
                    if len(p_toks) == 1:
                        tokens.append(p_toks[0])
                    elif p not in dropped_phrases:
                        dropped_phrases.append(p)
                tokens.extend(_re.findall(r"[a-zA-Z0-9_-]{3,}", bare))
                seen = set()
                deduped = []
                for t in tokens:
                    tl = t.lower()
                    if tl in seen:
                        continue
                    seen.add(tl)
                    if t.upper() in ("AND", "OR", "NOT"):
                        continue
                    if tl in self.compact_stoplist:
                        continue
                    deduped.append(t)
                # Generic stem-family expansion from research config: when a
                # kept token falls under a declared stem prefix, enumerate the
                # morphology variants now, because the Lucene layer will not.
                for prefix, extras in self.compact_stem_families:
                    if any(t.lower().startswith(prefix) for t in deduped):
                        for extra in extras:
                            if extra not in deduped:
                                deduped.append(extra)
                if deduped:
                    compact_clauses.append(
                        "(" + " OR ".join(f"all:{t}" for t in deduped[:6]) + ")"
                    )
            if compact_clauses:
                translated_query = " AND ".join(compact_clauses)
                # Never silent (SRCH-12): the leg says the query was rewritten
                # and what the rewrite dropped.
                note = (
                    f"arXiv query compacted from {len(original_translation)} characters to "
                    f"{len(translated_query)}: multi-word phrases dropped, at most 6 single "
                    "tokens kept per clause"
                )
                if dropped_phrases:
                    note += "; dropped phrases: " + ", ".join(f'"{p}"' for p in dropped_phrases)
                self._record_note(note)

        limit = query.max_results
        params = {
            "search_query": translated_query,
            "start": 0,
            "max_results": min(limit or self.PAGE_SIZE, self.PAGE_SIZE),
        }
        self._record_executed(translated_query, params)
        if query.year_min or query.year_max:
            self._record_note(
                "arXiv has no year filter in its API; years were filtered after retrieval, "
                "so fetched can be below the reported total"
            )

        # arXiv doesn't support direct year filtering in the query string well,
        # so we fetch and filter locally. Page with ``start`` (SRCH-11).
        count = 0
        while True:
            response = await self.client.get(self.base_url, params=params)
            self._record_page()

            # Parse XML
            if not response.text.strip():
                return

            root = ET.fromstring(response.content)
            total_elem = root.find("opensearch:totalResults", self.ns)
            total = None
            if total_elem is not None and total_elem.text:
                try:
                    total = int(total_elem.text.strip())
                except ValueError:
                    total = None
            self._record_total(total)

            entries = root.findall("atom:entry", self.ns)
            for entry in entries:
                doc = self._parse_xml_entry(entry, query.id)

                if query.year_min and (doc.year or 0) < query.year_min:
                    continue
                if query.year_max and (doc.year or 9999) > query.year_max:
                    continue

                yield doc
                count += 1
                if limit and count >= limit:
                    return

            next_start = int(params["start"]) + len(entries)
            if not entries or total is None or next_start >= total:
                return
            params["start"] = next_start

    # arXiv has no native snowballing API
