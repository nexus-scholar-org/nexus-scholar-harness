"""Phase 4 workstream 3 aggregator (conflict-of-interest audit).

Normalizes the per-chunk analyst (subagent) COI classifications produced from
extraction fulltext, validates coverage against the 94-study manifest, applies a
documented deterministic relabel for analyst `no-statement` drift, and writes:

  phase4/coi_audit.json   canonical analyst classification + entities
  phase4/coi_audit.md     report

Coi chunk schema variants accepted:
  * flat  : workspace_id / coi_label / funding_statement / acknowledgments /
            coi_statement / industry_entities[{entity,kind,quote}] / notes
  * v2    : study_id / coi_label / funding_verbatim / acknowledgments_verbatim /
            coi_verbatim / industry_entities[{name,kind:"company",
            affiliation_role}] / rationale (chunk 2)

Relabel rule (applied ONLY to analyst `no-statement`, recorded in `adjusted`):
  if coi_statement present and no non-tooling entity  -> declared-no-conflict
  elif funding_statement present and no non-tooling entity -> academic-or-public
  elif non-tooling entity with kind in (funding,) -> industry-money
  elif non-tooling entity -> industry-affiliation-or-equipment

Usage: uv run python workspaces/uav-cv-precision-agriculture/phase4/coi_aggregate.py
"""
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

WS = Path("workspaces/uav-cv-precision-agriculture")
PHASE4 = WS / "phase4"
LABELS = (
    "no-statement",
    "academic-or-public",
    "industry-money",
    "industry-affiliation-or-equipment",
    "declared-no-conflict",
)
ENTITY_KINDS = ("funding", "affiliation", "donated-equipment", "tooling", "unspecified")


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


def _strip(v):
    return (v or "").strip()


def norm_entities(raw):
    out = []
    for e in _to_list(raw):
        if isinstance(e, str):
            out.append({"entity": e, "kind": "unspecified", "quote": ""})
            continue
        if not isinstance(e, dict):
            continue
        kind = (e.get("kind") or "").lower()
        if kind == "company":
            role = (e.get("affiliation_role") or "").lower()
            if "equipment" in role or "support" in role or "field_access" in role:
                kind = "donated-equipment"
            elif "funding" in role or "money" in role:
                kind = "funding"
            else:
                kind = "affiliation"
        if kind not in ENTITY_KINDS:
            kind = "unspecified"
        quote = e.get("quote") or ""
        out.append({"entity": e.get("name") or e.get("entity") or "", "kind": kind, "quote": _strip(quote)})
    return out


def normalize(entry):
    wid = entry.get("workspace_id") or entry.get("study_id") or entry.get("id")
    if not wid:
        raise ValueError(f"no id in {list(entry.keys())}")
    label = _strip(entry.get("coi_label"))
    if label not in LABELS:
        raise ValueError(f"{wid}: unknown coi_label {label!r}")

    funding = _strip(entry.get("funding_statement")) or _strip(entry.get("funding_verbatim"))
    ack = _strip(entry.get("acknowledgments")) or _strip(entry.get("acknowledgments_verbatim"))
    coi = _strip(entry.get("coi_statement")) or _strip(entry.get("coi_verbatim"))
    entities = norm_entities(entry.get("industry_entities"))
    notes = _strip(entry.get("notes")) or _strip(entry.get("rationale"))

    adjusted_to = None
    if label == "no-statement":
        non_tooling = [e for e in entities if e["kind"] not in ("tooling", "unspecified")]
        if coi and not non_tooling:
            label = "declared-no-conflict"
            adjusted_to = label
        elif funding and not non_tooling:
            label = "academic-or-public"
            adjusted_to = label
        elif any(e["kind"] == "funding" for e in non_tooling):
            label = "industry-money"
            adjusted_to = label
        elif non_tooling:
            label = "industry-affiliation-or-equipment"
            adjusted_to = label

    return {
        "workspace_id": wid,
        "coi_label": label,
        "adjusted_from": "no-statement" if adjusted_to else None,
        "funding_statement": funding,
        "acknowledgments": ack,
        "coi_statement": coi,
        "industry_entities": entities,
        "notes": notes,
    }


