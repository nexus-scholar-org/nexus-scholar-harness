"""Conflict-of-interest audit aggregator.

Normalizes per-chunk analyst COI classifications (any of the accepted chunk
schemas), validates coverage against the study manifest, applies a documented
deterministic relabel for analyst `no-statement` drift, and produces the
canonical coi_audit output (JSON + Markdown).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

LABELS = (
    "no-statement",
    "academic-or-public",
    "industry-money",
    "industry-affiliation-or-equipment",
    "declared-no-conflict",
)
ENTITY_KINDS = ("funding", "affiliation", "donated-equipment", "tooling", "unspecified")

_RELABEL_DOC = (
    "no-statement with a COI statement -> declared-no-conflict; "
    "no-statement with only funding -> academic-or-public; "
    "non-tooling entities upgrade to the matching industry label; "
    "adjustments recorded on each row."
)


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


def norm_entities(raw) -> list[dict[str, str]]:
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


def normalize(entry: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single analyst COI entry (any chunk schema variant)."""
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


def load_chunks(chunks_dir: Path, prefix: str = "coi_chunk_", n_chunks: int = 8) -> list[dict[str, Any]]:
    """Read all per-chunk analyst outputs into a flat list."""
    chunks = []
    for i in range(1, n_chunks + 1):
        path = chunks_dir / f"{prefix}{i}.json"
        if not path.exists():
            raise SystemExit(f"missing analyst chunk: {path}")
        chunks.extend(json.loads(path.read_text(encoding="utf-8")))
    return chunks


def run(manifest: list[dict[str, Any]], chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate analyst COI chunks against the study manifest.

    manifest: list of {workspace_id, title, year} rows (phase4/_manifest.json shape).
    chunks:   flat list of raw analyst entries (any schema variant).
    """
    expected = [m["workspace_id"] for m in manifest]
    normalized = {n["workspace_id"]: n for n in (normalize(c) for c in chunks)}

    got = list(normalized)
    missing = [w for w in expected if w not in got]
    extra = [w for w in got if w not in expected]
    dup_counts = Counter(c.get("workspace_id") or c.get("study_id") for c in chunks)
    dups = [w for w, c in dup_counts.items() if c > 1]
    if missing or extra or dups:
        raise SystemExit(
            f"validation failed\n missing={missing}\n extra={extra}\n dups={dups}\n"
            f" (count expected={len(expected)} got={len(got)})"
        )

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

    all_entities: Counter[tuple[str, str]] = Counter()
    for r in rows:
        for e in r["industry_entities"]:
            if e["kind"] not in ("tooling", "unspecified"):
                all_entities[(e["entity"], e["kind"])] += 1

    return {
        "run_metadata": {
            "tool": "scholar-verify-kit/coi",
            "run_date_utc": datetime.now().astimezone().isoformat(),
            "method": "LLM analyst read of extraction fulltext (parallel subagents: funding/acknowledgments/COI verbatim + industry entities + severity-ordered label)",  # noqa: E501
            "corpus_size": len(rows),
            "labels": list(LABELS),
            "relabel_rule": _RELABEL_DOC,
        },
        "summary": {
            "studies_scanned": len(rows),
            "labels": dict(label_counts),
            "industry_money_count": len(industry_money),
            "industry_affiliation_or_equipment_count": len(industry_aff_or_eq),
            "any_industry_tie_count": len(any_industry),
            "adjusted_relabels": len(adjusted),
            "top_industry_entities": [
                {"entity": e, "kind": k, "count": c} for (e, k), c in all_entities.most_common(12)
            ],
        },
        "industry_money_studies": [r["workspace_id"] for r in industry_money],
        "industry_affiliation_or_equipment_studies": [r["workspace_id"] for r in industry_aff_or_eq],
        "adjusted_studies": [(r["workspace_id"], r["coi_label"]) for r in adjusted],
        "results": rows,
    }


def render_report(out: dict[str, Any]) -> str:
    s = out["summary"]
    md = [
        "# Conflict-of-Interest Audit",
        "",
        f"**Corpus**: {s['studies_scanned']} studies (post-audit); **run**: {out['run_metadata']['run_date_utc']}",
        "**Method**: independent analyst read of extraction fulltext (parallel subagents); funding/acknowledgments/COI statements captured verbatim; industry entities tagged (`funding` / `affiliation` / `donated-equipment` / `tooling`); single severity-ordered label per study.",
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
        md += [
            "## Adjusted labels",
            "",
            "Subagents occasionally used `no-statement` to mean \"no COI section\" even when a funding/COI statement exists; a deterministic relabel was applied (recorded per study in the JSON output).",
            "",
            "| ID | Final label |",
            "|---|---|",
        ]
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
    declared = [
        r
        for r in out["results"]
        if r["coi_label"] == "declared-no-conflict"
        and any(e["kind"] not in ("tooling", "unspecified") for e in r["industry_entities"])
    ]
    if declared:
        md += [
            "## Caution: declared-no-conflict with non-tooling entity tags",
            "",
            "Analysts declared no financial conflict while still tagging a non-tooling entity (e.g. field access, donated data). Review verbatim quotes in the JSON output.",
            "",
            ", ".join(r["workspace_id"] for r in declared),
            "",
        ]

    md += [
        "## Methodological note",
        "",
        "- Government/academic/university grants are NOT industry entities; they map to `academic-or-public` or `declared-no-conflict` when an explicit declaration exists.",
        "- `industry-money` = any funding/salary/equity from a private-sector company (incl. corporate foundations); `industry-affiliation-or-equipment` = author employed by industry or equipment/data donated by industry without cash.",
        "- Seed/variety donations from agrochemical companies (e.g. BASF, Bayer) are tagged `donated-equipment`.",
        "- Verbatim statements and evidence are recorded per study in the JSON output for independent verification.",
        f"- Regenerate with `scholar-verify coi --workspace <dir>`; relabel rule: {s['labels'] and out['run_metadata']['relabel_rule']}",
        "",
    ]
    return "\n".join(md)


def save_results(workspace: Path, name: str, out: dict[str, Any], report_md: str) -> None:
    out_dir = workspace / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{name}.md").write_text(report_md, encoding="utf-8")
