"""An exclusive OS lock over a file (Windows and POSIX), as the screening events use."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class LockBusy(Exception):
    """The lock could not be taken; nothing was read or stored."""


@contextmanager
def locked(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            except OSError as exc:  # Windows gives up after ten retries
                raise LockBusy(str(exc)) from exc
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX)
            except OSError as exc:
                raise LockBusy(str(exc)) from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
