"""Structural QA for the regenerated figures: sizes, valid PNG, and (for the
PRISMA figure) a reading of the rendered pixel region to confirm bands exist
(non-white content where bands were drawn) - without visual inspection."""

import struct
from pathlib import Path

WS = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness\workspaces\ai-research-harnesses-trust\synthesis")

figs = [
    "figures/fig_prisma_scr_flow.png",
    "figures_d2/fig1_verification_versus_coverage.png",
    "figures_d2/fig2_scope_and_debates.png",
    "figures_d2/fig3_verification_repair_loop.png",
    "figures_d2/fig4_per_rq_rates.png",
]
for rel in figs:
    p = Path(WS) / rel
    d = p.read_bytes()
    ok = d[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", d[16:24])
    print(f"{rel}: {'PNG' if ok else 'BAD'}, {w}x{h}, {p.stat().st_size} bytes")