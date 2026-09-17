# Scholar Bib Kit -- Comprehensive Deep Dive Analysis

> **Kit path:** `C:\Users\mouadh\Documents\nexus-scholar-harness\tools\scholar-bib-kit`
> **Analysis date:** 2026-09-14
> **Version:** 0.1.0 (hatchling build)
> **Total source files:** 5 Python modules + 1 test file
> **Total source LOC:** ~351 lines (src + tests)

---

## 1. Executive Summary

`scholar-bib-kit` is the bibliography management component of the Nexus Scholar Suite. It provides four core capabilities -- parsing, linting, deduplication, and Crossref resolution -- for BibTeX databases. Despite its small codebase (~290 LOC of application code), it plays a critical role in the literature review pipeline: every project's `references.bib` should pass through this kit for hygiene before being consumed by RAG indexing, graph construction, or export.

**Current maturity: Early alpha.** The kit has a working CLI with four commands, a thin Python API, and basic tests. However, it exhibits significant gaps in documentation accuracy, error handling, API surface consistency with its own docs, and integration alignment with the rest of the Nexus Suite. The documentation (`docs/tutorial.md`, `docs/api_reference.md`) describes classes and methods (`RepairEngine`, `CrossrefValidator`, `BibEntry` model) that do not exist in the codebase -- a strong signal of stale/aspirational docs that will confuse agents and developers.

**Key finding:** The kit's documentation describes a `fix` command, `RepairEngine`, `CrossrefValidator`, and `BibEntry`/`RepairStats` Pydantic models that are **entirely absent** from the implementation. The actual implementation provides `lint`, `merge`, `dedup`, `resolve` commands and `BibParser`, `BibLinter`, `BibDeduplicator`, `BibResolver` classes. This is a major coherence failure.

---

## 2. Detailed Analysis by Dimension

### 2.1 Functionalities

#### 2.1.1 Complete Capability Inventory

| Capability | Module | Status | Notes |
|:--|:--|:--|:--|
| BibTeX file loading | `parser.py` | Working | Thin wrapper around `bibtexparser.parse_file` |
| BibTeX file saving | `parser.py` | Working | Thin wrapper around `bibtexparser.write_file` |
| Title case protection (double braces) | `linter.py:12-18` | Working | Idempotent, handles single-brace and no-brace |
| Citation key standardization (AuthorYear) | `linter.py:21-48` | Working | Single mode only; suffix starts at 'a' (chr(97)) |
| Multi-file merge | `cli.py:42-72` | Working | Sequential load + block-level add |
| DOI-based deduplication | `deduplicator.py:22-30` | Working | Exact match on cleaned DOI |
| Title-based deduplication | `deduplicator.py:31-33` | Working | Exact match on cleaned title |
| Field grafting on dedup | `deduplicator.py:36-40` | Working | Merges missing fields from duplicate into survivor |
| Crossref DOI resolution | `resolver.py:14-25` | Working | Fetches `application/x-bibtex` from Crossref |
| Crossref title/author search | `resolver.py:27-45` | Working | Fallback when DOI is missing |
| Entry-level resolution | `resolver.py:47-87` | Working | Replaces entire entry fields in-place |
| Library-level resolution | `resolver.py:89-100` | Working | Parallel async tasks via `as_completed` |
| CLI: `lint` | `cli.py:23-40` | Working | With `--generate-keys` option |
| CLI: `merge` | `cli.py:42-72` | Working | With `--dedup/--no-dedup` |
| CLI: `dedup` | `cli.py:74-96` | Working | Standalone dedup command |
| CLI: `resolve` | `cli.py:98-124` | Working | Async Crossref resolution |

#### 2.1.2 CLI Commands to Functions Mapping

