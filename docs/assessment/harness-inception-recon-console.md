# Harness inception, recon and console assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1. Scope: `src/scholar_harness/inception/` (2,133 lines: `genesis.py` 646, `grounded.py` 507, `wizard.py` 486, `intent.py` 307, `__init__.py` 155, `display.py` 32), `src/scholar_harness/recon/` (1,760 lines: `adapter.py` 391, `adaptive.py` 338, `engine.py` 314, `distiller.py` 305, `lexicon.py` 141, `gates.py` 128, `cache_key.py` 113), `src/scholar_harness/console/` (4,827 lines: `api/screening.py` 1,662, `api/workspace.py` 1,427, `api/pipelines.py` 537, `runtimes/job_runner.py` 498, `runtimes/actions.py` 254, rest small). Total 8,720 lines (the brief's ~7.7k is an undercount). Method: read every inception and recon module in full; read `serve.py`, `jobs.py`, `audit.py`, `streams.py`, `actions.py`, `job_runner.py`, the storage/endpoints half of `pipelines.py`, the write path, UI-07 read routes and action routes of `screening.py`, and `workspace.py` lines 1–940; followed calls into `pipeline_executor.py`, `pipeline/validation.py`, `scholar_search/engine.py` and `workspace-manager/scripts/init_project.py`. Ran the existing suites (`uv run pytest tests/inception tests/recon tests/unit/test_recon_adapter_characterization.py tests/console -q`: 353 passed), `ruff --select F401,F811,F821,F841` on the scope, and six offline reproduction scripts (stubbed `search_fn`, `TestClient`, temp directories; no provider calls). Scripts are in the session scratchpad (`repro1.py`–`repro6.py`); the commands and their outputs are quoted below.

## 1. Verdict

The recon core (cache key, distiller, gates, lexicon, adaptive merge) is small, pure and readable. The inception wizard and the console around it have real defects. Two of them are serious: the console API runs arbitrary commands for any client that can reach it, and re-running the inception wizard with an existing title silently replaces a compiled protocol. Scientifically, the "grounded" guarantee does not mean what it says. A concept counts as "anchored" when a provider returns any DOI-bearing record for it, even an unrelated one. The wizard also writes eligibility criteria the researcher never typed and never sees before the protocol is compiled. None of the nine findings in the 2026-10-09 scientific review has been fixed. The 353 passing tests confirm the current behaviour, including its questionable defaults; they are not evidence that the behaviour is correct.

| Lens | Rating | Reason |
|---|---|---|
| Code quality & architecture | Weak | Clean recon core, but the console has unauthenticated command execution, argv injection, forgeable audit rows, duplicated routes that contradict each other, and test seams hacked into production modules. |
| Correctness & bugs | Weak | 2 High and 7 Medium defects reproduced: protocol overwrite, a failed probe cached forever, a cancel race, console actions that cannot run, a readiness flag that overstates progress, and an audit-feed crash. |
| Research-method fitness | Weak | "Anchored" is vacuous, eligibility criteria are auto-generated and not shown before compiling, English-only is the silent default, and all 9 prior method findings are still present. |

## 2. Architecture and code quality

**INC-01 — High — Reproduced — Unauthenticated arbitrary command execution through the console API.**
`POST /api/v1/pipelines` (`console/api/pipelines.py:460-484`) stores any `PipelineSpec`. A node's `command` is a free `list[str]` (`pipeline/models.py:21-24`), and `validate_spec` checks only graph structure, with no command allowlist (`pipeline/validation.py:76-116`). `POST /api/v1/jobs/start` with `action_id=pipeline` then executes the spec in-process (`job_runner.py:158-160` → `pipeline_executor.py:189-199`, `["uv","run",*node.command]`). The app has no authentication and no `TrustedHostMiddleware` (`serve.py:36-73`), and only the `/actions/*` routes check `Origin` (`screening.py:1299-1323`). `repro6.py` sent both POSTs with `Host: rebound.attacker.example`, using the node command `["python","-c","open(...,'w').write(...)"]`:
```
save 201 / start 202 running / job state success / marker exists: True arbitrary code ran
```
Impact: when the server is bound to loopback (`cli.py:1017-1019`), a DNS-rebinding page can reach it, and any local process can too. `--host 0.0.0.0` is accepted with no warning. The CORS comment's premise ("Browsers never mutate through this API", `serve.py:56-60`) does not hold, because a rebinding page is same-origin with the attacker's host.

