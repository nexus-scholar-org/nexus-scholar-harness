"""Scaffold RQ2 edge-inference tables from the UAV extraction records.

Output: synthesis/rq2_edge_tables.md (working manuscript material, not final).
Defines the 'true-edge' cohort = device reported AND (fps OR latency) measured on real hardware.
"""
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MATRIX = json.loads((BASE / "synthesis/synthesis_matrix.json").read_text(encoding="utf-8"))
RECORDS = json.loads((BASE / "literature/extraction/merged/records.json").read_text(encoding="utf-8"))
M = {r["workspace_id"]: r for r in MATRIX}

def mval(edge, key):
    v = (edge.get(key) or {}).get("value") if isinstance(edge.get(key), dict) else None
    if isinstance(v, bool):
        return None
    return v

def quot(edge, key, n=90):
    e = edge.get(key) or {}
    q = re.sub(r"\s+", " ", e.get("quote") or "") if e.get("quote") else ""
    return q[:n]

def fmt(x, nd=3):
    if x is None:
        return ""
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)

rows = []

def deployment_class(device: str, family: str):
    entok = ("jetson", "orin", "xavier", "nano", "rk358", "tinker", "orange pi",
             "raspberry", "i.mx", "snapdragon", "hisi", "kunlun", "edge tpu")
    embfam = {"jetson tx2", "jetson nano", "jetson agx xavier", "jetson xavier nx",
              "jetson orin", "rockchip rk3588", "tinker board s", "cpu"}
    target_w = ("targets ", "target the", "feasib", "argues", "intended", "paper proposes",
                "proposes deployment", "potential for", "aimed at", "for deployment on")
    d = (f"{device} {family}").lower()
    in_board = any(x in d for x in entok)
    in_target = any(x in d for x in target_w)
    if in_board and in_target and family.lower() not in embfam:
        return "target-edge"
    if in_board:
        return "embedded"
    if family.lower() in embfam and "desktop" not in d:
        return "embedded"
    if "cpu" in d and not any(x in d for x in ("desktop", "pc", "gpu", "geforce", "rtx", "gtx", "titan", "tesla")):
        return "embedded"
    if "cpu" in family.lower():
        return "accelerator"
    if "desktop" in family.lower() or "server" in family.lower() or "gpu" in d:
        return "accelerator"
    return "unspecified"

for rec in RECORDS:
    wid = rec["workspace_id"]
    seg = rec.get("segmentation", {})
    edge = rec.get("edge", {})
    mrow = M[wid]
    fps = mval(edge, "fps"); lat = mval(edge, "latency_ms"); pow_ = mval(edge, "power_w")
    params = mval(edge, "params_M"); gflops = mval(edge, "gflops")
    device = (edge.get("device") or "").strip()
    precision = (edge.get("precision") or "").strip()
    res = edge.get("resolution_input")
    runtime_reported = bool(edge.get("runtime_reported"))
    device_family = (mrow.get("device_family") or "").strip()
    edge_runtime = str(mrow.get("edge_runtime") or "N")
    framework = (edge.get("framework") or "").strip()
    true_edge = bool(device) and (fps is not None or lat is not None)
    dc = deployment_class(device, device_family)
    rows.append({
        "wid": wid, "device": device, "family": device_family, "precision": precision,
        "res": res, "fps": fps, "lat": lat, "power": pow_, "params": params, "gflops": gflops,
        "runtime": runtime_reported, "true_edge": true_edge, "edge_flag": edge_runtime,
        "fps_q": quot(edge, "fps"), "lat_q": quot(edge, "latency_ms"),
        "framework": framework, "dc": dc,
    })

def header_meta():
    return ("Auto-generated from `literature/extraction/merged/records.json` + `synthesis/synthesis_matrix.json`. "
            "True-edge = device reported AND (fps OR latency) measured on hardware. Quote snippets = extraction evidence, to curate in the manuscript.\n")

lines = []
lines.append("# RQ2 Edge-Inference Tables (Scaffold) — UAV CV Precision Agriculture\n")
lines.append(header_meta())

n_dev = sum(1 for r in rows if r["device"])
n_res = sum(1 for r in rows if r["res"])
n_prec = sum(1 for r in rows if r["precision"])
n_fps = sum(1 for r in rows if r["fps"] is not None)
n_lat = sum(1 for r in rows if r["lat"] is not None)
n_true = sum(1 for r in rows if r["true_edge"])
n_params = sum(1 for r in rows if r["params"] is not None)
n_gflops = sum(1 for r in rows if r["gflops"] is not None)
lines.append("## Diagnostics")
lines.append(f"- device reported = {n_dev} | resolution = {n_res} | precision = {n_prec} | fps = {n_fps} | latency = {n_lat} | params = {n_params} | FLOPs = {n_gflops}")
lines.append(f"- true-edge cohort (device + runtime measured) = {n_true}")
lines.append(f"- deployment class: embedded on-device = {sum(1 for r in rows if r['dc']=='embedded')} | desktop/cloud accelerator = {sum(1 for r in rows if r['dc']=='accelerator')} | unspecified = {sum(1 for r in rows if r['dc']=='unspecified')}")
lines.append("- NOTE: the pipeline's earlier `true_edge_studies=15` stat used a stricter definition (embedded-class board only); reconcile one canonical definition before the manuscript.\n")

