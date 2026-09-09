"""Resolve the 39 CAVEAT_EXC06_FULLTEXT_VERIFICATION provisional inclusions.

Decision rule (from adjudication): a provisional study is CONFIRMED if fulltext/abstract
shows a QUANTITATIVE segmentation benchmark metric; EXCLUDED under EXC-06 otherwise.
This script only PRODUCES a resolution note (synthesis/provisional_resolution.md) — it
does NOT mutate included.json / project.json / any pipeline artifact.

Buckets:
  CONFIRMED                    — numeric segmentation metric verified in extracted fulltext
  CONFIRMED_PENDING_FULLTEXT   — metric token(s) in abstract/segmentation-strong title,
                                 fulltext missing (PDF not retrieved)
  EXCLUDE_TOPIC                — clearly outside the UAV crop/weed segmentation scope
  REVIEW_REQUIRED              — ambiguous; human loop needed before manuscript inclusion
"""
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
rows = json.loads((BASE / "literature/included.json").read_text(encoding="utf-8"))
RECORDS = json.loads((BASE / "literature/extraction/merged/records.json").read_text(encoding="utf-8"))
RID = {r["workspace_id"]: r for r in RECORDS}

prov = [r for r in rows
        if (r.get("screening") or {}).get("provisional_reason") == "CAVEAT_EXC06_FULLTEXT_VERIFICATION"]

OFFTOPIC = ("sidewalk", "crack", "bombard", "traffic", "human search", "time synchronization",
            "amphibious", "wildfire", "forest fire", "urban", "landslide", "building",
            "person re-identification", "corn earworm", "ad hoc", "mars", "anti-drone",
            "surveillance", "insect")
REVIEW = ("cotton weed detection", "active sensing", "cofly", "crop vision navigation", "contextual u-net")
STRONG_SEG = ("semantic segmentation", "instance segmentation", "u-net", "unet", "segnet")
STRONG_DATA = ("dataset", "benchmark")
METRIC_KW = ("m iou", "miou", "iou", "dice", "f1", " mpa", " precision", " recall", " accuracy", " pa ")
DIG = re.compile(r"\d+(?:\.\d+)?\s*%")

def rec_value(wid):
    rec = RID.get(wid)
    if not rec:
        return None, None
    seg = rec.get("segmentation") or {}
    m = seg.get("metrics") or {}
    vals = {k: (v.get("value") if isinstance(v, dict) else v)
            for k, v in m.items() if isinstance(v, dict) and v.get("value") is not None}
    if vals:
        return seg.get("task"), vals
    if seg.get("task") == "semantic":
        return seg.get("task"), {}
    return None, None

out = []
out.append("# Provisional Inclusion Resolution (39 studies — CAVEAT_EXC06_FULLTEXT_VERIFICATION)\n")
out.append("Decision rule: CONFIRMED if a QUANTITATIVE segmentation benchmark metric exists "
           "(fulltext where retrieved, else abstract); EXCLUDED under EXC-06 otherwise. "
           "This is a manuscript-side resolution note; pipeline files are untouched.\n")
out.append("| # | Study | Year | Resolution | Justification |")
out.append("|---|---|---|---|---|")

buckets = {"CONFIRMED": [], "CONFIRMED_PENDING_FULLTEXT": [], "EXCLUDE_TOPIC": [], "EXCLUDE_EXC06": [], "REVIEW_REQUIRED": []}
seen = set()
for r in sorted(prov, key=lambda x: x["workspace_id"]):
    wid = r["workspace_id"]
    seen.add(wid)
    title = (r.get("title") or "")
    year = r.get("year")
    abstract = (r.get("abstract") or "")
    tl = title.lower()
    task, vals = rec_value(wid)
    if task == "semantic" and vals:
        bucket = "CONFIRMED"
        just = "Fulltext extraction: " + ", ".join(f"{k}={v}" for k, v in vals.items())
    elif any(o in tl for o in OFFTOPIC):
        bucket = "EXCLUDE_TOPIC"
        just = f"Off-scope topic ('{title[:70]}') — not UAV crop/weed segmentation."
    elif "excluded under EXC-06" in ((r.get("screening") or {}).get("screening_reasoning") or ""):
        bucket = "EXCLUDE_EXC06"
        just = "Adjudicator statement: no concrete quantitative segmentation metric in fulltext."
    elif any(s in tl for s in STRONG_SEG) or (any(s in tl for s in STRONG_DATA) and any(w in tl for w in ("weed", "crop", "field"))):
        bucket = "CONFIRMED_PENDING_FULLTEXT"
        just = "Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected."
    elif any(o in tl for o in REVIEW):
        bucket = "REVIEW_REQUIRED"
        just = "Likely in scope with metrics not confidently abstracted; fulltext missing."
    elif any(k in abstract.lower() for k in METRIC_KW):
        has_num = bool(DIG.search(abstract)) or bool(re.search(r"\b0\.\d{2,}\b", abstract))
        if has_num:
            bucket = "CONFIRMED_PENDING_FULLTEXT"
            just = "Metric token(s) + numerics in abstract; fulltext not extracted."
        else:
            bucket = "REVIEW_REQUIRED"
            just = "Metric keyword in abstract but no explicit numeric value — verify manually."
    else:
        bucket = "REVIEW_REQUIRED"
        just = "No numeric segmentation metric observable in abstract; no fulltext."
    buckets[bucket].append(wid)
    out.append(f"| {wid} | {title[:70]} | {year} | {bucket} | {just} |")

tbl = out[4:]
body = out[:4]
body.append(f"Counts: CONFIRMED={len(buckets['CONFIRMED'])} | "
            f"CONFIRMED_PENDING_FULLTEXT={len(buckets['CONFIRMED_PENDING_FULLTEXT'])} | "
            f"EXCLUDE_TOPIC={len(buckets['EXCLUDE_TOPIC'])} | EXCLUDE_EXC06={len(buckets['EXCLUDE_EXC06'])} | "
            f"REVIEW_REQUIRED={len(buckets['REVIEW_REQUIRED'])} (of 39 total)\n")
body.append("## Bucket summaries")
for b in ("CONFIRMED", "CONFIRMED_PENDING_FULLTEXT", "EXCLUDE_TOPIC", "EXCLUDE_EXC06", "REVIEW_REQUIRED"):
    body.append(f"\n### {b} ({len(buckets[b])})")
    body.append(", ".join(buckets[b]) if buckets[b] else "—")
body.append("")

(md_base := BASE / "synthesis" / "provisional_resolution.md").write_text(
    "\n".join(body) + "\n" + "\n".join(tbl) + "\n", encoding="utf-8")
print("buckets:", {k: len(v) for k, v in buckets.items()})
print(f"wrote {md_base}")