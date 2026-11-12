# Decisions

One entry per decision that still shapes the code, newest first. The full
records were removed in the 2026-11-03 docs cut; each entry names the commit
history to read if you need the original reasoning (`git log --follow -- <path>`).

## 2026-11-12 — Releasing the index workspace lock waits out a file in use; an exhausted wait stays an OS error (accepted 2026-11-12; PR #230)

Found by a full-suite run on Windows: `test_two_runs_on_one_workspace_are_mutually_exclusive` failed once because `WorkspaceLock.release()` (`src/scholar_rag/replacement.py`) raised `PermissionError` (WinError 32). A refused second run reads the lock file to name its holder; Windows refuses to delete a file another handle has open, so the holder's delete failed after its replacement had completed and the lock file stayed behind.

1. **The delete is tried again, a bounded number of times.** Only `ERROR_SHARING_VIOLATION` is treated as transient: `LOCK_RELEASE_ATTEMPTS` (200) tries, `LOCK_RELEASE_RETRY_INTERVAL_SECONDS` (0.01 s) apart, about two seconds at most. No clock is read, in keeping with 7.4 ("never reads a timestamp"). A file that is already gone is a released lock. Any other failure is raised on the first try. The recovery store's release takes the same path.
2. **An exhausted wait is not a typed refusal.** By the time a run releases, it has published or refused. A typed `ReplacementError` from `release()` would travel back as a `REFUSED` result for a replacement that committed, which is a contract change (4.5 and 6.5 close the codes and the result model). So the operating system's error is raised unchanged, as before this change, and the file left behind is an orphan lock, which 7.4 already refuses like a live holder. The researcher accepted this as it is on 2026-11-12, so that case keeps no outcome of its own. What a caller sees today, unchanged by this fix: `IndexReplacement.run` raises the `PermissionError`; the index service (`src/scholar_rag/index_service.py`) reports the run as `FAILED`, naming only the error type, with no journal row; recovery is then refused `CONFLICT` by the orphan lock, so an operator has to delete the lock file by hand. The same single delete is now used when a lock's holder cannot be recorded (`acquire`'s failure path).
3. **Not covered here (follow-up).** The commit-intent deletes in `replacement.py` and `recovery.py` can meet the unlocked reader `IndexRecovery.inspect` the same way, and `release()` clears its held flag before the delete, so a second `release()` after an exhausted wait does nothing. Both predate this change.

No Contract v1 schema, code or baseline file changes. Tests: `tests/kits/rag/test_index_replacement.py` (a simulated file in use on every platform, a real open handle on Windows, the bounded wait, and no retry for another fault).

## 2026-11-12 — Protocol-change signals are flags; the hand-off accept refuses a changed search only (accepted 2026-11-12; H-protocol-signals, PR #228)

Fixes F2, F3 and F4 of the three-phase review (`docs/assessment/three-phase-hardening-2026-11-10.md`). Record: `docs/roadmap/milestones/H-protocol-signals.md`.

1. **Screening after a protocol edit is a flag, not a refusal (F2).** `GET /screening/summary` and `GET /screening/queue` carry `protocol_changed: true` when a batch of the current round was prepared under another protocol than `protocol.json` now (each batch envelope's `protocol_fingerprint` against the current canonical fingerprint); Screening Home shows the `PROTOCOL_CHANGED_SINCE_BATCH` card ("The protocol changed after screening started") with a link to Inception, and no triage button. The refusal option (`PROTOCOL_CHANGED_SINCE_BATCH` as a 409 on both reads) was not taken: the reads would stop answering while nothing was lost, the record view and conflicts still need them, and the existing behaviour that a decision bound to the current protocol is accepted stays as it was. The code is a UI state, so it is not added to `console/refusals.py`. `/prisma/preview`'s `bound_to_current_protocol` is no longer vacuous: false with no decision, and false when a current batch was prepared under another protocol. Recovery is undoing the edit, or replacing the protocol through Inception (M4d archives the screening and starts clean); Prepare cannot rebind batches because it refuses a protocol that differs from the accepted corpus's. Batches of an archived M3g round are not current, so they never raise the flag.
2. **The hand-off accept refuses a changed search, and flags any other edit (F3).** Every search run records `protocol_fingerprint` and `protocol_search` (query text, year window, language, retrieval cap, database list) in `legs.json`. `GET /discovery/runs` items and `GET /discovery/handoff` carry `protocol_changed` (the fingerprint differs) and `search_changed` (the compiled search differs). `PROTOCOL_CHANGED_SINCE_RUN` is widened from the query and years to the whole compiled search, because a change to the protocol's database list, language or cap since the run means the protocol now asks for a search the run did not do (the gate compares the protocol's list then and now, not the databases a browser run chose to search). The database list is recorded only when the protocol names one, and only the keys both records hold are compared, so a later change of the adapter's default list (F15) or a key added to the record never reads as an edit. An edit outside the search (criteria, title, research questions) is flagged but does not refuse: the records still answer the protocol's search, the accept binds them to the protocol as it is now, and no screening exists yet that the edit could invalidate; refusing would force a new harvest for a wording change. A run written before this change has no record, so its query and years decide as before. Not a Contract v1 change: `legs.json` is a run record, not a v1 artifact.
3. **The corpus view of a search corpus (F4).** `GET /screening/corpus` gains `origin`; for a browser harvest `databases` comes from the corpus run's legs and `preview` from the legs' fetched counts and `deduped.json`; in an M3g citation-searching round `origin` is `"citation_searching"` and `preview` is the chase's counts, while `databases` stays the staged exports' rows (none when round 1 was a browser harvest; the run's rows are not repeated there) and `from_discovery` keeps its value: citation searching is not a database search (PRISMA 2020 reports it under other methods) and the chase screen lists its legs. Screening Home's "imported" line shows only when `origin` is `imports`. The response keeps its keys and adds `origin` and three keys on a database row.

## 2026-11-12 — Input limits for drafts and decision events; one envelope for validation errors (accepted 2026-11-12; H-input-limits, PR #226)

Fixes F5, F6 and F7 of the three-phase review (`docs/assessment/three-phase-hardening-2026-11-10.md`). Record: `docs/roadmap/milestones/H-input-limits.md`.

1. **Every refusal carries a code (F5).** A body, query or path parameter pydantic refuses, on any console route, answers 422 `BODY_INVALID` in the refusal envelope with `details.errors[]` (`loc`, `msg`, `type`), never FastAPI's bare error list, and never the client's own value (`input`), which may be the oversized one. The UI shows one card for it with the engine's reason under it.
2. **Draft size limits (F6).** The limits live on the draft shape (`inception/steps.py`, `DRAFT_LIMITS`), not on the console body, so every route that parses a draft (create, save, steps, preview, genesis, recon) refuses the same way. They are generous for a real review and match the discovery note's 2 000 characters: 2 000 characters for each free-text answer (topic, unit of analysis, proof, title, each research question, each scope exclusion, each extra criterion); 200 for each name or label (researcher, venue, concept, synonym, matrix column, criterion id, lens, playbook, language tag); 20 research questions; 50 concepts with 50 synonyms each; 50 items in each of `out_of_scope`, `extra_inclusions`, `extra_exclusions`, `matrix_columns`; 500 criterion decisions; 20 languages; 25 seeds (the Recall limit, already in place). A draft over them is refused `DRAFT_TOO_LARGE` (422) and nothing is saved; a shape error in the same body is listed too. A draft saved before this change still loads; it is checked when it is next saved, stepped or previewed.
3. **Decision events (F7).** Intake refuses a `decided_at` more than 5 minutes ahead of the engine's own `received_at` as `PROVENANCE_MISSING` (a device clock may run a little fast, a year cannot; the event's own time is still what is stored and projected), a `device` that is not the token's scope as `INVALID_OUTPUT` (a desktop token sends `desktop`, a phone token `phone`; the alternative of overwriting `device` from the scope was not taken because the client's claim is kept as a claim, never rewritten), and a `note` that is not text or is over 2 000 characters as `INVALID_OUTPUT`. No new code was added for F7; the two existing codes cover it. The F7 limits apply to new events only: a retry of an event stored before them is still a `duplicate`. The researcher decided on 2026-11-12 that the note cap applies only to new client input: a note equal to the stored note of the event it supersedes is a copy and skips the cap, so resolving a conflict that keeps a note written before the cap succeeds and keeps the note whole (never truncated). Not a Contract v1 change: the decision event is not a v1 artifact.

## 2026-11-12 — Citation chasing: one level, capped forward legs, both directions, a second screening round (accepted; M3g-citation-chasing)

The researcher took the four recommended options on 2026-11-11 ("confirm all four as recommended"), relayed by the coordinating session; the stated defaults stand with them. Record: `docs/roadmap/milestones/M3g-citation-chasing.md`.

1. **One level per chase run.** The seeds are the published includes (`literature/included.json`, decision `INCLUDE`; `--seeds included+unclear` adds the `MAYBE` ones); what the chase finds is screened, never chased again in the same run. Chasing a later round's includes is the same command again, so saturation is reached deliberately and each round is reported. The kit's multi-hop `CitationChainer` stays a kit tool.
2. **Caps.** References (backward) are uncapped: a paper cites a bounded list. Citing papers (forward) are capped at 500 per seed and database; a leg that reaches the cap records `cap_hit` and is reported as a lower bound, as a harvest leg is. The run keeps at most 5,000 new records after deduplication; beyond that it is `PARTIAL` with a note naming how many were not kept. The protocol's year window is applied before screening and the removed count is reported (`outside_year_window`), because the frozen protocol makes the window an exclusion anyway (lesson 47). A record without a year is kept for screening.
3. **Both directions by default**, `--directions forward|backward` to restrict. OpenAlex is asked first, Semantic Scholar second, for every seed; the union is deduplicated. A seed is asked by its own id (OpenAlex work id, Semantic Scholar id, or `DOI:` on Semantic Scholar); a seed known only by DOI costs one OpenAlex lookup; a seed with no DOI and no database id is listed as not chaseable, never guessed (lesson 2).
4. **A chased batch is a second screening round, never an addition to the frozen snapshot.** Screening batches and every decision event are bound to the corpus fingerprint, and the contract makes a mismatch a closed gate, so no record can join the accepted snapshot without invalidating every decision. The accept therefore: takes the chase's new records (deduplicated against the whole corpus with the workspace's deduplicator, inside the year window) as `literature/verified.json` of round 2; freezes them as their own `corpus_snapshot` whose `inputs` name the parent snapshot (id and sha256), with the chase run named in the journal row and the rounds index; archives round 1's `literature/screening/` and its published `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json` and `prisma_screening_report.md` under `literature/screening_rounds/round_001/` (nothing is deleted, as a protocol replace archives a corpus); and records the rounds in `literature/screening_rounds/rounds.json`. Round 2 is prepared and screened in the usual place; its PRISMA report keeps round 1's published numbers in the databases arm and puts the chase in the "citation searching" arm (PRISMA 2020 item 7). Preconditions: round 1 published and current, the protocol unchanged since, the chase run from that publication. No Contract v1 schema, fixture or baseline file changes. Rejected: rebuilding one combined snapshot and carrying decisions forward (it would mint decision events the researcher never made, Compass §3); chasing only before the freeze from the protocol's golden seeds (not chasing from the includes; anchors are few; a possible cheap extra later).

