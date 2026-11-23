"""Decisions stored from the agent's drafts, declared (H-adopted-decisions-disclosure).

Decision 2026-11-22 ("H-adopted-decisions-disclosure"): a decision event is a
human decision (``method: HUMAN``) whether or not the reviewer read the record;
when drafts were stored as decisions in bulk, the reviewer *declares* it here.
Nothing in the event log is rewritten, and the Contract v1 ``ScreeningDecision``
model is unchanged.

**The file.** ``audit/adoption_declarations.jsonl``, append-only, one JSON object
per line, three kinds:

- ``declaration``: the decision events "stored from the agent's draft without
  being read one by one" (``event_id``, ``study_id``, ``outcome`` each), the
  outcome counts, who (the workspace's screener id), when (the engine's clock),
  an optional note, and the sample drawn from its exclusions if any (size, seed,
  the study ids);
- ``withdrawal``: names declared events the reviewer has since read;
- ``sample_result``: the reviewer has read the sample of one declaration; the
  engine counts the sampled decisions whose outcome is no longer the stored one.

**Who wrote a line.** Each line is written with one journal row naming its id and
the SHA-256 of the line. A line is applied only when the journal holds that row,
so a line typed into the file by hand is not applied (``unconfirmed``); a
journal row whose line is missing or changed is reported (``removed``). Both
make the Publish check "Look at this"; neither blocks publication (answer 3).

**What is declared.** An event is declared while a confirmed declaration names
it and no later withdrawal does. A record counts as stored from a draft only
while its *current winning* decision is a declared event: a record decided again
in Triage (a new event) is the reviewer's reading, and leaves the declared set.

**Candidates.** The current winning decisions whose note says they were adopted
or stored in bulk (answer 2), offered for confirmation and never applied silently.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DECLARATIONS_FILE = Path("audit") / "adoption_declarations.jsonl"
JOURNAL_FILE = Path("audit") / "journal.jsonl"
SCHEMA = "nexus.adoption-declaration.v1"
#: The decided phrase (answer 6), in every place it is stated.
PHRASE = "stored from the agent's draft without being read one by one"
ACTIONS = {
    "declaration": "SCREENING_ADOPTION_DECLARED",
    "withdrawal": "SCREENING_ADOPTION_WITHDRAWN",
    "sample_result": "SCREENING_ADOPTION_SAMPLE_READ",
}
ID_PREFIX = {"declaration": "ADD-", "withdrawal": "ADW-", "sample_result": "ADS-"}
OUTCOMES = ("INCLUDE", "EXCLUDE", "MAYBE")
#: The note words that make a decision a candidate (answer 2; PROPOSED item 2).
CANDIDATE_PATTERN = re.compile(r"\badopt(?:ed|ion|ing)?\b|\bin bulk\b", re.IGNORECASE)
MAX_NOTE_CHARS = 500
MAX_EVENTS = 20_000

# Refusal codes (console refusals; screening API contract §7).
ADOPTION_CONFIRM_REQUIRED = "ADOPTION_CONFIRM_REQUIRED"
ADOPTION_EVENT_NOT_WINNING = "ADOPTION_EVENT_NOT_WINNING"
ADOPTION_ALREADY_DECLARED = "ADOPTION_ALREADY_DECLARED"
ADOPTION_DECLARATION_INVALID = "ADOPTION_DECLARATION_INVALID"
ADOPTION_NOT_DECLARED = "ADOPTION_NOT_DECLARED"
ADOPTION_SAMPLE_INVALID = "ADOPTION_SAMPLE_INVALID"
CODES = frozenset({
    ADOPTION_CONFIRM_REQUIRED, ADOPTION_EVENT_NOT_WINNING, ADOPTION_ALREADY_DECLARED,
    ADOPTION_DECLARATION_INVALID, ADOPTION_NOT_DECLARED, ADOPTION_SAMPLE_INVALID,
})


class AdoptionRefused(ValueError):
    def __init__(self, status: int, code: str, message: str, **details: Any):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def is_candidate(event: Mapping[str, Any]) -> bool:
    note = event.get("note")
    return isinstance(note, str) and bool(CANDIDATE_PATTERN.search(note))


def _line_text(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(path: Path) -> str | None:
    from . import read_store

    try:
        return read_store.read_text(path)
    except OSError:
        return None


@dataclass
class Ledger:
    """The confirmed lines of the file, in file order, and what does not match the journal."""

    lines: list[dict[str, Any]] = field(default_factory=list)
    #: Ids the journal records whose line is missing or not the one recorded.
    removed: list[str] = field(default_factory=list)
    #: Ids of lines in the file the journal does not record (not applied).
    unconfirmed: list[str] = field(default_factory=list)

    @property
    def declarations(self) -> list[dict[str, Any]]:
        return [r for r in self.lines if r["kind"] == "declaration"]

    @property
    def sample_results(self) -> dict[str, dict[str, Any]]:
        """The first recorded result of each declaration's sample."""
        out: dict[str, dict[str, Any]] = {}
        for row in self.lines:
            if row["kind"] == "sample_result":
                out.setdefault(str(row.get("declaration_id")), row)
        return out

    def declared_events(self) -> dict[str, dict[str, Any]]:
        """Event id → ``{event_id, study_id, outcome, declaration_id}``, declared and not withdrawn."""
        active: dict[str, dict[str, Any]] = {}
        for row in self.lines:
            if row["kind"] == "declaration":
                for item in row.get("events") or []:
                    active[str(item["event_id"])] = {**item, "declaration_id": row["declaration_id"]}
            elif row["kind"] == "withdrawal":
                for event_id in row.get("event_ids") or []:
                    active.pop(str(event_id), None)
        return active

    @property
    def intact(self) -> bool:
        return not self.removed and not self.unconfirmed


