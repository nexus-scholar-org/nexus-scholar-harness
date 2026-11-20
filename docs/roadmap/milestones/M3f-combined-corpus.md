# M3f-combined-corpus One corpus from a harvest and database exports, deduplicated together
Branch: `dev/m3f/combined-corpus` (from `origin/main` `2436fe66`) · Lane: **RELEASE** (plan §6: Packet B inputs; see "Lane") · Status: IN PROGRESS · Started: 2026-11-20

Plan §6 row: "One snapshot from a harvest plus staged exports, deduplicated together. Until then `VERIFIED_EXISTS` keeps them apart." Sources: `M3d-engine.md` Deferred and decision 12; `DISCOVERY_API_PACKET.md` §4.4. The researcher approved the start on 2026-11-20.

**Why now.** The acceptance run of 2026-11-20 (`docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md`; findings 18 to 29 are on the local branch `dev/docs/acceptance-run-part-2`, commit `812ad954`, not pushed). The researcher had Scopus and IEEE Xplore exports and wanted the app's own harvest of OpenAlex, Semantic Scholar and arXiv in the same corpus. The app could not do it. The workaround was `scholar-search search --provider X --format ris` three times, then importing those files. That loses the harvest's record of each database's search, its abstract filling and its per-record checks. Findings that belong here:
- **26** (P1): a corpus is either a harvest or imported files. The Harvest warning "If you have exports, import them first" reads as if the two then combine.
- **27** (P2): for imported files the Hand-off shows "With an abstract: 0 (0 %)" and "Title only: 0". The real figures were 1,012 and 50 of 1,062 works.
- **13** (P2, related): a second harvest replaces the first; no way to retry one database. It is out of scope (item 7 below).

## What is true at HEAD (checked by the `phase-auditor`, 2026-11-20, on `2436fe66`)

- **One builder.** All three accept paths call `corpus_accept.accept_corpus`, which calls `scholar_search.identity.build_corpus_snapshot_artifact`: the CLI `accept-corpus`, the end of a CLI `run` (`_accept_run_corpus`) and the Hand-off (`accept_discovery_corpus`). It reads `literature/verified.json`, deduplicates the rows with the protocol's `Deduplicator` and emits the snapshot.
- **What enters an id.**
  - A record's `REC-` id hashes its `provider`, `provider_id`, external ids, title and year.
  - A study's `STU-` id hashes its sorted member `REC-` ids.
  - The `COR-` id and the corpus fingerprint hash the studies and `record_to_study`.
  - The artifact id hashes the workspace, the `run_id`, the protocol fingerprint and the corpus fingerprint.
  - The `run_id` hashes the exact `verified.json` rows (`records_sha256`), so the rows' order and every key on them count.
  - `inputs` is `[]`.
- **Harvest rows and import rows cannot collide.**
  - A harvest row keeps its database (`openalex`, …), its own id and `sources[]`.
  - An imported row has `provider` `ris` or `nbib`, `provider_id` `<source id>#<position>`, and `source_database` (the label) in `verified.json` only.
- **The harvest's file.** The harvest writes `verified.json` only when its last stage (checks) ends, and it holds works that were already deduplicated. An import writes `verified.json` only at the accept (`_materialise_staged`), with every record, duplicates included.
- **The guards that keep the two apart:**
  - `VERIFIED_EXISTS` refuses staging after a run (`corpus_accept.py:266`).
  - `STAGED_IMPORT_PENDING` refuses a run and "Finish preparing" while exports are staged (`console/api/discovery.py:905`, `:965`), and refuses the end of a CLI `run` (`pipeline/coordinator.py:203`).
  - The accept route (`screening_v1.py:714`) accepts the exports and ignores a harvest whenever exports are staged.
- **Finding 27, reproduced.** The Hand-off reads only `verified.json`, which does not exist before an import is accepted. After the accept it counts records, not works, and names the format (`ris`), not the database.
- **Contract v1.** `generate_contract_baseline.py --check` passes at HEAD.

## Design

The plain rule: **until the accept, a corpus has two parts, the harvest and the staged exports. The accept deduplicates them as one set and freezes one snapshot.** Nothing of either part is written over before the accept.

