"""The workspace format version, and the copy made before a newer build writes.

H-workspace-format-version (record ``docs/roadmap/milestones/H-workspace-format-version.md``).

- **The version** lives in ``workspace_format.json`` at the workspace root: one
  number for the whole workspace (``format``) and the build that last opened
  it for writing (``written_by``). Only this module writes it. A workspace
  without it was written before format versions existed: format 0.
- **Opening for writing** (:func:`prepare_for_writing`): a workspace whose
  format is newer than :data:`CURRENT_FORMAT` is refused; an unreadable file
  is refused; when the format is older, or the build is newer than
  ``written_by``, a verified zip of the workspace is saved first in
  ``<parent>/.nexus-copies/<slug>/`` and only then are the migration steps run
  and the file stamped. A failed copy leaves the workspace untouched.
- **Reads never write**: :func:`read_format`, :func:`describe` and
  :func:`check_not_newer` only read.
- **Migrations** (:data:`STEPS`): one step from ``n`` to ``n + 1``, idempotent,
  journalled, writing only files the copy holds. Step 0 to 1 rewrites nothing.

A change that an older build would refuse, misread or overwrite raises
:data:`CURRENT_FORMAT` by one and adds a step (``DEVELOPER_COMPASS.md``).
"""

from __future__ import annotations

import functools
import json
import os
import re
import threading
import time
import uuid
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FORMAT_FILE = "workspace_format.json"
FORMAT_SCHEMA = "nexus.workspace-format.v1"
#: The newest layout this build reads and writes. 1 = the layout of 1.1.0b7.
CURRENT_FORMAT = 1
COPIES_DIR = ".nexus-copies"
KEEP_COPIES = 5
#: Left out of the copy (record §3.3): secret, vendored, caches, re-made, removed features.
EXCLUDED_DIRS = frozenset({".agents", ".cache", "exports", "chroma_db", "rag"})
EXCLUDED_FILES = frozenset({".env"})
#: Already compressed: stored, not deflated (deflating PDFs took 22 s instead of 0.9 s for 417 MB).
STORED_SUFFIXES = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".xlsx", ".docx", ".webp"})
#: Copies smaller than this are made before the app serves; larger ones in the background.
FOREGROUND_BYTES = 64 * 1024 * 1024
LOCK_NAME = ".copy.lock"
#: How long an open waits for another live process's copy of the same review.
LOCK_WAIT_S = 600.0

WORKSPACE_FORMAT_NEWER = "WORKSPACE_FORMAT_NEWER"
WORKSPACE_FORMAT_UNREADABLE = "WORKSPACE_FORMAT_UNREADABLE"
WORKSPACE_COPY_FAILED = "WORKSPACE_COPY_FAILED"
WORKSPACE_PREPARING = "WORKSPACE_PREPARING"

ACTION_STAMPED = "WORKSPACE_FORMAT_STAMPED"
ACTION_MIGRATED = "WORKSPACE_FORMAT_MIGRATED"
ACTION_NEWER_BUILD = "WORKSPACE_OPENED_BY_NEWER_BUILD"
FORMAT_ACTIONS = frozenset({ACTION_STAMPED, ACTION_MIGRATED, ACTION_NEWER_BUILD})

#: A copy's file name; the folder (`.nexus-copies/<slug>/`) names the review, so the
#: file name does not repeat it (a long folder name would pass Windows' 260 characters).
_COPY_NAME = re.compile(r"^(?P<at>\d{8}T\d{6}Z)(?:-\d+)?-format\d+-to\d+-.+\.zip$")


