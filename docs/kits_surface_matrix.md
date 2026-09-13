# Kit Surface Matrix — API · CLI · MCP

> **Status:** Live — generated 2026-09-13 by a full read-only sweep of all eight kits
> (one exploration agent per kit, evidence cited inline). This is the **agent-facing
> knowledge base** that backstops the `SKILL.md` files and the MCP tools.
> **Regenerate:** re-run the sweep when kit APIs/CLIs change; skill content mirrors this
> matrix and is synced to the plugin bundle by `scripts/sync_skills_bundle.py`.

## Purpose

One place that answers, for every kit: *what is the public API, what does the CLI
do, which MCP tools wrap it, what is silently broken/different, and what must an
agent know before driving it.* The `SKILL.md` files carry the operational subset;
this file carries the full evidence-backed map and the cross-cutting failure modes
that no single skill covers.

---

## Quick map

| Kit (package) | Public API anchor | CLI | MCP tool(s) | Harness role |
| :-- | :-- | :-- | :-- | :-- |
| search (`scholar_search`) | `SearchEngine`, `Deduplicator`, `DocumentVerifier`, `CitationChainer`, screening fns, `Exporter` | `scholar-search` (search/snowball/chain/import/dedup/verify/export/screen) | `nexus_discover`, `nexus_dedup`, `nexus_screen`, `nexus_screen_reconcile` | Phase-1 discovery/prepare (`compile_protocol_search`) |
| pdf (`scholar_pdf`) | `AsyncPDFDownloader`, `PyMuPDFEngine`/`DoclingEngine`/`GrobidEngine`, validators | `scholar-pdf` (download/ingest/extract) | `nexus_extract_pdf` (PyMuPDF only) | Phase-2 fulltext |
| bib (`scholar_bib`) | `BibParser`, `BibLinter`, `BibDeduplicator`, `BibResolver` | `scholar-bib` (lint/merge/dedup/resolve) | `nexus_bib_clean` (lint only) | bibliography hygiene |
| rag (`scholar_rag`) | `ScholarIndexer`, `ScholarRetriever`, `GroundedSynthesisEngine`, `ConsensusCartographer`, `MatrixExtractor` | `scholar-rag` (index/query/synthesize/consensus/matrix/stats) | `nexus_rag_index/query/synthesize`, `nexus_matrix_extract` | Phase-3 retrieval + synthesis |
| graph (`scholar_graph`) | `CitationGraphBuilder`, `GraphVisualizer` | `scholar-graph` (build/pagerank) | `nexus_graph_build` | Phase-3 knowledge-graph |
| protocol (`scholar_protocol`) | `ResearchProtocol`, `compile_protocol`, `canonical_json/fingerprint`, `validate_protocol`, `render_screening_criteria`, `build_extraction_model` | `scholar-protocol` (compile/validate/fingerprint/canon/render-criteria/extraction-schema/extraction-prompt) | `nexus_protocol_compile/validate/render_criteria` (+ matrix via rag) | Phase-0 protocol |
| agent (`scholar_agent`) | MCP server (18 tools) + harness-recon adapter | `scholar-agent` (MCP stdio server) | every `nexus_*` + `recon_probe/distill/delta` | MCP front-door |
| verify (`scholar_verify`) | `RetractionChecker`, open-science DAS/CAS, COI audit, QUADAS-2/PROBAST RoB, trust-context, `VerbatimClaimVerifier` | `scholar-verify` (retraction/open-science/coi/risk-of-bias/trust-context/all/verbatim-claims) | `nexus_verify_claims` (verbatim only) — Phase-4 streams are **CLI-only** | Phase-4 trust |

---

## Critical cross-cutting findings (read first)

These are the failure modes an agent or tool will hit. Each is a **tooling gap or a
latent bug**, with the working path in parentheses.

