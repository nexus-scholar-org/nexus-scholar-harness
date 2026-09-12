# 09 — Nexus MCP Integration

> Reference for how the Nexus MCP surface (15 `nexus_*` tools) underpins the Grounded Exploratory Inception Agent. All tool implementations were **audited against real kit source** on 2026-09-12; results below.

## 1. Server wiring

- Config (opencode): `opencode.json` → `mcp.nexus-scholar.command = ["uv", "run", "--directory", "tools/scholar-agent-kit", "scholar-agent"]`.
- Kit's own config (`.agents/plugins/nexus-scholar/mcp_config.json`) is the agent-kit documentation source; `opencode.json` is the local wiring. Either surface exposes the same tools.
- Entrypoint: `tools/scholar-agent-kit/src/scholar_agent/server.py` → `[project.scripts] scholar-agent` (FastMCP server, tool registry on `main()`).

## 2. Tool audit matrix (verified against kit APIs)

| Tool | Status | Backing implementation (source anchor) |
| :--- | :--- | :--- |
| `nexus_protocol_compile` | ✅ genuine | `compile_protocol` + `IntentPacket` + `canonical_json/fingerprint` (scholar-protocol-kit) |
| `nexus_protocol_validate` | ✅ genuine | `validate_protocol` → `ValidationReport.is_valid/.errors` |
| `nexus_protocol_render_criteria` | ✅ genuine | `render_screening_criteria` |
| `nexus_dedup` | ✅ genuine | `JSONImporter.parse` → `Deduplicator().deduplicate()` → `Exporter().json` |
| `nexus_screen` | ✅ genuine | `evaluate_heuristic_screening` + `partition_screening_results` (search-kit screening.py:208/:343) |
| `nexus_extract_pdf` | ✅ genuine | `PyMuPDFEngine.extract_markdown` |
| `nexus_rag_index` | ✅ genuine | `ScholarIndexer.index_directory` |
| `nexus_rag_query` | ✅ genuine | `ScholarRetriever.query` (params match signature) |
| `nexus_rag_synthesize` | ✅ genuine | `GroundedSynthesisEngine.synthesize` (rq_id/n_chunks/paradigm valid) |
| `nexus_matrix_extract` | ✅ genuine | `MatrixExtractor.extract_all` |
| `nexus_graph_build` | ✅ genuine | `CitationGraphBuilder.build_graph` (async) + `compute_pagerank` + `export_json` + `GraphVisualizer.generate_html` |
| `nexus_bib_clean` | ✅ genuine | scholar-bib `lint` CLI |
| `nexus_screen_reconcile` | ✅ genuine | `reconcile_multi_screener_decisions` (Fleiss' κ computed in the result) |
| `nexus_verify_claims` | ✅ genuine | `VerbatimClaimVerifier.verify_claims_ledger` |
| `nexus_discover` | ✅ **fixed** (was a stub, 2026-09-12) | now `SearchEngine.search_all` + `Exporter().json` — verified live (8 deduped papers) |

## 3. Discovery tool contract (post-fix)

- **Inputs:** `query` (str), `limit` (default 10), `start_year` (default 2020) → `Query(text, max_results=limit, year_min=start_year)`.
- **Providers:** OpenAlex, Semantic Scholar, Crossref, arXiv (OpenAlex-first).
- **Dedup:** `engine.search_all(q, dedup=True)` (PID clustering + title similarity).
- **Output:** path `{repo_root}/.cache/mcp/discover_<slug>_<ts>.json` + count + top-3 preview in the tool reply. Output is intentionally *paths*, not prose — machine-readable, agent-continuable.
- **Example live call (2026-09-12):**
  ```
  Search completed: 6 unique papers (deduped). Saved to .cache\mcp\discover_deep_learning_crop_d_….json.
    - (2024) Deep Learning Methods and UAV Technologies for Crop Disease Detection | crossref | 10.22314/2073-7599-2024-18-4-24-33
    - (2026) Deep Learning for Satellite, UAV, and Hyperspectral Crop Monitoring | crossref | 10.1201/9781003715726-4
  ```

## 4. Known-limitations & hygiene (accepted)

| Item | State | Action |
| :--- | :--- | :--- |
| `nexus_discover` output path | Fixed | Sandboxed to `.cache/mcp/` (gitignored) — no repo-root pollution |
| Dead import `calculate_fleiss_kappa` | Fixed | Removed from `server.py:33` import list |
| Server code changes | — | Require opencode restart to take effect (MCP is not hot-reloaded) |
| `nexus_discover` returns *count*, per-doc JSON is only on disk | By design | Agent reads the JSON path; keeps tool replies ≤ preview |

## 5. Recon ↔ MCP mapping (the agent driving lifecycle Step 2)

| Lifecycle step | MCP tool(s) used by the copilot |
| :--- | :--- |
| Step 2 probe | `nexus_discover` (fresh probe) — realistic fallback: + `nexus_dedup` |
| Step 2 full-text | `nexus_extract_pdf` on the OA path (2-3 first) |
| Step 3 distill | `nexus_protocol_validate`/`nexus_bib_clean` indirect; terms produced by harness `distiller.py` (M0.2) or copilot over pool JSON |
| Step 4 direction | copilot proposal (agent-held) + researcher validation |
| Step 5 emit | `nexus_protocol_compile` + `nexus_protocol_render_criteria` |
| Later (Phase-1+) | `nexus_screen`, `nexus_screen_reconcile`, `nexus_rag_*`, `nexus_graph_build`, `nexus_verify_claims` |