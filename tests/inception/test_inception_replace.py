"""INC-08: re-running inception must not overwrite a live protocol.

`run_wizard` refuses a folder that already holds a workspace and writes
nothing. `replace=True` backs the old protocol files up under
`audit/replaced/<stamp>/`, keeps `project.json` (its `created_at`, `stats` and
identity), and logs GENESIS with the old fingerprint and the backup path. A
workspace with screening decisions or a publication also needs
`discard_screening_binding=True` (decision 2026-11-08, re-inception).
"""

from __future__ import annotations

import hashlib
import json
import re

import pytest
import typer
from conftest import E2E_ANSWERS, GENESIS_TS, ScriptedResponder
from typer.testing import CliRunner

from scholar_harness.cli import app
from scholar_harness.inception import run_wizard
from scholar_harness.inception.emit import screening_state

SLUG = "on-device-weed-detection-for-embedded-agriculture"
SENTINEL = b'{"sentinel": "live protocol"}'


def _journal(ws):
    return [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def _first_run(root, **kwargs):
    run_wizard(ScriptedResponder(list(E2E_ANSWERS)), root, genesis_timestamp=GENESIS_TS, **kwargs)


def _make_live(ws):
    """Stand in for a workspace that has been searched: stats, a date, a protocol."""
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    manifest["created_at"] = "2026-01-01T00:00:00+00:00"
    manifest["stats"]["discovered_papers"] = 812
    (ws / "project.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ws / "protocol.json").write_bytes(SENTINEL)
    return manifest


def test_rerun_refuses_an_existing_workspace_and_writes_nothing(tmp_path):
    _first_run(tmp_path)
    ws = tmp_path / "workspaces" / SLUG
    manifest = _make_live(ws)
    rows_before = len(_journal(ws))

    with pytest.raises(typer.Exit) as exc:
        _first_run(tmp_path)

    assert exc.value.exit_code == 1
    assert (ws / "protocol.json").read_bytes() == SENTINEL
    after = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert after["created_at"] == manifest["created_at"]
    assert after["stats"]["discovered_papers"] == 812
    assert len(_journal(ws)) == rows_before
    assert not (ws / "audit" / "replaced").exists()


def test_rerun_into_a_raw_folder_refuses_too(tmp_path):
    target = tmp_path / "raw"
    _first_run(tmp_path, target_dir=target)
    (target / "protocol.json").write_bytes(SENTINEL)

    with pytest.raises(typer.Exit):
        _first_run(tmp_path, target_dir=target)

    assert (target / "protocol.json").read_bytes() == SENTINEL


def test_replace_backs_up_the_old_protocol_and_keeps_the_manifest(tmp_path):
    _first_run(tmp_path)
    ws = tmp_path / "workspaces" / SLUG
    manifest = _make_live(ws)
    # The sentinel is not a protocol, so it is named by a labelled byte hash.
    old_fingerprint = "file-sha256:" + hashlib.sha256(SENTINEL).hexdigest()

    result = run_wizard(ScriptedResponder(list(E2E_ANSWERS)), tmp_path, genesis_timestamp=GENESIS_TS, replace=True)

    backups = list((ws / "audit" / "replaced").iterdir())
    assert len(backups) == 1
    assert (backups[0] / "protocol.json").read_bytes() == SENTINEL
    assert (backups[0] / "intent.json").is_file()
    assert (backups[0] / "SCREENING_CRITERIA.md").is_file()

    assert (ws / "protocol.json").read_bytes() != SENTINEL
    assert result["protocol_fingerprint"] == "sha256:" + hashlib.sha256((ws / "protocol.json").read_bytes()).hexdigest()

    after = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert after["created_at"] == manifest["created_at"]
    assert after["stats"]["discovered_papers"] == 812
    assert after["registered_workspace_id"] == manifest["registered_workspace_id"]

    rows = _journal(ws)
    assert [r["action"] for r in rows].count("PROJECT_INITIALIZED") == 1
    genesis = [r for r in rows if r["action"] == "GENESIS"][-1]
    assert old_fingerprint in genesis["description"]
    assert "audit/replaced/" in genesis["description"]


def _add_screening_decision(ws):
    events = ws / "literature" / "screening" / "events"
    events.mkdir(parents=True, exist_ok=True)
    (events / "researcher.jsonl").write_text('{"event_id": "e1"}\n{"event_id": "e2"}\n', encoding="utf-8")


def _add_batch_decisions(ws):
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True, exist_ok=True)
    (screening / "batch_000_decisions.json").write_text('{"decisions": []}', encoding="utf-8")


def _add_publication(ws):
    screening = ws / "literature" / "screening"
    screening.mkdir(parents=True, exist_ok=True)
    (screening / "generation.json").write_text('{"generation": 1}', encoding="utf-8")


@pytest.mark.parametrize(
    ("bind", "expected"),
    [
        (_add_screening_decision, {"decision_events": 2, "decision_files": 0, "published": False}),
        (_add_batch_decisions, {"decision_events": 0, "decision_files": 1, "published": False}),
        (_add_publication, {"decision_events": 0, "decision_files": 0, "published": True}),
    ],
    ids=["decision-events", "batch-decision-file", "publication"],
)
def test_replace_refuses_a_workspace_bound_to_screening(tmp_path, bind, expected):
    _first_run(tmp_path)
    ws = tmp_path / "workspaces" / SLUG
    _make_live(ws)
    bind(ws)
    assert {k: v for k, v in screening_state(ws).items() if k != "bound"} == expected

    with pytest.raises(typer.Exit) as exc:
        run_wizard(ScriptedResponder(list(E2E_ANSWERS)), tmp_path, genesis_timestamp=GENESIS_TS, replace=True)

    assert exc.value.exit_code == 1
    assert (ws / "protocol.json").read_bytes() == SENTINEL
    assert not (ws / "audit" / "replaced").exists()


def test_replace_with_discard_confirmation_proceeds_on_a_bound_workspace(tmp_path):
    _first_run(tmp_path)
    ws = tmp_path / "workspaces" / SLUG
    _make_live(ws)
    _add_screening_decision(ws)

    run_wizard(
        ScriptedResponder(list(E2E_ANSWERS)), tmp_path, genesis_timestamp=GENESIS_TS,
        replace=True, discard_screening_binding=True,
    )

    assert (ws / "protocol.json").read_bytes() != SENTINEL
    genesis = [r for r in _journal(ws) if r["action"] == "GENESIS"][-1]
    assert "2 screening decision events" in genesis["description"]


ANSI_PATTERN = r"\x1b\[[0-9;]*[A-Za-z]"  # a style code, written as an escape


def test_cli_offers_replace_and_the_discard_confirmation():
    raw = CliRunner().invoke(app, ["inception", "--help"], terminal_width=200).output
    # CI forces colour: Rich puts style codes inside the option names, so strip them.
    out = re.sub(ANSI_PATTERN, "", raw)
    assert "--replace" in out
    assert "--discard-screening-binding" in out