### 1. Order

- **Exports can be staged before or after a harvest, and removed, any time before the accept.** `VERIFIED_EXISTS` no longer refuses staging after a search run. It is kept for one case: a `verified.json` that no search run of this app made and no import made (a hand-made or very old workspace). The app cannot tell where those records came from, so it does not mix exports into them.
- **A harvest can run while exports are staged.** `STAGED_IMPORT_PENDING` goes from "Run the search", "Finish preparing this corpus" and the end of a CLI `run`. A harvest never touches the staged files.
- **Both can be repeated before the accept.** A second harvest replaces the first as the harvest part, exactly as today: the first run is marked stale (`SUPERSEDED`) and can never enter the corpus. The staged exports stay as they are.
- **Which harvest is the harvest part.** It is the newest published run whose preparation is `ready`. A run that failed or was stopped before its search was published is not a part, and it blocks nothing.
- **A harvest part that is not ready** (failed, stopped or interrupted after its search, or `incomplete` because a quota ran out during the checks):
  - Without staged exports, the accept refuses `PREPARATION_UNFINISHED`, as today (M3i item 7, H-quota-hang item 4).
  - With staged exports, the accept takes the exports only and leaves the unfinished harvest out. That is M3i item 10, accepted on 2026-11-18, kept as it is.
  - New: before the accept, the Hand-off says in words that the harvest is not prepared and that accepting now freezes the exports without it. The CLI says the same in its output. See decision 3, the one point the researcher should confirm.
- **After the accept** nothing changes: no staging, no harvest (`CORPUS_ALREADY_ACCEPTED`). Adding records to a frozen corpus is M3g's second-round mechanism, not this milestone.
- **The CLI.**
  - `accept-corpus` (and `accept-corpus --ris …` after a harvest) builds the combined snapshot.
  - The end of a CLI `run` with staged exports builds it too, where today it refuses. Its panel names the exports it combined.

### 2. Deduplication and where each record came from

- **One pass.** The accept builds one list of rows and hands it to the existing builder, which runs the protocol's `Deduplicator` once over all of them:
  - first the harvest part's `verified.json` rows, unchanged and in their order;
  - then every staged record, in the order the files were staged and the order inside each file, built exactly as an import builds them today.

  The order is fixed by that rule, not by what the researcher did first, so the same inputs always give the same `run_id` and artifact id.
- **The harvest's own duplicates.** They were already removed by the harvest's deduplication stage, which stays as it is. The second pass merges harvest works with imported records, and imported records with each other.
- **Which record represents a work.** The existing rule, unchanged: the deduplicator keeps the record with the best metadata score and merges the others' identifiers and `sources` into it. The snapshot keeps every member record under its study (`source_record_ids`, `alias_ids`).
- **What screening shows.** Screening shows, for each work, the first member record (in alias order) that has an abstract (`batcher.py:255`). So a work whose harvest copy has no abstract shows the Scopus abstract.
- **Ids.**
  - No identity algorithm or schema changes.
  - A harvest-only accept and an import-only accept give the same snapshot, byte for byte, as before. Tests pin both.
  - In a combined corpus, each harvest row keeps the `REC-` id it would have alone, and each import row keeps its own.
- **Where each record came from (PRISMA "records identified from").**
  - Each record keeps it in `verified.json`: `provider` and `sources[]` for a harvest row, `source_database` for an import row.
  - The accept writes `literature/raw/provenance_manifest.json` with a new schema, `nexus.corpus-combined.v1`. It holds the harvest part (run, records fetched per database, total fetched), the import part (the same `sources` and `databases` rows an import manifest has) and `total_raw_harvested` (fetched plus imported).
  - PRISMA identification for such a corpus: identified = records fetched by the harvest plus records imported; duplicates removed = identified − works.
- **The harvest's file is kept.** Before the combined accept writes the combined `verified.json`, it copies the harvest's file to the run's own folder (`literature/search_runs/run_NNN/verified.json`). If the acceptance gate refuses, the harvest's file and manifest are put back.

