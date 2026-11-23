"""The machine-wide lock the gate puts around a full suite (H-gate-and-ci)."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "suite_lock.py"
SPEC = importlib.util.spec_from_file_location("suite_lock", SCRIPT)
assert SPEC and SPEC.loader
LOCK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOCK)


@pytest.fixture
def lock_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "suite.lock"
    monkeypatch.setenv("NEXUS_SUITE_LOCK", str(path))
    return path


def _holder(path: Path) -> subprocess.Popen[bytes]:
    """Another process that takes the lock and keeps it until it is killed or ends (30 s)."""
    process = subprocess.Popen(
        [sys.executable, str(SCRIPT), "--", sys.executable, "-c", "import time; time.sleep(30)"],
        env={**os.environ, "NEXUS_SUITE_LOCK": str(path)},
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 15
    while not LOCK.holder_path(path).exists():
        assert time.monotonic() < deadline, "the holder never took the lock"
        time.sleep(0.02)
    return process


def test_the_lock_lives_outside_the_checkout_unless_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEXUS_SUITE_LOCK", raising=False)
    path = LOCK.lock_path()
    assert path.name == "nexus-scholar-suite.lock"
    assert Path(__file__).resolve().parents[2] not in path.resolve().parents


def test_a_free_lock_is_taken_named_and_given_back(lock_file: Path) -> None:
    held = LOCK.acquire(lock_file, ["pytest", "-q"], timeout=1)
    assert held is not None
    assert LOCK.read_holder(lock_file)["pid"] == os.getpid()
    assert LOCK.read_holder(lock_file)["command"] == "pytest -q"
    LOCK.release(held)
    assert not LOCK.holder_path(lock_file).exists()
    again = LOCK.acquire(lock_file, ["pytest"], timeout=1)
    assert again is not None
    LOCK.release(again)


def test_a_held_lock_makes_the_second_caller_wait_and_give_up(lock_file: Path) -> None:
    held = LOCK.acquire(lock_file, ["uv", "run", "pytest", "-q", "-n", "4"], timeout=1)
    assert held is not None
    try:
        out = io.StringIO()
        began = time.monotonic()
        assert LOCK.acquire(lock_file, ["pytest"], timeout=0.3, poll=0.05, out=out) is None
        assert time.monotonic() - began >= 0.3
        assert "waiting; a full suite is running" in out.getvalue()
        assert "uv run pytest -q -n 4" in out.getvalue()
        assert "gave up" in out.getvalue()
    finally:
        LOCK.release(held)


def test_the_lock_of_a_holder_that_was_killed_is_freed_by_the_system(lock_file: Path) -> None:
    holder = _holder(lock_file)
    assert LOCK.acquire(lock_file, ["pytest"], timeout=0.2, poll=0.05, out=io.StringIO()) is None
    holder.kill()
    holder.wait(timeout=15)
    out = io.StringIO()
    held = LOCK.acquire(lock_file, ["pytest"], timeout=10, poll=0.05, out=out)
    assert held is not None
    assert "ended without releasing" in out.getvalue()
    assert LOCK.read_holder(lock_file)["pid"] == os.getpid()
    LOCK.release(held)


def test_a_holder_file_not_yet_written_never_frees_the_lock(lock_file: Path) -> None:
    """The race the first build had: an empty or unreadable holder file is not a stale lock."""
    held = LOCK.acquire(lock_file, ["pytest"], timeout=1)
    assert held is not None
    try:
        LOCK.holder_path(lock_file).write_text("", encoding="utf-8")
        out = io.StringIO()
        assert LOCK.acquire(lock_file, ["pytest"], timeout=0.2, poll=0.05, out=out) is None
        assert "has not written its name yet" in out.getvalue()
    finally:
        LOCK.release(held)


def test_a_lock_held_for_hours_is_reported_not_broken(lock_file: Path) -> None:
    held = LOCK.acquire(lock_file, ["pytest"], timeout=1)
    assert held is not None
    try:
        record = {**held.record, "started": time.time() - 4 * 3600}
        LOCK.holder_path(lock_file).write_text(json.dumps(record), encoding="utf-8")
        out = io.StringIO()
        assert LOCK.acquire(lock_file, ["pytest"], timeout=0.2, max_age=3600, poll=0.05, out=out) is None
        assert "held for over 3600 s" in out.getvalue()
    finally:
        LOCK.release(held)


def test_release_keeps_a_holder_file_that_is_no_longer_ours(lock_file: Path) -> None:
    held = LOCK.acquire(lock_file, ["pytest"], timeout=1)
    assert held is not None
    other = {**held.record, "pid": os.getpid() + 1}
    LOCK.holder_path(lock_file).write_text(json.dumps(other), encoding="utf-8")
    LOCK.release(held)
    assert LOCK.read_holder(lock_file) == other


def test_main_runs_the_command_returns_its_code_and_releases(lock_file: Path) -> None:
    code = LOCK.main(["--", sys.executable, "-c", "import sys; sys.exit(3)"])
    assert code == 3
    assert not LOCK.holder_path(lock_file).exists()
    held = LOCK.acquire(lock_file, ["pytest"], timeout=1)
    assert held is not None
    LOCK.release(held)


def test_main_returns_75_when_the_lock_stays_busy(lock_file: Path) -> None:
    held = LOCK.acquire(lock_file, ["pytest"], timeout=1)
    assert held is not None
    try:
        assert LOCK.main(["--timeout", "0", "--", sys.executable, "-c", "pass"]) == LOCK.EXIT_TIMEOUT
    finally:
        LOCK.release(held)


def test_status_names_the_holder(lock_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert LOCK.main(["--status"]) == 0
    assert "free" in capsys.readouterr().out
    held = LOCK.acquire(lock_file, ["npm", "--prefix", "apps/research-ui", "test"], timeout=1)
    assert held is not None
    try:
        assert LOCK.main(["--status"]) == 0
        assert "held by pid" in capsys.readouterr().out
    finally:
        LOCK.release(held)


@pytest.mark.slow
def test_a_second_session_waits_for_the_first_to_finish(lock_file: Path) -> None:
    """Two real processes: the second starts its command only after the first released the lock."""
    marks = lock_file.parent / "marks.txt"

    def child(tag: str, seconds: float) -> subprocess.Popen[bytes]:
        body = (
            "import sys, time; "
            f"open(sys.argv[1], 'a').write('{tag} start %f\\n' % time.time()); "
            f"time.sleep({seconds}); "
            f"open(sys.argv[1], 'a').write('{tag} end %f\\n' % time.time())"
        )
        return subprocess.Popen(
            [sys.executable, str(SCRIPT), "--", sys.executable, "-c", body, str(marks)],
            env={**os.environ, "NEXUS_SUITE_LOCK": str(lock_file)},
            stderr=subprocess.PIPE,
        )

    first = child("first", 1.0)
    deadline = time.monotonic() + 15
    while not LOCK.holder_path(lock_file).exists():
        assert time.monotonic() < deadline, "the first session never took the lock"
        time.sleep(0.02)
    second = child("second", 0.1)
    assert first.wait(timeout=30) == 0
    _, err = second.communicate(timeout=30)
    assert second.returncode == 0
    times = {" ".join(line.split()[:2]): float(line.split()[2]) for line in marks.read_text().splitlines()}
    assert times["second start"] >= times["first end"]
    assert b"waiting; a full suite is running" in err
    assert not LOCK.holder_path(lock_file).exists()
