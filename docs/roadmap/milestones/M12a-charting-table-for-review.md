# M12a Charting table: for your review

Date: 2026-11-21 · Status: **draft, waiting for your answers; nothing built** · Full record: [`M12a-charting-table.md`](M12a-charting-table.md) · Screens (drafts): `docs/ux/phase3-extraction/final/01-charting-table.md`, `02-one-study.md` · Decisions: `docs/decisions.md`, "2026-11-21 — M12a charting table" (PROPOSED)

## What you will be able to do

After you publish screening, a new **Charting** step lists every record you kept: your Includes and your "Unclear → full text" records, from the database search and from a citation-chasing round, each marked with where it came from. In a **Full text** view you mark many records at once as To get, Requested, Retrieved or Not retrieved (with one reason), attach the PDF you downloaded or paste a link, and decide each one at full text: Include, or Exclude with exactly one reason. The app fetches nothing. In a **Charting** view you fill your two columns, one row per study still included, by keyboard. "Not reported" and "Not applicable" are values of their own, and each cell can have a note and a "where from" (page or quote). You try the form on about five studies, change the columns, and the change is recorded beside the protocol, which itself is never edited. Every change saves at once and can be undone with `Z`. You export a CSV, or a spreadsheet with the table, the full-text decisions, the PRISMA full-text counts, the form and its changes, and a methods paragraph you can adapt.

## Your review, as an illustration

*Illustration only: the values below were written from memory of the WeedMap paper (Sa et al., 2018, Remote Sensing) and are not checked against it.*

1. You publish screening. Charting opens with every kept record, your Includes (about 74) and your Unclear records, all "To get". The filter "To decide at full text" shows the Unclear ones first if you want them.
2. Full text view. You select the open-access papers you downloaded tonight (X, Shift+J), press R: "Mark 23 records as Retrieved?" Enter. You attach the WeedMap PDF with P. You press I on WeedMap: included at full text. On a paper that turns out to use only RGB images, E, then your exclusion criterion "RGB only" as the one reason: excluded, and counted for PRISMA.
3. Charting view, WeedMap:

| Column (as you typed it at Inception) | Value | Note / where from |
| :-- | :-- | :-- |
| Sensor problems addressed | **Not reported** | Two cameras are used, but no misregistration, missing band or change of camera is measured, corrected or simulated. Methods, dataset section (to check) |
| Cameras and evaluation design | RedEdge-M and Sequoia; one model per camera; no test on a camera absent from training; split by orthomosaic tiles | Methods (to check) |

4. After five studies the second column is clearly three questions. In the form you split it, with the reason "One value per question makes the table countable", into **Cameras** (text), **Test camera absent from training** (Yes/No) and **Data split** (one of: random tiles, by field, by date, by camera, not reported). The five charted cells are marked "Chart again" with their old text shown beside them. The amendment goes into the journal and into the exported methods paragraph: "The charting form was piloted on 5 studies and revised: …".
5. Export: the spreadsheet has your table and the counts "N reports sought, M not retrieved (reasons), K assessed, E excluded (reasons), I included", split by databases and citation chasing.

## Questions (the first three touch the contract, the protocol model or an accepted decision)

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| 1 | **Contract v1.** Are full-text decisions and charting cells typed Contract v1 artifacts now, or workspace records outside the contract (as the method amendments are), each bound to the protocol fingerprint and the published screening? | **Outside the contract for now**; a contract decision before an agent proposes cells or a second reviewer joins. | Now: about one more PR (models, schemas, golden fixtures, negative tests, an independent review) before the table. Later: the same work, then. |
| 2 | **Where the column types and options live.** The protocol's columns have a name, a description and a type, but no list of options. Keep the options (and Yes/No) in a charting form beside the protocol, or add them to the protocol model? | **Beside the protocol.** The protocol, its fingerprint and your screening stay untouched; column changes are recorded amendments. | In the protocol: a schema change, a moved fingerprint for every protocol with columns, and an amendment path that today refuses changes after the corpus is accepted. |
| 3 | **What this un-parks.** Plan §8 and the decision of 2026-11-20 (item 7) keep the Matrix "beyond the charting table" parked. Do the full-text status, the full-text decision and the hand-filled table become production (no parked banner), Inception's line "Parked: the Matrix phase…" become "These columns are filled on the Charting step", and everything else stay parked (PDF fetching and reading, the automatic matrix, synthesis, the graph, the trust score)? | **Yes.** | A wording change on Inception and its test; §8 gets a line saying what left it. |
| 4 | **Rows only after publication.** Publishing needs every batch decided and approved. Show the table only after publication, or also a read-only preview from your current decisions? | **Only after publication**: the counts then match the published screening. | You finish title and abstract screening first. The preview would be about half a part more, and its rows would move as you decide. |
| 5 | **Full-text screening here**, in its smallest form (Include, or Exclude with exactly one reason from your criteria or "Other"), one study at a time, with no approval step? | **Yes.** A milestone of its own would leave excluded papers in your table and the PRISMA full-text box empty. | Part A grows by one field, one reason list and the counts. A triage-like full-text screen with criteria and an agent is later. |
| 6 | **The app fetches nothing**: you attach your own PDF (kept in `pdfs/`, which is not in git) or paste a link. | **Yes.** The fetcher is parked and has a known defect (PDF-07); a wrong PDF attached silently is worse than none. | You download the PDFs yourself. Fetching, with a check of each file, could come in M12b. |
| 7 | **"Not applicable" as a value**, and charting allowed without a retrieved full text (the row marked "No full text" everywhere)? | **Yes to both.** | Small. The export and the methods text count rows charted from the abstract only. |
| 8 | **The spreadsheet file.** No xlsx library is installed today. Add `openpyxl` (pure Python) to the base install, or ship CSV only? | **Add it.** | A new dependency of the wheel (STANDARD-sized change inside part C). CSV only saves that, but you lose the extra sheets (counts, form, about). |
| 9 | **An agent proposing cells: later**, after full texts can be read with page anchors, a quote check over the full text like screening's, the highlighter from M8b, and a measurement on your own charted rows? | **Later.** Every change already records who made it, so nothing would need migrating. | Nothing now. |
| 10 | **Order and timing.** Three PRs: A rows and full text, B form and cells, C export and counts, each in the RELEASE lane. If you need to chart before C lands, B would carry a plain CSV of the table. | **A, B, C; the plain CSV in B.** | Three RELEASE reviews in one to two weeks is tight. If needed, cut in this order: the xlsx (CSV stays), then "Not applicable", then merging columns (splitting stays). |

The screen specs have their own smaller questions (keys, the route name, the size limit for a PDF, whether pilot values stay final when the pilot ends). They do not change the size.
