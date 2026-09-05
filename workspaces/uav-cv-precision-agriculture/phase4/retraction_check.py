"""Phase 4 workstream 1: retraction & publication-status checks for the 94-study corpus.

For every study in literature/extraction/merged/records.json:
  - OpenAlex  : is_retracted, last_status_in_oa        (via DOI, or arXiv id fallback)
  - Crossref  : message.update-to (retraction / correction / expression-of-concern / addendum)

Writes:
  phase4/retraction_status_check.json  per-study results + run metadata
  phase4/retraction_status_check.md    human-readable report

Usage: uv run python workspaces/uav-cv-precision-agriculture/phase4/retraction_check.py
"""
import json
import sys
import time
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import requests

WS = Path("workspaces/uav-cv-precision-agriculture")
HEADERS = {
    "User-Agent": "nexus-scholar-harness/1.0 (systematic review verification; contact: research@necus-scholar.example)"
}
RETRY_LIMIT = 3
SLEEP_S = 0.2
CROSSREF_UPDATE_TYPES = ("retraction", "expression-of-concern", "correction", "addendum", "correction-addendum")


def fetch_json(url, timeout=30):
    for attempt in range(RETRY_LIMIT):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code in (404, 400, 422):
                return {"_status": r.status_code}
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            if attempt == RETRY_LIMIT - 1:
                return {"_error": f"{type(exc).__name__}: {exc}"}
            time.sleep(2 * (attempt + 1))
    return {"_error": "unreachable"}


def openalex_by_doi(doi):
    return fetch_json(f"https://api.openalex.org/works/doi:{doi}")


def _norm_title(t):
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in t).split())


def openalex_by_arxiv(arxiv_id, title=None, year=None):
    abs_url = fetch_json(f"https://api.openalex.org/works/https://arxiv.org/abs/{arxiv_id}")
    if "id" in abs_url:
        return abs_url, "via_arxiv_abs"
    filter_url = fetch_json(f"https://api.openalex.org/works?filter=ids.arxiv:{arxiv_id}")
    works = filter_url.get("results") or []
    if works:
        return works[0], "via_arxiv_filter"
    if title and year:
        quoted = requests.utils.quote(f'"{_norm_title(title)}"')
        fuzz = fetch_json(
            f"https://api.openalex.org/works?filter=title.search:{quoted},publication_year:{year}&per-page=50"
        )
        for hit in fuzz.get("results") or []:
            hit_title = hit.get("title") or ""
            if _norm_title(hit_title) == _norm_title(title) and hit.get("publication_year") == int(year):
                return hit, "via_title_match"
    return {"_status": 404}, "unresolved"


def openalex_by_openalex_id(oa_id):
    return fetch_json(f"https://api.openalex.org/works/{oa_id}")


def crossref_by_doi(doi):
    if doi.lower().startswith("10.48550/"):  # DataCite-managed (arXiv); Crossref has no record
        return {"_datacite": True}
    return fetch_json(f"https://api.crossref.org/works/{doi}?mailto=verification@nexus-scholar.example")


def main():
    records = json.load(open(WS / "literature/extraction/merged/records.json", encoding="utf-8"))
    included = json.load(open(WS / "literature/included.json", encoding="utf-8"))
    by_id = {r["workspace_id"]: r for r in included}

    rows = []
    for rec in records:
        wid = rec["workspace_id"]
        meta = by_id.get(wid, {}) or {}
        ext = meta.get("external_ids") or {}
        doi = (ext.get("doi") or meta.get("doi") or "").strip() or None
        arxiv_id = (ext.get("arxiv_id") or "").strip() or None

        row = {
            "workspace_id": wid,
            "title": (rec.get("study") or {}).get("title") or meta.get("title"),
            "year": (rec.get("study") or {}).get("year") or meta.get("year"),
            "provider": meta.get("provider"),
            "doi": doi,
            "arxiv_id": arxiv_id,
            "openalex": {},
            "crossref": {},
            "flagged": False,
            "flag_reasons": [],
        }

        openalex_id = (ext.get("openalex_id") or "").strip().split("/")[-1] or None
        if doi:
            oa, lookup = openalex_by_doi(doi), "via_doi"
        elif arxiv_id:
            oa, lookup = openalex_by_arxiv(arxiv_id, rec_title := (row["title"] or ""), row.get("year"))
        else:
            oa, lookup = (openalex_by_openalex_id(openalex_id) if openalex_id else {"_status": 404}), "via_openalex_id"
        if "_status" in oa or "_error" in oa:
            row["openalex"] = {"is_retracted": None, "lookup": lookup, "error": oa}
        else:
            row["openalex"] = {
                "is_retracted": oa.get("is_retracted"),
                "last_status_in_oa": oa.get("last_status_in_oa"),
                "year_published": oa.get("publication_year"),
                "openalex_id": oa.get("id"),
                "lookup": lookup,
            }
            if doi is None:
                row["openalex"]["note"] = "looked up without DOI"

        if doi:
            cr = crossref_by_doi(doi)
            if "_status" in cr or "_error" in cr:
                row["crossref"] = {"update_to": [], "error": cr}
            elif "_datacite" in cr:
                row["crossref"] = {"update_to": [], "note": "DataCite-managed arXiv DOI; Crossref record not applicable"}
            else:
                updates = (cr.get("message") or {}).get("update-to") or []
                row["crossref"]["update_to"] = [
                    {"type": u.get("type"), "label": u.get("label"), "updated": u.get("updated")}
                    for u in updates
                ]
        else:
            row["crossref"]["note"] = "no DOI; Crossref lookup not applicable"

        openalex_flag = row["openalex"].get("is_retracted") is True
        crossref_flags = [
            u["type"] for u in row["crossref"].get("update_to", []) if u.get("type") in CROSSREF_UPDATE_TYPES
        ]
        row["flagged"] = openalex_flag or bool(crossref_flags)
        if openalex_flag:
            row["flag_reasons"].append("openalex:retracted")
        row["flag_reasons"].extend(f"crossref:{t}" for t in crossref_flags)

        rows.append(row)
        time.sleep(SLEEP_S)

    n_flagged = sum(1 for r in rows if r["flagged"])
    retracted_oa = [r for r in rows if r["openalex"].get("is_retracted") is True]
    crossref_updates = Counter()
    for r in rows:
        for u in r["crossref"].get("update_to", []):
            crossref_updates[u.get("type")] += 1
    status_oa = Counter(
        v for r in rows if (v := r["openalex"].get("last_status_in_oa")) is not None
    )
    errs = [r for r in rows if ("error" in r["openalex"] or "error" in r["crossref"])]
    unresolved = [
        r["workspace_id"] for r in rows if not ("error" in r["openalex"]) and r["openalex"].get("is_retracted") is None
    ]

    out = {
        "run_metadata": {
            "script": "phase4/retraction_check.py",
            "run_date_utc": datetime.now().astimezone().isoformat(),
            "data_sources": ["OpenAlex works API", "Crossref works API"],
            "corpus_size": len(rows),
        },
        "summary": {
            "studies_checked": len(rows),
            "flagged_any": n_flagged,
            "retracted_openalex": len(retracted_oa),
            "crossref_update_events": dict(crossref_updates),
            "openalex_provenance_status": dict(status_oa),
            "api_errors": len(errs),
            "unresolved_lookups": unresolved,
        },
        "results": rows,
    }
    out_path = WS / "phase4" / "retraction_status_check.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(out_path, "w", encoding="utf-8"), indent=2)

    _write_report(out_path, out)
    print(json.dumps(out["summary"], indent=2))


