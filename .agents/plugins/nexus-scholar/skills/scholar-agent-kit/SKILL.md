---
name: scholar-agent-kit
description: The MCP front-door to the eight kit CLIs: discovery, screening hand-off, retrieval, verification, and recon — with declared-unsupported refusals.
applies_to: [orchestrator, inception-agent]
requires: [scholar-agent]
variables: [CACHE, CLI, CONFIG, KIT_ROOT, SKILL_DIR, WORKSPACE]
returns: json
layer: domain
---
# `scholar-agent-kit` Skill Instructions

MCP front-door for most Nexus Scholar surfaces — **not** every API/CLI capability.
31 tools: 28 `nexus_*` + 3 `recon_*` (`scholar-agent --help` lists all 31 registered tools; parity
enforced by `tests/conformance/test_mcp_tool_parity.py`). Pinned source:
`{KIT_ROOT:agent}/src/scholar_agent/server.py` (tool list/signatures,
`_resolve_path`, refusals) + `capabilities.py` (registry; pin: see `{CONFIG}`).
Detail pointers below route to `--help`, the surface matrix, and those two
files — this page stays the small-footprint entrypoint.

## Preflight
- `MCP nexus_*` availability, or `{CLI:agent} --help` resolves (lists all 31 registered tools) → else `BLOCKED_INPUT`.
- `{WORKSPACE}` resolves — `protocol.json`/`project.json` where the tools require workspace input; `literature/extraction/merged/records.json` + `phase4/_manifest.json` for #18/#19.
- `{CONFIG}` present (the pin manifest).

## Refusals
- `E1` / `E2` / `E3` declared-unsupported refusals (§3): JSON envelope with `code="UNSUPPORTED_CAPABILITY"`, `status="FAILED"`, `retryable=false`.

## Pointers
- `docs/kits_surface_matrix.md` (agent-kit section, E1/E2/E3 boundaries).

## 1. Launch & path anchoring

```bash
{CLI:agent} [--workspace <ws>]
{CLI:agent} --help  # lists all 31 registered tools
```

- Server CWD is `{KIT_ROOT:agent}/`; `mcp_config.json` ships no `env`/cwd.
- Relative file/dir args are anchored by `_resolve_path` (`server.py:255`) to
  `NEXUS_MCP_WORKSPACE` when set, else the harness repo root (nearest `.git`
  ancestor) — **not** the kit checkout. Absolute paths and inline-JSON payloads
  (protocol/intent/screener) pass through untouched. Prefer absolute
  `<workspace>/…` paths anyway; never assume a bare `./…` default is
  workspace-relative unless `NEXUS_MCP_WORKSPACE` (or `-w`) is set.
- `-w/--workspace <ws>` (`server.py:2069`): sets `NEXUS_MCP_WORKSPACE` and, when
  unset, defaults `NEXUS_RECON_ROOT` to `<ws>/.cache/inception_recon`.
- Recon cache is CWD-independent: `canonical_recon_root()` =
  `NEXUS_RECON_ROOT`, else `<repo>/.cache/inception_recon`, shared by CLI
  wizard and MCP. Sessions:
  `.cache/inception_recon/sessions/<session_id>/session.json` + content-addressed
  `pool_<sha>.json` / `distilled[_lx<sha>]_<…>.json`.
- Known gap: client auto-setup should set `NEXUS_RECON_ROOT` explicitly since
  `mcp_config.json` declares no `env`.

## 2. Tool inventory — Exposed MCP Tools (31 total) — signature → return