## 2026-11-11 — Citation chasing comes after M4d, before the parked phases (accepted)

The researcher asked which of synthesis, the extraction matrix and the citation graph to build first. Answer taken: citation chasing (backward and forward snowballing from the includes) first, as a small discovery milestone `M3g-citation-chasing` after M4d, because it raises recall, the product's core promise, and the search kit already has the primitives. Then the extraction matrix, because synthesis without extracted data is a summary of abstracts. Synthesis after that, starting from matrix tables rather than generated prose. The graph visualisation last, if ever. The three stay parked until screening is solid with real users; only `M3g` enters the plan now (`docs/roadmap/production-plan.md` §6).

## 2026-11-11 — How M4d grounds browser inception: keys, languages, pool synonyms, anchor seeds (accepted 2026-11-11; M4d-inception-bridge)

Choices made while building M4d; the researcher accepted all six as written on 2026-11-11 ("confirm all the proposed decisions as they are"). Record: `docs/roadmap/milestones/M4d-inception-bridge.md`.

1. **The recon probe still asks OpenAlex without a key.** A probe fetches at most 25 records, which the keyless daily budget usually allows, so the probe is not refused the way a discovery run is (`OPENALEX_KEY_NOT_SET`). The leg says the key is missing (`key_set: false` and the provider's note), and a refusal (401, 403 or 409) fails the leg with `PROVIDER_REFUSED` and a note naming `SCHOLAR_OPENALEX_KEY`; the pool is then `partial` and never cached. A rejected Semantic Scholar key (403) and a throttle (429) fail their legs with `PROVIDER_REFUSED` and `PROVIDER_RATE_LIMITED`. Each leg keeps `error_code`, `notes` and `key_set`.
2. **Languages are recorded, not filtered.** The draft's languages go on the probe's query, into the pool and into its cache key, so a pool says which languages it was searched for. No database filters the probe by language today; every leg notes it. A real filter changes what the providers send for discovery too, so it waits for the provider package that owns them.
3. **A changed scope makes a bound direction stale.** A binding records the draft's question, years and languages. When any of them later differs, `check_binding` answers `SCOPE_CHANGED`, and preview and genesis refuse with `STALE_BINDING`, as for a changed pool.
4. **Pool synonyms are counts, not suggestions from a model.** For each concept, a term is offered when it occurs (1 to 3 words, stopwords dropped) in at least two of the pool records whose title or abstract contains the concept or one of its synonyms. It must not be a term of any concept, nor a piece or an extension of one. At most 10 are offered, the most frequent first. Nothing is added until the researcher ticks it.
5. **Seeds are DOIs from the pool's anchors.** The offered papers are pool records with a DOI that anchor a direction or a concept. The draft keeps at most 25 (the Recall limit), normalised and checked as DOIs. An intent without seeds compiles to the same protocol bytes as before.
6. **Replace keeps the review notes.** `synthesis/literature_review.md` is the researcher's own text and stays; everything else listed in the F1 decision moves.

## 2026-11-11 — Replacing a protocol archives its corpus; inception grounding answers (accepted; M4d-inception-bridge)

The researcher answered on 2026-11-11 in chat, taking every recommended option. Record: `docs/roadmap/milestones/M4d-inception-bridge.md`.

1. **Replace archives the corpus (F1).** When a protocol is replaced (`--replace`, or genesis with `replace: true` and the typed slug), everything that belongs to the old protocol's corpus moves into the same `audit/replaced/<stamp>/` folder as the old protocol: `literature/`, `artifacts/`, `audit/artifact_registry.json`, `.harness-console/`, and, when present, `rag/`, `extracted/`, `phase4/`, `synthesis/` and `pdfs/`. The new protocol starts with an empty corpus and can search. The `GENESIS` journal event names what was archived. The typed-slug confirmation stays as it is. Refusing replace with a `CORPUS_BOUND` code was the alternative; the researcher chose the archive, which is what "replace and back up" already promises.
2. **Continuing without a direction is recorded.** Binding "none" writes `grounding {choice: "none", grounded: false}`, so Review and `intent.json` say the protocol was not grounded (spec 03 Q1).
3. **The gap check is left out of the M4d screens.** The `delta` route stays for MCP. It merges follow-ups into a new pool, and the synonyms and seeds are drawn from that pool (spec 03 Q2).
4. **Defaults for the remaining spec questions:** no custom lexicon in the browser (02 Q1); the contact email is still set outside the app (02 Q2); the engine reports `scope_changed` when the draft's question, years or languages differ from the pool's, and a changed scope marks a bound direction out of date (02 Q3, 03 Q3); a read-only check says whether the researcher's own phrase occurs in the pool before binding (03 Q4); anchor seeds are kept in the draft, compiled into `search_strategy.golden_seeds` at genesis, and pre-filled on Recall with source "Anchor" (replaces 2026-11-10 discovery answer 3).

## 2026-11-11 — Autonomy ladder amended: the gate counts includes, and the agent is never shown outcome statistics (accepted)

The researcher approved two corrections to the 2026-11-10 ladder entry below, both from `docs/lessons/2026-10-17_uav_harvest_calibration_lessons.md`, which the first design did not use. (1) Lesson 35: the UAV corpus was about 98.7% excludes, so the gate's "100 records compared" held one or two includes and its recall interval meant nothing. The gate now counts the researcher's blind includes (an Unclear counts as an include): L1 needs at least 35 compared with a 95% Wilson lower bound on include recall of at least 0.90; L2 needs 75 and 0.95. Agreement and Cohen's κ are shown, never gated on. At a 2% include rate L1 needs about 1 750 records screened first; on a sparse corpus it may never unlock, by design. (2) Lesson 54: a disclosed exclusion prior flipped blind Unclear judgments to Exclude, so at every rung the agent's prompt carries no outcome statistics and no database of origin, any new prior passes a blinded A/B test measured on the Unclear-preservation rate, and the L1 audit reports the agent's Unclear rate beside its misses. Design: [`architecture/agent_autonomy_ladder.md`](architecture/agent_autonomy_ladder.md) §4.

## 2026-11-10 — A Semantic Scholar key that is rejected fails the leg; no silent keyless fallback (proposed; M3h-providers)

Until now a 403 on `SCHOLAR_S2_KEY` retried the bulk search keyless with only a warning log, so a bad, quoted or pruned key was invisible and the report could not say which pool served the leg. Now a 401 or 403 fails the Semantic Scholar leg with `PROVIDER_REFUSED` and a note naming `SCHOLAR_S2_KEY` (the other databases still run, the run is `PARTIAL`); to search keyless the researcher unsets the key. `GET /discovery/plan` reports `s2_key_set` and the Plan screen says "Set, not yet verified", because the plan sends nothing. The key stays optional: the bulk endpoint runs keyless. The abstract hydrator's one keyless retry is unchanged (a follow-up). Evidence: `docs/kits/search/PROVIDERS_2026-11.md` §3a.

## 2026-11-10 — OpenAlex needs its API key: a browser run that selects OpenAlex refuses without it (proposed; M3h-providers)

OpenAlex has required an API key since 2026-02-13 (keys only; the email parameter is gone; keyless calls share a small daily budget per IP, then 409; cursor paging past page one answers 401). The search kit stops sending `mailto` to OpenAlex. `POST /api/v1/discovery/runs` refuses with the new code `OPENALEX_KEY_NOT_SET` (409), after `MAILTO_NOT_SET` and before any request, when OpenAlex is among the run's databases (the body's `providers`, else the protocol's) and `SCHOLAR_OPENALEX_KEY` is unset; `GET /discovery/plan` reports `openalex_key_set`, and the Plan screen prints the line to set as it does for the contact email. The key stays an environment variable, like the email (decision 2026-11-08): the browser writes no settings file. Not gated: the engine and the CLI `run` (a keyless OpenAlex leg fails with `PROVIDER_REFUSED` and a note naming the key, and the other databases still run), and recall checks (a DOI lookup per seed fits the keyless budget). An OpenAlex 401, 403 or 409 keeps `error_code: PROVIDER_REFUSED` and adds that note. Record: `docs/roadmap/milestones/M3h-providers.md`; findings F12 in `docs/assessment/three-phase-hardening-2026-11-10.md`.

## 2026-11-10 — Agent autonomy ladder: the agent earns each rung on the researcher's own decisions (accepted; design, not yet built)

The screening agent stays a proposer by default (rung L0, today's behaviour). Two gated modes are added: "Agent screens, you audit" (L1: the agent's EXCLUDE proposals stand as decisions; the researcher decides every agent INCLUDE, every Unclear, and a random audit sample of 60 agent excludes) and "Autopilot" (L2: every record the agent could decide; Unclear stays with the researcher; typed acknowledgement at publish). A rung unlocks only through a calibration on the researcher's own blind decisions of this review: L1 needs at least 100 compared (the whole corpus under 200 records, never fewer than 50), include recall ≥ 0.95, 95% CI low ≥ 0.90, at most 2 missed includes; L2 needs 200, ≥ 0.98, ≥ 0.95, ≤ 1. L2 is designed but built only after the screening agent has been measured on the IEEE corpus. Provenance: one `AGENT_ADOPTED` decision event per record, minted by the engine only (never accepted from a client), carrying the proposal id, the mode, the calibration run and the human who set the mode; a Contract v1 change through the baseline gate and an independent review. A protocol change drops the review to L0 and invalidates the calibration. A missed include found in the audit is reported on Home and in the methods paragraph; the researcher, not the engine, decides whether to drop the mode. The methods paragraph states the classifier, the mode, the calibration numbers and the audit result. The existing `ai_agreed_exclusion` setting, which no code acts on, is retired. A bounded discovery assistant (synonyms, translation explanations, recall repair) is proposals into the protocol, no autonomy. Milestones M9a-measure, M9b-ladder-engine (RELEASE), M9c-ladder-ui, M9d-discovery-assistant, none before M3c-screens lands. Design: [`architecture/agent_autonomy_ladder.md`](architecture/agent_autonomy_ladder.md).

## 2026-11-10 — Discovery API: what the packet left open (proposed; M3b-api)

Twelve points the discovery API packet did not settle, decided while building M3b-api; each is listed with its packet section in `docs/roadmap/milestones/M3b-api.md` "Decisions". The ones that shape later work: a researcher's cancel (and a console shutdown) stops the harvest only, archives the run `PARTIAL` with its records in the run folder, and builds nothing from it; the methods draft is rendered on read and never stored, the reviewed text is stored per run; a run is `stale` once a later run's records became the corpus; `PROVIDER_UNKNOWN` (422) is a new code; a leg failure that is not a provider answer has no `error_code`; `run_pipeline` gains optional keyword hooks, the CLI and orchestrator calls are unchanged.

## 2026-11-10 — Discovery screens: ten answers that close specs 01–08 (accepted; M3c-screens)

The researcher took every recommended answer on 2026-11-10 ("all recommended"). The specs are `docs/ux/phase1-discovery/final/01-plan.md` to `08-handoff.md`; the record is `docs/roadmap/milestones/M3c-screens.md`.

1. `/discovery/` is a short status page (step bar, one line per step from the routes, "Continue at …"), not a redirect: a running harvest stays visible.
2. A protocol change from discovery is a sentence and a link to the inception drafts screen; no one-click amendment until the replace path is reachable from the browser (deferred).
3. Recall seeds are the researcher's own (DOI or arXiv id); inception's anchor papers wait for an engine item that records them in the workspace (deferred).
4. Duplicates says that records the rules did not prove to be one work stay separate works.
5. The share removed is shown as a percentage; the written fraction is under Details.
6. A reviewed methods text can be edited; the save warns that it will no longer be marked reviewed.
7. The methods text of the latest run can be reviewed after the corpus is accepted (it is not part of the frozen corpus); older runs stay read-only.
8. "Hide the database of origin while screening" is cut: the existing blinding hides the agent's proposal, not the origin; a future screening setting with its own spec.
9. "Fill missing abstracts" is cut: the hand-off shows how many records have an abstract; a hydration field only if testers ask.
10. Failed databases are reached from the hand-off through the report in M3c; naming them in the hand-off answer is a small engine follow-up (deferred).

Also decided in the milestone, not asked: the primary navigation is Workspaces · Discovery · Screening (Inception is not a navigation entry today).

## 2026-11-10 — A browser harvest does not freeze the corpus; the hand-off screen does (accepted; M3b-api, engine change in M3d-engine)

The researcher chose this on 2026-11-10 (option a of the M3b-api open question): "I press Accept on the hand-off screen". A search run started from the browser stops after deduplication and verification; it builds no corpus snapshot and prepares no screening batches. The corpus is frozen only by the hand-off screen's accept, the existing `POST /screening/corpus/accept`. Until then another harvest is allowed; an import is allowed only before any harvest (researcher, 2026-11-10, in M3d-engine: "Keep the rule for now, combine later"; `VERIFIED_EXISTS` keeps a harvest and imports apart, and one snapshot from both, deduplicated together, is M3f-combined-corpus, a RELEASE-lane milestone of its own because it changes the snapshot's inputs). The CLI `scholar-harness run` is unchanged (it still accepts the snapshot at the end of a run, as since M3a). The engine change (the browser run skipping `_accept_run_corpus` and the screening prepare) is M3d-engine, not M3b-api: in M3b-api a successful browser run still accepts the snapshot as M3a does. Built in M3d-engine: the browser run ends `PENDING_CORPUS_ACCEPT` with `corpus_snapshot` `NOT_ACCEPTED`, and the accept builds the artifact the CLI run's accept step builds from the same records (`docs/roadmap/milestones/M3d-engine.md`).

