"""SCR1 progress snapshot — mutual include counts over surviving decisions."""

import json
from pathlib import Path

SCR = Path(r"workspaces\uav-crop-weed-v03\calibration_v03\screening_scr1")


def load(fam):
    out = {}
    batches = []
    for i in range(1, 284):
        fp = SCR / "decisions" / f"batch_{i:04d}_decisions_{fam}.json"
        if not fp.exists():
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        batches.append(i)
        for d in data["decisions"]:
            out[d["screening_id"]] = d["decision"]
    return out, batches


a1, b1 = load("A1")
a2, b2 = load("A2")
both_batches = sorted(set(b1) & set(b2))
sh = set(a1) & set(a2)
mut_inc = sum(1 for s in sh if a1[s] == "INCLUDE" and a2[s] == "INCLUDE")
only_a1 = sum(1 for s in sh if a1[s] == "INCLUDE" and a2[s] != "INCLUDE")
only_a2 = sum(1 for s in sh if a2[s] == "INCLUDE" and a1[s] != "INCLUDE")
pend_any = sum(1 for s in sh if a1[s] == "PENDING" or a2[s] == "PENDING")
dec = [
    s for s in sh if a1[s] in ("INCLUDE", "EXCLUDE") and a2[s] in ("INCLUDE", "EXCLUDE")
]
print(
    f"A1 batches done: {len(b1)}   A2 batches done: {len(b2)}   both: {len(both_batches)}"
)
print(f"A1 records: {len(a1)}   A2 records: {len(a2)}   shared: {len(sh)}")
print()
print("=== CURRENT MUTUAL SNAPSHOT (suggestions only, NOT final) ===")
print(f"mutual INCLUDE          : {mut_inc}")
print(f"INCLUDE one-sided (A1)  : {only_a1}")
print(f"INCLUDE one-sided (A2)  : {only_a2}")
print(f"PENDING (either agent)  : {pend_any}")
if dec:
    rate = mut_inc / len(dec)
    print(f"mutually decided INC/EXC: {len(dec)}")
    print(f"mutual include rate     : {rate * 100:.2f}%")
    print(f"run-rate extrapolation to 14150: ~{round(rate * 14150)}")
