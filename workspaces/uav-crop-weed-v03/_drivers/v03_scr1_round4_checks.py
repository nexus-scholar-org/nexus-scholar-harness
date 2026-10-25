# -*- coding: utf-8 -*-
"""
SCR1 follow-up round 4 (queue items #6 and #10) — deterministic driver.

#6  screening-entropy vs abstract length (conflicts vs mutual lanes; raw and
    moderation-flagged records separated)
#10 batch-position drift across the 283 screening batches (disagreement and
    exclusion rates by batch number deciles, per family)

Outputs NEW file: calibration_v03/v03_scr1_round4_checks.json
"""

import json
import pathlib
import statistics
from collections import Counter, defaultdict

CAL = pathlib.Path(__file__).resolve().parents[1] / "calibration_v03"
DEC = CAL / "screening_scr1" / "decisions"


def main():
    ded = json.loads(
        (CAL / "v03_r3e_20261017_deduped.json").read_text(encoding="utf-8-sig")
    )
    docs = ded["documents"]
    D = lambda sid: docs[int(sid.split("-")[1]) - 1]

    # per sid: family -> decision ; keep batch number per family & sid
    fam = defaultdict(dict)
    fam_batches = defaultdict(dict)
    for df in sorted(DEC.glob("*.json")):
        x = json.loads(df.read_text(encoding="utf-8-sig"))
        f = str(x.get("screener_id") or "").upper()
        if f not in ("A1", "A2"):
            f = "A1" if "A1" in df.name else "A2"
        # batch number from filename
        name = df.name
        bnum = None
        if "batch_" in name:
            try:
                bnum = int(name.split("batch_")[1][:4])
            except Exception:
                bnum = None
        for r in x.get("decisions") or []:
            if r.get("screening_id") and r.get("decision"):
                fam[r["screening_id"]][f] = r["decision"]
                if bnum:
                    fam_batches[r["screening_id"]][f] = bnum

    # moderation/redaction set (from round-2 ledger sources)
    red = json.loads(
        (CAL / "v03_scr1_redaction_ledger.json").read_text(encoding="utf-8-sig")
    )
    srcm = red.get("sources", {}) if isinstance(red, dict) else {}
    redacted = set()
    mv = CAL / "screening_scr1" / "moderation_views"
    for mf in sorted(mv.glob("*.json")):
        mx = json.loads(mf.read_text(encoding="utf-8-sig"))
        for mr in mx.get("records", []):
            if mr.get("moderation_redacted") is True:
                sid_key = mr.get("screening_id")
                if sid_key:
                    redacted.add(sid_key)


    # ---- #6: abstract-length vs lane -----------------------------------------
    def alen(sid):
        s = (D(sid).get("abstract") or "").strip()
        return len(s), s

    lanes = {"mutual": [], "conflict": []}
    stats = {
        "mutual": [],
        "conflict": [],
        "mutual_redacted": [],
        "conflict_redacted": [],
    }
    for sid, f in fam.items():
        d1, d2 = f.get("A1"), f.get("A2")
        if not d1 or not d2:
            continue
        ablen, _ = alen(sid)
        bucket = "mutual" if d1 == d2 else "conflict"
        if sid in redacted:
            stats[
                "mutual_redacted" if bucket == "mutual" else "conflict_redacted"
            ].append((ablen, sid))
        stats[bucket].append(ablen)

    def ms(v):
        return {
            "n": len(v),
            "mean": round(statistics.mean(v), 0) if v else None,
            "median": round(statistics.median(v), 0) if v else None,
            "pct_under_300": round(
                100 * sum(1 for x in v if x < 300) / max(1, len(v)), 1
            ),
        }

    out6 = {}
    for k, v in stats.items():
        lens = [x[0] for x in v] if v and isinstance(v[0], tuple) else v
        out6[k] = ms(lens)

    # ---- #10: batch-position drift --------------------------------------------
    dec_all = []
    for sid, f in fam.items():
        d1, d2 = f.get("A1"), f.get("A2")
        b1 = fam_batches[sid].get("A1")
        if d1 and d2 and b1:
            dec_all.append((b1, 1 if d1 != d2 else 0))

    acc = defaultdict(list)
    for b, dis in dec_all:
        acc["disagree_b" + str(min(3, int((b - 1) / 95)))].append(dis)
    exc_all = []
    for sid, f in fam.items():
        d1 = f.get("A1")
        b1 = fam_batches[sid].get("A1")
        if d1 and b1:
            exc_all.append((b1, 1 if d1 == "EXCLUDE" else 0))
    for b, e in exc_all:
        acc["exclude_b" + str(min(3, int((b - 1) / 95)))].append(e)
    out10 = {}
    for k in sorted(acc):
        v = acc[k]
        out10[k] = {"n": len(v), "rate_pct": round(100 * sum(v) / max(1, len(v)), 2)}
    out = {
        "round": "SCR1_round4_followups",
        "items": ["6", "10"],
        "abstract_length_vs_lane": out6,
        "batch_band_dx": {
            "bands": "batch 1=1..95, 2=96..190, 3=191..283",
            "note": "batch number derived from decision filenames; family A1 frames",
            "drift": out10,
        },
        "redacted_flag_count": len(redacted),
    }
    p = CAL / "v03_scr1_round4_checks.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("#6 abstract length vs lane:")
    for k, v in out6.items():
        print(f"  {k:18s} {v}")
    print("#10 drift by batch band:")
    for k, v in out10.items():
        print(f"  {k:14s} {v}")
    print("written ->", p.name)


if __name__ == "__main__":
    main()
