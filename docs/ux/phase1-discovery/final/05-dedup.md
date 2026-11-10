# 05 Duplicates    Status: FINAL | Phase 1 Discovery | Route `/[locale]/discovery/dedup` (desktop only) | Milestone M3c-screens (counts only; the near-twin pair review is M3e)

Boards: `Dedup` (D5, `docs/ux/phase1-discovery/final/project/Dedup.dc.html`), `MobileDedup` (`.../MobileDedup.dc.html`). Contract/packet: `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.5 (Stage 1 only), §6 decision 2; `docs/roadmap/milestones/M3d-engine.md` decisions 9-11. Code: `src/scholar_harness/console/api/discovery.py:516` (`dedup_counts`), `:494-511` (`_dedup_summary`). Decisions: `docs/decisions.md` 2026-11-10 "Discovery over HTTP: seven decisions" (2). Brand: `docs/ux/brand/BRAND_BOOK.md`, `docs/ux/brand/tokens.json`. Shared rules (step bar, `?console=`, run selector, SSE, refusal copy, hard rules): see 01-plan.md, Shared.

**Purpose.** See how many records the harness merged as duplicates, by which rule and with which parameters, before the report and the hand-off.

**Changed from the canvas.** Every cut or change:
- **The near-twin pair review is cut: "M3e, RELEASE".** The queue "Near-twins 14", the filter chips (To decide, Decided), the pair card (Record A, Record B, highlighted differences, "Why the tiers did not merge"), the keys M, K and S, the buttons "Merge, keep B as the record", "Keep both" and "Skip for now", the "Decided · journaled" table (`you · HUMAN · time · sha256`) and its Undo, the progress bar "2 of 14 decided", and `MobileDedup` (the whole phone pair card with Keep both and Merge). Packet decision 2: the pair review changes what the snapshot is built from (Packet B inputs), so it is its own RELEASE-lane milestone, decided after the researcher's own corpora show how many near-twins survive. `GET /discovery/dedup` answers `near_twins: null` (`discovery.py:511`). Honest state shown instead: counts per rule, and one line saying that pairs the rules did not prove are not listed and stay separate works (open question 1).
- **No merge, keep or undo control and no HUMAN decision is recorded.** The screen has no write call. The board's journal claim "journaled as DEDUPLICATION" is dropped: no route returns the journal row, so the screen does not say it.
- **The gate "Confirm 3,241 works" and "Save decisions and come back later" are cut.** The corpus is frozen only by the accept on the hand-off screen (08; decision 2026-11-10 "A browser harvest does not freeze the corpus; the hand-off screen does"). This screen has no brand button; its one forward link, "Continue to the report", is a secondary link (one brand button per screen, and there is no action here that needs one).
- **Headline "3,506 records became 3,241 works. Are these 14 pairs the same paper?"** becomes a count sentence built from `unique_works` and `input_records` exactly as written ("{input} records became {unique} works."). The browser adds no figure.
- **Tier captions.** "DOI, arXiv id, PMID or OpenAlex id" and "a conflicting id blocks the merge" are not fields of the answer, so they are cut. Captions come from `method` (the fuzzy tier prints the engine's own `title_similarity`, `year_tolerance` and `first_author`).
- **"Removed in total 265 · 7.6%"**: `removed` and `removed_rate` as the harness wrote them (`removed_rate` is a fraction rounded to 4 places, `discovery.py` via `_dedup_summary`; the screen formats it as a percentage for reading and prints the written fraction under Details).
- **Run.** The screen describes the newest deduplication (the `run` field of the answer); `GET /discovery/dedup` takes no run parameter. The shared run selector is shown read-only here and a mismatch with `?run=` is stated (see Default).
- **App-bar phase ladder** ("Not production", Inception to Trust) is the shell's, not this screen's; cut as on the inception specs.
- **Phone.** `MobileDedup` and the "Near-twins 12" tab of the phone tab bar are cut; discovery routes are not phone routes (see Mobile layout).

## Entry / exit
- Entry: the step bar (Plan, Recall, Harvest, Import, Dedup, Report, Hand-off); "Continue to deduplication" at the end of Harvest (03); a direct URL.
- Exit: "Continue to the report" goes to `/[locale]/discovery/report` (06) carrying `?console=` and the selected `?run=`. "Back to Harvest" goes to 03. No gate. The screen writes nothing.

## Data in
| Field | Source |
| :-- | :-- |
| `run` ("run_NNN": the run this deduplication belongs to) | `GET /api/v1/discovery/dedup` ✓ M3d-engine `discovery.py:516` |
| `input_records`, `unique_works`, `removed`, `removed_rate` | same |
| `tiers.identifier`, `tiers.exact_title`, `tiers.fuzzy_title` (records removed per rule; the three add up to `removed`, M3d-engine decision 9) | same |
| `method.title_similarity`, `method.year_tolerance`, `method.first_author`, `method.source` (`protocol` or `default`) | same |
| `near_twins` (always `null`) | same; not shown |
| the run list for the read-only selector and the stale marker | `GET /api/v1/discovery/runs` ✓ M3b-api `discovery.py:397` (shared, see 01-plan.md, Shared) |

The browser adds, subtracts or reconciles nothing; if the engine's numbers did not add up the screen would still print them as written.

## Data out
None. No write, no journal event. (The `DEDUPLICATION` journal row is written by the run, not by this screen.)

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/discovery/dedup` | ✓ M3d-engine `console/api/discovery.py:516` |
| `GET /api/v1/discovery/runs` | ✓ M3b-api `discovery.py:397` |
| `GET /api/v1/discovery/dedup/pairs`, `POST /api/v1/discovery/dedup/decisions` | ✗ M3e-neartwins (RELEASE); not called, not allowlisted |

