---
name: scholar-agent-kit
description: Instructions for using the scholar-agent-kit Model Context Protocol (MCP) server, exposing Nexus Scholar discovery, BibTeX curation, PDF extraction, vector indexing, protocol, screening, graph, grounded-synthesis, and recon tools to AI agents.
---

# `scholar-agent-kit` Skill Instructions

You are the AI agent interoperability and MCP specialist of the Nexus Scholar Suite. `scholar-agent-kit` exposes the full suite of research tools to Claude Code, Antigravity, and MCP-compatible AI agent clients over standard Model Context Protocol (MCP).

## Exposed MCP Tools (23 total)

**Protocol (3):**
1. **`nexus_protocol_compile`** — path or JSON-string intent → `{status, protocol_id, fingerprint, protocol}`; does **not** persist (write protocol.json yourself).
2. **`nexus_protocol_validate`** — file path or inline JSON; both run the full structural + cross-field rule set (duplicate IDs, RQ/criterion/dimension coherence).
3. **`nexus_protocol_render_criteria`** — render `SCREENING_CRITERIA.md` (returns raw markdown).

**Discovery / screening (5):**
4. **`nexus_discover`** — federated discovery (OpenAlex/Semantic Scholar/Crossref/arXiv — no PubMed/bioRxiv), `dedup=True` forced, writes `.cache/mcp/discover_<slug>_<ts>.json`.
5. **`nexus_dedup`** — PID + title dedup of a JSON collection into clusters.
6. **`nexus_screen`** — heuristic PRISMA screening → included/excluded/conflicts JSON + prisma_report.json + `prisma_screening_report.md`.
7. **`nexus_screen_llm`** — LLM-enhanced screening via Gemini with structured checklist prompts; falls back to heuristic on any LLM failure (network, auth, rate-limit). Parameters: `input_path`, `protocol_path`, `output_dir`, `api_key`, `model`, `batch_size`, `temperature`. Produces the same 5 output files as `nexus_screen`.
8. **`nexus_screen_reconcile`** — majority-vote reconciliation + Fleiss' κ over `batch_NNN_decisions*.json` (or a screener→decision map).

**Fulltext / bibliography (2):**
9. **`nexus_extract_pdf`** — extraction via `engine=pymupdf|docling|grobid` (heavy engines fall back to PyMuPDF); `title`/`doi`/`workspace_id` metadata is derived from the PDF path and passed through.
10. **`nexus_bib_clean`** — full documented pipeline: lint + `generate_keys=True` + dedup, saved to the output path (in-place by default).

**RAG (4):**
11. **`nexus_rag_index`** — AST-chunk + index a docs dir (collection/embedder locked).
12. **`nexus_rag_query`** — hybrid search + sectional slicing + `boost_doi` seed + graph boosting via `graph_source` (α=0.25, β=0.15 defaults).
13. **`nexus_rag_synthesize`** — grounded synthesis with entailment verification (`rq_id` default `"RQ1"`).
14. **`nexus_matrix_extract`** — dynamic protocol extraction matrix (db pinned to `<workspace_dir>/chroma_db`).

**Graph (2):**
15. **`nexus_graph_build`** — citation graph with a real `AcademicHttpClient(name="openalex-graph")` client; accepts `results`/`items` dict payloads; errors on no DOIs.
16. **`nexus_graph_narrative`** — Visual Synthesis Agent: reads graph JSON (PageRank + Louvain communities) and generates `synthesis/visual_synthesis.md` with hub papers, thematic communities, and network overview.

**Verification (2):**
17. **`nexus_verify_claims`** — verbatim quote verification. Digests scholar-rag `claims.json` (`{claims:[…]}` or bare list; `claim_text` as the quote), returns aggregate metrics + per-claim verdicts + failures-by-reason.
18. **`nexus_verify_phase4`** — run a scholar-verify Phase-4 stream against a workspace: `retraction` (OpenAlex/Crossref), `open-science` (DAS/CAS), `coi`, `risk-of-bias` (QUADAS-2/PROBAST), `trust-context`, or `all`; writes `<ws>/phase4/<name>.{json,md}`. `skip_retraction=True` by default.

**Methodology Critique (1):**
19. **`nexus_critique_methodology`** — Methodology Critique Agent: wraps `scholar-verify-kit` risk-of-bias (QUADAS-2/PROBAST) over extracted records + manifest; outputs `phase4/methodological_critique.md` with domain-level summary and per-study table.

**Pipeline (1):**
20. **`nexus_pipeline_run`** — run the full 10-stage `ResearchOrchestrator` pipeline (protocol → discovery → dedup → screening → verification → PDF → extraction → RAG → synthesis). Parameters: `workspace_dir`, `query`, `protocol_path`, `skip_stages` (comma-separated stage names to skip).

**Recon (3) — Grounded Exploratory Inception Agent:**
21. **`recon_probe`** — probe a topic into a FAIR recon session (OpenAlex; `semantic=True` → `search.semantic`).
22. **`recon_distill`** — distill latest session pool into anchored terms (deterministic, lexicon-mergeable).
23. **`recon_delta`** — bounded adaptive gap follow-up probes (hard cap 3).

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
# lists all 23 registered tools
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

# All 21 suite tools are registered via FastMCP's @mcp.tool() decorator:
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