def _valid(row: Any) -> bool:
    if not isinstance(row, dict) or row.get("schema") != SCHEMA or row.get("kind") not in ACTIONS:
        return False
    if not str(row.get("id") or "").startswith(ID_PREFIX[row["kind"]]):
        return False
    if row["kind"] == "declaration":
        events = row.get("events")
        return isinstance(events, list) and bool(events) and all(
            isinstance(e, dict) and e.get("event_id") and e.get("study_id") and e.get("outcome") in OUTCOMES
            for e in events
        ) and row.get("declaration_id") == row["id"]
    if row["kind"] == "withdrawal":
        return isinstance(row.get("event_ids"), list) and bool(row["event_ids"])
    return bool(row.get("declaration_id")) and isinstance(row.get("changed_study_ids"), list)


def read_ledger(workspace: Path | str) -> Ledger:
    """The file's lines the journal confirms; a display route reads both through the read store."""
    ws = Path(workspace)
    text = _read(ws / DECLARATIONS_FILE) or ""
    journal = _read(ws / JOURNAL_FILE) or ""
    recorded: dict[str, str] = {}
    wanted = tuple(ACTIONS.values())
    for line in journal.splitlines():
        if not any(action in line for action in wanted):
            continue  # most journal rows are not ours; skip parsing them
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or row.get("action") not in wanted:
            continue
        params = row.get("parameters") if isinstance(row.get("parameters"), dict) else {}
        if params.get("line_id") and params.get("line_sha256"):
            recorded[str(params["line_id"])] = str(params["line_sha256"])
    ledger = Ledger()
    seen: set[str] = set()
    for raw in text.splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except ValueError:
            ledger.unconfirmed.append("(unreadable line)")
            continue
        if not _valid(row):
            ledger.unconfirmed.append(str(row.get("id") if isinstance(row, dict) else "(not an object)"))
            continue
        line_id = str(row["id"])
        if recorded.get(line_id) != _sha(raw.strip()) or line_id in seen:
            ledger.unconfirmed.append(line_id)
            continue
        seen.add(line_id)
        ledger.lines.append(row)
    ledger.removed = sorted(set(recorded) - seen)
    return ledger


# --- the state the screens show -------------------------------------------------------


