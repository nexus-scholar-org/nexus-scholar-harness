from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "select_test_gate.py"
SPEC = importlib.util.spec_from_file_location("select_test_gate", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

# The full Python suite, as the manifest spells it since H-gate-and-ci: through the machine-wide
# lock, four workers, work stealing. Locally it runs at closure or as the unknown-path fallback;
# the pr gate is the area's checkpoint, and CI runs the full suites.
FULL = MODULE.LOCKED_FULL_SUITE


def test_manifest_is_valid_and_covers_every_task() -> None:
    data = MODULE.load_manifest()
    # The E3 indexing tasks (T-10 to T-100, T-130, T-140) left with scholar_rag
    # (H-remove-rag-verify, 2026-11-23).
    expected = {"T-110", "T-120", "T-150"} | {f"T-{number}" for number in range(160, 240, 10)}
    assert set(data["tasks"]) == expected


def test_inner_selection_is_narrow_and_deterministic() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(data, tasks=["T-160"], paths=[], stage="inner")
    assert tasks == ["T-160"]
    assert commands == [
        "git diff --check",
        "uv run pytest tests/authority -q",
    ]


def test_path_selection_unions_overlapping_tasks_without_duplicate_commands() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(
        data,
        tasks=["T-120", "T-160", "T-170"],
        paths=["src/scholar_agent/server.py"],
        stage="checkpoint",
    )
    # Explicit tasks union with the agent-mcp area gate, without duplicates.
    assert tasks == ["T-120", "T-160", "T-170"]
    assert commands[0] == "git diff --check"
    assert len(commands) == len(set(commands))
    assert any("tests/kits/agent" in command for command in commands)


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
        FULL,
        "uv run ruff check scripts/",
    ]


def test_empty_task_stage_uses_owning_repository_fallback() -> None:
    data = MODULE.load_manifest()
    tasks, commands = MODULE.select_commands(data, tasks=["T-110"], paths=[], stage="closure")
    assert tasks == ["T-110"]
    assert "uv run pytest tests/kits/agent -q" in commands


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
    assert FULL not in commands


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
    assert FULL not in commands


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
    assert FULL not in commands


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
    assert FULL not in commands


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
    assert FULL not in pr_commands
    assert any(command.startswith("uv run pytest tests/authority ") for command in pr_commands)
    _, closure = MODULE.select_commands(
        data,
        tasks=[],
        paths=["src/scholar_harness/authority/binding.py"],
        stage="closure",
    )
    assert FULL in closure


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
        FULL,
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
    assert f"uv run pytest {directory} -q" in pr
    assert FULL not in pr
    _, closure = MODULE.select_commands(data, tasks=[], paths=[path], stage="closure")
    assert FULL in closure


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
        ("src/scholar_harness/console/api/screening.py", "console-screening", "tests/console/test_screening_actions.py"),
        ("src/scholar_harness/console/api/charting.py", "console-charting", "tests/console/test_charting_api.py"),
        ("src/scholar_harness/charting/fetch.py", "console-charting", "tests/console/test_charting_fetch_api.py"),
        ("src/scholar_harness/console/api/discovery.py", "console-discovery", "tests/console/test_discovery_api.py"),
        ("src/scholar_harness/console/api/inception.py", "console-inception", "tests/console/test_inception_api.py"),
        ("src/scholar_harness/console/serve.py", "console", "tests/console"),
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
    assert FULL not in commands
    assert not any("test_e3_index_lineage_boundary" in command for command in commands)
    _, pr = MODULE.select_commands(data, tasks=[], paths=[path], stage="pr")
    _, checkpoint = MODULE.select_commands(data, tasks=[], paths=[path], stage="checkpoint")
    assert FULL not in pr
    assert all(command in pr for command in checkpoint)
    _, closure = MODULE.select_commands(data, tasks=[], paths=[path], stage="closure")
    assert FULL in closure


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
        "npm --prefix apps/research-ui run lint:ui",
        "npm --prefix apps/research-ui run test:related -- "
        "components/screening-page.tsx lib/screening-api.ts",
    ]
    _, pr = MODULE.select_commands(data, tasks=[], paths=paths, stage="pr")
    assert pr == [
        "git diff --check",
        "npm --prefix apps/research-ui run typecheck",
        "npm --prefix apps/research-ui run lint:ui",
        "uv run python scripts/suite_lock.py -- npm --prefix apps/research-ui test",
    ]
    _, closure = MODULE.select_commands(data, tasks=[], paths=paths, stage="closure")
    assert "npm --prefix apps/research-ui run build" in closure
    # The browser suite was removed on 2026-11-23 (H-test-diet); no gate may name it.
    assert not any("test:browser" in command or "playwright" in command for command in pr + closure)
    assert not any("pytest" in command for command in pr + closure)


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
    assert FULL in commands
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
    pytest_runs = [command for command in commands if "pytest" in command]
    assert pytest_runs == [FULL]
    assert "uv run ruff check scripts/" in commands


# H-gate-and-ci (2026-11-23): the local gate is what a change touched, CI is the full gate,
# every full suite on the PC goes through the machine-wide lock, every test file has an area.


