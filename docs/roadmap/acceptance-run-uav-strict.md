# Strict acceptance run: UAV crop-weed mapping

Status: READY TO RUN · Written 2026-11-12 · Runner: the researcher · Build under test: a wheel built from `main`

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
- Use the workspace name `uav-crop-weed-strict-2026-11`. It lands in `workspaces/`, next to the golden run, so it can be committed as evidence afterwards.

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
nexus-scholar doctor --workspace workspaces/uav-crop-weed-strict-2026-11 --exit-code
```

```bash
uv run python scripts/check_golden_workspace.py workspaces/uav-crop-weed-strict-2026-11
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

| # | Screen or command | What happened | What you expected | Severity |
|---|---|---|---|---|
