"""Contribution-gate surface: the pre-push hook must actually be runnable.

Git silently ignores a hook file that lacks the executable bit, so a committed
``100644`` mode turns the fork+PR gate into documentation. The check is POSIX
only: Windows has no meaningful execute bit for git hooks, and the hook itself
carries a POSIX shebang.
"""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / "scripts" / "hooks" / "pre-push"


@pytest.mark.skipif(sys.platform == "win32", reason="no execute bit on Windows")
def test_pre_push_hook_is_executable() -> None:
    assert HOOK.is_file(), "the pre-push hook is missing"
    assert HOOK.stat().st_mode & stat.S_IXUSR, (
        "scripts/hooks/pre-push is not executable; git ignores a non-executable "
        "hook, so the fork+PR gate would not run"
    )


def test_pre_push_hook_has_a_shebang() -> None:
    first_line = HOOK.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("#!"), "a hook without a shebang cannot execute"


def test_hook_instructions_point_at_the_fork_workflow() -> None:
    text = HOOK.read_text(encoding="utf-8")
    assert "fork" in text.lower()
    assert "origin" in text.lower()
