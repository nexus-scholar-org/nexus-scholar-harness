# Context Efficiency Policy

**Status:** Active — governing document for agent context engineering in this repository.
**Scope:** the harness repository only (`nexus-scholar-org/nexus-scholar-harness`).
No `scholar-*-kit` source, pin, or vendored snapshot is changed by this policy, and
none may be changed because of it. A toolkit change follows the three-invariant
sync rule in `docs/architecture/DEVELOPER_COMPASS.md` §8 instead.
**Enforcement:** `scripts/check_context_policy.py` (see [How to verify](#how-to-verify)).

## Purpose

An external report titled *Optimizing Coding Harness Token Usage* makes a set of
context-engineering claims. Some of them describe mechanisms this repository
already implements, some are false **for this repository**, and some are
unverified vendor marketing. This policy records the three categories separately
so that a generic advice list can never inject a false repository invariant into
the harness.

The policy also fixes the reverse direction: the mechanisms this repository
already relies on are named with their real implementation paths, so a future
"simplification" cannot silently remove one of them.

Documented behaviour must match measured behaviour. Every measurable claim below
is either (a) re-checkable by the drift check in this repository, or (b) explicitly
labelled as an external measurement with its source status stated.

## Repository facts

These are the verified facts about this repository. The machine-checked subset is
enclosed in the facts block; `scripts/check_context_policy.py` parses that block
and fails when it disagrees with the script constants or with the repository.

```text
<!-- facts:begin -->
kit_root=tools
kits=scholar-agent-kit,scholar-bib-kit,scholar-graph-kit,scholar-pdf-kit,scholar-protocol-kit,scholar-rag-kit,scholar-search-kit,scholar-verify-kit
agents_md_word_floor=600
agents_md_word_budget=1500
source_report=Optimizing Coding Harness Token Usage
<!-- facts:end -->
```

The three tokens `kits/scholar-`, `scholar-monitor-kit` and `sqlite` are
**forbidden inside the facts block** — they are the three false invariants this
policy rejects. They are deliberately named in the prose below, because a policy
that rejects a claim must state what it rejects.

| # | Verified fact | Evidence |
|---|---|---|
| F1 | The repository has exactly **8** kits, all under `tools/`, each carrying a `pyproject.toml`. There is **no** root `kits/` directory. | `tools/` tree; `docs/architecture/README.md` ("the eight modular kits under `tools/`") |
| F2 | `scholar-monitor-kit` is **not** a kit of this repository, and never was. The name appears only in ecosystem design/planning documents — `docs/internal/ecosystem/NEXUS_MASTER_SPECIFICATION.md` (purged from the working tree; read it with `git show d08b388:docs/internal/ecosystem/NEXUS_MASTER_SPECIFICATION.md`) and `brainstorming/starter_pack_manifest.md` (purged; `git show f27d556:brainstorming/starter_pack_manifest.md`, where it is a planned notebook demo) — and was never realised as a kit directory in git history. The capability it was planned for (retraction status, open-science DAS/CAS, COI audit, risk-of-bias) lives in `scholar-verify-kit`. | `tools/` tree; `docs/architecture/README.md` Phase 4 row; root `AGENTS.md` (post-screening verification paragraph); `git log --all --diff-filter=A --name-only -- 'tools/scholar-monitor-kit/*' 'kits/scholar-monitor-kit/*'` returns nothing |
| F3 | The kits are vendored snapshots of eight external canonical repositories, pinned by full commit SHA in `.agents/plugins/nexus-scholar/plugins.json`. | `.agents/plugins/nexus-scholar/plugins.json`; `docs/architecture/DEVELOPER_COMPASS.md` §8 |
| F4 | **No `sqlite3` import exists anywhere under `tools/*/src`.** The search kit's HTTP cache is `hishel.AsyncCacheClient` (`hishel==0.0.32`) writing under `settings.cache_dir / "scholar_cache"`; the *only* SQLite wording in kit source is the human-readable description string of the `cache_dir` setting. | `tools/scholar-search-kit/src/scholar_search/http_client.py:64-84`; `tools/scholar-search-kit/src/scholar_search/config.py:26-28`; repository-wide scan of `tools/*/src` |
| F5 | **Rate limiting is real.** `AcademicHttpClient` wraps a `RateLimiter`, and per-provider `rate_limit_*` settings exist for OpenAlex, Crossref, Semantic Scholar and PubMed. | `tools/scholar-search-kit/src/scholar_search/http_client.py:18-27,64`; `tools/scholar-search-kit/src/scholar_search/config.py:34-46`; `tools/scholar-search-kit/src/scholar_search/providers/*.py` |
| F6 | **Heavy ML dependencies are real** in the RAG kit: `chromadb>=0.4.22` and `sentence-transformers>=2.3.1` are required, deliberately. | `tools/scholar-rag-kit/pyproject.toml` |
| F7 | The root `AGENTS.md` measured **1,436 words / 11,669 characters** at baseline commit `c10d2819` under the [counting convention](#counting-convention). The declared budget band is **600–1,500 words**. | `AGENTS.md`; facts block above; enforced by `scripts/check_context_policy.py` |
| F8 | `opencode.json` uses the `mcp` key with `"type": "local"`. `mcpServers` is not an OpenCode key. | `opencode.json` |
| F9 | `tools/scholar-agent-kit/.venv` holds **43,272 files / 1,397,817,885 bytes** (≈1.30 GiB). It is gitignored (`tools/scholar-agent-kit/.gitignore:1`, confirmed by `git check-ignore -v`) but sits **inside a tracked kit tree**. | `tools/scholar-agent-kit/.gitignore:1`; measurement taken 2026-10-20 |
| F10 | The MCP front door exposes **25 tools** (22 `nexus_*` + 3 `recon_*`) at a pinned rev. | `docs/kits_surface_matrix.md`; `.agents/plugins/nexus-scholar/plugins.json` |
| F11 | `.opencode/agent/` holds **11 agent definitions** (frontmatter generated from `roles/*.json`, instruction bodies preserved verbatim) plus a generated `_generated/permissions.json`. The former non-agent workflow note now lives at `docs/architecture/git_workflow.md`, outside the agent directory. | `.opencode/agent/*.md`; `.opencode/agent/_generated/permissions.json`; `scripts/generate_agent_roles.py`; `docs/architecture/git_workflow.md`; `tests/conformance/test_agent_role_permissions.py` |

## What this repo already implements

Do not re-invent these. The report's "recommended" mechanisms mostly describe
things that are already present here under different names.

| Mechanism | Real implementation in this repository | Path |
|---|---|---|
| Repository constitution | Root agent rules, contract-v1 baseline gate, contribution gate, toolkit sync rule, workspace/audit conventions | `AGENTS.md` |
| Nested domain constitution | UI-scoped agent rules, isolated from backend/kit history | `apps/research-ui/AGENTS.md`; `docs/architecture/agent_context_protocol.md` §UI isolation |
| On-demand domain skills | 14 skill bundles (8 kit skills + 6 cross-cutting), loaded only when the domain is touched | `.agents/skills/<name>/SKILL.md` |
| Task-context capsule | One compact capsule per task: stable sources read once, then capsule + repair delta only | `docs/architecture/agent_context_protocol.md` |
| Bounded reading set | Packet-size rule (capsule, ≤4 stable sources, exact line ranges) | `docs/architecture/agent_context_protocol.md` §Packet-size rule |
| Targeted test gates | `FAST` / `STANDARD` / `RELEASE` lanes with machine-readable gate selection | `docs/architecture/test_gate_policy.md`; `docs/architecture/test_gate_manifest.json`; `scripts/select_test_gate.py` |
| Evidence reuse | Documented reuse conditions for a recorded executable result | `docs/architecture/test_gate_policy.md` §Evidence reuse |
| Subagent roles with narrow permissions | 11 agent definitions; reviewer is `edit: deny`, `bash: ask`, `read: allow` | `.opencode/agent/*.md`; `tests/conformance/test_opencode_dev_agents.py` |
| Ignored heavy artifacts | Repo-level and kit-level ignore rules for `.venv/`, caches, PDFs, `chroma_db`, vendored JS | `.gitignore`; `tools/scholar-agent-kit/.gitignore` |
| MCP server configuration | Typed local MCP server under the valid `mcp` key | `opencode.json` |
| MCP front door | 25-tool front door with declared-unsupported boundaries | `.agents/plugins/nexus-scholar/mcp_config.json`; `docs/kits_surface_matrix.md` |

## Claims we reject (false for this repo)

| Claim | Verdict | Correct fact for this repo | Evidence path |
|---|---|---|---|
| The kits live under `kits/scholar-*` | **False** | Kits live under `tools/scholar-*`; there is no root `kits/` directory. | `tools/` tree; `docs/architecture/README.md`; enforced by the layout check |
| `scholar-monitor-kit` is one of the kits | **False (planned, never realised)** | Eight kits only. The name appears only in ecosystem planning documents and was never a kit directory in git history; the capability it was planned for lives in `scholar-verify-kit`. | `tools/` tree; `docs/architecture/README.md` Phase 4 row; git history query in F2 |
| The hardened kits use "local SQLite caching" | **False** | No `sqlite3` import exists anywhere under `tools/*/src`. The HTTP cache is `hishel.AsyncCacheClient` over a plain cache directory; only a description string mentions SQLite. | `tools/scholar-search-kit/src/scholar_search/http_client.py:64-84`; `tools/scholar-search-kit/src/scholar_search/config.py:26-28` |
| Rate limiting is part of the hardening story | **True here (keep it)** | Rate limiting is implemented: `RateLimiter` in the HTTP client plus per-provider `rate_limit_*` settings. | `tools/scholar-search-kit/src/scholar_search/http_client.py:18-27,64`; `config.py:34-46` |
| `scholar-rag-kit` carries heavy ML dependencies | **True here (keep it)** | `chromadb>=0.4.22` and `sentence-transformers>=2.3.1` are required on purpose. | `tools/scholar-rag-kit/pyproject.toml` |
| The root `AGENTS.md` should be cut to "under 200 words" | **False for this repo** | The root file is a constitution, not a summary. See [Root constitution budget](#root-constitution-budget). | `AGENTS.md`; `docs/architecture/DEVELOPER_COMPASS.md` §5, §9 |

### External corrections (verified 2026-10-20)

These are corrections to claims in the source report about tooling outside this
repository. They are recorded so the same wrong claim is not re-imported later.

| Report claim | Correct fact |
|---|---|
| `.claudeignore` is a context firewall | **No effect.** Claude Code's own documentation states that `.claudeignore` "has no effect". The working firewall is `permissions.deny` rules with `Read(...)` patterns. |
| The Anthropic prompt-cache prefix order is system → tools → messages | The order is **tools → system → messages**. The report inverted it. |
| OpenCode auto-compaction fires at 95 % of the context window | The default fires at **~85 %** (15 % buffer, 16k minimum), not 95 %. |
| `repo-mapper-mcp` is a PyPI package | It does not exist on PyPI. The real options are npm `repomap-mcp`, `pdavis68/RepoMapper` (Python), and `mackenney/repo-mapper` (Rust, whose `--max-tokens` default is 1024 — not a fixed 2048). |
| The npm package is `claude-context-mode` | The npm package is **`context-mode`**. |
| `trace-mcp` exposes 29 tools | It exposes **182** tools. |
| RTK is an npm package | RTK is a **Rust binary** distributed through brew/winget. The npm `rtk` package is unrelated. |
| AGENTS.md adoption by 60,000 repositories is a token-performance result | The 60,000 figure is a real **Linux Foundation adoption** statistic. It is an adoption count, **not** a performance measurement. |

## Claims that are vendor marketing, not measurements

None of the following is a verified property of this repository or of any vendor
product. They may be quoted as marketing, never as evidence.

| Claim | Corrected number / status | Source status |
|---|---|---|
| "Claude Code natively uses 5.5x fewer tokens than Cursor" | 5.5x is a **third-party builder.io single-task benchmark**, not an Anthropic property. | Third-party benchmark, single task, not a vendor guarantee. |
| "openslimedit reduces token usage by 45 %" | 45 % is **self-measured by the vendor on 4 tiny files**; the npm description says **33 %**. | Vendor self-measurement; two different numbers in the vendor's own material. |
| "ast-grep-mcp cuts ~75 % fewer tokens" | **Unmeasured vendor README claim.** | No independent measurement. |
| "Subagent isolation keeps the main session under 50K tokens and cuts cost ~60 %" | **No Anthropic source exists for either figure.** | Unsourced. |
| "trace-mcp saves ~11,600 tokens" | The figure **appears in no source**. | Unsourced. |
| "mackenney/repo-mapper uses a fixed 2048-token map" | The default is `--max-tokens` **1024** and is configurable. | Corrected against the tool's own CLI defaults. |

## Adopt now / Defer / Reject

| Mechanism | Decision | Reason |
|---|---|---|
| Root `AGENTS.md` as the single constitution | **ADOPTED NOW** (already implemented) | It carries the invariants below; see `AGENTS.md`. |
| Nested `AGENTS.md` for the UI domain | **ADOPTED NOW** (already implemented) | `apps/research-ui/AGENTS.md` isolates UI work from kit/contract history. |
| On-demand per-domain `SKILL.md` | **ADOPTED NOW** (already implemented) | 14 skill bundles load only for the domain in play. |
| Task-context capsule + bounded reading set | **ADOPTED NOW** (already implemented) | `docs/architecture/agent_context_protocol.md` bounds every round. |
| Targeted gates + evidence reuse | **ADOPTED NOW** (already implemented) | `docs/architecture/test_gate_policy.md` avoids paying for a full suite per edit. |
| Narrow-permission subagent roles | **ADOPTED NOW** (already implemented) | `.opencode/agent/*.md`; reviewer cannot edit. |
| MCP firewall via `permissions.deny` `Read(...)` rules | **DEFERRED** | **Current state: this repo has no such rules.** `opencode.json` declares no top-level `permission` block and no agent registration: the former decorative `agents` block (removed 2026-10-28) carried a harness-internal `permissionRef` pointer that opencode never read — opencode discovers agents from `.opencode/agent/*.md` frontmatter. That generated frontmatter is tool-level only (`reviewer.md` has `edit: deny`), with no `Read(...)` path-pattern deny anywhere. **Target surface:** `opencode.json` permission rules. **Why deferred:** the harness agents are required to read `tools/`, `docs/` and the kit trees by design, and no read-path audit has been done, so adding deny rules today risks breaking legitimate reads. **Reopen when** a read-path audit of the harness agents exists and the deny patterns can be shown to exclude only non-source trees. (The external fact is unchanged and is about Claude Code, not this repo: `.claudeignore` is a no-op there, and `permissions.deny` `Read(...)` rules are that product's working mechanism.) |
| Scope every repository search to `tools/<kit>/src` | **ADOPT NOW** | A recursive root-level read drowns in the nested `tools/scholar-agent-kit/.venv`; the dated file count is in [Measured hazards](#measured-hazards). |
| Keep the `mcp` key with `"type": "local"` in `opencode.json` | **ADOPT NOW** | `mcpServers` is not a valid OpenCode key; the current config is correct. |
| Trim the root `AGENTS.md` to "under 200 words" | **REJECTED** | It would delete the contract-v1 baseline gate, the fork+PR contribution gate, the toolkit three-invariant sync rule, and the workspace/audit conventions. |
| Adopt "local SQLite caching" as a hardening feature | **REJECTED** | No `sqlite3` import exists under `tools/*/src`; the claim is false for this repository and adding it would be unjustified scope. |
| Tune OpenCode auto-compaction away from its default | **DEFERRED** | The default already fires at ~85 % (15 % buffer, 16k minimum); no measured gain is available for this repository, and the threshold is not the 95 % the report assumes. |
| Repo-map MCP (`repomap-mcp`, `RepoMapper`, `repo-mapper`) | **DEFERRED** | An external server with no measured benefit here; the capsule protocol already bounds the reading set. Re-evaluate only with a measured harness-side result. |
| `context-mode` (npm) | **DEFERRED** | Third-party MCP server; the repo already has on-demand skills and a bounded reading set. |
| `trace-mcp` | **DEFERRED** | 182 tools would enlarge the tool-surface context for no measured gain. |
| `ast-grep-mcp` | **DEFERRED** | Its 75 % figure is an unmeasured vendor README claim. |
| `openslimedit` | **DEFERRED** | 45 % / 33 % are vendor self-measurements on four tiny files. |
| RTK (Rust binary) | **DEFERRED** | Not an npm package; adds a non-Python binary dependency with no measured gain here. |
| Subagent isolation under a "50K token" target | **REJECTED as a target** | No Anthropic source supports the 50K/60 % figures. |

## Measured hazards

**`tools/scholar-agent-kit/.venv` — 43,272 files / 1,397,817,885 bytes (≈1.30 GiB),
measured 2026-10-20.** The directory is gitignored
(`tools/scholar-agent-kit/.gitignore:1`, confirmed with `git check-ignore -v
tools/scholar-agent-kit/.venv/`), so it never reaches a commit — but it lives
**inside a tracked kit tree**, so any recursive read that ignores `.gitignore`
(or any search tool without ignore support) drowns in it.

Concrete rule:

- Scope repository searches to `tools/<kit>/src` (and `tools/<kit>/tests`).
  **Never recurse from the repository root.**
- For repository-wide questions use `git ls-files` / `git grep`, which honour the
  tracked tree and therefore skip the nested virtual environment.
- The same hazard exists for the other ignored trees: `.cache/` (grounded-recon
  cache root), `workspaces/**/pdfs/`, `rag/chroma_db/`, and the vendored `lib/`
  JavaScript. See `.gitignore` and the root `AGENTS.md` "Where research output
  goes" section.

This is the repository-specific version of the source report's "context firewall"
advice: the enforceable equivalent of an ignore file is a scoped search, because
a tool that ignores `.gitignore` will still read the virtual environment.

## Root constitution budget

### Counting convention

Every size figure in this policy uses one convention, so that two numbers are
always comparable:

- **Word count** — whitespace-delimited tokens of the file content
  (`len(text.split())`); the trailing newline does not add a token.
- **Character count** — characters of the file content after normalising CRLF
  line endings to LF, including the trailing newline.

The convention is stated because a CRLF checkout and an LF checkout of the same
file differ by one character per line: publishing a CRLF count next to an LF
count implies a growth that does not exist.

| Item | Value |
|---|---|
| Baseline commit `c10d2819` (measured 2026-10-20) | **1,436 words / 11,669 characters** |
| Worktree after CTX-1 repair round 1 (measured 2026-10-20) | **1,487 words / 12,128 characters** |
| Declared budget band | **600 – 1,500 words** (floor / budget; enforced) |
| Enforcement | `scripts/check_context_policy.py` — fails below the floor, above the budget, or when an invariant marker is missing |

### Derivation of the band

- **Upper bound (1,500 words) — a bounded-regression guard, not a target.** The
  measured baseline is 1,436 words, so the ceiling leaves roughly 60 words of
  documented headroom for one further non-obvious invariant. The ceiling exists
  to stop the constitution from growing without review; it does not license
  growth towards it.
- **Lower bound (600 words) — a size proxy only.** It exists to catch a
  catastrophic truncation (a truncated file, a bad merge, a partially applied
  edit). It is **not** an invariant check: a file can be cut from 1,436 to 700
  words while dropping the contract-v1 baseline gate, and the floor would still
  pass. The floor must never be cited as evidence that the invariants survive.
- **The invariant check is the real control.** `scripts/check_context_policy.py`
  verifies that `AGENTS.md` still contains each of the six invariants below,
  matching a marker per invariant, case-insensitively. Removing one is a
  reported failure that names the invariant, whatever the remaining word count.

### The six invariants the root file must keep

| # | Invariant | Marker verified in `AGENTS.md` | What it protects |
|---|---|---|---|
| 1 | Contract v1 baseline gate | `generate_contract_baseline.py --check` | Read `docs/architecture/contract_v1_baseline.md`, run the baseline check, report `BLOCKED_BASELINE_DRIFT` on failure; never regenerate to bless a change. |
| 2 | Fork + PR contribution gate | `pull-request-gate` | Improvements ship through the personal fork and a PR to `nexus-scholar-org/nexus-scholar-harness`, never by pushing a feature branch to canonical `origin`. |
| 3 | Toolkit three-invariant sync rule | `The three invariants change together, never alone` | A kit code change must land in that kit's own canonical repository, bump `plugins.json` `default_rev` to the full commit SHA, and leave the vendored `tools/<kit>/` tree synchronized. |
| 4 | Workspace and audit-ledger conventions | `audit/journal.jsonl` | Output belongs under `workspaces/<project-slug>/`, every significant step is logged to the append-only audit ledger, and the workspace layout is canonical. |
| 5 | `uv run` only | `Never rely on a system Python` | Everything runs through the project venv. |
| 6 | Kit domain skills and MCP front-door path | `mcp_config.json` | Which `SKILL.md` to load before working in a domain, and where the MCP server entrypoint lives. |

The markers are the same strings the check uses (`AGENTS_MD_INVARIANTS` in
`scripts/check_context_policy.py`), so the binding between this table and the
executable check can be read off directly.

The generic "keep the root `AGENTS.md` under 200 words" rule is **REJECTED** for
this repository. The root file is not a summary of the repository; it is the
constitution that stops agents from making specific, expensive mistakes. Cutting
it to 200 words would delete the invariants above — and, as noted, the size-only
floor would not notice.

The band, not the 200-word rule, is the operative size constraint: the file may grow
to 1,500 words if a new non-obvious invariant must be recorded, and must shrink
when an invariant is retired.

## How to verify

```powershell
uv run python scripts/check_context_policy.py --check
```

Exit code 0 means the policy still matches the repository; exit code 1 lists
every mismatch. The check verifies the kit inventory under `tools/`, the absence
of a root `kits/` directory, the `mcp`/`mcpServers` shape of `opencode.json`, the
`AGENTS.md` word band **and** the six `AGENTS.md` invariant markers, the policy
facts block against the script constants and against the three forbidden
false-invariant tokens, and the presence of the source-report citation. A nested
`tools/*/.venv` is reported as an advisory, not a failure. A file that is not
valid UTF-8 is reported as a failure naming the file, never as a traceback.

The regression tests for the check live in `tests/unit/test_context_policy.py`:

```powershell
uv run pytest tests/unit/test_context_policy.py -q
```

## Provenance

Assessed against the external report *Optimizing Coding Harness Token Usage* on
**2026-10-20**. Repository facts were measured in this repository at that date;
external corrections were verified against the vendors' own documentation and
package metadata on the same date. Claims marked as vendor marketing are
reproduced only so that they can be refused by name.
