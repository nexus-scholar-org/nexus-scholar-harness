# AGENTS.md

OpenCode / agent guidance for the Nexus Scholar Harness repo. Compact: only non-obvious facts that prevent mistakes.

## What this repo is
A thin **orchestrator** ("harness") for systematic literature reviews. The actual logic lives in seven external `scholar-*-kit` packages, checked out under `tools/<kit>/` (tracked in git) and installed **editable** into the shared `.venv/`. All kit CLIs are invoked via `uv run <cli>`.

## Setup / environment (the big gotcha)
- `uv sync` installs only the thin harness deps (typer, rich, dev extras). It does **NOT** install the kits, so `uv run scholar-search` etc. won't exist after a bare sync.
- Kits are installed into the shared `.venv/` with `python scripts/install_plugins.py` (uses `uv pip install`, **not** `uv sync` — the kits' `[tool.uv.sources]` relative paths only work inside a monorepo). It auto-detects local checkouts in `tools/` for editable installs; falls back to the Git repos/branches declared in `.agents/plugins/nexus-scholar/plugins.json` (source of truth for kit versions).
- Run everything through the project venv with `uv run ...`. Never rely on a system Python.

## Commands
- All tests: `uv run pytest` (currently **10 passed, 1 failed** — `test_phase2_e2e.py::test_phase2_full_pipeline_e2e` fails with `StopIteration` in matrix extraction; not a new break you introduced). Tests import the harness from `src/` and kits from `tools/*/src` via `[tool.pytest.ini_options] pythonpath`.
- Lint: `uv run ruff check scripts/` (CI scopes ruff to `scripts/` only). Note: there are ~15 pre-existing errors; don't assume a clean pass.
- This repo's own CLI: `uv run scholar-harness status|run|export --workspace <dir>` (defined in `src/scholar_harness/cli.py`).
- Multi-step research is agent-driven and file-based, so commands often hand off:
  - `python src/scholar_harness/agent_screen.py prepare|<status>|collect <workspace>` — the PRISMA screening step is an **agent-in-the-loop file handoff**, not an external API. The pipeline (orchestrator) stops after writing `literature/screening/batch_NNN.json`; an agent reads each batch and writes `batch_NNN_decisions.json`, then `collect` assembles `included.json`/`excluded.json`/`prisma_screening_report.md`.

## Where research output goes
- All project work lives under `workspaces/<project-slug>/` — never scaffold or dump results into the repo root or `tools/` (enforced by the `workspace-manager` skill). Canonical layout: `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md`, `INDEX.md`, `project.json`, `audit/journal.jsonl`, `literature/`, `pdfs/`, `extracted/`, `synthesis/`.
- **Audit ledger**: every significant step must be logged to the append-only `audit/journal.jsonl` (use `uv run python .agents/skills/workspace-manager/scripts/log_event.py <slug> ...` or `batch_log.py`) and reflect in `project.json`/`INDEX.md`. This is a hard convention, not optional.
- Current active project: `workspaces/uav-cv-precision-agriculture`.
- Heavy/generated artifacts are gitignored: `workspaces/**/pdfs/`, `rag/chroma_db/`, `lib/` (vendored JS: vis/tom-select — do not edit). `workspaces/` text/metadata files **are** tracked. `tools/` **is** tracked (contrary to the stale `scripts/pre_commit_check.py`, which is outdated).

## Kit domain skills
Each domain has an SKILL.md under `.agents/skills/<kit>/SKILL.md` (scholar-search-kit, scholar-pdf-kit, scholar-bib-kit, scholar-rag-kit, scholar-graph-kit, scholar-protocol-kit, scholar-agent-kit, methodology-copilot, workspace-manager). Load the relevant skill before working in that domain — they document the exact CLIs and data formats (e.g. YAML-frontmatter Markdown for extracted fulltext, the audit event schema). The MCP server entrypoint for the agent kit is `.agents/plugins/nexus-scholar/mcp_config.json`.

## Style / workflow notes
- Do not re-derive kit internals in harness code; call the kit CLIs / import their APIs (e.g. `scholar_search.dedup.Deduplicator`, `scholar_rag.indexer.ScholarIndexer`) as `orchestrator.py` does.
- CI (`.github/workflows/ci.yml`) runs on main/develop across ubuntu/windows/macos × Python 3.11/3.12: lint `scripts/`, plugin-installer help, manifest schema validation, and (best-effort) plugin install.