class WorkspaceFormatRefused(Exception):
    """The workspace is not opened for writing; ``code`` names why."""

    def __init__(self, code: str, message: str, status: int = 409, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


class CopyCancelled(Exception):
    """The copy was stopped (the server is shutting down); nothing was stamped."""


# --- the build's version ---------------------------------------------------- #


@functools.lru_cache(maxsize=1)
def build_version() -> str:
    """The installed package's version (``1.1.0b8``), else ``unknown``."""
    try:
        from importlib.metadata import version

        return version("nexus-scholar")
    except Exception:  # noqa: BLE001 - a source tree without metadata
        return "unknown"


_VERSION = re.compile(r"^(\d+(?:\.\d+)*)(?:(a|b|rc)(\d+))?(?:\.post(\d+))?(?:\.dev(\d+))?(?:\+.*)?$")
_PRE_RANK = {"a": 0, "b": 1, "rc": 2}


def version_key(text: str | None) -> tuple | None:
    """A sortable key for a PEP 440 release such as ``1.1.0b7``; ``None`` when unreadable."""
    match = _VERSION.match((text or "").strip())
    if not match:
        return None
    release, pre, pre_n, post, dev = match.groups()
    numbers = tuple(int(x) for x in release.split("."))
    numbers = numbers + (0,) * (6 - len(numbers))
    # A final release sorts after its pre-releases; a .dev sorts before what it precedes.
    if pre:
        pre_key = (_PRE_RANK[pre], int(pre_n))
    elif dev and not post:
        pre_key = (-1, 0)  # 1.1.0.dev1 comes before 1.1.0a1
    else:
        pre_key = (3, 0)
    return (numbers, pre_key, int(post) if post else -1, int(dev) if dev else 1 << 30)


# --- reading ---------------------------------------------------------------- #


@dataclass(frozen=True)
class FormatState:
    format: int
    written_by: str | None
    updated_at: str | None
    recorded: bool


def format_path(ws: Path) -> Path:
    return Path(ws) / FORMAT_FILE


def read_format(ws: Path | str) -> FormatState:
    """The recorded format; format 0 when there is no file. Refuses an unreadable one, never guesses."""
    path = format_path(Path(ws))
    if not path.exists():
        return FormatState(0, None, None, False)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _unreadable(path, f"{type(exc).__name__}") from exc
    if not isinstance(data, dict) or data.get("schema") != FORMAT_SCHEMA:
        raise _unreadable(path, "it is not a format file this version reads")
    number = data.get("format")
    if isinstance(number, bool) or not isinstance(number, int) or number < 0:
        raise _unreadable(path, "its format is not a whole number")
    written_by = data.get("written_by")
    return FormatState(number, written_by if isinstance(written_by, str) else None, data.get("updated_at"), True)


def _unreadable(path: Path, why: str) -> WorkspaceFormatRefused:
    return WorkspaceFormatRefused(
        WORKSPACE_FORMAT_UNREADABLE,
        f"This review was not opened: its format file ({path.name}) cannot be read ({why}). "
        "Nothing in the review was changed.",
        details={"path": str(path)},
    )


def newer_refusal(ws: Path, state: FormatState, build: str | None = None) -> WorkspaceFormatRefused:
    build = build or build_version()
    by = state.written_by or "a newer version"
    return WorkspaceFormatRefused(
        WORKSPACE_FORMAT_NEWER,
        f"Made with a newer version of Nexus Scholar. This review was last opened with Nexus Scholar {by}, "
        f"which stores reviews in a way this version ({build}) cannot read safely. To keep it intact, this "
        f"version does not open it. Install Nexus Scholar {by} or later to continue.",
        details={"format": state.format, "this_format": CURRENT_FORMAT, "written_by": state.written_by, "build": build},
    )


def check_not_newer(ws: Path | str) -> FormatState:
    """Refuse a newer or unreadable workspace; a pure read (the journal writer's backstop)."""
    state = read_format(ws)
    if state.format > CURRENT_FORMAT:
        raise newer_refusal(Path(ws), state)
    return state


@dataclass(frozen=True)
class Plan:
    state: FormatState
    build: str
    reason: str | None  # "format", "build" or None (nothing to do)

    @property
    def needed(self) -> bool:
        return self.reason is not None


def plan(ws: Path | str, *, build: str | None = None) -> Plan:
    """What opening for writing would do; refuses a newer or unreadable workspace. A pure read."""
    build = build or build_version()
    state = check_not_newer(ws)
    if state.format < CURRENT_FORMAT:
        return Plan(state, build, "format")
    mine, theirs = version_key(build), version_key(state.written_by)
    if mine is not None and (theirs is None or theirs < mine):
        return Plan(state, build, "build")
    return Plan(state, build, None)


# --- the copy ----------------------------------------------------------------- #


def copies_dir(ws: Path | str) -> Path:
    ws = Path(ws).resolve()
    return ws.parent / COPIES_DIR / ws.name


def _excluded_dir(rel_parts: tuple[str, ...]) -> bool:
    """A left-out folder at the root, or inside ``audit/replaced/<stamp>/``."""
    if len(rel_parts) == 1:
        return rel_parts[0] in EXCLUDED_DIRS
    return len(rel_parts) == 4 and rel_parts[:2] == ("audit", "replaced") and rel_parts[3] in EXCLUDED_DIRS


def copy_members(ws: Path | str) -> list[tuple[Path, str, int]]:
    """``(file, name in the zip, size)`` for every file the copy holds, in a stable order."""
    ws = Path(ws).resolve()
    out: list[tuple[Path, str, int]] = []
    for folder, dirs, files in os.walk(ws, followlinks=False):
        here = Path(folder)
        rel = here.relative_to(ws).parts
        dirs[:] = sorted(d for d in dirs if not _excluded_dir((*rel, d)) and not (here / d).is_symlink())
        for name in sorted(files):
            if not rel and name in EXCLUDED_FILES:
                continue
            path = here / name
            if path.is_symlink():
                continue
            out.append((path, "/".join((*rel, name)), path.stat().st_size))
    return out


def copy_name(from_format: int, to_format: int, from_build: str | None, build: str, now: datetime) -> str:
    """``20261130T100000Z-format0-to1-earlier-to-1.1.0b8.zip``: short whatever the review's name."""
    safe = re.compile(r"[^A-Za-z0-9.+-]+")
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return (
        f"{stamp}-format{from_format}-to{to_format}-"
        f"{safe.sub('_', from_build or 'earlier')[:40]}-to-{safe.sub('_', build)[:40]}.zip"
    )


Progress = Callable[[int, int], None]


def make_copy(
    ws: Path | str,
    name: str,
    *,
    progress: Progress | None = None,
    cancel: threading.Event | None = None,
) -> Path:
    """Write ``name`` into :func:`copies_dir`, verified; refuse ``WORKSPACE_COPY_FAILED`` on any fault.

    The zip is written as ``<name>.partial``, every member's CRC is checked,
    the member list and the sizes are compared with what was listed, and only
    then is it renamed. A file that changed size while it was copied fails the
    copy. Nothing in the workspace is written.
    """
    ws = Path(ws).resolve()
    target_dir = copies_dir(ws)
    final = target_dir / name
    n = 1
    while final.exists():  # two copies in one second
        n += 1
        final = target_dir / re.sub(r"^(\d{8}T\d{6}Z)-format", rf"\g<1>-{n}-format", name, count=1)
    partial = target_dir / (final.name + ".partial")
    try:
        members = copy_members(ws)
        total = sum(size for _p, _n, size in members)
        target_dir.mkdir(parents=True, exist_ok=True)
        _write_readme(target_dir.parent)
        done = 0
        if progress:
            progress(0, total)
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path, arcname, size in members:
                if cancel is not None and cancel.is_set():
                    raise CopyCancelled()
                kind = zipfile.ZIP_STORED if path.suffix.lower() in STORED_SUFFIXES else zipfile.ZIP_DEFLATED
                archive.write(path, arcname, compress_type=kind)
                done += size
                if progress:
                    progress(done, total)
        with zipfile.ZipFile(partial) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise OSError(f"the copy of {bad} does not read back")
            written = {info.filename: info.file_size for info in archive.infolist()}
        expected = {arcname: size for _p, arcname, size in members}
        if written != expected:
            changed = sorted(n for n in expected if written.get(n) != expected[n]) or sorted(set(written) - set(expected))
            raise OSError(f"a file changed while it was being copied ({', '.join(changed[:3])}); try again")
        if cancel is not None and cancel.is_set():
            raise CopyCancelled()
        os.replace(partial, final)
        return final
    except CopyCancelled:
        _remove(partial)
        raise
    except Exception as exc:  # noqa: BLE001 - every fault refuses the open
        _remove(partial)
        raise WorkspaceFormatRefused(
            WORKSPACE_COPY_FAILED,
            "This review was not opened. Nexus Scholar saves a copy of a review before a newer version opens "
            f"it, and the copy could not be saved: {type(exc).__name__}: {str(exc)[:300]}. Nothing in the "
            f"review was changed. Check that there is enough free disk space and that the folder {target_dir} "
            "can be written (on Windows a very deep folder can also be the cause), then try again.",
            details={"copies_dir": str(target_dir), "reason": f"{type(exc).__name__}: {str(exc)[:300]}"},
        ) from exc


def _remove(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


_README = """Copies of your Nexus Scholar reviews

Nexus Scholar saves a copy of a review here before a newer version of the app
opens it, in case the newer version changes something you want to undo.
Each review has its own folder; the five newest copies are kept.

To go back to a copy:
1. Close Nexus Scholar.
2. Rename the review's folder (for example add "-newer" to its name).
3. Unzip the copy into a new folder with the review's original name.
4. Copy your .env file back into it if the review had one (copies never hold keys).
5. Open it with the version of Nexus Scholar you used before.

These copies sit beside your reviews: they are not a backup of your disk.
"""


def _write_readme(root: Path) -> None:
    readme = root / "README.txt"
    if not readme.exists():
        try:
            readme.write_text(_README, encoding="utf-8")
        except OSError:
            pass


def prune(ws: Path | str, keep: int = KEEP_COPIES) -> list[str]:
    """Delete this mechanism's copies beyond the ``keep`` newest; never another file."""
    folder = copies_dir(ws)
    ours: list[tuple[str, int, Path]] = []
    try:
        for path in folder.glob("*.zip") if folder.is_dir() else []:
            match = _COPY_NAME.match(path.name)
            if match:
                try:
                    ours.append((match.group("at"), path.stat().st_mtime_ns, path))
                except OSError:
                    continue  # removed meanwhile
    except OSError:
        return []
    ours.sort(key=lambda item: item[:2])
    removed = []
    for _at, _mtime, path in ours[: max(0, len(ours) - keep)]:
        try:
            path.unlink()
            removed.append(path.name)
        except OSError:
            pass
    return removed


def last_copy(ws: Path | str) -> dict[str, Any] | None:
    """The newest copy of this workspace, for the Workspaces screen; a pure read."""
    folder = copies_dir(ws)
    best: tuple[str, int, Path] | None = None
    try:
        for path in folder.glob("*.zip") if folder.is_dir() else []:
            match = _COPY_NAME.match(path.name)
            if match:
                key = (match.group("at"), path.stat().st_mtime_ns, path)
                if best is None or key[:2] > best[:2]:
                    best = key
        if best is None:
            return None
        at = datetime.strptime(best[0], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC).isoformat()
        return {"name": best[2].name, "folder": str(folder), "at": at, "bytes": best[2].stat().st_size}
    except OSError:
        return None


# --- the lock ----------------------------------------------------------------- #


class _CopyLock:
    """One copy of a workspace at a time, across processes; the file lives beside the copies.

    An operating-system lock on an open file (``msvcrt.locking`` on Windows,
    ``fcntl.flock`` elsewhere): it ends with the process that holds it, so a
    copy interrupted by a crash, a closed window or a power cut leaves nothing
    that blocks the next open. The file itself stays; it holds no state.
    """

    def __init__(self, ws: Path, cancel: threading.Event | None):
        self.path = copies_dir(ws) / LOCK_NAME
        self.cancel = cancel
        self.handle: Any = None

    def __enter__(self) -> _CopyLock:
        try:
            return self._take()
        except OSError as exc:
            if self.handle is not None:
                self.handle.close()
                self.handle = None
            raise WorkspaceFormatRefused(
                WORKSPACE_COPY_FAILED,
                f"This review was not opened: the copy could not be started ({exc}). Nothing in the review was changed.",
                details={"copies_dir": str(self.path.parent), "reason": str(exc)},
            ) from exc

    def _take(self) -> _CopyLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = open(self.path, "a+b")  # noqa: SIM115 - held until __exit__
        deadline = time.monotonic() + LOCK_WAIT_S
        while True:
            if _try_lock(self.handle):
                return self
            if time.monotonic() > deadline:
                raise OSError("another copy of this review is still being made by a running Nexus Scholar")
            if self.cancel is not None and self.cancel.wait(0.2):
                self.handle.close()
                self.handle = None
                raise CopyCancelled()
            if self.cancel is None:
                time.sleep(0.2)

    def __exit__(self, *_exc: object) -> None:
        if self.handle is not None:
            _unlock(self.handle)
            self.handle.close()
            self.handle = None


def _try_lock(handle: Any) -> bool:
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(handle: Any) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


# --- migrations ------------------------------------------------------------- #


@dataclass(frozen=True)
class Step:
    from_format: int
    name: str
    description: str
    apply: Callable[[Path], list[str]]

    @property
    def to_format(self) -> int:
        return self.from_format + 1


def _stamp_today(_ws: Path) -> list[str]:
    """Format 1 is the layout of 1.1.0b7: no file is rewritten."""
    return []


STEPS: dict[int, Step] = {
    0: Step(0, "stamp-today", "records that the workspace follows the layout of 1.1.0b7; no file is rewritten", _stamp_today),
}


def write_format(ws: Path | str, number: int, build: str | None = None, *, now: datetime | None = None) -> Path:
    """Write ``workspace_format.json`` atomically (temporary file, then replace)."""
    path = format_path(Path(ws))
    data = {
        "schema": FORMAT_SCHEMA,
        "format": number,
        "written_by": build or build_version(),
        "updated_at": (now or datetime.now(UTC)).isoformat(),
    }
    tmp = path.with_name(f"{path.name}.tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def stamp_new(ws: Path | str) -> Path:
    """Genesis: a new workspace starts at the current format, written by this build."""
    return write_format(ws, CURRENT_FORMAT)


# --- opening for writing ------------------------------------------------------ #


@dataclass
class Prepared:
    copy: Path | None = None
    reason: str | None = None
    from_format: int = 0
    to_format: int = CURRENT_FORMAT
    from_build: str | None = None
    steps: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "copied": self.copy is not None,
            "copy": {"name": self.copy.name, "folder": str(self.copy.parent)} if self.copy else None,
            "reason": self.reason,
            "from_format": self.from_format,
            "to_format": self.to_format,
            "from_build": self.from_build,
            "steps": list(self.steps),
        }


_READY: set[str] = set()
_READY_LOCK = threading.Lock()


def _key(ws: Path) -> str:
    return os.path.normcase(str(Path(ws).resolve()))


def prepare_for_writing(
    ws: Path | str,
    *,
    agent: str,
    progress: Progress | None = None,
    cancel: threading.Event | None = None,
    build: str | None = None,
) -> Prepared:
    """Open ``ws`` for writing: refuse, or copy then migrate and stamp; a no-op when current.

    Raises :class:`WorkspaceFormatRefused` (newer, unreadable, copy failed) or
    :class:`CopyCancelled`. Remembered per folder for the life of the process.
    """
    ws = Path(ws).resolve()
    build = build or build_version()
    with _READY_LOCK:
        if _key(ws) in _READY and build == build_version():
            return Prepared(reason=None, from_format=CURRENT_FORMAT)
    first = plan(ws, build=build)
    if not first.needed:
        _remember(ws, build)
        return Prepared(reason=None, from_format=first.state.format, from_build=first.state.written_by)
    with _CopyLock(ws, cancel):
        current = plan(ws, build=build)  # another process may have done it while we waited
        if not current.needed:
            _remember(ws, build)
            return Prepared(reason=None, from_format=current.state.format, from_build=current.state.written_by)
        state = current.state
        name = copy_name(state.format, max(state.format, CURRENT_FORMAT), state.written_by, build, datetime.now(UTC))
        copy = make_copy(ws, name, progress=progress, cancel=cancel)
        result = Prepared(copy, current.reason, state.format, max(state.format, CURRENT_FORMAT), state.written_by)
        if cancel is not None and cancel.is_set():  # the server is stopping: stamp nothing
            _remove(copy)
            raise CopyCancelled()
        try:
            _record(ws, result, agent=agent, build=build)
        except OSError as exc:
            raise WorkspaceFormatRefused(
                WORKSPACE_COPY_FAILED,
                f"This review was not opened: a copy was saved ({copy.name}) but the review's format could not be "
                f"recorded ({type(exc).__name__}: {exc}). Try again.",
                details={"copies_dir": str(copy.parent), "reason": f"{type(exc).__name__}: {exc}"},
            ) from exc
        prune(ws)
    _remember(ws, build)
    return result


def _remember(ws: Path, build: str) -> None:
    if build == build_version():
        with _READY_LOCK:
            _READY.add(_key(ws))


def forget(ws: Path | str | None = None) -> None:
    """Tests: forget what this process has prepared."""
    with _READY_LOCK:
        if ws is None:
            _READY.clear()
        else:
            _READY.discard(_key(Path(ws)))


def _record(ws: Path, result: Prepared, *, agent: str, build: str) -> None:
    """The journal rows and the stamp, after the copy: row, step, stamp, per step."""
    from .audit import append_event

    copy_rel = f"{COPIES_DIR}/{ws.name}/{result.copy.name}" if result.copy else None
    common = {"copy": copy_rel, "build": build, "previous_build": result.from_build}
    for number in range(result.from_format, CURRENT_FORMAT):
        step = STEPS[number]
        action = ACTION_STAMPED if number == 0 else ACTION_MIGRATED
        if number == 0:
            text = (
                f"Workspace format recorded as {step.to_format} by Nexus Scholar {build}; a copy of the review was "
                f"saved first ({copy_rel}). No file was rewritten."
            )
        else:
            text = f"Workspace format {number} to {step.to_format} ({step.name}): {step.description}; copy {copy_rel}."
        append_event(
            ws, action, text, agent=agent, outputs=[FORMAT_FILE],
            parameters={**common, "from_format": number, "to_format": step.to_format, "step": step.name},
            refresh_index=False,
        )
        changed = step.apply(ws)
        write_format(ws, step.to_format, build)
        result.steps.append(step.name)
        if changed:
            append_event(
                ws, action, f"Step {step.name} changed: {', '.join(changed)}.", agent=agent, outputs=changed,
                parameters={**common, "step": step.name, "changed": changed}, refresh_index=False,
            )
    if result.from_format >= CURRENT_FORMAT:
        append_event(
            ws, ACTION_NEWER_BUILD,
            f"Opened for the first time by Nexus Scholar {build} (last written by {result.from_build or 'an earlier version'}); "
            f"a copy of the review was saved first ({copy_rel}).",
            agent=agent, outputs=[FORMAT_FILE], parameters=common, refresh_index=False,
        )
        write_format(ws, result.from_format, build)


def describe(ws: Path | str) -> dict[str, Any]:
    """The format block of a Workspaces row; a pure read."""
    try:
        state = read_format(ws)
    except WorkspaceFormatRefused:
        return {"recorded": True, "format": None, "written_by": None, "newer": False, "unreadable": True}
    return {
        "recorded": state.recorded,
        "format": state.format if state.recorded else None,
        "written_by": state.written_by,
        "newer": state.format > CURRENT_FORMAT,
        "unreadable": False,
    }


# --- the browser app's gate ---------------------------------------------------- #


class OpenGate:
    """Prepare the app's workspace, in the background when the copy is large.

    ``state`` is ``ready``, ``preparing`` or ``refused``. While preparing,
    workspace routes answer ``WORKSPACE_PREPARING`` with :meth:`snapshot`;
    when refused, the refusal's own code. :meth:`stop` cancels a running copy
    (the server is shutting down): the partial zip is removed and nothing is stamped.
    """

    def __init__(self, ws: Path, *, agent: str, title: str | None = None, foreground_bytes: int | None = None):
        self.ws = Path(ws).resolve()
        self.agent = agent
        self.title = title or self.ws.name
        self.foreground_bytes = FOREGROUND_BYTES if foreground_bytes is None else foreground_bytes
        self.state = "ready"
        self.reason: str | None = None
        self.refusal: WorkspaceFormatRefused | None = None
        self.result: Prepared | None = None
        self.done_bytes = 0
        self.total_bytes = 0
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None
        self._finished = threading.Event()

    def start(self) -> OpenGate:
        try:
            first = plan(self.ws)
        except WorkspaceFormatRefused as exc:
            return self._refuse(exc)
        if not first.needed:
            _remember(self.ws, first.build)
            self.result = Prepared(reason=None, from_format=first.state.format, from_build=first.state.written_by)
            self._finished.set()
            return self
        self.reason = first.reason
        try:
            self.total_bytes = sum(size for _p, _n, size in copy_members(self.ws))
        except OSError:
            self.total_bytes = 0
        self.state = "preparing"
        import logging

        logging.getLogger(__name__).warning(
            "Saving a copy of %s before this version of Nexus Scholar opens it (%.0f MB)…",
            self.title, self.total_bytes / 1e6,
        )
        if self.total_bytes <= self.foreground_bytes:
            self._run()
        else:
            self._thread = threading.Thread(target=self._run, name=f"workspace-copy-{self.ws.name}", daemon=True)
            self._thread.start()
        return self

    def _progress(self, done: int, total: int) -> None:
        self.done_bytes, self.total_bytes = done, total

    def _run(self) -> None:
        try:
            self.result = prepare_for_writing(self.ws, agent=self.agent, progress=self._progress, cancel=self._cancel)
            self.state = "ready"
            if self.result.copy is not None:
                import logging

                logging.getLogger(__name__).warning(
                    "Saved a copy of %s before opening it: %s", self.title, self.result.copy
                )
        except WorkspaceFormatRefused as exc:
            self._refuse(exc)
        except CopyCancelled:
            self.state = "cancelled"
        except Exception as exc:  # noqa: BLE001 - a fault in a background thread must not leave the gate open
            self._refuse(WorkspaceFormatRefused(WORKSPACE_COPY_FAILED, f"This review was not opened: {type(exc).__name__}: {exc}"))
        finally:
            self._finished.set()

    def _refuse(self, exc: WorkspaceFormatRefused) -> OpenGate:
        self.state, self.refusal = "refused", exc
        self._finished.set()
        return self

    def wait(self, timeout: float | None = None) -> bool:
        return self._finished.wait(timeout)

    def stop(self, timeout: float = 30.0) -> None:
        self._cancel.set()
        if self._thread is not None:
            self._thread.join(timeout)

    @property
    def ready(self) -> bool:
        return self.state == "ready"

    def snapshot(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "state": self.state,
            "slug": self.ws.name,
            "title": self.title,
            "reason": self.reason,
            "done_bytes": self.done_bytes,
            "total_bytes": self.total_bytes,
        }
        if self.refusal is not None:
            out["refusal"] = {"code": self.refusal.code, "message": self.refusal.message, "details": self.refusal.details}
        if self.result is not None:
            out["result"] = self.result.as_dict()
        return out
