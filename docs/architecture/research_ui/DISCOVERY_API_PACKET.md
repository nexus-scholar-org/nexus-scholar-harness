# Discovery API packet (Phase 1 screens 01–08)

Status: DECIDED 2026-11-10 (the seven decisions in §6 were taken by the researcher; recorded in [`docs/decisions.md`](../../decisions.md)). Nothing here is implemented; no route in this document exists on `main` (`dfdb691`) unless the "exists" column says so. Implementation starts with M3b-api (§7).
Plan: [`docs/roadmap/production-plan.md`](../../roadmap/production-plan.md) §2 Phase 1 (screens 01–08), §6 M3, §7 cut rule 1 and 3.
Engine record: [`docs/roadmap/milestones/M3a-discovery.md`](../../roadmap/milestones/M3a-discovery.md) (what the engine already does and what it deferred).
Boards: `docs/ux/phase1-discovery/final/project/{Plan,Recall,Harvest,Import,Dedup,Report,States,Handoff}.dc.html`. The written `Status: FINAL` specs 01–08 are M3b's first task; this packet gives them the routes to point at.
Conventions it follows: [`AGENT_WORK_PACKETS.md`](./AGENT_WORK_PACKETS.md) §UI-09 (same-origin proxy, no browser job start), [`UI-07_ACTION_SPEC.md`](./UI-07_ACTION_SPEC.md) §2 (browser credentials carry no authority), `apps/research-ui/AGENTS.md` (the harness computes, the UI shows).

Every path below is under `/api/v1`. Bodies and answers are JSON unless marked SSE or Markdown. Refusals use the inception envelope: `{"detail": {"code", "message", "details"?}}` (`console/api/inception.py:41-45`). Every new code is added to `console/refusals.py` and so to `tests/console/test_console_refusals.py`.

## 1. Why a packet first

The discovery engine (M3a) writes everything the screens need to show, but **no console route reads or runs it**: the only path is the generic `discovery` job action (`scholar-search search`), which is not browser-reachable, and `/harvest/corpus` and `/ui/corpus/{kind}` are the PDF harvest and the screening output, not the search corpus. The import routes (`/screening/corpus*`, M5b/M5c) exist and stay. Building screens 01–08 against guessed routes would repeat the M4b lesson in reverse (specs drifted from the engine until the step API existed), so the routes are fixed here, with the engine work each one needs named, before any screen is written.

## 2. What exists on `main`, per screen