| CLI Command | Entry Function | Core API Calls |
|:--|:--|:--|
| `scholar-bib lint <file>` | `cli.lint()` | `BibParser.load()` -> `BibLinter.lint()` -> `BibParser.save()` |
| `scholar-bib merge <files>` | `cli.merge()` | `BibParser.load()` x N -> `Library.add()` loop -> `BibDeduplicator.dedup()` -> `BibParser.save()` |
| `scholar-bib dedup <file>` | `cli.dedup()` | `BibParser.load()` -> `BibDeduplicator.dedup()` -> `BibParser.save()` |
| `scholar-bib resolve <file>` | `cli.resolve()` | `BibParser.load()` -> `BibResolver.resolve_library()` -> `BibParser.save()` |

#### 2.1.3 Data Models and Schemas

The kit uses `bibtexparser` v2 data models directly -- there are **no custom Pydantic models** despite `pydantic` being a declared dependency and the docs claiming `BibEntry`/`RepairStats` models exist.

**Actual data flow:**
```
File (.bib) -> bibtexparser.parse_file() -> Library (blocks: list[Block])
  -> Library.entries: list[Entry]
    -> Entry.key: str
    -> Entry.entry_type: str
    -> Entry.fields_dict: dict[str, Field]
      -> Field.key: str
      -> Field.value: str
  -> Library.blocks: list[Block] (includes Entry, Preamble, Comment)
```

#### 2.1.4 Integration Points with Other Kits

| Consumer Kit | Integration Point | Usage |
|:--|:--|:--|
| `scholar-agent-kit` | `server.py:66-68,586-591` | MCP tool `nexus_bib_clean` imports `BibParser`, `BibLinter`, `BibDeduplicator` |
| `scholar-search-kit` | `providers/crossref.py:116-142` | Crossref provider exposes `validate_reference()` hook intended for bib-kit (but bib-kit does NOT use it -- it has its own Crossref client) |
| `scholar-search-kit` | `http_client.py:47-122` | `BibResolver` uses `AcademicHttpClient` for HTTP requests |
| `scholar-harness` | `tests/test_mcp_tools_graph.py:191-208` | Integration tests exercise `BibParser` round-trips |
| `nexus-scholar` metapackage | `pyproject.toml` | Kit is included in distribution wheel via hatchling `force-include` |

**Critical integration gap:** `BibResolver` builds its own Crossref query (lines 29-31 of `resolver.py`) rather than using the `CrossrefProvider.validate_reference()` hook from `scholar-search-kit`. This duplicates rate limiting, user-agent handling, and error recovery logic. The `scholar-search-kit` Crossref provider at `providers/crossref.py:118-141` already has a `validate_reference()` method with a relevance score threshold (>40) that `BibResolver` lacks.

---

### 2.2 Improvements

#### 2.2.1 Code Quality Issues

**[IMP-1] Debug print statements in production code**
- `resolver.py:19`: `print(f"DOI {doi} status: {response.status_code}, content: {response.text[:100]}")`
- `resolver.py:23`: `print(f"Error fetching DOI {doi}: {e}")`
- `resolver.py:33`: `print(f"Search status: {response.status_code}")`
- `resolver.py:39`: `print(f"Found DOI from search: {doi}")`
- `resolver.py:49`: `print(f"Resolving entry: {entry.key}")`
- `resolver.py:54`: `print(f"DOI field: {doi_field}")`
- `resolver.py:60`: `print(f"Using DOI: {doi}")`
- `resolver.py:75`: `print(f"Resolved new entry for {entry.key} with {len(new_entry.fields_dict)} fields")`
- `resolver.py:85`: `print(f"No entries parsed from crossref string for {entry.key}: {bibtex_str}")`
- `resolver.py:87`: `print(f"Exception parsing bibtex string: {e}")`

These are debug prints that should use `logging` or be removed. They leak potentially sensitive data (full DOI strings, API responses) to stdout.