### 3. Checks and abstracts for imported records

**Recommended, and built: imported records stay unchecked and keep the abstracts they came with, and the app says so.** The Hand-off says "{n} records come from your exports. They were not checked against Crossref or OpenAlex, and missing abstracts were not filled in." The methods text says the same in one sentence.

Why:
- A check fills missing identifiers in a record (H-provenance-s2 item 1). The `REC-` id hashes the identifiers, so checking an import would make its id depend on what a database answered that day.
- It would cost one OpenAlex request per imported record, the very quota the 2026-11-20 run used up. Scopus and IEEE records are those databases' own records.
- M3c decision 9 cut "Fill missing abstracts" until testers ask.

The alternative, not built: run the checks and abstract filling over imported records too, with H-quota-hang's `incomplete` and "Finish preparing". It is a milestone of its own if wanted.

### 4. The Hand-off

One view of the corpus as the accept would build it.

- **Counts.** Records identified, duplicates removed and works come from one in-memory deduplication of both parts, the same function the accept uses.
- **Provider mix.** One row per source: each database the harvest searched, and each export by its label (Scopus, IEEE Xplore). Each row gains `kind: "search" | "import"`, and counts the works that source found. The existing caption stays: a work found in two places is counted twice, so the shares can add up to more than 100 %.
- **Abstracts (finding 27).** Counted per work: a work has an abstract when any of its records has one, which is what screening will show. This fixes the zeros for imported files before and after the accept.
- **Gate conditions.**
  - Harvest part not ready, nothing staged: "Not ready", as today.
  - Harvest part not ready, exports staged: a note above Accept says the harvest is not prepared and accepting now leaves it out, with "Finish preparing" linking to Harvest. Accept stays available (decision 3).
  - The protocol's search changed since the harvest: the accept refuses `PROTOCOL_CHANGED_SINCE_RUN`, as today. A stale run is never the harvest part.
  - Imported records are unchecked: one line, which blocks nothing (item 3).
- **New fields, additive.** `corpus.origin` gains `"combined"`. `corpus.harvest` is `{run, state, included}` or `null`: the harvest part, its preparation state, and whether the accept would include it.

### 5. The search report and methods text (PRISMA-S)

The report of the harvest run that the corpus uses (`GET /discovery/report`) lists in `identification[]`:
- each database the app searched, with its recorded query and request (`kind: "search"`);
- each export (`kind: "import"`), with the date, search string and limits the researcher stated, "not stated" when absent, and the lines the importer noted.

Its `dedup` counts are those of the combined set.

The methods text:
- **Databases the app searched.** "We searched 3 databases (…) on 2026-11-20 with the query `…`". This sentence is unchanged.
- **Exports.** "We also searched 2 databases ourselves and imported their exports: Scopus (618 records; searched on 2026-11-20; search string: `…`; limits: …) and IEEE Xplore (208 records; date searched not stated; search string not stated)."
- **Unchecked imports.** "The imported records were not checked against Crossref or OpenAlex."
- **Deduplication.** "Deduplication across the 5 sources removed 1,114 records, leaving 1,062 unique works."

The screening export's methods paragraph ("Records were identified from …") lists the harvest's databases and the exports together.

An import-only corpus keeps today's report and paragraph. Its report still answers 404 without a run; that is an M3d-engine deferred item, not this one.

### 6. Copy (finding 26), en/fr/ar

- `harvest.warn.imports` becomes: "Database exports you add on the Import step, before or after this harvest, are combined with it when you accept the corpus on the Hand-off, and duplicates across both are removed."
- `plan.imports.afterRun` becomes: "You can still add database exports; they are combined with this harvest when you accept the corpus."
- The Import screen gains one line while a harvest part exists: "These exports will be combined with the harvest {run} ({works} works) when you accept on the Hand-off."
- The `VERIFIED_EXISTS` card stays for the one case it still covers, reworded to say why: "records of unknown origin".
- Every new key gets its row in the guidance audit (`docs/ux/shared/final/03-guidance.md`).

### 7. Out of scope, and why

