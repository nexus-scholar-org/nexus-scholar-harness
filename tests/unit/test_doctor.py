"""P7.5 tests: ``nexus-scholar doctor`` — distribution-health checks.

Hermetic: ``tmp_path`` workspaces, an injectable ``{kit: importable}`` map for
the kits check, and monkeypatched resolver/check seams -- no network, no heavy
dependencies.

Seam-context note: the dev environment installs the harness as
``nexus-scholar-harness``; the ``scholar-agent`` entrypoint ships from the
``scholar-agent-kit`` console script. The ``nexus-scholar`` metapackage
entrypoint is wheel-provided and therefore asserted only where it is
guaranteed to exist (the ``uvx --from`` smoke).
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from scholar_harness import doctor as doctor_mod
from scholar_harness.cli import app
from scholar_harness.doctor import (
    CheckResult,
    Status,
    check_keys,
    check_kits,
    check_layout,
    check_seam,
    check_skills,
    load_kit_manifest,
)

runner = CliRunner()


def _pass_seam() -> list[CheckResult]:
    return [
        CheckResult("seam", "python-version", Status.PASS, "Python 3"),
        CheckResult("seam", "cli-import", Status.PASS, "app importable"),
        CheckResult("seam", "entrypoint-nexus-scholar", Status.PASS, "present"),
        CheckResult("seam", "entrypoint-scholar-agent", Status.PASS, "present"),
    ]


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_doctor_command_registered():
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    assert "--workspace" in result.stdout
    assert "--env-file" in result.stdout
    assert "--json" in result.stdout
    assert "--exit-code" in result.stdout
    assert "Validate kits/versions, API keys, skills, and workspace layout" in result.stdout


# ---------------------------------------------------------------------------
# kits
# ---------------------------------------------------------------------------


def test_kits_all_importable_dev_env():
    manifest = load_kit_manifest()
    assert len(manifest) == 8  # all 8 scholar-*-kit packages declared
    results = check_kits()
    assert [r.name for r in results] == list(manifest)
    assert all(r.status == Status.PASS for r in results)
    # every declared kit carries its pinned default_rev in the detail
    assert all("pinned" in r.detail for r in results)


def test_load_kit_manifest_wheel_fallback(tmp_path, monkeypatch):
    """The wheel-deployed scenario: no repo plugins.json, bundled pins snapshot."""
    pins = tmp_path / "nexus_scholar_pins.json"
    pins.write_text(
        json.dumps(
            {"kits": [{"name": "scholar-rag-kit", "default_rev": "abc123"}, {"name": "other"}]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(doctor_mod, "_repo_plugins_json", lambda: tmp_path / "ghost")
    monkeypatch.setattr(doctor_mod, "_wheel_pins_path", lambda: pins)
    manifest = load_kit_manifest()
    assert manifest == {"scholar-rag-kit": "abc123", "other": ""}
    # no repo, no wheel -> empty manifest (doctor stays usable)
    monkeypatch.setattr(doctor_mod, "_wheel_pins_path", lambda: None)
    assert load_kit_manifest() == {}


def test_kits_fail_reachable_via_importable_map():
    names = [r.name for r in check_kits()]
    importable_map = dict.fromkeys(names, True)
    importable_map["scholar-rag-kit"] = False
    results = check_kits(importable_map=importable_map)
    assert [r.name for r in results] == names
    assert any(r.status == Status.FAIL for r in results)
    rag = next(r for r in results if r.name == "scholar-rag-kit")
    assert "import FAILED" in rag.detail


def test_cli_doctor_fail_reachable_via_monkeypatch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor_mod,
        "check_kits",
        lambda importable_map=None: [CheckResult("kits", "scholar-rag-kit", Status.FAIL, "import FAILED")],
    )
    result = runner.invoke(app, ["doctor", "--workspace", str(tmp_path)])
    assert result.exit_code == 0  # advisory default
    assert "FAIL" in result.stdout


# ---------------------------------------------------------------------------
# keys (presence checks, values never echoed)
# ---------------------------------------------------------------------------


def test_keys_mailto_pass_model_keys_warn_not_fail(tmp_path):
    env = tmp_path / ".env"
    env.write_text("SCHOLAR_MAILTO=me@example.com\n", encoding="utf-8")
    results = check_keys(env)
    by_name = {r.name: r.status for r in results}
    assert by_name["SCHOLAR_MAILTO"] == Status.PASS
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        assert by_name[key] == Status.WARN
    assert not any(r.status == Status.FAIL for r in results)
    assert not any("me@example.com" in r.detail for r in results)


def test_keys_no_env_file_skips():
    results = check_keys(None)
    assert len(results) == 1
    assert results[0].status == Status.SKIP


def test_keys_missing_mailto_warns(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=sk-value\n", encoding="utf-8")
    results = check_keys(env)
    by_name = {r.name: r.status for r in results}
    assert by_name["SCHOLAR_MAILTO"] == Status.WARN
    assert by_name["OPENAI_API_KEY"] == Status.PASS


# ---------------------------------------------------------------------------
# skills
# ---------------------------------------------------------------------------


def test_skills_pass_when_resolver_has_skills(tmp_path):
    root = tmp_path / "skills-root"
    (root / "scholar-search-kit").mkdir(parents=True)
    (root / "scholar-search-kit" / "SKILL.md").write_text("# scholar-search\n", encoding="utf-8")
    results = check_skills(skills_root=root)
    assert len(results) == 1
    assert results[0].status == Status.PASS


def test_skills_fail_when_resolver_none(monkeypatch):
    monkeypatch.setattr("scholar_harness.inception.resolve_skills_root", lambda: None)
    results = check_skills()
    assert len(results) == 1
    assert results[0].status == Status.FAIL
    assert "NEXUS_SKILLS_SRC" in results[0].detail  # guidance line present


# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------


def _scaffold(tmp_path):
    from scholar_harness.inception import init_command

    ws = tmp_path / "proj"
    init_command("Doctor Test Project", ws, scaffold_only=True)
    return ws


def test_layout_pass_on_scaffolded_workspace(tmp_path):
    ws = _scaffold(tmp_path)
    results = check_layout(ws)
    assert results
    assert any(r.name == "canonical-files" and r.status == Status.PASS for r in results)
    assert not any(r.status == Status.FAIL for r in results)


def test_layout_fail_when_protocol_removed(tmp_path):
    ws = _scaffold(tmp_path)
    (ws / "protocol.json").unlink()
    results = check_layout(ws)
    assert any(r.status == Status.FAIL for r in results)
    canonical = next(r for r in results if r.name == "canonical-files")
    assert "protocol.json" in canonical.detail


def test_layout_skip_on_empty_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    results = check_layout(empty)
    assert results
    assert all(r.status == Status.SKIP for r in results)


def test_layout_bom_tolerant_when_stats_stale(tmp_path):
    """Windows tools write UTF-8 BOM; doctor must still read/parse project.json."""
    ws = _scaffold(tmp_path)
    (ws / "literature" / "raw_search.json").write_text("[{}]", encoding="utf-8")
    manifest = ws / "project.json"
    content = manifest.read_text(encoding="utf-8")
    manifest.write_text("\ufeff" + content, encoding="utf-8")
    results = check_layout(ws)
    stats = next(r for r in results if r.name == "project.json-stats")
    assert stats.status == Status.WARN  # stale (raw_search.json has 1 doc, declared 0) — not a parse failure


# ---------------------------------------------------------------------------
# --json: valid, machine-readable, secret-free
# ---------------------------------------------------------------------------


def test_json_output_valid_and_masked(tmp_path):
    secret = "sk-super-secret-doctor-test"
    mailto = "doctor-secret@example.com"
    env = tmp_path / ".env"
    env.write_text(f"SCHOLAR_MAILTO={mailto}\nOPENAI_API_KEY={secret}\n", encoding="utf-8")

    result = runner.invoke(
        app, ["doctor", "--workspace", str(tmp_path), "--env-file", str(env), "--json"]
    )
    assert result.exit_code == 0, result.stdout

    payload = json.loads(result.stdout)
    assert "checks" in payload and "overall" in payload
    assert all({"group", "name", "status", "detail"} <= set(c) for c in payload["checks"])

    # mask proof: no env values anywhere, present keys masked as ***
    text = result.stdout
    assert secret not in text
    assert mailto not in text
    keys = [c for c in payload["checks"] if c["group"] == "keys"]
    mailto_check = next(c for c in keys if c["name"] == "SCHOLAR_MAILTO")
    assert mailto_check["status"] == "PASS"
    assert mailto_check["detail"] == "***"


def test_doctor_default_env_file_from_workspace(tmp_path):
    ws = _scaffold(tmp_path)
    (ws / ".env").write_text("SCHOLAR_MAILTO=a@b.c\n", encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--workspace", str(ws), "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    keys = [c for c in payload["checks"] if c["group"] == "keys"]
    assert any(c["name"] == "SCHOLAR_MAILTO" and c["status"] == "PASS" for c in keys)
    assert "a@b.c" not in result.stdout


# ---------------------------------------------------------------------------
# seam
# ---------------------------------------------------------------------------


def test_seam_entrypoints_and_python_version():
    results = check_seam()
    by_name = {r.name: r.status for r in results}
    assert by_name["cli-import"] == Status.PASS
    assert by_name["python-version"] == Status.PASS
    # scholar-agent is present in the dev environment's console_scripts
    assert by_name["entrypoint-scholar-agent"] == Status.PASS
    # The nexus-scholar metapackage entrypoint is wheel-provided: PASS inside
    # the installed wheel, WARN in a repo/dev checkout — never FAIL (clamp:
    # a healthy dev workspace must not report overall FAIL on its seam).
    assert by_name["entrypoint-nexus-scholar"] in (Status.PASS, Status.WARN)
    version = next(r for r in results if r.name == "python-version")
    assert version.detail.startswith("Python ")


# ---------------------------------------------------------------------------
# --exit-code: opt-in; only FAIL trips it
# ---------------------------------------------------------------------------


def test_exit_code_flag_exits_1_on_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor_mod,
        "check_kits",
        lambda importable_map=None: [CheckResult("kits", "scholar-rag-kit", Status.FAIL, "import FAILED")],
    )
    result = runner.invoke(app, ["doctor", "--workspace", str(tmp_path), "--exit-code"])
    assert result.exit_code == 1


def test_advisory_default_exits_0_despite_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor_mod,
        "check_kits",
        lambda importable_map=None: [CheckResult("kits", "scholar-rag-kit", Status.FAIL, "import FAILED")],
    )
    result = runner.invoke(app, ["doctor", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "FAIL" in result.stdout


def test_exit_code_not_tripped_by_warn(tmp_path, monkeypatch):
    """Wheel-style scenario: missing model keys WARN but never trip --exit-code."""
    monkeypatch.setattr(
        doctor_mod,
        "check_keys",
        lambda env_file=None: [CheckResult("keys", "OPENAI_API_KEY", Status.WARN, "Missing (optional)")],
    )
    monkeypatch.setattr(doctor_mod, "check_seam", lambda: _pass_seam())
    ws = tmp_path / "ws"
    ws.mkdir()
    result = runner.invoke(app, ["doctor", "--workspace", str(ws), "--exit-code"])
    assert result.exit_code == 0
    assert "WARN" in result.stdout