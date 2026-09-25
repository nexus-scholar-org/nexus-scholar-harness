# Phase C Execution Plan

## Task 1: Create `VectorBackend` Protocol in `backends.py` [INDEPENDENT]
**Description:** Define the abstract protocol for vector storage backends to establish the contract for all implementations.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/backends.py`

### Execution Checklist
- [ ] Create new file `tools/scholar-rag-kit/src/scholar_rag/backends.py`
- [ ] Import `Protocol`, `Any`, `runtime_checkable` from `typing`
- [ ] Define `VectorBackend` Protocol class with methods: `add_documents()`, `query()`, `delete()`, `count()`
- [ ] Add `@runtime_checkable` decorator for structural typing support
- [ ] Add docstrings explaining the protocol contract for each method

### Testing Strategy
- [ ] Create `tests/test_backends_protocol.py`
- [ ] Test that `NumpyBackend` (once implemented) satisfies the Protocol via `isinstance` check
- [ ] Test Protocol method signatures match expected contracts

### Definition of Done (DoD)
- [ ] `VectorBackend` Protocol defined with all required methods
- [ ] Protocol is importable without errors
- [ ] Unit test confirms structural typing compliance

---

## Task 2: Implement `NumpyBackend` Class [DEPENDS ON Task 1]
**Description:** Build the in-memory numpy-based vector backend for lightweight similarity search without external dependencies.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/backends.py`

### Execution Checklist
- [ ] Add `NumpyBackend` class implementing `VectorBackend` protocol
- [ ] Implement `__init__()` with internal storage: `_documents`, `_metadatas`, `_ids`, `_vectors`, `_embedder`
- [ ] Implement `set_embedder(embedder)` method to inject embedding function
- [ ] Implement `add_documents()` with numpy array normalization for cosine similarity
- [ ] Implement `query()` with vectorized dot product for cosine similarity scoring
- [ ] Implement `delete()` with index filtering
- [ ] Implement `count()` returning document count
- [ ] Handle edge cases: empty store query returns empty results, division by zero protection
- [ ] Use deferred numpy import inside methods (P7.7 lazy imports)

### Testing Strategy
- [ ] Create `tests/test_numpy_backend.py`
- [ ] Use `MockEmbeddingFunction` from `scholar_rag.embedder` as the embedder
- [ ] Test `add_documents()` with 3 sample texts and verify count increases
- [ ] Test `query()` returns results sorted by similarity (most similar first)
- [ ] Test `query()` on empty store returns empty dict with correct keys
- [ ] Test `delete()` removes specific documents by ID
- [ ] Test `count()` accuracy after add/delete operations
- [ ] Test normalization prevents zero-division with empty vectors

### Definition of Done (DoD)
- [ ] `NumpyBackend` class passes all unit tests
- [ ] Class satisfies `VectorBackend` Protocol
- [ ] Handles edge cases: empty store, single document, duplicate IDs
- [ ] NumPy imports are deferred inside method bodies

---

## Task 3: Integrate `NumpyBackend` with `ScholarIndexer` [DEPENDS ON Task 2]
**Description:** Wire the numpy backend into the existing indexer so it can be used as an alternative to ChromaDB.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/indexer.py`

### Execution Checklist
- [ ] Add optional `backend` parameter to `ScholarIndexer.__init__()` (default: `None` for ChromaDB)
- [ ] When `backend` is provided, skip ChromaDB initialization and use the provided backend
- [ ] Modify `index_markdown()` to use backend's `add_documents()` when backend is set
- [ ] Modify `get_collection_count()` to delegate to backend's `count()` when backend is set
- [ ] Ensure backward compatibility: existing ChromaDB path works unchanged
- [ ] Add `NumpyBackend` import in `__init__.py` for public API

### Testing Strategy
- [ ] Create `tests/test_indexer_backend.py`
- [ ] Test `ScholarIndexer` with `NumpyBackend` backend indexes documents correctly
- [ ] Test `ScholarIndexer` without backend still uses ChromaDB (mock ChromaDB)
- [ ] Test `get_collection_count()` delegates correctly to backend
- [ ] Test backward compatibility: existing `ScholarIndexer()` constructor unchanged

### Definition of Done (DoD)
- [ ] `ScholarIndexer` accepts optional `backend` parameter
- [ ] Existing `index`/`query` CLI commands work unchanged
- [ ] New backend path produces equivalent results to ChromaDB path
- [ ] No breaking changes to existing API

---

## Task 4: Create `schemas.py` with Extraction Pydantic Models [INDEPENDENT]
**Description:** Define the Pydantic models for structured paper extraction, aligning with existing `MethodologyMetadata`.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/schemas.py`

