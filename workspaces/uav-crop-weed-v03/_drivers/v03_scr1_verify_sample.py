"""SCR1 verification-sample generator — 10% of the 12,357 mutual-EXCLUDE pairs.

Systematic deterministic sample: sorted mutual-EXCLUDE screening_ids, every
10th taken (k=10) -> 1,236 records; blinded 50-record packs under
screening_scr1/verification_lane/packs/ in the same view3 format as the T3
lane (no decisions, reasons, or confidences; moderator-visibility identical to
what A1/A2 saw). The T4 verifiers must not learn that the current expectation
is EXCLUDE; a PENDING/INCLUDE suggestion from T4 does NOT overturn the
closed pair — it routes to the human lead adjudication sheet as a verified
exceptional case.

Outputs (new): verification_lane/packs/pack_*.view3.json + manifest.
"""

import json
import sys
from collections import Counter
from pathlib import Path

DRIVERS = Path(__file__).resolve().parent
sys.path.insert(0, str(DRIVERS))
from v03_scr1_schema import normalize_row  # noqa: E402
from v03_scr1_reconcile2 import load_family, lane_key  # noqa: E402

ROOT = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness-demo")
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
SCR = CAL / "screening_scr1"
VIEWS = SCR / "moderation_views"
VL = SCR / "verification_lane"
PACKS = VL / "packs"
PACKS.mkdir(parents=True, exist_ok=True)


def main():
    a1 = load_family("A1")
    a2 = load_family("A2")
    mutual_exc = [
        s for s in sorted(a1) if a1[s]["decision"] == a2[s]["decision"] == "EXCLUDE"
    ]
    sample = mutual_exc[9::10]  # every 10th (k=10), deterministic
    print(f"mutual_EXCLUDE {len(mutual_exc)} -> systematic 10% sample {len(sample)}")

    view_recs = {}
    for n in range(1, 284):
        v = json.loads((VIEWS / f"batch_{n:04d}.view.json").read_text(encoding="utf-8"))
        for r in v["records"]:
            view_recs[r["screening_id"]] = r

    packs = {}
    for i, sid in enumerate(sample):
        packs.setdefault(i // 50 + 1, []).append(sid)

    for pn, sids in sorted(packs.items()):
        recs = []
        for sid in sids:
            vr = view_recs[sid]
            recs.append(
                {
                    "screening_id": sid,
                    "title": vr.get("title"),
                    "abstract": vr.get("abstract"),
                    "abstract_effectively_null": vr.get("abstract_effectively_null"),
                    "moderation_redacted": vr.get("moderation_redacted"),
                    "moderation_terms": vr.get("moderation_terms"),
                }
            )
        fp = PACKS / f"pack_{pn:04d}.view3.json"
        fp.write_text(
            json.dumps(
                {
                    "role": "T4 exclusion-verification third-rater, blinded",
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

    manifest = {f"pack_{p:04d}": len(s) for p, s in sorted(packs.items())}
    (CAL / "v03_scr1_verify_sample_manifest.json").write_text(
        json.dumps(
            {
                "scheme": "systematic every-10th over sorted mutual-EXCLUDE pairs",
                "k": 10,
                "mutual_exclude_total": len(mutual_exc),
                "sample_n": len(sample),
                "packs": manifest,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"packs: {len(packs)} | totals check: {sum(manifest.values())}")


if __name__ == "__main__":
    main()
