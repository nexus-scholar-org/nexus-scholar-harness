# PRISMA-ScR readiness: what the app covers for the PhD review

Date: 2026-11-06 · Base: `main` at `87d4467` · Author: Claude, for the researcher

This is a checklist for the researcher's PhD review on UAV crop-weed mapping. It sets each
reporting item against what the app does today. The plan is a clean workspace for that
review that also tests the product. The reporting guideline is **PRISMA-ScR**
(Tricco et al., 2018, *Ann Intern Med* 169:467–473). The earlier v03 protocol already
declares it (`playbook_type: SCOPING_REVIEW`, "PRISMA-ScR Scoping Review").

**Status key**

- **App:** the app produces it, with an audit trail.
- **Part:** the app produces part of it; the rest is listed.
- **You:** written or done by the researcher outside the app. Where the app can help, the row says how.
- **Gap:** needed for this review, but the app cannot do it yet.

## Decide first: scoping review or systematic review

The protocol says scoping review. The request said "full systematic review".

A scoping review maps the evidence. A systematic review reported under PRISMA 2020 asks for
more: risk of bias per study (items 11 and 18), effect measures (12), a synthesis method
(13), reporting-bias assessment (14) and certainty of evidence such as GRADE (15 and 22).
In the app, risk of bias, extraction and synthesis are parked (production plan §8).

So a PRISMA 2020 systematic review would mean doing all of those outside the app or building
them first. **Recommendation:** keep the scoping review the protocol defines. The question
(reliability and generalization across evaluation designs) is a mapping question, and
journals such as COMPAG and *Remote Sensing* publish PRISMA-ScR reviews.

## Checklist (PRISMA-ScR, 22 items)

| # | Item | Status | What the app gives / what is missing |
| :-- | :-- | :-- | :-- |
| 1 | Title | You | Say "scoping review" in the title. |
| 2 | Structured summary | You | The methods paragraph (`/screening/export`) supplies the screening counts. |
| 3 | Rationale | You | — |
| 4 | Objectives | Part | The inception wizard writes the research questions into `protocol.json`. Their wording, framed as population–concept–context, is yours. |
| 5 | Protocol and registration | Part | The app keeps the protocol (`protocol.json`), its hash (`protocol.sha256`) and an amendments log, so you can show the protocol was not changed silently. **You:** register on OSF before searching. The app writes no registration document, so you write that text from the protocol. |
| 6 | Eligibility criteria | App | `SCREENING_CRITERIA.md` and the criteria in the protocol. Each exclusion carries its code (`EXC-n`, `FAILS-INC-n`). The rationale for each criterion is yours. |
| 7 | Information sources | Part | Built-in search (OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed) is not production; Discovery (M3) is a stretch milestone (2026-11-10: since built, M3a to M3d; the Discovery screens are on `main` for 1.1.0b6, and the provider findings are in `docs/kits/search/PROVIDERS_2026-11.md`). **You:** search Scopus, Web of Science and IEEE Xplore (plus any others you choose) in their own interfaces, export RIS, and add one RIS file per database on the Import screen with its date searched and search string (M5b, G1 built). |
| 8 | Search | You | Report the full search string for at least one database. Log the exact string, date and hit count for each database as you run it. The PRISMA-S search report is an M3 item and not built. |
| 9 | Selection of sources of evidence | Part | Title/abstract screening is production: blinded human decisions, optional AI drafts with model and prompt hash recorded, per-batch approval, an audit journal, and a methods paragraph with an automation-use statement. **Gaps:** G2 (second reviewer, agreement, resolving disagreements) and G3 (full-text screening). |
| 10 | Data charting process | Gap | Charting/extraction is parked. **You:** use a charting form in a spreadsheet, piloted on a few papers and checked by a second person on a sample. The CSV export of included records is the starting sheet. See G4. |
| 11 | Data items | You | List the charted variables. The v03 `CHARTING_CODEBOOK.md` is a starting point, and needs re-validating against the new protocol. |
| 12 | Critical appraisal (optional in ScR) | You | Risk of bias is parked. In a scoping review, state that you did no critical appraisal and why. |
| 13 | Synthesis of results | You | Synthesis is parked. Describe how you will group and map the studies. |
| 14 | Selection of sources (results, flow diagram) | Part | For the title/abstract stage the app gives identified, duplicates removed, screened, excluded by reason, unclear and included counts, plus a RIS/CSV export. **You:** draw the PRISMA flow diagram from those counts. Since M5b the counts per database and the duplicates removed come from the import (G1). **Gap:** G3 (full-text counts and reasons). |
| 15 | Characteristics of sources | You | From your charting sheet (G4). |
| 16 | Critical appraisal within sources (optional) | You | Only if you do item 12. |
| 17 | Results of individual sources | You | From your charting sheet. |
| 18 | Synthesis of results | You | — |
| 19 | Summary of evidence | You | — |
| 20 | Limitations | You | Include single-reviewer screening (if G2 is not closed) and AI assistance. Report no recall figure until it is measured against human labels (see "AI use" below). |
| 21 | Conclusions | You | — |
| 22 | Funding | You | — |

