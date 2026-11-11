# 08 States and resume draft    Status: FINAL, built (M4b, PR #209) | Phase 0 Inception | Route `/[locale]/inception/` (desktop only) | Milestone M4b

Boards: `States` (D9, `docs/ux/phase0-inception/final/project/States.dc.html`) and the "Resume your draft" card of `Main` (D1, `.../Main.dc.html`). Contract: `docs/architecture/inception-api.md` (Routes: list, create); refusal rows in `docs/architecture/screening-api-contract.md` §7 (lines 197-210). Code: `src/scholar_harness/console/api/inception.py` (`list_drafts` `:66`, `create_draft` `:71`), `src/scholar_harness/inception/drafts.py` (`DraftStore.listing` `:101`, `SESSION_ID_RE` `:25`), `src/scholar_harness/console/refusals.py:94-107`, `apps/research-ui/components/screening-state-card.tsx`, `apps/research-ui/lib/screening-states.ts`. Decisions: `docs/decisions.md`, 2026-11-08 "Inception drafts live under the workspaces root, with one session id". The shared draft rules are in 01 "Shared by 01, 04, 05, 06 and 07".

**Purpose.** Pick up an unfinished review draft, or start a new one; and, for every other inception screen, name what happens when a step cannot go on as planned (this spec holds the shared refusal copy).

**Changed from the canvas.** Every cut or change:
- **Where it lives.** The canvas puts drafts in the Workspaces table beside reviews and in the recon cache. Drafts are in `<workspaces root>/.drafts/<session id>/draft.json`, the workspace list skips dot-folders (decision 2026-11-08), so drafts have their own page, reached by the "New review" link on the Workspaces screen (addendum in `00-workspaces.md`).
- **"Resume at step 5", "Needs you · 3 criteria to decide", "stopped at Concepts and criteria".** The list item has `session_id, title, topic, created_at, updated_at, emitted` only (`drafts.py:115`); the draft has no "step reached" field and unknown draft keys are refused. Resume opens Scope (01); see open question 2.
- **No "Start over from this question" and no "Discard draft".** The browser may use GET, HEAD, POST and PUT only (`browser.py:117`, `route.ts:198`), so `DELETE /drafts/{id}` is not reachable and discard is deferred. "Start over" would only add another draft that cannot be removed. Cut. The page says so in one line.
- **No pool age, "Refresh pool, then resume".** Recon has no HTTP surface.
- **No "Agent proposal" card, no "Do this with your agent in Claude", no "Review on your phone / Show pairing code", no recon cache line.** None has a source in the draft API; inception routes are not phone routes.
- **Recon states in the canvas States board are held**: "No direction has two anchor papers" (`NO_ANCHORED_DIRECTION`), "Thin pool" (`POOL_THIN`), "Unanchored term" (`TERM_UNANCHORED`), "Search failed" (`PROBE_FAILED`), "Scope changed" (`POOL_STALE`), "Narrower search found nothing" (`DELTA_EMPTY`), "Gap check partial" (`DELTA_PARTIAL`) and the "Loading: searching 25 papers" card. They are live since M4d (steps 2 Explore and 3 Direction, specs 02 and 03; `NO_ANCHORED_DIRECTION`, `POOL_THIN`, `PROBE_FAILED` and `POOL_STALE` appear there as screen states or typed refusals; the `DELTA_*` cards are not built because the gap check is not shown in the browser; `TERM_UNANCHORED` appears on 05 as "not in the pool").
- **Canvas card to spec.** "Workspace exists" is 06 (the two confirmations). "Resume a draft" is this screen. "Engine unreachable" is below (shared). "Empty" is this screen. "Loading" is each screen's skeleton.

## Entry / exit
- Entry: the "New review" link on the Workspaces screen (00, addendum); "Back to your drafts" and "Save draft and exit" on the draft screens; the "Go to your drafts" action of `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID` and `DRAFT_UNREADABLE`; "Start another review" on 07; a direct URL.
- Exit: "Start a new review" creates a draft and goes to Scope (01); "Resume" on a row goes to Scope (01) of that draft; "Done" on a finished draft's row goes to Done (07); "All workspaces" goes to `/workspaces`.
- Gate: none that writes a workspace. "Start a new review" writes one small draft file under the workspaces root; that is the only write on the screen.

## Data in
| Field | Source |
| :-- | :-- |
| `root` (the workspaces folder) and `items[{session_id, readable, title, topic, created_at, updated_at, emitted}]`, newest first; an unreadable draft is `{session_id, readable: false, updated_at: ""}` | `GET /api/v1/inception/drafts` ✓ M4a |

`emitted` is `null` or `{slug, path, protocol_fingerprint, replaced, at}`. The screen sorts nothing: it shows the engine's order.

