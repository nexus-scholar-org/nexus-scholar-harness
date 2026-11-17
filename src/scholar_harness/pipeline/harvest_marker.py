"""The stage marker of a harvest, and the reading of its saved records (M3i-harvest-robustness).

A search run is archived as published right after its search; three stages
follow before screening can receive anything: deduplication, hydration (the
missing abstracts) and verification, and only the last one writes
``literature/verified.json``. This module keeps a small record of those three
beside the run's other files, ``literature/search_runs/run_NNN/pipeline.json``:

```json
{
  "schema": "nexus.harvest-pipeline.v1",
  "run": "run_001",
  "stages": {"deduplication": {"status": "DONE", "at": "..."}, "hydration": {...}, "verification": {...}},
  "ended": null,
  "verified_run": null,
  "resumed": []
}
```

``stages`` holds the stages that ended, in order. ``ended`` is ``null`` until
the preparation ends, then ``{"status", "at", "stage", "message"}`` with status
``DONE``, ``FAILED`` (an error in ``stage``) or ``STOPPED`` (the researcher's
stop, read before ``stage`` started). ``verified_run`` names the run whose
records are in ``verified.json``: this run, once its verification ended.
``resumed`` lists each later attempt to finish the preparation.

The file is written with the workspace's atomic writer, so a reader never sees
half of it. A process that dies leaves ``ended`` as ``null``; the reading
functions call that ``interrupted``. A run made before this module has no
marker and is never guessed at: with a ``verified.json`` it reads as ready, as
it always did, and without one as interrupted at an unknown stage.

``load_saved_documents`` reads what a stage saved (a run's ``raw.json``,
``deduped.json``) back into the search kit's models, so the remaining stages
can run from the files instead of from memory.

Nothing here is a Contract v1 artifact: the marker is a run record, like
``legs.json``; no snapshot, fingerprint or study id depends on it.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.workspace.atomic import atomic_write_text

MARKER_NAME = "pipeline.json"
SCHEMA = "nexus.harvest-pipeline.v1"
#: The stages after the search, in the order they run.
PREPARATION_STAGES = ("deduplication", "hydration", "verification")
DONE, FAILED, STOPPED = "DONE", "FAILED", "STOPPED"
#: ``preparation.state`` values of the public run views.
READY, RUNNING, INTERRUPTED, SUPERSEDED, NONE = "ready", "running", "interrupted", "superseded", "none"
UNFINISHED_STATES = ("failed", "stopped", INTERRUPTED)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def marker_path(run_dir: Path) -> Path:
    return Path(run_dir) / MARKER_NAME


def read(run_dir: Path | None) -> dict[str, Any] | None:
    """The run's marker; ``None`` when the run has none; ``{}`` when it cannot be read."""
    if run_dir is None:
        return None
    path = marker_path(run_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(run_dir: Path, marker: dict[str, Any]) -> None:
    atomic_write_text(marker_path(run_dir), json.dumps(marker, indent=2, ensure_ascii=False) + "\n")


def _usable(run_dir: Path | None) -> bool:
    return run_dir is not None and Path(run_dir).is_dir()


def _stages(marker: dict[str, Any] | None) -> dict[str, Any]:
    stages = (marker or {}).get("stages")
    return stages if isinstance(stages, dict) else {}


def first_unfinished(marker: dict[str, Any] | None) -> str | None:
    """The first stage the marker has no record of; ``None`` when all three ended."""
    done = _stages(marker)
    return next((stage for stage in PREPARATION_STAGES if stage not in done), None)


def start(run_dir: Path | None, *, from_stage: str = PREPARATION_STAGES[0]) -> None:
    """Open the marker: a new one after a published search, or a later attempt from ``from_stage``.

    A later attempt keeps the records of the stages before ``from_stage`` (they
    are not run again), drops the others and adds one ``resumed`` entry.
    """
    if not _usable(run_dir):
        return
    run_dir = Path(run_dir)
    previous = read(run_dir)
    keep = PREPARATION_STAGES[: PREPARATION_STAGES.index(from_stage)]
    stages = {name: record for name, record in _stages(previous).items() if name in keep}
    resumed = list((previous or {}).get("resumed") or []) if isinstance((previous or {}).get("resumed"), list) else []
    if previous is not None or from_stage != PREPARATION_STAGES[0]:
        resumed.append({"at": _now(), "from_stage": from_stage})
    _write(run_dir, {
        "schema": SCHEMA, "run": run_dir.name, "stages": stages, "ended": None,
        "verified_run": None, "resumed": resumed,
    })


def _current(run_dir: Path) -> dict[str, Any]:
    marker = read(run_dir) or {}
    marker.setdefault("schema", SCHEMA)
    marker.setdefault("run", run_dir.name)
    if not isinstance(marker.get("stages"), dict):
        marker["stages"] = {}
    marker.setdefault("ended", None)
    marker.setdefault("verified_run", None)
    marker.setdefault("resumed", [])
    return marker


def record_stage(run_dir: Path | None, stage: str, status: str) -> None:
    """One stage ended with ``status``."""
    if not _usable(run_dir):
        return
    run_dir = Path(run_dir)
    marker = _current(run_dir)
    marker["stages"][stage] = {"status": status, "at": _now()}
    _write(run_dir, marker)


def complete(run_dir: Path | None, verification_status: str) -> None:
    """Verification ended and wrote ``verified.json`` from this run: one write for both facts."""
    if not _usable(run_dir):
        return
    run_dir = Path(run_dir)
    marker = _current(run_dir)
    now = _now()
    marker["stages"]["verification"] = {"status": verification_status, "at": now}
    marker["ended"] = {"status": DONE, "at": now, "stage": None, "message": None}
    marker["verified_run"] = run_dir.name
    _write(run_dir, marker)


def end(run_dir: Path | None, status: str, *, stage: str, message: str | None = None) -> None:
    """The preparation ended without a ``verified.json``: ``FAILED`` in ``stage`` or ``STOPPED`` before it."""
    if not _usable(run_dir):
        return
    run_dir = Path(run_dir)
    marker = _current(run_dir)
    marker["ended"] = {"status": status, "at": _now(), "stage": stage, "message": message}
    marker["verified_run"] = None
    _write(run_dir, marker)


def load_saved_documents(path: Path | str) -> list[Any]:
    """The documents a stage saved (``raw.json`` of a run, ``deduped.json``), as the kit's models.

    M3i-harvest-robustness: a harvest is finished from its saved records. Each
    record is rebuilt field for field (``scholar_search.models.document_from_record``),
    so the stages that follow write the same files as when the records were
    still in memory. Raises ``ValueError`` when the file is not a list of records.
    """
    from scholar_search.models import document_from_record

    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{Path(path).name} is not a list of saved records")
    return [document_from_record(row) for row in rows]


def _is_published(manifest: dict[str, Any]) -> bool:
    return bool(manifest.get("corpus_published", manifest.get("raw_published")))


def preparation_view(
    lit_dir: Path,
    run_dir: Path,
    *,
    published: bool,
    newest_published: bool,
    job_running: bool = False,
    frozen: bool = False,
) -> dict[str, Any]:
    """What a run view says about the stages after the search (``preparation``).

    ``state``: ``none`` (the search was not published, nothing follows it),
    ``superseded`` (a later run is the corpus), ``ready`` (``verified.json`` is
    this run's), ``running``, ``failed``, ``stopped`` or ``interrupted`` (it
    never ended: the console was closed or the process died). ``stage`` is the
    stage it is in, or where it failed or stopped; ``None`` when ready or when
    there is no marker to say. ``can_finish`` says whether the remaining stages
    can be run from the run's saved records; when they cannot, ``cannot_finish``
    says why (``corpus_accepted`` or ``records_missing``).
    """
    marker = read(run_dir)
    view: dict[str, Any] = {
        "state": NONE, "stage": None, "stages": dict(_stages(marker)), "ended_at": None,
        "message": None, "marker": marker is not None, "can_finish": False, "cannot_finish": None,
    }
    if not published:
        return view
    if not newest_published:
        view["state"] = SUPERSEDED
        return view
    verified = (Path(lit_dir) / "verified.json").is_file()
    if marker is None:
        # A run made before the marker existed: its state is not guessed.
        view["state"] = READY if verified else INTERRUPTED
    else:
        ended = marker.get("ended")
        if not isinstance(ended, dict):
            view["state"] = RUNNING if job_running else INTERRUPTED
            view["stage"] = first_unfinished(marker) if marker else None
        else:
            status = ended.get("status")
            view["ended_at"] = ended.get("at")
            if status == DONE and marker.get("verified_run") == Path(run_dir).name and verified:
                view["state"] = READY
            elif status == FAILED:
                view["state"], view["stage"], view["message"] = "failed", ended.get("stage"), ended.get("message")
            elif status == STOPPED:
                view["state"], view["stage"] = "stopped", ended.get("stage")
            else:
                # Ended as done, but verified.json is missing or is not this run's.
                view["state"], view["stage"] = INTERRUPTED, "verification"
    if view["state"] in UNFINISHED_STATES:
        # Why the remaining stages cannot be run, when they cannot: the corpus
        # is frozen (it came from elsewhere), or the run's records are gone.
        if frozen:
            view["cannot_finish"] = "corpus_accepted"
        elif not (Path(run_dir) / "raw.json").is_file():
            view["cannot_finish"] = "records_missing"
        view["can_finish"] = view["cannot_finish"] is None
    return view


def corpus_run_dir(lit_dir: Path) -> Path | None:
    """The newest search run published as the corpus, or ``None``."""
    runs_dir = Path(lit_dir) / "search_runs"
    if not runs_dir.is_dir():
        return None
    runs = sorted(
        (d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_") and d.name[4:].isdigit()),
        key=lambda d: int(d.name[4:]),
        reverse=True,
    )
    for run_dir in runs:
        try:
            manifest = json.loads((run_dir / "legs.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(manifest, dict) and _is_published(manifest):
            return run_dir
    return None


def pending_preparation(workspace: Path | str) -> dict[str, Any] | None:
    """The corpus run's ``preparation`` while it is not ready, else ``None``.

    Read from disk only, so it answers the same before and after a restart. A
    preparation that is still running reads as ``interrupted`` here (no job is
    known at this level); either way ``verified.json`` is not this run's yet.
    """
    lit_dir = Path(workspace) / "literature"
    run_dir = corpus_run_dir(lit_dir)
    if run_dir is None:
        return None
    view = preparation_view(lit_dir, run_dir, published=True, newest_published=True)
    return None if view["state"] == READY else {"run": run_dir.name, **view}
