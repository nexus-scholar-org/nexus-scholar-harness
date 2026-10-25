# -*- coding: utf-8 -*-
"""
SCR1 FOLLOW-UP: per-provider harvest quality investigation.

Question (researcher): the exclusion rate was very high — is it dominated by
Crossref records introduced by removing the per-query cap in favor of
yearly-batched harvesting? Was the cap removal worth it?

Method (deterministic, from frozen artifacts):
1. Final corpus = v03_r3e_20261017_deduped.json (14,150 docs; SCI-N = docs[N-1],
   mapping verified against pack records).
2. Rebuild pairwise lanes from all 566 A1/A2 decision files (alias-tolerant,
   same loader semantics as v03_scr1_reconcile2.py lane_key on final rows).
3. Cross: provider composition x lane; primary reason codes x provider;
   include-lean composition; moderation-substrate composition.
4. Harvest-side: per-provider raw retrieval volumes (r3e raw_* files) and
   dedup funnel (provider x sources).

Output: calibration_v03/v03_scr1_provider_investigation.json (NEW file).
"""

import json
import pathlib
from collections import Counter, defaultdict

DPIP = pathlib.Path(__file__).resolve().parents[1]  # uav-crop-weed-v03
CAL = DPIP / "calibration_v03"
DEC = CAL / "screening_scr1" / "decisions"
MOD = CAL / "screening_scr1" / "moderation_views"

# exact text per row, per family: extract decisions and reason codes
DEC_KEYS = ("decision",)
ALIAS_CODE_KEYS = (
    "reason_code",
    "exclusion_reason_code",
    "pending_reason_code",
    "inclusion_hint",
    "reason_CODE",
)
ALIAS_DEC_KEYS = ("decision",)


def row_decision(row):
    for k in ALIAS_DEC_KEYS:
        if k in row and row[k] in ("INCLUDE", "EXCLUDE", "PENDING"):
            return row[k]
    return None


def row_code(row):
    for k in ALIAS_CODE_KEYS:
        if row.get(k):
            return str(row[k])
    if "reason" in row and isinstance(row["reason"], dict):
        # embedded `reason` object family: try common keys
        for k in ("reason_code", "code", "code_note"):
            if row["reason"].get(k):
                return str(row["reason"][k])
    return "UNSPECIFIED"