Not in `_PHONE_ROUTES` (`serve.py:55`): a phone token gets `TOKEN_SCOPE_REFUSED` (403, `serve.py:230`).

## States
- **Default**: eyebrow "Step 5 of 7 · Duplicates"; Literata h1 "{input} records became {unique} works."; lede "The harness merged records that are the same work by three rules. The rules and their settings are below."; four count cards (Records in, Works left, Removed with the written rate, and the tiers as three rows: Same identifier, Same normalized title, Fuzzy title, each a number); card **The rules in force** ("Title similarity at least {title_similarity}", "Publication years at most {year_tolerance} apart", "Same first author: yes/no", "These values are {set in the signed protocol | the harness defaults}"); caption "This is the newest deduplication, from {run}." If `?run=` names another run: "You are viewing {selected}. Deduplication is shown for {run} only." The pairs note: "Records the rules did not prove to be the same work are not listed here and stay separate works." The forward link "Continue to the report". Counts and the rate are status-neutral text; no colour carries a count.
- **Empty** (`DEDUP_NOT_RUN`, 404): the StateCard stands for the screen (`pageHeading`): "No deduplication has run yet." Affects: this screen. Action: link "Go to Harvest". Caption: "A database export you staged is deduplicated when you accept it; its counts are on the hand-off." with a link to 08. This is also the answer for an import-only workspace (known P3, M3d-engine; the sentence above covers it without claiming a count). Not an error in the researcher's work; role `exclude`.
- **Loading** (skeleton): h1 area and four card skeletons, `aria-busy`; no number is shown before the read finishes.
- **Error** (typed refusal, `StateCard`): `PROTOCOL_MISSING` (409) and `PROTOCOL_INVALID` (422) cannot come from this route (it reads `clusters.json`, not the protocol) but the shell's workspace read can show them: shared card, see 01-plan.md, Shared. `DEDUP_NOT_RUN` as Empty. A malformed `clusters.json` also answers `DEDUP_NOT_RUN` (`discovery.py:494-496`), so a damaged file reads as "not run"; the card does not claim more. `ENGINE_UNREACHABLE` (client side of the proxy's `CONSOLE_UNREACHABLE` 502 or `CONSOLE_TIMEOUT` 504): the shared card with "Try again". `TOKEN_SCOPE_REFUSED` (403, phone): the desktop pointer card.
- **Partial**: `tiers` absent or `null` (the packet allows it for a deduplication written before E4a): the three rule rows show "Not recorded for this deduplication" in the `exclude` role and the totals stay; nothing is invented. A tier of 0 is shown as 0. A `removed` of 0 shows the rate as written ("0 %").
- **Offline**: the engine is local, so offline means unreachable. The last read stays with "As of {time}"; "Try again" is shown; nothing is queued.
- **Protocol-changed**: cannot occur on this screen. The answer carries no protocol fingerprint, so there is nothing to compare; the nearest case is that the `method.source` is `protocol` for a protocol that has since changed, which the Report and Hand-off screens catch (`PROTOCOL_CHANGED_SINCE_RUN` at the accept). The screen does not claim the method is current. **Stale run**: if the selected run is `stale`, the shared marker applies and this screen still shows the newest deduplication with the run named.