| # | Screen (board) | Exists today | Missing for the screen |
| :-- | :-- | :-- | :-- |
| 01 | Search plan (Plan) | `compile_protocol_search(protocol) -> (Query, providers)` (`scholar_search/protocol_adapter.py:10-96`); `method.retrieval_cap`, `ENGINE_CEILING = 10_000`, `cap_source` values (`protocol`, `run_override`, `query`, `engine_ceiling`); `MailtoNotSet` (`SCHOLAR_MAILTO`, no default) | **No dry run.** Per-provider strings are produced inside each provider at execution (`BooleanQueryTranslator`) and are visible only afterwards as `leg.executed_query`. No route reads the plan. |
| 02 | Recall check (Recall) | `scholar-search validate-query --seed` (`scholar_search/cli.py:808`) over `QueryDiagnosticValidator.validate_and_heal` (`query_validator.py:20-107`); `DocumentVerifier` title check (`verifier.py:60-73`, code `DOI_TITLE_MISMATCH`) | The validator **rewrites the query** ("heals" by appending `OR (doi:…)`), which a frozen protocol forbids; it is CLI-only and ignores the protocol cap; the per-seed, per-database result is not stored or journaled; the harness discards the verifier's audit list. |
| 03 | Harvest (Harvest) | `run_discovery` → one `SearchLeg` per provider (`scholar_search/models.py:162-208`), `progress_callback(provider, fetched)`, `literature/search_runs/run_NNN/{legs.json,raw.json,search_report.md}` (`pipeline/discovery.py:494-544`), `DISCOVERY_SEARCH` event with `parameters.legs`; `scholar-harness run` runs discovery → dedup → verification → hydration → snapshot → prepare | No route starts a run or streams legs. `JobRunner` runs `uv run …` subprocesses and streams stdout lines, not legs. No per-leg stop, no slice yield (the "stop this slice" idea on the board has no engine). |
| 04 | Import (Import) | `GET /screening/corpus`, `POST /screening/corpus/sources` (`label`, `file_name`, `content_base64`, `searched_on?`, `query?`; RIS or `.nbib`), `POST …/sources/{id}/remove`, `POST /screening/corpus/accept`; staged rows carry `id`, `format`, `stored_as`, `sha256`, `records`, `searched_on`, `query`; events `CORPUS_SOURCE_STAGED`, `CORPUS_SOURCE_REMOVED`, `CORPUS_IMPORTED` | No CSV (plan §2 says "RIS/CSV"); no rejected-lines list (the board's `IMPORT_NO_TITLE`, `IMPORT_BAD_TAG`, `IMPORT_BAD_YEAR`); no "limits you applied there" field. |
| 05 | Dedup (Dedup) | `Deduplicator` tiers (identifier, exact title, fuzzy title ≥ 0.97 with year ± 1 and first author), `stable_order`, `get_statistics`; the stage writes `literature/deduped.json` only | **No tier per cluster, no near-twin pairs, no merge log, no decision store.** The board's whole review flow has no engine. |
| 06 | Report (Report) | `search_report.md` per run (executed string, reported total, fetched, cap, status, date, notes, request parameters); `GET /screening/prisma/preview` (`identified`, `duplicates_removed`, …); `prisma_identification` | No route reads `search_runs/`; no run list; the methods paragraph exists for screening only; no PRISMA-S table that joins legs, imports and dedup. |
| 07 | States (States) | Engine codes: `MAILTO_NOT_SET`, `CORPUS_ALREADY_ACCEPTED`, `STAGED_IMPORT_PENDING`, `NOT_BUILT`; leg `status` ok/failed with `error` text and `cap_hit` | `PROTOCOL_CHANGED_SINCE_SNAPSHOT` and `BATCHES_INCOMPLETE` are reason-string prefixes, not typed codes; provider failures are free text (`"{ExcType}: {msg}"`), not `PROVIDER_RATE_LIMITED`/`PROVIDER_TIMEOUT`; there is no `PROTOCOL_MISSING`. |
| 08 | Hand-off (Handoff) | `GET /screening/corpus` (`state` EMPTY/STAGED/ACCEPTED, `preview{identified,duplicates,unique_studies}`, `accepted{artifact_id,…}`, `from_discovery`), `POST /screening/corpus/accept`, `POST /screening/prepare` (`batch_size`), snapshot artifact with `protocol_fingerprint` and `corpus_fingerprint` | Provider mix, abstract coverage, title-only count, outside-window count are not computed anywhere. |

## 3. Shape of the packet

Three layers, so the screens that need no new engine can start first:

- **Layer R (read-only over files the engine already writes):** plan limits, run list and legs, the report table, the hand-off summary. STANDARD lane; no engine semantics change.
- **Layer J (jobs from the browser):** start a discovery run, start a recall check, stream their progress, cancel. One typed route per action, never `/jobs/start`. STANDARD, but §6 decision 1 first.
- **Layer E (engine additions):** the plan dry run, the check-only recall, import rejections, dedup tiers and near-twin pairs with HUMAN decisions, typed provider failure codes. Each is its own milestone item; near-twin review is plan §7 cut 3 ("show counts only" first).

## 4. Routes

### 4.1 Plan (screen 01)

| Method and path | Layer | Answer |
| :-- | :-- | :-- |
| `GET /discovery/plan` | R + E1 | `{shape: "discovery.plan-v1", protocol_fingerprint, query: {id, text, year_min, year_max, language}, cap: {value, source, ceiling: 10000}, mailto_set, providers: [{name, selected, executed_query, request, cannot_express: [str], notes: [str], status: "translated" \| "not_selected" \| "off_by_default" \| "no_connection"}], imports_hint: ["scopus", "wos"]}` |

- `cap` is the protocol's `method.retrieval_cap` with `source: "protocol"`, else `{value: 10000, source: "engine_ceiling"}`. A run override is per run (§4.3), shown on the run, never on the plan.
- `providers[].executed_query` needs **E1, the dry run**: a `translate(query) -> (executed_query, request, notes)` on each provider that returns what `run` would send, without sending it. The engine already builds these strings before the first request; E1 exposes that step. `cannot_express` is the translator's own notes (arXiv phrases dropped, Semantic Scholar has no boolean, Crossref has no language filter, bioRxiv cannot evaluate NOT). Until E1 lands the field is `null` and the screen shows the protocol query with "executed string known after the run" (an honest Loading-like state, not a guess).
- Refusals: `409 PROTOCOL_MISSING` (no `protocol.json`), `422 PROTOCOL_INVALID` (existing code, from `compile_protocol_search`).
- "Copy all executed strings" is client-side over this answer. "Approve the plan" is not a server action: the plan is the frozen protocol; starting a run (§4.3) records the plan it ran as `legs.json` and the `DISCOVERY_SEARCH` event, which is the approval record. No new event.

### 4.2 Recall check (screen 02)

| Method and path | Layer | Answer |
| :-- | :-- | :-- |
| `POST /discovery/recall` | J + E2 | `202 {job}` with `job.kind = "recall"`. Body `{seeds: [{id, kind: "doi" \| "arxiv", source: "anchor" \| "you"}], providers?: [name]}`, 1–25 seeds. |
| `GET /discovery/recall` | R | The last finished check: `{shape: "discovery.recall-v1", checked_at, protocol_fingerprint, query_text, seeds: [{id, kind, source, title, title_check: "ok" \| "DOI_TITLE_MISMATCH" \| "unresolved", per_provider: {name: "found" \| "not_found" \| "n/a" \| "failed"}}], found, total, missed_everywhere: [id], legs: [SearchLeg]}` or `404 RECALL_NOT_RUN`. |

- **E2, check-only recall.** A new `check_seeds(query, seeds, providers, cap)` in `scholar_search` that runs the frozen query with the protocol cap, resolves each seed through `DocumentVerifier` (title check kept, mismatch reported, record never swapped), and reports found/not found per provider. It **never rewrites the query**; `QueryDiagnosticValidator.validate_and_heal` stays CLI-only. "n/a" is a provider that cannot hold that kind of record (a journal DOI on arXiv).
- Anchor seeds come from the draft's recon binding (`GET /inception/drafts/{id}/recon` → `binding`), resolved client-side into `seeds[]` with `source: "anchor"`; the researcher adds `source: "you"` seeds. The route never reads inception state itself.
- Written: `literature/recall_checks/check_NNN.json` (same numbering rule as `search_runs`, `mkdir(exist_ok=False)`), event `DISCOVERY_RECALL_CHECK` with `parameters: {seeds, found, total, missed_everywhere, legs}`, agent `scholar-harness-console`.
- A miss blocks nothing (board: "Run anyway, 1 missed"); the report (§4.6) prints the check next to the run it preceded. "Add a synonym" is a protocol amendment and is **out of this packet**: it goes through inception's replace path, which re-fingerprints the protocol.
- Refusals: `409 MAILTO_NOT_SET`, `409 PROTOCOL_MISSING`, `422 SEEDS_INVALID` (empty, over 25, malformed id), `409 DISCOVERY_JOB_ACTIVE`.

### 4.3 Harvest (screen 03)

| Method and path | Layer | Answer |
| :-- | :-- | :-- |
| `POST /discovery/runs` | J | `202 {job}`, `job.kind = "run"`. Body `{cap_override?: int, providers?: [name], note?: str}`. Starts `run_pipeline` for the open workspace, in-process, as recon does (`console/api/recon.py:97-136`). |
| `GET /discovery/runs` | R | `{shape: "discovery.runs-v1", runs: [{run: "run_003", status, started_at, finished_at, legs_total, fetched_total, raw_published, stale: bool}], active_job: job \| null}` from `literature/search_runs/*/legs.json`, newest first. `stale` is true for a run older than the accepted snapshot's run or than a later run (the board's "run 2's files stay and are named stale"). |
| `GET /discovery/runs/{run}` | R | `legs.json` as stored (`run`, `status`, `query_id`, `query_text`, `year_min`, `year_max`, `raw_published`, `legs: [SearchLeg.to_dict()]`) plus `report_path`, `recall_check?` (the check that preceded it), `cap_override?`. `404 RUN_NOT_FOUND`. |
| `GET /discovery/runs/{run}/report` | R | `text/markdown`: `search_report.md` as written. |
| `GET /discovery/jobs/{job_id}` | J | `{job}`; `404 DISCOVERY_JOB_NOT_FOUND`. |
| `GET /discovery/jobs/{job_id}/events` | J | SSE, replayed in full on connect: `snapshot {job}`, `leg {job_id, provider, fetched, reported_total?, cap, cap_hit, status}`, `stage {job_id, stage: "discovery" \| "deduplication" \| "verification" \| "hydration" \| "corpus_snapshot" \| "screening_prepare", status, detail}`, `done {job}` or `failed {job}`; `: keepalive` every 15 s. |
| `POST /discovery/jobs/{job_id}/cancel` | J | `{job}` with `state: "cancelled"`; fetched records are kept and the run is archived with `status: "PARTIAL"` and a note `cancelled by the researcher` (the board's "cancel the run and keep results"). |

- Job dict, as recon's: `{job_id: "djob_<16hex>", kind: "run" \| "recall", state: "running" \| "succeeded" \| "failed" \| "cancelled", started_at, finished_at, result, error: {code, message, details}}`. One running discovery job per workspace. The `result` of a finished run is `{run, status, stages}` (the coordinator's `results["stages"]`, which already carries `corpus_snapshot.status` ACCEPTED/ALREADY_ACCEPTED/NOT_BUILT/REFUSED).
- `cap_override` is the CLI `--limit`: it sets `cap_source: "run_override"` on every leg and is shown on the run, never on the plan.
- Per-leg stop ("Stop arXiv") and slice yield are **not offered**: the engine has no leg cancel and no slice model. The spec for 03 drops them (recorded as "Changed from the canvas") until an engine item adds `stop_provider(name)` to the run.
- A browser run ends before the snapshot: it runs discovery, deduplication, hydration and verification, and builds no corpus snapshot and no screening batches; the hand-off screen's accept (§4.8) freezes the corpus, and until then another run or an import is allowed (decision 2026-11-10, engine change in M3d-engine; M3b-api still accepts at the end of a run as M3a does).
- Refusals: `409 MAILTO_NOT_SET` (checked before the job starts, as recon does), `409 PROTOCOL_MISSING`, `409 DISCOVERY_JOB_ACTIVE` with `details.job`, `409 CORPUS_ALREADY_ACCEPTED` (a frozen snapshot is never re-run from the browser; replacing it is the inception replace path with its screening-binding checks), `422 CAP_INVALID` (not 1..10000).
- Provider failures inside a leg stay on the leg (`status: "failed"`, `error`); **E5** adds a typed `error_code` next to `error`: `PROVIDER_RATE_LIMITED` (429), `PROVIDER_TIMEOUT`, `PROVIDER_UNAVAILABLE` (5xx), `PROVIDER_REFUSED` (4xx other), `CAP_REACHED` (not a failure: `cap_hit`, kept as the leg flag). Until E5 the screen shows `error` text.

