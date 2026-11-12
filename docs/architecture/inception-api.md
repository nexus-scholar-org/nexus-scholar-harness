# Inception API (M4a, recon M4c, grounding M4d)

Status: **IN USE** (engine M4a, PR #206, 2026-11-08; screens M4b, PR #209, 2026-11-09; recon M4c, PR #210, 2026-11-09; specs `docs/ux/phase0-inception/final/`). The browser surface (`console/browser.py` and the Next proxy) carries GET, POST to drafts, steps, preview, genesis and the recon `probe`, `delta`, `distill` and `bind`, and PUT on a draft; it does not carry DELETE, so the browser cannot discard a draft. Decisions: [2026-11-08 re-inception, criteria acceptance, inception drafts](../decisions.md). Conventions follow [`workspaces-api.md`](workspaces-api.md): JSON over `/api/v1`, refusals as `{"detail": {"code", "message", "details"?}}`, desktop only (not in `_PHONE_ROUTES`). Every route answers with or without an open workspace (`_workspace_free` in `console/serve.py`).

Code: routes in `src/scholar_harness/console/api/inception.py`; steps, preview and genesis in `src/scholar_harness/inception/steps.py`; drafts in `inception/drafts.py`; the gate in `inception/emit.py`.

## Draft

A draft holds every interview answer. All fields are optional until preview, and unknown keys are refused (`DRAFT_INVALID`):

`topic`, `paradigm`, `playbook`, `secondary_paradigm`, `unit_of_analysis`, `proof`, `out_of_scope[]`, `languages[]` (default `["en"]`, as the wizard), `start_year`, `end_year`, `rqs[]`, `concepts[{concept, synonyms[]}]`, `extra_inclusions[]`, `extra_exclusions[{criterion, reason_category}]`, `criteria_decisions{criterion id: bool}`, `matrix_columns[]`, `verification_checks` (default true), `golden_seeds[]` (M4d: DOIs kept as recall seeds, at most 25 (else `DRAFT_TOO_LARGE`), normalised and checked as DOIs (else `DRAFT_INVALID`); compiled into `search_strategy.golden_seeds`), `title`, `lead_researcher`, `venue`, `timeline_weeks`.

A criterion id is derived from the criterion's kind, source and text (`crit_` plus 12 hex characters). Editing the text makes a new criterion, which has no decision yet.

## Routes

| Route | Purpose | Request → response |
| :-- | :-- | :-- |
| `GET /api/v1/inception/drafts` | list drafts (screen 08, resume) | → `{root, items: [{session_id, readable, title, topic, created_at, updated_at, emitted}]}`, newest first. An unreadable draft is listed with `readable: false` |
| `POST /api/v1/inception/drafts` | start a draft (screen 00) | `{draft}` → `201 {session_id, created_at, updated_at, draft, emitted: null}`. The id is `rec_` plus 32 hex characters |
| `GET /api/v1/inception/drafts/{id}` | resume | → the record; `404 DRAFT_NOT_FOUND`, `422 DRAFT_ID_INVALID` |
| `PUT /api/v1/inception/drafts/{id}` | save | `{draft, base_updated_at?}` → the record. `409 DRAFT_CONFLICT` when `base_updated_at` is not the stored one; `409 DRAFT_EMITTED` once the draft has created a workspace |
| `DELETE /api/v1/inception/drafts/{id}` | discard | → `204` |
| `POST /api/v1/inception/steps/{scope\|shape\|criteria\|matrix}` | what the wizard proposes at that step (screens 01–05) | `{draft}` → step output; stores nothing. `422 DRAFT_INCOMPLETE` names the `missing` fields |
| `POST /api/v1/inception/preview` | compile-preview (screen 06) | `{draft}` → `{intent, protocol, protocol_fingerprint, screening_criteria, criteria, files, written: [], target: {slug, path, exists, workspace, screening, archive}}`. Writes nothing. `archive` (M4d, F1) lists what a replacement would move into `audit/replaced/<stamp>/` beside the old protocol: `literature/`, `artifacts/`, `audit/artifact_registry.json`, `.harness-console/`, `pdfs/`, `extracted/`, `rag/`, `phase4/`, `synthesis/` (without `literature_review.md`), `chroma_db/`, `run-reports/`, each only when it holds a file. `workspace` says the folder holds a workspace (an init marker), which is what genesis decides on; `exists` alone may be a folder that is not one. The fingerprint is a preview: genesis stamps its own `genesis_timestamp`, so the written protocol's fingerprint differs. `files` names every file genesis would write: a new workspace's files and support files, or, when the target holds a workspace, what a replacement rewrites plus `audit/replaced/<UTC stamp>/` (M4b). `422 CRITERIA_UNDECIDED`, `CRITERIA_MISSING`, `INTENT_INVALID` |
| `POST /api/v1/inception/drafts/{id}/genesis` | the only write (screen 06) | `{replace?, confirm_discard_screening_binding?}` → `201 {session_id, slug, path, protocol_fingerprint, replaced, previous_fingerprint?, backup_dir?, archived}`. A replacement moves the old corpus beside the old protocol (`archived`, M4d, F1), so the new protocol starts with no corpus and no screening decisions; the `GENESIS` event names what moved. Creates `<root>/<slug>` through `emit_workspace`. The draft's `emitted` keeps `slug`, `path`, `protocol_fingerprint`, `replaced` and, for a replacement, `previous_fingerprint` and `backup_dir` (M4b). Refusals: `409 WORKSPACE_EXISTS` (no `replace`), `409 SCREENING_BOUND` (with counts), `422 CONFIRMATION_MISMATCH` (the typed slug is wrong), `409 DRAFT_EMITTED`, `409 WORKSPACE_JOB_ACTIVE` (a discovery or console job of this process is still running in the workspace; nothing moved, M4d), `409 ARCHIVE_INCOMPLETE` (a move failed part way; `details {backup_dir, moved, not_moved}`, a `PROTOCOL_REPLACE_INCOMPLETE` journal event says the same, and the protocol was not replaced, M4d), `409 STALE_BINDING`. A new workspace that fails part-way is removed |

### Steps

- **`scope`** gives `leanings`, `recommended_paradigm`, `paradigms`, `refraction` and `default_concepts`.
- **`shape`** gives `recommended_playbook`, `playbooks`, `trustworthiness_framework`, `rq_draft`, `lexicon` and `lexicon_warnings`.
- **`criteria`** gives `criteria`, `undecided` and `missing_sides`.
  - Each criterion has `id`, `kind`, `criterion` (verbatim), `reason_category`, `source`, `source_label`, `generated` and `status`.
  - `status` is `accepted`, `rejected` or `undecided`. A criterion the wizard wrote stays `undecided` until it has a decision. A criterion the researcher typed is accepted unless rejected (INC-22).
- **`matrix`** gives `columns` and `selected`.

The same answers give the same intent and fingerprint through the CLI wizard and through preview (`test_preview_and_the_cli_wizard_compile_the_same_protocol`).

## Recon (M4c)

Code: `src/scholar_harness/console/api/recon.py` (routes), `recon/session.py` (the recon session store the CLI wizard, the MCP `recon_*` tools and these routes share), `inception/grounding.py` (binding and `STALE_BINDING`). The draft's id is its recon session id. The probe runs the M3a providers through `ReconEngine` (`SearchEngine.run`); the contact address is the console process's `SCHOLAR_MAILTO` (environment or `.env`), with no default. Decision: [2026-11-09, Recon over HTTP](../decisions.md).

| Route | Purpose | Request → response |
| :-- | :-- | :-- |
| `GET .../drafts/{id}/recon` | the session (screens 02, 03) | → `{session_id, mailto_set, keys: {openalex_key_set, s2_key_set}, topic_changed, scope_changed, scope_changes[], session: {topic, latest, probes[], narrower_left} \| null, grounding \| null, binding: {stale, code?, reason?, changes?, bound, current} \| null, active_job}`. `keys` (M4d) say whether OpenAlex and Semantic Scholar have their keys, as `GET /discovery/plan` does. `scope_changed` and `scope_changes` (subset of `topic`, `years`, `languages`, M4d) compare the saved draft with the latest pool. `binding.code` is `POOL_CHANGED` or `SCOPE_CHANGED` (with `changes`). Each probe has `purpose` (`topic`, `narrower`, `concept`, `delta`), `query`, `pool_path`, `fingerprint` (`sha256:` of the pool's canonical JSON), `created_at`, `status` (`complete`, `partial`, `empty`), `n_docs`, `served_from_cache`, `year_min`, `year_max`, `languages` (M4d) and one leg per provider (`provider`, `status`, `reported_total`, `fetched`, `cap`, `cap_hit`, `error`, and since M4d `error_code`, `notes[]` and `key_set`: true or false for OpenAlex and Semantic Scholar, null for a database without keys) |
| `POST .../recon/probe` | first search, refresh, or the narrower search | `{refresh?, semantic?, narrower?}` → `202 {job}`. The topic, years and languages (M4d) come from the saved draft; the languages are recorded in the pool and its cache key, and no database filters by them yet (each leg notes it). `narrower` is a direction label of the current pool (one per draft). Refusals before the job: `409 MAILTO_NOT_SET` (no request sent), `422 DRAFT_INCOMPLETE` (no topic), `409 NARROW_BUDGET_SPENT`, `422 DIRECTION_UNKNOWN`, `409 RECON_JOB_ACTIVE`. The job fails with `POOL_EMPTY` or `PROVIDERS_FAILED` (`details.legs`) |
| `POST .../recon/delta` | the gap check (screen 03) | `{followups?: 0..3}` → `202 {job}`; the result lists each follow-up with `corpus_total` and `saturation_label` |
| `GET .../recon/jobs/{job_id}` | a job (the last 10 finished jobs of a draft are kept) | → `{job: {job_id, kind, state: running\|succeeded\|failed, result, error: {code, message, details?}}}`; `404 RECON_JOB_NOT_FOUND` |
| `GET .../recon/jobs/{job_id}/events` | its stream | SSE: `snapshot`, then `leg` `{provider, fetched}` while live providers page, then `done` or `failed` with the job. The stream ends with the job |
| `POST .../recon/distill` | Explore (screen 02) | → `{pool, gates: {pool: {n_docs, sufficient, threshold}, purity: {label, top3_share, ...}}, qei, schools, topics, metrics, datasets, micro_taxonomy_top, papers[{doi, title, year, provider, directions_anchored}], terms_path}` |
| `GET .../recon/directions` | Direction (screen 03) | → `{pool, gates, directions: [{label, concept, anchor_dois, observed_in, n_docs, schools, detail}], narrower_left}`: at most three, each with at least 2 anchor papers |
| `GET .../recon/concepts` | per-concept anchoring and pool synonyms (screens 02, 05; M4d) | → `{session_id, fingerprint, n_docs, concepts: [{concept, source: draft\|suggested, terms: [{term, observed_in, anchor_dois}], anchored_in, suggestions: [{term, observed_in}]}]}`. `suggested` concepts are the scope step's words when the draft has none. A suggestion occurs in at least 2 of the records anchoring the concept, is not a term of any concept nor a piece or an extension of one; at most 10, most frequent first. Only records with a DOI count, as for every anchor. `404 RECON_SESSION_NOT_FOUND`, `409 RECON_NO_POOL` |
| `GET .../recon/evidence?term=` | does a phrase occur in the pool (screen 03, own direction; M4d) | → `{term, hits, observed_in, anchor_dois, n_docs}`. Reads only. `422 TERM_EMPTY` |
| `GET .../recon/seeds` | papers to keep as recall seeds (screen 03; M4d) | → `{session_id, fingerprint, papers: [{doi, title, year, provider, anchors: {directions[], concepts[]}}]}`: pool records with a DOI that anchor a direction or a concept, most anchors first. Kept ones are saved in the draft's `golden_seeds` |
| `POST .../recon/bind` | choose a direction into the draft | `{direction \| own \| skip: true, accept_thin_pool?, base_updated_at?}` → the draft record with `grounding`. `skip` (M4d) records going on without a direction: `choice: "none"`, `direction.source: "none"`, `grounded: false`, no anchors, no pool floor. `409 POOL_TOO_SMALL` under 12 papers without `accept_thin_pool`; `422 DIRECTION_UNKNOWN`, `422 NO_DIRECTION`, `409 DRAFT_CONFLICT`, `409 DRAFT_EMITTED` |

**Pools (INC-09).** Only a `complete` pool is cached and reused. A gap check makes a new pool: it carries the original's and each follow-up's legs (with their `query`), its own `created_at`, `merged_from`, and is `partial` when any follow-up leg failed. A `partial` pool (a leg failed) is usable and says which provider failed, but it is never reused. An `empty` pool is recorded as a probe and never becomes the session's pool. `refresh` probes again.

**Anchors (INC-21).** A paper anchors a term only when the term occurs, as whole words, in its title or abstract. Evidence keeps `hits` (records the providers returned) apart from `observed_in`.

**Grounding.**
- `bind` writes `grounding` beside `draft` on the record:
  - `session_id` and `bound_at`;
  - `pool {fingerprint, created_at, cache_key, path, status, query, n_docs, legs}`;
  - `direction {label, concept, anchor_dois, observed_in, source: pool|researcher, grounded}`;
  - `anchors`, `default_concepts`, `anchored_terms` and `term_evidence`;
  - since M4d, `choice` (`pool`, `researcher` or `none`) and `scope {topic, year_min, year_max, languages}`, the draft's scope at bind time.
- `PUT` of the draft keeps it.
- `POST /preview` with `session_id` adds `grounding {pool, direction, anchors, rq_evidence[{rq, terms, anchor_dois}], concept_evidence, apr_observed}`, and lists `audit/recon_context.json` in `files`.
- Genesis writes that file and the GENESIS journal summary, with `pool_created_at`.
- Preview and genesis refuse `409 STALE_BINDING` when the session's latest pool is no longer the bound one, or when the pool file changed. A refresh, a narrower search or a gap check after binding makes the bound pool no longer the latest. Since M4d they also refuse when the draft's question, years or languages differ from the recorded `scope` (`details.code: SCOPE_CHANGED`, `changes`); a grounding bound before M4d has no `scope` and is compared on its pool only.
- A draft without `grounding` answers as in M4b.

## Not here yet

- **The gap check in the browser.** `POST .../recon/delta` is not used by the screens (spec 03, researcher 2026-11-11); it stays for MCP.
- **A language filter.** The probe records the languages; no database filters by them.
- **A custom lexicon over HTTP.** The MCP `recon_distill` takes `lexicon_json`.
- **A multi-workspace server.** Genesis creates a workspace; opening it is still `POST /workspaces/open`.

## Known issues (three-phase review, 2026-11-10)

From [`three-phase-hardening-2026-11-10.md`](../assessment/three-phase-hardening-2026-11-10.md); not fixed on `main` unless marked:

- **F1 (P1).** Fixed in M4d: a replacement archives the old corpus beside the old protocol (decision 2026-11-11).
- **F6 (P2).** Fixed in H-input-limits: the draft shape (`inception/steps.py`, `DRAFT_LIMITS`) caps every text, name and list; a draft over a limit is refused `DRAFT_TOO_LARGE` on every route that parses one (decision 2026-11-12).
- **F5 (P2).** Fixed in H-input-limits: `console/serve.py` answers every pydantic refusal as 422 `BODY_INVALID` in the envelope above, with `details.errors[]` and without the client's value (decision 2026-11-12).
