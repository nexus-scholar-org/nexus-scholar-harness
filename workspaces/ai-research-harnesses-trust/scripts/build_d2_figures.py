"""Build D2 manuscript figures (trust-provenance method paper).

Figure 1: Head-to-head claim verification rate + coverage (RAG baseline vs verbatim).
Figure 2: Corpus-scope compliance (studies represented / out-of-scope citations / debates).
Requires matplotlib (installed in shared venv).
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness\workspaces\ai-research-harnesses-trust")
OUT = WS / "synthesis" / "figures_d2"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

GOLD = "#b8860b"
TEAL = "#1f6f6f"


def fig1():
    labels = ["RAG baseline", "Verbatim pipeline"]
    verified = [39, 510]
    total = [90, 510]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    ax = axes[0]
    bars = ax.bar(labels, [v / t for v, t in zip(verified, total)], color=[GOLD, TEAL], width=0.55)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Verification pass rate")
    ax.set_title("Claims passed the trust gate")
    for bar, v, t in zip(bars, verified, total):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.03,
            f"{v}/{t} = {100*v/t:.1f}%",
            ha="center",
            fontweight="bold",
        )
    ax2 = axes[1]
    studies = [25, 57]
    incl = 58
    bars = ax2.bar(labels, studies, color=[GOLD, TEAL], width=0.55, label="studies represented")
    ax2.axhline(incl, color="dimgray", ls="--", lw=1)
    ax2.text(1.02, incl + 0.5, f"included corpus: {incl}", color="dimgray", fontsize=9)
    ax2.set_ylim(0, 66)
    ax2.set_ylabel("Distinct studies represented")
    ax2.set_title("Corpus coverage")
    ax2.annotate("44/58 included studies\ninvisible to RAG", xy=(2.0, 32), color="dimgray", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_verification_versus_coverage.png", dpi=300)
    fig.savefig(OUT / "fig1_verification_versus_coverage.pdf")
    plt.close(fig)


def fig2():
    cats = ["Out-of-scope studies cited", "Studies with zero claims", "Active debates"]
    baseline = [11, 44, 0]
    verbatim = [0, 0, 7]
    import numpy as np

    x = np.arange(len(cats))
    w = 0.36
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    b1 = ax.bar(x - w / 2, baseline, w, label="RAG baseline", color=GOLD)
    b2 = ax.bar(x + w / 2, verbatim, w, label="Verbatim pipeline", color=TEAL)
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylabel("Count")
    ax.set_title("Corpus-scope & debate structure (lower is better for left two, higher for debates)")
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            if h or bar is not None:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.6, str(int(h)), ha="center")
    ax.legend(frameon=False)
    ax.set_ylim(0, 50)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_scope_and_debates.png", dpi=300)
    fig.savefig(OUT / "fig2_scope_and_debates.pdf")
    plt.close(fig)


def fig3():
    stages = ["v1 initial extraction", "v4 after repair loop", "Final (11 re-cast verbatim)"]
    fails = [156, 11, 0]
    passed = [510 - f for f in fails]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    x = range(len(stages))
    b1 = ax.bar([i - 0.18 for i in x], passed, 0.36, label="Passed verbatim gate", color=TEAL)
    b2 = ax.bar([i + 0.18 for i in x], fails, 0.36, label="Failed the gate", color=GOLD)
    ax.set_xticks(list(x))
    ax.set_xticklabels(stages, fontsize=9)
    ax.set_ylabel("Claims (of 510)")
    ax.set_ylim(0, 540)
    ax.set_title("Verbatim verification repair loop (fix-loop auditable at every stage)")
    for bars in (b1, b2):
        for bar in bars:
            h = int(bar.get_height())
            if h:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 6, str(h), ha="center", fontsize=9)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_verification_repair_loop.png", dpi=300)
    fig.savefig(OUT / "fig3_verification_repair_loop.pdf")
    plt.close(fig)


def fig4():
    rq = ["RQ1", "RQ2", "RQ3"]
    rate = [36.7, 46.7, 46.7]
    lo = [21.9, 30.2, 30.2]
    hi = [54.5, 63.9, 63.9]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    xs = range(len(rq))
    ax.errorbar(
        xs, rate, yerr=[[rate[i] - lo[i] for i in xs], [hi[i] - rate[i] for i in xs]],
        fmt="o", color=GOLD, capsize=5, lw=2, ms=7, label="RAG baseline (Wilson 95% CI)",
    )
    ax.plot(xs, [100] * 3, "s", color=TEAL, ms=8, label="Verbatim pipeline (510/510)")
    ax.axhline(43.3, color="gray", ls=":", lw=1)
    ax.text(2.35, 43.3, "pooled 43.3%", color="gray", fontsize=9, va="center")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(rq)
    ax.set_ylim(0, 115)
    ax.set_ylabel("Verification pass rate (%)")
    ax.set_title("Per-research-question verification rates")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_per_rq_rates.png", dpi=300)
    fig.savefig(OUT / "fig4_per_rq_rates.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    print("D2 figures written to", OUT)