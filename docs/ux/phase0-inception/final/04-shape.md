# 04 Shape    Status: FINAL, built (M4b, PR #209) | Phase 0 Inception | Route `/[locale]/inception/shape?draft=rec_<32 hex>` (desktop only) | Milestone M4b

Boards: `Shape` (D5, `docs/ux/phase0-inception/final/project/Shape.dc.html`). No dedicated mobile board; `MobileScope` sets the narrow pattern. Contract: `docs/architecture/inception-api.md` (Steps: `scope`, `shape`). Code: `src/scholar_harness/inception/steps.py` (`_scope` `:165`, `_shape` `:177`, `_require` `:123`), `src/scholar_harness/inception/intent.py` (`PARADIGM_PROFILE`, `ALL_PLAYBOOKS` `:43`, `TRUSTWORTHINESS_FRAMEWORK` `:52`, `detect_leanings` `:119`, `enforce_lexicon` `:137`, `draft_rq` `:234`). The load/save protocol, the stepper, the proposal-card styling, conflict handling and the phone rule are in 01 "Shared by 01, 04, 05, 06 and 07".

**Purpose.** Choose the lens (paradigm) and playbook, say what the unit of analysis and the accepted proof are, and write the research questions, starting from a template draft the wizard offers.

**Changed from the canvas.**
- **No numeric leaning score.** The canvas badge "Leaning · 0.58" has no source: `detect_leanings` returns an integer keyword count. The marked card says "{n} keyword matches"; with a count of 0 for every lens, no card is marked.
- **A lens is never preselected.** The canvas shows Design Science checked and says choosing it pre-fills the playbook. Here the paradigm cards start unchecked (a machine proposal is a draft, not an answer); the researcher's click is the answer. After it, the recommended playbook is **marked** but not selected, with a secondary button "Use the recommended playbook". Continue needs a playbook the researcher chose.
- **Playbook list from the engine.** The canvas lists five playbooks by hand. The names and frameworks come from `steps/shape` `playbooks[{name, framework}]`; the UI hard-codes no list. The canvas's "(matches Design Science)" is the engine's `recommended_playbook`.
- **Secondary paradigm** is a select ("None" or one of the other three lenses), because the draft field `secondary_paradigm` is one value; the canvas checkbox "Add a secondary paradigm" had no field to choose which.
- **RQ proposal is one template.** The canvas shows a tidy-up warning ('"baseline" appears twice'). That is a text check the engine does not make; cut. The engine gives one `rq_draft` (RQ1). "Accept RQ1 as written" becomes "Use this as RQ1"; "Add RQ2" becomes "Add another question" (the draft holds `rqs[]` as plain strings, so facet and evidence type are not editable here).
- **Lexicon warnings** (`lexicon_warnings`) are shown as plain captions when present (they exist only for Interpretivist text using Positivist terms). The canvas's static vocabulary line is the engine's `lexicon` text, shown as is.
- **Unit of analysis and proof** sit in the main column beside the RQ, not in a side card, because the RQ template is filled from them.
- **Cut**: the phase ladder in the app bar (the shell owns it) and the "Run from the terminal" disclosure (no resumable command). Each card's "Evidence" and "Excludes" lines are kept, but they come from the engine's `refraction[{paradigm, evidence, negatives}]`, not from hand-written text.

