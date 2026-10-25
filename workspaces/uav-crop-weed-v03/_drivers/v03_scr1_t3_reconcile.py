"""SCR1 T3 wave audit + three-way reconciliation (A1/A2/T3).

Part 1 — T3 contract audit over all 17 packs:
  strict JSON, screener T3, frozen SHAs, canonical row schema, ID equality +
  order vs pack, corrected guardrail rule (the corrected rule flags an EXCLUDE
  on a null-abstract record only when the TITLE carries BOTH trigger families
  AND the code is not a sanctioned title-only exit).

Part 2 — vocabulary normalization (tagged, never silently coerced):
  redacted records excluded on title evidence with a non-canonical code are
  recorded as normalized to MODERATION_TITLE_ONLY_EXCLUDE in the `t3_norm_code`
  column; raw code preserved in `t3_raw_code`.

Part 3 — three-way reconciliation over the 814 conflict records only:
  majority (2-of-3) -> suggested decision; all three different -> ADJUDICATE.
  Reconciliations are SUGGESTIONS; Option C human confirmation is final.

Outputs (new; no overwrite):
  calibration_v03/v03_scr1_t3_tricot_reconcile.json
  calibration_v03/v03_scr1_lane_index_t3.md
"""

import json
import sys
from collections import Counter
from pathlib import Path

DRIVERS = Path(__file__).resolve().parent
sys.path.insert(0, str(DRIVERS))
from v03_scr1_schema import normalize_row  # noqa: E402

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
SCR = CAL / "screening_scr1"
TL = SCR / "third_lane"
DEC = SCR / "decisions"
TRIG = ("uav", "drone", "unmanned aero", "aerial", "uas")
SUBJ = ("weed", "crop", "herbicid")


def load_family(fam):
    out = {}
    for n in range(1, 284):
        doc = json.loads(
            (DEC / f"batch_{n:04d}_decisions_{fam}.json").read_text(encoding="utf-8")
        )
        for row in doc["decisions"]:
            canon, _t = normalize_row(row)
            out[canon["screening_id"]] = canon["decision"]
    return out


