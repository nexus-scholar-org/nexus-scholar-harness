"""Data contracts for Phase F specialized agents (F1: Critique, F2: Narrative).

Defines the input/output schemas consumed and produced by
``nexus_critique_methodology`` and ``nexus_graph_narrative``.  These are
plain dataclass-style dicts (not Pydantic BaseModel) to match the existing
kit convention for MCP return payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# F1: Methodology Critique Agent
# ---------------------------------------------------------------------------


@dataclass
class CritiqueRequest:
    """Input contract for ``nexus_critique_methodology``."""

    workspace_dir: str
    protocol_path: str | None = None
    rq_id: str | None = None


@dataclass
class CritiqueResult:
    """Output contract for ``nexus_critique_methodology``.

    Attributes
    ----------
    overall_risk:
        Aggregate risk label across all assessed studies (``"H"`` / ``"?"`` / ``"L"``).
    domain_ratings:
        Per-domain summary counts, e.g.
        ``{"d1": {"H": 2, "L": 5}, "d2": {"?": 1, "L": 6}}``.
    per_study:
        List of per-study dicts with ``workspace_id``, ``title``, ``overall_risk``,
        and ``domains`` breakdown.
    summary_md:
        Rendered Markdown critique report.
    """

    overall_risk: str = "n/a"
    domain_ratings: dict[str, dict[str, int]] = field(default_factory=dict)
    per_study: list[dict[str, Any]] = field(default_factory=list)
    summary_md: str = ""


# ---------------------------------------------------------------------------
# F2: Visual Synthesis Agent
# ---------------------------------------------------------------------------


@dataclass
class NarrativeRequest:
    """Input contract for ``nexus_graph_narrative``."""

    workspace_dir: str
    graph_json_path: str
    consensus_path: str | None = None


@dataclass
class NarrativeResult:
    """Output contract for ``nexus_graph_narrative``.

    Attributes
    ----------
    hub_summary:
        Markdown section listing top hub papers.
    community_summaries:
        Per-community dicts with ``group_id``, ``node_count``, ``top_nodes``,
        and a ``label``.
    narrative_md:
        Full rendered ``visual_synthesis.md`` content.
    """

    hub_summary: str = ""
    community_summaries: list[dict[str, Any]] = field(default_factory=list)
    narrative_md: str = ""