1. **MCP CWD-relative defaults land in `tools/scholar-agent-kit/`.** The server is
   launched `uv run --directory tools/scholar-agent-kit scholar-agent`, so bare
   `db_path="./chroma_db"`, `output_dir="./extracted"`, `output_path="./deduped.json"`,
   `output_dir="./literature"` and `.cache/mcp/…` all resolve **inside the kit
   checkout**, not your workspace. (Always pass absolute workspace paths, e.g.
   `<ws>/chroma_db`, `<ws>/pdfs/`.)
2. **`nexus_graph_build` always produces 0-edge graphs.** It constructs
   `CitationGraphBuilder(http_client=None)`; every OpenAlex fetch fails and is
   swallowed to `None` → only fallback isolation nodes, uniform PageRank 1.0 —
   yet reports "N nodes, 0 edges" as success. (Use `uv run scholar-graph build
   --input <ws>/literature/included.json` — the CLI builds a real client.)
3. **`nexus_extract_pdf` drops all metadata.** Frontmatter contains only
   stem-derived `title` + `extraction_engine` + `extracted_at`; the kit's
   `metadata=` kwarg (workspace_id/doi/year/authors) is never passed. MCP-extracted
   files silently lose `doi` → downstream RAG DOI lookup and bib-enrichment degrade.
   (`engine=…` param is dead — always PyMuPDF.) Only the Python API can inject metadata.
4. **`nexus_bib_clean` is lint-only.** Name/docstring say "clean, standardize keys,
   and deduplicate" but it calls `lint(generate_keys=False)` — no key
   standardization, no dedup. (Run `uv run scholar-bib lint --generate-keys` +
   `dedup`/`merge --dedup` for the documented pipeline. Output defaults to
   **in-place overwrite**.)
5. **`nexus_protocol_validate` string mode skips cross-field rules.** Passing
   inline JSON only runs Pydantic structural validation; passing a **file path**
   runs the full rule set (`_check_cross_field`: duplicate IDs, date/pool
   coherence, RQ refs, warnings). No `--strict` surface. Errors return as
   `{"status": "INVALID", …}` JSON, not MCP failures.
6. **`nexus_verify_claims` cannot digest `scholar-rag` claims.json.** The tool
   reads `claim_id/workspace_id/study_id/evidence_quote`; `SynthesisClaim` emits
   `claim_text/citation_tokens/entailment_status/…` with **no `evidence_quote`** →
   every claim fails `MISSING_QUOTE`. The two "verification" concepts are unrelated
   (RAG entailment = embedding cosine; verify = verbatim quote matching). Only
   aggregate `metrics` are returned, per-claim verdicts are discarded.
7. **`nexus_rag_query` cannot do graph boosting.** Docstring advertises PageRank
   boosting but no `graph_source`/`alpha`/`beta` parameter exists; only `boost_doi`
   (seed term, default β=0.15) is reachable. Full hybrid retrieval needs the CLI
   `scholar-rag query --graph <graph.json> --alpha --beta`.
8. **`nexus_screen` bypasses the agent-in-the-loop PRISMA contract.** It runs
   heuristic screening in-process; `conflicts.json` and `prisma_report.json` are
   computed but **never written** (only included/excluded/md). Pairing it with
   `nexus_screen_reconcile` (which expects `batch_NNN_decisions*.json` files) is not
   natural. The harness's real screening pipeline is the `agent_screen.py` batch handoff.
9. **Harness orchestrator bugs (do not trust pipeline Stage 5/7/8/9 outputs):**
   provider *name strings* are passed to `SearchEngine` (expects provider instances)
   → search exceptions swallowed → empty `raw_search.json`; Stage 7/9 call
   `indexer.retriever` (no such attribute) → `AttributeError`; Stage 5 fabricates
   placeholder extraction text; Stage 8 mirrors the 0-edge graph bug; the console
   "Extract fulltext" action uses a non-existent `--input` flag on `scholar-pdf extract`.
   The reliable path is the kit CLIs/MCP tools directly, not `scholar-harness run` stages.
