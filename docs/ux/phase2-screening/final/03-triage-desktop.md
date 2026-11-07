# 03 Triage queue, desktop    Status: FINAL | Phase 2 Screening | Route `/screening/triage` | Milestone M1a (events, queue) + M1b (UI)

Boards: `Triage` (D4, proposal hidden), `TriageRevealed` (D5, after deciding). Contract: `docs/architecture/screening-api-contract.md` §3-§4.

## Amended 2026-11-07 (M6-beta)
Source: `docs/roadmap/milestones/M6-beta.md` section A and B; decisions "Answer until decisive", "Advance on decide, as a workspace setting", "Details on demand"; review U-4 to U-8, S-P1-3. Where a sentence further down says otherwise, this section wins; the old sentences are struck or rewritten in place.

**1. Answer until decisive.** The checklist is no longer all-or-nothing.
- **Exclude** is enabled as soon as one criterion fails: an inclusion criterion answered no, or an exclusion criterion answered yes.
- **Include** is enabled when every inclusion criterion is answered yes and no exclusion criterion is answered yes. Exclusion criteria left unanswered do not block it.
- **Unclear → full text** is always enabled. **Skip** is unchanged.
- A criterion left unanswered is **absent** from the event's `criteria`. It is never sent as `not_reported`: that value is sent only when the reviewer presses "Not reported" on that criterion, because it claims the reviewer looked and found nothing.
- The line under the checklist replaces "Answer every criterion before deciding" (`screening.triage.checklist.required`, removed). It is a status line, `aria-live="polite"`:
  - one criterion fails: "Exclude is ready: INC-01 answered no" (`screening.triage.checklist.excludeReady`, `{id}`, `{answer}`); with an exclusion criterion: "Exclude is ready: EXC-02 answered yes";
  - nothing fails and inclusion answers are missing: "Include needs INC-02 and INC-03" (`screening.triage.checklist.includeNeeds`, `{ids}`);
  - an inclusion answered "not reported" counts as not yet yes: "Include needs INC-02 to be yes";
  - Include ready: "Include is ready" (`screening.triage.checklist.includeReady`).
