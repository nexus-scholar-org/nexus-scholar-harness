"""M13 Part W: the Windows bundle recipe and installer, checked without building them.

The build itself runs on GitHub's Windows runner (`.github/workflows/windows-installer.yml`,
the researcher's answer of 2026-11-24); these tests pin what the files promise.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "packaging" / "windows"


def _build():
    spec = importlib.util.spec_from_file_location("ns_windows_build", WINDOWS / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_version_keys_order_as_pep_440_does():
    key = _build().version_key
    ordered = ["1.0.0", "1.1.0.dev3", "1.1.0a1", "1.1.0b6", "1.1.0b7", "1.1.0b10", "1.1.0rc1", "1.1.0", "1.1.1", "1.2.0", "2.0.0"]
    assert [key(v) for v in ordered] == sorted(key(v) for v in ordered)
    assert len({key(v) for v in ordered}) == len(ordered)
    assert key("1.1") == key("1.1.0")
    assert key("2.0.0") < 2**63  # Inno Setup reads it as a 64-bit integer


@pytest.mark.parametrize("bad", ["", "1.1.0.post1", "v1.1.0", "1.1.0b7.dev1", "latest"])
def test_a_version_the_installer_cannot_order_is_refused(bad):
    with pytest.raises(ValueError):
        _build().version_key(bad)


def test_the_version_comes_from_the_wheel_name():
    build = _build()
    assert build.wheel_version(Path("dist/nexus_scholar-1.1.0b7-py3-none-any.whl")) == "1.1.0b7"
    with pytest.raises(ValueError):
        build.wheel_version(Path("dist/something.zip"))


def test_the_installer_is_per_user_and_keeps_the_promises_of_the_specification():
    iss = (WINDOWS / "nexus-scholar.iss").read_text(encoding="utf-8")
    assert "PrivilegesRequired=lowest" in iss  # no administrator password
    assert r"DefaultDirName={userpf}\{#AppName}" in iss  # %LOCALAPPDATA%\Programs\Nexus Scholar
    task = re.search(r'^Name: "desktopicon".*$', iss, flags=re.M).group(0)
    assert "unchecked" not in task  # the desktop icon is ticked
    assert "'--stop'" in iss and "EngineRunning" in iss  # stop it first, after asking
    assert "VersionKey" in iss and "MB_DEFBUTTON2" in iss  # the downgrade warning defaults to No
    assert "'--forget'" in iss and "RemoveUserData := False" in iss  # settings kept unless asked
    assert "never removed" in iss  # the uninstaller says reviews are kept
    assert re.search(r'#define AppId "[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}"', iss)


def test_the_bundle_recipe_has_both_programs_and_the_lessons_of_the_trial():
    spec = (WINDOWS / "nexus-scholar.spec").read_text(encoding="utf-8")
    assert 'name="Nexus Scholar"' in spec and "console=False" in spec
    assert 'name="nexus-scholar-mcp"' in spec and "console=True" in spec
    assert 'collect_all("scholar_harness_data")' in spec and 'copy_metadata("nexus-scholar")' in spec
    for excluded in ("IPython", "jedi", "parso"):
        assert f'"{excluded}"' in spec
    assert (ROOT / "packaging" / "icons" / "nexus-scholar.ico").is_file()


def test_the_ci_test_never_points_at_the_real_reviews_folder():
    smoke = (WINDOWS / "smoke_test.ps1").read_text(encoding="utf-8")
    assert "$env:NEXUS_WORKSPACES_ROOT = Join-Path $root" in smoke
    assert "$env:NEXUS_APP_HOME = Join-Path $root" in smoke
    assert "kept-review" in smoke and "removed a review" in smoke


def test_the_workflow_runs_on_tags_on_demand_and_on_packaging_changes_only():
    flow = (ROOT / ".github" / "workflows" / "windows-installer.yml").read_text(encoding="utf-8")
    assert "tags:" in flow and "workflow_dispatch" in flow
    assert "- 'packaging/**'" in flow and "runs-on: windows-latest" in flow
    assert "smoke_test.ps1" in flow and "--installer" in flow
