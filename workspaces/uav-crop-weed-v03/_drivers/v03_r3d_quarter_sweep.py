"""R3D — Crossref quarterly completion sweep (researcher authorization).

Completes the Crossref leg from r3c's ~58% coverage by partitioning every
2020–2026 year into Q1–Q4 (28 disjoin partitions expected per-queart << cap;
any cap-bound partition is labelled honestly for further subdivision).

Harness-level composition, kit untouched:
  - same kit CrossrefProvider + the SAME translated query it emits;
  - the partition filter is built EXPLICITLY in the driver (the kit's
    search() only supports year granularity — using it here would silently
    re-fetch whole years, so the fetch composes params + kit
    _normalize_document at the research layer instead);
  - one call per quarter (total-results + items in the same response).

Base pool for duplicate detection = r3c pre-dedup pool (8,382 records).
Outputs all v03_r3c/r3d-prefixed NEW files; nothing overwritten.
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

import uav_query_translator as uqt

DATE_TAG = "20261017"
SESSION = "UAV-HARVEST-R3D-20261017"
ROWS = 1000

QUARTERS = {
    1: ("01-01", "03-31"),
    2: ("04-01", "06-30"),
    3: ("07-01", "09-30"),
    4: ("10-01", "12-31"),
}

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


async def run_sweep(QUERY):
    from scholar_search.models import Query
    from scholar_search.providers import CrossrefProvider

    cr = CrossrefProvider()
    q_ref = Query(text=QUERY, id=SESSION, year_min=2020, year_max=2026)
    translated = cr.translator.translate(q_ref)

    per_part = []
    items_all = []
    t0 = time.perf_counter()
    failed_calls = 0
    for y in range(2020, 2027):
        y_items = 0
        for qn, (qs, qe) in QUARTERS.items():
            fl = f"from-pub-date:{y}-{qs},until-pub-date:{y}-{qe}"
            params = {"query": translated, "rows": ROWS, "filter": fl}
            status = "SUCCESS"
            error = None
            try:
                resp = await asyncio.wait_for(
                    cr.client.get(cr.base_url, params=params), timeout=120
                )
                msg = resp.json().get("message", {})
                items = msg.get("items", [])
                total = msg.get("total-results")
            except Exception as ex:  # noqa: BLE001
                items, total = [], None
                status = "PARTIAL"
                error = f"{type(ex).__name__}: {str(ex)[:160]}"
                failed_calls += 1
            docs = [cr._normalize_document(it, f"{SESSION}-Y{y}Q{qn}") for it in items]
            y_items += len(docs)
            items_all.extend(docs)
            cap_bound = len(items) >= ROWS
            per_part.append(
                {
                    "year": y,
                    "quarter": qn,
                    "filter": fl,
                    "universe_total": total,
                    "fetched": len(docs),
                    "cap": ROWS,
                    "cap_bound": cap_bound,
                    "status": status,
                    "error": error,
                }
            )
            print(
                f"[r3d Y{y}Q{qn}] universe={total} fetched={len(docs)} status={status}",
                flush=True,
            )
    await cr.client.close()
    wall = round(time.perf_counter() - t0, 2)
    return per_part, items_all, translated, wall, failed_calls


def main_sync():
    if os.environ.get("SCHOLAR_S2_KEY") is not None:
        raise SystemExit(
            "ABORT: SCHOLAR_S2_KEY visible in this process; r3c runs strictly "
            "keyless. Launch with the variable removed."
        )

    qtext = uqt.build_protocol_boolean_query(
        ROOT / "workspaces" / "uav-crop-weed-v03" / "protocol.json"
    )
    base_pool = json.loads(
        (CAL / f"v03_r3c_{DATE_TAG}_union_hydrated.json").read_text(encoding="utf-8")
    )
    base_ded = json.loads(
        (CAL / f"v03_r3c_{DATE_TAG}_deduped.json").read_text(encoding="utf-8")
    )
    existing = base_pool["documents"]
    print(
        f"BASE r3c pool: {len(existing)} records (dedup reps {base_ded['cluster_count']})",
        flush=True,
    )

    per_part, sweep_docs, translated, wall, failed_calls = asyncio.run(run_sweep(qtext))
    sweep_dicts = [ser(d) for d in sweep_docs]
    total_fetched = len(sweep_docs)
    cap_bound_parts = [p for p in per_part if p["cap_bound"]]
    universe_sum = sum(p["universe_total"] or 0 for p in per_part)
    fetched_of_known = sum(p["fetched"] for p in per_part if p["universe_total"])
    print(
        f"SWEEP: partitions={len(per_part)} fetched={total_fetched} "
        f"universe_sum={universe_sum} cap_bound={len(cap_bound_parts)} failed_calls={failed_calls}",
        flush=True,
    )

    # Completion verdict: every partition SUCCESS + not cap-bound => leg complete.
    leg_complete = (failed_calls == 0) and (not cap_bound_parts)

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

    new_raw = [d for d in sweep_dicts if is_new(d)]
    print(
        f"NEW-DETECTION: sweep={len(sweep_dicts)} new={len(new_raw)} dup={len(sweep_dicts) - len(new_raw)}",
        flush=True,
    )

    if not new_raw:
        summary = {
            "session": SESSION,
            "partition_strategy": "crossref_quarter_sweep_2020_2026",
            "per_part": per_part,
            "sweep_total_fetched": total_fetched,
            "universe_sum": universe_sum,
            "crossref_leg_complete": leg_complete,
            "sweep_new_in_r3d": 0,
            "pool_unchanged": {
                "pool": len(existing),
                "reps": base_ded["cluster_count"],
            },
            "sentinel": {
                "tier1_hits": 7,
                "of": 7,
                "note": "borrowed check on r3c pool (unchanged)",
            },
        }
        (DRIVERS / "v03_r3d_quarter_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("NO new records; pool unchanged; wrote summary", flush=True)
        return

    skipped = []
    new_live = [d for d in (_u3.rebuild(r, skipped) for r in new_raw) if d is not None]
    new_live = [d for d in new_live if d is not None]
    print(f"REBUILT new={len(new_live)} skipped={len(skipped)}", flush=True)

    async def run_hydrate():
        from scholar_search.enrichment import AbstractHydrator
        from scholar_search.http_client import AcademicHttpClient

        c = AcademicHttpClient(name="r3d-hydrator", rate_limit=1.0)
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
    for d in existing:
        got = _u3.rebuild(d, skipped2)
        if got is not None:
            existing_h_live.append(got)
    pool = existing_h_live + list(new_h)
    print(
        f"POOL: existing={len(existing_h_live)} new={len(new_h)} total={len(pool)}",
        flush=True,
    )

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

    (CAL / f"v03_r3d_{DATE_TAG}_crossref_quarter_sweep.json").write_text(
        json.dumps(
            {
                "session": SESSION,
                "partition_strategy": "crossref_quarter_sweep_2020_2026",
                "search_implementation": "patched_post-L1L6+r2fixes+pubmednorm+stemlex",
                "protocol_boolean_unchanged": True,
                "executed_query": qtext,
                "translated_reference": translated,
                "per_part": per_part,
                "sweep_total_fetched": total_fetched,
                "universe_sum": universe_sum,
                "cap_bound_partitions": [
                    f"Y{p['year']}Q{p['quarter']}" for p in cap_bound_parts
                ],
                "failed_calls": failed_calls,
                "crossref_leg_complete_after_this_round": leg_complete,
                "documents": sweep_dicts,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (CAL / f"v03_r3d_{DATE_TAG}_union_hydrated.json").write_text(
        json.dumps(
            {
                "base_pool": f"v03_r3c_{DATE_TAG}_union_hydrated.json",
                "leg_labels": [
                    *(base_pool.get("leg_labels") or []),
                    "crossref-quarter-sweep(r3d, completion)",
                ],
                "hydration_stats_r3d": hstats,
                "union_count_r3d": len(pool),
                "documents": pool_docs_pre,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (CAL / f"v03_r3d_{DATE_TAG}_deduped.json").write_text(
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

    blobs = [str(d.get("external_ids") or "").lower() for d in reps]
    out = ["# r3d sentinel memo (pool after crossref quarter completion)\n"]
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
            f"- {sid}: {'HIT' if ok else 'MISS'} ({'doi-exact' if doi_hits else 'arxiv_id' if ax_hits else 'none'}) {sci}"
        )
    out.append(f"\nTier-1 PID: {hits}/7")
    (CAL / f"v03_r3d_{DATE_TAG}_sentinel_memo.md").write_text(
        "\n".join(out), encoding="utf-8"
    )

    summary = {
        "session": SESSION,
        "partition_strategy": "crossref_quarter_sweep_2020_2026",
        "per_part": per_part,
        "sweep_total_fetched": total_fetched,
        "universe_sum": universe_sum,
        "cap_bound_partitions": [
            f"Y{p['year']}Q{p['quarter']}" for p in cap_bound_parts
        ],
        "failed_calls": failed_calls,
        "crossref_leg_complete_after_this_round": leg_complete,
        "sweep_new_in_r3d": len(new_raw),
        "sweep_dropped_as_pool_duplicates": len(sweep_dicts) - len(new_raw),
        "wall_seconds": wall,
        "pool": {
            "pool_r3d": len(pool),
            "with_abstract_pre_dedup": cov_pre,
            "coverage_basis": "pre-dedup snapshot (mutation-safe)",
            "new_hydrated": hstats.get("hydrated"),
            "new_attempted": hstats.get("attempted"),
            "new_failed": hstats.get("failed"),
        },
        "dedup_r3d": {
            "stats": stats,
            "clusters": len(clusters),
            "singletons": singletons,
            "error": derr,
        },
        "sentinel": {"tier1_hits": hits, "of": 7},
    }
    (DRIVERS / "v03_r3d_quarter_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE r3d files + summary", flush=True)


if __name__ == "__main__":
    main_sync()
