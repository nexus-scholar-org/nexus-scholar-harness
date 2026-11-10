# 01 Scope    Status: FINAL, built (M4b, PR #209) | Phase 0 Inception | Route `/[locale]/inception/scope?draft=rec_<32 hex>` (desktop only) | Milestone M4b (browser screens over the M4a step API)

Boards: `Scope` (D2, `docs/ux/phase0-inception/final/project/Scope.dc.html`), `MobileScope` (M2, `.../MobileScope.dc.html`). Contract: `docs/architecture/inception-api.md` (Draft, Routes, Steps). Code: `src/scholar_harness/console/api/inception.py`, `src/scholar_harness/inception/steps.py` (`Draft` at `:84`, `_scope` at `:165`), `src/scholar_harness/inception/drafts.py`. Decisions: `docs/decisions.md`, 2026-11-08 "Inception drafts live under the workspaces root, with one session id". Brand: `docs/ux/brand/BRAND_BOOK.md` (principles 4 and 5, step header pattern), `docs/ux/brand/tokens.json`.

**Purpose.** Write down what the review is about (the question, the years, the languages) in a draft that is saved but writes no workspace, and see what the wizard's rules read from the question.

**Changed from the canvas.** The canvas's Scope step is the front of a first search (recon). Recon has no HTTP surface yet (INC-09 and INC-21 are deferred), and a draft carries no grounded evidence, so every recon field is cut. Every cut:
- **Search mode** (Semantic or Keyword) and the sentence about OpenAlex embeddings: not a draft field (`Draft` in `steps.py:84` has no mode). Plan §2 (Phase 0, open M4) names provider, date and mode in the protocol as a Contract v1 decision, so they are not shown.
- **"Papers to sample" (25)**, "12 or more keeps directions reliable": a recon parameter; not a draft field.
- **The side card "The first search will use"** (papers, years, languages, mode, source): the search does not exist. The years and languages stay as plain fields.
- **"Topic checks as you type"** (two subjects, fewer than 4 words, a question with no subject): a client-side heuristic. The browser makes no domain decision (`apps/research-ui/AGENTS.md`), and the engine has no such check. Cut. The only length rule is that the question is not empty.
- **The button "Search 25 papers"**: becomes "Continue to Shape". Steps 2 Explore and 3 Direction need recon; the stepper shows them as "Coming with recon", not as links (see 02 and 03). The step numbers are kept so recon can slot in without renumbering.
- **"Nothing written yet … recon cache … session rec_7f3a…"**: drafts are in `<workspaces root>/.drafts/<session id>/draft.json`, not the recon cache (decision 2026-11-08). The card says so with the real root.
- **The disclosure "Run from the terminal" (`uv run scholar-harness inception --grounded`)**: that command does not read a browser draft, and there is no `--resume` (`grep` of `cli.py` and `inception/` finds none). Cut on every inception screen.
- **The phase ladder in the app bar** (Inception, Discovery, … Trust, "Not production"): the shell's primary nav owns it. Cut.
- **Out of scope** is not asked here. It is a draft field (`out_of_scope[]`) that becomes exclusion criteria, so it lives with the criteria (05).
- **Machine output as a draft.** The canvas shows no proposal on this step. The step API's `scope` output (recommended paradigm, suggested concepts) is shown in a side card styled as a draft, because the researcher should see what the wizard reads before step 4 asks them to choose.
- **Phone.** `MobileScope` is a phone layout. The inception routes are not phone routes (see Mobile layout).

## Shared by 01, 04, 05, 06 and 07 (the draft screens)
The other specs refer to this section instead of repeating it.

**Route and shell.** `?draft=` carries the session id (`rec_` plus 32 lowercase hex characters; `SESSION_ID_RE` allows 6 to 64, the UI mints none). The `?console=<origin>` parameter is carried on every link, as on the screening screens. The inception routes are workspace-free on the engine (`_workspace_free`, `serve.py:74`): they must render with no workspace open, so the shell treats `/inception/*` as a workspace-free, live-only path (no Demonstration marker), as `/workspaces` is. The proxy already allows the calls (`apps/research-ui/app/api/console/[...path]/route.ts:68-86`, `src/scholar_harness/console/browser.py:53-61`): POST for drafts, preview, steps and genesis; PUT for one draft; **no DELETE**, so no screen offers to discard a draft.

