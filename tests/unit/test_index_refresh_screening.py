"""INDEX refresh must not drop the screening/human-confirmation record.

Regression: the screening block lived only in a hand-edited ``INDEX.md``, and
``refresh_index_md`` regenerated the file from ``project.json`` without it, so
every audit-journal write erased the reviewer status. These tests pin the
generator behaviour: render what ``project.json`` records, and render nothing
when it records nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scholar_harness.workspace.loader import (
    load_log_module_uncached,
    resolve_workspace_manager_scripts,
)


def _refresher():
    scripts = resolve_workspace_manager_scripts()
    if scripts is None:
        pytest.skip("workspace-manager skill is not reachable")
    module = load_log_module_uncached(
        scripts, import_name="workspace_manager_log_event_index_refresh_test"
    )
    if module is None:
        pytest.skip("log_event.py could not be loaded")
    return module.refresh_index_md


def _workspace(tmp_path: Path, manifest: dict) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    return ws


def _base_manifest() -> dict:
    return {
        "project_id": "uav-demo",
        "title": "Demo workspace",
        "status": "active",
        "research_questions": ["RQ1: Does it work?"],
        "stats": {},
    }


def test_screening_status_is_rendered_from_the_manifest(tmp_path):
    manifest = _base_manifest()
    manifest.update(
        {
            "screening_status": "FINAL_AGENT_UNCONFIRMED",
            "human_confirmation": "SIGNED (HumanConfirmation@1, Ada Lovelace; 2026-10-31)",
            "protocol_fingerprint": "sha256:aaaa",
            "criteria_sha256": "bbbb",
            "screening": {
                "totals": {
                    "screened": 14150,
                    "included": 644,
                    "excluded": 13506,
                    "not_retrieved": 346,
                    "identified": 14413,
                    "duplicates_removed": 263,
                },
                "deviations": ["DEV-01"],
            },
        }
    )

    index = Path(_refresher()(_workspace(tmp_path, manifest))).read_text(encoding="utf-8")

    assert "## 🔎 Screening Status" in index
    assert "`FINAL_AGENT_UNCONFIRMED`" in index
    assert "SIGNED (HumanConfirmation@1, Ada Lovelace; 2026-10-31)" in index
    assert "**Screened**: 14,150 (14,413 identified − 263 duplicates)" in index
    assert "**Included**: 644 · **Excluded**: 13,506 (of which 346 *not retrieved*)" in index
    assert "**Deviations**: DEV-01" in index
    assert "protocol `sha256:aaaa`, criteria `bbbb`" in index


def test_no_screening_section_when_the_manifest_records_none(tmp_path):
    index = Path(
        _refresher()(_workspace(tmp_path, _base_manifest()))
    ).read_text(encoding="utf-8")

    assert "## 🔎 Screening Status" not in index
    # The surrounding structure is unchanged.
    assert "## 📊 Summary Metrics" in index
    assert "## 🎯 Research Questions" in index


def test_refresh_keeps_the_section_across_repeated_writes(tmp_path):
    """A second refresh (what every audit event triggers) is idempotent."""

    manifest = _base_manifest()
    manifest.update(
        {
            "screening_status": "FINAL_AGENT_UNCONFIRMED",
            "human_confirmation": "UNSIGNED",
            "screening": {"totals": {"included": 1, "excluded": 2}},
        }
    )
    ws = _workspace(tmp_path, manifest)
    refresh = _refresher()

    refresh(ws)
    first = (ws / "INDEX.md").read_text(encoding="utf-8")
    refresh(ws)
    second = (ws / "INDEX.md").read_text(encoding="utf-8")

    assert second.count("## 🔎 Screening Status") == 1
    assert "**Human confirmation**: UNSIGNED" in second
    assert "**Included**: 1 · **Excluded**: 2" in second

    def screening_section(text: str) -> str:
        start = text.index("## 🔎 Screening Status")
        end = text.index("## 🎯 Research Questions")
        return text[start:end]

    assert screening_section(first) == screening_section(second)