- **Retrying one failed database (finding 13).** The harvest part would have to be several runs, not one: legs merged across runs, a per-database stale rule, and its own screens. It is its own milestone, and the design above does not block it.
- **Several queries per review (finding 22).** It changes the protocol's model, a contract decision.
- **An export as a comparison set for the recall check (finding 21).** A Recall feature, not corpus building.
- **Checking and filling abstracts of imported records.** Item 3's alternative.
- **Adding exports or a harvest to an accepted corpus.** That would be a second screening round, M3g's mechanism, for a "late import" round if ever needed.
- **Leaving a ready harvest out on purpose.** No "discard this harvest" action; nothing asked for it.
- **CSV import.** Decision of 2026-11-10, item 6.
- **Near-twin review.** M3e.
- **The import-only report and Duplicates 404s.** M3d-engine deferred.
- **A harvest-only corpus's PRISMA "records identified".** Read from the code, not run: no manifest is written, so it counts works and 0 duplicates. Changing it changes published numbers of harvest-only corpora, so it is a follow-up with its own decision.

### Contract v1

**No contract decision is needed.** The snapshot schema, the `REC`/`STU`/`COR`/artifact identity rules, the canonical JSON and fingerprint rules, and `inputs: []` are unchanged. What changes is which rows the builder receives (Packet B inputs). That is why the lane is RELEASE.

New files are harness run records outside Contract v1, as `verification_checks.json` is:
- the combined manifest schema;
- the copy of the harvest's file in its run folder.

`generate_contract_baseline.py --check`, the schema, fixture and protocol checks run at every gate.

### Accepted decisions this touches

- **Superseded, as they announced.** The decision of 2026-11-10 ("an import is allowed only before any harvest") and M3d-engine decision 12 ("Keep the rule for now, combine later"). This milestone is the "later", approved by the researcher at its start on 2026-11-20. Both entries get a note.
- **Superseded.** The M3a review repair that refuses a CLI run's snapshot while exports are staged ("two corpora are never merged silently"). They are now merged on purpose, and the merge is stated.
- **Kept unchanged.**
  - M3i items 7 and 10, and H-quota-hang item 4: an unfinished harvest is never frozen; with exports staged, the exports are accepted alone. Item 10 gains words on the Hand-off.
  - H-quota-hang item 5: no per-record check status in the contract.
  - M3c decision 9: no abstract filling.
- **Amended by an addendum.** The Hand-off spec's line "no separate imports row" in the provider mix (`08-handoff.md`), a spec choice from when the two could not coexist.

## Definition of done
- [ ] **D1 Order.** Staging after a harvest, a harvest after staging, repeating both and removing exports work before the accept. `VERIFIED_EXISTS` is kept only for `verified.json` of unknown origin, and `STAGED_IMPORT_PENDING` is no longer raised by run, prepare or the CLI `run`. Tests: `tests/cli/test_combined_corpus.py`, `tests/console/test_combined_corpus_api.py`.
- [ ] **D2 One deduplication.** The accept builds one snapshot from the harvest part plus the staged records: one pass, a fixed order, every record kept under its study, and the combined manifest and PRISMA identification. The harvest's file is copied to its run folder and restored on a refused gate. Harvest-only and import-only snapshots are byte-identical to before (golden digests). Tests: `tests/cli/test_combined_corpus.py`, `tests/pipeline/test_golden_search_cassettes.py`.
- [ ] **D3 Unfinished or stale harvest.** An unfinished harvest plus exports accepts the exports only and says so. Without exports it refuses `PREPARATION_UNFINISHED`. A superseded run never enters. A changed protocol refuses `PROTOCOL_CHANGED_SINCE_RUN`. Tests: `tests/console/test_combined_corpus_api.py`.
- [ ] **D4 The Hand-off and corpus views.** Counts from the combined preview, a provider mix with database labels and `kind`, abstracts per work (finding 27), and `corpus.origin` `combined` with `corpus.harvest`. Tests: the API tests above; `apps/research-ui/tests/discovery-handoff.test.tsx`.
- [ ] **D5 The report and methods text.** Combined `dedup`, export sentences with their stated details, the unchecked-imports sentence, and the screening export's database sentence. Tests: `tests/kits/search/test_methods_text_combined.py`, `tests/console/test_combined_corpus_api.py`, `tests/console/test_methods_api.py`.
- [ ] **D6 Screens and copy.** Specs addenda FINAL before UI work. Harvest and Plan copy (finding 26), the Import line, the Hand-off mix, abstract and warning lines, en/fr/ar, and guidance audit rows. Vitest and Playwright.
- [ ] **Gate.** `/gate inner` after edits and `/gate checkpoint` per item. `/gate pr` once on the final commit. Contract, schema, fixture and protocol `--check`. `milestone-reviewer` APPROVE.