### 4.4 Import (screen 04)

Existing routes, unchanged: `GET /screening/corpus`, `POST /screening/corpus/sources`, `POST /screening/corpus/sources/{id}/remove`. The discovery Import screen is the same screen as spec 11 (M5b) reached from discovery's step bar; it does not get a second route set.

Additions, all **E3**:
- `POST /screening/corpus/sources` body gains `limits?: str` (stored verbatim, printed in the report) and the staged row gains `rejected: [{line, code, reason}]` with codes `IMPORT_NO_TITLE`, `IMPORT_BAD_TAG`, `IMPORT_BAD_YEAR`, and `records` stays the parsed count. The importer (`scholar_search/importers.py`) returns rejections instead of dropping lines silently.
- CSV import is **not in this packet** (RIS and `.nbib` only, as today). Plan §2 row 04 says "RIS/CSV"; the researcher decides whether CSV is worth a column-mapping step (Scopus CSV headers differ from WoS). Until then the screen says "RIS or PubMed .nbib".

### 4.5 Dedup (screen 05)

| Method and path | Layer | Answer |
| :-- | :-- | :-- |
| `GET /discovery/dedup` | R + E4a | Stage 1 (counts only, plan §7 cut 3): `{shape: "discovery.dedup-v1", run, input_records, unique_works, removed, removed_rate, tiers: {identifier, exact_title, fuzzy_title} \| null, method: {title_similarity, year_tolerance, first_author, source: "protocol" \| "default"}, near_twins: null}`. |
| `GET /discovery/dedup/pairs?state=undecided\|decided` | E4b | Stage 2: `{pairs: [{pair_id, a: record, b: record, similarity, reasons: [str], decision: null \| {decision: "merge_keep_a" \| "merge_keep_b" \| "keep_both", decided_at, method: "HUMAN", event_id, supersedes?}}], total, decided}`. |
| `POST /discovery/dedup/decisions` | E4b | Body `{event_id (UUIDv7), pair_id, decision, supersedes?}` → `201 {event}`; journaled `DEDUP_DECISION` with `method: "HUMAN"`; an undo is a superseding event, nothing is deleted. |

