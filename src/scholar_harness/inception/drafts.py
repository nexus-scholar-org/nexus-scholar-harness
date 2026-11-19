"""Inception draft sessions (M4a; screens 00 and 08, UX finding #10).

A draft is the researcher's unfinished interview, saved so the web wizard can
resume it. It lives at ``<workspaces root>/.drafts/<session id>/draft.json``
(decision 2026-11-08, inception drafts): it is the researcher's work, not a
cache, and the workspace list skips dot-folders.

One session id names a draft and its recon session: ``rec_`` plus 32 lowercase
hex digits, the format the MCP recon tools already use. The grounded CLI wizard
mints its session id here too.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DRAFTS_DIRNAME = ".drafts"
SESSION_ID_RE = re.compile(r"^rec_[0-9a-f]{6,64}$")


#: One lock per draft file (M10b, ``01-proposals`` "Where a proposal is kept").
#: FastAPI runs the sync routes in threads, and every write here is load then
#: write of the whole record: without a lock a side write (an origin mark, a
#: check dismissal) racing a save would write the old ``draft`` back.
_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


def _thread_lock(path: Path) -> threading.RLock:
    # Always the absolute path, so one file has one key before and after it exists.
    # One lock per draft ever touched in this process: a small, bounded-by-use map.
    key = str(path.absolute())
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.RLock())


#: How deep this process holds each draft's OS lock (guarded by the draft's thread lock).
_DEPTH: dict[str, int] = {}


@contextmanager
def _lock_for(path: Path) -> Iterator[None]:
    """The draft's thread lock and, once per process, its OS lock (M10c, decision item 10).

    The MCP server writes the same record from a second process, so the
    thread lock alone cannot keep a read-then-write whole. The OS lock is a
    file in ``.drafts/.locks/`` (outside the draft's folder, which a discard
    removes); it is taken once per process and re-entered by depth.
    """
    lock = _thread_lock(path)
    with lock:
        key = str(path.absolute())
        if _DEPTH.get(key, 0):
            _DEPTH[key] += 1
            try:
                yield
            finally:
                _DEPTH[key] -= 1
            return
        lock_path = path.parent.parent / ".locks" / f"{path.parent.name}.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as handle:
            _os_lock(handle)
            _DEPTH[key] = 1
            try:
                yield
            finally:
                _DEPTH[key] = 0
                _os_unlock(handle)


def _os_lock(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        while True:  # LK_LOCK gives up after ten one-second retries; a held draft lock is short
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError:
                continue
    import fcntl

    fcntl.flock(handle, fcntl.LOCK_EX)


def _os_unlock(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(handle, fcntl.LOCK_UN)


def new_session_id() -> str:
    """The one session-id format shared by the wizard, the drafts and MCP recon."""
    return "rec_" + uuid.uuid4().hex


def _now() -> str:
    return datetime.now(UTC).isoformat()


class DraftRefused(Exception):
    """A draft operation was refused; ``code`` names why, ``status`` is the HTTP status."""

    def __init__(self, code: str, message: str, status: int = 409, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


class DraftStore:
    """Drafts under one workspaces root."""

    def __init__(self, workspaces_root: Path):
        self.root = Path(workspaces_root)
        self.dir = self.root / DRAFTS_DIRNAME

    def _path(self, session_id: str) -> Path:
        if not isinstance(session_id, str) or SESSION_ID_RE.fullmatch(session_id) is None:
            raise DraftRefused("DRAFT_ID_INVALID", "a draft id is 'rec_' followed by hex digits", status=422)
        return self.dir / session_id / "draft.json"

    def _write(self, record: dict[str, Any]) -> dict[str, Any]:
        path = self._path(record["session_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
        return record

    def create(
        self, draft: dict[str, Any], session_id: str | None = None, *, extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """A new draft record; ``extra`` holds side keys written with it (an import's ``origin``, M10b)."""
        sid = session_id or new_session_id()
        with _lock_for(self._path(sid)):
            if self._path(sid).exists():
                raise DraftRefused("DRAFT_EXISTS", f"a draft {sid} already exists")
            stamp = _now()
            record = {"session_id": sid, "created_at": stamp, "updated_at": stamp, "draft": draft, "emitted": None}
            record.update(extra or {})
            return self._write(record)

    def update_side(self, session_id: str, key: str, change: Callable[[Any], Any]) -> dict[str, Any]:
        """Change one side key of the record, not the draft (M10b).

        Re-reads the record under the draft's lock and writes ``change(current)``
        to ``key`` only; ``updated_at`` does not change, so another tab's
        ``base_updated_at`` stays valid and a save made in between is kept.
        Nothing is changed on an emitted draft: the record is answered as it is.
        """
        with _lock_for(self._path(session_id)):
            record = self.load(session_id)
            if record.get("emitted"):
                return record
            record[key] = change(record.get(key))
            return self._write(record)

    def transact(
        self,
        session_id: str,
        change: Callable[[dict[str, Any]], Any],
        *,
        answer: bool,
        base_updated_at: str | None = None,
    ) -> tuple[dict[str, Any], Any]:
        """One write of the record under the draft's lock (M10b, ``01-proposals``).

        ``change(record)`` edits the record in place and returns what the route
        answers. An *answer* write (it changes ``draft`` or what the answers rest
        on) checks ``base_updated_at`` (``DRAFT_CONFLICT``) and sets a new
        ``updated_at``; a *side* write does neither, so another tab's next save
        is not refused. Both refuse ``DRAFT_EMITTED``. A ``change`` that raises
        writes nothing.
        """
        with _lock_for(self._path(session_id)):
            record = self.load(session_id)
            if answer and base_updated_at is not None and base_updated_at != record["updated_at"]:
                raise DraftRefused(
                    "DRAFT_CONFLICT", "the draft changed since it was read; reload it",
                    details={"updated_at": record["updated_at"]},
                )
            if record.get("emitted"):
                raise DraftRefused(
                    "DRAFT_EMITTED", "this draft already created a workspace", details={"emitted": record["emitted"]},
                )
            result = change(record)
            if answer:
                record["updated_at"] = _now()
            self._write(record)
            return record, result

    def load(self, session_id: str) -> dict[str, Any]:
        path = self._path(session_id)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DraftRefused("DRAFT_NOT_FOUND", f"no draft {session_id}", status=404) from exc
        except (OSError, ValueError) as exc:
            raise DraftRefused("DRAFT_UNREADABLE", f"draft {session_id} cannot be read: {exc}", status=500) from exc

    def save(self, session_id: str, draft: dict[str, Any], base_updated_at: str | None = None) -> dict[str, Any]:
        """Replace the draft; ``base_updated_at`` refuses a save over a newer one."""
        with _lock_for(self._path(session_id)):
            return self._save(session_id, draft, base_updated_at)

    def _save(self, session_id: str, draft: dict[str, Any], base_updated_at: str | None) -> dict[str, Any]:
        record = self.load(session_id)
        if base_updated_at is not None and base_updated_at != record["updated_at"]:
            raise DraftRefused(
                "DRAFT_CONFLICT", "the draft changed since it was read; reload it",
                details={"updated_at": record["updated_at"]},
            )
        if record.get("emitted"):
            raise DraftRefused("DRAFT_EMITTED", "this draft already created a workspace", details={"emitted": record["emitted"]})
        record["draft"] = draft
        record["updated_at"] = _now()
        return self._write(record)

    def bind_grounding(
        self,
        session_id: str,
        grounding: dict[str, Any],
        base_updated_at: str | None = None,
        *,
        record_change: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Write the grounded evidence of a chosen direction beside the draft (M4c).

        Only the recon bind route calls this; a ``save`` of the draft keeps it.
        ``record_change`` adds to the same write (M10b: the ``engine:direction`` record).
        """
        with _lock_for(self._path(session_id)):
            return self._bind(session_id, grounding, base_updated_at, record_change)

    def _bind(
        self, session_id: str, grounding: dict[str, Any], base_updated_at: str | None,
        record_change: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        record = self.load(session_id)
        if base_updated_at is not None and base_updated_at != record["updated_at"]:
            raise DraftRefused(
                "DRAFT_CONFLICT", "the draft changed since it was read; reload it",
                details={"updated_at": record["updated_at"]},
            )
        if record.get("emitted"):
            raise DraftRefused("DRAFT_EMITTED", "this draft already created a workspace", details={"emitted": record["emitted"]})
        record["grounding"] = grounding
        if record_change is not None:
            record_change(record)
        record["updated_at"] = _now()
        return self._write(record)

    def mark_emitted(self, session_id: str, result: dict[str, Any]) -> dict[str, Any]:
        with _lock_for(self._path(session_id)):
            record = self.load(session_id)
            record["emitted"] = {**result, "at": _now()}
            record["updated_at"] = record["emitted"]["at"]
            return self._write(record)

    def listing(self) -> list[dict[str, Any]]:
        """Newest first; unreadable drafts are listed with ``readable: false``, never hidden."""
        items = []
        if not self.dir.is_dir():
            return items
        for child in self.dir.iterdir():
            if not child.is_dir() or SESSION_ID_RE.fullmatch(child.name) is None:
                continue
            try:
                record = self.load(child.name)
            except DraftRefused:
                items.append({"session_id": child.name, "readable": False, "updated_at": ""})
                continue
            draft = record.get("draft") or {}
            items.append({
                "session_id": record["session_id"],
                "readable": True,
                "title": draft.get("title") or "",
                "topic": draft.get("topic") or "",
                "created_at": record["created_at"],
                "updated_at": record["updated_at"],
                "emitted": record.get("emitted"),
                # M10b (09-start-from-protocol): the start screen says "Started from {label}".
                "origin_label": ((record.get("origin") or {}).get("source") or {}).get("label"),
            })
        items.sort(key=lambda item: item["updated_at"], reverse=True)
        return items

    def discard(self, session_id: str) -> None:
        path = self._path(session_id)
        if not path.parent.is_dir():
            raise DraftRefused("DRAFT_NOT_FOUND", f"no draft {session_id}", status=404)
        shutil.rmtree(path.parent)
