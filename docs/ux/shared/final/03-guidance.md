# 03 Guidance (shared rules)    Status: FINAL, built (M10d-lighter-screens, 2026-11-19; questions closed by the researcher 2026-11-15; Criteria, Harvest, Report and Chase not folded yet, question 3) | Shared (Phase 0 Inception and Phase 1 Discovery; later screens adopt it) | Applies to inception 01 to 07 and discovery 01 to 09 | Milestone M10b (this spec) + M10d (lighter screens, the build)

Boards: none. The rules restate and extend decisions already taken: BRAND_BOOK principles 3 ("plain words first, raw value underneath"), 4 ("the human is the gate") and 6 ("quiet by default"), the step-header pattern and "one brand button per screen"; the details-disclosure rule (`docs/ux/phase2-screening/final/12-details-disclosure.md`, decided 2026-11-07); and the researcher's request of 2026-11-14 ("tips and hints should be hidden in icons and pop up; controls and steps should be easy and have recommendations"). Contract: none; this spec changes no behaviour and adds no backend call.

**Purpose.** Each screen shows what the researcher must read and act on; explanation, examples and "why" sit one tap away, and the one recommended choice is marked but never chosen for the researcher.

**Changed from the canvas.**
- The per-screen specs show help text inline under the field (`aria-describedby` paragraphs such as `inception-scope.tsx:74,106,128`, `inception-shape.tsx:184,199,217`, `discovery-harvest.tsx:301,317`, `discovery-chase.tsx:308,327,346`). This spec overrides **where** that text is shown, not **what** it says. A text that moves behind a hint keeps its copy key, so no translation changes and the specs' Copy sections stay the source of every string.
- Spec 12 rule 4 fixes the summary "Details" for proof disclosures. This spec adds one more disclosure use, a collapsed secondary card (rule 4 below), which keeps the card's own title as its summary, as "Run from the terminal" does in 12.
- The per-screen audit (section "Audit") is a snapshot of the copy catalogs on this branch (`apps/research-ui/lib/inception-copy.ts`, `apps/research-ui/lib/discovery-copy.ts`). The snapshot was taken at `a0191cc6` and recounted on 2026-11-18, after M10a and M3i merged, for every screen whose keys changed since: Explore, Harvest, Plan, Hand-off and Chase (see "Counts per decision"). The test `guidance.audit.test.tsx` below fails on any key it does not know, so a later copy change cannot slip past the audit.

## Entry / exit
- Entry: applies to every screen listed above when M10d builds it; no route of its own. Later phases (Screening, Synthesis) adopt it by adding rows to the audit.
- Exit: none. Gate: none. The rules never add a gate and never remove the one a screen has (BRAND_BOOK principle 4: one gate per screen at most).

## Data in
| Field | Source |
| :-- | :-- |
| every string | the existing catalogs `lib/inception-copy.ts`, `lib/discovery-copy.ts`, `lib/screening-states.ts` (no new text for moved blocks) |
| `recommended_paradigm`, `default_concepts[]` (marks the Shape lens and its playbook, suggests concepts) | `POST /api/v1/inception/steps/scope` ✓ M4a (`console/api/inception.py:106`, `steps.py:165`) |
| pool health gates (`gates.pool.sufficient`) that mark "semantic search" when a pool is thin | recon routes ✓ M4c (02-explore, "Backend calls") |
| a suggested harvest cap | `size estimate` ✗ M10b (`01-plan` "Size estimate (M10b)"); until it exists no cap is marked |
| open checks that mark the next fix on Review | `checks` ✗ M10b (02-checks); until it exists Review marks nothing |
| the next step of a review | the "what's next" bar ✗ M10b (04-next-step) |

## Data out
Nothing. The rules write no draft field, no journal event and no workspace file. A hint opening, a disclosure opening and a recommended mark leave no record.

## Backend calls
| Call | Status |
| :-- | :-- |
| none of its own | ✓ nothing new, ✗ nothing |

The rows above that read an existing route are ✓ (cited); the three that read a route another spec adds are ✗ M10b and are only consumed here, never defined here.

## The rules

### Rule 1: Hint (explanatory text behind an information button)
**What may be hidden** (a hint holds only these kinds, and only text the researcher can act without):
- T1 how-to ("One item per line", "Tick one to add it as a synonym");
- T2 an example ("for example en, fr", "a model, a team, a crop field");
- T3 a definition ("a paper anchors a direction only when ...", "what a miss means");
- T4 methodology background (why a rule exists, what a number is);
- T5 the "why" of a recommended option (rule 3).

**What may never be hidden** (a hint never holds these; they stay in the page, in their role colour and their card):
- V1 a refusal: its plain sentence, what it affects, its next step (the typed code goes in Details, spec 12 rule 7);
- V2 a warning, a limit or a "not known" (a lower bound, a partial run, a missing key, an out-of-date pool, "not in production");
- V3 a check result (found / not found, accepted / waiting, "failed" next to a database, a count of noted lines);
- V4 a number and its denominator, in the sentence that states it;
- V5 provenance and source labels, and every draft label ("Template draft · not yet yours", "Translated by the engine · not yet sent", "Heuristic reading · not yet yours", fingerprints, run ids);
- V6 anything the researcher must read **before a decision is recorded or something is written**: gate text, the consequence of a destructive confirmation, what leaves the machine, what a "Create", "Accept" or "Send" will do;
- V7 field labels, option names and button names (a label is never only an icon);
- V8 the status of the step (saved, loading, offline, as-of).

A hint may repeat a number or a label that is also visible elsewhere; it is never the only place that states one (rule "quote, never host"). A hint holds **plain text from one copy key, no markup, no link, no control**: the component takes a key, not children, so a card, a StateCard or a button cannot be placed inside one.