def state(
    workspace: Path | str, winners: Mapping[str, Mapping[str, Any]], *, ledger: Ledger | None = None,
    list_candidates: bool = False,
) -> dict[str, Any]:
    """What is declared among the current winning decisions, the candidates, and each sample.

    ``winners`` is ``study_id → winning event`` for the workspace's screener (``_state``).
    """
    ledger = ledger if ledger is not None else read_ledger(workspace)
    active = ledger.declared_events()
    declared = {s: w for s, w in winners.items() if str(w.get("event_id")) in active}
    by_outcome = dict.fromkeys(OUTCOMES, 0)
    for winner in declared.values():
        by_outcome[str(winner["outcome"])] += 1
    candidates = {s: w for s, w in winners.items() if is_candidate(w)}
    undeclared = {s: w for s, w in candidates.items() if s not in declared}
    samples = []
    results = ledger.sample_results
    for row in ledger.declarations:
        sample = row.get("sample")
        if not isinstance(sample, dict):
            continue
        result = results.get(row["declaration_id"])
        samples.append({
            "declaration_id": row["declaration_id"],
            "size": int(sample.get("size") or 0),
            "seed": sample.get("seed"),
            "study_ids": list(sample.get("study_ids") or []),
            "read": result is not None,
            "changed": len(result.get("changed_study_ids") or []) if result else None,
            "recorded_at": result.get("recorded_at") if result else None,
        })
    excluded_declared = by_outcome["EXCLUDE"]
    owed = [s for s in samples if not s["read"]]
    # PROPOSED item 6: with declared exclusions and no sample drawn, a sample is still owed (size unknown).
    no_sample_drawn = excluded_declared > 0 and not samples
    out: dict[str, Any] = {
        "phrase": PHRASE,
        "declared": len(declared),
        "declared_by_outcome": by_outcome,
        "declared_study_ids": sorted(declared),
        "candidates": len(candidates),
        "undeclared_candidates": len(undeclared),
        "undeclared_by_outcome": {o: sum(1 for w in undeclared.values() if w["outcome"] == o) for o in OUTCOMES},
        "declarations": [
            {k: row.get(k) for k in ("declaration_id", "declared_by", "declared_at", "note", "counts", "sample")}
            for row in ledger.declarations
        ],
        "samples": samples,
        "sample_owed": bool(owed) or no_sample_drawn,
        "sample_owed_size": sum(s["size"] for s in owed) if owed else None,
        "no_sample_drawn": no_sample_drawn,
        "integrity": {"removed": list(ledger.removed), "unconfirmed": list(ledger.unconfirmed)},
    }
    if list_candidates:
        out["candidate_list"] = [
            {"event_id": w["event_id"], "study_id": s, "outcome": w["outcome"], "note": w.get("note"),
             "declared": s in declared}
            for s, w in sorted(candidates.items())
        ]
    return out


# --- writes -----------------------------------------------------------------------------