**[IMP-2] Stale documentation describes non-existent API**
- `docs/api_reference.md:18-31` describes `CrossrefValidator` class with `get_by_doi()` and `fuzzy_match()` methods -- does not exist.
- `docs/api_reference.md:33-51` describes `RepairEngine` class with `repair_entry()` method -- does not exist.
- `docs/api_reference.md:53-57` describes `BibEntry` and `RepairStats` Pydantic models -- do not exist.
- `docs/tutorial.md:10` describes `scholar-bib fix` command -- does not exist (actual commands: `lint`, `merge`, `dedup`, `resolve`).
- `docs/tutorial.md:16-21` describes `--no-fuzzy` and `--overwrite` options -- do not exist.
- `docs/api_reference.md:12-16` describes `BibParser` as instantiated with `BibParser(Path("file.bib"))` followed by `.read()` / `.write()` -- the actual API is `BibParser.load(filepath)` / `BibParser.save(library, filepath)` (static methods).

**[IMP-3] Unused `pydantic` dependency**
- `pyproject.toml:18` declares `pydantic>=2.0.0` but no module in the kit imports or uses Pydantic.

**[IMP-4] Inconsistent `__init__.py` exports**
- `__init__.py:1` contains only `"""Scholar Bib Kit"""` -- no public API re-exports.
- Consumers must import from submodules (`from scholar_bib.parser import BibParser`).

**[IMP-5] No type hints on CLI functions**
- `cli.py` functions lack return type annotations and parameter type hints beyond what Typer infers.

#### 2.2.2 Missing Features or Capabilities

**[FEAT-1] No `fix`/`repair` command** -- The docs promise a `fix` command that repairs entries using Crossref. The actual `resolve` command does something similar but is not the documented interface.

**[FEAT-2] No confidence scoring on resolution** -- `BibResolver.resolve_search()` takes the first Crossref result without any relevance score check. The `scholar-search-kit` Crossref provider (`crossref.py:138`) checks `score > 40` but `BibResolver` does not.

**[FEAT-3] No `--format` export option** -- Cannot export to RIS, EndNote, or other formats. BibTeX is the only supported format.

**[FEAT-4] No `validate`/`check` command** -- No way to validate a BibTeX file for structural issues without linting it.

**[FEAT-5] No batch/file-list input for resolve** -- Can only resolve one `.bib` file at a time.

**[FEAT-6] No `--verbose`/`--quiet` flags** -- All commands have fixed output verbosity.

**[FEAT-7] No progress reporting for resolve** -- The `progress_callback` in `resolve_library()` is a no-op (`pass` at `cli.py:118`). No progress bar or percentage is shown.

**[FEAT-8] No structured output (JSON)** -- All output is human-readable console text. No `--json` flag for machine consumption.

#### 2.2.3 API Design Improvements

**[API-1] `BibParser` should support string parsing**
- `BibParser` only has `load(filepath)` and `save(library, filepath)`. There is no `parse_string(text)` static method, even though `bibtexparser.parse_string()` is used directly in `resolver.py:72`.

**[API-2] `BibResolver` should return results, not mutate in-place**
- `resolve_entry()` mutates the entry in-place and returns `None`. This is error-prone and makes it impossible to compare before/after. A better design returns a new `Entry` or a result object.

**[API-3] `BibDeduplicator.dedup()` should accept configuration**
- No way to configure dedup strategy (DOI-only, title-only, fuzzy threshold, case sensitivity).

**[API-4] `BibLinter.lint()` should accept a configuration object**
- Only `generate_keys` is configurable. No control over title wrapping style, key format, field normalization, etc.

**[API-5] Inconsistent error handling patterns**
- `BibParser.load()` has no error handling (raw exception propagation).
- `BibResolver.resolve_doi()` catches all exceptions and returns `None`.
- `BibResolver.resolve_search()` catches all exceptions and returns `None`.
- `BibDeduplicator.dedup()` has no error handling.
- `BibLinter.lint()` has no error handling.

#### 2.2.4 Error Handling Gaps

**[ERR-1] No file-existence check in `BibParser.load()`**
- Passing a non-existent path will raise an opaque `FileNotFoundError` from bibtexparser.

