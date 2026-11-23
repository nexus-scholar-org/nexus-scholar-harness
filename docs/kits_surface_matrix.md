# Kit Surface Matrix — API · CLI · MCP

> **Status:** Live — generated 2026-09-13 by a full read-only sweep of all eight kits; `scholar_bib` was removed in M5-slim (2026-11-05), and `scholar_rag` and `scholar_verify` on 2026-11-23 (H-remove-rag-verify), and `scholar_graph` the same day (H-remove-graph); findings below that name them are history, leaving four
> (one exploration agent per kit, evidence cited inline). This is the **agent-facing
> knowledge base** that backstops the `SKILL.md` files and the MCP tools.
> **Regenerate:** re-run the sweep when kit APIs/CLIs change; skill content mirrors this
> matrix and is synced to the plugin bundle by `scripts/sync_skills_bundle.py`.

> **Parked, not production (M5-slim, production plan §8).** The beta ships
> **screening** (import → prepare → screen → publish, with optional agent
> proposals). Reading PDFs (`scholar_pdf` `extract`, `extract-run`, and E1
> `acquire`; findings PDF-07/08) still works, but is parked: its `--help` says so
> first, its MCP tools say so in their descriptions, and the app labels any
> screen that shows it. Do not rely on it for a review. The citation graph
> (`scholar_graph`) was removed on 2026-11-23 (H-remove-graph).
>
> **The PDF kit's downloading is production** (decision 2026-11-21, M12a items 21
> and 27, K0): `scholar-pdf download` and `ingest` need a contact e-mail
> (`SCHOLAR_MAILTO`, or the kit's `MAILTO`; refused `MAILTO_NOT_SET` without),
> name the app in their User-Agent, request only the providers' own open-access
> locations (no guessed publisher URL), and refuse an institutional proxy.
>
> Since Part K of M12a (decision 2026-11-21, item 15): OpenAlex is asked only
> with `SCHOLAR_OPENALEX_KEY`, sent as its key (without it only Unpaywall is
> asked and the command says so; a 409 reads "the daily budget is spent"); a PDF
> address that answers 400, 401, 403, 404, 410 or 451 is asked once (a 5xx, a
> timeout, and a 429 whose `Retry-After` is at most 60 s are retried); a
> service's closed evidence (`is_oa: false`, `oa_status: closed`) overrides its
> `pdf_url`; every DOI asked gets one row in `download-manifest.jsonl` (in
> `--output`, or `--manifest PATH`) with the file, its SHA-256, the address
> asked, the redirects, the version, licence and host, each check by name, the
> access status and every PDF request; the command prints the PDF requests per
> DOI; with the `pdf` extra the first two pages are searched for the DOI and
> the title ("doi found", "title found", "not found: check it"; "not checked"
> without it), never blocking a file; `ingest` and a missing `--input` exit
> non-zero; the publisher patterns and `--smart-names` are removed; where hard
> links fail (FAT or exFAT drives) the file is copied. Check each stored file's
> identity before you use it.

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
| pdf (`scholar_pdf`) | `AsyncPDFDownloader`, `PyMuPDFEngine`/`DoclingEngine`/`GrobidEngine`, validators, **`scholar_pdf.acquisition`** (WP01-E1, parent-bound), **`scholar_pdf.extraction`** (WP01-E2, parent-bound) | `scholar-pdf` (download/ingest: **production** since K0; **acquire**/**extract-run**/extract: parked) | `nexus_extract_pdf` (PyMuPDF only, non-authoritative); acquisition: **UNSUPPORTED** (`pdf_acquisition`, `mcp_supported=false`); extraction: **UNSUPPORTED** (`pdf_extraction`, `mcp_supported=false`) | Phase-2 fulltext + E1 acquired-document + E2 extracted-text boundary |
| protocol (`scholar_protocol`) | `ResearchProtocol`, `compile_protocol`, `canonical_json/fingerprint`, `validate_protocol`, `render_screening_criteria`, `build_extraction_model` | `scholar-protocol` (compile/validate/fingerprint/canon/render-criteria/extraction-schema/extraction-prompt) | `nexus_protocol_compile/validate/render_criteria` | Phase-0 protocol |
| agent (`scholar_agent`) | MCP server (**22 tools**, incl. the five M10c `nexus_assistant_*` tools, `nexus_pdf_acquire` = declared-unsupported E1 boundary and `nexus_pdf_extraction` = declared-unsupported E2 boundary) + harness-recon adapter | `scholar-agent` (MCP stdio server) | every `nexus_*` + `recon_probe/distill/delta` | MCP front-door |
| harness (`scholar_harness`) | thin wrapper over the kit APIs (`orchestrator.py`; inception engine) | `nexus-scholar` (P7): `init` (P7.3 scaffold), `setup-mcp` (P7.4), `doctor` (P7.5 — kits import + pinned `default_rev` via `plugins.json`/wheel `nexus_scholar_pins.json`, `SCHOLAR_MAILTO` + model keys, skill resolvability, workspace layout; `--json` machine-readable with key values masked `***`; `--exit-code` opt-in, trips on FAIL only), `log` (P7.6 — `log event` single canonical event, `log batch` JSONL lenient-skip, `log sync-index` INDEX regeneration; all refresh INDEX + append to `audit/journal.jsonl` via the wheel-portable `workspace-manager` loader, workstation path-or-slug resolution with clean refusal); dev-venv script is `scholar-harness` (status/sync/run/export/inception) | — (agent kit owns the MCP front-door) | distribution / orchestration front-door |

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
   **RESOLVED:** relative path args now anchor to `NEXUS_MCP_WORKSPACE` when set,
   else to the harness repo root (nearest ancestor with `.git`) via `_resolve_path`,
   applied to every file/dir parameter across all `nexus_*` tools; `.cache/mcp`
   discover output and `db_path`/`output_dir`/`output_path`/`graph.json|html`/
   `literature` defaults no longer land in the kit checkout. Inline JSON payloads
   (protocol/intent/screener) and absolute paths pass through untouched. The recon
   cache was already CWD-independent via `canonical_recon_root()`/`NEXUS_RECON_ROOT`
   (regression tests in `tests/test_mcp_tools_graph.py`).
2. **`nexus_graph_build` always produces 0-edge graphs.** It constructs
   `CitationGraphBuilder(http_client=None)`; every OpenAlex fetch fails and is
   swallowed to `None` → only fallback isolation nodes, uniform PageRank 1.0 —
   yet reports "N nodes, 0 edges" as success. (Use `uv run scholar-graph build
   --input <ws>/literature/included.json` — the CLI builds a real client.)
   **RESOLVED:** the MCP tool now builds `AcademicHttpClient(name="openalex-graph",
   rate_limit=10)` exactly like the CLI; DOI extraction also accepts `results`/`items`
   dict payloads and errors out on empty input. Regression test:
   `tests/test_mcp_tools_graph.py::test_nexus_graph_build_uses_real_http_client`.
3. **`nexus_extract_pdf` drops all metadata.** Frontmatter contains only
   stem-derived `title` + `extraction_engine` + `extracted_at`; the kit's
   `metadata=` kwarg (workspace_id/doi/year/authors) is never passed. MCP-extracted
   files silently lose `doi` → downstream RAG DOI lookup and bib-enrichment degrade.
   (`engine=…` param is dead — always PyMuPDF.) Only the Python API can inject metadata.
   **RESOLVED:** the tool now derives `title`/`doi`/`workspace_id` from the PDF path
   (`doi` via a DOI pattern on the stem, `workspace_id` via `SCI-x` segments) and
   passes them through `metadata=`; `engine=` now routes to `docling`/`grobid`
   (both fall back to PyMuPDF, which still receives the metadata). Regression tests:
   `tests/test_mcp_tools_graph.py::test_nexus_extract_pdf_*`.
4. **`nexus_bib_clean`** was removed with `scholar_bib` in M5-slim (its dedup merged distinct works; see `docs/assessment/kit-bib.md`).
5. **`nexus_protocol_validate` string mode skips cross-field rules.** Passing
   inline JSON only runs Pydantic structural validation; passing a **file path**
   runs the full rule set (`_check_cross_field`: duplicate IDs, date/pool
   coherence, RQ refs, warnings). No `--strict` surface. Errors return as
   `{"status": "INVALID", …}` JSON, not MCP failures.
   **RESOLVED:** inline-JSON mode now runs the same structural + cross-field rule
   set as file mode (`ResearchProtocol.model_validate` + `_check_cross_field`),
   and both modes share identical response formatting (verified by a parity test
   in `tests/test_mcp_tools_graph.py`).
6. **`nexus_verify_claims` cannot digest `scholar-rag` claims.json.** The tool
   reads `claim_id/workspace_id/study_id/evidence_quote`; `SynthesisClaim` emits
   `claim_text/citation_tokens/entailment_status/…` with **no `evidence_quote`** →
   every claim fails `MISSING_QUOTE`. The two "verification" concepts are unrelated
   (RAG entailment = embedding cosine; verify = verbatim quote matching). Only
   aggregate `metrics` are returned, per-claim verdicts are discarded.
   **RESOLVED:** the tool now accepts either a bare array or `{"claims": [...]}`
   (SynthesisClaim shape), falls back to `claim_text` as the quote to verify,
   returns per-claim verdicts, a `failures_by_reason` breakdown, and surfaces the
   RAG `entailment_status` alongside each verbatim verdict (regression tests in
   `tests/test_mcp_tools_graph.py`).
7. **`nexus_rag_query` cannot do graph boosting.** Docstring advertises PageRank
   boosting but no `graph_source`/`alpha`/`beta` parameter exists; only `boost_doi`
   (seed term, default β=0.15) is reachable. Full hybrid retrieval needs the CLI
   `scholar-rag query --graph <graph.json> --alpha --beta`.
   **RESOLVED:** `nexus_rag_query` now accepts `graph_source` (as exported by
   `nexus_graph_build`) plus `alpha` (default 0.25) and `beta` (default 0.15) and
   passes them to `ScholarRetriever.query`, matching the CLI
   (`CosineSim + alpha*PageRank + beta*seed`). Regression tests in
   `tests/test_mcp_tools_graph.py`.
8. **`nexus_screen` bypasses the agent-in-the-loop PRISMA contract.** It runs
    heuristic screening in-process; `conflicts.json` and `prisma_report.json` are
    computed but **never written** (only included/excluded/md). Pairing it with
    `nexus_screen_reconcile` (which expects `batch_NNN_decisions*.json` files) is not
    natural. The harness's real screening pipeline is the `agent_screen.py` batch handoff.
    **RESOLVED:** the tool now also writes `conflicts.json` and `prisma_report.json`
    (dataclass dump of `PrismaFlowReport`) alongside included/excluded, so flagged
    borderline docs and the flow counts are persisted for downstream audit
    (regression tests in `tests/test_mcp_tools_graph.py`).
9. **Harness orchestrator bugs (do not trust pipeline Stage 5/7/8/9 outputs):**
   provider *name strings* are passed to `SearchEngine` (expects provider instances)
   → search exceptions swallowed → empty `raw_search.json`; Stage 7/9 call
   `indexer.retriever` (no such attribute) → `AttributeError`; Stage 5 fabricates
   placeholder extraction text; Stage 8 mirrors the 0-edge graph bug; the console
   "Extract fulltext" action uses a non-existent `--input` flag on `scholar-pdf extract`.
   The reliable path is the kit CLIs/MCP tools directly, not `scholar-harness run` stages.
   **RESOLVED:** Stage 1 provider resolution (`_PROVIDER_MAP`/`_resolve_providers`)
   and the console `extract --input` flag were already fixed in the PR-#4 sweep
   (`c67705f`); the remaining stages are now honest in `run_pipeline_async` — Stages
   5–9 gate on `literature/included.json` (missing → each `SKIPPED`, status
   `PENDING_AGENT_REVIEW`, audit `PIPELINE_RUN_PAUSED_FOR_SCREENING`, early return);
   Stage 5 does real PyMuPDF extraction of located PDFs (or a metadata-frontmatter-only
   `.md` with verbatim abstract, `extraction_engine: "metadata"`, never invented
   Methodology/Results/Limitations); Stages 7/9 bind a real `ScholarRetriever`
   (`db_path=chroma_dir, collection_name, embedder_kwargs` from the indexer);
   Stage 8 builds the graph with `AcademicHttpClient(name="openalex-graph")` and an
   empty `nx.DiGraph()` when no DOIs exist. Hermetic regression tests in
   `tests/test_orchestrator_fidelity.py`.
10. **Verify Phase-4 streams (retraction/open-science/coi/risk-of-bias/trust-context)
    are CLI-only.** No MCP tool wraps them; only `verbatim` is on MCP. The console
    exposes just `trust-context` as an action (`mcp_tool: None`). Agents must shell
    `uv run scholar-verify <stream> --workspace <ws>`.
    **RESOLVED:** `nexus_verify_phase4(workspace_dir, stream="all", sleep_s=0.2,
    skip_retraction=True, rq_id=None)` wraps the same thin CLI helpers
    (`_merged_records/_load/_write/_manifest`) and module functions, writes
    `<ws>/phase4/<name>.{json,md}` mirrors of each stream, and returns the written
    paths. `retraction` is network-bound (OpenAlex/Crossref) so `skip_retraction`
    defaults True; `trust-context`/`all` skip gracefully when no `synthesis/consensus.json`
    exists. Regression tests in `tests/test_mcp_tools_graph.py`.
11. *(fixed this sweep)* **`scholar-verify` CLI crashed on Python 3.14** —
    `cli.py:229` used `Optional[Path]` in a `typer` callback annotation while only
    importing `typing.Any`; with `from __future__ import annotations`, typer evaluates
    the string annotation → `NameError: name 'Optional' is not defined` on **every**
    subcommand, including `--help`. One-line import fix applied (`Optional`); the CLI
    now resolves and all 7 subcommands are reachable. Also note: the module docstring
    lists an `ingress` command that is not registered on the app.
12. **WP01-E1 acquired-document boundary: acquisition is API/CLI-only, and the MCP gap
    is *declared*, not silent.** `nexus_pdf_acquire` is a registered MCP tool that
    refuses rather than a tool that is missing, so the boundary is observable.
    (Use `uv run scholar-pdf acquire <config.json> --audit-logger
    <path-to-log_event.py>` or the
    `scholar_pdf.acquisition` Python API; both route through the same public
    `scholar-pdf-kit` domain service.) Full declaration in the
    *WP01-E1 acquired-document boundary* section below.

---

## Per-kit surface

### scholar-search-kit
- **Re-checked 2026-11-10** against `main` and [`docs/kits/search/PROVIDERS_2026-11.md`](kits/search/PROVIDERS_2026-11.md) (the provider reference: limits, what the code sends, hardening candidates). The bullets below were corrected where they had drifted.
- **Public API (importable from root):** `SearchEngine(providers=None)` (the one default set, `models.DEFAULT_DATABASES`: openalex, semanticscholar, crossref, arxiv; M3h-b-resilience),
  `Deduplicator.deduplicate(docs) -> list[DocumentCluster]` (SCI-`%06d` ids),
  `DocumentVerifier`, `CitationChainer.chain(…)`, `evaluate_heuristic_screening`,
  `partition_screening_results`, `reconcile_multi_screener_decisions`,
  `batch_partition`, `generate_batch_screening_prompt`, `Exporter`, `compile_protocol_search`.
  ⚠ `from scholar_search import Query, Document, …` **fails** — they live in
  `scholar_search.models` (docs/skills that import them from root are wrong).
- **CLI:** search / snowball / chain / import / dedup / verify / export / screen.
  `screen` needs `--input` + `--protocol`; `dedup` has only `--output/--format`
  (no `--export/--csv-output`). `search` CLI default = 5 providers (no bioRxiv,
  `cli.py:195-201`); protocol search default DBs = openalex/semanticscholar/crossref/arxiv
  (`protocol_adapter.py:81-84`, `scholar_protocol/models.py:126-129`; the CLI's
  protocol path falls back to the same four, `cli.py:187-193`).
  **One default set since M3h-b-resilience:** the engine, the plan, the browser
  plan, the protocol adapter, the CLI, recon and MCP `nexus_discover` read
  `scholar_search.models.DEFAULT_DATABASES` (the four above; the protocol model and
  presets hold the same list, kept equal by a test). The choice of the four is a
  proposed decision (`docs/decisions.md` 2026-11-18 item 1).
- **Known bug, PubMed `[ab]`:** `providers/pubmed.py:33` maps the abstract field to
  `[ab]`, which is not a PubMed field tag; PubMed silently searches all fields and the
  leg's executed query still shows `[ab]`. `[tiab]` is the planned fix. Not fixed.
- **MCP:** `nexus_discover` hardcodes 4 providers (no PubMed/bioRxiv, `scholar_agent/server.py:510-515`), `dedup=True`
  forced, writes CWD-relative `.cache/mcp/discover_<slug>_<ts>.json`; `nexus_dedup`
  JSON-only; `nexus_screen` (see finding 8); `nexus_screen_reconcile` (screener-id
  keyed from file stem).
- **Knowledge:** env `SCHOLAR_MAILTO` (required: no default, a live search refuses
  `MAILTO_NOT_SET`, `config.py:12-17`, `engine.py:35-44`), `SCHOLAR_OPENALEX_KEY`
  (required in practice: OpenAlex made keys mandatory on 2026-02-13; keyless calls share
  a small per-IP daily budget and, per the OpenAlex docs, cursor paging past page one answers 401; the code
  still labels the key optional, `config.py:20-22`, and still sends `mailto`, which
  OpenAlex no longer uses), `SCHOLAR_S2_KEY`, `SCHOLAR_CACHE_DIR`, `SCHOLAR_HTTP_CACHE`;
  rate limits OA 10/s · CR 5/s · S2 1/s · PubMed 3/s (arXiv/bioRxiv 1/s).
  **Provider limits now below ours:** Crossref list requests are 3/s polite, 1/s
  public (since 2026-07-21; `config.py:46-48` sends 5/s); arXiv asks for one request
  every 3 s. OpenAlex `per_page` max is 100 (200 deprecated; `openalex.py:160, 266, 297`
  ask for 200). Client = httpx+hishel, 4 transport retries, 429/5xx →
  3 retries with backoff (`http_client.py:60, 105-130`), 30 s timeout, user-agent
  `nexus-scholar/<installed version> (mailto:…)` (`http_client.user_agent`, M3h-b-resilience);
  shared per-provider budgets (Crossref list 3/s and single-record 10/s polite,
  arXiv one request per 3 s, Semantic Scholar `SCHOLAR_RATE_LIMIT_S2`), lowered by
  `x-rate-limit-*` headers; a 4xx answer to a POST is not retried;
  dedup = PID tier → exact-normalized-title tier → fuzzy 0.97 / year±1 / first-author
  containment; verifier thresholds ≥0.90 bidirectional or ≥12-char containment
  (Crossref validate score > 40 + OpenAlex); snowball sandbox caps depth 5/500/2000,
  CLI `chain` defaults depth 1/200/500 backward. `SearchEngine.snowball_forward/backward`
  take an optional `limit` (M3g): the harness's citation chase (`scholar_harness.pipeline.citation_chase`,
  CLI `nexus-scholar chase`, routes `/api/v1/discovery/chase/*`) calls them per seed, OpenAlex then
  Semantic Scholar, with a forward cap of 500 and no MCP tool yet. A provider failure is recorded on
  its search leg with `error_code` (`PROVIDER_RATE_LIMITED`, `PROVIDER_TIMEOUT`,
  `PROVIDER_UNAVAILABLE`, `PROVIDER_REFUSED`; `engine.py:55-75, 172-175`) since M3b-api,
  rather than swallowed.

