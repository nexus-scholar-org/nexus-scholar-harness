# 03 Triage queue, desktop    Status: FINAL | Phase 2 Screening | Route `/screening/triage` | Milestone M1a (events, queue) + M1b (UI); amended M6-beta, M7-method, M8-triage

Boards: `Triage` (D4, proposal hidden), `TriageRevealed` (D5, after deciding). Contract: `docs/architecture/screening-api-contract.md` §3-§4.

## Amended 2026-11-09 (M8-triage)
Source: `docs/roadmap/milestones/M8-triage.md`; the three decisions of 2026-11-09 tagged M8-triage in `docs/decisions.md` (not reopened here); mockup `.taste-skill/triage-inspect/desktop-fold.jpg`. Where a sentence further down, or in the M6-beta and M7-method sections, says otherwise, this section wins; the old sentences are struck or rewritten in place. Engine and event contract: no change.

**0. Rule.** "The checklist is a tool for the reason, not a gate for the decision."

**1. One screen, no page scroll (≥ 1024 px).**
- Amended 2026-11-09 (decision "Triage is a focus screen on desktop", second M8-triage build): at ≥ 1024 px the triage route is a focus screen. At 1440×900 and 1280×720 the page never scrolls: `document.documentElement.scrollHeight <= innerHeight`. There is **no site header and no step bar** on this route, no footer, and the shell takes exactly the viewport height. The language and theme menus are one step away, on any other screen (Home). Below 1024 px the page flows and scrolls as before (the phone is 04).
- Zones, top to bottom (≥ 1024 px):
  1. one **triage bar**, about 48 px tall, containing:
     - "Nexus Scholar" (wordmark, a link to screening Home);
     - the h1 "Triage" (`screening.triage.barTitle`);
     - the position line "Record 12 of 30 · batch 1" (`screening.triage.position`, key unchanged) with a thin progress strip of decided/total beside it (decorative, `aria-hidden`; the position line carries the meaning);
     - on the inline end: **Queue** with key hints J K (`screening.triage.queueToggle`; a toggle button with `aria-expanded` and `aria-controls` on the queue list; it replaces the "Show the whole queue"/"Hide the queue" button), **Help** with key hint ? (`screening.triage.helpButton`; opens the existing help dialog) and **Leave triage** (`screening.triage.leave`; a link to screening Home; no Esc shortcut: Esc keeps closing help and the reason panel);
  2. banners (stale binding, refusal) when present;
  3. three columns that fill the remaining height:
     - **left column, about 220 px, a counts rail**: Need you, Decided (both from `GET /summary`) and Skipped (skips in this browser session, client-side, no event), each a large number over a small label (`screening.triage.rail.{needsYou,decided,skipped}`). Under the rail sit the current and next titles (M6-beta amendment 4, kept). When Queue is open the whole list shows there, and its view is chosen from one `<select>` labelled "Show" (`screening.triage.queue.viewLabel`) with the options Needs you / Proposal ready / No proposal / Title only / Decided; this replaces the five chip buttons. The list scrolls inside the column;
     - **record pane**, unchanged: title, year and venue, Details, abstract, origin note. It scrolls inside itself, is a labelled region "Record text" (`screening.triage.recordPane`, `role="region"`) with `tabindex="0"` so the keyboard can scroll it;
     - **right column**, about 340 px, unchanged: the reason panel when open, the checklist, the comparison table after a reveal, the agent draft aside, the note, the decision history. It scrolls inside itself;
  4. a **decision bar** at the bottom that never scrolls away, unchanged. While deciding: Include (brand), Exclude, Unclear → full text, Skip, with key hints and the status line (point 4). Once decided: the outcome badge, "Saved" with its Details, Next record (N, brand), Change my decision, Undo (only when it can).