## Entry / exit
- Entry: "Continue to Shape" on 01; the stepper; "Back to Shape" from 05.
- Exit: "Continue to concepts and criteria" goes to 05 after saving; "Back to Scope" goes to 01; "Save draft and exit" goes to 08.
- Gate: Continue is enabled when a paradigm, a playbook, a unit of analysis, a proof and at least one non-empty research question are present (a presence check that mirrors the engine's `_require` for `paradigm`, `playbook`, `unit_of_analysis`, `proof`, `rqs`; the engine stays the authority). Nothing is written to a workspace.

## Data in
| Field | Source |
| :-- | :-- |
| the draft record | `GET /api/v1/inception/drafts/{id}` ✓ M4a |
| `draft.paradigm`, `secondary_paradigm`, `playbook`, `unit_of_analysis`, `proof`, `rqs[]` | same record |
| paradigm cards: `paradigms[{name, goal}]`, `leanings[{paradigm, score}]`, `recommended_paradigm`, `refraction[{paradigm, goal, sample_rq, evidence, negatives}]` | `POST /api/v1/inception/steps/scope` ✓ M4a (needs `topic`; works before a paradigm is chosen) |
| playbooks and proposals: `recommended_playbook`, `playbooks[{name, framework}]`, `trustworthiness_framework`, `rq_draft`, `lexicon`, `lexicon_warnings[]` | `POST /api/v1/inception/steps/shape` ✓ M4a (needs `topic` and `paradigm`; `DRAFT_INCOMPLETE` names `paradigm` until one is chosen) |

`steps/shape` is called on load, when the paradigm or playbook changes, and when the unit or proof field loses focus, always with the in-memory draft, so the template RQ follows what is typed. It stores nothing.

## Data out
- Save: `PUT /api/v1/inception/drafts/{id}` ✓ M4a; writes `paradigm`, `secondary_paradigm`, `playbook`, `unit_of_analysis`, `proof`, `rqs`; every other field is carried through. Changing `proof` or `paradigm` changes the ids of generated criteria (05 handles the consequence). No journal event.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/inception/drafts/{id}` | ✓ M4a `console/api/inception.py:80` |
| `PUT /api/v1/inception/drafts/{id}` | ✓ M4a `inception.py:88` |
| `POST /api/v1/inception/steps/scope` | ✓ M4a `inception.py:106`, `steps.py:165` |
| `POST /api/v1/inception/steps/shape` | ✓ M4a `inception.py:106`, `steps.py:177` |

Desktop only, loopback origin on writes, as 01.

## States
- **Default**: eyebrow "Step 4 of 6 · Shape"; h1 "Which lens fits, and what will you ask?"; lede "A word scan of your question leans one way; that card is marked. The lens and the playbook are your choice. The template question is a draft until you use it."; four paradigm cards (radiogroup), the playbook list, the secondary-paradigm select, unit, proof, the RQ list with the template draft card. One brand button: "Continue to concepts and criteria".
- **Empty**: no paradigm chosen yet. The cards are unchecked; the playbook, unit, proof and RQ areas show their fields empty; the template card says "Choose a lens to get a template question." Continue is disabled with the reason.
- **Loading** (skeleton): four card skeletons and field skeletons while the draft loads; the playbook list and the template card have their own skeleton (`aria-busy`) while the steps run.
- **Error** (typed refusal, `StateCard`; texts in 08):
  - `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE`: the card stands for the screen, with "Go to your drafts".
  - `DRAFT_CONFLICT`, `DRAFT_EMITTED`: as in 01.
  - `DRAFT_INCOMPLETE` from `steps/scope` or `steps/shape`: `missing` is `topic` (no question yet): the sentence "Write your question in step 1 first." with a link to 01; or `paradigm` while none is chosen, which is the Empty state and shows no error.
  - `DRAFT_INVALID` (an unknown paradigm or playbook, `details.paradigms` or `details.playbooks`): the card lists the allowed names under Details; the form keeps the values.
  - Guard codes and `ENGINE_UNREACHABLE`: shared cards (08).
- **Partial**: a lens is chosen but no playbook, or an RQ is empty. The missing parts are named beside Continue ("Choose a playbook", "Write RQ1"). The template card still shows.
- **Offline**: edits stay in the tab; the step calls fail with `ENGINE_UNREACHABLE`; the proposals keep their last text with "As of {time}"; Continue and Save are disabled with "needs the engine on this computer".
- **Protocol-changed**: cannot occur (a draft binds no protocol). If the question was edited in another tab, the next save is `DRAFT_CONFLICT`.

## Desktop layout
Source: `Shape` (D5). Regions: shell, stepper, step header. **Main**: the paradigm radiogroup as a 2-by-2 grid of cards (name, `goal`, "Evidence: …" and "Excludes: …" from `refraction`; the leaning card carries a text badge "Closest by keywords · {n} matches", not a fill); the caption "The leaning is a keyword scan of your question, not a judgement. Four lenses only; question frameworks such as PICO or SPIDER are not offered yet." (open M6 stays visible); the playbook fieldset (name and framework, the recommended one marked "Recommended for {paradigm}"; button "Use the recommended playbook"); the secondary-paradigm select. **Side**: unit of analysis, proof, then the **RQ block**: the template card (draft styling, label "Template draft · not yet yours", the text, a mono line "template {playbook} · RQ1 · filled from unit and proof"), buttons "Use this as RQ1" (secondary) and "Write my own"; below it the researcher's RQ fields (RQ1, then more; each a textarea with a "Remove" text button; "Add another question"); the lexicon line. Button row at the end (Back to Scope, Save draft and exit, Continue to concepts and criteria). New components: none; the radio card is the existing card with a `brand` outline and `brand-soft` fill when chosen.

## Mobile layout (≤ 640 px)
Desktop-only on the engine (see 01); this is a narrow desktop window. One column: header, paradigm cards stacked (one per row, each 44 px or taller and wholly tappable), the playbook list (44 px rows), secondary select, unit, proof, the template card, the RQ fields, then the sticky action bar with "Save draft and exit" above "Continue to concepts and criteria". A real phone shows the desktop pointer card (`inception.common.phone.desktopOnly`).

## Keyboard
Focus order: skip link, shell, stepper, h1, paradigm radiogroup (arrow keys move within it, `Space` selects), "Use the recommended playbook", playbook radiogroup, secondary-paradigm select, unit, proof, "Use this as RQ1", "Write my own", RQ fields with their Remove buttons, "Add another question", Back, Save draft and exit, Continue. Choosing a lens moves focus nowhere (it keeps the radio). "Use this as RQ1" moves focus into the RQ1 field; "Write my own" does the same with the field cleared. After "Remove", focus goes to the previous RQ field or to "Add another question". No single-key shortcuts.

## Copy
Keys in `apps/research-ui/lib/inception-copy.ts`; shared keys are in 01.
- `inception.shape.title` "Which lens fits, and what will you ask?"
- `lede` "A word scan of your question leans one way; that card is marked. The lens and the playbook are your choice. The template question is a draft until you use it."
- `paradigm.legend` "Lens"; `paradigm.leaning` "Closest by keywords · {n} matches"; `paradigm.evidence` "Evidence: {text}"; `paradigm.excludes` "Excludes: {text}"; `paradigm.note` "The leaning is a keyword scan of your question, not a judgement. Four lenses only; question frameworks such as PICO or SPIDER are not offered yet."; `paradigm.secondary` "Secondary lens (mixed methods)"; `paradigm.secondaryNone` "None".
- `playbook.legend` "Playbook"; `playbook.recommended` "Recommended for {paradigm}"; `playbook.useRecommended` "Use the recommended playbook"; `playbook.framework` "Rigor framework: {framework}"; `playbook.waiting` "Choose a lens to see the playbooks."
- `unit.label` "Unit of analysis"; `unit.help` "For example a model, a team, a crop field."; `proof.label` "Proof a reviewer would accept"; `proof.help` "It becomes the first inclusion criterion in step 5; you accept it there."
- `rq.template` "Template draft · not yet yours"; `rq.templateMeta` "template {playbook} · RQ1 · filled from unit and proof"; `rq.use` "Use this as RQ1"; `rq.own` "Write my own"; `rq.waiting` "Choose a lens to get a template question."; `rq.label` "Research question {n}"; `rq.add` "Add another question"; `rq.remove` "Remove question {n}"; `rq.vocab` "Vocabulary for this lens: {lexicon}"; `rq.lexiconWarning` "{warning}".
- `gate.paradigm` "Choose a lens"; `gate.playbook` "Choose a playbook"; `gate.unit` "Write the unit of analysis"; `gate.proof` "Write the proof"; `gate.rq` "Write RQ1".
- `back` "Back to Scope"; `continue` "Continue to concepts and criteria".
- Refusals: `inception.refusal.<CODE>.*` (08); the `DRAFT_INCOMPLETE` topic sentence is `inception.shape.needTopic` "Write your question in step 1 first."

## Accessibility
- Paradigm cards are `role="radiogroup"` labelled "Lens", each a labelled radio with its goal as description; the marked leaning card carries the text badge, so colour is not the cue. The playbook list is a fieldset with a legend; the recommended one has text "Recommended for {paradigm}".
- The template card is announced by its badge; "Use this as RQ1" states its effect. The disabled Continue has `aria-describedby` listing what is missing.
- Contrast pairs from tokens (`brand` on `brand-soft` for the chosen card, `ink` elsewhere). Refusals `role="alert"`.
- RTL (ar): mirrored grid; the template text and RQ fields are `dir="auto"`; the playbook names (`PRISMA_SLR` and the like) and the framework names are `dir="ltr"`; numerals Latin.

## Acceptance tests
Vitest `apps/research-ui/tests/inception-shape.test.tsx`: no lens is checked on a new draft and the template card says to choose one; choosing a lens calls `steps/shape` and marks (does not select) the recommended playbook; "Use this as RQ1" copies the template into the field and sends nothing until Continue; the template RQ follows unit and proof on blur; Continue is disabled until the five presence conditions hold and the reasons are listed; the saved PUT carries unrelated draft fields unchanged; `DRAFT_INCOMPLETE` (`topic`) links to Scope; `DRAFT_INVALID` lists the allowed names; `DRAFT_CONFLICT` read-only and reload; i18n and N9 guard.
Playwright `inception.spec.ts` (this screen's part): choose a lens and a playbook, use the template, add RQ2, Continue, reload and see the same values; the marked card has a text badge; keyboard-only completion; RTL pass; axe in light and dark; no horizontal overflow at 375 and 1440 px.

## Open questions
None.

## As built (M4b, 2026-11-09)
- The lens cards show the engine's goal sentence; the evidence and excludes lines are not drawn (the scope step returns them only in `refraction`).
- There is no secondary-paradigm select and no "Use the recommended playbook" or "Write my own" button: the recommended playbook is marked and the researcher ticks one; "Use this draft as RQ{n}" fills the first empty question, which stays editable.
- Continue needs a lens (disabled, with the reason); other missing answers are named by the engine later (`DRAFT_INCOMPLETE` on the next step or at Review).
- Copy keys and their en, fr and ar texts are the code's: `apps/research-ui/lib/inception-copy.ts` (screen copy) and `apps/research-ui/lib/screening-states.ts` (refusal cards). The Copy section above gives the design intent and the English wording; where a key name or a sentence differs, the code is the record and `tests/inception-copy.test.ts` pins every key in every locale.
