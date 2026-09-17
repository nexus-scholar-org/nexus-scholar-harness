"""P7.6 tests: ``nexus-scholar log`` — append-only audit-contract CLI (event/batch/sync-index).

Hermetic: ``tmp_path`` workspaces scaffolded via ``init_command(..., scaffold_only=True)``,
``CliRunner`` invocations, and monkeypatched resolver seams (the wheel-bundle
leg) -- no network, no heavy dependencies.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import shutil
from pathlib import Path

from typer.testing import CliRunner

from scholar_harness import inception
from scholar_harness.cli import app
from scholar_harness.inception import init_command

runner = CliRunner()

REPO_ROOT = Path(__file__).resolve().parents[2]
EVT_RE = re.compile(r"^EVT-\d{14}-[0-9a-f]{6}$")


def _norm(s: str) -> str:
    """Collapse newlines/whitespace so rich Console wrapping never splits a
    phrase we assert on."""
    return re.sub(r"\s+", " ", s).strip()


def _journal(ws: Path) -> list[dict]:
    journal = ws / "audit" / "journal.jsonl"
    text = journal.read_text(encoding="utf-8")
    events = []
    for line in text.splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def _scaffold(tmp_path: Path, title: str = "Audit Log QA") -> Path:
    ws = tmp_path / "ws"
    init_command(title, ws, scaffold_only=True)
    return ws


def _manifest(ws: Path) -> dict:
    return json.loads((ws / "project.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_log_help_lists_three_subcommands():
    result = runner.invoke(app, ["log", "--help"])
    assert result.exit_code == 0
    for name in ("event", "batch", "sync-index"):
        assert name in result.stdout


def test_log_event_help_exposes_flags_and_policy():
    result = runner.invoke(app, ["log", "event", "--help"])
    assert result.exit_code == 0
    for flag in ("--action", "--agent", "--description", "--inputs",
                 "--outputs", "--status", "--param", "--metric"):
        assert flag in result.stdout


def test_log_batch_help_documents_lenient_skip_policy():
    result = runner.invoke(app, ["log", "batch", "--help"])
    assert result.exit_code == 0
    assert "Lenient-skip" in result.stdout
    assert "JSON-parse-clean" in result.stdout


# ---------------------------------------------------------------------------
# log event
# ---------------------------------------------------------------------------


def test_log_event_canonical_schema(tmp_path):
    ws = _scaffold(tmp_path)
    before = _journal(ws)
    updated_before = _manifest(ws)["updated_at"]

    result = runner.invoke(app, [
        "log", "event", str(ws),
        "--action", "DISCOVERY_SEARCH",
        "--agent", "scholar-search-kit",
        "--description", "probe",
    ])
    assert result.exit_code == 0, result.output

    events = _journal(ws)
    assert len(events) == len(before) + 1
    record = events[-1]
    assert record["action"] == "DISCOVERY_SEARCH"
    assert record["agent_or_tool"] == "scholar-search-kit"
    assert record["description"] == "probe"
    assert record["status"] == "SUCCESS"
    assert EVT_RE.match(record["event_id"])
    _dt.datetime.fromisoformat(record["timestamp"])  # ISO timestamp, parseable
    assert record["inputs"] == []
    assert record["outputs"] == []
    assert record["parameters"] == {}
    assert record["metrics"] == {}

    # The old events are untouched (append-only).
    assert events[:-1] == before

    # project.json.updated_at bumped.
    assert _manifest(ws)["updated_at"] > updated_before

    # INDEX.md refreshed and carries the project slug.
    index_text = (ws / "INDEX.md").read_text(encoding="utf-8")
    assert "`audit-log-qa`" in index_text

    # Standard "Logged event [...] -> path" line printed (by log_event.py).
    assert "Logged event [DISCOVERY_SEARCH]" in result.output
    assert str(ws / "audit" / "journal.jsonl") in result.output


def test_log_event_roundtrips_status_params_metrics_inputs_outputs(tmp_path):
    ws = _scaffold(tmp_path)
    result = runner.invoke(app, [
        "log", "event", str(ws),
        "--action", "screening_round",
        "--agent", "scholar-search-kit",
        "--description", "round 2",
        "--status", "failed",
        "--param", "round=2",
        "--param", "mode=semi",
        "--metric", "screened=10",
        "--inputs", "in_a",
        "--inputs", "in_b",
        "--outputs", "out_a",
        "--outputs", "out_b",
    ])
    assert result.exit_code == 0, result.output

    record = _journal(ws)[-1]
    assert record["action"] == "SCREENING_ROUND"
    assert record["status"] == "FAILED"
    assert record["parameters"] == {"round": "2", "mode": "semi"}
    assert record["metrics"] == {"screened": "10"}
    assert record["inputs"] == ["in_a", "in_b"]
    assert record["outputs"] == ["out_a", "out_b"]


def test_log_event_space_separated_inputs(tmp_path):
    ws = _scaffold(tmp_path)
    result = runner.invoke(app, [
        "log", "event", str(ws),
        "--action", "EXPORT",
        "--description", "exports",
        "--inputs", "a.xml b.json",
        "--outputs", "out.csv out.json",
    ])
    assert result.exit_code == 0, result.output
    record = _journal(ws)[-1]
    assert record["inputs"] == ["a.xml", "b.json"]
    assert record["outputs"] == ["out.csv", "out.json"]


def test_log_event_refuses_non_workspace_dir(tmp_path):
    plain = tmp_path / "plain-dir"
    plain.mkdir()
    result = runner.invoke(app, [
        "log", "event", str(plain),
        "--action", "PROBE",
        "--description", "must refuse",
    ])
    assert result.exit_code == 1
    assert "Not a Nexus Scholar workspace" in result.output
    assert not (plain / "audit" / "journal.jsonl").exists(), (
        "refusal must not create an audit ledger in a plain dir"
    )
    assert not (plain / "INDEX.md").exists()


def test_log_event_refuses_nonexistent_target(tmp_path):
    missing = tmp_path / "no-such-workspace"
    result = runner.invoke(app, [
        "log", "event", str(missing),
        "--action", "PROBE",
        "--description", "must refuse",
    ])
    assert result.exit_code == 1
    assert "Not a Nexus Scholar workspace" in result.output


def test_log_event_refuses_bad_kv_flag(tmp_path):
    ws = _scaffold(tmp_path)
    before = len(_journal(ws))
    result = runner.invoke(app, [
        "log", "event", str(ws),
        "--action", "PROBE",
        "--description", "bad param",
        "--param", "no-equals-sign",
    ])
    assert result.exit_code == 1
    assert "must be KEY=VALUE" in result.output
    # Nothing appended: the bad flag is rejected before any write.
    assert len(_journal(ws)) == before


# ---------------------------------------------------------------------------
# log batch
# ---------------------------------------------------------------------------


def _write_events(ws_events: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(json.dumps(record) + "\n" for record in ws_events)


def _valid_event(action: str, **extra) -> dict:
    record = {"action": action, "description": f"{action} step"}
    record.update(extra)
    return record


def test_log_batch_all_valid(tmp_path):
    ws = _scaffold(tmp_path)
    events_file = tmp_path / "events.jsonl"
    _write_events([
        _valid_event("SCREEN_PREPARE", agent_or_tool="agent", inputs=["a"], outputs=["b"]),
        _valid_event("SCREEN_COLLECT", status="FAILED", metrics={"screened": "12"}),
        _valid_event("PDF_GATHER", parameters={"shard": "3"}),
    ], events_file)
    before = len(_journal(ws))

    result = runner.invoke(app, ["log", "batch", str(ws), str(events_file)])
    assert result.exit_code == 0, result.output
    assert "Logged 3 event(s)" in _norm(result.output)
    assert "0 record error(s)" in _norm(result.output)

    events = _journal(ws)
    assert len(events) == before + 3
    assert [e["action"] for e in events[-3:]] == [
        "SCREEN_PREPARE", "SCREEN_COLLECT", "PDF_GATHER"
    ]
    assert events[-2]["metrics"] == {"screened": "12"}
    assert events[-1]["parameters"] == {"shard": "3"}
    assert events[-3]["inputs"] == ["a"] and events[-3]["outputs"] == ["b"]
    assert all(e["status"] in ("SUCCESS", "FAILED") for e in events[-3:])
    # one "Logged event" line per appended record + summary
    assert result.output.count("Logged event [") == 3


def test_log_batch_skips_missing_action_record(tmp_path):
    ws = _scaffold(tmp_path)
    events_file = tmp_path / "events.jsonl"
    _write_events([
        _valid_event("ONE"),
        _valid_event("TWO"),
        _valid_event("THREE"),
        {"description": "missing action"},
    ], events_file)
    before = len(_journal(ws))

    result = runner.invoke(app, ["log", "batch", str(ws), str(events_file)])
    assert result.exit_code == 1
    assert "missing required 'action'" in result.stdout + result.stderr
    assert "1 record error(s)" in _norm(result.output)

    events = _journal(ws)
    assert len(events) == before + 3
    assert all(json.loads(line) for line in (ws / "audit" / "journal.jsonl")
               .read_text(encoding="utf-8").splitlines() if line.strip()), (
        "journal must stay JSON-parse-clean"
    )


def test_log_batch_malformed_json_line(tmp_path):
    ws = _scaffold(tmp_path)
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        '{"action": "OK_EVENT", "description": "fine"}\n'
        "this is not json {{\n",
        encoding="utf-8",
    )
    before = len(_journal(ws))

    result = runner.invoke(app, ["log", "batch", str(ws), str(events_file)])
    assert result.exit_code == 1
    assert "malformed JSON" in result.stdout + result.stderr

    events = _journal(ws)
    assert len(events) == before + 1
    assert events[-1]["action"] == "OK_EVENT"
    # Every journal line remains parse-clean.
    for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            json.loads(line)


def test_log_batch_missing_file(tmp_path):
    ws = _scaffold(tmp_path)
    result = runner.invoke(app, ["log", "batch", str(ws), str(tmp_path / "nope.jsonl")])
    assert result.exit_code == 1
    assert "Events file not found" in result.output
    assert len(_journal(ws)) == 2  # init's two events only; nothing appended


# ---------------------------------------------------------------------------
# log sync-index
# ---------------------------------------------------------------------------


def test_log_sync_index_refreshes_without_appending(tmp_path):
    ws = _scaffold(tmp_path)
    before = len(_journal(ws))
    # Corrupt INDEX.md; sync-index must regenerate (drop the junk).
    index_path = ws / "INDEX.md"
    index_path.write_text("JUNK THAT MUST BE REGENERATED\n", encoding="utf-8")

    result = runner.invoke(app, ["log", "sync-index", str(ws)])
    assert result.exit_code == 0, result.output
    assert "Refreshed INDEX.md" in result.output

    regenerated = index_path.read_text(encoding="utf-8")
    assert "JUNK" not in regenerated
    assert "`audit-log-qa`" in regenerated  # project slug back in the index
    assert len(_journal(ws)) == before  # *no* journal append
    assert not result.output.count("Logged event [")


# ---------------------------------------------------------------------------
# slug resolution (script's workspaces/<slug> fallback, CWD-relative)
# ---------------------------------------------------------------------------


def test_log_event_resolves_workspace_by_slug(tmp_path, monkeypatch):
    parent = tmp_path / "workspaces"
    ws = parent / "qa-slug-workspace"
    init_command("QA Slug Workspace", ws, scaffold_only=True)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, [
        "log", "event", "qa-slug-workspace",
        "--action", "SLUG_PROBE",
        "--description", "slug resolution",
    ])
    assert result.exit_code == 0, result.output
    assert _journal(ws)[-1]["action"] == "SLUG_PROBE"


# ---------------------------------------------------------------------------
# wheel-bundle loader: resolver reaches an alternative source root
# ---------------------------------------------------------------------------


def test_log_event_uses_wheel_bundled_log_module(tmp_path, monkeypatch):
    """Simulate the wheel env: the resolver's bundle root is a standalone copy
    of the workspace-manager scripts tree (what the wheel ships as
    ``scholar_harness_data/skills``), NOT the repo checkout.  ``uvx --from
    nexus-scholar`` from an arbitrary cwd is exactly this configuration."""
    ws = _scaffold(tmp_path)

    source_script = (
        REPO_ROOT / ".agents" / "skills" / "workspace-manager" / "scripts" / "log_event.py"
    )
    assert source_script.is_file()
    fake_bundle = tmp_path / "wheel-bundle-skills"
    (fake_bundle / "workspace-manager" / "scripts").mkdir(parents=True)
    shutil.copy2(source_script, fake_bundle / "workspace-manager" / "scripts" / "log_event.py")

    monkeypatch.delenv("NEXUS_SKILLS_SRC", raising=False)
    monkeypatch.setattr(inception, "_bundled_skills_root", lambda: fake_bundle)
    monkeypatch.setattr(inception, "_log_module_ref", None)
    monkeypatch.setattr(inception, "_log_module_tried", False)

    # Run from a bare, non-repo cwd -- the loader must still find the script.
    bare_cwd = tmp_path / "bare-cwd"
    bare_cwd.mkdir(exist_ok=True)
    monkeypatch.chdir(bare_cwd)

    result = runner.invoke(app, [
        "log", "event", str(ws),
        "--action", "WHEEL_PROBE",
        "--description", "wheel bundle loader",
    ])
    assert result.exit_code == 0, result.output
    # the resolved module must come from the bundle, not the repo checkout
    mod = inception._log_module_ref
    assert mod is not None
    assert str(Path(mod.__file__).resolve()).startswith(str(fake_bundle.resolve()))
    assert _journal(ws)[-1]["action"] == "WHEEL_PROBE"