- Below 1024 px: the site header, the step bar, the title "Is this record in scope?" (`screening.triage.title`), the lede and the stacked layout stay as before; the triage bar shows at the top of the content, wrapped.
- At ≥ 1024 px the lede about the blinding setting is not shown: the draft aside already says "Hidden until you decide" or shows the draft. The all-decided lede ("Every record has your decision.") stays in the hand-off card. The live-data stamp is not shown at ≥ 1024 px.
- Adopted from the mockup: the counts rail, the progress strip and Leave triage. Not adopted: the workspace name in the bar, because no API gives it to the screen.

**2. The checklist is collapsed by default.**
- A 44 px toggle button "Your checklist · optional" (`screening.triage.checklist.toggle`; `aria-expanded`, `aria-controls`) with a one-line summary: "No answers" (`screening.triage.checklist.summaryNone`) or "{n} of {m} answered" (`screening.triage.checklist.summarySome`, `{n}`, `{m}`).
- It opens on the toggle; on **E** (to pick the reason); on **1**, **2** or **3**, which also answer the focused criterion (the first criterion by default), as before.
- Each new record opens with the checklist closed, unless the researcher opened it with the toggle: that choice is remembered for the browser session (`sessionStorage`, one key for the browser session, like the queue toggle), not stored in the workspace.
- It is a toggle button, not a Details disclosure, so rule page 12 is unchanged (no edit to 12 is needed).

**3. What is enabled.** This replaces M6-beta amendment 1's Include rule.
- **Include** needs no answers. It is disabled only while an answer the researcher gave fails a criterion: an inclusion answered no, an exclusion answered yes, or, under the protocol's `exclude` not-reported policy (M7-method), an inclusion answered "not reported".
- **Exclude** is always enabled while deciding. It needs a reason: pre-selected as the first failed criterion when the answers give one (M6-beta amendment 2 and the M7-method ordering unchanged). Otherwise the reason chips are offered with none chosen and the line "Choose a reason: press its number, then Enter" (`screening.triage.reason.choose`). Chips whose criterion is answered the other way (`FAILS-INC-n` with INC-n answered yes; `EXC-n` with EXC-n answered no) are disabled, because the engine would refuse them (`REASON_CODE_INCONSISTENT`).
- **Unclear → full text** and **Skip** are unchanged.
- Absent answers stay absent in the event: never auto-filled, never sent as `not_reported`. An Include with no answers sends an empty `criteria` list (no answers), which the engine reads as absent. The server's `derived_outcome` rule is unchanged.

**4. Status line** (`aria-live="polite"`, in the decision bar):
- a criterion fails: the existing `excludeReady` / `excludeReadyNotReported` line, followed by "Include is off while it fails." (`screening.triage.checklist.includeOff`);
- no answers: "The checklist is optional: decide now, or answer to give a reason." (`screening.triage.checklist.optional`);
- every inclusion answered yes and nothing fails: "Include is ready" (`includeReady`, kept);
- some answers, nothing fails: "{n} of {m} answered; unanswered criteria are not recorded." (`screening.triage.checklist.answeredSome`).
- Removed: `screening.triage.checklist.includeNeeds`, `includeNeedsYes`.

**5. Keyboard.** The map is unchanged (I/E/U, S, Z, N, J/K, 1/2/3, ?; Esc closes help and the reason panel; Enter confirms the chosen reason). Changes: 1/2/3 open a closed checklist and answer; E opens the checklist and the reason panel; with no failed criterion, a reason chip number then Enter excludes. Budget: Include in one keypress (I); Exclude in three (2, E, Enter, or E, chip number, Enter). Playwright `triage-desktop.spec.ts` keeps ten records by keyboard in at most 25 keypresses, with focus on the next record's title.

**6. Kept unchanged.** Position line; advance on decide (M6-beta 3); undo rules (5); the all-decided hand-off (6; it fills the record and right columns); the Details rule (12: 44 px summaries with a focus ring); the draft hidden until decided; one brand button per state.

**7. Methods paragraph:** unchanged (decision 2026-11-09).

