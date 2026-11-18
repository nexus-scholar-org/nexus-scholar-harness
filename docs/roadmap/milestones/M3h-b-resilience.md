# M3h-b-resilience Provider resilience (F14, F15, F16)
Branch: dev/m3h-b/provider-resilience · Lane: **RELEASE** (see "Lane") · Status: READY FOR PR · Started: 2026-11-18

The second package of the plan §6 M3h row: findings F14, F15 and F16 of
[`three-phase-hardening-2026-11-10.md`](../../assessment/three-phase-hardening-2026-11-10.md)
("Provider side", §4 item 5), and the two items the
[M3h-providers record](M3h-providers.md) deferred with them: one Semantic
Scholar budget for the leg and the abstract hydrator, and the auth channel
per leg. Provider reference: [`PROVIDERS_2026-11.md`](../../kits/search/PROVIDERS_2026-11.md).
Approved by the researcher on 2026-11-18 (relayed by the planning session).

## Lane

**RELEASE**, declared at the start. `docs/architecture/test_gate_policy.md`
§"Delivery lanes" puts "artifact identity or persistence; public API, CLI, or
MCP semantics" in RELEASE. This package adds fields to every run's persisted
`legs.json` (endpoint, auth channel, page size per leg; the client identity
per run), which the console's run answers pass through, and F15 changes which
databases a protocol without a database list searches (CLI and browser
semantics). No Contract v1 schema, artifact identity or snapshot change is
intended: `generate_contract_baseline.py --check` runs at every commit.

## Definition of done
- [x] Audit: `phase-auditor` re-verified every point at HEAD (`e7644a6c`); result summarised under "Audit".
- [x] F14 Crossref rate: list requests at most 3 per second with a contact address, at most 1 without (test named below).
- [x] F14 headers: `x-rate-limit-limit` / `x-rate-limit-interval` lower the provider's budget, never raise it (test named below).
- [x] F14 User-Agent: `nexus-scholar/<installed version>`, never `scholar-search-kit/0.1.0` (test named below).
- [x] F15: one default database set, one constant; the recommended option built and recorded in `docs/decisions.md` as proposed, with what changing it would cost; a protocol that names its databases runs exactly those (test named below).
- [x] F16 arXiv rate: at most one request every 3 seconds (test named below).
- [x] F16 arXiv date filter: the leg note no longer denies the `submittedDate` filter (test named below); sending the clause needs the arXiv golden interaction re-recorded (see "Deferred" and "Open for the researcher").
- [x] F16 S2 citations and references are paged past 1,000 (test named below).
- [x] F16 leg record: each leg in `legs.json` records its endpoint, auth channel and page size; the run records the client package and version (test named below).
- [x] Deferred from M3h: the leg and the abstract hydrator share one Semantic Scholar budget; the hydrator no longer retries keyless after a rejected key (tests named below).
- [x] Deferred from M3h: the auth channel per leg (`key`, `mailto`, `none`, `key_rejected`) (test named below).
- [x] Golden cassettes pass without re-recording (`tests/pipeline/test_golden_search_cassettes.py`, `test_golden_recon_cassette.py`).
- [x] Gates: inner after edits, checkpoint (one run after all items, see Evidence), pr once on the final executable commit, contract baseline `--check`, both ruff commands; `milestone-reviewer` APPROVE.
- [x] Plan §6 M3h row updated.

## Audit

