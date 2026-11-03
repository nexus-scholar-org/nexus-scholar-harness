"""Retraction & publication-status verification (Phase 4 workstream 1).

For every study in a workspace's merged extraction records:
  - OpenAlex : is_retracted, last_status_in_oa  (via DOI, or arXiv id fallback)
  - Crossref : message.update-to (retraction / correction / expression-of-concern / addendum)

Outputs a per-study result list plus a human-readable Markdown report.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from .http_client import DEFAULT_SLEEP_S, VerifyHttpClient

CROSSREF_UPDATE_TYPES = (
    "retraction",
    "expression-of-concern",
    "correction",
    "addendum",
    "correction-addendum",
)


def _norm_title(t: str) -> str:
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in t).split())


class RetractionChecker:
    """Checks each canonical record against OpenAlex + Crossref for retraction/correction signals."""

    def __init__(
        self,
        http: VerifyHttpClient | None = None,
        sleep_s: float = DEFAULT_SLEEP_S,
    ) -> None:
        self.http = http or VerifyHttpClient()
        self.sleep_s = sleep_s

    def check(self, records: list[dict[str, Any]], included: list[dict[str, Any]]) -> dict[str, Any]:
        """Run the full check over the canonical records.

        records: the merged extraction records (literature/extraction/merged/records.json).
        included: the screened included.json documents (used for workspace_id -> DOI map).
        """
        by_id = {r.get("workspace_id"): r for r in included}
        rows = []
        for rec in records:
            rows.append(self._check_one(rec, by_id.get(rec.get("workspace_id"), {}) or {}))
            import time

            time.sleep(self.sleep_s)

        summary = self._summarize(rows)
        out = {
            "run_metadata": {
                "tool": "scholar-verify-kit/retraction",
                "run_date_utc": datetime.now().astimezone().isoformat(),
                "data_sources": ["OpenAlex works API", "Crossref works API"],
                "corpus_size": len(rows),
            },
            "summary": summary,
            "results": rows,
        }
        return out

    # -- internals -------------------------------------------------------------

    def _openalex_by_doi(self, doi: str) -> dict[str, Any]:
        return self.http.fetch_json(f"https://api.openalex.org/works/doi:{doi}")

    def _openalex_by_openalex_id(self, oa_id: str) -> dict[str, Any]:
        return self.http.fetch_json(f"https://api.openalex.org/works/{oa_id}")

    def _openalex_by_arxiv(self, arxiv_id: str, title: str | None = None, year: int | None = None):
        abs_url = self.http.fetch_json(f"https://api.openalex.org/works/https://arxiv.org/abs/{arxiv_id}")
        if "id" in abs_url:
            return abs_url, "via_arxiv_abs"
        filter_url = self.http.fetch_json(f"https://api.openalex.org/works?filter=ids.arxiv:{arxiv_id}")
        works = filter_url.get("results") or []
        if works:
            return works[0], "via_arxiv_filter"
        if title and year:
            quoted = requests.utils.quote(f'"{_norm_title(title)}"')
            fuzz = self.http.fetch_json(
                f"https://api.openalex.org/works?filter=title.search:{quoted},publication_year:{year}&per-page=50"
            )
            for hit in fuzz.get("results") or []:
                hit_title = hit.get("title") or ""
                if _norm_title(hit_title) == _norm_title(title) and hit.get("publication_year") == int(year):
                    return hit, "via_title_match"
        return {"_status": 404}, "unresolved"

    def _crossref_by_doi(self, doi: str) -> dict[str, Any]:
        if doi.lower().startswith("10.48550/"):  # DataCite-managed (arXiv); Crossref has no record
            return {"_datacite": True}
        return self.http.fetch_json(f"https://api.crossref.org/works/{doi}?mailto=verification@nexus-scholar.example")

    def _check_one(self, rec: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
        wid = rec["workspace_id"]
        ext = meta.get("external_ids") or {}
        doi = (ext.get("doi") or meta.get("doi") or "").strip() or None
        arxiv_id = (ext.get("arxiv_id") or "").strip() or None
        openalex_id = (ext.get("openalex_id") or "").strip().split("/")[-1] or None

        row: dict[str, Any] = {
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

        if doi:
            oa, lookup = self._openalex_by_doi(doi), "via_doi"
        elif arxiv_id:
            oa, lookup = self._openalex_by_arxiv(arxiv_id, row["title"] or "", row.get("year"))
        else:
            oa, lookup = (
                self._openalex_by_openalex_id(openalex_id) if openalex_id else {"_status": 404}
            ), "via_openalex_id"
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
            cr = self._crossref_by_doi(doi)
            if "_status" in cr or "_error" in cr:
                row["crossref"] = {"update_to": [], "error": cr}
            elif "_datacite" in cr:
                row["crossref"] = {"update_to": [], "note": "DataCite-managed arXiv DOI; Crossref record not applicable"}
            else:
                updates = (cr.get("message") or {}).get("update-to") or []
                row["crossref"]["update_to"] = [
                    {"type": u.get("type"), "label": u.get("label"), "updated": u.get("updated")} for u in updates
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
        return row

    @staticmethod
    def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        n_flagged = sum(1 for r in rows if r["flagged"])
        retracted_oa = [r for r in rows if r["openalex"].get("is_retracted") is True]
        crossref_updates: Counter[str] = Counter()
        for r in rows:
            for u in r["crossref"].get("update_to", []):
                crossref_updates[u.get("type")] += 1
        status_oa: Counter[str] = Counter(
            v for r in rows if (v := r["openalex"].get("last_status_in_oa")) is not None
        )
        errs = [r for r in rows if "error" in r["openalex"] or "error" in r["crossref"]]
        unresolved = [
            r["workspace_id"]
            for r in rows
            if "error" not in r["openalex"] and r["openalex"].get("is_retracted") is None
        ]
        return {
            "studies_checked": len(rows),
            "flagged_any": n_flagged,
            "retracted_openalex": len(retracted_oa),
            "crossref_update_events": dict(crossref_updates),
            "openalex_provenance_status": dict(status_oa),
            "api_errors": len(errs),
            "unresolved_lookups": unresolved,
        }


def render_retraction_report(out: dict[str, Any]) -> str:
    """Render the retraction check result dict to a Markdown report string."""
    s = out["summary"]
    md = [
        "# Retraction & Publication-Status Check",
        "",
        f"**Corpus**: {s['studies_checked']} studies (post-audit); **run**: {out['run_metadata']['run_date_utc']}",
        "**Sources**: OpenAlex `is_retracted`/`last_status_in_oa` + Crossref `update-to`",
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
        md += [
            "## Unresolved lookups",
            "",
            "The following studies could not be resolved to an OpenAlex work (no DOI / arXiv id / OpenAlex id matched):",
            "",
            "| ID | DOI | arXiv | OpenAlex id |",
            "|---|---|---|---|",
        ]
        for r in out["results"]:
            if r["workspace_id"] in unresolved:
                oa_id = r["openalex"].get("openalex_id") or ""
                md.append(f"| {r['workspace_id']} | {r['doi'] or '—'} | {r['arxiv_id'] or '—'} | {oa_id} |")
        md.append("")

    flagged = [r for r in out["results"] if r["flagged"]]
    if flagged:
        md += ["## Flagged studies", "", "| ID | Year | DOI | Reasons |", "|---|---|---|---|"]
        for r in flagged:
            md.append(
                f"| {r['workspace_id']} | {r['year']} | {r['doi'] or '—'} | {'; '.join(r['flag_reasons']) or '—'} |"
            )
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
        "- OpenAlex `is_retracted` reflects the current metadata snapshot, not publisher live status.",
        "- All per-study rows are in the JSON output; regenerate with `scholar-verify retraction --workspace <dir>`.",
        "",
    ]
    return "\n".join(md)


def save_results(workspace: Path, name: str, out: dict[str, Any], report_md: str) -> None:
    """Write the JSON result + Markdown report into the workspace's phase4/verify dir."""
    out_dir = workspace / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{name}.md").write_text(report_md, encoding="utf-8")
