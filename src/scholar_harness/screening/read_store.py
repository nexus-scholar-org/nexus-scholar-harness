"""What the display routes read once and keep (H-screening-read-performance).

Two things, both active only inside :func:`display_reads`, which the routes that
*show* a state enter (publication status, the next step, the PRISMA preview, the
corpus, the workspaces list, the charting table, the discovery checks). Outside
it every function here is a plain read of the disk, so Approve, Publish, export,
the methods paragraph and every write path read the disk as they always did
(question 3, decided 2026-11-22).

1. **One read per file per request.** :func:`read_bytes` and :func:`read_text`
   keep a file's bytes for the rest of the request, so the context, the event
   log and the decision files are opened once although several checks read them.
2. **Results kept between requests.** :func:`remember` keeps a computed result
   per workspace, keyed by the name, size and modification time of every file
   under the workspace (the folders in :data:`NOT_READ` aside, which no kept
   result reads; a test checks it). A result is reused only when every key is
   unchanged; a file added, removed or rewritten recomputes it. The key is read
   before and after the computation, and a result is kept only when both match,
   so a write during the computation is never kept. Nothing is written to disk.

Known cost (question 3): a file rewritten by hand with the same size within one
tick of the file system's clock is not noticed by a display route.
"""

from __future__ import annotations

import copy
import os
import threading
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")

#: Top-level folders of a workspace that no kept result reads (full texts,
#: extracted text, the RAG index, synthesis drafts, caches, the charting table's
#: own files). Left out of the key so a full text downloaded or a chart edited
#: does not throw away the screening's results.
NOT_READ = frozenset({"pdfs", "extracted", "rag", "synthesis", ".cache", "charting"})
#: How many workspaces keep results at once (the workspaces list visits each).
MAX_WORKSPACES = 32

_request: ContextVar[dict[str, tuple[tuple[int, int], bytes]] | None] = ContextVar("scholar_read_store_request", default=None)
_lock = threading.Lock()
_kept: OrderedDict[str, dict[str, tuple[tuple[Any, ...], Any]]] = OrderedDict()


@contextmanager
def display_reads() -> Iterator[None]:
    """Read through the store for the rest of this call (a display route's body)."""
    if _request.get() is not None:
        yield
        return
    token = _request.set({})
    try:
        yield
    finally:
        _request.reset(token)


def display_route(function: Callable[..., T]) -> Callable[..., T]:
    """A route that shows a state: its body runs inside :func:`display_reads`."""

    @wraps(function)
    def route(*args: Any, **kwargs: Any) -> T:
        with display_reads():
            return function(*args, **kwargs)

    return route


def active() -> bool:
    return _request.get() is not None


def read_bytes(path: Path | str) -> bytes:
    """The file's bytes; inside a display call, opened once per call.

    The bytes kept are reused only while the file's size and modification time
    are the ones read with them, so a kept result never combines bytes read
    before a change with a key read after it.
    """
    files = _request.get()
    if files is None:
        return Path(path).read_bytes()
    key = os.path.abspath(path)
    stat = os.stat(key)
    kept = files.get(key)
    if kept is not None and kept[0] == (stat.st_size, stat.st_mtime_ns):
        return kept[1]
    data = Path(path).read_bytes()
    files[key] = ((stat.st_size, stat.st_mtime_ns), data)
    return data


def read_text(path: Path | str, encoding: str = "utf-8") -> str:
    """As ``Path.read_text``: decoded, with ``\\r\\n`` and ``\\r`` read as ``\\n``."""
    if _request.get() is None:
        return Path(path).read_text(encoding=encoding)
    text = read_bytes(path).decode(encoding)
    return text.replace("\r\n", "\n").replace("\r", "\n") if "\r" in text else text


def signature(workspace: Path | str) -> tuple[tuple[str, int, int], ...]:
    """The name, size and modification time of every file the kept results may read."""
    root = os.path.abspath(workspace)
    found: list[tuple[str, int, int]] = []
    for directory, folders, files in os.walk(root):
        if directory == root:
            folders[:] = [f for f in folders if f not in NOT_READ]
        folders.sort()
        relative = os.path.relpath(directory, root)
        for name in sorted(files):
            try:
                stat = os.stat(os.path.join(directory, name))
            except OSError:
                continue
            found.append((name if relative == "." else f"{relative}/{name}", stat.st_size, stat.st_mtime_ns))
    return tuple(found)


def remember(workspace: Path | str, name: str, compute: Callable[[], T]) -> T:
    """``compute()``, kept between display calls while the workspace's files are unchanged.

    Outside a display call this is ``compute()``. The caller gets its own copy.
    """
    if _request.get() is None:
        return compute()
    key = os.path.abspath(workspace)
    before = signature(key)
    with _lock:
        kept = _kept.get(key, {}).get(name)
    if kept is not None and kept[0] == before:
        return copy.deepcopy(kept[1])
    value = compute()
    if signature(key) == before:
        with _lock:
            _kept.setdefault(key, {})[name] = (before, copy.deepcopy(value))
            _kept.move_to_end(key)
            while len(_kept) > MAX_WORKSPACES:
                _kept.popitem(last=False)
    return value


def clear() -> None:
    """Forget every kept result (tests; a workspace closed)."""
    with _lock:
        _kept.clear()
