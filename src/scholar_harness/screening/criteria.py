"""The screening criteria in force (M11b part A, decision 2026-11-21 items 1 to 4).

A criteria revision is an **amendment beside the signed protocol**, as the
method amendments of H-screening-drafts are (``screening/method.py``):
``protocol.json``, its fingerprint, the accepted corpus, the batch files and
every decision event keep their bytes and their binding. Each revision is one
line of ``audit/criteria_amendments.jsonl`` and one ``PROTOCOL_CRITERIA_AMENDED``
journal row. The criteria in force are the signed list plus the amendments made
under the current protocol fingerprint, oldest first; each amendment raises the
**criteria version** (1 is the signed list), which the engine stamps on every
new decision event and every new draft.

This module is the one reader. Every consumer of the criteria (the reason check
at intake, the agent run and its estimate, the draft reader, Triage's criteria
and checklist, the agreement read, the MCP record tool, the export) asks
:func:`criteria_in_force`; ``tests/unit/test_criteria_readers.py`` fails on a
new reader of ``screening_criteria`` that bypasses it.

Ids (item 3): a reword keeps the id; a split, a merge and a removal retire the
ids they replace; a new id takes the next number on its side after every id
ever used, retired ones included, so an id is never reused.

Shown again (item 2): after a revision, a counted decision made under an
earlier version is shown again when it is an Include or an Unclear, or an
Exclude whose reason cites a criterion the revision touched. Until it is
decided again its batch is not fully decided (the record is left out of the
batch decisions file, so approval and collect refuse; decision 2026-11-21, M11b
part A, item 4).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

AMENDMENTS_FILE = Path("audit") / "criteria_amendments.jsonl"
AMENDED_ACTION = "PROTOCOL_CRITERIA_AMENDED"
CRITERIA_FILE = "SCREENING_CRITERIA.md"
AMENDED_DIR = Path("audit") / "amended"

# Refusal codes (screening API contract §7).
CRITERIA_AMENDMENT_INVALID = "CRITERIA_AMENDMENT_INVALID"
CRITERIA_AMENDMENT_NO_BATCHES = "CRITERIA_AMENDMENT_NO_BATCHES"
CRITERIA_AMENDMENT_AFTER_APPROVAL = "CRITERIA_AMENDMENT_AFTER_APPROVAL"
CRITERIA_SIDE_EMPTY = "CRITERIA_SIDE_EMPTY"
#: A current batch was decided through the file hand-off (a worker recommendation or a
#: decisions file not built from events): a revision could not show those decisions again.
CRITERIA_AMENDMENT_HANDOFF = "CRITERIA_AMENDMENT_HANDOFF"
#: ``amend_criteria(pilot_id=OPEN_PILOT)``: record the pilot open at the time of the revision,
#: read under the events lock (M11b part B).
OPEN_PILOT = object()
#: At most this many texts in a split (review round 1, F5).
MAX_SPLIT_TEXTS = 10
#: The file hand-off worker reads the signed wording from the batch file; once
#: the criteria are amended it refuses (decision 2026-11-21, M11b part A, item 1).
CRITERIA_AMENDED_USE_ENGINE = "CRITERIA_AMENDED_USE_ENGINE"

SIDES = ("inclusion", "exclusion")
PREFIX = {"inclusion": "INC", "exclusion": "EXC"}
OPS = ("reword", "split", "merge", "remove", "add", "reason_category")
#: The ops after which a decision may no longer hold (a change of reason
#: category alone changes no test, so it shows nothing again).
WORDING_OPS = frozenset({"reword", "split", "merge", "remove", "add"})
MAX_REASON_CHARS = 500
MAX_TEXT_CHARS = 2_000
OUTCOMES = ("INCLUDE", "MAYBE", "EXCLUDE")

_NUMBERED = re.compile(r"^(INC|EXC)-(\d+)$")


class AmendmentRefused(ValueError):
    """A revision the engine does not record; ``code`` is the typed refusal."""

    def __init__(self, code: str, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class Criterion:
    id: str
    side: str
    text: str
    reason_category: str | None = None
    maps_to_rqs: tuple[str, ...] = ()
    #: The criteria version this wording dates from (1: the signed protocol).
    since_version: int = 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "side": self.side,
            "text": self.text,
            "reason_category": self.reason_category,
            "since_version": self.since_version,
        }

    def protocol_item(self) -> dict[str, Any]:
        """The criterion as the protocol writes it (``ScreeningCriterion``)."""
        return {
            "id": self.id,
            "criterion": self.text,
            "maps_to_rqs": list(self.maps_to_rqs),
            "reason_category": self.reason_category,
        }


@dataclass(frozen=True)
class CriteriaInForce:
    version: int
    inclusion: tuple[Criterion, ...]
    exclusion: tuple[Criterion, ...]
    #: Every id ever retired under this protocol, oldest first.
    retired: tuple[str, ...] = ()
    #: The amendment rows applied, oldest first.
    amendments: tuple[dict[str, Any], ...] = ()
    protocol_fingerprint: str | None = None
    #: Every id ever used on a side (signed and amended), for numbering.
    used: tuple[str, ...] = field(default=(), repr=False)

    # --- reading -----------------------------------------------------------

    def side(self, side: str) -> tuple[Criterion, ...]:
        return self.inclusion if side == "inclusion" else self.exclusion

    @property
    def all(self) -> tuple[Criterion, ...]:
        return self.inclusion + self.exclusion

    def ids(self, side: str) -> frozenset[str]:
        return frozenset(c.id for c in self.side(side))

    def get(self, criterion_id: str) -> Criterion | None:
        return next((c for c in self.all if c.id == criterion_id), None)

    def reason_criterion(self, code: str | None) -> str | None:
        """The criterion id a reason code cites (``EXC-n`` or ``FAILS-INC-n``)."""
        if not code:
            return None
        code = str(code)
        return code[len("FAILS-"):] if code.startswith("FAILS-") else code

    def valid_reason(self, code: str | None) -> bool:
        """A reason code citing a criterion in force."""
        if not code:
            return False
        if code in self.ids("exclusion"):
            return True
        return code.startswith("FAILS-") and code[len("FAILS-"):] in self.ids("inclusion")

    def retired_ids(self, side: str) -> frozenset[str]:
        return frozenset(
            str(f.get("id"))
            for r in self.amendments
            if r.get("side") == side and r.get("op") in ("split", "merge", "remove")
            for f in r.get("from") or [] if isinstance(f, dict)
        )

    def retired_reason(self, code: str | None) -> bool:
        """A reason code citing a retired criterion (valid on events made before)."""
        if not code:
            return False
        if code.startswith("FAILS-"):
            return code[len("FAILS-"):] in self.retired_ids("inclusion")
        return code in self.retired_ids("exclusion")

    def protocol_block(self) -> dict[str, Any]:
        """The ``screening_criteria`` block in force, in the protocol's shape."""
        return {
            "inclusion": [c.protocol_item() for c in self.inclusion],
            "exclusion": [c.protocol_item() for c in self.exclusion],
        }

    def protocol_in_force(self, protocol: dict[str, Any]) -> dict[str, Any]:
        """A copy of ``protocol`` whose criteria are the ones in force.

        For readers that take a protocol dict (the agent run's prompt). Never
        fingerprint this copy: the fingerprint is the signed protocol's.
        """
        out = copy.deepcopy(protocol)
        block = dict(out.get("screening_criteria") or {})
        block.update(self.protocol_block())
        out["screening_criteria"] = block
        return out

    def next_id(self, side: str, already: Iterable[str] = ()) -> str:
        """The next unused number on ``side``, after every id ever used."""
        prefix = PREFIX[side]
        numbers = [
            int(m.group(2))
            for cid in (*self.used, *already)
            if (m := _NUMBERED.match(cid)) and m.group(1) == prefix
        ]
        width = max([2, *(len(m.group(2)) for cid in self.used if (m := _NUMBERED.match(cid)))])
        return f"{prefix}-{(max(numbers, default=0) + 1):0{width}d}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "criteria_version": self.version,
            "criteria": [c.as_dict() for c in self.all],
            "retired": list(self.retired),
            "amendments": [public_row(a) for a in self.amendments],
        }


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "amendment_id", "op", "side", "from", "to", "reason", "criteria_version_before",
        "criteria_version_after", "protocol_fingerprint", "pilot_id", "decided_at_time", "shown_again",
        "amended_by", "amended_at",
    )
    return {k: row.get(k) for k in keys}