**[ERR-2] Silent failure on empty library**
- `cli.py:49-51` checks `if not input_files` but `cli.py:64` accesses `merged_library.entries` without checking if `merged_library is None` (the `for` loop body might never execute if `input_files` is empty after the guard).

**[ERR-3] Resolver swallows all errors silently**
- `resolver.py:22-24`, `resolver.py:43-44`, `resolver.py:86-87` catch `Exception` and either `pass` or `print` -- no way for callers to know resolution failed.

**[ERR-4] No validation of input file format**
- If the input is not a valid `.bib` file, `bibtexparser` may raise cryptic errors.

**[ERR-5] `resolve` CLI overwrites input on error**
- `cli.py:107` sets `output_file = input_file` by default. If `resolve_library()` fails partway through, the original file may be corrupted since `BibParser.save()` writes back to the same path.

**[ERR-6] `BibResolver` creates `AcademicHttpClient` but never closes it**
- `resolver.py:12` creates `self.http_client = AcademicHttpClient(...)` but there is no `__aenter__`/`__aexit__` or `close()` method. The HTTP session leaks.

#### 2.2.5 Documentation Needs

**[DOC-1] README.md is a stub** -- Only 3 lines: "# scholar-bib-kit" and "Part of the Nexus Scholar Suite."

**[DOC-2] API reference is entirely wrong** -- Describes non-existent classes and methods (see IMP-2).

**[DOC-3] Tutorial describes non-existent command** -- `scholar-bib fix` does not exist.

**[DOC-4] No CHANGELOG or version history**

**[DOC-5] No contribution guidelines**

---

### 2.3 Problems

#### 2.3.1 Known Bugs

**[BUG-1] Documentation/code mismatch is a blocking issue for agents**
- An agent reading `docs/api_reference.md` will attempt `from scholar_bib.validator import CrossrefValidator` and fail. This is the single most impactful problem because agents rely on docs.

**[BUG-2] `nexus_bib_clean` MCP tool was historically lint-only**
- Per `kits_surface_matrix.md:73-81`, this was documented as a known issue. It has been resolved in the MCP server, but the kit itself has no corresponding `clean()` convenience function that bundles lint + dedup.

**[BUG-3] `resolved.bib` contains incorrect search result**
- `resolved.bib:18-25` shows the "Attention Is All You Need" resolution matched to `DOI: 10.65215/r5bs2d54` (Shenzhen Medical Academy, 2025) instead of the actual Vaswani et al. 2017 paper. The resolver picks the first Crossref result without relevance validation.

**[BUG-4] `BibResolver.resolve_entry()` can corrupt entry on partial failure**
- `resolver.py:80`: `entry.fields_dict.clear()` is called before the new entry is fully verified. If the BibTeX string parsing at line 72-83 fails after the clear, the entry is left with zero fields.

#### 2.3.2 Edge Cases Not Handled

**[EDGE-1] Entries with no DOI and no title**
- `BibResolver.resolve_entry()` requires either a DOI or a title to attempt resolution. Entries with neither (e.g., only author + year) are silently skipped.

**[EDGE-2] Very long author lists**
- `linter.py:27` splits on ` and ` to get the first author. Author lists with ` and ` in affiliations or names (e.g., "Institute of Science and Technology") will be incorrectly split.

**[EDGE-3] Unicode in author names**
- `linter.py:34` strips all non-ASCII from author names with `re.sub(r'[^a-zA-Z]', '', first_author)`. Names with diacritics (e.g., "Muller" -> "Muller", "Garcia" -> "Garcia") are fine, but non-Latin scripts (CJK, Cyrillic, Arabic) produce empty keys.

**[EDGE-4] Entries with non-ASCII DOI characters**
- `deduplicator.py:7` cleans DOIs with `re.sub(r'[^a-z0-9]', '', str(s).lower())`. This is correct for standard DOIs but would strip URL-encoded characters.

