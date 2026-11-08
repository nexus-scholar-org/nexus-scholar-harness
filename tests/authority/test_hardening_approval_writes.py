"""M6-hardening H1: the batch review and approval files are written atomically.

Full review 2026-11-06 (T-P2): ``review.py`` wrote both files in place, so a
crash mid-approval could leave a torn approval that fails safe but needs a
manual repair. A crash before the replace (simulated by failing
``os.replace``) must now leave neither file, nor a temporary file, behind.
Before the fix the approval never reached ``os.replace``, so the simulated
crash never fired and both files were written in place.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scholar_harness.authority.review import batch_approval_path, review_path
from scholar_harness.workspace import atomic

from .test_ag04_interaction import _approve, _recommend, _scaffold, _write_decisions, _write_operator_context


def test_a_crash_while_approving_leaves_no_torn_approval(tmp_path: Path, monkeypatch) -> None:
    workspace, studies = _scaffold(tmp_path)
    _write_operator_context(workspace)
    _recommend(workspace)
    _write_decisions(workspace, studies)

    def crash(src, dst):
        raise OSError("power cut before the replace")

    monkeypatch.setattr(atomic.os, "replace", crash)
    with pytest.raises(OSError, match="power cut"):
        _approve(workspace, message="interrupted approval")

    for path in (review_path(workspace, 1), batch_approval_path(workspace, 1)):
        assert not path.exists(), path
        assert [p.name for p in path.parent.glob("*.tmp-*")] == []
