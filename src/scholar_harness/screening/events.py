"""Screening decision events (screening API contract §3, M1a).

A researcher's decision is an **event**: minted once on the device (its
`event_id` is the idempotency key), appended to
`literature/screening/events/<screener_id>.jsonl`, never edited. The batch
decision files the collector and acceptance consume
(`batch_NNN_decisions.json`) are a deterministic **projection** of those
events, so an offline phone can replay its queue any number of times and the
projected bytes, the decision ids and any approval over them stay the same.

- `intake` judges each event alone: `accepted`, `duplicate` (same id, same
  content), `conflict` (a second, differing head for one study and screener;
  stored, and the study leaves the projection) or `refused` with a typed code.
  A request's events and its one journal row are committed together or not at
  all (`ATOMIC_COMMIT_FAILED`).
- `project_batch` is a pure function of the log and the accepted batch.
  `decided_at` is the event's own client time, never the time of projection.

Every append happens under an OS file lock (contract §9.2), so the CLI and the
console can write at the same time.
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scholar_harness.contracts.canonical import deterministic_id
from scholar_harness.contracts.identifiers import IdentifierKind
from scholar_harness.screening.integrity import PROVENANCE_MISSING, STALE_BINDING
from scholar_harness.workspace.audit import append_event

logger = logging.getLogger(__name__)

EVENTS_DIR = Path("literature") / "screening" / "events"
OUTCOMES = frozenset({"INCLUDE", "EXCLUDE", "MAYBE"})
DEVICES = frozenset({"desktop", "phone"})
#: F7 (H-input-limits): a ``decided_at`` further ahead of the engine's clock
#: than this is refused; a device clock may run a little fast, a year cannot.
MAX_FUTURE_SKEW = timedelta(minutes=5)
#: F7: a ``note`` longer than this is refused (the discovery note's limit).
MAX_NOTE_CHARS = 2_000
REVEALS_FILE = Path("literature") / "screening" / "reveals.jsonl"
REVEAL_ACTION = "SCREENING_PROPOSAL_REVEALED"
PROJECTION_FAILED_ACTION = "SCREENING_PROJECTION_FAILED"
JOURNAL_ACTION = "SCREENING_DECISIONS_RECEIVED"

# Refusal codes (console refusal set, contract §7).
UNKNOWN_STUDY = "UNKNOWN_STUDY"
REASON_CODE_INVALID = "REASON_CODE_INVALID"
#: An EXCLUDE whose reason names a criterion the same event answers the other way (M6-beta).
REASON_CODE_INCONSISTENT = "REASON_CODE_INCONSISTENT"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
ATOMIC_COMMIT_FAILED = "ATOMIC_COMMIT_FAILED"
INVALID_OUTPUT = "INVALID_OUTPUT"
PROJECTION_STALE = "PROJECTION_STALE"

#: Fields the engine stamps on intake; the client cannot set them, and they do
#: not count when an `event_id` is replayed (idempotency compares the rest).
ENGINE_FIELDS = frozenset({"received_at", "token_scope", "changed_after_reveal"})

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SAFE_SCREENER = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class IntakeResult:
    event_id: str
    result: str  # accepted | duplicate | conflict | refused
    refusal: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"event_id": self.event_id, "result": self.result}
        if self.refusal is not None:
            out["refusal"] = self.refusal
        return out


@dataclass(frozen=True)
class BatchBinding:
    batch_index: int
    batch_id: str
    batch_sha256: str
    candidates: tuple[str, ...]


@dataclass
class ScreeningContext:
    """What an event is checked against: the protocol and the accepted batches."""

    protocol_fingerprint: str
    exclusion_ids: frozenset[str]
    inclusion_ids: frozenset[str]
    batches: dict[int, BatchBinding] = field(default_factory=dict)
    study_batch: dict[str, int] = field(default_factory=dict)

    def valid_reason(self, code: str | None) -> bool:
        if not code:
            return False
        if code in self.exclusion_ids:
            return True
        return code.startswith("FAILS-") and code[len("FAILS-") :] in self.inclusion_ids


def load_context(workspace: Path) -> ScreeningContext:
    """Read the current protocol and the newest accepted batch per index."""
    from scholar_protocol.canonical import canonical_fingerprint as protocol_fingerprint
    from scholar_protocol.models import ResearchProtocol

    ws = Path(workspace)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    criteria = protocol.get("screening_criteria") or {}

    def _ids(kind: str) -> frozenset[str]:
        return frozenset(
            str(item.get("id")) for item in criteria.get(kind) or [] if isinstance(item, dict)
        )

    context = ScreeningContext(
        protocol_fingerprint=protocol_fingerprint(ResearchProtocol.model_validate(protocol)),
        exclusion_ids=_ids("exclusion"),
        inclusion_ids=_ids("inclusion"),
    )
    registry_path = ws / "audit" / "artifact_registry.json"
    if not registry_path.is_file():
        return context
    entries = json.loads(registry_path.read_text(encoding="utf-8")).get("artifacts", {})
    newest: dict[int, tuple[str, dict]] = {}
    for artifact_id, entry in entries.items():
        if entry.get("artifact_type") != "screening_batch":
            continue
        artifact = json.loads((ws / entry["path"]).read_text(encoding="utf-8"))
        index = int(artifact["data"]["batch_index"])
        if index not in newest or entry.get("accepted_at", "") > newest[index][1].get("accepted_at", ""):
            newest[index] = (artifact_id, {**entry, "_artifact": artifact})
    for index, (_, entry) in sorted(newest.items()):
        data = entry["_artifact"]["data"]
        candidates = tuple(str(c["study_id"]) for c in data.get("candidates", []))
        context.batches[index] = BatchBinding(index, str(data["batch_id"]), entry["sha256"], candidates)
        for study in candidates:
            context.study_batch[study] = index
    return context


def screener_file(workspace: Path, screener_id: str) -> Path:
    """`events/<screener_id>.jsonl`, with the id made safe as a file name."""
    safe = _SAFE_SCREENER.sub("_", screener_id).strip("._") or "screener"
    return Path(workspace) / EVENTS_DIR / f"{safe}.jsonl"


class LockBusy(Exception):
    """The events lock could not be taken; nothing was read or stored."""


@contextmanager
def _locked(workspace: Path) -> Iterator[None]:
    """Exclusive OS lock over the events directory (Windows and POSIX)."""
    lock_path = Path(workspace) / EVENTS_DIR / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            except OSError as exc:  # Windows gives up after ten retries
                raise LockBusy(str(exc)) from exc
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX)
            except OSError as exc:
                raise LockBusy(str(exc)) from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


def read_events(workspace: Path) -> list[dict[str, Any]]:
    """Every stored event, across screener files, in file order."""
    directory = Path(workspace) / EVENTS_DIR
    events: list[dict[str, Any]] = []
    if not directory.is_dir():
        return events
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
    return events


def _client_content(event: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in event.items() if k not in ENGINE_FIELDS}


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip() or value.startswith("1970-01-01"):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    # A time without an offset is read as UTC, so two times always compare.
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _refuse(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def validate_event(
    event: Any,
    context: ScreeningContext,
    *,
    token_scope: str | None = None,
    received_at: str | None = None,
) -> dict[str, str] | None:
    """The typed refusal for one event, or None when it may be stored.

    F7 (H-input-limits): with ``received_at`` (the engine's clock) a
    ``decided_at`` more than :data:`MAX_FUTURE_SKEW` ahead is refused; with
    ``token_scope`` (``desktop`` or ``phone``) the event's ``device`` must be
    that scope; a ``note`` is text of at most :data:`MAX_NOTE_CHARS`.
    """
    if not isinstance(event, dict):
        return _refuse(INVALID_OUTPUT, "an event must be an object")
    if not _UUID.match(str(event.get("event_id") or "")):
        return _refuse(INVALID_OUTPUT, "event_id must be a UUID string")
    decided = _parse_time(event.get("decided_at"))
    if not str(event.get("screener_id") or "").strip() or decided is None:
        return _refuse(PROVENANCE_MISSING, "screener_id and a real decided_at are required")
    received = _parse_time(received_at)
    if received is not None and decided - received > MAX_FUTURE_SKEW:
        return _refuse(
            PROVENANCE_MISSING,
            f"decided_at is more than {MAX_FUTURE_SKEW.seconds // 60} minutes ahead of the engine's clock; "
            "check the device's clock",
        )
    if event.get("method") != "HUMAN":
        return _refuse(
            INVALID_OUTPUT, "decision events are human decisions; agents submit proposals"
        )
    if event.get("outcome") not in OUTCOMES:
        return _refuse(INVALID_OUTPUT, "outcome must be INCLUDE, EXCLUDE or MAYBE")
    if event.get("device") not in DEVICES:
        return _refuse(INVALID_OUTPUT, "device must be desktop or phone")
    if token_scope in DEVICES and event["device"] != token_scope:
        return _refuse(INVALID_OUTPUT, f"device must be {token_scope}, the scope of the token that sent the event")
    note = event.get("note")
    if note is not None and not isinstance(note, str):
        return _refuse(INVALID_OUTPUT, "note must be text or null")
    if isinstance(note, str) and len(note) > MAX_NOTE_CHARS:
        return _refuse(INVALID_OUTPUT, f"note is longer than {MAX_NOTE_CHARS} characters")
    for engine_field in ENGINE_FIELDS:
        if engine_field in event:
            return _refuse(INVALID_OUTPUT, f"{engine_field} is set by the engine, not the client")
    study = str(event.get("study_id") or "")
    if study not in context.study_batch:
        return _refuse(UNKNOWN_STUDY, f"{study!r} is not in the bound corpus")
    if event["outcome"] == "EXCLUDE" and not context.valid_reason(event.get("reason_code")):
        return _refuse(
            REASON_CODE_INVALID,
            "an EXCLUDE needs a protocol exclusion code or FAILS-<inclusion id>",
        )
    if event["outcome"] == "EXCLUDE":
        # The reason must agree with the event's own checklist (M6-beta, review
        # S-P1-3): FAILS-INC-n is refused when INC-n is answered yes, and EXC-n
        # when EXC-n is answered no. An absent or not_reported answer is fine.
        code = str(event.get("reason_code"))
        criterion, contradiction = (code[len("FAILS-"):], "yes") if code.startswith("FAILS-") else (code, "no")
        answers = {
            str(c.get("id")): c.get("answer")
            for c in (event.get("criteria") or [])
            if isinstance(c, dict)
        }
        if answers.get(criterion) == contradiction:
            return _refuse(
                REASON_CODE_INCONSISTENT,
                f"{code} contradicts this decision's own answer: {criterion} is answered {contradiction}",
            )
    binding = event.get("binding") or {}
    batch = context.batches[context.study_batch[study]]
    if (
        binding.get("protocol_fingerprint") != context.protocol_fingerprint
        or binding.get("batch_id") != batch.batch_id
        or binding.get("batch_sha256") != batch.batch_sha256
    ):
        return _refuse(STALE_BINDING, "the event is bound to an earlier protocol or batch")
    return None


def is_current(event: dict[str, Any], context: ScreeningContext) -> bool:
    """True when the event is bound to its study's current batch and protocol."""
    study = event.get("study_id")
    if study not in context.study_batch:
        return False
    batch = context.batches[context.study_batch[study]]
    binding = event.get("binding") or {}
    return (
        binding.get("protocol_fingerprint") == context.protocol_fingerprint
        and binding.get("batch_id") == batch.batch_id
        and binding.get("batch_sha256") == batch.batch_sha256
    )


def current_events(events: list[dict[str, Any]], context: ScreeningContext) -> list[dict[str, Any]]:
    """Review A: the events of the current generation. After a protocol change
    or a re-prepare, earlier decisions count nowhere: not as decided, not as
    conflicts, not as a reason to reveal a proposal."""
    return [e for e in events if is_current(e, context)]


class ProjectionStale(RuntimeError):
    """A decisions file claims the event log but differs from it; collect refuses."""

    code = PROJECTION_STALE


def read_reveals(workspace: Path) -> list[dict[str, Any]]:
    path = Path(workspace) / REVEALS_FILE
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _revealed(reveals: list[dict[str, Any]], study_id: str, screener_id: str, context: ScreeningContext) -> bool:
    """True when the study's proposal was revealed to the screener in the current generation."""
    return any(
        r.get("study_id") == study_id and r.get("screener_id") == screener_id and is_current(r, context)
        for r in reveals
    )


def record_reveal(
    workspace: Path,
    *,
    study_id: str,
    screener_id: str,
    proposal_id: str,
    context: ScreeningContext,
    revealed_at: str,
) -> bool:
    """Record the first reveal of a proposal to a screener (contract §3.1).

    Written under the events lock, so an intake either sees the reveal or ran
    before it. The journal row names the proposal, never its outcome. Returns
    False when this proposal was already revealed to this screener. Raises
    `LockBusy` when the lock cannot be taken; the caller must not show the
    proposal then, or a later change would go unstamped.
    """
    ws = Path(workspace)
    batch = context.batches[context.study_batch[study_id]]
    record = {
        "study_id": study_id,
        "screener_id": screener_id,
        "proposal_id": proposal_id,
        "revealed_at": revealed_at,
        "binding": {
            "protocol_fingerprint": context.protocol_fingerprint,
            "batch_id": batch.batch_id,
            "batch_sha256": batch.batch_sha256,
        },
    }
    with _locked(ws):
        if any(
            r.get("proposal_id") == proposal_id and r.get("screener_id") == screener_id and is_current(r, context)
            for r in read_reveals(ws)
        ):
            return False
        path = ws / REVEALS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        size = path.stat().st_size if path.exists() else 0
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        try:
            append_event(
                ws,
                REVEAL_ACTION,
                f"Showed the agent proposal for {study_id} to {screener_id}",
                agent="scholar-harness/screening-events",
                outputs=[str(REVEALS_FILE).replace("\\", "/")],
                parameters={"study_id": study_id, "screener_id": screener_id, "proposal_id": proposal_id},
                metrics={},
                refresh_index=False,
            )
        except Exception:
            with path.open("r+b") as handle:
                handle.truncate(size)
            raise
    return True


def _superseded(events: list[dict[str, Any]]) -> set[str]:
    gone: set[str] = set()
    for event in events:
        if event.get("supersedes"):
            gone.add(str(event["supersedes"]))
        gone.update(str(item) for item in event.get("resolves") or [])
    return gone


def heads(events: list[dict[str, Any]], study_id: str, screener_id: str) -> list[dict[str, Any]]:
    """The events for one (study, screener) that no later event supersedes."""
    mine = [
        e for e in events if e.get("study_id") == study_id and e.get("screener_id") == screener_id
    ]
    gone = _superseded(mine)
    return sorted((e for e in mine if e["event_id"] not in gone), key=lambda e: e["event_id"])


def winning_event(events: list[dict[str, Any]], study_id: str, screener_id: str) -> dict[str, Any] | None:
    """The head of the supersession chain, or None when the study is in conflict.

    Several heads with the same outcome are confirmations, not a conflict (a
    second device repeating the decision); the earliest `event_id` wins so the
    result does not depend on arrival order.
    """
    live = heads(events, study_id, screener_id)
    if not live or len({e["outcome"] for e in live}) > 1:
        return None
    return live[0]


def conflicts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every (study, screener) with differing heads, in study order."""
    keys = sorted({(e["study_id"], e["screener_id"]) for e in events})
    found = []
    for study, screener in keys:
        live = heads(events, study, screener)
        if len({e["outcome"] for e in live}) > 1:
            found.append({"study_id": study, "screener_id": screener, "events": live})
    return found


def intake(
    workspace: Path,
    events: list[Any],
    *,
    token_scope: str,
    received_at: str,
    device: str | None = None,
    context: ScreeningContext | None = None,
    after_commit: Any = None,
) -> list[IntakeResult]:
    """Judge and store a request's events (contract §3.4).

    `after_commit`, when given, is called with the stored events while the
    event lock is still held (the console regenerates projections there).
    """
    ws = Path(workspace)
    context = context or load_context(ws)
    try:
        with _locked(ws):
            return _intake_locked(ws, events, token_scope, received_at, device, context, after_commit)
    except LockBusy:
        # Review B: only a failure to take the lock means nothing was stored.
        return [
            IntakeResult(
                str(raw.get("event_id") or "") if isinstance(raw, dict) else "",
                "refused",
                _refuse(ATOMIC_COMMIT_FAILED, "the event log is busy; retry"),
            )
            for raw in events
        ]


def _intake_locked(ws, events, token_scope, received_at, device, context, after_commit):
    results: list[IntakeResult] = []
    stored = read_events(ws)
    reveals = read_reveals(ws)
    known = {e["event_id"]: e for e in stored}
    pending: list[dict[str, Any]] = []
    for raw in events:
        event_id = str(raw.get("event_id") or "") if isinstance(raw, dict) else ""
        refusal = validate_event(raw, context, token_scope=token_scope, received_at=received_at)
        if refusal is not None:
            results.append(IntakeResult(event_id, "refused", refusal))
            continue
        previous = known.get(event_id)
        if previous is not None:
            if _client_content(previous) == _client_content(raw):
                results.append(IntakeResult(event_id, "duplicate"))
            else:
                results.append(
                    IntakeResult(
                        event_id,
                        "refused",
                        _refuse(IDEMPOTENCY_CONFLICT, "event_id reused with different content"),
                    )
                )
            continue
        supersedes = raw.get("supersedes")
        if supersedes and not any(
            e["event_id"] == supersedes
            and e["study_id"] == raw["study_id"]
            and e["screener_id"] == raw["screener_id"]
            for e in stored + pending
        ):
            results.append(
                IntakeResult(
                    event_id,
                    "refused",
                    _refuse(INVALID_OUTPUT, "supersedes names no earlier event for this study"),
                )
            )
            continue
        # M1b-0: a superseding event after a reveal of this study's proposal
        # (same screener, current generation) is a change made after seeing it.
        after_reveal = bool(supersedes) and _revealed(reveals, raw["study_id"], raw["screener_id"], context)
        record = {
            **raw, "received_at": received_at, "token_scope": token_scope, "changed_after_reveal": after_reveal,
        }
        pending.append(record)
        known[event_id] = record
        live = heads(current_events(stored, context) + pending, raw["study_id"], raw["screener_id"])
        in_conflict = len({e["outcome"] for e in live}) > 1
        results.append(IntakeResult(event_id, "conflict" if in_conflict else "accepted"))
    if pending:
        _commit(ws, pending, results, device=device or str(pending[0].get("device")))
    # Review finding 8: project under the same lock as the append. Duplicates
    # re-project too, so a retry repairs a projection that failed earlier.
    project = [
        known[r.event_id] for r in results if r.result in ("accepted", "conflict", "duplicate")
    ]
    if after_commit is not None and project:
        try:
            after_commit(project)
        except Exception as exc:  # noqa: BLE001
            # Review B: the events are stored and journaled, so their results
            # stand. Review B2: the failure is journaled, and collect refuses
            # while any projection differs from the event log, so a stale
            # file is never published. A retry (a duplicate) re-projects.
            _journal_projection_failure(ws, project, exc)
    return results


def _journal_projection_failure(ws: Path, events: list[dict[str, Any]], exc: Exception) -> None:
    try:
        append_event(
            ws,
            PROJECTION_FAILED_ACTION,
            f"Stored {len(events)} decision event(s); their decisions file could not be rewritten "
            "(collect refuses until it is)",
            agent="scholar-harness/screening-events",
            parameters={"first_event_id": events[0]["event_id"], "error": type(exc).__name__},
            metrics={"events": len(events)},
            refresh_index=False,
        )
    except OSError as journal_exc:
        # The collect gate still refuses the stale file; say so on stderr.
        logger.warning("could not journal a failed projection: %s", journal_exc)


def projection_is_current(workspace: Path, batch_index: int, path: Path) -> bool:
    """True when `path` holds exactly what the event log projects for the batch."""
    try:
        final = path.read_bytes()
        payload = json.loads(final)
        manifest = json.loads((Path(workspace) / "project.json").read_text(encoding="utf-8"))
        workspace_id = str(manifest.get("registered_workspace_id") or manifest.get("project_id") or "")
        projected = project_batch(
            workspace, batch_index, str(payload.get("reviewed_by") or ""), workspace_id=workspace_id
        )
    except (KeyError, OSError, ValueError, AttributeError):
        return False
    return final.replace(b"\r\n", b"\n") == projected


def stale_projections(workspace: Path) -> list[int]:
    """Batches whose decisions file claims the event log but no longer matches it."""
    directory = Path(workspace) / "literature" / "screening"
    stale = []
    for path in sorted(directory.glob("batch_[0-9][0-9][0-9]_decisions.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not (isinstance(payload, dict) and payload.get("source") == "decision-events"):
            continue
        index = int(path.name[6:9])
        if not projection_is_current(workspace, index, path):
            stale.append(index)
    return stale


def _commit(
    workspace: Path, pending: list[dict[str, Any]], results: list[IntakeResult], *, device: str
) -> None:
    """Append the events and their one journal row, or neither."""
    sizes: dict[Path, int] = {}
    try:
        by_file: dict[Path, list[dict[str, Any]]] = {}
        for record in pending:
            by_file.setdefault(screener_file(workspace, record["screener_id"]), []).append(record)
        for path, records in by_file.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            sizes[path] = path.stat().st_size if path.exists() else 0
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                for record in records:
                    handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        append_event(
            workspace,
            JOURNAL_ACTION,
            f"Received {len(pending)} screening decision event(s) from {device}",
            agent="scholar-harness/screening-events",
            outputs=sorted(str(p.relative_to(workspace)).replace("\\", "/") for p in by_file),
            parameters={
                "device": device,
                "first_event_id": pending[0]["event_id"],
                "last_event_id": pending[-1]["event_id"],
            },
            metrics={
                "events": len(pending),
                "conflicts": sum(1 for r in results if r.result == "conflict"),
            },
            refresh_index=False,
        )
    except Exception:  # review finding 7: any failure rolls the events back
        for path, size in sizes.items():
            with path.open("r+b") as handle:
                handle.truncate(size)
        stored_ids = {record["event_id"] for record in pending}
        for i, result in enumerate(results):
            if result.event_id in stored_ids:
                results[i] = IntakeResult(
                    result.event_id,
                    "refused",
                    _refuse(ATOMIC_COMMIT_FAILED, "the events and their journal row could not be written together"),
                )


def _reason_text(event: dict[str, Any]) -> str:
    note = str(event.get("note") or "").strip()
    if note:
        return note
    if event.get("reason_code"):
        return str(event["reason_code"])
    return f"{event['outcome']} (no note)"


def decision_id_for(
    workspace_id: str,
    batch_id: str,
    event: dict[str, Any],
    parent_decision_ids: list[str],
) -> str:
    """The collector's existing recipe (`collector.py`), fed the event's fields."""
    return deterministic_id(
        IdentifierKind.SCREENING_DECISION,
        workspace_id,
        {
            "batch_id": batch_id,
            "study_id": event["study_id"],
            "screener_id": event["screener_id"],
            "method": event["method"],
            "decision": event["outcome"],
            "reason": _reason_text(event),
            "decided_at": event["decided_at"],
            "parent_decision_ids": parent_decision_ids,
        },
    )


def _chain(events: list[dict[str, Any]], head: dict[str, Any]) -> list[dict[str, Any]]:
    """Oldest-first supersession chain ending at `head`."""
    by_id = {e["event_id"]: e for e in events}
    chain = [head]
    while chain[0].get("supersedes") in by_id:
        chain.insert(0, by_id[chain[0]["supersedes"]])
    return chain


def project_batch(
    workspace: Path,
    batch_index: int,
    screener_id: str,
    *,
    workspace_id: str,
    context: ScreeningContext | None = None,
) -> bytes:
    """The `batch_NNN_decisions.json` bytes for one screener (contract §3.3)."""
    context = context or load_context(workspace)
    batch = context.batches[batch_index]
    events = [e for e in read_events(workspace) if e.get("screener_id") == screener_id]
    entries: list[dict[str, Any]] = []
    # Review finding 3: only events bound to this batch generation and protocol
    # count; after a re-prepare, earlier decisions are not carried over.
    current = {
        "protocol_fingerprint": context.protocol_fingerprint,
        "batch_id": batch.batch_id,
        "batch_sha256": batch.batch_sha256,
    }
    events = current_events(events, context)
    for study in sorted(batch.candidates):
        winner = winning_event(events, study, screener_id)
        if winner is None:
            continue  # undecided or in conflict: the coverage gate refuses collect
        parents: list[str] = []
        for link in _chain(events, winner)[:-1]:
            parents = [decision_id_for(workspace_id, batch.batch_id, link, parents)]
        entry = {
            "workspace_id": study,
            "decision": winner["outcome"],
            "method": winner["method"],
            "screener_id": winner["screener_id"],
            "decided_at": winner["decided_at"],
            "screening_reasoning": _reason_text(winner),
            "event_id": winner["event_id"],
            "parent_decision_ids": parents,
        }
        if winner.get("reason_code"):
            entry["reason_code"] = winner["reason_code"]
        if winner["outcome"] == "EXCLUDE" and winner.get("reason_code") in context.exclusion_ids:
            entry["violated_exclusion_criteria"] = [winner["reason_code"]]
        if winner.get("criteria"):
            entry["criteria"] = winner["criteria"]
        entries.append(entry)
    payload = {
        "batch": batch_index,
        "binding": current,
        "source": "decision-events",
        "reviewed_by": screener_id,
        "timestamp": max((e["decided_at"] for e in entries), default=""),
        "decisions": entries,
    }
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write_projection(
    workspace: Path,
    batch_index: int,
    screener_id: str,
    *,
    workspace_id: str,
    context: ScreeningContext | None = None,
) -> Path:
    """Write the projection, touching the file only when its bytes change."""
    data = project_batch(workspace, batch_index, screener_id, workspace_id=workspace_id, context=context)
    path = Path(workspace) / "literature" / "screening" / f"batch_{batch_index:03d}_decisions.json"
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return path