**8. Copy** (`lib/triage-copy.ts`):
- `screening.triage.checklist.toggle`: en "Your checklist · optional"; fr "Votre grille · facultative"; ar "قائمتك المرجعية · اختيارية"
- `.summaryNone`: en "No answers"; fr "Aucune réponse"; ar "لا إجابات"
- `.summarySome`: en "{n} of {m} answered"; fr "{n} sur {m} répondus"; ar "تمت الإجابة على {n} من {m}"
- `.includeOff`: en "Include is off while it fails."; fr "Inclure est désactivé tant qu'il échoue."; ar "الإدراج معطّل ما دام المعيار غير مستوفى."
- `.optional`: en "The checklist is optional: decide now, or answer to give a reason."; fr "La grille est facultative : décidez maintenant, ou répondez pour donner un motif."; ar "القائمة اختيارية: قرّر الآن، أو أجب لتحديد السبب."
- `.answeredSome`: en "{n} of {m} answered; unanswered criteria are not recorded."; fr "{n} sur {m} répondus ; les critères sans réponse ne sont pas enregistrés."; ar "تمت الإجابة على {n} من {m}؛ المعايير دون إجابة لا تُسجَّل."
- `screening.triage.reason.choose`: en "Choose a reason: press its number, then Enter"; fr "Choisissez un motif : appuyez sur son numéro, puis Entrée"; ar "اختر سببًا: اضغط رقمه ثم Enter"
- `screening.triage.recordPane`: en "Record text"; fr "Texte de la notice"; ar "نص السجل"
- Focus bar (second M8-triage build):
  - `screening.triage.barTitle`: en "Triage"; fr "Tri"; ar "الفرز"
  - `.queueToggle`: en "Queue"; fr "File"; ar "قائمة الانتظار"
  - `.helpButton`: en "Help"; fr "Aide"; ar "مساعدة"
  - `.leave`: en "Leave triage"; fr "Quitter le tri"; ar "مغادرة الفرز"
  - `.rail.needsYou`: en "need you"; fr "à traiter"; ar "بانتظارك"
  - `.rail.decided`: en "decided"; fr "décidées"; ar "تم البتّ فيها"
  - `.rail.skipped`: en "skipped"; fr "passées"; ar "متخطّاة"
  - `.queue.viewLabel`: en "Show"; fr "Afficher"; ar "عرض"

**9. Tests.**
- Vitest: `triage.decisive.test.tsx` (rewritten for the new Include rule); `triage.collapsed-checklist.test.tsx` (closed by default; opens on the toggle, on E and on 1/2/3; Include with no answers sends no `criteria`; the session choice is remembered); `triage.reason-from-checklist.test.tsx` (extended: no failed criterion means no chip chosen, a chip then Enter excludes; contradicting chips are disabled); `triage.not-reported-policy.test.tsx` (kept).
- Vitest `triage.position and the collapsed queue` now uses the Queue toggle. New `triage.focus-bar`: the bar with h1 "Triage"; Queue toggles the list; Help opens the dialog; Leave links to Home; the rail counts; Skipped counts a skip; the view select changes the view.
- Playwright `screening/triage-desktop.spec.ts`: no page scroll at 1440×900 and 1280×720 on `/screening/triage` with a long abstract, and the record pane scrolls instead (the no-scroll tests stand); the 25-keypress budget; axe with no violation in light and dark. `shell.spec.ts`: the language-switch test moves to `/screening/home`, because desktop triage has no site header.

## Amended 2026-11-07 (M6-beta)
Source: `docs/roadmap/milestones/M6-beta.md` section A and B; decisions "Answer until decisive", "Advance on decide, as a workspace setting", "Details on demand"; review U-4 to U-8, S-P1-3. Where a sentence further down says otherwise, this section wins; the old sentences are struck or rewritten in place.

