"""Run a command under one machine-wide lock, so two sessions never run a full suite at once.

Usage (the gate commands in ``docs/architecture/test_gate_manifest.json`` call it this way)::

    uv run python scripts/suite_lock.py -- uv run pytest -q -n 4 --dist worksteal
    uv run python scripts/suite_lock.py --status

The lock is one file for the whole machine, outside every checkout and worktree:
``NEXUS_SUITE_LOCK`` if set, else ``<temp>/nexus-scholar-suite.lock``. It holds the holder's
process id, host, start time, folder and command. A second caller waits, saying every minute
who holds the lock, until it is released; ``--timeout`` gives up after that many seconds
(exit 75).

Stale-lock rule: a lock is taken over when its holder process is no longer running on this
host, when it is older than ``--max-age`` seconds (default 3 hours, longer than any full
suite has run; it also covers a reused process id), or when its file cannot be read. The
command's own exit code is returned; the lock is released however the command ends.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, TextIO

EXIT_TIMEOUT = 75  # EX_TEMPFAIL: the lock stayed busy.
DEFAULT_MAX_AGE = 3 * 60 * 60
POLL_SECONDS = 2.0
REPORT_EVERY = 60.0


def lock_path() -> Path:
    override = os.environ.get("NEXUS_SUITE_LOCK")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "nexus-scholar-suite.lock"


def pid_running(pid: int) -> bool:
    """True when a process with this id is running on this machine."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        process_query_limited_information = 0x1000
        still_active = 259
        error_access_denied = 5
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            # Access denied means the process exists but belongs to someone else.
            return ctypes.get_last_error() == error_access_denied
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_holder(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def stale_reason(holder: dict[str, Any] | None, *, max_age: float, now: float) -> str | None:
    """Why a held lock may be taken over, or None when its holder is alive and recent."""
    if holder is None:
        return "the lock file cannot be read"
    started = holder.get("started")
    if not isinstance(started, (int, float)):
        return "the lock file has no start time"
    if now - started > max_age:
        return f"it is older than {int(max_age)} s"
    if holder.get("host") == socket.gethostname():
        pid = holder.get("pid")
        if not isinstance(pid, int) or not pid_running(pid):
            return f"its holder (pid {pid}) is no longer running"
    return None


def describe(holder: dict[str, Any] | None) -> str:
    if not holder:
        return "an unreadable holder"
    started = holder.get("started")
    since = time.strftime("%H:%M:%S", time.localtime(started)) if isinstance(started, (int, float)) else "?"
    return f"pid {holder.get('pid')} since {since} in {holder.get('cwd')}: {holder.get('command')}"


def try_acquire(path: Path, record: dict[str, Any]) -> bool:
    """Create the lock file atomically; False when it already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle)
    return True


def release(path: Path, record: dict[str, Any]) -> None:
    """Remove the lock only while it is still ours."""
    holder = read_holder(path)
    if holder and holder.get("pid") == record["pid"] and holder.get("started") == record["started"]:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def acquire(
    path: Path,
    command: list[str],
    *,
    timeout: float | None,
    max_age: float,
    poll: float = POLL_SECONDS,
    out: TextIO | None = None,
) -> dict[str, Any] | None:
    """Wait for the lock and take it; None when ``timeout`` ran out."""
    out = out or sys.stderr
    record: dict[str, Any] = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started": time.time(),
        "cwd": os.getcwd(),
        "command": " ".join(command),
    }
    began = time.monotonic()
    last_report = -REPORT_EVERY
    while True:
        record["started"] = time.time()
        if try_acquire(path, record):
            return record
        holder = read_holder(path)
        reason = stale_reason(holder, max_age=max_age, now=time.time())
        if reason is not None:
            print(f"suite-lock: taking over a stale lock ({reason}): {describe(holder)}", file=out, flush=True)
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue
        waited = time.monotonic() - began
        if timeout is not None and waited >= timeout:
            print(f"suite-lock: gave up after {int(waited)} s; held by {describe(holder)}", file=out, flush=True)
            return None
        if waited - last_report >= REPORT_EVERY:
            print(f"suite-lock: waiting; a full suite is running: {describe(holder)}", file=out, flush=True)
            last_report = waited
        time.sleep(poll)


def run(command: list[str]) -> int:
    """Run the command; on Windows ``npm`` and ``uv`` are found through PATH with their extension."""
    executable = shutil.which(command[0]) or command[0]
    return subprocess.call([executable, *command[1:]])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--timeout", type=float, default=None, help="give up after this many seconds (exit 75)")
    parser.add_argument("--max-age", type=float, default=DEFAULT_MAX_AGE, help="a lock older than this is stale")
    parser.add_argument("--status", action="store_true", help="print the holder and exit")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="the command to run, after --")
    args = parser.parse_args(argv)
    path = lock_path()
    if args.status:
        if not path.exists():
            print(f"suite-lock: free ({path})")
            return 0
        holder = read_holder(path)
        reason = stale_reason(holder, max_age=args.max_age, now=time.time())
        state = f"stale ({reason})" if reason else "held"
        print(f"suite-lock: {state} by {describe(holder)} ({path})")
        return 0
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("give the command to run after --")
    record = acquire(path, command, timeout=args.timeout, max_age=args.max_age)
    if record is None:
        return EXIT_TIMEOUT
    try:
        return run(command)
    finally:
        release(path, record)


if __name__ == "__main__":
    raise SystemExit(main())
