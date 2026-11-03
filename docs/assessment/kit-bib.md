# scholar-bib-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-bib-kit`). Scope: `tools/scholar-bib-kit/src/scholar_bib/` (6 modules, 352 lines by `wc -l`), `tests/` (2 modules, about 130 lines), `docs/`, `README.md`, `pyproject.toml`. Harness consumers: `src/scholar_harness/` grep for `scholar_bib`. Method: read all source and tests in full. Ran `uv run pytest tools/scholar-bib-kit/tests` (4 passed, 1 skipped). Ran an offline repro script (scratchpad `bib_repro.py`; results B1–B12) against the shared `.venv`, which has bibtexparser 2.1.0. The resolver was exercised with its two network methods stubbed, so no network call was made. Docs were treated as claims to check, not as evidence.

## 1. Verdict

This is a thin wrapper of about 350 lines around bibtexparser v2. In its current state it is not fit for reference management in a publishable review; it is more likely to damage a `.bib` file than repair it. Both deduplication rules produce silent false merges: a punctuation-stripped DOI key that collides for distinct DOIs (BIB-02), and exact-title matching that overrides differing DOIs (BIB-01). In both cases fields are grafted from the other work and the losing cite key disappears with no mapping. The Crossref resolver accepts the top-1 search hit without any check. Because of a no-op `fields_dict.clear()`, it then produces a hybrid record that mixes the wrong paper's metadata with the original's stale fields (BIB-03). Every mutating command overwrites the input in place by default. Key generation can emit duplicate keys and strips accented letters. There are two behavioural tests, and both assert only entry counts. The harness does not use the kit at all.

| Lens | Rating | Reason |
|---|---|---|
| Code quality & architecture | Weak | Debug `print()` calls in library code, swallowed exceptions, a git-pinned dependency on the whole search kit just for an HTTP client, an eagerly imported resolver, and no result or report types. |
| Correctness & bugs | Failing | Reproduced silent false merges, a hybrid-record resolver, duplicate generated keys, and a crash when merging files that share a key. |
| Research-method fitness | Failing | No reference-integrity features (validation, retraction status, key-change mapping, links to included studies). Its defaults destroy provenance. |

## 2. Architecture and code quality

- **No outcome reporting.** `BibDeduplicator.dedup` returns only a new `Library` (`deduplicator.py:50-60`). Callers never learn which entries were merged, into which survivor, on which rule (DOI or title), or which fields were grafted. The resolver mutates entries in place and returns nothing about success, failure or what changed (`resolver.py:47-87`). A review tool needs an audit trail for every merge and overwrite. This design cannot provide one.
- **Library code prints to stdout.** There are nine `print()` debug statements in `resolver.py` (lines 19, 23, 33, 39, 49, 54, 60, 75, 85). One of them dumps the response body (`resolver.py:19`). Exceptions are swallowed with `except Exception` (`resolver.py:22,43,86`), so a failed lookup is indistinguishable from "nothing to do".
- **Coupling.** `resolver.py:6` imports `scholar_search.http_client.AcademicHttpClient`. As a result the kit declares a git-pinned dependency on all of scholar-search-kit (`pyproject.toml`). `cli.py:10` imports the resolver at module level, so even `scholar-bib lint` fails if scholar-search-kit is missing. `pydantic` is a declared dependency but is not used anywhere in `src/`.
- **Concurrency.** `resolve_library` creates one task per entry at once (`resolver.py:89-100`) and relies on the client's 10 req/s limiter. There is no retry policy, no cache, and no `mailto` handling visible in the kit.
- **Dead or placeholder code.** The `resolve` CLI command defines a no-op `update_progress` and an unused `status` variable (`cli.py:116-119`).
- **Tests.** `tests/test_bib.py` has two tests on one hand-written fixture:
  - `test_bib_parser_and_linter` asserts only that 3 entries survive a lint round-trip, not what the keys or titles became.
  - `test_bib_deduplicator` asserts only that the count goes from 3 to 2, not which entry survived or which fields were merged.

  Nothing tests the resolver, the CLI, `merge`, duplicate keys, malformed entries, `@string`, Unicode names, or any negative case for dedup. `test_standalone_packaging.py` is skipped unless a wheel has been built. Coverage is far from adequate for a tool that rewrites bibliographic data in place.

