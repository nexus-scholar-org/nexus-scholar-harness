"""P7.3  tests: `scholar-harness init <title>` (nexus-scholar init) portable raw-folder bootstrap."""

from __future__ import annotations

import json

import pytest
import typer

# Reuse the responder/answer harness from the wizard e2e tests (tests/ is on
# the pytest path in prepend import mode).
from test_inception import E2E_ANSWERS, GENESIS_TS, ScriptedResponder
from typer.testing import CliRunner

from scholar_harness import inception
from scholar_harness.cli import app
from scholar_harness.inception import (
    init_command,
    install_skills,
    resolve_skills_root,
    run_wizard,
)

runner = CliRunner()

# The raw wizard test freezes time so both PROJECT_INITIALIZED runs are
# comparable; scaffold-only uses its own frozen timestamp.
_TITLE = "On-Device: Weed Detection!"


def _journal(target):
    return [
        json.loads(line)
        for line in (target / "audit" / "journal.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]


# ---------------------------------------------------------------------------
# scaffold-only: canonical contract layout
# ---------------------------------------------------------------------------


def test_init_scaffold_only_full_layout(tmp_path):
    target = tmp_path / "proj"
    result = init_command(_TITLE, target, scaffold_only=True)

    assert result["slug"] == "on-device-weed-detection"
    assert result["paradigm"] == "Positivist"
    assert result["playbook"] == "PRISMA_SLR"
    assert result["protocol_fingerprint"].startswith("sha256:")

    # All canonical contract files + support artifacts exist.
    for marker in (
        "project.json", "protocol.json", "intent.json", "SCREENING_CRITERIA.md",
        "INDEX.md", "audit/journal.jsonl", ".env.example", ".mcp.json",
    ):
        assert (target / marker).is_file(), f"missing canonical file: {marker}"
    for sub in ("literature", "pdfs", "extracted", "synthesis", "exports", "audit"):
        assert (target / sub).is_dir(), f"missing canonical dir: {sub}"
    assert (target / ".agents" / "skills" / "workspace-manager" / "SKILL.md").is_file()

    # project.json mirrors the workspace-manager init_project.py manifest.
    manifest = json.loads((target / "project.json").read_text(encoding="utf-8"))
    assert set(manifest) == {
        "$schema", "project_id", "title", "description", "created_at", "updated_at",
        "status", "paradigm", "research_questions", "keywords", "stats",
    }
    assert manifest["project_id"] == "on-device-weed-detection"
    assert manifest["title"] == _TITLE
    assert manifest["status"] == "active"
    assert len(manifest["research_questions"]) == 1
    assert manifest["stats"] == {
        "discovered_papers": 0, "verified_papers": 0,
        "downloaded_pdfs": 0, "extracted_markdowns": 0,
    }

    # Deterministic placeholder protocol.
    intent = json.loads((target / "intent.json").read_text(encoding="utf-8"))
    assert intent["project_slug"] == "on-device-weed-detection"
    assert intent["playbook_type"] == "PRISMA_SLR"
    protocol = (target / "protocol.json").read_bytes()
    expected_fp = "sha256:" + __import__("hashlib").sha256(protocol).hexdigest()
    assert result["protocol_fingerprint"] == expected_fp

    # Audit events: workspace-manager PROJECT_INITIALIZED + nexus-scholar/init GENESIS.
    events = _journal(target)
    actions = [e["action"] for e in events]
    assert "PROJECT_INITIALIZED" in actions and "GENESIS" in actions
    init_evt = next(e for e in events if e["action"] == "PROJECT_INITIALIZED")
    assert init_evt["agent_or_tool"] == "workspace-manager"
    assert "project.json" in init_evt["outputs"]
    assert "synthesis/literature_review.md" in init_evt["outputs"]
    assert init_evt["parameters"]["slug"] == "on-device-weed-detection"
    genesis = next(e for e in events if e["action"] == "GENESIS")
    assert genesis["agent_or_tool"] == "nexus-scholar/init"
    assert "placeholder protocol fingerprint" in genesis["description"]
    assert genesis["status"] == "SUCCESS"


def test_init_scaffold_only_is_deterministic(tmp_path, monkeypatch):
    frozen = "2026-09-01T00:00:00+00:00"
    monkeypatch.setattr(inception, "_now_iso", lambda: frozen)

    a = init_command("Reproducible ML Pipelines", tmp_path / "a", scaffold_only=True)
    b = init_command("Reproducible ML Pipelines", tmp_path / "b", scaffold_only=True)

    assert a["protocol_fingerprint"] == b["protocol_fingerprint"]
    assert a["protocol_fingerprint"].startswith("sha256:")
    assert (tmp_path / "a" / "protocol.json").read_bytes() == (tmp_path / "b" / "protocol.json").read_bytes()
    assert (tmp_path / "a" / "intent.json").read_bytes() == (tmp_path / "b" / "intent.json").read_bytes()
    intent = json.loads((tmp_path / "a" / "intent.json").read_text(encoding="utf-8"))
    assert intent["genesis_timestamp"] == frozen


# ---------------------------------------------------------------------------
# refusal rule + slugification
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("marker", ["project.json", "intent.json", "audit/journal.jsonl", ".mcp.json"])
def test_init_refuses_existing_nucleus(tmp_path, marker):
    target = tmp_path / "nucleus"
    (target / marker).parent.mkdir(parents=True, exist_ok=True)
    (target / marker).write_text("{}", encoding="utf-8")
    with pytest.raises(typer.Exit) as excinfo:
        init_command("Should Refuse", target, scaffold_only=True)
    assert excinfo.value.exit_code == 1
    assert not (target / "protocol.json").exists(), "refusal must write nothing"

    # while the marker stays, the dir must stay untouched
    assert (target / marker).read_text(encoding="utf-8") == "{}"


def test_init_refuses_existing_file_target(tmp_path):
    target = tmp_path / "file-as-dir"
    target.write_text("this is a file, not a directory", encoding="utf-8")
    with pytest.raises(typer.Exit) as excinfo:
        init_command("File Target", target, scaffold_only=True)
    assert excinfo.value.exit_code == 1
    assert target.read_text(encoding="utf-8") == "this is a file, not a directory"


def test_init_non_empty_folder_without_markers_is_fine(tmp_path):
    target = tmp_path / "docs"
    target.mkdir()
    (target / "notes.txt").write_text("unrelated", encoding="utf-8")
    result = init_command("Mixed Content", target, scaffold_only=True)
    assert result["slug"] == "mixed-content"
    assert (target / "protocol.json").is_file()
    assert (target / "notes.txt").exists()


def test_slugify_used_for_workspace_name(tmp_path):
    target = tmp_path / "w"
    init_command("The: Study of Chunking!!!", target, scaffold_only=True)
    manifest = json.loads((target / "project.json").read_text(encoding="utf-8"))
    assert manifest["project_id"] == "the-study-of-chunking"


# ---------------------------------------------------------------------------
# support files: .env.example, .mcp.json, skills vendoring
# ---------------------------------------------------------------------------


def test_init_writes_env_template_without_secrets(tmp_path):
    target = tmp_path / "proj"
    init_command("Env Check", target, scaffold_only=True)
    env = (target / ".env.example").read_text(encoding="utf-8")
    for key in ("SCHOLAR_MAILTO", "SCHOLAR_OPENALEX_KEY", "SCHOLAR_S2_KEY",
                "OPENAI_API_KEY", "GEMINI_API_KEY", "NEXUS_RECON_ROOT", "NEXUS_SKILLS_SRC"):
        assert f"{key}=" in env
    # Placeholders only: no real secrets, and API keys are left empty.
    assert "SCHOLAR_MAILTO=you@example.com" in env
    assert "NEXUS_RECON_ROOT=.cache/inception_recon" in env
    for line in env.splitlines():
        if line.startswith("SCHOLAR_OPENALEX_KEY="):
            assert line.endswith("=")
        if line.startswith("OPENAI_API_KEY="):
            assert line.endswith("=")
        if line.startswith("GEMINI_API_KEY="):
            assert line.endswith("=")


def test_init_writes_absolute_mcp_json(tmp_path):
    target = tmp_path / "proj"
    init_command("Mcp Wiring", target, scaffold_only=True)
    cfg = json.loads((target / ".mcp.json").read_text(encoding="utf-8"))
    server = cfg["mcpServers"]["nexus-scholar"]
    assert server["command"] == "uvx"
    assert server["args"][:2] == ["--from", "nexus-scholar"]
    assert "scholar-agent" in server["args"]
    i = server["args"].index("--workspace")
    assert server["args"][i + 1] == str(target.resolve())
    assert "${workspaceFolder}" not in (target / ".mcp.json").read_text(encoding="utf-8")


def test_skills_install_copy_fallback_when_symlink_blocked(tmp_path, monkeypatch):
    def _blocked(*_args, **_kwargs):
        raise PermissionError("symlink requires privileges")

    monkeypatch.setattr(inception.os, "symlink", _blocked)
    source = resolve_skills_root()
    dest = tmp_path / "skills"
    records = install_skills(source, dest)
    assert records and all(r["mode"] == "copy" for r in records)
    assert (dest / "workspace-manager" / "SKILL.md").is_file()
    assert (dest / "workspace-manager").is_dir()
    assert not (dest / "workspace-manager").is_symlink()


def test_skills_install_symlink_when_allowed(tmp_path, monkeypatch):
    calls = []

    def _record(src, dst, target_is_directory=False):
        calls.append((src, dst, target_is_directory))

    monkeypatch.setattr(inception.os, "symlink", _record)
    source = resolve_skills_root()
    dest = tmp_path / "skills"
    records = install_skills(source, dest)
    assert records and all(r["mode"] == "symlink" for r in records)
    assert calls and all(c[2] is True for c in calls)
    assert {str(c[0]) for c in calls} == {r["source"] for r in records}


def test_skills_source_resolution_env_override(tmp_path, monkeypatch):
    fake = tmp_path / "fake-skills"
    (fake / "mini-skill").mkdir(parents=True)
    (fake / "mini-skill" / "SKILL.md").write_text("# Mini", encoding="utf-8")
    monkeypatch.setenv("NEXUS_SKILLS_SRC", str(fake))
    assert resolve_skills_root() == fake.resolve()

    dest = tmp_path / "vendored"
    records = install_skills(resolve_skills_root(), dest)
    assert [r["name"] for r in records] == ["mini-skill"]
    assert (dest / "mini-skill" / "SKILL.md").is_file()


# ---------------------------------------------------------------------------
# wizard handoff: run_wizard with target_dir scaffolds the RAW folder
# ---------------------------------------------------------------------------


def test_run_wizard_raw_target_handoff(tmp_path):
    root = tmp_path / "root"
    raw = tmp_path / "raw"
    result = run_wizard(
        ScriptedResponder(list(E2E_ANSWERS)),
        root,
        genesis_timestamp=GENESIS_TS,
        target_dir=raw,
        init_title="On-Device Weed Detection",
    )

    assert result["slug"] == "on-device-weed-detection-for-embedded-agriculture"
    assert result["paradigm"] == "Design Science"
    assert result["workspace_dir"] == str(raw.resolve())
    # No monorepo workspaces/<slug> tree anywhere.
    assert not (root / "workspaces").exists()

    for f in ("protocol.json", "intent.json", "project.json", "SCREENING_CRITERIA.md"):
        assert (raw / f).is_file(), f"missing {f} in raw target"
    assert (raw / "synthesis" / "literature_review.md").is_file()

    events = _journal(raw)
    init_evt = next(e for e in events if e["action"] == "PROJECT_INITIALIZED")
    assert init_evt["agent_or_tool"] == "workspace-manager"
    assert init_evt["parameters"]["title"] == "On-Device Weed Detection for Embedded Agriculture"
    genesis = next(e for e in events if e["action"] == "GENESIS")
    assert genesis["agent_or_tool"] == "scholar-harness/inception"
    assert all(e["status"] == "SUCCESS" for e in events)


def test_run_wizard_raw_target_accepts_init_title_default(tmp_path):
    """init_title only default-seeds the title prompt; a scripted title wins."""
    root = tmp_path / "root"
    raw = tmp_path / "raw"
    result = run_wizard(
        ScriptedResponder(list(E2E_ANSWERS)),
        root,
        genesis_timestamp=GENESIS_TS,
        target_dir=raw,
        init_title="Title Seed From CLI",
    )
    assert result["title"] == "On-Device Weed Detection for Embedded Agriculture"
    assert result["slug"] == "on-device-weed-detection-for-embedded-agriculture"


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_init_command_registered():
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "project_title" in result.stdout
    assert "--dir" in result.stdout
    assert "--scaffold-only" in result.stdout
    assert "Bootstrap a portable Nexus Scholar research workspace" in result.stdout


def test_init_cli_scaffold_only_smoke(tmp_path):
    target = tmp_path / "w"
    result = runner.invoke(
        app, ["init", "Microkernel Telemetry", "--dir", str(target), "--scaffold-only"]
    )
    assert result.exit_code == 0, result.stdout
    assert (target / "protocol.json").is_file()
    assert (target / ".mcp.json").is_file()


def test_init_cli_refuses_existing_marker(tmp_path):
    target = tmp_path / "w"
    target.mkdir()
    (target / "protocol.json").write_text("{}", encoding="utf-8")
    result = runner.invoke(
        app, ["init", "Clobber Attempt", "--dir", str(target), "--scaffold-only"]
    )
    assert result.exit_code == 1
    assert "Refusing" in result.stdout
    assert (target / "protocol.json").read_text(encoding="utf-8") == "{}"