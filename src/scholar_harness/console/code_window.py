"""Show approval codes in a window on this computer's desktop (finding 38).

When `nexus-scholar ui` was started for the researcher, the terminal that
prints the approval codes may be hidden. This window is the same kind of
surface as that terminal: it is opened by the engine, on this computer's
desktop, and nothing in it travels over HTTP. What a code proves does not
change: someone at this computer saw it (decision 2026-11-04, UI-07 §2).

Rules kept here:

* the window runs in its own child process (`python -I <this file>`), never in
  the engine's process: Tk must own the main thread on macOS (a first load
  elsewhere aborts the whole process), and a Tk crash on any platform must not
  take the engine down. This file imports the standard library only, and the
  child runs it in isolated mode, so it starts in well under a second instead
  of loading the whole console package. Inside a frozen bundle (the installed
  app, M13 Part A) ``sys.executable`` is the app, not Python, and ``-I`` is
  not an option it knows (trial build fault 3): there the child is the app
  itself started with :data:`CHILD_FLAG`, which the app's entry points
  (``console/desktop.py`` and ``cli.main``) hand to :func:`run_child` before
  anything else loads;
* the codes reach the child on its standard input, never on its command line
  (other programs can read command lines), and are never in the window title;
* the window names the batches and tells the researcher to close it if they
  did not just ask for codes on the Publish screen (another program holding
  the console token could ask for codes too);
* it closes itself when the codes expire;
* it is best-effort: with no display or no Tk the child says so and the codes
  stay on the terminal only (`code_shown_on: "terminal"`).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

#: Set to "0" to keep the codes on the terminal only.
WINDOW_ENV = "NEXUS_APPROVAL_WINDOW"

TITLE = "Nexus Scholar: approval"
#: The flag that makes a frozen app run as this window (never a user-facing option).
CHILD_FLAG = "--approval-window"
READY, UNAVAILABLE = "ready", "unavailable"
_START_TIMEOUT_S = 5.0


def enabled() -> bool:
    return os.environ.get(WINDOW_ENV, "1").strip() not in ("0", "false", "no", "off")


def _batch_list(batches: list[int]) -> str:
    shown = ", ".join(str(b) for b in batches[:12])
    return shown + (f" and {len(batches) - 12} more" if len(batches) > 12 else "")


def message(batches: list[int], expires_at: str) -> str:
    """The words above the codes (no code in them)."""
    try:
        until = datetime.fromisoformat(expires_at).astimezone().strftime("%H:%M")
    except ValueError:
        until = expires_at
    what = f"batch {batches[0]}" if len(batches) == 1 else f"batches {_batch_list(batches)}"
    return (
        f"Approval codes for {what}. If you did not just ask for codes on the Publish "
        f"screen, close this window and copy nothing. Otherwise copy the block below into "
        f"the Publish screen: each line approves one batch, once. The codes expire at "
        f"{until}; this window closes then."
    )


def _seconds_left(expires_at: str) -> float:
    try:
        moment = datetime.fromisoformat(expires_at)
    except ValueError:
        return 300.0
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return max(1.0, (moment - datetime.now(timezone.utc)).total_seconds())


def _show(payload: dict[str, Any]) -> None:
    """The child: build the window on its own main thread, then say ready."""
    try:
        import tkinter as tk

        root = tk.Tk()
    except Exception:  # noqa: BLE001 - no Tk or no display: terminal only
        print(UNAVAILABLE, flush=True)
        return
    codes, batches, expires_at = payload["codes"], payload["batches"], payload["expires_at"]
    root.title(TITLE)
    root.attributes("-topmost", True)
    tk.Label(root, text=message(batches, expires_at), wraplength=480, justify="left").pack(
        padx=16, pady=(16, 8), anchor="w"
    )
    text = tk.Text(root, width=40, height=min(12, codes.count("\n") + 1), font=("Courier", 11))
    text.insert("1.0", codes)
    text.configure(state="disabled")
    text.pack(padx=16, pady=4, fill="both", expand=True)

    def copy() -> None:
        root.clipboard_clear()
        root.clipboard_append(codes)
        root.update()

    buttons = tk.Frame(root)
    buttons.pack(padx=16, pady=(8, 16), anchor="e")
    tk.Button(buttons, text="Copy the codes", command=copy).pack(side="left", padx=4)
    tk.Button(buttons, text="Close", command=root.destroy).pack(side="left", padx=4)
    root.after(int(_seconds_left(expires_at) * 1000), root.destroy)
    root.lift()
    root.focus_force()
    print(READY, flush=True)
    root.mainloop()


def _command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, CHILD_FLAG]
    # Isolated mode: no user site, no PYTHON* variables, no script folder on the path.
    return [sys.executable, "-I", str(Path(__file__).resolve())]


def run_child() -> int:
    """The child's work when started with :data:`CHILD_FLAG`: the payload is on standard input."""
    if sys.stdin is None:
        return 1
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        return 1
    _show(payload)
    return 0


def reveal(*, codes: str, batches: list[int], expires_at: str) -> bool:
    """Open the window in a child process; ``True`` once it says it is on the desktop."""
    if not enabled():
        return False
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    try:
        child = subprocess.Popen(  # noqa: S603 - our own interpreter and module
            _command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            creationflags=flags,
        )
    except OSError:
        return False
    try:
        assert child.stdin is not None and child.stdout is not None
        child.stdin.write(json.dumps({"codes": codes, "batches": batches, "expires_at": expires_at}))
        child.stdin.close()
        line = _first_line(child, _START_TIMEOUT_S)
    except (OSError, ValueError):
        line = ""
    if line != READY:
        if child.poll() is None:
            child.kill()
        return False
    return True


def _first_line(child: subprocess.Popen, timeout: float) -> str:
    """The child's first line, or "" when it says nothing in time."""
    import threading

    out: list[str] = []
    reader = threading.Thread(target=lambda: out.append(child.stdout.readline().strip()), daemon=True)
    reader.start()
    reader.join(timeout)
    return out[0] if out else ""


if __name__ == "__main__":
    sys.exit(run_child())