## 3. Correctness and bugs

**BIB-01 — Critical — Reproduced (B3, B3b).** Exact-title match overrides differing DOIs and merges distinct works.
- **Evidence:** The title branch runs whenever the DOI is not already in the map (`deduplicator.py:28-33`). It runs even when both entries carry *different* DOIs. In B3, `@inproceedings{conf …doi=10.1109/conf.2021.1, year=2021, booktitle=ICRA}` and `@article{jour …doi=10.1016/j.jour.2023.2, year=2023, journal=Robotics}`, which share a title, collapsed to `['conf']`. The survivor kept the conference DOI and year but was given `journal=Robotics`, grafted from the other work (`deduplicator.py:38-40`). In B3b, two different `Editorial` entries (different authors, years and journals) collapsed to one.
- **Impact:** In a large exported library, the conference and journal versions of a paper, generic titles (Editorial, Introduction, Reply, Erratum) and same-titled retraction notices are silently merged into a chimeric record. The removed key (`jour`) vanishes, so any `\cite{jour}` in the manuscript breaks.

**BIB-02 — High — Reproduced (B1, B2).** DOI normalization is wrong in both directions.
- **Evidence:** `_clean_string` removes every non-`[a-z0-9]` character (`deduplicator.py:5-7`), so `10.1234/5678` and `10.12345/678` both become `1012345678`. In B1, two different papers collapsed to `['a']`. Conversely, `https://doi.org/10.1000/XYZ` normalizes to `httpsdoiorg101000xyz`, which does not match bare `10.1000/xyz`. In B2, both entries were kept.
- **Impact:** False merges, where data is lost, and missed duplicates. Correct DOI handling means stripping the resolver prefix and `doi:`, then case-folding, and nothing more. DOI suffixes are opaque and punctuation is significant.

**BIB-03 — Critical — Reproduced with stubs (B12) / Static for network.** The resolver silently replaces an entry with an unverified Crossref hit and leaves stale fields behind.
- **Evidence:**
  - Search fallback takes `rows=1` and accepts `items[0]` with no title or author similarity check and no score threshold (`resolver.py:30,38`).
  - The overwrite does `entry.fields_dict.clear()` (`resolver.py:80`). In bibtexparser 2.x, `fields_dict` is a property that returns a *fresh* dict, so the clear is a no-op. `set_field` then overwrites only the keys Crossref returned.
  - In B12, an entry `{title=My Real Paper, author=Me, year=2022, note=retracted 2023, keywords=uav}` resolved against a stubbed unrelated record became `{title: 'An Unrelated Paper', author: 'Other, A.', year: '2019', note: 'retracted 2023', keywords: 'uav', doi: '10.9/unrelated', …}`, still under the original key `mine`.
  - It also re-resolves entries that already have a DOI and overwrites the curated metadata (`resolver.py:57-61`).
  - DOI cleaning strips only `http(s)://doi.org/` (`resolver.py:59`). It misses `doi:` and `dx.doi.org`, and the DOI is put in the URL path unescaped (`resolver.py:16`).
- **Impact:** A citation silently points to a different paper while keeping the original key and some of its original fields. Combined with the in-place default (BIB-04), there is no recovery except version control. This is the worst failure a reference tool can have in a systematic review.

**BIB-04 — High — Static + Reproduced (B4).** Destructive in-place defaults with no record of what changed. `lint`, `dedup` and `resolve` write back to the input when `--output` is omitted (`cli.py:31,81,107`). They make no backup, write no change log, and output no old-key to new-key mapping, whether for keys removed by dedup or keys renamed by `--generate-keys`. Removed or renamed keys break `\cite{}` commands in the manuscript with no trace.

