"""r2 sentinel recall (UAV-HARVEST-R3-20261017) â€” PID Tier-1 + separate title axis.

Decision (b)2 applied: Tier-1 = Canonical Persistent Identifier equality on
(doi OR arxiv_id), including OBSERVED cross-PIDs (recorded from live v0.3-run
artifacts / baseline deduped.json â€” never invented). Title containment stays
a separate, non-identity axis and is reported but does not count as Tier-1.
"""

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DATE_TAG = "20261017"

# (label, primary doi, [(axis, value, source)], title, note)
# OBSERVED cross-PIDs are sourced from live artifacts seen this session:
#  - S1 arxiv 2502.13103 and S4 2603.01932: arXiv raw records in v03 run raw files
#  - S5 arxiv_id 2609.05762: DataCite DOI 10.48550/arxiv.2609.05762 suffix
SEEDS = [
    (
        "S1",
        "10.1109/wacv61041.2025.00467",
        [("arxiv_id", "2502.13103")],
        "WeedsGalore: A Multispectral and Multitemporal UAV-Based Dataset for Crop and Weed Segmentation in Agricultural Maize Fields",
    ),
    (
        "S2",
        "10.3389/fpls.2022.927368",
        [],
        "Semi-supervised Learning for Weed and Crop Segmentation Using UAV Imagery",
    ),
    ("S3", "10.3390/rs15215165", [], "Transformer in UAV Image-Based Weed Mapping"),
    (
        "S4",
        "10.3390/rs18060915",
        [("arxiv_id", "2603.01932")],
        "BAWSeg: A UAV Multispectral Benchmark for Barley Weed Segmentation",
    ),
    (
        "S5",
        "10.48550/arxiv.2609.05762",
        [("arxiv_id", "2609.05762")],
        "AAMBERS-UAV: Acquisition-Aware Multimodal Backbone Evaluation and Ranking for UAV Weedy Rice Segmentation",
    ),
    (
        "S6",
        "10.1186/s13007-023-01060-8",
        [],
        "Improved weed segmentation in UAV imagery of sorghum fields with a combined deblurring segmentation model",
    ),
    (
        "S7",
        "10.1016/j.compag.2022.107388",
        [],
        "Deep learning-based early weed segmentation using motion blurred UAV images of sorghum fields",
    ),
]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def pid_blob(rec):
    """All canonical PIDs carried by a record (external_ids string repr)."""
    s = str(rec.get("external_ids") or "").lower()
    return s


def main():
    ded = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_deduped.json").read_text(encoding="utf-8")
    )
    reps = ded.get("documents", [])
    uni = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_union_raw.json").read_text(encoding="utf-8")
    )
    records = uni.get("documents", [])

    lines = ["# r2 sentinel recall â€” UAV-HARVEST-R3-20261017\n"]
    lines.append(
        f"Recall base: `v03_r3_{DATE_TAG}_deduped.json` ({ded.get('cluster_count')} representatives). "
        "Tier-1 = Canonical PID equality (doi OR arxiv_id, crosswalk PIDs marked OBSERVED from live artifacts). "
        "Title containment is reported separately and is NOT identity. Provider arrivals from the raw union.\n"
    )
    lines.append(
        "| Seed | Tier-1 PIDs (seed) | DOI-exact | arxiv_id-exact | Title-only | SCI-id(s) | Arrivals (providers) | Verdict |"
    )
    lines.append(
        "|------|--------------------|-----------|----------------|------------|-----------|----------------------|---------|"
    )

    summary = []
    for sid, doi, crosspids, title in SEEDS:
        dl = doi.lower()
        doi_hits = [d for d in reps if dl in pid_blob(d)]
        ax_hits = []
        ax_vals = [v.lower() for _, v in crosspids]
        if ax_vals and not doi_hits:
            ax_hits = [d for d in reps if any(v in pid_blob(d) for v in ax_vals)]
        title_hits = []
        if not (doi_hits or ax_hits):
            title_hits = [
                d for d in reps if norm(title) and norm(title) in norm(d.get("title"))
            ]
        raw_p = sorted({r.get("provider") for r in records if dl in pid_blob(r)})
        raw_a = sorted(
            {
                r.get("provider")
                for r in records
                if ax_vals and any(v in pid_blob(r) for v in ax_vals)
            }
        )
        sci = sorted({d.get("workspace_id") or "?" for d in doi_hits + ax_hits})

        print(
            f"SENTINEL {sid} doi-hits={len(doi_hits)} arxiv-hits={len(ax_hits)} title-only={len(title_hits)} pids={sci} doi-arrivals={raw_p} arxiv-arrivals={raw_a}",
            flush=True,
        )
        if doi_hits:
            verdict, arr = "PID HIT (doi-exact)", "; ".join(raw_p)
        elif ax_hits:
            ax_label = ", ".join(f"{a}={v}" for a, v in crosspids)
            verdict, arr = (
                f"PID HIT (observed crosswalk: {ax_label})",
                "arxiv via " + ("; ".join(raw_a) or "n/a"),
            )
        elif title_hits:
            verdict, arr = "TITLE-ONLY MATCH (not identity)", "title-axis"
        else:
            verdict, arr = "MISS", "none"
        summary.append((sid, bool(doi_hits or ax_hits), verdict))
        pid_desc = f"`{doi}`" + (
            f" + {', '.join(f'{a}={v}' for a, v in crosspids)} (OBSERVED)"
            if crosspids
            else ""
        )
        nsci = "; ".join(sci) if sci else "â€”"
        lines.append(
            f"| {sid} | {pid_desc} | {len(doi_hits)} | {len(ax_hits)} | {len(title_hits)} "
            f"| {nsci} | {arr} | {verdict} |"
        )

    lines.append("")
    lines.append(
        ""
        ""
        "(1 DOI-exact + 3 title-only; S3/S5/S7 MISS). r2 rows above show the "
        "post-fix (strict filter, scoped pubmed IDs, PID axis) behavior."
    )
    lines.append("")
    n_pid = sum(1 for s in summary if s[1])
    lines.append(f"## Summary â€” Tier-1 PID recall: {n_pid}/7")
    for sid, ok, verdict in summary:
        lines.append(f"- {sid}: {verdict}")
    out = CAL / f"v03_r3_{DATE_TAG}_sentinel_recall.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE {out.name}", flush=True)


if __name__ == "__main__":
    main()