### scholar-pdf-kit
- **Public API:** `AsyncPDFDownloader(output_dir, proxy_url, …, manifest_path=None)`
  (async `download_batch`/`process_doi(session, client, doi, *, title, study_id)`/
  `ingest_pdf(client, path, doi, *, study_id)`; `DownloadResult` carries `outcome`,
  `open_copy`, `lookups`, `attempts` (each PDF request: address, host, status or
  error, retry, final address, redirects, content type, checks), `request_count`,
  `request_hosts()`, `source_url`, `route`, `access_status`, `identity`, `size`,
  `sha256`, `study_id`), `scholar_pdf.manifest` (one JSON line per DOI,
  `scholar-pdf-download-manifest-v1`), `scholar_pdf.identity.check_identity`,
  `PyMuPDFEngine.extract_markdown(pdf, output_dir, metadata=None)`, `DoclingEngine`,
  `GrobidEngine(grobid_url)`, `is_valid_pdf`/`pdf_checks`/`validate_pdf_structure`/
  `clean_invalid_pdf`, the parked proxy-rewrite helpers (the publisher direct-PDF
  patterns are removed, Part K item 3).
- **CLI:** `download` (`--doi` repeatable / `--input` JSON list (a missing file is a
  usage error, exit 2), `--output`, `--manifest PATH` (default
  `download-manifest.jsonl` in `--output`), `--export json|bibtex` (one entry per DOI,
  written atomically), `--proxy*` (refused, `PROXY_REFUSED`), `--strict-validate`, `-c`;
  exit codes: 0 every DOI has its file; 3 a lookup failed (run again later); 1 a listed
  address gave no PDF, or another failure; 4 open access but no direct PDF address
  listed; 5 no open copy listed; it prints the PDF requests per DOI) /
  `ingest` (`--manifest`, `--study-id`; exit 1 when nothing is stored) (both production
  since K0, decision 2026-11-21, M12a items 21 and 27, repaired in Part K: a contact
  e-mail required, `MAILTO_NOT_SET` without; the app's own User-Agent; OpenAlex only
  with `SCHOLAR_OPENALEX_KEY`; no guessed publisher URL; no proxy) / `extract`
  (**positional** `pdf_path` — no `--input`; `--engine` accepts only **docling|grobid**;
  pymupdf is API/MCP only).