- Logic: `lib/triage-logic.ts` `allAnswered` is replaced by `decisiveFor(outcome)`; the UI states what is enabled, it does not derive the outcome (the server's `derived_outcome` rule is unchanged and the reviewer can still choose another outcome).
- Engine: no change to the event contract (`criteria` stays optional; `events.py` validates the reason code only).

**2. The reason comes from the checklist.** On Exclude, the reason is pre-selected as the **first failed criterion in protocol order** (inclusions and exclusions in the order the protocol lists them) and shown in words: "Fails INC-01 · Uses UAV-acquired imagery …" (`screening.triage.reason.fails`, `{id}`, `{text}`), or "Meets exclusion EXC-02 · …" (`screening.triage.reason.meets`); the code (`FAILS-INC-01` or `EXC-02`) sits in mono underneath. The other codes stay available as chips labelled with the criterion's first clause, truncated at 60 characters (`lib/triage-copy.ts`, from the protocol text); the code is the chip's second line. **E then Enter** excludes with the pre-selected reason; choosing another chip first changes it. The numbered chips 1 to 7 and their keys stay.
- Engine (S-P1-3, ✗ M6-beta, optional): `REASON_CODE_INCONSISTENT` (HTTP 422) when an EXCLUDE's code names a criterion that the same event answers the other way. Plain sentence: "That reason does not match your answers." (`screening.refusal.REASON_CODE_INCONSISTENT`); the code is in Details. Test `tests/test_screening_events.py`. The UI never triggers it with the pre-selection; it guards a chip chosen against the checklist.

**3. Advance on decide.** The setting lives on Prepare (02) and is read by `GET /settings`.
- "Show the draft, then N" (default): with a draft, the revealed state shows as before and **N** advances; with no draft to reveal, the next record opens at once.
- "Move on at once": the next record always opens at once. The draft is **not** requested after the decision (no reveal is recorded); it stays in the record's details and is shown when the reviewer reopens the decided record.
- When drafts are already shown beside the record (`blinding = show`) there is nothing to reveal, so the next record opens at once under either value.
- Focus moves to the new record's heading; the live region says "Decision saved. Record 13 of 30." (`screening.triage.announce.savedNext`). The next record is the next item of the current queue view. Keypress budget: ten records decided by keyboard in at most ten keypresses each, Playwright `screening/triage-desktop.spec.ts`.

**4. Position and a collapsed queue.**
- Above the record: "Record 12 of 30 · batch 1" (`screening.triage.position`, `{k}`, `{total}`, `{batch}`). `k` is the number of records already decided plus this record's place in the "Needs you" list; `total` is the summary total (client-side, from `GET /summary` and the loaded queue, no engine change). When a decided record is open from the "Decided" view it reads "Decided record 4 of 11 · batch 1".
- The queue card is **collapsed by default**: the view chips plus two rows, the current title and the next title (`screening.triage.queue.current`, `.next`). A toggle button "Show the whole queue" / "Hide the queue" (`screening.triage.queue.expand`, `.collapse`, `aria-expanded`, `aria-controls`) expands it; so does the first **J** or **K**. The choice is remembered for the browser session (`sessionStorage`, key per workspace), not stored in the workspace. The toggle and the chips are 44 px.

**5. Undo only when it can.** **Z** and the Undo button are absent until the record has a superseding target (`undoTarget` returns a value). The copy "A first decision cannot be undone; change it instead." (`undoUnavailable`) is removed. "Change my decision" stays.

**6. All decided is a hand-off.** When the "Needs you" view is empty the centre shows the heading "All 30 records are decided" (`screening.triage.allDecided.title`, `{total}`), then **Publish** as the one brand button (link to 09) and **Agreement** as a text link (07). The draft aside is not rendered. The lede stops describing the blinding setting and reads "Every record has your decision." (`screening.triage.allDecided.lede`). The Home link remains. If a conflict is open or the binding is stale, the card above it is shown and Publish is replaced by "See the change" or by the conflict card's action.

**7. Details (12).** The record's study id and the raw DOI; the "Recorded as you · HUMAN · time · protocol sha" line; event ids; the refusal code in banners; and, in the draft aside, model, prompt hash and proposal id move behind one "Details" per card. The decision card keeps one word, "Saved", with the time on hover.

- Tests: `triage.decisive.test.tsx`, `triage.reason-from-checklist.test.tsx`, `triage.advance-on-decide.test.tsx`, `triage.position.test.tsx`, `triage.undo-hidden.test.tsx`, `triage.all-decided.test.tsx`, `triage.details.test.tsx`. Playwright at 1440 and 1024 for the collapsed queue.

**Purpose.** Decide every record: read it, fill the checklist, choose Include / Exclude / Unclear → full text, and move on by keyboard.

**Changed from the canvas.**
- Canvas D4/D5 already hide the proposal until you decide and show the queue as all records (chips Proposal ready / No proposal / Title only). Kept.
- **Skip** (S) is a client-side deferral and writes **no event** (canvas shows it as an action; it is not a decision).
- **Changing a decision after the reveal** ("Change my decision", D5) is allowed as a superseding event; the engine sets `changed_after_reveal` (contract §3.1). **Undo** (Z) is also a superseding event; it appears only once the record has something to undo (amendment 5).
- ~~The checklist answers (yes / no / not reported) are **required** on desktop.~~ Amended: answers are taken until the decision is decisive (amendment 1); unanswered criteria are absent, never `not_reported`. The "From your answers: Include" line is the server's plain-code rule-table result; "you can still choose another outcome" is kept. The model never derives the outcome.
- Chip filters that reveal the agent's call (D5 "Differs" on the compared record, and any "agent disagrees" view) exist only for records you have already decided (`GET /queue` with `decided=true`).
- A queue ordering by the agent's uncertainty is available after a proposals run: `GET /queue?order=agent_uncertainty` ✗ M1a. It orders without revealing the agent's call, and the methods paragraph discloses it (see 06). Default ordering is the seeded order. A decision on a study with an open conflict returns the per-event result `conflict` (no separate refusal code).
- The canvas "Unclear" button reads "Unclear" with a tooltip; the label everywhere else is "Unclear → full text" (stored `MAYBE`).

## Entry / exit
- Entry: Home (01) "Open triage"; step bar; `g t`.
- Exit: queue empty → 09 (brand button) or 07 (link), see amendment 6. Gate: decisions are disabled when the binding is `STALE_BINDING`.

## Data in
| Field | Source |
| :-- | :-- |
| queue items `{study_id, title, batch_id, has_proposal, decided, flags}`; views `needs_you`, `proposal_ready`, `no_proposal`, `title_only`, `decided` | `GET /queue?view=&cursor=&limit=` ✗ M1a |
| record, highlights, criteria, my_decision, history | `GET /records/{study_id}` ✗ M1a (see 05) |
| proposal (after decision) | `GET /records/{study_id}/proposal` ✗ M1a; `PROPOSAL_HIDDEN` before |
| conflicts | `GET /decisions/conflicts` ✗ M1a |
| settings (including the advance-on-decide value) | `GET /settings` ✓ `screening_v1.py:325`; the new field is ✗ M6-beta |

## Data out
`POST /decisions/events` ✗ M1a (≤ 200 per request): event with `event_id` (UUIDv7, client), `study_id`, `screener_id`, `method: HUMAN`, `outcome` INCLUDE | EXCLUDE | MAYBE, `reason_code` (required for EXCLUDE: protocol code or `FAILS-<id>`; pre-selected from the first failed criterion, amendment 2), `note`, `criteria[]` (only the criteria the reviewer answered), `decided_at`, `device: desktop`, `supersedes`, `binding`. Per-event result: `accepted`, `duplicate`, `conflict`, `refused`. Engine adds `received_at`, `token_scope`, `changed_after_reveal`. A conflict goes to `GET /decisions/conflicts`; `POST /decisions/conflicts/{study_id}/resolve` ✗ M1a writes a superseding event. Journal: one `SCREENING_DECISIONS_RECEIVED` row per accepted request.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/queue?view=&cursor=` | ✗ M1a |
| `GET /api/v1/screening/records/{study_id}` | ✗ M1a |
| `GET /api/v1/screening/records/{study_id}/proposal` | ✗ M1a |
| `POST /api/v1/screening/decisions/events` | ✗ M1a |
| `POST /decisions/events` refusal `REASON_CODE_INCONSISTENT` (422) | ✗ M6-beta (optional; `events.py:240-243` validates the code only today) |
| `GET /api/v1/screening/settings` (advance-on-decide) | ✓ `screening_v1.py:325`; new field ✗ M6-beta |
| `GET /api/v1/screening/decisions/conflicts` | ✗ M1a |
| `POST /api/v1/screening/decisions/conflicts/{study_id}/resolve` | ✗ M1a |
| `GET /api/v1/screening/ui/batch/{n}/criterion-refs` | ✓ `screening.py:1024` (until `/records` carries criteria) |
| `POST /api/v1/screening/batch/{n}/decisions` (legacy draft writer) | ✓ `screening.py:102`; deprecated, not used by this screen |

## States
- **Default (D4)** (amended): h1 "Is this record in scope? Decide first; the agent's draft opens after." "Record 12 of 30 · batch 1" above the record. Left queue card collapsed: chips (Proposal ready n, No proposal n, Title only n) plus the current and next titles, expandable. Centre record with highlights; "Your checklist" with chip answers and the status line ("Exclude is ready: INC-01 answered no"); right `draft` aside "Agent proposal · draft · Hidden until you decide" with skeleton bars (model, prompt hash and date in its Details); decision card: Include (brand), Exclude, Unclear, Skip with key hints (Undo only when it can); on Exclude the pre-selected reason in words and the other reasons as chips; after a decision "Saved" (the recorded-as line is in Details).
- **Revealed (D5)**: h1 "You included it. The agent's draft said exclude, on INC-03." Queue row tagged "Included by you". Table "Your checklist beside the agent's" with a "Differs" badge row and an Outcome row; the draft aside shows outcome "Exclude · fails INC-03" with "Not a decision", the reasoning verbatim, the abstract quote; model, prompt hash and proposal id are in the aside's Details. Actions: Next record (N, brand), Change my decision, Undo (only when it can), Decision history. Reached only when the record has a draft and the setting is "show the draft, then N".
- **Empty**: all decided → the hand-off of amendment 6 ("All 30 records are decided", Publish brand button, Agreement link); zero batches → link to 02 (D7 Empty).
- **Loading**: skeleton rows and record (D7 Loading); next 5 records prefetched.
- **Error**: `PROPOSAL_HIDDEN` (no error styling, the hidden aside), `REASON_CODE_INVALID`, `REASON_CODE_INCONSISTENT` (✗ M6-beta, plain sentence on the card, code in Details), `UNKNOWN_STUDY`, `STALE_BINDING` (✓ `integrity.py:28`), `IDEMPOTENCY_CONFLICT`, `TOKEN_SCOPE_REFUSED`, `ENGINE_UNREACHABLE` (client-side; "Your last n decisions are held in this tab").
- **Partial**: event result `conflict` → row badge "Conflict" (`unclear`), record locked until chosen; `duplicate` is silent. Proposal rejected by a validator is shown as "Proposal rejected" with the failed check.
- **Offline**: decisions queue locally (IndexedDB) and flush with backoff; proposal reads unavailable; badge shows the count.
- **Protocol-changed**: banner "Batches no longer match the protocol", decisions disabled, existing decisions kept (08).

## Desktop layout
Canvas D4/D5: three zones (queue 260 px, record and checklist, draft aside), compact density, one brand button per screen: Include in D4, Next record in D5. The `draft` surface is plain `surface`, never an `include` tint until a person verifies.

## Mobile layout (≤ 640 px)
See 04.

## Keyboard
`I` Include, `E` Exclude (reason pre-selected; `Enter` confirms it, chips 1-7 choose another), `U` Unclear → full text, `S` Skip (deferral), `Z` Undo (only when available), `N` next record (after a reveal), `J`/`K` queue (the first press expands the collapsed queue), `1`/`2`/`3` yes/no/not reported on the focused criterion, `?` help. Shortcuts are off in text fields. After a decision focus moves to the revealed heading, then to Next record.

## Copy
`screening.triage.title`, `screening.triage.lede`, `screening.triage.queue.chip.{proposalReady,noProposal,titleOnly}`, `screening.triage.queue.hiddenRow`, `screening.triage.checklist.*`, `screening.triage.proposal.{hiddenTitle,hiddenBody,draftLabel,notADecision,differs}`, `screening.triage.decision.{include,exclude,unclear,skip,undo,change,next,history}`, `screening.triage.reason.*` (including `.fails`, `.meets`), `screening.triage.checklist.{excludeReady,includeNeeds,includeReady}`, `screening.triage.position`, `screening.triage.queue.{current,next,expand,collapse}`, `screening.triage.allDecided.{title,lede}`, `screening.triage.announce.savedNext`, `screening.refusal.REASON_CODE_INCONSISTENT`, `screening.details.*` (12; replaces `screening.triage.recordedAs` on the card), removed: `screening.triage.checklist.required`, `undoUnavailable`, `screening.triage.revealed.title.{agrees,differs}`, `screening.outcome.unclear.long`.

## Accessibility
Decision buttons show text and a key hint. Queue is a list with `aria-current`; chips use `aria-pressed`. Live region announces "Decision saved", "Queued", "Conflict". Draft aside is labelled "Agent proposal, hidden" / "revealed". Answer chips are 44 px. Contrast per tokens: `include`/`unclear`/`blocked` as text and icon colour on their `-soft` fills only. RTL: queue card flips to the inline end; key hints Latin.

## Acceptance tests
Vitest: `triage.keymap.test.tsx`, `triage.blinding-no-proposal-field.test.tsx`, `triage.skip-writes-no-event.test.ts`, `triage.undo-superseding.test.ts`, `triage.changed-after-reveal.test.ts`, and the M6-beta tests listed in the amendment. Playwright: `screening/triage-desktop.spec.ts` (golden-uav-30 end to end, proposal hidden until decision, conflict visible, replay idempotent).

## Open questions
None.
