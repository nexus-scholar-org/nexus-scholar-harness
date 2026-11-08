"""Atomic file writes, tolerant of transient Windows holds (M6-hardening H1/H2).

``atomic_write_text`` writes a sibling temporary file, flushes it to disk and
replaces the target, so a crash leaves either the old file or the new one,
never a torn mix, and never a stray temporary file once the call returns.

The bytes are exactly what ``Path.write_text(text, encoding="utf-8")`` writes
(text mode, default newline translation), so digests computed over those bytes
elsewhere (``authority.generations.publication_file_bytes``) do not move.

On Windows a file another process holds open (an antivirus scan, the search
indexer, a reader) makes ``os.replace`` raise ``PermissionError`` for a moment.
``replace_with_retry`` retries that case there only, with a short backoff; on
other systems a ``PermissionError`` is a real permission problem and is raised
at once.
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

_IS_WINDOWS = os.name == "nt"
#: Attempts and base delay: at most ~1.1 s of waiting in total.
REPLACE_ATTEMPTS = 8
REPLACE_DELAY_S = 0.04


def replace_with_retry(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
    """``os.replace``, retrying a transient ``PermissionError`` on Windows."""
    for attempt in range(1, REPLACE_ATTEMPTS + 1):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if not _IS_WINDOWS or attempt == REPLACE_ATTEMPTS:
                raise
            time.sleep(REPLACE_DELAY_S * attempt)


def atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` (UTF-8) to ``path`` atomically; parents are created."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{uuid.uuid4().hex[:8]}")
    try:
        with tmp.open("w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        replace_with_retry(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
