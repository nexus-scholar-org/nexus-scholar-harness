"""M6-beta (review T-P1-6): one version, read from the project, everywhere.

The wheel, `__version__`, the CLI, the Desktop Extension and the release
workflows all said 1.0.0 by literal, so a beta tag would have shipped a wheel
named 1.0.0 (and could have published 1.0.0 to PyPI). The version now lives
in `pyproject.toml` only, and a tag that does not match it stops the release.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def test_the_package_reports_the_project_version():
    import scholar_harness

    assert scholar_harness.__version__ == VERSION


def test_the_cli_prints_its_version():
    from scholar_harness.cli import app

    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == f"nexus-scholar {VERSION}"


def test_the_release_workflows_name_no_version_and_check_the_tag():
    for name in ("release.yml", "publish.yml"):
        text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert not re.search(r"nexus[_-]scholar-\d+\.\d+", text), f"{name} names a fixed version"
        assert 'v$VERSION' in text, f"{name} does not check the tag against the project version"
