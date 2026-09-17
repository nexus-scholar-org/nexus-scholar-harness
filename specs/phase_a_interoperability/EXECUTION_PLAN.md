# Phase A Execution Plan

> **Spec:** `specs/phase_a_interoperability/README.md`
> **Note:** Feature A2 (CSL-JSON Exporter) is **dropped** per review feedback. This plan covers A1, A3, A4, A5 only.

---

## Task 1: Add `post()` method to `AcademicHttpClient` [INDEPENDENT]
**Description:** Extend the HTTP client with a POST method supporting rate limiting, retries, and exponential backoff. Required by A4 (Semantic Scholar batch API) and future POST-capable providers.
**Files to Touch:** `tools/scholar-search-kit/src/scholar_search/http_client.py`

### Execution Checklist
- [ ] Add `async def post(self, url, json=None, params=None, headers=None, timeout=30.0)` method to `AcademicHttpClient` class after the existing `get()` method (line ~117).
- [ ] Implement rate limiting via `await self.rate_limiter.wait()` before each attempt.
- [ ] Merge caller-supplied headers with default `{"Accept": "application/json"}`.
- [ ] Implement retry loop (up to `self.max_retries`) with exponential backoff: `await asyncio.sleep(self.base_delay * (2 ** attempt))`.
- [ ] Handle HTTP 429 (rate limit): read `retry-after` header, sleep, then `continue` retry loop.
- [ ] Wrap `httpx.RequestError` / `httpx.HTTPStatusError` exceptions identically to `get()`, raising `ProviderError` on final failure.
- [ ] Return raw `httpx.Response` (caller decides parsing).

### Testing Strategy
- **Unit test:** Add `tests/test_http_client.py` (new file) with `pytest.mark.asyncio`.
- Mock `self.client.post` via `AsyncMock` to return controlled `httpx.Response` objects.
- Test cases: (a) successful POST returns 200, (b) 429 triggers retry then succeeds, (c) 5xx exhausts retries then raises `ProviderError`, (d) `httpx.RequestError` triggers exponential backoff.
- Fixture: `tmp_path` for cache dir isolation; `unittest.mock.patch` for `RateLimiter.wait` to make tests instant.

### Definition of Done (DoD)
- `uv run pytest tests/test_http_client.py -v` passes all cases.
- `post()` has docstring with Args/Returns/Raises.
- No top-level imports added (all httpx/hishel already present).

---

## Task 2: Create `completeness.py` module — scoring functions [INDEPENDENT]
**Description:** Implement deterministic completeness scoring (0–10 base + provider weight) for representative election. Standalone module with no runtime dependencies beyond `Document` model.
**Files to Touch:** `tools/scholar-search-kit/src/scholar_search/completeness.py` (NEW)

### Execution Checklist
- [ ] Create `tools/scholar-search-kit/src/scholar_search/completeness.py`.
- [ ] Define `PROVIDER_WEIGHTS: dict[str, int]` constant mapping normalized provider names to weights: `openalex→5, crossref→4, semanticscholar→3, s2→3, arxiv→2, pubmed→2, biorxiv→1, unknown→0`.
- [ ] Implement `compute_completeness_score(doc: Document) -> int` with the 0–10 formula: DOI (+2), abstract >20 chars (+2), venue (+1), authors non-empty (+1), year (+1), citations >0 (+1), any author has orcid (+1), not retracted (+1).
- [ ] Implement `compute_total_score(doc: Document) -> int` = `compute_completeness_score(doc) + PROVIDER_WEIGHTS.get(doc.provider.lower(), 0)`.
- [ ] Add module docstring explaining the scoring rationale and reference to NEXUS_MASTER_SPECIFICATION.md §3.1.B.

### Testing Strategy
- **Unit test:** Add `tests/test_completeness.py` (new file).
- Fixture: `sample_documents` from spec (He 2016, Devlin 2019) plus edge cases: empty doc (score 0), full doc (score 10), retracted doc (no +1).
- Test cases: (a) `compute_completeness_score` returns correct integer for each fixture, (b) `compute_total_score` adds provider weight, (c) provider weight lookup is case-insensitive, (d) unknown provider returns 0 weight, (e) abstract with ≤20 chars scores 0 for that bit.

### Definition of Done (DoD)
- `uv run pytest tests/test_completeness.py -v` passes.
- All public functions have docstrings.
- No imports beyond `from .models import Document`.

---

