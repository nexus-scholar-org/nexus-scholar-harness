# M12a Charting table: for your review

Date: 2026-11-21 · Status: **your ten answers recorded (2026-11-21); eight new, smaller questions below, seven of them on the new fetching part; nothing built, and the start of the build is yours to approve** · Full record: [`M12a-charting-table.md`](M12a-charting-table.md) · Screens (drafts, their own questions still open): `docs/ux/phase3-extraction/final/01-charting-table.md`, `02-one-study.md` · Decisions: `docs/decisions.md`, "2026-11-21 — M12a charting table" · The agent's plan: [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md)

## What you will be able to do

After you publish screening, a new **Charting** step lists every record you kept: your Includes and your "Unclear → full text" records, from the database search and from a citation-chasing round, each marked with where it came from. In a **Full text** view you mark many records at once as To get, Requested, Retrieved or Not retrieved (with one reason), attach the PDF you downloaded or paste a link, and decide each one at full text: Include, or Exclude with exactly one reason. **From Part F on**, you can also ask the app to look up open-access copies: it asks Unpaywall (and OpenAlex if your key is set) with your contact e-mail, downloads only what they list as open access, records every file in a manifest, and shows each one as "Fetched, to confirm" until you have opened it and confirmed it is the paper. In a **Charting** view you fill your two columns, one row per study still included, by keyboard. "Not reported" and "Not applicable" are values of their own, and each cell can have a note and a "where from" (page or quote). You try the form on about five studies, change the columns, and the change is recorded beside the protocol, which itself is never edited. Every change saves at once and can be undone with `Z`. You export a CSV, or a spreadsheet with the table, the full-text decisions, the PRISMA full-text counts, the form and its changes, and a methods paragraph you can adapt.

The parts come in the order **A** (rows, full text, attach your own), **F** (fetching open-access copies), **B** (form and cells, with a plain CSV of the table), **C** (spreadsheet, counts, methods text), each reviewed in the RELEASE lane.

## Your review, as an illustration

*Illustration only: the values below were written from memory of the WeedMap paper (Sa et al., 2018, Remote Sensing) and are not checked against it.*

1. You publish screening. Charting opens with every kept record, your Includes (about 74) and your Unclear records, all "To get". The filter "To decide at full text" shows the Unclear ones first if you want them.
2. Full text view. You select every "To get" row and press L: "Look up open-access copies of 214 records? … 37 have no DOI and are skipped." Enter. Later, the found copies wait as "Fetched, to confirm". You open WeedMap's (O), see it is the published version, and press I to include it at full text; the app first asks "Confirm this PDF as the full text?" Enter. On a paper that turns out to use only RGB images, E, then your exclusion criterion "RGB only" as the one reason: excluded, and counted for PRISMA. For a paper with no open copy, you attach the one you got from the library with P.
3. Charting view, WeedMap:

| Column (as you typed it at Inception) | Value | Note / where from |
| :-- | :-- | :-- |
| Sensor problems addressed | **Not reported** | Two cameras are used, but no misregistration, missing band or change of camera is measured, corrected or simulated. Methods, dataset section (to check) |
| Cameras and evaluation design | RedEdge-M and Sequoia; one model per camera; no test on a camera absent from training; split by orthomosaic tiles | Methods (to check) |

4. After five studies the second column is clearly three questions. In the form you split it, with the reason "One value per question makes the table countable", into **Cameras** (text), **Test camera absent from training** (Yes/No) and **Data split** (one of: random tiles, by field, by date, by camera, not reported). The five charted cells are marked "Chart again" with their old text shown beside them. The amendment goes into the journal and into the exported methods paragraph: "The charting form was piloted on 5 studies and revised: …".
5. Export: the spreadsheet has your table and the counts "N reports sought, M not retrieved (reasons), K assessed, E excluded (reasons), I included", split by databases and citation chasing, and says how many full texts were open-access copies you confirmed.