**[EDGE-5] Concurrent modification during dedup**
- `deduplicator.py:38-40` modifies `target_entry` while iterating over the duplicate's fields. This is safe with bibtexparser v2's dict-like `fields_dict`, but would be problematic if the library is shared.

**[EDGE-6] Merge with duplicate keys across files**
- `cli.py:61-62` adds blocks by reference. If two files have entries with the same key but different content, both are added (no key collision check). `BibDeduplicator` only deduplicates by DOI/title, not by key.

**[EDGE-7] `asyncio.run()` in `resolve` CLI**
- `cli.py:121` calls `asyncio.run(run_resolve())`. This is correct for a fresh event loop, but if the kit is ever called from an already-running async context (e.g., from an MCP server), this will fail with "RuntimeError: This event loop is already running."

#### 2.3.3 Limitations

**[LIM-1] No fuzzy dedup** -- Title dedup is exact (after cleaning). Typos, abbreviation differences, or subtitle variations produce false negatives.

**[LIM-2] No author-based dedup** -- Two entries for the same paper with different DOIs (e.g., preprint vs. published) are not caught.

**[LIM-3] No field normalization** -- Author names, journal abbreviations, and date formats are not standardized.

**[LIM-4] BibTeX-only** -- No RIS, EndNote, CSV, or JSON import/export.

**[LIM-5] Single-threaded HTTP** -- Despite using `asyncio`, the resolver does not use connection pooling or concurrent connection limits beyond the rate limiter.

---

### 2.4 Optimizations

#### 2.4.1 Performance Bottlenecks

**[OPT-1] Sequential file loading in merge**
- `cli.py:55-62` loads files one at a time in a `for` loop. For large bibliographies (10k+ entries), this could be parallelized with `asyncio.gather()` or `concurrent.futures`.

**[OPT-2] O(n^2) potential in dedup**
- `deduplicator.py:28-33` does O(1) dict lookups per entry, which is good. However, the `unique_entries` list is scanned linearly for field grafting (`unique_entries[target_idx]`), and the list is rebuilt at the end. For very large libraries (100k+ entries), the list operations could be optimized.

**[OPT-3] Unbounded concurrency in resolver**
- `resolver.py:91-93` creates all resolve tasks upfront and runs them with `as_completed()`. With a library of 10,000 entries, this creates 10,000 concurrent HTTP requests. The rate limiter (10/s) throttles but the task objects themselves consume memory.

**[OPT-4] No connection pooling**
- Each `BibResolver` instance creates a new `AcademicHttpClient`. If multiple resolvers are instantiated (e.g., in a pipeline), each has its own connection pool.

#### 2.4.2 Caching Opportunities

**[CACHE-1] Crossref DOI resolution**
- `resolve_doi()` fetches the same DOI multiple times if it appears in different entries. The `AcademicHttpClient` uses `hishel` caching, but the cache key includes the full URL. Identical DOIs would hit the cache, but the overhead of URL construction and cache lookup per request is unnecessary.

**[CACHE-2] Title search results**
- `resolve_search()` queries Crossref for each title. If the same title appears in multiple entries (e.g., duplicates before dedup), the same search is performed repeatedly.

#### 2.4.3 Parallelization Potential

**[PAR-1] Library-level dedup**
- The dedup algorithm is inherently sequential (order-dependent for field grafting). However, the initial DOI/title map building could be parallelized, followed by a sequential merge pass.

**[PAR-2] Lint operations**
- Each entry's linting is independent. The `lint()` method could process entries in parallel with `concurrent.futures.ThreadPoolExecutor`.

---

### 2.5 Scientific Correction

#### 2.5.1 BibTeX Parsing Accuracy

**[SCHOL-1] bibtexparser v2 beta**
- The kit pins `bibtexparser>=2.0.0b7` (actual installed: `2.0.0b9`). This is a beta version of a major rewrite. Known issues include:
  - Stripping of outer braces from titles (partially addressed by the linter).
  - Inconsistent handling of `@string` and `@preamble` directives.
  - Potential data loss on round-trip for entries with unusual formatting.

