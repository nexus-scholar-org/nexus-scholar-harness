# nexus-scholar v1.0.0 — User Guide

`nexus-scholar` is the distributed entry point for the **Nexus Scholar
Harness**: a portable toolkit that scaffolds a systematic literature review
workspace, wires it into AI agents (MCP), audits every step, and checks its own
health. Everything runs from a single pure-Python wheel published on PyPI and
GitHub Releases — no source checkout, no per-kit installs.

- Works on **Windows, macOS, Linux** (Python 3.11+ via `uv` or `pip`).
- The wheel bundles the harness CLI **plus all eight scholar kits** and the
  twelve skill bundles, so a workspace initialized here is self-contained and
  portable.
- PyPI: <https://pypi.org/project/nexus-scholar/>
- GitHub Releases: <https://github.com/nexus-scholar-org/nexus-scholar-harness/releases>

---

## 1. Install (choose one)

**Prerequisite:** Python 3.11+ (and optionally [uv](https://docs.astral.sh/uv/) 0.12+).

### A. Zero-friction, no install — `uvx`

Run any command in an ephemeral isolated environment directly from PyPI:

```sh
uvx nexus-scholar --help
```

`uvx` caches the environment, so repeat runs are fast.

> Tip: set a shell alias to shorten it, e.g.
> `alias ns='uvx nexus-scholar'`.

### B. Persistent install — `pip` or `uv tool`

```sh
# Via standard pip:
pip install nexus-scholar

# Or as an isolated CLI tool via uv:
uv tool install nexus-scholar
```

Installs **two** executables on your PATH:
`nexus-scholar` (this guide) and `scholar-agent` (the MCP server, §7).

Verify:

```sh
nexus-scholar --help          # lists the command surface
scholar-agent --help          # lists the MCP tools exposed
```

---

## 2. Quick start

```sh
# 1. create a workspace anywhere
nexus-scholar init "My Systematic Review" --dir ~/projects/my-review --scaffold-only

# 2. health-check it (exit code is 0 when nothing FAILs)
nexus-scholar doctor --workspace ~/projects/my-review --exit-code

# 3. record the first audit event (append-only journal + INDEX refresh)
nexus-scholar log event ~/projects/my-review --action PROJECT_INITIALIZED --agent me --description "started review"

# 4. wire the MCP server into your AI client (see §4)
nexus-scholar setup-mcp --workspace ~/projects/my-review --harness all
```

You now have a fully scaffolded, auditable, agent-capable research workspace.

---

## 3. `nexus-scholar init` — scaffold a workspace

Bootstrap a portable workspace in **any** folder (does not need the repo):

```sh
nexus-scholar init "Project Title" [--dir PATH] [--scaffold-only]
```

| Option | Meaning |
| --- | --- |
| `project_title` (required) | Human-readable title; the workspace slug is derived from it |
| `--dir, -d PATH` | Target folder (default: current directory) |
| `--scaffold-only` | Skip the interactive Socratic wizard; write a placeholder protocol |

What you get:

```
<workspace>/
├── protocol.json         # compiled research protocol (placeholder w/ --scaffold-only)
├── intent.json           # research intent
├── SCREENING_CRITERIA.md # human-readable inclusion/exclusion criteria
├── INDEX.md              # regenerable project index
├── project.json          # machine-readable manifest + stats
├── audit/journal.jsonl   # append-only audit ledger (see `log`)
├── .agents/skills/       # 14 skill bundles (symlinked when possible, else copied)
├── .env.example          # API-key template (SCHOLAR_*, NEXUS_*, provider keys)
├── .mcp.json             # MCP wiring with the absolute workspace path
├── literature/           # raw + screened records land here
├── pdfs/                 # downloaded Open Access PDFs
├── extracted/            # extracted fulltext (YAML-frontmatter Markdown)
└── synthesis/            # grounded synthesis outputs
```

Notes:
- On systems where symlinks are unavailable (e.g. Windows without Developer
  Mode) the skills are **copied**; the CLI tells you how to switch to symlinks
  later.
- Re-running `init` into a folder that is already a Nexus Scholar workspace (or
  a git repo / a plain file target) is **refused** to avoid clobbering data.
- Interactive mode runs the inception wizard to shape the protocol; for
  automation or CI use `--scaffold-only`.

---

## 4. `nexus-scholar setup-mcp` — wire AI agents

Point the MCP server at a workspace and generate/merge configs for popular
harnesses:

```sh
nexus-scholar setup-mcp --workspace <workspace> [--harness all|claude|cursor|vscode|dsh|mcp] [--dry-run] [--env-file PATH]
```

| Option | Meaning |
| --- | --- |
| `--workspace, -w` | Workspace the server anchors to (default `.`) |
| `--harness, -h` | Targets: `claude`, `cursor`, `vscode`, `dsh`, `mcp`, or `all` |
| `--dry-run` | Print the exact write plan **without** touching files |
| `--env-file` | `.env` carrying `SCHOLAR_*`/`NEXUS_*`/provider keys to pass through (default `<workspace>/.env` when present) |

Behavior:
- Emits `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, and the Claude
  Desktop config with the **absolute** workspace path baked in.
- Re-runs are **idempotent and merge-only**: foreign `mcpServers` blocks are
  preserved; corrupt or missing files are rebuilt.
- The config root is independent of the current directory. Set
  `NEXUS_MCP_CONFIG_HOME` to override where config files are written (useful for
  hermetic/CI setups).
- Key values never end up in generated configs as plaintext duplicates beyond
  what you already declared in `.env`; `--dry-run` shows you exactly what will be
  written first.

---

## 5. `nexus-scholar doctor` — health checks

Advisory check of kits, keys, skills, layout, and the CLI seam. **Exit code is
0 by default** (advisory); pass `--exit-code` to turn FAILs into a non-zero
exit (ideal for CI gates):

```sh
nexus-scholar doctor [--workspace PATH] [--env-file PATH] [--json] [--exit-code]
```

| Option | Meaning |
| --- | --- |
| `--workspace, -w` | Workspace to layout-validate (default `.`) |
| `--env-file` | `.env` to check (default `<workspace>/.env` when present) |
| `--json` | Machine-readable report; **secret values always masked** |
| `--exit-code` | Exit non-zero if any check FAILs |

What it verifies:

| Group | Checks |
| --- | --- |
| `kits` | Each of the 8 bundled kits imports and matches its pinned revision |
| `keys` | API keys present/absent (values shown masked `***` or `Missing`); model keys warn rather than fail |
| `skills` | Skill bundles resolvable (workspace copy / repo / wheel bundle) |
| `layout` | Canonical contract files present; `project.json` stats match disk state |
| `seam` | CLI importable, both entrypoints resolvable, Python version |

Example gate in CI:

```sh
uvx nexus-scholar doctor --workspace <ws> --json --exit-code
```

A freshly scaffolded workspace reports **PASS** (or WARN for the optional
`.env`). Use `--json` output to drive dashboards or failure triage.

---

## 6. `nexus-scholar log` — audit contract

Every significant step should be recorded in the append-only
`audit/journal.jsonl`. `log` gives standalone workspaces a first-class CLI for
this (no repo-relative scripts needed).

```sh
nexus-scholar log event <workspace> --action ACTION --agent NAME --description "..."

nexus-scholar log batch <workspace> events.jsonl

nexus-scholar log sync-index <workspace>
```

### `log event`

One canonical record + `INDEX.md` refresh:

```sh
nexus-scholar log event ~/projects/my-review \
  --action DISCOVERY_SEARCH --agent scholar-search-kit \
  --description "primary search on OpenAlex" \
  --inputs raw_search.json --outputs screened.json \
  --param source=openalex --metric hits=1240
```

| Option | Meaning |
| --- | --- |
| `workspace` (required) | Directory path, or a project slug under a `workspaces/` parent |
| `--action` (required) | Action name; stored uppercased |
| `--agent` | Responsible agent/tool (default `agent`) |
| `--description` | Human-readable description |
| `--inputs` / `--outputs` | File(s) or id(s); repeatable and space-separated |
| `--param` / `--metric` | `KEY=VALUE`; repeatable |
| `--status` | `SUCCESS` (default) / `FAILED`; stored uppercased |

Each event writes one compact JSON line — e.g.

```json
{"timestamp":"2026-09-14T09:32:36Z","event_id":"EVT-20260914093236-a491","action":"DISCOVERY_SEARCH","agent_or_tool":"scholar-search-kit","description":"primary search on OpenAlex","parameters":{"source":"openalex"},"inputs":["raw_search.json"],"outputs":["screened.json"],"metrics":{"hits":1240},"status":"SUCCESS"}
```

— bumps `project.json.updated_at` (and any declared `stats` keys), and
regenerates `INDEX.md`.

### `log batch`

Append many events from a JSONL file, JSON-parse-clean even when some records
are bad:

```sh
nexus-scholar log batch <workspace> events.jsonl
```

Policy: malformed records (invalid JSON, or missing `action`/`description`) are
**skipped with an error line**; validated records still append. The command
exits `1` if any record was skipped or failed — ideal for catching corrupted
input in pipelines — but the journal never contains a half-written line.
Each line is an event object:

```json
{"action":"FULLTEXT_EXTRACT","description":"batch extraction","agent_or_tool":"scholar-pdf-kit","outputs":["extracted/","pdfs/"],"metrics":{"pdfs":18}}
{"action":"SCREENING_DECISION","description":"two screeners done","agent_or_tool":"agent","status":"SUCCESS"}
```

### `log sync-index`

Regenerate `INDEX.md` from workspace state only (no journal append):

```sh
nexus-scholar log sync-index <workspace>
```

---

## 7. `scholar-agent` — the MCP server

The same wheel installs the **Model Context Protocol** server, which exposes
the full kit surface to AI agents (Claude Desktop, Cursor, VS Code, etc.):

```sh
scholar-agent [--workspace <root>] [--transport stdio|sse|streamable-http]
```

- `--workspace, -w` anchors every relative path and cache to the given root
  (default `NEXUS_MCP_WORKSPACE` or the current repo root). CWD-independent.
- `--transport` selects the protocol; `stdio` is the default for desktop
  clients.
- Execute commands like `--help` to list the 15 tools (`nexus_discover`,
  `nexus_screen`, `nexus_rag_query`, `nexus_verify_claims`, …).

Pair it with §4: `setup-mcp --harness claude` writes the client config that
starts this server on your workspace.

---

## 8. Configuration & environment

| Variable | Purpose |
| --- | --- |
| `SCHOLAR_MAILTO` | Contact email used by OpenAlex/Crossref requests (helps rate limits) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | Provider keys for synthesis/verification steps |
| `NEXUS_RECON_ROOT` | Where discovery-recon cache pools live (default repo `.cache/inception_recon`); makes caching CWD-independent |
| `NEXUS_MCP_CONFIG_HOME` | Where `setup-mcp` writes configs (hermetic setups) |
| `NEXUS_SKILLS_SRC` | Override the skill-bundle source root (`init` picks it first) |

Copy `.env.example` (created by `init`) to `.env` and fill in keys; `doctor` and
`setup-mcp` read `<workspace>/.env` by default.

---

## 9. The rest of the CLI

The wheel also carries the full orchestrator surface (reuse the workspace you
scaffolded):

| Command | Purpose |
| --- | --- |
| `nexus-scholar status` | Pipeline status + metrics for a workspace |
| `nexus-scholar sync` | Atomically rebuild `project.json` stats + `INDEX.md` from disk |
| `nexus-scholar run` | Execute a research pipeline (classic `--protocol` or a `--pipeline` DAG) |
| `nexus-scholar export` | Export findings/bibliographies to external tools |
| `nexus-scholar serve` | Run the FastAPI console server (uvicorn) for a workspace |
| `nexus-scholar inception` | Interactive Phase-0 Socratic methodology interview → compiled protocol |

Run any with `--help` for full options.

---

## 10. Troubleshooting

| Symptom | Likely fix |
| --- | --- |
| `doctor` exits non-zero with a `kits` FAIL | Rebuild/redownload the wheel — kit revisions are pinned and bundled; a source checkout mismatch is impossible by construction |
| `log batch` exits 1 but the journal looks fine | One or more records were skipped (invalid JSON or missing `action`/`description`); the error lines show which |
| `doctor` reports `keys` as `Missing` | No `.env` present; create one from `.env.example` (optional — `doctor` WARNs/SKIPs, not FAILs) |
| `init` refuses a folder | It already looks like a workspace (or is a git repo / a file target). Point `--dir` at a fresh folder |
| Skills were `COPIED` and you want symlinks | Enable Developer Mode (Windows) / re-run `init` into a fresh folder per the CLI hint |
| `doctor` overall is `WARN` but `--exit-code` returns 0 | WARNs are advisory by design; only a `FAIL` trips `--exit-code` |

## 11. Versioning

- Releases are tagged on the harness repo (`v*`); each tag publishes a wheel to
  PyPI and GitHub Releases with auto-generated notes.
- Upgrade with `pip install -U nexus-scholar` or `uv tool upgrade nexus-scholar`
  (or force reinstall via `uv tool install --force nexus-scholar`).