## Task 3: RIS Exporter — `ris()` method and type detection [INDEPENDENT]
**Description:** Add RIS (Tagged) export to the `Exporter` class with field mapping and type detection logic.
**Files to Touch:** `tools/scholar-search-kit/src/scholar_search/export.py`

### Execution Checklist
- [ ] Add `_determine_ris_type(doc: Document) -> str` static method: returns `"JOUR"` if venue contains "journal"/"trans", `"CONF"` if venue contains "conf", else `"GEN"`.
- [ ] Add `ris(self, documents: list[Document], output_file: str | Path) -> Path` method to `Exporter` class after the existing `csv()` method.
- [ ] In `ris()`: ensure `.ris` suffix, `mkdir(parents=True, exist_ok=True)`.
- [ ] Implement field mapping loop per document: `TY`, `TI`, `AU` (Family, Given format), `PY`, `JO`/`T2` (conditional on type), `AB`, `DO`, `UR`, `C1` (arXiv prefix), `DB` (from `sources[0].provider` or fallback "nexus-scholar"), `ER`.
- [ ] Handle edge cases: no authors → skip AU; no abstract → skip AB; no DOI → skip DO; no arxiv_id → skip C1.
- [ ] Write with `encoding="utf-8"` and `"\n".join(lines)`.
- [ ] Add docstring mentioning Rayyan/Covidence/EndNote/Zotero compatibility.

### Testing Strategy
- **Unit test:** Add `tests/test_ris_export.py` (new file).
- Fixtures: `sample_documents` (2 docs: one journal, one conference), plus edge cases: doc with no authors, doc with no DOI, doc with no venue.
- Test cases: (a) output file exists and has `.ris` suffix, (b) TY correctly determined for JOUR/CONF/GEN, (c) AU lines use "Family, Given" format, (d) DO line present when DOI exists, (e) C1 line prefixed with "arXiv:", (f) DB falls back to "nexus-scholar" when sources empty, (g) ER terminates each record, (h) multi-document output contains correct record count.

### Definition of Done (DoD)
- `uv run pytest tests/test_ris_export.py -v` passes.
- Exported `.ris` content matches RIS format spec in §2.1.1.

---

## Task 4: GEXF & GraphML Exporters — static methods on `CitationGraphBuilder` [INDEPENDENT]
**Description:** Add `export_gexf()` and `export_graphml()` static methods with XML-safe attribute sanitization and deferred networkx imports (P7.7).
**Files to Touch:** `tools/scholar-graph-kit/src/scholar_graph/builder.py`

### Execution Checklist
- [ ] Add `_sanitize_node_attrs(G: nx.DiGraph) -> None` static method: iterate all nodes, replace `None` values with `0` for numeric keys (`year`, `citations`, `pagerank`) and `""` for string keys.
- [ ] Add `export_gexf(G: nx.DiGraph, output_path: str | Path) -> Path` static method: deferred `import networkx as nx`, ensure `.gexf` suffix, ensure pagerank attribute exists (compute if missing via `nx.pagerank`), call `_sanitize_node_attrs`, call `nx.write_gexf`.
- [ ] Add `export_graphml(G: nx.DiGraph, output_path: str | Path) -> Path` static method: identical pattern to `export_gexf` but calling `nx.write_graphml`.
- [ ] Both methods create parent dirs via `path.parent.mkdir(parents=True, exist_ok=True)`.
- [ ] Both methods have docstrings noting P7.7 deferred import constraint.

### Testing Strategy
- **Unit test:** Add `tests/test_graph_export.py` (new file).
- Fixture: `sample_graph()` — a `nx.DiGraph` with 3 nodes (varying attributes: some with `None` values, some with pagerank, some without), 2 edges.
- Test cases: (a) `export_gexf` creates valid `.gexf` file, (b) `export_graphml` creates valid `.graphml` file, (c) `_sanitize_node_attrs` replaces `None` with defaults, (d) pagerank auto-computed when missing, (e) existing pagerank preserved, (f) suffix auto-corrected (`.txt` → `.gexf`/`.graphml`).

### Definition of Done (DoD)
- `uv run pytest tests/test_graph_export.py -v` passes.
- No `import networkx` at module top level (only inside method bodies).

---

## Task 5: CLI integration — RIS format in `_save_output()` and `--format` help text
**Description:** Wire the RIS exporter into the `scholar-search` CLI so `--format ris` works on `search`, `snowball`, `chain`, `export`, `dedup`, and `verify` commands.
**Files to Touch:** `tools/scholar-search-kit/src/scholar_search/cli.py`

