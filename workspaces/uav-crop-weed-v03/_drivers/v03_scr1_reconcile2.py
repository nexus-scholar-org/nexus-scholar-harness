"""SCR1 RECONCILE v2 — PENDING-aware, full-sweep, schema-contract consumption.

Upgrades the pilot-only reconcile (batches 1-6, object-copy preserving original
pilot artifacts untouched) to the full 283-batch sweep, consuming
v03_scr1_schema.normalize_row (alias map + debt tags), and routes every paired
decision to exactly one lane (never Excel-fill an EXCLUDE):

  LANES
    mutual_include            INC|INC  -> human confirmation packet
    mutual_exclude            EXC|EXC  -> closed (10% verification sample: NEXT wave, not generated here)
    mutual_pending            PEND|PEND-> human lane (both screeners deferred)
    third_inc_exc             INC|EXC or EXC|INC -> blinded boundary third-rater
    third_inc_pend            INC|PEND or PEND|INC -> blinded boundary third-rater
    third_exc_pend            EXC|PEND or PEND|EXC -> blinded boundary third-rater

Third-rater packets (`third_lane/packs/pack_NNNN.view3.json`) carry view text
ONLY (title/abstract exactly as A1/A2 saw it; no decisions, no reasons, no
confidences) so the T3 agents are fully blinded.

Outputs (new files; no prior artifact overwritten):
  - calibration_v03/v03_scr1_reconciliation_full.json  (stats + lane manifest)
  - calibration_v03/v03_scr1_lane_index.md             (routing sheet)
  - calibration_v03/screening_scr1/third_lane/packs/*.view3.json
"""

import json
import sys
from collections import Counter
from pathlib import Path

DRIVERS = Path(__file__).resolve().parent
sys.path.insert(0, str(DRIVERS))
from v03_scr1_schema import normalize_row  # noqa: E402

ROOT = (
    DRIVERS.parents[2]
    if False
    else Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
)
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
SCR = CAL / "screening_scr1"
DEC = SCR / "decisions"
VIEWS = SCR / "moderation_views"
LANE = SCR / "third_lane"
PACKS = LANE / "packs"
PACKS.mkdir(parents=True, exist_ok=True)

NOBS = 283


def load_family(fam):
    out = {}
    for n in range(1, NOBS + 1):
        fp = DEC / f"batch_{n:04d}_decisions_{fam}.json"
        doc = json.loads(fp.read_text(encoding="utf-8"))
        for row in doc["decisions"]:
            canon, tags = normalize_row(row)
            sid = canon["screening_id"]
            assert sid not in out, f"{fam} duplicate {sid}"
            out[sid] = {
                "decision": canon["decision"],
                "reason_code": canon["reason_code"],
                "confidence": canon["confidence"],
                "support": canon["one_line_support"] or row.get("reason"),
                "batch": n,
                "debt": tags,
            }
    return out


def lane_key(a, b):
    s = {a, b}
    if a == b == "INCLUDE":
        return "mutual_include"
    if a == b == "EXCLUDE":
        return "mutual_exclude"
    if a == b == "PENDING":
        return "mutual_pending"
    order = sorted(s)
    return "third_" + order[0].lower() + "_" + order[1].lower()


