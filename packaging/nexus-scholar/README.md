# nexus-scholar

Agent-native, audited systematic literature review orchestration in a single
installable wheel.  The `nexus-scholar` metapackage bundles the harness CLI,
all eight `scholar-*` research kits, and twelve skill bundles so a workspace
initialized anywhere is self-contained and portable.

## What is inside

- **`nexus-scholar` CLI** -- scaffold workspaces, wire AI agents (MCP), log
  audit events, run health checks.
- **`scholar-agent` MCP server** -- exposes discovery, screening, RAG, graph,
  verification, and synthesis tools to any Model Context Protocol client.
- **8 research kits** -- search, protocol, PDF, bibliography, RAG, graph,
  verification, and agent kits.
- **12 skill bundles** -- PRISMA, workspace-manager, inception-agent,
  methodology-copilot, and more.

## Install

**Prerequisite:** Python 3.11+ (and optionally [uv](https://docs.astral.sh/uv/) 0.12+).

### Zero-friction (`uvx`)

```sh
uvx nexus-scholar --help
```

### Persistent install (`pip` or `uv tool`)

```sh
# Via pip:
pip install nexus-scholar

# Or as an isolated CLI tool with uv:
uv tool install nexus-scholar
```

## Quick start

```sh
# Scaffold a workspace
nexus-scholar init "My Systematic Review" --dir ~/projects/my-review --scaffold-only

# Health check
nexus-scholar doctor --workspace ~/projects/my-review --exit-code

# Record an audit event
nexus-scholar log event ~/projects/my-review --action PROJECT_INITIALIZED --agent me --description "started review"

# Wire MCP into your AI client
nexus-scholar setup-mcp --workspace ~/projects/my-review --harness all
```

## Commands

| Command | Purpose |
|---------|---------|
| `nexus-scholar init` | Scaffold a portable research workspace in any folder |
| `nexus-scholar doctor` | Health-check kits, keys, skills, and layout |
| `nexus-scholar log` | Append audit events and refresh the project index |
| `nexus-scholar setup-mcp` | Generate MCP config for Claude, Cursor, VS Code, and more |

## Documentation

See the [User Guide](https://github.com/nexus-scholar-org/nexus-scholar-harness/blob/main/docs/nexus_scholar_user_guide.md)
for full instructions, configuration reference, and troubleshooting.

## License

MIT