**BIB-05 — High — Reproduced (B5, B6).** `--generate-keys` creates duplicate keys and mangles names.
- **Evidence:** `existing_keys` holds only *already processed* keys (`linter.py:42,48`), so a generated key can collide with a later entry's original key. In B5, `[x (Smith, John 2020), Smith2020]` became `['Smith2020','Smith2020']`. On reload, bibtexparser demoted the second entry to a `DuplicateBlockKeyBlock` (entries: `['Smith2020']`), so one reference was effectively lost. `re.sub(r'[^a-zA-Z]', '', …)` (`linter.py:34`) turns Müller into `Mller2020` and García Márquez into `Mrquez2021`, and `{World Health Organization}` becomes `Organization2020` (B6). The `while … and new_key != entry.key` guard (`linter.py:42`) adds nothing useful. Suffixes run past `z` into punctuation.

**BIB-06 — Medium — Reproduced (B10).** `merge` crashes on the most common real-world input, namely two files that share a cite key. `merged_library.add(block)` (`cli.py:62`) uses bibtexparser's default `fail_on_duplicate_key=True`. In B10 the command exited 1 with `ValueError: Duplicate keys found: ['smith2020']` before any dedup could run.

**BIB-07 — Medium — Reproduced (B8, B9).** Parse problems are invisible. Within a single file, a duplicate key turns the second entry into a `DuplicateBlockKeyBlock` (B9: only `('dup','First paper')` remains in `entries`), and lint, dedup and resolve then never see it. Malformed entries become failed blocks. The kit never reports `library.failed_blocks`; `BibParser.load` (`parser.py:7-9`) returns the library as-is, and the CLI prints only the count of entries it did parse.

**BIB-08 — Low — Reproduced (B7).** The title "protection" heuristic is inconsistent. `linter.py:17` skips wrapping when the value starts with `{` and ends with `}`. So `{BERT}: Pre-training of {Transformers}` is left single-braced while `A study of {GPT}` becomes `{{A study of {GPT}}}`. Wrapping whole titles in braces is also a known anti-pattern for styles that require sentence case (APA, many journal styles), and the kit applies it unconditionally.

**BIB-09 — Low — Reproduced (B11).** On write, `@string` macro usages are expanded inline (`journal = {IEEE Transactions}`) while the `@string` definition is kept. The bibtexparser default middleware therefore rewrites the user's file structure even under `dedup` alone. `dedup` also moves all non-entry blocks (comments, preamble, strings) ahead of every entry (`deduplicator.py:54-58`).

## 4. Research-method fitness

What a systematic review needs from a bibliography tool, against what the kit provides:

| Need | Provided? | Note |
|---|---|---|
| Lossless, auditable deduplication (DOI-first, conservative title matching, a log of every merge) | No | BIB-01, BIB-02 and BIB-04. No log or report exists. |
| Verified metadata enrichment (match confidence, only fill missing fields, keep the original) | No | BIB-03: top-1 hit, overwrite, hybrid record. |
| Reference validation (required fields per entry type, DOI syntax, year sanity, encoding) | No | The `BibLinter` "lint" (`linter.py:4-50`) only brace-wraps titles and optionally rekeys. It checks nothing. |
| Retraction or correction status of cited works | No | Not in this kit. scholar-verify-kit covers retraction for included studies, but nothing links it to the `.bib`. |
| Stable cite keys, with a mapping when keys change | No | BIB-05 and BIB-04. |
| Link between the included-studies set and the bibliography | No | The harness never imports `scholar_bib`. The only reference is a portability alias, `src/scholar_harness/skills_portability/variables.py:150`. The LaTeX/Typst export reads `literature/references.bib` or `synthesis/references.bib` (`src/scholar_harness/cli.py:934-936`), produced elsewhere, with no integrity check. |

For a sole reviewer, a silent false merge in the bibliography means a citation in the published review points to the wrong study, and no second reviewer will catch it. Until BIB-01 to BIB-04 are fixed, the safe use of this kit is "do not run `dedup` or `resolve` on a bibliography you care about". If `lint` is used at all, write to a separate `--output` and check the diff.

## 5. Doc drift

