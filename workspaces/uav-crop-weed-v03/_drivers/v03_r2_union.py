"""r2 union + hydration + dedup driver (UAV-HARVEST-R2-20261017).

Adapted from v03_union.py: r2 SOURCES/outputs, corrected DOI counting
(regex over string external_ids — the v03-run has_doi() defect is fixed at
the driver level). Hydration runs against the patched kit (OpenAlex-first).
"""

import asyncio
import json
import os
import re
from pathlib import Path

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"

from importlib import util as _ilu

_spec_u = _ilu.spec_from_file_location(
    "v03union",
    str(ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers" / "v03_union.py"),
)
_u3 = _ilu.module_from_spec(_spec_u)
_spec_u.loader.exec_module(_u3)

DATE_TAG = "20261017"
SESSION = "UAV-HARVEST-R2-20261017"

SOURCES = [
    ("openalex-full", f"v03_r2_{DATE_TAG}_raw_openalex.json"),
    ("semanticscholar", f"v03_r2_{DATE_TAG}_raw_semanticscholar.json"),
    ("crossref-full", f"v03_r2_{DATE_TAG}_raw_crossref.json"),
    ("arxiv-full", f"v03_r2_{DATE_TAG}_raw_arxiv.json"),
    ("pubmed", f"v03_r2_{DATE_TAG}_raw_pubmed.json"),
]

DOI_VAL_RE = re.compile(r"doi='([^']+)'")


def has_doi(rec):
    m = DOI_VAL_RE.search(str(rec.get("external_ids") or ""))
    return bool(m and m.group(1))


async def hydrate_isolated(hydrator, docs):
    try:
        return await hydrator.hydrate_missing_abstracts(docs, batch_size=50)
    except Exception:  # noqa: BLE001
        if len(docs) <= 1:
            return docs, {"attempted": len(docs), "hydrated": 0, "failed": len(docs)}
        mid = len(docs) // 2
        d1, s1 = await hydrate_isolated(hydrator, docs[:mid])
        d2, s2 = await hydrate_isolated(hydrator, docs[mid:])
        return d1 + d2, {
            "attempted": s1.get("attempted", 0) + s2.get("attempted", 0),
            "hydrated": s1.get("hydrated", 0) + s2.get("hydrated", 0),
            "failed": s1.get("failed", 0) + s2.get("failed", 0),
            "isolated_splits": True,
        }


def dedup_isolated(dedup, docs):
    try:
        return dedup.deduplicate(docs), None
    except Exception as e:  # noqa: BLE001
        if len(docs) <= 1:
            return [], str(e)[:200]
        mid = len(docs) // 2
        c1, e1 = dedup_isolated(dedup, docs[:mid])
        c2, e2 = dedup_isolated(dedup, docs[mid:])
        return c1 + c2, f"dedup split fallback used: {e1 or ''} {e2 or ''}".strip()


async def main():
    from scholar_search.dedup import Deduplicator
    from scholar_search.enrichment import AbstractHydrator
    from scholar_search.http_client import AcademicHttpClient

    per_source, raw_all = {}, []
    for label, fname in SOURCES:
        payload = json.loads((CAL / fname).read_text(encoding="utf-8"))
        per_source[label] = len(payload.get("documents", []))
        raw_all.extend(payload.get("documents", []))
        print(
            f"READ {fname}: count-field={payload.get('count')} docs={per_source[label]}",
            flush=True,
        )

    union_count = len(raw_all)
    cov_before = sum(1 for d in raw_all if _u3.has_abstract(d))
    doi_before = sum(1 for d in raw_all if has_doi(d))
    (CAL / f"v03_r2_{DATE_TAG}_union_raw.json").write_text(
        json.dumps(
            {
                "sources": [l for l, _ in SOURCES],
                "per_source_counts": per_source,
                "union_count": union_count,
                "abstract_coverage_before": {
                    "with_abstract": cov_before,
                    "without_abstract": union_count - cov_before,
                },
                "doi_bearing": doi_before,
                "doi_less": union_count - doi_before,
                "documents": raw_all,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        f"WROTE raw union={union_count} (sum={sum(per_source.values())}) abstracts={cov_before} doi-bearing={doi_before}",
        flush=True,
    )

    skipped = []
    live = [d for d in (_u3.rebuild(r, skipped) for r in raw_all) if d is not None]
    print(f"REBUILT live={len(live)} skipped={len(skipped)}", flush=True)

    hydr = AcademicHttpClient(name="r2-hydrator", rate_limit=1.0)
    h = AbstractHydrator(hydr)
    live_h, hstats = await hydrate_isolated(h, live)
    try:
        await hydr.close()
    except Exception:
        pass
    cov_after = sum(1 for d in live_h if (d.abstract or "").strip())
    (CAL / f"v03_r2_{DATE_TAG}_union_hydrated.json").write_text(
        json.dumps(
            {
                "hydration_stats": hstats,
                "abstract_coverage_before": cov_before,
                "abstract_coverage_after": cov_after,
                "documents": [_u3.ser_doc(d) for d in live_h],
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        f"HYDRATION attempted={hstats.get('attempted')} hydrated={hstats.get('hydrated')} failed={hstats.get('failed')} coverage {cov_before}->{cov_after}",
        flush=True,
    )

    dedup = Deduplicator()
    clusters, derr = dedup_isolated(dedup, live_h)
    stats = (
        dedup.get_statistics(clusters)
        if clusters
        else {
            "total_documents": 0,
            "unique_documents": 0,
            "duplicates": 0,
            "duplicate_rate": 0.0,
        }
    )
    singletons = sum(1 for c in clusters if getattr(c, "size", len(c.members)) == 1)
    (CAL / f"v03_r2_{DATE_TAG}_deduped.json").write_text(
        json.dumps(
            {
                "dedup_stats": stats,
                "cluster_count": len(clusters),
                "singleton_count": singletons,
                "dedup_error_note": derr,
                "documents": [_u3.ser_doc(c.representative) for c in clusters],
                "clusters": [
                    {
                        "cluster_id": c.cluster_id,
                        "size": len(c.members),
                        "representative_title": (c.representative.title or "")[:150],
                        "members": [
                            {
                                "title": (m.title or "")[:120],
                                "year": m.year,
                                "provider": m.provider,
                                "doi": m.external_ids.doi if m.external_ids else None,
                                "arxiv_id": m.external_ids.arxiv_id
                                if m.external_ids
                                else None,
                            }
                            for m in c.members
                        ],
                    }
                    for c in clusters
                ],
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        f"DEDUP {stats} clusters={len(clusters)} singletons={singletons} err={derr!r}",
        flush=True,
    )

    summary = {
        "session": SESSION,
        "per_provider": per_source,
        "union_total": union_count,
        "rebuild_skipped": len(skipped),
        "hydration": hstats,
        "abstract_coverage": {
            "before": cov_before,
            "after": cov_after,
            "still_no_abstract_pool": len(live_h) - cov_after,
        },
        "dedup": {
            "stats": stats,
            "clusters": len(clusters),
            "singletons": singletons,
            "merged": stats.get("duplicates"),
            "error_note": derr,
        },
    }
    (DRIVERS / "v03_r2_union_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE v03_r2_union_summary.json", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
