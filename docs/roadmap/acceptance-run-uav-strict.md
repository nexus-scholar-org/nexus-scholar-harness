# Strict acceptance run: UAV crop-weed mapping

Status: READY TO RUN (first attempt stopped 2026-11-13, see "Resuming") · Written 2026-11-12 · Runner: the researcher · Build under test: a wheel built from `main`

One new workspace, taken through inception, discovery, screening and one citation
chase in the installed app, with no shortcuts. It is the human acceptance test for
M4d, M3g and the hardening PRs (#223 to #230), and it replaces the removed v0.2
workspaces as the place where the system is tried on a real topic.

## Rules that make it strict

1. Run the **installed wheel**, not the development checkout.
2. Do every step **in the browser**. The command line is used only to install, to start the app and to run the checks at the end.
3. **Never edit a workspace file by hand.** If a step cannot be done, stop and write it down as a finding.
4. Screen with agent drafts **hidden until you decide**, so agreement is measured.
5. **No AI spend**: agent drafts come over the MCP route, as on 2026-11-06.
6. Write every surprise in the findings table at the end of this file, with the screen and what you expected.

## Before you start

The wheel carries the app's screens only if the UI was exported first. Build the UI, then the wheel:

```bash
cd apps/research-ui && npm ci && npm run build:export && cd ../..
```

```bash
uv build --wheel
```

```bash
uv tool install --force dist/nexus_scholar-1.1.0b6-py3-none-any.whl
```

```bash
nexus-scholar ui --root workspaces
```

- The wheel built from `main` carries the version `1.1.0b6`, the same number as the released beta, although it holds everything merged since. `--force` replaces an installed b6 with it; `nexus-scholar --version` cannot tell the two apart.
- Start the app from the repository root. The search settings are read from a `.env` file in the folder the app starts from (it is ignored by git; there is none in the repository root today). It must set `SCHOLAR_MAILTO` (your contact email) and `SCHOLAR_OPENALEX_KEY`; `SCHOLAR_S2_KEY` is optional. Without the first two, a harvest that includes OpenAlex is refused.
- To see the missing-key case once, start without `SCHOLAR_OPENALEX_KEY`: Explore must say that OpenAlex was probed without a key. Then add the key and restart.
- The app does not let you type a workspace name: it names the folder after the review title. With the title below, **Review and create** shows the folder `reliability-and-generalization-in-uav-crop-weed-mapping-a-scoping-review`, and the workspace lands in `workspaces/<that folder>`, next to the golden run. Wherever this runbook says `<workspace>`, that is the folder. (Rename it after the run if you want a short name as evidence.)

## Resuming the stopped run of 2026-11-13 (after M3i)

The first attempt stopped at an empty Hand-off after harvest `run_001` (1,074 records, no marker, because it was made before M3i). Do not harvest again. With a wheel built from current `main` (build the UI first, see above) and the workspace folder in the `--root` you start the app with:

- **Harvest** for `run_001` should read "The search finished, but the corpus was not prepared." with the badge "Preparation unfinished", and say "The records found are saved, but the steps after the search did not end, so screening has nothing to receive yet." and "This run was made by an earlier version, which did not record the step it stopped at."
- The button **Finish preparing this corpus** runs deduplication, abstracts and verification from the saved records ("No database is searched again"). When it ends, the Hand-off opens.
- **Hand-off** before that says "The corpus is not ready to hand off yet." and links "Finish preparing this corpus on Harvest", not "There is nothing to hand off yet."
- If instead it says "The saved records of this run cannot be read, so it cannot be finished. Harvest again.", write that down as a finding.

Wording is copied from `apps/research-ui/lib/discovery-copy.ts` at `e7644a6c`. M3i's own record says this exact folder was not tried (`docs/roadmap/milestones/M3i-harvest-robustness.md`, "Not verified"), so reaching it is the first real check. Then continue the run at "Accept this corpus" below.

## What to enter (from `workspaces/uav-crop-weed-v03/protocol.json`, protocol v0.3)

| Field | Value |
|---|---|
| Title | Reliability and Generalization in UAV Crop-Weed Mapping: A Scoping Review |
| Review type | Scoping review (PRISMA-ScR) |
| Years | 2020 to 2026 |
| Language | English |
| Databases | OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed |
| Research questions | RQ1 to RQ4, copied from the v0.3 protocol |
| Concept 1 | UAV: UAS, drone, drones, unmanned aerial vehicle(s), unmanned aircraft system, uncrewed aerial vehicle, remotely piloted aircraft, aerial imagery, orthomosaic |
| Concept 2 | weed: weeds, crop weed, crop-weed, crop and weed, site-specific weed management, precision weeding, herbicide prescription |
| Concept 3 | mapping: detection, segmentation, classification, monitoring, localization, identification, discrimination |
| Criteria | INC-01 to INC-03 and EXC-01 to EXC-04, copied from `workspaces/uav-crop-weed-v03/SCREENING_CRITERIA.md` |
| Retrieval cap | Small enough to screen by hand: aim for 150 to 300 studies after duplicates |

The v0.3 protocol has no seed papers. Take them from the Explore step and accept them one by one.

## The run, phase by phase

### Inception
- [ ] New review → Scope, **Explore**, **Direction**, Shape, Concepts and criteria, Review and create.
- [ ] Explore shows which databases answered and whether the OpenAlex key was used.
- [ ] Synonym suggestions come from the pool and are accepted one by one.
- [ ] Anchor papers become seeds (stored as DOIs, at most 25).
- [ ] Change the question after choosing a direction: the direction is flagged as stale.
- [ ] Nothing is written before **Create the workspace**.

### Discovery
- [ ] Plan shows the compiled query with the accepted synonyms, the years and the language.
- [ ] Recall finds the seeds. A seed that is missing is explained.
- [ ] Harvest runs every database; a failed or capped leg says so.
- [ ] Duplicates and Report show counts that add up.
- [ ] Edit a criterion's wording after the harvest: Hand-off warns, and the accept still works (F3).
- [ ] Change the years after the harvest: Hand-off refuses the accept until a new harvest (F3). Change them back.
- [ ] **Accept this corpus**. The corpus view shows the databases and counts, not zeros (F4).

### Screening
- [ ] Prepare, then Triage every record yourself, with agent drafts hidden.
- [ ] Agent proposals arrive over MCP; Agreement reports real agreement.
- [ ] Resolve every conflict. Publish. Export PRISMA and the methods text.

### Citation chase
- [ ] The **Chase** step appears only after publishing.
- [ ] Run one chase (both directions). Legs, cap hits and "already in your corpus" are shown.
- [ ] Send the new studies to screening: round 1 is archived under `literature/screening_rounds/round_001/`.
- [ ] Screen at least one batch of round 2. If round 2 is too large to finish, say so in the findings; do not publish it half-screened.

### Protocol replace (on a throwaway copy, not on this workspace)
- [ ] Replace the protocol: the old corpus and decisions move to `audit/replaced/<stamp>/`.

## Checks at the end

```bash
nexus-scholar doctor --workspace "workspaces/<workspace>" --exit-code
```

```bash
uv run python scripts/check_golden_workspace.py "workspaces/<workspace>"
```

The second check was written for the golden workspace and reads round 1's journal,
provenance and PRISMA numbers. After a chase is accepted it may not understand
round 2; if it fails for that reason, record it as a finding, not as a failed run.

## The run passes when

- every box above is ticked or has a finding that explains it;
- `doctor` exits 0;
- the PRISMA numbers reconcile with the corpus and the published decisions;
- every decision is recorded as yours (method `HUMAN`), none as the agent's;
- no workspace file was edited by hand.

## Not covered by this run

Arabic and French screens (check a few by eye), full-text retrieval, extraction, synthesis, the citation graph.

## Findings

| # | Screen or command | What happened | What you expected | Severity | Status at `e7644a6c` |
|---|---|---|---|---|---|
| 1 | Runbook, "Before you start" | Asked for the workspace name `uav-crop-weed-strict-2026-11`; the app cannot set one | A name the app can set, or the real folder name | P3 | Fixed here (H-small-fixes-2026-11-18) |
| 2 | Inception, Explore: topic field | The field asks for "one or two sentences"; a sentence returned 0 from OpenAlex and Semantic Scholar and noise from Crossref and arXiv, shown as "answered" | A keyword query from the topic; "0 results" said as such | P2 | Partly fixed by M10a (PR #233): keyword query, "0 results" said, arXiv terms combined; Crossref is left as it was |
| 3 | Inception, Explore: the 25-paper pool | Cut by database-name order, not relevance (`probe_pool` kept `docs[:25]` after `stable_order`) | A sample chosen by relevance | P1 for Inception | Fixed by M10a (PR #233) |
| 4 | Inception, Direction | The proposals were generic (follows from 3) | Directions anchored in on-topic records | P2 | Partly fixed by M10a (PR #233): the sample is relevance-chosen, so directions rest on on-topic records; the generic labels come from the direction scorer, which M10a did not tune: open |
| 5 | Inception, criteria | Every exclusion is labelled `OUT_OF_SCOPE`; no reason category can be set. PRISMA "excluded by reason" counts are per criterion id (`EXC-nn`), not per `reason_category`; the label only reaches `SCREENING_CRITERIA.md` and the batch instructions | Not recorded | P3 | Open |
| 6 | Inception, matrix columns | Only three suggested columns; none can be added | Not recorded | P3 | Open |
| 7 | Inception, Shape | The "Sample Size" sentence reads badly with the unit of analysis pasted in | Not recorded | P3 | Open |
| 8 | Inception, Review | Concepts are listed without their synonyms | Not recorded | P3 | Open |
| 9 | Inception, Review | A stray dot before the folder path; "Convincing evidence is A primary…" | Not recorded | P3 | Open |
| 10 | Inception (gap, not a defect) | No agent proposes research questions, concepts, synonyms, criteria or seeds | The researcher's remark: assisted inception (candidate milestone, their decision) | n/a | Planned: M10b to M10e |
| 11 | Discovery, Import | The only accept button met in Discovery is the disabled one on Import; nothing points to the Hand-off | Not recorded | P2 | Open (M3i added the Hand-off link for an unprepared corpus only) |
| 12 | Discovery, Hand-off | "There is nothing to hand off yet" after a harvest of 1,050 works. One harvest job runs search, deduplication, abstracts, verification; only verification writes `literature/verified.json`; the run is archived as published after the search, so Harvest looks finished. A job that failed or was closed after the search left no trace; `verified.json` carries no run id | The Hand-off, or a stated reason and a way forward | P1 or P2 | Fixed by M3i (PR #235); the strict run's own folder not yet tried |
| 13 | `uv build --wheel`, then the app | A local build silently builds a wheel with no UI when `apps/research-ui/.next-export` is missing; the "no app bundle" message says build when a reinstall is needed. The runbook omitted `npm ci` and `npm run build:export` | A loud failure naming the two commands; a message that says what to do | P2 | Runbook fixed here; guard and message: see the H-small-fixes record |

Source: the researcher's notes of 2026-11-14 (findings 1 to 13); the PRISMA point in 5 and the explanation in 12 were confirmed in code. The "What you expected" column states only what the notes or the fix records say.
