"""Generate D1 figure assets with matplotlib (PNG @300 dpi + vector PDF) under synthesis/figures/.

Figures:
1. fig1_prisma_2020_flow  - PRISMA 2020 flow diagram (identification -> included)
2. fig2_year_distribution - publication year bar 2018-2026
3. fig3_family_distribution - architecture family bar
4. fig4_dataset_reuse     - single-use vs shared datasets
5. fig5_edge_throughput   - embedded true-edge FPS by board
6. fig6_ro_bias_heatmap   - QUADAS-2-adapted risk levels per domain
"""
import json
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "synthesis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
REC = json.loads((BASE / "literature/extraction/merged/records.json").read_text(encoding="utf-8"))
RECBY = {r["workspace_id"]: r for r in REC}

NAVY = "#123A6B"
BLUE = "#1F6FB2"
LBLUE = "#BFD7EE"
RED = "#C5373D"
GREEN = "#227A45"
AMBER = "#C89B3C"
GREY = "#5A5A5A"
PLOT_BG = "#FBFCFF"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "axes.labelsize": 14,
    "axes.labelweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "axes.titlesize": 16,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "figure.facecolor": "white",
    "axes.facecolor": PLOT_BG,
})


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name, "(png@300 + pdf)")


def light_grid(ax, which="y"):
    ax.grid(which, axis=which, color="#D8DEE6", lw=0.9, zorder=0)
    ax.set_axisbelow(True)


def annotate_top(ax, bars, fmt="%d", dy=0.02, fs=12, color="#111"):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_y() + b.get_height() + dy,
                fmt % b.get_height(), ha="center", va="bottom", fontsize=fs,
                fontweight="bold", color=color)


# ---- canonical embedded true-edge cohort (rq2_edge_tables.md Table B1) ----
EMB_SET = frozenset({
    "SCI-000084", "SCI-000149", "SCI-000286", "SCI-000346", "SCI-000440",
    "SCI-000565", "SCI-000669", "SCI-000683", "SCI-000810", "SCI-000852",
    "SCI-000968", "SCI-001085", "SCI-001173", "SCI-001292", "SCI-001333",
})


def mval(edge, key):
    v = edge.get(key)
    return (v or {}).get("value") if isinstance(v, dict) else v


# =====================================================================
# Figure 1 - PRISMA 2020 flow diagram
# =====================================================================
fig, ax = plt.subplots(figsize=(10.5, 11.8))
ax.set_xlim(0, 10); ax.set_ylim(0, 12); ax.axis("off")

PHASE_BAND = "#EEF3FA"


def phase_colour(top, bottom):
    for y in np.linspace(top - 1.62, bottom + 0.18, 4):
        ax.add_patch(plt.Rectangle((0, y), 10, 1.62, fc=PHASE_BAND, ec="none", alpha=0.55, zorder=0))


def box(x, y, w, h, head, sub, fc=LBLUE, text_scale=1.0, head_bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.09",
                                fc=fc, ec="#2B3A4A", lw=1.4, zorder=3))
    ax.text(x + w / 2, y + h - 0.16, head, ha="center", va="top",
            fontsize=13 * text_scale, fontweight="bold" if head_bold else "semibold",
            color="#101820", zorder=4)
    ax.text(x + w / 2, y + h / 2 - 0.05, sub, ha="center", va="center",
            fontsize=12 * text_scale, color="#2B3A4A", zorder=4)


def arrow(x1, y1, x2, y2, color="#2B3A4A", lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=22,
                                 lw=lw, color=color, zorder=2))


def side(x, y, sub, colour=GREY):
    ax.text(x + 0.42, y, sub, ha="left", va="center", fontsize=13, color=colour,
            fontweight="bold", zorder=4)


# ---- IDENTIFICATION ----
phase_colour(12.0, 9.0)
ax.text(0.45, 10.9, "IDENTIFICATION", fontsize=15, fontweight="bold", color=NAVY, zorder=4)
box(0.7, 9.2, 3.4, 1.25, "Records identified from databases", "n = 1,837")
box(5.9, 9.2, 3.4, 1.25, "Duplicate records removed", "n = 349", fc="#F5EEE1")
arrow(4.1, 9.83, 5.9, 9.83)
box(0.7, 7.15, 3.4, 1.25, "Records after duplicates removed", "n = 1,488")
arrow(2.4, 9.2, 2.4, 8.4)