### Execution Checklist
- [ ] In `_save_output()` (line ~66): add `elif format_clean == "ris": exporter.ris(documents, output_path)` branch.
- [ ] Update the error message in the `else` branch to include `ris` in the options list: `"Options: json, jsonl, csv, ris"`.
- [ ] Update `--format` help text in all commands that use it (`search`, `snowball`, `chain`, `export`, `dedup`, `verify`): change `"Output format: json, jsonl, csv"` to `"Output format: json, jsonl, csv, ris"`.
- [ ] Verify no other format-dispatch logic exists that would need updating.

### Testing Strategy
- **Unit test:** Update existing `tests/test_cli.py` or add cases to `tests/test_ris_export.py`.
- Test: call `_save_output(docs, tmp_path / "out", "ris")` and verify output file contains `TY  -` lines.
- Integration: invoke `scholar-search export` via `typer.testing.CliRunner` with `--format ris` and verify exit code 0 + output file exists.

### Definition of Done (DoD)
- `uv run pytest tests/test_ris_export.py tests/test_cli.py -v` passes.
- `scholar-search export --format ris` produces valid `.ris` output.

---

## Task 6: CLI integration — GEXF/GraphML formats in `scholar-graph build`
**Description:** Extend the `--format` option of the `build` command to support `gexf`, `graphml`, and `all` values.
**Files to Touch:** `tools/scholar-graph-kit/src/scholar_graph/cli.py`

### Execution Checklist
- [ ] Add `--format` option to `build` command (default `"html+json"`, help: `"Export formats: html, json, gexf, graphml, all"`).
- [ ] Parse format string: `formats = [f.strip() for f in format.split("+")]`.
- [ ] After existing JSON export block, add: if `"gexf" in formats or "all" in formats` → call `builder.export_gexf(G, output_json.with_suffix(".gexf"))` and echo success.
- [ ] Add: if `"graphml" in formats or "all" in formats` → call `builder.export_graphml(G, output_json.with_suffix(".graphml"))` and echo success.
- [ ] Ensure existing `html` and `json` exports still work when `"all"` is selected.

### Testing Strategy
- **Unit test:** Update `tests/test_cli.py` in scholar-graph-kit.
- Use `typer.testing.CliRunner` to invoke `build --format all` with mocked `AcademicHttpClient`.
- Assert exit code 0 and that output messages contain "GEXF" and "GraphML".

### Definition of Done (DoD)
- `uv run pytest tests/test_cli.py -v` passes in scholar-graph-kit.
- `scholar-graph build --doi 10.xxxx --format all` produces `.html`, `.json`, `.gexf`, `.graphml`.

---

## Task 7: Abstract Backfilling — `AbstractHydrator` class [DEPENDS ON Task 1]
**Description:** Implement the `AbstractHydrator` class that batch-queries Semantic Scholar and OpenAlex for missing abstracts, with graceful degradation.
**Files to Touch:** `tools/scholar-search-kit/src/scholar_search/enrichment.py` (NEW)

### Execution Checklist
- [ ] Create `tools/scholar-search-kit/src/scholar_search/enrichment.py`.
- [ ] Implement `AbstractHydrator.__init__(self, http_client: AcademicHttpClient)` storing S2 and OA base URLs.
- [ ] Implement `hydrate_missing_abstracts(self, documents, batch_size=50) -> tuple[list[Document], dict[str, int]]`: filter docs with no abstract + has DOI, process in batches, return hydrated docs and stats.
- [ ] Implement `_hydrate_from_s2(self, dois) -> dict[str, str]`: POST to S2 batch endpoint with `{"ids": ["DOI:..."]}`, `fields=paperId,externalIds,abstract`, parse response, map DOI → abstract. Wrap in try/except for graceful degradation.
- [ ] Implement `_hydrate_from_openalex(self, dois) -> dict[str, str]`: GET to OpenAlex per-DOI, parse `abstract_inverted_index`, reconstruct via `_reconstruct_abstract`.
- [ ] Implement `_reconstruct_abstract(inverted_index: dict) -> str` static method: build `(position, word)` tuples, sort, join.