`phase-auditor` at `e7644a6c` (2026-11-18, read-only, offline repros only): every point **still true**; M3h, M10a and M3i changed none of the code behind them. Partial: a refused Semantic Scholar leg already said whether it was keyed (`refused_note`), nothing on a successful leg; since M10a the browser's OpenAlex key check also covers a run whose list is empty. Found beyond the finding text:
- the abstract hydrator ran its Semantic Scholar batches through its own client at 10 requests per second (`pipeline/hydration.py:64`), not the leg's 0.9;
- `AcademicHttpClient.post` retried every 4xx three times, so a rejected key cost 4 keyed and then 4 keyless requests;
- the golden Crossref answer of 2026-11-08 carries `x-rate-limit-limit: 3`, `x-rate-limit-interval: 1s`, `x-concurrency-limit: 3` (`golden_uav_search.yaml`), which confirms F14 offline;
- the CLI with a protocol whose names are all unknown fell back to four, without a protocol to five; MCP `nexus_discover` hard-coded four;
- the arXiv date clause would change the arXiv request in both golden cassettes (both 2020–2026), matched on the query string: not sendable without a re-record.
Cassette matching is `method, scheme, host, path, query`; headers (the User-Agent) are not matched, and no test digests a leg dict.

## Findings fixed
| ID | Reproducing test (`tests/kits/search/test_provider_resilience.py` unless named) | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| F14 User-Agent | `::test_the_user_agent_names_nexus_scholar_and_its_installed_version`, `::test_the_user_agent_carries_no_contact_address_when_none_is_set` | yes, 2 failed at `e7644a6c` | yes |
| F14 Crossref rate | `::test_crossref_list_requests_stay_at_three_per_second_with_a_contact_address`, `::..._at_one_per_second_without_a_contact_address`, `::test_crossref_list_and_single_record_requests_have_separate_budgets`, `::test_a_budget_follows_a_contact_address_set_later` | yes, the first two failed at `e7644a6c` (the last two were added with the list/single split) | yes |
| F14 headers | `::test_crossref_rate_limit_headers_lower_the_budget`, `::test_rate_limit_headers_never_raise_the_budget`, `::test_the_recorded_golden_crossref_headers_keep_three_per_second`, `::test_rate_limit_header_values_are_read_or_ignored` (8 cases), `::test_a_header_from_a_host_without_a_budget_lowers_only_that_client` | yes, 12 failed at `e7644a6c` | yes |
| F15 | `::test_one_default_database_set` (eleven places, among them the CLI and the console), `::test_a_protocol_that_names_its_databases_searches_exactly_those` (guard), `::test_the_mcp_discover_tool_searches_the_default_set` (guard) | yes, the first failed before the fix; the guards passed before and after (they pin behaviour that must not change) | yes |
| F16 arXiv rate | `::test_arxiv_asks_at_most_one_request_every_three_seconds` | yes | yes |
| F16 arXiv note | `::test_the_arxiv_leg_note_no_longer_denies_a_date_filter`; `tests/console/test_discovery_api.py` line 199 updated to the new note | yes | yes |
| F16 S2 paging | `::test_s2_citations_and_references_are_paged_past_1000` (2 cases), `::test_s2_citation_paging_stops_when_next_does_not_advance` (guard) | yes, 2 failed at `e7644a6c` (1,000 records from one request) | yes |
| F16 leg record | `::test_each_leg_records_its_endpoint_auth_channel_and_page_size` (7 cases), `::test_a_leg_without_a_contact_address_says_its_auth_channel_is_none`; `tests/unit/test_discovery_legs.py::test_legs_json_records_the_client_and_each_legs_endpoint_auth_and_page_size` | yes, 8 failed, and the `legs.json` test failed on `KeyError: 'client'` | yes |
| M3h deferred: auth per leg | `::test_a_rejected_s2_key_is_recorded_as_key_rejected` (401, 403), `::test_an_openalex_key_refusal_is_recorded_on_the_leg` (401, 403, 409) | yes, 5 failed | yes |
| M3h deferred: one S2 budget | `::test_the_leg_and_the_abstract_hydrator_share_one_semantic_scholar_budget`, `::test_a_post_to_semantic_scholar_waits_on_the_shared_budget`, `::test_the_hydrator_never_retries_keyless_after_a_rejected_key` | yes, 3 failed at `e7644a6c` | yes |
| POST 4xx retries (audit) | `::test_a_post_answered_4xx_is_sent_once` (400, 403), `::test_a_post_answered_5xx_is_still_retried` (guard) | yes, both 4xx cases failed with only the retry condition reverted | yes |

