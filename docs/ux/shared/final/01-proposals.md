# 01 Proposals    Status: FINAL, not built (questions closed by the researcher 2026-11-15) | Shared pattern (Phase 0 Inception and Phase 1 Discovery) | No route of its own: a card and a per-step list mounted on the draft screens (`/[locale]/inception/*?draft=rec_<32 hex>`) and, for workspace targets, on the Discovery screens | Milestone M10b (store, API, card, list); M10c adds the agent source

Boards: none. The proposal card reuses the draft styling of `docs/ux/phase0-inception/final/01-scope.md` "Shared by 01, 04, 05, 06 and 07" (item 5) and the Accept / Edit / Drop row of `docs/ux/phase0-inception/final/05-criteria.md`; it draws no new component. Contract: `docs/roadmap/milestones/M10b-proposals-checks.md` "One proposal object" (normative; this spec details it and does not change it). Typed models: none yet (new, ✗ M10b). Refusal naming follows `docs/architecture/refusals.md` (see "Refusal codes" for why the new codes are not Envelope codes).

**Purpose.** Show the researcher, one card at a time, a change the engine suggests to the draft or the protocol, with the reason and the evidence, and let them apply it, edit it then apply it, or reject it, with every decision recorded.

**Changed from the canvas.** There is no canvas for this pattern. What it changes in existing specs:
- **One card for every suggestion.** Inception 01 (item 5), 04 and 05 each describe their own draft card. This spec is the single definition; those specs keep their fields (see "The six mechanisms that exist today") and adopt the card in the build.
- **Edit is allowed on every card.** In 05 a wizard-written criterion has Accept and Drop only, because it has no text field. A stored proposal always carries a `value`, so Edit exists on every proposal card (it opens the field's normal editor). The six existing mechanisms keep their current actions until they adopt the card; where a mechanism has no editable value (a wizard criterion), its card shows Apply and Reject only and says why.
- **Words.** 05 uses Accept / Drop for criteria. The card uses Apply / Edit / Reject for every proposal, and a criterion card keeps "Accept" and "Drop" as its own labels (`inception.criteria.act.*`); the engine's meaning is the same.
- **Stale is a state of the card.** 01-scope names `DRAFT_CONFLICT` for a draft that changed in another tab. A proposal can go out of date without the draft conflicting (the researcher edited the same field in this tab); the card handles that itself.
- **No language model in M10b.** The sources are `check:<id>` (the only one that creates an open proposal in M10b), `import:<name>` (accepted by the store, created by nothing yet), plus `engine:<mechanism>` for the write-only record of an accepted suggestion from one of the six mechanisms that exist today (decided 2026-11-15, see "The six mechanisms that exist today"). The `agent:<model>` source is reserved for M10c and is refused here (`PROPOSAL_SOURCE_REFUSED`); the in-app chat (M10e) is reserved too.

## Entry / exit
- Entry: the per-step list is mounted on inception 01 to 06 and shows only the proposals whose target belongs to that step (map below). A check's "recommended action" on `02-checks` links to the card. An imported protocol (`09-start-from-protocol`) creates no proposal in M10b: it prefills a new draft with the researcher's own earlier answers. The `import:<name>` source is kept for the later case of importing into a draft that already has answers.
- Exit: none. The list never navigates. Apply, Edit and Reject change the page's draft state and stay on the screen; the screen's own Continue still decides when to leave.
- Gate: no proposal is ever a gate. Open proposals do not disable Continue and are not counted as accepted anything. The Review step's readiness list (02-checks) may mention open proposals as a `note`, never a `blocker`.

## Data in
| Field | Source |
| :-- | :-- |
| the proposal `{proposal_id, target{kind (draft|workspace), id, field}, op, value, why, evidence[], source, base, status, decided_at, step}` | `GET /api/v1/inception/drafts/{id}/proposals` ✗ M10b |
| per-step counts `{by_step{scope, explore, direction, shape, criteria, review: {open, stale}}}` (stepper badges; one read for the whole stepper) | same response |
| the current value of the target (to show "now" beside "proposed" and to compute stale) | `GET /api/v1/inception/drafts/{id}` ✓ M4a `console/api/inception.py:99` (the record; `draft` holds the fields) |
| workspace-targeted proposals (after genesis) | `GET /api/v1/workspaces/{slug}/proposals` ✗ M10b (shape as above; `target.kind = "workspace"`) |

The proposal object (fields are the milestone's, with the exact meanings fixed here):

| Field | Meaning in the engine |
| :-- | :-- |
| `proposal_id` | `prop_` plus the first 12 hex digits of a sha256 over `(source, target, op, value, base_hash)`. Content-derived like `crit_` ids (`intent.py:265`): the same check on the same unchanged draft proposes the same id, so a re-run never duplicates and a rejection is remembered; if the target changed, the id changes. |
| `target` | `{kind: "draft"\|"workspace", id: "rec_…"\|"<slug>", field}`. `field` is one of the `Draft` fields (`steps.py:149`: `topic`, `start_year`, `end_year`, `languages`, `paradigm`, `playbook`, `unit_of_analysis`, `proof`, `rqs`, `concepts`, `extra_inclusions`, `extra_exclusions`, `out_of_scope`, `matrix_columns`, `golden_seeds`, …) or `concepts[<concept>].synonyms` (concept matched by name). A field that is not in `Draft` is refused `PROPOSAL_TARGET_UNSUPPORTED`. A workspace field is named by the screen that owns it (discovery spec); none is defined by this spec. |
| `op` | `add` appends one element to a list field (a no-op refused `PROPOSAL_NOT_OPEN` if it is already there); `remove` removes the equal element; `replace` sets a scalar field or a whole list. A scalar field accepts only `replace`. |
| `value` | exactly what would be written: one element for `add` and `remove`, the whole new value for `replace`. |
| `why` | one sentence, plain words, shown on the card. |
| `evidence[]` | `{kind: "doi"\|"count"\|"check"\|"file", …}`; DOIs link to `https://doi.org/{doi}`; counts are numbers with their unit; `check` carries the check id. |
| `source` | `check:<id>`, `import:<name>` or `engine:<mechanism>` in M10b (the last only on a record written by `…/proposals/record`, never on an open card). Shown through the source label (Copy). |
| `base` | `{hash, shown}`: a sha256 of the canonical JSON of the target's value when the proposal was made, and the short text shown as "was". |
| `status` | stored: `open`, `applied`, `applied_edited`, `rejected`. `stale` is **derived on every read** (status `open` and the target's current hash differs from `base.hash`) and never stored; if the researcher puts the old value back, the card is open again. |
| `decided_at`, `decided_value` | when, and the value that was actually written (for `applied_edited`, the researcher's own). |
| `step` | which stepper step lists it. Computed by the engine from `target.field`; the browser never derives it. Map: `scope` = `topic`, `start_year`, `end_year`, `languages`; `explore` = none in M10b; `direction` = `golden_seeds`; `shape` = `paradigm`, `playbook`, `secondary_paradigm`, `unit_of_analysis`, `proof`, `rqs`; `criteria` = `concepts`, `concepts[*].synonyms`, `extra_inclusions`, `extra_exclusions`, `out_of_scope`, `criteria_decisions`, `matrix_columns`, `verification_checks`; `review` = `title`, `lead_researcher`, `venue`, `timeline_weeks`. |

## Where a proposal is kept
- **Before genesis: the draft record.** `<workspaces root>/.drafts/<session id>/draft.json` (`drafts.py:52`, `:55`) gets a new sibling key `proposals: [...]` next to `grounding` and `emitted`. It cannot go inside `draft`: `Draft` is `extra="forbid"` (`steps.py:152`) and a save replaces only `record["draft"]` (`drafts.py:91`), so a sibling key survives every PUT, exactly as `grounding` does (`bind_grounding`, `drafts.py:95`) and `mark_emitted` keeps it (`drafts.py:112`). Every proposal write is one `_write` (temp file then `os.replace`, `drafts.py:57-63`), so a decision and the draft change it causes land together or not at all. It uses the same `base_updated_at` check (`DRAFT_CONFLICT`) and the same `DRAFT_EMITTED` refusal as a draft save. Not verified: whether anything else reads `draft.json` and rejects an unknown top-level key; the code read here does not.
- **From genesis on: the workspace's audit trail.** Two parts (✗ M10b):
  1. `audit/proposals.jsonl`, written by genesis (new file, listed in `NEW_WORKSPACE_FILES` and `REPLACEMENT_FILES`, which `planned_files` returns in the preview's `files`, `steps.py:428`; so the public preview response changes). One JSON line per event: `proposed` (the full object) then, if decided, `applied`, `applied_edited` or `rejected` (id, `decided_at`, `decided_value`). Append-only, never rewritten, like `audit/journal.jsonl` (`workspace/audit.py:178`). Later decisions on workspace-targeted proposals append here.
  2. Journal events in `audit/journal.jsonl` through `append_event` (`audit.py:144`, action uppercased, agent `nexus-scholar/ui` as `UI_AGENT`, `console/api/inception.py:38`): `PROPOSALS_RECORDED` once at genesis (parameters: counts by status and by source; outputs: `audit/proposals.jsonl`), and `PROPOSAL_DECIDED` for each later decision (parameters: `proposal_id`, `target`, `op`, `status`, `source`). The file is the record; the journal is the index. Genesis's own event is `GENESIS`, written best-effort through `log_event.py` (`genesis.py:97-134`, a warning and no row if the skill is unreachable); because that path is best-effort, the proposal record is **not** left to the journal: the file is written with the other genesis files, and the journal row may be missing without losing the record. Not verified: whether `emit_workspace` writes its files atomically as one unit, so whether a failure after `audit/proposals.jsonl` removes it; the build must test this (`emit.py`, not read in full).
- **What the methods text may count.** A decided proposal says what the researcher clicked, not what the protocol holds: an applied value can be edited away later. At genesis the engine therefore writes `in_protocol: true|false` on every `applied` and `applied_edited` line of `audit/proposals.jsonl` (the value, or the researcher's edited value, is in the compiled draft's field or it is not), and `PROPOSALS_RECORDED` counts both. A methods sentence counts only `in_protocol: true` (✗ M10b).
- A replacement genesis (re-inception) archives the old `audit/proposals.jsonl` with the old protocol and starts a new one; open proposals of the old draft are not carried (they are stale by definition).
- Discarding a draft (`DELETE`, `inception.py:116`) removes its proposals with it; the proxy does not carry DELETE and no screen offers it (01-scope), so this is not a researcher path.

## Data out
Writes (all ✗ M10b, all POST, all on the draft record, body always carries `base_updated_at` like a save):
- **Apply**: `POST …/proposals/{proposal_id}/apply` `{base_updated_at}`. The engine builds the new draft by applying `op` and `value` to the current draft, runs `parse_draft` on it (the same validation as `PUT`, `inception.py:110`), then writes the draft and the proposal's `status = applied`, `decided_at` in one `_write`. Response: the new record (`draft`, `updated_at`, `proposals`).
- **Apply edited**: `POST …/proposals/{proposal_id}/apply-edited` `{value, base_updated_at}`. As Apply with the researcher's `value`; `status = applied_edited`, `decided_value = value`. The value goes through the same `parse_draft`.
- **Reject**: `POST …/proposals/{proposal_id}/reject` `{base_updated_at, reason?}`. Only `status` and `decided_at` change; the draft's fields do not. `reason` is optional free text up to the draft's `MAX_TEXT_CHARS` (`steps.py:90`).
- **Restore**: `POST …/proposals/{proposal_id}/restore` `{base_updated_at}`. Only a `rejected` proposal returns to `open`. An applied proposal is not restored: the researcher edits the field (the draft is the truth); the record keeps "applied" and the later edit is just a draft change.
- Journal: none before genesis (a draft is not a workspace, as in 01-scope "Data out"). From genesis on: as in "Where a proposal is kept".
- **Record an accepted engine suggestion**: `POST …/proposals/record` `{mechanism, field, value, base_updated_at}` (✗ M10b). `mechanism` is one of the six names in "The six mechanisms that exist today" (`wizard_criterion`, `pool_synonym`, `suggested_concept`, `matrix_column`, `direction`, `anchor_seed`). The engine checks that this mechanism offers this value for this draft now (the same code the mechanism's read route runs), then writes one decided entry: `source: "engine:<mechanism>"`, `op: "add"` (`replace` for `direction`), `status: "applied"`, `decided_at`, the same content-derived id. It changes no draft field: the mechanism's own save writes the field as today, and the screen sends the record after that save succeeds. A second call for the same value is a no-op (same id). Unticking later writes nothing; "What the methods text may count" covers it. A record is listed under "Decided" with its source label and is never an open card.
- Open proposals are **created** by the engine only, never by the browser: in M10b by a check run (`02-checks`) only. There is no public create route in M10b; M10c adds the MCP route for the agent source.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/inception/drafts/{id}` (the target's current value) | ✓ M4a `console/api/inception.py:99`, `drafts.py:72` |
| `PUT /api/v1/inception/drafts/{id}` (the screen's own save; carries `proposals` through) | ✓ M4a `inception.py:107`, `drafts.py:81` |
| `POST /api/v1/inception/steps/{scope,shape,criteria,matrix}` (the six mechanisms' own reads) | ✓ M4a `inception.py:125`, `steps.py:324` |
| `GET /api/v1/inception/drafts/{id}/recon/concepts`, `…/recon/seeds`, `…/recon/directions` (mechanisms 2, 5, 6) | ✓ M4d `console/api/recon.py:397`, `:427`, `:379` |
| `GET /api/v1/inception/drafts/{id}/proposals` (`?step=`) | ✗ M10b |
| `POST /api/v1/inception/drafts/{id}/proposals/{proposal_id}/apply` | ✗ M10b |
| `POST /api/v1/inception/drafts/{id}/proposals/{proposal_id}/apply-edited` | ✗ M10b |
| `POST /api/v1/inception/drafts/{id}/proposals/{proposal_id}/reject` | ✗ M10b |
| `POST /api/v1/inception/drafts/{id}/proposals/{proposal_id}/restore` | ✗ M10b |
| `POST /api/v1/inception/drafts/{id}/proposals/record` (an accepted suggestion of one of the six mechanisms; write-only) | ✗ M10b |
| `GET /api/v1/workspaces/{slug}/proposals` and the same four POSTs under `/api/v1/workspaces/{slug}/proposals/{proposal_id}/…` (workspace targets, after genesis) | ✗ M10b |
| Proxy allow-list: the four POST routes and `…/proposals/record` must be added to `POST_PATHS` in `src/scholar_harness/console/browser.py:40-61` **and** to the matching list in `apps/research-ui/app/api/console/[...path]/route.ts:71-86`. Both lists are explicit regexes; a path not in them is not carried. GET is not listed there (read at those lines; GET routes need no entry). | ✗ M10b |

Desktop only on the engine, as every inception route: none is in `_PHONE_ROUTES` (`serve.py:55`, per 01-scope; not re-read here), so a phone token gets `TOKEN_SCOPE_REFUSED`. Writes sit under the loopback origin check.

### Refusal codes
`docs/architecture/refusals.md` is the closed set of `Envelope@1` codes for the agent roles. The console's draft codes (`DRAFT_CONFLICT`, `DRAFT_EMITTED`, `DRAFT_INVALID`, … in `drafts.py` and `steps.py`) are **not in it**; they are plain codes on `DraftRefused` and `StepRefused`, returned as `{code, message, details}` (`inception.py:41`). The new codes follow that style and are not added to `refusals.md`; if the researcher wants them registered there, that is a contract decision (Open question 5). New, all ✗ M10b:

| Code | HTTP | When | `details` |
| :-- | :-- | :-- | :-- |
| `PROPOSAL_NOT_FOUND` | 404 | no such id on this draft or workspace | `proposal_id` |
| `PROPOSAL_STALE` | 409 | the target's current hash is not `base.hash` | `base`, `current` (short texts) |
| `PROPOSAL_NOT_OPEN` | 409 | apply, apply-edited or reject on one that is not `open`; restore on one that is not `rejected`; an `add` whose element is already present | `status` |
| `PROPOSAL_TARGET_UNSUPPORTED` | 422 | `target.field` is not a `Draft` field or the `op` does not fit the field | `field`, `op` |
| `PROPOSAL_SOURCE_REFUSED` | 422 | a source other than `check:*` or `import:*` (M10b); `agent:*` until M10c; on `…/record`, a `mechanism` that is not one of the six | `source` |
| `PROPOSAL_NOT_OFFERED` | 409 | `…/record` for a value the named mechanism does not offer for this draft now | `mechanism`, `field` |

An applied value that the draft refuses surfaces as the engine's existing `DRAFT_INVALID` or `DRAFT_TOO_LARGE` (with `details.errors`, `details.limits`, `steps.py:206-213`), not as a new code: Apply must refuse exactly as a manual edit would. `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE`, `DRAFT_CONFLICT`, `DRAFT_EMITTED` are as in 01-scope.

## States
- **Default**: below the screen's fields and above its button row, a card list headed "Suggestions for this step · {n}" (`n` = open count; stale ones counted apart: "{n} out of date"). Each open proposal is a card (Desktop layout). Nothing is pre-ticked, pre-applied or pre-selected; no card has focus on load. The stepper shows a text badge "{n} suggestions" on a step with open proposals (never colour alone).
- **Empty**: no proposals for this step: the list region is not drawn (no "No suggestions" card; less on screen, M10d guidance). A screen that wants to say so does it in its own copy. With proposals decided and none open: a single quiet line "No suggestions are waiting." and the decided ones under a collapsed "Decided ({n})" disclosure.
- **Loading** (skeleton): one card skeleton `aria-busy`; the screen's fields are usable at once (a proposal never blocks a field). The list keeps its previous cards with `aria-busy` while a decision is being sent, so cards do not jump.
- **Error** (typed refusal, `StateCard` per 01-scope):
  - `PROPOSAL_STALE` on Apply or Apply edited: the card switches to the stale state (below) and the list re-reads.
  - `PROPOSAL_NOT_OPEN`: the card re-reads and shows its real state ("Already applied" or "Already rejected"); no error alarm.
  - `PROPOSAL_NOT_FOUND`: the card is removed after a re-read, with the polite line "That suggestion is no longer there."
  - `PROPOSAL_TARGET_UNSUPPORTED`, `PROPOSAL_SOURCE_REFUSED`: cannot be provoked from the browser (it creates none); if seen, a card-level sentence with the code under Details.
  - `DRAFT_INVALID` / `DRAFT_TOO_LARGE` on Apply: the card stays open and says "The draft cannot take this value: {first error}"; Details lists `details.errors`; the card's Edit is the way forward.
  - `DRAFT_CONFLICT`, `DRAFT_EMITTED`: as in 01-scope (read-only form; the card list is read-only too, decisions shown, no buttons).
  - `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE`: whole-screen card, owned by the screen.
  - Guard codes and `ENGINE_UNREACHABLE`: the shared cards (08).
- **Partial**: some proposals decided, some open (the common state). The header counts open ones; decided ones leave the open list at once and appear under "Decided". After Apply the field shows the new value and the card becomes a one-line "Applied: {value}" row with the source label, in the include role badge text "Applied by you" ("Applied after your edit" for `applied_edited`), and "Undo" is **not** offered (see Restore above); a rejected row shows "Rejected" in the exclude role with "Restore".
- **Offline**: the engine is local, so offline is "unreachable". Cards stay visible with "As of {time}"; Apply, Edit-save, Reject and Restore are disabled with "needs the engine on this computer". Nothing is queued (as 01-scope).
- **Stale / protocol changed**: **stale** (the target changed since the proposal): the card is greyed, badge "Out of date" in the `unclear` role (text), showing "Was: {base.shown}" and "Now: {current}", the line "This field changed after the suggestion was made, so it is not applied.", and only **Reject** ("Dismiss"). Apply and Edit are disabled, because applying over a changed value could silently overwrite the researcher's own words; the check that made it re-runs on the next visit and offers a new proposal if it still applies (new `base`, so a new id). Protocol-changed: a draft has no protocol, so the case is the same as stale; after genesis, a proposal whose `target.kind = "workspace"` is stale when the workspace's protocol fingerprint is not the one it was made against (the engine adds the fingerprint to `base`), shown with the same card and the sentence "The protocol changed after the suggestion was made."

## Desktop layout
A card list inside the screen's main column, between the form and the button row; no side column. Each card (`li` in a list labelled by the heading), in order:
1. Eyebrow row: the source label (Copy) and, at the end, the status badge only when not open.
2. **What**: the change in words and the exact value in `data` style, with "Add {value} to {field name}", "Replace {now} with {value}" or "Remove {value} from {field name}" (the field name is the screen's own label).
3. **Why**: the `why` sentence, `body` text.
4. **Evidence**: a collapsed "Evidence ({n})" disclosure (help behind an icon or disclosure, 03-guidance): DOIs as links, counts, the check id. Open by default only if the proposal has no `why`.
5. Buttons: **Apply** (secondary button; the screen's one brand button stays the screen's own Continue), **Edit** (secondary), **Reject** (text button). Never pre-ticked, never a checkbox, never a "select all"; there is no "Apply all" in M10b (Open question 2 is about it).
Edit opens the field's normal editor (the same component the screen uses for that field) inside the card with the value filled in; "Apply my edit" (secondary) writes it as `applied_edited`; "Cancel" returns.
Styling: the shared draft style, `surface` with a 1px dashed `ink-muted` border (01-scope item 5, canvas `.draft`), plus the label "Suggestion · not yet yours". Machine output is a draft: no card is styled as accepted, and the `-soft` tints appear only behind the role badges (BRAND_BOOK rule quoted in 05). The dashed `brand` border stays reserved for the gate. Components: existing card, badge, button, disclosure; no new component. Keys for the brand roles: include = applied, exclude = rejected, `unclear` = stale and "waiting".

## Mobile layout (≤ 640 px)
Desktop-only on the engine, so this is a narrow desktop window (01-scope). One column; each card full width; the three buttons stack, each at least 44 px high, Apply first; Evidence stays collapsed; a stale card shows only Dismiss. A toast "Applied · {field}" with no Undo (see Restore), `role="status"`. No swipe gestures. A real phone (`TOKEN_SCOPE_REFUSED`) gets the shared desktop-only card, `inception.common.phone.desktopOnly`, and no card list.

## Keyboard
Focus order inside the list: heading, then per card: Apply, Edit, Reject (a stale card: Dismiss only), then the Evidence disclosure. After Apply or Reject, focus moves to the next open card's Apply; when none is left, to the list heading. After Edit, focus moves into the field's editor; `Escape` cancels and returns to Edit; "Apply my edit" returns focus to the next open card as above. After Restore focus stays on the row. Decisions are announced politely ("Applied: {field}", "Rejected: {field}", "Out of date: {field}"). No single-key shortcuts. `Enter` on a button acts; nothing acts on focus or hover.

## Copy
Keys in a new shared file `apps/research-ui/lib/proposals-copy.ts` (✗ M10b; en master, fr and ar fall back to en, plan §7; the N9 guard bars literal `aria-label`, `title`, `alt`, `placeholder`). Refusal cards: `inception.refusal.<CODE>.*` through `apps/research-ui/lib/screening-states.ts`, as 01-scope.
- List: `proposals.title` "Suggestions for this step · {n}"; `proposals.outOfDate` "{n} out of date"; `proposals.none` "No suggestions are waiting."; `proposals.decided` "Decided ({n})"; `proposals.badge` "{n} suggestions" (stepper).
- Card: `proposals.draftLabel` "Suggestion · not yet yours"; `proposals.what.add` "Add {value} to {field}"; `proposals.what.remove` "Remove {value} from {field}"; `proposals.what.replace` "Replace {now} with {value}"; `proposals.why` "Why"; `proposals.evidence` "Evidence ({n})"; `proposals.evidence.doi` "Paper {doi}"; `proposals.evidence.check` "Check {id}".
- Source labels: `proposals.source.check` "Suggested by a check: {name}"; `proposals.source.import` "From the protocol {name}"; `proposals.source.agent` "Suggested by an assistant" (reserved, M10c; not shown in M10b); `proposals.source.engine.<mechanism>` for the six records: "Written by the wizard from your answers", "A term from the sampled papers", "A concept suggested from your topic", "A column suggested for this playbook", "A direction proposed from the sampled papers", "A paper from the sample kept as a known paper".
- Actions: `proposals.act.apply` "Apply"; `proposals.act.edit` "Edit"; `proposals.act.applyEdit` "Apply my edit"; `proposals.act.cancel` "Cancel"; `proposals.act.reject` "Reject"; `proposals.act.dismiss` "Dismiss"; `proposals.act.restore` "Restore"; `proposals.act.announceApplied` "Applied: {field}"; `proposals.act.announceRejected` "Rejected: {field}"; `proposals.act.toast` "Applied · {field}".
- Status: `proposals.status.applied` "Applied by you"; `proposals.status.appliedEdited` "Applied after your edit"; `proposals.status.rejected` "Rejected"; `proposals.status.stale` "Out of date".
- Stale: `proposals.stale.was` "Was: {shown}"; `proposals.stale.now` "Now: {shown}"; `proposals.stale.line` "This field changed after the suggestion was made, so it is not applied."; `proposals.stale.protocol` "The protocol changed after the suggestion was made."
- Errors in the card: `proposals.err.invalid` "The draft cannot take this value: {error}"; `proposals.err.gone` "That suggestion is no longer there."; `proposals.err.already` "Already {status}."
- Offline: `proposals.offline` "needs the engine on this computer".
- Refusals: `inception.refusal.PROPOSAL_STALE.*`, `PROPOSAL_NOT_OPEN.*`, `PROPOSAL_NOT_FOUND.*`, `PROPOSAL_TARGET_UNSUPPORTED.*`, `PROPOSAL_SOURCE_REFUSED.*`, `PROPOSAL_NOT_OFFERED.*` (en text written with the build, in the form sentence, effect, next step). A refused record never blocks the screen: the field is already saved, and the screen shows one quiet line "This choice was saved; its source could not be recorded."

## Accessibility
- The list is a `ul` labelled by its heading; each card is an `li`; the change is real text, never an image; the source label and status badge carry words, so colour is never the only cue (stale and rejected are text badges).
- Buttons name their target by visible text plus `aria-describedby` to the "What" line ("Apply" described by "Add uas to Concepts"). Decisions and the toast use `aria-live="polite"`; refusals `role="alert"`.
- Dashed border plus the label "Suggestion · not yet yours" mark a draft without colour; the contrast pairs come from `docs/ux/brand/tokens.json`: `ink` on `surface`; role badge text in the role's full colour on its `-soft` tint; `blocked` is text colour only (BRAND_BOOK).
- Evidence disclosure is a real `button` with `aria-expanded`.
- **RTL (ar)**: the card layout mirrors; the button order follows reading order (Apply first, at the inline start); the `value` and `now` text is `dir="auto"` (user words, in the review's language); DOIs, ids, check ids, field names in `data` style and counts are `dir="ltr"` inside `bdi`, numerals Latin; the stale "Was / Now" pair is two labelled rows, not a side-by-side arrow, so reading direction cannot reverse its meaning; the list-count badge in the stepper keeps the number in `bdi`.
- Target size 44 px on mobile; focus ring visible on every button; the Edit editor keeps the field's own label.

## The six mechanisms that exist today
Each is engine-written (no language model) and each stays as it is. **In M10b each keeps its own fields, its own read route and its own place in the draft, and only adopts the card (its look and its Apply / Edit / Reject wording, never pre-ticked); none is migrated to the proposal store**, so none is ever an open stored proposal. Their decisions live where they do today (the draft field, and for direction the `grounding`). **When the researcher accepts one, the screen also sends `…/proposals/record`** (decided 2026-11-15), so the record, and after genesis `audit/proposals.jsonl`, can say that a synonym came from the sampled papers or a known paper from the sample. Only acceptances are recorded; a suggestion left unticked leaves no trace. The record name of each mechanism is in the table.

| # | Mechanism | Code that produces it | Where its decision lives today | Card in M10b |
| :-- | :-- | :-- | :-- | :-- |
| 1 `wizard_criterion` | Wizard-written criteria (from the proof answer, the paradigm default, the out-of-scope list) | `CRITERION_SOURCES` `intent.py:243`; `draft_criteria` `intent.py:287`; `criteria_with_decisions` `steps.py:285`; route `POST /steps/criteria` `steps.py:304` | `draft.criteria_decisions[crit_id]` (`steps.py:169`) | Accept / Drop (no Edit: no value to edit), source label from `source_label` verbatim |
| 2 `pool_synonym` | Pool synonym suggestions | `concept_report` `recon/vocabulary.py:43`; route `GET …/recon/concepts` `recon.py:397` | ticked term appended to `draft.concepts[i].synonyms` | Apply (tick) / Edit (change the word) / Reject (leave unticked) |
| 3 `suggested_concept` | Suggested concepts | `draft_default_concepts` `intent.py:210`; `_scope` `steps.py:259`; used by `_concept_rows` `recon.py:390` when the draft has no concept | `draft.concepts` | Apply (add) / Edit / Reject |
| 4 `matrix_column` | Suggested matrix columns | `_default_matrix_dimensions` `genesis.py:373`; `_matrix` `steps.py:315` | `draft.matrix_columns` (names; `build_intent` keeps only default names, `steps.py:353-355`) | Apply (tick) / Reject; Edit is not offered, because a custom name would be dropped silently (05) unless `02-checks` / 05's amendment adds own columns |
| 5 `direction` | Direction proposals | `directions_for` `recon/session.py:504`; route `GET …/recon/directions` `recon.py:379`; bound by `POST …/recon/bind` `recon.py:445` into `record["grounding"]` (`drafts.py:95`) | the record's `grounding` (not a draft field) | Choose / Own words / Skip stay as 03-direction defines them; the card look only |
| 6 `anchor_seed` | Anchor papers kept as seeds | `seed_candidates` `recon/vocabulary.py:82`; route `GET …/recon/seeds` `recon.py:427` | `draft.golden_seeds` (DOIs, at most 25, `steps.py:83`, `:174`) | Keep (= Apply) / Skip (= Reject); no Edit |

Not verified in the code: that the screens of 02 and 03 (built) show these in the order and wording above; the table follows the code that produces each, not the built UI. The inception `01-scope`, `02-explore` and `03-direction` specs are being amended on another branch and are not edited here.

Which **new** M10b suggestions are open stored proposals: a fixed check's recommended change (`02-checks`). An imported protocol's fields are not proposals in M10b (`09-start-from-protocol` "How imported values arrive"). There is no "Apply all" for a step in M10b (decided 2026-11-15; revisit in M10c when the assistant adds volume).

## Acceptance tests
Vitest, `apps/research-ui/tests/proposals.test.tsx` (names are what the file's `it` titles say):
- `a proposal card is never pre-ticked or pre-applied`: on load no card has an applied state, no checkbox is checked, nothing was sent.
- `Apply sends one POST and shows the new value`: the request carries only `base_updated_at`; the field shows the value; the card becomes the "Applied by you" row.
- `Edit then Apply sends the researcher's value as apply-edited`: the body has `value`; status text is "Applied after your edit".
- `Reject changes no field; Restore returns it to open`: the draft fields are unchanged after Reject.
- `a stale proposal shows Was and Now, no Apply and no Edit`: `PROPOSAL_STALE` from the engine and a derived `stale` both render it.
- `PROPOSAL_NOT_OPEN re-reads the card and does not alarm`.
- `DRAFT_INVALID on Apply keeps the card open with the first error`.
- `DRAFT_CONFLICT and DRAFT_EMITTED make the list read-only`.
- `the stepper badge and the list heading show the engine's count, never one the browser derived`.
- `no card is rendered for an empty step, and the "Decided" disclosure lists decided ones`.
- `offline disables every button and keeps the cards`.
- `RTL: values are dir=auto and DOIs and ids are dir=ltr`; `copy: every proposals.* key exists in en and fr/ar fall back` (the N9 guard).
- `agent source is not rendered in M10b`: a proposal with `source: "agent:…"` from a stub is shown with the generic label and the test documents that the engine refuses it (`PROPOSAL_SOURCE_REFUSED`).
Python, `tests/console/test_inception_proposals.py` (new ✗ M10b): apply writes the draft and the proposal in one `_write`; a PUT keeps `proposals`; `PROPOSAL_STALE` when the target changed; apply goes through `parse_draft` (a value over the limits is `DRAFT_TOO_LARGE`); the id is stable for the same input and changes with `base`; `agent:*` refused; genesis writes `audit/proposals.jsonl` and one `PROPOSALS_RECORDED` row; a later decision appends `PROPOSAL_DECIDED`; the new routes are in both allow-lists; `record` writes one `engine:<mechanism>` entry and changes no draft field, is a no-op the second time, refuses an unknown mechanism (`PROPOSAL_SOURCE_REFUSED`) and a value the mechanism does not offer (`PROPOSAL_NOT_OFFERED`); genesis writes `in_protocol: false` for an applied value that was edited away.
Playwright, `apps/research-ui/e2e/inception.spec.ts` (this pattern's part): a check produces a proposal on step 5; Apply writes it into the field; reload and it is still applied; reject and restore; edit the target by hand and watch the card go out of date; keyboard-only decision; RTL pass; axe in light and dark; no horizontal overflow at 375 and 1440 px; after genesis the workspace holds `audit/proposals.jsonl` listing the decisions.

## Open questions
None.

Closed by the researcher on 2026-11-15 (record: `docs/roadmap/milestones/M10b-proposals-checks.md`, R1 and R2 and "Adopted from the writers' recommendations"):
1. The six existing mechanisms are recorded when the researcher accepts one, as a write-only `engine:<mechanism>` entry (`…/proposals/record`); they are not migrated to the store.
2. No "Apply all" in M10b; revisit in M10c.
3. A stale proposal cannot be edited or applied, only dismissed; the check offers a new one if it still holds.
4. Only a rejected proposal can be restored; an applied one is undone by editing the field.
5. The new refusal codes are not added to `docs/architecture/refusals.md` (the closed `Envelope@1` registry); they are documented in `docs/architecture/inception-api.md` at build. No contract change.
