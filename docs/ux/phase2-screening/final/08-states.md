# 08 States and recovery    Status: FINAL | Phase 2 Screening | Route: inline cards on 01-09 plus `/screening/issues` | Milestone M1a (typed refusals) + M1b (UI)

Board: `States` (D7, nine cards). Contract: `screening-api-contract.md` §4, §7. Code check: `src/` grepped for each existing code.

**Purpose.** Turn every way screening can stop into what happened, what it affects, and one next step, with the typed code shown so a supervisor can find it in the journal.

**Amended 2026-11-07 (M6-beta, researcher).** The typed code moves behind the card's "Details" disclosure (rule page `12-details-disclosure.md`). It stays in the DOM and is still selectable text, so a supervisor can still find it in the journal. The card body keeps the plain sentence, what it affects, and the next step.

**Changed from the canvas.**
- Codes follow contract §7: `DECISION_CONFLICT` is dropped (a conflict is the per-event result `conflict`, not a refusal); the Conflict card shows `conflict`. `RATE_LIMITED` is kept (exists in code). `PROVENANCE_MISSING` is in contract §7. `RUN_ALREADY_ACTIVE` and `COST_CEILING_REACHED` (contract §7) get cards too. `ENGINE_UNREACHABLE` is client-side only.
- The Conflict card, the Engine-unreachable card and the Phone-offline card appear on the phone too (04).
- Wherever a card would mention the agent's call for an undecided record it says "Available after you decide".
- "Approval waits until queued phone decisions have arrived" (Phone offline card) is decided: approval is refused while any paired phone has queued events (contract §9.1, spec 09).
- New card (not on the canvas): **Not approved**, because `APPROVAL_MISSING` exists and publish needs it.

## Entry / exit
Cards appear inline on the screen that hit the state; `/screening/issues` lists all currently active cards. Each action exits to the screen it names.

## Data in
Typed refusals from the routes of 01-09; `GET /ui/batches` ✓ `screening.py:572` (`binding.state = STALE_BINDING`, coverage, `unresolved_rows`); `GET /ui/batch/{n}/review` ✓ `screening.py:839`; `GET /decisions/conflicts` ✗ M1a; `GET /summary` ✗ M1a.