## Decisions
- [2026-11-18 — M3h-b: one default database set, shared provider budgets, the leg's auth channel](../../decisions.md) (seven items, all **proposed**). Item 1 (which default set) and item 2 (re-recording arXiv for its date filter) need the researcher's choice.
- The console is touched in one place: `console/api/discovery.py` imports the search kit's default set instead of its own copy (an import line and the assignment), because its "off by default" wording reads that list. No other console or UI change; the screens already show "Off by default" without a reason for any database with that status.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| before | `e7644a6c` + the new test file | `uv run pytest tests/kits/search/test_provider_resilience.py` (then the leg-record and default-set tests, and the `legs.json` test, as each was written) | 23 failed, 1 passed; then 14 failed, 1 passed; `KeyError: 'client'` (table above) | |
| inner | working tree | `select_test_gate.py --changed origin/main --stage inner` (`git diff --check`; pytest `tests/console`, `tests/recon`, `tests/pipeline tests/unit`, `tests/kits/search`, not slow) | 9 failures, all tests that pinned the old behaviour (the arXiv note, PubMed in the default set, the hydrator's keyless retry, the five-database fallback); updated to the new behaviour, see "Decisions" | 798 s |
| inner | working tree | the updated files plus `tests/pipeline/test_golden_search_cassettes.py`, `test_golden_recon_cassette.py` | all passed; golden: 9 passed (no re-record) | 156 s + 102 s |
| lint | working tree | `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; broad `ruff check` on each touched kit file against `origin/main` | clean; clean; no new finding (counts equal before and after) | |
| contract | working tree | `generate_contract_baseline.py --check` | current | |
| closure (includes pr) | `c8b5ecd7` (executable code as `3c67d6fc`) | `select_test_gate.py --changed origin/main --stage closure`: contract baseline, schemas and two-study fixture `--check`; `ruff check scripts/`; ruff bug classes on `src/`; `git diff --check origin/main...HEAD`; `uv run pytest -q -n auto`; `uv build --wheel` | all exit 0; pytest 5110 passed, 15 skipped, 0 failed (counted from the progress output: this repo's `-q` prints no summary line); wheel `nexus_scholar-1.1.0b6` built | 739 s |
| review | `75def6c7` | `milestone-reviewer` | CHANGES (R1 P2, R2–R6 P3; see "Review"), repaired in `79944f50` | |
| review | `7ec53ed3` | `milestone-reviewer` round 2 (R1–R6 and the repair delta `75def6c7..7ec53ed3`) | **APPROVE** (R1 withdrawn as a misreading, R2–R6 fixed); the reviewer relied on the recorded pr gate for the repair tests | |
| pr | `79944f50` (final executable commit) | `git diff --check origin/main...HEAD`; contract baseline `--check`; `ruff check scripts/`; ruff bug classes on `src/`; `sync_skills_bundle.py --check`; `uv run pytest -q -n auto` | all exit 0; pytest 5116 passed, 15 skipped, 0 failed | 521 s |
| checkpoint | `5f0d55fe` | `select_test_gate.py --changed origin/main --stage checkpoint` (`git diff --check`; pytest console+authority, recon+inception+MCP recon, pipeline+unit+e2e+console pipelines/jobs, kits/search+identity+stages+http client+screening migration, kits/agent+mcp+parity+capability+agent CLI, each `-n auto`; `sync_skills_bundle.py --check`; `test_count_freshness.py`) | every command exit 0 | 1085 s |

## Review
- Round 1 (`milestone-reviewer` on `75def6c7`): **CHANGES**, 1 P2 and 5 P3, no P1. Repaired in `79944f50`:
  - R1 (P2): the record and decision said "the verifier" shares the Crossref budget; the reviewer read the post-screening `scholar_verify` kit, which has its own client. The harvest's verification stage (`scholar_search.verifier.DocumentVerifier`) does use the shared single-record budget; `::test_the_harvest_verifier_waits_on_the_crossref_single_record_budget` shows it (it passes on the code before the repair, which is the point: only the wording was wrong). The decision, the docstring and the config comment now name the harvest verifier and say `scholar_verify` is not counted (deferred).
  - R2 (P3): a header can no longer set a budget below 1 per second (or the configured rate when lower) (`::test_a_throttle_header_never_sets_a_budget_below_one_per_second`, fails before).
  - R3 (P3): zero or negative rate settings are refused, and a limiter with no rate never divides (`::test_a_zero_rate_setting_is_refused` ×3, `::test_a_limiter_with_no_rate_never_waits_or_divides`, both fail before).
  - R4 (P3): `tests/conftest.py` resets the shared budgets around every test.
  - R5 (P3): DoD ticked and Deferred filled (this file).
  - R6 (P3): the search-kit skill (both copies, `sync_skills_bundle.py --check` clean) states the new User-Agent and limits; `PROVIDERS_2026-11.md` says its code cells describe `b6643a0` and points at the fixed list.
- Round 2 (`milestone-reviewer`, limited to R1–R6 and `75def6c7..7ec53ed3`): **APPROVE**. R1 withdrawn (the reviewer had read `scholar_verify` as the harvest verifier); R2–R6 fixed; no new finding. Follow-up, not blocking: pin `apps/research-ui/lib/recon-api.ts` to the Python constant (Deferred).

## Deferred
Plan §7 ("Risks and cuts") names no rule for these. Each is left out because it needs a researcher decision or a live recording (no live calls in this milestone), or lies outside the areas this milestone was given:
- **Sending the arXiv `submittedDate` clause** (F16). Needs the two arXiv golden interactions re-recorded with the researcher's `SCHOLAR_MAILTO` (decision 2026-11-18 item 2). Sketch in the shared hand-over note.
- **The post-screening `scholar_verify` kit and `scholar_pdf`** keep their own HTTP clients and User-Agents (`nexus-scholar-verify-kit/0.1`, `scholar-pdf-kit/0.1`) and are outside the shared budgets.
- **The UI's recon database list** (`apps/research-ui/lib/recon-api.ts`) holds the same four as a literal, not pinned to the Python constant (reviewer follow-up; outside this milestone's area).
- **Semantic Scholar `/citations` paging beyond about 10,000 records** (a possible offset limit) is unverified; paging stops on a missing or non-advancing `next`.
- **The rate limit per leg** (hardening candidate (c) 1 also named it) is not recorded; endpoint, auth channel and page size are.
- **Header caps are per process and only go down** (bounded below by 1 per second); a restart resets them. Raising them again from a later header is a researcher's call (decision item 4).
- **A quota-aware circuit breaker for 429s** (lesson 18, backlog K4, H6), deferred again from M3h-providers.

## Open for the researcher
1. Decision 2026-11-18 item 1 (F15): keep the four (built) or choose five (costs a protocol identity change, see the decision).
2. Decision item 2: record the arXiv golden interactions so the date clause can be sent, or leave arXiv unfiltered.
3. Items 3 to 7: confirm or overrule.
4. Push to the fork and open the PR (title suggestion: "M3h-b-resilience: provider rates, one default database set, a fuller leg record").

## Not verified
No live provider was called in this milestone. Every check is offline: unit
doubles and the golden cassettes recorded on 2026-11-08 and 2026-11-10. So the
following rest on the providers' documentation and on recorded answers only:
Crossref's public-pool headers and its single-record limit; whether S2 sends
`next` exactly as assumed on `/citations` and `/references`; arXiv's
`submittedDate` syntax. No wheel was installed and run (it was built). Windows
and Python 3.12 only (CI covers the other platforms). The UI was not run: the
console change is one import and one assignment, and the screens already
render `off_by_default` for any database.
