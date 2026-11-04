# 05 Record detail (shared component)    Status: FINAL | Phase 2 Screening | Component `RecordDetail`, used in 03 and 04 | Milestone M1a (data) + M1b (UI)

Boards: `Triage` (D4), `TriageRevealed` (D5), `MobileTriage` (M3), `MobileRevealed` (M5). Brand components: `EvidenceQuote`, `DataCell`, `StatusBadge`. Contract: `screening-api-contract.md` §3-§5.

**Purpose.** Show everything needed to judge one record: abstract with criterion highlights, your checklist, and, only after you decide, the agent's draft beside it.

**Changed from the canvas.**
- Nothing structural. Spec rules added: the outcome row is the plain-code rule-table result returned by the server (`derived_outcome`); the UI never computes it.
- The draft aside never shows an `include` tint (BRAND_BOOK principle 5); the badge "Not a decision" stays.
- On the phone (M3) the checklist is absent; it is not required there; an Exclude needs a reason only (contract §9.3). On desktop the checklist answers are required.

## Entry / exit
Embedded. Prop `studyId`; emits `onDecide({outcome, reasonCode, criteria, note})`, `onSkip()` (local only), `onUndo()`. No navigation.

## Data in
| Field | Source |
| :-- | :-- |
| `title, authors, year, venue, doi, abstract, highlights[{start,end,criterion_id}], criteria[{id,text,kind}], binding, my_decision?, history[]` | `GET /records/{study_id}` ✗ M1a |
| `proposal_id, task_version, model, prompt_sha256, criteria[{id,answer,evidence{start,end,text}}], derived_outcome, reason_code, validators[], cannot_decide` | `GET /records/{study_id}/proposal` ✗ M1a; `PROPOSAL_HIDDEN` until a decision exists (blinding on) |
| criteria text (interim) | `GET /ui/batch/{n}/criterion-refs` ✓ `screening.py:1024` |
| legacy row (interim) | `GET /ui/batch/{n}/rows` ✓ `screening.py:774` |

## Data out
Via the host: `POST /decisions/events` ✗ M1a. After the reveal the host may post a superseding event (change or undo); the engine sets `changed_after_reveal`. Skip writes nothing.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/records/{study_id}` | ✗ M1a |
| `GET /api/v1/screening/records/{study_id}/proposal` | ✗ M1a |
| `GET /api/v1/screening/ui/batch/{n}/criterion-refs` | ✓ `screening.py:1024` |
| `GET /api/v1/screening/ui/batch/{n}/rows` | ✓ `screening.py:774` |

## States
- **Default (undecided)**: title (Literata), meta (year, venue, DOI link in `anchor`, `STU-` id), abstract with `hl` highlights, note "Highlighted words are tied to a criterion. The database of origin is hidden.", checklist (yes / no / not reported, 44 px chips), line "From your answers: Include · you can still choose another outcome", draft aside "Hidden until you decide" with skeleton, the recorded-as line.
- **Revealed**: checklist table with columns Criterion / You / Agent draft, row "Differs" badge on a mismatch (`unclear-soft` row), Outcome row (your badge vs agent badge incl. reason), your provenance note (`you · HUMAN · time · protocol fingerprint · proposal hash revealed after decision`), the aside with reasoning verbatim, `EvidenceQuote` cited from the abstract, model, prompt hash, proposal hash, and a sentence on where the split comes from.
- **Empty (title only)**: abstract slot "No abstract available"; badge "Title only"; text "the record goes to Unclear and on to full text; it is never excluded by default" (D7). The record is still shown; checklist answers can be "not reported".
- **Loading**: skeleton for abstract and criteria.
- **Error**: `PROPOSAL_HIDDEN` (hidden aside), `UNKNOWN_STUDY`, `STALE_BINDING` (✓ `integrity.py:28`: criteria shown read-only against the old fingerprint), `ENGINE_UNREACHABLE` (client-side).
- **Partial**: a field not stored shows "Not stored" (never filled); a proposal whose validators failed (for example `QUOTE_NOT_IN_SOURCE`, `INVALID_OUTPUT`) shows "Proposal rejected" and the failed check; `cannot_decide` shows "The agent could not decide".
- **Offline**: cached record with an "as cached" caption; proposal unavailable.
- **Protocol-changed**: banner and read-only checklist.

## Desktop layout
Zones as in D4/D5: record card, checklist card (flex 999 1 420 px), draft aside (flex 1 1 260 px); decision card below (03).

## Mobile layout (≤ 640 px)
M3 card: label with `STU-` id, Literata title 22/28, meta, abstract with highlights, `draft` strip at the bottom. M5: stacked "Your decision" card then the `draft` card. Highlights also underlined (not colour alone).

## Keyboard
`c` toggle criteria, `p` toggle the draft (after decision only), `1`/`2`/`3` set the focused criterion answer, arrows move between criteria. Answer chips are `aria-pressed` toggle buttons.

## Copy
`screening.record.meta.titleOnly`, `screening.record.highlights.note`, `screening.record.checklist.{title,yes,no,notReported,fromYourAnswers}`, `screening.record.outcome.derived`, `screening.record.compare.{title,you,agent,differs,outcome}`, `screening.record.draft.{label,hidden,notADecision,rejected,cannotDecide}`, `screening.record.provenance`, `screening.record.missingField`.

## Accessibility
Highlights are `<mark>` with a visually hidden "tied to INC-01". The aside is labelled "Agent proposal, hidden" / "revealed". `anchor` on `anchor-soft` for quotes and DOI. RTL: abstract `dir=auto`, hashes LTR.

## Acceptance tests
Vitest: `record-detail.hidden-until-decision.test.tsx`, `record-detail.draft-never-include-tint.test.tsx`, `record-detail.missing-field.test.tsx`, `record-detail.derived-outcome-from-server.test.tsx`.

## Decisions
1. Contract §9.3 (decided 2026-11-04): the phone card has no checklist; an Exclude needs a reason only. The checklist is required on desktop.