def main():
    a1 = load_family("A1")
    a2 = load_family("A2")
    sids = sorted(set(a1) | set(a2))
    assert len(sids) == 14150, f"expected 14150 corpus ids, got {len(sids)}"

    # regression guards: physical totals must match the closed-sweep stats
    t1 = Counter(v["decision"] for v in a1.values())
    t2 = Counter(v["decision"] for v in a2.values())
    assert (t1["INCLUDE"], t1["EXCLUDE"], t1["PENDING"]) == (787, 12764, 599), t1
    assert (t2["INCLUDE"], t2["EXCLUDE"], t2["PENDING"]) == (844, 12682, 624), t2

    lanes = {
        k: []
        for k in (
            "mutual_include",
            "mutual_exclude",
            "mutual_pending",
            "third_include_exclude",
            "third_exclude_include",
            "third_exclude_pending",
            "third_include_pending",
            "third_pending_include",
            "third_pending_exclude",
        )
    }
    for sid in sids:
        (a1 if sid in a1 else a2)  # silence unused; sids always covered below
        d1 = a1.get(sid, {}).get("decision")
        d2 = a2.get(sid, {}).get("decision")
        key = lane_key(d1, d2)
        lanes.setdefault(key, []).append(sid)

    lane_counts = {k: len(v) for k, v in lanes.items()}

    # binary agreement / kappa recompute on both-terminal pairs
    both_term = [
        s
        for s in sids
        if a1[s]["decision"] in ("INCLUDE", "EXCLUDE")
        and a2[s]["decision"] in ("INCLUDE", "EXCLUDE")
    ]
    agree = sum(1 for s in both_term if a1[s]["decision"] == a2[s]["decision"])
    n = len(both_term)
    po = agree / n
    cats = ("INCLUDE", "EXCLUDE")
    pe = sum(
        (sum(1 for s in both_term if a1[s]["decision"] == c) / n)
        * (sum(1 for s in both_term if a2[s]["decision"] == c) / n)
        for c in cats
    )
    kappa = (po - pe) / (1 - pe)

    # load views once; build record lookup for third-lane packets
    view_recs = {}
    for npb in range(1, NOBS + 1):
        v = json.loads(
            (VIEWS / f"batch_{npb:04d}.view.json").read_text(encoding="utf-8")
        )
        for r in v["records"]:
            view_recs[r["screening_id"]] = r

    # third-rater packs: 50 per pack, sorted sid
    third_sids = (
        lanes["third_include_exclude"]
        + lanes["third_exclude_include"]
        + lanes["third_include_pending"]
        + lanes["third_pending_include"]
        + lanes["third_exclude_pending"]
        + lanes["third_pending_exclude"]
    )
    third_sids = sorted(third_sids)
    packs = {}
    for i, sid in enumerate(third_sids):
        packs.setdefault(i // 50 + 1, []).append(sid)

    manifest = {}
    for pn, p_sids in sorted(packs.items()):
        recs = []
        for sid in p_sids:
            vr = view_recs[sid]
            recs.append(
                {
                    "screening_id": sid,
                    "title": vr.get("title"),
                    "abstract": vr.get("abstract"),
                    "abstract_effectively_null": vr.get("abstract_effectively_null"),
                    "moderation_redacted": vr.get("moderation_redacted"),
                    "moderation_terms": vr.get("moderation_terms"),
                    "source_batch": vr.get("_batch") or vr.get("batch_index"),
                }
            )
        fp = PACKS / f"pack_{pn:04d}.view3.json"
        fp.write_text(
            json.dumps(
                {
                    "role": "T3 boundary third-rater, blinded (no A1/A2 decisions inside)",
                    "pack": f"pack_{pn:04d}",
                    "n_records": len(recs),
                    "instruction_anchor_sha_prompt": "0c7f129d",
                    "criteria_sha_prefix": "9ae1f97d",
                    "records": recs,
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest[f"pack_{pn:04d}"] = len(p_sids)

    recon = {
        "session": "UAV-SCREEN-SCR1-20261018",
        "schema_source": "_drivers/v03_scr1_schema.py (frozen template normative)",
        "totals": {"records": len(sids), "A1": dict(t1), "A2": dict(t2)},
        "lane_counts": lane_counts,
        "human_lanes": {
            "mutual_include": lanes["mutual_include"],
            "mutual_pending": lanes["mutual_pending"],
        },
        "agreement": {
            "both_terminal_n": n,
            "raw_agreement_pct": round(100 * po, 2),
            "cohens_kappa": round(kappa, 4),
        },
        "third_lane": {
            "n_records": len(third_sids),
            "n_packs": len(packs),
            "pack_manifest": manifest,
        },
        "notes": [
            "mutual_exclude (EXC|EXC) 12357 records: closed pending the NEXT 10% verification-sample wave (deferred)",
            "third-rater outputs land under screening_scr1/third_lane/decisions/",
            "human lead confirms 100% of records per Option C; agent lanes are suggestions",
        ],
    }
    (CAL / "v03_scr1_reconciliation_full.json").write_text(
        json.dumps(recon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# SCR1 reconciliation — lane routing index (Pass-1 suggestions ONLY)",
        "",
        f"Records: {len(sids)} | both-terminal: {n} | raw agreement {recon['agreement']['raw_agreement_pct']}% | kappa {recon['agreement']['cohens_kappa']}",
        "",
        "| lane | n | route |",
        "|---|---:|---|",
        f"| mutual INCLUDE | {lane_counts['mutual_include']} | human confirmation packet |",
        f"| mutual EXCLUDE | {lane_counts['mutual_exclude']} | closed; 10% verification sample next wave |",
        f"| mutual PENDING | {lane_counts['mutual_pending']} | human lane |",
        f"| INC|EXC conflicts | {lane_counts['third_include_exclude'] + lane_counts['third_exclude_include']} | blinded T3 third-rater |",
        f"| INC|PEND conflicts | {lane_counts['third_include_pending'] + lane_counts['third_pending_include']} | blinded T3 third-rater |",
        f"| EXC|PEND conflicts | {lane_counts['third_exclude_pending'] + lane_counts['third_pending_exclude']} | blinded T3 third-rater |",
        "",
        f"Third-rater lane: {len(third_sids)} records in {len(packs)} packs (50/pack).",
    ]
    (CAL / "v03_scr1_lane_index.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                k: recon[k]
                for k in ("totals", "lane_counts", "agreement", "third_lane", "notes")
            },
            indent=2,
        )[:1600]
    )


if __name__ == "__main__":
    main()
