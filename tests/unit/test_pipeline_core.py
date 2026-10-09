"""Neutral pipeline-core ownership + behavior-parity tests (HCM-03).

Proves the refactor moved reusable pipeline specifications, validation,
and execution coordination from the console transport into
``scholar_harness.pipeline`` with zero behavior change:

- the core owns models/validation/toposort/fingerprint; the console module
  is a thin re-export shim plus transport-owned store/templates/endpoints;
- executor, script exporter, and job runner consume the core (import guard);
- validate/fingerprint/toposort outputs match base golden vectors;
- invalid specs (unresolved template, cycle, collision, unknown edge,
  empty command) stay typed errors and publish nothing.

Hermetic: no network, no kit CLIs, ``tmp_path`` only.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import scholar_harness.console.api.pipelines as shim
import scholar_harness.pipeline as core

GOLDEN_SPEC = {
    "schema_version": "0.1.0",
    "id": "my_review",
    "archetype": "PRISMA_SLR",
    "name": "My Review",
    "workspace_slug": "my-review",
    "settings": {"queries": {"q1": "UAV weeds"}},
    "nodes": [
        {
            "id": "n1",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "run"],
            "args": {"query": "{{queries.q1}}"},
            "outputs": ["literature/candidates.json"],
        },
        {
            "id": "n2",
            "kit": "scholar-search-kit",
            "command": ["scholar-search", "dedup"],
            "args": {"input": "literature/candidates.json"},
            "inputs": ["literature/candidates.json"],
            "outputs": ["literature/corpus.json"],
        },
    ],
    "edges": [["n1", "n2"]],
    "created_by": "test",
}

# Recorded from base behavior (HEAD console.api.pipelines) before the move.
GOLDEN_FINGERPRINT = (
    "sha256:d2692b9b33fabd2586d27cb734751358512d14138060c7cb5da9427dafafc5ac"
)
GOLDEN_ORDER = ["n1", "n2"]

REEXPORTED = [
    "SCHEMA_VERSION",
    "PipelineNode",
    "PipelineSpec",
    "_TEMPLATE_RE",
    "_extract_template_keys",
    "_fingerprint",
    "_lookup",
    "_output_collisions",
    "_toposort",
    "validate_spec",
]


def test_console_shim_reexports_core_objects():
    """Existing `console.api.pipelines` seams resolve to the core objects."""
    for name in REEXPORTED:
        assert getattr(shim, name) is getattr(core, name), name
    assert set(shim.__all__) >= set(REEXPORTED)


_IMPORT_LINE_RE = re.compile(r"^\s*(from|import)\s+(\S+)", re.MULTILINE)
_FORBIDDEN_IMPORT_RE = re.compile(
    r"(from|import)\s+[\w.]*console\.api\.pipelines|console/api/pipelines"
)


def _import_lines(path: Path) -> list[str]:
    """Logical import lines of a module (joins backslash/paren continuations)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out, buf, depth = [], "", 0
    for line in lines:
        stripped = line.strip()
        if not buf and not stripped.startswith(("from ", "import ")):
            continue
        buf += line + "\n"
        depth += line.count("(") - line.count(")")
        if line.rstrip().endswith("\\"):
            continue
        if depth <= 0:
            out.append(buf)
            buf, depth = "", 0
    if buf:
        out.append(buf)
    return out


def _harness_src() -> Path:
    root = Path(__file__).resolve().parents[2] / "src" / "scholar_harness"
    assert root.is_dir(), root
    return root


def test_no_console_pipeline_import_outside_console():
    """Only `console/` may import the console transport shim (HCM3-01)."""
    src = _harness_src()
    violators = []
    for path in sorted(src.rglob("*.py")):
        if "console" in path.relative_to(src).parts:
            continue
        for stmt in _import_lines(path):
            if _FORBIDDEN_IMPORT_RE.search(stmt):
                violators.append(f"{path.relative_to(src)}: {stmt.strip()}")
    assert violators == []

    # The guard itself is non-vacuous: it flags a restored forbidden import.
    assert _FORBIDDEN_IMPORT_RE.search(
        "from ..console.api.pipelines import PipelineSpec"
    )
    assert _FORBIDDEN_IMPORT_RE.search(
        "from scholar_harness.console.api.pipelines import validate_spec"
    )
    assert not _FORBIDDEN_IMPORT_RE.search("from ...pipeline import PipelineSpec")


