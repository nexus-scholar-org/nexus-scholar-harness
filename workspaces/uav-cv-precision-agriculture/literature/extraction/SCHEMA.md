# Extraction Schema Contract — Dual-Route Comparison

This document is the SINGLE source of truth for the structured-data extraction of the
94-study clean corpus. **Route A (batch parallel) and Route B (sequential + validation)
MUST emit records conforming to this exact schema.** Comparative analysis is only as good
as the schema fidelity.

## Goal
For each study, extract two families of quantitative facts:

- **QUALITY (RQ1):** DL pixel-level segmentation accuracy of UAV crop/weed imagery
  (mIoU, mPA, F1, Dice, PA, per-class values).
- **EDGE (RQ2):** on-device inference performance (FPS, latency, power, model size,
  device, precision, resolution).

## Canonicity rules (CRITICAL)
1. **All accuracy metrics are stored as FRACTIONS in [0,1].** If the paper reports
   `89.41%`, store `"value": 0.8941`. The unit field is always `"fraction"` for these.
2. **Every metric object must include `"reported"`** (bool). If the metric is not
   reported anywhere, `"reported": false` and `value: null`. Do NOT omit the metric key.
3. **`"normalized_digits"`** optional integer (default 3): how many decimals to round for
   comparison (avoid fp jitter).
4. **Provenance is mandatory.** For every reported value, include:
   - `"quote"`: the raw text snippet from the markdown containing the value (max 300 chars)
   - `"section"`: the markdown heading/section where the value appears
   - `"table"`: table caption or null
5. **`fps` values are stored as numbers (frames/sec). Latency as ms. Power as W.**
   Params as millions (`params_M`). GFLOPS as numbers.
6. **If a quantity is ambiguous, still extract your best reading** and set
   `"confidence"` in the metric object to < 0.7, with a note in `"ambiguity"`.

## Record shape (one JSON object per study)

```json
{
  "workspace_id": "SCI-000482",
  "study": {
    "title": "Full original title",
    "short_title": "Trimmed title <= 90 chars",
    "year": 2021,
    "venue": "Journal / Conf / Preprint",
    "extracted_md": "2019_You_....md"
  },
  "segmentation": {
    "task": "semantic|instance|both",
    "domain": "crop-weed|crop-only|weed-only|crop-row|other-veg",
    "models_tested": ["ModelA", "ModelB"],
    "best_model": "ModelA",
    "dataset": {
      "name": "Dataset name or 'self-collected UAV'",
      "uav_collected": true,
      "images": 1234,
      "resolution_gsp_m": 0.07,
      "flight_altitude_m": 10,
      "note": ""
    },
    "classes": ["background", "crop", "weed"],
    "num_classes": 3,
    "backbone": "",
    "metrics": {
      "mIoU":   {"reported": true, "value": 0.8941, "unit": "fraction", "normalized_digits": 3, "confidence": 0.95, "quote": "…", "section": "Table 4", "table": "Table 4", "ambiguity": ""},
      "mPA":    {"reported": false, "value": null, "unit": "fraction", "normalized_digits": 3, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
      "F1":     {"reported": false, "value": null, "unit": "fraction", "normalized_digits": 3, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
      "Dice":   {"reported": false, "value": null, "unit": "fraction", "normalized_digits": 3, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
      "PA":     {"reported": false, "value": null, "unit": "fraction", "normalized_digits": 3, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
      "weed_F1":{"reported": false, "value": null, "unit": "fraction", "normalized_digits": 3, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
      "crop_F1":{"reported": false, "value": null, "unit": "fraction", "normalized_digits": 3, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""}
    }
  },
  "edge": {
    "reported": false,
    "device": "",
    "precision": "",
    "resolution_input": null,
    "framework": "",
    "fps":      {"reported": false, "value": null, "unit": "fps",  "normalized_digits": 2, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
    "latency_ms":{"reported": false, "value": null, "unit": "ms", "normalized_digits": 2, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
    "power_w":  {"reported": false, "value": null, "unit": "W",  "normalized_digits": 2, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
    "params_M": {"reported": false, "value": null, "unit": "millions", "normalized_digits": 2, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""},
    "gflops":   {"reported": false, "value": null, "unit": "GFLOPS", "normalized_digits": 2, "confidence": 0.0, "quote": "", "section": "", "table": "", "ambiguity": ""}
  },
  "extraction": {
    "route": "A|B",
    "route_batch": "A-1",
    "extractor": "agent id",
    "verified_md_read": true,
    "confidence_overall": 0.9,
    "issues": [],
    "extracted_at": "2026-09-04T00:00:00Z"
  }
}
```

## Metric value policy (which value to record)
- **Segmentation metrics:** record the value for the BEST-performing reported model
  consistent with `best_model`, read from the paper's own headline result (test set).
  If the paper reports both per-class and mean, take the mean; note per-class in
  `weed_F1`/`crop_F1` only when explicitly a distinct reported metric (not derived by you).
- **FPS/latency/power:** record the value on the PRIMARY edge device targeted by the
  paper (or the Jetson-family device if multiple). If latency is reported as ms/image,
  convert to FPS = 1000/latency ONLY if the paper itself does not report FPS, and then
  `"derived": true` in your `issues` list. Never invent values.
- **Dataset resolution/altitude:** only when stated; else null. Include `uav_collected`
  true when imagery is from UAV, false for bench/ground or unspecified.

## Anticipated ambiguity handling
- Paper reports both `%` and `fraction`: always store fraction.
- Value for network with different input resolution: keep the headline paper claim.
- If two tables contradict, prefer the main results table (usually the last, most recent,
  or "comparison" table), note the discrepancy in `issues`.
- If the metric is given only in a figure (no table), set `reported=true`, value from
  your reading, `confidence` <= 0.6, `ambiguity` = "read from figure".

## Required file-out
- Route A: one JSON file per batch under `literature/extraction/route_A/`, named
  `route_A_batch1.json` … containing a JSON **array** of records (one per study).
- Route B: one JSON file per study under `literature/extraction/route_B/`, named
  `route_B_<workspace_id>.json`, plus a top-level `route_B_index.json` array mapping
  workspace_id -> filename.
- Every study in the clean corpus must appear **exactly once** in each route's output.
- Verify before declaring done: open your output files, confirm valid JSON, confirm each
  required metric key present on every record, confirm workspace_ids match the clean set.