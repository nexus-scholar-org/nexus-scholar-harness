"""Skill-contract frontmatter (spec 03 §3) and validation (§3/§8).

A skill ships YAML frontmatter with a closed vocabulary:

```yaml
---
name: scholar-pdf-kit
description: ...one sentence...
applies_to: [extractor-a, extractor-b]   # ⊆ roles/*.json
requires: [scholar-pdf]                  # drives Preflight
variables: [CLI, WORKSPACE, CACHE, CONFIG, SKILL_DIR]  # ⊆ REGISTRY
returns: json | prose | files
layer: domain | procedure | policy
---
```

Semantic checks (spec 03 §8): ``applies_to`` ⊆ role ids present as
``roles/*.json`` (Phase A records) — an orphan skill is a defect; every used
``{PLACEHOLDER}`` in the body must be declared; a skill declaring
``requires`` must carry a ``## Preflight`` section (a missing refusal path
is a defect, never a traceback).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from scholar_harness.contracts.envelope.registry import RefusalCode

from .variables import VARIABLE_PATTERN, audit_text

RETURNS = ("json", "prose", "files")
LAYERS = ("domain", "procedure", "policy")


class SkillContract(BaseModel):
    """The §3 skill contract, shape-only (semantic checks are separate)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    applies_to: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    returns: Literal["json", "prose", "files"] = "prose"
    layer: Literal["domain", "procedure", "policy"] = "domain"

    @field_validator("name", "description")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must be a non-blank string")
        return value

    @field_validator("applies_to", "requires", "variables")
    @classmethod
    def unique_non_empty(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("duplicates are a defect, not a set")
        if any(not entry for entry in value):
            raise ValueError("empty entries are not names")
        return value

    @field_validator("variables")
    @classmethod
    def registered(cls, value: list[str]) -> list[str]:
        from .variables import REGISTRY

        unknown = [entry for entry in value if entry not in REGISTRY]
        if unknown:
            raise ValueError(f"placeholders not in the registry: {unknown}")
        return value


class SkillContractRefusal(Exception):
    """Named refusal for a defective skill tree (Phase B/C convention)."""

    def __init__(self, refusal_code: RefusalCode, detail: str) -> None:
        self.refusal_code = refusal_code
        self.detail = detail
        super().__init__(f"{refusal_code}: {detail}")


_FM_RE = re.compile(r"\A(?P<fm>---\n.*?\n---\n?)(?P<body>.*)\Z", re.DOTALL)


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    """The frontmatter subset: scalars, inline lists, block lists.

    No general YAML — only what the §3 contract needs (deterministic
    parsing, no anchor/alias surprises).
    """

    data: dict[str, Any] = {}
    key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line == "---":  # closing fence of the frontmatter block
            key = None
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        inline = re.match(r"^\s*([a-z_]+)\s*:\s*(.*?)\s*$", line)
        if inline:
            key, value = inline.group(1), inline.group(2)
            if value == "":
                data[key] = []  # a block sequence follows
                continue
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                data[key] = [v.strip() for v in inner.split(",")] if inner else []
            else:
                data[key] = value.strip(" \"'")
                key = None
            continue
        block = re.match(r"^\s+-\s*(.+?)\s*$", line)
        if block and key is not None:
            entries = data[key]
            if not isinstance(entries, list):
                raise ValueError(f"{key}: block list started but key holds {entries!r}")
            entries.append(block.group(1).strip(" \"'"))
            continue
        raise ValueError(f"unparsable frontmatter line: {raw!r}")
    return data


def parse_frontmatter(
    skill_text: str, path: Path | None = None
) -> tuple[SkillContract, str]:
    """Parse the contract frontmatter + body; refuse shape defects by name."""

    match = _FM_RE.match(skill_text)
    if match is None:
        raise SkillContractRefusal(
            RefusalCode.INVALID_OUTPUT,
            f"{path or '<skill>'}: missing '---' frontmatter block (spec 03 §3)",
        )
    raw = _parse_yaml_subset(match.group("fm"))
    try:
        contract = SkillContract.model_validate(raw)
    except Exception as exc:
        raise SkillContractRefusal(
            RefusalCode.INVALID_OUTPUT,
            f"{path or '<skill>'}: frontmatter {exc}",
        ) from exc
    return contract, match.group("body")


def known_role_ids(roles_dir: str | Path) -> set[str]:
    """Role ids present as ``roles/<id>.json``."""

    roles_dir = Path(roles_dir)
    if not roles_dir.is_dir():
        raise SkillContractRefusal(
            RefusalCode.BLOCKED_INPUT, f"roles directory missing: {roles_dir}"
        )
    return {p.stem for p in roles_dir.glob("*.json")}


def validate_frontmatter(
    contract: SkillContract,
    *,
    roles_dir: str | Path,
    skill_text: str,
    path: Path | None = None,
) -> None:
    """Semantic side of the §3 contract (spec 03 §8 assertions)."""

    label = str(path or contract.name)
    roles = known_role_ids(roles_dir)
    unknown = sorted(set(contract.applies_to) - roles)
    if unknown:
        raise SkillContractRefusal(
            RefusalCode.INVALID_OUTPUT,
            f"{label}: applies_to names roles that do not exist: {unknown}",
        )

    match = _FM_RE.match(skill_text)
    body_only = match.group("body") if match is not None else skill_text

    if contract.requires and not re.search(
        r"^##\s+Preflight\b", body_only, re.MULTILINE
    ):
        raise SkillContractRefusal(
            RefusalCode.INVALID_OUTPUT,
            f"{label}: declares requires={contract.requires} but has no "
            "'## Preflight' section (spec 03 §7) — a missing refusal path",
        )

    # Every used placeholder must be declared; declared must be used.
    used = {name for name, _arg in VARIABLE_PATTERN.findall(body_only)}
    undeclared = sorted(used - set(contract.variables))
    if undeclared:
        raise SkillContractRefusal(
            RefusalCode.INVALID_OUTPUT,
            f"{label}: body uses placeholders not declared in frontmatter: "
            f"{undeclared}",
        )


def audit_skill_file(path: str | Path) -> list[dict[str, Any]]:
    """Audit one ``SKILL.md`` file end to end (frontmatter + body scan)."""

    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    contract, body = parse_frontmatter(text, file_path)
    findings = audit_text(body)
    return [
        {"line": f.line_no, "rule": f.rule, "detail": f.detail} for f in findings
    ] or []


__all__ = [
    "RETURNS",
    "LAYERS",
    "SkillContract",
    "SkillContractRefusal",
    "audit_skill_file",
    "known_role_ids",
    "parse_frontmatter",
    "validate_frontmatter",
]