10. **Verify Phase-4 streams (retraction/open-science/coi/risk-of-bias/trust-context)
    are CLI-only.** No MCP tool wraps them; only `verbatim` is on MCP. The console
    exposes just `trust-context` as an action (`mcp_tool: None`). Agents must shell
    `uv run scholar-verify <stream> --workspace <ws>`.
11. *(fixed this sweep)* **`scholar-verify` CLI crashed on Python 3.14** —
    `cli.py:229` used `Optional[Path]` in a `typer` callback annotation while only
    importing `typing.Any`; with `from __future__ import annotations`, typer evaluates
    the string annotation → `NameError: name 'Optional' is not defined` on **every**
    subcommand, including `--help`. One-line import fix applied (`Optional`); the CLI
    now resolves and all 7 subcommands are reachable. Also note: the module docstring
    lists an `ingress` command that is not registered on the app.

---

## Per-kit surface

### scholar-search-kit
- **Public API (importable from root):** `SearchEngine(providers=None)` (defaults 6),
  `Deduplicator.deduplicate(docs) -> list[DocumentCluster]` (SCI-`%06d` ids),
  `DocumentVerifier`, `CitationChainer.chain(…)`, `evaluate_heuristic_screening`,
  `partition_screening_results`, `reconcile_multi_screener_decisions`,
  `batch_partition`, `generate_batch_screening_prompt`, `Exporter`, `compile_protocol_search`.
  ⚠ `from scholar_search import Query, Document, …` **fails** — they live in
  `scholar_search.models` (docs/skills that import them from root are wrong).
- **CLI:** search / snowball / chain / import / dedup / verify / export / screen.
  `screen` needs `--input` + `--protocol`; `dedup` has only `--output/--format`
  (no `--export/--csv-output`). `search` CLI default = 5 providers (no bioRxiv);
  protocol search default DBs = openalex/semanticscholar/crossref/arxiv.
- **MCP:** `nexus_discover` hardcodes 4 providers (no PubMed/bioRxiv), `dedup=True`
  forced, writes CWD-relative `.cache/mcp/discover_<slug>_<ts>.json`; `nexus_dedup`
  JSON-only; `nexus_screen` (see finding 8); `nexus_screen_reconcile` (screener-id
  keyed from file stem).
- **Knowledge:** env `SCHOLAR_MAILTO` (polite pool), `SCHOLAR_OPENALEX_KEY`,
  `SCHOLAR_S2_KEY`, `SCHOLAR_CACHE_DIR`; rate limits OA 10/s · CR 5/s · S2 1/s ·
  PubMed 3/s (arXiv/bioRxiv 1/s); client = httpx+hishel, 4 transport retries, 429→
  5 exponential retries, 30 s timeout, user-agent `scholar-search-kit/0.1.0 (mailto:…)`;
  dedup = PID tier → exact-normalized-title tier → fuzzy 0.97 / year±1 / first-author
  containment; verifier thresholds ≥0.90 bidirectional or ≥12-char containment
  (Crossref validate score > 40 + OpenAlex); snowball sandbox caps depth 5/500/2000,
  CLI `chain` defaults depth 1/200/500 backward; per-provider exceptions are
  **swallowed** (empty results ≠ error).

### scholar-pdf-kit
- **Public API:** `AsyncPDFDownloader(output_dir, use_smart_names, proxy_url, …)`
  (async `download_batch`/`process_doi`/`ingest_pdf`), `PyMuPDFEngine.extract_markdown
  (pdf, output_dir, metadata=None)`, `DoclingEngine`, `GrobidEngine(grobid_url)`,
  `is_valid_pdf`/`validate_pdf_structure`/`clean_invalid_pdf`, publisher direct-PDF
  + proxy-rewrite helpers.
