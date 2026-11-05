# AGENTS.md

OpenCode / agent guidance for the Nexus Scholar Harness repo. Compact: only non-obvious facts that prevent mistakes.

## What this repo is
A harness for systematic literature reviews, shipped as **one package** (`nexus-scholar`). `src/scholar_harness/` is the orchestrator; the domain logic lives in seven packages beside it under `src/` (`scholar_search`, `scholar_pdf`, `scholar_rag`, `scholar_graph`, `scholar_protocol`, `scholar_agent`, `scholar_verify`) — formerly separate `scholar-*-kit` repositories, merged 2026-11-03. Their tests live in `tests/kits/<kit>/`. All CLIs are invoked via `uv run <cli>`.

- Post-screening verification (retraction status, open-science DAS/CAS, COI audit, risk-of-bias) is provided by `scholar-verify-kit` (`uv run scholar-verify ...`); outputs land under `<ws>/phase4/*.json|.md` and mirror the Phase-4 streams.

## Setup / environment (the big gotcha)
- `uv sync --extra dev` installs everything needed for development: the harness, all seven kits (editable, from `src/`), every CLI (`scholar-harness`, `nexus-scholar`, `scholar-search`, `scholar-pdf`, `scholar-rag`, …) and the test tools. Heavy backends are opt-in extras: `--extra pdf` (PyMuPDF), `--extra rag` (chromadb, sentence-transformers, openai), `--extra extract` (Docling, lxml), `--extra all`. The full test suite needs `--extra dev --extra pdf --extra rag`.
- **One package, one version.** There are no per-kit repositories, pins or sync steps: change kit code in `src/scholar_<kit>/` like any other code, in one PR. The old kit repos (`nexus-scholar-org/scholar-<name>-kit`) are archived history. `.agents/plugins/nexus-scholar/plugins.json` is only the agent-plugin manifest (kit names and console scripts).
- **Distribution:** `uv build --wheel` builds the `nexus-scholar` wheel from the root `pyproject.toml` (all eight packages plus the bundled skills and the app). Both entrypoints (`nexus-scholar`, `scholar-agent`) must answer `--help` on the base install without heavy backends; CI smoke is a hard gate. `nexus-scholar init <title>` scaffolds a portable workspace in any folder.
- **Active work: the production plan for Phases 0–2 (`docs/roadmap/production-plan.md`, see "Development workflow" below).** Synthesis, matrix, graph and RoB-trust are parked. Phase 7 (distribution/portability) is shipped; the operational commands are in `docs/nexus_scholar_user_guide.md`. The inception dev-loop spec (`specs/exploratory-grounding-agent/`) is complete/historical; its agent tasks are all `[x]`.
- Run everything through the project venv with `uv run ...`. Never rely on a system Python.

### Contract v1 baseline (hard gate)

- **Developer entrypoint:** before contract-related implementation or review, read `docs/architecture/DEVELOPER_COMPASS.md` (the hard invariants, minimum screening provenance, required validation and prohibited shortcuts) and the current priorities in `docs/assessment/README.md`. The frozen baseline and typed models remain normative for contract semantics.
- PR #37 merged the frozen WP-00 **reference implementation**, not WP-01 runtime adoption. Protocol/search producers, harness consumers, legacy workspaces, and screening remain unmigrated until their packet gates pass.
- Before WP-01 or downstream remediation, read `docs/architecture/contract_v1_baseline.md` and run `uv run python scripts/generate_contract_baseline.py --check`. Failure is `BLOCKED_BASELINE_DRIFT`; never regenerate merely to bless unexplained changes.
- Packet C is the `CONSUMER_GATED_REFERENCE` in `docs/architecture/wp01_packet_c_reference.md`. Packets A (protocol) and B (search) are ready. Packet D (screening migration) and Packet E (PDF/RAG stubs) are blocked on A+B.
- Contract changes require an architecture/version decision, regenerated schemas and golden fixtures, a negative regression test, and independent review. Adapter inconvenience never authorizes weakening the contract.

- Test gates are tiered by `docs/architecture/test_gate_policy.md`; every task declares a `FAST`, `STANDARD`, or `RELEASE` delivery lane before work. The machine-readable E3 mapping is `docs/architecture/test_gate_manifest.json`. Use `uv run python scripts/select_test_gate.py --task T-<n> --stage inner|checkpoint|pr|closure` to select commands. Run targeted tests during edits, the owning repo's full suite once for a final executable `STANDARD` PR candidate, and the full harness/cross-platform gates only for `RELEASE` closure. Documentation-only repairs may reuse recorded executable evidence when the policy's SHA/path conditions hold. Tests import every package from `src/` via `[tool.pytest.ini_options] pythonpath`; one `uv run pytest` runs the harness and kit suites together.
- Lint: `uv run ruff check scripts/` (CI scopes ruff to `scripts/` only). Note: `scripts/` currently passes clean; if you run ruff with a broader scope (`src/`) you'll see pre-existing findings in `src/scholar_harness/cli.py` (B008/BLE001/S110) and `src/scholar_agent/` (BLB001/RUF013/…) that are out of CI scope.
- This repo's own CLI: `uv run scholar-harness` with `status|sync|run|export|inception` subcommands (defined in `src/scholar_harness/cli.py`, Phase-0 wizard in `src/scholar_harness/inception/`).
- Multi-step research is agent-driven and file-based, so commands often hand off:
  - `python src/scholar_harness/agent_screen.py prepare|<status>|collect <workspace>` — the PRISMA screening step is an **agent-in-the-loop file handoff**, not an external API. The pipeline (orchestrator) stops after writing `literature/screening/batch_NNN.json`; an agent reads each batch and writes `batch_NNN_decisions.json`, then `collect` assembles `included.json`/`excluded.json`/`prisma_screening_report.md`.

