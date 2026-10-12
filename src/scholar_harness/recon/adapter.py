"""Harness-owned explicit MCP recon adapter interface (HCM-05).

Characterization unit: this module defines the versioned, typed boundary the
MCP ``recon_*`` tools *should* consume instead of the current dynamic
discovery seam (``scholar_agent.server._harness_src`` + ``sys.path`` insert +
lazy ``_ensure_harness_recon_loaded`` globals).  It delegates 1:1 to the
existing harness recon machinery and introduces no new algorithms, no cache-key
logic, no taxonomy logic, and no transport behavior.

Rules for this module:

- Delegation only: every entry point calls exactly one existing
  ``scholar_harness.recon`` function (engine / cache_key / distiller /
  lexicon / adaptive / gates).  No ``hashlib`` digests, no regex tables, no
  scoring, and no session-file helpers live here.
- No ``sys.path`` tricks, no ``NEXUS_HARNESS_SRC`` handling, no fallback
  roots, no ``scholar_agent`` / MCP imports.  Importing this module must work
  standalone (``uv run python -c "import scholar_harness.recon.adapter"``).
- Typed errors: dependency problems raise
  :class:`ReconAdapterDependencyError`; invalid caller inputs raise
  :class:`ReconAdapterInputError`.  Both subclass :class:`RuntimeError` (and
  the input error additionally subclasses :class:`ValueError`) so a future
  kit consumer keeping its current
  ``except (RuntimeError, ValueError, OSError)`` envelope maps them to the
  documented ``{status: error, ...}`` reply instead of leaking an uncaught
  ``TypeError`` (the OBSERVED kit failure mode when the lazy globals are
  ``None``).

Kit-consumption status (HCM-05 ADOPTED): the vendored
``tools/scholar-agent-kit/src/scholar_agent/server.py`` now consumes this
adapter through a plain guarded import -- the dynamic seam
(``_harness_src`` / ``NEXUS_HARNESS_SRC`` / ``sys.path`` insert / parent-walk
discovery) is deleted, and the MCP ``recon_*`` tools call the loader first and
return the documented ``{status: error, ...}`` envelope when this module is
unavailable.  Canonical kit merge ``50c0b3fbf52fc1a9768b219bc2e894d713eb38af``
(``nexus-scholar-org/scholar-agent-kit`` PR #5); its
``plugins.json`` ``default_rev`` and the vendored tree are pinned to that
commit -- see the HCM-05 arch record for the three-invariant proof and the
live adapter-path evidence.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .adaptive import execute_followups as _execute_followups
from .adaptive import merge_pools as _merge_pools
from .adaptive import plan_followups as _plan_followups
from .cache_key import cache_key as _cache_key
from .cache_key import normalize_query as _normalize_query
from .cache_key import parse_cache_key as _parse_cache_key
from .distiller import distill_pool as _distill_pool
from .engine import DEFAULT_PROVIDERS as _DEFAULT_PROVIDERS
from .engine import POOL_MAX as _POOL_MAX
from .engine import ReconEngine as _ReconEngine
from .engine import SearchFn as _SearchFn
from .engine import canonical_recon_root as _canonical_recon_root
from .gates import compute_pool_sufficiency as _compute_pool_sufficiency
from .gates import compute_topic_purity as _compute_topic_purity
from .lexicon import DEFAULT_LEXICON as _DEFAULT_LEXICON
from .lexicon import DomainLexicon as _DomainLexicon
from .lexicon import merge_lexicons as _merge_lexicons

ADAPTER_VERSION = "1.0"

__all__ = [
    "ADAPTER_VERSION",
    "ReconAdapterDependencyError",
    "ReconAdapterError",
    "ReconAdapterInputError",
    "adapter_version",
    "build_cache_key",
    "default_lexicon",
    "default_providers",
    "describe_interface",
    "distill_terms",
    "make_engine",
    "merge_lexicon",
    "merge_pool_list",
    "normalize_text",
    "parse_key",
    "plan_candidates",
    "pool_gate",
    "probe_topic",
    "resolve_cache_root",
    "run_followups",
    "saturation_for",
    "topic_gate",
]


class ReconAdapterError(RuntimeError):
    """Base for all typed adapter failures (envelope-compatible)."""


class ReconAdapterDependencyError(ReconAdapterError):
    """A delegated harness symbol or injected callable dependency is missing."""


class ReconAdapterInputError(ReconAdapterError, ValueError):
    """A caller-supplied adapter input is malformed (also a ValueError)."""


def _require_symbol(name: str, value: Any) -> Any:
    if value is None:
        raise ReconAdapterDependencyError(
            f"adapter dependency unavailable: {name} is None"
        )
    return value


def _reject_workspaces(path: Path, what: str) -> Path:
    if any(part.lower() == "workspaces" for part in path.parts):
        raise ReconAdapterInputError(f"refusing {what} under workspaces/: {path}")
    return path


def adapter_version() -> str:
    """Return the versioned adapter interface identifier (``"1.0"``)."""
    return ADAPTER_VERSION


def describe_interface() -> dict[str, Any]:
    """Return the explicit adapter surface (version + entry points)."""
    _require_symbol("ReconEngine", _ReconEngine)
    _require_symbol("canonical_recon_root", _canonical_recon_root)
    _require_symbol("distill_pool", _distill_pool)
    return {
        "adapter_version": ADAPTER_VERSION,
        "entry_points": sorted(
            [
                "adapter_version",
                "build_cache_key",
                "default_lexicon",
                "default_providers",
                "describe_interface",
                "distill_terms",
                "make_engine",
                "merge_lexicon",
                "merge_pool_list",
                "normalize_text",
                "parse_key",
                "plan_candidates",
                "pool_gate",
                "probe_topic",
                "resolve_cache_root",
                "run_followups",
                "saturation_for",
                "topic_gate",
            ]
        ),
        "delegates_to": sorted(
            [
                "scholar_harness.recon.engine.ReconEngine",
                "scholar_harness.recon.engine.canonical_recon_root",
                "scholar_harness.recon.engine.cache_key",
                "scholar_harness.recon.distiller.distill_pool",
                "scholar_harness.recon.adaptive.plan_followups",
                "scholar_harness.recon.adaptive.merge_pools",
                "scholar_harness.recon.adaptive.execute_followups",
                "scholar_harness.recon.gates.compute_pool_sufficiency",
                "scholar_harness.recon.gates.compute_topic_purity",
                "scholar_harness.recon.lexicon.merge_lexicons",
            ]
        ),
    }


def resolve_cache_root() -> Path:
    """Return the canonical recon cache root (1:1 delegation).

    No fallback, no override handling here: ``NEXUS_RECON_ROOT`` and the
    repo-anchored default are owned by :func:`canonical_recon_root`.
    """
    fn = _require_symbol("canonical_recon_root", _canonical_recon_root)
    return fn()


def make_engine(
    cache_root: Path | str | None = None,
    search_fn: _SearchFn | None = None,
) -> Any:
    """Build a :class:`ReconEngine` with typed adapter errors.

    ``cache_root=None`` delegates root selection to the engine (which reads
    ``NEXUS_RECON_ROOT`` / the canonical root).  An explicit ``cache_root``
    under any ``workspaces`` path segment is refused with
    :class:`ReconAdapterInputError`.  A non-callable ``search_fn`` raises
    :class:`ReconAdapterDependencyError` instead of failing later as an
    uncaught ``TypeError``.
    """
    engine_cls = _require_symbol("ReconEngine", _ReconEngine)
    if search_fn is not None and not callable(search_fn):
        raise ReconAdapterDependencyError(
            "adapter dependency invalid: search_fn is not callable"
        )
    if cache_root is not None:
        resolved = Path(cache_root).resolve()
        _reject_workspaces(resolved, "cache_root")
        return engine_cls(cache_root=resolved, search_fn=search_fn)
    return engine_cls(cache_root=None, search_fn=search_fn)


def build_cache_key(
    query: str,
    providers: list[str] | None = None,
    year_min: int = 2000,
    year_max: int | None = None,
    semantic: bool = False,
) -> str:
    """Build the hierarchical probe cache key (delegates to ``cache_key``)."""
    fn = _require_symbol("cache_key", _cache_key)
    if not isinstance(query, str) or not query.strip():
        raise ReconAdapterInputError("query must be a non-empty string")
    provider_list = list(_DEFAULT_PROVIDERS) if providers is None else list(providers)
    if not provider_list or not all(isinstance(p, str) and p for p in provider_list):
        raise ReconAdapterInputError("providers must be a non-empty list of strings")
    return fn(query, provider_list, year_min, year_max, semantic=semantic)


def parse_key(key: str) -> dict[str, Any]:
    """Parse a cache key back into its segments (delegates)."""
    fn = _require_symbol("parse_cache_key", _parse_cache_key)
    if not isinstance(key, str) or not key:
        raise ReconAdapterInputError("key must be a non-empty string")
    return fn(key)


def normalize_text(text: str) -> str:
    """Normalize probe text exactly as the cache-key builder does."""
    fn = _require_symbol("normalize_query", _normalize_query)
    if not isinstance(text, str):
        raise ReconAdapterInputError("text must be a string")
    return fn(text)


def default_providers() -> list[str]:
    """Return the default probe provider list (a copy)."""
    _require_symbol("DEFAULT_PROVIDERS", _DEFAULT_PROVIDERS)
    return list(_DEFAULT_PROVIDERS)


def default_lexicon() -> Any:
    """Return the shipped default domain lexicon."""
    return _require_symbol("DEFAULT_LEXICON", _DEFAULT_LEXICON)


def merge_lexicon(base: Any, extra: Any) -> Any:
    """Merge an extra lexicon onto a base (delegates to ``merge_lexicons``)."""
    fn = _require_symbol("merge_lexicons", _merge_lexicons)
    if base is None or extra is None:
        raise ReconAdapterDependencyError(
            "adapter dependency unavailable: lexicon operand is None"
        )
    if not isinstance(base, _DomainLexicon) or not isinstance(extra, _DomainLexicon):
        raise ReconAdapterInputError("base and extra must be DomainLexicon instances")
    return fn(base, extra)


def distill_terms(
    pool: dict[str, Any],
    lexicon: Any | None = None,
    query_text: str | None = None,
) -> dict[str, Any]:
    """Distill a pool dict into a terms payload (delegates to ``distill_pool``)."""
    fn = _require_symbol("distill_pool", _distill_pool)
    if not isinstance(pool, dict):
        raise ReconAdapterInputError("pool must be a dict")
    if lexicon is not None and not isinstance(lexicon, _DomainLexicon):
        raise ReconAdapterInputError("lexicon must be a DomainLexicon or None")
    if query_text is not None and not isinstance(query_text, str):
        raise ReconAdapterInputError("query_text must be a string or None")
    return fn(pool, lexicon=lexicon, query_text=query_text)


def plan_candidates(
    distilled: dict[str, Any], pool: dict[str, Any]
) -> list[dict[str, Any]]:
    """Plan thin-school/topic follow-up candidates (delegates)."""
    fn = _require_symbol("plan_followups", _plan_followups)
    if not isinstance(distilled, dict) or not isinstance(pool, dict):
        raise ReconAdapterInputError("distilled and pool must both be dicts")
    return fn(distilled, pool)


def merge_pool_list(
    pools: list[dict[str, Any]], cap: int | None = None
) -> dict[str, Any]:
    """Merge pools by DOI-union (delegates to ``merge_pools``)."""
    fn = _require_symbol("merge_pools", _merge_pools)
    if not isinstance(pools, list):
        raise ReconAdapterInputError("pools must be a list")
    if cap is None:
        pool_max = _require_symbol("POOL_MAX", _POOL_MAX)
        return fn(pools, cap=int(pool_max))
    if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
        raise ReconAdapterInputError("cap must be a positive int")
    return fn(pools, cap=cap)


def pool_gate(n_docs: int) -> dict[str, Any]:
    """Assess pool sufficiency (delegates to ``compute_pool_sufficiency``)."""
    fn = _require_symbol("compute_pool_sufficiency", _compute_pool_sufficiency)
    if not isinstance(n_docs, int) or isinstance(n_docs, bool) or n_docs < 0:
        raise ReconAdapterInputError("n_docs must be a non-negative int")
    return fn(n_docs)


def topic_gate(topics: list[dict[str, Any]]) -> dict[str, Any]:
    """Score topic-layer coherence (delegates to ``compute_topic_purity``)."""
    fn = _require_symbol("compute_topic_purity", _compute_topic_purity)
    if not isinstance(topics, list):
        raise ReconAdapterInputError("topics must be a list")
    return fn(topics)


def saturation_for(corpus_total: int) -> str:
    """Map a corpus works-count to its saturation label (delegates)."""
    engine_cls = _require_symbol("ReconEngine", _ReconEngine)
    if not isinstance(corpus_total, int) or isinstance(corpus_total, bool):
        raise ReconAdapterInputError("corpus_total must be an int")
    return engine_cls.saturation_label(corpus_total)


async def probe_topic(
    query: str,
    providers: list[str] | None = None,
    year_min: int = 2000,
    year_max: int | None = None,
    max_results: int = 25,
    semantic: bool = False,
    cache_root: Path | str | None = None,
    search_fn: Callable[..., Any] | None = None,
) -> tuple[Path, int]:
    """Run one hermetic-or-live probe via a fresh engine (delegates).

    Returns ``(pool_file, n)`` exactly as :meth:`ReconEngine.probe` does, so
    cache identity and idempotency are preserved by construction.
    """
    if not isinstance(query, str) or not query.strip():
        raise ReconAdapterInputError("query must be a non-empty string")
    if not isinstance(max_results, int) or isinstance(max_results, bool):
        raise ReconAdapterInputError("max_results must be an int")
    if max_results <= 0:
        raise ReconAdapterInputError("max_results must be a positive int")
    engine = make_engine(cache_root=cache_root, search_fn=search_fn)
    provider_list = list(_DEFAULT_PROVIDERS) if providers is None else list(providers)
    return await engine.probe(
        query,
        providers=provider_list,
        year_min=year_min,
        year_max=year_max,
        max_results=max_results,
        semantic=semantic,
    )


async def run_followups(
    pool: dict[str, Any],
    distilled: dict[str, Any],
    cache_root: Path | str | None = None,
    search_fn: Callable[..., Any] | None = None,
    max_followups: int = 3,
    providers: list[str] | None = None,
    year_min: int = 2000,
    year_max: int | None = None,
    max_results: int = 25,
    lexicon: Any | None = None,
) -> dict[str, Any]:
    """Execute the bounded adaptive horizon (delegates to ``execute_followups``)."""
    fn = _require_symbol("execute_followups", _execute_followups)
    if not isinstance(pool, dict) or not isinstance(distilled, dict):
        raise ReconAdapterInputError("pool and distilled must both be dicts")
    if not isinstance(max_followups, int) or isinstance(max_followups, bool):
        raise ReconAdapterInputError("max_followups must be an int")
    if max_followups < 0:
        raise ReconAdapterInputError("max_followups must be >= 0")
    engine = make_engine(cache_root=cache_root, search_fn=search_fn)
    return await fn(
        pool,
        distilled,
        engine,
        max_followups=max_followups,
        providers=providers,
        year_min=year_min,
        year_max=year_max,
        max_results=max_results,
        lexicon=lexicon,
    )
