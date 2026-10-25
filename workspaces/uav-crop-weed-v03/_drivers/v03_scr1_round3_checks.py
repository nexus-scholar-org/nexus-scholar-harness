# -*- coding: utf-8 -*-
"""
SCR1 follow-up round 3 (queue items #7, #8, #9, #13) — one deterministic driver.

#7  grounding-flag rate by provider (cross-tab of v03_scr1_rationale_audit.json
    'flagged' rows with corpus provider labels)
#8  T4 agreement stratified by pack crossref-dominance (share buckets)
#9  marginal value of S2/arXiv/PubMed (lanes + unicity)
#13 2027-leak rows: lane + reason-code disqualification check

Outputs NEW file: calibration_v03/v03_scr1_round3_checks.json
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
    D = lambda sid: docs[int(sid.split("-")[1]) - 1]
    prov = lambda sid: D(sid).get("provider")

    fam = defaultdict(dict)
    for df in sorted(DEC.glob("*.json")):
        x = json.loads(df.read_text(encoding="utf-8-sig"))
        f = str(x.get("screener_id") or "").upper()
        if f not in ("A1", "A2"):
            f = "A1" if "A1" in df.name else "A2"
        for r in x.get("decisions") or []:
            if r.get("screening_id") and r.get("decision"):
                fam[r["screening_id"]][f] = r["decision"]
    inc = {s for s, f in fam.items() if f.get("A1") == f.get("A2") == "INCLUDE"}
    exc = {s for s, f in fam.items() if f.get("A1") == f.get("A2") == "EXCLUDE"}
    pen = {s for s, f in fam.items() if f.get("A1") == f.get("A2") == "PENDING"}
    out = {"round": "SCR1_round3_followups", "items": ["7", "8", "9", "13"]}

    # ---- #7: grounding flag rate by provider --------------------------------
    ra = json.loads(
        (CAL / "v03_scr1_rationale_audit.json").read_text(encoding="utf-8-sig")
    )
    rows_per_prov = Counter()
    for sid, f in fam.items():
        if f.get("A1"):
            rows_per_prov[prov(sid)] += 1
    by_prov_flag = Counter()
    flags_by_code = defaultdict(Counter)
    for row in ra.get("flagged", []):
        sid = row["screening_id"]
        p = prov(sid)
        by_prov_flag[p] += 1
        for pr in row.get("problems", []):
            flags_by_code[p][pr] += 1
        if not row.get("problems"):
            flags_by_code[p]["low_grounding_ratio_only"] += 1
    flagged_rate = {
        p: {
            "screened_rows_A1": rows_per_prov.get(p, 0),
            "flagged_rows": by_prov_flag.get(p, 0),
            "flag_rate_pct": round(
                100 * by_prov_flag.get(p, 0) / max(1, rows_per_prov.get(p, 0)), 2
            ),
            "top_problem_classes": dict(flags_by_code[p].most_common(4)),
        }
        for p in rows_per_prov
    }
    out["grounding_flags_by_provider"] = flagged_rate

    # ---- #8: T4 agreement by pack crossref-dominance --------------------------
    lane = CAL / "screening_scr1" / "verification_lane"
    packs = sorted((lane / "packs").glob("pack_*.view3.json"))
    strat = defaultdict(lambda: {"packs": 0, "n": 0, "agree": 0, "exceptions": 0})
    for pf in packs:
        pid = pf.name.replace(".view3.json", "")
        pk = json.loads(pf.read_text(encoding="utf-8-sig"))
        try:
            dec = json.loads(
                (lane / "decisions" / f"{pid}_decisions_T4.json").read_text(
                    encoding="utf-8-sig"
                )
            )
        except FileNotFoundError:
            continue
        rows = {r["screening_id"]: r["decision"] for r in dec["decisions"]}
        recs = pk["records"]
        cr = sum(
            1
            for r in recs
            if docs[int(r["screening_id"].split("-")[1]) - 1].get("provider")
            == "crossref"
        )
        share = cr / len(recs)
        q = (
            "0-90"
            if share <= 0.90
            else "90-95"
            if share <= 0.95
            else "95-99"
            if share <= 0.99
            else "100"
        )
        s = strat[q]
        s["packs"] += 1
        for r in recs:
            d = rows.get(r["screening_id"])
            if d is None:
                continue
            s["n"] += 1
            if d == "EXCLUDE":
                s["agree"] += 1
            else:
                s["exceptions"] += 1
    out["t4_agreement_by_pack_crossref_share"] = {
        q: {**v, "agreement_pct": round(100 * v["agree"] / max(1, v["n"]), 2)}
        for q, v in strat.items()
    }

    # ---- #9: marginal value of S2/arXiv/PubMed -------------------------------
    marg = {}
    for p in ("semanticscholar", "arxiv", "pubmed"):
        sids_p = [
            f"SCI-{i + 1:06d}" for i, d in enumerate(docs) if d.get("provider") == p
        ]
        marg[p] = {
            "unique_records": len(sids_p),
            "mutual_include": sum(1 for s in sids_p if s in inc),
            "mutual_pending": sum(1 for s in sids_p if s in pen),
            "mutual_exclude": sum(1 for s in sids_p if s in exc),
        }
    out["small_provider_marginal_value"] = marg

    # ---- #13: 2027-leak check -------------------------------------------------
    leak = []
    for i, d in enumerate(docs):
        if d.get("provider") == "crossref" and str(d.get("year")) == "2027":
            sid = f"SCI-{i + 1:06d}"
            leak.append(
                {
                    "sid": sid,
                    "title": (d.get("title") or "")[:80],
                    "lane": (
                        "mutual_include"
                        if sid in inc
                        else "mutual_exclude"
                        if sid in exc
                        else "mutual_pending"
                        if sid in pen
                        else "conflict/unscreened"
                    ),
                    "A1": fam.get(sid, {}).get("A1"),
                    "A2": fam.get(sid, {}).get("A2"),
                    "citations": d.get("citations_count"),
                }
            )
    out["year_2027_leak"] = {"n": len(leak), "rows": leak}

    outpath = CAL / "v03_scr1_round3_checks.json"
    outpath.write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print("#7 grounding flag rate by provider:")
    for p, v in flagged_rate.items():
        print(
            f"  {p:16s} rows={v['screened_rows_A1']:6d} flagged={v['flagged_rows']:5d} "
            f"rate={v['flag_rate_pct']:5.2f}% {v['top_problem_classes']}"
        )
    print("#8 T4 agreement by pack crossref share:")
    for q, v in out["t4_agreement_by_pack_crossref_share"].items():
        print(
            f"  share {q}%: packs={v['packs']} n={v['n']} agree={v['agree']} "
            f"except={v['exceptions']} ({v['agreement_pct']}%)"
        )
    print("#9 marginal value:", json.dumps(marg))
    print("#13 2027-leak rows:", len(leak))
    for e in leak[:6]:
        print("  ", e["sid"], e["lane"], e["A1"], "|", e["title"][:55])
    print("written ->", outpath.name)


if __name__ == "__main__":
    main()
