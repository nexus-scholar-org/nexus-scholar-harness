"""The live-gate sandbox never deletes what it did not create (M1b-1 review 5)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("golden_screening_sandbox", ROOT / "scripts" / "golden_screening_sandbox.py")
sandbox = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = sandbox
_SPEC.loader.exec_module(sandbox)


@pytest.mark.parametrize("dest", [ROOT, ROOT.parent, ROOT / "workspaces", ROOT / "workspaces" / "x"])
def test_refuses_the_repository_its_ancestors_and_workspaces(dest):
    with pytest.raises(SystemExit, match="refusing"):
        sandbox.check_dest(dest)


def test_refuses_a_non_empty_directory_it_did_not_create(tmp_path):
    keep = tmp_path / "notes.txt"
    keep.write_text("mine", encoding="utf-8")
    with pytest.raises(SystemExit, match="did not create"):
        sandbox.build(tmp_path, batch_size=10)
    assert keep.read_text(encoding="utf-8") == "mine"


def test_rebuilds_a_sandbox_it_created(tmp_path):
    dest = tmp_path / "sandbox"
    sandbox.build(dest, batch_size=10)
    assert (dest / sandbox.MARKER).is_file()
    (dest / "stray.txt").write_text("x", encoding="utf-8")
    sandbox.build(dest, batch_size=10)
    assert not (dest / "stray.txt").exists()
    assert (dest / "literature" / "screening" / "batch_001.json").is_file()