- `tools/scholar-bib-kit/docs/api_reference.md:18-56` documents `scholar_bib.validator.CrossrefValidator` with `get_by_doi`/`fuzzy_match`, a `repair_entry(entry, fuzzy=True, overwrite=False)` engine, and a `BibEntry` "strictly validated" model. None of these exist; `src/scholar_bib/` has only `cli`, `deduplicator`, `linter`, `parser` and `resolver`.
- `tools/scholar-bib-kit/docs/tutorial.md:10,16,20` documents a `scholar-bib fix` command with `--no-fuzzy` and `--overwrite`. The CLI has only `lint`, `merge`, `dedup` and `resolve` (`cli.py:24,43,75,99`).
- `.agents/skills/scholar-bib-kit/SKILL.md:49-50` says "Deduplicate records by DOI and title similarity". Matching is exact equality after stripping punctuation; there is no similarity measure. Line 24 says the resolver resolves "missing" metadata, but it also overwrites entries that are already complete (BIB-03).
- `docs/kits_surface_matrix.md:345` says the resolver "replaces whole entry". It does not; stale fields survive (B12). Lines 349 and 509 state bibtexparser `2.0.0b9`, but the shared `.venv` has 2.1.0.
- `tools/scholar-bib-kit/README.md` is a three-line stub, so there are no claims to check there.

## 6. Prioritized recommendations

Source fixes belong in `nexus-scholar-org/scholar-bib-kit`, followed by a `default_rev` bump in `plugins.json`.

| ID | Severity | Effort | Action |
|---|---|---|---|
| BIB-03 | Critical | M | Resolver: accept a search hit only above a title/author/year similarity threshold, and otherwise report it as unresolved. Never overwrite an entry that already has a DOI unless asked. Fill only missing fields. Build the new entry instead of calling the no-op `fields_dict.clear()`. Return a per-entry result (resolved, unchanged or ambiguous, plus a diff). Replace the `print` calls with logging. |
| BIB-01 | Critical | S | Dedup: when both entries have DOIs that differ, never merge on title. Treat title-only matches as *candidates* that need year and first-author agreement, and report them instead of merging automatically. |
| BIB-02 | High | S | Normalize DOIs by stripping the `https?://(dx.)?doi.org/` and `doi:` prefixes, trimming and lower-casing, while keeping punctuation. Add regression tests for `10.1234/5678` versus `10.12345/678`. |
| BIB-04 | High | S | Require `--output` or `--in-place`, write a `.bak`, and emit a JSON change log (merged keys mapped to survivors, renamed keys, grafted fields) suitable for `audit/journal.jsonl`. |
| BIB-05 | High | S | Key generation: collect all existing keys first, transliterate names (NFKD to ASCII) instead of deleting letters, handle braced corporate authors, and output a key map. |
| BIB-06 / BIB-07 | Medium | S | Merge with `fail_on_duplicate_key=False` and report the collisions. Surface `library.failed_blocks` (duplicate keys, parse failures) in every command and exit non-zero unless `--allow-failed`. |
| Tests | High | M | Add negative dedup tests (B1, B3, B3b), resolver tests with a stubbed client (B12), CLI tests with `CliRunner`, and Unicode and duplicate-key fixtures. Assert on survivor identity and field contents, not counts. |
| Coupling | Low | S | Import the resolver lazily in `cli.resolve`. Drop the unused `pydantic` dependency. Consider a minimal HTTP client instead of depending on all of scholar-search-kit. |
| Docs | Low | S | Delete or rewrite `docs/api_reference.md` and `docs/tutorial.md` to match the real API. Correct SKILL.md ("similarity") and the surface-matrix resolver claim. |
| BIB-08 / BIB-09 | Low | S | Make title brace-wrapping opt-in, and when used, wrap only acronyms and proper nouns. Preserve `@string` usage and block order on write. |

## 7. Limits of this assessment

- No network. Real Crossref behaviour (hit quality, rate limiting, the `AcademicHttpClient` retry logic in scholar-search-kit) was not exercised. BIB-03 was reproduced by stubbing `resolve_doi`/`resolve_search` on an instance built with `__new__`.
- The packaging test was skipped because no wheel was built, and I did not build one.
- bibtexparser behaviour was observed with the 2.1.0 install in the shared `.venv`. A different pinned version in a standalone install could differ in middleware defaults (BIB-08, BIB-09).
- I did not check whether `nexus_bib_clean` in scholar-agent-kit adds safeguards around `lint`.
- I did not compare the vendored tree against the kit repo's pinned commit.
