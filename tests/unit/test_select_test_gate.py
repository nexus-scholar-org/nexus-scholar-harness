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
    expected = {
        f"T-{number}" for number in (*range(10, 100, 10), 95, *range(100, 160, 10))
    } | {f"T-{number}" for number in range(160, 240, 10)}
    assert set(data["tasks"]) == expected


def test_inner_selection_is_narrow_and_deterministic() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(data, tasks=["T-10"], paths=[], stage="inner")
    assert tasks == ["T-10"]
    assert commands == [
        "git diff --check",
        "uv run pytest tests/kits/rag/test_canonical.py -q",
    ]


def test_path_selection_unions_overlapping_tasks_without_duplicate_commands() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=["T-20", "T-40", "T-120"],
        paths=["src/scholar_rag/chunker.py"],
        stage="checkpoint",
    )
    # Explicit E3 tasks union with the rag area gate, without duplicates.
    assert tasks == ["T-20", "T-40", "T-120"]
    assert commands[0] == "git diff --check"
    assert len(commands) == len(set(commands))
    assert any("tests/kits/rag" in command for command in commands)


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
        "uv run pytest -q -n auto",
        "uv run ruff check scripts/",
    ]


def test_empty_task_stage_uses_owning_repository_fallback() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(data, tasks=["T-10"], paths=[], stage="closure")
    assert tasks == ["T-10"]
    assert "uv run pytest tests/kits/rag -q" in commands


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
    assert "uv run pytest -q -n auto" not in commands


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
    assert "uv run pytest -q -n auto" not in commands


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
    assert "uv run pytest -q -n auto" not in commands


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
    assert "uv run pytest -q -n auto" not in commands


def test_executable_change_selects_executable_gate() -> None:
    """F1-04: executable change selects the mapped gate, never light-only."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_harness/authority/binding.py"],
        stage="inner",
    )
    assert tasks == []
    assert commands != ["git diff --check"]
    assert 'uv run pytest tests/authority -q -m "not slow"' in commands
    _, pr_commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_harness/authority/binding.py"],
        stage="pr",
    )
    assert "uv run pytest -q -n auto" in pr_commands


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
    assert mixed_tasks == []
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
    assert 'uv run pytest tests/authority -q -m "not slow"' in union_commands


def test_unknown_path_falls_back_conservatively() -> None:
    """F1-06: unknown paths take the harness full suite, never light-only."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data, tasks=[], paths=["packaging/unknown.cfg"], stage="inner"
    )
    assert tasks == []
    assert commands == [
        "git diff --check",
        "uv run pytest -q -n auto",
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


@pytest.mark.parametrize(
    ("path", "directory"),
    [
        ("tests/authority/test_review_lifecycle.py", "tests/authority"),
        ("tests/pipeline/test_pipeline_executor.py", "tests/pipeline"),
        ("tests/unit/test_audit_log.py", "tests/unit"),
        ("tests/e2e/test_e2e_search_screen.py", "tests/e2e"),
        ("tests/console/test_console_jobs.py", "tests/console"),
        ("tests/mcp/test_mcp_setup.py", "tests/mcp"),
        ("tests/recon/test_engine.py", "tests/recon"),
        ("tests/kits/search/test_engine.py", "tests/kits/search"),
    ],
)
def test_changed_test_file_runs_itself_then_its_directory(path: str, directory: str) -> None:
    """A test-only edit runs that file at inner and its directory at checkpoint."""
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(data, tasks=[], paths=[path], stage="inner")
    assert tasks == []
    assert commands == ["git diff --check", f"uv run pytest {path} -q"]
    _, checkpoint = MODULE.select_commands(
        data, tasks=[], paths=[path], stage="checkpoint"
    )
    assert f"uv run pytest {directory} -q" in checkpoint
    _, pr = MODULE.select_commands(data, tasks=[], paths=[path], stage="pr")
    assert "uv run pytest -q -n auto" in pr


def test_top_level_test_file_runs_itself_at_checkpoint() -> None:
    data = MODULE.load_manifest()
    _, commands = MODULE.select_commands(
        data, tasks=[], paths=["tests/test_handoff.py"], stage="checkpoint"
    )
    assert "uv run pytest tests/test_handoff.py -q" in commands
    assert "uv run pytest tests -q" not in commands


def test_explicit_e3_task_still_selects_its_gate() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data, tasks=["T-160"], paths=[], stage="inner"
    )
    assert tasks == ["T-160"]
    assert "uv run pytest tests/authority -q" in commands


