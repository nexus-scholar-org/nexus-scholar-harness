"""Scaffold RQ1 paired intra-study benchmark tables from the UAV extraction records.

Output: synthesis/rq1_benchmark_tables.md (working manuscript material, not final).
Architecture-family classification is a documented heuristic; UNCLASSIFIED rows are flagged for manual review.
"""
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MATRIX = json.loads((BASE / "synthesis/synthesis_matrix.json").read_text(encoding="utf-8"))
RECORDS = json.loads((BASE / "literature/extraction/merged/records.json").read_text(encoding="utf-8"))

TRANSFORMER_TOK = ("transformer", "vit", "vision transformer", "swin", "segformer", "deit", "beit", "patch embed", "patchmerger", "fastvit")
HYBRID_TOK = ("hybrid",)
CNN_TOK = ("cnn", "u-net", "unet", "u net", "resnet", "deeplab", "vgg", "mobilenet", "yolo", "mask r-cnn", "mask rcnn", "segnet", "densenet", "efficient", "hourglass", "fcn", "linknet", "bisenet", "enet", "dla", "repvgg", "edanet", "convnext", "convmixer")
VLM_TOK = ("qwen", "llava", "llama", "gpt-4", "vlm", "lora", "pp-liteseg")
NO_MODEL_TOK = ("n/a", "no model", "not reported", "dataset-contribution", "dataset paper")

def classify(best_text: str, backbone_text: str = ""):
    b = " ".join((best_text or "", backbone_text or "")).lower()
    if any(x in b for x in NO_MODEL_TOK):
        return "no-model"
    if any(x in b for x in VLM_TOK):
        return "VLM"
    if any(x in b for x in HYBRID_TOK):
        return "Hybrid"
    if any(x in b for x in TRANSFORMER_TOK):
        return "Transformer"
    if any(x in b for x in CNN_TOK):
        return "CNN"
    return "UNCLASSIFIED"

def metric(rec, key):
    v = rec.get("segmentation", {}).get("metrics", {}).get(key, {}).get("value")
    if isinstance(v, bool):
        return None
    return v

def fmt(x, nd=4):
    if x is None:
        return ""
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)

rows = []
for rec in RECORDS:
    wid = rec["workspace_id"]
    seg = rec.get("segmentation", {})
    models_tested = seg.get("models_tested") or []
    best = seg.get("best_model") or ""
    backbone = seg.get("backbone") or ""
    fam = classify(best, backbone)
    m = seg.get("metrics", {})
    mIoU = metric(rec, "mIoU"); f1 = metric(rec, "F1"); dice = metric(rec, "Dice"); wf1 = metric(rec, "weed_F1")
    conf = m.get("mIoU", {}).get("confidence") if m.get("mIoU") else None
    amb = m.get("mIoU", {}).get("ambiguity") or "" if m.get("mIoU") else ""
    rows.append({
        "wid": wid, "fam": fam, "best": best, "n_models": len(models_tested),
        "mIoU": mIoU, "F1": f1, "Dice": dice, "weed_F1": wf1, "conf": conf, "amb": amb,
        "uav": (metric(rec, "mIoU") is not None),
    })

# ---- diagnostics
n_miou = sum(1 for r in rows if r["mIoU"] is not None)
n_f1   = sum(1 for r in rows if r["F1"] is not None)
n_weedf1 = sum(1 for r in rows if r["weed_F1"] is not None)
n_multi = sum(1 for r in rows if r["n_models"] >= 2)
n_uncl  = [r["wid"] for r in rows if r["fam"] == "UNCLASSIFIED"]
n_amb_numeric = sum(1 for r in rows if re.search(r"\d", r["amb"] or ""))
families = {}
for r in rows:
    families.setdefault(r["fam"], 0)
    families[r["fam"]] += 1

# ---- Table A: quasi-paired dataset groups
from collections import defaultdict
by_ds = defaultdict(list)
for rec in RECORDS:
    ds = (rec.get("segmentation", {}).get("dataset") or {}).get("name") or ""
    by_ds[ds].append(rec["workspace_id"])
paired_ds = {ds: ids for ds, ids in by_ds.items() if len(ids) >= 2}

def row_for(wid):
    r = next(x for x in rows if x["wid"] == wid)
    return r

lines = []
lines.append("# RQ1 Bench-Portable Tables (Scaffold) — UAV CV Precision Agriculture\n")
lines.append("Auto-generated from `literature/extraction/merged/records.json` + `synthesis/synthesis_matrix.json`. "
             "Architecture family from a keyword heuristic; every `UNCLASSIFIED` row needs manual verification. "
             "Intra-study variant cells cite the extractor's evidence (`ambiguity`), to be curated into final paired tables.\n")

lines.append(f"## Diagnostics\n- studies = 94 | mIoU reported = {n_miou} | F1 = {n_f1} | weed_F1 = {n_weedf1} | multi-model studies = {n_multi} | ambiguity-with-numbers = {n_amb_numeric}")
lines.append(f"- family counts: {families}")
lines.append(f"- UNCLASSIFIED: {n_uncl}\n")

lines.append("## Table A — quasi-paired dataset benchmark groups (same test bed, >=2 studies)\n")
lines.append("| Dataset | Study | Fam | Best model (reported) | mIoU | F1 | Weed F1 | conf |")
lines.append("|---|---|---|---|---:|---:|---:|---:|")
for ds in sorted(paired_ds, key=lambda d: (-len(paired_ds[d]), d)):
    for wid in sorted(paired_ds[ds]):
        r = row_for(wid)
        lines.append(f"| {ds} | {r['wid']} | {r['fam']} | {r['best'][:70]} | {fmt(r['mIoU'])} | {fmt(r['F1'])} | {fmt(r['weed_F1'])} | {r['conf']} |")

lines.append("\n## Table B — intra-study paired candidates (multiple models tested within one study)\n")
lines.append("| Study | Fam | Models tested | Best (mIoU) | F1 | Extractors' variant evidence (`ambiguity`) |")
lines.append("|---|---|---|---|---:|---|")
for r in sorted(rows, key=lambda x: (x["fam"], x["wid"])):
    if r["n_models"] >= 2:
        rec = next(x for x in RECORDS if x["workspace_id"] == r["wid"])
        variants = " ; ".join((rec.get("segmentation", {}).get("models_tested") or []))
        ev = re.sub(r"\s+", " ", r["amb"])[:240]
        lines.append(f"| {r['wid']} | {r['fam']} | {variants[:90]} | {fmt(r['mIoU'])} | {fmt(r['F1'])} | {ev} |")

lines.append("\n## Table C — rows excluded from the architecture comparison (UNCLASSIFIED / VLM / no-model) — manual review required\n")
lines.append("| Study | Family | best_model | backbone |")
lines.append("|---|---|---|---|")
for wid in n_uncl:
    rec = next(x for x in RECORDS if x["workspace_id"] == wid)
    seg = rec.get("segmentation", {})
    famr = next(r["fam"] for r in rows if r["wid"] == wid)
    lines.append(f"| {wid} | {famr} | {seg.get('best_model','')} | {seg.get('backbone','')} |")

out = BASE / "synthesis" / "rq1_benchmark_tables.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(lines)} lines)")
for h in ("Diagnostics line:", "UNCLASSIFIED count", "paired datasets"):
    pass
print("n_mIoU", n_miou, "n_F1", n_f1, "n_weedF1", n_weedf1, "n_multi_model", n_multi, "family counts", families, "unclassified", n_uncl)