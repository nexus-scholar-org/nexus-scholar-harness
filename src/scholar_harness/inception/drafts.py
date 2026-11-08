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
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DRAFTS_DIRNAME = ".drafts"
SESSION_ID_RE = re.compile(r"^rec_[0-9a-f]{6,64}$")


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

    def create(self, draft: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or new_session_id()
        if self._path(sid).exists():
            raise DraftRefused("DRAFT_EXISTS", f"a draft {sid} already exists")
        stamp = _now()
        return self._write({"session_id": sid, "created_at": stamp, "updated_at": stamp, "draft": draft, "emitted": None})

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

    def mark_emitted(self, session_id: str, result: dict[str, Any]) -> dict[str, Any]:
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
            })
        items.sort(key=lambda item: item["updated_at"], reverse=True)
        return items

    def discard(self, session_id: str) -> None:
        path = self._path(session_id)
        if not path.parent.is_dir():
            raise DraftRefused("DRAFT_NOT_FOUND", f"no draft {session_id}", status=404)
        shutil.rmtree(path.parent)
