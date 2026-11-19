"""Proposals on a workspace after genesis (M10c D5; decision 2026-11-19, item 9 option (a)).

An assistant suggests a change to the protocol's search: a concept's synonyms,
a new concept, the start or end year, the languages. The suggestion is a line
in the workspace's existing ``audit/proposals.jsonl`` (``target.kind:
"workspace"``), shown as a card on Discovery Plan. Only the researcher's Apply
changes anything: it amends those fields of ``intent.json`` and recompiles
``protocol.json`` with the compiler genesis uses, and journals
``PROPOSAL_DECIDED`` and ``PROTOCOL_AMENDED``.

Guards (each a refusal, nothing written):

* the amended protocol may differ from the current ``protocol.json`` only under
  ``search_strategy.core_concepts``, ``.date_range`` and ``.languages``
  (``PROTOCOL_AMENDMENT_REFUSED``, ``reason: "outside_search"``): a workspace
  whose ``protocol.json`` no longer matches its ``intent.json`` elsewhere (a
  hand edit, an older version) is never rewritten by an Apply;
* not once a corpus is accepted (``CORPUS_ALREADY_ACCEPTED``), nor while a
  discovery job runs in the console (``DISCOVERY_JOB_ACTIVE``, checked by the
  route, which alone sees the console's jobs);
* a proposal is stale when the protocol's fingerprint is not the one it was
  made against (``PROPOSAL_STALE``); it can then only be rejected.

The file is append-only: a ``proposed`` line, then at most one decision line
(``applied`` or ``rejected``). Genesis's own lines (``target.kind: "draft"``)
are history and are not listed here. The console and the MCP server both
write the file, so every read-then-append holds one lock across processes.
"""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .inception import proposals as P
from .inception.drafts import file_lock

PROPOSALS_FILE = P.PROPOSALS_FILE
#: Where a replaced intent and protocol are kept before an amendment writes.
AMENDED_DIR = "audit/amended"
#: The lock both processes take (a git-ignored console folder).
LOCK_FILE = ".harness-console/proposals.lock"
#: The step a workspace proposal is listed on.
STEP = "plan"
#: The protocol paths an amendment may change (decision item 9(a): the search fields).
AMENDABLE = (
    ("search_strategy", "core_concepts"),
    ("search_strategy", "date_range"),
    ("search_strategy", "languages"),
)
#: The intent fields a workspace proposal may target, and the ``op`` each takes.
FIELD_OPS: dict[str, tuple[str, ...]] = {
    "core_concepts": ("add",),
    "start_year": ("replace",),
    "end_year": ("replace",),
    "languages": ("add", "remove", "replace"),
}
SYNONYM_OPS = ("add", "remove")
_SYNONYMS = re.compile(r"^core_concepts\[(?P<concept>.+)\]\.synonyms$")
JOURNAL_AGENT = "nexus-scholar/ui"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _refused(code: str, message: str, http: int = 409, **details: Any) -> P.ProposalRefused:
    return P.ProposalRefused(code, message, http, details)


# --------------------------------------------------------------------------- the workspace's documents


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _refused("PROTOCOL_MISSING", f"{path.name} is missing or unreadable", 409, file=path.name) from exc