**[SCHOL-2] Title brace wrapping is incomplete**
- `linter.py:17` checks `if not (title.startswith('{') and title.endswith('}'))` -- this catches single-brace wrapping (`{Title}`) but not nested braces (`{{Title}}`). The bibtexparser v2 beta may strip outer braces, leaving `{{Title}}` as `{Title}`, which the linter would then re-wrap to `{{{Title}}}`.

**[SCHOL-3] Crossref BibTeX is not standardized**
- Crossref's `application/x-bibtex` format uses its own field naming (e.g., `ISSN` instead of `issn`, mixed-case field names). The kit does not normalize these after resolution.

#### 2.5.2 Reference Format Compliance

**[SCHOL-4] DOI normalization is minimal**
- `resolver.py:59` only strips `https://doi.org/` and `http://doi.org/` prefixes. It does not handle:
  - `doi:` prefix (common in some tools)
  - URL-encoded DOIs
  - DOIs with trailing slashes or query parameters
  - `10.` prefix validation

**[SCHOL-5] Key generation does not handle edge cases**
- `linter.py:34` strips non-alpha from author names, producing empty strings for numeric-only names. `linter.py:35` strips non-digits from year, but does not validate the year is a reasonable academic year (e.g., 1900-2099).

#### 2.5.3 Citation Style Correctness

**[SCHOL-6] No citation style enforcement**
- The kit does not enforce any citation style (APA, Chicago, IEEE, etc.). It focuses on BibTeX structural hygiene, not bibliography formatting.

**[SCHOL-7] Journal name normalization is absent**
- Abbreviated vs. full journal names are not standardized. "J. Mach. Learn. Res." and "Journal of Machine Learning Research" are treated as different values.

#### 2.5.4 Academic Standards Adherence

**[SCHOL-8] No retraction/correction awareness**
- The kit does not check whether resolved DOIs correspond to retracted papers. This is handled by `scholar-verify-kit` but is not integrated into the resolution pipeline.

**[SCHOL-9] No open-access metadata enrichment**
- Resolved entries from Crossref do not include open-access status, license, or version information.

---

### 2.6 Agent/Skill Recommendation

#### 2.6.1 Should a specialized agent or skill be created?

**Current state:** A `scholar-bib-kit` skill already exists at `.agents/skills/scholar-bib-kit/SKILL.md` (110 lines). It is well-structured and covers CLI usage, Python API, and agent guidelines.

**Recommendation: No new skill is needed. The existing skill is sufficient but needs updates to match the actual API.**

However, the kit's scope is narrow enough that a **dedicated agent** could add value if the following conditions are met:

1. **The documentation is fixed** -- An agent reading stale docs will fail.
2. **The resolve pipeline needs orchestration** -- Currently, the `resolve` command is a black box. An agent could provide intelligent resolution strategies (e.g., "resolve only entries missing DOIs", "resolve but preserve existing fields", "resolve with confidence threshold").

#### 2.6.2 Evaluation Metrics for Agent

If a bib-kit agent were created, these metrics would be relevant:

| Metric | Definition | Target |
|:--|:--|:--|
| `bib_parse_success_rate` | % of `.bib` files parsed without errors | >99% |
| `bib_dedup_precision` | % of detected duplicates that are true duplicates | >95% |
| `bib_dedup_recall` | % of true duplicates that are detected | >90% |
| `bib_resolve_accuracy` | % of resolved entries matching the correct paper | >85% |
| `bib_resolve_coverage` | % of entries successfully resolved | >70% (for messy inputs) |
| `bib_lint_idempotency` | Running lint twice produces identical output | 100% |
| `bib_roundtrip_fidelity` | load -> save -> load produces identical Library | 100% |
| `bib_key_uniqueness` | Generated keys are unique within the library | 100% |

#### 2.6.3 Critic Capabilities Needed