## Desktop layout
Source: `Dedup` (D5), reduced as listed. Regions: shell and step bar; eyebrow, h1, lede; count cards in a four-column grid (the board's `section aria-label="Merged by tier"`); **The rules in force** card; the note about unlisted pairs; the run caption; footer link row. The left near-twin list, the pair card, the decided table and the gate panel are cut, so the page is one column of cards. Existing tokens and components only: `card`, `label`, `title num`, `caption muted` from `docs/ux/brand/tokens.json`; no new component.

## Mobile layout (≤ 640 px)
Discovery routes are desktop-only on the engine (no discovery route is in `_PHONE_ROUTES`; plan §4, write and job screens are desktop only), so `MobileDedup` is cut and this serves a **narrow desktop window**: one column in this order: back link, eyebrow and h1, the four count cards stacked (each full width), the rules card, the notes, then the link "Continue to the report" as a 44 px full-width secondary button. A real phone (first read refused with `TOKEN_SCOPE_REFUSED`) shows one card `discovery.common.phone.desktopOnly` ("Discovery runs on your desktop. Open this page there.") with a 44 px link "Go to screening". The phone board's "Connected" badge, offline queue and decision buttons are not built.

## Keyboard
Focus order: skip link, shell, step bar (each step a link, current has `aria-current="step"`), h1, count cards (not focusable, read in order), the rules card, the run selector if shown, "Back to Harvest", "Continue to the report". The board's keys M, K and S are not built (no decision exists). After a refusal, focus moves to the card heading. No single-key shortcuts.

## Copy
Keys in the discovery copy file named in 01-plan.md (en master, then fr and ar by the implementer). No literal `aria-label`, `title`, `alt` or `placeholder` attributes (N9 guard).
- `discovery.dedup.eyebrow` "Step 5 of 7 · Duplicates"; `title` "{input} records became {unique} works."; `lede` "The harness merged records that are the same work by three rules. The rules and their settings are below."
- `discovery.dedup.in` "Records in"; `out` "Works left"; `removed` "Removed"; `rate` "Share removed"; `rateWritten` "Written by the harness as {fraction}"
- `discovery.dedup.tier.identifier` "Same identifier"; `tier.exactTitle` "Same normalized title"; `tier.fuzzyTitle` "Fuzzy title"; `tier.notRecorded` "Not recorded for this deduplication"
- `discovery.dedup.rules.title` "The rules in force"; `rules.similarity` "Title similarity at least {value}"; `rules.years` "Publication years at most {value} apart"; `rules.author` "Same first author: {yesNo}"; `rules.sourceProtocol` "These values are set in the signed protocol."; `rules.sourceDefault` "These values are the harness defaults."
- `discovery.dedup.run` "This is the newest deduplication, from {run}."; `runMismatch` "You are viewing {selected}. Deduplication is shown for {run} only."
- `discovery.dedup.pairsNote` "Records the rules did not prove to be the same work are not listed here and stay separate works."
- `discovery.dedup.next` "Continue to the report"; `back` "Back to Harvest"
- `discovery.dedup.empty.title` "No deduplication has run yet."; `empty.importNote` "A database export you staged is deduplicated when you accept it; its counts are on the hand-off."
- `discovery.common.phone.desktopOnly`, `discovery.common.asOf` "As of {time}" (shared, defined in 01-plan.md).
- Refusals: `discovery.states.<CODE>.{title,body,affects,action}` (07).

## Accessibility
- Contrast pairs from tokens: `ink` on `surface` for counts, `ink-muted` captions on `surface`; the "Not recorded" tag is `exclude` text with the words, never colour alone.
- Counts are real text in a `dl` or labelled cards, not an image; the board's `role="img"` bar is cut with the progress it showed. The h1 is the page heading; the count cards are a labelled `section`.
- Percentages and fractions are `dir="ltr"`, Latin digits in ar; run id mono and LTR. RTL (ar): the grid mirrors and the step bar order reverses.
- Targets 44 px; light and dark tokens; refusal cards use `role="alert"`.

## Acceptance tests
Vitest `apps/research-ui/tests/discovery-dedup.test.tsx`: the four cards print the answer's numbers verbatim and the page computes none (feed counts that do not add up and see them unchanged); `tiers` rows print per rule; `removed_rate` prints the written fraction under Details; `method.source` `protocol` and `default` give the two sentences; `near_twins` is not rendered and no merge, keep or undo control exists (`queryByRole('button')` finds only Retry-type actions); `DEDUP_NOT_RUN` shows the empty card with its code under Details and a link to Harvest; `tiers: null` shows "Not recorded"; `?run=` different from `run` prints the mismatch line; offline keeps the last read with "As of"; `ENGINE_UNREACHABLE` and `TOKEN_SCOPE_REFUSED` map to copy; `discovery-dedup.i18n` (keys in en; N9 guard); `discovery.live-only` (no Demonstration marker on `/discovery/*`).
Playwright `apps/research-ui/tests-browser/discovery.spec.ts` (this screen's part, stateful fake of the discovery API): default, empty, partial; RTL (ar) pass; axe in light and dark; no horizontal overflow at 375 and 1440 px; a phone-scoped token shows the desktop pointer.

## Questions closed by the researcher (2026-11-10: each recommended answer taken, "all recommended")
1. **The note about pairs the rules did not prove.** Because the near-twin pair review is not built, the screen says in one line: "Records the rules did not prove to be the same work are not listed here and stay separate works." The engine does not report how many such pairs exist, so the screen cannot say "none" or "some". Do you want that line on the screen, or no mention at all until the pair review exists? Recommended: keep the line, because a work counted twice can end up both included and excluded and you should know the rules are not the last word.
2. **Percent or fraction.** The harness writes the share removed as a fraction (for example 0.0756). The screen shows it as a percentage for reading and prints the written fraction under Details. Is that acceptable for your manuscript's PRISMA numbers? Recommended: yes; the written value stays visible and copyable.

## As built (M3c)
Built in `apps/research-ui/components/discovery-dedup.tsx` as written: counts verbatim, the share as a percentage with the written fraction under Details (answer 5), the pairs note (answer 4), no write. Not built: keeping the last read with "As of" while the engine is unreachable (the refusal card with Try again stands in).
