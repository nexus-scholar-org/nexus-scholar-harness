"""The harness registry, rather than sibling git refs, owns kit resolution."""

import importlib.util
import io
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install_plugins.py"
spec = importlib.util.spec_from_file_location("plugin_installer", SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def kit(root, name, dependencies, extras=""):
    path = root / "tools" / name
    path.mkdir(parents=True)
    path.joinpath("pyproject.toml").write_text(
        f'[project]\nname = "{name}"\ndependencies = {dependencies!r}\n{extras}',
        encoding="utf-8",
    )
    return {
        "name": name,
        "repo": f"https://github.com/nexus-scholar-org/{name}",
        "default_rev": "a" * 40,
    }


def test_agent_dependency_uses_registry_rag_pin_and_preserves_external_extras(tmp_path):
    rag = kit(tmp_path, "scholar-rag-kit", ["pydantic>=2"])
    agent = kit(
        tmp_path,
        "scholar-agent-kit",
        [
            "scholar-rag-kit @ git+https://example.org/old@" + "b" * 40,
            "mcp>=1; python_version >= '3.11'",
        ],
        '[project.optional-dependencies]\nextra = ["httpx>=0.27"]\n',
    )
    agent["extras"] = ["extra"]
    selected, external = installer.dependency_plan(
        [agent], [rag, agent], tmp_path, None, False
    )
    assert [p["name"] for p in selected] == ["scholar-rag-kit", "scholar-agent-kit"]
    assert selected[0]["default_rev"] == "a" * 40
    assert external == [
        "httpx>=0.27",
        "mcp>=1; python_version >= '3.11'",
        "pydantic>=2",
    ]
    assert not any("git+" in req for req in external)


@pytest.mark.parametrize("git_only", [False, True])
def test_install_cannot_replace_managed_dependencies(tmp_path, monkeypatch, git_only):
    plugin = kit(tmp_path, "scholar-rag-kit", [])
    calls = []
    monkeypatch.setattr(
        installer,
        "run_command",
        lambda cmd, **kw: calls.append(cmd) or subprocess.CompletedProcess(cmd, 0),
    )
    assert installer.install_plugin(plugin, None, git_only, False, False, tmp_path)
    assert "--no-deps" in calls[0]
    assert "--python" in calls[0]
    assert str(tmp_path / ".venv") in calls[0][calls[0].index("--python") + 1]
    if git_only:
        assert calls[0][-1].endswith("@" + "a" * 40)


def test_local_only_never_fetches_remote_dependency_metadata(tmp_path, monkeypatch):
    plugin = {
        "name": "scholar-agent-kit",
        "repo": "https://github.com/org/kit",
        "default_rev": "a" * 40,
    }
    monkeypatch.setattr(
        installer, "urlopen", lambda *a, **k: pytest.fail("network touched")
    )
    with pytest.raises(ValueError, match="No local dependency metadata"):
        installer.dependency_plan([plugin], [plugin], tmp_path, None, False, True)


def test_verification_uses_selected_environment_without_sync(tmp_path, monkeypatch):
    calls = []

    def run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(installer.subprocess, "run", run)
    assert installer.verify_installation(
        [{"name": "scholar-rag-kit", "console_script": "scholar-rag"}], tmp_path
    ) == {"scholar-rag-kit": True}
    assert calls[0][0] == ["uv", "run", "--no-sync", "scholar-rag", "--help"]
    assert calls[0][1]["cwd"] == tmp_path


def test_transitive_extras_and_cycles_do_not_override_registry(tmp_path):
    rag = kit(tmp_path, "scholar-rag-kit", ["scholar-agent-kit"])
    agent = kit(
        tmp_path,
        "scholar-agent-kit",
        ["scholar-rag-kit[extra]"],
        '[project.optional-dependencies]\nextra = ["httpx>=0.27"]\n',
    )
    rag_path = tmp_path / "tools/scholar-rag-kit/pyproject.toml"
    rag_path.write_text(
        rag_path.read_text() + '[project.optional-dependencies]\nextra = ["rich>=13"]\n'
    )
    chosen, requirements = installer.dependency_plan(
        [agent], [rag, agent], tmp_path, None, False
    )
    assert chosen[0]["extras"] == ["extra"]
    assert requirements == ["rich>=13"]


def test_git_metadata_is_read_at_the_selected_full_sha(tmp_path, monkeypatch):
    plugin = {
        "name": "scholar-rag-kit",
        "repo": "https://github.com/nexus-scholar-org/scholar-rag-kit.git",
        "default_rev": "a" * 40,
    }
    urls = []

    def fetch(url, **kwargs):
        urls.append(url)
        return io.BytesIO(b'[project]\ndependencies = ["pydantic>=2"]\n')

    monkeypatch.setattr(installer, "urlopen", fetch)
    _, external = installer.dependency_plan([plugin], [plugin], tmp_path, None, True)
    assert urls == [
        "https://raw.githubusercontent.com/nexus-scholar-org/scholar-rag-kit/"
        + "a" * 40
        + "/pyproject.toml"
    ]
    assert external == ["pydantic>=2"]


def test_failed_kit_install_cannot_report_ready(tmp_path, monkeypatch, capsys):
    (tmp_path / ".venv").mkdir()
    plugin = {"name": "scholar-rag-kit"}
    monkeypatch.setattr(
        installer, "__file__", str(tmp_path / "scripts/install_plugins.py")
    )
    monkeypatch.setattr(installer.sys, "argv", ["install_plugins.py", "--no-verify"])
    monkeypatch.setattr(installer, "load_registry", lambda _: [plugin])
    monkeypatch.setattr(installer, "dependency_plan", lambda *a: ([plugin], []))
    monkeypatch.setattr(installer, "install_plugin", lambda **kwargs: False)
    with pytest.raises(SystemExit) as exc:
        installer.main()
    assert exc.value.code == 1
    assert "environment ready" not in capsys.readouterr().out
