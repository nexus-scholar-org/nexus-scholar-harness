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
from .models import Query
from .protocol_adapter import compile_protocol_search
from .providers.base import public_request

#: Every database the engine knows, in the order a plan lists them.
KNOWN_PROVIDERS: tuple[str, ...] = ("openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv")
#: The databases a protocol selects unless it says otherwise; bioRxiv is off by default.
DEFAULT_PROVIDERS: tuple[str, ...] = ("openalex", "semanticscholar", "crossref", "arxiv", "pubmed")


def canonical_provider(name: str) -> str:
    key = str(name).lower().strip().replace("-", "_").replace(" ", "_")
    return "semanticscholar" if key == "semantic_scholar" else key


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
) -> dict[str, Any]:
    """The per-database preview of a protocol's search, sending nothing.

    ``providers`` lists the databases to report on (default: every known one).
    A database the protocol selects is ``translated``; one it does not select is
    ``not_selected`` (or ``off_by_default`` for bioRxiv) and is not translated.
    """
    query, selected = compile_protocol_search(protocol)
    chosen = {canonical_provider(n) for n in selected}
    rows = []
    for name in [canonical_provider(n) for n in (providers or KNOWN_PROVIDERS)]:
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
