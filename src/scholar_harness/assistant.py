"""The assistant and the critic over MCP (M10c, ``docs/roadmap/milestones/M10c-assistant-mcp.md``).

The researcher's own MCP client is the assistant; no model is called here.
It reads a draft or a workspace, and it may only *add a suggestion*:

* a **proposal** (the M10b object, ``inception/proposals.py``) with the source
  ``agent:<model>``, applied, edited or rejected by the researcher on the
  existing card; recorded by a side write, so no answer and no ``updated_at``
  changes;
* a **finding** (the critic): a row of the M10b check object
  (``inception/checks.py``) with ``source: "agent"``, listed by the same check
  endpoints and dismissed through the same record. On a draft it is kept in
  the record's ``assistant_findings`` key; on a workspace in
  ``audit/assistant_findings.jsonl``.

Nothing here starts a search, accepts a corpus, decides a screening record or
publishes (decision 2026-11-14, item 3).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.inception import checks as C
from scholar_harness.inception import proposals as P
from scholar_harness.inception import steps
from scholar_harness.inception.drafts import DraftRefused, DraftStore

TASK_VERSION = "assistant-v1"
#: M9d's three tasks and a general one (decision item 2); ``critic`` is the findings' task.
PROPOSAL_TASKS = ("suggest", "synonyms", "translation", "recall_repair")
FINDING_TASK = "critic"
#: Severity to check level (decision item 8): never a blocker.
SEVERITIES = {"critical": "warning", "major": "warning", "minor": "note"}
MODEL_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
#: Decision item 7: open ones only; a decided proposal or a dismissed finding does not count.
MAX_OPEN_PROPOSALS = 30
MAX_OPEN_FINDINGS = 50
MAX_EVIDENCE = 20
EVIDENCE_KINDS = ("doi", "count", "check", "file", "words", "name", "locator", "run")

FINDING_CHECK_ID = "ASSISTANT_FINDING"
FINDINGS_KEY = "assistant_findings"
FINDINGS_FILE = "audit/assistant_findings.jsonl"
#: The journal agent of an assistant's write; the model is a parameter.
JOURNAL_AGENT = "nexus-scholar/assistant"
#: A locator into the draft's answers rather than its intent (an incomplete draft has no intent).
DRAFT_PREFIX = "draft:"
#: A locator into a workspace's ``protocol.json`` (what exists only once compiled, such as criterion ids).
PROTOCOL_PREFIX = "protocol:"

#: Which inception step lists a finding located in the intent (01-proposals' step map, in intent words).
INTENT_STEP: dict[str, str] = {
    **dict.fromkeys(("start_year", "end_year", "languages"), "scope"),
    "golden_seeds": "direction",
    **dict.fromkeys(
        ("playbook_type", "primary_paradigm", "secondary_paradigm", "unit_of_analysis", "research_questions",
         "pool_min", "pool_max", "epistemological_rationale", "trustworthiness_framework", "incompatible_concepts"),
        "shape",
    ),
    **dict.fromkeys(
        ("core_concepts", "inclusion_criteria", "exclusion_criteria", "matrix_dimensions", "two_tier_screening",
         "retraction_check_required", "coi_and_funding_audit_required", "reproducibility_das_cas_check",
         "minimum_trust_score_threshold"),
        "criteria",
    ),
}


class AssistantRefused(Exception):
    """An assistant's request was refused; ``{code, message, details}`` as the console's refusals."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details or {}


def refusal(exc: Exception) -> dict[str, Any]:
    """The tool answer for any engine refusal (draft, step, proposal, check or assistant)."""
    out: dict[str, Any] = {"status": "ERROR", "code": getattr(exc, "code", type(exc).__name__),
                           "message": getattr(exc, "message", str(exc))}
    details = getattr(exc, "details", None)
    if details:
        out["details"] = details
    return out


def _now() -> str:
    return datetime.now(UTC).isoformat()


