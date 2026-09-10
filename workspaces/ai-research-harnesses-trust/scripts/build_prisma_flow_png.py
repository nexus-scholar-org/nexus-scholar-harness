"""Render the PRISMA-ScR flow of information as a publication-grade PNG + PDF.

PRISMA-2020-style layout drawn with matplotlib: identification / screening /
eligibility / included bands, main-left + removed-right flow, explicit arrows.
Box sizes are computed from the rendered text extents so text never overflows.
Counts are identical to the machine-validated vector figure
(fig_prisma_scr_flow.svg) and the flow table in prisma_scr_flow.md.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
from matplotlib.textpath import TextPath

WS = Path(__file__).resolve().parents[3] / "workspaces" / "ai-research-harnesses-trust"
OUT = WS / "synthesis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

BLUE = "#2c5f8a"
RED = "#9c3d3d"
GREY = "#6b7280"
BG = {"ident": "#eef4fb", "screen": "#effaf1", "elig": "#fdedec", "incl": "#f4f6f7"}
BGL = {"ident": "#c5d5ea", "screen": "#b8dcc4", "elig": "#e4b9b6", "incl": "#c5d5ea"}

# canvas geometry
FIG_W = 8.4
FIG_H = 10.2
X0, X1, Y0, Y1 = 0.0, 100.0, 0.0, 118.0
PT2U = (Y1 - Y0) / (FIG_H * 72.0)


def text_w_u(text, fs):
    prop = FontProperties(family="DejaVu Sans", size=fs)
    wpt = TextPath((0, 0), text, prop=prop).get_extents().width
    return wpt / 72.0 * (X1 - X0) / FIG_W


def box_h_u(nlines, fs, ls=1.35, pad=1.6):
    line = fs * ls * PT2U
    return nlines * line + pad


def box(ax, x, y, w, h, fc="white", ec="#1f2937", lw=1.2, r=1.2):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0.02,rounding_size={r}",
            fc=fc, ec=ec, lw=lw, zorder=2,
        )
    )


def band(ax, y, h, key, label):
    box(ax, 2, y, 96, h, fc=BG[key], ec=BGL[key], lw=1.0, r=2.2)
    ax.text(5, y + h - 2.2, label, fontsize=11, fontweight="bold", color="#374151",
            va="center", zorder=3)


def tb(ax, x, y, lines, fs=9.0, ls=1.35):
    ax.text(x, y, lines, fontsize=fs, va="top", ha="left", zorder=3, linespacing=ls)


def arrow(ax, x0, y0, x1, y1):
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops={"arrowstyle": "-|>", "lw": 1.6, "color": "#374151",
                    "mutation_scale": 16},
    )


def main():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.axis("off")

    # ---- IDENTIFICATION ----
    ident_box_h = box_h_u(4, 8.6)
    band_top = Y1 - 4.0
    band_h = ident_box_h + 3.2
    bid = band_top - band_h
    band(ax, bid, band_h, "ident", "Identification")

    box_w = 62.0
    x = 6.0
    by = bid + 1.0
    box(ax, x, by, box_w, ident_box_h)
    tb(ax, x + 2.4, by + ident_box_h - 0.7,
       "Records identified from 5 sources\n"
       "(OpenAlex, Semantic Scholar, Crossref, PubMed,\n"
       "arXiv; bioRxiv-track via indexing)\n"
       "n = 250   (50 per source, query Q001)")

    rx = 72.0
    rbox_w = 24.0
    rbox_h = box_h_u(3, 8.6)
    rbox_y = by + (ident_box_h - rbox_h) / 2
    box(ax, rx, rbox_y, rbox_w, rbox_h)
    tb(ax, rx + 2.0, rbox_y + rbox_h - 0.7,
       "Records removed\nbefore screening\nn = 11")
    arrow(ax, x + box_w, by + ident_box_h / 2, rx, rbox_y + rbox_h / 2)

    # ---- SCREENING ----
    scr_box_h = box_h_u(3, 8.6)
    band_scr_top = bid - 3.4
    bscr = band_scr_top - (scr_box_h + 3.2)
    band(ax, bscr, band_scr_top - bscr, "screen", "Screening")
    sx = 6.0
    sy = bscr + 1.0
    box(ax, sx, sy, box_w, scr_box_h)
    tb(ax, sx + 2.4, sy + scr_box_h - 0.7,
       "Records screened by 4 independent AI screeners\n"
       "(12 agent-in-the-loop batches)\n"
       "n = 239")
    rbox_h2 = box_h_u(3, 8.6)
    ry2 = sy + (scr_box_h - rbox_h2) / 2
    box(ax, rx, ry2, rbox_w, rbox_h2)
    tb(ax, rx + 2.0, ry2 + rbox_h2 - 0.7,
       "Records excluded at\ntitle/abstract\nn = 181")
    arrow(ax, sx + box_w, sy + scr_box_h / 2, rx, ry2 + rbox_h2 / 2)

    # ---- ELIGIBILITY ----
    elig_box_h = box_h_u(3, 8.6)
    elig_lh = box_h_u(4, 8.3)
    band_elig_top = bscr - 3.4
    belig = band_elig_top - (max(elig_box_h, elig_lh) + 3.2)
    band(ax, belig, band_elig_top - belig, "elig", "Eligibility (trust verification)")
    ex = 6.0
    ey = belig + 1.0
    box(ax, ex, ey, box_w, elig_box_h)
    tb(ax, ex + 2.4, ey + elig_box_h - 0.7,
       "OA full-text harvested & validated\n"
       "64 PDFs; 57 included studies contribute claims\n"
       "(1 empty abstract, claim-void)")
    rbox_h3 = box_h_u(4, 8.3)
    ry3 = ey + (elig_box_h - rbox_h3) / 2
    box(ax, rx, ry3, rbox_w, rbox_h3)
    tb(ax, rx + 2.0, ry3 + rbox_h3 - 0.7,
       "Phase-4 trust streams (4)\n"
       "retraction 48 (0 flagged);\n"
       "COI 47; open-science 32;\n"
       "risk-of-bias attestation",
       fs=8.3)
    arrow(ax, ex + box_w, ey + elig_box_h / 2, rx, ry3 + rbox_h3 / 2)

    # ---- INCLUDED ----
    inc_box_h = box_h_u(4, 8.6)
    band_inc_top = belig - 3.4
    binc = band_inc_top - (inc_box_h + 3.2)
    band(ax, binc, band_inc_top - binc, "incl", "Included")
    cx = 18.0
    cw = 60.0
    cy = binc + 1.0
    box(ax, cx, cy, cw, inc_box_h, ec=BLUE, lw=1.8)
    tb(ax, cx + 2.4, cy + inc_box_h - 0.7,
       "Studies included in living review 1.0\n"
       "n = 58 included  /  181 excluded\n"
       "510 claims (RQ1 166 / RQ2 132 / RQ3 212);\n"
       "95 consensus clusters; 47 fully Phase-4 certified")

    # ---- vertical flow arrows ----
    arrow(ax, 35, by + ident_box_h / 2, 35, band_scr_top - 0.5)
    arrow(ax, 35, sy + scr_box_h / 2, 35, band_elig_top - 0.5)
    arrow(ax, 35, ey + elig_box_h / 2, 35, band_inc_top - 0.5)

    # footnote
    ax.text(5, binc - 3.0,
            "Version 1.0, corpus finalized 2026-09-09. Full accounting: 250 identified − 11 duplicates = 239 screened.",
            fontsize=8.2, color=GREY)

    fig.tight_layout()
    fig.savefig(OUT / "fig_prisma_scr_flow.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "fig_prisma_scr_flow.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("PRISMA flow PNG + PDF written to", OUT)


if __name__ == "__main__":
    main()