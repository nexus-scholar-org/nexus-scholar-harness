# Nexus Scholar Harness

> **Agent-native, audited orchestration for systematic literature reviews.**
> A thin orchestrator that drives eight external research kits through a unified CLI, workspaces-as-file-contract state, and an append-only audit ledger.

[![CI](https://github.com/nexus-scholar-org/nexus-scholar-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/nexus-scholar-org/nexus-scholar-harness/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](pyproject.toml)
[![Managed with uv](https://img.shields.io/badge/managed%20with-uv-7841db?logo=astral)](https://docs.astral.sh/uv/)
[![Kits](https://img.shields.io/badge/8%20research%20kits-galaxy)](tools/)

---

## Why this repo exists

The harness is deliberately **thin**: it does not re-implement research logic. Instead it orchestrates a family of purpose-built kits — discovery, screening, PDF harvesting, extraction, RAG synthesis, citation graphs, protocol compilation, and verification — that live under `tools/` and are installed **editable** into one shared environment. Everything a researcher or an AI agent does on the pipeline is:

1. **Deterministic and idempotent** — re-runs produce identical artifacts (`protocol.json` carries a SHA-256 fingerprint).
2. **Audited** — every significant step appends an immutable event to `audit/journal.jsonl`.
3. **Agent-agnostic** — the same CLI, MCP tools (`scholar-agent-kit`), and workspace files drive opencode, Claude, Copilot, and any other coding agent.

The pipeline in one flow:

```text
Socratic Inception ─▶ Federated Discovery ─▶ Dedup & Verify ─▶ PRISMA Screening ─▶ OA Harvest ─▶ Extraction ─▶ RAG Synthesis ─▶ Trust Verification
(methodology-copilot)   (scholar-search)   (scholar-search)  (agent-in-the-loop)  (scholar-pdf)  (scholar-pdf)  (scholar-rag)   (scholar-verify)
```

---

## The research kits

| Kit | Purpose | Key CLI |
| :-- | :-- | :-- |
| `scholar-protocol-kit` | Compiles, fingerprints, and renders research protocols from `intent.json`. | `scholar-protocol compile -i intent.json -o protocol.json --fingerprint` |
| `scholar-search-kit` | Federated search (OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed, bioRxiv), snowballing, dedup, verify, screening export. | `scholar-search search / dedup / verify / snowball / chain` |
| `scholar-pdf-kit` | OA discovery, resilient downloading (institutional-proxy aware), `%PDF` integrity validation, Markdown extraction. | `scholar-pdf download / extract / ingest` |
| `scholar-bib-kit` | BibTeX parse, lint, merge, dedup, resolve missing metadata. | `scholar-bib lint / merge / resolve` |
| `scholar-rag-kit` | AST chunking, ChromaDB indexing, grounded synthesis with atomic attribution tokens. | `scholar-rag index / query / synthesize / consensus` |
| `scholar-graph-kit` | Citation/co-citation networks, PageRank, interactive PyVis HTML maps. | `scholar-graph build / pagerank` |
| `scholar-agent-kit` | MCP server exposing all kits as `nexus_*` tools to AI agents. | `scholar-agent` (MCP entrypoint) |
| `scholar-verify-kit` | Phase-4 trust streams: retraction status, open-science DAS/CAS, COI audit, risk-of-bias, trust-weighted consensus. | `scholar-verify retraction / coi / ... / trust-context --rq-id` |

---

## Quick start

### Requirements

- **Python 3.11+**
- **[`uv`](https://docs.astral.sh/uv/)** — install: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows) or `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux)
- **Git 2.30+**

```bash
git clone https://github.com/nexus-scholar-org/nexus-scholar-harness.git
cd nexus-scholar-harness

# Thin harness deps (typer, rich, dev extras)
uv sync --extra dev

# Install the eight kits into the shared .venv (editable installs when tools/ checkouts exist;
# Git-branch fallback declared in .agents/plugins/nexus-scholar/plugins.json)
uv run python scripts/install_plugins.py

# Scaffold a workspace (or restore one from git history), then check status:
uv run scholar-harness status --workspace workspaces/<your-project>
```

> **Gotcha:** `uv sync` installs only the harness. Kit CLIs become available only after `install_plugins.py` runs — the installer is the source of truth for kit versions.

### Scaffold a workspace

```bash
uv run scholar-harness inception --root .          # Socratic wizard → intent.json + fingerprinted protocol.json + SCREENING_CRITERIA.md
uv run scholar-harness status -w workspaces/<slug> # dashboard-style status table
uv run scholar-harness sync -w workspaces/<slug>   # rebuild project.json / INDEX.md from filesystem
```

A canonical workspace is a **file contract**:

```text
workspaces/<slug>/
├── protocol.json            # canonical, fingerprinted protocol
├── intent.json              # inception intent
├── SCREENING_CRITERIA.md    # rendered PRISMA criteria
├── INDEX.md                 # master catalog
├── project.json             # machine-readable state
├── audit/journal.jsonl      # append-only event ledger
├── literature/              # candidates, included/excluded, PRISMA report, screening batches
├── pdfs/                    # harvested OA PDFs (gitignored)
├── extracted/               # full-text Markdown with YAML frontmatter
├── synthesis/               # consensus, matrices, literature review
└── phase4/                  # trust_consensus*, RoB/COI/retraction reports
```

---

## Usage highlights

```bash
# Federated discovery + dedup
uv run scholar-search search --query "multispectral weed segmentation" --providers openalex semanticscholar crossref arxiv --year-min 2018 --limit 50 --output workspaces/<slug>/literature/raw_search.json
uv run scholar-search dedup  --input workspaces/<slug>/literature/raw_search.json --output workspaces/<slug>/literature/deduped.json

# PRISMA screening is an agent-in-the-loop handoff (not an opaque API)
uv run python src/scholar_harness/agent_screen.py prepare <ws>    # writes literature/screening/batch_NNN.json
#   ... an agent reads each batch and writes batch_NNN_decisions.json ...
uv run python src/scholar_harness/agent_screen.py collect <ws>    # assembles included.json / excluded.json / prisma_screening_report.md

# Harvest + extract with optional institutional-proxy rescue
uv run scholar-pdf download --input workspaces/<slug>/literature/included.json --output workspaces/<slug>/pdfs/ --smart-names --proxy https://www.sndl1.arn.dz --proxy-style subdomain
uv run scholar-pdf extract  --input workspaces/<slug>/pdfs/ --output workspaces/<slug>/extracted/ --engine pymupdf

# Synthesize, cartograph, verify
uv run scholar-rag synthesize --ws workspaces/<slug> --output-claims synthesis/claims.json
uv run scholar-rag consensus   synthesis/claims.json --rq-id RQ1
uv run scholar-graph build --input workspaces/<slug>/literature/included.json --output literature/knowledge_graph.html
uv run scholar-verify trust-context --workspace workspaces/<slug> --claims-dir synthesis --rq-id RQ2
```

---

## Quality & testing

```bash
uv run pytest              # harness suite (imports src/ + kits from tools/*/src via pythonpath)
uv run ruff check scripts/ # CI-scoped lint (this is the lint gate)
```

- Hermetic suites live beside each kit (`tools/<kit>/tests/`).
- CI (`.github/workflows/ci.yml`) runs on `main`/`develop` across `ubuntu/windows/macos` × Python `3.11/3.12`: ruff lint on `scripts/`, plugin-installer syntax, plugin manifest schema validation, and best-effort plugin install.

## Documentation

- **Design set:** [`docs/phase_0/`](docs/phase_0) (protocol schema, Socratic inception, playbooks) · [`docs/phase_5/`](docs/phase_5) (agent-first **Harness Console** — plan, blueprint, specs; not yet implemented)
- **Agent workflows:** `.agents/skills/<kit>/SKILL.md` per kit · MCP entrypoint at `.agents/plugins/nexus-scholar/mcp_config.json`
- **Roadmap state:** [`ROADMAP_ASSESSMENT_AND_TASK_LIST.md`](ROADMAP_ASSESSMENT_AND_TASK_LIST.md) · [`docs/UPCOMING_WORK.md`](docs/UPCOMING_WORK.md)

## Repository layout

```text
nexus-scholar-harness/
├── .agents/
│   ├── plugins/nexus-scholar/   # plugin registry (kit versions) + MCP config
│   └── skills/<kit>/            # per-kit agent skill: SKILL.md + references
├── src/scholar_harness/         # the thin orchestrator (cli, orchestrator, inception, agent_screen)
├── scripts/                     # install_plugins.py (kit installer), lint/validate helpers
├── tools/<kit>/                 # eight tracked kit packages (editable-installed into .venv)
├── docs/                        # phase_0 protocol specs, phase_5 console design, commit snapshots
├── workspaces/                  # research project workspaces (text/metadata tracked)
├── pyproject.toml
└── AGENTS.md                    # agent operational guidance (read me first)
```

## License

MIT. Free for academic and open-source use.

---

*Designed for **agent-native**, audited, reproducible literature research — from research question to trust-weighted consensus.*