**INC-02 — Medium — Reproduced — Argv injection and broken quoting in action rendering.**
`render_command` substitutes `{q}`/`{ws}` into a template string by text replacement, then splits it with a hand-rolled quote toggler (`runtimes/actions.py:207-238`). The client also chooses `workspace` (`jobs.py:29`, `job_runner.py:123`). `repro1.py`:
```
discovery, q='llm" --output C:/Windows/evil.json "x' -> ['uv','run','scholar-search','search','llm','--output','C:/Windows/evil.json','x']
dedup, ws='C:/Users/John Doe/ws' -> [..., 'C:/Users/John', 'Doe/ws/literature/candidates.json', '--output', 'C:/Users/John', 'Doe/ws/literature/corpus.json']
```
Impact: a query can inject flags, including output paths. Every action fails for a workspace path that contains a space, which is common on Windows (`C:\Users\First Last`). A request body can also point mutating kit commands at any directory. Build argv as a list and never re-split it; drop the `workspace` override, since the server is already bound to one workspace.

**INC-03 — Medium — Reproduced — Audit and screening provenance can be forged by the client.**
`audit.py:7-8` says "never trust the client for provenance fields", but `POST /api/v1/audit/events` takes `action`, `agent_or_tool` and `status` from the body (`audit.py:111-135`). `repro5.py` (foreign `Host` and foreign `Origin`):
```
201 {'action': 'SCREENING_PUBLISH_COMPLETED', 'agent_or_tool': 'researcher:mouadh', 'status': 'SUCCESS'}
action route with foreign Origin: 403   |   audit route with foreign Origin: 201
```
The forged `SCREENING_*` row then appears in the screening-journey feed (`screening.py:1201-1204`). The decisions writer takes `reviewed_by` and `timestamp` from the client and stores them once per file (`screening.py:84-87, 203-209`). Each per-record merge therefore re-attributes every earlier decision in the batch to the last caller. Reproduced: after "agent-x" saved S0 and "Dr. Somebody Else" saved S1 with `timestamp: 1999-01-01`, the file read `reviewed_by: Dr. Somebody Else, timestamp: 1999-01-01T00:00:00Z`, and no record kept its own reviewer. For a sole-reviewer PRISMA record, who decided what, and when, is the provenance that matters.

**INC-04 — Medium — Static — Test seams are built into production modules.**
`inception/__init__.py:114-155` replaces the package's module class at runtime. Every `setattr` on the package is copied into five submodules and into `workspace.loader`, and failures are swallowed by `except Exception: pass` (`:126-127, :151-152`). `genesis.py:72-94` keeps "deprecated cache variables retained so existing monkeypatch seams do not error". As a result, any assignment to `scholar_harness.inception.<name>` silently mutates other modules, and a mistyped name fails without an error. Tests should patch the owning module instead.

**INC-05 — Medium — Static — The console has duplicated, divergent routes.**
`_ui07_error` and `_ui07_refuse_caller_identity` are copied verbatim (`workspace.py:340-382` and `screening.py:269-305`). There are two journal readers with opposite error behaviour (`workspace.py:278-310` versus `screening.py:1173-1224`; see INC-14). There are three batch-progress views with three definitions of "done" (`workspace.py:154-172`, `workspace.py:498-516`, `screening.py:545-565`; see INC-13). The caller-identity guard is a deny-list of query-parameter names. No route reads identity from the query, so the guard protects nothing, and a renamed parameter would bypass it anyway.

