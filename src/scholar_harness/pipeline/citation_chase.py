"""Citation chasing (snowballing) from the published includes (M3g-citation-chasing).

A chase run takes the researcher's published includes (``literature/included.json``)
as seeds, asks each database for the papers they cite (backward) and the papers
that cite them (forward), deduplicates what comes back against the whole corpus
and within the chase, applies the protocol's year window, and keeps the new
records in a run folder of its own, ``literature/citation_chase/chase_NNN/``:

* ``chase.json``: the manifest (seeds, one leg per seed × database × direction,
  counts, status, notes);
* ``raw.json``: every record fetched, in seed, database and direction order;
* ``edges.json``: one row per (seed, direction, database, record) link, the
  provenance of why a record is here (kept for records already in the corpus too);
* ``new.json``: the records that are new to the corpus and inside the year
  window, written only when the run is published (not ``FAILED``, not cancelled).

The run re-derives nothing: ``SearchEngine.snowball_forward`` /
``snowball_backward`` and the providers' ``get_citations`` / ``get_references``
fetch, the workspace's ``Deduplicator`` (the protocol's ``method.dedup``) decides
what is one work. Honesty follows the discovery stage: every database failing is
``FAILED`` (nothing published), one failing is ``PARTIAL``, nothing new is
``EMPTY_RESULT``, a cancel is ``PARTIAL`` with ``cancelled by the researcher``.
The chase changes nothing of the frozen corpus: adding its records to screening is
the accept step (``accept_citation_chase``), decided separately.
"""

from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_search.dedup import Deduplicator, stable_order
from scholar_search.engine import STOPPED_NOTE, SearchEngine, provider_error_code
from scholar_search.exceptions import ProviderError
from scholar_search.models import Document
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.recall import normalize_doi

from scholar_harness.pipeline import discovery as _discovery
from scholar_harness.workspace.audit import append_event

logger = logging.getLogger(__name__)

CHASE_DIR = "citation_chase"
CHASE_SCHEMA = "nexus.citation-chase.v1"
AGENT = "scholar-harness"
#: OpenAlex first, Semantic Scholar second (plan §6 row M3g).
DEFAULT_PROVIDERS: tuple[str, ...] = ("openalex", "semanticscholar")
DIRECTIONS: tuple[str, ...] = ("forward", "backward")
#: Decision 2 (proposed): citing papers are capped per seed and database; references are not.
DEFAULT_FORWARD_CAP = 500
#: Decision 2 (proposed): the run keeps at most this many new records.
DEFAULT_RUN_CEILING = 5_000
#: The `sources[]` marker every chased record carries.
VIA = "citation-chase"
#: The decisions a published include row may carry to be a seed.
SEED_DECISIONS: dict[str, tuple[str, ...]] = {
    "included": ("INCLUDE",),
    "included+unclear": ("INCLUDE", "MAYBE"),
}

_OPENALEX_PREFIX = re.compile(r"^https?://(?:api\.)?openalex\.org/(?:works/)?", re.I)


class ChaseRefused(Exception):
    """A typed refusal before anything is fetched or written."""

    def __init__(self, message: str, code: str = "CHASE_REFUSED") -> None:
        super().__init__(message)
        self.code = code
        self.details: dict[str, Any] = {}


@dataclass
class ChaseSeed:
    study_id: str
    title: str
    decision: str
    doi: str | None = None
    openalex_id: str | None = None
    s2_id: str | None = None
    chaseable: bool = True
    reason: str | None = None


@dataclass
class ChaseLeg:
    seed: str
    provider: str
    direction: str
    fetched: int = 0
    cap: int | None = None
    cap_hit: bool = False
    status: str = "pending"
    error: str | None = None
    error_code: str | None = None
    notes: list[str] = field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None


@dataclass
class ChaseCounts:
    raw: int = 0
    duplicates_within_chase: int = 0
    already_in_corpus: int = 0
    outside_year_window: int = 0
    over_ceiling: int = 0
    new: int = 0


@dataclass
class ChaseOutcome:
    chase: str
    status: str
    reason: str
    seeds: list[ChaseSeed]
    legs: list[ChaseLeg]
    counts: ChaseCounts
    published: bool
    cancelled: bool
    files: tuple[str, ...]
    notes: list[str] = field(default_factory=list)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _short_openalex(value: str | None) -> str | None:
    if not value:
        return None
    return _OPENALEX_PREFIX.sub("", value.strip()) or None


# --------------------------------------------------------------------------- seeds


