# -*- coding: utf-8 -*-
"""
SCR1 follow-ups #14 (WRONG_TASK taxonomy over Crossref exclusions) and
#2 (citation-gap: are the 69 crossref-unique includes low-citation diamonds
or missing classics?).

Outputs NEW files only:
- calibration_v03/v03_scr1_wrongtask_taxonomy.json
- calibration_v03/v03_scr1_citation_gap.json
"""

import json
import pathlib
import re
from collections import Counter, defaultdict

CAL = pathlib.Path(__file__).resolve().parents[1] / "calibration_v03"
DEC = CAL / "screening_scr1" / "decisions"

BUCKETS = [
    (
        "navigation_autonomy",
        r"navigat|path plan|trajectory|slam|obstacle|autonomous flight|waypoint|guidance|attitude control|position control|formation",
    ),
    (
        "communications_network",
        r"communicat|network|5g|6g|iot|internet of things|telemetry|routing|edge comput|federated|blockchain|security|privacy|authenticat|intrusion|cyber",
    ),
    (
        "power_propulsion_hardware",
        r"propuls|motor|rotor|battery|fuel cell|energy|noise|vibration|aeroelastic|design of|aerodynamic|materials|structure|antenna|radar hardware|lidar sensor|vtol|fixed-wing aircraft desig",
    ),
    (
        "inspection_infrastructure",
        r"inspect|bridge|concrete|crack|pavement|railway|power line|wind turbine|dam|pipeline|construction|monitor of structur",
    ),
    (
        "military_security",
        r"milita|combat|swarm attack|defense|counter-?uav|drone detection of uavs|antis |jamming|surveillance of border|weapon",
    ),
    (
        "enviro_nature_beyond_ag",
        r"wildlife|forest|tree species|fire|wetland|marine|ocean|river|glacier|landslide|geodetic|seismic|aquatic|coral|biodiversity (?!of crop)",
    ),
    ("delivery_logistics", r"deliver|logistic|transport of|package|parcel"),
    (
        "traffic_people",
        r"traffic|pedestrian|vehicle detection|parking|crowd|person detection|tracking of people",
    ),
    (
        "image_vision_generic",
        r"image stabiliz|photo quality|visual odometry|camera calibration|stitching|3d reconstruction of urban|photogrammetry of urban|registration of aeria",
    ),
    (
        "human_uav_interaction",
        r"human-?drone|gesture control|virtual reality|teleoperat|simulator for pilots",
    ),
    (
        "spraying_application",
        r"spray(?!weed)|application (?:of|rate)|droplet|deposition of pesticide",
    ),
    (
        "phenotyping_traits",
        r"phenotyp|height estimat|biomass estimat|yield estimat|estimation (?:of|for) yield|nitrogen|chlorophyll|lai|spad|leaf area|growth monitor|disease detec|crop health monitor",
    ),
    (
        "survey_review_secondary",
        r"review|survey of|systematic res|scoping res|advances in|perspective on|state of the art on",
    ),
]


