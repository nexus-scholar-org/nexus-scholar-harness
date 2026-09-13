"""Action → Command mapping table (single source of truth, SPECS.md §5).

This table drives three consumers; keep it in sync across all of them:
  1. the UI "Agent Exchange" panel rendering the `uv run` / MCP tool for
     every action,
  2. the job runner's command construction (runtimes/job_runner.py),
  3. the CI drift test (tests/... assert the CLI parses `--help` and the
     mcp_tool, if any, is exported by the scholar-agent-kit MCP server).

Convention: every command runs through `uv run <cli>` against the shared
`.venv` (see AGENTS.md). Placeholder tokens use `{ws}` for the workspace path,
`{q}` for a free-text query, and `{pipeline}` for a pipeline store path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_WORKSPACE = "."


@dataclass(frozen=True)
class Action:
    """A single console action plus its CLI/MCP parity surface."""

    action_id: str
    label: str
    # Command template with {ws} / {q} placeholders. The job runner expands
    # these before executing. Always starts with "uv run".
    command_template: str
    mcp_tool: str | None
    mutates: bool


ACTIONS: list[Action] = [
    Action("status", "Show workspace status", "uv run scholar-harness status -w {ws}", None, False),
    Action("sync", "Resync project state", "uv run scholar-harness sync -w {ws}", None, True),
    Action(
        "discovery",
        "Federated discovery",
        'uv run scholar-search search --query "{q}"',
        "nexus_discover",
        True,
    ),
    Action(
        "dedup",
        "Deduplicate candidates",
        "uv run scholar-search dedup --input {ws}/literature/candidates.json "
        "--output {ws}/literature/corpus.json",
        "nexus_dedup",
        True,
    ),
    Action(
        "screen_prepare",
        "Prepare screening batch",
        "uv run python src/scholar_harness/agent_screen.py prepare {ws}",
        "nexus_screen",
        True,
    ),
    Action(
        "screen_collect",
        "Assemble screening decisions",
        "uv run python src/scholar_harness/agent_screen.py collect {ws}",
        "nexus_screen",
        True,
    ),
    Action(
        "download",
        "Harvest OA PDFs",
        "uv run scholar-pdf download --input {ws}/literature/included.json --output {ws}/pdfs/",
        "nexus_extract_pdf",
        True,
    ),
    Action(
        "extract",
        "Extract fulltext",
        "uv run scholar-pdf extract {ws}/pdfs/ --output {ws}/extracted/",
        "nexus_extract_pdf",
        True,
    ),
    Action(
        "rag_index",
        "Index into vector store",
        "uv run scholar-rag index {ws}/extracted/ --workspace-id {ws}",
        "nexus_rag_index",
        True,
    ),
    Action(
        "trust_context",
        "Build trust consensus",
        "uv run scholar-verify trust-context --workspace {ws}",
        None,
        True,
    ),
    Action(
        "synthesize",
        "Grounded synthesis",
        'uv run scholar-rag synthesize "{q}" --rq-id RQ1 --output-claims {ws}/synthesis/claims.json',
        "nexus_rag_synthesize",
        True,
    ),
    Action(
        "graph",
        "Build citation graph",
        "uv run scholar-graph build --input {ws}/literature/included.json "
        "--output {ws}/literature/knowledge_graph.html",
        "nexus_graph_build",
        True,
    ),
    Action("export", "Export artifact set", "uv run scholar-harness export latex -w {ws}", None, True),
    Action(
        "pipeline",
        "Run pipeline DAG",
        "uv run scholar-harness run --pipeline {pipeline} -w {ws}",
        None,
        True,
    ),
]

_ACTIONS_BY_ID: dict[str, Action] = {a.action_id: a for a in ACTIONS}


def get_action(action_id: str) -> Action:
    """Return the action or raise KeyError with a helpful message."""
    try:
        return _ACTIONS_BY_ID[action_id]
    except KeyError:
        known = ", ".join(sorted(_ACTIONS_BY_ID))
        raise KeyError(f"Unknown action '{action_id}'. Known actions: {known}") from None


def render_command(action: Action, workspace: str = DEFAULT_WORKSPACE, query: str | None = None,
                   pipeline: str | None = None) -> list[str]:
    """Expand an action's command template into an argv list.

    `{ws}` is substituted with workspace; `{q}` with query; `{pipeline}` with
    the pipeline store path. Tokens are optional; unresolved `{q}` / `{pipeline}`
    yield a literal "..." placeholder that is still a `--help`-safe probe.
    """
    if not action.command_template.startswith("uv run "):
        raise ValueError(f"Action '{action.action_id}' command must start with 'uv run '")

    values: dict[str, Any] = {
        "ws": workspace,
        "q": query if query is not None else "...",
        "pipeline": pipeline if pipeline is not None else "...",
    }
    text = action.command_template
    for token, value in values.items():
        text = text.replace("{" + token + "}", str(value))

    # shlex is not used: command templates are simple whitespace-separated,
    # double-quoted argv - split while respecting double quotes.
    return _split_command(text)


def _split_command(text: str) -> list[str]:
    """Split a command string into argv, honoring double-quoted segments."""
    parts: list[str] = []
    buf: list[str] = []
    in_quotes = False
    for ch in text:
        if ch == '"':
            in_quotes = not in_quotes
            continue
        if ch.isspace() and not in_quotes:
            if buf:
                parts.append("".join(buf))
                buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


def actions_payload(workspace: str = DEFAULT_WORKSPACE) -> dict[str, Any]:
    """Serializable summary for the `/api/v1/agents/actions` endpoint."""
    return {
        "rows": [
            {
                "action_id": a.action_id,
                "label": a.label,
                "command": " ".join(render_command(a, workspace=workspace)),
                "mcp_tool": a.mcp_tool,
                "mutates": a.mutates,
            }
            for a in ACTIONS
        ]
    }
