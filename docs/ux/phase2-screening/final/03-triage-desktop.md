# 03 Triage queue, desktop    Status: FINAL | Phase 2 Screening | Route `/screening/triage` | Milestone M1a (events, queue) + M1b (UI)

Boards: `Triage` (D4, proposal hidden), `TriageRevealed` (D5, after deciding). Contract: `docs/architecture/screening-api-contract.md` §3-§4.

**Purpose.** Decide every record: read it, fill the checklist, choose Include / Exclude / Unclear → full text, and move on by keyboard.

**Changed from the canvas.**
- Canvas D4/D5 already hide the proposal until you decide and show the queue as all records (chips Proposal ready / No proposal / Title only). Kept.
- **Skip** (S) is a client-side deferral and writes **no event** (canvas shows it as an action; it is not a decision).
- **Changing a decision after the reveal** ("Change my decision", D5) is allowed as a superseding event; the engine sets `changed_after_reveal` (contract §3.1). **Undo** (Z) is also a superseding event and is available later from the record's decision history.
- The checklist answers (yes / no / not reported) are **required** on desktop (the rule table needs them). The "From your answers: Include" line is the server's plain-code rule-table result; "you can still choose another outcome" is kept. The model never derives the outcome.
- Chip filters that reveal the agent's call (D5 "Differs" on the compared record, and any "agent disagrees" view) exist only for records you have already decided (`GET /queue` with `decided=true`).
- A queue ordering by the agent's uncertainty is available after a proposals run: `GET /queue?order=agent_uncertainty` ✗ M1a. It orders without revealing the agent's call, and the methods paragraph discloses it (see 06). Default ordering is the seeded order. A decision on a study with an open conflict returns the per-event result `conflict` (no separate refusal code).
- The canvas "Unclear" button reads "Unclear" with a tooltip; the label everywhere else is "Unclear → full text" (stored `MAYBE`).

## Entry / exit
- Entry: Home (01) "Open triage"; step bar; `g t`.
- Exit: queue empty → 07 or 09. Gate: decisions are disabled when the binding is `STALE_BINDING`.

## Data in
| Field | Source |
| :-- | :-- |
| queue items `{study_id, title, batch_id, has_proposal, decided, flags}`; views `needs_you`, `proposal_ready`, `no_proposal`, `title_only`, `decided` | `GET /queue?view=&cursor=&limit=` ✗ M1a |
| record, highlights, criteria, my_decision, history | `GET /records/{study_id}` ✗ M1a (see 05) |
| proposal (after decision) | `GET /records/{study_id}/proposal` ✗ M1a; `PROPOSAL_HIDDEN` before |
| conflicts | `GET /decisions/conflicts` ✗ M1a |
| settings | `GET /settings` ✗ M1a |

