"""The download manifest: one JSON line per DOI asked (Part K item 8, PDF-07, the kit's half).

The kit stores its files as ``DOC-<sha256>.pdf``; without a record nothing
downstream can tell which file is which DOI or study. The downloader writes a
row for every DOI it is asked, at the path its caller gives
(``AsyncPDFDownloader(manifest_path=...)``; ``download --manifest PATH``, or
``download-manifest.jsonl`` in the output folder). No file is kept without its
row: when the row cannot be written, a file the same call created is removed.

A row never holds a lookup request (they carry the contact e-mail and the
OpenAlex key), only what each service answered, in short. The legacy
``literature/pdf_manifest.json`` is not written.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .open_copies import FAILED, NOT_ASKED, not_asked_note

if TYPE_CHECKING:
    from .downloader import DownloadResult, FetchAttempt

#: The default file name, in the output folder of ``download`` and ``ingest``.
MANIFEST_NAME = "download-manifest.jsonl"
#: The row format; a change of a field's meaning changes it.
MANIFEST_SCHEMA = "scholar-pdf-download-manifest-v1"
#: The outcome of a DOI whose row could not be written (its new file was removed).
MANIFEST_NOT_WRITTEN = "MANIFEST_NOT_WRITTEN"


def _app_version() -> str:
    from scholar_search.http_client import package_version

    return package_version()


def _file_entry(file_path: Path | None, manifest_path: Path) -> str | None:
    """The file relative to the manifest's folder when it is inside it (POSIX), else absolute."""
    if file_path is None:
        return None
    try:
        return file_path.resolve().relative_to(manifest_path.resolve().parent).as_posix()
    except ValueError:
        return str(file_path.resolve())


def _request(attempt: FetchAttempt) -> dict[str, Any]:
    return {
        "url": attempt.url,
        "host": attempt.host,
        "retry": attempt.retry,
        "route": attempt.route,
        "http_status": attempt.http_status,
        "final_url": attempt.final_url,
        "redirects": list(attempt.redirects),
        "content_type": attempt.content_type,
        "error": attempt.error,
    }


def _producing_attempt(result: DownloadResult) -> FetchAttempt | None:
    """The request that gave the stored bytes: the last one to the chosen address."""
    if result.source_url is None:
        return None
    for attempt in reversed(result.attempts):
        if attempt.url == result.source_url and attempt.error is None:
            return attempt
    return None


def manifest_row(result: DownloadResult, manifest_path: Path) -> dict[str, Any]:
    """The row for one DOI, from its result."""
    producing = _producing_attempt(result)
    copy = result.open_copy
    checks: dict[str, str] = {}
    if producing is not None:
        checks = {check.name: "pass" if check.passed else "fail" for check in producing.checks}
    elif result.checks:
        checks = {check.name: "pass" if check.passed else "fail" for check in result.checks}
    if result.identity is not None:
        checks["identity"] = result.identity
    lookups = []
    for lookup in result.lookups:
        said = None
        if lookup.state == FAILED:
            said = f"{lookup.name} {lookup.failure()}"
        elif lookup.state == NOT_ASKED:
            said = not_asked_note(lookup)
        lookups.append(
            {
                "service": lookup.provider,
                "state": lookup.state,
                "http_status": lookup.http_status,
                "error": said,
            }
        )
    return {
        "schema": MANIFEST_SCHEMA,
        "doi": result.doi,
        "study_id": result.study_id,
        "outcome": result.outcome,
        "status": result.status,
        "message": result.error_message,
        "file": _file_entry(result.file_path, manifest_path),
        "size": result.size,
        "sha256": result.sha256,
        "address": result.source_url,
        "final_url": producing.final_url if producing else None,
        "redirects": list(producing.redirects) if producing else [],
        "http_status": producing.http_status if producing else None,
        "content_type": producing.content_type if producing else None,
        "version": copy.version if copy else None,
        "version_label": copy.version_label if copy else None,
        "license": copy.license if copy else None,
        "host_type": copy.host_type if copy else None,
        "source_name": copy.source_name if copy else None,
        "provider": copy.provider if copy else None,
        "route": result.route,
        "access_status": result.access_status,
        "checks": checks,
        "lookups": lookups,
        "copies_listed": result.copies_listed,
        "copies_tried": result.copies_tried,
        "request_count": result.request_count,
        "request_hosts": result.request_hosts(),
        "requests": [_request(attempt) for attempt in result.attempts],
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "app_version": _app_version(),
    }


def append_row(manifest_path: Path, row: dict[str, Any]) -> None:
    """Append one line and flush it to the disk; ``OSError`` when it cannot be written."""
    line = json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "a", encoding="utf-8", newline="\n") as stream:
        stream.write(line)
        stream.flush()
        os.fsync(stream.fileno())
