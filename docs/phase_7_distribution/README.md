# Phase 7: Zero-Friction Distribution — Bench-Portable Nexus Scholar

**Status**: DECIDED (blueprint reviewed 2026-09-09, implementation pending — see `docs/UPCOMING_WORK.md`)
**North star**: a researcher can type one command, open a folder in *any* harness (DeepSeek Harness, Claude Desktop, Cursor, OpenCode, VS Code, or terminal), and immediately run systematic reviews with verifiable provenance.
**Repository for this phase**: `docs/phase_7_distribution/` (this README = blueprint + review). Related: `docs/phase_6/` (trust primitives this builds on), `docs/phase_5/` (agent-agnostic direction).

---

## 1. The Problem Today vs. The Vision

| Today (Repo-Tied) | The Goal (Portable Everywhere) |
|---|---|
| Must clone `nexus-scholar-harness` monorepo | Run **one installer / uvx command** from anywhere |
| Workspaces constrained to `nexus-scholar-harness/workspaces/` | Open any empty folder: `mkdir my-review && cd my-review` |
| Monorepo relative editable paths (`tools/*`) | Pre-packaged distribution + global MCP entrypoint |
| Manual setup of 8 toolkits via custom scripts | Zero-config autodetection of skills and MCP by any harness |

---

## 2. The 3-Tier Shipping Strategy (as blueprinted)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TIER 1: Distribution                            │
│           Single umbrella package (nexus-scholar)                      │
│          Pip-installable or zero-install via `uvx nexus-scholar`       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                        TIER 2: Workspace Portable CLI                  │
│       `nexus-scholar init .` scaffolds local contracts & audit         │
│         Skills copied / symlinked to `.agents/skills/` locally         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                        TIER 3: Universal MCP Server                    │
│   `uvx --from nexus-scholar scholar-agent --workspace .`              │
│       One-line stdio config for Claude, DSH, Cursor, Windsurf          │
└────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Single umbrella package (`nexus-scholar`)
Instead of requiring users to install 8 separate sub-packages manually, bundle them under one unified entrypoint:

```toml
[project]
name = "nexus-scholar"
version = "1.0.0"
description = "Systematic literature review harness with verifiable provenance."
dependencies = [
    "scholar-protocol-kit>=0.2.0",
    "scholar-search-kit>=0.2.0",
    "scholar-pdf-kit>=0.2.0",
    "scholar-verify-kit>=0.2.0",
    "scholar-rag-kit>=0.2.0",
    "scholar-graph-kit>=0.2.0",
    "scholar-bib-kit>=0.2.0",
    "scholar-agent-kit>=0.2.0",
    "typer>=0.12.0",
    "rich>=13.0.0",
]

[project.scripts]
nexus-scholar = "scholar_harness.cli:app"
scholar-agent = "scholar_agent.server:main"
```

Zero-install user flow:
```bash
# Initialize a review workspace anywhere
uvx nexus-scholar init "UAV Precision Agriculture"
# Or launch the MCP server in any folder
uvx --from nexus-scholar scholar-agent
```

### Tier 2: Self-contained workspace portability (`nexus-scholar init .`)
Standing in any folder, `nexus-scholar init .` turns it into an autonomous Nexus research cell:

1. **Scaffolds the file contracts**:
   ```text
   protocol.json            <- Research protocol contract
   project.json             <- Stats and manifest
   audit/journal.jsonl      <- Append-only local ledger
   literature/              <- Search and screening outputs
   pdfs/                    <- Harvested fulltexts
   extracted/               <- Section-aware markdown
   synthesis/               <- Claims and consensus cartography
   .agents/
       skills/              <- Auto-populated SKILL.md files
       mcp.json             <- Ready-to-copy harness config
   ```
2. **Auto-vendors agent skills**: the standard `SKILL.md` files land in `.agents/skills/` so any AI agent (Claude Code, Cursor, OpenCode, Antigravity) reads them instantly.

### Tier 3: Universal MCP configuration (copy-paste into any harness)
Because `scholar-agent` runs over standard `stdio`, configuration is just a few JSON lines pointing at the current working directory.

#### DeepSeek Harness (DSH)
DSH Settings → MCP Servers → Add: command `uvx`, args `["--from", "nexus-scholar", "scholar-agent", "--workspace", "."]`.

#### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "nexus-scholar": { "command": "uvx", "args": ["--from", "nexus-scholar", "scholar-agent"] }
  }
}
```

#### Cursor / Windsurf / VS Code (`.cursor/mcp.json` or `.vscode/mcp.json`)
```json
{
  "mcpServers": {
    "nexus-scholar": {
      "command": "uvx",
      "args": ["--from", "nexus-scholar", "scholar-agent", "--workspace", "${workspaceFolder}"]
    }
  }
}
```

### The 1-minute user experience
```bash
mkdir ~/research/quantum-computing-review && cd ~/research/quantum-computing-review
uvx nexus-scholar init                 # Socratic wizard -> protocol.json + audit ledger
# open DSH / Cursor / Claude Desktop in this folder -> MCP already wired
# "Run nexus_search across OpenAlex and Crossref to identify candidate studies."
# All screening passes, multi-screener κ adjudications, and 100% verbatim-verified
# claims are logged to audit/journal.jsonl inside the workspace folder.
```

---

## 3. Technical Review & Gaps Identified (2026-09-09)

Review of the blueprint against the actual repo (`src/scholar_harness/`, `tools/*/`, `.agents/plugins/nexus-scholar/`, `scripts/install_plugins.py`). The direction is endorsed; these obstacles must be handled before "zero-friction" is real.

### 3.1 Critical
1. **`--workspace` does not exist.** `scholar_agent.server.main()` takes no arguments; every tool resolves paths from **process cwd** (`nexus_matrix_extract(workspace_dir=".")`, `nexus_rag_index(db_path="./chroma_db")`). Tier-3 configs would silently run against the harness's cwd (e.g. Claude Desktop starts at an uncontrolled/home directory). **Required:** add a `--workspace <root>` (rootdir) flag to `main()` and resolve all tool defaults against it.
2. **`${workspaceFolder}` only expands in Cursor/Windsurf/VS Code.** The Claude Desktop snippet must bake in an absolute path (no expansion there), and DSH-in-terminal must pass a real path, not `.`.
3. **`uvx nexus-scholar` fails today** — nothing is packaged or published. The repo root must first ship as a buildable metapackage (or GitHub-Release wheel) before any `uvx` example works.

### 3.2 Version & supply-chain discipline
4. **Single source of truth.** Kit versions live in `.agents/plugins/nexus-scholar/plugins.json`. The metapackage `pyproject.toml` dependency pins must be **generated from that file** (CI codegen), not hand-maintained — otherwise the two drift.
5. **Prefer a repo-root metapackage + GitHub Release wheel over 8 PyPI packages.** Publishing 8 kits + a metapackage multiplies release coordination and supply-chain surface for no current external consumer. Revisit PyPI publication only when consumers exist outside the monorepo. Verify PyPI name availability (`nexus-scholar`, `scholar-*-kit`) before committing to those names.

### 3.3 Workspace portability internals
6. **Skills must be symlinked/shipped, not copied.** Copying `SKILL.md` into every `.agents/skills/` freezes skill versions and every old workspace drifts from the kits. Prefer: skills shipped inside the package + `init` symlinking (same machine) or pointing the harness at the installed location. A `nexus-scholar sync-skills` upgrade path for existing workspaces.
7. **Audit tooling must travel with the workspace.** `log_event.py` / `batch_log.py` and the `project.json`/`INDEX.md` syncer currently live in repo-relative `scripts/`. A standalone workspace needs these shipped as an importable CLI (`nexus-scholar log`), or the scaffold's audit conventions are instructions without tools.
8. **Reuse `inception`, don't re-implement it.** A Socratic wizard already exists (`scholar-harness inception`, `src/scholar_harness/inception.py`). `init` should wrap it and add raw-folder scaffolding.

### 3.4 Runtime & configuration
9. **LLM/API configuration is unaddressed.** Screening and claim extraction are model-backed; search needs `mailto` (+ optional provider keys). Show a concrete `.env` story (`NEXUS_*` vars, model ids, decoding pins) via `.env.example` scaffolding in `init` and env passthrough in the Claude Desktop config (`env:` block).
10. **Heavy deps.** `scholar-rag-kit` pulls chromadb + sentence-transformers (torch) — first `uvx` run is minutes. **Lazy-import** rag/graph so `init`, `setup-mcp`, `search`, `doctor` never load torch. Keep the 1-minute claim honest.
11. **`doctor` command.** `nexus-scholar doctor` should validate: kits installed & versions match `plugins.json`, keys present, skills resolvable, workspace layout valid.

---

## 4. Implementation Checklist (deferred — see `docs/UPCOMING_WORK.md`)

- [ ] **P7.1** `--workspace` rootdir resolution in `scholar_agent.server.main()`; refactor tool defaults onto a resolved root (the portability enabler).
- [ ] **P7.2** Repo-root `nexus-scholar` tool-metapackage; `pyproject.toml` `[project]` + script entrypoints; dependency pins **generated from `.agents/plugins/nexus-scholar/plugins.json`** by CI.
- [ ] **P7.3** `nexus-scholar init <title>` — reuse `inception` wizard; scaffold canonical contract layout, `audit/journal.jsonl`, `.env.example`, `.mcp.json`, skill **symlinks**.
- [ ] **P7.4** `nexus-scholar setup-mcp` — emits `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, and prints the Claude Desktop snippet with **absolute workspace path** baked in (+ `env:` block).
- [ ] **P7.5** `nexus-scholar doctor` — validate kits/versions, keys, skills, workspace layout.
- [ ] **P7.6** Ship `log_event`/`batch_log`/INDEX-sync as an importable CLI (`nexus-scholar log`) so standalone workspaces keep the audit contract.
- [ ] **P7.7** Lazy-import rag/graph so light commands never load torch/chromadb.
- [ ] **P7.8** GitHub-Release wheel + CI verification that the blueprinted `uvx` commands run end-to-end in a temp folder.
- [ ] **P7.9** (Deferred) PyPI publication of individual kits + metapackage, only if external consumers appear.

*Deferred by: no external distribution consumer yet; Phase 6/trust layer still hardening; single-source-of-truth packaging needs a CI build step first.*