## 2026-11-10 — Discovery over HTTP: seven decisions for the Phase 1 screens (accepted; discovery API packet)

The researcher chose these on 2026-11-10, each explained in plain terms and taken one by one. The packet is `docs/architecture/research_ui/DISCOVERY_API_PACKET.md`.

1. **A harvest started from the browser runs inside the console process**, as recon does, so each database's progress is reported record by record. Closing the console stops the run; what was fetched is kept as a `PARTIAL` run. Not chosen: a subprocess job with a log poll (coarse progress).
2. **Near-twin pair review waits.** The first Duplicates screen shows counts per rule (identifier, exact title, fuzzy title). Whether pair-by-pair review is built is decided after the researcher's own corpora show how many near-twins survive. It would change the snapshot's inputs, so it is a RELEASE-lane milestone of its own.
3. **The recall check never rewrites the query.** It reports found or not found per database against the frozen protocol's query; a miss is recorded and never blocks the harvest; the fix is a protocol amendment through inception. The terminal tool's "heal" stays off the console.
4. **The plan shows the exact string each database will receive before the run.** Every provider exposes its translation without a request; a test pins the preview equal to the replayed golden legs.
5. **The contact email stays `SCHOLAR_MAILTO`.** On `MAILTO_NOT_SET` the screen prints the line to set and offers Retry; the browser writes no settings file. Revisit after testers.
6. **No CSV import** until a tester brings a CSV-only export. RIS and PubMed `.nbib` remain the formats.
7. **A per-run cap override is allowed from the browser**, recorded as `run_override` on every leg and in the report; the plan shows only the protocol's cap.

## 2026-11-09 — Recon over HTTP: one session store, pools that say what failed, anchors by occurrence (proposed; M4c)

Proposed by the M4c session. The researcher accepts or changes it at the PR.

- **One recon engine.**
  - The recon session store moves from `scholar_agent/server.py` to `scholar_harness/recon/session.py`.
  - The CLI wizard, the MCP `recon_*` tools and the console routes all probe through it, on the M3a `SearchEngine.run`. The MCP tools reach it through the adapter (`make_sessions`, adapter 1.1).
  - `MAILTO_NOT_SET` is a refusal at every door, before any request.
- **What a pool keeps, and what is cached (INC-09).**
  - A pool records one leg per provider and a status: `complete`, `partial` (a leg failed) or `empty`.
  - Only a complete pool is cached.
  - A partial pool is used and says which provider failed, but it is searched again next time.
  - An empty pool never becomes the session's pool.
  - `refresh` searches again.
  - `created_at` is shown in every probe answer, in the grounding and in the GENESIS summary.
- **Anchored means observed (INC-21).**
  - A paper anchors a term only when the term occurs as whole words in its title or abstract. Case, hyphens and punctuation are ignored, and there is no stemming.
  - "Hits returned" is kept apart from "observed in".
  - `compute_apr_observed` measures occurrence.
  - The topic is anchored only where it occurs.
- **Grounding lives beside the draft.**
  - `bind` writes `grounding` on the draft record, never inside `draft`. A client save cannot forge or drop it, and a draft without recon is unchanged, so no migration is needed.
  - `STALE_BINDING` means that the session's latest pool is not the bound pool.
  - Per-RQ evidence is computed at preview and genesis, because the RQs are written after the direction is chosen.
- **A pool under 12 papers binds only with consent.** `bind` refuses `POOL_TOO_SMALL` unless `accept_thin_pool` is set (INC-28 for the HTTP route). The CLI wizard still only prints a note.
- **No new search at genesis.** The CLI wizard searches each concept and synonym (budget 3). The HTTP flow does not search again at genesis. Preview shows each concept's occurrence in the bound pool and `apr_observed` instead.
- **The contact email** is the console process's `SCHOLAR_MAILTO`, from the environment or `.env`. There is no in-app setting yet, and the screens say how to set it.
- **Recon jobs** are kept in memory by the console process. A restart loses the job records, not the results: every probe is in the session store.
- **A direction needs its concept in two papers.** Over HTTP a direction is offered only when its concept occurs in at least two titles or abstracts, and its anchors are those papers. The wizard's "pool vocabulary" fallback (prior finding 9), which joins unrelated terms, is therefore not offered there. The CLI wizard keeps it.
- **The suite runs offline.**
  - `tests/conftest.py` refuses any non-loopback socket connect unless `NEXUS_RECORD_CASSETTES=1` or `NEXUS_ALLOW_NETWORK=1` is set.
  - It sets `HF_HUB_OFFLINE` for the RAG tests' cached embedding model. The guard found three RAG tests that reached the Hugging Face Hub on every run.
  - CI fetches `all-MiniLM-L6-v2` in a step before pytest.
- **The golden recon cassette** was recorded once, on 2026-11-09, with the researcher's approval and contact address. That address is filtered out and is not in the file. Semantic Scholar answered HTTP 429 (no API key). The cassette keeps that partial answer, so the replay proves INC-09 on real responses.
- **Lane.** RELEASE: the milestone changes public HTTP and MCP answers and what the recon cache persists.

**Not chosen:**
- Grounding inside the draft: a client could forge it.
- A TTL on cached pools: complete pools stay reusable, `created_at` shows their age, and `refresh` replaces them.
- Running the console's probes through the subprocess `JobRunner`: a recon probe runs in-process and has no CLI action.

## 2026-11-09 — The inception write gate names every file, and a draft keeps its backup (accepted; M4b)

The researcher chose this on 2026-11-09, closing the open questions of the inception specs 06, 07 and 08 before the screens were built.

- **The preview lists every file genesis writes.** `POST /inception/preview` answers `files` with the files of a new workspace (`NEW_WORKSPACE_FILES` in `inception/emit.py` plus `SUPPORT_FILES` in `inception/genesis.py`), or, when the target already holds a workspace, the files a replacement rewrites and its backup folder (`REPLACEMENT_FILES`). It used to name four files, so the write gate under-promised. `test_preview_names_every_file_genesis_writes` runs both geneses and compares.
- **A draft keeps the backup.** The draft's `emitted` record now also holds `backup_dir` and `previous_fingerprint` when genesis returns them, so the Done screen shows them after a reload.
- **Blank drafts and resume.** "Start a new review" always creates a draft; a draft with no title and no topic is listed as "Empty draft" (the browser cannot discard drafts: DELETE is not carried). Resume opens Scope.
- **Lane.** The two engine changes alter public HTTP answers, so M4b is RELEASE (`test_gate_policy.md` §lanes), not the STANDARD it started as.

**Not chosen:** showing the four-file list verbatim and deferring the engine change (the gate would keep under-promising); keeping the backup only in the browser tab (lost on reload); reusing an untouched draft (a frontend rule about what counts as untouched).
## 2026-11-09 — Triage is a focus screen on desktop: its own top bar, a counts rail, no filter chips (accepted; M8-triage)

