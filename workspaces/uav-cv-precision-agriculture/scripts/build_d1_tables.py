"""Compile journal-ready tables for D1 manuscript embedding.

Table 1. Metric reporting rates (RQ1)                  -> §3.3
Table 2. Embedded true-edge cohort (RQ2, n=15)         -> §3.4
Table 3. QUADAS-2-adapted risk-of-bias tallies (RQ3)   -> §3.5

Writes synthesis/d1_tables.md (single source for manuscript embedding).
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "synthesis" / "d1_tables.md"
REC = json.loads((BASE / "literature/extraction/merged/records.json").read_text(encoding="utf-8"))
BY = {r["workspace_id"]: r for r in REC}

EMB_SET = frozenset({  # canonical embedded true-edge cohort (rq2_edge_tables.md Table B1)
    "SCI-000084", "SCI-000149", "SCI-000286", "SCI-000346", "SCI-000440",
    "SCI-000565", "SCI-000669", "SCI-000683", "SCI-000810", "SCI-000852",
    "SCI-000968", "SCI-001085", "SCI-001173", "SCI-001292", "SCI-001333",
})


def mval(edge, key):
    v = edge.get(key)
    return (v or {}).get("value") if isinstance(v, dict) else v


rows = []
for sid in EMB_SET:
    r = BY[sid]
    e = r.get("edge") or {}
    dev = (e.get("device") or "").strip()
    fps, lat = mval(e, "fps"), mval(e, "latency_ms")
    rows.append([sid, dev, fps, lat, mval(e, "precision") or "not stated",
                 mval(e, "resolution_input")])
rows.sort(key=lambda t: -(t[2] if t[2] else 1000 / t[3]))
assert len(rows) == 15, f"expected 15 embedded rows, got {len(rows)}"

T1 = """#### Table 1. Metric reporting rates across the 94-study corpus (RQ1)
| Metric | Studies reporting | Share of 94 | Note |
|---|---|---|---|
| mIoU | 64 | 68% | dominant single metric |
| F1 | 32 | 34% | incl. class-level crop/weed F1 |
| Dice | 19 | 20% | |
| Pixel accuracy (PA) | 36 | 38% | after quote-backed relabel of one OA mis-record |
| Mean pixel accuracy (mPA) | 10 | 11% | |
| Weed-class F1 | 5 | 5% | crop-level F1: 8 |
| ≥2 numeric metrics | 59 | 63% | reporting-rich minority |
| ≥1 numeric ambiguity flag | 73 | 78% | human reconciliation required before citation |
| Flight altitude | 59 | 63% | median 10 m |
| Ground sampling distance | 50 | 53% | of dataset records |
"""

T2_hdr = """#### Table 2. Embedded true-edge cohort (RQ2, n = 15): measured runtime on embedded-class hardware
| Study | Device | FPS | Latency (ms) | Precision | Input (px) |
|---|---|---|---|---|---|
"""
T2_rows = []
for sid, dev, fps, lat, prec, res in rows:
    T2_rows.append(f"| {sid} | {dev} | {fps if fps else '—'} | {lat if lat else '—'} | {prec} | {res} |")
T2 = T2_hdr + "\n".join(T2_rows) + "\n"

T3 = """#### Table 3. Risk of bias (QUADAS-2-adapted), n = 94 (RQ3)
| Domain | Low | Unclear | High / n/a |
|---|---|---|---|
| Patient / selection | 71 | 20 | 3 |
| Index condition (data + labels) | 10 | 72 | 12 |
| Flow / timing | 37 | 56 | 1 |
| Reporting / nature of target | 18 | 32 | 44 (n/a) |
| **Overall** | **2** | **77** | **15** |
"""

doc = "\n".join([
    "# D1 manuscript tables (compiled, journal-ready)",
    "",
    "Compiled 2026-09-09 from `literature/extraction/merged/records.json` and",
    "`synthesis/rq1_metric_reporting.md`. Identical text is embedded in the manuscript",
    "(`d1_manuscript_draft.md`); keep in sync via `scripts/build_d1_tables.py`.",
    "",
    T1, T2, T3,
])
OUT.write_text(doc, encoding="utf-8")
print("wrote", OUT.name)
print([f"[{r[0]}] {r[1][:40]} FPS={r[2]} ms={r[3]}" for r in rows])