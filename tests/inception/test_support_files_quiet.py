"""F9 (three-phase review 2026-11-10): installing a workspace's skills prints nothing.

Genesis runs inside an API request; the per-skill "COPIED (symlink unavailable)"
paragraph went to the process's stdout. It now goes through logging, and the
command line (`nexus-scholar init`) tells the researcher once, in a summary.
"""

from __future__ import annotations

import logging

from scholar_harness.inception import genesis


def _records(*modes):
    return [{"name": f"skill-{i}", "mode": mode, "source": f"/src/skill-{i}"} for i, mode in enumerate(modes)]


def test_installing_skills_prints_nothing_and_logs_each_skill(tmp_path, monkeypatch, capsys, caplog):
    monkeypatch.setattr(genesis, "resolve_skills_root", lambda: tmp_path)
    monkeypatch.setattr(genesis, "install_skills", lambda source, dest: _records("copy", "symlink", "existing"))
    monkeypatch.setattr(genesis, "_generate_skill_meta_records", lambda target, root: {})
    with caplog.at_level(logging.INFO, logger=genesis.__name__):
        support = genesis.install_workspace_support_files(tmp_path)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
    text = caplog.text
    assert "skill-0" in text and "COPIED" in text
    assert "skill-1" in text and "symlinked" in text
    assert "skill-2" in text and "kept existing" in text
    assert [r["mode"] for r in support["skill_records"]] == ["copy", "symlink", "existing"]


def test_a_missing_skill_source_is_a_logged_warning_not_a_print(tmp_path, monkeypatch, capsys, caplog):
    monkeypatch.setattr(genesis, "resolve_skills_root", lambda: None)
    monkeypatch.setattr(genesis, "_generate_skill_meta_records", lambda target, root: {})
    with caplog.at_level(logging.WARNING, logger=genesis.__name__):
        genesis.install_workspace_support_files(tmp_path)
    assert capsys.readouterr().out == ""
    assert "no skill source found" in caplog.text


def test_scaffolding_a_workspace_through_the_step_path_prints_no_skill_lines(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(genesis, "install_skills", lambda source, dest: _records("copy", "copy"))
    genesis.scaffold_placeholder_workspace(tmp_path / "ws", "A title", agent="test")
    assert "COPIED" not in capsys.readouterr().out


def test_the_command_line_says_once_that_skills_were_copied(tmp_path, monkeypatch, capsys):
    from scholar_harness.inception import init_command

    monkeypatch.setattr(genesis, "install_skills", lambda source, dest: _records("copy", "copy", "copy"))
    init_command("A title", tmp_path / "proj", scaffold_only=True)
    out = capsys.readouterr().out
    assert out.count("COPIED") == 1
    assert "3 skills were COPIED" in " ".join(out.split())
