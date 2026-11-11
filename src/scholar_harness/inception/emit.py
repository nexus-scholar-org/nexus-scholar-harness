"""The one gated genesis path (M4a; INC-08).

Every way of writing an inception protocol into a folder goes through
:func:`emit_workspace`: the CLI wizard (`scholar-harness inception`,
`nexus-scholar init`) and the inception HTTP route. Nothing else writes
`protocol.json`, `intent.json` or `SCREENING_CRITERIA.md` from an interview.

The overwrite guard (decision 2026-11-08, re-inception):

* a folder that already holds a workspace (any :data:`INIT_MARKERS` file) is
  refused with ``WORKSPACE_EXISTS`` unless ``replace`` is set;
* with ``replace``, a workspace that has screening decisions or a published
  screening is refused with ``SCREENING_BOUND`` (the counts are in
  ``details``) unless ``discard_screening_binding`` is also set;
* a replacement backs the old protocol files up under
  ``audit/replaced/<UTC stamp>/``, keeps ``project.json`` (its ``created_at``,
  ``stats`` and identity; only the title, paradigm and research questions are
  refreshed), and logs GENESIS naming the old fingerprint and the backup.

The intent is compiled before any write, so an invalid intent writes nothing.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .genesis import (
    INIT_MARKERS,
    compile_intent,
    compile_protocol_files,
    log_genesis,
    scaffold_project,
    scaffold_raw_project,
    write_review_notes,
)

#: The files a replacement backs up before it overwrites them.
REPLACED_FILES = ("protocol.json", "intent.json", "SCREENING_CRITERIA.md")

#: What belongs to a protocol's corpus and is archived beside it when the
#: protocol is replaced (F1, decision 2026-11-11): the search runs, the
#: accepted corpus and its registry, the screening decisions, the console's
#: jobs and everything built from the corpus. Directories end in ``/``.
ARCHIVED_ON_REPLACE = (
    "literature/",
    "artifacts/",
    "audit/artifact_registry.json",
    ".harness-console/",
    "pdfs/",
    "extracted/",
    "rag/",
    "phase4/",
    "synthesis/",
    "chroma_db/",
    "run-reports/",
)
#: The canonical folders a workspace starts with, made again after an archive.
CANONICAL_DIRS = ("literature", "pdfs", "extracted", "synthesis")
#: Kept in place: the researcher's own review notes, which every workspace starts with.
KEPT_ON_REPLACE = ("synthesis/literature_review.md",)


def _corpus_files(ws_dir: Path, rel: str) -> list[Path]:
    """The files under one :data:`ARCHIVED_ON_REPLACE` entry, without the kept ones."""
    path = Path(ws_dir) / rel.rstrip("/")
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()] if path.is_dir() else []
    return [f for f in files if f.relative_to(ws_dir).as_posix() not in KEPT_ON_REPLACE]

#: What :func:`emit_workspace` writes into a new folder (``target_dir`` layout).
#: The review screen shows this list at the write gate (M4b, researcher
#: 2026-11-09); ``test_preview_names_every_file_genesis_writes`` keeps it exact.
NEW_WORKSPACE_FILES = (
    "project.json",
    "intent.json",
    "protocol.json",
    "SCREENING_CRITERIA.md",
    "INDEX.md",
    "audit/journal.jsonl",
    "synthesis/literature_review.md",
)

#: What a replacement writes or rewrites: the protocol files, the refreshed
#: manifest and index, the journal, and one backup folder. A partial workspace
#: (only some markers present) may lack `project.json`, which is then not
#: refreshed: the list can over-promise there, never under-promise.
REPLACEMENT_FILES = (
    "intent.json",
    "protocol.json",
    "SCREENING_CRITERIA.md",
    "project.json",
    "INDEX.md",
    "audit/journal.jsonl",
    "audit/replaced/<UTC stamp>/",
)


class GenesisRefused(Exception):
    """The gated genesis path refused to write; ``code`` names why."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details or {}


def workspace_dir_for(slug: str, *, root: Path | None = None, target_dir: Path | None = None) -> Path:
    """Where genesis writes: ``target_dir`` itself, else ``root/workspaces/<slug>``."""
    if target_dir is not None:
        return Path(target_dir).resolve()
    if root is None:
        raise ValueError("root or target_dir is required")
    return Path(root).resolve() / "workspaces" / slug


def existing_markers(ws_dir: Path) -> list[str]:
    """The :data:`INIT_MARKERS` already present (a file at ``ws_dir`` counts as one)."""
    ws_dir = Path(ws_dir)
    if ws_dir.is_file():
        return [ws_dir.name]
    if not ws_dir.is_dir():
        return []
    return [marker for marker in INIT_MARKERS if (ws_dir / marker).exists()]


