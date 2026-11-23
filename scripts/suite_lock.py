"""Run a command under one machine-wide lock, so two sessions never run a full suite at once.

Usage (the gate commands in ``docs/architecture/test_gate_manifest.json`` call it this way)::

    uv run python scripts/suite_lock.py -- uv run pytest -q -n 4 --dist worksteal
    uv run python scripts/suite_lock.py --status

The lock is the operating system's lock on one file for the whole machine, outside every
checkout and worktree: ``NEXUS_SUITE_LOCK`` if set, else ``<temp>/nexus-scholar-suite.lock``
(``msvcrt.locking`` on Windows, ``fcntl.flock`` elsewhere). Beside it, ``<lock>.json`` names
the holder: process id, host, start time, folder and command. A second caller waits, saying
every minute who holds the lock, until it is free; ``--timeout`` gives up after that many
seconds (exit 75).

Stale-lock rule: the system frees the lock when its holder process ends, however it ends
(finished, crashed, killed, the PC restarted), so a lock never outlives its holder and there
is nothing to take over or delete. A holder file left by a holder that ended is ignored and
replaced, and the takeover is printed. A lock held longer than ``--max-age`` (3 hours) is
reported while waiting, because its holder is alive but may be stuck; stopping that session is
the researcher's call, not the script's.

The command's own exit code is returned; the lock is released however the command ends.
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
from typing import Any, BinaryIO, TextIO

EXIT_TIMEOUT = 75  # EX_TEMPFAIL: the lock stayed busy.
DEFAULT_MAX_AGE = 3 * 60 * 60
POLL_SECONDS = 2.0
REPORT_EVERY = 60.0


def lock_path() -> Path:
    override = os.environ.get("NEXUS_SUITE_LOCK")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "nexus-scholar-suite.lock"


def holder_path(path: Path) -> Path:
    return path.with_name(path.name + ".json")


def _os_lock(handle: BinaryIO) -> bool:
    """Take the system lock on the file's first byte without waiting; False when it is held."""
    handle.seek(0)
    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _os_unlock(handle: BinaryIO) -> None:
    handle.seek(0)
    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def read_holder(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(holder_path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def describe(holder: dict[str, Any] | None) -> str:
    if not holder:
        return "a holder that has not written its name yet"
    started = holder.get("started")
    since = time.strftime("%H:%M:%S", time.localtime(started)) if isinstance(started, (int, float)) else "?"
    return f"pid {holder.get('pid')} since {since} in {holder.get('cwd')}: {holder.get('command')}"


class Held:
    """A taken lock: the open file that carries the system lock, and our holder record."""

    def __init__(self, path: Path, handle: BinaryIO, record: dict[str, Any]) -> None:
        self.path = path
        self.handle = handle
        self.record = record


def try_acquire(path: Path, command: list[str]) -> Held | None:
    """Take the lock now, or return None while another process holds it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+b")  # noqa: SIM115 - held open for as long as the lock is held
    if not _os_lock(handle):
        handle.close()
        return None
    record = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started": time.time(),
        "cwd": os.getcwd(),
        "command": " ".join(command),
    }
    target = holder_path(path)
    scratch = target.with_name(f"{target.name}.{os.getpid()}.tmp")
    scratch.write_text(json.dumps(record), encoding="utf-8")
    os.replace(scratch, target)
    return Held(path, handle, record)


def release(held: Held) -> None:
    """Remove our holder file and free the lock."""
    if read_holder(held.path) == held.record:
        try:
            holder_path(held.path).unlink()
        except OSError:
            pass
    _os_unlock(held.handle)
    held.handle.close()


def acquire(
    path: Path,
    command: list[str],
    *,
    timeout: float | None,
    max_age: float = DEFAULT_MAX_AGE,
    poll: float = POLL_SECONDS,
    out: TextIO | None = None,
) -> Held | None:
    """Wait for the lock and take it; None when ``timeout`` ran out."""
    out = out or sys.stderr
    began = time.monotonic()
    last_report = -REPORT_EVERY
    while True:
        left_behind = read_holder(path)
        held = try_acquire(path, command)
        if held is not None:
            if left_behind and left_behind.get("pid") != os.getpid():
                print(
                    f"suite-lock: the previous holder ended without releasing (the system freed its lock): "
                    f"{describe(left_behind)}",
                    file=out,
                    flush=True,
                )
            return held
        holder = read_holder(path)
        waited = time.monotonic() - began
        if timeout is not None and waited >= timeout:
            print(f"suite-lock: gave up after {int(waited)} s; held by {describe(holder)}", file=out, flush=True)
            return None
        if waited - last_report >= REPORT_EVERY:
            note = ""
            started = (holder or {}).get("started")
            if isinstance(started, (int, float)) and time.time() - started > max_age:
                note = f" (held for over {int(max_age)} s: if that session is stuck, stop it; the lock is freed when its process ends)"
            print(f"suite-lock: waiting; a full suite is running: {describe(holder)}{note}", file=out, flush=True)
            last_report = waited
        time.sleep(poll)


def run(command: list[str]) -> int:
    """Run the command; on Windows ``npm`` and ``uv`` are found through PATH with their extension."""
    executable = shutil.which(command[0]) or command[0]
    return subprocess.call([executable, *command[1:]])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--timeout", type=float, default=None, help="give up after this many seconds (exit 75)")
    parser.add_argument("--max-age", type=float, default=DEFAULT_MAX_AGE, help="report a holder older than this")
    parser.add_argument("--status", action="store_true", help="print the holder and exit")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="the command to run, after --")
    args = parser.parse_args(argv)
    path = lock_path()
    if args.status:
        probe = try_acquire(path, ["--status"])
        if probe is not None:
            release(probe)
            print(f"suite-lock: free ({path})")
        else:
            print(f"suite-lock: held by {describe(read_holder(path))} ({path})")
        return 0
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("give the command to run after --")
    held = acquire(path, command, timeout=args.timeout, max_age=args.max_age)
    if held is None:
        return EXIT_TIMEOUT
    try:
        return run(command)
    finally:
        release(held)


if __name__ == "__main__":
    raise SystemExit(main())