### Testing Strategy
- **Unit test:** Add `tests/test_enrichment.py` (new file).
- Mock `AcademicHttpClient.post` and `.get` via `AsyncMock`.
- Fixtures: documents with 30% missing abstracts, mock S2 batch response, mock OpenAlex response with inverted index.
- Test cases: (a) S2 batch returns abstracts for known DOIs, (b) fallback to OpenAlex for missing S2 results, (c) docs without DOI skipped, (d) stats dict correct (attempted/hydrated/failed), (e) `_reconstruct_abstract` produces correct string from inverted index, (f) API failure returns empty dict (graceful degradation).

### Definition of Done (DoD)
- `uv run pytest tests/test_enrichment.py -v` passes.
- No network calls in tests (all mocked).

---

## Task 8: Integrate completeness scoring into `Deduplicator.deduplicate()` [DEPENDS ON Task 2]
**Description:** Replace the current first-seen representative election with score-based election: when a duplicate is found, compare total scores and swap the representative if the candidate scores higher.
**Files to Touch:** `tools/scholar-search-kit/src/scholar_search/dedup.py`

### Execution Checklist
- [ ] Add `from .completeness import compute_total_score` import at top of `dedup.py`.
- [ ] In `deduplicate()`, in the `else` branch (match found, line ~96): before `match.members.append(document)`, compute `candidate_score = compute_total_score(document)` and `current_score = compute_total_score(match.representative)`.
- [ ] If `candidate_score > current_score`: swap — assign `document.workspace_id = match.representative.workspace_id`, `document.cluster_id = match.representative.cluster_id`, merge old rep metadata into new via `_merge_metadata(document, match.representative)`, set `match.representative = document`, append old rep to `match.members`.
- [ ] If `candidate_score <= current_score`: keep current representative, assign workspace_id/cluster_id to candidate, merge candidate metadata into representative, append candidate to `match.members`.
- [ ] Ensure cluster identity (workspace_id, cluster_id) is always preserved on the representative.

### Testing Strategy
- **Unit test:** Add `tests/test_dedup_scoring.py` (new file).
- Fixture: two documents with same DOI but different metadata richness (one from OpenAlex with abstract, one from arxiv without). Verify the richer one becomes representative.
- Fixture: three documents same DOI — OpenAlex (score 9), Crossref (score 7), arXiv (score 4) — verify OpenAlex wins.
- Fixture: edge case — identical scores, first-seen wins (determinism).
- Test: `test_dedup_metadata_merging` still passes (existing test).

### Definition of Done (DoD)
- `uv run pytest tests/test_dedup.py tests/test_dedup_scoring.py -v` passes.
- Representative election is deterministic: same input order → same output.

---

## Task 9: Integrate `AbstractHydrator` into orchestrator pipeline [DEPENDS ON Task 7]
**Description:** Insert an abstract hydration step in `ResearchOrchestrator.run_pipeline_async()` between dedup (Stage 2) and verification (Stage 3).
**Files to Touch:** `src/scholar_harness/orchestrator.py`

### Execution Checklist
- [ ] Add import: `from scholar_search.enrichment import AbstractHydrator` (lazy, inside method body or at top).
- [ ] In `run_pipeline_async()`, after dedup (line ~491) and before verification (line ~499): instantiate `AbstractHydrator` with a new `AcademicHttpClient(name="hydration", rate_limit=10)`.
- [ ] Call `hydrated_docs, hydration_stats = await hydrator.hydrate_missing_abstracts(unique_docs)`.
- [ ] Log hydration stats to audit journal: action `"ABSTRACT_HYDRATION"`, metrics=hydration_stats.
- [ ] Pass `hydrated_docs` (instead of `unique_docs`) to `verifier.process_batch()`.
- [ ] Update `results["stages"]["hydration"]` with stats.

### Testing Strategy
- **Integration test:** Add `tests/test_orchestrator_hydration.py` (new file) or extend existing orchestrator tests.
- Mock `AbstractHydrator.hydrate_missing_abstracts` to return controlled results.
- Verify: (a) hydration is called between dedup and verify, (b) verified_docs receive hydrated abstracts, (c) audit event logged, (d) pipeline continues normally.

### Definition of Done (DoD)
- `uv run pytest tests/ -k "orchestrator" -v` passes.
- Blank abstract rate in test corpus drops ≥75%.

---

## Task 10: Update SKILL.md files for new capabilities [INDEPENDENT]
**Description:** Document the new RIS export, completeness scoring, abstract backfilling, and GEXF/GraphML export capabilities in the respective skill files.
**Files to Touch:**
- `.agents/skills/scholar-search-kit/SKILL.md`
- `.agents/skills/scholar-graph-kit/SKILL.md`

