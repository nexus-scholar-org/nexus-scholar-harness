"""Agent screening proposals (agent-system §3–§4, M1a).

A proposal is the agent's draft for one record: an answer per criterion, each
with a verbatim evidence span, and a `cannot_decide` flag. It is advice, never
a decision: it is stored in its own append-only log
(`literature/screening/proposals/proposals.jsonl`), it never reaches a batch
decision file, and a human decides with it hidden first.

**The model never chooses the outcome.** `derive_outcome` (rule table
`RULES_VERSION`) turns the answers into one:
- every inclusion criterion `yes` and no exclusion `yes` → INCLUDE;
- any exclusion `yes`, or any inclusion `no` → EXCLUDE, with that criterion as
  the reason code (`EXC-n`, or `FAILS-INC-n`);
- any `not_reported`, `cannot_decide`, or failed check → MAYBE ("Unclear → full
  text"), never EXCLUDE.

Plain-code validators run on every proposal: the schema, one answer per
criterion, and each evidence quote found verbatim at its offsets in the
record's title and abstract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scholar_harness.workspace.audit import append_event

PROPOSALS_FILE = Path("literature") / "screening" / "proposals" / "proposals.jsonl"
RULES_VERSION = "screening-rules-v1"
ANSWERS = frozenset({"yes", "no", "not_reported"})
JOURNAL_ACTION = "SCREENING_PROPOSAL_SUBMITTED"


@dataclass(frozen=True)
class Criteria:
    inclusion: tuple[str, ...]
    exclusion: tuple[str, ...]

    @classmethod
    def from_protocol(cls, protocol: dict[str, Any]) -> Criteria:
        criteria = protocol.get("screening_criteria") or {}

        def ids(kind: str) -> tuple[str, ...]:
            return tuple(
                str(item["id"]) for item in criteria.get(kind) or [] if isinstance(item, dict) and item.get("id")
            )

        return cls(ids("inclusion"), ids("exclusion"))

    @property
    def all(self) -> tuple[str, ...]:
        return self.inclusion + self.exclusion


def record_text(title: str | None, abstract: str | None) -> str:
    """The text evidence offsets index into: title, a blank line, abstract."""
    return f"{title or ''}\n\n{abstract or ''}"


def input_sha256(title: str | None, abstract: str | None) -> str:
    return "sha256:" + hashlib.sha256(record_text(title, abstract).encode("utf-8")).hexdigest()


def proposal_id(task_version: str, input_hash: str, protocol_fingerprint: str, model: str) -> str:
    """Contract §2: sha256(task_version, input_sha256, protocol_fingerprint, model)."""
    payload = json.dumps([task_version, input_hash, protocol_fingerprint, model], separators=(",", ":"))
    return "PRP-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def validate_output(output: Any, criteria: Criteria, text: str) -> list[dict[str, Any]]:
    """Run every plain-code check; each returns {name, ok, detail}."""
    checks: list[dict[str, Any]] = []
    if not isinstance(output, dict) or not isinstance(output.get("criteria"), list):
        return [{"name": "schema", "ok": False, "detail": "output must be an object with a criteria list"}]
    answers = output["criteria"]
    ids = [a.get("id") for a in answers if isinstance(a, dict)]
    schema_ok = all(
        isinstance(a, dict) and a.get("answer") in ANSWERS for a in answers
    ) and isinstance(output.get("cannot_decide", False), bool)
    checks.append({"name": "schema", "ok": schema_ok, "detail": "" if schema_ok else "unknown answer value"})
    complete = sorted(ids) == sorted(criteria.all) and len(ids) == len(set(ids))
    checks.append(
        {
            "name": "one_answer_per_criterion",
            "ok": complete,
            "detail": "" if complete else f"expected {sorted(criteria.all)}, got {sorted(map(str, ids))}",
        }
    )
    bad_quotes = []
    for answer in answers:
        if not isinstance(answer, dict) or answer.get("answer") == "not_reported":
            continue
        evidence = answer.get("evidence") or {}
        quote, start, end = evidence.get("text"), evidence.get("start"), evidence.get("end")
        if not (isinstance(quote, str) and quote and isinstance(start, int) and isinstance(end, int)):
            bad_quotes.append(f"{answer.get('id')}: no evidence span")
        elif text[start:end] != quote:
            bad_quotes.append(f"{answer.get('id')}: quote not at its offsets")
    checks.append(
        {"name": "quote_in_source", "ok": not bad_quotes, "detail": "; ".join(bad_quotes)}
    )
    return checks


def derive_outcome(
    output: Any, criteria: Criteria, checks: list[dict[str, Any]]
) -> tuple[str, str | None]:
    """The rule table (`RULES_VERSION`): (outcome, reason_code)."""
    if not all(check["ok"] for check in checks):
        return "MAYBE", None
    if output.get("cannot_decide"):
        return "MAYBE", None
    answers = {a["id"]: a["answer"] for a in output["criteria"]}
    if any(answers[c] == "not_reported" for c in criteria.all):
        return "MAYBE", None
    for exclusion in criteria.exclusion:
        if answers[exclusion] == "yes":
            return "EXCLUDE", exclusion
    for inclusion in criteria.inclusion:
        if answers[inclusion] == "no":
            return "EXCLUDE", f"FAILS-{inclusion}"
    return "INCLUDE", None


def submit_proposal(
    workspace: Path,
    *,
    study_id: str,
    title: str | None,
    abstract: str | None,
    output: Any,
    protocol: dict[str, Any],
    protocol_fingerprint: str,
    provenance: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    """Validate, derive the outcome, append one proposal line, journal it.

    `provenance` carries the agent-system §4 fields the caller knows:
    `task_id`, `task_version`, `prompt_sha256`, `driver`, `model`, `effort`,
    `batch_binding`, `usage`, `cost_estimate`, `request_id`, `batch_id`.
    A failed check is recorded, and the outcome becomes Unclear.
    """
    ws = Path(workspace)
    criteria = Criteria.from_protocol(protocol)
    text = record_text(title, abstract)
    checks = validate_output(output, criteria, text)
    outcome, reason_code = derive_outcome(output, criteria, checks)
    in_hash = input_sha256(title, abstract)
    task_version = str(provenance.get("task_version") or "")
    model = str(provenance.get("model") or "")
    record = {
        **{k: provenance.get(k) for k in (
            "task_id", "task_version", "prompt_sha256", "driver", "model", "effort",
            "batch_binding", "usage", "cost_estimate", "request_id", "batch_id",
        )},
        "proposal_id": proposal_id(task_version, in_hash, protocol_fingerprint, model),
        "study_id": study_id,
        "input_sha256": in_hash,
        "protocol_fingerprint": protocol_fingerprint,
        "rules_version": RULES_VERSION,
        "output": output,
        "validators": checks,
        "derived_outcome": outcome,
        "reason_code": reason_code,
        "cannot_decide": bool(isinstance(output, dict) and output.get("cannot_decide")),
        "created_at": created_at,
    }
    path = ws / PROPOSALS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    size = path.stat().st_size if path.exists() else 0
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    try:
        append_event(
            ws,
            JOURNAL_ACTION,
            f"Stored agent proposal for {study_id} (derived {outcome})",
            agent=f"scholar-harness/proposals ({record.get('driver') or 'unknown'})",
            outputs=[str(PROPOSALS_FILE).replace("\\", "/")],
            parameters={
                "proposal_id": record["proposal_id"],
                "study_id": study_id,
                "model": model,
                "task_version": task_version,
            },
            metrics={"failed_checks": sum(1 for c in checks if not c["ok"])},
            refresh_index=False,
        )
    except OSError:
        with path.open("r+b") as handle:
            handle.truncate(size)
        raise
    return record


def read_proposals(workspace: Path) -> list[dict[str, Any]]:
    path = Path(workspace) / PROPOSALS_FILE
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest_proposal(workspace: Path, study_id: str) -> dict[str, Any] | None:
    """The newest proposal for a study, or None."""
    mine = [p for p in read_proposals(workspace) if p.get("study_id") == study_id]
    return max(mine, key=lambda p: (p.get("created_at") or "", p["proposal_id"]), default=None)
