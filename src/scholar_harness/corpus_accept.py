"""``nexus-scholar accept-corpus``: the entry path into screening (M0).

``prepare`` needs an accepted Contract-v1 ``corpus_snapshot`` in the artifact
registry, but no runtime code built one (CORE-07), so screening could not
start on a fresh workspace. This command builds the snapshot from the
workspace's verified records with the search kit's own builder
(``scholar_search.identity.build_corpus_snapshot_artifact``) and publishes it
through the harness acceptance gate, which validates it against the frozen
Contract-v1 schema and journals the acceptance. Full Packet B adoption in the
discovery stage is M3; this is the minimal bridge.

Sources: ``literature/verified.json`` (what discovery writes), or one export
per database: RIS (Scopus, Web of Science, IEEE Xplore, Zotero...) or PubMed's
MEDLINE ``.nbib`` (*Send to → Citation manager*; M5c-nbib). The format is
chosen per file by its extension, else by sniffing its first line
(``detect_import_format``), and recorded with the staged source. Each export
file is first *staged* under ``literature/raw/ris/`` with its database label;
acceptance writes every staged record to ``verified.json`` (one row per record,
with its source and a record-derived ``SCI-`` id, so a re-import yields the same
ids) and ``literature/raw/provenance_manifest.json`` (records per database, the
total identified). Duplicates within and across files are left to the snapshot
builder's deduplicator, so the PRISMA counts read: identified = every record,
duplicates removed = identified - studies.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from scholar_protocol.canonical import canonical_fingerprint as protocol_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.dedup import Deduplicator
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.importers import NBIBImporter, RISImporter
from scholar_search.models import Document

from .contracts import AcceptanceContext, accept_artifact
from .contracts.canonical import canonical_fingerprint, deterministic_id
from .contracts.identifiers import IdentifierKind
from .screening.batcher import _rebuild_doc
from .workspace.audit import append_event


class AcceptCorpusRefused(Exception):
    """A precondition or the acceptance gate refused; nothing was published."""

    def __init__(self, message: str, code: str = "ACCEPT_CORPUS_REFUSED") -> None:
        super().__init__(message)
        self.code = code


RIS_DIR = Path("literature") / "raw" / "ris"
SOURCES_FILE = RIS_DIR / "sources.json"
MANIFEST_FILE = Path("literature") / "raw" / "provenance_manifest.json"
MAX_SOURCE_BYTES = 50 * 1024 * 1024
LABEL_MAX_LENGTH = 40
_LABEL_RE = re.compile(r"^[\w][\w .&()+/-]*$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class AcceptCorpusResult:
    artifact_id: str
    study_count: int
    record_count: int
    already_accepted: bool
    # The builder's OperationOutcome status (SUCCESS, or PARTIAL when provider
    # warnings were passed) and those warnings (M3a review finding 5).
    outcome_status: str = "SUCCESS"
    warnings: tuple[str, ...] = ()


def _workspace_id(ws: Path) -> str:
    try:
        manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AcceptCorpusRefused(f"project.json is missing or unreadable in {ws}") from exc
    value = manifest.get("registered_workspace_id") if isinstance(manifest, dict) else None
    if not isinstance(value, str) or not value.startswith("WSP-"):
        raise AcceptCorpusRefused(
            "project.json records no registered_workspace_id (WSP-...). Create the "
            "workspace with `nexus-scholar init` or `scholar-harness inception`."
        )
    return value


def _protocol_fingerprint(ws: Path) -> str:
    path = ws / "protocol.json"
    if not path.is_file():
        raise AcceptCorpusRefused(f"protocol.json not found in {ws}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return protocol_fingerprint(ResearchProtocol.model_validate(raw))
    except ValueError as exc:  # JSON and pydantic validation errors
        raise AcceptCorpusRefused(f"protocol.json is not a valid protocol ({exc})", "PROTOCOL_INVALID") from exc


def _stable_sci_id(document: Document, *, source: str, position: int) -> str:
    """A record-derived ``SCI-`` id: the same record of the same file always gets
    the same id. Source and position keep two copies of one paper apart."""
    identity = {
        "source": source,
        "position": position,
        "title": document.title,
        "year": document.year,
        "doi": document.external_ids.doi,
        "authors": [a.family_name for a in document.authors],
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
    return f"SCI-{int(digest[:12], 16):015d}"


def _verified_row(document: Document) -> dict[str, Any]:
    """The ``verified.json`` shape that ``batcher._rebuild_doc`` reads back."""
    eids = document.external_ids
    return {
        "workspace_id": document.workspace_id,
        "title": document.title,
        "year": document.year,
        "provider": document.provider,
        "provider_id": document.provider_id,
        "external_ids": {
            key: value
            for key, value in {
                "doi": eids.doi,
                "arxiv_id": eids.arxiv_id,
                "pubmed_id": eids.pubmed_id,
                "openalex_id": eids.openalex_id,
                "s2_id": eids.s2_id,
            }.items()
            if value
        },
        "abstract": document.abstract,
        "authors": [
            {"family_name": a.family_name, "given_name": a.given_name} for a in document.authors
        ],
        "venue": document.venue,
        "url": document.url,
    }


#: Import formats, by the extension the stored copy keeps.
IMPORT_FORMATS = ("ris", "nbib")
_IMPORTERS = {"ris": RISImporter, "nbib": NBIBImporter}
_FORMAT_NAMES = {"ris": "RIS", "nbib": "PubMed (MEDLINE .nbib)"}


def detect_import_format(file_name: str, content: bytes) -> str:
    """``"ris"`` or ``"nbib"`` for one export file (M5c-nbib).

    The extension decides when it is ``.ris`` or ``.nbib``. Otherwise (``.txt``,
    no extension) the first non-blank line decides: a MEDLINE export starts with
    ``PMID- ``; anything else is read as RIS, the M5b behaviour.
    """
    suffix = Path(file_name).suffix.lower()
    if suffix in {".ris", ".nbib"}:
        return suffix[1:]
    head = content[:4096].decode("utf-8-sig", errors="replace")
    first = next((line.strip() for line in head.splitlines() if line.strip()), "")
    return "nbib" if first.startswith("PMID- ") else "ris"


def _parse_export(path: Path, source_id: str, fmt: str = "ris") -> list[Document]:
    """Every record of one export file, each kept apart with its file and position.

    Records are not collapsed here, not even exact repeats inside one file: the
    snapshot builder's deduplicator does that, so the duplicate count covers both.
    ``provider`` is the format (``ris`` or ``nbib``), so a ``verified.json`` row
    says which reader produced it.
    """
    documents = []
    for position, document in enumerate(_IMPORTERS[fmt]().parse(path), start=1):
        document.provider = fmt
        document.provider_id = f"{source_id}#{position}"
        document.workspace_id = _stable_sci_id(document, source=source_id, position=position)
        documents.append(document)
    return documents


def _check_label(label: str) -> str:
    label = (label or "").strip()
    if not label or len(label) > LABEL_MAX_LENGTH or not _LABEL_RE.match(label):
        raise AcceptCorpusRefused(
            f"database label {label!r} must be 1-{LABEL_MAX_LENGTH} letters, digits, "
            "spaces or . & ( ) + / - _",
            "SOURCE_LABEL_INVALID",
        )
    return label


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "source"


def _accepted_snapshot(ws: Path) -> bool:
    registry = ws / "audit" / "artifact_registry.json"
    if not registry.is_file():
        return False
    entries = json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {})
    return any(e.get("artifact_type") == "corpus_snapshot" for e in entries.values())


def staged_sources(ws: Path) -> list[dict[str, Any]]:
    """The staged RIS sources, in the order they were added."""
    path = Path(ws) / SOURCES_FILE
    if not path.is_file():
        return []
    return list(json.loads(path.read_text(encoding="utf-8")).get("sources", []))


def _write_sources(ws: Path, sources: list[dict[str, Any]]) -> None:
    path = ws / SOURCES_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps({"schema": "nexus.corpus-sources.v1", "sources": sources}, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


def _imported(ws: Path) -> bool:
    """True when ``verified.json`` was written by this import (its manifest says so).

    A discovery harvest also writes ``provenance_manifest.json`` (legacy
    workspaces have one), so the file's presence alone proves nothing.
    """
    path = ws / MANIFEST_FILE
    if not path.is_file():
        return False
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("schema") == IMPORT_MANIFEST_SCHEMA
    except (OSError, ValueError, AttributeError):
        return False


def _refuse_if_frozen(ws: Path) -> None:
    if _accepted_snapshot(ws):
        raise AcceptCorpusRefused(
            "the corpus is already accepted; its sources can no longer change",
            "CORPUS_ALREADY_ACCEPTED",
        )
    if (ws / "literature" / "verified.json").exists() and not _imported(ws):
        raise AcceptCorpusRefused(
            "literature/verified.json already exists (a corpus from discovery); "
            "remove it first to import database exports instead",
            "VERIFIED_EXISTS",
        )


def stage_ris_source(
    workspace: Path | str,
    label: str,
    content: bytes,
    *,
    file_name: str,
    searched_on: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """Copy one database's export (RIS or PubMed ``.nbib``) into the workspace, with its label.

    The file is kept byte for byte under ``literature/raw/ris/`` so the import
    can be re-run and shared; its format is detected from the name and first line
    and recorded. Nothing reaches ``verified.json`` until acceptance.
    """
    ws = Path(workspace).resolve()
    _refuse_if_frozen(ws)
    _deduplicator(ws)  # M7-method: an invalid method block refuses before anything is written
    label = _check_label(label)
    if len(content) > MAX_SOURCE_BYTES:
        raise AcceptCorpusRefused(
            f"{file_name} is larger than {MAX_SOURCE_BYTES // (1024 * 1024)} MB",
            "SOURCE_TOO_LARGE",
        )
    if searched_on is not None and searched_on != "":
        try:
            valid = bool(_DATE_RE.match(searched_on)) and date.fromisoformat(searched_on).isoformat() == searched_on
        except ValueError:
            valid = False
        if not valid:
            raise AcceptCorpusRefused(
                f"date searched {searched_on!r} must be a real date, YYYY-MM-DD", "SOURCE_DATE_INVALID"
            )
    sources = staged_sources(ws)
    digest = hashlib.sha256(content).hexdigest()
    for existing in sources:
        # A database exported in parts is staged once per part under one label;
        # the first spelling of the label is kept so the parts add up together.
        if existing["label"].casefold() == label.casefold():
            label = existing["label"]
        if existing["sha256"] == digest:
            raise AcceptCorpusRefused(
                f"{file_name} is the same file as {existing['label']} ({existing['file_name']})",
                "SOURCE_DUPLICATE_FILE",
            )
    source_id = f"{_slug(label)}-{digest[:8]}"
    fmt = detect_import_format(file_name, content)
    stored = ws / RIS_DIR / f"{source_id}.{fmt}"
    stored.parent.mkdir(parents=True, exist_ok=True)
    stored.write_bytes(content)
    records = len(_parse_export(stored, source_id, fmt))
    if records == 0:
        stored.unlink()
        suffix = Path(file_name).suffix.lower()
        chosen_by = f"from its {suffix} name" if suffix in {".ris", ".nbib"} else "from its first line"
        raise AcceptCorpusRefused(
            f"{file_name} contains no {_FORMAT_NAMES[fmt]} records (read as {fmt} {chosen_by}); "
            "export the results as RIS, or from PubMed as MEDLINE .nbib",
            "SOURCE_NOT_RIS",
        )
    entry = {
        "id": source_id,
        "label": label,
        "file_name": Path(file_name).name,
        "format": fmt,
        "stored_as": stored.relative_to(ws).as_posix(),
        "sha256": digest,
        "records": records,
        "searched_on": searched_on or None,
        "query": (query or "").strip() or None,
    }
    _write_sources(ws, [*sources, entry])
    append_event(
        ws,
        "CORPUS_SOURCE_STAGED",
        f"Staged {records} records from {label} ({entry['file_name']})",
        inputs=[entry["file_name"]],
        outputs=[entry["stored_as"], SOURCES_FILE.as_posix()],
        parameters={
            "id": source_id, "label": label, "format": fmt,
            "searched_on": entry["searched_on"], "query": entry["query"],
        },
        metrics={"records": records, "sha256": digest},
    )
    return entry


def remove_staged_source(workspace: Path | str, source_id: str) -> None:
    """Drop one staged file (by its ``id``) before acceptance; its stored copy goes too."""
    ws = Path(workspace).resolve()
    _refuse_if_frozen(ws)
    _deduplicator(ws)  # M7-method: an invalid method block refuses before anything is written
    sources = staged_sources(ws)
    keep = [s for s in sources if s["id"] != source_id]
    if len(keep) == len(sources):
        raise AcceptCorpusRefused(f"no staged file has the id {source_id!r}", "SOURCE_NOT_FOUND")
    gone = next(s for s in sources if s not in keep)
    (ws / gone["stored_as"]).unlink(missing_ok=True)
    _write_sources(ws, keep)
    append_event(
        ws,
        "CORPUS_SOURCE_REMOVED",
        f"Removed the staged source {gone['label']} ({gone['file_name']})",
        parameters={"id": gone["id"], "label": gone["label"]},
        metrics={"records": gone["records"], "sha256": gone["sha256"]},
    )


def _staged_documents(ws: Path) -> tuple[list[dict[str, Any]], list[Document]]:
    sources = staged_sources(ws)
    documents: list[Document] = []
    for source in sources:
        # Sources staged before M5c-nbib carry no format: they are RIS.
        documents.extend(_parse_export(ws / source["stored_as"], source["id"], source.get("format", "ris")))
    return sources, documents


def databases(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Staged files summed per database label, in the order the labels first appear.

    PRISMA counts records per database; a database exported in parts is one row.
    ``search_details_missing`` is true when any part lacks a date searched or a
    search string, so the screen and the methods paragraph can say "not stated".
    """
    rows: dict[str, dict[str, Any]] = {}
    for source in sources:
        row = rows.setdefault(
            source["label"],
            {"label": source["label"], "records": 0, "files": 0, "searched_on": [], "search_details_missing": False},
        )
        row["records"] += int(source["records"])
        row["files"] += 1
        if source.get("searched_on") and source["searched_on"] not in row["searched_on"]:
            row["searched_on"].append(source["searched_on"])
        if not source.get("searched_on") or not source.get("query"):
            row["search_details_missing"] = True
    for row in rows.values():
        row["searched_on"].sort()
    return list(rows.values())