**INC-06 — Low — Static — Dead code, unused imports and two undefined names.**
`ruff --select F401,F811,F821,F841` reports 30 findings in scope. They include `F821 logger` at `screening.py:1193` (a live bug, see INC-14) and `F821 Responder` at `grounded.py:253`, which only works because of `from __future__ import annotations`. `grounded.py:17-18` imports `distill_pool`/`TOPIC_COHERENCE_TOP3_SHARE` and imports them again inside functions (`:213-214, :279`). `genesis.py` has 10 unused imports. In `recon/adapter.py:106-111`, `_require_symbol` guards module-level imports that cannot be `None` (a failed import raises first), so the advertised "typed dependency errors" are unreachable. `ReconEngine.__init__` lets `NEXUS_RECON_ROOT` override an explicit `cache_root` (`engine.py:135-141`), so the adapter's `workspaces/` check on `cache_root` (`adapter.py:199-202`) validates a value the engine may ignore.

**INC-07 — Low — Static — Assorted console runtime issues.**
`serve --reload` passes an app object to `uvicorn.run(..., reload=True)` (`cli.py:1041`); uvicorn requires an import string for reload and exits. SSE subscriber queues are unbounded (`jobs.py:44`). Single-flight is per action, not per workspace (`job_runner.py:119`), so `screen_prepare` and `screen_collect` can run concurrently on the same files.

Strength worth keeping: the recon modules are side-effect-light, deterministic given a pool, and fully injectable (`search_fn`). This makes the defects above cheap to pin with regression tests.

## 3. Correctness and bugs

**INC-08 — High — Reproduced — Re-running inception overwrites a live protocol and resets the manifest.**
In the monorepo path, `run_wizard` never calls `require_uninitialized`; only `init_command` does (`wizard.py:434`). `scaffold_project` runs `init_project.py`, which rewrites `project.json` with fresh `created_at` and zeroed `stats` (`init_project.py:131-155`). `compile_protocol_files` then overwrites `intent.json`, `protocol.json` and `SCREENING_CRITERIA.md` (`genesis.py:158-167`). `repro3.py` ran the wizard twice with the same title (second run with a different proof) after setting `stats.discovered_papers=812`:
```
same dir: True / fingerprint changed: True / stats after rerun: 0 created_at: 2026-11-03T00:02:48...
journal actions: ['PROJECT_INITIALIZED', 'GENESIS', 'PROJECT_INITIALIZED', 'GENESIS']
```
Impact: a workspace that has already been searched or screened is silently re-protocolled. Earlier screening decisions then refer to criteria that no longer exist. There is no prompt and no backup; the journal is the only trace.

**INC-09 — High — Reproduced — A failed or partial probe is cached permanently.**
`scholar_search.engine.search_all` logs and swallows every provider exception (`tools/scholar-search-kit/src/scholar_search/engine.py:53-61`). `ReconEngine.probe` persists whatever comes back, including an empty list, and later returns it on every cache hit without TTL or refresh (`engine.py:294-313`). `repro1.py`:
```
first probe (search_fn -> []) -> n=0 ; second probe with a working search_fn -> n=0, search calls=1
```
Impact: one offline run or rate-limited window permanently "proves" that a topic or concept has no literature evidence. The grounded wizard then aborts on every later run (`grounded.py:296-301`, `:468-470`), with no hint that the cache is the cause. A partial failure (for example OpenAlex down, arXiv answering) is cached as a normal pool, with no record of which providers failed.

**INC-10 — Medium — Static — The 25-document pool is chosen by arrival order, not by relevance.**
Each provider receives `max_results=25` (`engine.py:167-174`), so up to 100 documents come back. `search_all` appends results from concurrently running providers in network-arrival order (`scholar_search/engine.py:50-63`). `probe` keeps `docs[:POOL_MAX]` (`engine.py:310`). The pool that drives the taxonomy, directions, QEI and topic purity is therefore whichever providers answered first, deduplicated. That is neither relevance-ranked nor reproducible across a cache miss. "Deterministic caching" is true of the cache key only.

**INC-11 — Medium — Reproduced — Cancelling a job ends as `failed` and leaves two contradictory journal rows.**
`cancel` sets `state="cancelled"` and journals `PARTIAL` (`job_runner.py:433-449`). `_run_to_completion` keeps draining, then overwrites the state (`:207-208`) and journals again (`:222-231`). `repro4.py`:
```
state right after cancel: cancelled / final state: failed exit: 1
[('STATUS','PARTIAL','status job ... cancelled'), ('STATUS','FAILED',"status job ... finished with state 'failed'")]
```