# --- reading the protocol and the amendments ----------------------------------


def _text(item: dict[str, Any]) -> str:
    return str(item.get("criterion") or item.get("description") or item.get("text") or "")


def signed_criteria(protocol: dict[str, Any] | None, fingerprint: str | None = None) -> CriteriaInForce:
    """Version 1: the criteria of the signed protocol."""
    block = (protocol or {}).get("screening_criteria") if isinstance(protocol, dict) else None
    block = block if isinstance(block, dict) else {}
    sides: dict[str, list[Criterion]] = {}
    for side in SIDES:
        sides[side] = [
            Criterion(
                id=str(item["id"]),
                side=side,
                text=_text(item),
                reason_category=item.get("reason_category"),
                maps_to_rqs=tuple(str(r) for r in item.get("maps_to_rqs") or []),
            )
            for item in block.get(side) or []
            if isinstance(item, dict) and item.get("id")
        ]
    used = tuple(c.id for side in SIDES for c in sides[side])
    return CriteriaInForce(1, tuple(sides["inclusion"]), tuple(sides["exclusion"]), (), (), fingerprint, used)


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def read_rows(workspace: Path | str, fingerprint: str | None, *, until: datetime | None = None) -> list[dict[str, Any]]:
    """The amendment rows made under ``fingerprint``, in file order; an unreadable line is skipped."""
    path = Path(workspace) / AMENDMENTS_FILE
    if fingerprint is None or not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or row.get("protocol_fingerprint") != fingerprint or row.get("op") not in OPS:
            continue
        if until is not None and ((when := _time(row.get("amended_at"))) is None or when > until):
            continue
        rows.append(row)
    return rows


