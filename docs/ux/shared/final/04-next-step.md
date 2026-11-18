# 04 Next step    Status: FINAL, not built (questions closed by the researcher 2026-11-15) | Shared (every screen of a review) | Route none (a bar in the shell, `AppShell`) | Milestone M10b (engine state, endpoint and bar), Part C of the build; the per-run stage marker, resume and Stop came first in their own fix, M3i-harvest-robustness (merged, PR #235)

**Order of work (decided 2026-11-15; reconciled 2026-11-18).** The harvest's robustness was fixed on its own before the M10b build: M3i-harvest-robustness merged on 2026-11-18 (PR #235). It writes the per-run stage marker `literature/search_runs/run_NNN/pipeline.json` (with `verified_run`), offers "Finish preparing this corpus" on Harvest (`POST /discovery/runs/{run}/prepare`, job kind `prepare`), honours Stop between the stages, and serves a `preparation` view (`pipeline/harvest_marker.py::preparation_view`: `state` one of `none`, `superseded`, `ready`, `running`, `failed`, `stopped`, `interrupted`; `stage`; `can_finish`; `cannot_finish`) on `GET /discovery/runs`, `/runs/{run}` and `/handoff`. The bar reads that view through the engine's own function; it never reads `pipeline.json` itself. Where this spec still says "✗ M3i-harvest-robustness", read "✓ M3i, PR #235".

Boards: none. No canvas board exists. The bar reuses the patterns of the step bars (`discovery-frame.tsx:77`, `inception-frame.tsx:202`) and the state card (`screening-state-card.tsx`); no new visual language. Records: `docs/roadmap/milestones/M10b-proposals-checks.md` ("a what's next bar on every screen of a review, computed by the engine"). Source of the scope: the strict UAV acceptance run of 2026-11-13. Neighbouring specs: `docs/ux/phase1-discovery/final/07-states.md`, `08-handoff.md`, `09-chase.md`; `docs/ux/phase2-screening/final/00-workspaces.md`, `01-screening-home.md`; `docs/ux/phase0-inception/final/07-done.md`. Brand: `docs/ux/brand/BRAND_BOOK.md` (one brand button per screen; machine output as a draft), `docs/ux/brand/tokens.json`.

**Purpose.** On every screen of a review, say in one sentence what the researcher should do next and take them there with one button; when something is running, failed or stopped, say that instead, with the reason.

**Changed from the existing specs.** No board exists, so each point is where the bar touches a finished spec. None of those specs is edited by this file; the amendments are listed under "Dependencies" and are made when this spec is FINAL.
- **The bar never accepts, starts, publishes or decides.** It is a link to the screen that owns the action. The gates (Accept this corpus, Send these works to screening, Publish) stay on their screens (decision 2026-11-14: an assistant never accepts a corpus, makes a screening decision or publishes). So the bar's label is "Review and accept the corpus", never "Accept this corpus".
- **The state is computed by the engine.** The browser never inspects files, counts, fingerprints or job stages to pick a sentence (`apps/research-ui/AGENTS.md`: no domain decision in frontend code). It receives a state code, copy parameters as the engine wrote them, and a destination screen name.
- **The Hand-off gains the bar above its own states** (`08-handoff.md` "The next-step bar (M10b)", the amendment this spec needs). Since M3i the Hand-off's "Not ready" state already names an unfinished preparation and links to Harvest; the bar adds the same engine state in one line, and on "Empty" it says why there is nothing to hand off (see "The Hand-off case, exactly").
- **Not added:** a progress percentage, a "step n of m" count, an estimate of time left (the engine has none), and any suggestion about the content of the review (that is M10c).

## Entry / exit
- Entry: none of its own. The bar is rendered by the shell on every route of a review (see Desktop layout for the exceptions).
- Exit: its one button, a plain link to the destination screen, carrying `?console=` and, where the screen needs one, `?run=`, `?job=` or `?draft=` (the engine names them in `action.to.query`; the browser adds only `console`).
- Gate: none. The bar writes nothing.

## Data in
| Field | Source |
| :-- | :-- |
| `shape`, `scope` (`workspace` or `draft`), `phase` (`inception`, `discovery`, `screening`, `published`), `state` (a code from the table), `round` | `GET /api/v1/review/next-step` ✗ M10b |
| `params` (counts and names the sentence prints, as the engine wrote them) | same |
| `waiting` (`null` or `{kind: "running" \| "stopped" \| "failed" \| "interrupted", job, stage, reason{code, message}, since}`) | same |
| `action` (`null` or `{key, to{screen, query}}`) and `also[]` (at most one secondary link) | same |
| `unknown[]` (what the engine could not read, for the hedged sentence), `computed_at` | same |
| for a draft, the same shape | `GET /api/v1/inception/drafts/{id}/next-step` ✗ M10b |

The engine builds the answer only from the sources in the next table. Each is an existing field or file; where a state cannot be told apart today, the table says what the engine must add (✗ M10b).