A bib-kit critic should check:
1. **Stale documentation** -- Verify that all documented classes/methods/commands exist in the code.
2. **Resolution quality** -- Verify that Crossref-resolved entries match the original intent (title similarity, year consistency, author overlap).
3. **Dedup correctness** -- Verify that removed entries were true duplicates and no entries were incorrectly merged.
4. **Key uniqueness** -- Verify that generated citation keys are unique and meaningful.
5. **Roundtrip safety** -- Verify that `load -> process -> save -> load` produces equivalent results.

#### 2.6.4 Agent-in-the-Loop Opportunities

| Opportunity | Description | Priority |
|:--|:--|:--|
| Resolution review | Agent reviews Crossref matches before accepting | High |
| Dedup conflict resolution | Agent decides when two entries are "similar enough" | Medium |
| Field merging strategy | Agent decides which fields to keep when duplicates have conflicting values | Medium |
| Key generation review | Agent reviews generated keys for meaningfulness | Low |

#### 2.6.5 Automation Potential

| Automation | Description | Complexity |
|:--|:--|:--|
| Pre-commit bib lint | Auto-lint `.bib` files on commit | Low |
| CI bib validation | Validate `.bib` files in CI pipeline | Low |
| Batch resolve with progress | Resolve large libraries with progress reporting | Medium |
| Smart dedup with fuzzy matching | Use embeddings or string similarity for dedup | High |

---

## 3. Priority-Ranked Improvement Suggestions

### Priority 1 (Critical -- Blocking)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| IMP-2 | **Fix documentation to match actual API** -- Rewrite `docs/api_reference.md` and `docs/tutorial.md` to describe `BibParser`, `BibLinter`, `BibDeduplicator`, `BibResolver` and the `lint`/`merge`/`dedup`/`resolve` commands. | 2h | Critical -- agents and developers rely on docs |
| BUG-1 | **Remove stale Crossref/Repair class references** -- Delete references to `CrossrefValidator`, `RepairEngine`, `BibEntry`, `RepairStats` from docs. | 1h | Critical -- prevents import errors |
| ERR-5 | **Add output-before-overwrite safety** -- Write to a temp file first, then rename on success. Prevents data loss on partial failure. | 4h | Critical -- data loss prevention |

### Priority 2 (High -- Important)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| IMP-1 | **Replace print() with logging** -- Use `logging` module throughout `resolver.py`. Remove all debug prints. | 2h | High -- production readiness |
| ERR-3 | **Add structured error reporting** -- Return success/failure per entry from resolver. Log failures. | 4h | High -- observability |
| BUG-3 | **Add relevance score check to resolver** -- Use Crossref's `score` field to filter low-confidence matches. Add configurable threshold. | 4h | High -- scientific accuracy |
| BUG-4 | **Fix entry corruption on partial failure** -- Do not clear entry fields until new entry is fully parsed. | 2h | High -- data integrity |
| ERR-6 | **Add context manager to BibResolver** -- Implement `__aenter__`/`__aexit__` to properly close HTTP client. | 2h | High -- resource leak |

### Priority 3 (Medium -- Nice to Have)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| FEAT-7 | **Add progress reporting for resolve** -- Show progress bar using `rich.progress`. | 4h | Medium -- user experience |
| FEAT-6 | **Add --verbose/--quiet flags** -- Control output verbosity. | 2h | Medium -- usability |
| IMP-3 | **Remove unused pydantic dependency** -- Or implement validation models. | 1h | Medium -- dependency hygiene |
| IMP-4 | **Add public API re-exports to __init__.py** -- `from scholar_bib import BibParser, BibLinter, ...` | 1h | Medium -- API ergonomics |
| EDGE-3 | **Handle non-Latin author names in key generation** -- Fall back to entry key or generate hash. | 2h | Medium -- internationalization |
| LIM-1 | **Add fuzzy title dedup** -- Use string similarity (Levenshtein, Jaccard) for title comparison. | 8h | Medium -- dedup quality |
| SCHOL-4 | **Expand DOI normalization** -- Handle `doi:` prefix, URL-encoded DOIs, trailing slashes. | 2h | Medium -- robustness |

