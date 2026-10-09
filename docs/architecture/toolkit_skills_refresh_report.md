# Toolkit Skills Refresh Report

**Task:** TOOLKIT-SKILLS-REFRESH · **Lane:** FAST (documentation-only, no runtime change)
**Base:** `83c54814efdf0956fb0a9dc8dcfb051f0d1a65fd` (`origin/main`) · **Branch:** `cdx/toolkit-skills-refresh`
**Worktree:** `C:/Users/mouadh/AppData/Local/Temp/opencode/toolkit-skills-refresh` (isolated; primary checkout untouched)
**Primary dirty baseline (preserved):** `M .opencode/agent/reviewer.md`, `M apps/research-ui/{AGENTS.md,README.md,docs/GATES.md,tests/*.test.tsx}`, `M docs/architecture/research_ui/AGENT_WORK_PACKETS.md`

## Kit pins verified (`.agents/plugins/nexus-scholar/plugins.json`)

| Kit | `default_rev` |
|---|---|
| scholar-protocol-kit | `4e10f25c25a1b150ce518348d211c7771683a9b7` |
| scholar-search-kit | `911d864fcb6a706d4c0339f80524a46f591e2cad` |
| scholar-pdf-kit | `3c024c37071b49265cfea6e713c1c9065e2a2cc0` |
| scholar-bib-kit | `fbdd38ba25301e613621f18119623f04d2673dca` |
| scholar-graph-kit | `646b84cec215ebd9b7b449448bca879492e78492` |
| scholar-rag-kit | `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad` |
| scholar-agent-kit | `79ffe421dfea2a2b6e4c02fdff651e6d23ce9b92` |
| scholar-verify-kit | `44a8d63cc0a11694bbcb7a355a53f73c3f93145c` |

All claims below were verified against these vendored implementations, not memory or historical reports.

## Allowed / immutable boundaries

- **Allowed:** `.agents/skills/scholar-*/**` (8 skills), mirrors via `scripts/sync_skills_bundle.py` only, this report.
- **Immutable (untouched):** `tools/**/`, pins, `packaging/**`, generated contracts/schemas/fixtures, HCM docs, unrelated skills, UI files.
- **Ownership:** runtime belongs to the eight canonical `nexus-scholar-org/scholar-*-kit` repos. No `push_tools.py`, no pin bump. No `BLOCKED_CANONICAL_REPO` — no kit source fix was required for this refresh.

## Corrections by kit

### RAG (`scholar-rag-kit`, rev `15a7a5a…`)
- Rewrote SKILL.md 212→93 lines + 3 new refs (`typed_index.md`, `retrieval_synthesis.md`, `mcp_and_boundaries.md`).
- Fixed stale line refs: `index_workspace` `:722`→`:752`, `IndexServiceRequest` `:370`→`:400`, exit codes `:209`→`:223`, run actions `:195`→`:209`, chunker threshold `:530`→`:531`, retriever over-fetch `:205`→`:204`, orchestrator Stage 6 `:1402`→`:1425`.
- Removed unrunnable minimal `index docs/ --embedder gemini` example (10 flags required; no `--api-key` on `index`); relabeled `NumpyBackend`/`LLMExtractor`/`PIIRedactor`/`extract` as auxiliary-only.
- Clarified `nexus_rag_index` declared-unsupported envelope (`rag_index`/`FAILED`/`UNSUPPORTED_CAPABILITY`, zero I/O) with CLI/API alternative; scoped legacy-`ScholarIndexer` supersession to Stage 6.

### PDF (`scholar-pdf-kit`, rev `3c024c3…`)
- Fixed cascade 2-stage→4-stage (OpenAlex→Unpaywall→publisher direct→proxy rewrite); validation to versioned header/trailer/floor; naming to content-addressed `DOC-<32hex>.pdf` with `--smart-names` inert note.
- Fixed MCP `nexus_extract_pdf` to heuristic path-derived metadata + engine routing (not dead/`metadata`-dropped); E2 envelope now includes `warnings=[]`.
- Preserved E1 dual-parent / E2 single-parent + transitive `corpus_fingerprint`, `ACQ-/DOC-/EXT-` identities, fail-closed, candidate `not_performed_by_kit`, registry `UNSUPPORTED_ARTIFACT_TYPE`.

### Agent (`scholar-agent-kit`, rev `79ffe42…`)
- Single-file rewrite (~190→~150 lines) as compact 25-tool entrypoint with signature→return table.
- Stated all three refusals explicitly: E1 `acquire_pdf`, E2 `extract_pdf`, E3 `rag_index` (each `FAILED`/`artifacts=[]`/`warnings=[]`/one non-retryable `UNSUPPORTED_CAPABILITY`, zero I/O, CLI/API alternative).
- Fixed launch/anchoring (`--directory tools/scholar-agent-kit`, `_resolve_path`→`NEXUS_MCP_WORKSPACE`-else-repo-root), recon root, return conventions, query `graph_source`/α/β, verify bridge, phase4 fields, critique, screen-LLM outputs.

### Search (`scholar-search-kit`, rev `911d864…`)
- Fixed `export` to positional `<input> <output> --format` (no `--output`); dedup to only `--output/--format`; `Query`/`Document`/`ExternalIds` imports to `scholar_search.models`.
- Fixed `compile_protocol_search` example (name strings→provider instances; finding-9 bug documented, not replicated).
- Updated `nexus_screen` to persist all five artifacts (removed stale never-written claim); added `nexus_screen_llm` + reconcile map-or-directory + adjudication semantics.

