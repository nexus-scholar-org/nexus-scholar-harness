"""R3C — Crossref year-partitioned sweep (researcher authorization).

Splits the UNCHANGED 27-term protocol boolean over the same Crossref leg into
disjoint publication-year partitions 2020..2026 (same query string, same kit
provider semantics, same from/until-pub-date filters as the full-range leg).
Each partition must land under the 1000-row cap for the sweep to be COMPLETE;
any year hitting the cap is labelled HONESTLY in the manifest (not silently).

Outputs (all v03_r3c_* NEW files; nothing overwritten):
  - v03_r3c_20261017_crossref_year_sweep.json  (per-year meta/fetch/dup/new stats + docs)
  - v03_r3c_20261017_union_hydrated.json       (PRE-dedup pool snapshot, mutation-safe)
  - v03_r3c_20261017_deduped.json              (full dedup of r3b pool + new crossref)
  - v03_r3c_20261017_sentinel_memo.md
  - _drivers/v03_r3c_sweep_summary.json

Discipline: strictly keyed=no (assert), no other round's artifacts touched,
dedup mutation-safe ordering (snapshot before dedup — r3b lesson).
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
YEARS = list(range(2020, 2027))
PER_YEAR_CAP = 1000
SESSION = "UAV-HARVEST-R3C-20261017"

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
    q0 = Query(text=QUERY, id=SESSION, year_min=2020, year_max=2026)
    translated_full = cr.translator.translate(q0)

    per_year = []
    all_docs = []
    t0 = time.perf_counter()
    for y in YEARS:
        qy = Query(
            text=QUERY,
            id=f"{SESSION}-Y{y}",
            year_min=y,
            year_max=y,
            language="en",
            max_results=PER_YEAR_CAP,
        )
        translated = cr.translator.translate(qy)
        # Meta probe: same query + same year filter, rows=1, read total-results.
        params = {
            "query": translated,
            "rows": 1,
            "filter": f"from-pub-date:{y}-01-01,until-pub-date:{y}-12-31",
        }
        meta_resp = await cr.client.get(cr.base_url, params=params)
        meta = meta_resp.json().get("message", {})
        total = meta.get("total-results")

        docs_y = []
        status = "SUCCESS"
        error = None
        try:

            async def fetch_n():
                n = 0
                async for d in cr.search(qy):
                    docs_y.append(d)
                    n += 1
                    if n == 1 or n % 100 == 0:
                        print(f"[r3c-crossref Y{y}] {n} records", flush=True)

            await asyncio.wait_for(fetch_n(), timeout=240)
        except asyncio.TimeoutError:
            status, error = "PARTIAL_TIMEOUT", "watchdog 240s; partial kept"
        except Exception as ex:  # noqa: BLE001
            status, error = "PARTIAL", f"{type(ex).__name__}: {str(ex)[:200]}"
        cap_bound = len(docs_y) >= PER_YEAR_CAP
        per_year.append(
            {
                "year": y,
                "universe_total": total,
                "fetched": len(docs_y),
                "cap": PER_YEAR_CAP,
                "cap_bound": cap_bound,
                "status": status,
                "error": error,
            }
        )
        all_docs.extend(docs_y)
        print(
            f"[r3c-crossref Y{y}] universe={total} fetched={len(docs_y)} "
            f"cap_bound={cap_bound} status={status}",
            flush=True,
        )
    await cr.client.close()
    wall = round(time.perf_counter() - t0, 2)
    return per_year, all_docs, translated_full, wall


def main_sync():
    if os.environ.get("SCHOLAR_S2_KEY") is not None:
        raise SystemExit(
            "ABORT: SCHOLAR_S2_KEY visible in this process; r3c runs strictly "
            "keyless. Launch with the variable removed."
        )

    qtext = uqt.build_protocol_boolean_query(
        ROOT / "workspaces" / "uav-crop-weed-v03" / "protocol.json"
    )
    r3b_pool = json.loads(
        (CAL / f"v03_r3b_{DATE_TAG}_union_hydrated.json").read_text(encoding="utf-8")
    )
    r3b_ded = json.loads(
        (CAL / f"v03_r3b_{DATE_TAG}_deduped.json").read_text(encoding="utf-8")
    )
    existing = r3b_pool["documents"]
    print(
        f"BASE r3b pool: {len(existing)} records (dedup reps {r3b_ded['cluster_count']})",
        flush=True,
    )

    per_year, sweep_docs, translated_full, wall = asyncio.run(run_sweep(qtext))
    sweep_dicts = [ser(d) for d in sweep_docs]
    total_fetched = len(sweep_docs)
    print(
        f"SWEEP: fetched={total_fetched} across {len(YEARS)} years wall={wall}s",
        flush=True,
    )

    # New-record detection (PID overlap OR title+year signature) against the
    # ENTIRE r3b pool (not just representatives): anything matching any pool
    # member is a duplicate by definition.
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
        f"NEW-DETECTION: sweep={len(sweep_docs)} new={len(new_raw)} dup-against-pool={len(sweep_docs) - len(new_raw)}",
        flush=True,
    )

    skipped = []
    new_live = [d for d in (_u3.rebuild(r, skipped) for r in new_raw) if d is not None]
    print(f"REBUILT new={len(new_live)} skipped={len(skipped)}", flush=True)

    async def run_hydrate():
        from scholar_search.enrichment import AbstractHydrator
        from scholar_search.http_client import AcademicHttpClient

        c = AcademicHttpClient(name="r3c-hydrator", rate_limit=1.0)
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

    # MUTATION-SAFE: snapshot the pool BEFORE dedup (r3b lesson).
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

    (CAL / f"v03_r3c_{DATE_TAG}_crossref_year_sweep.json").write_text(
        json.dumps(
            {
                "session": SESSION,
                "partition_strategy": "crossref_year_sweep_2020_2026",
                "protocol_boolean_unchanged": True,
                "search_implementation": "patched_post-L1L6+r2fixes+pubmednorm+stemlex",
                "executed_query": qtext,
                "translated_full_range_reference": translated_full,
                "per_year": per_year,
                "sweep_total_fetched": total_fetched,
                "cap_bound_years": [p["year"] for p in per_year if p["cap_bound"]],
                "documents": sweep_dicts,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (CAL / f"v03_r3c_{DATE_TAG}_union_hydrated.json").write_text(
        json.dumps(
            {
                "base_pool": f"v03_r3b_{DATE_TAG}_union_hydrated.json",
                "leg_labels": [
                    *(r3b_pool.get("leg_labels") or []),
                    "crossref-year-sweep(r3c)",
                ],
                "hydration_stats_r3c": hstats,
                "union_count_r3c": len(pool),
                "documents": pool_docs_pre,
            },
            default=str,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (CAL / f"v03_r3c_{DATE_TAG}_deduped.json").write_text(
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
    # Sentinel memo
    out = ["# r3c sentinel memo (pool after crossref year sweep)\n"]
    hits = 0
    for sid, doi, ax in SEEDS:
        dl = doi.lower()
        blobs = [str(d.get("external_ids") or "").lower() for d in reps]
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
    (CAL / f"v03_r3c_{DATE_TAG}_sentinel_memo.md").write_text(
        "\n".join(out), encoding="utf-8"
    )

    summary = {
        "session": SESSION,
        "partition_strategy": "crossref_year_sweep_2020_2026",
        "per_year": per_year,
        "sweep_total_fetched": total_fetched,
        "sweep_new_in_r3c": len(new_raw),
        "sweep_dropped_as_pool_duplicates": len(sweep_docs) - len(new_raw),
        "wall_seconds": wall,
        "pool": {
            "pool_r3c": len(pool),
            "with_abstract_pre_dedup": cov_pre,
            "coverage_basis": "pre-dedup snapshot (mutation-safe)",
            "new_hydrated": hstats.get("hydrated"),
            "new_attempted": hstats.get("attempted"),
            "new_failed": hstats.get("failed"),
        },
        "dedup_r3c": {
            "stats": stats,
            "clusters": len(clusters),
            "singletons": singletons,
            "error": derr,
        },
        "sentinel": {"tier1_hits": hits, "of": 7},
    }
    (DRIVERS / "v03_r3c_sweep_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("WROTE r3c files + summary", flush=True)


if __name__ == "__main__":
    main_sync()