**Stepper** (`nav`, label `inception.common.stepper.label`): `1 Scope`, `2 Explore` and `3 Direction` (plain text with the tag "Coming with recon", not focusable, no link), `4 Shape`, `5 Concepts and criteria`, `6 Review and create`, and `Done` only once the draft has `emitted`. The current step has `aria-current="step"`. Any linked step can be opened at any time; no step is locked, because the draft has no "step reached" field.

**Loading and saving.**
1. Every screen starts with `GET /drafts/{id}` and keeps the record's `updated_at` as `base_updated_at`. Fields the screen does not edit are carried through unchanged in the next save (PUT replaces the whole draft).
2. "Continue" saves with `PUT /drafts/{id}` `{draft, base_updated_at}` and, on 200, stores the returned `updated_at`, then navigates. If nothing changed on the page, it navigates without a PUT. "Save draft and exit" does the same and goes to `/inception/` (08). Leaving by any other link with unsaved changes opens the dialog `inception.common.leave.*` (Save and leave, Leave without saving, Stay); closing the tab asks through `beforeunload`.
3. **`DRAFT_CONFLICT`** (409, `details.updated_at`): the card says the draft changed in another tab, the terminal or an agent, that nothing was overwritten, and that the changes on this page are not saved. The form becomes read-only. One action: "Reload the saved draft" (`GET` again; the unsaved edits on this page are replaced, and the card says so first). It never retries the PUT on its own.
4. **`DRAFT_EMITTED`** (409, `details.emitted` has `slug`, `path`): on load or on save. The form is read-only and the card says this draft already created the workspace `{slug}`, with a link to Done (07).
5. A step proposal (`POST /steps/<step>` with the current in-memory draft) stores nothing and is never applied without a click on the proposal's own button. Stale answers are dropped by request order. The proposal sits in a card that is `surface` with a 1px dashed `ink-muted` border (the canvas `.draft`, `screens.css:58`), the label "Template draft · not yet yours" and the line "Written by the wizard's rules from your answers." The dashed `brand` border belongs only to the gate (GatePanel README).
6. `DRAFT_INCOMPLETE` (422, `details.missing`) names draft fields. They map to screens: `topic` to Scope (01); `paradigm`, `playbook`, `unit_of_analysis`, `proof`, `rqs` to Shape (04); `concepts` to Concepts and criteria (05); `title`, `lead_researcher` to Review (06). The sentence names the fields in plain words and links to the screen that owns each.

**Refusals** are shown through `StateCard` (`apps/research-ui/components/screening-state-card.tsx`): a plain sentence, what it affects, one next step, and the typed code under "Details". The shared codes (`DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE`, `DRAFT_CONFLICT`, `DRAFT_EMITTED`, `DRAFT_INVALID`, `DRAFT_INCOMPLETE`, the guard codes and `ENGINE_UNREACHABLE`) have their en copy in 08. Each screen lists the codes it can hit.

**One brand button per screen**, 44 px targets, light and dark tokens, RTL for ar.