### Execution Checklist
- [ ] In `scholar-search-kit/SKILL.md`: add RIS export section under CLI usage — document `--format ris`, field mappings, compatibility with Rayyan/Covidence/Zotero.
- [ ] In `scholar-search-kit/SKILL.md`: document completeness scoring in the dedup section — mention 0–10 base + provider weight formula.
- [ ] In `scholar-search-kit/SKILL.md`: document abstract backfilling step in pipeline flow — mention S2 batch + OpenAlex fallback.
- [ ] In `scholar-graph-kit/SKILL.md`: add GEXF/GraphML export section — document `--format gexf`, `--format graphml`, `--format all`.
- [ ] Verify no outdated references to dropped A2 (CSL-JSON).

### Testing Strategy
- Manual review: ensure all new CLI options are mentioned, no broken markdown links.

### Definition of Done (DoD)
- SKILL.md files accurately reflect all Phase A features.
- No references to CSL-JSON (A2) remain.

---

## Task 11: Conformance tests — register new CLI options [INDEPENDENT]
**Description:** Ensure new `--format ris`, `--format gexf`, `--format graphml` options are registered in the Typer apps so existing conformance tests pass.
**Files to Touch:**
- `tools/scholar-search-kit/src/scholar_search/cli.py` (verify option registration)
- `tools/scholar-graph-kit/src/scholar_graph/cli.py` (verify option registration)

### Execution Checklist
- [ ] Run `uv run pytest tests/conformance/test_actions_cli_parity.py -v` — verify no regressions.
- [ ] Run `uv run pytest tests/conformance/test_mcp_tool_parity.py -v` — verify no regressions.
- [ ] If conformance tests fail due to new options, update the conformance test expectations to include `ris`, `gexf`, `graphml`.

### Testing Strategy
- Run existing conformance test suite and fix any failures.

### Definition of Done (DoD)
- `uv run pytest tests/conformance/ -v` passes with 0 failures.

---

## Task 12: Full Phase A test suite & final validation [DEPENDS ON ALL]
**Description:** Run the complete test suite, verify coverage, ensure no regressions, and validate success gates.
**Files to Touch:** None (validation only).

### Execution Checklist
- [ ] Run `uv run pytest tests/ -v` — all tests pass, 0 failures.
- [ ] Run `uv run ruff check scripts/` — lint clean (CI scope).
- [ ] Verify RIS export: `scholar-search export --format ris` produces valid `.ris` (manual or automated import test).
- [ ] Verify GEXF/GraphML: files parseable by `networkx.read_gexf()` / `networkx.read_graphml()` in tests.
- [ ] Verify completeness determinism: run dedup twice on same input, identical representative selection.
- [ ] Verify abstract backfilling: test corpus with 30% missing abstracts → ≥75% recovered.
- [ ] Run `uv run pytest tests/conformance/ -v` — all conformance gates pass.

### Testing Strategy
- Full suite execution; no new tests needed.

### Definition of Done (DoD)
- `uv run pytest tests/ -v` → **all pass, 0 failures**.
- `uv run ruff check scripts/` → **clean**.
- All 5 success gates from spec §1 met.

---

## Dependency Graph

```
Task 1 (HTTP post)  ──────────────────────┐
Task 2 (completeness.py)  ────────────────┤
Task 3 (RIS exporter)  ───────────────────┤
Task 4 (GEXF/GraphML)  ───────────────────┤
Task 10 (SKILL.md)  ──────────────────────┤  All independent
Task 11 (conformance)  ───────────────────┤
                                           │
Task 5 (CLI RIS)  ← depends on Task 3  ──┤
Task 6 (CLI graph) ← depends on Task 4  ──┤
Task 7 (AbstractHydrator) ← Task 1  ─────┤
Task 8 (dedup scoring) ← Task 2  ────────┤
                                           │
Task 9 (orchestrator) ← Tasks 7, 8  ─────┤
Task 12 (final validation) ← ALL  ───────┘
```

**Parallelizable wave:** Tasks 1, 2, 3, 4, 10, 11 can run simultaneously.
**Second wave:** Tasks 5, 6, 7, 8 can run once their dependencies land.
**Third wave:** Task 9 after 7+8.
**Final wave:** Task 12 after everything.