## Data out
Per card action: `POST /prepare` ✗ M1a (rebind, re-screen a batch); `POST /decisions/conflicts/{study_id}/resolve` ✗ M1a (keep one; writes a superseding event naming both); `POST /proposals/runs` ✗ M1b (resume); `POST /actions/defer` ✓ `screening.py:1512`.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /ui/batches`, `GET /ui/batch/{n}/review` | ✓ `screening.py:572`, `:839` |
| `POST /actions/defer` | ✓ `screening.py:1512` |
| `GET /decisions/conflicts`, `POST /decisions/conflicts/{study_id}/resolve` | ✗ M1a |
| `POST /prepare` | ✗ M1a |
| `POST /proposals/runs` | ✗ M1b |

## States (the cards; each has loading skeleton, copy, a code line and one primary action)
| Card (badge) | Role | Code | Exists? | Next step |
| :-- | :-- | :-- | :-- | :-- |
| Empty: No batches yet | exclude | none | n/a | Prepare batches (02) |
| Loading: Reading 163 batch files | brand | none | n/a | no partial number shown as final |
| Protocol changed | blocked | `STALE_BINDING` | ✓ `src/scholar_harness/screening/integrity.py:28` | Rebind and re-screen what changed / See the change; decisions kept |
| Title only: n records have no abstract | unclear | none (flag `title_only`) | n/a | Fill abstracts from OpenAlex first / Screen them as they are; goes to Unclear, never excluded by default |
| Refused file: decisions file without provenance | blocked | `PROVENANCE_MISSING` | contract §7 (events intake, collect; a decision lacks screener, method or `decided_at`) | Re-screen batch / Open the refused file (kept as `.rejected`) |
| Engine unreachable | blocked | `ENGINE_UNREACHABLE` | client-side only | Try again; "held in this tab" warning |
| Conflict: decided on both devices | unclear | per-event result `conflict` | contract §3.4 | Keep Include / Keep Exclude · reason; never auto-resolved |
| Partial: agent run stopped at 2,410 of 3,241 | unclear | `RATE_LIMITED` | ✓ `src/scholar_harness/contracts/models.py:74` | Resume at 4 at a time; 831 records have no draft |
| Phone offline | unclear | none | n/a | Show the pairing QR again |
| Not approved | unclear | `APPROVAL_MISSING` | ✓ `src/scholar_harness/authority/binding.py:42` | Review and approve (09) |
| Coverage incomplete | unclear | `COVERAGE_INCOMPLETE` | ✓ `src/scholar_harness/screening/integrity.py:20` (maps `BATCH_INCOMPLETE` in refusals.md) | Open the unresolved rows in the queue |
| Unresolved rows at finalize | unclear | `UNRESOLVED_FINALIZE_REFUSED` | ✓ `src/scholar_harness/screening/integrity.py:24` | Decide the rows, or send them to full text |
| Batch missing | blocked | `BATCH_MISSING` | ✓ `src/scholar_harness/console/api/screening.py:471,784` (string code) | Prepare again (02) |
| Not the operator | blocked | `APPROVAL_NOT_OPERATOR` | ✓ `src/scholar_harness/authority/binding.py:43` | Approve from the desktop launcher |
| Wrong pairing code | blocked | `PAIRING_CODE_INVALID` | ✓ `src/scholar_harness/authority/pairing.py:65` | Re-enter the code on the gate |
| Non-loopback action | blocked | `ACTION_ORIGIN_REFUSED` | ✓ `screening.py:1319` | Open the app on this computer |
| Token scope | blocked | `TOKEN_SCOPE_REFUSED` | contract §7 | Connect the phone again, or use the desktop |
| Snapshot missing | blocked | `SNAPSHOT_NOT_ACCEPTED` | contract §7 | Accept the corpus (02) |
| Hidden proposal | exclude (quiet) | `PROPOSAL_HIDDEN` | contract §7 | Decide the record first |
| Idempotency | blocked | `IDEMPOTENCY_CONFLICT` | contract §7 / refusals.md | Reload; the event id was reused with other content |
| Provider | blocked | `PROVIDER_TRANSIENT`, `INVALID_OUTPUT` | ✓ refusals.md | Retry; record routes to Unclear |

Cross-cutting: loading = skeleton; offline = "as of" caption; partial = show what exists plus `missing[]`; protocol-changed = the card above.

## Desktop layout
`States` (D7): auto-fit grid of cards (min 300 px); each card is `card stack` with a badge, `heading`, body, "Affects:" caption, a `data` line carrying the code in the role colour, and actions. Codes use text colour only; `blocked` is never a fill behind text.

## Mobile layout (≤ 640 px)
One card per row; primary action full width, 44 px; same copy. The phone shows only the cards that apply to it (Engine unreachable, Conflict, Phone offline, Protocol changed, Token scope).

## Keyboard
Each card is a `section` with an `h2`; the primary action is the first focusable; `Esc` closes dialogs and returns focus to the trigger.

## Copy
`screening.state.<CODE>.{badge,title,body,affects,action1,action2}` for each code above (for example `screening.state.STALE_BINDING.title`); `screening.state.conflict.*`; `screening.state.unknown` renders the typed code verbatim.

## Accessibility
Badge text names the state; colour is never the only cue. Codes are selectable text. RTL: action order flips; codes and hashes LTR.

## Acceptance tests
Vitest: `states.copy-for-every-code.test.tsx`, `states.conflict-not-a-refusal.test.tsx`. Playwright: `screening/states.spec.ts` (stale binding, conflict, approval missing, token scope, engine unreachable).

## Open questions
None.
