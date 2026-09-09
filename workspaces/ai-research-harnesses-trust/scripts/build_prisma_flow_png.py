"""Render the PRISMA-ScR flow of information as a publication PNG + PDF.

Mirrors the validated vector figure synthesis/figures/fig_prisma_scr_flow.svg
(whose XML is machine-validated) using the same flow counts read from the
pipeline artifacts (prisma_scr_flow.md §1). Deterministic, reproducible.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

WS = Path(__file__).resolve().parents[3] / "workspaces" / "ai-research-harnesses-trust"
OUT = WS / "synthesis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#eef4fb"
GREEN = "#effaf1"
RED = "#fdedec"
GREY = "#f4f6f7"
INK = "#1a5276"
NEG = "#922B21"


def box(ax, x, y, w, h, fill, edge, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=2.5",
                                fc=fill, ec=edge, lw=lw))


def text(ax, x, y, s, bold=False, fill="black", size=10.5, ha="left"):
    ax.text(x, y, s, fontweight="bold" if bold else "normal", color=fill,
            fontsize=size, va="center", ha=ha, linespacing=1.35)


def main():
    fig, ax = plt.subplots(figsize=(8.6, 9.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # ---- IDENTIFICATION ----
    box(ax, 2, 87, 96, 12, BLUE, "#c5d5ea")
    text(ax, 3.5, 97.2, "Identification", bold=True, size=11)
    box(ax, 6, 88, 48, 9.8, "white", "#333")
    text(ax, 7.2, 93.6, "Records identified from 5 sources", bold=True, size=10)
    text(ax, 7.2, 91.4, "(OpenAlex, Semantic Scholar, Crossref, PubMed,", size=9)
    text(ax, 7.2, 89.6, "arXiv; bioRxiv-track via indexing)", size=9)
    text(ax, 54, 94.0, "n = 250  (50 per source, query Q001)", bold=True, fill=INK, size=10)
    text(ax, 54, 92.0, "literature/raw_search.json", size=8.5, fill="#555555")
    box(ax, 58, 88, 38, 9.8, "white", "#333")
    text(ax, 59.2, 92.4, "Records removed before screening", bold=True, size=10)
    text(ax, 59.2, 90.4, "duplicate removal via DOI +\nnormalized-title dedup", size=9)
    text(ax, 59.2, 89.0, "n = 11", bold=True, fill=NEG, size=10)

    # ---- SCREENING ----
    box(ax, 2, 74, 96, 12, GREEN, "#b8dcc4")
    text(ax, 3.5, 84.2, "Screening", bold=True, size=11)
    box(ax, 28, 75.4, 44, 8, "white", "#333")
    text(ax, 50, 79.3, "Records screened (4 AI screeners, 12 batches)", bold=True, size=9.5, ha="center")
    text(ax, 50, 76.9, "n = 239", bold=True, fill=INK, size=10.5, ha="center")
    box(ax, 28, 74.4, 44, 0.4, "white", "#bbb")

    # ---- ELIGIBILITY (trust verification) ----
    box(ax, 2, 55, 96, 12, RED, "#e4b9b6")
    text(ax, 3.5, 65.2, "Eligibility (trust verification)", bold=True, size=11)
    box(ax, 6, 56.2, 56, 8.4, "white", "#333")
    text(ax, 7.2, 61.3, "OA full-text harvested & validated", bold=True, size=9.5)
    text(ax, 7.2, 59.1, "64 PDFs; 57 included studies contribute claims", size=8.8)
    text(ax, 7.2, 57.3, "(1 empty abstract, claim-void)", size=8.8)
    text(ax, 7.2, 61.3 + 0.4, "n = 64", bold=True, fill=INK, size=9)
    box(ax, 56, 56.2, 40, 8.4, "white", "#333")
    text(ax, 57.2, 61.3, "Phase-4 trust streams (4)", bold=True, size=9.5)
    text(ax, 57.2, 59.1, "retraction 48 checked (0 flagged);", size=8.8)
    text(ax, 57.2, 57.3, "COI 47 scanned; open-science 32 statements", size=8.8)

    # ---- INCLUDED ----
    box(ax, 2, 38, 96, 12, GREY, "#c5d5ea")
    text(ax, 3.5, 48.2, "Included", bold=True, size=11)
    box(ax, 24, 39, 52, 9.8, "white", INK, lw=2.0)
    text(ax, 50, 46.5, "Studies included in living review 1.0", bold=True, fill=INK, size=10.5, ha="center")
    text(ax, 50, 44.3, "n = 58 included / 181 excluded", bold=True, fill=INK, size=10, ha="center")
    text(ax, 50, 42.1, "510 claims (RQ1 166 / RQ2 132 / RQ3 212);", size=9, ha="center")
    text(ax, 50, 40.3, "95 consensus clusters; 47 fully Phase-4 certified", size=9, ha="center")

    # ---- upstream arrows ----
    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops={"arrowstyle": "-|>" , "color": "#555" , "lw": 1.1})

    arrow(50, 87.0, 50, 84.2)     # ident -> screening
    arrow(50, 74.0, 50, 68.2)     # screening -> eligibility
    arrow(50, 55.0, 50, 51.2)     # eligibility -> included
    arrow(50, 88.0 - 0.2, 50, 99.0 - 0.2)  # top

    # footnote
    ax.text(3.5, 35.6,
            "Version 1.0, corpus finalized 2026-09-09. Deduplication accounting: 250 − 11 = 239 screened.",
            fontsize=8.5, color="#555555")

    fig.tight_layout()
    fig.savefig(OUT / "fig_prisma_scr_flow.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "fig_prisma_scr_flow.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("PRISMA flow PNG + PDF written to", OUT)


if __name__ == "__main__":
    main()