def load_seeds(workspace: Path | str, *, seed_source: str = "included") -> list[ChaseSeed]:
    """The published includes as seeds (``literature/included.json``).

    A row is a seed when its published decision is one of ``SEED_DECISIONS[seed_source]``;
    it is chaseable when it carries a DOI, an OpenAlex id or a Semantic Scholar id,
    which is all a database can be asked about (lesson 2: never a constructed guess).
    """
    if seed_source not in SEED_DECISIONS:
        raise ChaseRefused(f"seed source must be one of {sorted(SEED_DECISIONS)}", "CHASE_SEEDS_INVALID")
    ws = Path(workspace)
    path = ws / "literature" / "included.json"
    if not path.is_file():
        raise ChaseRefused(
            "literature/included.json is missing: publish the screening before chasing citations",
            "SCREENING_NOT_PUBLISHED",
        )
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ChaseRefused(f"literature/included.json cannot be read ({exc})", "SCREENING_NOT_PUBLISHED") from exc
    wanted = SEED_DECISIONS[seed_source]
    seeds: list[ChaseSeed] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        screening = row.get("screening") if isinstance(row.get("screening"), dict) else {}
        decision = str(screening.get("decision") or "INCLUDE")
        if decision not in wanted:
            continue
        eids = row.get("external_ids") if isinstance(row.get("external_ids"), dict) else {}
        doi = normalize_doi(eids.get("doi") or row.get("doi")) or None
        openalex_id = _short_openalex(eids.get("openalex_id"))
        s2_id = (eids.get("s2_id") or "").strip() or None
        study_id = str(row.get("workspace_id") or "")
        seed = ChaseSeed(
            study_id=study_id,
            title=str(row.get("title") or "Untitled"),
            decision=decision,
            doi=doi,
            openalex_id=openalex_id,
            s2_id=s2_id,
        )
        if not study_id:
            seed.chaseable, seed.reason = False, "no study id"
        elif not (doi or openalex_id or s2_id):
            seed.chaseable, seed.reason = False, "no DOI, OpenAlex id or Semantic Scholar id"
        seeds.append(seed)
    seeds.sort(key=lambda s: s.study_id)
    return seeds


# --------------------------------------------------------------------------- the run


async def _seed_id_for(provider: Any, seed: ChaseSeed) -> tuple[str | None, str | None]:
    """The id this database is asked about for ``seed``, or ``(None, why)``.

    OpenAlex takes a work id; a seed known only by DOI is looked up once
    (``/works/https://doi.org/<doi>``, as the verifier does). Semantic Scholar
    takes its own id or ``DOI:<doi>`` directly.
    """
    name = str(getattr(provider, "name", "")).lower()
    if name == "openalex":
        if seed.openalex_id:
            return seed.openalex_id, None
        if not seed.doi:
            return None, "OpenAlex needs a work id or a DOI"
        resolve = getattr(provider, "resolve_doi", None)
        if resolve is not None:  # a double may answer directly
            found = await resolve(seed.doi)
            return (found, None) if found else (None, f"DOI {seed.doi} not found on OpenAlex")
        client = getattr(provider, "client", None)
        base_url = getattr(provider, "base_url", None)
        if client is None or not base_url:
            return None, "OpenAlex cannot look the DOI up"
        try:
            resp = await client.get(f"{base_url}/https://doi.org/{seed.doi}")
        except ProviderError as exc:
            if exc.status_code == 404:
                return None, f"DOI {seed.doi} not found on OpenAlex"
            raise
        body = resp.json() if hasattr(resp, "json") else {}
        work_id = _short_openalex((body.get("ids") or {}).get("openalex") or body.get("id"))
        if work_id:
            seed.openalex_id = work_id
            return work_id, None
        return None, f"DOI {seed.doi} not found on OpenAlex"
    if name == "semanticscholar":
        if seed.s2_id:
            return seed.s2_id, None
        if seed.doi:
            return f"DOI:{seed.doi}", None
        return None, "Semantic Scholar needs its paper id or a DOI"
    # Any other database: a DOI is the only id every provider understands.
    if seed.doi:
        return seed.doi, None
    return None, f"{name} needs a DOI"


def _year_window(protocol_path: Path) -> tuple[int | None, int | None]:
    query, _providers = compile_protocol_search(protocol_path)
    return getattr(query, "year_min", None), getattr(query, "year_max", None)


def _corpus_documents(ws: Path) -> list[Document]:
    """Every record of the frozen corpus, from ``literature/verified.json``."""
    from scholar_harness.screening.batcher import _rebuild_doc

    path = ws / "literature" / "verified.json"
    if not path.is_file():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    docs: list[Document] = []
    for i, row in enumerate(rows if isinstance(rows, list) else [], start=1):
        if isinstance(row, dict):
            docs.append(_rebuild_doc(row, fallback_id=f"corpus-{i:06d}"))
    return docs


def _deduplicator(ws: Path) -> Deduplicator:
    from scholar_harness.corpus_accept import AcceptCorpusRefused, _deduplicator

    try:
        return _deduplicator(ws)
    except AcceptCorpusRefused as exc:
        raise ChaseRefused(str(exc), exc.code or "PROTOCOL_METHOD_INVALID") from exc