def _write_report(out_path: Path, out: dict) -> None:
    s = out["summary"]
    md = [
        "# Retraction & Publication-Status Check — UAV Precision Agriculture Corpus",
        "",
        f"**Corpus**: {s['studies_checked']} studies (post-audit); **run**: {out['run_metadata']['run_date_utc']}",
        f"**Sources**: OpenAlex `is_retracted`/`last_status_in_oa` + Crossref `update-to`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
f"| Studies checked | {s['studies_checked']} |",
        f"| Flagged (any retraction/correction/EoC signal) | {s['flagged_any']} |",
        f"| Retracted (OpenAlex) | {s['retracted_openalex']} |",
        f"| Crossref update-to events | {s['crossref_update_events'] or 'none'} |",
        f"| OpenAlex provenance (`last_status_in_oa`) | {s['openalex_provenance_status'] or 'not populated for this corpus'} |",
        f"| Unresolved lookups | {len(s['unresolved_lookups'])} |",
        "",
    ]

    unresolved = s["unresolved_lookups"]
    if unresolved:
        md += ["## Unresolved lookups", "", "The following studies could not be resolved to an OpenAlex work (no DOI / arXiv id / OpenAlex id matched):", "", "| ID | DOI | arXiv | OpenAlex id |", "|---|---|---|---|"]
        for r in out["results"]:
            if r["workspace_id"] in unresolved:
                oa_id = r["openalex"].get("openalex_id") or ""
                md.append(f"| {r['workspace_id']} | {r['doi'] or '—'} | {r['arxiv_id'] or '—'} | {oa_id} |")
        md.append("")

    flagged = [r for r in out["results"] if r["flagged"]]
    if flagged:
        md += ["## Flagged studies", "", "| ID | Year | DOI | Reasons |", "|---|---|---|---|"]
        for r in flagged:
            md.append(f"| {r['workspace_id']} | {r['year']} | {r['doi'] or '—'} | {'; '.join(r['flag_reasons']) or '—'} |")
        md.append("")
        md.append("> Corrections (minor errata) do not invalidate the extraction; retractions or expressions of concern would require re-review of the cited record.")
        md.append("")
    else:
        md += ["## Flagged studies", "", "None.", ""]

    arxiv_only = [r for r in out["results"] if r["doi"] is None]
    if arxiv_only:
        md += [
            "## arXiv-only records (no formal retraction channel)",
            "",
            "The following studies have no DOI and are arXiv-tracked; OpenAlex was consulted through a DOI-independent lookup (arXiv id → title/year match → OpenAlex id):",
            "",
            "| ID | Title | OpenAlex retracted |",
            "|---|---|---|",
        ]
        for r in arxiv_only:
            md.append(f"| {r['workspace_id']} | {r['title']} | {r['openalex'].get('is_retracted')} |")
        md.append("")

    errs = [r for r in out["results"] if "error" in r["openalex"] or "error" in r["crossref"]]
    if errs:
        md += ["## API errors (lookups that did not resolve)", "", "| ID | DOI | Detail |", "|---|---|---|"]
        for r in errs:
            detail = r["openalex"].get("error") or r["crossref"].get("error")
            md.append(f"| {r['workspace_id']} | {r['doi'] or '—'} | `{detail}` |")
        md.append("")

    md += [
        "## Methodological note",
        "",
        "- Correction markers from Crossref may be self-published errata; treat as low-severity unless `type == retraction` or `expression-of-concern`.",
        "- OpenAlex `is_retracted` reflects the current (2026) metadata snapshot, not publisher live status.",
        "- All per-study rows are in `phase4/retraction_status_check.json`; regenerate with `uv run python phase4/retraction_check.py`.",
        "",
    ]
    open(out_path.with_name("retraction_status_check.md"), "w", encoding="utf-8").write("\n".join(md))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()