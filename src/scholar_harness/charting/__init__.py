"""The charting table (M12a): full-text status, the full-text decision and, later, the cells.

Workspace records outside Contract v1 (decision 2026-11-21, M12a item 1), under
``<ws>/charting/``: ``events/<screener_id>.jsonl`` (append-only events, the
screening pattern), ``kept_history.jsonl`` (the kept sets the table has seen,
so a record that leaves or joins after a new publication is marked). Rows come
only from published screening files (item 4): the current round's
``literature/included.json`` and each archived round's copy.
"""

from __future__ import annotations

from pathlib import Path

CHARTING_DIR = Path("charting")


class ChartingRefused(Exception):
    """A typed refusal (console refusal set, ``screening-api-contract.md`` §7)."""

    def __init__(self, status: int, code: str, message: str, **details: object) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details
