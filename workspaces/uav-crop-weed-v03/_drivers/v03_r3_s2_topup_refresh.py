"""S2 top-up incremental refresh — v03_r3 (decision (i), `_INC` outputs only).

Reads the top-up file (any count, including 0/DRY) + the ORIGINAL r3 artifacts
(read-only), computes genuinely-new S2 records, hydrates ONLY the new ones
(OA-first, patched), merges and re-dedups the full pool into *_INC files,
re-checks the 7 sentinels on the INC pool, and writes a refresh summary for
journaling. Never overwrites ANY existing artifact.
"""

import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))

DATE_TAG = "20261017"
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


# Load v03_union.py's rebuild ONCE (module-level, mirroring v03_r3_union.py);
# per-call re-execution would reload the module for every record.
from importlib import util as _ilu

_spec_u = _ilu.spec_from_file_location("v03union", str(DRIVERS / "v03_union.py"))
_u3 = _ilu.module_from_spec(_spec_u)
_spec_u.loader.exec_module(_u3)


def rebuild(raw, skipped):
    return _u3.rebuild(raw, skipped)


def main_sync():
    import os

    if os.environ.get("SCHOLAR_S2_KEY") is not None:
        raise SystemExit(
            "ABORT: SCHOLAR_S2_KEY visible in this process; the top-up round is "
            "strictly keyed=no. Launch with the variable removed."
        )
    topup_path = CAL / f"v03_r3_{DATE_TAG}_s2_topup.json"
    if not topup_path.exists():
        print("NO-TOPUP-FILE: run v03_r3_s2_topup.py first")
        return
    topup = json.loads(topup_path.read_text(encoding="utf-8"))
    topup_docs = topup.get("documents", [])
    dry = topup.get("quota_state") == "DRY"
    print(
        f"TOPUP: count={len(topup_docs)} quota_state={topup.get('quota_state')}",
        flush=True,
    )

    uni_raw = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_union_raw.json").read_text(encoding="utf-8")
    )
    hyd = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_union_hydrated.json").read_text(encoding="utf-8")
    )
    base_ded = json.loads(
        (CAL / f"v03_r3_{DATE_TAG}_deduped.json").read_text(encoding="utf-8")
    )
    existing = uni_raw["documents"]
    n_existing = len(existing)

    # genuinely-new detection
    def idsig(rec):
        s = str(rec.get("external_ids") or "").lower()
        return s + "|" + norm(rec.get("title")) + "|" + str(rec.get("year"))

    existing_sigs = {idsig(r) for r in existing}
    existing_pids = set()
    for r in existing:
        s = str(r.get("external_ids") or "").lower()
        for pid in re.findall(r"10\.\d{4,9}/[^\s']+", s):
            existing_pids.add(pid)
        for pid in re.findall(r"arxiv_id='([^']+)'", s):
            existing_pids.add(f"arxiv:{pid.lower()}")

    def is_new(rec):
        ext = str(rec.get("external_ids") or "").lower()
        overlaps = 0
        for pid in re.findall(r"10\.\d{4,9}/[^\s']+", ext):
            if pid in existing_pids:
                overlaps += 1
        for pid in re.findall(r"arxiv_id='([^']+)'", ext):
            if f"arxiv:{pid.lower()}" in existing_pids:
                overlaps += 1
        if overlaps:
            return False
        # Provider-name collision adds no identity signal here (the r3 base
        # pool contains zero S2 records), so PID + title/year signature is
        # the discriminant.
        return idsig(rec) not in existing_sigs

    new_raw = [d for d in topup_docs if is_new(d)]
    print(
        f"NEW-DETECTION: topup={len(topup_docs)} new={len(new_raw)} "
        f"dup-against-base={len(topup_docs) - len(new_raw)}",
        flush=True,
    )

    if dry or not new_raw:
        # Dry-quota or pure-duplicate outcome: NO _INC pool change; re-check
        # the sentinels on the UNCHANGED r3 pool and write the memo + summary.
        memo = sentinel_memo(base_ded, suffix="topup", merged_note=True)
        summary = {
            "quota_state": topup.get("quota_state"),
            "topup_fetched": len(topup_docs),
            "topup_new": len(new_raw),
            "inc_pool_changed": False,
            "base_pool_unchanged": {
                "union": n_existing,
                "dedup_reps": base_ded["cluster_count"],
                "merged": base_ded["dedup_stats"]["duplicates"],
            },
            "acceptance_note": (
                "PRISMA DISCLOSURE: Semantic Scholar contributed 0 records to "
                "the definitive harvest (retrieval executed 2026-10-17); the "
                "unauthenticated per-IP quota was exhausted by the same-day "
                "verification pass; database partially covered on the recorded "
                "date. r2->r3 S2 200->0 is rate-limit life-cycle, not regression."
            )
            if dry
            else "top-up fetched {0} records; all already represented by PID/title overlap".format(
                len(topup_docs)
            ),
            "sentinel_memo": memo,
        }
        (DRIVERS / "v03_r3_topup_refresh_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("WROTE v03_r3_topup_refresh_summary.json (no pool change)", flush=True)
        return

    # Real incremental path
    skipped = []
    new_live = [d for d in (rebuild(r, skipped) for r in new_raw) if d is not None]
    print(f"REBUILT new={len(new_live)} skipped={len(skipped)}", flush=True)

    async def hydrate_new():
        from scholar_search.enrichment import AbstractHydrator
        from scholar_search.http_client import AcademicHttpClient

        c = AcademicHttpClient(name="r3-topup-hydrator", rate_limit=1.0)
        h = AbstractHydrator(c)

        async def isolated(docs):
            try:
                return await h.hydrate_missing_abstracts(docs, batch_size=50)
            except Exception:  # noqa: BLE001
                if len(docs) <= 1:
                    return docs, {
                        "attempted": len(docs),
                        "hydrated": 0,
                        "failed": len(docs),
                    }
                mid = len(docs) // 2
                d1, s1 = await isolated(docs[:mid])
                d2, s2 = await isolated(docs[mid:])
                return d1 + d2, {
                    k: s1.get(k, 0) + s2.get(k, 0)
                    for k in ("attempted", "hydrated", "failed")
                }

        out, stats = await isolated(new_live)
        await c.close()
        return out, stats

    new_h, hstats = asyncio.run(hydrate_new())
    print(f"HYDRATION-NEW stats={hstats}", flush=True)

    # merged pool = existing hydrated docs (strings) rebuilt + new docs
    existing_h_live = []
    skipped2 = []
    for d in hyd["documents"]:
        got = rebuild(d, skipped2)
        if got is not None:
            existing_h_live.append(got)
    pool = existing_h_live + list(new_h)
    print(
        f"POOL: existing_hydrated={len(existing_h_live)} new={len(new_h)} total={len(pool)}",
        flush=True,
    )

    from scholar_search.dedup import Deduplicator

    ded = Deduplicator()

    def dedup_isolated(dedup, docs):
        # Mirrors v03_r3_union.py: deduplicate() returns a bare cluster list;
        # errors fall back to bisected retry so one poison record cannot
        # zero the leg.
        try:
            return dedup.deduplicate(docs), None
        except Exception as e:  # noqa: BLE001
            if len(docs) <= 1:
                return [], str(e)[:200]
            mid = len(docs) // 2
            c1, e1 = dedup_isolated(dedup, docs[:mid])
            c2, e2 = dedup_isolated(dedup, docs[mid:])
            return c1 + c2, f"dedup split fallback used: {e1 or ''} {e2 or ''}".strip()

    clusters, derr = dedup_isolated(ded, pool)
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
    (CAL / f"v03_r3_{DATE_TAG}_union_hydrated_INC.json").write_text(
        json.dumps(
            {
                "base_hydrated": f"v03_r3_{DATE_TAG}_union_hydrated.json",
                "base_union_raw": f"v03_r3_{DATE_TAG}_union_raw.json",
                "topup_source": topup_path.name,
                "per_source_counts": {
                    **uni_raw["per_source_counts"],
                    "s2_topup_new": len(new_raw),
                },
                "hydration_stats_topup": hstats,
                "union_count_INC": len(pool),
                "documents": [ser(d) for d in pool],
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    ded_inc = {
        "dedup_stats": stats,
        "cluster_count": len(clusters),
        "singleton_count": singletons,
        "dedup_error_note": derr,
        "documents": [ser(c.representative) for c in clusters],
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
                        "arxiv_id": m.external_ids.arxiv_id if m.external_ids else None,
                    }
                    for m in c.members
                ],
            }
            for c in clusters
        ],
    }
    (CAL / f"v03_r3_{DATE_TAG}_deduped_INC.json").write_text(
        json.dumps(ded_inc, default=str, ensure_ascii=False), encoding="utf-8"
    )
    memo = sentinel_memo(ded_inc, suffix="topup", merged_note=True)
    cov = sum(1 for d in pool if (str(getattr(d, "abstract", "") or "")).strip())
    summary = {
        "quota_state": topup.get("quota_state"),
        "topup_fetched": len(topup_docs),
        "topup_new": len(new_raw),
        "inc_pool_changed": True,
        "pool": {
            "pool_INC": len(pool),
            "with_abstract": cov,
            "topup_hydrated": hstats.get("hydrated"),
            "topup_attempted": hstats.get("attempted"),
        },
        "dedup_INC": {
            "stats": stats,
            "clusters": len(clusters),
            "singletons": singletons,
            "error": derr,
        },
        "sentinel_memo": memo,
        "acceptance_note": None,
    }
    (DRIVERS / "v03_r3_topup_refresh_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE _INC files + summary", flush=True)