def corpus_paths(ws_dir: Path) -> list[str]:
    """The :data:`ARCHIVED_ON_REPLACE` paths that hold something (an empty folder is left alone)."""
    return [rel for rel in ARCHIVED_ON_REPLACE if _corpus_files(ws_dir, rel)]


def _archive_corpus(ws_dir: Path, backup: Path) -> list[str]:
    """Move the old protocol's corpus into ``backup``; make the empty canonical folders again.

    A move that fails part way (a locked file, a full disk) is journaled with
    what was already moved and refused as ``ARCHIVE_INCOMPLETE``, so the
    record says where every path is; nothing is moved back.
    """
    planned = corpus_paths(ws_dir)
    moved: list[str] = []
    try:
        _move_corpus(ws_dir, backup, planned, moved)
    except OSError as exc:
        backup_rel = backup.relative_to(ws_dir).as_posix()
        left = [rel for rel in planned if rel not in moved]
        description = (
            f"Protocol replacement stopped while archiving the old corpus into {backup_rel}: "
            f"{type(exc).__name__}: {str(exc)[:200]}. Moved: {', '.join(moved) or 'nothing'}. "
            f"Not moved: {', '.join(left)}. The protocol was not replaced."
        )
        try:
            from scholar_harness.workspace.audit import append_event

            append_event(
                ws_dir, "PROTOCOL_REPLACE_INCOMPLETE", description, agent="scholar-harness/inception",
                outputs=[f"{backup_rel}/{rel}" for rel in moved], status="FAILED",
            )
        except OSError:
            pass  # the refusal below still names every path
        raise GenesisRefused(
            "ARCHIVE_INCOMPLETE", description,
            {"backup_dir": str(backup), "moved": moved, "not_moved": left},
        ) from exc
    for sub in CANONICAL_DIRS:
        (ws_dir / sub).mkdir(parents=True, exist_ok=True)
    return moved


def _move_corpus(ws_dir: Path, backup: Path, planned: list[str], moved: list[str]) -> None:
    for rel in planned:
        source = ws_dir / rel.rstrip("/")
        kept = [ws_dir / k for k in KEPT_ON_REPLACE if (ws_dir / k).is_file() and (ws_dir / k).is_relative_to(source)]
        if kept:  # move what is not kept, file by file
            for path in _corpus_files(ws_dir, rel):
                dest = backup / path.relative_to(ws_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(dest))
            moved.append(rel)
            continue
        dest = backup / rel.rstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        moved.append(rel)


def screening_state(ws_dir: Path) -> dict[str, int | bool]:
    """What a protocol replacement would orphan: decisions and a publication."""
    screening = Path(ws_dir) / "literature" / "screening"
    events = 0
    for path in sorted((screening / "events").glob("*.jsonl")):
        try:
            events += sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except OSError:
            events += 1  # unreadable still counts as present
    batch_files = len(list(screening.glob("batch_[0-9][0-9][0-9]_decisions.json")))
    published = (screening / "generation.json").is_file()
    return {
        "decision_events": events,
        "decision_files": batch_files,
        "published": published,
        "bound": bool(events or batch_files or published),
    }


def check_writable(
    ws_dir: Path, *, replace: bool = False, discard_screening_binding: bool = False
) -> dict[str, Any]:
    """The overwrite guard alone, with no write: raises :class:`GenesisRefused` or
    returns ``{"exists": bool, "screening": {...} | None}``."""
    ws_dir = Path(ws_dir)
    if ws_dir.is_file():
        raise GenesisRefused("WORKSPACE_EXISTS", f"{ws_dir} is a file, not a folder", {"path": str(ws_dir)})
    present = existing_markers(ws_dir)
    if not present:
        return {"exists": False, "screening": None, "archive": []}
    if not replace:
        raise GenesisRefused(
            "WORKSPACE_EXISTS",
            f"{ws_dir} already holds a Nexus Scholar workspace ({', '.join(present)}); "
            "re-run with --replace to replace its protocol (the old one is backed up)",
            {"path": str(ws_dir), "markers": present},
        )
    state = screening_state(ws_dir)
    if state["bound"] and not discard_screening_binding:
        raise GenesisRefused(
            "SCREENING_BOUND",
            f"{ws_dir} has {state['decision_events']} screening decision events, "
            f"{state['decision_files']} batch decision files and "
            f"{'a' if state['published'] else 'no'} published screening, all made under the current "
            "protocol; replacing it leaves them pointing at criteria that no longer exist. "
            "Add --discard-screening-binding to replace it anyway",
            {"path": str(ws_dir), **state},
        )
    return {"exists": True, "screening": state, "archive": corpus_paths(ws_dir)}


