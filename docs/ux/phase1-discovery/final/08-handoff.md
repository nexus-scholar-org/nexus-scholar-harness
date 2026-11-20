# 08 Hand-off to screening    Status: FINAL, built (M3c-screens, PR #216) | Phase 1 Discovery | Route `/[locale]/discovery/handoff` (desktop only) | Milestone M3c-screens

Amended 2026-11-17 for M3i-harvest-robustness (accepted by the researcher 2026-11-15 as answer R5 of the M10b spec questions; the choices made while building it are in `docs/decisions.md`, 2026-11-17, accepted 2026-11-18). Where this amendment contradicts the text below, the amendment wins. The full text is the section **"An unfinished preparation (M3i)"** at the end of this file.

Boards: `Handoff` (D8, `docs/ux/phase1-discovery/final/project/Handoff.dc.html`); no phone board (`MobileStatus` carries only the Status tab). Packet: `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.8, §6; records `docs/roadmap/milestones/M3d-engine.md` decisions 1-3, 6, 12, 13 and `M3b-api.md`. Code: `src/scholar_harness/console/api/discovery.py:655` (`handoff`), `console/api/screening_v1.py:563` (corpus view), `:603` (accept), `src/scholar_harness/corpus_accept.py:520`, `apps/research-ui/components/screening-home.tsx:305` (Prepare entry), `apps/research-ui/components/screening-state-card.tsx`. Decisions: `docs/decisions.md` 2026-11-10 "A browser harvest does not freeze the corpus; the hand-off screen does" and "Discovery over HTTP: seven decisions". Brand: `docs/ux/brand/BRAND_BOOK.md` (GatePanel: the dashed `brand` border is for the gate only), `docs/ux/brand/tokens.json`. Shared rules (step bar, run selector, refusal copy, hard rules): see 01-plan.md, Shared.

**Purpose.** Read what screening will receive and accept it, which freezes the corpus; after that, go to screening.

**Changed from the canvas.** Every cut or change:
- **Headline "Accept these 3,241 works".** The number is `corpus.preview.unique_studies` as the engine wrote it (with `identified` and `duplicates`); the browser computes no count. If `preview` is `null` the headline drops the number.
- **"Corpus snapshot sha256:[corpus]…" before the accept, "from run 003 · dedup decisions to 2026-11-03 09:43 UTC".** No snapshot exists before the accept, so no fingerprint is shown; it appears after the accept as `corpus.accepted.artifact_id`. "Dedup decisions to ..." is cut (near-twin decisions are M3e; `dedup_decided_at` is not in the answer). The card shows the run (`run`) and the protocol fingerprint (`protocol_fingerprint`) the engine sends.
- **"Carried forward: per-database legs and the dedup event fill the PRISMA identification box."** A claim with no field behind it; cut. The Report (06) shows identification.
- **The Crossref sentence** ("In the UAV v0.3 review, Crossref records were about 70 times less likely to be included ... Expect most exclusions to come from Crossref.") is a hard-coded domain claim about another review. The browser makes no domain decision; cut.
- **"Imports 0%"** in the mix: the mix lists providers as the engine counted them (`provider_mix[]`); no separate imports row.
- **"Near-twin pairs left undecided: 12 / Counted separately"** is cut: `near_twins_undecided` is `null` until the pair review exists (M3e, RELEASE; packet decision 2).
- **Option "Fill missing abstracts from OpenAlex before screening".** Cut. Hydration is a stage the run already performs (`ABSTRACT_HYDRATION`); no route says whether it ran for this corpus (the SSE `hydration` stage is only on the live job and jobs are in memory; `GET /discovery/handoff` has no field). A checkbox would promise a choice the engine does not offer and a status the page cannot read. The screen shows only what is true now: `abstracts.with_abstract`, `title_only`, `share_with_abstract`.
- **Option "Hide the database of origin and noise statistics while screening".** Cut as a checkbox here, and not a link. The existing screening setting `blinding` (`PUT /screening/settings`, `screening_v1.py` settings, `reveal_after_decision`) hides the agent's draft until the human decides, not the database of origin; no setting hides the origin (open question 1). The screen therefore claims nothing about blinding.
- **"Accept corpus and prepare screening" becomes "Accept this corpus".** Prepare stays on screening Home, which already offers it (`screening-home.tsx:305`, `POST /screening/prepare`, batch size 5 to 100, 409 `SNAPSHOT_NOT_ACCEPTED`). Duplicating it here would put a second batch-size choice and a second job start in discovery. After the accept the screen's one brand button is "Go to screening".
- **"Export RIS for Zotero"** is out (packet §4.8: out of this packet).
- **"Run from the terminal" disclosure** (the `agent_screen.py prepare` line): cut. Home holds the terminal fallback; this screen is the browser path.
- **Phone.** No phone board; the screen is desktop-only (see Mobile layout).

## Entry / exit
- Entry: the step bar; "Continue to hand-off" from the Report (06); a direct URL.
- Exit before the accept: "Search again" (03), "Read the report" (06), "Stage an export" (04, only while `staging_refused` is `null`). After the accept: "Go to screening" (`/[locale]/screening/`, Home), carrying `?console=`.
- Gate: **Accept this corpus** = `POST /api/v1/screening/corpus/accept`. It freezes a corpus snapshot with its own fingerprint, journals `ARTIFACT_ACCEPTED` and `CORPUS_SNAPSHOT_ACCEPTED` (with the `run`, agent `scholar-harness-console`), and from then on runs and imports answer `CORPUS_ALREADY_ACCEPTED`. It is the only browser path that builds the snapshot (decision 2026-11-10). A second harvest is allowed before the accept; an import only before any harvest (`staging_refused` says why).

## Data in
| Field | Source |
| :-- | :-- |
| `corpus.state` (`EMPTY`, `STAGED`, `ACCEPTED`), `corpus.from_discovery`, `corpus.preview {identified, duplicates, unique_studies}`, `corpus.accepted {artifact_id, accepted_at, records, studies, duplicates}`, `corpus.staging_refused {code, message}` | `GET /api/v1/discovery/handoff` → `corpus` ✓ M3d-engine (`discovery.py:655`; the same object as `GET /screening/corpus`, `screening_v1.py:563`) |
| `run` (newest run whose records became the corpus; `null` if none) | same |
| `provider_mix[{provider, records, share}]` (`share` is the fraction as written, 4 places) | same |
| `abstracts {with_abstract, title_only, share_with_abstract}` | same |
| `outside_year_window` | same |
| `lower_bound_databases[]` (names whose leg hit its cap in the corpus run) | same |
| `protocol_fingerprint` | same |
| `near_twins_undecided` (always `null`) | same; not shown |

`provider_mix` counts a work once per database that found it, so shares can add up to more than 100 %; the card says so. The bar's segment widths use `share` as written; the browser does not normalise it.

## Data out
- Accept: `POST /api/v1/screening/corpus/accept` ✓ M3d-engine (`screening_v1.py:603`; browser allowlist: POST already allowed), empty body. Answers the corpus view (`state: "ACCEPTED"`, `accepted {...}`). Journals `CORPUS_SNAPSHOT_ACCEPTED` and `ARTIFACT_ACCEPTED`. The page re-reads `GET /discovery/handoff` after the answer and trusts the engine's `accepted`, never its own state.
- Nothing else. No prepare, no settings write.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/discovery/handoff` | ✓ M3b-api `console/api/discovery.py:655` (`staging_refused` ✓ M3d-engine decision 12) |
| `POST /api/v1/screening/corpus/accept` | ✓ `console/api/screening_v1.py:603` (hand-off branch ✓ M3d-engine decision 1, `accept_discovery_corpus`) |
| `GET /api/v1/discovery/runs` (selector, stale marker) | ✓ M3b-api `discovery.py:397` |
| `POST /api/v1/screening/prepare` | ✓ existing; **not called here** (screening Home owns it) |
| `PUT /api/v1/screening/settings` | ✓ existing; **not called here** |
| a route saying whether hydration ran; a route for the origin-hiding option; `near_twins_undecided` | ✗ none planned; M3e-neartwins for the last (RELEASE) |

