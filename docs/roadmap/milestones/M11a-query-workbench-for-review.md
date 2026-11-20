# M11a Query workbench: for your review

Date: 2026-11-20 · Status: **questions answered** (the researcher accepted all ten recommendations on 2026-11-20 and approved the specification for building; build not started) · Full record: [`M11a-query-workbench.md`](M11a-query-workbench.md) · Screens (drafts): `docs/ux/phase0-inception/final/10-query-workbench.md`, `docs/ux/phase1-discovery/final/10-plan-amend-search.md`

## What you will be able to do

At Inception's step 5, while you type concepts and synonyms, you can press **Count** and see, for each database, how many records your query finds, and how many it would find with each concept left out. You can ask what each synonym adds, read a page of the papers a concept removes, and merge two concepts in one click. You see whether your known papers can actually test the query, and you can drop in a Scopus or Web of Science export to see which of its records your query misses and which words those records use. Nothing is counted until you press the button, and every button says how many requests it will send. After the protocol is created, the same tool opens from Discovery's Plan, and a change is recorded as an amendment with your reason.

## Your review, replayed

Step 5, your four concepts: UAV, multispectral, weed, segmentation. You press Count.

| | Your query | without UAV | without multispectral | without weed | without segmentation |
| :-- | --: | --: | --: | --: | --: |
| OpenAlex | 166 | ? | ? | ? | ? |
| Semantic Scholar | 107 | ? | ? | ? | ? |
| arXiv | at most 7 | ? | ? | ? | ? |
| Crossref | not counted: it cannot combine concepts with AND (it said 6,221 for any of the words) | | | | |

The "?" are the numbers nobody measured on 2026-11-20. Scopus, measured by hand afterwards, showed the pattern: 130 strict, 236 without UAV, 512 without multispectral. If OpenAlex shows the same, a note appears on "multispectral": "Without 'multispectral', OpenAlex finds … records instead of 166. Read a few of them before deciding whether they belong." You read the page of titles it removes, select UAV and multispectral, press **Merge**, and Count again: **166 becomes 781**, side by side.

The seed panel says: **4 of 4** known papers use a term of every concept, "so they cannot show a paper this query misses". It suggests adding a known paper that does not say "multispectral", or comparing with an export.

You drop in the Scopus export. On Plan, after a harvest, it reads: **"31 of 130 Scopus records are missing from what your query finds"**, lists the 31 titles, and the words they share that your query lacks, each with "Add as synonym". Before a harvest, the same report compares the export with the query's words and, if you allow it, with OpenAlex (one request per 50 records).

None of this would have changed the frozen protocol by itself: you decide, and "Use this version" saves it in the draft.

## Questions (the first three touch an accepted decision or the files a workspace gets)

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| 1 | After the protocol is created, may you **remove, rename or merge** concepts from Plan? Today an amendment can only add a concept or a synonym (M10c, accepted item 16), and only an assistant can propose one. | Yes: a researcher's amendment replaces the whole concept list, with a required reason, through the same recorded path. As today, a harvest made before it can no longer become the corpus (you harvest again; adding only the difference is M3j). | Changes an accepted decision; one new route; part D is RELEASE. |
| 2 | The agreed order says the redesign's **Explore and Direction part becomes the workbench**. Should M11a also rebuild Explore and Direction in direction A, with A's frame? | No: M11a builds the workbench as A's concepts block and evidence column inside today's step 5. The frame and the Explore/Direction relayout go with M11b (or a row of their own). | Keeps M11a near M10b's size; Explore and Direction stay as they are for longer. |
| 3 | Should the **search development** (versions tried, counts, seed checks, comparison sets) go into every new workspace at Create, under `audit/query_development/`? | Yes: it is what a methods section reports ("developed over 7 versions") and what you would otherwise write down by hand. | One more folder per workspace; the preview's file list changes (part B is RELEASE). |
| 4 | A **daily request budget** per database for counting, shared by all your reviews: OpenAlex 200, Semantic Scholar 100, arXiv 100, PubMed 100, Crossref 20. | Yes, as a safety net for the harvest's quota; adjust after your first real session. | You may hit it on a heavy day; cached counts still show. |
| 5 | Count only when you press **Count**, never while typing? | Yes. | One click per try. |
| 6 | The note on a concept appears when leaving it out **at least doubles** a count. | ×2. | Nothing; a constant. |
| 7 | **Crossref** not counted by default for two or more concepts (count anyway on request), and never in the drop test or comparisons. | Yes, the same rule H-run-small-fixes applies to the harvest. | Crossref's real matches are not shown unless asked. |
| 8 | The "by the words" check uses whole words, as directions do. Should the workbench's own matcher also treat **plurals** ("weed", "weeds") as one word? | Yes, English plural only, in the workbench; the direction rule (INC-21) stays as accepted. | Two matchers to keep apart. |
| 9 | **OpenAlex only** for the per-database seed and comparison checks (one request per 50 records), behind a switch until tried live. | Yes. | Semantic Scholar and arXiv say "not checked here"; the recall check on Plan still covers them. |
| 10 | Show your query **translated for Scopus and Web of Science** (TITLE-ABS-KEY, TS=) to copy, so the export you compare with uses the same search? | Yes, in the Inception screen; marked "check it in the database". | Small; the strings are not tested against those databases. |

What I could not check without a live run: whether OpenAlex and Semantic Scholar show the dropped-concept pattern Scopus showed; whether OpenAlex answers a seed check in one request; how many requests a real session sends. The record lists the rest.