def agent_of(model: str, task: str, allowed: tuple[str, ...]) -> dict[str, str]:
    """The ``agent`` provenance; refuses a missing model or an unknown task (decision item 2)."""
    if not isinstance(model, str) or not MODEL_RE.fullmatch(model.strip()):
        raise AssistantRefused(
            "PROVENANCE_MISSING", "name the model that wrote this (letters, digits, '.', '_', ':', '-'; up to 64)",
            {"field": "model"},
        )
    if task not in allowed:
        raise AssistantRefused("TASK_UNKNOWN", f"task must be one of {', '.join(allowed)}", {"tasks": list(allowed)})
    return {"model": model.strip(), "task": task, "task_version": TASK_VERSION}


def _text(value: Any, name: str, *, required: bool) -> str | None:
    text = (value or "").strip() if isinstance(value, str) or value is None else None
    if text is None:
        raise AssistantRefused("BODY_INVALID", f"{name} must be text", {"field": name})
    if required and not text:
        raise AssistantRefused("BODY_INVALID", f"{name} is required", {"field": name})
    if len(text) > steps.MAX_TEXT_CHARS:
        raise AssistantRefused("BODY_INVALID", f"{name} is longer than {steps.MAX_TEXT_CHARS} characters",
                               {"field": name, "limit": steps.MAX_TEXT_CHARS})
    return text or None


def _evidence(evidence: Any) -> list[dict[str, Any]]:
    if evidence is None:
        return []
    if not isinstance(evidence, list) or len(evidence) > MAX_EVIDENCE:
        raise AssistantRefused("BODY_INVALID", f"evidence is a list of at most {MAX_EVIDENCE} items", {"field": "evidence"})
    for item in evidence:
        if not isinstance(item, dict) or item.get("kind") not in EVIDENCE_KINDS:
            raise AssistantRefused(
                "BODY_INVALID", f"each evidence item is an object whose kind is one of {', '.join(EVIDENCE_KINDS)}",
                {"field": "evidence"},
            )
    if len(P.canonical(evidence)) > steps.MAX_TEXT_CHARS * 2:
        raise AssistantRefused("BODY_INVALID", "the evidence is too long", {"field": "evidence"})
    return evidence


# ---------------------------------------------------------------------------
# Locators: a JSON pointer into the intent, or ``draft:`` + a pointer into the answers
# ---------------------------------------------------------------------------


