"""Trust-weighted consensus: annotate Consensus Cartographer clusters with Phase-4 trust context.

Pure, hermetic join (no network): merges a ``consensus.json`` report from the
Consensus Cartographer with the four Phase-4 verification outputs
(risk-of-bias, COI audit, retraction check, open-science baseline) per study,
then renders a trust-weighted consensus report.

Trust levels are deterministic and documented:

- ``BLOCKED``   any supporting study carries a retraction/concern/correction flag
                (a flagged corpus record must not be quoted without re-review).
- ``UNVERIFIED`` no supporting study appears in the Phase-4 trust index.
- ``WEAK``      coverage < 50% of supporting studies, any high-risk overall
                rating, or any industry-money link.
- ``STRONG``    coverage >= 50%, zero unclear overall ratings, zero industry
                ties, and at least one study with a public data/code link.
- ``ADEQUATE``  otherwise (covered, but with "?" ratings or mixed signals).

The worst applicable level wins per-cluster. All study-level details remain
in the JSON for downstream audit.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CONSENSUS_DEFAULT = "synthesis/consensus.json"
# (output stem -> phase4 file name)
PHASE4_INPUTS = {
    "risk_of_bias": "risk_of_bias.json",
    "coi": "coi_audit.json",
    "retraction": "retraction_status_check.json",
    "open_science": "open_science_regex_baseline.json",
}

TRUST_LEVELS = ("BLOCKED", "UNVERIFIED", "WEAK", "ADEQUATE", "STRONG")
_FLAG_REASON_SENSITIVE = ("retraction", "expression-of-concern", "erratum", "retracted")


def _parse_rq_codes(text: Any) -> list[str]:
    """Extract ``RQ<n>`` codes from a free-form report label (e.g. ``ALL (RQ1+RQ2)``)."""
    return sorted(set(re.findall(r"RQ\d+", text or "")))


def _rq_code_from_claims_stem(stem: str) -> str | None:
    m = re.match(r"claims_rq(\d+)$", stem)
    return f"RQ{m.group(1)}" if m else None


def load_rq_claims(claims_dir: Any) -> dict[str, dict[str, Any]]:
    """Load per-RQ claim pools from ``claims_rq*.json`` files into an attribution index."""
    d = Path(claims_dir)
    out: dict[str, dict[str, Any]] = {}
    if not d.is_dir():
        return out
    for p in sorted(d.glob("claims_rq*.json")):
        code = _rq_code_from_claims_stem(p.stem)
        if not code:
            continue
        rows = _rows(_load_json(p))
        out[code] = {
            "rows": rows,
            "keys": {(c.get("study_id"), c.get("claim_text")) for c in rows},
        }
    return out


def cluster_rq_ids(group: dict[str, Any], claims_by_rq: dict[str, dict[str, Any]]) -> list[str]:
    """RQ codes whose claim pool contains any of the cluster's claims (exact study/claim match)."""
    keys = {(c.get("study_id"), c.get("claim_text")) for c in group.get("claims", [])}
    if not keys:
        return []
    return sorted(rq for rq, info in claims_by_rq.items() if keys & info["keys"])


