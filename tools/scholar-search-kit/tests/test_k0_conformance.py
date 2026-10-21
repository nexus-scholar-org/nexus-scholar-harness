"""K0 conformance gates for the scholar-search-kit landing (packet T-K0).

Covers:
  * AC-5 — no domain token may appear in kit source (the kit stays
    domain-neutral; domain configuration lives in the research layer).
  * AC-6 — the arXiv compaction knobs keep EMPTY defaults and the default
    emitted query is byte-identical to the pure single-token translation.
"""

import re
from pathlib import Path

import pytest

from scholar_search.models import Query
from scholar_search.providers import ArxivProvider

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "scholar_search"

# The forbidden tokens are assembled from fragments on purpose: the kit's own
# test corpus must not carry the domain vocabulary it forbids in kit source.
_FORBIDDEN_DOMAIN_PATTERNS = (
    r"\bU\s?AV\b",  # unmanned aerial vehicle
    r"\bUAS\b",  # unmanned aircraft system
    r"\bweeds?\b",
    r"\bweedy\b",
    r"\bweediness\b",
    r"\bcrops?\b",
    r"\bcropping\b",
    r"\bcropped\b",
    r"\bdrones?\b",
    r"\bagricultur\w*",
    r"\borthomosaic\w*",
    r"\bsorghum\b",
    r"\bmaize\b",
    r"\bherbicide\w*",
)

# A hardcoded instrument / prompt SHA would be a frozen artifact reference
# inside the kit: forbidden, the kit must not pin an external instrument.
_HEX_LITERAL_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{32,}(?![0-9a-fA-F])")


def _kit_source_files() -> list[Path]:
    return sorted(SRC_ROOT.rglob("*.py"))


def test_kit_source_contains_no_domain_token():
    """AC-5: no domain token may appear anywhere in the kit source tree."""
    assert _kit_source_files(), (
        "kit source tree not found — the gate must not pass vacuously"
    )

    offenders: list[str] = []
    for path in _kit_source_files():
        text = path.read_text(encoding="utf-8")
        for pattern in _FORBIDDEN_DOMAIN_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                offenders.append(
                    f"{path.relative_to(SRC_ROOT)}: {match.group(0)!r} ({pattern})"
                )
    assert not offenders, "domain tokens found in kit source: " + "; ".join(offenders)


def test_kit_source_contains_no_hardcoded_instrument_sha():
    """AC-5: no hardcoded instrument SHA (frozen external artifact) in kit source."""
    offenders: list[str] = []
    for path in _kit_source_files():
        text = path.read_text(encoding="utf-8")
        for match in _HEX_LITERAL_RE.finditer(text):
            offenders.append(f"{path.relative_to(SRC_ROOT)}: {match.group(0)!r}")
    assert not offenders, "hardcoded hex digests found in kit source: " + "; ".join(
        offenders
    )


def test_provider_names_are_not_treated_as_domain_tokens():
    """The domain-token gate must not ban provider names.

    Provider names (crossref / openalex / pubmed / arxiv / semanticscholar)
    are infrastructure, not domain configuration, and they legitimately appear
    in kit source.
    """
    provider_names = ("crossref", "openalex", "pubmed", "arxiv", "semanticscholar")
    for name in provider_names:
        assert not any(
            re.search(pattern, name, flags=re.IGNORECASE)
            for pattern in _FORBIDDEN_DOMAIN_PATTERNS
        ), f"provider name {name!r} must not be a forbidden domain token"

    haystack = "\n".join(p.read_text(encoding="utf-8") for p in _kit_source_files())
    assert "openalex" in haystack.lower()


# ---------------------------------------------------------------------------
# AC-6 — arXiv compaction knobs: empty defaults, byte-parity at defaults
# ---------------------------------------------------------------------------

