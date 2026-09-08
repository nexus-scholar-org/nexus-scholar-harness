"""Hermetic tests for the M5.4 PipelineSpec DAG executor + CLI `--pipeline`.

Covers: topological scheduling, `{{...}}` template resolution against settings
and node outputs (incl. output-reference form `{{node_id.path}}`), subprocess
execution, `on_fail` (abort/skip/continue), `requires_decision` halt + resume,
idempotent re-runs, validation rejections, and the CLI wiring.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scholar_harness.cli import app
from scholar_harness.pipeline_executor import (
    PipelineError,
    build_command,
    execute_file,
    load_spec,
    requires_decision_satisfied,
    resolve_args,
)

runner = CliRunner()

CODE_WRITE = (
    "import pathlib,argparse,sys;"
    "p=argparse.ArgumentParser();p.add_argument('--out');p.add_argument('--content');"
    "a=p.parse_args(sys.argv[1:]);"
    "pathlib.Path(a.out).parent.mkdir(parents=True,exist_ok=True);"
    "pathlib.Path(a.out).write_text(a.content)"
)
CODE_N2_ASSERT = (
    "import pathlib,argparse,sys;"
    "p=argparse.ArgumentParser();"
    "p.add_argument('--input');p.add_argument('--out');p.add_argument('--content');"
    "a=p.parse_args(sys.argv[1:]);"
    "assert pathlib.Path(a.input).read_text()=='n1','node ref not resolved';"
    "assert a.content=='boom','settings ref not resolved';"
    "pathlib.Path(a.out).write_text('n2')"
)
CODE_FAIL = "import sys;sys.exit(7)"


def _spec_dict(**overrides):
    base = {
        "schema_version": "0.1.0",
        "id": "test_pipeline",
        "name": "Test DAG",
        "archetype": "PRISMA_SLR",
        "workspace_slug": "test-ws",
        "settings": {"queries": {"x": "boom"}},
        "nodes": [
            {
                "id": "n1",
                "kit": "test",
                "command": ["python", "-c", CODE_WRITE],
                "args": {"out": "literature/n1.json", "content": "n1"},
                "inputs": [],
                "outputs": ["literature/n1.json"],
                "on_fail": "abort",
            },
            {
                "id": "n2",
                "kit": "test",
                "command": ["python", "-c", CODE_N2_ASSERT],
                "args": {"input": "{{n1.literature/n1.json}}",
                         "out": "literature/n2.json",
                         "content": "{{queries.x}}"},
                "inputs": ["literature/n1.json"],
                "outputs": ["literature/n2.json"],
                "on_fail": "abort",
            },
        ],
        # edges populated below to cover both linear and divergent shapes
        "edges": [["n1", "n2"]],
        "dry_run": {},
        "created_by": "test",
    }
    base.update(overrides)
    return base


def _write_spec(tmp, spec: dict) -> Path:
    spec_file = tmp / "pipeline.json"
    spec_file.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return spec_file


def _bootstrap(tmp):
    ws = tmp / "ws"
    (ws / "literature").mkdir(parents=True)
    return ws


def test_load_spec_and_topological_order(tmp_path):
    ws = _bootstrap(tmp_path)
    spec_file = _write_spec(tmp_path, _spec_dict())
    spec = load_spec(spec_file)
    assert spec.id == "test_pipeline"
    results = execute_file(spec_file, ws)[1]
    assert [r.node_id for r in results] == ["n1", "n2"]
    assert all(r.state == "success" for r in results)
    assert (ws / "literature" / "n1.json").read_text() == "n1"
    assert (ws / "literature" / "n2.json").read_text() == "n2"


def test_template_resolution_node_output_ref_and_settings(tmp_path):
    spec = load_spec(_write_spec(tmp_path, _spec_dict()))
    n1 = spec.nodes[0]
    prior = {n1.id: {o: o for o in n1.outputs}}
    resolved = resolve_args(spec.nodes[1], spec, prior)
    assert resolved["input"] == "literature/n1.json"
    assert resolved["content"] == "boom"


def test_resolve_args_unresolved_template_raises(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = _spec_dict()
    spec["nodes"][1]["args"]["content"] = "{{missing_setting}}"
    with pytest.raises(PipelineError):
        execute_file(_write_spec(tmp_path, spec), ws)


def test_on_fail_abort_stops_pipeline(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = _spec_dict()
    spec["nodes"].append({
        "id": "bad", "kit": "test", "command": ["python", "-c", CODE_FAIL],
        "args": {}, "inputs": [], "outputs": [], "on_fail": "abort",
    })
    spec["nodes"].append({
        "id": "n3", "kit": "test", "command": ["python", "-c", CODE_WRITE],
        "args": {"out": "literature/n3.json", "content": "n3"},
        "inputs": [], "outputs": ["literature/n3.json"], "on_fail": "abort",
    })
    spec["edges"] = [["n1", "n2"], ["n2", "bad"], ["bad", "n3"]]
    with pytest.raises(PipelineError):
        execute_file(_write_spec(tmp_path, spec), ws)
    assert not (ws / "literature" / "n3.json").exists()


def test_on_fail_continue_keeps_running(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = _spec_dict()
    spec["nodes"].append({
        "id": "bad", "kit": "test", "command": ["python", "-c", CODE_FAIL],
        "args": {}, "inputs": [], "outputs": [], "on_fail": "continue",
    })
    spec["nodes"].append({
        "id": "n3", "kit": "test", "command": ["python", "-c", CODE_WRITE],
        "args": {"out": "literature/n3.json", "content": "n3"},
        "inputs": [], "outputs": ["literature/n3.json"], "on_fail": "abort",
    })
    spec["edges"] = [["n1", "n2"], ["n2", "bad"], ["bad", "n3"]]
    results = execute_file(_write_spec(tmp_path, spec), ws)[1]
    states = {r.node_id: r.state for r in results}
    assert states["bad"] == "failed"
    assert states["n3"] == "success"
    assert (ws / "literature" / "n3.json").exists()


def test_on_fail_skip_marks_skipped(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = _spec_dict()
    spec["nodes"].append({
        "id": "bad", "kit": "test", "command": ["python", "-c", CODE_FAIL],
        "args": {}, "inputs": [], "outputs": [], "on_fail": "skip",
    })
    spec["nodes"].append({
        "id": "n3", "kit": "test", "command": ["python", "-c", CODE_WRITE],
        "args": {"out": "literature/n3.json", "content": "n3"},
        "inputs": [], "outputs": ["literature/n3.json"], "on_fail": "abort",
    })
    spec["edges"] = [["n1", "n2"], ["n2", "bad"], ["bad", "n3"]]
    results = execute_file(_write_spec(tmp_path, spec), ws)[1]
    states = {r.node_id: r.state for r in results}
    assert states["bad"] == "skipped"
    assert states["n3"] == "success"


def test_requires_decision_halt_and_resume(tmp_path):
    ws = _bootstrap(tmp_path)
    (ws / "literature" / "screening").mkdir()
    CODE_BATCH = (
        "import pathlib,argparse,sys;"
        "p=argparse.ArgumentParser();p.add_argument('--out');"
        "a=p.parse_args(sys.argv[1:]);"
        "p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);"
        "p.write_text('{}')"
    )
    spec = _spec_dict()
    spec["nodes"].append({
        "id": "screen", "kit": "harness-agent-screen",
        "command": ["python", "-c", CODE_BATCH],
        "args": {"out": "literature/screening/batch_001.json"},
        "inputs": ["literature/n2.json"],
        "outputs": ["literature/screening/batch_*.json"],
        "on_fail": "abort",
        "requires_decision": True,
    })
    spec["edges"] = [["n1", "n2"], ["n2", "screen"]]
    spec_file = _write_spec(tmp_path, spec)

    with pytest.raises(PipelineError):
        execute_file(spec_file, ws)
    ok, pending = requires_decision_satisfied(ws)
    assert not ok and "batch_001.json" in pending
    assert (ws / "literature" / "screening" / "batch_001.json").exists()

    # Agent/GUI writes the decision file; resume is idempotent (node skipped).
    dummy = {"batch": 1, "decisions": [{"workspace_id": "X", "decision": "INCLUDE"}]}
    (ws / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(dummy), encoding="utf-8")
    results = execute_file(spec_file, ws)[1]
    screen = [r for r in results if r.node_id == "screen"]
    assert screen[0].state == "skipped" and screen[0].skipped_reason
    assert requires_decision_satisfied(ws)[0]


def test_idempotent_repeat_skips_existing_outputs(tmp_path):
    ws = _bootstrap(tmp_path)
    spec_file = _write_spec(tmp_path, _spec_dict())
    results = execute_file(spec_file, ws)[1]
    assert all(r.state == "success" for r in results)
    repeat = execute_file(spec_file, ws)[1]
    assert all(r.state == "skipped" for r in repeat)


def test_cycle_rejected(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = _spec_dict()
    spec["edges"] = [["n1", "n2"], ["n2", "n1"]]
    with pytest.raises(PipelineError) as exc:
        execute_file(_write_spec(tmp_path, spec), ws)
    assert "cycle" in str(exc.value)


def test_build_command_flags_and_repo_root(tmp_path):
    spec = _spec_dict()
    spec_file = _write_spec(tmp_path, spec)
    loaded = load_spec(spec_file)
    n1 = loaded.nodes[0]
    resolved = resolve_args(n1, loaded, {})
    cmd = build_command(n1, resolved, Path(str(tmp_path)))
    assert cmd[:2] == ["uv", "run"]
    assert "--out" in cmd and "--content" in cmd
    assert cmd[cmd.index("--out") + 1] == "literature/n1.json"

    # repo-relative "src/..." token resolves against the harness repo root
    real_root = Path(__file__).resolve().parents[1]
    assert real_root.joinpath("src/scholar_harness/agent_screen.py").exists()
    node_with_src = {
        "id": "s", "kit": "harness-agent-screen",
        "command": ["python", "src/scholar_harness/agent_screen.py", "prepare"],
        "args": {}, "inputs": [], "outputs": [], "on_fail": "abort",
        "requires_decision": False,
    }
    cmd2 = build_command(type(n1).model_validate(node_with_src), {}, Path(str(tmp_path)))
    assert "uv" == cmd2[0] and "run" == cmd2[1]
    agent_path = cmd2[cmd2.index("python") + 1]
    assert Path(agent_path).is_file() and agent_path.endswith("agent_screen.py")
    assert "prepare" in cmd2


def test_cli_run_pipeline_flag(tmp_path):
    ws = _bootstrap(tmp_path)
    spec_file = _write_spec(tmp_path, _spec_dict())
    result = runner.invoke(
        app,
        ["run", "--pipeline", str(spec_file), "--workspace", str(ws)],
    )
    assert result.exit_code == 0, result.output
    assert "PipelineSpec test_pipeline" in result.output
    assert (ws / "literature" / "n2.json").exists()


def test_cli_run_pipeline_halted_exit(tmp_path):
    ws = _bootstrap(tmp_path)
    CODE_BATCH = (
        "import pathlib,argparse,sys;"
        "p=argparse.ArgumentParser();p.add_argument('--out');"
        "a=p.parse_args(sys.argv[1:]);"
        "p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);"
        "p.write_text('{}')"
    )
    spec = _spec_dict()
    spec["nodes"].append({
        "id": "screen", "kit": "harness-agent-screen",
        "command": ["python", "-c", CODE_BATCH],
        "args": {"out": "literature/screening/batch_001.json"},
        "inputs": ["literature/n2.json"],
        "outputs": ["literature/screening/batch_*.json"],
        "on_fail": "abort",
        "requires_decision": True,
    })
    spec["edges"] = [["n1", "n2"], ["n2", "screen"]]
    spec_file = _write_spec(tmp_path, spec)
    result = runner.invoke(
        app,
        ["run", "--pipeline", str(spec_file), "--workspace", str(ws)],
    )
    assert result.exit_code == 1
    assert "Pipeline halted" in result.output
    assert "review" in result.output