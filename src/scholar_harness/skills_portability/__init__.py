"""Skill portability (agent-layer Phase D, spec ``03_skills_portability.md``).

The skills are the strongest asset in the repository and the least portable.
This module gives them a machine-checkable contract:

* ``REGISTRY`` — the environment placeholders a skill body may use
  (spec 03 §4). A skill names *roles for parts of an environment*;
  the adapter (dev loop or app) binds them. No literal ``uv run``, absolute
  paths, bare ``tools/``, or ``workspaces/<literal>`` survive a rewrite.
* ``parse_frontmatter`` / ``validate_frontmatter`` — the skill contract
  frontmatter (spec 03 §3): ``name``, ``applies_to`` ⊆ ``roles/*.json``,
  ``variables`` ⊆ ``REGISTRY``, ``returns`` ∈ {json, prose, files}, ``layer``
  ∈ {domain, procedure, policy}, and a ``Preflight`` section whenever
  ``requires`` is declared.
* ``audit_text`` — the mechanical portability violations (spec 03 §8),
  each reported with a line number. Deterministic, no network.
* ``render`` — bind placeholders under a ``Preamble`` (dev or app).
* ``generate_skill_meta`` — ``SKILL.meta.json`` regenerated at install from
  ``plugins.json`` (spec 03 §5): the manifest is the only source of pins.
  A skill body never restates a version.

Refusal convention (Phase B/C): named codes from the frozen envelope registry
(``BLOCKED_INPUT`` for a missing requirement, ``INVALID_OUTPUT`` for a bad
record). Nothing here returns a silent empty result.
"""

from .variables import (
    CLI_SHORTS,
    DEV_KIT_ROOT_TEMPLATE,
    KIT_SHORTS,
    Preamble,
    REGISTRY,
    VARIABLE_PATTERN,
    audit_text,
    render,
    rewrite_text,
)
from . import frontmatter
from .frontmatter import (
    SkillContract,
    known_role_ids,
    parse_frontmatter,
    validate_frontmatter,
)
from .meta import generate_skill_meta

__all__ = [
    "CLI_SHORTS",
    "DEV_KIT_ROOT_TEMPLATE",
    "KIT_SHORTS",
    "Preamble",
    "REGISTRY",
    "VARIABLE_PATTERN",
    "SkillContract",
    "audit_text",
    "generate_skill_meta",
    "known_role_ids",
    "parse_frontmatter",
    "render",
    "rewrite_text",
    "validate_frontmatter",
]