### Priority 4 (Low -- Future Work)

| ID | Improvement | Effort | Impact |
|:--|:--|:--|:--|
| FEAT-3 | **Add RIS/EndNote/JSON export** -- Multi-format output support. | 16h | Low -- niche use case |
| FEAT-4 | **Add validate/check command** -- Structural validation without modification. | 4h | Low -- nice to have |
| OPT-1 | **Parallelize merge file loading** -- Use async or threading for large file sets. | 4h | Low -- perf at scale |
| OPT-3 | **Add concurrency limits to resolver** -- Use `asyncio.Semaphore` to cap parallel requests. | 2h | Low -- memory at scale |
| LIM-6 | **Add field normalization** -- Standardize author names, journal abbreviations, date formats. | 16h | Low -- quality of life |

---

## 4. File Inventory with Line References

| File | LOC | Purpose | Key Issues |
|:--|:--|:--|:--|
| `src/scholar_bib/__init__.py` | 1 | Package marker | Empty -- no public API exports |
| `src/scholar_bib/cli.py` | 127 | Typer CLI with 4 commands | No type hints; progress callback is no-op; overwrite safety missing |
| `src/scholar_bib/parser.py` | 14 | BibTeX load/save wrapper | No string parsing; no error handling |
| `src/scholar_bib/linter.py` | 50 | Title wrapping + key generation | Unicode edge cases; single key mode |
| `src/scholar_bib/deduplicator.py` | 60 | DOI + title dedup | No fuzzy matching; no config |
| `src/scholar_bib/resolver.py` | 100 | Crossref resolution | Debug prints; no confidence check; resource leak; entry corruption risk |
| `tests/test_bib.py` | 61 | Basic unit tests | Only 2 test functions; no resolver tests; no edge case coverage |
| `docs/api_reference.md` | 57 | API documentation | **Entirely wrong** -- describes non-existent classes |
| `docs/tutorial.md` | 40 | Tutorial | **Entirely wrong** -- describes non-existent command |
| `README.md` | 3 | Package README | Stub -- no useful content |

---

## 5. Cross-Reference: Kit vs. Surface Matrix

The `kits_surface_matrix.md` (lines 212-225) documents these known facts about `scholar-bib-kit`:

| Surface Matrix Claim | Verified? | Notes |
|:--|:--|:--|
| `BibParser.load/save` (bibtexparser v2) | Yes | `parser.py:7-14` |
| `BibLinter.lint(lib, generate_keys=False)` -- only AuthorYear key mode | Yes | `linter.py:6-50` |
| `BibDeduplicator.dedup` -- cleaned-DOI first, then cleaned-title; survivor = first occurrence | Yes | `deduplicator.py:11-60` |
| `BibResolver.resolve_doi/search/entry/library` -- async, Crossref x-bibtex, replaces whole entry | Yes | `resolver.py:14-100` |
| CLI: lint/merge/dedup/resolve | Yes | `cli.py:23-124` |
| lint/dedup/resolve overwrite input in place when --output omitted | Yes | `cli.py:30-31,80-81,106-107` |
| merge default output = CWD merged.bib | Yes | `cli.py:45` |
| MCP: `nexus_bib_clean` = in-place lint only | Was true, now resolved | See matrix finding 4 |
| bibtexparser 2.0.0b9 (beta) | Yes | `pyproject.toml:17` |
| title brace-wrapping idempotent | Partially -- see SCHOL-2 | |
| DOI normalization only strips `https?://doi.org/` | Yes | `resolver.py:59` |
| pydantic declared-but-unused | Yes | `pyproject.toml:18` |
| print()-based output in resolve | Yes | 10 print statements in resolver.py |

---

*Analysis generated 2026-09-14 by deep-dive file sweep of `tools/scholar-bib-kit/`.*
