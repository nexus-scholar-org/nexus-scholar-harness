"""The kept records of every published round (M12a DoD 1 and 2).

A row of the charting table is a record published as Include or as Unclear →
full text (``MAYBE``) in ``included.json``: the current round's file under
``literature/`` and each archived round's copy under
``literature/screening_rounds/round_NNN/`` (M3g). Nothing is read from
unpublished decisions (decision 2026-11-21, M12a item 4).

The current round counts as published when its generation is CURRENT or
STALE (decisions changed after publishing: the table follows the published
files and says so). While a citation-chasing round is being screened, the
archived rounds are shown and ``chasing_pending`` is set. With no published
round at all the table refuses ``SCREENING_NOT_PUBLISHED``.

``charting/kept_history.jsonl`` remembers each published kept set the table
has seen (one row per round and generation, written the first time it is
read), because a re-publication overwrites ``included.json``. From it a
record that left the kept set is marked ``no_longer_kept`` and a record that
joined is marked ``new_since`` with that publication's date.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import CHARTING_DIR, ChartingRefused
from .lock import LockBusy, locked

HISTORY_FILE = CHARTING_DIR / "kept_history.jsonl"
KEPT_DECISIONS = ("INCLUDE", "MAYBE")
SCREENING_NOT_PUBLISHED = "SCREENING_NOT_PUBLISHED"
CHARTING_PROTOCOL_REPLACED = "CHARTING_PROTOCOL_REPLACED"
#: The statuses under which the current round's published files are read.
READABLE = ("CURRENT", "STALE")


@dataclass(frozen=True)
class KeptRecord:
    """One kept record as published, with the round it came from."""

    study_id: str
    round: int
    arm: str
    generation_id: str
    ta_decision: str
    ta_reason: str
    title: str
    authors: tuple[str, ...]
    year: int | None
    venue: str | None
    doi: str | None
    url: str | None
    abstract: str | None
    arxiv_id: str | None


@dataclass
class Source:
    """One published round: where its kept records are and which generation published them."""

    round: int
    arm: str
    included: Path
    generation: Path
    generation_id: str
    published_at: str | None
    protocol_fingerprint: str | None
    generation_sha256: str | None
    #: The digest the publication recorded for ``included.json`` (``sha256:<hex>``).
    included_digest: str | None = None


@dataclass
class KeptState:
    records: list[KeptRecord]
    sources: list[Source]
    publication: dict[str, Any]
    chasing_pending: bool
    no_longer_kept: dict[str, dict[str, Any]] = field(default_factory=dict)
    new_since: dict[str, str] = field(default_factory=dict)
    changes: dict[str, Any] | None = None

    @property
    def kept_ids(self) -> set[str]:
        return {r.study_id for r in self.records}


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _authors(value: Any) -> tuple[str, ...]:
    names: list[str] = []
    for author in value if isinstance(value, list) else []:
        if isinstance(author, str) and author.strip():
            names.append(author.strip())
        elif isinstance(author, dict):
            name = _text(author.get("name")) or " ".join(
                p for p in (_text(author.get("given_name")), _text(author.get("family_name"))) if p
            )
            if name:
                names.append(name)
    return tuple(names)


def _year(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def study_id_of(entry: dict[str, Any]) -> str:
    """The record's study id (the published shape names it ``workspace_id``)."""
    return str(entry.get("study_id") or entry.get("workspace_id") or "")


def _record(entry: dict[str, Any], source: Source) -> KeptRecord | None:
    screening = entry.get("screening") if isinstance(entry.get("screening"), dict) else {}
    decision = str(screening.get("decision") or "").upper()
    study_id = study_id_of(entry)
    if decision not in KEPT_DECISIONS or not study_id:
        return None
    ids = entry.get("external_ids") if isinstance(entry.get("external_ids"), dict) else {}
    reason = _text(screening.get("note")) or _text(screening.get("screening_reasoning")) or _text(screening.get("reason"))
    return KeptRecord(
        study_id=study_id,
        round=source.round,
        arm=source.arm,
        generation_id=source.generation_id,
        ta_decision=decision,
        ta_reason=reason or "",
        title=_text(entry.get("title")) or "",
        authors=_authors(entry.get("authors")),
        year=_year(entry.get("year")),
        venue=_text(entry.get("venue")),
        doi=_text(ids.get("doi")) or _text(entry.get("doi")),
        url=_text(entry.get("url")),
        abstract=_text(entry.get("abstract")),
        arxiv_id=_text(ids.get("arxiv_id")),
    )


