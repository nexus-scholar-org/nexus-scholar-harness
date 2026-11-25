"""The installed app's control window (M13 Part A, specification §4.2).

The window is the sign that the engine is running and the place to stop it.
It holds one status sentence, **Open in browser**, **Stop Nexus Scholar**,
and the folders a tester is asked about (the log folder and the settings
folder). Closing it asks "Stop Nexus Scholar?" and, when an agent run, a
harvest, an approval or a copy of a review is in progress, says which and
offers **Keep running**.

Two layers:

* :class:`ControlPanel` holds every decision (what the status line says, what
  the closing question names, what each button does) and needs no display,
  so tests drive it directly;
* :class:`ControlWindow` is a thin Tk view of a panel. It runs on the
  process's main thread (Tk must own it on macOS) while the engine runs in a
  background thread, polls the panel once a second, and never blocks on the
  engine.

The window is English only, as the approval-code window is. It is not a
second way into the engine: its buttons call the launcher in this process.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: The title bar's icon (shared with the approval-code window and the folder dialog).
from .window_icon import ICON, set_icon  # noqa: F401 - ICON is read by tests and callers

TITLE = "Nexus Scholar"
POLL_MS = 1000
#: After this long with the first launch link unused, the status line says the browser may be blocked.
BROWSER_HINT_SECONDS = 60.0

STOP_QUESTION = "Stop Nexus Scholar? Open browser tabs will stop working."
BROWSER_BLOCKED = (
    "If your browser did not open Nexus Scholar, click Open in browser. If it still cannot reach it: "
    "a security program or a company proxy may block local addresses; allow 127.0.0.1."
)
FAILED = (
    "Nexus Scholar stopped because of an error. The details are in the log file. "
    "Please send that file to the person who gave you Nexus Scholar."
)


@dataclass(frozen=True)
class Busy:
    """What stopping now would end, in words for the closing question."""

    reasons: tuple[str, ...]

    def question(self) -> str:
        if not self.reasons:
            return STOP_QUESTION
        return f"{' '.join(self.reasons)} Stopping Nexus Scholar now ends it. {STOP_QUESTION}"


def _mb(value: int) -> str:
    return f"{value / 1e6:.0f} MB"


class ControlPanel:
    """What the window shows and does, for one launcher; no Tk here."""

    def __init__(
        self,
        launcher: Any,
        *,
        settings_folder: Path,
        log_file: Path | None,
        open_browser_at_start: bool = True,
        clock: Callable[[], float] = time.monotonic,
        open_folder: Callable[[Path], None] | None = None,
    ):
        self.launcher = launcher
        self.settings_folder = Path(settings_folder)
        self.log_file = Path(log_file) if log_file is not None else None
        self.open_browser_at_start = open_browser_at_start
        self.clock = clock
        #: When the server was first seen answering; the browser hint counts from then.
        self.answered_at: float | None = None
        self.failure: str | None = None
        self.raise_requested = threading.Event()
        self._open_folder = open_folder or open_folder_on_desktop

    # -- what the window says -------------------------------------------------

    def status(self) -> str:
        """The status sentence: running, opening, saving a copy, refused, or failed."""
        if self.failure is not None:
            return FAILED
        root = getattr(self.launcher, "root", None)
        lines = [f"Nexus Scholar is running on this computer. Your reviews are in {root}."]
        gate = self._gate()
        if getattr(self.launcher, "opening", None) is not None:
            # A review is being opened (a restart, or a small review's copy before the server
            # answers): the last app's copy state is not this review's.
            lines.append("Opening your review…")
        elif gate is not None:
            snap = gate.snapshot()
            if snap.get("state") == "preparing":
                total = int(snap.get("total_bytes") or 0)
                done = int(snap.get("done_bytes") or 0)
                progress = f": {_mb(done)} of {_mb(total)}" if total else ""
                lines.append(f"Saving a copy of {snap.get('title')} before opening it{progress}.")
            elif snap.get("state") == "refused":
                refusal = snap.get("refusal") or {}
                lines.append(f"{snap.get('title')} was not opened: {refusal.get('message', 'refused')}")
        if self._browser_seems_blocked():
            lines.append(BROWSER_BLOCKED)
        return " ".join(lines)

    def busy(self) -> Busy:
        """What is in progress in the open review; the closing question names it."""
        reasons: list[str] = []
        workspace = getattr(self.launcher, "workspace", None)
        app = getattr(self.launcher, "app", None)
        gate = self._gate()
        if gate is not None and gate.snapshot().get("state") == "preparing":
            reasons.append("A copy of your review is being saved; the review opens only when it is complete.")
        if workspace is not None:
            try:
                from scholar_harness.workspace.catalog import busy

                state = busy(Path(workspace))
            except Exception:  # noqa: BLE001 - an unreadable review is not a reason to refuse a stop
                state = {}
            if state.get("run_active"):
                reasons.append("An agent run is in progress.")
            if state.get("pairing_open"):
                reasons.append("Approval codes are waiting to be used.")
            jobs = getattr(getattr(app, "state", None), "discovery_jobs", None) if app is not None else None
            try:
                job = jobs.active(Path(workspace).resolve()) if jobs is not None else None
            except Exception:  # noqa: BLE001
                job = None
            if job is not None:
                reasons.append("A search of the literature databases is in progress.")
        return Busy(tuple(reasons))

    # -- what the buttons do --------------------------------------------------

    def open_in_browser(self) -> None:
        """A new tab with a new one-time link (useful when the tab was closed)."""
        webbrowser.open(self.launcher.launch_url())

    def stop(self) -> None:
        self.launcher.request_stop()

    def open_log_folder(self) -> None:
        if self.log_file is not None:
            self._open_folder(self.log_file.parent)

    def open_settings(self) -> None:
        """The Settings screen in the browser, with a fresh one-time link (M13 Part B)."""
        webbrowser.open(self.launcher.launch_url("/en/settings/"))

    def details(self) -> str:
        """What "Copy the details" puts on the clipboard: version, system, log file, the error."""
        import platform

        from scholar_harness import __version__

        return "\n".join(
            [
                f"Nexus Scholar {__version__} on {platform.platform()}",
                f"Log file: {self.log_file}",
                f"Error: {self.failure or 'none'}",
            ]
        )

    # -- what the engine tells the window -----------------------------------

    def second_start(self) -> None:
        """A second click on the icon: the window comes to the front too."""
        self.raise_requested.set()

    def engine_failed(self, error: BaseException) -> None:
        self.failure = f"{type(error).__name__}: {error}"

    # -- helpers ------------------------------------------------------------

    def _gate(self) -> Any:
        app = getattr(self.launcher, "app", None)
        gate = getattr(getattr(app, "state", None), "format_gate", None) if app is not None else None
        return gate if gate is not None and hasattr(gate, "snapshot") else None

    def _server_started(self) -> bool:
        return bool(getattr(getattr(self.launcher, "_server", None), "started", False))

    def _browser_seems_blocked(self) -> bool:
        if not self.open_browser_at_start or not self._server_started():
            return False
        if self.answered_at is None:
            self.answered_at = self.clock()
        codes = getattr(self.launcher, "codes", None)
        if codes is None or getattr(codes, "redeemed", 0):
            return False
        return self.clock() - self.answered_at >= BROWSER_HINT_SECONDS


def open_folder_on_desktop(folder: Path) -> None:
    """Show a folder in Explorer, Finder or the Linux file manager; best-effort."""
    try:
        if sys.platform == "win32":
            os.startfile(str(folder))  # noqa: S606 - a folder of this user's, opened in Explorer
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])  # noqa: S603, S607
        else:
            subprocess.Popen(["xdg-open", str(folder)])  # noqa: S603, S607
    except OSError:
        pass


class ControlWindow:
    """The Tk view of a :class:`ControlPanel`; :meth:`run` returns when the window closes."""

    def __init__(self, panel: ControlPanel, engine: threading.Thread, root: Any):
        import tkinter as tk

        self.panel, self.engine, self.root = panel, engine, root
        self._stopping = False
        root.title(TITLE)
        set_icon(root)
        root.minsize(420, 0)
        frame = tk.Frame(root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)
        self.status = tk.Label(frame, text=panel.status(), wraplength=420, justify="left", anchor="w")
        self.status.pack(fill="x", pady=(0, 12))
        buttons = tk.Frame(frame)
        buttons.pack(fill="x")
        self.open_button = tk.Button(buttons, text="Open in browser", command=panel.open_in_browser)
        self.open_button.pack(side="left", padx=(0, 8))
        tk.Button(buttons, text="Settings", command=panel.open_settings).pack(side="left", padx=(0, 8))
        self.stop_button = tk.Button(buttons, text="Stop Nexus Scholar", command=self.ask_to_stop)
        self.stop_button.pack(side="left")
        links = tk.Frame(frame)
        links.pack(fill="x", pady=(12, 0))
        tk.Button(links, text="Show the log file", relief="flat", fg="#1a5fb4", command=panel.open_log_folder).pack(side="left")
        self.copy_button = tk.Button(links, text="Copy the details", relief="flat", fg="#1a5fb4", command=self.copy_details)
        root.protocol("WM_DELETE_WINDOW", self.ask_to_stop)
        root.after(POLL_MS, self.poll)

    def copy_details(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self.panel.details())
        self.root.update()

    def ask_to_stop(self) -> None:
        if self.panel.failure is not None or not self.engine.is_alive():
            self.root.destroy()
            return
        from tkinter import messagebox

        busy = self.panel.busy()
        if busy.reasons:
            stop = messagebox.askyesno(TITLE, busy.question() + "\n\nYes: stop now. No: keep running.", parent=self.root, default="no")
        else:
            stop = messagebox.askokcancel(TITLE, busy.question(), parent=self.root)
        if not self._alive():
            return  # the engine stopped (`--stop`) while the question was open; the window is gone
        if stop:
            self._stopping = True
            self.status.configure(text="Stopping Nexus Scholar…")
            self.open_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
            self.panel.stop()

    def _alive(self) -> bool:
        try:
            return bool(self.root.winfo_exists())
        except Exception:  # noqa: BLE001 - a destroyed root raises TclError
            return False

    def poll(self) -> None:
        if not self.engine.is_alive():
            if self.panel.failure is None or self._stopping:
                self.root.destroy()
                return
            # The engine stopped on an error: say so and keep the window for the log and the details.
            self.status.configure(text=self.panel.status())
            self.open_button.configure(state="disabled")
            self.stop_button.configure(text="Close", command=self.root.destroy)
            if not self.copy_button.winfo_ismapped():
                self.copy_button.pack(side="left")
            return
        if self.panel.raise_requested.is_set():
            self.panel.raise_requested.clear()
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        if not self._stopping:
            self.status.configure(text=self.panel.status())
        self.root.after(POLL_MS, self.poll)

    def run(self) -> None:
        self.root.mainloop()


def make_root() -> Any | None:
    """A Tk root for the window, or ``None`` with no Tk or no display (the start runs headless)."""
    try:
        import tkinter as tk

        return tk.Tk()
    except Exception:  # noqa: BLE001 - no Tk, no display
        return None
