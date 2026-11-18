"""The wheel build must not silently drop the app (H-small-fixes, strict-run finding 13).

`hatch_build.py` bundles the Research UI export into the wheel. A build run
without `apps/research-ui/.next-export` used to succeed and produce a wheel whose
`nexus-scholar ui` said "no app bundle". The hook is exercised directly, with
`hatchling` stubbed (it exists only in the isolated build environment).
"""

from __future__ import annotations

import importlib.util
import re
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UI_COMMANDS = ("npm ci", "npm run build:export")


@pytest.fixture
def hook_class(monkeypatch):
    for name in (
        "hatchling",
        "hatchling.builders",
        "hatchling.builders.hooks",
        "hatchling.builders.hooks.plugin",
    ):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    interface = types.ModuleType("hatchling.builders.hooks.plugin.interface")
    interface.BuildHookInterface = type("BuildHookInterface", (), {})
    monkeypatch.setitem(sys.modules, "hatchling.builders.hooks.plugin.interface", interface)
    spec = importlib.util.spec_from_file_location("nexus_hatch_build_under_test", ROOT / "hatch_build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CustomBuildHook


def _hook(hook_class, root: Path, target: str = "wheel"):
    hook = hook_class()
    hook.root = str(root)
    hook.target_name = target
    return hook


def _build(hook, version: str = "standard") -> dict:
    data = {"force_include": {}}
    hook.initialize(version, data)
    return data


def _export(root: Path) -> Path:
    export = root / "apps" / "research-ui" / ".next-export"
    (export / "en").mkdir(parents=True)
    (export / "en" / "index.html").write_text("<html></html>", encoding="utf-8")
    return export


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("NEXUS_WHEEL_REQUIRE_UI", raising=False)
    monkeypatch.delenv("NEXUS_WHEEL_ALLOW_NO_UI", raising=False)


def test_a_wheel_build_without_the_ui_export_fails_and_names_the_two_commands(hook_class, tmp_path):
    with pytest.raises(RuntimeError) as raised:
        _build(_hook(hook_class, tmp_path))
    message = str(raised.value)
    for command in UI_COMMANDS:
        assert command in message
    assert "apps/research-ui" in message
    assert "NEXUS_WHEEL_ALLOW_NO_UI" in message


def test_a_wheel_build_with_the_export_bundles_it(hook_class, tmp_path):
    export = _export(tmp_path)
    data = _build(_hook(hook_class, tmp_path))
    assert data["force_include"] == {str(export): "scholar_harness_data/ui"}


def test_the_opt_out_builds_a_wheel_without_the_ui_and_says_so(hook_class, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NEXUS_WHEEL_ALLOW_NO_UI", "1")
    data = _build(_hook(hook_class, tmp_path))
    assert data["force_include"] == {}
    warning = capsys.readouterr().err
    assert "no UI" in warning and "npm run build:export" in warning


def test_the_release_flag_still_fails_even_with_the_opt_out(hook_class, tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_WHEEL_REQUIRE_UI", "1")
    monkeypatch.setenv("NEXUS_WHEEL_ALLOW_NO_UI", "1")
    with pytest.raises(RuntimeError):
        _build(_hook(hook_class, tmp_path))


def test_editable_installs_and_other_targets_never_need_the_export(hook_class, tmp_path):
    assert _build(_hook(hook_class, tmp_path), version="editable")["force_include"] == {}
    assert _build(_hook(hook_class, tmp_path, target="sdist"))["force_include"] == {}


def test_the_no_bundle_message_of_an_installed_app_says_to_rebuild_the_wheel_and_reinstall(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from scholar_harness.cli import app
    from scholar_harness.console import launcher

    monkeypatch.setattr(launcher, "resolve_ui_dir", lambda: None)
    raw = CliRunner().invoke(app, ["ui", "--root", str(tmp_path)]).output
    output = " ".join(re.sub(r"\x1b\[[0-9;]*m", "", raw).split())
    assert "no app bundle" in output
    for needle in (*UI_COMMANDS, "uv build --wheel", "uv tool install --force", "NEXUS_UI_DIR"):
        assert needle in output
