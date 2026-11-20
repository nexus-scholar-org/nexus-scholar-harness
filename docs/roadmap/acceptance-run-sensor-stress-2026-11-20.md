# Acceptance run on a real review: sensor stress in multispectral UAV weed segmentation

Date: 2026-11-20 · Status: IN PROGRESS. The first workspace stopped at Harvest and is superseded; a second workspace with a wider query holds an accepted corpus of 1,062 works from five databases and is ready for screening (see "The search was too narrow") · Build: wheel from `main` at `f05cd29a` (version string `1.1.0b6`), installed with the `ai` extra, opened with `nexus-scholar ui`

This run replaces the unfinished strict UAV run (`acceptance-run-uav-strict.md`) as the end-to-end check on an installed wheel. It is a real review for the researcher's thesis, so its output is kept. The main session drove the browser at the researcher's request; the researcher made the scope decisions.

## The review

| Field | Value |
| :-- | :-- |
| Workspace | `Documents\Nexus Scholar\workspaces\sensor-stress-in-multispectral-uav-weed-segmentation-a-scoping-review` (outside the repository) |
| Title | Sensor stress in multispectral UAV weed segmentation: a scoping review |
| Playbook | Scoping review, 2013 to 2026, English, 300 to 2,000 planned records |
| RQ1 | In studies that segment crops or weeds in multispectral UAV images with learned models, which sensor problems (band misregistration, missing bands, a change of camera) are addressed, and how? |
| RQ2 | How are these models evaluated when the camera changes, and has any study tested on a camera absent from training? |
| Concepts | UAV, multispectral, weed, segmentation, each with synonyms |
| Criteria | Four inclusion and five exclusion criteria, each a single test. The two research questions are charting columns, not screening criteria |
| Recall seeds | WeedMap, WeedsGalore, BAWSeg, Khoshboresh-Masouleh and Akhoondzadeh 2021 |
| Spend | AI screener on Haiku, ceiling $10 (researcher, 2026-11-20). Nothing spent so far |

Design decisions by the researcher on 2026-11-20: one review with one broad screening rule; "weed" as the search concept, without "crop" alone; Crossref left out of the harvest.

## What happened, step by step

| Step | Result |
| :-- | :-- |
| Inception, six steps | Completed, workspace created. First search returned 25 papers, including the four seeds |
| Discovery, Plan and estimate | OpenAlex 166, Semantic Scholar 107, arXiv 7, Crossref 6,221 |
| Discovery, Recall | 4 of 4 seeds found (OpenAlex 4, Crossref 4, Semantic Scholar 3) |
| Harvest, run 1 | PARTIAL: 173 records (OpenAlex 166, arXiv 7), Semantic Scholar refused (HTTP 429). Duplicates, abstracts and checks ended; 166 records after duplicates; paused for the hand-off |
| Harvest, run 2 | Started by the main session to retry Semantic Scholar. Refused again. OpenAlex then answered HTTP 429 with a retry time of about 14 hours (daily quota). The "Checks" step hung; the app was restarted. The run now reads "The search finished, but the corpus was not prepared" and offers "Finish preparing this corpus" |

Next: press "Finish preparing this corpus" after the OpenAlex quota resets (midnight UTC), then Hand-off and screening.

## Findings

