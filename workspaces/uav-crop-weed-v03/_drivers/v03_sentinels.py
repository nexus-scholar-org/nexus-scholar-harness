"""v0.3 sentinel recall probe (UAV-HARVEST-V03-PATCHED-20261017) — v2.

DOI-exact (case-insensitive) across record external_ids; if no DOI hit,
normalized-title containment fallback. Titles verified against baseline
artifacts (pilot calibration SENTINELS.md / demo 2026-10-16 deduped.json),
never invented. v2: records per-hit provenance (SCI-id, provider, year,
recorded DOI) and flags DOI-mismatch title hits. Read-only inputs; one MD output.
"""

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DATE_TAG = "20261017"

SEEDS = [
    (
        "S1",
        "10.1109/wacv61041.2025.00467",
        "WeedsGalore: A Multispectral and Multitemporal UAV-Based Dataset for Crop and Weed Segmentation in Agricultural Maize Fields",
    ),
    (
        "S2",
        "10.3389/fpls.2022.927368",
        "Semi-supervised Learning for Weed and Crop Segmentation Using UAV Imagery",
    ),
    ("S3", "10.3390/rs15215165", "Transformer in UAV Image-Based Weed Mapping"),
    (
        "S4",
        "10.3390/rs18060915",
        "BAWSeg: A UAV Multispectral Benchmark for Barley Weed Segmentation",
    ),
    (
        "S5",
        "10.48550/arxiv.2609.05762",
        "AAMBERS-UAV: Acquisition-Aware Multimodal Backbone Evaluation and Ranking for UAV Weedy Rice Segmentation",
    ),
    (
        "S6",
        "10.1186/s13007-023-01060-8",
        "Improved weed segmentation in UAV imagery of sorghum fields with a combined deblurring segmentation model",
    ),
    (
        "S7",
        "10.1016/j.compag.2022.107388",
        "Deep learning-based early weed segmentation using motion blurred UAV images of sorghum fields",
    ),
]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def ext_str(rec):
    return str(rec.get("external_ids") or "").lower()


def rec_field(d, key):
    v = d.get(key)
    return v if v is not None else "—"


def repr_line(d):
    ext = str(d.get("external_ids") or "")
    m = re.search(r"doi='([^']+)'", ext)
    doi = m.group(1) if m else "None"
    return (
        f"{d.get('workspace_id') or 'no-SCI'} | {d.get('provider')} | "
        f"{d.get('year')} | doi={doi}"
    )


