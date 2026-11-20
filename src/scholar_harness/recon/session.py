"""Recon sessions: one engine for the CLI wizard, the MCP tools and the console (M4c).

A recon session is ``<recon root>/sessions/<rec_id>/session.json`` plus its
content-addressed ``pool_<sha>.json`` and ``distilled_<sha>.json`` artifacts
(M0.5, T5.4). The session id is the inception draft's id (M4a), so a draft
and its recon share one ``rec_<hex>``.

Before M4c this store lived in ``scholar_agent/server.py`` and the CLI wizard
probed without a session. Now the three front doors call :class:`ReconSessions`:

* :meth:`ReconSessions.probe` runs one probe on the M3a providers through
  :class:`~scholar_harness.recon.engine.ReconEngine` and records it with its
  pool fingerprint, ``created_at``, status and one leg per provider (INC-09);
* :meth:`ReconSessions.distill`, :meth:`ReconSessions.directions` and
  :meth:`ReconSessions.delta` read the session's latest pool.

Refusals are :class:`ReconRefused` with a code and a plain sentence.

One session has one writer at a time: the console runs one job per draft, and
a CLI or MCP run on the same ``rec_`` id at the same moment may overwrite the
other's last probe record (the pools themselves are content-addressed).

INC-21: :func:`term_evidence` anchors a term only on records whose title or
abstract contains it, and keeps the number of records the provider returned
(``hits``) apart from the number that contain it (``observed_in``).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_search.config import settings
from scholar_search.engine import MailtoNotSet

from .distiller import distill_pool
from .engine import (
    DEFAULT_PROVIDERS,
    KEY_SETTINGS,
    POOL_COMPLETE,
    POOL_EMPTY,
    POOL_MAX,
    ProgressFn,
    ReconEngine,
    SearchFn,
)
from .gates import compute_pool_sufficiency, compute_topic_purity
from .sample import effective_pool, paper_key

SESSION_ID_RE = re.compile(r"^rec_[0-9a-f]{6,64}$")

#: Refusal codes (also in ``console/refusals.py``).
MAILTO_NOT_SET = "MAILTO_NOT_SET"
RECON_SESSION_INVALID = "RECON_SESSION_INVALID"
RECON_SESSION_NOT_FOUND = "RECON_SESSION_NOT_FOUND"
RECON_NO_POOL = "RECON_NO_POOL"
POOL_EMPTY_REFUSED = "POOL_EMPTY"
POOL_TOO_SMALL = "POOL_TOO_SMALL"
PROVIDERS_FAILED = "PROVIDERS_FAILED"
NARROW_BUDGET_SPENT = "NARROW_BUDGET_SPENT"
DIRECTION_UNKNOWN = "DIRECTION_UNKNOWN"
NO_DIRECTION = "NO_DIRECTION"

#: The wizard allows one narrower search after the first probe (``_DELTA_PROBE_CHOICE``).
NARROW_BUDGET = 1
#: Gap follow-ups per delta (M0.4).
DELTA_BUDGET = 3


class ReconRefused(RuntimeError):
    """A recon step was refused; ``code`` names why, ``status`` is the HTTP status.

    A ``RuntimeError`` so callers that only know the adapter's error envelope
    (the MCP tools) report it without importing this module.
    """

    def __init__(self, code: str, message: str, status: int = 409, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def new_session_id() -> str:
    return "rec_" + uuid.uuid4().hex


def pool_fingerprint(pool: dict[str, Any]) -> str:
    """``sha256:`` of the pool's canonical JSON (sorted keys, no whitespace)."""
    canonical = json.dumps(pool, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- INC-21

_NON_WORD = re.compile(r"[^0-9a-z]+")


def _normalize(text: str) -> str:
    return " " + _NON_WORD.sub(" ", (text or "").casefold()).strip() + " "


def term_occurs(term: str, text: str) -> bool:
    """True when ``term`` occurs in ``text`` as whole words (case, hyphens and punctuation ignored)."""
    needle = _normalize(term)
    return needle.strip() != "" and needle in _normalize(text)


def term_evidence(pool: dict[str, Any], term: str) -> dict[str, Any]:
    """``hits`` (records returned), ``observed_in`` (records containing ``term``) and their DOIs.

    Only a record with a DOI whose title or abstract contains the term anchors it.
    """
    docs = [d for d in pool.get("docs") or [] if isinstance(d, dict)]
    dois: list[str] = []
    for doc in docs:
        doi = doc.get("doi")
        text = f"{doc.get('title') or ''} {doc.get('abstract') or ''}"
        if doi and term_occurs(term, text) and doi not in dois:
            dois.append(str(doi))
    return {"hits": len(docs), "observed_in": len(dois), "anchor_dois": sorted(dois)}


# --------------------------------------------------------------------------- store


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    # A unique temporary name, so two writers never collide on it (review #6).
    tmp = path.with_suffix(f"{path.suffix}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _content_sha(payload: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def key_state() -> dict[str, bool]:
    """Whether each keyed database has its key set (never the key itself)."""
    return {
        "openalex_key_set": bool(getattr(settings, "openalex_key", None)),
        "s2_key_set": bool(getattr(settings, "s2_key", None)),
    }


def _legs_summary(
    legs: list[dict[str, Any]], query: str | None = None, semantic: bool = False
) -> list[dict[str, Any]]:
    """One line per database: its status, counts, failure code and notes (INC-09, M4d DoD 1).

    ``key_set`` is ``True``/``False`` for a database that takes a key and
    ``None`` for one that does not, as it was when the probe ran.
    ``executed_query`` is the query the database received (M10a), ``None`` when not recorded.
    ``shorten`` (H-provenance-s2) says whether this database's empty answer may come
    from a long keyword query (:func:`leg_says_shorten`) the researcher sent. A leg
    with its own ``query`` is a follow-up of a gap check, a term the engine chose,
    so it never says shorten (the advice is to edit the query above).
    """
    keep = ("provider", "status", "executed_query", "reported_total", "fetched", "cap", "cap_hit", "error", "error_code")
    out = []
    for leg in legs:
        row = {k: leg.get(k) for k in keep}
        row["notes"] = list(leg.get("notes") or [])
        setting = KEY_SETTINGS.get(str(leg.get("provider")))
        if "key_set" in leg:  # stamped by the engine when the leg ran (a cached pool keeps it)
            row["key_set"] = leg["key_set"]
        else:
            row["key_set"] = bool(getattr(settings, setting, None)) if setting else None
        row["shorten"] = "query" not in leg and leg_says_shorten(query, leg, semantic)
        out.append(row)
    return out


class ReconSessions:
    """Recon sessions under one recon root, probing through one :class:`ReconEngine`."""

    def __init__(
        self,
        root: Path | str | None = None,
        search_fn: SearchFn | None = None,
        engine: ReconEngine | None = None,
    ) -> None:
        self.engine = engine if engine is not None else ReconEngine(cache_root=root, search_fn=search_fn)
        self.root = Path(self.engine.cache_root)

    # -- sessions ---------------------------------------------------------

    def session_root(self, session_id: str) -> Path:
        if not isinstance(session_id, str) or SESSION_ID_RE.fullmatch(session_id) is None:
            raise ReconRefused(
                RECON_SESSION_INVALID,
                "malformed session_id (expected 'rec_' followed by hex digits)",
                status=422,
            )
        path = (self.root / "sessions" / session_id).resolve()
        if any(part.lower() == "workspaces" for part in path.parts):
            raise ReconRefused(RECON_SESSION_INVALID, f"refusing to write under workspaces/: {path}", status=422)
        return path

    def exists(self, session_id: str) -> bool:
        return (self.session_root(session_id) / "session.json").is_file()

    def blank(self, session_id: str, topic: str) -> dict[str, Any]:
        stamp = _now()
        return {
            "session_id": session_id,
            "topic": topic,
            "cache_keys": [],
            "pools": [],
            "probes": [],
            "created_at": stamp,
            "updated_at": stamp,
        }

    def load(self, session_id: str) -> dict[str, Any]:
        path = self.session_root(session_id) / "session.json"
        if not path.is_file():
            raise ReconRefused(RECON_SESSION_NOT_FOUND, f"session not found: {session_id}", status=404)
        session = json.loads(path.read_text(encoding="utf-8"))
        session.setdefault("probes", [])
        return session

    def save(self, session: dict[str, Any]) -> Path:
        session["updated_at"] = _now()
        root = self.session_root(str(session["session_id"]))
        root.mkdir(parents=True, exist_ok=True)
        path = root / "session.json"
        _atomic_write_json(path, session)
        return path

    def persist(self, session_id: str, prefix: str, payload: dict[str, Any]) -> Path:
        """Content-addressed artifact: the same payload gives the same file, written once."""
        root = self.session_root(session_id)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{prefix}_{_content_sha(payload)}.json"
        if not path.is_file():
            _atomic_write_json(path, payload)
        return path.resolve()

    def latest_pool(self, session_id: str) -> tuple[dict[str, Any], Path]:
        session = self.load(session_id)
        if not session["pools"]:
            raise ReconRefused(RECON_NO_POOL, f"session {session_id} has no pool; run a probe first", status=409)
        path = Path(session["pools"][-1])
        return json.loads(path.read_text(encoding="utf-8")), path

    def effective(self, session_id: str, exclusions: Any = None) -> tuple[dict[str, Any], dict[str, Any], Path]:
        """``(effective pool, raw pool, pool file)`` of the latest pool (M10b Part C).

        ``exclusions`` are the keys the draft left out (``sample.keys_of``);
        ``None`` or empty reads the sample as the probe stored it.
        """
        pool, path = self.latest_pool(session_id)
        return effective_pool(pool, exclusions), pool, path

    # -- probe --------------------------------------------------------------

    async def probe(
        self,
        query: str,
        *,
        session_id: str | None = None,
        topic: str | None = None,
        purpose: str = "topic",
        year_min: int = 2000,
        year_max: int | None = None,
        max_results: int = 25,
        semantic: bool = False,
        refresh: bool = False,
        providers: list[str] | None = None,
        progress: ProgressFn | None = None,
        languages: list[str] | None = None,
    ) -> dict[str, Any]:
        """Probe ``query``, record the pool in the session and return its summary.

        ``MAILTO_NOT_SET`` refuses before any request. An empty or partial pool
        is recorded (it is what the providers answered) but never cached.
        """
        sid = session_id or new_session_id()
        self.session_root(sid)  # validate before any request
        asked = list(DEFAULT_PROVIDERS) if providers is None else list(providers)
        try:
            pool, _cache_file, cached = await self.engine.probe_pool(
                query,
                providers=asked,
                year_min=year_min,
                year_max=year_max,
                max_results=max_results,
                semantic=semantic,
                refresh=refresh,
                progress=progress,
                languages=languages,
            )
            if cached and pool.get("query") != query:
                # The cache key casefolds and collapses whitespace, but Semantic Scholar
                # and arXiv read AND/OR/NOT only in capitals: a query that differs in
                # letter case is another search (M10a review round 2, item 2).
                pool, _cache_file, cached = await self.engine.probe_pool(
                    query,
                    providers=asked,
                    year_min=year_min,
                    year_max=year_max,
                    max_results=max_results,
                    semantic=semantic,
                    refresh=True,
                    progress=progress,
                    languages=languages,
                )
        except MailtoNotSet as exc:
            raise ReconRefused(
                MAILTO_NOT_SET,
                "A search needs a contact email for the literature databases. Set SCHOLAR_MAILTO "
                "for the console (environment or .env) and start it again.",
                status=409,
            ) from exc
        artifact = self.persist(sid, "pool", pool)
        session = self.load(sid) if self.exists(sid) else self.blank(sid, topic or query)
        if topic:
            session["topic"] = topic
        record = {
            "purpose": purpose,
            "query": query,
            "providers": asked,  # M10a: the databases asked, in order
            "pool_path": str(artifact),
            "fingerprint": pool_fingerprint(pool),
            "created_at": pool.get("created_at"),
            "cache_key": str(pool.get("cache_key") or ""),
            "status": pool.get("status", POOL_COMPLETE),
            "n_docs": len(pool.get("docs") or []),
            "served_from_cache": cached,
            "year_min": pool.get("year_min"),
            "year_max": pool.get("year_max"),
            "languages": pool.get("languages"),
            "legs": _legs_summary(pool.get("legs") or [], pool.get("query"), bool(pool.get("semantic"))),
            "at": _now(),
        }
        session["probes"].append(record)
        if record["cache_key"] and record["cache_key"] not in session["cache_keys"]:
            session["cache_keys"].append(record["cache_key"])
        # An empty pool is recorded as a probe but never becomes the session's
        # latest pool: distill, directions and bindings keep the last usable one.
        if record["n_docs"]:
            if str(artifact) in session["pools"]:  # the same pool again: make it the latest
                session["pools"].remove(str(artifact))
            session["pools"].append(str(artifact))
        self.save(session)
        return {"session_id": sid, **record}

    # -- read the latest pool -------------------------------------------------

    def current(self, session_id: str) -> dict[str, Any]:
        """The session, its latest probe and how many narrower searches are left."""
        session = self.load(session_id)
        probes = session.get("probes") or []
        for probe in probes:  # a probe recorded before M10a reads back with these keys as null
            probe.setdefault("providers", None)
            for leg in probe.get("legs") or []:
                leg.setdefault("executed_query", None)
        narrowed = sum(1 for p in probes if p.get("purpose") == "narrower")
        return {
            "session_id": session_id,
            "topic": session.get("topic"),
            "latest": probes[-1] if probes else None,
            "probes": probes,
            "narrower_left": max(0, NARROW_BUDGET - narrowed),
        }

    def distill(
        self, session_id: str, lexicon: Any | None = None, artifact_prefix: str = "distilled", exclusions: Any = None,
    ) -> dict[str, Any]:
        """Distill the latest pool and score it: the Explore screen's data.

        Over the effective pool (M10b Part C): the papers the draft left out
        (``exclusions``) are not read, and the reserve refills the sample.
        """
        session = self.load(session_id)
        pool, raw, pool_path = self.effective(session_id, exclusions)
        query = _latest_query(session) or session.get("topic")
        distilled = distill_pool(pool, lexicon=lexicon, query_text=query)
        terms_file = self.persist(session_id, artifact_prefix, distilled)
        docs = pool.get("docs") or []
        directions = directions_for(distilled, pool)
        anchors: dict[str, int] = {}
        for d in directions:
            for doi in d["anchor_dois"]:
                anchors[doi] = anchors.get(doi, 0) + 1
        papers = [
            {
                # M10b Part C: the engine's key (DOI, else the pool id) and the left-out paper it replaced.
                "key": paper_key(doc),
                "doi": doc.get("doi"),
                "title": doc.get("title"),
                "year": doc.get("year"),
                "provider": doc.get("provider"),
                "directions_anchored": anchors.get(doc.get("doi") or "", 0),
                "added_for": doc.get("added_for"),
            }
            for doc in docs
        ]
        papers.sort(key=lambda p: (-p["directions_anchored"], str(p["title"] or "")))
        return {
            "session_id": session_id,
            "pool": _pool_summary(raw, pool_path, pool),
            "terms_path": str(terms_file),
            "distilled": distilled,
            "qei": distilled.get("qei"),
            "gates": {
                "pool": compute_pool_sufficiency(len(docs)),
                "purity": compute_topic_purity(distilled.get("topics") or []),
            },
            "papers": papers,
        }

    def directions(self, session_id: str, exclusions: Any = None) -> dict[str, Any]:
        """Up to three directions with >= 2 anchor papers each, from the latest (effective) pool."""
        pool, raw, pool_path = self.effective(session_id, exclusions)
        session = self.load(session_id)
        distilled = distill_pool(pool, query_text=_latest_query(session) or session.get("topic"))
        docs = pool.get("docs") or []
        return {
            "session_id": session_id,
            "pool": _pool_summary(raw, pool_path, pool),
            "gates": {
                "pool": compute_pool_sufficiency(len(docs)),
                "purity": compute_topic_purity(distilled.get("topics") or []),
            },
            "directions": directions_for(distilled, pool),
            "narrower_left": self.current(session_id)["narrower_left"],
            "distilled": distilled,
        }

    async def delta(
        self,
        session_id: str,
        followups: int = DELTA_BUDGET,
        year_min: int = 2000,
        year_max: int | None = None,
    ) -> dict[str, Any]:
        """The gap check: up to three follow-up probes for thin schools, merged into the pool.

        The follow-ups (if any) ask the databases of the pool they extend
        (:func:`pool_providers`), as the narrower search does: its recorded
        ``providers``, or for a pool stored before M10a, which names none, those
        of the latest probe that recorded them and found records, else the four
        defaults. The delta record and the merged pool name exactly that list
        (a pre-M10a pool gains it), with or without follow-ups. A later probe
        that found nothing left the pool as it was, so its databases never count.
        """
        from .adaptive import execute_followups

        session = self.load(session_id)
        pool, _path = self.latest_pool(session_id)
        distilled = distill_pool(pool)
        budget = max(0, min(int(followups), DELTA_BUDGET))
        asked = pool_providers(pool, session)
        try:
            result = await execute_followups(
                pool, distilled, self.engine, max_followups=budget, providers=asked,
                year_min=year_min, year_max=year_max,
            )
        except MailtoNotSet as exc:
            raise ReconRefused(
                MAILTO_NOT_SET,
                "A search needs a contact email for the literature databases. Set SCHOLAR_MAILTO "
                "for the console (environment or .env) and start it again.",
            ) from exc
        merged_pool, merged_terms = result["pool"], result["distilled"]
        followup_pools = result.get("followup_pools") or []
        if followup_pools:
            # INC-09 provenance (review #3): the merged pool is a new pool. It keeps
            # the original's legs and every follow-up's legs (each with its query),
            # is partial when any of them failed, and has its own time.
            legs = [dict(leg) for leg in pool.get("legs") or []]
            for fp in followup_pools:
                legs += [{**leg, "query": fp.get("query")} for leg in fp.get("legs") or []]
            partial = pool.get("status") == "partial" or any(
                fp.get("status") == "partial" or any(leg.get("status") == "failed" for leg in fp.get("legs") or [])
                for fp in followup_pools
            )
            merged_pool = {
                **merged_pool,
                "status": "partial" if partial else POOL_COMPLETE,
                "legs": legs,
                "created_at": _now(),
                "merged_from": {
                    "created_at": pool.get("created_at"),
                    "followups": [{k: fp.get(k) for k in ("query", "status", "created_at", "cache_key")} for fp in followup_pools],
                },
            }
        if not pool.get("providers"):
            # A pool stored before M10a names no databases: the merged pool names
            # those asked, so the record, the merged pool and distill agree.
            merged_pool = {**merged_pool, "providers": asked}
        pool_file = self.persist(session_id, "pool", merged_pool)
        terms_file = self.persist(session_id, "distilled", merged_terms)
        merged_keys: list[str] = []
        for key in [str(pool.get("cache_key") or ""), *[str(k) for k in result.get("cache_keys_merged") or []]]:
            if key and key not in merged_keys:
                merged_keys.append(key)
        for key in merged_keys:
            if key not in session["cache_keys"]:
                session["cache_keys"].append(key)
        if str(pool_file) in session["pools"]:  # the same pool again: make it the latest
            session["pools"].remove(str(pool_file))
        session["pools"].append(str(pool_file))
        session["probes"].append({
            "purpose": "delta",
            "query": None,
            # The databases of the pool, which the follow-ups (if any) asked, in order.
            "providers": asked,
            "pool_path": str(pool_file),
            "fingerprint": pool_fingerprint(merged_pool),
            "created_at": merged_pool.get("created_at"),
            "cache_key": str(merged_pool.get("cache_key") or ""),
            "status": merged_pool.get("status", POOL_COMPLETE),
            "n_docs": len(merged_pool.get("docs") or []),
            "served_from_cache": False,
            "legs": _legs_summary(merged_pool.get("legs") or [], pool.get("query"), bool(pool.get("semantic"))),
            "at": _now(),
        })
        self.save(session)
        return {
            "session_id": session_id,
            "merged_cache_keys": merged_keys,
            "followups": [
                {
                    "term": str(item.get("term") or ""),
                    "reason": str(item.get("reason") or ""),
                    "confidence": {"label": "gap", "detail": str(item.get("reason") or "")},
                    "school_n": int(item.get("school_n") or 0),
                    "corpus_total": int(item.get("corpus_total", -1)),
                    "saturation_label": str(item.get("saturation_label") or "unknown"),
                }
                for item in result.get("followups") or []
            ],
            "pool_path": str(pool_file),
            "terms_path": str(terms_file),
            "pool_fingerprint": pool_fingerprint(merged_pool),
            "topics": merged_terms.get("topics") or [],
            "dropped_n": int(result.get("dropped_n") or 0),
            "pool_size_before": len(pool.get("docs") or []),
            "pool_size_after": len(merged_pool.get("docs") or []),
        }


def pool_providers(pool: dict[str, Any], session: dict[str, Any]) -> list[str]:
    """The databases a narrower search or the gap check asks: those of the pool it narrows or extends.

    A pool stored before M10a names none; then those of the latest probe that
    recorded them and found records, else the four (:func:`latest_providers`).
    """
    if pool.get("providers"):
        return list(pool["providers"])
    return latest_providers(session)


def latest_providers(session: dict[str, Any]) -> list[str]:
    """The databases of the latest probe that recorded them and found records, in order; the four by default.

    The fallback of :func:`pool_providers` for a pool stored before M10a. A
    probe that found nothing (empty or failed) never became the session's
    pool, so its databases do not count.
    """
    for probe in reversed(session.get("probes") or []):
        if probe.get("providers") and probe.get("n_docs"):
            return list(probe["providers"])
    return list(DEFAULT_PROVIDERS)


def _latest_query(session: dict[str, Any]) -> str | None:
    for probe in reversed(session.get("probes") or []):
        if probe.get("query"):
            return str(probe["query"])
    return None


def _pool_summary(pool: dict[str, Any], path: Path, effective: dict[str, Any] | None = None) -> dict[str, Any]:
    """The pool's summary; ``fingerprint`` is the raw pool's, ``n_docs`` the effective pool's (M10b Part C)."""
    counted = effective if effective is not None else pool
    return {
        "path": str(path),
        "fingerprint": pool_fingerprint(pool),
        "created_at": pool.get("created_at"),
        "cache_key": str(pool.get("cache_key") or ""),
        "status": pool.get("status", POOL_COMPLETE),
        "query": pool.get("query"),
        "providers": pool.get("providers"),
        "year_min": pool.get("year_min"),
        "year_max": pool.get("year_max"),
        "languages": pool.get("languages"),
        "semantic": pool.get("semantic"),
        "n_docs": len(counted.get("docs") or []),
        "n_docs_raw": len(pool.get("docs") or []),
        "reserve_n": len(pool.get("reserve") or []),
        "max_docs": POOL_MAX,
        "legs": _legs_summary(pool.get("legs") or [], pool.get("query"), bool(pool.get("semantic"))),
    }


def directions_for(distilled: dict[str, Any], pool: dict[str, Any]) -> list[dict[str, Any]]:
    """The wizard's directions whose concept occurs in at least two records (INC-21).

    Each carries ``observed_in`` (records whose title or abstract contains the
    concept, out of ``n_docs``), its anchor DOIs by that same rule, and the
    schools that share them. The wizard's "pool vocabulary" fallback, which
    joins unrelated terms and anchors on their union, does not pass.
    """
    from .directions import _grounded_directions_for_terms

    schools = distilled.get("schools") or []
    n_docs = len(pool.get("docs") or [])
    out = []
    for d in _grounded_directions_for_terms(distilled):
        ev = term_evidence(pool, d["concept"])
        if ev["observed_in"] < 2:
            continue
        anchors = set(ev["anchor_dois"])
        out.append({
            **d,
            "anchor_dois": ev["anchor_dois"],
            "observed_in": ev["observed_in"],
            "n_docs": n_docs,
            "schools": [s["label"] for s in schools if anchors & set(s.get("anchor_dois") or [])],
        })
    return out


#: A keyword query of at least this many words that every database answered with nothing
#: may be too long: every word must appear (M10b Part C, ``02-explore`` "Explore on an empty search").
SHORTEN_MIN_WORDS = 3
_OPERATORS = {"AND", "OR", "NOT"}


def _long_keyword_query(query: str | None, semantic: bool) -> bool:
    """A keyword query (not semantic, no ``OR``) of :data:`SHORTEN_MIN_WORDS` or more words."""
    words = [w for w in re.split(r"[\s()\"]+", str(query or "")) if w]
    return not (semantic or "OR" in words or len([w for w in words if w not in _OPERATORS]) < SHORTEN_MIN_WORDS)


def says_shorten(summary: dict[str, Any], semantic: bool = False) -> bool:
    """Whether an empty search should advise a shorter query.

    True when the query was a keyword query (not semantic, no ``OR``) of
    :data:`SHORTEN_MIN_WORDS` or more words and every database answered (none
    failed) with no record. The browser never counts the words.
    """
    if not _long_keyword_query(summary.get("query"), semantic):
        return False
    legs = summary.get("legs") or []
    return bool(legs) and all(leg.get("status") != "failed" and not leg.get("fetched") for leg in legs)


def leg_says_shorten(query: str | None, leg: dict[str, Any], semantic: bool = False) -> bool:
    """Whether one database's empty answer should advise a shorter query (H-provenance-s2).

    True when the query was a long keyword query (:func:`_long_keyword_query`)
    and this database answered (it did not fail) with no record and no
    reported total above zero. Another database may have found papers: on
    2026-11-19 OpenAlex answered a six-word query while Semantic Scholar, whose
    search needs every word, reported 0 (a live check gave 2 papers for four
    of the words). A failed leg never says shorten: a refusal is not "nothing found".
    """
    if leg.get("status") != "ok" or leg.get("fetched") or leg.get("reported_total"):
        return False
    return _long_keyword_query(query, semantic)


def refuse_unusable_pool(summary: dict[str, Any], semantic: bool = False) -> None:
    """Refuse a pool that cannot carry directions: empty, or every provider failed.

    A ``POOL_EMPTY`` refusal carries ``details.shorten`` (:func:`says_shorten`).
    """
    legs = summary.get("legs") or []
    if summary.get("n_docs", 0) == 0:
        failed = [leg for leg in legs if leg.get("status") == "failed"]
        if legs and len(failed) == len(legs):
            raise ReconRefused(
                PROVIDERS_FAILED,
                "Every database failed to answer, so there is no pool. Nothing was cached; try again later.",
                details={"legs": legs},
            )
        raise ReconRefused(
            POOL_EMPTY_REFUSED,
            "The search found no papers. Nothing was cached; widen the years or rephrase the topic.",
            details={"legs": legs, "status": summary.get("status", POOL_EMPTY),
                     "shorten": says_shorten(summary, semantic)},
        )
