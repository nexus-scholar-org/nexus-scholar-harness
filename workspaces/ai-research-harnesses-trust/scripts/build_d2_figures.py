"""Build D3 manuscript figures (trust-provenance method paper).

Figure 3: Head-to-head claim verification rate + coverage (RAG baseline vs verbatim).
Figure 4: Corpus-scope compliance (studies represented / out-of-scope citations / debates).
Figure 2: Verbatim verification repair loop (v1 -> after repair -> final).
Figure 5: Per-RQ verification rates with Wilson 95% CIs.

Shared clean style; data identical to the audited stats (stats_audit.md).
"""

from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

WS = Path(__file__).resolve().parents[3] / "workspaces" / "ai-research-harnesses-trust"
OUT = WS / "synthesis" / "figures_d2"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "legend.frameon": False,
    }
)

GOLD = "#b45309"   # amber-700 (RAG baseline)
TEAL = "#0f766e"   # teal-700   (verbatim)
GREY = "#6b7280"


def _label(ax, bars, fmt=lambda v: str(int(v)), dy=1.5):
    for b in bars:
        h = b.get_height()
        if h <= 0:
            continue
        ax.text(
            b.get_x() + b.get_width() / 2, h + dy, fmt(h),
            ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#111827",
        )


def fig1():
    """Verification pass rate + corpus coverage (Figure 3 in manuscript)."""
    labels = ["RAG baseline", "Verbatim\nmulti-agent ledger"]
    verified = [39, 510]
    total = [90, 510]
    studies = [25, 57]
    incl = 58
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.4), width_ratios=[1.05, 1.0])

    palms1 = [v / t * 100 for v, t in zip(verified, total)]
    b1 = ax1.bar(labels, palms1, color=[GOLD, TEAL], width=0.5)
    _label(ax1, b1, fmt=lambda v: f"{v:.1f}%")
    ax1.set_ylim(0, 115)
    ax1.set_ylabel("Verification pass rate (%)")
    ax1.set_title("Claims passed the trust gate", fontweight="bold", fontsize=11)
    ax1.set_xticks(range(len(labels))); ax1.set_xticklabels(labels)
    ax1.grid(axis="y", alpha=0.25, lw=0.7)
    for i, (v, t) in enumerate(zip(verified, total)):
        ax1.text(i, v / t * 100 - 10, f"{v}/{t}", ha="center", fontsize=8.5,
                 color="white", fontweight="bold")

    b2 = ax2.bar(labels, studies, color=[GOLD, TEAL], width=0.5, alpha=0.95)
    _label(ax2, b2, fmt=lambda v: f"{v:.0f} studies", dy=0.8)
    ax2.axhline(incl, color=GREY, ls="--", lw=1.0)
    ax2.text(1.02, incl + 1.5, f"included corpus: {incl}", color=GREY, fontsize=9)
    ax2.set_ylim(0, 66)
    ax2.set_ylabel("Distinct studies represented")
    ax2.set_title("Corpus coverage", fontweight="bold", fontsize=11)
    ax2.set_xticks(range(len(labels))); ax2.set_xticklabels(labels)
    ax2.grid(axis="y", alpha=0.25, lw=0.7)
    ax2.annotate("44/58 included studies\ninvisible to RAG", xy=(0.0, 25),
                 xytext=(-0.12, 0.55), textcoords="axes fraction",
                 fontsize=8.8, color=GREY, ha="left", va="bottom")

    fig.tight_layout()
    fig.savefig(OUT / "fig1_verification_versus_coverage.png")
    fig.savefig(OUT / "fig1_verification_versus_coverage.pdf")
    plt.close(fig)


