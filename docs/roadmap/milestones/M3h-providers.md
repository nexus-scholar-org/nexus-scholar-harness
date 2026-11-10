# M3h-providers Provider correctness (F11, F12, F13)
Branch: dev/m3h-providers/provider-correctness · Lane: STANDARD (plan §6) · Status: IN PROGRESS · Started: 2026-11-10

Scope is the first package of the plan §6 row: F11, F12, F13 from
[`three-phase-hardening-2026-11-10.md`](../../assessment/three-phase-hardening-2026-11-10.md)
and two stale UI strings. F14 to F16 (Crossref rate limits and headers, arXiv
pacing and date filter, Semantic Scholar citation paging, the default database
set, the User-Agent version) are a later package.

## Definition of done
- [x] F11: PubMed sends `[tiab]` for abstract-scoped terms, never `[ab]`, and the leg says so; the executed string is pinned (`tests/kits/search/test_provider_correctness.py::test_pubmed_abstract_terms_are_sent_as_title_or_abstract`, `::test_pubmed_leg_records_the_tiab_string_it_sent`).
- [x] F11: a field tag PubMed did not apply becomes a leg note, read from the ESearch answer recorded on 2026-11-10 (`::test_a_field_tag_pubmed_did_not_apply_becomes_a_leg_note`, `::test_a_fieldsnotfound_entry_becomes_a_leg_note`, `::test_every_applied_tag_gives_no_note`; fixtures `tests/kits/search/fixtures/pubmed/`).
- [x] F12: OpenAlex is never sent `mailto` (`::test_openalex_never_sends_the_contact_email`); the key is documented as required (`config.py`, user guide §8, getting started).
- [x] F12: `GET /discovery/plan` reports `openalex_key_set`; `POST /discovery/runs` refuses `OPENALEX_KEY_NOT_SET` (409) when OpenAlex is selected without the key (`tests/console/test_discovery_api.py::test_a_run_that_selects_openalex_needs_its_key`, `::test_a_run_without_openalex_needs_no_openalex_key`, `::test_the_plan_reports_the_openalex_key`); registered in `console/refusals.py` and the screening API contract §7 (`tests/console/test_console_refusals.py`), listed in the discovery packet §4.7.
- [x] F12: an OpenAlex 401/403/409 is `PROVIDER_REFUSED` with a note naming the key (`::test_an_openalex_key_refusal_is_provider_refused_with_a_key_note`).
- [x] F12: the Plan screen prints the `SCHOLAR_OPENALEX_KEY` line as it does for the contact email; Harvest shows the refusal card (`apps/research-ui/tests/discovery-plan.test.tsx`, `discovery-harvest.test.tsx`, `discovery-copy.test.ts`; en, fr, ar).
- [x] F13: OpenAlex pages are at most 100, search and snowballing (`::test_openalex_page_size_never_exceeds_100`, `::test_openalex_snowball_pages_are_100`); boolean queries use `search.title_and_abstract` through `translate()` (`::test_openalex_boolean_query_uses_the_scoped_search_parameter`, `::test_openalex_boolean_query_with_a_comma_is_sent_unchanged`, `::test_openalex_search_sends_what_translate_says`).
- [x] UI strings: inception says Explore and Direction are not built yet; the contact email is required by Crossref and PubMed, OpenAlex needs its key (`inception-scope.test.tsx`, `discovery-copy.test.ts`).
- [ ] Golden search cassette green with the new OpenAlex request (`tests/pipeline/test_golden_search_cassettes.py`): needs the researcher's OK and key to re-record the OpenAlex interaction.
- [ ] PR gate (`select_test_gate.py --changed main --stage pr`), contract baseline check, `milestone-reviewer` APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| F11 | `tests/kits/search/test_provider_correctness.py` (5 PubMed tests) | yes, 5 failed at `3e353ea` | yes |
| F12 | `test_provider_correctness.py` (5 OpenAlex key tests); `tests/console/test_discovery_api.py` (2 key tests) | yes, 7 failed at `3e353ea` | yes |
| F13 | `test_provider_correctness.py` (8 page and parameter tests) | yes, 8 failed at `3e353ea` (one import error first; the test reads `MAX_PER_PAGE` through the module) | yes |

## Decisions
- [2026-11-10 — OpenAlex needs its API key](../../decisions.md) (proposed; the researcher confirms at the PR).
- A live check on 2026-11-10 (one keyless ESearch request to NCBI, no email, recorded as the fixtures) showed that the JSON answer's `errorlist.fieldsnotfound` is empty for `weed[ab]` while the XML answer says `<FieldNotFound>ab</FieldNotFound>`. The provider therefore also compares the tags it sent with the labels in `querytranslation`.
- The inception copy key `step.comingWithRecon` keeps its name (spec 02 names it for deletion when Explore ships); only its text changes.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree | `uv run pytest tests/kits/search/test_provider_correctness.py tests/kits/search/test_providers.py tests/kits/search/test_query_honesty.py tests/kits/search/test_plan_dry_run.py tests/kits/search/test_leg_error_codes.py tests/kits/search/test_search_legs.py tests/console/test_discovery_api.py tests/console/test_console_refusals.py` | 106 passed | ~40 s |
| inner | working tree | `npx vitest run` (plan, copy, inception copy, inception scope, harvest, recall) and `tsc --noEmit` | 40 passed; typecheck clean | ~20 s |
| inner | working tree | `uv run pytest tests/pipeline/test_golden_search_cassettes.py` | 3 failed: the OpenAlex request is not in the cassette (expected; re-record pending) | ~30 s |

## Deferred
- F14, F15, F16 (plan §6 row, second package).
- Recall checks do not require the OpenAlex key (decision above).