def _load_json(path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(data: Any) -> list[dict[str, Any]]:
    """Accept either a bare result list or the full file dict (with ``results``)."""
    if isinstance(data, dict):
        return data.get("results") or []
    return data or []


def build_trust_index(phase4: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Flatten the four Phase-4 result lists into a per-study trust index."""
    index: dict[str, dict[str, Any]] = {}
    for stream, rows in phase4.items():
        for row in rows:
            wid = row.get("workspace_id")
            if not wid:
                continue
            rec = index.setdefault(wid, {"workspace_id": wid})
            if stream == "risk_of_bias":
                rec["overall_risk"] = row.get("overall_risk")
                rec["risk_domains"] = row.get("domains")
            elif stream == "coi":
                rec["coi_label"] = row.get("coi_label")
                rec["adjusted_from"] = row.get("adjusted_from")
                rec["industry_entities"] = row.get("industry_entities") or []
            elif stream == "retraction":
                rec["flagged"] = bool(row.get("flagged"))
                rec["flag_reasons"] = row.get("flag_reasons") or []
                rec["openalex_retracted"] = (row.get("openalex") or {}).get("is_retracted")
            elif stream == "open_science":
                rec["das"] = row.get("das")
                rec["cas"] = row.get("cas")
                rec["repo_links"] = row.get("repo_links") or []
    return index


def _industry_money(rec: dict[str, Any]) -> bool:
    return any((e.get("kind") == "funding") for e in rec.get("industry_entities", []))


def _industry_any(rec: dict[str, Any]) -> bool:
    return bool(rec.get("industry_entities"))


def _open_science_public(rec: dict[str, Any]) -> bool:
    return any(rec.get(k) == "public+link" for k in ("das", "cas"))


def trust_level(studies: list[dict[str, Any]], coverage: float) -> str:
    """Deterministic cluster trust level (worst applicable wins)."""
    if not studies or coverage <= 0.0:
        return "UNVERIFIED"
    if any(s.get("flagged") for s in studies):
        return "BLOCKED"
    if coverage < 0.5 or any(s.get("overall_risk") == "H" for s in studies) or any(_industry_money(s) for s in studies):
        return "WEAK"
    if coverage >= 0.5 and all(s.get("overall_risk") not in (None, "?") for s in studies) and not any(
        _industry_any(s) for s in studies
    ) and any(_open_science_public(s) for s in studies):
        return "STRONG"
    return "ADEQUATE"


def _fraction_overall(studies: list[dict[str, Any]], rating: str) -> int:
    return sum(1 for s in studies if s.get("overall_risk") == rating)


def annotate_group(group: dict[str, Any], index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Attach trust context to a single consensus cluster."""
    study_ids = group.get("supporting_studies") or sorted(
        {c.get("study_id") for c in group.get("claims", []) if c.get("study_id")}
    )
    ctx_studies = [index.get(s, {"workspace_id": s}) for s in study_ids]
    present = [s for s in ctx_studies if s.get("overall_risk") is not None or s.get("coi_label") is not None]
    coverage = len(present) / len(study_ids) if study_ids else 0.0
    level = trust_level(present, coverage)
    flags = []
    if any(s.get("flagged") for s in present):
        flags.append("flagged-study")
    if _fraction_overall(present, "H") > 0:
        flags.append("high-risk-study")
    if any(_industry_money(s) for s in present):
        flags.append("industry-money")
    if coverage < 0.5:
        flags.append("low-coverage")
    if coverage <= 0.0:
        flags.append("unverified")

    out = dict(group)
    out["trust"] = {
        "trust_level": level,
        "flags": flags,
        "coverage": round(coverage, 3),
        "supporting_studies": study_ids,
        "studies_audited": len(present),
        "studies_total": len(study_ids),
        "aggregates": {
            "overall_risk": {
                "H": _fraction_overall(present, "H"),
                "L": _fraction_overall(present, "L"),
                "?": _fraction_overall(present, "?"),
            },
            "industry_money": sum(1 for s in present if _industry_money(s)),
            "industry_any_ties": sum(1 for s in present if _industry_any(s)),
            "no_coi_statement": sum(1 for s in present if s.get("coi_label") == "no-statement"),
            "flagged": sum(1 for s in present if s.get("flagged")),
            "open_science_public_link": sum(1 for s in present if _open_science_public(s)),
            "repo_links": sum(len(s.get("repo_links", [])) for s in present),
        },
        "studies": [
            {
                "workspace_id": s.get("workspace_id"),
                "overall_risk": s.get("overall_risk"),
                "coi_label": s.get("coi_label"),
                "adjusted_from": s.get("adjusted_from"),
                "industry_entities": [
                    {"entity": e.get("entity"), "kind": e.get("kind")} for e in s.get("industry_entities", [])
                ],
                "flagged": s.get("flagged", False),
                "flag_reasons": s.get("flag_reasons", []),
                "openalex_retracted": s.get("openalex_retracted"),
                "das": s.get("das"),
                "cas": s.get("cas"),
                "repo_links": s.get("repo_links", []),
            }
            for s in ctx_studies
        ],
    }
    return out


def annotate(
    consensus: dict[str, Any],
    phase4: dict[str, list[dict[str, Any]]],
    *,
    rq_id: str | None = None,
    claims_by_rq: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Annotate a full Consensus Cartographer report with cluster trust context.

    When ``claims_by_rq`` (see :func:`load_rq_claims`) is given, every annotated
    cluster carries ``rq_ids`` — the RQs whose claim pools contain the cluster's
    claims — and ``rq_id`` (the single RQ when unanimous, else ``None``).

    When ``rq_id`` is given, the report is scoped to clusters whose claims belong
    to that RQ. Clusters with no RQ attribution fall back to the report-level
    RQ codes parsed from ``consensus["rq_id"]``.
    """
    index = build_trust_index(phase4)
    buckets = ("high_consensus", "active_debates", "unresolved", "provisional")
    report_rq_ids = _parse_rq_codes(consensus.get("rq_id"))

    def annotate_bucket(name: str) -> list[dict[str, Any]]:
        out = []
        for g in consensus.get(name) or []:
            ag = annotate_group(g, index)
            ids = cluster_rq_ids(g, claims_by_rq) if claims_by_rq else []
            ag["rq_ids"] = ids
            ag["rq_id"] = ids[0] if len(ids) == 1 else None
            out.append(ag)
        return out

    annotated_buckets = {b: annotate_bucket(b) for b in buckets}

    if rq_id:
        def keep(g: dict[str, Any]) -> bool:
            if g["rq_ids"]:
                return rq_id in g["rq_ids"]
            return rq_id in report_rq_ids

        annotated_buckets = {b: [g for g in gs if keep(g)] for b, gs in annotated_buckets.items()}

    total = sum(len(gs) for gs in annotated_buckets.values())

    level_counter: dict[str, int] = {lev: 0 for lev in TRUST_LEVELS}
    for bucket in annotated_buckets.values():
        for g in bucket:
            level_counter[g["trust"]["trust_level"]] += 1

    return {
        "rq_id": rq_id or consensus.get("rq_id"),
        "report_rq_ids": report_rq_ids,
        "input_claims": consensus.get("input_claims"),
        "total_groups": total,
        "total_groups_all": consensus.get("total_groups"),
        "threshold": consensus.get("threshold"),
        "trust_level_counts": {k: v for k, v in level_counter.items() if v},
        "buckets": annotated_buckets,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _mono(s: str, width: int = 36) -> str:
    s = (s or "").replace("\n", " ")
    return (s[:width] + "…") if len(s) > width else s


def render_report(annotated: dict[str, Any]) -> str:
    md = [
        "# Trust-Weighted Consensus Report",
        "",
        f"**RQ**: {annotated.get('rq_id') or 'General'} | **Clusters**: {annotated.get('total_groups')} | "
        f"**Input claims**: {annotated.get('input_claims')}",
        "",
    ]
    if (
        annotated.get("total_groups_all") is not None
        and annotated["total_groups_all"] != annotated["total_groups"]
    ):
        md.append(f"_Scoped to `{annotated.get('rq_id')}`: {annotated['total_groups']} of {annotated['total_groups_all']} clusters._")
        md.append("")
    md.extend([
        "## Trust-level distribution",
        "",
        "| Level | Clusters |",
        "|---|---|",
    ])
    total = 0
    for lev in TRUST_LEVELS:
        n = annotated["trust_level_counts"].get(lev, 0)
        total += n
        md.append(f"| {lev} | {n} |")
    md.append(f"| **Total audited** | {total} |")
    md.append("")
    md.append(
        "_Levels_: `BLOCKED` (flagged retraction/concern/correction) → `UNVERIFIED` (no Phase-4 data) → "
        "`WEAK` (low coverage / high-risk / industry money) → `ADEQUATE` → `STRONG` (covered, definitive risk "
        "ratings, public data/code links, no industry ties)."
    )
    md.append("")

    bucket_titles = {
        "high_consensus": "High-Consensus Findings",
        "active_debates": "Active Debates",
        "unresolved": "Unresolved",
        "provisional": "Provisional",
    }
    for bucket, groups in annotated["buckets"].items():
        if not groups:
            continue
        md.append(f"## {bucket_titles[bucket]}")
        md.append("")
        for g in groups:
            t = g["trust"]
            md.append(f"### {g['cluster_id']} — {_mono(g.get('theme'), 80)}")
            md.append("")
            rqs = g.get("rq_ids") or []
            if len(rqs) > 1:
                md.append(f"- **RQs**: {', '.join(rqs)}")
            md.append(
                f"- **Level**: `{t['trust_level']}` {('(' + ', '.join(t['flags']) + ')') if t['flags'] else ''}"
            )
            md.append(f"- **Coverage**: {t['studies_audited']}/{t['studies_total']} supporting studies in Phase-4")
            agg = t["aggregates"]
            md.append(
                f"- **RoB**: H={agg['overall_risk']['H']} L={agg['overall_risk']['L']} ?={agg['overall_risk']['?']} | "
                f"**COI**: industry-money={agg['industry_money']}, any-ties={agg['industry_any_ties']}, "
                f"no-statement={agg['no_coi_statement']} | **Retraction flags**: {agg['flagged']} | "
                f"**Open-science**: public+link={agg['open_science_public_link']}, repo-links={agg['repo_links']}"
            )
            md.append("")
            if t["studies"]:
                md.append("| Study | RoB | COI | Industry | Retr. | DAS | CAS |")
                md.append("|---|---|---|---|---|---|---|")
                for s in t["studies"]:
                    kb = "m" if any(e.get("kind") == "funding" for e in s["industry_entities"]) else (
                        "a" if s["industry_entities"] else "—"
                    )
                    md.append(
                        f"| {s.get('workspace_id') or '—'} | {s.get('overall_risk') or '—'} | "
                        f"{s.get('coi_label') or '—'} | {kb} | "
                        f"{('F:' + ';'.join(s.get('flag_reasons', []))) if s.get('flagged') else '—'} | "
                        f"{s.get('das') or '—'} | {s.get('cas') or '—'} |"
                    )
                md.append("")
    md.append("---")
    md.append("_Generated by `scholar-verify trust-context` from consensus.json + the four Phase-4 verification streams._")
    return "\n".join(md)


def run(
    consensus: dict[str, Any],
    phase4_dir: Any,
    *,
    rq_id: str | None = None,
    claims_dir: Any = None,
) -> dict[str, Any]:
    """Load Phase-4 outputs from a directory and annotate the consensus report."""
    phase4 = {}
    d = Path(phase4_dir)
    for key, fname in PHASE4_INPUTS.items():
        p = d / fname
        if p.exists():
            phase4[key] = _rows(_load_json(p))
    claims_by_rq = load_rq_claims(claims_dir) if claims_dir else None
    return annotate(consensus, phase4, rq_id=rq_id, claims_by_rq=claims_by_rq)
