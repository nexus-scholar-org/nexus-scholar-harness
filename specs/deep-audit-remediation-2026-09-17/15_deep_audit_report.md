# Deep Architecture Audit: Nexus Scholar Harness

I completed a read-only audit of the harness under `src/` and assigned a separate reviewer to each of the eight toolkits. No files were modified, and the existing untracked files were preserved.

## Executive conclusion

The project has a sound high-level decomposition:

```text
Protocol → Search → Dedup/Verify → Human screening
         → PDF/Extraction → RAG/Matrix/Synthesis
         → Graph → Phase-4 verification
```

The main weakness is not the overall architecture—it is contract integrity between layers.

The most consequential current problems are:

1. The console’s five built-in pipelines validate successfully but are not executable.
2. RAG confuses corpus identity with study identity, collapsing multiple papers into one study.
3. RAG generates invented methodology defaults when evidence is absent.
4. MCP’s pipeline tool accepts `query` and `skip_stages` but does not honor them operationally.
5. Protocol compilation permits cross-field-invalid protocols.
6. Search and BibTeX deduplication both fail on transitive identifier bridges.
7. PDF “strict validation” is not applied to downloaded PDFs.
8. Graph coupling and hybrid modes crash.
9. Phase-4 trust logic can fail to block a retracted paper.
10. Documentation and operational skills have substantial drift from current source.

The system is promising, but I would not yet characterize the complete automated path as scientifically reliable without the P0 fixes below.

---

## Harness architecture

The harness currently contains four overlapping orchestration surfaces:

- The monolithic research workflow in [orchestrator.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py:484).
- The configurable DAG executor in [pipeline_executor.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/pipeline_executor.py:296).
- The FastAPI console and job runner in [console/serve.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/console/serve.py:30).
- The inception/recon subsystem under [inception](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/inception) and [recon](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/recon).

Supporting boundaries include:

- Agent-in-the-loop screening under [screening](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/screening).
- Workspace/audit state synchronization.
- MCP setup and environment diagnosis.
- Export integrations for Zotero, Obsidian, LaTeX/Typst, and pipeline scripts.

This is no longer a strictly “thin” harness. It contains substantial workflow, UI, persistence, scheduling, recon, screening, and provenance logic. That is not inherently wrong, but the package description and architectural documentation should acknowledge it.

## Critical harness findings

### P0 — Built-in pipelines are structurally valid but operationally broken

All five built-in templates start discovery using:

```python
["scholar-search", "run"]
```

For example, [pipelines.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/console/api/pipelines.py:100) uses a command that does not exist. The real command is `scholar-search search`.

The validator nevertheless reports every template as valid because it validates graph shape and interpolation, not the CLI contract.

Further incompatibilities exist in [build_command](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/pipeline_executor.py:178):

- Positional arguments are always rendered as `--name value`.
- Boolean switches become `--strict-validate true`, although Typer commonly expects a flag with no value.
- List values receive one flag followed by multiple tokens rather than repeated option flags.
- Declared output paths are not automatically passed to commands.

This means the console dry-run is currently a structural preview, not an executable-contract validation.

### P0 — Stale screening output can bypass a newly prepared review

The orchestrator always regenerates screening batches with `force=True` at [orchestrator.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py:646), but then only tests whether an `included.json` file exists at [orchestrator.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py:672).

A stale `included.json` from an earlier corpus therefore allows stages 5–9 to proceed immediately against obsolete screening decisions. Neither the included corpus nor decision files are bound to the current verified-corpus fingerprint.

This is a scientific provenance failure, not merely an idempotency issue.

### P1 — Invalid graph references can crash validation

The validator detects unknown edge sources but still calls `_toposort`. `_toposort` performs `adj[src].append(dst)` without guarding an unknown source at [pipelines.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/console/api/pipelines.py:416). I reproduced a `KeyError` with an unknown source node.

Invalid user input should produce a validation error, never a server exception.

### P1 — Audit events are weaker than the repository’s stated contract

The orchestrator constructs event IDs using Python’s process-randomized `hash()` and marks every event `SUCCESS` at [orchestrator.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py:857).

This creates several problems:

- IDs are not reproducible across processes.
- The status cannot represent partial, failed, skipped, or pending work.
- Appends are not protected against concurrent writers.
- The harness contains multiple independent audit-writing implementations.