def documents(ws: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    """``(intent, protocol, fingerprint)`` as the workspace holds them now."""
    from pydantic import ValidationError

    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol

    intent, protocol = _read_json(ws / "intent.json"), _read_json(ws / "protocol.json")
    if not isinstance(intent, dict) or not isinstance(protocol, dict):
        raise _refused("PROTOCOL_INVALID", "intent.json and protocol.json must hold JSON objects", 422)
    try:
        fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    except ValidationError as exc:
        raise _refused("PROTOCOL_INVALID", f"protocol.json is not a valid protocol: {str(exc)[:300]}", 422) from exc
    return intent, protocol, fingerprint


def frozen(ws: Path) -> bool:
    """A corpus was accepted: the protocol it was accepted under is never amended.

    Fails closed: a registry that cannot be read (half-written by an accept in
    another process, corrupt) counts as accepted, so nothing is amended
    without knowing (DEVELOPER_COMPASS §12).
    """
    from .corpus_accept import _accepted_snapshot

    try:
        return bool(_accepted_snapshot(ws))
    except (OSError, ValueError, AttributeError, TypeError):
        return True


# --------------------------------------------------------------------------- targets and values


def check_target(field: str, op: str) -> None:
    allowed = SYNONYM_OPS if _SYNONYMS.match(field) else FIELD_OPS.get(field)
    if allowed is None:
        raise _refused(
            "PROPOSAL_TARGET_UNSUPPORTED",
            f"{field!r} is not a search field a workspace proposal can change "
            "(core_concepts, core_concepts[<concept>].synonyms, start_year, end_year, languages)",
            422, field=field, op=op,
        )
    if op not in allowed:
        raise _refused("PROPOSAL_TARGET_UNSUPPORTED", f"{field!r} takes {', '.join(allowed)}, not {op!r}", 422,
                       field=field, op=op)


def _concept_index(intent: dict[str, Any], name: str) -> int | None:
    for i, concept in enumerate(intent.get("core_concepts") or []):
        if str((concept or {}).get("concept") or "").casefold() == str(name).casefold():
            return i
    return None


def target_value(intent: dict[str, Any], protocol: dict[str, Any], field: str) -> Any:
    """The target's value now; ``languages`` left to the preset is the protocol's list."""
    match = _SYNONYMS.match(field)
    if match:
        i = _concept_index(intent, match["concept"])
        return None if i is None else list((intent["core_concepts"][i] or {}).get("synonyms") or [])
    if field == "languages" and intent.get("languages") is None:
        return list((protocol.get("search_strategy") or {}).get("languages") or [])
    return copy.deepcopy(intent.get(field))


def _text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _refused("PROTOCOL_AMENDMENT_REFUSED", f"{what} must be a non-empty text", 422, reason="invalid",
                       errors=[f"{what} must be a non-empty text"])
    return value.strip()


def _concept_value(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return {"concept": _text(value, "the concept"), "synonyms": []}
    if not isinstance(value, dict) or set(value) - {"concept", "synonyms", "boolean_operator"}:
        raise _refused("PROTOCOL_AMENDMENT_REFUSED", "a new concept is a name or {concept, synonyms}", 422,
                       reason="invalid", errors=["a new concept is a name or {concept, synonyms}"])
    synonyms = value.get("synonyms") or []
    if not isinstance(synonyms, list):
        raise _refused("PROTOCOL_AMENDMENT_REFUSED", "synonyms must be a list of texts", 422, reason="invalid",
                       errors=["synonyms must be a list of texts"])
    out = {"concept": _text(value.get("concept"), "the concept"), "synonyms": [_text(s, "a synonym") for s in synonyms]}
    if "boolean_operator" in value:
        out["boolean_operator"] = value["boolean_operator"]
    return out


def apply_op(intent: dict[str, Any], protocol: dict[str, Any], field: str, op: str, value: Any) -> dict[str, Any]:
    """A new intent with ``op value`` applied to ``field``; a change that changes nothing is refused."""
    check_target(field, op)
    new = copy.deepcopy(intent)
    match = _SYNONYMS.match(field)
    if match:
        i = _concept_index(new, match["concept"])
        if i is None:
            raise _refused("PROPOSAL_TARGET_UNSUPPORTED", "no concept of that name in the protocol", 422, field=field, op=op)
        term = _text(value, "a synonym")
        holder = new["core_concepts"][i]
        items = list(holder.get("synonyms") or [])
        present = [s for s in items if str(s).casefold() == term.casefold()]
        if op == "add":
            if present or term.casefold() == str(holder.get("concept") or "").casefold():
                raise _refused("PROPOSAL_NOT_OPEN", "the term is already in the protocol", status="present")
            holder["synonyms"] = [*items, term]
        else:
            if not present:
                raise _refused("PROPOSAL_NOT_OPEN", "the term is not in the protocol", status="absent")
            holder["synonyms"] = [s for s in items if str(s).casefold() != term.casefold()]
        return new
    if field == "core_concepts":
        concept = _concept_value(value)
        if _concept_index(new, concept["concept"]) is not None:
            raise _refused("PROPOSAL_NOT_OPEN", "the protocol already has this concept", status="present")
        new["core_concepts"] = [*(new.get("core_concepts") or []), concept]
        return new
    if field in ("start_year", "end_year"):
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise _refused("PROTOCOL_AMENDMENT_REFUSED", f"{field} must be a whole year or null", 422, reason="invalid",
                           errors=[f"{field} must be a whole year or null"])
        if new.get(field) == value:
            raise _refused("PROPOSAL_NOT_OPEN", f"{field} is already {value}", status="present")
        new[field] = value
        return new
    # languages
    current = target_value(intent, protocol, "languages")
    if op == "replace":
        if not isinstance(value, list):
            raise _refused("PROTOCOL_AMENDMENT_REFUSED", "languages is a list of codes", 422, reason="invalid",
                           errors=["languages is a list of codes"])
        new["languages"] = [_text(v, "a language") for v in value]
        if new["languages"] == current:
            raise _refused("PROPOSAL_NOT_OPEN", "the protocol already has these languages", status="present")
        return new
    code = _text(value, "a language")
    present = [v for v in current if str(v).casefold() == code.casefold()]
    if op == "add":
        if present:
            raise _refused("PROPOSAL_NOT_OPEN", "the language is already in the protocol", status="present")
        new["languages"] = [*current, code]
    else:
        if not present:
            raise _refused("PROPOSAL_NOT_OPEN", "the language is not in the protocol", status="absent")
        new["languages"] = [v for v in current if str(v).casefold() != code.casefold()]
    return new


def _diff(old: Any, new: Any, path: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    if isinstance(old, dict) and isinstance(new, dict):
        out: list[tuple[str, ...]] = []
        for key in sorted(set(old) | set(new)):
            if key not in old or key not in new:
                out.append((*path, key))
            else:
                out.extend(_diff(old[key], new[key], (*path, key)))
        return out
    return [] if old == new else [path]


def compile_amendment(protocol: dict[str, Any], new_intent: dict[str, Any]) -> dict[str, Any]:
    """Compile ``new_intent`` as genesis does; refuse a result that changes more than the search.

    Returns :func:`genesis.compile_intent`'s answer plus ``changed``, the
    protocol paths it changes (``search_strategy.…``).
    """
    from pydantic import ValidationError

    from .inception.genesis import compile_intent

    try:
        out = compile_intent(new_intent)
    except (ValidationError, ValueError, TypeError, KeyError) as exc:
        errors = [e.get("msg", str(e)) for e in exc.errors()] if isinstance(exc, ValidationError) else [str(exc)]
        raise _refused("PROTOCOL_AMENDMENT_REFUSED", "the amended intent does not compile to a protocol", 422,
                       reason="invalid", errors=errors[:10]) from exc
    changed = _diff(protocol, json.loads(out["protocol_bytes"]))
    outside = [p for p in changed if not any(p[: len(a)] == a for a in AMENDABLE)]
    if outside:
        raise _refused(
            "PROTOCOL_AMENDMENT_REFUSED",
            "applying this would change the protocol outside its search fields; nothing was written",
            422, reason="outside_search", paths=[".".join(p) or "/" for p in outside][:20],
        )
    if not changed:
        raise _refused("PROPOSAL_NOT_OPEN", "the protocol already says this", status="present")
    return {**out, "changed": [".".join(p) for p in changed]}


# --------------------------------------------------------------------------- the record


def _lines(ws: Path) -> list[dict[str, Any]]:
    path = ws / PROPOSALS_FILE
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    out = []
    for raw in text.splitlines():
        try:
            line = json.loads(raw)
        except ValueError:
            continue
        if isinstance(line, dict):
            out.append(line)
    return out


def stored(ws: Path) -> list[dict[str, Any]]:
    """The workspace proposals with their stored status (genesis's draft lines left out)."""
    by_id: dict[str, dict[str, Any]] = {}
    for line in _lines(ws):
        if line.get("event") == "proposed":
            if (line.get("target") or {}).get("kind") == "workspace":
                item = {k: v for k, v in line.items() if k != "event"}
                item.update(status="open", decided_at=None, decided_value=None)
                by_id[item["proposal_id"]] = item
        elif line.get("proposal_id") in by_id and line.get("event") in ("applied", "rejected"):
            by_id[line["proposal_id"]].update(
                status=line["event"], decided_at=line.get("decided_at"),
                decided_value=line.get("decided_value"), reason=line.get("reason"),
            )
    return list(by_id.values())


def view(proposal: dict[str, Any], intent: dict[str, Any], protocol: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    out = dict(proposal)
    out["current"] = P.shown(target_value(intent, protocol, proposal["target"]["field"]))
    if proposal["status"] == "open" and proposal["base"].get("protocol_fingerprint") != fingerprint:
        out["status"] = "stale"
    return out


def listing(ws: Path) -> dict[str, Any]:
    intent, protocol, fingerprint = documents(ws)
    items = [view(p, intent, protocol, fingerprint) for p in stored(ws)]
    return {
        "shape": "discovery.proposals-v1",
        "protocol_fingerprint": fingerprint,
        "frozen": frozen(ws),
        "proposals": items,
        "counts": {s: sum(1 for i in items if i["status"] == s) for s in ("open", "stale", "applied", "rejected")},
    }


def _append(ws: Path, line: dict[str, Any]) -> None:
    path = ws / PROPOSALS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def lock(ws: Path):
    return file_lock(Path(ws) / LOCK_FILE)


def make(
    ws: Path, *, source: str, field: str, op: str, value: Any, why: str, evidence: list[dict[str, Any]],
    extra: dict[str, Any] | None = None, open_limit: int | None = None, limit_error: Exception | None = None,
) -> tuple[dict[str, Any], bool]:
    """Record one open proposal (the caller checked the source); ``(view, created)``.

    The value is checked as Apply would check it (applied to a copy and
    compiled), so a suggestion the protocol cannot take is refused here.
    """
    ws = Path(ws)
    with lock(ws):
        intent, protocol, fingerprint = documents(ws)
        if frozen(ws):
            raise _refused("CORPUS_ALREADY_ACCEPTED", "a corpus was accepted under this protocol; it is not amended")
        check_target(field, op)
        current = target_value(intent, protocol, field)
        base = {"hash": P.value_hash(current), "shown": P.shown(current), "protocol_fingerprint": fingerprint}
        target = {"kind": "workspace", "id": ws.name, "field": field}
        pid = P.proposal_id(source, target, op, value, fingerprint)
        same = next((p for p in stored(ws) if p["proposal_id"] == pid), None)
        if same is not None:
            return view(same, intent, protocol, fingerprint), False
        compile_amendment(protocol, apply_op(intent, protocol, field, op, value))
        if open_limit is not None:
            live = [view(p, intent, protocol, fingerprint) for p in stored(ws) if p["source"].startswith(source.split(":", 1)[0] + ":")]
            if sum(1 for p in live if p["status"] in ("open", "stale")) >= open_limit and limit_error is not None:
                raise limit_error
        proposal = {
            "proposal_id": pid, "target": target, "op": op, "value": value, "why": why, "evidence": list(evidence),
            "source": source, "base": base, "status": "open", "step": STEP, "proposed_at": _now(), **(extra or {}),
        }
        _append(ws, {"event": "proposed", **proposal})
        return view({**proposal, "decided_at": None, "decided_value": None}, intent, protocol, fingerprint), True


def _write_atomic(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def decide(ws: Path, pid: str, action: str, *, reason: str | None = None) -> dict[str, Any]:
    """``apply`` or ``reject`` one workspace proposal (the researcher's action in the app).

    The caller (the console route) has refused a running discovery job.
    Answers the new listing plus ``amended`` (fingerprints and changed paths) on an Apply.
    """
    from .workspace.audit import append_event

    ws = Path(ws)
    with lock(ws):
        intent, protocol, fingerprint = documents(ws)
        proposal = next((p for p in stored(ws) if p["proposal_id"] == pid), None)
        if proposal is None:
            raise _refused("PROPOSAL_NOT_FOUND", f"no proposal {pid} on this workspace", 404, proposal_id=pid)
        state = view(proposal, intent, protocol, fingerprint)["status"]
        field = proposal["target"]["field"]
        amended: dict[str, Any] | None = None
        if action == "reject":
            if state not in ("open", "stale"):
                raise _refused("PROPOSAL_NOT_OPEN", f"this suggestion is {state}", status=state)
            text = (reason or "").strip() or None
            line = {"event": "rejected", "proposal_id": pid, "decided_at": _now(), "decided_value": None}
            if text:
                line["reason"] = text
            _append(ws, line)
        elif action == "apply":
            if state == "stale":
                raise _refused("PROPOSAL_STALE", "the protocol changed after the suggestion was made", 409,
                               base=proposal["base"]["shown"], current=P.shown(target_value(intent, protocol, field)))
            if state != "open":
                raise _refused("PROPOSAL_NOT_OPEN", f"this suggestion is {state}", status=state)
            if frozen(ws):
                raise _refused("CORPUS_ALREADY_ACCEPTED", "a corpus was accepted under this protocol; it is not amended")
            new_intent = apply_op(intent, protocol, field, proposal["op"], proposal["value"])
            out = compile_amendment(protocol, new_intent)
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            backup = ws / AMENDED_DIR / stamp
            backup.mkdir(parents=True, exist_ok=False)
            for name in ("intent.json", "protocol.json", "SCREENING_CRITERIA.md"):
                if (ws / name).is_file():
                    (backup / name).write_bytes((ws / name).read_bytes())
            _write_atomic(ws / "intent.json", out["intent_text"].encode("utf-8"))
            _write_atomic(ws / "protocol.json", out["protocol_bytes"])
            _write_atomic(ws / "SCREENING_CRITERIA.md", out["criteria_text"].encode("utf-8"))
            amended = {
                "previous_fingerprint": fingerprint, "protocol_fingerprint": out["protocol_fingerprint"],
                "changed": out["changed"], "backup": backup.relative_to(ws).as_posix(),
            }
            _append(ws, {"event": "applied", "proposal_id": pid, "decided_at": _now(),
                         "decided_value": proposal["value"], "in_protocol": True, **amended})
        else:
            raise _refused("BODY_INVALID", f"unknown action {action!r}", 422)
        source_kind = proposal["source"].split(":", 1)[0]
        append_event(
            ws, "PROPOSAL_DECIDED", f"{'applied' if action == 'apply' else 'rejected'} {pid} on {field}",
            agent=JOURNAL_AGENT, outputs=[PROPOSALS_FILE],
            parameters={"proposal_id": pid, "decision": "applied" if action == "apply" else "rejected",
                        "field": field, "op": proposal["op"], "source": proposal["source"], "source_kind": source_kind,
                        **({"reason": line["reason"]} if action == "reject" and line.get("reason") else {})},
        )
        if amended is not None:
            append_event(
                ws, "PROTOCOL_AMENDED",
                f"search fields amended from {pid}: protocol fingerprint {fingerprint} -> {amended['protocol_fingerprint']}",
                agent=JOURNAL_AGENT, inputs=[PROPOSALS_FILE],
                outputs=["intent.json", "protocol.json", "SCREENING_CRITERIA.md", amended["backup"] + "/"],
                parameters={"proposal_id": pid, **amended},
            )
        answer = listing(ws)
        answer["amended"] = amended
        return answer