- **CLI:** `download` (`--doi` repeatable / `--input` JSON, `--output`, `--smart-names`,
  `--export json|bibtex`, `--proxy*`, `--strict-validate`, `-c`) / `ingest` / `extract`
  (**positional** `pdf_path` — no `--input`; `--engine` accepts only **docling|grobid**;
  pymupdf is API/MCP only).
- **MCP:** `nexus_extract_pdf(pdf_path, output_dir="./extracted", engine="pymupdf")`
  — engine param dead, metadata dropped (finding 3).
- **Knowledge:** env `MAILTO`, `DOWNLOAD_DIR`, `MAX_CONCURRENT_DOWNLOADS`,
  `DOWNLOAD_TIMEOUT`, `PROXY_URL/PROXY_STYLE`, `PDF_STRUCTURAL_VALIDATION`,
  `ENABLE_PUBLISHER_DIRECT_PATTERNS` (no prefix); cascade = OpenAlex best_oa →
  Unpaywall → publisher direct-PDF (IEEE/Springer/arXiv patterns) → proxy rewrite;
  validation = ≥10 KB + `%PDF-` in first 1 KB + `%%EOF` in last 8 KB (+ optional
  encryption-tolerant pypdf gate); invalid files auto-deleted; frontmatter keys =
  `workspace_id|doi|title|authors|year|extraction_engine|extracted_at` (empty keys
  dropped); smart filename `{year}_{author}_{title}.pdf` (title ≤50 alnum); PDF bytes
  stream via aiohttp (Chrome UA) while metadata uses search-kit's httpx+hishel client;
  `import fitz` (PyMuPDF); `pyyaml` is an undeclared transitive dep; extraction
  writes a stub line on parse failure — "success" ≠ content.

### scholar-bib-kit
- **Public API:** `BibParser.load/save` (bibtexparser v2), `BibLinter.lint(lib,
  generate_keys=False)` — only **AuthorYear** key mode (no sequential mode);
  `BibDeduplicator.dedup` (cleaned-DOI match first, then cleaned-title; survivor =
  first occurrence, graft missing fields); `BibResolver.resolve_doi/search/entry/library`
  (async, Crossref `transform/application/x-bibtex`, replaces whole entry).
- **CLI:** lint/merge/dedup/resolve. **lint/dedup/resolve overwrite input in place**
  when `--output` omitted; `merge` default output = CWD `merged.bib`.
- **MCP:** `nexus_bib_clean` = in-place `lint` only (finding 4).
- **Knowledge:** bibtexparser **2.0.0b9** (beta); title brace-wrapping idempotent;
  dedup identity = case/punct-insensitive DOI then title (`attentionisallyouneed`);
  resolver silently swallows Crossref failures; DOI normalization only strips
  `https?://doi.org/`; `pydantic` declared-but-unused dep; Crossref polite client at
  10/s; `print()`-based output in resolve.

### scholar-rag-kit
- **Public API:** `MarkdownChunker` (AST headings, chunk id `chk-<docslug>-<secslug>-<NN>`,
  slug = first4 + md5[6] when doc_id > 8 chars — `min_chunk_chars` dead),
  `ScholarIndexer(db_path="./chroma_db", collection_name="scholar_docs")` with
  upsert (idempotent, but re-index ≠ rebuild), `ScholarRetriever.query(…, alpha=0.25,
  beta=0.15, graph_source=None, boost_dois=None)` (hybrid `cos + α·PR + β·seed`,
  over-fetch ×4 when boosting), `GroundedSynthesisEngine.synthesize/synthesize(
  …, llm_callable=None)` (deterministic bullets when no LLM; entailment thresholds
  VERIFIED ≥0.85 / AMBIGUOUS ≥0.50; lexical fallback 0.6/0.3), `ConsensusCartographer(
  threshold=0.30)` (verdicts from **study counts**), `MatrixExtractor(protocol…)`
  (dynamic dims via `build_extraction_model`, writes `synthesis_matrix.{json,csv,md}`).
