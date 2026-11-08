"""PRISMA-S style search report for one discovery run (M3a-discovery D9).

Rendered from the run's ``legs.json`` manifest (``search_runs/run_NNN/``), so
the report states exactly what the journal recorded: for each database, the
query string that was sent, the total the database reported, how many records
were fetched, the cap that applied and whether it stopped the search, and
when. PRISMA-S (Rethlefsen et al., 2021) items 1, 8 and 13: databases, full
search strings, dates searched. The contact address and API keys are never in
a leg, so they cannot reach the report.
"""

from __future__ import annotations

from typing import Any

_CAP_SOURCES = {
    "protocol": "protocol (method.retrieval_cap)",
    "run_override": "run override",
    "query": "caller",
    "engine_ceiling": "engine ceiling",
}


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _total(leg: dict[str, Any]) -> str:
    total = leg.get("reported_total")
    return "not reported" if total is None else str(total)


def _cap(leg: dict[str, Any]) -> str:
    cap = leg.get("cap")
    source = _CAP_SOURCES.get(str(leg.get("cap_source")), str(leg.get("cap_source") or ""))
    text = f"{cap} ({source})" if cap is not None else "none"
    if leg.get("cap_hit"):
        if leg.get("reported_total") is None:
            text += ", cap reached: the database reported no total, more may exist"
        else:
            text += ", cap reached: more records exist"
    return text


def _date(leg: dict[str, Any]) -> str:
    return str(leg.get("started_at") or "")[:10]


def render_search_report(manifest: dict[str, Any]) -> str:
    """Markdown for one run's search, one table row per database."""
    legs = list(manifest.get("legs") or [])
    years = ""
    if manifest.get("year_min") or manifest.get("year_max"):
        years = f"{manifest.get('year_min') or '…'}–{manifest.get('year_max') or '…'}"
    lines = [
        f"# Search report (PRISMA-S): {manifest.get('run', '')}",
        "",
        f"- Run status: {manifest.get('status', '')}",
        f"- Query id: {manifest.get('query_id', '')}",
        f"- Protocol query: `{_cell(manifest.get('query_text'))}`",
    ]
    if years:
        lines.append(f"- Publication years: {years}")
    lines += [
        "",
        "| Database | Executed query | Reported total | Fetched | Cap | Status | Date |",
        "| :-- | :-- | --: | --: | :-- | :-- | :-- |",
    ]
    for leg in legs:
        status = str(leg.get("status") or "")
        if leg.get("error"):
            status += f": {leg['error']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(leg.get("provider")),
                    f"`{_cell(leg.get('executed_query'))}`" if leg.get("executed_query") else "not sent",
                    _total(leg),
                    str(leg.get("fetched", 0)),
                    _cell(_cap(leg)),
                    _cell(status),
                    _date(leg),
                ]
            )
            + " |"
        )
    notes = [(leg.get("provider"), note) for leg in legs for note in (leg.get("notes") or [])]
    if notes:
        lines += ["", "## Notes on the executed queries", ""]
        lines += [f"- {provider}: {note}" for provider, note in notes]
    filters = [(leg.get("provider"), leg.get("request")) for leg in legs if leg.get("request")]
    if filters:
        lines += ["", "## Request parameters (as sent, without contact address or keys)", ""]
        for provider, request in filters:
            params = ", ".join(f"{k}={_cell(v)}" for k, v in sorted(request.items()))
            lines.append(f"- {provider}: {params}")
    lines.append("")
    return "\n".join(lines)