## Data out
- Start: `POST /api/v1/inception/drafts` ✓ M4a, body `{draft: {}}`, answers `201 {session_id, created_at, updated_at, draft, emitted: null}`; the screen navigates to `scope?draft=<session_id>`. The draft is `{}`; the screens treat an absent `languages` as `["en"]` (the engine default, `steps.py:96`) and write it on the first save. No journal event: a draft is not a workspace.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/inception/drafts` | ✓ M4a `console/api/inception.py:66`, `drafts.py:101` |
| `POST /api/v1/inception/drafts` | ✓ M4a `inception.py:71`, `drafts.py:65` |
| `DELETE /api/v1/inception/drafts/{id}` | ✓ engine `inception.py:97`; **not offered**: the browser allowlist serves no DELETE (deferred) |

Not in `_PHONE_ROUTES` (`serve.py:55`); the POST sits under the loopback origin check.

## States
- **Default**: Literata h1 "Which draft are you continuing?"; lede "A draft is your unfinished answers to the review interview. It is saved on this computer in {root}/.drafts, and it is not a workspace until the last step."; the newest unfinished draft as a **Resume card** (badge "Resume a draft" in the brand role as text, the title or the question, "Last saved {date} · draft {id}", a secondary link "Resume"); a table of the other drafts (Title or question, Last saved, Status, action). One brand button: "Start a new review". A line under the table: "Drafts cannot be discarded from the app yet."
- **Empty** (no items): EmptyState "No drafts yet" with the caption "A review starts with a question. Six steps later you confirm, and only then a workspace folder is written." and the brand button "Start a new review". Not an error; no code.
- **Loading** (skeleton): a card skeleton and three table rows; the button renders disabled. Starting: the button reads "Starting a new review", disabled, until the 201 arrives; no optimistic row.
- **Error** (typed refusal, `StateCard`): the listing failing stands for the screen. Codes: guard codes (below) and `ENGINE_UNREACHABLE` (client-side, "Try again"). `POST /drafts` failing shows the card above the button and keeps the list: `DRAFT_EXISTS` (409, cannot occur: the client sends no id), `DRAFT_INVALID` (cannot occur with `{}`), `ENGINE_UNREACHABLE`, the guard codes. An unrecognised 5xx renders as its own code (the `stateCopy` fallback never guesses).
- **Partial**: some drafts are unreadable. They are listed, never hidden: a row "Unreadable draft" in the blocked role as text, the id in mono, the sentence "This file cannot be read. Your other drafts are not affected.", and no Resume (the engine would answer `DRAFT_UNREADABLE`, 500). Finished drafts (`emitted` set) show the badge "Workspace created" in the include role and the link "Done" instead of "Resume"; they are listed because discard is not offered, and they stay below the resumable ones.
- **Offline**: the engine is local; offline means unreachable. The last listing stays with "As of {time}"; Start and Resume are disabled with "needs the engine on this computer".
- **Protocol-changed**: not applicable. Drafts bind no protocol.

### Blank drafts
Every "Start a new review" makes a new file and none can be removed. A draft with no title and no question (`title` and `topic` empty) is shown as "Empty draft · started {date}", so it is recognised. Open question 1.

## Shared refusals (for 01, 04, 05, 06, 07 and this screen)
`StateCard` reads `stateCopy(locale, code)` from `apps/research-ui/lib/screening-states.ts`. The implementer registers the entries below in `STATES` (from `INCEPTION_STATES` in `inception-copy.ts`) and adds the actions `draft-list` ("Go to your drafts", link to `/inception/`), `draft-reload` (re-reads the draft; uses the screen's `onRetry`), `draft-done` (link to `/inception/done?draft=`), `inception-step` (link to the step in `details`). Each entry shows the sentence, what it affects, one next step, and the code under Details; the role is the brand status role. Codes already registered for the Workspaces screen are reused: `WORKSPACE_TITLE_INVALID`, `WORKSPACE_PATH_REFUSED`, `WORKSPACE_ROOT_UNAVAILABLE`, `WORKSPACE_NOT_VALID`, `WORKSPACE_BUSY`, `RESTART_UNSUPPORTED`, `ENGINE_UNREACHABLE`, `ACTION_ORIGIN_REFUSED`, `TOKEN_SCOPE_REFUSED`. **`WORKSPACE_EXISTS` is not reused**: the registered copy is for the create-by-title flow; at genesis its meaning is a confirmation, so 06 renders it from `inception.review.exists.*` and not from `STATES`.

| Code (HTTP) | Role | en title | en body | en affects | en action |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `DRAFT_NOT_FOUND` (404) | blocked | This draft does not exist | No saved draft has this id. It may belong to another workspaces folder. | This page only | Go to your drafts |
| `DRAFT_ID_INVALID` (422) | blocked | That is not a draft link | A draft id is "rec_" followed by letters and digits. The link may be cut short. | This page only | Go to your drafts |
| `DRAFT_UNREADABLE` (500) | blocked | This draft cannot be read | The saved file is damaged or unreadable. Your other drafts are not affected. | This draft only | Go to your drafts |
| `DRAFT_EXISTS` (409) | unclear | A draft with this id already exists | Starting a new draft should never reuse an id. Nothing was overwritten. | Starting a draft | Try again |
| `DRAFT_CONFLICT` (409) | unclear | The draft changed since you opened it | Another tab, your terminal or an agent saved a newer version. Nothing was overwritten, and the changes on this page are not saved. | Saving this page | Reload the saved draft |
| `DRAFT_EMITTED` (409) | unclear | This draft already created a workspace | It was written as {slug}. A draft is written once. To change the protocol, start a new review with the same title and replace it. | Editing this draft | Go to the finished workspace |
| `DRAFT_INVALID` (422) | blocked | An answer is not in a form the wizard knows | A field has the wrong type, or names a lens or playbook that does not exist. Details lists them. | Saving and the suggestions | Check the answers on this page |
| `DRAFT_INCOMPLETE` (422) | unclear | The wizard needs more answers first | It needs {fields}. Each is asked in the step named beside it. | This step's suggestions and the review | Go to {step} |
| `STEP_UNKNOWN` (404) | blocked | The wizard has no such step | The page asked for a step the engine does not have. This should not happen. | This page only | Reload the page |
| `CRITERIA_UNDECIDED` (422) | unclear | {n} criteria still need your answer | The wizard wrote these criteria. Each needs Accept or Drop from you before the protocol is compiled. | The review and the workspace | Decide the criteria |
| `CRITERIA_MISSING` (422) | unclear | The protocol needs both sides | It needs at least one accepted inclusion criterion and one accepted exclusion criterion. Missing: {sides}. | The review and the workspace | Add a criterion |
| `INTENT_INVALID` (422) | blocked | The compiler refused these answers | A cross-check on years, languages or criteria failed. Details lists each field and message. | The review and the workspace | Check the answers it names |
| `SCREENING_BOUND` (409) | blocked | This workspace has screening under the old protocol | {events} decision events, {files} batch decision files and {published} published screening exist. Replacing the protocol leaves them pointing at criteria that no longer exist. | Replacing the protocol | Type the workspace name to confirm |
| `CONFIRMATION_MISMATCH` (422) | blocked | That is not the workspace name | Type {expected} exactly to replace it. Nothing was changed. | This confirmation | Type {expected} |

`STEP_UNKNOWN` and `DRAFT_EXISTS` are listed so a stray response renders instead of falling back; the screens cannot cause them. The guard codes `HOST_REFUSED` and `TOKEN_REQUIRED` use whatever the shared guard cards show; where `STATES` has no entry they render as their own code. The proxy's own refusals `CONSOLE_ORIGIN_REFUSED`, `CONSOLE_METHOD_REFUSED` and `CONSOLE_PATH_REFUSED` (`browser.py:106`) render as their code too; a `CONSOLE_METHOD_REFUSED` on a DELETE is why discard is not offered.

**Engine unreachable** (client-side `ENGINE_UNREACHABLE`, existing entry `screening-states.ts:137`): the shared card, with the draft screens' addition: "Your answers up to the last save are in the draft." (`inception.common.unreachable.kept`), "Try again" and "All workspaces". The existing body names the screening engine; the inception pages add the sentence above under it and do not replace the card.

## Desktop layout
Source: `States` (D9) and `Main` (D1) reduced as listed. Regions: shell; eyebrow "Drafts · {n} in progress"; h1, lede; Resume card; table card; footer caption "Drafts cannot be discarded from the app yet. This computer · {root}/.drafts" (LTR path). Table columns: Title or question (the title if set, else the question, else "Empty draft"), Last saved, Status (badge: "In progress" in the unclear role as text, "Workspace created" include, "Unreadable" blocked), action (Resume or Done, a 44 px link button). The brand button "Start a new review" sits at the top right of the header row, as in `Main`. Components: the existing table, badge, EmptyState and StateCard.

## Mobile layout (≤ 640 px)
Desktop-only on the engine (see 01); a narrow desktop window gets one column: h1, lede, the brand button full width (44 px), the Resume card, then the other drafts as cards (title or question, last saved, status badge, a 44 px action link). A real phone shows the desktop pointer card (`inception.common.phone.desktopOnly`) from the refused first read.

## Keyboard
Focus order: skip link, shell, h1, "Start a new review", the Resume card's link, table rows in order (each action link), footer. There are no single-key shortcuts on the inception screens (the Workspaces screen's `n` is not repeated here). After Start, focus is on the h1 of Scope. After a refusal, focus is on the card heading.

## Copy
Keys in `apps/research-ui/lib/inception-copy.ts` (en master, then fr and ar).
- `inception.list.eyebrow` "Drafts · {n} in progress"; `title` "Which draft are you continuing?"; `lede` "A draft is your unfinished answers to the review interview. It is saved on this computer in {root}/.drafts, and it is not a workspace until the last step."
- `list.start` "Start a new review"; `list.starting` "Starting a new review"; `list.resumeCard` "Resume a draft"; `list.resume` "Resume"; `list.done` "Done"; `list.last` "Last saved {date} · draft {id}"; `list.untitled` "Empty draft · started {date}"; `list.col.{title,saved,status,action}` "Title or question", "Last saved", "Status", "Action"; `list.status.{progress,created,unreadable}` "In progress", "Workspace created", "Unreadable"; `list.unreadable` "This file cannot be read. Your other drafts are not affected."; `list.noDiscard` "Drafts cannot be discarded from the app yet."; `list.footer` "This computer · {root}/.drafts"; `list.workspaces` "All workspaces".
- `list.empty.title` "No drafts yet"; `list.empty.body` "A review starts with a question. Six steps later you confirm, and only then a workspace folder is written."
- `inception.common.unreachable.kept` "Your answers up to the last save are in the draft."; `inception.common.offline` "needs the engine on this computer".
- Refusals: `inception.refusal.<CODE>.{title,body,affects,action}` for the 14 codes in the table; en text as in the table; fr and ar by the implementer.

## Accessibility
- The Resume card and table are labelled; the table has real headers and a caption; each action link names its draft ("Resume: {title}"). Status is text in a badge, never colour alone; `blocked` is text colour only.
- The id is mono, selectable, LTR; the short form `rec_7f3a…` is for display, the full id is in the link and in the row's accessible name only through the title.
- Refusals `role="alert"`; the Start button announces "Starting a new review" with `aria-live="polite"`.
- Contrast pairs from tokens (`ink` on `surface`, `brand` on `ground` for the brand button). RTL (ar): the layout and table columns mirror; ids, the root path and dates' digits are LTR/Latin; titles and questions are `dir="auto"`.
- Touch and pointer targets at least 44 px.

## Acceptance tests
Vitest `apps/research-ui/tests/inception-states.test.tsx`:
- the list renders the engine's order; the newest unfinished draft is the Resume card; an unreadable item shows no Resume; an emitted item shows "Workspace created" and a Done link; an item with no title and no topic is "Empty draft";
- Start posts `{draft: {}}` once, disables itself while pending, and navigates to Scope with the new id;
- no control calls `DELETE` and the page says discard is unavailable;
- every shared code in the table maps to a copy key and shows its code under Details; an unknown code renders as itself; `DRAFT_CONFLICT` offers "Reload the saved draft" and `DRAFT_EMITTED` links to Done;
- the empty state and the offline state render; the unreachable card adds the kept-draft sentence;
- i18n and N9 guard; `inception.live-only` (no Demonstration marker).
Python: `tests/console/test_console_refusals.py` already keeps the M4a codes in step with `refusals.py:94-107`; no new engine code is added by this screen.
Playwright `inception.spec.ts` (this screen's part, stateful fake): empty list, start, reach Scope; two drafts listed newest first; one unreadable; one finished with a Done link; engine down shows the card; RTL pass; axe in light and dark; no horizontal overflow at 375 and 1440 px.

## Open questions
Answered by the researcher, 2026-11-09:
1. Blank drafts: "Start a new review" always creates a draft; a draft with no title and no topic is listed as "Empty draft". The UI applies no reuse rule.
2. Resume opens Scope (01); the stepper links every built step.

None open.

## As built (M4b, 2026-11-09)
- There is no Resume card for the newest draft: every draft is a row with Resume (or "See what was created" once it made a workspace).
- The refusal cards are entries in `STATES` (`lib/screening-states.ts`), not a separate `INCEPTION_STATES` table, and no new StateCard actions were added: the wording differs from the table above but keeps its what-happened / affects / next-step shape, and the engine's `missing` fields are listed with links to their step.
- Copy keys and their en, fr and ar texts are the code's: `apps/research-ui/lib/inception-copy.ts` (screen copy) and `apps/research-ui/lib/screening-states.ts` (refusal cards). The Copy section above gives the design intent and the English wording; where a key name or a sentence differs, the code is the record and `tests/inception-copy.test.ts` pins every key in every locale.