## Entry / exit
- Entry: "Start a new review" on 08 (`POST /drafts`, then here); "Resume" on 08; the stepper from any other draft screen; a link "New review" on the Workspaces screen reaches 08 first (addendum in `docs/ux/phase2-screening/final/00-workspaces.md`).
- Exit: "Continue to Shape" goes to 04 after saving. "Save draft and exit" goes to 08. "Back to your drafts" (no save needed when clean) goes to 08.
- Gate: Continue is disabled until the question is not empty (the engine's `_require` for `topic`; the engine stays the authority). Nothing is written to a workspace on this screen.

## Data in
| Field | Source |
| :-- | :-- |
| the draft record `{session_id, created_at, updated_at, draft, emitted}` | `GET /api/v1/inception/drafts/{id}` ✓ M4a |
| `draft.topic`, `draft.start_year`, `draft.end_year`, `draft.languages` (default `["en"]` when absent) | same record |
| the wizard's reading of the question: `leanings[{paradigm, score}]`, `recommended_paradigm`, `default_concepts[]` | `POST /api/v1/inception/steps/scope` ✓ M4a, called with the current draft once the question is not empty (on load, and after each successful save) |
| workspaces root (shown in the "where it is saved" card) | `GET /api/v1/inception/drafts` `root` ✓ M4a (one read at load) |

`score` is a count of matched keywords, not a probability (`detect_leanings`, `intent.py:119`). The canvas showed "Leaning · 0.58" on step 4; no such number exists. The screens show the count in words ("2 keyword matches"), never as a decimal.

## Data out
- Save: `PUT /api/v1/inception/drafts/{id}` ✓ M4a, `{draft, base_updated_at}`; writes `topic`, `start_year`, `end_year`, `languages` and carries every other draft field through. Unknown keys are refused with `DRAFT_INVALID`, so the UI sends only draft fields. No journal event: a draft is not a workspace.
- Nothing else. The step call writes nothing.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/inception/drafts/{id}` | ✓ M4a `console/api/inception.py:80`, `drafts.py:72` |
| `PUT /api/v1/inception/drafts/{id}` | ✓ M4a `inception.py:88`, `drafts.py:81` |
| `POST /api/v1/inception/steps/scope` | ✓ M4a `inception.py:106`, `steps.py:165` |
| `GET /api/v1/inception/drafts` (root only) | ✓ M4a `inception.py:66`, `drafts.py:101` |

None is in `_PHONE_ROUTES` (`serve.py:55`): a phone token gets `TOKEN_SCOPE_REFUSED`. Writes sit under the loopback origin check (`ACTION_ORIGIN_REFUSED`) plus `HOST_REFUSED` and `TOKEN_REQUIRED`.

## States
- **Default**: eyebrow "Step 1 of 6 · Scope"; Literata h1 "What is your review about?"; lede "The question, the years and the languages set the window of the review. Nothing is written to a workspace in this step."; the form card; the side cards. One brand button: "Continue to Shape".
- **Empty**: a new draft (`draft` is `{}`): the question is empty, years are empty, language chip "English" is on (the engine default `["en"]`), Continue is disabled with the reason beside it ("Write your question first"). The side proposal card is replaced by the line "The wizard reads your question after you write it." Not an error; no code.
- **Loading** (skeleton): the h1 area and three field skeletons; no field is editable until the draft has loaded. The proposal card has its own skeleton (`aria-busy`) while `steps/scope` runs; the form is usable meanwhile.
- **Error** (typed refusal, `StateCard`):
  - `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE` on load: the card stands for the screen (`pageHeading`), with "Go to your drafts".
  - `DRAFT_CONFLICT`, `DRAFT_EMITTED`: as in the shared section.
  - `DRAFT_INVALID` on save (for example a year that is not a whole number): the card lists `details.errors` under Details; the field the error names gets `aria-invalid`.
  - `DRAFT_INCOMPLETE` from `steps/scope` cannot occur once the question is not empty; if it does, the proposal card shows the sentence and the screen is unaffected.
  - Guard codes `ACTION_ORIGIN_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `TOKEN_SCOPE_REFUSED` (phone): the shared guard cards (08). `ENGINE_UNREACHABLE` (client-side): the engine-unreachable card with "Try again".
- **Partial**: the question is written but years or languages are empty. That is valid: the years are optional (`start_year` and `end_year` are `None` until set) and the card says "Leave a year empty for no limit." The proposal card shows what it could read; the question alone is enough.
- **Offline**: the engine is local, so offline means "engine unreachable". The page keeps the loaded draft and any edits in the tab, shows "needs the engine on this computer" beside Continue and Save, and disables both. `beforeunload` guards the edits. Nothing is queued.
- **Protocol-changed**: cannot occur. A draft binds no protocol and no workspace. The nearest case is the draft changing under the page, which is `DRAFT_CONFLICT`.

## Desktop layout
Source: `Scope` (D2), reduced as listed above; split like the canvas (main about two thirds, side one third). Regions in order: shell and stepper; eyebrow, h1, lede; main card with **Your question** (textarea, 3 rows, visible label "Research question, in one or two sentences"), **From year** and **To year** (text inputs with `inputmode="numeric"`, to-year help "Leave empty for no limit"), **Languages** (chips; "English" is on; "Add a language" opens a small field for a language code such as `fr`, which becomes a chip; a chip can be removed; at least one stays on, because the engine reads an empty list as `["en"]`); button row at the end (Back to your drafts, Save draft and exit, Continue to Shape). Side: card **What the wizard reads** (draft styling: "Closest lens by keywords: {paradigm}, {n} keyword matches. You choose the lens in step 4." plus "Words it picked out as concepts: …" as plain chips that are **not** added to anything), card **Where this is saved** ("This draft is saved on this computer in {root}/.drafts, not in a workspace. Draft {id}", path LTR). The tokens come from `docs/ux/brand/tokens.json`; the new pieces are the stepper and the proposal card (both compose existing tokens). The one gate panel of the flow is on 06, not here.

## Mobile layout (≤ 640 px)
The inception routes are desktop-only on the engine: none is in `_PHONE_ROUTES`, and a phone-scoped token gets `TOKEN_SCOPE_REFUSED` (plan §4, "write screens are desktop only"). So `MobileScope` serves a **narrow desktop window**, not a phone. At ≤ 640 px the layout is one column in this order: back link and draft id, eyebrow and h1, question, From and To side by side, Languages (chips at 44 px), the proposal card, the where-saved card, then the button row stacked and full width: "Save draft and exit" (secondary) above "Continue to Shape" (brand), both 44 px. The canvas phone's sticky action bar is kept (`m-actions`). The step number reads "Step 1 of 6". A real phone (the first read is refused with `TOKEN_SCOPE_REFUSED`) shows one card, `inception.common.phone.desktopOnly` ("Starting a review is done on your desktop. Open this page there."), with a 44 px link "Go to screening" (`/screening`). No form on a phone. The canvas's Search-mode chips and sample-size field are not built at any width.

## Keyboard
Focus order: skip link, shell, stepper (linked steps only), h1, question, From year, To year, language chips (each a toggle button, `aria-pressed`), "Add a language" and its field, Back to your drafts, Save draft and exit, Continue to Shape, then the side cards. `Enter` in a single-line field does nothing destructive (it does not submit); `Enter` in the add-language field adds the chip, `Escape` closes it and returns focus to "Add a language". After a failed save, focus moves to the refusal card heading. After a successful save and navigation, focus is on the h1 of the next screen. There are no single-key shortcuts.

## Copy
Keys in `apps/research-ui/lib/inception-copy.ts` (en master, then fr and ar; fr/ar are added by the implementer, not here). No literal `aria-label`, `title`, `alt` or `placeholder` attributes (N9 guard).

Shared (`inception.common.*`):
- `stepper.label` "Inception steps"; `stepper.scope` "1 Scope"; `stepper.explore` "2 Explore"; `stepper.direction` "3 Direction"; `stepper.shape` "4 Shape"; `stepper.criteria` "5 Concepts and criteria"; `stepper.review` "6 Review and create"; `stepper.done` "Done"; `stepper.comingWithRecon` "Not built yet" (was "Coming with recon" until M3h-providers: recon runs over HTTP since M4c, the Explore and Direction screens do not exist).
- `eyebrow` "Step {n} of 6 · {name}"; `draftId` "Draft {id}"; `draftSaved` "Draft saved {date}"; `unsaved` "Unsaved changes"; `saving` "Saving the draft"; `saved` "Draft saved".
- `back` "Back to your drafts"; `saveExit` "Save draft and exit"; `offlineNote` "needs the engine on this computer"; `asOf` "As of {time}".
- `leave.title` "Leave without saving?"; `leave.body` "Your changes on this page are not in the draft yet."; `leave.save` "Save and leave"; `leave.discard` "Leave without saving"; `leave.stay` "Stay".
- `proposal.badge` "Template draft · not yet yours"; `proposal.source` "Written by the wizard's rules from your answers."
- `phone.desktopOnly` "Starting a review is done on your desktop. Open this page there."; `phone.go` "Go to screening".
- `readonly.emitted` "This draft already created {slug}. It can no longer be edited here."; `readonly.conflict` "Reload the saved draft to edit it."

Scope (`inception.scope.*`):
- `title` "What is your review about?"; `lede` "The question, the years and the languages set the window of the review. Nothing is written to a workspace in this step."
- `topic.label` "Research question, in one or two sentences"; `topic.help` "Write it the way you would say it to a colleague. You refine it into research questions in step 4."; `topic.required` "Write your question first".
- `years.from` "From year"; `years.to` "To year"; `years.help` "Leave a year empty for no limit."
- `languages.label` "Languages"; `languages.add` "Add a language"; `languages.code` "Language code, for example fr"; `languages.remove` "Remove {language}"; `languages.help` "Records in other languages are excluded at screening only if you write an exclusion for them."
- `reads.title` "What the wizard reads"; `reads.lens` "Closest lens by keywords: {paradigm}, {n} keyword matches. You choose the lens in step 4."; `reads.none` "No keyword matches any lens yet."; `reads.concepts` "Words it picked out as concepts"; `reads.waiting` "The wizard reads your question after you write it."; `reads.note` "These are suggestions only. Nothing is added until you add it in step 5."
- `saved.title` "Where this is saved"; `saved.body` "This draft is saved on this computer in {root}, not in a workspace. A workspace is written only at step 6."
- `continue` "Continue to Shape".
- Refusals use the shared keys `inception.refusal.<CODE>.{title,body,affects,action}` (08).

## Accessibility
- Contrast pairs from tokens: `ink` on `ground`, `ink-muted` captions on `surface`, `brand` on `brand-soft` for the current step; the "Coming with recon" tag is `ink-muted` text, not colour alone. Status never rests on colour only.
- The question and years have visible labels and `aria-describedby` for their help; the disabled Continue carries `aria-describedby` pointing at the reason; refusals use `role="alert"`; "Draft saved" is announced with `aria-live="polite"`.
- Language chips are a `role="group"` labelled "Languages", each chip a button with `aria-pressed`; the add field has a visible label.
- The proposal card is labelled by its badge; its keyword matches are text.
- RTL (ar): the layout mirrors; the stepper order reverses; the draft id, the saved path, language codes and years are `dir="ltr"`; numerals Latin; the question textarea is `dir="auto"` because the question may be in any language.
- Screen readers: the stepper is an ordered list; the two unavailable steps are list items with text, not links, so they are read but not focusable.

## Acceptance tests
Vitest `apps/research-ui/tests/inception-scope.test.tsx`: a new draft renders the empty state with Continue disabled; typing enables it; Continue sends exactly one `PUT` with `{draft, base_updated_at}` and carries the other draft fields unchanged; no `PUT` when clean; `DRAFT_CONFLICT` shows the sentence and the "Reload the saved draft" action, makes the form read-only, and never retries; `DRAFT_EMITTED` shows the Done link; `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID` and `DRAFT_UNREADABLE` each map to copy and show their code under Details; the proposal card is styled as a draft and applies nothing on its own; the stepper shows steps 2 and 3 as text without links; the offline state disables Continue; `inception-scope.i18n` (keys exist in en; N9 guard); `inception.live-only` (no Demonstration marker on `/inception/*`).
Playwright `apps/research-ui/tests-browser/inception.spec.ts` against a stateful fake of the inception API (this screen's part): start a draft, write a question and years, add `fr`, Continue, reload and see the values; a second tab saves first and the first tab's Continue shows the conflict card; the proposal card shows after the question is written; RTL (ar) pass; axe in light and dark; no horizontal overflow at 375 and 1440 px; a phone-scoped token shows the desktop pointer and no form.

## Open questions
None.

## As built (M4b, 2026-11-09)
- Languages are one comma-separated field (codes, LTR), not chips with "Add a language".
- There is no side proposal card; the leaning the engine reads from the topic is shown on Shape (04), where it is used.
- Offline is the `ENGINE_UNREACHABLE` card on the failed call; controls are not pre-disabled and there is no `beforeunload` guard.
- Continue is disabled until the topic is written, with the reason beside it, as specified.
- Copy keys and their en, fr and ar texts are the code's: `apps/research-ui/lib/inception-copy.ts` (screen copy) and `apps/research-ui/lib/screening-states.ts` (refusal cards). The Copy section above gives the design intent and the English wording; where a key name or a sentence differs, the code is the record and `tests/inception-copy.test.ts` pins every key in every locale.
