"""The app's icon in the title bar of its Tk windows (H-b8-small-faults).

Used by the control window, the approval-code window and the folder dialog.
Standard library only: the approval-code window and the folder dialog run as
`python -I <their file>` outside the bundle and load this file beside them.

The icon is a copy of `packaging/icons/nexus-scholar.ico` kept beside this
module, so a wheel install and the bundle (which collects the package's data)
both have it; `tests/test_windows_packaging.py` checks that the two files are
the same bytes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ICON = Path(__file__).resolve().with_name("nexus-scholar.ico")


def set_icon(root: Any, icon: Path = ICON) -> bool:
    """Put the app's icon in a Tk root's title bar; ``False`` when it cannot.

    Tk takes an ``.ico`` only on Windows; elsewhere, or with the file missing,
    the window keeps Tk's own icon: an icon is never a reason for a window not
    to open.
    """
    try:
        if not Path(icon).is_file():
            return False
        root.iconbitmap(default=str(icon))
    except Exception:  # noqa: BLE001 - tk.TclError on a platform without .ico support, or any Tk refusal
        return False
    return True
