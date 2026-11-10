# 04 Triage, mobile    Status: FINAL, not built (M2) | Phase 2 Screening | Route `/screening/triage` (≤ 640 px, LAN sub-app) | Milestone M2 (on M1a routes)

Boards: `MobileTriage` (M3), `MobileReason` (M4), `MobileRevealed` (M5), `MobileOffline` (M6). Rules: production plan §4. Contract: `docs/architecture/screening-api-contract.md` §3, §6.

**Purpose.** Screen one record at a time on a phone, reliably, even if the connection drops.

**Changed from the canvas.**
- **Swipe is physical in RTL too**: right is Include, left is Exclude, up is Unclear. The hints on screen say it in words ("Swipe right · Include"), and the arrows do not mirror.
- **Skip** is a button and a client-side deferral; it writes no event.
- M5 "Undo" toast (5 s) posts a superseding event. Later undo from the record history is allowed, also as a superseding event.
- Canvas M3 shows no checklist on the phone. The contract makes `criteria` optional on a swipe; the phone does not need it; an Exclude needs a reason only (contract §9.3).
- The phone exposes only the restricted routes of contract §6; the Settings, Prepare, Proposals and Publish routes are not mounted on the LAN sub-app.
- "Unclear" on the button; the long label "Unclear → full text" is used in text, sheet and provenance (stored `MAYBE`).
- The M5 reveal of the agent draft appears only after the decision is recorded.

## Entry / exit
- Entry: Home (01 phone) "Start triage" or Triage tab.
- Exit: back to Home; "Next record". Gate: an expired or reused phone token → connect again (`TOKEN_SCOPE_REFUSED`).

## Data in
Through the phone-scope routes only: `GET /queue` ✗ M1a, `GET /records/{study_id}` ✗ M1a, `GET /records/{study_id}/proposal` ✗ M1a (after a decision), `GET /summary` ✗ M1a, `GET /decisions/conflicts` ✗ M1a, `GET /prisma/preview` ✗ M1a.

## Data out
`POST /decisions/events` ✗ M1a with `device: "phone"`, client `event_id` minted at the tap; events wait in the IndexedDB queue and are replayed oldest first. `duplicate` → drop the local copy; `conflict` → conflict card; `refused` → keep and show the code. `POST /decisions/conflicts/{study_id}/resolve` ✗ M1a for "Keep Exclude / Keep Include". Pairing: `POST /lan/pair` ✗ M2 (09).

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/queue`, `/records/{study_id}`, `/records/{study_id}/proposal`, `/summary`, `/decisions/conflicts` | ✗ M1a (mounted on the LAN sub-app in M2) |
| `POST /api/v1/screening/decisions/events` | ✗ M1a |
| `POST /api/v1/screening/decisions/conflicts/{study_id}/resolve` | ✗ M1a |
| `POST /api/v1/screening/lan/pair` | ✗ M2 |

## States
- **Default (M3)**: top bar Home + offline badge; "40 today · 2,055 need you", batch, bar; hint "Swipe up · Unclear"; swipe card (record id, Literata title, meta, abstract with highlights, `draft` strip "Agent proposal · draft · hidden until you decide"); hints "← Exclude", Skip, "Include →"; footnote "A swipe commits at 40% of the way; you get 5 s to undo."; bottom bar Exclude / Unclear / Include (Include brand).
- **Reason sheet (M4)**: modal bottom sheet "Why does this record go?" with a radio group of protocol codes (Fails INC-01..03, EXC-01 ..., "More: Fails INC-04 · EXC-02 · EXC-03"), optional note, button "Exclude · EXC-01" (52 px). One tap picks; the reason is required (`REASON_CODE_INVALID` otherwise). Footer "Queued on this phone until it reconnects" when offline.
- **Revealed (M5)**: "You excluded it. The agent's draft agrees." Your decision card (badge, provenance line with proposal hash revealed after decision) and the `draft` card (outcome, reasoning verbatim, abstract quote, model, prompt hash, date); toast "Excluded · EXC-01 · undo for 5 s" with Undo; primary "Next record".
- **Empty**: "All records decided" with a link to Home.
- **Loading**: skeleton card; next 5 records prefetched.
- **Error**: `TOKEN_SCOPE_REFUSED` (expired or wrong scope), `PROPOSAL_HIDDEN` (hidden strip, not an error), `UNKNOWN_STUDY`, `STALE_BINDING`.
- **Partial**: some queued events accepted, others `conflict` or `refused`: the Queued screen lists what remains.
- **Offline (M6)**: "3 decisions queued · will send when connected." Each queued row shows title, time and outcome badge. Text: "They are sent once, in order. Keep this page open: reloading while offline loses the queue" (no service worker without HTTPS). Primary "Try to send now".
- **Conflict (M6)**: card "This record was decided on both devices." with the phone and desktop decisions and times; "Neither counts until you choose; the other is kept as superseded"; buttons Keep Exclude / Keep Include. Never auto-resolved.
- **Protocol-changed**: decisions disabled with "Protocol changed on the desktop"; the queue is kept.

## Desktop layout
See 03.

## Mobile layout (≤ 640 px)
390 x 844 reference. One card; bottom action bar thumb-reachable; all targets ≥ 44 px (sheet buttons, undo, Keep buttons); comfortable density only. Gestures: right = Include, left = Exclude, up = Unclear, commit at 40 % travel, tint plus text label on drag; button equivalents for every gesture.

## Keyboard
External keyboard on tablets: same keys as 03 (`I E U S Z`). Sheet: arrow keys pick a reason, `Enter` confirms, `Esc` closes.

## Copy
`screening.mobile.header.today`, `screening.mobile.swipe.{hintUp,hintLeft,hintRight}` (words, not arrows), `screening.mobile.swipe.commitNote`, `screening.mobile.proposal.hiddenStrip`, `screening.mobile.reason.{eyebrow,title,more,note,confirm}`, `screening.mobile.revealed.{excluded,included,unclear}.{agrees,differs}`, `screening.mobile.undo.toast`, `screening.mobile.offline.{title,body,send}`, `screening.mobile.conflict.{title,body,keepExclude,keepInclude}`, `screening.outcome.unclear.long`.

## Accessibility
Every swipe has a button path. Toast is `role=status`; undo also reachable from the decision history. Sheet is `role=dialog` with a labelled radiogroup. RTL: text mirrors, swipe directions do not (right Include, left Exclude, stated on screen); verify in Playwright at mobile width in `ar`. Reduced motion: no swipe animation, tint only.

## Acceptance tests
Vitest: `record-card.swipe-physical-rtl.test.tsx`, `offline-queue.replay-once.test.ts`, `skip-writes-no-event.test.ts`. Playwright (WebKit mobile emulation): `screening/triage-mobile.spec.ts` (30 decisions with the network cut mid-run, all replayed once; a conflict surfaced; jobs and pipelines unreachable over LAN; `ar` layout).

## Decisions
1. Contract §9.3 (decided 2026-11-04): an Exclude on the phone requires a reason; an Include or Unclear requires nothing more. No checklist on the phone.
2. Contract §9.4 (decided 2026-11-04): 200 events per request; the UI replays an offline backlog in chunks of 200, each retried on its own.
