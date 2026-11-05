"""The screening proposal task (agent-system §3, §5).

One structured call per record: an answer per criterion (`yes`, `no`,
`not_reported`), a verbatim quote for each `yes` or `no`, a `cannot_decide`
flag and one sentence of reasoning. The model never chooses the outcome; the
engine's rule table derives it (`scholar_harness.screening.proposals`).

Two things are done in plain code here rather than asked of the model:

- **Offsets.** The model returns a quote only. `to_proposal_output` locates it
  in the record text the validators index into; a quote that is not there is
  given offsets that fail `quote_in_source`, so the record becomes Unclear.
- **The prompt hash.** `Task.prompt_sha256` hashes the template, the output
  schema and the task version, so any change to them is a new task version
  under the prompt gate.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ANSWERS = ("yes", "no", "not_reported")


@dataclass(frozen=True)
class Criterion:
    id: str
    kind: str  # "inclusion" | "exclusion"
    text: str


@dataclass(frozen=True)
class Task:
    task_id: str
    task_version: str
    template: str
    defaults: dict[str, Any]
    settings: dict[str, Any] = field(default_factory=dict)

    @property
    def prompt_sha256(self) -> str:
        payload = json.dumps(
            {"task_version": self.task_version, "template": self.template, "schema": output_schema(("ID",))},
            sort_keys=True,
        )
        return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_task() -> Task:
    config = tomllib.loads((HERE / "task.toml").read_text(encoding="utf-8"))
    return Task(
        task_id=config["task_id"],
        task_version=config["task_version"],
        template=(HERE / "prompt.md").read_text(encoding="utf-8"),
        defaults=dict(config["defaults"]),
        settings={k: v for k, v in config.items() if isinstance(v, dict) and k != "defaults"},
    )


def load_prices() -> dict[str, Any]:
    return tomllib.loads((HERE / "prices.toml").read_text(encoding="utf-8"))


def criteria_from_protocol(protocol: dict[str, Any]) -> list[Criterion]:
    block = protocol.get("screening_criteria") or {}
    out: list[Criterion] = []
    for kind in ("inclusion", "exclusion"):
        for item in block.get(kind) or []:
            if isinstance(item, dict) and item.get("id"):
                text = str(item.get("description") or item.get("text") or item.get("criterion") or "")
                out.append(Criterion(str(item["id"]), kind, text))
    return out


def system_prompt(task: Task, criteria: list[Criterion]) -> str:
    """The stable prefix shared by every record of a run (cached; no ids or times)."""
    lines = [f"- `{c.id}` ({c.kind}): {c.text}".rstrip() for c in criteria]
    return task.template.replace("{criteria}", "\n".join(lines))


def record_message(title: str | None, abstract: str | None) -> str:
    """The per-record user message; the record is wrapped as data (agent-system §7)."""
    return f"<record>\nTitle: {title or ''}\n\nAbstract: {abstract or ''}\n</record>"


def output_schema(criterion_ids: tuple[str, ...] | list[str]) -> dict[str, Any]:
    """The JSON schema sent as structured output; ids are pinned to the protocol."""
    return {
        "type": "object",
        "properties": {
            "criteria": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "enum": list(criterion_ids)},
                        "answer": {"type": "string", "enum": list(ANSWERS)},
                        "quote": {"type": "string"},
                    },
                    "required": ["id", "answer", "quote"],
                    "additionalProperties": False,
                },
            },
            "cannot_decide": {"type": "boolean"},
            "reasoning": {"type": "string"},
        },
        "required": ["criteria", "cannot_decide", "reasoning"],
        "additionalProperties": False,
    }


def record_text(title: str | None, abstract: str | None) -> str:
    """The text the engine's validators index into (title, blank line, abstract)."""
    from scholar_harness.screening.proposals import record_text as engine_record_text

    return engine_record_text(title, abstract)


def to_proposal_output(raw: Any, title: str | None, abstract: str | None) -> Any:
    """Map the model's answer to the engine's proposal shape, locating each quote.

    Anything that is not the expected object is passed through unchanged, so
    the engine's schema check fails it and the record becomes Unclear.
    """
    if not isinstance(raw, dict) or not isinstance(raw.get("criteria"), list):
        return raw
    text = record_text(title, abstract)
    criteria = []
    for item in raw["criteria"]:
        if not isinstance(item, dict):
            criteria.append(item)
            continue
        quote = item.get("quote") if isinstance(item.get("quote"), str) else ""
        entry: dict[str, Any] = {"id": item.get("id"), "answer": item.get("answer")}
        if item.get("answer") != "not_reported":
            start = text.find(quote) if quote else -1
            # Not found: offsets that cannot match, so quote_in_source fails.
            entry["evidence"] = {"text": quote, "start": start, "end": start + len(quote) if start >= 0 else -1}
        criteria.append(entry)
    out: dict[str, Any] = {"criteria": criteria, "cannot_decide": bool(raw.get("cannot_decide", False))}
    if isinstance(raw.get("reasoning"), str):
        out["reasoning"] = raw["reasoning"]
    return out
