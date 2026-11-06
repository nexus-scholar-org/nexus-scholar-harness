# M5b Corpus import (several databases, deduplicated, accepted in the app)
Branch: dev/m5b/corpus-import · Lane: **RELEASE** (raised from STANDARD at the review: the change alters artifact persistence (`verified.json` rows, a new provenance manifest, record ids), the published identification counts, public HTTP routes and CLI semantics; `test_gate_policy.md` §lanes) · Status: IN PROGRESS · Started: 2026-11-06

Why: gap G1 in [`prisma-scr-readiness.md`](../../assessment/prisma-scr-readiness.md). A review searches several databases. Its PRISMA flow diagram needs the records identified per database and the duplicates removed. Before this change, `accept-corpus --ris` took one file and the counts read 0 duplicates. The researcher asked for this on 2026-11-06, with a way to accept the corpus in the app. This branch also carries the M5-slim gate part 2 record and the readiness checklist (`a1e8811`).

## Definition of done
- [x] **Several RIS exports, one per database,** staged with a label (optional date searched and search string), kept byte for byte under `literature/raw/ris/` (from the terminal and, since the review, from the app: the browser sends the file's bytes as base64), journaled; `accept-corpus --ris LABEL=PATH` repeatable. A label may repeat (a database exported in parts) and is summed per database. Tests `tests/cli/test_accept_corpus.py` (multi-database, parts summed, preview, refusals including impossible dates, frozen, option parsing, BOM), `tests/console/test_corpus_import_api.py::test_the_stored_copy_is_the_uploaded_bytes`.
- [x] **Cross-database deduplication** by the snapshot's own `Deduplicator`; every record kept with `source_database`; `provenance_manifest.json` written, so PRISMA reads identified = records and duplicates removed = records − studies. Test: 6 records from 2 files → 4 studies; Prepare batches 4, and a study keeps the abstract one of its records has.
- [x] **Methods paragraph** names each database once with its summed count and dates searched; `not_stated` lists a missing date or search string. Test `tests/console/test_methods_api.py::test_an_imported_corpus_publishes_the_snapshot_counts_and_names_its_databases` (two RIS files through accept, prepare, approve and publish; `prisma_report.json` equals `/prisma/preview`).
- [x] **API:** `GET /corpus`, `POST /corpus/sources`, `POST /corpus/sources/{id}/remove`, `POST /corpus/accept`, desktop only, in both browser allowlists; contract rows updated. Tests `tests/console/test_corpus_import_api.py`, `tests/console/test_browser_access.py`, `console-proxy.test.ts`.
- [x] **Import screen** (spec `docs/ux/phase2-screening/final/11-import-corpus.md`, FINAL 2026-11-06 with the researcher's answers): the screen, the Import step until acceptance, the Home line after it, the Prepare refusal's Import link. Tests `apps/research-ui/tests/screening-import.test.tsx` (15: copy keys in en/fr/ar, empty, parts summed, engine counts as a draft, remove by id, bytes sent, size stopped in the browser, refusal cards, field marked, phone token → pointer, confirmation with Go back first and Tab kept inside, focus on the frozen heading, read-only when accepted, discovery card, Home entry and line, steps bar), `apps/research-ui/tests-browser/screening-import.spec.ts` (flow, Arabic RTL, phone pointer, axe with contrast in en and ar; light and dark) and committed screenshots `apps/research-ui/screenshots/*screening-import*.png`.
- [x] **Decision** `docs/decisions.md` 2026-11-06 "Several database exports in one corpus": approved by the researcher on 2026-11-06, with three changes (repeated labels summed per database; search details behind a disclosure with a "not stated" flag; the Import step until acceptance, then one line on Home).
- [ ] Closure gate (RELEASE), contract `--check`, independent re-review of the review fixes.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| S-P0-1 ([full review 2026-11-06](../../assessment/full-review-2026-11-06.md), another session) | `tests/console/test_methods_api.py::test_an_imported_corpus_publishes_the_snapshot_counts_and_names_its_databases` | yes: published `(6, 0, 4)`, expected `(6, 2, 4)`. Collect and approval computed duplicates from `verified.json` rows, which now hold every record | yes: both call `corpus_accept.prisma_identification`, which takes the counts from the accepted snapshot for an imported corpus |
| G1 (readiness checklist) | `test_several_ris_exports_are_deduplicated_and_counted_per_database` | not run on the old code; by construction it could not pass (`--ris` took one path, no manifest was written) | yes |
| Review 1 (P1): a discovery corpus with a harvest manifest could be overwritten | `test_a_discovery_corpus_with_a_harvest_manifest_is_never_replaced` | reproduced by the reviewer (staging succeeded, `verified.json` replaced) | yes: only a manifest with the import schema marks `verified.json` as imported |
| Review 2 (P1): a study showed "No abstract available" when its duplicate had one | `test_several_ris_exports_are_deduplicated_and_counted_per_database` (abstract assertion) | yes, run with the old `batcher.py`: `'No abstract available.' == 'Three.'` | yes: the first record with an abstract is shown |
| Review 3 (P1): lane | — | STANDARD declared | RELEASE |
| Review 4 (P2): app uploads were text, not bytes | `test_the_stored_copy_is_the_uploaded_bytes` | not run on the old route (it took text) | yes: `content_base64` |
| Review 5 (P2): a total summed in the browser | vitest `import.staged` | — | the footer shows the engine's `identified` |
| Review 6 (P2): the confirmation let Tab leave | vitest `import.accept` | — | Tab and Shift+Tab stay on its two buttons; `aria-modal` |
| Review 7, 8 (P2, P3): this file and `{slug}` in the decision | — | — | updated |
| Review 9 (P3): a stale `verified.json` accepted after every file was removed | `test_an_import_whose_files_were_all_removed_cannot_be_accepted` | — | `NOTHING_STAGED` |
| Review 10 (P3): invalid protocol → 500; gate refusal code undocumented | `test_an_invalid_protocol_is_a_typed_refusal` | — | `PROTOCOL_INVALID`; both codes in the contract row |
| Review 11 (P3): a phone token saw a refusal card | vitest `import.add` phone case | — | the desktop pointer |
| Review 12 (P3): focus and field errors | vitest `import.accept`, `import.add` | — | focus on the frozen heading; `aria-invalid` on the named field |
| Review follow-ups | `SOURCE_DATE_INVALID` for `2026-13-45`; `test_a_byte_order_mark_does_not_lose_the_first_record` | — | real-date check; the RIS importer reads `utf-8-sig` |

## Decisions
- [2026-11-06 — Several database exports in one corpus, deduplicated by the snapshot](../../decisions.md) (approved by the researcher, 2026-11-06)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner (engine + API) | working tree before the engine commit | `select_test_gate.py --changed main --stage inner`: `git diff --check`; `ruff check scripts/`; contract baseline `--check`; `tsc`; `vitest related route.ts`; `pytest -q -n auto` | all pass except `test_the_committed_fixtures_are_what_the_engine_produces` (the Prepare refusal message changed on purpose); fixtures regenerated, a one-line diff, then the contract fixture tests and both corpus test files pass. The first draft of the API tests had overwritten the existing `tests/console/test_corpus_api.py` (UI-07 paged reads); restored from `HEAD`, the new tests live in `test_corpus_import_api.py` | pytest about 20 min |
| checkpoint (S-P0-1 fix) | working tree on `b43b99c` | `pytest tests/authority tests/console tests/cli tests/test_screening_events.py -n auto`; `pytest tests/test_golden_screening_sandbox.py`; the new test against the old counting code (`git apply -R`) | all pass; golden tests pass; old code fails as expected | about 6 min |
| pr | `f573e2f` | `select_test_gate.py --changed main --stage pr`: `git diff --check main...HEAD`; `ruff check scripts/`; contract baseline `--check`; `pytest -q -n auto`; `tsc`; `vitest`; `build`; `test:browser` | all pass; pytest: no failure in its output (the gate log kept only the progress lines); vitest 238/238; build clean; Playwright 154 passed, 13 skipped, 1 failed: locale-routing N2 in the dark project (open, Deferred in M5-slim) | about 30 min |
| review | `f573e2f` | `milestone-reviewer` | CHANGES: 3 P1, 4 P2, 5 P3 (table above); all fixed in the next commit | — |

## Deferred
- Non-RIS formats (CSV, BibTeX, PubMed nbib): spec 11 decision 3.
- Reviewing near-duplicate groups by hand: spec 11 decision 5.
- From the review, not fixed here: `partition_screening_results` keeps the last duplicate row's metadata in `included.json` while the batch shows the first record with an abstract (one representative rule for both is follow-up work); `sources.json` has no lock, so two tabs staging at the same moment could lose an entry; `GET /corpus` re-parses and re-deduplicates the staged files on every call, including from the steps bar (cost not measured; fine for thousands of records, to cache if it shows).