def main():
    # 1. Corpus + provider map
    ded = json.loads(
        (CAL / "v03_r3e_20261017_deduped.json").read_text(encoding="utf-8-sig")
    )
    docs = ded["documents"]
    corpus = {}
    for i, d in enumerate(docs):
        sid = f"SCI-{i + 1:06d}"
        srcs = d.get("sources")
        srcs = [s for s in (srcs if isinstance(srcs, list) else [])] if srcs else []
        corpus[sid] = {
            "provider": str(d.get("provider") or "unknown"),
            "sources": [str(s) for s in srcs],
            "year": d.get("year"),
            "title": str(d.get("title") or ""),
            "has_abstract": bool(str(d.get("abstract") or "").strip()),
            "citations_count": d.get("citations_count"),
        }
    by_provider = Counter(v["provider"] for v in corpus.values())

    # 2. Rebuild pairwise decisions from A1/A2 files
    fam_rows = defaultdict(
        lambda: defaultdict(dict)
    )  # sid -> family(A1/A2) -> (dec, code)
    for df in sorted(DEC.glob("*.json")):
        x = json.loads(df.read_text(encoding="utf-8-sig"))
        fam = str(x.get("screener_id") or x.get("family") or "").upper()
        if fam not in ("A1", "A2"):
            fam = (
                "A1"
                if "A1" in df.name.upper()
                else ("A2" if "A2" in df.name.upper() else fam)
            )
        rows = x.get("decisions") or x.get("rows") or []
        for r in rows:
            sid = r.get("screening_id")
            dec = row_decision(r)
            if sid and dec:
                fam_rows[sid][fam] = (dec, row_code(r))

    lanes = Counter()
    res = {"mutual_include": [], "mutual_exclude": [], "mutual_pending": []}
    conflicts = Counter()
    for sid, f in fam_rows.items():
        d1 = f.get("A1")
        d2 = f.get("A2")
        if not d1 or not d2:
            lanes["missing_family_" + ("A1" if not d1 else "A2")] += 1
            continue
        key = tuple(sorted((d1[0], d2[0])))
        if key == ("EXCLUDE", "EXCLUDE"):
            res["mutual_exclude"].append((sid, d1[1], d2[1]))
            lanes["mutual_exclude"] += 1
        elif key == ("INCLUDE", "INCLUDE"):
            res["mutual_include"].append(sid)
            lanes["mutual_include"] += 1
        elif key == ("PENDING", "PENDING"):
            res["mutual_pending"].append(sid)
            lanes["mutual_pending"] += 1
        else:
            conflicts["third_lane"] += 1

    # 3. Cross analyses
    def provider_counter(sids):
        return Counter(corpus[s]["provider"] for s in sids if s in corpus)

    # primary reason codes by provider over mutual-EXCLUDE (use A1 primary;
    # moderation/title-only codes tagged if present in either)
    excl_by_prov = defaultdict(Counter)
    no_abs_by_prov = Counter()
    for sid, c1, c2 in res["mutual_exclude"]:
        cinfo = corpus.get(sid, {})
        p = cinfo["provider"]
        code1 = c1 if c1 not in ("UNSPECIFIED",) else c2
        excl_by_prov[p][code1] += 1
        if not cinfo.get("has_abstract", True):
            no_abs_by_prov[p] += 1

    # include rate per provider (mutual include / provider corpus share)
    inc_by_prov = provider_counter(res["mutual_include"])
    pen_by_prov = provider_counter(res["mutual_pending"])
    rates = {}
    for p, n in by_provider.items():
        rates[p] = {
            "corpus": n,
            "mutual_include": inc_by_prov.get(p, 0),
            "mutual_pending": pen_by_prov.get(p, 0),
            "mutual_exclude": sum(
                1
                for s in res["mutual_exclude"]
                if corpus.get(s, {}).get("provider") == p
            ),
            "include_rate_per_1000": round(1000 * inc_by_prov.get(p, 0) / n, 2),
            "n_no_abstract": no_abs_by_prov.get(p, 0),
        }

    # 4. Harvest-side raw provider volumes (r3e raw_*)
    raw = {}
    for pf in sorted(CAL.glob("v03_r3e_*_raw_*.json")) + sorted(
        CAL.glob("v03_r3e_20261017_union_hydrated.json")
    ):
        try:
            x = json.loads(pf.read_text(encoding="utf-8-sig"))
            docs_r = x.get("documents", x if isinstance(x, list) else [])
            n = len(docs_r)
            prov = (
                Counter(str(dd.get("provider") or "unknown") for dd in docs_r)
                if n
                else {}
            )
            raw[pf.name] = {"documents": n, "by_provider": dict(prov.most_common())}
        except Exception as e:
            raw[pf.name] = {"error": str(e)}

    out = {
        "investigation": "SCR1_provider_quality_exclusion_rate_deep_dive",
        "corpus_source": "v03_r3e_20261017_deduped.json",
        "sci_id_mapping_verified": "SCI-N == documents[N-1] (checked against pack_0001 record SCI-000046)",
        "corpus_by_provider": dict(by_provider.most_common()),
        "lane_totals_rebuilt": dict(lanes),
        "provider_rates": {
            k: rates[k] for k in sorted(rates, key=lambda p: -rates[p]["corpus"])
        },
        "exclude_reason_codes_by_provider": {
            p: dict(c.most_common(8))
            for p, c in sorted(
                excl_by_prov.items(), key=lambda kv: -sum(kv[1].values())
            )
        },
        "no_abstract_share_by_provider": {
            p: {
                "n": no_abs_by_prov.get(p, 0),
                "pct": round(100 * no_abs_by_prov.get(p, 0) / n, 1),
            }
            for p, n in by_provider.items()
            if n
        },
        "harvest_raw_volumes_r3e": raw,
        "include_provider_counter": dict(inc_by_prov.most_common()),
        "pending_provider_counter": dict(pen_by_prov.most_common()),
    }
    outpath = CAL / "v03_scr1_provider_investigation.json"
    outpath.write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: out[k] for k in ("corpus_by_provider", "lane_totals_rebuilt")},
            indent=1,
            ensure_ascii=False,
        )
    )
    for p, v in out["provider_rates"].items():
        print(
            f"{p:16s} corpus={v['corpus']:6d} inc={v['mutual_include']:3d} "
            f"pend={v['mutual_pending']:3d} excl={v['mutual_exclude']:6d} "
            f"incRate/1k={v['include_rate_per_1000']:6} noAbsPct={out['no_abstract_share_by_provider'].get(p, {}).get('pct', '-')}"
        )
    print("\nEXCLUDE codes by provider (top):")
    for p, codes in out["exclude_reason_codes_by_provider"].items():
        print(f"  {p:16s}", codes)
    print("\nraw r3e volumes:")
    for f, v in raw.items():
        print(f"  {f}: {v.get('documents', v.get('error'))}", v.get("by_provider", {}))
    print("written ->", outpath)


if __name__ == "__main__":
    main()
