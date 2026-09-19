from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / ".opencode" / "agent"
SKILL_DIR = ROOT / ".agents" / "skills"
AGENTS = (
    "screener",
    "screening-critic",
    "extractor-a",
    "extractor-b",
    "extraction-critic",
    "adjudicator",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", AGENTS)
def test_scientific_agents_are_discoverable_subagents(name: str) -> None:
    text = _read(AGENT_DIR / f"{name}.md")
    assert re.match(r"\A---\n.*?\n---\n", text, re.DOTALL)
    assert "mode: subagent" in text
    assert "read: allow" in text
    assert "bash: ask" in text
    assert "skill: allow" in text


def test_shared_role_contracts_exist_and_are_referenced() -> None:
    doer = _read(SKILL_DIR / "doer-contract" / "SKILL.md")
    critic = _read(SKILL_DIR / "critic-contract" / "SKILL.md")
    assert "name: doer-contract" in doer
    assert "name: critic-contract" in critic

    for name in ("screener", "extractor-a", "extractor-b", "adjudicator"):
        assert "doer-contract" in _read(AGENT_DIR / f"{name}.md")
    for name in ("screening-critic", "extraction-critic"):
        assert "critic-contract" in _read(AGENT_DIR / f"{name}.md")


def test_port_is_field_agnostic_and_machine_portable() -> None:
    forbidden = (
        "AGRIEVAL-",
        "agrieval-2026",
        "AppData\\Local\\Temp",
        "opencode/mimo",
        "opencode/ling",
        "opencode/muse",
        "paper × dataset × task",
    )
    for name in AGENTS:
        text = _read(AGENT_DIR / f"{name}.md")
        for value in forbidden:
            assert value not in text, f"{name} retains project-specific value {value!r}"


def test_independence_and_adjudication_boundaries_are_explicit() -> None:
    extractor_b = _read(AGENT_DIR / "extractor-b.md")
    adjudicator = _read(AGENT_DIR / "adjudicator.md")
    critic = _read(AGENT_DIR / "extraction-critic.md")

    assert "Never open extractor-a output" in extractor_b
    assert "never overwrite A or B" in adjudicator
    assert "Do not adjudicate disagreements or repair records" in critic
    assert "deterministic pass never cancels a critic failure" in _read(
        SKILL_DIR / "critic-contract" / "SKILL.md"
    )


def test_contract_v1_screening_states_are_not_collapsed() -> None:
    screener = _read(AGENT_DIR / "screener.md")
    assert "INCLUDE|EXCLUDE|MAYBE|CONFLICT" in screener
    assert "never map uncertainty to terminal exclusion" in screener
    assert "canonical `study_id`" in screener


def test_agents_require_lineage_and_audit_provenance() -> None:
    for name in AGENTS:
        text = _read(AGENT_DIR / f"{name}.md").lower()
        assert "hash" in text
        assert "schema" in text
        assert "output" in text or "assigned critique" in text

    doer = _read(SKILL_DIR / "doer-contract" / "SKILL.md").lower()
    assert "parent hashes" in doer
    assert "workspace-manager" in doer
    assert "real actor" in doer
