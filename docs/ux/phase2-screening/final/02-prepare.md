# 02 Prepare and binding check    Status: FINAL | Phase 2 Screening | Route `/screening/prepare` | Milestone M0 (`accept-corpus`) + M1a (`/prepare`, settings) + M1b (UI)

Board: `Prepare` (D2, snapshot-missing state). Contract: `docs/architecture/screening-api-contract.md`.

## Amended 2026-11-07 (M6-beta)
Source: `docs/roadmap/milestones/M6-beta.md` section C and decision "Advance on decide, as a workspace setting"; review U-1.
- **The batch-size field is honoured.** `POST /prepare` passes the size to the job (✓ done 2026-11-07, `screening_v1.py:566-590`; `tests/console/test_job_runner.py::test_prepare_honours_batch_size`, 10 records at size 10 give 3 batches on the golden fixture). The size is bounded 5 to 100; outside it the route refuses `BATCH_SIZE_INVALID` (HTTP 422, contract §7), shown as "Choose a batch size from 5 to 100." (`screening.refusal.BATCH_SIZE_INVALID`, code in Details) and the field keeps the typed value. The confirm dialog's "Prepare batches of n records?" is therefore true. Field hint `screening.prepare.batch.sizeHint` = "5 to 100 records".
- **New setting: after I decide.** In the "Hidden while screening" card, below the reveal radios, a second radio group (`fieldset` + `legend`) "After I decide":
  - "Show the draft, then N" (default) ;
  - "Move on at once (drafts stay in the record's details)".
  Keys `screening.prepare.advance.{legend,draftThenNext,atOnce,noteShown}`. It is stored with the other settings (`GET`/`PUT /settings` ✓ `screening_v1.py:325,339`; the new field is ✗ M6-beta; proposed wire name `advance_on_decide` with values `show_draft_then_next` | `next_at_once`, written into the contract §4 settings row with the engine change) and journaled as `SCREENING_SETTINGS_CHANGED` with `before`/`after`. When the reveal setting is "Show beside the record" the group is disabled with the note "Drafts are already beside the record, so there is nothing to reveal." (`noteShown`). The methods paragraph reports the choice only when drafts were skipped (10).
- Tests: Vitest `prepare.advance-setting.test.tsx` (default value, change is sent through `PUT /settings`, disabled when drafts are shown), `prepare.batch-size.test.tsx` (out-of-range value shows the refusal sentence and keeps the field); Python tests as above.

**Purpose.** Verify the protocol and corpus binding, accept the corpus snapshot if missing, choose batch and reveal settings, and prepare the batches.

**Changed from the canvas.**
- None of the layout changes. Overrides applied to the content: "Hidden while screening → The agent's proposal: Reveal after my decision (default) / Show beside the record" maps to the `blinding` setting (`reveal_after_decision` | `show`).
- New block (absent on the canvas): the `mode` setting. Default `human_sees_every_record`. The opt-in `ai_agreed_exclusion` ("AI-agreed exclusion": skip records the agent calls clear exclusions) is off, needs a confirmation body, a sample-audit size, and is journaled and disclosed in the methods paragraph. Without the opt-in, the sample check on 07 does not apply.
- The outcome tiles (Include / Exclude / Unclear · full text) are a read-only view of the **plain-code rule table**; the model never derives the outcome.
- "The agent also writes one sentence of reasoning per record" stays; the agent is one lane, lane B is dropped.

## Entry / exit
- Entry: Home (01) with no batches; Discovery hand-off; "Rebind" from the Protocol-changed card (08).
- Exit: Prepare success → 01, or 06 if proposals are wanted. Gate: the "Prepare gate" panel; nothing is written until confirmed. Prepare is disabled until the snapshot is accepted.

## Data in
| Field | Source |
| :-- | :-- |
| protocol and instrument fingerprints, criteria counts, snapshot state | `GET /summary` ✗ M1a; criteria text `GET /ui/batch/{n}/criterion-refs` ✓ `screening.py:1024` (`CriterionRefs`, `screening-api.ts:102`) |
| settings (blinding, mode, sample_audit_size) | `GET /settings` ✗ M1a |
| existing batches | `GET /ui/batches` ✓ `screening.py:572` |

