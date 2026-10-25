"""R3E — Single bounded rehydration retry over the r3d pool (researcher auth).

Retries abstract recovery for every DOI-bearing abstractless record in the
r3d definitive pool (14,413 pre-dedup docs). No new search calls; no kit
changes; strictly keyless (~assert SCHOLAR_S2_KEY absent). OA-first patched
hydrator, one bounded attempt (per researcher instruction: 'one last time').

Outputs (all v03_r3e_* NEW files; earlier rounds never overwritten):
  - v03_r3e_20261017_rehydration.json   (candidate list + per-batch stats)
  - v03_r3e_20261017_union_hydrated.json (full pool snapshot, pre-dedup, mutation-safe)
  - v03_r3e_20261017_deduped.json        (re-dedup after abstract merge)
  - v03_r3e_20261017_sentinel_memo.md
  - _drivers/v03_r3e_rehydration_summary.json
"""

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))
sys.path.insert(0, str(DRIVERS))

DATE_TAG = "20261017"
SESSION = "UAV-HARVEST-R3E-REHYD-20261017"
DOI_RE = re.compile(r"10\.\d{4,9}/[^,'\s]+")


from importlib import util as _ilu

_spec_u = _ilu.spec_from_file_location("v03union", str(DRIVERS / "v03_union.py"))
_u3 = _ilu.module_from_spec(_spec_u)
_spec_u.loader.exec_module(_u3)

SEEDS = [
    ("S1", "10.1109/wacv61041.2025.00467", ["2502.13103"]),
    ("S2", "10.3389/fpls.2022.927368", []),
    ("S3", "10.3390/rs15215165", []),
    ("S4", "10.3390/rs18060915", ["2603.01932"]),
    ("S5", "10.48550/arxiv.2609.05762", ["2609.05762"]),
    ("S6", "10.1186/s13007-023-01060-8", []),
    ("S7", "10.1016/j.compag.2022.107388", []),
]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def ser(doc):
    return dict(doc.__dict__) if hasattr(doc, "__dict__") else {"repr": str(doc)}


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


async def hydrate_isolated(hydrator, docs):
    try:
        return await hydrator.hydrate_missing_abstracts(docs, batch_size=50)
    except Exception:  # noqa: BLE001
        if len(docs) <= 1:
            return docs, {
                "attempted": len(docs),
                "hydrated": 0,
                "failed": len(docs),
            }
        mid = len(docs) // 2
        d1, s1 = await hydrate_isolated(hydrator, docs[:mid])
        d2, s2 = await hydrate_isolated(hydrator, docs[mid:])
        return d1 + d2, {
            "attempted": s1.get("attempted", 0) + s2.get("attempted", 0),
            "hydrated": s1.get("hydrated", 0) + s2.get("hydrated", 0),
            "failed": s1.get("failed", 0) + s2.get("failed", 0),
            "isolated_splits": True,
        }


