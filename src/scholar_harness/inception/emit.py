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
)

#: The files a replacement backs up before it overwrites them.
REPLACED_FILES = ("protocol.json", "intent.json", "SCREENING_CRITERIA.md")


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
        return {"exists": False, "screening": None}
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
    return {"exists": True, "screening": state}


def _fingerprint_of(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


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
        }

    previous = _fingerprint_of(ws_dir / "protocol.json")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup = _backup(ws_dir, stamp)
    compiled = compile_protocol_files(ws_dir, intent)
    _refresh_manifest(ws_dir, intent)
    state = guard["screening"] or {}
    backup_rel = backup.relative_to(ws_dir).as_posix()
    note = (
        f" REPLACED protocol fingerprint {previous or 'none'} (backup at {backup_rel})"
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
    }