### Execution Checklist
- [ ] Create new file `tools/scholar-rag-kit/src/scholar_rag/schemas.py`
- [ ] Import `BaseModel`, `Field` from pydantic and `MethodologyMetadata` from `.models`
- [ ] Define `AuthorExtraction` model with fields: `family_name`, `given_name`, `orcid`, `affiliation`, `email`
- [ ] Define `PaperExtraction` model with all metadata fields per spec section 2.2.3
- [ ] Ensure `PaperExtraction.methodology` reuses `MethodologyMetadata` from existing `models.py`
- [ ] Define `ExtractionResult` model with provenance fields: `confidence`, `source_file`, `chunk_index`, `extraction_timestamp`, `pii_redacted`
- [ ] Add field descriptions using `Field(description=...)` for LLM prompt context
- [ ] Export all models from `__init__.py`

### Testing Strategy
- [ ] Create `tests/test_schemas.py`
- [ ] Test `PaperExtraction` instantiation with valid data
- [ ] Test `PaperExtraction` accepts `MethodologyMetadata` as `methodology` field
- [ ] Test `ExtractionResult` defaults: `pii_redacted=False`, `extraction_timestamp` auto-set
- [ ] Test `AuthorExtraction` optional fields default to `None`

### Definition of Done (DoD)
- [ ] All three Pydantic models defined and importable
- [ ] `PaperExtraction.methodology` type is `MethodologyMetadata | None`
- [ ] Models serialize/deserialize correctly via `.model_dump()` and `**dict`
- [ ] Unit tests pass

---

## Task 5: Create `redactor.py` with PII Detection and Redaction [INDEPENDENT]
**Description:** Implement regex-based PII detection and recursive redaction for emails, ORCIDs, phones, and grant numbers.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/redactor.py`

### Execution Checklist
- [ ] Create new file `tools/scholar-rag-kit/src/scholar_rag/redactor.py`
- [ ] Define `PIIRedactor` class with compiled regex patterns for: EMAIL, ORCID_URI, ORCID_NUMERIC, PHONE, GRANT
- [ ] Implement `redact(text: str) -> tuple[str, bool]` method
- [ ] Implement `redact_dict(data: dict) -> tuple[dict, bool]` for recursive dictionary redaction
- [ ] Implement `redact_list(items: list) -> tuple[list, bool]` for recursive list redaction
- [ ] Ensure ORCID URIs are redacted before numeric ORCIDs (avoid partial replacement)
- [ ] Use replacement markers: `[EMAIL REDACTED]`, `[ORCID REDACTED]`, `[PHONE REDACTED]`, `[GRANT REDACTED]`

### Testing Strategy
- [ ] Create `tests/test_redactor.py`
- [ ] Test email detection: `user@example.com` → `[EMAIL REDACTED]`
- [ ] Test ORCID URI: `https://orcid.org/0000-0002-1825-0097` → `[ORCID REDACTED]`
- [ ] Test numeric ORCID: `0000-0002-1825-0097` → `[ORCID REDACTED]`
- [ ] Test phone: `(555) 123-4567` → `[PHONE REDACTED]`
- [ ] Test grant: `NIH Grant R01-12345` → `[GRANT REDACTED]`
- [ ] Test `redact_dict()` recursively redacts nested structures
- [ ] Test `redact_list()` handles mixed-type lists
- [ ] Test return value `pii_found=True` when PII detected, `False` otherwise

