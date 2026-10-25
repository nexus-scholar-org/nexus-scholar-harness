"""SCR1 RECONCILE — reconcile two blinded screener-agents' Pass-1 decisions.

Consumes batch_NNN_decisions_A1.json / _A2.json produced by the blinded pilot
agents and produces:
  - per-batch and overall agreement metrics
  - kit `reconcile_multi_screener_decisions` output on the INCLUDE/EXCLUDE
    rating layer (majority + tie routing) for the 2-rater pilot
  - guardrail-compliance check (abstract-null + UAV/weed title MUST be PENDING)
  - decision-vs-decision confusion matrix and per-reason-code breakdown
  - raw agreement + Cohen's kappa (binary include/exclude view)
  - pilot extrapolation: records screened -> projected full-corpus include
    counts with Wilson 95% interval (TO the human lead, never a decision)

Outputs (new files):
  - calibration_v03/v03_scr1_pilot_reconciliation.json
  - _drivers/v03_scr1_reconcile_summary.json
  - calibration_v03/v03_scr1_human_confirmation_packet_pilot.md  (the human-lead
    review sheet for the 300 pilot records: every record's ID, both agents'
    decisions, and the suggested action)
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
SCR = CAL / "screening_scr1"
DEC = SCR / "decisions"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))

from scholar_search.screening import reconcile_multi_screener_decisions  # noqa: E402


def norm_dec(d):
    if not d:
        return None
    u = str(d).upper()
    if u in ("INCLUDE", "EXCLUDE", "PENDING"):
        return u
    return "INVALID"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, center - half), min(1.0, center + half))


def cohens_kappa(x, y):
    n = len(x)
    assert n == len(y)
    if n == 0:
        return None, None
    po = sum(1 for a, b in zip(x, y) if a == b) / n
    cats = set(x) | set(y)
    pe = sum(
        (sum(1 for v in x if v == c) / n) * (sum(1 for v in y if v == c) / n)
        for c in cats
    )
    if abs(1 - pe) < 1e-12:
        return po, 1.0
    return po, (po - pe) / (1 - pe)


def load_screener(tag):
    out = {}
    for i in range(1, 7):
        fp = DEC / f"batch_{i:04d}_decisions_{tag}.json"
        data = json.loads(fp.read_text(encoding="utf-8"))
        batch = json.loads((SCR / f"batch_{i:04d}.json").read_text(encoding="utf-8"))
        expected = {r["screening_id"] for r in batch["records"]}
        for d in data["decisions"]:
            sid = d["screening_id"]
            if sid not in expected:
                raise SystemExit(f"{tag} returned an id not in batch {i}: {sid}")
            out[sid] = {
                "decision": norm_dec(d.get("decision")),
                "reason_code": d.get("reason_code"),
                "confidence": d.get("confidence"),
                "support": d.get("one_line_support"),
                "batch": f"batch_{i:04d}",
            }
    return out


def main():
    a1 = load_screener("A1")
    a2 = load_screener("A2")
    shared = sorted(set(a1) & set(a2))
    missing_a1 = sorted(set(a2) - set(a1))
    missing_a2 = sorted(set(a1) - set(a2))
    print(
        f"shared ids={len(shared)} missing_A2={len(missing_a2)} missing_A1={len(missing_a1)}"
    )

    # Decision-level stats over shared ids.
    both_same = [s for s in shared if a1[s]["decision"] == a2[s]["decision"]]
    conf_pairs = Counter((a1[s]["decision"], a2[s]["decision"]) for s in shared)
    agree_inc = sum(
        1
        for s in shared
        if a1[s]["decision"] == "INCLUDE" and a2[s]["decision"] == "INCLUDE"
    )
    decide_only = [
        s
        for s in shared
        if a1[s]["decision"] in ("INCLUDE", "EXCLUDE")
        and a2[s]["decision"] in ("INCLUDE", "EXCLUDE")
    ]
    po_kappa_bin, kappa_bin = cohens_kappa(
        [("INC" if a1[s]["decision"] == "INCLUDE" else "EXC") for s in decide_only],
        [("INC" if a2[s]["decision"] == "INCLUDE" else "EXC") for s in decide_only],
    )

    # PENDING / guardrail compliance.
    guardrail_ids = set()
    for i in range(1, 7):
        b = json.loads((SCR / f"batch_{i:04d}.json").read_text(encoding="utf-8"))
        for r in b["records"]:
            if not (str(r.get("abstract") or "").strip()):
                t = (r.get("title") or "").lower()
                if any(
                    w in t for w in ("uav", "drone", "unmanned aero", "aerial")
                ) and any(w in t for w in ("weed", "crop", "herbicid", "herband")):
                    guardrail_ids.add(r["screening_id"])
    guardrail_check = []
    for s in guardrail_ids:
        for tag, amap in (("A1", a1), ("A2", a2)):
            if s in amap and amap[s]["decision"] == "EXCLUDE":
                guardrail_check.append(
                    {"id": s, "screener": tag, "violation": str(amap[s]["reason_code"])}
                )
    guardrail_ok = not guardrail_check

    # Kit reconciliation INCLUDE/EXCLUDE layer (2 raters).
    screeners_map = {
        "A1": {
            s: a1[s]["decision"]
            for s in shared
            if a1[s]["decision"] in ("INCLUDE", "EXCLUDE")
        },
        "A2": {
            s: a2[s]["decision"]
            for s in shared
            if a2[s]["decision"] in ("INCLUDE", "EXCLUDE")
        },
    }
    rec = reconcile_multi_screener_decisions(screeners_map)
    reconciled_decisions = {k: v for k, v in rec["reconciled"].items()}

    pilot_recs = {}
    for s in shared:
        pilot_recs[s] = {
            "batch": a1[s]["batch"],
            "A1": a1[s]["decision"],
            "A2": a2[s]["decision"],
            "A1_reason": a1[s]["reason_code"],
            "A2_reason": a2[s]["reason_code"],
            "suggested_action": reconciled_decisions.get(s, "PENDING/TIE"),
            "A1_support": a1[s]["support"],
            "A2_support": a2[s]["support"],
        }

    # Extrapolation (report-only): dual-reconciled include rate over shared.
    inc_k = sum(1 for v in reconciled_decisions.values() if v == "INCLUDE")
    inc_n = len(reconciled_decisions)
    lo, hi = wilson(inc_k, inc_z := inc_n)
    projected = (inc_k / inc_z if inc_z else 0) * 14150

    recon = {
        "session": "UAV-SCREEN-SCR1-20261018",
        "pilot_scope": "batches 0001-0006 (300 records target)",
        "screener_ids": ["A1", "A2"],
        "shared_decided": len(shared),
        "missing_from_A1": len(missing_a1),
        "missing_from_A2": len(missing_a2),
        "agreement_pct": round(100 * len(both_same) / len(shared), 2)
        if shared
        else None,
        "confusion_pairs": {f"{k[0]}|{k[1]}": v for k, v in conf_pairs.items()},
        "shared_include_agreement": agree_inc,
        "binary_include_vs_include_and_exclude_vs_exclude_only_n": len(decide_only),
        "po_binary": po_kappa_bin,
        "kappa_binary": kappa_bin,
        "guardrail": {
            "guardrail_title_only_ids": len(guardrail_ids),
            "violations": guardrail_check,
            "ok": guardrail_ok,
        },
        "kit_reconciliation": {
            "majority_count": rec["majority_count"],
            "ties": len(rec["ties"]),
            "fleiss_kappa": rec["fleiss_kappa"],
        },
        "reconciled_include": inc_k,
        "reconciled_decided": inc_z,
        "include_rate_point": round(inc_k / inc_z, 4) if inc_z else None,
        "include_rate_wilson95": [round(lo, 4), round(hi, 4)],
        "projected_full_corpus_includes_14150": round(projected),
        "pilot_records": pilot_recs,
    }
    (CAL / "v03_scr1_pilot_reconciliation.json").write_text(
        json.dumps(recon, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# SCR1 pilot — human lead confirmation packet (Pass-1 suggestions ONLY)",
        "",
        f"Pilot slices: batches 0001–0006; decision file record pairs reconciled: {inc_z}",
        f"Dual raw agreement: {recon['agreement_pct']}%; Cohen κ (binary): {kappa_bin}",
        f"Guardrail (abstract-null UAV+weed titles kept PENDING): {'OK' if guardrail_ok else 'VIOLATED'}",
        "",
        "Every row needs the human research lead's firm decision; agent outputs are",
        "suggestions under Option C (100% human confirmation), not final state.",
        "",
        "| batch | screening_id | A1 | A1 reason | A2 | A2 reason | Suggested |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in sorted(pilot_recs):
        r = pilot_recs[s]
        lines.append(
            f"| {r['batch']} | {s} | {r['A1']} | {r['A1_reason']} | {r['A2']} | {r['A2_reason']} | {r['suggested_action']} |"
        )
    (CAL / "v03_scr1_human_confirmation_packet_pilot.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    summary = {
        k: recon[k]
        for k in (
            "shared_decided",
            "missing_from_A1",
            "missing_from_A2",
            "agreement_pct",
            "kappa_binary",
            "shared_include_agreement",
            "reconciled_include",
            "reconciled_decided",
            "include_rate_point",
            "include_rate_wilson95",
            "projected_full_corpus_includes_14150",
            "kit_reconciliation",
            "guardrail",
        )
    }
    (DRIVERS / "v03_scr1_reconcile_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