def test_every_full_suite_in_the_manifest_goes_through_the_lock_with_four_workers() -> None:
    text = MODULE.MANIFEST.read_text(encoding="utf-8")
    assert "-n auto" not in text
    data = MODULE.load_manifest()
    commands = [
        command
        for section in (data["common"], data.get("area_defaults", {}), data["fallback"])
        for value in section.values()
        if isinstance(value, list)
        for command in value
    ]
    commands += [c for area in data["areas"] for stage in data["stages"] for c in area.get(stage, [])]
    commands += [c for task in data["tasks"].values() for stage in data["stages"] for c in task[stage]]
    for command in commands:
        bare = command.split(" -- ", 1)[-1]
        if bare in {"uv run pytest -q", "uv run pytest -q -n 4 --dist worksteal", "npm --prefix apps/research-ui test"}:
            assert command.startswith("uv run python scripts/suite_lock.py -- "), command


def test_the_local_pr_gate_is_the_area_checkpoint_and_the_full_suite_is_for_closure() -> None:
    data = MODULE.load_manifest()
    for area in data["areas"]:
        path = area["paths"][0].replace("**", "x.py")
        if MODULE.matched_areas(data, [path]) != [area["name"]]:
            continue
        _, pr = MODULE.select_commands(data, tasks=[], paths=[path], stage="pr")
        assert FULL not in pr, area["name"]


def test_changed_defaults_to_origin_main() -> None:
    assert MODULE.DEFAULT_BASE == "origin/main"


def test_checkpoint_token_is_refused_at_inner(tmp_path, monkeypatch) -> None:
    data = MODULE.load_manifest()
    data["areas"][0]["inner"] = [MODULE.CHECKPOINT_TOKEN]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(__import__("json").dumps(data), encoding="utf-8")
    monkeypatch.setattr(MODULE, "MANIFEST", manifest)
    with pytest.raises(ValueError, match="allowed only at pr and closure"):
        MODULE.load_manifest()


def test_the_check_names_a_test_file_no_area_owns(tmp_path) -> None:
    data = {
        "stages": ["inner", "checkpoint", "pr", "closure"],
        "areas": [
            {"name": "a", "inner": ["uv run pytest tests/kits/a -q"], "checkpoint": ["uv run pytest tests --ignore=tests/kits -q"]},
        ],
    }
    for name in ("tests/kits/a/test_one.py", "tests/unit/test_two.py", "tests/test_three.py"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("def test_x():\n    pass\n", encoding="utf-8")
    # The catch-all `tests --ignore=...` owns nothing: an area must name the file or its folder.
    assert MODULE.unowned_test_files(data, root=tmp_path) == ["tests/test_three.py", "tests/unit/test_two.py"]
    assert MODULE.missing_test_targets(data, root=tmp_path) == []
    data["areas"][0]["inner"] = ["uv run pytest tests/kits/gone -q"]
    assert MODULE.missing_test_targets(data, root=tmp_path) == ["a/inner: tests/kits/gone"]


def test_the_repository_has_no_unowned_test_file() -> None:
    data = MODULE.load_manifest()
    assert MODULE.unowned_test_files(data) == []
    assert MODULE.missing_test_targets(data) == []


def test_finer_console_areas_keep_inner_to_a_few_files() -> None:
    data = MODULE.load_manifest()
    for path, area in (
        ("src/scholar_harness/console/api/charting.py", "console-charting"),
        ("src/scholar_harness/console/api/discovery.py", "console-discovery"),
        ("src/scholar_harness/console/api/screening_v1.py", "console-screening"),
        ("src/scholar_harness/console/api/recon.py", "console-inception"),
    ):
        assert MODULE.matched_areas(data, [path]) == [area]
        _, inner = MODULE.select_commands(data, tasks=[], paths=[path], stage="inner")
        targets = [t for command in inner for t in MODULE.pytest_targets(command)]
        assert targets and "tests/console" not in targets, area
        assert all(target.endswith(".py") for target in targets), area


def test_a_workflow_change_takes_the_workflow_check_not_the_full_suite() -> None:
    data = MODULE.load_manifest()
    _, pr = MODULE.select_commands(data, tasks=[], paths=[".github/workflows/ci.yml"], stage="pr")
    assert pr == ["git diff --check", "uv run python scripts/check_workflows.py"]


def test_no_e3_task_runs_the_full_suite_at_pr() -> None:
    """Review finding 3: a test helper or conftest change runs its task's checkpoint at pr, not the full suite."""
    data = MODULE.load_manifest()
    for task_id, task in data["tasks"].items():
        assert FULL not in task["pr"], task_id
    _, pr = MODULE.select_commands(data, tasks=[], paths=["tests/console/conftest.py"], stage="pr")
    assert FULL not in pr
    assert "uv run pytest tests/console -q" in pr


def test_the_missing_path_check_covers_e3_tasks(tmp_path) -> None:
    data = {
        "stages": ["inner", "checkpoint", "pr", "closure"],
        "areas": [],
        "tasks": {"T-1": {"inner": ["uv run pytest tests/kits/rag/test_gone.py -q"], "checkpoint": [], "pr": [], "closure": []}},
    }
    assert MODULE.missing_test_targets(data, root=tmp_path) == ["T-1/inner: tests/kits/rag/test_gone.py"]