### Definition of Done (DoD)
- [ ] All PII patterns correctly detect and redact target data
- [ ] Recursive methods handle nested dicts/lists
- [ ] `pii_found` flag accurately reflects PII presence
- [ ] 100% of test PII samples redacted (per spec acceptance criteria)

---

## Task 6: Create `extractor.py` with LLMExtractor Class [DEPENDS ON Tasks 4, 5]
**Description:** Build the LLM-based structured extraction pipeline with Gemini REST API integration and heuristic fallback.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/extractor.py`

### Execution Checklist
- [ ] Create new file `tools/scholar-rag-kit/src/scholar_rag/extractor.py`
- [ ] Define `LLMExtractor` class with `__init__(api_key, model, temperature, timeout)`
- [ ] Implement `EXTRACTION_PROMPT` class constant with schema and rules per spec
- [ ] Implement `_FIELD_WEIGHTS` dict for confidence calculation
- [ ] Implement `extract_from_text(text, schema, chunk_index, source_file, section_name)` async method
- [ ] Implement `extract_from_file(file_path, schema)` async method using `MarkdownChunker`
- [ ] Implement `_call_llm(prompt)` async method with Gemini REST API call via `httpx`
- [ ] Implement `_parse_llm_json(response)` for robust JSON extraction from LLM output
- [ ] Implement `_heuristic_extract(text, schema)` for rule-based fallback (title, DOI, year)
- [ ] Implement `_calculate_confidence(extracted, schema)` with weighted field scoring
- [ ] Wire `PIIRedactor` into extraction pipeline for automatic redaction
- [ ] Handle LLM failures gracefully: catch exceptions → fallback to heuristic

### Testing Strategy
- [ ] Create `tests/test_extractor.py`
- [ ] Mock `httpx.AsyncClient.post()` to return canned JSON responses
- [ ] Test `extract_from_text()` with valid LLM response → correctly parsed `ExtractionResult`
- [ ] Test LLM failure → heuristic fallback activates and produces valid result
- [ ] Test `_parse_llm_json()` handles markdown fences, bare JSON, malformed input
- [ ] Test `_calculate_confidence()` produces correct weighted scores
- [ ] Test PII redaction is applied to extraction results
- [ ] Test `extract_from_file()` chunks document and extracts from each chunk

### Definition of Done (DoD)
- [ ] `LLMExtractor` extracts structured metadata from text via mocked LLM
- [ ] Heuristic fallback activates on LLM failure
- [ ] PII redaction applied to all extraction results
- [ ] Confidence score uses weighted field importance
- [ ] All unit tests pass with mocked HTTP

---

## Task 7: Add `extract` CLI Command [DEPENDS ON Task 6]
**Description:** Register the `extract` command in the existing Typer CLI for end-to-end document extraction.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/cli.py`

### Execution Checklist
- [ ] Import `LLMExtractor` from `.extractor` and `PaperExtraction` from `.schemas` in `cli.py`
- [ ] Add `@app.command("extract")` decorated function with parameters: `input_file`, `schema_name`, `output`, `api_key`
- [ ] Implement schema registry: `{"paper": PaperExtraction}`
- [ ] Use `asyncio.run()` to call `extractor.extract_from_file()` (async/sync bridge)
- [ ] Output JSON to file (`--output`) or stdout
- [ ] Add `typer.echo()` success/error messages
- [ ] Add help text: "Extract structured metadata from a document using LLM"

### Testing Strategy
- [ ] Create `tests/test_cli_extract.py`
- [ ] Use `typer.testing.CliRunner` for CLI testing
- [ ] Mock `LLMExtractor` to avoid real API calls
- [ ] Test `extract` command with valid input file produces JSON output
- [ ] Test `--output` flag writes to file correctly
- [ ] Test invalid `--schema` raises `BadParameter`
- [ ] Test missing input file shows error

