"""Check-only recall: is each seed paper in what the frozen query returns? (E2, M3b-api)

`docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.2 and decision 3 of
2026-11-10. ``check_seeds`` runs the protocol's query **as it is**, with the
protocol's cap, on each provider, and reports per seed and per provider
whether the seed came back. It never rewrites the query: the "heal" of
``QueryDiagnosticValidator.validate_and_heal`` (which appends ``OR (doi:...)``)
stays a CLI tool. A miss is a finding to record, not something to repair here;
the repair is a protocol amendment.

Each seed is resolved through ``DocumentVerifier`` for its title. When the
identifier resolves to a different title than the record a provider returned,
the seed says ``DOI_TITLE_MISMATCH`` and keeps the returned record's title:
the record is never swapped for the resolved one (SRCH-10).
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from .engine import SearchEngine
from .models import Document, ExternalIds, Query
from .verifier import DocumentVerifier

MAX_SEEDS = 25
SEED_KINDS = ("doi", "arxiv")
SEED_SOURCES = ("anchor", "you")

_DOI = re.compile(r"^10\.\d+(\.\d+)*/\S+$")
_ARXIV = re.compile(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})$", re.I)
_ARXIV_DOI = "10.48550/arxiv."


class SeedsInvalid(ValueError):
    """The seed list is empty, too long, or holds a malformed identifier (``SEEDS_INVALID``)."""

    code = "SEEDS_INVALID"


def normalize_doi(value: str | None) -> str:
    text = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text


def normalize_arxiv(value: str | None) -> str:
    text = (value or "").strip()
    if text.lower().startswith("arxiv:"):
        text = text[6:]
    if text.lower().startswith(_ARXIV_DOI):
        text = text[len(_ARXIV_DOI):]
    return re.sub(r"v\d+$", "", text).lower()


def validate_seeds(seeds: list[dict[str, Any]]) -> list[dict[str, str]]:
    """The seeds as ``{id, kind, source}``, or ``SeedsInvalid`` naming the first problem."""
    if not seeds:
        raise SeedsInvalid("a recall check needs at least one seed")
    if len(seeds) > MAX_SEEDS:
        raise SeedsInvalid(f"a recall check takes at most {MAX_SEEDS} seeds, not {len(seeds)}")
    out: list[dict[str, str]] = []
    for seed in seeds:
        sid, kind = str(seed.get("id") or "").strip(), seed.get("kind")
        source = seed.get("source") or "you"
        if kind not in SEED_KINDS or source not in SEED_SOURCES:
            raise SeedsInvalid(f"seed {sid or '(empty)'}: kind must be doi or arxiv, source anchor or you")
        ok = _DOI.match(normalize_doi(sid)) if kind == "doi" else _ARXIV.match(normalize_arxiv(sid))
        if not sid or not ok:
            raise SeedsInvalid(f"seed {sid or '(empty)'} is not a well-formed {kind} identifier")
        out.append({"id": sid, "kind": kind, "source": source})
    return out


def _holds(provider: str, seed: dict[str, str]) -> bool:
    """Whether a provider can hold that kind of record at all ("n/a" otherwise)."""
    name = provider.lower()
    if seed["kind"] == "doi":
        return name != "arxiv" or normalize_doi(seed["id"]).startswith(_ARXIV_DOI)
    return name not in ("pubmed",)


def _matches(doc: Document, seed: dict[str, str]) -> bool:
    eids = doc.external_ids
    if seed["kind"] == "doi":
        doi = normalize_doi(seed["id"])
        if eids.doi and normalize_doi(eids.doi) == doi:
            return True
        # An arXiv DOI (10.48550/arXiv.<id>) is the same work as the arXiv id.
        return doi.startswith(_ARXIV_DOI) and bool(eids.arxiv_id) and normalize_arxiv(eids.arxiv_id) == normalize_arxiv(doi)
    want = normalize_arxiv(seed["id"])
    return normalize_arxiv(eids.arxiv_id) == want or normalize_arxiv(eids.doi) == want


class _Collecting:
    """Keeps the records one provider returned; the engine sees the provider itself."""

    def __init__(self, provider: Any, sink: dict[str, list[Document]]):
        self._provider = provider
        self._sink = sink

    @property
    def name(self) -> str:
        return getattr(self._provider, "name", type(self._provider).__name__)

    @property
    def current_leg(self) -> Any:
        return getattr(self._provider, "current_leg", None)

    @current_leg.setter
    def current_leg(self, leg: Any) -> None:
        try:
            self._provider.current_leg = leg
        except AttributeError:  # pragma: no cover - read-only doubles
            pass

    async def search(self, query: Query):
        async for doc in self._provider.search(query):
            self._sink.setdefault(self.name, []).append(doc)
            yield doc

    def __getattr__(self, item: str) -> Any:
        return getattr(self._provider, item)


async def _title_check(verifier: Any, seed: dict[str, str], found: Document | None) -> tuple[str, str | None]:
    """``(title_check, title)``: ``ok``, ``DOI_TITLE_MISMATCH`` or ``unresolved``."""
    if found is not None:
        probe = found
    elif seed["kind"] == "doi":
        probe = Document(title="Untitled", external_ids=ExternalIds(doi=normalize_doi(seed["id"])))
    else:
        probe = Document(title="Untitled", external_ids=ExternalIds(arxiv_id=normalize_arxiv(seed["id"])))
    try:
        verified, resolved, note = await verifier.verify_document(probe)
    except Exception:  # noqa: BLE001 - a failed lookup is "unresolved", never a crash
        return "unresolved", found.title if found else None
    if verified:
        return "ok", (found.title if found else resolved.title)
    if str(note).startswith("DOI_TITLE_MISMATCH"):
        return "DOI_TITLE_MISMATCH", found.title if found else None
    return "unresolved", found.title if found else None


async def check_seeds(
    query: Query,
    seeds: list[dict[str, Any]],
    providers: list[Any],
    cap: int | None,
    *,
    verifier: Any | None = None,
    leg_callback=None,
    should_stop=None,
) -> dict[str, Any]:
    """Run ``query`` unchanged (cap ``cap``) and report each seed per provider.

    Returns ``{checked_at, query_text, seeds: [{id, kind, source, title,
    title_check, per_provider}], found, total, missed_everywhere, legs}``. A
    provider's answer per seed is ``found``, ``not_found``, ``n/a`` (it cannot
    hold that kind of record) or ``failed`` (its leg failed).
    """
    checked = validate_seeds(seeds)
    run_query = replace(query, max_results=cap) if cap else query
    by_provider: dict[str, list[Document]] = {}
    engine = SearchEngine(providers=[_Collecting(p, by_provider) for p in providers])
    try:
        run = await engine.run(run_query, dedup=False, leg_callback=leg_callback, should_stop=should_stop)
    finally:
        await engine.close()
    legs = [leg.to_dict() for leg in run.legs]
    failed = {leg["provider"] for leg in legs if leg["status"] == "failed"}

    verifier = verifier or DocumentVerifier()
    rows: list[dict[str, Any]] = []
    try:
        for seed in checked:
            per_provider: dict[str, str] = {}
            found: Document | None = None
            for leg in legs:
                name = leg["provider"]
                if not _holds(name, seed):
                    per_provider[name] = "n/a"
                    continue
                hit = next((d for d in by_provider.get(name, []) if _matches(d, seed)), None)
                if hit is not None:
                    per_provider[name] = "found"
                    found = found or hit
                else:
                    per_provider[name] = "failed" if name in failed else "not_found"
            title_check, title = await _title_check(verifier, seed, found)
            rows.append({**seed, "title": title, "title_check": title_check, "per_provider": per_provider})
    finally:
        close = getattr(verifier, "close", None)
        if close is not None:
            await close()
    missed = [row["id"] for row in rows if "found" not in row["per_provider"].values()]
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "query_text": query.text,
        "seeds": rows,
        "found": len(rows) - len(missed),
        "total": len(rows),
        "missed_everywhere": missed,
        "legs": legs,
    }