# ---- SCREENING & RETRIEVAL ----
phase_colour(9.0, 6.2)
ax.text(0.45, 8.35, "SCREENING", fontsize=15, fontweight="bold", color=NAVY, zorder=4)
box(0.7, 5.1, 3.4, 1.25, "Records screened (title + abstract)", "n = 1,488")
arrow(2.4, 7.15, 2.4, 6.35)
side(4.7, 5.72, "Excluded at title/abstract\nn = 1,338", colour=RED)
arrow(4.1, 5.72, 4.6, 5.72)

# ---- ELIGIBILITY ----
phase_colour(6.2, 3.4)
ax.text(0.45, 5.55, "ELIGIBILITY", fontsize=15, fontweight="bold", color=NAVY, zorder=4)
box(0.7, 3.05, 3.4, 1.25, "Reports sought for retrieval", "n = 150")
arrow(2.4, 5.1, 2.4, 4.3)
side(4.7, 4.42, "Reports not retrieved\nn = 12", colour=RED)
arrow(4.1, 4.42, 4.6, 4.42)
box(0.7, 1.0, 3.4, 1.25, "Reports assessed for eligibility", "n = 138")
arrow(2.4, 3.05, 2.4, 2.25)
side(4.7, 2.05, "Excluded at full-text verification\nn = 44\n(138 assessed - 94 audited)", colour=RED)
arrow(4.1, 2.25, 4.6, 2.25)

# ---- INCLUDED ----
phase_colour(3.4, 0.0)
ax.text(0.45, 1.6, "INCLUDED", fontsize=15, fontweight="bold", color=GREEN, zorder=4)
box(0.7, 0.15, 3.4, 1.0, "Studies included in quantitative synthesis", "n = 94  (audited corpus)",
    fc="#D9EDDC", text_scale=0.95)
arrow(2.4, 1.0, 2.4, 1.15)

fig.tight_layout()
save(fig, "fig1_prisma_2020_flow")

# =====================================================================
# Figure 2 - publication year distribution
# =====================================================================
YEARS = list(range(2018, 2027))
COUNTS = [5, 1, 7, 7, 8, 10, 16, 21, 19]
fig, ax = plt.subplots(figsize=(9.5, 5.2))
cols = [RED if y >= 2025 else BLUE for y in YEARS]
bars = ax.bar([str(y) for y in YEARS], COUNTS, color=cols, edgecolor="#26323F", linewidth=0.9,
              width=0.68, zorder=3)
annotate_top(ax, bars)
ax.set_ylabel("Studies (n = 94)")
ax.set_xlabel("Publication year")
ax.set_ylim(0, 25)
light_grid(ax, "y")
ax.text(0.015, 0.96, "19/94 (20%) in 2026; 40/94 (43%) in 2025–2026 (red)",
        transform=ax.transAxes, fontsize=11.5, color=GREY, va="top")
fig.tight_layout()
save(fig, "fig2_year_distribution")

# =====================================================================
# Figure 3 - architecture family distribution
# =====================================================================
FAM = [("CNN", 69, BLUE), ("Transformer", 10, "#3B8BBF"), ("Hybrid", 3, "#74B3D8"),
       ("Vision-language", 2, "#A5CCE8"), ("Dataset-only", 1, "#D3E4F2"), ("Unclassified", 9, AMBER)]
labels = [f[0] for f in FAM]; vals = [f[1] for f in FAM]
fig, ax = plt.subplots(figsize=(9.0, 4.6))
bars = ax.barh(labels[::-1], vals[::-1], color=[c for _, _, c in reversed(FAM)],
               edgecolor="#26323F", linewidth=0.9, height=0.6, zorder=3)
for b, v in zip(bars, vals[::-1]):
    ax.text(b.get_width() + 1.2, b.get_y() + b.get_height() / 2, f"{v}  ({v/94*100:.0f}%)",
            va="center", fontsize=12.5, fontweight="bold", color="#111")
ax.set_xlabel("Studies (best-reporting model / backbone)"); ax.set_xlim(0, 84)
light_grid(ax, "x")
ax.text(0.015, 0.98, "79/94 (84%) derive from convolutional families",
        transform=ax.transAxes, fontsize=11.5, color=GREY, va="top")
fig.tight_layout()
save(fig, "fig3_family_distribution")

# =====================================================================
# Figure 4 - dataset reuse
# =====================================================================
labels = ["Single-study\ndatasets", "Shared\n(\u2265 2 studies)"]
vals = [83, 5]
fig, ax = plt.subplots(figsize=(7.0, 5.4))
bars = ax.bar(labels, vals, color=[GREEN, RED], edgecolor="#26323F", linewidth=0.9,
              width=0.5, zorder=3)
