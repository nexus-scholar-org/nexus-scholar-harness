"""M13 Part A: the approval-code window starts inside a frozen bundle (trial build fault 3).

In a PyInstaller bundle ``sys.executable`` is the app, not Python, so
``sys.executable -I code_window.py`` answered ``No such option: -I``. Frozen,
the window is started as the app itself with a dedicated flag, which the
app's entry points hand to the window before anything else loads.
"""

from __future__ import annotations

import sys

from scholar_harness.console import code_window


def test_frozen_the_window_is_started_as_the_app_with_its_flag(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Programs\Nexus Scholar\Nexus Scholar.exe")
    assert code_window._command() == [r"C:\Programs\Nexus Scholar\Nexus Scholar.exe", code_window.CHILD_FLAG]


def test_from_python_the_window_still_runs_isolated(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    command = code_window._command()
    assert command[:2] == [sys.executable, "-I"] and command[2].endswith("code_window.py")


def test_both_entry_points_hand_the_flag_to_the_window(monkeypatch):
    from scholar_harness import cli
    from scholar_harness.console import desktop

    shown = []
    monkeypatch.setattr(code_window, "run_child", lambda: shown.append("window") or 0)
    assert desktop.main([code_window.CHILD_FLAG]) == 0
    monkeypatch.setattr(sys, "argv", ["nexus-scholar", code_window.CHILD_FLAG])
    assert cli.main() == 0
    assert shown == ["window", "window"]
