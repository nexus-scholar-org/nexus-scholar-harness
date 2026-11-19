# M3h-c-arxiv-date The arXiv leg sends its year range (F16, second half)
Branch: dev/m3h-c/arxiv-date-filter · Lane: **STANDARD** (see "Lane") · Status: **MERGED** (PR #251, merge commit `95cc6233`, 2026-11-19; both golden cassettes re-recorded by the researcher 2026-11-19; `milestone-reviewer` APPROVE) · Started: 2026-11-18

The half of finding F16 of
[`three-phase-hardening-2026-11-10.md`](../../assessment/three-phase-hardening-2026-11-10.md)
that [M3h-b-resilience](M3h-b-resilience.md) deferred ("Deferred", first item):
the arXiv leg sends the protocol's years as a `submittedDate` clause instead of
filtering them after retrieval. M3h-b made the leg note stop denying that the
filter exists; this milestone sends it. Decision 2026-11-18 item 2 (M3h-b):
the researcher re-records the arXiv answers later, then the date range is
sent. Provider reference: [`PROVIDERS_2026-11.md`](../../kits/search/PROVIDERS_2026-11.md) §4.
Choices of this milestone: `docs/decisions.md`, top entry (2026-11-18, M3h-c, five items, all **proposed**).

## Lane

**STANDARD**, declared at the start and kept after the check below (item 3 of the decision entry, proposed).
`docs/architecture/test_gate_policy.md` puts "contract semantics; artifact identity or persistence; public API, CLI, or MCP semantics; cross-kit compatibility" in RELEASE.
This diff changes the request one provider sends and the notes its leg records. It adds no field, no schema and no identity code.

- **The golden cassettes are not covered by the contract baseline.** `uv run python scripts/generate_contract_baseline.py --check` answered "current" before the first edit (`088af7cf`) and after the code and tests (HEAD below); neither cassette, nor any test that replays one, is named in `scripts/generate_contract_baseline.py`, `docs/architecture/contract_v1_baseline.md` or the gate manifest. A cassette changing therefore does not force RELEASE.
- The pinned `GOLDEN_SCI_DIGEST` and `GOLDEN_REC_DIGEST` move at the re-record, because the arXiv answer is different data (as in M3h-providers). They pin a test fixture's result, not a contract artifact.
- The full `pr` gate runs once on the final commit, after the re-record, and the `milestone-reviewer` reads the diff.

## Definition of done
- [x] Reproducing test first: a year range gives the `submittedDate:[... TO ...]` clause, no range gives none (`tests/kits/search/test_arxiv_date_filter.py`, offline, no network).
- [x] The clause is added after compaction, wrapped so the AND binds to the whole topic query, once.
- [x] The leg record and the leg note say the range was sent; `cannot_express` no longer lists an arXiv year line; the local year check stays as a guard.
- [x] The re-record is one step for the researcher: one script, the commands, what each sends and to whom, how to check (below).
- [x] The researcher re-records both arXiv answers (`scripts/record_golden_recon_arxiv.py`); the golden replay tests go green (9 passed, 0 failed).
- [x] The pinned golden digests: **they did not move** (the replayed corpus is the same set, see "After the re-record"), so `GOLDEN_SCI_DIGEST` / `GOLDEN_REC_DIGEST` stay as they are; the arXiv record counts before and after are recorded below.
- [ ] The open-ended range checked live once (`--check-open-ended`): **not run** (the researcher reported the re-record only); decision item 1 stays open and the bounds 1991 and 9999 stay unverified live.
- [x] Gates: inner after edits, the `pr` gate once on the final executable commit `d89c4c99`, contract baseline `--check`, both ruff commands; `milestone-reviewer` APPROVE (2026-11-19, one P2 asking for this evidence row, done).
- [ ] Researcher's word before any push or PR.

## Built
- `ArxivProvider.translate` (`src/scholar_search/providers/arxiv.py`): when `year_min` or `year_max` is set, after compaction, `search_query` becomes `(<topic>) AND submittedDate:[<first>01010000 TO <last>12312359]`. An open start is `1991`, an open end `9999` (`DATE_OPEN_START`, `DATE_OPEN_END`; decision item 1). A query with no year range is unchanged. The leg's `executed_query` and `request.search_query` carry the clause; the note reads "arXiv year range sent as a submittedDate filter (2020 to 2026; ...); years are also checked after retrieval". The old `YEAR_NOTE` and the `cannot_express` year line are removed (the plan shows what is sent in `executed_query`).
- `scripts/record_golden_recon_arxiv.py` records both golden cassettes (recon probe and golden search), refuses to write unless every check passes (decision item 4), and has `--check-open-ended`.
- Two tests that pinned the old behaviour were updated, nothing weakened: `tests/console/test_discovery_api.py::test_plan_reports_the_protocol_cap_and_the_ceiling` (the plan's arXiv string carries the clause; the note says "sent"; no year line in `cannot_express`) and `tests/kits/search/test_k0_conformance.py` (its helper sent a year range while pinning the compaction output byte for byte; it now sends none, and the date clause is tested in `test_arxiv_date_filter.py`).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| contract (before) | `088af7cf` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" (exit 0) | seconds |
| before | `088af7cf` + the new test file | `uv run pytest tests/kits/search/test_arxiv_date_filter.py` | 6 failed (no clause; the old note); then fixed two mistakes in the tests themselves (the default `language` in `cannot_express`, a query too short to compact) | |
| after | working tree | the same file plus `tests/unit/test_record_golden_recon_arxiv.py` | all passed | |
| golden replay | working tree | `uv run pytest tests/pipeline/test_golden_search_cassettes.py tests/pipeline/test_golden_recon_cassette.py tests/recon/test_direction_pool_quality.py -n 4 -rA` | **4 failed**, 7 passed; see "Red until the re-record" | |
| full suite without the golden files | working tree | `uv run pytest tests -n auto --ignore=<the two golden files>` | 72 failed or errored, none in a search, console, recon, pipeline, harness or unit test: all in `tests/kits/rag`, `tests/kits/pdf`, `tests/kits/agent` (RAG tools), `tests/e2e` and `tests/conformance` index/extract tests, because this worktree was synced with `--extra dev` only (58 of them print `No module named 'chromadb'`; the rest are the `DEPENDENCY_ERROR` envelope of the same missing backends). Not caused by this change; the final gate runs with `--extra pdf --extra rag` | |
| contract (after) | `e1bd0950` | `generate_contract_baseline.py --check` | "Contract baseline current" (exit 0) | |
| golden replay (after re-record) | `d89c4c99` | `uv run pytest tests/pipeline/test_golden_search_cassettes.py tests/pipeline/test_golden_recon_cassette.py` | 9 passed, 0 failed | |
| pr gate | `d89c4c99` | `uv run --extra dev --extra pdf --extra rag pytest -q -n auto` (the pr stage's pytest line; `git diff --check` and `ruff check scripts/` also clean) | exit 0, no failure or error in the progress output (about 5,377 passed, 17 skipped, counted from the dots: this run printed no summary line) | |
| contract (after the re-record) | `d89c4c99` | `generate_contract_baseline.py --check` | "Contract baseline current" (exit 0) | |
| lint | `d89c4c99` | `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | both "All checks passed" | |
| review | `d89c4c99` | `milestone-reviewer` | **APPROVE**; P2 (this row) done; P3: the common browser case is an open end (year_min only), first live use may refuse, fix is one constant | |

## After the re-record (2026-11-19)
The researcher re-recorded both cassettes. The diff touches one request line and the arXiv answer in each file and nothing else (the number of address-like strings in each cassette is unchanged); the request now carries the clause: `(...) AND submittedDate:[202001010000 TO 202612312359]`, closed range, so the open-end bounds are not in these cassettes.

| Cassette | arXiv entries before | after | `totalResults` before | after |
| :-- | :-- | :-- | :-- | :-- |
| `golden_recon_probe.yaml` (cap 25) | 9 | 6 | 9 | 6 |
| `golden_uav_search.yaml` (cap 100) | 44 | 36 | 44 | 36 |

arXiv now filters by year itself: the 3 and 8 records that fall away are the ones the leg used to drop after retrieval (the local guard). That is why the pinned digests do not move: the corpus after the local guard is the same. Replay: `uv run pytest tests/pipeline/test_golden_search_cassettes.py tests/pipeline/test_golden_recon_cassette.py` gives 9 passed.

## Red until the re-record (history: all four are green now)
Four tests failed on this branch, every one for the same reason: `CannotOverwriteExistingCassetteException`, the arXiv request now carries the clause and the recorded arXiv interaction does not (the cassettes match on method, scheme, host, path and query). Nothing was weakened, skipped, deleted or hand-edited.

| Test | Why it fails now | After the re-record |
| :-- | :-- | :-- |
| `tests/pipeline/test_golden_search_cassettes.py::test_golden_search_replays_with_legs_report_and_stable_ids` | the arXiv leg is `failed`; the test asserts `ok` on every leg | green |
| `tests/pipeline/test_golden_search_cassettes.py::test_the_handoff_accept_gives_the_snapshot_the_cli_run_gives` | same, in the CLI and browser runs | green |
| `tests/pipeline/test_golden_search_cassettes.py::test_dedup_tiers_are_recorded_and_the_ids_do_not_move` | same | **stays red until the pinned `GOLDEN_SCI_DIGEST` / `GOLDEN_REC_DIGEST` are moved**; that is my step after the re-record (decision item 5) |
| `tests/pipeline/test_golden_recon_cassette.py::test_the_golden_probe_keeps_each_leg_and_feeds_directions` | the arXiv leg is `failed` (`CannotOverwriteExistingCassetteException`); the test asserts `ok` for each answering database | green |

Replay-sensitive tests that pass today and keep passing (they are not a check of the new answer): `test_the_golden_probe_runs_from_http_and_binds` (a failed arXiv leg still leaves a `partial` pool, which is what it asserts), `test_the_plan_dry_run_equals_the_replayed_legs` (a failed leg still records the string it tried to send), the two "holds no contact address or key" tests, and `tests/recon/test_direction_pool_quality.py` (reads the recorded pool without replaying the arXiv request). They are re-run after the re-record.

## For the researcher: the re-record
Your terminal is PowerShell. Run it in this worktree: `C:\Users\mouadh\Documents\nexus-scholar-harness-demo\.claude\worktrees\arxiv-date-filter-b3b9d5`. Put your own contact address where the placeholder is; it is read from the environment only and never written to a file.

```powershell
cd C:\Users\mouadh\Documents\nexus-scholar-harness-demo\.claude\worktrees\arxiv-date-filter-b3b9d5
$env:SCHOLAR_MAILTO = "<your contact address>"
```

**Step 1: the re-record (two requests).**

```powershell
uv run python scripts/record_golden_recon_arxiv.py
```

- Sends **two GET requests to `https://export.arxiv.org/api/query`**, one after the other (arXiv's one request per three seconds holds): the golden recon probe (`max_results=25`) and the golden search (`max_results=100`), each with `submittedDate:[202001010000 TO 202612312359]`. Nothing goes to OpenAlex, Crossref, Semantic Scholar or PubMed.
- Your address goes to arXiv in the `User-Agent` header (`nexus-scholar/<version> (mailto:...)`), as in every harvest, and is filtered out of what is saved. No API key is used (arXiv has none, and the script clears the others).
- Writes the arXiv interaction of `tests/fixtures/cassettes/golden_recon_probe.yaml` and of `tests/fixtures/cassettes/golden_uav_search.yaml` and nothing else. Every other interaction is kept byte for byte, and **nothing is written at all** unless, for both cassettes, the leg is `ok` with records fetched, the query sent has a `submittedDate` clause, arXiv's answer is not an error feed (arXiv answers a query it cannot parse with one error entry and the leg still says `ok`) and the address is not in the recording. If a check fails it prints `refused: ...` and exits 1; send me the output.
- There is no dry run in the steps on purpose: arXiv asks clients not to repeat the same query within a day, and the script already writes nothing on a failed check. `--dry-run` exists (`uv run python scripts/record_golden_recon_arxiv.py --dry-run`) and sends the same two requests, so use it only if you want to see the output before anything is written, and then run step 1 again (four requests in all).
- It prints, per cassette, the leg status, `fetched`, `reported_total`, the query sent and the arXiv interaction count (1 to 1). Keep that output; the numbers go in this record.

**Step 2: check that the replay is green** (offline, no request):

```powershell
Remove-Item Env:SCHOLAR_MAILTO
uv run pytest tests/pipeline/test_golden_search_cassettes.py tests/pipeline/test_golden_recon_cassette.py tests/recon tests/unit/test_record_golden_recon_arxiv.py -q -rf
```

Expected: three of the four red tests of the table above are green, including both "holds no contact address or key" tests; **`test_dedup_tiers_are_recorded_and_the_ids_do_not_move` stays red** (its pinned digests belong to the old answer) until I move them. `git status` shows exactly two modified files under `tests/fixtures/cassettes/`.

**Step 3 (optional, decision item 1): does arXiv accept an open-ended range?** Sends **one more GET request to `https://export.arxiv.org/api/query`**, the recon probe with a start year and no end year (`submittedDate:[202001010000 TO 999912312359]`), into a scratch file that is discarded. It writes nothing and touches no cassette. It needs the address again if you removed it in step 2:

```powershell
$env:SCHOLAR_MAILTO = "<your contact address>"
uv run python scripts/record_golden_recon_arxiv.py --check-open-ended
Remove-Item Env:SCHOLAR_MAILTO
```

It prints `status=ok` with `fetched` above 0 when arXiv accepts the open end, and `refused: ...` (exit 1) when it answers an error feed. In the second case tell me: decision item 1 option (b) or (c) is then one change.

Then tell me in this chat that you re-recorded and paste the output of step 1 (and step 3). I then move the digests, fill the evidence rows above, run the PR gate once and the `milestone-reviewer`, and ask you before any push.

## Deferred
- **The documented syntax was not tested live by us** (`PROVIDERS_2026-11.md` §"Not verified"). The unit tests pin the string; the researcher's re-record is the first request that carries it. A closed range is what the documentation shows (`submittedDate:[YYYYMMDDTTTT TO YYYYMMDDTTTT]`, GMT, to the minute); the open ends (1991, 9999) are verified only by step 3.
- **The size estimate (M10b Part D) and the Plan screen's arXiv wording.** `docs/ux/phase1-discovery/final/01-plan.md` §224 and §248 call the arXiv count "an upper bound only" because the years were filtered after retrieval, and count arXiv as 0 in `records.low`. Once this merges, the arXiv `totalResults` is already date-filtered. Part D's code in `src/scholar_search` is not touched here; the Part D session should read the arXiv total as a count for the range. Hand-over note in the shared notes folder.
- **`docs/kits/search/PROVIDERS_2026-11.md`** keeps its cell for the arXiv year filter as of `b6643a0` by its own header; its "Hardening candidates" item 5 is done by this milestone. Not edited here (outside the milestone's files).
- **Sub-year precision.** `published` is read as a year; the clause is sent as whole years from 1 January 00:00 to 31 December 23:59 (GMT), so a year edge can differ from a local-time year by a day. The local guard compares years only.

## Open for the researcher
1. Run the re-record (above), and step 3 if you want decision item 1 settled.
2. Decision 2026-11-18 (M3h-c), items 1 to 5: confirm or overrule (item 1 open end, item 3 lane).
3. Push and PR: your word, after the gate and the review.