annotate_top(ax, bars, dy=1.0)
ax.set_ylabel("Distinct datasets of 88")
ax.set_ylim(0, 95)
light_grid(ax, "y")
ax.text(0.015, 0.98, "Reused sets: WeedsGalore \u00d73; WeedMap, CoFly-WeedDB,\n"
                     "and two self-collected UAV sets \u00d72",
        transform=ax.transAxes, fontsize=11.5, color=GREY, va="top")
fig.tight_layout()
save(fig, "fig4_dataset_reuse")

# =====================================================================
# Figure 5 - embedded true-edge throughput
# =====================================================================
def short_dev(d):
    d = d.replace("NVIDIA ", "").replace("ASUS ", "")
    d = re.split(r"[\\(\u2014;]", d)[0].strip()
    return d or d


rows, lat_only = [], []
for sid in EMB_SET:
    e = RECBY[sid].get("edge") or {}
    dev = (e.get("device") or "").strip()
    fps = mval(e, "fps")
    if fps is None:
        lat_only.append((sid, short_dev(dev), mval(e, "latency_ms")))
    else:
        rows.append((sid, short_dev(dev), fps))
rows.sort(key=lambda t: t[2])
lat_only.sort(key=lambda t: t[2])
fig, ax = plt.subplots(figsize=(9.8, 6.6))
ypos = np.arange(len(rows))
bar_cols = [GREEN if f >= 40 else (AMBER if f >= 20 else BLUE) for _, _, f in rows]
bars = ax.barh(list(ypos), [f for _, _, f in rows], color=bar_cols,
               edgecolor="#26323F", linewidth=0.9, height=0.64, zorder=3)
ax.set_yticks(list(ypos))
ax.set_yticklabels([f"{s}  ·  {d}" for s, d, _ in rows], fontsize=11.5)
ax.set_xlabel("Measured throughput (FPS)"); ax.invert_yaxis()
for i, (_, _, f) in enumerate(rows):
    ax.text(f + 0.9, i, f"{f:.1f}", va="center", fontsize=11.5, fontweight="bold", color="#111")
light_grid(ax, "x")
import matplotlib.patches as mpatches
handles = [mpatches.Patch(color=GREEN, label="\u2265 40 FPS (real-time at 512 px)"),
           mpatches.Patch(color=AMBER, label="20–39.9 FPS (near real-time)"),
           mpatches.Patch(color=BLUE, label="< 20 FPS (below real-time)")]
ax.legend(handles=handles, loc="lower right", fontsize=10.5, frameon=True, framealpha=0.95)
if lat_only:
    ax.text(0.012, 0.06,
            "Latency-only cohort members: " + ", ".join(f"{s} {v:g} ms" for s, _, v in lat_only)
            + "\n(15-study embedded cohort; measurements on physical boards)",
            transform=ax.transAxes, fontsize=10.5, color=GREY, va="bottom")
fig.tight_layout()
save(fig, "fig5_edge_throughput")

# =====================================================================
# Figure 6 - risk-of-bias heatmap (QUADAS-2-adapted)
# =====================================================================
DOM = [("Patient /\nselection", [71, 20, 3]),
       ("Index condition\n(data + labels)", [10, 72, 12]),
       ("Flow /\ntiming", [37, 56, 1]),
       ("Reporting /\nnature of target", [18, 32, 44]),
       ("Overall\n(QUADAS-2)", [2, 77, 15])]
LEVELS = ["Low", "Unclear", "High / n/a"]
M = np.array([c for _, c in DOM], dtype=float) / 94.0
fig, ax = plt.subplots(figsize=(8.6, 5.6))
im = ax.imshow(M, cmap="Blues", vmin=0, vmax=M.max() * 1.08)
ax.set_xticks(range(3)); ax.set_xticklabels(LEVELS, fontsize=12.5)
ax.set_yticks(range(len(DOM))); ax.set_yticklabels([d for d, _ in DOM], fontsize=11.5)
for i in range(len(DOM)):
    for j in range(3):
        txt = f"{DOM[i][1][j]}"
        ax.text(j, i, txt, ha="center", va="center", fontsize=13.5,
                fontweight="bold", color="white" if M[i, j] > 0.42 else "#14304D")
for i in range(1, len(DOM)):
    ax.axhline(i - 0.5, color="white", lw=1.4)
for j in range(1, 3):
    ax.axvline(j - 0.5, color="white", lw=1.4)
ax.set_title("Risk of bias across QUADAS-2-adapted domains\n(n = 94 audited corpus)", pad=14)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cb.set_label("share of studies", fontsize=12)
cb.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
fig.tight_layout()
save(fig, "fig6_ro_bias_heatmap")

print("done: figures written to", OUT)