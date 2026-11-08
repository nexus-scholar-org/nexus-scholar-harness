"""The inception-agent emit helper goes through the gated genesis path (M4a)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from conftest import E2E_ANSWERS, GENESIS_TS, ScriptedResponder

from scholar_harness.inception import run_wizard

HELPER = Path(".agents/skills/inception-agent/scripts/emit_protocol.py").resolve()


def _helper():
    spec = importlib.util.spec_from_file_location("emit_protocol_helper", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _intent(tmp_path) -> Path:
    first = run_wizard(ScriptedResponder(list(E2E_ANSWERS)), tmp_path / "first", genesis_timestamp=GENESIS_TS)
    path = tmp_path / "intent.json"
    path.write_text(json.dumps(first["intent"]), encoding="utf-8")
    return path


def test_preview_writes_nothing_and_shows_the_criteria(tmp_path, capsys):
    intent = _intent(tmp_path)
    capsys.readouterr()
    root = tmp_path / "repo"
    assert _helper().main(["--intent", str(intent), "--root", str(root), "--preview"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PREVIEW" and out["written"] == []
    assert "Reports the gold-standard proof" in out["screening_criteria"]
    assert not root.exists()


def test_emit_then_refuse_then_replace(tmp_path, capsys):
    intent = _intent(tmp_path)
    capsys.readouterr()
    target = tmp_path / "ws"
    helper = _helper()
    assert helper.main(["--intent", str(intent), "--dir", str(target)]) == 0
    capsys.readouterr()
    assert (target / "protocol.json").is_file()

    assert helper.main(["--intent", str(intent), "--dir", str(target)]) == 3
    refused = json.loads(capsys.readouterr().out)
    assert refused["code"] == "WORKSPACE_EXISTS"

    assert helper.main(["--intent", str(intent), "--dir", str(target), "--replace"]) == 0
    replaced = json.loads(capsys.readouterr().out)
    assert replaced["replaced"] is True
    assert Path(replaced["backup_dir"], "protocol.json").is_file()
