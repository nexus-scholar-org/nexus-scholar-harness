from __future__ import annotations

from rich.console import Console
from rich.table import Table



console = Console()

_INLINE_LIST_CAP = 50


def _bounded(items: list, cap: int = _INLINE_LIST_CAP) -> dict:
    """Bound a list for an audit-description payload (subprocess argv safety)."""
    if len(items) <= cap:
        return {"values": list(items), "truncated_count": 0}
    return {"values": list(items[:cap]), "truncated_count": len(items) - cap}


def show_refraction_grid(topic: str) -> None:
    from . import refraction_rows
    table = Table(title="4-Way Paradigm Refraction", show_header=True, header_style="bold cyan")
    table.add_column("Paradigm", style="bold white", width=24)
    table.add_column("Epistemological Goal", width=34)
    table.add_column("Sample Refined RQ", width=52)
    table.add_column("Required Primary Evidence", width=34)
    table.add_column("Strict Negative Exclusions", width=34)
    for r in refraction_rows(topic):
        table.add_row(
            r["paradigm"], r["goal"], r["sample_rq"], r["evidence"], r["negatives"]
        )
    console.print(table)
