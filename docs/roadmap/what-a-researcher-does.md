# What a researcher actually does

Date: 2026-11-20 · Status: motivation for the milestones after the acceptance run; not a specification · Written by the main session at the researcher's request

This note describes the work of a literature review as it is really done, and where the app's assumptions differ. Its sources are review methodology (PRISMA 2020, PRISMA-S, the JBI guidance for scoping reviews) and the acceptance run of 2026-11-20 (`acceptance-run-sensor-stress-2026-11-20.md`). The researcher does this work and the author of this note does not: where the two disagree, the researcher's practice wins and this file should be corrected.

## The work, step by step

**1. Before any tool: a vague question and a pile of known papers.** The researcher starts with 5 to 30 papers already in a reference manager, a supervisor's hint, and a question that is still moving. The kind of review (scoping or systematic) is chosen mostly by what the venue and the supervisor expect. The question gets sharper by reading, not by filling in a form.

**2. Developing the search: days of trial and error.** A string is tried in one database; the count and the first two pages are read; a term is changed; it is tried again, ten to twenty times. Terms are borrowed from the keywords of the known papers. Each time, the researcher checks that the known papers show up, and finds out why when one is missing. The final string is translated into each database's syntax by hand. There are often several strings, one per sub-question. The string, the date and the count are written down per database, because the methods section must report them. The search is developed, not typed once.

**3. The protocol: written, but not final.** Question, criteria, databases, years and languages; sometimes registered; usually shown to the supervisor. The criteria change after a pilot: 50 to 100 records are screened, the criteria turn out ambiguous, they are rewritten, and only then fixed.

**4. Running the searches: exports are the main road.** Scopus, Web of Science and IEEE Xplore come through the university's access and leave as files. Each database has its own limits and formats (a personal sign-in to export, CSV only, a cap of 1,000 results with no abstracts). Free sources (OpenAlex, arXiv, Google Scholar) are additions to these, not the base.

**5. Removing duplicates.** In a reference manager or a screening tool, with a manual look at near-duplicates such as the conference and journal versions of one study.

**6. Title and abstract screening: fast and forgiving.** Ten to thirty seconds a record, on the keyboard, in sessions, with fatigue. The rule is "when in doubt, keep it". A reason for exclusion is not required at this stage; PRISMA asks for reasons only at full text. Missing abstracts are looked up one by one. Two reviewers is the ideal; a PhD student usually works alone and the supervisor checks a sample. Decisions are revisited.

**7. Getting the full texts.** Through the library, by request, or by writing to authors. "Not retrieved" has to be counted.

**8. Full-text screening.** Each exclusion gets one reason, and those counts go into the flow diagram.

**9. Citation chasing.** The references of the included papers and the papers that cite them; what is new is screened.

**10. Charting the data: the bulk of the time.** One row per study in a spreadsheet. The columns are piloted on five papers and then revised. Values come from methods sections and tables. "Not reported" is common and is itself a finding.

**11. Synthesis and writing.** Tables, figures, an evidence map, the narrative; the PRISMA diagram, an appendix with every search string, and the list of included studies.

**12. Updating.** Months later, before submission or after review, the searches are run again and only the new records are screened.

## What runs through all of it

- **It loops.** The search, the criteria and the charting columns are each revised after a pilot. A revision must be recorded, not blocked.
- **The researcher is accountable.** Every choice has to be defensible to a supervisor and a reviewer. The outputs needed are the diagram, the strings, the counts and the reasons.
- **Time goes to screening and charting.** Setup should take minutes.
- **AI is a second reader.** It is used when the researcher knows how often it is wrong.
- **Other tools stay.** A reference manager, a spreadsheet and a word processor are the hub. A review tool must take files in and give files out.

## Where the app's assumptions differ (at `2436fe66`)

| What a researcher does | What the app assumes |
| :-- | :-- |
| Develops the search over many tries | The query is typed once in Inception and frozen; the first counts appear after the freeze |
| Uses several strings | One query per review |
| Brings most records as exports | The harvest is the main path; imported files get no abstract filling and no checks, and cannot be combined with a harvest |
| Revises criteria after a pilot | Criteria are frozen when the workspace is created |
| Keeps when in doubt; no reason needed at the abstract stage | Agent drafts answer every criterion; before H-screening-drafts one gap made the draft unclear |
| Updates the search later | A new harvest replaces the old one |
| Spends most of the time on charting | Charting (the Matrix phase) is parked |

## What the acceptance run added

The run of 2026-11-20 was the first real review taken through the app. It produced 37 findings; the ones that would have stopped or misled a researcher working alone were the quota hang, the Crossref noise, a query too narrow with no warning, no way to combine Scopus with a harvest, 85% of agent drafts marked unclear, and a default that would have cost $7.59 where $0.22 was meant. The test suite passed throughout: the tests show that the code does what was specified, not that the specification serves a researcher. Three of the six were born in Inception and discovered downstream.

## Consequences (order agreed with the researcher on 2026-11-20)

In this order, each sized so the researcher's own review can use it:

1. **Every source equal** (M3f-combined-corpus, started 2026-11-20): a harvest and imported files in one corpus, with the same abstract filling and checks.
2. **A query workbench** in Inception and on Discovery's Plan: counts as the query is edited, the cost of each concept, a check that the known papers can test the query, and a database export as a comparison set.
3. **A criteria pilot:** screen a sample, revise the criteria as a recorded amendment, and warn about criteria that mirror or contradict each other.
4. **A minimal charting table:** the protocol's columns, one row per included study, full-text status, export to a spreadsheet.
5. **Search updates and several queries:** add a new search to an accepted corpus and screen only what is new; needs a contract decision.

Not before these: the in-app chat, agent autonomy, more interface languages.