def main():
    manifest = json.load(open(PHASE4 / "_manifest.json", encoding="utf-8"))
    expected = [m["workspace_id"] for m in manifest]
    chunks = []
    for i in range(1, 9):
        chunks.extend(json.load(open(PHASE4 / "_agent_results" / f"coi_chunk_{i}.json", encoding="utf-8")))
    normalized = {n["workspace_id"]: n for n in (normalize(c) for c in chunks)}

    got = list(normalized)
    missing = [w for w in expected if w not in got]
    extra = [w for w in got if w not in expected]
    dup_counts = Counter(c.get("workspace_id") or c.get("study_id") for c in chunks)
    dups = [w for w, c in dup_counts.items() if c > 1]
    if missing or extra or dups:
        raise SystemExit(f"validation failed\n missing={missing}\n extra={extra}\n dups={dups}\n (count expected={len(expected)} got={len(got)})")

    rows = []
    for m in manifest:
        wid = m["workspace_id"]
        n = normalized[wid]
        rows.append(
            {
                "workspace_id": wid,
                "title": m["title"],
                "year": m["year"],
                "coi_label": n["coi_label"],
                "adjusted_from": n["adjusted_from"],
                "funding_statement": n["funding_statement"],
                "acknowledgments": n["acknowledgments"],
                "coi_statement": n["coi_statement"],
                "industry_entities": n["industry_entities"],
                "notes": n["notes"],
            }
        )

    label_counts = Counter(r["coi_label"] for r in rows)
    adjusted = [r for r in rows if r["adjusted_from"]]
    industry_money = [r for r in rows if r["coi_label"] == "industry-money"]
    industry_aff_or_eq = [r for r in rows if r["coi_label"] == "industry-affiliation-or-equipment"]
    any_industry = industry_money + industry_aff_or_eq

    all_entities = Counter()
    for r in rows:
        for e in r["industry_entities"]:
            if e["kind"] not in ("tooling", "unspecified"):
                all_entities[(e["entity"], e["kind"])] += 1

    out = {
        "run_metadata": {
            "script": "phase4/coi_aggregate.py",
            "run_date_utc": datetime.now().astimezone().isoformat(),
            "method": "LLM analyst read of extraction fulltext (8 parallel subagents: funding/acknowledgments/COI verbatim + industry entities + severity-ordered label)",
            "inputs": ["_agent_results/coi_chunk_1..8.json", "phase4/_manifest.json"],
            "corpus_size": len(rows),
            "labels": list(LABELS),
            "relabel_rule": "no-statement with a COI statement -> declared-no-conflict; no-statement with only funding -> academic-or-public; non-tooling entities upgrade to the matching industry label; adjustments recorded on each row.",
        },
        "summary": {
            "studies_scanned": len(rows),
            "labels": dict(label_counts),
            "industry_money_count": len(industry_money),
            "industry_affiliation_or_equipment_count": len(industry_aff_or_eq),
            "any_industry_tie_count": len(any_industry),
            "adjusted_relabels": len(adjusted),
            "top_industry_entities": [{"entity": e, "kind": k, "count": c} for (e, k), c in all_entities.most_common(12)],
        },
        "industry_money_studies": [r["workspace_id"] for r in industry_money],
        "industry_affiliation_or_equipment_studies": [r["workspace_id"] for r in industry_aff_or_eq],
        "adjusted_studies": [(r["workspace_id"], r["coi_label"]) for r in adjusted],
        "results": rows,
    }
    json.dump(out, open(PHASE4 / "coi_audit.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    _write_report(PHASE4 / "coi_audit.md", out)
    print(json.dumps(out["summary"], indent=2, ensure_ascii=False))


def _write_report(path: Path, out: dict) -> None:
    s = out["summary"]
    md = [
        "# Conflict-of-Interest Audit",
        "",
        f"**Corpus**: {s['studies_scanned']} studies (post-audit); **run**: {out['run_metadata']['run_date_utc']}",
        f"**Method**: independent analyst read of extraction fulltext (8 parallel subagents); funding/acknowledgments/COI statements captured verbatim; industry entities tagged (`funding` / `affiliation` / `donated-equipment` / `tooling`); single severity-ordered label per study.",
        "",
        "## Summary",
        "",
        "| Label | Count |",
        "|---|---|",
    ]
    for label in LABELS:
        md.append(f"| {label} | {s['labels'].get(label, 0)} |")
    md += [
        f"| **Studies with any industry tie (money OR affiliation/equipment)** | **{s['any_industry_tie_count']}** |",
        f"| — of which industry money | {s['industry_money_count']} |",
        f"| — of which industry affiliation / donated equipment | {s['industry_affiliation_or_equipment_count']} |",
        f"| Analyst-label adjustments (no-statement -> relabel) | {s['adjusted_relabels']} |",
        "",
        "Labels are severity-ordered: `industry-money` > `industry-affiliation-or-equipment` > `declared-no-conflict` > `academic-or-public` > `no-statement`. Vendor products merely used in methods are `tooling` and do NOT raise the label.",
        "",
    ]

    if s["adjusted_relabels"]:
        md += ["## Adjusted labels", "", "Subagents occasionally used `no-statement` to mean \"no COI section\" even when a funding/COI statement exists; a deterministic relabel was applied (recorded per study in `coi_audit.json`).", "", "| ID | Final label |", "|---|---|"]
        for wid, label in out["adjusted_studies"]:
            md.append(f"| {wid} | {label} |")
        md.append("")

    ims = out["industry_money_studies"]
    if ims:
        md += ["## Industry-money studies", "", ", ".join(ims), ""]
    iae = out["industry_affiliation_or_equipment_studies"]
    if iae:
        md += ["## Industry affiliation / donated-equipment studies", "", ", ".join(iae), ""]

    md += ["## Top tagged industry entities (non-tooling)", "", "| Entity | Kind | Studies |", "|---|---|---|"]
    for t in s["top_industry_entities"]:
        md.append(f"| {t['entity']} | {t['kind']} | {t['count']} |")
    md.append("")

    interesting = [r for r in out["results"] if r["industry_entities"]]
    md += ["## Per-study detail (studies with tagged entities)", "", "| ID | Year | Label | Entities |", "|---|---|---|---|"]
    for r in interesting:
        ents = "; ".join(f"{e['entity']} ({e['kind']})" for e in r["industry_entities"]) or "—"
        md.append(f"| {r['workspace_id']} | {r['year']} | {r['coi_label']} | {ents} |")
    md.append("")

    no_statement = [r for r in out["results"] if r["coi_label"] == "no-statement"]
    if no_statement:
        md += ["## Studies with no statement available", "", ", ".join(r["workspace_id"] for r in no_statement), ""]
    declared = [r for r in out["results"] if r["coi_label"] == "declared-no-conflict" and any(e["kind"] not in ("tooling", "unspecified") for e in r["industry_entities"])]
    if declared:
        md += ["## Caution: declared-no-conflict with non-tooling entity tags", "", "Analysts declared no financial conflict while still tagging a non-tooling entity (e.g. field access, donated data). Review verbatim quotes in `coi_audit.json`.", "", ", ".join(r["workspace_id"] for r in declared), ""]

    md += [
        "## Methodological note",
        "",
        "- Government/academic/university grants are NOT industry entities; they map to `academic-or-public` or `declared-no-conflict` when an explicit declaration exists.",
        "- `industry-money` = any funding/salary/equity from a private-sector company (incl. corporate foundations); `industry-affiliation-or-equipment` = author employed by industry or equipment/data donated by industry without cash.",
        "- Seed/variety donations from agrochemical companies (e.g. BASF, Bayer) are tagged `donated-equipment`.",
        "- Verbatim statements and evidence are recorded per study in `coi_audit.json` for independent verification.",
        "- Regenerate with `uv run python phase4/coi_aggregate.py`; raw analyst inputs are frozen in `_agent_results/coi_chunk_1..8.json`.",
        "",
    ]
    open(path, "w", encoding="utf-8").write("\n".join(md))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()