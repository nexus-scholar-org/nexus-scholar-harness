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

M3f-combined-corpus: until the accept a corpus has two parts, the harvest (the
newest search run published as the corpus, once its preparation is ready) and
the staged exports, changed on their own and in any order. The accept hands
the builder the harvest's ``verified.json`` rows, then every staged record, and
the deduplicator runs once over both (``_materialise_combined``); the harvest's
own file is kept in its run folder. A harvest-only or import-only accept is
unchanged.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, replace
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
from .screening import read_store
from .screening.batcher import _rebuild_doc
from .workspace.audit import append_event


class AcceptCorpusRefused(Exception):
    """A precondition or the acceptance gate refused; nothing was published."""

    def __init__(
        self, message: str, code: str = "ACCEPT_CORPUS_REFUSED", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        #: Typed facts beside the message (M3i: the unfinished run, its state and stage).
        self.details = details


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
    # M3f: the harvest run combined with the staged exports, or the unfinished
    # harvest the accept left out because exports were staged ({run, state}).
    combined_run: str | None = None
    left_out: dict[str, Any] | None = None


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
        raw = json.loads(read_store.read_text(path))
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
    return _read_export(path, source_id, fmt)[0]


def _read_export(path: Path, source_id: str, fmt: str = "ris") -> tuple[list[Document], list[dict[str, Any]]]:
    """``_parse_export`` plus the lines the importer could not use (E3, M3d-engine)."""
    importer = _IMPORTERS[fmt]()
    documents = []
    for position, document in enumerate(importer.parse(path), start=1):
        document.provider = fmt
        document.provider_id = f"{source_id}#{position}"
        document.workspace_id = _stable_sci_id(document, source=source_id, position=position)
        documents.append(document)
    return documents, list(importer.rejected)


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
    entries = json.loads(read_store.read_text(registry)).get("artifacts", {})
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
    return _manifest_schema(ws) in (IMPORT_MANIFEST_SCHEMA, COMBINED_MANIFEST_SCHEMA)


def _manifest(ws: Path) -> dict[str, Any] | None:
    path = ws / MANIFEST_FILE
    if not path.is_file():
        return None
    try:
        value = json.loads(read_store.read_text(path))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _manifest_schema(ws: Path) -> str | None:
    manifest = _manifest(ws)
    return manifest.get("schema") if manifest else None


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def harvest_part(ws: Path) -> dict[str, Any] | None:
    """The harvest part of a corpus not yet accepted (M3f), or ``None`` without a published run.

    The newest search run published as the corpus, with its preparation state
    (``ready``, ``incomplete``, ``failed``, ...) and whether the accept would
    include it: only a ready preparation is included (an unfinished one is
    never frozen, M3i item 7). ``rows_path`` is where its works are: the run's
    own copy when an earlier combined accept made one, else ``verified.json``.
    A ready run whose ``verified.json`` was written over by an import accept
    the gate refused (before M3f) has no rows left, so it is not included,
    unless the run's verification wrote ``verified.json`` after that manifest
    (review F1: the file is then the run's own and the manifest is stale).
    """
    from .pipeline.harvest_marker import READY, corpus_run_dir, preparation_view

    lit = ws / "literature"
    run_dir = corpus_run_dir(lit)
    if run_dir is None:
        return None
    view = preparation_view(lit, run_dir, published=True, newest_published=True)
    own = run_dir / "verified.json"
    included = view["state"] == READY and (own.is_file() or not _imported(ws) or _verified_after_manifest(ws))
    manifest = _read_json(run_dir / "legs.json")
    return {
        "run": run_dir.name, "state": view["state"], "included": included, "run_dir": run_dir,
        "manifest": manifest if isinstance(manifest, dict) else {},
        "rows_path": own if own.is_file() else lit / "verified.json",
    }


def _verified_after_manifest(ws: Path) -> bool:
    """True when ``verified.json`` was written after the provenance manifest (a search's, not the import's)."""
    try:
        return (ws / "literature" / "verified.json").stat().st_mtime_ns > (ws / MANIFEST_FILE).stat().st_mtime_ns
    except OSError:
        return False


def public_harvest(harvest: dict[str, Any] | None) -> dict[str, Any] | None:
    """What the corpus view says of the harvest part: ``{run, state, included}``."""
    return None if harvest is None else {k: harvest[k] for k in ("run", "state", "included")}


def failed_leg_warnings(manifest: dict[str, Any]) -> list[str]:
    """The snapshot warnings of a run's failed databases, as the pipeline passes them (M3d decision 3)."""
    errors = {
        str(leg.get("provider")): str(leg.get("error") or "failed")
        for leg in manifest.get("legs") or []
        if isinstance(leg, dict) and leg.get("status") == "failed"
    }
    return [f"{name}: {error}" for name, error in sorted(errors.items())]


def _staging_refusal(ws: Path) -> AcceptCorpusRefused | None:
    """Why a database export cannot be staged now, or ``None`` when it can.

    M3f-combined-corpus: an export can be staged before or after a search run;
    the accept combines the two. Refused once the corpus is accepted, and for a
    ``verified.json`` that no search run and no import of this app made
    (records of unknown origin, which are never mixed with an export).
    """
    if _accepted_snapshot(ws):
        return AcceptCorpusRefused(
            "the corpus is already accepted; its sources can no longer change",
            "CORPUS_ALREADY_ACCEPTED",
        )
    if (ws / "literature" / "verified.json").exists() and not _imported(ws):
        from .pipeline.harvest_marker import corpus_run_dir

        if corpus_run_dir(ws / "literature") is None:
            return AcceptCorpusRefused(
                "literature/verified.json holds records that no search run and no import of this app made, "
                "so their origin is unknown and a database export is not mixed with them. Accept them as "
                "they are, or remove literature/verified.json to import exports instead",
                "VERIFIED_EXISTS",
            )
    return None


def refuse_if_run_protocol_changed(ws: Path, manifest: dict[str, Any]) -> None:
    """Refuse a search run's corpus when ``protocol.json`` no longer compiles to the search it ran.

    The hand-off accept (M3d-engine) binds the run's records to the current
    protocol fingerprint, so the run must have searched that protocol's query,
    year window, language, retrieval cap and databases (review F3; a run from
    before F3 is checked on its query and year window):
    ``PROTOCOL_CHANGED_SINCE_RUN`` otherwise. An edit outside the search (the
    criteria, the title) is flagged on the hand-off but does not refuse
    (decision 2026-11-12).
    """
    from .pipeline.discovery import run_protocol_drift

    # Review R1: a missing or unreadable protocol refuses typed (as accept_corpus does), never a 500.
    _protocol_fingerprint(ws)
    if run_protocol_drift(ws / "protocol.json", manifest)["search_changed"]:
        raise AcceptCorpusRefused(
            f"{manifest.get('run') or 'the search run'} searched a query, year window, language, cap or "
            "database list the protocol no longer has; run the search again before accepting its corpus",
            "PROTOCOL_CHANGED_SINCE_RUN",
        )


def refuse_if_preparation_unfinished(ws: Path) -> None:
    """Refuse a search run's corpus while the stages after its search have not ended.

    M3i-harvest-robustness: a run is published right after its search, and
    ``literature/verified.json`` is that run's only once its verification
    ended (the run's stage marker says so). Until then the file is missing or
    is an earlier run's, and nothing is frozen: ``PREPARATION_UNFINISHED``,
    with the run, the state and the stage in ``details``. A run made before
    the marker existed is not refused when a ``verified.json`` exists (its
    state is not guessed); without one it is refused as ``interrupted``.
    """
    from .pipeline.harvest_marker import pending_preparation

    pending = pending_preparation(ws)
    if pending is None:
        return
    where = f" at {pending['stage']}" if pending.get("stage") else ""
    raise AcceptCorpusRefused(
        f"the corpus of {pending['run']} is not prepared yet ({pending['state']}{where}); "
        "finish preparing it on the Harvest screen, or search again",
        "PREPARATION_UNFINISHED",
        {"run": pending["run"], "state": pending["state"], "stage": pending.get("stage")},
    )


def _refuse_if_frozen(ws: Path) -> None:
    refusal = _staging_refusal(ws)
    if refusal is not None:
        raise refusal


def stage_ris_source(
    workspace: Path | str,
    label: str,
    content: bytes,
    *,
    file_name: str,
    searched_on: str | None = None,
    query: str | None = None,
    limits: str | None = None,
) -> dict[str, Any]:
    """Copy one database's export (RIS or PubMed ``.nbib``) into the workspace, with its label.

    The file is kept byte for byte under ``literature/raw/ris/`` so the import
    can be re-run and shared; its format is detected from the name and first line
    and recorded. Nothing reaches ``verified.json`` until acceptance.

    E3 (M3d-engine): the row carries ``rejected`` (the lines the importer could
    not use, ``{line, code, reason}``) and ``limits`` (the filters the researcher
    applied in the database, stored verbatim; ``None`` when not given).
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
    parsed, rejected = _read_export(stored, source_id, fmt)
    records = len(parsed)
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
        "limits": limits if limits and limits.strip() else None,
        "rejected": rejected,
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
            "limits": entry["limits"],
        },
        metrics={"records": records, "sha256": digest, "rejected": len(rejected)},
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
        "sources": _source_rows(sources),
        "databases": databases(sources),
        "identified": len(documents),
        "duplicates": len(documents) - unique,
        "unique_studies": unique,
    }


def _source_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The staged files as the corpus view lists them (no file is parsed)."""
    return [
        {
            **{k: s[k] for k in ("id", "label", "file_name", "records", "searched_on", "query")},
            "format": s.get("format", "ris"),
            # E3 (M3d-engine); rows staged before it carry neither.
            "limits": s.get("limits"),
            "rejected": list(s.get("rejected") or []),
        }
        for s in sources
    ]


def _staged_as_accepted(ws: Path, sources: list[dict[str, Any]], manifest: dict[str, Any] | None) -> bool:
    """True when the staged files are, byte for byte, the ones the accepted corpus was built from.

    H-screening-read-performance: the acceptance's manifest names each file's id and
    sha256; each stored file is hashed again here (no parsing).
    """
    if not manifest or manifest.get("schema") not in (IMPORT_MANIFEST_SCHEMA, COMBINED_MANIFEST_SCHEMA):
        return False
    accepted = [(m.get("id"), m.get("sha256")) for m in manifest.get("sources") or [] if isinstance(m, dict)]
    if accepted != [(s.get("id"), s.get("sha256")) for s in sources]:
        return False
    for source in sources:
        try:
            if hashlib.sha256((ws / source["stored_as"]).read_bytes()).hexdigest() != source["sha256"]:
                return False
        except (OSError, KeyError, TypeError):
            return False
    return True


def _accepted_counts(
    ws: Path, snapshot: dict[str, Any], sources: list[dict[str, Any]], manifest: dict[str, Any] | None
) -> dict[str, int] | None:
    """``preview_staged``'s counts for exports accepted alone, read from the acceptance (no de-duplication).

    H-screening-read-performance: answered from the accepted snapshot and its manifest
    only when the snapshot is the one those exports built: an import manifest whose
    record count is the staged files' and the snapshot's, round 1 (a later round's
    snapshot is the chase's), and the protocol the snapshot was built under is the
    current one (so is its de-duplication method). Otherwise ``None``: the exports are
    parsed and de-duplicated again, as before.
    """
    from .screening.rounds import current_round

    if not manifest or manifest.get("schema") != IMPORT_MANIFEST_SCHEMA:
        return None
    if int(current_round(ws).get("round") or 1) > 1:
        return None
    try:
        artifact = json.loads(read_store.read_text(ws / snapshot["path"]))
        records = len(artifact["data"]["record_to_study"])
        studies = len(artifact["data"]["studies"])
        staged = sum(int(s["records"]) for s in sources)
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if manifest.get("total_raw_harvested") != records or staged != records:
        return None
    try:
        current = _protocol_fingerprint(ws)
    except AcceptCorpusRefused:
        # Review finding 2: an unreadable protocol is not this path's refusal to make; the
        # full preview answers as it always did.
        return None
    if artifact.get("protocol_fingerprint") != current:
        return None
    return {"identified": records, "duplicates": records - studies, "unique_studies": studies}


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
    from .screening.rounds import chase_identification

    # M3g: a citation-searching round identifies what the chase fetched; its
    # duplicates are the records found twice or already in the corpus.
    chased = chase_identification(ws)
    if chased is not None:
        return chased
    manifest_path = ws / MANIFEST_FILE
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {}
    if manifest.get("schema") in (IMPORT_MANIFEST_SCHEMA, COMBINED_MANIFEST_SCHEMA):
        registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))
        corpora = sorted(
            (e for e in registry.get("artifacts", {}).values() if e.get("artifact_type") == "corpus_snapshot"),
            key=lambda e: str(e.get("accepted_at") or ""),
        )
        data = json.loads((ws / corpora[-1]["path"]).read_text(encoding="utf-8"))["data"]
        records = len(data["record_to_study"])
        if manifest.get("schema") == COMBINED_MANIFEST_SCHEMA:
            # M3f: the harvest's records fetched (its own duplicates included) plus every imported record.
            records = int(manifest.get("total_raw_harvested") or records)
        return records, records - len(data["studies"])
    total = manifest.get("total_raw_harvested", screened_docs) if manifest else screened_docs
    return total, max(0, total - screened_docs)