| Source the engine reads | Where it exists today |
| :-- | :-- |
| protocol present and valid; fingerprint | `_protocol`, `console/api/discovery.py:227` (`PROTOCOL_MISSING` 409, `PROTOCOL_INVALID` 422) |
| contact email and OpenAlex key set; selected databases | `GET /discovery/plan` `mailto_set`, `openalex_key_set`, `providers`, `discovery.py:399-428`; the run's own refusals `discovery.py:248-269` |
| search runs: `status`, `raw_published`, `fetched_total`, `legs_total`, `started_at`, `finished_at`, `stale`, `protocol_changed`, `search_changed` | `GET /discovery/runs`, `discovery.py:324-353`; manifest `legs.json` (`corpus_published`, `raw_published`, `legs[].status`, notes "cancelled by the researcher") written at `pipeline/discovery.py:496-507`, `:613-660` |
| the running job: `kind`, `state`, `started_at`, `error{code,message}`, and while it lives the events `snapshot`, `leg`, `stage` (`discovery`, `deduplication`, `hydration`, `verification`, `corpus_snapshot`), `done`, `failed` | `DiscoveryJobs`, `discovery.py:86-153`; `stage` events from `run_pipeline`, `pipeline/coordinator.py:622, 687, 702, 731, 741`; read as `active_job` in `GET /discovery/runs` and `/discovery/chase`. Used for variants A and F only; the preparation stages come from `preparation`, not from job events |
| a run's `preparation` (`state`, `stage`, `can_finish`, `cannot_finish`, `message`) | ✓ M3i: `console/api/discovery.py` `_preparation(ws, run_dir, manifest, newest_published=…, active=<the active discovery job>, frozen=…)`, the function `GET /discovery/runs` and `/handoff` use. With the active job it answers `running` for the run a live job is preparing. The builder never uses `harvest_marker.pending_preparation`, which has no job and never answers `running` |
| `literature/deduped.json` (count after duplicates), `literature/dedup/clusters.json` | `pipeline/deduplication.py:161`, `:52`; counts `_dedup_summary`, `discovery.py:528-556` |
| `literature/verified.json` (the verification stage writes it) and `literature/verified_unresolved.json` (quarantine) | `pipeline/verification.py:172`, `:188`; read as `from_discovery`, `corpus_accept.py:651-656` |
| corpus: `state` (`EMPTY`, `STAGED`, `ACCEPTED`), `from_discovery`, `sources[]`, `preview`, `accepted`, `staging_refused` | `corpus_status`, `corpus_accept.py:608-670`; `GET /screening/corpus`, `screening_v1.py:569` |
| batches prepared; `total`, `decided`, `needs_you`, `conflicts`, `protocol_changed` | `GET /screening/summary`, `screening_v1.py:136-166` (`ev.load_context(ws).batches` empty means nothing prepared) |
| the prepare job: `action_id` `screen_prepare`, `state` `queued`, `running`, `success`, `failed`, `cancelled`, `exit_code` | `GET /api/v1/jobs`, `console/api/jobs.py:86`; `job_runner.py:63, 171, 228, 453`; started at `screening_v1.py:661` |
| publication: `status` (`CURRENT`, `STALE`, ...), `code` `GENERATION_STALE`, `generation_id` | `GET /ui/publication-status`, `workspace.py:405-425, 576`; `catalog._status`, `workspace/catalog.py:88-107` |
| chase: `screening{published, round, arm}`, `seeds{chaseable}`, `runs[]` (`published`, `accepted`, `counts.new`), `active_job` | `GET /discovery/chase`, `discovery.py:979-1030` |
| inception draft: `draft` fields, `emitted{slug, path, ...}`, `updated_at` | `drafts.py:112-141`, `GET /inception/drafts/{id}`; the missing fields exist only as the `DRAFT_INCOMPLETE` refusal (`inception/steps.py:216-219`) |

## The state table
Computed top to bottom; the first row whose condition holds is the answer (so a later row never needs to say "and not"). `waiting` is a second, independent field: a state may carry a waiting variant (table 2). Sentences are the en master (`next.state.<CODE>`); `{...}` are params printed as the engine wrote them (`bdi`, LTR for ids and numbers). The button is secondary-styled (see Desktop layout). "Screen" names a route: `inception.*` `/[locale]/inception/<step>`; `discovery.*` `/[locale]/discovery/<step>`; `screening.*` `/[locale]/screening/<step>`.

