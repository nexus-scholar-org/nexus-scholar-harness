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

from scholar_search.config import settings
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

# Saturation thresholds (13_evaluation.md section 3.4, GAP B).
SATURATION_SCANT = 50
SATURATION_SPARSE = 500


def _source_root() -> Path:
    """Walk up from this module to the enclosing project root (pyproject.toml).

    Anchoring on the source tree (not ``Path.cwd()``) makes the default cache
    root deterministic: launching from ``tools/scholar-agent-kit/``, a repo
    subdirectory, or any other CWD resolves to the same path (P4).
    """
    current = Path(__file__).resolve().parent
    while True:
        if (current / "pyproject.toml").is_file():
            return current
        parent = current.parent
        if parent == current:
            raise RuntimeError("could not locate project root (no pyproject.toml)")
        current = parent


def canonical_recon_root() -> Path:
    """The canonical recon cache root shared by CLI and MCP (M0.7 T7.7, P4).

    ``NEXUS_RECON_ROOT`` overrides the default so an operator can point the
    whole pipeline at one root explicitly.  Without it, the root is the
    CWD-independent ``<project-root>/.cache/inception_recon``; because the MCP
    server imports the same helper from this harness, the CLI wizard and the
    server agree by construction instead of scattering under their separate
    current directories.
    """
    env_root = os.environ.get("NEXUS_RECON_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return _source_root() / ".cache" / "inception_recon"

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
        cache_root: Path | str | None = None,
        search_fn: SearchFn | None = None,
    ) -> None:
        # Canonical recon root (M0.7 T7.7, P4): NEXUS_RECON_ROOT wins; else an
        # explicit cache_root; else the CWD-independent repo-anchored default
        # from canonical_recon_root().  The CLI and the MCP server share one
        # cache even when launched from different directories.
        env_root = os.environ.get("NEXUS_RECON_ROOT")
        if env_root:
            self.cache_root = Path(env_root).resolve()
        elif cache_root is not None:
            self.cache_root = Path(cache_root).resolve()
        else:
            self.cache_root = canonical_recon_root().resolve()
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

    @staticmethod
    def saturation_label(corpus_total: int) -> str:
        """Map a corpus works-count to a saturation label (13_evaluation section 3.4).

        ``scant < 50 | sparse 50-500 | dense > 500 | unknown -1``.  Thresholds
        are module-level constants (``SATURATION_SCANT``/``SATURATION_SPARSE``).
        """
        if corpus_total < 0:
            return "unknown"
        if corpus_total < SATURATION_SCANT:
            return "scant"
        if corpus_total <= SATURATION_SPARSE:
            return "sparse"
        return "dense"

    async def corpus_count(
        self,
        term: str,
        providers: list[str] | None = None,
        year_min: int = 2000,
        year_max: int | None = None,
    ) -> int:
        """Uncapped corpus works-count for a term (GAP B, M0.7 T7.3).

        A cheap OpenAlex ``meta.count`` request (per-page=1, no result bodies)
        that answers "is a thin pool the sign of a real gap or a query-phrasing
        artifact?".  Returns ``-1`` when OpenAlex is not in scope or the count
        cannot be obtained (unknown), or when an injected ``search_fn`` is set
        (hermetic/test seams must never touch the network).
        """
        provider_list = (
            list(DEFAULT_PROVIDERS) if providers is None else list(providers)
        )
        if "openalex" not in provider_list or self.search_fn is not None:
            return -1
        provider = OpenAlexProvider()
        params: dict[str, Any] = {
            "search": term,
            "per-page": 1,
            "mailto": settings.mailto,
        }
        if settings.openalex_key:
            params["api_key"] = settings.openalex_key
        filters: list[str] = []
        if year_min:
            filters.append(f"from_publication_date:{year_min}-01-01")
        if year_max:
            filters.append(f"to_publication_date:{year_max}-12-31")
        if filters:
            params["filter"] = ",".join(filters)
        try:
            resp = await provider.client.get(provider.base_url, params=params)
            body = resp.json()
            return int(body.get("meta", {}).get("count", -1))
        except Exception:  # noqa: BLE001 - unknown count degrades to -1 by contract
            return -1
        finally:
            await provider.client.close()

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