def fig2():
    """Corpus scope + debates (Figure 4 in manuscript)."""
    cats = ["Out-of-scope studies\ncited", "Included studies\nwith zero claims", "Active debates\nsurfaced"]
    baseline = [11, 44, 0]
    verbatim = [0, 0, 7]
    x = np.arange(len(cats))
    w = 0.34
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    b1 = ax.bar(x - w / 2, baseline, w, color=GOLD, label="RAG baseline")
    b2 = ax.bar(x + w / 2, verbatim, w, color=TEAL, label="Verbatim multi-agent ledger")
    _label(ax, b1)
    _label(ax, b2)
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylabel("Count")
    ax.set_title("Corpus-scope & debate structure", fontweight="bold", fontsize=11)
    ax.set_ylim(0, 52)
    ax.grid(axis="y", alpha=0.25, lw=0.7)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_xlim(x[0] - 0.9, x[-1] + 0.9)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_scope_and_debates.png")
    fig.savefig(OUT / "fig2_scope_and_debates.pdf")
    plt.close(fig)


def fig3():
    """Verbatim verification repair loop (Figure 2 in manuscript)."""
    stages = ["Initial\nextraction", "After 4 repair\niterations", "Final verified\nledger"]
    fails = [156, 0, 0]
    passed = [510 - f for f in fails]
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    x = range(len(stages))
    b1 = ax.bar([i - 0.18 for i in x], passed, 0.36, color=TEAL, label="Passed verbatim gate (≥ 0.90)")
    b2 = ax.bar([i + 0.18 for i in x], fails, 0.36, color=GOLD, label="Failed the gate")
    _label(ax, b1)
    _label(ax, b2)
    ax.set_xticks(list(x)); ax.set_xticklabels(stages, fontsize=9)
    ax.set_ylabel("Claims (of 510)")
    ax.set_ylim(0, 560)
    ax.set_title("Verbatim verification repair loop (auditable at every stage)", fontweight="bold", fontsize=11)
    ax.grid(axis="y", alpha=0.25, lw=0.7)
    ax.legend(loc="upper left", fontsize=9)
    for i, f in enumerate(fails):
        if f:
            ax.text(i + 0.18, f + 8, str(f), ha="center", fontsize=9.5, fontweight="bold", color="#111827")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_verification_repair_loop.png")
    fig.savefig(OUT / "fig3_verification_repair_loop.pdf")
    plt.close(fig)


def fig4():
    """Per-RQ verification rates (Figure 5 in manuscript)."""
    rq = ["RQ1", "RQ2", "RQ3"]
    rate = [36.7, 46.7, 46.7]
    lo = [21.9, 30.2, 30.2]
    hi = [54.5, 63.9, 63.9]
    xs = range(len(rq))
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.errorbar(
        xs, rate,
        yerr=[[rate[i] - lo[i] for i in xs], [hi[i] - rate[i] for i in xs]],
        fmt="o", color=GOLD, capsize=5, lw=2, ms=8, markeredgewidth=1,
        markeredgecolor="white", label="RAG baseline (Wilson 95% CI)",
    )
    ax.plot(xs, [100.0] * 3, "s", color=TEAL, ms=9, label="Verbatim ledger (510/510, ≥ 0.90)")
    ax.axhline(43.3, color=GREY, ls=":", lw=1.0)
    ax.text(2.32, 43.3, "RAG pooled 43.3%", color=GREY, fontsize=9, va="center", ha="right")
    for x, v in zip(xs, rate):
        ax.text(x, v + 3.2, f"{v}%", ha="center", fontsize=9, fontweight="bold", color="#111827")
    ax.set_xticks(list(xs)); ax.set_xticklabels(rq)
    ax.set_ylim(0, 120)
    ax.set_ylabel("Verification pass rate (%)")
    ax.set_title("Per-research-question verification rates", fontweight="bold", fontsize=11)
    ax.grid(axis="y", alpha=0.25, lw=0.7)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_per_rq_rates.png")
    fig.savefig(OUT / "fig4_per_rq_rates.pdf")
    plt.close(fig)


def main():
    fig1()
    fig2()
    fig3()
    fig4()
    print("D3 figures written to", OUT)


if __name__ == "__main__":
    main()