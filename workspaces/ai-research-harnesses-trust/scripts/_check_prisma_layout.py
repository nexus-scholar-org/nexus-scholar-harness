"""Verify the PRISMA flow figure: measure each text block's rendered extent and
compare against its enclosing box in data coordinates. Exit 0 if all fit."""

import sys

import matplotlib
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

matplotlib.use("Agg")

X_WORLD = 100.0
FIG_W_IN = 8.4
PT_PER_UNIT = FIG_W_IN / X_WORLD * 72.0  # points per data-unit (x)


def measure(text, fontsize):
    prop = FontProperties(family="DejaVu Sans", size=fontsize)
    path = TextPath((0, 0), text, prop=prop)
    wpt = path.get_extents().width
    return wpt / 72.0 * X_WORLD / FIG_W_IN  # width in data units


# (text, fontsize, box_x, box_w) in data units
def check(text, fontsize, box_x, box_w, pad=2.0):
    w = measure(text, fontsize)
    avail = box_w - pad
    left_needed = w
    ok = left_needed <= avail
    print(
        f"{'OK ' if ok else 'OVER'} width {w:5.1f}u vs avail {avail:5.1f}u | "
        f"{text.splitlines()[0][:38]}"
    )
    return ok


blocks = [
    # identification (left box x=6 w=58 ; right x=70 w=26)
    ("Records identified from 5 sources\n(OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv;\nbioRxiv-track via indexing)\nn = 250   (50 per source, query Q001)", 8.6, 6, 58, 6.0),
    ("Records removed\nbefore screening\nn = 11", 8.6, 70, 26, 5.0),
    # screening (left x=6 w=58 ; right x=70 w=26)
    ("Records screened by 4 independent AI screeners\n(12 agent-in-the-loop batches)\nn = 239", 8.6, 6, 58, 6.0),
    ("Records excluded at\ntitle/abstract\nn = 181", 8.6, 70, 26, 5.0),
    # eligibility (left x=6 w=58 ; right x=70 w=26)
    ("OA full-text harvested & validated\n64 PDFs; 57 included studies contribute claims\n(1 empty abstract, claim-void)", 8.6, 6, 58, 6.0),
    ("Phase-4 trust streams (4)\nretraction 48 (0 flagged);\nCOI 47; open-science 32;\nrisk-of-bias attestation", 8.3, 70, 26, 5.0),
    # included (x=18 w=60)
    ("Studies included in living review 1.0\nn = 58 included  /  181 excluded\n510 claims (RQ1 166 / RQ2 132 / RQ3 212);\n95 consensus clusters; 47 fully Phase-4 certified", 8.6, 18, 60, 8.0),
]

all_ok = all(check(*b) for b in blocks)
if all_ok:
    print("ALL PRISMA TEXT BLOCKS FIT")
    sys.exit(0)
print("SOME TEXT BLOCKS OVERFLOW")
sys.exit(1)