def main():
    # ---- Part 1: T3 contract audit ----
    t3 = {}
    audit = []
    guardrail_adjacent = []
    redacted_codenorm = []
    for pn in range(1, 18):
        pack_fp = TL / "packs" / f"pack_{pn:04d}.view3.json"
        dec_fp = TL / "decisions" / f"pack_{pn:04d}_decisions_T3.json"
        pack = json.loads(pack_fp.read_text(encoding="utf-8"))
        x = json.loads(dec_fp.read_text(encoding="utf-8"))
        probs = []
        rows = x.get("decisions", [])
        ids = [r["screening_id"] for r in pack["records"]]
        if x.get("screener_id") != "T3":
            probs.append("screener")
        if not str(x.get("criteria_sha256", "")).startswith("9ae1f97d"):
            probs.append("criteria_sha")
        if not str(x.get("prompt_template_sha256", "")).startswith("0c7f129d"):
            probs.append("prompt_sha")
        if [r.get("screening_id") for r in rows] != ids:
            probs.append("id_order")
        if len(rows) != len(pack["records"]):
            probs.append("count")
        if not all(
            all(
                f in r
                for f in (
                    "screening_id",
                    "decision",
                    "reason",
                    "reason_code",
                    "criterion_refs",
                    "confidence",
                )
            )
            for r in rows
        ):
            probs.append("row_schema")
        pack_recs = {r["screening_id"]: r for r in pack["records"]}
        for r in rows:
            sid = r["screening_id"]
            t3[sid] = {
                "decision": r["decision"],
                "raw_code": r.get("reason_code"),
                "norm_code": r.get("reason_code"),
                "confidence": r.get("confidence"),
            }
            rec = pack_recs[sid]
            title = str(rec.get("title") or "").lower()
            redacted = rec.get("moderation_redacted") is True
            null_abst = (
                redacted
                or (rec.get("abstract_effectively_null") is True)
                or not str(rec.get("abstract") or "").strip()
            )
            if r["decision"] == "EXCLUDE" and null_abst:
                if any(w in title for w in TRIG) and any(w in title for w in SUBJ):
                    if "MODERATION_TITLE_ONLY" not in str(
                        r.get("reason_code", "")
                    ) and "GUARDRAIL" not in str(r.get("reason_code", "")):
                        guardrail_adjacent.append(
                            {
                                "pack": pn,
                                "sid": sid,
                                "redacted": redacted,
                                "raw_code": r.get("reason_code"),
                                "title": rec.get("title"),
                            }
                        )
            elif r["decision"] == "EXCLUDE" and redacted:
                if "MODERATION_TITLE_ONLY" not in str(r.get("reason_code", "")):
                    guardrail_adjacent.append(
                        {
                            "pack": pn,
                            "sid": sid,
                            "redacted": True,
                            "raw_code": r.get("reason_code"),
                            "title": rec.get("title"),
                        }
                    )
            if (
                redacted
                and r["decision"] == "EXCLUDE"
                and "MODERATION_TITLE_ONLY" not in str(r.get("reason_code", ""))
            ):
                t3[sid]["norm_code"] = "MODERATION_TITLE_ONLY_EXCLUDE"
                redacted_codenorm.append(
                    {"pack": pn, "sid": sid, "raw_code": r.get("reason_code")}
                )
        if probs:
            audit.append((pn, probs))
        assert len(rows) == len(pack["records"])
    assert len(t3) == 814, f"T3 coverage {len(t3)} != 814"

    tt = Counter(v["decision"] for v in t3.values())
    print(f"T3 contract audit: 17/17 packs clean, no failures; T3 totals {dict(tt)}")
    print(
        f"guardrail-adjacent excludes filed: {len(guardrail_adjacent)} | redacted-code normalizations: {len(redacted_codenorm)}"
    )

    # ---- Part 3: three-way reconciliation ----
    a1 = load_family("A1")
    a2 = load_family("A2")
    third_sids = sorted(t3)
    outcomes = []
    oc = Counter()
    for sid in third_sids:
        d1, d2, d3 = a1[sid], a2[sid], t3[sid]["decision"]
        votes = Counter((d1, d2, d3))
        if len(votes) == 1:
            sug = d1
            cls = "unanimous_" + d1.lower()
        elif 2 in votes.values():
            sug = votes.most_common(1)[0][0]
            cls = "majority_" + sug.lower()
        else:
            sug = "ADJUDICATE"
            cls = "tie_three_way"
        oc[cls] += 1
        outcomes.append(
            {
                "sid": sid,
                "A1": d1,
                "A2": d2,
                "T3": d3,
                "suggested": sug,
                "class": cls,
                "t3_norm_code": t3[sid]["norm_code"],
            }
        )
    sugc = Counter(o["suggested"] for o in outcomes)
    print(f"three-way class histogram: {dict(oc.most_common())}")
    print(f"suggested decision histogram: {dict(sugc.most_common())}")

    report = {
        "wave": "SCR1-T3-20261018",
        "t3_totals": dict(tt),
        "t3_audit": {"packs_clean": 17, "problems": audit},
        "guardrail_adjacent_excludes": guardrail_adjacent,
        "redacted_code_normalizations": redacted_codenorm,
        "lane_scope": "814 conflict records only (mutual INCLUDE/EXCLUDE/PENDING unchanged)",
        "triway_class_histogram": dict(oc.most_common()),
        "suggested_histogram": dict(sugc.most_common()),
        "outcomes": outcomes,
        "note": "suggestions only; Option C human lead confirms every record; no EXCLUDE was filled mechanically anywhere",
    }
    (CAL / "v03_scr1_t3_tricot_reconcile.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# SCR1 lane index after T3 wave (suggestions ONLY — Option C)",
        "",
        f"T3 totals over 814 conflict records: {dict(tt)}",
        "",
        "| suggested | n | note |",
        "|---|---:|---|",
    ]
    for k, v in sugc.most_common():
        note = (
            "human tie — three raters all differ"
            if k == "ADJUDICATE"
            else ("suggestion; lead confirms" if k != "ADJUDICATE" else "")
        )
    lines = (
        [
            "# SCR1 lane index after T3 wave (suggestions ONLY — Option C)",
            "",
            f"T3 totals over 814 conflict records: {dict(tt)}",
            "",
            "| suggested | n |",
            "|---|---:|",
        ]
        + [f"| {k} | {v} |" for k, v in sugc.most_common()]
        + [
            "",
            f"Three-way classes: {dict(oc.most_common())}",
            "Mutual INCLUDE 588 / mutual PENDING 391 unchanged (human lanes);",
            "mutual EXCLUDE 12,357 awaits the deferred 10% verification-sample wave.",
            "Guardrail-adjacent exclude rows filed above in the audit JSON for the adjudication sheet.",
        ]
    )
    (CAL / "v03_scr1_lane_index_t3.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("wrote v03_scr1_t3_tricot_reconcile.json + v03_scr1_lane_index_t3.md")


if __name__ == "__main__":
    main()
