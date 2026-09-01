---
name: scholar-agent-kit
description: Instructions for using the scholar-agent-kit Model Context Protocol (MCP) server, exposing Nexus Scholar discovery, BibTeX curation, PDF extraction, vector indexing, and grounded synthesis tools to AI agents.
---

# `scholar-agent-kit` Skill Instructions

You are the AI agent interoperability and MCP specialist of the Nexus Scholar Suite. `scholar-agent-kit` exposes the full suite of research tools to Claude Code, Antigravity, and MCP-compatible AI agent clients over standard Model Context Protocol (MCP).

## Exposed MCP Tools

1. **`nexus_discover`**: Executes federated literature discovery across OpenAlex and academic repositories.
2. **`nexus_bib_clean`**: Cleans, standardizes keys, and deduplicates BibTeX databases.
3. **`nexus_extract_pdf`**: Extracts layout-aware, heading-structured Markdown from PDFs using Docling/PyMuPDF.
4. **`nexus_rag_index`**: Chunks and indexes literature into ChromaDB with companion BibTeX metadata.
5. **`nexus_rag_query`**: Executes scale-safe hybrid search with sectional filtering and PageRank graph boosting.
6. **`nexus_rag_synthesize`**: Generates grounded research reviews with atomic citation tokens and cosine entailment verification.
7. **`nexus_graph_build`**: Builds citation networks and interactive PyVis HTML visualization maps.

---

## CLI & MCP Server Usage

All commands are executed via `uv run`:

### 1. Start FastMCP Server (stdio mode)
```bash
# Start MCP server listening on stdin/stdout
uv run scholar-agent
```

### 2. Display Help & Tool Registry
```bash
uv run scholar-agent --help
```

---

## MCP Client Configuration

To register `scholar-agent-kit` in your Claude Desktop, Claude Code, or Antigravity IDE configuration:

### `mcp_config.json` / Claude Desktop Config
```json
{
  "mcpServers": {
    "nexus-scholar": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "tools/scholar-agent-kit",
        "scholar-agent"
      ]
    }
  }
}
```

---

## Python Server Architecture

```python
from mcp.server.mcpserver import MCPServer
from scholar_agent.server import mcp

# The server exposes all suite tools via standard FastMCP decorators:
# @mcp.tool()
# def nexus_rag_query(...): ...
```

---

## Agent Guidelines & Best Practices

- **Tool Selection**: Use lazy or eager MCP tool calls (`nexus_discover`, `nexus_rag_query`, `nexus_rag_synthesize`) when operating within an automated subagent loop.
- **Direct CLI Fallback**: If running in an interactive developer terminal, direct CLI commands (`scholar-search`, `scholar-pdf`, `scholar-rag`, `scholar-graph`) are also fully accessible.
