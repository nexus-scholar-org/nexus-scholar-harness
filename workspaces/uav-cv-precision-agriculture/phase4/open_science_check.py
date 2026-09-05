"""Phase 4 workstream 2: open-science artifact (DAS/CAS) scan.

For each of the 94 corpus studies, scans the extracted fulltext for
Data-Availability (DAS) and Code-Availability (CAS) statements, classifies
them (public+link / statement-only / request-only / explicitly-unavailable /
not-stated), and records the matched snippets for manual review.

Writes:
  phase4/open_science_artifacts.json   per-study classification + contexts
  phase4/open_science_artifacts.md     human-readable report

Usage: uv run python workspaces/uav-cv-precision-agriculture/phase4/open_science_check.py
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

WS = Path("workspaces/uav-cv-precision-agriculture")

DATA_PATTERNS = [
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
DATA_NEGATE = [
    r"not\s+(?:publicly\s+)?availab\w+",
    r"cannot\s+be\s+(?:shared|released|distributed|disclosed)",
    r"are not\s+availab\w+",
    r"is not\s+availab\w+",
    r"not\s+disclosed",
    r"unavailable",
    r"no\s+data\s+availab\w+",
    r"will\s+not\s+be\s+published",
]

CODE_PATTERNS = [
    ("code_avail_kw", r"code\s+availab\w*"),
    ("source_code_available", r"source\s+code\s+(?:is|will\s+be|has\s+been)\s+availab\w+"),
    ("code_is_available", r"code\s+(?:is|will\s+be|has\s+been)\s+(?:made\s+)?availab\w+"),
    ("code_released", r"code\s+(?:is|has\s+been)\s+released"),
    ("our_code", r"our\s+code\b"),
    ("github_kw", r"\bgithub\b"),
    ("implementation_available", r"implementation\s+(?:is|was|has\s+been)\s+availab\w+"),
    ("project_repo", r"(?:project|training)\s+(?:code|repository)"),
]
CODE_NEGATE = [
    r"no\s+code\b",
    r"code\s+will\s+not\s+be",
    r"code\s+is\s+not\s+availab\w+",
    r"cannot\s+be\s+released",
]

URL_PATTERN = re.compile(r"https?://[^\s\)\]\}\"}]+")
REPO_HOSTS = ("github.com", "gitlab.com", "zenodo", "figshare", "doi.org/10.5281", "osf.io", "kaggle.com", "huggingface.co", "paperswithcode.com")

CONTEXT = 140


def norm(text):
    return " ".join(text.split())


def find_matches(text, patterns):
    hits = []
    for key, pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            lo = max(0, m.start() - CONTEXT)
            hi = min(len(text), m.end() + CONTEXT)
            hits.append({"signal": key, "pattern": pat, "snippet": norm(text[lo:hi])})
    return hits


def links_near(urls, text):
    found = []
    for m in URL_PATTERN.finditer(text):
        url = m.group(0).rstrip(".,;:")
        lo = max(0, m.start() - CONTEXT)
        hi = min(len(text), m.end() + CONTEXT)
        if any(host in url for host in REPO_HOSTS):
            found.append({"url": url, "snippet": norm(text[lo:hi])})
    return found


def classify(hits, neg_hits, links):
    has_positive = bool(hits)
    negated = bool(neg_hits)
    has_repo_link = bool(links)
    on_request = any(h["signal"] in ("avail_on_request", "upon_request", "avail_from_author") for h in hits)

    if negated and not has_positive:
        label = "explicitly-unavailable"
    elif has_positive:
        if has_repo_link:
            label = "public+link"
        elif on_request:
            label = "request-only"
        else:
            label = "statement-only"
    else:
        label = "not-stated"
    return label


def main():
    records = json.load(open(WS / "literature/extraction/merged/records.json", encoding="utf-8"))
    rows = []
    missing = []
    for rec in records:
        md_name = (rec.get("study") or {}).get("extracted_md")
        wid = rec["workspace_id"]
        f = WS / "extracted" / (md_name or "")
        if not md_name or not f.exists():
            missing.append(wid)
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        data_hits = find_matches(text, DATA_PATTERNS)
        data_neg = find_matches(text, [("negation", p) for p in DATA_NEGATE])
        code_hits = find_matches(text, CODE_PATTERNS)
        code_neg = find_matches(text, [("negation", p) for p in CODE_NEGATE])
        links = links_near(URL_PATTERN, text)
        rows.append(
            {
                "workspace_id": wid,
                "title": (rec.get("study") or {}).get("title"),
                "year": (rec.get("study") or {}).get("year"),
                "das": classify(data_hits, data_neg, links),
                "cas": classify(code_hits, code_neg, links),
                "data_signals": data_hits,
                "code_signals": code_hits,
                "repo_links": links,
            }
        )

    kids = Counter(r["das"] for r in rows)
    ck = Counter(r["cas"] for r in rows)
    both = sum(1 for r in rows if r["das"] == "public+link" and r["cas"] == "public+link")
    any_statement = sum(1 for r in rows if r["das"] not in ("not-stated",) or r["cas"] not in ("not-stated",))
    any_link = sum(1 for r in rows if r["repo_links"])

    out = {
        "run_metadata": {
            "script": "phase4/open_science_check.py",
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
    out_path = WS / "phase4" / "open_science_regex_baseline.json"
    json.dump(out, open(out_path, "w", encoding="utf-8"), indent=2)

    _write_report(out_path.parent / "open_science_regex_baseline.md", out)
    print(json.dumps(out["summary"], indent=2))


def _write_report(path: Path, out: dict) -> None:
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
    for label in ("public+link", "request-only", "statement-only", "explicitly-unavailable", "not-stated"):
        md.append(f"| {label} | {s['das'].get(label, 0)} | {s['cas'].get(label, 0)} |")
    md += [
        f"| Studies with a repo/data link anywhere | {s['repo_link_present']} | — |",
        f"| Studies with both public data AND code links | {s['both_public_link']} | — |",
        "",
        "Transparency context: only **published** repository links provide independently reproducible artifacts;",
        "`request-only` and `statement-only` claims cannot be re-verified from the record alone.",
        "",
    ]

    interesting = [r for r in out["results"] if r["das"] != "not-stated" or r["cas"] != "not-stated" or r["repo_links"]]
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
            for l in r["repo_links"]:
                md.append(f"- link `{l['url']}` … {l['snippet'][:160]}")
            md.append("")
    else:
        md += ["## Per-study detail", "", "No data/code availability statements or repository links detected in the corpus.", ""]

    md += [
        "## Methodological note",
        "",
        "- Scan is regex-based over extraction text (`±`{} char windows); classify labels are heuristic and intended for manual verification.",
        "- `public+link` = positive statement AND an identifiable repository/data DOI URL; `request-only` = available on request;",
        "  `statement-only` = asserted availability without a link or request channel.",
        "- Regenerate with `uv run python phase4/open_science_check.py`.",
        "",
    ]
    open(path, "w", encoding="utf-8").write("\n".join(md))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()