Audit generation should be consolidated behind one canonical append-and-sync API.

### P1 — Resource lifecycle is incomplete

The search engine is closed only after a successful search at [orchestrator.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py:518). Verification and graph clients also lack reliable cleanup in this path.

Use async context managers or `try/finally` around every external client.

---

# Toolkit findings

## 1. scholar-search-kit

Validation: 151 tests passed.

Strong points:

- Clear provider abstraction.
- Normalized document model.
- Good breadth across six providers.
- Bounded citation chaining and useful screening functions.

Critical findings:

- Package-root exports are broken: names appear in `__all__` but are not imported in [__init__.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/__init__.py:25).
- Deduplication cannot union two existing clusters joined by a later DOI/arXiv bridge in [dedup.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/dedup.py:57).
- Provider exceptions are swallowed in [engine.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-search-kit/src/scholar_search/engine.py:50), making “provider outage” indistinguishable from “zero papers.”
- Document verification replaces records and loses lineage metadata.
- `max_results` is effectively per provider, not a global corpus limit.
- JSON round-trips discard provenance, OA locations, topics, and raw data.
- Documented GET retry and persistent-cache behavior are not implemented.

## 2. scholar-pdf-kit

Validation: 43 tests passed.

Critical findings:

- `--strict-validate` is passed into the downloader but not applied to normal downloads in [downloader.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-pdf-kit/src/scholar_pdf/downloader.py:106).
- Successful Docling extraction drops YAML frontmatter and supplied metadata in [extract.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-pdf-kit/src/scholar_pdf/extract.py:95).
- PyMuPDF failures produce a successful-looking stub Markdown artifact at [extract.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-pdf-kit/src/scholar_pdf/extract.py:85).
- Institutional gateway rewriting is conflated with aiohttp forward-proxy transport.
- Strict ingest failure leaves the copied invalid file behind.
- Downloads are written directly to their destination without atomic replacement or a response-size cap.
- PyYAML is imported but not declared directly.

## 3. scholar-bib-kit

Validation: only two tests exist; both passed.

Critical findings:

- Documentation describes nonexistent classes and a nonexistent `scholar-bib fix` command.
- Deduplication has the same non-transitive identity problem as search-kit.
- Resolver accepts the first Crossref result without score, title, author, or year verification in [resolver.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-bib-kit/src/scholar_bib/resolver.py:27).
- Resolution clears original fields before replacing them, dropping curated metadata.
- Network failures are swallowed while the CLI still reports success.
- The HTTP client is never closed.
- Default in-place writes are not atomic.
- Distinct entries with the same citation key can survive.

## 4. scholar-rag-kit

Validation: 64 tests passed.

This toolkit contains the most important scientific-integrity defect.

### Corpus identity is used as study identity

The indexer places the same `workspace_id` on every paper at [indexer.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/indexer.py:217). Downstream code prefers it over DOI or filename:

- Citation tokens: [retriever.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/retriever.py:123)
- Synthesis claims: [synthesis.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/synthesis.py:197)
- Matrix grouping: [matrix.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/matrix.py:203)

The harness supplies the project slug as that shared ID at [orchestrator.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py:756). Consequently, multiple papers may collapse into one “study,” contaminating matrices, citation attribution, consensus counts, and downstream trust analysis.

Other serious findings:

- Standard matrices fabricate absent values such as “Design Science / Empirical,” “Standard Corpus,” and “Accuracy / F1” in [synthesis.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/synthesis.py:362).
- “Entailment verification” is embedding similarity, not logical entailment.
- Re-indexing shorter documents leaves obsolete chunks in the vector store.
- `scholar-protocol-kit` and `httpx` are used but not properly declared.
- Audit-journal discovery depends on process CWD.
- `min_chunk_chars` is dead configuration.
- Consensus mutates caller-owned claims.

## 5. scholar-graph-kit

Validation: 77 passed, one genuine test failure caused by stale expected CLI text.

Critical findings:

- `--mode coupling` crashes because CLI passes `min_jaccard` to an API expecting `min_overlap`.
- `--mode hybrid` crashes because CLI passes `alpha` to an API expecting different weight parameters.
- Co-citation/coupling transformations discard titles, years, citations, and sometimes entire isolate nodes.
- The “Louvain” command actually runs greedy modularity and ignores `seed`.
- Fetch and PageRank exceptions are converted into plausible-looking isolated or uniform graphs.
- `numpy` and `pydantic-settings` are undeclared.
- A missing `--input` file can exit successfully as “No DOIs.”
- Documentation describes a substantially different API.

