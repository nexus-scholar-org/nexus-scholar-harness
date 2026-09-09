"""Build the full-text read-through manifest for the remaining (non-anchor) corpus studies.

Source of truth: literature/extraction/merged/records.json. For each study we emit every
numeric claim the manuscript/tables cite (metrics + edge runtime), so a fresh reader can
re-verify each value against the extracted fulltext under extracted/<study.extracted_md>.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REC = json.loads((BASE / "literature/extraction/merged/records.json").read_text(encoding="utf-8"))
EXTRACTED = BASE / "extracted"

VERIFIED = {
    "SCI-000129", "SCI-000180", "SCI-000371", "SCI-000083", "SCI-000092", "SCI-000145",
    "SCI-000505", "SCI-000548", "SCI-000637", "SCI-000650", "SCI-000754", "SCI-000898",
    "SCI-001081", "SCI-001096", "SCI-001153", "SCI-001210", "SCI-001292", "SCI-001305",
    "SCI-001371", "SCI-001413", "SCI-000067",
}

FAMILY = {"CNN": 0, "Transformer": 0, "Hybrid": 0}
def family_of(r):
    seg = r.get("segmentation") or {}
    model = (seg.get("best_model") or "").strip() or (seg.get("backbone") or "").strip()
    ml = model.lower()
    if any(k in ml for k in ("segformer", "vit", "swin", "transformer", "mask2former",
                            "mobilevit", "deit", "transunet", "dpt", "hierarchical vision")):
        return "Transformer"
    if any(k in ml for k in ("hybrid", "cvt", "conformer", "unet+transformer")):
        return "Hybrid"
    return "CNN"

def metric_items(seg):
    out = []
    for key, m in (seg.get("metrics") or {}).items():
        if not isinstance(m, dict) or m.get("value") is None:
            continue
        item = {
            "kind": "metric", "key": key, "value": m.get("value"), "unit": m.get("unit"),
            "confidence": m.get("confidence"), "ambiguity": m.get("ambiguity"),
            "quote_in_records": (m.get("quote") or "")[:300],
        }
        out.append(item)
    return out

def edge_items(edge):
    out = []
    if not edge:
        return out
    dev = (edge.get("device") or "").strip()
    if dev:
        out.append({"kind": "edge_field", "key": "device", "value": dev})
    for field in ("precision", "resolution_input", "framework"):
        v = edge.get(field)
        if v is not None and ("".join(str(v).split()) or v):
            out.append({"kind": "edge_field", "key": field, "value": str(v)[:80]})
    for key, label in (("fps", "fps"), ("latency_ms", "latency_ms"), ("power_w", "power_w"),
                       ("params_M", "params_M"), ("gflops", "gflops")):
        v = edge.get(key)
        v = (v or {}).get("value") if isinstance(v, dict) else v
        if v is not None:
            out.append({"kind": "edge_metric", "key": key, "value": v,
                        "quote_in_records": ((edge.get(key) or {}).get("quote") or "")[:300]
                        if isinstance(edge.get(key), dict) else ""})
    return out

manifest = []
skipped = []
for r in REC:
    wid = r.get("workspace_id")
    if wid in VERIFIED:
        continue
    study = r.get("study") or {}
    md = study.get("extracted_md") or ""
    md = md.replace("\\", "/")
    md_file = EXTRACTED / md if not Path(md).is_absolute() else Path(md)
    if not md_file.exists() or md_file.suffix != ".md":
        skipped.append((wid, md, str(md_file.exists())))
        continue
    seg = r.get("segmentation") or {}
    item = {
        "workspace_id": wid,
        "title": (study.get("title") or "")[:200],
        "year": study.get("year"),
        "venue": (study.get("venue") or "")[:120],
        "extracted_md": md_file.as_posix(),
        "attributed_model": (seg.get("best_model") or "").strip() or "(data-only)",
        "attributed_backbone": (seg.get("backbone") or "").strip() or "",
        "family": family_of(r),
        "dataset_name": ((seg.get("dataset") or {}).get("name") or "").strip() or "",
        "num_classes": seg.get("num_classes"),
        "verify": metric_items(seg) + edge_items(r.get("edge") or {}),
    }
    manifest.append(item)

out = BASE / "synthesis" / "fulltext_audit"
out.mkdir(parents=True, exist_ok=True)
(out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

BATCH = 9
for i in range(0, len(manifest), BATCH):
    idx = i // BATCH
    (out / f"batch_{idx:02d}.json").write_text(
        json.dumps({"batch": idx, "studies": manifest[i:i + BATCH]}, indent=1), encoding="utf-8")

stats = {k: sum(1 for m in manifest if m["family"] == k) for k in FAMILY}
print(f"manifest studies: {len(manifest)} (skipped: {len(skipped)} {skipped[:5]})")
print("batches written:", len(range(0, len(manifest), BATCH)), "| family split:", stats)
print("total verify items:", sum(len(m['verify']) for m in manifest))