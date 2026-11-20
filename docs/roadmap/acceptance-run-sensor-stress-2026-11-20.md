# Acceptance run on a real review: sensor stress in multispectral UAV weed segmentation

Date: 2026-11-20 · Status: IN PROGRESS, stopped at Harvest (the corpus is not prepared) · Build: wheel from `main` at `f05cd29a` (version string `1.1.0b6`), installed with the `ai` extra, opened with `nexus-scholar ui`

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

Severity: P1 blocks a real user, P2 misleads or costs time, P3 is cosmetic. Status is at `f05cd29a`. Findings 12, 15 and 16 are fixed by H-quota-hang (`docs/roadmap/milestones/H-quota-hang.md`, its own PR); the others are open.

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

## What to fix first

Findings 12, 15 and 16 are one defect seen from three sides, and the one real blocker of this run:

- when a provider answers 429 with a `Retry-After` far beyond the cap, stop retrying and report "quota used up, resets at …";
- let "Checks" end early with what it has, mark the rest as not checked, and say so on the Harvest and Hand-off screens;
- test the stop request between records.

Then finding 9 (warn on Plan that Crossref cannot express the AND, or leave it out by default for multi-concept queries) and finding 13 (retry one database).

## Not verified

- "Finish preparing this corpus" after a restart (not pressed: the quota is still used up).
- Hand-off, screening, the AI screener and its cost on this corpus.
- Whether the Semantic Scholar key is valid.
- How much of the OpenAlex daily quota this run used.
