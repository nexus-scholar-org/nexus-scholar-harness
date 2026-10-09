"""Neutral manifest policy (HCM-02).

Owns the ``project.json`` read/merge/atomic-write discipline used by the audit
path:

* canonical event projection updates ``updated_at`` and overwrites only
  pre-existing ``stats`` keys (unknown metric keys stay journal-only);
* writes are atomic temp-file + ``os.replace`` (never in-place truncation);
* manifest-read failures during projection are best-effort (swallowed with a
  debug log), while journal-append failures propagate as ``OSError`` so
  acceptance can map them to ``ATOMIC_COMMIT_FAILED``.

``orchestrator.sync_state`` keeps its own merge (including HCM-01 defects
(b)/(c), preserved, not repaired here); this module serves only the
append-event projection shared by console/CLI/acceptance/index paths.
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def read_manifest(workspace: Path | str) -> dict[str, Any] | list[Any] | Any:
    """Read ``project.json`` without policy (raw JSON, may be non-object)."""
    path = Path(workspace) / "project.json"
    return json.loads(path.read_text(encoding="utf-8"))


def update_manifest_for_event(
    workspace: Path | str,
    *,
    now_iso: str,
    metrics: dict[str, Any] | None,
) -> None:
    """Best-effort projection: bump ``updated_at``, gate ``stats`` keys.

    Swallows all failures (missing/corrupt/non-object manifest, unwritable
    file) with a debug log -- the journal append is authoritative, this
    projection is not. Non-object manifests are left untouched (no
    ``TypeError`` here; the sync-state non-object ``TypeError`` defect (b) lives
    in ``orchestrator.sync_state`` and is preserved there, not here).
    """
    ws = Path(workspace)
    manifest_path = ws / "project.json"
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        logger.debug("project.json refresh failed", exc_info=True)
        return
    if not isinstance(manifest, dict):
        return
    try:
        manifest["updated_at"] = now_iso
        if metrics:
            stats = manifest.get("stats", {})
            if isinstance(stats, dict):
                for key, value in metrics.items():
                    if key in stats:
                        stats[key] = value
        tmp = manifest_path.with_name(
            manifest_path.name + f".tmp-{uuid.uuid4().hex[:8]}"
        )
        tmp.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        tmp.replace(manifest_path)
    except Exception:
        logger.debug("project.json refresh failed", exc_info=True)
