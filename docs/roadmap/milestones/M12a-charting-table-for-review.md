# M12a Charting table: for your review

Date: 2026-11-21 · Status: **all your answers recorded (2026-11-21): the ten, the eight follow-ups and G1 to G5; item 21 answered "Production from now" and K0 "Label plus four repairs"; the screen questions closed except two deferred items; nothing built, and the start of the build is yours to approve** · Full record: [`M12a-charting-table.md`](M12a-charting-table.md) · Screens (drafts, their own questions still open): `docs/ux/phase3-extraction/final/01-charting-table.md`, `02-one-study.md` · Decisions: `docs/decisions.md`, "2026-11-21 — M12a charting table" · The agent's plan: [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md)

## What you will be able to do

After you publish screening, a new **Charting** step lists every record you kept: your Includes and your "Unclear → full text" records, from the database search and from a citation-chasing round, each marked with where it came from. In a **Full text** view you mark many records at once as To get, Requested, Retrieved or Not retrieved (with one reason), attach the PDF you downloaded or paste a link, and decide each one at full text: Include, or Exclude with exactly one reason. In a **Charting** view you fill your two columns, one row per study still included, by keyboard. "Not reported" and "Not applicable" are values of their own, and each cell can have a note and a "where from" (page or quote). You try the form on about five studies, change the columns, and the change is recorded beside the protocol, which itself is never edited. Every change saves at once and can be undone with `Z`. **From Part F on**, you can also ask the app to look up open-access copies: it asks Unpaywall (and OpenAlex if your key is set) with your contact e-mail, and arXiv for records that have only an arXiv id, downloads only what they list as open, records every file in a manifest, and shows each one as "Fetched, to confirm" until you have opened it and confirmed it is the paper. You export a CSV, or a spreadsheet with the table, the full-text decisions, the PRISMA full-text counts, the form and its changes, and a methods paragraph you can adapt.

The parts come in the order **A** (rows, full text, attach your own), **B** (form and cells, with a plain CSV of the table), **F** (fetching open-access copies), **C** (spreadsheet, counts, methods text). A new part, **K**, makes the PDF kit's downloading production-ready (your answer F1, narrowed to downloading by G1 to G5); it touches different files from B and can be built beside it, and F needs it. Each part is reviewed in the RELEASE lane.

## Your review, as an illustration

*Illustration only: the values below were written from memory of the WeedMap paper (Sa et al., 2018, Remote Sensing) and are not checked against it.*

1. You publish screening. Charting opens with every kept record, your Includes (about 74) and your Unclear records, all "To get". The filter "To decide at full text" shows the Unclear ones first if you want them.
2. Full text view, before Part F: you download the papers you need first and attach them with P. On a paper that turns out to use only RGB images, E, then your exclusion criterion "RGB only" as the one reason: excluded, and counted for PRISMA.
3. Charting view, WeedMap:

| Column (as you typed it at Inception) | Value | Note / where from |
| :-- | :-- | :-- |
| Sensor problems addressed | **Not reported** | Two cameras are used, but no misregistration, missing band or change of camera is measured, corrected or simulated. Methods, dataset section (to check) |
| Cameras and evaluation design | RedEdge-M and Sequoia; one model per camera; no test on a camera absent from training; split by orthomosaic tiles | Methods (to check) |

4. After five studies the second column is clearly three questions. In the form you split it, with the reason "One value per question makes the table countable", into **Cameras** (text), **Test camera absent from training** (Yes/No) and **Data split** (one of: random tiles, by field, by date, by camera, not reported). The five charted cells are marked "Chart again" with their old text shown beside them. The amendment goes into the journal and into the exported methods paragraph: "The charting form was piloted on 5 studies and revised: …".
5. Once Part F is in, you select every row still "To get" and press L: "Look up open-access copies of 214 records? … 177 by DOI, 31 by arXiv id; 6 have neither and are skipped." Later the found copies wait as "Fetched, to confirm". You open one (O), see it is the published version, and press I to include it at full text; the app first asks "Confirm this PDF as the full text?" Enter.
6. Export: the spreadsheet has your table and the counts "N reports sought, M not retrieved (reasons), K assessed, E excluded (reasons), I included", split by databases and citation chasing, and says how many full texts were open-access copies you confirmed.

## Your answers (2026-11-21)

