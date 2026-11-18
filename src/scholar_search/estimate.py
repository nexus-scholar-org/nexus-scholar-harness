"""The size estimate before a harvest (M10b; `docs/ux/phase1-discovery/final/01-plan.md` "Size estimate").

Two parts:

* ``count_providers(query, names)`` asks each database how many records match
  the planned query (``BaseAPIProvider.count``: one request, no record body),
  in parallel. A database that fails or cannot report a total is its own row,
  never an error of the whole estimate.
* ``summarize(rows, cap=..., limit=..., pace_seconds=..., year_window=...)`` is
  the arithmetic the screen prints: what each database would fetch under the
  cap, the records and works range, the screening hours, the warning against
  the size limit and one recommendation. The browser computes none of it.

Nothing here writes a file or a journal row.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Iterable, Sequence
from typing import Any

from .engine import provider_error_code
from .models import Query
from .plan import leg_query

#: The general size limit, in works, when the researcher stated no planned number (decided 2026-11-15, R3).
SIZE_WARN_WORKS = 1_000
#: A suggested cap under this would drop most of what a database holds: narrowing is advised instead.
SUGGESTED_CAP_MIN = 100
#: How long counts are kept for the same protocol and databases, in seconds.
ESTIMATE_TTL = 600
#: The longest one database's count may take, in seconds. The HTTP client retries a 429 or a 5xx
#: and waits out ``Retry-After``; past this the row is ``failed`` with ``PROVIDER_TIMEOUT``, so a slow
#: database never times the whole estimate out at the browser proxy (120 s).
COUNT_TIMEOUT = 45.0
#: The default screening pace, an editable assumption (decided 2026-11-15): seconds per record, one reviewer.
DEFAULT_PACE_SECONDS = 30
PACE_MIN, PACE_MAX = 5, 600

#: The databases whose count ignores the year window (it is filtered after retrieval).
UPPER_BOUND_WITH_YEARS = frozenset({"arxiv"})
#: A row's status when a total is known.
COUNTED = ("counted", "from_recall_check")
#: Rows that are not part of this harvest.
NOT_ASKED = ("not_selected", "off_by_default")

WORKS_ASSUMPTION = "low: every record of a smaller database is a duplicate of the largest; high: no duplicate"


def _provider(name: str) -> Any:
    from .plan import _provider as make

    return make(name)


async def _close(provider: Any) -> None:
    close = getattr(getattr(provider, "client", None), "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result


async def count_one(name: str, query: Query) -> dict[str, Any]:
    """One database's count row: ``counted``, ``not_countable`` or ``failed`` with the harvest's codes."""
    provider = _provider(name)
    row: dict[str, Any] = {"name": name, "status": "counted", "reported_total": None, "error": None, "error_code": None}
    try:
        row["reported_total"] = await asyncio.wait_for(provider.count(leg_query(query)), timeout=COUNT_TIMEOUT)
        if row["reported_total"] is None:
            row.update(status="failed", error=f"{name} answered without a total")
    except NotImplementedError:
        row["status"] = "not_countable"
    except (TimeoutError, asyncio.TimeoutError):
        row.update(status="failed", error=f"{name} did not answer the count within {COUNT_TIMEOUT:g} s",
                   error_code="PROVIDER_TIMEOUT")
    except Exception as exc:  # noqa: BLE001 - a database's failure is its row, never the estimate's
        row.update(status="failed", error=str(exc)[:300], error_code=provider_error_code(exc))
    finally:
        await _close(provider)
    return row


async def count_providers(query: Query, names: Sequence[str]) -> dict[str, dict[str, Any]]:
    """Each database's count row, asked in parallel (the shared per-host budgets still apply)."""
    rows = await asyncio.gather(*(count_one(name, query) for name in names))
    return {row["name"]: row for row in rows}


def _hours(works: int | None, pace_seconds: int) -> float | None:
    return None if works is None else round(works * pace_seconds / 3600, 1)


def _suggested_cap(totals: Iterable[int], cap: int, limit: int) -> int:
    """The largest per-database cap ``c`` (0 to ``cap``) with ``sum(min(t, c))`` at most ``limit``."""
    totals = list(totals)
    low, high = 0, cap
    while low < high:
        mid = (low + high + 1) // 2
        if sum(min(t, mid) for t in totals) <= limit:
            low = mid
        else:
            high = mid - 1
    return low


def summarize(
    rows: Sequence[dict[str, Any]], *, cap: int, limit: int, pace_seconds: int, year_window: bool,
) -> dict[str, Any]:
    """The estimate of a list of count rows (one per database, in order).

    Per database ``fetch_estimate = min(reported_total, cap)``, ``cap_binds`` and
    ``not_fetched`` (what the cap leaves out).
    Records: high is the sum, low the same sum without an upper-bound count
    (arXiv with a year window). Works: low is the largest exact single
    estimate (every smaller database a duplicate of it), high the sum (no
    duplicate). A database not counted leaves every upper end unknown.
    """
    out_rows: list[dict[str, Any]] = []
    exact: list[int] = []
    every: list[int] = []
    totals: list[int] = []
    counted_all = True
    for row in rows:
        row = {"notes": [], "error": None, "error_code": None, **row}
        status, total = row.get("status"), row.get("reported_total")
        upper = bool(year_window) and row["name"] in UPPER_BOUND_WITH_YEARS
        row.update(fetch_estimate=None, fetch_is_upper_bound=False, cap_binds=None, not_fetched=None)
        if status in NOT_ASKED:
            out_rows.append(row)
            continue
        if status in COUNTED and isinstance(total, int):
            fetch = min(total, cap)
            row.update(fetch_estimate=fetch, fetch_is_upper_bound=upper, cap_binds=total > cap, not_fetched=total - fetch)
            every.append(fetch)
            totals.append(total)
            if not upper:
                exact.append(fetch)
        else:
            counted_all = False
        out_rows.append(row)

    records_low = sum(exact)
    records_high = sum(every) if counted_all else None
    works_low = max(exact, default=0)
    works_high = records_high
    if works_low > limit:
        level = "warning"
    elif works_high is None or works_high > limit:
        level = "note"
    else:
        level = "none"

    recommendation: dict[str, Any] = {"kind": None, "cap": None, "expected_works": None, "cuts": None}
    if level != "none":
        suggested = _suggested_cap(totals, cap, limit) if counted_all else 0
        if counted_all and suggested >= SUGGESTED_CAP_MIN:
            kept = [min(t, suggested) for t in totals]
            kept_exact = [min(r["reported_total"], suggested) for r in out_rows
                          if r["fetch_estimate"] is not None and not r["fetch_is_upper_bound"]]
            recommendation = {
                "kind": "cap", "cap": suggested,
                "expected_works": {"low": max(kept_exact, default=0), "high": sum(kept)},
                "cuts": sum(1 for t in totals if t > suggested),
            }
        else:
            recommendation = {"kind": "narrow", "cap": None, "expected_works": None, "cuts": None}

    return {
        "providers": out_rows,
        "estimate": {
            "counted_all": counted_all,
            "records": {"low": records_low, "high": records_high},
            "works": {"low": works_low, "high": works_high},
            "assumption": WORKS_ASSUMPTION,
        },
        "effort": {"pace_seconds": pace_seconds,
                   "hours": {"low": _hours(works_low, pace_seconds), "high": _hours(works_high, pace_seconds)}},
        "warn": {"level": level, "threshold_works": limit},
        "recommendation": recommendation,
    }