def apply_rows(state: CriteriaInForce, rows: Iterable[dict[str, Any]]) -> CriteriaInForce:
    """``state`` with each recorded row applied in order (the rows carry their result)."""
    for row in rows:
        side = row.get("side")
        if side not in SIDES:
            continue
        before = list(state.side(side))
        gone = {str(f.get("id")) for f in row.get("from") or [] if isinstance(f, dict)}
        new_items = [
            Criterion(
                id=str(t["id"]), side=side, text=str(t.get("text") or ""),
                reason_category=t.get("reason_category"),
                maps_to_rqs=tuple(str(r) for r in t.get("maps_to_rqs") or []),
                since_version=int(row.get("criteria_version_after") or state.version + 1),
            )
            for t in row.get("to") or [] if isinstance(t, dict) and t.get("id")
        ]
        op = row.get("op")
        if op in ("reword", "reason_category"):
            replacement = {c.id: c for c in new_items}
            after = []
            for c in before:
                new = replacement.get(c.id)
                if new is None:
                    after.append(c)
                elif op == "reason_category":
                    after.append(replace(c, reason_category=new.reason_category))
                else:
                    after.append(new)
            retired: tuple[str, ...] = ()
        elif op == "add":
            after = before + new_items
            retired = ()
        else:  # split, merge, remove: the replacement takes the first retired place
            after, placed = [], False
            for c in before:
                if c.id in gone:
                    if not placed:
                        after.extend(new_items)
                        placed = True
                    continue
                after.append(c)
            if not placed:
                after.extend(new_items)
            retired = tuple(i for i in (str(f.get("id")) for f in row.get("from") or [] if isinstance(f, dict)) if i)
        used = state.used + tuple(c.id for c in new_items if c.id not in state.used)
        sides = {s: tuple(after) if s == side else state.side(s) for s in SIDES}
        state = CriteriaInForce(
            version=int(row.get("criteria_version_after") or state.version + 1),
            inclusion=sides["inclusion"],
            exclusion=sides["exclusion"],
            retired=state.retired + tuple(r for r in retired if r not in state.retired),
            amendments=state.amendments + (row,),
            protocol_fingerprint=state.protocol_fingerprint,
            used=used,
        )
    return state


