"""Exploratory reconnaissance package (empirical surface scan, M0.1)."""

from .adaptive import execute_followups, merge_pools, plan_followups
from .cache_key import cache_key, normalize_query, parse_cache_key
from .distiller import distill, distill_pool
from .engine import DEFAULT_PROVIDERS, POOL_MAX, ReconEngine, canonical_recon_root
from .lexicon import DEFAULT_LEXICON, DomainLexicon, merge_lexicons

__all__ = [
    "DEFAULT_LEXICON",
    "DEFAULT_PROVIDERS",
    "POOL_MAX",
    "DomainLexicon",
    "ReconEngine",
    "cache_key",
    "canonical_recon_root",
    "distill",
    "distill_pool",
    "execute_followups",
    "merge_lexicons",
    "merge_pools",
    "normalize_query",
    "parse_cache_key",
    "plan_followups",
]