@pytest.mark.parametrize(
    ("path", "area", "expected"),
    [
        (
            "src/scholar_harness/screening/collector.py",
            "screening",
            "tests/test_screening_migration.py",
        ),
        ("src/scholar_harness/console/api/screening.py", "console", "tests/console"),
        ("src/scholar_harness/inception/wizard.py", "inception", "tests/inception"),
        ("src/scholar_search/providers/pubmed.py", "search", "tests/kits/search"),
        ("src/scholar_protocol/compiler.py", "protocol", "tests/kits/protocol"),
        ("src/scholar_agent/server.py", "agent-mcp", "tests/kits/agent"),
        ("src/scholar_harness/handoff.py", "harness-other", "tests/unit"),
    ],
)
def test_source_area_selects_narrow_inner_gate(path: str, area: str, expected: str) -> None:
    """Area gates replace both the irrelevant E3 match and the full-suite fallback."""
    data = MODULE.load_manifest()
    assert MODULE.matched_areas(data, [path]) == [area]
    tasks, commands = MODULE.select_commands(data, tasks=[], paths=[path], stage="inner")
    assert tasks == []
    assert any(expected in command and '-m "not slow"' in command for command in commands)
    assert "uv run pytest -q -n auto" not in commands
    assert not any("test_e3_index_lineage_boundary" in command for command in commands)
    _, pr = MODULE.select_commands(data, tasks=[], paths=[path], stage="pr")
    assert "uv run pytest -q -n auto" in pr


def test_contracts_area_keeps_baseline_drift_check_at_inner() -> None:
    data = MODULE.load_manifest()
    _, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_harness/contracts/acceptance.py"],
        stage="inner",
    )
    assert "uv run python scripts/generate_contract_baseline.py --check" in commands


def test_research_ui_change_takes_ui_gate_not_python_suite() -> None:
    data = MODULE.load_manifest()
    paths = [
        "apps/research-ui/components/screening-page.tsx",
        "apps/research-ui/lib/screening-api.ts",
    ]
    _, inner = MODULE.select_commands(data, tasks=[], paths=paths, stage="inner")
    assert inner == [
        "git diff --check",
        "npm --prefix apps/research-ui run typecheck",
        "npm --prefix apps/research-ui run test:related -- "
        "components/screening-page.tsx lib/screening-api.ts",
    ]
    _, pr = MODULE.select_commands(data, tasks=[], paths=paths, stage="pr")
    assert "npm --prefix apps/research-ui run test:browser" in pr
    assert not any(command.startswith("uv run pytest") for command in pr)


def test_research_ui_markdown_stays_prose() -> None:
    data = MODULE.load_manifest()
    _, commands = MODULE.select_commands(
        data, tasks=[], paths=["apps/research-ui/docs/GATES.md"], stage="inner"
    )
    assert commands == ["git diff --check"]


def test_mixed_area_and_unknown_path_still_takes_full_fallback() -> None:
    data = MODULE.load_manifest()
    _, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_search/engine.py", "packaging/unknown.cfg"],
        stage="inner",
    )
    # The full-suite fallback subsumes the narrower search run.
    assert "uv run pytest -q -n auto" in commands
    assert not any("tests/kits/search" in command for command in commands)


def test_every_area_command_targets_existing_test_paths() -> None:
    """Area commands must not silently point at deleted or renamed tests."""
    data = MODULE.load_manifest()
    root = SCRIPT.parents[1]
    for area in data["areas"]:
        for stage in data["stages"]:
            for command in area.get(stage, []):
                if not command.startswith("uv run pytest "):
                    continue
                for raw in command.split()[3:]:
                    token = raw.removeprefix("--ignore=")
                    if token.startswith("tests"):
                        assert (root / token).exists(), f"{area['name']}/{stage}: {token}"


def test_full_suite_runs_once_and_subsumes_narrower_pytest_runs() -> None:
    """A pr selection with a full-suite fallback must not also run subsets."""
    data = MODULE.load_manifest()
    _, commands = MODULE.select_commands(
        data,
        tasks=[],
        paths=["pyproject.toml", ".gitignore", "scripts/select_test_gate.py"],
        stage="pr",
    )
    pytest_runs = [command for command in commands if command.startswith("uv run pytest")]
    assert pytest_runs == ["uv run pytest -q -n auto"]
    assert "uv run ruff check scripts/" in commands