- **CLI:** index/query/synthesize/consensus/matrix/stats; graph boost + alpha/beta
  only via CLI; consensus `--similarity` lexical|sentence-transformers.
- **MCP:** `nexus_rag_index` (dir input only; collection/embedder locked; journaling on),
  `nexus_rag_query` (no graph params, single boost_doi), `nexus_rag_synthesize`
  (rq_id default **"RQ1"**, no boost/llm), `nexus_matrix_extract` (db pinned to
  `<workspace_dir>/chroma_db` — mismatch with CWD-relative index default).
- **Knowledge:** embedder default `all-MiniLM-L6-v2` (HF download on first use;
  hermetic `mock` provider for CI); OPENAI provider needs `OPENAI_API_KEY`; no env for
  db path; sector categories `abstract_intro|methodology|results_empirical|
  discussion_limitations|other` via keyword classification; paradigm/study_design from
  **BibTeX only**; journal discovery walks up from data dir (indexer/synthesis) but
  from CWD (retriever); `scholar-protocol-kit` imported but **undeclared** dep;
  citation tokens `[<ws|paper_id|doi|filename>#<sec10>#<chunk_id>]`; claims.json has
  **no `evidence_quote`/`claim_id`** (finding 6); audit events `RAG_INDEX_BUILT`,
  `RAG_QUERY_RETRIEVED`, `SYNTHESIS_GENERATED`, `MATRIX_EXTRACTED`.

### scholar-graph-kit
- **Public API:** `CitationGraphBuilder(http_client)` (mandatory client — API-pinned;
  `build_graph` raises nothing, swallows fetch failures to None), `compute_pagerank(
  alpha=0.85)` (normalized to max 1.0, 4dp, lowercased keys), `export_json` (node-link
  + `"pagerank"` key), `GraphVisualizer(output_path).generate_html` (PyVis, mutates
  node attrs). `config.Settings` and `models.GraphNode/GraphEdge` are **dead**.
- **CLI:** `build --doi/-d (repeatable) | --input json; --output graph.html; 
  --json-output` (renders HTML **before** exporting JSON → CLI JSON includes PyVis
  `value`/`title` node keys), `pagerank <graph.json>` (needs the `pagerank` key).
  JSON always written even without `--json-output` (sidecar `graph.json`).
- **MCP:** `nexus_graph_build(input_path, output_html, json_output)` — 0-edge bug
  (finding 2); DOI precedence `doi` → `external_ids` (reverse of CLI).
- **Knowledge:** OpenAlex only, **no polite-pool mailto sent**; intra-pool edges only
  (source → referenced work in pool via wid→doi); **no co-citation logic exists**
  (prose claims are aspirational); no TF-based weighting (RAG does that); graph.json
  consumed by RAG retriever (reuses `pagerank` key or recomputes nx.pagerank α=0.85;
  blend α=0.25/β=0.15 differs from computation α); pyvis 0.3.2 `lib/` materializes in
  run CWD and the HTML is a hybrid (local bindings + **CDN vis.js**) — not offline;
  unbounded per-DOI concurrency; fallback nodes get `year=None`, `title="Study <doi>"`.

### scholar-protocol-kit
- **Public API:** `compile_protocol(IntentPacket) -> ResearchProtocol` (pure, zero
  LLM/network), `canonical_json` (declaration-order keys; nested dict keys sorted;
  arrays **not** sorted — reordering changes fingerprint), `canonical_fingerprint`
  (`sha256:<64hex>`), `validate_protocol` (structural + cross-field), `render_screening_criteria`
  (ScreeningCriteria.md), `build_extraction_model` (dynamic Pydantic), presets (5 playbooks).
- **CLI:** `compile <intent_path>` → canonical bytes to **stdout** (no `-i/-o/
  --fingerprint`); `render-criteria <path>` → stdout (no `-o`); validate/fingerprint/
  canon/extraction-schema/extraction-prompt. **Never writes files.**