def _generation(path: Path) -> tuple[dict[str, Any], str] | None:
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
    except (OSError, ValueError):
        return None
    return (data, hashlib.sha256(raw).hexdigest()) if isinstance(data, dict) else None


def _source(number: int, arm: str, included: Path, generation: Path) -> Source | None:
    if not included.is_file():
        return None
    found = _generation(generation)
    data, digest = found if found else ({}, None)
    outputs = data.get("outputs") if isinstance(data.get("outputs"), dict) else {}
    return Source(
        round=number,
        arm=arm,
        included=included,
        generation=generation,
        generation_id=str(data.get("generation_id") or ""),
        published_at=_text(data.get("published_at")),
        protocol_fingerprint=_text(data.get("protocol_fingerprint")),
        generation_sha256=digest,
        included_digest=_text(outputs.get("included.json")),
    )


def _sources(ws: Path) -> tuple[list[Source], dict[str, Any], bool]:
    """The published rounds, the current round's publication status, and whether a chase round is pending."""
    from scholar_harness.screening import rounds
    from scholar_harness.screening.currentness import screening_currentness

    found: list[Source] = []
    for previous in rounds.previous_rounds(ws):
        folder = ws / str(previous.get("path") or rounds.round_folder(ws, int(previous.get("round") or 0)).relative_to(ws))
        source = _source(
            int(previous.get("round") or 0), str(previous.get("arm") or rounds.ARM_DATABASES),
            folder / "included.json", folder / "screening" / "generation.json",
        )
        if source is not None:
            found.append(source)
    current = rounds.current_round(ws)
    number, arm = int(current.get("round") or 1), str(current.get("arm") or rounds.ARM_DATABASES)
    result = screening_currentness(ws)
    status = result.status.value
    publication = {
        "round": number, "arm": arm, "status": status, "code": result.code,
        "generation_id": result.record.generation_id if result.record is not None else None,
        "published_at": result.record.published_at if result.record is not None else None,
    }
    included = ws / "literature" / "included.json"
    pending = False
    if status in READABLE and result.record is not None:
        source = _source(number, arm, included, ws / "literature" / "screening" / "generation.json")
        if source is not None:
            source.included_digest = result.record.output_digests.get("included.json")
            found.append(source)
    elif number > 1 and not included.is_file() and found:
        pending = True  # a chased round is being screened; earlier rounds stay readable
    elif included.is_file():
        # Review of Part A, follow-up: a current round whose publication is neither
        # current nor stale refuses the table, rather than showing its rows as left.
        raise ChartingRefused(
            409, SCREENING_NOT_PUBLISHED,
            "The screening publication cannot be read as published now. Publish it again.",
            publication=publication,
        )
    return found, publication, pending


def _read_history(ws: Path) -> list[dict[str, Any]]:
    path = ws / HISTORY_FILE
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _summary(record: KeptRecord) -> dict[str, Any]:
    return {"title": record.title, "year": record.year, "doi": record.doi, "round": record.round,
            "arm": record.arm, "ta_decision": record.ta_decision}


def _remember(ws: Path, sources: list[Source], by_source: dict[int, list[KeptRecord]]) -> list[dict[str, Any]]:
    """Append one history row for each round whose current generation the table has not seen yet."""
    with locked(ws / CHARTING_DIR / ".lock"):
        history = _read_history(ws)
        seen = {(int(r.get("round") or 0), str(r.get("generation_id") or "")) for r in history}
        fresh = [s for s in sources if (s.round, s.generation_id) not in seen]
        if fresh:
            path = ws / HISTORY_FILE
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                for source in fresh:
                    row = {
                        "schema": "nexus.charting-kept-history.v1",
                        "round": source.round,
                        "generation_id": source.generation_id,
                        "published_at": source.published_at,
                        "seen_at": _now(),
                        "kept": {r.study_id: _summary(r) for r in by_source.get(source.round, [])},
                    }
                    handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
                    history.append(row)
        return history


