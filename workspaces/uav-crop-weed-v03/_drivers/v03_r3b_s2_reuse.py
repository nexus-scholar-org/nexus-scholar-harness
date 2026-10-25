"""R3B S2-leg REUSE refresh — Option A (researcher authorization EVT-20261017191328).

Source = the cached, verified r2 S2 raw leg (v03_r2_20261017_raw_semanticscholar.json,
200 records fetched 2026-10-17 ~16:10 under code state patched_post-L1L6+r2fixes,
unauthenticated after keyed-403 downgrade). NO new S2 API call is attempted.

Flow: read-only against ALL r3 artifacts -> PID/title overlap detection of
genuinely-new S2 records -> rebuild (models-level PMID normalization applies to
legacy cached docs) -> hydrate ONLY the new (OA-first, warmly split-fixed) ->
merged pool re-dedup -> r3b-prefixed outputs + sentinel memo + summary.
Never overwrites r3 or r2 artifacts; all outputs are v03_r3b_* new files.
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
SRC_FILE = "v03_r2_20261017_raw_semanticscholar.json"
LEG_LABEL = "S2-leg-reused-from-r2-cache"
LEG_NOTE = (
    "S2 retrieval executed 2026-10-17 (~16:10) under "
    "patched_post-L1L6+r2fixes, unauthenticated endpoint after keyed-403 "
    "downgrade; reuse authorized by the researcher (Option A). No new S2 "
    "API call in r3b."
)

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


def sentinel_memo(reps, path):
    out = [
        "# r3b sentinel memo (pool after S2-leg reuse)\n",
        "Tier-1 = Canonical PID equality (doi OR arxiv_id, observed crosswalks).\n",
    ]
    hits = 0
    rows = []
    for sid, doi, ax in SEEDS:
        dl = doi.lower()
        blob = [str(d.get("external_ids") or "").lower() for d in reps]
        doi_hits = [reps[i] for i, b in enumerate(blob) if dl in b]
        ax_hits = (
            [reps[i] for i, b in enumerate(blob) if any(a in b for a in ax)]
            if ax and not doi_hits
            else []
        )
        ok = bool(doi_hits or ax_hits)
        hits += ok
        sci = sorted({d.get("workspace_id") or "?" for d in doi_hits + ax_hits})
        rows.append(
            f"- {sid}: {'HIT' if ok else 'MISS'} "
            f"({'doi-exact' if doi_hits else 'arxiv_id' if ax_hits else 'none'}) {sci}"
        )
    out.extend(rows)
    out.append(f"\nTier-1 PID: {hits}/7")
    path.write_text("\n".join(out), encoding="utf-8")
    return {"tier1_hits": hits, "of": 7}


def main_sync():
    import os

    if os.environ.get("SCHOLAR_S2_KEY") is not None:
        raise SystemExit(
            "ABORT: SCHOLAR_S2_KEY visible in this process; r3b runs strictly "
            "keyless. Launch with the variable removed."
        )

    src = json.loads((CAL / SRC_FILE).read_text(encoding="utf-8"))
    s2_docs = src.get("documents", [])
    print(
        f"SOURCE {SRC_FILE}: count-field={src.get('count')} docs={len(s2_docs)}",
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
        return idsig(rec) not in existing_sigs

    new_raw = [d for d in s2_docs if is_new(d)]
    researcher_hypothesis = {
        "s2_total": len(s2_docs),
        "predicted_new_uniques": len(s2_docs) - 126,
    }
    print(
        f"NEW-DETECTION: s2={len(s2_docs)} new={len(new_raw)} "
        f"dup-against-base={len(s2_docs) - len(new_raw)} "
        f"(researcher hypothesis ~74 unique; verified empirically, not assumed)",
        flush=True,
    )

    if not new_raw:
        memo = sentinel_memo(
            base_ded["documents"], DRIVERS / "v03_r3b_sentinel_memo.md"
        )
        summary = {
            "leg_label": LEG_LABEL,
            "leg_note": LEG_NOTE,
            "s2_total": len(s2_docs),
            "s2_new": 0,
            "pool_changed": False,
            "base_unchanged": {"union": n_existing, "reps": base_ded["cluster_count"]},
            "sentinel_memo": memo,
        }
        (DRIVERS / "v03_r3b_reuse_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("WROTE v03_r3b_reuse_summary.json (no pool change)", flush=True)
        return

    skipped = []
    new_live = [_u3.rebuild(r, skipped) for r in new_raw]
    new_live = [d for d in new_live if d is not None]
    print(f"REBUILT new={len(new_live)} skipped={len(skipped)}", flush=True)

    async def run_hydrate():
        from scholar_search.enrichment import AbstractHydrator
        from scholar_search.http_client import AcademicHttpClient

        c = AcademicHttpClient(name="r3b-hydrator", rate_limit=1.0)
        h = AbstractHydrator(c)
        out, stats = await hydrate_isolated(h, new_live)
        try:
            await c.close()
        except Exception:  # noqa: BLE001
            pass
        return out, stats

    new_h, hstats = asyncio.run(run_hydrate())
    print(
        f"HYDRATION-NEW attempted={hstats.get('attempted')} hydrated={hstats.get('hydrated')} failed={hstats.get('failed')}",
        flush=True,
    )

    existing_h_live = []
    skipped2 = []
    for d in hyd["documents"]:
        got = _u3.rebuild(d, skipped2)
        if got is not None:
            existing_h_live.append(got)
    pool = existing_h_live + list(new_h)
    print(
        f"POOL: existing_hydrated={len(existing_h_live)} new={len(new_h)} total={len(pool)}",
        flush=True,
    )

    # PRE-dedup snapshot FIRST: Deduplicator._merge_metadata mutates
    # representative documents IN PLACE (longer abstracts, merged PIDs and
    # sources) during clustering. Writing the pool after dedup (r3b pass-1
    # defect) captured post-mutation state under a pre-dedup filename —
    # 17 member records showed representative-enriched abstracts and the
    # coverage count drifted +7. The union snapshot must reflect the pool
    # exactly as dedup received it.
    pool_docs_pre = [ser(d) for d in pool]
    cov_pre = sum(1 for d in pool if (str(getattr(d, "abstract", "") or "")).strip())

    from scholar_search.dedup import Deduplicator

    ded = Deduplicator()
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
    reps = [_u3.ser_doc(c.representative) for c in clusters]

    (CAL / f"v03_r3b_{DATE_TAG}_s2_reuse.json").write_text(
        json.dumps(
            {
                "leg_label": LEG_LABEL,
                "leg_note": LEG_NOTE,
                "source_file": SRC_FILE,
                "s2_fetched_leg": len(s2_docs),
                "s2_new_in_r3b": len(new_raw),
                "s2_dropped_as_base_duplicates": len(s2_docs) - len(new_raw),
                "documents": new_raw,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (CAL / f"v03_r3b_{DATE_TAG}_union_hydrated.json").write_text(
        json.dumps(
            {
                "base_hydrated": f"v03_r3_{DATE_TAG}_union_hydrated.json",
                "base_union_raw": f"v03_r3_{DATE_TAG}_union_raw.json",
                "leg_labels": [
                    "openalex-full(r3)",
                    "crossref-full(r3)",
                    "arxiv-full(r3)",
                    "pubmed(r3)",
                    LEG_LABEL,
                ],
                "hydration_stats_r3b": hstats,
                "union_count_r3b": len(pool),
                "documents": pool_docs_pre,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (CAL / f"v03_r3b_{DATE_TAG}_deduped.json").write_text(
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
    memo = sentinel_memo(reps, CAL / f"v03_r3b_{DATE_TAG}_sentinel_memo.md")
    summary = {
        "leg_label": LEG_LABEL,
        "leg_note": LEG_NOTE,
        "s2_total": len(s2_docs),
        "s2_new_in_r3b": len(new_raw),
        "s2_dropped_as_base_duplicates": len(s2_docs) - len(new_raw),
        "researcher_hypothesis_126dups": [k for k in researcher_hypothesis.items()],
        "pool": {
            "pool_r3b": len(pool),
            "with_abstract": cov_pre,
            "coverage_basis": "pre-dedup snapshot (mutation-safe)",
            "new_hydrated": hstats.get("hydrated"),
            "new_attempted": hstats.get("attempted"),
        },
        "dedup_r3b": {
            "stats": stats,
            "clusters": len(clusters),
            "singletons": singletons,
            "error": derr,
        },
        "sentinel_memo": memo,
    }
    (DRIVERS / "v03_r3b_reuse_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE r3b files + summary", flush=True)


if __name__ == "__main__":
    main_sync()