## 6. scholar-protocol-kit

Validation: 134 tests passed, with four Windows subprocess decoding warnings.

Critical findings:

- Valid protocol files return `INVALID` through MCP because JSON text is passed directly to `ResearchProtocol.model_validate` in [server.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-agent-kit/src/scholar_agent/server.py:230).
- `compile_protocol()` performs structural validation but does not apply the cross-field rules. I confirmed that a criterion referencing nonexistent `RQ999` compiles successfully.
- `golden_seeds` exists in `SearchStrategy` but is absent from the intent/compiler path, so supplied seeds are silently discarded.
- Numeric extraction dimensions compile to string fields in [extraction.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-protocol-kit/src/scholar_protocol/extraction.py:31).
- Models silently ignore extra fields, allowing misspelled protocol fields to disappear.
- The PRISMA score mixes protocol readiness with post-execution conditions.

## 7. scholar-agent-kit

Validation: 27 passed, one genuine failure for protocol path validation.

Critical findings:

- `nexus_pipeline_run(query, skip_stages)` ignores `query`; skipped stages are executed and mutated, then merely removed from the returned dictionary in [server.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-agent-kit/src/scholar_agent/server.py:513).
- `scholar_verify` is eagerly imported but is not a declared dependency.
- `--workspace` sets the recon-root environment variable after the global recon cache path has already been calculated.
- LLM screening falls back on any exception to heuristic decisions but returns success without recording the downgrade.
- Calibration utilities exist but do not gate MCP screening.
- Grobid extraction does not preserve the metadata claimed by the skill.
- Response contracts alternate between structured JSON and prose `"Error: ..."` strings.
- Tool counts and several warnings in the skill/surface matrix are stale.

## 8. scholar-verify-kit

Targeted toolkit, MCP, CLI, and parity tests passed; two were skipped.

Critical findings:

- The `verbatim-claims` command calls `re.search` in [cli.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-verify-kit/src/scholar_verify/cli.py:247) but `re` is never imported (imports end at `cli.py:22`), so the command raises `NameError` at runtime.
- Retraction-only evidence can produce `UNVERIFIED` rather than `BLOCKED`, because a study is treated as “present” only when RoB or COI data exists in [trust_context.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-verify-kit/src/scholar_verify/trust_context.py:153).
- `"No data available"` is misclassified as a positive data-availability statement.
- An unrelated repository URL anywhere in a paper can upgrade both data and code availability to `public+link`.
- `--dry-run` still performs real OpenAlex/Crossref calls and sleeps; it only suppresses file output.
- CLI `all` and MCP `all` run different stream sets.
- Corrections/addenda are described as low severity but currently block trust exactly like a retraction.
- Direct CLI/MCP Phase-4 runs do not append the required workspace audit event or synchronize project state.

---

## Test-state interpretation

Observed validation:

- Harness run: 445 passed, 5 skipped, one shared-temp setup collision.
- The allegedly failing harness test passed when rerun with an isolated temp directory.
- Toolkit tests passed except:
  - one graph CLI message expectation;
  - one agent-kit protocol-path validation failure.
- Parallel agents repeatedly collided on the repository-wide fixed `tests_temp` path. This is a test-infrastructure concurrency problem worth fixing.

The high pass count demonstrates strong happy-path coverage. It does not invalidate the findings: most defects live at cross-package boundaries, failure semantics, provenance rules, or untested CLI modes.

## Recommended repair order

1. Establish canonical IDs: `workspace_id` for corpus, `study_id` for paper, `chunk_id` for evidence.
2. Remove fabricated RAG matrix defaults and weaken “verified entailment” terminology.
3. Repair built-in DAG templates and make validation verify actual CLI signatures.
4. Fingerprint screening inputs/decisions/included outputs so stale screening cannot pass the gate.
5. Fix MCP pipeline `query` and true stage-skipping semantics.
6. Enforce cross-field protocol validation during compilation and preserve `golden_seeds`.
7. Fix transitive deduplication in search and BibTeX using connected components or union-find.
8. Enforce PDF strict validation and explicit extraction-failure states.
9. Repair graph coupling/hybrid modes and preserve metadata.
10. Fix retraction-only trust coverage and open-science negation/link association.
11. Consolidate audit logging and structured result envelopes.
12. Add clean-install tests for every kit and regenerate all skills/API documentation from the live surfaces.