- **MCP:** `nexus_protocol_compile` (path-or-JSON-string; returns `{status, protocol_id,
  fingerprint, protocol}` wrapper; **does not persist** — agent writes protocol.json),
  `nexus_protocol_validate` (file path = full validation; inline JSON = structural
  only; warnings dropped on valid), `nexus_protocol_render_criteria` (path-only, raw md).
  `extraction-schema`/`extraction-prompt`/`canon`/strict have no MCP surface.
- **Knowledge:** `created_at` pinned from `genesis_timestamp` (the one nondeterminism
  trap when hand-constructing); fingerprint = canonical content (formatting won't change
  it), comparable across compile/validate; golden `.sha256` fixtures gate serializer
  changes (preset/model changes need version bump); validator never touches
  `schemas/v1/protocol.schema.json` (derived artifact, CI-checked); errors fold into
  JSON strings, not MCP failures; matrix-extract validates only structurally.

### scholar-agent-kit (MCP front-door)
- **18 tools** (15 `nexus_*` + 3 `recon_*`) — NOT the 7 the skill documents; `--help`
  lists only 16 (omits `nexus_screen_reconcile`, `nexus_verify_claims`). Full inventory
  and signatures in `server.py` (tool list at lines 125-930); launch via `uv run
  --directory tools/scholar-agent-kit scholar-agent` (CWD = kit dir; no env/cwd in
  `mcp_config.json`).
- **Harness adapter:** `_harness_src()` walks up for `src/scholar_harness/recon/__init__.py`,
  honors `NEXUS_HARNESS_SRC`, injects into `sys.path` at import; `RECON_CACHE_ROOT =
  canonical_recon_root()` (= `NEXUS_RECON_ROOT` or `<repo>/.cache/inception_recon`);
  `RECON_SEARCH_FN = None` test seam threaded into every `ReconEngine(search_fn=…)`.
- **Return conventions:** machine JSON = protocol + reconcile + verify + recon tools;
  prose strings (success "Error:" prefixes) = the rest.
- **`nexus_verify_claims`** wraps `VerbatimClaimVerifier(threshold=0.90)` (verify kit),
  returns only `{status, metrics}` — schema mismatch documented in finding 6.
- **Bare `uv sync` of the kit would break** — `scholar_verify.verbatim` is imported but
  `scholar-verify-kit` is not a declared dep (shared-venv install hides it).

### scholar-verify-kit
- **Public API:** `RetractionChecker` (OpenAlex/Crossref, deterministic
  `flagged = OA is_retracted OR any Crossref update ∈ {retraction, expression-of-concern,
  correction, addendum, correction-addendum}`; sleeps `sleep_s` per record — 94 studies
  ≈ +19 s), open-science DAS/CAS `run` (regex + repo-host whitelist; missing extraction
  **dropped** by default), COI `run` (deterministic relabel of `no-statement`;
  `coi_chunk_1..8.json` must be contiguous or `SystemExit`), `risk_of_bias.run`
  (QUADAS-2/PROBAST L/?/H + n/a; worst-domain overall; conservative `?` for
  self-collected w/o docs), `build_trust_index`/`trust_level` (BLOCKED/WEAK/ADEQUATE/
  STRONG/UNVERIFIED ladder; any flag → BLOCKED; STRONG needs zero `?` + zero industry
  + ≥1 public+link), `VerbatimClaimVerifier` (verbatim — the only MCP-exposed part).
- **CLI:** retraction/open-science/coi/risk-of-bias/trust-context/all/verbatim-claims,
  all `--workspace/-w` (requires protocol.json or INDEX.md); `all` ≠ all (no
  trust-context/verbatim, no overwrite prompt); outputs `phase4/{retraction_status_check,
  open_science_regex_baseline, coi_audit, risk_of_bias, trust_consensus[_<rq>]}.{json,md}`
  with envelope `{run_metadata, summary, results}`.