def _append(ws: Path, kind: str, row: dict[str, Any], description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """One line, then its journal row; a journal row that cannot be written takes the line back out."""
    from scholar_harness.workspace.audit import append_event

    text = _line_text(row)
    path = ws / DECLARATIONS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    size = path.stat().st_size if path.exists() else 0
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(text + "\n")
    try:
        append_event(
            ws, ACTIONS[kind], description, agent="scholar-harness/console",
            outputs=[DECLARATIONS_FILE.as_posix()],
            parameters={"line_id": row["id"], "line_sha256": _sha(text), **parameters},
            refresh_index=False,
        )
    except OSError:
        with path.open("r+b") as handle:
            handle.truncate(size)
        raise
    return row


def _note(note: str | None) -> str | None:
    text = (note or "").strip()
    if len(text) > MAX_NOTE_CHARS:
        raise AdoptionRefused(422, ADOPTION_DECLARATION_INVALID, f"the note is longer than {MAX_NOTE_CHARS} characters")
    return text or None


def declare(
    workspace: Path | str, winners: Mapping[str, Mapping[str, Any]], *, event_ids: Iterable[str],
    declared_by: str, declared_at: str, note: str | None = None, sample: Mapping[str, Any] | None = None,
    protocol_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Record one declaration. The caller holds the events lock and passes the current winners."""
    ws = Path(workspace)
    ids = [str(e) for e in event_ids]
    if not ids:
        raise AdoptionRefused(422, ADOPTION_DECLARATION_INVALID, "name at least one decision event")
    if len(ids) > MAX_EVENTS:
        raise AdoptionRefused(422, ADOPTION_DECLARATION_INVALID, f"at most {MAX_EVENTS} decisions per declaration")
    by_event = {str(w.get("event_id")): (s, w) for s, w in winners.items()}
    not_winning = [e for e in ids if e not in by_event]
    if not_winning:
        raise AdoptionRefused(
            409, ADOPTION_EVENT_NOT_WINNING,
            f"{len(not_winning)} event id(s) are not a current winning decision", event_ids=not_winning[:20],
        )
    studies = [by_event[e][0] for e in ids]
    twice = sorted({s for s in studies if studies.count(s) > 1})
    ledger = read_ledger(ws)
    active = ledger.declared_events()
    already = sorted({by_event[e][0] for e in ids if e in active})
    if twice or already:
        raise AdoptionRefused(
            409, ADOPTION_ALREADY_DECLARED,
            "a record is named twice" if twice else f"{len(already)} record(s) are already declared",
            study_ids=(twice or already)[:20],
        )
    events = [{"event_id": e, "study_id": by_event[e][0], "outcome": str(by_event[e][1]["outcome"])} for e in ids]
    counts = {o: sum(1 for e in events if e["outcome"] == o) for o in OUTCOMES}
    drawn = _sample(events, sample) if sample is not None else None
    line_id = ID_PREFIX["declaration"] + uuid.uuid4().hex[:24]
    row = {
        "schema": SCHEMA, "kind": "declaration", "id": line_id, "declaration_id": line_id,
        "events": events, "counts": counts, "declared_by": declared_by, "declared_at": declared_at,
        "note": _note(note), "sample": drawn, "protocol_fingerprint": protocol_fingerprint,
    }
    return _append(
        ws, "declaration", row,
        f"Declared {len(events)} decisions {PHRASE} ({counts['EXCLUDE']} exclude, {counts['INCLUDE']} include, "
        f"{counts['MAYBE']} unclear); the decision events are unchanged",
        {"declaration_id": line_id, "counts": counts, "declared_by": declared_by,
         "sample": {k: drawn[k] for k in ("size", "seed")} if drawn else None},
    )


def _sample(events: list[dict[str, Any]], sample: Mapping[str, Any]) -> dict[str, Any]:
    """The sample of declared exclusions: drawn with the seed, or the study ids given (PROPOSED item 5)."""
    exclusions = sorted(e["study_id"] for e in events if e["outcome"] == "EXCLUDE")
    try:
        size = int(sample.get("size"))
        seed = int(sample.get("seed"))
    except (TypeError, ValueError) as exc:
        raise AdoptionRefused(422, ADOPTION_SAMPLE_INVALID, "a sample needs a whole-number size and seed") from exc
    if not 1 <= size <= len(exclusions):
        raise AdoptionRefused(
            422, ADOPTION_SAMPLE_INVALID, f"the sample size must be between 1 and the {len(exclusions)} declared exclusions",
        )
    given = sample.get("study_ids")
    if given is not None:
        chosen = [str(s) for s in given]
        if len(chosen) != size or len(set(chosen)) != size or not set(chosen) <= set(exclusions):
            raise AdoptionRefused(
                422, ADOPTION_SAMPLE_INVALID, "the sample's study ids must be distinct declared exclusions, as many as its size",
            )
        how = "given"
    else:
        chosen = random.Random(seed).sample(exclusions, size)
        how = "drawn"
    return {"size": size, "seed": seed, "study_ids": sorted(chosen), "how": how}


def withdraw(
    workspace: Path | str, *, event_ids: Iterable[str], withdrawn_by: str, withdrawn_at: str, note: str | None = None,
) -> dict[str, Any]:
    ws = Path(workspace)
    ids = sorted({str(e) for e in event_ids})
    if not ids:
        raise AdoptionRefused(422, ADOPTION_DECLARATION_INVALID, "name at least one declared event")
    active = read_ledger(ws).declared_events()
    missing = [e for e in ids if e not in active]
    if missing:
        raise AdoptionRefused(409, ADOPTION_NOT_DECLARED, f"{len(missing)} event id(s) are not declared", event_ids=missing[:20])
    line_id = ID_PREFIX["withdrawal"] + uuid.uuid4().hex[:24]
    row = {
        "schema": SCHEMA, "kind": "withdrawal", "id": line_id, "event_ids": ids,
        "withdrawn_by": withdrawn_by, "withdrawn_at": withdrawn_at, "note": _note(note),
    }
    return _append(
        ws, "withdrawal", row, f"Withdrew {len(ids)} decisions from a declaration: the reviewer has since read them",
        {"withdrawn_by": withdrawn_by, "count": len(ids)},
    )


def record_sample_result(
    workspace: Path | str, winners: Mapping[str, Mapping[str, Any]], *, declaration_id: str, recorded_by: str,
    recorded_at: str, note: str | None = None,
) -> dict[str, Any]:
    """The reviewer has read every sampled record; the engine counts those whose outcome changed (PROPOSED item 7)."""
    ws = Path(workspace)
    ledger = read_ledger(ws)
    row = next((r for r in ledger.declarations if r["declaration_id"] == declaration_id), None)
    if row is None or not isinstance(row.get("sample"), dict):
        raise AdoptionRefused(409, ADOPTION_SAMPLE_INVALID, "no declaration with a sample has that id")
    if declaration_id in ledger.sample_results:
        raise AdoptionRefused(409, ADOPTION_SAMPLE_INVALID, "this sample's result is already recorded")
    stored = {e["study_id"]: e for e in row["events"]}
    changed = []
    for study in row["sample"]["study_ids"]:
        winner = winners.get(study)
        if winner is None:
            raise AdoptionRefused(
                409, ADOPTION_SAMPLE_INVALID, f"{study} has no current decision; decide it before recording the result",
            )
        if str(winner["outcome"]) != stored[study]["outcome"]:
            changed.append(study)
    line_id = ID_PREFIX["sample_result"] + uuid.uuid4().hex[:24]
    result = {
        "schema": SCHEMA, "kind": "sample_result", "id": line_id, "declaration_id": declaration_id,
        "read": int(row["sample"]["size"]), "changed_study_ids": sorted(changed),
        "recorded_by": recorded_by, "recorded_at": recorded_at, "note": _note(note),
    }
    return _append(
        ws, "sample_result", result,
        f"Read the sample of {result['read']} declared exclusions; {len(changed)} decisions changed",
        {"declaration_id": declaration_id, "read": result["read"], "changed": len(changed), "recorded_by": recorded_by},
    )


def declared_in_decision_files(folder: Path | str, ledger: Ledger) -> dict[str, str]:
    """``study_id → outcome`` of the decisions in ``folder``'s ``batch_NNN_decisions.json`` files whose
    event is declared (item 6: the charting table marks a kept study whose inclusion was declared).

    The published records do not carry the decision's event id; the decision files of the same
    round do (``event_id``), so a record is matched by the event that was published, never by its id
    alone.
    """
    active = ledger.declared_events()
    if not active:
        return {}
    found: dict[str, str] = {}
    for path in sorted(Path(folder).glob("batch_*_decisions.json")):
        try:
            payload = json.loads(_read(path) or "")
        except ValueError:
            continue
        for entry in (payload.get("decisions") if isinstance(payload, dict) else None) or []:
            if isinstance(entry, dict) and str(entry.get("event_id") or "") in active:
                found[str(entry.get("workspace_id") or entry.get("study_id"))] = str(entry.get("decision"))
    return found