### Definition of Done (DoD)
- [ ] `scholar-rag extract` command is registered and callable
- [ ] Command accepts `--schema`, `--output`, `--api-key` options
- [ ] Command produces valid JSON extraction output
- [ ] CLI integration tests pass

---

## Task 8: Add `GeminiEmbedding` Class to `embedder.py` [INDEPENDENT]
**Description:** Add Gemini API embedding model as an alternative to sentence-transformers for vector storage.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/embedder.py`

### Execution Checklist
- [ ] Add `GeminiEmbedding` class to existing `embedder.py` (not a new file)
- [ ] Implement `__init__(api_key, model)` with deferred `GEMINI_API_KEY` env var lookup
- [ ] Implement `_ensure_initialized()` with lazy `google.generativeai` import (P7.7)
- [ ] Implement `embed(texts: list[str]) -> list[list[float]]` with batch processing (batch_size=100)
- [ ] Implement `dimension` property returning 768 (text-embedding-004)
- [ ] Handle rate limits with try/except for future exponential backoff
- [ ] Keep all heavy imports deferred inside method bodies

### Testing Strategy
- [ ] Create `tests/test_gemini_embedding.py`
- [ ] Mock `google.generativeai` module to avoid real API calls
- [ ] Test `GeminiEmbedding.dimension` returns 768
- [ ] Test `embed()` with mocked API returns correct-shaped embeddings
- [ ] Test batch processing: 150 texts → 2 batches
- [ ] Test `_ensure_initialized()` lazy import works

### Definition of Done (DoD)
- [ ] `GeminiEmbedding` class added to existing `embedder.py`
- [ ] Class produces 768-dimensional embeddings via mocked API
- [ ] Batch processing handles large text lists
- [ ] All imports deferred (P7.7 compliant)
- [ ] Unit tests pass

---

## Task 9: Register `gemini` in `get_embedder()` Factory [DEPENDS ON Task 8]
**Description:** Wire `GeminiEmbedding` into the existing embedder factory so `--embedder gemini` works in CLI.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/embedder.py`

### Execution Checklist
- [ ] Add `elif prov == "gemini":` branch in `get_embedder()` function
- [ ] Instantiate `GeminiEmbedding(api_key=api_key, model_name=model_name)` when provider is `gemini`
- [ ] Add `gemini` to the `ValueError` message in the `else` clause
- [ ] Update docstring to document `gemini` as supported provider
- [ ] Handle missing `GEMINI_API_KEY` with descriptive `ValueError`

### Testing Strategy
- [ ] Update `tests/test_embeddings.py`
- [ ] Test `get_embedder(provider="gemini")` returns `GeminiEmbedding` instance
- [ ] Test `get_embedder(provider="gemini", api_key="test")` works
- [ ] Test `get_embedder(provider="gemini")` without API key raises `ValueError`
- [ ] Test existing providers (`sentence-transformers`, `openai`, `mock`) still work

### Definition of Done (DoD)
- [ ] `get_embedder(provider="gemini")` returns `GeminiEmbedding`
- [ ] Missing API key raises descriptive error
- [ ] Existing providers unaffected
- [ ] Unit tests pass

---

## Task 10: Write Unit Tests for NumpyBackend [DEPENDS ON Task 2]
**Description:** Comprehensive unit tests for the numpy vector backend covering all operations.
**Files to Touch:** `tests/test_numpy_backend.py`

### Execution Checklist
- [ ] Create `tests/test_numpy_backend.py`
- [ ] Import `NumpyBackend` from `scholar_rag.backends`
- [ ] Import `MockEmbeddingFunction` from `scholar_rag.embedder`
- [ ] Create fixture: `numpy_backend` with mock embedder set
- [ ] Test `test_add_documents`: add 3 docs, verify count is 3
- [ ] Test `test_query_returns_sorted_by_similarity`: most similar doc first
- [ ] Test `test_query_empty_store`: returns empty dict with correct keys
- [ ] Test `test_delete_documents`: delete by ID removes correct docs
- [ ] Test `test_count`: accurate after add/delete operations
- [ ] Test `test_add_documents_no_embedder_raises`: ValueError when embedder not set
- [ ] Test `test_cosine_similarity_accuracy`: known texts produce expected similarity ordering

