"""The size limit of a review (M10b, decided 2026-11-15, R3).

One rule for the size estimate before a harvest and for the size checks: the
researcher's planned maximum number of records when they stated one, else the
general limit of 1,000 works. "Stated" is read from the workspace's
``intent.json`` (``pool_max`` not null): a protocol's
``target_candidate_pool_size`` can hold a playbook preset nobody chose, and a
preset is never treated as the researcher's plan.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scholar_search.estimate import SIZE_WARN_WORKS


def size_limit(workspace: Path) -> dict[str, Any]:
    """``{"value": int, "source": "planned" | "general"}`` for a workspace."""
    try:
        intent = json.loads((Path(workspace) / "intent.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        intent = None
    planned = intent.get("pool_max") if isinstance(intent, dict) else None
    if isinstance(planned, int) and not isinstance(planned, bool) and planned > 0:
        return {"value": planned, "source": "planned"}
    return {"value": SIZE_WARN_WORKS, "source": "general"}