The best first implementation slice is the identity/provenance boundary. Until that is fixed, downstream matrix, consensus, trust, and paper-facing results can be internally consistent while still being attributed to the wrong study.


=====================================================
Completed the read-only `scholar-search-kit` audit and sent the parent agent a line-specific report.

Key confirmed issues:

- Broken package-root exports; `from scholar_search import *` raises `AttributeError`.
- Deduplication does not union clusters connected later by a multi-identifier bridge.
- Provider failures are swallowed, making outages indistinguishable from zero-result searches.
- Documented GET retry and persistent-cache behavior is not implemented.
- Verification replaces records and loses lineage metadata; the harness compensates incompletely.
- Search limits are per provider, despite being described as global.
- JSON/JSONL export-import cycles discard provenance, topics, OA locations, and raw data.
- Client cleanup is not exception-safe in several CLI and harness paths.

Validation: all 151 toolkit tests passed, but the identified contract and failure-mode cases are largely untested.

=====================================================
Completed the independent `scholar-pdf-kit` audit and sent the full evidence-backed report to the parent agent.

Key result: 43/43 targeted tests passed, but the audit confirmed several contract-level issues, led by:

- `--strict-validate` not being applied to downloaded PDFs.
- Successful Docling extraction dropping metadata/frontmatter.
- PyMuPDF silently turning extraction errors into successful-looking stub files.
- Institutional gateway URLs being incorrectly treated as forward proxies.
- Undeclared direct PyYAML dependency.
- Material README and surface-matrix drift.

No files were modified.
=====================================================
Completed the read-only `scholar-bib-kit` audit and sent the parent a detailed evidence report.

Key findings:

- Targeted tests pass, but there are only two shallow tests.
- Shipped tutorial/API documentation describes nonexistent commands and classes.
- Deduplication has a reproduced non-transitive identity bug.
- Crossref resolution can replace entries using an unverified first search result.
- Resolution destructively drops locally curated fields.
- The HTTP client is never closed, and network failures are silently reported as success.
- Harness documentation is stale: the current MCP cleaner now generates keys and deduplicates.
- Recommended priorities are documentation repair, conservative metadata resolution, connected-component deduplication, proper async lifecycle, atomic writes, and comprehensive tests.

=====================================================
Completed a read-only deep audit of `tools/scholar-graph-kit` and sent the full evidence-backed report to the parent agent.

Key findings:

- 77 tests pass; 1 fails due to stale expected CLI output.
- `--mode coupling` and `--mode hybrid` are confirmed broken by invalid keyword arguments.
- Graph transformations discard paper metadata and sometimes nodes.
- “Louvain” clustering actually uses greedy modularity and ignores `seed`.
- `numpy` and `pydantic-settings` are used but undeclared.
- Error swallowing can turn OpenAlex or PageRank failures into misleading successful-looking graphs.
- API reference, tutorial, skill guidance, and surface matrix contain substantial drift.
- Harness and MCP integration now use real HTTP clients, but the documentation still describes the former MCP zero-edge bug.
- Prioritized P0–P2 recommendations and exact file/line evidence were delivered.
=====================================================
Scholar RAG Kit audit — read-only.

Validation: `uv run pytest tools/scholar-rag-kit/tests -q` → **64 passed**, one third-party ChromaDB deprecation warning, 40.56s.

## Architecture and surfaces

The kit contains:

- Structural Markdown chunking: `chunker.py`
- Persistent ChromaDB indexing and BibTeX enrichment: `indexer.py`
- Dense retrieval plus optional PageRank/seed reranking: `retriever.py`
- Deterministic or caller-supplied-LLM synthesis: `synthesis.py`
- Protocol-driven extraction matrices: `matrix.py`
- Claim clustering and stance-based consensus: `consensus.py`
- Gemini/heuristic metadata extraction: `extractor.py`
- CLI commands: `index`, `query`, `synthesize`, `consensus`, `matrix`, `stats`, `extract` in [cli.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/cli.py:33)
- Broad public API exports in [__init__.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/__init__.py:3)