### Testing Strategy
- [ ] All tests use `MockEmbeddingFunction` (hermetic, no network)
- [ ] Use `pytest` fixtures for backend setup/teardown
- [ ] Assert return dict keys match expected structure: `documents`, `metadatas`, `distances`, `ids`

### Definition of Done (DoD)
- [ ] All 7+ test cases pass
- [ ] Tests are hermetic (no network, no real embeddings)
- [ ] Coverage for edge cases: empty store, single doc, duplicate IDs

---

## Task 11: Write Unit Tests for PII Redactor [DEPENDS ON Task 5]
**Description:** Comprehensive unit tests for PII detection and redaction covering all patterns.
**Files to Touch:** `tests/test_redactor.py`

### Execution Checklist
- [ ] Create `tests/test_redactor.py`
- [ ] Import `PIIRedactor` from `scholar_rag.redactor`
- [ ] Create fixture: `redactor` instance
- [ ] Test `test_redact_email`: `Contact john@example.com for info` → email redacted
- [ ] Test `test_redact_orcid_uri`: `https://orcid.org/0000-0002-1825-0097` → ORCID redacted
- [ ] Test `test_redact_orcid_numeric`: `0000-0002-1825-0097` → ORCID redacted
- [ ] Test `test_redact_phone`: `(555) 123-4567` → phone redacted
- [ ] Test `test_redact_grant`: `NIH Grant R01-12345` → grant redacted
- [ ] Test `test_redact_dict_recursive`: nested dict redacted correctly
- [ ] Test `test_redact_list_recursive`: mixed-type list handled
- [ ] Test `test_no_pii_found`: clean text returns unchanged with `pii_found=False`
- [ ] Test `test_multiple_pii_types`: text with email+phone → both redacted, `pii_found=True`

### Testing Strategy
- [ ] Use `pytest.mark.parametrize` for pattern variations
- [ ] Test both `redact()` and `redact_dict()` methods
- [ ] Verify `pii_found` flag accuracy for each test case

### Definition of Done (DoD)
- [ ] All PII patterns tested with positive and negative cases
- [ ] Recursive redaction works for nested structures
- [ ] `pii_found` flag accurate in all scenarios
- [ ] 100% of target PII types detected (spec acceptance criteria)

---

## Task 12: Write Unit Tests for LLMExtractor [DEPENDS ON Tasks 6, 7]
**Description:** Comprehensive unit tests for the LLM extraction pipeline with mocked HTTP responses.
**Files to Touch:** `tests/test_extractor.py`

### Execution Checklist
- [ ] Create `tests/test_extractor.py`
- [ ] Import `LLMExtractor` from `scholar_rag.extractor`
- [ ] Import `PaperExtraction` from `scholar_rag.schemas`
- [ ] Mock `httpx.AsyncClient.post()` with `pytest_asyncio` or `unittest.mock`
- [ ] Test `test_extract_from_text_valid_response`: mocked LLM returns valid JSON
- [ ] Test `test_extract_from_text_llm_failure_fallback`: LLM raises exception → heuristic activates
- [ ] Test `test_parse_llm_json_with_fences`: parses JSON inside markdown code fences
- [ ] Test `test_parse_llm_json_bare`: parses bare JSON object
- [ ] Test `test_parse_llm_json_invalid`: raises ValueError on unparseable input
- [ ] Test `test_heuristic_extract_title`: extracts title from `# Title` pattern
- [ ] Test `test_heuristic_extract_doi`: extracts DOI from text
- [ ] Test `test_heuristic_extract_year`: extracts 4-digit year
- [ ] Test `test_calculate_confidence`: weighted score matches expected value
- [ ] Test `test_pii_redaction_applied`: extraction results have PII redacted
- [ ] Test `test_extract_from_file`: chunks file and extracts from each chunk

