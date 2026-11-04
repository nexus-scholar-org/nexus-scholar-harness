"""AGT-01: MCP tool path arguments stay inside the MCP workspace.

Each writer tool is given an output path that escapes the workspace, by ``..``
and by an absolute path. The call must be refused before anything is written.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scholar_agent import server


@pytest.fixture
def ws(tmp_path, monkeypatch) -> Path:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(workspace))
    (workspace / "in.json").write_text(json.dumps([]), encoding="utf-8")
    (workspace / "refs.bib").write_text("@article{a, title={A}}\n", encoding="utf-8")
    return workspace


ESCAPES = ["../escape", "ABSOLUTE"]


def _target(ws: Path, escape: str, name: str) -> str:
    if escape == "ABSOLUTE":
        return str(ws.parent / "abs_escape" / name)
    return f"{escape}/{name}"


WRITERS = [
    ("dedup", lambda ws, out: server.nexus_dedup("in.json", out("out.json"))),
    ("graph_build", lambda ws, out: server.nexus_graph_build("in.json", out("g.html"), out("g.json"))),
    ("bib_clean", lambda ws, out: server.nexus_bib_clean("refs.bib", out("clean.bib"))),
    ("screen", lambda ws, out: server.nexus_screen("in.json", "in.json", out("lit"))),
    ("extract_pdf", lambda ws, out: server.nexus_extract_pdf("in.json", out("extracted"))),
]


@pytest.mark.parametrize("escape", ESCAPES)
@pytest.mark.parametrize(("name", "call"), WRITERS, ids=[w[0] for w in WRITERS])
def test_writer_tools_refuse_output_outside_workspace(ws, escape, name, call):
    with pytest.raises(server.PathOutsideWorkspace, match="PATH_OUTSIDE_WORKSPACE"):
        call(ws, lambda leaf: _target(ws, escape, leaf))
    outside = [p for p in ws.parent.rglob("*") if ws not in p.parents and p != ws]
    assert outside == [], f"{name} wrote outside the workspace: {outside}"


def test_reader_tool_refuses_input_outside_workspace(ws):
    secret = ws.parent / "secret.json"
    secret.write_text("{}", encoding="utf-8")
    with pytest.raises(server.PathOutsideWorkspace):
        server.nexus_protocol_render_criteria(str(secret))
    with pytest.raises(server.PathOutsideWorkspace):
        server.nexus_dedup("../secret.json", "out.json")


def test_inside_paths_and_inline_json_still_resolve(ws):
    assert server._resolve_path("sub/x.json") == str((ws / "sub" / "x.json").resolve())
    assert server._resolve_path(str(ws / "x.json")) == str((ws / "x.json").resolve())
    assert server._resolve_path('{"a": 1}') == '{"a": 1}'
    assert server._resolve_path(None) is None
