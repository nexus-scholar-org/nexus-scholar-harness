"""Open-science artifact (DAS/CAS) scan over extracted fulltext.

For each study, scan the extraction markdown for Data-Availability and
Code-Availability statements, classify each (public+link / statement-only /
request-only / explicitly-unavailable / not-stated), and record the matched
snippets for manual review. Deterministic regex baseline, cross-checkable
against the LLM-analyst aggregate.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_PATTERNS: list[tuple[str, str]] = [
    ("data_avail_kw", r"data\s+availab\w*"),
    ("availability_of_data", r"availab\w+\s+of\s+(?:the\s+)?data"),
    ("avail_on_request", r"availab\w+\s+on\s+(?:reasonable\s+)?request"),
    ("upon_request", r"upon\s+(?:reasonable\s+)?request"),
    ("data_is_available", r"(?:the\s+)?data\s+(?:is|are|will\s+be)\s+availab\w+"),
    ("dataset_available", r"(?:the\s+)?dataset\s+(?:is|are|will\s+be)\s+availab\w+"),
    ("avail_from_author", r"available\s+from\s+the\s+(?:corresponding\s+)?author"),
    ("publicly_available_data", r"publicly\s+availab\w+\s+(?:dataset|data)"),
    ("downloadable", r"can\s+be\s+(?:downloaded|accessed|obtained|requested)"),
    ("supplementary", r"supplementary\s+(?:material|data|information)"),
    ("released_dataset", r"released\s+(?:the\s+)?(?:dataset|data)"),
    ("repository_kw", r"(?:public|online|open)\s+repositor\w+"),
]
DATA_NEGATE: list[str] = [
    r"not\s+(?:publicly\s+)?availab\w+",
    r"cannot\s+be\s+(?:shared|released|distributed|disclosed)",
    r"are not\s+availab\w+",
    r"is not\s+availab\w+",
    r"not\s+disclosed",
    r"unavailable",
    r"no\s+data\s+availab\w+",
    r"will\s+not\s+be\s+published",
]

CODE_PATTERNS: list[tuple[str, str]] = [
    ("code_avail_kw", r"code\s+availab\w*"),
    ("source_code_available", r"source\s+code\s+(?:is|will\s+be|has\s+been)\s+availab\w+"),
    ("code_is_available", r"code\s+(?:is|will\s+be|has\s+been)\s+(?:made\s+)?availab\w+"),
    ("code_released", r"code\s+(?:is|has\s+been)\s+released"),
    ("our_code", r"our\s+code\b"),
    ("github_kw", r"\bgithub\b"),
    ("implementation_available", r"implementation\s+(?:is|was|has\s+been)\s+availab\w+"),
    ("project_repo", r"(?:project|training)\s+(?:code|repository)"),
]
CODE_NEGATE: list[str] = [
    r"no\s+code\b",
    r"code\s+will\s+not\s+be",
    r"code\s+is\s+not\s+availab\w+",
    r"cannot\s+be\s+released",
]

URL_PATTERN = re.compile(r"https?://[^\s\)\]\}\"}]+")
REPO_HOSTS = (
    "github.com",
    "gitlab.com",
    "zenodo",
    "figshare",
    "doi.org/10.5281",
    "osf.io",
    "kaggle.com",
    "huggingface.co",
    "paperswithcode.com",
)

CONTEXT = 140

DAS_CAS_LABELS = ("public+link", "request-only", "statement-only", "explicitly-unavailable", "not-stated")


def norm(text: str) -> str:
    return " ".join(text.split())


def find_matches(text: str, patterns: list[tuple[str, str]]) -> list[dict[str, Any]]:
    hits = []
    for key, pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            lo = max(0, m.start() - CONTEXT)
            hi = min(len(text), m.end() + CONTEXT)
            hits.append({"signal": key, "pattern": pat, "snippet": norm(text[lo:hi])})
    return hits


def links_near(text: str) -> list[dict[str, Any]]:
    found = []
    for m in URL_PATTERN.finditer(text):
        url = m.group(0).rstrip(".,;:")
        lo = max(0, m.start() - CONTEXT)
        hi = min(len(text), m.end() + CONTEXT)
        if any(host in url for host in REPO_HOSTS):
            found.append({"url": url, "snippet": norm(text[lo:hi])})
    return found


def classify(hits: list[dict[str, Any]], neg_hits: list[dict[str, Any]], links: list[dict[str, Any]]) -> str:
    has_positive = bool(hits)
    negated = bool(neg_hits)
    has_repo_link = bool(links)
    on_request = any(
        h["signal"] in ("avail_on_request", "upon_request", "avail_from_author") for h in hits
    )
    if negated and not has_positive:
        return "explicitly-unavailable"
    if has_positive:
        if has_repo_link:
            return "public+link"
        if on_request:
            return "request-only"
        return "statement-only"
    return "not-stated"


def scan_record(record: dict[str, Any], fulltext: str) -> dict[str, Any]:
    """Classify DAS/CAS for a single canonical record given its extraction fulltext."""
    data_hits = find_matches(fulltext, DATA_PATTERNS)
    data_neg = find_matches(fulltext, [("negation", p) for p in DATA_NEGATE])
    code_hits = find_matches(fulltext, CODE_PATTERNS)
    code_neg = find_matches(fulltext, [("negation", p) for p in CODE_NEGATE])
    links = links_near(fulltext)
    study = record.get("study") or {}
    return {
        "workspace_id": record["workspace_id"],
        "title": study.get("title"),
        "year": study.get("year"),
        "das": classify(data_hits, data_neg, links),
        "cas": classify(code_hits, code_neg, links),
        "data_signals": data_hits,
        "code_signals": code_hits,
        "repo_links": links,
    }


def run(
    records: list[dict[str, Any]],
    extracted_dir: Path,
    drop_missing: bool = True,
) -> dict[str, Any]:
    """Run the regex baseline over canonical records and extracted markdown files.

    extracted_dir holds <extracted_md> files named by record["study"]["extracted_md"].
    Returns the canonical out dict ({run_metadata, summary, results}); studies whose
    extraction is missing (or unset) are listed in run_metadata.missing_extractions.
    """
    rows = []
    missing = []
    for rec in records:
        md_name = (rec.get("study") or {}).get("extracted_md")
        wid = rec["workspace_id"]
        f = extracted_dir / (md_name or "")
        if not md_name or not f.exists():
            missing.append(wid)
            if not drop_missing:
                study = rec.get("study") or {}
                rows.append(
                    {
                        "workspace_id": wid,
                        "title": study.get("title"),
                        "year": study.get("year"),
                        "das": "not-stated",
                        "cas": "not-stated",
                        "data_signals": [],
                        "code_signals": [],
                        "repo_links": [],
                        "missing_extraction": True,
                    }
                )
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        rows.append(scan_record(rec, text))

    kids = Counter(r["das"] for r in rows)
    ck = Counter(r["cas"] for r in rows)
    both = sum(1 for r in rows if r["das"] == "public+link" and r["cas"] == "public+link")
    any_statement = sum(1 for r in rows if r["das"] not in ("not-stated",) or r["cas"] not in ("not-stated",))
    any_link = sum(1 for r in rows if r["repo_links"])

    return {
        "run_metadata": {
            "tool": "scholar-verify-kit/open-science",
            "run_date_utc": datetime.now().astimezone().isoformat(),
            "scan": "extracted fulltext markdown",
            "corpus_size": len(rows),
            "missing_extractions": missing,
        },
        "summary": {
            "studies_scanned": len(rows),
            "das": dict(kids),
            "cas": dict(ck),
            "both_public_link": both,
            "any_das_or_cas_statement": any_statement,
            "repo_link_present": any_link,
        },
        "results": rows,
    }


def render_report(out: dict[str, Any]) -> str:
    s = out["summary"]
    md = [
        "# Open-Science Artifact Scan (Data / Code Availability)",
        "",
        f"**Corpus**: {s['studies_scanned']} studies (post-audit); **run**: {out['run_metadata']['run_date_utc']}",
        "",
        "## Summary",
        "",
        "| Category | Data (DAS) | Code (CAS) |",
        "|---|---|---|",
    ]
    for label in DAS_CAS_LABELS:
        md.append(f"| {label} | {s['das'].get(label, 0)} | {s['cas'].get(label, 0)} |")
    md += [
        f"| Studies with a repo/data link anywhere | {s['repo_link_present']} | — |",
        f"| Studies with both public data AND code links | {s['both_public_link']} | — |",
        "",
        "Transparency context: only **published** repository links provide independently reproducible artifacts;"
        " `request-only` and `statement-only` claims cannot be re-verified from the record alone.",
        "",
    ]

    interesting = [
        r
        for r in out["results"]
        if r["das"] != "not-stated" or r["cas"] != "not-stated" or r["repo_links"]
    ]
    if interesting:
        md += ["## Per-study detail (any signal)", "", "| ID | Year | DAS | CAS | Links |", "|---|---|---|---|---|"]
        for r in interesting:
            links = "; ".join(x["url"] for x in r["repo_links"][:3]) or "—"
            md.append(f"| {r['workspace_id']} | {r['year']} | {r['das']} | {r['cas']} | {links} |")
        md.append("")
        md += ["## Matched context snippets", ""]
        for r in interesting:
            md.append(f"### {r['workspace_id']} — {r['das']} / {r['cas']}")
            for h in r["data_signals"] + r["code_signals"]:
                md.append(f"- `{h['signal']}` … {h['snippet'][:220]}")
            for link in r["repo_links"]:
                md.append(f"- link `{link['url']}` … {link['snippet'][:160]}")
            md.append("")
    else:
        md += ["## Per-study detail", "", "No data/code availability statements or repository links detected in the corpus.", ""]

    missing = out["run_metadata"].get("missing_extractions") or []
    if missing:
        md += [
            "## Studies without an extraction to scan",
            "",
            ", ".join(missing),
            "",
        ]

    md += [
        "## Methodological note",
        "",
        f"- Scan is regex-based over extraction text (`±`{CONTEXT} char windows); classify labels are heuristic and intended for manual verification.",
        "- `public+link` = positive statement AND an identifiable repository/data DOI URL; `request-only` = available on request;"
        "  `statement-only` = asserted availability without a link or request channel.",
        "- Regenerate with `scholar-verify open-science --workspace <dir>`.",
        "",
    ]
    return "\n".join(md)


def save_results(workspace: Path, name: str, out: dict[str, Any], report_md: str) -> None:
    out_dir = workspace / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{name}.md").write_text(report_md, encoding="utf-8")
