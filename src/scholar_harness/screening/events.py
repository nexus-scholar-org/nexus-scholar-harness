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
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from scholar_harness.contracts.canonical import deterministic_id
from scholar_harness.contracts.identifiers import IdentifierKind
from scholar_harness.screening.integrity import PROVENANCE_MISSING, STALE_BINDING
from scholar_harness.workspace.audit import append_event

EVENTS_DIR = Path("literature") / "screening" / "events"
OUTCOMES = frozenset({"INCLUDE", "EXCLUDE", "MAYBE"})
DEVICES = frozenset({"desktop", "phone"})
JOURNAL_ACTION = "SCREENING_DECISIONS_RECEIVED"

# Refusal codes (console refusal set, contract §7).
UNKNOWN_STUDY = "UNKNOWN_STUDY"
REASON_CODE_INVALID = "REASON_CODE_INVALID"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
ATOMIC_COMMIT_FAILED = "ATOMIC_COMMIT_FAILED"
INVALID_OUTPUT = "INVALID_OUTPUT"

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


@contextmanager
def _locked(workspace: Path) -> Iterator[None]:
    """Exclusive OS lock over the events directory (Windows and POSIX)."""
    lock_path = Path(workspace) / EVENTS_DIR / ".lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX)
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
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _refuse(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def validate_event(event: Any, context: ScreeningContext) -> dict[str, str] | None:
    """The typed refusal for one event, or None when it may be stored."""
    if not isinstance(event, dict):
        return _refuse(INVALID_OUTPUT, "an event must be an object")
    if not _UUID.match(str(event.get("event_id") or "")):
        return _refuse(INVALID_OUTPUT, "event_id must be a UUID string")
    if not str(event.get("screener_id") or "").strip() or _parse_time(event.get("decided_at")) is None:
        return _refuse(PROVENANCE_MISSING, "screener_id and a real decided_at are required")
    if event.get("method") != "HUMAN":
        return _refuse(
            INVALID_OUTPUT, "decision events are human decisions; agents submit proposals"
        )
    if event.get("outcome") not in OUTCOMES:
        return _refuse(INVALID_OUTPUT, "outcome must be INCLUDE, EXCLUDE or MAYBE")
    if event.get("device") not in DEVICES:
        return _refuse(INVALID_OUTPUT, "device must be desktop or phone")
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
    binding = event.get("binding") or {}
    batch = context.batches[context.study_batch[study]]
    if (
        binding.get("protocol_fingerprint") != context.protocol_fingerprint
        or binding.get("batch_id") != batch.batch_id
        or binding.get("batch_sha256") != batch.batch_sha256
    ):
        return _refuse(STALE_BINDING, "the event is bound to an earlier protocol or batch")
    return None


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
) -> list[IntakeResult]:
    """Judge and store a request's events (contract §3.4)."""
    ws = Path(workspace)
    context = context or load_context(ws)
    results: list[IntakeResult] = []
    with _locked(ws):
        stored = read_events(ws)
        known = {e["event_id"]: e for e in stored}
        pending: list[dict[str, Any]] = []
        for raw in events:
            event_id = str(raw.get("event_id") or "") if isinstance(raw, dict) else ""
            refusal = validate_event(raw, context)
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
            record = {**raw, "received_at": received_at, "token_scope": token_scope, "changed_after_reveal": False}
            pending.append(record)
            known[event_id] = record
            live = heads(stored + pending, raw["study_id"], raw["screener_id"])
            in_conflict = len({e["outcome"] for e in live}) > 1
            results.append(IntakeResult(event_id, "conflict" if in_conflict else "accepted"))
        if pending:
            _commit(ws, pending, results, device=device or str(pending[0].get("device")))
    return results


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
    except OSError:
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