**Behaviour.**
1. **Trigger.** A real `<button type="button">` with a 16 px, 1.5 px stroke "i in a circle" glyph in `currentColor` (BRAND_BOOK Iconography), placed as a sibling immediately after the label or heading it explains, never inside a `<label>` (so a tap cannot toggle its field). Hit area at least 44 x 44 px (a padded hit area, the glyph stays 16 px). `aria-expanded` true/false, `aria-controls` the panel id, accessible name from `guidance.hint.open` = "About {label}" (the label's own text, so a screen reader hears which field). Not hover-driven: the same control works by mouse click, touch tap, and keyboard.
2. **Panel.** A non-modal popover: `surface` fill, `hairline` border, `radius-md`, `shadow-overlay` (the token is reserved for "dialogs and popovers", `tokens.json`), `ink` text at `body`/`caption` size, `max-width` 24 rem (about 55 characters, near the 65-character running-text rule), and a body of at most 3 sentences and 300 characters. No backdrop, no focus trap, the page stays operable. The panel is rendered in the DOM next to its button (never removed), hidden when closed; the field's `aria-describedby` points at the panel id, so a screen-reader user hears the help without opening it (parity with spec 12 rule 5: nothing leaves the DOM).
3. **Open and close.** Click, tap, `Enter` or `Space` on the button toggles it. `Escape` closes it from the button or the panel. Click or tap outside closes it. Moving focus out of the button/panel pair (Tab away) closes it, so a hint never covers the next control the researcher is about to reach. Opening a hint closes any other open hint. Nothing auto-opens, nothing is remembered, there is no "don't show again".
4. **Focus.** Opening does not move focus; the panel has no focusable content. Closing by `Escape`, by the button, or by a click on the button leaves focus on the button. If focus is ever inside the panel (a screen-reader virtual cursor, a programmatic focus), `Escape` returns it to the button. Closing by outside click does not steal focus.
5. **Placement in the logical direction.** First choice: beside the button on the inline-end side; second: below it; third: inline-start. Placement is computed with logical sides, so in right-to-left (ar) the first choice is the physical left side. The panel is never clipped by a card's `overflow` (top layer or portal) and never wider than `100vw - 2 x space-4`.
6. **Repeated explanation in a list gets one hint, on the list's heading**, never one per row (the wizard-criterion edit hint, "what a miss means", the completeness note). A row keeps only what is specific to it.
7. **One hint per label or heading**, and at most 6 hint buttons visible per screen (the density budget, rule 5).

**Component.** One new component `Hint` in `apps/research-ui/components/ui/base.tsx`, `<Hint labelKey="..." textKey="..." />`, beside the existing `Button`, `DecisionBadge`, `GatePanel`, `EvidenceQuote` and `DataCell`. Today no tooltip, popover or hint component exists: the screens use hand-written `<details>` (for example `discovery-harvest.tsx:80`, `discovery-plan.tsx:141`, `inception-direction.tsx:322`), `aria-expanded` quiet buttons (`inception-explore.tsx:562,642`) and `aria-describedby` paragraphs. Spec 12 names a `Details` wrapper in `base.tsx`; on this branch `base.tsx` exports only the five components above, so M10d adds `Details` and `Hint` together. Implementation may use the native Popover API (light-dismiss and `Escape` are built in) or a controlled component; the behaviour above is the contract, not the mechanism.

### Rule 2: One sentence of lede per screen, one main action per step
- The step header is the BRAND_BOOK pattern: `label` eyebrow, the `display` question, then **one** `body` line in `ink-muted`. The lede is **one sentence** (at most about 130 characters, two lines at 65 characters). A second lede sentence is either a hint (T1 to T4), a duplicate of a label or badge on the same screen (removed), or a warning (which then is its own card, not lede).
- **One brand button per screen** and per state (BRAND_BOOK: "a screen with two brand buttons has one too many"). Everything else is `secondary` or `quiet`. Where a screen has a "before" and an "after" button, only one is brand at a time (Direction: "Pursue {direction}" before the bind, "Continue to Shape" after; the same holds for Recall "Check these seeds" then "Continue to Harvest", and Report "I reviewed this text" while the text is unreviewed, then "Continue to hand-off").
- The button names its effect (BRAND_BOOK voice). A disabled main action keeps its reason as visible text beside it (`scope.needTopic`, `shape.needLens`, `direction.reason.*`, `harvest`/`chase.startDisabled.*`): that is V6/V2, not a hint.
- The next step is stated **once**: by the main action. The "what's next" bar (04-next-step, ✗ M10b) will own "which step is next"; until it ships, `overview.continue`, `done.lede` sentence 2 and the per-screen "Continue ..." stay as they are, and they are the blocks the bar replaces.

### Rule 3: Recommended
- **Mark.** A word badge "Recommended" (`guidance.recommended`) on the option's title line, `radius-sm`, `ink` text on `surface-raised`, a 1 px **dashed** `ink-muted` border (the existing "machine draft" outline of 01-scope "Shared", item 5), followed by a Hint button. It is not `brand` (brand is spent on the one primary action, BRAND_BOOK), not `include` (green reads as "accepted"), not `unclear` (that role means "needs a person"). Never colour alone: the word is the mark.
- **The source is visible, the why is behind the hint.** The badge reads "Recommended · {source}" (`guidance.recommended.by`), where `{source}` is short: "word scan of your topic" (Shape), "check {id}" (M10b checks), "imported protocol" (09-start-from-protocol), later "{model}" (M10c). The hint holds the one-sentence why and no live value that is not also visible. The source is provenance (V5) so it is never hidden.
- **Never pre-selected.** Nothing is checked, ticked, filled, focused or scrolled to because it is recommended; the options keep the engine's order (an engine order is evidence, not a recommendation, as `direction.lede` already says); the main action stays disabled until the researcher chooses. A recommendation is a draft until the researcher acts (BRAND_BOOK principle 5; 03-direction, "Nothing is preselected"). Existing field defaults (an empty "From year", `["en"]` for languages) are not recommendations and carry no mark.
- **Where it applies** (and where not):
  | Screen | Marked | Not marked |
  | :-- | :-- | :-- |
  | 04 Shape | the lens the word scan leans to (`shape.leaning`), the playbook that matches it (`shape.recommended`, today "Matches the lens", becomes the mark) | the template RQ draft (it keeps its own draft label "Template draft · not yet yours") |
  | 02 Explore | "Search again with semantic search" (`explore.thin.semantic`) when the pool is thin | the keyword/semantic radios when the pool is healthy |
  | 03 Direction | nothing: the engine lists directions by evidence and states it is not a recommendation | any of the three directions; the seeds (the anchors are labelled "Anchors", nothing is ticked) |
  | 05 Criteria | the suggested concepts and pool synonyms keep their "not yet yours" label; the badge is added only when an M10b check proposes one | any wizard criterion (it keeps "Waiting for you") |
  | 06 Review | the first open check's fix, when 02-checks exists | the Create button |
  | 03 Harvest | the suggested cap, when the size estimate (`01-plan` "Size estimate (M10b)") exists | the cap input is never pre-filled with it |
- **Step-level recommendation** is the what's-next bar, not a badge on a button.
- **As built (accepted 2026-11-19, decision M10d item 10).** No mark on the screens carries a hint of its own: Shape's why is the lens legend's hint (a button may not sit in a radio's label), Explore's is the Search mode hint just above it, and Review's first fix and the size estimate's cap keep the row's own "Why" disclosure.

### Rule 4: Collapsed details
Reuse the details-disclosure pattern of spec 12 (native `<details>`/`<summary>`, closed by default, content stays in the DOM, 44 px summary, `focus` ring, no nesting). Two uses:
1. **Proof and identifiers** (spec 12, label "Details", `screening.details.label`): fingerprints, run ids, file digests, typed codes, raw values. Unchanged.
2. **A secondary card** that would take the screen over the card budget (rule 5) becomes a collapsed section whose summary is the card's own title plus its count in the same line ("Papers · 25", "Databases asked · 4"); it is not labelled "Details". If the content holds a failing, blocked or unclear item, the summary line carries that as a role badge with a word ("1 failed"), so the failure is never one click away (spec 12 rule 8). Only the table or list is collapsed, never a warning.
A hint is for a sentence; a disclosure is for a block (a table, a list, a form). A hint never contains a disclosure and a disclosure never contains more than one hint per label.

### Rule 5: Density budget
Numbers are tuned to the BRAND_BOOK layout: a step header (eyebrow, display, one body line), then regions of "evidence on the left two thirds, decision on the right third", sections separated by `space-5`, one gate and one brand button, running text near 65 characters.

Before any interaction (hints closed, disclosures closed) a screen shows at most:
| Budget | Limit | Defence from the brand book |
| :-- | :-- | :-- |
| B1 lede | 1 sentence, at most 130 characters | "one `body` line in `ink-muted`" (Layout patterns, Step header) |
| B2 cards | 4 cards; a group of option cards (a radiogroup) counts as one card | two regions, each with at most two cards: evidence beside the decision |
| B3 explanatory blocks | 0 outside the lede and card captions; at most 1 caption per card, one sentence | principle 6 "quiet by default"; principle 3 keeps the raw value one disclosure away |
| B4 hint buttons | 6 per screen | one per field or heading of a form of up to six fields; a screen needing more is over its field budget too |
| B5 brand buttons / gates | 1 / 1 | "A screen with two brand buttons has one too many"; "one gate per screen at most" |
| B6 inline help paragraphs under fields | 0 | help is a hint (rule 1) |

Not counted against the budget (and never to be removed to meet it): refusals, warnings, check results, numbers with their denominators, provenance and draft labels, gate text, field and button labels, and the tables that carry them. A screen over B2 folds secondary cards (rule 4, use 2); the fold plan below is indicative.

Accepted exceptions (the researcher, 2026-11-19, decisions 2026-11-19 M10d items 3 and 4; held by `density.budget.test.tsx`, a count may only go down): B4, Explore with a pool shows up to 9 hint buttons until its repeated search controls are folded behind "Search settings" (after the researcher has tried Explore with real data), and Plan shows 7, one per key line under Limits; B1, Shape's lede may have up to 170 characters.

| Screen | Cards today (from the copy, approximate; the implementer counts the rendered DOM) | Fold into collapsed sections |
| :-- | :-- | :-- |
| inception 02 Explore | first search, pool, three health tiles, schools, topics, metrics, papers, databases, your concepts (about 9) | topics and metrics, papers, databases (its summary carries "{n} failed") |
| inception 05 Criteria | concepts, inclusion, exclusion, extraction columns, verification (5) | extraction columns and verification into one section "After screening" (its summary names the ticked count) |
| inception 06 Review | about, protocol summary, direction and seeds, files and fingerprint, checks, gate (6) | files and fingerprint into Details (spec 12 use 1) |
| discovery 03 Harvest | what will be searched, one row per database, steps after the search, this harvest form, gate-like stop (5) | steps after the search |
| discovery 06 Report | identification, not searched, imports, duplicates, screening so far, methods text, run history (7) | not searched (when none: absent), run history |
| discovery 09 Chase | seeds, databases/options, per-database legs, counts, already in corpus, gate (6) | per-seed legs (already a `<details>`), already in corpus (already a `<details>`) |

## Audit
Each row is a text block shown today, by copy key (the key's sentences are split into separate rows when they get different decisions). Decision is **STAYS** (visible), **HINT** (moves behind a Hint button, keeping its key as the hint body), or **REMOVED** (duplicate of another block on the same screen or of the stepper, a badge or a control). Reason codes are the classes of rule 1: V1 to V8 (never hidden), T1 to T5 (may be hidden), X1 a duplicate of a title, label, badge or control on the same screen, X2 a duplicate of a stronger statement at the point of action, X3 a description of the layout. Keys are the en master; `.` groups mean "every key under it". The screens' own main action is named at the head of each group.

### Inception (phase 0)
Shared frame (`inception-frame.tsx`, every screen 01 to 07), then 01 Scope, 02 Explore, 03 Direction, 04 Shape, 05 Concepts and criteria, 06 Review and create, 07 Done. Screens 02 and 03 are specified but not built (M4d); their rows read the spec and the catalog.

| ID | Copy key | Text today | Decision | Reason |
| :-- | :-- | :-- | :-- | :-- |
| I-F1 | `eyebrow`, `draftId`, `saved`, `notSaved`, `stepsLabel`, `step.*` | "New review", "Draft {id}", "Draft saved {at}", the stepper | STAYS | V8 status and navigation |
| I-F2 | `nothingWritten` | "Nothing is written to a workspace before Review. The answers are saved as a draft ..." | HINT | T1/T4 how it works; the one write is stated at the gate (I-R19, V6). Hint beside the "Draft saved" status |
| I-F3 | `fieldsMissing`, `missing.goTo` | "The engine needs these answers first:" and the links | STAYS | V1 refusal (DRAFT_INCOMPLETE) names what blocks |
| I-F4 | `saving`, `loading`, `asking` | "Saving the draft...", "Reading the draft...", "Asking the engine..." | STAYS | V8 transient status |
| I-F5 | `backToWorkspaces`, `backToDrafts`, `saveAndExit`, `draftLabel`, `noDraft`, `list.sep`, `field.*`, `refusal.*` | "All workspaces", "Save draft and exit", the field names of I-F3, the refusal words | STAYS | V7/V1 navigation, labels and refusals (row added by M10d, 2026-11-19: keys the snapshot did not list) |
| I-S1 | `scope.kicker` | "Step 1 of 6 · Scope" | STAYS | V8 step header eyebrow |
| I-S2 | `scope.title` | "What is the review about?" | STAYS | the question the screen answers |
| I-S3 | `scope.lede` (sentence 1) | "The topic, years and languages set the review window." | STAYS | the one lede sentence (rule 2) |
| I-S4 | `scope.lede` (sentence 2) | "The engine reads the topic to suggest a lens on the next step." | REMOVED | X1 says the same as `scope.topicHelp`, which becomes a hint |
| I-S5 | `scope.topicHelp` | "One subject. The suggested lens and the draft question are built from these words." | HINT | T1 how-to |
| I-S6 | `scope.toYearHelp` | "Empty means up to today." | HINT | T3 definition; Review shows the result ("{from} to today", `review.yearsOpen`) |
| I-S7 | `scope.languagesHelp` | "Language codes separated by commas, for example en, fr." | HINT | T2 example |
| I-S8 | `scope.yearInvalid` | "Write a year as four digits, or leave it empty." | STAYS | V1 field error |
| I-S9 | `scope.needTopic` | "Write your topic first." | STAYS | V2 why the main action ("Continue to Explore") is disabled |
| I-S10 | `scope.topic`, `fromYear`, `toYear`, `languages`, `continue` | the field labels and "Continue to Explore" | STAYS | V7 (row added by M10d) |
| I-E1 | `explore.kicker` | "Step 2 of 6 · Explore · the first search" | STAYS | V8 eyebrow |
| I-E2 | `explore.title` | "What do the first papers say about your question?" | STAYS | the question |
| I-E3 | `explore.lede` (sentence 1) | "Pool health first, in plain words with the raw value underneath." | REMOVED | X3 describes the layout; the cards do it (principle 3) |
| I-E4 | `explore.lede` (sentence 2) | "The schools, topics and papers below are what the later steps draw on." | STAYS | the one lede sentence |
| I-E5 | `explore.first.title`, `first.question`, `first.years`, `first.toPresent`, `defaultYear` | "Your first search", the question, the years, "Your draft has no from-year, so the search starts at {year}." | STAYS | V4/V6 what is searched; a silent default is stated |
| I-E6 | `explore.first.body` | "This sends your question to the databases you ticked and keeps up to {max} papers." (M10a wording) | STAYS | V6 what leaves the machine before the main action |
| I-E7 | `explore.mode.legend`, `mode.keyword`, `mode.semantic` | "Search mode", "Keyword", "Semantic" | STAYS | V7 option names (marked Recommended only on a thin pool) |
| I-E8 | `explore.mode.help` | "Semantic search matches meaning, not only words." | HINT | T3 definition |
| I-E9 | `explore.pool.title`, `pool.meta`, `pool.cached`, `pool.fingerprint` | "Pool · {n} papers", "fetched {date} · {mode} ...", "from cache", "Pool {fingerprint}" | STAYS | V4/V5 numbers and provenance (fingerprint in Details per spec 12) |
| I-E10 | `explore.pool.refreshNote` | "A refresh runs the same search again and replaces this pool. An empty or failed search is never cached ..." | HINT | T1/T4; the consequence that matters (a bound direction goes out of date) is `explore.refreshWarn.*` (I-E33), which stays |
| I-E11 | `explore.pool.partial`, `partial.title`, `partial.body`, `partial.again` | "Partial pool", "Some databases did not answer", "This pool was not saved for reuse ..." | STAYS | V2 warning |
| I-E12 | `explore.pool.langNote` | "No database filters by language in this search; the languages are recorded with the pool." | STAYS | V2 a limit of the result, not an explanation |
| I-E13 | `explore.tile.size.title`, `size.ok`, `size.value`, `size.raw`, `size.thin`, `size.thinRaw` | "Pool size", "Enough papers", "{n} of up to {max}", "floor is {threshold}", "Only {n} papers came back" | STAYS | V3/V4 check result with its denominator |
| I-E14 | `explore.tile.size.thinBody` (sentence 1) | "Directions from fewer than {threshold} papers are often fragments." | STAYS | V2 warning |
| I-E15 | `explore.tile.size.thinBody` (sentence 2) | "Widening the years or using semantic search usually helps." | REMOVED | X1 duplicates the marked button `explore.thin.semantic` (rule 3) |
| I-E16 | `explore.tile.spread.title`, `coherent`, `fragmented`, `value`, `raw` | "Topical spread", "Focused subfields", "Top 3 topics cover {pct}% ..." | STAYS | V3/V4 |
| I-E17 | `explore.tile.spread.none`, `spread.noneBody` | "No topic data", "Topics come from OpenAlex records; this pool has none ..." | STAYS | V2 "not known" |
| I-E18 | `explore.tile.echo.title`, `echo.value` | "Your own words in the pool's terms", "{qei} of the ten most frequent terms" | STAYS | V4 number |
| I-E19 | `explore.tile.echo.body` | "Share of the ten most frequent pool terms that repeat words of your question ... not a pass or a fail." | HINT | T3/T4 definition |
| I-E20 | `explore.reading.badge` | "Heuristic reading · not yet yours" | STAYS | V5 draft label |
| I-E21 | `explore.reading.source` | "Counted from titles and abstracts by keyword rules." | STAYS | V5 provenance of the counts |
| I-E22 | `explore.schools.title`, `schools.count`, `schools.one` | "Schools of thought", "{n} papers", "1 paper" | STAYS | V4 |
| I-E23 | `explore.schools.oneNote` | "A school with one paper cannot become a direction on its own ..." | HINT | T3 definition |
| I-E24 | `explore.topics.title`, `topics.more`, `metrics.title` | "OpenAlex topics", "+ {n} more", "Metrics and datasets seen" | STAYS | V4 data (folded in a collapsed section, rule 4) |
| I-E25 | `explore.papers.title`, `papers.sorted`, `papers.col.*`, `papers.anchors*`, `papers.noDoi`, `papers.newTab`, `papers.link`, `papers.linkDoi`, `papers.more`, `papers.less` | the Papers table | STAYS | V4/V5 DOI and anchor counts (folded in a collapsed section) |
| I-E26 | `explore.papers.note` | "A paper anchors a direction only when the direction's term occurs in its title or abstract." | HINT | T3 definition; one hint body shared with I-D8, I-C7, I-E32 |
| I-E27 | `explore.legs.title`, `legs.latest`, `legs.none`, `legs.col.*`, `legs.ok`, `legs.failed`, `legs.fetchedOf`, `legs.atLeast`, `provider.*` | the "Databases asked" table | STAYS | V3 a failed database is a result (summary carries "{n} failed") |
| I-E28 | `explore.legs.refused.*`, `keys.openalex.unset`, `keys.s2.unset` | "OpenAlex refused the request; set SCHOLAR_OPENALEX_KEY", "Not set" | STAYS | V1/V2 refusal and missing key |
| I-E29 | `explore.legs.neverEmpty` | "A database that failed is not the same as a database that found nothing." | HINT | T4 background; the status word "failed" stays on the row |
| I-E30 | `explore.keys.openalex.emptyNote` | "OpenAlex is still asked without a key and may still answer; once it refuses, ..." | HINT | T4 background; the missing key itself is I-E28 |
| I-E31 | `explore.concepts.title`, `concepts.line`, `concepts.none`, `concepts.suggested`, `concepts.edit` | "Your concepts in this pool", "{concept}: in {anchored} of {total} ...", "Suggested ... not yet in your draft" | STAYS | V4/V5 |
| I-E32 | `explore.concepts.note` | "A concept counts a paper only when it, or one of its synonyms, occurs ... as whole words." | HINT | T3 definition; shares the anchor-definition body (I-E26) |
| I-E33 | `explore.changed.*`, `explore.refreshWarn.*`, `explore.stale.*` | "You changed your {parts} after this pool was searched ...", "Searching again will make your chosen direction out of date" | STAYS | V2/V6 warning before a recorded effect |
| I-E34 | `explore.progress.title`, `progress.leg`, `progress.lost` | "Searching", "{provider} · {fetched} fetched", "Lost contact with the engine ..." | STAYS | V8/V2 |
| I-E35 | `explore.progress.note` | "Results are kept only if the search succeeds." | HINT | T4 background; the partial and failed cards (I-E11) carry the outcome |
| I-E36 | `explore.first.go`, `explore.next*`, `explore.change`, `explore.offline`, `explore.asOf`, `explore.first.needTopic` | "Search the literature" / "See {n} directions", "needs the engine on this computer", "As of {time}" | STAYS | V7/V8; main action: "Search the literature" while no pool exists, "See {n} directions" after |
| I-E37 | `explore.query.label`, `query.useDerived`, `query.tooLong` | "Query sent to the databases", "Use the derived query", "The query can have at most 2000 characters." | STAYS | V7 field label and control; V1 the length refusal (M10a, recounted 2026-11-18) |
| I-E38 | `explore.query.help` | "The keywords below are sent to the databases. Your question above is not changed." | HINT | T3/T4 what the field is; the field label says the rest |
| I-E39 | `explore.query.emptyHint` | "Leave empty and the engine derives a keyword query from your question." | HINT | T1 how-to; shown only when the engine has no derived query |
| I-E40 | `explore.picker.legend`, `picker.check.*`, `picker.up.*`, `picker.down.*`, `picker.moved`, `picker.none`, `picker.reset`, `picker.unknown` | "Databases to ask", the per-database controls, "Pick at least one database." | STAYS | V7 controls and their names; V1 the "at least one" refusal |
| I-E41 | `explore.picker.orderHelp` | "The order decides which papers fill the sample of {max} first." | HINT | T3 what the order means |
| I-E42 | `explore.legs.col.query`, `legs.zero`, `legs.editQuery` | "Query sent", "0 results", "Edit the query" | STAYS | V3 "0 results" is a result; V5 the query each database received |
| I-E44 | `explore.pool.refresh`, `explore.thin.semantic` | "Refresh pool", "Search again with semantic search" | STAYS | V7; the second carries the Recommended mark on a thin pool (row added by M10d) |
| I-E45 | `sample.*` | the sample curation (M10b Part C): "Not relevant", "{n} papers · {k} left out", the warnings before a bound direction or a seed is affected, "Left out · {k}", the Undo toast | STAYS | V3/V4/V6/V7 (row added by M10d, 2026-11-19: the keys came after the snapshot). The table and its controls sit in the folded Papers section; the curation's refusal, the empty sample and the toast stay outside it. `sample.left.help` is a candidate for a hint in a later pass |
| I-E43 | `explore.legs.shorten` | "Six words joined by AND can find nothing; shorten the query above." | STAYS | V2 advice tied to an empty result; M10b shows it only when the engine says the empty result followed a query of several words joined by AND (it showed for any empty search) |
| I-D1 | `direction.kicker` | "Step 3 of 6 · Direction · pick one" | STAYS | V8 eyebrow |
| I-D2 | `direction.title` | "Which direction should this review pursue?" | STAYS | the question |
| I-D3 | `direction.lede` (sentence 1) | "These directions come from phrases that occur in the titles or abstracts of at least two papers of your pool." | STAYS | the one lede sentence; V5 says where they come from |
| I-D4 | `direction.lede.order` (sentence 2 of the lede, its own key since M10d) | "They are listed in the engine's order (longer phrases first, then how often they occur), which is evidence, not a recommendation." | HINT | T3/T4; keeps the rule that nothing here is Recommended (rule 3) |
| I-D5 | `direction.lede` (sentence 3) | "You can also write your own, or go on without one." | REMOVED | X1 the two controls say it (`direction.own.button`, `direction.skip.link`) |
| I-D6 | `direction.card.legend`, `card.position`, `card.anchors*`, `card.occurs`, `card.schools`, `card.noSchools` | "Direction {n}", "{n} anchor papers", "Term occurs in {observed} of {total} ..." | STAYS | V4 evidence beside the choice |
| I-D7 | `direction.card.detail.term`, `detail.vocab`, `card.showAll` | "Pool term observed in {n} papers", "Show all {n} DOIs" | STAYS | V5 provenance; already inside the card's Details (spec 12) |
| I-D8 | `direction.card.note` | "A paper anchors a direction only when ... The number of papers the databases returned is a different number and is not support." | HINT | T3 definition; the anchor-definition body shared with I-E26 |
| I-D9 | `direction.card.proposal`, `card.selected`, `card.earlier` | "Proposed by the wizard · not yet yours", "selected", "chosen on the earlier pool" | STAYS | V5 draft label and state |
| I-D10 | `direction.pool.line`, `pool.fromNarrower`, `pool.backFirst`, `pool.backFirstFresh` | "Pool of {n} papers · fetched {date} ...", "These directions come from the narrower search on ...", "The first search was partial, so going back runs it again." | STAYS | V4/V5/V6 |
| I-D11 | `direction.thin.title`, `thin.body`, `thin.raw`, `thin.accept` | "Only {n} papers came back", "I accept a pool this small" | STAYS | V2 warning and the box that gates the button |
| I-D12 | `direction.none.pool.title`, `none.pool.action`, `none.dir.title`, `none.dir.semantic` | "There is no pool to draw directions from", "No phrase occurs in two or more titles or abstracts" | STAYS | V3 empty result with its next step |
| I-D13 | `direction.none.dir.body` (sentence 1) | "Nothing is invented as a direction." | STAYS | V3 states what the engine did |
| I-D14 | `direction.none.dir.body` (sentence 2) | "You can change the scope, search with semantic search, write your own, or go on without one." | REMOVED | X1 four buttons already offer exactly these |
| I-D15 | `direction.skip.link`, `skip.note`, `skip.none.*` | "Continue without a direction", "The draft is recorded as not grounded, and Review and the protocol say so." | STAYS | V6 consequence before the choice is recorded |
| I-D16 | `direction.narrow.button`, `narrow.chooseFirst` | "Search again, narrower · {n} left", "Choose a direction first." | STAYS | V7/V2 |
| I-D17 | `direction.narrow.help` | "Searches the literature for the direction you have chosen." | HINT | T1 how-to |
| I-D18 | `direction.own.button`, `own.label`, `own.check`, `own.checking`, `own.check.grounded`, `own.check.groundedWords`, `own.check.under`, `own.grounded`, `own.groundedWords`, `own.ungrounded`, `own.dois` | "Your direction", "This phrase occurs in {observed} of {total} ... recorded as not grounded." | STAYS | V3 check result |
| I-D19 | `direction.own.help` | "Check my phrase counts how many titles or abstracts of the pool contain it. Under two, it is recorded as not grounded." | HINT | T1/T3; the result is I-D18 |
| I-D20 | `direction.pursue`, `pursue.empty`, `reason.choose`, `reason.thin`, `reason.busy`, `continue`, `back` | "Pursue {direction}", "Choose a direction, or write your own." | STAYS | V7/V2; main action: "Pursue {direction}", then "Continue to Shape" |
| I-D21 | `direction.bound.*` | "Your direction: {label}", "Grounded", "Bound {date} on the pool of {pooldate}" | STAYS | V5 provenance |
| I-D22 | `direction.leave.*` | "Your choice is not in the draft yet ..." | STAYS | V2 unsaved warning |
| I-D23 | `direction.seeds.title`, `seeds.count`, `seeds.max`, `seeds.anchors`, `seeds.none`, `seeds.saved`, `seeds.save`, `seeds.savedNote`, `seeds.label` | "Papers to check discovery against", "{n} of 25 ticked", "Anchors: {anchors}" | STAYS | V4/V5 |
| I-D24 | `direction.seeds.caption` | "The discovery Recall check will look for each one. Nothing is ticked for you." | HINT | T1/T4; the title names the purpose and the empty boxes show the rest |
| I-D25 | `direction.stale.*` | "The direction you chose was based on an earlier pool ..." | STAYS | V2 warning |
| I-SH1 | `shape.kicker`, `shape.title` | "Step 4 of 6 · Shape", "Which lens fits, and what will you ask?" | STAYS | V8 / the question |
| I-SH2 | `shape.lede` (sentence 1) | "A word scan of your topic leans one way; that lens is marked." | REMOVED | X1 the badge `shape.leaning` says it |
| I-SH3 | `shape.lede` (sentence 2) | "Choosing a lens marks the playbook that matches it and offers a first research question; you choose the playbook, and the question stays a draft until you use it." | STAYS | the one lede sentence |
| I-SH4 | `shape.paradigm`, `shape.playbook`, `shape.unit`, `shape.proof`, `shape.outOfScope`, `shape.rq`, `shape.addRq`, `shape.removeRq` | field and option labels | STAYS | V7 |
| I-SH5 | `shape.leaning` | "Leaning · word scan of your topic" | STAYS | V5 provenance and draft label (the mark's source, rule 3) |
| I-SH6 | `shape.leaningNote` | "The leaning is a keyword scan, not a judgement. Four lenses only; frameworks such as PICO or SPIDER are not offered yet." | HINT | T4 background; the badge keeps "word scan" visible |
| I-SH7 | `shape.recommended` | "Matches the lens" | STAYS | V5 becomes the Recommended mark (`guidance.recommended.by`); its why is the hint |
| I-SH8 | `shape.unitHelp` | "For example a model, a team, a crop field." | HINT | T2 example |
| I-SH9 | `shape.proofHelp` | "The wizard writes your first inclusion criterion from this answer." | HINT | T1; the criterion appears on step 5 with its source `source.proof` (V5) and waits for acceptance |
| I-SH10 | `shape.outOfScopeHelp` | "One item per line. Each becomes an exclusion criterion you typed." | HINT | T1 how-to |
| I-SH11 | `shape.rqDraft`, `shape.useDraft`, `shape.draftWaiting`, `shape.draftNeeds`, `shape.chooseLens` | "Template draft · not yet yours", "Use this draft as RQ{n}" | STAYS | V5/V8 |
| I-SH12 | `shape.lexicon` | "Vocabulary for this lens" | HINT | T2 examples of the lens's words |
| I-SH14 | `shape.planned.title`, `from`, `upTo`, `preset`, `usePreset`, `useEarlier`, `err.*` | "How many records do you plan to screen?", its fields, the preset and the range errors (M10b Part A) | STAYS | V7/V1 (row added by M10d) |
| I-SH15 | `shape.planned.hint` | "Titles and abstracts you will read. The size warnings before and after a harvest compare with this number." | HINT | T3; `04-shape` "The field" names it a Hint (row added by M10d) |
| I-SH13 | `shape.continue`, `shape.back`, `shape.needLens`, `shape.needPlaybook` | "Continue to concepts and criteria", "Back to Direction", "Choose a lens first.", "Choose a playbook first." | STAYS | V7/V2; main action "Continue to concepts and criteria" |
| I-C1 | `criteria.kicker`, `criteria.title` | "Step 5 of 6 · Concepts and criteria", "Which concepts and criteria will screen this review?" | STAYS | V8 / the question |
| I-C2 | `criteria.needYou`, `criteria.allDecided`, `criteria.sideCount` | "{n} still need you.", "{accepted} of {total} accepted" | STAYS | V3/V4 count of what waits |
| I-C3 | `criteria.lede` (sentence 1) | "Every criterion is shown word for word with where it came from." | REMOVED | X1 each criterion carries its `source.*` label |
| I-C4 | `criteria.lede` (sentence 2) | "A criterion the wizard wrote stays out of the protocol until you accept it." | STAYS | V6 the one lede sentence; states the gate before the decision |
| I-C5 | `criteria.concepts`, `criteria.concept`, `criteria.synonyms`, `criteria.addConcept`, `criteria.removeConcept`, `criteria.suggested`, `criteria.suggestedAdd` | field labels, "Suggested from your topic" | STAYS | V7/V5 |
| I-C6 | `criteria.anchor.concept`, `anchor.term`, `anchor.none`, `anchor.dois`, `anchor.scopeChanged` | "{concept}: in {anchored} of {total}", "not in the pool", "The pool was searched for an earlier scope; counts may not match." | STAYS | V3/V4/V2 |
| I-C7 | `criteria.anchor.note` | "A DOI in the pool is not enough: the term itself has to appear in the title or abstract." | HINT | T3 definition; the anchor-definition body shared with I-E26 |
| I-C8 | `criteria.synonyms.title`, `synonyms.group`, `synonyms.option`, `synonyms.none`, `synonyms.noPool`, `synonyms.goExplore`, `synonyms.more`, `synonyms.less` | "Terms from your first search · not yet yours", "{term} · {observed} papers" | STAYS | V5 draft label and V4 counts |
| I-C9 | `criteria.synonyms.help` | "Words that occur in at least two of the papers that matched this concept. Tick one to add it ... Nothing is added unless you tick it." | HINT | T1/T3; the boxes are unticked (rule 3) |
| I-C10 | `criteria.synonyms.unsaved` | "Saved with the page. Counts update after you save." | HINT | T1 how-to |
| I-C11 | `criteria.inclusion`, `criteria.exclusion`, `criteria.accepted`, `criteria.rejected`, `criteria.undecided`, `criteria.accept`, `criteria.reject`, `criteria.decision`, `criteria.addInclusion`, `criteria.addExclusion`, `criteria.newCriterion`, `criteria.add`, `criteria.remove` | list headings, badges, buttons | STAYS | V7/V3; the badge "Waiting for you" is a visible state |
| I-C12 | `source.proof`, `source.paradigm_default`, `source.out_of_scope`, `source.manual` | "Written by the wizard from your proof answer", "Typed by you" | STAYS | V5 provenance of each criterion |
| I-C13 | `criteria.defaultNo` | "Written by the wizard: not in the protocol unless you accept it." (once per wizard criterion) | REMOVED | X1 repeats I-C4 and the `source.*` and "Waiting for you" labels on every card |
| I-C14 | `criteria.editHint` | "To change it, change the answer it came from on Shape." (once per wizard criterion) | HINT | T1 how-to, one hint on the list heading, not one per row (rule 1.6) |
| I-C15 | `criteria.missingSide.inclusion`, `missingSide.exclusion` | "No inclusion criterion is accepted yet. Accept one above or add your own." | STAYS | V2 warning that blocks Review |
| I-C16 | `criteria.matrix`, `criteria.tickAll` | "Extraction matrix columns", "Tick all suggested columns" | STAYS | V7 |
| I-C17 | `criteria.matrixHelp` | "Ticked columns are saved in the protocol. With none ticked, the protocol has no matrix columns." | HINT | T1/T3 |
| I-C18 | `criteria.matrixCharting` | "These columns are filled on the Charting step." | STAYS | V2 says where the columns are filled (M12a DoD 9 replaced the parked line, `criteria.matrixParked`) |
| I-C19 | `criteria.verification` | "Run the post-screening verification checks (...)" | STAYS | V7 option label |
| I-C20 | `criteria.verificationParked` | "Advisory: Phase 4 checks are parked; this choice is saved in the protocol, nothing runs them yet." | STAYS | V2 an honest "not in production" |
| I-C21 | `criteria.continue` | "Continue to review" | STAYS | V7 main action |
| I-C22 | `criteria.reason.*` | the reason category of each exclusion (M10b Part A) | STAYS | V7/V1/V2 (row added by M10d; `criteria.reason.hasPhrases` and `noPhrases` are candidates for a hint in a later pass) |
| I-C23 | `criteria.mine.*` | the researcher's own matrix columns (M10b Part A) | STAYS | V7/V1/V5 (row added by M10d; `criteria.mine.descriptionHelp` is a candidate for a hint in a later pass) |
| I-R1 | `review.kicker`, `review.title` | "Step 6 of 6 · Review and create", "Check the protocol, then create the workspace" | STAYS | V8 / the question |
| I-R2 | `review.lede` (sentence 1) | "This is what will be written." | STAYS | the one lede sentence |
| I-R3 | `review.lede` (sentence 2) | "Nothing is written until you create the workspace." | REMOVED | X1 the gate says it (`review.gateBody`, I-R22) |
| I-R4 | `review.about`, `review.reviewTitle`, `review.lead`, `review.venue` | "About this review", field labels | STAYS | V7 |
| I-R5 | `review.reviewTitleHelp` | "The workspace folder is named after the title." | HINT | T1; the resulting path is shown as `review.folder` (V5) |
| I-R6 | `review.check`, `review.checking`, `review.notChecked`, `review.stale` | "Check the protocol", "Save the title and lead researcher, then check the protocol.", "The preview is out of date ..." | STAYS | V2/V8 |
| I-R7 | `review.lens`, `review.window`, `review.yearsRange`, `review.yearsOpen`, `review.yearsAny`, `review.questions`, `review.concepts`, `review.criteria`, `review.edit`, `review.rejected`, `review.screeningText` | the protocol summary | STAYS | V4/V5 what will be written |
| I-R8 | `review.direction.title`, `direction.chosen`, `direction.own`, `direction.grounded`, `direction.ungrounded`, `direction.occurs`, `direction.skipped`, `direction.none` | "Direction: {label}", "Not grounded" | STAYS | V3/V5 |
| I-R9 | `review.direction.skippedBody` | "The protocol will say it was not grounded in a direction." | REMOVED | X1 `review.direction.skipped` ("No direction chosen · Not grounded") says it |
| I-R10 | `review.seeds.count`, `seeds.none`, `seeds.details` | "Recall seeds kept: {n}", "DOIs" | STAYS | V4 |
| I-R11 | `review.seeds.caption` | "The discovery Recall check will look for these. They are written to the protocol when you create the workspace." | HINT | T1/T4; same sentence as the gate's list, which stays |
| I-R12 | `review.files`, `review.folder`, `review.fingerprint` | "Files that will be written", "Workspace folder", "Protocol fingerprint (preview)" | STAYS | V5 (in Details per spec 12 use 1) |
| I-R13 | `review.fingerprintNote` | "Creating the workspace stamps the date into the protocol, so the fingerprint written there differs from this preview. Done shows the written one." | HINT | T4; the label says "(preview)" (V5) and Done shows the written value (I-DN4) |
| I-R14 | `review.checks`, `review.check.decided`, `check.sides`, `check.compiler`, `check.free`, `check.folder`, `check.exists`, `check.bound` | the Checks list | STAYS | V3 check results |
| I-R15 | `review.targetExists`, `review.targetBound` | "A workspace already exists in this folder ...", "That workspace has screening decisions ..." | STAYS | V2 warning |
| I-R16 | `review.replaceTitle`, `review.replaceBody` | "Replace the protocol of the existing workspace?" and what is backed up | STAYS | V6 consequence of a destructive confirmation |
| I-R17 | `review.boundTitle`, `review.boundBody`, `review.boundType`, `review.boundConfirm`, `review.boundPublished`, `review.boundNotPublished` | "Screening was done under the current protocol ..." | STAYS | V6/V2 |
| I-R18 | `review.archive.title`, `review.archive.body` | "A replacement also archives ... These move into audit/replaced/<time>/" | STAYS | V6 what a replacement does |
| I-R19 | `review.gate`, `review.gateReplacing`, `review.gateBody` | "Create the workspace", "Writes the protocol, the criteria and the first audit journal entries into {path}." | STAYS | V6 the one gate |
| I-R21 | `review.synonyms`, `noSynonyms`, `planned`, `planned.stated`, `planned.notStated` | the concepts' synonyms and the planned records in the summary (M10b) | STAYS | V4/V5 what will be written (row added by M10d) |
| I-R20 | `review.create`, `review.creating`, `review.replace`, `review.cancel` | the main action and its confirmations | STAYS | V7 main action "Create the workspace" |
| I-DN1 | `done.kicker`, `done.title`, `done.titleReplaced` | "Done", "The workspace is created" | STAYS | V8 |
| I-DN2 | `done.lede` (sentence 1) | "The protocol and the criteria are written, and GENESIS is in the audit journal." | REMOVED | X1 the title and the rows below state it (folder, fingerprint) |
| I-DN3 | `done.lede` (sentence 2) | "Next, open the workspace and import your search results." | STAYS | the one lede sentence; replaced by the what's-next bar when 04-next-step ships |
| I-DN4 | `done.folder`, `done.fingerprint`, `done.previous`, `done.backup`, `done.archived` | "Folder", "Protocol fingerprint", "Old protocol backed up in" | STAYS | V5 provenance |
| I-DN5 | `done.archivedNote` | "The new protocol starts with no corpus; the earlier search results and decisions are in the backup folder." | STAYS | V6 consequence of the replacement |
| I-IM1 | `imported.*` | the "Started from {label}" banner, the per-step marks and the "does not store" lines of a draft started from a protocol (M10b Part A, `09-start-from-protocol`) | STAYS | V5/V2 (row added by M10d) |
| I-X1 | `start.*` | 08 Drafts and resume (`/inception`) | STAYS | screen outside this audit; it adopts the rules when it is audited (row added by M10d so every catalog key has a row) |
| I-X2 | `import.*` | 09 Start from a protocol (`/inception/import`) | STAYS | screen outside this audit (row added by M10d) |
| I-DN6 | `done.open`, `done.opening`, `done.another`, `done.allWorkspaces`, `done.notEmitted`, `done.toReview` | the actions and the not-created state | STAYS | V7/V8; main action "Open the workspace" |

### Discovery (phase 1)
Shared (the entry `/discovery/` and spec 07 "States"), then 01 Plan, 02 Recall, 03 Harvest, 04 Import (the discovery visit's additions; screen 11's own text is audited with Screening), 05 Duplicates, 06 Report, 07 Shared states (the cross-screen blocks), 08 Hand-off, 09 Chase. Spec 07 has no route: its blocks are the DS rows.

| ID | Copy key | Text today | Decision | Reason |
| :-- | :-- | :-- | :-- | :-- |
| D-DS1 | `steps.*`, `eyebrow`, `asOf`, `loading`, `lowerBound`, `copied` | the step bar, "Step {n} of 7 · {name}", "As of {time}", "at least {n}" | STAYS | V8 status and navigation |
| D-DS2 | `run.label`, `run.option`, `run.stale`, `run.staleBody`, `run.readonly`, `run.describes`, `run.differs`, `run.newest` | the run selector and its warnings ("A later run's records became the corpus ...") | STAYS | V5/V2 provenance and staleness |
| D-DS3 | `job.connectionLost`, `job.retry`, `job.follow`, `job.otherKind`, `job.openHarvest`, `job.openRecall` | "Connection lost · as of {time}", "Another discovery job is running ..." | STAYS | V2/V8 |
| D-DS4 | `job.keepOpen` | "Keep this window's console open until the harvest ends; closing the console stops the harvest ..." | STAYS | V2 warning: closing the console stops the run |
| D-DS5 | `mailto.title`, `mailto.line`, `mailto.where`, `mailto.check` | the MAILTO_NOT_SET card with the line to set | STAYS | V1 refusal and its next step |
| D-DS6 | `openalexKey.title`, `openalexKey.line`, `openalexKey.where` | the OpenAlex key card | STAYS | V1 refusal and its next step |
| D-DS7 | `amend.link` | "Change the protocol through inception" | STAYS | V7 link |
| D-DS8 | `amend.help` | "A different query or database is a protocol amendment, recorded by inception." | REMOVED | no longer true for the query since M11a part D: Recall's hint is now `plan.search.help` on its "Change the search" link (D-P24); the inception link stays without a hint |
| D-DS9 | `status.PENDING_CORPUS_ACCEPT`, `status.PARTIAL`, `status.CANCELLED`, `status.COMPLETED`, `status.FAILED` | run status badges | STAYS | V3 status in role colour, with words |
| D-DS10 | `overview.title` | "Where the search stands" | STAYS | the question |
| D-DS11 | `overview.lede` (sentence 1) | "Each line below is read from the engine." | REMOVED | X1 the "As of" caption carries the provenance |
| D-DS12 | `overview.lede` (sentence 2) | "Every step stays open; nothing here is locked." | HINT | T3 definition of the page |
| D-DS13 | `overview.recall.done`, `recall.earlier`, `recall.none`, `harvest.done`, `harvest.none`, `harvest.running`, `harvest.unfinished`, `import.done`, `import.none`, `dedup.done`, `dedup.none`, `report.done`, `report.none`, `handoff.done`, `handoff.none` | one status line per step | STAYS | V3/V8 step status |
| D-DS14 | `overview.plan.line` | "The plan records nothing: starting a harvest is the record." | HINT | T4 background |
| D-DS16 | `overview.recall.earlier` | "The last recall check was made for an earlier protocol." | STAYS | V2 (row added by M10d: the D-DS13 group missed it) |
| D-DS17 | `combined.state.running`, `combined.state.incomplete`, `combined.state.failed`, `combined.state.stopped`, `combined.state.interrupted` | "being prepared", "not fully checked", "preparation failed", "stopped", "interrupted": the words that fill `{state}` in D-I9 and D-HO19 (M3f-combined-corpus; an unknown state is printed verbatim) | STAYS | V8 the state in words, never colour alone |
| D-DS15 | `overview.continue` | "Continue at {step}" | STAYS | V7 the step-level recommendation; replaced by the what's-next bar (04-next-step) |
| D-P1 | `plan.eyebrowName`, `plan.title` | "Search plan", "This is what each database will receive" | STAYS | V8 / the question |
| D-P2 | `plan.lede` (sentence 1) | "The question comes from the frozen protocol." | STAYS | the one lede sentence; V5 where it comes from |
| D-P3 | `plan.lede` (sentence 2) | "Each string is sent exactly as written; the executed forms below are the engine's translation, shown before anything is sent." | REMOVED | X1 the badge `plan.string.badge` ("Translated by the engine · not yet sent") says it |
| D-P4 | `plan.strings.title`, `plan.fingerprint`, `plan.string.badge`, `plan.status.*` | "Executed string per database", badges | STAYS | V5 draft/provenance labels |
| D-P5 | `plan.noPreview`, `plan.notSearched`, `plan.cannotExpress`, `plan.nothingDropped` | "Not expressed: {list}", "The engine reports nothing dropped for this database." | STAYS | V2/V3 what the translation could not carry |
| D-P6 | `plan.request.show`, `plan.copyAll` | "Show the request", "Copy all executed strings" | STAYS | V7 controls (the request is already a `<details>`) |
| D-P7 | `plan.imports.hint` | "Scopus and Web of Science have no connection. Search them yourself and import the export." | HINT | T1 how-to |
| D-P8 | `plan.imports.afterRun` | "You can still add database exports; they are combined with this harvest when you accept the corpus." (reworded by M3f-combined-corpus, 2026-11-20; the key is in the catalog and is not rendered, as before) | REMOVED | X2 `harvest.warn.imports` says it at the harvest, where it matters (D-H12) |
| D-P9 | `plan.limits.title`, `limits.window`, `limits.noLimit`, `limits.language`, `limits.cap` | "Limits", "Date window", "Cap per database" | STAYS | V4 the limits that apply |
| D-P10 | `plan.limits.cap.protocol` | "Set in the protocol. A database that stops at the cap is reported as at least that many, never as complete." | HINT | T3 definition; the per-row lower-bound label is D-H5 |
| D-P11 | `plan.limits.cap.engine_ceiling` | "The protocol sets no cap; the engine stops at {ceiling} records per database." | STAYS | V2 a limit that changes the result |
| D-P12 | `plan.limits.mailto.set`, `mailto.notSet`, `s2Key.title`, `s2Key.set` | "Set", "Not set", "Semantic Scholar API key" | STAYS | V3 status of what a run needs |
| D-P13 | `plan.limits.mailto.help` | "Required by Crossref and PubMed. OpenAlex needs its API key instead." | HINT | T3; the missing setting itself is D-DS5 |
| D-P14 | `plan.limits.openalexKey.help` | "Required by OpenAlex. Without it a run that includes OpenAlex is refused." | HINT | T3; when the key is missing the refusal card D-DS6 is visible |
| D-P15 | `plan.limits.s2Key.help` | "Optional. Without it Semantic Scholar is searched in its shared keyless pool ..." | HINT | T3/T4 |
| D-P16 | `plan.noneSelected`, `plan.next`, `plan.changed` | "The protocol selects no database to search.", "Continue to Recall", "The protocol changed since this page was read." | STAYS | V2/V7; main action "Continue to Recall" |
| D-P17 | `plan.picker.title`, `picker.legend`, `picker.check.*`, `picker.up.*`, `picker.down.*`, `picker.moved`, `picker.none`, `picker.unknown`, `picker.reset`, `picker.loading` | "Databases for this harvest", the per-database controls, "Pick at least one database.", "Loading the plan for this choice" | STAYS | V7 controls and their names; V1 the "at least one" refusal; V8 loading (the same decision as I-E40) |
| D-P18 | `plan.picker.orderHelp` | "The order only sets the order the databases are searched and listed; it never changes the corpus." | HINT | T3 what the order means (the same decision as I-E41) |
| D-P19 | `plan.picker.differs`, `picker.differs.*` | "This harvest differs from the protocol: {list}" | STAYS | V5/V2 the harvest's choice against the protocol's, before it is sent |
| D-P21 | `estimate.*` | the size estimate (M10b Part D) on Plan and Harvest: the counts, the cap lines, the warnings, the suggested cap | STAYS | V4/V2/V5/V7 (row added by M10d, 2026-11-19); the suggested cap carries the Recommended mark (rule 3). `estimate.cap.order`, `estimate.works.assumption`, `estimate.effort.basis`, `estimate.pace.help` and `estimate.rec.cap.help` are candidates for a hint in a later pass |
| D-P20 | `plan.next.harvest` | "Continue to Harvest with this choice" | STAYS | V7 the link that carries the choice to Harvest |
| D-P22 | `plan.ignoresAnd`, `plan.defaultWithout` | "Crossref does not apply the AND between the {n} concepts of this query: ...", "Crossref is left out by default: ..." (Plan and Harvest) | STAYS | V2 warning: a database that would return off-topic records; V5 why the default choice differs from the protocol (row added by H-run-small-fixes Part B, 2026-11-20) |
| D-P23 | `plan.search.open`, `plan.search.close`, `plan.search.protocol`, `plan.search.version`, `plan.search.noConcepts` | "Change the search", "In the protocol" | STAYS | V7 the section's one control and its read-only group (M11a part D) |
| D-P24 | `plan.search.help` | "A different query is an amendment of the protocol's search. It is recorded with your reason. ..." | HINT | T1 how-to on the section heading; replaces `plan.amend.help` for the query (10-plan-amend-search) |
| D-P25 | `plan.search.record`, `plan.search.recording`, `plan.search.cancel`, `plan.search.reason.label`, `plan.search.reason.help`, `plan.search.reason.need`, `plan.search.confirm.title` | "Record this amendment", "Why are you changing the search?" | STAYS | V6 the one write and its reason field |
| D-P26 | `plan.search.conseq.*` | "{run} ({n} records) was searched with the earlier query. After this amendment it cannot become the corpus; harvest again." | STAYS | V2 what the amendment makes obsolete, engine-written, before the write |
| D-P27 | `plan.search.counts.before`, `plan.search.counts.after`, `plan.search.counts.none` | "Before: {summary}", "not counted" | STAYS | V4 the counts the journal row records |
| D-P28 | `plan.search.done`, `plan.search.backup` | "Amendment recorded. The search in the protocol has changed." | STAYS | V3 the result and where the earlier files are |
| D-P29 | `plan.search.accepted`, `plan.search.accepted.new` | "The corpus is accepted, so the search is not amended here. ..." | STAYS | V2 why nothing is recorded after the accept, and the way on |
| D-P30 | `plan.search.err.jobActive`, `plan.search.err.outside`, `plan.search.details` | "A search or a check is running in this workspace, so the search cannot be amended now. ..." | STAYS | V2 refusals in words |
| D-R1 | `recall.eyebrowName`, `recall.title`, `recall.titleNone` | "The query finds {found} of the {total} papers you gave it" | STAYS | V4 the result is the title |
| D-R2 | `recall.lede` (sentence 1) | "Each seed is looked up and compared by title first." | STAYS | the one lede sentence |
| D-R3 | `recall.lede` (sentence 2) | "A paper no database returns is listed; nothing is blocked." | REMOVED | X1 `recall.missedEverywhere` lists it and the miss hint says "nothing is blocked" |
| D-R4 | `recall.ledeEmpty` (sentence 1) | "Give the papers you already know are relevant." | STAYS | the one lede sentence in the empty state |
| D-R5 | `recall.ledeEmpty` (sentence 2) | "The check looks each one up and says which databases find it." | REMOVED | X1 the title and the result table say it |
| D-R6 | `recall.seeds.title`, `recall.col.*`, `recall.source.you`, `recall.source.anchor`, `recall.found`, `recall.notFound`, `recall.na`, `recall.failed`, `recall.missedEverywhere` | the seed table | STAYS | V3 check results with source (You / Anchor) |
| D-R7 | `recall.titleCheck.DOI_TITLE_MISMATCH`, `recall.titleCheck.unresolved` | "This DOI resolves to a different title ..." | STAYS | V3/V2 |
| D-R8 | `recall.legend` | "Not found means the database did not return the paper for this query. It does not say why." | REMOVED | X1 duplicates the miss hint (D-R9) |
| D-R9 | `recall.mean.title`, `recall.mean.one`, `recall.mean.all` | "What a miss means" and its two readings | HINT | T3/T4; one hint on the "Not found" column heading; the result itself stays (D-R6) |
| D-R10 | `recall.checkedAt`, `recall.queryChecked`, `recall.earlierProtocol` | "Checked {date} UTC", "This check was made for an earlier protocol ..." | STAYS | V5/V2 |
| D-R11 | `recall.form.title`, `form.kind*`, `form.id`, `form.max`, `form.add`, `form.remove` | "Check these papers", "At most 25 seeds." | STAYS | V7/V2 |
| D-R12 | `recall.form.help` | "Give identifiers taken from a real record. A DOI whose title does not match is reported, not replaced." | HINT | T1/T4; the mismatch itself is D-R7 |
| D-R13 | `recall.form.anchorNote` | "These are the anchor papers you kept in inception. Remove any you do not want, or add your own." | HINT | T1; each row carries `recall.form.anchorRow` ("Anchor", V5) |
| D-R14 | `recall.form.anchorRow`, `recall.form.anchorTitleLater` | "Anchor", "The title appears after the check." | STAYS | V5/V2 what is not yet known |
| D-R15 | `recall.submit`, `recall.submitAgain`, `recall.cancel`, `recall.cancelled`, `recall.checking*`, `recall.asking`, `recall.earlier`, `recall.next`, `recall.accepted` | the actions and states | STAYS | V7/V8; main action "Check these seeds", then "Continue to Harvest" |
| D-H1 | `harvest.eyebrowName`, `harvest.title.*` | "Search the databases your protocol selects" and the run states | STAYS | V8 / the state in one sentence |
| D-H2 | `harvest.lede.ready` (sentence 1) | "Each database receives the string shown on the plan." | STAYS | the one lede sentence |
| D-H3 | `harvest.lede.ready` (sentence 2) | "Nothing is frozen by a harvest; the corpus is frozen on the hand-off screen." | REMOVED | X2 `harvest.title.finished` and `harvest.stage.corpusNotFrozen` say it |
| D-H4 | `harvest.badge.*`, `harvest.willSearch`, `harvest.legs.title`, `harvest.col.*`, `harvest.count.of`, `harvest.count.unknown`, `harvest.leg.status.*`, `harvest.leg.capSource.*`, `harvest.leg.notSelected`, `harvest.leg.offByDefault`, `harvest.headline` | the per-database table and headline | STAYS | V3/V4 |
| D-H5 | `harvest.leg.capped`, `harvest.leg.failedNoCode`, `harvest.leg.code.*`, `harvest.leg.stopped`, `harvest.failedList` | "The database stopped at the cap, so this count is a lower bound.", "The database limited the request rate." | STAYS | V1/V2 per-row lower bound and failure |
| D-H6 | `harvest.stages.title`, `harvest.stage.discovery`, `stage.deduplication`, `stage.verification`, `stage.hydration`, `stage.corpus_snapshot` | "Steps after the search" | STAYS | V8 (folded section, rule 4) |
| D-H7 | `harvest.stage.corpusNotFrozen` | "The corpus is frozen on the hand-off screen." | REMOVED | X1 `harvest.title.finished` ("The corpus is not frozen yet.") says it |
| D-H8 | `harvest.recall.line`, `harvest.recall.none` | "A recall check preceded this run: {found} of {total}, {date}", "No recall check preceded this run." | STAYS | V5 provenance and what is not known |
| D-H9 | `harvest.note.label`, `harvest.capOverride.line`, `harvest.form.title`, `harvest.form.cap`, `harvest.form.capInvalid`, `harvest.form.note` | "This harvest", "Cap for this harvest only", "Cap for this run: {value} (run override)" | STAYS | V7/V5 an override is recorded |
| D-H10 | `harvest.form.capHelp` | "Overrides the protocol's cap of {value} for every database in this run. It is recorded ... Between 1 and {ceiling}." | HINT | T1/T3; the suggested cap is marked Recommended when the size estimate (`01-plan` "Size estimate (M10b)") exists |
| D-H11 | `harvest.form.noteHelp` | "Kept with the run and printed in the report." | HINT | T1 how-to |
| D-H12 | `harvest.start`, `harvest.again`, `harvest.againHelp`, `harvest.warn.imports` | "Start the harvest", "A new harvest replaces this run as the candidate corpus ...", "Database exports you add on the Import step, before or after this harvest, are combined with it when you accept the corpus on the Hand-off, and duplicates across both are removed." (`harvest.warn.imports` reworded by M3f-combined-corpus, 2026-11-20) | STAYS | V6 consequence before the main action; main action "Start the harvest" |
| D-H13 | `harvest.stop`, `harvest.stop.late`, `harvest.stop.prepare` | "Stop the harvest and keep what was fetched", "Stop after the current step", and since M3i "Fetching is finished. A stop now takes effect when the current step ends ..." | STAYS | V7 the button says what is kept; V6 when a stop takes effect, said before the click |
| D-H14 | `harvest.stop.title`, `harvest.stop.body` | "If you stop: Fetched records are kept and the run is marked partial ..." | HINT | T1 reassurance; the button label states the consequence |
| D-H15 | `harvest.saved` | "The databases, queries and counts are saved with the run and printed in the search report." | HINT | T4 background |
| D-H16 | `harvest.next.*`, `harvest.changed`, `harvest.accepted`, `harvest.reading` | "Go to Duplicates", "This run searched an earlier query or year window ..." | STAYS | V7/V2 |
| D-H17 | `harvest.asked.title`, `harvest.leg.query`, `harvest.leg.status.none`, `harvest.leg.notChosen` | "Databases asked, in order", "Query sent", "0 results", "Not selected for this harvest." | STAYS | V3/V5 what each database received and returned (M10a, recounted 2026-11-18) |
| D-H18 | `harvest.title.preparing`, `harvest.title.prep.*`, `harvest.badge.preparing`, `harvest.prep.card`, `harvest.prep.badge.*` | "The corpus is being prepared", "The search finished, but preparing the corpus failed.", "Preparation unfinished" | STAYS | V8 the state in one sentence and its badge (M3i) |
| D-H19 | `harvest.preparing.lede` | "Removing duplicates, adding missing abstracts and checking the works of {run}. No database is searched." | STAYS | the one lede sentence of the preparing state; V6 nothing leaves the machine |
| D-H20 | `harvest.prep.failed`, `prep.stopped`, `prep.interrupted`, `prep.interruptedAt`, `prep.noMarker`, `prep.error` | "The step “{stage}” then failed, so screening has nothing to receive yet.", "This run was made by an earlier version ..." | STAYS | V2 what failed and what is not known |
| D-H21 | `harvest.prep.ended`, `prep.noneEnded` | "Steps that ended", "No step after the search ended." | STAYS | V4 the stages as recorded |
| D-H22 | `harvest.prep.finish`, `prep.cannotFinish`, `prep.cannotFinishAccepted` | "Finish preparing this corpus", "The saved records of this run cannot be read, so it cannot be finished." | STAYS | V7 the main action of the state; V1 why it is not offered |
| D-H24 | `harvest.capPrefilled` | "Filled in from the estimate. You can change it." | STAYS | V5 provenance of a filled value (row added by M10d) |
| D-H23 | `harvest.prep.finishHelp` | "Removes duplicates, adds missing abstracts and checks the works, from the saved records. No database is searched again." | HINT | T1 how it works; the button names the action |
| D-H26 | `harvest.prep.incomplete.quota`, `harvest.prep.incomplete.paused`, `harvest.prep.incomplete.stopped`, `harvest.prep.incomplete.count`, `harvest.prep.incomplete.unverified`, `harvest.prep.incomplete.unenriched`, `harvest.prep.incomplete.afterReset`, `harvest.prep.incomplete.now` | "The OpenAlex quota is used up. It resets at {time}.", "{unchecked} of {records} records were not fully checked. ...", "After the reset, press “Finish preparing this corpus” ..." | STAYS | V2 why the checks ended early, what was not checked and what to do (H-quota-hang) |
| D-H27 | `harvest.prep.incomplete.finishHelp` | "Checks only the records not checked yet, from the saved records. No database is searched again." | HINT | T1 how it works; the button names the action (the same decision as D-H23; H-quota-hang) |
| D-I1 | `import.eyebrow`, `import.back`, `import.handoff` | "Step 4 of 7 · Import", "Back to discovery", "Go to the hand-off" | STAYS | V8/V7 |
| D-I2 | `import.limits.label`, `import.limits.row` | "Limits you applied there, if any", "Limits" | STAYS | V7/V5 the limits the researcher states are recorded |
| D-I3 | `import.limits.help` | "For example: document type, language, subject area. Stored exactly as you write it and printed in the search report." | HINT | T2 example |
| D-I4 | `import.rejected.title`, `rejected.caption`, `rejected.line`, `rejected.code`, `rejected.what`, `rejected.IMPORT_NO_TITLE`, `rejected.IMPORT_BAD_TAG`, `rejected.IMPORT_BAD_YEAR` | "Lines the importer noted" and what happened to each | STAYS | V3 check result per line |
| D-I5 | `import.rejected.inReport` | "The lines noted here are listed in the search report." | HINT | T1 where they end up |
| D-I6 | `import.inReport` | "These appear in the search report." | REMOVED | X1 says what D-I5 says |
| D-I7 | `import.refused.title`, `refused.body`, `refused.affects`, `refused.action` | "This workspace holds records whose origin the app does not know (no search and no import of this app made them), so a database export is not added to them." (reworded by M3f-combined-corpus: the title and body now say the unknown-origin case) | STAYS | V1 refusal (VERIFIED_EXISTS, now only for a `verified.json` of unknown origin) |
| D-I8 | `import.rule` | "Add exports before or after a harvest; they are combined with it when you accept the corpus on the Hand-off. You can remove a staged export any time before the accept." (reworded by M3f-combined-corpus; it said "either a harvest or imported exports, not both") | HINT | T4; the stronger statements are D-I9 (the combined line) and D-H12 (warning at the harvest) |
| D-I9 | `import.combined.with`, `import.combined.notReady`, `import.combined.openHarvest`, `import.combined.accepted` | "These exports will be combined with the harvest {run} when you accept the corpus on the Hand-off.", "The harvest {run} is not prepared ({state}), so it is not part of this corpus yet. ...", "Combined with the harvest {run}." (M3f-combined-corpus) | STAYS | V2/V5/V6 what the accept will include, said before the accept; one line at a time, above the file list |
| D-DD1 | `dedup.eyebrowName`, `dedup.title` | "{input} records became {unique} works." | STAYS | V4 the result is the title |
| D-DD2 | `dedup.lede` (sentence 1) | "The harness merged records that are the same work by three rules." | STAYS | the one lede sentence |
| D-DD3 | `dedup.lede` (sentence 2) | "The rules and their settings are below." | REMOVED | X3 describes the layout |
| D-DD4 | `dedup.counts`, `dedup.in`, `dedup.out`, `dedup.removed`, `dedup.rate`, `dedup.rateWritten` | counts and "Written by the harness as {fraction}" | STAYS | V4/V5 (the written value is under Details already) |
| D-DD5 | `dedup.tiers`, `dedup.tier.identifier`, `dedup.tier.exactTitle`, `dedup.tier.fuzzyTitle`, `dedup.tier.notRecorded` | "Removed per rule" | STAYS | V4 |
| D-DD6 | `dedup.rules.title`, `rules.similarity`, `rules.years`, `rules.author`, `dedup.yes`, `dedup.no`, `rules.sourceProtocol`, `rules.sourceDefault` | the rules and where they came from | STAYS | V5 provenance of the settings |
| D-DD7 | `dedup.run`, `dedup.runMismatch` | "This is the newest deduplication, from {run}.", "You are viewing {selected}. ..." | STAYS | V2/V5 |
| D-DD8 | `dedup.pairsNote` | "Records the rules did not prove to be the same work are not listed here and stay separate works." | HINT | T3 definition |
| D-DD9 | `dedup.importNote` | "A database export you staged is deduplicated when you accept it; its counts are on the hand-off." | HINT | T1/T4 |
| D-DD10 | `dedup.next`, `dedup.back` | "Continue to the report" | STAYS | V7 main action |
| D-RP1 | `report.eyebrowName`, `report.title` | "What each database was asked and what came back." | STAYS | V8 / the question |
| D-RP2 | `report.lede` (sentence 1) | "Every row carries the exact string sent, the database's own total, the fetched count and the UTC date." | REMOVED | X1 the column headings say it |
| D-RP3 | `report.lede` (sentence 2) | "A count stopped at a cap is a lower bound." | REMOVED | X1 `report.completeness.lowerBound` and `completeness.atLeast` label each row |
| D-RP4 | `report.capOverride`, `report.identification`, `report.col.*`, `report.reportedNone`, `report.noAbstractNone`, `report.copy`, `report.completeness.full`, `completeness.lowerBound`, `completeness.atLeast`, `completeness.failed`, `completeness.stopped`, `report.kind.import` | the PRISMA-S table | STAYS | V3/V4/V5 |
| D-RP5 | `report.completeness.lowerBoundNote` | "Stopped at the cap, so the database holds at least this many." (once per capped row) | HINT | T3, one hint on the "Completeness" heading (rule 1.6); each row keeps "Lower bound / At least {n}" |
| D-RP6 | `report.notSearched.title`, `notSearched.off`, `notSearched.notSelected` | "Not searched" | STAYS | V3 what was not asked |
| D-RP7 | `report.imports.title`, `imports.none`, `imports.limits`, `imports.records` | "Database exports" | STAYS | V5 |
| D-RP8 | `report.dedup.title`, `dedup.removed`, `dedup.unique`, `dedup.notThisRun`, `dedup.notThisRunShort`, `report.window` | "Duplicate counts are not this run's ..." | STAYS | V4/V2 |
| D-RP9 | `report.prisma.title`, `prisma.none`, `prisma.identified`, `prisma.duplicates`, `prisma.screened`, `prisma.excluded`, `prisma.included` | "Screening so far" | STAYS | V4 |
| D-RP10 | `report.methods.title`, `methods.label`, `methods.badgeDraft`, `methods.badgeReviewed`, `methods.badgeEdited`, `methods.built` | "Methods text · draft · not reviewed", "Built from {run} by the harness's template. Check every number against the rows above." | STAYS | V5 draft label and the instruction that makes it a draft |
| D-RP11 | `report.methods.review`, `methods.saving`, `methods.draft`, `methods.unreview`, `methods.confirmDraft`, `methods.copy`, `methods.earlier`, `methods.count`, `methods.tooLong`, `methods.saved` | the methods actions | STAYS | V6/V7 the review is a human gate |
| D-RP12 | `report.history.title` | "Run history" | STAYS | V5 (folded section) |
| D-RP13 | `report.history.note` | "Each run keeps its own files; none is overwritten." | HINT | T4 background |
| D-RP14 | `report.markdown` | "Open the report as markdown" | STAYS | V7 |
| D-RP15 | `report.again` | "To fetch more, search again from Harvest (a higher cap can be chosen there)." | HINT | T1 how-to |
| D-RP16 | `report.stringsNote` | "These are the strings sent in {run}; they may differ from today's plan." | STAYS | V2/V5 |
| D-RP18 | `report.dedup.removed` | "Removed" | STAYS | V4 (row added by M10d: the D-RP8 group missed it) |
| D-RP19 | `report.kind.search`, `report.kind.import`, `report.import.notStated` | "searched by the app", "your export" (`report.kind.import` was "export"), "not stated" (M3f-combined-corpus; it fills the date, search-string and limits cells of an export row that has none) | STAYS | V3/V5 what each identification row is and what the researcher stated, "not stated" is a "not known" (V2) |
| D-RP20 | `report.dedup.combinedNote` | "This count covers the harvest and your exports together, so it is not broken down by rule." (M3f-combined-corpus; shown when `dedup.by_tier` is null for a combined corpus) | STAYS | V4/V2 what a number covers |
| D-RP17 | `report.next`, `report.back`, `report.running`, `report.offline` | "Continue to hand-off" | STAYS | V7/V8; main action: "I reviewed this text" while unreviewed (the human gate), then "Continue to hand-off" |
| D-HO1 | `handoff.eyebrowName`, `handoff.title`, `handoff.titleNoCount` | "Accept these {n} works as the corpus you will screen?" | STAYS | V6 the question the gate asks |
| D-HO2 | `handoff.lede` (sentence 1) | "Accepting freezes a corpus snapshot with its own fingerprint." | STAYS | the one lede sentence; V6 |
| D-HO3 | `handoff.lede.why` (sentence 2 of the lede, its own key since M10d) | "Screening reads only that snapshot, so later runs cannot change what you screen." | HINT | T4 why the freeze exists; the gate says nothing is handed over before accepting |
| D-HO4 | `handoff.mix.title`, `mix.row`, `mix.none` | "Provider mix", "{records} records · {share}" | STAYS | V4 |
| D-HO5 | `handoff.mix.note` | "A work found in two databases is counted in both, so shares can add up to more than 100 %." | HINT | T3 explains a number; each number stays |
| D-HO6 | `handoff.receive.title`, `receive.identified`, `receive.duplicates`, `receive.works`, `receive.withAbstract`, `receive.titleOnly`, `receive.hard`, `receive.window`, `receive.lowerBound`, `receive.none` | "What screening will receive" | STAYS | V4 |
| D-HO7 | `handoff.receive.lowerBoundNote`, `handoff.receive.noPreview` | "{names}: a count stopped at its cap is a lower bound. The report says so." | STAYS | V2 |
| D-HO8 | `handoff.from.title`, `from.run`, `from.protocol`, `from.sources` | "From", "Search run {run}", "Protocol fingerprint" | STAYS | V5 |
| D-HO9 | `handoff.gate.label`, `gate.body`, `gate.accept`, `gate.accepting`, `gate.offline`, `gate.running`, `gate.protocolChanged` | "Gate · accept the corpus", "Nothing is handed to screening until you accept ..." | STAYS | V6 the one gate; main action "Accept this corpus" |
| D-HO10 | `handoff.failedNote` | "If a database failed in the corpus run, the report names it." | REMOVED | X1 the per-database rows and `receive.lowerBound` name it, and "Read the report" is a link |
| D-HO11 | `handoff.again`, `handoff.report`, `handoff.import` | "Search again", "Read the report", "Stage an export" | STAYS | V7 quiet links |
| D-HO12 | `handoff.accepted.title`, `accepted.card`, `accepted.id`, `accepted.at`, `accepted.counts`, `accepted.go` | "This corpus is accepted." | STAYS | V5 |
| D-HO13 | `handoff.empty.title`, `handoff.empty.body` | "There is nothing to hand off yet." | STAYS | V3 empty with its next step |
| D-HO14 | `handoff.pending.title`, `pending.running`, `pending.runningNoStage`, `pending.failed`, `pending.stopped`, `pending.interrupted`, `pending.incomplete` | "The corpus is not ready to hand off yet." and one sentence by state ("... failed at the step “{stage}”.") | STAYS | V3/V2 the state of the preparation and the stage it stopped at (M3i) |
| D-HO17 | `handoff.mix.kind.search`, `handoff.mix.kind.import` | "searched by the app", "your export": the word beside each provider-mix name (M3f-combined-corpus) | STAYS | V5 provenance of a source, in words, not colour alone |
| D-HO18 | `handoff.imports.unchecked` | "{n} records come from your exports. They were not checked against Crossref or OpenAlex, and missing abstracts were not filled in." (M3f-combined-corpus; shown when `imports_unchecked` > 0, blocks nothing) | STAYS | V2 a "not checked" that changes how far the records can be trusted |
| D-HO19 | `handoff.harvestOut.note`, `handoff.harvestOut.open` | "The harvest {run} is not prepared ({state}). If you accept now, the corpus holds your exports only and the harvest's records are left out for good. Finish preparing it first to include them.", "Open Harvest" (M3f-combined-corpus) | STAYS | V6 the consequence before the gate; the unclear role, Accept stays enabled |
| D-HO15 | `handoff.pending.kept` | "The records found are saved; nothing has to be searched again." | HINT | T1 reassurance; the link names the action (the same decision as D-H14) |
| D-HO16 | `handoff.pending.finish`, `handoff.pending.follow` | "Finish preparing this corpus on Harvest", "Follow the harvest" | STAYS | V7 the main action of the Not ready state |
| D-CH1 | `chase.eyebrow`, `chase.eyebrowRun`, `chase.title.*` | "Chase the citations of your included studies" and the run states | STAYS | V8 / the state in one sentence |
| D-CH2 | `chase.lede` (sentence 1) | "The chase asks OpenAlex and Semantic Scholar which works cite your included studies and which works they cite." | STAYS | the one lede sentence; V6 what is asked, of whom |
| D-CH3 | `chase.lede` (sentence 2) | "What is new is screened as a separate second round and counted in its own arm of the PRISMA flow." | REMOVED | X2 `chase.gate.body` says it, fully, at the gate |
| D-CH4 | `chase.seeds.title`, `seeds.source.*`, `seeds.count`, `seeds.notChaseable.title`, `seeds.notChaseable.row` | "{chaseable} of {total} can be chased", "{title}: {reason}" | STAYS | V3/V4 |
| D-CH5 | `chase.seeds.notChaseable.help` | "A study needs a DOI, an OpenAlex id or a Semantic Scholar id to be chased." | HINT | T3 definition; each row keeps its reason |
| D-CH6 | `chase.keys.*` | "OpenAlex key set", "The chase needs an OpenAlex key." | STAYS | V1/V2 status of what a run needs |
| D-CH7 | `chase.options.title`, `options.directions`, `options.dir.*`, `options.providers`, `options.cap`, `options.ceiling`, `options.invalid`, `options.seedSource`, `options.note` | the options form | STAYS | V7/V5 |
| D-CH8 | `chase.options.capHelp` | "Citing works are capped per study and database; a capped count is a lower bound. References are not capped." | HINT | T3; per-row lower bound stays on the legs |
| D-CH9 | `chase.options.ceilingHelp` | "Beyond {ceiling} new works the run is partial." | HINT | T3; the partial result is `chase.partial.ceiling` (D-CH14) |
| D-CH10 | `chase.options.noteHelp` | "Kept with the run and printed in the report." | HINT | T1; the same body as D-H11 |
| D-CH11 | `chase.start`, `chase.startDisabled.*`, `chase.again`, `chase.back`, `chase.stop`, `chase.stopping`, `chase.badge.running`, `chase.reading` | "Chase citations", "Set the OpenAlex key first." | STAYS | V7/V2; main action "Chase citations" |
| D-CH12 | `chase.warn.console` | "Keep this window's console open until the chase ends; closing the console stops it ..." | STAYS | V2 warning |
| D-CH13 | `chase.stop.title`, `chase.stop.body` | "If you stop: Fetched records are kept in the run folder. Nothing is published ..." | HINT | T1 reassurance; same decision as D-H14 |
| D-CH14 | `chase.legs.title`, `legs.show`, `legs.perSeed`, `chase.col.*`, `chase.dir.*`, `chase.count.of`, `chase.leg.*`, `chase.partial.failedNote`, `chase.partial.ceiling` | the legs table (with M10a's `chase.leg.zero` "0 results") | STAYS | V3/V4 failures and caps are results |
| D-CH15 | `chase.counts.title`, `counts.raw`, `counts.dupes`, `counts.inCorpus`, `counts.window`, `counts.over`, `counts.new`, `chase.inCorpus.*`, `chase.notes` | "What the chase found" | STAYS | V4 |
| D-CH16 | `chase.empty.noSeeds`, `chase.empty.nothingNewBody`, `chase.cancelled.body`, `chase.failed.body` | "The chase found nothing new." and the counts say which | STAYS | V3 |
| D-CH17 | `chase.empty.noSeedsBody` | "A study needs a DOI, an OpenAlex id or a Semantic Scholar id; the list below says why each one cannot be chased." | REMOVED | X1 duplicates `chase.seeds.notChaseable.help` (D-CH5) and the list |
| D-CH18 | `chase.gate.label`, `gate.title`, `gate.body`, `gate.accept`, `gate.accepting`, `gate.offline`, `gate.running` | "Send these {new} works to screening as round {round}." | STAYS | V6 the one gate; main action "Send these {new} works to screening" |
| D-CH19 | `chase.gate.record` | "The accept is recorded with the time and the snapshot fingerprint." | HINT | T4; the accepted card shows both (`chase.accepted.at`, `accepted.id`) |
| D-CH20 | `chase.accepted.*`, `chase.notPublished.*`, `chase.status.*`, `chase.stale`, `chase.run.*` | "Round {round} corpus", "Publish the screening first." | STAYS | V1/V5 |

### Query workbench (phase 0 step 5, and Plan's "Change the search"; M11a)
Spec `docs/ux/phase0-inception/final/10-query-workbench.md` (and `docs/ux/phase1-discovery/final/10-plan-amend-search.md`). Keys in `lib/workbench-copy.ts`; the size line reuses the `estimate.*` keys of D-P rows. Written with the build (M11a part C, 2026-11-21); the wording waits for the researcher's read (decision 2026-11-21, item 4).

| Id | Copy key | Text (en) | Decision | Reason |
| :-- | :-- | :-- | :-- | :-- |
| W-B1 | `workbench.title`, `workbench.queryKey`, `workbench.written`, `workbench.op.and`, `workbench.op.or`, `workbench.databases`, `workbench.pool.none`, `workbench.term.inPool` | "Search" | STAYS | V7/V4 the block's heading, the query's key, the operators and the first-search counts on each term |
| W-B2 | `workbench.concept.label`, `workbench.concept.remove`, `workbench.concept.select`, `workbench.concept.merge`, `workbench.concept.mergeName`, `workbench.concept.mergeDo`, `workbench.concept.cancel`, `workbench.concept.add`, `workbench.concept.newName`, `workbench.term.add`, `workbench.term.addButton`, `workbench.term.remove`, `workbench.term.split`, `workbench.term.splitShort`, `workbench.tools.concept`, `workbench.topic.add` | "Concept {n}" | STAYS | V7 field labels and the concept and term actions (rename, merge, split, add, remove) |
| W-B3 | `workbench.concept.mergeNameHelp` | "The name is one of its terms: in the protocol a concept's name is searched too." | HINT | T3 definition: why the merged name is one of its terms |
| W-B4 | `workbench.count`, `workbench.counting`, `workbench.use`, `workbench.discard`, `workbench.cost`, `workbench.cost.cached`, `workbench.cost.part`, `workbench.cost.reading`, `workbench.needConcept`, `workbench.oneConcept`, `workbench.used`, `workbench.unused`, `workbench.offline`, `workbench.asOf` | "Count" | STAYS | V6/V3 the decision bar and its cost line: what one Count sends, stated before it is sent |
| W-B5 | `workbench.leave`, `workbench.leave.use`, `workbench.leave.leave` | "You have a version you have not used. Use it, or leave it?" | STAYS | V6 the one question before leaving a version not used |
| W-B6 | `workbench.keys` | "J and K move, A applies, R rejects, Ctrl+Enter runs the main action." | HINT | T1 how-to: the keys, each with a visible button |
| W-B7 | `workbench.announce.counting`, `workbench.announce.counted`, `workbench.announce.added`, `workbench.announce.merged`, `workbench.announce.split` | "Counting {n} requests." | STAYS | V3 the live region's words (announced, not drawn) |
| W-C1 | `workbench.section.counts`, `workbench.caption`, `workbench.col.database`, `workbench.col.query`, `workbench.col.without`, `workbench.cell.gain`, `workbench.cell.gainNoRatio`, `workbench.cell.gainSpoken`, `workbench.largest`, `workbench.string.show`, `workbench.badge.previous`, `workbench.empty`, `workbench.cell.state` | "Counts" | STAYS | V4 the counts table: caption, headings, cells, the largest effect in words, the exact string |
| W-C2 | `workbench.note` | "Without '{concept}', {database} finds {n} records instead of {m}. Read a few of them befor…" | STAYS | V2 the note on a concept whose absence at least doubles a count; never says to drop it |
| W-C3 | `workbench.row.counting`, `workbench.row.counted`, `workbench.row.cached`, `workbench.row.upperBound`, `workbench.row.stale`, `workbench.row.quota`, `workbench.row.quota.none`, `workbench.row.budget`, `workbench.row.busy`, `workbench.row.refused`, `workbench.row.unavailable`, `workbench.row.timeout`, `workbench.row.failed`, `workbench.row.keyMissing`, `workbench.row.crossref`, `workbench.row.crossrefCounted`, `workbench.row.notCountable`, `workbench.row.notAsked`, `workbench.row.toCount`, `workbench.row.stopped`, `workbench.state.rate_limited`, `workbench.state.refused`, `workbench.state.unavailable`, `workbench.state.timeout`, `workbench.state.quota_used_up`, `workbench.state.budget_spent`, `workbench.state.key_missing`, `workbench.state.not_countable`, `workbench.state.failed`, `workbench.state.to_count`, `workbench.crossref.anyway`, `workbench.span`, `workbench.today`, `workbench.onDay`, `workbench.budget.low` | "Counting…" | STAYS | V2/V3 each row state in words (counted, cached, used-up quota, budget, busy, refused, Crossref) |
| W-C4 | `workbench.err.invalid`, `workbench.err.jobActive`, `workbench.err.mailto`, `workbench.err.key`, `workbench.err.conflict`, `workbench.err.state`, `workbench.err.other`, `workbench.err.checkAgain`, `workbench.cmp.err.format`, `workbench.cmp.err.size`, `workbench.cmp.err.count` | "This version cannot be searched: {error}." | STAYS | V2 refusals and their words |
| W-C5 | `workbench.syn.button`, `workbench.syn.database`, `workbench.syn.cost`, `workbench.syn.cost.cached`, `workbench.syn.confirm`, `workbench.syn.add`, `workbench.syn.none`, `workbench.syn.title`, `workbench.removed.button`, `workbench.removed.cost`, `workbench.removed.absent`, `workbench.removed.title`, `workbench.removed.none` | "What does each synonym add?" | STAYS | V4/V7 what each synonym adds and what a concept removes, each with its cost |
| W-C6 | `workbench.versions.last`, `workbench.versions.now`, `workbench.versions.label`, `workbench.versions.notCounted` | "Last counted" | STAYS | V4 the last counted version beside this one |
| W-S1 | `workbench.suggest.label`, `workbench.suggest.source.pool`, `workbench.suggest.source.comparison`, `workbench.suggest.source.seed`, `workbench.suggest.source.topic`, `workbench.suggest.apply`, `workbench.suggest.reject`, `workbench.suggest.applyTo`, `workbench.suggest.evidence.pool`, `workbench.suggest.evidence.cmp`, `workbench.suggest.more`, `workbench.suggest.addAs`, `workbench.suggest.chooseConcept` | "Suggested by {source} · not yet yours" | STAYS | V5 the one suggestion look: source, evidence, Apply and Reject |
| W-K1 | `workbench.seeds.title`, `workbench.seeds.summary`, `workbench.seeds.summary.none`, `workbench.seeds.found`, `workbench.seeds.lacks`, `workbench.seeds.notRead`, `workbench.seeds.missed`, `workbench.seeds.missed.why`, `workbench.seeds.db.found`, `workbench.seeds.db.notFound`, `workbench.seeds.db.notChecked`, `workbench.seeds.db.switchOff`, `workbench.seeds.none`, `workbench.seeds.check`, `workbench.seeds.lookup`, `workbench.seeds.notReadAll`, `workbench.seeds.add`, `workbench.seeds.addButton`, `workbench.seeds.full`, `workbench.seeds.warn.all`, `workbench.seeds.warn.concept`, `workbench.seeds.warn.few` | "Known papers" | STAYS | V2/V4 the known papers: per paper the concepts found or lacking, the warning, what is not checked here |
| W-K2 | `workbench.seeds.measure` | "By the words of their titles and abstracts; databases also match keywords and word forms." | HINT | T3 definition: the measure is by words, a lower bound |
| W-M1 | `workbench.cmp.title`, `workbench.cmp.summary`, `workbench.cmp.summary.staged`, `workbench.cmp.summary.none`, `workbench.cmp.empty`, `workbench.cmp.add`, `workbench.cmp.file`, `workbench.cmp.database`, `workbench.cmp.string`, `workbench.cmp.date`, `workbench.cmp.stage`, `workbench.cmp.staged`, `workbench.cmp.remove`, `workbench.cmp.compare`, `workbench.cmp.measureChoice`, `workbench.cmp.report`, `workbench.cmp.none`, `workbench.cmp.measure`, `workbench.cmp.measure.harvest`, `workbench.cmp.measure.openalex`, `workbench.cmp.measure.words`, `workbench.cmp.measure.openalex.use`, `workbench.cmp.measure.openalex.cost`, `workbench.cmp.measure.openalex.off`, `workbench.cmp.notInDatabase`, `workbench.cmp.noDoi`, `workbench.cmp.noAbstract`, `workbench.cmp.missing`, `workbench.cmp.missing.lacks`, `workbench.cmp.page`, `workbench.cmp.prev`, `workbench.cmp.next`, `workbench.cmp.terms`, `workbench.cmp.terms.none`, `workbench.cmp.stale` | "Compare with an export" | STAYS | V4/V2 the comparison set, its report line, its measure in words, the missing records and terms |
| W-M2 | `workbench.cmp.measure.words.help` | "This finds a query that is too narrow. It cannot find a database's gaps, such as a missing…" | HINT | T3 definition: what the words measure can and cannot find |
| W-X1 | `workbench.external.title`, `workbench.external.check` | "Your query for other databases, to copy" | STAYS | V2 the strings for other databases, marked to check there |

### Screening (phase 2): Triage marks (M8b-triage-highlights, 2026-11-21), not counted yet
Triage has not adopted this audit (no Screening screen is in `tests/guidance-screens.tsx`, and the counts below are of `I-` and `D-` rows only). The test reads these `S-` rows against `triage-copy` so a hint's key is checked (`guidance.never-hidden.test.tsx`), but does not count them. They list every sentence M8b adds (`apps/research-ui/lib/triage-copy.ts`, keys `marks.*`; spec `docs/ux/phase2-screening/final/03-triage-desktop.md`, M8b point 9). When Screening adopts the audit, they join the count.

| ID | Keys | Sentence (en) | Decision | Reason |
| :-- | :-- | :-- | :-- | :-- |
| S-TM1 | `marks.region`, `marks.terms.switch`, `marks.quotes.switch` | "Search terms", "Agent's quotes" (group "Marks in the record") | STAYS | controls the researcher acts on |
| S-TM2 | `marks.legend.title`, `marks.legend.summary`, `marks.legend.mentions`, `marks.legend.absent`, `marks.legend.item`, `marks.legend.other` | "Search terms in this record · Mentions {n} of {m} concepts"; "{name}: {n} mentions" or "not in this record" | STAYS | V4 the legend is the result: which concept is missing |
| S-TM3 | `marks.hint.label`, `marks.hint.text` | "Marks show whole words and phrases from your search concepts …" | HINT | T1 the matching rule is explanation, one tap away |
| S-TM4 | `marks.noConcepts` | "The protocol has no search concepts." | STAYS | V3 says why there is no legend |
| S-TM5 | `marks.quote.suffix` | "agent's quote for {id} ({answer})" (in the quote's accessible name only) | STAYS | names the tie for assistive technology; not shown as text |
| S-TM6 | `marks.quote.show` | "Show in the text" | STAYS | an action |
| S-TM7 | `marks.quote.notFound` | "Not found at its place in the record, so it is not marked." | STAYS | V3 says why a quote is not marked |


### Counts per decision
(Counted by the test `guidance.audit.test.tsx` from the tables above.)

| Phase | STAYS | HINT | REMOVED | Total blocks |
| :-- | --: | --: | --: | --: |
| Inception 01 to 07 (shared frame included) | 107 | 35 | 11 | 153 |
| Discovery 01 to 09 (shared included) | 115 | 35 | 16 | 166 |
| Query workbench (M11a) | 15 | 4 | 0 | 19 |

A "block" is a row: one sentence or one group of keys that share a decision and a reason (for example `harvest.col.*`). Sentences of one key with different decisions are separate rows. The test derives the same counts by counting rows with prefix `I-`, `D-` and `W-` (the query workbench, M11a) per decision.

Recounted on 2026-11-18 after M10a and M3i merged, by counting rows (`grep -cE "^\| D-[A-Z0-9]+ \|.*\| STAYS \|"` and the same for `I-`, `HINT` and `REMOVED`): Explore (I-E6 reworded; I-E37 to I-E43 added), Harvest (D-H13 reworded; D-H17 to D-H23 added), Plan (D-P17 to D-P20 added: M10a's database picker and "Continue to Harvest with this choice"), Hand-off (D-HO14 to D-HO16 added: M3i's Not ready state) and the shared overview (D-DS13 gains M3i's `overview.harvest.unfinished`). Chase gained one key, M10a's `chase.leg.zero` "0 results", which falls under `chase.leg.*` in D-CH14, so no row was added. Scope and Direction have no key changed since `a0191cc6` and keep their rows. M10d recounts every screen it lightens, from the rendered DOM. Before the recount: inception 92 / 31 / 11 (134), discovery 84 / 31 / 15 (130). H-quota-hang (2026-11-20) added D-H26 (STAYS) and D-H27 (HINT) for the `incomplete` preparation state and put `pending.incomplete` in D-HO14: discovery 99 / 34 / 15 (148) became 100 / 35 / 15 (150). M3f-combined-corpus (2026-11-20) added seven STAYS rows (D-DS17, D-I9, D-HO17, D-HO18, D-HO19, D-RP19, D-RP20) and reworded four (D-P8 stays REMOVED, D-H12 STAYS, D-I7 STAYS, D-I8 HINT): discovery 100 / 35 / 15 (150) became 107 / 35 / 15 (157), recounted with the same `grep -cE` commands. Inception is unchanged. H-run-small-fixes Part B (2026-11-20) added D-P22 (STAYS) for the Crossref warning and the default-choice line: 107 / 35 / 15 (157) became 108 / 35 / 15 (158). M11a part D (2026-11-21) added D-P23 to D-P30 for "Change the search" on Plan (seven STAYS, one HINT): 115 / 36 / 15 (166); its review round 1 moved D-DS8 (`amend.help`) to REMOVED: 115 / 35 / 16 (166).

### Per-screen header and action check
| Screen | Lede after the audit (one sentence) | Main action (the one brand button) | Other actions |
| :-- | :-- | :-- | :-- |
| inception 01 Scope | "The topic, years and languages set the review window." | Continue to Explore | Save draft and exit (quiet) |
| 02 Explore | "The schools, topics and papers below are what the later steps draw on." | Search the literature, then See {n} directions | Refresh pool, Change scope (secondary/quiet) |
| 03 Direction | "These directions come from phrases that occur in the titles or abstracts of at least two papers of your pool." | Pursue {direction}, then Continue to Shape | Write my own, Search again narrower, Continue without a direction (quiet) |
| 04 Shape | "Choosing a lens marks the playbook that matches it and offers a first research question; you choose the playbook, and the question stays a draft until you use it." | Continue to concepts and criteria | Back to Direction, Use this draft (secondary) |
| 05 Criteria | "A criterion the wizard wrote stays out of the protocol until you accept it." | Continue to review | Accept/Reject on each criterion are decision controls, not brand buttons |
| 06 Review | "This is what will be written." | Create the workspace (the gate) | Check the protocol (secondary) |
| 07 Done | "Next, open the workspace and import your search results." | Open the workspace | Start another review, All workspaces (quiet) |
| discovery entry | none (title only) | Continue at {step} (until the what's-next bar) | step links |
| 01 Plan | "The question comes from the frozen protocol." | Continue to Recall | Copy all executed strings, Continue to Harvest with this choice, Reset to the protocol |
| 02 Recall | "Each seed is looked up and compared by title first." | Check these seeds, then Continue to Harvest | Cancel the check |
| 03 Harvest | "Each database receives the string shown on the plan." | Start the harvest | Stop the harvest and keep what was fetched (secondary) |
| 04 Import | none added by discovery | the screen 11 accept | Back to discovery, Go to the hand-off |
| 05 Duplicates | "The harness merged records that are the same work by three rules." | Continue to the report | Back to Harvest |
| 06 Report | none (the title says it) | I reviewed this text while unreviewed, then Continue to hand-off | Copy, Save as draft |
| 08 Hand-off | "Accepting freezes a corpus snapshot with its own fingerprint." | Accept this corpus (the gate) | Search again, Read the report, Stage an export; in the Not ready state the one action is Finish preparing this corpus on Harvest (or Follow the harvest) |
| 09 Chase | "The chase asks OpenAlex and Semantic Scholar which works cite your included studies and which works they cite." | Chase citations, then Send these {new} works to screening | Stop the chase |

## States
These rules are a pattern, so each state describes the pattern, not a screen.
- **Default**: hints closed; disclosures closed; at most the B1 to B6 budget visible; recommended badges present only where the engine has a reason.
- **Empty**: a label whose hint text is empty or missing renders no button (never an empty popover); a card with nothing to hide renders no Details; no Recommended badge appears when the engine proposed nothing.
- **Loading** (skeleton): no hint button and no Recommended badge in a skeleton; they appear with their content. A hint whose body needs a value (`{value}`, `{ceiling}`) renders after the value loads.
- **Error** (typed refusal): refusals are never inside a hint. The refusal card stays in its role colour with sentence, affects line and next step, code in Details. A hint beside a failing field remains available but never replaces the field's error text (`scope.yearInvalid` stays visible).
- **Partial**: a partial result keeps its warning visible (`explore.pool.partial`, `harvest.leg.capped`); a collapsed section's summary carries the failing count. A hint body with a placeholder that has no value shows "Not stored" rather than a blank.
- **Offline**: hints and disclosures are local copy and work offline; the screens' own "needs the engine on this computer" statements stay visible.
- **Stale / protocol changed**: a hint with a placeholder re-renders from the same data as its screen and never caches; the stale and protocol-changed warnings (`explore.stale.*`, `plan.changed`, `harvest.changed`, `handoff.gate.protocolChanged`) stay visible. A Recommended mark is removed when the check that proposed it is no longer true.

## Desktop layout
No board. Placement rules: the hint button follows the label text on the same line (inline-end of the label); for a card heading, it follows the heading; for a table column heading, it sits at the inline-end of the heading cell; the Recommended badge sits at the inline-end of the option's title line, followed by its hint button. The panel opens on the inline-end side of the button, below as a fallback. Regions and order of each screen are unchanged from its own spec.

## Mobile layout (≤ 640 px)
Inception and discovery are desktop-only on the engine (a real phone shows the desktop pointer card), but a narrow desktop window (plan §4: breakpoints 640 and 1024 px) uses one column. There: the hint hit area is 44 x 44 px, tap toggles, there is no hover and no gesture; the panel is placed below the button and spans the content width minus `space-4` on each side; opening a hint closes the others; a tap outside closes it; collapsed sections have 44 px summaries. Phone screening screens (04, 07) are outside this spec and use no hints.

## Keyboard
- `Tab` reaches the hint button right after its label (DOM order: label, hint button, field). `Enter` or `Space` opens or closes it. `Escape` closes the open hint (focus stays on, or returns to, the button). `Tab` away closes it.
- No new shortcut key. A disclosure summary is reachable by `Tab` and toggles by `Enter` or `Space` (spec 12).
- Focus ring: the existing 2 px `brand` ring, offset 2 px, on the button and the summary.
- Focus order of a screen is unchanged by moving text into hints: the hint button adds one tab stop per hint, at most 6 per screen (B4).

## Copy
New keys, en master (`guidance.*` in a new `lib/guidance-copy.ts`; fr and ar fall back to en until translated, plan §7; `guidance.hint.open` and `guidance.recommended` are translated from the start):
| Key | en |
| :-- | :-- |
| `guidance.hint.open` | About {label} |
| `guidance.hint.close` | Close |
| `guidance.recommended` | Recommended |
| `guidance.recommended.by` | Recommended · {source} |
| `guidance.recommended.source.wordScan` | word scan of your topic |
| `guidance.recommended.source.poolHealth` | pool size check |
| `guidance.recommended.source.check` | check {id} |
| `guidance.recommended.source.import` | imported protocol |
| `guidance.recommended.source.estimate` | size estimate (added in M10d: the suggested cap of the size estimate) |
| `guidance.recommended.source.lens` | matches your lens (added in M10d: the playbook that matches the lens) |
| `guidance.section.count` | {title} · {n} |
| `guidance.section.failed` | {n} failed |
| `guidance.section.zero` | {n} found nothing (added in M10d: databases that answered with nothing, named in the summary of the Databases asked fold) |
| `guidance.notStored` | Not stored |

Every moved block keeps its existing key as the hint body (the Audit table's "Copy key" column is the list). The labels for hint buttons come from the label they sit beside (`guidance.hint.open` with `{label}`). No literal `aria-label`, `title`, `alt` or `placeholder` (N9 guard). Voice: a hint body is a plain sentence in the researcher's words; it never says "AI".

## Accessibility
- **Contrast.** Panel text `ink` on `surface` (4.5:1 in both themes, `tokens.json`); the glyph `ink-muted` on `surface` (4.5:1 per tokens); open state `surface-raised` fill plus the `aria-expanded` state, not colour alone; focus ring `brand` 2 px. The Recommended badge is `ink` on `surface-raised` with a dashed `ink-muted` border and a word; it passes 4.5:1 and does not rely on colour.
- **Right-to-left (ar).** The hint button follows the label on its inline-end side and the panel opens on the inline-end side (the physical left), with logical flipping when there is no room; text in the panel is `dir="auto"`; any number, DOI or code quoted in a body stays `dir="ltr"` and numerals stay Latin; the info glyph does not mirror (it is symmetric), the disclosure chevron does (spec 12).
- **Screen readers.** The button announces "About {label}, button, collapsed/expanded"; the field's `aria-describedby` points at the hint text so it is read with the field without opening anything; the panel is a plain element with `role="note"` (not `tooltip`, not `dialog`); a Recommended badge reads "Recommended, {source}" before the option's name is finished; a collapsed section reads "{title}, {n}, collapsed" and its failing badge is inside the summary.
- **Reduced motion.** No animation on open or close.

## Acceptance tests
Vitest (`apps/research-ui/tests/`):
- `hint.test.tsx`: the trigger is a `<button type="button">` with `aria-expanded`, `aria-controls`, a name from `guidance.hint.open`; click and `Enter`/`Space` toggle; `Escape` closes and `document.activeElement` is the button; a pointer event of type `touch` toggles it (no hover handler is needed); opening a second hint closes the first; the body is in the DOM while closed; the component accepts a copy key and renders no markup from the body; a missing key renders no button; the button is outside any `<label>`.
- `hint.rtl.test.tsx`: with `dir="rtl"` the first-choice placement is the physical left; the panel text is `dir="auto"`; quoted DOIs stay `dir="ltr"`.
- `guidance.audit.test.tsx`: a fixture of the Audit table (screen, key, decision, in `tests/`) is checked against the rendered screens: every key marked HINT is inside `[data-hint-body]` and never in the visible flow; every key marked STAYS is outside any `[data-hint-body]`; every key marked REMOVED is absent from the DOM; a key that exists in the catalogs but not in the fixture fails the test (so M10a's amendments cannot slip in unaudited).
- `guidance.never-hidden.test.tsx` (**a warning is never inside a hint**): for every screen and state fixture, no element matching `[role="alert"]`, `[data-state]` (StateCard), `[data-role="blocked"]`, `[data-role="unclear"]`, `[data-check]`, `[data-provenance]`, `[data-gate]` has a `[data-hint-body]` ancestor; a static check fails the build if any key of `screening-states.ts`, or any key listed as V1/V2/V3/V5/V6 in the audit fixture, is passed as a hint's `textKey`.
- `density.budget.test.tsx`: for each audited screen with a fixture in its default state, hints closed: one `[data-copy="lede"]` of one sentence and at most 130 characters; at most 4 `[data-card]` outside collapsed sections; at most one `[data-copy="caption"]` per card; zero inline-help paragraphs under fields; at most 6 hint buttons; exactly one `button[data-variant="primary"]`; at most one dashed-brand gate.
- `recommended.test.tsx`: a Recommended badge carries its source in visible text; no option in a group with a badge is checked, ticked, filled or focused on load; the order of options equals the engine's order; the main action is disabled until a choice is made; a badge with no source is not rendered.
- `details.rule.test.tsx` (existing, spec 12) gains: a collapsed secondary card shows its title and count in its summary and a role badge with a word when it holds a failing item.
- `copy` parity: `guidance-copy.test.ts` (keys and `{placeholders}` in en, fr, ar; N9 guard).

Playwright (`tests-browser/guidance.spec.ts`):
- `hint opens on click and on touch tap, closes on Escape and returns focus to its button` (chromium; WebKit mobile emulation for the tap).
- `hint placement mirrors in Arabic` (the panel opens to the physical left of the button; no clipping inside a card with `overflow`).
- `a warning is never inside a hint`: drive Explore with a thin pool, Harvest with a capped database, Review with an existing workspace; open every hint on the page; assert each warning, refusal, check result and gate is visible and has no `[data-hint-body]` ancestor, and that closing all hints leaves them visible.
- `explanatory text is in the DOM while its hint is closed`: the moved keys are found by locator with `state: "attached"`; they are not visible until opened (parity with spec 12 rule 5).
- `density budget per screen`: for every audited route (inception 01 to 07, discovery entry and 01 to 06, 08, 09) the counts of B1 to B6.
- `recommended is never preselected`: Shape (no lens checked when the word scan leans), Explore thin pool (semantic radio unchecked), the main button disabled until the researcher chooses.
- `hints work without a mouse`: the whole Scope and Shape forms are completed with the keyboard and every hint is opened and closed by keyboard alone.
- `rendered axe on every amended screen in en and ar, light and dark` (`tests-browser/rendered-axe.spec.ts`): includes open hints and collapsed sections.
- The existing provenance checks keep passing with at most one added step per moved value (`await hint.click()` or `await details.click()`).

## Open questions
None.

Closed by the researcher on 2026-11-15 (record: `docs/roadmap/milestones/M10b-proposals-checks.md`, R8 and "Adopted from the writers' recommendations"):
1. Two exceptions to the brand book are allowed: the hint button is an icon-only control named by its `aria-label`, and "Recommended" uses the neutral dashed badge. They are recorded as one `docs/decisions.md` entry (written when M10a's entries are merged, because that branch edits the file) and one line in the brand book's Iconography section, added with M10d's first slice.
2. The four limitations stay visible and are not moved behind a hint: `explore.pool.langNote`, `criteria.matrixCharting` (until M12a `criteria.matrixParked`), `criteria.verificationParked`, `plan.limits.cap.engine_ceiling`.
3. The fold plan of rule 4 is built for Explore and Review first, as M10d's first slice. The researcher looks at both with real data before Criteria, Harvest, Report and Chase are folded; those four keep their current layout until then.
4. On Report, "I reviewed this text" is the one brand button while the methods text is unreviewed, and "Continue to hand-off" becomes the brand button after; the researcher can still continue earlier through a secondary link.
5. The density numbers B1 to B6 are the starting budget enforced by `density.budget.test.tsx`; they change only by editing this spec and the test together, after Explore has been tried. `overview.continue` and the second sentence of `done.lede` stay until the what's-next bar of `04-next-step` is built.
