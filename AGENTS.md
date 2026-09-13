# AGENTS.md

OpenCode / agent guidance for the Nexus Scholar Harness repo. Compact: only non-obvious facts that prevent mistakes.

## What this repo is
A thin **orchestrator** ("harness") for systematic literature reviews. The actual logic lives in eight external `scholar-*-kit` packages, checked out under `tools/<kit>/` (tracked in git) and installed **editable** into the shared `.venv/`. All kit CLIs are invoked via `uv run <cli>`.

- Post-screening verification (retraction status, open-science DAS/CAS, COI audit, risk-of-bias) is provided by `scholar-verify-kit` (`uv run scholar-verify ...`); outputs land under `<ws>/phase4/*.json|.md` and mirror the Phase-4 streams.

## Setup / environment (the big gotcha)
- `uv sync` installs only the thin harness deps (typer, rich, dev extras). It does **NOT** install the kits, so `uv run scholar-search` etc. won't exist after a bare sync.
- Kits are installed into the shared `.venv/` with `python scripts/install_plugins.py` (uses `uv pip install`, **not** `uv sync` — the kits' `[tool.uv.sources]` relative paths only work inside a monorepo). It auto-detects local checkouts in `tools/` for editable installs; falls back to the Git repos/branches declared in `.agents/plugins/nexus-scholar/plugins.json` (source of truth for kit versions).
- Run everything through the project venv with `uv run ...`. Never rely on a system Python.

- All tests: `uv run pytest` (currently **25 passed, 0 failed** — 100% test pass rate). Tests import the harness from `src/` and kits from `tools/*/src` via `[tool.pytest.ini_options] pythonpath`.
- Lint: `uv run ruff check scripts/` (CI scopes ruff to `scripts/` only). Note: `scripts/` currently passes clean; if you run ruff with a broader scope (`src/`, `tools/`) you'll see pre-existing findings in `src/scholar_harness/cli.py` (B008/BLE001/S110) and `tools/scholar-agent-kit` (BLB001/RUF013/…) that are out of CI scope and not ours to fix.
- This repo's own CLI: `uv run scholar-harness` with `status|sync|run|export|inception` subcommands (defined in `src/scholar_harness/cli.py`, Phase-0 wizard in `src/scholar_harness/inception.py`).
- Multi-step research is agent-driven and file-based, so commands often hand off:
  - `python src/scholar_harness/agent_screen.py prepare|<status>|collect <workspace>` — the PRISMA screening step is an **agent-in-the-loop file handoff**, not an external API. The pipeline (orchestrator) stops after writing `literature/screening/batch_NNN.json`; an agent reads each batch and writes `batch_NNN_decisions.json`, then `collect` assembles `included.json`/`excluded.json`/`prisma_screening_report.md`.

## Where research output goes
- All project work lives under `workspaces/<project-slug>/` — never scaffold or dump results into the repo root or `tools/` (enforced by the `workspace-manager` skill). Canonical layout: `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md`, `INDEX.md`, `project.json`, `audit/journal.jsonl`, `literature/`, `pdfs/`, `extracted/`, `synthesis/`.
- **Audit ledger**: every significant step must be logged to the append-only `audit/journal.jsonl` (use `uv run python .agents/skills/workspace-manager/scripts/log_event.py <slug> ...` or `batch_log.py`) and reflect in `project.json`/`INDEX.md`. This is a hard convention, not optional.
- Workspaces were emptied on 2026-09-11; the directory is scaffolded by `scholar-harness inception`. Prior workspace content lives in git history — restore from snapshot `72090e5` (see `docs/COMMIT_SNAPSHOTS.md`).
- Heavy/generated artifacts are gitignored: `workspaces/**/pdfs/`, `rag/chroma_db/`, `lib/` (vendored JS: vis/tom-select — do not edit). `workspaces/` text/metadata files **are** tracked. `tools/` **is** tracked (contrary to the stale `scripts/pre_commit_check.py`, which is outdated).

## Kit domain skills
Each domain has an SKILL.md under `.agents/skills/<kit>/SKILL.md` (scholar-search-kit, scholar-pdf-kit, scholar-bib-kit, scholar-rag-kit, scholar-graph-kit, scholar-protocol-kit, scholar-agent-kit, scholar-verify-kit, methodology-copilot, workspace-manager, inception-agent). Load the relevant skill before working in that domain — they document the exact CLIs and data formats (e.g. YAML-frontmatter Markdown for extracted fulltext, the audit event schema). The MCP server entrypoint for the agent kit is `.agents/plugins/nexus-scholar/mcp_config.json`. `inception-agent` runs the Grounded Exploratory Inception Agent interactively in chat, reusing the MCP `recon_*` tools and `.agents/skills/inception-agent/scripts/grounded_directions.py` (imports the real wizard functions for direction parity).

## Style / workflow notes
- Do not re-derive kit internals in harness code; call the kit CLIs / import their APIs (e.g. `scholar_search.dedup.Deduplicator`, `scholar_rag.indexer.ScholarIndexer`) as `orchestrator.py` does.
- CI (`.github/workflows/ci.yml`) runs on main/develop across ubuntu/windows/macos × Python 3.11/3.12: lint `scripts/`, plugin-installer help, manifest schema validation, and (best-effort) plugin install.
- **Contribution gate (hard rule):** improvements ship through the fork + a PR, never by pushing feature branches to `origin`. Load and follow `.agents/skills/pull-request-gate/SKILL.md` before any `git push`/PR/merge; a pre-push hook (`scripts/hooks/pre-push`, enabled via `git config core.hooksPath scripts/hooks`) blocks direct `origin` pushes.