Harness integration is now materially healthier than older internal audits suggest: the harness constructs a real retriever for matrix and synthesis, and a real graph HTTP client at [orchestrator.py](C:/Users/mouadh/Documents/nexus-scholar-harness/src/scholar_harness/orchestrator.py:756). The MCP query now exposes `graph_source`, `alpha`, and `beta` at [server.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-agent-kit/src/scholar_agent/server.py:653).

## Confirmed defects

1. **Critical: corpus identity is mistaken for study identity.**

   `index_directory()` assigns the same `workspace_id` to every paper and assigns no `paper_id` ([indexer.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/indexer.py:217)). Downstream code consistently prefers `workspace_id` over DOI/filename:

   - citation tokens: [retriever.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/retriever.py:123)
   - synthesis `study_id`: [synthesis.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/synthesis.py:197)
   - dynamic matrix grouping: [matrix.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/matrix.py:203)
   - standard matrix grouping: [synthesis.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/synthesis.py:354)

   In the normal harness call, all papers therefore collapse into one “study.” Matrix retrieval is then scoped to that shared workspace and may populate a row from different papers ([matrix.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/matrix.py:123)). Consensus study counts likewise become scientifically invalid.

2. **Critical: the standard methodology matrix fabricates absent evidence.**

   Missing metadata defaults to `"Design Science / Empirical"`, `"Evaluation Benchmark"`, `"Standard Corpus"`, `"Accuracy / F1"`, `"Proposed System"`, and `"Domain bounded"` at [synthesis.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/synthesis.py:362). These are presented as extracted study attributes, not marked placeholders. This violates evidence-preserving behavior.

3. **High: “entailment verification” is embedding similarity, not entailment.**

   The verifier computes cosine similarity between a claim and each source chunk, rescales it, and labels scores ≥0.85 `VERIFIED` ([synthesis.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/synthesis.py:112)). Semantic relatedness cannot establish that a source entails a claim, especially for negation, quantities, or direction of effect. README language calls this “automated entailment verification” at [README.md](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/README.md:29), overstating the guarantee.

4. **High: re-indexing can leave stale chunks.**

   Indexing only upserts current deterministic IDs ([indexer.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/indexer.py:73)). If a revised paper becomes shorter, IDs from removed sections/chunks are never deleted. The README’s “guaranteed re-indexing idempotency” claim at [README.md](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/README.md:19) is therefore incomplete: repeated identical input is stable, but replacement semantics are not.

5. **High: package dependency declarations are inconsistent.**

   `matrix.py` imports `scholar_protocol` at module import time ([matrix.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/matrix.py:15)), and `__init__.py` eagerly imports `MatrixExtractor`, but `scholar-protocol-kit` is absent from runtime dependencies while present only under `[tool.uv.sources]` ([pyproject.toml](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/pyproject.toml:13)). A standalone installation can fail merely on `import scholar_rag`.

   `extractor.py` also imports `httpx` dynamically ([extractor.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/extractor.py:93)) without declaring it directly. Conversely, `scholar-graph-kit`, `scholar-bib-kit`, and `scholar-search-kit` are declared but not imported by this package.

6. **Medium: audit logging is location-dependent and silently lossy.**

   Retriever journal discovery starts from the process CWD, not `db_path` or an explicit workspace ([retriever.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/retriever.py:133)). Logging failures are swallowed ([retriever.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/retriever.py:161)). Indexer and matrix use different discovery rules, so events from one operation can land in a journal while another disappears.

7. **Medium: `min_chunk_chars` is dead configuration and paragraph overlap is absent.**

   `min_chunk_chars` is stored at [chunker.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/chunker.py:19) but never consulted. Documentation explicitly says it merges micro-chunks at [api_reference.md](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/docs/api_reference.md:10). Overlap is applied only while splitting oversized single paragraphs; ordinary paragraph-boundary splits have none ([chunker.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/chunker.py:96), [chunker.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/chunker.py:123)).

8. **Medium: dynamic matrix repeats the identical retrieval call.**

   When no scoped result is found, `extract_study()` executes the same query with the same parameters again ([matrix.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/matrix.py:129), [matrix.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/matrix.py:141)). This adds latency without changing behavior.

9. **Medium: consensus mutates caller-owned claims.**

   `analyze()` overwrites `stance` and possibly `study_id` in input objects ([consensus.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/consensus.py:297)). That side effect is undocumented and can alter later analyses.

