"""r2 reconcile (UAV-HARVEST-R3-20261017): manifest == files == live records."""

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
    manifest = json.loads(
        (DRV / "v03_r3_run_manifest.json").read_text(encoding="utf-8")
    )
    summary = json.loads(
        (DRV / "v03_r3_union_summary.json").read_text(encoding="utf-8")
    )

    per_file = {}
    for prov in ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]:
        p = json.loads(
            (CAL / f"v03_r3_{DATE_TAG}_raw_{prov}.json").read_text(encoding="utf-8")
        )
        per_file[prov] = {
            "count_field": p.get("count"),
            "live_docs": len(p.get("documents", [])),
        }

    union = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_union_raw.json").read_text(encoding="utf-8")
    )
    hydr = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_union_hydrated.json").read_text(encoding="utf-8")
    )
    ded = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_deduped.json").read_text(encoding="utf-8")
    )

    def eq(a, b, label):
        if a != b:
            failures.append(f"{label}: {a} != {b}")

    eq(
        {k: v["count"] for k, v in manifest["providers"].items()},
        {k: v["count_field"] for k, v in per_file.items()},
        "manifest vs raw count-fields",
    )
    for k, v in per_file.items():
        eq(v["count_field"], v["live_docs"], f"raw {k} live")
    eq(
        union["union_count"],
        sum(
            manifest_counts := {
                k: v["count"] for k, v in manifest["providers"].items()
            }.values()
        ),
        "union vs sum(manifest)",
    )
    eq(union["union_count"], len(union["documents"]), "union vs live docs")
    eq(len(hydr["documents"]), len(union["documents"]), "hydrated vs union live")
    eq(ded["cluster_count"], len(ded["clusters"]), "cluster_count vs clusters")
    eq(len(ded["documents"]), ded["cluster_count"], "reps vs clusters")
    eq(ded["dedup_stats"]["total_documents"], len(hydr["documents"]), "dedup input")
    eq(
        ded["singleton_count"],
        sum(1 for c in ded["clusters"] if c["size"] == 1),
        "singletons",
    )
    merged = sum(c["size"] - 1 for c in ded["clusters"])
    eq(merged, ded["dedup_stats"]["duplicates"], "merged")
    eq(summary["hydration"], hydr["hydration_stats"], "summary hydration stats")
    label_alias = {
        "openalex-full": "openalex",
        "crossref-full": "crossref",
        "arxiv-full": "arxiv",
        "semanticscholar": "semanticscholar",
        "pubmed": "pubmed",
    }
    eq(
        {label_alias[k]: v for k, v in summary["per_provider"].items()},
        {k: v["live_docs"] for k, v in per_file.items()},
        "summary per-provider",
    )

    n = len(ded["documents"])
    rep_doi = sum(
        1 for d in ded["documents"] if DOI_RE.search(str(d.get("external_ids") or ""))
    )
    rep_abs = sum(1 for d in ded["documents"] if (str(d.get("abstract") or "")).strip())
    rep_win = sum(
        1
        for d in ded["documents"]
        if isinstance(d.get("year"), int) and 2020 <= d["year"] <= 2026
    )
    uni_doi = union["doi_bearing"]
    out = {
        "session": manifest["run_identity"]["session"],
        "status": "RECONCILED" if not failures else "MISMATCH",
        "failures": failures,
        "reconcile_line": (
            f"manifest_counts == raw_file_counts == live_records -> union {union['union_count']} = "
            f"{union['union_count']} = {union['union_count']}; dedup {ded['cluster_count']} = {ded['cluster_count']} "
            f"= {ded['dedup_stats']['unique_documents']} ({merged} merged)"
        ),
        "quality_snapshot_deduped": {
            "n": n,
            "with_abstract": rep_abs,
            "pct_with_abstract": round(100 * rep_abs / n, 1),
            "title_only": n - rep_abs,
            "pct_title_only": round(100 * (n - rep_abs) / n, 1),
            "with_doi": rep_doi,
            "pct_with_doi": round(100 * rep_doi / n, 1),
            "in_window": rep_win,
            "pct_in_window": round(100 * rep_win / n, 1),
        },
        "union_doi": {
            "doi_bearing": uni_doi,
            "doi_less": union["union_count"] - uni_doi,
        },
        "hydration_stats": hydr["hydration_stats"],
        "dedup_stats": ded["dedup_stats"],
    }
    (DRV / "v03_r3_reconcile.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(out, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