## Data out
`POST /decisions/events` ✗ M1a (≤ 200 per request): event with `event_id` (UUIDv7, client), `study_id`, `screener_id`, `method: HUMAN`, `outcome` INCLUDE | EXCLUDE | MAYBE, `reason_code` (required for EXCLUDE: protocol code or `FAILS-<id>`), `note`, `criteria[]`, `decided_at`, `device: desktop`, `supersedes`, `binding`. Per-event result: `accepted`, `duplicate`, `conflict`, `refused`. Engine adds `received_at`, `token_scope`, `changed_after_reveal`. A conflict goes to `GET /decisions/conflicts`; `POST /decisions/conflicts/{study_id}/resolve` ✗ M1a writes a superseding event. Journal: one `SCREENING_DECISIONS_RECEIVED` row per accepted request.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/queue?view=&cursor=` | ✗ M1a |
| `GET /api/v1/screening/records/{study_id}` | ✗ M1a |
| `GET /api/v1/screening/records/{study_id}/proposal` | ✗ M1a |
| `POST /api/v1/screening/decisions/events` | ✗ M1a |
| `GET /api/v1/screening/decisions/conflicts` | ✗ M1a |
| `POST /api/v1/screening/decisions/conflicts/{study_id}/resolve` | ✗ M1a |
| `GET /api/v1/screening/ui/batch/{n}/criterion-refs` | ✓ `screening.py:1024` (until `/records` carries criteria) |
| `POST /api/v1/screening/batch/{n}/decisions` (legacy draft writer) | ✓ `screening.py:102`; deprecated, not used by this screen |

## States
- **Default (D4)**: h1 "Is this record in scope? Decide first; the agent's draft opens after." Left queue card with chips (Proposal ready n, No proposal n, Title only n) and rows `Batch 060 · proposal hidden`; centre record with highlights; "Your checklist" table with chip answers; right `draft` aside "Agent proposal · draft · Hidden until you decide" with skeleton bars, model/prompt hash/date; decision card: Include (brand), Exclude, Unclear, Skip, Undo with key hints; Exclude reason chips (Fails INC-01..04, EXC-01..03); "Recorded as you · HUMAN · time · protocol fingerprint" line.
- **Revealed (D5)**: h1 "You included it. The agent's draft said exclude, on INC-03." Queue row tagged "Included by you". Table "Your checklist beside the agent's" with a "Differs" badge row and an Outcome row; the draft aside shows outcome "Exclude · fails INC-03" with "Not a decision", the reasoning verbatim, the abstract quote, model/prompt/proposal hashes. Actions: Next record (N, brand), Change my decision, Undo, Decision history.
- **Empty**: all decided → "All records decided" with links to 07 and 09; zero batches → link to 02 (D7 Empty).
- **Loading**: skeleton rows and record (D7 Loading); next 5 records prefetched.
- **Error**: `PROPOSAL_HIDDEN` (no error styling, the hidden aside), `REASON_CODE_INVALID`, `UNKNOWN_STUDY`, `STALE_BINDING` (✓ `integrity.py:28`), `IDEMPOTENCY_CONFLICT`, `TOKEN_SCOPE_REFUSED`, `ENGINE_UNREACHABLE` (client-side; "Your last n decisions are held in this tab").
- **Partial**: event result `conflict` → row badge "Conflict" (`unclear`), record locked until chosen; `duplicate` is silent. Proposal rejected by a validator is shown as "Proposal rejected" with the failed check.
- **Offline**: decisions queue locally (IndexedDB) and flush with backoff; proposal reads unavailable; badge shows the count.
- **Protocol-changed**: banner "Batches no longer match the protocol", decisions disabled, existing decisions kept (08).

## Desktop layout
Canvas D4/D5: three zones (queue 260 px, record and checklist, draft aside), compact density, one brand button per screen: Include in D4, Next record in D5. The `draft` surface is plain `surface`, never an `include` tint until a person verifies.

## Mobile layout (≤ 640 px)
See 04.

## Keyboard
`I` Include, `E` Exclude (reason chips 1-7, `Enter` confirms), `U` Unclear → full text, `S` Skip (deferral), `Z` Undo, `N` next record (after reveal), `J`/`K` queue, `1`/`2`/`3` yes/no/not reported on the focused criterion, `?` help. Shortcuts are off in text fields. After a decision focus moves to the revealed heading, then to Next record.

## Copy
`screening.triage.title`, `screening.triage.lede`, `screening.triage.queue.chip.{proposalReady,noProposal,titleOnly}`, `screening.triage.queue.hiddenRow`, `screening.triage.checklist.*`, `screening.triage.proposal.{hiddenTitle,hiddenBody,draftLabel,notADecision,differs}`, `screening.triage.decision.{include,exclude,unclear,skip,undo,change,next,history}`, `screening.triage.reason.*`, `screening.triage.recordedAs`, `screening.triage.revealed.title.{agrees,differs}`, `screening.outcome.unclear.long`.

## Accessibility
Decision buttons show text and a key hint. Queue is a list with `aria-current`; chips use `aria-pressed`. Live region announces "Decision saved", "Queued", "Conflict". Draft aside is labelled "Agent proposal, hidden" / "revealed". Answer chips are 44 px. Contrast per tokens: `include`/`unclear`/`blocked` as text and icon colour on their `-soft` fills only. RTL: queue card flips to the inline end; key hints Latin.

## Acceptance tests
Vitest: `triage.keymap.test.tsx`, `triage.blinding-no-proposal-field.test.tsx`, `triage.skip-writes-no-event.test.ts`, `triage.undo-superseding.test.ts`, `triage.changed-after-reveal.test.ts`. Playwright: `screening/triage-desktop.spec.ts` (golden-uav-30 end to end, proposal hidden until decision, conflict visible, replay idempotent).

## Open questions
None.