def test_core_imports_stay_neutral():
    """Core stays kit/transport-free; stages call kits, never transport.

    HCM-04b repair per roadmap §3.3 (higher authority than the HCM-03 pin):
    the neutral core {__init__, models, validation, fingerprint} still
    imports stdlib/pydantic only — no kits, no transport (verbatim HCM-03
    strength) — while roadmap-mandated stage modules (discovery.py and any
    future pipeline/<stage>.py) may call kit APIs (scholar_*) plus core /
    stdlib / pydantic but must import no console transport.
    """
    src = _harness_src()
    core_dir = src / "pipeline"
    CORE_NEUTRAL = [
        "__init__.py",
        "fingerprint.py",
        "models.py",
        "validation.py",
    ]
    names = sorted(p.name for p in core_dir.glob("*.py"))
    # (pin) Core enumeration preserved: all four neutral files are present;
    # extra pipeline/<stage>.py files fall under the stage (b) rule below.
    assert sorted(n for n in names if n in set(CORE_NEUTRAL)) == CORE_NEUTRAL
    stage_names = sorted(n for n in names if n not in set(CORE_NEUTRAL))
    assert "discovery.py" in stage_names

    def _core_violation(stmt: str) -> bool:
        low = stmt.lower()
        return (
            "console" in low
            or "fastapi" in low
            or "scholar_" in low
            or "uvicorn" in low
        )

    def _stage_violation(stmt: str) -> bool:
        low = stmt.lower()
        return "console" in low or "fastapi" in low or "uvicorn" in low

    def _has_kit_import(stmts: list[str]) -> bool:
        return any(
            "scholar_" in s.lower() and "scholar_harness" not in s.lower()
            for s in stmts
        )

    bad: list[str] = []
    for path in sorted(core_dir.glob("*.py")):
        if path.name not in set(CORE_NEUTRAL):
            continue
        for stmt in _import_lines(path):
            if _core_violation(stmt):
                bad.append(f"{path.name}: {stmt.strip()}")
    assert bad == []

    stage_bad: list[str] = []
    for path in sorted(core_dir.glob("*.py")):
        if path.name in set(CORE_NEUTRAL):
            continue
        stmts = _import_lines(path)
        for stmt in stmts:
            if _stage_violation(stmt):
                stage_bad.append(f"{path.name}: {stmt.strip()}")
        if not _has_kit_import(stmts):
            stage_bad.append(f"{path.name}: missing required scholar_* kit import")
    assert stage_bad == []

    # Non-vacuity self-proof: both halves flag synthetic violations.
    assert _core_violation("from scholar_search.engine import SearchEngine")
    assert not _core_violation("from pydantic import BaseModel")
    assert _stage_violation(
        "from scholar_harness.console.api.pipelines import PipelineSpec"
    )
    assert _stage_violation("import fastapi")
    assert not _stage_violation("from scholar_search.engine import SearchEngine")
    assert _has_kit_import(["from scholar_search.engine import SearchEngine"])
    assert not _has_kit_import(["import scholar_harness.orchestrator"])


def test_golden_validate_fingerprint_toposort():
    """Core outputs match the base golden vectors (HCM3-02)."""
    spec = core.PipelineSpec.model_validate(GOLDEN_SPEC)
    assert core.validate_spec(spec) == {
        "errors": [],
        "warnings": [],
        "order": GOLDEN_ORDER,
    }
    assert core._fingerprint(spec) == GOLDEN_FINGERPRINT
    assert core._toposort({"n1", "n2"}, [["n1", "n2"]]) == (GOLDEN_ORDER, [])
    # Shim path agrees (same objects, same outputs).
    assert shim.validate_spec(spec) == core.validate_spec(spec)
    assert shim._fingerprint(spec) == GOLDEN_FINGERPRINT
    # Fingerprint ignores a stale `fingerprint` value (stable across save+read).
    stamped = core.PipelineSpec.model_validate(
        {**GOLDEN_SPEC, "fingerprint": "sha256:stale"}
    )
    assert core._fingerprint(stamped) == GOLDEN_FINGERPRINT


def test_template_regex_stable():
    assert core._TEMPLATE_RE.pattern == shim._TEMPLATE_RE.pattern
    found = core._TEMPLATE_RE.findall(
        "{{queries.q1}} and {{n1_disc.literature/candidates.json}}"
    )
    assert found == ["queries.q1", "n1_disc.literature/candidates.json"]