def _parent_corpus(ws: Path) -> dict[str, Any] | None:
    """The newest accepted corpus snapshot's registry row, or ``None``."""
    registry = ws / "audit" / "artifact_registry.json"
    if not registry.is_file():
        return None
    try:
        entries = json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {})
    except (OSError, ValueError):
        return None
    corpora = [
        {"artifact_id": aid, **entry}
        for aid, entry in entries.items()
        if isinstance(entry, dict) and entry.get("artifact_type") == "corpus_snapshot"
    ]
    if not corpora:
        return None
    return max(corpora, key=lambda e: str(e.get("accepted_at") or ""))


def _corpus_entry(ws: Path, artifact_id: str) -> dict[str, Any] | None:
    """One registered corpus snapshot's registry row, or ``None``."""
    registry = ws / "audit" / "artifact_registry.json"
    try:
        entry = json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {}).get(artifact_id)
    except (OSError, ValueError):
        return None
    if not isinstance(entry, dict) or entry.get("artifact_type") != "corpus_snapshot":
        return None
    return {"artifact_id": artifact_id, **entry}


def _generation_id(ws: Path) -> str | None:
    path = ws / "literature" / "screening" / "generation.json"
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("generation_id") or "") or None
    except (OSError, ValueError):
        return None


def _doc_key(doc: Document) -> str:
    doi = normalize_doi(doc.external_ids.doi) if doc.external_ids.doi else ""
    if doi:
        return f"doi:{doi}"
    return f"{doc.provider}:{doc.provider_id}"


def _as_row(doc: Document) -> dict[str, Any]:
    return asdict(doc)


def _next_chase_dir(lit_dir: Path) -> Path:
    runs = lit_dir / CHASE_DIR
    runs.mkdir(parents=True, exist_ok=True)
    taken = [
        int(p.name[6:]) for p in runs.iterdir()
        if p.is_dir() and p.name.startswith("chase_") and p.name[6:].isdigit()
    ]
    run_dir = runs / f"chase_{max(taken, default=0) + 1:03d}"
    run_dir.mkdir(exist_ok=False)
    return run_dir


