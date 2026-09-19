# Scholar Bib Kit Remediation Specification

## Metadata

- Status: Draft for implementation
- Date: 2026-09-17
- Scope: `tools/scholar-bib-kit` and bibliography-facing MCP/harness adapters
- Evidence convention: **Confirmed** findings cite checkout lines; **Hypothesis** items require tests.

## Problem and safety boundary

Bibliographic cleanup changes citation identity and can silently corrupt the evidence map. In-place writes, first-hit deduplication, and wholesale remote replacement currently lack durable provenance. Remediation MUST preserve the original on failure, expose every merge/resolution decision, and never invent DOI, title, author, venue, year, or resolution confidence. Remote candidates are suggestions until identity checks pass.

## Architecture and data flow

`BibParser` loads/writes bibtexparser v2 libraries (`tools/scholar-bib-kit/src/scholar_bib/parser.py:1-14`). `BibLinter` normalizes title braces and optionally keys. `BibDeduplicator` indexes cleaned DOI then cleaned title, keeps the first entry and grafts missing fields (`tools/scholar-bib-kit/src/scholar_bib/deduplicator.py:9-60`). `BibResolver` queries Crossref through search-kit's HTTP client and mutates entries (`tools/scholar-bib-kit/src/scholar_bib/resolver.py:8-100`). CLI `lint`, `merge`, `dedup`, and `resolve` persist results (`tools/scholar-bib-kit/src/scholar_bib/cli.py:23-124`).

## Confirmed findings

1. `lint`, `dedup`, and `resolve` default to overwriting input (`tools/scholar-bib-kit/src/scholar_bib/cli.py:23-40`, `:74-95`, `:98-124`). `BibParser.save` delegates directly to `write_file` with no atomic staging (`tools/scholar-bib-kit/src/scholar_bib/parser.py:11-14`).
2. DOI normalization removes every non-alphanumeric character (`tools/scholar-bib-kit/src/scholar_bib/deduplicator.py:5-7`, `:22-33`), a non-standard identity transform that can collapse syntactically distinct strings; it does not validate DOI syntax.
3. Dedup matches by DOI, else exact cleaned title, keeps the first occurrence, and fills only absent fields (`tools/scholar-bib-kit/src/scholar_bib/deduplicator.py:18-48`). Conflicting populated fields and match reasons are not recorded.
4. Resolver catches failures and returns `None`, including a silent title-search catch (`tools/scholar-bib-kit/src/scholar_bib/resolver.py:14-45`), so not-found and provider failure are indistinguishable.
5. Resolver prints DOI responses and internal fields (`tools/scholar-bib-kit/src/scholar_bib/resolver.py:18-23`, `:47-75`) rather than returning structured diagnostics; response snippets may expose unexpected upstream content.
6. A resolved Crossref entry clears all original fields and replaces them wholesale, preserving only the key (`tools/scholar-bib-kit/src/scholar_bib/resolver.py:69-83`). Local notes, provenance, file links, and conflicting metadata can be lost.
7. Resolver creates `AcademicHttpClient` (`tools/scholar-bib-kit/src/scholar_bib/resolver.py:8-12`) but exposes no close/context-manager path; CLI does not close it (`tools/scholar-bib-kit/src/scholar_bib/cli.py:114-121`).
8. Resolution schedules one coroutine per entry without a toolkit-level concurrency bound (`tools/scholar-bib-kit/src/scholar_bib/resolver.py:89-98`); HTTP rate limiting alone does not bound task memory.
9. `bibtexparser` uses a pre-release-compatible lower bound and search-kit is a direct dependency (`tools/scholar-bib-kit/pyproject.toml:14-20`); the verified matrix reports the resolved lock at 2.0.0b9 and MCP clean as in-place lint only (`docs/kits_surface_matrix.md:212-225`).
10. Dedup identity is non-transitive. A reproduced sequence `A(title=T)`, `B(doi=D,title=U)`, `C(doi=D,title=T)` leaves two survivors because the bridge merges into one existing representative without unioning both DOI/title components (`deduplicator.py:28-48`).
11. Resolver accepts the first Crossref search result without score, title, author, or year verification (`resolver.py:27-42`), even though search-kit already contains a scored Crossref validation hook. Unrelated metadata can therefore replace an entry.
12. Shipped tutorial/API documentation describes nonexistent `scholar-bib fix`, flags, and classes, while the README is effectively empty. The operational surface cannot be inferred safely from current docs.
13. Only two shallow toolkit tests were present and passed; resolver, CLI, failure, transitive identity, conflict, key collision, and atomicity behavior have no meaningful regression coverage.

