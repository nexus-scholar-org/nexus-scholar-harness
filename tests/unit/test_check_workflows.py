"""The local check of the GitHub Actions workflows (H-gate-and-ci)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_workflows.py"
SPEC = importlib.util.spec_from_file_location("check_workflows", SCRIPT)
assert SPEC and SPEC.loader
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def _problems(tmp_path: Path, text: str) -> list[str]:
    root = tmp_path
    path = root / ".github" / "workflows" / "ci.yml"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    CHECK.ROOT = root
    try:
        return CHECK.check_workflow(path)
    finally:
        CHECK.ROOT = Path(__file__).resolve().parents[2]


GOOD = """
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/upload-artifact@v4
        with: {name: wheel, path: dist}
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with: {name: wheel}
      - run: echo ok
"""


def test_the_repository_workflows_pass() -> None:
    assert CHECK.main() == 0


def test_a_sound_workflow_has_no_problem(tmp_path: Path) -> None:
    assert _problems(tmp_path, GOOD) == []


def test_an_unknown_need_is_reported(tmp_path: Path) -> None:
    problems = _problems(tmp_path, GOOD.replace("needs: build", "needs: biuld"))
    assert any("needs unknown job biuld" in problem for problem in problems)


def test_a_download_without_an_upload_upstream_is_reported(tmp_path: Path) -> None:
    problems = _problems(tmp_path, GOOD.replace("    needs: build\n", ""))
    assert any("downloads wheel, which no job it needs uploads" in problem for problem in problems)


def test_a_step_without_uses_or_run_and_an_unversioned_action_are_reported(tmp_path: Path) -> None:
    problems = _problems(tmp_path, GOOD.replace("- run: echo ok", "- name: nothing").replace("actions/checkout@v4", "actions/checkout"))
    assert any("has neither uses nor run" in problem for problem in problems)
    assert any("without a version" in problem for problem in problems)


def test_unparsable_yaml_is_reported(tmp_path: Path) -> None:
    assert any("does not parse" in problem for problem in _problems(tmp_path, "jobs: [unclosed"))