- **E4a** makes `run_deduplication` write `literature/dedup/clusters.json` (`{run, method, clusters: [{cluster_id, tier: "identifier" \| "exact_title" \| "fuzzy_title", representative, members}]}`) next to `deduped.json`; `tiers` is then the count per tier. Until E4a, `tiers` is `null` and the screen shows the totals from `deduped.json` versus the run's fetched total.
- **E4b** adds near-twin candidates: pairs that pass the fuzzy-title gate between a lower bound (0.90) and the method's threshold, or fail exactly one check (year, first author, case-only difference), recorded as `literature/dedup/near_twins.json`, never merged by the engine. Decisions are applied by `accept_corpus` before the snapshot is built, so the snapshot carries them (its `inputs` lists the decision event ids). This changes what the snapshot is built from: **RELEASE lane and a Packet B note**, which is why it is Stage 2.
- Refusals: `404 DEDUP_NOT_RUN`, `409 CORPUS_ALREADY_ACCEPTED` on a decision after the snapshot, `422 PAIR_UNKNOWN`, `409 DECISION_SUPERSEDED` (the `supersedes` is not the current event for that pair).

### 4.6 Report (screen 06)

| Method and path | Layer | Answer |
| :-- | :-- | :-- |
| `GET /discovery/report` | R | `{shape: "discovery.report-v1", run, status, identification: [{database, kind: "search" \| "import", executed_query, reported_total, fetched, completeness: "full" \| "lower_bound" \| "failed" \| "stopped" \| "not_searched", no_abstract_rate?, cache?, searched_at, notes}], not_searched: [{database, reason}], imports: [{label, searched_on, query, limits, records, rejected}], dedup: {removed, by_tier?, near_twins?, unique_works}, outside_year_window: int, prisma: GET /screening/prisma/preview, methods_text: {text, built_from: run, reviewed: bool}, runs: GET /discovery/runs}` |
| `PUT /discovery/report/methods` | R | Body `{text, reviewed: bool}` → stored at `literature/search_runs/<run>/methods.md` with a front-matter `reviewed_at`; journaled `METHODS_TEXT_REVIEWED`. The draft is never silently overwritten by a later run: a new run writes `methods.draft.md` and the screen shows both. |