## Tests written first
Committed in `1eb12173` before any engine change and run on `2436fe66`'s code. Each failed for the reason named.

| Test | Fails before | Passes after |
| :-- | :-- | :-- |
| `tests/console/test_combined_corpus_api.py::test_an_export_staged_after_a_harvest_is_combined_at_the_accept` | yes: 409 `VERIFIED_EXISTS` | yes |
| `::test_a_harvest_after_staging_is_combined_and_both_can_be_repeated` | yes: 409 `STAGED_IMPORT_PENDING` | yes |
| `::test_an_unfinished_harvest_beside_exports_is_left_out_and_said_so` | yes: no `harvest` field | yes |
| `::test_a_changed_protocol_refuses_the_combined_accept` | yes: staging refused (409) | yes |
| `::test_the_handoff_counts_abstracts_of_staged_exports_per_work` (finding 27) | yes: `with_abstract` 0, `title_only` 0 | yes |
| `::test_the_handoff_shows_the_combined_corpus` | yes: staging refused (409) | yes |
| `::test_the_report_and_methods_text_name_both_parts` | yes: staging refused (409) | yes |
| `::test_records_of_unknown_origin_still_refuse_an_export` | no, by design: it pins the case `VERIFIED_EXISTS` keeps | yes |
| `tests/cli/test_combined_corpus.py` (8 tests: combine, order-independence, idempotence, refused gate restores, PRISMA identification, unfinished harvest left out, `--ris` after a harvest, determinism across folders) | yes: `VERIFIED_EXISTS`; the CLI did not name the left-out run | yes |
| `tests/cli/test_combined_corpus.py::test_an_import_only_accept_gives_the_snapshot_it_gave_before`, `::test_a_verified_only_accept_gives_the_snapshot_it_gave_before` | no, by design: artifact ids taken at `2436fe66` (`ART-corpus-8ddb6e7a…`, `ART-corpus-37531fd3…`) | yes, ids unchanged |

Tests changed because they pinned the rule this milestone lifts (each now pins the new rule):
- `tests/console/test_discovery_api.py::test_a_run_cannot_start_over_staged_exports` became `test_a_run_starts_over_staged_exports_and_leaves_them_staged`.
- `::test_after_a_browser_run_the_corpus_says_why_an_export_cannot_be_staged` became `test_after_a_browser_run_an_export_can_still_be_staged_until_the_accept`.
- `tests/unit/test_run_builds_snapshot.py::test_staged_imports_are_never_silently_swapped_for_the_run` now expects the combined snapshot and `combined_with`.
- `tests/cli/test_accept_corpus.py::test_accept_corpus_from_ris_refuses_to_overwrite_verified` keeps its refusal; the message is reworded ("origin is unknown").

Added after the engine: `tests/console/test_methods_api.py::test_a_combined_corpus_publishes_fetched_plus_imported_and_names_every_source`. It checks the published PRISMA counts, the preview, and the "Records were identified from" sentence after a real publish.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
`docs/decisions.md`, entry "2026-11-20 — M3f-combined-corpus" (PROPOSED).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `2436fe66` | `uv run python scripts/generate_contract_baseline.py --check` | Contract baseline current (phase-auditor) | |

## Deferred
- Retrying one failed database (finding 13), several queries (22), the recall comparison set (21), checking imported records, late imports after the accept, the harvest-only PRISMA count, and the import-only report and Duplicates 404s: see Design §7.
