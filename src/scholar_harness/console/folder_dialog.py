"""The system's folder dialog, opened by the engine on this computer's desktop (M13 Part B).

A browser cannot read a folder path from the computer, so **Change…** on the
Settings screen asks the engine, which opens the system's own folder dialog
(specification §4.3). Same rules as the approval-code window
(``console/code_window.py``): the dialog runs in its own child process, never
in the engine's (Tk must own the main thread on macOS, and a Tk crash must not
take the engine down); it imports the standard library only; frozen, the
child is the app itself started with :data:`CHILD_FLAG`.

The child prints one JSON line: ``{"chosen": "<path>"}``, ``{"chosen": null}``
when the user cancelled, or ``{"unavailable": true}`` with no Tk or display.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CHILD_FLAG = "--choose-folder"
TITLE = "Nexus Scholar: where your reviews are kept"
#: The dialog waits for the user; past this the request gives up and the child is ended.
WAIT_SECONDS = 600.0


class FolderDialogUnavailable(RuntimeError):
    """No desktop to show a dialog on (no Tk, no display, or the child failed)."""


def _command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, CHILD_FLAG]
    return [sys.executable, "-I", str(Path(__file__).resolve())]


def run_child() -> int:
    """The child's work: the starting folder on standard input, the answer on standard output."""
    start = sys.stdin.read().strip() if sys.stdin is not None else ""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
    except Exception:  # noqa: BLE001 - no Tk or no display
        print(json.dumps({"unavailable": True}), flush=True)
        return 0
    root.withdraw()
    root.attributes("-topmost", True)
    chosen = filedialog.askdirectory(parent=root, title=TITLE, initialdir=start or None, mustexist=False)
    root.destroy()
    print(json.dumps({"chosen": chosen or None}), flush=True)
    return 0


def choose(start: Path | None) -> Path | None:
    """Open the dialog and wait; the folder chosen, or ``None`` when the user cancelled."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        child = subprocess.run(  # noqa: S603 - our own interpreter and module
            _command(),
            input=str(start) if start is not None else "",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=WAIT_SECONDS,
            creationflags=flags,
            env={**os.environ},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FolderDialogUnavailable(str(exc)) from exc
    try:
        answer = json.loads((child.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise FolderDialogUnavailable("the folder dialog gave no answer") from exc
    if answer.get("unavailable"):
        raise FolderDialogUnavailable("no desktop to show the folder dialog on")
    chosen = answer.get("chosen")
    return Path(chosen) if chosen else None


if __name__ == "__main__":
    sys.exit(run_child())
