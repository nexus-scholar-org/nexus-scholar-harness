"""Proposals: a change to the draft the engine suggests (M10b, ``docs/ux/shared/final/01-proposals.md``).

A proposal names a target field of the draft, an ``op`` (``add``, ``remove``,
``replace``), the exact ``value`` and the ``base`` the target had when it was
made. Nothing is applied without the researcher's click. In M10b open
proposals are created only by a fixed check (``check:<id>``); a draft save may
also carry ``accepted_from`` records of the six engine mechanisms that exist
today (``engine:<mechanism>``), which are written decided and never shown as
open cards.

The proposals live in the draft record's ``proposals`` key, beside ``draft``
(``Draft`` is ``extra="forbid"``), and from genesis on in the workspace's
``audit/proposals.jsonl``. ``stale`` is derived on every read, never stored.
"""

from __future__ import annotations

import hashlib
import json
import re
import typing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import steps

#: The proposal record a genesis writes (01-proposals "Where a proposal is kept").
PROPOSALS_FILE = "audit/proposals.jsonl"

#: Stored statuses; ``stale`` is derived.
STATUSES = ("open", "applied", "applied_edited", "rejected")
OPS = ("add", "remove", "replace")

#: The six engine mechanisms that exist today (01-proposals), as recorded names.
MECHANISMS = ("wizard_criterion", "pool_synonym", "suggested_concept", "matrix_column", "direction", "anchor_seed")

#: Which stepper step lists a proposal on a field (01-proposals, the ``step`` row).
STEP_OF_FIELD: dict[str, str] = {
    **dict.fromkeys(("topic", "start_year", "end_year", "languages"), "scope"),
    "golden_seeds": "direction",
    #: Not a draft field: the bind's ``engine:direction`` record names the record's ``grounding``.
    "grounding": "direction",
    **dict.fromkeys(
        ("paradigm", "playbook", "secondary_paradigm", "unit_of_analysis", "proof", "rqs", "pool_min", "pool_max"),
        "shape",
    ),
    **dict.fromkeys(
        (
            "concepts", "extra_inclusions", "extra_exclusions", "out_of_scope", "out_of_scope_reasons",
            "default_exclusion_reason", "criteria_decisions", "matrix_columns", "custom_matrix_columns",
            "verification_checks",
        ),
        "criteria",
    ),
    **dict.fromkeys(("title", "lead_researcher", "venue", "timeline_weeks"), "review"),
}
PROPOSAL_STEPS = ("scope", "explore", "direction", "shape", "criteria", "review")

_SYNONYMS = re.compile(r"^concepts\[(?P<concept>.+)\]\.synonyms$")