def read_kept(ws: Path | str, *, remember: bool = True) -> KeptState:
    """Every kept record of every published round, with what left and joined since the table first saw them."""
    ws = Path(ws)
    sources, publication, pending = _sources(ws)
    if not sources:
        raise ChartingRefused(
            409, SCREENING_NOT_PUBLISHED,
            "Screening is not published yet. The charting table lists the studies you kept, so publish first.",
            publication=publication,
        )
    records: list[KeptRecord] = []
    by_source: dict[int, list[KeptRecord]] = {}
    seen_ids: set[str] = set()
    for source in sorted(sources, key=lambda s: s.round):
        try:
            raw = source.included.read_bytes()
            rows = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError) as exc:
            raise ChartingRefused(
                409, SCREENING_NOT_PUBLISHED,
                f"The published file {source.included.relative_to(ws).as_posix()} cannot be read ({type(exc).__name__}).",
                publication=publication,
            ) from exc
        _require_published_bytes(ws, source, raw, publication)
        for entry in rows if isinstance(rows, list) else []:
            record = _record(entry, source) if isinstance(entry, dict) else None
            if record is None or record.study_id in seen_ids:
                continue  # one study in two rounds is impossible by construction (M3g); first round wins
            seen_ids.add(record.study_id)
            records.append(record)
            by_source.setdefault(source.round, []).append(record)
    state = KeptState(records=records, sources=sources, publication=publication, chasing_pending=pending)
    try:
        history = _remember(ws, sources, by_source) if remember else _read_history(ws)
    except LockBusy:
        history = _read_history(ws)  # review finding 7: a busy lock reads, never fails the table
    _mark_changes(state, history)
    return state


def _require_published_bytes(ws: Path, source: Source, raw: bytes, publication: dict[str, Any]) -> None:
    """Read only the bytes the publication recorded (review of Part A, finding 1).

    A STALE generation can mean "a decision changed after publishing" (the
    published files are intact) or "an output no longer matches its digest";
    an archived round is never checked by the gate. Each source's
    ``included.json`` must equal the digest its own ``generation.json``
    recorded, else the table refuses.
    """
    from scholar_harness.authority.binding import content_sha256

    if source.included_digest and content_sha256(raw) == source.included_digest:
        return
    rel = source.included.relative_to(ws).as_posix()
    raise ChartingRefused(
        409, SCREENING_NOT_PUBLISHED,
        f"{rel} is not the file round {source.round}'s publication recorded. Publish the screening again.",
        publication=publication, file=rel, round=source.round,
    )


def _mark_changes(state: KeptState, history: list[dict[str, Any]]) -> None:
    """``no_longer_kept``: kept in an earlier generation the table saw, not now. ``new_since``: joined after the first."""
    current = {(s.round, s.generation_id) for s in state.sources}
    first_seen: dict[str, dict[str, Any]] = {}
    last_seen: dict[str, dict[str, Any]] = {}
    for row in history:
        for study_id, summary in (row.get("kept") or {}).items():
            first_seen.setdefault(study_id, row)
            last_seen[study_id] = {**summary, "generation_id": row.get("generation_id"), "round": row.get("round")}
    rounds_first = {}
    for row in history:
        rounds_first.setdefault(int(row.get("round") or 0), row)
    kept = state.kept_ids
    for study_id, summary in last_seen.items():
        if study_id not in kept:
            state.no_longer_kept[study_id] = summary
    for record in state.records:
        first = first_seen.get(record.study_id)
        opening = rounds_first.get(record.round)
        if first is not None and opening is not None and first is not opening and first.get("published_at"):
            state.new_since[record.study_id] = str(first["published_at"])
    latest = [row for row in history if (int(row.get("round") or 0), str(row.get("generation_id") or "")) in current]
    if latest:
        newest = max(latest, key=lambda r: str(r.get("published_at") or ""))
        added = sum(1 for sid, at in state.new_since.items() if at == newest.get("published_at"))
        if added or state.no_longer_kept:
            state.changes = {
                "published_at": newest.get("published_at"),
                "added": added,
                "no_longer_kept": len(state.no_longer_kept),
            }


def protocol_replaced(ws: Path, state: KeptState) -> bool:
    """True when the current protocol is not the one the newest published round was screened under."""
    from scholar_harness.corpus_accept import AcceptCorpusRefused, _protocol_fingerprint

    newest = max(state.sources, key=lambda s: s.round)
    if not newest.protocol_fingerprint:
        return False
    try:
        return _protocol_fingerprint(ws) != newest.protocol_fingerprint
    except AcceptCorpusRefused:
        return True


def as_dict(record: KeptRecord) -> dict[str, Any]:
    data = asdict(record)
    data["authors"] = list(record.authors)
    return data