def main_sync():
    if os.environ.get("SCHOLAR_S2_KEY") is not None:
        raise SystemExit(
            "ABORT: SCHOLAR_S2_KEY visible in this process; r3e retry runs "
            "strictly keyless. Launch with the variable removed."
        )

    base = json.loads(
        (CAL / f"v03_r3d_{DATE_TAG}_union_hydrated.json").read_text(encoding="utf-8")
    )
    existing = base["documents"]
    print(f"BASE r3d pool: {len(existing)} records", flush=True)

    # Candidate selection: abstractless AND DOI-bearing (hydratable channel).
    cand_idx = []
    for i, r in enumerate(existing):
        abs_txt = str(r.get("abstract") or "").strip()
        if abs_txt:
            continue
        ext = str(r.get("external_ids") or "")
        m = DOI_RE.search(ext.lower())
        if m:
            cand_idx.append(i)
    no_doil_title_only = sum(
        1
        for i, r in enumerate(existing)
        if not str(r.get("abstract") or "").strip() and i not in set(cand_idx)
    )
    print(
        f"CANDIDATES: doi-bearing abstractless={len(cand_idx)} "
        f"title-only-without-doi={no_doil_title_only}",
        flush=True,
    )

    # Rebuild every pool record live; assemble in original order.
    skipped = []
    pool_live = {}
    cand_set = set(cand_idx)
    cand_live = []
    for i, r in enumerate(existing):
        s2 = []
        d = _u3.rebuild(r, s2)
        skipped.extend(s2)
        if d is None:
            continue
        pool_live[i] = d
        if i in cand_set:
            cand_live.append(d)
    print(
        f"REBUILT pool={len(pool_live)} candidates={len(cand_live)} skipped={len(skipped)}",
        flush=True,
    )

    async def run_hydrate():
        from scholar_search.enrichment import AbstractHydrator
        from scholar_search.http_client import AcademicHttpClient

        c = AcademicHttpClient(name="r3e-rehyd", rate_limit=1.0)
        h = AbstractHydrator(c)
        out, stats = await hydrate_isolated(h, cand_live)
        try:
            await c.close()
        except Exception:  # noqa: BLE001
            pass
        return out, stats

    t0 = time.perf_counter()
    hydrated_live, hstats = asyncio.run(run_hydrate())
    wall = round(time.perf_counter() - t0, 2)
    print(
        f"REHYDRATION attempted={hstats.get('attempted')} hydrated={hstats.get('hydrated')} "
        f"failed={hstats.get('failed')} wall={wall}s",
        flush=True,
    )

    # Commit hydrated docs back into pool positions (by instance identity).
    hmap = {id(d): d for d in hydrated_live}
    pool_final = []
    for i in sorted(pool_live):
        d = pool_live[i]
        pool_final.append(hmap.get(id(d), d))
    print(f"POOL-FINAL: {len(pool_final)}", flush=True)

    pool_docs_pre = [ser(d) for d in pool_final]
    cov_pre = sum(
        1 for d in pool_final if (str(getattr(d, "abstract", "") or "")).strip()
    )

    from scholar_search.dedup import Deduplicator

    ded = Deduplicator()
    clusters, derr = dedup_isolated(ded, pool_final)
    stats = (
        ded.get_statistics(clusters)
        if clusters
        else {
            "total_documents": 0,
            "unique_documents": 0,
            "duplicates": 0,
            "duplicate_rate": 0.0,
        }
    )
    singletons = sum(1 for c in clusters if getattr(c, "size", len(c.members)) == 1)
    reps = [_u3.ser_doc(c.representative) for c in clusters]

    (CAL / f"v03_r3e_{DATE_TAG}_union_hydrated.json").write_text(
        json.dumps(
            {
                "base_pool": f"v03_r3d_{DATE_TAG}_union_hydrated.json",
                "purpose": "bounded rehydration retry (researcher authorization)",
                "leg_labels": [
                    *(base.get("leg_labels") or []),
                    "rehydration-retry(r3e)",
                ],
                "hydration_stats_r3e_retry": hstats,
                "union_count_r3e": len(pool_final),
                "documents": pool_docs_pre,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (CAL / f"v03_r3e_{DATE_TAG}_deduped.json").write_text(
        json.dumps(
            {
                "dedup_stats": stats,
                "cluster_count": len(clusters),
                "singleton_count": singletons,
                "dedup_error_note": derr,
                "documents": reps,
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
    (CAL / f"v03_r3e_{DATE_TAG}_rehydration.json").write_text(
        json.dumps(
            {
                "session": SESSION,
                "base_pool": f"v03_r3d_{DATE_TAG}_union_hydrated.json",
                "candidates_doi_abstractless": len(cand_idx),
                "title_only_without_doi": no_doil_title_only,
                "rebuilt_pool": len(pool_live),
                "rebuilt_candidates": len(cand_live),
                "hydration_stats": hstats,
                "wall_seconds": wall,
                "coverage_pre_dedup": {
                    "pool": len(pool_final),
                    "with_abstract": cov_pre,
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    blobs = [str(d.get("external_ids") or "").lower() for d in reps]
    out = ["# r3e sentinel memo (pool after bounded rehydration retry)\n"]
    hits = 0
    for sid, doi, ax in SEEDS:
        dl = doi.lower()
        doi_hits = [reps[i] for i, b in enumerate(blobs) if dl in b]
        ax_hits = (
            [reps[i] for i, b in enumerate(blobs) if any(a in b for a in ax)]
            if ax and not doi_hits
            else []
        )
        ok = bool(doi_hits or ax_hits)
        hits += ok
        sci = sorted(
            {
                reps[i].get("workspace_id") or "?"
                for i, b in enumerate(blobs)
                if dl in b or (ax and any(a in b for a in ax))
            }
        )
        out.append(
            f"- {sid}: {'HIT' if ok else 'MISS'} "
            f"({'doi-exact' if doi_hits else 'arxiv_id' if ax_hits else 'none'}) {sci}"
        )
    out.append(f"\nTier-1 PID: {hits}/7")
    (CAL / f"v03_r3e_{DATE_TAG}_sentinel_memo.md").write_text(
        "\n".join(out), encoding="utf-8"
    )

    summary = {
        "session": SESSION,
        "candidates_doi_abstractless": len(cand_idx),
        "title_only_without_doi": no_doil_title_only,
        "hydration_stats": hstats,
        "wall_seconds": wall,
        "pool": {
            "pool_r3e": len(pool_final),
            "with_abstract_pre_dedup": cov_pre,
            "coverage_basis": "pre-dedup snapshot (mutation-safe)",
        },
        "dedup_r3e": {
            "stats": stats,
            "clusters": len(clusters),
            "singletons": singletons,
            "error": derr,
        },
        "sentinel": {"tier1_hits": hits, "of": 7},
    }
    (DRIVERS / "v03_r3e_rehydration_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE r3e files + summary", flush=True)


if __name__ == "__main__":
    main_sync()
