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
| `proposal_id` | `sha256(task_version, input_sha256, protocol_fingerprint, model)`; from criteria version 2 on, `criteria_version` is a fifth hashed field (M11b part A; under version 1 the recipe and every existing id are unchanged) | engine | re-reads |

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
  "binding": {"protocol_fingerprint": "sha256:…", "batch_id": "…", "batch_sha256": "sha256:…", "criteria_version": 1}
}
```

- `outcome: MAYBE` is shown as **"Unclear → full text"** (`decisions.md`, 2026-11-03). It exists in `ScreeningDecisionValue` (`contracts/models.py:93`).
- `reason_code` is required when `outcome` is `EXCLUDE`, and must be one of the protocol's exclusion codes or `FAILS-<inclusion id>`.
- `criteria` is optional on every device. When present it holds only the criteria the reviewer answered; an unanswered criterion is absent, never `not_reported`, and an empty list means no answers. (Amended 2026-11-09, M8-triage, `docs/decisions.md` "Triage: the checklist is a tool for the reason, not a gate for the decision": the desktop checklist is no longer required. The engine already read `criteria` as optional; no schema or engine change.) ~~Required for a desktop checklist decision.~~
- `proposal_shown` is `null` when the researcher decided before any proposal was revealed. With blinding on (the default) it is always `null` at decision time; the reveal is recorded afterwards as a separate `REVEAL` audit row, not as a decision.
- `changed_after_reveal` is set by the engine, not the client, when a superseding event follows a reveal of the agent proposal for that study. It lets the methods paragraph report how often the researcher changed their mind after seeing the agent.
  - **A reveal** (M1b-0) is the first time `GET /records/{id}/proposal` returns a proposal to a screener. The engine appends it to `literature/screening/reveals.jsonl` under the events lock, bound to the study's current batch and protocol, and journals `SCREENING_PROPOSAL_REVEALED` with the proposal id and never its outcome. If the lock cannot be taken the read is refused (`ATOMIC_COMMIT_FAILED`, 503) rather than shown unrecorded.
  - **The stamp** is `true` on a superseding event from the same screener received after a current-generation reveal of that study's proposal, whether or not the outcome changes; the event chain shows what changed. A reveal from an earlier protocol or batch does not count.
  - Events stored before M1b-0 carry `false`, which for them means "not tracked".
- **Skip** is client-side deferral. It writes no event.
- `binding.criteria_version` (M11b part A, decision item 5 of 2026-11-21) is echoed from `GET /records/{id}`: the criteria version the record was shown under. Intake refuses a new event whose bound version is not the one in force with `STALE_BINDING`, so a decision made under an earlier wording (an offline phone queue across a revision) is refused and its record stays in the queue; the client shows the refusal. A binding without it reads as version 1. It is checked at intake only: `is_current` (which events count) compares the protocol fingerprint, the batch id and the batch hash as before, and a stored event replays as a `duplicate`.
- `criteria_version` (M11b part A) is set by the engine, not the client: the version of the screening criteria in force when the event was received (1 is the signed protocol's list; each criteria amendment raises it, `audit/criteria_amendments.jsonl`). An event that sends it is refused `INVALID_OUTPUT`; an event stored before M11b has none and reads as version 1. It is a field of this harness event log only, never of the Contract v1 `ScreeningDecision`, and it is not projected (§3.3).
- `screener_id` is an unauthenticated local attestation (CON-02 relabel). The engine stamps `received_at` and the `device` token scope on intake; the client cannot set them. Since H-input-limits (F7) intake also refuses, as `INVALID_OUTPUT`, a `device` that is not the token's scope (a desktop token sends `desktop`, a phone token `phone`) and a `note` that is not text or is longer than 2 000 characters.

### 3.2 Storage

- Events are appended to `literature/screening/events/<screener_id>.jsonl`, one line per accepted event, with the engine-stamped `received_at` and `token_scope`.
- Each accepted batch of events appends one `SCREENING_DECISIONS_RECEIVED` row to `audit/journal.jsonl`, carrying counts, device and the first and last `event_id`.

### 3.3 Projection

The engine regenerates `literature/screening/batch_NNN_decisions.json` (the existing contract format the collector and acceptance consume) deterministically from the event log:
- the **winning event** for (`study_id`, `screener_id`) is the head of its supersession chain;
- events are sorted by (`study_id`, `event_id`);
- a study with a **conflict** (§3.4) is left out of the projection, so the existing coverage gate refuses collect visibly (`BATCH_INCOMPLETE`) instead of silently picking one;
- a study whose winning event a criteria amendment **shows again** (M11b part A: an Include or an Unclear made under an earlier criteria version, or an Exclude whose reason cites a criterion a later amendment reworded, split, merged or removed) is left out too, so approval and collect refuse the batch until the study is decided again. Recording an amendment rebuilds every projected batch file under the events lock.

Projection is a pure function of the event log and the criteria amendments (M11b part A). Running it twice on the same log yields byte-identical files (required test, §8).

### 3.4 Intake rules (`POST /decisions/events`)

Each event is judged on its own and gets one result:

| Result | When |
| :-- | :-- |
| `accepted` | new `event_id`; binding is current; schema valid |
| `duplicate` | `event_id` already stored with identical content (the replay of an offline flush) |
| `conflict` | a second non-superseding event for the same (`study_id`, `screener_id`) whose outcome differs; both are stored and the study moves to `GET /decisions/conflicts` |
| `refused` | a typed refusal (§7): stale binding, unknown study, bad reason code, `event_id` reused with different content (`IDEMPOTENCY_CONFLICT`), wrong token scope |

M11b part A adds two checks on **new** events only (a replay of a stored event stays a `duplicate`): an EXCLUDE whose reason cites a criterion an amendment retired is refused `REASON_CODE_RETIRED`; and a decision on a study shown again must supersede the decision shown again (`supersedes`, or `resolves` on a conflict resolution), else it is refused `INVALID_OUTPUT`, because a second head with the same outcome would leave the earlier one winning.

A repeat of the same outcome from a second device is not a conflict. It is stored and treated as a confirmation. Intake is atomic per request: the events file and its journal row are written together or not at all (`ATOMIC_COMMIT_FAILED`).

## 4. Endpoints

**Scopes:**
- `desktop` is the per-launch token on loopback (INC-01).
- `phone` is the short-lived token from `POST /lan/pair`, accepted only on the restricted LAN sub-app (plan §4).

M = milestone; ✓ = route exists today.

| Method and path | Purpose | Request → Response | Scope | M |
| :-- | :-- | :-- | :-- | :-- |
| `GET /summary` | home progress | → `{total, decided, by_outcome, agent_proposed, needs_you, conflicts, queued_on_phones?, lanes:{agent, you, second_screener:"PARKED"}, protocol_changed}`. `protocol_changed` (review F2, H-protocol-signals): a current batch was prepared under another protocol than `protocol.json` now, so earlier decisions count nowhere; Home shows `PROTOCOL_CHANGED_SINCE_BATCH` (a UI state, not a refusal). Only the current screening round's batches count (M3g). M11b part A adds `criteria_version` (the criteria in force) and `recheck` (how many of the screener's decisions an amendment shows again; they count in `needs_you`, not in `decided`) | desktop, phone | M1a |
| `GET /queue?view=&cursor=&limit=` | cross-batch queue in server order (items carry `batch_index` since M6-beta) | `view ∈ {needs_you, proposal_ready, no_proposal, title_only, decided, recheck}` (`recheck`, M11b part A: the decisions a criteria amendment shows again; they are also in `needs_you`; a draft made under an earlier criteria version does not order `agent_uncertainty`), plus `order=agent_uncertainty` after a run: it orders by how unsure the agent was, without revealing its call, and is disclosed in the methods paragraph → `{items:[{study_id, title, batch_id, has_proposal, decided, flags}], next_cursor, protocol_changed}` (`protocol_changed` as on `/summary`). `has_proposal` is a boolean only, and agent outcomes are never returned before a decision. Views that reveal agent calls (`agent_disagrees`) need `decided=true`. | desktop, phone | M1a |
| `GET /records/{study_id}` | record detail | → `{study_id, title, authors, year, venue, doi, abstract, batch_index (M6-beta), highlights:[{start,end,criterion_id}], criteria:[{id, text, kind}], binding, my_decision?, history:[event…], not_reported_policy (M7-method), search_terms:{concepts:[{concept, terms, mentions}], marks:[{field, start, end, concept}]} (M8b)}`; `search_terms` lists the protocol's concepts in order with their words and mentions, and the non-overlapping places of those words in the title or the abstract (`field`), offsets in UTF-16 code units of the string served; `highlights` stays empty. M11b part A: `criteria` are the criteria in force, each with `since_version` (the version its wording dates from); `criteria_version`; `shown_again: {decision, criteria_version} | null`, the earlier decision a criteria amendment shows again (then `my_decision` is null) | desktop, phone | M1a |
| `GET /records/{study_id}/proposal` | agent draft | → `{proposal_id, task_version, model, prompt_sha256, criteria:[{id, answer, evidence:{start,end,text}}], derived_outcome, reason_code, validators:[…], cannot_decide, not_reported_policy, recorded:{derived_outcome, reason_code, not_reported_policy}, quotes:[{criterion_id, answer, found, field, start, end}] (M8b)}`; **`PROPOSAL_HIDDEN`** until a decision exists and blinding is on. `derived_outcome` and `reason_code` are derived when read, under the not-reported policy in force; `recorded` is what the store holds (`not_reported_policy` null for a draft stored before H-screening-drafts). M11b part A: `criteria_version` (the version the draft answered) and `earlier_wording` (true when that is not the version in force: the draft keeps its stored outcome and is left out of agreement, calibration and queue order) | desktop, phone | M1a |
| `POST /decisions/events` | submit decisions | `{events:[…]}` (≤ 200) → `{results:[{event_id, result, decision_id?, refusal?}]}` | desktop, phone | M1a |
| `GET /decisions/conflicts` | conflicts to resolve | → `{items:[{study_id, events:[…]}]}` | desktop, phone | M1a |
| `POST /decisions/conflicts/{study_id}/resolve` | keep one | `{keep_event_id}` → writes a superseding event that names both. M11b part A (review round 3, decision item 11): the resolution is bound to the record as it is now (`binding.criteria_version` in force) and is stamped with the criteria version of the event it keeps, which may cite a criterion retired since; a revision that could change that decision then shows the record again (`view=recheck`) | desktop, phone | M1a |
| `GET /settings`, `PUT /settings` | screening settings | `{blinding: "reveal_after_decision"\|"show", mode: "human_sees_every_record"\|"ai_agreed_exclusion", sample_audit_size?, queue_order: "seeded"\|"agent_uncertainty", advance_on_decide: "show_draft_then_next"\|"next_at_once", blinding_source: "protocol"\|"settings" and not_reported_policy: "unclear"\|"exclude"\|"decisive_first" (read-only, M7-method; `decisive_first` H-screening-drafts), not_reported_source: "protocol"\|"defaults"\|"amendment" and method_amendments: [{amendment_id, field, from, to, amended_by, amended_at, protocol_fingerprint, note}] (read-only, H-screening-drafts), reporting: "prisma-2020"\|"prisma-scr"\|"none" and reporting_source: "protocol"\|"playbook"\|"defaults" (read-only, M7b-guideline; "defaults" only when `protocol.json` is missing or unreadable)}` (when the protocol's method block sets blinding, a `PUT` that changes it is refused `BLINDING_SET_BY_PROTOCOL`, and `POST /method/amendments` changes it; an invalid block refuses `PROTOCOL_METHOD_INVALID`) (`queue_order` M5-slim: `GET /queue` uses it, and an `order` parameter that differs is refused `INVALID_OUTPUT`); turning on AI-agreed exclusion needs a confirmation body and is journaled | desktop | M1a |
| `GET /approver`, `PUT /approver` | the name approvals are recorded under | `GET` → `{name: string\|null, set_at, basis: "typed-name"}`. `PUT {name}` (whitespace collapsed, 1–120 printable characters) writes `literature/screening/operator_context.json`, the operator context the approval reads, and journals `SCREENING_APPROVER_SET` with the name before and after; the same name again writes nothing. Refuses `INVALID_OUTPUT` (empty, too long, control characters) and `APPROVAL_NOT_OPERATOR` (a name the engine never trusts as a person, e.g. "unknown"). A typed name, not a verified sign-in (CON-02/03); approvals already made keep the name they were made under (decision 2026-11-06) | desktop | M5-slim |
| `GET /corpus` | the corpus import (spec 11) | → `{shape:"screening.corpus-v1", state: "EMPTY"\|"STAGED"\|"ACCEPTED", sources:[{id, label, file_name, format, records, searched_on, query, limits, rejected:[{line, code, reason}]}], databases:[{label, records, files, searched_on:[…], search_details_missing}], preview:{identified, duplicates, unique_studies}, accepted:{artifact_id, accepted_at, records, studies, duplicates}\|null, from_discovery, limits:{max_source_bytes, label_max_length}, staging_refused:{code, message}\|null}`. The preview uses the snapshot's own deduplicator and writes nothing. M3d-engine: `STAGED` also means a search run's `verified.json` waiting for the hand-off accept (`from_discovery: true`); `sources[].limits` is the researcher's verbatim limits string (not the top-level upload `limits`); `rejected` lists the lines the importer could not use (`IMPORT_NO_TITLE`, `IMPORT_BAD_TAG`, `IMPORT_BAD_YEAR`); `staging_refused` is the refusal staging would answer now (`CORPUS_ALREADY_ACCEPTED` after the accept; `VERIFIED_EXISTS` only for a `verified.json` that no search run and no import made, since M3f-combined-corpus; before M3f it answered `VERIFIED_EXISTS` after any search run). Review F4 (H-protocol-signals): `origin` is `"imports"`, `"discovery"`, `"citation_searching"` or `null`; for a search run's corpus (before and after the accept) `databases` has one row per database the run searched, from its `legs.json` (`label` is the database's name, `records` its fetched count, `files: 0`, `searched_on` the leg dates, `search_details_missing: false`, plus `provider`, `status`, `cap_hit`), and `preview` is `{identified: Σ fetched, duplicates: identified − unique_studies, unique_studies: len(deduped.json)}`; in an M3g citation-searching round `preview` comes from the chase run (identified = fetched, duplicates = found twice or already in the corpus, unique_studies = the new works) while `databases` stays the staged exports' rows (none when round 1 was a browser harvest) and `from_discovery` keeps its value (citation searching is not a database row). M3f-combined-corpus: `harvest: {run, state, included} | null` is the harvest part (the newest published search run, its preparation state, and whether the accept includes it: only when `ready`); with exports staged beside an included harvest, and after such a corpus is accepted, `origin` is `"combined"`, `from_discovery` is true, `databases` is the harvest's rows then the exports' rows, and `preview` is `{identified: Σ fetched + every imported record, duplicates: identified − works, unique_studies: works}` from one deduplication of both parts (the same one the accept runs) | desktop | M5b |
| `POST /corpus/sources` | stage one database's export, RIS or PubMed MEDLINE `.nbib` (M5c-nbib: the format is chosen by the file's extension, else by its first line, and returned as `format` on each source row) | `{label, file_name, content_base64, searched_on?, query?, limits?}` (`limits`: at most 2,000 characters, stored verbatim, M3d-engine; extra fields refused; a label may repeat for a database exported in parts, and its files are summed per database) → 201 + the `GET /corpus` body; the file is kept under `literature/raw/ris/`; journaled `CORPUS_SOURCE_STAGED`. Refuses `SOURCE_LABEL_INVALID`, `SOURCE_DATE_INVALID` (not a real `YYYY-MM-DD` date), `SOURCE_NOT_RIS` (422; also content that is not base64), `SOURCE_TOO_LARGE` (413, 50 MB), `SOURCE_DUPLICATE_FILE`, `VERIFIED_EXISTS`, `CORPUS_ALREADY_ACCEPTED` (409) | desktop | M5b |
| `POST /corpus/sources/{id}/remove` | drop a staged export file | → the `GET /corpus` body; journaled `CORPUS_SOURCE_REMOVED`; `SOURCE_NOT_FOUND` (404), `CORPUS_ALREADY_ACCEPTED` (409) | desktop | M5b |
| `POST /corpus/accept` | UI for `nexus-scholar accept-corpus` | → the `GET /corpus` body, `state: "ACCEPTED"`; writes `verified.json` and `literature/raw/provenance_manifest.json`, then the acceptance gate publishes the snapshot (journaled). With nothing staged and a search run's `verified.json` (`from_discovery`), it is the discovery hand-off (M3d-engine): no file is written before the gate, the snapshot is built from that `verified.json` with the run's failed databases as provider warnings, and `CORPUS_SNAPSHOT_ACCEPTED` is journaled with the `run`; `PROTOCOL_CHANGED_SINCE_RUN` (409) when the protocol now compiles to another search than the run's: query, years, language, retrieval cap or database list (review F3; a run written before F3 is compared on its query and years only). An edit outside the search (criteria, title) does not refuse; `GET /discovery/handoff` flags it. `PREPARATION_UNFINISHED` (409, M3i) when nothing is staged and the newest published run's stages after the search have not ended; `NOTHING_STAGED` (also when every imported file was removed), `CORPUS_ALREADY_ACCEPTED`, `PROTOCOL_INVALID`, and `ACCEPT_CORPUS_REFUSED` when the acceptance gate refuses the snapshot (409, its issues in the message) | desktop | M5b |
| `POST /method/amendments` | change the method after genesis (H-screening-drafts) | `{field: "blinding"\|"not_reported", value, confirm: true, note?}` → `{amendment, settings}`. `protocol.json` and its fingerprint are not changed; one line of `audit/method_amendments.jsonl` and one `PROTOCOL_METHOD_AMENDED` journal row (who, when, from, to, the protocol fingerprint). An amendment applies only under the protocol it was made under. Blinding can be amended only when the protocol's method block sets it (otherwise it is the `PUT /settings` value). Refuses `METHOD_AMENDMENT_INVALID` | desktop | H-screening-drafts |
| `GET /criteria` | the criteria in force (M11b part A) | → `{criteria_version, criteria:[{id, side, text, reason_category, since_version}], retired:[id…], amendments:[{amendment_id, op, side, from, to, reason, criteria_version_before, criteria_version_after, protocol_fingerprint, pilot_id, decided_at_time, shown_again, amended_by, amended_at}], can_amend, batches_prepared, batch_approved}`; the signed list plus the amendments made under the current protocol fingerprint, oldest first | desktop | M11b |
| `POST /criteria/amendments` | revise a criterion beside the signed protocol (M11b part A) | `{op: "reword"\|"split"\|"merge"\|"remove"\|"add"\|"reason_category", side: "inclusion"\|"exclusion", ids:[…], text?: string (reword, merge, add) \| [2 to 10 strings] (split), reason_category?, reason (required to record, ≤ 500 characters), confirm: true\|false}` → `{recorded, op, side, new_ids, retired_ids, criteria_version_before, criteria_version_after, decided, shown_again:{INCLUDE, MAYBE, EXCLUDE, total}, waiting_after, amendment?}`. `confirm: false` is the dry call and writes nothing. `confirm: true` appends one line to `audit/criteria_amendments.jsonl` (id `CRA-` + 24 hex), rewrites `SCREENING_CRITERIA.md` (the earlier file backed up under `audit/amended/<stamp>/`), rebuilds the projected batch files and journals `PROTOCOL_CRITERIA_AMENDED`; `protocol.json`, its fingerprint, the corpus snapshot and the batch files are not changed. A reword keeps the id; split, merge and remove retire ids; a new id takes the next number on its side after every id ever used. Refuses `CRITERIA_AMENDMENT_NO_BATCHES`, `CRITERIA_AMENDMENT_AFTER_APPROVAL`, `CRITERIA_AMENDMENT_HANDOFF` (409), `CRITERIA_AMENDMENT_INVALID`, `CRITERIA_SIDE_EMPTY` (422) | desktop | M11b |
| `POST /prepare` | allowlisted prepare job | `{batch_size}` (5 to 100, default 20; passed to the job since M6-beta) → `{job_id}`; refuses `SNAPSHOT_NOT_ACCEPTED`, `BATCH_SIZE_INVALID` | desktop | M1a |
| `POST /proposals/runs` | estimate, or start, an agent run | `{driver:"api", provider: "anthropic"\|"openai_compatible"\|"gemini", model, effort, base_url? (OpenAI-compatible), scope:{view: "needs_you"\|"no_proposal" \| study_ids}, consent?:{provider, accepted_at}, cost_ceiling_usd?, dry_run? (the first 20 records), estimate_only? (writes nothing)}` → `{run_id (null for an estimate), estimate:{records, tokens:{input_tokens, cache_read_tokens, cache_write_tokens, output_tokens}, assumptions, cost_usd, batch, prices_as_of, priced}}`. Refuses `CONSENT_REQUIRED`, `PROVIDER_KEY_MISSING`, `DRIVER_UNAVAILABLE`, `CEILING_NOT_PRICED`, `COST_CEILING_REACHED` (the estimate is above the ceiling), `RUN_ALREADY_ACTIVE`, `UNKNOWN_STUDY`, `INVALID_OUTPUT` (bad scope or consent) | desktop | M1b |
| `POST /proposals/calibrations` | check the agent on your labels | `{study_ids, provider, model, effort, base_url?, cost_ceiling_usd?}` → `{run_id}`; the same refusals as a run; result `{include_recall, ci_low, missed_includes:[…]}`. **Advisory:** a missed include shows a warning and never blocks a run, because the researcher decides whether to trust it | desktop | M1b |
| `GET /proposals/setup` | what the run screen needs before a run | → `{task:{task_version, prompt_sha256, model, effort}, providers:[{provider, key: "keychain"\|"environment"\|"none", consent}], data_flow, active_run, latest_run, last_model: {provider, model}\|null}` (`last_model`: the newest run of any kind in this workspace, H-screening-drafts); `earlier_wording_drafts: {criteria_version, count, study_ids}` (M11b part A: the records whose latest draft predates the criteria version in force); names where a key is stored, never the key (M1b-2) | desktop | M1b |
| `GET /proposals/runs/{run_id}` | run status | → `{run_id, kind, state: "running"\|"completed"\|"stopped"\|"cancelled"\|"failed", cancel_requested (H-run-small-fixes: a cancel asked and the run not stopped yet), code, provider, model, effort, records, done, failed, refused, truncated, invalid, check_failures, cost_so_far (null when the provider/model is not priced), cost_ceiling_usd, started_at, finished_at, batch, chunk_size, calibration?}` (`batch`: sent to the provider's batch service, answers arrive in chunks of `chunk_size`; H-screening-drafts). A Batch run checks the ceiling between chunks of 200 records | desktop | M1b |
| `POST /proposals/runs/{run_id}/cancel` | cancel | → `{run_id, state, cancel_requested}` (H-run-small-fixes, finding 35: `state` is the run's own, `"running"` with `cancel_requested: true` until its worker notices the cancel, at the latest after the current chunk of a Batch run; before, the answer said `"cancelled"` at once and the screen offered Start, which the engine refused `RUN_ALREADY_ACTIVE`); a run left `running` by an engine that stopped is finished as cancelled and frees the workspace lock | desktop | M1b |
| `GET /prisma/preview` | PRISMA screening box | → `{identified, duplicates_removed, screened, excluded:{total, by_reason}, unclear_to_full_text, included, not_yet_decided, checks:[{name, ok, detail}]}`; `checks` covers HUMAN provenance on every decision, no open conflicts, every batch bound to the current protocol (`bound_to_current_protocol`, review F2: false with no decision, and false when a current batch was prepared under another protocol), the sample audit if the opt-in is on, and agreement attached | desktop, phone | M1a |
| `GET /agreement` | agreement with the agent | → `{decided_with_proposal, decided_after_seeing_the_draft, agreement_pct, table_2x2, splits_by_criterion:[{criterion_id, n}], unclear_either_side, kappa: null, kappa_note: "needs a second human screener"}`; counts only decisions made before the reveal | desktop | M1b |
| `GET /export?format=ris\|csv&set=included,unclear,excluded` | export the published decisions | read-only, from the **published** generation only (`included.json`, `excluded.json`; unclear = `screening.decision == "MAYBE"` in `included.json`; reason codes from the generation's decision files). Default `set` is `included,unclear` for RIS and all three for CSV. → file bytes with `Content-Disposition: attachment; filename="{slug}-screening-{generation_id}-{set}.{ris\|csv}"`. RIS: `TY  - JOUR` blocks with `TI AU PY T2 DO UR AB ID N1 ER`, UTF-8 without BOM, no empty field. CSV: `study_id, decision, reason_code, title, authors, year, venue, doi, url, abstract, generation_id`, UTF-8 with BOM, CRLF. Refuses `EXPORT_NOT_PUBLISHED`, `GENERATION_STALE` (a decision changed after publication, or the generation is otherwise stale), `GENERATION_SUPERSEDED`, `EXPORT_SOURCE_MISMATCH`, `EXPORT_FORMAT_INVALID`. No journal row (spec 10) | desktop | M5-slim |
| `GET /methods` | methods paragraph of the published screening | → `{generation_id, generation_fingerprint, published_at, language: "en", paragraph, figures, sources:[{name, path, digest?}], caveats, not_stated}`; a fixed English template of facts and counts from `prisma_report.json`, the `SCREENING_SETTINGS_CHANGED` history, proposals, agent runs, consent, decision events and reveals; every number in `paragraph` is a value in `figures`. Same currentness refusals as `/export`, plus `METHODS_SOURCE_MISSING`. Writes no file and no journal row (spec 10) | desktop | M5-slim |
| `POST /lan/session/begin` | show the phone QR | → `{qr_payload, one_time_token_expires_at}`; desktop only; separate from approval pairing | desktop | M2 |
| `POST /lan/session/stop` | stop phone access | revokes every phone token | desktop | M2 |
| `POST /actions/pairing/begin` | start approval pairing for one batch | `{batch}` → `{batch_index, snapshot_fingerprint, code_expires_at, attempt_cap, code_shown_on: "terminal"\|"desktop"}`. The code is printed only in the terminal running the console, never returned over HTTP (decision 2026-11-04). `"desktop"` (H-run-small-fixes Part A, PROPOSED): the packaged app (`nexus-scholar ui`) also showed it in a window of the engine's own process on this computer's desktop | desktop | M1a |
| `POST /actions/pairing/begin-all` | stage the codes of every decided batch (H-run-small-fixes Part A, finding 38; PROPOSED) | `{}` → `{batches:[{batch_index, snapshot_fingerprint}], skipped:[{batch_index, reason: "ALREADY_APPROVED"\|"DEFERRED"\|"NOT_DECIDED"\|<refusal code>}], code_expires_at, attempt_cap, code_shown_on}`. One fresh code per batch generation, staged exactly as `begin` stages it (§9.1 unchanged); a batch gets one when every candidate has a terminal decision, it has no current approval (none, or one made before a decision changed) and it is not deferred. The codes are printed together on the terminal as `batch n: CODE` lines (and shown in the desktop window, as for `begin`), never returned. A batch that refuses its own code (for example `WORKER_BATCH_MISSING`) is listed under `skipped` with that code and the others still get theirs. Refuses `APPROVAL_MISSING` (409) when no batch is ready, `OPERATOR_CONTEXT_MISSING` without an approver | desktop | H-run-small-fixes |
| `POST /actions/pairing/redeem-all` | approve from one pasted block (H-run-small-fixes Part A; PROPOSED) | `{codes, request_id?}` → `{shape: "screening-action-redeem-all-v1", request_id, approved:[{batch_index, approval_fingerprint, journal_event_id}], refused:[{batch_index, code, message}], publication_approval_fingerprint}`. Each `batch n: CODE` pair goes through `redeem` unchanged, in batch order, with the same approval file, journal row (`SCREENING_PAIRING_REDEEMED`, plus `bulk: true`) and rollback; a refused pair does not stop the others. With nothing approved, the first refusal is the answer (`PAIRING_CODE_INVALID` 403 when the text holds no code; text over 64,000 characters holds none). A journal failure answers 500 `ACTION_AUDIT_FAILED` with `details.approved` and `details.refused` (that batch, then the later ones as `NOT_ATTEMPTED`) | desktop | H-run-small-fixes |
| `GET /actions/pairing/status` ✓ | pairing state | `screening.py:1407` | desktop, phone (read-only) | — |
| `POST /actions/pairing/redeem` ✓ | approve | `screening.py:1429` (fix the proxy allowlist path, plan §1.2). **Desktop only in stage 1:** the phone shows the PRISMA summary and "Approve on your desktop" (changed from the MobileApprove canvas) | desktop | M0 |
| `POST /actions/defer` ✓, `POST /actions/publish` ✓ | defer or publish | `screening.py:1512, :1581` | desktop | — |
| `POST /lan/pair` | phone pairing | `{one_time_token}` → sets the phone session cookie. The one-time token lasts 2 minutes and works once. The phone session ends at the first of: `POST /lan/session/stop`, the desktop `nexus-scholar ui` process stopping, or 12 hours. Expired or reused tokens are refused | LAN sub-app only | M2 |
| `GET /ui/batches`, `/ui/batch/{n}/review` ✓ | existing reads | kept; the new screens use `/queue` and `/records`. `/ui/batch/{n}/rows`, `/criterion-refs`, `/ui/audit-feed` and `/ui/project-summary` were removed in M6-hardening (no caller) | desktop | — |

**Note on `mode` (2026-11-10, informational; the contract above is unchanged).** The setting `mode: "ai_agreed_exclusion"` exists in name only: no code reads it, so it changes nothing in the queue or the intake; it is only reported in the methods paragraph (`screening/export.py`). The researcher decided on 2026-11-10 to replace it with the modes of the [agent autonomy ladder](agent_autonomy_ladder.md) (§3, §6). That replacement is a contract change planned as M9b-ladder-engine; until it lands, this table is what the engine answers.

**Errors.** Every route answers a refusal as HTTP 4xx with `{"detail": {"code": "<CODE>", "message": "…", "retryable": false, "details": {…}}}`, the shape the existing actions already use (for example `ACTION_ORIGIN_REFUSED` in `tests/console/test_screening_actions.py`). **Pagination** is cursor-based and opaque to the client.

## 5. Proposals as the UI sees them

The UI reads proposals only through `GET /records/{study_id}/proposal`. The fields are a subset of the stored proposal (agent-system §4). `derived_outcome` comes from the plain-code rule table, never from the model. `validators` lists each check and its result, so the UI can show "quote not found in abstract" or "refused by provider" as the reason a proposal routed to Unclear. The UI styles every proposal as a draft (BRAND_BOOK).

`quotes` (M8b-triage-highlights) is computed when the draft is read: for each answer that quotes the record (never a `not_reported` one), `found` says whether the record text, rebuilt as the run built it (`record_text`: title, blank line, stripped abstract, the year line), holds the quote at its offsets; `field` is `title` or `abstract` when the quote lies inside one of them, with `start`/`end` in UTF-16 code units of the string `GET /records/{study_id}` serves, and `null` otherwise (year line, across the two fields, or not found). The draft's own `evidence.start/end` keep counting code points in the record text. `quotes` is part of the draft, so `PROPOSAL_HIDDEN` hides it.

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
| `PROVENANCE_MISSING` | events intake, collect | a decision lacks screener, method or `decided_at`, or its `decided_at` is more than 5 minutes ahead of the engine's clock (H-input-limits, F7); refused, never filled in (CON-11) |
| `PROJECTION_STALE` | publish, PRISMA preview check | a `batch_NNN_decisions.json` differs from the decision events (its rewrite failed); publish refuses until a retry re-projects it (M1b-0) |
| `EXPORT_NOT_PUBLISHED` | `/export`, `/methods` | HTTP 409: no screening generation has been published (M5-slim, spec 10) |
| `EXPORT_FORMAT_INVALID` | `/export` | HTTP 422: `format` is not `ris` or `csv`, or `set` names an unknown set (M5-slim) |
| `EXPORT_SOURCE_MISMATCH` | `/export`, `/methods` | HTTP 409: a published file is missing or its digest differs from `generation.json`; nothing is exported (M5-slim) |
| `METHODS_SOURCE_MISSING` | `/methods` | HTTP 409: `prisma_report.json`, which the paragraph cannot omit, is missing or lacks a count; missing optional sources are listed under `caveats` (M5-slim) |
| `SOURCE_LABEL_INVALID` | `/corpus/sources` | HTTP 422: the database name is empty, too long or uses other characters (M5b) |
| `SOURCE_DATE_INVALID` | `/corpus/sources` | HTTP 422: date searched is not a real `YYYY-MM-DD` date (M5b) |
| `SOURCE_NOT_RIS` | `/corpus/sources` | HTTP 422: no RIS or PubMed `.nbib` records in the file, or content that is not base64 (M5b; `.nbib` since M5c-nbib) |
| `SOURCE_TOO_LARGE` | `/corpus/sources` | HTTP 413: the file is over 50 MB (M5b) |
| `SOURCE_DUPLICATE_FILE` | `/corpus/sources` | HTTP 409: the same file is already staged (M5b) |
| `SOURCE_NOT_FOUND` | `/corpus/sources/{id}/remove` | HTTP 404: no staged file has that id (M5b) |
| `VERIFIED_EXISTS` | `/corpus/sources` | HTTP 409: `verified.json` holds records that no search run and no import of this app made (unknown origin), so an export is not mixed with them (M5b; since M3f-combined-corpus no longer raised after a search run) |
| `CORPUS_ALREADY_ACCEPTED` | `/corpus/*` writes | HTTP 409: the corpus is frozen (M5b) |
| `NOTHING_STAGED` | `/corpus/accept` | HTTP 409: no database file staged (M5b) |
| `PROTOCOL_INVALID` | `/corpus/accept` | HTTP 409: `protocol.json` does not validate (M5b) |
| `ACCEPT_CORPUS_REFUSED` | `/corpus/accept` | HTTP 409: the acceptance gate refused the snapshot; its issues in the message (M5b) |
| `BATCH_SIZE_INVALID` | `/prepare` | HTTP 422: batch size outside 5 to 100 (M6-beta) |
| `PROTOCOL_METHOD_INVALID` | `/settings`, `/corpus`, `/corpus/accept` | HTTP 409: the protocol's `method` block is outside the checked limits (M7-method) |
| `BLINDING_SET_BY_PROTOCOL` | `PUT /settings` | HTTP 409: the protocol's method block sets blinding; change it with `POST /method/amendments` (M7-method; the route since H-screening-drafts) |
| `METHOD_AMENDMENT_INVALID` | `/method/amendments` | HTTP 422: a field other than `blinding` or `not_reported`, an unknown value, the value already in force, blinding on a protocol without a method block, or no `confirm: true` (H-screening-drafts) |
| `CRITERIA_AMENDMENT_INVALID` | `/criteria/amendments` | HTTP 422: an unknown op or side, an unknown or retired id, an id of the other side, the wrong number of ids or texts for the op, a revision that changes nothing, no reason or one over 500 characters when recording, or no `confirm` (M11b part A) |
| `CRITERIA_AMENDMENT_NO_BATCHES` | `/criteria/amendments` | HTTP 409: no screening batch is prepared; criteria are revised from the moment batches exist (M11b part A) |
| `CRITERIA_AMENDMENT_AFTER_APPROVAL` | `/criteria/amendments` | HTTP 409: a batch is approved, or the workspace screens a later citation-chasing round; changing the criteria now is a new screening (M11b part A) |
| `CRITERIA_SIDE_EMPTY` | `/criteria/amendments` | HTTP 422: the revision would leave no inclusion or no exclusion criterion in force (M11b part A) |
| `CRITERIA_AMENDMENT_HANDOFF` | `/criteria/amendments` | HTTP 409: a current batch holds a worker recommendation or a decisions file not built from decision events (the file hand-off); a revision could not show those decisions again (M11b part A, review round 1) |
| `REASON_CODE_RETIRED` | events intake | a new EXCLUDE cites a criterion a criteria amendment retired; events stored before keep it (M11b part A) |
| `BATCHES_NOT_PREPARED` | screening reads (`/queue`, `/records`, `/agreement`, runs) | HTTP 409: the corpus is accepted but no screening batch is prepared yet; before H-screening-drafts these reads said `SNAPSHOT_NOT_ACCEPTED` |
| `DRAFT_ID_INVALID` | `/inception/drafts/{id}` | HTTP 422: the id is not `rec_` followed by hex digits (M4a) |
| `DRAFT_NOT_FOUND` | `/inception/drafts/{id}` | HTTP 404: no draft with that id (M4a) |
| `DRAFT_UNREADABLE` | `/inception/drafts/{id}` | HTTP 500: the stored draft cannot be read (M4a) |
| `DRAFT_EXISTS` | `/inception/drafts` | HTTP 409: a draft with that id already exists (M4a) |
| `DRAFT_CONFLICT` | `PUT /inception/drafts/{id}` | HTTP 409: the draft changed since `base_updated_at`; reload it (M4a) |
| `DRAFT_EMITTED` | `/inception/drafts/{id}` save, genesis | HTTP 409: this draft already created a workspace (M4a) |
| `DRAFT_INVALID` | `/inception/*` | HTTP 422: the draft does not match the draft shape, or names an unknown paradigm or playbook (M4a) |
| `DRAFT_INCOMPLETE` | `/inception/steps`, preview, genesis | HTTP 422: the step needs answers the draft lacks; `details.missing` names them (M4a) |
| `STEP_UNKNOWN` | `/inception/steps/{step}` | HTTP 404: not `scope`, `shape`, `criteria` or `matrix` (M4a) |
| `CRITERIA_UNDECIDED` | preview, genesis | HTTP 422: a criterion the wizard wrote has no accept/reject decision (M4a, INC-22) |
| `CRITERIA_MISSING` | preview, genesis | HTTP 422: no accepted inclusion or no accepted exclusion criterion (M4a) |
| `INTENT_INVALID` | preview | HTTP 422: the protocol compiler refused the intent (M4a) |
| `SCREENING_BOUND` | genesis with `replace` | HTTP 409: the workspace has screening decisions or a publication; `details` gives the counts (M4a, INC-08) |
| `CONFIRMATION_MISMATCH` | genesis | HTTP 422: the typed confirmation is not the workspace slug (M4a, INC-08) |
| `WORKSPACE_JOB_ACTIVE` | genesis with `replace` | HTTP 409: a discovery or console job is still running in the workspace; nothing moved (M4d, F1) |
| `ARCHIVE_INCOMPLETE` | genesis with `replace` | HTTP 409: archiving the old corpus stopped part way; `details {backup_dir, moved, not_moved}`, journaled as `PROTOCOL_REPLACE_INCOMPLETE`; the protocol was not replaced (M4d, F1) |
| `MAILTO_NOT_SET` | recon probe, delta; discovery runs, recall, estimate | HTTP 409: the console has no contact email (`SCHOLAR_MAILTO`); no request was sent (M4c, M3b-api) |
| `OPENALEX_KEY_NOT_SET` | discovery runs, estimate | HTTP 409: the run selects OpenAlex and the console has no `SCHOLAR_OPENALEX_KEY` (OpenAlex requires a key since 2026-02-13); no request was sent (M3h-providers) |
| `RECON_SESSION_INVALID` | `/inception/drafts/{id}/recon/*` | HTTP 422: the id is not a recon session id, or its folder would be under `workspaces/` (M4c) |
| `RECON_SESSION_NOT_FOUND` | `/inception/drafts/{id}/recon/*` | HTTP 404: the draft has no recon session yet; run a probe (M4c) |
| `RECON_NO_POOL` | distill, directions, delta, bind, narrower probe | HTTP 409: the session has no usable pool; run a probe (M4c) |
| `POOL_EMPTY` | recon probe job | the probe found no papers; nothing was cached (M4c, INC-09) |
| `PROVIDERS_FAILED` | recon probe job | every database failed; `details.legs` names each failure; nothing was cached (M4c, INC-09) |
| `POOL_TOO_SMALL` | recon bind | HTTP 409: the pool is under the floor of 12 papers; bind again with `accept_thin_pool` (M4c) |
| `NARROW_BUDGET_SPENT` | recon probe with `narrower` | HTTP 409: the draft's one narrower search is used (M4c) |
| `DIRECTION_UNKNOWN` | recon probe with `narrower`, bind | HTTP 422: the label is not a direction of the current pool; `details.directions` lists them (M4c) |
| `NO_DIRECTION` | recon bind | HTTP 422: send exactly one of `direction` or `own` (M4c) |
| `RECON_JOB_ACTIVE` | recon probe, delta | HTTP 409: a search for this draft is already running (M4c) |
| `RECON_JOB_NOT_FOUND` | `.../recon/jobs/{job_id}` | HTTP 404: no recon job with that id for this draft (M4c) |
| `RECON_FAILED` | recon jobs | the job stopped on an unexpected error; `message` names it (M4c) |
| `TERM_EMPTY` | recon evidence | HTTP 422: the phrase to check is empty (M4d) |
| `PROTOCOL_MISSING` | discovery plan, runs, recall, report, handoff | HTTP 409: the workspace has no `protocol.json` (M3b-api) |
| `DISCOVERY_JOB_ACTIVE` | discovery runs, recall, estimate | HTTP 409: a discovery job is already running for this workspace; `details.job` is it (M3b-api) |
| `DISCOVERY_JOB_NOT_FOUND` | `/discovery/jobs/{job_id}` | HTTP 404: no discovery job with that id in this workspace (M3b-api) |
| `RUN_NOT_FOUND` | `/discovery/runs/{run}`, report, report methods | HTTP 404: no search run of that name, or no run yet (M3b-api) |
| `RECALL_NOT_RUN` | `GET /discovery/recall` | HTTP 404: no recall check has been run (M3b-api) |
| `SEEDS_INVALID` | discovery recall | HTTP 422: no seed, more than 25, or a malformed DOI or arXiv id (M3b-api) |
| `CAP_INVALID` | discovery runs, estimate | HTTP 422: `cap_override` (a run) or `cap` (the size estimate's what-if, M10b) is not 1 to 10,000 (M3b-api) |
| `PACE_INVALID` | discovery estimate | HTTP 422: the size estimate's `pace_seconds` is not a whole number from 5 to 600; no database was asked (M10b) |
| `WORKBENCH_BUDGET_SPENT` | query workbench | HTTP 409: a Count (or a synonym or removed read) would pass a database's daily workbench request budget; `details.databases` names each with `limit`, `spent`, `left`, `renews_at`; nothing was sent (M11a) |
| `WORKBENCH_VERSION_INVALID` | query workbench | HTTP 422: the version cannot be searched (no concept with a term, years out of order, a query key other than `main`, a concept index it does not have); nothing was sent (M11a) |
| `WORKBENCH_STATE_UNREADABLE` | query workbench | HTTP 503: the shared budget and quota file (`<workspaces root>/.query_workbench/state.json`) cannot be read after a few tries; nothing was sent and the file is not overwritten (M11a) |
| `WORKBENCH_COMPARISON_FORMAT` | query workbench | HTTP 422: the comparison file is not a RIS or NBIB export (unreadable, not base64, or no record with a title); nothing was kept (M11a) |
| `WORKBENCH_COMPARISON_TOO_LARGE` | query workbench | HTTP 422: the comparison export holds more than 5,000 records (or is over 50 MB); nothing was kept (M11a) |
| `WORKBENCH_COMPARISON_FULL` | query workbench | HTTP 409: five comparison sets are already staged; nothing was kept (M11a) |
| `WORKBENCH_COMPARISON_NOT_FOUND` | query workbench | HTTP 404: no comparison set with that id beside this draft or workspace (M11a) |
| `WORKBENCH_COMPARISON_MEASURE` | query workbench | HTTP 409: the report's measure `harvest` has no run or accepted corpus to compare with (at Inception, always); an unknown measure is `BODY_INVALID` (M11a) |
| `WORKBENCH_REASON_INVALID` | query workbench | HTTP 422: the researcher's amendment from Plan has no reason, or one over 2,000 characters; nothing was written (M11a) |
| `WORKBENCH_PROTOCOL_CHANGED` | query workbench | HTTP 409: the protocol's fingerprint is not the one the page read (another tab, an assistant's amendment); nothing was written (M11a) |
| `PROVIDER_UNKNOWN` | discovery runs, recall, estimate | HTTP 422: a database name the engine does not know; `details.known` lists them (M3b-api) |
| `DISCOVERY_FAILED` | discovery jobs | the job stopped on an unexpected error; `message` names it (M3b-api) |
| `PROTOCOL_CHANGED_SINCE_SNAPSHOT` | discovery run job `error` | the protocol no longer matches the accepted snapshot; resume refused (E5, M3b-api; also the reason's prefix) |
| `BATCHES_INCOMPLETE` | discovery run job `error` | the accepted snapshot has studies in no screening batch; resume refused (E5, M3b-api; also the reason's prefix) |
| `STAGED_IMPORT_PENDING` | discovery run job `error` | no longer raised since M3f-combined-corpus (staged exports are combined with the run's works at the accept); kept registered for older clients. Before: database exports were staged and the search run built no snapshot (M3a, typed on the job in M3b-api) |
| `PROVIDER_RATE_LIMITED` | search leg `error_code` | the database answered 429; a leg field, never an HTTP status (E5, M3b-api) |
| `PROVIDER_TIMEOUT` | search leg `error_code` | the database did not answer in time; a leg field (E5, M3b-api) |
| `PROVIDER_UNAVAILABLE` | search leg `error_code` | a 5xx answer or no answer at all; a leg field (E5, M3b-api) |
| `PROVIDER_REFUSED` | search leg `error_code` | any other 4xx answer; a leg field (E5, M3b-api) |
| `IMPORT_NO_TITLE` | staged source `rejected[].code` | a record without a title; not imported; a row field, never an HTTP status (E3, M3d-engine) |
| `IMPORT_BAD_TAG` | staged source `rejected[].code` | a line that is neither a tag nor a continuation; a row field (E3, M3d-engine) |
| `IMPORT_BAD_YEAR` | staged source `rejected[].code` | a year tag without a four-digit year; the record is imported without a year; a row field (E3, M3d-engine) |
| `DEDUP_NOT_RUN` | `GET /discovery/dedup` | HTTP 404: no deduplication has run in this workspace (E4a, M3d-engine) |
| `PROTOCOL_CHANGED_SINCE_RUN` | `POST /corpus/accept` (discovery hand-off) | HTTP 409: the newest search run's query, year window, language, retrieval cap or database list differs from what `protocol.json` compiles to now; search again before accepting (M3d-engine; widened by review F3) |
| `PREPARATION_UNFINISHED` | `POST /corpus/accept` (discovery hand-off) | HTTP 409: the stages after the newest published search run's search (deduplication, abstracts, verification) have not ended, so `literature/verified.json` is missing or is an earlier run's and nothing is frozen; `details` gives `run`, `state` (`failed`, `stopped` or `interrupted`; a preparation still running reads `interrupted` here) and `stage`. Checked before `NOTHING_STAGED`, and only when no export is staged. A run without a stage marker (made before M3i) is not refused when a `verified.json` exists; without one it is refused as `interrupted` with `stage: null` (M3i-harvest-robustness) |
| `PREPARATION_NOT_AVAILABLE` | `POST /discovery/runs/{run}/prepare` | HTTP 409: the run has nothing to finish; `details.reason` is `not_published` (its search was stopped or failed), `superseded` (a later run is the corpus), `already_prepared` or `records_missing` (its `raw.json` cannot be read) (M3i-harvest-robustness) |
| `DRAFT_TOO_LARGE` | `/inception/*` | HTTP 422: the draft is over its size limits (2 000 characters per free-text answer, 200 per name, 20 research questions, 50 concepts with 50 synonyms each, 50 items per list, 500 criterion decisions, 25 seeds); `message` names each field over its limit, `details.limits` the limits; nothing is saved (H-input-limits, F6) |
| `IMPORT_SOURCE_NOT_FOUND` | `POST /inception/drafts/import` | HTTP 404: the source workspace or its `protocol.json` does not exist; `details.slug` (M10b, start from a protocol) |
| `IMPORT_SOURCE_UNREADABLE` | `POST /inception/drafts/import` | HTTP 422: the source cannot be read: not base64, not UTF-8, not JSON, or not a JSON object; `details.reason` (M10b) |
| `IMPORT_SOURCE_TOO_LARGE` | `POST /inception/drafts/import` | HTTP 413: a picked file over 1 MiB decoded; `details.max_bytes`, `details.got_bytes` (M10b) |
| `IMPORT_NOT_A_PROTOCOL` | `POST /inception/drafts/import` | HTTP 422: a JSON object that is neither a protocol (`epistemology`, `search_strategy`, `screening_criteria`) nor an intent (`inclusion_criteria`, `research_questions`); `details.missing` (M10b) |
| `IMPORT_PROTOCOL_VERSION_UNSUPPORTED` | `POST /inception/drafts/import` | HTTP 422: `$schema` is present and is not `schemas/v1/protocol.schema.json`; nothing is guessed; `details.found`, `details.supported` (M10b) |
| `IMPORT_SOURCE_CHANGED` | `POST /inception/drafts/import` (creating) | HTTP 409: the source's fingerprint is not the `expect_fingerprint` the report showed; no draft is created; `details.expected`, `details.found` (M10b) |
| `PROPOSAL_NOT_FOUND` | `POST /inception/drafts/{id}/proposals/{pid}/…` | HTTP 404: no proposal with that id on this draft; `details.proposal_id` (M10b, proposals) |
| `PROPOSAL_STALE` | `POST /inception/drafts/{id}/proposals/{pid}/apply`, `…/apply-edited` | HTTP 409: the target field changed since the proposal was made; nothing is written; `details.base`, `details.current` (M10b) |
| `PROPOSAL_NOT_OPEN` | `POST /inception/drafts/{id}/proposals/{pid}/…` | HTTP 409: apply, apply-edited or reject of a proposal that is not open, restore of one that is not rejected, or an `add` whose value is already there; `details.status` (M10b) |
| `PROPOSAL_TARGET_UNSUPPORTED` | `POST /inception/drafts/{id}/proposals/{pid}/…` | HTTP 422: the target is not a draft field or the `op` does not fit it; `details.field`, `details.op` (M10b) |
| `PROPOSAL_SOURCE_REFUSED` | proposal creation (engine) | HTTP 422: a source other than `check:*` or `import:*` (`agent:*` only through the assistant's MCP tools, M10c); `details.source` (M10b) |
| `PROTOCOL_AMENDMENT_REFUSED` | workspace proposal apply (Plan) | HTTP 422: applying it would change the protocol outside its search fields (`details.reason: "outside_search"`, `details.paths`), or the amended intent does not compile (`"invalid"`, `details.errors`) (M10c) |
| `CHECK_NOT_FOUND` | `/inception/drafts/{id}/checks…`, `/discovery/checks…` dismiss, restore | HTTP 404: the check id is not in the catalogue, or no instance has this `subject` now; `details.check_id`, `details.subject` (M10b, checks) |
| `CHECK_NOT_DISMISSIBLE` | `/inception/drafts/{id}/checks…`, `/discovery/checks…` dismiss | HTTP 409: a `blocker`, or a warning answered by a confirmation in the gate; `details.level`, `details.refusal` (M10b) |
| `CHECK_REASON_REQUIRED` | `/inception/drafts/{id}/checks…`, `/discovery/checks…` dismiss | HTTP 422: a warning dismissed with an empty reason, or a reason over the draft text limit; `details.limit`, `details.level` (M10b) |
| `CHECK_CHANGED` | `/inception/drafts/{id}/checks…`, `/discovery/checks…` dismiss | HTTP 409: the instance's `evidence_digest` is not the one sent (the data changed); nothing is dismissed; `details.current` (M10b) |
| `CHECK_NOT_DISMISSED` | `/inception/drafts/{id}/checks…`, `/discovery/checks…` restore | HTTP 409: restore of an instance that is not dismissed; `details.status` (M10b) |
| `PAPER_UNKNOWN` | `/inception/drafts/{id}/recon/sample` | HTTP 422: a key to leave out that is not a paper of the current sample, or a key to put back that is neither left out nor in the pool; nothing is changed; `details.keys` (M10b Part C) |
| `SAMPLE_EXCLUSIONS_FULL` | `/inception/drafts/{id}/recon/sample` | HTTP 422: the draft would hold more than 200 left-out papers; nothing is changed; `details.limit` (M10b Part C) |
| `BODY_INVALID` | every route | HTTP 422: a body, query or path parameter pydantic refuses (wrong type, unknown field, a discovery note over 2 000 characters); `details.errors[]` gives `loc`, `msg` and `type`, never the client's value (H-input-limits, F5) |
| `SCREENING_NOT_PUBLISHED` | `POST /discovery/chase/runs`, `POST /discovery/chase/accept` | HTTP 409: the screening of this workspace is not published and current (`literature/included.json` missing, or the generation is not `CURRENT`); the chase's seeds are the published includes (M3g-citation-chasing) |
| `CHASE_NOT_RUN` | `POST /discovery/chase/accept`, `GET /discovery/chase/runs/{chase}` | HTTP 409 (404 on the read): no published chase run to send, or the named run does not exist or was not published (failed or cancelled) (M3g) |
| `CHASE_NOTHING_NEW` | `POST /discovery/chase/accept` | HTTP 409: the chase run found nothing new to the corpus inside the year window; there is no round to start (M3g) |
| `CHASE_ALREADY_ACCEPTED` | `POST /discovery/chase/accept` | HTTP 409: this chase run was already sent to screening; `message` names the round (M3g) |
| `CHASE_STALE` | `POST /discovery/chase/accept` | HTTP 409: the screening was published again, or a later corpus snapshot was accepted, after this chase ran; run the chase again (M3g) |
| `CHASE_DIRECTION_INVALID` | `POST /discovery/chase/runs` | HTTP 422: a direction other than `forward` or `backward`, or none (M3g) |
| `CHASE_SEEDS_INVALID` | `POST /discovery/chase/runs` | HTTP 422: a seed source other than `included` or `included+unclear` (M3g) |
| `CHASE_ACCEPT_PENDING` | `POST /discovery/chase/runs`, `POST /discovery/chase/accept` | HTTP 409: an earlier chase's accept refused `ARCHIVE_INCOMPLETE` after registering the next round's corpus snapshot. That unscreened snapshot is the newest one, so a new chase would take it as its parent, and another chase's accept would archive the round on its behalf; `message` names the chase that owns it. Finish that accept first (`POST /discovery/chase/accept` with that `chase` again) (M3g deferred P3) |
| `PROTOCOL_CHANGED_SINCE_PUBLISH` | `POST /discovery/chase/accept` | HTTP 409: `protocol.json` differs from the protocol the screening was published under; the includes no longer belong to the current protocol, so screening must be redone and published before a chase is sent (M3g) |
| `RECORD_NOT_KEPT` | `POST /charting/events` (per event), `POST /charting/records/{id}/attachment`, `GET …/attachment` | HTTP 409 (per event: in its result): the study is not in the published kept set (Include or Unclear → full text of any published round), or left it at a later publication; its earlier charting events are kept (M12a Part A) |
| `FULLTEXT_REASON_REQUIRED` | `POST /charting/events` (per event) | Not retrieved or Exclude without its one reason, or the reason Other without words (M12a) |
| `FULLTEXT_REASON_INVALID` | `POST /charting/events` (per event) | a reason that is not one of the options (the four Not retrieved reasons; the protocol's `EXC-n`, `FAILS-INC-n`, or `OTHER`), or a reason on a status or outcome that takes none (M12a) |
| `ATTACHMENT_NOT_PDF` | `POST /charting/records/{id}/attachment` | HTTP 422: the body has no `%PDF-` header in its first 1 024 bytes; nothing is stored (M12a) |
| `ATTACHMENT_TOO_LARGE` | `POST /charting/records/{id}/attachment` | HTTP 413: the body (or its declared length) is over 100 MB; nothing is stored (M12a) |
| `ATTACHMENT_MISSING` | `GET /charting/records/{id}/attachment` | HTTP 404: no PDF is attached to this record now (M12a) |
| `LINK_INVALID` | `POST /charting/records/{id}/attachment` (JSON), `POST /charting/events` (per event, kind `link`) | HTTP 422: a link that is not one http or https address (M12a) |
| `CHARTING_EXPORT_FORMAT_INVALID` | `GET /charting/export` | HTTP 422: a format or view the table does not export (Part A: `format=csv&view=fulltext`) (M12a) |
| `CHARTING_PROTOCOL_REPLACED` | every charting write | HTTP 409: `protocol.json` differs from the protocol the newest published round was screened under; the table is read-only (M12a) |
| `CHARTING_VALUE_INVALID` | `POST /charting/events` (per event, kind `cell`) | a cell value that does not fit its column: text empty or over 5 000 characters, a number that is not a finite number, a value not among the options, a "several" list empty or with a value not among the options (M12a Part B) |
| `CHARTING_COLUMN_UNKNOWN` | `POST /charting/events` (per event, kind `cell`) | a cell for a column that is not in the charting form, or before the form exists (M12a Part B) |
| `CHARTING_AMENDMENT_REASON_REQUIRED` | `PUT /charting/form` | HTTP 422: a form change after any cell holds a value, sent without its one-sentence reason; nothing is changed (M12a Part B) |
| `CHARTING_FORM_STALE` | `PUT /charting/form`, `POST /charting/form/pilot/end` | HTTP 409: the change was made from a form version that is no longer current; `details.version` names the current one (M12a Part B) |
| `STALE_BINDING` (inception) | preview with `session_id`, genesis | HTTP 409: the draft's direction was chosen on a pool that is no longer its recon session's latest (M4c), or the draft's question, years or languages changed after it was chosen (`details.code: SCOPE_CHANGED`, `details.changes`; M4d); choose it again. The code predates M4c and is listed in the console set. |
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

1. **Approval code:** a fresh one-time code is issued for each batch generation; the pairing code is never reused for approval. (H-run-small-fixes Part A keeps this: `begin-all` issues one fresh code per batch and only shows them together; a code that covers several batches would change this decision and was not built.) Approval is refused while any paired phone still holds queued events (`APPROVAL_MISSING`, detail `queued_events`).
2. **Event-file locking:** every append takes an exclusive OS file lock on `events/<screener_id>.jsonl` (Windows and Unix), so the CLI and the console can write at the same time without lost or interleaved lines (CON-19).
3. **`criteria` on a phone swipe:** an Exclude requires a `reason_code`; an Include or Unclear requires nothing more. The checklist stays optional on the phone and is captured on desktop.
4. **Batch size limit:** 200 events per request. The UI splits a larger offline backlog into chunks of 200 and retries each on its own; `event_id` makes replays harmless.
5. **Methods paragraph wording (PRISMA 2020 item 8):** deferred to M5-slim, with the default and minimum sample-audit size. Specs 02 and 07 keep a placeholder until then.
6. **Cost display:** a dated price table in the tasks folder, updated each release; the UI shows its "prices as of" date next to the estimate. No network call for prices.