def _deduplicator(ws: Path) -> Deduplicator:
    """The protocol's dedup tiers (M7-method); an invalid block refuses."""
    from scholar_harness.screening.method import MethodInvalid, effective_method

    try:
        return effective_method(ws).deduplicator()
    except MethodInvalid as exc:
        raise AcceptCorpusRefused(str(exc), exc.code) from exc


def preview_staged(workspace: Path | str) -> dict[str, Any]:
    """The counts acceptance would produce, without writing anything.

    Uses the same deduplicator as the snapshot builder, so ``unique_studies``
    is the number of records screening will show.
    """
    ws = Path(workspace).resolve()
    sources, documents = _staged_documents(ws)
    unique = len(_deduplicator(ws).deduplicate(copy.deepcopy(documents))) if documents else 0
    return {
        "sources": [
            {
                **{k: s[k] for k in ("id", "label", "file_name", "records", "searched_on", "query")},
                "format": s.get("format", "ris"),
            }
            for s in sources
        ],
        "databases": databases(sources),
        "identified": len(documents),
        "duplicates": len(documents) - unique,
        "unique_studies": unique,
    }


IMPORT_MANIFEST_SCHEMA = "nexus.corpus-import.v1"


def prisma_identification(ws: Path, screened_docs: int) -> tuple[int, int]:
    """``(total_identified, duplicates_removed)`` for the PRISMA counts.

    Collect and approval both call this, so the two stay byte-identical. For a
    corpus imported from database exports, ``verified.json`` holds every record
    (duplicates included), so the counts come from the accepted snapshot:
    identified = its records, duplicates = records - studies, the same numbers
    as ``/prisma/preview`` and ``check_golden_workspace.py``. Otherwise the
    discovery harvest manifest is read as before (or no duplicates are known).
    """
    manifest_path = ws / MANIFEST_FILE
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {}
    if manifest.get("schema") == IMPORT_MANIFEST_SCHEMA:
        registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))
        corpora = sorted(
            (e for e in registry.get("artifacts", {}).values() if e.get("artifact_type") == "corpus_snapshot"),
            key=lambda e: str(e.get("accepted_at") or ""),
        )
        data = json.loads((ws / corpora[-1]["path"]).read_text(encoding="utf-8"))["data"]
        records = len(data["record_to_study"])
        return records, records - len(data["studies"])
    total = manifest.get("total_raw_harvested", screened_docs) if manifest else screened_docs
    return total, max(0, total - screened_docs)