## Data out
- `POST /prepare` ✓ `screening_v1.py:566` with `{batch_size, shuffle_seed}` → `{job_id}`; `batch_size` is passed to the job (M6-beta, bounded 5 to 100); refuses `SNAPSHOT_NOT_ACCEPTED` and `BATCH_SIZE_INVALID`.
- `PUT /settings` ✗ M1a (blinding, mode, sample_audit_size?).
- "Accept the Discovery corpus as a snapshot": `POST /corpus/accept` ✗ M0 with `{source: "verified" | "import", import_id?}` → `{snapshot_id, studies, fingerprint}`; runs the baseline drift check; journaled with the snapshot fingerprint.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/ui/batch/{n}/criterion-refs` | ✓ `screening.py:1024` |
| `GET /api/v1/screening/ui/batches` | ✓ `screening.py:572` |
| `GET /api/v1/screening/summary` | ✗ M1a |
| `GET /api/v1/screening/settings`, `PUT /api/v1/screening/settings` | ✗ M1a |
| `POST /api/v1/screening/prepare` | ✗ M1a |
| `POST /api/v1/screening/corpus/accept` | ✗ M0 |

## States
- **Default**: binding table (Protocol Matches, Screening instrument Ready, Corpus snapshot), criteria and answers table (yes / no / not reported), rule tiles, Batches (records per batch, shuffle with recorded seed, seed), reveal setting, Prepare gate.
- **Empty (the drawn state)**: snapshot missing. Row "Corpus snapshot · none accepted" in `blocked-soft`; note "Refused: `SNAPSHOT_NOT_ACCEPTED`", affects "batch preparation only"; primary button "Accept the Discovery corpus as a snapshot · 3,241 works"; Prepare disabled with the reason ("Available once the corpus snapshot is accepted"). No log error is shown.
- **Loading**: skeleton for the binding table; Prepare shows job progress by `job_id`.
- **Error**: `SNAPSHOT_NOT_ACCEPTED` (contract §7), `BATCH_SIZE_INVALID` (✓ `screening_v1.py:577`), `STALE_BINDING` (✓ `integrity.py:28`), `ENGINE_UNREACHABLE` (client-side). Each shows code, what it affects, one next step.
- **Partial**: some batches written and others failed: list them and offer retry; prepare is idempotent for the same seed.
- **Offline**: page read-only; Prepare disabled ("needs the engine on this computer").
- **Protocol-changed**: binding row `Mismatch`; "Rebind" shown (08).

## Desktop layout
`Prepare` (D2): h1 states the blocker; split: main (Binding check card, criteria card with three rule tiles), side (Batches card, Hidden while screening card, Prepare gate panel with "Prepare 163 batches", "Preview one batch", and "Run from the terminal" `agent_screen.py prepare`). One brand button on screen: the accept button while blocked, Prepare afterwards.

## Mobile layout (≤ 640 px)
Prepare is desktop-only (the phone does not mount `/prepare`, contract §6). The phone shows nothing for this route except "Prepare on your desktop".

## Keyboard
Tab order: binding table, accept button, criteria, batch size, shuffle, seed, reveal radios, Preview, Prepare. `Enter` on Prepare opens a confirm dialog; `Esc` closes.

## Copy
`screening.prepare.title.blocked`, `screening.prepare.binding.*`, `screening.prepare.accept.cta`, `screening.prepare.answers.*`, `screening.prepare.rule.{include,exclude,unclear}`, `screening.prepare.batch.{size,shuffle,seed}`, `screening.prepare.hidden.*`, `screening.prepare.reveal.{afterDecision,beside}`, `screening.prepare.mode.{humanSeesEvery,aiAgreed}`, `screening.prepare.aiAgreed.confirm`, `screening.prepare.gate.*`, `screening.refusal.SNAPSHOT_NOT_ACCEPTED`.

## Accessibility
Checkbox/radio groups in `fieldset` + `legend`; table headers `th scope`. Blocked row uses text "Blocked" plus `blocked-soft` fill (the `blocked` colour is text/icon only). RTL: criteria text `dir=auto`; hashes LTR.

## Acceptance tests
Vitest: `prepare.snapshot-missing.test.tsx`, `prepare.rule-table-readonly.test.tsx`, `prepare.ai-agreed-needs-confirm.test.tsx`. Playwright: `screening/prepare.spec.ts` (accept snapshot then prepare the golden-uav-30 workspace; refusal copy).

## Decisions
1. Contract §9.5 (decided 2026-11-04): the methods-paragraph wording and the sample-audit size are deferred to M5-slim. The disclosure text is a placeholder until then.