| # | Question | Your answer |
| :-- | :-- | :-- |
| 1 | Contract v1 | "Outside for now" (as recommended) |
| 2 | Column types and options | "Beside the protocol" (as recommended) |
| 3 | What this un-parks | "Yes" (as recommended); F1 later widened it (below) |
| 4 | Rows | "Only after publication" (as recommended) |
| 5 | Full-text screening here | "Yes, smallest form" (as recommended) |
| 6 | PDFs | **"Fetch open-access PDFs"**, in **"Own part after A"** (recommended: fetch nothing). Part A keeps attach-your-own; Part F fetches, keeps a manifest and shows each file "to confirm" before it counts as Retrieved. Record section (d2). |
| 7 | Not applicable; charting without a full text | "Yes to both" (as recommended) |
| 8 | The spreadsheet file | "Add openpyxl" (as recommended) |
| 9 | An agent proposing cells | **"Plan it now"** (recommended: later). Its specification is written: [`M12c-agent-cells.md`](M12c-agent-cells.md), with its own questions. Nothing in it is approved to build or spend. |
| 10 | Order and timing | "A, B, C; CSV in B" (as recommended); with answers 6 and F2 the order is A, B, F, C |

## Your follow-up answers (2026-11-21)

| # | Question | Your answer |
| :-- | :-- | :-- |
| 1 | The three items not asked separately | "Accept all three" (as recommended) |
| F1 | What Part F un-parks | **"Un-park the whole kit"** (recommended: only three pieces). This adds **Part K**: what the kit needs before it can be called production is in the record, section (d3), and below. |
| F2 | F before B, or B first | **"B before F"** (recommended: F before B unless time is short). The order is A, B, F, C. |
| F3 | Versions | "Best open copy, labelled" (as recommended) |
| F4 | Confirmation | "One at a time" (as recommended) |
| F5 | Institutional proxy | "Leave it out" (as recommended), knowing the kit has proxy code |
| F6 | OpenAlex | "Yes" (as recommended): OpenAlex too when your key is set |
| F7 | Records without a DOI | **"Look up by arXiv id now"** (recommended: skip them). Records with only an arXiv id are asked of arXiv's own API; the PDF is the link arXiv gives, labelled "preprint (arXiv vN)". It costs no money or key, about four minutes per 40 such records (arXiv allows one request every three seconds, as recalled), and a small addition to Part F, including a fix: today an old-style id such as `hep-th/9901001` loses its `hep-th/` part. |

## What "the whole kit is production" means

The PDF kit is two systems side by side: an older downloader with the commands `download` and `ingest` (and `extract` for reading), and a newer, careful contract-bound pair (`acquire`, `extract-run`) that nothing in the app calls. The 2026-11-03 assessment found 23 problems in it. Before its downloading can be called production, Part K must, among other things: require your real e-mail (it sends `student@university.edu` by default), name the app instead of posing as a Chrome browser, stop guessing publisher addresses, send your OpenAlex key, stop retrying "not found" answers, stop calling a closed paper open access, write the manifest that says which file belongs to which study, and exit with an error when it fails. Its tests today: 170 test functions, but none drives a live download, the proxy, or a real Docling conversion, and some lock in today's behaviour (the guessed addresses, a broken PDF "succeeding").

**Size.** Part K is one large RELEASE PR (about the size of Part A) if it covers downloading only. Reading PDFs would be another large PR; the newer `acquire` another medium one. With K, the milestone is five RELEASE PRs instead of three: A and B (the charting) still fit one to two weeks, K, F and C do not.

**F1 and F5 together.** The kit becomes production; the proxy does not. Part F neither uses it nor offers it. In the kit, setting a proxy is refused with a message, rather than quietly ignored, until you decide otherwise (G4).

**After G1 to G5 (below), Part K covers downloading only:** the downloader and the `download` and `ingest` commands, with the thirteen repairs of the record's section (d3), the address patterns deleted and a proxy refused. One large RELEASE PR, built beside B. Reading, `acquire` and the old pipeline buttons stay parked.

## Your answers on what "the whole kit" covers (2026-11-21, all as recommended)

| # | Question | Your answer |
| :-- | :-- | :-- |
| G1 | Reading PDFs | "Reading waits for M12b-read" |
| G2 | The newer `acquire` command | "Keep it parked" |
| G3 | The publisher address patterns | "Remove them" |
| G4 | The proxy in the kit | "Refuse with a message" (code kept parked) |
| G5 | The old pipeline buttons | "Yes, they stay parked" |