#: Review F4: the names the corpus view gives a database a run searched (the UI's own names).
DATABASE_LABELS = {
    "openalex": "OpenAlex", "semanticscholar": "Semantic Scholar", "crossref": "Crossref",
    "arxiv": "arXiv", "pubmed": "PubMed", "biorxiv": "bioRxiv",
}


def _leg_rows(legs: list[Any]) -> list[dict[str, Any]]:
    """One corpus-view row per database a run searched, summed over its legs (review F4).

    The import rows' keys (``label``, ``records``, ``files``, ``searched_on``,
    ``search_details_missing``) plus ``provider``, ``status`` and ``cap_hit``:
    a database the engine searched has its query and date in the run's record,
    so its search details are never missing, and it has no export file.
    """
    rows: dict[str, dict[str, Any]] = {}
    for leg in legs:
        if not isinstance(leg, dict) or not leg.get("provider"):
            continue
        provider = str(leg["provider"])
        row = rows.setdefault(provider, {
            "label": DATABASE_LABELS.get(provider, provider), "records": 0, "files": 0, "searched_on": [],
            "search_details_missing": False, "provider": provider, "status": "ok", "cap_hit": False,
        })
        row["records"] += int(leg.get("fetched") or 0)
        row["cap_hit"] = row["cap_hit"] or bool(leg.get("cap_hit"))
        if leg.get("status") and leg.get("status") != "ok":
            row["status"] = str(leg["status"])
        day = str(leg.get("started_at") or "")[:10]
        if day and day not in row["searched_on"]:
            row["searched_on"].append(day)
    for row in rows.values():
        row["searched_on"].sort()
    return list(rows.values())


