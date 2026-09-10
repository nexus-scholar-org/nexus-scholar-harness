"""Structural QA for rendered manuscript artifacts (no visual inspection).

Checks that the DOCX contains 7 tables + 5 embedded PNGs and that the HTML
preview has balanced emphasis tags, no residue markdown bold markers, and no
missing image files.
"""

import re
import struct
import sys
import zipfile
from pathlib import Path

WS = Path(__file__).resolve().parents[3] / "workspaces" / "ai-research-harnesses-trust"
REPORTS = WS / "reports"
HTML = REPORTS / "manuscript_draft_v3.html"
DOCX = REPORTS / "manuscript_draft_v3.docx"
IMGS = [
    WS / "synthesis" / "figures" / "fig_prisma_scr_flow.png",
    WS / "synthesis" / "figures_d2" / "fig1_verification_versus_coverage.png",
    WS / "synthesis" / "figures_d2" / "fig2_scope_and_debates.png",
    WS / "synthesis" / "figures_d2" / "fig3_verification_repair_loop.png",
    WS / "synthesis" / "figures_d2" / "fig4_per_rq_rates.png",
]

ok = True


def check(pred, desc):
    global ok
    status = "OK " if pred else "FAIL"
    print(f"{status} {desc}")
    ok = ok and pred


def is_png(p):
    d = p.read_bytes()[:24]
    if len(d) < 24 or d[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    w, h = struct.unpack(">II", d[16:24])
    return (w, h)


for p in IMGS:
    r = is_png(p)
    check(isinstance(r, tuple) and r[0] > 0, f"{p.name}: valid PNG {r}")

with zipfile.ZipFile(DOCX) as z:
    tables = z.read("word/document.xml").count(b"<w:tbl>")
    media = [n for n in z.namelist() if n.startswith("word/media/") and n.endswith(".png")]
    check(tables == 7, f"DOCX tables: {tables} (expect 7)")
    check(len(media) == 5, f"DOCX embedded PNGs: {len(media)} (expect 5)")

body = HTML.read_text(encoding="utf-8")
body = body[body.index("<body>") :]
check(body.count("<strong>") == body.count("</strong>"), "HTML strong tags balanced")
check(body.count("<em") == body.count("</em>"), "HTML em tags balanced")
check("\ufffd" not in body, "no replacement chars in HTML")
check(len(re.findall(r"\*\*", body)) == 0, "no residue markdown bold in HTML")
check(HTML.read_text(encoding="utf-8").count("<img ") == 5, "HTML has 5 images")

print("ALL QA PASS" if ok else "QA FAILURES PRESENT")
sys.exit(0 if ok else 1)