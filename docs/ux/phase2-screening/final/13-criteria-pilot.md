# 13 Criteria pilot and revision    Status: DRAFT | Phase 2 Screening | Route `/screening/pilot?id=pilot_001` (the result); entries on `/screening/prepare` and `/screening/triage` | Milestone M11b-criteria-pilot (part B engine, part C this screen)

Boards: none of its own; the screen follows `Prepare` (D2) and `Triage` (D4) as amended in `02-prepare.md` and `03-triage-desktop.md`, and `Agreement` (D6) for the per-criterion read. Contract: `docs/roadmap/milestones/M11b-criteria-pilot.md` (sections (a), (b), (d), (e), (f) "after the pilot", (h), (i), the definition of done parts B and C, and the refusal codes; normative for behaviour: this spec draws it and decides nothing beyond it), `docs/architecture/screening-api-contract.md` §3, §4, §7, `docs/architecture/refusals.md`. Related: `07-agreement-with-agent.md`, `09-publish.md`, `docs/ux/phase0-inception/final/11-criteria-block.md` (Inception's side, part D). Brand: `docs/ux/brand/BRAND_BOOK.md`, `tokens.json`. Every number in this spec marked "illustration" is invented for layout and comes from the worked example of the record (4 inclusion and 5 exclusion criteria, 1,062 records); the screen shows only what the engine returns.

**Purpose.** Before screening everything, decide a small sample under your criteria, see where the criteria worked and where they did not, and, if you choose, revise a criterion with a recorded reason.

**Changed from the canvas and from 02 and 03.** This spec adds to 02 and 03; it does not rewrite them.
- **Prepare** (02) gains one card after batches exist (the canvas has none). 02's blocks, gate and states are unchanged.
- **Triage** (03) gains a pilot banner, one default (the checklist opens during a pilot, 03 M8-triage point 2 closes it by default) and a "Shown again" view with the earlier decision beside the record. 03's keys, bars, rules and every other state are unchanged.
- **New screen** at `/screening/pilot`: the result, and the revise dialog opened from it (and from each observation).
- **No second reader, no model in the observations.** Observations are fixed rules over counts (record (f)); the agent's answers appear only in draft styling.
- **Machine output is a draft.** Agent columns, agent disagreements and the calibration result use the dashed `ink-muted` border on plain `surface` with the label "Agent draft · not a decision". The engine's observations use the same look with the label "A reading of your answers · not an instruction". "Record the revision" and "Draw the pilot" are the only actions that write.
- **Brand button rule.** One brand button per state (BRAND_BOOK). On Prepare's card the brand button is "Draw a pilot of {n}" and "Screen everything" is secondary (Open question 7). On the result it is "Screen the rest" once the pilot is complete and "Continue the pilot" while it is not; "Revise a criterion" and "Pilot more records" are secondary.

## Entry / exit
- Entry: (1) Prepare, card "Pilot your criteria first", shown once batches exist and no batch is approved. (2) Triage's pilot banner, link "See the result so far" (opens the result in progress). (3) The result is also reached when the last pilot record is decided: Triage's all-decided card for the pilot (the 03 hand-off, but for the pilot) leads here with "See the pilot result" as its brand button. (4) A direct link `/screening/pilot?id=pilot_NNN`. (5) The revise dialog from "Revise a criterion", from an observation's "Revise {id}", and from Triage's recheck banner link "What changed".
- Exit: "Screen the rest" records nothing and goes to Triage (the queue skips decided records; records shown again come first). "Continue the pilot" goes to Triage `view=pilot`. After a revision: "Open the {n} records shown again" goes to Triage `view=recheck`. "Pilot 50 more records" opens the draw confirmation and then Triage `view=pilot`.
- Gate: a pilot can be drawn, and a criterion revised, only from the moment batches are prepared until the first batch is approved. Before batches exist, the card does not show; after a batch is approved, the draw and the revision are refused (states below). While a pilot has undecided records, a new draw is refused (`PILOT_OPEN`).

## Data in
Every figure is a field of an answer. The browser computes no count, percentage, denominator, threshold or observation, and never derives an outcome (03 rule).

| Field | Source |
| :-- | :-- |
| batches exist, approved batches, protocol-changed signal | `GET /api/v1/screening/summary` ✓ `screening_v1.py:166` (`protocol_changed`); the pilot block of the same answer (open pilot id, drawn, decided, pilots so far) ✗ M11b part B (Open question 1) |
| the draw's size limits and how many undecided records remain | `POST /api/v1/screening/pilot` with `confirm: false` ✗ M11b part B (Open question 2) |
| the pilot queue, in drawn order | `GET /api/v1/screening/queue?view=pilot` ✗ M11b part B (the route and its cursor ✓ `screening_v1.py:203`; the view is new) |
| the checklist-open-by-default flag for the current session | the queue's answer ✗ M11b part B (a setting the queue answers, not a browser guess, DoD 12) |
| result: n decided of N drawn; Include, Exclude, Unclear; per criterion: exclusions decided, checklist "not reported" (of those answered), draft "not reported" and disagreement (of those where both answered), each with its denominator; observations with their counts; the records list; for a second pilot, the first pilot's figures beside | `GET /api/v1/screening/pilot/{pilot_id}/result` ✗ M11b part B |
| criteria in force, their version, retired ids | `GET /api/v1/screening/records/{study_id}` ✓ `screening_v1.py:268` for the record's criteria (it must read the criteria in force, DoD 2, ✗ M11b part A); the list for the dialog ✗ M11b part A (Open question 3) |
| the dry answer of a revision: new ids, records shown again by outcome | `POST /api/v1/screening/criteria/amendments` with `confirm: false` ✗ M11b part A |
| the record shown again: the earlier decision (outcome, reason code, checklist answers, `criteria_version`), the criteria version in force | `GET /api/v1/screening/records/{study_id}` ✓ `screening_v1.py:268`; the new fields ✗ M11b part A (names for the build) |
| the shown-again queue | `GET /api/v1/screening/queue?view=recheck` ✗ M11b part A |
| the agreement read per criterion, with `answered_by_both` | `GET /api/v1/screening/agreement` ✓ `screening_v1.py:1184`; `answered_by_both` ✗ M11b part B |
| the calibration dialog: provider keys, consent, data flow, `last_model` | `GET /api/v1/screening/proposals/setup` ✓ `screening_v1.py:1085` |
| the calibration estimate | `POST /api/v1/screening/proposals/runs` with `estimate_only` and `scope: study_ids` ✓ `screening_v1.py:1022` (Open question 4) |
| the calibration's progress and result (`include_recall`, `ci_low`, `missed_includes`) | `GET /api/v1/screening/proposals/runs/{run_id}` ✓ `screening_v1.py:1120` |
| settings (blinding, not-reported rule in force) | `GET /api/v1/screening/settings` ✓ `screening_v1.py:436` |

## Data out
Writes, all desktop-only (the phone never calls them, contract §6):
- **Draw:** `POST /api/v1/screening/pilot {n, confirm: true}` ✗ M11b part B. `n` is 20 to 100 in steps of 10 (default 50). The engine draws the seed and the records (undecided only, simple random), writes `literature/screening/pilot/pilot_NNN.json` and the journal row `SCREENING_PILOT_DRAWN` (pilot id, n, seed). Answer: `{pilot_id, n, seed, drawn_at}`. Refuses `PILOT_OPEN` and the others below.
- **Revision:** `POST /api/v1/screening/criteria/amendments {op, side, ids, text?, reason_category?, reason, confirm}` ✗ M11b part A. `op` is `reword`, `split`, `merge`, `remove`, `add` or `reason_category`. `confirm: false` writes nothing and answers the new ids and the shown-again counts by outcome; `confirm: true` appends one line to `audit/criteria_amendments.jsonl` (id `CRA-` plus 24 hex, from and to, the reason, the versions, `pilot_id` when a pilot is in progress, the shown-again counts), writes the journal row `PROTOCOL_CRITERIA_AMENDED`, rewrites `SCREENING_CRITERIA.md` and backs the earlier file up under `audit/amended/<stamp>/`. `protocol.json`, the snapshot and the batch files keep their bytes.
- **Decisions on pilot records and on records shown again:** the existing `POST /api/v1/screening/decisions/events` ✓ `screening_v1.py:372`. A decision made again names the earlier one in `supersedes`; the engine stamps `criteria_version`; the browser cannot send it. No new payload field.
- **Calibration:** `POST /api/v1/screening/proposals/calibrations {study_ids, provider, model, effort, base_url?, cost_ceiling_usd?}` ✓ `screening_v1.py:1154`. This screen **always sends `model`** and never relies on the route's own default (Opus 5.5; finding 32, record (i)).
- No setting is written. Nothing is stored in the browser except the open or closed state of the checklist for the session (03).

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/summary` | ✓ `screening_v1.py:166`; pilot block ✗ M11b part B |
| `GET /api/v1/screening/queue?view=pilot` | ✗ M11b part B |
| `GET /api/v1/screening/queue?view=recheck` | ✗ M11b part A |
| `GET /api/v1/screening/records/{study_id}` | ✓ `screening_v1.py:268`; earlier-decision fields and criteria in force ✗ M11b part A |
| `POST /api/v1/screening/decisions/events` | ✓ `screening_v1.py:372` |
| `POST /api/v1/screening/pilot` | ✗ M11b part B |
| `GET /api/v1/screening/pilot/{pilot_id}/result` | ✗ M11b part B |
| `POST /api/v1/screening/criteria/amendments` | ✗ M11b part A |
| `GET /api/v1/screening/agreement` | ✓ `screening_v1.py:1184`; `answered_by_both` ✗ M11b part B |
| `GET /api/v1/screening/proposals/setup` | ✓ `screening_v1.py:1085` |
| `POST /api/v1/screening/proposals/runs` (`estimate_only`) | ✓ `screening_v1.py:1022` |
| `POST /api/v1/screening/proposals/calibrations` | ✓ `screening_v1.py:1154` |
| `GET /api/v1/screening/proposals/runs/{run_id}` | ✓ `screening_v1.py:1120` |
| `POST /api/v1/screening/proposals/runs/{run_id}/cancel` | ✓ `screening_v1.py:1130` |
| `GET /api/v1/screening/settings` | ✓ `screening_v1.py:436` |
| New refusals `CRITERIA_AMENDMENT_INVALID`, `CRITERIA_AMENDMENT_NO_BATCHES`, `CRITERIA_AMENDMENT_AFTER_APPROVAL`, `CRITERIA_SIDE_EMPTY` (part A), `REASON_CODE_RETIRED` (part A), `PILOT_OPEN` (part B) | ✗ M11b; they go in the console refusal set and `refusals.md`, not Contract v1 (record (c)) |

The pilot, the amendments file and `criteria_version` are not Contract v1 artifacts; `generate_contract_baseline.py --check` stays current (record DoD 21).

## States

### A. Prepare: the entry card
- **No batches yet** (cannot show the card): Prepare is in its own states (02). The card is not rendered. The sentence under the Prepare gate stays 02's. A direct link to `/screening/pilot` shows the state "Prepare the batches first" (below).
- **Pilot not started** (default of the card), shown after batches exist and before any approval:
  - Heading "Pilot your criteria first" (h2).
  - Body: "Read a small random sample under your criteria before you screen everything. You see where a criterion is hard to judge, and you can reword it while little is decided."
  - Field "Records in the pilot": number input, 20 to 100, step 10, default 50, hint "20 to 100 records. About half an hour for 50." (the half hour is the record's estimate at 30 seconds a record; shown as a hint, never as a promise).
  - Brand button "Draw a pilot of 50"; secondary "Screen everything" (link to Triage). Neither is required: the researcher can ignore the card.
  - Confirmation dialog (`role="alertdialog"`, "Draw the pilot?") before anything is written: "Draw 50 records at random from the 1,062 in your corpus (illustration)? The app picks records you have not decided yet and records the random seed it used, so the draw can be repeated. Your decisions on them are ordinary decisions: they stay, and count in the full screening." Buttons "Draw the pilot" and "Not now". The words "random" and "seed" and "ordinary decisions" must be in the dialog.
- **Pilot in progress:** the card heading becomes "Pilot in progress · 12 of 50 decided" with "Continue the pilot" (brand, to Triage `view=pilot`) and "See the result so far".
- **Pilot complete:** "Pilot complete · 50 of 50 decided" with "See the result" (brand), "Pilot 50 more records", "Screen the rest".
- **Records waiting to be re-checked:** the card carries one line "{n} records are shown again because a criterion changed." with "Open them" (Triage `view=recheck`).
- **After a batch is approved:** the card is replaced by a plain note "A batch is already approved, so the criteria are fixed. To change them after publication, start a new screening from this protocol." (`CRITERIA_AMENDMENT_AFTER_APPROVAL`), with no draw button. Pilots already made stay readable.
- **Offline:** the card shows its last state with the "as of" caption; the draw button is disabled with "Needs the engine on this computer." (02's reason).
- **Protocol changed:** the card is disabled with "Batches no longer match the protocol" (02's Mismatch row; 08). Pilots and revisions made under the earlier protocol stay in the log and no longer apply to the new one.
- **Loading:** skeleton card. **Error:** `ENGINE_UNREACHABLE` (client-side), `BATCHES_NOT_PREPARED` (HTTP 409; the card does not show; stale tab only).

### B. Triage during a pilot (delta to 03)
- **Banner.** Above the record pane, inside the triage bar's banner zone (03 M8-triage point 1, zone 2): "Pilot · 12 of 50 decided" with a thin strip (decorative, `aria-hidden`), then the one sentence "In the pilot your answers per criterion show which criteria are hard to judge." and the link "See the result so far". The banner is a `region` labelled "Pilot". The position line "Record 12 of 30 · batch 1" is replaced, in the pilot view only, by "Pilot record 12 of 50". It never shows an agent call.
- **Checklist open by default** while the pilot view is showing and the record is a pilot record: the 44 px toggle starts expanded, because the queue answers `checklist_open_by_default` (DoD 12). It stays optional and its toggle still closes it for the session (03 point 2 session memory applies). Outside the pilot view the 03 default (collapsed) returns. Unanswered criteria stay absent (never sent as `not_reported`).
- **Pilot complete:** the all-decided hand-off of 03 point 6 for the pilot view reads "The pilot is decided: 50 of 50" with "See the pilot result" (brand) and "Screen the rest" (link). The main queue is not "all decided" in the rest of the corpus, so the 03 Publish hand-off does not show.
- **No drafts for pilot records** (no run made): the banner is unchanged; the result's agent columns read "No agent drafts for these records. Run the agent to compare." with a link to the run screen (06). Nothing is requested here.
- **A record shown again (recheck).**
  - Triage's "Show" select gains the option "Shown again" (`view=recheck`); with at least one record waiting, a banner reads "{n} records are shown again because criteria changed (version {v})." with "What changed" (opens the amendment's summary: from and to wording and the reason, read-only).
  - On a record shown again, the **earlier decision is shown beside the record**, in the right column above the checklist, as a plain card labelled "Your decision under the earlier wording (version 1)": the outcome badge (text plus icon), the reason code in mono, the checklist answers you gave, and a Details with the earlier wording of each criterion the revision touched. It is a record of what you decided, not the agent's, so it is not draft-styled; it is dimmed no further than `ink-muted` text. It is not a decision to copy: the decision bar is the normal 03 bar and nothing is pre-selected.
  - When the new decision is saved the card changes to "Replaces your earlier decision (version 1)" (the earlier event stays in the log; the new one carries `supersedes`).
  - A batch that holds a record shown again is not fully decided, so it cannot be approved until the record is decided again (09's gate; no new copy there).
- **`REASON_CODE_RETIRED`** (stale tab or a chip left from before a revision): the reason panel shows "{id} was replaced in version 2. Choose a reason from the criteria in force." The chips refresh from the criteria in force; the code is in Details; nothing is saved.
- **Offline:** decisions queue locally as in 03; the pilot banner keeps its last count with the "as of" caption; the earlier-decision card and the recheck view need a loaded record and show "Not available offline" for records not yet loaded.
- **Protocol changed:** as 03 (banner "Batches no longer match the protocol", decisions disabled).

### C. The result: `/screening/pilot?id=pilot_001`
- **Default (pilot complete):** h1 "The pilot is decided: 50 of 50 records." Lede "Counts only, from your own decisions. Nothing here is an instruction." Regions in order: counts, per-criterion table, "What this suggests", the records list, the small-sample sentence, the action bar (Desktop layout).
- **No batches yet:** the route shows a card "Prepare the batches first" with a link to Prepare (`CRITERIA_AMENDMENT_NO_BATCHES` / `BATCHES_NOT_PREPARED`: before batches there is nothing to protect; criteria are changed in Inception). No actions.
- **Pilot not started:** `id` unknown or no pilot: "No pilot yet." with the draw control of the Prepare card repeated (same dialog). The `id` the engine does not know shows "That pilot does not exist in this workspace." (a plain not-found card; the exact code is the engine's, Open question 1).
- **Pilot in progress:** h1 "Pilot in progress: 12 of 50 decided." Counts and table read "of 12 decided so far" on each denominator; observations appear only when the engine returns them (it applies its own minimum counts; the browser applies none); the primary action is "Continue the pilot". "Revise a criterion" is available (the amendment records the pilot in progress, `pilot_id`). The draw of a new pilot is refused (`PILOT_OPEN`: "Finish the pilot you started first: 38 records are still undecided.").
- **Second pilot (compare with the first):** after a revision and "Pilot 50 more records", `pilot_002` is drawn (new seed, undecided records only). Its result shows the same regions with the first pilot's figures in a second column beside it ("Pilot 1" and "Pilot 2" under one caption "Criteria version 1 and criteria version 2"), counts only, no difference arrow, no verdict word. Each pilot's column is captioned with the criteria version it was decided under. Observations are listed for the newer pilot only.
- **Empty observations:** "Nothing stood out in these 50 records." is a real state, shown as a plain line (not an error).
- **No drafts for pilot records:** see B. The agent columns and the "the agent disagreed" filter are absent (not disabled).
- **Calibration** (the dialog "Check the agent on these 50 records", opened from the action bar; offered only when every pilot record is decided and a provider key exists):
  - *Ready:* the dialog names the **model** (`last_model` from the setup, else the run screen's constant `claude-haiku-5-5`, as on the run screen (H-screening-drafts item 6); a select of the run screen's models; settled by the record, (i)), the **count** ("50 records you decided"), the **estimate** ("About $0.01 for 50 records on {model}, an estimate at {prices_as_of} prices"), the data flow sentence from `GET /proposals/setup` ("Titles and abstracts of these 50 records are sent to {provider}."), an optional cost ceiling, the consent line when `CONSENT_REQUIRED` applies. Button "Run the check · about $0.01" (brand). Nothing is sent before it; Esc and "Not now" close it. The dialog is never reached with a model chosen by the engine's default.
  - *Running:* "Checking the agent on 50 records · 31 done" with Cancel (`POST …/cancel`; after a cancel the dialog says "Stopping…" until the engine reports the state; it does not offer Start again before then, the finding 35 rule).
  - *Done:* the agent columns of the table fill in draft styling; "Missed includes" opens the pilot records the agent would have dropped (the existing advisory warning; it never blocks anything).
  - *Failed / refused:* `COST_CEILING_REACHED` ("The estimate is above your ceiling. Raise it or choose a cheaper model."; when it stops mid-run, "Stopped at your ceiling. {n} done are kept."), `PROVIDER_KEY_MISSING` ("No key for {provider} on this computer. Set it with `nexus-scholar keys set {provider}`."), `CONSENT_REQUIRED`, `CEILING_NOT_PRICED` ("This model has no price in the app, so a ceiling cannot be measured. Run it without a ceiling or choose another model."), `DRIVER_UNAVAILABLE`, `RUN_ALREADY_ACTIVE` ("An agent run is already active in this workspace."), `PROVIDER_TRANSIENT` ("The provider did not answer. Nothing is lost; try again."). Each shows the sentence, the code in Details, one next step; no spend happens in any refused case.
- **Drafts made under an earlier version** (after a revision): labelled "made under the earlier wording" and left out of the agent columns and of agreement (DoD 9); the line "Draft again the {n} records whose draft predates the revision" links to the run screen with its own estimate (06). Nothing is requested here.
- **A revision recorded:** the result shows a notice "Criteria version 2 recorded on {date}. {n} records are shown again." with "Open them" (Triage `view=recheck`) and "Pilot 50 more records". The notice does not move the counts of the pilot already read; the table says which version each pilot was decided under.
- **Records waiting to be re-checked:** the result shows "{n} records are waiting to be decided again" next to the action bar; "Screen the rest" is still available, and the engine fails closed on approval (a batch holding one cannot be approved).
- **After a batch is approved:** "Revise a criterion" and "Pilot more records" are replaced by the note "A batch is already approved, so the criteria are fixed. To change them after publication, start a new screening from this protocol." (`CRITERIA_AMENDMENT_AFTER_APPROVAL`). Counts, table and records stay readable.
- **Loading:** skeleton for the counts, the table and the list; observations show a skeleton line. **Error:** `ENGINE_UNREACHABLE`, `STALE_BINDING` (`integrity.py:28`: "Batches no longer match the protocol", read-only), `UNKNOWN_STUDY` on a record link.
- **Partial:** a pilot with some decisions made under version 1 and some under version 2 (a revision during the pilot) shows the table with the caption "Decided under more than one version of the criteria" and "of N" denominators that count only decisions on records not shown again; the engine states the split.
- **Offline:** the last result stays, captioned "as of {time}"; every action is disabled with "Needs the engine on this computer."
- **Protocol changed:** actions disabled; banner "Batches no longer match the protocol"; "Rebind" is 02's, linked. The pilot's own file is kept and marked "made under the earlier protocol".

### D. The revise dialog
- **Opening:** from "Revise a criterion" (no criterion chosen), "Revise EXC-05" (that criterion pre-chosen), or from the recheck banner. `role="dialog"`, labelled "Revise a criterion", focus on the first radio, Esc and "Not now" close it without writing.
- **Step 1, choose the operation** (`fieldset` + `legend` "What do you want to do?"; six radios, each with one plain sentence): "Reword · same test, clearer words", "Split · one criterion into two", "Merge · two criteria into one", "Remove", "Add", "Change the reason category · wording stays". No default is selected.
- **Step 2, the criteria and the new text** (fields follow the operation): reword, a select of one criterion in force plus a text area with the current wording prefilled; split, one criterion plus two text areas; merge, two criteria on the same side plus one text area; remove, one criterion; add, a side (radios Inclusion / Exclusion) plus a text area; reason category, one criterion plus a text field for the "Rejection Reason Code" text. A retired id is not selectable. Each criterion option shows its id and the first 60 characters of its wording.
- **Step 3, the reason** (required): "Why are you making this change? One sentence." text area, 500 characters at most with a live count (`aria-describedby`), no default. The button "Check what this changes" stays disabled until the reason is not empty; it sends the dry call (`confirm: false`).
- **Dry call loading:** "Checking what this changes…" in the dialog (skeleton line). Nothing is written.
- **Confirmation** (the same dialog becomes `role="alertdialog"`, "Record this revision?"):
  - what changes: e.g. reword "EXC-03 keeps its number. Its wording becomes version 2." or split "EXC-03 will be retired. New criteria: EXC-06 and EXC-07."; ids are never reused; the wording before and after sits in a two-row table (draft look is not used: it is the researcher's own text);
  - "This will show again 14 records you decided: 6 Include, 5 Unclear, 3 Exclude citing EXC-03." (illustration; the numbers and the id come from the dry answer; the outcome words are badges with text and icon; "Exclude citing {id}" is plain text); when nothing is shown again: "No record will be shown again.";
  - what stays: "Your signed protocol, the corpus and your decisions keep their binding. The revision is recorded beside the protocol with your reason, and it appears in the methods paragraph.";
  - buttons "Record the revision" (brand; `confirm: true`) and "Back" (to step 3). Nothing is written before "Record the revision". The reason typed is repeated read-only above the buttons.
- **Recorded:** the dialog closes; the result shows the notice of C ("a revision recorded"); focus goes to that notice (`aria-live="polite"`: "Revision recorded. Criteria version 2.").
- **Refusals** (each a card inside the dialog, plain sentence, the code in Details, one next step; the typed text and the reason stay in the fields):
  - `CRITERIA_AMENDMENT_INVALID` (HTTP 422): "This change cannot be recorded: {engine message}." (no reason, an unknown or retired id, a change that changes nothing, or no confirmation; the message is the engine's, the card does not guess). Next step: "Back".
  - `CRITERIA_AMENDMENT_NO_BATCHES`: "Prepare the batches first. Before that, change criteria in Inception." Link to Prepare. (Not reachable from the card; stale tab.)
  - `CRITERIA_AMENDMENT_AFTER_APPROVAL`: "A batch is already approved, so the criteria are fixed. To change them after publication, start a new screening from this protocol." No next step in the dialog; "Close".
  - `CRITERIA_SIDE_EMPTY`: "This would leave no {inclusion | exclusion} criterion. Add one first, or choose another change."
  - `PILOT_OPEN` is **not** a revision refusal (a revision is allowed during a pilot; record (h) stores the `pilot_id`). It refuses the draw only (A, C).
  - `REASON_CODE_RETIRED` appears in Triage (B), not in this dialog.
  - Existing codes that can occur: `STALE_BINDING` (a tab out of date; "Batches no longer match the protocol"; Close and reload), `TOKEN_SCOPE_REFUSED` (a phone: the dialog is not reachable on a phone), `ENGINE_UNREACHABLE`.
- **Offline:** the dialog does not open; the button is disabled with its reason.
- **Protocol changed:** the dialog does not open; same reason as C.
- **Why the dialog is the only revise path in this milestone:** revision before batches exist is Inception's (record "When a revision is allowed"); a revision after a batch is approved is a new screening.

## Desktop layout
Follows the step-header pattern of BRAND_BOOK (a `label` eyebrow "STEP 2 · SCREENING · PILOT", the `display` heading, one `body` line in `ink-muted`) and the Prepare/Agreement split (main plus side). Compact density. One brand button per state.

**Prepare card (A).** A `surface` card in Prepare's main column under the criteria card: h2, one body paragraph, the size field, then the two buttons in one row (brand first in reading order). No gate panel of its own: Prepare's gate panel (02) is the only dashed-border panel on the screen.

**Triage (B).** The banner strip sits between the triage bar and the three columns; it never changes the focus-screen rule (no page scroll at ≥ 1024 px: the banner is 40 px and the record pane and right column shrink by that height). The earlier-decision card is the first block of the right column.

**The result (C), at 1440 and 1280 px.**
1. Header: eyebrow, h1, lede.
2. **Counts row.** Four tiles: "Decided 50 of 50", Include, Unclear, Exclude (illustration: 14 / 11 / 25). Each tile has its label, the number, and the denominator ("of 50"); each outcome tile has its badge (text plus icon; roles include, unclear, exclude), never colour alone. Tiles are real elements with `th`-style labels, not a chart.
3. **Per-criterion table** (main column, full width, scrolls inside the card on narrow windows): rows are criteria in protocol order, with the id in mono and the first 60 characters of the wording (full text in Details); columns "Decided exclusions", "Your checklist: not reported", then the agent columns "Draft: not reported" and "Draft and you disagreed" (draft-styled header "Agent draft · not a decision"; present only when drafts exist), and one column per pilot when there are two. Cells read "3 of 25 exclusions", "4 of 18 answered", "9 of 40", "6 of 38" (illustration). A row is a retired criterion only in the second pilot, labelled "Retired in version 2" in text. No cell is coloured by a threshold.
4. **What this suggests** (a list of cards, draft look: dashed `ink-muted` border, label "A reading of your answers · not an instruction"). Each card is one fixed-rule observation: a plain sentence that names the criterion and the counts, e.g. "EXC-05 decided no record in this pilot of 50. It may be rare, or covered by another criterion." (illustration) and one action "Revise EXC-05". A pair observation (a mirrored pair, exclusions that fire together) names both ids and offers one "Revise {id}" per id. The card never contains a proposed wording, an instruction, or a verdict. The seven observation kinds of the record, with words in Copy.
5. **Records.** A list of the pilot's records (title, outcome badge, reason code), 25 per page, with three filters in one row: "Criterion" (select), "Outcome" (select), and "The agent disagreed" (a checkbox, present only when drafts exist and only for records you decided). Each title opens Triage on that record (`view=decided` for a decided record).
6. **The small-sample sentence**, once, under the table: "Counts from 50 records. A criterion that decided nothing here may still matter in the full corpus."
7. **The action bar** (sticky at the bottom of the main column; at most one brand button): "Revise a criterion", "Pilot 50 more records", "Screen the rest" (brand when the pilot is complete and nothing is waiting to be re-checked), and "Check the agent on these 50 records" (secondary, with a hint button "About this check" naming that it sends titles and abstracts to a provider and costs money; max 6 hint buttons on the screen, guidance rule 1). "Screen the rest" records nothing.
8. **Side column:** a "Details" disclosure (12) with the pilot id, the seed, `drawn_at`, the snapshot id, the criteria version and the protocol fingerprint (LTR), and, after a revision, the amendment ids.

## Mobile layout (≤ 640 px)
Plan §4 and contract §6: the phone does not mount `/prepare`, `/proposals/*`, settings or any route that writes the method or the criteria.
- **Prepare card:** not shown on the phone (Prepare is "Prepare on your desktop").
- **Draw, revise and calibration** are desktop-only. The phone shows, on the pilot route, one card: "Pilot and criteria changes are made on your desktop." with the pilot's decided count read-only; the result's read-only regions (counts, table as stacked rows, observations, the small-sample sentence, records list) may be shown, but no action is, and the dialog is never mounted. A call from a phone is refused `TOKEN_SCOPE_REFUSED`.
- **Triage on the phone (04):** the pilot banner shows as one line "Pilot · 12 of 50 decided" above the record; the checklist default is the phone's own (04 has no checklist); a record shown again shows "Your decision under the earlier wording (version 1)" as a card above the decision buttons (the earlier outcome badge and reason code; the checklist answers behind a 44 px "Details" row). Decisions are ordinary phone decisions. Touch targets at least 44 px; no gesture is added; the existing swipe and long-press map of 04 is unchanged.
- A narrow desktop window gets one column: counts tiles two by two, the table scrolling inside its card, the action bar stacked at the end.

## Keyboard
- Prepare card: Tab order is the size field, "Draw a pilot of {n}", "Screen everything". Enter on the draw button opens the confirmation (Esc closes it; focus returns to the button).
- Triage: 03's map is unchanged (I, E, U, S, Z, N, J, K, 1 to 3, ?). The pilot banner's link is in the tab order after the bar. In the recheck view the earlier-decision card is a labelled region and is read before the checklist; no key pre-selects a decision. `J`/`K` still move through the queue view chosen.
- Result: Tab order is the counts row (as plain text), the table (rows focusable only for their Details), the observation actions in list order, the records filters, the records, the small-sample sentence (not a stop), the action bar. `Ctrl+Enter` runs the primary action of the screen (Screen the rest, or Continue the pilot, or the dialog's primary). No single-letter shortcut is added on the result.
- Revise dialog: focus starts on the operation radios; arrow keys move the radio; Tab follows the steps; Enter on "Check what this changes" or "Record the revision" activates the focused button only (never the dry call by Enter in the text area); Esc closes and writes nothing; focus returns to the button that opened it.
- Calibration dialog: the same pattern; the run button is the last stop; the cost ceiling and model select come before it.

## Copy
Master strings are English (fr and ar fall back to en, plan §7). Keys live in `components/screening-pilot.tsx` for the result and the dialogs, in `lib/triage-copy.ts` for Triage, and in `components/screening-prepare.tsx` for the card. The one-sentence rule of record (d) and the figures' words are exact.

| Key | en |
| :-- | :-- |
| `screening.pilot.card.title` | Pilot your criteria first |
| `screening.pilot.card.body` | Read a small random sample under your criteria before you screen everything. You see where a criterion is hard to judge, and you can reword it while little is decided. |
| `screening.pilot.card.size` | Records in the pilot |
| `screening.pilot.card.sizeHint` | 20 to 100 records. About half an hour for 50. |
| `screening.pilot.card.draw` | Draw a pilot of {n} |
| `screening.pilot.card.skip` | Screen everything |
| `screening.pilot.card.inProgress` | Pilot in progress · {k} of {n} decided |
| `screening.pilot.card.complete` | Pilot complete · {k} of {n} decided |
| `screening.pilot.card.recheck` | {n} records are shown again because a criterion changed. |
| `screening.pilot.draw.title` | Draw the pilot? |
| `screening.pilot.draw.body` | Draw {n} records at random from the {N} in your corpus? The app picks records you have not decided yet and records the random seed it used, so the draw can be repeated. Your decisions on them are ordinary decisions: they stay, and count in the full screening. |
| `screening.pilot.draw.confirm` / `.cancel` | Draw the pilot / Not now |
| `screening.pilot.banner` | Pilot · {k} of {n} decided |
| `screening.pilot.banner.sentence` | In the pilot your answers per criterion show which criteria are hard to judge. |
| `screening.pilot.banner.link` | See the result so far |
| `screening.pilot.position` | Pilot record {k} of {n} |
| `screening.pilot.done.title` / `.action` | The pilot is decided: {n} of {n} / See the pilot result |
| `screening.pilot.result.title.done` | The pilot is decided: {k} of {n} records. |
| `screening.pilot.result.title.open` | Pilot in progress: {k} of {n} decided. |
| `screening.pilot.result.lede` | Counts only, from your own decisions. Nothing here is an instruction. |
| `screening.pilot.counts.decided` / `.include` / `.unclear` / `.exclude` | Decided / Include / Unclear → full text / Exclude |
| `screening.pilot.counts.of` | of {n} |
| `screening.pilot.table.*` | Criterion · Decided exclusions · Your checklist: not reported · Draft: not reported · Draft and you disagreed · Pilot 1 · Pilot 2 · Retired in version {v} |
| `screening.pilot.table.cell.exclusions` | {k} of {n} exclusions |
| `screening.pilot.table.cell.answered` | {k} of {n} answered |
| `screening.pilot.draft.label` | Agent draft · not a decision |
| `screening.pilot.reading.label` | A reading of your answers · not an instruction |
| `screening.pilot.suggests.title` / `.none` | What this suggests / Nothing stood out in these {n} records. |
| `screening.pilot.suggests.revise` | Revise {id} |
| `screening.pilot.obs.mirrored` | {a} and {b} gave opposite answers on {k} of {n} records where both were answered. They may say the same thing. |
| `screening.pilot.obs.together` | {a} and {b} were both yes on {k} of the {n} records where either was. |
| `screening.pilot.obs.notReported` | {id} was answered not reported on {k} of {n}. It may be hard to judge from a title and abstract. |
| `screening.pilot.obs.neverUsed` | {id} decided no record in this pilot of {n}. It may be rare, or covered by another criterion. |
| `screening.pilot.obs.mostWork` | {id} decided {k} of the {n} exclusions. Check it is worded as you mean. |
| `screening.pilot.obs.manyUnclear` | {k} of {n} records were decided Unclear → full text. |
| `screening.pilot.obs.readDifferently` | The agent and you answered {id} differently on {k} of {n} records. |
| `screening.pilot.smallSample` | Counts from {n} records. A criterion that decided nothing here may still matter in the full corpus. |
| `screening.pilot.records.title` / `.filter.criterion` / `.filter.outcome` / `.filter.disagreed` | Records / Criterion / Outcome / The agent disagreed |
| `screening.pilot.noDrafts` | No agent drafts for these records. Run the agent to compare. |
| `screening.pilot.earlierDrafts` | Draft again the {n} records whose draft predates the revision |
| `screening.pilot.actions.revise` / `.more` / `.rest` / `.continue` / `.check` | Revise a criterion / Pilot {n} more records / Screen the rest / Continue the pilot / Check the agent on these {n} records |
| `screening.pilot.revised` | Criteria version {v} recorded on {date}. {n} records are shown again. |
| `screening.pilot.revised.announce` | Revision recorded. Criteria version {v}. |
| `screening.pilot.fixed` | A batch is already approved, so the criteria are fixed. To change them after publication, start a new screening from this protocol. |
| `screening.pilot.waiting` | {n} records are waiting to be decided again. |
| `screening.pilot.notPrepared` | Prepare the batches first. |
| `screening.criteria.revise.title` | Revise a criterion |
| `screening.criteria.revise.op.legend` | What do you want to do? |
| `screening.criteria.revise.op.{reword,split,merge,remove,add,reasonCategory}` | Reword · same test, clearer words / Split · one criterion into two / Merge · two criteria into one / Remove / Add / Change the reason category · wording stays |
| `screening.criteria.revise.text` / `.side` / `.reasonCategory` | New wording / Side / Rejection reason text |
| `screening.criteria.revise.reason` | Why are you making this change? One sentence. |
| `screening.criteria.revise.reasonCount` | {k} of 500 characters |
| `screening.criteria.revise.check` | Check what this changes |
| `screening.criteria.revise.checking` | Checking what this changes… |
| `screening.criteria.revise.confirm.title` | Record this revision? |
| `screening.criteria.revise.confirm.kept` | {id} keeps its number. Its wording becomes version {v}. |
| `screening.criteria.revise.confirm.retired` | {id} will be retired. New criteria: {ids}. |
| `screening.criteria.revise.confirm.shown` | This will show again {n} records you decided: {x} Include, {y} Unclear, {z} Exclude citing {id}. |
| `screening.criteria.revise.confirm.none` | No record will be shown again. |
| `screening.criteria.revise.confirm.stays` | Your signed protocol, the corpus and your decisions keep their binding. The revision is recorded beside the protocol with your reason, and it appears in the methods paragraph. |
| `screening.criteria.revise.record` / `.back` / `.cancel` | Record the revision / Back / Not now |
| `screening.triage.recheck.view` | Shown again |
| `screening.triage.recheck.banner` | {n} records are shown again because criteria changed (version {v}). |
| `screening.triage.recheck.what` | What changed |
| `screening.triage.recheck.earlier` | Your decision under the earlier wording (version {v}) |
| `screening.triage.recheck.replaced` | Replaces your earlier decision (version {v}) |
| `screening.calibrate.title` | Check the agent on these {n} records |
| `screening.calibrate.model` / `.count` | Model / {n} records you decided |
| `screening.calibrate.estimate` | About {cost} for {n} records on {model}, an estimate at {date} prices. |
| `screening.calibrate.flow` | Titles and abstracts of these {n} records are sent to {provider}. |
| `screening.calibrate.run` / `.running` / `.stopping` | Run the check · about {cost} / Checking the agent on {n} records · {k} done / Stopping… |
| `screening.refusal.CRITERIA_AMENDMENT_INVALID` | This change cannot be recorded: {message}. |
| `screening.refusal.CRITERIA_AMENDMENT_NO_BATCHES` | Prepare the batches first. Before that, change criteria in Inception. |
| `screening.refusal.CRITERIA_AMENDMENT_AFTER_APPROVAL` | = `screening.pilot.fixed` |
| `screening.refusal.CRITERIA_SIDE_EMPTY` | This would leave no {side} criterion. Add one first, or choose another change. |
| `screening.refusal.PILOT_OPEN` | Finish the pilot you started first: {n} records are still undecided. |
| `screening.refusal.REASON_CODE_RETIRED` | {id} was replaced in version {v}. Choose a reason from the criteria in force. |
| `screening.refusal.COST_CEILING_REACHED` / `PROVIDER_KEY_MISSING` / `CEILING_NOT_PRICED` / `RUN_ALREADY_ACTIVE` / `PROVIDER_TRANSIENT` | the existing keys of the run screen (06), reused; this spec adds none |

No fr or ar string is written here (fall back to en until translated, plan §7); DoD 16 requires en, fr and ar before the part C PR is merged.

## Accessibility
- Status is never colour alone: outcome words with an icon (`include`, `unclear`, `exclude` badges on their `-soft` fills; the `exclude` role is grey, so the counts rely on the word). Observations and refusal cards carry a label word ("A reading of your answers", "Refused") and a code in Details. The draft look (dashed `ink-muted` border on plain `surface`) is paired with the label text; it is never the only signal.
- Tables use real `table`, `th scope="col"` and `th scope="row"` for the criterion; numerals are tabular; denominators are text beside each number ("4 of 18 answered"), so a screen reader reads the pair.
- The pilot banner is a `region` named "Pilot"; the strip is `aria-hidden`. The live region announces "Decision saved. Pilot record 13 of 50." (03's announce pattern) and "Revision recorded. Criteria version 2."
- Dialogs: the revise dialog is `role="dialog"` and becomes `role="alertdialog"` at the confirmation; the draw confirmation is an `alertdialog`; focus is trapped and returned to the opener on close; a refusal card is `role="alert"`. The reason field has a visible label, a count tied by `aria-describedby`, and no placeholder as label.
- Targets are 44 px (radio rows, buttons, the "Details" rows). The size field is labelled and has its hint tied by `aria-describedby`.
- Contrast: `ink` on `surface`, `ink-muted` for secondary lines (at least 4.5:1); status colours as text or icon only on their `-soft` fills.
- RTL: the table and tiles mirror; criterion ids, seeds, fingerprints and the model name are LTR; criterion wording is `dir="auto"`; numerals stay Latin; "Pilot 1 | Pilot 2" columns keep the reading order of the page.
- axe passes in light and dark (DoD 16).

## Acceptance tests
Vitest (`apps/research-ui/tests/`), each with a fixture, no live call:
- `pilot.card-states.test.tsx`: the card shows only with batches and no approved batch; the size is 20 to 100 and defaults to 50; the confirmation names n, "random", "seed" and "ordinary decisions" before anything is sent; in progress, complete, waiting and approved states read as written.
- `pilot.draw-refusals.test.tsx`: `PILOT_OPEN` and `BATCHES_NOT_PREPARED` show their sentences; nothing is written on Not now.
- `pilot.triage-banner.test.tsx`: the banner reads "Pilot · 12 of 50 decided" with the one sentence; the checklist is open by default in the pilot view only and its toggle still closes it; no agent call is shown.
- `pilot.recheck-earlier-decision.test.tsx`: a record shown again shows "Your decision under the earlier wording (version 1)" beside the record with outcome, reason code and answers; no outcome is pre-selected; after a decision the card reads "Replaces your earlier decision".
- `pilot.result-counts.test.tsx`: the counts and every table cell show their denominator from the answer; the browser computes none; agent columns are draft-styled and absent without drafts.
- `pilot.observations.test.tsx`: each observation shows its criterion and counts and exactly one action "Revise {id}" per id; no proposed wording; "Nothing stood out" is a plain state.
- `pilot.second-pilot-compare.test.tsx`: two columns with their criteria versions; no verdict word; observations for the newer pilot only.
- `pilot.calibration-dialog.test.tsx`: the dialog names model, count and estimate; the request always carries `model` (with no `last_model` it is `claude-haiku-5-5`, never the route's default); `COST_CEILING_REACHED`, `PROVIDER_KEY_MISSING`, `CEILING_NOT_PRICED`, `RUN_ALREADY_ACTIVE` show their sentences and spend nothing; cancel shows "Stopping…".
- `criteria.revise-dialog.test.tsx`: each operation shows its fields; the reason is required and capped at 500; the dry call runs on "Check what this changes" and nothing is written; the confirmation lists new ids and the shown-again counts by outcome; "Record the revision" sends `confirm: true`.
- `criteria.revise-refusals.test.tsx`: the four new refusal sentences, with the code in Details and the typed text kept; `REASON_CODE_RETIRED` in Triage's reason panel refreshes the chips.
- `pilot.offline-protocol-changed.test.tsx`: offline and protocol-changed disable every action with their reasons.
- `pilot.mobile-readonly.test.tsx`: at 390 px no draw, revise or calibration control is mounted; the banner and the earlier-decision card show.
- `pilot.a11y.test.tsx`: tables have `th scope`, dialogs have roles and focus return, the banner is a named region.

Playwright (`apps/research-ui/e2e/screening/`):
- `pilot.spec.ts`: the golden-uav-30 fixture: draw 20, decide them by keyboard with the checklist open, open the result, revise one criterion (dry call, confirm, record), open the records shown again and decide one; axe in light and dark at 1440 and 1280 px.
- `pilot-approved.spec.ts`: after a batch is approved the draw and the revision are refused with the "criteria are fixed" sentence.

Python tests of the engine are the build record's (parts A and B); none is named here.

## Open questions
Questions 1 to 4 were settled by the milestone record on 2026-11-21, after this draft was written; they are kept here with the record's answer.
1. **How do Prepare and Triage know a pilot is open?** *Settled by the record (DoD 11b, 2026-11-21):* `GET /summary` gains a `pilot` block (the open or last pilot's id, n, decided, and how many records wait to be shown again). An unknown `id` on the result route answers a plain not-found refusal.
2. **Is there a dry call for the draw?** *Settled by the record (DoD 11):* `confirm: false` answers n, the undecided count and the expected time, and writes nothing, so the dialog can say how many records are left to draw from and refuse before the call when fewer remain.
3. **Which route lists the criteria in force for the dialog?** *Settled by the record (DoD 7b):* `GET /api/v1/screening/criteria` ✗ M11b part A, read-only, desktop: the criteria in force with the version each wording dates from, the retired ids, the current version and the amendments.
4. **Calibration estimate and model.** *Settled by the record ((i), DoD 14):* the estimate comes from the existing `POST /proposals/runs {estimate_only: true, scope: {study_ids}}` (✓ `screening_v1.py:987-1042`); the model is `last_model`, else `claude-haiku-5-5`; the request always carries `model` and the route's own Opus default is not changed in M11b.
5. **Earlier decision on a record shown again.** The record says the earlier decision stays in the log and is superseded, but not how it is shown. Recommended: beside the record, as a plain card "Your decision under the earlier wording (version 1)", with outcome, reason code, answers and the earlier wording in Details; nothing pre-selected; not draft-styled because it is the researcher's own.
6. **Where records shown again appear in Triage.** The record names `view=recheck` and says a batch holding one is not fully decided. Recommended: they also appear in "Needs you" first, tagged "Shown again", so a researcher who never opens the view still sees them; the "Shown again" option filters to them; the banner states the count.
7. **Which button is brand on Prepare's card.** The record says "beside Screen everything" and the brand book allows one brand button per screen. Recommended: "Draw a pilot of {n}" brand while no pilot exists (the practice the record describes), "Screen everything" secondary; neither is required; once a pilot is complete, "Screen the rest" is the brand button on the result.
8. **Phone.** Plan §4 and contract §6 keep writes of the method and criteria on the desktop. Recommended: the phone shows the pilot banner, the earlier-decision card and a read-only result, and draws, revises and calibrates nothing; a tester should confirm that reading the result on a phone is wanted at all.