**INC-12 — Medium — Reproduced — Several console actions cannot run as defined.**
`screen_prepare` and `screen_collect` use the repo-relative path `src/scholar_harness/agent_screen.py` (`actions.py:70,77`), but the job runs with `cwd=workspace` (`job_runner.py:162-167`). Running `screen_prepare` from a repo workspace produced: `failed 2 … can't open file '…\workspaces\_assess_tmp\src\scholar_harness\agent_screen.py'`. `rag_index` passes literal `<RUN-...>`, `<rfc3339>` and `<int>` placeholders (`actions.py:110-120`), so it always fails or is refused. `synthesize` hard-codes `--rq-id RQ1` (`actions.py:134`).

**INC-13 — Medium — Reproduced — Screening readiness is overstated.**
`/ui/project-summary` counts a batch as resolved when its decisions file exists (`workspace.py:503-516`). The legacy `/screening/batches` sets `collected = decisions.exists()` (`workspace.py:169`). The console's own writer creates that file on the first single-record save. `repro5.py`, 50-paper batch, 2 decisions saved:
```
project-summary run: {'batches': 1, 'batches_resolved': 1} all_batches_resolved: True
legacy /screening/batches: [{'items': 50, 'decisions_count': 2, 'collected': True}]
ui/batches coverage: INCOMPLETE decisions_count: 2
```
Three endpoints give three answers, and the summary shown to the researcher is the most optimistic.

**INC-14 — Medium — Reproduced — The audit feed crashes on a corrupt journal line; the other reader hides it.**
`screening.py:1193` calls an undefined `logger`. The inline comment says "one bad line never refuses the feed". With one truncated line in `journal.jsonl`: `GET /api/v1/screening/ui/audit-feed → 500`, while `GET /api/v1/audit/events → 200, total 1` (`workspace.py:293-297` drops the line silently). Neither behaviour is right for an append-only provenance ledger: corruption should be surfaced as an explicit item.

**INC-15 — Medium — Reproduced — Declining Phase-4 verification is recorded inconsistently.**
`wizard.py:302-306` asks "Enable all Phase-4 verification checks?", and "no" only sets the trust threshold to 0.0. `make_intent` always writes `retraction_check_required`, `coi_and_funding_audit_required` and `reproducibility_das_cas_check` as `True` (`intent.py:301-304`). The compiled protocol showed `{'retraction_check_required': True, …, 'minimum_trust_score_threshold': 0.0}`. The protocol therefore claims checks the researcher declined, with a threshold that makes them meaningless. (The `if` branch at `:303-304` also re-assigns the same 6.0.)

**INC-16 — Medium — Reproduced — Unvalidated inputs compile into a fingerprinted protocol.**
Nothing checks `start_year <= end_year`. Unparseable years (for example `2015-2020`) silently become `None` (`wizard.py:248-249`, `num_if_valid`). An empty "proof" answer is accepted. Compiling a survey with `2024`/`2010` and an empty proof produced `"date_range": {"end_year": 2010, "start_year": 2024}` and the screening criterion `**Criterion**: Reports the gold-standard proof — ` with an empty value (`intent.py:235-236`).

**INC-17 — Low — Reproduced — `nexus-scholar init` writes literal `\n` sequences.**
`genesis.py:266-273` uses `"\\n"` in normal strings, so `synthesis/literature_review.md` comes out as `'# Literature Review: T\\n\\n## Objectives…'`. The same happens in the error text at `:205`. The docstring claims a "byte-for-byte" mirror of `init_project.py` (`:230-231`).

**INC-18 — Low — Reproduced — SKILL.meta generation never finds the dev manifest.**
`genesis.py:577-582` uses `parents[4]`, which resolves to `C:\Users\mouadh\Documents\.agents\...` (above the repo). `parents[3]` exists. Result: `{'manifest': None, 'generated': 0}`, so workspaces scaffolded from the repo get no pin metadata.

**INC-19 — Low — Reproduced — Dataset regex typo.**
`lexicon.py:60` matches `\bmmmlu\b` instead of `mmlu`, so `"Results on MMLU and GSM8K"` yields `{'GSM8K': 1}`.

