# -*- coding: utf-8 -*-
"""
SCR1 yield/coverage follow-ups (Tier A #1 and #4, Tier C #11):
1. include-lean + pending-yield per query_id (dead-query ranking);
4. per-provider year coverage curves (records vs includes);
11. cap-ablation replay over Crossref queries (file-order rank proxy).

Output: calibration_v03/v03_scr1_yield_investigation.json (NEW).
Assumption (documented in output): for #11, retrieval rank within a query is
proxied by record order in the deduped corpus (query blocks are contiguous);
original provider-side ranking was not retained by the dedup layer.
"""

import json
import pathlib
from collections import Counter, defaultdict

CAL = pathlib.Path(__file__).resolve().parents[1] / "calibration_v03"
DEC = CAL / "screening_scr1" / "decisions"


def main():
    ded = json.loads(
        (CAL / "v03_r3e_20261017_deduped.json").read_text(encoding="utf-8-sig")
    )
    docs = ded["documents"]
    doc = lambda sid: docs[int(sid.split("-")[1]) - 1]

    fam = defaultdict(dict)
    for df in sorted(DEC.glob("*.json")):
        x = json.loads(df.read_text(encoding="utf-8-sig"))
        f = str(x.get("screener_id") or "").upper()
        if f not in ("A1", "A2"):
            f = "A1" if "A1" in df.name else "A2"
        for r in x.get("decisions") or []:
            if r.get("screening_id") and r.get("decision"):
                fam[r["screening_id"]][f] = r["decision"]
    inc = [s for s, f in fam.items() if f.get("A1") == f.get("A2") == "INCLUDE"]
    pen = [s for s, f in fam.items() if f.get("A1") == f.get("A2") == "PENDING"]

    # ---- #1: per-query yield ------------------------------------------------
    # all corpus records (any family label) grouped by query_id
    by_q = defaultdict(list)
    for i, d in enumerate(docs):
        by_q[str(d.get("query_id"))].append(i)
    qstats = {}
    for q, idxs in by_q.items():
        sids_q = {i: f"SCI-{i + 1:06d}" for i in idxs}
        n = len(idxs)
        n_inc = sum(
            1
            for i in idxs
            if sids_q[i] in fam
            and fam[sids_q[i]].get("A1") == fam[sids_q[i]].get("A2") == "INCLUDE"
        )
        n_pen = sum(
            1
            for i in idxs
            if sids_q[i] in fam
            and fam[sids_q[i]].get("A1") == fam[sids_q[i]].get("A2") == "PENDING"
        )
        providers = Counter(docs[i].get("provider") for i in idxs)
        qstats[q] = {
            "records": n,
            "include_lean": n_inc,
            "pending_lean": n_pen,
            "include_per_1k": round(1000 * n_inc / n, 2) if n else 0.0,
            "providers": dict(providers.most_common(3)),
        }
    ranked = sorted(
        qstats.items(), key=lambda kv: (-kv[1]["include_lean"], kv[1]["include_per_1k"])
    )

    # ---- #4: year curves ----------------------------------------------------
    def year_curve(sids_label, provider):
        rec = Counter()
        incs = Counter()
        target = set(sids_label)
        for i, d in enumerate(docs):
            if d.get("provider") != provider:
                continue
            sid = f"SCI-{i + 1:06d}"
            rec[str(d.get("year"))] += 1
            if sid in fam and fam[sid].get("A1") == fam[sid].get("A2") == "INCLUDE":
                incs[str(d.get("year"))] += 1
        return {
            "records_by_year": dict(sorted(rec.items())),
            "includes_by_year": dict(sorted(incs.items())),
            "include_per_1k_by_year": {
                y: round(1000 * incs.get(y, 0) / rec[y], 1) for y in sorted(rec)
            },
        }

    # ---- #11: cap ablation replay (crossref queries) -------------------------
    # within-query file-order rank proxy; N = first-N per query group
    cr_inc_q = defaultdict(
        list
    )  # query_id -> [rank positions of crossref-labeled includes]
    cr_by_q = defaultdict(list)
    for i, d in enumerate(docs):
        if d.get("provider") != "crossref":
            continue
        q = str(d.get("query_id"))
        cr_by_q[q].append(i)
        sid = f"SCI-{i + 1:06d}"
        if sid in fam and fam[sid].get("A1") == fam[sid].get("A2") == "INCLUDE":
            cr_inc_q[q].append(i)
    caps = {}
    for N in (100, 250, 500, 1000, None):
        kept = 0
        inc_alive = 0
        for q, idxs in cr_by_q.items():
            sub = idxs if N is None else idxs[:N]
            kept += len(sub)
            incset = set(cr_inc_q.get(q, []))
            inc_alive += sum(1 for i in sub if i in incset)
        caps["inf" if N is None else str(N)] = {
            "crossref_records_kept": kept,
            "crossref_unique_includes_alive": inc_alive,
            "recall_pct_of_69": round(
                100 * inc_alive / max(1, sum(len(v) for v in cr_inc_q.values())), 1
            ),
        }
    cr_total = sum(len(v) for v in cr_by_q.values())

    out = {
        "investigation": "SCR1_query_yield_year_curves_cap_replay",
        "n_includes": len(inc),
        "n_pending": len(pen),
        "query_yield_ranked": [{"query_id": q, **s} for q, s in ranked],
        "query_count": len(by_q),
        "year_curves": {
            "crossref": year_curve([], "crossref"),
            "openalex": year_curve([], "openalex"),
        },
        "cap_replay_crossref": {
            "crossref_records_total": cr_total,
            "crossref_unique_includes_total": sum(len(v) for v in cr_inc_q.values()),
            "rank_proxy": "deduped file order within query_id (blocks contiguous); NOT original provider rank",
            "caps": caps,
        },
    }
    outpath = CAL / "v03_scr1_yield_investigation.json"
    outpath.write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print("== #1 query yield (ranked by include-lean) ==")
    for e in ranked[:12]:
        q, s = e
        print(
            f"  {q:34s} recs={s['records']:5d} inc={s['include_lean']:3d} "
            f"pend={s['pending_lean']:3d} inc/1k={s['include_per_1k']:7.2f}"
        )
    dead = [e for e in ranked if e[1]["include_lean"] == 0][:10]
    print("  zero-include queries:", [e[0] for e in dead])
    print("== #4 year curves ==")
    for prov in ("crossref", "openalex"):
        yc = out["year_curves"][prov]
        print(f"  {prov}: inc/1k by year:", yc["include_per_1k_by_year"])
    print("== #11 cap replay (crossref) ==")
    for k, v in caps.items():
        print(
            f"  cap={k:5s} kept={v['crossref_records_kept']:6d} "
            f"uniqIncAlive={v['crossref_unique_includes_alive']:3d} "
            f"({v['recall_pct_of_69']}% of 69)"
        )
    print("written ->", outpath)


if __name__ == "__main__":
    main()
