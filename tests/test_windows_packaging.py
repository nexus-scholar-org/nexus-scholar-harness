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


def test_the_compiler_gets_absolute_paths(tmp_path, monkeypatch):
    """Review of Part W, P1: Inno Setup reads a relative path from the script's own folder."""
    build = _build()
    seen: list[list[str]] = []
    monkeypatch.setattr(build, "run", lambda command, **_k: seen.append(command))
    out = Path("relative-out")
    monkeypatch.chdir(tmp_path)
    (tmp_path / out).mkdir()
    (tmp_path / out / "NexusScholar-1.1.0b7-setup.exe").write_text("x", encoding="utf-8")
    build.build_installer(Path("relative-bundle"), "1.1.0b7", out, "iscc")
    source = next(a for a in seen[0] if a.startswith("/DSourceDir="))
    output = next(a for a in seen[0] if a.startswith("/O"))
    assert Path(source.split("=", 1)[1]).is_absolute() and Path(output[2:]).is_absolute()


def test_the_uninstaller_never_calls_a_setup_only_function_and_a_failed_stop_stops_the_install():
    iss = (WINDOWS / "nexus-scholar.iss").read_text(encoding="utf-8")
    assert "IsUninstaller()" in iss and "UninstallSilent()" in iss
    ask = iss[iss.index("function AskToStop"):iss.index("function InitializeSetup")]
    assert "WizardSilent" not in ask and "Silent()" in ask  # P1: through the helper only
    assert "if not StopEngine(Exe) then" in ask and "Result := False" in ask  # P3: no install over a running engine
    assert "DisableDirPage=yes" in iss


def test_the_smoke_test_refuses_to_run_on_a_computer_someone_uses():
    smoke = (WINDOWS / "smoke_test.ps1").read_text(encoding="utf-8")
    assert '$env:GITHUB_ACTIONS -ne "true" -and -not $ThrowAwayMachine' in smoke


def test_only_the_tag_job_may_write_to_the_release():
    flow = (ROOT / ".github" / "workflows" / "windows-installer.yml").read_text(encoding="utf-8")
    top = flow[: flow.index("jobs:")]
    assert "contents: read" in top and "contents: write" not in top
    attach = flow[flow.index("  attach:"):]
    assert "if: github.ref_type == 'tag'" in attach and "contents: write" in attach


def test_a_bundle_without_the_plugin_manifest_is_a_failed_build():
    spec = (WINDOWS / "nexus-scholar.spec").read_text(encoding="utf-8")
    assert "plugin manifest is missing" in spec and "raise SystemExit" in spec