| # | Tool | Key signature (defaults) | Returns |
|---|------|--------------------------|---------|
| 1 | `nexus_protocol_compile` | `(intent_json: str)` path or inline JSON | JSON `{status, protocol_id, fingerprint, protocol}`; does **not** persist — write `protocol.json` yourself |
| 2 | `nexus_protocol_validate` | `(protocol_json: str)` path or inline JSON; **both** modes run structural + cross-field rules | JSON `{status: VALID\|INVALID, …}`; never an MCP failure |
| 3 | `nexus_protocol_render_criteria` | `(protocol_path: str)` path-only | raw markdown prose (`Error: …` on failure) |
| 4 | `nexus_discover` | `(query, limit=10, start_year=2020)`; 4 providers (OpenAlex/S2/Crossref/arXiv — no PubMed/bioRxiv), `dedup=True` forced | prose; writes anchored `.cache/mcp/discover_<slug>_<ts>.json` + preview |
| 5 | `nexus_dedup` | `(input_path, output_path="./deduped.json")` PID + title clustering | prose (`Error: …`) |
| 6 | `nexus_screen` | `(input_path, protocol_path, output_dir="./literature")` heuristic | prose; **proposals only** (AGT-16): writes `screening_proposals.json` (status `PROPOSALS_ONLY`, proposals + preview counts), never the published partition; journals `MCP_SCREENING_PROPOSED` inside a workspace |
| 7 | `nexus_extract_pdf` | `(pdf_path, output_dir="./extracted", engine="pymupdf")`; `title`/`doi`/`workspace_id` heuristically derived from path (§5) | prose (`Error…` prefix); **not** an envelope |
| 8 | `nexus_pdf_acquire` | 14 E1-shaped args, all default `""`, discoverability only | JSON refusal envelope (§4) |
| 9 | `nexus_pdf_extraction` | `(pdf_path="", output_dir="", engine="")`, discoverability only | JSON refusal envelope (§4) |
| 10 | `nexus_rag_index` | `(docs_dir, db_path="./chroma_db", bib_file=None, workspace_id=None)`, discoverability only | JSON refusal envelope (§4); retrieval tools unaffected |
| 11 | `nexus_rag_query` | `(query, db_path="./chroma_db", section=None, section_category=None, paradigm=None, boost_doi=None, n_results=5, graph_source=None, alpha=0.25, beta=0.15)`; blend `CosineSim + alpha*PageRank + beta*seed` | prose hits with citation tokens (`Error…`); categories: `abstract_intro`, `methodology`, `results_empirical`, `discussion_limitations` |
| 12 | `nexus_rag_synthesize` | `(query, rq_id="RQ1", db_path="./chroma_db", section_category=None, paradigm=None, n_chunks=5)`; entailment = embedding-cosine wording (§5) | prose synthesis + verified-count header (`Error…`) |
| 13 | `nexus_matrix_extract` | `(workspace_dir=".", protocol_path=None→<ws>/protocol.json, output_dir="./literature")`; retriever db pinned to `<workspace_dir>/chroma_db` | prose (`Error…`) |
| 14 | `nexus_graph_build` | `(input_path, output_html="./graph.html", json_output="./graph.json")`; real `AcademicHttpClient(name="openalex-graph", rate_limit=10)`; accepts list or `{results\|items}` dicts; DOI precedence `external_ids.doi → doi`; errors on zero DOIs | prose (`Error…`) |
| 15 | `nexus_screen_reconcile` | `(screeners_json, adjudication_json=None)`; dir of `batch_*_decisions*.json` or screener→decision map | JSON majority-vote + Fleiss' κ (`{"status":"ERROR"…}` on failure) |
| 16 | `nexus_verify_claims` | `(claims_json_path, extracted_dir_path, threshold=0.90)`; accepts `{claims:[…]}` or bare list, `claim_text` as quote; surfaces RAG `entailment_status` as `rag_entailment_status` | JSON `{status, metrics, failures_by_reason, claims}` |
| 17 | `nexus_verify_phase4` | `(workspace_dir=".", stream="all", sleep_s=0.2, skip_retraction=True, rq_id=None)`; streams `retraction\|open-science\|coi\|risk-of-bias\|trust-context\|all`; `retraction` is network-bound; `trust-context` SKIPS cleanly without `synthesis/consensus.json` | JSON `{status, stream, written}`; writes `<ws>/phase4/<name>.{json,md}` |
| 18 | `nexus_critique_methodology` | `(workspace_dir, protocol_path=None, rq_id=None)`; needs `literature/extraction/merged/records.json` + `phase4/_manifest.json`; QUADAS-2/PROBAST via verify kit | JSON `{status, overall_risk, domain_ratings, per_study_count, output_path}`; writes `phase4/methodological_critique.md` |
| 19 | `nexus_graph_narrative` | `(workspace_dir, graph_json_path, top_hubs=10)`; hubs by PageRank, communities by `group` | JSON `{status, n_hubs, n_communities, output_path}`; writes `synthesis/visual_synthesis.md` |
| 20 | `nexus_pipeline_run` | `(workspace_dir, query=None, protocol_path=None, skip_stages=None)`; 10-stage `ResearchOrchestrator`, comma-separated skips | JSON result (`{"status":"ERROR"…}` on failure) |
| 21 | `recon_probe` | `(topic, session_id=None, start_year=2020, limit=10, semantic=False)`; pool capped at 25; `semantic=True` → OpenAlex `search.semantic` (`/m/semantic/` cache-key segment); upserts `rec_<hex>` sessions | JSON `{session_id, cache_key, status: probe_ok, n_docs, pool_path}` |
| 22 | `recon_distill` | `(session_id, lexicon_json=None)`; str **or** dict; optional `metrics/datasets/schools` regex→label maps merged over default; lexicon hash in artifact name; carries `pool` sufficiency + `purity` gates (`qei` never standalone) | JSON `{session_id, cache_key, terms_path, qei, pool, purity, metrics, datasets, schools, topics, micro_taxonomy_top}` |
| 23 | `recon_delta` | `(session_id, followups=3)`; hard cap 3; thin schools `n ≤ 2`; gap reason verbatim under `reason` **and** `confidence.detail` (`label: gap`); `corpus_total` + `saturation_label` per follow-up; `dropped_n` counts 25-cap discards | JSON `{session_id, merged_cache_keys, followups, pool_path, terms_path, topics, dropped_n, pool_size_before/after}` |
| 24 | `nexus_screening_queue` | `(workspace_dir=".", view="needs_you", limit=50)`; views `needs_you`, `no_proposal`, `decided` | JSON `{status, items:[{study_id, title, has_proposal}]}`; never shows an agent outcome |
| 25 | `nexus_screening_record` | `(study_id, workspace_dir=".")` | JSON `{status, study_id, title, abstract, criteria, answers}`; evidence offsets index into title + blank line + abstract |
| 26 | `nexus_submit_proposal` | `(study_id, proposal_json, model, task_version="screen-v1", prompt_sha256=None, workspace_dir=".")`; one answer per criterion with a verbatim evidence span | JSON `{status, proposal_id, derived_outcome, validators}`; appends to the proposal store, journals, **never** writes a decision |
| 27 | `nexus_assistant_drafts` | `(workspaces_root=None)`; the app's root (`NEXUS_WORKSPACES_ROOT` or the default) | JSON `{status, workspaces_root, drafts:[{session_id, topic, title, updated_at, emitted, open_proposals, findings}]}`; read-only |
| 28 | `nexus_assistant_read_draft` | `(session_id, workspaces_root=None)` | JSON `{status, draft, intent, intent_refused, grounding, checks, proposals, pool}`; read-only (the checks are computed as the app does; nothing is recorded) |
| 29 | `nexus_assistant_read_workspace` | `(workspace_dir)` a slug under the app's root, or a path inside the MCP anchor | JSON `{status, intent, protocol, plan, recall, checks, proposals}`; `plan.providers[]` carries each database's translation and `cannot_express`; read-only |
| 30 | `nexus_assistant_propose` | `(field, op, value, why, model, session_id=None, workspace_dir=None, task="suggest", evidence=None, workspaces_root=None)`; exactly one of `session_id`, `workspace_dir`; `task` ∈ `suggest\|synonyms\|translation\|recall_repair` | JSON `{status, created, proposal}`; one open proposal, source `agent:<model>`. On a draft: on the app's card for its step; a side write (no answer, no `updated_at` change); checked as a save of the field would be; refused after genesis (`DRAFT_EMITTED`). On a workspace: a card on Discovery Plan; only the search (`core_concepts` add, `core_concepts[<name>].synonyms` add/remove, `start_year`/`end_year` replace, `languages`); checked as an Apply would be; refused once a corpus is accepted (`CORPUS_ALREADY_ACCEPTED`). At most 30 open |
| 31 | `nexus_assistant_report_finding` | `(locator, severity, finding, model, session_id=None, workspace_dir=None, why=None, workspaces_root=None)`; exactly one target; `locator` a JSON pointer into the intent (`draft:/…` into a draft's answers, `protocol:/…` into a workspace's `protocol.json`); `severity` ∈ `critical\|major\|minor` | JSON `{status, created, finding}`; an `ASSISTANT_FINDING` row (`source: "agent"`, never a blocker) in the app's checks panel; draft: record key `assistant_findings`; workspace: `audit/assistant_findings.jsonl` + `ASSISTANT_FINDING_REPORTED`; at most 50 open |

