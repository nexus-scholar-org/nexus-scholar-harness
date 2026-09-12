"""Empirical surface scan engine (M0.1).

Probes literature providers, dedups via the scholar-search kit, and persists a
content-addressed candidate pool under ``.cache/inception_recon/pools/`` per
spec 04_memory_and_cache.md sections 2-5.  Probe input is an injectable
``search_fn`` for hermetic tests; the default builds the kit ``SearchEngine``.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_search.engine import SearchEngine
from scholar_search.models import Document, Query
from scholar_search.providers import (
    ArxivProvider,
    CrossrefProvider,
    OpenAlexProvider,
    SemanticScholarProvider,
)

from .cache_key import cache_key

DEFAULT_PROVIDERS = ["openalex", "semanticscholar", "crossref", "arxiv"]
POOL_MAX = 25

_PROVIDER_CLASSES: dict[str, type] = {
    "openalex": OpenAlexProvider,
    "semanticscholar": SemanticScholarProvider,
    "crossref": CrossrefProvider,
    "arxiv": ArxivProvider,
}

SearchFn = Callable[[Query, list[str]], list[Document] | Awaitable[list[Document]]]


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _doc_to_pool_entry(doc: Document) -> dict[str, Any]:
    oa_url = None
    for loc in doc.oa_locations or []:
        if isinstance(loc, dict):
            oa_url = loc.get("pdf_url") or loc.get("landing_page_url") or None
            if oa_url:
                break
    if not oa_url:
        oa_url = doc.url
    provider = doc.provider or "unknown"
    entry = {
        "id": f"{provider}|{doc.provider_id}" if doc.provider_id else provider,
        "provider": provider,
        "doi": doc.external_ids.doi,
        "title": doc.title,
        "abstract": doc.abstract,
        "year": doc.year,
        "citations": doc.citations_count,
        "oa_url": oa_url,
    }
    if doc.topics:
        # Optional §5 field: carried only when the normalizer populated it.
        entry["topics"] = doc.topics
    return entry


class ReconEngine:
    """Single-probe empirical surface scan with deterministic caching."""

    def __init__(
        self,
        cache_root: Path | str = Path(".cache/inception_recon"),
        search_fn: SearchFn | None = None,
    ) -> None:
        self.cache_root = Path(cache_root).resolve()
        self.pools_dir = self.cache_root / "pools"
        self.search_fn = search_fn

    def _assert_safe_output(self, path: Path) -> None:
        resolved = Path(path).resolve()
        if any(p.lower() == "workspaces" for p in resolved.parts):
            raise RuntimeError(f"refusing to write under workspaces/: {resolved}")

    def _build_engine(self, providers: list[str]) -> SearchEngine:
        unknown = [p for p in providers if p not in _PROVIDER_CLASSES]
        if unknown:
            raise ValueError(f"unknown provider(s): {', '.join(unknown)}")
        return SearchEngine(providers=[_PROVIDER_CLASSES[p]() for p in providers])

    async def _fetch_real(
        self,
        query_text: str,
        providers: list[str],
        year_min: int,
        year_max: int | None,
        max_results: int | None,
        semantic: bool = False,
    ) -> list[Document]:
        engine = self._build_engine(providers)
        try:
            q = Query(
                text=query_text,
                max_results=max_results,
                year_min=year_min,
                year_max=year_max,
                semantic=semantic,
            )
            return await engine.search_all(q, dedup=True)
        finally:
            await engine.close()

    async def _fetch(
        self,
        query_text: str,
        providers: list[str],
        year_min: int,
        year_max: int | None,
        max_results: int | None,
        semantic: bool = False,
    ) -> list[Document]:
        if self.search_fn is not None:
            result = self.search_fn(
                Query(
                    text=query_text,
                    max_results=max_results,
                    year_min=year_min,
                    year_max=year_max,
                    semantic=semantic,
                ),
                providers,
            )
            if inspect.isawaitable(result):
                result = await result
            return list(result)
        return await self._fetch_real(
            query_text, providers, year_min, year_max, max_results, semantic
        )

    async def probe(
        self,
        query: str,
        providers: list[str] | None = None,
        year_min: int = 2000,
        year_max: int | None = None,
        max_results: int = 25,
        semantic: bool = False,
    ) -> tuple[Path, int]:
        """Run one probe and return ``(pool_file, n)``.

        A cache hit for the same key returns the existing pool with zero
        network calls; otherwise a fresh pool is persisted under ``pools/``.

        ``semantic=True`` (M0.6) selects OpenAlex ``search.semantic`` and
        mints a mode-segmented cache key (``/m/semantic/``) so keyword and
        semantic pools never collide.  The default is byte-identical to the
        pre-M0.6 keyword path.

        Returned pool size is ``min(25, len(deduped_docs))``; on sparse
        provider returns ``n`` may be < 10 (by design -- no zero-padding is
        performed).  This is the documented tension between DoD M0.1.1's
        ``10 <= n <= 25`` and T1.2's no-zero-padding rule: the bound holds
        for normal-denseness providers, not for sparse ones.
        """
        provider_list = list(DEFAULT_PROVIDERS) if providers is None else list(providers)
        key = cache_key(query, provider_list, year_min, year_max, semantic=semantic)
        pool_path = self.pools_dir / f"{_sha1(key)}_pool.json"
        self._assert_safe_output(pool_path)

        if pool_path.exists():
            try:
                payload = json.loads(pool_path.read_text(encoding="utf-8"))
                return pool_path, len(payload.get("docs", []))
            except (OSError, ValueError):
                pass

        docs = await self._fetch(
            query, provider_list, year_min, year_max, max_results, semantic
        )
        self.pools_dir.mkdir(parents=True, exist_ok=True)
        self._assert_safe_output(pool_path)

        payload = {
            "cache_key": key,
            "created_at": datetime.now(UTC).isoformat(),
            "docs": [_doc_to_pool_entry(d) for d in docs[:POOL_MAX]],
            "fulltexts": {},
        }
        _atomic_write_json(pool_path, payload)
        return pool_path, len(payload["docs"])