"""Deterministic metadata-driven risk-of-bias assessment.

Adapts the QUADAS-2 / PROBAST risk-of-bias domains to the metadata
systematically extracted for the corpus (records.json), scoring four domains
per study with deterministic, transparent rules (D1 dataset selection, D2
metric measurement/reporting, D3 ground-truth labeling, D4 runtime/efficiency
claim completeness). Ratings: L / ? / H; D4 is n/a for studies with no
reported edge/runtime component. OVERALL = worst applicable domain.

This captures *reporting and verifiability* risk — it does not substitute for
a human full-text appraisal.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

BENCH_RE = re.compile(
    r"weedsgalore|weedmap|phenobench|cofly|weeddb|agriculture-vision|cwfid|"
    r"deblurweedseg|uav-hsi-crop|weedyrice|rfsd|bawseg|agriadapt|leavesuav|"
    r"landcover|benchmark|public datasets|open access|sugarbeets|already published",
    re.I,
)
SPLIT_RE = re.compile(r"train.*test|train.?.val.?.test|cross-?valid|held-?out|split|fold", re.I)
ANNOT_RE = re.compile(r"annotat|label|pixel-?wise|ground.?.truth", re.I)

ORDER = {"H": 3, "?": 2, "L": 1}

PRIMARY_METRICS = ("mIoU", "weed_F1", "crop_F1", "F1", "Dice", "mPA", "PA")

DOMAIN_NAMES = {
    "d1": "Dataset selection & representativeness",
    "d2": "Metric measurement & reporting integrity",
    "d3": "Ground-truth labeling quality",
    "d4": "Runtime/efficiency claim completeness",
}


def _d(r: dict[str, Any], key: str) -> dict[str, Any]:
    return (r.get("segmentation") or {}).get(key) or {}


def _metric(r: dict[str, Any], name: str) -> dict[str, Any]:
    return (_d(r, "metrics") or {}).get(name) or {}


def primary_metric(r: dict[str, Any]):
    for name in PRIMARY_METRICS:
        m = _metric(r, name)
        if m.get("reported"):
            return True, m, name
    return False, None, None


def rate_d1(r: dict[str, Any]):
    ds = _d(r, "dataset")
    uav = bool(ds.get("uav_collected"))
    named = bool((ds.get("name") or "").strip())
    images = ds.get("images")
    if not uav:
        return "H", "claims not from UAV imagery -> outside RQ scope"
    note = (ds.get("note") or "") + " " + (ds.get("name") or "")
    split = bool(SPLIT_RE.search(note))
    if named and images is not None and images >= 20:
        rating = "L"
    elif named and (split or (images is not None and images < 20)):
        rating = "L" if split or images >= 10 else "?"
    else:
        rating = "?"
    reason = f"uav={uav}, images={images or 'n/s'}, split={'y' if split else 'n'}"
    return rating, reason


def rate_d2(r: dict[str, Any]):
    reported, m, name = primary_metric(r)
    if not reported:
        return "H", f"no primary accuracy metric ({name or 'none'})"
    conf = m.get("confidence")
    agmt = m.get("agreement")
    amb = bool(m.get("ambiguity"))
    if agmt == "both_equal" and conf is not None and conf >= 0.8:
        rating = "L"
    elif agmt in ("both_equal", None) and conf is None:
        rating = "?"
    elif agmt == "adjudicated" and conf is not None and conf >= 0.8:
        rating = "L"
    elif agmt in ("a_only", "b_only", "adjudicated"):
        rating = "?"
    else:
        rating = "?"
    if amb:
        rating = "?" if rating in ("L",) else rating
    reason = f"{name} conf={conf}, agreement={agmt or 'n/s'}, ambiguity={'y' if amb else 'n'}"
    return rating, reason


def rate_d3(r: dict[str, Any]):
    ds = _d(r, "dataset")
    note = (ds.get("note") or "") + " " + (ds.get("name") or "")
    is_bench = bool(BENCH_RE.search(note))
    annot = bool(ANNOT_RE.search(note))
    uav = bool(ds.get("uav_collected"))
    if is_bench or annot:
        return "L", f"benchmark={'y' if is_bench else 'n'}, annotation={'y' if annot else 'n'}"
    if not uav:
        return "H", "non-UAV source, no documented GT"
    if not (is_bench or annot):
        return "?", "self-collected; no documented GT / benchmark"
    return "L", "benchmark/public GT"


def rate_d4(r: dict[str, Any]):
    e = r.get("edge") or {}
    if not e.get("reported") and not e.get("runtime_reported") and not e.get("efficiency_reported"):
        return "n/a", "no edge/runtime claims"
    device = bool(str(e.get("device") or "").strip())
    runtime = bool(e.get("runtime_reported"))
    eff = bool(e.get("efficiency_reported"))
    fps = bool((e.get("fps") or {}).get("reported"))
    lat = bool((e.get("latency_ms") or {}).get("reported"))
    powr = bool((e.get("power_w") or {}).get("reported"))
    if device and runtime and eff and (fps or lat):
        return "L", f"device={'y' if device else 'n'}, runtime={'y' if runtime else 'n'}, fps={fps}, lat={lat}"
    if (device or runtime or eff) and not (device and runtime and eff):
        return "?", f"device={'y' if device else 'n'}, runtime={'y' if runtime else 'n'}, eff={'y' if eff else 'n'}, fps={fps}, lat={lat}, pwr={powr}"
    return "H", f"device={'y' if device else 'n'}, runtime={'y' if runtime else 'n'}, eff={'y' if eff else 'n'}, fps={fps}, lat={lat}"


RATERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "d1": rate_d1,
    "d2": rate_d2,
    "d3": rate_d3,
    "d4": rate_d4,
}


def run(records: list[dict[str, Any]], manifest: list[dict[str, Any]]) -> dict[str, Any]:
    """Score risk-of-bias for the manifest studies against canonical extraction records."""
    rec_by_id = {r["workspace_id"]: r for r in records}
    m_by_id = {m["workspace_id"]: m for m in manifest}

    missing = [w for w in m_by_id if w not in rec_by_id]
    if missing:
        raise SystemExit(f"records missing for: {missing}")

    rows = []
    for m in manifest:
        wid = m["workspace_id"]
        r = rec_by_id[wid]
        domains = {}
        for k, fn in RATERS.items():
            res = fn(r)
            rating = res[0] if isinstance(res, tuple) else res
            reason = res[1] if isinstance(res, tuple) else ""
            domains[k] = {"rating": rating, "reason": reason}
        applicable = [v["rating"] for v in domains.values() if v["rating"] != "n/a"]
        overall = max(applicable, key=lambda x: ORDER.get(x, 0)) if applicable else "n/a"
        rows.append(
            {
                "workspace_id": wid,
                "title": m["title"],
                "year": m["year"],
                "overall_risk": overall,
                "domains": domains,
            }
        )

    overall_counts = Counter(r["overall_risk"] for r in rows)
    d_counts = {k: Counter(r["domains"][k]["rating"] for r in rows) for k in RATERS}

    return {
        "run_metadata": {
            "tool": "scholar-verify-kit/risk-of-bias",
            "run_date_utc": datetime.now().astimezone().isoformat(),
            "method": "Deterministic metadata-driven adaptation of QUADAS-2/PROBAST risk-of-bias domains over the canonical records.json (reporting/verifiability risk, not a human full-text appraisal)",  # noqa: E501
            "inputs": ["literature/extraction/merged/records.json", "phase4/_manifest.json"],
            "corpus_size": len(rows),
            "ratings": "L (low) / ? (unclear) / H (high); n/a = domain not applicable",
        },
        "summary": {
            "studies_assessed": len(rows),
            "overall_risk": dict(overall_counts),
            "by_domain": {k: dict(c) for k, c in d_counts.items()},
            "studies_high_risk": [r["workspace_id"] for r in rows if r["overall_risk"] == "H"],
            "studies_unclear": [r["workspace_id"] for r in rows if r["overall_risk"] == "?"],
            "studies_edge_rq2": sum(1 for r in rows if r["domains"]["d4"]["rating"] != "n/a"),
        },
        "results": rows,
    }


def render_report(out: dict[str, Any]) -> str:
    s = out["summary"]
    md = [
        "# Risk-of-Bias Assessment",
        "",
        f"**Corpus**: {s['studies_assessed']} studies (post-audit); **run**: {out['run_metadata']['run_date_utc']}",
        "**Method**: deterministic, metadata-driven adaptation of the QUADAS-2 / PROBAST risk-of-bias domains over the canonical extraction records (`records.json`). Ratings: **L** low, **?** unclear, **H** high, **n/a** not applicable.",
        "",
        "## Domain definitions",
        "",
        "| Domain | Adapted from | Signal |",
        "|---|---|---|",
        "| D1 Dataset selection & representativeness | QUADAS-2 patient selection | UAV-collected; named dataset; sample size; explicit train/test or cross-validation split |",
        "| D2 Metric measurement & reporting integrity | QUADAS-2 index test / PROBAST outcome | Primary accuracy metric present; extraction confidence; independent-route agreement; ambiguity flagged |",
        "| D3 Ground-truth labeling quality | QUADAS-2 reference standard | Documented labels; public benchmark / known dataset vs unverifiable self-collected |",
        "| D4 Runtime/efficiency claim completeness | QUADAS-2 flow & timing | Device named; runtime + efficiency measured; fps/latency/power reported |",
        "",
        "Scoping note: this captures **reporting and verifiability** risk of the numbers entering the synthesis (can the claim be checked from the record alone?). It does not substitute for a human full-text appraisal.",
        "",
        "## Summary",
        "",
        "| Overall risk | Count |",
        "|---|---|",
    ]
    for rating in ("L", "?", "H", "n/a"):
        md.append(f"| {rating} | {s['overall_risk'].get(rating, 0)} |")
    md += ["", "Per-domain counts:", ""]
    md.append("| Domain | L | ? | H | n/a |")
    md.append("|---|---|---|---|---|")
    for k, c in s["by_domain"].items():
        md.append(f"| {k} | {c.get('L', 0)} | {c.get('?', 0)} | {c.get('H', 0)} | {c.get('n/a', 0)} |")
    md.append("")

    hexp = s["studies_high_risk"]
    if hexp:
        md += ["## Studies rated high risk (overall)", "", ", ".join(hexp), ""]
    uexp = s["studies_unclear"]
    if uexp:
        md += ["## Studies rated unclear (overall)", "", ", ".join(uexp), ""]

    md += [f"## Studies with an edge/runtime component (D4 applicable): **{s['studies_edge_rq2']}**", ""]
    md += ["## Per-study ratings", "", "| ID | Year | Overall | D1 | D2 | D3 | D4 | D4 detail (device/runtime/fps/latency) |", "|---|---|---|---|---|---|---|---|"]
    for r in out["results"]:
        d = r["domains"]
        d4 = d["d4"]
        detail = d4["reason"] if d4["rating"] != "n/a" else ""
        md.append(
            f"| {r['workspace_id']} | {r['year']} | {r['overall_risk']} | "
            f"{d['d1']['rating']} | {d['d2']['rating']} | {d['d3']['rating']} | {d4['rating']} | {detail} |"
        )
    md.append("")

    md += [
        "## Methodological note",
        "",
        "- A study is rated **H** on D2 when no primary accuracy metric is reported (extraction found none); it may still contribute RQ2-only data.",
        "- D3 is conservative: self-collected datasets without annotation/benchmark documentation are automatically `?` — presence of a sentence is not proof of quality.",
        "- D4 rates reporting completeness of runtime/efficiency numbers, which matters directly for the RQ2 (embedded edge inference) synthesis.",
        "- Per-domain reasons and verbatim flags are stored in the JSON output for manual override of any rating.",
        "- Regenerate with `scholar-verify risk-of-bias --workspace <dir>`.",
        "",
    ]
    return "\n".join(md)


def save_results(workspace: Path, name: str, out: dict[str, Any], report_md: str) -> None:
    out_dir = workspace / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{name}.md").write_text(report_md, encoding="utf-8")
