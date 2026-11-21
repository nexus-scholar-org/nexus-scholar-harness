"""The criteria pilot (M11b part B; decision 2026-11-21, M11b items 5, 6, 9, 11).

A pilot is a random sample of the records with no main decision, screened
before the full screening to see where the criteria work. Its decisions are
**not counted** (answer 5): they are not decision events and never reach the
event log, the projected batch decisions files, approval, collect, PRISMA or
the agreement read. They live in their own append-only file, which a reader
that does not know it never sees (fail closed). When the pilot closes, its
records are ordinary undecided records of the main screening, screened again
blind to the pilot decision (answer 11).

Files, under ``literature/screening/pilot/`` (so a chase round archives them):

- ``pilot_NNN.json``: the draw (``pilot_id``, ``seed``, ``n``, the snapshot id,
  the protocol fingerprint, the criteria version, ``drawn_at``, ``drawn_by``,
  the drawn ``{study_id, batch_id}`` in drawn order); never rewritten.
- ``pilot_NNN_decisions.jsonl``: one line per pilot decision
  (``pilot_decision_id`` "PLD-" + 24 hex, derived from the pilot and the
  client's ``event_id``, so a replay is a duplicate).
- ``pilot_NNN_closed.json``: written once when the pilot ends ("End the pilot")
  or its last record is decided.

Journal rows: ``SCREENING_PILOT_DRAWN``, ``SCREENING_PILOT_DECISIONS_RECEIVED``
(counts only), ``SCREENING_PILOT_CLOSED``.

The result (``result``) is counts only, each with its denominator, and the
observations of the record's section (f), each a fixed rule over counts; the
agent's drafts appear only as counts per criterion, never one record's draft
(answer 11).
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import secrets
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PILOT_DIR = Path("literature") / "screening" / "pilot"
DRAWN_ACTION = "SCREENING_PILOT_DRAWN"
RECEIVED_ACTION = "SCREENING_PILOT_DECISIONS_RECEIVED"
CLOSED_ACTION = "SCREENING_PILOT_CLOSED"

# Refusal codes (screening API contract §7).
PILOT_OPEN = "PILOT_OPEN"
PILOT_RECORD_UNKNOWN = "PILOT_RECORD_UNKNOWN"
PILOT_CLOSED = "PILOT_CLOSED"
#: An unknown pilot id (404).
PILOT_NOT_FOUND = "PILOT_NOT_FOUND"
#: ``n`` outside 20 to 100 in steps of 10, or more than the records left to draw from.
PILOT_SIZE_INVALID = "PILOT_SIZE_INVALID"

MIN_N, MAX_N, STEP_N, DEFAULT_N = 20, 100, 10, 50
#: The record's estimate of a pilot's time: 30 seconds a record.
SECONDS_PER_RECORD = 30
OUTCOMES = ("INCLUDE", "MAYBE", "EXCLUDE")
MAX_NOTE_CHARS = 2_000

# The observation rules (record (f)); constants, never tuned per review.
MIRROR_SHARE, MIRROR_MIN = 0.90, 10
TOGETHER_SHARE, TOGETHER_MIN = 0.90, 5
HARD_SHARE, HARD_MIN = 0.50, 10
MOST_WORK_SHARE, MOST_WORK_MIN = 0.60, 5
UNCLEAR_SHARE, UNCLEAR_MIN = 0.30, 10
DIFFER_SHARE, DIFFER_MIN = 0.25, 10
#: "Never used" is read only once this many pilot decisions exist.
NEVER_USED_MIN = 10

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_PILOT_ID = re.compile(r"^pilot_(\d{3})$")
#: Fields the engine stamps; a client that sends one is refused.
ENGINE_FIELDS = frozenset({"pilot_decision_id", "pilot_id", "received_at", "criteria_version", "protocol_fingerprint"})


class PilotRefused(ValueError):
    def __init__(self, code: str, message: str, status: int = 409, **details: Any) -> None:
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _dir(ws: Path) -> Path:
    return Path(ws) / PILOT_DIR


def draw_path(ws: Path, pilot_id: str) -> Path:
    return _dir(ws) / f"{pilot_id}.json"


def decisions_path(ws: Path, pilot_id: str) -> Path:
    return _dir(ws) / f"{pilot_id}_decisions.jsonl"


def closed_path(ws: Path, pilot_id: str) -> Path:
    return _dir(ws) / f"{pilot_id}_closed.json"


# --- reading -------------------------------------------------------------------------


def list_pilots(ws: Path) -> list[dict[str, Any]]:
    """Every draw in this screening round, oldest first."""
    directory = _dir(ws)
    if not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.glob("pilot_[0-9][0-9][0-9].json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and _PILOT_ID.match(str(data.get("pilot_id") or "")):
            out.append(data)
    return out


def read_draw(ws: Path, pilot_id: str) -> dict[str, Any]:
    if not _PILOT_ID.match(str(pilot_id or "")) or not draw_path(ws, pilot_id).is_file():
        raise PilotRefused(PILOT_NOT_FOUND, f"no pilot {pilot_id!r} in this workspace", status=404)
    return json.loads(draw_path(ws, pilot_id).read_text(encoding="utf-8"))


def read_decisions(ws: Path, pilot_id: str) -> list[dict[str, Any]]:
    path = decisions_path(ws, pilot_id)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def heads(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The pilot decision in force per study: the latest one received (a change of mind supersedes)."""
    latest: dict[str, dict[str, Any]] = {}
    for d in decisions:  # file order is arrival order
        latest[str(d.get("study_id"))] = d
    return latest