**INC-20 — Low — Static — "Newest" lineage artifact is chosen by string order.**
`workspace.py:841-845` sorts `accepted_at` as strings. `…T00:00:00Z` sorts after `…T00:00:00.5+00:00` (`Z` > `.`), so mixed timestamp formats can serve an older artifact as current.

## 4. Research-method fitness

**INC-21 — High — Reproduced — "Anchored" means only that the provider returned something.**
In grounded mode every user concept and synonym must be "anchored", or the wizard aborts and "nothing unanchored is ever emitted" (`grounded.py:269-271, 434-439`). The check is `_pool_anchor_dois(pool)`: any DOI in the probe's result pool, with no test that the term occurs in that record (`grounded.py:417-424, 446-453, 468-471`). Reproduced with a stub provider that returns one bird-migration paper:
```
{'quantum error correction': ['10.9/birds'], 'surface codes': ['10.9/birds']}
```
Four fuzzy full-text providers return something for almost any string, so this gate almost never rejects. The topic itself is anchored to every DOI in its pool (`grounded.py:303-308, 365-367`). The APR gate built on these maps (`gates.py:31-41`) scores 1.0 by construction. Recommendation: require term occurrence in title/abstract (as the distiller already does for taxonomy terms), and record "provider returned N hits" separately from "term observed in K records".

**INC-22 — High — Reproduced — The wizard writes eligibility criteria the researcher did not author and does not see.**
`make_intent` always adds the inclusion criterion "Reports the gold-standard proof — {proof}", mapped to every RQ (`intent.py:235-236`). The answer to "what would convince a top-tier peer reviewer" thereby becomes a mandatory inclusion rule. When no exclusions are given, it injects the paradigm's `negative_exclusions` (`intent.py:249-251`). Reproduced: the Positivist run (`repro3.py`) got the exclusion "Subjective emotional state as primary proof; non-replicable anecdotes." For Interpretivist, the default excludes studies reporting "Statistical p-values, claims of global generalizability" (`intent.py:77`), which would drop mixed-methods evidence. The final confirmation panel shows only the counts (`inclusion: 1 / exclusion: 1`), never the criterion text (`wizard.py:346-353`), and then compiles `SCREENING_CRITERIA.md`. This extends prior finding 2: the defaults are not merely suggestive, they become hidden screening policy.

**INC-23 — Medium — Static — English-only is a silent default.**
`languages = ["en"]` unless the researcher opts into the date/language question (`wizard.py:245-251`), and `make_intent` falls back to `["en"]` again (`intent.py:260`). The same applies to `--scaffold-only` (`genesis.py:630`). A language restriction is a known source of bias that PRISMA asks reviewers to report and justify. The default should be "unrestricted" or "undetermined, ask".

**INC-24 — Medium — Reproduced — Directions are ranked by n-gram length; headless "best" picks the longest phrase.**
Candidates sort by `(-word_count, -freq, term)` (`grounded.py:154`). CLI help says `--auto-select` picks "the best (first) grounded direction" (`cli.py:523`), and the docstring says "most anchored" (`grounded.py:273-274`). With "soil salinity" in 20 papers and three 3-word terms in 2 papers each, the output was `salt tolerant rice cultivars 2 / deficit irrigation scheduling 2 / electrical conductivity measurement 2`, and auto-select takes the first. A "direction" is a frequent title/abstract n-gram observed in at least 2 of at most 25 records. The wording "Grounded Direction" overstates that.

**INC-25 — Medium — Static — QEI is compared against the wrong threshold and framed as novelty.**
The distiller defines QEI as the share of the top-10 n-grams that share a token with the query, gated at `<= 0.3` (`distiller.py:129-150`). The wizard compares it with `TOPIC_COHERENCE_TOP3_SHARE` (0.50), a topic-share constant (`grounded.py:239-247`). The inception-agent skill tells the agent that `qei ≤ 0.3` means "pool is novel relative to the prompt (good)" (`.agents/skills/inception-agent/SKILL.md:66`). Lexical non-overlap with a prompt is not novelty; at best it shows that the vocabulary differs.