Return rule of thumb: **JSON** = #1, #2, #8–#10, #15–#31.
**Prose** (`"Error: …"` prefixes, no envelope) = #3–#6, #7, #11–#15.

`nexus_screen_llm` was removed on 2026-11-23 (H-close-side-doors): use the app's agent run or #26.

## 3. Declared-unsupported capabilities (E1, E2, E3)

The front-door **declares** what it does not serve (`scholar_agent.capabilities`,
immutable `CapabilityDeclaration`s) so a refused call is observable, not a
vanished tool. Every refusal: JSON operation envelope with `operation`,
`status="FAILED"`, `artifacts=[]`, `warnings=[]`, exactly one error
`code="UNSUPPORTED_CAPABILITY"`, `retryable=false`; unconditional and
pre-validation (no run identity echoed — fabricating one would be worse);
**zero I/O** by construction (pure builders over the immutable registry — no
transport, engine, file, store, sidecar/manifest, or audit-success append). A
rejected call **never succeeds on retry**; describe refusals as refusals, not
as successes. Each is an explicit *unsupported difference*, **never** a parity
claim. The envelope is operation-envelope vocabulary, **not** a Contract v1
`OperationOutcome`.

- **E1 — `nexus_pdf_acquire`** (`pdf_acquisition`, `mcp_supported=false`, owner
  `nexus-scholar-org/scholar-pdf-kit`): every call →
  `operation="acquire_pdf"` refusal. Use instead: `{CLI:pdf} acquire
  <config.json> --audit-logger <path-to-log_event.py>` CLI or the
  `scholar_pdf.acquisition` Python API (same PDF-kit domain service).