# A long, multi-cluster boolean query (translated length > 300 characters,
# which is the arXiv compaction trigger). The vocabulary is deliberately
# generic: the kit carries no domain knowledge.
_QUERY_TEXT = (
    '("measurement" OR "estimation" OR "calibration" OR "validation" OR "replication")'
    " AND "
    '("instrumentation" OR "observation" OR "aggregation" OR "reconstruction"'
    ' OR "registration")'
    " AND "
    '("uncertainty" OR "variability" OR "sensitivity" OR "robustness"'
    ' OR "reproducibility")'
    " AND "
    '("baseline" OR "reference" OR "benchmark" OR "prototype" OR "simulation")'
)

# The expected default output: the pure single-token translation, one
# `all:<token>` clause per source cluster, with no stoplist filtering and no
# stem-family expansion (i.e. no domain knowledge at defaults).
_EXPECTED_DEFAULT_QUERY = (
    "(all:measurement OR all:estimation OR all:calibration OR all:validation"
    " OR all:replication) AND (all:instrumentation OR all:observation"
    " OR all:aggregation OR all:reconstruction OR all:registration) AND"
    " (all:uncertainty OR all:variability OR all:sensitivity OR all:robustness"
    " OR all:reproducibility) AND (all:baseline OR all:reference OR all:benchmark"
    " OR all:prototype OR all:simulation)"
)


class _CapturingClient:
    """Minimal stand-in for the HTTP client that records the request params."""

    def __init__(self) -> None:
        self.params: dict | None = None

    async def get(self, url, params=None, **kwargs):
        self.params = params

        class _EmptyResponse:
            text = ""
            content = b""

        return _EmptyResponse()


async def _emitted_search_query(provider: ArxivProvider) -> str:
    provider.client = _CapturingClient()
    query = Query(text=_QUERY_TEXT, id="Q-CONFORMANCE", year_min=2020, year_max=2026)
    async for _ in provider.search(query):
        pass
    assert provider.client.params is not None
    return provider.client.params["search_query"]


@pytest.mark.asyncio
async def test_arxiv_compaction_defaults_are_empty():
    """AC-6: the compaction knobs keep EMPTY defaults (no domain config)."""
    provider = ArxivProvider()

    assert provider.compact_stoplist == frozenset()
    assert provider.compact_stem_families == ()


@pytest.mark.asyncio
async def test_arxiv_compaction_default_output_is_byte_identical():
    """AC-6: at defaults the emitted query is byte-identical to the
    pure single-token translation (no stoplist, no morphology invented)."""
    emitted = await _emitted_search_query(ArxivProvider())

    assert emitted == _EXPECTED_DEFAULT_QUERY


@pytest.mark.asyncio
async def test_arxiv_compaction_default_invents_no_token():
    """AC-6 / NC-7: at defaults no token outside the query is introduced.

    Every emitted `all:<token>` must already occur in the source query, i.e.
    the kit default adds no domain vocabulary and drops nothing silently.
    """
    emitted = await _emitted_search_query(ArxivProvider())

    tokens = re.findall(r"all:([^\s)]+)", emitted)
    assert tokens
    for token in tokens:
        assert token.lower() in _QUERY_TEXT.lower(), (
            f"token {token!r} was not present in the source query"
        )


@pytest.mark.asyncio
async def test_arxiv_compaction_knobs_change_the_output_when_configured():
    """NEGATIVE CONTROL for the default-output assertions.

    The default assertions above must be able to FAIL: when a research layer
    supplies a stoplist and a stem family, the emitted query changes (the
    stoplisted token disappears, the declared morphology appears). If this
    test failed, the default assertion would be vacuous.
    """
    default_emitted = await _emitted_search_query(ArxivProvider())

    configured = ArxivProvider(
        compact_stoplist=("baseline",),
        compact_stem_families={"calibr": ("calibrated",)},
    )
    configured_emitted = await _emitted_search_query(configured)

    assert configured_emitted != default_emitted
    assert "all:baseline" not in configured_emitted
    assert "all:calibrated" in configured_emitted
    # The default output keeps the stoplisted token (no domain knowledge).
    assert "all:baseline" in default_emitted
    assert "all:calibrated" not in default_emitted