**1. Answer until decisive.** The checklist is no longer all-or-nothing.
- **Exclude** is enabled as soon as one criterion fails: an inclusion criterion answered no, or an exclusion criterion answered yes.
- ~~**Include** is enabled when every inclusion criterion is answered yes and no exclusion criterion is answered yes. Exclusion criteria left unanswered do not block it.~~ Amended 2026-11-09 (M8-triage 3): Include needs no answers; it is disabled only while an answer fails a criterion.
- **Unclear → full text** is always enabled. **Skip** is unchanged.
- A criterion left unanswered is **absent** from the event's `criteria`. It is never sent as `not_reported`: that value is sent only when the reviewer presses "Not reported" on that criterion, because it claims the reviewer looked and found nothing.
- The line under the checklist replaces "Answer every criterion before deciding" (`screening.triage.checklist.required`, removed). It is a status line, `aria-live="polite"`:
  - one criterion fails: "Exclude is ready: INC-01 answered no" (`screening.triage.checklist.excludeReady`, `{id}`, `{answer}`); with an exclusion criterion: "Exclude is ready: EXC-02 answered yes";
  - ~~nothing fails and inclusion answers are missing: "Include needs INC-02 and INC-03" (`includeNeeds`, `{ids}`);~~ removed (M8-triage 4);
  - ~~an inclusion answered "not reported" counts as not yet yes: "Include needs INC-02 to be yes";~~ removed (`includeNeedsYes`); the lines are now those of M8-triage 4;
  - Include ready: "Include is ready" (`screening.triage.checklist.includeReady`, kept).
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
- The queue card is **collapsed by default**: ~~the view chips plus~~ two rows, the current title and the next title (`screening.triage.queue.current`, `.next`). ~~A toggle button "Show the whole queue" / "Hide the queue" (`screening.triage.queue.expand`, `.collapse`, `aria-expanded`, `aria-controls`) expands it;~~ Superseded 2026-11-09 by M8-triage point 1: the Queue toggle in the triage bar opens it, and the view is chosen from one "Show" select instead of chips. The first **J** or **K** still opens the queue. The choice is remembered for the browser session (`sessionStorage`, key per workspace), not stored in the workspace. ~~The toggle and the chips are 44 px.~~

**5. Undo only when it can.** **Z** and the Undo button are absent until the record has a superseding target (`undoTarget` returns a value). The copy "A first decision cannot be undone; change it instead." (`undoUnavailable`) is removed. "Change my decision" stays.

**6. All decided is a hand-off.** When the "Needs you" view is empty the centre shows the heading "All 30 records are decided" (`screening.triage.allDecided.title`, `{total}`), then **Publish** as the one brand button (link to 09) and **Agreement** as a text link (07). The draft aside is not rendered. The lede stops describing the blinding setting and reads "Every record has your decision." (`screening.triage.allDecided.lede`). The Home link remains. If a conflict is open or the binding is stale, the card above it is shown and Publish is replaced by "See the change" or by the conflict card's action.

**7. Details (12).** The record's study id and the raw DOI; the "Recorded as you · HUMAN · time · protocol sha" line; event ids; the refusal code in banners; and, in the draft aside, model, prompt hash and proposal id move behind one "Details" per card. The decision card keeps one word, "Saved", with the time on hover.

- Tests: `triage.decisive.test.tsx`, `triage.reason-from-checklist.test.tsx`, `triage.advance-on-decide.test.tsx`, `triage.position.test.tsx`, `triage.undo-hidden.test.tsx`, `triage.all-decided.test.tsx`, `triage.details.test.tsx`. Playwright at 1440 and 1024 for the collapsed queue.

