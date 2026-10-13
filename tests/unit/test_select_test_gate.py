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
        MODULE.select_commands(data, tasks=[], paths=[], stage="inner")


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


def test_prose_only_doc_selects_light_gate_without_full_suite() -> None:
    """F1-01: prose-only change takes the light doc gate, not the full suite."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["docs/architecture/agent-controls/README.md"],
        stage="inner",
    )
    assert tasks == []
    assert commands == ["git diff --check"]
    assert "uv run pytest -q" not in commands


def test_unmatched_root_readme_is_prose_not_an_error() -> None:
    """F1-01 companion: the old README.md error is now the light gate."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data, tasks=[], paths=["README.md"], stage="inner"
    )
    assert tasks == []
    assert commands == ["git diff --check"]


def test_consumed_doc_keeps_boundary_check() -> None:
    """F1-02: docs/kits_surface_matrix.md keeps its freshness boundary check."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data, tasks=[], paths=["docs/kits_surface_matrix.md"], stage="inner"
    )
    assert "uv run pytest tests/conformance/test_count_freshness.py -q" in commands
    assert "uv run pytest -q" not in commands


def test_consumed_skill_doc_keeps_mirror_check() -> None:
    """F1-02 companion: mirrored skill docs keep the sync boundary check."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=[".agents/skills/scholar-search-kit/SKILL.md"],
        stage="inner",
    )
    assert "uv run python scripts/sync_skills_bundle.py --check" in commands
    assert "uv run pytest -q" not in commands


def test_locked_doc_keeps_drift_requirements() -> None:
    """F1-03: baseline-locked docs keep drift + architecture requirements."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["docs/architecture/contract_v1_baseline.md"],
        stage="inner",
    )
    assert "uv run python scripts/generate_contract_baseline.py --check" in commands
    assert "uv run python scripts/generate_contract_schemas.py --check" in commands
    assert "uv run pytest -q" not in commands


def test_executable_change_selects_executable_gate() -> None:
    """F1-04: executable change selects the mapped gate, never light-only."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_harness/authority/binding.py"],
        stage="inner",
    )
    assert tasks == ["T-130"]
    assert commands != ["git diff --check"]
    assert (
        "uv run pytest tests/conformance/test_e3_index_lineage_boundary.py -q"
        in commands
    )
    _, pr_commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_harness/authority/binding.py"],
        stage="pr",
    )
    assert "uv run pytest -q" in pr_commands


def test_mixed_prose_and_executable_unions() -> None:
    """F1-05: mixed change sets union; prose dilutes nothing."""
    data = MODULE.load_manifest()
    mixed_tasks, mixed_commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=[
            "docs/architecture/agent-controls/README.md",
            "src/scholar_harness/authority/binding.py",
        ],
        stage="inner",
    )
    _, exec_commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_harness/authority/binding.py"],
        stage="inner",
    )
    assert mixed_tasks == ["T-130"]
    assert mixed_commands == exec_commands
    _, union_commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=[
            "docs/kits_surface_matrix.md",
            "src/scholar_harness/authority/binding.py",
        ],
        stage="inner",
    )
    assert (
        "uv run pytest tests/conformance/test_count_freshness.py -q" in union_commands
    )
    assert (
        "uv run pytest tests/conformance/test_e3_index_lineage_boundary.py -q"
        in union_commands
    )


def test_unknown_path_falls_back_conservatively() -> None:
    """F1-06: unknown paths take the harness full suite, never light-only."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data, tasks=[], paths=["apps/research-ui/app/page.tsx"], stage="inner"
    )
    assert tasks == []
    assert commands == [
        "git diff --check",
        "uv run pytest -q",
        "uv run ruff check scripts/",
    ]


def test_empty_selection_is_an_error_not_a_skip() -> None:
    """F1-07: empty selection stays an error."""
    data = MODULE.load_manifest()
    with pytest.raises(ValueError, match="no task selected"):
        MODULE.select_commands(data, tasks=[], paths=[], stage="inner")


def test_contribution_skill_points_to_policy() -> None:
    """F1-08: the skill defers to the test-gate policy; no own full-suite rule."""
    skill = (
        Path(__file__).resolve().parents[2]
        / ".agents"
        / "skills"
        / "pull-request-gate"
        / "SKILL.md"
    )
    text = skill.read_text(encoding="utf-8")
    assert "docs/architecture/test_gate_policy.md" in text
    assert "select_test_gate.py" in text
    assert "uv run pytest          # must pass" not in text


def test_manifest_docs_cover_baseline_locked_non_executable_paths() -> None:
    """Locked non-executable files must keep governance (never ride light)."""
    baseline_script = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "generate_contract_baseline.py"
    )
    spec = importlib.util.spec_from_file_location(
        "contract_baseline_for_gate_test", baseline_script
    )
    assert spec and spec.loader
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    data = MODULE.load_manifest()
    root = Path(__file__).resolve().parents[2]
    locked_paths = set(baseline.EXPLICIT_PATHS)
    for pattern in baseline.GLOBS:
        locked_paths.update(
            path.relative_to(root).as_posix() for path in root.glob(pattern)
        )
    uncovered = sorted(
        path
        for path in locked_paths
        if not MODULE.fallback_repositories([path])
        and not MODULE.path_is_task_matched(data, path)
        and path not in MODULE._covered_doc_paths(data, [path])
        and not (root / path).is_dir()
    )
    assert uncovered == []