- `completeness` is derived, not stored: `lower_bound` when `cap_hit`; `failed` when `status == "failed"`; `stopped` when the run was cancelled; `full` otherwise. `no_abstract_rate` is counted from `raw.json` when published.
- `methods_text.text` is built by a new `render_methods_text(legs, imports, dedup)` next to `render_search_report` (`scholar_search/search_report.py`): one paragraph per the board's example, each number from a field, no adjectives. Marked `reviewed: false` until the researcher saves it.

### 4.7 States (screen 07)

No route. The codes every discovery route may return, with HTTP status, all registered in `console/refusals.py`:

| Code | Status | Raised by |
| :-- | :-- | :-- |
| `PROTOCOL_MISSING` | 409 | plan, recall, runs: no `protocol.json` |
| `PROTOCOL_INVALID` | 422 | existing; plan |
| `MAILTO_NOT_SET` | 409 | existing; recall, runs, before any request |
| `DISCOVERY_JOB_ACTIVE` | 409 | recall, runs; `details.job` |
| `DISCOVERY_JOB_NOT_FOUND` | 404 | jobs |
| `RUN_NOT_FOUND` | 404 | runs/{run} |
| `RECALL_NOT_RUN`, `DEDUP_NOT_RUN` | 404 | recall, dedup reads |
| `SEEDS_INVALID`, `CAP_INVALID`, `PAIR_UNKNOWN` | 422 | recall, runs, dedup decisions |
| `CORPUS_ALREADY_ACCEPTED` | 409 | existing; runs, dedup decisions |
| `DECISION_SUPERSEDED` | 409 | dedup decisions |
| `PROTOCOL_CHANGED_SINCE_SNAPSHOT`, `BATCHES_INCOMPLETE` | 409 | **E5** turns these reason prefixes (`pipeline/coordinator.py:248-283`) into typed codes on the run job's `error` |
| `PROVIDER_RATE_LIMITED`, `PROVIDER_TIMEOUT`, `PROVIDER_UNAVAILABLE`, `PROVIDER_REFUSED` | leg field | **E5**, `leg.error_code`; never an HTTP refusal (a failed leg is a `PARTIAL` run) |
| `ENGINE_UNREACHABLE` | client | the proxy's `CONSOLE_UNREACHABLE` 502 / `CONSOLE_TIMEOUT` 504, shown by the shared state card |