def test_model_semantics_unchanged():
    """No new node types, fields, or semantics (HCM3-06)."""
    assert set(core.PipelineSpec.model_fields) == {
        "schema_version",
        "id",
        "archetype",
        "name",
        "workspace_slug",
        "settings",
        "nodes",
        "edges",
        "dry_run",
        "created_by",
        "fingerprint",
    }
    assert set(core.PipelineNode.model_fields) == {
        "id",
        "kit",
        "command",
        "args",
        "inputs",
        "outputs",
        "on_fail",
        "requires_decision",
    }
    assert core.SCHEMA_VERSION == "0.1.0"
    node = core.PipelineNode(id="n", kit="k", command=["c"])
    assert node.on_fail == "abort" and node.requires_decision is False
    with pytest.raises(Exception, match="unsupported schema_version"):
        core.PipelineSpec.model_validate({**GOLDEN_SPEC, "schema_version": "9.9.9"})
    with pytest.raises(Exception, match="edges must be"):
        core.PipelineSpec.model_validate({**GOLDEN_SPEC, "edges": [["only-one"]]})


def _spec_with(**overrides):
    import copy

    spec = copy.deepcopy(GOLDEN_SPEC)
    spec.update(overrides)
    return core.PipelineSpec.model_validate(spec)


def test_negative_unresolved_template():
    spec = _spec_with(
        nodes=[
            {**GOLDEN_SPEC["nodes"][0], "args": {"query": "{{missing_setting}}"}},
            GOLDEN_SPEC["nodes"][1],
        ]
    )
    errors = core.validate_spec(spec)["errors"]
    assert any(
        "unresolved template keys" in e and "missing_setting" in e for e in errors
    )


def test_negative_cycle():
    spec = _spec_with(edges=[["n1", "n2"], ["n2", "n1"]])
    result = core.validate_spec(spec)
    assert result["order"] == []
    assert any("cycle" in e for e in result["errors"])
    _, cycle_errors = core._toposort({"n1", "n2"}, [["n1", "n2"], ["n2", "n1"]])
    assert any("cycle" in e for e in cycle_errors)


def test_negative_output_collision():
    spec = _spec_with(
        nodes=[
            GOLDEN_SPEC["nodes"][0],
            {**GOLDEN_SPEC["nodes"][1], "outputs": ["literature/candidates.json"]},
        ]
    )
    errors = core.validate_spec(spec)["errors"]
    assert any("collision" in e for e in errors)
    collisions = core._output_collisions(spec)
    assert len(collisions) == 1 and "literature/candidates.json" in collisions[0]


def test_negative_unknown_edge_and_empty():
    spec = _spec_with(edges=[["n1", "nope"]])
    assert any("unknown target" in e for e in core.validate_spec(spec)["errors"])
    spec = _spec_with(nodes=[], edges=[])
    assert any("at least one node" in e for e in core.validate_spec(spec)["errors"])
    spec = _spec_with(nodes=[{**GOLDEN_SPEC["nodes"][0], "command": []}])
    assert any("must not be empty" in e for e in core.validate_spec(spec)["errors"])


def test_validation_writes_nothing(tmp_path, monkeypatch):
    """Validation is pure: no canonical (or any) files are created (HCM3-04)."""
    monkeypatch.chdir(tmp_path)
    spec = core.PipelineSpec.model_validate(GOLDEN_SPEC)
    assert core.validate_spec(spec)["errors"] == []
    assert list(tmp_path.iterdir()) == []


def test_save_read_fingerprint_stable(tmp_path):
    """Store round-trip preserves the golden fingerprint (HCM3-05)."""
    spec = shim.PipelineSpec.model_validate(GOLDEN_SPEC)
    saved = shim._write_spec(tmp_path, spec)
    assert saved.fingerprint == GOLDEN_FINGERPRINT
    assert (tmp_path / ".harness-console" / "pipelines" / "my_review.json").is_file()
    reloaded = shim._load_spec(tmp_path, "my_review")
    assert reloaded.fingerprint == GOLDEN_FINGERPRINT
    assert core._fingerprint(reloaded) == GOLDEN_FINGERPRINT