def main():
    ded = json.loads(
        (CAL / "v03_r3e_20261017_deduped.json").read_text(encoding="utf-8-sig")
    )
    docs = ded["documents"]
    D = lambda sid: docs[int(sid.split("-")[1]) - 1]

    # ---- #14: WRONG_TASK taxonomy (A1 primary code, crossref-labeled) ----------
    counts = Counter()
    unlabeled_titles = []
    per_bucket_years = defaultdict(Counter)
    for df in sorted(DEC.glob("*.json")):
        x = json.loads(df.read_text(encoding="utf-8-sig"))
        if str(x.get("screener_id") or "").upper() != "A1":
            continue
        for r in x.get("decisions") or []:
            if r.get("decision") != "EXCLUDE":
                continue
            sid = r["screening_id"]
            d = D(sid)
            if d.get("provider") != "crossref":
                continue
            code = None
            for k in ("reason_code", "exclusion_reason_code", "reason_CODE"):
                if r.get(k):
                    code = str(r[k]).upper()
                    break
            if code != "WRONG_TASK":
                continue
            t = (d.get("title") or "").lower()
            for name, pat in BUCKETS:
                if re.search(pat, t):
                    counts[name] += 1
                    per_bucket_years[name][str(d.get("year"))[:4]] += 1
                    break
            else:
                counts["untainorized_other"] += 1
                unlabeled_titles.append((sid, (d.get("title") or "")[:90]))
    total_wt = sum(counts.values())

    # ---- #2: citation gap ------------------------------------------------------
    fam = defaultdict(dict)
    for df in sorted(DEC.glob("*.json")):
        x = json.loads(df.read_text(encoding="utf-8-sig"))
        f = str(x.get("screener_id") or "").upper()
        if f not in ("A1", "A2"):
            f = "A1" if "A1" in df.name else "A2"
        for r in x.get("decisions") or []:
            if r.get("screening_id") and r.get("decision"):
                fam[r["screening_id"]][f] = r["decision"]

    def sids(dec):
        return [s for s, f in fam.items() if f.get("A1") == f.get("A2") == dec]

    inc, exc = sids("INCLUDE"), sids("EXCLUDE")
    cr = [i for i, d in enumerate(docs) if d.get("provider") == "crossref"]

    def cites(sid):
        return D(sid).get("citations_count") or 0

    cr_inc = [s for s in inc if D(s).get("provider") == "crossref"]
    oa_inc = [s for s in inc if D(s).get("provider") == "openalex"]
    hist = lambda vals: dict(
        sorted(
            Counter(
                "0"
                if v == 0
                else "1-5"
                if v <= 5
                else "6-20"
                if v <= 20
                else "21-50"
                if v <= 50
                else ">50"
                for v in vals
            ).items()
        )
    )
    # high-citation classics check: openalex corpus citations cap vs crossref
    top_oa = sorted(
        D(s).get("citations_count") or 0
        for s in [s for s in fam if D(s).get("provider") == "openalex"]
    )[::-1][:5]
    top_cr = sorted(D(f"SCI-{i + 1:06d}").get("citations_count") or 0 for i in cr)[
        ::-1
    ][:5]
    gap = {
        "crossref_unique_includes_n": len(cr_inc),
        "crossref_includes_citation_hist": hist([cites(s) for s in cr_inc]),
        "openalex_includes_citation_hist": hist([cites(s) for s in oa_inc]),
        "crossref_includes_citations_median": sorted(cites(s) for s in cr_inc)[
            len(cr_inc) // 2
        ],
        "openalex_includes_citations_median": sorted(cites(s) for s in oa_inc)[
            len(oa_inc) // 2
        ],
        "top_cited_corpus_by_provider": {
            "openalex_top5": top_oa,
            "crossref_top5": top_cr,
        },
        "note": (
            "If crossref includes skew 0-5 cites while openalex holds all >50 cites, "
            "crossref adds high-recall/low-impact long tail, not classics; if the top-5 "
            "crossref citations exceed openalex top-5, openalex has a coverage gap."
        ),
        "examples_top_cited_crossref_includes": [
            {
                "id": s,
                "title": (D(s).get("title") or "")[:80],
                "citations": cites(s),
                "year": D(s).get("year"),
            }
            for s in sorted(cr_inc, key=lambda s: -cites(s))[:10]
        ],
    }

    p14 = CAL / "v03_scr1_wrongtask_taxonomy.json"
    p14.write_text(
        json.dumps(
            {
                "a1_crossref_wrongtask_rows": total_wt,
                "bucket_counts": dict(counts.most_common()),
                "buckets_uncategorized": {
                    "n": counts["untainorized_other"],
                    "examples": unlabeled_titles[:30],
                },
                "per_bucket_year_top": {
                    k: dict(v.most_common(3)) for k, v in per_bucket_years.items()
                },
                "bucket_regexes": {k: p for k, p in BUCKETS},
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    p2 = CAL / "v03_scr1_citation_gap.json"
    p2.write_text(
        json.dumps(gap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print(f"#14 WRONG_TASK taxonomy: {total_wt} crossref A1 WRONG_TASK rows")
    for k, v in counts.most_common():
        print(f"  {k:28s} {v:6d} ({100 * v / max(1, total_wt):4.1f}%)")
    print(
        f"#2 citation gap: crossref-inc hist {gap['crossref_includes_citation_hist']} "
        f"median {gap['crossref_includes_citations_median']} | "
        f"openalex-inc {gap['openalex_includes_citation_hist']} median {gap['openalex_includes_citations_median']}"
    )
    print("  top-5 corpus cites — openalex:", top_oa, "| crossref:", top_cr)
    print("written ->", p14.name, "+", p2.name)


if __name__ == "__main__":
    main()
