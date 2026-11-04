# 07 Agreement with the agent    Status: DRAFT | Phase 2 Screening | Route `/screening/agreement` | Milestone M1b (`GET /agreement` and UI)

Board: `Agreement` (D6). Contract: `screening-api-contract.md`.

**Purpose.** After deciding, see how your decisions and the agent's drafts agree and where they split. Descriptive only.

**Changed from the canvas.**
- The "Sample check of agreed exclusions" card applies **only when the AI-agreed-exclusion opt-in is on** (`mode: ai_agreed_exclusion`). By default you see every record, and the card reads "You saw every record. No sample needed." The canvas draws the card unconditionally as a fatigue check; that is overridden.
- The kappa tile renders the server's `kappa: null` and `kappa_note`; agreement counts only decisions made before the reveal.
- Kappa tile: shown **greyed** with the note "needs a second human screener · not production" (the canvas has "Parked" and "Kappa is reported only between two human screeners"; wording aligned to the maintainer decision).
- Agreement counts only records you have decided; nothing reveals the agent's call on an undecided record (blinding).
- Headline numbers come from the server. "Unclear on either side" counts `MAYBE` ("Unclear → full text").

## Entry / exit
- Entry: step bar "4 Agreement"; Home link; reachable at any time for the records decided so far ("so far").
- Exit: "Open the 9 missed includes" → 03 (decided view, filtered); Publish → 09.

## Data in
| Field | Source |
| :-- | :-- |
| `{decided_with_proposal, agreement_pct, table_2x2, splits_by_criterion, unclear_either_side, kappa: null, kappa_note}`; counts only decisions made before the reveal | `GET /agreement` ✗ M1b |
| decided records where the agent differs | `GET /queue?view=decided` ✗ M1a (agent-reveal views need `decided=true`) |
| settings (mode, sample size) | `GET /settings` ✗ M1a |
| counts | `GET /summary` ✗ M1a |

## Data out
Sample-check results (opt-in only): decision events by `POST /decisions/events` ✗ M1a with a re-look on each sampled study; a wrong exclusion posts a superseding event. The report is written to `literature/prisma_screening_report.md` at publish and recomputed from the decision files each time it opens (D6 caption).

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/summary` | ✗ M1a |
| `GET /api/v1/screening/queue?view=decided` | ✗ M1a |
| `GET /api/v1/screening/settings` | ✗ M1a |
| `POST /api/v1/screening/decisions/events` | ✗ M1a |
| `GET /api/v1/screening/agreement` | ✗ M1b |

## States
- **Default (D6)**: h1 "You and the agent agreed on 95.9% of records; it would have dropped 9 of your includes." Lede states "Not an inter-rater statistic: the agent is not a second reviewer." Four cards: Agreement with the agent, Your includes it proposed to exclude (`unclear` accent, "the number that matters most"), Its includes you excluded, Unclear on either side. 2x2 table with disagreement cells in `unclear-soft`; criterion bars (INC-03 first); the greyed kappa card; sample-check card.
- **Empty**: nothing decided → "Decide some records first". No proposals run → "No agent proposals to compare" with a link to 06.
- **Loading**: skeleton cards and table.
- **Error**: `PROPOSAL_HIDDEN` shown as "Available after you decide this record" (not an error), `STALE_BINDING` (✓ `integrity.py:28`), `ENGINE_UNREACHABLE` (client-side).
- **Partial**: only part decided → every card is captioned "of n decided so far"; records without a proposal count as "no proposal", not as disagreement.
- **Offline**: last read kept with an "as of" caption; sample check disabled.
- **Protocol-changed**: concordance against the old fingerprint shows a stale banner and is excluded from the publish report.

## Desktop layout
`Agreement` (D6): h1 + lede, four cards, split main (matrix, criterion bars) and side (kappa card, sample check, report path caption). Tables use `th scope`; numbers tabular. One brand button: "Start the sample check · 60 records" when the opt-in is on; otherwise the screen has no brand button and the step bar leads to Publish.

## Mobile layout (≤ 640 px)
Not a phone route in stage 1. Phone Home shows no agreement data.

## Keyboard
Tab: cards, matrix cells (each links to the filtered decided view), criterion bars, kappa card (focusable, disabled), sample-check button.

## Copy
`screening.agreement.title`, `screening.agreement.lede`, `screening.agreement.notInterRater`, `screening.agreement.cards.*`, `screening.agreement.matrix.*`, `screening.agreement.byCriterion`, `screening.agreement.kappa.disabled` = "needs a second human screener · not production", `screening.agreement.sample.{title,body,start,notNeeded}`, `screening.outcome.unclear.long`.

## Accessibility
Matrix is a real table; bars have value text; disabled kappa card uses `aria-disabled` and keeps text contrast ≥ 4.5:1 (grey is by `exclude`, not reduced opacity on text). RTL: matrix mirrored; numerals Latin.

## Acceptance tests
Vitest: `agreement.no-kappa-value.test.tsx`, `agreement.sample-only-with-optin.test.tsx`, `agreement.no-undecided-leak.test.tsx`. Playwright: `screening/agreement.spec.ts`.

## Open questions
1. Contract §9.5: default and minimum sample-audit size for the opt-in sample check (canvas draws 60).