# ---------------------------------------------------------------------------
# HCM-04a — typed refusal for edges referencing unknown nodes (Option B)
# ---------------------------------------------------------------------------
# Human-authorized behavior decision (prerequisite to HCM-04 stage
# extraction): a pipeline graph whose edges reference unknown nodes used to
# raise an accidental ``KeyError`` out of ``_toposort`` (surfacing as a 500
# at the console endpoint), even though ``validate_spec`` already records
# typed unknown-endpoint errors — the crash fired first. ``_toposort`` now
# skips unknown-endpoint edges (already reported by ``validate_spec``) and
# runs cycle detection on the known subgraph, so every such spec is a typed
# validation refusal (422 at the endpoint, ``PipelineError`` in the
# executor) instead of a crash. Valid specs take byte-identical code paths.


def test_hcm04a_dangling_edges_return_typed_errors_without_raising():
    """HCM-04a: nodes=[] + edges=[[n1,n2]] is typed errors, never KeyError."""
    spec = core.PipelineSpec.model_validate(
        {
            "schema_version": "0.1.0",
            "id": "dangling",
            "archetype": "PRISMA_SLR",
            "name": "Dangling",
            "workspace_slug": "ws",
            "settings": {},
            "nodes": [],
            "edges": [["n1", "n2"]],
            "created_by": "test",
        }
    )
    result = core.validate_spec(spec)  # must not raise KeyError
    assert any("at least one node" in e for e in result["errors"])
    assert any("unknown source" in e for e in result["errors"])
    assert any("unknown target" in e for e in result["errors"])


def test_hcm04a_unknown_endpoints_plus_cycle_reports_both_classes():
    """HCM-04a: unknown endpoints do not mask a real cycle on known nodes."""
    spec = _spec_with(edges=[["n1", "n2"], ["n2", "n1"], ["n1", "ghost"]])
    result = core.validate_spec(spec)  # must not raise KeyError
    assert any("unknown target" in e and "ghost" in e for e in result["errors"])
    assert any("cycle" in e for e in result["errors"])
    assert result["order"] == []


def test_hcm04a_toposort_with_unknown_endpoints_does_not_raise():
    """HCM-04a: ``_toposort`` skips unknown-endpoint edges on the known subgraph."""
    order, errors = core._toposort(set(), [["n1", "n2"]])
    assert (order, errors) == ([], [])
    order, errors = core._toposort({"n1", "n2"}, [["n1", "ghost"]])
    assert sorted(order) == ["n1", "n2"] and errors == []
    _, cycle_errors = core._toposort(
        {"n1", "n2"}, [["n1", "n2"], ["n2", "n1"], ["n1", "ghost"]]
    )
    assert any("cycle" in e for e in cycle_errors)


def test_hcm04a_endpoint_post_unknown_endpoints_returns_422(tmp_path):
    """HCM-04a: POST with unknown-endpoint edges is 422 (not 500)."""
    import copy

    from fastapi.testclient import TestClient

    from scholar_harness.console import create_app

    ws = tmp_path / "ws"
    ws.mkdir()
    client = TestClient(create_app(ws))
    bad = copy.deepcopy(GOLDEN_SPEC)
    bad["edges"] = [["n1", "ghost"]]
    r = client.post("/api/v1/pipelines", json={"spec": bad})
    assert r.status_code == 422, r.text
    assert "unknown target" in r.text
    # Rejected specs persist nothing.
    assert not (ws / ".harness-console" / "pipelines" / "my_review.json").exists()


def test_hcm04a_executor_refuses_unknown_endpoint_spec_without_running(tmp_path):
    """HCM-04a: the executor refuses unknown-endpoint specs before anything runs."""
    import copy
    import json
    import subprocess

    from scholar_harness.pipeline_executor import PipelineError, execute_file

    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    bad = copy.deepcopy(GOLDEN_SPEC)
    bad["edges"] = [["n1", "ghost"]]
    spec_file = tmp_path / "pipeline.json"
    spec_file.write_text(json.dumps(bad, indent=2), encoding="utf-8")

    calls: list[list[str]] = []

    def _forbid(*args: object, **kwargs: object):
        calls.append([str(a) for a in args])
        raise AssertionError("subprocess must not run for an invalid spec")

    import unittest.mock as mock

    with mock.patch.object(subprocess, "run", _forbid):
        with pytest.raises(PipelineError, match="unknown target"):
            execute_file(spec_file, ws)
    assert calls == []
    assert list((ws / "literature").iterdir()) == []
