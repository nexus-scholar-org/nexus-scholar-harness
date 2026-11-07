# Screening API contract (M1a ⇄ M1b, M2)

**Status:** ACCEPTED 2026-11-04 (open questions decided in §9; the methods wording is deferred to M5-slim). Proposed refusal codes are added to the registry in M1a. It defines the boundary between the engine (M1a) and the UI (M1b desktop, M2 phone), so the two can be built in parallel against shared fixtures.
**Related:**
- [`../roadmap/production-plan.md`](../roadmap/production-plan.md) §2, §4, §6;
- [`agent-system.md`](agent-system.md) §3–§4;
- [`refusals.md`](refusals.md);
- the screen specs `docs/ux/phase2-screening/final/0N-*.md`;
- the canvases (PR #182).

## 1. Scope and rules

- **Base path:** all routes are under `/api/v1/screening`, served by the FastAPI console (`src/scholar_harness/console/api/screening.py`).
- **Single writer:** the engine is the only writer of workspace files and `audit/journal.jsonl`. The UI never computes identifiers, fingerprints, outcomes or acceptance results (`apps/research-ui/AGENTS.md`).
- **Human decisions are events.** They are append-only, idempotent, and never edited or deleted. A change of mind is a new event that supersedes the old one.
- **Agent proposals are separate records** in the proposal store (agent-system §2). They are hidden from the UI until the researcher has decided the study (`PROPOSAL_HIDDEN`).
- **Existing routes stay** (`screening.py:102–1581`). The batch draft writer `POST /batch/{n}/decisions` (`:102`) is kept for compatibility. Once event intake lands it is marked deprecated, and the UI stops using it in M1b.

## 2. Identity

| Name | Form | Source | Stable across |
| :-- | :-- | :-- | :-- |
| `study_id` | `STU-…` | corpus snapshot (`scholar_search/identity.py:320-331`) | re-runs and order (content-derived) |
| `event_id` | UUIDv7 string | **minted by the client** at the moment of the tap or keypress | replays (the idempotency key) |
| `decision_id` | contract id | collector's existing recipe (`screening/collector.py:929-942`) | replays, see below |
| `proposal_id` | `sha256(task_version, input_sha256, protocol_fingerprint, model)` | engine | re-reads |

**`decision_id` keeps its current recipe.** That keeps the change out of Contract v1. The collector already derives it from `batch_id`, `study_id`, `screener_id`, `method`, `decision`, `reason`, `decided_at` and `parent_decision_ids`. The projection (§3.3) feeds that recipe the **winning event's own, immutable fields**: `decided_at` is the event's client timestamp, never the time of the flush or projection. A replay of the same events therefore yields the same `decision_id`s and the same bytes, and an approval stays valid. A superseding event is a new decision with a new id, and it lists the old id in `parent_decision_ids`. M1a confirms with `generate_contract_baseline.py --check` that this needs no baseline change. If it does, stop: that is `BLOCKED_BASELINE_DRIFT`, and it needs an architecture decision.

## 3. Decision events

### 3.1 Shape

```json
{
  "event_id": "0193f4a2-7c1e-7b2a-9e55-2f1d3c4b5a69",
  "study_id": "STU-6f1c…",
  "screener_id": "researcher:<local-attestation-id>",
  "method": "HUMAN",
  "outcome": "INCLUDE | EXCLUDE | MAYBE",
  "reason_code": "EXC-01 | FAILS-INC-03 | null",
  "note": "optional free text",
  "criteria": [{"id": "INC-01", "answer": "yes | no | not_reported"}],
  "decided_at": "2026-11-03T14:22:07.123Z",
  "device": "desktop | phone",
  "supersedes": "<event_id> | null",
  "proposal_shown": {"proposal_id": "…", "revealed_after_decision": true},
  "changed_after_reveal": false,
  "binding": {"protocol_fingerprint": "sha256:…", "batch_id": "…", "batch_sha256": "sha256:…"}
}
```

- `outcome: MAYBE` is shown as **"Unclear → full text"** (`decisions.md`, 2026-11-03). It exists in `ScreeningDecisionValue` (`contracts/models.py:93`).
- `reason_code` is required when `outcome` is `EXCLUDE`, and must be one of the protocol's exclusion codes or `FAILS-<inclusion id>`.
- `criteria` is optional on a phone swipe and required for a desktop checklist decision.
- `proposal_shown` is `null` when the researcher decided before any proposal was revealed. With blinding on (the default) it is always `null` at decision time; the reveal is recorded afterwards as a separate `REVEAL` audit row, not as a decision.
- `changed_after_reveal` is set by the engine, not the client, when a superseding event follows a reveal of the agent proposal for that study. It lets the methods paragraph report how often the researcher changed their mind after seeing the agent.
  - **A reveal** (M1b-0) is the first time `GET /records/{id}/proposal` returns a proposal to a screener. The engine appends it to `literature/screening/reveals.jsonl` under the events lock, bound to the study's current batch and protocol, and journals `SCREENING_PROPOSAL_REVEALED` with the proposal id and never its outcome. If the lock cannot be taken the read is refused (`ATOMIC_COMMIT_FAILED`, 503) rather than shown unrecorded.
  - **The stamp** is `true` on a superseding event from the same screener received after a current-generation reveal of that study's proposal, whether or not the outcome changes; the event chain shows what changed. A reveal from an earlier protocol or batch does not count.
  - Events stored before M1b-0 carry `false`, which for them means "not tracked".
- **Skip** is client-side deferral. It writes no event.
- `screener_id` is an unauthenticated local attestation (CON-02 relabel). The engine stamps `received_at` and the `device` token scope on intake; the client cannot set them.

### 3.2 Storage

- Events are appended to `literature/screening/events/<screener_id>.jsonl`, one line per accepted event, with the engine-stamped `received_at` and `token_scope`.
- Each accepted batch of events appends one `SCREENING_DECISIONS_RECEIVED` row to `audit/journal.jsonl`, carrying counts, device and the first and last `event_id`.

### 3.3 Projection

The engine regenerates `literature/screening/batch_NNN_decisions.json` (the existing contract format the collector and acceptance consume) deterministically from the event log:
- the **winning event** for (`study_id`, `screener_id`) is the head of its supersession chain;
- events are sorted by (`study_id`, `event_id`);
- a study with a **conflict** (§3.4) is left out of the projection, so the existing coverage gate refuses collect visibly (`BATCH_INCOMPLETE`) instead of silently picking one.

Projection is a pure function of the event log. Running it twice on the same log yields byte-identical files (required test, §8).

### 3.4 Intake rules (`POST /decisions/events`)

Each event is judged on its own and gets one result:

| Result | When |
| :-- | :-- |
| `accepted` | new `event_id`; binding is current; schema valid |
| `duplicate` | `event_id` already stored with identical content (the replay of an offline flush) |
| `conflict` | a second non-superseding event for the same (`study_id`, `screener_id`) whose outcome differs; both are stored and the study moves to `GET /decisions/conflicts` |
| `refused` | a typed refusal (§7): stale binding, unknown study, bad reason code, `event_id` reused with different content (`IDEMPOTENCY_CONFLICT`), wrong token scope |

A repeat of the same outcome from a second device is not a conflict. It is stored and treated as a confirmation. Intake is atomic per request: the events file and its journal row are written together or not at all (`ATOMIC_COMMIT_FAILED`).

## 4. Endpoints

**Scopes:**
- `desktop` is the per-launch token on loopback (INC-01).
- `phone` is the short-lived token from `POST /lan/pair`, accepted only on the restricted LAN sub-app (plan §4).

M = milestone; ✓ = route exists today.

| Method and path | Purpose | Request → Response | Scope | M |
| :-- | :-- | :-- | :-- | :-- |
| `GET /summary` | home progress | → `{total, decided, by_outcome, agent_proposed, needs_you, conflicts, queued_on_phones?, lanes:{agent, you, second_screener:"PARKED"}}` | desktop, phone | M1a |
| `GET /queue?view=&cursor=&limit=` | cross-batch queue in server order | `view ∈ {needs_you, proposal_ready, no_proposal, title_only, decided}`, plus `order=agent_uncertainty` after a run: it orders by how unsure the agent was, without revealing its call, and is disclosed in the methods paragraph → `{items:[{study_id, title, batch_id, has_proposal, decided, flags}], next_cursor}`. `has_proposal` is a boolean only, and agent outcomes are never returned before a decision. Views that reveal agent calls (`agent_disagrees`) need `decided=true`. | desktop, phone | M1a |
| `GET /records/{study_id}` | record detail | → `{study_id, title, authors, year, venue, doi, abstract, batch_index (M6-beta), highlights:[{start,end,criterion_id}], criteria:[{id, text, kind}], binding, my_decision?, history:[event…]}` | desktop, phone | M1a |
| `GET /records/{study_id}/proposal` | agent draft | → `{proposal_id, task_version, model, prompt_sha256, criteria:[{id, answer, evidence:{start,end,text}}], derived_outcome, reason_code, validators:[…], cannot_decide}`; **`PROPOSAL_HIDDEN`** until a decision exists and blinding is on | desktop, phone | M1a |
| `POST /decisions/events` | submit decisions | `{events:[…]}` (≤ 200) → `{results:[{event_id, result, decision_id?, refusal?}]}` | desktop, phone | M1a |
| `GET /decisions/conflicts` | conflicts to resolve | → `{items:[{study_id, events:[…]}]}` | desktop, phone | M1a |
| `POST /decisions/conflicts/{study_id}/resolve` | keep one | `{keep_event_id}` → writes a superseding event that names both | desktop, phone | M1a |
| `GET /settings`, `PUT /settings` | screening settings | `{blinding: "reveal_after_decision"\|"show", mode: "human_sees_every_record"\|"ai_agreed_exclusion", sample_audit_size?, queue_order: "seeded"\|"agent_uncertainty", advance_on_decide: "show_draft_then_next"\|"next_at_once"}` (`queue_order` M5-slim: `GET /queue` uses it, and an `order` parameter that differs is refused `INVALID_OUTPUT`); turning on AI-agreed exclusion needs a confirmation body and is journaled | desktop | M1a |
| `GET /approver`, `PUT /approver` | the name approvals are recorded under | `GET` → `{name: string\|null, set_at, basis: "typed-name"}`. `PUT {name}` (whitespace collapsed, 1–120 printable characters) writes `literature/screening/operator_context.json`, the operator context the approval reads, and journals `SCREENING_APPROVER_SET` with the name before and after; the same name again writes nothing. Refuses `INVALID_OUTPUT` (empty, too long, control characters) and `APPROVAL_NOT_OPERATOR` (a name the engine never trusts as a person, e.g. "unknown"). A typed name, not a verified sign-in (CON-02/03); approvals already made keep the name they were made under (decision 2026-11-06) | desktop | M5-slim |
| `GET /corpus` | the corpus import (spec 11) | → `{shape:"screening.corpus-v1", state: "EMPTY"\|"STAGED"\|"ACCEPTED", sources:[{id, label, file_name, records, searched_on, query}], databases:[{label, records, files, searched_on:[…], search_details_missing}], preview:{identified, duplicates, unique_studies}, accepted:{artifact_id, accepted_at, records, studies, duplicates}\|null, from_discovery, limits:{max_source_bytes, label_max_length}}`. The preview uses the snapshot's own deduplicator and writes nothing | desktop | M5b |
| `POST /corpus/sources` | stage one database's RIS export | `{label, file_name, content_base64, searched_on?, query?}` (extra fields refused; a label may repeat for a database exported in parts, and its files are summed per database) → 201 + the `GET /corpus` body; the file is kept under `literature/raw/ris/`; journaled `CORPUS_SOURCE_STAGED`. Refuses `SOURCE_LABEL_INVALID`, `SOURCE_DATE_INVALID` (not a real `YYYY-MM-DD` date), `SOURCE_NOT_RIS` (422; also content that is not base64), `SOURCE_TOO_LARGE` (413, 50 MB), `SOURCE_DUPLICATE_FILE`, `VERIFIED_EXISTS`, `CORPUS_ALREADY_ACCEPTED` (409) | desktop | M5b |
| `POST /corpus/sources/{id}/remove` | drop a staged export file | → the `GET /corpus` body; journaled `CORPUS_SOURCE_REMOVED`; `SOURCE_NOT_FOUND` (404), `CORPUS_ALREADY_ACCEPTED` (409) | desktop | M5b |
| `POST /corpus/accept` | UI for `nexus-scholar accept-corpus` | → the `GET /corpus` body, `state: "ACCEPTED"`; writes `verified.json` and `literature/raw/provenance_manifest.json`, then the acceptance gate publishes the snapshot (journaled). `NOTHING_STAGED` (also when every imported file was removed), `CORPUS_ALREADY_ACCEPTED`, `PROTOCOL_INVALID`, and `ACCEPT_CORPUS_REFUSED` when the acceptance gate refuses the snapshot (409, its issues in the message) | desktop | M5b |
| `POST /prepare` | allowlisted prepare job | `{batch_size}` (5 to 100, default 20; passed to the job since M6-beta) → `{job_id}`; refuses `SNAPSHOT_NOT_ACCEPTED`, `BATCH_SIZE_INVALID` | desktop | M1a |
| `POST /proposals/runs` | estimate, or start, an agent run | `{driver:"api", provider: "anthropic"\|"openai_compatible"\|"gemini", model, effort, base_url? (OpenAI-compatible), scope:{view: "needs_you"\|"no_proposal" \| study_ids}, consent?:{provider, accepted_at}, cost_ceiling_usd?, dry_run? (the first 20 records), estimate_only? (writes nothing)}` → `{run_id (null for an estimate), estimate:{records, tokens:{input_tokens, cache_read_tokens, cache_write_tokens, output_tokens}, assumptions, cost_usd, batch, prices_as_of, priced}}`. Refuses `CONSENT_REQUIRED`, `PROVIDER_KEY_MISSING`, `DRIVER_UNAVAILABLE`, `CEILING_NOT_PRICED`, `COST_CEILING_REACHED` (the estimate is above the ceiling), `RUN_ALREADY_ACTIVE`, `UNKNOWN_STUDY`, `INVALID_OUTPUT` (bad scope or consent) | desktop | M1b |
| `POST /proposals/calibrations` | check the agent on your labels | `{study_ids, provider, model, effort, base_url?, cost_ceiling_usd?}` → `{run_id}`; the same refusals as a run; result `{include_recall, ci_low, missed_includes:[…]}`. **Advisory:** a missed include shows a warning and never blocks a run, because the researcher decides whether to trust it | desktop | M1b |
| `GET /proposals/setup` | what the run screen needs before a run | → `{task:{task_version, prompt_sha256, model, effort}, providers:[{provider, key: "keychain"\|"environment"\|"none", consent}], data_flow, active_run, latest_run}`; names where a key is stored, never the key (M1b-2) | desktop | M1b |
| `GET /proposals/runs/{run_id}` | run status | → `{run_id, kind, state: "running"\|"completed"\|"stopped"\|"cancelled"\|"failed", code, provider, model, effort, records, done, failed, refused, truncated, invalid, check_failures, cost_so_far (null when the provider/model is not priced), cost_ceiling_usd, started_at, finished_at, calibration?}`. A Batch run checks the ceiling between chunks of 200 records | desktop | M1b |
| `POST /proposals/runs/{run_id}/cancel` | cancel | → `{run_id, state:"cancelled"}`; a run left `running` by an engine that stopped is finished as cancelled and frees the workspace lock | desktop | M1b |
| `GET /prisma/preview` | PRISMA screening box | → `{identified, duplicates_removed, screened, excluded:{total, by_reason}, unclear_to_full_text, included, not_yet_decided, checks:[{name, ok, detail}]}`; `checks` covers HUMAN provenance on every decision, no open conflicts, every batch bound to the current protocol, the sample audit if the opt-in is on, and agreement attached | desktop, phone | M1a |
| `GET /agreement` | agreement with the agent | → `{decided_with_proposal, decided_after_seeing_the_draft, agreement_pct, table_2x2, splits_by_criterion:[{criterion_id, n}], unclear_either_side, kappa: null, kappa_note: "needs a second human screener"}`; counts only decisions made before the reveal | desktop | M1b |
| `GET /export?format=ris\|csv&set=included,unclear,excluded` | export the published decisions | read-only, from the **published** generation only (`included.json`, `excluded.json`; unclear = `screening.decision == "MAYBE"` in `included.json`; reason codes from the generation's decision files). Default `set` is `included,unclear` for RIS and all three for CSV. → file bytes with `Content-Disposition: attachment; filename="{slug}-screening-{generation_id}-{set}.{ris\|csv}"`. RIS: `TY  - JOUR` blocks with `TI AU PY T2 DO UR AB ID N1 ER`, UTF-8 without BOM, no empty field. CSV: `study_id, decision, reason_code, title, authors, year, venue, doi, url, abstract, generation_id`, UTF-8 with BOM, CRLF. Refuses `EXPORT_NOT_PUBLISHED`, `GENERATION_STALE` (a decision changed after publication, or the generation is otherwise stale), `GENERATION_SUPERSEDED`, `EXPORT_SOURCE_MISMATCH`, `EXPORT_FORMAT_INVALID`. No journal row (spec 10) | desktop | M5-slim |
| `GET /methods` | methods paragraph of the published screening | → `{generation_id, generation_fingerprint, published_at, language: "en", paragraph, figures, sources:[{name, path, digest?}], caveats, not_stated}`; a fixed English template of facts and counts from `prisma_report.json`, the `SCREENING_SETTINGS_CHANGED` history, proposals, agent runs, consent, decision events and reveals; every number in `paragraph` is a value in `figures`. Same currentness refusals as `/export`, plus `METHODS_SOURCE_MISSING`. Writes no file and no journal row (spec 10) | desktop | M5-slim |
| `POST /lan/session/begin` | show the phone QR | → `{qr_payload, one_time_token_expires_at}`; desktop only; separate from approval pairing | desktop | M2 |
| `POST /lan/session/stop` | stop phone access | revokes every phone token | desktop | M2 |
| `POST /actions/pairing/begin` | start approval pairing for one batch | `{batch}` → `{batch_index, snapshot_fingerprint, code_expires_at, attempt_cap, code_shown_on: "terminal"}`. The code is printed only in the terminal running the console, never returned over HTTP (decision 2026-11-04) | desktop | M1a |
| `GET /actions/pairing/status` ✓ | pairing state | `screening.py:1407` | desktop, phone (read-only) | — |
| `POST /actions/pairing/redeem` ✓ | approve | `screening.py:1429` (fix the proxy allowlist path, plan §1.2). **Desktop only in stage 1:** the phone shows the PRISMA summary and "Approve on your desktop" (changed from the MobileApprove canvas) | desktop | M0 |
| `POST /actions/defer` ✓, `POST /actions/publish` ✓ | defer or publish | `screening.py:1512, :1581` | desktop | — |
| `POST /lan/pair` | phone pairing | `{one_time_token}` → sets the phone session cookie. The one-time token lasts 2 minutes and works once. The phone session ends at the first of: `POST /lan/session/stop`, the desktop `nexus-scholar ui` process stopping, or 12 hours. Expired or reused tokens are refused | LAN sub-app only | M2 |
| `GET /ui/batches`, `/ui/batch/{n}/rows`, `/review`, `/criterion-refs`, `/ui/audit-feed` ✓ | existing reads | kept; the new screens use `/queue` and `/records` | desktop | — |

**Errors.** Every route answers a refusal as HTTP 4xx with `{"detail": {"code": "<CODE>", "message": "…", "retryable": false, "details": {…}}}`, the shape the existing actions already use (for example `ACTION_ORIGIN_REFUSED` in `tests/console/test_screening_actions.py`). **Pagination** is cursor-based and opaque to the client.

## 5. Proposals as the UI sees them

The UI reads proposals only through `GET /records/{study_id}/proposal`. The fields are a subset of the stored proposal (agent-system §4). `derived_outcome` comes from the plain-code rule table, never from the model. `validators` lists each check and its result, so the UI can show "quote not found in abstract" or "refused by provider" as the reason a proposal routed to Unclear. The UI styles every proposal as a draft (BRAND_BOOK).

## 6. Phone and offline

- The phone keeps a queue of unsent events in IndexedDB and replays them oldest first through `POST /decisions/events`. On `duplicate` it drops the local copy. On `conflict` it shows the conflict card (canvas MobileOffline). On `refused` it keeps the event and shows the code.
- `event_id` is minted on the phone, so a replay can never create a second decision.
- The phone never calls jobs, pipelines, settings, `/prepare`, `/proposals/runs` or publish. Those routes are not mounted on the LAN sub-app.

## 7. Refusal codes

**Already exist** (`refusals.md`, `contracts/models.py` ErrorCode, `screening/integrity.py:20-28`, `authority/binding.py:42-43`, `authority/pairing.py:65`): `COVERAGE_INCOMPLETE`, `UNRESOLVED_FINALIZE_REFUSED`, `APPROVAL_NOT_OPERATOR`, `RATE_LIMITED`, and also:
- `STALE_BINDING`, `APPROVAL_MISSING`, `BATCH_INCOMPLETE`;
- `IDEMPOTENCY_CONFLICT`, `ATOMIC_COMMIT_FAILED`, `INVALID_OUTPUT`;
- `IDENTITY_AMBIGUOUS`, `QUOTE_NOT_IN_SOURCE`, `PROVIDER_TRANSIENT`;
- `ACTION_ORIGIN_REFUSED`, `PAIRING_CODE_INVALID` (console actions).

**Proposed here** (to confirm in M1a; they go in the console refusal set, not Contract v1):

| Code | Route | Meaning |
| :-- | :-- | :-- |
| `PROPOSAL_HIDDEN` | `/records/{id}/proposal` | blinding on and no decision yet |
| `SNAPSHOT_NOT_ACCEPTED` | `/prepare` | no accepted corpus snapshot; run `accept-corpus` |
| `UNKNOWN_STUDY` | events, records | `study_id` not in the bound corpus |
| `REASON_CODE_INVALID` | events | EXCLUDE without a valid protocol reason code |
| `REASON_CODE_INCONSISTENT` | events | EXCLUDE whose reason contradicts the event's own answer: `FAILS-INC-n` with INC-n answered yes, or `EXC-n` with EXC-n answered no (M6-beta) |
| `TOKEN_SCOPE_REFUSED` | any | phone token used on a desktop-only route, or an expired token |
| `CONSENT_REQUIRED` | `/proposals/runs` | no recorded consent for this provider |
| `RUN_ALREADY_ACTIVE` | `/proposals/runs`, `/proposals/calibrations` | one agent run per workspace at a time |
| `COST_CEILING_REACHED` | `/proposals/runs`, `/proposals/calibrations`, run status | at start: the estimate is above the ceiling; during a run: it stopped at its per-run hard cost ceiling, and done proposals are kept |
| `PROVIDER_KEY_MISSING` | `/proposals/runs`, `/proposals/calibrations` | no key for the provider in the OS keychain or the environment; set it with `nexus-scholar keys set <provider>` on this computer (M1b-2) |
| `UNKNOWN_RUN` | `/proposals/runs/{id}` | no agent run with that id in this workspace (M1b-2) |
| `DRIVER_UNAVAILABLE` | `/proposals/runs`, `/proposals/calibrations` | the provider's driver cannot be built: its SDK is not installed (the `ai` extra, 409) or a required setting such as the OpenAI-compatible base URL is missing (422); refused before the workspace lock is taken (M1b-2) |
| `CEILING_NOT_PRICED` | `/proposals/runs`, `/proposals/calibrations` | a cost ceiling on a provider/model the dated price table does not price, so its cost cannot be measured; run it without a ceiling (M1b-2) |
| `WORKSPACE_TITLE_INVALID` | `/workspaces` (create) | the title yields an empty folder name |
| `WORKSPACE_EXISTS` | `/workspaces` (create) | the target folder already exists; never suffixed |
| `WORKSPACE_PATH_REFUSED` | `/workspaces`, `/workspaces/open` | the folder is outside the workspaces root |
| `WORKSPACE_ROOT_UNAVAILABLE` | `/workspaces` | the root is missing and cannot be created, unreadable, or not writable |
| `WORKSPACE_NOT_VALID` | `/workspaces/open` | the folder is not a workspace, or no longer exists |
| `WORKSPACE_BUSY` | `/workspaces/open` | an agent run is active or an approval is open; the restart would end it |
| `RESTART_UNSUPPORTED` | `/workspaces/open` | the server was not started by `nexus-scholar ui` (M5-slim; all seven in `workspaces-api.md` §5) |
| `PROVENANCE_MISSING` | events intake, collect | a decision lacks screener, method or `decided_at`; refused, never filled in (CON-11) |
| `PROJECTION_STALE` | publish, PRISMA preview check | a `batch_NNN_decisions.json` differs from the decision events (its rewrite failed); publish refuses until a retry re-projects it (M1b-0) |
| `EXPORT_NOT_PUBLISHED` | `/export`, `/methods` | HTTP 409: no screening generation has been published (M5-slim, spec 10) |
| `EXPORT_FORMAT_INVALID` | `/export` | HTTP 422: `format` is not `ris` or `csv`, or `set` names an unknown set (M5-slim) |
| `EXPORT_SOURCE_MISMATCH` | `/export`, `/methods` | HTTP 409: a published file is missing or its digest differs from `generation.json`; nothing is exported (M5-slim) |
| `METHODS_SOURCE_MISSING` | `/methods` | HTTP 409: `prisma_report.json`, which the paragraph cannot omit, is missing or lacks a count; missing optional sources are listed under `caveats` (M5-slim) |
| `SOURCE_LABEL_INVALID` | `/corpus/sources` | HTTP 422: the database name is empty, too long or uses other characters (M5b) |
| `SOURCE_DATE_INVALID` | `/corpus/sources` | HTTP 422: date searched is not a real `YYYY-MM-DD` date (M5b) |
| `SOURCE_NOT_RIS` | `/corpus/sources` | HTTP 422: no RIS records in the file, or content that is not base64 (M5b) |
| `SOURCE_TOO_LARGE` | `/corpus/sources` | HTTP 413: the file is over 50 MB (M5b) |
| `SOURCE_DUPLICATE_FILE` | `/corpus/sources` | HTTP 409: the same file is already staged (M5b) |
| `SOURCE_NOT_FOUND` | `/corpus/sources/{id}/remove` | HTTP 404: no staged file has that id (M5b) |
| `VERIFIED_EXISTS` | `/corpus/sources` | HTTP 409: the corpus came from discovery; database exports would replace it (M5b) |
| `CORPUS_ALREADY_ACCEPTED` | `/corpus/*` writes | HTTP 409: the corpus is frozen (M5b) |
| `NOTHING_STAGED` | `/corpus/accept` | HTTP 409: no database file staged (M5b) |
| `PROTOCOL_INVALID` | `/corpus/accept` | HTTP 409: `protocol.json` does not validate (M5b) |
| `ACCEPT_CORPUS_REFUSED` | `/corpus/accept` | HTTP 409: the acceptance gate refused the snapshot; its issues in the message (M5b) |
| `BATCH_SIZE_INVALID` | `/prepare` | HTTP 422: batch size outside 5 to 100 (M6-beta) |
| `ENGINE_UNREACHABLE` | UI only | client-side state, never sent by the engine |

## 8. Shared fixtures and tests

**Fixtures:** `tests/fixtures/screening_api/*.json`, one request/response pair per route and state:
- hidden proposal; revealed proposal;
- duplicate, conflict and refused events;
- an empty queue; a stale binding.

The fixtures serve twice:
- Python contract tests (`tests/console/test_screening_api_contract.py`) check that the engine produces them.
- The UI loads the same files as its mock data (replacing the hand-written `lib/mock-screening.ts`), so M1b can be built before M1a merges.

A fixture change is a contract change and needs review by both tracks.

**Required tests, M1a:**
1. Replaying the same event set gives byte-identical `batch_NNN_decisions.json`, and approval stays valid.
2. Duplicate `event_id` → `duplicate`; same id with different content → `IDEMPOTENCY_CONFLICT`.
3. Two differing non-superseding events → `conflict`; the study is excluded from the projection; collect refuses `BATCH_INCOMPLETE`.
4. `GET /records/{id}/proposal` before a decision → `PROPOSAL_HIDDEN`.
5. EXCLUDE without a reason code → `REASON_CODE_INVALID`. An EXCLUDE whose reason contradicts the event's own `criteria` answer for that criterion → `REASON_CODE_INCONSISTENT` (M6-beta); an absent or `not_reported` answer never contradicts.
6. MAYBE passes finalize and is counted as "unclear to full text" in the PRISMA preview.
7. A phone token on `/prepare`, `/proposals/runs` or publish → `TOKEN_SCOPE_REFUSED`. In M2, those routes are absent on the LAN sub-app.
8. Every accepted batch of events writes exactly one journal row.

**The MCP driver** starts no run through this API. The researcher's Claude Code or Claude Desktop reads the queue and calls `submit_proposal` over MCP (agent-system §2). The proposals screen shows that path as an instruction ("run it from Claude"), not as a `driver` value. A decision on a study with an open conflict returns the per-event result `conflict`; there is no separate refusal code.

## 9. Decisions (researcher, 2026-11-04)

1. **Approval code:** a fresh one-time code is issued for each batch generation; the pairing code is never reused for approval. Approval is refused while any paired phone still holds queued events (`APPROVAL_MISSING`, detail `queued_events`).
2. **Event-file locking:** every append takes an exclusive OS file lock on `events/<screener_id>.jsonl` (Windows and Unix), so the CLI and the console can write at the same time without lost or interleaved lines (CON-19).
3. **`criteria` on a phone swipe:** an Exclude requires a `reason_code`; an Include or Unclear requires nothing more. The checklist stays optional on the phone and is captured on desktop.
4. **Batch size limit:** 200 events per request. The UI splits a larger offline backlog into chunks of 200 and retries each on its own; `event_id` makes replays harmless.
5. **Methods paragraph wording (PRISMA 2020 item 8):** deferred to M5-slim, with the default and minimum sample-audit size. Specs 02 and 07 keep a placeholder until then.
6. **Cost display:** a dated price table in the tasks folder, updated each release; the UI shows its "prices as of" date next to the estimate. No network call for prices.