## Gaps, in the order they bite

**G1. Importing several database exports. Built in M5b (2026-11-06), on branch `dev/m5b/corpus-import`, not merged yet.**
The Import screen and `accept-corpus --ris LABEL=PATH` (repeatable) handle this:
- one RIS file per database, kept unchanged in `literature/raw/ris/`;
- a database exported in parts, added under the same name and summed;
- the date searched and the search string, both optional, flagged "not stated" when missing;
- duplicates removed across and within files by the snapshot's deduplicator;
- counts per database and the duplicate count, carried into the PRISMA counts and the methods paragraph.

An end-to-end test runs two RIS files through publish and checks that the published PRISMA counts equal the preview. This test was added after an independent review found duplicates published as 0 (`full-review-2026-11-06.md`, S-P0-1). Until the branch is merged, the Zotero workaround still applies.

**G2. Second reviewer (blocks item 9 at the level Q1 reviewers expect).**
The app shows the second screener as PARKED, and Agreement measures only human versus AI.
The protocol plans "multi-rater verification sampling (Fleiss/Cohen kappa)". That needs:
- a second human's decisions, made blind, on a random sample (10–20%) or on all records;
- Cohen's kappa between the two people;
- a step to resolve disagreements, recorded in the journal.

This is the "second-screener lane" milestone recommended next.

**G3. Full-text screening (items 9 and 14).**
Records marked Include or Unclear go on to full text. The app has no full-text stage: PDF retrieval and full-text work are parked. The flow diagram needs:
- records sought for retrieval, and records not retrieved;
- reports assessed;
- reports excluded, with reasons;
- studies included.

The workaround is a spreadsheet from the CSV export, with the counts kept by hand. This is the milestone after G2.

**G4. Charting (items 10, 11, 15, 17).**
Charting is parked. A spreadsheet works for the thesis. Building it into the app can wait until G2 and G3 are done.

## AI use (methods and declarations)

- Screening drafts come over the MCP route (Claude, `screen-v1`, prompt hash recorded per draft). The methods paragraph states this.
- Set blinding to **"hidden until you decide"** before screening. Otherwise the human-versus-AI agreement measures nothing, because only decisions made before the reveal count.
- **Do not report a recall figure from the prompt gate.** An independent review (`full-review-2026-11-06.md`, S-P0-2) found its 1,644-record "gold set" was labelled by earlier AI runs and confirmed in bulk, not screened by humans. Gate part 3 would therefore measure agreement with earlier AI labels, not sensitivity. To state the AI's recall in the methods, it must first be measured on a sample that two humans screened independently (for example 300–500 records, with kappa reported). Until then, write that AI drafts were used and that you made every decision.
- Elsevier and MDPI journals ask for a declaration of generative-AI use. The methods paragraph and `docs/data-flow.md` give its facts.

## Data availability (good already)

For an OSF supplement, the app already produces:
- the hashed protocol and its amendments log;
- the append-only audit journal;
- per-decision provenance;
- the RIS/CSV decision export.

## Before the first search, in order

1. Confirm scoping review (above).
2. Merge M5b (multi-file import with deduplication and per-source counts), or use the Zotero workaround knowingly.
3. Agree the second-reviewer sample with Soumia Zertal and Fadhila Djenba, who appear in the v03 calibration records and journal, and build G2 or plan it in a spreadsheet.
4. Back up the 49 gitignored files of `uav-crop-weed-v03` (mostly PDFs) before removing the old workspaces.
5. Create the workspace with `nexus-scholar init` and run inception. Freeze the protocol and register it on OSF.
6. Run the searches, logging string, date and hit count per database. Export RIS.
7. Set blinding to hidden, accept the corpus, screen.