Not in `_PHONE_ROUTES` (`serve.py:55`): `TOKEN_SCOPE_REFUSED` (403) on a phone.

## States
- **Default** (`corpus.state` `STAGED`, `from_discovery` true): eyebrow "Step 7 of 7 · Hand-off to screening · gate"; Literata h1 "Accept these {unique_studies} works as the corpus you will screen?"; lede "Accepting freezes a corpus snapshot with its own fingerprint. Screening reads only that snapshot, so later runs cannot change what you screen."; **Provider mix** (a bar and a list: provider, records, share; caption "A work found in two databases is counted in both, so shares can add up to more than 100 %."); **What screening will receive** table: Records identified, Duplicates removed, Works (the `preview` numbers as written), With an abstract, Title only (`title_only`, "Hard to screen" in the unclear role as words), Published outside the year window, Lower-bound databases (names; "stated in the report" link to 06); card **From** (run `run`, protocol fingerprint, mono); the gate panel (the one brand button "Accept this corpus", with the line "Nothing is handed to screening until you accept. The accept is recorded with the time and the snapshot fingerprint."); secondary links "Search again" and "Read the report". If `lower_bound_databases` is not empty a unclear-role note above the gate: "{names}: a count stopped at its cap is a lower bound. The report says so." (does not block the accept). If the corpus run had failed databases, the engine accepts the corpus as partial and the Report (06) lists the failure; the screen links to it and says nothing more because the answer does not name them.
- **Accepted** (`state: "ACCEPTED"`): no gate. h1 "This corpus is accepted." The card **Accepted corpus** prints `accepted.artifact_id` (mono, selectable), `accepted_at`, `records`, `studies`, `duplicates` as written. The one brand button is "Go to screening" (screening Home, where Prepare lives). No "Run again", no import, no re-accept; `staging_refused` is `CORPUS_ALREADY_ACCEPTED` and the step-bar links to Harvest and Import are shown as read-only history.
- **Empty** (`state: "EMPTY"`, or `STAGED` with nothing yet and `run` `null`): "There is nothing to hand off yet." Affects: the hand-off. Actions: "Go to Harvest" and "Stage an export" (04). The Accept button is not shown. Not an error (role `exclude`); a forced accept would be `NOTHING_STAGED`.
- **Staged exports** (`STAGED`, `from_discovery` false): the corpus came from staged database exports, not a harvest. The same layout, with `sources[]` labels listed from `corpus.sources`, the provider mix as the engine wrote it for `verified.json` (it can be empty: say "No harvest records" rather than a bar), and "Search again" replaced by the sentence from `staging_refused` (after a harvest) or hidden (before). Accept is the same call.
- **Loading** (skeleton): headline, bar and table skeletons, `aria-busy`; no number before the read finishes; the Accept button is absent until `GET /discovery/handoff` has answered. During the accept the button reads "Accepting the corpus" and is disabled; there is no optimistic Accepted state.
- **Error** (typed refusal, `StateCard`; see 07 for the sentences):
  - On the read: `PROTOCOL_MISSING` (409), `PROTOCOL_INVALID` (422): shared cards; `ENGINE_UNREACHABLE`; `TOKEN_SCOPE_REFUSED`.
  - On the accept, shown above the gate with the page kept: `CORPUS_ALREADY_ACCEPTED` (409: re-read and show the Accepted state; it is the finished state, not a failure); `NOTHING_STAGED` (409: Empty state); `PROTOCOL_CHANGED_SINCE_RUN` (409: "{run} searched a query or year window the protocol no longer has; run the search again before accepting its corpus", with the action "Search again" linking to 03); `PROTOCOL_INVALID` (422, "The protocol cannot be read", action to inception); any other 409 corpus code (`ACCEPT_CORPUS_REFUSED`, `PROTOCOL_METHOD_INVALID`, ...): the engine's code under Details and its message, with "Try again"; the page never guesses a meaning for an unregistered code.