## Your answers (2026-11-21)

| # | Question | Your answer |
| :-- | :-- | :-- |
| 1 | Contract v1 | "Outside for now" (as recommended) |
| 2 | Column types and options | "Beside the protocol" (as recommended) |
| 3 | What this un-parks | "Yes" (as recommended) |
| 4 | Rows | "Only after publication" (as recommended) |
| 5 | Full-text screening here | "Yes, smallest form" (as recommended) |
| 6 | PDFs | **"Fetch open-access PDFs"**, in **"Own part after A"** (recommended: fetch nothing). Part A keeps attach-your-own; Part F fetches, keeps a manifest and shows each file "to confirm" before it counts as Retrieved. Record section (d2). |
| 7 | Not applicable; charting without a full text | "Yes to both" (as recommended) |
| 8 | The spreadsheet file | "Add openpyxl" (as recommended) |
| 9 | An agent proposing cells | **"Plan it now"** (recommended: later). Its specification is written: [`M12c-agent-cells.md`](M12c-agent-cells.md), with its own questions. Nothing in it is approved to build or spend. |
| 10 | Order and timing | "A, B, C; CSV in B" (as recommended); with answer 6 the order is A, F, B, C |

## New questions (the first two touch an accepted decision)

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| 1 | **Three items you have not been asked separately.** The page described them, but no question named them: the four full-text statuses set in bulk (record (b)); the Pilot switch and the amendments with a reason (record (f)); saving every change as an event with undo and journal rows (record (i)). Accept them as written? | **Yes.** | Nothing. |
| F1 | **What Part F un-parks.** Your answer 3 keeps "fetching and reading PDFs (`scholar_pdf`)" parked. With answer 6: a new fetch module becomes production, reusing three pieces of the parked kit (its PDF check, its safe file writing, its reading of Unpaywall and OpenAlex answers), while the kit's downloader as it is, its `scholar-pdf` commands and MCP tools, the institutional proxy, and reading PDFs stay parked? | **Yes.** The kit's downloader sends a placeholder e-mail, poses as a Chrome browser, guesses publisher URLs and calls OpenAlex without the key it now needs. | Nothing beyond Part F. |
| F2 | **If time is short,** does F stay before B (as you chose), or may B go first so you can chart sooner, with you downloading by hand meanwhile? F and B share the table screen, so they cannot be built at the same time. | **F before B as you chose, but B first if the two-week date is at risk.** | Part F is about one RELEASE PR (size M). |
| F3 | **Versions.** Fetch the best open copy there is, published version first, then the accepted manuscript, then a preprint, each labelled and exported with its version; or the published version only? | **Best open copy, labelled.** You decide at confirmation whether a preprint will do. | A version column in the export. |
| F4 | **Confirmation one study at a time**, folded into the full-text decision (I or E on a row with a file to confirm asks to confirm it first); no bulk confirmation? | **Yes.** Confirming means having looked; you open each paper anyway to decide on it. | A few hundred Enter presses, inside work you do anyway. |
| F5 | **The institutional proxy.** Leave it out of Part F entirely, or allow it when you set it yourself? | **Leave it out.** It means your library credentials and its terms; only openly listed copies are fetched. | Paywalled papers stay "To get" for you to download. |
| F6 | **OpenAlex.** Ask OpenAlex too when your OpenAlex key is set (its calls share the daily budget with a harvest), and Unpaywall alone otherwise? | **Yes.** | None; a key you already have for harvests. |
| F7 | **Records without a DOI** (some arXiv-only entries) are not looked up in Part F; the run counts them and you attach them yourself? | **Yes, for Part F.** A look-up by arXiv id could come later if the count is large. | You download those by hand. |

The screen specs have their own smaller questions (keys, the route name, the size limit for a PDF, whether pilot values stay final when the pilot ends, and the not-yet-drafted fetch states). They do not change the size.