def _harvest_view(ws: Path) -> tuple[str, list[dict[str, Any]] | None, dict[str, int]] | None:
    """``(origin, databases, preview)`` of a corpus that came from a search, else ``None`` (review F4).

    A citation-searching round (M3g) reads its chase run's own counts
    (identified = fetched, duplicates = found twice or already in the corpus,
    studies = the new works); it gives no database rows (``None``), because
    citation searching is not a database search (PRISMA 2020 reports it under
    other methods) and the chase screen lists its legs. A browser harvest reads
    the newest run published as the corpus: its legs, and ``deduped.json``
    for the studies after deduplication. Unreadable files answer ``None``.
    """
    from .pipeline.coordinator import discovery_corpus_run
    from .screening.rounds import ARM_CITATION_SEARCHING, current_round

    def read(path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    current = current_round(ws)
    if current.get("arm") == ARM_CITATION_SEARCHING and current.get("chase"):
        chase = read(ws / "literature" / "citation_chase" / str(current["chase"]) / "chase.json")
        if not isinstance(chase, dict) or not isinstance(chase.get("counts"), dict):
            return None
        counts = chase["counts"]
        duplicates = int(counts.get("duplicates_within_chase") or 0) + int(counts.get("already_in_corpus") or 0)
        preview = {
            "identified": int(counts.get("raw") or 0), "duplicates": duplicates,
            "unique_studies": int(counts.get("new") or 0),
        }
        return "citation_searching", None, preview
    run_dir = discovery_corpus_run(ws)
    manifest = read(run_dir / "legs.json") if run_dir is not None else None
    if not isinstance(manifest, dict):
        return None
    rows = _leg_rows(list(manifest.get("legs") or []))
    identified = sum(row["records"] for row in rows)
    deduped = read(ws / "literature" / "deduped.json")
    unique = len(deduped) if isinstance(deduped, list) else identified
    return "discovery", rows, {"identified": identified, "duplicates": max(0, identified - unique), "unique_studies": unique}


def corpus_status(workspace: Path | str) -> dict[str, Any]:
    """What the Import screen shows: ``EMPTY``, ``STAGED`` or ``ACCEPTED``, with counts."""
    ws = Path(workspace).resolve()
    registry = ws / "audit" / "artifact_registry.json"
    snapshot = None
    if registry.is_file():
        entries = json.loads(read_store.read_text(registry)).get("artifacts", {})
        accepted = [e for e in entries.values() if e.get("artifact_type") == "corpus_snapshot"]
        if accepted:
            snapshot = max(accepted, key=lambda e: str(e.get("accepted_at") or ""))
    # H-screening-read-performance: while nothing is accepted, or when a staged file
    # changed since the accept, the exports are parsed and de-duplicated as before.
    # Once accepted from these very files, the staged counts are computed only if the
    # answer shows them, and then read from the acceptance where it is certain.
    staged = staged_sources(ws)
    manifest_now = _manifest(ws) if snapshot else None
    preview: dict[str, Any] | None = None
    if not snapshot or (staged and not _staged_as_accepted(ws, staged, manifest_now)):
        preview = preview_staged(ws)
    elif any(int(s.get("records") or 0) for s in staged):
        _deduplicator(ws)  # an invalid method block refuses, as the de-duplication would
    sources = preview["sources"] if preview is not None else _source_rows(staged)
    status: dict[str, Any] = {
        "shape": "screening.corpus-v1",
        "state": "ACCEPTED" if snapshot else ("STAGED" if sources else "EMPTY"),
        "sources": sources,
        "databases": preview["databases"] if preview is not None else databases(staged),
        # Set below, by the first part of the answer that shows counts.
        "preview": {k: preview[k] for k in ("identified", "duplicates", "unique_studies")} if preview is not None else None,
        "accepted": None,
        "from_discovery": False,
        # Review F4: where the corpus comes from: "imports", "discovery",
        # "citation_searching" (an M3g round), or None while nothing is there.
        "origin": "imports" if sources else None,
        "limits": {"max_source_bytes": MAX_SOURCE_BYTES, "label_max_length": LABEL_MAX_LENGTH},
        # M3d-engine: why staging an export is refused now ({code, message}), else None.
        "staging_refused": None,
        # M3f: the harvest part ({run, state, included}), or None without a published search run.
        "harvest": None,
    }
    refusal = _staging_refusal(ws)
    if refusal is not None:
        status["staging_refused"] = {"code": refusal.code, "message": str(refusal)}
    if snapshot:
        artifact = json.loads(read_store.read_text(ws / snapshot["path"]))
        studies = len(artifact["data"]["studies"])
        records = len(artifact["data"]["record_to_study"])
        status["accepted"] = {
            "artifact_id": artifact["artifact_id"],
            "accepted_at": snapshot.get("accepted_at"),
            "records": records,
            "studies": studies,
            "duplicates": records - studies,
        }
        manifest = _manifest(ws) or {}
        if manifest.get("schema") == COMBINED_MANIFEST_SCHEMA and isinstance(manifest.get("harvest"), dict):
            # M3f: an accepted combined corpus names both parts.
            part = manifest["harvest"]
            status["from_discovery"] = True
            status["origin"] = "combined"
            status["harvest"] = {"run": part.get("run"), "state": "ready", "included": True}
            status["databases"] = [*(part.get("databases") or []), *databases(staged)]
            identified = int(manifest.get("total_raw_harvested") or records)
            status["preview"] = {"identified": identified, "duplicates": max(0, identified - studies),
                                 "unique_studies": studies}
        else:
            status["from_discovery"] = not sources
    else:
        from .pipeline.harvest_marker import pending_preparation

        verified = ws / "literature" / "verified.json"
        # M3i-harvest-robustness: while the newest published run's later stages
        # have not ended, verified.json is an earlier run's (or missing): no
        # discovery corpus is waiting for the accept.
        status["from_discovery"] = verified.is_file() and not _imported(ws) and pending_preparation(ws) is None
        if status["from_discovery"]:
            # M3d-engine: a discovery corpus waiting for the hand-off accept is
            # staged, as database exports are (decision 2026-11-10).
            status["state"] = "STAGED"
        harvest = harvest_part(ws)
        status["harvest"] = public_harvest(harvest)
        if sources and harvest is not None and harvest["included"]:
            # M3f: the corpus the accept would build from both parts.
            combined = corpus_preview(ws)
            status["origin"] = "combined"
            status["preview"] = {k: combined[k] for k in ("identified", "duplicates", "unique_studies")}
            status["databases"] = [*_harvest_databases(harvest["manifest"]), *preview["databases"]]
            return status
    from .screening.rounds import ARM_CITATION_SEARCHING, current_round

    chase_round = snapshot is not None and current_round(ws).get("arm") == ARM_CITATION_SEARCHING
    if (status["from_discovery"] and status["origin"] != "combined") or chase_round:
        # Review F4: a corpus from a search shows its databases and counts, not zeros;
        # an M3g round shows its chase, also after a first round built from imports.
        # In an M3g round only ``origin`` and ``preview`` change: the database
        # rows and ``from_discovery`` stay round 1's (the databases arm).
        harvest = _harvest_view(ws)
        if harvest is not None:
            status["origin"], rows, status["preview"] = harvest
            if rows is not None:
                status["databases"] = rows
    if status["preview"] is None:
        # An accepted corpus whose counts no other part gave: the staged exports' own.
        counts = _accepted_counts(ws, snapshot, staged, manifest_now) if snapshot else None
        if counts is None:
            full = preview_staged(ws)
            counts = {k: full[k] for k in ("identified", "duplicates", "unique_studies")}
        status["preview"] = counts
    return status


def _staged_rows(ws: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The staged sources and their records as ``verified.json`` rows, each with its ``source_database``."""
    sources, documents = _staged_documents(ws)
    label_of = {s["id"]: s["label"] for s in sources}
    rows = []
    for document in documents:
        row = _verified_row(document)
        row["source_database"] = label_of[document.provider_id.rsplit("#", 1)[0]]
        rows.append(row)
    return sources, rows


def _manifest_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **{k: s[k] for k in ("id", "label", "file_name", "stored_as", "sha256", "records", "searched_on", "query")},
            "format": s.get("format", "ris"),
        }
        for s in sources
    ]


def _materialise_staged(ws: Path, *, left_out: dict[str, Any] | None = None) -> None:
    """Write ``verified.json`` and the provenance manifest from the staged sources.

    M3f review F5: ``left_out`` ({run, state}) is the unfinished harvest the
    accept leaves out; it is journaled with ``CORPUS_IMPORTED``.
    """
    sources, rows = _staged_rows(ws)
    if not rows:
        raise AcceptCorpusRefused("no database export is staged", "NOTHING_STAGED")
    verified = ws / "literature" / "verified.json"
    verified.parent.mkdir(parents=True, exist_ok=True)
    verified.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    manifest = {
        "schema": IMPORT_MANIFEST_SCHEMA,
        "total_raw_harvested": len(rows),
        "sources": _manifest_sources(sources),
        "databases": databases(sources),
    }
    (ws / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    documents = rows
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
            **({"left_out": left_out} if left_out else {}),
        },
        metrics={"records": len(documents), "by_source": {d["label"]: d["records"] for d in databases(sources)}},
    )


COMBINED_MANIFEST_SCHEMA = "nexus.corpus-combined.v1"


def _harvest_rows(harvest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = _read_json(Path(harvest["rows_path"]))
    if not isinstance(rows, list) or not rows:
        raise AcceptCorpusRefused(f"the works of {harvest['run']} cannot be read ({harvest['rows_path']})")
    return rows


def _harvest_databases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return _leg_rows(list(manifest.get("legs") or []))


def _materialise_combined(ws: Path, harvest: dict[str, Any]) -> Any:
    """Write the combined ``verified.json`` and manifest: the harvest's rows, then the staged records (M3f).

    The order is fixed by the parts, never by what the researcher did first,
    so the same parts give the same ``run_id`` and artifact id. The harvest's
    own file is copied to its run folder first (kept for good). Returns the
    function that puts both files back as they were, for a refused gate.
    """
    from .workspace.atomic import atomic_write_text

    sources, staged = _staged_rows(ws)
    harvest_rows = _harvest_rows(harvest)
    verified = ws / "literature" / "verified.json"
    manifest_path = ws / MANIFEST_FILE
    restore = _restorer(ws)
    own = Path(harvest["run_dir"]) / "verified.json"
    if not own.is_file():
        atomic_write_text(own, json.dumps(harvest_rows, indent=2))
    legs = _harvest_databases(harvest["manifest"])
    fetched = sum(int(row["records"]) for row in legs)
    manifest = {
        "schema": COMBINED_MANIFEST_SCHEMA,
        "total_raw_harvested": fetched + len(staged),
        "harvest": {
            "run": harvest["run"], "identified": fetched, "works": len(harvest_rows),
            "query_text": harvest["manifest"].get("query_text"), "databases": legs,
            "stored_as": own.relative_to(ws).as_posix(),
        },
        "sources": _manifest_sources(sources),
        "databases": databases(sources),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(verified, json.dumps([*harvest_rows, *staged], indent=2))
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2))
    return restore


def _restorer(ws: Path) -> Any:
    """A function that puts ``verified.json`` and the provenance manifest back as they are now."""
    paths = (ws / "literature" / "verified.json", ws / MANIFEST_FILE)
    before = {path: path.read_bytes() if path.is_file() else None for path in paths}

    def restore() -> None:
        for path, content in before.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)

    return restore


#: ``(workspace, input file stamps, preview)`` of the last ``corpus_preview``; the screens read it on every poll.
_PREVIEW_CACHE: list[Any] = [None]


def _stamp(paths: list[Path]) -> tuple[Any, ...]:
    out = []
    for path in paths:
        try:
            stat = path.stat()
            out.append((str(path), stat.st_mtime_ns, stat.st_size))
        except OSError:
            out.append((str(path), None, None))
    return tuple(out)


def row_sources(row: dict[str, Any]) -> set[tuple[str, str]]:
    """Where one ``verified.json`` row came from: ``{(name, kind)}``, kind ``search`` or ``import``."""
    if row.get("source_database"):
        return {(str(row["source_database"]), "import")}
    names = {str(s.get("provider")) for s in (row.get("sources") or []) if isinstance(s, dict) and s.get("provider")}
    if not names and row.get("provider") and row.get("provider") != "unknown":
        names = {str(row["provider"])}
    return {(name, "search") for name in names}


def _works_of(ws: Path, rows: list[dict[str, Any]]) -> tuple[list[list[dict[str, Any]]], list[dict[str, Any]]]:
    """The works the snapshot builder would make of ``rows``: each work's rows, and its representative's row."""
    documents = [_rebuild_doc(row, f"SCI-{i:06d}") for i, row in enumerate(rows, start=1)]
    index = {id(document): i for i, document in enumerate(documents)}
    clusters = _deduplicator(ws).deduplicate(documents)
    works = [[rows[index[id(member)]] for member in cluster.members] for cluster in clusters]
    return works, [rows[index[id(cluster.representative)]] for cluster in clusters]


def corpus_preview(workspace: Path | str) -> dict[str, Any] | None:
    """The corpus the accept would build now from the staged exports and the harvest part (M3f).

    ``None`` when nothing is staged (a harvest alone keeps its own view).
    Nothing is written. ``identified`` counts what each source returned (the
    harvest's records fetched per leg, every staged record), ``duplicates`` =
    identified - works, as PRISMA reads them after the accept. ``works`` holds
    each work's rows and ``representatives`` its representative's row, from
    the same deduplication the accept runs.
    """
    ws = Path(workspace).resolve()
    sources = staged_sources(ws)
    if not sources:
        return None
    harvest = harvest_part(ws)
    paths = [ws / SOURCES_FILE, ws / "protocol.json", ws / "literature" / "verified.json", ws / MANIFEST_FILE]
    if harvest is not None:
        paths += [Path(harvest["run_dir"]) / name for name in ("legs.json", "pipeline.json", "verified.json")]
    key = _stamp(paths)
    cached = _PREVIEW_CACHE[0]
    if cached is not None and cached[0] == str(ws) and cached[1] == key:
        return cached[2]
    included = harvest is not None and harvest["included"]
    harvest_rows = _harvest_rows(harvest) if included else []
    _, staged = _staged_rows(ws)
    works, representatives = _works_of(ws, [*harvest_rows, *staged])
    fetched = sum(int(row["records"]) for row in _harvest_databases(harvest["manifest"])) if included else 0
    identified = fetched + len(staged)
    value = {
        "harvest": harvest,
        "identified": identified,
        "duplicates": max(0, identified - len(works)),
        "unique_studies": len(works),
        "imported": len(staged),
        "works": works,
        "representatives": representatives,
    }
    _PREVIEW_CACHE[0] = (str(ws), key, value)
    return value


def combined_counts(workspace: Path | str) -> dict[str, int] | None:
    """``{identified, duplicates, unique_studies}`` of a corpus built from a harvest and exports, else ``None``.

    Before the accept: the preview, only when a ready harvest is included with
    the staged exports. After it: the combined manifest (what was fetched and
    imported) and the first accepted snapshot (round 1, also after an M3g
    chase round replaced ``verified.json``). Review F2: decided by the parts,
    not by ``origin``, which says ``imports`` when an unfinished harvest was
    left out and ``citation_searching`` in a chase round.
    """
    ws = Path(workspace).resolve()
    if not _accepted_snapshot(ws):
        harvest = harvest_part(ws)
        if not staged_sources(ws) or harvest is None or not harvest["included"]:
            return None
        preview = corpus_preview(ws)
        return {k: preview[k] for k in ("identified", "duplicates", "unique_studies")}
    manifest = _manifest(ws) or {}
    if manifest.get("schema") != COMBINED_MANIFEST_SCHEMA:
        return None
    registry = _read_json(ws / "audit" / "artifact_registry.json") or {}
    corpora = sorted(
        (e for e in (registry.get("artifacts") or {}).values() if e.get("artifact_type") == "corpus_snapshot"),
        key=lambda e: str(e.get("accepted_at") or ""),
    )
    artifact = _read_json(ws / corpora[0]["path"]) if corpora else None
    if not isinstance(artifact, dict):
        return None
    studies = len(artifact["data"]["studies"])
    identified = int(manifest.get("total_raw_harvested") or 0)
    return {"identified": identified, "duplicates": max(0, identified - studies), "unique_studies": studies}


def corpus_works(workspace: Path | str) -> tuple[list[list[dict[str, Any]]], list[dict[str, Any]]] | None:
    """The works screening will receive, each as its rows, and their representatives (M3f, finding 27).

    Before the accept, when exports are staged: the combined preview's works.
    After the accept of a corpus built from exports (alone or with a harvest):
    the snapshot's studies, each with the ``verified.json`` rows of its records.
    ``None`` otherwise (a harvest alone counts its ``verified.json`` rows,
    which are already works).
    """
    ws = Path(workspace).resolve()
    if not _accepted_snapshot(ws):
        preview = corpus_preview(ws)
        return None if preview is None else (preview["works"], preview["representatives"])
    if not _imported(ws):
        return None
    registry = _read_json(ws / "audit" / "artifact_registry.json") or {}
    corpora = sorted(
        (e for e in (registry.get("artifacts") or {}).values() if e.get("artifact_type") == "corpus_snapshot"),
        key=lambda e: str(e.get("accepted_at") or ""),
    )
    artifact = _read_json(ws / corpora[-1]["path"]) if corpora else None
    rows = _read_json(ws / "literature" / "verified.json")
    if not isinstance(artifact, dict) or not isinstance(rows, list):
        return None
    by_id = {row.get("workspace_id"): row for row in rows if isinstance(row, dict)}
    pairs = [
        ([by_id[a] for a in study.get("alias_ids") or [] if a in by_id],
         {"title": study.get("title"), "year": study.get("publication_year")})
        for study in artifact["data"]["studies"]
    ]
    pairs = [(work, representative) for work, representative in pairs if work]
    # Review F7: the representative is the builder's (the study's title and year), as before the accept.
    return [work for work, _ in pairs], [representative for _, representative in pairs]


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
    restore = None
    harvest: dict[str, Any] | None = None
    left_out: dict[str, Any] | None = None
    if not _accepted_snapshot(ws):
        if staged_sources(ws):
            harvest = harvest_part(ws)
            if harvest is not None and harvest["included"]:
                # M3f: the harvest part and the staged exports, deduplicated together.
                # The accept binds the run's works to the current protocol (M3d review F3).
                refuse_if_run_protocol_changed(ws, harvest["manifest"])
                if provider_warnings is None:
                    provider_warnings = failed_leg_warnings(harvest["manifest"])
                restore = _materialise_combined(ws, harvest)
            else:
                # M3i item 10, kept: an unfinished harvest is never frozen; the
                # exports are accepted alone and the result names what was left out.
                if harvest is not None:
                    left_out = {"run": harvest["run"], "state": harvest["state"]}
                harvest = None
                restore = _restorer(ws)
                _materialise_staged(ws, left_out=left_out)
        elif _imported(ws):
            raise AcceptCorpusRefused(
                "every database file was removed; add at least one before accepting",
                "NOTHING_STAGED",
            )

    try:
        result = _freeze_rows(
            ws, workspace_id=workspace_id, fingerprint=fingerprint, deduplicator=deduplicator,
            now=now, provider_warnings=provider_warnings,
        )
    except BaseException:
        # Compass §7: a refused gate publishes nothing and leaves the harvest part as it was.
        if restore is not None:
            restore()
        raise
    if harvest is not None and not result.already_accepted:
        sources = staged_sources(ws)
        append_event(
            ws,
            "CORPUS_COMBINED",
            f"Combined the works of {harvest['run']} with {sum(int(s['records']) for s in sources)} records "
            f"from {len(sources)} export file(s) into literature/verified.json",
            inputs=[Path(harvest["run_dir"]).relative_to(ws).as_posix() + "/verified.json",
                    *[s["stored_as"] for s in sources]],
            outputs=["literature/verified.json", MANIFEST_FILE.as_posix()],
            parameters={"run": harvest["run"], "sources": [s["id"] for s in sources],
                        "artifact_id": result.artifact_id},
            metrics={"records": result.record_count, "studies": result.study_count},
        )
    return replace(result, combined_run=harvest["run"] if harvest is not None else None, left_out=left_out)


def _freeze_rows(
    ws: Path,
    *,
    workspace_id: str,
    fingerprint: str,
    deduplicator: Deduplicator,
    now: datetime | None,
    provider_warnings: list[str] | None,
) -> AcceptCorpusResult:
    """Build the snapshot from ``verified.json`` and pass it through the acceptance gate."""
    if not _accepted_snapshot(ws) and not _imported(ws):
        # H-quota-hang review F2: a search run's corpus is frozen only once its
        # preparation ended, also from the CLI (``accept-corpus``), as on the
        # hand-off. An ``incomplete`` run has its own verified.json with records
        # that were not checked; a failed or stopped run may leave an earlier
        # run's file in place.
        refuse_if_preparation_unfinished(ws)

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
