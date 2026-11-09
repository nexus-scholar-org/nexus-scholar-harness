# Inception API (M4a)

Status: **IN USE** (engine M4a, 2026-11-08; screens M4b, 2026-11-09, specs `docs/ux/phase0-inception/final/`). The browser surface (`console/browser.py` and the Next proxy) carries GET, POST to drafts, steps, preview and genesis, and PUT on a draft; it does not carry DELETE, so the browser cannot discard a draft. Decisions: [2026-11-08 re-inception, criteria acceptance, inception drafts](../decisions.md). Conventions follow [`workspaces-api.md`](workspaces-api.md): JSON over `/api/v1`, refusals as `{"detail": {"code", "message", "details"?}}`, desktop only (not in `_PHONE_ROUTES`). Every route answers with or without an open workspace (`_workspace_free` in `console/serve.py`).

Code: routes in `src/scholar_harness/console/api/inception.py`; steps, preview and genesis in `src/scholar_harness/inception/steps.py`; drafts in `inception/drafts.py`; the gate in `inception/emit.py`.

## Draft

A draft holds every interview answer. All fields are optional until preview, and unknown keys are refused (`DRAFT_INVALID`):

`topic`, `paradigm`, `playbook`, `secondary_paradigm`, `unit_of_analysis`, `proof`, `out_of_scope[]`, `languages[]` (default `["en"]`, as the wizard), `start_year`, `end_year`, `rqs[]`, `concepts[{concept, synonyms[]}]`, `extra_inclusions[]`, `extra_exclusions[{criterion, reason_category}]`, `criteria_decisions{criterion id: bool}`, `matrix_columns[]`, `verification_checks` (default true), `title`, `lead_researcher`, `venue`, `timeline_weeks`.

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
| `POST /api/v1/inception/preview` | compile-preview (screen 06) | `{draft}` → `{intent, protocol, protocol_fingerprint, screening_criteria, criteria, files, written: [], target: {slug, path, exists, workspace, screening}}`. Writes nothing. `workspace` says the folder holds a workspace (an init marker), which is what genesis decides on; `exists` alone may be a folder that is not one. The fingerprint is a preview: genesis stamps its own `genesis_timestamp`, so the written protocol's fingerprint differs. `files` names every file genesis would write: a new workspace's files and support files, or, when the target holds a workspace, what a replacement rewrites plus `audit/replaced/<UTC stamp>/` (M4b). `422 CRITERIA_UNDECIDED`, `CRITERIA_MISSING`, `INTENT_INVALID` |
| `POST /api/v1/inception/drafts/{id}/genesis` | the only write (screen 06) | `{replace?, confirm_discard_screening_binding?}` → `201 {session_id, slug, path, protocol_fingerprint, replaced, previous_fingerprint?, backup_dir?}`. Creates `<root>/<slug>` through `emit_workspace`. The draft's `emitted` keeps `slug`, `path`, `protocol_fingerprint`, `replaced` and, for a replacement, `previous_fingerprint` and `backup_dir` (M4b). Refusals: `409 WORKSPACE_EXISTS` (no `replace`), `409 SCREENING_BOUND` (with counts), `422 CONFIRMATION_MISMATCH` (the typed slug is wrong), `409 DRAFT_EMITTED`. A new workspace that fails part-way is removed |

### Steps

- **`scope`** gives `leanings`, `recommended_paradigm`, `paradigms`, `refraction` and `default_concepts`.
- **`shape`** gives `recommended_playbook`, `playbooks`, `trustworthiness_framework`, `rq_draft`, `lexicon` and `lexicon_warnings`.
- **`criteria`** gives `criteria`, `undecided` and `missing_sides`.
  - Each criterion has `id`, `kind`, `criterion` (verbatim), `reason_category`, `source`, `source_label`, `generated` and `status`.
  - `status` is `accepted`, `rejected` or `undecided`. A criterion the wizard wrote stays `undecided` until it has a decision. A criterion the researcher typed is accepted unless rejected (INC-22).
- **`matrix`** gives `columns` and `selected`.

The same answers give the same intent and fingerprint through the CLI wizard and through preview (`test_preview_and_the_cli_wizard_compile_the_same_protocol`).

## Not here yet

- **Recon over HTTP** (probe, distill, delta) and grounded drafts are held until M3a merges.
- **A multi-workspace server.** Genesis creates a workspace; opening it is still `POST /workspaces/open`.