def closure(ws: Path, pilot_id: str) -> dict[str, Any] | None:
    path = closed_path(ws, pilot_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"pilot_id": pilot_id, "reason": "unreadable"}  # a closure that cannot be read is still a closure


def drawn_ids(draw: dict[str, Any]) -> list[str]:
    return [str(r["study_id"]) for r in draw.get("records") or [] if isinstance(r, dict)]


@dataclass(frozen=True)
class PilotState:
    pilot_id: str
    n: int
    decided: int
    open: bool
    closed: dict[str, Any] | None
    studies: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "pilot_id": self.pilot_id, "n": self.n, "decided": self.decided, "open": self.open,
            "closed_at": (self.closed or {}).get("closed_at"), "closed_reason": (self.closed or {}).get("reason"),
        }


def state(ws: Path, draw: dict[str, Any]) -> PilotState:
    pilot_id = str(draw["pilot_id"])
    studies = tuple(drawn_ids(draw))
    decided = len(set(heads(read_decisions(ws, pilot_id))) & set(studies))
    closed = closure(ws, pilot_id)
    return PilotState(pilot_id, len(studies), decided, closed is None and decided < len(studies), closed, studies)


def open_pilot(ws: Path) -> PilotState | None:
    """The pilot with undecided records that was not ended, if any (at most one is open)."""
    for draw in reversed(list_pilots(ws)):
        current = state(ws, draw)
        if current.open:
            return current
    return None


def last_pilot(ws: Path) -> PilotState | None:
    pilots = list_pilots(ws)
    return state(ws, pilots[-1]) if pilots else None


def open_studies(ws: Path) -> frozenset[str]:
    """The records of the open pilot (main decisions on them are refused ``PILOT_OPEN``)."""
    current = open_pilot(ws)
    return frozenset(current.studies) if current is not None else frozenset()


# --- the draw ----------------------------------------------------------------------------


def draw_sample(pool: list[str], seed: int, n: int) -> list[str]:
    """``random.Random(seed).sample`` over the pool in snapshot order: the same seed on the same
    snapshot gives the same list."""
    return random.Random(seed).sample(list(pool), n)


def _snapshot_id(ws: Path) -> str | None:
    try:
        entries = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")).get("artifacts", {})
    except (OSError, ValueError):
        return None
    corpora = [(k, e) for k, e in entries.items() if isinstance(e, dict) and e.get("artifact_type") == "corpus_snapshot"]
    if not corpora:
        return None
    return max(corpora, key=lambda kv: str(kv[1].get("accepted_at") or ""))[0]


