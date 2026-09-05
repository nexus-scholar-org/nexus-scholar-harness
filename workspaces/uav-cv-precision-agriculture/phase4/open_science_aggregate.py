"""Phase 4 workstream 2 aggregator.

Normalizes the per-chunk analyst (subagent) DAS/CAS classifications produced
from extraction fulltext, validates coverage against the 94-study manifest,
merges the deterministic regex baseline for cross-check, and writes:

  phase4/open_science_artifacts.json   canonical analyst classification
  phase4/open_science_artifacts.md     report

Raw analyst outputs live in phase4/_agent_results/chunk_<n>.json (read-only inputs).

Usage: uv run python workspaces/uav-cv-precision-agriculture/phase4/open_science_aggregate.py
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

WS = Path("workspaces/uav-cv-precision-agriculture")
PHASE4 = WS / "phase4"
LABELS = ("public+link", "request-only", "statement-only", "explicitly-unavailable", "not-stated")


def _to_list(x):
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    return list(x)


def _dig(node, key):
    for part in key.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def normalize(entry):
    wid = entry["workspace_id"]
    sources = [
        ("das", "cas"),
        ("das.label", "cas.label"),
        ("dataAvailability.label", "codeAvailability.label"),
        ("data_availability.label", "code_availability.label"),
    ]
    das = cas = None
    for key_d, key_c in sources:
        if das is None:
            das = _dig(entry, key_d)
        if cas is None:
            cas = _dig(entry, key_c)
        if isinstance(das, dict):
            das = das.get("label")
        if isinstance(cas, dict):
            cas = cas.get("label")
    if das is None or cas is None:
        raise ValueError(f"{wid}: could not locate das/cas labels in {list(entry.keys())}")

    def evidence(k1, k2):
        for k in (k1, k2):
            v = _dig(entry, k)
            if v:
                return _to_list(v)
        return []

    def links():
        out = []
        for k in ("links", "dataAvailability.links", "codeAvailability.links", "das.links", "cas.links", "data_availability.links", "code_availability.links"):
            v = _dig(entry, k)
            if v:
                for item in _to_list(v):
                    if isinstance(item, dict):
                        out.append(item)
                    else:
                        out.append({"url": str(item), "context": ""})
        dedup = []
        seen = set()
        for item in out:
            key = item.get("url") or ""
            if key and key not in seen:
                seen.add(key)
                dedup.append(item)
        return dedup

    return {
        "workspace_id": wid,
        "das": str(das).lower(),
        "cas": str(cas).lower(),
        "data_evidence": evidence("data_evidence", "dataAvailability.evidence") or evidence("das.evidence", "data_availability.evidence"),
        "code_evidence": evidence("code_evidence", "codeAvailability.evidence") or evidence("cas.evidence", "code_availability.evidence"),
        "links": links(),
        "notes": entry.get("notes") or "",
    }


def main():
    manifest = json.load(open(PHASE4 / "_manifest.json", encoding="utf-8"))
    expected = [m["workspace_id"] for m in manifest]
    chunks = []
    for i in range(1, 9):
        chunks.extend(
            json.load(open(PHASE4 / "_agent_results" / f"chunk_{i}.json", encoding="utf-8"))
        )
    normalized = {n["workspace_id"]: n for n in (normalize(c) for c in chunks)}

    got = list(normalized)
    missing = [w for w in expected if w not in got]
    extra = [w for w in got if w not in expected]
    dup_counts = Counter()
    for n in chunks:
        dup_counts[n["workspace_id"]] += 1
    dups = [w for w, c in dup_counts.items() if c > 1]
    if dups:
        raise ValueError(f"duplicate workspace_id in chunks: {dups}")

    bad_labels = []
    for w, n in normalized.items():
        for k in ("das", "cas"):
            if n[k] not in LABELS:
                bad_labels.append((w, k, n[k]))
    if missing or extra or bad_labels:
        raise SystemExit(f"validation failed\n missing={missing}\n extra={extra}\n bad_labels={bad_labels}")

    regex_data = json.load(open(PHASE4 / "open_science_regex_baseline.json", encoding="utf-8"))
    regex_by_id = {r["workspace_id"]: r for r in regex_data["results"]}

    rows = []
    for m in manifest:
        wid = m["workspace_id"]
        n = normalized[wid]
        rb = regex_by_id.get(wid, {})
        row = {
            "workspace_id": wid,
            "title": m["title"],
            "year": m["year"],
            "das": n["das"],
            "cas": n["cas"],
            "data_evidence": n["data_evidence"],
            "code_evidence": n["code_evidence"],
            "links": n["links"],
            "notes": n["notes"],
            "regex_baseline_das": rb.get("das"),
            "regex_baseline_cas": rb.get("cas"),
        }
        rows.append(row)

    das_counts = Counter(r["das"] for r in rows)
    cas_counts = Counter(r["cas"] for r in rows)
    both_link = sum(1 for r in rows if r["das"] == "public+link" and r["cas"] == "public+link")
    any_stat = sum(1 for r in rows if r["das"] != "not-stated" or r["cas"] != "not-stated")
    any_link = sum(1 for r in rows if r["links"])
    das_disagree = sum(1 for r in rows if r["regex_baseline_das"] != r["das"])
    cas_disagree = sum(1 for r in rows if r["regex_baseline_cas"] != r["cas"])

    out = {
        "run_metadata": {
            "script": "phase4/open_science_aggregate.py",
            "run_date_utc": datetime.now().astimezone().isoformat(),
            "method": "LLM analyst read of extraction fulltext (8 parallel subagents) + regex baseline cross-check",
            "inputs": ["_agent_results/chunk_1..8.json", "open_science_artifacts.json (regex baseline)", "literature/extraction/merged/records.json"],
            "corpus_size": len(rows),
        },
        "summary": {
            "studies_scanned": len(rows),
            "das": dict(das_counts),
            "cas": dict(cas_counts),
            "both_public_link": both_link,
            "any_das_or_cas_statement": any_stat,
            "repo_link_present": any_link,
            "regex_baseline_agreement_das": len(rows) - das_disagree,
            "regex_baseline_agreement_cas": len(rows) - cas_disagree,
            "regex_baseline_disagreements_das": das_disagree,
            "regex_baseline_disagreements_cas": cas_disagree,
        },
        "results": rows,
    }
    json.dump(out, open(PHASE4 / "open_science_artifacts.json", "w", encoding="utf-8"), indent=2)
    _write_report(PHASE4 / "open_science_artifacts.md", out)
    print(json.dumps(out["summary"], indent=2))


def _write_report(path: Path, out: dict) -> None:
    s = out["summary"]
    md = [
        "# Open-Science Artifact Scan (Data / Code Availability)",
        "",
        f"**Corpus**: {s['studies_scanned']} studies (post-audit); **run**: {out['run_metadata']['run_date_utc']}",
        f"**Method**: analyst read of extraction fulltext (8 parallel subagents), validated labels, cross-checked against a deterministic regex baseline.",
        "",
        "## Summary",
        "",
        "| Category | Data (DAS) | Code (CAS) |",
        "|---|---|---|",
    ]
    for label in ("public+link", "request-only", "statement-only", "explicitly-unavailable", "not-stated"):
        md.append(f"| {label} | {s['das'].get(label, 0)} | {s['cas'].get(label, 0)} |")
    md += [
        f"| Studies with at least one repo/data link anywhere | {s['repo_link_present']} | — |",
        f"| Studies with BOTH public data and public code links | {s['both_public_link']} | — |",
        f"| Regex-baseline agreement (DAS / CAS) | {s['regex_baseline_agreement_das']} / {s['regex_baseline_agreement_cas']} | — |",
        "",
        "Interpretation: `public+link` claims are independently verifiable; `request-only` and `statement-only` cannot be checked from the record alone.",
        "",
    ]

    interesting = [r for r in out["results"] if r["das"] != "not-stated" or r["cas"] != "not-stated" or r["links"]]
    md += ["## Per-study classification (any signal)", "", "| ID | Year | DAS | CAS | Links | Regex DAS/CAS |", "|---|---|---|---|---|---|"]
    for r in interesting:
        links = "; ".join(x["url"] for x in r["links"][:3]) or "—"
        rb = f"{r['regex_baseline_das']}/{r['regex_baseline_cas']}"
        md.append(f"| {r['workspace_id']} | {r['year']} | {r['das']} | {r['cas']} | {links} | {rb} |")
    md.append("")

    md += ["## Studies without any statement", "", ", ".join(r["workspace_id"] for r in out["results"] if r not in interesting) or "none", ""]

    disagreements = [r for r in out["results"] if r["regex_baseline_das"] != r["das"] or r["regex_baseline_cas"] != r["cas"]]
    if disagreements:
        md += ["## Analyst vs regex-baseline disagreements", "", "Diffs reflect false positives in the regex pass (third-party github/tool mentions) or statements the regex missed (reference-list \"Available:\" URLs).", "", "| ID | DAS analyst/baseline | CAS analyst/baseline |", "|---|---|---|"]
        for r in disagreements:
            md.append(f"| {r['workspace_id']} | {r['das']}/{r['regex_baseline_das']} | {r['cas']}/{r['regex_baseline_cas']} |")
        md.append("")

    md += ["## Methodological note", "", "- Labels follow TOP-level semantics: `public+link` requires an explicit availability statement plus an identifiable URL/DOI.", "- Third-party tooling references (e.g. cited libraries or benchmarks) are not counted as the authors' code availability.", "- Raw analyst evidence (verbatim snippets) is recorded per study in `open_science_artifacts.json`.", "- Regenerate the aggregate with `uv run python phase4/open_science_aggregate.py`; raw chunk inputs are frozen in `_agent_results/`.", ""]
    open(path, "w", encoding="utf-8").write("\n".join(md))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()