### Table 1. States in order
| # | State code | Condition (files and fields; ✓ exists, ✗ M10b adds) | Sentence | Button → destination |
| :-- | :-- | :-- | :-- | :-- |
| 1 | `NO_REVIEW` | `app.state.workspace` is `None`, or no valid row in `GET /workspaces` ✓ (`workspaces.py:33`; `catalog.listing`). The engine never knows the browser's route; it answers this state itself, because the route is workspace-free (see "The new endpoint") | "No review is open." | "Choose or start a review" → `workspaces` (or `inception.list` when the listing is empty) |
| 2 | `DRAFT_STARTED` (scope `draft`) | a draft record exists, `emitted` is `null` ✓ (`drafts.py:70`), and a field the Scope step needs is empty (`topic`) ✗ the engine must compute `missing[]` without a genesis attempt; today only `_require` raises `DRAFT_INCOMPLETE` (`steps.py:216`) | "Your draft has no topic yet." | "Go to Scope" → `inception.scope?draft=` |
| 3 | `DRAFT_INCOMPLETE` (scope `draft`) | `emitted` null and `missing[]` names fields; the step per field is the browser's existing `FIELD_STEP` (`inception-frame.tsx:74`) but the engine names the step: `action.to.screen` = the first missing field's step in the order Scope, Explore, Direction, Shape, Criteria, Review ✗ M10b | "Your draft still needs {fields}." | "Go to {step}" → that step |
| 4 | `DRAFT_READY` (scope `draft`) | `emitted` null and the checks builder of `02-checks` answers `ready: true` for the saved draft (no open blocker: every required field present, every wizard criterion decided, both sides, the compiler accepts, the folder is usable, the binding is not stale). One function, so the bar never says "complete" while Review lists a "Must fix" row. With fields present but a blocker open, row 3 does not hold and the answer is `DRAFT_INCOMPLETE` with `params.fields` naming the blocker's field and the step of its action | "Your draft is complete. Create the workspace when you are ready." | "Go to Review" → `inception.review?draft=` |
| 5 | `DRAFT_CREATED` (scope `draft`) | `emitted` not null (`drafts.py:112`) | "The workspace {title} exists. Open it to continue." | "Go to the finished workspace" → `inception.done?draft=` (Open is on that screen; spec 07) |
| 6 | `NO_PROTOCOL` | scope `workspace`; `protocol.json` missing (`discovery.py:233-235`, `PROTOCOL_MISSING`) | "This review has no protocol yet." | "Go to inception" → `inception.list` |
| 7 | `PROTOCOL_INVALID` | `protocol.json` fails `ResearchProtocol` validation (`discovery.py:236-240`, `PROTOCOL_INVALID`) | "The protocol file cannot be read, so nothing can be searched." | "Go to inception" → `inception.list` |
| 8 | `PROTOCOL_PLACEHOLDER` | the protocol is the placeholder a New workspace scaffolds (`00-workspaces.md` decision 5) ✗ M10b: no field marks it today; `project.json` must carry a `protocol_origin` of `placeholder` or `inception`, so the engine can tell | "This protocol is a placeholder. Write your own with New review." | "Go to inception" → `inception.list` |
| 9 | `SETUP_NEEDED` | `plan.mailto_set` false, or `plan.openalex_key_set` false while `openalex` is in `plan.providers` (`discovery.py:420-421`; the run refuses with `MAILTO_NOT_SET` / `OPENALEX_KEY_NOT_SET`, `:248-269`); no search run yet | "A search needs {what}." (`what` = "a contact email", "an OpenAlex key" or both) | "See what to set" → `discovery.plan` (prints the exact line) |
| 10 | `READY_TO_SEARCH` | protocol valid; no run dir with `legs.json` (`_run_dirs`, `discovery.py:281`); `corpus.state` `EMPTY` (`corpus_accept.py:622`); no `active_job` | "Your protocol is ready. Run the search." | "Go to Harvest" → `discovery.harvest` |
| 11 | `STAGED_EXPORTS` | `corpus.state` `STAGED`, `from_discovery` false, `sources` not empty (`corpus_accept.py:622, 651`) | "{n} database exports are staged. Accept them to start screening." | "Review and accept the exports" → `discovery.handoff` |
| 12 | `SEARCH_CHANGED` | the corpus run's `search_changed` true (`discovery.py:741`, `_drift`), `corpus.state` not `ACCEPTED`; the accept would be refused `PROTOCOL_CHANGED_SINCE_RUN` (`08-handoff.md`) | "You changed the search after run {run}. Search again before you accept." | "Go to Harvest" → `discovery.harvest` |
| 13 | `CORPUS_READY` | the corpus run's `preparation.state` is `ready` (✓ M3i: `verified_run` names that run and `verified.json` exists), `corpus.state` `STAGED`, `from_discovery` true (`corpus_status`; since M3i `from_discovery` is false while the preparation is unfinished); `search_changed` not true; not accepted | "Your corpus is ready: {works} works from {records} records. Accept it to start screening." | "Review and accept the corpus" → `discovery.handoff` |
| 14 | `SEARCH_UNFINISHED` | a harvest job is running and no run is published yet, or the newest run is not published (`raw_published` false: a `FAILED` run or a stopped search, `discovery.py:324-353`). Always carries `waiting` (table 2 rows A, G(a) or H). Added 2026-11-18: before, a first harvest that was still searching, failed or stopped matched no row | see table 2 | "Follow the search" or "Search again" (table 2) |
| 15 | `CORPUS_PENDING` | the newest run is published (`raw_published` true), nothing is staged, and its `preparation.state` is `running`, `failed`, `stopped` or `interrupted` (✓ M3i, read through `_preparation` with the active job): this is the Hand-off case. Always carries `waiting` (table 2 rows B to D, G(b), I, J) | see table 2 | "Follow the search", "Finish preparing this corpus" or "Search again" (table 2) |
| 16 | `NOT_PREPARED` | `corpus.state` `ACCEPTED`; `summary.total` 0 (no batches, `screening_v1.py:139-147`); no `screen_prepare` job running | "The corpus is accepted. Prepare the screening batches." | "Go to screening" → `screening.home` (Prepare lives there, `screening-home.tsx:305`) |
| 17 | `PROTOCOL_CHANGED_AFTER_BATCHES` | `summary.protocol_changed` true (`screening_v1.py:165`) | "The protocol changed after screening started, so earlier decisions count nowhere." | "Open inception" → `inception.list` (spec 01 "Protocol changed after screening started") |
| 18 | `CONFLICTS` | `summary.conflicts` > 0 (`screening_v1.py:161`) | "{n} decisions conflict. Resolve them before you go on." | "Go to screening home" → `screening.home` (the conflict card is there; no conflicts screen exists) |
| 19 | `SCREENING` | `summary.needs_you` > 0 | "{needs_you} of {total} records still need you." | "Open triage" → `screening.triage` |
| 20 | `READY_TO_PUBLISH` | `summary.total` > 0, `needs_you` 0, no `generation.json` (`catalog._status` is not `PUBLISHED`) | "Every record is decided. Check the agreement, then publish." | "Go to Publish" → `screening.publish` |
| 21 | `PUBLISHED_STALE` | publication `status` not `CURRENT`, `code` `GENERATION_STALE` (`workspace.py:405-425`; `catalog` `PUBLISHED_CHANGED`) | "{n} studies changed since you published." | "Publish again" → `screening.publish` |
| 22 | `PUBLISHED` | publication `CURRENT`; `chase.screening.published` true; no chase run (`runs` empty); `seeds.chaseable` > 0 | "Screening is published. You can chase the citations of your included studies." | "Go to Chase" → `discovery.chase` |
| 23 | `CHASE_READY_TO_SEND` | newest chase run `published` true, `accepted` null, `counts.new` > 0, no `active_job` (`discovery.py:979-1022`) | "The chase found {new} new works. Send them to screening as round {round}." | "Review and send the works" → `discovery.chase` |
| 24 | `CHASE_NOTHING_NEW` | newest chase run `published` true, `counts.new` 0, `EMPTY_RESULT` | "The chase found nothing new." | "Go to Chase" → `discovery.chase` |
| 25 | `ROUND_ACCEPTED` | `chase.screening.round` > 1 and the round's batches are not prepared | "Round {round} is with screening. Prepare its batches." | "Go to screening" → `screening.home` |
| 26 | `DONE` | publication `CURRENT`, and either no chaseable seed (`seeds.chaseable` 0: "No included study can be chased.") or the latest round published and its chase empty | "Nothing is waiting for you. Export and methods are on Publish." | "Go to Publish" → `screening.publish` |