lines.append("## Table A — all studies with device or runtime information\n")
lines.append("| Study | Device | Family | Prec | Res | FPS | Lat(ms) | W | Params(M) | GFLOPS | evidence (fps/lat) |")
lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---|")
for r in sorted(rows, key=lambda x: (x["device"] == "", x["wid"])):
    if r["device"] or r["fps"] is not None or r["lat"] is not None:
        ev = (r["fps_q"] or r["lat_q"]).replace("|", "/")
        lines.append(f"| {r['wid']} | {r['device'][:28]} | {r['family'][:16]} | {r['precision'][:8]} | {r['res']} | {fmt(r['fps'])} | {fmt(r['lat'],1)} | {fmt(r['power'])} | {fmt(r['params'],2)} | {fmt(r['gflops'],1)} | {ev[:80]} |")

lines.append("\n## Table B — TRUE-EDGE cohort (device + measured inference, split by deployment class)\n")
lines.append(f"### B1 — Embedded on-device (RQ2 core answer set; {sum(1 for r in rows if r['true_edge'] and r['dc']=='embedded')} studies)\n")
lines.append("| Study | Device | Family | Prec | Res | FPS | Lat(ms) | params | evidence |")
lines.append("|---|---|---|---|---:|---:|---:|---:|---|")
for r in sorted(rows, key=lambda x: x["wid"]):
    if r["true_edge"] and r["dc"] == "embedded":
        ev = (r["fps_q"] or r["lat_q"]).replace("|", "/")
        lines.append(f"| {r['wid']} | {r['device'][:32]} | {r['family'][:16]} | {r['precision'][:8]} | {r['res']} | {fmt(r['fps'])} | {fmt(r['lat'],1)} | {fmt(r['params'],2)} | {ev[:100]} |")

lines.append(f"\n### B2 — Desktop/cloud accelerator (measured, but not edge hardware; {sum(1 for r in rows if r['true_edge'] and r['dc']=='accelerator')} studies — auxiliary)\n")
lines.append("| Study | Device | Family | Prec | Res | FPS | Lat(ms) | params |")
lines.append("|---|---|---|---|---:|---:|---:|---:|")
for r in sorted(rows, key=lambda x: x["wid"]):
    if r["true_edge"] and r["dc"] == "accelerator":
        lines.append(f"| {r['wid']} | {r['device'][:32]} | {r['family'][:16]} | {r['precision'][:8]} | {r['res']} | {fmt(r['fps'])} | {fmt(r['lat'],1)} | {fmt(r['params'],2)} |")

lines.append("\n## Table D — TARGET-EDGE (measured on accelerator but paper argues deployment on embedded; flag for careful reading — do NOT cite as on-device evidence)\n")
lines.append("| Study | Device | Family | Prec | Res | FPS | Lat(ms) | evidence |")
lines.append("|---|---|---|---|---:|---:|---:|---|")
for r in sorted(rows, key=lambda x: x["wid"]):
    if r["dc"] == "target-edge":
        ev = (r["fps_q"] or r["lat_q"]).replace("|", "/")
        lines.append(f"| {r['wid']} | {r['device'][:34]} | {r['family'][:16]} | {r['precision'][:8]} | {r['res']} | {fmt(r['fps'])} | {fmt(r['lat'],1)} | {ev[:100]} |")

lines.append("\n## Table C — device deployed but no measured fps/latency (efficiency-only); flag for primary-justification checks\n")
lines.append("| Study | Device | Family | params | note |")
lines.append("|---|---|---|---|---|")
for r in sorted(rows, key=lambda x: x["wid"]):
    if r["device"] and not r["true_edge"]:
        lines.append(f"| {r['wid']} | {r['device'][:30]} | {r['family'][:16]} | {fmt(r['params'],2)} | {r['framework'][:60].replace('|','/')} |")

out = BASE / "synthesis" / "rq2_edge_tables.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(lines)} lines)")
print("n_dev", n_dev, "n_fps", n_fps, "n_lat", n_lat, "n_true_edge", n_true, "n_prec", n_prec, "n_params", n_params)