async def run_citation_chase(
    workspace: Path | str,
    *,
    providers: list[str] | None = None,
    directions: tuple[str, ...] | list[str] = DIRECTIONS,
    forward_cap: int | None = DEFAULT_FORWARD_CAP,
    run_ceiling: int | None = DEFAULT_RUN_CEILING,
    seed_source: str = "included",
    note: str | None = None,
    leg_callback=None,
    should_stop=None,
    agent: str = AGENT,
) -> ChaseOutcome:
    """Chase the published includes' references and citing papers; see the module doc."""
    ws = Path(workspace).resolve()
    lit_dir = ws / "literature"
    protocol_path = ws / "protocol.json"
    if not protocol_path.is_file():
        raise ChaseRefused("protocol.json not found", "PROTOCOL_MISSING")
    for direction in directions:
        if direction not in DIRECTIONS:
            raise ChaseRefused(f"direction must be one of {DIRECTIONS}", "CHASE_DIRECTION_INVALID")
    if not directions:
        raise ChaseRefused("at least one direction is needed", "CHASE_DIRECTION_INVALID")
    seeds = load_seeds(ws, seed_source=seed_source)
    deduplicator = _deduplicator(ws)
    year_min, year_max = _year_window(protocol_path)
    names = [str(n) for n in (providers or list(DEFAULT_PROVIDERS))]
    instances = _discovery._resolve_providers(names)
    if not instances:
        raise ChaseRefused(f"no known database among {names}", "PROVIDER_UNKNOWN")
    engine = SearchEngine(providers=instances)
    parent = _parent_corpus(ws)
    generation_id = _generation_id(ws)
    started_at = _now()

    chaseable = [s for s in seeds if s.chaseable]
    legs: list[ChaseLeg] = []
    raw: list[Document] = []
    edges: list[dict[str, Any]] = []
    notes: list[str] = [note.strip()] if note and note.strip() else []
    cancelled = False
    retrieved_at = datetime.now(UTC)

    # Seed order, then database order (OpenAlex first), then direction: the raw
    # list depends on the inputs, never on which answer arrived first.
    for seed in chaseable:
        for provider in instances:
            if should_stop is not None and should_stop():
                cancelled = True
                break
            seed_id, why = await _seed_id_for_safe(provider, seed)
            for direction in directions:
                leg = ChaseLeg(seed=seed.study_id, provider=provider.name, direction=direction,
                               cap=forward_cap if direction == "forward" else None, started_at=_now())
                legs.append(leg)
                if seed_id is None:
                    leg.status, leg.finished_at = "skipped", _now()
                    leg.notes.append(why or "no id for this database")
                    if leg_callback:
                        leg_callback(leg)
                    continue
                try:
                    if direction == "forward":
                        docs = await engine.snowball_forward(seed_id, provider.name, limit=leg.cap)
                    else:
                        docs = await engine.snowball_backward(seed_id, provider.name, limit=leg.cap)
                except Exception as exc:  # noqa: BLE001 - a database's failure is the leg's record
                    leg.status, leg.error, leg.error_code = "failed", f"{type(exc).__name__}: {exc}"[:300], provider_error_code(exc)
                    leg.finished_at = _now()
                    if leg_callback:
                        leg_callback(leg)
                    continue
                leg.fetched = len(docs)
                leg.cap_hit = bool(leg.cap is not None and leg.fetched >= leg.cap)
                if leg.cap_hit:
                    leg.notes.append(f"stopped at the cap of {leg.cap}: the count is a lower bound")
                leg.status, leg.finished_at = "ok", _now()
                for doc in docs:
                    doc = copy.deepcopy(doc)
                    doc.workspace_id = None
                    doc.query_id = None
                    doc.retrieved_at = retrieved_at
                    doc.sources = [{
                        "provider": provider.name, "id": doc.provider_id, "via": VIA,
                        "seed": seed.study_id, "direction": direction,
                    }]
                    raw.append(doc)
                    edges.append({
                        "seed": seed.study_id, "direction": direction, "provider": provider.name,
                        "record": _doc_key(doc), "provider_id": doc.provider_id, "title": doc.title,
                    })
                if leg_callback:
                    leg_callback(leg)
        if cancelled:
            break
    await engine.close()

    counts = ChaseCounts(raw=len(raw))
    new_docs, already, within = _deduplicate(ws, raw, deduplicator)
    counts.duplicates_within_chase = within
    counts.already_in_corpus = len(already)
    kept: list[Document] = []
    for doc in new_docs:
        if doc.year is not None and (
            (year_min is not None and doc.year < year_min) or (year_max is not None and doc.year > year_max)
        ):
            counts.outside_year_window += 1
            continue
        kept.append(doc)
    if run_ceiling is not None and len(kept) > run_ceiling:
        counts.over_ceiling = len(kept) - run_ceiling
        kept = kept[:run_ceiling]
        notes.append(f"run ceiling of {run_ceiling} new records reached: {counts.over_ceiling} not kept")
    counts.new = len(kept)

    asked = [leg for leg in legs if leg.status != "skipped"]
    failed = [leg for leg in asked if leg.status == "failed"]
    if not chaseable:
        status, reason = "EMPTY_RESULT", "no chaseable seed: the published includes carry no DOI or database id"
    elif asked and len(failed) == len(asked):
        status, reason = "FAILED", "every database leg failed"
    elif failed:
        status, reason = "PARTIAL", f"{len(failed)} of {len(asked)} legs failed"
    elif counts.new == 0:
        status, reason = "EMPTY_RESULT", "nothing new: every chased record is in the corpus, a duplicate or outside the year window"
    else:
        status, reason = "SUCCESS", f"{counts.new} new record(s) from {len(chaseable)} seed(s)"
    if cancelled:
        status = "PARTIAL"
        reason = f"{STOPPED_NOTE}: {counts.raw} record(s) fetched before the stop; not published"
        notes.append(STOPPED_NOTE)
    if counts.over_ceiling and status == "SUCCESS":
        status = "PARTIAL"
    published = status != "FAILED" and not cancelled

    run_dir = _next_chase_dir(lit_dir)
    files: list[str] = []
    (run_dir / "raw.json").write_text(_dump([_as_row(d) for d in raw]), encoding="utf-8")
    files.append(str(run_dir / "raw.json"))
    (run_dir / "edges.json").write_text(_dump(edges), encoding="utf-8")
    files.append(str(run_dir / "edges.json"))
    if published:
        (run_dir / "new.json").write_text(_dump([_as_row(d) for d in kept]), encoding="utf-8")
        files.append(str(run_dir / "new.json"))
    manifest = {
        "schema": CHASE_SCHEMA,
        "chase": run_dir.name,
        "status": status,
        "reason": reason,
        "started_at": started_at,
        "finished_at": _now(),
        "seed_source": seed_source,
        "generation_id": generation_id,
        "parent_corpus": {
            "artifact_id": parent["artifact_id"], "sha256": parent.get("sha256"),
        } if parent else None,
        "providers": [p.name for p in instances],
        "directions": list(directions),
        "forward_cap": forward_cap,
        "run_ceiling": run_ceiling,
        "year_min": year_min,
        "year_max": year_max,
        "seeds": [asdict(s) for s in seeds],
        "legs": [asdict(leg) for leg in legs],
        "counts": asdict(counts),
        "already_in_corpus": already,
        "published": published,
        "cancelled": cancelled,
        "notes": notes,
        "accepted": None,
    }
    (run_dir / "chase.json").write_text(_dump(manifest), encoding="utf-8")
    files.append(str(run_dir / "chase.json"))

    append_event(
        ws,
        "CITATION_CHASE",
        f"Citation chase {run_dir.name} ({status}): {counts.raw} fetched from {len(chaseable)} seed(s), "
        f"{counts.new} new to the corpus",
        agent=agent,
        inputs=[str(lit_dir / "included.json"), str(lit_dir / "verified.json"), str(protocol_path)],
        outputs=files,
        parameters={
            "chase": run_dir.name, "providers": manifest["providers"], "directions": list(directions),
            "forward_cap": forward_cap, "run_ceiling": run_ceiling, "seed_source": seed_source,
            "generation_id": generation_id, "parent_corpus": manifest["parent_corpus"],
            "published": published, "method": "EXTERNAL_PROVIDER", "reason": reason, "notes": notes,
        },
        metrics={
            "seeds": len(seeds), "chaseable_seeds": len(chaseable), "legs": len(legs),
            "legs_failed": len(failed), **asdict(counts),
        },
        status=status,
    )
    return ChaseOutcome(
        chase=run_dir.name, status=status, reason=reason, seeds=seeds, legs=legs, counts=counts,
        published=published, cancelled=cancelled, files=tuple(files), notes=notes,
    )