Hypotheses to verify: generated `AuthorYear` keys may collide and block/comment ordering may change after dedup/save. These require dedicated fixtures before prescribing an algorithm.

## Goals and non-goals

Goals: transactional bibliography writes; standards-aware identity; explainable dedup/resolution; preservation of local fields and blocks; structured outcomes; bounded concurrency and cleanup. Non-goals: automatically deciding ambiguous citation identity, rewriting citation keys without an alias map, or treating Crossref as infallible ground truth.

## Normative requirements

Requirement IDs: the numbered requirements below carry stable IDs `BIB-001`…`BIB-018`
(requirement *n* = `BIB-0nn`). Regression tests and the traceability ledger required
by `11_validation_and_test_plan.md` (VAL-001, §11–§12) MUST reference these IDs.

1. Every save MUST serialize to a same-directory temporary file, parse and validate it, flush/close it, then atomically replace the target.
2. In-place CLI operation MUST require explicit `--in-place` or preserve the current default only during a deprecation window with a prominent warning and backup-independent atomicity.
3. Lint/dedup/resolve MUST return versioned structured outcomes with input/output counts, changed keys, warnings, errors, and commit status.
4. DOI normalization MUST strip recognized wrappers, normalize case where appropriate, preserve DOI-significant punctuation, and distinguish invalid from missing values.
5. Dedup MUST report match basis, normalized values, survivor rule, merged fields, and conflicts. Ambiguous matches MUST remain separate pending review.
6. Conflicting non-empty fields MUST never be silently overwritten or discarded.
7. Resolver MUST distinguish `resolved`, `not_found`, `ambiguous`, `invalid_input`, `provider_failed`, `parse_failed`, and `unchanged`.
8. Title-search resolution MUST enforce documented title/author/year checks before accepting a remote candidate. Scores/evidence MUST be retained.
9. Remote resolution MUST merge allowed fields into the original entry; local-only fields and original values MUST remain in provenance/conflict records.
10. All owned HTTP clients MUST close on success, failure, and cancellation; resolver SHOULD implement async context management.
11. Resolution concurrency MUST be bounded and configurable independently of request rate.
12. Debug output MUST use logging with redaction; library code MUST not print response bodies or entry internals.
13. Citation-key changes MUST be deterministic, collision-safe, and accompanied by old-to-new aliases.
14. Comments, preambles, string blocks, and stable ordering SHOULD survive parse-transform-save unless the user explicitly requests canonical reformatting.
15. MCP `clean` MUST accurately describe lint-only behavior or expose explicit lint/dedup/key-generation options; it MUST not overwrite implicitly.
16. No remote field or identifier MAY be fabricated to complete an entry.
17. Dedup MUST compute connected identity components across every accepted DOI/title edge. A bridging entry MUST union all previously separate components before representative election.
18. Crossref resolution MUST reject or mark ambiguous candidates that do not meet a documented score plus title/author/year agreement policy; the first result is not inherently authoritative.

## API, data, and CLI behavior

Add `BibliographyOperationOutcome`, `EntryChange`, `DedupDecision`, and `ResolutionOutcome` schemas. Existing APIs MAY continue returning `Library` through deprecated convenience methods, but new methods MUST return the library plus outcome. Provide normalized DOI parsing as a public, independently tested function. Resolver candidate acceptance must be separable from lookup for deterministic testing.