## Amended 2026-11-08 (M7-method)
Source: `docs/decisions.md` 2026-11-08 "Method parameters move into the protocol". Extends amendment 1 ("Answer until decisive"); where it says an inclusion answered "not reported" only counts as not yet yes, this section wins when the policy is `exclude`.
- **The screen reads the policy.** `not_reported_policy` (`"unclear"` default | `"exclude"`, from the protocol's `method.not_reported`) comes with `GET /settings` and with `GET /records/{study_id}` (✗ M7-method; the screen never reads `protocol.json`). With `"unclear"` nothing changes.
- **Policy `exclude`.**
  - An inclusion criterion answered "not reported" counts as failing: **Exclude is ready**, with the reason pre-selected as `FAILS-INC-n` (amendment 2 wording: "Fails INC-02 · …").
  - A **definite failure outranks a not-reported inclusion** for the reason shown: an inclusion answered no or an exclusion answered yes comes first (protocol order among them); not-reported inclusions follow (protocol order among them). The other codes stay as chips.
  - An **exclusion criterion answered "not reported" never fails**; it does not enable Exclude.
  - Status line (`aria-live="polite"`): "Exclude is ready: INC-02 not reported (your protocol excludes when not reported)" (`screening.triage.checklist.excludeReadyNotReported`, `{id}`). When a definite failure exists, the existing `excludeReady` line names that failure instead. This line is followed by "Include is off while it fails." (M8-triage 4); the "Include needs …" lines are removed.
  - **Include**: ~~it needs every inclusion yes and no exclusion yes~~ (M8-triage 3) needs no answers and is disabled while an inclusion is answered "not reported" under this policy. **Unclear → full text** and Skip stay always enabled. The server's `derived_outcome` follows the same policy; the reviewer's own decision is never overridden, and "you can still choose another outcome" is kept. The model never derives the outcome.
- **Events.** "Not reported" is still sent as `not_reported` only when the reviewer presses it; unanswered stays absent. Under `exclude`, `REASON_CODE_INCONSISTENT` (amendment 2) must accept `FAILS-INC-n` for a criterion answered `not_reported` (✗ M7-method with the policy); under `unclear` it is as before.
- **Logic.** `lib/triage-logic.ts` `decisiveFor('EXCLUDE')` takes the policy as an argument; `lib/triage-copy.ts` picks the line.
- Copy (key `screening.triage.checklist.excludeReadyNotReported`):
  - en: "Exclude is ready: {id} not reported (your protocol excludes when not reported)"
  - fr: "Exclure est prêt : {id} non rapporté (votre protocole exclut ce qui n'est pas rapporté)"
  - ar: "الاستبعاد جاهز: {id} غير مُبلَّغ عنه (يستبعد بروتوكولك ما لم يُبلَّغ عنه)"
- Tests: `triage.not-reported-policy.test.tsx` (exclude policy: not-reported inclusion enables Exclude with `FAILS-INC-n`; definite failure outranks it; not-reported exclusion does not enable Exclude; Include is disabled by a not-reported inclusion and needs no answers otherwise (M8-triage 3); unclear policy leaves all as today; choosing Unclear is possible). Python: `tests/test_screening_events.py` for the policy in `derived_outcome` and the consistency check.

**Purpose.** Decide every record: read it, choose Include / Exclude / Unclear → full text, answer the checklist when it helps give a reason (M8-triage), and move on by keyboard.

**Changed from the canvas.**
- Canvas D4/D5 already hide the proposal until you decide and show the queue as all records (chips Proposal ready / No proposal / Title only). Kept.
- **Skip** (S) is a client-side deferral and writes **no event** (canvas shows it as an action; it is not a decision).
- **Changing a decision after the reveal** ("Change my decision", D5) is allowed as a superseding event; the engine sets `changed_after_reveal` (contract §3.1). **Undo** (Z) is also a superseding event; it appears only once the record has something to undo (amendment 5).
- ~~The checklist answers (yes / no / not reported) are **required** on desktop.~~ Amended: ~~answers are taken until the decision is decisive (amendment 1);~~ the checklist is optional and collapsed by default (M8-triage 2 and 3); unanswered criteria are absent, never `not_reported`. The "From your answers: Include" line is the server's plain-code rule-table result; "you can still choose another outcome" is kept. The model never derives the outcome.
- Chip filters that reveal the agent's call (D5 "Differs" on the compared record, and any "agent disagrees" view) exist only for records you have already decided (`GET /queue` with `decided=true`).
- A queue ordering by the agent's uncertainty is available after a proposals run: `GET /queue?order=agent_uncertainty` ✗ M1a. It orders without revealing the agent's call, and the methods paragraph discloses it (see 06). Default ordering is the seeded order. A decision on a study with an open conflict returns the per-event result `conflict` (no separate refusal code).
- The canvas "Unclear" button reads "Unclear" with a tooltip; the label everywhere else is "Unclear → full text" (stored `MAYBE`).

## Entry / exit
- Entry: Home (01) "Open triage"; step bar; `g t`.
- Exit: queue empty → 09 (brand button) or 07 (link), see amendment 6. Gate: decisions are disabled when the binding is `STALE_BINDING`.

## Data in
| Field | Source |
| :-- | :-- |
| rail counts Need you, Decided (Skipped is client-side) | `GET /summary` |
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
- **Default (D4)** (amended): h1 "Is this record in scope? Decide first; the agent's draft opens after." "Record 12 of 30 · batch 1" above the record. Layout as in M8-triage 1 (at ≥ 1024 px: triage bar with h1 "Triage", no page scroll; the h1 above applies below 1024 px). Left column: counts rail (need you, decided, skipped) over the current and next titles; Queue opens the whole list with the "Show" select. Centre record pane with highlights; right column with "Your checklist · optional" (collapsed, M8-triage 2; chip answers when opened) and the status line in the decision bar ("Exclude is ready: INC-01 answered no. Include is off while it fails."); right `draft` aside "Agent proposal · draft · Hidden until you decide" with skeleton bars (model, prompt hash and date in its Details); decision card: Include (brand), Exclude, Unclear, Skip with key hints (Undo only when it can); on Exclude the pre-selected reason in words and the other reasons as chips; after a decision "Saved" (the recorded-as line is in Details).
- **Revealed (D5)**: h1 "You included it. The agent's draft said exclude, on INC-03." Queue row tagged "Included by you". Table "Your checklist beside the agent's" with a "Differs" badge row and an Outcome row; the draft aside shows outcome "Exclude · fails INC-03" with "Not a decision", the reasoning verbatim, the abstract quote; model, prompt hash and proposal id are in the aside's Details. Actions: Next record (N, brand), Change my decision, Undo (only when it can), Decision history. Reached only when the record has a draft and the setting is "show the draft, then N".
- **Empty**: all decided → the hand-off of amendment 6 ("All 30 records are decided", Publish brand button, Agreement link); zero batches → link to 02 (D7 Empty).
- **Loading**: skeleton rows and record (D7 Loading); next 5 records prefetched.
- **Error**: `PROPOSAL_HIDDEN` (no error styling, the hidden aside), `REASON_CODE_INVALID`, `REASON_CODE_INCONSISTENT` (✗ M6-beta, plain sentence on the card, code in Details), `UNKNOWN_STUDY`, `STALE_BINDING` (✓ `integrity.py:28`), `IDEMPOTENCY_CONFLICT`, `TOKEN_SCOPE_REFUSED`, `ENGINE_UNREACHABLE` (client-side; "Your last n decisions are held in this tab").
- **Partial**: event result `conflict` → row badge "Conflict" (`unclear`), record locked until chosen; `duplicate` is silent. Proposal rejected by a validator is shown as "Proposal rejected" with the failed check.
- **Offline**: decisions queue locally (IndexedDB) and flush with backoff; proposal reads unavailable; badge shows the count.
- **Protocol-changed**: banner "Batches no longer match the protocol", decisions disabled, existing decisions kept (08).

## Desktop layout
~~Canvas D4/D5: three zones (queue 260 px, record and checklist, draft aside)~~ Amended 2026-11-09: three columns (counts rail and titles about 220 px, record pane, right column about 340 px) under a 48 px triage bar and a fixed decision bar, filling the viewport with no page scroll (M8-triage 1). Compact density, one brand button per screen: Include in D4, Next record in D5. The `draft` surface is plain `surface`, never an `include` tint until a person verifies.

## Mobile layout (≤ 640 px)
See 04.

## Keyboard
`I` Include, `E` Exclude (opens the checklist and the reason panel; reason pre-selected when a criterion fails, else none; `Enter` confirms it, chips 1-7 choose another), `U` Unclear → full text, `S` Skip (deferral), `Z` Undo (only when available), `N` next record (after a reveal), `J`/`K` queue (the first press expands the collapsed queue), `1`/`2`/`3` yes/no/not reported on the focused criterion (and open a closed checklist), `?` help, `Esc` closes help and the reason panel. Budget: Include one keypress, Exclude three (M8-triage 5). Shortcuts are off in text fields. After a decision focus moves to the revealed heading, then to Next record.

## Copy
`screening.triage.title` (below 1024 px), `screening.triage.lede` (below 1024 px), `screening.triage.{barTitle,queueToggle,helpButton,leave}`, `screening.triage.rail.{needsYou,decided,skipped}`, `screening.triage.queue.viewLabel`, `screening.triage.queue.hiddenRow`, `screening.triage.checklist.*`, `screening.triage.proposal.{hiddenTitle,hiddenBody,draftLabel,notADecision,differs}`, `screening.triage.decision.{include,exclude,unclear,skip,undo,change,next,history}`, `screening.triage.reason.*` (including `.fails`, `.meets`), `screening.triage.checklist.{excludeReady,excludeReadyNotReported,includeReady,includeOff,optional,answeredSome,toggle,summaryNone,summarySome}`, `screening.triage.reason.choose`, `screening.triage.recordPane`, `screening.triage.position`, `screening.triage.queue.{current,next}`, `screening.triage.allDecided.{title,lede}`, `screening.triage.announce.savedNext`, `screening.refusal.REASON_CODE_INCONSISTENT`, `screening.details.*` (12; replaces `screening.triage.recordedAs` on the card), removed: `screening.triage.queue.{expand,collapse}`, `screening.triage.queue.chip.{proposalReady,noProposal,titleOnly}`, `screening.triage.checklist.required`, `screening.triage.checklist.includeNeeds`, `includeNeedsYes`, `undoUnavailable`, `screening.triage.revealed.title.{agrees,differs}`, `screening.outcome.unclear.long`.

## Accessibility
Decision buttons show text and a key hint. Queue is a list with `aria-current`; the Queue toggle has `aria-expanded`/`aria-controls`; the view select is labelled "Show"; the progress strip is `aria-hidden`. Live region announces "Decision saved", "Queued", "Conflict". Draft aside is labelled "Agent proposal, hidden" / "revealed". Answer chips are 44 px. Contrast per tokens: `include`/`unclear`/`blocked` as text and icon colour on their `-soft` fills only. RTL: queue card flips to the inline end; key hints Latin.

## Acceptance tests
Vitest: `triage.keymap.test.tsx`, `triage.blinding-no-proposal-field.test.tsx`, `triage.skip-writes-no-event.test.ts`, `triage.undo-superseding.test.ts`, `triage.changed-after-reveal.test.ts`, the M6-beta tests listed in that amendment (`triage.decisive` rewritten) and the M8-triage tests (amendment 9: `triage.collapsed-checklist`, extended `triage.reason-from-checklist`, no page scroll at 1440×900 and 1280×720, 25-keypress budget, axe in light and dark). Playwright: `screening/triage-desktop.spec.ts` (golden-uav-30 end to end, proposal hidden until decision, conflict visible, replay idempotent).

## Open questions
None.
