"""Surface count freshness.

The repo documents cardinal numbers (8 kits, 13 mirrored skills, 16 console
actions, 25 MCP tools) in ``docs/kits_surface_matrix.md`` / AGENTS.md.  These
must match runtime reality so prose never silently corrodes.  The skill check
also guards mirror completeness: the plugin bundle must contain every
canonical skill except ``pull-request-gate`` (the sync script's one exclusion).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from scholar_agent.server import mcp

from scholar_harness.console.runtimes.actions import ACTIONS

REPO_ROOT = Path(__file__).resolve().parents[2]

TOOLS_DIR = REPO_ROOT / "tools"
SKILLS_CANONICAL = REPO_ROOT / ".agents" / "skills"
SKILLS_MIRROR = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "skills"
MANIFEST = REPO_ROOT / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"

EXPECTED_KITS = 8
EXPECTED_ACTIONS = 16
EXPECTED_MCP_TOOLS = 25
EXPECTED_MIRRORED_SKILLS = 13

# Live-derived 25-tool surface via `{t.name for t in mcp._tool_manager.list_tools()}`.
# Exact set (not a subset) so an added/removed/renamed tool fails loudly with
# missing/unexpected lists instead of blessing whatever number prose carries.
EXPECTED_MCP_TOOL_NAMES = frozenset(
    {
        "nexus_bib_clean",
        "nexus_critique_methodology",
        "nexus_dedup",
        "nexus_discover",
        "nexus_extract_pdf",
        "nexus_graph_build",
        "nexus_graph_narrative",
        "nexus_matrix_extract",
        "nexus_pdf_acquire",
        "nexus_pdf_extraction",
        "nexus_pipeline_run",
        "nexus_protocol_compile",
        "nexus_protocol_render_criteria",
        "nexus_protocol_validate",
        "nexus_rag_index",
        "nexus_rag_query",
        "nexus_rag_synthesize",
        "nexus_screen",
        "nexus_screen_llm",
        "nexus_screen_reconcile",
        "nexus_verify_claims",
        "nexus_verify_phase4",
        "recon_delta",
        "recon_distill",
        "recon_probe",
    }
)

# Declared-unsupported boundary tools stay registered so the E1/E2/E3 refusals
# are observable (never missing tools). Subset of EXPECTED_MCP_TOOL_NAMES.
BOUNDARY_MCP_TOOLS = frozenset(
    {"nexus_pdf_acquire", "nexus_pdf_extraction", "nexus_rag_index"}
)

# ``pull-request-gate`` is intentionally not distributed with the plugin bundle
# (it is a contributor-facing convention, not a research-kit skill).
SYNC_EXCLUDED = {"pull-request-gate"}

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def test_kit_count_matches_documentation():
    kits = sorted(
        p.name for p in TOOLS_DIR.iterdir() if p.is_dir() and p.name.endswith("-kit")
    )
    assert len(kits) == EXPECTED_KITS, f"expected {EXPECTED_KITS} kits, found {kits}"


def test_actions_count_matches_documentation():
    assert len(ACTIONS) == EXPECTED_ACTIONS, (
        f"expected {EXPECTED_ACTIONS} console actions, found {len(ACTIONS)}"
    )


def test_mcp_tool_count_matches_documentation():
    registered = {t.name for t in mcp._tool_manager.list_tools()}
    assert len(registered) == EXPECTED_MCP_TOOLS, (
        f"expected {EXPECTED_MCP_TOOLS} registered MCP tools, found {len(registered)}: "
        f"{sorted(registered)}"
    )
    missing_boundary = sorted(BOUNDARY_MCP_TOOLS - registered)
    assert not missing_boundary, (
        f"declared-unsupported boundary tools missing from the live surface: "
        f"{missing_boundary}"
    )
    assert registered == EXPECTED_MCP_TOOL_NAMES, (
        f"MCP surface drift: missing={sorted(EXPECTED_MCP_TOOL_NAMES - registered)} "
        f"unexpected={sorted(registered - EXPECTED_MCP_TOOL_NAMES)}"
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


def test_manifest_default_revs_are_pinned_commits():
    """Manifest kit pins must be full commit SHAs, never floating branches.

    ``default_rev`` in plugins.json is the fallback install ref (used when no
    local ``tools/<kit>`` checkout exists); a 40-hex SHA makes those installs
    reproducible instead of tracking whichever ``main`` happens to be HEAD.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(manifest["plugins"]) == EXPECTED_KITS
    unpinned = [
        (p["name"], p.get("default_rev"))
        for p in manifest["plugins"]
        if not FULL_SHA_RE.match(p.get("default_rev", ""))
    ]
    assert not unpinned, (
        f"plugins.json default_rev must be full commit SHAs: {unpinned}"
    )
