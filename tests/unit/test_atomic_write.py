"""M6-hardening H1/H2: one atomic writer, and a Windows-tolerant ``os.replace``.

A torn settings or operator-context file fails safe but needs manual repair
(full review 2026-11-06, T-P2); an antivirus or indexer briefly holding a file
on Windows surfaces as a 500. The helper writes a sibling temporary file and
replaces the target, retrying a ``PermissionError`` on Windows only.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scholar_harness.workspace import atomic


def test_the_written_bytes_match_write_text(tmp_path: Path) -> None:
    """Digests are computed over ``write_text`` bytes; the helper must not move them."""
    text = '{\n  "a": "é"\n}\n'
    reference = tmp_path / "reference.json"
    reference.write_text(text, encoding="utf-8")
    target = tmp_path / "sub" / "target.json"
    atomic.atomic_write_text(target, text)
    assert target.read_bytes() == reference.read_bytes()


def test_a_crash_before_the_replace_keeps_the_old_file_and_no_temp(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "settings.json"
    target.write_text("old\n", encoding="utf-8")

    def crash(src, dst):
        raise OSError("power cut")

    monkeypatch.setattr(atomic.os, "replace", crash)
    with pytest.raises(OSError, match="power cut"):
        atomic.atomic_write_text(target, "new\n")
    assert target.read_text(encoding="utf-8") == "old\n"
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_a_transient_windows_hold_is_retried(tmp_path: Path, monkeypatch) -> None:
    calls: list[int] = []
    real_replace = os.replace

    def held_twice(src, dst):
        calls.append(1)
        if len(calls) <= 2:
            raise PermissionError(13, "The process cannot access the file")
        real_replace(src, dst)

    monkeypatch.setattr(atomic, "_IS_WINDOWS", True)
    monkeypatch.setattr(atomic.os, "replace", held_twice)
    monkeypatch.setattr(atomic.time, "sleep", lambda s: None)
    target = tmp_path / "f.json"
    atomic.atomic_write_text(target, "x\n")
    assert len(calls) == 3
    assert target.read_text(encoding="utf-8") == "x\n"


def test_a_lasting_hold_is_raised_after_the_last_attempt(tmp_path: Path, monkeypatch) -> None:
    calls: list[int] = []

    def always_held(src, dst):
        calls.append(1)
        raise PermissionError(13, "held")

    monkeypatch.setattr(atomic, "_IS_WINDOWS", True)
    monkeypatch.setattr(atomic.os, "replace", always_held)
    monkeypatch.setattr(atomic.time, "sleep", lambda s: None)
    target = tmp_path / "f.json"
    with pytest.raises(PermissionError):
        atomic.atomic_write_text(target, "x\n")
    assert len(calls) == atomic.REPLACE_ATTEMPTS
    assert not target.exists() and list(tmp_path.iterdir()) == []


def test_a_permission_error_elsewhere_is_not_retried(tmp_path: Path, monkeypatch) -> None:
    calls: list[int] = []

    def denied(src, dst):
        calls.append(1)
        raise PermissionError(13, "denied")

    monkeypatch.setattr(atomic, "_IS_WINDOWS", False)
    monkeypatch.setattr(atomic.os, "replace", denied)
    with pytest.raises(PermissionError):
        atomic.replace_with_retry(tmp_path / "a", tmp_path / "b")
    assert len(calls) == 1