class ProposalRefused(Exception):
    """A proposal operation was refused; console-style ``{code, message, details}``."""

    def __init__(self, code: str, message: str, status: int = 409, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def value_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _list_fields() -> frozenset[str]:
    out = set()
    for name, field in steps.Draft.model_fields.items():
        if typing.get_origin(field.annotation) is list:
            out.add(name)
    return frozenset(out)


LIST_FIELDS = _list_fields()


def _base_field(field: str) -> str:
    return "concepts" if _SYNONYMS.match(field) else field


def step_of(field: str) -> str:
    return STEP_OF_FIELD.get(_base_field(field), "review")


def _concept_index(draft: dict[str, Any], name: str) -> int | None:
    for i, concept in enumerate(draft.get("concepts") or []):
        if str((concept or {}).get("concept") or "").casefold() == name.casefold():
            return i
    return None


def check_target(field: str, op: str) -> None:
    """Refuse a field that is not a draft field, or an ``op`` that does not fit it."""
    match = _SYNONYMS.match(field)
    if op not in OPS:
        raise ProposalRefused("PROPOSAL_TARGET_UNSUPPORTED", f"unknown op {op!r}", 422, {"field": field, "op": op})
    if match:
        if op == "replace":
            return
        if op in ("add", "remove"):
            return
    if field not in steps.Draft.model_fields:
        raise ProposalRefused(
            "PROPOSAL_TARGET_UNSUPPORTED", f"{field!r} is not a draft field", 422, {"field": field, "op": op}
        )
    if field not in LIST_FIELDS and op != "replace":
        raise ProposalRefused(
            "PROPOSAL_TARGET_UNSUPPORTED", f"{field!r} holds one value; only replace fits it", 422,
            {"field": field, "op": op},
        )


def target_value(draft: dict[str, Any], field: str) -> Any:
    """The target's current value in a raw draft (``None`` for a concept that is gone)."""
    match = _SYNONYMS.match(field)
    if match:
        i = _concept_index(draft, match["concept"])
        return None if i is None else list((draft["concepts"][i] or {}).get("synonyms") or [])
    if field in draft:
        return draft[field]
    if field not in steps.Draft.model_fields:
        return None  # a record key such as ``grounding`` (the direction record)
    default = steps.Draft.model_fields[field].get_default(call_default_factory=True)
    return default


def shown(value: Any, limit: int = 120) -> str:
    """The short text of a value, as "Was" and "Now" show it."""
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    elif isinstance(value, list):
        text = ", ".join(_one(v) for v in value)
    else:
        text = _one(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _one(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("concept") or value.get("criterion") or value.get("name") or canonical(value))
    return str(value)


def proposal_id(source: str, target: dict[str, Any], op: str, value: Any, base_hash: str) -> str:
    raw = canonical([source, target, op, value, base_hash])
    return "prop_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


#: Who may create an open proposal. ``agent`` only through the assistant (M10c, ``scholar_harness/assistant.py``).
CREATING_SOURCES = ("check", "import")


def check_source(source: str, kinds: tuple[str, ...] = CREATING_SOURCES) -> None:
    kind = source.split(":", 1)[0]
    if kind not in kinds or ":" not in source or not source.split(":", 1)[1]:
        raise ProposalRefused(
            "PROPOSAL_SOURCE_REFUSED", f"the source {source!r} cannot create a proposal in this version", 422,
            {"source": source},
        )


def make(
    *, draft_id: str, draft: dict[str, Any], source: str, field: str, op: str, value: Any, why: str,
    evidence: list[dict[str, Any]] | None = None, sources: tuple[str, ...] = CREATING_SOURCES,
) -> dict[str, Any]:
    """An open proposal against ``draft`` as it is now (the engine and, since M10c, an assistant create them)."""
    check_source(source, sources)
    check_target(field, op)
    current = target_value(draft, field)
    base = {"hash": value_hash(current), "shown": shown(current)}
    target = {"kind": "draft", "id": draft_id, "field": field}
    return {
        "proposal_id": proposal_id(source, target, op, value, base["hash"]),
        "target": target,
        "op": op,
        "value": value,
        "why": why,
        "evidence": list(evidence or []),
        "source": source,
        "base": base,
        "status": "open",
        "decided_at": None,
        "decided_value": None,
        "step": step_of(field),
    }


def view(proposal: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    """The proposal as read: ``stale`` derived, ``current`` shown for "Now"."""
    current = target_value(draft, proposal["target"]["field"])
    out = dict(proposal)
    out["step"] = step_of(proposal["target"]["field"])
    out["current"] = shown(current)
    if proposal["status"] == "open" and value_hash(current) != proposal["base"]["hash"]:
        out["status"] = "stale"
    return out


def listing(record: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    draft = record.get("draft") or {}
    items = [view(p, draft) for p in record.get("proposals") or []]
    by_step = {s: {"open": 0, "stale": 0} for s in PROPOSAL_STEPS}
    for item in items:
        if item["status"] in ("open", "stale") and item["step"] in by_step:
            by_step[item["step"]]["open" if item["status"] == "open" else "stale"] += 1
    if step is not None:
        items = [i for i in items if i["step"] == step]
    return {"session_id": record.get("session_id"), "updated_at": record.get("updated_at"), "proposals": items, "by_step": by_step}


def _same(a: Any, b: Any, field: str) -> bool:
    if _base_field(field) == "concepts" and not _SYNONYMS.match(field):
        name = lambda v: str((v or {}).get("concept") if isinstance(v, dict) else v).casefold()  # noqa: E731
        return name(a) == name(b)
    if isinstance(a, str) and isinstance(b, str):
        return a.casefold() == b.casefold() if _SYNONYMS.match(field) else a == b
    return canonical(a) == canonical(b)


def apply_op(draft: dict[str, Any], field: str, op: str, value: Any) -> dict[str, Any]:
    """A new raw draft with ``op value`` applied to ``field`` (the caller validates it)."""
    check_target(field, op)
    new = json.loads(json.dumps(draft))
    match = _SYNONYMS.match(field)
    if match:
        i = _concept_index(new, match["concept"])
        if i is None:
            raise ProposalRefused("PROPOSAL_STALE", "the concept is no longer in the draft", 409, {"field": field})
        holder, key = new["concepts"][i], "synonyms"
    else:
        holder, key = new, field
    if op == "replace":
        holder[key] = value
        return new
    items = list(holder.get(key) if key in holder else target_value(draft, field) or [])
    present = [x for x in items if _same(x, value, field)]
    if op == "add":
        if present:
            raise ProposalRefused("PROPOSAL_NOT_OPEN", "the value is already there", 409, {"status": "present"})
        items.append(value)
    else:
        if not present:
            raise ProposalRefused("PROPOSAL_NOT_OPEN", "the value is no longer there", 409, {"status": "absent"})
        items = [x for x in items if not _same(x, value, field)]
    holder[key] = items
    return new


def find(record: dict[str, Any], pid: str) -> dict[str, Any]:
    for proposal in record.get("proposals") or []:
        if proposal["proposal_id"] == pid:
            return proposal
    raise ProposalRefused("PROPOSAL_NOT_FOUND", f"no proposal {pid} on this draft", 404, {"proposal_id": pid})


def decide(record: dict[str, Any], pid: str, action: str, *, value: Any = None, reason: str | None = None) -> bool:
    """Apply ``action`` to the record in place; ``True`` when the draft's answers changed.

    ``action`` is ``apply``, ``apply_edited``, ``reject`` or ``restore``. The
    new draft goes through :func:`steps.parse_draft` with ``saving=True``, so an
    applied value is refused exactly as a manual save of it would be.
    """
    proposal = find(record, pid)
    draft = record.get("draft") or {}
    state = view(proposal, draft)["status"]
    if action == "restore":
        if proposal["status"] != "rejected":
            raise ProposalRefused("PROPOSAL_NOT_OPEN", "only a rejected suggestion can be restored", 409, {"status": state})
        proposal.update(status="open", decided_at=None, decided_value=None, reason=None)
        return False
    if action == "reject":
        if state not in ("open", "stale"):
            raise ProposalRefused("PROPOSAL_NOT_OPEN", f"this suggestion is {state}", 409, {"status": state})
        proposal.update(status="rejected", decided_at=_now(), reason=(reason or "").strip() or None)
        return False
    if state == "stale":
        current = target_value(draft, proposal["target"]["field"])
        raise ProposalRefused(
            "PROPOSAL_STALE", "this field changed after the suggestion was made", 409,
            {"base": proposal["base"]["shown"], "current": shown(current)},
        )
    if state != "open":
        raise ProposalRefused("PROPOSAL_NOT_OPEN", f"this suggestion is {state}", 409, {"status": state})
    written = proposal["value"] if action == "apply" else value
    new = apply_op(draft, proposal["target"]["field"], proposal["op"], written)
    steps.parse_draft(new, saving=True)
    record["draft"] = new
    proposal.update(
        status="applied" if action == "apply" else "applied_edited", decided_at=_now(), decided_value=written,
    )
    return True


def add_open(record: dict[str, Any], proposal: dict[str, Any]) -> bool:
    """Record an engine-created open proposal once (same id: nothing changes)."""
    existing = record.setdefault("proposals", [])
    if any(p["proposal_id"] == proposal["proposal_id"] for p in existing):
        return False
    existing.append(proposal)
    return True


# ---------------------------------------------------------------------------
# accepted_from: the six mechanisms that exist today (01-proposals, R1)
# ---------------------------------------------------------------------------


def offered(
    mechanism: str, field: str, value: Any, draft: steps.Draft, *, pool: dict[str, Any] | None = None,
    directions: list[dict[str, Any]] | None = None,
) -> bool:
    """Did ``mechanism`` offer ``value`` for ``field`` on ``draft`` (the stored draft, before the save)?

    The same code the mechanism's read route runs. ``pool`` (and
    ``directions``) come from the draft's recon session; without them the pool
    mechanisms offered nothing.
    """
    from scholar_harness.recon.vocabulary import concept_report, seed_candidates

    from .intent import draft_default_concepts

    try:
        if mechanism == "wizard_criterion" and field == "criteria_decisions":
            items = steps.criteria_with_decisions(draft)
            return any(i["id"] == value and i["generated"] for i in items)
        if mechanism == "matrix_column" and field == "matrix_columns" and draft.playbook:
            dims = steps._default_matrix_dimensions(draft.playbook, draft.unit_of_analysis or "the unit of analysis")
            return value in {d["name"] for d in dims}
        if mechanism == "suggested_concept" and field == "concepts":
            name = value.get("concept") if isinstance(value, dict) else value
            return not draft.concepts and str(name) in draft_default_concepts(draft.topic)
        if mechanism == "pool_synonym" and pool is not None:
            match = _SYNONYMS.match(field)
            if not match:
                return False
            rows, source = _concept_rows(draft)
            for row in concept_report(pool, rows, source):
                if row["concept"].casefold() == match["concept"].casefold():
                    return any(s["term"] == value for s in row["suggestions"])
            return False
        if mechanism == "anchor_seed" and field == "golden_seeds" and pool is not None:
            rows, _source = _concept_rows(draft)
            papers = seed_candidates(pool, directions or [], [r["concept"] for r in rows])
            return str(value).lower() in {p["doi"].lower() for p in papers}
    except (steps.StepRefused, KeyError, TypeError, ValueError):
        return False
    return False


def _concept_rows(draft: steps.Draft) -> tuple[list[dict[str, Any]], str]:
    from .intent import draft_default_concepts

    if draft.concepts:
        return [{"concept": c.concept, "synonyms": list(c.synonyms)} for c in draft.concepts], "draft"
    return [{"concept": w, "synonyms": []} for w in draft_default_concepts(draft.topic)], "suggested"


def engine_record(draft_id: str, mechanism: str, field: str, value: Any, base_hash: str) -> dict[str, Any]:
    """A decided ``engine:<mechanism>`` entry (never an open card)."""
    source = f"engine:{mechanism}"
    op = "replace" if mechanism == "direction" else "add"
    target = {"kind": "draft", "id": draft_id, "field": field}
    stamp = _now()
    return {
        "proposal_id": proposal_id(source, target, op, value, base_hash),
        "target": target,
        "op": op,
        "value": value,
        "why": "",
        "evidence": [],
        "source": source,
        "base": {"hash": base_hash, "shown": ""},
        "status": "applied",
        "decided_at": stamp,
        "decided_value": value,
        "step": step_of(field),
    }


def holds(draft: dict[str, Any], mechanism: str, field: str, value: Any) -> bool:
    """Does the saved draft hold the accepted value (review of Part B, finding 1)?"""
    if mechanism == "wizard_criterion":
        return (draft.get("criteria_decisions") or {}).get(value) is True
    current = target_value(draft, field)
    return isinstance(current, list) and any(_same(x, value, field) for x in current)


def record_accepted(
    record: dict[str, Any], entries: list[dict[str, Any]], *,
    pool: dict[str, Any] | None = None, directions: list[dict[str, Any]] | None = None,
    saved: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Write one decided entry per offered value into ``record``; answer the ones not recorded.

    Called before the save replaces ``record["draft"]``: what was offered is
    judged on the stored draft, the one the screen read (a mechanism stops
    offering a value once it is accepted, ``recon/vocabulary.py``); that it
    was accepted is judged on ``saved``, the draft this save writes: an entry
    the saved draft does not hold (a criterion sent as dropped) is not recorded.
    """
    not_recorded = []
    raw = record.get("draft") or {}
    try:
        stored = steps.parse_draft(raw)
    except steps.StepRefused:
        stored = None
    for entry in entries:
        mechanism, field, value = entry["mechanism"], entry["field"], entry["value"]
        if (
            mechanism == "direction"  # chosen by the bind, which writes its own record
            or stored is None
            or (saved is not None and not holds(saved, mechanism, field, value))
            or not offered(mechanism, field, value, stored, pool=pool, directions=directions)
        ):
            not_recorded.append({"mechanism": mechanism, "field": field, "value": value})
            continue
        # The base is the stored target before this save, so a second save of the same entry is a no-op.
        base = value_hash(target_value(raw, field))
        add_open(record, engine_record(record["session_id"], mechanism, field, value, base))
    return not_recorded


# ---------------------------------------------------------------------------
# Genesis: audit/proposals.jsonl
# ---------------------------------------------------------------------------


def _in_protocol(proposal: dict[str, Any], record: dict[str, Any]) -> bool:
    draft = record.get("draft") or {}
    field, op = proposal["target"]["field"], proposal["op"]
    if field == "grounding":
        return ((record.get("grounding") or {}).get("direction") or {}).get("label") == proposal.get("decided_value")
    written = proposal.get("decided_value", proposal["value"])
    current = target_value(draft, field)
    if op == "replace":
        return canonical(current) == canonical(written)
    present = any(_same(x, written, field) for x in (current or []))
    if field == "criteria_decisions":
        present = bool((draft.get("criteria_decisions") or {}).get(written))
    return present if op == "add" else not present


def genesis_lines(record: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The lines of ``audit/proposals.jsonl``: each ``proposed``, then its decision with ``in_protocol``."""
    if not record:
        return []
    lines: list[dict[str, Any]] = []
    for proposal in record.get("proposals") or []:
        stored = {k: v for k, v in proposal.items() if k not in ("decided_at", "decided_value", "reason")}
        stored["status"] = "open"
        lines.append({"event": "proposed", **stored})
        if proposal["status"] in ("applied", "applied_edited", "rejected"):
            line = {
                "event": proposal["status"],
                "proposal_id": proposal["proposal_id"],
                "decided_at": proposal.get("decided_at"),
                "decided_value": proposal.get("decided_value"),
            }
            if proposal["status"] != "rejected":
                line["in_protocol"] = _in_protocol(proposal, record)
            elif proposal.get("reason"):
                line["reason"] = proposal["reason"]
            lines.append(line)
    return lines


def counts(lines: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_source: dict[str, int] = {}
    in_protocol = 0
    for line in lines:
        if line["event"] == "proposed":
            kind = line["source"].split(":", 1)[0]
            by_source[kind] = by_source.get(kind, 0) + 1
        else:
            by_status[line["event"]] = by_status.get(line["event"], 0) + 1
            in_protocol += bool(line.get("in_protocol"))
    proposed = sum(by_source.values())
    by_status["open"] = proposed - sum(by_status.values())
    return {"proposed": proposed, "by_status": by_status, "by_source": by_source, "in_protocol": in_protocol}


def write_jsonl(path: Path, lines: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines), encoding="utf-8")