def _tokens(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise AssistantRefused("LOCATOR_INVALID", "a locator is a JSON pointer: '' or '/key/0/…'", {"locator": pointer})
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def resolve(doc: Any, pointer: str) -> tuple[bool, Any]:
    """``(found, value)``; a missing last step under an existing list or object is ``(False, None)``.

    Raises ``LOCATOR_UNKNOWN`` when a step before the last does not exist.
    """
    tokens = _tokens(pointer)
    node = doc
    for i, token in enumerate(tokens):
        last = i == len(tokens) - 1
        if isinstance(node, dict):
            if token in node:
                node = node[token]
                continue
        elif isinstance(node, list) and (token.isdigit() or token == "-"):
            index = len(node) if token == "-" else int(token)
            if index < len(node):
                node = node[index]
                continue
            if last and index <= len(node):
                return False, None
        if last and isinstance(node, (dict, list)):
            return False, None
        raise AssistantRefused("LOCATOR_UNKNOWN", f"{pointer!r} does not exist here", {"locator": pointer})
    return True, node


def located_hash(doc: Any, pointer: str) -> str | None:
    try:
        found, value = resolve(doc, pointer)
    except AssistantRefused:
        return None
    return P.value_hash(value if found else None)


def _split(locator: str) -> tuple[str, str]:
    """``("draft" | "protocol" | "intent", pointer)``."""
    if not isinstance(locator, str) or len(locator) > 500:
        raise AssistantRefused("LOCATOR_INVALID", "a locator is a JSON pointer of at most 500 characters", {"locator": locator})
    for kind, prefix in (("draft", DRAFT_PREFIX), ("protocol", PROTOCOL_PREFIX)):
        if locator.startswith(prefix):
            return kind, locator[len(prefix):]
    return "intent", locator


def step_of_locator(locator: str, *, workspace: bool) -> str:
    """The step that lists a finding: ``plan`` on a workspace; an inception step on a draft."""
    if workspace:
        return "plan"
    kind, pointer = _split(locator)
    head = (_tokens(pointer) or [""])[0]
    if kind == "draft":
        return P.step_of(head) if head else "review"
    return INTENT_STEP.get(head, "review")


def draft_intent(record: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """The intent the draft compiles to (``(intent, None)``) or why it does not (``(None, refusal)``).

    The draft's ``created_at`` is the genesis timestamp, so the intent is the
    same on every read of the same answers.
    """
    try:
        draft = steps.parse_draft(record.get("draft"))
        return steps.build_intent(draft, record.get("created_at") or "1970-01-01T00:00:00+00:00"), None
    except steps.StepRefused as exc:
        return None, {"code": exc.code, "message": exc.message, **({"details": exc.details} if exc.details else {})}


def _docs_of_draft(record: dict[str, Any]) -> dict[str, Any]:
    intent, _why = draft_intent(record)
    return {"intent": intent, "draft": record.get("draft") or {}}


# ---------------------------------------------------------------------------
# Findings as check rows
# ---------------------------------------------------------------------------


def finding_id(locator: str, finding: str, model: str) -> str:
    raw = P.canonical([locator, finding, model])
    return "find_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _doc_for(docs: dict[str, Any], locator: str) -> tuple[Any, str]:
    kind, pointer = _split(locator)
    return docs.get(kind), pointer


def row(entry: dict[str, Any], docs: dict[str, Any], *, workspace: bool) -> dict[str, Any]:
    """One finding as a check object (02-checks "The slot for M10c")."""
    locator = entry["locator"]
    step = step_of_locator(locator, workspace=workspace)
    evidence = [
        {"kind": "locator", "value": locator},
        {"kind": "name", "name": "located_hash", "value": entry.get("located_hash")},
    ]
    doc, pointer = _doc_for(docs, locator)
    now = located_hash(doc, pointer) if doc is not None else None
    kind, _ = _split(locator)
    head = (_tokens(pointer) or [""])[0]
    if workspace:
        action: dict[str, Any] = {"kind": "step", "step": "plan"}
    elif kind == "draft" and head in steps.Draft.model_fields:
        action = {"kind": "field", "step": step, "field": head}
    else:
        action = {"kind": "step", "step": step}
    return {
        "check_id": FINDING_CHECK_ID,
        "subject": entry["finding_id"],
        "step": step,
        "level": SEVERITIES[entry["severity"]],
        "severity": entry["severity"],
        "source": "agent",
        "agent": entry["agent"],
        "message_key": None,
        "params": {},
        "message": entry["finding"],
        "why_key": None,
        "why_params": {},
        "why": entry.get("why"),
        "evidence": evidence,
        "threshold": None,
        "action": {**action, "label_key": f"checks.{FINDING_CHECK_ID}.action"},
        "refusal": None,
        "dismissible": True,
        "status": "open",
        "dismissal": None,
        "previously_dismissed": None,
        "evidence_digest": C.digest(FINDING_CHECK_ID, entry["finding_id"], evidence),
        "locator": locator,
        "outdated": bool(now is not None and entry.get("located_hash") and now != entry["located_hash"]),
        "reported_at": entry.get("reported_at"),
    }


def draft_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    entries = record.get(FINDINGS_KEY) or []
    if not entries:
        return []
    docs = _docs_of_draft(record)
    return [row(e, docs, workspace=False) for e in entries if isinstance(e, dict)]


def workspace_findings(ws: Path) -> list[dict[str, Any]]:
    path = Path(ws) / FINDINGS_FILE
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out, seen = [], set()
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("event") == "reported" and entry.get("finding_id") not in seen:
            seen.add(entry["finding_id"])
            out.append(entry)
    return out


def _workspace_docs(ws: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for kind in ("intent", "protocol"):
        try:
            out[kind] = json.loads((Path(ws) / f"{kind}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            out[kind] = None
    return out


def workspace_rows(ws: Path) -> list[dict[str, Any]]:
    entries = workspace_findings(ws)
    if not entries:
        return []
    docs = _workspace_docs(ws)
    return [row(e, docs, workspace=True) for e in entries]


def _open_findings(rows: list[dict[str, Any]], dismissals: list[dict[str, Any]]) -> int:
    C.with_dismissals(rows, dismissals)
    return sum(1 for r in rows if r["status"] == "open")


def _finding_entry(
    docs: dict[str, Any], *, locator: str, severity: str, finding: str, why: str | None, agent: dict[str, str],
    workspace: bool,
) -> dict[str, Any]:
    if severity not in SEVERITIES:
        raise AssistantRefused("BODY_INVALID", f"severity is one of {', '.join(SEVERITIES)}", {"field": "severity"})
    kind, pointer = _split(locator)
    if kind == "draft" and workspace:
        raise AssistantRefused("LOCATOR_INVALID", "a workspace finding points into intent.json, not a draft", {"locator": locator})
    if kind == "protocol" and not workspace:
        raise AssistantRefused("LOCATOR_INVALID", "a draft has no protocol yet; point into its intent", {"locator": locator})
    doc = docs.get(kind)
    if doc is None:
        hint = ("this draft does not compile to an intent yet; point into its answers with 'draft:/…'" if not workspace
                else f"this workspace has no readable {kind}.json")
        raise AssistantRefused("LOCATOR_INVALID", hint, {"locator": locator})
    found, value = resolve(doc, pointer)
    return {
        "finding_id": finding_id(locator, finding, agent["model"]),
        "locator": locator,
        "severity": severity,
        "finding": finding,
        "why": why,
        "agent": agent,
        "located_hash": P.value_hash(value if found else None),
        "reported_at": _now(),
    }


def report_on_draft(
    root: Path, session_id: str, *, locator: str, severity: str, finding: str, why: str | None, model: str,
) -> dict[str, Any]:
    """Add one finding to a draft (a side write); answers the row and whether it was new."""
    agent = agent_of(model, FINDING_TASK, (FINDING_TASK,))
    text = _text(finding, "finding", required=True)
    why = _text(why, "why", required=False)
    store = DraftStore(root)

    def change(record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        docs = _docs_of_draft(record)
        entry = _finding_entry(docs, locator=locator, severity=severity, finding=text, why=why, agent=agent, workspace=False)
        existing = record.get(FINDINGS_KEY) or []
        same = next((e for e in existing if e.get("finding_id") == entry["finding_id"]), None)
        if same is not None:
            return row(same, docs, workspace=False), False
        if _open_findings([row(e, docs, workspace=False) for e in existing], record.get("check_dismissals") or []) >= MAX_OPEN_FINDINGS:
            raise AssistantRefused("ASSISTANT_LIMIT_REACHED", f"this draft holds {MAX_OPEN_FINDINGS} open findings",
                                   {"limit": MAX_OPEN_FINDINGS, "kind": "findings"})
        record[FINDINGS_KEY] = [*existing, entry]
        return row(entry, docs, workspace=False), True

    _record, (out, created) = store.transact(session_id, change, answer=False)
    return {"status": "SUCCESS", "created": created, "finding": out}


def report_on_workspace(
    ws: Path, *, locator: str, severity: str, finding: str, why: str | None, model: str,
) -> dict[str, Any]:
    """Append one finding to ``audit/assistant_findings.jsonl`` and index it in the journal."""
    from scholar_harness.console.discovery_checks import dismissals
    from scholar_harness.workspace.audit import append_event

    ws = Path(ws)
    if not (ws / "protocol.json").is_file() and not (ws / "intent.json").is_file():
        raise AssistantRefused("WORKSPACE_NOT_FOUND", f"{ws} holds no protocol.json or intent.json", {"workspace": str(ws)})
    agent = agent_of(model, FINDING_TASK, (FINDING_TASK,))
    text = _text(finding, "finding", required=True)
    why = _text(why, "why", required=False)
    docs = _workspace_docs(ws)
    entry = _finding_entry(docs, locator=locator, severity=severity, finding=text, why=why, agent=agent, workspace=True)
    existing = workspace_findings(ws)
    same = next((e for e in existing if e["finding_id"] == entry["finding_id"]), None)
    if same is not None:
        return {"status": "SUCCESS", "created": False, "finding": row(same, docs, workspace=True)}
    if _open_findings([row(e, docs, workspace=True) for e in existing], dismissals(ws)) >= MAX_OPEN_FINDINGS:
        raise AssistantRefused("ASSISTANT_LIMIT_REACHED", f"this workspace holds {MAX_OPEN_FINDINGS} open findings",
                               {"limit": MAX_OPEN_FINDINGS, "kind": "findings"})
    path = ws / FINDINGS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "reported", **entry}, ensure_ascii=False) + "\n")
    append_event(
        ws, "ASSISTANT_FINDING_REPORTED", f"{entry['severity']} at {entry['locator']}: {entry['finding'][:120]}",
        agent=JOURNAL_AGENT, outputs=[FINDINGS_FILE],
        parameters={"finding_id": entry["finding_id"], "locator": entry["locator"], "severity": entry["severity"],
                    "model": agent["model"], "task": agent["task"], "task_version": agent["task_version"],
                    "method": "AGENT_PROPOSED"},
    )
    return {"status": "SUCCESS", "created": True, "finding": row(entry, docs, workspace=True)}


# ---------------------------------------------------------------------------
# Proposals on a draft
# ---------------------------------------------------------------------------


def _open_agent_proposals(record: dict[str, Any]) -> int:
    draft = record.get("draft") or {}
    return sum(
        1 for p in record.get("proposals") or []
        if str(p.get("source", "")).startswith("agent:") and P.view(p, draft)["status"] in ("open", "stale")
    )


def propose_on_draft(
    root: Path, session_id: str, *, field: str, op: str, value: Any, why: str, evidence: Any, model: str, task: str,
) -> dict[str, Any]:
    """Add one open proposal to a draft (a side write: no answer, no ``updated_at`` changes)."""
    agent = agent_of(model, task, PROPOSAL_TASKS)
    why_text = _text(why, "why", required=True)
    items = _evidence(evidence)
    store = DraftStore(root)

    def change(record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        draft = record.get("draft") or {}
        proposal = P.make(
            draft_id=session_id, draft=draft, source=f"agent:{agent['model']}", field=field, op=op, value=value,
            why=why_text, evidence=items, sources=("agent",),
        )
        proposal["agent"] = agent
        same = next((p for p in record.get("proposals") or [] if p["proposal_id"] == proposal["proposal_id"]), None)
        if same is not None:
            return P.view(same, draft), False
        try:
            new = P.apply_op(draft, field, op, value)
        except P.ProposalRefused as exc:
            if exc.code == "PROPOSAL_STALE":  # the named concept is not in the draft
                raise P.ProposalRefused("PROPOSAL_TARGET_UNSUPPORTED", "no concept of that name in the draft", 422,
                                        {"field": field, "op": op}) from exc
            raise
        if P.canonical(new) == P.canonical(draft):
            raise P.ProposalRefused("PROPOSAL_NOT_OPEN", "the draft already holds this value", 409, {"status": "present"})
        steps.parse_draft(new, saving=True)  # refused here exactly as Apply would refuse it
        if _open_agent_proposals(record) >= MAX_OPEN_PROPOSALS:
            raise AssistantRefused("ASSISTANT_LIMIT_REACHED", f"this draft holds {MAX_OPEN_PROPOSALS} open assistant suggestions",
                                   {"limit": MAX_OPEN_PROPOSALS, "kind": "proposals"})
        P.add_open(record, proposal)
        return P.view(proposal, draft), True

    _record, (out, created) = store.transact(session_id, change, answer=False)
    return {"status": "SUCCESS", "created": created, "proposal": out}


def propose_on_workspace(
    ws: Path, *, field: str, op: str, value: Any, why: str, evidence: Any, model: str, task: str,
) -> dict[str, Any]:
    """Add one open proposal to a workspace's search (M10c D5, decision item 9(a)); nothing is applied.

    Listed as a card on Discovery Plan; only the researcher's Apply amends
    ``intent.json`` and recompiles ``protocol.json``.
    """
    from scholar_harness import workspace_proposals as WP
    from scholar_harness.workspace.audit import append_event

    agent = agent_of(model, task, PROPOSAL_TASKS)
    why_text = _text(why, "why", required=True)
    items = _evidence(evidence)
    ws = Path(ws)
    if not (ws / "protocol.json").is_file() or not (ws / "intent.json").is_file():
        raise AssistantRefused("WORKSPACE_NOT_FOUND", f"{ws} holds no protocol.json and intent.json", {"workspace": str(ws)})
    source = f"agent:{agent['model']}"
    limit = AssistantRefused("ASSISTANT_LIMIT_REACHED", f"this workspace holds {MAX_OPEN_PROPOSALS} open assistant suggestions",
                             {"limit": MAX_OPEN_PROPOSALS, "kind": "proposals"})
    out, created = WP.make(
        ws, source=source, field=field, op=op, value=value, why=why_text, evidence=items, extra={"agent": agent},
        open_limit=MAX_OPEN_PROPOSALS, limit_error=limit,
    )
    if created:
        append_event(
            ws, "ASSISTANT_PROPOSAL_RECORDED", f"{op} on {field} suggested by {source}",
            agent=JOURNAL_AGENT, outputs=[WP.PROPOSALS_FILE],
            parameters={"proposal_id": out["proposal_id"], "field": field, "op": op, "model": agent["model"],
                        "task": agent["task"], "task_version": agent["task_version"], "method": "AGENT_PROPOSED",
                        "protocol_fingerprint": out["base"]["protocol_fingerprint"]},
        )
    return {"status": "SUCCESS", "created": created, "proposal": out}


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def list_drafts(root: Path) -> dict[str, Any]:
    store = DraftStore(root)
    items = []
    for item in store.listing():
        out = dict(item)
        if item.get("readable", True):
            try:
                record = store.load(item["session_id"])
            except DraftRefused:
                record = None
            if record is not None:
                listing = P.listing(record)
                out["open_proposals"] = sum(v["open"] for v in listing["by_step"].values())
                out["findings"] = len(record.get(FINDINGS_KEY) or [])
        items.append(out)
    return {"status": "SUCCESS", "workspaces_root": str(Path(root)), "drafts": items}


def _pool_summary(sessions: Any, session_id: str, record: dict[str, Any]) -> dict[str, Any] | None:
    """The sample as the app shows it: the papers the researcher left out are not in it (M10b Part C)."""
    from scholar_harness.recon import sample as sample_mod
    from scholar_harness.recon.session import ReconRefused

    try:
        if not sessions.exists(session_id):
            return None
        pool, raw, _path = sessions.effective(session_id, sample_mod.keys_of(record.get("sample_exclusions")))
    except ReconRefused:
        return None
    docs = [d for d in pool.get("docs") or [] if isinstance(d, dict)]
    left_out = (record.get("sample_exclusions") or {}).get("items") or []
    return {
        "providers": pool.get("providers"),
        "legs": [{k: leg.get(k) for k in ("provider", "status", "fetched", "total", "executed_query", "error_code")}
                 for leg in raw.get("legs") or [] if isinstance(leg, dict)],
        "papers": [{k: d.get(k) for k in ("title", "doi", "year", "provider")} for d in docs],
        "left_out_by_researcher": [{k: i.get(k) for k in ("doi", "title", "year", "provider")}
                                   for i in left_out if isinstance(i, dict)],
    }


def read_draft(root: Path, session_id: str, *, sessions: Any) -> dict[str, Any]:
    """Everything an assistant may read about one draft; writes nothing (decision item 12)."""
    from scholar_harness.console.api.inception import draft_checks

    record = DraftStore(root).load(session_id)
    intent, why_not = draft_intent(record)
    items, waiting, partial, _made = draft_checks(Path(root), sessions, session_id, record, make_proposal=None)
    C.with_dismissals(items, record.get("check_dismissals") or [])
    listing = P.listing(record)
    return {
        "status": "SUCCESS",
        "session_id": session_id,
        "updated_at": record.get("updated_at"),
        "emitted": record.get("emitted"),
        "draft": record.get("draft") or {},
        "intent": intent,
        "intent_refused": why_not,
        "grounding": record.get("grounding"),
        "checks": C.respond(items, steps_order=C.INCEPTION_STEPS, step=None, waiting=waiting, partial=partial,
                            scope={"kind": "draft", "id": session_id, "updated_at": record.get("updated_at")}),
        "proposals": listing["proposals"],
        "pool": _pool_summary(sessions, session_id, record),
    }


class _State:
    """The ``request.app.state`` the discovery routes read, for one workspace (no console running)."""

    def __init__(self, ws: Path):
        self.workspace = ws


class _App:
    def __init__(self, ws: Path):
        self.state = _State(ws)


class _Request:
    def __init__(self, ws: Path):
        self.app = _App(ws)


def read_workspace(ws: Path) -> dict[str, Any]:
    """Everything an assistant may read about a workspace's protocol and search; writes nothing."""
    from fastapi import HTTPException

    from scholar_harness.console import discovery_checks as DC
    from scholar_harness.console.api import discovery as D

    ws = Path(ws).resolve()
    if not (ws / "protocol.json").is_file():
        raise AssistantRefused("WORKSPACE_NOT_FOUND", f"{ws} holds no protocol.json", {"workspace": str(ws)})
    request = _Request(ws)

    def read(path: str) -> Any:
        try:
            return json.loads((ws / path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def route(fn, *args, **kwargs) -> Any:
        try:
            return fn(*args, **kwargs)
        except HTTPException as exc:
            return {"refused": exc.detail}
        except D.Refused as exc:
            return {"refused": {"code": exc.code, "message": str(exc)}}

    plan = route(D.plan, request)
    recall = route(D.last_recall, request)
    try:
        items, waiting, partial, scope = DC.compute(request)
        C.with_dismissals(items, DC.dismissals(ws))
        checks = C.respond(items, steps_order=C.DISCOVERY_STEPS, step=None, scope=scope, waiting=waiting, partial=partial)
    except (HTTPException, D.Refused) as exc:
        checks = {"refused": getattr(exc, "detail", None) or {"code": getattr(exc, "code", ""), "message": str(exc)}}
    return {
        "status": "SUCCESS",
        "workspace": str(ws),
        "intent": read("intent.json"),
        "protocol": read("protocol.json"),
        "plan": plan,
        "recall": recall,
        "checks": checks,
        # D5: the workspace's open and decided proposals, stale derived (the Plan cards' read).
        "proposals": route(_workspace_proposals, ws),
        # Every line of audit/proposals.jsonl, genesis's draft history included.
        "proposal_history": _proposal_lines(ws),
    }


def _workspace_proposals(ws: Path) -> Any:
    from scholar_harness import workspace_proposals as WP

    try:
        return WP.listing(ws)
    except P.ProposalRefused as exc:
        return {"refused": {"code": exc.code, "message": exc.message}}


def _proposal_lines(ws: Path) -> list[dict[str, Any]]:
    try:
        lines = (ws / P.PROPOSALS_FILE).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out
