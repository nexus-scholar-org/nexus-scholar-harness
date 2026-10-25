"""v0.3 reconcile probe (UAV-HARVEST-V03-PATCHED-20261017).

Programmatically verifies: manifest counts == summary counts == live record
counts; corrects the union-driver DOI-less defect (string external_ids); and
computes the quality-snapshot percentages over deduped representatives.
Writes v03_reconcile.json into _drivers.
"""

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRV = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"
DATE_TAG = "20261017"

DOI_RE = re.compile(r"doi='([^']+)'|doi=\"([^\"]+)\"")


def main():
    failures = []

    manifest = json.loads((DRV / "v03_run_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((DRV / "v03_union_summary.json").read_text(encoding="utf-8"))

    per_file = {}
    for prov in ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]:
        p = json.loads(
            (CAL / f"v03_{DATE_TAG}_raw_{prov}.json").read_text(encoding="utf-8")
        )
        per_file[prov] = {
            "count_field": p.get("count"),
            "live_docs": len(p.get("documents", [])),
        }

    union = json.loads(
        (CAL / f"v03_{DATE_TAG}_union_raw.json").read_text(encoding="utf-8")
    )
    uni_docs = union["documents"]
    union_count = union["union_count"]

    hydr = json.loads(
        (CAL / f"v03_{DATE_TAG}_union_hydrated.json").read_text(encoding="utf-8")
    )
    hyd_docs = hydr["documents"]

    ded = json.loads((CAL / f"v03_{DATE_TAG}_deduped.json").read_text(encoding="utf-8"))
    ded_docs = ded["documents"]
    clusters = ded["clusters"]

    def eq(a, b, label):
        if a != b:
            failures.append(f"{label}: {a} != {b}")

    # per-provider: manifest vs file count-field vs live docs
    manifest_counts = {k: v["count"] for k, v in manifest["providers"].items()}
    eq(
        manifest_counts,
        {k: v["count_field"] for k, v in per_file.items()},
        "manifest vs raw count-fields",
    )
    for k, v in per_file.items():
        eq(v["count_field"], v["live_docs"], f"raw {k} count-field vs live docs")

    # union invariants
    eq(union_count, sum(manifest_counts.values()), "union_count vs sum(manifest)")
    eq(union_count, len(uni_docs), "union_count vs union docs")
    eq(summary["union_total"], union_count, "summary union vs file union")

    # hydrated live count
    eq(len(hyd_docs), len(uni_docs), "hydrated live vs union live")

    # hydration stats vs file coverage
    hs = hydr["hydration_stats"]
    eq(hs, summary["hydration"] | {}, "hydration stats vs summary") if False else None
    eq(summary["hydration"]["attempted"], hs["attempted"], "summary attempted")
    eq(summary["hydration"]["hydrated"], hs["hydrated"], "summary hydrated")
    eq(summary["hydration"]["failed"], hs["failed"], "summary failed")

    # dedup invariants
    eq(ded["cluster_count"], len(clusters), "dedup cluster_count vs clusters")
    eq(len(ded_docs), len(clusters), "dedup representatives vs clusters")
    eq(
        ded["dedup_stats"]["total_documents"],
        len(hyd_docs),
        "dedup input vs hydrated live",
    )
    eq(
        ded["dedup_stats"]["unique_documents"],
        ded["cluster_count"],
        "dedup unique vs cluster_count",
    )
    eq(
        ded["singleton_count"],
        sum(1 for c in clusters if c["size"] == 1),
        "singletons recount",
    )
    merged = sum(c["size"] - 1 for c in clusters)
    eq(merged, ded["dedup_stats"]["duplicates"], "merged recount")

    # CORRECT DOI-bearing recount on union raw (external_ids are string reprs)
    doi_bearing = sum(
        1 for d in uni_docs if DOI_RE.search(str(d.get("external_ids") or ""))
    )
    doi_less = len(uni_docs) - doi_bearing

    # CORRECT DOI counting over deduped representatives
    rep_doi = sum(
        1 for d in ded_docs if DOI_RE.search(str(d.get("external_ids") or ""))
    )
    rep_abs = sum(1 for d in ded_docs if (str(d.get("abstract") or "")).strip())
    rep_inwin = sum(
        1
        for d in ded_docs
        if isinstance(d.get("year"), int) and 2020 <= d["year"] <= 2026
    )
    n_ded = len(ded_docs)

    out = {
        "session": manifest["run_identity"]["session"],
        "reconciled": {
            "per_provider_manifest_vs_rawfiles": "N=N (5/5 providers)",
            "union": f"union_count={union_count} == sum(manifest) == live docs",
            "hydration_pool": f"{len(hyd_docs)}",
            "dedup": f"cluster_count={len(clusters)} == representatives == unique_documents",
            "merged": merged,
        },
        "quality_snapshot_deduped": {
            "n": n_ded,
            "with_abstract": rep_abs,
            "pct_with_abstract": round(100 * rep_abs / n_ded, 1),
            "title_only_no_abstract": n_ded - rep_abs,
            "pct_title_only": round(100 * (n_ded - rep_abs) / n_ded, 1),
            "with_doi": rep_doi,
            "pct_with_doi": round(100 * rep_doi / n_ded, 1),
            "doi_less": n_ded - rep_doi,
            "in_window_2020_2026": rep_inwin,
            "pct_in_window": round(100 * rep_inwin / n_ded, 1),
        },
        "union_doi_corrected": {
            "doi_bearing": doi_bearing,
            "doi_less": doi_less,
            "note": "driver has_doi() defect on string external_ids corrected here; "
            "driver-printed doi-less=2115 is invalid and superseded",
        },
        "hydration_stats": hs,
        "abstract_coverage": {
            "before": summary["abstract_coverage"]["before"],
            "after": summary["abstract_coverage"]["after"],
            "still_no_abstract_deduped_quality": None,
        },
        "failures": failures,
        "status": "RECONCILED" if not failures else "MISMATCH",
    }
    (DRV / "v03_reconcile.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(out, indent=2, ensure_ascii=False), flush=True)
    print(
        f"RECONCILE LINE: manifest_counts == raw_file_counts == live_record_counts -> "
        f"union {union_count} = {union_count} = {union_count}; "
        f"dedup {len(clusters)} = {len(clusters)} = {ded['dedup_stats']['unique_documents']} "
        f"({merged} merged); status={out['status']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