def pool(ws: Path, context: Any) -> list[str]:
    """Records with no main decision (no event of the current generation) and in no earlier pilot,
    in snapshot order (the batches' order)."""
    from . import events as ev

    decided = {e.get("study_id") for e in ev.current_events(ev.read_events(ws), context)}
    piloted: set[str] = set()
    for draw in list_pilots(ws):
        piloted.update(drawn_ids(draw))
    order = [s for index in sorted(context.batches) for s in context.batches[index].candidates]
    return [s for s in order if s not in decided and s not in piloted]


def check_size(n: Any, available: int) -> int:
    if not isinstance(n, int) or isinstance(n, bool) or not (MIN_N <= n <= MAX_N) or n % STEP_N:
        raise PilotRefused(PILOT_SIZE_INVALID, f"n must be {MIN_N} to {MAX_N} in steps of {STEP_N}", status=422)
    if n > available:
        raise PilotRefused(
            PILOT_SIZE_INVALID, f"only {available} records have no decision and are in no earlier pilot",
            status=422, available=available,
        )
    return n


def draw(
    ws: Path, *, n: int, confirm: bool, drawn_by: str, drawn_at: str | None = None, seed: int | None = None
) -> dict[str, Any]:
    """Draw a pilot (DoD 11). Under the events lock; the dry call writes nothing."""
    from scholar_harness.workspace.audit import append_event

    from . import events as ev
    from .criteria import CRITERIA_AMENDMENT_AFTER_APPROVAL, any_batch_approved

    ws = Path(ws)
    with ev._locked(ws):
        context = ev.load_context(ws)
        if not context.batches:
            raise PilotRefused("BATCHES_NOT_PREPARED", "prepare the screening batches first; a pilot draws from them")
        if any_batch_approved(ws):
            raise PilotRefused(
                CRITERIA_AMENDMENT_AFTER_APPROVAL,
                "a batch is approved, so the criteria are fixed; a pilot can no longer change them",
            )
        current = open_pilot(ws)
        if current is not None:
            raise PilotRefused(
                PILOT_OPEN, f"{current.pilot_id} has {current.n - current.decided} undecided records; finish or end it first",
                pilot_id=current.pilot_id, undecided=current.n - current.decided,
            )
        candidates = pool(ws, context)
        n = check_size(n, len(candidates))
        answer = {
            "n": n, "available": len(candidates),
            "expected_minutes": math.ceil(n * SECONDS_PER_RECORD / 60),
        }
        if not confirm:
            return {"recorded": False, **answer}
        seed = seed if seed is not None else secrets.randbits(32)
        chosen = draw_sample(candidates, seed, n)
        pilots = list_pilots(ws)
        pilot_id = f"pilot_{len(pilots) + 1:03d}"
        record = {
            "pilot_id": pilot_id,
            "seed": seed,
            "n": n,
            "snapshot_id": _snapshot_id(ws),
            "protocol_fingerprint": context.protocol_fingerprint,
            "criteria_version": context.criteria_version,
            "drawn_at": drawn_at or _now(),
            "drawn_by": drawn_by,
            "pool": len(candidates),
            "records": [{"study_id": s, "batch_id": context.batches[context.study_batch[s]].batch_id} for s in chosen],
        }
        path = draw_path(ws, pilot_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            append_event(
                ws, DRAWN_ACTION, f"Drew {pilot_id}: {n} records at random (seed {seed}); its decisions are not counted",
                agent="scholar-harness/console",
                outputs=[path.relative_to(ws).as_posix()],
                parameters={"pilot_id": pilot_id, "n": n, "seed": seed, "criteria_version": context.criteria_version,
                            "drawn_by": drawn_by},
                metrics={"n": n, "pool": len(candidates)},
            )
        except Exception:
            path.unlink(missing_ok=True)
            raise
    return {"recorded": True, "pilot_id": pilot_id, "seed": seed, "drawn_at": record["drawn_at"], **answer}


# --- closing -------------------------------------------------------------------------------


def _close_locked(ws: Path, current: PilotState, *, reason: str, closed_by: str, closed_at: str) -> dict[str, Any]:
    from scholar_harness.workspace.audit import append_event

    record = {"pilot_id": current.pilot_id, "reason": reason, "closed_at": closed_at, "closed_by": closed_by,
              "n": current.n, "decided": current.decided}
    path = closed_path(ws, current.pilot_id)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        append_event(
            ws, CLOSED_ACTION,
            f"Closed {current.pilot_id} ({reason}): {current.decided} of {current.n} decided; "
            "its records are ordinary undecided records of the main screening",
            agent="scholar-harness/console", outputs=[path.relative_to(ws).as_posix()],
            parameters={"pilot_id": current.pilot_id, "reason": reason, "closed_by": closed_by},
            metrics={"n": current.n, "decided": current.decided},
        )
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return record


def close(ws: Path, pilot_id: str, *, closed_by: str, closed_at: str | None = None) -> dict[str, Any]:
    """"End the pilot" (DoD 11d): its undecided records go back to the main screening."""
    from . import events as ev

    ws = Path(ws)
    with ev._locked(ws):
        current = state(ws, read_draw(ws, pilot_id))
        if current.closed is not None:
            raise PilotRefused(PILOT_CLOSED, f"{pilot_id} has already ended")
        if not current.open:  # every record decided: it closed by itself
            raise PilotRefused(PILOT_CLOSED, f"{pilot_id} is complete; every record is decided")
        record = _close_locked(ws, current, reason="ended", closed_by=closed_by, closed_at=closed_at or _now())
    return {**state(ws, read_draw(ws, pilot_id)).as_dict(), "closure": record}


# --- pilot decisions -------------------------------------------------------------------------


def pilot_decision_id(pilot_id: str, event_id: str) -> str:
    return "PLD-" + hashlib.sha256(f"{pilot_id}:{event_id}".encode()).hexdigest()[:24]


def _client(decision: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in decision.items() if k not in ENGINE_FIELDS}


def _refusal(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _check(raw: Any, context: Any, studies: set[str], token_scope: str, received_at: str) -> dict[str, str] | None:
    """The event intake's checks that apply to a pilot decision (no batch binding: it is in no batch)."""
    from . import events as ev

    if not isinstance(raw, dict):
        return _refusal(ev.INVALID_OUTPUT, "a pilot decision must be an object")
    for name in ENGINE_FIELDS:
        if name in raw:
            return _refusal(ev.INVALID_OUTPUT, f"{name} is set by the engine, not the client")
    if "binding" in raw:
        return _refusal(ev.INVALID_OUTPUT, "a pilot decision has no batch binding: it is part of no batch")
    if not _UUID.match(str(raw.get("event_id") or "")):
        return _refusal(ev.INVALID_OUTPUT, "event_id must be a UUID string (the client's idempotency key)")
    if not str(raw.get("screener_id") or "").strip() or ev._parse_time(raw.get("decided_at")) is None:
        return _refusal(ev.PROVENANCE_MISSING, "screener_id and a real decided_at are required")
    if raw.get("method", "HUMAN") != "HUMAN":
        return _refusal(ev.INVALID_OUTPUT, "pilot decisions are human decisions")
    if raw.get("outcome") not in OUTCOMES:
        return _refusal(ev.INVALID_OUTPUT, "outcome must be INCLUDE, EXCLUDE or MAYBE")
    if raw.get("device") not in ev.DEVICES:
        return _refusal(ev.INVALID_OUTPUT, "device must be desktop or phone")
    study = str(raw.get("study_id") or "")
    if study not in studies:
        return _refusal(PILOT_RECORD_UNKNOWN, f"{study!r} is not a record of this pilot")
    code = raw.get("reason_code")
    if raw["outcome"] == "EXCLUDE":
        if context.retired_reason(code):
            return _refusal(ev.REASON_CODE_RETIRED, f"{code} cites a criterion retired by a revision")
        if not context.valid_reason(code):
            return _refusal(ev.REASON_CODE_INVALID, "an EXCLUDE needs a protocol exclusion code or FAILS-<inclusion id>")
        criterion, contradiction = (code[len("FAILS-"):], "yes") if code.startswith("FAILS-") else (code, "no")
        answers = {str(c.get("id")): c.get("answer") for c in raw.get("criteria") or [] if isinstance(c, dict)}
        if answers.get(criterion) == contradiction:
            return _refusal(
                ev.REASON_CODE_INCONSISTENT, f"{code} contradicts this decision's own answer: {criterion} is answered {contradiction}"
            )
    elif code:
        return _refusal(ev.REASON_CODE_INVALID, "only an EXCLUDE carries a reason code")
    criteria = raw.get("criteria")
    if criteria is not None and (
        not isinstance(criteria, list)
        or not all(isinstance(c, dict) and c.get("answer") in ("yes", "no", "not_reported") for c in criteria)
    ):
        return _refusal(ev.INVALID_OUTPUT, "criteria is a list of {id, answer: yes|no|not_reported}")
    # H-input-limits (F7), as the event intake applies them.
    decided = ev._parse_time(raw.get("decided_at"))
    received = ev._parse_time(received_at)
    if decided is not None and received is not None and decided - received > ev.MAX_FUTURE_SKEW:
        return _refusal(ev.PROVENANCE_MISSING, "decided_at is ahead of the engine's clock; check the device's clock")
    if token_scope in ev.DEVICES and raw.get("device") != token_scope:
        return _refusal(ev.INVALID_OUTPUT, f"device must be {token_scope}, the scope of the token that sent it")
    note = raw.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > MAX_NOTE_CHARS):
        return _refusal(ev.INVALID_OUTPUT, f"note must be text of at most {MAX_NOTE_CHARS} characters")
    return None


def intake(
    ws: Path, pilot_id: str, decisions: list[Any], *, token_scope: str, received_at: str
) -> list[dict[str, Any]]:
    """Store a request's pilot decisions and its one journal row together, or neither (DoD 11c).

    Each decision gets ``accepted``, ``duplicate`` (its ``event_id`` already stored with the same
    content) or ``refused``. The last record decided closes the pilot by itself.
    """
    from scholar_harness.workspace.audit import append_event

    from . import events as ev

    ws = Path(ws)
    with ev._locked(ws):
        draw_record = read_draw(ws, pilot_id)
        current = state(ws, draw_record)
        is_open = current.closed is None and current.open
        context = ev.load_context(ws)
        studies = set(current.studies)
        stored = read_decisions(ws, pilot_id)
        known = {d["pilot_decision_id"]: d for d in stored if d.get("pilot_decision_id")}
        results: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []
        for raw in decisions:
            event_id = str(raw.get("event_id") or "") if isinstance(raw, dict) else ""
            pld = pilot_decision_id(pilot_id, event_id) if _UUID.match(event_id) else ""
            # A replay of a stored decision is a duplicate, whatever changed since (a revision, the
            # pilot's end), as the event intake answers a replayed event.
            if pld and pld in known:
                same = _client(known[pld]) == raw
                results.append({"event_id": event_id, "pilot_decision_id": pld, "result": "duplicate"} if same else {
                    "event_id": event_id, "result": "refused",
                    "refusal": _refusal(ev.IDEMPOTENCY_CONFLICT, "event_id reused with different content")})
                continue
            if not is_open:
                results.append({"event_id": event_id, "result": "refused", "refusal": _refusal(
                    PILOT_CLOSED, f"{pilot_id} has ended; its records are screened in the main screening")})
                continue
            refusal = _check(raw, context, studies, token_scope, received_at)
            if refusal is None and raw.get("supersedes"):
                parent = known.get(str(raw["supersedes"]))
                if parent is None or parent.get("study_id") != raw.get("study_id"):
                    refusal = _refusal(ev.INVALID_OUTPUT, "supersedes names no earlier pilot decision for this record")
            if refusal is not None:
                results.append({"event_id": event_id, "result": "refused", "refusal": refusal})
                continue
            record = {
                **raw,
                "pilot_decision_id": pld,
                "pilot_id": pilot_id,
                "received_at": received_at,
                "criteria_version": context.criteria_version,
                "protocol_fingerprint": context.protocol_fingerprint,
            }
            pending.append(record)
            known[pld] = record
            results.append({"event_id": event_id, "pilot_decision_id": pld, "result": "accepted"})
        if pending:
            path = decisions_path(ws, pilot_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            size = path.stat().st_size if path.exists() else 0
            try:
                with path.open("a", encoding="utf-8", newline="\n") as handle:
                    for record in pending:
                        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
                append_event(
                    ws, RECEIVED_ACTION,
                    f"Received {len(pending)} pilot decision(s) for {pilot_id} (not counted)",
                    agent="scholar-harness/console", outputs=[path.relative_to(ws).as_posix()],
                    parameters={"pilot_id": pilot_id, "device": token_scope},
                    metrics={"decisions": len(pending)},
                    refresh_index=False,
                )
            except Exception:
                with path.open("r+b") as handle:
                    handle.truncate(size)
                for i, r in enumerate(results):
                    if r["result"] == "accepted":
                        results[i] = {"event_id": r["event_id"], "result": "refused", "refusal": _refusal(
                            ev.ATOMIC_COMMIT_FAILED, "the pilot decisions and their journal row could not be written together")}
                return results
            after = state(ws, draw_record)
            if not after.open and after.closed is None:
                try:
                    _close_locked(ws, after, reason="complete", closed_by="engine", closed_at=received_at)
                except OSError:
                    pass  # the pilot reads as closed (every record decided) without the file
    return results


# --- the result --------------------------------------------------------------------------------


def implied(decision: dict[str, Any], criterion_id: str, side: str) -> str | None:
    """What a decision implies about one criterion ("yes" met / "no" not met), or None (record (e))."""
    outcome, code = decision.get("outcome"), str(decision.get("reason_code") or "")
    if outcome == "EXCLUDE":
        if code == criterion_id and side == "exclusion":
            return "yes"
        if code == f"FAILS-{criterion_id}" and side == "inclusion":
            return "no"
        return None
    if outcome == "INCLUDE":
        return "yes" if side == "inclusion" else "no"
    return None


def _share(count: int, of: int) -> dict[str, int]:
    return {"count": count, "of": of}


def _drafts_for(ws: Path, context: Any, decisions: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    """The latest draft's answers per pilot record, when it was made under the criteria version the
    pilot decision was made under (an earlier wording answered other criteria)."""
    from . import proposals as pr

    latest: dict[str, dict[str, Any]] = {}
    for p in sorted(pr.read_proposals(ws), key=lambda p: (p.get("created_at") or "", p.get("proposal_id") or "")):
        if p.get("study_id") in decisions and p.get("protocol_fingerprint") == context.protocol_fingerprint:
            latest[p["study_id"]] = p
    out: dict[str, dict[str, str]] = {}
    for study, proposal in latest.items():
        if pr.draft_version(proposal) != int(decisions[study].get("criteria_version") or 1):
            continue
        output = proposal.get("output") if isinstance(proposal.get("output"), dict) else {}
        out[study] = {str(a.get("id")): a.get("answer") for a in output.get("criteria") or [] if isinstance(a, dict)}
    return out


def _rows(current: Any, decisions: dict[str, dict[str, Any]]) -> list[tuple[str, str, str, bool]]:
    """(id, side, text, retired): the criteria in force, then retired ones this pilot's decisions cite."""
    rows = [(c.id, c.side, c.text, False) for c in current.all]
    known = {r[0] for r in rows}
    for d in decisions.values():
        cited = current.reason_criterion(d.get("reason_code")) if d.get("outcome") == "EXCLUDE" else None
        if cited and cited not in known:
            side = "inclusion" if str(d.get("reason_code")).startswith("FAILS-") else "exclusion"
            rows.append((cited, side, "", True))
            known.add(cited)
    return rows


def summarise(ws: Path, pilot_id: str, context: Any) -> dict[str, Any]:
    """The counts, per-criterion rows and observations of one pilot (recomputed when read)."""
    draw_record = read_draw(ws, pilot_id)
    current = state(ws, draw_record)
    criteria = context.criteria
    decisions = {s: d for s, d in heads(read_decisions(ws, pilot_id)).items() if s in set(current.studies)}
    decided = len(decisions)
    by_outcome = {o: sum(1 for d in decisions.values() if d.get("outcome") == o) for o in OUTCOMES}
    excludes = by_outcome["EXCLUDE"]
    checklist = {s: {str(c.get("id")): c.get("answer") for c in d.get("criteria") or [] if isinstance(c, dict)}
                 for s, d in decisions.items() if d.get("criteria")}
    drafts = _drafts_for(ws, context, decisions)
    reasons = Counter(criteria.reason_criterion(d.get("reason_code")) for d in decisions.values() if d.get("outcome") == "EXCLUDE")
    rows = []
    for cid, side, text, retired in _rows(criteria, decisions):
        checked = [a[cid] for a in checklist.values() if cid in a]
        drafted = [a[cid] for a in drafts.values() if cid in a]
        differ, both, sources = 0, 0, set()
        for study, answers in drafts.items():
            agent = answers.get(cid)
            if agent not in ("yes", "no"):
                continue
            mine = checklist.get(study, {}).get(cid)
            source = "answers"
            if mine not in ("yes", "no"):
                mine, source = implied(decisions[study], cid, side), "implied"
            if mine not in ("yes", "no"):
                continue
            both += 1
            sources.add(source)
            differ += mine != agent
        rows.append({
            "id": cid, "side": side, "text": text, "retired": retired,
            "exclusions": _share(reasons.get(cid, 0), excludes),
            "checklist_not_reported": _share(sum(a == "not_reported" for a in checked), len(checked)) if checklist else None,
            "draft_not_reported": _share(sum(a == "not_reported" for a in drafted), len(drafted)) if drafts else None,
            "read_differently": (
                {**_share(differ, both), "source": "mixed" if len(sources) > 1 else (next(iter(sources), "implied"))}
                if drafts else None
            ),
        })
    observations, not_computed = _observations(rows, by_outcome, decided, drafts, checklist, criteria)
    records = [
        {"study_id": s, "outcome": decisions[s].get("outcome"), "reason_code": decisions[s].get("reason_code"),
         "criteria_version": int(decisions[s].get("criteria_version") or 1)}
        for s in current.studies if s in decisions
    ]
    return {
        **current.as_dict(),
        "seed": draw_record.get("seed"), "drawn_at": draw_record.get("drawn_at"),
        "snapshot_id": draw_record.get("snapshot_id"), "protocol_fingerprint": draw_record.get("protocol_fingerprint"),
        "criteria_version_drawn": draw_record.get("criteria_version"),
        "criteria_versions_decided": sorted({r["criteria_version"] for r in records}),
        "criteria_version": context.criteria_version,
        "counted": False,
        "by_outcome": by_outcome,
        "criteria": rows,
        "drafts": {"records": len(drafts), "of": decided},
        "checklist": {"records": len(checklist), "of": decided},
        "observations": observations,
        "not_computed": not_computed,
        "records": records,
    }


def _observations(rows, by_outcome, decided, drafts, checklist, criteria):
    """The readings of record (f) as fixed rules over counts; and those that could not be computed."""
    obs: list[dict[str, Any]] = []
    in_force = [r for r in rows if not r["retired"]]
    excludes = by_outcome["EXCLUDE"]
    if decided >= UNCLEAR_MIN and by_outcome["MAYBE"] >= UNCLEAR_SHARE * decided:
        obs.append({"kind": "many_unclear", "criteria": [], "counts": _share(by_outcome["MAYBE"], decided)})
    if excludes >= MOST_WORK_MIN:
        top = max(in_force, key=lambda r: r["exclusions"]["count"], default=None)
        if top is not None and top["exclusions"]["count"] >= MOST_WORK_SHARE * excludes:
            obs.append({"kind": "does_most_work", "criteria": [top["id"]], "counts": dict(top["exclusions"])})
    answers_known = bool(drafts) or bool(checklist)
    if decided >= NEVER_USED_MIN:
        for r in in_force:
            if r["exclusions"]["count"]:
                continue
            if answers_known:
                against = "yes" if r["side"] == "exclusion" else "no"
                said = [a.get(r["id"]) for a in (*drafts.values(), *checklist.values())]
                if against in said:
                    continue
                obs.append({"kind": "never_used", "form": "full", "criteria": [r["id"]],
                            "counts": {"exclusions": 0, "of": excludes, "answered": sum(1 for x in said if x)}})
            else:
                obs.append({"kind": "never_used", "form": "weaker", "criteria": [r["id"]],
                            "counts": {"exclusions": 0, "of": excludes}})
    for r in in_force:
        for source, key in (("drafts", "draft_not_reported"), ("checklist", "checklist_not_reported")):
            share = r[key]
            if share and share["of"] >= HARD_MIN and share["count"] >= HARD_SHARE * share["of"]:
                obs.append({"kind": "hard_to_judge", "criteria": [r["id"]], "source": source, "counts": dict(share)})
    exclusions = [r["id"] for r in in_force if r["side"] == "exclusion"]
    inclusions = [r["id"] for r in in_force if r["side"] == "inclusion"]
    for source, answer_sets in (("drafts", list(drafts.values())), ("checklist", list(checklist.values()))):
        if not answer_sets:
            continue
        for i, a in enumerate(exclusions):
            for b in exclusions[i + 1:]:
                either = [s for s in answer_sets if s.get(a) == "yes" or s.get(b) == "yes"]
                together = sum(1 for s in either if s.get(a) == "yes" and s.get(b) == "yes")
                if len(either) >= TOGETHER_MIN and together >= TOGETHER_SHARE * len(either):
                    obs.append({"kind": "fire_together", "criteria": [a, b], "source": source,
                                "counts": _share(together, len(either))})
    if drafts:
        for exc in exclusions:
            for inc in inclusions:
                both = [s for s in drafts.values() if s.get(exc) in ("yes", "no") and s.get(inc) in ("yes", "no")]
                same = sum(1 for s in both if (s[exc] == "yes") == (s[inc] == "no"))
                if len(both) >= MIRROR_MIN and same >= MIRROR_SHARE * len(both):
                    obs.append({"kind": "mirrored_pair", "criteria": [exc, inc], "source": "drafts",
                                "counts": _share(same, len(both))})
        for r in in_force:
            share = r["read_differently"]
            if share and share["of"] >= DIFFER_MIN and share["count"] >= DIFFER_SHARE * share["of"]:
                obs.append({"kind": "read_differently", "criteria": [r["id"]], "source": share["source"],
                            "counts": {"count": share["count"], "of": share["of"]}})
    not_computed = []
    if not answers_known:
        not_computed += [{"kind": k, "needs": ["agent_check", "checklist"]} for k in ("hard_to_judge", "fire_together")]
    if not drafts:
        not_computed += [{"kind": "mirrored_pair", "needs": ["agent_check"]},
                         {"kind": "read_differently", "needs": ["agent_check"]}]
    return obs, not_computed


def result(ws: Path, pilot_id: str) -> dict[str, Any]:
    """``GET /screening/pilot/{id}/result`` (DoD 13): this pilot, and the one before it beside it."""
    from . import events as ev

    ws = Path(ws)
    context = ev.load_context(ws)
    answer = summarise(ws, pilot_id, context)
    pilots = [p["pilot_id"] for p in list_pilots(ws)]
    index = pilots.index(pilot_id)
    if index > 0:
        earlier = summarise(ws, pilots[index - 1], context)
        answer["previous"] = {k: earlier[k] for k in ("pilot_id", "n", "decided", "by_outcome", "criteria",
                                                         "criteria_versions_decided")}
    else:
        answer["previous"] = None
    return answer


def summary_block(ws: Path, recheck: int) -> dict[str, Any] | None:
    """The ``pilot`` block of ``GET /summary`` (DoD 11b): the open, else the last, pilot."""
    current = open_pilot(ws) or last_pilot(ws)
    if current is None:
        return None
    return {**current.as_dict(), "pilots": len(list_pilots(ws)), "recheck": recheck}


def decided_labels(ws: Path, pilot_id: str, study_ids: Iterable[str] | None = None) -> dict[str, str]:
    """The pilot decisions as reference labels for the agent check (record (i)): Include and Unclear
    count as Include, Exclude as Exclude."""
    current = state(ws, read_draw(ws, pilot_id))
    decisions = {s: d for s, d in heads(read_decisions(ws, pilot_id)).items() if s in set(current.studies)}
    wanted = set(study_ids) if study_ids is not None else set(decisions)
    return {s: ("EXCLUDE" if d.get("outcome") == "EXCLUDE" else "INCLUDE") for s, d in decisions.items() if s in wanted}
