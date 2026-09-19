from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / ".opencode" / "agent"


def _agent(name: str) -> str:
    path = AGENT_DIR / f"{name}.md"
    assert path.is_file(), f"missing OpenCode agent: {path}"
    return path.read_text(encoding="utf-8")


def _frontmatter(text: str) -> str:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "agent definition must start with YAML frontmatter"
    return match.group(1)


def test_development_agents_have_enforceable_roles() -> None:
    coder = _frontmatter(_agent("coder"))
    reviewer = _frontmatter(_agent("reviewer"))
    orchestrator = _frontmatter(_agent("orchestrator"))

    assert "mode: subagent" in coder
    assert "permission: allow" in coder
    assert "mode: subagent" in reviewer
    assert "edit: deny" in reviewer
    assert "bash: ask" in reviewer
    assert "read: allow" in reviewer
    assert "mode: primary" in orchestrator
    assert "permission: allow" in orchestrator


def test_agents_encode_contract_and_scientific_gates() -> None:
    coder = _agent("coder")
    reviewer = _agent("reviewer")
    orchestrator = _agent("orchestrator")

    for text in (coder, reviewer, orchestrator):
        assert "canonical" in text.lower()
        assert "parent hash" in text.lower()
        assert "provider failure" in text.lower()
        assert "semantic similarity" in text.lower()
        assert "tools/<kit>/" in text

    assert "BLOCKED_CANONICAL_REPO" in coder
    assert "BLOCKED_CANONICAL_REPO" in orchestrator
    assert "critic failure" in coder.lower()
    assert "critic fail" in orchestrator.lower()
    assert "permission" in reviewer.lower()
    assert "actual diff/artifacts" in reviewer


def test_orchestrator_task_packet_and_loop_are_explicit() -> None:
    orchestrator = _agent("orchestrator")

    for field in (
        "TASK_ID",
        "OBJECTIVE",
        "OWNER_SURFACE",
        "DEPENDENCIES_AND_EVIDENCE",
        "ALLOWED_PATHS",
        "FORBIDDEN_PATHS",
        "ACCEPTANCE_CRITERIA",
        "NEGATIVE_CASES",
        "VALIDATION_COMMANDS",
        "TOOLKIT_SYNC_AND_PIN_PLAN",
    ):
        assert field in orchestrator

    assert "at most three coder-reviewer cycles" in orchestrator
    assert "reviewer `APPROVE`" in orchestrator
    assert "tester failure reopens" in orchestrator.lower()


def test_agent_markdown_links_resolve() -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

    for name in ("coder", "reviewer", "orchestrator"):
        path = AGENT_DIR / f"{name}.md"
        for target in link_pattern.findall(_agent(name)):
            if "://" in target or target.startswith("#"):
                continue
            clean_target = target.split("#", 1)[0]
            resolved = (path.parent / clean_target).resolve()
            assert resolved.exists(), f"broken link in {path}: {target}"


def test_agents_do_not_reference_obsolete_phase7_path() -> None:
    obsolete = "docs/phase_7_distribution/README.md"
    for name in ("coder", "reviewer", "orchestrator"):
        assert obsolete not in _agent(name)