10. **Documentation drift.**

    The API reference ends after five core components and omits `MatrixExtractor`, consensus, extraction, backends, and most exported models ([api_reference.md](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/docs/api_reference.md:1)). README also says `project.json` enriches sample size, metrics, and dataset, but indexing only reads it to derive workspace ID; those fields are never propagated ([indexer.py](C:/Users/mouadh/Documents/nexus-scholar-harness/tools/scholar-rag-kit/src/scholar_rag/indexer.py:194)).

## Hypotheses requiring empirical evaluation

- Lexical stance classification likely mislabels scientific negation and comparator-relative claims; current unit tests cover simple polarity phrases, not realistic claims.
- Four-times over-fetch before graph reranking may miss highly authoritative graph nodes that rank below the dense candidate cutoff.
- Greedy order-dependent consensus clustering may produce unstable clusters under claim reordering.
- First-sentence extraction for matrix cells likely has poor factual precision, but this requires corpus-level scoring.

## Prioritized fixes

1. Introduce a canonical per-paper `study_id`; retain `workspace_id` only as corpus scope. Use `study_id`/DOI first for tokens, matrix grouping, synthesis claims, and consensus.
2. Replace invented matrix defaults with explicit null/`NOT_REPORTED` values and provenance/status fields.
3. Rename embedding checks to semantic-support similarity, or implement genuine NLI plus verbatim quote verification before using `VERIFIED`.
4. Make document replacement atomic: identify all chunks belonging to a paper, delete obsolete IDs, then upsert.
5. Correct dependency metadata and add a clean isolated-install/import test.
6. Pass an explicit audit journal/workspace path through APIs; make logging failures observable.
7. Implement or remove `min_chunk_chars`, add paragraph overlap, remove duplicate matrix query, and copy claims before consensus normalization.
8. Add regression tests for two papers in one workspace, shortened-document re-indexing, absent-metadata matrices, negated/numeric claims, and journal placement.

=====================================================
Completed the read-only `scholar-agent-kit` audit and sent the parent agent a detailed report with exact file-and-line evidence.

Key confirmed findings:

- File-based protocol validation is currently broken.
- `nexus_pipeline_run` ignores `query` and only hides skipped stages after executing them.
- `scholar-verify-kit` is an undeclared hard dependency.
- `--workspace` does not redirect the already-initialized recon cache.
- LLM screening silently falls back to heuristics without reporting that downgrade.
- Calibration utilities exist but do not gate MCP screening.
- The skill and surface matrix contain stale tool counts and behavior claims.
- Targeted toolkit tests produced 27 passes and one genuine failure; the broader suite had 55 passes plus two shared-temp-directory setup collisions.
=====================================================
Completed the read-only `scholar-protocol-kit` audit.

Key confirmed defects:

- Valid protocol files return `INVALID` through MCP path-mode due to reparsing JSON text as a model object.
- `compile_protocol()` does not enforce cross-field validity; invalid RQ references compile successfully.
- `golden_seeds` exists in the output model but cannot survive the intent/compiler path.
- Numeric extraction dimensions generate JSON Schema fields of type `string`.
- `scholar-rag-kit` imports protocol-kit but omits it from package dependencies.
- Extra fields are silently ignored across models, masking typos.
- The PRISMA score mixes protocol readiness with permanently-failing post-execution items.
- README module names have drifted from the implementation.

Validation: all 134 protocol-kit tests passed, with four Windows subprocess decoding warnings. No files were changed.

=====================================================

Completed the read-only `scholar-verify-kit` audit and sent the parent agent the full evidence-backed report.

Highest-priority confirmed defects:

- Retraction-only evidence can incorrectly yield `UNVERIFIED` rather than `BLOCKED`.
- “No data available” is misclassified as `statement-only`.
- Unrelated repository links can inflate both DAS and CAS to `public+link`.
- `--dry-run` still performs live API requests.
- CLI and MCP `all` semantics differ.
- `scholar-agent-kit` imports but does not declare `scholar-verify-kit`.
- README input paths and command coverage have drifted.
- Corrections are described as low severity but currently block trust like retractions.

The targeted toolkit, MCP, CLI, and parity suites all passed with two skips, confirming these are uncovered boundary defects rather than existing test failures. No files were changed.

======================================================

