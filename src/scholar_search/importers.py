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


#: A MEDLINE tag line: one to four capitals or digits padded to four columns,
#: a hyphen, a space, the value (``PMID- 123``, ``TI  - ...``, ``FAU - ...``).
_NBIB_TAG = re.compile(r"^([A-Z][A-Z0-9]{0,3}) {0,3}- ?(.*)$")
#: ``AID``/``LID`` values carry their kind in brackets: ``10.1000/x [doi]``, ``s123 [pii]``.
_NBIB_DOI = re.compile(r"^(.*?)\s*\[doi\]$", re.IGNORECASE)
_NBIB_YEAR = re.compile(r"\d{4}")


class NBIBImporter:
    """Parses PubMed MEDLINE exports (*Send to → Citation manager*, ``.nbib``).

    Each line is a four-column tag, ``- `` and the value. A wrapped value
    continues on lines that start with spaces and is joined with one space. A
    blank line (or the next ``PMID``) ends the record. A tag may repeat
    (``FAU``/``AU``, ``MH``, ``PT``, ``AID``, ``LA``) and every value is kept in
    order. A record without a ``PMID`` is not a MEDLINE record and is skipped,
    so a RIS file passed here yields nothing (M5c-nbib).

    Mapping: ``PMID`` → ``external_ids.pubmed_id`` and ``provider_id``; ``TI``,
    ``AB``; ``FAU`` ("Family, Given") preferred over ``AU`` ("Family I"); ``DP``
    first four digits → year; ``JT`` else ``TA`` → venue; ``AID … [doi]``, else
    ``LID … [doi]`` → DOI; ``MH`` → ``mesh_terms``; ``PT``, ``OT`` and ``LA`` are
    kept in ``raw_data`` (``publication_types``, ``keywords``, ``language``).
    """

    def parse(self, filepath: str | Path) -> Iterator[Document]:
        record: dict[str, list[str]] = {}
        last_tag: str | None = None

        with Path(filepath).open("r", encoding="utf-8-sig", errors="replace") as f:
            for raw in f:
                line = raw.rstrip("\r\n")
                if not line.strip():
                    if record:
                        yield from self._emit(record)
                    record, last_tag = {}, None
                    continue
                match = None if line[0] == " " else _NBIB_TAG.match(line)
                if match is None:
                    # A continuation of the previous value (PubMed indents it six spaces).
                    if last_tag is not None and record.get(last_tag):
                        values = record[last_tag]
                        values[-1] = f"{values[-1]} {line.strip()}".strip()
                    continue
                tag, value = match.group(1), match.group(2).strip()
                if tag == "PMID" and record:
                    # A new record glued to the previous one without a blank line.
                    yield from self._emit(record)
                    record = {}
                record.setdefault(tag, []).append(value)
                last_tag = tag

            if record:
                yield from self._emit(record)

    def _emit(self, record: dict[str, list[str]]) -> Iterator[Document]:
        pmid = next((v.strip() for v in record.get("PMID", []) if v.strip()), None)
        if pmid is None:
            return
        authors = [self._full_author(v) for v in record.get("FAU", []) if v.strip()] or [
            self._abbreviated_author(v) for v in record.get("AU", []) if v.strip()
        ]
        year = None
        for value in record.get("DP", []):
            found = _NBIB_YEAR.search(value)
            if found:
                year = int(found.group())
                break
        doc = Document(
            title=" ".join(record.get("TI", [])).strip() or "Unknown Title",
            year=year,
            provider="local_nbib",
            provider_id=pmid,
            external_ids=ExternalIds(
                doi=self._doi(record.get("AID", [])) or self._doi(record.get("LID", [])),
                pubmed_id=pmid,
            ),
            abstract=" ".join(record.get("AB", [])).strip() or None,
            authors=authors,
            venue=next((v for v in [*record.get("JT", []), *record.get("TA", [])] if v.strip()), None),
            mesh_terms=[v for v in record.get("MH", []) if v.strip()],
            raw_data={
                "publication_types": [v for v in record.get("PT", []) if v.strip()],
                "keywords": [v for v in record.get("OT", []) if v.strip()],
                "language": [v for v in record.get("LA", []) if v.strip()],
            },
        )
        doc.mark_retrieved()
        yield doc

    @staticmethod
    def _doi(values: list[str]) -> str | None:
        for value in values:
            found = _NBIB_DOI.match(value.strip())
            if found and found.group(1).strip():
                return found.group(1).strip()
        return None

    @staticmethod
    def _full_author(value: str) -> Author:
        """``FAU``: ``Family, Given`` (the given part may be missing for a group author)."""
        family, _, given = value.partition(",")
        return Author(family_name=family.strip(), given_name=given.strip() or None)

    @staticmethod
    def _abbreviated_author(value: str) -> Author:
        """``AU``: ``Family I`` with the initials after the last space (``van der Berg A``)."""
        family, _, initials = value.strip().rpartition(" ")
        if not family:
            return Author(family_name=initials)
        return Author(family_name=family.strip(), given_name=initials.strip() or None)


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
