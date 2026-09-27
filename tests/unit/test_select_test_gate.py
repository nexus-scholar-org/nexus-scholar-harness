from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "select_test_gate.py"
SPEC = importlib.util.spec_from_file_location("select_test_gate", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_manifest_is_valid_and_covers_every_e3_task() -> None:
    data = MODULE.load_manifest()
    expected = {f"T-{number}" for number in (*range(10, 100, 10), 95, *range(100, 160, 10))}
    assert set(data["tasks"]) == expected


def test_inner_selection_is_narrow_and_deterministic() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(data, tasks=["T-10"], paths=[], stage="inner")
    assert tasks == ["T-10"]
    assert commands == [
        "git diff --check",
        "uv run --directory tools/scholar-rag-kit pytest tests/test_canonical.py -q",
    ]


def test_path_selection_unions_overlapping_tasks_without_duplicate_commands() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["tools/scholar-rag-kit/src/scholar_rag/chunker.py"],
        stage="checkpoint",
    )
    # A vendored kit edit also selects the harness synchronization boundary.
    assert tasks == ["T-20", "T-40", "T-120"]
    assert commands[0] == "git diff --check"
    assert len(commands) == len(set(commands))


def test_unknown_task_and_empty_selection_fail_closed() -> None:
    data = MODULE.load_manifest()
    with pytest.raises(ValueError, match="unknown tasks"):
        MODULE.select_commands(data, tasks=["T-999"], paths=[], stage="inner")
    with pytest.raises(ValueError, match="no task selected"):
        MODULE.select_commands(data, tasks=[], paths=["README.md"], stage="inner")


def test_unmatched_executable_path_uses_full_repository_fallback() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data, tasks=[], paths=["scripts/new_tool.py"], stage="inner"
    )
    assert tasks == []
    assert commands == [
        "git diff --check",
        "uv run pytest -q",
        "uv run ruff check scripts/",
    ]


def test_empty_task_stage_uses_owning_repository_fallback() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(data, tasks=["T-10"], paths=[], stage="closure")
    assert tasks == ["T-10"]
    assert "uv run --directory tools/scholar-rag-kit pytest -q" in commands