### Testing Strategy
- [ ] Use `pytest.mark.asyncio` for async test methods
- [ ] Mock all HTTP calls (hermetic testing)
- [ ] Use fixture with sample markdown text for extraction

### Definition of Done (DoD)
- [ ] LLM extraction works with mocked responses
- [ ] Heuristic fallback activates on failure
- [ ] PII redaction applied to all results
- [ ] Confidence scoring is deterministic
- [ ] All async tests pass

---

## Task 13: Write Unit Tests for GeminiEmbedding [DEPENDS ON Tasks 8, 9]
**Description:** Unit tests for the Gemini embedding class with mocked API.
**Files to Touch:** `tests/test_gemini_embedding.py`

### Execution Checklist
- [ ] Create `tests/test_gemini_embedding.py`
- [ ] Import `GeminiEmbedding` from `scholar_rag.embedder`
- [ ] Mock `google.generativeai` module
- [ ] Test `test_gemini_embedding_dimension`: `dimension` property returns 768
- [ ] Test `test_embed_single_text`: returns list of one 768-dim vector
- [ ] Test `test_embed_batch`: 5 texts → 5 embeddings
- [ ] Test `test_embed_large_batch`: 150 texts → batched into 2 API calls
- [ ] Test `test_api_key_from_env`: reads `GEMINI_API_KEY` env var
- [ ] Test `test_api_key_from_param`: explicit `api_key` overrides env var

### Testing Strategy
- [ ] Use `unittest.mock.patch` to mock `google.generativeai`
- [ ] Verify mock API called with correct `task_type` and `title`
- [ ] Assert embedding dimensions match expected (768)

### Definition of Done (DoD)
- [ ] All 7 test cases pass
- [ ] Batch processing verified
- [ ] API key handling (env var and explicit) tested
- [ ] Tests are hermetic (no real API calls)

---

## Task 14: Write CLI Integration Test for `extract` Command [DEPENDS ON Task 7]
**Description:** End-to-end integration test for the `extract` CLI command with mocked dependencies.
**Files to Touch:** `tests/test_cli_extract.py`

### Execution Checklist
- [ ] Create `tests/test_cli_extract.py`
- [ ] Use `typer.testing.CliRunner` for CLI invocation
- [ ] Create fixture: sample markdown file in `tmp_path`
- [ ] Mock `LLMExtractor.extract_from_file()` to return canned result
- [ ] Test `test_extract_stdout`: output goes to stdout as JSON
- [ ] Test `test_extract_output_file`: `--output` flag writes to file
- [ ] Test `test_extract_invalid_schema`: `--schema invalid` raises error
- [ ] Test `test_extract_missing_file`: non-existent file shows error

### Testing Strategy
- [ ] Use `CliRunner.invoke()` for CLI testing
- [ ] Assert exit codes and output content
- [ ] Verify JSON output is valid and parseable

### Definition of Done (DoD)
- [ ] All 4 CLI test cases pass
- [ ] Command output is valid JSON
- [ ] Error handling works for invalid inputs

---

## Task 15: Run Full Test Suite and Fix Regressions [DEPENDS ON Tasks 10-14]
**Description:** Execute the complete Phase C test suite and fix any regressions or failures.
**Files to Touch:** `tests/` (all Phase C test files)

### Execution Checklist
- [ ] Run `uv run pytest tests/test_numpy_backend.py -v`
- [ ] Run `uv run pytest tests/test_redactor.py -v`
- [ ] Run `uv run pytest tests/test_schemas.py -v`
- [ ] Run `uv run pytest tests/test_extractor.py -v`
- [ ] Run `uv run pytest tests/test_gemini_embedding.py -v`
- [ ] Run `uv run pytest tests/test_cli_extract.py -v`
- [ ] Run full suite: `uv run pytest tests/ -k "backend or extractor or redactor or embedding or schema" -v`
- [ ] Fix any failing tests
- [ ] Verify coverage ≥90% for new code: `uv run pytest --cov=scholar_rag`