The researcher chose this on 2026-11-09, after trying the first M8-triage build: "I want the triage the full viewport like the screenshots", and "I don't like those buttons" (the step bar and the queue's view chips).

**The decision.** From 1024 px the triage route is a focus screen, as in the redesign mockup:
- the site header and the screening step bar are not shown there; one slim triage bar takes their place, with the product name, "Triage" (the page's h1), the position line with a progress strip, and Queue (J/K), Help (?) and Leave triage (a link to screening Home);
- the queue column becomes a counts rail (need you, decided, skipped in this session) over the current and next titles; the whole queue opens from Queue or J/K, and its view is chosen from one dropdown instead of five chip buttons.

Below 1024 px nothing changes: the site header, the step bar and the stacked layout stay. On the desktop triage screen the language and theme menus are therefore one step away, on any other screen.

**Not chosen:** keeping the site header with a compact step bar (the first M8-triage build).

## 2026-11-09 — Triage: the checklist is a tool for the reason, not a gate for the decision (accepted; M8-triage)

The researcher chose this on 2026-11-09, after screening real IEEE records: the long checklist had to be answered for every record before Include was possible.

**The decision.** The checklist is collapsed by default. The screen shows the record and the three decision buttons.
- **Include** needs no answers. It is turned off only while an answer the researcher gave fails a criterion (an inclusion answered no, an exclusion answered yes, or an inclusion answered "not reported" under the protocol's `exclude` policy), so a decision never contradicts its own answers.
- **Exclude** is always available. It needs a reason. The reason is pre-selected from the first failed criterion when the answers give one; otherwise the reason chips are offered with none chosen.
- **The checklist opens** on E, to pick the reason, on a number key (1/2/3 answer the focused criterion), or on demand with its toggle.
- **Absent answers stay absent** in the event. They are never auto-filled and never sent as `not_reported`.

**Engine:** no change. `criteria` is optional in the decision-event contract, an EXCLUDE still carries `EXC-n` or `FAILS-INC-n`, and `REASON_CODE_INCONSISTENT` still refuses a reason that contradicts an answered criterion.

**Not chosen:** the inclusion criteria as one compact row of chips with Include still gated on every inclusion yes, and the two combined. Both keep the checklist as a gate.

## 2026-11-09 — The methods paragraph does not count decisions made without per-criterion answers (accepted; M8-triage)

The researcher chose this on 2026-11-09. The exported methods paragraph is unchanged by M8-triage. Each decision event still records which answers were given, so the count can be added later from the events.

**Not chosen:** a sentence such as "n decisions were recorded without per-criterion answers" in `screening/export.py`.

## 2026-11-09 — The triage screen fits 1440×900 and 1280×720 without page scroll (accepted; M8-triage)

The researcher chose this on 2026-11-09. At both viewport sizes the triage page never scrolls; a long abstract, the open checklist and the expanded queue scroll inside their own panes. Playwright checks `document.documentElement.scrollHeight <= innerHeight` at both sizes with a long abstract.

**Not chosen:** 1440×900 only, which would leave laptop screens scrolling.

## 2026-11-09 — An additive import format is a STANDARD-lane change (accepted; M5c-nbib)

The researcher chose this on 2026-11-09, asked at the review of M5c-nbib (PubMed MEDLINE `.nbib` import beside RIS).

**The question.** `test_gate_policy.md` §lanes lists public API and CLI semantics as RELEASE, and M5b (the RIS import, the same surface) was RELEASE. M5c-nbib widens `POST /corpus/sources` and `--ris` to a second file format and adds a `format` field to the source rows; the reviewer read that as RELEASE.

**The decision.** A new import format that leaves identity, the contract, the `verified.json` row shape and every existing input's behaviour unchanged is STANDARD: the pr gate once on the final executable commit, the contract check, and an independent review. The closure-stage extras (schema and two-study fixture checks, wheel build) were run and recorded for M5c-nbib anyway, so the evidence covers either lane.

**Not chosen:** relabelling the milestone RELEASE (no extra evidence would have been produced); treating every route widening as RELEASE by rule (the policy's RELEASE line is for changes to what existing inputs mean, which this is not).
## 2026-11-08 — Re-inception: refuse without `--replace`, back up, confirm a screening binding (accepted; M4a, INC-08)

The researcher chose this on 2026-11-08.

**One gated write path.** `scholar_harness.inception.emit.emit_workspace` is the only code that writes an inception protocol into a folder. The CLI wizard, `nexus-scholar init` (with and without `--scaffold-only`), the workspaces API, the inception HTTP route and the inception-agent helper `emit_protocol.py` all go through it. It compiles the intent before writing, so an invalid intent writes nothing.

**The guard:**
- **No `--replace`.** A folder that already holds a workspace (any `INIT_MARKERS` file) is refused with `WORKSPACE_EXISTS`, and nothing is written. The wizard checks as soon as the title gives the slug, then checks again at the write.
- **`--replace`.** It copies `protocol.json`, `intent.json` and `SCREENING_CRITERIA.md` to `audit/replaced/<UTC stamp>/` before writing. `project.json` is kept: `created_at`, `stats`, `registered_workspace_id` and `project_id` stay. Only the fields the new protocol states are refreshed: title, paradigm, research questions and `updated_at`. GENESIS names the old fingerprint and the backup path.
- **A screening binding needs a second, explicit confirmation.** Screening decisions are counted from the event log lines and the `batch_NNN_decisions.json` files, and a publication from `literature/screening/generation.json`. With any of these, `--replace` alone is refused with `SCREENING_BOUND`, and the refusal gives the counts.
  - **Mechanism:** on the CLI and in the skill helper, the extra flag `--discard-screening-binding`. Over HTTP, the body must also carry `confirm_discard_screening_binding` equal to the workspace slug, typed by the researcher.
  - GENESIS records that the binding was discarded, with the counts.

**What does not change:** the protocol compiler, the fingerprint rules and the screening data. The old decisions stay on disk, and they still refer to the old criteria, which are kept in the backup.

## 2026-11-08 — Inception criteria are shown verbatim and accepted one by one (accepted; M4a, INC-22)

The researcher chose this on 2026-11-08.

- **Every criterion is shown verbatim, with its source, and accepted one by one.** The source is one of: written by the wizard from the proof answer; the paradigm's default exclusion, written by the wizard; the researcher's out-of-scope answer; typed by the researcher.
- **A criterion the wizard wrote needs an explicit yes.** Its prompt defaults to no. A criterion the researcher typed defaults to yes.
- **A rejected criterion is not compiled.** The rationale's "Explicitly out of scope" sentence names only the accepted out-of-scope items.
- **An empty side is filled by asking.** If either side would be left empty, the wizard asks the researcher to write a criterion, because `IntentPacket` needs at least one inclusion and one exclusion criterion.
- **The pre-emit panel lists every accepted criterion in full**, not as counts.
- **The source is not stored in the protocol.** Storing it would be a contract change. It appears in the wizard and in the step API output.
- **The deterministic `--scaffold-only` placeholder protocol keeps every drafted criterion,** so its fingerprint does not move.
- **The agent path follows the same rule.** The inception-agent skill must show each criterion and get a per-criterion yes before it writes `intent.json`.

## 2026-11-08 — Inception drafts live under the workspaces root, with one session id (accepted; M4a, screens 00 and 08)

The researcher chose this on 2026-11-08.

- **Where drafts live.** A draft of the web wizard is saved at `<workspaces root>/.drafts/<session id>/draft.json`. A draft is the researcher's work, not a cache. The recon cache root defaults to `<repo>/.cache`, which does not fit a PyPI install.
- **The workspace list ignores drafts.** It skips folders whose name starts with a dot.
- **The session id** is `rec_` followed by 32 lowercase hex characters, the format the MCP recon sessions already use. The grounded CLI wizard uses it too (it used 12 hex characters). One id now names a draft and its recon session. The recon pools stay in the canonical recon cache.

## 2026-11-08 — The retrieval cap is a protocol method key (accepted; M3a-discovery, SRCH-31)

The researcher chose this on 2026-11-08.

**The key.** The protocol's `method` block gains an optional `retrieval_cap`: a positive integer, the most records fetched from one database for one query. When the key is absent, the protocol sets no cap: each database is paged until its reported total is reached.

**A safety ceiling still exists** in the engine, so a runaway query cannot fetch a million records. It is not a protocol value. When a leg stops at the protocol cap or at the ceiling, that leg reports `cap_hit: true`, the cap that applied and where it came from (`protocol` or `engine_ceiling`). The PRISMA-S report and the journal state it per database. A cap is never silent.

**`search_strategy.target_candidate_pool_size`** stops being a retrieval cap. Today its `max` (default 100) silently capped every provider (`protocol_adapter.py`). It stays in the protocol as an advisory planning figure and changes no retrieval.

**Fingerprint.** An absent `retrieval_cap` is left out of the canonical JSON, like an absent `reporting`, so no existing protocol's fingerprint changes. New workspaces do not write it (no cap is the default).

**Contract v1.** The protocol model is not in the contract baseline; `generate_contract_baseline.py --check` decides. The protocol JSON schema is regenerated by `scripts/generate_protocol_schema.py`.

**Not chosen:** reinterpreting `target_candidate_pool_size` as the cap (a misleading name); a run-time setting only (the signed protocol would not state the cap).

## 2026-11-08 — A live search needs a real contact email (accepted; M3a-discovery)

The researcher chose this on 2026-11-08.

Crossref, OpenAlex and NCBI ask for a contact address on each request (the "polite pool"). The default was a placeholder, `student@university.edu` (`scholar_search/config.py`), sent on every request on the user's behalf.

- The placeholder is removed. `SCHOLAR_MAILTO` (or `mailto` in the `.env`) has no default.
- A live search refuses before any request with the typed refusal `MAILTO_NOT_SET`, naming the setting to fill.
- What does not need it: `--help`, imports, dedup, the golden search replayed from cassettes (the test sets a placeholder, and the cassettes filter it out), and every offline path.
- Each search leg records whether a contact address was sent (`mailto_set: true`), never the address itself.

**Not chosen:** warn and run anonymously; leave the placeholder.

## 2026-11-08 — One live golden search, frozen to cassettes (accepted; M3a-discovery)

The researcher allowed one live search on the golden UAV protocol, against the free providers (OpenAlex, Crossref, PubMed, Semantic Scholar, arXiv), to record the VCR cassettes the golden search replays from. The cassettes are committed with the contact address and any API key filtered out. After that, every test replays offline; re-recording is a deliberate, separate step.

## 2026-11-08 — Reporting follows a guideline chosen in the protocol (accepted; plan step 11)

This accepts the 2026-11-06 consequence that screening is not specific to systematic reviews. The researcher chose the options below on 2026-11-08.

**The key.** The protocol's `method` block gains an optional `reporting` key, with three values: `prisma-2020`, `prisma-scr` or `none`. When the key is absent, or the protocol has no block at all, the guideline comes from `playbook_type`:

| Playbook type | Guideline |
| :-- | :-- |
| `PRISMA_SLR` | `prisma-2020` |
| `RAPID_EVIDENCE` | `prisma-2020` (rapid reviews usually report against PRISMA 2020) |
| `STUDENT_DISSERTATION` | `prisma-2020` |
| `SCOPING_REVIEW` | `prisma-scr` |
| `DESIGN_SCIENCE` | `none` (no systematic-search claim) |

A protocol may still set any of the three values to override this.

**Fingerprint.** An absent `reporting` is left out of the canonical JSON, the same way an absent block is. So no existing protocol's fingerprint changes, including protocols written with the M7-method block. New workspaces write the derived value into their block, so the signed protocol states it.

**What the guideline changes.** Only the labels and one sentence.
- **Screen labels name the guideline.**
  - Publish's preview reads "PRISMA 2020 screening preview", "PRISMA-ScR screening preview" or "Screening preview".
  - Export's counts heading reads "PRISMA 2020 counts", "PRISMA-ScR counts" or "Screening counts".
  - Export's language note names the matching flow diagram, or "your flow diagram".
- **The methods paragraph adds one sentence after the source sentence:**
  - `prisma-2020`: "The screening is reported following PRISMA 2020."
  - `prisma-scr`: "The screening is reported following PRISMA-ScR, the PRISMA extension for scoping reviews."
  - `none`: no sentence.
- **`figures.method.reporting` and `figures.method.reporting_source`** carry the value and where it came from: `protocol` or `playbook`, or `defaults` when there is no readable protocol (review, 2026-11-08). **`figures.method.reporting_label`** carries the name the sentence states ("PRISMA 2020", "PRISMA-ScR", or null for `none`), so the number in "PRISMA 2020" traces to a figure.

**What does not change:**
- The counts, their meaning and the counts sentence.
- The engine and the rule table.
- The published file `prisma_report.json`. It is a publication artifact that digests and currentness checks depend on, so it keeps its name under every guideline.

**Not chosen:**
- Always deriving from `playbook_type`, which would leave no way to override it.
- PRISMA-ScR's "sources of evidence" wording in the counts sentence and labels. It is deferred to the parked PRISMA-ScR checklist work.
- Renaming `prisma_report.json`.

## 2026-11-08 — Method parameters move into the protocol (accepted; plan step 10)

Accepts point 2 of "Three kinds of parameter" (2026-11-06) with the researcher's choices of 2026-11-08.

**The block.** `protocol.json` may carry an optional `method` block:

```json
"method": {
  "dedup": { "doi": true, "title_similarity": 0.97, "first_author": true, "year_tolerance": 1 },
  "rules_version": "screening-rules-v1",
  "not_reported": "unclear",
  "blinding": "reveal_after_decision"
}
```

**What goes in:** four values, the ones that can change what is included or how biased the screening is:
- the dedup tiers;
- the rule-table version;
- the not-reported policy;
- blinding.

Batch size stays a Prepare setting, because it only changes how the work is chunked.

**What a review may change, and the checked limits.** The protocol validator refuses anything outside these limits (`PROTOCOL_METHOD_INVALID`):
- `title_similarity`: 0.90–1.00.
- `year_tolerance`: 0–2.
- `doi`: always true.
- `first_author`: true or false.
- `rules_version`: a version the engine knows (today only `screening-rules-v1`).
- `not_reported`:
  - `unclear` (today's rule): any criterion not reported gives Unclear, which goes to full text.
  - `exclude`: an *inclusion* criterion not reported gives Exclude with `FAILS-INC-n`.
  - In both cases an *exclusion* criterion not reported never fails, as today.
  - The choice applies to the agent's drafts and to the reason the screen offers. A researcher's own decision is never overridden.
- `blinding`: `reveal_after_decision` or `show`. When the protocol sets it, the Prepare control shows the value and does not change it; the refusal is `BLINDING_SET_BY_PROTOCOL`.

**Fingerprint.** The block is optional, and when it is absent it is left out of the canonical JSON, so the fingerprint of every protocol without a block is unchanged. A protocol with the block hashes it, so the signed protocol covers these values. New workspaces are written with the block, filled with today's values.

**Existing workspaces** are left as they are. Without a block the defaults apply (today's values), decisions and fingerprints are untouched, and the methods paragraph names the defaults it used. There is no adopt command. Adopting the block means re-inception or a new workspace.

**Methods paragraph.** The paragraph reads the values in force (the block, or the defaults) and says which source it used.

**Contract v1.** Adding an optional field to the protocol schema is decided by `generate_contract_baseline.py --check`, not by convenience. If the check moves, this entry is the architecture decision the gate requires. The work then also needs:
- regenerated schemas and golden fixtures;
- a negative regression test (a protocol without the block keeps its exact fingerprint; an out-of-range value is refused);
- independent review.

**Not chosen:**
- An always-serialized default block. It would have changed every existing fingerprint.
- Environment variables. They are invisible to the hash.
- Batch size in the block. It does not change outcomes.
- An adopt command for existing workspaces.

## 2026-11-07 — Details on demand (M6-beta)

Each screening screen shows only what the researcher acts on. Identifiers and proofs sit
behind one "Details" disclosure per card. The disclosure is closed by default, reachable
from the keyboard, and has the same label on every screen. This is the brand book's "plain
words first, raw value underneath", read as: the raw value is one disclosure away, never
inline.

**Moved behind Details:**
- study ids and the raw form of DOIs;
- protocol and batch fingerprints;
- generation ids and fingerprints;
- event ids, run ids and prompt hashes;
- the "Recorded as you · HUMAN · time · protocol sha" line (the card keeps "Saved", with the time on hover);
- refusal codes (the plain sentence stays on the card);
- batch file names on Home and Publish.

Nothing leaves the DOM, so the provenance checks in Playwright still find every value. The
list for each screen is `docs/ux/phase2-screening/final/12-details-disclosure.md`.

## 2026-11-07 — Answer until decisive (M6-beta)

The desktop checklist no longer has to be filled in full before a decision.
- **Exclude** is enabled as soon as one criterion fails: an inclusion criterion answered
  no, or an exclusion criterion answered yes.
- **Include** needs every inclusion criterion answered yes and no exclusion criterion
  answered yes.
- **Unclear** is always enabled.

A criterion left unanswered is stored as absent from the event's `criteria`. It is never
recorded as `not_reported`, because that would claim the reviewer looked and found nothing.

The screening contract does not change: `criteria` is already optional, and the engine
validates only the reason code. On Exclude, the reason is pre-selected as the first failed
criterion in protocol order, so E then Enter excludes. An engine refusal,
`REASON_CODE_INCONSISTENT`, guards the case where an Exclude's reason code names a criterion
that the same event answers the other way.

## 2026-11-07 — Advance on decide, as a workspace setting (M6-beta)

After a decision, triage moves on in one of two ways, chosen per workspace on Prepare:
- **"show the draft, then N"** (the default): if the record has a draft, the revealed
  state shows and N advances. If it has no draft, the next record opens at once.
- **"move on at once"**: the next record always opens at once, and drafts stay in each
  record's details.

The setting is stored with the other screening settings (`GET/PUT /settings`) and journaled
as `SCREENING_SETTINGS_CHANGED`. The methods paragraph reports it only when it changed what
the reviewer saw, that is, when drafts were skipped.

## 2026-11-07 — Published means current (M6-beta)

A screening reads "Published" only while the published generation still matches the
decision files. The publication gate (`require_current_generation`, or one wrapper that
`/ui/publication-status`, `/summary`, export and methods all call) also checks
`stale_projections`. A decision recorded after publish makes every surface read
`GENERATION_STALE`, naming the stale batches or the number of changed studies.

Stored files and the Contract-v1 artifacts do not change; only the status that is read
changes. If the change turns out to alter stored semantics, it stops as
`BLOCKED_BASELINE_DRIFT` and the lane escalates to RELEASE. This closes the currentness gap
that M5-slim deferred (review T-P1-1).

## 2026-11-07 — The beta's parked list (M6-beta)

The researcher's plan of 2026-11-07 sets the order: every step before the first testers
shortens a tester's path to a good first hour, and every step after them is driven by what
they report.

**Parked until a tester asks:**
- the 1,644-record prompt gate (it measures agreement with earlier AI labels, review S-P0-2);
- the second-screener lane;
- the phone (M2);
- the live audit view;
- the PRISMA-ScR checklist rewrite;
- full text, extraction, synthesis, graph and verify.

**After the first testers:**
- the Windows pytest job, once the suite runs in under ten minutes or there is a second
  maintainer;
- the hardening pass (atomic writes, `os.replace` retry, `/healthz`, dead routes and client
  functions);
- the parameters decision, acted on between tester rounds because it changes the protocol
  fingerprint of new workspaces;
- reporting as a guideline switch keyed from `playbook_type`.

The beta is tagged `v1.1.0b1` only after the version fix, so the GitHub Release and its
wheel carry the same version, and nothing named 1.0.0 is published under a beta tag
(researcher, 2026-11-07).

## 2026-11-06 — Three kinds of parameter, and where each lives (proposed; point 2 accepted 2026-11-08, see "Method parameters move into the protocol")

The researcher raised it on 2026-11-06: values are encoded throughout the
project, screening may not be specific to systematic reviews, and the stages
may one day be composed by the researcher. A survey of the harness found
about 35 module-level numeric constants, five `NEXUS_*` environment
variables, and pydantic-settings classes in three kits. Most of the constants
are floors or contract limits; the problem is not their number but that three
kinds of value are mixed with no rule. The rule:

1. **Invariants stay in code.** Security floors and contract limits: pairing
   code length and lifetime, the launch code's two minutes, 200 events per
   request, the 50 MB import cap, the approver name length. They are not
   preferences; changing one is an architecture decision. They are listed
   once, with their floor and the reason, in
   `docs/architecture/DEVELOPER_COMPASS.md`, and nowhere else.
2. **Method parameters live in the protocol.** Anything a reviewer could ask
   "how did you …" about belongs in `protocol.json`, under a `method` block,
   versioned and covered by the protocol hash, so the researcher signs it and
   the methods paragraph reads it from the same place. Today these are in
   code: the deduplication tiers (exact DOI, then fuzzy title at 0.97 with
   first-author match and a year tolerance of ±1, `scholar_search/dedup.py`),
   the screening rule table and its version (`screening-rules-v1`,
   `screening/proposals.py`), the "any criterion not reported means Unclear"
   policy, the default batch size (20), and the blinding default
   (`reveal_after_decision`). The current values become the defaults a new
   protocol is written with, so nothing changes for a workspace that says
   nothing. A workspace that adopts the block gets a new protocol fingerprint,
   like any amendment; existing workspaces keep theirs until re-inception.
   Whether adding the block is a Contract v1 change is decided by
   `generate_contract_baseline.py --check`, not by convenience: if the check
   moves, stop and decide.
3. **Operator preferences live in the workspace settings and the keychain.**
   Provider, model, cost ceiling, queue order, advance-on-decide, theme,
   workspaces root. They are journaled when they affect provenance (as
   `SCREENING_SETTINGS_CHANGED` already is) and never hashed into the
   protocol.

Two consequences follow, both deferred until after M6-beta:

- **Screening is not specific to systematic reviews.** Criteria come from the
  protocol, decisions are events, the outcome is a rule table over
  per-criterion answers; that holds for scoping and mapping studies, umbrella
  and rapid reviews, dataset curation and abstract triage. What is specific is
  the reporting layer (PRISMA counts, the flow-diagram boxes, the methods
  paragraph), so reporting becomes a guideline chosen in the protocol
  (`prisma-2020`, `prisma-scr`, `none`), keyed from the existing
  `playbook_type`. The engine does not change.
- **Composition comes from artifact types, not a workflow engine.** Every stage
  is a step that declares the Contract v1 artifact types it consumes and
  produces and refuses with a typed code when an input is missing; the order
  falls out of the dependencies (import or discovery produce a corpus
  snapshot; prepare consumes it; collect consumes decisions). No workflow
  builder, no pipeline-spec runner, until a second workflow exists. The
  legacy nine-stage coordinator (`pipeline/coordinator.py`) and the
  pipeline-spec runner (`pipeline_executor.py`) are not that model and are
  not extended.

Not chosen: a settings framework for the harness (there are too few knobs to
justify one), environment variables for method parameters (invisible to the
protocol hash), and a per-screen configuration file (a preference that
changes the science must be in the protocol).

## 2026-11-06 — Several database exports in one corpus, deduplicated by the snapshot (M5b)

The researcher asked for several RIS files with cross-database deduplication and a way to
accept the corpus in the app. A PRISMA flow diagram needs the records identified per
database and the duplicates removed. Before this change, `accept-corpus --ris` took one
file and the counts read 0 duplicates.

- **Staging.** Each export is staged with a database label under `literature/raw/ris/`, kept
  byte for byte, and listed in `literature/raw/ris/sources.json`. A label may repeat (a
  database exported in parts); its files are summed into one database for PRISMA. Each
  file can carry a date searched and a search string, both optional. Staging and removal are journaled
  (`CORPUS_SOURCE_STAGED`, `CORPUS_SOURCE_REMOVED`).
- **Acceptance.** Acceptance writes one `verified.json` row per record, with
  `source_database`. It also writes `literature/raw/provenance_manifest.json`
  (`total_raw_harvested`, records per source), which the PRISMA counts already read.
- **Deduplication.** Nothing is collapsed at import. The snapshot builder's existing
  `Deduplicator` (DOI, then title, first author and year ±1) groups records into studies,
  so duplicates removed = records − studies, within and across files.
- **Contract.** The Contract-v1 snapshot schema is unchanged (`generate_contract_baseline.py
  --check` passes). Record ids now include the source and position, so two copies of one
  paper stay two records.
- **Freezing.** Once a corpus is accepted, its sources are frozen
  (`CORPUS_ALREADY_ACCEPTED`), and the app offers no way to replace it.
- **Routes.** `GET /corpus`, `POST /corpus/sources`, `POST /corpus/sources/{id}/remove`
  and `POST /corpus/accept` replace the planned M0 `POST /corpus/accept` row. They are
  desktop only and in both browser allowlists.
- **Methods paragraph.** It names each database with its count and date searched.

Approved by the researcher on 2026-11-06, with three changes to the Import screen (spec 11):
repeated labels are summed per database; the search details sit behind a "Search details"
disclosure with a "not stated" flag; and the Import step stays in the steps bar until the
corpus is accepted, after which Home shows one line of what was imported.

## 2026-11-06 — The approver's name is set on the Publish screen (M5-slim)

The researcher chose a field on the Publish screen over a command. Before,
nothing in the app wrote `literature/screening/operator_context.json`, so the
first approval of the golden run refused `OPERATOR_CONTEXT_MISSING` and the
researcher wrote the file by hand. Now `GET`/`PUT /api/v1/screening/approver`
read and write it (desktop only, in both browser allowlists), and every change
is journaled `SCREENING_APPROVER_SET` with the name before and after. The
Publish screen shows an Approver card above the batches; until a name is
saved, the code and approve buttons are disabled and the card says why.

What the name is, said plainly on the screen and in the contract: a name
typed on this computer, not a verified sign-in (CON-02/03 stay open; real
authentication is later work). Names the engine never trusts as a person
("unknown", …) refuse `APPROVAL_NOT_OPERATOR`. Changing the name later does
not rewrite approvals already made: each keeps the name it was made under.

## 2026-11-05 — The demonstration screens are removed; a new header and footer (M5-slim)

At the researcher's request the stale demonstration screens are gone: the
overview, the single-record `/screening` page, corpus, lineage and audit, with
their mock data (`lib/mock-*.ts`, `lib/contracts.ts`, `lib/project-state.ts`),
components and tests. Every remaining route reads a live workspace, so the
"Demonstration data" marker is gone too. `/<locale>` now forwards to
`/workspaces`, and `/<locale>/screening` forwards to `/screening/home`, so old
links still land somewhere real. The packaged app now opens on
`/en/screening/home/` (it opened the old demonstration page before).

This supersedes plan §8's "`corpus`, `lineage` and `audit` stay". Audit is
the loss that matters, since it carried provenance. The removed page showed
fixtures only, and a live audit view is follow-up work. The `ParkedNotice`
went with the screens it labelled; the parked CLI help and MCP descriptions
are unchanged.

The header is one 64px bar: the wordmark (no logo yet, per the brand book),
`Workspaces` and `Screening` with a brand underline on the current one, then a
language menu and a three-icon theme toolbar. Below `lg` these move into one
menu dialog. The footer is one line: the app runs on this computer, nothing is
sent unless agent proposals are started, and every decision is recorded in the
workspace's audit journal. The catalog shrank from 150 keys to 22 (the shell
chrome only); the screening screens keep their own per-locale copy.

## 2026-11-05 — The Claude Desktop Extension carries the wheel and launches it with uvx (M5-slim)

`scripts/build_mcpb.py` builds `nexus-scholar-<version>.mcpb` (MCPB `manifest_version` 0.4, the schema shipped with `@anthropic-ai/mcpb` 2.1.2). It bundles the `nexus-scholar` wheel and starts the server as `uvx --from ${__dirname}/<wheel> scholar-agent --workspace ${user_config.workspace}`, so it works before anything is on PyPI and needs only `uv` on the computer. Its one setting is the workspace folder. It holds no key and asks for none: provider keys stay in the OS keychain, which the server now reads at start (CORE-17 follow-up). The release workflow attaches it beside the wheel. Not chosen: the experimental `uv` server type (it would ship the source tree), and `sensitive` key fields in the extension (a second place for keys). Not verified here: installing it in Claude Desktop, and `npx @anthropic-ai/mcpb validate` (running the packer was not allowed in this session; the manifest is checked against the schema's required fields and types by `tests/test_build_mcpb.py`).

## 2026-11-05 — The packaged UI reaches the engine by a launch cookie and the proxy's allowlist (M5-slim)

The packaged app serves the UI as a static export from the console process
(plan §5.3), so the Next.js proxy, which held the token and allowed the
browser only reads and a list of writes, is not there. Its job moves into the
console (`src/scholar_harness/console/browser.py`), with the same rules:

- The UI keeps calling `/api/console/api/v1/...`; those requests are checked,
  then served as `/api/v1/...`. `/api/v1/...` itself still needs the bearer
  token, which never reaches the browser.
- The browser authenticates with an **HttpOnly, SameSite=Strict session
  cookie**. `nexus-scholar ui` opens `/launch?code=<code>`: a one-time code,
  valid 2 minutes, never the token. The session secret belongs to the launch,
  so it survives the restart onto another workspace.
- The **allowlist is the proxy's** (GET/HEAD on plain `/api/v1/...` paths; POST
  and PUT only on its lists, only from this origin; the draft read only from
  this app's pages); the workspaces routes join both lists. A test keeps the
  Python lists equal to `route.ts`.
- The static UI holds no workspace data and is served without a session.

New console codes: `CONSOLE_PATH_REFUSED`, `CONSOLE_ORIGIN_REFUSED`,
`CONSOLE_METHOD_REFUSED` (the proxy's), `LAUNCH_CODE_INVALID`.

## 2026-11-05 — The minimal workspace screen: root, open, create (M5-slim)

Spec `docs/ux/phase2-screening/final/00-workspaces.md` (FINAL). The
researcher's answers, 2026-11-05:

- **Root:** `--root`, then `NEXUS_WORKSPACES_ROOT`, then
  `~/Documents/Nexus Scholar/workspaces`; `--workspace <path>` still opens one
  folder and skips the screen. No settings screen or config file.
- **Open restarts** the engine and UI on the chosen folder (no in-place
  rebind, so no run state, pairing, phone token or cache crosses workspaces).
  It is refused `WORKSPACE_BUSY` while an agent run or an approval pairing is
  active, since a restart would kill it. Opening writes no journal event.
- **Create** asks for a title only; the folder is `{root}/{slug}`; an existing
  folder is refused `WORKSPACE_EXISTS`, never suffixed. It runs the same
  scaffold and support files as `nexus-scholar init --scaffold-only`, and its
  placeholder protocol is shown as a draft (no Contract v1 change).
- **Listing:** a folder counts as a workspace when it has `protocol.json`,
  `project.json` and `audit/journal.jsonl` (`.mcp.json` is not required);
  others are hidden behind "n folders skipped · Show them". `GET /workspaces`
  returns absolute paths (desktop-only, local).
- `docs/architecture/workspaces-api.md` is written and agreed before the
  engine work, with the codes `WORKSPACE_TITLE_INVALID`, `WORKSPACE_EXISTS`,
  `WORKSPACE_PATH_REFUSED`, `WORKSPACE_ROOT_UNAVAILABLE`, `WORKSPACE_NOT_VALID`,
  `WORKSPACE_BUSY`.

## 2026-11-05 — The prompt gate may be met on the MCP route

With no API credit, the researcher's own Claude (Claude Code subagents on the
subscription) answers the frozen v03 set through `nexus-scholar prompt-gate
export|import`: a blind export (prompt, schema and record text only; no label,
nothing ordered by label), one JSON answer per record, scored by the same
checks, rule table and bar as an API run. **A pass on this route is enough for
the M5-slim prompt-gate requirement for now** (researcher, 2026-11-05).

- The report names the route (`provider: "claude-code-mcp"`) and the model;
  its cost is null (the subscription is not metered per record).
- It measures the MCP route, not the API driver: the prompt runs inside
  Claude Code's own instructions, the output format is checked after the fact
  rather than enforced, and effort cannot be set. The API route stays
  unmeasured, and the agent-system §6 cost per 1,000 records stays an
  estimate, until an API run.
- Nothing may claim an API-route pass on the strength of an MCP-route one.

## 2026-11-05 — M1b-2 merges before its live prompt gate; the gate blocks M5-slim

The live prompt gate (Opus 5.5 on the frozen v03 set, Wilson lower bound of
include-recall >= 0.90; Sonnet 5.5 and Haiku 5.5 measured) needs API credit
the researcher does not have yet. Two smoke attempts measured nothing: a
placeholder key (401), then a real key on an account with no credit (400,
credit balance too low); neither was billed. M1b-2 therefore merges as
**code-complete with the prompt unmeasured** (researcher, 2026-11-05):

- the PR says plainly that the bar is not yet measured: Opus 5.5 is not shown
  to meet it, Sonnet and Haiku are unmeasured, and the agent-system §6 cost
  per 1,000 records is still an estimate;
- nothing in the product, its docs or its marketing may claim the agent passed
  the gate, or quote a measured recall or cost, until a gate report exists;
- the gate is a **blocking item for M5-slim**: no packaged release that runs
  agent proposals ships before it passes on the default provider and model,
  and its report and measured cost are recorded in the milestone file;
- the stand-ins were declined: a free Gemini key would not test the decided
  default and may let the provider use the records; a local model measures
  the pipeline, not the product.


The shell drew `Demonstration data` and "Read-only demonstrator" on every
route, including the six screening steps (`/screening/home`, `prepare`,
`proposals`, `triage`, `agreement`, `publish`) that only read the workspace's
engine and record decisions. There the labels were false. On those six routes
the shell now leaves the marker out and its footer says the data is live
(`isLiveOnlyPath`, `tests/shell.test.tsx`). Every other route keeps both,
including `/screening`, `/corpus`, `/lineage` and `/audit`, which still default
to fixtures; the rule "no mock data without the label" is unchanged
(researcher, 2026-11-05).

## 2026-11-05 — A minimal workspace screen joins M5-slim

The researcher asked why workspace management, Inception and Discovery came
after screening. The order stands (2026-11-03 entry below): screening is the
wedge, `accept-corpus` is its entry path, web Inception (M4) is past the
horizon and Discovery (M3) is stretch. One gap is pulled forward: a packaged
desktop app that can only open the single folder named on the command line is
not sellable. M5-slim therefore adds a **minimal workspace screen**: list the
workspaces under the workspaces root, open one, and create one (the same
scaffold as `nexus-scholar init`), with no Inception wizard. Its spec is written
before M5-slim starts; the M4 multi-workspace server and Inception spec 00 stay
in M4 (researcher, 2026-11-05).

## 2026-11-05 — The checked record text carries the publication year (M1b-2)

The text an agent sees and quotes, and that the engine checks quotes against
(`proposals.record_text`), is the title, a blank line and the abstract, then,
when the record has a year, a blank line and `Published: <year>`. Date
criteria (v03 INC-03, EXC-04) can then be answered with a verifiable quote;
before, the agent could only answer `not_reported`, so every record became
Unclear and the prompt gate measured nothing useful (researcher, 2026-11-05).

- Without a year the text and its `input_sha256` are unchanged, so earlier
  proposals keep their ids. With one, the hash and `proposal_id` change; no
  real proposals existed yet (only sandbox and test ones).
- Language still has no field; a language criterion is answered from the
  abstract or stays `not_reported`.
- The MCP record tool returns this `text` with the year, so an agent using
  MCP quotes the same string.
- **Usefulness is reported, not gated:** the prompt-gate report also gives
  the share of confirmed excludes the agent excludes and its Unclear rate;
  the pass bar stays include-recall.

## 2026-11-05 — The screening prompt gate: bar, sample and models (M1b-2)

The researcher set the prompt gate of agent-system §5 for the screening task:

- **Bar:** the 95% Wilson lower bound of include-recall is at least **0.90**.
  Include-recall counts an agent Unclear as not excluded, because Unclear goes
  on to full text. The bar applies per task version (provider, model, prompt,
  effort).
- **Sample:** every human-confirmed include of `uav-crop-weed-v03` (644) and
  1,000 of its confirmed excludes, drawn with a fixed, recorded seed. The set
  is frozen as a list of study ids with its SHA-256, so every model and prompt
  version is measured on the same records.
- **Models:** `claude-opus-5-5` (the default), `claude-sonnet-5-5` and
  `claude-haiku-5-5`. A cheaper model is adopted only if it meets the bar
  (agent-system §9 item 3).
- **The live run spends the researcher's key.** It runs only after the
  researcher sees the token-counted estimate and starts it; the key is stored
  in the OS keychain and never seen by the agent or written to a file.

**Caveat (carried from 2026-11-04):** the v03 labels are confirmations of agent
drafts. The gate measures recall against labels a person reviewed with a
draft in view, not against independent blind screening; the methods text says
so.

## 2026-11-05 — M1b is three PRs; three screening providers

M1b splits into **M1b-0** reveal tracking (RELEASE, backend only), **M1b-1**
desktop triage UI (STANDARD) and **M1b-2** drivers and the prompt-gate eval
(STANDARD). The researcher agreed the split on 2026-11-05. The reveal change is
isolated so the strict lane covers only the engine change to stored decision
events.

**Providers (researcher, 2026-11-05):** one driver interface with Anthropic
(the default), any **OpenAI-compatible** endpoint (a base URL and a key) and
Gemini. They share the prompt, the output schema, the plain-code outcome rule
and the rule that a refusal or a failed check becomes Unclear. Each provider
and model is its own task version and must pass the prompt gate on its own.
This settles agent-system §9 item 1: Gemini stays, behind the interface.

**Reveal semantics (contract §3.1, applied literally):** a reveal is the first
time the API returns a proposal for a study to a screener. It is recorded in
`literature/screening/reveals.jsonl` under the events lock and journaled as
`SCREENING_PROPOSAL_REVEALED` without the outcome. A superseding event received
after a reveal of that study's proposal, by that screener and in the current
generation, is stamped `changed_after_reveal: true`, whether or not the outcome
changes; the methods paragraph can compare outcomes from the event chain.
Events stored before M1b-0 keep `false`, which for them means "not tracked".

## 2026-11-04 — `accept-corpus` is the screening entry path until Packet B (M0)

`nexus-scholar accept-corpus` builds the Contract-v1 corpus snapshot with the
search kit's `build_corpus_snapshot_artifact` from `literature/verified.json`.
It publishes the snapshot through the existing acceptance gate, which
validates it against the frozen schema and journals the acceptance; `prepare`
then works on a fresh workspace.
- **RIS import:** `--ris <file>` imports a RIS export first. Each record gets
  a record-derived `SCI-` id (from title, year, DOI and author names), so a
  re-import yields the same ids. The import refuses to overwrite an existing
  `verified.json`.
- **Re-runs:** re-running on unchanged records publishes nothing.
- **No CSV importer:** none exists yet, so CSV is deferred.
- **Snapshot semantics unchanged:** the builder and acceptance are reused as
  they are, so the lane stays STANDARD.
- **Packet B:** full adoption, with discovery producing the snapshot itself,
  remains M3.

## 2026-11-04 — Approval: terminal-only code; event-decided batches need no worker step (CON-02/03)

**The code stays on the terminal.** The approval code is printed only in the
terminal running `nexus-scholar serve`, never returned over HTTP, and the
researcher types it into the publish screen. This keeps the existing pinned
rule: something that can call the console API (a malicious page that got the
token, another local process) still cannot approve on its own. The contract's
`qr_payload` for `pairing/begin` is dropped; spec 09 follows.

**Events replace the worker step.** A batch decided entirely by human decision
events is approved on its event projection. No worker recommendation is
required. The approval binds that batch's projected bytes only, never another
batch's (CON-03), and the approver is recorded as an unauthenticated local
attestation, not an identity (CON-02). The worker path stays for
agent-screened batches. Researcher's choices, 2026-11-04.

## 2026-11-04 — The v03 screening labels are human-confirmed: the M1b eval set

`uav-crop-weed-v03` has a signed screening confirmation:
`literature/screening/HUMAN_CONFIRMATION.json` (`HumanConfirmation@1`, PR
#172, 2026-10-31). Its lead reviewer, Mouadh BEKHOUCHE, confirmed all 14,150
agent decisions and changed none, and the record pins the 283 decision files
by SHA-256. The M0 note that v03 had no human labels was wrong: it read the
README and the `decision_status: FINAL_AGENT_UNCONFIRMED` fields and missed
this record.

**Consequences:**
- The v03 labels are the human-confirmed eval set for the M1b prompt gate
  (agent-system §5).
- The 200-record AI reference screening (`method: LLM`, 2026-11-04) is no
  longer needed as a stopgap. It stays available only as a model-versus-human
  comparison.
- The stale status fields are not rewritten: they sit in hashed decision
  files, a published report and the append-only journal. The README says so,
  and a `SCREENING_CONFIRMATION_RECOGNISED` journal row records that the
  confirmation supersedes them.

**Caveat for the methods text:** these are confirmations of agent drafts,
none changed. The eval measures recall against labels a human reviewed with
the draft in view, not against independent blind screening.

## 2026-11-04 — Unclear records go forward to full text (PRISMA)

A record the researcher marks Unclear (stored as `MAYBE`, labelled "Unclear →
full text") passes title and abstract screening. In the PRISMA flow it is
counted in "records sought for retrieval" with the includes, and shown on its
own line (`unclear_to_full_text`), never with the exclusions. The collector
stops refusing `MAYBE` at finalize (M1a), and `check_golden_workspace.py`
reconciles included + unclear + excluded + conflicts with records screened.
Researcher's choice, 2026-11-04.

## 2026-11-04 — CON-13 is guarded outside the Contract v1 lock

`contracts/acceptance.py` and `contracts/chain.py` check batch identity,
binding and membership only when a `screening_decisions` artifact has exactly
one `screening_batch` parent; zero or several parents skip those checks
(CON-13). Both files are locked by the Contract v1 baseline. Rather than a
contract change, the harness refuses to submit a decisions artifact without
exactly one batch parent, before it calls the frozen gate (M1a). A caller that
bypasses the harness and calls `accept_artifact` directly is not covered; that
gap is recorded for Contract v1.1. Researcher's choice, 2026-11-04.

## 2026-11-04 — Console guards and the `--lan` threat model (INC-01)

**Threats.** In stage 1 the console holds unpublished review data and can run
kit commands. Three kinds of caller can reach it:
- a web page in the researcher's browser: cross-site requests, and DNS
  rebinding through a name that resolves to 127.0.0.1;
- another process on the machine, including an AI agent's sandbox;
- from M2, a device on the same LAN.

**Guards, on every request** (`console/serve.py`):
- **Host.** The `Host` must be a loopback name (`HOST_REFUSED`).
- **Origin.** A browser `Origin` must be loopback (`ACTION_ORIGIN_REFUSED`,
  the code the screening actions already used).
- **Token.** Every route except `/healthz` needs `Authorization: Bearer
  <token>` (`TOKEN_REQUIRED`). `serve` takes the token from
  `NEXUS_CONSOLE_TOKEN`, or generates one and prints it once.
- **Loopback bind.** `serve` refuses a non-loopback `--host`.

**What a caller can run.**
- **Pipeline nodes** may run only the kit CLIs and the screening handoff
  script (`COMMAND_NOT_ALLOWED` in `validate_spec`). This applies in the
  console and in `scholar-harness run`; tests that run `python -c` stub nodes
  extend the list explicitly.
- **Jobs** run only in the served workspace (`WORKSPACE_MISMATCH`).

**The UI proxy** adds the token server-side, so the browser never holds it. It
answers only on a loopback host and forwards a POST only when its `Origin` is
the app's own.

**Residual risk, accepted for stage 1.** A process running as the same user
can forge `Origin` and POST through the proxy. It already has the user's
files, so this grants no new privilege. M5-slim serves the UI from the same
FastAPI process and replaces the proxy with a session cookie.

**`--lan` (M2).** It never exposes this app. `nexus-scholar ui --lan` mounts a
separate restricted sub-app on the LAN address:
- **Routes:** screening reads and decision-event POSTs only. The jobs,
  pipelines, streams and audit-writer routers are never mounted there; a test
  proves they are unreachable.
- **Pairing:** a phone pairs through a one-time token in the desktop QR code.
  The token lives 2 minutes and is exchanged for a session cookie scoped to
  the sub-app; no token appears in a URL after the first load.
- **Session end:** on stop, on process exit, or after 12 hours.
- **Transport:** plain HTTP on the LAN, so someone on the network can read
  abstracts and decisions in transit. That is accepted for stage 1, shown on
  the pairing screen, and fixed by opt-in HTTPS (`mkcert`) or the sync tier.
- **Desktop only:** approval stays on the desktop (contract §4, §9.1).

## 2026-11-04 — MCP tool paths are contained in the workspace (AGT-01)

Every path argument of a `scholar-agent` tool, for reading and for writing, must
resolve inside the MCP workspace (`--workspace`, else `NEXUS_MCP_WORKSPACE`, else
the repository root). Relative paths are joined onto it; absolute paths are
allowed only when they land inside it. Symlinks and `..` are resolved first. An
escaping path raises `PathOutsideWorkspace` (`PATH_OUTSIDE_WORKSPACE`) before
any I/O, which the MCP client sees as a tool error. Consequence: a researcher
who wants a tool to read a file elsewhere (a PDF in Downloads) copies it into
the workspace first. Reads are contained too, because an agent could otherwise
use a reader tool to pull any local file into its context. Path parameters never pass
anything through by its content (`'["/../x"]'` is valid JSON and, on POSIX, a
legal path). Only the four parameters that accept an inline payload
(`intent_json`, `protocol_json`, `screeners_json`, `adjudication_json`) keep a
value that parses as JSON, and never open it as a path (review findings, M0).

## 2026-11-04 — MCP keys stay in the env file, never in a config file (CORE-17)

`setup-mcp` used to copy provider keys from `.env` into an `env:` block of each
MCP config, including `<workspace>/.mcp.json` and `.cursor/mcp.json`, which git
tracked. Now it adds `--env-file <path>` to the server command, and
`scholar-agent` loads the approved keys (`SCHOLAR_*`, `NEXUS_*`, the three
provider keys) from that file at start. Variables already set in the
environment win. No config file holds a key value, VS Code works like the
other targets, and `.env`, `.mcp.json` and `.cursor/mcp.json` are gitignored.
Configs written by older versions keep their `env:` block until `setup-mcp` is
run again.

## 2026-11-04 — Screening API contract accepted

The researcher decided the contract's six open questions:
- a fresh approval code for each batch generation, refused while any phone has queued events;
- an OS file lock on each screener's event file;
- an Exclude on the phone needs a reason only, with no checklist;
- 200 events per request, with the UI sending larger backlogs in chunks;
- methods-paragraph wording and sample-audit size deferred to M5-slim;
- a dated price table, updated each release, behind the cost estimate.

All nine screening screen specs are now FINAL. Details:
[`architecture/screening-api-contract.md`](architecture/screening-api-contract.md) §9.

## 2026-11-03 — Plan revised after independent review: screening wedge at week 6

An independent review of the production plan found that screening could not be
reached before week 6: no code builds a corpus snapshot outside tests, and the
import path was not scheduled. It also found that M1 was too large for one
person. The researcher accepted three changes:

- **Order.** M0 (adding a minimal `accept-corpus` entry path) → M1a screening
  backend → M1b desktop UI and driver → M2 mobile → M5-slim package, where the
  wedge ships. Discovery (M3) is stretch. The web Inception wizard (M4) moves
  past the two-month horizon; inception stays CLI/MCP, labelled beta.
- **You see every record by default.** The agent orders the queue and
  proposes. Exclusion without a human look is an explicit opt-in with a sample
  audit, and the methods paragraph discloses it (PRISMA 2020 item 8).
- **Unclear is stored as the existing `ScreeningDecisionValue.MAYBE`.** It is
  labelled "Unclear → full text". There is no Contract v1 version change; only
  the collector's refusal of MAYBE at finalize changes, in M1a.

The review also moved the prompt-gate eval from the 30-record golden workspace
to the human-labelled `uav-crop-weed-v03` screening data (at least 200 records,
at least 30 includes). It restricted `--lan` to a sub-app without the
job-running routers, and keyed decision IDs on the client event ID so replays
cannot void approvals. Details: `roadmap/production-plan.md` §2, §4, §6;
`architecture/agent-system.md` §2–§6, §8.

## 2026-11-03 — Agent system: proposals only, least autonomy per job

The AI behind Phases 0–2 is built as versioned *tasks*: a prompt, an output
schema, a model and effort setting, and an eval set. Most tasks are plain code
or single structured calls. Only the inception conversation and the
researcher's own Claude Code or Claude Desktop (through MCP) run agent loops.
Model output is always a proposal in an append-only store with full provenance
(model, prompt hash, input hash, checks, usage). Plain-code validators check
each proposal, and anything that fails, refuses or is truncated goes to the
researcher as Unclear, never Exclude. Only the engine writes artifacts and the
journal, and only after a human decision. The in-app driver (the researcher's
own API key, with Message Batches and prompt caching) and the MCP driver share
the same tasks. Changing a prompt, model or effort setting needs a new task
version and an eval re-run, mirroring the contract-baseline gate. Default
model: `claude-opus-5-5`. Open: whether to keep Gemini, whether to build the
in-app inception chat, and whether a cheaper screening model holds recall.
Design: [`architecture/agent-system.md`](architecture/agent-system.md).

## 2026-11-03 — Claude Code dev workflow and area-based test gates

The OpenCode four-agent loop is no longer the development workflow; the files
stay, baseline-locked, as history. Development runs in Claude Code with three
project slash commands (`/milestone`, `/gate`, `/ship` in `.claude/skills/`) and
four narrow subagents (`.claude/agents/`): a read-only finding auditor, a test
gatekeeper, an independent milestone reviewer, and a UX spec writer. The
researcher approves milestone starts, contract decisions and every push.

The test selector was keyed to E3 RAG tasks, so after the one-package merge a
screening edit selected an unrelated RAG test and a search, protocol or UI edit
fell back to the full ten-minute Python suite. Selection is now by source area
(`areas` in `docs/architecture/test_gate_manifest.json`, `--changed` from git).
Inner gates skip `@pytest.mark.slow`, and the PR gate runs the full suite once in
parallel (`pytest-xdist`, `-n auto`). The full suite still runs once per PR
candidate; that rule did not change. Details are in
[`architecture/test_gate_policy.md`](architecture/test_gate_policy.md) §Selector.

## 2026-11-03 — Deployment: local engine first, hybrid sync later (option C staged from A0)

Nexus Scholar ships first as a local engine. `uv tool install nexus-scholar`,
then `nexus-scholar ui`, serves the static-exported research UI and `/api/v1`
from the one FastAPI process on loopback, behind a per-launch token. `--lan`
plus a QR code lets a phone on the same network screen. Workspaces stay local
folders, with no hosted infrastructure. AI proposals come first from the
researcher's own Claude Code or Claude Desktop through the `scholar-agent` MCP
server, which writes proposals only. A bring-your-own Anthropic key is the
second path, for in-app runs. Whether Gemini stays as a third option is open
(`architecture/agent-system.md` §9). The maintainer never pays for or resells
tokens. The engine, UI and MCP server stay MIT. Paid features (end-to-end
encrypted sync of decision and journal events, team dual screening with real
κ, institutional SSO) go in a separate proprietary service, built only after
10–20 real users. Stage 1 sells onboarding and support, not code-gated
features. A signed desktop app (Tauri with a Python sidecar) waits for user
demand. Hosted web-first (option B) was rejected: it contradicts the privacy
of unpublished reviews and adds operations work that one maintainer cannot
carry. The full option study is in
[`roadmap/production-plan.md`](roadmap/production-plan.md) §5.

## 2026-11-03 — Brand book replaces VISUAL_DIRECTION as the UI design system

`docs/ux/brand/tokens.json` and `BRAND_BOOK.md` become the design system of
record for `apps/research-ui`. This reverses VISUAL_DIRECTION decision D1 (no
web fonts, no radius, light only). Tokens generate the Tailwind 4 theme, with
light and dark modes. The fonts (Literata, Public Sans, IBM Plex Mono) are
self-hosted, not loaded from Google, so the tool works offline and makes no
third-party calls. VISUAL_DIRECTION rules that do not conflict are kept as
amendments. GATES and the browser colour tests are updated in the same PR.

## 2026-11-03 — Production scope: Inception, Discovery, Screening over two months

Only Phases 0–2 are brought to production, on the two-month sequence M0–M5 in
[`roadmap/production-plan.md`](roadmap/production-plan.md) §6. Screening comes
first. The quality gate is a real end-to-end run on the golden UAV workspace,
not the autonomous agent loop. Everything else is labelled "not production —
parked" in UI, docs, CLI and MCP.

## 2026-11-03 — One package instead of eight kit repositories

The harness and the eight `scholar-*-kit` packages ship as one distribution,
`nexus-scholar`, from the root `pyproject.toml`. Kit code lives in
`src/scholar_<kit>/`, kit tests in `tests/kits/<kit>/`. The per-kit repositories,
vendored snapshots, `plugins.json` pins, pin codegen, installer and separate
metapackage were removed: syncing eight repositories cost a single maintainer a
great deal and bought nothing while no one installs a kit on its own. If a kit
gains independent users it can be split out again with `git subtree split`.
Contract producer provenance keeps the component names and now reports the
package version and repository commit. See the
[assessment](assessment/README.md) for why this came first.

## 2026-11-03 — Fresh assessment replaces earlier audit material as the current view

[`assessment/`](assessment/README.md) is the current, evidence-backed view of
the harness and kits, with a ranked P0/P1/P2 list. Older dated reviews remain
as history only.

## 2026-10-26 — Human confirmation is a separate package outside the frozen baseline (Phase C)

`contracts/confirmation/` and its schema sit outside the non-recursive globs
that `generate_contract_baseline.py` hashes, so adding confirmation did not
change the frozen Contract v1 payload. The refusal registry is imported, never
extended. Behaviour: [`architecture/confirmation.md`](architecture/confirmation.md).
Spec: `specs/agent-layer-portability/06_human_confirmation.md`.
Original record: `docs/architecture/decision_phase_c_confirmation_2026-10-26.md`.

## 2026-10-26 — The agent envelope is a package, not a flat module (Phase B)

`scholar_harness.contracts.envelope` is a package for the same reason: a flat
module or a schema under `schemas/v1/` would have entered the frozen lock set.
Refusal codes: [`architecture/refusals.md`](architecture/refusals.md).
Spec: `specs/agent-layer-portability/02_envelope_and_refusals.md`.
Original record: `docs/architecture/decision_phase_b_envelope_2026-10-26.md`.

## 2026-10-25 — Agent roles are generated from `roles/*.json` (Phase A)

Role definitions (`roles/*.json` plus prompts) are the source; the OpenCode
agent files are generated by `scripts/generate_agent_roles.py`. Write
permissions are derived (a critic is denied what it judges; `deny_glob` is a
write denylist; `audit/journal.jsonl` is protected).
Spec: `specs/agent-layer-portability/01_role_model.md`.
Original record: `docs/architecture/decision_phase_a_role_generation_2026-10-25.md`.

## 2026-10-23 — T-SC1 accepted without a recorded independent review (accepted risk)

PR #144 (cross-kit canonical and identifier parity pin) entered `main` without
the independent reviewer and tester evidence the gates require. The researcher
accepted that risk explicitly; it is not a precedent for skipping review.
Original record: `docs/architecture/decision_t_sc1_acceptance_without_review_2026-10-23.md`.

## 2026-10-13 — Product direction: the individual researcher

The first user is an individual researcher running a review directly in Nexus:
a local research service with a browser review interface, with CLI and MCP as
advanced interfaces. First journey: provisional protocol → bounded retrieval →
review recommendations with preserved overrides → authorized screening
decisions → transparent screening record. Full-text charting and synthesis
follow as separately validated capabilities.
Original record: `docs/architecture/decisions/individual-researcher-product.md`.

## 2026-10-12 — TD-E3-CURRENTNESS: stale extracted bodies are refused (Option B)

When an extracted body is stale, the indexing stage writes one
`RAG_INDEX_REJECTED` event and returns the typed `STALE_EXTRACTED_BODY` refusal
before any backend call or index publication (it previously crashed on an
unsupported `parameters=` argument).
Original record: `docs/architecture/decisions/td_e3_currentness_decision.md`.

## 2026-10-12 — Agent instructions must reference files that exist

The baseline-locked agent definitions pointed at two spec files that never
existed; they were corrected to `10_cross_kit_contracts.md` and
`12_execution_roadmap.md`. Backticked paths are not caught by link checks, so
such references need review.
Original record: `docs/architecture/decisions/agent-instruction-reference-repair.md`.

## 2026-10-10/12 — Authorized screening: protected publisher, restricted worker (AG)

The researcher approved a protected local publisher with a restricted
scientific worker: agents may propose screening decisions, but publication of
final decisions requires the researcher's authorization. Approval of the
direction is not proof of isolation; the
[assessment](assessment/harness-contracts-screening.md) (CON-02/03) found the
authorization still bypassable.
Current state: [`architecture/agent-controls/README.md`](architecture/agent-controls/README.md).
Original record: `docs/architecture/agent-controls/agent_controls_decision.md`.