The board's `CONTACT_EMAIL_MISSING` is `MAILTO_NOT_SET` (one code, as the engine, the CLI and recon already use it). The board's `IMPORT_LINE_*` is the `rejected[].code` list of §4.4.

### 4.8 Hand-off (screen 08)

| Method and path | Layer | Answer |
| :-- | :-- | :-- |
| `GET /discovery/handoff` | R | `{shape: "discovery.handoff-v1", corpus: GET /screening/corpus, run, provider_mix: [{provider, records, share}], abstracts: {with_abstract, title_only, share_with_abstract}, outside_year_window: int, near_twins_undecided: int \| null, lower_bound_databases: [name], protocol_fingerprint, dedup_decided_at?}` computed from `literature/verified.json` (`sources[]` per record for the mix; `abstract` presence; `publication_year` against the protocol window) |

- A browser run ends before the snapshot (§4.3), so the corpus is frozen here: the researcher's accept on this screen is the only browser path that builds the snapshot (decision 2026-11-10, from M3d-engine on).
- Accept and prepare are the existing `POST /screening/corpus/accept` and `POST /screening/prepare`; acceptance already journals `ARTIFACT_ACCEPTED` and `CORPUS_SNAPSHOT_ACCEPTED`. The board's two options are not new routes: "Fill missing abstracts" is the hydration stage that `run` already performs (`ABSTRACT_HYDRATION`), so the screen states whether it ran; "Hide the database of origin while screening" is the existing screening blinding setting (`PUT /screening/settings`), linked, not duplicated.
- "Export RIS for Zotero" reuses the screening export route when it lands for the corpus; out of this packet.

## 5. Allowlists and transport

Both lists change together (`console/browser.py:40-65`, `apps/research-ui/app/api/console/[...path]/route.ts:48-102`, kept equal by `tests/console/test_browser_access.py`):

- POST: `api/v1/discovery/(runs|recall)`, `api/v1/discovery/jobs/[A-Za-z0-9_-]+/cancel`, `api/v1/discovery/dedup/decisions` (Stage 2).
- PUT: `api/v1/discovery/report/methods`.
- Stream paths (proxy `STREAM_PATHS`): `api/v1/discovery/jobs/<id>/events`.
- `/jobs/start` stays `405` from the browser. Discovery runs go through their own typed route, as recon does, so the proxy never becomes a general job starter.
- Phone tokens (`_PHONE_ROUTES`, `serve.py:56-64`) get no discovery route: discovery is desktop-only, like inception.

