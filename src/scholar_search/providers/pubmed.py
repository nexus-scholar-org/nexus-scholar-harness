"""PubMed provider implementation."""

import re
import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator

from ..config import settings
from ..models import Author, Document, ExternalIds, Query
from ..query_translator import BooleanQueryTranslator, QueryField
from .base import BaseAPIProvider


class PubMedProvider(BaseAPIProvider):
    """Searches PubMed via NCBI E-utilities."""

    ESEARCH_PAGE = 10_000  # ESearch maximum retmax

    def __init__(self) -> None:
        super().__init__(name="pubmed", rate_limit=settings.rate_limit_pubmed)
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

        # PubMed naturally supports AND, OR, NOT and fields via [Tag]
        self.translator = BooleanQueryTranslator(
            field_map={
                QueryField.ANY: "",
                QueryField.TITLE: "ti",
                QueryField.ABSTRACT: "tiab",
                QueryField.AUTHOR: "au",
            },
            operator_map={"AND": "AND", "OR": "OR", "NOT": "NOT"},
        )

    # PubMed field tags for the parser's fields (suffix syntax: term[tag]).
    # PubMed has no abstract-only tag: ``[ab]`` answers FieldNotFound and the
    # term is silently searched in all fields (F11, live 2026-11-10), so an
    # abstract-scoped term is sent as title-or-abstract and the leg says so.
    _TAGS = {QueryField.TITLE: "ti", QueryField.ABSTRACT: "tiab", QueryField.AUTHOR: "au"}

    ABSTRACT_NOTE = (
        "PubMed has no abstract-only field: abstract-scoped terms are sent as "
        "title-or-abstract ([tiab])"
    )

    def build_term(self, text: str) -> str:
        """Translate the query from parsed tokens into PubMed syntax (SRCH-14).

        Field-tagged terms become ``term[ti]`` and field-tagged phrases
        ``"a phrase"[ti]``. Untagged words, phrases, operators and parentheses
        pass through unchanged, so a colon inside a phrase is never read as a
        field. A query the parser cannot read is sent exactly as written.
        """
        parser = self.translator.parser
        tokens = parser.parse(text)
        if not parser.validate(tokens):
            return text
        parts: list[str] = []
        for token in tokens:
            if token.is_operator:
                parts.append(token.value)
                continue
            value = f'"{token.value}"' if token.is_phrase else token.value
            tag = self._TAGS.get(token.field)
            parts.append(f"{value}[{tag}]" if tag else value)
        return " ".join(parts).replace("( ", "(").replace(" )", ")")

    async def _fetch_details(
        self, pmids: list[str], query_id: str | None = None
    ) -> AsyncIterator[Document]:
        """Fetches full XML details for a list of PMIDs and yields Document models."""
        if not pmids:
            return

        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
        if settings.mailto:
            params["email"] = settings.mailto
            params["tool"] = "nexus-scholar"

        resp = await self.client.get(f"{self.base_url}/efetch.fcgi", params=params)
        root = ET.fromstring(resp.content)

        for article_elem in root.findall(".//PubmedArticle"):
            medline = article_elem.find("MedlineCitation")
            article = medline.find("Article") if medline is not None else None

            if medline is None or article is None:
                continue

            # Parse IDs — ONLY from the article's own
            # <PubmedData><ArticleIdList>, never <ReferenceList>: descendant
            # `.//ArticleId` surfaced reference-list DOIs and the last-write
            # loop overwrote the article's true DOI (observed live 2026-10-17:
            # Plant Methods article got doi=10.7717/peerj.453 from its
            # bibliography's last reference).
            pmid = medline.findtext("PMID")
            doi = None
            pmcid = None
            for id_elem in article_elem.findall("./PubmedData/ArticleIdList/ArticleId"):
                id_type = id_elem.get("IdType")
                if id_type == "doi" and id_elem.text:
                    doi = id_elem.text.strip()
                elif id_type == "pmc" and id_elem.text:
                    pmcid = id_elem.text.strip()
            # Fallback to Article/ELocationID when PubmedData/ArticleIdList
            # carries no own-DOI (e.g., ahead-of-print records).
            if doi is None:
                for eloc in article.findall("./ELocationID"):
                    if eloc.get("EIdType") == "doi" and eloc.text:
                        doi = eloc.text.strip()
                        break

            # Parse Year
            year = None
            pub_date = article.find(".//PubDate")
            if pub_date is not None:
                year_elem = pub_date.find("Year")
                if year_elem is not None and year_elem.text:
                    try:
                        year = int(year_elem.text)
                    except ValueError:
                        pass

            # Parse Authors
            authors = []
            for author_elem in article.findall(".//Author"):
                last = author_elem.findtext("LastName")
                first = author_elem.findtext("ForeName") or author_elem.findtext(
                    "Initials"
                )
                if last:
                    authors.append(Author(family_name=last, given_name=first))

            # Parse MeSH Terms
            mesh_terms = []
            for mesh_elem in medline.findall(".//MeshHeading/DescriptorName"):
                if mesh_elem.text:
                    mesh_terms.append(mesh_elem.text)

            # Title & Abstract
            title = article.findtext("ArticleTitle", default="Untitled")

            abstract = None
            abstract_elem = article.find("Abstract")
            if abstract_elem is not None:
                abstract_texts = []
                for text_elem in abstract_elem.findall("AbstractText"):
                    if text_elem.text:
                        abstract_texts.append(text_elem.text)
                abstract = " ".join(abstract_texts) if abstract_texts else None

            doc = Document(
                title=title,
                year=year,
                provider=self.name,
                provider_id=pmid or "",
                external_ids=ExternalIds(doi=doi, pubmed_id=pmid),
                abstract=abstract,
                authors=authors,
                venue=article.findtext(".//Journal/Title"),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                mesh_terms=mesh_terms,
                query_id=query_id,
            )
            doc.mark_retrieved()
            yield doc

    def translate(self, query: Query) -> tuple[str, dict, list[str]]:
        pubmed_query = self.build_term(query.text)

        limit = query.max_results
        params = {
            "db": "pubmed",
            "term": pubmed_query,
            "retmode": "json",
            "retmax": min(limit or self.ESEARCH_PAGE, self.ESEARCH_PAGE),
            "retstart": 0,
        }
        if settings.mailto:
            params["email"] = settings.mailto
            params["tool"] = "nexus-scholar"

        # Add year filter to PubMed query syntax if provided
        if query.year_min and query.year_max:
            params["term"] += f" AND {query.year_min}:{query.year_max}[pdat]"
        elif query.year_min:
            params["term"] += f" AND {query.year_min}:3000[pdat]"
        elif query.year_max:
            params["term"] += f" AND 1000:{query.year_max}[pdat]"
        notes = [self.ABSTRACT_NOTE] if self._has_abstract_terms(query.text) else []
        return params["term"], params, notes

    def _has_abstract_terms(self, text: str) -> bool:
        parser = self.translator.parser
        tokens = parser.parse(text)
        if not parser.validate(tokens):
            return False
        return any(t.field == QueryField.ABSTRACT for t in tokens if not t.is_operator)

    # How ESearch's ``querytranslation`` names each tag this provider sends.
    _TAG_LABELS = {
        "ti": "[Title]",
        "tiab": "[Title/Abstract]",
        "au": "[Author]",
        "pdat": "[Date - Publication]",
    }

    def _record_esearch_errors(self, result: dict, term: str) -> None:
        """Put a field tag PubMed did not apply on the leg (F11), never drop it.

        ESearch answers an unknown tag by searching the term in all fields. The
        XML answer says ``<ErrorList><FieldNotFound>``, but the JSON
        ``errorlist.fieldsnotfound`` stays empty (recorded 2026-11-10,
        ``tests/kits/search/fixtures/pubmed/``), so a tag sent that is not one
        of the tags PubMed is known to apply (``_TAG_LABELS``, each seen in a
        recorded ``querytranslation``) is reported when PubMed translated the
        term. Known tags are never inferred missing by counting labels: PubMed
        also drops not-found and ignored terms from the translation, which
        would read as an unapplied tag (review finding, M3h-providers).
        """
        errors = result.get("errorlist") or {}
        if not isinstance(errors, dict):
            errors = {}
        warnings = result.get("warninglist") or {}
        if not isinstance(warnings, dict):
            warnings = {}
        missing: list[str] = [str(f) for f in errors.get("fieldsnotfound") or [] if f]
        translation = result.get("querytranslation")
        if isinstance(translation, str) and translation:
            for tag in re.findall(r"\[([A-Za-z]+)\]", term):
                tag = tag.lower()
                if tag not in self._TAG_LABELS and tag not in missing:
                    missing.append(tag)
        if missing:
            seen = f" PubMed's translation: {translation}" if isinstance(translation, str) and translation else ""
            self._record_note(
                "PubMed did not apply the field tag(s) "
                + ", ".join(f"[{f}]" for f in missing)
                + " it was sent; an unknown tag is searched in all fields."
                + seen
            )
        phrases = [p for p in errors.get("phrasesnotfound") or [] if p]
        phrases += [p for p in warnings.get("quotedphrasesnotfound") or [] if p and p not in phrases]
        if phrases:
            self._record_note(
                "PubMed found no records for the phrase(s) "
                + ", ".join(f'"{p}"' for p in phrases)
                + "; it left them out of the search"
            )
        ignored = [p for p in warnings.get("phrasesignored") or [] if p]
        if ignored:
            self._record_note(
                "PubMed ignored the term(s) "
                + ", ".join(f'"{p}"' for p in ignored)
                + " (stop words); they were not searched"
            )

    async def search(self, query: Query) -> AsyncIterator[Document]:
        """Search PubMed using esearch and efetch."""
        _, params, _ = self._record_translation(query)
        limit = query.max_results

        # Page ESearch with retstart (SRCH-11), then fetch details in chunks.
        chunk_size = 200
        count = 0
        while True:
            resp = await self.client.get(f"{self.base_url}/esearch.fcgi", params=params)
            self._record_page()
            result = resp.json().get("esearchresult", {}) or {}
            if params["retstart"] == 0:
                self._record_esearch_errors(result, params["term"])
            self._record_total(result.get("count"))
            pmids = result.get("idlist", []) or []
            if not pmids:
                return
            for i in range(0, len(pmids), chunk_size):
                chunk = pmids[i : i + chunk_size]
                async for doc in self._fetch_details(chunk, query.id):
                    yield doc
                    count += 1
                    if limit and count >= limit:
                        return
            next_start = int(params["retstart"]) + len(pmids)
            try:
                total = int(result.get("count"))
            except (TypeError, ValueError):
                total = None
            if total is not None and next_start >= total:
                return
            if total is None and len(pmids) < int(params["retmax"]):
                return  # a short page is the last one when no total is reported
            # ESearch without the history server stops at 10,000 records.
            if next_start >= 10_000:
                self._record_note("PubMed ESearch returns at most 10,000 records per query")
                return
            params["retstart"] = next_start
            if limit:
                params["retmax"] = min(limit - count, self.ESEARCH_PAGE)

    async def get_citations(self, document_id: str) -> AsyncIterator[Document]:
        """Forward Snowballing: Get PMIDs that cite this PMID using elink."""
        params = {
            "dbfrom": "pubmed",
            "linkname": "pubmed_pubmed_citedin",
            "id": document_id,
            "retmode": "json",
        }
        resp = await self.client.get(f"{self.base_url}/elink.fcgi", params=params)
        response = resp.json()

        linkset = response.get("linksets", [])
        if not linkset:
            return

        links = linkset[0].get("linksetdbs", [])
        if not links:
            return

        citing_pmids = links[0].get("links", [])
        async for doc in self._fetch_details(citing_pmids):
            yield doc
