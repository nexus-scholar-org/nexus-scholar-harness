"""The workspaces under one root (M5-slim; `docs/architecture/workspaces-api.md`).

The packaged app serves one workspace at a time. This module lists the
workspaces under a root, creates one there (the `nexus-scholar init
--scaffold-only` scaffold), and checks a workspace before the launcher restarts
the server on it. It reads files only; it never holds a workspace open.

- **The root** is `--root`, else `NEXUS_WORKSPACES_ROOT`, else
  `~/Documents/Nexus Scholar/workspaces` (`resolve_root`).
- **A workspace** is a direct child of the root holding `protocol.json`,
  `project.json` and `audit/journal.jsonl`; support files are not required.
- **Busy:** an agent run live in this engine, or a staged approval pairing.
  Opening another workspace restarts the server, which would end either.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

ROOT_ENV = "NEXUS_WORKSPACES_ROOT"
DEFAULT_ROOT = Path("~") / "Documents" / "Nexus Scholar" / "workspaces"
MARKERS = ("protocol.json", "project.json", "audit/journal.jsonl")
UI_AGENT = "nexus-scholar/ui"


class WorkspaceRefused(Exception):
    def __init__(self, code: str, message: str, status: int = 409, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


def resolve_root(flag: Path | None = None, env: dict[str, str] | None = None) -> tuple[Path, str]:
    """The workspaces root and where it came from: `flag`, `environment` or `default`."""
    env = os.environ if env is None else env
    if flag is not None:
        return Path(flag).expanduser().resolve(), "flag"
    if env.get(ROOT_ENV):
        return Path(env[ROOT_ENV]).expanduser().resolve(), "environment"
    return DEFAULT_ROOT.expanduser().resolve(), "default"


def _writable(path: Path) -> bool:
    return path.is_dir() and os.access(path, os.W_OK)


def validity(folder: Path) -> tuple[bool, str | None]:
    """Whether `folder` is a workspace; the reason when it is not."""
    try:
        missing = [m for m in MARKERS if not (folder / m).is_file()]
    except OSError:
        return False, "unreadable"
    return (not missing, f"missing {', '.join(missing)}" if missing else None)


def _last_event(ws: Path) -> dict[str, Any] | None:
    journal = ws / "audit" / "journal.jsonl"
    try:
        with journal.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - 65536))
            lines = [line for line in handle.read().splitlines() if line.strip()]
        row = json.loads(lines[-1]) if lines else None
    except (OSError, ValueError):
        return None
    return {"at": row.get("timestamp"), "action": row.get("action")} if isinstance(row, dict) else None


def _has_corpus(ws: Path) -> bool:
    try:
        registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return any(e.get("artifact_type") == "corpus_snapshot" for e in (registry.get("artifacts") or {}).values())


def _screening_started(ws: Path) -> bool:
    from scholar_harness.screening.events import EVENTS_DIR

    folder = ws / EVENTS_DIR
    return folder.is_dir() and any(p.stat().st_size > 0 for p in folder.glob("*.jsonl"))


def _status(ws: Path, has_corpus: bool) -> str:
    """Where the screening stands (M6-beta, review U-3), most advanced first.

    PUBLISHED: a generation is published and still current. PUBLISHED_CHANGED:
    a generation is published but no longer current (a decision since).
    SCREENING: batches are prepared. CORPUS_ACCEPTED, NEW: before that.
    """
    screening = ws / "literature" / "screening"
    if (screening / "generation.json").is_file():
        from scholar_harness.authority.generations import GenerationStatus
        from scholar_harness.screening.currentness import screening_currentness

        current = screening_currentness(ws).status is GenerationStatus.CURRENT
        return "PUBLISHED" if current else "PUBLISHED_CHANGED"
    if screening.is_dir() and any(screening.glob("batch_[0-9][0-9][0-9].json")):
        return "SCREENING"
    return "CORPUS_ACCEPTED" if has_corpus else "NEW"


def _title(ws: Path) -> str | None:
    try:
        return json.loads((ws / "project.json").read_text(encoding="utf-8")).get("title")
    except (OSError, ValueError, AttributeError):
        return None


def describe(folder: Path, current: Path | None) -> dict[str, Any]:
    valid, reason = validity(folder)
    item: dict[str, Any] = {
        "slug": folder.name,
        "title": _title(folder) if valid else None,
        "path": str(folder),
        "valid": valid,
        "is_current": current is not None and folder.resolve() == current.resolve(),
    }
    if not valid:
        item["invalid_reason"] = reason
        return item
    has_corpus = _has_corpus(folder)
    item.update(
        has_corpus=has_corpus,
        screening_started=_screening_started(folder),
        status=_status(folder, has_corpus),
        last_event=_last_event(folder),
    )
    return item


def most_recent(root: Path) -> Path | None:
    """The valid workspace under the root with the latest journal row, if any."""
    if not root.is_dir():
        return None
    ranked = [((d["last_event"] or {}).get("at") or "", c) for c in _children(root) if (d := describe(c, None))["valid"]]
    return max(ranked)[1] if ranked else None


def busy(ws: Path) -> dict[str, bool]:
    """What a restart onto another workspace would end."""
    from scholar_harness.authority import pairing
    from scholar_harness.screening import agent_runs

    holder = agent_runs.active_run(ws)
    run_active = bool(holder) and agent_runs._live(ws, holder) is not None
    pairing_open = False
    screening = ws / "literature" / "screening"
    for batch in sorted(screening.glob("batch_[0-9][0-9][0-9].json")) if screening.is_dir() else []:
        if pairing.pairing_status(ws, int(batch.stem.split("_")[1]))["state"] == pairing.PAIRING_STATE_STAGED:
            pairing_open = True
            break
    return {"run_active": run_active, "pairing_open": pairing_open}


def _children(root: Path) -> list[Path]:
    """Direct child folders of the root, never a symlink out of it."""
    out = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        try:
            if child.name.startswith(".") or not child.is_dir():
                continue
            if not child.resolve().is_relative_to(root):
                continue
        except OSError:
            continue
        out.append(child)
    return out


def listing(root: Path, source: str, current: Path | None, *, include_invalid: bool = False) -> dict[str, Any]:
    if not root.is_dir():
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise WorkspaceRefused("WORKSPACE_ROOT_UNAVAILABLE", f"the workspaces folder cannot be created: {root} ({exc})") from exc
    try:
        children = _children(root)
    except OSError as exc:
        raise WorkspaceRefused("WORKSPACE_ROOT_UNAVAILABLE", f"the workspaces folder cannot be read: {root} ({exc})") from exc
    described = [describe(child, current) for child in children]
    valid = [d for d in described if d["valid"]]
    invalid = [d for d in described if not d["valid"]]
    current_item = next((d for d in valid if d["is_current"]), None)
    if current_item is None and current is not None and validity(current)[0]:
        # `--workspace` may open a folder outside the root; it is still the current row.
        current_item = describe(current, current)
        valid.insert(0, current_item)
    return {
        "root": str(root),
        "root_source": source,
        "writable": _writable(root),
        "current": {"slug": current.name, "path": str(current)} if current is not None else None,
        "busy": busy(current) if current is not None else {"run_active": False, "pairing_open": False},
        "skipped_count": len(invalid),
        "items": valid + (invalid if include_invalid else []),
    }


def _target(root: Path, slug: str) -> Path:
    if not slug or slug in (".", "..") or slug.startswith(".") or any(sep in slug for sep in ("/", "\\", ":")):
        raise WorkspaceRefused("WORKSPACE_PATH_REFUSED", "that folder is outside the workspaces folder", status=422)
    target = root / slug
    try:
        resolved = target.resolve()
    except OSError as exc:
        raise WorkspaceRefused("WORKSPACE_PATH_REFUSED", "that folder is outside the workspaces folder", status=422) from exc
    if resolved.parent != root.resolve():
        raise WorkspaceRefused("WORKSPACE_PATH_REFUSED", "that folder is outside the workspaces folder", status=422)
    return resolved


def create(root: Path, title: str) -> dict[str, Any]:
    """Create `{root}/{slug}` as `nexus-scholar init --scaffold-only` would; nothing is left on failure."""
    from scholar_harness.inception.genesis import WorkspaceScaffoldRefused, scaffold_placeholder_workspace
    from scholar_harness.inception.intent import slugify

    slug = slugify(title or "")
    if not slug:
        raise WorkspaceRefused("WORKSPACE_TITLE_INVALID", "the title has no letters or digits to make a folder name from", status=422)
    if not _writable(root):
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise WorkspaceRefused("WORKSPACE_ROOT_UNAVAILABLE", f"the workspaces folder cannot be written: {root}") from exc
        if not _writable(root):
            raise WorkspaceRefused("WORKSPACE_ROOT_UNAVAILABLE", f"the workspaces folder cannot be written: {root}")
    target = _target(root, slug)
    if target.exists():
        raise WorkspaceRefused("WORKSPACE_EXISTS", f"a workspace for this title already exists at {target}", details={"path": str(target)})
    try:
        result = scaffold_placeholder_workspace(target, title, agent=UI_AGENT)
    except WorkspaceScaffoldRefused as exc:
        shutil.rmtree(target, ignore_errors=True)
        raise WorkspaceRefused(exc.code, exc.message, status=422 if exc.code == "WORKSPACE_TITLE_INVALID" else 409) from exc
    except (OSError, shutil.Error) as exc:
        # The folder did not exist before this request: remove all of it. On
        # Windows a deep root can pass the 260-character path limit while the
        # skills are copied; the reason is named, not hidden in a 500.
        shutil.rmtree(target, ignore_errors=True)
        raise WorkspaceRefused(
            "WORKSPACE_ROOT_UNAVAILABLE", f"the workspace could not be written under {root}: {type(exc).__name__}: {str(exc)[:300]}"
        ) from exc
    except BaseException:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return {"slug": result["slug"], "path": str(target), "protocol_fingerprint": result["protocol_fingerprint"]}


def check_open(root: Path, slug: str, current: Path | None) -> Path:
    """The folder to restart on, after the validity and busy checks."""
    target = _target(root, slug)
    if not target.is_dir() or not validity(target)[0]:
        raise WorkspaceRefused("WORKSPACE_NOT_VALID", f"{target} is not a Nexus Scholar workspace ({validity(target)[1] or 'missing'})")
    if current is None:
        return target
    if target == current.resolve():
        return target
    state = busy(current)
    if state["run_active"] or state["pairing_open"]:
        which = "an agent run is active" if state["run_active"] else "an approval is open"
        raise WorkspaceRefused("WORKSPACE_BUSY", f"{which}; opening another workspace restarts the app and would end it", details=state)
    return target
