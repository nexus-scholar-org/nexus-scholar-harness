"""E1, the plan dry run (M3d-engine; discovery API packet §4.1, decision 4).

``compile_plan(protocol, providers)`` says, per database, the string a run
would send and the request it would make, without sending anything: each
provider's ``translate(query)`` is the step its ``search`` takes before the
first request. The query is the one each leg receives (the protocol's cap, else
the engine ceiling), so the preview and the run's ``SearchLeg.executed_query``
are the same string.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from .engine import ENGINE_CEILING
from .models import DEFAULT_DATABASES, Query
from .protocol_adapter import compile_protocol_search
from .providers.base import public_request

#: Every database the engine knows, in the order a plan lists them.
KNOWN_PROVIDERS: tuple[str, ...] = ("openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv")
#: The engine's own default suite (``SearchEngine()`` with no providers), which a
#: run falls back to when its list names no known database; bioRxiv is off by default.
DEFAULT_PROVIDERS: tuple[str, ...] = DEFAULT_DATABASES


def canonical_provider(name: str) -> str:
    key = str(name).lower().strip().replace("-", "_").replace(" ", "_")
    return "semanticscholar" if key == "semantic_scholar" else key


def run_providers(names: Sequence[str] | None) -> list[str]:
    """The databases a run searches for a list of names (M10a).

    Canonical names, known ones only (the run drops an unknown name), the first
    of each repeat, in order; a list with no known name is the engine's default
    suite, as ``SearchEngine`` builds it when it is given no providers.
    """
    known = [canonical_provider(n) for n in names or []]
    ordered = list(dict.fromkeys(n for n in known if n in KNOWN_PROVIDERS))
    return ordered or list(DEFAULT_PROVIDERS)


def protocol_default_providers() -> list[str]:
    """The list the protocol adapter gives a protocol without ``search_strategy.target_databases``."""
    return list(compile_protocol_search({"search_strategy": {}})[1])


def leg_query(query: Query) -> Query:
    """The query one leg receives: ``max_results`` bounded by the engine ceiling (as ``SearchEngine.run``)."""
    cap = min(int(query.max_results), ENGINE_CEILING) if query.max_results else ENGINE_CEILING
    return replace(query, max_results=cap)


def _provider(name: str) -> Any:
    from .providers.arxiv import ArxivProvider
    from .providers.biorxiv import BiorxivProvider
    from .providers.crossref import CrossrefProvider
    from .providers.openalex import OpenAlexProvider
    from .providers.pubmed import PubMedProvider
    from .providers.semanticscholar import SemanticScholarProvider

    classes = {
        "openalex": OpenAlexProvider,
        "semanticscholar": SemanticScholarProvider,
        "crossref": CrossrefProvider,
        "arxiv": ArxivProvider,
        "pubmed": PubMedProvider,
        "biorxiv": BiorxivProvider,
    }
    return classes[name]()


def translate_provider(provider: Any, query: Query) -> dict[str, Any]:
    """One provider's dry run: ``executed_query``, the public ``request``, ``notes``, ``cannot_express``."""
    executed, request, notes = provider.translate(leg_query(query))
    return {
        "executed_query": executed,
        "request": public_request(request),
        "notes": list(notes),
        "cannot_express": list(provider.cannot_express(query)),
    }


def compile_plan(
    protocol: dict[str, Any] | str | Path,
    providers: Sequence[str] | None = None,
    selected: Sequence[str] | None = None,
) -> dict[str, Any]:
    """The per-database preview of a protocol's search, sending nothing.

    ``providers`` lists the databases to report on (default: every known one).
    A database the protocol selects is ``translated``; one it does not select is
    ``not_selected`` (or ``off_by_default`` for bioRxiv) and is not translated.
    The protocol selects what a run sent no list searches (``run_providers``):
    an explicit empty list selects the engine's default suite.

    ``selected`` (M10a) is the list a run is asked to search, in order; it
    replaces the protocol's list. Those rows come first in that order, then the
    others in ``providers`` order. The query is the protocol's either way, so a
    chosen row has the string that run's leg receives.
    """
    query, protocol_selected = compile_protocol_search(protocol)
    names = [canonical_provider(n) for n in (providers or KNOWN_PROVIDERS)]
    if selected is None:
        chosen = set(run_providers(protocol_selected))
    else:
        ordered = list(dict.fromkeys(canonical_provider(n) for n in selected))
        chosen = set(ordered)
        names = ordered + [n for n in dict.fromkeys(names) if n not in chosen]
    rows = []
    for name in names:
        row: dict[str, Any] = {
            "name": name, "selected": name in chosen,
            "executed_query": None, "request": None, "cannot_express": [], "notes": [],
        }
        if name not in chosen:
            row["status"] = "not_selected" if name in DEFAULT_PROVIDERS else "off_by_default"
        else:
            provider = _provider(name)
            try:
                row.update(translate_provider(provider, query))
                row["status"] = "translated"
            except NotImplementedError as exc:
                row["status"] = "selected"
                row["notes"] = [str(exc)]
            finally:
                close = getattr(getattr(provider, "client", None), "close", None)
                if close is not None:
                    _close_quietly(close)
        rows.append(row)
    return {"query": query, "providers": rows}


def _close_quietly(close: Any) -> None:
    import asyncio
    import inspect

    result = close()
    if inspect.isawaitable(result):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(result)
        else:  # pragma: no cover - called from a running loop: the client holds no open connection yet
            result.close()