def _fingerprint_of(path: Path) -> str | None:
    """The protocol fingerprint the screening bindings carry (``canonical_fingerprint``).

    A file that does not validate as a protocol gets a byte hash, labelled
    ``file-sha256:`` so it is never mistaken for a protocol fingerprint.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    try:
        from scholar_protocol.canonical import canonical_fingerprint
        from scholar_protocol.models import ResearchProtocol

        return canonical_fingerprint(ResearchProtocol.model_validate(json.loads(raw)))
    except Exception:  # noqa: BLE001 - anything unreadable as a protocol is hashed as bytes
        return "file-sha256:" + hashlib.sha256(raw).hexdigest()


def _backup(ws_dir: Path, stamp: str) -> Path:
    backup = ws_dir / "audit" / "replaced" / stamp
    n = 1
    while backup.exists():  # two replacements in one second
        n += 1
        backup = ws_dir / "audit" / "replaced" / f"{stamp}-{n}"
    backup.mkdir(parents=True)
    for name in REPLACED_FILES:
        if (ws_dir / name).is_file():
            shutil.copy2(ws_dir / name, backup / name)
    return backup


def _refresh_manifest(ws_dir: Path, intent: dict) -> None:
    """Keep `project.json`; refresh only what the new protocol states."""
    path = ws_dir / "project.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    manifest["title"] = intent["title"]
    manifest["paradigm"] = intent["primary_paradigm"]
    manifest["research_questions"] = [rq["text"] for rq in intent["research_questions"]]
    manifest["updated_at"] = datetime.now(UTC).isoformat()
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def emit_workspace(
    intent: dict,
    *,
    root: Path | None = None,
    target_dir: Path | None = None,
    replace: bool = False,
    discard_screening_binding: bool = False,
    recon_context: dict | None = None,
    agent: str = "scholar-harness/inception",
    description: str | None = None,
    fingerprint_label: str = "protocol",
) -> dict[str, Any]:
    """Write ``intent`` as a workspace's protocol through the overwrite guard.

    ``target_dir`` writes into that folder (``nexus-scholar init``, the HTTP
    route); otherwise the workspace is ``root/workspaces/<slug>``. Returns
    ``workspace_dir``, ``protocol_fingerprint``, ``replaced`` and, for a
    replacement, ``previous_fingerprint`` and ``backup_dir``.
    """
    slug = intent["project_slug"]
    ws_dir = workspace_dir_for(slug, root=root, target_dir=target_dir)
    guard = check_writable(ws_dir, replace=replace, discard_screening_binding=discard_screening_binding)
    compile_intent(intent)  # validate before any write
    title, paradigm = intent["title"], intent["primary_paradigm"]
    rqs = [rq["text"] for rq in intent["research_questions"]]
    summary = description or f"Phase-0 Inception: '{title}' [{paradigm}, {intent['playbook_type']}]"

    if not guard["exists"]:
        if target_dir is not None:
            scaffold_raw_project(ws_dir, title, slug, paradigm, rqs)
        else:
            scaffold_project(Path(root), title, slug, paradigm, rqs)
        compiled = compile_protocol_files(ws_dir, intent)
        log_genesis(
            ws_dir,
            f"{summary} compiled {fingerprint_label} fingerprint {compiled['protocol_fingerprint']}",
            recon_context=recon_context,
            agent=agent,
        )
        return {
            "workspace_dir": str(ws_dir),
            "protocol_fingerprint": compiled["protocol_fingerprint"],
            "replaced": False,
            "archived": [],
        }

    previous = _fingerprint_of(ws_dir / "protocol.json")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup = _backup(ws_dir, stamp)
    archived = _archive_corpus(ws_dir, backup)
    compiled = compile_protocol_files(ws_dir, intent)
    _refresh_manifest(ws_dir, intent)
    write_review_notes(ws_dir, title, rqs)
    state = guard["screening"] or {}
    backup_rel = backup.relative_to(ws_dir).as_posix()
    note = (
        f" REPLACED protocol fingerprint {previous or 'none'} (backup at {backup_rel})"
    )
    if archived:
        note += (
            f"; the old protocol's corpus was archived with it ({', '.join(archived)}), "
            "so the new protocol starts with no corpus and no screening decisions"
        )
    if state.get("bound"):
        note += (
            f"; screening binding discarded by the researcher: {state['decision_events']} screening decision events, "
            f"{state['decision_files']} batch decision files, published={state['published']}"
        )
    log_genesis(
        ws_dir,
        f"{summary} compiled {fingerprint_label} fingerprint {compiled['protocol_fingerprint']}.{note}",
        recon_context=recon_context,
        agent=agent,
    )
    return {
        "workspace_dir": str(ws_dir),
        "protocol_fingerprint": compiled["protocol_fingerprint"],
        "replaced": True,
        "previous_fingerprint": previous,
        "backup_dir": str(backup),
        "archived": archived,
    }
