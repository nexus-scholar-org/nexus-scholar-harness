"""Decision export and the methods paragraph of a published screening (spec 10).

Both read the **published** generation only: `generation.json` and the files
it commits, checked by `require_current_generation`, plus the decision files
the generation was collected from. Nothing here writes a file or a journal row.

Currentness has two parts:

* `require_current_generation` (authority layer): the published files match
  their recorded digests, the approval still resolves, the protocol is
  unchanged. It does **not** look at decisions made after publication: the
  generation binds the batch files, not the decision files, so a new decision
  event leaves it CURRENT.
* `_check_decisions_unchanged` (here): the decision event log still projects
  to the decision files (`stale_projections`), and the decision files still
  say what the published records say (same studies, outcomes, reasons and
  reason counts). A decision made after publication fails one of the two and
  is refused `GENERATION_STALE`.

The reason code of an excluded record is not always in `excluded.json` (an
exclusion that fails an inclusion criterion, `FAILS-INC-01`, has no violated
exclusion criterion, and its `screening_reasoning` is the note when there is
one). It is read from the decision files, which the check above has tied to
the published records, never from live events.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.authority.binding import content_sha256
from scholar_harness.authority.generations import (
    GENERATION_FILENAME,
    GENERATION_STALE,
    GenerationRecord,
    GenerationStatus,
    require_current_generation,
)
from scholar_harness.screening import events as ev
from scholar_harness.screening import proposals as pr

EXPORT_NOT_PUBLISHED = "EXPORT_NOT_PUBLISHED"
EXPORT_FORMAT_INVALID = "EXPORT_FORMAT_INVALID"
EXPORT_SOURCE_MISMATCH = "EXPORT_SOURCE_MISMATCH"
METHODS_SOURCE_MISSING = "METHODS_SOURCE_MISSING"

FORMATS = ("ris", "csv")
SETS = ("included", "unclear", "excluded")
DEFAULT_SETS = {"ris": ("included", "unclear"), "csv": ("included", "unclear", "excluded")}
CSV_COLUMNS = (
    "study_id", "decision", "reason_code", "title", "authors", "year", "venue", "doi", "url", "abstract",
    "generation_id",
)
ROLE_WORDS = {"INCLUDE": "include", "MAYBE": "unclear", "EXCLUDE": "exclude"}
SET_OF = {"INCLUDE": "included", "MAYBE": "unclear", "EXCLUDE": "excluded"}

#: Reveal tracking (M1b-0, commit 7ef4d20) began at this instant. Events stored
#: before it carry `changed_after_reveal: false`, which for them means "not
#: tracked" (contract §3.1), so a change received earlier is never counted as
#: "not changed after a reveal".
REVEAL_TRACKING_SINCE = "2026-11-05T05:26:45Z"
#: Words the paragraph never contains (spec 10, decision 4). Tests pin it.
FORBIDDEN_WORDS = ("validated", "accurate", "recall", "agreement", "concordance", "kappa", "cost", "gate")

SETTINGS_ACTION = "SCREENING_SETTINGS_CHANGED"
JOURNAL_FILE = Path("audit") / "journal.jsonl"
DEFAULT_SETTINGS = {
    "blinding": "reveal_after_decision",
    "mode": "human_sees_every_record",
    "sample_audit_size": None,
    "queue_order": "seeded",
    "advance_on_decide": "show_draft_then_next",
}
ORDER_LABELS = {"seeded": "seeded random", "agent_uncertainty": "agent-uncertainty"}
NO_ABSTRACT = "No abstract available."


class ExportRefused(Exception):
    """A typed refusal; the route returns it as `{"detail": {code, message, ...}}`."""

    def __init__(self, status: int, code: str, message: str, **details: Any):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


@dataclass
class Published:
    record: GenerationRecord
    generation_bytes: bytes
    included: list[dict[str, Any]]
    excluded: list[dict[str, Any]]
    #: Decision-file entry per published study (the accepted decisions).
    entries: dict[str, dict[str, Any]]
    #: `(name, path, digest)` of each decision file read.
    decision_files: list[tuple[str, str, str]] = field(default_factory=list)
    event_sourced: bool = True


# --- the published generation ---------------------------------------------------


def _refuse_from_currentness(result: Any, *, purpose: str) -> ExportRefused:
    details = result.details or {}
    generation_id = details.get("generation_id")
    extra = {"generation_id": generation_id} if generation_id else {}
    if result.status is GenerationStatus.LEGACY_UNVERIFIED or (
        result.status is GenerationStatus.MISMATCHED and details.get("lineage_without_generation")
    ):
        return ExportRefused(409, EXPORT_NOT_PUBLISHED, "the screening is not published yet; approve and publish it first")
    output = details.get("output")
    if output:
        if purpose == "methods" and output == "prisma_report.json" and details.get("actual_digest") is None:
            return ExportRefused(
                409, METHODS_SOURCE_MISSING, "prisma_report.json is missing; the paragraph cannot state the PRISMA counts",
                missing="prisma_report.json", **extra,
            )
        return ExportRefused(
            409, EXPORT_SOURCE_MISMATCH,
            f"{output} no longer matches its recorded digest, so nothing was exported", output=output, **extra,
        )
    return ExportRefused(409, result.code or GENERATION_STALE, result.message, **extra)


def _read_json_output(ws: Path, record: GenerationRecord, name: str) -> Any:
    """Read a published file and re-check its digest against `generation.json`."""
    path = ws / "literature" / name
    try:
        raw = path.read_bytes()
    except OSError:
        raw = None
    if raw is None or content_sha256(raw) != record.output_digests[name]:
        raise ExportRefused(
            409, EXPORT_SOURCE_MISMATCH, f"{name} no longer matches its recorded digest, so nothing was exported",
            output=name, generation_id=record.generation_id,
        )
    return json.loads(raw.decode("utf-8"))


def _decision_entries(ws: Path, record: GenerationRecord) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str, str]], bool]:
    screening = ws / "literature" / "screening"
    entries: dict[str, dict[str, Any]] = {}
    files: list[tuple[str, str, str]] = []
    event_sourced = True
    for binding in record.batch_bindings:
        name = f"batch_{int(binding['batch_index']):03d}_decisions.json"
        path = screening / name
        try:
            raw = path.read_bytes()
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError) as exc:
            raise ExportRefused(
                409, GENERATION_STALE, f"{name} cannot be read, so the published decisions cannot be confirmed ({exc})",
                generation_id=record.generation_id,
            ) from exc
        files.append((name, f"literature/screening/{name}", content_sha256(raw)))
        if not (isinstance(payload, dict) and payload.get("source") == "decision-events"):
            event_sourced = False
        for entry in (payload.get("decisions") if isinstance(payload, dict) else None) or []:
            if isinstance(entry, dict):
                entries[str(entry.get("workspace_id") or entry.get("study_id") or "")] = entry
    return entries, files, event_sourced


def _entry_code(entry: dict[str, Any]) -> str | None:
    violated = entry.get("violated_exclusion_criteria") or []
    if violated:
        return str(violated[0])
    return str(entry["reason_code"]) if entry.get("reason_code") else None


def _check_decisions_unchanged(
    ws: Path, record: GenerationRecord, published: list[dict[str, Any]], entries: dict[str, dict[str, Any]],
    prisma: dict[str, Any] | None,
) -> None:
    """Refuse `GENERATION_STALE` when a decision changed after publication."""
    stale = ev.stale_projections(ws)
    if stale:
        raise ExportRefused(
            409, GENERATION_STALE,
            "the screening changed after it was published (the decision events differ from the decisions files); "
            "publish again before you export",
            generation_id=record.generation_id, batches=stale,
        )
    changed: list[str] = []
    seen: set[str] = set()
    for item in published:
        screening = item.get("screening") or {}
        study = str(screening.get("workspace_id") or item.get("workspace_id") or "")
        seen.add(study)
        entry = entries.get(study)
        if entry is None or str(entry.get("decision")) != str(screening.get("decision")):
            changed.append(study)
            continue
        if "screening_reasoning" in entry and str(entry["screening_reasoning"]) != str(screening.get("screening_reasoning")):
            changed.append(study)
            continue
        violated = list(screening.get("violated_exclusion_criteria") or [])
        if violated and _entry_code(entry) not in violated:
            changed.append(study)
    changed.extend(sorted(set(entries) - seen))
    if not changed and prisma is not None:
        counts: Counter[str] = Counter()
        for item in published:
            screening = item.get("screening") or {}
            if screening.get("decision") != "EXCLUDE":
                continue
            entry = entries[str(screening.get("workspace_id") or item.get("workspace_id"))]
            for code in screening.get("violated_exclusion_criteria") or [_entry_code(entry) or "UNSPECIFIED"]:
                counts[str(code)] += 1
        if dict(counts) != dict(prisma.get("exclusion_reasons_breakdown") or {}):
            changed.append("exclusion_reasons_breakdown")
    if changed:
        raise ExportRefused(
            409, GENERATION_STALE,
            "the screening changed after it was published; publish again before you export",
            generation_id=record.generation_id, changed=len(changed),
        )


def load_published(ws: Path, *, purpose: str) -> tuple[Published, dict[str, Any] | None]:
    """The CURRENT published generation, or a typed refusal. Pure read."""
    ws = Path(ws)
    result = require_current_generation(ws)
    if result.status is not GenerationStatus.CURRENT or result.record is None:
        raise _refuse_from_currentness(result, purpose=purpose)
    record = result.record
    try:
        generation_bytes = (ws / "literature" / "screening" / GENERATION_FILENAME).read_bytes()
    except OSError as exc:
        raise ExportRefused(409, GENERATION_STALE, f"generation.json cannot be read ({exc})") from exc
    included = _read_json_output(ws, record, "included.json")
    excluded = _read_json_output(ws, record, "excluded.json")
    prisma: dict[str, Any] | None = None
    try:
        prisma = _read_json_output(ws, record, "prisma_report.json")
    except ExportRefused:
        if purpose == "methods":
            raise
    entries, files, event_sourced = _decision_entries(ws, record)
    if event_sourced:
        _check_decisions_unchanged(ws, record, list(included) + list(excluded), entries, prisma)
    view = Published(record, generation_bytes, list(included), list(excluded), entries, files, event_sourced)
    return view, prisma


# --- export -----------------------------------------------------------------------


def parse_request(fmt: str, sets: str | None) -> tuple[str, tuple[str, ...]]:
    fmt = (fmt or "").strip().lower()
    if fmt not in FORMATS:
        raise ExportRefused(422, EXPORT_FORMAT_INVALID, f"format must be one of {FORMATS}", format=fmt)
    if sets is None:
        return fmt, DEFAULT_SETS[fmt]
    names = [s.strip().lower() for s in sets.split(",") if s.strip()]
    unknown = sorted(set(names) - set(SETS))
    if not names or unknown:
        raise ExportRefused(422, EXPORT_FORMAT_INVALID, f"set names one or more of {SETS}", unknown=unknown)
    return fmt, tuple(s for s in SETS if s in names)


def _clean(value: Any) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def _authors(item: dict[str, Any]) -> list[str]:
    out = []
    for author in item.get("authors") or []:
        if isinstance(author, dict):
            family, given = _clean(author.get("family_name")), _clean(author.get("given_name"))
        else:
            family, given = _clean(author), ""
        if family:
            out.append(f"{family}, {given}" if given else family)
    return out


def _doi(item: dict[str, Any]) -> str:
    ids = item.get("external_ids") if isinstance(item.get("external_ids"), dict) else {}
    return _clean(ids.get("doi") or item.get("doi") or (item.get("screening") or {}).get("doi"))


def _abstract(item: dict[str, Any]) -> str:
    text = _clean(item.get("abstract"))
    return "" if text == NO_ABSTRACT else text


def _rows(view: Published, sets: tuple[str, ...]) -> list[dict[str, str]]:
    rows = []
    for item in view.included + view.excluded:
        screening = item.get("screening") or {}
        decision = str(screening.get("decision") or "")
        if SET_OF.get(decision) not in sets:
            continue
        study = _clean(screening.get("workspace_id") or item.get("workspace_id"))
        reason = ""
        if decision == "EXCLUDE":
            violated = screening.get("violated_exclusion_criteria") or []
            entry = view.entries.get(study) or {}
            reason = _clean(violated[0] if violated else (_entry_code(entry) or screening.get("screening_reasoning")))
            reason = reason or "UNSPECIFIED"
        rows.append({
            "study_id": study,
            "outcome": decision,
            "decision": ROLE_WORDS.get(decision, decision.lower()),
            "reason_code": reason,
            "title": _clean(item.get("title") or screening.get("document_title")),
            "authors": "; ".join(_authors(item)),
            "_authors": _authors(item),  # type: ignore[dict-item]
            "year": _clean(item.get("year")),
            "venue": _clean(item.get("venue")),
            "doi": _doi(item),
            "url": _clean(item.get("url")),
            "abstract": _abstract(item),
            "generation_id": view.record.generation_id,
        })
    order = {name: i for i, name in enumerate(SETS)}
    return sorted(rows, key=lambda r: order[SET_OF[r["outcome"]]])


def render_ris(rows: list[dict[str, Any]]) -> bytes:
    lines: list[str] = []
    for row in rows:
        lines.append("TY  - JOUR")

        def tag(name: str, value: str) -> None:
            if value:
                lines.append(f"{name}  - {value}")

        tag("TI", row["title"])
        for author in row["_authors"]:
            tag("AU", author)
        tag("PY", row["year"])
        tag("T2", row["venue"])
        tag("DO", row["doi"])
        tag("UR", row["url"])
        tag("AB", row["abstract"])
        tag("ID", row["study_id"])
        note = f"Screening: {row['outcome']}"
        if row["reason_code"]:
            note += f"; reason: {row['reason_code']}"
        tag("N1", f"{note}; generation {row['generation_id']}")
        lines.append("ER  - ")
        lines.append("")
    return "\r\n".join(lines).encode("utf-8")  # UTF-8, no BOM


def render_csv(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        writer.writerow([row[c] for c in CSV_COLUMNS])
    return ("﻿" + buffer.getvalue()).encode("utf-8")  # UTF-8 with BOM, CRLF


def _slug(ws: Path) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", ws.name).strip("-.") or "workspace"


def build_export(ws: Path, fmt: str, sets: str | None) -> tuple[bytes, str, str]:
    """`(bytes, filename, media type)` for one export of the published screening."""
    fmt, chosen = parse_request(fmt, sets)
    view, _prisma = load_published(ws, purpose="export")
    rows = _rows(view, chosen)
    body = render_ris(rows) if fmt == "ris" else render_csv(rows)
    filename = f"{_slug(Path(ws))}-screening-{view.record.generation_id}-{'+'.join(chosen)}.{fmt}"
    media = "application/x-research-info-systems" if fmt == "ris" else "text/csv; charset=utf-8"
    return body, filename, media


# --- methods paragraph --------------------------------------------------------------


def _time(value: Any) -> datetime | None:
    """An aware instant (UTC assumed when the text names no zone), or None."""
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _date(value: Any) -> str:
    parsed = _time(value)
    return parsed.date().isoformat() if parsed else str(value)[:10]


def _journal(ws: Path) -> list[dict[str, Any]] | None:
    path = ws / JOURNAL_FILE
    if not path.is_file():
        return None
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _settings_now(ws: Path, method: Any = None) -> dict[str, Any]:
    path = ws / "literature" / "screening" / "settings.json"
    try:
        stored = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (OSError, ValueError):
        stored = {}
    settings = {**DEFAULT_SETTINGS, **(stored if isinstance(stored, dict) else {})}
    if method is not None and method.source == "protocol":
        settings["blinding"] = method.config.blinding  # set by the protocol (M7-method)
    return settings


def _dedup_sentence(dedup: Any) -> str:
    """Spec 10 amendment 2026-11-08: the dedup tiers in force, in words."""
    years = (
        "the same publication year"
        if dedup.year_tolerance == 0
        else f"publication years at most {dedup.year_tolerance} year{'s' if dedup.year_tolerance > 1 else ''} apart"
    )
    author = "the same first author and " if dedup.first_author else ""
    return (
        f"Duplicates across databases were removed by exact DOI and by title similarity of at least "
        f"{dedup.title_similarity:.2f} with {author}{years}."
    )


NOT_REPORTED_SENTENCES = {
    "unclear": "A criterion the title and abstract did not report sent the record to full-text assessment.",
    "exclude": "An inclusion criterion the title and abstract did not report excluded the record.",
}


@dataclass
class Timeline:
    initial: Any
    #: `(date, value)` for every recorded change up to publication.
    changes: list[tuple[str, Any]]
    at_publish: Any
    recorded: bool


def _timeline(rows: list[dict[str, Any]], key: str, published: datetime | None, now: Any) -> Timeline:
    history = []
    for row in rows:
        params = row.get("parameters") or {}
        after, before = params.get("after") or {}, params.get("before") or {}
        if key in after:
            history.append((_time(row.get("timestamp")), before.get(key), after[key], row.get("timestamp")))
    history.sort(key=lambda h: h[0] or datetime.min.replace(tzinfo=UTC))
    initial = history[0][1] if history else now
    # A row that leaves the value as it was is not a change (M6-beta, review U-2):
    # the paragraph says each real change once.
    changes, value = [], initial
    for h in history:
        if h[2] != value:
            changes.append(h)
            value = h[2]
    history = changes
    upto = [h for h in history if published is None or h[0] is None or h[0] <= published]
    at_publish = upto[-1][2] if upto else initial
    return Timeline(initial, [(_date(h[3]), h[2]) for h in upto], at_publish, bool(upto))


def _published_events(ws: Path, view: Published, published: datetime | None) -> dict[str, list[dict[str, Any]]]:
    """Current-generation events of the published studies, up to publication."""
    context = ev.load_context(ws)
    screeners = {str(e.get("screener_id")) for e in view.entries.values() if e.get("screener_id")}
    out: dict[str, list[dict[str, Any]]] = {}
    for event in ev.current_events(ev.read_events(ws), context):
        received = _time(event.get("received_at"))
        if event.get("study_id") not in view.entries or (screeners and event.get("screener_id") not in screeners):
            continue
        if published is not None and received is not None and received > published:
            continue
        out.setdefault(str(event["study_id"]), []).append(event)
    return out


def build_methods(ws: Path) -> dict[str, Any]:
    """The methods paragraph of the published screening. Pure read."""
    ws = Path(ws)
    view, prisma = load_published(ws, purpose="methods")
    if not isinstance(prisma, dict):
        raise ExportRefused(409, METHODS_SOURCE_MISSING, "prisma_report.json is missing", missing="prisma_report.json")
    record = view.record
    published = _time(record.published_at)
    caveats: list[str] = []
    not_stated: list[str] = []
    sources: list[dict[str, Any]] = [
        {"name": "generation.json", "path": "literature/screening/generation.json",
         "digest": content_sha256(view.generation_bytes)},
        *[
            {"name": name, "path": f"literature/{name}", "digest": record.output_digests[name]}
            for name in ("prisma_report.json", "included.json", "excluded.json")
        ],
        *[{"name": n, "path": p, "digest": d} for n, p, d in view.decision_files],
    ]

    def source(path: Path, *, digest: bool = True) -> bool:
        full = ws / path
        if not full.is_file():
            return False
        entry: dict[str, Any] = {"name": path.name, "path": str(path).replace("\\", "/")}
        if digest:
            entry["digest"] = content_sha256(full.read_bytes())
        sources.append(entry)
        return True

    try:
        figures_counts = {
            "identified": int(prisma["total_identified"]),
            "duplicates_removed": int(prisma["duplicates_removed"]),
            "screened": int(prisma["records_screened"]),
            "excluded": int(prisma["records_excluded"]),
            "unclear": int(prisma.get("records_unclear") or 0),
            "included": int(prisma["records_included"]),
        }
        reasons = {str(k): int(v) for k, v in (prisma.get("exclusion_reasons_breakdown") or {}).items()}
    except (KeyError, TypeError, ValueError) as exc:
        raise ExportRefused(
            409, METHODS_SOURCE_MISSING, f"prisma_report.json lacks a count the paragraph needs ({exc})",
            missing="prisma_report.json",
        ) from exc
    figures: dict[str, Any] = {**figures_counts, "exclusion_reasons": reasons}
    sentences: list[str] = []

    # 0. Databases (one RIS export per database, from accept-corpus or the Import screen)
    manifest_path = Path("literature") / "raw" / "provenance_manifest.json"
    if source(manifest_path):
        try:
            imported = json.loads((ws / manifest_path).read_text(encoding="utf-8")).get("sources") or []
        except ValueError:
            imported = []
            caveats.append("provenance_manifest.json cannot be read.")
        if imported:
            from ..corpus_accept import databases

            per_database = databases(imported)
            parts = [
                f"{d['label']} (n = {d['records']}"
                + (f", searched {' and '.join(d['searched_on'])}" if d["searched_on"] else "")
                + ")"
                for d in per_database
            ]
            listed = parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} and {parts[-1]}"
            sentences.append(f"Records were identified from {listed}.")
            figures["identified_by_source"] = [
                {"label": d["label"], "records": d["records"], "searched_on": d["searched_on"]}
                for d in per_database
            ]
            if any(not s.get("searched_on") for s in imported):
                not_stated.append("Date searched: not recorded for every database.")
            if any(not s.get("query") for s in imported):
                not_stated.append("Search string: not recorded for every database.")

    # 1. PRISMA
    c = figures_counts
    reason_text = f" ({', '.join(f'{k}: {v}' for k, v in sorted(reasons.items()))})" if reasons else ""
    sentences.append(
        f"{c['identified']} records were identified; {c['duplicates_removed']} duplicates were removed; "
        f"{c['screened']} records were screened; {c['excluded']} were excluded{reason_text}; "
        f"{c['unclear']} were unclear and went to full-text assessment; {c['included']} were included."
    )
    # M7-method: the dedup tiers in force (always stated; spec 10 amendment).
    from .method import MethodInvalid, effective_method

    try:
        method = effective_method(ws)
    except MethodInvalid as exc:
        raise ExportRefused(409, exc.code, str(exc)) from exc
    sentences.append(_dedup_sentence(method.config.dedup))
    figures["method"] = {**method.config.model_dump(mode="json"), "source": method.source}
    if "UNSPECIFIED" in reasons:
        caveats.append(
            f"{reasons['UNSPECIFIED']} exclusions in this older publication are counted as unspecified; "
            "their codes are in the export."
        )

    # 2. Screener
    published_entries = [view.entries[s] for s in view.entries]
    screeners = {str(e.get("screener_id")) for e in published_entries if e.get("screener_id")}
    all_human = bool(published_entries) and all(str(e.get("method") or "").upper() == "HUMAN" for e in published_entries)
    if all_human and len(screeners) == 1:
        sentences.append("One reviewer screened every record.")
        figures["reviewers"] = 1
    else:
        not_stated.append("Screener: the published decisions are not all human decisions by one reviewer.")
    # M7-method: the not-reported policy and where the values come from.
    sentences.append(NOT_REPORTED_SENTENCES[method.config.not_reported])
    sentences.append(
        "These values are set in the signed protocol."
        if method.source == "protocol"
        else f"These are the harness defaults ({method.config.rules_version}); the protocol does not set them."
    )

    # 3. Agent use
    have_proposals = source(pr.PROPOSALS_FILE)
    proposals = [
        p for p in pr.read_proposals(ws)
        if p.get("protocol_fingerprint") == record.protocol_fingerprint and p.get("study_id") in view.entries
    ] if have_proposals else []
    runs_dir = ws / "literature" / "screening" / "proposals" / "runs"
    runs: dict[str, dict[str, Any]] = {}
    for path in sorted(runs_dir.glob("RUN-*.json")) if runs_dir.is_dir() else []:
        try:
            runs[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        source(path.relative_to(ws))
    consent_path = Path("literature") / "screening" / "agent_consent.json"
    consent: dict[str, Any] = {}
    if source(consent_path):
        try:
            consent = json.loads((ws / consent_path).read_text(encoding="utf-8"))
        except ValueError:
            caveats.append("agent_consent.json cannot be read.")
    figures["n_proposed"] = len({p["study_id"] for p in proposals})
    agents: list[dict[str, Any]] = []
    if not proposals:
        sentences.append("No AI model proposed decisions for this screening.")
        if not have_proposals:
            caveats.append("proposals.jsonl is absent: no AI model proposal is recorded.")
    else:
        groups: dict[tuple[str, str, str, str], set[str]] = {}
        drivers: dict[tuple[str, str, str, str], set[str]] = {}
        for p in proposals:
            run = runs.get(str(p.get("run_id") or ""), {})
            key = (
                str(run.get("provider") or ""), str(p.get("model") or ""), str(p.get("task_version") or ""),
                str(p.get("prompt_sha256") or ""),
            )
            groups.setdefault(key, set()).add(str(p["study_id"]))
            drivers.setdefault(key, set()).add(str(p.get("driver") or ""))
        for (provider, model, task_version, prompt), studies in sorted(groups.items()):
            short = prompt.split(":", 1)[-1][:12]
            agent = {
                "provider": provider or None, "model": model, "task_version": task_version,
                "prompt_sha256_12": short, "n_proposed": len(studies),
            }
            # Drafts submitted over MCP have no agent run: the researcher's own
            # Claude session wrote them (M6-beta, review S-P1-2).
            via_mcp = not provider and drivers[(provider, model, task_version, prompt)] == {"mcp"}
            if via_mcp:
                agent["route"] = "mcp"
            who = (
                f"{model}, via the researcher's Claude session (MCP)" if via_mcp
                else ", ".join(x for x in (provider or "provider not recorded", model) if x)
            )
            sentences.append(
                f"An AI model ({who}, task version {task_version}, prompt SHA-256 {short}) proposed a draft decision "
                f"with quoted evidence for {len(studies)} of {c['screened']} records."
            )
            if not provider and not via_mcp:
                not_stated.append(f"Provider of the {model} drafts: no agent run records it.")
            agents.append(agent)
        if sum(1 for p in proposals if p.get("cannot_decide")):
            caveats.append(
                f"{sum(1 for p in proposals if p.get('cannot_decide'))} proposals say the model could not decide; "
                "they are counted as proposals."
            )
        if all_human:
            sentences.append("Drafts were advisory; every decision in this screening was made by the reviewer.")
        # 4. Consent
        for provider in sorted({a["provider"] for a in agents if a["provider"]}):
            given = consent.get(provider) if isinstance(consent, dict) else None
            if isinstance(given, dict) and given.get("accepted_at"):
                date = _date(given["accepted_at"])
                flow = _clean(given.get("data_flow")) or "record titles and abstracts"
                sentences.append(f"The reviewer consented to sending {flow} to {provider} on {date}.")
                for a in agents:
                    if a["provider"] == provider:
                        a["consent_accepted_at"] = date
            else:
                not_stated.append(f"Consent for {provider}: agent_consent.json has no record.")
    figures["agents"] = agents

    # Settings history (the journal), then sentences 5-7.
    journal = _journal(ws)
    if journal is None:
        caveats.append("audit/journal.jsonl is absent: the settings history cannot be read.")
        journal = []
    else:
        sources.append({"name": "journal.jsonl", "path": "audit/journal.jsonl"})
    rows = [r for r in journal if r.get("action") == SETTINGS_ACTION]
    now = _settings_now(ws, method)
    if method.source == "protocol":
        # Set by the signed protocol for the whole screening (M7 review 3): older
        # settings rows, from before the block, describe nothing that applied.
        blinding = Timeline(method.config.blinding, [], method.config.blinding, False)
    else:
        blinding = _timeline(rows, "blinding", published, now["blinding"])
    mode = _timeline(rows, "mode", published, now["mode"])
    audit_size = _timeline(rows, "sample_audit_size", published, now["sample_audit_size"])
    order = _timeline(rows, "queue_order", published, now["queue_order"])
    events = _published_events(ws, view, published)
    for path in sorted((ws / ev.EVENTS_DIR).glob("*.jsonl")) if (ws / ev.EVENTS_DIR).is_dir() else []:
        source(path.relative_to(ws))

    # 5. Reveal
    shown = "Drafts were shown before the decision"
    hidden = "Drafts were hidden until the reviewer decided"
    figures["blinding"] = {"at_publish": blinding.at_publish, "changes": [list(x) for x in blinding.changes]}
    if proposals:
        if not blinding.changes:
            sentences.append(f"{hidden}." if blinding.initial != "show" else f"{shown} throughout the screening.")
        else:
            sentences.append(f"{shown if blinding.initial == 'show' else hidden} at the start of the screening.")
            for date, value in blinding.changes:
                sentences.append(f"{shown if value == 'show' else hidden} from {date}.")
        have_reveals = source(ev.REVEALS_FILE)
        context = ev.load_context(ws)
        revealed = {
            str(r["study_id"]) for r in (ev.read_reveals(ws) if have_reveals else [])
            if r.get("study_id") in view.entries and ev.is_current(r, context)
            and (published is None or (_time(r.get("revealed_at")) or published) <= published)
        }
        tracked_since = _time(REVEAL_TRACKING_SINCE)
        changed, untracked = set(), set()
        for study, chain in events.items():
            for event in chain:
                if not event.get("supersedes"):
                    continue
                received = _time(event.get("received_at"))
                if received is not None and tracked_since is not None and received < tracked_since:
                    untracked.add(study)
                elif event.get("changed_after_reveal") is True:
                    changed.add(study)
        figures["changed_after_reveal"] = len(changed)
        figures["revealed_decisions"] = len(revealed)
        figures["changes_not_tracked"] = len(untracked)
        # A decision made with its draft already in view is not a blind decision:
        # "changed k of n after seeing a draft" would read as a blind-then-reveal
        # result (M6-beta, review S-P1-1). The first event of each study says
        # whether the draft was in view (`proposal_shown`, contract §3.1).
        proposed = {str(p["study_id"]) for p in proposals}
        visible, blind = set(), set()
        for study, chain in events.items():
            first = next((e for e in chain if not e.get("supersedes")), None)
            if first is None or study not in proposed:
                continue
            shown_info = first.get("proposal_shown")
            if shown_info and shown_info.get("revealed_after_decision") is not True:
                visible.add(study)
            else:
                blind.add(study)
        figures["decided_with_draft_visible"] = len(visible)
        if visible:
            # Only decisions made before their reveal are a blind comparison.
            blind_revealed = revealed & blind
            figures["revealed_blind_decisions"] = len(blind_revealed)
            figures["changed_after_reveal_blind"] = len(changed & blind)
            if blind_revealed:
                sentences.append(
                    f"After seeing a draft, the reviewer changed {len(changed & blind)} of {len(blind_revealed)} decisions."
                )
            sentences.append(
                f"{len(visible)} decisions were made with the draft visible; no blind comparison is reported."
                if len(visible) != 1
                else "1 decision was made with the draft visible; no blind comparison is reported."
            )
        elif revealed:
            sentences.append(
                f"After seeing a draft, the reviewer changed {len(changed)} of {len(revealed)} decisions."
            )
        else:
            sentences.append("No draft was recorded as shown to the reviewer.")
        if untracked:
            sentences.append(
                f"For {len(untracked)} decisions changed before reveal tracking began, whether the change "
                "followed a draft was not tracked."
            )
            not_stated.append(f"Changes after a draft: not tracked for {len(untracked)} decisions changed before reveal tracking began.")

    # 5b. Advance on decide: reported only when drafts were skipped.
    if proposals:
        history: list[tuple[datetime | None, Any]] = []
        for row in rows:
            after = (row.get("parameters") or {}).get("after") or {}
            if "advance_on_decide" in after:
                history.append((_time(row.get("timestamp")), after["advance_on_decide"]))
        history.sort(key=lambda h: h[0] or datetime.min.replace(tzinfo=UTC))

        def mode_at(when: datetime | None) -> Any:
            value = DEFAULT_SETTINGS["advance_on_decide"]
            for at, after in history:
                if when is None or at is None or at <= when:
                    value = after
            return value

        proposed_studies = {str(p["study_id"]) for p in proposals}
        drafted_at: dict[str, datetime | None] = {}
        for p in proposals:
            created = _time(p.get("created_at"))
            study = str(p["study_id"])
            if study not in drafted_at or (created and (drafted_at[study] is None or created < drafted_at[study])):
                drafted_at[study] = created
        skipped = 0
        for study, chain in events.items():
            first = next((e for e in chain if not e.get("supersedes")), None)
            if first is None or study not in proposed_studies or study in visible:
                continue
            received = _time(first.get("received_at"))
            drafted = drafted_at.get(study)
            if received is None or drafted is None or drafted > received:
                continue  # no draft existed when the record was decided
            if mode_at(received) == "next_at_once":
                skipped += 1
        figures["decided_draft_skipped"] = skipped
        if skipped:
            sentences.append(
                f"For {skipped} records the next record opened at once after the decision, so the draft was not "
                "shown unless the reviewer opened it from the record's details."
            )

    # 6. AI-agreed exclusion
    on = "ai_agreed_exclusion"
    size = audit_size.at_publish
    figures["mode"] = {"at_publish": mode.at_publish, "changes": [list(x) for x in mode.changes], "sample_audit_size": size}
    with_size = f", with a sample check of {size}" if size else ""
    label = "The AI-agreed-exclusion setting was"
    if not mode.changes:
        sentences.append(f"{label} on throughout the screening{with_size}." if mode.initial == on else f"{label} off.")
    else:
        sentences.append(f"{label} {'on' if mode.initial == on else 'off'} at the start of the screening.")
        for date, value in mode.changes:
            sentences.append(f"{label} on from {date}{with_size}." if value == on else f"{label} off from {date}.")

    # 7. Order
    figures["queue_order"] = {"at_publish": order.at_publish if order.recorded else None,
                              "changes": [list(x) for x in order.changes]}
    if order.recorded:
        for date, value in order.changes:
            sentences.append(f"Records were presented in {ORDER_LABELS.get(value, str(value))} order from {date}.")
        first = order.changes[0][0]
        earliest = min((str(e.get("received_at") or "") for chain in events.values() for e in chain), default="")
        if earliest and _date(earliest) < first:
            not_stated.append(f"Queue order: not recorded before {first}.")
    else:
        not_stated.append("Queue order: not recorded for this screening.")

    paragraph = " ".join(sentences)
    return {
        "generation_id": record.generation_id,
        "generation_fingerprint": record.fingerprint(),
        "published_at": record.published_at,
        "language": "en",
        "paragraph": paragraph,
        "figures": figures,
        "sources": sources,
        "caveats": caveats,
        "not_stated": not_stated,
    }
