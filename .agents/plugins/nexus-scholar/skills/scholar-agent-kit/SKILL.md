---
name: scholar-agent-kit
description: Instructions for using the scholar-agent-kit Model Context Protocol (MCP) server, exposing Nexus Scholar discovery, BibTeX curation, PDF extraction, vector indexing, protocol, screening, graph, grounded-synthesis, and recon tools to AI agents.
---

# `scholar-agent-kit` Skill Instructions

You are the AI agent interoperability and MCP specialist of the Nexus Scholar Suite. `scholar-agent-kit` exposes the full suite of research tools to Claude Code, Antigravity, and MCP-compatible AI agent clients over standard Model Context Protocol (MCP).

## Exposed MCP Tools (18 total)

**Protocol (3):**
1. **`nexus_protocol_compile`** — path or JSON-string intent → `{status, protocol_id, fingerprint, protocol}`; does **not** persist (write protocol.json yourself).
2. **`nexus_protocol_validate`** — file path = full structural + cross-field validation; inline JSON = structural only.
3. **`nexus_protocol_render_criteria`** — render `SCREENING_CRITERIA.md` (returns raw markdown).

**Discovery / screening (4):**
4. **`nexus_discover`** — federated discovery (OpenAlex/Semantic Scholar/Crossref/arXiv — no PubMed/bioRxiv), `dedup=True` forced, writes `.cache/mcp/discover_<slug>_<ts>.json`.
5. **`nexus_dedup`** — PID + title dedup of a JSON collection into clusters.
6. **`nexus_screen`** — heuristic PRISMA screening → included/excluded/md (`conflicts.json`/`prisma_report.json` not written).
7. **`nexus_screen_reconcile`** — majority-vote reconciliation + Fleiss' κ over `batch_NNN_decisions*.json`.

**Fulltext / bibliography (2):**
8. **`nexus_extract_pdf`** — PyMuPDF extraction (engine arg is dead; **metadata dropped** — no `doi` in frontmatter).
9. **`nexus_bib_clean`** — in-place lint only (no key gen, no dedup despite the name).

**RAG (4):**
10. **`nexus_rag_index`** — AST-chunk + index a docs dir (collection/embedder locked).
11. **`nexus_rag_query`** — hybrid search + sectional slicing + `boost_doi` seed (no graph/α/β surface).
12. **`nexus_rag_synthesize`** — grounded synthesis with entailment verification (`rq_id` default `"RQ1"`).
13. **`nexus_matrix_extract`** — dynamic protocol extraction matrix (db pinned to `<workspace_dir>/chroma_db`).

**Graph (1):**
14. **`nexus_graph_build`** — ⚠ *broken today*: builds with `http_client=None` → 0-edge graph with uniform PageRank. Use `uv run scholar-graph build` instead.

**Verification (1):**
15. **`nexus_verify_claims`** — verbatim quote verification (verify-kit). ⚠ Rag `claims.json` lacks `evidence_quote`/`claim_id` → every claim `MISSING_QUOTE`; only aggregate `metrics` returned.

**Recon (3) — Grounded Exploratory Inception Agent:**
16. **`recon_probe`** — probe a topic into a FAIR recon session (OpenAlex; `semantic=True` → `search.semantic`).
17. **`recon_distill`** — distill latest session pool into anchored terms (deterministic, lexicon-mergeable).
18. **`recon_delta`** — bounded adaptive gap follow-up probes (hard cap 3).

---

## CLI & MCP Server Usage

All commands are executed via `uv run`:

### 1. Start MCP Server (stdio mode)
```bash
# IMPORTANT: launch from the kit directory so tool defaults/caches resolve predictably
uv run --directory tools/scholar-agent-kit scholar-agent
```

### 2. Display Help & Tool Registry
```bash
uv run --directory tools/scholar-agent-kit scholar-agent --help
# lists 16 tools; nexus_screen_reconcile + nexus_verify_claims are registered but hidden from --help
```

### 3. Launch a raw recon function (for testing/RECON_SEARCH_FN)
```bash
uv run python -c "from scholar_harness.recon import ReconEngine; import asyncio; print(asyncio.run(ReconEngine.probe('serious games education', limit=5)))"
```

---

## Verified surface & agent guidance

- **CWD poisoning**: the MCP server runs with CWD = `tools/scholar-agent-kit/`, so any
  default-relative `db_path`/`output_dir`/`output_path` (`.cache/mcp/…`, `./chroma_db`,
  `./extracted`, `./literature`) lands **inside the kit checkout, not your workspace**.
  Always pass **absolute workspace paths** into every tool that writes files.
- **Return conventions**: machine-readable JSON for protocol + reconcile + verify + recon
  tools; prose strings (success/`"Error: …"` prefixes) for everything else.
- **Recon integration**: sessions persist under `NEXUS_RECON_ROOT` (else
  `<repo>/.cache/inception_recon`) — CWD-independent and shared with the harness CLI
  wizard; `RECON_SEARCH_FN` is a test seam threaded into every `ReconEngine` call.
- **Known gap**: `mcp_config.json` declares no `env`, so auto-setup would benefit from
  `NEXUS_RECON_ROOT` being configured explicitly in the client.

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
from scholar_agent.server import mcp   # mcp.MCPServer, stdio transport (mcp==2.1.1)

# All 18 suite tools are registered via FastMCP's @mcp.tool() decorator:
# @mcp.tool()
# def nexus_rag_query(...): ...
```

## Agent Guidelines & Best Practices

- **Tool Selection**: Use lazy or eager MCP tool calls (`nexus_discover`, `nexus_rag_query`,
  `nexus_rag_synthesize`, `recon_probe`/`recon_distill`/`recon_delta`) when operating within
  an automated subagent loop — this is the intended MCP front-door for the suite.
- **Direct CLI Fallback**: If running in an interactive developer terminal, or when a MCP
  tool is known-broken (`nexus_graph_build`), use the direct CLI commands (`scholar-search`,
  `scholar-pdf`, `scholar-rag`, `scholar-graph`, `scholar-verify`, `scholar-protocol`).
- **Absolute paths > defaults**: every MCP tool's default output path resolves under
  `tools/scholar-agent-kit/`. Pass `<workspace>/…` paths explicitly for anything file-backed.
