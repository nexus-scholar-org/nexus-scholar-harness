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

from collections.abc import Sequence
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


def protocol_databases_left_out(manifest: dict[str, Any], fallback: Sequence[str] | None = None) -> list[str]:
    """The protocol databases a run's own choice left out (M10a), in the known order.

    Empty unless the run recorded ``requested_providers``. The protocol's list is
    the one the run recorded in ``protocol_search.databases`` (``None``: the
    protocol named none, so the adapter's default), read as a run reads it
    (``run_providers``); ``fallback`` stands in for a run without that record.
    """
    from .plan import (
        KNOWN_PROVIDERS,
        canonical_provider,
        protocol_default_providers,
        run_providers,
    )

    requested = manifest.get("requested_providers")
    if not isinstance(requested, list):
        return []
    record = manifest.get("protocol_search")
    if isinstance(record, dict) and "databases" in record:
        databases = record["databases"]
        names = protocol_default_providers() if databases is None else databases
    elif fallback is not None:
        names = fallback
    else:
        return []
    protocol = set(run_providers(names))
    asked = {canonical_provider(n) for n in requested}
    return [n for n in KNOWN_PROVIDERS if n in protocol and n not in asked]


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
    left_out = protocol_databases_left_out(manifest)
    if left_out:
        lines.append(f"- Protocol databases not selected for this run: {_names(left_out)}")
    if manifest.get("cap_override") is not None:
        lines.append(f"- Run override cap: {manifest['cap_override']} records per database")
    for note in manifest.get("notes") or []:
        lines.append(f"- Note: {_cell(note)}")
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


def _names(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def render_methods_text(
    legs: list[dict[str, Any]],
    imports: list[dict[str, Any]] | None = None,
    dedup: dict[str, Any] | None = None,
    *,
    query_text: str | None = None,
    years: tuple[Any, Any] | None = None,
    cap_override: int | None = None,
    not_selected_for_run: Sequence[str] | None = None,
) -> str:
    """The search paragraph of a methods section, every number from a field (packet §4.6).

    One sentence for the searched databases, one per database with its counts
    and cap, one for the imported exports and one for deduplication. It states
    what the run recorded and nothing else: no adjectives, no claims about
    completeness beyond the cap flags. ``not_selected_for_run`` (M10a,
    ``protocol_databases_left_out``) adds one sentence after the first.
    """
    searched = [leg for leg in legs if leg.get("status") != "pending"]
    dates = sorted(str(leg.get("started_at") or "")[:10] for leg in searched if leg.get("started_at"))
    names = [str(leg.get("provider")) for leg in searched]
    parts: list[str] = []
    if searched:
        when = f" on {dates[0]}" if dates and dates[0] == dates[-1] else (
            f" between {dates[0]} and {dates[-1]}" if dates else "")
        lead = f"We searched {len(searched)} database{'s' if len(searched) != 1 else ''} ({_names(names)}){when}"
        if query_text:
            lead += f" with the query `{query_text}`"
        if years and (years[0] or years[1]):
            lead += f", limited to publication years {years[0] or '…'}–{years[1] or '…'}"
        parts.append(lead + ".")
        if not_selected_for_run:
            left_out = list(not_selected_for_run)
            verb = "was" if len(left_out) == 1 else "were"
            parts.append(f"The protocol also names {_names(left_out)}, which {verb} not selected for this run.")
        if cap_override is not None:
            parts.append(f"This run fetched at most {cap_override} records per database (a run override of the protocol cap).")
        for leg in searched:
            name = leg.get("provider")
            total = leg.get("reported_total")
            fetched = int(leg.get("fetched") or 0)
            status = leg.get("status")
            if status == "failed":
                parts.append(f"{name} did not answer ({leg.get('error_code') or 'failed'}); it contributed {fetched} records.")
                continue
            sentence = f"{name} reported {total} records and {fetched} were fetched" if total is not None else (
                f"{name} reported no total and {fetched} records were fetched")
            if status == "stopped":
                sentence += "; the search was stopped by the researcher, so the count is a lower bound"
            elif leg.get("cap_hit"):
                sentence += f"; the cap of {leg.get('cap')} records was reached, so the count is a lower bound"
            parts.append(sentence + ".")
    imports = imports or []
    groups = _import_groups(imports)
    if groups:
        # M3f-combined-corpus (PRISMA-S): each database the researcher searched
        # and exported, with the search details they stated, "not stated" otherwise.
        rows = []
        for group in groups:
            n = group["records"]
            details = [f"{n} record{'s' if n != 1 else ''}"]
            details.append(f"searched on {' and '.join(group['dates'])}" if group["dates"] else "date searched not stated")
            details.append(
                "search string: " + "; ".join(f"`{q}`" for q in group["queries"]) if group["queries"]
                else "search string not stated"
            )
            if group["limits"]:
                details.append("limits: " + "; ".join(group["limits"]))
            rows.append(f"{group['label']} ({'; '.join(details)})")
        k = len(groups)
        lead = "We also searched" if searched else "We searched"
        parts.append(
            f"{lead} {k} database{'s' if k != 1 else ''} ourselves and imported "
            f"{'their exports' if k != 1 else 'its export'}: {_names(rows)}."
        )
        total = sum(group["records"] for group in groups)
        parts.append(
            f"The {total} imported record{'s were' if total != 1 else ' was'} not checked against Crossref or OpenAlex."
        )
    if dedup and dedup.get("unique_works") is not None:
        if groups:
            sources = len({str(leg.get("provider")) for leg in searched}) + len(groups)
            removed = dedup.get("removed")
            parts.append(
                f"Deduplication across the {sources} sources removed {removed} record{'s' if removed != 1 else ''}, "
                f"leaving {dedup.get('unique_works')} unique works."
            )
        else:
            parts.append(
                f"Deduplication removed {dedup.get('removed')} records, leaving {dedup.get('unique_works')} unique works."
            )
    return " ".join(parts)


def _import_groups(imports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Staged export files summed per database label, in the order the labels first appear."""
    groups: dict[str, dict[str, Any]] = {}
    for imp in imports:
        label = str(imp.get("label"))
        group = groups.setdefault(label, {"label": label, "records": 0, "dates": [], "queries": [], "limits": []})
        group["records"] += int(imp.get("records") or 0)
        for key, value in (("dates", imp.get("searched_on")), ("queries", imp.get("query")), ("limits", imp.get("limits"))):
            if value and value not in group[key]:
                group[key].append(value)
    for group in groups.values():
        group["dates"].sort()
    return list(groups.values())
