# 01 Screening home    Status: FINAL; desktop built (M1b-1), phone home not built (M2) | Phase 2 Screening | Route `/screening` (desktop), `/screening` ≤ 640 px (phone home) | Milestone M1a (backend) + M1b (UI) + M2 (phone)

Boards: `Main` (D1), `MobileHome` (M1), `MobilePair` (M2, entry from the QR). Contract: `docs/architecture/screening-api-contract.md` (authoritative).

## Amended 2026-11-07 (M6-beta)
Source: `docs/roadmap/milestones/M6-beta.md` section B, decision "Details on demand", review U-13. The rule is in [12](12-details-disclosure.md). This section overrides any older sentence below.
- **The first screen is the next action and three numbers.** In order: eyebrow, h1 (the question sentence, unchanged), one line of lede, the one brand button, then three tiles: **Need you**, **Decided**, **Included so far** (`by_outcome.INCLUDE`, `screening.home.progress.includedSoFar`), and the progress bar. The Import step line and the "Export and methods" link from M5b/M5-slim stay where they are, under the button (spec 11 decisions 4 and the publication-CURRENT rule are unchanged). M3g (spec 09, researcher 2026-11-12): beside "Export and methods", the published state also links "Chase citations" to `/[locale]/discovery/chase` (`screening.home.chaseLink`), because citation chasing starts from the published includes.
- **Moved below the first screen** (document order, no layout change on phone): the Included / Excluded / Unclear badge row, the Batches table, "Who screens", the phone card, the settings line "Drafts: … · Mode: …", and the "Run from the terminal" block.
- **Moved behind Details** (12): the batch file names (rows read "Batch n"), the agent-draft count and the conflicts tile (a non-zero conflicts count still shows the conflict card above the tiles).
- **The raw `NOT_PREPARED` code leaves the card body.** The empty state reads "No batches yet. Prepare the screening batches to start." with the button "Prepare batches"; the code is inside the card's Details (shared state card, 12).
- **Published means current** (decision 2026-11-07). When a decision is made after publish, `GET /ui/publication-status` reads `STALE` (`GENERATION_STALE`, with the number of changed studies; engine ✓ done, `tests/console/test_publication_currentness.py`). Home then replaces the "Export and methods" link with the line "Published, {n} studies changed since" (`screening.home.publication.stale`) and a link "Publish again" to 09. The lede and tiles are unchanged.
- Tests: `home.compact.test.tsx` (h1, button and the three tiles come before the Batches heading in the DOM; `NOT_PREPARED` text appears only inside a `<details>`; batch file names only inside Details; stale line shows after a decision following publish). Rendered axe, en and ar, light and dark.

**Purpose.** See how far screening is, what needs you next, who is screening (the agent drafts, you decide), and connect a phone.

**Changed from the canvas.**
- Phone card text "The phone can triage and approve with the pairing code" becomes "The phone can triage; it approves on your desktop" (contract §4, approval is desktop-only in stage 1). MobileHome tab "Approve" opens a read-only PRISMA summary with "Approve on your desktop" (see 09).
- The "Who screens" third card (second screener) stays as a parked card: "Second screener · team feature, not production yet". Lane B is dropped; the lanes are the agent and you.
- The Queued-from-phone tile is shown only when the summary returns `queued_on_phones`; that field is optional in the contract and the desktop may not be able to count offline phones (D7 "Phone offline").
- Home counts never reveal the agent's call for an undecided record. "Agent proposed · needs you" counts only that a draft exists (`has_proposal`).
- "Unclear" is stored as `MAYBE` and labelled "Unclear → full text".

## Entry / exit
- Entry: primary nav "Screening"; Discovery hand-off; a refusal card (08).
- Exit: "Open triage" → 03 (phone: 04); step bar → 02 Prepare, 06 Agent proposals, 07 Agreement, 09 Publish; "Run settings" → 06; "Agreement with the agent" → 07; "1 conflict to resolve" → conflicts list (08).
- Gate: Open triage is disabled when batches are `STALE_BINDING` or absent.

## Data in
| Field | Source | Contract |
| :-- | :-- | :-- |
| total, decided, by_outcome, agent_proposed, needs_you, conflicts, queued_on_phones?, lanes | `GET /summary` ✗ M1a | contract §4 |
| per-batch coverage, binding state, unresolved rows | `GET /ui/batches` ✓ `screening.py:572` | `ui07.screening-batches-v1`, `screening-api.ts:56-76` |
| recent audit rows | `GET /ui/audit-feed` ✓ `screening.py:1173` | `ui07.audit-feed-v1` |
| conflicts to resolve | `GET /decisions/conflicts` ✗ M1a | contract §4 |
| settings (reveal after decision, mode) | `GET /settings` ✗ M1a | contract §4 |
| phone QR payload (URL + one-time token, valid 2 min, single use) | `POST /lan/session/begin` ✗ M2 (separate from approval pairing) | contract §4 |
| approval pairing state | `GET /actions/pairing/status` ✓ `screening.py:1407` | contract §4 |

## Data out
Phone access only: `POST /lan/session/begin` ✗ M2 shows the QR; `POST /lan/session/stop` ✗ M2 ("Stop phone access", revokes every phone token); the phone's own `POST /lan/pair` ✗ M2 (see 09).