## Item 21, Part K's bar: your answer

**"Production from now"** (recommended: keep the parked notice until the repairs are done). What it means:
- The words "PARKED, not production" come off `download` and `ingest` (they stay on `extract`, `extract-run` and `acquire`), in the command's help, its test, the user guide, the kit list and the kit's skill; plan §8 changes with them. That is a code change, which this answer does not approve to build. It fits a small PR of its own, **K0**, before Part A.
- Until Part K's repairs land (weeks: after A, beside B), the production `download` sends `student@university.edu` to Unpaywall and OpenAlex in your name, unless `MAILTO` (not `SCHOLAR_MAILTO`, which the kit does not read) is set where it runs; it poses as Chrome to every publisher; it tries the publisher address patterns you decided to remove (G3), one of which saves the wrong IEEE paper; it goes through an institutional proxy if `PROXY_URL` is in a `.env` where it runs, which you decided to refuse (G4); and it keeps no record of which file is which study.
- The app is not exposed: Part F, the only app path to the kit, comes after Part K.

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| K0 | *(Answered 2026-11-21: "Label plus four repairs", as recommended. K0 is a small RELEASE PR before Part A.)* **What the notice-removal PR carries.** Words only; or the words plus the four smallest repairs, so that what you called production keeps the decisions you took today: your e-mail required (refused without it, reading `SCHOLAR_MAILTO` too), the app's own user agent, the address patterns switched off, a set proxy refused with a message? | **The words plus the four repairs.** Each is a few lines with a test; without them a production command contradicts G3 and G4 and writes to Unpaywall in a stranger's name. Part K keeps the other nine. | Words only: a small STANDARD PR. With the repairs: a small RELEASE PR (about a day's review). |

## The questions G1 to G5 as they were asked (kept for the record)

| # | Question | My recommendation | What it costs |
| :-- | :-- | :-- | :-- |
| G1 | **Reading PDFs.** Answer 3 kept "fetching and reading PDFs" parked; F1 un-parks the whole kit. Does "the whole kit" include reading now (`extract`, `extract-run`, the app's stage 5, the MCP tool that parses a PDF), with its eight known reading defects (a failed parse written as success, two-column papers scrambled, Docling never running, …)? Or does reading stay parked until M12b-read, the step before the agent plan? | **Reading stays with M12b-read.** M12a does not read PDFs; you open them. | If included now: another large RELEASE PR before C. |
| G2 | **The newer `acquire` command.** It only accepts studies included in a contract-accepted screening, so it cannot fetch your Unclear rows or M12a's rows (outside the contract by your answer 1). Keep it as it is (parked, with its MCP tool's honest refusal) until a full-text contract path needs it, or make it production now too? | **Keep it parked.** Two production downloaders is the problem the assessment named first. | If now: a medium RELEASE PR, and a use for it to be decided. |
| G3 | **The publisher address patterns.** They were added "for Cloudflare/WAF bypass", are on by default, and the IEEE one points at a different paper. A production kit cannot keep them next to "no guessed addresses, no bypass". Remove them from the kit? | **Remove them.** arXiv, the one honest case, is covered by its own API (F7). | Some closed papers that the patterns sometimes reached stay "To get" for you. |
| G4 | **The proxy inside the production kit.** Part F leaves it out (F5). In the kit itself: refuse a proxy setting with a message and keep the code parked until a decision of its own; or keep it usable from the command line only, with every file it fetches recorded as "institutional access", never open access, and never exported; or delete it? | **Refuse it with a message; code kept parked.** Your library's terms and your credentials are a decision of their own. | Nothing now. |
| G5 | **The app's old pipeline buttons** that run `download`, then `extract`, then the parked matrix and synthesis stages. They stay parked with the matrix and synthesis, even though `download` itself becomes production? | **Yes.** Part F replaces their downloading for M12a. | Nothing. |

The screen specs' smaller questions were closed on 2026-11-21: the keys "Keep as proposed", pilot values "Kept as final", the others "Close as proposed" (the route, the reasons kept apart, the charted count, 100 MB, offline refused, the phone, typed values on an excluded study, where the decision sits, attach on desktop only, and the J/K and Ctrl keys). The wording and layout stay open until you see the built screens. Two items stay open: Part F's fetch states (drafted before Part F) and what the highlighter marks (the M8b amendment).