## 6. Decisions (taken by the researcher, 2026-11-10)

1. **A run executes in-process**, like recon (`ReconJobs`): leg progress comes from `progress_callback` and the coordinator's stage results, which a `uv run` subprocess would only expose as log lines. Accepted cost: a long run holds the console process, and closing the console stops it (the archived run stays `PARTIAL`). The `JobRunner` alternative (`discovery_run` action with a `legs.json` poll) is not built.
2. **Near-twin review (E4b) is Stage 2**: counts per tier first (plan §7 cut 3). Whether the pair review is built at all is decided after the researcher's own corpora show how many near-twins survive the tiers.
3. **The recall check is check-only.** `validate_and_heal` stays off the console; the executed query is always the protocol's. A miss is recorded in the check and the report and never blocks the run; the fix is a protocol amendment through inception.
4. **The plan dry run (E1) is built**: every provider exposes its translation without a request, with a test that the preview equals the replayed golden legs' `executed_query`. No behaviour change.
5. **The contact email stays an environment variable** (`SCHOLAR_MAILTO`, decision 2026-11-08). On `MAILTO_NOT_SET` the screen prints the exact line to set and offers Retry; the browser writes no settings file. Revisit after testers.
6. **CSV import is out** until a tester brings a CSV-only export; the Import screen says "RIS or PubMed .nbib".
7. **A per-run cap override is allowed from the browser**, recorded as `cap_source: "run_override"` on every leg and on the run and printed in the report; the plan screen shows only the protocol cap.

## 7. Milestone split and lanes

| Milestone | Content | Lane | Needs |
| :-- | :-- | :-- | :-- |
| **M3b-api** | Layer R routes (plan without E1, runs, run, report markdown, report-v1 without `by_tier`, handoff), Layer J (runs in-process, recall with E2, jobs, events, cancel, cap override), refusals registered, allowlists, proxy stream path, E5 typed codes | STANDARD (no snapshot semantics change; `generate_contract_baseline.py --check` in every commit) | decided |
| **M3c-screens** | Specs 01–04, 06–08 `Status: FINAL` from the boards against M3b-api, then the screens; 05 as counts only; the `MAILTO_NOT_SET` state prints the line to set | STANDARD | M3b-api merged |
| **M3d-engine** | E1 dry run, E3 import rejections and `limits` (no CSV), E4a tiers | STANDARD | decided |
| **M3e-neartwins** | E4b pairs, decisions, acceptance reads them | RELEASE (Packet B inputs) | after the researcher's own corpora show the need |

## 8. Tests each route brings (names to create)

- `tests/console/test_discovery_api.py`: `test_plan_refuses_without_a_protocol`, `test_plan_reports_the_protocol_cap_and_the_ceiling`, `test_runs_lists_every_search_run_newest_first_and_marks_stale_ones`, `test_a_run_cannot_start_without_a_contact_email`, `test_a_run_cannot_start_on_an_accepted_snapshot`, `test_one_discovery_job_per_workspace`, `test_run_events_replay_snapshot_legs_stages_and_done`, `test_cancel_keeps_fetched_records_and_archives_a_partial_run`, `test_recall_never_rewrites_the_query`, `test_recall_reports_a_doi_title_mismatch_and_keeps_the_seed`, `test_report_marks_a_capped_leg_as_a_lower_bound`, `test_methods_text_is_a_draft_until_reviewed`, `test_handoff_counts_abstracts_and_the_year_window_from_verified_json`.
- `tests/console/test_browser_access.py`: the new POST/PUT paths allowed, `/jobs/start` still refused.
- `apps/research-ui/tests/console-proxy.test.ts`: the discovery stream path streams.
- `tests/pipeline/test_golden_search_cassettes.py`: the dry run's executed strings equal the replayed legs' (E1).
- `tests/console/test_console_refusals.py`: every new code registered.
