"""Hermetic tests for M5.4 shell-script export (`export pipeline-sh`).

Covers:
  - render_pipeline_sh: deterministic rendering, fingerprint header, topo
    order, resolved `{{...}}` args materialized, shell quoting, on_fail /
    requires_decision flags, idempotency guard.
  - CLI `export pipeline-sh --pipeline <id|path>` writes the rendered script
    (default next to the spec in `.harness-console/pipelines/`, or `-o`).
  - Bash execution parity: when `bash` is available, running the rendered
    script reproduces the executor's output files in the same order; repeat
    runs are idempotent; requires_decision halts with exit 1 until a decision
    file exists.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scholar_harness.cli import app
from scholar_harness.integrations.pipeline_script import render_pipeline_sh
from scholar_harness.pipeline_executor import load_spec

runner = CliRunner()


def _bash_available() -> bool:
    """True only if a *functional* bash exists (WindowsApps WSL stub fails here)."""
    exe = shutil.which("bash")
    if not exe:
        return False
    try:
        return subprocess.run(["bash", "-c", "true"], capture_output=True, check=False).returncode == 0
    except OSError:
        return False


BASH = pytest.mark.skipif(not _bash_available(), reason="functional bash not available")

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
CODE_BATCH = (
    "import pathlib,argparse,sys;"
    "p=argparse.ArgumentParser();p.add_argument('--out');"
    "a=p.parse_args(sys.argv[1:]);"
    "p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);"
    "p.write_text('{}')"
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


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def test_render_is_deterministic_and_has_header(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = load_spec(_write_spec(tmp_path, _spec_dict()))
    a = render_pipeline_sh(spec, ws)
    b = render_pipeline_sh(spec, ws)
    assert a == b
    assert a.startswith("#!/usr/bin/env bash")
    assert "fingerprint: sha256:" in a
    assert "test_pipeline" in a
    assert "executes equivalently" in a.lower() or "uv run scholar-harness run --pipeline" in a


def test_render_topo_order_and_resolved_args(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = load_spec(_write_spec(tmp_path, _spec_dict()))
    script = render_pipeline_sh(spec, ws)
    assert script.index("run_node 'n1'") < script.index("run_node 'n2'")
    # args materialized: --out / --content values, node-output + settings refs
    assert "'literature/n1.json'" in script
    assert "boom" in script
    # every node command is rendered shell-quoted under `uv run`
    assert "'uv' 'run' 'python' '-c'" in script


def test_render_shell_quoting(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = _spec_dict()
    spec["nodes"] = [
        {
            "id": "n1", "kit": "test", "command": ["python", "-c", CODE_WRITE],
            "args": {"msg": "spaced value with don't"},
            "inputs": [], "outputs": [], "on_fail": "abort",
        },
        {
            "id": "n2", "kit": "test", "command": ["python", "-c", CODE_WRITE],
            "args": {"msg": "plain"},
            "inputs": [], "outputs": [], "on_fail": "abort",
        },
    ]
    spec["edges"] = []
    loaded = load_spec(_write_spec(tmp_path, spec))
    script = render_pipeline_sh(loaded, ws)
    assert "'spaced value with don'\\''t'" in script


def test_render_applies_semantics_flags(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = _spec_dict()
    spec["nodes"].append({
        "id": "screen", "kit": "test", "command": ["python", "-c", CODE_BATCH],
        "args": {"out": "literature/screening/batch_001.json"},
        "inputs": [], "outputs": ["literature/screening/batch_*.json"],
        "on_fail": "abort", "requires_decision": True,
    })
    spec["nodes"].append({
        "id": "bad", "kit": "test", "command": ["python", "-c", CODE_FAIL],
        "args": {}, "inputs": [], "outputs": [], "on_fail": "skip",
    })
    spec["edges"] = [["n1", "n2"], ["n2", "screen"], ["screen", "bad"]]
    script = render_pipeline_sh(load_spec(_write_spec(tmp_path, spec)), ws)
    assert "run_node 'screen' 'abort' 'true'" in script
    assert "run_node 'bad' 'skip' 'false'" in script
    assert "outputs already present, idempotent" in script
    assert "decisions are required" in script
    assert "aborting pipeline" in script


def test_render_cycle_rejected(tmp_path):
    from scholar_harness.console.api.pipelines import PipelineSpec

    spec = _spec_dict()
    spec["edges"] = [["n1", "n2"], ["n2", "n1"]]
    with pytest.raises(ValueError, match="cycle"):
        render_pipeline_sh(PipelineSpec.model_validate(spec), tmp_path / "ws")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_export_pipeline_sh_by_path(tmp_path):
    ws = _bootstrap(tmp_path)
    spec_file = _write_spec(tmp_path, _spec_dict())
    result = runner.invoke(
        app,
        ["export", "pipeline-sh", "--pipeline", str(spec_file), "--workspace", str(ws)],
    )
    assert result.exit_code == 0, result.output
    out = ws / ".harness-console" / "pipelines" / "test_pipeline.sh"
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")


def test_cli_export_pipeline_sh_by_id_and_output(tmp_path):
    ws = _bootstrap(tmp_path)
    store = ws / ".harness-console" / "pipelines"
    store.mkdir(parents=True)
    (store / "test_pipeline.json").write_text(
        json.dumps(_spec_dict(), indent=2), encoding="utf-8")
    out = tmp_path / "custom.sh"
    result = runner.invoke(
        app,
        ["export", "pipeline-sh", "--pipeline", "test_pipeline",
         "--workspace", str(ws), "--output", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "run_node 'n2'" in out.read_text(encoding="utf-8")


def test_cli_export_pipeline_sh_errors(tmp_path):
    ws = _bootstrap(tmp_path)
    r = runner.invoke(app, ["export", "pipeline-sh", "--workspace", str(ws)])
    assert r.exit_code == 1 and "--pipeline" in r.output
    r2 = runner.invoke(app, ["export", "pipeline-sh", "--pipeline", "nope", "--workspace", str(ws)])
    assert r2.exit_code == 1 and "not found" in r2.output


# ---------------------------------------------------------------------------
# bash execution parity (POSIX CI / git-bash; skipped when bash absent)
# ---------------------------------------------------------------------------

@BASH
def test_bash_run_executes_equivalently(tmp_path):
    ws = _bootstrap(tmp_path)
    spec = load_spec(_write_spec(tmp_path, _spec_dict()))
    sh = tmp_path / "run.sh"
    sh.write_text(render_pipeline_sh(spec, ws), encoding="utf-8")

    proc = subprocess.run(["bash", str(sh)], cwd=str(tmp_path), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (ws / "literature" / "n1.json").read_text() == "n1"
    assert (ws / "literature" / "n2.json").read_text() == "n2"

    repeat = subprocess.run(["bash", str(sh)], cwd=str(tmp_path), capture_output=True, text=True, check=False)
    assert "outputs already present" in repeat.stdout


@BASH
def test_bash_run_requires_decision_halt(tmp_path):
    ws = _bootstrap(tmp_path)
    (ws / "literature" / "screening").mkdir()
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
    sh = tmp_path / "run.sh"
    sh.write_text(render_pipeline_sh(load_spec(_write_spec(tmp_path, spec)), ws), encoding="utf-8")

    proc = subprocess.run(["bash", str(sh)], cwd=str(tmp_path), capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    assert "decisions are required" in proc.stdout
    assert (ws / "literature" / "screening" / "batch_001.json").exists()

    dummy = {"batch": 1, "decisions": [{"workspace_id": "X", "decision": "INCLUDE"}]}
    (ws / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(dummy), encoding="utf-8")
    again = subprocess.run(["bash", str(sh)], cwd=str(tmp_path), capture_output=True, text=True, check=False)
    assert again.returncode == 0, again.stdout + again.stderr


@BASH
def test_bash_run_on_fail_abort_stops(tmp_path):
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
    sh = tmp_path / "run.sh"
    sh.write_text(render_pipeline_sh(load_spec(_write_spec(tmp_path, spec)), ws), encoding="utf-8")

    proc = subprocess.run(["bash", str(sh)], cwd=str(tmp_path), capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    assert "aborting pipeline" in proc.stdout
    assert not (ws / "literature" / "n3.json").exists()

