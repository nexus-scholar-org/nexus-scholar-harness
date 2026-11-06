# M5b Corpus import (several databases, deduplicated, accepted in the app)
Branch: dev/m5b/corpus-import · Lane: STANDARD (screening entry path; escalate to RELEASE if the contract baseline moves) · Status: IN PROGRESS · Started: 2026-11-06

Why: gap G1 in [`prisma-scr-readiness.md`](../../assessment/prisma-scr-readiness.md). A review searches several databases. Its PRISMA flow diagram needs the records identified per database and the duplicates removed. Before this change, `accept-corpus --ris` took one file and the counts read 0 duplicates. The researcher asked for this on 2026-11-06, with a way to accept the corpus in the app. This branch also carries the M5-slim gate part 2 record and the readiness checklist (`a1e8811`).

## Definition of done
- [x] **Several RIS exports, one per database,** staged with a label (optional date searched and search string), kept byte for byte under `literature/raw/ris/`, journaled; `accept-corpus --ris LABEL=PATH` repeatable. Tests `tests/cli/test_accept_corpus.py` (multi-database, preview, refusals, frozen, option parsing).
- [x] **Cross-database deduplication** by the snapshot's own `Deduplicator`; every record kept with `source_database`; `provenance_manifest.json` written, so PRISMA reads identified = records and duplicates removed = records − studies. Test: 6 records from 2 files → 4 studies; Prepare batches 4.
- [x] **Methods paragraph** names each database with its count and date searched; `not_stated` lists a missing date. Test `tests/console/test_methods_api.py::test_an_imported_corpus_publishes_the_snapshot_counts_and_names_its_databases` (two RIS files through accept, prepare, approve and publish; `prisma_report.json` equals `/prisma/preview`).
- [x] **API:** `GET /corpus`, `POST /corpus/sources`, `POST /corpus/sources/{slug}/remove`, `POST /corpus/accept`, desktop only, in both browser allowlists; contract rows updated. Tests `tests/console/test_corpus_import_api.py`, `tests/console/test_browser_access.py`, `console-proxy.test.ts`.
- [ ] **Import screen** (spec `docs/ux/phase2-screening/final/11-import-corpus.md`, FINAL 2026-11-06 with the researcher's answers): the screen, the Import step, the Home line and the Prepare refusal link, with vitest and Playwright checks (en/fr/ar, light/dark, phone pointer).
- [x] **Decision** `docs/decisions.md` 2026-11-06 "Several database exports in one corpus": approved by the researcher on 2026-11-06, with three changes (repeated labels summed per database; search details behind a disclosure with a "not stated" flag; the Import step until acceptance, then one line on Home). The engine part of the label change is done: `test_a_database_exported_in_parts_is_one_database_with_summed_counts`.
- [ ] PR gate, contract `--check`, independent review.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| S-P0-1 ([full review 2026-11-06](../../assessment/full-review-2026-11-06.md), another session) | `tests/console/test_methods_api.py::test_an_imported_corpus_publishes_the_snapshot_counts_and_names_its_databases` | yes: published `(6, 0, 4)`, expected `(6, 2, 4)`. Collect and approval computed duplicates from `verified.json` rows, which now hold every record | yes: both call `corpus_accept.prisma_identification`, which takes the counts from the accepted snapshot for an imported corpus |
| G1 (readiness checklist) | `test_several_ris_exports_are_deduplicated_and_counted_per_database` | not run on the old code; by construction it could not pass (`--ris` took one path, no manifest was written) | yes |

## Decisions
- [2026-11-06 — Several database exports in one corpus, deduplicated by the snapshot](../../decisions.md) (proposed)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner (engine + API) | working tree before the engine commit | `select_test_gate.py --changed main --stage inner`: `git diff --check`; `ruff check scripts/`; contract baseline `--check`; `tsc`; `vitest related route.ts`; `pytest -q -n auto` | all pass except `test_the_committed_fixtures_are_what_the_engine_produces` (the Prepare refusal message changed on purpose); fixtures regenerated, a one-line diff, then the contract fixture tests and both corpus test files pass. The first draft of the API tests had overwritten the existing `tests/console/test_corpus_api.py` (UI-07 paged reads); restored from `HEAD`, the new tests live in `test_corpus_import_api.py` | pytest about 20 min |
| checkpoint (S-P0-1 fix) | working tree on `b43b99c` | `pytest tests/authority tests/console tests/cli tests/test_screening_events.py -n auto`; `pytest tests/test_golden_screening_sandbox.py`; the new test against the old counting code (`git apply -R`) | all pass; golden tests pass; old code fails as expected | about 6 min |

## Deferred
- Non-RIS formats (CSV, BibTeX, PubMed nbib): spec 11 open question 3.
- Reviewing near-duplicate groups by hand: spec 11 open question 5.