CLI defaults SHOULD write to an explicit derived output unless `--output` or `--in-place` is supplied. `--json-summary` MUST expose changes and unresolved items. Exit nonzero for parse/write failure or complete resolver failure; partial resolution must remain distinguishable. Human output MUST not imply that unresolved entries were verified.

## Migration and backward compatibility

- First release: atomic saves everywhere; warn on implicit in-place behavior; add structured APIs alongside existing returns.
- Next major release: require `--in-place`; make structured outcomes primary.
- Preserve old keys by default. If regeneration is requested, emit an alias map usable by manuscripts.
- Accept existing BibTeX without added provenance; provenance MAY live in a sidecar to avoid polluting bibliography fields.
- Coordinate search HTTP-client changes, agent MCP updates, canonical kit repo, vendored snapshot, and pin.

## Delivery plan

### P0

1. Implement atomic validated save and failure preservation.
2. Add structured resolver outcomes; remove broad silent failure and prints.
3. Preserve original/local fields during resolution and record conflicts.
4. Close clients reliably and bound concurrency.
5. Implement standards-aware DOI normalization and explainable dedup decisions.
6. Replace first-match dedup with connected-component union and add bridge/permutation regressions.
7. Add conservative Crossref candidate validation before any merge.

### P1

1. Deprecate implicit in-place operations and add JSON summaries.
2. Add remote candidate identity thresholds and ambiguous-review output.
3. Make key generation collision-safe with aliases.
4. Align MCP naming/options/persistence semantics.

### P2

1. Improve block/order round-trip fidelity and add explicit canonical-format mode.
2. Pin a stable bibtexparser release when available after compatibility testing.

## Failure-focused test matrix

| Area | Cases | Required assertion |
|---|---|---|
| Save | disk full, serialization error, interruption, destination exists | original intact; no partial final |
| Parse | malformed entry, duplicate key, comments/preamble/string blocks | diagnostic outcome; no destructive write |
| DOI | URL/prefix/case, punctuation, malformed, lookalike strings | standards-aware identity; no false collapse |
| Dedup | same DOI/conflicting title, same title/different DOI, bridge, missing fields | explainable safe decision; conflicts retained |
| Keys | same author/year, non-ASCII, missing author/year, rerun | deterministic unique keys; alias map; idempotence |
| Resolver | 404, timeout, 429, malformed BibTeX, no candidates, ambiguous title | distinct status; original unchanged where unsafe |
| Merge | conflicting fields, local notes/file fields, entry type change | allowed merge only; provenance complete |
| Concurrency | large library, cancellation, callback failure | bounded tasks; client closed; no half-write |
| CLI/MCP | default, explicit output, in-place, JSON summary | consistent semantics and truthful exit/status |
| Round trip | all block types and ordering fixtures | no unintended evidence loss |

## Definition of done

All P0 tests pass; destructive failure injection never changes the original bibliography; every dedup and remote resolution is explainable; unresolved/ambiguous/provider-failed are distinct; no client leaks or library `print()` calls remain; existing suites and cross-kit consumers pass; canonical repo, vendored tree, and pinned revision are synchronized.

## Dependencies and risks

The resolver depends on search-kit's HTTP semantics (`tools/scholar-bib-kit/pyproject.toml:19-20`). Parser beta behavior may constrain round-trip fidelity. Safer dedup will retain more ambiguous duplicates, which is preferable to evidence loss but changes counts. Key aliases require integration with manuscript tooling.

## Documentation updates

Update README, tutorial, API reference, `.agents/skills/scholar-bib-kit/SKILL.md`, and `docs/kits_surface_matrix.md` with atomic/in-place semantics, outcome schemas, DOI rules, merge conflict policy, resolver acceptance criteria, cleanup, key aliases, MCP scope, and migration examples.