**Changed from the canvas (session text).** The phone card says "valid until you close the app"; it now says: code valid for 2 minutes and one use; phone session ends at Stop phone access, when the desktop app exits, or after 12 hours. A "Stop phone access" button is added.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/ui/batches` | ✓ `screening.py:572` |
| `GET /api/v1/screening/ui/audit-feed` | ✓ `screening.py:1173` |
| `GET /api/v1/screening/actions/pairing/status` | ✓ `screening.py:1407` |
| `GET /api/v1/ui/publication-status` (reads `STALE` after a later decision, M6-beta) | ✓ `screening-api.ts:335`; currentness wrapper `screening/currentness.py` ✓ done 2026-11-07 |
| `GET /api/v1/screening/summary` | ✗ M1a |
| `GET /api/v1/screening/decisions/conflicts` | ✗ M1a |
| `GET /api/v1/screening/settings` | ✗ M1a |
| `POST /api/v1/screening/lan/session/begin` | ✗ M2 |
| `POST /api/v1/screening/lan/session/stop` | ✗ M2 |
| `POST /api/v1/screening/lan/pair` | ✗ M2 |

## States
- **Default** (amended): Literata question h1 ("1,184 of 3,241 records are decided; 2,057 still need you."), one brand button "Open triage · n need you", three tiles (Need you, Decided, Included so far) with the progress bar. Below the first screen: the outcome badge row, the batch table ("Batch n", Decided, Needs you, coverage; file names in Details), "Who screens" cards (agent as `draft` card, you, parked second screener; the agent's model and prompt hash are in the agent card's Details), the settings line, phone card with QR and code, "Run from the terminal". The draft count and the "queued from phone" tile sit in the progress card's Details.
- **Empty**: no batches → EmptyState "No batches yet" with "Prepare batches" (D7 Empty); the code `NOT_PREPARED` is in the card's Details. Refusal `SNAPSHOT_NOT_ACCEPTED` is surfaced on 02.
- **Loading**: skeleton; "Counts appear only once every file is read; no partial number is shown as final" (D7 Loading).
- **Error**: `STALE_BINDING` (✓ `integrity.py:28`) shows the Protocol-changed card (08); `ENGINE_UNREACHABLE` (client-side only) shows the Engine-unreachable card; `TOKEN_SCOPE_REFUSED` on the phone shows "Connect again".
- **Partial**: agent run partial (batch 121 running, 831 records without a draft): text "you can decide these without one". `missing[]` entries are listed, never hidden.
- **Offline**: desktop: last summary with an "as of" caption. Phone: header badge "Offline · n queued" and the tab "Queued n"; the count is the local IndexedDB queue (04).
- **Protocol-changed**: batch rows show "Protocol changed" (the code `STALE_BINDING` is in Details); the primary button becomes "See the change".
- **Protocol changed after screening started** (review F2, H-protocol-signals): when `/summary` answers `protocol_changed: true`, the h1 is "The protocol changed after screening started.", the `PROTOCOL_CHANGED_SINCE_BATCH` card (08) is shown with "Open inception", and there is no "Open triage" button (the queue would show every record as undecided).
- **Published, decisions since** (new): see the amendment; the publication status is `STALE`, the export link is hidden and "Publish again" is offered. This state cannot occur before a first publish.

## Desktop layout
`Main` (D1), reordered by the amendment: app bar with phase stepper (Full text, Synthesis, Matrix, Graph, Trust struck through with a "Not production" marker), screening step bar (Home, 1 Prepare, 2 Agent proposals, 3 Triage, 4 Agreement, 5 Publish), h1 + lede + one brand button, the three tiles with the progress bar. Everything else follows below the first screen: batches, split of "Who screens" and the phone card, terminal block. Agent card uses the draft styling (BRAND_BOOK principle 5). The first screen fits 1440 × 900 and 1024 × 768 without scrolling.

## Mobile layout (≤ 640 px)
`MobileHome` (M1): header with Connected badge; h1 "2,057 records still need you."; Today card (decided here, queued, decided in all, bar, "1,226 have an agent draft, hidden until you decide"); Connected-to-desktop card; fixed primary "Start triage" (44 px+); tab bar Home / Triage / Queued n / Approve. `MobilePair` (M2) is the first-run connect screen (see 09).

## Keyboard
`g t` triage, `g p` publish, `?` help. Focus order: skip link, phase nav, step bar, h1, primary button, progress tiles, batch table, who-screens, phone card.

## Copy (i18n keys, en master)
`screening.home.title`, `screening.home.lede`, `screening.home.cta.openTriage`, `screening.home.progress.*` (including `screening.home.progress.includedSoFar` = "Included so far"), `screening.home.batch.n` ("Batch {n}"), `screening.home.publication.stale` ("Published, {n} studies changed since"), `screening.home.publication.publishAgain` ("Publish again"), `screening.details.*` (12), `screening.home.who.agent|you|secondScreener`, `screening.home.secondScreener.parked`, `screening.home.phone.title|scan|canDo`, `screening.home.empty.noBatches`, `screening.outcome.{include,unclear,exclude,blocked}`, `screening.outcome.unclear.long` = "Unclear → full text", `screening.notProduction`.

## Accessibility
Progress bar has `role=img` with a full-sentence label. Statuses carry text, not colour alone. Parked items `aria-disabled`. Contrast pairs from tokens (`ink` on `ground`, `brand` on `brand-soft`). RTL: bars fill from the inline start; QR and hashes stay LTR; numerals Latin.

## Acceptance tests
Vitest: `screening-home.summary.test.tsx`, `screening-home.no-agent-call-leak.test.tsx`, `home.compact.test.tsx` (M6-beta). Playwright: `screening/home.spec.ts` (default, empty, stale, engine unreachable), `screening/home.mobile.spec.ts` (WebKit mobile; RTL).

## Open questions
None.