## Where research output goes
- All project work lives under `workspaces/<project-slug>/` — never scaffold or dump results into the repo root or `src/` (enforced by the `workspace-manager` skill). Canonical layout: `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md`, `INDEX.md`, `project.json`, `audit/journal.jsonl`, `literature/`, `pdfs/`, `extracted/`, `synthesis/`.
- **Audit ledger**: every significant step must be logged to the append-only `audit/journal.jsonl` (use `uv run python .agents/skills/workspace-manager/scripts/log_event.py <slug> ...` or `batch_log.py`) and reflect in `project.json`/`INDEX.md`. This is a hard convention, not optional.
- Workspaces were emptied on 2026-09-11; the directory is scaffolded by `scholar-harness inception`. Prior workspace content lives in git history — restore from snapshot `72090e5` (see `docs/internal/COMMIT_SNAPSHOTS.md`).
- Heavy/generated artifacts are gitignored: `workspaces/**/pdfs/`, `rag/chroma_db/`, `.cache/`, `lib/` (vendored JS: vis/tom-select — do not edit). `workspaces/` text/metadata files **are** tracked.
- Grounded-recon state (sessions, pools) lives under the **canonical cache root**: `NEXUS_RECON_ROOT` override, else `<repo>/.cache/inception_recon` — CWD-independent so the CLI wizard and the MCP server (`uv run scholar-agent`) share one cache. See `specs/exploratory-grounding-agent/13_evaluation.md` §3.6.

## Kit domain skills
Each domain has an SKILL.md under `.agents/skills/<kit>/SKILL.md` (scholar-search-kit, scholar-pdf-kit, scholar-rag-kit, scholar-graph-kit, scholar-protocol-kit, scholar-agent-kit, scholar-verify-kit, methodology-copilot, workspace-manager, inception-agent). Load the relevant skill before working in that domain — they document the exact CLIs and data formats (e.g. YAML-frontmatter Markdown for extracted fulltext, the audit event schema). The verified API↔CLI↔MCP map, known-broken tooling, and cross-kit contracts live in `docs/kits_surface_matrix.md` (read it before driving kit CLIs/MCP tools). The MCP server entrypoint for the agent kit is `.agents/plugins/nexus-scholar/mcp_config.json`. `inception-agent` runs the Grounded Exploratory Inception Agent interactively in chat, reusing the MCP `recon_*` tools and `.agents/skills/inception-agent/scripts/grounded_directions.py` (imports the real wizard functions for direction parity).
- Scope repository searches to `src/<package>` or `tests/`, never recursively from the repo root (`.venv/`, `apps/research-ui/node_modules/` flood results).

## Development workflow (Claude Code)

Current mission: [`docs/roadmap/production-plan.md`](docs/roadmap/production-plan.md) — Phases 0–2 to production, milestones M0–M5, screening first. Decisions are in `docs/decisions.md`. The quality gate is the golden UAV workspace run, not an autonomous agent loop.

- **Slash commands** (`.claude/skills/`): `/milestone <M>` starts or resumes a milestone (branch from `main`, lane, `docs/roadmap/milestones/<M>.md` with DoD and evidence); `/gate [inner|checkpoint|pr]` runs only the tests selected for what changed; `/ship <M>` runs the PR gate once, the independent review, then fork + PR.
- **Subagents** (`.claude/agents/`): `phase-auditor` (read-only; re-verifies a finding and names its reproducing test), `test-gatekeeper` (runs a gate, returns evidence), `milestone-reviewer` (independent APPROVE/CHANGES/BLOCKED against the milestone DoD), `ux-spec-writer` (writes `docs/ux/<phase>/final/` specs only).
- The researcher approves each milestone start, every contract decision, and every push/PR. Design decisions stay in the main session.
- **Testing:** `uv run python scripts/select_test_gate.py --changed main --stage <stage>` selects by source area (`areas` in `docs/architecture/test_gate_manifest.json`). `inner` skips `@pytest.mark.slow`; `pr` runs the full suite once in parallel (`-n auto`). Never run the full suite after every small edit.
- **Git:** `main` → `dev/<m>/<slug>` per milestone, one PR per milestone through the fork.
- The OpenCode dev roles (`.opencode/agent/{orchestrator,coder,tester,reviewer}.md`, generated from `roles/`) are legacy and baseline-locked: do not edit them or use them as the gate. The research roles in `roles/` (screener, adjudicator, extractors, critics) are product behaviour, not dev tooling.

## Style / workflow notes
- Do not re-derive kit internals in harness code; call the kit CLIs / import their APIs (e.g. `scholar_search.dedup.Deduplicator`, `scholar_rag.indexer.ScholarIndexer`) as `orchestrator.py` does.
- CI (`.github/workflows/ci.yml`) runs on main/develop across ubuntu/windows/macos × Python 3.11/3.12: lint `scripts/`, plugin-installer help, manifest schema validation, and (best-effort) plugin install.
- **Contribution gate (hard rule):** improvements ship through the fork + a PR, never by pushing feature branches to `origin`. Load and follow `.agents/skills/pull-request-gate/SKILL.md` before any `git push`/PR/merge; a pre-push hook (`scripts/hooks/pre-push`, enabled via `git config core.hooksPath scripts/hooks`) blocks direct `origin` pushes.
