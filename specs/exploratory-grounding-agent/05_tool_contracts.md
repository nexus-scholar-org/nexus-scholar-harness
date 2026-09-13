# 05 — Harness Subsystems & Tool Contracts (verified)

> Every API named below was **confirmed against the installed kit source** — no invented methods. The harness must call kit CLIs / import kit APIs; it never re-derives kit internals.

## 1. Role assignment

| Subsystem | Kit / Component | Real API (verified) | Recon use |
| :--- | :--- | :--- | :--- |
| Search + dedup | `scholar-search-kit` | `SearchEngine(providers=[...])` → `await engine.search_all(q, dedup=True)` (`engine.py`); `Deduplicator().deduplicate(docs)` → `list[DocumentCluster]` (`dedup.py:28`); provider classes in `providers.py` | Step 2 probe queries |
| Open-Access fetch | `scholar-pdf-kit` | `AsyncPDFDownloader.download_batch(dois, ...)` | Step 2 full-text pull (2-3 OA) |
| Full-text extraction | `scholar-pdf-kit` | `PyMuPDFEngine.extract_markdown(pdf_path)` → markdown w/ YAML frontmatter (`extract.py:20`) | Distiller input |
| Candidate screening (micro) | `scholar-search-kit` | `evaluate_heuristic_screening(doc, protocol_data)` → `ScreeningDecision` (`screening.py:208`) | Withheld in recon (no frozen protocol yet); reserved for Phase-1 validation |
| Query construction | `scholar-search-kit` | `Query(text=..., max_results=..., year_min=..., year_max=...)` (order/limits live in `Query` model). **M0.6:** `Query.semantic: bool = False` → `OpenAlexProvider` selects `search.semantic` vs `search` | Steps 2-5 |
| Rate-limit / retry / cache | `scholar-search-kit` | `AcademicHttpClient` (429/503 retry, per-provider `RateLimiter`, timeout, caching) (`http_client.py:50-93`) | Inherited transparently via `SearchEngine` |
| Protocol compile | `scholar-protocol-kit` | `compile_protocol(intent_dict)` → canonical `ResearchProtocol` (`compiler.py:126`); `IntentPacket` (`intent.py:126`); `validate_protocol(...)` → `ValidationReport.is_valid` (`validate.py:284`) | Step 5 emission |
| Criteria render | `scholar-protocol-kit` | `render_screening_criteria(protocol)` (`render.py:14`) | `SCREENING_CRITERIA.md` |
| Workspace + audit | `workspace-manager` | `init_project(...)`, `log_event.py` → append-only `audit/journal.jsonl` | Step 5 genesis (includes `recon_context`) |

## 2. New harness code (the only new code)

| Module | Responsibility | Key external dependency (real kit API) | Scope guard |
| :--- | :--- | :--- | :--- |
| `src/scholar_harness/recon/engine.py` | Fire probes, dedup, cap (10-25), persist to `.cache/inception_recon/` | `scholar_search.engine.SearchEngine`, `scholar_search.dedup.Deduplicator` | Never writes `workspaces/`, never emits protocol |
| `src/scholar_harness/recon/distiller.py` | Micro-taxonomy, metrics/datasets terms, sub-school clustering, anchor-evidence emission. **M0.6:** deterministic `topics` layer (`label/n/score/anchor_dois`) aggregated from OpenAlex `Document.topics` (Topics + Concepts fallback) — classifier-grounded, anchored by construction | consumes `pools/<sha>_pool.json` (plain JSON, no ML deps); `Document.topics` from OpenAlex normalizer | Pure-Python term-frequency baseline first; LLM augmentation optional & gated |

> Mirror the pattern in `orchestrator.py:15-19` (import kit APIs, don't re-derive).

## 3. Verified license to invoke, by entrypoint

| Entrypoint | Command (real) | Use |
| :--- | :--- | :--- |
| Harness CLI | `uv run scholar-harness inception [--root|--no-scaffold]` | Existing wizard (flags only `--root/--no-scaffold` per `cli.py:84-94`) |
| MCP agent tools | `uv run --directory tools/scholar-agent-kit scholar-agent` | 18 `nexus_*` tools (see `09_mcp_integration.md`) — all confirmed backed by real kits |
| Kit CLIs | `uv run scholar-search search "…"`, `uv run scholar-pdf fetch` etc. | Debug / regression checks only |

> **Notes**
> - The `--grounded` flag is a **proposal for milestone M0.3**; today's `inception` subcommand accepts only `--root/--no-scaffold`.
> - A `--resume` flag for cache reuse across wizard runs is a **future extension**, explicitly out of M0.x scope.
> - Micro-screening (`evaluate_heuristic_screening`) intentionally plays **no role** in recon — there is no frozen protocol yet; it remains reserved for Phase-1 screening.