### Testing Strategy
- [ ] Run tests in order: unit → integration
- [ ] Check for import errors, type errors, runtime failures
- [ ] Verify no regressions in existing tests

### Definition of Done (DoD)
- [ ] All Phase C tests pass
- [ ] No regressions in existing test suite
- [ ] Coverage ≥90% for new modules

---

## Task 16: Update `__init__.py` Exports [DEPENDS ON Tasks 1-9]
**Description:** Ensure all new modules are properly exported from the package's public API.
**Files to Touch:** `tools/scholar-rag-kit/src/scholar_rag/__init__.py`

### Execution Checklist
- [ ] Read current `__init__.py` exports
- [ ] Add `VectorBackend`, `NumpyBackend` from `.backends`
- [ ] Add `PaperExtraction`, `AuthorExtraction`, `ExtractionResult` from `.schemas`
- [ ] Add `PIIRedactor` from `.redactor`
- [ ] Add `LLMExtractor` from `.extractor`
- [ ] Add `GeminiEmbedding` from `.embedder`
- [ ] Verify imports work: `python -c "from scholar_rag import NumpyBackend, LLMExtractor"`

### Testing Strategy
- [ ] Create `tests/test_init_exports.py`
- [ ] Test all new classes are importable from `scholar_rag`
- [ ] Test no import errors on package load

### Definition of Done (DoD)
- [ ] All new classes exported and importable
- [ ] No circular import errors
- [ ] Package loads cleanly

---

## Task 17: Update SKILL.md Documentation [DEPENDS ON Tasks 1-9]
**Description:** Document new capabilities in the scholar-rag-kit SKILL.md for agent consumption.
**Files to Touch:** `.agents/skills/scholar-rag-kit/SKILL.md`

### Execution Checklist
- [ ] Read current SKILL.md content
- [ ] Add section: "In-Memory Vector Backend (NumpyBackend)"
- [ ] Add section: "Structured Extraction with LLM (extract command)"
- [ ] Add section: "Gemini Embedding Integration (--embedder gemini)"
- [ ] Document CLI usage examples for each new feature
- [ ] Document Python API usage for programmatic access
- [ ] Add troubleshooting section for common issues (API key, rate limits)

### Testing Strategy
- [ ] Review documentation for accuracy against implementation
- [ ] Verify CLI examples work as documented

### Definition of Done (DoD)
- [ ] SKILL.md covers all Phase C features
- [ ] CLI examples are correct and runnable
- [ ] Python API examples are correct

---

## Task 18: Run Lint and Type Checks [DEPENDS ON Tasks 1-16]
**Description:** Ensure all new code passes linting and type checking without errors.
**Files to Touch:** All new/modified files

### Execution Checklist
- [ ] Run `uv run ruff check tools/scholar-rag-kit/src/scholar_rag/` (or CI scope if narrower)
- [ ] Fix any ruff findings in new code
- [ ] Run type checker if configured (e.g., `uv run mypy`)
- [ ] Fix any type errors in new code
- [ ] Verify no new warnings introduced

### Testing Strategy
- [ ] Lint passes with zero findings in new code
- [ ] Type checker passes with zero errors in new code

### Definition of Done (DoD)
- [ ] `ruff check` clean for all new/modified files
- [ ] Type checker clean for all new/modified files
- [ ] No regressions in existing lint status

---

## Task 19: Conformance Test Verification [DEPENDS ON Task 7]
**Description:** Verify new `extract` command passes conformance tests for CLI parity.
**Files to Touch:** `tests/conformance/test_actions_cli_parity.py`

### Execution Checklist
- [ ] Run `uv run pytest tests/conformance/test_actions_cli_parity.py -v`
- [ ] Verify `extract` command is registered in Typer app
- [ ] Check CLI help text is accessible: `scholar-rag extract --help`
- [ ] Fix any conformance test failures

### Testing Strategy
- [ ] Run existing conformance tests
- [ ] Verify new command doesn't break existing parity checks

