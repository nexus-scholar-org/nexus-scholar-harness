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

## Amended 2026-11-08 (M7-method)
Source: `docs/decisions.md` 2026-11-08 "Method parameters move into the protocol" (accepted by the researcher). Where a sentence above or below says the blinding setting is always editable, this section wins for protocols that set it.
- **Blinding can be set by the protocol.** `protocol.json` may carry an optional `method` block with `blinding` (`reveal_after_decision` default | `show`). `GET /settings` returns `blinding_source: "protocol" | "settings"` (✗ M7-method; `"protocol"` only when the block sets blinding, otherwise `"settings"`; the `blinding` value returned is the effective one). Batch size stays a Prepare setting, unchanged.
- **Source `"settings"` (no block): behaviour unchanged.** The reveal radios are editable and `PUT /settings` journals `SCREENING_SETTINGS_CHANGED` as today.
- **Source `"protocol"`: read-only with its reason.** The reveal radio group (`fieldset` + `legend`, unchanged) is replaced by the same two options rendered read-only: the effective value is shown selected, the other is not selectable, and the line "Set by your protocol" sits under the legend. It must not look like a disabled control without a reason: the line is visible text (not a tooltip), `ink-2` on `surface`, linked with `aria-describedby` from the group; the group carries `aria-readonly="true"`, stays in the tab order as a single stop, and the radios are not given the dimmed disabled treatment. There is no link to the protocol in this milestone; it is deferred until a protocol screen exists (the app has none). No journal row is written by viewing it.
- **Refusal.** `PUT /settings` with a `blinding` value that differs from the effective one while the source is `"protocol"` is refused `BLINDING_SET_BY_PROTOCOL` (HTTP 409, ✗ M7-method; contract §7 and `console/refusals.py` in the same change; a `PUT` that repeats the current value, or changes only other fields, is accepted). Sentence: "Your protocol sets this. Change the protocol to change it." (`screening.refusal.BLINDING_SET_BY_PROTOCOL`; code in Details). The UI does not send the change, so the refusal is reached only by a stale tab or another client; the control is then refreshed read-only.
- **"After I decide" still applies** to the effective blinding value: when it is `show` (from the protocol or the setting) the group is disabled with `noteShown`, as above.
- **Protocol-changed.** If the protocol changes (or gains or loses a `method` block) the binding row reads Mismatch and the source is re-read after Rebind.
- **The rule table follows `not_reported_policy`.** The read-only tiles (`ruleUnclear`, `ruleExclude`, `ruleInclude` in `components/screening-prepare.tsx`) read `not_reported_policy` from `GET /settings` (✗ M7-method). With `"unclear"` the three lines are unchanged. With `"exclude"` the three `...ExcludePolicy` variants below replace them: Unclear is only for a failed check or an undecided agent; Exclude covers any exclusion yes, any inclusion no, or any inclusion not reported; an exclusion not reported never fails, so Include is every inclusion yes and no exclusion yes. The tiles stay a read-only view of the engine's plain-code table; the model never derives the outcome.
- Copy (keys `screening.prepare.blinding.setByProtocol`, `screening.refusal.BLINDING_SET_BY_PROTOCOL`; the three rule keys sit beside `ruleUnclear` / `ruleExclude` / `ruleInclude`):
  - en: "Set by your protocol" / "Your protocol sets this. Change the protocol to change it."
  - fr: "Défini par votre protocole" / "Votre protocole fixe ce réglage. Modifiez le protocole pour le changer."
  - ar: "محدَّد في بروتوكولك" / "يحدد بروتوكولك هذا الإعداد. عدّل البروتوكول لتغييره."
  - `ruleUnclearExcludePolicy` en: "First, Unclear → full text: a check on the draft failed or the agent could not decide." fr: "D'abord, Incertain → texte intégral : une vérification du brouillon a échoué ou l'agent n'a pas pu trancher." ar: "أولًا، غير واضح ← النص الكامل: فشل فحص المسودة أو لم يستطع الوكيل الحسم."
  - `ruleExcludeExcludePolicy` en: "Otherwise exclude: any exclusion criterion answered yes, any inclusion criterion answered no, or any inclusion criterion not reported." fr: "Sinon, exclure : un critère d'exclusion à oui, un critère d'inclusion à non, ou un critère d'inclusion non rapporté." ar: "وإلا فاستبعد: أي معيار استبعاد جوابه نعم، أو أي معيار تضمين جوابه لا، أو أي معيار تضمين غير مُبلَّغ عنه."
  - `ruleIncludeExcludePolicy` en: "Otherwise include: every inclusion yes and no exclusion yes." fr: "Sinon, inclure : tous les critères d'inclusion à oui et aucun critère d'exclusion à oui." ar: "وإلا فضمِّن: كل معايير التضمين نعم ولا معيار استبعاد جوابه نعم."
- Tests: Vitest `prepare.blinding-from-protocol.test.tsx` (source `protocol` renders the value read-only, the reason line is in the DOM and referenced by `aria-describedby`, no radio is `disabled`; source `settings` stays editable and sends `PUT`), `prepare.advance-setting.test.tsx` extended (disabled when the protocol sets `show`), `prepare.rule-table-policy.test.tsx` (policy `unclear` renders the three existing lines; policy `exclude` renders the three `ExcludePolicy` lines and none of the old ones). Python `tests/console/test_screening_v1_api.py::test_blinding_set_by_protocol_refuses_change` (409 `BLINDING_SET_BY_PROTOCOL`, no journal row; no block gives `blinding_source: "settings"` and the change is accepted).

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