def corpus_status(workspace: Path | str) -> dict[str, Any]:
    """What the Import screen shows: ``EMPTY``, ``STAGED`` or ``ACCEPTED``, with counts."""
    ws = Path(workspace).resolve()
    registry = ws / "audit" / "artifact_registry.json"
    snapshot = None
    if registry.is_file():
        entries = json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {})
        accepted = [e for e in entries.values() if e.get("artifact_type") == "corpus_snapshot"]
        if accepted:
            snapshot = max(accepted, key=lambda e: str(e.get("accepted_at") or ""))
    preview = preview_staged(ws)
    sources = preview["sources"]
    status: dict[str, Any] = {
        "shape": "screening.corpus-v1",
        "state": "ACCEPTED" if snapshot else ("STAGED" if sources else "EMPTY"),
        "sources": sources,
        "databases": preview["databases"],
        "preview": {k: preview[k] for k in ("identified", "duplicates", "unique_studies")},
        "accepted": None,
        "from_discovery": False,
        "limits": {"max_source_bytes": MAX_SOURCE_BYTES, "label_max_length": LABEL_MAX_LENGTH},
    }
    if snapshot:
        artifact = json.loads((ws / snapshot["path"]).read_text(encoding="utf-8"))
        studies = len(artifact["data"]["studies"])
        records = len(artifact["data"]["record_to_study"])
        status["accepted"] = {
            "artifact_id": artifact["artifact_id"],
            "accepted_at": snapshot.get("accepted_at"),
            "records": records,
            "studies": studies,
            "duplicates": records - studies,
        }
        status["from_discovery"] = not sources
    else:
        verified = ws / "literature" / "verified.json"
        status["from_discovery"] = verified.is_file() and not _imported(ws)
    return status