- **Partial**: `abstracts.title_only` > 0 (shown as a count with words, not a block); `lower_bound_databases` not empty (note above); `corpus.preview` `null` (the headline and counts say "The engine gave no preview numbers"; Accept stays available only if `state` is `STAGED`). None of these blocks the accept.
- **Offline**: the engine is local; offline means unreachable. The last read stays with "As of {time}"; Accept is disabled with "needs the engine on this computer"; nothing is queued. If the connection fails during the accept, the page does not assume either result: it re-reads on "Try again" and shows what the engine says.
- **Protocol-changed**: `protocol_fingerprint` is printed; the real check is the engine's at the accept (`PROTOCOL_CHANGED_SINCE_RUN`, above), because the accept binds the run's records to the current protocol fingerprint (M3d-engine decision 13). The page does not compare fingerprints itself; since review F3 (H-protocol-signals) it shows the engine's flags before the click: `search_changed` true shows the `PROTOCOL_CHANGED_SINCE_RUN` card above the gate and disables "Accept this corpus"; `protocol_changed` true with `search_changed` false shows a line in the gate panel: "The protocol changed after this search, outside the search itself (the criteria or the title). The records still answer the protocol's search; accepting binds them to the protocol as it is now." (the accept stays enabled). After an accept, a later protocol edit is not this screen's concern (screening reads the snapshot).
- **Stale run**: the corpus run is never stale by definition (a later run's records are the corpus). If `?run=` names an older run, the shared stale marker applies and the screen says the hand-off is about `run`.

## Desktop layout
Source: `Handoff` (D8), reduced as listed. Split like the canvas: main (provider mix, What screening will receive, the options area removed) and side (card **From**, the gate panel). The gate panel uses the GatePanel pattern: `surface` with a dashed `brand` border, label "Gate · accept the corpus", the single brand button; the browser shows nothing but the engine's numbers inside it. After the accept the gate panel is replaced by the Accepted corpus card and the brand button "Go to screening". Provider bar: segments with the provider names printed as text (not colour only); a segment under 1 % is listed in the row below the bar. Components: existing card, table, badge, StateCard; the bar is a flex row of `div`s with `role="img"` and an `aria-label` made from the engine's numbers.

## Mobile layout (≤ 640 px)
Discovery is desktop-only on the engine (plan §4: write, gate and job screens are desktop only); there is no phone board, and the accept is a gate, so it is never offered on a phone. A narrow desktop window gets one column: eyebrow, h1, lede, the provider mix as a list (no bar overflow; bar full width above), the table as stacked rows, the From card, the gate panel with "Accept this corpus" full width at 44 px, then "Search again" and "Read the report" as 44 px secondary links. A real phone (refused first read, `TOKEN_SCOPE_REFUSED`) shows `discovery.common.phone.desktopOnly` ("Discovery runs on your desktop. Open this page there.") with a 44 px link "Go to screening".

## Keyboard
Focus order: skip link, shell, step bar, run selector, h1, provider list, table (not focusable), From card, "Read the report", "Search again", then the gate panel's "Accept this corpus" last in the page so a keyboard user reaches it after the evidence. No single-key shortcut accepts the corpus. After an accept, focus moves to the h1 "This corpus is accepted." and the result is announced (`aria-live="polite"`); after a refusal, focus moves to the card heading.

## Copy
Keys in the discovery copy file named in 01-plan.md (en master; fr and ar by the implementer). No literal `aria-label`, `title`, `alt` or `placeholder` (N9).
- `discovery.handoff.eyebrow` "Step 7 of 7 · Hand-off to screening · gate"; `title` "Accept these {n} works as the corpus you will screen?"; `titleNoCount` "Accept this corpus for screening?"; `lede` "Accepting freezes a corpus snapshot with its own fingerprint. Screening reads only that snapshot, so later runs cannot change what you screen."
- `discovery.handoff.mix.title` "Provider mix"; `mix.note` "A work found in two databases is counted in both, so shares can add up to more than 100 %."; `mix.none` "No harvest records."
- `discovery.handoff.receive.title` "What screening will receive"; `receive.identified` "Records identified"; `receive.duplicates` "Duplicates removed"; `receive.works` "Works"; `receive.withAbstract` "With an abstract"; `receive.titleOnly` "Title only"; `receive.hard` "Hard to screen"; `receive.window` "Published outside the year window"; `receive.lowerBound` "Lower-bound databases"; `receive.lowerBoundNote` "{names}: a count stopped at its cap is a lower bound. The report says so."; `receive.noPreview` "The engine gave no preview numbers."
- `discovery.handoff.from.title` "From"; `from.run` "Search run {run}"; `from.protocol` "Protocol fingerprint"; `from.sources` "Staged exports"
- `discovery.handoff.gate.label` "Gate · accept the corpus"; `gate.body` "Nothing is handed to screening until you accept. The accept is recorded with the time and the snapshot fingerprint."; `gate.accept` "Accept this corpus"; `gate.accepting` "Accepting the corpus"
- `discovery.handoff.again` "Search again"; `report` "Read the report"; `import` "Stage an export"; `staged.refused` shows the engine's `staging_refused.message` verbatim
- `discovery.handoff.accepted.title` "This corpus is accepted."; `accepted.card` "Accepted corpus"; `accepted.id` "Snapshot"; `accepted.at` "Accepted {date}"; `accepted.counts` "{records} records · {studies} studies · {duplicates} duplicates"; `accepted.go` "Go to screening"
- `discovery.handoff.empty.title` "There is nothing to hand off yet."
- Shared: `discovery.common.stale`, `discovery.common.asOf`, `discovery.common.offline`, `discovery.common.phone.desktopOnly` (01-plan.md). Refusals: `discovery.states.<CODE>.*` (07).

## Accessibility
- Contrast pairs from tokens: `ink` on `surface`; the gate label is `brand` on `surface`; the unclear note and the "Hard to screen" badge carry words; status never rests on colour alone.
- The provider bar is an image with a text alternative built from the engine's providers and shares, and the same numbers are in the list beneath it; the table has real headers.
- The gate panel is a labelled `section`; the brand button has no icon-only form; the disabled state names its reason (`aria-describedby`). The result of the accept is announced with `aria-live="polite"`; refusals use `role="alert"`.
- RTL (ar): layout and bar mirror; artifact id, run id, fingerprint, dates and counts are `dir="ltr"`, Latin digits. Targets 44 px; light and dark tokens.

## Acceptance tests
Vitest `apps/research-ui/tests/discovery-handoff.test.tsx`: the headline and table print `preview` and `abstracts` as written and the page computes none; the mix bar uses `share` as written and the note about more than 100 % shows; `near_twins_undecided` is not rendered; no hydration checkbox and no blinding checkbox exist; the Accept button posts `POST /screening/corpus/accept` once, disables itself while pending, and the Accepted state shows only from the engine's `accepted`; `CORPUS_ALREADY_ACCEPTED` re-reads and shows Accepted; `NOTHING_STAGED` shows Empty; `PROTOCOL_CHANGED_SINCE_RUN` shows the message with a link to Harvest and no second accept; `PROTOCOL_INVALID` and an unknown 409 code render their code under Details; an accepted corpus offers "Go to screening" and no Run again, Stage or Prepare control; `lower_bound_databases` shows the note and does not disable Accept; `staging_refused` is printed verbatim; offline disables Accept with the reason; `TOKEN_SCOPE_REFUSED` shows the desktop pointer; `discovery-handoff.i18n`; `discovery.live-only`.
Playwright `discovery.spec.ts` (this screen's part, stateful fake of the discovery and corpus API): staged harvest, accept, land on Home; a protocol edit between the harvest and the accept gives the refusal; a second tab accepting first gives `CORPUS_ALREADY_ACCEPTED`; empty workspace; RTL (ar); axe light and dark; no overflow at 375 and 1440 px.

## Questions closed by the researcher (2026-11-10: each recommended answer taken, "all recommended")
1. **"Hide the database of origin while screening".** The board offers this option, but no screening setting does it: the existing blinding setting hides the agent's draft until you decide, not which database a record came from. The screen cuts the option and says nothing about blinding. Do you want the origin hidden while screening (a new setting, built in screening, not here)? Recommended: no, not for the first release; the board gives the reason (disclosed priors changed decisions in the UAV review), so decide after your own corpus, and add it as a screening setting with its own spec.
2. **"Fill missing abstracts".** The harness fills missing abstracts from OpenAlex as part of every search run, and no route tells this screen whether it ran for the corpus. The screen shows only how many records have an abstract. Do you want a visible "abstracts filled" line later? Recommended: no for now; add a field to the hand-off answer only if testers ask.
3. **Failed databases at the accept.** When a database failed in the corpus run, the corpus is accepted as partial, and the hand-off answer lists only databases stopped at a cap, not failed ones. The screen sends you to the report for them. Do you want the failed databases named on this screen too (it needs one more field in the hand-off answer)? Recommended: yes, as a small engine follow-up, because the accept is the point where partial coverage becomes permanent; until then the link to the report stands.

## As built (M3c)
Built in `apps/research-ui/components/discovery-handoff.tsx`. **Route gap found while building:** for a harvest, `corpus.preview` counts staged exports only and is zero, and no field of `GET /discovery/handoff` gives the number of works a harvest hands to screening. The headline is therefore "Accept this corpus for screening?" without a number, and the browser adds nothing up (Deferred in `docs/roadmap/milestones/M3c-screens.md`). After `PROTOCOL_CHANGED_SINCE_RUN` the Accept button stays disabled until a reload. Failed databases are reached through the report link (answer 10).
Review follow-up (M3c): `POST /screening/corpus/accept` does not check a running discovery job, so the screen reads `GET /discovery/runs` `active_job` and disables Accept while a harvest runs, with a sentence that says why. An engine guard (`DISCOVERY_JOB_ACTIVE` on the accept) is a follow-up (Deferred).


## An unfinished preparation (M3i)

**What was wrong.** After a harvest whose later steps (duplicates, abstracts, checks) did not end, this screen read "There is nothing to hand off yet", although the search had found records. And when an earlier run's works were still on disk, it showed them under the newer run's name and the accept froze them as that run's.

**Data in (added).** `preparation` on `GET /discovery/handoff` (the corpus run's; `null` without a run), as on the runs (`03-harvest.md`). While it is not `ready` and nothing is staged or accepted, the engine sends `corpus.from_discovery: false`, an empty `provider_mix` and zero abstracts: none of an earlier run's rows are counted.

**State (added): Not ready.** Shown when the corpus is not accepted, no export is staged, and `preparation.state` is `running`, `failed`, `stopped` or `interrupted`. It comes before "Empty".
- h1 "The corpus is not ready to hand off yet."
- One sentence, by state (`role="status"`): running, "The works of {run} are being prepared (step “{stage}”). The hand-off opens when this ends."; failed, "The search of {run} finished, but preparing its corpus failed at the step “{stage}”."; stopped, "You stopped the harvest of {run} before the step “{stage}”."; interrupted, "The search of {run} finished, but its corpus was not prepared. The console may have been closed while it ran."
- For the three states that are not running: "The records found are saved; nothing has to be searched again."
- The screen's one brand link, to Harvest with `?run=`: "Finish preparing this corpus on Harvest" ("Follow the harvest" while running; "Open Harvest" when the run cannot be finished). The action itself is on Harvest (the M10b spec's destination).
- "Check again" re-reads the hand-off. No accept button, no provider mix, no counts.

**Empty (changed).** "There is nothing to hand off yet." is now shown only when there is no published run and nothing staged.

**The accept (changed).** `POST /screening/corpus/accept` answers `409 PREPARATION_UNFINISHED` (with the run, state and stage) while the corpus run's preparation is unfinished and nothing is staged; the card reads "The corpus is not prepared yet" with "Open Harvest". The screens do not offer the accept in that state (the Hand-off shows "Not ready"; the Import step's accept is disabled without staged exports, and with staged exports it accepts the exports), so the card is the engine's guard: it appears only if the state changed after the page was read, or for another client of the route. M10b replaces the Import accept with a link here.

**Copy.** `handoff.pending.*` in en, fr and ar (`lib/discovery-copy.ts`); the card of `PREPARATION_UNFINISHED` in `lib/screening-states.ts`.

**Acceptance tests.** Vitest `apps/research-ui/tests/discovery-preparation.test.tsx` (failed, interrupted, running then stopped, ready after finishing, staged exports beside an unfinished harvest, fr and ar). Playwright `tests-browser/discovery.spec.ts`, tests named "M3i". Engine: `tests/console/test_harvest_preparation_api.py`.
## The next-step bar (M10b)
Status of this section: FINAL, built in M10b Part C (item C1; `docs/ux/shared/final/04-next-step.md`).

The shell draws the next-step bar above this screen. The screen's own states, copy and accept are unchanged; the bar adds one engine-written line:
- **Not ready** (M3i): the bar says the same engine state as the page (`CORPUS_PENDING`, waiting variants B to D, G(b), I and J of `04-next-step` table 2) and shows its own button to Harvest ("Follow the search" while running, "Finish preparing this corpus" when `can_finish`, else "Search again"). The page keeps its brand link to Harvest; both go to the same screen. Both read `preparation` through the same engine function, so they cannot disagree.
- **Empty** (no published run, nothing staged): the bar says why there is nothing to hand off: `READY_TO_SEARCH` ("Your protocol is ready. Run the search."), or `SEARCH_UNFINISHED` with the search still running (A), stopped (G(a)) or failed with no database answering (H). The page's sentence "There is nothing to hand off yet." and its two actions stay.
- **Default** (`CORPUS_READY`) and **Staged exports** (`STAGED_EXPORTS`): the Hand-off is the gate, so the bar is in its naming form ("Next: Review and accept the corpus. The button is on this page."), with no link.
- **Accepted**: the bar names the next screening step (`NOT_PREPARED` and later rows).

Tests: `apps/research-ui/tests/next-step-bar.test.tsx` and `tests-browser/next-step.spec.ts` (`04-next-step` "Acceptance tests"); this screen's own tests are unchanged.

## Addendum M3f-combined-corpus (2026-11-20)    Status: FINAL (M3f-combined-corpus)
Where this addendum contradicts the text above (the cut "Imports 0%" line in "Changed from the canvas", the Default and Staged-exports states, the "As built (M3c)" headline note, and the M3i accept paragraph), the addendum wins. Source: `docs/roadmap/milestones/M3f-combined-corpus.md` "Design" §1 to §4; finding 27.

**What changes.** Until the accept, a corpus has two parts: the harvest (the newest published run, included only when its preparation is `ready`) and the staged exports. This screen shows the corpus as the accept would build it, with both parts counted together. The gate, its text and the one brand button are unchanged.

**Data in (added).** All from `GET /api/v1/discovery/handoff` ✓ M3f-combined-corpus (`src/scholar_harness/console/api/discovery.py:800`):
| Field | Use |
| :-- | :-- |
| `corpus.harvest {run, state, included} \| null`, `corpus.origin` (now also `"combined"`) | the not-prepared note; the From card |
| `corpus.preview {identified, duplicates, unique_studies}` | for a combined corpus it counts both parts (identified = records the harvest fetched + every imported record); the headline and table print it as written. For a harvest-only corpus `preview` is as in "As built (M3c)" (no number in the headline) |
| `provider_mix[] {provider, kind: "search" \| "import", records, share}` | one row per database searched and one per export label; `records` = works that source found (a work found in two places counts in both) |
| `abstracts {with_abstract, title_only, share_with_abstract}` | now counts works for every corpus (a work has an abstract if any of its records has one); this fixes finding 27, where exports showed 0 of 0 |
| `imports_unchecked` (int) | records from exports in the corpus; 0 when none |

**Provider mix (amended).** The line "no separate imports row" is withdrawn: the mix now includes one row per export. Each row shows the name, then `kind` in words (`handoff.mix.kind.search` "searched by the app" or `handoff.mix.kind.import` "your export"), then `handoff.mix.row` ("{records} records · {share}"). The kind is text beside the name, never a colour or a segment style alone; the bar segments keep their printed names and the `role="img"` label adds the kind. The caption `handoff.mix.note` (shares can add up to more than 100 %) stays unchanged. `handoff.mix.none` ("No harvest records.") shows only when the mix has no row at all.

**With an abstract / Title only (amended).** The two lines count works for every corpus, exports included. Their labels do not change.

**Unchecked imports line.** When `imports_unchecked` > 0, one neutral line (ink-muted, no role colour, not a warning card) under the "What screening will receive" table: `handoff.imports.unchecked`. It blocks nothing and is not a hint (V2: a "not checked" the researcher must read).

**Harvest not prepared, exports staged (new note).** When `corpus.harvest` is not null, `included` is false and exports are staged, a note in the `unclear` role above the gate: `handoff.harvestOut.note` with `{state}` as the word from `combined.state.<state>` (an unknown state is printed verbatim), and a link `handoff.harvestOut.open` to `/discovery/harvest?run={run}`. It is a consequence read before the gate (V6), so it is not behind a hint. "Accept this corpus" stays enabled (accepting freezes the exports alone; M3i item 10 kept). With no exports staged the state is "Not ready" as in M3i; with a harvest `running` the accept stays disabled by the existing active-job rule.

**From card.** For a combined corpus it shows `from.run` ("Search run {run}") and the staged export labels (`from.sources`), both with existing keys.

**Copy** (`lib/discovery-copy.ts`; `combined.state.*` are the keys of the Import addendum, shared):
| Key | en | fr | ar |
| :-- | :-- | :-- | :-- |
| `handoff.mix.kind.search` | searched by the app | recherché par l'application | بحث أجراه التطبيق |
| `handoff.mix.kind.import` | your export | votre export | صادرك |
| `handoff.imports.unchecked` | {n} records come from your exports. They were not checked against Crossref or OpenAlex, and missing abstracts were not filled in. | {n} notices proviennent de vos exports. Elles n'ont pas été vérifiées auprès de Crossref ou d'OpenAlex, et les résumés manquants n'ont pas été complétés. | {n} سجلًا من صادراتك. لم يُتحقق منها لدى Crossref أو OpenAlex، ولم تُستكمل الملخصات الناقصة. |
| `handoff.harvestOut.note` | The harvest {run} is not prepared ({state}). If you accept now, the corpus holds your exports only and the harvest's records are left out for good. Finish preparing it first to include them. | La collecte {run} n'est pas préparée ({state}). Si vous acceptez maintenant, le corpus ne contiendra que vos exports et les notices de la collecte seront définitivement laissées de côté. Terminez d'abord sa préparation pour les inclure. | الحصاد {run} غير مُحضَّر ({state}). إن قبلت الآن فستضم المجموعة صادراتك فقط، وتُترك سجلات الحصاد خارجها نهائيًا. أكمل تحضيره أولًا لتضمينها. |
| `handoff.harvestOut.open` | Open Harvest | Ouvrir la collecte | افتح الحصاد |

**States.**
- **Default** (`STAGED`, combined): headline "Accept these {n} works ..." now carries the number from `preview.unique_studies` (the engine counts both parts); mix with search and export rows; table; unchecked line when `imports_unchecked` > 0; the From card; the gate.
- **Empty**, **Loading**, **Error**, **Offline**, **Protocol-changed**, **Stale run**: as above. `PROTOCOL_CHANGED_SINCE_RUN` still refuses the accept when the harvest's search changed (a stale run is never the harvest part); `PREPARATION_UNFINISHED` still refuses without exports (the "Not ready" state is shown instead, as in M3i).
- **Partial**: adds the not-prepared note above; `lower_bound_databases` note, `title_only` count and `preview: null` are as above and none blocks the accept.
- **Accepted**: the Accepted card as above; for a combined corpus the From card still lists the run and the export labels, and the mix rows are those of the frozen corpus.
- **Staged exports only** (`harvest` null): the mix lists the export rows (it is no longer empty), the same layout; "Search again" is shown (a harvest can now follow exports) instead of the old `staging_refused` sentence.
- **Protocol-changed / offline**: unchanged.

**Accessibility.** The note is a `section` with `role="status"` and words (state in text, not colour alone); the unchecked line is a plain paragraph; the mix `role="img"` label includes each kind in words; `{run}` is in `bdi` and `dir="ltr"` in ar; the "Open Harvest" link is a 44 px target after the note and before the gate in focus order.

**Backend calls.** `GET /api/v1/discovery/handoff` ✓ (`discovery.py:800`, M3f-combined-corpus fields); `POST /api/v1/screening/corpus/accept` ✓ (`screening_v1.py:696`: ready harvest plus exports builds the combined snapshot, unfinished harvest plus exports accepts the exports alone, refusals unchanged). Nothing is ✗.

**Tests.** `apps/research-ui/tests/discovery-handoff.test.tsx`: the mix prints one row per `provider_mix` entry with `kind` in words ("searched by the app", "your export") and the shares as written; the caption about more than 100 % stays; the "no separate imports row" assertion is removed; with an import row and `abstracts` counting works, "With an abstract" and "Title only" print those numbers (no 0 of 0); `imports_unchecked: 618` shows the unchecked line and `imports_unchecked: 0` shows none; the unchecked line does not disable Accept and has no `[data-hint-body]` ancestor; `harvest {state: "failed", included: false}` with staged exports shows the not-prepared note with the word "preparation failed", a link to Harvest with `?run=`, and Accept enabled; `harvest {included: true}` shows no note; an unknown `state` prints verbatim; the headline prints `preview.unique_studies` for a combined corpus. `apps/research-ui/tests/discovery-preparation.test.tsx`: "staged exports beside an unfinished harvest" shows the note. `apps/research-ui/tests/discovery-copy.test.ts` (keys in en, fr, ar; N9 guard); `apps/research-ui/tests/guidance.audit.test.tsx`: D-HO17, D-HO18, D-HO19 STAYS. Playwright `tests-browser/discovery.spec.ts`: ready harvest plus two exports, read the mix and accept; unfinished harvest plus export, read the note, accept, see the exports-only corpus; RTL (ar); axe in light and dark.

**Open questions:** none.
