"""Apply quote-backed record corrections from the full-text read-through (batches 00-08).

Every fix cites the extraction record + verbatim source line in the audit trail.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
P = BASE / "literature/extraction/merged/records.json"
recs = json.loads(P.read_text(encoding="utf-8"))
by = {r["workspace_id"]: r for r in recs}

def set_metric(rec, key, **kw):
    m = (rec.get("segmentation") or {}).get("metrics") or {}
    if key in m and isinstance(m[key], dict):
        m[key].update({k: v for k, v in kw.items() if v is not None})

# 1) SCI-000005: PA was actually OA (Overall Accuracy); P/R/F1/OA/kappa row quote.
r = by["SCI-000005"]
set_metric(r, "PA", reported=False, value=None, unit=None,
           ambiguity="READTHROUGH: 0.946 is OA (overall accuracy) per quote 'P R F1 OA kappa ... 0.851 0.843 0.847 0.946 0.794'; source reports P=0.851, R=0.843. PA field was mislabeled as pixel accuracy.")

# 2) SCI-000708: mIoU 0.753 belongs to U-Net TrueRGN cross-domain (orthophoto->frame), not SynthFakeRGN.
r = by["SCI-000708"]
set_metric(r, "mIoU",
           ambiguity="READTHROUGH: 0.753 is U-Net TrueRGN cross-domain generalization example (trained on orthophoto, evaluated on frame data); the record's attributed best_model SynthFakeRGN is not the source of this value. SynthFakeRGN cross-domain mIoU is not stated in text.")

# 3) SCI-001333: model input 352x480; 800 was dataset tile width (650x800).
r = by["SCI-001333"]
e = r.get("edge") or {}
e["resolution_input"] = "352x480"
e["resolution_note"] = "READTHROUGH: model input resized to 352x480 ('the input images were resized to 352 x 480 pixels'); earlier 800 came from cropped dataset tile image size 650x800, not a model input."

# 4) SCI-000962: gflops/fps/latency replicated the LW-Unet column; correct to LW-Segnet per efficiency table.
r = by["SCI-000962"]
e = r.get("edge") or {}
if isinstance(e.get("gflops"), dict):
    e["gflops"].update({"value": 36.8, "confidence": 0.95,
                        "quote": "LW-Segnet 693.4 36.8 11.0 117.5 LW-Unet 603.7 32.1 10.6 143.3",
                        "ambiguity": "READTHROUGH: extracted 32.1 was LW-Unet's row; LW-Segnet (best model) gflops is 36.8."})
if isinstance(e.get("fps"), dict):
    e["fps"].update({"value": 11.0, "unit": "FPS", "confidence": 0.95,
                     "quote": "LW-Segnet 693.4 36.8 11.0 117.5 LW-Unet 603.7 32.1 10.6 143.3",
                     "ambiguity": "READTHROUGH: 143.3 was LW-Unet's row; LW-Segnet fps is 11.0."})
if isinstance(e.get("latency_ms"), dict):
    e["latency_ms"].update({"value": 117.5, "unit": "ms", "confidence": 0.95,
                            "quote": "LW-Segnet 693.4 36.8 11.0 117.5 LW-Unet 603.7 32.1 10.6 143.3",
                            "ambiguity": "READTHROUGH: latency not previously extracted; LW-Segnet row is 117.5 ms."})
else:
    e["latency_ms"] = {"reported": True, "value": 117.5, "unit": "ms", "confidence": 0.95,
                       "quote": "LW-Segnet 693.4 36.8 11.0 117.5 LW-Unet 603.7 32.1 10.6 143.3",
                       "ambiguity": "READTHROUGH: latency not previously extracted; LW-Segnet row is 117.5 ms."}
e["note"] = "READTHROUGH: gflops/fps/latency corrected from LW-Unet column to LW-Segnet column per source efficiency table."

# 5) SCI-000040: latency 96.8 is derived (1000/10.33 FPS), not stated in source.
r = by["SCI-000040"]
e = r.get("edge") or {}
if isinstance(e.get("latency_ms"), dict):
    e["latency_ms"].update({"ambiguity": "READTHROUGH: 96.8 ms is derived as 1000/FPS (10.33); source reports FPS only, no explicit latency."})

# 6) precision implied-not-stated (SCI-000669/683/852) - flag on the edge record.
for wid in ("SCI-000669", "SCI-000683", "SCI-000852"):
    e = by[wid].get("edge") or {}
    e["precision_note"] = "READTHROUGH: FP32 not stated in source; implied PyTorch default, treat as LOW_CONF."

P.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
print("record corrections applied:", [k for k in ("SCI-000005", "SCI-000708", "SCI-001333", "SCI-000962", "SCI-000040") if k in by])
print("PA count (was 37):", sum(1 for r in recs if (r.get('segmentation') or {}).get('metrics', {}).get('PA', {}).get('reported')))