def _materialise_staged(ws: Path) -> None:
    """Write ``verified.json`` and the provenance manifest from the staged sources."""
    sources, documents = _staged_documents(ws)
    if not documents:
        raise AcceptCorpusRefused("no database export is staged", "NOTHING_STAGED")
    verified = ws / "literature" / "verified.json"
    verified.parent.mkdir(parents=True, exist_ok=True)
    label_of = {s["id"]: s["label"] for s in sources}
    rows = []
    for document in documents:
        row = _verified_row(document)
        row["source_database"] = label_of[document.provider_id.rsplit("#", 1)[0]]
        rows.append(row)
    verified.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    manifest = {
        "schema": IMPORT_MANIFEST_SCHEMA,
        "total_raw_harvested": len(documents),
        "sources": [
            {
                **{k: s[k] for k in ("id", "label", "file_name", "stored_as", "sha256", "records", "searched_on", "query")},
                "format": s.get("format", "ris"),
            }
            for s in sources
        ],
        "databases": databases(sources),
    }
    (ws / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    append_event(
        ws,
        "CORPUS_IMPORTED",
        f"Imported {len(documents)} records from {len(sources)} export file(s) of "
        f"{len(databases(sources))} database(s) into literature/verified.json",
        inputs=[s["stored_as"] for s in sources],
        outputs=["literature/verified.json", MANIFEST_FILE.as_posix()],
        parameters={
            "formats": sorted({s.get("format", "ris") for s in sources}),
            "sources": [s["id"] for s in sources],
        },
        metrics={"records": len(documents), "by_source": {d["label"]: d["records"] for d in databases(sources)}},
    )


def import_ris(ws: Path, sources: list[tuple[str | None, Path]]) -> int:
    """Stage exports (RIS or PubMed ``.nbib``) given as ``(label, path)`` (label ``None``: the file stem)."""
    for label, path in sources:
        path = Path(path)
        if not path.is_file():
            raise AcceptCorpusRefused(f"export file not found: {path}", "SOURCE_NOT_FOUND")
        stage_ris_source(ws, label or path.stem, path.read_bytes(), file_name=path.name)
    return sum(s["records"] for s in staged_sources(ws))


def parse_ris_option(value: str) -> tuple[str | None, Path]:
    """``LABEL=PATH`` or a bare ``PATH`` (Windows drive letters are not labels)."""
    label, sep, rest = value.partition("=")
    if sep and label.strip() and not any(c in label for c in "/\\:"):
        return label.strip(), Path(rest)
    return None, Path(value)


def accept_corpus(
    workspace: Path | str,
    *,
    ris: list[Path | tuple[str | None, Path]] | None = None,
    now: datetime | None = None,
    provider_warnings: list[str] | None = None,
) -> AcceptCorpusResult:
    """Build and accept the corpus snapshot for ``workspace``.

    Preconditions are checked before anything is written. Re-running on the
    same records and protocol is idempotent: the deterministic artifact id is
    already in the registry, and nothing new is published.
    """
    ws = Path(workspace).resolve()
    workspace_id = _workspace_id(ws)
    # The specific refusal first: an invalid method block also fails the full
    # protocol validation below, which would only say PROTOCOL_INVALID.
    deduplicator = _deduplicator(ws)
    fingerprint = _protocol_fingerprint(ws)
    if ris:
        _refuse_if_frozen(ws)
        import_ris(ws, [r if isinstance(r, tuple) else (None, Path(r)) for r in ris])
    if not _accepted_snapshot(ws):
        if staged_sources(ws):
            _materialise_staged(ws)
        elif _imported(ws):
            raise AcceptCorpusRefused(
                "every database file was removed; add at least one before accepting",
                "NOTHING_STAGED",
            )

    verified = ws / "literature" / "verified.json"
    if not verified.is_file():
        raise AcceptCorpusRefused(
            f"{verified} not found; run discovery first or pass --ris <export.ris>",
            "NOTHING_STAGED",
        )
    rows = json.loads(verified.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise AcceptCorpusRefused(f"{verified} has no records")
    documents = [_rebuild_doc(row, f"SCI-{i:06d}") for i, row in enumerate(rows, start=1)]

    run_id = deterministic_id(
        IdentifierKind.RUN,
        workspace_id,
        {
            "operation": "accept-corpus",
            "protocol_fingerprint": fingerprint,
            "records_sha256": canonical_fingerprint(rows),
        },
    )
    built = build_corpus_snapshot_artifact(
        documents,
        workspace_id=workspace_id,
        run_id=run_id,
        protocol_fingerprint=fingerprint,
        created_at=now or datetime.now(UTC),
        deduplicator=deduplicator,
        provider_warnings=provider_warnings,
    )
    artifact = built.artifact
    registry = ws / "audit" / "artifact_registry.json"
    if registry.is_file():
        entries = json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {})
        if artifact["artifact_id"] in entries:
            return AcceptCorpusResult(
                artifact["artifact_id"],
                len(artifact["data"]["studies"]),
                len(documents),
                already_accepted=True,
                outcome_status=str(built.outcome.get("status", "SUCCESS")),
                warnings=tuple(built.outcome.get("warnings", ())),
            )

    result = accept_artifact(
        ws,
        artifact,
        expected=AcceptanceContext(
            workspace_id=workspace_id,
            protocol_fingerprint=fingerprint,
            corpus_fingerprint=artifact["corpus_fingerprint"],
        ),
        actor="nexus-scholar-accept-corpus",
    )
    if not result.accepted:
        issues = "; ".join(f"{i.code}: {i.message}" for i in result.issues) or "no detail"
        raise AcceptCorpusRefused(f"the acceptance gate refused the snapshot ({issues})")
    return AcceptCorpusResult(
        artifact["artifact_id"],
        len(artifact["data"]["studies"]),
        len(documents),
        already_accepted=False,
        outcome_status=str(built.outcome.get("status", "SUCCESS")),
        warnings=tuple(built.outcome.get("warnings", ())),
    )