def _protocol(workspace: Path | str) -> dict[str, Any] | None:
    try:
        raw = json.loads((Path(workspace) / "protocol.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return raw if isinstance(raw, dict) else None


def criteria_from_protocol(
    workspace: Path | str, protocol: dict[str, Any] | None, fingerprint: str | None, *, until: datetime | None = None
) -> CriteriaInForce:
    """The criteria in force for a caller that already holds the protocol and its fingerprint."""
    signed = signed_criteria(protocol, fingerprint)
    if not (Path(workspace) / AMENDMENTS_FILE).is_file():
        return signed
    return apply_rows(signed, read_rows(workspace, fingerprint, until=until))


def criteria_in_force(workspace: Path | str, *, until: datetime | None = None) -> CriteriaInForce:
    """The one reader: the signed criteria plus the amendments under the current fingerprint.

    With ``until``, only the amendments made at or before it apply (the
    methods paragraph states the criteria at publication).
    """
    from .method import protocol_fingerprint

    protocol = _protocol(workspace)
    if not (Path(workspace) / AMENDMENTS_FILE).is_file():
        return signed_criteria(protocol)  # no amendment: nothing to bind, nothing fingerprinted
    fingerprint = protocol_fingerprint(protocol)
    return criteria_from_protocol(workspace, protocol, fingerprint, until=until)


def protocol_in_force(workspace: Path | str) -> dict[str, Any]:
    """``protocol.json`` with its criteria replaced by the ones in force."""
    protocol = _protocol(workspace)
    if protocol is None:
        raise FileNotFoundError("the workspace has no readable protocol.json")
    return criteria_in_force(workspace).protocol_in_force(protocol)


def event_version(record: dict[str, Any]) -> int:
    """The criteria version a decision event or a draft names (1 when it has none)."""
    try:
        return max(1, int(record.get("criteria_version") or 1))
    except (TypeError, ValueError):
        return 1


# --- shown again ----------------------------------------------------------------


def _touched(row: dict[str, Any]) -> set[str]:
    if row.get("op") == "reword":
        return {str(f.get("id")) for f in row.get("from") or [] if isinstance(f, dict)}
    if row.get("op") in ("split", "merge", "remove"):
        return {str(f.get("id")) for f in row.get("from") or [] if isinstance(f, dict)}
    return set()


def shown_again(decision: dict[str, Any], current: CriteriaInForce) -> bool:
    """True when a revision after the decision's version could change it.

    Include and Unclear: after any change of wording (an added criterion
    included). Exclude: when its reason cites a criterion a later revision
    reworded, split, merged or removed. A change of reason category alone
    shows nothing again.
    """
    made_under = event_version(decision)
    later = [
        r for r in current.amendments
        if r.get("op") in WORDING_OPS and int(r.get("criteria_version_after") or 0) > made_under
    ]
    if not later:
        return False
    outcome = decision.get("outcome")
    if outcome in ("INCLUDE", "MAYBE"):
        return True
    if outcome == "EXCLUDE":
        cited = current.reason_criterion(decision.get("reason_code"))
        return any(cited in _touched(r) for r in later)
    return False


# --- recording a revision -------------------------------------------------------


@dataclass(frozen=True)
class Plan:
    """What a revision would record: the row without its id, time and counts."""

    op: str
    side: str
    from_: tuple[dict[str, Any], ...]
    to: tuple[dict[str, Any], ...]
    after: CriteriaInForce

    @property
    def new_ids(self) -> list[str]:
        before = {f["id"] for f in self.from_}
        return [t["id"] for t in self.to if t["id"] not in before]

    @property
    def retired_ids(self) -> list[str]:
        if self.op in ("split", "merge", "remove"):
            return [f["id"] for f in self.from_]
        return []


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{what} must be non-empty text")
    text = " ".join(value.split())
    if len(text) > MAX_TEXT_CHARS:
        raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{what} is longer than {MAX_TEXT_CHARS} characters")
    return text


def _item(c: Criterion) -> dict[str, Any]:
    return {"id": c.id, "text": c.text, "reason_category": c.reason_category, "maps_to_rqs": list(c.maps_to_rqs)}


def plan_amendment(
    current: CriteriaInForce,
    *,
    op: str,
    side: str,
    ids: list[str] | None,
    text: str | list[str] | None = None,
    reason_category: str | None = None,
    reason_category_given: bool = False,
) -> Plan:
    """Check one revision against the criteria in force and say what it would record.

    Pure: refuses (``AmendmentRefused``) an unknown op or side, an unknown or
    retired id, an id of the other side, a revision that changes nothing, and
    one that leaves a side with no criterion (``CRITERIA_SIDE_EMPTY``).
    """
    if op not in OPS:
        raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"op must be one of {', '.join(OPS)}")
    if side not in SIDES:
        raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "side must be inclusion or exclusion")
    ids = [str(i) for i in (ids or [])]
    if len(set(ids)) != len(ids):
        raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "an id is named twice")
    for cid in ids:
        if cid in current.retired:
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{cid} is retired; a retired criterion is not revised")
        found = current.get(cid)
        if found is None:
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{cid} is not a criterion in force")
        if found.side != side:
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{cid} is an {found.side} criterion, not {side}")
    wanted = {"reword": (1, 1), "split": (1, 1), "merge": (2, None), "remove": (1, 1), "add": (0, 0),
              "reason_category": (1, 1)}[op]
    if len(ids) < wanted[0] or (wanted[1] is not None and len(ids) > wanted[1]):
        count = "no id" if wanted == (0, 0) else ("at least two ids" if op == "merge" else "exactly one id")
        raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{op} names {count}")
    olds = [current.get(cid) for cid in ids]
    from_ = tuple(_item(c) for c in olds if c is not None)
    category = (reason_category or None) if reason_category_given else None
    if category is not None:
        category = _clean_text(category, "reason_category")
    to: list[dict[str, Any]] = []
    if op == "reword":
        if isinstance(text, list):
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "reword takes one text")
        new_text = _clean_text(text, "text")
        old = olds[0]
        new_category = category if reason_category_given else old.reason_category
        if new_text == old.text:
            # Review round 1, F2: a change of reason category alone is its own op, which
            # shows nothing again and reads as what it is in the methods paragraph.
            hint = "; to change only its reason category use op reason_category" if new_category != old.reason_category else ""
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{old.id} already reads so; nothing is reworded{hint}")
        to = [{"id": old.id, "text": new_text, "reason_category": new_category, "maps_to_rqs": list(old.maps_to_rqs)}]
    elif op == "reason_category":
        old = olds[0]
        if not reason_category_given:
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "reason_category is required (null clears it)")
        if category == old.reason_category:
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"{old.id} already has that reason category")
        to = [{**_item(old), "reason_category": category}]
    elif op == "split":
        texts = text if isinstance(text, list) else None
        if not texts or len(texts) < 2 or len(texts) > MAX_SPLIT_TEXTS:
            raise AmendmentRefused(
                CRITERIA_AMENDMENT_INVALID, f"split takes a list of 2 to {MAX_SPLIT_TEXTS} texts"
            )
        old = olds[0]
        cleaned = [_clean_text(t, "each text") for t in texts]
        made: list[str] = []
        for t in cleaned:
            new_id = current.next_id(side, made)
            made.append(new_id)
            to.append({"id": new_id, "text": t,
                       "reason_category": category if reason_category_given else old.reason_category,
                       "maps_to_rqs": list(old.maps_to_rqs)})
    elif op == "merge":
        if isinstance(text, list):
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "merge takes one text")
        new_text = _clean_text(text, "text")
        rqs: list[str] = []
        for c in olds:
            rqs.extend(r for r in c.maps_to_rqs if r not in rqs)
        to = [{"id": current.next_id(side), "text": new_text,
               "reason_category": category if reason_category_given else olds[0].reason_category,
               "maps_to_rqs": rqs}]
    elif op == "add":
        if isinstance(text, list):
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "add takes one text")
        new_text = _clean_text(text, "text")
        if any(c.text == new_text for c in current.side(side)):
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "a criterion in force already reads so")
        to = [{"id": current.next_id(side), "text": new_text, "reason_category": category, "maps_to_rqs": []}]
    # remove: nothing replaces it
    row = {"op": op, "side": side, "from": list(from_), "to": to, "criteria_version_after": current.version + 1}
    after = apply_rows(current, [row])
    if not after.side(side):
        raise AmendmentRefused(
            CRITERIA_SIDE_EMPTY, f"the revision leaves no {side} criterion in force; a protocol needs both sides"
        )
    return Plan(op, side, from_, tuple(to), after)


