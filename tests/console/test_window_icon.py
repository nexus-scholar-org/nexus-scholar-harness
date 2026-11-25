"""H-b8-small-faults: the approval-code window and the folder dialog show the app's icon too.

Both run as a child process: `python -I <their file>` from a Python install (no
package, standard library only), or the bundled app with a flag (in the
package). The icon comes from `console/window_icon.py` either way, and a
missing helper, a missing file or a refusing Tk never stops the window.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scholar_harness.console import (
    code_window,
    control_window,
    folder_dialog,
    window_icon,
)

CHILDREN = [code_window, folder_dialog]


class IconRoot:
    """Stands in for a Tk root: records the icon it was given, or refuses it as Tk does off Windows."""

    def __init__(self, error: BaseException | None = None):
        self.error = error
        self.icons: list[str] = []

    def iconbitmap(self, default: str) -> None:
        if self.error is not None:
            raise self.error
        self.icons.append(default)


@pytest.mark.parametrize("module", CHILDREN, ids=["approval-code-window", "folder-dialog"])
def test_the_child_window_gets_the_app_icon_in_the_bundle(module):
    root = IconRoot()
    assert module.__package__  # imported: the bundle's path (`--approval-window`, `--choose-folder`)
    assert module._app_icon(root) is True
    assert root.icons == [str(window_icon.ICON)]


@pytest.mark.parametrize("module", CHILDREN, ids=["approval-code-window", "folder-dialog"])
def test_the_child_window_gets_the_app_icon_as_a_script(module, monkeypatch):
    monkeypatch.setattr(module, "__package__", None)  # `python -I <file>`: the helper is loaded from beside it
    root = IconRoot()
    assert module._app_icon(root) is True
    assert root.icons == [str(window_icon.ICON)]


@pytest.mark.parametrize("module", CHILDREN, ids=["approval-code-window", "folder-dialog"])
@pytest.mark.parametrize("script", [False, True], ids=["bundle", "script"])
def test_a_refused_icon_or_a_missing_helper_never_stops_the_child_window(module, script, monkeypatch, tmp_path):
    if script:
        monkeypatch.setattr(module, "__package__", None)
    assert module._app_icon(IconRoot(RuntimeError('bitmap "x.ico" not defined'))) is False
    if script:
        monkeypatch.setattr(module, "__file__", str(tmp_path / "moved.py"))  # no window_icon.py beside it
        assert module._app_icon(IconRoot()) is False


def test_the_helper_a_script_loads_imports_the_standard_library_only():
    """The children start in isolated mode in well under a second: loading the helper pulls in no package."""
    helper = Path(window_icon.__file__).resolve()
    probe = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('_nexus_window_icon', {str(helper)!r})\n"
        "module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n"
        "print(module.ICON.is_file(), any(name.startswith('scholar_') for name in sys.modules))\n"
    )
    out = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, check=True, timeout=60)
    assert out.stdout.split() == ["True", "False"]


def test_the_control_window_uses_the_same_helper():
    assert control_window.set_icon is window_icon.set_icon and control_window.ICON == window_icon.ICON


@pytest.mark.parametrize("module", CHILDREN, ids=["approval-code-window", "folder-dialog"])
def test_real_tk_takes_the_icon_in_each_child_window(module):
    root = control_window.make_root()
    if root is None:
        pytest.skip("no Tk or no display here")
    try:
        root.withdraw()
        accepted = module._app_icon(root)
        if sys.platform == "win32":
            assert accepted is True  # Tk on Windows takes the real .ico
    finally:
        root.destroy()



@pytest.mark.parametrize(
    "module", [*CHILDREN, window_icon], ids=["approval-code-window", "folder-dialog", "icon-helper"]
)
def test_the_child_window_files_still_import_the_standard_library_only(module):
    """The children run alone (`python -I <file>`), and so does the helper they load: no import of a package."""
    import ast

    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    names |= {"." for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level}
    assert names <= set(sys.stdlib_module_names) | {"__future__"}, names