def sentinel_memo(ded_payload, suffix, merged_note):
    """PID tier-1 re-check over a dedup payload dict."""
    reps = ded_payload["documents"]
    out = [f"# r3 top-up sentinel memo ({suffix})\n"]
    hits = 0
    for sid, doi, ax in SEEDS:
        dl = doi.lower()
        doi_hits = [d for d in reps if dl in str(d.get("external_ids") or "").lower()]
        ax_hits = [
            d
            for d in reps
            if ax and any(a in str(d.get("external_ids") or "").lower() for a in ax)
        ]
        sci = sorted({d.get("workspace_id") or "?" for d in doi_hits + ax_hits})
        ok = bool(doi_hits or ax_hits)
        hits += ok
        out.append(
            f"- {sid}: {'HIT' if ok else 'MISS'} ({'doi' if doi_hits else 'arxiv_id' if ax_hits else 'none'}) {sci}"
        )
    out.append(
        f"\nTier-1 PID: {hits}/7 — expected memo: 7/7 unchanged." if merged_note else ""
    )
    (CAL / f"v03_r3_{DATE_TAG}_sentinel_memo_{suffix}.md").write_text(
        "\n".join(out), encoding="utf-8"
    )
    return {"tier1_hits": hits, "of": 7}


if __name__ == "__main__":
    main_sync()