Rows 16 to 21 repeat for round 2 and later (`round` from `chase.screening.round`, `screening_v1` summary reads the current round's batches only, `rounds.py:92`); the sentences gain "in round {round}" when `round` > 1.

### Table 2. Waiting, failed, stopped and interrupted variants
`waiting` is set when a job is running, or when the newest run ended without a usable result. It replaces the sentence and the button of the state it sits on. A waiting bar is a `role="status"` line; its reason sits behind a Details disclosure with the typed code (rule: details on demand, `docs/ux/phase2-screening/final/12-details-disclosure.md`).

| | Variant (`waiting.kind`, `stage`) | Condition | Sentence | Button → destination |
| :-- | :-- | :-- | :-- | :-- |
| A | `running`, `searching` | state `SEARCH_UNFINISHED`; `active_job.kind` `run` and the run it searches is not published yet (`DiscoveryJobs.active`, `discovery.py:123`) | "The search is running. {answered} of {databases} databases have answered." | "Follow the search" → `discovery.harvest?job=` |
| B | `running`, `deduplicating` | `preparation.state` `running` and `preparation.stage` `deduplication` (✓ M3i; the engine's stage names map to the bar's: `deduplication` to `deduplicating`, `hydration` to `adding_abstracts`, `verification` to `verifying`, decision 2026-11-17 item 1). A `prepare` job (Finish preparing) reads the same. Deduplication runs on the event loop; the engine may not answer reads during it, see Offline | "The search found {records} records. Removing duplicates." | "Follow the search" |
| C | `running`, `adding_abstracts` | `preparation.state` `running`, `stage` `hydration` (✓ M3i) | "{works} works remain after duplicates. Adding missing abstracts." | "Follow the search" |
| D | `running`, `verifying` | `preparation.state` `running`, `stage` `verification` (✓ M3i) | "Checking {works} works against the databases. The hand-off opens when this ends." | "Follow the search" |
| E | `running`, `preparing` | `GET /jobs` has a `screen_prepare` job `queued` or `running` (`job_runner.py:63, 171`) | "Preparing the screening batches." | "Follow the preparation" → `screening.home` |
| F | `running`, `chasing` | `active_job.kind` `chase` (`discovery.py:1057`) | "The citation chase is running." | "Follow the chase" → `discovery.chase?job=` |
| G | `stopped`, `searching` or a preparation stage | (a) State `SEARCH_UNFINISHED`: the search was stopped: newest run `PARTIAL`, `raw_published` false, a leg `stopped`, note "cancelled by the researcher"; job `cancelled`. (b) State `CORPUS_PENDING`: the preparation was stopped (✓ M3i): `preparation.state` `stopped`, `stage` the stage that did not start | (a) "You stopped the search. What was fetched is kept, but no corpus was made." (b) "You stopped the search while {stage}. The corpus was not made." Reason `STOPPED_BY_RESEARCHER`. | (a) "Search again" → `discovery.harvest`. (b) "Finish preparing this corpus" → `discovery.harvest` when `can_finish`, with "Search again" in `also`; "Search again" alone otherwise |
| H | `failed`, `searching` | state `SEARCH_UNFINISHED`; newest run `FAILED` or job error `PROVIDERS_FAILED` (`discovery.py:766-780`) | "No database answered, so nothing was kept." Reason `PROVIDERS_FAILED` and the legs' codes. | "Search again" → `discovery.harvest` |
| I | `failed`, `deduplicating`, `adding_abstracts` or `verifying` | `preparation.state` `failed` (✓ M3i: read from the marker, so it survives a console restart), `stage` and `message` from it | "The search finished, but preparing the corpus failed at {stage}. {message}" Reason `DISCOVERY_FAILED` with the marker's message. | "Finish preparing this corpus" → `discovery.harvest` (no new search) when `can_finish`, with "Search again" in `also`; "Search again" alone when `cannot_finish` |
| J | `interrupted`, the marker's stage or unknown | `preparation.state` `interrupted` (✓ M3i: the marker never ended and no job is running, or a run made before the marker has no `verified.json`) | "The search finished, but the corpus was not prepared. The console may have been closed while it ran." Reason `INTERRUPTED`, cause unknown; the stage is named under Details when the marker has one. | "Finish preparing this corpus" → `discovery.harvest` (no new search) when `can_finish`, with "Search again" in `also`; "Search again" alone when `cannot_finish` |
| K | `running`/`failed`, `accepting_chase` | `WORKSPACE_JOB_ACTIVE` on the accept (`09-chase.md`) | "Wait for the running job to end, then send these works." | "Go to Chase" |

Reasons are shown as `waiting.reason{code, message}`. Codes are the engine's: `STOPPED_BY_RESEARCHER` and `INTERRUPTED` are new labels (✗ M10b, they are not refusals and are not added to `console/refusals.py`); `PROVIDERS_FAILED`, `DISCOVERY_FAILED`, `PROVIDER_*` are registered (`07-states.md`). The page never guesses a meaning for an unregistered code; it prints the engine's text under Details.

### The Hand-off case, exactly
A harvest has finished its search (1,074 records, 1,050 works after duplicates), nothing is staged, and the researcher opens the Hand-off:
1. The run list shows the newest run `raw_published` true; Harvest shows every leg done.
2. `deduped.json` exists (1,050 works). The run's marker has not ended `DONE` with `verified_run` equal to the run, so `verified.json` is missing or an earlier run's.
3. Since M3i `corpus_status` reports `from_discovery: false` and the Hand-off shows its "Not ready" state: "The corpus is not ready to hand off yet." with one sentence by `preparation.state` and the link to Harvest ("Finish preparing this corpus on Harvest", "Follow the harvest" while running, "Open Harvest" when the run cannot be finished; `08-handoff.md` "An unfinished preparation (M3i)"). The accept would be refused `PREPARATION_UNFINISHED`.
4. The engine's answer is state `CORPUS_PENDING` with `waiting`, read from `_preparation` with the active job:
   - a live job is preparing the run (`preparation.state` `running`): variant B, C or D by `preparation.stage` (`deduplication` → `deduplicating`, `hydration` → `adding_abstracts`, `verification` → `verifying`), for example "Checking 1,050 works against the databases. The hand-off opens when this ends." with "Follow the search";
   - `preparation.state` `failed`: variant I with the marker's stage and message, and "Finish preparing this corpus" when `can_finish`;
   - `stopped`: variant G(b), same button rule;
   - `interrupted` (the marker never ended and no job is preparing the run, or a run made before the marker has no `verified.json`): variant J, "Finish preparing this corpus" when `can_finish`, else "Search again".
5. With an export staged the answer is `STAGED_EXPORTS` (row 11) instead: the accept takes the exports and the unfinished harvest is left as a record (M3i decision item 10).
On the Hand-off the bar's destination for these variants is Harvest, which is not the current screen, so the bar shows its button; the page's own link goes to the same place (`08-handoff.md` "The next-step bar (M10b)").
Before M3i the same folder read as an empty Hand-off ("There is nothing to hand off yet") and the accept could freeze an earlier run's works under the newer run's name.

### What M3i settled, and what is still M10b's
- **Which stage a preparation is in, after a restart too**: ✓ M3i (`pipeline.json`, `preparation.state` and `stage`).
- **Whether `verified.json` belongs to the newest run**: ✓ M3i (`verified_run`; `preparation.state` is `ready` only then; the accept refuses `PREPARATION_UNFINISHED` otherwise).
- **Stop in the later stages**: ✓ M3i (read before each stage; a running stage is not interrupted; the marker records `STOPPED` and the stage).
- **Placeholder protocol** (row 8): ✗ M10b. `project.json` gets `protocol_origin`: `placeholder` from the placeholder scaffold of `nexus-scholar init`; `inception` or `import` (a draft started from an earlier review, `09`) from both genesis paths, the web genesis and the CLI `emit_workspace`, and from `_refresh_manifest` on a replacement, so a replaced placeholder becomes `inception` or `import`. A workspace without the field is read as `inception` (never guessed as a placeholder).
- **Works count before verification**: ✗ M10b. The engine reads `len(deduped.json)` and `fetched_total` itself for the `{works}` and `{records}` params of rows B to D.
- **Cause of an interruption** (console closed or crashed): not recoverable; the marker records only that it ended unfinished.
- **Dedup blocking the engine**: deduplication still runs on the event loop (M3i decision item 6 lists moving it off as a follow-up); the bar's Offline state covers it.

## Data out
None. The bar writes nothing and journals nothing. Its refresh may read, never act.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/review/next-step` (scope `workspace`; the engine's current workspace) | ✗ M10b |
| `GET /api/v1/inception/drafts/{id}/next-step` (scope `draft`) | ✗ M10b |
| `literature/search_runs/run_NNN/pipeline.json` stage marker; `verified_run`; the `preparation` view | ✓ M3i, PR #235 (`pipeline/harvest_marker.py`; read by the builder through `console/api/discovery.py` `_preparation` with the active job, which calls `preparation_view`; never through `pending_preparation`) |
| `project.json` `protocol_origin` (`placeholder`, `inception` or `import`; written by the placeholder scaffold, by both genesis paths and by `_refresh_manifest` on a replacement; project metadata, no Contract v1 change) | ✗ M10b (engine writes, no route) |
| `GET /api/v1/discovery/runs`, `/plan`, `/handoff`, `/chase`, `/jobs/{id}/events`, `/jobs/{id}` | ✓ `discovery.py:440, 399, 698, 1025, 913, 904` (read by the engine's own function, not by the browser) |
| `GET /api/v1/screening/summary`, `/corpus`, `/ui/publication-status`; `GET /api/v1/jobs` | ✓ `screening_v1.py:136, 569`; `workspace.py:576`; `jobs.py:86` |
| `GET /api/v1/inception/drafts/{id}` | ✓ `inception.py:99` |
| `GET /api/v1/workspaces` | ✓ `workspaces.py:33` |

### The new endpoint
`GET /api/v1/review/next-step` (no query) and `GET /api/v1/inception/drafts/{session_id}/next-step`. Both are reads, answer `200`, take the engine's own functions (no HTTP call to itself) and share one builder, `console/next_step.py` ✗ M10b (a pure function of the workspace folder, the job registries and the draft record, so a test drives it from a folder). **`GET /api/v1/review/next-step` is workspace-free** ✗ M10b: today the console middleware answers `409 WORKSPACE_NOT_VALID` for any `/api/` route outside `_workspace_free` when no workspace is open (`console/serve.py`, `_workspace_free` and `_no_workspace`), so the path is added to `_workspace_free`, and the route answers `NO_REVIEW` itself when no workspace is open. The draft route is under `/api/v1/inception/`, already workspace-free. The proxy (`apps/research-ui/app/api/console/[...path]/route.ts`) forwards GET; GET routes need no allow-list entry. Neither is in `_PHONE_ROUTES` (`serve.py:59`): a phone-scoped token gets `TOKEN_SCOPE_REFUSED` and the bar renders nothing.

Response, in the style of the existing routes (`shape`, engine-written values, nulls explicit):
```json
{
  "shape": "review.next-step-v1",
  "scope": "workspace",
  "phase": "discovery",
  "round": 1,
  "state": "CORPUS_PENDING",
  "params": {"run": "run_003", "records": 1074, "works": 1050, "databases": 5, "answered": 5},
  "waiting": {
    "kind": "running",
    "stage": "verifying",
    "job": {"job_id": "djob_ab12cd34ef56ab12", "kind": "run", "state": "running", "started_at": "2026-11-13T09:40:12+00:00"},
    "reason": null,
    "since": "2026-11-13T09:52:30+00:00"
  },
  "action": {
    "key": "followSearch",
    "to": {"screen": "discovery.harvest", "query": {"job": "djob_ab12cd34ef56ab12"}}
  },
  "also": [],
  "unknown": [],
  "protocol_fingerprint": "…as the engine wrote it…",
  "computed_at": "2026-11-13T09:52:41+00:00"
}
```
- `state` is one of the codes in table 1; `waiting.stage` one of `searching`, `deduplicating`, `adding_abstracts`, `verifying`, `preparing`, `chasing`, `accepting_chase`; `waiting.kind` one of `running`, `stopped`, `failed`, `interrupted`; `waiting.reason` is `{code, message}` for `stopped`, `failed`, `interrupted`, else `null`.
- `action.key` selects the button label (`next.action.<key>`); `action.to.screen` is a screen name the browser maps to a route in one table; `action.to.query` holds only ids (`run`, `job`, `draft`). The engine does not know which screen the researcher is on, so it sends `to.screen` only; the browser compares it with the current screen name to choose between the button and the naming form (see Desktop layout). That is presentation, not a domain decision.
- `unknown[]` lists what could not be read (`journal`, `jobs`, `publication`); the sentence for a hedged state is the same, with the line "Some information could not be read." behind Details. The state is still computed from what was readable; the engine never invents a state.
- No ETag and no `304`: the proxy forwards neither `If-None-Match` nor `ETag`. The browser keeps the answer with the newest `computed_at` and discards an older one that arrives late.
- Refusals: none of its own (so no new code in `console/refusals.py`). No workspace open is the state `NO_REVIEW`, not a refusal. A workspace read error is `unknown[]`, not a 5xx. `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE` (draft route, existing codes, `07-done.md`), `TOKEN_SCOPE_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED` (shared guards).

### When the bar refreshes
Job events and writes that already exist trigger a re-read; nothing is added to the job streams.
- On mount and on every route change inside the shell.
- On the discovery job stream's events seen by the page: `stage`, `done`, `failed` (`discovery.py:913-933`, `job.emit` at `:112`; `useJobStream` in `discovery-frame.tsx:355`) and `snapshot` on connect. The hook dispatches a `nexus:review-changed` window event on those; the bar listens. `leg` events are ignored (too frequent; the bar's A sentence refreshes on the next stage or poll).
- After a write the page makes and the engine answered: start run, cancel, corpus accept, source stage or remove, prepare (`screening_v1.py:644`), publish, chase start or accept, draft save, genesis, workspace open. Each screen already knows when it wrote; it dispatches the same event.
- While `waiting.kind` is `running`: a poll every 5 s, because a page that holds no stream (the Hand-off, Home, Import) gets no event. The poll stops when `waiting` is null.
- On window focus and when the tab becomes visible, if the last answer is older than 30 s.
- Never on a timer when nothing is waiting, and never more than one request in flight.

## States
- **Default**: one line, `bg-leaf` with a `rule` border: the sentence, then the one secondary button; the state code is behind a Details disclosure ("Details": state, run or job ids, the engine's time).
- **Empty**: no bar when there is nothing to say: `DONE` still shows its sentence; scope `workspace` with no workspace on `/workspaces` shows none (the screen is the next step); a phone token shows none.
- **Loading** (skeleton): a one-line skeleton of the bar's height with `aria-busy="true"`, no sentence and no button until the first answer, so the layout does not jump and no wrong sentence flashes. A refresh keeps the previous answer on screen (no skeleton).
- **Error** (typed refusal → copy): `ENGINE_UNREACHABLE` (client-side, proxy `CONSOLE_UNREACHABLE` 502 / `CONSOLE_TIMEOUT` 504): "The page cannot reach the engine, so what comes next is not known. Last answer: {state sentence} as of {time}." with no button (the screen's own card says the rest); `TOKEN_SCOPE_REFUSED`: the bar is not rendered; `HOST_REFUSED`, `TOKEN_REQUIRED`: not rendered (the screen's guard card says it); draft route `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE`: not rendered (the screen's card says it). An unregistered code prints itself under Details.
- **Partial**: `unknown[]` not empty: the sentence stays, the line "Some information could not be read." sits behind Details, and the state is the engine's best reading. States `INTERRUPTED` (J) and the missing `pipeline.json` of a run made before M3i read as "cause unknown", never as a guess.
- **Offline**: the engine is local, so offline means unreachable: the error state above. The last answer stays with "as of {time}"; the button is removed (a link to a screen that cannot load would mislead), re-added on the next answer. During variant B the engine may not answer (dedup runs on the event loop): the bar shows the offline state for those seconds and recovers on its own; it does not report it as a failure.
- **Stale / protocol changed**: the bar never compares fingerprints. States `SEARCH_CHANGED` (12) and `PROTOCOL_CHANGED_AFTER_BATCHES` (17) are the engine's flags (`search_changed`, `protocol_changed`); when `protocol_changed` is true and `search_changed` false before an accept, the engine still answers `CORPUS_READY` and adds `params.protocol_changed` true; the sentence gains "The protocol changed outside the search; accepting binds the records to it as it is now." (as spec 08). An answer older than the page's last write is discarded by `computed_at`.
- **Live-only**: yes. No fixture, no demonstration marker; the bar is absent on the screens that have none to show.

## Desktop layout
- **Where**: in `AppShell` (`apps/research-ui/components/app-shell.tsx:35-81`), a `<section role="region" aria-labelledby>` between the site header and `<main>`, outside `main` so a route's one `main` landmark is untouched (the shell comment at `:21-26`). The step bars (`DiscoverySteps`, `InceptionSteps`) stay inside the screens, below the bar. It is a sibling of the banner, in the document order: skip link, banner, bar, main. The skip link still targets `main`.
- **Which routes**: every `/[locale]/inception/*` (draft scope, `?draft=` read after hydration, as `useLocationParams`, `inception-frame.tsx:48`), `/[locale]/discovery/*` and `/[locale]/screening/*` (workspace scope). Not on `/workspaces` (the screen is the next step), not on the triage focus route (`isOneScreenRoute`, `app-shell.tsx:84`: a focus screen has no header at 1024 px and up and the bar would break the one-screen rule), not on a phone.
- **Look**: one row, `min-h-12`, the sentence on the inline start, the button on the inline end; `bg-leaf`, `rule` bottom border, `ink` text; a small state word before the sentence only in waiting variants (`Running`, `Stopped`, `Failed`, `Interrupted`, as text with the role colour: `brand` for running, `unclear` for stopped and interrupted, `blocked` for failed; text and icon, never a fill behind text). The sentence is not a draft: it is the engine's state, not a machine judgement about the research.
- **Not sticky.** It scrolls away with the page, so it never covers content or a focused element (WCAG 2.2 focus not obscured), and the triage and gate screens keep their full height.
- **It never competes with the screen's own main button.** Three rules, all decided by the browser from `action.to.screen` and the current screen name (a fixed route-to-screen table in one file; no engine call):
  1. The bar's button is secondary (outline, `brand` text and border, no fill). The brand fill is reserved for the screen's one brand button (`08-handoff.md`, `09-chase.md`: one brand button per screen).
  2. When `action.to.screen` is the current screen, the bar shows no button. It names the screen's own control instead, in words: "Next: {label}. The button is on this page." where `{label}` is the same `next.action.<key>` text the screen's own button carries. It is plain text, not a link (no second way to the same action, no focus stop).
  3. When the current screen is a gate (`discovery.handoff` in `CORPUS_READY`, `discovery.chase` in `CHASE_READY_TO_SEND`, `screening.publish`), the bar is in the naming form even if a waiting variant would point elsewhere; the gate's own panel carries the evidence.
- The Hand-off in `CORPUS_PENDING` is not a gate state (it has no accept there) and the bar's destination is Harvest, so the bar shows its button ("Follow the search" or "Finish preparing this corpus") above the page's own "Not ready" state (M3i), which links to Harvest too; `08-handoff.md` "The next-step bar (M10b)".

## Mobile layout (≤ 640 px)
Per plan §4, write, gate and job screens are desktop-only; the bar's states point at such screens, so a phone shows no bar (the route is outside `_PHONE_ROUTES`; the first read answers `TOKEN_SCOPE_REFUSED` and the bar renders nothing). The phone's own screens (home, triage, queue; spec 01) keep their own primary buttons. A narrow desktop window (≤ 640 px) shows the bar as a block under the header: the sentence (up to three lines, wraps), then the button full width at 44 px; the waiting state word above the sentence; Details below. Not sticky, not at the bottom (a phone home has a fixed primary button there). No gestures.

## Keyboard
Focus order: skip link, site header, the bar's button (when it has one), then the page. The bar has at most one tab stop; the naming form has none. No single-key shortcut (the existing `g t`, `g p`, `?` are untouched). `Enter` and `Space` activate the button; Details is a native disclosure. A refresh never moves focus. When the answer changes while the focus is on the button, the button's label and destination change in place and the live region announces the new sentence (below); focus stays.

## Copy
Keys in a new copy file `apps/research-ui/lib/next-step-copy.ts` ✗ M10b (en master; fr and ar fall back to en, plan §7). No literal `aria-label`, `title`, `alt` or `placeholder` (N9). Placeholders `{...}` are printed LTR in `bdi`.

Frame: `next.region` "What comes next"; `next.details` "Details"; `next.asOf` "As of {time}"; `next.unknown` "Some information could not be read."; `next.here` "Next: {label}. The button is on this page."; `next.offline` "The page cannot reach the engine, so what comes next is not known."; `next.offline.last` "Last answer: {sentence}"; `next.word.running` "Running"; `next.word.stopped` "Stopped"; `next.word.failed` "Failed"; `next.word.interrupted` "Interrupted".

Sentences `next.state.<CODE>`:
- `NO_REVIEW` "No review is open."
- `DRAFT_STARTED` "Your draft has no topic yet."
- `DRAFT_INCOMPLETE` "Your draft still needs {fields}."
- `DRAFT_READY` "Your draft is complete. Create the workspace when you are ready."
- `DRAFT_CREATED` "The workspace {title} exists. Open it to continue."
- `NO_PROTOCOL` "This review has no protocol yet."
- `PROTOCOL_INVALID` "The protocol file cannot be read, so nothing can be searched."
- `PROTOCOL_PLACEHOLDER` "This protocol is a placeholder. Write your own with New review."
- `SETUP_NEEDED` "A search needs {what}."
- `READY_TO_SEARCH` "Your protocol is ready. Run the search."
- `STAGED_EXPORTS` "{n} database exports are staged. Accept them to start screening."
- `SEARCH_CHANGED` "You changed the search after run {run}. Search again before you accept."
- `CORPUS_READY` "Your corpus is ready: {works} works from {records} records. Accept it to start screening."
- `NOT_PREPARED` "The corpus is accepted. Prepare the screening batches."
- `PROTOCOL_CHANGED_AFTER_BATCHES` "The protocol changed after screening started, so earlier decisions count nowhere."
- `CONFLICTS` "{n} decisions conflict. Resolve them before you go on."
- `SCREENING` "{needs_you} of {total} records still need you."
- `READY_TO_PUBLISH` "Every record is decided. Check the agreement, then publish."
- `PUBLISHED_STALE` "{n} studies changed since you published."
- `PUBLISHED` "Screening is published. You can chase the citations of your included studies."
- `CHASE_READY_TO_SEND` "The chase found {new} new works. Send them to screening as round {round}."
- `CHASE_NOTHING_NEW` "The chase found nothing new."
- `ROUND_ACCEPTED` "Round {round} is with screening. Prepare its batches."
- `DONE` "Nothing is waiting for you. Export and methods are on Publish."
- `round` suffix `next.inRound` " in round {round}"; `SETUP_NEEDED.what.email` "a contact email"; `.key` "an OpenAlex key"; `.both` "a contact email and an OpenAlex key".

Waiting `next.waiting.<stage>` and reasons:
- `searching` "The search is running. {answered} of {databases} databases have answered."
- `deduplicating` "The search found {records} records. Removing duplicates."
- `adding_abstracts` "{works} works remain after duplicates. Adding missing abstracts."
- `verifying` "Checking {works} works against the databases. The hand-off opens when this ends."
- `preparing` "Preparing the screening batches."
- `chasing` "The citation chase is running."
- `accepting_chase` "Wait for the running job to end, then send these works."
- `next.stopped.searching` "You stopped the search. What was fetched is kept, but no corpus was made."
- `next.stopped.stage` "You stopped the search while {stage}. The corpus was not made."
- `next.failed.searching` "No database answered, so nothing was kept."
- `next.failed.stage` "The search finished, but preparing the corpus failed at {stage}. {message}"
- `next.interrupted` "The search finished, but the corpus was not prepared. The console may have been closed while it ran."
- `next.reason.STOPPED_BY_RESEARCHER` "Stopped by you."; `next.reason.INTERRUPTED` "The search ended before the corpus was written. The cause is not recorded."; the registered codes use `discovery.states.<CODE>.*` (07).
- stage names for `{stage}`: `next.stage.deduplicating` "removing duplicates", `next.stage.adding_abstracts` "adding abstracts", `next.stage.verifying` "checking the works".

Buttons `next.action.<key>`: `chooseReview` "Choose or start a review"; `goToStep` "Go to {step}"; `goToReview` "Go to Review"; `goToDone` "Go to the finished workspace"; `goToInception` "Go to inception"; `seeWhatToSet` "See what to set"; `goToHarvest` "Go to Harvest"; `reviewExports` "Review and accept the exports"; `reviewCorpus` "Review and accept the corpus"; `followSearch` "Follow the search"; `searchAgain` "Search again"; `goToScreening` "Go to screening"; `openInception` "Open inception"; `goToScreeningHome` "Go to screening home"; `openTriage` "Open triage"; `goToPublish` "Go to Publish"; `publishAgain` "Publish again"; `goToChase` "Go to Chase"; `reviewChase` "Review and send the works"; `followPreparation` "Follow the preparation"; `followChase` "Follow the chase"; `finishPreparing` "Finish preparing this corpus" (the words of the M3i Harvest button).

## Accessibility
- The bar is a labelled region (`next.region`). Waiting and result changes are announced through one `aria-live="polite"` `role="status"` node that holds the sentence; it announces only when the state code or `waiting.stage` changes (not on every poll) and is debounced by 2 s, so a fast stage sequence is read once. `aria-busy` while loading. The offline state is `role="status"`, not an alert (it is not a refusal of an action).
- Status never rests on colour: the state word (Running, Stopped, Failed, Interrupted) is text with an icon; `blocked` is text colour only (tokens.json usage). Contrast pairs from tokens: `ink` on `leaf`; the secondary button `brand` on `leaf`; role words `brand`, `unclear`, `blocked` on `leaf`. Focus ring `focus` token, never clipped; the bar is not sticky so it never obscures a focused control.
- The button is a link with a visible text label naming its destination ("Go to Harvest"), never an icon alone; its label changes with the answer. Targets 44 px.
- RTL (ar): the row mirrors (sentence on the right, button on the left); the arrow in the button mirrors; ids (`run_003`, `djob_…`), counts, fingerprints and times are `dir="ltr"` with Latin digits inside `bdi`. Counts in a sentence stay the engine's numbers (no localised plural logic in the browser beyond the message format).
- Light and dark tokens.

## Acceptance tests
Vitest `apps/research-ui/tests/next-step-bar.test.tsx`:
- every `state` code in table 1 and every `waiting.stage` in table 2 maps to a sentence key in en, fr and ar, and every `action.key` to a button key (table-driven; `next-step.i18n`, the N9 guard);
- the bar prints `params` as sent and computes nothing: no count, no state, no fingerprint is derived in the component (a fixture with `works` 1050 prints 1,050; a fixture with different `works` and `records` prints both unmodified);
- the harvest-finished, verification-pending answer (`CORPUS_PENDING`, `waiting` `verifying`) shows "Checking 1,050 works against the databases..." and a "Follow the search" link to Harvest with the `job` id, and no "Accept" label anywhere;
- the same answer with `waiting.kind` `interrupted` and `can_finish` shows the interrupted sentence and "Finish preparing this corpus" with "Search again" in `also`, and the reason sits under Details;
- `SEARCH_UNFINISHED` with `waiting` A, G(a) and H shows each sentence and its button;
- when `action.to.screen` equals the current screen the bar renders the naming sentence (`next.here`) and no link; when the screen is a gate it renders the naming form;
- the button is secondary (no brand fill class) and the page keeps exactly one brand button;
- loading shows the skeleton with `aria-busy` and no sentence; `ENGINE_UNREACHABLE` shows the last sentence with "as of" and no button; `TOKEN_SCOPE_REFUSED`, `HOST_REFUSED` and a draft refusal render nothing;
- a refresh happens on `nexus:review-changed`, on route change, and by a 5 s poll only while `waiting.kind` is `running`; never two requests at once; no `If-None-Match` is sent; an answer with an older `computed_at` than the one shown is discarded;
- the live region announces on a state change and not on an unchanged poll; focus is not moved by a refresh;
- the bar is absent on `/workspaces`, on the triage route and with a phone-scoped token; present on inception, discovery and screening routes (`isOneScreenRoute` untouched);
- RTL (ar): ids and counts `dir="ltr"`, arrow mirrored; no literal `aria-label`.

Python `tests/console/test_next_step_api.py` (the builder from a folder; each case from the table):
- `test_harvest_finished_verification_running_is_corpus_pending_waiting`: a workspace whose newest run has `raw_published` true, `deduped.json` with 1,050 works, a marker at stage `verification` that has not ended, no staged export, and a live `prepare` job for that run answers `state` `CORPUS_PENDING`, `waiting.kind` `running`, `waiting.stage` `verifying`, `params.works` 1050, `params.records` 1074; the same marker at `hydration` answers `adding_abstracts`, at `deduplication` `deduplicating`. The stage comes from `preparation`, never from job events. **This fails before** because no next-step route exists; the folder itself, read through `GET /discovery/handoff`, shows the M3i "Not ready" state with `preparation.state` `running`;
- `test_marker_without_job_is_interrupted` (the same folder with no job: variant J, and "Finish preparing this corpus" when `can_finish`); `test_failed_preparation_keeps_its_stage_and_message`; `test_stopped_search_is_search_unfinished`; `test_failed_search_is_search_unfinished`; `test_first_harvest_searching_is_search_unfinished`; `test_staged_exports_win_over_an_unfinished_harvest` (`STAGED_EXPORTS`); `test_stale_verified_from_an_earlier_run_is_not_ready` (run 1's `verified.json` with a published run 2 whose marker has not ended answers `CORPUS_PENDING`, not `CORPUS_READY`);
- one test per row of table 1 in order, including the first-match rule; `test_draft_ready_follows_the_checks_ready_flag` (all fields present and one undecided wizard criterion answers `DRAFT_INCOMPLETE`, not `DRAFT_READY`); `test_unreadable_journal_goes_to_unknown`; `test_phone_token_refused`; `test_no_workspace_answers_no_review` (through the HTTP app with no workspace open: `200` and `NO_REVIEW`, not `409 WORKSPACE_NOT_VALID`); `test_no_etag_header`;
- `test_stopped_preparation_offers_finish`, `test_failed_preparation_after_restart_offers_finish` and `test_cannot_finish_offers_search_again_only` (from M3i markers the fixtures write); `test_protocol_origin_written_by_both_genesis_paths_and_on_replace` (web genesis and CLI `emit_workspace` write `inception` or `import`; a replacement of a `placeholder` workspace writes `inception`; `nexus-scholar init`'s placeholder scaffold writes `placeholder`); `tests/console/test_console_refusals.py` is unchanged (no new refusal code).
Playwright `tests-browser/next-step.spec.ts` (stateful fake of the engine):
- `harvest finished, verification running`: after a harvest the Hand-off shows the bar "Checking 1,050 works against the databases..." above the page's "Not ready" state (M3i); when the fake ends the marker and writes `verified.json` the bar becomes "Your corpus is ready..." with "Review and accept the corpus", and on the Hand-off it names the screen's own button and shows no link;
- interrupted case (job gone): "Finish preparing this corpus" leads to Harvest; a run that cannot be finished offers "Search again" only;
- full path: no protocol, ready to search, searching, corpus ready, accepted, prepare running, screening, ready to publish, published, chase;
- RTL (ar); axe in light and dark; no horizontal overflow at 375 and 1440 px; the bar is not on `/workspaces` or triage.

## Dependencies (amendments to finished specs, each made by the work that builds it)
- `docs/ux/phase1-discovery/final/08-handoff.md`: M3i (merged) added the "Not ready" state ("The corpus is not ready to hand off yet", a link to Harvest) and narrowed "Empty". M10b adds "The next-step bar (M10b)" there: the bar above both states, built in C1. The Hand-off stays the one place to accept.
- `docs/ux/phase2-screening/final/11-import-corpus.md` (the Import step): the Hand-off is the one place where a corpus is accepted, for harvests and for staged exports (decided 2026-11-15). The Import step keeps staging and its preview; its accept button is replaced by a link "Review and accept on the Hand-off", and a disabled state names the reason with the bar's sentence. Amended on 2026-11-18, as the first step of the M10b build.
- `docs/ux/phase1-discovery/final/03-harvest.md` is not edited here; the Harvest screen's own job panel is the destination of "Follow the search" and already reads `?job=`.

## Open questions
None.

Closed by the researcher on 2026-11-15 (record: `docs/roadmap/milestones/M10b-proposals-checks.md`, R5 and R6 and "Adopted from the writers' recommendations"):
1. Resume instead of searching again: yes, as "Finish preparing this corpus", built in M3i-harvest-robustness (merged before the M10b build). Variants G(b), I and J offer it when `can_finish`, and "Search again" otherwise.
2. Stop during preparation: yes, checked between stages and recorded, in the same fix.
3. A placeholder protocol is marked by `protocol_origin` in `project.json` (M10b).
4. The bar also serves the inception screens, through the draft route with the same response shape; `missing[]` is computed by the existing `_require` rules without a genesis attempt (M10b).
5. Staged exports are accepted on the Hand-off, as harvests are; the Import step links to it.
