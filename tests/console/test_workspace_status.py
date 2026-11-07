"""M6-beta (review U-3): a workspace's status is where its screening stands.

The list read "Screening in progress" for a workspace whose screening was
published, because it looked only at whether any decision event existed.
`catalog.describe` now reports one `status`, in this order: published and
current, published with decisions since, screening in progress, corpus
accepted, new.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from test_export_api import change_after_publish, published_workspace

from scholar_harness.workspace.catalog import describe

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "workspaces" / "golden-uav-30"


def _new(tmp_path: Path) -> Path:
    ws = tmp_path / "new"
    (ws / "audit").mkdir(parents=True)
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    (ws / "project.json").write_text(json.dumps({"title": "New"}), encoding="utf-8")
    (ws / "protocol.json").write_text("{}", encoding="utf-8")
    return ws


def test_each_state_has_its_status(tmp_path):
    assert describe(_new(tmp_path), None)["status"] == "NEW"

    accepted = tmp_path / "accepted"
    shutil.copytree(GOLDEN, accepted)
    assert describe(accepted, None)["status"] == "CORPUS_ACCEPTED"

    (tmp_path / "pub").mkdir()
    published, ids = published_workspace(tmp_path / "pub")
    assert describe(published, None)["status"] == "PUBLISHED"

    change_after_publish(published, ids["included"])
    assert describe(published, None)["status"] == "PUBLISHED_CHANGED"


def test_prepared_but_not_published_is_in_progress(tmp_path):
    from scholar_harness.screening.batcher import cmd_prepare

    ws = tmp_path / "prepared"
    shutil.copytree(GOLDEN, ws)
    cmd_prepare(ws, batch_size=10)
    assert describe(ws, None)["status"] == "SCREENING"
