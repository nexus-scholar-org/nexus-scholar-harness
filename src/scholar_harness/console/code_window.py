"""Show approval codes in a window on this computer's desktop (finding 38).

When `nexus-scholar ui` was started for the researcher, the terminal that
prints the approval codes may be hidden. This window is the same kind of
surface as that terminal: it belongs to the engine's own process, on this
computer's desktop, and nothing in it travels over HTTP. What a code proves
does not change: someone at this computer saw it (decision 2026-11-04,
UI-07 §2).

Rules kept here:

* the codes are never in the window title (other programs can read titles);
* the window closes itself when the codes expire;
* it is best-effort: with no display or no Tk, the codes stay on the terminal
  only, and the caller says so (`code_shown_on: "terminal"`).
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from datetime import datetime, timezone

#: Set to "0" to keep the codes on the terminal only.
WINDOW_ENV = "NEXUS_APPROVAL_WINDOW"

TITLE = "Nexus Scholar: approval"
_START_TIMEOUT_S = 3.0


def enabled() -> bool:
    return os.environ.get(WINDOW_ENV, "1").strip() not in ("0", "false", "no", "off")


def message(batches: list[int], expires_at: str) -> str:
    """The words above the codes (no code in them)."""
    try:
        moment = datetime.fromisoformat(expires_at).astimezone()
        until = moment.strftime("%H:%M")
    except ValueError:
        until = expires_at
    count = len(batches)
    what = f"batch {batches[0]}" if count == 1 else f"{count} batches"
    return (
        f"Approval code for {what}. Copy the block below into the Publish screen "
        f"and press Approve. Each line approves one batch, once. "
        f"The codes expire at {until}; this window closes then."
    )


def _seconds_left(expires_at: str) -> float:
    try:
        moment = datetime.fromisoformat(expires_at)
    except ValueError:
        return 300.0
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return max(1.0, (moment - datetime.now(timezone.utc)).total_seconds())


def _run_window(codes: str, batches: list[int], expires_at: str, started: threading.Event, ok: list[bool]) -> None:
    try:
        import tkinter as tk
    except Exception:  # noqa: BLE001 - no Tk in this Python: terminal only
        started.set()
        return
    try:
        root = tk.Tk()
    except Exception:  # noqa: BLE001 - no display: terminal only
        started.set()
        return
    ok.append(True)
    started.set()
    root.title(TITLE)
    root.attributes("-topmost", True)
    tk.Label(root, text=message(batches, expires_at), wraplength=460, justify="left").pack(padx=16, pady=(16, 8), anchor="w")
    lines = codes.count("\n") + 1
    text = tk.Text(root, width=40, height=min(12, lines), font=("Courier", 11))
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
    root.mainloop()


def reveal(*, codes: str, batches: list[int], expires_at: str) -> bool:
    """Open the window in its own thread; ``True`` once it is on the desktop."""
    if not enabled():
        return False
    started = threading.Event()
    ok: list[bool] = []
    threading.Thread(
        target=_run_window, args=(codes, batches, expires_at, started, ok), daemon=True, name="approval-code-window"
    ).start()
    started.wait(_START_TIMEOUT_S)
    return bool(ok)


CodeWindow = Callable[..., bool]