Severity: P1 blocks a real user, P2 misleads or costs time, P3 is cosmetic. Status is at `f05cd29a`. Findings 12, 15 and 16 are fixed by H-quota-hang (`docs/roadmap/milestones/H-quota-hang.md`, PR #259, merged 2026-11-20); the others are open.

| # | Screen | What happened | Severity |
| :-- | :-- | :-- | :-- |
| 1 | Inception, Criteria | The wizard writes an inclusion criterion from the "proof a reviewer would accept" answer ("Reports the gold-standard proof — A table of…"). It is not a screening rule | P2 |
| 2 | Inception, Criteria | The out-of-scope answer becomes one lumped exclusion criterion and is accepted without a decision. Five separate criteria had to be typed | P2 |
| 3 | Inception, Direction | The proposed directions are weak phrases ("aerial vehicle uav"). A custom direction needs an exact phrase match in two papers, so a natural sentence scores 0 of 25 (strict run finding 4, still open) | P2 |
| 4 | Inception, Scope | A new, empty draft shows the note "No start year is set. The first search used 2000" before any search | P3 |
| 5 | Inception, several | Raw timestamps (`2026-11-20T09:45:15.784778+00:00`) in the drafts list and the "Draft saved" line; "Notes ()" with an empty count | P3 |
| 6 | Inception, Direction | The direction radio buttons are all named "on" for assistive technology; DOI link names start with a comma | P3 |
| 7 | Inception, Create | The browser console logged one HTTP 422 around the create step. The workspace was created. Cause not traced | P3, unverified |
| 8 | App | The app stopped answering between Inception and Discovery (port closed, process alive, no traceback in the log). A restart fixed it. Cause unknown; seen once | P1 if it repeats |
| 9 | Discovery, Plan | Crossref receives the words with the AND between concepts dropped. The screen shows the string but gives no warning. Only the estimate reveals it: 6,221 matches against 166 in OpenAlex | P1 |
| 10 | Discovery, Plan | The recommended cap ("1720 per database") would keep about 1,500 loosely matching Crossref records and every record of the other databases. It trims nothing useful | P2 |
| 11 | Discovery, Harvest | Semantic Scholar answers HTTP 429 on every run and its key stays "Set, not yet verified". The app cannot tell a bad key from throttling, and offers no key check | P2 |
| 12 | Discovery, Harvest | When OpenAlex's daily quota runs out during "Checks", the run neither fails nor pauses with a message. The screen says "Preparing" | P1 |
| 13 | Discovery, Harvest | "Harvest again" repeats every database and marks the finished run stale, even when one database failed. There is no "retry the failed database" | P2 |
| 14 | Discovery, Harvest | The per-record check is rate-limited by Crossref on almost every record (one retry each), which slows preparation | P3 |
| 15 | Discovery, Harvest | "Stop after the current step" is not read inside "Checks" (`should_stop` is tested between stages only), so a stop can take hours | P1 |
| 16 | Discovery, Harvest | "Checks" calls OpenAlex once per record (`DocumentVerifier.hydrate_metadata`). With the quota gone, each record costs three refused attempts of 60 seconds (`http_client.get` caps the wait at 60 s and ignores that `Retry-After` is 14 hours): about nine hours for 166 records | P1 |
| 17 | Discovery, Recall | The line "Checked 2026-11-20 10:58 UTC" shows the researcher's local time with the label UTC (the journal has the harvest that followed at 10:01 UTC) | P3 |

Not counted as a defect: three concepts first lost their synonyms. The cause was the automation tool filling the fields without the events a keyboard sends; typing saved them.

## The search was too narrow (afternoon of 2026-11-20)

A side session compared the first workspace's 166 records with other databases, through the researcher's institutional sign-in, using the same strict query (UAV AND multispectral AND weed AND segmentation or mapping, 2013 to 2026). Overlap was computed by DOI and normalised title, so near-duplicates are undercounted; relevance was judged from titles only.

| Source | Records | Compared with the app's 166 |
| :-- | --: | :-- |
| App harvest (OpenAlex and arXiv) | 166 | |
| Scopus (title, abstract, keywords) | 130 | 99 shared, 31 only in Scopus, 66 only in the app |
| IEEE Xplore (all metadata) | 45 | 17 in the app, 19 in Scopus, 25 in neither |
| ScienceDirect (shortened query) | 30 | 1 new |
| SpringerLink (full text) | 1,713 | of the 20 most relevant titles, 16 are in no other source; several are on topic |

The likely cause (the side session's inference; the papers were not opened): the query requires both "UAV" and "multispectral" in the title, abstract or keywords, and relevant papers that use only one of them are missed by every abstract-based source. Scopus counts when one concept is dropped: 130 strict, 236 without UAV, 512 without multispectral.

The morning's recall check passed 4 of 4, and the main session read that as "OpenAlex alone is enough". That was wrong: all four seeds contain every concept, so they could not show this gap.

**Decision by the researcher:** widen to three concepts, (UAV or multispectral terms) AND weed AND segmentation or mapping, in a new workspace; import the Scopus and IEEE Xplore exports first, then harvest.

**Second workspace** (created 2026-11-20, 14:37 local, on the build from `b9c7dc0b`): `sensor-stress-in-uav-and-multispectral-weed-segmentation-a-scoping-review`. Same questions, criteria and charting columns. Five recall seeds, one of which the strict query had missed ("CLIP Meets DINOv3 for Effective Crop and Weed Multispectral Semantic Segmentation"). Estimate without Crossref: OpenAlex 781, Semantic Scholar 539, arXiv 30; 781 to 1,350 works after duplicates. Recall check: 5 of 5. The first workspace is left as it is.

**Corpus of the second workspace** (accepted 2026-11-20, 15:21 local, snapshot `ART-corpus-f679e82b9933f5bf7e14821d659330e0`). All five sources came in through the Import screen, because this build cannot combine a harvest with imported files (finding 26). Scopus (618, RIS with abstracts) and IEEE Xplore (208, CSV converted to RIS) were exported by the researcher through their institutional sign-in. OpenAlex (781), Semantic Scholar (539) and arXiv (30) were retrieved with `scholar-search search --protocol <workspace>/protocol.json --provider <name> --limit 5000 --no-dedup --format ris`; each count equals the app's estimate. Total 2,176 records, 1,114 duplicates removed, 1,062 works; 50 of them have no abstract (counted outside the app with `Deduplicator`). SpringerLink (full-text search, two exports capped at 1,000, 1,332 records not in the corpus, 291 of them with "weed" in the title, no abstracts) was looked at and left out by the researcher. Batches of 20 are prepared. Agent proposals are not started: the app shows no Anthropic key, and the estimate for 1,062 records is about $0.22 on Haiku 5.5 and $7.59 on Opus 5.5 (batch pricing).

The researcher replaced the OpenAlex key the same afternoon; with it OpenAlex answered again. Semantic Scholar answered the first search, the estimate and the recall check with the key that had been refused in the morning, so finding 11 was throttling, not a bad key.

### Findings from this part

| # | Screen | What happened | Severity |
| :-- | :-- | :-- | :-- |
| 18 | Inception, Concepts; Discovery, Plan | Nothing shows what each concept costs. A four-concept AND returned 166 records where a three-concept one returns 781, and no screen hints at it. Counts with one concept dropped would have shown it | P1 for the review's quality |
| 19 | Inception to Discovery | The first counts for the real query appear on Discovery's Plan, after the protocol is frozen. Changing a concept then means going back through Inception | P1 |
| 20 | Discovery, Recall | The recall check gives false comfort when every seed contains every concept. No warning says the seeds cannot test the query | P2 |
| 21 | Discovery, Recall and Import | A database export cannot be used as a comparison set ("31 of these 130 are missing from your harvest"). The comparison was done by hand outside the app | P2 |
| 22 | Protocol | One query per review: one list of concepts joined by AND. Several named queries, each reported, cannot be expressed. The researcher recalls that an earlier version supported several queries; not checked in the history | P2, a milestone of its own (needs a contract decision) |
| 23 | Inception, Direction | One of the three proposed directions was "blue green red" | P3 (same cause as finding 3) |
| 24 | Discovery, Recall | The result lists "Crossref: 6221" in the second workspace, where Crossref was not counted. The number equals the first workspace's count; whether it is a real count or a carried value was not checked | P3, unverified |
| 25 | Discovery, Import | Scopus RIS exports can carry a malformed type (`label.ris.referenceType.BOOK_CHAPTER`); IEEE Xplore's quick export is CSV only. Tested on 2026-11-20: the importer reads 31 such records without error (the type is ignored), and the converted IEEE file imports | P3 (CSV is not accepted) |
| 26 | Discovery, Harvest and Import | A corpus is either a harvest or imported files; one snapshot from both is M3f-combined-corpus, not built. The Harvest warning says "If you have exports, import them first", which reads as if the two then combine. A researcher with a Scopus export cannot use the app's own harvest in the same review | P1 |
| 27 | Discovery, Hand-off | For a corpus of imported files the Hand-off shows "With an abstract: 0 (0 %)" and "Title only: 0"; the real figures were 1,012 and 50 | P2 |
| 28 | Screening, Agent proposals | Before batches are prepared, the screen says "No accepted corpus … Import your search results and accept them first" although the corpus is accepted | P3 |
| 29 | `scholar-search search` | The command stops at 100 records by default and prints "Saved 100 documents" with no word that more exist; arXiv timed out once after 30 s and the command saved an empty file with exit code 0 | P2 |

## What to fix first

Findings 12, 15 and 16 are one defect seen from three sides, and the one real blocker of this run:

- when a provider answers 429 with a `Retry-After` far beyond the cap, stop retrying and report "quota used up, resets at …";
- let "Checks" end early with what it has, mark the rest as not checked, and say so on the Harvest and Hand-off screens;
- test the stop request between records.

Then finding 9 (warn on Plan that Crossref cannot express the AND, or leave it out by default for multi-concept queries) and finding 13 (retry one database).

After the afternoon's part, findings 18 to 21 come before both: a loop that lets the researcher edit concepts and see counts (full query, one concept dropped, seeds found) before the protocol freezes, shared by Inception's Concepts step and Discovery's Plan; a warning when the seeds cannot test the query; and a database export as a comparison set. The researcher's view, recorded on 2026-11-20: these checks belong to Inception, and several queries per review (finding 22) should come back.

## Not verified

- "Finish preparing this corpus" after a restart (not pressed: the quota is still used up).
- Hand-off, screening, the AI screener and its cost on this corpus.
- Whether the Semantic Scholar key is valid.
- How much of the OpenAlex daily quota this run used.