async def _seed_id_for_safe(provider: Any, seed: ChaseSeed) -> tuple[str | None, str | None]:
    try:
        return await _seed_id_for(provider, seed)
    except Exception as exc:  # noqa: BLE001 - a failed lookup skips the seed on this database
        return None, f"lookup failed: {type(exc).__name__}: {exc}"[:300]


def _dump(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def _deduplicate(
    ws: Path, raw: list[Document], deduplicator: Deduplicator
) -> tuple[list[Document], list[dict[str, Any]], int]:
    """``(new, already_in_corpus, duplicates_within_chase)``.

    The corpus records and the chased records are clustered together with the
    workspace's deduplicator. A cluster with a corpus member is not new: each of
    its chased members is listed under ``already_in_corpus`` with the study it
    matched. A cluster of chased records only keeps the first member in stable
    order as the new record, with every member's ``sources`` merged on it.
    """
    if not raw:
        return [], [], 0
    corpus = _corpus_documents(ws)
    # The deduplicator rewrites every member's ``workspace_id`` in memory, so the
    # study ids are taken before clustering; the corpus copies are discarded after.
    corpus_study = {id(doc): doc.workspace_id for doc in corpus}
    corpus_ids = set(corpus_study)
    chased = copy.deepcopy(raw)
    chased_index = {id(doc): i for i, doc in enumerate(chased)}
    clusters = deduplicator.deduplicate(stable_order(corpus + chased))
    new: list[Document] = []
    already: list[dict[str, Any]] = []
    unique_chased = 0
    for cluster in clusters:
        members = list(cluster.members) or [cluster.representative]
        chased_members = [m for m in members if id(m) in chased_index]
        if not chased_members:
            continue
        unique_chased += 1
        corpus_members = [m for m in members if id(m) in corpus_ids]
        if corpus_members:
            study = corpus_study[id(corpus_members[0])]
            for m in chased_members:
                already.append({"record": _doc_key(m), "title": m.title, "study_id": study, "sources": list(m.sources)})
            continue
        keep = copy.deepcopy(min(chased_members, key=lambda m: chased_index[id(m)]))
        merged: list[dict[str, Any]] = []
        for m in sorted(chased_members, key=lambda m: chased_index[id(m)]):
            for source in m.sources:
                if source not in merged:
                    merged.append(source)
        keep.sources = merged
        keep.workspace_id = None  # minted by the accept, never by the chase
        keep.cluster_id = None
        new.append(keep)
    within = len(raw) - unique_chased
    # ``new`` holds copies; order them by the first appearance of their key in the raw list.
    first_seen: dict[str, int] = {}
    for i, doc in enumerate(chased):
        first_seen.setdefault(_doc_key(doc), i)
    new.sort(key=lambda d: first_seen.get(_doc_key(d), len(chased)))
    return new, already, within


# --------------------------------------------------------------------------- reading runs


def chase_dirs(workspace: Path | str) -> list[Path]:
    """Every chase run folder, newest first."""
    runs = Path(workspace) / "literature" / CHASE_DIR
    if not runs.is_dir():
        return []
    return sorted(
        (d for d in runs.iterdir() if d.is_dir() and d.name.startswith("chase_") and d.name[6:].isdigit()),
        key=lambda d: int(d.name[6:]),
        reverse=True,
    )


def read_manifest(run_dir: Path) -> dict[str, Any]:
    return json.loads((run_dir / "chase.json").read_text(encoding="utf-8"))


def chase_summaries(workspace: Path | str) -> list[dict[str, Any]]:
    """One row per chase run for the status views, newest first."""
    out: list[dict[str, Any]] = []
    for run_dir in chase_dirs(workspace):
        try:
            m = read_manifest(run_dir)
        except (OSError, ValueError):
            continue
        out.append({
            "chase": m.get("chase", run_dir.name),
            "status": m.get("status"),
            "reason": m.get("reason"),
            "started_at": m.get("started_at"),
            "finished_at": m.get("finished_at"),
            "seeds": len(m.get("seeds") or []),
            "chaseable_seeds": sum(1 for s in m.get("seeds") or [] if s.get("chaseable")),
            "providers": m.get("providers") or [],
            "directions": m.get("directions") or [],
            "counts": m.get("counts") or {},
            "published": bool(m.get("published")),
            "accepted": m.get("accepted"),
        })
    return out


# --------------------------------------------------------------------------- the accept (round 2)


@dataclass
class ChaseAccepted:
    chase: str
    round: int
    artifact_id: str
    study_count: int
    record_count: int
    outcome_status: str
    parent_corpus: str
    archived: list[str]
    round_path: str
    already_accepted: bool = False


def legs_summary(legs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per database and direction, summed by the engine (the browser sums nothing)."""
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for leg in legs:
        if not isinstance(leg, dict):
            continue
        key = (str(leg.get("provider")), str(leg.get("direction")))
        row = rows.setdefault(key, {
            "provider": key[0], "direction": key[1], "legs": 0, "ok": 0, "failed": 0, "skipped": 0,
            "fetched": 0, "cap_hits": 0,
        })
        row["legs"] += 1
        status = str(leg.get("status") or "")
        if status in ("ok", "failed", "skipped"):
            row[status] += 1
        row["fetched"] += int(leg.get("fetched") or 0)
        row["cap_hits"] += 1 if leg.get("cap_hit") else 0
    def order(key: tuple[str, str]) -> tuple[int, str, int]:
        provider, direction = key
        return (
            DEFAULT_PROVIDERS.index(provider) if provider in DEFAULT_PROVIDERS else 9,
            provider,
            DIRECTIONS.index(direction) if direction in DIRECTIONS else 9,
        )

    return [rows[k] for k in sorted(rows, key=order)]


def chase_run_dir(workspace: Path | str, chase: str | None = None) -> Path | None:
    """The named chase run, or the newest published one; ``None`` when there is none."""
    ws = Path(workspace)
    if chase:
        run_dir = ws / "literature" / CHASE_DIR / chase
        if not re.fullmatch(r"chase_\d{3,}", chase) or not (run_dir / "chase.json").is_file():
            raise ChaseRefused(f"no chase run {chase!r} in this workspace", "CHASE_NOT_RUN")
        return run_dir
    for run_dir in chase_dirs(ws):
        try:
            manifest = read_manifest(run_dir)
        except (OSError, ValueError):
            continue
        if manifest.get("published") and (run_dir / "new.json").is_file():
            return run_dir
    return None


def accept_citation_chase(
    workspace: Path | str, *, chase: str | None = None, agent: str = AGENT, now: datetime | None = None
) -> ChaseAccepted:
    """Send a chase run's new records to screening as the next round (decision 2026-11-12, item 4).

    Order, fail-closed: every precondition is checked and the round's corpus
    snapshot is built and validated in memory before anything is written; the
    acceptance gate registers the snapshot (its ``inputs`` name the parent
    snapshot); then the finished round's ``literature/screening/`` and its
    published outputs move into ``literature/screening_rounds/round_NNN/``,
    the new records become ``literature/verified.json``, the rounds index
    makes the new round current, the chase manifest records the accept and
    three journal rows are written (``CORPUS_SNAPSHOT_ACCEPTED``,
    ``SCREENING_ROUND_ARCHIVED``, ``CITATION_CHASE_ACCEPTED``). A move that
    stops part way is journaled and refused as ``ARCHIVE_INCOMPLETE``; a retry
    continues it.
    """
    from pydantic import ValidationError
    from scholar_search.identity import build_corpus_snapshot_artifact

    from scholar_harness.authority.generations import GenerationStatus, require_current_generation
    from scholar_harness.contracts import AcceptanceContext, accept_artifact
    from scholar_harness.contracts.canonical import canonical_fingerprint, deterministic_id
    from scholar_harness.contracts.identifiers import IdentifierKind
    from scholar_harness.contracts.models import CorpusSnapshotArtifact
    from scholar_harness.corpus_accept import (
        AcceptCorpusRefused,
        AcceptCorpusResult,
        _protocol_fingerprint,
        _stable_sci_id,
        _workspace_id,
    )
    from scholar_harness.pipeline.coordinator import _journal_snapshot_accepted
    from scholar_harness.screening import rounds
    from scholar_harness.screening.batcher import _rebuild_doc

    ws = Path(workspace).resolve()
    lit = ws / "literature"
    run_dir = chase_run_dir(ws, chase)
    if run_dir is None:
        raise ChaseRefused("no published chase run in this workspace; run `chase run` first", "CHASE_NOT_RUN")
    manifest = read_manifest(run_dir)
    if manifest.get("accepted"):
        sent_round = manifest["accepted"].get("round")
        raise ChaseRefused(f"{run_dir.name} was already sent to screening (round {sent_round})", "CHASE_ALREADY_ACCEPTED")
    if not manifest.get("published") or not (run_dir / "new.json").is_file():
        raise ChaseRefused(f"{run_dir.name} was not published ({manifest.get('status')}): nothing to send", "CHASE_NOT_RUN")
    rows = json.loads((run_dir / "new.json").read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ChaseRefused(f"{run_dir.name} found nothing new to screen", "CHASE_NOTHING_NEW")

    try:
        workspace_id = _workspace_id(ws)
        fingerprint = _protocol_fingerprint(ws)
    except AcceptCorpusRefused as exc:
        raise ChaseRefused(str(exc), exc.code or "PROTOCOL_INVALID") from exc
    current = rounds.current_round(ws)
    previous_number = int(current.get("round") or 1)
    number = previous_number + 1
    # A retry after an archive that stopped part way: the finished round's
    # generation record is already in the round folder, so it is read there.
    partial = rounds.round_folder(ws, previous_number)
    resumed = partial.is_dir() and (partial / "screening" / "generation.json").is_file()
    if resumed:
        try:
            published = json.loads((partial / "screening" / "generation.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ChaseRefused(f"the archived generation record of round {previous_number} cannot be read ({exc})", "ARCHIVE_INCOMPLETE") from exc
        generation_id = str(published.get("generation_id") or "")
        generation_protocol = str(published.get("protocol_fingerprint") or "")
    else:
        currentness = require_current_generation(ws)
        record = currentness.record
        if record is not None and record.protocol_fingerprint != fingerprint:
            raise ChaseRefused(
                "protocol.json changed after the screening was published; the published includes no longer belong "
                "to the current protocol, so screening must be redone and published under it before a chase is sent",
                "PROTOCOL_CHANGED_SINCE_PUBLISH",
            )
        if currentness.status is not GenerationStatus.CURRENT or record is None:
            raise ChaseRefused(
                f"the screening is not published and current ({currentness.code or currentness.status.value}: "
                f"{currentness.message})",
                "SCREENING_NOT_PUBLISHED",
            )
        generation_id, generation_protocol = record.generation_id, record.protocol_fingerprint
    if generation_protocol and generation_protocol != fingerprint:
        raise ChaseRefused(
            "protocol.json changed after the screening was published; screening must be redone and published "
            "under the current protocol before a chase is sent",
            "PROTOCOL_CHANGED_SINCE_PUBLISH",
        )
    if manifest.get("generation_id") and manifest["generation_id"] != generation_id:
        raise ChaseRefused("the screening was published again after this chase ran; run the chase again", "CHASE_STALE")
    declared = (manifest.get("parent_corpus") or {}).get("artifact_id")
    if resumed and declared:
        # The round's snapshot was registered before the move stopped, so the
        # newest snapshot is no longer the parent: the parent is the declared one.
        parent = _corpus_entry(ws, declared)
        if parent is None:
            raise ChaseRefused(f"the parent corpus {declared} of this chase is not registered", "CHASE_STALE")
    else:
        parent = _parent_corpus(ws)
        if parent is None:
            raise ChaseRefused("no accepted corpus snapshot in this workspace", "SNAPSHOT_NOT_ACCEPTED")
        if declared and declared != parent["artifact_id"]:
            raise ChaseRefused("a later corpus snapshot was accepted after this chase ran; run the chase again", "CHASE_STALE")
    deduplicator = _deduplicator(ws)

    verified_rows: list[dict[str, Any]] = []
    docs: list[Document] = []
    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ChaseRefused(f"{run_dir.name}/new.json row {i} is not a record", "CHASE_NOT_RUN")
        doc = _rebuild_doc(row, fallback_id="")
        doc.workspace_id = _stable_sci_id(doc, source=run_dir.name, position=i)
        new_row = dict(row)
        new_row["workspace_id"] = doc.workspace_id
        verified_rows.append(new_row)
        docs.append(doc)
    failed = sorted({
        f"{leg.get('provider')}: {leg.get('error_code') or leg.get('error') or 'failed'}"
        for leg in manifest.get("legs") or [] if isinstance(leg, dict) and leg.get("status") == "failed"
    })
    run_id = deterministic_id(
        IdentifierKind.RUN, workspace_id,
        {"operation": "accept-chase-corpus", "chase": run_dir.name, "protocol_fingerprint": fingerprint,
         "records_sha256": canonical_fingerprint(verified_rows)},
    )
    built = build_corpus_snapshot_artifact(
        docs, workspace_id=workspace_id, run_id=run_id, protocol_fingerprint=fingerprint,
        created_at=now or datetime.now(UTC), deduplicator=deduplicator, provider_warnings=failed,
    )
    artifact = built.artifact
    artifact["inputs"] = [{"artifact_id": parent["artifact_id"], "sha256": parent["sha256"]}]
    try:
        CorpusSnapshotArtifact.model_validate(artifact)
    except ValidationError as exc:
        raise ChaseRefused(
            f"the round {number} snapshot is not a valid corpus snapshot ({str(exc)[:300]})", "ACCEPT_CORPUS_REFUSED"
        ) from exc

    registry = ws / "audit" / "artifact_registry.json"
    entries = json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {}) if registry.is_file() else {}
    already = artifact["artifact_id"] in entries
    if not already:
        result = accept_artifact(
            ws, artifact,
            expected=AcceptanceContext(
                workspace_id=workspace_id, protocol_fingerprint=fingerprint,
                corpus_fingerprint=artifact["corpus_fingerprint"],
            ),
            actor="nexus-scholar-chase-accept",
        )
        if not result.accepted:
            issues = "; ".join(f"{i.code}: {i.message}" for i in result.issues) or "no detail"
            raise ChaseRefused(f"the acceptance gate refused the round {number} snapshot ({issues})", "ACCEPT_CORPUS_REFUSED")

    try:
        finished = rounds.archive_round(
            ws, number=previous_number, arm=str(current.get("arm") or rounds.ARM_DATABASES),
            generation_id=generation_id, corpus_artifact_id=parent["artifact_id"], chase=current.get("chase"),
        )
    except rounds.RoundArchiveIncomplete as exc:
        append_event(
            ws, "SCREENING_ROUND_ARCHIVE_INCOMPLETE", str(exc), agent=agent,
            outputs=[f"{exc.backup}/{rel}" for rel in exc.moved],
            parameters={"round": previous_number, "chase": run_dir.name, "moved": exc.moved, "not_moved": exc.not_moved,
                        "snapshot_artifact_id": artifact["artifact_id"]},
            status="FAILED",
        )
        refused = ChaseRefused(str(exc), "ARCHIVE_INCOMPLETE")
        refused.details = {"backup_dir": exc.backup, "moved": exc.moved, "not_moved": exc.not_moved}
        raise refused from exc

    lit.mkdir(parents=True, exist_ok=True)
    (lit / "verified.json").write_text(_dump(verified_rows), encoding="utf-8")
    rounds.start_round(
        ws, finished, number=number, arm=rounds.ARM_CITATION_SEARCHING, chase=run_dir.name,
        corpus_artifact_id=artifact["artifact_id"],
    )
    accepted_at = _now()
    manifest["accepted"] = {
        "round": number, "artifact_id": artifact["artifact_id"], "accepted_at": accepted_at,
        "records": len(docs), "studies": len(artifact["data"]["studies"]),
    }
    (run_dir / "chase.json").write_text(_dump(manifest), encoding="utf-8")

    accepted = AcceptCorpusResult(
        artifact["artifact_id"], len(artifact["data"]["studies"]), len(docs), already_accepted=already,
        outcome_status=str(built.outcome.get("status", "SUCCESS")), warnings=tuple(built.outcome.get("warnings", ())),
    )
    _journal_snapshot_accepted(
        ws, accepted, f"from citation chase {run_dir.name} (screening round {number})", agent=agent, run=run_dir.name,
    )
    append_event(
        ws, "SCREENING_ROUND_ARCHIVED",
        f"Screening round {previous_number} ({finished['arm']}) archived under {finished['path']} before round {number}",
        agent=agent, inputs=[str(lit / "screening")], outputs=[f"{finished['path']}/{rel}" for rel in finished["moved"]],
        parameters={"round": previous_number, "arm": finished["arm"], "generation_id": generation_id,
                    "corpus_artifact_id": parent["artifact_id"], "moved": finished["moved"]},
    )
    append_event(
        ws, "CITATION_CHASE_ACCEPTED",
        f"Citation chase {run_dir.name} sent to screening as round {number}: {len(docs)} record(s), "
        f"{accepted.study_count} work(s), corpus {artifact['artifact_id']}",
        agent=agent, inputs=[str(run_dir / "new.json"), str(run_dir / "chase.json")],
        outputs=[str(lit / "verified.json"), str(rounds.rounds_path(ws)), str(run_dir / "chase.json")],
        parameters={"chase": run_dir.name, "round": number, "artifact_id": artifact["artifact_id"],
                    "parent_corpus": parent["artifact_id"], "archived": finished["moved"],
                    "archive_path": finished["path"], "method": "DETERMINISTIC_RULE"},
        metrics={"records": len(docs), "studies": accepted.study_count},
        status=accepted.outcome_status,
    )
    return ChaseAccepted(
        chase=run_dir.name, round=number, artifact_id=artifact["artifact_id"], study_count=accepted.study_count,
        record_count=len(docs), outcome_status=accepted.outcome_status, parent_corpus=parent["artifact_id"],
        archived=list(finished["moved"]), round_path=str(finished["path"]), already_accepted=already,
    )
