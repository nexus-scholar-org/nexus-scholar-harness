"""Workspace templates: build each kind of test workspace once per process, copy it per test.

H-faster-python-tests (test-suite review 2026-11-23, step 3.2). Building a
prepared or published screening workspace (scaffold, accept a corpus, prepare
batches, decide, approve, publish) costs about half a second, and most console
tests built one from nothing. A template is built the first time a test of
this process (one pytest-xdist worker) asks for that kind, under a private
temporary root, and every test then gets a copy of it under its own
``tmp_path``. The test owns its copy; the template is never handed out.

What makes a copy equivalent to a fresh build:

* the builders use fixed identities, fingerprints and dates, except for the
  "now" stamps written when the template was built (still earlier than
  anything the test does) and random ids (``uuid4`` event ids, and the
  generation ids and file names that follow from them): every copy made in one
  process shares those, where fresh builds would differ. No test relies on two
  workspaces having different ids (the read store and the preview cache are
  keyed by absolute path);
* the template holds no absolute path to where it was built: this is checked
  when it is built, and a builder that writes one fails loudly here instead of
  handing a test paths into another folder;
* the copy keeps file contents and modification times (``shutil.copy2``); the
  read store keys its kept results by absolute workspace path, so two copies
  never share one.
"""

from __future__ import annotations

import atexit
import copy
import shutil
import tempfile
from collections.abc import Callable, Hashable
from pathlib import Path
from typing import Any

_root: Path | None = None
_built: dict[Hashable, tuple[Path, Path, Any]] = {}


def _templates_root() -> Path:
    global _root
    if _root is None:
        _root = Path(tempfile.mkdtemp(prefix="nexus-ws-templates-"))
        atexit.register(shutil.rmtree, _root, True)
    return _root


def _refuse_own_path(root: Path) -> None:
    needles = {str(root), root.as_posix(), str(root).replace("\\", "\\\\")}
    for path in root.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            for needle in needles:
                if needle.encode("utf-8") in data:
                    raise AssertionError(
                        f"workspace template {path.relative_to(root)} records the path it was built in "
                        f"({needle}); a copy elsewhere would point back to it, so it cannot be a template"
                    )


def copy_of(
    key: Hashable,
    build: Callable[[Path], tuple[Path, Any]],
    tmp_path: Path,
) -> tuple[Path, Any]:
    """A copy, under ``tmp_path``, of the workspace ``build(root)`` makes.

    ``build`` receives an empty folder and returns ``(workspace, extra)``, the
    workspace being inside that folder. It runs once per process per ``key``;
    each call returns ``(copied workspace, a deep copy of extra)``. Everything
    the builder wrote in its folder is copied, at the same relative paths.
    """
    if key not in _built:
        # A fresh folder per attempt: a builder that failed leaves its folder behind
        # and must not turn every later call into a FileExistsError.
        root = Path(tempfile.mkdtemp(prefix="t", dir=_templates_root()))
        workspace, extra = build(root)
        _refuse_own_path(root)
        _built[key] = (root, Path(workspace), extra)
    root, workspace, extra = _built[key]
    tmp_path.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root, tmp_path, dirs_exist_ok=True)
    return tmp_path / workspace.relative_to(root), copy.deepcopy(extra)