**INC-26 — Medium — Reproduced — Paradigm detection is raw substring matching, and the lexicon check runs before any RQ exists.**
`kw in text` (`intent.py:124`) yields `ecosystem services in coastal wetlands → Design Science` ("system"), `building energy codes → Design Science`, and `costume history → Pragmatist` ("cost"). `enforce_lexicon` runs only on the topic (`wizard.py:241`). The RQ text and proof that enter the protocol are written afterwards and never checked.

**INC-27 — Low — Static — Human decisions get an invented confidence and reasoning.**
`Decision.confidence` defaults to 0.8, an unrecognised word also maps to 0.8, and an empty reasoning becomes "include during console verification review" (`screening.py:44, 62-78`). The stored record then reads as if the reviewer stated a confidence and a reason.

**INC-28 — Low — Static — Gates are advisory, and pool age is not surfaced.**
`gates.py:21-22` says directions "should not be proposed below" 12 docs. The wizard only prints a note and proposes anyway, also in headless mode (`grounded.py:204-249`). The GENESIS summary records `cache_keys` and `pool_sizes`, but not the pool `created_at` (`genesis.py:314-326`), so provenance cannot show that a direction came from a months-old cached pool (see INC-09).

### Status of the 2026-10-09 review findings

| # | Prior finding | Status at 5deb3a1 | Evidence |
|---|---|---|---|
| 1 | Paradigm conflated with review design; zero-score ties to Positivist | Still present | `intent.py:36-41, 116-126`; `wizard.py:212`. `detect_leanings("soil salinity")` → all 0, Positivist first; wizard emitted `Positivist PRISMA_SLR`. Substring false positives worsen it (INC-26). |
| 2 | Outcome-presupposing templates; profile exclusions become criteria | Still present, broader than reported | Templates unchanged `intent.py:71, 94, 105`; default exclusion `:249-251`; plus the always-added proof inclusion criterion and count-only confirmation (INC-22). |
| 3 | Concentration labelled coherence | Still present | `gates.py:118-120`. Oncology/astronomy/economics n=1 each → `label: coherent, purity: 1.0`. |
| 4 | Retrieval volume labelled saturation/gap | Changed (wording only) | Code unchanged `engine.py:36-37, 179-191`. Skill now says "search sparsity alone never proves a research gap" (`SKILL.md:78`), but the same line calls scant/sparse "genuinely thin literature" and the emitted label is still `confidence.label: gap`. |
| 5 | Field neutrality and anchor strength overstated | Still present | ASCII tokenizer `distiller.py:29`; DOI-only evidence `:76-78`; ML-weighted lexicon. New: MMLU typo (INC-19). |
| 6 | Full pools absorb no follow-up evidence | Still present | `adaptive.py:216-233`. 25-doc original + new DOI → `25 False`. |
| 7 | Cache identity omits sample size | Still present | `engine.py:290, 294`. `probe(max_results=5)` then `(max_results=25)` → `5 5`. |
| 8 | Venue-token substring junk filter | Still present, broader | `grounded.py:81`. `science journalism`, `volume rendering`, `workshop pedagogy`, `meeting scheduling`, `journaling intervention` → all `True`. |
| 9 | Fallback direction concept lacks two-paper support | Still present | `grounded.py:166-186`. `alpha`(10.1/a) + `beta`(10.1/b) → `{'label':'alpha beta','concept':'alpha','anchor_dois':['10.1/a','10.1/b'],'detail':'pool vocabulary observed in 2 papers'}`. |

## 5. Doc drift

- `console/serve.py:56-60`, "Browsers never mutate through this API": false. Foreign `Host` is accepted, and mutations need no auth (INC-01, INC-03).
- `console/api/audit.py:7-8`, "never trust the client for provenance fields": `agent_or_tool`, `status`, `reviewed_by` and `timestamp` are client-supplied (INC-03).
- `inception/grounded.py:273-274` "most anchored" and `cli.py:523` "best": the ranking is by word count first (INC-24).
- `inception/grounded.py:269-271, 438-439`, "nothing unanchored is ever emitted": true only in the sense of INC-21.
- `inception/genesis.py:230-231`, "mirrors … byte-for-byte": false (INC-17).
- `recon/gates.py:21-22`, "Directions should not be proposed below this": the wizard proposes them (INC-28).
- `console/api/screening.py:1192`, "one bad line never refuses the feed": it returns 500 (INC-14).