- **MCP:** `nexus_verify_claims` (verbatim only). Phase-4 streams **CLI-only** (finding 10).
- **Knowledge:** only retraction hits the network (mailto `verification@nexus-scholar.example`);
  hermetic everything else; `10.48550` arXiv DOIs short-circuit Crossref (`_datacite`);
  RQ attribution = exact `(study_id, claim_text)` match; `_FLAG_REASON_SENSITIVE` dead
  constant (no sensitivity filtering — any flag blocks); 3 retries/exponential on
  `fetch_json`, clean misses `{"_status": 404|400|422}`; kit standalone (typer/rich/
  requests only); inputs `literature/extraction/merged/records.json`,
  `literature/included.json`, `phase4/_manifest.json`, `phase4/_agent_results/*`,
  `extracted/*.md`, `synthesis/consensus.json` + 4 phase4 JSONs.

---

## Cross-kit dependency graph

```text
scholar-search-kit ──http_client──► scholar-pdf-kit        (AcademicHttpClient)
                ├──http_client──► scholar-bib-kit          (resolver)
                ├──http_client──► scholar-graph-kit        (mandatory ctor arg)
                ├──SearchEngine─► scholar-agent-kit/recon  (ReconEngine.search_fn)
                │                 scholar_harness.recon
scholar-bib-kit ────────────────► (rag declares, unused in code)
scholar-protocol-kit ──build_extraction_model──► scholar-rag-kit (matrix, UNDECLARED dep)
scholar-protocol-kit ──────────► scholar-agent-kit (compile/validate/render)
scholar-rag-kit ────────────────► scholar-agent-kit (index/query/synthesize/matrix)
scholar-graph-kit ──graph.json──► scholar-rag-kit (CLI --graph consumption, workflow-level)
scholar-verify-kit ─verbatim────► scholar-agent-kit (nexus_verify_claims, UNDECLARED dep)
scholar-agent-kit ──sys.path──► scholar_harness.recon (harness adapter, NEXUS_HARNESS_SRC)
```

## Env vars & versions

| Scope | Variable (default) | Kit |
| :-- | :-- | :-- |
| Polite pool / keys | `SCHOLAR_MAILTO`, `SCHOLAR_OPENALEX_KEY`, `SCHOLAR_S2_KEY` | search |
| Cache | `SCHOLAR_CACHE_DIR` (`.cache`, hishel TTL 30d unused) | search |
| PDF | `MAILTO`, `DOWNLOAD_DIR`, `MAX_CONCURRENT_DOWNLOADS`, `DOWNLOAD_TIMEOUT`, `PROXY_URL`, `PROXY_STYLE`, `PDF_STRUCTURAL_VALIDATION`, `ENABLE_PUBLISHER_DIRECT_PATTERNS` | pdf |
| Embedder | `OPENAI_API_KEY` | rag |
| MCP/harness | `NEXUS_RECON_ROOT`, `NEXUS_HARNESS_SRC` | agent/harness |
| LLM screening | `GEMINI_API_KEY` | search (`LLMBatchScreener`) |

Known pins: protocol `1.0.0`; all other kits `0.1.0` (Phase-7 doc's `>=0.2.0`
requirement unsatisfiable today); bibtexparser `2.0.0b9` **beta**; chromadb `1.5.9`;
sentence-transformers `6.0.0`; networkx `3.6.1`; mcp `2.1.1` (agent kit);
pymupdf `1.28.2` (`import fitz`); docling `2.123.0` (only with `[extract]` extra);
`plugins.json` pins all kits to `default_rev: main` (no hashes).

## Keeping this fresh

- Re-run one exploration agent per kit when a kit bumps API/CLI surface; update this
  matrix, then the `SKILL.md` files, then `uv run python scripts/sync_skills_bundle.py`.
- Sweep provenance: 8 read-only explore agents, 2026-09-13, every claim file:line
  verified against kit sources and `tools/scholar-agent-kit/src/scholar_agent/server.py`.