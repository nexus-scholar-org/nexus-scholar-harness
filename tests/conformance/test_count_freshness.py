"""Surface count freshness.

The repo documents cardinal numbers (8 kits, 11 mirrored skills, 14 console
actions, 18 MCP tools) in ``docs/kits_surface_matrix.md`` / AGENTS.md.  These
must match runtime reality so prose never silently corrodes.  The skill check
also guards mirror completeness: the plugin bundle must contain every
canonical skill except ``pull-request-gate`` (the sync script's one exclusion).
"""

from __future__ import annotations

from pathlib import Path

from scholar_agent.server import mcp

from scholar_harness.console.runtimes.actions import ACTIONS

REPO_ROOT = Path(__file__).resolve().parents[2]

TOOLS_DIR = REPO_ROOT / "tools"
SKILLS_CANONICAL = REPO_ROOT / ".agents" / "skills"
SKILLS_MIRROR = (
    REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "skills"
)

EXPECTED_KITS = 8
EXPECTED_ACTIONS = 14
EXPECTED_MCP_TOOLS = 18
EXPECTED_MIRRORED_SKILLS = 11

# ``pull-request-gate`` is intentionally not distributed with the plugin bundle
# (it is a contributor-facing convention, not a research-kit skill).
SYNC_EXCLUDED = {"pull-request-gate"}


def test_kit_count_matches_documentation():
    kits = sorted(p.name for p in TOOLS_DIR.iterdir() if p.is_dir() and p.name.endswith("-kit"))
    assert len(kits) == EXPECTED_KITS, f"expected {EXPECTED_KITS} kits, found {kits}"


def test_actions_count_matches_documentation():
    assert len(ACTIONS) == EXPECTED_ACTIONS, (
        f"expected {EXPECTED_ACTIONS} console actions, found {len(ACTIONS)}"
    )


def test_mcp_tool_count_matches_documentation():
    registered = {t.name for t in mcp._tool_manager.list_tools()}
    assert len(registered) == EXPECTED_MCP_TOOLS, (
        f"expected {EXPECTED_MCP_TOOLS} registered MCP tools, found {len(registered)}"
    )


def test_skills_mirror_is_complete_and_current():
    canonical = {p.name for p in SKILLS_CANONICAL.iterdir() if p.is_dir()}
    mirrored = {p.name for p in SKILLS_MIRROR.iterdir() if p.is_dir()}

    expected_mirror = canonical - SYNC_EXCLUDED
    assert mirrored == expected_mirror, (
        f"skill bundle out of sync: missing={sorted(expected_mirror - mirrored)} "
        f"unexpected={sorted(mirrored - expected_mirror)}"
    )
    assert len(mirrored) == EXPECTED_MIRRORED_SKILLS, (
        f"expected {EXPECTED_MIRRORED_SKILLS} mirrored skills, found {len(mirrored)}"
    )