- **MCP:** `nexus_extract_pdf(pdf_path, output_dir="./extracted", engine="pymupdf")`
  — engine param dead, metadata dropped (finding 3). PDF **acquisition** is
  `UNSUPPORTED` on MCP — see the *WP01-E1 acquired-document boundary* section. PDF
  **extraction** is `UNSUPPORTED` on MCP — see the *WP01-E2 extracted-text boundary*
  section.
- **Acquisition (WP01-E1):** `scholar_pdf.acquisition` API + `scholar-pdf acquire`
  CLI; typed models in `scholar_pdf.acquisition_models`; parent binding in
  `scholar_pdf.contract_parents`.
- **Extraction (WP01-E2):** `scholar_pdf.extraction.PDFExtractionService` API +
  `scholar-pdf extract-run` CLI (parent-bound; `extract` remains as the legacy,
  non-parent-bound raw-path convenience); typed models in
  `scholar_pdf.extraction_models`; candidate builder in
  `scholar_pdf.contract_candidate`.
- **Knowledge:** env `SCHOLAR_MAILTO` (read first) or `MAILTO` (required, no default),
  `DOWNLOAD_DIR`, `MAX_CONCURRENT_DOWNLOADS`, `DOWNLOAD_TIMEOUT`,
  `PROXY_URL/PROXY_STYLE` (refused by `download`/`ingest`), `PDF_STRUCTURAL_VALIDATION`,
  `ENABLE_PUBLISHER_DIRECT_PATTERNS` (the patterns are removed; `true` is still refused,
  `PUBLISHER_PATTERNS_REFUSED`; no prefix), `SCHOLAR_OPENALEX_KEY` (OpenAlex is asked
  only with it; a 409 is "the daily budget is spent"); lookup =
  every open location OpenAlex lists (`best_oa_location`, `primary_location`,
  `locations`) and Unpaywall lists (`oa_locations`), both services asked once for
  every DOI when the key is set (Unpaywall only without it); a service's closed
  evidence overrides its `pdf_url`; best version first (published, accepted,
  submitted), at most three addresses tried, only a provider's own direct PDF
  address requested, never a landing page (H-pdf-resolver-locations,
  `scholar_pdf.open_copies`); User-Agent `nexus-scholar/<version> (mailto:…)`;
  retries only for a connection error, a timeout, a 5xx or a 429 with
  `Retry-After` ≤ 60 s (PDF-06); access status from the location that gave the
  bytes (`VERIFIED_OPEN_ACCESS`; the parked gateway `INSTITUTIONAL_ACCESS`; `ingest`
  `USER_PROVIDED`);
  validation = each check named (`pdf_header` in first 1 KB, `pdf_trailer` in last
  8 KB, `size_floor` ≥10 KB reported as a size floor, optional encryption-tolerant
  pypdf `structure`); invalid files never stored; files `DOC-<sha256[:32]>.pdf`,
  published by hard link or, where links fail, an exclusive-create copy (PDF-03);
  identity on the first two pages with the `pdf` extra (PDF-22); frontmatter keys =
  `workspace_id|doi|title|authors|year|extraction_engine|extracted_at` (empty keys
  dropped); PDF bytes
  stream via aiohttp (the app's user agent) while metadata uses search-kit's httpx client without its disk cache (the lookup addresses carry the OpenAlex key and the e-mail; M12a Part K);
  `import fitz` (PyMuPDF); `pyyaml` is an undeclared transitive dep; extraction
  writes a stub line on parse failure — "success" ≠ content.

### WP01-E1 acquired-document boundary

Normative spec: `docs/architecture/wp01/evidence-boundaries.md`
(E1, §4.7 for the MCP boundary; §10.2 `E1-NEG-030`/`044`/`047`).

**Supported surfaces — API/CLI only.**

| Surface | Surface artifact | Status |
| :-- | :-- | :-- |
| API | `scholar_pdf.acquisition` (typed request/outcome models in `scholar_pdf.acquisition_models`; parent binding in `scholar_pdf.contract_parents`) | **supported** |
| CLI | `uv run scholar-pdf acquire <config.json> --audit-logger <path-to-log_event.py>` (serializable `AcquisitionRunConfig` → standard operation envelope) | **supported** |
| MCP | `nexus_pdf_acquire` → capability `pdf_acquisition` | **`UNSUPPORTED_CAPABILITY`** |

Declared facts (all harness-enforced by
`tests/conformance/test_e1_acquired_document_boundary.py`, offline + deterministic):

- **MCP declares `pdf_acquisition` with `mcp_supported=false`.** The declaration lives
  in `scholar_agent.capabilities` as an immutable `CapabilityDeclaration`; the owning
  surfaces are `("API", "CLI")` and the canonical owner is
  `nexus-scholar-org/scholar-pdf-kit`.
- **Stable rejection.** Every acquisition-shaped MCP call returns the standard
  operation envelope with `operation=acquire_pdf`, `status=FAILED`, `artifacts=[]`, and
  exactly one error with the **stable** code `UNSUPPORTED_CAPABILITY` and
  `retryable=false`. Retrying a declared boundary cannot succeed, so it is never
  retryable. The rejection is unconditional and pre-validation: no run identity is
  echoed, because fabricating one would be worse than omitting it. The envelope uses
  operation-envelope field vocabulary and is **not** a Contract v1 `OperationOutcome`.
- **Zero I/O.** The rejection happens before any provider transport, temporary or
  final file creation, manifest construction, or audit-success append. The envelope is
  produced by pure functions over the immutable declaration, so the zero-I/O property
  is structural rather than merely asserted.
- **No parity claim.** This is a declared *unsupported difference* between surfaces. The
  MCP surface must never be described as semantically equivalent to, or a substitute
  for, the API/CLI acquisition path.
- **The kit-owned manifest is not a registry type.** `pdf_acquisition_manifest`
  (`pdf-acquisition-manifest-v1`, `ACQ-<32hex>`) is published atomically and
  deterministically, bound to accepted `corpus_snapshot` + `screening_decisions`
  parents — but the **frozen** Contract v1 acceptance/chain registries reject it as
  `UNSUPPORTED_ARTIFACT_TYPE` and never fabricate a registry entry or an
  `artifacts/pdf_acquisition_manifest/` directory for it. The harness registries stay
  frozen at the six Contract v1 types; the harness does **not** absorb the kit type.
- **Sync/packaging drift is a hard fail.** Canonical commit ↔ vendored tree ↔
  full-SHA `plugins.json` pin ↔ generated metapackage pin must agree in both
  directions; `tests/conformance/fixtures/e1_vendored/*.json` records the vendored
  `(mode, blob, path)` rows at the merged E1 commits
  (`scholar-pdf-kit` `858911f…`, `scholar-agent-kit` `6050e0c…`).

### WP01-E2 extracted-text boundary

Normative spec: `docs/architecture/wp01/evidence-boundaries.md`
(E2, §4.7 for the MCP boundary; §10.2 `E2-NEG-021`/`022`/`023`/`025`/`035`/`036`/`037`/`045`).

**Supported surfaces — API/CLI only.**

| Surface | Surface artifact | Status |
| :-- | :-- | :-- |
| API | `scholar_pdf.extraction.PDFExtractionService` (typed request/outcome models in `scholar_pdf.extraction_models`; record projections in `scholar_pdf.contract_candidate`) | **supported** |
| CLI | `uv run scholar-pdf extract-run <config.json> --audit-logger <path-to-log_event.py>` (serializable run config → standard operation envelope) | **supported** |
| MCP | `nexus_pdf_extraction` → capability `pdf_extraction` | **`UNSUPPORTED_CAPABILITY`** |

Declared facts (all harness-enforced by
`tests/conformance/test_e2_extraction_boundary.py`, offline + deterministic):

- **MCP declares `pdf_extraction` with `mcp_supported=false`.** The declaration lives
  in `scholar_agent.capabilities` as an immutable `CapabilityDeclaration`; the owning
  surfaces are `("API", "CLI")` and the canonical owner is
  `nexus-scholar-org/scholar-pdf-kit`.
- **Stable rejection.** Every extraction-shaped MCP call returns the standard
  operation envelope with `operation=extract_pdf`, `status=FAILED`, `artifacts=[]`, and
  exactly one error with the **stable** code `UNSUPPORTED_CAPABILITY` and
  `retryable=false`. Retrying a declared boundary cannot succeed, so it is never
  retryable. The rejection is unconditional and pre-validation: no run identity is
  echoed, because fabricating one would be worse than omitting it. The envelope uses
  operation-envelope field vocabulary and is **not** a Contract v1 `OperationOutcome`.
- **Zero I/O.** The rejection happens before any engine execution, extracted-text
  write, sidecar construction, Contract artifact, or audit-success append. The
  boundary module imports no PDF kit and no filesystem/network capability, and the
  envelope is produced by pure functions over the immutable declaration, so the
  zero-I/O property is structural rather than merely asserted.
- **No parity claim.** This is a declared *unsupported difference* between surfaces. The
  MCP surface must never be described as semantically equivalent to, or a substitute
  for, the API/CLI extraction path.
- **Parent-bound and deterministic.** Every request binds **exactly one**
  already-accepted Contract v1 parent — `screening_decisions` — with the corpus bound
  by `corpus_fingerprint` as a transitive ancestor through the screening chain (unlike
  E1's acquisition request, which really does carry both `corpus_snapshot` and
  `screening_decisions`), and the run publishes a
  `pdf-extraction-manifest-v1` sidecar plus a `document_manifest` Contract v1
  **candidate** stamped `contract_acceptance="not_performed_by_kit"`. A candidate is
  non-authoritative: the harness adapter
  (`scholar_harness.extraction_adapter.accept_extraction_candidate`) is the single
  surface that can turn it into an accepted artifact, bound to the accepted
  `screening_decisions` parent.
- **The kit-owned sidecar is not a registry type.** `pdf_extraction_manifest`
  (`pdf-extraction-manifest-v1`, `EXT-<32hex>`) is kit-owned. Passing it to the
  **frozen** Contract v1 acceptance/chain registries is rejected as
  `UNSUPPORTED_ARTIFACT_TYPE`, and **no registry entry is fabricated** — the harness
  registries stay frozen at the six Contract v1 types, because the kit emits the
  existing `document_manifest` rather than adding a seventh.
- **Cross-repository drift is a hard fail.** Canonical commit ↔ vendored tree ↔
  full-SHA `plugins.json` pin ↔ generated metapackage pin must agree, and the imported
  `scholar_pdf` / `scholar_agent` packages must resolve inside `tools/<kit>/src` rather
  than from some other install. The pins at the E2 commits are `scholar-pdf-kit`
  `6ec6e3b…` and `scholar-agent-kit` `deebfad9…`.
- **Behavioral proofs live in the kits.** Engine selection, content-status
  truthfulness, fallback recording, sidecar commit, and premature-publication
  atomicity are proven by the canonical kit suites; a green harness run is **not**
  evidence that extraction works.

### scholar-bib-kit
Removed in M5-slim (2026-11-05): the harness never used it, and its dedup and resolver could silently damage a `.bib` file (`docs/assessment/kit-bib.md`, BIB-01 to BIB-03).

### scholar-graph-kit
Removed on 2026-11-23 (H-remove-graph): the citation graph was parked, no product path used it, and it alone brought `networkx`, `pyvis` and `scipy` into the base install. Restore it from `9af17212`.

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
  `nexus_protocol_validate` (file path or inline JSON — both run the full structural +
  cross-field rule set; warnings dropped on valid), `nexus_protocol_render_criteria` (path-only, raw md).
  `extraction-schema`/`extraction-prompt`/`canon`/strict have no MCP surface.
- **Knowledge:** `created_at` pinned from `genesis_timestamp` (the one nondeterminism
  trap when hand-constructing); fingerprint = canonical content (formatting won't change
  it), comparable across compile/validate; golden `.sha256` fixtures gate serializer
  changes (preset/model changes need version bump); validator never touches
  `schemas/v1/protocol.schema.json` (derived artifact, CI-checked); errors fold into
  JSON strings, not MCP failures.

### scholar-agent-kit (MCP front-door)
- **22 tools** (19 `nexus_*` + 3 `recon_*`; since M10c the five `nexus_assistant_*` tools: read the app's drafts and workspaces, add a proposal or a finding, never apply one; H-remove-graph removed the two graph tools); `--help` lists all 22 (listing parity enforced
  by `tests/conformance/test_mcp_tool_parity.py`). Full inventory and signatures in
  `server.py` (tool list at lines 203-1782); launch via `uv run
  --directory tools/scholar-agent-kit scholar-agent` (CWD = kit dir; no env/cwd in
  `mcp_config.json`).
- **Declared unsupported capabilities (WP01-E1, WP01-E2):** two registered tools refuse
  rather than go missing, so both boundaries are observable.
  - `nexus_pdf_acquire` is registered but declares `pdf_acquisition` with
    `mcp_supported=false` in `scholar_agent.capabilities`; every acquisition-shaped call
    returns `operation="acquire_pdf"`, `status="FAILED"`, `artifacts=[]`, and one
    non-retryable `UNSUPPORTED_CAPABILITY` error with **zero I/O** (no provider
    transport, no temp/final file, no manifest, no audit-success append). The owning
    surfaces are the PDF kit's `scholar_pdf.acquisition` API and `scholar-pdf acquire`
    CLI. See the *WP01-E1 acquired-document boundary* section below.
  - `nexus_pdf_extraction` is registered but declares `pdf_extraction` with
    `mcp_supported=false`; every extraction-shaped call returns
    `operation="extract_pdf"`, `status="FAILED"`, `artifacts=[]`, and one non-retryable
    `UNSUPPORTED_CAPABILITY` error with **zero I/O** (no engine execution, no extracted
    text, no sidecar, no Contract artifact, no audit-success append). The owning surfaces
    are the PDF kit's `scholar_pdf.extraction.PDFExtractionService` API and
    `scholar-pdf extract-run` CLI. See the *WP01-E2 extracted-text boundary* section
    below.
- **Harness adapter (HCM-05 adopted, canonical kit `50c0b3f`):** the `recon_*`
  tools drive ONLY `scholar_harness.recon.adapter v1.0` (`make_engine` /
  `distill_terms` / `merge_lexicon` / `default_lexicon` / `pool_gate` /
  `topic_gate` / `run_followups`) bound by `_ensure_harness_recon_loaded()`
  via a plain guarded import -- zero discovery (`_harness_src`,
  `NEXUS_HARNESS_SRC`, `sys.path` mutation, `find_spec` all absent).
  `RECON_CACHE_ROOT` resolves via `_recon_adapter.resolve_cache_root()`
  (= `NEXUS_RECON_ROOT` or `<repo>/.cache/inception_recon`);
  `RECON_SEARCH_FN = None` test seam threaded read-only into `make_engine`
  (probe + delta) and `run_followups` (delta). Adapter-unavailable answers
  the typed `{status: error, cache_key: None}` envelope, never `TypeError`.
  Year-window honesty: MCP `start_year` defaults to 2020, engine/adapter to
  2000 -- parity needs an explicit shared window.
- **Return conventions:** machine JSON = protocol + reconcile + recon + screening + assistant tools;
  prose strings (success "Error:" prefixes) = the rest.

## Cross-kit dependency graph

```text
scholar-search-kit ──http_client──► scholar-pdf-kit        (AcademicHttpClient)
                ├──SearchEngine─► scholar-agent-kit/recon  (adapter make_engine search_fn)
                │                 scholar_harness.recon.adapter
scholar-protocol-kit ──────────► scholar-agent-kit (compile/validate/render)
scholar-agent-kit ──adapter import──► scholar_harness.recon.adapter (guarded, no sys.path)
```

## Env vars & versions

| Scope | Variable (default) | Kit |
| :-- | :-- | :-- |
| Polite pool / keys | `SCHOLAR_MAILTO` (required, no default), `SCHOLAR_OPENALEX_KEY` (required by OpenAlex since 2026-02-13; the code still calls it optional), `SCHOLAR_S2_KEY`. No NCBI key setting exists. | search |
| Cache | `SCHOLAR_CACHE_DIR` (`.cache`, hishel TTL 30d unused) | search |
| PDF | `SCHOLAR_MAILTO` or `MAILTO` (required since K0), `DOWNLOAD_DIR`, `MAX_CONCURRENT_DOWNLOADS`, `DOWNLOAD_TIMEOUT`, `PROXY_URL`, `PROXY_STYLE` (refused by `download`/`ingest`), `PDF_STRUCTURAL_VALIDATION`, `ENABLE_PUBLISHER_DIRECT_PATTERNS` (default off, `true` refused) | pdf |
| MCP/harness | `NEXUS_RECON_ROOT`, `NEXUS_SKILLS_SRC`, `NEXUS_MCP_CONFIG_HOME` (P7.4 `setup-mcp` config root override, mirrors `NEXUS_RECON_ROOT`) | agent/harness |
| LLM screening | `GEMINI_API_KEY` | search (`LLMBatchScreener`) |

Known pins (2026-11-10): there are no per-kit versions any more; every package ships in the one `nexus-scholar` wheel, version `1.1.0b6` (`pyproject.toml:7`). `.agents/plugins/nexus-scholar/plugins.json` carries no `default_rev` pins, so the `default_rev` sentence below is history. Third-party pins as last swept (2026-09-13, not re-checked): bibtexparser `2.0.0b9` **beta**; chromadb `1.5.9`;
sentence-transformers `6.0.0`; networkx `3.6.1`; mcp `2.1.1` (agent kit);
pymupdf `1.28.2` (`import fitz`); docling `2.123.0` (only with `[extract]` extra);
`plugins.json` lists all 7 kits to `default_rev` full commit SHAs (freshness enforced by
`tests/conformance/test_count_freshness.py`); `nexus-scholar doctor` (P7.5) reports
importability + that pinned rev from the repo `plugins.json` (wheel fallback: the bundled
`nexus_scholar_pins.json`).

## Keeping this fresh

- Re-run one exploration agent per kit when a kit bumps API/CLI surface; update this
  matrix, then the `SKILL.md` files, then `uv run python scripts/sync_skills_bundle.py`.
- Sweep provenance: 8 read-only explore agents, 2026-09-13, every claim file:line
  verified against kit sources and `tools/scholar-agent-kit/src/scholar_agent/server.py`.