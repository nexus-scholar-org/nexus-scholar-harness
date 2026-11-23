"""The machine-wide lock the gate puts around a full suite (H-gate-and-ci)."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import socket
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


def _hold(path: Path, **fields: object) -> dict[str, object]:
    record: dict[str, object] = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started": time.time(),
        "cwd": "elsewhere",
        "command": "uv run pytest -q -n 4",
    }
    record.update(fields)
    path.write_text(json.dumps(record), encoding="utf-8")
    return record


def _finished_pid() -> int:
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait()
    return process.pid


def test_the_lock_lives_outside_the_checkout_unless_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEXUS_SUITE_LOCK", raising=False)
    path = LOCK.lock_path()
    assert path.name == "nexus-scholar-suite.lock"
    assert Path(__file__).resolve().parents[2] not in path.resolve().parents


def test_a_free_lock_is_taken_and_given_back(lock_file: Path) -> None:
    record = LOCK.acquire(lock_file, ["pytest", "-q"], timeout=1, max_age=60)
    assert record is not None
    assert json.loads(lock_file.read_text(encoding="utf-8"))["pid"] == os.getpid()
    LOCK.release(lock_file, record)
    assert not lock_file.exists()


def test_a_running_holder_makes_the_second_caller_wait_and_give_up(lock_file: Path) -> None:
    holder = _hold(lock_file)
    out = io.StringIO()
    began = time.monotonic()
    assert LOCK.acquire(lock_file, ["pytest"], timeout=0.3, max_age=3600, poll=0.05, out=out) is None
    assert time.monotonic() - began >= 0.3
    assert json.loads(lock_file.read_text(encoding="utf-8")) == holder
    assert "waiting; a full suite is running" in out.getvalue()
    assert "gave up" in out.getvalue()


def test_a_lock_whose_holder_has_ended_is_taken_over(lock_file: Path) -> None:
    _hold(lock_file, pid=_finished_pid())
    out = io.StringIO()
    record = LOCK.acquire(lock_file, ["pytest"], timeout=1, max_age=3600, poll=0.05, out=out)
    assert record is not None
    assert "no longer running" in out.getvalue()
    assert json.loads(lock_file.read_text(encoding="utf-8"))["pid"] == os.getpid()


def test_a_lock_older_than_the_limit_is_taken_over(lock_file: Path) -> None:
    _hold(lock_file, started=time.time() - 7200)
    out = io.StringIO()
    assert LOCK.acquire(lock_file, ["pytest"], timeout=1, max_age=3600, poll=0.05, out=out) is not None
    assert "older than 3600 s" in out.getvalue()


def test_an_unreadable_lock_is_taken_over(lock_file: Path) -> None:
    lock_file.write_text("{not json", encoding="utf-8")
    assert LOCK.acquire(lock_file, ["pytest"], timeout=1, max_age=3600, poll=0.05, out=io.StringIO()) is not None


def test_a_recent_lock_from_another_host_is_respected(lock_file: Path) -> None:
    # The process id means nothing on another machine; only the age can make it stale.
    _hold(lock_file, host="another-machine", pid=_finished_pid())
    assert LOCK.acquire(lock_file, ["pytest"], timeout=0.2, max_age=3600, poll=0.05, out=io.StringIO()) is None


def test_release_leaves_a_lock_that_is_no_longer_ours(lock_file: Path) -> None:
    record = LOCK.acquire(lock_file, ["pytest"], timeout=1, max_age=60)
    assert record is not None
    other = _hold(lock_file, pid=os.getpid() + 1)
    LOCK.release(lock_file, record)
    assert json.loads(lock_file.read_text(encoding="utf-8")) == other


def test_main_runs_the_command_returns_its_code_and_releases(lock_file: Path) -> None:
    code = LOCK.main(["--", sys.executable, "-c", "import sys; sys.exit(3)"])
    assert code == 3
    assert not lock_file.exists()


def test_main_returns_75_when_the_lock_stays_busy(lock_file: Path) -> None:
    _hold(lock_file)
    assert LOCK.main(["--timeout", "0", "--", sys.executable, "-c", "pass"]) == LOCK.EXIT_TIMEOUT


def test_status_names_the_holder(lock_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert LOCK.main(["--status"]) == 0
    assert "free" in capsys.readouterr().out
    _hold(lock_file, command="npm --prefix apps/research-ui test")
    assert LOCK.main(["--status"]) == 0
    assert "held by" in capsys.readouterr().out


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
    deadline = time.monotonic() + 10
    while not lock_file.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert lock_file.exists(), "the first session never took the lock"
    second = child("second", 0.1)
    assert first.wait(timeout=30) == 0
    _, err = second.communicate(timeout=30)
    assert second.returncode == 0
    lines = dict((line.split()[0] + " " + line.split()[1], float(line.split()[2])) for line in marks.read_text().splitlines())
    assert lines["second start"] >= lines["first end"]
    assert b"waiting; a full suite is running" in err
    assert not lock_file.exists()
