"""SCR1 provider composition + review dashboard.

Q1: provider mix of completed vs remaining batches (the user's question).
Q2: self-contained local review dashboard HTML (no deps, file://-safe).

Outputs:
  - _drivers/v03_scr1_provider_composition.json
  - calibration_v03/v03_scr1_review_dashboard.html
"""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCR = Path(r"workspaces\uav-crop-weed-v03\calibration_v03\screening_scr1")
CAL = SCR.parent
TAGS = ("openalex", "crossref", "arxiv", "pubmed", "semanticscholar")


def batch_records(n):
    return json.loads((SCR / f"batch_{n:04d}.json").read_text(encoding="utf-8"))


def fam_map(fam):
    out = {}
    for n in range(1, 284):
        fp = SCR / "decisions" / f"batch_{n:04d}_decisions_{fam}.json"
        if not fp.exists():
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if len(data.get("decisions", [])) != 50:
            continue
        out[n] = {d["screening_id"]: d["decision"] for d in data["decisions"]}
    return out


a1, a2 = fam_map("A1"), fam_map("A2")

prov_total = Counter()
prov_screened_both = Counter()
prov_remaining = Counter()
records = []
batch_rows = []
state_done_one = Counter()
for n in range(1, 284):
    b = batch_records(n)
    state = (
        "both"
        if (n in a1 and n in a2)
        else ("A1" if n in a1 else ("A2" if n in a2 else "pending"))
    )
    state_done_one[state] += 1
    pcs = []
    for r in b["records"]:
        provs = r.get("providers") or r.get("provider") or []
        if isinstance(provs, str):
            provs = [provs]
        elif isinstance(provs, dict):
            provs = list(provs.keys())
        elif isinstance(provs, (list, tuple)):
            provs = [str(p) for p in provs]
        provs = [p.lower() for p in provs if p]
        primary = provs[0] if provs else "unknown"
        for t in TAGS:
            if t in provs:
                prov_total[t] += 1
                if state == "both":
                    prov_screened_both[t] += 1
                else:
                    prov_remaining[t] += 1
        if state not in ("both", ""):
            for t in TAGS:
                if t in provs:
                    prov_remaining[t] += 1 if state else 0
        d_a1 = (a1.get(n) or {}).get(r["screening_id"])
        d_a2 = (a2.get(n) or {}).get(r["screening_id"])
        pcs.append(
            {
                "id": r["screening_id"],
                "t": (r.get("title") or "")[:110],
                "y": r.get("year"),
                "p": ",".join(provs) or primary,
                "an": r.get("abstract_effectively_null"),
                "a1": d_a1,
                "a2": d_a2,
            }
        )
    mut_inc = sum(1 for d in pcs if d["a1"] == "INCLUDE" and d["a2"] == "INCLUDE")
    batch_rows.append(
        {
            "n": n,
            "state": state,
            "records": len(pcs),
            "mutual_inc": mut_inc,
            "inc_a1": sum(1 for d in pcs if d["a1"] == "INCLUDE"),
            "inc_a2": sum(1 for d in pcs if d["a2"] == "INCLUDE"),
            "pend": sum(1 for d in pcs if d["a1"] == "PENDING" or d["a2"] == "PENDING"),
        }
    )
    records.extend(pcs)

comp = {
    "note": "containment across provider lists (merged docs carry several tags); primary provider not counted separately here",
    "universe_by_tag": dict(prov_total),
    "screened_both_by_tag": dict(prov_screened_both),
    "remaining_by_tag": dict(prov_remaining),
    "batch_states": dict(state_done_one),
    "screened_both_leaves": sum(
        br["records"] for br in batch_rows if br["state"] == "both"
    ),
}
(CAL.parent / "_drivers" / "v03_scr1_provider_composition.json").write_text(
    json.dumps(comp, indent=2), encoding="utf-8"
)
print(json.dumps(comp, indent=2))

html_t = Path(__file__).with_name("v03_scr1_dashboard_template.html")
html = html_t.read_text(encoding="utf-8")
html = html.replace("__BATCHES__", json.dumps(batch_rows, ensure_ascii=False))
html = html.replace("__RECORDS__", json.dumps(records, ensure_ascii=False))
out = CAL / "v03_scr1_review_dashboard.html"
out.write_text(html, encoding="utf-8")
print("WROTE dashboard:", out, f"({out.stat().st_size / 1e6:.1f} MB)")
