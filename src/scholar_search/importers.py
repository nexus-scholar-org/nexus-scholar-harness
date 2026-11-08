"""Importers for reading local files into the normalized Document model."""

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .models import Author, Document, ExternalIds


#: A RIS tag line: two characters (letter, then letter or digit), two spaces,
#: a hyphen, then the value. ``ER  -`` often has no trailing space.
_RIS_TAG = re.compile(r"^([A-Z][A-Z0-9])  -(?: (.*))?$")
#: Primary authors. IEEE, Lens and Scopus write ``AU``; Web of Science's RIS and
#: older EndNote-style exports write ``A1``. ``A2``..``A4`` are editors and series
#: authors, not the study's authors, so they are not read as authors.
_RIS_AUTHOR_TAGS = frozenset({"AU", "A1"})


class RISImporter:
    """Parses standard RIS academic citation files.

    Wrapped values (a line without a tag, as some exporters write long titles
    and abstracts) are joined to the value they continue with one space
    (M6-hardening H6).
    """

    def parse(self, filepath: str | Path) -> Iterator[Document]:
        current_record: dict[str, Any] = {}
        authors: list[Author] = []
        last_tag: str | None = None

        with Path(filepath).open("r", encoding="utf-8-sig", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                match = _RIS_TAG.match(line)
                if match is None:
                    # A continuation of the previous value.
                    if last_tag is not None and last_tag in current_record:
                        current_record[last_tag] = f"{current_record[last_tag]} {line}".strip()
                    continue

                tag, value = match.group(1), (match.group(2) or "").strip()
                if tag == "ER":
                    if current_record or authors:
                        yield self._build_document(current_record, authors)
                    current_record, authors, last_tag = {}, [], None
                    continue
                if tag in _RIS_AUTHOR_TAGS:
                    if value:
                        authors.append(self._author(value))
                    last_tag = None
                else:
                    current_record[tag] = value
                    last_tag = tag

            if current_record or authors:
                yield self._build_document(current_record, authors)

    @staticmethod
    def _author(value: str) -> Author:
        parts = value.split(",")
        if len(parts) > 1:
            return Author(family_name=parts[0].strip(), given_name=parts[1].strip())
        return Author(family_name=value)

    def _build_document(self, record: dict, authors: list[Author]) -> Document:
        ext_ids = ExternalIds()
        if "DO" in record:
            ext_ids.doi = record["DO"]

        year = None
        if "PY" in record:
            try:
                year = int(record["PY"][:4])
            except (ValueError, IndexError):
                pass
        elif "Y1" in record:
            try:
                year = int(record["Y1"][:4])
            except (ValueError, IndexError):
                pass

        doc = Document(
            title=record.get("TI") or record.get("T1") or "Unknown Title",
            year=year,
            provider="local_ris",
            external_ids=ext_ids,
            abstract=record.get("AB") or record.get("N2"),
            authors=authors,
            venue=record.get("JO") or record.get("JF") or record.get("T2"),
        )
        doc.mark_retrieved()
        return doc


class JSONImporter:
    """Parses standard JSON array files into Document models."""

    def parse(self, filepath: str | Path) -> Iterator[Document]:
        with Path(filepath).open("r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            # If wrapped in a top-level key like {"results": [...]} or {"papers": [...]}
            for key in ("results", "papers", "documents", "data"):
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
            else:
                data = [data]

        for item in data:
            if not isinstance(item, dict):
                continue

            # Parse external IDs
            ext_data = item.get("external_ids", {})
            if not ext_data:
                # Handle flat doi keys
                ext_ids = ExternalIds(
                    doi=item.get("doi"),
                    arxiv_id=item.get("arxiv_id"),
                    pubmed_id=item.get("pubmed_id"),
                    openalex_id=item.get("openalex_id"),
                    s2_id=item.get("s2_id"),
                )
            else:
                ext_ids = ExternalIds(**ext_data)

            # Parse authors
            authors = []
            for a in item.get("authors", []):
                if isinstance(a, dict):
                    authors.append(Author(**a))
                elif isinstance(a, str):
                    authors.append(Author(family_name=a))

            doc = Document(
                title=item.get("title") or "Untitled",
                year=item.get("year"),
                provider=item.get("provider", "local_json"),
                provider_id=item.get("provider_id", ""),
                external_ids=ext_ids,
                abstract=item.get("abstract"),
                authors=authors,
                venue=item.get("venue"),
                url=item.get("url"),
                citations_count=item.get("citations_count"),
                references_count=item.get("references_count"),
                citation_intents=item.get("citation_intents", []),
                mesh_terms=item.get("mesh_terms", []),
                tldr=item.get("tldr"),
                query_id=item.get("query_id"),
                workspace_id=item.get("workspace_id"),
                cluster_id=item.get("cluster_id"),
            )
            doc.mark_retrieved()
            yield doc


class JSONLImporter:
    """Parses JSONL files into Document models."""

    def parse(self, filepath: str | Path) -> Iterator[Document]:
        with Path(filepath).open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)

                ext_ids = ExternalIds(**data.get("external_ids", {}))
                authors = [Author(**a) for a in data.get("authors", [])]

                doc = Document(
                    title=data["title"],
                    year=data.get("year"),
                    provider=data.get("provider", "local_jsonl"),
                    provider_id=data.get("provider_id", ""),
                    external_ids=ext_ids,
                    abstract=data.get("abstract"),
                    authors=authors,
                    venue=data.get("venue"),
                    url=data.get("url"),
                    citations_count=data.get("citations_count"),
                    references_count=data.get("references_count"),
                    citation_intents=data.get("citation_intents", []),
                    mesh_terms=data.get("mesh_terms", []),
                    tldr=data.get("tldr"),
                    query_id=data.get("query_id"),
                    workspace_id=data.get("workspace_id"),
                    cluster_id=data.get("cluster_id"),
                )
                doc.mark_retrieved()
                yield doc
