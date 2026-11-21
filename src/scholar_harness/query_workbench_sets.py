"""The query workbench's known papers, comparison sets and genesis copy (M11a Part B).

Spec: `docs/roadmap/milestones/M11a-query-workbench.md` (c), (d), (e), DoD 9 to 15.
Part A (``query_workbench``) holds the count log, the budget and the quota memory;
this module adds:

* **The seed check** (DoD 9, 10): each known paper's title and abstract come
  from the draft's first-search pool, a harvest, an earlier lookup, or one
  OpenAlex lookup by DOI per 50 papers (asked for, counted in the budget); the
  words decide which concepts it contains (``scholar_search.workbench.seed_check``).
* **The OpenAlex check** (DoD 11): one request per 50 DOIs combining an
  identifier filter with the query; off until a live run shows OpenAlex answers
  it (:func:`openalex_ids_enabled`, environment ``NEXUS_WORKBENCH_OPENALEX_IDS=1``).
* **Comparison sets** (DoD 12 to 14): a RIS or NBIB export from a database the
  app cannot query, stored as ``comparison/cmp_NNN/`` beside the count log,
  never in the corpus staging (``literature/raw/``), never accepted into a
  corpus; the report says how many of its records the query misses, by the
  strongest measure the place allows.
* **Genesis** (DoD 15): the draft's development is copied to
  ``audit/query_development/`` of the new workspace.

Nothing here is journaled except the genesis copy (one row).
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from scholar_search import workbench as wb

from . import query_workbench as qw

IDS_PER_REQUEST = 50
MAX_SETS = 5
MAX_SET_RECORDS = 5_000
MAX_FILE_BYTES = 50 * 1024 * 1024
PAGE_SIZE = 20
MAX_TERMS = 15
COMPARISON_DIR = "comparison"
SEED_TEXTS_FILE = "seed_texts.json"
SEED_CHECKS_FILE = "seed_checks.jsonl"
SET_FILE = "set.json"
CMP_ID = re.compile(r"cmp_\d{3}")
MEASURES = ("harvest", "openalex", "words")
SWITCH_ENV = "NEXUS_WORKBENCH_OPENALEX_IDS"

WORKBENCH_COMPARISON_FORMAT = "WORKBENCH_COMPARISON_FORMAT"
WORKBENCH_COMPARISON_TOO_LARGE = "WORKBENCH_COMPARISON_TOO_LARGE"
WORKBENCH_COMPARISON_FULL = "WORKBENCH_COMPARISON_FULL"
WORKBENCH_COMPARISON_NOT_FOUND = "WORKBENCH_COMPARISON_NOT_FOUND"
WORKBENCH_COMPARISON_MEASURE = "WORKBENCH_COMPARISON_MEASURE"


def openalex_ids_enabled() -> bool:
    """The OpenAlex identifier check (DoD 11): off until a live run confirms OpenAlex combines the filter and the search."""
    return os.environ.get(SWITCH_ENV, "") == "1"


def development_dir(log: qw.CountLog) -> Path:
    """The folder that holds the count log, the seed checks and the comparison sets."""
    return log.path.parent


def normalize_doi(value: Any) -> str:
    from scholar_search.recall import normalize_doi as norm

    return norm(str(value)) if value else ""


def title_key(title: Any) -> str:
    from scholar_search.dedup import title_key as key

    return key(str(title or ""))


def doc_record(doc: Any) -> dict[str, Any]:
    """``{doi, title, abstract, keywords, year}`` of a search Document."""
    eids = getattr(doc, "external_ids", None)
    return {
        "doi": normalize_doi(getattr(eids, "doi", None)) or None,
        "title": getattr(doc, "title", None) or None,
        "abstract": getattr(doc, "abstract", None) or None,
        "keywords": list(getattr(doc, "mesh_terms", None) or []),
        "year": getattr(doc, "year", None),
    }


def row_record(row: dict[str, Any]) -> dict[str, Any]:
    """The same from a stored record (a pool doc, a run's raw row, a verified row)."""
    eids = row.get("external_ids") if isinstance(row.get("external_ids"), dict) else {}
    keywords = row.get("keywords") or row.get("mesh_terms") or []
    return {
        "doi": normalize_doi(row.get("doi") or eids.get("doi")) or None,
        "title": row.get("title") or None,
        "abstract": row.get("abstract") or None,
        "keywords": list(keywords) if isinstance(keywords, list) else [],
        "year": row.get("year") or row.get("publication_year"),
    }


def _candidates(text: str) -> set[str]:
    """Terms of 1 to 3 words of ``text``: the M4d candidate rule (``recon.distiller``)."""
    from .recon.distiller import _term_candidates

    return _term_candidates((text or "").casefold())


def _status_of(exc: BaseException) -> tuple[str, str | None]:
    from scholar_search.engine import provider_error_code
    from scholar_search.exceptions import QuotaExhaustedError

    code = provider_error_code(exc)
    if isinstance(exc, QuotaExhaustedError):
        return "quota_used_up", code
    return qw.STATUS_BY_CODE.get(code or "", "failed"), code


def _gate(state: qw.SharedState, *, openalex_key: bool) -> str | None:
    """Why OpenAlex cannot be asked now (before any budget), or ``None``."""
    if not openalex_key:
        return "key_missing"
    if state.paused_until("openalex", qw.utcnow()):
        return "quota_used_up"
    return None


def _reserve(state: qw.SharedState, cost: int) -> None:
    """Take ``cost`` OpenAlex requests from today's budget, or refuse before anything is sent."""
    now = qw.utcnow()
    if cost and state.reserve({"openalex": cost}, now):
        raise qw.WorkbenchRefused(
            409, qw.WORKBENCH_BUDGET_SPENT, "Today's counting budget for openalex would be passed; nothing was sent.",
            details={"databases": [{"name": "openalex", **state.budget("openalex", now)}]},
        )


def _give_back(state: qw.SharedState, unused: int) -> None:
    if unused > 0:
        qw._quietly(state.spend, "openalex", -unused, qw.utcnow())


# --------------------------------------------------------------------------- OpenAlex by identifier


def ids_cost(dois: list[str]) -> int:
    return -(-len(dois) // IDS_PER_REQUEST)


async def _by_ids(call: str, dois: list[str], query: Any = None) -> dict[str, Any]:
    """``find_dois`` (with or without the query) or ``works_by_doi``, one request per 50; stops at the first failure."""
    from scholar_search import estimate as est

    found: list[Any] = []
    requests, status, code, resets_at = 0, "checked", None, None
    provider = est._provider("openalex")
    try:
        for start in range(0, len(dois), IDS_PER_REQUEST):
            chunk = dois[start:start + IDS_PER_REQUEST]
            requests += 1
            try:
                if call == "works":
                    found += await provider.works_by_doi(chunk)
                else:
                    found += await provider.find_dois(query, chunk)
            except Exception as exc:  # noqa: BLE001 - the database's failure is the answer's status
                status, code = _status_of(exc)
                resets_at = getattr(exc, "resets_at", None)
                break
    finally:
        await est._close(provider)
    return {"found": found, "requests": requests, "status": status, "error_code": code, "resets_at": resets_at}


def _log_ids(log: qw.CountLog, state: qw.SharedState, result: dict[str, Any], *, kind: str, query_key: str,
             scope: dict[str, Any]) -> None:
    if not result["requests"]:
        return
    now = qw.utcnow()
    log.append([{"shape": qw.LOG_SHAPE, "query_key": query_key, "provider": "openalex", "kind": kind,
                 "status": "read" if result["status"] == "checked" else "failed", "total": len(result["found"]),
                 "error_code": result["error_code"], "resets_at": result["resets_at"],
                 "counted_at": now.isoformat(), "requests": result["requests"], "key": None, **scope}])
    if result["status"] == "quota_used_up" and result["resets_at"]:
        qw._quietly(state.pause, "openalex", result["resets_at"], now)


# --------------------------------------------------------------------------- the seed check


def _texts_path(log: qw.CountLog) -> Path:
    return development_dir(log) / SEED_TEXTS_FILE


def seed_texts(log: qw.CountLog) -> dict[str, dict[str, Any]]:
    """Titles and abstracts looked up earlier, by DOI."""
    try:
        data = json.loads(_texts_path(log).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_texts(log: qw.CountLog, texts: dict[str, dict[str, Any]]) -> None:
    path = _texts_path(log)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{SEED_TEXTS_FILE}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(texts, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _seed_records(dois: list[str], known: list[dict[str, Any]], texts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    by_doi = {r["doi"]: r for r in known if r.get("doi")}
    out = []
    for doi in dois:
        rec = by_doi.get(doi) or texts.get(doi) or {}
        out.append({"doi": doi, "title": rec.get("title"), "abstract": rec.get("abstract"),
                    "keywords": rec.get("keywords") or []})
    return out


def _wanted(dois: list[str]) -> list[str]:
    return list(dict.fromkeys(d for d in (normalize_doi(x) for x in dois) if d))


def local_seed_check(version: wb.Version, dois: list[str], *, log: qw.CountLog, known: list[dict[str, Any]]) -> dict[str, Any]:
    """The seed check by the words only, from what is already here (no request): the fixed check reads it."""
    wanted = _wanted(dois)
    return wb.seed_check(version, _seed_records(wanted, known, seed_texts(log)), candidates=_candidates)


async def seeds(
    version: wb.Version, dois: list[str], *, log: qw.CountLog, state: qw.SharedState, known: list[dict[str, Any]],
    lookup: bool, openalex: bool, openalex_key: bool, dry_run: bool, scope: dict[str, Any],
) -> dict[str, Any]:
    """The seed check of ``dois``: by the words (always), and found or not by OpenAlex (asked for, behind the switch)."""
    wanted = _wanted(dois)
    texts = seed_texts(log)
    by_doi = {r["doi"] for r in known if r.get("doi") and wb.readable(r)}
    unknown = [d for d in wanted if d not in by_doi and d not in texts]
    lookup_cost = ids_cost(unknown) if lookup else 0
    gate = _gate(state, openalex_key=openalex_key) if (lookup_cost or openalex) else None
    check_status = ("not_asked" if not openalex else "switch_off" if not openalex_ids_enabled()
                    else gate or ("to_check" if dry_run else "checked"))
    check_cost = ids_cost(wanted) if check_status in ("to_check", "checked") else 0
    if gate is not None:
        lookup_cost = 0
    cost = {"lookup": lookup_cost, "openalex": check_cost}
    requests = 0
    databases = [{"name": "openalex", "status": check_status, "found": [], "not_found": []}]
    lookup_status = None
    if not dry_run and (lookup_cost or check_cost):
        _reserve(state, lookup_cost + check_cost)
        sent = 0
        try:
            if lookup_cost:
                got = await _by_ids("works", unknown)
                sent += got["requests"]
                _log_ids(log, state, got, kind="seed_lookup", query_key=version.query_key, scope=scope)
                lookup_status = got["status"]
                stamp = qw.utcnow().isoformat()
                for rec in (doc_record(d) for d in got["found"]):
                    if rec["doi"]:
                        texts[rec["doi"]] = {k: rec[k] for k in ("title", "abstract", "keywords", "year")} | {"looked_up_at": stamp}
                if got["status"] == "checked":
                    for doi in unknown:
                        texts.setdefault(doi, {"title": None, "abstract": None, "looked_up_at": stamp, "not_found": True})
                _save_texts(log, texts)
            if check_cost:
                hit = await _by_ids("find", wanted, wb.compile_version(version))
                sent += hit["requests"]
                _log_ids(log, state, hit, kind="seed_openalex", query_key=version.query_key, scope=scope)
                found = {normalize_doi(d) for d in hit["found"]}
                databases = [{"name": "openalex", "status": hit["status"],
                              "found": [d for d in wanted if d in found] if hit["status"] == "checked" else [],
                              "not_found": [d for d in wanted if d not in found] if hit["status"] == "checked" else []}]
        finally:
            _give_back(state, lookup_cost + check_cost - sent)
        requests = sent
    check = wb.seed_check(version, _seed_records(wanted, known, texts), candidates=_candidates)
    answer: dict[str, Any] = {
        "shape": "workbench.seeds-v1", "query_key": version.query_key, "dry_run": dry_run,
        "version": version.to_dict(), "cost": cost, "requests": requests, "lookup": lookup_status,
        "lookup_gate": gate if lookup else None, **check, "databases": databases,
        "others": "not_checked_here", "checked_at": qw.utcnow().isoformat(),
    }
    if not dry_run:
        path = development_dir(log) / SEED_CHECKS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        keep = ("query_key", "version", "seeds", "total", "read", "not_read", "use_every_concept", "missed",
                "warning", "databases", "checked_at")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({k: answer[k] for k in keep} | scope, ensure_ascii=False) + "\n")
    return answer


# --------------------------------------------------------------------------- comparison sets: stage, list, remove


def _sets_dir(log: qw.CountLog) -> Path:
    return development_dir(log) / COMPARISON_DIR


def _read_set(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads((path / SET_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _summary(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k != "records"}


def list_sets(log: qw.CountLog) -> list[dict[str, Any]]:
    """The staged comparison sets, oldest first, without their records."""
    root = _sets_dir(log)
    if not root.is_dir():
        return []
    out = []
    for path in sorted(p for p in root.iterdir() if p.is_dir() and CMP_ID.fullmatch(p.name)):
        data = _read_set(path)
        if data is not None:
            out.append(_summary(data))
    return out


def stage_set(
    log: qw.CountLog, *, file_name: str, content: bytes, database: str, string: str | None, exported_on: str | None,
) -> dict[str, Any]:
    """Store one export as a comparison set; refused before anything is kept (``WORKBENCH_COMPARISON_*``)."""
    from .corpus_accept import _IMPORTERS, detect_import_format

    if len(list_sets(log)) >= MAX_SETS:
        raise qw.WorkbenchRefused(409, WORKBENCH_COMPARISON_FULL,
                                  f"{MAX_SETS} comparison sets are staged, the most there can be. Remove one first.")
    if len(content) > MAX_FILE_BYTES:
        raise qw.WorkbenchRefused(422, WORKBENCH_COMPARISON_TOO_LARGE,
                                  f"{file_name} is over {MAX_FILE_BYTES // (1024 * 1024)} MB.")
    fmt = detect_import_format(file_name, content)
    root = _sets_dir(log)
    root.mkdir(parents=True, exist_ok=True)
    taken = [int(p.name[4:]) for p in root.iterdir() if p.is_dir() and CMP_ID.fullmatch(p.name)]
    set_id = f"cmp_{max(taken, default=0) + 1:03d}"
    tmp = root / f".{set_id}.{os.getpid()}.tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    try:
        original = tmp / f"export.{fmt}"
        original.write_bytes(content)
        try:
            docs = list(_IMPORTERS[fmt]().parse(original))
        except Exception as exc:  # noqa: BLE001 - an unreadable file is a refusal, never a crash
            raise qw.WorkbenchRefused(422, WORKBENCH_COMPARISON_FORMAT,
                                      "This file is not RIS or NBIB: it could not be read.") from exc
        docs = [d for d in docs if str(getattr(d, "title", "") or "").strip() and d.title != "Untitled"]
        if not docs:
            raise qw.WorkbenchRefused(422, WORKBENCH_COMPARISON_FORMAT, "This file is not RIS or NBIB: no record was found.")
        if len(docs) > MAX_SET_RECORDS:
            raise qw.WorkbenchRefused(422, WORKBENCH_COMPARISON_TOO_LARGE,
                                      f"This export has {len(docs)} records, more than {MAX_SET_RECORDS}.")
        now = qw.utcnow().isoformat()
        records = [doc_record(d) for d in docs]
        data = {
            "id": set_id, "database": " ".join(database.split()), "string": (string or "").strip() or None,
            "exported_on": exported_on or now[:10], "staged_at": now, "file_name": file_name, "format": fmt,
            "records_count": len(records), "no_abstract": sum(1 for r in records if not r["abstract"]),
            "with_doi": sum(1 for r in records if r["doi"]), "records": records,
        }
        (tmp / SET_FILE).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, root / set_id)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    log.append([{"shape": qw.LOG_SHAPE, "kind": "comparison_staged", "comparison": set_id, "database": data["database"],
                 "records": len(records), "status": "staged", "counted_at": data["staged_at"], "requests": 0,
                 "key": None}])
    return _summary(data)


def _set_path(log: qw.CountLog, set_id: str) -> Path:
    path = _sets_dir(log) / set_id
    if not CMP_ID.fullmatch(set_id or "") or _read_set(path) is None:
        raise qw.WorkbenchRefused(404, WORKBENCH_COMPARISON_NOT_FOUND, f"There is no comparison set {set_id}.")
    return path


def remove_set(log: qw.CountLog, set_id: str) -> None:
    """Delete one set and leave one line in the count log."""
    path = _set_path(log, set_id)
    data = _read_set(path) or {}
    shutil.rmtree(path)
    log.append([{"shape": qw.LOG_SHAPE, "kind": "comparison_removed", "comparison": set_id,
                 "database": data.get("database"), "records": data.get("records_count"), "status": "removed",
                 "counted_at": qw.utcnow().isoformat(), "requests": 0, "key": None}])


# --------------------------------------------------------------------------- the report


def missing_terms(version: wb.Version, records: list[dict[str, Any]], *, limit: int = MAX_TERMS) -> list[dict[str, Any]]:
    """Terms of 1 to 3 words (the M4d candidate rule) in at least two of ``records`` and related to no query term."""
    seen: dict[str, int] = {}
    for record in records:
        for term in _candidates(wb.record_text(record)):
            seen[term] = seen.get(term, 0) + 1
    terms = [(t, n) for t, n in seen.items() if n >= 2 and not wb.related(t, version)]
    # Most records first; at equal counts the shorter term (a single word is the likelier synonym).
    terms.sort(key=lambda item: (-item[1], len(item[0].split()), item[0]))
    return [{"term": t, "records": n, "of": len(records)} for t, n in terms[:limit]]


def harvest_records(ws: Path | None, run: str | None = None) -> tuple[str | None, list[dict[str, Any]]]:
    """``(label, records)`` the query found: the accepted corpus (``corpus``), else a run's records (newest by default)."""
    if ws is None:
        return None, []
    from .corpus_accept import _accepted_snapshot

    lit = Path(ws) / "literature"
    if _accepted_snapshot(Path(ws)):
        try:
            rows = json.loads((lit / "verified.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rows = []
        return "corpus", [row_record(r) for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []
    runs = lit / "search_runs"
    names = sorted((p.name for p in runs.iterdir() if p.is_dir() and re.fullmatch(r"run_\d{3,}", p.name)),
                   key=lambda n: int(n[4:])) if runs.is_dir() else []
    if run is not None and run not in names:
        return None, []
    chosen = run or (names[-1] if names else None)
    if chosen is None:
        return None, []
    try:
        rows = json.loads((runs / chosen / "raw.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        rows = []
    if isinstance(rows, dict):
        rows = rows.get("documents") or rows.get("records") or []
    return chosen, [row_record(r) for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def _empty_page(answer: dict[str, Any]) -> dict[str, Any]:
    return answer | {"missing": [], "missing_count": None, "page": 1, "pages": 0, "terms": []}


async def report(
    log: qw.CountLog, set_id: str, version: wb.Version, *, measure: str, page: int, state: qw.SharedState,
    harvest: tuple[str | None, list[dict[str, Any]]] | None, openalex_key: bool, dry_run: bool, scope: dict[str, Any],
) -> dict[str, Any]:
    """``{n} of {m} {database} records are missing from what your query finds``, by one measure (DoD 13, 14).

    ``harvest``: in the harvest or the accepted corpus, by DOI or normalised
    title, no request (Plan only). ``openalex``: records with a DOI, one request
    per 50 with the query and one per 50 without it (behind the switch).
    ``words``: the query's words in the title, abstract and keywords, no request.
    """
    data = _read_set(_set_path(log, set_id)) or {}
    records: list[dict[str, Any]] = [dict(r) for r in data.get("records") or []]
    answer: dict[str, Any] = {
        "shape": "workbench.comparison-report-v1", "query_key": version.query_key, "set": _summary(data),
        "measure": measure, "version": version.to_dict(), "total": len(records), "dry_run": dry_run,
        "no_abstract": sum(1 for r in records if not r.get("abstract")), "cost": 0, "requests": 0,
        "status": "measured", "against": None, "not_checked": 0, "not_in_database": None,
    }
    if measure == "harvest":
        label, found_records = harvest if harvest is not None else (None, [])
        if label is None:
            raise qw.WorkbenchRefused(409, WORKBENCH_COMPARISON_MEASURE,
                                      "There is no harvest or accepted corpus to compare with here.")
        dois = {r["doi"] for r in found_records if r.get("doi")}
        titles = {k for r in found_records if (k := title_key(r.get("title")))}
        answer["against"] = {"label": label, "records": len(found_records)}
        missing = [r for r in records if not ((r.get("doi") and r["doi"] in dois) or title_key(r.get("title")) in titles)]
    elif measure == "openalex":
        with_doi = [r for r in records if r.get("doi")]
        dois = list(dict.fromkeys(r["doi"] for r in with_doi))
        answer["not_checked"] = len(records) - len(with_doi)
        why = "switch_off" if not openalex_ids_enabled() else _gate(state, openalex_key=openalex_key)
        if why is not None:
            return _empty_page(answer | {"status": why})
        cost = 2 * ids_cost(dois)
        answer["cost"] = cost
        if dry_run:
            return _empty_page(answer | {"status": "to_check"})
        _reserve(state, cost)
        sent = 0
        try:
            query = wb.compile_version(version)
            hit = await _by_ids("find", dois, query)
            sent += hit["requests"]
            _log_ids(log, state, hit, kind="comparison_openalex", query_key=version.query_key, scope=scope)
            held = {"status": "checked", "found": [], "requests": 0}
            if hit["status"] == "checked":
                held = await _by_ids("find", dois, None)
                sent += held["requests"]
                _log_ids(log, state, held, kind="comparison_openalex_any", query_key=version.query_key, scope=scope)
        finally:
            _give_back(state, cost - sent)
        answer["requests"] = sent
        if hit["status"] != "checked" or held["status"] != "checked":
            return _empty_page(answer | {"status": hit["status"] if hit["status"] != "checked" else held["status"]})
        found = {normalize_doi(d) for d in hit["found"]}
        inside = {normalize_doi(d) for d in held["found"]}
        missing = [r for r in with_doi if r["doi"] not in found]
        answer["not_in_database"] = sum(1 for r in missing if r["doi"] not in inside)
    elif measure == "words":
        missing = [r for r in records if not wb.matches(version, wb.record_text(r))]
    else:
        raise qw.WorkbenchRefused(422, WORKBENCH_COMPARISON_MEASURE, f"Unknown measure {measure!r}.")
    pages = max(1, -(-len(missing) // PAGE_SIZE))
    page = min(max(1, page), pages)
    shown = missing[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]
    answer.update(
        missing_count=len(missing), page=page, pages=pages,
        missing=[{"title": r.get("title"), "doi": r.get("doi"), "year": r.get("year"),
                  "lacks": wb.lacking(version, wb.record_text(r)) if wb.readable(r) else [],
                  "no_abstract": not r.get("abstract")} for r in shown],
        terms=missing_terms(version, missing),
    )
    return answer


# --------------------------------------------------------------------------- genesis: the development goes into the workspace


def development_files(source: Path | None) -> list[str]:
    """The workspace paths genesis writes for a draft's query development (none when there is none)."""
    if source is None or not Path(source).is_dir():
        return []
    out = [f"audit/{qw.DEVELOPMENT_DIR}/{name}" for name in (qw.COUNTS_FILE, SEED_CHECKS_FILE, SEED_TEXTS_FILE)
           if (Path(source) / name).is_file()]
    sets = Path(source) / COMPARISON_DIR
    if sets.is_dir() and any(p.is_dir() and CMP_ID.fullmatch(p.name) for p in sets.iterdir()):
        out.append(f"audit/{qw.DEVELOPMENT_DIR}/{COMPARISON_DIR}/")
    return out


def copy_development(source: Path | None, workspace: Path) -> dict[str, Any]:
    """Copy a draft's count log, seed checks, looked-up texts and comparison sets under ``audit/query_development/``.

    A replacement keeps what the workspace already holds: the logs are
    appended, the texts merged, the comparison sets numbered after the
    existing ones (each keeps its draft id as ``draft_id``).
    """
    copied: dict[str, Any] = {"counts": 0, "seed_checks": 0, "comparison_sets": 0, "files": []}
    if source is None or not Path(source).is_dir():
        return copied
    source = Path(source)
    target = Path(workspace) / "audit" / qw.DEVELOPMENT_DIR
    target.mkdir(parents=True, exist_ok=True)
    for name, key in ((qw.COUNTS_FILE, "counts"), (SEED_CHECKS_FILE, "seed_checks")):
        path = source / name
        if path.is_file():
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            with open(target / name, "a", encoding="utf-8") as handle:
                for line in lines:
                    handle.write(line + "\n")
            copied[key] = len(lines)
            copied["files"].append(f"audit/{qw.DEVELOPMENT_DIR}/{name}")
    if (source / SEED_TEXTS_FILE).is_file():
        try:
            new = json.loads((source / SEED_TEXTS_FILE).read_text(encoding="utf-8"))
        except ValueError:
            new = {}
        try:
            old = json.loads((target / SEED_TEXTS_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            old = {}
        merged = {**(old if isinstance(old, dict) else {}), **(new if isinstance(new, dict) else {})}
        (target / SEED_TEXTS_FILE).write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        copied["files"].append(f"audit/{qw.DEVELOPMENT_DIR}/{SEED_TEXTS_FILE}")
    sets = source / COMPARISON_DIR
    if sets.is_dir():
        out = target / COMPARISON_DIR
        out.mkdir(exist_ok=True)
        number = max((int(p.name[4:]) for p in out.iterdir() if p.is_dir() and CMP_ID.fullmatch(p.name)), default=0)
        for path in sorted(p for p in sets.iterdir() if p.is_dir() and CMP_ID.fullmatch(p.name)):
            number += 1
            new_id = f"cmp_{number:03d}"
            shutil.copytree(path, out / new_id)
            data = _read_set(out / new_id)
            if data is not None and data.get("id") != new_id:
                data["draft_id"], data["id"] = data.get("id"), new_id
                (out / new_id / SET_FILE).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            copied["comparison_sets"] += 1
        if copied["comparison_sets"]:
            copied["files"].append(f"audit/{qw.DEVELOPMENT_DIR}/{COMPARISON_DIR}/")
    return copied