- **E2 — `nexus_pdf_extraction`** (`pdf_extraction`, `mcp_supported=false`,
  owner `nexus-scholar-org/scholar-pdf-kit`; separate from E1, neither broadens
  it): every call → `operation="extract_pdf"` refusal, before any engine
  import/read/write. Use instead: `{CLI:pdf} extract-run <config.json>
  --audit-logger <path-to-log_event.py>` CLI or the
  `scholar_pdf.extraction.PDFExtractionService` API. The legacy
  `scholar-pdf extract` / `scholar_pdf.extract` path is explicitly
  non-authoritative — never cite it as the alternative.
- **E3 — `nexus_rag_index`** (`rag_indexing`, `mcp_supported=false`, owner
  `nexus-scholar-org/scholar-rag-kit`; different owner/service from the PDF
  pair): every call → `operation="rag_index"` refusal, before any store open,
  directory read, or filesystem/audit I/O. The retired path (hard-coded
  CWD-relative `db_path`, silent `project.json` identity substitution, no
  parent/embedder/`PARTIAL`, free text) was non-authoritative and is removed,
  not kept. Use instead: the T-90 `{CLI:rag} index <docs_path>
  --parent-view … --journal … --workspace-root … --run-id … --created-at …
  --producer-version … --producer-commit … --embedder-provider …
  --embedder-model … --embedder-dimension …` CLI or the
  `scholar_rag.index_service.index_workspace(IndexServiceRequest)` API (same
  shared service). Retrieval over an existing index (#11, #12) is unaffected.

Conformance: `test_e1_acquired_document_boundary.py`,
`test_e2_extraction_boundary.py`, E3 lineage boundary suite.

## 4. Authoritative vs non-authoritative (do not conflate)

- `nexus_extract_pdf` (#7) is a **non-authoritative convenience**: verifies
  nothing (no checksum/E1 manifest/parent), identifies nothing (no
  `document_id`, no identity-addressed output, no sidecar); `title`/`doi`/
  `workspace_id` are path heuristics (stem text, filename DOI regex, `SCI-`
  directory segment). It emits no Contract artifact and claims none. Never cite
  its output as a verified extracted-text result; never write it into
  authoritative `extracted/<document_id>.md` or sidecar paths. The authority is
  #9's owning API/CLI.
- Synthesis "entailment" (#12: `VERIFIED ≥0.85 / AMBIGUOUS ≥0.50 /
  UNSUPPORTED`) is embedding-cosine similarity wording, **not** logical
  entailment and not verification — verify quotes with #17 (verbatim n-gram +
  char-window matching, `threshold=0.90`).
- No MCP surface exists for `extraction-schema` / `extraction-prompt` /
  `canon` / strict protocol surfaces — use the `scholar-protocol` CLI there.
  Absence of an MCP tool is not authorization to substitute another tool's
  output.

## 5. Agent guidelines

- **Tool selection**: lazy/eager MCP calls (`nexus_discover`, #11, #12,
  `recon_probe/distill/delta`) inside subagent loops — this kit is the intended
  front-door. Interactive terminal or a known-broken MCP path → the direct kit
  CLIs (`scholar-search`, `scholar-pdf`, `scholar-rag`, `scholar-graph`,
  `scholar-verify`, `scholar-protocol`).
- **Direct CLI fallbacks**: `{CLI:graph} build --input
  <ws>/literature/included.json` (real client, same as #14 builds); `{CLI:verify} <stream> --workspace <ws>` mirrors #17.
- **Screening contract**: #6 is heuristic screening that writes proposals
  only (`screening_proposals.json`), never a decision; the harness agent-in-the-loop batch handoff
  (`agent_screen.py` `batch_NNN.json` → `batch_NNN_decisions.json`) is a
  separate contract — do not mix its files with #16's reconciler inputs
  without checking shapes.
- **Absolute paths > defaults** (see §1): anything file-backed gets an explicit
  `<workspace>/…` path.
- **The assistant and the critic (#27–#31, M10c)**: on the researcher's
  drafts and workspaces, read freely and explain; suggest a change only with
  #30 and raise a problem only with #31. Nothing you send is applied: the
  researcher applies, edits or rejects each suggestion and dismisses each
  finding in the app. Never start a search or a harvest for the app's draft
  (`recon_probe`/`recon_delta` refuse its session id:
  `RECON_SESSION_IS_A_DRAFT`); never accept a corpus, decide a screening
  record or publish. Name your model in `model`. As a critic, report one
  finding per problem, at the most specific locator (the criterion, the
  concept's synonyms, the question), with a severity from §2 #31, and stay
  quiet on what is sound. M9d's tasks: synonyms (`task="synonyms"`, field
  `concepts[<name>].synonyms`), translation explanations (read
  `plan.providers[].cannot_express` and explain it), recall repair (read
  `recall`, propose the smallest change, `task="recall_repair"`). After
  genesis, suggest a search change on the workspace (`workspace_dir`,
  fields `core_concepts[<name>].synonyms`, `core_concepts`, `start_year`,
  `end_year`, `languages`); anything else is a finding. When the researcher
  applies one, the protocol's fingerprint moves and every other open
  suggestion on that workspace goes out of date: send one change at a time
  and read the workspace again before the next.

## 6. Sources, limits, deferred pointers

- Sources: `server.py` tool defs/docstrings (signatures above), `capabilities.py`
  registry + rejection messages, `scholar-agent --help` (25-line registry),
  `docs/kits_surface_matrix.md` (agent-kit section, E1/E2/E3 boundaries,
  findings 1–10), pin: see `{CONFIG}`.
- Limits kept, not erased: only `retraction` hits the network (#18);
  per-provider search exceptions are swallowed (empty ≠ error); `consensus`
  verdicts count studies; `scholar-verify-kit` is an undeclared MCP-side dep
  (shared-venv install hides it — bare `uv sync` of the kit alone breaks #17).
- Deferred (not fixed here — needs canonical-kit work, reported as
  `BLOCKED_CANONICAL_REPO` if pursued): any runtime change under `tools/`,
  pin bumps, or contract/fixture edits are out of scope for this doc refresh.
