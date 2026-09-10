"""Generate XeLaTeX manuscripts from the committed markdown sources.

Each deliverable gets a self-contained `latex/<name>/` folder: main.tex (pandoc
fragment wrapped in a fontspec preamble), a header.tex, and figure paths that
point back to the committed originals (single source of truth).

Usage:  uv run python scripts/generate_latex.py
Build:  cd latex/<name> && xelatex -output-directory=build main.tex (x2)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage{fontspec}
\setmainfont{Times New Roman}
\usepackage{amsmath,amssymb}
\usepackage{textcomp}
\usepackage{newunicodechar}
\newunicodechar{⇒}{\ensuremath{\Rightarrow}}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}
\usepackage{calc} % for calculating minipage widths
\usepackage{caption}
\captionsetup[table]{skip=6pt}
\newcounter{none} % for unnumbered tables
\usepackage{etoolbox}
\makeatletter
\patchcmd\longtable{\par}{\if@noskipsec\mbox{}\fi\par}{}{}
\makeatother
\providecommand{\tightlist}{%
  \setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\usepackage{graphicx}
\makeatletter
\newsavebox\pandoc@box
\newcommand*\pandocbounded[1]{% scales image to fit in text height/width
  \sbox\pandoc@box{#1}%
  \Gscale@div\@tempa{\textheight}{\dimexpr\ht\pandoc@box+\dp\pandoc@box\relax}%
  \Gscale@div\@tempb{\linewidth}{\wd\pandoc@box}%
  \ifdim\@tempb\p@<\@tempa\p@\let\@tempa\@tempb\fi% select the smaller of both
  \ifdim\@tempa\p@<\p@\scalebox{\@tempa}{\usebox\pandoc@box}%
  \else\usebox{\pandoc@box}%
  \fi%
}
\def\fps@figure{htbp}
\makeatother
\usepackage{float}
\usepackage{caption}
\usepackage[margin=2.4cm]{geometry}
\usepackage{xcolor}
\usepackage[colorlinks=true,linkcolor=Black,urlcolor=Blue,citecolor=Black]{hyperref}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\leftmark}
\fancyhead[R]{\small\thepage}
\begin{document}
"""

DELIVERABLES = [
    {
        "name": "d1",
        "dir": ROOT / "workspaces" / "uav-cv-precision-agriculture" / "latex" / "d1",
        "source": ROOT / "workspaces" / "uav-cv-precision-agriculture" / "synthesis" / "d1_manuscript_draft.md",
        "rewrites": [("figures/", "../../synthesis/figures/")],
    },
    {
        "name": "d2",
        "dir": ROOT / "workspaces" / "ai-research-harnesses-trust" / "latex" / "d2",
        "source": ROOT / "workspaces" / "ai-research-harnesses-trust" / "reports" / "manuscript_d2.md",
        "rewrites": [("../synthesis/figures_d2/", "../../synthesis/figures_d2/")],
    },
    {
        "name": "d3",
        "dir": ROOT / "workspaces" / "ai-research-harnesses-trust" / "latex" / "d3",
        "source": ROOT / "workspaces" / "ai-research-harnesses-trust" / "reports" / "manuscript_draft.md",
        "rewrites": [
            ("../synthesis/figures/", "../../synthesis/figures/"),
            ("../synthesis/figures_d2/", "../../synthesis/figures_d2/"),
        ],
    },
    {
        "name": "d4",
        "dir": ROOT / "workspaces" / "ai-research-harnesses-trust" / "latex" / "d4",
        "source": ROOT / "workspaces" / "ai-research-harnesses-trust" / "reports" / "D4_SOFTWARE_PAPER_SCOPE.md",
        "rewrites": [],
    },
    {
        "name": "thesis",
        "dir": ROOT / "workspaces" / "ai-research-harnesses-trust" / "latex" / "thesis",
        "source": ROOT / "workspaces" / "ai-research-harnesses-trust" / "reports" / "THESIS_ASSEMBLY.md",
        "rewrites": [],
    },
]


def pandoc_fragment(src: Path) -> str:
    result = subprocess.run(
        [
            "pandoc",
            str(src),
            "-f",
            "markdown",
            "-t",
            "latex",
            "--top-level-division=section",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def main() -> int:
    for item in DELIVERABLES:
        out_dir = item["dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        body = pandoc_fragment(item["source"])
        for old, new in item["rewrites"]:
            body = body.replace(old, new)
        (out_dir / "main.tex").write_text(
            PREAMBLE + body + "\n\\end{document}\n", encoding="utf-8"
        )
        print(f"generated {out_dir / 'main.tex'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())