### Definition of Done (DoD)
- [ ] All conformance tests pass
- [ ] `extract` command registered in Typer app
- [ ] CLI help text works

---

## Task 20: Monorepo Sync Preparation [INDEPENDENT]
**Description:** Prepare kit changes for sync to external repos per monorepo governance rules.
**Files to Touch:** `scripts/push_tools.py`, `plugins.json`

### Execution Checklist
- [ ] Run `python scripts/push_tools.py` to copy kit changes to external repos
- [ ] Update `plugins.json` with new commit SHAs (manual step after push)
- [ ] Run `python scripts/generate_nexus_scholar_pins.py --check` to verify pin freshness
- [ ] Run `python scripts/generate_nexus_scholar_pins.py` to regenerate pins if needed
- [ ] Verify `uv run pytest tests/conformance/` still passes

### Testing Strategy
- [ ] Verify push script runs without errors
- [ ] Verify pin generation succeeds
- [ ] Verify conformance tests pass after sync

### Definition of Done (DoD)
- [ ] Kit changes synced to external repos
- [ ] `plugins.json` updated with new SHAs
- [ ] Metapackage pins regenerated
- [ ] Conformance tests pass

---

## Task Summary

| Task | Title | Dependencies | Est. Hours | Independent? |
|------|-------|--------------|------------|--------------|
| 1 | Create `VectorBackend` Protocol | None | 0.5 | Yes |
| 2 | Implement `NumpyBackend` Class | Task 1 | 2.0 | No |
| 3 | Integrate `NumpyBackend` with `ScholarIndexer` | Task 2 | 1.0 | No |
| 4 | Create `schemas.py` Pydantic Models | None | 0.5 | Yes |
| 5 | Create `redactor.py` PII Detection | None | 1.0 | Yes |
| 6 | Create `extractor.py` LLMExtractor | Tasks 4, 5 | 2.0 | No |
| 7 | Add `extract` CLI Command | Task 6 | 1.0 | No |
| 8 | Add `GeminiEmbedding` Class | None | 1.0 | Yes |
| 9 | Register `gemini` in Factory | Task 8 | 0.5 | No |
| 10 | Unit Tests: NumpyBackend | Task 2 | 1.0 | No |
| 11 | Unit Tests: PII Redactor | Task 5 | 1.0 | No |
| 12 | Unit Tests: LLMExtractor | Tasks 6, 7 | 1.5 | No |
| 13 | Unit Tests: GeminiEmbedding | Tasks 8, 9 | 1.0 | No |
| 14 | CLI Integration Test: extract | Task 7 | 0.5 | No |
| 15 | Full Test Suite & Regression Fix | Tasks 10-14 | 1.5 | No |
| 16 | Update `__init__.py` Exports | Tasks 1-9 | 0.5 | No |
| 17 | Update SKILL.md Documentation | Tasks 1-9 | 1.0 | No |
| 18 | Lint & Type Checks | Tasks 1-16 | 0.5 | No |
| 19 | Conformance Test Verification | Task 7 | 0.5 | No |
| 20 | Monorepo Sync Preparation | Task 19 | 1.5 | Yes |

**Total Estimated Hours:** 20.0

## Execution Order (Critical Path)

```
Task 1 → Task 2 → Task 3 → Task 10
Task 4 → Task 6 → Task 7 → Task 12, 14, 19
Task 5 → Task 6
Task 8 → Task 9 → Task 13
Task 15 → Task 16 → Task 17 → Task 18
Task 20 (parallel, post-implementation)
```

## Parallel Execution Opportunities

The following task groups can be executed concurrently:
- **Group A (Vector Backend):** Tasks 1, 2, 3, 10
- **Group B (Extraction):** Tasks 4, 5, 6, 7, 11, 12, 14
- **Group C (Gemini Embedding):** Tasks 8, 9, 13
- **Group D (Integration):** Tasks 15, 16, 17, 18, 19, 20

Groups A, B, and C can run in parallel. Group D depends on completion of A, B, and C.
