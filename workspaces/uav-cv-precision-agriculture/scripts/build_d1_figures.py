"""Generate D1 figure assets with matplotlib (PNG, 150 dpi) under synthesis/figures/.

Figures:
1. fig1_prisma_2020_flow.png  - PRISMA 2020 flow diagram (identification -> included)
2. fig2_year_distribution.png - publication year bar 2018-2026
3. fig3_family_distribution.png - architecture family bar
4. fig4_dataset_reuse.png     - single-use vs shared datasets
5. fig5_edge_throughput.png   - embedded true-edge FPS by board
6. fig6_ro_bias_heatmap.png   - QUADAS-2-adapted risk levels per domain
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "synthesis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
REC = json.loads((BASE / "literature/extraction/merged/records.json").read_text(encoding="utf-8"))

BLUE = "#08306b"; MID = "#2171b5"; LIGHT = "#c6dbef"; RED = "#ca0020"; GREY = "#444"
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans",
                     "axes.spines.top": False, "axes.spines.right": False})

# --- Figure 1: PRISMA 2020 flow ---
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")


def box(x, y, w, h, head, sub, fc=LIGHT, fs=11):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.08",
                                fc=fc, ec="#333", lw=1.2))
    ax.text(x + w / 2, y + h - 0.34, head, ha="center", va="top", fontsize=fs, fontweight="bold")
    ax.text(x + w / 2, y + h / 2 - 0.1, sub, ha="center", va="center", fontsize=fs - 1)


def arrow(x1, y1, x2, y2, color="#333"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                                 lw=1.4, color=color))


ax.text(1.0, 9.6, "IDENTIFICATION", ha="left", fontsize=13, fontweight="bold", color=BLUE)
box(0.6, 7.6, 2.8, 1.1, "Records identified", "n = 1,837")
box(5.6, 7.6, 2.8, 1.1, "Duplicate records removed", "n = 349")
arrow(3.4, 8.15, 5.6, 8.15)
box(0.6, 5.6, 2.8, 1.1, "Records screened (title/abstract)", "n = 1,488")
arrow(3.4, 7.7, 3.4, 6.7)
ax.text(9.45, 6.1, "Records excluded\nn = 1,338", ha="right", va="center", fontsize=10, color=GREY)
arrow(3.4, 6.7, 9.4, 6.15, color=RED)

ax.text(1.0, 5.4, "SCREENING & RETRIEVAL", ha="left", fontsize=13, fontweight="bold", color=BLUE)
box(0.6, 3.6, 2.8, 1.1, "Reports sought for retrieval", "n = 150")
arrow(3.4, 5.7, 3.4, 4.7)
box(5.6, 3.6, 2.8, 1.1, "Reports not retrieved", "n = 12\n(paywalled/restricted)")
arrow(3.4, 4.7, 5.6, 4.15, color=RED)
box(0.6, 1.6, 2.8, 1.1, "Reports assessed for eligibility", "n = 138")
arrow(3.4, 3.7, 3.4, 2.7)
ax.text(9.45, 2.0, "Excluded at full-text verification\nn = 44\n(non-verifiable metric/retrieval)", ha="right", va="center", fontsize=10, color=GREY)
arrow(3.4, 2.7, 9.4, 2.15, color=RED)

box(0.6, 0.1, 2.8, 1.0, "Studies included in quantitative synthesis", "n = 94  (audited corpus)", fc="#c7e9c0")
arrow(3.4, 1.7, 3.4, 1.1)
fig.tight_layout()
fig.savefig(OUT / "fig1_prisma_2020_flow.png", dpi=150)
plt.close(fig)

# --- Figure 2: year distribution ---
YEARS = list(range(2018, 2027))
COUNTS = [5, 1, 7, 7, 8, 10, 16, 21, 19]
fig, ax = plt.subplots(figsize=(9, 4.4))
cols = [RED if y >= 2025 else BLUE for y in YEARS]
bars = ax.bar([str(y) for y in YEARS], COUNTS, color=cols, edgecolor="#333", linewidth=0.6)
for b, v in zip(bars, COUNTS):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.4, str(v), ha="center", fontsize=10, fontweight="bold")
ax.set_ylabel("Studies")
ax.set_ylim(0, 25)
ax.text(0.99, 0.96, "19/94 in 2026; 40/94 in 2025-2026", transform=ax.transAxes,
        ha="right", va="top", fontsize=9, color=GREY)
fig.tight_layout(); fig.savefig(OUT / "fig2_year_distribution.png", dpi=150); plt.close(fig)

# --- Figure 3: family distribution ---
FAM = [("CNN", 69, MID), ("Transformer", 10, "#3182bd"), ("Hybrid", 3, "#6baed6"),
       ("Vision-language", 2, "#9ecae1"), ("Dataset-only", 1, LIGHT), ("Unclassified", 9, "#fdae6b")]
labels = [f[0] for f in FAM]; vals = [f[1] for f in FAM]
fig, ax = plt.subplots(figsize=(8.4, 4.0))
bars = ax.barh(labels[::-1], vals[::-1], color=[c for _, _, c in reversed(FAM)], edgecolor="#333", linewidth=0.6)
for b in bars:
    ax.text(b.get_width() + 1, b.get_y() + b.get_height() / 2, str(int(b.get_width())),
            va="center", fontsize=10, fontweight="bold")
ax.set_xlabel("Studies (best-reporting model / backbone)"); ax.set_xlim(0, 80)
ax.text(0.99, 0.05, "79/94 (84%) derive from convolutional families", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=9, color=GREY)
fig.tight_layout(); fig.savefig(OUT / "fig3_family_distribution.png", dpi=150); plt.close(fig)

# --- Figure 4: dataset reuse ---
labels = ["Single-study datasets", "Shared (≥2 studies)"]
vals = [83, 5]
fig, ax = plt.subplots(figsize=(6.4, 4.2))
colours = ["#1a9641", RED]
b = ax.bar(labels, vals, color=colours, edgecolor="#333", linewidth=0.6, width=0.55)
for bb, v in zip(b, vals):
    ax.text(bb.get_x() + bb.get_width() / 2, v + 0.4, str(v), ha="center", fontsize=11, fontweight="bold")
ax.set_ylabel("Distinct datasets of 88"); ax.set_ylim(0, 92)
ax.text(0.03, 0.98, "Reused sets: WeedsGalore ×3; WeedMap, CoFly-WeedDB\nand two self-collected UAV sets ×2 (94 records)", transform=ax.transAxes,
        ha="left", va="top", fontsize=9, color=GREY)
fig.tight_layout(); fig.savefig(OUT / "fig4_dataset_reuse.png", dpi=150); plt.close(fig)

# --- Figure 5: embedded true-edge throughput ---
EMB_SET = frozenset({  # canonical embedded true-edge cohort (rq2_edge_tables.md Table B1)
    "SCI-000084", "SCI-000149", "SCI-000286", "SCI-000346", "SCI-000440",
    "SCI-000565", "SCI-000669", "SCI-000683", "SCI-000810", "SCI-000852",
    "SCI-000968", "SCI-001085", "SCI-001173", "SCI-001292", "SCI-001333",
})


def mval(edge, key):
    v = edge.get(key)
    return (v or {}).get("value") if isinstance(v, dict) else v


rows = []
lat_only = []
for sid in EMB_SET:
    r = {x["workspace_id"]: x for x in REC}[sid]
    e = r.get("edge") or {}
    dev = (e.get("device") or "").strip()
    fps = mval(e, "fps")
    if fps is None:
        lat_only.append((sid, dev, mval(e, "latency_ms")))
    else:
        rows.append((sid, dev[:34], fps))
rows.sort(key=lambda t: t[2])
fig, ax = plt.subplots(figsize=(8.6, 5.6))
ypos = range(len(rows))
ax.barh(list(ypos), [f for _, _, f in rows], color=BLUE, edgecolor="#333", linewidth=0.6, height=0.62)
ax.set_yticks(list(ypos)); ax.set_yticklabels([f"{s} {d}" for s, d, _ in rows], fontsize=8.5)
ax.set_xlabel("Measured throughput (FPS)"); ax.invert_yaxis()
for i, (_, _, f) in enumerate(rows):
    ax.text(f + 1.2, i, f"{f:.1f}", va="center", fontsize=9, fontweight="bold")
ax.text(0.99, 0.02, "n = 13 with measured FPS; INT8/FP16 on Jetson Orin/RK3588 reach real-time (>20 FPS)",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=GREY)
if lat_only:
    lat_only.sort(key=lambda t: t[2])
    ax.text(0.99, 0.10, "2 further cohort studies report latency only: " +
            ", ".join(f"{s} {v:g} ms" for s, _, v in lat_only) + " -> 15-study embedded cohort",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5, color=GREY)
fig.tight_layout(); fig.savefig(OUT / "fig5_edge_throughput.png", dpi=150); plt.close(fig)

# --- Figure 6: RoB heatmap ---
DOM = [("Selection / patient", [71, 20, 3]), ("Index condition (data + labels)", [10, 72, 12]),
       ("Flow / timing", [37, 56, 1]), ("Reporting / nature of target", [18, 32, 44]),
       ("Overall (QUADAS-2)", [2, 77, 15])]
LEVELS = ["Low", "Unclear", "High / n/a"]
import numpy as np
M = np.array([c for _, c in DOM], dtype=float) / 94.0
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ax.imshow(M, cmap="YlGnBu", vmin=0, vmax=1)
ax.set_xticks(range(3)); ax.set_xticklabels(LEVELS)
ax.set_yticks(range(len(DOM))); ax.set_yticklabels([d for d, _ in DOM])
for i in range(len(DOM)):
    for j in range(3):
        ax.text(j, i, f"{DOM[i][1][j]}", ha="center", va="center", fontsize=12,
                fontweight="bold", color="white" if M[i, j] > 0.45 else "#111")
ax.set_title("Risk of bias across QUADAS-2-adapted domains (n = 94)")
fig.tight_layout(); fig.savefig(OUT / "fig6_ro_bias_heatmap.png", dpi=150); plt.close(fig)

print("figures written:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))
print("embedded cohort rows:", len(rows))