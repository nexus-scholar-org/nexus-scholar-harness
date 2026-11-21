"""Attaching the researcher's own PDF to a kept record (M12a DoD 7; record (d)).

The file is streamed to a staging file under ``pdfs/`` with a hard stop at
:data:`MAX_BYTES`, checked by its first bytes (a ``%PDF-`` header within the
first 1,024 bytes), hashed, and moved to ``pdfs/<study_id>.pdf``. Nothing is
fetched: no route here sends a request.

Nothing is deleted. A file replaced by a later attachment, or taken off by an
undo, moves to ``pdfs/replaced/<study_id>.<sha256[:16]>.pdf`` and comes back
when an undo restores it, so ``pdfs/<study_id>.pdf`` always holds the file the
study's current attachment event names.
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import ChartingRefused
from . import events as ev

MAX_BYTES = 100 * 1024 * 1024
HEADER_SCAN = 1024
PDFS_DIR = Path("pdfs")
REPLACED_DIR = PDFS_DIR / "replaced"
ATTACHMENT_NOT_PDF = "ATTACHMENT_NOT_PDF"
ATTACHMENT_TOO_LARGE = "ATTACHMENT_TOO_LARGE"
JOURNAL_ACTION = "CHARTING_ATTACHMENT_ADDED"
_SAFE_NAME = re.compile(r"[^\w .()+,-]+", re.UNICODE)
_SAFE_STUDY = re.compile(r"^[A-Za-z0-9_-]+$")


def _file_name(study_id: str) -> str:
    if not _SAFE_STUDY.match(study_id):
        raise ChartingRefused(422, ev.BODY_INVALID, "a study id is letters, digits, '-' and '_'")
    return f"{study_id}.pdf"


def attached_path(ws: Path, study_id: str) -> Path:
    return Path(ws) / PDFS_DIR / _file_name(study_id)


def _replaced_path(ws: Path, study_id: str, sha256: str) -> Path:
    return Path(ws) / REPLACED_DIR / f"{study_id}.{sha256[:16]}.pdf"


def display_name(raw: str | None) -> str:
    """The name the researcher's file had, kept for display only (never a path)."""
    name = (raw or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = _SAFE_NAME.sub("_", name).strip(" .")[:200]
    return name or "attachment.pdf"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Stager:
    """Write an upload to a staging file chunk by chunk; refuse a non-PDF or an oversize body."""

    def __init__(self, ws: Path, *, declared_size: int | None = None, limit: int | None = None) -> None:
        limit = MAX_BYTES if limit is None else limit
        if declared_size is not None and declared_size > limit:
            raise ChartingRefused(413, ATTACHMENT_TOO_LARGE, "That file is too large to keep in the workspace.",
                                  limit_bytes=limit)
        directory = Path(ws) / PDFS_DIR
        directory.mkdir(parents=True, exist_ok=True)
        self.limit = limit
        self.path = directory / f".attach-{uuid.uuid4().hex}.tmp"
        self.size, self._head, self._digest = 0, b"", hashlib.sha256()
        self._handle = self.path.open("wb")

    def write(self, chunk: bytes) -> None:
        if not chunk:
            return
        self.size += len(chunk)
        if self.size > self.limit:
            self.abort()
            raise ChartingRefused(413, ATTACHMENT_TOO_LARGE, "That file is too large to keep in the workspace.",
                                  limit_bytes=self.limit)
        if len(self._head) < HEADER_SCAN:
            self._head += chunk[: HEADER_SCAN - len(self._head)]
        self._digest.update(chunk)
        self._handle.write(chunk)

    def finish(self) -> tuple[Path, int, str]:
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()
        if b"%PDF-" not in self._head:
            self.abort()
            raise ChartingRefused(422, ATTACHMENT_NOT_PDF, "Only a PDF can be attached. Paste a link instead.")
        return self.path, self.size, self._digest.hexdigest()

    def abort(self) -> None:
        if not self._handle.closed:
            self._handle.close()
        self.path.unlink(missing_ok=True)


def stage(ws: Path, chunks: Iterable[bytes], *, declared_size: int | None = None, limit: int | None = None) -> tuple[Path, int, str]:
    """Stage a whole body (tests and callers that hold the bytes)."""
    stager = Stager(ws, declared_size=declared_size, limit=limit)
    try:
        for chunk in chunks:
            stager.write(chunk)
    except BaseException:
        stager.abort()
        raise
    return stager.finish()


def _park(ws: Path, study_id: str, path: Path) -> None:
    """Move the file at ``pdfs/<study_id>.pdf`` aside under its own hash (never delete)."""
    if not path.is_file():
        return
    target = _replaced_path(ws, study_id, _sha256(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        path.unlink()  # the same bytes are already kept aside
    else:
        os.replace(path, target)


def place(ws: Path, study_id: str, staging: Path, sha256: str) -> None:
    """Make the staged file the study's attached file, keeping any earlier one aside."""
    final = attached_path(ws, study_id)
    if final.is_file() and _sha256(final) == sha256:
        staging.unlink(missing_ok=True)
        return
    _park(ws, study_id, final)
    os.replace(staging, final)


def sync_file(ws: Path, study_id: str, value: dict[str, Any] | None) -> None:
    """After an undo or a restore: ``pdfs/<study_id>.pdf`` holds what the current attachment names."""
    final = attached_path(ws, study_id)
    if value is None:
        _park(ws, study_id, final)
        return
    want = str(value.get("sha256") or "")
    if final.is_file() and _sha256(final) == want:
        return
    kept = _replaced_path(ws, study_id, want)
    if kept.is_file():
        _park(ws, study_id, final)
        os.replace(kept, final)


def serve_path(ws: Path, study_id: str, value: dict[str, Any] | None) -> Path | None:
    """The file to serve for the current attachment, or None when there is none on disk."""
    if value is None:
        return None
    final = attached_path(ws, study_id)
    want = str(value.get("sha256") or "")
    if final.is_file() and final.stat().st_size == int(value.get("size") or -1) and _sha256(final) == want:
        return final
    kept = _replaced_path(ws, study_id, str(value.get("sha256") or ""))
    return kept if kept.is_file() else None