def main():
    ded = json.loads((CAL / f"v03_{DATE_TAG}_deduped.json").read_text(encoding="utf-8"))
    reps = ded.get("documents", [])
    clusters = ded.get("clusters", [])

    uni = json.loads(
        (CAL / f"v03_{DATE_TAG}_union_raw.json").read_text(encoding="utf-8")
    )
    records = uni.get("documents", [])

    lines = []
    lines.append("# v0.3 sentinel recall — UAV-HARVEST-V03-PATCHED-20261017\n")
    lines.append(
        f"Recall base: `v03_{DATE_TAG}_deduped.json` ({ded.get('cluster_count')} representatives); "
        f"arrivals traced against `v03_{DATE_TAG}_union_raw.json` ({uni.get('union_count')} raw records). "
        "DOI match = case-insensitive containment on external_ids; title match = normalized-title "
        "containment fallback ONLY when the DOI axis missed; the two axes are kept separate. "
        "Title containment is NOT identity and is NOT counted as a DOI hit.\n"
    )
    lines.append(
        "| Seed | DOI | Title (short) | DOI-exact hits | Title-fallback hits | Hit provenance (SCI | provider | year | recorded DOI) | Raw arrivals | Verdict/Note |"
    )
    lines.append(
        "|------|-----|---------------|----------------|--------------------|---------------------|--------------|--------------|"
    )

    summary = []
    for sid, doi, title in SEEDS:
        dl = doi.lower()
        nests = []
        for d in reps:
            if dl in ext_str(d):
                nests.append(d)
        rtitle = [d for d in reps if nests == [] or False]
        thits = []
        if not nests:
            thits = [
                d for d in reps if norm(title) and norm(title) in norm(d.get("title"))
            ]
        raw_doi_arrivals = [(r.get("provider"), r) for r in records if dl in ext_str(r)]
        raw_t_arrivals = []
        if not nests and thits:
            raw_t_arrivals = [
                (r.get("provider"), r)
                for r in records
                if norm(title) and norm(title) in norm(r.get("title"))
            ]

        # DOI-mismatch check on title hits
        mismatch = False
        for d in thits:
            m = re.search(r"doi='([^']+)'", str(d.get("external_ids") or ""))
            rd = (m.group(1) or "").lower() if m else ""
            if rd and rd != dl:
                mismatch = True

        hit = bool(nests or thits)
        if nests:
            verdict = "DOI-EXACT HIT"
            prov = "; ".join(repr_line(d) for d in nests[:3])
        elif thits:
            verdict = "TITLE-FALLBACK HIT" + (
                " (DOI MISMATCH on record — see note)" if mismatch else ""
            )
            prov = "; ".join(repr_line(d) for d in thits[:3])
            if mismatch:
                prov += " | WARNING: same title, recorded DOI differs from seed DOI — possible provider ArticleId mis-parse or genuine title collision; NOT counted as DOI-exact"
            else:
                prov += " | note: record lacks the seed DOI (e.g., arXiv DOI-less twin); title axis only"
        else:
            verdict = "MISS"
            prov = "—"
        arr = "; ".join(sorted({a for a, _ in raw_doi_arrivals})) or (
            "title-axis: " + "; ".join(sorted({a for a, _ in raw_t_arrivals}))
            if raw_t_arrivals
            else "none"
        )
        note = ""
        if not hit:
            note = (
                "no raw record carries the seed DOI or its exact normalized title; "
                "consistent with relevance-rank shift + cap truncation under the expanded "
                "27-term v0.3 query (providers are relevance-ranked, cap-bounded) — human decision required"
            )
        summary.append((sid, dl, len(nests), len(thits), hit, mismatch))
        lines.append(
            f"| {sid} | `{doi}` | {title.split(':')[0][:48]} ({title.split(':')[1].strip()[:40] if ':' in title else '...'}) | "
            f"{len(nests)} | {len(thits)} | {prov} | {arr} | {verdict}. {note} |"
        )

    lines.append("")
    n_doi = sum(1 for s in summary if s[2] > 0)
    n_title = sum(1 for s in summary if s[3] > 0)
    n_hit = sum(1 for s in summary if s[4])
    lines.append(
        f"## Summary — DOI-exact: {n_doi}/7 | title-fallback only: {n_title - n_doi}/7 | total recalled: {n_hit}/7"
    )
    lines.append("")
    lines.append(
        "Baseline anchor (2026-10-16 unpatched, 5-sentinel table): S1 DOI-exact 2 (openalex+crossref), "
        "WeedMap S2' MISS out-of-window, SemiWeedNet DOI-exact 2, rs15215165 DOI-exact 2, j.atech HIT 1 — 4/4 in-window."
    )
    lines.append("")
    lines.append("Key deltas (headline findings for human interpretation):")
    lines.append(
        "- S1: baseline DOI-exact (crossref copy); this run DOI axis missed — same paper arrives title-exact via arXiv as a DOI-less twin (arxiv_id 2502.13103). Cross-provider identity alternative present, DOI crosswalk absent."
    )
    lines.append(
        "- S2 SemiWeedNet: DOI-exact HIT via crossref (baseline had openalex+crossref copies). This seed was historically an expected miss; its appearance under the patched run is patched-code/expanded-synonym behavior, verified against live raw records, not assumed."
    )
    lines.append(
        "- S3 rs15215165: baseline DOI-exact 2; this run MISS (no raw record with DOI or exact title) — consistent with relevance-rank shift + cap truncation under the expanded query."
    )
    lines.append(
        "- S4 BAWSeg: arrives title-exact via arXiv DOI-less twin (arxiv_id 2603.01932); seed DOI 10.3390/rs18060915 absent from all raw files."
    )
    lines.append(
        "- S5 AAMBERS (arxiv 2609.05762): MISS — arXiv leg returned 39/cap records; seed not among them."
    )
    lines.append(
        "- S6 s13007-023-01060-8: identical-title pubmed record carries DOI 10.7717/peerj.453 ≠ seed DOI; possible PubMed ArticleId mis-parse or genuine title collision; flagged, NOT counted as DOI-exact."
    )
    lines.append("- S7 compag.2022.107388: MISS.")
    out = CAL / f"v03_{DATE_TAG}_sentinel_recall.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE {out.name}", flush=True)
    for sid, dl, nd, nt, hit, mis in summary:
        print(
            f"SENTINEL {sid} {dl} doi-hits={nd} title-only={nt} hit={hit} mismatch={mis}",
            flush=True,
        )


if __name__ == "__main__":
    main()