## 6. Prioritized recommendations

| ID | Severity | Effort | Action |
|---|---|---|---|
| INC-01 | High | M | Add a per-launch bearer token (printed by `serve`, forwarded by the UI proxy), `TrustedHostMiddleware` for loopback names, and an allowlist of kit CLIs for pipeline node commands; refuse a non-loopback `--host` without an explicit flag. |
| INC-08 | High | S | Call `require_uninitialized` (or an explicit `--replace` with a backup of `protocol.json`/`intent.json`) in `run_wizard` before scaffolding; stop `init_project.py` from rewriting `created_at`/`stats` of an existing manifest. |
| INC-21 | High | S | Anchor a concept only on records whose title/abstract contains it; keep "hits returned" as a separate field; make APR measure occurrence. |
| INC-22 | High | S | Remove the auto proof-inclusion and the paradigm default exclusions, or show each generated criterion verbatim and require explicit acceptance per criterion. |
| INC-09 | High | S | Never cache an empty or provider-error pool; store per-provider outcome in the pool; add `refresh=True` and surface pool `created_at` in `recon_context`. |
| INC-02 | Medium | S | Build argv lists directly (no string re-split); drop the client `workspace` override. |
| INC-03 | Medium | S | Fix `agent_or_tool` server-side; restrict `/audit/events` actions to a console namespace; store reviewer and server timestamp per decision record. |
| INC-13 | Medium | S | Derive readiness from the same coverage check as `/ui/batches`; delete the legacy batches route. |
| INC-14 | Medium | S | Define `logger`; report corrupt journal lines as explicit items in both readers (one shared reader). |
| INC-15 / INC-16 | Medium | S | Make declined checks `False` in the intent; validate year order, year format and non-empty proof before compiling. |
| INC-11 | Medium | S | Guard finalisation with `if job.state == "cancelled": return` (after cleanup); journal exactly once. |
| INC-12 | Medium | S | Resolve `src/...` against the repo root (as `pipeline_executor` does); hide `rag_index`/`synthesize` until their parameters can be supplied. |
| INC-10 | Medium | M | Request a relevance-ordered sample (one provider or an explicit merge rule) and record the selection rule in the pool. |
| INC-23 | Medium | S | Default languages to "unrestricted" (or force the question) and record the rationale. |
| INC-24 / INC-25 / INC-26 | Medium | M | Rank directions by evidence and show counts; rename `--auto-select` help; compare QEI with its own gate and drop the "novel" wording; use word-boundary matching and run the lexicon check on the final RQ/proof text. |
| INC-04 / INC-05 / INC-06 | Medium/Low | M | Remove the module-class hack and patch owning modules in tests; deduplicate `_ui07_*` helpers; clear the ruff F-findings. |
| Prior 3–9 | Medium | M | Execute the follow-up order already written in `inception_recon_scientific_review.md` (regression tests first). |
| INC-17–20, 27, 28, 07 | Low | S | Point fixes as described. |

## 7. Limits of this assessment

- About 230 lines of `screening.py` (roughly 840–1170: the review, criterion-refs and audit-feed helpers) and the first 380 lines of `pipelines.py` (template rendering and builtins) were skimmed or not read line by line. `authority/`, `screening/` and `pipeline_executor.py` were followed only as far as the console calls into them. Their own correctness belongs to other assessments.
- INC-01 was reproduced with `TestClient` and a forged `Host` header, not with a live DNS-rebinding attack. Exploitability through a real browser also depends on browser private-network-access policies, which vary.
- INC-10 is reasoned from the kit's concurrent-append code. No live multi-provider run was made, because there were no network calls.
- No live provider runs were made, so pool quality, topic layers and saturation counts were not observed on real data. Research-method judgements rest on code semantics and constructed counterexamples, not on expert-rated cases.
- The existing 353 tests passed. I did not measure coverage, so "untested" is not claimed for any finding.