### Protocol (`scholar-protocol-kit`, rev `4e10f25…`)
- Fixed canonical description (declaration-order + nested-sorted, arrays unsorted, `sha256:<64hex>` over compact bytes).
- Fixed `nexus_protocol_validate`: both file and inline run full structural + cross-field rules (was structural-only-inline).
- Added missing `validate --strict` surface, golden-`.sha256` gate, derived-schema note, JSON-error-not-MCP-failure, legacy-explicit routing.

### Bib (`scholar-bib-kit`, rev `fbdd38b…`)
- Fixed `nexus_bib_clean`: lint-only/`generate_keys=False` → full pipeline `lint(generate_keys=True)` + `dedup`, in-place by default, never resolves.
- Added `AuthorYear` key anatomy (FirstAuthorLastName+Year, `a/b/c` suffix, author+year guard), in-place defaults, dedup `_clean_string`, resolver `transform/x-bibtex` + key preservation + swallow-`None` + narrow DOI strip + 10/s.

### Graph (`scholar-graph-kit`, rev `646b84c…`)
- Fixed `nexus_graph_build` to real `AcademicHttpClient(name="openalex-graph", rate_limit=10)` (not 0-edge); stated DOI precedence, `results`/`items`, empty-input error.
- Removed obsolete `analyze`/`cluster`/`--format`/`--mode` surfaces; corrected `config.Settings`/`GraphNode`/`GraphEdge` as dead-but-present; added `nexus_graph_narrative`, sidecar/`pagerank`-key, intra-pool-only, RAG-blend vs compute-α, PyVis CDN/offline notes.

### Verify (`scholar-verify-kit`, rev `44a8d63…`)
- Replaced obsolete CLI-crash + CLI-only claims with workspace guard (`protocol.json` or `INDEX.md`), `all≠all` (CLI 4-core vs MCP `all` with trust-context `SKIPPED` sentinel), envelope `{run_metadata,summary,results}`.
- Separated verbatim matching from RAG cosine-similarity vocabulary; documented claims bridge (`claim_text` fallback, per-claim verdicts, `failures_by_reason`, `rag_entailment_status`).
- Stated MCP `skip_retraction=True` default, network-only-retraction, arXiv short-circuit, contiguous-chunk `SystemExit`, trust ladder + dead constant.

## Verification evidence (FAST)

- `uv run python scripts/sync_skills_bundle.py --check` → all `OK` (13/13) after sync; pre-sync `DIFF` on the 8 refreshed skills was expected (canonical-first, orchestrator-synced).
- `git diff --check` → clean (only benign LF→CRLF advisories).
- Narrow static checks per skill (AST import/CLI verification, citation line resolution, negative-phrasing greps, ref/link existence) → PASS (see worker acceptance maps). No searches, downloads, servers, or workspace mutations; live `--help` unavailable in bare worktree venv by design (AGENTS.md), so CLI surfaces were verified from pinned `cli.py`/`server.py` slices.
- Drift: `tests/conformance/test_count_freshness.py` applicable at checkpoint; no pin/vendor/contract/fixture change in this lane (`git diff --name-only -- tools/ plugins.json packaging/` empty before report).

## Unresolved limitations

- Live CLI/MCP execution not performed (bare venv, no network); evidence is source-slice + help-text verification.
- RAG deeper R1–R7 semantics, graph `visualizer.py` PyVis-only mutation nuance, and matrix PDF row vs finding-3 wording remain follow-ups outside allowed paths.
- `docs/kits_surface_matrix.md` line numbers and one stale PDF-row sentence were left untouched (matrix owner follow-up).

## Deferred defects (kit-owned, NOT fixed here)

- RAG: `GeminiEmbedding` Chroma-protocol gap; retriever/synthesis CWD-dependent journal discovery.
- Search: `__init__.__all__` re-export gap for `Query`/`Document`/etc.
- PDF: dead `--smart-names` path; matrix PDF row staleness.
- Bib: `>=2.0.0b7` floor vs `2.0.0b9` doc; narrow DOI strip; `resolve update_progress` no-op.
- Graph: vendored `scientometrics.py`/extra CLI verbs out-of-pin; `value`/`title` mutation scope needs canonical clarification.
- Verify: CLI-vs-MCP `verbatim-claims` shape asymmetry; `all --skip-retraction` default asymmetry; dead `_FLAG_REASON_SENSITIVE`; unregistered `ingress` docstring.
- Protocol: `_response` warning-drop on VALID; `identity.py` PRT-vs-`proto-` ID nuance.
- Agent: undeclared verify dep breaks bare-`uv sync`; terse `--help` epilog.

## Next gate

Scoped factual review → repair-delta verification only → fork PR (no merge, no pin change, no HCM work).

### Repair delta (review P2 ×3)

- RAG+PDF E3 adapter EXISTS (`src/scholar_harness/index_acceptance.py` `accept_index_candidate`, `index-acceptance-v1` → `rag/index/accepted.json` + `RAG_INDEX_BUILT`); kit `SUCCESS` ≠ acceptance; ledger `MISSING == ()`; Stage 6 via `index_accepted_documents` → typed `index_workspace`.
- RAG index example: workspace-relative `extracted/` + `run-reports/rag-index.jsonl` + explicit `--db-path`; note `<ws>`-prefix doubling.
- Chain flags: `--direction backward --direction forward` (repeat flag).
- Deferred (kit-owned, NOT fixed here): `tools/scholar-search-kit/src/scholar_search/cli.py:384` docstring repeats `-d backward forward`; belongs to `nexus-scholar-org/scholar-search-kit`.