def file_sha256(workspace: Path | str) -> str | None:
    """``sha256:`` of the amendments file, or ``None`` when there is none (the publish row)."""
    path = Path(workspace) / AMENDMENTS_FILE
    if not path.is_file():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def new_amendment_id() -> str:
    return "CRA-" + uuid.uuid4().hex[:24]


def render_criteria_file(protocol: dict[str, Any], current: CriteriaInForce) -> str:
    """``SCREENING_CRITERIA.md`` for the criteria in force, with an "Amendments" section."""
    from scholar_protocol.models import ResearchProtocol
    from scholar_protocol.render import render_screening_criteria

    text = render_screening_criteria(ResearchProtocol.model_validate(current.protocol_in_force(protocol)))
    lines = [text.rstrip("\n"), "", "## Amendments", ""]
    lines.append(
        f"The criteria above are version {current.version}: the signed protocol's, amended after it was signed."
        if current.amendments else "None: these are the signed protocol's criteria."
    )
    lines.append("")
    for row in current.amendments:
        olds = ", ".join(f"{f['id']} “{f.get('text', '')}”" for f in row.get("from") or [])
        news = ", ".join(f"{t['id']} “{t.get('text', '')}”" for t in row.get("to") or [])
        lines.append(f"### {row.get('amendment_id')} (version {row.get('criteria_version_after')})")
        lines.append(f"- **Change**: {row.get('op')} ({row.get('side')})")
        if olds:
            lines.append(f"- **From**: {olds}")
        if news:
            lines.append(f"- **To**: {news}")
        lines.append(f"- **Reason**: {row.get('reason')}")
        lines.append(f"- **By**: {row.get('amended_by')}, {row.get('amended_at')}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# --- the workspace side: refusals, counts, the record ----------------------------


def any_batch_approved(workspace: Path | str) -> bool:
    """A batch of this screening was approved (or an earlier round was published).

    A citation-chasing round starts after a published screening (M3g), so a
    round after the first counts as approved: its criteria are the ones the
    published decisions were made under.
    """
    from .rounds import current_round

    ws = Path(workspace)
    if int(current_round(ws).get("round") or 1) > 1:
        return True
    approvals = ws / "literature" / "screening" / "approvals"
    return approvals.is_dir() and any(approvals.glob("batch_[0-9][0-9][0-9]_approval.json"))


def handoff_batches(workspace: Path | str, context: Any) -> list[int]:
    """Current batches with a worker recommendation, or a decisions file not built from events.

    Those decisions live outside the event log, so an amendment can neither count
    them nor show them again (review round 1, F1).
    """
    from .worker import recommendation_path

    ws = Path(workspace)
    found = []
    for index in sorted(context.batches):
        decisions = ws / "literature" / "screening" / f"batch_{index:03d}_decisions.json"
        from_events = False
        if decisions.is_file():
            try:
                payload = json.loads(decisions.read_text(encoding="utf-8"))
                from_events = isinstance(payload, dict) and payload.get("source") == "decision-events"
            except (OSError, ValueError):
                from_events = False
        if recommendation_path(ws, index).is_file() or (decisions.is_file() and not from_events):
            found.append(index)
    return found


def winners(context: Any, events: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """The winning counted decision per (study, screener) in the bound corpus."""
    from . import events as ev

    keys = sorted({(e["study_id"], e["screener_id"]) for e in events if e.get("study_id") in context.study_batch})
    out = {}
    for study, screener in keys:
        winner = ev.winning_event(events, study, screener)
        if winner is not None:
            out[(study, screener)] = winner
    return out


def by_outcome(decisions: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = dict.fromkeys(OUTCOMES, 0)
    for d in decisions:
        if d.get("outcome") in counts:
            counts[d["outcome"]] += 1
    return {**counts, "total": sum(counts.values())}


def awaiting(context: Any, events: list[dict[str, Any]], current: CriteriaInForce) -> dict[tuple[str, str], dict[str, Any]]:
    """The counted decisions ``current`` shows again, keyed by (study, screener)."""
    return {k: w for k, w in winners(context, events).items() if shown_again(w, current)}


def _workspace_id(ws: Path) -> str:
    try:
        manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(manifest.get("registered_workspace_id") or manifest.get("project_id") or "")


def _reproject(ws: Path, context: Any) -> list[int]:
    """Rebuild every batch decisions file the event log projects, under the criteria in ``context``."""
    from . import events as ev

    rebuilt = []
    for path in sorted((ws / "literature" / "screening").glob("batch_[0-9][0-9][0-9]_decisions.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not (isinstance(payload, dict) and payload.get("source") == "decision-events"):
            continue
        index = int(path.name[6:9])
        if index not in context.batches:
            continue
        ev.write_projection(
            ws, index, str(payload.get("reviewed_by") or ""), workspace_id=_workspace_id(ws), context=context
        )
        rebuilt.append(index)
    return rebuilt


def amend_criteria(
    workspace: Path | str,
    *,
    op: str,
    side: str,
    ids: list[str] | None,
    text: str | list[str] | None,
    reason_category: str | None,
    reason_category_given: bool,
    reason: str | None,
    confirm: bool,
    amended_by: str,
    amended_at: str,
    pilot_id: Any = None,
) -> dict[str, Any]:
    """Check, and with ``confirm`` record, one criteria revision (DoD 1 to 8).

    Runs under the events lock, so no decision is received between the count of
    the records shown again and the line that shows them again. Refuses before
    batches exist (``CRITERIA_AMENDMENT_NO_BATCHES``) and once a batch is
    approved (``CRITERIA_AMENDMENT_AFTER_APPROVAL``). The dry call
    (``confirm=False``) writes nothing and answers the new ids and how many
    records it would show again, by outcome. On ``confirm``: one line of
    ``AMENDMENTS_FILE``, ``SCREENING_CRITERIA.md`` rewritten (the earlier file
    backed up under ``audit/amended/<stamp>/``), every batch decisions file the
    event log projects rebuilt, and one ``PROTOCOL_CRITERIA_AMENDED`` journal row.
    Any failure before the journal row is written takes the line, the criteria
    file, the backup and the decisions files back.
    """
    from scholar_harness.workspace.audit import append_event

    from . import events as ev

    ws = Path(workspace)
    with ev._locked(ws):
        context = ev.load_context(ws)
        if not context.batches:
            raise AmendmentRefused(
                CRITERIA_AMENDMENT_NO_BATCHES,
                "no prepared batches: criteria are revised once the screening batches exist",
                status=409,
            )
        if any_batch_approved(ws):
            raise AmendmentRefused(
                CRITERIA_AMENDMENT_AFTER_APPROVAL,
                "a batch is approved: the criteria its decisions were made under are fixed; "
                "changing them now is a new screening",
                status=409,
            )
        handoff = handoff_batches(ws, context)
        if handoff:
            # Review round 1, F1 (decision item 10): a batch decided through the file
            # hand-off is not in the event log, so a revision could neither show its
            # decisions again nor count them; it would be approved under the old wording.
            raise AmendmentRefused(
                CRITERIA_AMENDMENT_HANDOFF,
                f"batch(es) {', '.join(str(i) for i in handoff)} hold a worker recommendation or decisions "
                "not made in the app; a revision could not show those decisions again. Decide them in the "
                "app's Triage (or start a new screening) before revising the criteria",
                status=409,
            )
        if pilot_id is OPEN_PILOT:
            from .pilot import open_pilot

            in_progress = open_pilot(ws)
            pilot_id = in_progress.pilot_id if in_progress is not None else None
        current = context.criteria if context.criteria is not None else signed_criteria(None)
        plan = plan_amendment(
            current, op=op, side=side, ids=ids, text=text,
            reason_category=reason_category, reason_category_given=reason_category_given,
        )
        events = ev.current_events(ev.read_events(ws), context)
        before = awaiting(context, events, current)
        later = awaiting(context, events, plan.after)
        newly = [w for k, w in later.items() if k not in before]
        answer = {
            "op": op,
            "side": side,
            "new_ids": plan.new_ids,
            "retired_ids": plan.retired_ids,
            "criteria_version_before": current.version,
            "criteria_version_after": current.version + 1,
            "decided": len(winners(context, events)),
            "shown_again": by_outcome(newly),
            "waiting_after": len(later),
        }
        if not confirm:
            return {"recorded": False, **answer}
        cleaned = " ".join(str(reason or "").split())
        if not cleaned:
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, "a revision needs a one-sentence reason")
        if len(cleaned) > MAX_REASON_CHARS:
            raise AmendmentRefused(CRITERIA_AMENDMENT_INVALID, f"the reason is longer than {MAX_REASON_CHARS} characters")
        row = {
            "amendment_id": new_amendment_id(),
            "op": op,
            "side": side,
            "from": list(plan.from_),
            "to": list(plan.to),
            "reason": cleaned,
            "criteria_version_before": current.version,
            "criteria_version_after": current.version + 1,
            "protocol_fingerprint": context.protocol_fingerprint,
            "pilot_id": pilot_id,
            "decided_at_time": answer["decided"],
            "shown_again": answer["shown_again"],
            "amended_by": amended_by,
            "amended_at": amended_at,
        }
        path = ws / AMENDMENTS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        size = path.stat().st_size if path.exists() else 0
        criteria_path = ws / CRITERIA_FILE
        earlier = criteria_path.read_bytes() if criteria_path.is_file() else None
        decisions = {
            p: p.read_bytes()
            for p in sorted((ws / "literature" / "screening").glob("batch_[0-9][0-9][0-9]_decisions.json"))
        }
        backup: Path | None = None
        try:
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            context.refresh_criteria(ws)
            protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
            if earlier is not None:
                backup = ws / AMENDED_DIR / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
                backup.mkdir(parents=True, exist_ok=False)
                (backup / CRITERIA_FILE).write_bytes(earlier)
            criteria_path.write_text(render_criteria_file(protocol, context.criteria), encoding="utf-8", newline="\n")
            rebuilt = _reproject(ws, context)
            from_ids = [f["id"] for f in plan.from_]
            to_ids = [t["id"] for t in plan.to]
            append_event(
                ws,
                AMENDED_ACTION,
                f"Amended the screening criteria: {op} on the {side} side "
                f"({', '.join(from_ids) or 'new'} -> {', '.join(to_ids) or 'retired'}); "
                f"version {current.version} -> {current.version + 1}; the signed protocol is unchanged",
                agent="scholar-harness/console",
                outputs=[AMENDMENTS_FILE.as_posix(), CRITERIA_FILE]
                + ([backup.relative_to(ws).as_posix() + "/"] if backup is not None else []),
                parameters={
                    "amendment_id": row["amendment_id"],
                    "op": op,
                    "side": side,
                    "from_ids": from_ids,
                    "to_ids": to_ids,
                    "reason": cleaned,
                    "criteria_version_before": current.version,
                    "criteria_version_after": current.version + 1,
                    "protocol_fingerprint": context.protocol_fingerprint,
                    "pilot_id": pilot_id,
                    "amended_by": amended_by,
                    "shown_again": answer["shown_again"],
                },
                metrics={"decided": answer["decided"], "shown_again": answer["shown_again"]["total"],
                         "projections_rebuilt": len(rebuilt)},
            )
        except Exception:
            with path.open("r+b") as handle:
                handle.truncate(size)
            if earlier is not None:
                criteria_path.write_bytes(earlier)
            elif criteria_path.is_file():
                criteria_path.unlink()
            for p, data in decisions.items():
                p.write_bytes(data)
            if backup is not None and backup.is_dir():
                for child in backup.iterdir():
                    child.unlink()
                backup.rmdir()
            raise
    return {"recorded": True, "amendment": public_row(row), **answer}
